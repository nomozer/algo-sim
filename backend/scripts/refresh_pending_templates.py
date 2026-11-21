# -*- coding: utf-8 -*-
"""Re-bind the C21 PENDING owner-approval templates (K-1, R-1, S-2) to the current runtime identity.

Shared tool (since /13). Twenty-four runs each copied their own `tools/refresh_pending_templates.py` that differed only
in the REASON text and in writing its receipt next to itself; those copies stay where they are (each produced its
run's frozen receipt). New runs call this one with their run directory.

Metadata refresh ONLY: a template must already say `owner_decision = "PENDING_OWNER_DECISION"` and
`paid_project_confirmed = false`, and keeps both — this never writes a human approval (`APPROVED_BY_USER` is the
Owner's alone). The receipt + the untouched originals go to `<run-dir>/pending_template_refresh.json` and
`<run-dir>/logs/prior-<template>`; an existing receipt is never overwritten (frozen evidence of an earlier refresh).

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/refresh_pending_templates.py \
        --run-dir ../docs/evaluation/geometry/runs/<run> --reason "<why the measured system changed>"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from scripts import run_s2_student_language_pilot as R  # noqa: E402

KEYS = ("measured_system", "runner_sha256", "paired_harness_sha256", "scorer_sha256")
PENDING = "PENDING_OWNER_DECISION"


def _sha_lf(b: bytes) -> str:
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def refresh(run_dir: Path, reason: str, *, specs=None, ident=None) -> dict:
    """Rewrite every template's identity fields; returns the receipt (also written to `run_dir`)."""
    receipt_path = run_dir / "pending_template_refresh.json"
    if receipt_path.exists():
        raise SystemExit(f"{receipt_path} exists — a refresh receipt is evidence; use a new run directory")
    ident = ident or R.runtime_identity()
    specs = specs or R.default_c21_pilot_specs()
    logs = run_dir / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    rows = []
    for study, sp in specs.items():
        tpath = Path(sp["template_path"])
        raw = tpath.read_bytes()
        tmpl = json.loads(raw.decode("utf-8"))
        if tmpl.get("owner_decision") != PENDING or tmpl.get("paid_project_confirmed") is not False:
            raise SystemExit(f"{study}: template is not a pending, unpaid template — refusing to touch it")
        backup = logs / f"prior-{tpath.name}"
        if not backup.exists():
            backup.write_bytes(raw)
        before = {k: tmpl.get(k) for k in (*KEYS, "measured_system_tree_hash")}
        for k in KEYS:
            tmpl[k] = ident[k]
        tmpl["measured_system_tree_hash"] = ident["measured_system"]
        tmpl["corpus_sha256"] = R.sha256_file(Path(sp["corpus_path"]))
        tpath.write_text(json.dumps(tmpl, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        rows.append({
            "study": study,
            "template": tpath.as_posix(),
            "before": before,
            "after": {k: tmpl.get(k) for k in (*KEYS, "measured_system_tree_hash")},
            "original_saved_as": backup.relative_to(run_dir).as_posix(),
            "original_sha256": _sha_lf(raw),
            "new_sha256": _sha_lf(tpath.read_bytes()),
            "owner_decision": tmpl["owner_decision"],
            "paid_project_confirmed": tmpl["paid_project_confirmed"],
        })
    out = {
        "classification": "CURRENT_PENDING_TEMPLATE_METADATA_REFRESH_NOT_HUMAN_APPROVAL",
        "tool": "backend/scripts/refresh_pending_templates.py",
        "reason": reason,
        "runtime_identity_measured_system": ident["measured_system"],
        "rows": rows,
    }
    receipt_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--run-dir", required=True, type=Path)
    p.add_argument("--reason", required=True)
    a = p.parse_args()
    out = refresh(a.run_dir.resolve(), a.reason)
    print(f"Refreshed {len(out['rows'])} pending templates -> {a.run_dir / 'pending_template_refresh.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
