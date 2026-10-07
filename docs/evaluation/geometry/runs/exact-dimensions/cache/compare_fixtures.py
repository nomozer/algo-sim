# -*- coding: utf-8 -*-
"""exact-dimensions — evidence for the CACHE_VERSION decision. 0 model calls.

Compares the envelope of every fixture `scripts/generate_generic_tier_a_fixtures.py` writes on the tree BEFORE the
product change (clean detached worktree at 1c91f90d) and AFTER (this run). The cache keeps only `status == "ok"`
responses: a fixture served on both trees with a different envelope ⇒ old rows return the old payload ⇒ bump.

The radical Euclidean-frame cases were renamed in this run (`regular_triangular_pyramid_*` → `…_radical_*`,
`regular_tetrahedron_positive` → `regular_tetrahedron_radical_positive`); they are matched through `RENAMED` so the
same program is compared with itself. The family's new canonical names hold NEW programs (rational sizes) and have no
pre-change counterpart.

usage: python compare_fixtures.py <pre fixtures dir> <post fixtures dir> <out.json>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PRE, POST, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
RENAMED = {f"regular_triangular_pyramid_{k}.json": f"regular_triangular_pyramid_radical_{k}.json"
           for k in ("positive", "assumption", "wrong_centroid", "ungrounded", "non_positive")}
RENAMED["regular_tetrahedron_positive.json"] = "regular_tetrahedron_radical_positive.json"


def env(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))["envelope"]


def bam(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def khac(a, b, path=""):
    if type(a) is not type(b):
        yield path, a, b
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            yield from khac(a.get(k), b.get(k), f"{path}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            yield path + ".length", len(a), len(b)
        for i, (x, y) in enumerate(zip(a, b)):
            yield from khac(x, y, f"{path}[{i}]")
    elif a != b:
        yield path, a, b


rows, changed = {}, []
for p in sorted(PRE.glob("*.json")):
    q = POST / RENAMED.get(p.name, p.name)
    if not q.exists():
        rows[p.name] = {"post": None}
        continue
    a, b = env(p), env(q)
    served = a.get("status") == "ok" and b.get("status") == "ok"
    diff = [{"path": d[0], "pre": d[1], "post": d[2]} for d in list(khac(a, b))[:12]]
    rows[p.name] = {"post_name": q.name, "served_both": served, "identical": bam(a) == bam(b), "diff": diff}
    if served and bam(a) != bam(b):
        changed.append(p.name)
new = sorted(x.name for x in POST.glob("*.json") if x.name not in {RENAMED.get(p.name, p.name) for p in PRE.glob("*.json")})
out = {"schema_version": "cache-fixture-diff/1", "compared": len(rows), "identical": sum(r.get("identical", False)
       for r in rows.values()), "served_and_changed": changed, "new_post_only": new, "rows": rows}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"compared {out['compared']} · identical {out['identical']} · served+changed {changed} · new {new}")
