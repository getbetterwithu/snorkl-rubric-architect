#!/usr/bin/env python3
"""
Automated Regression Test Suite for Snorkl Rubric Architect (v15.0)
Covers:
  1. Offline KaTeX bundle completeness & zero-CDN template guarantee
  2. Geometry engine safety (parallel line ValueError, concave polygon interior point, outward arcs)
  3. Renderer zero-false-positive guarantees (stale file rejection, DOM overflow & KaTeX error rejection)
  4. Validator & cross-file consistency checks (PNG header, MD plain-text, PDF page count, number/answer drift)
  5. Curriculum reference factual regression guards
"""

from __future__ import annotations

import os
import re
import shutil
import struct
import sys
import tempfile
import time
import unittest
import zlib
from unittest.mock import patch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import render_card
import snorkl_builder
import snorkl_geometry_engine as geo
import validate_outputs


def _make_dummy_png_bytes(width: int, height: int) -> bytes:
    """Construct a minimal valid PNG binary with exact (width, height) in IHDR."""
    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw_scanline = b"\x00" + (b"\xff\xff\xff" * width)
    idat = zlib.compress(raw_scanline * height)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


class TestLocalKatexAndTemplates(unittest.TestCase):
    def test_katex_vendor_bundle_referential_integrity(self):
        katex_dir = os.path.join(SCRIPTS_DIR, "vendor", "katex")
        for rel in ("katex.min.css", "katex.min.js", os.path.join("contrib", "auto-render.min.js"), "LICENSE"):
            full = os.path.join(katex_dir, rel)
            self.assertTrue(os.path.isfile(full), f"Missing vendored KaTeX file: {rel}")
            self.assertGreater(os.path.getsize(full), 100)

        with open(os.path.join(katex_dir, "katex.min.css"), "r", encoding="utf-8") as f:
            css = f.read()
        urls = re.findall(r"url\(([^)]+)\)", css)
        self.assertGreaterEqual(len(urls), 15)
        for u in urls:
            u_clean = u.strip("\"'")
            font_path = os.path.join(katex_dir, u_clean.replace("/", os.sep))
            self.assertTrue(os.path.isfile(font_path), f"Missing KaTeX font referenced by CSS: {u_clean}")
            self.assertGreater(os.path.getsize(font_path), 1000)

    def test_templates_have_zero_external_cdn_links(self):
        for tpl_name in ("template_card.html", "template_teacher_sheet.html"):
            with open(os.path.join(SCRIPTS_DIR, tpl_name), "r", encoding="utf-8") as f:
                html = f.read()
            self.assertNotIn("cdn.jsdelivr.net", html)
            self.assertNotIn("unpkg.com", html)
            self.assertIn("Malgun Gothic", html)
            self.assertIn("dataset.renderStatus", html)


class TestGeometryEngineSafety(unittest.TestCase):
    def test_line_intersection_exact_and_parallel_rejection(self):
        ix, iy = geo.line_intersection((0.0, 0.0), (10.0, 10.0), (0.0, 10.0), (10.0, 0.0))
        self.assertAlmostEqual(ix, 5.0)
        self.assertAlmostEqual(iy, 5.0)

        # Parallel lines MUST raise ValueError (never silently return midpoint!)
        with self.assertRaises(ValueError):
            geo.line_intersection((0.0, 0.0), (10.0, 0.0), (0.0, 5.0), (10.0, 5.0))

        # Collinear lines MUST raise ValueError
        with self.assertRaises(ValueError):
            geo.line_intersection((0.0, 0.0), (5.0, 0.0), (2.0, 0.0), (8.0, 0.0))

        # Degenerate zero-length line MUST raise ValueError
        with self.assertRaises(ValueError):
            geo.line_intersection((1.0, 1.0), (1.0, 1.0), (0.0, 0.0), (3.0, 3.0))

    def test_concave_polygon_interior_label_point(self):
        # Thin L-shaped polygon whose area-weighted centroid lies OUTSIDE in the empty cutout
        l_shape = [
            (0.0, 0.0),
            (200.0, 0.0),
            (200.0, 20.0),
            (20.0, 20.0),
            (20.0, 200.0),
            (0.0, 200.0),
        ]
        raw_centroid = geo.polygon_centroid(l_shape)
        self.assertFalse(
            geo.point_in_polygon(raw_centroid, l_shape),
            "Precondition: thin L-shape raw centroid should fall outside polygon",
        )

        safe_pt = geo.interior_label_point(l_shape)
        self.assertTrue(
            geo.point_in_polygon(safe_pt, l_shape),
            f"interior_label_point {safe_pt} must lie strictly inside concave polygon",
        )
        self.assertGreater(geo.polygon_min_clearance(safe_pt, l_shape), 5.0)

        svg = geo.render_shaded_region(l_shape, label="S")
        self.assertIn(f'x="{safe_pt[0]:.2f}"', svg)
        self.assertIn(f'y="{safe_pt[1]:.2f}"', svg)

    def test_outward_dimension_arc_and_new_helpers(self):
        rect = [(100.0, 100.0), (100.0, 250.0), (350.0, 250.0), (350.0, 100.0)]
        # Top edge (100,100) -> (350,100): outward must point UP (ny < 0) regardless of vertex order
        (nx, ny), _ = geo.outward_normal_vector((100.0, 100.0), (350.0, 100.0), rect)
        self.assertAlmostEqual(nx, 0.0)
        self.assertLess(ny, -0.9)

        self.assertIn("<circle", geo.render_circle((200.0, 200.0), 60.0, center_label="O"))
        self.assertIn("<path", geo.render_arc((200.0, 200.0), 60.0, 0.0, 90.0, dashed=True))
        self.assertIn("stroke-dasharray", geo.render_dashed_line((0.0, 0.0), (50.0, 50.0)))
        self.assertIn(">O</text>", geo.render_coord_axes(show_grid=True))
        self.assertIn(">A</text>", geo.render_vertex_label(rect[0], "A", direction="auto", polygon_points=rect))


class TestRendererZeroFalsePositives(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="snorkl_test_")

    def tearDown(self):
        os.environ.pop("SNORKL_BROWSER_BIN", None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_stale_existing_files_never_cause_false_success(self):
        html_path = os.path.join(self.tmpdir, "input.html")
        png_path = os.path.join(self.tmpdir, "stale.png")
        pdf_path = os.path.join(self.tmpdir, "stale.pdf")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><body>hello</body></html>")
        stale_png_bytes = _make_dummy_png_bytes(2000, 1000)
        with open(png_path, "wb") as f:
            f.write(stale_png_bytes)
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n%stale\n" + b"0" * 2048)

        # Point browser override to a non-existent binary -> render MUST return False despite valid stale files!
        os.environ["SNORKL_BROWSER_BIN"] = os.path.join(self.tmpdir, "missing_browser.exe")
        self.assertFalse(render_card.render_png(html_path, png_path))
        self.assertFalse(render_card.render_pdf(html_path, pdf_path))

    @unittest.skipUnless(render_card.find_browser(), "Headless browser required for live DOM audit tests")
    def test_headless_dom_audit_blocks_katex_error_and_overflow(self):
        with open(os.path.join(SCRIPTS_DIR, "template_card.html"), "r", encoding="utf-8") as f:
            tpl = f.read()

        # 1. Broken KaTeX expression -> must fail render_png
        bad_math_html = os.path.join(self.tmpdir, "bad_math.html")
        bad_png = os.path.join(self.tmpdir, "bad_math.png")
        with open(bad_math_html, "w", encoding="utf-8") as f:
            f.write(tpl.replace("<!-- PASSAGE_HTML_PLACEHOLDER -->", r'<div class="problem-header">$\frac{1}{$</div>'))
        self.assertFalse(render_card.render_png(bad_math_html, bad_png))
        self.assertFalse(os.path.exists(bad_png))

        # 2. Severe text overflow in .passage -> must fail render_png
        overflow_html = os.path.join(self.tmpdir, "overflow.html")
        overflow_png = os.path.join(self.tmpdir, "overflow.png")
        giant_text = "<br>".join([f"매우 긴 문장 줄바꿈 테스트 {i}" for i in range(30)])
        with open(overflow_html, "w", encoding="utf-8") as f:
            f.write(tpl.replace("<!-- PASSAGE_HTML_PLACEHOLDER -->", f'<div class="problem-header">{giant_text}</div>'))
        self.assertFalse(render_card.render_png(overflow_html, overflow_png))
        self.assertFalse(os.path.exists(overflow_png))

        # 3. 1px unreadable child span in teacher sheet -> must fail render_pdf
        with open(os.path.join(SCRIPTS_DIR, "template_teacher_sheet.html"), "r", encoding="utf-8") as f:
            sheet_tpl = f.read()
        tiny_sheet_html = os.path.join(self.tmpdir, "tiny_sheet.html")
        tiny_sheet_pdf = os.path.join(self.tmpdir, "tiny_sheet.pdf")
        tiny_body = '<div class="info-box"><span style="font-size:1px">UNREADABLE MODEL SOLUTION</span></div>'
        with open(tiny_sheet_html, "w", encoding="utf-8") as f:
            f.write(
                sheet_tpl.replace("<!-- TITLE_PLACEHOLDER -->", "Test")
                .replace("<!-- CONTENT_HTML_PLACEHOLDER -->", tiny_body)
            )
        self.assertFalse(render_card.render_pdf(tiny_sheet_html, tiny_sheet_pdf))
        self.assertFalse(os.path.exists(tiny_sheet_pdf))


class TestValidatorAndGoldenExamples(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="snorkl_val_test_")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_both_golden_examples_pass_full_validation(self):
        for folder in ("geometry_trapezoid_motion", "algebra_linear_inequality"):
            ex_dir = os.path.join(REPO_ROOT, "examples", folder)
            rc = validate_outputs.main([ex_dir])
            self.assertEqual(rc, 0, f"Golden example {folder} failed validate_outputs.py")

            pdfs = [os.path.join(ex_dir, fn) for fn in os.listdir(ex_dir) if fn.endswith(".pdf")]
            self.assertEqual(len(pdfs), 1)
            self.assertEqual(validate_outputs.count_pdf_pages_pure_python(pdfs[0]), 1)

    def test_validator_catches_resolution_latex_and_cross_file_drift(self):
        src_dir = os.path.join(REPO_ROOT, "examples", "algebra_linear_inequality")
        for fn in os.listdir(src_dir):
            src_fp = os.path.join(src_dir, fn)
            if os.path.isfile(src_fp) and not fn.endswith(".py"):
                shutil.copy2(src_fp, os.path.join(self.tmpdir, fn))

        slug = "일차부등식_최대자연수해"
        png = os.path.join(self.tmpdir, f"{slug}_문제등록화면.png")
        md = os.path.join(self.tmpdir, f"{slug}_정답_평가기준.md")
        pdf = os.path.join(self.tmpdir, f"{slug}_교사참고용_채점기준표.pdf")
        c_html = os.path.join(self.tmpdir, f"{slug}_card.html")
        s_html = os.path.join(self.tmpdir, f"{slug}_sheet.html")

        # Baseline passes (skip live DOM here for fast unit checks)
        ok, errs = validate_outputs.validate_deliverable_set(png, md, pdf, c_html, s_html, check_dom=False)
        self.assertTrue(ok, f"Baseline copy should pass: {errs}")

        # Case A: Wrong PNG dimensions (1000x500 instead of 2000x1000)
        with open(png, "wb") as f:
            f.write(_make_dummy_png_bytes(1000, 500))
        ok, errs = validate_outputs.validate_deliverable_set(png, md, pdf, c_html, s_html, check_dom=False)
        self.assertFalse(ok)
        self.assertTrue(any("2000x1000" in e for e in errs))

        # Restore valid 2000x1000 PNG and keep mtime consistent
        with open(png, "wb") as f:
            f.write(_make_dummy_png_bytes(2000, 1000))
        now = time.time()
        os.utime(c_html, (now - 10, now - 10))
        os.utime(png, (now - 5, now - 5))
        os.utime(s_html, (now - 4, now - 4))
        os.utime(pdf, (now - 1, now - 1))

        # Case B: Leaked `$` and `0.5점` in MD + stem number drift (`99` added in MD [문항])
        with open(md, "r", encoding="utf-8") as f:
            orig_md = f.read()
        mutated_md = orig_md.replace("(2/5)x", "$(2/5)x$ + 99") + "\n부분점수 0.5점 부여\n"
        with open(md, "w", encoding="utf-8") as f:
            f.write(mutated_md)
        ok, errs = validate_outputs.validate_deliverable_set(png, md, pdf, c_html, s_html, check_dom=False)
        self.assertFalse(ok)
        self.assertTrue(any("Forbidden LaTeX" in e for e in errs))
        self.assertTrue(any("0.5점" in e for e in errs))
        self.assertTrue(any("stem mismatch" in e for e in errs))

        # Case C: Answer mismatch between MD and Sheet HTML
        answer_drift_md = orig_md.replace("\n3\n", "\n7\n", 1)
        with open(md, "w", encoding="utf-8") as f:
            f.write(answer_drift_md)
        ok, errs = validate_outputs.validate_deliverable_set(png, md, pdf, c_html, s_html, check_dom=False)
        self.assertFalse(ok)
        self.assertTrue(any("final answer mismatch" in e for e in errs))

    def test_adversarial_rc_audit_bypasses_all_blocked(self):
        src_dir = os.path.join(REPO_ROOT, "examples", "algebra_linear_inequality")
        for fn in os.listdir(src_dir):
            src_fp = os.path.join(src_dir, fn)
            if os.path.isfile(src_fp) and not fn.endswith(".py"):
                shutil.copy2(src_fp, os.path.join(self.tmpdir, fn))

        slug = "일차부등식_최대자연수해"
        png = os.path.join(self.tmpdir, f"{slug}_문제등록화면.png")
        md = os.path.join(self.tmpdir, f"{slug}_정답_평가기준.md")
        pdf = os.path.join(self.tmpdir, f"{slug}_교사참고용_채점기준표.pdf")
        c_html = os.path.join(self.tmpdir, f"{slug}_card.html")
        s_html = os.path.join(self.tmpdir, f"{slug}_sheet.html")
        with open(md, "r", encoding="utf-8") as f:
            orig_md = f.read()

        # 1. ProblemSpec LaTeX vs Plain answer divergence ($999$ vs 3) -> ValueError at build time
        import importlib.util

        spec_mod_path = os.path.join(src_dir, "build_example.py")
        loader = importlib.util.spec_from_file_location("ex_alg", spec_mod_path)
        ex_alg = importlib.util.module_from_spec(loader)  # type: ignore[arg-type]
        assert loader and loader.loader
        loader.loader.exec_module(ex_alg)
        bad_spec = ex_alg.make_spec()
        bad_spec.final_answer_latex = "$999$"
        with self.assertRaises(ValueError):
            snorkl_builder.build_all_outputs(bad_spec, os.path.join(self.tmpdir, "bad_out"))

        # 2. Truncated 24-byte PNG -> rejected
        trunc_png = os.path.join(self.tmpdir, "truncated.png")
        with open(png, "rb") as f_in, open(trunc_png, "wb") as f_out:
            f_out.write(f_in.read(24))
        ok, errs = validate_outputs.validate_deliverable_set(trunc_png, md, pdf, c_html, s_html, check_dom=False)
        self.assertFalse(ok)

        # 3. Inequality flip (`>` -> `<`) and number order swap (`2/5` -> `5/2`) -> both rejected
        stem_part, rest_part = orig_md.split("[정답", 1)
        for bad_stem in (stem_part.replace(" > ", " < "), stem_part.replace("(2/5)", "(5/2)")):
            bad_md = os.path.join(self.tmpdir, "bad_stem.md")
            with open(bad_md, "w", encoding="utf-8") as f:
                f.write(bad_stem + "[정답" + rest_part)
            ok, errs = validate_outputs.validate_deliverable_set(png, bad_md, pdf, c_html, s_html, check_dom=False)
            self.assertFalse(ok, f"Expected stem mutation to fail: {bad_stem}")

        # 4. Unlisted LaTeX commands, fractional score bypasses, and Olympiad brackets -> all rejected
        for snippet in (
            r"\alpha + \beta \leq 90^\circ",
            r"집합 \{1, 2\}",
            "부분점수 0.5점을 준다(감점 금지).",
            "부분점수 0.5 점 부여",
            "부분점수 1.5점 부여",
            "반점 부여",
            "넓이를 [□ABCD]라 하자.",
            "넓이를 [ABC]라 하자.",
        ):
            bad_md = os.path.join(self.tmpdir, "bad_tok.md")
            with open(bad_md, "w", encoding="utf-8") as f:
                f.write(orig_md + "\n" + snippet + "\n")
            ok, _ = validate_outputs.validate_deliverable_set(png, bad_md, pdf, c_html, s_html, check_dom=False)
            self.assertFalse(ok, f"Expected snippet to be blocked: {snippet}")

        # 5. Unrelated US Letter PDF (612 x 792 pt) -> rejected even without PyMuPDF
        letter_pdf = os.path.join(self.tmpdir, "letter.pdf")
        fake_pdf_bytes = (
            b"%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
            b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >> endobj\n"
            + b"%padding\n" * 160
            + b"%%EOF\n"
        )
        with open(letter_pdf, "wb") as f:
            f.write(fake_pdf_bytes)
        ok, errs = validate_outputs.validate_deliverable_set(png, md, letter_pdf, c_html, s_html, check_dom=False)
        self.assertFalse(ok)
        self.assertTrue(any("not A4 portrait" in e for e in errs))

        # 6. Missing HTML sources -> rejected by default
        ok, errs = validate_outputs.validate_deliverable_set(png, md, pdf, None, None, check_dom=False)
        self.assertFalse(ok)
        self.assertTrue(any("missing" in e.lower() for e in errs))

        # 7. Missing headless browser when check_dom=True -> rejected (never silently skipped)
        with patch.object(validate_outputs, "find_browser", return_value=None):
            ok, errs = validate_outputs.validate_deliverable_set(png, md, pdf, c_html, s_html, check_dom=True)
            self.assertFalse(ok)
            self.assertTrue(any("browser" in e.lower() for e in errs))

        # 8. Post-build hand modification of `_sheet.html` body -> rejected by `snorkl-body-sha256`
        tampered_sheet = os.path.join(self.tmpdir, "tampered_sheet.html")
        with open(s_html, "r", encoding="utf-8") as f:
            orig_sheet = f.read()
        with open(tampered_sheet, "w", encoding="utf-8") as f:
            f.write(orig_sheet.replace("기본 모범답안", "임의 변조 모범답안"))
        now = time.time()
        os.utime(tampered_sheet, (now - 10, now - 10))
        os.utime(pdf, (now - 1, now - 1))
        ok, errs = validate_outputs.validate_deliverable_set(png, md, pdf, c_html, tampered_sheet, check_dom=False)
        self.assertFalse(ok)
        self.assertTrue(any("snorkl-body-sha256" in e for e in errs))


class TestCurriculumStandardsIntegrity(unittest.TestCase):
    def test_curriculum_fact_corrections_present(self):
        ref_path = os.path.join(REPO_ROOT, "references", "korean_middle_math_standards.md")
        with open(ref_path, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn("원의 접선과 현이 이루는 각의 성질", text)
        self.assertIn("0°에서 90°까지의 각도에 대한 삼각비의 값", text)
        self.assertIn("최대공약수·최소공배수의 실생활 활용 문제는 다루지 않음", text)
        self.assertIn("[9수04-05]", text)
        self.assertIn("각 계수가 $0$이 아닐 때", text)


if __name__ == "__main__":
    unittest.main()
