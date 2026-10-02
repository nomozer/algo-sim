# -*- coding: utf-8 -*-
"""W14 Task 12 — MANIFEST.json of this run: every file with sha256, its basis and its producer.

Basis per file: `raw_bytes` for binary files (PNG); `git_blob_lf` for text, i.e. the
LF-normalised content, which equals the committed blob under `core.autocrlf`.
The producer comes from the first matching rule below; a file no rule names stops
the build, so nothing is listed with an invented producer. Overwrites MANIFEST.json
(it is derived, not evidence). Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/build_manifest.py
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "MANIFEST.json"
M = "380db58c"
TEXT = {".json", ".md", ".log", ".txt", ".tsv", ".py", ".mjs"}
SUITE = f"frontend/scripts/compiler-scene-replay.mjs --suite @ {M}"
BUILDER = f"backend/scripts/build_scene3d_visual_evidence.py @ {M}"
PLAYBACK = f"frontend/scripts/scene3d-playback-check.mjs --theo-ho --lap-orbit 5 @ {M}"
SCRIPT = "hand-written W14 diagnostic script (0 model calls)"
RULES = [
    ("README.md", "hand-written run document"), ("REPORT.md", "hand-written run document"),
    ("HANDOFF.md", "hand-written run document"), ("RUN.json", "hand-written run document"),
    ("inputs/W14_SCOPE_DECISIONS.json", "hand-written record of the user's recorded answers (Task 0)"),
    ("inputs/CANDIDATE_DIVERGENCE_CORRECTION.json", "hand-written candidate divergence declaration (Task 10)"),
    ("inputs/FIXTURE_MANIFEST.json", f"backend/scripts/generate_generic_tier_a_fixtures.py @ {M} "
                                     "(candidate 40263983, product commit a2af56e4), 0 model calls"),
    ("inputs/fixtures/*", f"backend/scripts/generate_generic_tier_a_fixtures.py @ {M}, 0 model calls"),
    ("results/BROWSER_EVIDENCE.json", SUITE),
    ("results/OCCLUSION_MEASUREMENT.json", f"backend/scripts/measure_scene3d_occlusion.py "
                                           f"--declared-camera-change @ {M} (full command in "
                                           f"diagnostics/logs/OCCLUSION_{M}.log)"),
    ("results/PLAYBACK_EVIDENCE.json", PLAYBACK),
    ("results/HIDDEN_EDGE_CROPS.json", BUILDER),
    ("images/*/playback/*", PLAYBACK),
    ("images/*/hidden-edges/*", BUILDER), ("images/*/SHEET.png", BUILDER),
    ("images/*/FILMSTRIP.png", BUILDER), ("images/overview/*", BUILDER),
    ("images/*", SUITE),
    ("diagnostics/*.py", SCRIPT), ("diagnostics/assumption_corpus/*.py", SCRIPT),
    ("diagnostics/assumption_corpus/LABELS.json", "hand labels, committed before any mechanism ran (Task 5 Step 2)"),
    ("diagnostics/assumption_corpus/CORPUS.json", "diagnostics/assumption_corpus/build_corpus.py, 0 model calls"),
    ("diagnostics/S4_INVENTORY*.json", "diagnostics/s4_inventory.py, 0 model calls"),
    ("diagnostics/W14_SCENE_HASH_RECONCILIATION.json", "diagnostics/scene_hash_reconciliation.py"),
    ("diagnostics/TRUST_POLICY_CALLERS.json", "diagnostics/trust_policy_callers.py + per-caller classification"),
    ("diagnostics/ASSUMPTION_CENSUS.json", "diagnostics/assumption_census.py, 0 model calls"),
    ("diagnostics/ASSUMPTION_MECHANISM_DECISION.json", "diagnostics/assumption_census.py (pre-registered rule)"),
    ("diagnostics/PROOF_CACHE_ROW_W14.json", "diagnostics/proof_cache_row_w14.py (temp SQLite DB, 0 model calls)"),
    ("diagnostics/SOURCE_GROUNDING_PHRASING_PROBE_W14.json",
     "docs/evaluation/geometry/runs/w13-geometry-preregistration/diagnostics/source_grounding_probe.py, 0 model calls"),
    ("diagnostics/SECTION_SUBSTEPS_W12_W14.json", "diagnostics/section_substeps_compare.py"),
    ("diagnostics/OCCLUSION_TRANSFER_DIAGNOSTIC.json", "diagnostics/occlusion_transfer_diagnostic.py"),
    ("diagnostics/W13_LEFTOVER_INVENTORY.json", "Task 0 inventory: git hash-object of every file vs the blob at 7202befe"),
    ("diagnostics/logs/*", "captured command output (command and commit at the top of the log or in its name)"),
    ("diagnostics/*.json", "hand-written W14 record"), ("diagnostics/*.md", "hand-written W14 record"),
]


def _producer(rel: str) -> str:
    for pattern, producer in RULES:
        if fnmatch.fnmatch(rel, pattern):
            return producer
    raise SystemExit(f"no producer rule for {rel}")


def _entry(p: Path) -> dict:
    data = p.read_bytes()
    text = p.suffix.lower() in TEXT
    if text:
        data = data.replace(b"\r\n", b"\n")
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "sha256_basis": "git_blob_lf" if text else "raw_bytes",
            "producer": _producer(p.relative_to(RUN).as_posix())}


def main() -> None:
    files = sorted(p for p in RUN.rglob("*") if p.is_file() and p != OUT and "__pycache__" not in p.parts)
    OUT.write_text(json.dumps({
        "schema_version": "run-manifest/2",
        "run_id": RUN.name,
        "sha256_basis_values": {"raw_bytes": "sha256 of the file bytes (binary files)",
                                "git_blob_lf": "sha256 of the LF-normalised content = the committed git blob"},
        "files": {p.relative_to(RUN).as_posix(): _entry(p) for p in files},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(OUT.name, len(files))


if __name__ == "__main__":
    main()
