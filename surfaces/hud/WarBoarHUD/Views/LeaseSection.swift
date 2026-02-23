import SwiftUI

/// Lease section showing active trading lease.
struct LeaseSection: View {
    let lease: Lease

    var body: some View {
        HStack(spacing: HUDSpacing.md) {
            // Lease icon
            Image(systemName: leaseIcon)
                .font(.system(size: HUDIcon.large, weight: .medium))
                .foregroundColor(leaseColor)
                .symbolRenderingMode(.hierarchical)

            // Strategy name or status
            if let strategy = lease.strategy {
                Text(strategy)
                    .font(HUDFont.valueMD)
                    .foregroundColor(.textPrimary)
            } else {
                Text(lease.status.rawValue)
                    .font(HUDFont.valueSM)
                    .foregroundColor(.textSecondary)
            }

            Spacer()

            // Time remaining
            if let timeRemaining = lease.timeRemaining {
                Text(timeRemaining)
                    .font(HUDFont.valueMD)
                    .foregroundColor(timeColor)
            }
        }
        .cardStyle()
    }

    private var leaseIcon: String {
        switch lease.status {
        case .active:
            return "doc.badge.clock"
        case .draft:
            return "doc.badge.ellipsis"
        case .expired:
            return "doc.badge.minus"
        case .revoked, .halted:
            return "doc.badge.xmark"
        case .absent:
            return "doc"
        }
    }

    private var leaseColor: Color {
        switch lease.status {
        case .active:
            return .activeAccent
        case .draft:
            return .textSecondary
        case .expired, .revoked, .halted:
            return .textMuted
        case .absent:
            return .textMuted
        }
    }

    private var timeColor: Color {
        guard lease.status == .active else { return .textMuted }

        // Parse time remaining to check urgency
        // This is a simple heuristic
        if let time = lease.timeRemaining {
            if time.contains("h") {
                return .textPrimary
            } else if time.hasPrefix("0m") || time == "0m" {
                return .healthAmber
            }
        }
        return .textPrimary
    }
}

#Preview {
    VStack(spacing: 16) {
        LeaseSection(lease: Lease(
            status: .active,
            strategy: "ICT_FVG_v1",
            timeRemaining: "3h 30m",
            expiresAt: Date().addingTimeInterval(12600)
        ))

        LeaseSection(lease: Lease(
            status: .active,
            strategy: "SCALP_LONDON",
            timeRemaining: "15m",
            expiresAt: Date().addingTimeInterval(900)
        ))

        LeaseSection(lease: Lease(
            status: .draft,
            strategy: "NEW_STRATEGY",
            timeRemaining: nil,
            expiresAt: nil
        ))

        LeaseSection(lease: Lease(
            status: .absent,
            strategy: nil,
            timeRemaining: nil,
            expiresAt: nil
        ))
    }
    .padding()
    .frame(width: 280)
    .background(Color.black.opacity(0.9))
}
