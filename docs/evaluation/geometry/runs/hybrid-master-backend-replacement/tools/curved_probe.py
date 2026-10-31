"""Curved-solid DEVELOPMENT probe for Route D /4 (fifth continuation, Owner option (b)). Each oracle is written by hand
before any implementation, in the `radical.parse_exact` grammar (π kept). Offline, 0 provider calls; not held-out.
Usage: curved_probe.py [out.json]

Formulas (closed form, by hand): cylinder V = πr²h, S_xq = 2πrh, S_tp = 2πrh + 2πr²; oracles write π before √ ("4π√2", the parse_exact grammar); cone V = πr²h/3, l² = r² + h²,
S_xq = πrl, S_tp = πrl + πr²; sphere S = 4πR², V = 4πR³/3. A total area with two unlike radical terms is outside the exact
single-term domain (a·π·√b) and must be a TYPED refusal, never an approximation.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / 'backend'))
from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402
from app.simulation.geometry.radical import from_json, parse_exact  # noqa: E402


def solid(kind, notation, center, top, rim, radius, height, quote):
    s = {"solid_id": "k", "solid_type": kind, "notation": notation, "center": center, "rim_point": rim,
         "radius": radius, "quote": quote}
    s = {k: v for k, v in s.items() if v is not None}
    if top:
        s["apex_or_top"] = top
    if height:
        s["height"] = height
    return s


CYL = ("Cho hình trụ có tâm hai đáy là O và O', điểm A thuộc đường tròn đáy tâm O, bán kính đáy bằng 3 và chiều cao bằng 5.",
       solid("cylinder", "O.O'", "O", "O'", "A", "3", "5",
             "Cho hình trụ có tâm hai đáy là O và O', điểm A thuộc đường tròn đáy tâm O, bán kính đáy bằng 3 và chiều cao bằng 5"),
       [])
CONE = ("Cho hình nón đỉnh S, đáy là đường tròn tâm O, điểm A thuộc đường tròn đáy, bán kính đáy bằng 3 và chiều cao bằng 4.",
        solid("cone", "S.O", "O", "S", "A", "3", "4",
              "Cho hình nón đỉnh S, đáy là đường tròn tâm O, điểm A thuộc đường tròn đáy, bán kính đáy bằng 3 và chiều cao bằng 4"),
        [])
# slant given instead of the height: h² = SA² − OA² = 25 − 9 must be DERIVED (recomposition over named points)
CONE_L = ("Cho hình nón đỉnh S, đáy là đường tròn tâm O, điểm A thuộc đường tròn đáy, bán kính đáy bằng 3. Đường sinh SA = 5.",
          solid("cone", "S.O", "O", "S", "A", "3", None,
                "Cho hình nón đỉnh S, đáy là đường tròn tâm O, điểm A thuộc đường tròn đáy, bán kính đáy bằng 3"),
          [{"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "5"}, "quote": "Đường sinh SA = 5",
            "solid_id": "k"}])
CONE_R = ("Cho hình nón đỉnh S, đáy là đường tròn tâm O, điểm A thuộc đường tròn đáy, bán kính đáy bằng 2 và chiều cao bằng 2.",
          solid("cone", "S.O", "O", "S", "A", "2", "2",
                "Cho hình nón đỉnh S, đáy là đường tròn tâm O, điểm A thuộc đường tròn đáy, bán kính đáy bằng 2 và chiều cao bằng 2"),
          [])
SPH = ("Cho mặt cầu tâm O, điểm A thuộc mặt cầu, bán kính bằng 3.",
       solid("sphere", "O", "O", None, "A", "3", None, "Cho mặt cầu tâm O, điểm A thuộc mặt cầu, bán kính bằng 3"), [])
CYL_R = ("Cho hình trụ có tâm hai đáy là O và O', điểm A thuộc đường tròn đáy tâm O, bán kính đáy bằng √2 và chiều cao bằng 3.",
         solid("cylinder", "O.O'", "O", "O'", "A", "√2", "3",
               "Cho hình trụ có tâm hai đáy là O và O', điểm A thuộc đường tròn đáy tâm O, bán kính đáy bằng √2 và chiều cao bằng 3"),
         [])

# (id, figure, goal_type, question, expected): expected = exact oracle string, or "REFUSE"
CASES = [
    ("cyl.V", CYL, "volume", "Tính thể tích khối trụ.", "45π"),
    ("cyl.Sxq", CYL, "lateral_area", "Tính diện tích xung quanh của hình trụ.", "30π"),
    ("cyl.Stp", CYL, "area", "Tính diện tích toàn phần của hình trụ.", "48π"),
    ("cyl.r", CYL, "radius", "Tính bán kính đáy của hình trụ.", "3"),
    ("cone.V", CONE, "volume", "Tính thể tích khối nón.", "12π"),
    ("cone.Sxq", CONE, "lateral_area", "Tính diện tích xung quanh của hình nón.", "15π"),
    ("cone.Stp", CONE, "area", "Tính diện tích toàn phần của hình nón.", "24π"),
    ("coneL.V", CONE_L, "volume", "Tính thể tích khối nón.", "12π"),
    ("coneL.Sxq", CONE_L, "lateral_area", "Tính diện tích xung quanh của hình nón.", "15π"),
    ("coneR.Sxq", CONE_R, "lateral_area", "Tính diện tích xung quanh của hình nón.", "4π√2"),
    ("coneR.V", CONE_R, "volume", "Tính thể tích khối nón.", "8π/3"),
    ("sph.S", SPH, "area", "Tính diện tích mặt cầu.", "36π"),
    ("sph.V", SPH, "volume", "Tính thể tích khối cầu.", "36π"),
    ("cylR.V", CYL_R, "volume", "Tính thể tích khối trụ.", "6π"),
    ("cylR.Sxq", CYL_R, "lateral_area", "Tính diện tích xung quanh của hình trụ.", "6π√2"),
    ("cylR.Stp", CYL_R, "area", "Tính diện tích toàn phần của hình trụ.", "REFUSE"),     # 6√2π + 4π: two unlike terms
]


def payload(fig, goal_type, question, mutate=None):
    given, s, premises = fig
    target = {"solid_id": "k"} if goal_type == "volume" else {"solid": s["notation"]}
    p = {"schema_version": "typed-fact-next/2", "problem_text": f"{given} {question}", "length_unit": "1",
         "solids": [dict(s)], "premises": [dict(x) for x in premises], "derived_sections": [], "relations": [],
         "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "k", "quote": s["quote"]}],
         "math_goals": [{"goal_id": "mg1", "kind": "measurement", "goal_type": goal_type, "target": target,
                         "quote": question.rstrip(".")}]}
    if mutate:
        mutate(p)
    return p


def bad_slant(p):          # l = 3 < r = 3? equal ⇒ h = 0: contradictory data
    p["premises"][0] = {**p["premises"][0], "args": {"segment": ["S", "A"], "value": "3"}, "quote": "Đường sinh SA = 3"}
    p["problem_text"] = p["problem_text"].replace("SA = 5", "SA = 3")


def overdetermined(p):     # r = 3, h = 4 stated AND SA = 6 ≠ 5: contradictory, never pick one
    p["premises"].append({"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "6"}, "quote": "SA = 6",
                          "solid_id": "k"})
    p["problem_text"] = p["problem_text"].replace("chiều cao bằng 4.", "chiều cao bằng 4. SA = 6.")


def wrong_value(p):        # payload radius disagrees with the text
    p["solids"][0]["radius"] = "4"


def no_height(p):          # cylinder volume without a height: missing data
    p["solids"][0].pop("height")


def foreign_solid(p):      # the goal names a solid that is not declared
    p["math_goals"][0]["target"] = {"solid_id": "other"}


def swapped(p):            # radius and height exchanged against the text (r = 3, h = 5)
    p["solids"][0].update(radius="5", height="3")


def no_height_text(p):     # the source states no height: a cylinder volume is underdetermined
    q = "Cho hình trụ có tâm hai đáy là O và O', điểm A thuộc đường tròn đáy tâm O, bán kính đáy bằng 3"
    p["problem_text"] = q + ". Tính thể tích khối trụ."
    p["solids"][0].update(quote=q)
    p["solids"][0].pop("height")
    p["simulation_goals"][0]["quote"] = q


def composite(p):          # a pyramid in the same problem: no certified curved–polyhedral relation yet
    p["problem_text"] += " Cho hình chóp S.ABC."
    p["solids"].append({"solid_id": "c2", "solid_type": "pyramid", "notation": "S.ABC", "quote": "Cho hình chóp S.ABC"})


def foreign_segment(p):    # a length to a point the cone does not own
    p["premises"][0] = {**p["premises"][0], "args": {"segment": ["S", "B"], "value": "5"}, "quote": "Đường sinh SB = 5"}
    p["problem_text"] = p["problem_text"].replace("SA = 5", "SB = 5")


NEGATIVES = [("n.bad_slant", CONE_L, "volume", "Tính thể tích khối nón.", bad_slant),
             ("n.swapped", CYL, "volume", "Tính thể tích khối trụ.", swapped),
             ("n.wrong_kind", CYL, "volume", "Tính thể tích khối nón.", None),
             ("n.missing_height", CYL, "volume", "Tính thể tích khối trụ.", no_height_text),
             ("n.sphere_lateral", SPH, "lateral_area", "Tính diện tích xung quanh của mặt cầu.", None),
             ("n.area_unqualified", CYL, "area", "Tính diện tích của hình trụ.", None),
             ("n.composite", CYL, "volume", "Tính thể tích khối trụ.", composite),
             ("n.foreign_segment", CONE_L, "volume", "Tính thể tích khối nón.", foreign_segment),
             ("n.overdetermined", CONE, "volume", "Tính thể tích khối nón.", overdetermined),
             ("n.wrong_value", CYL, "volume", "Tính thể tích khối trụ.", wrong_value),
             ("n.no_height", CYL, "volume", "Tính thể tích khối trụ.", no_height),
             ("n.foreign_solid", CYL, "volume", "Tính thể tích khối trụ.", foreign_solid)]


def seg(a, b, v, q):
    return {"kind": "segment_length", "args": {"segment": [a, b], "value": v}, "quote": q, "solid_id": "k"}


_CYL = "Cho hình trụ có tâm hai đáy là O và O', điểm A thuộc đường tròn đáy tâm O"
_CONE = "Cho hình nón đỉnh S, đáy là đường tròn tâm O, điểm A thuộc đường tròn đáy"
#: Independent review of the curved slice (round 1): each served a WRONG exact value or served insufficient data. Every one
#: must now be REFUSED. (id, given, solid, premises, goal, question)
ADVERSARIAL = [
    ("r.radius_times_h", f"{_CYL}, chiều cao bằng 2 và bán kính đáy bằng 3 lần chiều cao.",
     solid("cylinder", "O.O'", "O", "O'", "A", "3", "2", f"{_CYL}, chiều cao bằng 2 và bán kính đáy bằng 3 lần chiều cao"), [],
     "volume", "Tính thể tích khối trụ."),
    ("r.radius_fraction_of_h", f"{_CYL}, chiều cao bằng 6 và bán kính đáy bằng 1/3 chiều cao.",
     solid("cylinder", "O.O'", "O", "O'", "A", "1/3", "6", f"{_CYL}, chiều cao bằng 6 và bán kính đáy bằng 1/3 chiều cao"), [],
     "volume", "Tính thể tích khối trụ."),
    ("r.radius_sum", f"{_CYL}, bán kính đáy bằng 3 + √2 và chiều cao bằng 5.",
     solid("cylinder", "O.O'", "O", "O'", "A", "3", "5", f"{_CYL}, bán kính đáy bằng 3 + √2 và chiều cao bằng 5"), [],
     "volume", "Tính thể tích khối trụ."),
    ("r.cyl_rim_on_other_base", "Cho hình trụ có tâm hai đáy là O và O', điểm A thuộc đường tròn đáy tâm O', chiều cao bằng 4. Biết OA = 5.",
     solid("cylinder", "O.O'", "O", "O'", "A", None, "4",
           "Cho hình trụ có tâm hai đáy là O và O', điểm A thuộc đường tròn đáy tâm O', chiều cao bằng 4"),
     [seg("O", "A", "5", "Biết OA = 5")], "volume", "Tính thể tích khối trụ."),
    ("r.cone_apex_centre_swapped", f"{_CONE}, chiều cao bằng 4. Đường sinh SA = 5.",
     solid("cone", "S.O", "S", "O", "A", None, "4", f"{_CONE}, chiều cao bằng 4"),
     [seg("S", "A", "5", "Đường sinh SA = 5")], "volume", "Tính thể tích khối nón."),
    ("r.sphere_point_outside", "Cho mặt cầu tâm O, điểm A nằm ngoài mặt cầu, OA = 5.",
     solid("sphere", "O", "O", None, "A", None, None, "Cho mặt cầu tâm O, điểm A nằm ngoài mặt cầu"),
     [seg("O", "A", "5", "OA = 5")], "volume", "Tính thể tích khối cầu."),
    ("r.cyl_point_on_axis", "Cho hình trụ có tâm hai đáy là O và O', chiều cao bằng 4. Điểm A thuộc đoạn OO' sao cho OA = 3.",
     solid("cylinder", "O.O'", "O", "O'", "A", None, "4", "Cho hình trụ có tâm hai đáy là O và O', chiều cao bằng 4"),
     [seg("O", "A", "3", "Điểm A thuộc đoạn OO' sao cho OA = 3")], "volume", "Tính thể tích khối trụ."),
    ("r.height_of_a_triangle", f"{_CONE}, bán kính đáy bằng 3, tam giác SAB có chiều cao bằng 2.",
     solid("cone", "S.O", "O", "S", "A", "3", "2", f"{_CONE}, bán kính đáy bằng 3, tam giác SAB có chiều cao bằng 2"), [],
     "volume", "Tính thể tích khối nón."),
    ("r.dimensions_of_another_solid", f"{_CONE} và một hình trụ có bán kính đáy bằng 3, chiều cao bằng 4.",
     solid("cone", "S.O", "O", "S", "A", "3", "4", f"{_CONE} và một hình trụ có bán kính đáy bằng 3, chiều cao bằng 4"), [],
     "volume", "Tính thể tích khối nón."),
    ("r.notation_against_roles", f"{_CONE}, bán kính đáy bằng 3 và chiều cao bằng 4.",
     solid("cone", "S.O", "S", "O", "A", "3", "4", f"{_CONE}, bán kính đáy bằng 3 và chiều cao bằng 4"), [],
     "volume", "Tính thể tích khối nón."),
    ("r.invented_labels", "Cho hình nón có bán kính đáy bằng 3 và chiều cao bằng 4.",
     solid("cone", "S.O", "O", "S", "A", "3", "4", "Cho hình nón có bán kính đáy bằng 3 và chiều cao bằng 4"), [],
     "volume", "Tính thể tích khối nón."),
]

def _cone(tail, r, h, kind_q=None):
    q = (kind_q or _CONE) + tail
    return solid("cone", "S.O", "O", "S", "A", r, h, q), q


#: Independent review round 2: the blacklist guard still served these; the closed clause grammar refuses them.
for _cid, _tail, _r, _h in (
        ("r2.second_cone_same_kind", ", bán kính đáy bằng 3 và một hình nón khác có chiều cao bằng 4", "3", "4"),
        ("r2.plane_section_circle", ", chiều cao bằng 4, mặt phẳng (P) song song với đáy cắt hình nón theo đường tròn có bán kính bằng 2", "2", "4"),
        ("r2.sector_radius", ", chiều cao bằng 4, được cuộn từ một hình quạt có bán kính bằng 5", "5", "4"),
        ("r2.unread_qualifier", ", bán kính đáy bằng 2, chiều cao bằng 3 và gấp đôi bán kính", "2", "3")):
    _s, _q = _cone(_tail, _r, _h)
    ADVERSARIAL.append((_cid, _q + ".", _s, [], "volume", "Tính thể tích khối nón."))
_q = "Cho tam giác SAB có chiều cao bằng 4 và hình nón đỉnh S, đáy là đường tròn tâm O, điểm A thuộc đường tròn đáy, bán kính đáy bằng 3"
ADVERSARIAL.append(("r2.object_before_kind_word", _q + ".", solid("cone", "S.O", "O", "S", "A", "3", "4", _q), [], "volume",
                    "Tính thể tích khối nón."))
_q = "Cho hình nón có bán kính đáy bằng 3 và chiều cao bằng 4"
ADVERSARIAL.append(("r2.notation_not_written", _q + ".", {"solid_id": "k", "solid_type": "cone", "notation": "(N)", "radius": "3",
                                                          "height": "4", "quote": _q}, [], "volume", "Tính thể tích khối nón."))
#: Over-refusals the review flagged, now served: the rim on the O' circle (centre O', top O) and "chiều cao của hình nón".
_q = "Cho hình trụ có tâm hai đáy là O và O', điểm A thuộc đường tròn đáy tâm O', bán kính đáy bằng 3 và chiều cao bằng 5"
CYL_TOP_RIM = (_q + ".", solid("cylinder", "O'.O", "O'", "O", "A", "3", "5", _q), [])
CONE_OF = (f"{_CONE}, bán kính đáy bằng 3 và chiều cao của hình nón bằng 4.",
           solid("cone", "S.O", "O", "S", "A", "3", "4", f"{_CONE}, bán kính đáy bằng 3 và chiều cao của hình nón bằng 4"), [])
CASES += [("cylTop.V", CYL_TOP_RIM, "volume", "Tính thể tích khối trụ.", "45π"),
          ("coneOf.V", CONE_OF, "volume", "Tính thể tích khối nón.", "12π")]
#: Labels are optional, never invented: a source that names no point is served in the canonical pose.
UNLABELLED = ("Cho hình nón (N) có bán kính đáy bằng 3 và chiều cao bằng 4.",
              {"solid_id": "k", "solid_type": "cone", "notation": "(N)", "radius": "3", "height": "4",
               "quote": "Cho hình nón (N) có bán kính đáy bằng 3 và chiều cao bằng 4"}, [])


def run():
    rows = []
    for cid, fig, gt, q, expected in CASES:
        r = run_typed_fact_next_v2_route(payload(fig, gt, q))
        got = (r.answer_exact or {}).get("mg1") if r.status == "SERVED" else None
        if expected == "REFUSE":
            outcome = "REFUSED_CORRECT" if got is None else "WRONG_SERVED"
        elif got is None:
            outcome = "REFUSED"
        else:
            outcome = "SERVED_CORRECT" if parse_exact(got["coef"]) == parse_exact(expected) else "WRONG_SERVED"
        rows.append({"id": cid, "status": r.status, "code": r.code, "answer": got, "oracle": expected,
                     "outcome": outcome, "reason": (r.reason or "")[:200]})
    for cid, fig, gt, q, mutate in NEGATIVES:
        r = run_typed_fact_next_v2_route(payload(fig, gt, q, mutate))
        outcome = "REFUSED_CORRECT" if r.status != "SERVED" and not r.answer_exact else "SERVED_NEGATIVE"
        rows.append({"id": cid, "status": r.status, "code": r.code, "outcome": outcome, "reason": (r.reason or "")[:200]})
    for cid, given, s, prem, gt, q in ADVERSARIAL:
        r = run_typed_fact_next_v2_route(payload((given, s, prem), gt, q))
        rows.append({"id": cid, "status": r.status, "code": r.code, "reason": (r.reason or "")[:200],
                     "outcome": "REFUSED_CORRECT" if r.status != "SERVED" and not r.answer_exact else "SERVED_NEGATIVE"})
    r = run_typed_fact_next_v2_route(payload(UNLABELLED, "volume", "Tính thể tích khối nón."))
    got = (r.answer_exact or {}).get("mg1")
    rows.append({"id": "u.unlabelled_cone.V", "status": r.status, "code": r.code, "answer": got, "oracle": "12π",
                 "outcome": "SERVED_CORRECT" if got and parse_exact(got["coef"]) == parse_exact("12π") else "REFUSED"})
    return rows


if __name__ == "__main__":
    rows = run()
    for x in rows:
        print(f"{x['id']:16s} {x['status']:8s} {str(x['code']):34s} {x.get('answer')} oracle {x.get('oracle')} {x['outcome']}")
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
            json.dump({"provider_calls": 0, "classification": "DEVELOPMENT_DIAGNOSTIC", "rows": rows}, f,
                      ensure_ascii=False, indent=1)
            f.write('\n')
