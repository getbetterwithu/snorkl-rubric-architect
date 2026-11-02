#!/usr/bin/env python3
"""
render_card.py - High-Speed Cross-Platform Problem Card & PDF Renderer (v14.0)
Capabilities:
  1. PNG Problem Card Rendering (2000x1000):
     - macOS: High-speed native WebKit binary (render_webkit)
     - Windows: Microsoft Edge (msedge.exe) headless
     - Auto-opens native viewer (open / os.startfile)
  2. Teacher Reference A4 PDF Generation:
     - Cross-platform headless browser --print-to-pdf
"""

import sys
import os
import platform
import subprocess
import shutil

def find_browser():
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
            if os.path.isfile(path):
                return path
        return shutil.which("msedge") or shutil.which("chrome")
    elif system == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        return shutil.which("google-chrome") or shutil.which("chromium")
    else: # Linux
        for name in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "microsoft-edge"]:
            p = shutil.which(name)
            if p:
                return p
    return None

def get_macos_binary(script_dir):
    binary_path = os.path.join(script_dir, "render_webkit")
    swift_source = os.path.join(script_dir, "render_webkit.swift")
    
    if os.path.isfile(binary_path):
        if not os.path.isfile(swift_source) or os.path.getmtime(binary_path) >= os.path.getmtime(swift_source):
            return binary_path

    if shutil.which("swiftc") and os.path.isfile(swift_source):
        try:
            res = subprocess.run(["swiftc", "-O", swift_source, "-o", binary_path], capture_output=True, text=True)
            if res.returncode == 0 and os.path.isfile(binary_path):
                os.chmod(binary_path, 0o755)
                return binary_path
        except Exception:
            pass

    return None

def render_png(html_path, png_path, width=1000, height=500):
    html_abs = os.path.abspath(html_path)
    png_abs = os.path.abspath(png_path)
    os.makedirs(os.path.dirname(png_abs), exist_ok=True)
    system = platform.system()

    # 1. macOS High-Speed WebKit
    if system == "Darwin":
        script_dir = os.path.dirname(os.path.abspath(__file__))
        binary = get_macos_binary(script_dir)
        if binary:
            res = subprocess.run([binary, html_abs, png_abs, str(width), str(height)], capture_output=True, text=True)
            if res.returncode == 0 and os.path.isfile(png_abs):
                print(f"[Renderer] macOS Native WebKit rendered: {png_abs}")
                return True
        
        swift_source = os.path.join(script_dir, "render_webkit.swift")
        if os.path.isfile(swift_source) and shutil.which("swift"):
            res = subprocess.run(["swift", swift_source, html_abs, png_abs, str(width), str(height)], capture_output=True, text=True)
            if res.returncode == 0 and os.path.isfile(png_abs):
                print(f"[Renderer] Swift JIT rendered: {png_abs}")
                return True

    # 2. Browser Headless (Windows Edge / Chrome / Linux)
    browser = find_browser()
    if browser:
        file_url = "file:///" + html_abs.replace("\\", "/") if system == "Windows" else "file://" + html_abs
        cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=2",
            f"--window-size={width},{height}",
            "--allow-file-access-from-files",
            f"--screenshot={png_abs}",
            file_url
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.isfile(png_abs):
            print(f"[Renderer] Headless browser rendered: {png_abs}")
            return True

    print(f"[Renderer Error] Could not render PNG from {html_path}", file=sys.stderr)
    return False

def render_pdf(html_path, pdf_path):
    html_abs = os.path.abspath(html_path)
    pdf_abs = os.path.abspath(pdf_path)
    os.makedirs(os.path.dirname(pdf_abs), exist_ok=True)
    system = platform.system()

    browser = find_browser()
    if not browser:
        print("[Renderer Warning] Headless browser not found for PDF export.", file=sys.stderr)
        return False

    file_url = "file:///" + html_abs.replace("\\", "/") if system == "Windows" else "file://" + html_abs
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_abs}",
        file_url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.isfile(pdf_abs):
        print(f"[Renderer] Teacher Reference PDF generated: {pdf_abs}")
        return True
    else:
        print(f"[Renderer Error] PDF generation failed: {res.stderr}", file=sys.stderr)
        return False

def open_file(file_path):
    f_abs = os.path.abspath(file_path)
    if not os.path.isfile(f_abs):
        return
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", f_abs])
        elif system == "Windows":
            os.startfile(f_abs)
        elif system == "Linux":
            subprocess.Popen(["xdg-open", f_abs])
        print(f"[Renderer] Launched native viewer for {f_abs}")
    except Exception as e:
        print(f"[Renderer Warning] Could not auto-open: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python3 render_card.py <input.html> <output.png> [width] [height] [--no-open]")
        print("  python3 render_card.py --pdf <input.html> <output.pdf>")
        sys.exit(1)
    
    if sys.argv[1] == "--pdf":
        html_arg = sys.argv[2]
        pdf_arg = sys.argv[3]
        success = render_pdf(html_arg, pdf_arg)
        sys.exit(0 if success else 1)
    else:
        html_arg = sys.argv[1]
        png_arg = sys.argv[2]
        w = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 1000
        h = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else 500
        no_open = "--no-open" in sys.argv

        success = render_png(html_arg, png_arg, w, h)
        if success and not no_open:
            open_file(png_arg)
        sys.exit(0 if success else 1)
