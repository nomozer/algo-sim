import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

workspace = Path('D:/Documents/projects/algo-sim')
root = Path(sys.argv[1]).resolve()
out = workspace / '.superpowers' / (sys.argv[2] if len(sys.argv) > 2 else 'scene3d-codex-t3')
out.mkdir(exist_ok=False)
def git(*args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()
assert not git('status', '--porcelain'), 'candidate must be clean'
assert subprocess.run(['git', 'symbolic-ref', '-q', 'HEAD'], cwd=root, capture_output=True).returncode != 0
head = git('rev-parse', 'HEAD')
python = workspace / 'backend/.venv/Scripts/python.exe'
env = {**os.environ, 'ALLOW_LIVE_AI': '0', 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8',
       'ALGO_SIM_PYTHON': str(python),
       'PYTEST_ADDOPTS': '-vv --basetemp=' + (workspace / '.superpowers/pt-codex-scene3d-final').as_posix()}
start = datetime.now(timezone.utc).isoformat()
clock = time.monotonic()
with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
    process = subprocess.Popen(['node', 'frontend/scripts/full-gate.mjs'], cwd=root, env=env, stdout=stdout, stderr=stderr)
    (out / 'running.json').write_text(json.dumps({'pid': process.pid, 'head': head, 'started_utc': start}))
    code = process.wait()
verify = subprocess.run([str(python), 'backend/scripts/freeze_evaluation_candidate.py', '--verify'], cwd=root, env=env, capture_output=True, text=True, encoding='utf-8')
stdout = (out / 'stdout.log').read_text(encoding='utf-8', errors='replace')
receipt = {'candidate': head, 'detached': True, 'source_tree_before': '', 'source_tree_after': git('status', '--porcelain'),
           'started_utc': start, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': round(time.monotonic() - clock, 3),
           'exit_code': code, 'verdict': 'FULL_PRODUCT_GATE_PASS' if code == 0 else 'FULL_PRODUCT_GATE_FAIL',
           'summaries': [line for line in stdout.splitlines() if re.search(r'\d+ passed|Test Files|Tests\s+|FULL_PRODUCT_GATE|^FAILED ', line)],
           'post_freeze': {'exit_code': verify.returncode, 'stdout': verify.stdout.strip()},
           'provider_calls': 0, 'execution_context': 'Codex clean detached machine verification; not independent review',
           'streams': {name: {'bytes': (out / name).stat().st_size, 'sha256': hashlib.sha256((out / name).read_bytes()).hexdigest()} for name in ['stdout.log', 'stderr.log']}}
(out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt, ensure_ascii=False, indent=2))
sys.exit(code or verify.returncode or bool(receipt['source_tree_after']))
