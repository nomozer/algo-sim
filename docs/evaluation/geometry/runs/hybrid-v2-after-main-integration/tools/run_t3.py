"""Record one full-gate invocation on a clean detached checkout, with UTF-8 artifacts."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def publish_receipt(receipt, output, exit_code, console=None):
    """Persist first; console transport must never replace the real result code."""
    (output / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        print(json.dumps(receipt, ensure_ascii=True), file=console or sys.stdout, flush=True)
    except (UnicodeError, OSError):
        pass
    return exit_code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    repo, output = args.repo.resolve(), args.out.resolve()
    env = {**os.environ, "ALLOW_LIVE_AI": "0", "ALGO_SIM_PYTHON": str(args.python.resolve()),
           "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "GIT_CONFIG_COUNT": "1",
           "GIT_CONFIG_KEY_0": "safe.directory", "GIT_CONFIG_VALUE_0": repo.as_posix()}
    env.pop("HYBRID_V2_LOCAL", None)
    env["PYTEST_ADDOPTS"] = f"-vv --basetemp={(output / 'pytest-temp').as_posix()}"
    def git(*command):
        return subprocess.check_output(["git", "-C", str(repo), *command], env=env, encoding="utf-8").strip()
    before = git("status", "--porcelain=v1", "--untracked-files=all")
    if before:
        raise RuntimeError("T3_SOURCE_NOT_CLEAN")
    if subprocess.run(["git", "-C", str(repo), "symbolic-ref", "-q", "HEAD"], env=env, capture_output=True).returncode == 0:
        raise RuntimeError("T3_SOURCE_NOT_DETACHED")
    if output == repo or repo in output.parents:
        raise RuntimeError("T3_OUTPUT_MUST_BE_OUTSIDE_CHECKOUT")
    output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    head, tree = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}")
    freeze_path = repo / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"
    frozen = json.loads(freeze_path.read_text(encoding="utf-8"))
    freeze_hash = hashlib.sha256(freeze_path.read_bytes()).hexdigest()
    with (output / "stdout.log").open("wb") as stdout, (output / "stderr.log").open("wb") as stderr:
        code = subprocess.run(["node", "frontend/scripts/full-gate.mjs"], cwd=repo, env=env,
                              stdout=stdout, stderr=stderr).returncode
    verify = subprocess.run([str(args.python.resolve()), "backend/scripts/freeze_evaluation_candidate.py", "--verify"],
                            cwd=repo, env=env, capture_output=True, encoding="utf-8")
    after = git("status", "--porcelain=v1", "--untracked-files=all")
    text = (output / "stdout.log").read_text(encoding="utf-8", errors="replace")
    passed = code == 0 and "FULL_PRODUCT_GATE_PASS" in text.splitlines()
    receipt = {"candidate": head, "git_tree": tree, "product_commit": frozen["product_commit_sha"],
               "detached": True, "source_tree_before": before, "source_tree_after": after,
               "head_after": git("rev-parse", "HEAD"), "git_tree_after": git("rev-parse", "HEAD^{tree}"),
               "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
               "exit_code": code, "verdict": "FULL_PRODUCT_GATE_PASS" if passed else "FULL_PRODUCT_GATE_FAIL",
               "summaries": [line for line in text.splitlines() if re.search(r"\d+ passed|Test Files|Tests\s+|^FULL_PRODUCT_GATE|^FAILED ", line)],
               "post_freeze": {"exit_code": verify.returncode, "stdout": verify.stdout.strip(), "stderr": verify.stderr.strip()},
               "freeze_sha256_before": freeze_hash, "freeze_sha256_after": hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
               "live_provider_calls": 0, "allow_live_ai": "0", "hybrid_v2_local": "UNSET",
               "streams": {name: {"sha256": hashlib.sha256((output / name).read_bytes()).hexdigest(),
                                  "bytes": (output / name).stat().st_size} for name in ("stdout.log", "stderr.log")}}
    valid = (not after and verify.returncode == 0 and receipt["head_after"] == head
             and receipt["git_tree_after"] == tree and receipt["freeze_sha256_after"] == freeze_hash)
    return publish_receipt(receipt, output, code or (0 if passed and valid else 1))


if __name__ == "__main__":
    raise SystemExit(main())
