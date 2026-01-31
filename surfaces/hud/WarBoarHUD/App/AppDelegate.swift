import AppKit
import SwiftUI

final class AppDelegate: NSObject, NSApplicationDelegate {
    private var panelController: PanelController?

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Verify mock manifest parses (Phase 2 exit gate)
        verifyMockManifestParsing()

        // Create and show the HUD panel
        panelController = PanelController()
        panelController?.showPanel()

        // Hide dock icon (menu bar app style)
        NSApp.setActivationPolicy(.accessory)
    }

    /// Phase 2 Exit Gate: Verify MockManifest.json parses without error
    private func verifyMockManifestParsing() {
        #if DEBUG
        // Try loading from bundle first
        if let bundleURL = Bundle.main.url(forResource: "MockManifest", withExtension: "json") {
            do {
                let manifest = try ManifestParser.parse(fileURL: bundleURL)
                print("✅ MockManifest.json parsed successfully!")
                print("   Schema version: \(manifest.meta.schemaVersion)")
                print("   Session: \(manifest.session.kz) (active: \(manifest.session.active))")
                print("   Portfolio: \(manifest.portfolio.formattedBalance)")
                print("   Live positions: \(manifest.livePositions.count)")
                print("   Recent trades: \(manifest.recentTrades.items.count)")
                print("   Gates: \(manifest.gatesSummary.count)")
                print("   Health: \(manifest.health.overall.rawValue)")
                print("   Lease: \(manifest.lease.status.rawValue)")
            } catch {
                print("❌ MockManifest.json parse FAILED: \(error)")
            }
        } else {
            // Fallback: try file system directly (for development)
            let devPath = "/Users/echopeso/phoenix-hud/WarBoarHUD/Preview Content/MockManifest.json"
            let devURL = URL(fileURLWithPath: devPath)
            do {
                let manifest = try ManifestParser.parse(fileURL: devURL)
                print("✅ MockManifest.json parsed from dev path!")
                print("   Schema version: \(manifest.meta.schemaVersion)")
                print("   Health: \(manifest.health.overall.rawValue)")
            } catch {
                print("⚠️ MockManifest.json not in bundle and dev path failed: \(error)")
                print("   Using preview manifest instead")
                let preview = ManifestParser.previewManifest
                print("   Preview schema version: \(preview.meta.schemaVersion)")
            }
        }
        #endif
    }

    func applicationWillTerminate(_ notification: Notification) {
        panelController?.closePanel()
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        // Keep running even if panel is hidden
        false
    }
}
