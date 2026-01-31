import SwiftUI

/// Portfolio section showing balance and P&L — ENLARGED for glanceability.
///
/// INV-HUD-COLOR-BOUNDARY: PnL uses neutral white text, NOT green/red.
/// Direction indicated by +/- prefix only.
struct PortfolioSection: View {
    let portfolio: Portfolio

    var body: some View {
        VStack(alignment: .leading, spacing: HUDSpacing.md) {
            // Balance — LARGE display (+50%)
            Text(portfolio.formattedBalance)
                .font(.system(size: 28, weight: .bold, design: .rounded))
                .foregroundColor(.textPrimary)

            // Daily P&L — larger
            HStack(spacing: HUDSpacing.sm) {
                Text("Today:")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.textTertiary)

                Text(portfolio.formattedTodayPnl)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color.forPnL(portfolio.todayPnl))

                Text("(\(portfolio.formattedTodayPct))")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color.forPnL(portfolio.todayPct))

                Spacer()
            }

            // Weekly P&L — larger
            HStack(spacing: HUDSpacing.sm) {
                Text("Week:")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.textTertiary)

                Text(portfolio.formattedWeekPct)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color.forPnL(portfolio.weekPct))

                Spacer()
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .cardStyle()
    }
}

#Preview {
    VStack(spacing: 16) {
        PortfolioSection(portfolio: Portfolio(
            balance: 10234.56,
            currency: "USD",
            todayPnl: 82.50,
            todayPct: 0.81,
            weekPct: 2.3
        ))

        PortfolioSection(portfolio: Portfolio(
            balance: 9850.00,
            currency: "USD",
            todayPnl: -150.25,
            todayPct: -1.5,
            weekPct: -0.8
        ))
    }
    .padding()
    .frame(width: 280)
    .background(Color.black.opacity(0.9))
}
