#!/usr/bin/env python3
r"""
validate_outputs.py - Automated Deliverable & Cross-File Consistency Validator (v15.0)

Mandatory pre-delivery gate before Step 5 completion can be declared.
Checks:
  1. Card PNG (`_문제등록화면.png`): exists, full PNG chunk/CRC32/IDAT decompression valid, exact `2000 x 1000` px.
  2. Snorkl Plain-Text Markdown (`_정답_평가기준.md`):
     - UTF-8 readable, non-empty
     - Zero `$` characters and zero LaTeX backslash commands/escapes (`\alpha`, `\frac`, `\{`, `^\circ`, ...)
     - Zero Olympiad area bracket notation (`[△ABC]`, `[□ABCD]`, `[ABC]`)
     - Zero fractional `0.5점` / `반점` AI grading instructions (Snorkl AI uses 0-4 integer scale)
     - Required Snorkl rubric sections present
  3. Teacher Reference PDF (`_교사참고용_채점기준표.pdf`):
     - Valid `%PDF-` header, non-trivial size
     - Exact page count `1 <= pages <= max_pdf_pages` (default `1` page)
     - Exact A4 portrait MediaBox (`~595.28 x 841.89 pt`; rejects US Letter `612 x 792 pt`)
     - PDF text-layer verification (footer provenance, title, `$`-free, and visible final answer match)
  4. Source HTML Presence, Body Integrity, Cross-File Consistency, and Headless DOM Audit:
     - Requires `_card.html` and `_sheet.html` by default (`require_html=True`)
     - Requires headless browser when `check_dom=True` (never silently skips)
     - Verifies `snorkl-body-sha256` & `snorkl-spec-sha256` against post-build tampering
     - Verifies ordered numbers, relational operators (`<, <=, >, >=, =, !=`), and variables in stem
     - Verifies visible rendered answer in `_sheet.html` (`#final-answer-value`) against `.md` `[정답]`
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import shutil
import sys
import tempfile

from render_card import (
    audit_dom_headless,
    ensure_utf8_stdio,
    find_browser,
    prepare_resolved_html,
    read_png_dimensions,
)
from snorkl_builder import (
    ALLOWED_DECIMAL_SCORE_DISCLAIMER,
    compute_html_body_sha256,
    extract_math_signature,
    strip_known_html_tags,
)

FORBIDDEN_LATEX_PATTERNS = [
    r"\$",
    r"\\[A-Za-z]+",
    r"\\[{}\[\]()^_]",
    r"[\^_]\{[^}]*\}",
]

OLYMPIAD_AREA_BRACKET_RE = re.compile(
    r"\[\s*(?:(?:△|∆|□|▱|\\triangle\s*|\\square\s*|삼각형\s*|사각형\s*|오각형\s*|평행사변형\s*|마름모\s*|사다리꼴\s*)[A-Za-z가-힣0-9]+|[A-Z]{2,6})\s*\]"
)

FRACTIONAL_SCORE_RE = re.compile(r"(?<!\d)[0-4]\.\d+\s*점|반\s*점")

A4_WIDTH_PT = 595.28
A4_HEIGHT_PT = 841.89
A4_TOLERANCE_PT = 10.0


def parse_pdf_pure_python(pdf_path: str) -> tuple[int | None, list[tuple[float, float]]]:
    """Count PDF pages and extract `/MediaBox` `(width_pt, height_pt)` without third-party packages."""
    try:
        with open(pdf_path, "rb") as f:
            raw = f.read()
    except OSError:
        return None, []
    if not raw.startswith(b"%PDF-"):
        return None, []

    page_matches = re.findall(rb"/Type\s*/Page(?![A-Za-z])", raw)
    if page_matches:
        page_count: int | None = len(page_matches)
    else:
        count_matches = [
            int(m) for m in re.findall(rb"/Type\s*/Pages\b[^>]*?/Count\s+(\d+)", raw, flags=re.DOTALL)
        ]
        page_count = max(count_matches) if count_matches else None

    boxes: list[tuple[float, float]] = []
    for x0_b, y0_b, x1_b, y1_b in re.findall(
        rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]", raw
    ):
        try:
            w = abs(float(x1_b) - float(x0_b))
            h = abs(float(y1_b) - float(y0_b))
            boxes.append((w, h))
        except ValueError:
            pass
    return page_count, boxes


def count_pdf_pages_pure_python(pdf_path: str) -> int | None:
    pages, _ = parse_pdf_pure_python(pdf_path)
    return pages


def inspect_pdf(pdf_path: str) -> tuple[int | None, list[tuple[float, float]], str | None]:
    """Return `(page_count, page_sizes_pt, extracted_text_or_none)`."""
    try:
        import pymupdf  # type: ignore

        doc = pymupdf.open(pdf_path)
        try:
            pages = len(doc)
            boxes = [(float(doc[i].rect.width), float(doc[i].rect.height)) for i in range(pages)]
            full_text = "\n".join(doc[i].get_text("text", sort=True) for i in range(pages))
            return pages, boxes, full_text
        finally:
            doc.close()
    except ImportError:
        pages, boxes = parse_pdf_pure_python(pdf_path)
        return pages, boxes, None
    except Exception:
        return None, [], None


def extract_md_section(md_text: str, header_prefix: str) -> str:
    lines = md_text.splitlines()
    collecting = False
    buf: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if stripped.startswith(header_prefix):
                collecting = True
                continue
            if collecting:
                break
        if collecting:
            buf.append(line)
    return "\n".join(buf).strip()


def extract_card_stem_raw(card_html_text: str) -> str:
    """Extract raw problem stem blocks from `card.html` (preserving LaTeX before math signature)."""
    chunks: list[str] = []
    for cls in ("problem-header", "problem-formula", "target-question", "condition-text"):
        for m in re.finditer(
            rf'<div[^>]*class="[^"]*\b{cls}\b[^"]*"[^>]*>(.*?)</div>',
            card_html_text,
            flags=re.DOTALL | re.IGNORECASE,
        ):
            chunks.append(m.group(1))
    return "\n".join(chunks).strip()


def extract_sheet_visible_answer_raw(sheet_html_text: str) -> str | None:
    """Extract the actual visible answer markup from `_sheet.html` (never trusting hidden attributes)."""
    m_val = re.search(
        r'<span[^>]*id="final-answer-value"[^>]*>(.*?)</span>',
        sheet_html_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if m_val:
        return m_val.group(1).strip()

    m_box = re.search(
        r'<div[^>]*id="final-answer-box"[^>]*>(.*?)</div>',
        sheet_html_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if m_box:
        inner = re.sub(r"<strong\b[^>]*>.*?</strong>", " ", m_box.group(1), count=1, flags=re.DOTALL | re.IGNORECASE)
        return inner.strip()
    return None


def validate_deliverable_set(
    png_path: str,
    md_path: str,
    pdf_path: str,
    card_html_path: str | None = None,
    sheet_html_path: str | None = None,
    max_pdf_pages: int = 3,
    check_dom: bool = True,
    require_html: bool = True,
    txt_path: str | None = None,
) -> tuple[bool, list[str]]:
    errors: list[str] = []

    # 1. Validate Card PNG (`2000 x 1000` + full chunk/CRC/IDAT decompression)
    if not os.path.isfile(png_path):
        errors.append(f"Card PNG missing: {png_path}")
    else:
        dims = read_png_dimensions(png_path)
        if dims is None:
            errors.append(f"Card PNG is corrupted, truncated, or not a valid PNG file: {png_path}")
        elif dims != (2000, 1000):
            errors.append(f"Card PNG dimensions must be 2000x1000, got {dims[0]}x{dims[1]}: {png_path}")

    # 2. Validate Snorkl Plain-Text Markdown (`.md`)
    md_text = ""
    if not os.path.isfile(md_path):
        errors.append(f"Snorkl Markdown missing: {md_path}")
    else:
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                md_text = f.read()
        except UnicodeDecodeError as e:
            errors.append(f"Snorkl Markdown is not valid UTF-8: {e}")

        if not md_text.strip():
            errors.append("Snorkl Markdown is empty.")
        else:
            for pat in FORBIDDEN_LATEX_PATTERNS:
                m = re.search(pat, md_text)
                if m:
                    errors.append(f"Forbidden LaTeX token `{m.group(0)}` leaked into Snorkl plain-text MD.")
                    break

            if OLYMPIAD_AREA_BRACKET_RE.search(md_text):
                errors.append("Forbidden Olympiad area bracket notation (e.g. `[△ABC]`, `[□ABCD]`, `[ABC]`) found in Snorkl MD.")

            # Check scoring/rubric sections for banned fractional point instructions
            rubric_start = md_text.find("[설명 점수 채점 기준")
            scoring_slice = md_text[rubric_start:] if rubric_start != -1 else md_text
            scoring_without_disclaimer = scoring_slice.replace(ALLOWED_DECIMAL_SCORE_DISCLAIMER, "")
            m_frac = FRACTIONAL_SCORE_RE.search(scoring_without_disclaimer)
            if m_frac:
                errors.append(
                    f"Fractional `{m_frac.group(0)}` AI scoring instruction found in MD; "
                    "Snorkl AI Explanation Score supports integer 0-4 only."
                )

            required_markers = ["[문항]", "[정답", "[기본 모범 풀이", "채점 기준"]
            for marker in required_markers:
                if marker not in md_text:
                    errors.append(f"Required section `{marker}` missing from Snorkl MD.")
            if "가드레일" not in md_text and "공통 채점" not in md_text:
                errors.append("Required common grading principles section (`[공통 채점 ...]`) missing from Snorkl MD.")

    # 2-1. Validate Snorkl Plain-Text TXT (`.txt`) parity if provided
    if txt_path:
        if not os.path.isfile(txt_path):
            errors.append(f"Snorkl TXT file missing: {txt_path}")
        else:
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    txt_text = f.read()
                if txt_text != md_text:
                    errors.append(f"Parity mismatch: Snorkl TXT text differs from MD text: {txt_path}")
            except UnicodeDecodeError as e:
                errors.append(f"Snorkl TXT is not valid UTF-8: {e}")

    md_stem = extract_md_section(md_text, "[문항") if md_text else ""
    md_answer = extract_md_section(md_text, "[정답") if md_text else ""

    # 3. Validate Teacher Reference PDF (page count + A4 portrait MediaBox + text provenance)
    pdf_text: str | None = None
    if not os.path.isfile(pdf_path):
        errors.append(f"Teacher PDF missing: {pdf_path}")
    else:
        size = os.path.getsize(pdf_path)
        if size < 1024:
            errors.append(f"Teacher PDF is abnormally small ({size} bytes): {pdf_path}")
        else:
            page_count, boxes, pdf_text = inspect_pdf(pdf_path)
            if page_count is None or page_count < 1:
                errors.append(f"Teacher PDF could not be parsed or has 0 pages: {pdf_path}")
            elif page_count > max_pdf_pages:
                errors.append(
                    f"Teacher PDF exceeded page limit: got {page_count} page(s), max allowed is {max_pdf_pages}."
                )

            if not boxes:
                errors.append("Teacher PDF is missing `/MediaBox` page dimension metadata.")
            else:
                for idx, (w_pt, h_pt) in enumerate(boxes, start=1):
                    if abs(w_pt - A4_WIDTH_PT) > A4_TOLERANCE_PT or abs(h_pt - A4_HEIGHT_PT) > A4_TOLERANCE_PT:
                        errors.append(
                            f"Teacher PDF page {idx} is not A4 portrait ({w_pt:.1f}x{h_pt:.1f} pt, expected ~595.3x841.9 pt)."
                        )
                        break

            if pdf_text is None:
                print(
                    "[Validator Warning] PyMuPDF not installed; PDF text-layer check skipped "
                    "(A4 MediaBox + Sheet HTML cross-check enforced).",
                    file=sys.stderr,
                )
            else:
                if not pdf_text.strip():
                    errors.append("Teacher PDF text layer is completely empty.")
                else:
                    if "$" in pdf_text:
                        errors.append("Unrendered `$` character detected in Teacher PDF text.")
                    if "Snorkl Rubric Architect" not in pdf_text:
                        errors.append("Teacher PDF lacks `Snorkl Rubric Architect` provenance footer (unrelated PDF?).")
                    if md_answer:
                        m_pdf_ans = re.search(
                            r"\[최종 정답[^\]]*\]\s*(.*?)\s*\[기본 모범답안\]",
                            pdf_text,
                            flags=re.DOTALL,
                        )
                        if not m_pdf_ans:
                            errors.append("Teacher PDF is missing `[최종 정답] ... [기본 모범답안]` block.")
                        else:
                            pdf_nums, _, _, pdf_kor = extract_math_signature(m_pdf_ans.group(1))
                            md_nums, _, _, md_kor = extract_math_signature(md_answer)
                            if set(pdf_nums) != set(md_nums) or set(pdf_kor) != set(md_kor):
                                errors.append(
                                    f"Teacher PDF visible answer (`{m_pdf_ans.group(1).strip()}`) does not match "
                                    f"Snorkl MD [정답] (`{md_answer}`)."
                                )

    # 4. Enforce HTML Source Presence & Browser Availability (No Silent Skips)
    if require_html:
        if not card_html_path or not os.path.isfile(card_html_path):
            errors.append(
                "Card HTML source (`_card.html`) missing — required for cross-consistency & DOM audit "
                "(use `snorkl_builder.py`, or pass `--allow-missing-html` if intentionally auditing standalone binaries)."
            )
        if not sheet_html_path or not os.path.isfile(sheet_html_path):
            errors.append(
                "Teacher Sheet HTML source (`_sheet.html`) missing — required for cross-consistency & DOM audit "
                "(use `snorkl_builder.py`, or pass `--allow-missing-html` if intentionally auditing standalone binaries)."
            )
    else:
        if not (card_html_path and os.path.isfile(card_html_path)) or not (
            sheet_html_path and os.path.isfile(sheet_html_path)
        ):
            print("[Validator Warning] HTML source cross-checks skipped (`require_html=False`).", file=sys.stderr)

    browser: str | None = None
    if check_dom:
        if (card_html_path and os.path.isfile(card_html_path)) or (
            sheet_html_path and os.path.isfile(sheet_html_path)
        ):
            browser = find_browser()
            if not browser:
                errors.append("Headless browser (Edge/Chrome) not found; required DOM render audit could not run.")
    else:
        print("[Validator Warning] Headless DOM render audit skipped (`check_dom=False`).", file=sys.stderr)

    # 5. Cross-File Consistency, Post-Build Tamper Hash, Timestamps, and DOM Render Audit
    card_sha = None
    sheet_sha = None

    if card_html_path and os.path.isfile(card_html_path):
        with open(card_html_path, "r", encoding="utf-8") as f:
            card_html = f.read()

        if OLYMPIAD_AREA_BRACKET_RE.search(strip_known_html_tags(card_html)):
            errors.append("Forbidden Olympiad area bracket notation found in Card HTML.")

        if os.path.isfile(png_path):
            if os.path.getmtime(png_path) + 1.0 < os.path.getmtime(card_html_path):
                errors.append(
                    "Card PNG is older than Card HTML — re-render `_문제등록화면.png` after editing Card HTML."
                )

        m_sha = re.search(r'<meta\s+name="snorkl-spec-sha256"\s+content="([^"]+)"', card_html)
        if m_sha:
            card_sha = m_sha.group(1)

        m_body_sha = re.search(r'<meta\s+name="snorkl-body-sha256"\s+content="([^"]+)"', card_html)
        if m_body_sha:
            actual_body_sha = compute_html_body_sha256(card_html)
            if actual_body_sha != m_body_sha.group(1):
                errors.append("Card HTML body was modified after builder generation (`snorkl-body-sha256` mismatch).")

        card_stem = extract_card_stem_raw(card_html)
        if card_stem and md_stem:
            c_nums, c_ops, c_vars, _ = extract_math_signature(card_stem)
            m_nums, m_ops, m_vars, _ = extract_math_signature(md_stem)
            if (c_nums, c_ops, c_vars) != (m_nums, m_ops, m_vars):
                errors.append(
                    "Cross-file stem mismatch between Card HTML "
                    f"(nums={c_nums}, ops={c_ops}, vars={c_vars}) and Snorkl MD [문항] "
                    f"(nums={m_nums}, ops={m_ops}, vars={m_vars})."
                )

        if browser:
            tdir = tempfile.mkdtemp(prefix="snorkl_val_card_")
            try:
                eff = prepare_resolved_html(os.path.abspath(card_html_path), tdir)
                ok_dom, msg = audit_dom_headless(browser, pathlib.Path(eff).as_uri(), 1000, 500, tdir)
                if not ok_dom:
                    errors.append(f"Card HTML DOM audit failed: {msg}")
            finally:
                shutil.rmtree(tdir, ignore_errors=True)

    if sheet_html_path and os.path.isfile(sheet_html_path):
        with open(sheet_html_path, "r", encoding="utf-8") as f:
            sheet_html = f.read()

        if OLYMPIAD_AREA_BRACKET_RE.search(strip_known_html_tags(sheet_html)):
            errors.append("Forbidden Olympiad area bracket notation found in Sheet HTML.")

        if os.path.isfile(pdf_path):
            if os.path.getmtime(pdf_path) + 1.0 < os.path.getmtime(sheet_html_path):
                errors.append("Teacher PDF is older than Sheet HTML — re-render PDF after editing Sheet HTML.")
            if os.path.isfile(png_path) and os.path.getmtime(pdf_path) + 1.0 < os.path.getmtime(png_path):
                errors.append("Teacher PDF is older than Card PNG — re-render PDF so preview matches latest card.")

        m_sha = re.search(r'<meta\s+name="snorkl-spec-sha256"\s+content="([^"]+)"', sheet_html)
        if m_sha:
            sheet_sha = m_sha.group(1)

        m_body_sha = re.search(r'<meta\s+name="snorkl-body-sha256"\s+content="([^"]+)"', sheet_html)
        if m_body_sha:
            actual_body_sha = compute_html_body_sha256(sheet_html)
            if actual_body_sha != m_body_sha.group(1):
                errors.append(
                    "Teacher Sheet HTML body was modified after builder generation (`snorkl-body-sha256` mismatch)."
                )

        m_h1 = re.search(r"<h1>(.*?)</h1>", sheet_html, flags=re.DOTALL | re.IGNORECASE)
        if m_h1 and pdf_text is not None:
            h1_plain = strip_known_html_tags(m_h1.group(1)).strip()
            if h1_plain and h1_plain not in pdf_text:
                errors.append(f"Teacher PDF title does not match Sheet HTML `<h1>` (`{h1_plain}`).")

        visible_ans_raw = extract_sheet_visible_answer_raw(sheet_html)
        if visible_ans_raw is None:
            errors.append("Teacher Sheet HTML is missing `#final-answer-box` / `#final-answer-value`.")
        elif md_answer:
            sheet_sig = extract_math_signature(visible_ans_raw)
            md_sig = extract_math_signature(md_answer)
            if sheet_sig != md_sig:
                errors.append(
                    f"Cross-file final answer mismatch between Snorkl MD (`{md_answer}`) "
                    f"and Teacher Sheet visible answer (`{strip_known_html_tags(visible_ans_raw).strip()}`)."
                )

        if browser:
            tdir = tempfile.mkdtemp(prefix="snorkl_val_sheet_")
            try:
                eff = prepare_resolved_html(os.path.abspath(sheet_html_path), tdir)
                ok_dom, msg = audit_dom_headless(browser, pathlib.Path(eff).as_uri(), 794, 1123, tdir)
                if not ok_dom:
                    errors.append(f"Teacher Sheet HTML DOM audit failed: {msg}")
            finally:
                shutil.rmtree(tdir, ignore_errors=True)

    if card_sha and sheet_sha and card_sha != sheet_sha:
        errors.append(
            f"Canonical ProblemSpec digest mismatch between Card HTML ({card_sha}) and Sheet HTML ({sheet_sha})."
        )

    return len(errors) == 0, errors


def _discover_paths_in_dir(directory: str, slug: str | None = None) -> tuple[str, str, str, str | None, str | None, str | None]:
    d = os.path.abspath(directory)
    if slug:
        png = os.path.join(d, f"{slug}_문제등록화면.png")
        md = os.path.join(d, f"{slug}_정답_평가기준.md")
        txt = os.path.join(d, f"{slug}_정답_평가기준.txt")
        pdf = os.path.join(d, f"{slug}_교사참고용_채점기준표.pdf")
        c_html = os.path.join(d, f"{slug}_card.html")
        s_html = os.path.join(d, f"{slug}_sheet.html")
        return (
            png,
            md,
            pdf,
            txt if os.path.isfile(txt) else None,
            c_html if os.path.isfile(c_html) else None,
            s_html if os.path.isfile(s_html) else None,
        )

    files = os.listdir(d)
    pngs = [os.path.join(d, f) for f in files if f.endswith("_문제등록화면.png")]
    mds = [os.path.join(d, f) for f in files if f.endswith("_정답_평가기준.md")]
    pdfs = [os.path.join(d, f) for f in files if f.endswith("_교사참고용_채점기준표.pdf")]
    if len(pngs) != 1 or len(mds) != 1 or len(pdfs) != 1:
        raise ValueError(
            f"Expected exactly 1 set of deliverables in {d}, found PNG={len(pngs)}, MD={len(mds)}, PDF={len(pdfs)}. "
            "Pass --slug <문제제목> to disambiguate."
        )
    inferred_slug = os.path.basename(pngs[0])[: -len("_문제등록화면.png")]
    txt = os.path.join(d, f"{inferred_slug}_정답_평가기준.txt")
    c_html = os.path.join(d, f"{inferred_slug}_card.html")
    s_html = os.path.join(d, f"{inferred_slug}_sheet.html")
    return (
        pngs[0],
        mds[0],
        pdfs[0],
        txt if os.path.isfile(txt) else None,
        c_html if os.path.isfile(c_html) else None,
        s_html if os.path.isfile(s_html) else None,
    )


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Validate Snorkl Rubric Architect 4-file deliverable set.")
    parser.add_argument("target_dir", help="Directory containing generated deliverables")
    parser.add_argument("--slug", default=None, help="Problem filename prefix (optional if 1 set in folder)")
    parser.add_argument("--max-pages", type=int, default=3, help="Max allowed PDF pages (default: 3)")
    parser.add_argument("--skip-dom", action="store_true", help="Skip headless browser DOM audit")
    parser.add_argument(
        "--allow-missing-html",
        action="store_true",
        help="Allow validating standalone PNG/MD/TXT/PDF without `_card.html` and `_sheet.html`",
    )
    args = parser.parse_args(argv)

    try:
        png, md, pdf, txt, c_html, s_html = _discover_paths_in_dir(args.target_dir, args.slug)
    except Exception as e:
        print(f"[Validator Error] {e}", file=sys.stderr)
        return 1

    ok, errors = validate_deliverable_set(
        png_path=png,
        md_path=md,
        pdf_path=pdf,
        txt_path=txt,
        card_html_path=c_html,
        sheet_html_path=s_html,
        max_pdf_pages=args.max_pages,
        check_dom=not args.skip_dom,
        require_html=not args.allow_missing_html,
    )
    if ok:
        print(f"[Validator OK] All deliverables verified cleanly in: {os.path.abspath(args.target_dir)}")
        return 0

    print("[Validator FAILED] Deliverable verification errors:", file=sys.stderr)
    for err in errors:
        print(f"  - {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
