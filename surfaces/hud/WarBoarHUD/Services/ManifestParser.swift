import Foundation

/// Parses manifest.json into StateManifest.
///
/// INV-HUD-ATOMIC-READ: Only reads complete, valid JSON.
/// On parse error, returns last valid manifest (if any).
enum ManifestParser {

    /// Custom date decoding strategy for ISO8601 dates
    private static var decoder: JSONDecoder {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }

    /// Parse manifest from JSON data
    static func parse(_ data: Data) throws -> StateManifest {
        try decoder.decode(StateManifest.self, from: data)
    }

    /// Parse manifest from file URL
    static func parse(fileURL: URL) throws -> StateManifest {
        let data = try Data(contentsOf: fileURL)
        return try parse(data)
    }

    /// Load mock manifest from Preview Content bundle
    static func loadMock() -> StateManifest? {
        guard let url = Bundle.main.url(forResource: "MockManifest", withExtension: "json") else {
            print("⚠️ MockManifest.json not found in bundle")
            return nil
        }

        do {
            return try parse(fileURL: url)
        } catch {
            print("⚠️ Failed to parse MockManifest.json: \(error)")
            return nil
        }
    }

    /// Create a sample manifest for previews (fallback if file not in bundle)
    static var previewManifest: StateManifest {
        StateManifest(
            meta: ManifestMeta(
                schemaVersion: "1.1",
                generatedAt: Date(),
                manifestSeq: 1,
                phoenixStateHash: "preview",
                source: "preview"
            ),
            session: Session(
                kz: "LONDON",
                active: true,
                timeRemaining: "2h 15m",
                nextSession: "NEW_YORK",
                nextStart: "13:00"
            ),
            portfolio: Portfolio(
                balance: 10234.56,
                currency: "USD",
                todayPnl: 82.50,
                todayPct: 0.81,
                weekPct: 2.3
            ),
            livePositions: [
                Position(
                    pair: "EURUSD",
                    direction: .long,
                    entryPrice: 1.0842,
                    currentPrice: 1.0857,
                    pnlPips: 15,
                    pnlDollars: 45.00,
                    duration: "2h 15m",
                    beadId: "TRADE_001"
                )
            ],
            recentTrades: RecentTrades(
                items: [
                    Trade(beadId: "TRADE_010", pair: "GBPUSD", resultPips: 32, closeTime: "11:30"),
                    Trade(beadId: "TRADE_009", pair: "EURUSD", resultPips: -18, closeTime: "09:15"),
                    Trade(beadId: "TRADE_008", pair: "USDJPY", resultPips: 24, closeTime: "08:45")
                ],
                totalCount: 10
            ),
            gatesSummary: [
                GateSummary(pair: "EURUSD", passed: 5, total: 5, status: .ready),
                GateSummary(pair: "GBPUSD", passed: 4, total: 5, status: .watching),
                GateSummary(pair: "USDJPY", passed: 2, total: 5, status: .watching)
            ],
            narrator: Narrator(
                lines: [
                    NarratorLine(timestamp: "14:32", text: "London active, 2h remaining.", sourceBeadId: nil),
                    NarratorLine(timestamp: "14:31", text: "EURUSD +15 pips, holding steady.", sourceBeadId: "TRADE_001"),
                    NarratorLine(timestamp: "14:31", text: "Systems nominal.", sourceBeadId: nil)
                ],
                bufferSize: 20
            ),
            requiresAction: [
                ActionItem(type: .leaseExpiry, message: "Lease expires 58m — review?", severity: .warning, actionRequired: true)
            ],
            health: Health(
                overall: .green,
                status: .healthy,
                since: Date().addingTimeInterval(-7200),
                degradedReasons: [],
                components: HealthComponents(
                    ibkr: .green,
                    river: .green,
                    haltState: .green,
                    lease: .green,
                    decay: .green
                ),
                heartbeatAgeSeconds: 5
            ),
            lease: Lease(
                status: .active,
                strategy: "ICT_FVG_v1",
                timeRemaining: "3h 30m",
                expiresAt: Date().addingTimeInterval(12600)
            )
        )
    }
}
