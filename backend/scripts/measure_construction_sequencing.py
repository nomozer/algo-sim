"""Measure the learner-facing construction order of Hybrid scenes — run `pedagogical-construction-sequencing`.

Per case of `inputs/corpus.json`: route status, refusal code, answers and an exact math fingerprint (every point of the
engine layout, every final-memory point/section value) for O5, plus the scene object ids/coordinates for O6; with
`--ordering` also the O1–O4 verdicts of `tests/geometry/construction_sequencing.py`. `--compare <metrics.json>` checks
O5/O6 against an earlier run. 0 model calls; refuses to overwrite.

  cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/measure_construction_sequencing.py \
      --split development|ordering_check --out <new.json> [--ordering] [--compare <before.json>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
CORPUS = ROOT / "docs/evaluation/geometry/runs/pedagogical-construction-sequencing/inputs/corpus.json"


def _problem(row):
    from tests.geometry import hybrid_compiler_benchmark as HB
    from tests.geometry.test_two_line_plane_section import CASES, problem
    if row["id"].startswith("benchmark-"):
        c = next(c for c in HB.cases() if c["id"] == row["id"][len("benchmark-"):])
        return c["text"], {"facts": c["facts"]}
    c = CASES[row.get("corpus_index", 0)]
    text, payload = problem(c["family"], c["mid"], c["lines"])
    if row.get("variant") == "rename":
        ren = str.maketrans("SABCDMP", "TEFGKNQ")
        f = lambda s: re.sub(r"(?<!\w)[A-Z][A-Z0-9'.]*(?!\w)", lambda m: m[0].translate(ren), s)
        text, payload = f(text), json.loads(f(json.dumps(payload, ensure_ascii=False)))
    elif row.get("variant") == "collision":
        text = text.replace("Gọi M", "Gọi H").replace("qua M", "qua H")
        payload = json.loads(json.dumps(payload, ensure_ascii=False).replace('"M"', '"H"')
                             .replace("Gọi M", "Gọi H").replace("qua M", "qua H"))
    return text, payload


def _value(v):
    if hasattr(v, "x") and hasattr(v, "z"):
        return [str(v.x), str(v.y), str(v.z)]
    if hasattr(v, "polygon"):
        return sorted([str(p.x), str(p.y), str(p.z)] for p in v.polygon)
    return None


def measure(row, ordering):
    from app.ai.function_route import run_fact_route
    from tests.geometry.construction_sequencing import check
    r = run_fact_route(*_problem(row))
    out = {"id": row["id"], "status": r.status, "code": r.code, "answers": r.answers}
    if r.status == "SERVED":
        fm = r.exec_result.final_memory
        math = {"points": {k: [str(x) for x in v] for k, v in sorted((r.points or {}).items())},
                "memory": {k: val for k in sorted(fm) if (val := _value(fm[k])) is not None}}
        out["math_sha256"] = hashlib.sha256(json.dumps(math, sort_keys=True).encode()).hexdigest()
        out["math"] = math
        out["scene_points"] = {o["id"]: o["xyz"] for o in r.scene3d["objects"] if o["type"] == "point3"}
        out["scene_ids"] = sorted(o["id"] for o in r.scene3d["objects"])
        out["trace_steps"] = len(r.scene3d["events"])
        out["formation_roles"] = sorted({x for st in r.scene3d["formation"]["steps"] for x in st["formation_roles"]})
        if ordering:
            out["ordering"] = check(r.scene3d)
            out["ordering_pass"] = not any(out["ordering"].values())
            out["learner_text"] = [e["learner_text"] for e in r.scene3d["events"]]
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=("development", "ordering_check"), required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--ordering", action="store_true")
    ap.add_argument("--compare", type=Path)
    a = ap.parse_args()
    if a.out.exists():
        print(f"refusing to overwrite {a.out}")
        return 2
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    rows = [measure(row, a.ordering) for row in corpus[a.split]]
    fails = []
    if a.compare:
        before = {x["id"]: x for x in json.loads(a.compare.read_text(encoding="utf-8"))["cases"]}
        for x in rows:
            b = before[x["id"]]
            for k in ("status", "code", "answers", "math_sha256", "scene_points"):
                if x.get(k) != b.get(k):
                    fails.append(f"{x['id']}: O5/O6 {k} changed")
            lost = set(b.get("formation_roles") or []) - set(x.get("formation_roles") or [])
            if b.get("formation_roles") is not None and lost:
                fails.append(f"{x['id']}: formation roles lost {sorted(lost)}")
            gone = set(b.get("scene_ids", [])) - set(x.get("scene_ids", []))
            if gone:
                fails.append(f"{x['id']}: O6 objects removed {sorted(gone)}")
    if a.ordering:
        fails += [f"{x['id']}: {x['ordering']}" for x in rows if x.get("ordering_pass") is False]
    served = sum(x["status"] == "SERVED" for x in rows)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    import subprocess
    git = lambda *c: subprocess.run(["git", *c], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    cand = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
    a.out.write_text(json.dumps({"split": a.split, "git_head": git("rev-parse", "HEAD"),
                                 "git_dirty_paths": len(git("status", "--porcelain").splitlines()),
                                 "candidate_tree_hash": cand["measured_system"]["tree_hash"], "corpus_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
                                 "ordering_computed": a.ordering, "compared_with": str(a.compare) if a.compare else None,
                                 "served": served, "refused": len(rows) - served, "model_calls": 0,
                                 "failures": fails, "cases": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"split": a.split, "served": served, "refused": len(rows) - served, "failures": fails[:10],
                      "n_failures": len(fails)}, ensure_ascii=False))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
