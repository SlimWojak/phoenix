import SwiftUI

/// Recent trades section with scrollable list.
///
/// INV-HUD-COLOR-BOUNDARY: Trade dots are neutral blue, NOT result-coded.
/// Trade results shown as +/- pips with neutral white text.
struct RecentTradesSection: View {
    let trades: RecentTrades
    let maxVisible: Int = 5

    var body: some View {
        SectionContainer("Recent Trades", icon: "list.bullet", trailing: countText) {
            if trades.items.isEmpty {
                emptyState
            } else {
                VStack(spacing: 0) {
                    ForEach(Array(visibleTrades.enumerated()), id: \.element.id) { index, trade in
                        TradeRow(trade: trade)
                            .rowStyle(separator: index < visibleTrades.count - 1)
                    }
                }
                .cardStyle()
            }
        }
    }

    private var visibleTrades: [Trade] {
        Array(trades.items.prefix(maxVisible))
    }

    private var countText: String? {
        guard !trades.items.isEmpty else { return nil }
        if trades.items.count > maxVisible {
            return "↕ \(maxVisible)/\(trades.totalCount)"
        }
        return "\(trades.items.count) trades"
    }

    private var emptyState: some View {
        HStack {
            Image(systemName: "tray")
                .font(.system(size: HUDIcon.medium))
                .foregroundColor(.textMuted)

            Text("No recent trades")
                .font(HUDFont.label)
                .foregroundColor(.textMuted)

            Spacer()
        }
        .padding(.vertical, HUDSpacing.sm)
    }
}

struct TradeRow: View {
    let trade: Trade

    var body: some View {
        HStack(spacing: HUDSpacing.md) {
            // Neutral blue dot (NOT result-coded)
            Circle()
                .fill(Color.tradeDot)
                .frame(width: HUDIcon.tradeDot, height: HUDIcon.tradeDot)

            // Pair
            Text(trade.pair)
                .font(HUDFont.pair)
                .foregroundColor(.textPrimary)
                .frame(width: 60, alignment: .leading)

            // Result pips (neutral color)
            PipsText(trade.resultPips, font: HUDFont.valueSM)

            Spacer()

            // Close time
            Text(trade.closeTime)
                .font(HUDFont.timestamp)
                .foregroundColor(.textMuted)
        }
    }
}

#Preview {
    VStack(spacing: 16) {
        RecentTradesSection(trades: RecentTrades(
            items: [
                Trade(beadId: "T1", pair: "GBPUSD", resultPips: 32, closeTime: "11:30"),
                Trade(beadId: "T2", pair: "EURUSD", resultPips: -18, closeTime: "09:15"),
                Trade(beadId: "T3", pair: "USDJPY", resultPips: 24, closeTime: "08:45"),
                Trade(beadId: "T4", pair: "GBPUSD", resultPips: 41, closeTime: "07:30"),
                Trade(beadId: "T5", pair: "EURUSD", resultPips: -12, closeTime: "06:15"),
            ],
            totalCount: 10
        ))

        RecentTradesSection(trades: RecentTrades(items: [], totalCount: 0))
    }
    .padding()
    .frame(width: 280)
    .background(Color.black.opacity(0.9))
}
