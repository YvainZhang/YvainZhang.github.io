"""Portable CPU regression; outputs only in a fresh temporary directory."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'Audio/Labs/lab03-fixed-point-dsp-aec-filter'


def main():
    compiler = shlex.split(os.environ.get('CC', 'cc'))
    flags = ['-std=c99', '-Wall', '-Wextra', '-Werror', '-fsanitize=undefined',
             '-fno-sanitize-recover=undefined']
    with tempfile.TemporaryDirectory(prefix='audio-lms-') as directory:
        work = Path(directory)
        for name, source, extra in [('unit', 'test_fixed_point.c', []),
                                    ('demo', 'fixed_point_lms.c', []),
                                    ('fail', 'fixed_point_lms.c', ['-DTARGET_ERLE_DB=100.0'])]:
            subprocess.run(compiler + flags + extra + [str(LAB/source), '-lm', '-o', str(work/name)], check=True)
        subprocess.run([str(work/'unit')], cwd=work, check=True)
        result = subprocess.run([str(work/'demo')], cwd=work, check=True, text=True, capture_output=True)
        first = (work/'erle_data.csv').read_bytes()
        subprocess.run([str(work/'demo')], cwd=work, check=True, capture_output=True)
        if first != (work/'erle_data.csv').read_bytes():
            raise AssertionError('fixed PRNG run is not reproducible')
        failed = subprocess.run([str(work/'fail')], cwd=work, capture_output=True, text=True)
        if failed.returncode == 0 or 'FAIL' not in failed.stdout or 'runtime error:' in failed.stderr:
            raise AssertionError('quality threshold must fail explicitly, not through UB')
        blocked = work/'blocked'
        blocked.mkdir()
        (blocked/'erle_data.csv').mkdir()  # Deterministic fopen failure, including root.
        if subprocess.run([str(work/'demo')], cwd=blocked, capture_output=True).returncode == 0:
            raise AssertionError('output failure incorrectly reported success')
        print(next(line for line in result.stdout.splitlines() if line.startswith('Final ERLE:')))
        print('PASS: UBSan, boundaries, silence, deterministic convergence, failed threshold and output failure')


if __name__ == '__main__':
    main()
