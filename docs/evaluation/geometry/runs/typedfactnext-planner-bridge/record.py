"""Run one bounded offline command and keep its raw stdout/stderr bytes plus a receipt (commit, dirty state, env, exit,
hashes). Same design as `geometric-visual-correctness-framing/record-command.py`: single-thread math libraries, a short
pytest temp root (Windows MAX_PATH), no overwrite, and no authoritative full gate on a dirty checkout."""
import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--cwd", required=True)
p.add_argument("--out", required=True)
p.add_argument("--timeout", type=int, default=2400)
p.add_argument("command", nargs=argparse.REMAINDER)
a = p.parse_args()
cmd = a.command[1:] if a.command[0] == "--" else a.command
out = Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=True)
assert not (out / "execution.json").exists(), "use a new attempt directory"
temp = Path(r"D:\Documents\projects\algo-sim\.superpowers") / f"pt-{os.getpid()}"
temp.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, ALLOW_LIVE_AI="0", PYTHONUTF8="1", PYTHONIOENCODING="utf-8", OMP_NUM_THREADS="1",
           OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1", PYTEST_DEBUG_TEMPROOT=str(temp),
           ALGO_SIM_PYTHON=r"D:\Documents\projects\algo-sim\backend\.venv\Scripts\python.exe")
git = lambda *args: subprocess.check_output(["git", "-C", a.cwd, *args], text=True, env=env).strip()  # noqa: E731
record = dict(command=cmd, cwd=str(Path(a.cwd).resolve()), source_commit=git("rev-parse", "HEAD"),
              dirty_before=git("status", "--porcelain"), started_utc=datetime.now(timezone.utc).isoformat(),
              timeout_seconds=a.timeout, attempt_limit=1,
              environment_overrides={k: env[k] for k in ("ALLOW_LIVE_AI", "PYTHONUTF8", "PYTHONIOENCODING", "OMP_NUM_THREADS",
                                                         "PYTEST_DEBUG_TEMPROOT")})
if any("full-gate.mjs" in part for part in cmd) and record["dirty_before"]:
    raise SystemExit("Refusing authoritative T3 on a dirty checkout")
(out / "invocation.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
start = time.monotonic()
with (out / "stdout.log").open("wb") as so, (out / "stderr.log").open("wb") as se:
    proc = subprocess.Popen(cmd, cwd=a.cwd, env=env, stdout=so, stderr=se)
    try:
        code, timed_out = proc.wait(timeout=a.timeout), False
    except subprocess.TimeoutExpired:
        proc.kill()
        code, timed_out = proc.wait(), True
record.update(exit_code=code, timed_out=timed_out, elapsed_seconds=round(time.monotonic() - start, 2),
              finished_utc=datetime.now(timezone.utc).isoformat(), dirty_after=git("status", "--porcelain"))
record["streams"] = {n: dict(bytes=(out / f"{n}.log").stat().st_size,
                             sha256=hashlib.sha256((out / f"{n}.log").read_bytes()).hexdigest()) for n in ("stdout", "stderr")}
(out / "execution.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
print(json.dumps({k: record[k] for k in ("source_commit", "exit_code", "elapsed_seconds", "timed_out")}, indent=2))
raise SystemExit(code if not timed_out else 124)
