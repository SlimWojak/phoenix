import SwiftUI

@main
struct WarBoarHUDApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        // Empty scene - panel is managed by AppDelegate
        Settings {
            EmptyView()
        }
    }
}
