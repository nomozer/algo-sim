# -*- coding: utf-8 -*-
"""W18 — MANIFEST.json of this run: every file with sha256, its basis, its producer and its
measurement status (same shape as w17's `diagnostics/build_manifest.py`).

Basis per file: `raw_bytes` for binary files (PNG); `git_blob_lf` for text, i.e. the
LF-normalised content, which equals the committed blob under `core.autocrlf`.
Producer and status come from the first matching rule below; a file no rule names stops
the build, so nothing is listed with an invented producer. The manifest never records the
SHA of the commit that contains it. Overwrites MANIFEST.json (it is derived, not evidence).
Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w18-binding-focus/diagnostics/build_manifest.py
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "MANIFEST.json"
M = "0ca3accf"
TEXT = {".json", ".md", ".log", ".txt", ".tsv", ".py", ".mjs", ".sh"}
SUITE = f"frontend/scripts/compiler-scene-replay.mjs --suite @ {M} (attempt 2 on the final candidate d3b4cab9)"
BUILDER = f"backend/scripts/build_scene3d_visual_evidence.py @ {M}"
PLAYBACK = f"frontend/scripts/scene3d-playback-check.mjs --theo-ho --lap-orbit 5 @ {M}"
SCRIPT = "hand-written W18 diagnostic script (0 model calls)"
ATT1 = "diagnostics/evidence-attempt1-8caa8307/"
A, S, D, R = "AUTHORITATIVE", "SUPERSEDED", "DIAGNOSTIC", "RECORD"
RULES = [  # (pattern, producer, measurement status) — first match wins
    ("README.md", "hand-written run document", R), ("REPORT.md", "hand-written run document", R),
    ("HANDOFF.md", "hand-written run document", R), ("RUN.json", "hand-written run document", R),
    ("inputs/CANDIDATE_DIVERGENCE_CORRECTION.json", "hand-written candidate divergence declaration (one freeze)", R),
    ("inputs/FIXTURE_MANIFEST.json", f"backend/scripts/generate_generic_tier_a_fixtures.py @ {M} "
                                     "(candidate d3b4cab9, product commit 7a06ee47), 0 model calls", A),
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
    (ATT1 + "NOTE.md", "hand-written provenance note", R),
    (ATT1 + "*", "complete acceptance measurement @ 8caa8307 on the final candidate d3b4cab9 (every gate passed), "
                 "superseded because the frontend fault injections run 1 found three browser-harness blind spots "
                 "(fixed in 1d8dfc6f); images never committed, reproducible from 8caa8307", S),
    ("diagnostics/browser-prefreeze-round1-91f750e6/NOTE.md", "hand-written provenance note", R),
    ("diagnostics/browser-prefreeze-round1-91f750e6/*", "compiler-scene-replay.mjs --suite on the scratch worktree @ "
                                                         "91f750e6 (pre-freeze round 1: cuboid red, a harness oracle that "
                                                         "ignored same_as, fixed in 32f10f69)", D),
    ("diagnostics/browser-prefreeze-round2-32f10f69/NOTE.md", "hand-written provenance note", R),
    ("diagnostics/browser-prefreeze-round2-32f10f69/*", "compiler-scene-replay.mjs --suite on the scratch worktree @ "
                                                         "32f10f69 (pre-freeze confirm round: 6/6)", D),
    ("diagnostics/w18_gates.sh", "hand-written identity-gate script (produced diagnostics/logs/GATES_*.log)", R),
    ("diagnostics/build_manifest.py", "hand-written manifest builder (this file)", R),
    ("diagnostics/*.py", SCRIPT, R), ("diagnostics/*.mjs", SCRIPT, R),
    ("diagnostics/construction_corpus_w18/*.py", SCRIPT, R),
    ("diagnostics/construction_corpus_w18/LABELS.json", "hand labels, committed in Task 0 (c479f377) before the fix "
                                                        "they judge", R),
    ("diagnostics/construction_corpus_w18/CORPUS.json", "build_corpus.py of the same folder, 0 model calls", R),
    ("diagnostics/CONSTRUCTION_BINDING_REPRODUCTION_f3edd903.json", "diagnostics/reproduce_construction_binding.py @ "
                                                                    "f3edd903 (two outside-scope rows never reached the "
                                                                    "route; amended in bb9f7004)", S),
    ("diagnostics/CONSTRUCTION_BINDING_REPRODUCTION_bb9f7004.json", "diagnostics/reproduce_construction_binding.py @ "
                                                                    "bb9f7004 (before any fix)", A),
    ("diagnostics/CONSTRUCTION_BINDING_REPRODUCTION_84ce7b70.json", "diagnostics/reproduce_construction_binding.py @ "
                                                                    "84ce7b70 (after the binding)", A),
    ("diagnostics/CONSTRUCTION_BINDING_CENSUS_W18.json", "diagnostics/construction_binding_census_w18.py @ 84ce7b70, "
                                                         "0 model calls", A),
    ("diagnostics/CONSTRUCTION_BINDING_DECISION_W18.json", "diagnostics/construction_binding_census_w18.py @ 84ce7b70", A),
    ("diagnostics/PROOF_CACHE_ROW_W18.json", "diagnostics/proof_cache_row_w18.py (before: envelopes of the W17 candidate; "
                                             "W18: the main tree before 1e8c5658), 0 model calls", A),
    ("diagnostics/PONYTAIL_REVIEW_W18.json", "ponytail:ponytail-review of the W18 code diff, run BEFORE the freeze; "
                                             "three cuts applied in 7a06ee47", R),
    ("diagnostics/MEASUREMENT_ATTEMPTS.json", "hand-written record of every run of the wave", R),
    ("diagnostics/WORKTREE_CLEANUP.json", "hand-written record of the removed worktrees", R),
    ("diagnostics/TEMP_FILE_INVENTORY.json", "inventory of temp files (D:/tmp, session scratchpad, plan workspace)", R),
    ("diagnostics/logs/NPM_CI_SPACED_*.log", "npm ci --offline of the spaced worktree @ 8caa8307, reused at "
                                             f"{M} (package files unchanged) for T3 and the gates", A),
    (f"diagnostics/logs/*_{M}.log", f"captured command output at the measurement commit {M}", A),
    ("diagnostics/logs/FAULT_INJECTION_W18_R3.log", "diagnostics/run_fault_injections_w18.py _R3 @ 8caa8307 (same product "
                                                    "code as the measurement commit)", A),
    ("diagnostics/logs/FAULT_INJECTION_W18_FRONTEND_R2.log", "diagnostics/run_fault_injections_w18_frontend.mjs _R2 on a "
                                                             f"detached worktree at {M}", A),
    ("diagnostics/logs/FAULT_INJECTION_W18_R2.log", "diagnostics/run_fault_injections_w18.py _R2 @ 83a0e0c1 + working tree "
                                                    "(12/12)", S),
    ("diagnostics/logs/FAULT_INJECTION_W18.log", "diagnostics/run_fault_injections_w18.py @ 256fdc8e + working tree "
                                                 "(11/12; FA4 guard strengthened in 83a0e0c1)", S),
    ("diagnostics/logs/FAULT_INJECTION_W18_FRONTEND.log", "diagnostics/run_fault_injections_w18_frontend.mjs @ 8caa8307 "
                                                          "(unit 8/8, browser 1/4: three harness blind spots fixed in "
                                                          "1d8dfc6f)", S),
    ("diagnostics/logs/PHASE0_REPOSITORY_GATE.log", "Phase 0 repository gate @ 0ec2bbbb (main tree)", A),
    ("diagnostics/logs/CENSUS_W18_84ce7b70.log", "census decision printout @ 84ce7b70", A),
    ("diagnostics/logs/PRE_FREEZE_*", "pre-freeze full backend run in the main tree at 7a06ee47 (16 failures classified "
                                      "in its header; diagnostics/MEASUREMENT_ATTEMPTS.json)", D),
    ("diagnostics/logs/RED_W18_HARNESS_FIX.log", "RED check of the two harness node tests of 1d8dfc6f against the "
                                                 "harness of 8caa8307", D),
    ("diagnostics/logs/RED_*", "RED check of the W18 tests before the fix they judge", D),
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
            A: f"the evidence of this run: measured at {M} on the final candidate d3b4cab9, or the final "
               "census/fault-injection/cache proof",
            S: "replaced by a later run of the same kind in this wave; valid for the commit or candidate it names",
            D: "investigation output, not acceptance evidence",
            R: "hand-written record, decision, registration input or script",
        },
        "files": {p.relative_to(RUN).as_posix(): _entry(p) for p in files},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(OUT.name, len(files))


if __name__ == "__main__":
    main()
