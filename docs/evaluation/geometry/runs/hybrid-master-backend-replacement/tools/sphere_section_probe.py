"""Sphere sections on Route D /4 (seventh continuation, registry /25). DEVELOPMENT probe: oracles by hand BEFORE the code.
Offline, 0 provider calls; not held-out.  Usage: sphere_section_probe.py [out.json]

Sphere centre O, radius R; a plane at distance d from the centre cuts it in a circle with r'² = R² − d² (d < R), touches it
at ONE point (d = R: no area), or misses it (d > R).
  R = 5, d = 3 ⇒ r' = 4, S = 16π.     R = 5, d = 4 ⇒ r' = 3, S = 9π.     R = 5, d = 2 ⇒ r' = √21, S = 21π.
  R = 5, through the centre ⇒ r' = 5, S = 25π (a great circle).       R = 5a, d = 3a ⇒ S = 16π (unit a).
"""
import importlib.util, json, sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / 'backend'))
_s = importlib.util.spec_from_file_location("curved_section_probe", Path(__file__).with_name("curved_section_probe.py"))
SP = importlib.util.module_from_spec(_s)
_s.loader.exec_module(SP)
from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402
from app.simulation.geometry.radical import parse_exact  # noqa: E402

AREA, RADIUS, build, CP = SP.AREA, SP.RADIUS, SP.build, SP.CP


def sphere(r="5", centre="O", rim="A"):
    given = f"Cho mặt cầu tâm {centre}, điểm {rim} thuộc mặt cầu, bán kính bằng {r}."
    return given, CP.solid("sphere", centre, centre, None, rim, r, None, given[:-1])


def case(clause, kind, goal, question, r="5", tail="cắt mặt cầu theo một đường tròn", unit=None, **fields):
    given, sol = sphere(r)
    sent = f"Mặt phẳng (P) {clause} {tail}."
    sec = {"section_id": "td", "plane_name": "P", "target_solid_id": "k", "plane_kind": kind, "section_shape": "circle",
           "quote": sent.rstrip("."), **fields}
    p = build(given, sol, sent, sec, question, goal)
    if unit:
        p["length_unit"] = unit
    return p


A_Q, R_Q = "Tính diện tích của thiết diện.", "Tính bán kính của đường tròn giao tuyến."
CASES = [
    ("s.d3.area", case("cách tâm O một khoảng bằng 3", "at_distance_from_center", AREA, A_Q, distance_from_center="3"), "16π"),
    ("s.d3.radius", case("cách tâm O một khoảng bằng 3", "at_distance_from_center", RADIUS, R_Q, distance_from_center="3"), "4"),
    ("s.d4.area", case("cách tâm một khoảng 4", "at_distance_from_center", AREA, A_Q, distance_from_center="4"), "9π"),
    ("s.d2.radius_irrational", case("cách tâm O một khoảng bằng 2", "at_distance_from_center", RADIUS, R_Q,
                                    distance_from_center="2"), "√21"),
    ("s.d2.area_giao_tuyen", case("cách tâm O một khoảng bằng 2", "at_distance_from_center", AREA,
                                  "Tính diện tích hình tròn giao tuyến.", distance_from_center="2"), "21π"),
    ("s.centre.area", case("đi qua tâm O", "through_center", AREA, A_Q), "25π"),
    ("s.centre.radius", case("qua tâm O", "through_center", RADIUS, R_Q), "5"),
    ("s.unit_a.area", case("cách tâm O một khoảng bằng 3a", "at_distance_from_center", AREA, A_Q, r="5a", unit="a",
                           distance_from_center="3a"), "16π"),
]

NEGATIVES = [  # (id, payload, expected code)
    ("n.tangent_d_equals_R", case("cách tâm O một khoảng bằng 5", "at_distance_from_center", AREA, A_Q,
                                  distance_from_center="5"), "CURVED_PLANE_TANGENT"),
    ("n.misses_d_above_R", case("cách tâm O một khoảng bằng 6", "at_distance_from_center", AREA, A_Q,
                                distance_from_center="6"), "CURVED_PLANE_DOES_NOT_CUT"),
    ("n.distance_not_stated", case("cách tâm O một khoảng bằng 3", "at_distance_from_center", AREA, A_Q,
                                   distance_from_center="4"), "UNGROUNDED_VALUE"),
    ("n.other_centre", case("cách tâm I một khoảng bằng 3", "at_distance_from_center", AREA, A_Q,
                            distance_from_center="3"), "SOURCE_OBJECT_MISMATCH"),
    ("n.from_a_point_not_the_centre", case("cách điểm A một khoảng bằng 3", "at_distance_from_center", AREA, A_Q,
                                           distance_from_center="3"), "CURVED_WORDING_UNSUPPORTED"),
    ("n.centre_kind_but_distance_text", case("cách tâm O một khoảng bằng 3", "through_center", AREA, A_Q),
     "SOURCE_OBJECT_MISMATCH"),
    ("n.distance_kind_but_centre_text", case("đi qua tâm O", "at_distance_from_center", AREA, A_Q, distance_from_center="3"),
     "SOURCE_OBJECT_MISMATCH"),
    ("n.parallel_to_a_base", case("song song với đáy và cách đáy một khoảng bằng 3", "at_distance_from_center", AREA, A_Q,
                                  distance_from_center="3"), "SOURCE_OBJECT_MISMATCH"),
    ("n.tangent_wording", case("tiếp xúc với mặt cầu", "at_distance_from_center", AREA, A_Q, tail="tại điểm H",
                               distance_from_center="5"), "CURVED_WORDING_UNSUPPORTED"),
    ("n.base_kind_on_sphere", case("song song với đáy và cách đáy một khoảng bằng 3", "parallel_to_base_at_distance", AREA, A_Q,
                                   distance_from_base="3"), "BRIDGE_UNSUPPORTED_CURVED"),
]
# a centre-distance plane on a solid WITH an axis is not a sphere section: the bridge refuses before any binding
_cyl = deepcopy(SP.build(SP.CYL_G, SP.CYL_S, "Mặt phẳng (P) cách tâm O một khoảng bằng 1 cắt hình trụ theo một đường tròn.",
                         SP.section("at_distance_from_center", "Mặt phẳng (P) cách tâm O một khoảng bằng 1 cắt hình trụ theo một "
                                    "đường tròn", distance_from_center="1", section_shape="circle"), A_Q, AREA))
NEGATIVES.append(("n.centre_distance_on_cylinder", _cyl, "BRIDGE_UNSUPPORTED_CURVED"))


def run():
    rows = []
    for cid, p, oracle in CASES:
        r = run_typed_fact_next_v2_route(p)
        got = (r.answer_exact or {}).get("mg1") if r.status == "SERVED" else None
        ok = got is not None and parse_exact(got["coef"]) == parse_exact(oracle)
        rows.append({"id": cid, "status": r.status, "code": r.code, "answer": got, "oracle": oracle,
                     "outcome": "SERVED_CORRECT" if ok else ("WRONG_SERVED" if got else "REFUSED"), "reason": (r.reason or "")[:200]})
    for cid, p, want in NEGATIVES:
        r = run_typed_fact_next_v2_route(p)
        rows.append({"id": cid, "status": r.status, "code": r.code, "oracle": f"REFUSE:{want}",
                     "outcome": "WRONG_SERVED" if r.status == "SERVED" else ("REFUSED_CORRECT" if r.code == want else
                                                                             "REFUSED_OTHER_CODE"),
                     "reason": (r.reason or "")[:200]})
    return rows


if __name__ == "__main__":
    rows = run()
    for x in rows:
        print(f"{x['id']:34s} {x['status']:8s} {str(x['code']):30s} {x['oracle']:34s} {x['outcome']}  {x['reason'][:90]}")
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
            json.dump({"provider_calls": 0, "classification": "DEVELOPMENT_DIAGNOSTIC", "rows": rows}, f,
                      ensure_ascii=False, indent=1)
            f.write('\n')
