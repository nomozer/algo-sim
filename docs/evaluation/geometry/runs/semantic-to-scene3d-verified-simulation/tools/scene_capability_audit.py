"""Semantic-to-Scene3D audit: what each goal type puts in the served scene, BEFORE and AFTER this run's change.

BEFORE = backend/app exported with `git archive` at the run's start HEAD (8a5a54e37) into a scratch directory; AFTER =
this checkout. Each side runs in its own child process (`--probe`) through `route_text_input` (local-first, no AI).
Probes are SYNTHETIC statements written by the agent to exercise one goal type each (development probes, not an
evaluation corpus).  Run from backend/:  python <tools>/scene_capability_audit.py <before_backend_dir>
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
P = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
CUBE = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. "
PROBES = {
    "angle_line_plane": ("angle", P + "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD)."),
    "angle_line_plane_lateral": ("angle", P + "Tính góc giữa đường thẳng SC và mặt phẳng (SAB)."),
    "angle_line_plane_tetra": ("angle", "Cho tứ diện đều ABCD có cạnh bằng a. Tính góc giữa đường thẳng AB và mặt phẳng (BCD)."),
    "angle_line_line_cross": ("angle", P + "Tính góc giữa hai đường thẳng SC và AC."),
    "angle_line_line_skew": ("angle", CUBE + "Tính góc giữa hai đường thẳng AC và A'D."),
    "angle_right": ("angle", P + "Tính góc giữa đường thẳng SA và mặt phẳng (ABCD)."),
    "dihedral_pyramid": ("angle", P + "Tính góc giữa mặt phẳng (SBC) và mặt phẳng (ABCD)."),
    "dihedral_prism": ("angle", "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh a, AA' = a. "
                                "Tính góc giữa mặt phẳng (A'BC) và mặt phẳng (ABC)."),
    "distance_point_plane": ("distance", P + "Tính khoảng cách từ A đến mặt phẳng (SBC)."),
    "distance_point_line": ("distance", P + "Tính khoảng cách từ A đến đường thẳng SC."),
    "distance_skew_lines": ("distance", P + "Tính khoảng cách giữa hai đường thẳng SB và AD."),
    "distance_skew_cuboid": ("distance", "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = a, BC = 2a và AA' = 3a. "
                                         "Tính khoảng cách giữa hai đường thẳng BD và A'C'."),
    "projection_named": ("projection", P + "Gọi H là hình chiếu vuông góc của A trên SB. Tính độ dài AH."),
    "midpoint_length": ("length", P + "Gọi M là trung điểm của SC. Tính độ dài AM."),
    "volume_pyramid": ("volume", P + "Tính thể tích khối chóp S.ABCD."),
    "volume_regular_pyramid": ("volume", "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a, cạnh bên bằng 2a. Tính thể tích khối chóp S.ABCD."),
    "section_midpoints": ("section", CUBE + "Gọi M, N lần lượt là trung điểm của AB và AD. Xác định thiết diện của hình lập phương cắt bởi mặt phẳng (MNC')."),
    "section_plane_cut": ("section", P + "Gọi M là trung điểm của SC. Mặt phẳng (ABM) cắt hình chóp theo thiết diện là hình gì?"),
    "intersection_planes": ("intersection", P + "Xác định giao tuyến của hai mặt phẳng (SAB) và (SCD)."),
    "centroid_foot": ("height", "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, hình chiếu vuông góc của S lên mặt phẳng (ABC) "
                                "trùng với trọng tâm G của tam giác ABC, SA = 2a. Tính thể tích khối chóp S.ABC."),
    "face_perp_base": ("height", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, tam giác SAB đều và nằm trong mặt phẳng "
                                 "vuông góc với mặt phẳng đáy. Tính thể tích khối chóp S.ABCD."),
    "late_square_side": ("distance", "Cho hình chóp S.ABCD có SA ⊥ (ABCD), đáy ABCD là hình vuông, biết AB = 1, SA = 2. "
                                     "Khoảng cách từ điểm C đến mặt phẳng (SBD) bằng"),
    "reflection_point": ("volume", "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc, OA = a, OB = a, OC = a. Gọi M là điểm đối xứng "
                                   "với O qua trung điểm của AB. Tính thể tích tứ diện MABC."),
    "scale_free_angle": ("angle", "Cho tứ diện đều ABCD. Gọi M là trung điểm của CD. Tính góc giữa hai đường thẳng AC và BM."),
}


def probe() -> None:
    os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
    from app.ai.adaptive_input_router import route_text_input
    out = {}
    for name, (goal, text) in json.loads(sys.stdin.read()).items():
        r = route_text_input(text, allow_live_ai=False).response
        rd, env = r.get("route_d") or {}, r.get("envelope") or {}
        sc = env.get("scene3d") or {}
        objs = sc.get("objects", [])
        q = [o for o in objs if o.get("type") == "quantity" and "target" in (o.get("display_group") or [])]
        ann = [(o.get("annotation") or {}) for o in q]
        out[name] = {
            "goal": goal, "status": rd.get("status"),
            "reason": r.get("reason_code") or env.get("reason_code") or (rd.get("refusal") or {}).get("code"),
            "types": dict(Counter(o["type"] for o in objs)),
            "has_solid": any(o["type"] == "solid" for o in objs),
            "derived_points": [f"{o['id']}:{o.get('producer')}" for o in objs if o["type"] == "point3" and o.get("origin") != "free"],
            "sections": [o["id"] for o in objs if o["type"] == "section"],
            "goal_annotation": [{"kind": a.get("kind"), "anchor": a.get("anchor"), "relation": (a.get("witness") or {}).get("relation")} for a in ann],
            "angle_construction": [o["angle_construction"]["relation"] for o in q if o.get("angle_construction")],
            "height_witness": sum(1 for o in objs if o.get("perpendicular_witness")),
            "chart_identity": sc.get("chart_metric") in (None, [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]]),
            "unit_chosen_by_system": any(t.get("step") == "choose_unit" for t in rd.get("construction_trace") or []),
            "layout_derived_points": sum(1 for o in objs if (o.get("source") or {}).get("provenance") == "LAYOUT_DERIVED"),
            "steps": len((sc.get("formation") or {}).get("steps", [])),
            "diagnostics": sc.get("diagnostics") or [],
        }
    print(json.dumps(out, ensure_ascii=False))


def side(backend: Path) -> dict:
    env = {**os.environ, "PYTHONPATH": str(backend), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": ""}
    res = subprocess.run([sys.executable, __file__, "--probe"], input=json.dumps(PROBES, ensure_ascii=False), capture_output=True,
                         text=True, cwd=backend, env=env, encoding="utf-8", check=True)
    return json.loads(res.stdout.strip().splitlines()[-1])


def level(r: dict) -> str:
    """Level 1 = base geometry served; Level 2 = the object the question studies is constructed in the scene."""
    if r["status"] != "SERVED":
        return "NOT_SERVED:" + str(r["reason"])
    if not r["has_solid"]:
        return "SERVED_WITHOUT_SOLID"
    g = r["goal"]
    ann = r["goal_annotation"][0] if r["goal_annotation"] else {}
    goal_built = {
        "angle": bool(r["angle_construction"]) or ann.get("anchor") == "witness",
        "distance": ann.get("anchor") in ("witness", "segment"),
        "projection": any(":construct_point.project_onto" in p for p in r["derived_points"]),
        "length": ann.get("anchor") == "segment",
        "volume": r["has_solid"],
        "section": bool(r["sections"]),
        "intersection": False, "height": r["height_witness"] > 0,
    }[g]
    return "LEVEL2_GOAL_CONSTRUCTED" if goal_built else "LEVEL1_BASE_ONLY"


def main() -> int:
    before, after = side(Path(sys.argv[1])), side(ROOT / "backend")
    rows = [{"probe": k, "goal": PROBES[k][0], "text": PROBES[k][1], "before": {**before[k], "level": level(before[k])},
             "after": {**after[k], "level": level(after[k])}} for k in PROBES]
    now = datetime.now(timezone.utc).isoformat()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    (RUN / "semantic_to_scene_gap_matrix.json").write_text(json.dumps({
        "run_id": RUN.name, "generated_at_utc": now, "head": head, "before_ref": "8a5a54e37 (start of this run)",
        "probe_class": "SYNTHETIC_DEVELOPMENT_PROBES written by the agent, one goal type each; not an evaluation corpus",
        "level_rule": "LEVEL1_BASE_ONLY = served with a solid; LEVEL2_GOAL_CONSTRUCTED = the studied object is in the scene "
                      "(angle: angle_construction or right-angle witness; distance: foot witness / segment; projection: derived foot; "
                      "section: section polygon; volume: the solid itself; height: certified altitude)",
        "before_levels": dict(Counter(r["before"]["level"] for r in rows)), "after_levels": dict(Counter(r["after"]["level"] for r in rows)),
        "changed": [{"probe": r["probe"], "before": r["before"]["level"], "after": r["after"]["level"]} for r in rows
                    if r["before"]["level"] != r["after"]["level"]],
        "rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"before": dict(Counter(r["before"]["level"] for r in rows)), "after": dict(Counter(r["after"]["level"] for r in rows))}, ensure_ascii=False))
    for r in rows:
        print(f"{r['probe']:28s} {r['before']['level']:40s} -> {r['after']['level']}")
    return 0


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
    else:
        raise SystemExit(main())
