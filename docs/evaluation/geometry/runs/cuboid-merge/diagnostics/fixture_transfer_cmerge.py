# -*- coding: utf-8 -*-
"""cuboid-merge — does the w18 visual evidence transfer to the current candidate? (read-only, 0 model calls)

Inputs: two output folders of `backend/scripts/generate_generic_tier_a_fixtures.py --out <dir>` (offline: Analyze
replaced by a canonical RequestContract, synthesis by the compiler or a frozen program, any model call raises), one run
in a clean detached worktree at the w18 measurement commit, one at the commit under review.

1. Reproduction: the raw-byte sha256 of the old folder's FIXTURE_MANIFEST.json must equal the
   `fixture_manifest_sha256` recorded in w18's results/BROWSER_EVIDENCE.json (the browser suite hashes raw bytes) —
   then every regenerated old fixture is the byte-exact fixture the w18 images were taken from.
2. Comparison: for every fixture, byte equality; if not, every differing JSON path (no field dropped or masked),
   grouped by the top-level key, with the old and new value for scalars.
Writes one JSON report. Usage:
  <python> fixture_transfer_cmerge.py <old dir> <new dir> <w18 BROWSER_EVIDENCE.json> <out.json>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

old, new, evidence, out = (Path(a) for a in sys.argv[1:5])


def diff(a, b, path="$"):
    if type(a) is not type(b):
        yield path, a, b
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                yield f"{path}.{k}", a.get(k, "<absent>"), b.get(k, "<absent>")
            else:
                yield from diff(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            yield f"{path}[len]", len(a), len(b)
        for i, (x, y) in enumerate(zip(a, b)):
            yield from diff(x, y, f"{path}[{i}]")
    elif a != b:
        yield path, a, b


def short(v):
    return v if isinstance(v, (int, float, bool)) or v is None or (isinstance(v, str) and len(v) <= 160) \
        else f"<{type(v).__name__}, {len(json.dumps(v, ensure_ascii=False))} chars>"


recorded = json.loads(evidence.read_text(encoding="utf-8"))["fixture_manifest_sha256"]
regenerated = hashlib.sha256((old / "FIXTURE_MANIFEST.json").read_bytes()).hexdigest()
report = {"schema_version": "fixture-transfer/1", "old_dir": str(old), "new_dir": str(new),
          "reproduction": {"recorded_fixture_manifest_sha256": recorded,
                           "regenerated_old_fixture_manifest_sha256": regenerated,
                           "byte_exact": recorded == regenerated},
          "fixtures": {}}
names = sorted(p.name for p in (old / "fixtures").glob("*.json"))
assert names == sorted(p.name for p in (new / "fixtures").glob("*.json")), "fixture sets differ"
for n in names:
    a_raw, b_raw = (old / "fixtures" / n).read_bytes(), (new / "fixtures" / n).read_bytes()
    entry = {"byte_equal": a_raw == b_raw}
    if not entry["byte_equal"]:
        d = list(diff(json.loads(a_raw), json.loads(b_raw)))
        groups: dict[str, int] = {}
        for p, _, _ in d:
            top = p.split(".")[1].split("[")[0] if "." in p else p
            groups[top] = groups.get(top, 0) + 1
        entry["differing_paths"] = len(d)
        entry["by_top_level_key"] = groups
        entry["paths"] = [{"path": p, "old": short(x), "new": short(y)} for p, x, y in d]
    report["fixtures"][n] = entry
report["summary"] = {"fixtures": len(names), "byte_equal": sum(e["byte_equal"] for e in report["fixtures"].values()),
                     "different": [n for n, e in report["fixtures"].items() if not e["byte_equal"]]}
out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(report["reproduction"]), json.dumps(report["summary"], ensure_ascii=False))
