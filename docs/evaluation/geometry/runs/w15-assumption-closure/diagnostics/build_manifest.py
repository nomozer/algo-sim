# -*- coding: utf-8 -*-
"""W15 Task 11 — MANIFEST.json of this run: every file with sha256, its basis, its producer and
its measurement status.

Basis per file: `raw_bytes` for binary files (PNG); `git_blob_lf` for text, i.e. the
LF-normalised content, which equals the committed blob under `core.autocrlf`.
Producer and status come from the first matching rule below; a file no rule names stops
the build, so nothing is listed with an invented producer. The manifest never records the
SHA of the commit that contains it. Overwrites MANIFEST.json (it is derived, not evidence).
Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/build_manifest.py
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "MANIFEST.json"
M = "c57ebd1b"
TEXT = {".json", ".md", ".log", ".txt", ".tsv", ".py", ".mjs", ".sh"}
SUITE = f"frontend/scripts/compiler-scene-replay.mjs --suite @ {M}"
BUILDER = f"backend/scripts/build_scene3d_visual_evidence.py @ {M}"
PLAYBACK = f"frontend/scripts/scene3d-playback-check.mjs --theo-ho --lap-orbit 5 @ {M}"
SCRIPT = "hand-written W15 diagnostic script (0 model calls)"
A, S, F, D, R = "AUTHORITATIVE", "SUPERSEDED", "FAILED_ATTEMPT_KEPT_APART", "DIAGNOSTIC", "RECORD"
RULES = [  # (pattern, producer, measurement status) — first match wins
    ("README.md", "hand-written run document", R), ("REPORT.md", "hand-written run document", R),
    ("HANDOFF.md", "hand-written run document", R), ("RUN.json", "hand-written run document", R),
    ("inputs/W15_SCOPE_DECISIONS.json", "hand-written record of the brief's D1-D3 and the user's verbatim answers U1-U5", R),
    ("inputs/CANDIDATE_DIVERGENCE_CORRECTION.json", "hand-written candidate divergence declaration (three freezes)", R),
    ("inputs/FIXTURE_MANIFEST.json", f"backend/scripts/generate_generic_tier_a_fixtures.py @ {M} "
                                     "(candidate b3b7eb79, product commit 41a26f11), 0 model calls", A),
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
    ("diagnostics/browser-attempt1-c1638891/*", "frontend/scripts/compiler-scene-replay.mjs --suite @ c1638891 "
                                                "(BROWSER-1, failed: section fill never drawn)", F),
    ("diagnostics/w15_gates.sh", "hand-written identity-gate script (produced diagnostics/logs/GATES_*.log)", R),
    ("diagnostics/*.py", SCRIPT, R), ("diagnostics/assumption_corpus_w15*/*.py", SCRIPT, R),
    ("diagnostics/assumption_corpus_w15*/LABELS.json", "hand labels, committed before the mechanism they judge ran", R),
    ("diagnostics/assumption_corpus_w15*/CORPUS.json", "build_corpus.py of the same folder, 0 model calls", R),
    ("diagnostics/w14_census_reproduction/*", "W14 assumption_census.py rerun on the W14 corpus (Task 1 reproduction)", D),
    ("diagnostics/TRACK_B_ROOT_CAUSE_TABLE.*", "diagnostics/track_b_table.py, 0 model calls", D),
    ("diagnostics/GOLD_ROW_VERIFICATION.json", "diagnostics/gold_row_verification.py (independent oracle + hand derivations)", D),
    ("diagnostics/ASSUMPTION_CENSUS_W15_R3.json", "diagnostics/assumption_census_w15_r2.py 3 @ 41a26f11, 0 model calls", A),
    ("diagnostics/ASSUMPTION_MECHANISM_DECISION_W15_R3.json", "diagnostics/assumption_census_w15_r2.py 3 (registered SHIP rule §9)", A),
    ("diagnostics/ASSUMPTION_CENSUS_W15_R2.json", "diagnostics/assumption_census_w15_r2.py @ fbabbc2e", S),
    ("diagnostics/ASSUMPTION_MECHANISM_DECISION_W15_R2.json", "diagnostics/assumption_census_w15_r2.py @ fbabbc2e", S),
    ("diagnostics/ASSUMPTION_CENSUS_W15.json", "diagnostics/assumption_census_w15.py @ cf57332b (gate not wired)", S),
    ("diagnostics/ASSUMPTION_MECHANISM_DECISION_W15.json", "diagnostics/assumption_census_w15.py @ cf57332b", S),
    ("diagnostics/PROOF_CACHE_ROW_W15.json", "diagnostics/proof_cache_row_w15.py (pre-W15 worktree at 4f6a0ab6 vs W15), 0 model calls", A),
    ("diagnostics/PONYTAIL_REVIEW.json", "ponytail:ponytail-review on 4f6a0ab6..0579d559 + hand classification", R),
    ("diagnostics/MEASUREMENT_ATTEMPTS.json", "hand-written record of every run of the wave", R),
    ("diagnostics/WORKTREE_CLEANUP.json", "hand-written record of the removed worktrees", R),
    ("diagnostics/TEMP_FILE_INVENTORY.json", "inventory of temp files (generator kept in the session scratchpad)", R),
    ("diagnostics/logs/*_c57ebd1b.log", f"captured command output at the measurement commit {M}", A),
    ("diagnostics/logs/FAULT_INJECTION_ASSUMPTION_GATE_FINAL.log", "diagnostics/run_fault_injections_w15.py _FINAL @ 41a26f11", A),
    ("diagnostics/logs/CENSUS_W15_R3.log", "assumption_census_w15_r2.py 3 @ 41a26f11", A),
    ("diagnostics/logs/PRE_FREEZE_3_FULL.log", "full backend suite in the main tree at bb0740f7", A),
    ("diagnostics/logs/*_e5b88647.log", "captured command output at e5b88647 (M2, superseded by the final-review fix)", S),
    ("diagnostics/logs/DRY_SUITE_*.log", "diagnostic dry run with the section-fill patch (outputs not kept)", D),
    ("diagnostics/logs/*_c1638891.log", "captured command output at c1638891 (BROWSER-1 attempt)", F),
    ("diagnostics/logs/FAULT_INJECTION_ASSUMPTION_GATE*.log", "diagnostics/run_fault_injections_w15.py at an earlier commit (named in the log)", S),
    ("diagnostics/logs/CENSUS_W15*.log", "census console output at an earlier round", S),
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
            A: f"the evidence of this run: measured at {M} on candidate b3b7eb79, or the final census/fault-injection/cache proof",
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
