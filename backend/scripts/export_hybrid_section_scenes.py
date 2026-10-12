"""Export Scene3D scenes produced by the REAL Hybrid route (typed facts → planner → gate → engine → IR → Scene3D) for the
section / intersection-line slice, for the browser harness `frontend/scripts/hybrid-section-visual.html` — 0 model calls.

    python scripts/export_hybrid_section_scenes.py --out <NEW directory>

Writes `scenes.json`: [{id, text, served, answers, section_vertices (count), scene}]. Refuses an existing directory.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ALLOW_LIVE_AI", "0")


def _cases():
    from tests.geometry import hybrid_compiler_benchmark as HB

    f, ask = HB._f, HB._ask

    def sec(fid, plane, solid="S.ABCD"):
        quote = f"Xác định thiết diện của hình chóp {solid} cắt bởi mặt phẳng ({''.join(plane)})."
        return f(fid, "section", quote, role="question", solid=solid, points=list(plane))

    sq = HB._square()
    cube_q = ["Cho hình lập phương ABCD.A'B'C'D' cạnh 2.", "Xác định thiết diện của hình lập phương cắt bởi mặt phẳng (A'BD)."]
    yield "section-MAB-trapezoid", HB._with(sq, HB._mid("f5", "M", "S", "C"), sec("f6", "MAB"))
    yield "section-SAC-triangle", HB._with(sq, sec("f5", "SAC"))
    yield "section-MNP-mid-square", HB._with(sq, HB._mid("f5", "M", "S", "A"), HB._mid("f6", "N", "S", "B"),
                                             HB._mid("f7", "P", "S", "C"), sec("f8", "MNP"))
    yield "section-cube-A1BD", (cube_q, [f("f1", "solid", cube_q[0], solid="ABCD.A'B'C'D'", solid_type="cube"),
                                         f("f2", "length", cube_q[0], solid="ABCD.A'B'C'D'", measure="edge", value="2"),
                                         f("f3", "section", cube_q[1], role="question", solid="ABCD.A'B'C'D'",
                                           points=["A'", "B", "D"])])
    yield "intersection-SAB-SCD", HB._with(sq, f("f5", "intersection_line", "Tìm giao tuyến của (SAB) và (SCD).",
                                                 role="question", points_a=list("SAB"), points_b=list("SCD")))
    yield "aux-foot-S-to-BD", HB._with(sq, ask("q", "Tính khoảng cách từ S đến BD.", "distance", points_a=["S"],
                                               points_b=["B", "D"]))
    # run hybrid-semantic-hardening: a second intersection line, through S and the base centre (not axis-parallel)
    yield "intersection-SAC-SBD", HB._with(sq, f("f5", "intersection_line", "Tìm giao tuyến của (SAC) và (SBD).",
                                                 role="question", points_a=list("SAC"), points_b=list("SBD")))
    # unit-size pyramid: the frame metric is the identity, so payload = world — the size at which a fixed ±6 line
    # display passed behind the camera
    uq = [s.replace("cạnh 2", "cạnh 1").replace("= 3", "= 1") for s in sq[0]]
    uf = [{**x, "quotes": [uq[i]], **({"value": "1"} if "value" in x else {})} for i, x in enumerate(sq[1])]
    yield "intersection-SAB-SCD-unit", HB._with((uq, uf), f("f5", "intersection_line", "Tìm giao tuyến của (SAB) và (SCD).",
                                                            role="question", points_a=list("SAB"), points_b=list("SCD")))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    if out.exists():
        print(f"refusing to overwrite {out}")
        return 2
    from app.ai.function_route import run_fact_route

    rows = []
    for cid, (sentences, facts) in _cases():
        text = " ".join(sentences)
        r = run_fact_route(text, {"facts": facts})
        sections = [o for o in (r.scene3d or {}).get("objects", []) if o.get("type") == "section"]
        n = len(r.exec_result.final_memory[sections[0]["id"]].polygon) if sections else 0
        rows.append({"id": cid, "text": text, "served": r.status == "SERVED", "code": r.code, "answers": r.answers,
                     "section_vertices": n, "scene": r.scene3d})
    out.mkdir(parents=True)
    (out / "scenes.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print(json.dumps([{k: v for k, v in x.items() if k != "scene"} for x in rows], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
