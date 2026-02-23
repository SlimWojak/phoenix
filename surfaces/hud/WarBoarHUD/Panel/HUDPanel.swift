import AppKit

/// NSPanel subclass configured for always-on-top HUD behavior.
///
/// Invariants:
/// - Floats above other windows
/// - Doesn't hide when app deactivates
/// - Follows across virtual desktops (Spaces)
/// - Non-activating (doesn't steal focus)
final class HUDPanel: NSPanel {

    override init(
        contentRect: NSRect,
        styleMask style: NSWindow.StyleMask,
        backing backingStoreType: NSWindow.BackingStoreType,
        defer flag: Bool
    ) {
        super.init(
            contentRect: contentRect,
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )

        configurePanel()
    }

    private func configurePanel() {
        // Floating behavior
        isFloatingPanel = true
        level = .floating

        // Don't hide when app loses focus
        hidesOnDeactivate = false

        // Allow dragging by background
        isMovableByWindowBackground = true

        // Transparent titlebar (we're borderless anyway)
        titlebarAppearsTransparent = true
        titleVisibility = .hidden

        // Follow across Spaces (virtual desktops)
        // Critical for Olya's workflow
        collectionBehavior = [
            .canJoinAllSpaces,
            .fullScreenAuxiliary,
            .stationary
        ]

        // Don't show in Exposé/Mission Control as separate window
        collectionBehavior.insert(.ignoresCycle)

        // Transparency for vibrancy
        isOpaque = false
        backgroundColor = .clear

        // Allow vibrancy effects
        hasShadow = true
    }

    /// Allows mouse events to pass through to content
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { false }
}
