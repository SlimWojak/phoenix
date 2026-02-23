import SwiftUI

// MARK: - Section Container

/// Standard section container with title
struct SectionContainer<Content: View>: View {
    let title: String
    let icon: String?
    let trailing: String?
    let content: Content

    init(
        _ title: String,
        icon: String? = nil,
        trailing: String? = nil,
        @ViewBuilder content: () -> Content
    ) {
        self.title = title
        self.icon = icon
        self.trailing = trailing
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: HUDSpacing.sm) {
            // Header
            HStack(spacing: HUDSpacing.sm) {
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.system(size: HUDIcon.medium, weight: .medium))
                        .foregroundColor(.textTertiary)
                }

                Text(title)
                    .font(HUDFont.sectionTitle)
                    .foregroundColor(.textTertiary)
                    .textCase(.uppercase)
                    .tracking(0.5)

                Spacer()

                if let trailing = trailing {
                    Text(trailing)
                        .font(HUDFont.sectionSubtitle)
                        .foregroundColor(.textMuted)
                }
            }

            // Content
            content
        }
    }
}

// MARK: - Card Style

struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(HUDSpacing.cardPadding)
            .background(
                RoundedRectangle(cornerRadius: 6)
                    .fill(Color.cardBackground)
            )
    }
}

extension View {
    func cardStyle() -> some View {
        modifier(CardStyle())
    }
}

// MARK: - Row Style

struct RowStyle: ViewModifier {
    let showSeparator: Bool

    func body(content: Content) -> some View {
        VStack(spacing: 0) {
            content
                .padding(.vertical, HUDSpacing.sm)

            if showSeparator {
                Divider()
                    .background(Color.separator)
            }
        }
    }
}

extension View {
    func rowStyle(separator: Bool = true) -> some View {
        modifier(RowStyle(showSeparator: separator))
    }
}

// MARK: - Status Badge

struct StatusBadge: View {
    let text: String
    let color: Color
    let filled: Bool

    init(_ text: String, color: Color, filled: Bool = false) {
        self.text = text
        self.color = color
        self.filled = filled
    }

    var body: some View {
        Text(text)
            .font(HUDFont.statusBadge)
            .foregroundColor(filled ? .white : color)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(
                RoundedRectangle(cornerRadius: 4)
                    .fill(filled ? color : color.opacity(0.15))
            )
    }
}

// MARK: - Health Dot

struct HealthDot: View {
    let health: HealthOverall
    let size: CGFloat

    init(_ health: HealthOverall, size: CGFloat = HUDIcon.healthDot) {
        self.health = health
        self.size = size
    }

    var body: some View {
        Circle()
            .fill(Color.forHealth(health))
            .frame(width: size, height: size)
    }
}

// MARK: - PnL Text

/// Displays PnL value with constitutional neutral colors
struct PnLText: View {
    let value: Double
    let prefix: String
    let suffix: String
    let font: Font

    init(
        _ value: Double,
        prefix: String = "",
        suffix: String = "",
        font: Font = HUDFont.valueMD
    ) {
        self.value = value
        self.prefix = prefix
        self.suffix = suffix
        self.font = font
    }

    var body: some View {
        Text(formattedValue)
            .font(font)
            .foregroundColor(Color.forPnL(value))
    }

    private var formattedValue: String {
        let sign = value >= 0 ? "+" : ""
        return "\(prefix)\(sign)\(formatNumber(value))\(suffix)"
    }

    private func formatNumber(_ num: Double) -> String {
        if abs(num) >= 1000 {
            return String(format: "%.0f", num)
        } else if abs(num) >= 100 {
            return String(format: "%.1f", num)
        } else {
            return String(format: "%.2f", num)
        }
    }
}

// MARK: - Pips Text

struct PipsText: View {
    let pips: Int
    let font: Font

    init(_ pips: Int, font: Font = HUDFont.valueSM) {
        self.pips = pips
        self.font = font
    }

    var body: some View {
        Text(formattedPips)
            .font(font)
            .foregroundColor(Color.forPnL(Double(pips)))
    }

    private var formattedPips: String {
        let sign = pips >= 0 ? "+" : ""
        return "\(sign)\(pips) pips"
    }
}
