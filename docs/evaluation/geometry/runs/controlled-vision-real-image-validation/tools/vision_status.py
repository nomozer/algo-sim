"""Record whether a live Vision benchmark is authorised, and what the offline harness can already do. No provider call.

Reads: this run's API receipts (observed provider calls), the frozen manifest (hash-bound image list a future
authorisation must name), and the previous run's authorisation preflight (tools/vision_comparison.py), which is run
as a subprocess in its default mode and in --self-test mode.  Run from backend/.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
PREFLIGHT = ROOT / "docs/evaluation/geometry/runs/real-image-ocr-vision-comparative-acceptance/tools/vision_comparison.py"
AUTHORIZATION = RUN / "owner_live_vision_authorization.json"  # only the Owner creates this file


def run(*args: str) -> dict:
    done = subprocess.run([sys.executable, str(PREFLIGHT), *args], capture_output=True, text=True, env={**os.environ, "ALLOW_LIVE_AI": "0"})
    return {"argv": list(args), "exit_code": done.returncode, "stdout": done.stdout.strip()[-400:]}


def main() -> int:
    manifest_path = RUN / "new_in_scope_image_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    calls = {}
    for name in sorted(RUN.glob("api_acceptance_*.json")):
        cases = json.loads(name.read_text(encoding="utf-8"))["cases"]
        calls[name.name] = sum(c.get("provider_calls") or 0 for c in cases)
    authorized_file = AUTHORIZATION.exists()
    preflight = [run("--self-test"), run()]
    if authorized_file:
        preflight.append(run("--authorization", str(AUTHORIZATION), "--corpus", str(manifest_path)))
    out = {
        "schema": "algosim-live-vision-authorization-status/2", "run_id": RUN.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "LIVE_VISION_AUTHORIZATION": "GRANTED" if authorized_file and preflight[-1]["exit_code"] == 3 else "NOT_GRANTED",
        "status": "LIVE_VISION_NOT_MEASURED", "blocker": "BLOCKED_PENDING_OWNER_APPROVAL",
        "architecture_decision": "ARCHITECTURE_DECISION_PENDING_LIVE_EVIDENCE",
        "owner_authorization_file_present": authorized_file,
        "allow_live_ai_in_measurement_server": os.environ.get("ALLOW_LIVE_AI", "0"),
        "observed_provider_calls_in_this_run": calls, "total_observed_provider_calls": sum(calls.values()),
        "provider_key_presence_used_as_authorization": False,
        "simulated_vision_payloads_used": False,
        "authorization_must_name": ["provider", "model and version", "image SHA-256 list (from the manifest below)", "maximum requests including retries",
                                    "maximum USD with a pre-request reservation", "retry limit", "personal-data rule", "stop conditions", "approver"],
        "hash_bound_corpus": {"manifest": manifest_path.relative_to(ROOT).as_posix(),
                              "manifest_sha256_lf": hashlib.sha256(manifest_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                              "images": [{"case_id": i["case_id"], "sha256": i["sha256"], "partition": i["partition"]} for i in manifest["items"]],
                              "personal_data": "none: rendered exam crops from a public dataset, no faces, names or handwriting"},
        "offline_readiness": {
            "preflight_tool": PREFLIGHT.relative_to(ROOT).as_posix(), "preflight_runs": preflight,
            "ready": ["frozen hash-bound manifest", "agent references and critical-fact schema (new_in_scope_image_manifest.json)",
                      "production Vision extractor reused, not duplicated: backend/app/ingestion/image_extraction.py", "request cap primitive: backend/app/ai/gemini.py ApiBudget",
                      "OCR-vs-Vision fact comparison with dimension binding: backend/app/ai/adaptive_input_router.py::compare_ocr_and_vision_facts",
                      "solver path for extracted text: /api/analyze (Source Gate -> parser -> planner -> exact kernel -> Scene3D)",
                      "grading against the dataset key: tools/evaluate_images.py::grade"],
            "not_connected_by_design": ["USD reservation and observed-cost accounting", "live executor (vision_comparison.py returns BOUNDED_EXECUTOR_REQUIRED even after a valid authorisation)"],
            "routing_safety_tests": "vision_routing_safety_tests.json"},
        "what_a_live_run_would_measure": ["Vision transcription CER / critical-fact recovery on the same 25 images", "diagram-fact reading",
                                          "the 17 statements the local parser cannot finish, through the live typed-fact extractor",
                                          "latency and USD per image", "wrong-served against the dataset key"]}
    (RUN / "live_vision_authorization_status.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out["LIVE_VISION_AUTHORIZATION"], out["total_observed_provider_calls"], [p["exit_code"] for p in preflight])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
