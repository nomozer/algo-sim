"""Build the 14 representative Scene3D audit cases for geometric-visual-correctness-framing.

Aligns all demo titles, problem texts, Scene3D objects, and vertex notations (P5):
  - Case A (family05_prism): aligned category to "5. Hình lăng trụ đứng ABC.DEF" matching Scene3D ABC.DEF.
  - Case B (family07_multi_solid_composition): aligned category to
    "7. Tổ hợp đa khối (Hai hình chóp S.ABC và D.ABC chung đáy ABC)" and regenerated via
    Adapter /3 without leaking internal solid_id ("D1" instead of "D(pyr2)").
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RUN_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUN_DIR.parents[4]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.ai.adapter3_simulation import build_adapter3_simulation_response  # noqa: E402


def _load_json(rel_path: str) -> dict:
    return json.loads((REPO_ROOT / rel_path).read_text(encoding="utf-8"))


def _scene_of(doc: dict) -> dict:
    if "envelope" in doc and doc["envelope"] and "scene3d" in doc["envelope"]:
        return doc["envelope"]["scene3d"]
    if "route_d" in doc and doc["route_d"] and "scene3d" in doc["route_d"]:
        return doc["route_d"]["scene3d"]
    if "route_b" in doc and doc["route_b"] and "scene3d" in doc["route_b"]:
        return doc["route_b"]["scene3d"]
    return doc["scene3d"]


def _build_ellipse_cylinder_demo() -> dict:
    problem_text = (
        "Cho hình trụ tròn xoay có tâm đáy dưới O, tâm đáy trên O', bán kính đáy R = 2a "
        "và chiều cao h = 6a. Mặt phẳng (P) có phương trình x - z + 3 = 0 cắt trục OO' "
        "và cắt mặt trụ theo một thiết diện elip. Hãy dựng hình trụ, mặt phẳng cắt (P), "
        "thiết diện elip và tính diện tích thiết diện elip cùng thể tích hình trụ."
    )
    payload = {
        "schema_version": "typed-fact-next/1",
        "problem_text": problem_text,
        "length_unit": "a",
        "solids": [
            {
                "solid_id": "cyl_1",
                "solid_type": "cylinder",
                "notation": "OO'",
                "center": "O",
                "apex_or_top": "O'",
                "radius": "2a",
                "height": "6a",
                "quote": "Cho hình trụ tròn xoay có tâm đáy dưới O, tâm đáy trên O', bán kính đáy R = 2a và chiều cao h = 6a.",
            }
        ],
        "premises": [],
        "relations": [],
        "derived_sections": [
            {
                "section_id": "sec_el",
                "plane_name": "P",
                "target_solid_id": "cyl_1",
                "plane_kind": "plane_equation",
                "section_shape": "ellipse",
                "equation_coeffs": ["1", "0", "-1", "3"],
                "quote": "Mặt phẳng (P) có phương trình x - z + 3 = 0 cắt trục OO' và cắt mặt trụ theo một thiết diện elip.",
            }
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_cyl",
                "kind": "construct_object",
                "target_solid_id": "cyl_1",
                "style_role": "primary",
                "quote": "Hãy dựng hình trụ",
            },
            {
                "goal_id": "sim_el",
                "kind": "construct_plane_section",
                "target_section_id": "sec_el",
                "style_role": "section",
                "quote": "thiết diện elip",
            },
        ],
        "math_goals": [
            {
                "goal_id": "area_el",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"section_id": "sec_el"},
                "quote": "tính diện tích thiết diện elip",
            },
            {
                "goal_id": "vol_cyl",
                "kind": "measurement",
                "goal_type": "volume",
                "target": {"solid": "cyl_1"},
                "quote": "thể tích hình trụ.",
            },
        ],
    }
    res = build_adapter3_simulation_response(payload)
    assert res["route_d"]["status"] == "SERVED", f"Expected SERVED for ellipse demo, got {res['route_d']}"
    return res


def main() -> None:
    demos_dir = RUN_DIR / "demos"
    demos_dir.mkdir(parents=True, exist_ok=True)

    w11_dir = "docs/evaluation/geometry/runs/w11-pedagogical-polish/inputs/fixtures"
    rsp_dir = "docs/evaluation/geometry/runs/regular-square-pyramid-w03/inputs/fixtures"
    cov_run_dir = REPO_ROOT / "docs/evaluation/geometry/runs/simulation-coverage-visual-validation"
    if str(cov_run_dir) not in sys.path:
        sys.path.insert(0, str(cov_run_dir))
    from oracle_eval import build_demos_and_corpus  # type: ignore[import-not-found]

    cov_demos_spec, _ = build_demos_and_corpus()
    cov_payload_by_id = {d[0]: d[2] for d in cov_demos_spec}

    f1 = _load_json(f"{w11_dir}/triangular_pyramid_positive.json")
    f2 = _load_json(f"{w11_dir}/rectangular_pyramid_positive.json")
    f3 = _load_json(f"{rsp_dir}/regular_square_pyramid_positive.json")
    f4 = build_adapter3_simulation_response(cov_payload_by_id["demo1-pyramid-derived-section"])
    f5 = _load_json(f"{w11_dir}/triangular_prism_positive.json")
    f6_cube = _load_json(f"{w11_dir}/cube_positive.json")
    f6_cuboid = _load_json(f"{w11_dir}/cuboid_positive.json")
    f7 = build_adapter3_simulation_response(cov_payload_by_id["demo3-multi-solid-shared-geometry"])
    f8 = build_adapter3_simulation_response(cov_payload_by_id["demo2-unnamed-section-intersections"])
    f9 = build_adapter3_simulation_response(cov_payload_by_id["demo6a-curved-cylinder-sections"])
    f10 = build_adapter3_simulation_response(cov_payload_by_id["demo6b-curved-cone-frustum-cut"])
    f11 = build_adapter3_simulation_response(cov_payload_by_id["demo6c-curved-sphere-plane-cut"])
    f12 = _build_ellipse_cylinder_demo()
    f13 = build_adapter3_simulation_response(cov_payload_by_id["demo7-invalid-geometry-safe-refusal"])

    scenes = [
        {
            "id": "family01_triangular_pyramid",
            "family": "triangular_pyramid",
            "category": "1. Hình chóp tam giác S.ABC",
            "served": True,
            "problem_text": f1.get("problem_text") or f1["envelope"].get("title") or "Cho hình chóp S.ABC có SA vuông góc với đáy.",
            "envelope": f1["envelope"],
            "scene": _scene_of(f1),
        },
        {
            "id": "family02_quadrilateral_pyramid",
            "family": "quadrilateral_pyramid",
            "category": "2. Hình chóp tứ giác S.ABCD",
            "served": True,
            "problem_text": f2.get("problem_text") or f2["envelope"].get("title") or "Cho hình chóp S.ABCD có đáy là hình chữ nhật.",
            "envelope": f2["envelope"],
            "scene": _scene_of(f2),
        },
        {
            "id": "family03_regular_pyramid",
            "family": "regular_pyramid",
            "category": "3. Hình chóp tứ giác đều S.ABCD",
            "served": True,
            "problem_text": f3.get("problem_text") or f3["envelope"].get("title") or "Cho hình chóp tứ giác đều S.ABCD.",
            "envelope": f3["envelope"],
            "scene": _scene_of(f3),
        },
        {
            "id": "family04_derived_sub_pyramid",
            "family": "derived_sub_pyramid",
            "category": "4. Thiết diện & Khối chóp con dẫn xuất S.ABMN",
            "served": True,
            "problem_text": f4.get("problem_text"),
            "route_d": f4["route_d"],
            "scene": _scene_of(f4),
        },
        {
            "id": "family05_prism",
            "family": "prism",
            "category": "5. Hình lăng trụ đứng ABC.DEF",
            "served": True,
            "problem_text": f5.get("problem_text") or f5["envelope"].get("title") or "Cho hình lăng trụ đứng ABC.DEF.",
            "envelope": f5["envelope"],
            "scene": _scene_of(f5),
        },
        {
            "id": "family06a_cube",
            "family": "cube",
            "category": "6a. Hình lập phương ABCD.A'B'C'D'",
            "served": True,
            "problem_text": f6_cube.get("problem_text") or f6_cube["envelope"].get("title") or "Cho hình lập phương ABCD.A'B'C'D'.",
            "envelope": f6_cube["envelope"],
            "scene": _scene_of(f6_cube),
        },
        {
            "id": "family06b_cuboid",
            "family": "cuboid",
            "category": "6b. Hình hộp chữ nhật ABCD.A'B'C'D'",
            "served": True,
            "problem_text": f6_cuboid.get("problem_text") or f6_cuboid["envelope"].get("title") or "Cho hình hộp chữ nhật ABCD.A'B'C'D'.",
            "envelope": f6_cuboid["envelope"],
            "scene": _scene_of(f6_cuboid),
        },
        {
            "id": "family07_multi_solid_composition",
            "family": "multi_solid_composition",
            "category": "7. Tổ hợp đa khối (Hai hình chóp S.ABC và D.ABC chung đáy ABC)",
            "served": True,
            "problem_text": f7.get("problem_text"),
            "route_d": f7["route_d"],
            "scene": _scene_of(f7),
        },
        {
            "id": "family08_unnamed_section_vertices",
            "family": "unnamed_section_vertices",
            "category": "8. Thiết diện có giao điểm ẩn tên I1",
            "served": True,
            "problem_text": f8.get("problem_text"),
            "route_d": f8["route_d"],
            "scene": _scene_of(f8),
        },
        {
            "id": "family09_cylinder_and_sections",
            "family": "right_circular_cylinder",
            "category": "9. Hình trụ tròn xoay & Thiết diện qua trục / song song đáy",
            "served": True,
            "problem_text": f9.get("problem_text"),
            "route_d": f9["route_d"],
            "scene": _scene_of(f9),
        },
        {
            "id": "family10_cone_frustum_cut",
            "family": "right_circular_cone",
            "category": "10. Hình nón tròn xoay & Thiết diện song song đáy / qua trục",
            "served": True,
            "problem_text": f10.get("problem_text"),
            "route_d": f10["route_d"],
            "scene": _scene_of(f10),
        },
        {
            "id": "family11_sphere_plane_cut",
            "family": "sphere",
            "category": "11. Mặt cầu & Thiết diện đường tròn cắt bởi mặt phẳng",
            "served": True,
            "problem_text": f11.get("problem_text"),
            "route_d": f11["route_d"],
            "scene": _scene_of(f11),
        },
        {
            "id": "family12_cylinder_ellipse_section",
            "family": "curved_cylinder_ellipse_section",
            "category": "12. Hình trụ & Thiết diện Elip (nghiêng 45°)",
            "served": True,
            "problem_text": f12.get("problem_text"),
            "route_d": f12["route_d"],
            "scene": _scene_of(f12),
        },
        {
            "id": "family13_invalid_geometry_refusal",
            "family": "safe_refusal",
            "category": "13. Từ chối an toàn khi mặt phẳng không cắt mặt cầu",
            "served": False,
            "problem_text": f13.get("problem_text"),
            "code": f13.get("route_d", {}).get("refusal", {}).get("code") or "MAT_PHANG_KHONG_CAT_KHOI",
            "reason": f13.get("route_d", {}).get("refusal", {}).get("detail") or "Mặt phẳng cách tâm lớn hơn bán kính.",
        },
    ]

    out_file = demos_dir / "audit_scenes.json"
    out_file.write_text(json.dumps(scenes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(scenes)} audit scenes to {out_file}")


if __name__ == "__main__":
    main()
