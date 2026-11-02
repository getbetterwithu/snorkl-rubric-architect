#!/usr/bin/env python3
"""
render_card.py - Cross-Platform Lossless Problem Card Renderer (v13.0)
Supports:
  - macOS: Headless WebKit (render_webkit.swift) or Chromium/Edge fallback
  - Windows: Microsoft Edge (msedge.exe) or Google Chrome headless
  - Linux: Chromium or Chrome headless
Auto-pops up OS native image viewer:
  - macOS: `open <file.png>`
  - Windows: `os.startfile(<file.png>)` or `start`
  - Linux: `xdg-open <file.png>`
"""

import sys
import os
import platform
import subprocess
import shutil

def find_windows_browser():
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
    which_edge = shutil.which("msedge") or shutil.which("chrome")
    return which_edge

def find_linux_browser():
    for name in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "microsoft-edge"]:
        path = shutil.which(name)
        if path:
            return path
    return None

def render(html_path, png_path, width=1000, height=500):
    html_abs = os.path.abspath(html_path)
    png_abs = os.path.abspath(png_path)
    os.makedirs(os.path.dirname(png_abs), exist_ok=True)
    system = platform.system()

    # 1. macOS with Swift WebKit
    if system == "Darwin":
        script_dir = os.path.dirname(os.path.abspath(__file__))
        swift_script = os.path.join(script_dir, "render_webkit.swift")
        if os.path.exists(swift_script) and shutil.which("swift"):
            cmd = ["swift", swift_script, html_abs, png_abs, str(width), str(height)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and os.path.isfile(png_abs):
                print(f"[Renderer] macOS WebKit rendered successfully: {png_abs}")
                return True
            else:
                print(f"[Renderer] Swift WebKit failed: {res.stderr}. Trying browser fallback...")

    # 2. Windows using native Microsoft Edge or Chrome headless
    if system == "Windows":
        browser = find_windows_browser()
        if not browser:
            print("[Renderer Error] Microsoft Edge or Google Chrome not found on Windows.", file=sys.stderr)
            return False
        
        file_url = "file:///" + html_abs.replace("\\", "/")
        cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--window-size={width * 2},{height * 2}",
            f"--screenshot={png_abs}",
            file_url
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.isfile(png_abs):
            print(f"[Renderer] Windows Edge/Chrome rendered successfully: {png_abs}")
            return True
        else:
            print(f"[Renderer Error] Headless browser execution failed: {res.stderr}", file=sys.stderr)
            return False

    # 3. Linux / macOS fallback using Chromium
    browser = find_linux_browser()
    if browser:
        file_url = "file://" + html_abs
        cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--window-size={width * 2},{height * 2}",
            f"--screenshot={png_abs}",
            file_url
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.isfile(png_abs):
            print(f"[Renderer] Browser headless rendered: {png_abs}")
            return True

    print(f"[Renderer Error] Could not render {html_path} to PNG on {system}.", file=sys.stderr)
    return False

def open_image(png_path):
    png_abs = os.path.abspath(png_path)
    if not os.path.isfile(png_abs):
        return
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", png_abs])
        elif system == "Windows":
            os.startfile(png_abs)
        elif system == "Linux":
            subprocess.Popen(["xdg-open", png_abs])
        print(f"[Renderer] Launched native viewer for {png_abs}")
    except Exception as e:
        print(f"[Renderer Warning] Could not auto-open viewer: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 render_card.py <input.html> <output.png> [width] [height] [--no-open]")
        sys.exit(1)
    
    html_arg = sys.argv[1]
    png_arg = sys.argv[2]
    w = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 1000
    h = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else 500
    no_open = "--no-open" in sys.argv

    success = render(html_arg, png_arg, w, h)
    if success and not no_open:
        open_image(png_arg)
    sys.exit(0 if success else 1)
