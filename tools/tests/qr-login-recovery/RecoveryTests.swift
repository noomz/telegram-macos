import Foundation
import XCTest
import SwiftSignalKit

enum ExportAuthTransferTokenError: Error { case generic, limitExceeded }
struct AuthTransferExportedToken: Equatable { let validUntil: Int32 }
enum ExportAuthTransferTokenResult: Equatable {
    case displayToken(AuthTransferExportedToken)
    case changeAccountAndRetry(Account)
    case passwordRequested(Account)
    case loggedIn
}
enum UnauthorizedAccountStateContents: Equatable { case empty }
final class Account: Equatable {
    static func == (lhs: Account, rhs: Account) -> Bool { lhs === rhs }
    let network = Network()
    let updateLoginTokenEvents = Signal<Void, NoError>.never()
}
final class Network { var globalTime: Double { Date().timeIntervalSince1970 } }
class ViewController {}
final class TokenController: ViewController {
    func update(_ token: AuthTransferExportedToken?, cancel: @escaping () -> Void, loginWithPasskey: @escaping () -> Void) {}
}
struct PeerId { let id: Int64 }
struct Peer { let peerId: PeerId }
struct Accounts { let accounts: [(Int, Peer)] = [] }
final class SharedContext {
    let accountManager = 0
    let activeAccounts = Signal<Accounts, NoError>.single(Accounts())
}
final class Auth {
    var attempts = 0
    var failuresRemaining = 2
    var failure: ExportAuthTransferTokenError = .generic
    func exportAuthTransferToken(accountManager: Int, otherAccountUserIds: [Int64], syncContacts: Bool) -> Signal<ExportAuthTransferTokenResult, ExportAuthTransferTokenError> {
        attempts += 1
        let shouldFail = failuresRemaining > 0
        failuresRemaining -= 1
        return Signal { subscriber in
            if shouldFail { subscriber.putError(self.failure) }
            else {
                subscriber.putNext(.displayToken(AuthTransferExportedToken(validUntil: Int32(Date().timeIntervalSince1970) + 30)))
                subscriber.putCompletion()
            }
            return EmptyDisposable
        }
    }
}
final class Engine { let auth = Auth() }
final class Controller {
    struct State: Equatable {
        var state: UnauthorizedAccountStateContents? = .empty
        var tokenAvailable = true
        var tokenResult: ExportAuthTransferTokenResult?
        var lockAfterLogin = false
        var qrEnabled = true
    }
    let sharedContext = SharedContext()
    let engine = Engine()
    var account = Account()
    let token_c = TokenController()
    let password_entry_c = ViewController()
    let tokenDisposable = MetaDisposable()
    let exportTokenDisposable = MetaDisposable()
    let tokenEventsDisposable = MetaDisposable()
    let stateValue = Atomic(value: State())
    let statePromise = ValuePromise(State(), ignoreRepeated: true)
    func refresh() -> () -> Void {
        let sharedContext = self.sharedContext
        let stateValue = self.stateValue
        let updateState: ((State) -> State) -> Void = { f in
            self.statePromise.set(stateValue.modify(f))
        }
REFRESH_SOURCE
        return refreshToken
    }
    func show(_ state: State, refresh: @escaping () -> Void) {
        updateState(state, refreshToken: refresh, updateState: { _ in })
    }
STATE_SOURCE
    deinit {
        tokenDisposable.dispose()
        exportTokenDisposable.dispose()
        tokenEventsDisposable.dispose()
    }
}
final class RecoveryTests: XCTestCase {
    func testRepeatedFailuresRecoverWithoutAnotherStateChange() {
        let controller = Controller()
        let recovered = expectation(description: "QR token arrives after two expired-token failures")
        let disposable = controller.statePromise.get().start(next: { state in
            if case .displayToken = state.tokenResult { recovered.fulfill() }
        })
        controller.refresh()()
        wait(for: [recovered], timeout: 6)
        XCTAssertEqual(controller.engine.auth.attempts, 3)
        disposable.dispose()
    }
    func testDisplayedTokenWaitsInsteadOfImmediatelyExportingAgain() {
        let controller = Controller()
        var state = Controller.State()
        state.tokenResult = .displayToken(AuthTransferExportedToken(validUntil: Int32(Date().timeIntervalSince1970) + 30))
        var refreshes = 0
        controller.show(state, refresh: { refreshes += 1 })
        XCTAssertEqual(refreshes, 0)
    }
    func testInitialEmptyStateRequestsToken() {
        let controller = Controller()
        var refreshes = 0
        controller.show(Controller.State(), refresh: { refreshes += 1 })
        XCTAssertEqual(refreshes, 1)
    }
    func testDisposingRequestCancelsScheduledRetry() {
        let controller = Controller()
        controller.refresh()()
        controller.tokenDisposable.dispose()
        let elapsed = expectation(description: "retry delay elapsed")
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { elapsed.fulfill() }
        wait(for: [elapsed], timeout: 3)
        XCTAssertEqual(controller.engine.auth.attempts, 1)
    }
    func testLeavingQRScreenCancelsScheduledRetry() {
        let controller = Controller()
        controller.refresh()()
        var state = Controller.State()
        state.tokenAvailable = false
        controller.show(state, refresh: controller.refresh())
        let elapsed = expectation(description: "retry delay elapsed after leaving QR")
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { elapsed.fulfill() }
        wait(for: [elapsed], timeout: 3)
        XCTAssertEqual(controller.engine.auth.attempts, 1)
    }
    func testRateLimitIsNotAutomaticallyRetried() {
        let controller = Controller()
        controller.engine.auth.failure = .limitExceeded
        controller.refresh()()
        let elapsed = expectation(description: "retry delay elapsed")
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { elapsed.fulfill() }
        wait(for: [elapsed], timeout: 3)
        XCTAssertEqual(controller.engine.auth.attempts, 1)
    }
}
