import SwiftUI

/// Gates section showing entry condition evaluation per pair.
///
/// Gates READY can use health green (it's a system state, not P&L).
struct GatesSection: View {
    let gates: [GateSummary]

    var body: some View {
        SectionContainer("Gates", icon: "checkmark.shield", trailing: summaryText) {
            if gates.isEmpty {
                emptyState
            } else {
                VStack(spacing: 0) {
                    ForEach(Array(gates.enumerated()), id: \.element.id) { index, gate in
                        GateRow(gate: gate)
                            .rowStyle(separator: index < gates.count - 1)
                    }
                }
                .cardStyle()
            }
        }
    }

    private var summaryText: String? {
        guard !gates.isEmpty else { return nil }
        let ready = gates.filter { $0.isReady }.count
        return "\(ready)/\(gates.count) ready"
    }

    private var emptyState: some View {
        HStack {
            Image(systemName: "shield.slash")
                .font(.system(size: HUDIcon.medium))
                .foregroundColor(.textMuted)

            Text("No gates configured")
                .font(HUDFont.label)
                .foregroundColor(.textMuted)

            Spacer()
        }
        .padding(.vertical, HUDSpacing.sm)
    }
}

struct GateRow: View {
    let gate: GateSummary

    var body: some View {
        HStack(spacing: HUDSpacing.md) {
            // Status indicator (health green for READY is allowed)
            Circle()
                .fill(gate.isReady ? Color.healthGreen : Color.textMuted)
                .frame(width: HUDIcon.healthDot, height: HUDIcon.healthDot)

            // Pair
            Text(gate.pair)
                .font(HUDFont.pair)
                .foregroundColor(.textPrimary)
                .frame(width: 60, alignment: .leading)

            // Progress
            Text(gate.progressString)
                .font(HUDFont.valueSM)
                .foregroundColor(.textSecondary)

            Spacer()

            // Status badge
            StatusBadge(
                gate.status.rawValue,
                color: statusColor,
                filled: gate.isReady
            )
        }
    }

    private var statusColor: Color {
        switch gate.status {
        case .ready:
            return .healthGreen
        case .watching:
            return .textSecondary
        case .blocked:
            return .healthAmber
        }
    }
}

#Preview {
    VStack(spacing: 16) {
        GatesSection(gates: [
            GateSummary(pair: "EURUSD", passed: 5, total: 5, status: .ready),
            GateSummary(pair: "GBPUSD", passed: 4, total: 5, status: .watching),
            GateSummary(pair: "USDJPY", passed: 2, total: 5, status: .watching),
        ])

        GatesSection(gates: [])
    }
    .padding()
    .frame(width: 280)
    .background(Color.black.opacity(0.9))
}
