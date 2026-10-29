# -*- coding: utf-8 -*-
"""Reviewed W3-F1/W3-F2 Full T3 runner, unchanged except its schema label (unified solid-scope)."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

repo = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
python = Path(sys.executable)


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


head = git("rev-parse", "HEAD")
before = git("status", "--porcelain=v1", "--untracked-files=all")
assert not before, "source must be clean"
assert subprocess.run(["git", "-C", str(repo), "symbolic-ref", "-q", "HEAD"], capture_output=True).returncode != 0
assert repo != out and repo not in out.parents
out.mkdir(parents=True, exist_ok=False)
(repo / ".superpowers").mkdir(parents=True, exist_ok=True)

env = {
    **os.environ,
    "ALLOW_LIVE_AI": "0",
    "ALGO_SIM_PYTHON": str(python),
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTEST_ADDOPTS": f"--tb=no --disable-warnings -p no:cacheprovider --basetemp={(repo / '.superpowers/t3-temp').as_posix()}",
}
env.pop("HYBRID_V2_LOCAL", None)

freeze = repo / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"
frozen = json.loads(freeze.read_text(encoding="utf-8"))
freeze_before = hashlib.sha256(freeze.read_bytes()).hexdigest()
started = datetime.now(timezone.utc).isoformat()

with (out / "full-t3.log").open("wb") as log:
    proc = subprocess.Popen(
        ["node", "frontend/scripts/full-gate.mjs"],
        cwd=repo,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        log.write(line)
        text = line.decode("utf-8", errors="replace")
        if re.search(r"passed|failed|FULL_PRODUCT_GATE|✔|✘|Test Files|Tests\s+", text):
            print(text.rstrip(), flush=True)
    code = proc.wait()

verify = subprocess.run(
    [str(python), "backend/scripts/freeze_evaluation_candidate.py", "--verify"],
    cwd=repo,
    env=env,
    capture_output=True,
    text=True,
    encoding="utf-8",
)
after = git("status", "--porcelain=v1", "--untracked-files=all")
freeze_after = hashlib.sha256(freeze.read_bytes()).hexdigest()
log_bytes = (out / "full-t3.log").read_bytes()
text = log_bytes.decode("utf-8", errors="replace")
integrity = not after and git("rev-parse", "HEAD") == head and verify.returncode == 0 and freeze_before == freeze_after

receipt = dict(
    schema="w3-f2-unified-solid-scope-full-t3/1",
    candidate=head,
    product_commit=frozen["product_commit_sha"],
    detached=True,
    source_tree_before=before,
    source_tree_after=after,
    started_utc=started,
    finished_utc=datetime.now(timezone.utc).isoformat(),
    exit_code=code,
    verdict="FULL_PRODUCT_GATE_PASS" if code == 0 and integrity else "FULL_PRODUCT_GATE_FAIL",
    source_integrity="MATCH" if integrity else "MISMATCH",
    measured_system=frozen["measured_system"],
    post_freeze=dict(exit_code=verify.returncode, stdout=verify.stdout.strip()),
    freeze_sha256_before=freeze_before,
    freeze_sha256_after=freeze_after,
    log=dict(path="full-t3.log", sha256=hashlib.sha256(log_bytes).hexdigest(), bytes=len(log_bytes)),
    summaries=[
        line
        for line in text.splitlines()
        if re.search(r"\d+ passed|Test Files|Tests\s+|^FULL_PRODUCT_GATE|^FAILED ", line)
    ],
    live_provider_calls=0,
    pytest_policy="all tests, --tb=no, no cache writes, fresh candidate-local ignored temp",
)
with (out / "receipt.json").open("x", encoding="utf-8") as f:
    f.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(receipt, ensure_ascii=True), flush=True)
sys.exit(code or (0 if integrity else 1))
