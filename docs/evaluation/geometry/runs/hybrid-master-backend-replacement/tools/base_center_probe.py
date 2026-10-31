"""Base-centre wording of curved solids on Route D /4 (seventh continuation, registry /25). DEVELOPMENT probe: oracles by
hand before the code; the first two wordings are those of the Adapter /3 fixtures /4 refused (`C.cone_base`, `C.cyl_base`).
Offline, 0 provider calls; not held-out.  Usage: base_center_probe.py [out.json]

Cone r = 3, h = 4 ⇒ V = 12π.  Cylinder r = 2, h = 3 ⇒ V = 12π.  Cone r = OB = 9, h = SO = 15 ⇒ V = 405π.
"""
import importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / 'backend'))
_s = importlib.util.spec_from_file_location("curved_probe", Path(__file__).with_name("curved_probe.py"))
CP = importlib.util.module_from_spec(_s)
_s.loader.exec_module(CP)
from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402
from app.simulation.geometry.radical import parse_exact  # noqa: E402


def cone(text, r="3", h="4", center="O", top="S", rim="A", notation="S.O"):
    q = text.rstrip(".")
    return (text, CP.solid("cone", notation, center, top, rim, r, h, q), [])


def cyl(text, r="2", h="3", center="O", top="O'", rim="A", notation="O.O'"):
    q = text.rstrip(".")
    return (text, CP.solid("cylinder", notation, center, top, rim, r, h, q), [])


V_CONE, V_CYL = ("volume", "Tính thể tích khối nón."), ("volume", "Tính thể tích khối trụ.")
CASES = [  # (id, figure, (goal, question), oracle | "REFUSE:<code>")
    ("b.cone.tam_day", cone("Cho hình nón đỉnh S, tâm đáy O, điểm A thuộc đường tròn đáy, bán kính đáy R = 3, chiều cao h = 4."),
     V_CONE, "12π"),
    ("b.cyl.day_duoi_tren", cyl("Cho hình trụ tròn xoay có tâm đáy dưới O, tâm đáy trên O', điểm A trên đường tròn đáy dưới, "
                                "bán kính đáy R = 2 và chiều cao h = 3."), V_CYL, "12π"),
    ("b.cone.day_co_tam", cone("Cho hình nón đỉnh S, đáy có tâm O, bán kính đáy bằng 3 và chiều cao bằng 4.", rim=None), V_CONE, "12π"),
    ("b.cone.duong_tron_day_tam", cone("Cho hình nón đỉnh S, đường tròn đáy tâm O, bán kính đáy bằng 3 và chiều cao bằng 4.", rim=None),
     V_CONE, "12π"),
    ("b.cyl.hai_day_co_tam", cyl("Cho hình trụ có hai đáy có tâm O và O', bán kính đáy bằng 2 và chiều cao bằng 3.", rim=None), V_CYL, "12π"),
    ("b.cyl.rim_circle_name", cyl("Cho hình trụ có tâm hai đáy là O và O', điểm A thuộc đường tròn đáy (O), bán kính đáy bằng 2, "
                                  "chiều cao bằng 3."), V_CYL, "12π"),
    ("b.cone.segments", cone("Cho hình nón đỉnh S có tâm đáy là O, điểm B thuộc đường tròn đáy, bán kính OB = 9 và chiều cao SO = 15.",
                             r="9", h="15", rim="B"), V_CONE, "405π"),
    # negatives
    ("n.cyl_single_base_ambiguous", cyl("Cho hình trụ có tâm đáy O, đỉnh O', bán kính đáy bằng 2 và chiều cao bằng 3.", rim=None),
     V_CYL, "REFUSE:AMBIGUOUS_REFERENCE"),
    ("n.cyl_lower_upper_swapped", cyl("Cho hình trụ tròn xoay có tâm đáy dưới O, tâm đáy trên O', bán kính đáy R = 2 và chiều cao h = 3.",
                                      center="O'", top="O", rim=None, notation="O'.O"), V_CYL, "REFUSE:SOURCE_OBJECT_MISMATCH"),
    ("n.cyl_rim_on_upper_base", cyl("Cho hình trụ tròn xoay có tâm đáy dưới O, tâm đáy trên O', điểm A trên đường tròn đáy trên, "
                                    "bán kính đáy R = 2 và chiều cao h = 3."), V_CYL, "REFUSE:SOURCE_OBJECT_MISMATCH"),
    ("n.cone_missing_height", cone("Cho hình nón đỉnh S, tâm đáy O, điểm A thuộc đường tròn đáy, bán kính đáy R = 3.", h=None),
     V_CONE, "REFUSE:MISSING_DIMENSION"),
    ("n.cone_two_base_centres", cone("Cho hình nón đỉnh S, tâm đáy O, tâm đáy I, bán kính đáy R = 3, chiều cao h = 4.", rim=None),
     V_CONE, "REFUSE:SOURCE_OBJECT_MISMATCH"),
    ("n.cone_contradictory_radius", cone("Cho hình nón đỉnh S, tâm đáy O, điểm B thuộc đường tròn đáy, bán kính đáy R = 3, "
                                         "bán kính OB = 4, chiều cao h = 4.", rim="B"), V_CONE, "REFUSE:INCONSISTENT_FACTS"),
    ("n.cone_height_is_slant", cone("Cho hình nón đỉnh S, tâm đáy O, điểm A thuộc đường tròn đáy, bán kính đáy R = 3, "
                                    "chiều cao SA = 5."), V_CONE, "REFUSE:SOURCE_OBJECT_MISMATCH"),
    ("n.cyl_prime_dropped", cyl("Cho hình trụ tròn xoay có tâm đáy dưới O, tâm đáy trên O', bán kính đáy R = 2 và chiều cao h = 3.",
                                top="O1", rim=None, notation="O.O1"), V_CYL, "REFUSE:UNKNOWN_LABEL"),
    ("n.cone_centre_of_other_object", cone("Cho hình nón đỉnh S, tâm đáy O, điểm A thuộc đường tròn tâm I, bán kính đáy R = 3, "
                                           "chiều cao h = 4."), V_CONE, "REFUSE:CURVED_WORDING_UNSUPPORTED"),
]


def run():
    rows = []
    for cid, fig, (gt, q), oracle in CASES:
        r = run_typed_fact_next_v2_route(CP.payload(fig, gt, q))
        got = (r.answer_exact or {}).get("mg1") if r.status == "SERVED" else None
        if oracle.startswith("REFUSE"):
            want = oracle.split(":", 1)[1]
            outcome = ("REFUSED_CORRECT" if r.code == want else "REFUSED_OTHER_CODE") if got is None else "WRONG_SERVED"
        else:
            outcome = ("SERVED_CORRECT" if parse_exact(got["coef"]) == parse_exact(oracle) else "WRONG_SERVED") if got else "REFUSED"
        rows.append({"id": cid, "status": r.status, "code": r.code, "answer": got, "oracle": oracle, "outcome": outcome,
                     "reason": (r.reason or "")[:200]})
    return rows


if __name__ == "__main__":
    rows = run()
    for x in rows:
        print(f"{x['id']:32s} {x['status']:8s} {str(x['code']):34s} {x['oracle']:38s} {x['outcome']}")
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
            json.dump({"provider_calls": 0, "classification": "DEVELOPMENT_DIAGNOSTIC", "rows": rows}, f,
                      ensure_ascii=False, indent=1)
            f.write('\n')
