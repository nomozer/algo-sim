"""Hash the run's text artifacts; preserve binary images in ignored local storage."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import evaluate_acceptance as E

run = E.RUN
artifacts = {}
for path in sorted(run.rglob("*")):
    if not path.is_file() or path.name == "run.json" or "__pycache__" in path.parts:
        continue
    assert path.suffix in (".json", ".md", ".py", ".mjs"), path
    data = path.read_bytes().replace(b"\r\n", b"\n")
    artifacts[path.relative_to(run).as_posix()] = {"sha256_lf": hashlib.sha256(data).hexdigest(), "bytes_lf": len(data)}
regression = json.loads((run / "full_regression_summary.json").read_text(encoding="utf-8"))
candidate = json.loads((E.ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
status = E.freeze._git("status", "--porcelain")
E.write("run.json", {"schema": "algosim-real-image-comparative-run/1", "run_id": run.name,
    "task_slug": run.name, "wave_id": "real-image-ocr-vision-comparative-acceptance-w01",
    "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    "baseline_commit": "6bb22fa3bb183ad28cdf1395c99e5eb375fac97c",
    "head_at_manifest_write": E.freeze._git("rev-parse", "HEAD"), "product_commit": E.freeze.product_commit(),
    "branch": E.freeze._git("branch", "--show-current"), "working_tree_clean_at_manifest_write": not bool(status),
    "measured_system": candidate["measured_system"], "cache_version": candidate["cache_version"],
    "regression_status": regression.get("verdict"), "status": "OFFLINE_DELIVERED_WITH_EXPLICIT_LIMITS",
    "live_vision": "NOT_AUTHORIZED", "actual_provider_calls": 0,
    "real_student_usability": "NOT_MEASURED", "independent_h1": "NOT_MEASURED", "physical_low_end": "NOT_MEASURED",
    "architecture_decision": "DECISION_PENDING_LIVE_EVIDENCE", "merge_push_deploy": "NOT_PERFORMED",
    "report": "AXO_REAL_IMAGE_OCR_VISION_COMPARATIVE_ACCEPTANCE_REPORT.md",
    "hash_policy": "SHA256 of UTF-8 text bytes with CRLF normalized to LF, matching Git content semantics. Manifest excludes itself; no image binaries committed.",
    "artifacts": artifacts})
print("Run manifest:", len(artifacts), "artifacts; regression", regression.get("verdict"))
