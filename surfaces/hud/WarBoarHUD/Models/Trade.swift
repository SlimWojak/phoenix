import Foundation

/// Completed trade in recent history.
///
/// INV-HUD-SOURCE-LINK: `beadId` provides provenance to Phoenix bead store.
/// INV-HUD-COLOR-BOUNDARY: Trade results use neutral blue dot, not win/loss colors.
struct Trade: Codable, Equatable, Identifiable {
    let beadId: String
    let pair: String
    let resultPips: Int
    let closeTime: String

    var id: String { beadId }

    enum CodingKeys: String, CodingKey {
        case beadId = "bead_id"
        case pair
        case resultPips = "result_pips"
        case closeTime = "close_time"
    }

    /// Formatted result with sign
    var formattedResult: String {
        let sign = resultPips >= 0 ? "+" : ""
        return "\(sign)\(resultPips) pips"
    }

    /// Whether trade was profitable
    var isWin: Bool { resultPips > 0 }
}
