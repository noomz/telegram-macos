# QR login recovery

## Reported behavior

The phone accepted a QR scan, but the desktop stayed on the QR screen. A later
attempt also appeared stuck. Local logs recorded two DC5 `auth.importLoginToken`
failures with `400 AUTH_TOKEN_EXPIRED`, followed by no further token requests.
The cause of the server-side expiration itself is not established.

The operator subsequently logged in successfully before this patch was installed.
That success is not evidence for the patch. The logs show successful authorization
activity at 15:20:04, including `updates.getState` and `messages.getDialogs`.

## Confirmed recovery defects

The unchanged HEAD controller failed the regression harness:

- A token request failure clears the token. Repeated equal empty state does not
  trigger another state-driven request, leaving recovery stopped.
- Showing a valid token schedules its expiration timer but also immediately
  exports another token. The extra request is unnecessary and creates competing
  refresh triggers.

Both defects exist in unchanged `packages/AuthUI/Sources/AuthUI/AuthController.swift`,
not in the square-window-corner implementation. The operator explicitly authorized
fixing the reported login behavior after the diagnosis.

## Changes

- Retry generic token-request failures with delays increasing from 1 to 5 seconds.
- Do not automatically retry explicit rate-limit errors.
- Request the first token from empty state, but let a displayed token use its
  existing expiration timer and login-update subscription.
- Cancel pending token requests and retries when QR login becomes unavailable,
  disabled, or locked after login.
- Preserve the existing account data, bundle identifier, and Telegram display name.

## Regression requirements

B1: repeated failed QR requests must not depend on an unequal UI state to recover.
B2: displaying a valid QR token must not immediately export another token.

The executable checks use the actual controller request closure and QR state
handler extracted from source, with simulated authentication responses and the
repository's real SwiftSignalKit. They do not simulate the network protocol or
claim to establish the server-side expiration cause.

```sh
python3 tools/tests/qr-login-recovery/run.py --baseline
python3 tools/tests/qr-login-recovery/run.py
```

Unchanged HEAD fails the repeated-error recovery and premature-export assertions.
The working tree passes six tests covering those cases, initial token generation,
request disposal, leaving the QR screen, and explicit rate-limit handling.

## Build and installation

The Debug arm64 build completed with `GITHUB` defined. The app was Developer ID
signed and installed at `/Users/noomz/Applications/Telegram.app`. Strict deep
signature verification passed. The prior app bundle was moved into the user's
Trash for recovery; no account data was deleted or moved.

An immediate Launch Services open returned error -600 after replacing the exiting
app. Opening a new instance succeeded. The installed process was PID `98463`.
Post-relaunch logs show authorized `updates.getDifference` requests at 15:28:41,
and the main-window probe reported `wid=50998 size=1420x1251 radius=1.00`.
The installed and signed-artifact `Telegram.debug.dylib` SHA-256 values match:
`6ef8886669a0b67299d17b11af6d0b7be53876a26af867628372eed6abc36d12`.

The operator's logged-in session was preserved. No logout or fresh phone QR scan
was performed after installation, so end-to-end fresh QR login remains unverified
on this patched binary. The regression failures are covered by automated tests.

Current archive: `.build/square-window-corners/artifacts/Telegram.zip`.
SHA-256: `9af246475253d998761721a400078a7f5b14bc8e97e89c86c084878cc343c8cc`.

Local evidence:
- `.build/square-window-corners/qr-baseline.log`
- `.build/square-window-corners/qr-fixed-tests.log`
- `.build/square-window-corners/qr-build.log`
- `.build/square-window-corners/qr-sign.log`

## Update channel

This build has no active updater. `GITHUB` compiles out the checking logic inside
`resetUpdater()` in `Telegram-Mac/updater/AppUpdateViewController.swift`.
The Check for Updates action can still show its screen and set an initializing
state, but it does not fetch an upstream update through that path. Packaging also
removes the Sparkle feed and disables automatic checks. Updates to this patched
build require a manual rebuild and installation.

The Tart VM was not used for this fix and still has the earlier build.
