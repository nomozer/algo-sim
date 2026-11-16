# -*- coding: utf-8 -*-
"""Re-bind the three PENDING owner-approval templates to the current measured system after a product change.

Only `measured_system` / `measured_system_tree_hash` change. owner_decision stays PENDING_OWNER_DECISION and
paid_project_confirmed stays false; this is metadata, not approval. Original bytes are saved in logs/.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "backend/scripts")]
import run_s2_student_language_pilot as R  # noqa: E402

KEYS = ("measured_system", "measured_system_tree_hash")
OUT = sys.argv[1] if len(sys.argv) > 1 else "pending_template_refresh.json"
REASON = sys.argv[2] if len(sys.argv) > 2 else (
    "test_s2_student_language_pilot_runner requires pending templates to bind the current runtime; "
    "compositional-planner-capability-expansion changes in registry.py, typed_fact_next_bridge.py, "
    "planner.py, and engine.py updated the measured system."
)


def main() -> int:
    ident = R.runtime_identity()
    logs = RUN / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    rows = []
    for study, spec in R.default_c21_pilot_specs().items():
        path = Path(spec["template_path"])
        original = path.read_bytes()
        data = json.loads(original.decode("utf-8"))
        assert data["owner_decision"] == "PENDING_OWNER_DECISION" and data["paid_project_confirmed"] is False, path
        before = {k: data.get(k) for k in KEYS}
        for key in KEYS:
            if key in data:
                data[key] = ident["measured_system"]
        for key in ("runner_sha256", "paired_harness_sha256", "scorer_sha256"):
            assert data[key] == ident[key], f"{study}: {key} drift is not a measured-system refresh; stop"
        saved = logs / f"prior-{path.name}"
        if not saved.exists():
            saved.write_bytes(original)
        path.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        rows.append({
            "study": study,
            "template": path.relative_to(ROOT).as_posix(),
            "before": before,
            "after": {k: data.get(k) for k in KEYS},
            "original_saved_as": saved.relative_to(RUN).as_posix(),
            "original_sha256": hashlib.sha256(original).hexdigest(),
            "new_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "owner_decision": data["owner_decision"],
            "paid_project_confirmed": data["paid_project_confirmed"],
        })
    (RUN / OUT).write_text(
        json.dumps(
            {
                "classification": "CURRENT_PENDING_TEMPLATE_METADATA_REFRESH_NOT_HUMAN_APPROVAL",
                "reason": REASON,
                "runtime_identity_measured_system": ident["measured_system"],
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps([(r["study"], r["before"]["measured_system"][:12], r["after"]["measured_system"][:12]) for r in rows]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
