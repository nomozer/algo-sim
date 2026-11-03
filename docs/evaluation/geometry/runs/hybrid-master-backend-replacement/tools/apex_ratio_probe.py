"""General apex ratio k for cone sections on Route D /4 (seventh continuation, registry /25). DEVELOPMENT probe; oracles
by hand before the code. Offline, 0 provider calls; not held-out.  Usage: apex_ratio_probe.py [out.json]

Cone S.O, r = 3, h = 4, V = 12π. With k = SM/SO (from the apex): r' = k·r, S = π(kr)², V_small = k³V, rest = (1 − k³)V.
  SM/SO = 1/3  ⇒ r' = 1,   S = π,      ratio small:original = 1/27, rest = 104π/9.
  OM/OS = 1/4  ⇒ SM/SO = 3/4 ⇒ S = 81π/16, ratio = 27/64.
  2/3 from the apex ⇒ r' = 2, S = 4π, ratio = 8/27, rest = 76π/9.
  r = 3a, h = 4a, SM/SO = 1/3 ⇒ S = πa², ratio = 1/27.
"""
import importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / 'backend'))
_s = importlib.util.spec_from_file_location("curved_section_probe", Path(__file__).with_name("curved_section_probe.py"))
SP = importlib.util.module_from_spec(_s)
_s.loader.exec_module(SP)
from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402
from app.simulation.geometry.radical import parse_exact  # noqa: E402

AREA, CONE_G, CONE_S, build, section, CP = SP.AREA, SP.CONE_G, SP.CONE_S, SP.build, SP.section, SP.CP
DERIVED = "Mặt phẳng (P) chia hình nón thành một khối nón nhỏ đỉnh S và một khối nón cụt."
RATIO = {"kind": "volume_ratio", "numerator_solid_id": "kn", "denominator_solid_id": "k"}
REST = {"kind": "residual_volume", "parent_solid_id": "k", "cut_solid_id": "kn"}


def ratio_case(clause, k, goal, question, point=None, derived=False, given=CONE_G, sol=CONE_S):
    sent = f"Mặt phẳng (P) song song với đáy {clause}, cắt hình nón theo một đường tròn."
    sec = section("parallel_to_base_at_ratio", sent.rstrip("."), ratio_from_apex=k, section_shape="circle")
    if point:
        sec["through_point"] = point
    return build(given, sol, sent + (" " + DERIVED if derived else ""), sec, question, goal,
                 derived=DERIVED.rstrip(".") if derived else None)


SM13 = "và cắt SO tại M sao cho SM/SO = 1/3"
CASES = [
    ("k.13.area", ratio_case(SM13, "1/3", AREA, "Tính diện tích thiết diện.", point="M"), "π"),
    ("k.13.ratio", ratio_case(SM13, "1/3", RATIO, "Tính tỉ số thể tích của khối nón nhỏ và khối nón ban đầu.", point="M",
                              derived=True), "1/27"),
    ("k.13.rest", ratio_case(SM13, "1/3", REST, "Tính thể tích của khối nón cụt.", point="M", derived=True), "104π/9"),
    ("k.from_base.area", ratio_case("và cắt SO tại M sao cho OM/OS = 1/4", "3/4", AREA, "Tính diện tích thiết diện.",
                                    point="M"), "81π/16"),
    ("k.from_base.ratio", ratio_case("và cắt SO tại M sao cho OM/OS = 1/4", "3/4", RATIO,
                                     "Tính tỉ số thể tích của khối nón nhỏ và khối nón ban đầu.", point="M", derived=True), "27/64"),
    ("k.23.area", ratio_case("cắt trục SO theo tỉ lệ 2/3 tính từ đỉnh S", "2/3", AREA, "Tính diện tích thiết diện."), "4π"),
    ("k.23.ratio", ratio_case("cắt trục SO theo tỉ lệ 2/3 tính từ đỉnh S", "2/3", RATIO,
                              "Tính tỉ số thể tích của khối nón nhỏ và khối nón ban đầu.", derived=True), "8/27"),
    ("k.23.rest", ratio_case("cắt trục SO theo tỉ lệ 2/3 tính từ đỉnh S", "2/3", REST, "Tính thể tích của khối nón cụt.",
                             derived=True), "76π/9"),
    ("k.half.still", ratio_case("và đi qua trung điểm của đường cao SO", "1/2", AREA, "Tính diện tích thiết diện."), "9π/4"),
]
_ga = "Cho hình nón đỉnh S, đáy là đường tròn tâm O, điểm A thuộc đường tròn đáy, bán kính đáy bằng 3a và chiều cao bằng 4a."
_sa = CP.solid("cone", "S.O", "O", "S", "A", "3a", "4a", _ga[:-1])
for cid, goal, q, o in (("k.unit_a.area", AREA, "Tính diện tích thiết diện.", "π"),
                        ("k.unit_a.ratio", RATIO, "Tính tỉ số thể tích của khối nón nhỏ và khối nón ban đầu.", "1/27")):
    pa = ratio_case(SM13, "1/3", goal, q, point="M", derived=goal is RATIO, given=_ga, sol=_sa)
    pa["length_unit"] = "a"
    CASES.append((cid, pa, o))

NEGATIVES = [  # (id, payload, expected code)
    ("n.k_is_one_base", ratio_case("và cắt SO tại M sao cho SM/SO = 1", "1/1", AREA, "Tính diện tích thiết diện.", point="M"),
     "CURVED_SECTION_IS_A_BASE"),
    ("n.k_above_one", ratio_case("và cắt SO tại M sao cho SM/SO = 3/2", "3/2", AREA, "Tính diện tích thiết diện.", point="M"),
     "CURVED_PLANE_DOES_NOT_CUT"),
    ("n.from_base_not_converted", ratio_case("và cắt SO tại M sao cho OM/OS = 1/4", "1/4", AREA, "Tính diện tích thiết diện.",
                                             point="M"), "UNGROUNDED_VALUE"),
    ("n.wrong_segment", ratio_case("và cắt SA tại M sao cho SM/SA = 1/3", "1/3", AREA, "Tính diện tích thiết diện.", point="M"),
     "SOURCE_OBJECT_MISMATCH"),
    ("n.point_identity", ratio_case(SM13, "1/3", AREA, "Tính diện tích thiết diện.", point="N"), "UNKNOWN_LABEL"),
    ("n.point_dropped", ratio_case(SM13, "1/3", AREA, "Tính diện tích thiết diện."), "UNGROUNDED_VALUE"),
    ("n.ratio_and_distance", ratio_case("và cách đáy một khoảng bằng 1 và cắt SO tại M sao cho SM/SO = 1/3", "1/3", AREA,
                                        "Tính diện tích thiết diện.", point="M"), "SOURCE_OBJECT_MISMATCH"),
    ("n.from_off_axis_vertex", ratio_case("cắt trục SO theo tỉ lệ 2/3 tính từ đỉnh A", "2/3", AREA, "Tính diện tích thiết diện."),
     "SOURCE_OBJECT_MISMATCH"),
    ("n.ratio_inverted_question", ratio_case(SM13, "1/3", RATIO, "Tính tỉ số thể tích của khối nón ban đầu và khối nón nhỏ.",
                                             point="M", derived=True), "SOURCE_OBJECT_MISMATCH"),
]


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
        served = r.status == "SERVED"
        rows.append({"id": cid, "status": r.status, "code": r.code, "oracle": f"REFUSE:{want}",
                     "outcome": "WRONG_SERVED" if served else ("REFUSED_CORRECT" if r.code == want else "REFUSED_OTHER_CODE"),
                     "reason": (r.reason or "")[:200]})
    return rows


if __name__ == "__main__":
    rows = run()
    for x in rows:
        print(f"{x['id']:28s} {x['status']:8s} {str(x['code']):34s} {x['oracle']:32s} {x['outcome']}")
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
            json.dump({"provider_calls": 0, "classification": "DEVELOPMENT_DIAGNOSTIC", "rows": rows}, f,
                      ensure_ascii=False, indent=1)
            f.write('\n')
