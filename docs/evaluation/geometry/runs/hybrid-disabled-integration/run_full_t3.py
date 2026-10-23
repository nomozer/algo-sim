"""One authoritative Full T3 attempt on a clean detached worktree; writes an execution receipt.

    python run_full_t3.py <clean-worktree> <expected-commit> <NEW-log-dir>

Same receipt fields as Session 3 (`hybrid-contract-v2/verification/full-t3/execution.json`), plus the raw
stdout/stderr files themselves so the detailed counts stay recoverable. Single attempt, no retry.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ENV = {'ALLOW_LIVE_AI': '0', 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8',
       'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
TIMEOUT = 2400


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, check=True).stdout.strip()


def main(root, expected, out):
    out.mkdir(parents=True, exist_ok=False)
    head = git(root, 'rev-parse', 'HEAD')
    assert head == expected, f'HEAD {head} != {expected}'
    dirty_before = git(root, 'status', '--porcelain')
    assert not dirty_before, 'worktree not clean'
    env = {k: v for k, v in os.environ.items() if k not in ('GEOMETRY_COMPILER_MODE', 'HYBRID_ROUTE_D_PREVIEW')}
    env.update(ENV)
    started = datetime.now(timezone.utc)
    t0 = time.monotonic()
    timed_out = False
    with (out / 'stdout.log').open('wb') as so, (out / 'stderr.log').open('wb') as se:
        try:
            code = subprocess.run(['node', 'frontend/scripts/full-gate.mjs'], cwd=root, env=env, stdout=so,
                                  stderr=se, timeout=TIMEOUT).returncode
        except subprocess.TimeoutExpired:
            code, timed_out = None, True
    elapsed = round(time.monotonic() - t0, 2)
    streams = {}
    for name in ('stdout', 'stderr'):
        data = (out / f'{name}.log').read_bytes()
        streams[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    receipt = {'command': ['node', 'frontend/scripts/full-gate.mjs'], 'cwd': str(root), 'source_commit': head,
               'dirty_before': dirty_before, 'started_utc': started.isoformat(), 'timeout_seconds': TIMEOUT,
               'attempt_limit': 1, 'environment_overrides': ENV, 'exit_code': code, 'timed_out': timed_out,
               'elapsed_seconds': elapsed, 'finished_utc': datetime.now(timezone.utc).isoformat(),
               'dirty_after': git(root, 'status', '--porcelain'), 'streams': streams}
    with (out / 'execution.json').open('x', encoding='utf-8') as f:
        json.dump(receipt, f, indent=2)
        f.write('\n')
    print(json.dumps({k: receipt[k] for k in ('source_commit', 'exit_code', 'timed_out', 'elapsed_seconds',
                                              'dirty_after')}))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve())
