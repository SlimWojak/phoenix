import SwiftUI

/// Typography system for WarBoar HUD.
/// Uses SF Pro with clear hierarchy for glanceability.
enum HUDFont {

    // ═══════════════════════════════════════════════════════════════════
    // SECTION HEADERS
    // ═══════════════════════════════════════════════════════════════════

    /// Section title (e.g., "LIVE POSITIONS")
    static let sectionTitle = Font.system(size: 10, weight: .semibold, design: .default)

    /// Section subtitle/count
    static let sectionSubtitle = Font.system(size: 9, weight: .medium, design: .default)

    // ═══════════════════════════════════════════════════════════════════
    // PRIMARY CONTENT
    // ═══════════════════════════════════════════════════════════════════

    /// Large value display (e.g., "$10,234.56")
    static let valueXL = Font.system(size: 20, weight: .semibold, design: .rounded)

    /// Medium value display (e.g., "+$82.50")
    static let valueLG = Font.system(size: 15, weight: .medium, design: .rounded)

    /// Standard value (e.g., "2h 15m")
    static let valueMD = Font.system(size: 13, weight: .medium, design: .default)

    /// Small value (e.g., pips count)
    static let valueSM = Font.system(size: 12, weight: .regular, design: .default)

    // ═══════════════════════════════════════════════════════════════════
    // LABELS & METADATA
    // ═══════════════════════════════════════════════════════════════════

    /// Label text (e.g., "Today:", "Week:")
    static let label = Font.system(size: 11, weight: .regular, design: .default)

    /// Small label
    static let labelSM = Font.system(size: 10, weight: .regular, design: .default)

    /// Timestamp/metadata
    static let timestamp = Font.system(size: 10, weight: .regular, design: .monospaced)

    /// Tiny metadata
    static let meta = Font.system(size: 9, weight: .regular, design: .default)

    // ═══════════════════════════════════════════════════════════════════
    // SPECIAL
    // ═══════════════════════════════════════════════════════════════════

    /// Narrator text
    static let narrator = Font.system(size: 11, weight: .regular, design: .default)

    /// Currency pair (e.g., "EURUSD")
    static let pair = Font.system(size: 12, weight: .semibold, design: .monospaced)

    /// Direction label (LONG/SHORT)
    static let direction = Font.system(size: 10, weight: .medium, design: .default)

    /// Status badge (e.g., "READY", "WATCHING")
    static let statusBadge = Font.system(size: 9, weight: .semibold, design: .default)

    /// Debug/monospace
    static let debug = Font.system(size: 9, weight: .regular, design: .monospaced)
}

// MARK: - Icon Sizes

enum HUDIcon {
    /// Small icon (inline with text)
    static let small: CGFloat = 10

    /// Medium icon (section headers)
    static let medium: CGFloat = 12

    /// Large icon (primary indicators)
    static let large: CGFloat = 14

    /// Health indicator dot
    static let healthDot: CGFloat = 8

    /// Trade history dot
    static let tradeDot: CGFloat = 6
}

// MARK: - Spacing (Refined for balanced vertical distribution)

enum HUDSpacing {
    /// Tiny spacing (2pt)
    static let xs: CGFloat = 2

    /// Small spacing (4pt)
    static let sm: CGFloat = 4

    /// Medium spacing (6pt) - reduced from 8
    static let md: CGFloat = 6

    /// Large spacing (10pt) - reduced from 12
    static let lg: CGFloat = 10

    /// Extra large spacing (12pt) - reduced from 16
    static let xl: CGFloat = 12

    /// Section gap (10pt) - space between sections
    static let sectionGap: CGFloat = 10

    /// Section padding
    static let sectionPadding: CGFloat = 8

    /// Card padding (6pt) - slightly tighter
    static let cardPadding: CGFloat = 6
}
