import Foundation
import WebKit
import AppKit

guard CommandLine.arguments.count >= 4 else {
    print("Usage: swift render_webkit.swift <input_svg_or_html> <output_png> <width> <height>")
    exit(1)
}

let inputPath = CommandLine.arguments[1]
let outputPath = CommandLine.arguments[2]
let width = Double(CommandLine.arguments[3]) ?? 1000.0
let height = Double(CommandLine.arguments[4]) ?? 500.0

let app = NSApplication.shared

class RenderDelegate: NSObject, WKNavigationDelegate {
    let webView: WKWebView
    let outputPath: String
    let width: Double
    let height: Double

    init(webView: WKWebView, outputPath: String, width: Double, height: Double) {
        self.webView = webView
        self.outputPath = outputPath
        self.width = width
        self.height = height
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            let config = WKSnapshotConfiguration()
            config.rect = CGRect(x: 0, y: 0, width: self.width, height: self.height)
            self.webView.takeSnapshot(with: config) { image, error in
                if let error = error {
                    print("Snapshot error: \(error)")
                    exit(1)
                }
                guard let image = image,
                      let tiff = image.tiffRepresentation,
                      let bitmap = NSBitmapImageRep(data: tiff),
                      let png = bitmap.representation(using: .png, properties: [:]) else {
                    print("Failed to convert image to PNG")
                    exit(1)
                }
                do {
                    try png.write(to: URL(fileURLWithPath: self.outputPath))
                    print("Successfully rendered to \(self.outputPath)")
                    exit(0)
                } catch {
                    print("Failed to save PNG: \(error)")
                    exit(1)
                }
            }
        }
    }
}

let config = WKWebViewConfiguration()
let frame = CGRect(x: 0, y: 0, width: width, height: height)
let webView = WKWebView(frame: frame, configuration: config)
let delegate = RenderDelegate(webView: webView, outputPath: outputPath, width: width, height: height)
webView.navigationDelegate = delegate

let fileURL = URL(fileURLWithPath: inputPath)
webView.loadFileURL(fileURL, allowingReadAccessTo: fileURL.deletingLastPathComponent())

RunLoop.main.run(until: Date(timeIntervalSinceNow: 5.0))
print("Timeout")
exit(1)
