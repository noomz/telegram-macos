# Square window corners verification

## Current status

The arm64 Debug app builds, has a Developer ID signature, and runs on `mbp14`.
Complete under the operator-approved scope. The signed app is installed and
running in the Tart VM. Logged-in light- and dark-theme main-window acceptance
passes, with compact behavior preserved as explicitly requested.

After reviewing the results, the operator accepted the recorded original-function
baseline instead of a separate official Telegram 13.1 control run in this VM,
and explicitly chose to keep the test account logged in. These are approved
deviations from the original test plan, not checks claimed to have been performed.
The operator is at the office and cannot currently log in on mbp14 at home.
The same signed app is now installed and running in the operator-selected Tart
VM `tf-t34-mac`. Its Screen Sharing display was opened for login.
The patched-app matrix is verified against the operator-approved decisions:
finite positive overrides are uncapped and existing compact behavior is preserved.
The original spec's literal compact rendering expectation of 0.00 is not met;
that pre-existing behavior was explicitly kept out of scope. Accessibility control was
unblocked by granting `sshd-keygen-wrapper` access under macOS 27's
**Privacy & Security → Device Control and Data Access**. Earlier grants had been
under Screen & System Audio Recording, a different permission.

The original `mac_jr` VM disappeared during the build. The operator authorized
`mbp14` instead and selected the isolated bundle identifier `space.noomz.Telegram`.
The operator also confirmed that finite positive overrides above 28 are used
without a cap, following the spec's rule table rather than its conflicting prose.
After the diagnostic tests exposed AppKit's zero-radius reset behavior, the operator
explicitly chose to preserve existing compact behavior rather than expand the change.

## Artifact

| Field | Value |
|---|---|
| Version | 13.2.0, build 283467 |
| Architecture | arm64 |
| Configuration | Debug, with `GITHUB` to disable the existing updater loop |
| Bundle identifier | `space.noomz.Telegram` |
| Signing identity | Developer ID Application: Siriwat Uamngamsup |
| Signing team | `W6P9Y44LWU` |
| Display name | Telegram |
| Local app | `.build/square-window-corners/artifacts/Telegram.app` |
| Local archive | `.build/square-window-corners/artifacts/Telegram.zip` |
| Archive SHA-256 | `9af246475253d998761721a400078a7f5b14bc8e97e89c86c084878cc343c8cc` |
| Installed app on mbp14 | `/Users/noomz/Applications/NoomzTelegramTest/Telegram.app` |
| Installed app in tf-t34-mac | `/Users/admin/Applications/Telegram.app` |

`codesign --verify --deep --strict` passed both locally and on `mbp14`.
The signature includes hardened runtime and a secure timestamp.
The app is signed, not notarized.

The packaged app has no `CFBundleURLTypes`, `SUFeedURL`, or `SUPublicDSAKeyFile`.
`SUAutomaticallyUpdate` and `SUEnableAutomaticChecks` are false.
The compiled `GITHUB` condition disables `resetUpdater`'s update loop.

## Subsequent local QR-recovery build

The current local archive additionally includes the QR recovery patch documented
in [qr-login-recovery-results.md](qr-login-recovery-results.md). It is installed
locally at `/Users/noomz/Applications/Telegram.app`. The VM and mbp14 installations
listed above still contain the earlier name-restored build, whose archive SHA-256
was `f9ab84ed65120fa2b421017e7f290ced6038f95f17db8ebec8d58e2bc6960c7b`.

## Original display name restored

The operator requested the original Telegram branding. Packaging now writes
`CFBundleName=Telegram` and `CFBundleDisplayName=Telegram` and produces
`Telegram.app`. The isolated identifier, signing team, storage, version, and
corner implementation are unchanged. The app was repackaged from the existing
build and re-signed, not rebuilt.

Both test installations were replaced. The earlier branded app bundles were
moved to each user's Trash for recovery; account data was not moved or removed.
Strict signature verification passed during both installations and again at the
final VM path. Launch Services reports the running app's name as `Telegram`.

The post-rename VM test recorded three passing standard-mode cases before SSH
reset the connection:

| Case | Probe |
|---|---|
| Global 1 | `wid=773 size=900x700 radius=1.00` |
| No override | `wid=778 size=900x700 radius=28.00` |
| Per-app 0 | `wid=783 size=900x700 radius=28.00` |

The interrupted run is not claimed as a full matrix pass. The complete light
and dark matrices below were run before this metadata-only rename.
The saved recovery backup was used to restore and verify both override
preferences and the saved frame preference. The app was relaunched normally;
final evidence was PID `5155` at `/Users/admin/Applications/Telegram.app/Contents/MacOS/Telegram`
and `wid=808 size=900x700 radius=28.00`. No test runner or UI helper remained
running, and the recovery backup was removed after successful restoration.
The operator was notified that VM use was finished; the VM and app were left
running with the account logged in.

Updated local evidence:
- `.build/square-window-corners/telegram-sign.log`
- `.build/square-window-corners/telegram-renamed-vm.log`
- `.build/square-window-corners/recover-preferences.py`

## Tart installation (initial branded artifact)

The operator requested installation in `mac_jr`. Tart had no VM with that name,
so the operator selected the already-running `tf-t34-mac` and requested a visible
guest display. Its guest agent did not respond, but SSH as `admin` worked.

The existing signed ZIP was transferred to the guest and extracted without a
rebuild. Strict deep signature verification passed inside macOS 27.2. The guest
reported bundle ID `space.noomz.Telegram` and signing team `W6P9Y44LWU`.

Launch evidence:

```text
2426 /Users/admin/Applications/Noomz Telegram.app/Contents/MacOS/Telegram
wid=422 size=480x584 radius=16.00
```

This is the authentication window without the host's global override, not a
logged-in main-window acceptance result.

The VM runs with `--no-graphics`. Its existing Screen Sharing service accepts
connections on `192.168.64.6:5900`. The host command
`open vnc://admin@192.168.64.6` succeeded. No VM restart or new remote-access
service configuration was needed. The operator subsequently reported login, but whether that meant Screen Sharing
or Telegram has not been confirmed. UI automation remained unavailable after
Accessibility grants: AppleScript timed out, and the direct helper returned
`trusted=false`, `windowsResult=-25211`.

A preference-driven attempt to run standard-mode cases did not reach the required
window size. All six launches remained `480x648`; these are invalid standard-mode
runs, not evidence of a production radius regression:

| Requested case | Observed probe |
|---|---|
| Global 1 | `wid=599 size=480x648 radius=1.00` |
| No override | `wid=600 size=480x648 radius=16.00` |
| Per-app 0 | `wid=601 size=480x648 radius=16.00` |
| Per-app -5 | `wid=602 size=480x648 radius=0.00` |
| Per-app 4 | `wid=603 size=480x648 radius=4.00` |
| Launch argument 1 | `wid=604 size=480x648 radius=1.00` |

The original absence of both global and app overrides was restored and verified.
The original saved frame preference was reapplied; after relaunch the visible
window was `wid=605 size=480x648 radius=16.00`, not its original 480x616 size.
No exact visible-frame restoration is claimed.

The runner now aborts on the first unmet standard-width precondition instead of
continuing the matrix. That revised runner has not been rerun while the
precondition is unresolved. The recorded run is in
`.build/square-window-corners/logged-in-vm.log`. No new spec invariant is needed:
the existing standard-mode precondition already excludes these measurements.
The operator cancelled the initial clarification prompt about login and app
theme. Later, the correct permission grant enabled direct AX control, and the
chat list and light appearance were visually confirmed. The successful runs
below supersede this earlier blocked attempt.

## Data isolation

The running app's entitlements name these groups:

- `W6P9Y44LWU.space.noomz.Telegram`
- `W6P9Y44LWU.space.noomz.Telegram.TelegramShare`

The running process's open database paths are under
`~/Library/Group Containers/W6P9Y44LWU.space.noomz.Telegram/debug/`.
No official account database was copied. The official Telegram 12.9 process
remained running. The host global corner override was not changed.

The local identity changes cover `ApiCredentials`, the app and extension build
settings, and their entitlement files. Existing Xcode 27 compatibility changes
and the pre-existing development-container fallback remain in the working tree.

## Verification results

| Check | Result | Evidence |
|---|---|---|
| Original radius selection | Expected failure | `square, standard, fullscreen=false: 28.0 != 1.0` |
| Fixed radius selection | PASS | 40 cases from production code with isolated defaults |
| Xcode build | PASS | `** BUILD SUCCEEDED **` |
| Developer ID signature | PASS | Strict deep verification locally and on mbp14 |
| Launch on mbp14, macOS 27.2.1 | PASS | PID `45587`, executable in the installed Noomz Telegram bundle, visible window |
| Initial authentication window | Observed, not main-window acceptance | `wid=10453 size=480x584 radius=1.00` |
| Logged-in criteria 1–5, light appearance | PASS | Six real-app cases on tf-t34-mac, table below |
| Logged-in compact mode, light appearance | PASS against approved preservation decision | 1.00 with global 1; 16.00 without override, matching baseline behavior |
| Logged-in full-screen return, light appearance | PASS | Entered full screen, exited, measured 1.00 |
| Logged-in dark-theme acceptance | PASS against approved compact preservation decision | All six standard cases, both compact cases, and actual full-screen return match light appearance |
| Official 13.1 control in VM | Not run | VM unavailable; mbp14 has official 12.9 |

### Logged-in light- and dark-theme main-window measurements

Direct Accessibility access returned `trusted=true`, `windowsResult=0` after
the correct grant. The app was visually confirmed to show the chat list in
light appearance with the System appearance option selected. No chat content
is included in the report. Direct AX resizing reached standard mode; System
Events AppleScript remained unavailable and was not used for these results.

The operator switched the app to dark appearance and confirmed "dark ready"
before the second matrix. No macOS appearance setting was changed by the runner.

| Case | Light probe | Dark probe |
|---|---|---|
| Global 1 | `wid=641 size=900x700 radius=1.00` | `wid=708 size=900x700 radius=1.00` |
| No override | `wid=646 size=900x700 radius=28.00` | `wid=713 size=900x700 radius=28.00` |
| Per-app 0 | `wid=651 size=900x700 radius=28.00` | `wid=718 size=900x700 radius=28.00` |
| Per-app -5 | `wid=656 size=900x700 radius=28.00` | `wid=723 size=900x700 radius=28.00` |
| Per-app 4 | `wid=661 size=900x700 radius=4.00` | `wid=728 size=900x700 radius=4.00` |
| Launch argument 1 | `wid=666 size=900x700 radius=1.00` | `wid=733 size=900x700 radius=1.00` |
| Compact, global 1 | `wid=680 size=480x732 radius=1.00` | `wid=743 size=480x732 radius=1.00` |
| After leaving full screen, global 1 | `wid=680 size=900x700 radius=1.00` | `wid=743 size=900x700 radius=1.00` |
| Compact, no override | `wid=696 size=480x732 radius=16.00` | `wid=757 size=480x732 radius=16.00` |

Full-screen entry was independently confirmed by AX status:
`pid=4530 position=0.0,0.0 size=1920.0x1080.0 fullscreen=1`.
Dark-mode entry was also confirmed:
`pid=4779 position=0.0,0.0 size=1920.0x1080.0 fullscreen=1`.
Exit status reported `fullscreen=0` before each final radius measurement.
The approved compact-mode behavior differs from the spec's original literal
0.00 rendering expectation; it is not reported as satisfying that original
expectation.

The runner restored and verified the original absence of both global and
per-app overrides after each suite. It reapplied the original saved frame
preference and relaunched the app. These runs used the isolated domain
`space.noomz.Telegram`, not the official app's domain.

Evidence:
- `.build/square-window-corners/logged-in-light-vm.log`
- `.build/square-window-corners/logged-in-light-transitions-vm.log`
- `.build/square-window-corners/logged-in-dark-vm.log`
- `.build/square-window-corners/logged-in-dark-transitions-vm.log`

The focused test covers missing, zero, negative, positive, fractional, large,
NaN, and infinite values across standard, compact, and full-screen states.
It substitutes only the defaults dependency. It does not test AppKit rendering.

The runtime test app compiles the actual `Window.applyCornerRadius` extension
against an `NSWindow` subclass. Its measurements are supplemental, not a
substitute for the logged-in Telegram acceptance matrix.

### Recorded diagnostic measurements

Each light and dark result below came from a separate window on mbp14.
The diagnostic app's own preferences were removed after the per-app tests.
No global preference was changed.

| Case | Light probe | Dark probe |
|---|---|---|
| Global override 1 | `wid=10651 size=800x632 radius=1.00` | `wid=10694 size=800x632 radius=1.00` |
| Launch override 0 | `wid=10654 size=800x632 radius=28.00` | `wid=10697 size=800x632 radius=28.00` |
| Launch override 1 | `wid=10660 size=800x632 radius=1.00` | `wid=10703 size=800x632 radius=1.00` |
| Launch override 4 | `wid=10663 size=800x632 radius=4.00` | `wid=10706 size=800x632 radius=4.00` |
| Launch override 40 | `wid=10666 size=800x632 radius=40.00` | `wid=10709 size=800x632 radius=40.00` |
| Launch override NaN | `wid=10669 size=800x632 radius=28.00` | `wid=10712 size=800x632 radius=28.00` |
| Launch override infinity | `wid=10672 size=800x632 radius=28.00` | `wid=10715 size=800x632 radius=28.00` |
| Per-app override 4 | `wid=10791 size=800x632 radius=4.00` | `wid=10803 size=800x632 radius=4.00` |
| Per-app override -5 | `wid=10794 size=800x632 radius=28.00` | `wid=10806 size=800x632 radius=28.00` |
| Per-app override 0 | `wid=10797 size=800x632 radius=28.00` | `wid=10809 size=800x632 radius=28.00` |
| Launch override 1 over per-app 4 | `wid=10800 size=800x632 radius=1.00` | `wid=10812 size=800x632 radius=1.00` |
| After diagnostic full-screen cycle | `wid=10684 size=800x632 radius=1.00` | `wid=10727 size=800x632 radius=1.00` |

The unchanged baseline under global override 1 produced
`wid=10648 size=800x632 radius=28.00`. This control used the original production
function in the diagnostic app, not official Telegram 13.1.

The first diagnostic run failed its launch-argument `-5` expectation. That argument
did not override the existing global value of 1. Setting -5 in the diagnostic
app's persistent preferences produced 28.00 in both themes, as required.

### Compact behavior preserved

The original requirement of a measured 0.00 failed for both the baseline and the
patched diagnostic app. Calling `_setCornerRadius:0` resets these ordinary
NSWindow windows to AppKit's default. The operator chose to preserve that behavior.
The rule tests still verify that compact mode passes zero to the setter.

| Theme and override | Baseline probe | Patched probe |
|---|---|---|
| Light, 0 | `wid=11000 size=800x632 radius=16.00` | `wid=11003 size=800x632 radius=16.00` |
| Light, 1 | `wid=11011 size=800x632 radius=1.00` | `wid=11014 size=800x632 radius=1.00` |
| Light, 4 | `wid=11017 size=800x632 radius=4.00` | `wid=11020 size=800x632 radius=4.00` |
| Dark, 0 | `wid=11023 size=800x632 radius=16.00` | `wid=11026 size=800x632 radius=16.00` |
| Dark, 1 | `wid=11029 size=800x632 radius=1.00` | `wid=11032 size=800x632 radius=1.00` |
| Dark, 4 | `wid=11035 size=800x632 radius=4.00` | `wid=11038 size=800x632 radius=4.00` |

The 12 comparison measurements pass. The logged-in Telegram tests subsequently confirmed the same 1.00 and 16.00
compact measurements in both themes, as recorded above.

## Reproduction commands

Rule verification:

```sh
python3 tools/tests/window-corner-radius/run.py
```

A source-path argument runs the same tests against an older implementation.
The baseline from `HEAD` fails the override-1 case.

Build command used for the isolated app:

```sh
xcodebuild -workspace Telegram-Mac.xcworkspace -scheme Telegram \
  -configuration Debug \
  -derivedDataPath .build/square-window-corners/DerivedData \
  -destination platform=macOS,arch=arm64 \
  ARCHS=arm64 ONLY_ACTIVE_ARCH=YES CODE_SIGNING_ALLOWED=NO \
  COMPILER_INDEX_STORE_ENABLE=NO \
  'SWIFT_ACTIVE_COMPILATION_CONDITIONS=$(inherited) GITHUB' build
```

Local build and signing records:

- `.build/square-window-corners/isolated-build.log`
- `.build/square-window-corners/isolated-sign.log`
- `.build/square-window-corners/sign.py`
- `.build/square-window-corners/runtime-test.log`
- `.build/square-window-corners/runtime-domain.log`
- `.build/square-window-corners/runtime-baseline.log`
- `.build/square-window-corners/runtime-compact-preserved.log`

Signing copies the build output to a separate artifact, preserves the Telegram display name,
removes URL and update registrations, signs nested code before the outer bundle,
and verifies the result. It does not overwrite the installed official app.

## Earlier test-environment blockers (resolved by switching to the VM)

The SSH-launched `osascript` could not use Accessibility on `mbp14`.
Testing subsequently moved to `tf-t34-mac`, where the operator logged into the
app and granted the correct Device Control and Data Access permission.
Direct AX control then worked. No permission database was modified, and the
operator entered login credentials directly.

Chrome Remote Desktop's host is installed and running, but the operator does not
know its PIN. The operator authorized enabling macOS Screen Sharing instead.
`sudo -n launchctl enable system/com.apple.screensharing` returned
`sudo: a password is required`. No Screen Sharing setting changed. Enabling it
requires the operator to authenticate in their own terminal. No shared VNC
password, router forwarding, or privacy-permission bypass was configured.
