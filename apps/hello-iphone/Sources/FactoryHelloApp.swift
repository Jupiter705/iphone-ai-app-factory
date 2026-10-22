import SwiftUI

@main
struct FactoryHelloApp: App {
    @StateObject private var counter: CounterStore

    init() {
        // UI tests opt into their own store; normal launches never reset user data.
        let arguments = ProcessInfo.processInfo.arguments
        let defaults: UserDefaults
        if arguments.contains("--ui-testing") {
            let suite = "FactoryHello.UITests"
            defaults = UserDefaults(suiteName: suite)!
            if arguments.contains("--reset-test-data") {
                defaults.removePersistentDomain(forName: suite)
            }
        } else {
            defaults = .standard
        }
        _counter = StateObject(wrappedValue: CounterStore(defaults: defaults))
    }

    var body: some Scene {
        WindowGroup { ContentView(counter: counter) }
    }
}
