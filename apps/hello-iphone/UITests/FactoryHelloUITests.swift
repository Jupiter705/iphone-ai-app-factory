import XCTest

final class FactoryHelloUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure = false
        XCUIDevice.shared.orientation = .portrait
    }

    override func tearDownWithError() throws {
        XCUIDevice.shared.orientation = .portrait
    }

    func testTapPersistsAfterRelaunchAndWorksInLandscape() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset-test-data"]
        app.launch()
        XCTAssertTrue(app.staticTexts["welcomeTitle"].waitForExistence(timeout: 10))
        XCTAssertEqual(app.staticTexts["counterValue"].label, "0")
        app.buttons["incrementButton"].tap()
        XCTAssertEqual(app.staticTexts["counterValue"].label, "1")
        app.terminate()
        app.launchArguments = ["--ui-testing"]
        app.launch()
        XCTAssertTrue(app.staticTexts["counterValue"].waitForExistence(timeout: 10))
        XCTAssertEqual(app.staticTexts["counterValue"].label, "1")
        XCUIDevice.shared.orientation = .landscapeLeft
        XCTAssertTrue(app.buttons["incrementButton"].waitForExistence(timeout: 5))
        app.buttons["incrementButton"].tap()
        XCTAssertEqual(app.staticTexts["counterValue"].label, "2")
        let screenshot = XCTAttachment(screenshot: app.screenshot())
        screenshot.lifetime = .keepAlways
        add(screenshot)
    }
}
