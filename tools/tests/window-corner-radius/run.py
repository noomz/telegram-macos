from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[3]
source_path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'Telegram-Mac/app/ApplicationContext.swift'
source = source_path.read_text()
start = source.index('\n', source.index('typealias SetCornerRadius', source.index('func applyCornerRadius'))) + 1
end = source.index('                unsafeBitCast', start)
selection = source[start:end]
fixture = '''import Foundation

struct Defaults {
    var value: Double = 0
    func double(forKey key: String) -> Double {
        precondition(key == "NSConvolutionOverride1")
        return value
    }
}
enum UserDefaults {
    static var standard = Defaults()
}
enum ChromeMode { case standard, compact }
func radius(mode: ChromeMode, isFullScreen: Bool) -> Double {
__SELECTION__
    return radius
}

let cases: [(String, Double?, Double)] = [
    ("missing", nil, 28),
    ("zero", 0.0, 28),
    ("negative", -5.0, 28),
    ("square", 1.0, 1),
    ("four", 4.0, 4),
    ("fraction", 0.5, 0.5),
    ("large", 40.0, 40),
    ("nan", Double.nan, 28),
    ("infinity", Double.infinity, 28),
    ("negative infinity", -Double.infinity, 28)
]
for (name, value, expected) in cases {
    UserDefaults.standard.value = value ?? 0
    for mode in [ChromeMode.standard, .compact] {
        for fullScreen in [false, true] {
            let actual = radius(mode: mode, isFullScreen: fullScreen)
            let wanted = mode == .standard && !fullScreen ? expected : 0
            precondition(actual == wanted, "\\(name), \\(mode), fullscreen=\\(fullScreen): \\(actual) != \\(wanted)")
        }
    }
}
print("PASS: 40 radius-selection cases using production code and isolated defaults")
'''.replace('__SELECTION__', selection)
with tempfile.TemporaryDirectory(prefix='window-corner-radius-') as directory:
    path = Path(directory)
    (path / 'main.swift').write_text(fixture)
    subprocess.run(['swiftc', str(path / 'main.swift'), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True, env={'HOME': str(path), 'CFFIXED_USER_HOME': str(path)})
