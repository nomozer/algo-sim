"""Run one bounded offline check; record exact command/exit/output hashes. Fresh output only."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def main(out, cwd, command, timeout=2400):
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    env.update(ALLOW_LIVE_AI='0', PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               ALGO_SIM_PYTHON=sys.executable)
    started = datetime.now(timezone.utc).isoformat(); start = time.monotonic()
    timed_out = False
    try:
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        timed_out = True
        result = subprocess.CompletedProcess(command, 124, error.stdout or b'', error.stderr or b'')
    streams = {}
    for name in ('stdout', 'stderr'):
        data = getattr(result, name)
        # Raw receipt stays local if a Python traceback is present; never add forbidden bytes to Git.
        if result.returncode != 0 or b'Traceback (most recent call last):' in data:
            local = cwd / '.superpowers/session5-raw' / out.name
            local.mkdir(parents=True, exist_ok=True); (local/(name+'.log')).write_bytes(data)
            safe = b'FAILURE_OR_RAW_TRACEBACK_WITHHELD_LOCAL_ONLY\n'
        else:
            safe = data
        path = out/(name+'.log'); path.write_bytes(safe)
        streams[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                         'stored_bytes': len(safe), 'stored_sha256': hashlib.sha256(safe).hexdigest()}
    text = result.stdout.decode('utf-8', errors='replace')
    summaries = re.findall(r'^.*(?:\d+ passed|Tests\s+\d|Test Files\s+\d|FULL_PRODUCT_GATE_|Candidate|candidate|MATCH|FAIL).*$', text, re.M)
    receipt = {'command': command, 'cwd': str(cwd), 'source_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=cwd,text=True).strip(),
               'started_utc': started, 'elapsed_seconds': round(time.monotonic()-start, 3),
               'exit_code': result.returncode, 'timeout_seconds': timeout, 'timed_out': timed_out,
               'environment': {k: env[k] for k in ('ALLOW_LIVE_AI','PYTHONUTF8','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','ALGO_SIM_PYTHON')},
               'streams': streams, 'summary': summaries}
    (out/'execution.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'exit_code': result.returncode,'summary':summaries},ensure_ascii=False))
    return result.returncode


if __name__ == '__main__':
    sys.exit(main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3:]))
