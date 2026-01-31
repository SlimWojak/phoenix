import Foundation

/// Gate evaluation summary for a currency pair.
struct GateSummary: Codable, Equatable, Identifiable {
    let pair: String
    let passed: Int
    let total: Int
    let status: GateStatus

    var id: String { pair }

    enum GateStatus: String, Codable {
        case ready = "READY"
        case watching = "WATCHING"
        case blocked = "BLOCKED"
    }

    /// Progress string (e.g., "5/5")
    var progressString: String {
        "\(passed)/\(total)"
    }

    /// Whether all gates are passed
    var isReady: Bool { status == .ready }
}
