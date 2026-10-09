# -*- coding: utf-8 -*-
"""oblique-prism — evidence for the CACHE_VERSION decision. 0 model calls.

Envelope of every fixture `backend/scripts/generate_generic_tier_a_fixtures.py` writes, on a clean detached worktree at
`ba995887` (pre) and on this branch (post), compared byte for byte BY NAME (this run renames nothing). The cache keeps
only `status == "ok"` responses: a fixture served on both trees with a different envelope ⇒ bump.

usage: python compare_fixtures.py <pre fixtures dir> <post fixtures dir> <out.json>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PRE, POST, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])


def env(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))["envelope"]


def bam(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


rows, changed = {}, []
for p in sorted(PRE.glob("*.json")):
    q = POST / p.name
    if not q.exists():
        rows[p.name] = {"post": None}
        continue
    a, b = env(p), env(q)
    rows[p.name] = {"status_pre": a.get("status"), "status_post": b.get("status"), "sha256_pre": bam(a),
                    "identical": bam(a) == bam(b)}
    if a.get("status") == "ok" and bam(a) != bam(b):
        changed.append(p.name)
new = sorted(x.name for x in POST.glob("*.json") if not (PRE / x.name).exists())
out = {"schema_version": "cache-fixture-diff/1", "compared": len(rows),
       "identical": sum(r.get("identical", False) for r in rows.values()),
       "served_pre": sum(r.get("status_pre") == "ok" for r in rows.values()),
       "served_and_changed": changed, "new_post_only": new, "rows": rows}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"compared {out['compared']} · identical {out['identical']} · served {out['served_pre']} · "
      f"served+changed {changed} · new {new}")
