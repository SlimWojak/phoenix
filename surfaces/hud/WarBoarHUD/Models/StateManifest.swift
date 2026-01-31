import Foundation

/// Root state manifest from Phoenix.
/// Schema version: 1.1
///
/// INV-HUD-READ-ONLY: This is a read-only projection of Phoenix state.
struct StateManifest: Codable, Equatable {
    let meta: ManifestMeta
    let session: Session
    let portfolio: Portfolio
    let livePositions: [Position]
    let recentTrades: RecentTrades
    let gatesSummary: [GateSummary]
    let narrator: Narrator
    let requiresAction: [ActionItem]
    let health: Health
    let lease: Lease

    enum CodingKeys: String, CodingKey {
        case meta
        case session
        case portfolio
        case livePositions = "live_positions"
        case recentTrades = "recent_trades"
        case gatesSummary = "gates_summary"
        case narrator
        case requiresAction = "requires_action"
        case health
        case lease
    }
}

/// Container for recent trades with pagination info
struct RecentTrades: Codable, Equatable {
    let items: [Trade]
    let totalCount: Int

    enum CodingKeys: String, CodingKey {
        case items
        case totalCount = "total_count"
    }
}

/// Container for narrator observations
struct Narrator: Codable, Equatable {
    let lines: [NarratorLine]
    let bufferSize: Int

    enum CodingKeys: String, CodingKey {
        case lines
        case bufferSize = "buffer_size"
    }
}
