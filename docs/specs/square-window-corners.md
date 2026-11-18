# Square window corners in Telegram for macOS 27

## Goal

A user who sets the AppKit corner-radius override gets square Telegram windows,
the same as every other AppKit app on their Mac:

```sh
defaults write -g NSConvolutionOverride1 -float 1
```

Today Telegram 13.x ignores that setting on macOS 27. It calls the private
`-[NSWindow _setCornerRadius:]` with its own value, so its main window stays
rounded at 28pt while Finder, TextEdit and kitty are square. Telegram 12.9 does
not make that call, which is why 12.9 is square on the same machine.

Measured on macOS 27.2.1 with `NSConvolutionOverride1 = 1` set globally
(`tools/corner-probe`):

| App | WindowServer corner radius |
|---|---|
| Finder | 1.00 |
| kitty | 1.00 |
| Telegram 13.1.0 (official) | 28.00 |

## Scope

In scope: the radius Telegram passes to `_setCornerRadius:` for its main window
(`Window.applyCornerRadius(for:)` in `Telegram-Mac/app/ApplicationContext.swift`).

Out of scope for this change:

- The inner sidebar card radius (`MainController_View.containerCornerRadius`,
  20pt on macOS 26+). It is a card inside the window, not the window frame.
  See [Open questions](#open-questions).
- Windows Telegram does not round itself (media viewer, separate chat windows).
  AppKit already applies the override to them.
- Picking up a changed setting while Telegram runs. AppKit apps read it at
  launch, so a relaunch is the expected way to apply it.

## The rule

The window radius is a function of three inputs:

| Input | Source |
|---|---|
| `override` | `UserDefaults.standard` value for `NSConvolutionOverride1` |
| `mode` | `Window.ChromeMode`: `.standard` or `.compact` |
| `isFullScreen` | `NSWindow.isFullScreen` |

| Case | Radius |
|---|---|
| full screen | 0 |
| `.compact` | 0 |
| `.standard`, `override` is finite and greater than 0 | `override` |
| `.standard`, `override` missing, 0, negative or not finite | 28 (unchanged default) |

`override` follows AppKit's own handling of the key, measured in a macOS 27.2 VM
with TextEdit launched as `open -a TextEdit --args -NSConvolutionOverride1 <v>`:

| `v` | TextEdit radius |
|---|---|
| unset | 16.00 |
| 0 | 16.00 (ignored) |
| -5 | 16.00 (ignored) |
| 1 | 1.00 |
| 4 | 4.00 |

Because the value comes from `UserDefaults.standard`, all three ways a user can
set it work with no extra code: the global domain (`defaults write -g`), the
Telegram domain (`defaults write ru.keepcoder.Telegram`), and a launch argument
(`--args -NSConvolutionOverride1 1`).

Compact and full-screen stay at 0 even when the override is set. The override
only ever makes the standard window less round, never rounder.

## Implementation notes

The rule touches one function. `applyCornerRadius(for:)` is called from all
three places that set the radius, so they inherit it:

- `AppDelegate.swift`, first chrome mode at launch.
- `ApplicationContext.applyWindowChrome(forState:)`, on split-view state change.
- `ApplicationContext.handleFullScreenDidChange(_:)`, on leaving full screen.

The working tree already has a draft of this change. It differs from the rule in
three ways that the final change fixes:

1. It applies the override in compact and full-screen modes, raising 0 to the
   override value.
2. It accepts 0 and negative values, where AppKit falls back to the default.
3. It adds a code comment, which `AGENTS.md` forbids.

## Acceptance criteria

With the fork build running in the test VM:

1. Global override 1, standard mode: main window radius reads 1.00.
2. No override, standard mode: radius reads 28.00.
3. Override 0 or -5, standard mode: radius reads 28.00.
4. Override 4 set only in the `ru.keepcoder.Telegram` domain: radius reads 4.00.
5. Override passed only as a launch argument: radius reads 1.00.
6. Compact mode, with or without override: 0.00. Compact means a single column
   with no folder sidebar. At launch it means a window narrower than 650pt.
7. After leaving full screen with override 1: radius reads 1.00 again.
8. Light and dark themes give the same radius in every case above.

## Test plan

### Where to test: Tart VM, not mbp14

The Tart VM `mac_jr` is enough, and it is the safer place:

- It runs macOS 27.2 arm64. The code path is gated on
  `#available(macOS 27.0, *)`, so any macOS 27 guest exercises it.
- Its WindowServer applies corner radii the same way as hardware. In the VM,
  `tools/corner-probe` read TextEdit at 16.00 by default and 1.00 with the
  override, matching the host.
- It has no Telegram account data. The fork keeps the official bundle ID
  (`ru.keepcoder.Telegram`), team (`6N38VWS5BX`) and app group, so on mbp14 a
  fork build could open the same data folder as the installed official
  Telegram 12.9 and migrate its database. This risk is inferred from the
  entitlements, not observed.

Use mbp14 only if a VM run shows something the VM cannot reproduce, and only
after the fork has its own bundle ID, team and app group (`INSTALL.md`,
"If you want to develop a fork", step 4).

### The probe

`tools/corner-probe.c` prints the WindowServer corner radius of every on-screen,
layer-0 window owned by a named app. It asks WindowServer directly through
`SLSWindowIteratorGetCornerRadii`, the call JankyBorders uses, so it measures
what is drawn, not what Telegram meant to set. A screenshot is not a substitute:
`screencapture -l` renders the backing store and always looks square.

```sh
clang -O2 -o corner-probe tools/corner-probe.c \
  -framework ApplicationServices -F/System/Library/PrivateFrameworks -framework SkyLight
./corner-probe Telegram
# wid=14885 size=1420x1252 radius=28.00
```

The probe is calibrated. On the host it separates official Telegram 13.1
(28.00) from Finder and kitty (1.00) under the same global override, which is
the exact failure this change fixes.

### Steps

1. Build the fork on the host with Xcode 27.2 (the `XCODE27.md` project edits
   are already in the working tree).
2. Control run: install official Telegram 13.1 in the VM, set the global
   override to 1, log in, and confirm the probe reads 28.00. If it does not,
   stop: the VM cannot show the bug, so it cannot show the fix.
3. Install the fork build in the VM. Log in with a test account.
4. Run acceptance criteria 1 to 8. For each, relaunch Telegram after changing
   the setting, put the window in the stated mode, and record the probe line.
5. Save the probe output for every case in a table next to this spec.
6. Log the test account out of the VM.

### Open risks

- Login. `ApplicationContext` exists only after login, so every case needs a
  logged-in session. INSTALL.md says the built-in `apiId` is rate-limited and
  only meant for verifying binaries. A short manual test may fit inside that.
  Anything automated or repeated needs the fork's own `apiId`.
- Signing. A local build cannot be signed by team `6N38VWS5BX`, so the app group
  entitlement may be rejected and the app may fail to launch or prompt for
  access. Find out on the first launch in the VM before running the matrix.

## Open questions

- Should the inner sidebar card (20pt) also follow the override, so a square
  window does not hold a rounded card? This is a design call, not a measurable
  one.
