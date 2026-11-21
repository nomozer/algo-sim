"""Score ablation arms with the shared independent scene oracle (read-only import) and diff them per case.

usage: (cwd = backend/) python compare.py <harness_dir> <unused> <out.json> <arm_dir>[,<arm_dir>...] <manifest_list.txt>
"""
import json, statistics, sys
from pathlib import Path

harness, runs_root, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
arm_dirs = [Path(p) for p in sys.argv[4].split(",")]
if out.exists():
    raise SystemExit(f"refusing to overwrite {out}")
sys.path.insert(0, str(harness))
import scene_oracle as SO  # noqa: E402

_man = {}


def manifest(src):
    if src not in _man:
        m = json.loads(Path(src_path[src]).read_text(encoding="utf-8"))
        _man[src] = {c["case_id"]: c for c in m["valid_cases"] + m["negative_cases"]}
    return _man[src]


src_path = {}
for line in Path(sys.argv[5]).read_text().strip().split(","):
    p = Path(line)
    src_path[p.parent.name + "/" + p.name] = p


def pct(v, q):
    if not v:
        return None
    s = sorted(v)
    return round(s[min(len(s) - 1, int(round((len(s) - 1) * q)))], 1)


report = {"schema": "axo17-routing-ablation-scores/1", "oracle": "docs/evaluation/geometry/harness/live-acceptance/scene_oracle.py", "arms": {}}
per_case = {}
for ad in arm_dirs:
    rows = [json.loads(l) for l in (ad / "rows.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    bodies = [json.loads(l) for l in (ad / "responses.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    arm = rows[0]["arm"]
    agg = {}
    for row, b in zip(rows, bodies):
        assert row["case_id"] == b["case_id"]
        case = manifest(row["source"])[row["case_id"]]
        v = SO.validate(case, b["body"])
        num = (v.get("numeric") or {}).get("status")
        pos = row["group"] == "valid_cases"
        served = row["route_status"] == "SERVED" and row["scene_served"]
        ok = pos and served and v["scene_validation"] == "MATHEMATICALLY_VALID" and num in (None, "CORRECT")
        rec = {"served": served, "oracle": v["scene_validation"], "numeric": num, "completed": ok,
               "mode": row["extraction_mode"], "reason": row["reason_code"], "slm": row["slm_inferences"], "ms": row["ms"],
               "http": row["http"]}
        per_case.setdefault((row["source"], row["case_id"]), {"expected": row["expected_behavior"], "group": row["group"]})[arm] = rec
        a = agg.setdefault(row["source"], {"positive": 0, "completed": 0, "served_positive": 0, "math_invalid_served": 0,
                                          "numeric_mismatch_served": 0, "negative": 0, "negative_served": 0,
                                          "slm_inferences": 0, "slm_invoked_cases": 0, "slm_contributed_completed": 0,
                                          "http_5xx": 0, "ms_completed": [], "ms_slm_completed": []})
        a["slm_inferences"] += row["slm_inferences"]
        a["slm_invoked_cases"] += int(row["slm_inferences"] > 0)
        a["http_5xx"] += int(row["http"] >= 500)
        if pos:
            a["positive"] += 1
            a["served_positive"] += int(served)
            a["completed"] += int(ok)
            a["math_invalid_served"] += int(served and v["scene_validation"] != "MATHEMATICALLY_VALID")
            a["numeric_mismatch_served"] += int(served and num == "MISMATCH")
            if ok:
                a["ms_completed"].append(row["ms"])
                if str(row["extraction_mode"] or "").startswith("LOCAL_SLM"):
                    a["slm_contributed_completed"] += 1
                    a["ms_slm_completed"].append(row["ms"])
        else:
            a["negative"] += 1
            a["negative_served"] += int(served)
    for a in agg.values():
        for k in ("ms_completed", "ms_slm_completed"):
            vals = a.pop(k)
            a[k.replace("ms_", "latency_") + "_ms"] = {"n": len(vals), "p50": round(statistics.median(vals), 1) if vals else None,
                                                        "p95": pct(vals, 0.95), "max": max(vals) if vals else None}
    tot = {}
    for a in agg.values():
        for k, val in a.items():
            if isinstance(val, int):
                tot[k] = tot.get(k, 0) + val
    report["arms"][arm] = {"by_source": agg, "total": tot, "summary": json.loads((ad / "summary.json").read_text())}

arms = [json.loads((ad / "summary.json").read_text())["arm"] for ad in arm_dirs]
diffs = []
for (src, cid), d in per_case.items():
    vals = [(d.get(a) or {}).get("completed") if d["group"] == "valid_cases" else (d.get(a) or {}).get("served") for a in arms]
    if len(set(vals)) > 1:
        diffs.append({"source": src, "case_id": cid, "expected": d["expected"], **{a: d.get(a) for a in arms}})
report["per_case_differences"] = diffs
out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
for a in arms:
    print(a, json.dumps(report["arms"][a]["total"]))
print("differences:", len(diffs))
