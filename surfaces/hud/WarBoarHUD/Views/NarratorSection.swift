import SwiftUI

/// Narrator section displaying Phoenix-generated observations.
/// Constrained height — not dominant, part of balanced layout.
///
/// INV-HUD-NO-SUGGEST: Displays facts only, no suggestions.
/// Phoenix generates these lines; HUD displays them verbatim.
struct NarratorSection: View {
    let narrator: Narrator
    let maxLines: Int = 6  // Reasonable for constrained height

    var body: some View {
        VStack(alignment: .leading, spacing: HUDSpacing.sm) {
            // Header styled like the spec mockup
            HStack {
                Image(systemName: "eye.fill")
                    .font(.system(size: HUDIcon.medium, weight: .medium))
                    .foregroundColor(.textTertiary)

                Text("WARBOAR OBSERVES")
                    .font(HUDFont.sectionTitle)
                    .foregroundColor(.textTertiary)
                    .tracking(0.5)

                Spacer()
            }

            // Narrator box — scrollable, 50% taller for better vertical balance
            ScrollView(.vertical, showsIndicators: false) {
                VStack(alignment: .leading, spacing: HUDSpacing.xs) {
                    if narrator.lines.isEmpty {
                        emptyState
                    } else {
                        ForEach(visibleLines) { line in
                            NarratorLineView(line: line)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .topLeading)
            }
            .frame(maxWidth: .infinity, minHeight: 195)  // Expanded for vertical balance
            .padding(HUDSpacing.cardPadding)
            .background(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color.separator, lineWidth: 1)
                    .background(
                        RoundedRectangle(cornerRadius: 6)
                            .fill(Color.sectionBackground)
                    )
            )
        }
    }

    private var visibleLines: [NarratorLine] {
        Array(narrator.lines.prefix(maxLines))
    }

    private var emptyState: some View {
        HStack {
            Image(systemName: "ellipsis")
                .font(.system(size: HUDIcon.small))
                .foregroundColor(.textMuted)

            Text("Awaiting observations...")
                .font(HUDFont.narrator)
                .foregroundColor(.textMuted)
                .italic()

            Spacer()
        }
        .padding(.vertical, HUDSpacing.sm)
    }
}

struct NarratorLineView: View {
    let line: NarratorLine

    var body: some View {
        HStack(alignment: .top, spacing: HUDSpacing.sm) {
            // Timestamp
            Text(line.timestamp)
                .font(HUDFont.timestamp)
                .foregroundColor(.textMuted)
                .frame(width: 36, alignment: .leading)

            // Text
            Text(line.text)
                .font(HUDFont.narrator)
                .foregroundColor(.textSecondary)
                .lineLimit(2)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(.vertical, 1)
    }
}

#Preview {
    VStack(spacing: 16) {
        NarratorSection(narrator: Narrator(
            lines: [
                NarratorLine(timestamp: "14:32", text: "London active, 2h remaining.", sourceBeadId: nil),
                NarratorLine(timestamp: "14:31", text: "EURUSD +15 pips, holding steady.", sourceBeadId: "T1"),
                NarratorLine(timestamp: "14:31", text: "Systems nominal. Heartbeat 5s ago.", sourceBeadId: nil),
                NarratorLine(timestamp: "14:30", text: "GBPUSD 4/5 gates, watching.", sourceBeadId: nil),
                NarratorLine(timestamp: "14:28", text: "Position opened EURUSD LONG.", sourceBeadId: "T1"),
                NarratorLine(timestamp: "14:25", text: "Gate threshold met for EURUSD.", sourceBeadId: nil),
            ],
            bufferSize: 20
        ))
        .frame(height: 180)

        NarratorSection(narrator: Narrator(lines: [], bufferSize: 20))
    }
    .padding()
    .frame(width: 280)
    .background(Color.black.opacity(0.9))
}
