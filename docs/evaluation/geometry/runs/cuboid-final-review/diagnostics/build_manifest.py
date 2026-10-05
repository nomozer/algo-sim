# -*- coding: utf-8 -*-
"""cuboid-final-review — MANIFEST.json of this run: every file with sha256, its basis, its producer and its measurement
status (same shape as w20's `diagnostics/build_manifest.py`).

Basis per file: `git_blob_lf` (the LF-normalised content, which equals the committed blob under `core.autocrlf`).
Producer and status come from the first matching rule below; a file no rule names stops the build, so nothing is
listed with an invented producer. The manifest never records the SHA of the commit that contains it. Overwrites
MANIFEST.json (it is derived, not evidence). Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/build_manifest.py
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "MANIFEST.json"
V = "a1c53cdb"
A, S, D, R = "AUTHORITATIVE", "SUPERSEDED", "DIAGNOSTIC", "RECORD"
HAND = "hand-written run document"
SCRIPT = "hand-written diagnostic script of this run (0 model calls)"
WT = f"@ {V} (clean detached worktree 'D:/tmp/cfr space/algo-sim')"
RULES = [  # (pattern, producer, measurement status) — first match wins
    ("PLAN.md", HAND, R), ("REPORT.md", HAND, R), ("HANDOFF.md", HAND, R), ("RUN.json", HAND, R),
    ("inputs/CANDIDATE_DIVERGENCE_CORRECTION.json", "hand-written candidate divergence declaration (one freeze)", R),
    ("inventory/DOCS_INVENTORY.json", f"diagnostics/inventory_docs_cfr.py {WT}", A),
    ("inventory/DOCS_INVENTORY_BEFORE_4048ff83.json", "diagnostics/inventory_docs_cfr.py @ 4048ff83 (detached worktree)", A),
    ("inventory/HISTORY_SPLIT.json", "diagnostics/split_history_cfr.py --apply (blocks of the 4048ff83 blobs)", A),
    ("inventory/CLEANUP_LOG.json", "hand-written log of the moves, in-place edits and deletions", R),
    ("diagnostics/TEMP_FILE_INVENTORY.json", "hand-written inventory of the temporary files of the run", R),
    ("diagnostics/cache_proof/CORPUS_W20_LABELS.json",
     "runs/w20-cleanup-premerge/diagnostics/proof_cache_row_w20.py corpus (W20 corpus builders, main tree @ fac2769e)", A),
    ("diagnostics/cache_proof/PROOF_CACHE_ROW_CFR.json",
     "runs/w20-cleanup-premerge/diagnostics/proof_cache_row_w20.py prove (envelopes: before 4048ff83, after 284a9bfa)", A),
    ("diagnostics/cache_proof/CACHE_DECISION_CFR.json", "diagnostics/cache_decision_cfr.py on the same envelopes", A),
    ("diagnostics/*.py", SCRIPT, R), ("diagnostics/*.mjs", SCRIPT, R), ("diagnostics/*.sh", SCRIPT, R),
    ("results/browser/CASES.json", f"diagnostics/refusal_fixtures_cfr.py {WT}", A),
    ("results/browser/fixtures/*.json", f"diagnostics/refusal_fixtures_cfr.py {WT} (frozen corpus programs through run_pipeline)", A),
    ("results/BROWSER_REFUSAL_CFR.json", f"diagnostics/browser_refusal_cfr.mjs {WT}, production build", A),
    ("images/*/*/*.png", f"diagnostics/browser_refusal_cfr.mjs {WT}, production build", A),
    ("results/logs/RED_*.log", "test output before the fix, main tree (trailing spaces stripped)", R),
    ("results/logs/GREEN_*.log", "test output after the fix, main tree @ the fix before its commit", R),
    ("results/logs/PRE_FREEZE_FULL_BACKEND_*.log", "pytest, main tree before the freeze (failure classification in the header)", D),
    (f"results/logs/T3_FULL_GATE_{V}.log", f"frontend/scripts/full-gate.mjs {WT}", A),
    (f"results/logs/GATES_{V}.log", f"diagnostics/cfr_gates.sh {V} 4048ff83 {WT}", A),
    (f"results/logs/BROWSER_REFUSAL_attempt1_DIST_CU_{V}.log", f"diagnostics/browser_refusal_cfr.mjs {WT}, stopped by the dist freshness guard", S),
    (f"results/logs/BROWSER_REFUSAL_{V}.log", f"diagnostics/browser_refusal_cfr.mjs {WT} (console)", A),
    (f"results/logs/BUILD_BEFORE_BROWSER_{V}.log", f"npm run build {WT}, before the second browser attempt", R),
    (f"results/logs/WORKTREE_STATUS_{V}.log", f"git status of the verification worktree after every run {WT}", A),
    ("results/logs/DOCS_GATES_FINAL.log", "docs gates in a clean detached worktree at the documentation commit", A),
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
        b = _ban_lf(p) if p.suffix != ".png" else p.read_bytes()
        muc.append({"path": r, "sha256": hashlib.sha256(b).hexdigest(),
                    "basis": "raw_bytes" if p.suffix == ".png" else "git_blob_lf", "bytes": len(b),
                    "producer": luat[0], "status": luat[1]})
    OUT.write_text(json.dumps({"schema_version": "run-manifest/1", "run": "cuboid-final-review",
                               "verification_commit": V, "files": muc}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8", newline="\n")
    print(f"{OUT.name}: {len(muc)} files")


if __name__ == "__main__":
    main()
