# -*- coding: utf-8 -*-
"""regular-triangular-pyramid-w01 — bằng chứng cho quyết định CACHE_VERSION. 0 lượt gọi model.

So envelope của MỌI fixture `scripts/generate_generic_tier_a_fixtures.py` sinh ở cây TRƯỚC (worktree tách rời tại
`dc0a804b`, mã sản phẩm chưa đổi) và cây SAU (cây làm việc của run). Cache chỉ giữ phản hồi `status == "ok"`: một
fixture PHỤC VỤ ở cả hai cây mà envelope khác ⇒ hàng cache cũ trả payload cũ ⇒ phải bump.

usage: python fixture_envelope_diff.py <pre fixtures dir> <post fixtures dir> <out.json>
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


def khac(a, b, path=""):
    if type(a) is not type(b):
        yield path, a, b
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                yield f"{path}.{k}", a.get(k, "<absent>"), b.get(k, "<absent>")
            else:
                yield from khac(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            yield f"{path}[len]", len(a), len(b)
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                yield from khac(x, y, f"{path}[{i}]")
    elif a != b:
        yield path, a, b


rows = {}
for f in sorted(PRE.glob("*.json")):
    a, b = env(f), env(POST / f.name)
    rows[f.name] = {"served": a.get("status") == "ok", "identical": bam(a) == bam(b),
                    "diff": [{"path": p, "pre": x, "post": y} for p, x, y in khac(a, b)]}
moi = sorted(p.name for p in POST.glob("*.json") if not (PRE / p.name).exists())
doi_phuc_vu = [n for n, r in rows.items() if r["served"] and not r["identical"]]
OUT.write_text(json.dumps({
    "schema_version": "cache-decision/1", "run_id": "regular-triangular-pyramid-w01",
    "cache_version_before": "115", "decision": "BUMP" if doi_phuc_vu else "NO_BUMP",
    "cache_version_after": "116" if doi_phuc_vu else "115",
    "rule": "The cache stores only status == ok responses. A bump is required when a response the old code SERVED "
            "would now be served with a different payload; refused -> served changes cannot leave a stale row.",
    "pre": "fixtures generated at dc0a804b (product code unchanged since e9435d67) in a detached worktree",
    "post": "fixtures generated from the run's working tree (product change of this run)",
    "fixtures_compared": len(rows), "identical": sum(r["identical"] for r in rows.values()),
    "served_and_changed": doi_phuc_vu, "new_fixtures_post_only": moi, "rows": rows,
    "model_surface_changed": False,
}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"{len(rows)} compared, {sum(r['identical'] for r in rows.values())} identical, served+changed {doi_phuc_vu}")
