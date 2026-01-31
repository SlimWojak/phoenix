import SwiftUI

/// Main container view for HUD content.
///
/// Displays all 9 sections in vertical stack:
/// 1. Session (with timezone clocks)
/// 2. Portfolio
/// 3. Live Positions (up to 3)
/// 4. Recent Trades
/// 5. Gates
/// 6. Narrator (EXPANDS to fill space)
/// 7. Requires Action
/// 8. System Health
/// 9. Lease
struct HUDContentView: View {
    @StateObject private var watcher = ManifestWatcher()

    var body: some View {
        ZStack(alignment: .top) {
            // Smoked glass overlay — 20% darker for better contrast
            Color.black.opacity(0.5)
                .ignoresSafeArea()

            // Main content — simple VStack, no GeometryReader tricks
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    // Header with logo and status
                    HUDHeader(
                        watcherState: watcher.watcherState,
                        isStale: watcher.isStale
                    )

                    // Content based on manifest state
                    if let manifest = watcher.manifest {
                        manifestContent(manifest)
                    } else {
                        loadingContent
                    }
                }
                .padding(.horizontal, HUDSpacing.lg)
                .padding(.top, 8)
                .padding(.bottom, 12)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            // Stale overlay (top of screen)
            if watcher.isStale {
                StaleOverlay(ageSeconds: watcher.manifestAgeSeconds)
                    .transition(.move(edge: .top).combined(with: .opacity))
            }

            // Error overlay
            if let error = watcher.lastError, watcher.manifest == nil {
                ErrorOverlay(error: error)
                    .transition(.move(edge: .top).combined(with: .opacity))
            }
        }
        .animation(.easeInOut(duration: 0.3), value: watcher.isStale)
        .animation(.easeInOut(duration: 0.3), value: watcher.lastError != nil)
        .onAppear {
            // Production: watch real Phoenix manifest
            // Falls back to mock if Phoenix manifest not found
            watcher.startWatchingPhoenix()
        }
        .onDisappear {
            watcher.stopWatching()
        }
    }

    // MARK: - Manifest Content

    /// Content when manifest is loaded — natural sizing, no forced stretching
    private func manifestContent(_ manifest: StateManifest) -> some View {
        VStack(spacing: 16) {  // 16px spacing between all sections
            // Timezone clocks row
            TimezoneClocksView(activeKZ: manifest.session.kz)

            // 1. Session
            SessionSection(session: manifest.session)

            // 2. Portfolio (full width)
            PortfolioSection(portfolio: manifest.portfolio)

            // 3. Live Positions (3 slots)
            PositionsSection(positions: manifest.livePositions)

            // 4. Recent Trades
            RecentTradesSection(trades: manifest.recentTrades)

            // 5. Gates
            GatesSection(gates: manifest.gatesSummary)

            // 6. Narrator
            NarratorSection(narrator: manifest.narrator)

            // 7. Requires Action (only shows if items exist)
            RequiresActionSection(items: manifest.requiresAction)

            // 8. System Health
            HealthSection(health: manifest.health)

            // 9. Lease
            LeaseSection(lease: manifest.lease)
        }
    }

    // MARK: - Loading State

    private var loadingContent: some View {
        VStack(spacing: HUDSpacing.xl) {
            Spacer()

            ProgressView()
                .progressViewStyle(CircularProgressViewStyle(tint: .textSecondary))

            Text("Loading manifest...")
                .font(HUDFont.label)
                .foregroundColor(.textMuted)

            Spacer()
        }
        .frame(maxWidth: .infinity, minHeight: 200)
    }
}

// MARK: - HUD Header with Logo

/// HUD header with WarBoar logo — CENTERED, no extra spacers
struct HUDHeader: View {
    var watcherState: ManifestWatcher.WatcherState = .idle
    var isStale: Bool = false

    var body: some View {
        VStack(spacing: 6) {
            // Logo image — 54px height, CENTERED
            HStack {
                Spacer()

                if let logoImage = loadLogo() {
                    Image(nsImage: logoImage)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(height: 54)
                } else {
                    // Fallback to SF Symbol
                    Image(systemName: "hare.fill")
                        .font(.system(size: 40, weight: .medium))
                        .foregroundColor(.textSecondary)
                }

                Spacer()
            }

            // Status indicator below logo — 30% larger
            HStack(spacing: 4) {
                Circle()
                    .fill(statusColor)
                    .frame(width: 10, height: 10)

                Text(statusText)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.textMuted)
            }
        }
        .padding(.top, 12)
        .padding(.bottom, 8)
    }

    private var statusText: String {
        if isStale { return "STALE" }
        switch watcherState {
        case .watching: return "LIVE"
        case .polling: return "POLLING"
        case .preview: return "PREVIEW"
        default: return ""
        }
    }

    private var statusColor: Color {
        if isStale {
            return .healthRed
        }
        switch watcherState {
        case .watching, .polling:
            return .healthGreen
        case .preview:
            return .activeAccent
        default:
            return .textMuted
        }
    }

    private func loadLogo() -> NSImage? {
        // Try bundle first
        if let bundleURL = Bundle.main.url(forResource: "warboar-logo", withExtension: "png"),
           let image = NSImage(contentsOf: bundleURL) {
            return image
        }

        // Fallback to file path
        let path = "/Users/echopeso/phoenix-hud/WarBoarHUD/Resources/warboar-logo.png"
        return NSImage(contentsOfFile: path)
    }
}

// MARK: - Timezone Clocks

/// Shows NY / LDN / ASIA times — EVENLY SPACED across full width
struct TimezoneClocksView: View {
    let activeKZ: String

    private let timezones: [(id: String, label: String, tz: String)] = [
        ("NEW_YORK", "NY", "America/New_York"),
        ("LONDON", "LDN", "Europe/London"),
        ("TOKYO", "ASIA", "Asia/Tokyo")
    ]

    @State private var currentTime = Date()
    let timer = Timer.publish(every: 60, on: .main, in: .common).autoconnect()

    var body: some View {
        HStack(spacing: HUDSpacing.sm) {
            ForEach(timezones, id: \.id) { tz in
                // Each clock takes equal width
                HStack(spacing: HUDSpacing.sm) {
                    Image(systemName: "clock.fill")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(isActive(tz.id) ? .activeAccent : .textMuted)

                    VStack(alignment: .leading, spacing: 1) {
                        Text(tz.label)
                            .font(.system(size: 10, weight: .semibold))
                            .foregroundColor(isActive(tz.id) ? .textPrimary : .textMuted)

                        Text(timeString(for: tz.tz))
                            .font(.system(size: 14, weight: .semibold, design: .monospaced))
                            .foregroundColor(isActive(tz.id) ? .textPrimary : .textSecondary)
                    }

                    Spacer(minLength: 0)
                }
                .padding(.horizontal, HUDSpacing.md)
                .padding(.vertical, HUDSpacing.sm)
                .frame(maxWidth: .infinity)
                .background(
                    RoundedRectangle(cornerRadius: 6)
                        .fill(isActive(tz.id) ? Color.activeAccent.opacity(0.2) : Color.sectionBackground)
                )
            }
        }
        .onReceive(timer) { _ in
            currentTime = Date()
        }
    }

    private func isActive(_ kzId: String) -> Bool {
        switch activeKZ.uppercased() {
        case "NEW_YORK", "NY":
            return kzId == "NEW_YORK"
        case "LONDON", "LDN":
            return kzId == "LONDON"
        case "TOKYO", "ASIA", "SYDNEY":
            return kzId == "TOKYO"
        default:
            return false
        }
    }

    private func timeString(for tzIdentifier: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        formatter.timeZone = TimeZone(identifier: tzIdentifier)
        return formatter.string(from: currentTime)
    }
}

// MARK: - Previews

#Preview("Full HUD") {
    HUDContentView()
        .frame(width: 280, height: 800)
        .background(Color.black.opacity(0.85))
}
