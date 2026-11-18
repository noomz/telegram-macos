from pathlib import Path
import csv
import re
import subprocess
import sys
import time

root = Path(sys.argv[1]).expanduser().resolve()
probe = root / 'corner-probe'
fixed = root / 'RadiusHarness.app/Contents/MacOS/RadiusHarness'
baseline = root / 'baseline/RadiusHarness.app/Contents/MacOS/RadiusHarness'
rows = []

def run(name, executable, args, expected, delay=1.5):
    with (root / 'runtime-harness.log').open('a') as log:
        process = subprocess.Popen([str(executable), *args], stdout=log, stderr=log)
        try:
            time.sleep(delay)
            if process.poll() is not None:
                raise RuntimeError(f'{name}: harness exited {process.returncode}')
            result = subprocess.run([str(probe), 'RadiusHarness'], capture_output=True, text=True, check=True)
            values = [float(value) for value in re.findall(r'radius=([0-9.]+)', result.stdout)]
            passed = bool(values) and (expected is None or all(value == expected for value in values))
            rows.append([name, ' '.join(args), expected, result.stdout.strip(), 'PASS' if passed else 'FAIL'])
            print('\t'.join(map(str, rows[-1])), flush=True)
        finally:
            process.terminate()
            process.wait(timeout=10)
    return values

if '--domain-only' in sys.argv:
    domain = 'space.noomz.CornerRadiusHarness'
    key = 'NSConvolutionOverride1'
    existing = subprocess.run(['defaults', 'read', domain, key], capture_output=True)
    if existing.returncode == 0:
        raise SystemExit('Refusing to overwrite an existing diagnostic override')
    try:
        for dark in [False, True]:
            appearance = ['-DarkTheme', 'YES' if dark else 'NO']
            theme = 'dark' if dark else 'light'
            for value, expected in [('4', 4), ('-5', 28), ('0', 28)]:
                subprocess.run(['defaults', 'write', domain, key, '-float', value], check=True)
                run(f'{theme}-domain-{value}', fixed, appearance, expected)
            subprocess.run(['defaults', 'write', domain, key, '-float', '4'], check=True)
            run(f'{theme}-argument-over-domain', fixed, [*appearance, '-NSConvolutionOverride1', '1'], 1)
    finally:
        subprocess.run(['defaults', 'delete', domain, key], check=True)
    raise SystemExit(0 if all(row[-1] == 'PASS' for row in rows) else 1)
if '--compact-only' not in sys.argv:
    run('baseline-global-1', baseline, [], 28)
if '--baseline-only' in sys.argv:
    run('baseline-compact-global-1', baseline, ['-CornerMode', 'compact'], 0)
    run('baseline-compact-zero', baseline, ['-CornerMode', 'compact', '-NSConvolutionOverride1', '0'], 0)
    raise SystemExit(0 if all(row[-1] == 'PASS' for row in rows) else 1)
for dark in [False, True]:
    theme = 'dark' if dark else 'light'
    appearance = ['-DarkTheme', 'YES' if dark else 'NO']
    if '--compact-only' not in sys.argv:
        run(f'{theme}-global-1', fixed, appearance, 1)
        for value, expected in [('0', 28), ('1', 1), ('4', 4), ('40', 40), ('nan', 28), ('inf', 28)]:
            run(f'{theme}-standard-{value}', fixed, [*appearance, '-NSConvolutionOverride1', value], expected)
    for value in ['0', '1', '4']:
        args = [*appearance, '-CornerMode', 'compact', '-NSConvolutionOverride1', value]
        previous = run(f'{theme}-baseline-compact-{value}', baseline, args, None)
        if len(set(previous)) != 1:
            raise RuntimeError('Baseline has inconsistent compact window radii')
        run(f'{theme}-compact-preserved-{value}', fixed, args, previous[0])
    if '--compact-only' not in sys.argv:
        run(f'{theme}-fullscreen-return', fixed, [*appearance, '-FullScreenCycle', 'YES', '-NSConvolutionOverride1', '1'], 1, 9)
with (root / 'runtime-results.tsv').open('w') as stream:
    writer = csv.writer(stream, delimiter='\t')
    writer.writerow(['case', 'arguments', 'expected', 'probe', 'result'])
    writer.writerows(rows)
if any(row[-1] != 'PASS' for row in rows):
    raise SystemExit(1)
print(f'PASS: {len(rows)} WindowServer measurements')
