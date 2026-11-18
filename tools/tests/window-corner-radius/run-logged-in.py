import copy
import json
import pathlib
import plistlib
import re
import subprocess
import sys
import time

app = pathlib.Path(sys.argv[1])
probe = pathlib.Path(sys.argv[2])
control = pathlib.Path(sys.argv[3])
domain = 'space.noomz.Telegram'
override_key = 'NSConvolutionOverride1'
frame_key = 'window_saver_TGUIKit.Window'
executable = str(app / 'Contents/MacOS/Telegram')
backup_path = pathlib.Path.home() / 'Downloads/corner-acceptance-backup.plist'


def preferences(name):
    result = subprocess.run(['defaults', 'export', name, '-'], capture_output=True)
    if result.returncode:
        raise RuntimeError(f'Cannot export preferences: {name}')
    return plistlib.loads(result.stdout)


def write_value(name, key, value):
    if value is None:
        if key in preferences(name):
            subprocess.run(['defaults', 'delete', name, key], check=True)
    elif isinstance(value, bytes):
        subprocess.run(['defaults', 'write', name, key, '-data', value.hex()], check=True)
    elif isinstance(value, (float, int)):
        subprocess.run(['defaults', 'write', name, key, '-float', str(value)], check=True)
    else:
        raise RuntimeError(f'Unsupported preference type: {type(value)}')


def processes():
    result = subprocess.run(['pgrep', '-f', '^' + re.escape(executable) + '( |$)'], capture_output=True, text=True)
    if result.returncode not in (0, 1):
        raise RuntimeError('Cannot inspect application processes')
    return [int(pid) for pid in result.stdout.split()]


def stop():
    for pid in processes():
        subprocess.run(['kill', '-TERM', str(pid)], check=True)
    for _ in range(100):
        if not processes():
            return
        time.sleep(0.1)
    raise RuntimeError('App did not terminate; refusing to alter preferences')


def start(args=()):
    subprocess.run(['open', str(app), '--args', *args], check=True)
    time.sleep(6)
    if not processes():
        raise RuntimeError('App did not remain running')


original_app = preferences(domain)
original_global = preferences('-g')
original_frame = original_app.get(frame_key)
if not isinstance(original_frame, bytes):
    raise RuntimeError('No saved window dimensions; leave the logged-in window open first')
archive = plistlib.loads(original_frame)
root = archive['$objects'][archive['$top']['root'].data]
rect_index = root['rect'].data
print('Original saved frame:', archive['$objects'][rect_index], flush=True)
if root['isFullScreen']:
    raise RuntimeError('Exit full screen before running this test')
backup = {'app': {key: original_app[key] for key in (override_key, frame_key) if key in original_app},
          'global': {override_key: original_global[override_key]} if override_key in original_global else {}}
if backup_path.exists():
    raise RuntimeError(f'Existing recovery backup must be handled first: {backup_path}')
backup_path.write_bytes(plistlib.dumps(backup))
backup_path.chmod(0o600)
failures = []

transitions_only = '--transitions-only' in sys.argv
cases = [
    ('global-1-transitions', 1, None, [], 1),
    ('no-override-compact', None, None, [], 28),
] if transitions_only else [
        ('global-1-standard', 1, None, [], 1),
        ('no-override-standard', None, None, [], 28),
        ('app-0-standard', None, 0, [], 28),
        ('app-negative-standard', None, -5, [], 28),
        ('app-4-standard', None, 4, [], 4),
        ('argument-1-standard', None, None, ['-NSConvolutionOverride1', '1'], 1),
]

try:
    for label, global_value, app_value, args, expected in cases:
        stop()
        write_value('-g', override_key, global_value)
        write_value(domain, override_key, app_value)
        frame = copy.deepcopy(archive)
        frame['$objects'][rect_index] = '{{200, 100}, {900, 700}}'
        write_value(domain, frame_key, plistlib.dumps(frame, fmt=plistlib.FMT_BINARY))
        start(args)
        subprocess.run([str(control), 'size', '900', '700'], check=True)
        time.sleep(1)
        result = subprocess.run([str(probe), app.stem], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().splitlines()
        measurements = [re.fullmatch(r'wid=\d+ size=(\d+)x(\d+) radius=([\d.]+)', line) for line in lines]
        standard_mode = bool(measurements) and all(m and int(m[1]) >= 650 for m in measurements)
        if not standard_mode:
            print(json.dumps({'case': label, 'probe': lines, 'blocked': 'Standard-width window not reached'}), flush=True)
            raise RuntimeError('Confirm Telegram login and widen the main window before retrying')
        passed = all(float(m[3]) == expected for m in measurements)
        print(json.dumps({'case': label, 'expected': expected, 'probe': lines, 'passed': passed}), flush=True)
        if not passed:
            failures.append(label)
        if transitions_only:
            subprocess.run([str(control), 'size', '480', '700'], check=True)
            time.sleep(1)
            compact = subprocess.check_output([str(probe), app.stem], text=True).strip()
            compact_match = re.fullmatch(r'wid=\d+ size=(\d+)x(\d+) radius=([\d.]+)', compact)
            compact_expected = 1 if global_value == 1 else 16
            compact_passed = bool(compact_match) and int(compact_match[1]) < 650 and float(compact_match[3]) == compact_expected
            print(json.dumps({'case': label + '-compact-preserved', 'expected': compact_expected, 'probe': compact, 'passed': compact_passed}), flush=True)
            if not compact_passed:
                failures.append(label + '-compact-preserved')
            subprocess.run([str(control), 'size', '900', '700'], check=True)
            time.sleep(1)
            if global_value == 1:
                subprocess.run([str(control), 'fullscreen', 'true'], check=True)
                time.sleep(4)
                status = subprocess.check_output([str(control), 'status'], text=True).strip()
                print('FULLSCREEN ENTERED: ' + status, flush=True)
                subprocess.run([str(control), 'fullscreen', 'false'], check=True)
                time.sleep(4)
                status_after = subprocess.check_output([str(control), 'status'], text=True).strip()
                returned = subprocess.check_output([str(probe), app.stem], text=True).strip()
                returned_match = re.fullmatch(r'wid=\d+ size=(\d+)x(\d+) radius=([\d.]+)', returned)
                fullscreen_passed = 'fullscreen=1' in status and 'fullscreen=0' in status_after and bool(returned_match) and int(returned_match[1]) >= 650 and float(returned_match[3]) == 1
                print(json.dumps({'case': 'fullscreen-return-global-1', 'probe': returned, 'passed': fullscreen_passed}), flush=True)
                if not fullscreen_passed:
                    failures.append('fullscreen-return-global-1')
finally:
    stop()
    write_value('-g', override_key, original_global.get(override_key))
    write_value(domain, override_key, original_app.get(override_key))
    write_value(domain, frame_key, original_frame)
    start()
    if preferences('-g').get(override_key) != original_global.get(override_key):
        raise RuntimeError('Global preference restoration failed')
    if preferences(domain).get(override_key) != original_app.get(override_key):
        raise RuntimeError('App preference restoration failed')
    print('RESTORED: original global/app overrides; original frame preference reapplied; app relaunched', flush=True)
    backup_path.unlink()

if failures:
    raise SystemExit('FAIL: ' + ', '.join(failures))
print('PASS: logged-in ' + ('transition' if transitions_only else 'standard-mode') + ' cases in the current app theme', flush=True)
