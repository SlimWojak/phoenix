import Foundation
import Combine

/// Watches manifest.json for changes and publishes updates.
///
/// Invariants:
/// - INV-HUD-ATOMIC-READ: Only reads complete, valid JSON
/// - INV-HUD-STALE-VISIBLE: Detects stale state (>60s since generated_at)
///
/// Features:
/// - DispatchSource file monitoring (primary)
/// - Fallback polling timer (1s if DispatchSource unavailable)
/// - 500ms throttle cap (prevents UI flooding)
/// - Parse error resilience (keeps last valid manifest)
final class ManifestWatcher: ObservableObject {

    // MARK: - Published State

    /// Current manifest state (last successfully parsed)
    @Published private(set) var manifest: StateManifest?

    /// Whether manifest is stale (generated_at > threshold ago)
    @Published private(set) var isStale: Bool = false

    /// Age of current manifest in seconds
    @Published private(set) var manifestAgeSeconds: Int = 0

    /// Current watcher state
    @Published private(set) var watcherState: WatcherState = .idle

    /// Last error encountered (for debugging)
    @Published private(set) var lastError: WatcherError?

    // MARK: - Configuration

    /// Threshold for considering manifest stale (default 60s per spec)
    let staleThreshold: TimeInterval

    /// Minimum interval between UI updates (throttle cap)
    private let throttleInterval: TimeInterval = 0.5  // 500ms

    /// Fallback polling interval when DispatchSource unavailable
    private let fallbackPollInterval: TimeInterval = 1.0  // 1s

    // MARK: - Private State

    private var fileDescriptor: Int32 = -1
    private var dispatchSource: DispatchSourceFileSystemObject?
    private var fallbackTimer: Timer?
    private var staleCheckTimer: Timer?
    private var lastUpdateTime: Date = .distantPast
    private var watchedURL: URL?

    private let fileQueue = DispatchQueue(label: "com.warboar.hud.filewatcher", qos: .userInitiated)

    // MARK: - Initialization

    init(staleThreshold: TimeInterval = 60) {
        self.staleThreshold = staleThreshold
    }

    deinit {
        stopWatching()
    }

    // MARK: - Public API

    /// Start watching a manifest file
    func startWatching(url: URL) {
        stopWatching()

        watchedURL = url
        watcherState = .starting

        // Initial load
        loadManifest(from: url)

        // Try DispatchSource first
        if setupDispatchSource(for: url) {
            watcherState = .watching
            print("📡 ManifestWatcher: DispatchSource active on \(url.lastPathComponent)")
        } else {
            // Fallback to polling
            setupFallbackPolling(for: url)
            watcherState = .polling
            print("⏱ ManifestWatcher: Fallback polling active on \(url.lastPathComponent)")
        }

        // Start stale check timer
        setupStaleCheckTimer()
    }

    /// Start watching the default mock manifest (for development)
    func startWatchingMock() {
        // Try bundle first
        if let bundleURL = Bundle.main.url(forResource: "MockManifest", withExtension: "json") {
            startWatching(url: bundleURL)
            return
        }

        // Fallback to dev path
        let devPath = NSString(string: "~/phoenix-hud/WarBoarHUD/Preview Content/MockManifest.json").expandingTildeInPath
        let devURL = URL(fileURLWithPath: devPath)

        if FileManager.default.fileExists(atPath: devURL.path) {
            startWatching(url: devURL)
        } else {
            // Use preview manifest as fallback
            print("⚠️ ManifestWatcher: No manifest file found, using preview data")
            manifest = ManifestParser.previewManifest
            watcherState = .preview
        }
    }

    /// Stop watching and clean up resources
    func stopWatching() {
        dispatchSource?.cancel()
        dispatchSource = nil

        if fileDescriptor >= 0 {
            close(fileDescriptor)
            fileDescriptor = -1
        }

        fallbackTimer?.invalidate()
        fallbackTimer = nil

        staleCheckTimer?.invalidate()
        staleCheckTimer = nil

        watcherState = .idle
    }

    /// Force reload manifest (useful for testing)
    func forceReload() {
        guard let url = watchedURL else { return }
        loadManifest(from: url)
    }

    // MARK: - DispatchSource Setup

    private func setupDispatchSource(for url: URL) -> Bool {
        fileDescriptor = open(url.path, O_EVTONLY)

        guard fileDescriptor >= 0 else {
            print("⚠️ ManifestWatcher: Failed to open file descriptor for \(url.path)")
            return false
        }

        let source = DispatchSource.makeFileSystemObjectSource(
            fileDescriptor: fileDescriptor,
            eventMask: [.write, .extend, .rename, .delete],
            queue: fileQueue
        )

        source.setEventHandler { [weak self] in
            self?.handleFileEvent(url: url)
        }

        source.setCancelHandler { [weak self] in
            guard let self = self, self.fileDescriptor >= 0 else { return }
            close(self.fileDescriptor)
            self.fileDescriptor = -1
        }

        source.resume()
        dispatchSource = source

        return true
    }

    // MARK: - Fallback Polling

    private func setupFallbackPolling(for url: URL) {
        fallbackTimer = Timer.scheduledTimer(withTimeInterval: fallbackPollInterval, repeats: true) { [weak self] _ in
            self?.loadManifest(from: url)
        }
    }

    // MARK: - Stale Detection

    private func setupStaleCheckTimer() {
        // Check staleness every 5 seconds
        staleCheckTimer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { [weak self] _ in
            self?.updateStaleStatus()
        }
    }

    private func updateStaleStatus() {
        guard let manifest = manifest else {
            isStale = false
            manifestAgeSeconds = 0
            return
        }

        let age = Date().timeIntervalSince(manifest.meta.generatedAt)
        manifestAgeSeconds = Int(age)
        isStale = age > staleThreshold
    }

    // MARK: - File Event Handling

    private func handleFileEvent(url: URL) {
        // Throttle: ignore events within throttle interval
        let now = Date()
        guard now.timeIntervalSince(lastUpdateTime) >= throttleInterval else {
            return
        }

        // Small delay to let write complete (atomic write pattern)
        fileQueue.asyncAfter(deadline: .now() + 0.05) { [weak self] in
            self?.loadManifest(from: url)
        }
    }

    // MARK: - Manifest Loading

    private func loadManifest(from url: URL) {
        do {
            let newManifest = try ManifestParser.parse(fileURL: url)

            // Check sequence to detect out-of-order updates
            if let currentManifest = manifest,
               newManifest.meta.manifestSeq < currentManifest.meta.manifestSeq {
                print("⚠️ ManifestWatcher: Ignoring out-of-order manifest (seq \(newManifest.meta.manifestSeq) < \(currentManifest.meta.manifestSeq))")
                return
            }

            // Update on main thread
            DispatchQueue.main.async { [weak self] in
                guard let self = self else { return }
                self.manifest = newManifest
                self.lastUpdateTime = Date()
                self.lastError = nil
                self.updateStaleStatus()
            }

        } catch {
            handleParseError(error, url: url)
        }
    }

    private func handleParseError(_ error: Error, url: URL) {
        let watcherError: WatcherError

        if let decodingError = error as? DecodingError {
            watcherError = .parseError(decodingError.localizedDescription)
        } else if (error as NSError).domain == NSCocoaErrorDomain {
            watcherError = .fileNotFound(url.path)
        } else {
            watcherError = .unknown(error.localizedDescription)
        }

        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            self.lastError = watcherError

            // Keep last valid manifest (INV-HUD-ATOMIC-READ)
            if self.manifest != nil {
                print("⚠️ ManifestWatcher: Parse error, keeping last valid manifest: \(error)")
            } else {
                print("❌ ManifestWatcher: Parse error, no fallback available: \(error)")
            }
        }
    }
}

// MARK: - Supporting Types

extension ManifestWatcher {

    enum WatcherState: String {
        case idle = "IDLE"
        case starting = "STARTING"
        case watching = "WATCHING"      // DispatchSource active
        case polling = "POLLING"        // Fallback timer active
        case preview = "PREVIEW"        // Using preview data
    }

    enum WatcherError: Error, Equatable {
        case fileNotFound(String)
        case parseError(String)
        case unknown(String)

        var displayMessage: String {
            switch self {
            case .fileNotFound(let path):
                return "File not found: \(path)"
            case .parseError(let message):
                return "Parse error: \(message)"
            case .unknown(let message):
                return "Error: \(message)"
            }
        }
    }
}
