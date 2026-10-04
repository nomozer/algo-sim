# -*- coding: utf-8 -*-
"""W19 — MANIFEST.json of this run: every file with sha256, its basis, its producer and its status (same shape as the
w18 run's `diagnostics/build_manifest.py`, schema run-manifest/3).

Basis: `git_blob_lf` for text (LF-normalised content = the committed blob under core.autocrlf), `raw_bytes` otherwise.
Producer and status come from the first matching rule; a file no rule names stops the build, so nothing is listed
with an invented producer. The manifest never records the SHA of the commit that contains it. Overwrites
MANIFEST.json (derived, not evidence). Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w19-docs-organization/diagnostics/build_manifest.py
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "MANIFEST.json"
TEXT = {".json", ".md", ".log", ".txt", ".py"}
D = "diagnostics/"
A, S, R = "AUTHORITATIVE", "SUPERSEDED", "RECORD"
RULES = [  # (pattern, producer, status) — first match wins
    ("README.md", "hand-written run document", R), ("REPORT.md", "hand-written run document", R),
    ("HANDOFF.md", "hand-written run document", R), ("RUN.json", "hand-written run document", R),
    ("inputs/W19_SCOPE_DECISIONS.json", "hand-written scope decisions (brief invariants, rulings R1-R12, skills)", R),
    ("inventory/INVENTORY.json", D + "inventory_docs.py --base 6d0e6321 (read-only, tree equal to the base)", A),
    ("inventory/MIGRATION_MAP.json", D + "rewrite_doc_paths.py --map (blobs from git hash-object after the moves)", A),
    ("inventory/REWRITE_LOG.json", D + "rewrite_doc_paths.py (pass 1: MOVE/ARCHIVE pairs), applied in a5c2e6f2", A),
    ("inventory/REWRITE_LOG_MERGE.json", D + "rewrite_doc_paths.py --only-merge (pass 2), applied in a44631a9", A),
    ("inventory/AUTHORITY_RETARGET.json", "hand-checked replacement list (each matched exactly once before writing)", A),
    ("verification/LINKS_BEFORE.json", D + "check_doc_links.py at 6d0e6321 (before any move)", A),
    ("verification/LINKS_AFTER_TASK2.json", D + "check_doc_links.py after the moves (commit a5c2e6f2)", S),
    ("verification/LINKS_AFTER_TASK3.json", D + "check_doc_links.py after the claim map and hubs (commit a44631a9)", S),
    ("verification/LINKS_FINAL.json", D + "check_doc_links.py on the final tree", A),
    ("verification/OLD_PATH_CONSUMERS_TASK2.json", D + "check_old_path_consumers.py after the moves", S),
    ("verification/OLD_PATH_CONSUMERS_TASK3.json", D + "check_old_path_consumers.py after the merge pass", S),
    ("verification/OLD_PATH_CONSUMERS_FINAL.json", D + "check_old_path_consumers.py on the final tree", A),
    ("verification/FROZEN_IDENTITY.json", D + "verify_frozen_identity.py --base 6d0e6321 (index of the final tree)", A),
    ("verification/DOCS_TREE_BEFORE_AFTER.txt", "git ls-tree 6d0e6321 / git ls-files, files per folder (shell, read-only)", A),
    ("verification/logs/*", "command output, header line names the command and the tree it ran on", A),
    (D + "*.py", "hand-written W19 script (0 model calls)", R),
    (D + "TEMP_FILE_INVENTORY.json", "hand-written temp-file inventory", R),
    (D + "PONYTAIL_REVIEW_W19.md", "ponytail-review of the W19 diff (hand-written)", R),
]


def main() -> int:
    files = {}
    for p in sorted(x for x in RUN.rglob("*") if x.is_file() and x != OUT and "__pycache__" not in x.parts):
        rel = p.relative_to(RUN).as_posix()
        rule = next((r for r in RULES if fnmatch.fnmatch(rel, r[0])), None)
        if rule is None:
            raise SystemExit(f"no producer rule for {rel}")
        data = p.read_bytes()
        text = p.suffix.lower() in TEXT
        if text:
            data = data.replace(b"\r\n", b"\n")
        files[rel] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                      "sha256_basis": "git_blob_lf" if text else "raw_bytes", "producer": rule[1],
                      "measurement_status": rule[2]}
    doc = {"schema_version": "run-manifest/3", "run_id": RUN.name,
           "sha256_basis_values": {"raw_bytes": "sha256 of the file bytes",
                                   "git_blob_lf": "sha256 of the LF-normalised content = the committed git blob"},
           "measurement_status_values": {
               "AUTHORITATIVE": "the evidence of this run on the final tree (or the base, where the file says so)",
               "SUPERSEDED": "an intermediate run of the same check in this wave; valid for the commit it names",
               "RECORD": "hand-written record, decision or script"},
           "files": files}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"MANIFEST.json: {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
