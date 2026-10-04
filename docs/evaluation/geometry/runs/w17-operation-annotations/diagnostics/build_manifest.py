# -*- coding: utf-8 -*-
"""W17 — MANIFEST.json of this run: every file with sha256, its basis, its producer and its
measurement status (same shape as w16's `diagnostics/build_manifest.py`).

Basis per file: `raw_bytes` for binary files (PNG); `git_blob_lf` for text, i.e. the
LF-normalised content, which equals the committed blob under `core.autocrlf`.
Producer and status come from the first matching rule below; a file no rule names stops
the build, so nothing is listed with an invented producer. The manifest never records the
SHA of the commit that contains it. Overwrites MANIFEST.json (it is derived, not evidence).
Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w17-operation-annotations/diagnostics/build_manifest.py
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "MANIFEST.json"
M = "99925723"
TEXT = {".json", ".md", ".log", ".txt", ".tsv", ".py", ".mjs", ".sh"}
SUITE = f"frontend/scripts/compiler-scene-replay.mjs --suite @ {M} (attempt 2 on the final candidate d63d6fd4)"
BUILDER = f"backend/scripts/build_scene3d_visual_evidence.py @ {M}"
PLAYBACK = f"frontend/scripts/scene3d-playback-check.mjs --theo-ho --lap-orbit 5 @ {M}"
SCRIPT = "hand-written W17 diagnostic script (0 model calls)"
INTER = "diagnostics/evidence-intermediate-c5592c1a/"
FINAL1 = "diagnostics/browser-final-attempt1-83f101e4/"
A, S, F, D, R = "AUTHORITATIVE", "SUPERSEDED", "FAILED_ATTEMPT_KEPT_APART", "DIAGNOSTIC", "RECORD"
RULES = [  # (pattern, producer, measurement status) — first match wins
    ("README.md", "hand-written run document", R), ("REPORT.md", "hand-written run document", R),
    ("HANDOFF.md", "hand-written run document", R), ("RUN.json", "hand-written run document", R),
    ("inputs/CANDIDATE_DIVERGENCE_CORRECTION.json", "hand-written candidate divergence declaration (two freezes)", R),
    ("inputs/FIXTURE_MANIFEST.json", f"backend/scripts/generate_generic_tier_a_fixtures.py @ {M} "
                                     "(candidate d63d6fd4, product commit d3817d5f), 0 model calls", A),
    ("inputs/fixtures/*", f"backend/scripts/generate_generic_tier_a_fixtures.py @ {M}, 0 model calls", A),
    ("results/BROWSER_EVIDENCE.json", SUITE, A),
    ("results/OCCLUSION_MEASUREMENT.json", f"backend/scripts/measure_scene3d_occlusion.py --declared-camera-change "
                                           f"--pending-human-review @ {M} (full command in diagnostics/logs/OCCLUSION_{M}.log)", A),
    ("results/PLAYBACK_EVIDENCE.json", PLAYBACK, A),
    ("results/HIDDEN_EDGE_CROPS.json", BUILDER, A),
    ("images/*/playback/*", PLAYBACK, A),
    ("images/*/hidden-edges/*", BUILDER, A), ("images/*/SHEET.png", BUILDER, A),
    ("images/*/FILMSTRIP.png", BUILDER, A), ("images/overview/*", BUILDER, A),
    ("images/*", SUITE, A),
    (INTER + "NOTE.md", "hand-written provenance note", R),
    (INTER + "logs/*_ATTEMPT1_INTERRUPTED.log", "browser suite attempt 1 @ c5592c1a, killed by a session end after two "
                                                "families (both PASS); no evidence written", F),
    (INTER + "*", "complete acceptance measurement @ c5592c1a on the intermediate candidate d4a24eba (evidence f07b0d24; "
                  "images at f07b0d24), superseded by the final-review fix and the re-measurement on d63d6fd4", S),
    (FINAL1 + "NOTE.md", "hand-written provenance note", R),
    (FINAL1 + "diag-cube-mobile/*.mjs", "hand-written scratch patch of the diagnostic runs (never applied to the "
                                        "repository's suite)", R),
    (FINAL1 + "diag-cube-mobile/*", "scratch-PATCHED suite (cube/mobile filter + 40-capture series, or the forced "
                                    "frame-difference path) @ 83f101e4 — cause proof only, never acceptance evidence", D),
    (FINAL1 + "*", "compiler-scene-replay.mjs --suite @ 83f101e4 (attempt 1 on the final candidate: cube/mobile "
                   "causal_restore red, a harness defect fixed in 4e07548e)", F),
    ("diagnostics/browser-t7-round1-4d9eacfb/NOTE.md", "hand-written provenance note", R),
    ("diagnostics/browser-t7-round1-4d9eacfb/*", "compiler-scene-replay.mjs --suite on the scratch worktree @ 4d9eacfb "
                                                 "(Task 7 round 1: 6/6 red, classified, fixed in 2c7d4134/ca6c4107/240ecba5)", D),
    ("diagnostics/browser-t7-round2-239efc05/NOTE.md", "hand-written provenance note", R),
    ("diagnostics/browser-t7-round2-239efc05/*", "compiler-scene-replay.mjs --suite on the scratch worktree @ 239efc05 "
                                                 "(Task 7 confirm round: 5/6, fixed in 240ecba5)", D),
    ("diagnostics/browser-t7-diag-cuboid-mobile-4d9eacfb/NOTE.md", "hand-written provenance note", R),
    ("diagnostics/browser-t7-diag-cuboid-mobile-4d9eacfb/*", "scratch-PATCHED suite (cuboid/mobile filter + frame dumps) "
                                                             "@ 4d9eacfb — cause proof only, never acceptance evidence", D),
    ("diagnostics/w17_gates.sh", "hand-written identity-gate script (produced diagnostics/logs/GATES_*.log)", R),
    ("diagnostics/*.py", SCRIPT, R), ("diagnostics/*.mjs", SCRIPT, R),
    ("diagnostics/assumption_corpus_w17/*.py", SCRIPT, R),
    ("diagnostics/assumption_corpus_w17/LABELS.json", "hand labels, committed in Task 0 (bce0b7bb) before the fixes they judge", R),
    ("diagnostics/assumption_corpus_w17/CORPUS.json", "build_corpus.py of the same folder @ d4ca6ea9, 0 model calls", R),
    ("diagnostics/assumption_corpus_w17c/*.py", SCRIPT, R),
    ("diagnostics/assumption_corpus_w17c/LABELS.json", "hand labels of the W17C addendum (final review), committed with "
                                                       "the red tests in 01b0c27c before the fix they judge", R),
    ("diagnostics/assumption_corpus_w17c/CORPUS.json", "build_corpus.py of the same folder, committed in 3cbe3a1f, "
                                                       "0 model calls", R),
    ("diagnostics/OPERATION_BINDING_REPRODUCTION_*.json", "diagnostics/reproduce_operation_binding.py @ bce0b7bb + RED tests "
                                                          "(reproduction before any fix)", D),
    ("diagnostics/NEGATIVE_FIXTURE_RECONCILIATION_*.json", "diagnostics/reconcile_negative_fixtures.py @ 0b71502b, "
                                                           "0 model calls", A),
    ("diagnostics/ASSUMPTION_CENSUS_W17.json", "diagnostics/assumption_census_w17.py @ d4ca6ea9 (round 1), 0 model calls", S),
    ("diagnostics/ASSUMPTION_MECHANISM_DECISION_W17.json", "diagnostics/assumption_census_w17.py @ d4ca6ea9 (round 1)", S),
    ("diagnostics/ASSUMPTION_CENSUS_W17_R2.json", "diagnostics/assumption_census_w17.py 2 @ d3817d5f (round 2), "
                                                  "0 model calls", A),
    ("diagnostics/ASSUMPTION_MECHANISM_DECISION_W17_R2.json", "diagnostics/assumption_census_w17.py 2 @ d3817d5f (round 2)", A),
    ("diagnostics/PROOF_CACHE_ROW_W17.json", "diagnostics/proof_cache_row_w17.py (before: worktree at dd6e86b0; W17: main "
                                             "tree at d4ca6ea9, product code of dbb38b95), 0 model calls", A),
    ("diagnostics/PONYTAIL_REVIEW_W17.json", "ponytail:ponytail-review of the W17 code diff, run BEFORE freeze 1; "
                                             "seven findings applied in add4afb0", R),
    ("diagnostics/MEASUREMENT_ATTEMPTS.json", "hand-written record of every run of the wave", R),
    ("diagnostics/WORKTREE_CLEANUP.json", "hand-written record of the removed worktrees (two cleanups)", R),
    ("diagnostics/TEMP_FILE_INVENTORY.json", "inventory of temp files (D:/tmp, session scratchpad, plan workspace)", R),
    ("diagnostics/logs/NPM_CI_SPACED_83f101e4.log", "npm ci --offline of the spaced worktree @ 83f101e4, reused at "
                                                    f"{M} (package files unchanged) for T3 and the gates", A),
    ("diagnostics/logs/*_83f101e4.log", "captured command output of attempt 1 on the final candidate @ 83f101e4", F),
    (f"diagnostics/logs/*_{M}.log", f"captured command output at the measurement commit {M}", A),
    ("diagnostics/logs/FAULT_INJECTION_W17_R3.log", "diagnostics/run_fault_injections_w17.py _R3 @ 6d52ab2f + working tree", A),
    ("diagnostics/logs/FAULT_INJECTION_W17_FRONTEND_R3.log", "diagnostics/run_fault_injections_w17_frontend.mjs _R3 on a "
                                                             f"detached worktree at {M}", A),
    ("diagnostics/logs/FAULT_INJECTION_W17_R2.log", "diagnostics/run_fault_injections_w17.py _R2 @ 239efc05 (20/20; before "
                                                    "the final-review fix)", S),
    ("diagnostics/logs/FAULT_INJECTION_W17_FRONTEND_R2.log", "diagnostics/run_fault_injections_w17_frontend.mjs _R2 on a "
                                                             "detached worktree at dbb38b95 (15/15)", S),
    ("diagnostics/logs/FAULT_INJECTION_W17.log", "diagnostics/run_fault_injections_w17.py @ 4d9eacfb (19/20; FM2 gap, "
                                                 "test added in ae279e8e)", S),
    ("diagnostics/logs/FAULT_INJECTION_W17_FRONTEND.log", "diagnostics/run_fault_injections_w17_frontend.mjs @ 240ecba5 "
                                                          "(13/15; FE3 and FB1 gaps closed in dbb38b95)", S),
    ("diagnostics/logs/PHASE0_REPOSITORY_GATE.log", "Phase 0 repository gate @ dd6e86b0 (main tree)", A),
    ("diagnostics/logs/RECONCILE_NEGATIVE_FIXTURES.log", "diagnostics/reconcile_negative_fixtures.py @ 0b71502b", A),
    ("diagnostics/logs/PRE_FREEZE_*", "pre-freeze full backend runs in the main tree at fadfd10e (superseded), add4afb0 and "
                                      "after the final-review fix (whitespace-only lines emptied; "
                                      "diagnostics/MEASUREMENT_ATTEMPTS.json)", D),
    ("diagnostics/logs/RED_CAUSAL_RESTORE_NOISE.log", "RED check of the restore-tolerance node test against the harness of "
                                                      "83f101e4 (scratch worktree)", D),
    ("diagnostics/logs/RED_*", "RED check of the Task 1 tests before any fix", D),
    ("diagnostics/logs/*", "captured command output (command and commit at the top of the log or in its name)", D),
]


def _rule(rel: str) -> tuple[str, str]:
    for pattern, producer, status in RULES:
        if fnmatch.fnmatch(rel, pattern):
            return producer, status
    raise SystemExit(f"no producer rule for {rel}")


def _entry(p: Path) -> dict:
    data = p.read_bytes()
    text = p.suffix.lower() in TEXT
    if text:
        data = data.replace(b"\r\n", b"\n")
    producer, status = _rule(p.relative_to(RUN).as_posix())
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "sha256_basis": "git_blob_lf" if text else "raw_bytes",
            "producer": producer, "measurement_status": status}


def main() -> None:
    files = sorted(p for p in RUN.rglob("*") if p.is_file() and p != OUT and "__pycache__" not in p.parts)
    OUT.write_text(json.dumps({
        "schema_version": "run-manifest/3",
        "run_id": RUN.name,
        "sha256_basis_values": {"raw_bytes": "sha256 of the file bytes (binary files)",
                                "git_blob_lf": "sha256 of the LF-normalised content = the committed git blob"},
        "measurement_status_values": {
            A: f"the evidence of this run: measured at {M} on the final candidate d63d6fd4, or the final "
               "census/fault-injection/cache proof",
            S: "replaced by a later run of the same kind in this wave; valid for the commit or candidate it names",
            F: "failed attempt kept apart from acceptance images (diagnostics/MEASUREMENT_ATTEMPTS.json)",
            D: "investigation output, not acceptance evidence",
            R: "hand-written record, decision, registration input or script",
        },
        "files": {p.relative_to(RUN).as_posix(): _entry(p) for p in files},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(OUT.name, len(files))


if __name__ == "__main__":
    main()
