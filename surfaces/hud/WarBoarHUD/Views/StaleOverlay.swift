import SwiftUI

/// Overlay displayed when manifest is stale (>60s since generated_at).
///
/// INV-HUD-STALE-VISIBLE: Red banner "STALE STATE — CHECK PHOENIX"
struct StaleOverlay: View {
    let ageSeconds: Int

    var body: some View {
        VStack(spacing: 4) {
            HStack(spacing: 6) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.system(size: 12, weight: .semibold))

                Text("STALE STATE — CHECK PHOENIX")
                    .font(.system(size: 11, weight: .bold))
                    .tracking(0.5)
            }

            Text("Last update: \(formattedAge) ago")
                .font(.system(size: 10, weight: .medium))
                .opacity(0.8)
        }
        .foregroundColor(.white)
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.staleBanner)
        )
        .padding(.horizontal, 8)
        .padding(.top, 8)
    }

    private var formattedAge: String {
        if ageSeconds < 60 {
            return "\(ageSeconds)s"
        } else if ageSeconds < 3600 {
            let minutes = ageSeconds / 60
            let seconds = ageSeconds % 60
            return "\(minutes)m \(seconds)s"
        } else {
            let hours = ageSeconds / 3600
            let minutes = (ageSeconds % 3600) / 60
            return "\(hours)h \(minutes)m"
        }
    }
}

/// Error overlay for parse/file errors
struct ErrorOverlay: View {
    let error: ManifestWatcher.WatcherError

    var body: some View {
        VStack(spacing: 4) {
            HStack(spacing: 6) {
                Image(systemName: "xmark.octagon.fill")
                    .font(.system(size: 12, weight: .semibold))

                Text(errorTitle)
                    .font(.system(size: 11, weight: .bold))
                    .tracking(0.5)
            }

            Text(error.displayMessage)
                .font(.system(size: 9, weight: .medium))
                .opacity(0.8)
                .lineLimit(2)
                .multilineTextAlignment(.center)
        }
        .foregroundColor(.white)
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.orange.opacity(0.9))
        )
        .padding(.horizontal, 8)
        .padding(.top, 8)
    }

    private var errorTitle: String {
        switch error {
        case .fileNotFound:
            return "NO STATE FILE"
        case .parseError:
            return "CORRUPT MANIFEST"
        case .unknown:
            return "WATCHER ERROR"
        }
    }
}

/// Watcher status indicator (for debugging)
struct WatcherStatusBadge: View {
    let state: ManifestWatcher.WatcherState

    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(statusColor)
                .frame(width: 6, height: 6)

            Text(state.rawValue)
                .font(.system(size: 8, weight: .medium, design: .monospaced))
                .foregroundColor(.white.opacity(0.5))
        }
    }

    private var statusColor: Color {
        switch state {
        case .idle:
            return .gray
        case .starting:
            return .yellow
        case .watching:
            return .green
        case .polling:
            return .orange
        case .preview:
            return .blue
        }
    }
}

#Preview("Stale Overlay") {
    VStack {
        StaleOverlay(ageSeconds: 73)
        StaleOverlay(ageSeconds: 180)
        StaleOverlay(ageSeconds: 3725)
    }
    .frame(width: 280)
    .background(Color.black.opacity(0.8))
}

#Preview("Error Overlay") {
    VStack {
        ErrorOverlay(error: .fileNotFound("/path/to/manifest.json"))
        ErrorOverlay(error: .parseError("Unexpected character at line 42"))
    }
    .frame(width: 280)
    .background(Color.black.opacity(0.8))
}
