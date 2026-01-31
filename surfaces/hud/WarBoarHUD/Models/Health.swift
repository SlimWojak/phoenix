import Foundation

/// System health status.
///
/// INV-HUD-COLOR-BOUNDARY: Only this section uses severity colors (green/amber/red).
struct Health: Codable, Equatable {
    let overall: HealthOverall
    let status: HealthStatus
    let since: Date
    let degradedReasons: [String]
    let components: HealthComponents
    let heartbeatAgeSeconds: Int

    enum CodingKeys: String, CodingKey {
        case overall
        case status
        case since
        case degradedReasons = "degraded_reasons"
        case components
        case heartbeatAgeSeconds = "heartbeat_age_seconds"
    }
}

/// Traffic light health indicator
enum HealthOverall: String, Codable {
    case green = "GREEN"
    case yellow = "YELLOW"
    case red = "RED"
}

/// Explicit health status
enum HealthStatus: String, Codable {
    case healthy = "HEALTHY"
    case degraded = "DEGRADED"
    case critical = "CRITICAL"
    case halted = "HALTED"
}

/// Individual component health states
struct HealthComponents: Codable, Equatable {
    let ibkr: HealthOverall
    let river: HealthOverall
    let haltState: HealthOverall
    let lease: HealthOverall
    let decay: HealthOverall

    enum CodingKeys: String, CodingKey {
        case ibkr
        case river
        case haltState = "halt_state"
        case lease
        case decay
    }
}
