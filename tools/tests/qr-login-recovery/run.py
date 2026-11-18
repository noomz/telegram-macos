import argparse
import pathlib
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--baseline', action='store_true')
args = parser.parse_args()
root = pathlib.Path(__file__).resolve().parents[3]
path = 'packages/AuthUI/Sources/AuthUI/AuthController.swift'
source = subprocess.check_output(['git', '-C', str(root), 'show', f'HEAD:{path}'], text=True) if args.baseline else (root / path).read_text()
refresh_start = source.index('        let refreshToken:()->Void = ')
refresh_end = source.index('        let engine = self.engine', refresh_start)
refresh = source[refresh_start:refresh_end]
method_start = source.index('    private func updateState(_ state: State,')
method_end = source.index('        } else {\n            switch currentState', method_start)
method = source[method_start:method_end] + '        }\n    }\n'
fixture = pathlib.Path(__file__).with_name('RecoveryTests.swift').read_text()
fixture = fixture.replace('REFRESH_SOURCE', refresh).replace('STATE_SOURCE', method)
package = pathlib.Path(tempfile.mkdtemp(prefix='telegram-qr-recovery-'))
(package / 'Tests').mkdir()
dependency = root / 'submodules/telegram-ios/submodules/SSignalKit'
(package / 'Package.swift').write_text(f'''// swift-tools-version:5.5
import PackageDescription
let package = Package(name: "QRRecovery", platforms: [.macOS(.v10_13)], dependencies: [.package(name: "SSignalKit", path: "{dependency}")], targets: [.testTarget(name: "RecoveryTests", dependencies: [.product(name: "SwiftSignalKit", package: "SSignalKit")], path: "Tests")])
''')
(package / 'Tests/RecoveryTests.swift').write_text(fixture)
print('Testing ' + ('unchanged HEAD' if args.baseline else 'working tree') + ' QR request and state handlers with real SwiftSignalKit', flush=True)
raise SystemExit(subprocess.run(['swift', 'test', '--package-path', str(package)]).returncode)
