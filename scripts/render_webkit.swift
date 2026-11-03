import Foundation
import WebKit
import AppKit

guard CommandLine.arguments.count >= 3 else {
    fputs("Usage: swift render_webkit.swift <input_html> <output_png> [width] [height]\n", stderr)
    exit(1)
}

let inputPath = CommandLine.arguments[1]
let outputPath = CommandLine.arguments[2]
let width = CommandLine.arguments.count >= 4 ? (Double(CommandLine.arguments[3]) ?? 1000.0) : 1000.0
let height = CommandLine.arguments.count >= 5 ? (Double(CommandLine.arguments[4]) ?? 500.0) : 500.0

let app = NSApplication.shared

class RenderDelegate: NSObject, WKNavigationDelegate {
    let webView: WKWebView
    let outputPath: String
    let width: Double
    let height: Double
    var pollAttempts: Int = 0

    init(webView: WKWebView, outputPath: String, width: Double, height: Double) {
        self.webView = webView
        self.outputPath = outputPath
        self.width = width
        self.height = height
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        fputs("[WebKit Error] Navigation failed: \(error.localizedDescription)\n", stderr)
        exit(1)
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        fputs("[WebKit Error] Provisional navigation failed: \(error.localizedDescription)\n", stderr)
        exit(1)
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        pollReadiness()
    }

    private func pollReadiness() {
        pollAttempts += 1
        let js = "(function(){ return JSON.stringify({ready: document.documentElement.dataset.renderReady || '', status: document.documentElement.dataset.renderStatus || ''}); })()"
        webView.evaluateJavaScript(js) { result, _ in
            var isReady = false
            var status = ""
            if let jsonStr = result as? String,
               let data = jsonStr.data(using: .utf8),
               let obj = try? JSONSerialization.jsonObject(with: data) as? [String: String] {
                isReady = (obj["ready"] == "true")
                status = obj["status"] ?? ""
            }

            if !isReady && self.pollAttempts < 25 {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                    self.pollReadiness()
                }
                return
            }

            if !status.isEmpty && status != "ok" {
                fputs("[WebKit Audit Error] \(status)\n", stderr)
                exit(1)
            }

            self.captureSnapshot()
        }
    }

    private func captureSnapshot() {
        let config = WKSnapshotConfiguration()
        config.rect = CGRect(x: 0, y: 0, width: self.width, height: self.height)
        // Force exact 2x Retina pixel width (e.g. 2000px for 1000px logical width) even on 1x displays
        config.snapshotWidth = NSNumber(value: Int(self.width * 2.0))

        self.webView.takeSnapshot(with: config) { image, error in
            if let error = error {
                fputs("[WebKit Error] Snapshot error: \(error.localizedDescription)\n", stderr)
                exit(1)
            }
            guard let image = image,
                  let tiff = image.tiffRepresentation,
                  let bitmap = NSBitmapImageRep(data: tiff),
                  let png = bitmap.representation(using: .png, properties: [:]) else {
                fputs("[WebKit Error] Failed to encode snapshot as PNG\n", stderr)
                exit(1)
            }
            let tempPath = self.outputPath + ".tmp.\(ProcessInfo.processInfo.processIdentifier)"
            let tempURL = URL(fileURLWithPath: tempPath)
            let finalURL = URL(fileURLWithPath: self.outputPath)
            do {
                try png.write(to: tempURL, options: .atomic)
                if FileManager.default.fileExists(atPath: self.outputPath) {
                    _ = try FileManager.default.replaceItemAt(finalURL, withItemAt: tempURL)
                } else {
                    try FileManager.default.moveItem(at: tempURL, to: finalURL)
                }
                print("[WebKit] Rendered \(bitmap.pixelsWide)x\(bitmap.pixelsHigh) PNG to \(self.outputPath)")
                exit(0)
            } catch {
                try? FileManager.default.removeItem(at: tempURL)
                fputs("[WebKit Error] Failed to save PNG: \(error.localizedDescription)\n", stderr)
                exit(1)
            }
        }
    }
}

let webConfig = WKWebViewConfiguration()
let frame = CGRect(x: 0, y: 0, width: width, height: height)
let webView = WKWebView(frame: frame, configuration: webConfig)
let delegate = RenderDelegate(webView: webView, outputPath: outputPath, width: width, height: height)
webView.navigationDelegate = delegate

let fileURL = URL(fileURLWithPath: inputPath)
// Allow reading local vendor assets (KaTeX fonts/scripts) and sibling PNG previews
let readRootURL = URL(fileURLWithPath: "/")
webView.loadFileURL(fileURL, allowingReadAccessTo: readRootURL)

RunLoop.main.run(until: Date(timeIntervalSinceNow: 8.0))
fputs("[WebKit Error] Render timeout exceeded (8.0s)\n", stderr)
exit(1)
