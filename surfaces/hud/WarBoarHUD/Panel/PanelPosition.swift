import AppKit

/// Edge pinning configuration for HUD panel positioning.
enum PanelEdge {
    case left
    case right

    /// Calculate frame for panel pinned to this edge
    func frame(width: CGFloat, padding: CGFloat, on screen: NSScreen) -> NSRect {
        let visibleFrame = screen.visibleFrame
        let height = visibleFrame.height - (padding * 2)

        let x: CGFloat
        switch self {
        case .left:
            x = visibleFrame.minX + padding
        case .right:
            x = visibleFrame.maxX - width - padding
        }

        return NSRect(
            x: x,
            y: visibleFrame.minY + padding,
            width: width,
            height: height
        )
    }
}

/// Panel positioning utilities
enum PanelPosition {

    /// Find the screen containing a given point
    static func screen(containing point: NSPoint) -> NSScreen? {
        NSScreen.screens.first { NSMouseInRect(point, $0.frame, false) }
    }

    /// Get the main screen or first available
    static var primaryScreen: NSScreen? {
        NSScreen.main ?? NSScreen.screens.first
    }

    /// Ensure a frame remains within visible screen bounds
    static func constrain(_ frame: NSRect, to screen: NSScreen) -> NSRect {
        let visibleFrame = screen.visibleFrame
        var constrained = frame

        // Keep within horizontal bounds
        if constrained.minX < visibleFrame.minX {
            constrained.origin.x = visibleFrame.minX
        }
        if constrained.maxX > visibleFrame.maxX {
            constrained.origin.x = visibleFrame.maxX - constrained.width
        }

        // Keep within vertical bounds
        if constrained.minY < visibleFrame.minY {
            constrained.origin.y = visibleFrame.minY
        }
        if constrained.maxY > visibleFrame.maxY {
            constrained.origin.y = visibleFrame.maxY - constrained.height
        }

        return constrained
    }
}
