import Foundation

/// Active trading lease information.
struct Lease: Codable, Equatable {
    let status: LeaseStatus
    let strategy: String?
    let timeRemaining: String?
    let expiresAt: Date?

    enum CodingKeys: String, CodingKey {
        case status
        case strategy
        case timeRemaining = "time_remaining"
        case expiresAt = "expires_at"
    }
}

/// Lease status enum
enum LeaseStatus: String, Codable {
    case absent = "ABSENT"
    case draft = "DRAFT"
    case active = "ACTIVE"
    case expired = "EXPIRED"
    case revoked = "REVOKED"
    case halted = "HALTED"
}
