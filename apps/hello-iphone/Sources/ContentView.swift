import SwiftUI

struct ContentView: View {
    @ObservedObject var counter: CounterStore

    private var version: String {
        let info = Bundle.main.infoDictionary ?? [:]
        return "v\(info["CFBundleShortVersionString"] as? String ?? "?") (\(info["CFBundleVersion"] as? String ?? "?"))"
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                Text("Hello, iPhone!")
                    .font(.largeTitle.bold())
                    .accessibilityIdentifier("welcomeTitle")
                Text("iPhone AI App Factory")
                    .font(.headline)
                Text("\(counter.count)")
                    .font(.system(size: 64, weight: .bold, design: .rounded))
                    .accessibilityIdentifier("counterValue")
                Button(action: counter.increment) {
                    Text("點我 +1")
                        .font(.title2.bold())
                        .frame(maxWidth: .infinity, minHeight: 52)
                }
                .buttonStyle(.borderedProminent)
                .accessibilityIdentifier("incrementButton")
                Text("次數保存在手機，關閉後再開啟仍會保留。")
                    .font(.body)
                    .multilineTextAlignment(.center)
                Text(version)
                    .font(.caption.monospaced())
                    .accessibilityIdentifier("appVersion")
            }
            .frame(maxWidth: 520)
            .padding(24)
            .frame(maxWidth: .infinity)
        }
    }
}
