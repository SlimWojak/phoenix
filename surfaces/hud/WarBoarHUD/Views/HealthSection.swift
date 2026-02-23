import SwiftUI

/// System health section with traffic light indicators — ENLARGED for glanceability.
///
/// INV-HUD-COLOR-BOUNDARY: This is the ONLY section that uses severity colors.
/// Traffic lights: GREEN (healthy), AMBER (degraded), RED (critical/halted).
struct HealthSection: View {
    let health: Health

    var body: some View {
        SectionContainer("System Health", icon: "heart.fill", trailing: nil) {
            VStack(spacing: HUDSpacing.md) {
                // Component grid — 3 columns, LARGER
                LazyVGrid(columns: [
                    GridItem(.flexible()),
                    GridItem(.flexible()),
                    GridItem(.flexible())
                ], spacing: HUDSpacing.md) {
                    HealthComponentView(name: "IBKR", health: health.components.ibkr)
                    HealthComponentView(name: "River", health: health.components.river)
                    HealthComponentView(name: "Halt", health: health.components.haltState)
                    HealthComponentView(name: "Lease", health: health.components.lease)
                    HealthComponentView(name: "Decay", health: health.components.decay)
                }

                // Heartbeat row — more prominent
                HStack(spacing: HUDSpacing.sm) {
                    Image(systemName: "waveform.path.ecg")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(heartbeatColor)

                    Text("Heartbeat:")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.textSecondary)

                    Text("\(health.heartbeatAgeSeconds)s ago")
                        .font(.system(size: 12, weight: .semibold, design: .monospaced))
                        .foregroundColor(heartbeatColor)

                    Spacer()

                    // Overall status badge
                    StatusBadge(
                        health.status.rawValue,
                        color: Color.forHealth(health.overall),
                        filled: health.status != .healthy
                    )
                }
            }
            .cardStyle()
        }
    }

    private var heartbeatColor: Color {
        if health.heartbeatAgeSeconds < 10 {
            return .healthGreen
        } else if health.heartbeatAgeSeconds < 30 {
            return .healthAmber
        } else {
            return .healthRed
        }
    }
}

/// Individual health component — LARGER for visibility
struct HealthComponentView: View {
    let name: String
    let health: HealthOverall

    var body: some View {
        HStack(spacing: HUDSpacing.sm) {
            // Larger health dot
            Circle()
                .fill(Color.forHealth(health))
                .frame(width: 10, height: 10)

            // Larger text
            Text(name)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(.textSecondary)
        }
    }
}

#Preview {
    VStack(spacing: 16) {
        HealthSection(health: Health(
            overall: .green,
            status: .healthy,
            since: Date(),
            degradedReasons: [],
            components: HealthComponents(
                ibkr: .green,
                river: .green,
                haltState: .green,
                lease: .green,
                decay: .green
            ),
            heartbeatAgeSeconds: 5
        ))

        HealthSection(health: Health(
            overall: .yellow,
            status: .degraded,
            since: Date(),
            degradedReasons: ["River slow"],
            components: HealthComponents(
                ibkr: .green,
                river: .yellow,
                haltState: .green,
                lease: .green,
                decay: .green
            ),
            heartbeatAgeSeconds: 25
        ))
    }
    .padding()
    .frame(width: 280)
    .background(Color.black.opacity(0.9))
}
