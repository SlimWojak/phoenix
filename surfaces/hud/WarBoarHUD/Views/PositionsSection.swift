import SwiftUI

/// Live positions section — shows 3 slots for concurrent positions.
///
/// INV-HUD-COLOR-BOUNDARY: Position P&L uses neutral white text, NOT green/red.
struct PositionsSection: View {
    let positions: [Position]
    let slotCount: Int = 3  // Always show 3 slots

    var body: some View {
        SectionContainer("Live Positions", icon: "chart.line.uptrend.xyaxis", trailing: countText) {
            VStack(spacing: HUDSpacing.xs) {
                // Always show 3 slots
                ForEach(0..<slotCount, id: \.self) { index in
                    if index < positions.count {
                        PositionRow(position: positions[index], isLast: index == slotCount - 1)
                    } else {
                        EmptyPositionSlot(isLast: index == slotCount - 1)
                    }
                }
            }
            .cardStyle()
        }
    }

    private var countText: String? {
        "\(positions.count) open"
    }
}

/// Empty slot placeholder
struct EmptyPositionSlot: View {
    let isLast: Bool

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("—")
                    .font(HUDFont.pair)
                    .foregroundColor(.textMuted)

                Spacer()

                Text("available")
                    .font(HUDFont.meta)
                    .foregroundColor(.textMuted)
            }
            .padding(.vertical, HUDSpacing.xs)

            if !isLast {
                Divider()
                    .background(Color.separator)
                    .padding(.vertical, HUDSpacing.xs)
            }
        }
    }
}

struct PositionRow: View {
    let position: Position
    let isLast: Bool

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: HUDSpacing.md) {
                // Pair + Direction
                HStack(spacing: HUDSpacing.sm) {
                    Text(position.pair)
                        .font(HUDFont.pair)
                        .foregroundColor(.textPrimary)

                    Text(position.direction.rawValue)
                        .font(HUDFont.direction)
                        .foregroundColor(position.direction == .long ? .activeAccent : .textSecondary)
                }
                .frame(width: 95, alignment: .leading)

                // Pips
                PipsText(position.pnlPips, font: HUDFont.valueSM)
                    .frame(width: 65, alignment: .trailing)

                // Dollars
                PnLText(position.pnlDollars, prefix: "$", font: HUDFont.valueSM)
                    .frame(width: 50, alignment: .trailing)

                Spacer()

                // Duration
                Text(position.duration)
                    .font(HUDFont.meta)
                    .foregroundColor(.textMuted)
            }

            if !isLast {
                Divider()
                    .background(Color.separator)
                    .padding(.vertical, HUDSpacing.xs)
            }
        }
    }
}

#Preview {
    VStack(spacing: 16) {
        // 1 position
        PositionsSection(positions: [
            Position(pair: "EURUSD", direction: .long, entryPrice: 1.0842, currentPrice: 1.0857, pnlPips: 15, pnlDollars: 45.00, duration: "2h 15m", beadId: "T1")
        ])

        // 3 positions (max visible)
        PositionsSection(positions: [
            Position(pair: "EURUSD", direction: .long, entryPrice: 1.0842, currentPrice: 1.0857, pnlPips: 15, pnlDollars: 45.00, duration: "2h 15m", beadId: "T1"),
            Position(pair: "GBPUSD", direction: .short, entryPrice: 1.2650, currentPrice: 1.2620, pnlPips: 30, pnlDollars: 90.00, duration: "1h 30m", beadId: "T2"),
            Position(pair: "USDJPY", direction: .long, entryPrice: 149.50, currentPrice: 149.20, pnlPips: -30, pnlDollars: -60.00, duration: "45m", beadId: "T3")
        ])

        // Empty
        PositionsSection(positions: [])
    }
    .padding()
    .frame(width: 280)
    .background(Color.black.opacity(0.9))
}
