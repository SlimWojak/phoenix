import SwiftUI

/// Session section showing current killzone and time remaining.
struct SessionSection: View {
    let session: Session

    var body: some View {
        VStack(alignment: .leading, spacing: HUDSpacing.sm) {
            // Main row: Killzone + Time remaining
            HStack(alignment: .center) {
                // Killzone indicator
                HStack(spacing: HUDSpacing.sm) {
                    Image(systemName: session.active ? "clock.fill" : "clock")
                        .font(.system(size: HUDIcon.large, weight: .medium))
                        .foregroundColor(session.active ? .activeAccent : .textTertiary)
                        .symbolRenderingMode(.hierarchical)

                    Text(session.kz)
                        .font(HUDFont.valueMD)
                        .foregroundColor(.textPrimary)
                        .fontWeight(.semibold)
                }

                Spacer()

                // Time remaining
                Text(session.timeRemaining)
                    .font(HUDFont.valueLG)
                    .foregroundColor(session.active ? .textPrimary : .textSecondary)

                Text("left")
                    .font(HUDFont.label)
                    .foregroundColor(.textTertiary)
            }

            // Next session row
            if let nextSession = session.nextSession, let nextStart = session.nextStart {
                HStack(spacing: HUDSpacing.xs) {
                    Text("Next:")
                        .font(HUDFont.labelSM)
                        .foregroundColor(.textTertiary)

                    Text(nextSession)
                        .font(HUDFont.labelSM)
                        .foregroundColor(.textSecondary)

                    Text("@")
                        .font(HUDFont.labelSM)
                        .foregroundColor(.textMuted)

                    Text(nextStart)
                        .font(HUDFont.timestamp)
                        .foregroundColor(.textSecondary)
                }
            }
        }
        .cardStyle()
    }
}

#Preview {
    VStack(spacing: 16) {
        SessionSection(session: Session(
            kz: "LONDON",
            active: true,
            timeRemaining: "2h 15m",
            nextSession: "NEW_YORK",
            nextStart: "13:00"
        ))

        SessionSection(session: Session(
            kz: "TOKYO",
            active: false,
            timeRemaining: "0m",
            nextSession: "LONDON",
            nextStart: "08:00"
        ))
    }
    .padding()
    .frame(width: 280)
    .background(Color.black.opacity(0.9))
}
