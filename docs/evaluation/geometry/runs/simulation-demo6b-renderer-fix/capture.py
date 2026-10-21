"""Capture one preregistered local command without text-mode stream conversion."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def capture(spec_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    cwd = Path(spec["cwd"])
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd, text=True).strip()
    assert commit == spec["source_commit"], (commit, spec["source_commit"])
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], cwd=cwd)
    assert not dirty.strip(), "Execution snapshot must be clean"
    env = {**os.environ, **spec["environment_overrides"]}
    assert env["ALLOW_LIVE_AI"] == "0"
    directory = Path(spec["output_directory"])
    directory.mkdir(parents=True, exist_ok=True)
    stdout_path, stderr_path = directory / "stdout.log", directory / "stderr.log"
    started = {**spec, "started_utc": timestamp(), "command_line": subprocess.list2cmdline(spec["argv"]),
               "environment": {k: env.get(k) for k in ["ALLOW_LIVE_AI", "PYTHONUTF8", "PYTHONIOENCODING",
                 "ALGO_SIM_PYTHON", "PLAYWRIGHT_BROWSERS_PATH", "NODE_OPTIONS", "PYTEST_ADDOPTS", "CI", "NO_COLOR"]}}
    with (directory / "started.json").open("x", encoding="utf-8") as stream:
        json.dump(started, stream, indent=2)
    print("CAPTURE_STARTED", spec["run_kind"], started["started_utc"], flush=True)
    timed_out = False
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        try:
            result = subprocess.run(spec["argv"], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                    stdout=stdout, stderr=stderr, timeout=spec["timeout_seconds"])
            returncode = result.returncode
        except subprocess.TimeoutExpired:
            returncode, timed_out = None, True
    execution = {**started, "finished_utc": timestamp(), "exit_code": returncode, "timed_out": timed_out,
                 "hash_policy": "RAW_BYTES_SHA256", "streams": {}}
    for name, path in [("stdout", stdout_path), ("stderr", stderr_path)]:
        raw = path.read_bytes()
        execution["streams"][name] = {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    execution["snapshot_dirty_after"] = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=cwd, text=True).splitlines()
    with (directory / "execution.json").open("x", encoding="utf-8") as stream:
        json.dump(execution, stream, indent=2)
        stream.write("\n")
    print("CAPTURE_FINISHED", spec["run_kind"], returncode, execution["finished_utc"], flush=True)
    return 1 if timed_out else returncode


if __name__ == "__main__":
    raise SystemExit(capture(sys.argv[1]))
