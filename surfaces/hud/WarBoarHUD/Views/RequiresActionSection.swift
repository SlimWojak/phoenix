import SwiftUI

/// Requires Action section for facts and required acknowledgments.
///
/// INV-HUD-NO-SUGGEST: Only facts and required acks, no suggestions.
/// Content allowed: CRITICAL/HALTED states, T2 approval, lease expiry, runbook instructions.
/// Content forbidden: Suggestions, recommendations, implicit guidance.
struct RequiresActionSection: View {
    let items: [ActionItem]

    var body: some View {
        if !items.isEmpty {
            VStack(alignment: .leading, spacing: HUDSpacing.sm) {
                // Header with warning icon
                HStack(spacing: HUDSpacing.sm) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: HUDIcon.medium, weight: .medium))
                        .foregroundColor(.healthAmber)
                        .symbolRenderingMode(.hierarchical)

                    Text("REQUIRES ACTION")
                        .font(HUDFont.sectionTitle)
                        .foregroundColor(.healthAmber)
                        .tracking(0.5)

                    Spacer()

                    Text("\(items.count)")
                        .font(HUDFont.sectionSubtitle)
                        .foregroundColor(.textMuted)
                }

                // Action items
                VStack(spacing: HUDSpacing.xs) {
                    ForEach(items) { item in
                        ActionItemRow(item: item)
                    }
                }
                .padding(HUDSpacing.cardPadding)
                .background(
                    RoundedRectangle(cornerRadius: 6)
                        .fill(Color.warningBanner)
                )
            }
        }
    }
}

struct ActionItemRow: View {
    let item: ActionItem

    var body: some View {
        HStack(alignment: .top, spacing: HUDSpacing.sm) {
            // Severity icon
            Image(systemName: iconName)
                .font(.system(size: HUDIcon.small, weight: .medium))
                .foregroundColor(severityColor)

            // Message
            Text(item.message)
                .font(HUDFont.label)
                .foregroundColor(.textPrimary)
                .lineLimit(2)

            Spacer()
        }
    }

    private var iconName: String {
        switch item.severity {
        case .critical:
            return "exclamationmark.octagon.fill"
        case .warning:
            return "exclamationmark.triangle.fill"
        case .info:
            return "info.circle.fill"
        }
    }

    private var severityColor: Color {
        switch item.severity {
        case .critical:
            return .healthRed
        case .warning:
            return .healthAmber
        case .info:
            return .activeAccent
        }
    }
}

#Preview {
    VStack(spacing: 16) {
        RequiresActionSection(items: [
            ActionItem(type: .leaseExpiry, message: "Lease expires 58m — review?", severity: .warning, actionRequired: true),
        ])

        RequiresActionSection(items: [
            ActionItem(type: .healthCritical, message: "IBKR connection lost", severity: .critical, actionRequired: true),
            ActionItem(type: .t2Approval, message: "T2 trade pending approval", severity: .info, actionRequired: true),
        ])

        RequiresActionSection(items: [])
    }
    .padding()
    .frame(width: 280)
    .background(Color.black.opacity(0.9))
}
