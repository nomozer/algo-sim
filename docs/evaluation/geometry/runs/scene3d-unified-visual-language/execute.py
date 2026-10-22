"""Bounded local command execution with raw-byte logs and exact-source receipt."""
import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--cwd', default='frontend')
parser.add_argument('--timeout', type=int, default=1200)
parser.add_argument('command', nargs=argparse.REMAINDER)
args = parser.parse_args()
command = args.command[1:] if args.command[0] == '--' else args.command
repo = args.repo.resolve()
out = args.out.resolve()
out.mkdir(parents=True, exist_ok=True)
assert not (out / 'execution.json').exists(), 'Never overwrite an execution receipt'
env = os.environ.copy()
overrides = dict(ALLOW_LIVE_AI='0', PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
                 ALGO_SIM_PYTHON=str(repo.parents[2] / 'backend/.venv/Scripts/python.exe'),
                 PYTEST_DEBUG_TEMPROOT=str(repo / '.superpowers/pytest-temp'))
env.update(overrides)
Path(overrides['PYTEST_DEBUG_TEMPROOT']).mkdir(parents=True, exist_ok=True)


def git(*parts):
    return subprocess.check_output(['git', *parts], cwd=repo, stderr=subprocess.DEVNULL).decode('utf-8').strip()


receipt = dict(command=command, cwd=str(repo / args.cwd), source_commit=git('rev-parse', 'HEAD'),
               dirty_before=git('status', '--porcelain'), started_utc=datetime.now(timezone.utc).isoformat(),
               timeout_seconds=args.timeout, attempt_limit=1, environment_overrides=overrides)
start = time.monotonic()
with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
    process = subprocess.Popen(command, cwd=repo / args.cwd, env=env, stdout=stdout, stderr=stderr)
    try:
        code = process.wait(timeout=args.timeout)
        receipt['timed_out'] = False
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, check=False)
        code = process.wait()
        receipt['timed_out'] = True
receipt.update(exit_code=code, elapsed_seconds=round(time.monotonic() - start, 3),
               finished_utc=datetime.now(timezone.utc).isoformat(), dirty_after=git('status', '--porcelain'))
receipt['streams'] = {name: dict(bytes=(out / (name + '.log')).stat().st_size,
    sha256=hashlib.sha256((out / (name + '.log')).read_bytes()).hexdigest()) for name in ['stdout', 'stderr']}
(out / 'execution.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: receipt[k] for k in ['source_commit', 'exit_code', 'elapsed_seconds', 'timed_out', 'streams']}, indent=2))
raise SystemExit(code)
