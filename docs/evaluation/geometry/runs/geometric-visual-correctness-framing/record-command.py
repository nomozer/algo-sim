"""Run one bounded offline verification and preserve the exact process streams."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from datetime import datetime, timezone

p = argparse.ArgumentParser()
p.add_argument('--cwd', required=True)
p.add_argument('--out', required=True)
p.add_argument('--timeout', type=int, default=2400)
p.add_argument('command', nargs=argparse.REMAINDER)
a = p.parse_args()
cmd = a.command[1:] if a.command[0] == '--' else a.command
out = Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=True)
assert not (out / 'execution.json').exists(), 'use a new attempt directory'
env = dict(os.environ, ALLOW_LIVE_AI='0', PYTHONUTF8='1', PYTHONIOENCODING='utf-8', ALGO_SIM_PYTHON=r'D:\Documents\projects\algo-sim\backend\.venv\Scripts\python.exe')
root = Path(a.cwd).resolve()
if root.name == 'backend':
    root = root.parent
pytest_temp = Path(r'D:\Documents\projects\algo-sim\.superpowers') / f'pt-{os.getpid()}'
pytest_temp.mkdir(parents=True, exist_ok=True)
env['PYTEST_DEBUG_TEMPROOT'] = str(pytest_temp)
config_count = int(env.get('GIT_CONFIG_COUNT', '0'))
env.update({
    f'GIT_CONFIG_KEY_{config_count}': 'safe.directory',
    f'GIT_CONFIG_VALUE_{config_count}': root.as_posix(),
    f'GIT_CONFIG_KEY_{config_count+1}': 'core.longpaths',
    f'GIT_CONFIG_VALUE_{config_count+1}': 'true',
    'GIT_CONFIG_COUNT': str(config_count + 2),
})
git = lambda *args: subprocess.check_output(['git', '-C', a.cwd, *args], text=True, env=env).strip()
record = dict(command=cmd, cwd=str(Path(a.cwd).resolve()), source_commit=git('rev-parse','HEAD'), dirty_before=git('status','--porcelain'), started_utc=datetime.now(timezone.utc).isoformat(), timeout_seconds=a.timeout, attempt_limit=1, environment_overrides={k:env[k] for k in ['ALLOW_LIVE_AI','PYTHONUTF8','PYTHONIOENCODING','ALGO_SIM_PYTHON','PYTEST_DEBUG_TEMPROOT']})
if any('full-gate.mjs' in part for part in cmd) and record['dirty_before']:
    raise SystemExit('Refusing authoritative T3 on a dirty checkout')
(out / 'invocation.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
start = time.monotonic()
with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
    process = subprocess.Popen(cmd, cwd=a.cwd, env=env, stdout=stdout, stderr=stderr)
    try:
        code = process.wait(timeout=a.timeout)
        timed_out = False
    except subprocess.TimeoutExpired:
        process.kill()
        code = process.wait()
        timed_out = True
record.update(exit_code=code, timed_out=timed_out, elapsed_seconds=round(time.monotonic()-start,2), finished_utc=datetime.now(timezone.utc).isoformat(), dirty_after=git('status','--porcelain'))
record['streams'] = {name:dict(bytes=(out/f'{name}.log').stat().st_size, sha256=hashlib.sha256((out/f'{name}.log').read_bytes()).hexdigest()) for name in ['stdout','stderr']}
(out / 'execution.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
raise SystemExit(code if not timed_out else 124)
