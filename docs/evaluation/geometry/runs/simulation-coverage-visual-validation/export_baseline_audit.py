# -*- coding: utf-8 -*-
"""Export baseline Scene3D payloads for Session 1 P2 Real Browser Audit (0 live LLM calls)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "backend"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.ai.function_route import run_function_route
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import build_simulation_state


def _compile_semantic_program(raw_spec: dict) -> dict:
    spec = SemanticProgramSpec.model_validate(raw_spec)
    res = SemanticProgramInterpreter().execute(spec)
    state = build_simulation_state(spec, res)
    return build_scene3d(state)


def build_baseline_scenes() -> list[dict]:
    scenes: list[dict] = []

    # 1. Triangular pyramid S.ABC (SA ⊥ (ABC), ΔABC vuông tại B)
    t1_text = "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = 3, BC = 4, SA vuông góc với mặt phẳng (ABC) và SA = 5. Tính thể tích khối chóp S.ABC."
    t1_calls = {
        "calls": [
            {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]}, "source": {"quote": "hình chóp S.ABC"}},
            {"id": "c2", "fn": "right_angle", "args": {"vertex": "B", "rays": ["A", "C"]}, "source": {"quote": "đáy ABC là tam giác vuông tại B"}},
            {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "3"}, "source": {"quote": "AB = 3"}},
            {"id": "c4", "fn": "segment_length", "args": {"segment": ["B", "C"], "value": "4"}, "source": {"quote": "BC = 4"}},
            {"id": "c5", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]}, "source": {"quote": "SA vuông góc với mặt phẳng (ABC)"}},
            {"id": "c6", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "5"}, "source": {"quote": "SA = 5"}},
            {"id": "c7", "fn": "ask_volume", "args": {"solid": "S.ABC"}, "source": {"quote": "Tính thể tích khối chóp S.ABC"}},
        ]
    }
    r1 = run_function_route(t1_text, t1_calls)
    assert r1.status == "SERVED" and r1.scene3d is not None, (r1.status, r1.code, r1.reason)
    scenes.append({
        "id": "audit_1_triangular_pyramid",
        "category": "Triangular pyramid",
        "served": True,
        "scene": r1.scene3d,
    })

    # 2. Regular square pyramid S.ABCD with derived plane section
    t2_text = "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy AB = 4 và cạnh bên SA = 6. Gọi M là trung điểm của SC. Mặt phẳng (ABM) cắt hình chóp S.ABCD theo một thiết diện. Tính diện tích tam giác ABM."
    t2_calls = {
        "calls": [
            {"id": "c1", "fn": "regular_pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quote": "hình chóp tứ giác đều S.ABCD"}},
            {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"]}, "source": {"quote": "hình chóp tứ giác đều S.ABCD"}},
            {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "4"}, "source": {"quote": "cạnh đáy AB = 4"}},
            {"id": "c5", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "6"}, "source": {"quote": "cạnh bên SA = 6"}},
            {"id": "c6", "fn": "midpoint", "args": {"point": "M", "segment": ["S", "C"]}, "source": {"quote": "Gọi M là trung điểm của SC"}},
            {"id": "c7", "fn": "section", "args": {"solid": "S.ABCD", "plane": ["A", "B", "M"]}, "depends_on": ["c6"], "source": {"quote": "Mặt phẳng (ABM) cắt hình chóp S.ABCD theo một thiết diện"}},
            {"id": "c8", "fn": "ask_area", "args": {"polygon": ["A", "B", "M"]}, "depends_on": ["c6"], "source": {"quote": "Tính diện tích tam giác ABM"}},
        ]
    }
    r2 = run_function_route(t2_text, t2_calls)
    assert r2.status == "SERVED" and r2.scene3d is not None, (r2.status, r2.code, r2.reason)
    scenes.append({
        "id": "audit_2_regular_square_pyramid_section",
        "category": "Regular square pyramid + plane section",
        "served": True,
        "scene": r2.scene3d,
    })

    # 3. Unnamed section intersections + multi-solid shared geometry + step-by-step construction (Demos 1–3 from Adapter /3)
    d1_path = ROOT / "docs/evaluation/geometry/runs/typedfact-next-adapter3-simulation/demos/demo1-unnamed-section-pyramid.json"
    d2_path = ROOT / "docs/evaluation/geometry/runs/typedfact-next-adapter3-simulation/demos/demo2-multi-solid-shared-geometry.json"
    d3_path = ROOT / "docs/evaluation/geometry/runs/typedfact-next-adapter3-simulation/demos/demo3-step-by-step-construction-highlight.json"
    for idx, (p, cat) in enumerate([
        (d1_path, "Automatically derived section points (I1..I3) + derived sub-pyramid + residual volume"),
        (d2_path, "Multiple solids with shared face (Cube ABCD.EFGH + Pyramid S.EFGH)"),
        (d3_path, "Step-by-step section construction and highlight"),
    ], start=3):
        d = json.loads(p.read_text(encoding="utf-8"))
        scenes.append({
            "id": f"audit_{idx}_{p.stem.replace('-', '_')}",
            "category": cat,
            "served": True,
            "scene": d["route_b"]["scene3d"],
        })

    # 6. Right triangular prism ABC.A'B'C'
    t6_text = "Cho lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh AB = 2, cạnh bên AA' = 3. Tính thể tích khối lăng trụ ABC.A'B'C'."
    t6_calls = {
        "calls": [
            {"id": "c1", "fn": "prism", "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"], "right": True}, "source": {"quote": "lăng trụ đứng ABC.A'B'C'"}},
            {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C"]}, "source": {"quote": "đáy ABC là tam giác đều"}},
            {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "2"}, "source": {"quote": "cạnh AB = 2"}},
            {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "A'"], "value": "3"}, "source": {"quote": "cạnh bên AA' = 3"}},
            {"id": "c5", "fn": "ask_volume", "args": {"solid": "ABC.A'B'C'"}, "source": {"quote": "Tính thể tích khối lăng trụ ABC.A'B'C'"}},
        ]
    }
    r6 = run_function_route(t6_text, t6_calls)
    assert r6.status == "SERVED" and r6.scene3d is not None
    scenes.append({
        "id": "audit_6_right_triangular_prism",
        "category": "Right triangular prism",
        "served": True,
        "scene": r6.scene3d,
    })

    # 7. Curved solids with scalar radius/height via existing SemanticProgram + curved.py
    cyl_scene = _compile_semantic_program({
        "spec_version": "1.0",
        "title": "Hình trụ tròn xoay",
        "memory_declarations": [
            {"name": "O", "type": "point3", "initial_value": [0, 0, 0], "provenance": "MODEL_ASSUMPTION", "model_assumption": "Chọn tâm đáy dưới O làm gốc tọa độ"},
            {"name": "R", "type": "float", "initial_value": 2, "provenance": "GIVEN", "source_fact_id": "f_R"},
            {"name": "h", "type": "float", "initial_value": 3, "provenance": "GIVEN", "source_fact_id": "f_h"},
            {"name": "tru", "type": "curved_solid"},
            {"name": "V", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_curved_solid", "target_var": "tru", "curved_kind": "cylinder", "anchor": "O", "radius": "R", "height": "h", "label": "Hình trụ tròn xoay tâm O"},
            {"kind": "assign", "target_var": "V", "expr": {"kind": "measure", "quantity": "volume", "of": "tru"}},
        ],
        "visual_bindings": {},
    })
    scenes.append({
        "id": "audit_7_curved_cylinder_scalar",
        "category": "Right circular cylinder (scalar R, h)",
        "served": True,
        "scene": cyl_scene,
    })

    cone_scene = _compile_semantic_program({
        "spec_version": "1.0",
        "title": "Hình nón tròn xoay",
        "memory_declarations": [
            {"name": "O", "type": "point3", "initial_value": [0, 0, 0], "provenance": "MODEL_ASSUMPTION", "model_assumption": "Chọn tâm đáy O làm gốc tọa độ"},
            {"name": "R", "type": "float", "initial_value": 3, "provenance": "GIVEN", "source_fact_id": "f_R"},
            {"name": "h", "type": "float", "initial_value": 4, "provenance": "GIVEN", "source_fact_id": "f_h"},
            {"name": "non", "type": "curved_solid"},
            {"name": "V", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_curved_solid", "target_var": "non", "curved_kind": "cone", "anchor": "O", "radius": "R", "height": "h", "label": "Hình nón tròn xoay đỉnh S"},
            {"kind": "assign", "target_var": "V", "expr": {"kind": "measure", "quantity": "volume", "of": "non"}},
        ],
        "visual_bindings": {},
    })
    scenes.append({
        "id": "audit_8_curved_cone_scalar",
        "category": "Right circular cone (scalar R, h)",
        "served": True,
        "scene": cone_scene,
    })

    sphere_scene = _compile_semantic_program({
        "spec_version": "1.0",
        "title": "Mặt cầu cắt bởi mặt phẳng",
        "memory_declarations": [
            {"name": "I", "type": "point3", "initial_value": [0, 0, 0], "provenance": "MODEL_ASSUMPTION", "model_assumption": "Chọn tâm mặt cầu I làm gốc tọa độ"},
            {"name": "R", "type": "float", "initial_value": 5, "provenance": "GIVEN", "source_fact_id": "f_R"},
            {"name": "cau", "type": "curved_solid"},
            {"name": "mp", "type": "plane3"},
            {"name": "duong_tron_giao", "type": "circle3"},
            {"name": "r_giao", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_curved_solid", "target_var": "cau", "curved_kind": "ball", "anchor": "I", "radius": "R", "label": "Mặt cầu (S) tâm I"},
            {"kind": "construct_plane_from_equation", "target_var": "mp", "a": 0, "b": 0, "c": 1, "d": -3, "label": "Mặt phẳng (α): z - 3 = 0"},
            {"kind": "assign", "target_var": "duong_tron_giao", "expr": {"kind": "intersect_plane_curved", "plane": "mp", "solid": "cau"}},
            {"kind": "assign", "target_var": "r_giao", "expr": {"kind": "measure", "quantity": "radius", "of": "duong_tron_giao"}},
        ],
        "visual_bindings": {},
    })
    scenes.append({
        "id": "audit_9_curved_sphere_scalar_section",
        "category": "Sphere (scalar R) + plane intersection circle",
        "served": True,
        "scene": sphere_scene,
    })

    return scenes


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent / "browser-audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "baseline_scenes.json"
    data = build_baseline_scenes()
    out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(data)} baseline audit scenes to {out_file}")
