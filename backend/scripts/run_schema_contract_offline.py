"""Eight sequential offline invocations with real exits, a process-tree watchdog, and receipt checks. Never live."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from scripts import run_schema_contract_evaluation as R


def invoke(command, timeout, log):
    """A timeout terminates this invocation's children; it is never a geometry result."""
    start = time.monotonic()
    with Path(log).open("wb") as stream:
        process = subprocess.Popen(command, cwd=ROOT / "backend", stdout=stream, stderr=subprocess.STDOUT,
                                   env={**os.environ, "ALLOW_LIVE_AI": "0", "PYTHONUTF8": "1"},
                                   start_new_session=os.name != "nt")
        try:
            code = process.wait(timeout=timeout)
            status = "PASS" if code == 0 else "FAILURE"
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                killed = subprocess.run(["taskkill", "/F", "/PID", str(process.pid), "/T"], capture_output=True)
                if killed.returncode and process.poll() is None:
                    process.kill()  # Reap our owned parent even if the environment denies descendant cleanup.
                    process.wait(timeout=10)
                    raise RuntimeError("WATCHDOG_TERMINATION_FAILED")
            else:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)
            code, status = None, "INCOMPLETE_TIMEOUT"
    return {"status": status, "exit_code": code, "duration_seconds": round(time.monotonic() - start, 4),
            "log_sha256": hashlib.sha256(Path(log).read_bytes()).hexdigest()}


def check_receipt(out, identity, planned, action):
    state = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    score = json.loads((out / "score.json").read_text(encoding="utf-8"))
    expected_class = "GOLD" if action == "gold" else "FAKE"
    if (state["identity"] != identity or score["identity"] != identity
            or state["rows_sha256"] != R.V1._sha(state["rows"])
            or score["source_manifest_rows_sha256"] != state["rows_sha256"]
            or state["execution_class"] != expected_class or score["execution_class"] != expected_class
            or state.get("live_model_calls") != 0 or score.get("live_model_calls") != 0
            or score["schema"] != R.E.SCORER_VERSION
            or any(row.get("infra") for row in state["rows"])):
        raise R.V1.PilotStopped("RECEIPT_IDENTITY_OR_EXECUTION_MISMATCH")
    schedule = R.E.validate_schedule(state, planned)
    if schedule["status"] != "COMPLETE" or score["schedule"] != schedule:
        raise R.V1.PilotStopped("INCOMPLETE_RECEIPT")
    return {"status": "COMPLETE", "score_sha256": R.V1._lf_sha(out / "score.json"),
            "manifest_rows_sha256": state["rows_sha256"], "rows": len(state["rows"])}


def run_matrix(inputs, out, python):
    inputs, out = Path(inputs).resolve(), Path(out).resolve()
    if out.exists():
        raise R.V1.PilotStopped("OUTPUT_EXISTS")
    inp = R.E.load_inputs(inputs)
    if inp["protocol"]["lock_status"] != "LOCKED":
        raise R.V1.PilotStopped("PROTOCOL_NOT_LOCKED")
    timeout = inp["protocol"]["offline_watchdog_seconds"]
    if not isinstance(timeout, (float, int)) or not 0 < timeout <= 600:
        raise R.V1.PilotStopped("INVALID_OFFLINE_WATCHDOG")
    rows = [{"action": action, "arm": arm, "mode": mode, "status": "NOT_STARTED"}
            for mode in ("PILOT", "LOCKED") for arm in R.ARMS for action in ("gold", "replay")]
    doc = {"schema": "SCHEMA_CONTRACT_OFFLINE_INVOCATIONS/1", "status": "INCOMPLETE", "invocations": rows,
           "measurement_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
           "watchdog_seconds": timeout, "live_model_calls": 0}
    out.mkdir(parents=True)
    logs = ROOT / ".superpowers" / "offline-logs" / (out.parent.name + "-" + out.name)
    logs.mkdir(parents=True, exist_ok=True)
    persist = lambda: R.V1._persist(out / "invocations.json", doc, ())
    persist()
    for row in rows:
        action, arm, mode = row["action"], row["arm"], row["mode"]
        # Recheck every bound file before each child, rather than accepting source drift halfway through the matrix.
        current = R.E.load_inputs(inputs)
        harness = R.harness(arm, current, mode)
        row["input_identity"] = harness.identity(current, mode)
        row["destination"] = f"{action}-{arm}-{mode}"
        target = out / row["destination"]
        command = [str(python), "-B", str(Path(R.__file__)), action, "--arm", arm, "--mode", mode,
                   "--inputs", str(inputs), "--out", str(target)]
        row["status"] = "RUNNING"
        persist()
        start = time.monotonic()
        try:
            row.update(invoke(command, timeout, logs / (row["destination"] + ".log")))
        except (OSError, RuntimeError) as exc:
            row.update(status="FAILURE_HARNESS", exit_code=None, error_type=type(exc).__name__,
                       duration_seconds=round(time.monotonic() - start, 4))
        row["receipt"] = {"status": "ABSENT_OR_UNVERIFIED"}
        if row["status"] == "PASS":
            try:
                fresh = R.E.load_inputs(inputs)
                if R.harness(arm, fresh, mode).identity(fresh, mode) != row["input_identity"]:
                    raise R.V1.PilotStopped("POST_RUN_IDENTITY_MISMATCH")
                row["receipt"] = check_receipt(target, row["input_identity"], harness.schedule(current, mode), action)
            except (OSError, ValueError, KeyError, R.V1.PilotStopped) as exc:
                row["status"] = "INCOMPLETE_RECEIPT"
                row["receipt"] = {"status": "INVALID", "error_type": type(exc).__name__}
        persist()
        print(json.dumps({k: row[k] for k in ("action", "arm", "mode", "status", "exit_code", "duration_seconds")}), flush=True)
        if row["status"] != "PASS":
            break
    if all(row["status"] == "PASS" for row in rows):
        doc["status"] = "COMPLETE"
    persist()
    return doc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=R.RUN / "inputs")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    result = run_matrix(args.inputs, args.out, args.python)
    raise SystemExit(0 if result["status"] == "COMPLETE" else 1)
