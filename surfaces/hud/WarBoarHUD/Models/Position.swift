import Foundation

/// Live trading position.
///
/// INV-HUD-SOURCE-LINK: `beadId` provides provenance to Phoenix bead store.
/// INV-HUD-COLOR-BOUNDARY: Position P&L uses neutral text, not severity colors.
struct Position: Codable, Equatable, Identifiable {
    let pair: String
    let direction: Direction
    let entryPrice: Double
    let currentPrice: Double
    let pnlPips: Int
    let pnlDollars: Double
    let duration: String
    let beadId: String?

    var id: String { beadId ?? "\(pair)-\(entryPrice)" }

    enum Direction: String, Codable {
        case long = "LONG"
        case short = "SHORT"
    }

    enum CodingKeys: String, CodingKey {
        case pair
        case direction
        case entryPrice = "entry_price"
        case currentPrice = "current_price"
        case pnlPips = "pnl_pips"
        case pnlDollars = "pnl_dollars"
        case duration
        case beadId = "bead_id"
    }

    /// Formatted pips with sign
    var formattedPips: String {
        let sign = pnlPips >= 0 ? "+" : ""
        return "\(sign)\(pnlPips) pips"
    }

    /// Formatted dollars with sign
    var formattedDollars: String {
        let sign = pnlDollars >= 0 ? "+" : ""
        return "\(sign)$\(String(format: "%.0f", pnlDollars))"
    }

    /// Price movement string (entry → current)
    var priceMovement: String {
        String(format: "%.4f → %.4f", entryPrice, currentPrice)
    }
}
