"""Refresh C21 pending owner-approval templates to bind the /12 candidate runtime identity.

Metadata refresh ONLY: preserves `owner_decision = "PENDING_OWNER_DECISION"` and
`paid_project_confirmed = false` in every template (never writes human approval).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path.insert(0, str(ROOT / "backend"))

from scripts import run_s2_student_language_pilot as R  # noqa: E402

REASON = (
    "test_s2_student_language_pilot_runner requires pending templates to bind the current "
    "runtime; AXO HYBRID /12 changed backend/app (compositional parser local-geometry-parser/3, "
    "compositional-clause-analyzer/1, local-slm-extractor/6, slm-grounding-validator/6, "
    "Source Gate geometry-functions/33, diacritic-free domain gate, CACHE_VERSION 147) and "
    "frontend/src (V11-VIS-1 Scene3D framing); metadata refresh only, not human approval."
)


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def main() -> int:
    ident = R.runtime_identity()
    specs = R.default_c21_pilot_specs()
    logs_dir = RUN / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    keys = ("measured_system", "runner_sha256", "paired_harness_sha256", "scorer_sha256")
    for study, sp in specs.items():
        tpath = Path(sp["template_path"])
        raw_bytes = tpath.read_bytes()
        orig_sha = _sha_bytes(raw_bytes)
        tmpl = json.loads(raw_bytes.decode("utf-8"))
        assert tmpl.get("owner_decision") == "PENDING_OWNER_DECISION", f"{study} not PENDING_OWNER_DECISION"
        assert tmpl.get("paid_project_confirmed") is False, f"{study} paid_project_confirmed not False"

        backup = logs_dir / f"prior-{tpath.name}"
        if not backup.exists():
            backup.write_bytes(raw_bytes)

        before = {k: tmpl.get(k) for k in (*keys, "measured_system_tree_hash")}
        for k in keys:
            tmpl[k] = ident[k]
        tmpl["measured_system_tree_hash"] = ident["measured_system"]
        tmpl["corpus_sha256"] = R.sha256_file(Path(sp["corpus_path"]))
        tmpl["owner_decision"] = "PENDING_OWNER_DECISION"
        tmpl["paid_project_confirmed"] = False

        new_text = json.dumps(tmpl, ensure_ascii=False, indent=2) + "\n"
        tpath.write_text(new_text, encoding="utf-8", newline="\n")
        new_sha = _sha_bytes(tpath.read_bytes())

        after = {k: tmpl.get(k) for k in (*keys, "measured_system_tree_hash")}
        rows.append({
            "study": study,
            "template": tpath.relative_to(ROOT).as_posix(),
            "before": before,
            "after": after,
            "original_saved_as": backup.relative_to(RUN).as_posix(),
            "original_sha256": orig_sha,
            "new_sha256": new_sha,
            "owner_decision": tmpl["owner_decision"],
            "paid_project_confirmed": tmpl["paid_project_confirmed"],
        })

    out = {
        "classification": "CURRENT_PENDING_TEMPLATE_METADATA_REFRESH_NOT_HUMAN_APPROVAL",
        "reason": REASON,
        "runtime_identity_measured_system": ident["measured_system"],
        "rows": rows,
    }
    receipt_path = RUN / "pending_template_refresh.json"
    receipt_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Refreshed {len(rows)} pending templates -> {receipt_path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
