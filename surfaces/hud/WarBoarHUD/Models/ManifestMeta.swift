import Foundation

/// Manifest metadata for versioning and freshness detection.
///
/// INV-HUD-STALE-VISIBLE: Use `generatedAt` to detect stale state (>60s).
/// INV-HUD-ATOMIC-READ: Use `manifestSeq` to detect partial reads.
struct ManifestMeta: Codable, Equatable {
    let schemaVersion: String
    let generatedAt: Date
    let manifestSeq: Int
    let phoenixStateHash: String?
    let source: String

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case generatedAt = "generated_at"
        case manifestSeq = "manifest_seq"
        case phoenixStateHash = "phoenix_state_hash"
        case source
    }

    /// Check if manifest is stale (older than threshold)
    func isStale(threshold: TimeInterval = 60) -> Bool {
        Date().timeIntervalSince(generatedAt) > threshold
    }

    /// Age of manifest in seconds
    var ageSeconds: Int {
        Int(Date().timeIntervalSince(generatedAt))
    }
}
