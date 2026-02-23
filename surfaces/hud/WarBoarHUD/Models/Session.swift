import Foundation

/// Trading session (killzone) information.
struct Session: Codable, Equatable {
    let kz: String
    let active: Bool
    let timeRemaining: String
    let nextSession: String?
    let nextStart: String?

    enum CodingKeys: String, CodingKey {
        case kz
        case active
        case timeRemaining = "time_remaining"
        case nextSession = "next_session"
        case nextStart = "next_start"
    }
}
