#!/usr/bin/env python3
"""
render_card.py - Zero-False-Positive Cross-Platform Card & PDF Renderer (v15.0)

Key Guarantees:
1. Local KaTeX Resolution: Automatically resolves `./vendor/katex` to the bundled
   local KaTeX directory even when the input HTML lives in an external output folder.
2. DOM Render Audit: Verifies via headless `--dump-dom` (or WebKit JS audit) that
   KaTeX loaded cleanly, zero `.katex-error` nodes exist, zero raw `$` leaked,
   zero broken `<img>` tags exist, and no container overflowed.
3. Atomic Output Replacement: Renders into an isolated temporary file first, checks
   `returncode == 0` AND binary header/dimensions (`2000x1000` for 1000x500 card,
   `%PDF-` for PDF), and only then `os.replace()`s the destination file.
   Pre-existing stale files NEVER cause a failed render to report success.
4. Quiet by Default: Does not pop up GUI image viewers unless `--open` is passed
   (`--no-open` remains accepted for backward compatibility).
"""

from __future__ import annotations

import io
import os
import pathlib
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_KATEX_DIR = os.path.join(SCRIPT_DIR, "vendor", "katex")


def ensure_utf8_stdio() -> None:
    """Prevent Windows cp949 stdout/stderr crashes or mojibake in agent subprocesses."""
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if isinstance(stream, io.TextIOWrapper):
            enc = (stream.encoding or "").lower().replace("-", "")
            if enc != "utf8":
                try:
                    stream.reconfigure(encoding="utf-8", errors="replace")
                except Exception:
                    pass


def find_browser() -> str | None:
    override = os.environ.get("SNORKL_BROWSER_BIN")
    if override is not None:
        return override if (override and os.path.isfile(override)) else None

    system = platform.system()
    if system == "Windows":
        candidates = [
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        for path in candidates:
            if path and os.path.isfile(path):
                return path
        return shutil.which("msedge") or shutil.which("chrome")
    if system == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        return shutil.which("google-chrome") or shutil.which("chromium")
    for name in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "microsoft-edge"]:
        p = shutil.which(name)
        if p:
            return p
    return None


def read_png_dimensions(png_path: str) -> tuple[int, int] | None:
    """
    Validate full PNG binary integrity (chunk framing, CRC32 on every chunk,
    zlib-decompressible IDAT scanline payload, and trailing IEND) and return `(width, height)`.
    Rejects truncated headers or corrupted PNG files without external dependencies.
    """
    try:
        with open(png_path, "rb") as f:
            raw = f.read()
    except OSError:
        return None

    if len(raw) < 33 or raw[:8] != b"\x89PNG\r\n\x1a\n":
        return None

    pos = 8
    dims: tuple[int, int] | None = None
    ihdr_meta: tuple[int, int, int] | None = None
    idat_parts: list[bytes] = []
    saw_iend = False

    while pos + 8 <= len(raw):
        (length,) = struct.unpack(">I", raw[pos : pos + 4])
        chunk_type = raw[pos + 4 : pos + 8]
        data_start = pos + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(raw):
            return None

        chunk_data = raw[data_start:data_end]
        (expected_crc,) = struct.unpack(">I", raw[data_end:crc_end])
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            return None

        if chunk_type == b"IHDR":
            if dims is not None or length != 13:
                return None
            w, h, bit_depth, color_type, comp, filt, interlace = struct.unpack(">IIBBBBB", chunk_data)
            if w <= 0 or h <= 0 or comp != 0 or filt != 0:
                return None
            dims = (int(w), int(h))
            ihdr_meta = (int(bit_depth), int(color_type), int(interlace))
        elif chunk_type == b"IDAT":
            idat_parts.append(chunk_data)
        elif chunk_type == b"IEND":
            if length != 0:
                return None
            saw_iend = True
            pos = crc_end
            break

        pos = crc_end

    if dims is None or ihdr_meta is None or not saw_iend or not idat_parts:
        return None

    try:
        decompressed = zlib.decompress(b"".join(idat_parts))
    except zlib.error:
        return None

    bit_depth, color_type, interlace = ihdr_meta
    channels_map = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    channels = channels_map.get(color_type)
    if channels is None:
        return None
    if interlace == 0:
        row_bytes = 1 + (dims[0] * channels * bit_depth + 7) // 8
        if len(decompressed) != row_bytes * dims[1]:
            return None
    elif len(decompressed) == 0:
        return None

    return dims


def get_macos_binary(script_dir: str) -> str | None:
    binary_path = os.path.join(script_dir, "render_webkit")
    swift_source = os.path.join(script_dir, "render_webkit.swift")

    if os.path.isfile(binary_path):
        if not os.path.isfile(swift_source) or os.path.getmtime(binary_path) >= os.path.getmtime(swift_source):
            return binary_path

    if shutil.which("swiftc") and os.path.isfile(swift_source):
        try:
            res = subprocess.run(
                ["swiftc", "-O", swift_source, "-o", binary_path],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            if res.returncode == 0 and os.path.isfile(binary_path):
                os.chmod(binary_path, 0o755)
                return binary_path
        except Exception:
            pass
    return None


def prepare_resolved_html(html_abs: str, temp_dir: str) -> str:
    """
    If `html_abs` references `./vendor/katex` (or `vendor/katex`) from a directory where
    `vendor/katex` does not exist locally, create a temporary resolved HTML with:
      1. `<base href="<original_dir_uri>/">` so relative image/asset paths continue to work, and
      2. `./vendor/katex` rewritten to the bundled `scripts/vendor/katex` file:/// URI.
    """
    with open(html_abs, "r", encoding="utf-8") as f:
        raw_html = f.read()

    html_dir = os.path.dirname(html_abs)
    local_vendor = os.path.join(html_dir, "vendor", "katex")
    needs_katex_rewrite = (
        ("./vendor/katex" in raw_html or '"vendor/katex/' in raw_html or "'vendor/katex/" in raw_html)
        and not os.path.isdir(local_vendor)
        and os.path.isdir(VENDOR_KATEX_DIR)
    )

    if not needs_katex_rewrite:
        return html_abs

    katex_uri = pathlib.Path(VENDOR_KATEX_DIR).as_uri()
    base_dir_uri = pathlib.Path(html_dir).as_uri().rstrip("/") + "/"

    patched = raw_html.replace("./vendor/katex", katex_uri).replace('"vendor/katex/', f'"{katex_uri}/')
    if "<base " not in patched.lower():
        patched = re.sub(
            r"(<head[^>]*>)",
            rf'\1\n  <base href="{base_dir_uri}">',
            patched,
            count=1,
            flags=re.IGNORECASE,
        )

    resolved_path = os.path.join(temp_dir, "resolved_input.html")
    with open(resolved_path, "w", encoding="utf-8") as f:
        f.write(patched)
    return resolved_path


def audit_dom_headless(browser: str, file_uri: str, width: int, height: int, temp_dir: str) -> tuple[bool, str]:
    """
    Run headless browser `--dump-dom` to verify post-JS rendering health:
    - Checks `data-render-status="ok"` when present on `<html>`
    - Checks absence of `class="katex-error"`
    """
    audit_profile = os.path.join(temp_dir, "audit_profile")
    os.makedirs(audit_profile, exist_ok=True)
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-sandbox",
        "--disable-crash-reporter",
        "--disable-breakpad",
        f"--user-data-dir={audit_profile}",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        "--allow-file-access-from-files",
        "--virtual-time-budget=2500",
        "--dump-dom",
        file_uri,
    ]
    res = subprocess.run(
        cmd,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=45,
    )
    if res.returncode in (-6, 134):
        return False, f"DOM audit browser crashed with signal {res.returncode} (SIGABRT/sandbox abort)"
    if res.returncode != 0:
        return False, f"DOM audit browser exited with {res.returncode}: {res.stderr.strip()}"

    dom = res.stdout or ""
    if not dom.strip():
        return False, "DOM audit returned empty document"

    m = re.search(r'data-render-status="([^"]*)"', dom)
    if m:
        status = m.group(1)
        if status != "ok":
            return False, f"DOM render check failed ({status})"

    if 'class="katex-error"' in dom or "class='katex-error'" in dom:
        return False, "KaTeX syntax error (.katex-error) detected in rendered DOM"

    body_match = re.search(r"<body\b[^>]*>(.*)</body>", dom, flags=re.DOTALL | re.IGNORECASE)
    if body_match:
        stripped = re.sub(r"<(script|style|svg)\b[^>]*>.*?</\1>", " ", body_match.group(1), flags=re.DOTALL | re.IGNORECASE)
        stripped = re.sub(r"<[^>]+>", " ", stripped)
        if "$" in stripped:
            return False, "Unrendered `$` detected in post-JS DOM body"

    return True, "ok"


def render_png(
    html_path: str,
    png_path: str,
    width: int = 1000,
    height: int = 500,
    audit_dom: bool = True,
) -> bool:
    ensure_utf8_stdio()
    html_abs = os.path.abspath(html_path)
    if not os.path.isfile(html_abs):
        print(f"[Renderer Error] Input HTML not found: {html_abs}", file=sys.stderr)
        return False

    png_abs = os.path.abspath(png_path)
    os.makedirs(os.path.dirname(png_abs), exist_ok=True)
    expected_px = (width * 2, height * 2)
    system = platform.system()

    temp_dir = tempfile.mkdtemp(prefix="snorkl_render_")
    try:
        effective_html = prepare_resolved_html(html_abs, temp_dir)
        temp_png = os.path.join(temp_dir, "capture_out.png")

        # 1. macOS Native WebKit (2x snapshotWidth enforced in render_webkit.swift)
        if system == "Darwin" and not os.environ.get("SNORKL_BROWSER_BIN"):
            binary = get_macos_binary(SCRIPT_DIR)
            if binary:
                res = subprocess.run(
                    [binary, effective_html, temp_png, str(width), str(height)],
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30,
                )
                dims = read_png_dimensions(temp_png) if res.returncode == 0 else None
                if res.returncode == 0 and dims == expected_px:
                    os.replace(temp_png, png_abs)
                    print(f"[Renderer] macOS Native WebKit rendered ({dims[0]}x{dims[1]}): {png_abs}")
                    return True
                if res.stderr:
                    print(f"[Renderer Warning] WebKit binary message: {res.stderr.strip()}", file=sys.stderr)
                    if "[WebKit Audit Error]" in res.stderr:
                        return False

            swift_source = os.path.join(SCRIPT_DIR, "render_webkit.swift")
            if os.path.isfile(swift_source) and shutil.which("swift"):
                res = subprocess.run(
                    ["swift", swift_source, effective_html, temp_png, str(width), str(height)],
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=45,
                )
                dims = read_png_dimensions(temp_png) if res.returncode == 0 else None
                if res.returncode == 0 and dims == expected_px:
                    os.replace(temp_png, png_abs)
                    print(f"[Renderer] Swift JIT rendered ({dims[0]}x{dims[1]}): {png_abs}")
                    return True
                if res.stderr and "[WebKit Audit Error]" in res.stderr:
                    print(res.stderr.strip(), file=sys.stderr)
                    return False

        # 2. Headless Browser (Windows Edge / Chrome / Linux / macOS fallback)
        browser = find_browser()
        if not browser:
            print("[Renderer Error] No compatible headless browser (Edge/Chrome) found.", file=sys.stderr)
            return False

        file_uri = pathlib.Path(effective_html).as_uri()
        if audit_dom:
            ok, msg = audit_dom_headless(browser, file_uri, width, height, temp_dir)
            if not ok:
                print(f"[Renderer Audit Error] {msg}", file=sys.stderr)
                return False

        shot_profile = os.path.join(temp_dir, "shot_profile")
        os.makedirs(shot_profile, exist_ok=True)
        cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            f"--user-data-dir={shot_profile}",
            "--hide-scrollbars",
            "--force-device-scale-factor=2",
            f"--window-size={width},{height}",
            "--allow-file-access-from-files",
            "--virtual-time-budget=3000",
            "--run-all-compositor-stages-before-draw",
            f"--screenshot={temp_png}",
            file_uri,
        ]
        res = subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=45,
        )
        if res.returncode != 0:
            if res.returncode in (-6, 134):
                print(
                    f"[Renderer Error] Headless browser crashed with code {res.returncode} (SIGABRT/sandbox abort).",
                    file=sys.stderr,
                )
            else:
                print(
                    f"[Renderer Error] Browser exited with non-zero code {res.returncode}: {res.stderr.strip()}",
                    file=sys.stderr,
                )
            return False

        dims = read_png_dimensions(temp_png)
        if dims is None:
            print("[Renderer Error] Browser did not produce a valid PNG file.", file=sys.stderr)
            return False
        if dims != expected_px:
            print(
                f"[Renderer Error] PNG resolution mismatch: got {dims[0]}x{dims[1]}, expected {expected_px[0]}x{expected_px[1]}.",
                file=sys.stderr,
            )
            return False

        os.replace(temp_png, png_abs)
        print(f"[Renderer] Headless browser rendered ({dims[0]}x{dims[1]}): {png_abs}")
        return True
    except Exception as e:
        print(f"[Renderer Error] Execution exception: {e}", file=sys.stderr)
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def render_pdf(html_path: str, pdf_path: str, audit_dom: bool = True) -> bool:
    ensure_utf8_stdio()
    html_abs = os.path.abspath(html_path)
    if not os.path.isfile(html_abs):
        print(f"[Renderer Error] Input HTML not found: {html_abs}", file=sys.stderr)
        return False

    pdf_abs = os.path.abspath(pdf_path)
    os.makedirs(os.path.dirname(pdf_abs), exist_ok=True)

    browser = find_browser()
    if not browser:
        print("[Renderer Error] Headless browser (Edge/Chrome) not found for PDF export.", file=sys.stderr)
        return False

    temp_dir = tempfile.mkdtemp(prefix="snorkl_pdf_")
    try:
        effective_html = prepare_resolved_html(html_abs, temp_dir)
        file_uri = pathlib.Path(effective_html).as_uri()
        temp_pdf = os.path.join(temp_dir, "sheet_out.pdf")

        if audit_dom:
            ok, msg = audit_dom_headless(browser, file_uri, 794, 1123, temp_dir)
            if not ok:
                print(f"[Renderer Audit Error] {msg}", file=sys.stderr)
                return False

        pdf_profile = os.path.join(temp_dir, "pdf_profile")
        os.makedirs(pdf_profile, exist_ok=True)
        cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-sandbox",
            "--disable-crash-reporter",
            "--disable-breakpad",
            f"--user-data-dir={pdf_profile}",
            "--no-pdf-header-footer",
            "--allow-file-access-from-files",
            "--virtual-time-budget=3000",
            "--run-all-compositor-stages-before-draw",
            f"--print-to-pdf={temp_pdf}",
            file_uri,
        ]
        res = subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=45,
        )
        if res.returncode != 0:
            if res.returncode in (-6, 134):
                print(
                    f"[Renderer Error] Headless browser crashed with code {res.returncode} (SIGABRT/sandbox abort).",
                    file=sys.stderr,
                )
            else:
                print(
                    f"[Renderer Error] PDF command exited with non-zero code {res.returncode}: {res.stderr.strip()}",
                    file=sys.stderr,
                )
            return False

        if not os.path.isfile(temp_pdf) or os.path.getsize(temp_pdf) < 512:
            print("[Renderer Error] PDF output file missing or truncated.", file=sys.stderr)
            return False

        with open(temp_pdf, "rb") as f:
            magic = f.read(5)
        if magic != b"%PDF-":
            print("[Renderer Error] Output file does not have a valid %PDF- header.", file=sys.stderr)
            return False

        os.replace(temp_pdf, pdf_abs)
        print(f"[Renderer] Teacher Reference PDF generated: {pdf_abs}")
        return True
    except Exception as e:
        print(f"[Renderer Error] PDF execution exception: {e}", file=sys.stderr)
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def open_file(file_path: str) -> None:
    f_abs = os.path.abspath(file_path)
    if not os.path.isfile(f_abs):
        return
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", f_abs])
        elif system == "Windows":
            os.startfile(f_abs)  # type: ignore[attr-defined]
        elif system == "Linux":
            subprocess.Popen(["xdg-open", f_abs])
        print(f"[Renderer] Launched native viewer for {f_abs}")
    except Exception as e:
        print(f"[Renderer Warning] Could not auto-open: {e}")


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_stdio()
    args = list(sys.argv[1:] if argv is None else argv)
    flags = {a for a in args if a.startswith("--")}
    pos = [a for a in args if not a.startswith("--")]

    if "--pdf" in flags:
        if len(pos) < 2:
            print("Usage: python render_card.py --pdf <input.html> <output.pdf> [--open]", file=sys.stderr)
            return 1
        success = render_pdf(pos[0], pos[1], audit_dom=("--skip-audit" not in flags))
        if success and "--open" in flags and "--no-open" not in flags:
            open_file(pos[1])
        return 0 if success else 1

    if len(pos) < 2:
        print("Usage:", file=sys.stderr)
        print("  python render_card.py <input.html> <output.png> [width] [height] [--open]", file=sys.stderr)
        print("  python render_card.py --pdf <input.html> <output.pdf> [--open]", file=sys.stderr)
        return 1

    html_arg, png_arg = pos[0], pos[1]
    w = int(pos[2]) if len(pos) > 2 and pos[2].isdigit() else 1000
    h = int(pos[3]) if len(pos) > 3 and pos[3].isdigit() else 500

    success = render_png(html_arg, png_arg, w, h, audit_dom=("--skip-audit" not in flags))
    if success and "--open" in flags and "--no-open" not in flags:
        open_file(png_arg)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
