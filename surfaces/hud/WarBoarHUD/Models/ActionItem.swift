import Foundation

/// Required action item in the "Requires Action" section.
///
/// INV-HUD-NO-SUGGEST: Only facts and required acknowledgments.
/// No suggestions, recommendations, or implicit guidance.
struct ActionItem: Codable, Equatable, Identifiable {
    let type: ActionType
    let message: String
    let severity: ActionSeverity
    let actionRequired: Bool

    var id: String { "\(type.rawValue)-\(message.prefix(20))" }

    enum ActionType: String, Codable {
        case leaseExpiry = "LEASE_EXPIRY"
        case healthCritical = "HEALTH_CRITICAL"
        case healthHalted = "HEALTH_HALTED"
        case t2Approval = "T2_APPROVAL"
        case runbookInstruction = "RUNBOOK_INSTRUCTION"
    }

    enum ActionSeverity: String, Codable {
        case info = "INFO"
        case warning = "WARNING"
        case critical = "CRITICAL"
    }

    enum CodingKeys: String, CodingKey {
        case type
        case message
        case severity
        case actionRequired = "action_required"
    }
}
