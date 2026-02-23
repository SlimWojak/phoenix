import AppKit
import SwiftUI

/// Manages the HUD panel lifecycle and content.
final class PanelController: NSObject {
    private var panel: HUDPanel?
    private var visualEffectView: NSVisualEffectView?

    // Panel dimensions
    private let panelWidth: CGFloat = 280
    private let panelPadding: CGFloat = 12

    override init() {
        super.init()
        setupPanel()
        observeScreenChanges()
    }

    private func setupPanel() {
        let contentRect = calculatePanelFrame()

        panel = HUDPanel(
            contentRect: contentRect,
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )

        guard let panel = panel else { return }

        // Setup vibrancy background
        let visualEffect = NSVisualEffectView(frame: panel.contentView?.bounds ?? .zero)
        visualEffect.autoresizingMask = [.width, .height]
        visualEffect.material = .hudWindow
        visualEffect.blendingMode = .behindWindow
        visualEffect.state = .active
        visualEffect.wantsLayer = true
        visualEffect.layer?.cornerRadius = 12
        visualEffect.layer?.masksToBounds = true

        panel.contentView?.addSubview(visualEffect)
        visualEffectView = visualEffect

        // Embed SwiftUI content
        let hostingView = NSHostingView(rootView: HUDContentView())
        hostingView.frame = visualEffect.bounds
        hostingView.autoresizingMask = [.width, .height]
        visualEffect.addSubview(hostingView)
    }

    /// Calculate panel frame pinned to left edge of main screen
    private func calculatePanelFrame() -> NSRect {
        guard let screen = NSScreen.main else {
            return NSRect(x: 0, y: 100, width: panelWidth, height: 600)
        }

        let screenFrame = screen.visibleFrame
        let panelHeight = screenFrame.height - (panelPadding * 2)

        return NSRect(
            x: screenFrame.minX + panelPadding,
            y: screenFrame.minY + panelPadding,
            width: panelWidth,
            height: panelHeight
        )
    }

    func showPanel() {
        panel?.setFrame(calculatePanelFrame(), display: true)
        panel?.orderFrontRegardless()
    }

    func closePanel() {
        panel?.close()
        panel = nil
    }

    func togglePanel() {
        if panel?.isVisible == true {
            panel?.orderOut(nil)
        } else {
            showPanel()
        }
    }

    // MARK: - Screen Change Handling

    /// Observe screen configuration changes (monitor swap, resolution change)
    /// Chaos gate: ultrawide_resize
    private func observeScreenChanges() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(screenParametersChanged),
            name: NSApplication.didChangeScreenParametersNotification,
            object: nil
        )
    }

    @objc private func screenParametersChanged() {
        // Reposition panel to remain visible after screen change
        panel?.setFrame(calculatePanelFrame(), display: true, animate: true)
    }

    deinit {
        NotificationCenter.default.removeObserver(self)
    }
}
