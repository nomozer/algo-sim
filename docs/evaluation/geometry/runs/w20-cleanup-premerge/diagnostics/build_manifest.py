# -*- coding: utf-8 -*-
"""W20 — MANIFEST.json of this run: every file with sha256, its basis, its producer and its measurement status
(same shape as w18's `diagnostics/build_manifest.py`).

Basis per file: `git_blob_lf` for text (the LF-normalised content, which equals the committed blob under
`core.autocrlf`). Producer and status come from the first matching rule below; a file no rule names stops the build,
so nothing is listed with an invented producer. The manifest never records the SHA of the commit that contains it.
Overwrites MANIFEST.json (it is derived, not evidence). Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w20-cleanup-premerge/diagnostics/build_manifest.py
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "MANIFEST.json"
V = "5fbb397b"
A, S, D, R = "AUTHORITATIVE", "SUPERSEDED", "DIAGNOSTIC", "RECORD"
HAND = "hand-written run document"
SCRIPT = "hand-written W20 diagnostic script (0 model calls)"
RULES = [  # (pattern, producer, measurement status) — first match wins
    ("PLAN.md", HAND, R), ("REPORT.md", HAND, R), ("HANDOFF.md", HAND, R), ("RUN.json", HAND, R),
    ("inputs/CANDIDATE_DIVERGENCE_CORRECTION.json", "hand-written candidate divergence declaration (two freezes)", R),
    ("diagnostics/literal_target_corpus/LABELS.json", "hand-written labels, registered before any product change (f0edcd11)", A),
    ("diagnostics/literal_target_corpus/CORPUS.json", "diagnostics/proof_cache_row_w20.py corpus @ 65c90bde (the probe's builders)", A),
    ("diagnostics/FROZEN_WRITER_REPRODUCTION.json", "hand-written record of a reproduction on a temporary copy @ f0edcd11", R),
    ("diagnostics/TEMP_FILE_INVENTORY.json", "hand-written inventory of the temporary files of the wave", R),
    ("diagnostics/CONSTRUCTION_BINDING_CENSUS_W20.json", "diagnostics/construction_binding_census_w20.py @ 65c90bde", A),
    ("diagnostics/CONSTRUCTION_BINDING_DECISION_W20.json", "diagnostics/construction_binding_census_w20.py @ 65c90bde", A),
    ("diagnostics/PROOF_CACHE_ROW_W20.json", "diagnostics/proof_cache_row_w20.py prove (envelopes: before f0edcd11, after 65c90bde)", A),
    ("diagnostics/LITERAL_THEN_CONSTRUCT_SCAN.json", "diagnostics/scan_literal_then_construct.py (commit in the file)", A),
    ("diagnostics/*.py", SCRIPT, R), ("diagnostics/*.ps1", SCRIPT, R), ("diagnostics/*.sh", SCRIPT, R),
    ("inventory/CLEANUP_INVENTORY.json", "diagnostics/inventory_cleanup_w20.py @ a36f3e97", A),
    ("inventory/DELETION_LOG.json", "inventory/CLEANUP_INVENTORY.json + results/logs/CLEANUP_APPLY.log (deletion step)", A),
    ("results/LITERAL_TARGET_PROBE_before_2cb4ed8c.json", "diagnostics/probe_literal_target.py --tag before @ 2cb4ed8c (23 rows, before amendment_1)", S),
    ("results/LITERAL_TARGET_PROBE_before-r2_2cb4ed8c.json", "diagnostics/probe_literal_target.py --tag before-r2 @ 2cb4ed8c (27 rows)", A),
    ("results/LITERAL_TARGET_PROBE_after_65c90bde.json", "diagnostics/probe_literal_target.py --tag after @ 65c90bde", A),
    (f"results/LITERAL_TARGET_PROBE_final_{V}.json", f"diagnostics/probe_literal_target.py --tag final @ {V} (clean detached worktree)", A),
    ("results/logs/RED_*.log", "pytest output before the fix (trailing spaces stripped)", R),
    ("results/logs/FAULT_INJECTION_W20.log", "diagnostics/run_fault_injections_w20.py @ f0edcd11 + uncommitted fix", S),
    ("results/logs/FAULT_INJECTION_W20_r2.log", "diagnostics/run_fault_injections_w20.py _r2 @ ac241a8d + uncommitted E fix", S),
    (f"results/logs/FAULT_INJECTION_W20_r3.log", f"diagnostics/run_fault_injections_w20.py _r3 @ {V} (clean detached worktree)", A),
    ("results/logs/PYTEST_INTERIM_MAIN_TREE.log", "pytest, main tree @ f0edcd11 + uncommitted fix (failure classification in the header)", D),
    ("results/logs/PRE_FREEZE_FULL_BACKEND_*.log", "pytest, main tree before the first freeze (failure classification in the header)", D),
    ("results/logs/CLEANUP_APPLY.log", "diagnostics/apply_cleanup_w20.ps1 output", A),
    (f"results/logs/T3_FULL_GATE_{V}.log", f"frontend/scripts/full-gate.mjs @ {V} from a path with a space (clean detached worktree)", A),
    (f"results/logs/GATES_{V}.log", f"diagnostics/w20_gates.sh {V} 2cb4ed8c (clean detached worktree)", A),
    (f"results/logs/WORKTREE_STATUS_AFTER_{V}.log", f"git status of the verification worktree after every run @ {V}", A),
]


def _ban_lf(p: Path) -> bytes:
    return p.read_bytes().replace(b"\r\n", b"\n")


def main() -> None:
    muc = []
    for p in sorted(x for x in RUN.rglob("*") if x.is_file() and x != OUT):
        r = p.relative_to(RUN).as_posix()
        luat = next(((sx, tt) for mau, sx, tt in RULES if fnmatch.fnmatch(r, mau)), None)
        if luat is None:
            raise SystemExit(f"no producer rule for {r}")
        b = _ban_lf(p)
        muc.append({"path": r, "sha256": hashlib.sha256(b).hexdigest(), "basis": "git_blob_lf", "bytes": len(b),
                    "producer": luat[0], "status": luat[1]})
    OUT.write_text(json.dumps({"schema_version": "run-manifest/1", "run": "w20-cleanup-premerge",
                               "verification_commit": V, "files": muc}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8", newline="\n")
    print(len(muc), "files")


if __name__ == "__main__":
    main()
