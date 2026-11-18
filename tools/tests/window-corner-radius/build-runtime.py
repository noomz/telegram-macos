from pathlib import Path
import plistlib
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
source_path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'Telegram-Mac/app/ApplicationContext.swift'
source = source_path.read_text()
start = source.index('extension Window {\n    func applyCornerRadius')
production = source[start:]
output = Path(sys.argv[2]) if len(sys.argv) > 2 else root / '.build/square-window-corners/runtime'
output.mkdir(parents=True, exist_ok=True)
app = output / 'RadiusHarness.app'
(app / 'Contents/MacOS').mkdir(parents=True, exist_ok=True)
fixture = '''import Cocoa

final class Window: NSWindow {
    enum ChromeMode { case standard, compact }
    var isFullScreen: Bool { styleMask.contains(.fullScreen) }
}

__PRODUCTION__

final class Delegate: NSObject, NSApplicationDelegate, NSWindowDelegate {
    var window: Window!
    let mode: Window.ChromeMode = UserDefaults.standard.string(forKey: "CornerMode") == "compact" ? .compact : .standard
    func applicationDidFinishLaunching(_ notification: Notification) {
        window = Window(contentRect: NSRect(x: 100, y: 100, width: 800, height: 600), styleMask: [.titled, .closable, .resizable, .miniaturizable], backing: .buffered, defer: false)
        window.delegate = self
        window.collectionBehavior = [.fullScreenPrimary]
        window.title = "Production corner-radius verification"
        window.appearance = NSAppearance(named: UserDefaults.standard.bool(forKey: "DarkTheme") ? .darkAqua : .aqua)
        window.makeKeyAndOrderFront(nil)
        window.applyCornerRadius(for: mode)
        NSApp.activate(ignoringOtherApps: true)
        if UserDefaults.standard.bool(forKey: "FullScreenCycle") {
            DispatchQueue.main.asyncAfter(deadline: .now() + 2) { self.window.toggleFullScreen(nil) }
        }
    }
    func windowDidEnterFullScreen(_ notification: Notification) {
        window.applyCornerRadius(for: mode)
        DispatchQueue.main.asyncAfter(deadline: .now() + 3) { self.window.toggleFullScreen(nil) }
    }
    func windowDidExitFullScreen(_ notification: Notification) {
        window.applyCornerRadius(for: mode)
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}
let application = NSApplication.shared
let delegate = Delegate()
application.delegate = delegate
application.setActivationPolicy(.regular)
application.run()
'''.replace('__PRODUCTION__', production)
(output / 'main.swift').write_text(fixture)
subprocess.run(['swiftc', str(output / 'main.swift'), '-o', str(app / 'Contents/MacOS/RadiusHarness'), '-framework', 'Cocoa'], check=True)
with (app / 'Contents/Info.plist').open('wb') as stream:
    plistlib.dump({'CFBundleIdentifier': 'space.noomz.CornerRadiusHarness', 'CFBundleName': 'RadiusHarness', 'CFBundleExecutable': 'RadiusHarness', 'CFBundlePackageType': 'APPL', 'NSHighResolutionCapable': True}, stream)
subprocess.run(['codesign', '--force', '--sign', '-', str(app)], check=True)
print(app)
