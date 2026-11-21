"""Join disjoint command receipts; retain failed attempts and never turn a blocked gate green."""
from copy import deepcopy
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
path = RUN / "full_regression_summary.json"
summary = json.loads(path.read_text(encoding="utf-8"))
backend = json.loads((RUN / "full_regression_backend_final.json").read_text(encoding="utf-8"))
assert backend["verdict"] == "PASS", "Final full backend command has not passed"
entry = backend["suites"][0]
assert entry["name"] == "backend_pytest" and entry["exit_code"] == 0
assert entry["source_unchanged_during_command"]
old = next(row for row in summary["suites"] if row["name"] == "backend_pytest")
replacement = deepcopy(entry)
replacement["previous_attempts"] = old.get("previous_attempts", []) + [{k: v for k, v in old.items() if k != "previous_attempts"}]
summary["suites"] = [replacement if row["name"] == "backend_pytest" else row for row in summary["suites"]]
source = entry["end_snapshot"]["working_product_source_sha256"]
summary["source_unchanged_across_run"] = all(row["start_snapshot"]["working_product_source_sha256"] == source
    and row["end_snapshot"]["working_product_source_sha256"] == source for row in summary["suites"])
assert summary["source_unchanged_across_run"], "Sources differ between verification commands"
by_name = {row["name"]: row for row in summary["suites"]}
summary["all_requested_gates_executed"] = len(by_name) == 8
summary["product_test_status"] = "PASS" if all(by_name[name]["verdict"] == "PASS" for name in ("backend_pytest", "frontend_test_wave")) else "FAIL"
summary["remaining_blocked_gates"] = [name for name, row in by_name.items() if row["verdict"] != "PASS"]
summary["verdict"] = "PASS" if not summary["remaining_blocked_gates"] else "BLOCKED_GATES_REMAIN"
summary["release_acceptance"] = "BLOCKED_EXISTING_PUBLICATION_EXCEPTIONS" if summary["remaining_blocked_gates"] == ["publication_head"] else summary["verdict"]
summary["backend_receipt"] = "full_regression_backend_final.json"
summary["ended_at_utc"] = backend["ended_at_utc"]
summary["end_snapshot"] = backend["end_snapshot"]
if "interruption_reason" in summary:
    summary.setdefault("interruption_history", []).append(summary.pop("interruption_reason"))
path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Product tests:", summary["product_test_status"], "blocked gates:", summary["remaining_blocked_gates"])
