# -*- coding: utf-8 -*-
"""W16 — MANIFEST.json of this run: every file with sha256, its basis, its producer and its
measurement status (same shape as w15's `diagnostics/build_manifest.py`).

Basis per file: `raw_bytes` for binary files (PNG); `git_blob_lf` for text, i.e. the
LF-normalised content, which equals the committed blob under `core.autocrlf`.
Producer and status come from the first matching rule below; a file no rule names stops
the build, so nothing is listed with an invented producer. The manifest never records the
SHA of the commit that contains it. Overwrites MANIFEST.json (it is derived, not evidence).
Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w16-premerge-closure/diagnostics/build_manifest.py
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "MANIFEST.json"
M = "7f3658b0"
TEXT = {".json", ".md", ".log", ".txt", ".tsv", ".py", ".mjs", ".sh"}
SUITE = f"frontend/scripts/compiler-scene-replay.mjs --suite @ {M}"
BUILDER = f"backend/scripts/build_scene3d_visual_evidence.py @ {M}"
PLAYBACK = f"frontend/scripts/scene3d-playback-check.mjs --theo-ho --lap-orbit 5 @ {M}"
SCRIPT = "hand-written W16 diagnostic script (0 model calls)"
A, S, F, D, R = "AUTHORITATIVE", "SUPERSEDED", "FAILED_ATTEMPT_KEPT_APART", "DIAGNOSTIC", "RECORD"
RULES = [  # (pattern, producer, measurement status) — first match wins
    ("README.md", "hand-written run document", R), ("REPORT.md", "hand-written run document", R),
    ("HANDOFF.md", "hand-written run document", R), ("RUN.json", "hand-written run document", R),
    ("inputs/CANDIDATE_DIVERGENCE_CORRECTION.json", "hand-written candidate divergence declaration (two freezes)", R),
    ("inputs/FIXTURE_MANIFEST.json", f"backend/scripts/generate_generic_tier_a_fixtures.py @ {M} "
                                     "(candidate 9bb0aaa7, product commit 6b120036), 0 model calls", A),
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
    ("diagnostics/browser-attempt1-55cde06e/*", "frontend/scripts/compiler-scene-replay.mjs --suite @ 55cde06e "
                                                "(attempt 1, failed: page code redeclared doc, 0 section-fill samples)", F),
    ("diagnostics/w16_gates.sh", "hand-written identity-gate script (produced diagnostics/logs/GATES_*.log)", R),
    ("diagnostics/*.py", SCRIPT, R), ("diagnostics/*.mjs", SCRIPT, R),
    ("diagnostics/assumption_corpus_w16*/*.py", SCRIPT, R),
    ("diagnostics/assumption_corpus_w16*/LABELS.json", "hand labels, committed before the fix they judge", R),
    ("diagnostics/assumption_corpus_w16/CORPUS.json", "build_corpus.py of the same folder @ 6d015112, 0 model calls", R),
    ("diagnostics/assumption_corpus_w16b/CORPUS.json", "build_corpus.py of the same folder @ 2dc55f1b, 0 model calls", R),
    ("diagnostics/PROBE_W16_PHASE1_*.json", "diagnostics/probe_w16_phase1.py @ 6d015112 (reproduction before any fix)", D),
    ("diagnostics/ASSUMPTION_CENSUS_W16_R2.json", "diagnostics/assumption_census_w16.py 2 @ 7695b967, 0 model calls", A),
    ("diagnostics/ASSUMPTION_MECHANISM_DECISION_W16_R2.json", "diagnostics/assumption_census_w16.py 2 @ 7695b967", A),
    ("diagnostics/ASSUMPTION_CENSUS_W16.json", "diagnostics/assumption_census_w16.py @ 00f0981d (before the primed-name fix)", S),
    ("diagnostics/ASSUMPTION_MECHANISM_DECISION_W16.json", "diagnostics/assumption_census_w16.py @ 00f0981d", S),
    ("diagnostics/PROOF_CACHE_ROW_W16.json", "diagnostics/proof_cache_row_w16.py (before: worktree at 8a339d17; W16: main "
                                             "tree at cd3a0efa, product code of 93d4ec69), 0 model calls", A),
    ("diagnostics/PONYTAIL_REVIEW.json", "ponytail:ponytail-review of the W16 code diff, run after the evidence; "
                                         "no finding applied", R),
    ("diagnostics/MEASUREMENT_ATTEMPTS.json", "hand-written record of every run of the wave", R),
    ("diagnostics/WORKTREE_CLEANUP.json", "hand-written record of the removed worktrees", R),
    ("diagnostics/TEMP_FILE_INVENTORY.json", "inventory of temp files (session scratchpad and plan workspace)", R),
    ("diagnostics/logs/*_7f3658b0.log", f"captured command output at the measurement commit {M}", A),
    ("diagnostics/logs/FAULT_INJECTION_W16_FINAL.log", "diagnostics/run_fault_injections_w16.py _FINAL @ 7695b967", A),
    ("diagnostics/logs/FAULT_INJECTION_W16_FRONTEND.log", "diagnostics/run_fault_injections_w16_frontend.mjs on a "
                                                          "detached worktree at cd3a0efa (renderer and harness unchanged since)", A),
    ("diagnostics/logs/FAULT_INJECTION_W16_FRONTEND_ATTEMPT1_FH1_STALE_CRLF.log", "frontend fault injections, attempt 1 "
                                                                                  "(FH1 STALE on a CRLF checkout)", F),
    ("diagnostics/logs/CENSUS_W16_R2.log", "assumption_census_w16.py 2 @ 7695b967", A),
    ("diagnostics/logs/FAULT_INJECTION_W16.log", "diagnostics/run_fault_injections_w16.py @ 00f0981d (before FA3/FA4)", S),
    ("diagnostics/logs/CENSUS_W16.log", "assumption_census_w16.py @ 00f0981d (round 1)", S),
    ("diagnostics/logs/DRY_SUITE_cross_section_55cde06e.log", "compiler-scene-replay.mjs --suite with a one-family "
                                                              "manifest @ 55cde06e (rejected: INVALID_SUITE_MANIFEST; "
                                                              "no measurement)", D),
    ("diagnostics/logs/PRE_FREEZE_*", "pre-freeze check at cd3a0efa: backend in the main tree, frontend in the worktree "
                                      "D:/tmp/w16-fe (diagnostics/MEASUREMENT_ATTEMPTS.json)", D),
    ("diagnostics/logs/*_55cde06e.log", "captured command output at 55cde06e (attempt 1, superseded by the second freeze)", F),
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
            A: f"the evidence of this run: measured at {M} on candidate 9bb0aaa7, or the final census/fault-injection/cache proof",
            S: "replaced by a later run of the same kind in this wave; valid for the commit it names",
            F: "failed attempt kept apart from acceptance images (diagnostics/MEASUREMENT_ATTEMPTS.json)",
            D: "investigation output, not acceptance evidence",
            R: "hand-written record, decision, registration input or script",
        },
        "files": {p.relative_to(RUN).as_posix(): _entry(p) for p in files},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(OUT.name, len(files))


if __name__ == "__main__":
    main()
