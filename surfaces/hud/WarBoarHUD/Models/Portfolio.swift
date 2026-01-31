import Foundation

/// Portfolio balance and P&L summary.
///
/// INV-HUD-COLOR-BOUNDARY: PnL values use neutral text colors, not severity colors.
struct Portfolio: Codable, Equatable {
    let balance: Double
    let currency: String
    let todayPnl: Double
    let todayPct: Double
    let weekPct: Double

    enum CodingKeys: String, CodingKey {
        case balance
        case currency
        case todayPnl = "today_pnl"
        case todayPct = "today_pct"
        case weekPct = "week_pct"
    }

    /// Formatted balance string
    var formattedBalance: String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = currency
        return formatter.string(from: NSNumber(value: balance)) ?? "$\(balance)"
    }

    /// Formatted daily P&L with sign
    var formattedTodayPnl: String {
        let sign = todayPnl >= 0 ? "+" : ""
        return "\(sign)$\(String(format: "%.2f", todayPnl))"
    }

    /// Formatted daily percentage with sign
    var formattedTodayPct: String {
        let sign = todayPct >= 0 ? "+" : ""
        return "\(sign)\(String(format: "%.2f", todayPct))%"
    }

    /// Formatted weekly percentage with sign
    var formattedWeekPct: String {
        let sign = weekPct >= 0 ? "+" : ""
        return "\(sign)\(String(format: "%.1f", weekPct))%"
    }
}
