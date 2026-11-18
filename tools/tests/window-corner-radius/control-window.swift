import AppKit
import ApplicationServices

func require(_ result: AXError, _ operation: String) {
    if result != .success {
        fputs("\(operation): AXError \(result.rawValue)\n", stderr)
        exit(1)
    }
}

func attribute(_ element: AXUIElement, _ name: String) -> CFTypeRef {
    var value: CFTypeRef?
    require(AXUIElementCopyAttributeValue(element, name as CFString, &value), name)
    guard let value else { exit(1) }
    return value
}

guard AXIsProcessTrusted() else {
    fputs("Accessibility permission is not granted\n", stderr)
    exit(1)
}
guard let app = NSRunningApplication.runningApplications(withBundleIdentifier: "space.noomz.Telegram").first else {
    exit(2)
}
let element = AXUIElementCreateApplication(app.processIdentifier)
require(AXUIElementSetMessagingTimeout(element, 5), "timeout")
guard let windows = attribute(element, kAXWindowsAttribute) as? [AXUIElement], windows.count == 1 else {
    fputs("Expected exactly one app window\n", stderr)
    exit(1)
}
let window = windows[0]
let args = Array(CommandLine.arguments.dropFirst())
if args.count == 3, args[0] == "size", let width = Double(args[1]), let height = Double(args[2]) {
    var size = CGSize(width: width, height: height)
    require(AXUIElementSetAttributeValue(window, kAXSizeAttribute as CFString, AXValueCreate(.cgSize, &size)!), "resize")
} else if args.count == 2, args[0] == "fullscreen", ["true", "false"].contains(args[1]) {
    require(AXUIElementSetAttributeValue(window, "AXFullScreen" as CFString, args[1] == "true" ? kCFBooleanTrue : kCFBooleanFalse), "fullscreen")
} else if args.count == 3, args[0] == "click", let x = Double(args[1]), let y = Double(args[2]) {
    var position = CGPoint.zero
    var size = CGSize.zero
    let positionValue = attribute(window, kAXPositionAttribute) as! AXValue
    let sizeValue = attribute(window, kAXSizeAttribute) as! AXValue
    guard AXValueGetValue(positionValue, .cgPoint, &position), AXValueGetValue(sizeValue, .cgSize, &size),
          x >= 0, y >= 0, x < size.width, y < size.height else { exit(1) }
    app.activate(options: [.activateIgnoringOtherApps])
    usleep(500_000)
    let point = CGPoint(x: position.x + x, y: position.y + y)
    for type in [CGEventType.leftMouseDown, .leftMouseUp] {
        guard let event = CGEvent(mouseEventSource: nil, mouseType: type, mouseCursorPosition: point, mouseButton: .left) else { exit(1) }
        event.postToPid(app.processIdentifier)
    }
} else if !args.isEmpty && args != ["status"] {
    fputs("Usage: control-window [status | size W H | fullscreen true/false | click X Y]\n", stderr)
    exit(2)
}
var position = CGPoint.zero
var size = CGSize.zero
let positionValue = attribute(window, kAXPositionAttribute) as! AXValue
let sizeValue = attribute(window, kAXSizeAttribute) as! AXValue
AXValueGetValue(positionValue, .cgPoint, &position)
AXValueGetValue(sizeValue, .cgSize, &size)
print("pid=\(app.processIdentifier) position=\(position.x),\(position.y) size=\(size.width)x\(size.height) fullscreen=\(attribute(window, "AXFullScreen"))")
