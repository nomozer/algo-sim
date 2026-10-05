# -*- coding: utf-8 -*-
"""cuboid-acceptance — MANIFEST.json of this run (shape of cuboid-final-review's build_manifest.py): every file with
sha256 of its LF-normalised content (= the committed blob under core.autocrlf), its producer and its status. A file no
rule names stops the build. The manifest never records the SHA of the commit that contains it. Run from the repository
root:  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/cuboid-acceptance/diagnostics/build_manifest_cacc.py
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "MANIFEST.json"
WT = "@ f93408b7 (clean detached worktree D:/tmp/cacc-verify)"
A, R = "AUTHORITATIVE", "RECORD"
RULES = [  # (pattern, producer, status) — first match wins
    ("REPORT.md", "hand-written run document", R), ("HANDOFF.md", "hand-written run document", R),
    ("RUN.json", "hand-written run document", R),
    ("results/INVARIANT_RECONCILIATION.json", "hand-written per-row reconciliation; checks in results/logs/", A),
    ("results/logs/DOCS_GATES_FINAL.log", f"diagnostics/cacc_gates.sh + diagnostics/split_scope_cacc.py {WT}", A),
    ("results/logs/INVARIANT_CHECKS_FINAL.log", f"diagnostics/invariant_checks_cacc.sh {WT}", A),
    ("diagnostics/*", "hand-written diagnostic script of this run (0 model calls)", R),
]


def main() -> None:
    files = []
    for p in sorted(x for x in RUN.rglob("*") if x.is_file() and x != OUT and "__pycache__" not in x.parts):
        r = p.relative_to(RUN).as_posix()
        rule = next(((sx, st) for pat, sx, st in RULES if fnmatch.fnmatch(r, pat)), None)
        if rule is None:
            raise SystemExit(f"no producer rule for {r}")
        b = p.read_bytes().replace(b"\r\n", b"\n")
        files.append({"path": r, "sha256": hashlib.sha256(b).hexdigest(), "basis": "git_blob_lf", "bytes": len(b),
                      "producer": rule[0], "status": rule[1]})
    OUT.write_text(json.dumps({"schema_version": "run-manifest/1", "run": "cuboid-acceptance",
                               "verification_commit": "f93408b7", "images": "NOT_APPLICABLE (no image captured; "
                               "the review checklist links the measured images of w18-binding-focus and "
                               "cuboid-final-review)", "files": files}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8", newline="\n")
    print(f"{OUT.name}: {len(files)} files")


if __name__ == "__main__":
    main()
