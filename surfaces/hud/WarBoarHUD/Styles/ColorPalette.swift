import SwiftUI

/// Constitutional color palette for WarBoar HUD.
///
/// INV-HUD-COLOR-BOUNDARY: Severity colors (green/amber/red) are ONLY for health indicators.
/// PnL and trade results use neutral text with +/- prefixes.
/// This prevents "dopamine casino UI" and maintains authority.
extension Color {

    // ═══════════════════════════════════════════════════════════════════
    // HEALTH STATES ONLY — Traffic light colors
    // These colors are CONSTITUTIONALLY RESERVED for system health display
    // ═══════════════════════════════════════════════════════════════════

    /// HEALTHY state - used only in Health section and Gates READY
    static let healthGreen = Color(red: 0.298, green: 0.686, blue: 0.314).opacity(0.7)  // #4CAF50 @ 70%

    /// DEGRADED state - used only in Health section
    static let healthAmber = Color(red: 1.0, green: 0.596, blue: 0.0).opacity(0.7)      // #FF9800 @ 70%

    /// CRITICAL/HALTED state - used only in Health section
    static let healthRed = Color(red: 0.957, green: 0.263, blue: 0.212).opacity(0.7)    // #F44336 @ 70%

    // ═══════════════════════════════════════════════════════════════════
    // PNL/TRADES — Neutral (no dopamine colors)
    // Direction indicated by +/- prefix only
    // ═══════════════════════════════════════════════════════════════════

    /// Positive PnL - brighter white, NOT green (increased contrast)
    static let pnlPositive = Color.white.opacity(0.95)

    /// Negative PnL - slightly muted, NOT red (increased contrast)
    static let pnlNegative = Color.white.opacity(0.70)

    // ═══════════════════════════════════════════════════════════════════
    // TRADE HISTORY — Neutral accent
    // All trades get same colored dot regardless of result
    // ═══════════════════════════════════════════════════════════════════

    /// Neutral blue dot for all trades (not result-coded)
    static let tradeDot = Color(red: 0.129, green: 0.588, blue: 0.953).opacity(0.5)     // #2196F3 @ 50%

    // ═══════════════════════════════════════════════════════════════════
    // TEXT HIERARCHY — Increased contrast for legibility
    // ═══════════════════════════════════════════════════════════════════

    /// Primary text - high emphasis (was 0.9, now 0.95)
    static let textPrimary = Color.white.opacity(0.95)

    /// Secondary text - medium emphasis (was 0.6, now 0.75)
    static let textSecondary = Color.white.opacity(0.75)

    /// Tertiary text - low emphasis, labels (was 0.4, now 0.55)
    static let textTertiary = Color.white.opacity(0.55)

    /// Muted text - timestamps, metadata (was 0.3, now 0.45)
    static let textMuted = Color.white.opacity(0.45)

    // ═══════════════════════════════════════════════════════════════════
    // ACCENTS & STRUCTURE
    // ═══════════════════════════════════════════════════════════════════

    /// Active accent - highlights, selections
    static let activeAccent = Color(red: 0.129, green: 0.588, blue: 0.953).opacity(0.8) // #2196F3 @ 80%

    /// Muted separator lines
    static let separator = Color.white.opacity(0.12)

    /// Section background
    static let sectionBackground = Color.white.opacity(0.04)

    /// Card background (slightly more visible)
    static let cardBackground = Color.white.opacity(0.06)

    // ═══════════════════════════════════════════════════════════════════
    // SPECIAL STATES
    // ═══════════════════════════════════════════════════════════════════

    /// Warning banner (for REQUIRES ACTION)
    static let warningBanner = Color(red: 1.0, green: 0.596, blue: 0.0).opacity(0.15)   // Subtle amber

    /// Stale state banner
    static let staleBanner = Color(red: 0.957, green: 0.263, blue: 0.212).opacity(0.9)
}

// MARK: - Health Color Helper

extension Color {
    /// Get color for health overall state
    static func forHealth(_ overall: HealthOverall) -> Color {
        switch overall {
        case .green: return .healthGreen
        case .yellow: return .healthAmber
        case .red: return .healthRed
        }
    }

    /// Get color for PnL value (neutral, not dopamine)
    static func forPnL(_ value: Double) -> Color {
        value >= 0 ? .pnlPositive : .pnlNegative
    }
}
