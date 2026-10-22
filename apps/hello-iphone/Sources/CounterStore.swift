import Foundation
import Combine

final class CounterStore: ObservableObject {
    @Published private(set) var count: Int
    private let defaults: UserDefaults
    private let key = "tapCount"

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        count = max(0, defaults.integer(forKey: key))
    }

    func increment() {
        guard count < Int.max else { return }
        count += 1
        defaults.set(count, forKey: key)
    }
}
