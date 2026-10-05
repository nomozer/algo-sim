# -*- coding: utf-8 -*-
"""regular-square-pyramid-w01 — MANIFEST.json of this run: every file with sha256, its basis, its producer and its
measurement status (same shape as w20-cleanup-premerge's `diagnostics/build_manifest.py`).

Basis per file: `git_blob_lf` (LF-normalised content, equal to the committed blob under `core.autocrlf`). Producer and
status come from the first matching rule; a file no rule names stops the build, so nothing is listed with an invented
producer. The manifest never records the SHA of the commit that contains it. Overwrites MANIFEST.json (derived, not
evidence). Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/regular-square-pyramid-w01/diagnostics/build_manifest.py
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "MANIFEST.json"
M, V = "ed37f9fa", "96181b87"
A, S, D, R = "AUTHORITATIVE", "SUPERSEDED", "DIAGNOSTIC", "RECORD"
HAND = "hand-written run document"
SCRIPT = "hand-written W1 diagnostic script (0 model calls)"
WT = "clean detached worktree 'D:/tmp/rsp w01'"
RULES = [  # (pattern, producer, measurement status) — first match wins
    ("PLAN.md", HAND, R), ("REPORT.md", HAND, R), ("HANDOFF.md", HAND, R), ("RUN.json", HAND, R),
    ("inputs/CANDIDATE_DIVERGENCE_CORRECTION.json", "hand-written candidate divergence declaration (one freeze)", R),
    ("inputs/FIXTURE_MANIFEST.json", f"backend/scripts/generate_generic_tier_a_fixtures.py @ {M} ({WT})", A),
    ("inputs/fixtures/*.json", f"backend/scripts/generate_generic_tier_a_fixtures.py @ {M} ({WT})", A),
    ("diagnostics/corpus/LABELS.json", "hand-written labels, registered before any product change (e537dbd9)", A),
    ("diagnostics/corpus/W18_LABEL_CORRECTIONS.json", "hand-written correction layer over the W18 labels (3bdada32)", A),
    ("diagnostics/PREREGISTRATION_CORRECTIONS.json", "hand-written, before any browser run (c37b2cc4)", A),
    ("diagnostics/PONYTAIL_REVIEW.json", "hand-written ponytail review of 38d41588..de5b2331", R),
    ("diagnostics/cache_proof_corpus_w01.json", "diagnostics/proof_cache_row_w01.py corpus (main tree @ 9d66c603)", A),
    ("diagnostics/PROOF_CACHE_ROW_W01.json", "diagnostics/proof_cache_row_w01.py prove (before 38d41588, after 9d66c603)", A),
    ("diagnostics/SCOPE_LENGTH_CLUE_PROBE_1310658b.json", "diagnostics/probe_scope_length_clue.py @ 1310658b", A),
    ("diagnostics/MEASUREMENT_ATTEMPTS.json", "hand-written record of every measurement attempt", R),
    ("diagnostics/TEMP_FILE_INVENTORY.json", "hand-written inventory of the temporary files of the wave", R),
    ("diagnostics/WORKTREE_CLEANUP.json", "hand-written record of worktree removal", R),
    ("diagnostics/*.py", SCRIPT, R), ("diagnostics/*.sh", SCRIPT, R),
    ("diagnostics/logs/PRE_FREEZE_FULL_BACKEND_de5b2331.log", "pytest, main tree before the freeze (stale-candidate class)", D),
    ("diagnostics/logs/*_attempt1_3ad9442f.log", f"failed measurement attempt 1 @ 3ad9442f ({WT})", S),
    ("diagnostics/logs/*_attempt2_1310658b.log", f"failed measurement attempt 2 @ 1310658b ({WT})", S),
    (f"diagnostics/logs/*_{M}.log", f"measurement @ {M} ({WT}); command at the top of the log", A),
    (f"diagnostics/logs/T3_FULL_GATE_attempt1_{V}.log", f"failed T3 attempt 1 @ {V}: its own log made the tree dirty", S),
    (f"diagnostics/logs/T3_FULL_GATE_{V}.log", f"frontend/scripts/full-gate.mjs @ {V} from a path with a space ({WT})", A),
    (f"diagnostics/logs/GATES_{V}.log", f"diagnostics/w01_gates.sh {V} 38d41588 ({WT})", A),
    ("results/BROWSER_EVIDENCE.json", f"frontend/scripts/compiler-scene-replay.mjs --suite @ {M} ({WT}, attempt 3)", A),
    ("results/OCCLUSION_MEASUREMENT.json", f"backend/scripts/measure_scene3d_occlusion.py @ {M} ({WT})", A),
    ("results/PLAYBACK_EVIDENCE.json", f"frontend/scripts/scene3d-playback-check.mjs --theo-ho --lap-orbit 5 @ {M} ({WT})", A),
    ("results/HIDDEN_EDGE_CROPS.json", f"backend/scripts/build_scene3d_visual_evidence.py @ {M} ({WT})", A),
    ("images/*/SHEET.png", f"backend/scripts/build_scene3d_visual_evidence.py @ {M}", A),
    ("images/*/FILMSTRIP.png", f"backend/scripts/build_scene3d_visual_evidence.py @ {M}", A),
    ("images/overview/*", f"backend/scripts/build_scene3d_visual_evidence.py @ {M}", A),
    ("images/*/hidden-edges/*", f"backend/scripts/build_scene3d_visual_evidence.py @ {M}", A),
    ("images/*/playback/*", f"frontend/scripts/scene3d-playback-check.mjs @ {M}", A),
    ("images/*", f"frontend/scripts/compiler-scene-replay.mjs --suite @ {M} (screenshots)", A),
]


def _ban_lf(p: Path) -> bytes:
    return p.read_bytes().replace(b"\r\n", b"\n") if p.suffix not in (".png",) else p.read_bytes()


def main() -> None:
    muc = []
    for p in sorted(x for x in RUN.rglob("*") if x.is_file() and x != OUT):
        r = p.relative_to(RUN).as_posix()
        luat = next(((sx, tt) for mau, sx, tt in RULES if fnmatch.fnmatch(r, mau)), None)
        if luat is None:
            raise SystemExit(f"no producer rule for {r}")
        b = _ban_lf(p)
        muc.append({"path": r, "sha256": hashlib.sha256(b).hexdigest(),
                    "basis": "raw_bytes" if p.suffix == ".png" else "git_blob_lf", "bytes": len(b),
                    "producer": luat[0], "status": luat[1]})
    OUT.write_text(json.dumps({"schema_version": "run-manifest/1", "run": "regular-square-pyramid-w01",
                               "measurement_commit": M, "verification_commit": V, "files": muc},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(len(muc), "files")


if __name__ == "__main__":
    main()
