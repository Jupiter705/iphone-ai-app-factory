import XCTest
@testable import FactoryHello

final class CounterStoreTests: XCTestCase {
    private var suite: String!
    private var defaults: UserDefaults!

    override func setUp() {
        super.setUp()
        suite = "FactoryHello.UnitTests.\(UUID().uuidString)"
        defaults = UserDefaults(suiteName: suite)!
    }

    override func tearDown() {
        defaults.removePersistentDomain(forName: suite)
        defaults = nil
        suite = nil
        super.tearDown()
    }

    func testNewStoreStartsAtZero() {
        XCTAssertEqual(CounterStore(defaults: defaults).count, 0)
    }

    func testIncrementPersistsAcrossStoreInstances() {
        let store = CounterStore(defaults: defaults)
        store.increment()
        store.increment()
        XCTAssertEqual(store.count, 2)
        XCTAssertEqual(CounterStore(defaults: UserDefaults(suiteName: suite)!).count, 2)
    }

    func testCounterDoesNotOverflow() {
        defaults.set(Int.max, forKey: "tapCount")
        let store = CounterStore(defaults: defaults)
        store.increment()
        XCTAssertEqual(store.count, Int.max)
    }
}
