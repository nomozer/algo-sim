"""Offline development cases; exact oracles are textbook formulas, never engine output.

No extraction-quality or independent holdout claim. Run with an explicit fresh output path.
"""
from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "backend"))


def prism(base="ABC", top="DEF", *, right=True, equivalent=False):
    a, b, c = base
    d = top[0]
    name = f"{base}.{top}"
    solid = f"Cho hình lăng trụ {'đứng ' if right else ''}{name}"
    shape = f"đáy {base} là tam giác vuông tại {a}"
    question = f"Tính thể tích khối lăng trụ {name}."
    text = f"{solid} có {shape}, {a}{b} = 3, {a}{c} = 4. Cạnh bên {a}{d} = 5. {question}"
    premises = [{"kind": "right_angle", "args": {"vertex": a, "rays": [b, c]}, "quote": shape}]
    if right:
        premises.append({"kind": "right_prism", "args": {"base": list(base), "top": list(top)}, "quote": solid})
    premises += [{"kind": "segment_length", "args": {"segment": [x, y], "value": v}, "quote": f"{x}{y} = {v}"}
                 for x, y, v in [(a, b, "3"), (a, c, "4"), (a, d, "5")]]
    if equivalent:
        # Same right angle and dimensions, different premise order and surface wording.
        text = f"{solid}. Cạnh bên {a}{d} = 5. Biết {shape}, {a}{c} = 4 và {a}{b} = 3. {question}"
    return {"schema_version": "typed-fact-next/2", "problem_text": text, "length_unit": "1",
            "solids": [{"solid_id": "pr", "solid_type": "prism", "notation": name, "quote": solid}],
            "premises": premises,
            "simulation_goals": [{"goal_id": "draw", "kind": "construct_object", "target_solid_id": "pr", "quote": solid}],
            "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": "volume",
                            "target": {"solid_id": "pr"}, "quote": question}]}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cases():
    """Oracles fix expectations mathematically before observing route output.

    The oblique pair has h=5 versus h=4 with the same lateral edge 5 by changing
    the horizontal offset from 0 to 3. Volumes 30 and 24 satisfy the same oblique
    givens, proving non-uniqueness; no renderer coordinates enter the oracle.
    """
    tools = ROOT / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/tools"
    curved = _load("reliability_curved", tools / "curved_probe.py")
    sections = _load("reliability_sections", tools / "curved_section_probe.py")
    sphere = _load("reliability_sphere", tools / "sphere_section_probe.py")
    polygon = _load("reliability_polygon", ROOT / "backend/tests/geometry/test_hybrid4_three_point_plane_sections.py")
    pyramid_text = "Cho hình chóp S.ABC có diện tích đáy ABC bằng 6, SA vuông góc với (ABC) và SA = 5. Tính thể tích khối chóp S.ABC."
    pyramid = {"schema_version": "typed-fact-next/2", "problem_text": pyramid_text, "length_unit": "1",
               "solids": [{"solid_id": "pyr", "solid_type": "pyramid", "notation": "S.ABC", "quote": "Cho hình chóp S.ABC"}],
               "premises": [{"kind": "polygon_area", "args": {"vertices": list("ABC"), "value": "6"},
                             "quote": "diện tích đáy ABC bằng 6"},
                            {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": list("ABC")},
                             "quote": "SA vuông góc với (ABC)"},
                            {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "5"}, "quote": "SA = 5"}],
               "simulation_goals": [{"goal_id": "draw", "kind": "construct_object", "target_solid_id": "pyr", "quote": "Cho hình chóp S.ABC"}],
               "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "pyr"},
                               "quote": "Tính thể tích khối chóp S.ABC."}]}
    solid, prem = polygon.square_pyramid("S", "ABCD", 4, 6)
    prem += [polygon.midpoint(p, "S", b) for p, b in zip("MNP", "ABC")]
    _, poly = polygon._payload(solid, prem, list("MNP"))
    bad = curved.payload(curved.CONE, "volume", "Tính thể tích khối nón.")
    curved.overdetermined(bad)
    return [
        ("right-prism", prism(), "30", "determined", "(3*4/2)*5"),
        ("oblique-prism", prism(right=False), None, "insufficient", "h=5 or h=4 with edge=5; V=30 or V=24"),
        ("pyramid-base-area", pyramid, "10", "unsupported", "6*5/3; area premise is outside the registered bridge"),
        ("cone-volume", curved.payload(curved.CONE, "volume", "Tính thể tích khối nón."), "12π", "determined", "pi*3**2*4/3"),
        ("cylinder-section", sections.CASES[0][1], "9π", "determined", "pi*3**2; section perpendicular to the axis"),
        ("sphere-volume", curved.payload(curved.SPH, "volume", "Tính thể tích khối cầu."), "36π", "determined", "4*pi*3**3/3"),
        ("sphere-plane", sphere.CASES[0][1], "16π", "determined", "pi*(5**2-3**2)"),
        ("polygon-section", poly, "4", "determined", "square side 4 scaled by 1/2; area=(4/2)**2"),
        ("contradiction", bad, None, "contradictory", "3**2+4**2 != 6**2"),
        ("exact-domain", curved.payload(curved.CONE_R, "area", "Tính diện tích toàn phần của hình nón."),
         None, "unsupported", "4*pi*sqrt(2)+4*pi is determined but outside the single-radical domain"),
        ("equivalent-wording", prism(equivalent=True), "30", "determined", "same right-prism facts; (3*4/2)*5"),
        ("renamed-points", prism("KLM", "NOP"), "30", "determined", "renaming preserves (3*4/2)*5"),
    ]


def main():
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route

    if sys.argv[1] == "--corpus":
        output = Path(sys.argv[2])
        rows = []
        for cid, p, oracle, category, derivation in cases():
            r = run_typed_fact_next_v2_route(p)
            rows.append({"id": cid, "input": p, "oracle": oracle, "mathematical_class": category,
                         "derivation": derivation, "kernel_check": r.kernel_check,
                         "response": build_adapter4_response(r, p["problem_text"])})
        with output.open("x", encoding="utf-8") as stream:
            json.dump(rows, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps({"cases": len(rows), "served": sum(r["response"]["route_d"]["status"] == "SERVED" for r in rows)}))
        return
    output = Path(sys.argv[1])
    p = prism()
    r = run_typed_fact_next_v2_route(p)
    response = build_adapter4_response(r, p["problem_text"])
    record = {"input": p, "oracle": {"base_area": "6", "height": "5", "volume": "30",
                                      "derivation": "(3*4/2)*5"},
              "status": r.status, "code": r.code, "kernel_check": r.kernel_check,
              "trace": r.trace, "response": response}
    with output.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": r.status, "kernel_check": r.kernel_check, "answer": r.answer_exact,
                      "certificates": [t for t in r.trace if t.get("step") == "certify_answer"]}))


if __name__ == "__main__":
    main()
