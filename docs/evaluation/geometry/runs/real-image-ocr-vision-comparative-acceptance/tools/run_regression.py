"""Run the canonical offline gates; retain only sanitized metadata in the run."""
from __future__ import annotations

import argparse
import hashlib
import fnmatch
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
BASELINE = "6bb22fa3bb183ad28cdf1395c99e5eb375fac97c"


def now():
    return datetime.now(timezone.utc).isoformat()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()


def snapshot():
    paths = git("ls-files", "backend/app", "frontend/src").splitlines()
    digest = hashlib.sha256()
    for name in paths:
        path = ROOT / name
        data = path.read_bytes().replace(b"\r\n", b"\n") if path.exists() else b"MISSING"
        digest.update(name.encode() + b"\0" + hashlib.sha256(data).digest())
    source_digest = hashlib.sha256()
    source_paths = sorted(path for folder in ("backend/app", "frontend/src") for path in (ROOT / folder).rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in (".pyc", ".pyo")
        and not any(fnmatch.fnmatch(path.relative_to(ROOT).as_posix(), pattern) for pattern in (
            "frontend/src/**/*.test.ts", "frontend/src/**/*.test.tsx", "frontend/src/**/*fixture*.json",
            "frontend/src/test-setup.ts", "frontend/src/test-source.ts")))
    for path in source_paths:
        source_digest.update(path.relative_to(ROOT).as_posix().encode() + b"\0"
            + hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).digest())
    return {"head_commit": git("rev-parse", "HEAD"), "product_paths_sha256": digest.hexdigest(),
            "product_path_count": len(paths), "hash_policy": "tracked backend/app + frontend/src, LF normalized; includes tests",
            "working_product_source_sha256": source_digest.hexdigest(), "working_product_source_count": len(source_paths),
            "working_source_policy": "all working backend/app + frontend/src including untracked; skip pycache and freeze TEST_ONLY_GLOBS"}


def details(name, output):
    clean = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", output)
    result = {}
    if name == "backend_pytest":
        lines = [line.strip() for line in clean.splitlines() if re.search(r"\d+ (?:passed|failed|error|skipped|deselected|xfailed)", line)]
        summary = lines[-1] if lines else "UNKNOWN"
        result["counts"] = {key: int(count) for count, key in re.findall(r"(\d+) (passed|failed|errors?|skipped|deselected|xfailed|xpassed)", summary)}
        result["summary"] = summary
        result["failure_node_ids"] = re.findall(r"^(?:FAILED|ERROR) ([^\s]+)", clean, re.MULTILINE)
    elif name == "frontend_test_wave":
        result["summary_lines"] = [line.strip() for line in clean.splitlines()
            if re.match(r"\s*(?:Test Files|Tests |Duration|.*built in )", line)]
        result["failure_node_ids"] = re.findall(r"^\s*FAIL\s+([^\n]+)", clean, re.MULTILINE)
        result["typescript_errors"] = len(re.findall(r"error TS\d+:", clean))
    elif name == "demo_replay":
        value = json.loads(clean)
        result = {key: value[key] for key in ("DEMO_CASES", "DEMO_REPLAY_PASS", "REDUCED_CHAIN_CASES")}
        result["semantic_pass"] = all(case.get("dat") for case in value["demo"]) and all(case.get("ok") for case in value["rut_gon"])
    elif name == "crash_audit":
        value = json.loads(clean)
        result = {"cases": len(value), "passed": sum(bool(case["khop"]) for case in value),
                  "uncaught": sum(bool(case["nem"]) for case in value)}
    elif name == "docs_ia":
        value = json.loads(clean)
        result = {"status": value["STATUS"], "broken_links": value["LINKS"]["broken_link_count"],
                  "stale_code_index_paths": value["CODE_INDEX"]["stale_path_count"],
                  "secret_leaks": value["SECRET_SCAN"]["leak_count"]}
    elif name.startswith("publication_"):
        result["summary_lines"] = [line for line in clean.splitlines() if line.startswith("SUMMARY ")]
    elif name == "freeze_verify":
        result["summary_lines"] = [line.strip() for line in clean.splitlines()
            if any(term in line for term in ("Candidate", "đóng băng", "MÃ SẢN PHẨM", "hiện tại", "commit"))]
    return result


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--phase", choices=("baseline", "final"), required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--only", nargs="+")
    args = parser.parse_args()
    temp_root = ROOT / ".superpowers/offline-logs" / RUN.name / args.phase
    temp_root.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": "", "PYTHONUTF8": "1",
           "TEMP": str(temp_root), "TMP": str(temp_root),
           "PYTEST_ADDOPTS": '-p no:cacheprovider --basetemp="' + (temp_root / ("pytest-" + str(os.getpid()))).as_posix() + '"',
           # conftest installs the parent guard, and adds sitecustomize only for children.
           "PYTHONPATH": str(ROOT / "backend"),
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "core.excludesFile", "GIT_CONFIG_VALUE_0": os.devnull,
           "GIT_CONFIG_KEY_1": "safe.directory", "GIT_CONFIG_VALUE_1": str(ROOT)}
    gates = [
        ("backend_pytest", [args.python, "-m", "pytest", "-c", "backend/pytest.ini", "backend/tests", "-q"], ROOT),
        ("frontend_test_wave", ["npm.cmd", "run", "test:wave"], ROOT / "frontend"),
        ("demo_replay", [args.python, "backend/scripts/replay_demo_cases.py", "--json"], ROOT),
        ("crash_audit", [args.python, "backend/scripts/audit_demo_crash_surface.py", "--json"], ROOT),
        ("docs_ia", [args.python, "backend/scripts/audit_docs_information_architecture.py", "--json"], ROOT),
        ("publication_head", [args.python, "backend/scripts/check_publication_safety.py", "--head"], ROOT),
        ("publication_range", [args.python, "backend/scripts/check_publication_safety.py", "--range", BASELINE + "..HEAD"], ROOT),
        ("freeze_verify", [args.python, "backend/scripts/freeze_evaluation_candidate.py", "--verify"], ROOT),
    ]
    if args.only:
        assert set(args.only) <= {gate[0] for gate in gates}, "unknown gate"
        gates = [gate for gate in gates if gate[0] in args.only]
    target = RUN / ("full_regression_baseline.json" if args.phase == "baseline" else "full_regression_summary.json")
    previous = json.loads(target.read_text(encoding="utf-8")) if target.exists() else None
    interrupted = previous and previous.get("verdict", "").startswith("INTERRUPTED_")
    if previous and not args.only and not interrupted:
        raise SystemExit("Refusing to overwrite an existing complete attempt; choose --only for explicit gate updates")
    receipt = previous or {
        "schema": "algosim-full-regression-summary/3", "run_id": RUN.name, "phase": args.phase,
        "started_at_utc": now(), "baseline_commit": BASELINE, "start_snapshot": snapshot(),
        "environment": {"os": platform.platform(), "python": sys.version.split()[0], "python_executable": args.python,
            "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": "EMPTY", "network_guard": "existing offline_child sitecustomize + pytest conftest socket/httpx guards",
            "node_dependencies": "ignored junction to existing root frontend/node_modules; no install"},
        "exclusions": ["pytest.ini: not postgres and not external_evidence", "live provider calls excluded", "no performance benchmark", "no independent clean-worktree claim"],
        "suites": []}
    if interrupted:
        receipt.setdefault("interrupted_attempts", []).append({key: receipt[key] for key in (
            "started_at_utc", "start_snapshot", "suites", "verdict")})
        receipt.update({"started_at_utc": now(), "start_snapshot": snapshot(), "suites": []})
    receipt["environment"]["TEMP_TMP"] = str(temp_root)
    receipt["environment"]["PYTEST_ADDOPTS"] = env["PYTEST_ADDOPTS"]
    receipt["environment"]["git_config_isolation"] = "Command-scoped: global/system config disabled; core.excludesFile=null; safe.directory=specified worktree only. No persistent Git config change."
    receipt["environment"]["network_guard"] = "Parent guard installed by backend/conftest.py; conftest injects sitecustomize for children. No premature child guard on parent PYTHONPATH."
    logs = RUN / "logs"
    logs.mkdir(exist_ok=True)
    receipt["verdict"] = "RUNNING"
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, command, cwd in gates:
        print("START " + name, flush=True)
        entry = {"name": name, "command": subprocess.list2cmdline(command), "argv": command,
                 "cwd": str(cwd), "started_at_utc": now(), "start_snapshot": snapshot()}
        started = time.monotonic()
        with tempfile.NamedTemporaryFile(prefix="algosim-regression-", suffix=".log", dir=temp_root, delete=False) as raw:
            raw_path = Path(raw.name)
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=raw, stderr=subprocess.STDOUT)
            print(json.dumps({"name": name, "pid": process.pid, "raw_local_log": str(raw_path)}), flush=True)
            process.wait()
        data = raw_path.read_bytes()
        entry.update({"ended_at_utc": now(), "duration_seconds": round(time.monotonic() - started, 3),
            "exit_code": process.returncode, "raw_output_sha256": hashlib.sha256(data).hexdigest(),
            "raw_output_bytes": len(data), "raw_output_retention": "ignored local .superpowers only; never staged",
            "end_snapshot": snapshot()})
        try:
            entry.update(details(name, data.decode("utf-8", errors="replace")))
        except (ValueError, KeyError, TypeError) as error:
            entry["summary_parse_error"] = type(error).__name__
        entry["source_unchanged_during_command"] = (
            entry["start_snapshot"]["working_product_source_sha256"]
            == entry["end_snapshot"]["working_product_source_sha256"])
        entry["verdict"] = "PASS" if (process.returncode == 0 and entry.get("semantic_pass", True)
            and "summary_parse_error" not in entry and entry["source_unchanged_during_command"]) else "FAIL"
        log_path = logs / (args.phase + "-" + name + ".json")
        if log_path.exists():
            old = json.loads(log_path.read_text(encoding="utf-8"))
            entry["previous_attempts"] = old.get("previous_attempts", []) + [{key: val for key, val in old.items() if key != "previous_attempts"}]
        log_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        receipt["suites"] = [item for item in receipt["suites"] if item["name"] != name] + [entry]
        receipt["end_snapshot"] = snapshot()
        receipt["source_unchanged_across_run"] = (receipt["start_snapshot"]["working_product_source_sha256"]
            == receipt["end_snapshot"]["working_product_source_sha256"])
        receipt["ended_at_utc"] = now()
        receipt["verdict"] = "PASS" if (len(receipt["suites"]) == 8 and receipt["source_unchanged_across_run"]
            and all(item["verdict"] == "PASS" for item in receipt["suites"])) else "INCOMPLETE_OR_FAIL"
        target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"name": name, "exit_code": process.returncode, "verdict": entry["verdict"], "raw_local_log": str(raw_path),
            **{key: entry[key] for key in ("counts", "summary", "summary_lines", "failure_node_ids", "status") if key in entry}}, ensure_ascii=False), flush=True)
    return 0 if receipt["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
