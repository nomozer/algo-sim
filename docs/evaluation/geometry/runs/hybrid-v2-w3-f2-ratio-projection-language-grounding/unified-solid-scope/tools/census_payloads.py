"""Read-only census: every committed TypedFactNext payload, which solid-scope fields it actually uses."""
import collections, json, sys
from pathlib import Path

ROOT = Path(sys.argv[1])
seen = collections.Counter(); curved = []; files = set()
def payloads(obj):
    if isinstance(obj, dict):
        if str(obj.get("schema_version", "")).startswith("typed-fact-next/") and "solids" in obj:
            yield obj
        for v in obj.values(): yield from payloads(v)
    elif isinstance(obj, list):
        for v in obj: yield from payloads(v)
for path in ROOT.rglob("*.json"):
    if ".superpowers" in path.parts or "node_modules" in path.parts: continue
    try: data = json.loads(path.read_text(encoding="utf-8"))
    except Exception: continue
    for p in payloads(data):
        files.add(path); seen["payloads"] += 1
        kinds = {s.get("solid_type", "pyramid") for s in p["solids"]}
        if kinds - {"pyramid", "prism"}:
            curved.append((path.relative_to(ROOT).as_posix(), len(p.get("premises", [])), len(p.get("relations", [])),
                           sorted({pr.get("kind") for pr in p.get("premises", [])})))
        for pr in p.get("premises", []):
            seen["premise.solid_id"] += "solid_id" in pr
            seen["premise.args.solid"] += "solid" in pr.get("args", {})
        for r in p.get("relations", []):
            for k in ("solid_id", "solid_a", "solid_b"): seen[f"relation.{k}"] += k in r
        for g in p.get("simulation_goals", []):
            seen["sim.parent_solid_id"] += "parent_solid_id" in g
        for g in p.get("math_goals", []):
            seen[f"math.{g.get('kind')}.solid_id"] += "solid_id" in g
            for k in ("solid", "solid_id", "section_id"): seen[f"math.target.{k}"] += k in g.get("target", {})
print(json.dumps({"files": len(files), "counts": seen, "curved_payloads": len(curved),
                  "curved_with_premises_or_relations": [c for c in curved if c[1] or c[2]][:15]}, ensure_ascii=False, indent=1))
