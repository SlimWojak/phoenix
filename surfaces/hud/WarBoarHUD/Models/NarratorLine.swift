import Foundation

/// Single narrator observation line.
///
/// INV-HUD-NO-SUGGEST: Narrator displays facts only, no suggestions.
/// Phoenix generates these lines; HUD displays them verbatim.
struct NarratorLine: Codable, Equatable, Identifiable {
    let timestamp: String
    let text: String
    let sourceBeadId: String?

    var id: String { "\(timestamp)-\(text.prefix(20))" }

    enum CodingKeys: String, CodingKey {
        case timestamp
        case text
        case sourceBeadId = "source_bead_id"
    }
}
