"""Curved SECTIONS and cone volume ratios on Route D /4 (sixth continuation). DEVELOPMENT probe; oracles written by hand
BEFORE the implementation, in the `radical.parse_exact` grammar (π before √). Offline, 0 provider calls; not held-out.
Usage: curved_section_probe.py [out.json]

Figures (from `curved_probe.py`): cylinder O.O', r = 3, h = 5; cone S.O, r = 3, h = 4 (slant 5).
• Plane ∥ base at distance d from the base: cylinder → circle r' = r, S = 9π; cone → r' = r(h − d)/h.
  cone d = 1 → r' = 9/4, S = 81π/16; cone through the midpoint of SO (k = SI/SO = 1/2) → r' = 3/2, S = 9π/4.
• Axial section: cylinder → rectangle 2r × h = 30; cone → isosceles triangle ½·2r·h = 12.
• Cone cut at d = 2 (k = (h − d)/h = 1/2): V = 12π, V_small = k³V = 3π/2, ratio small : original = 1/8 (inverse 8),
  remaining (frustum) = V − V_small = 21π/2.
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

CYL_G, CYL_S = CP.CYL[0], CP.CYL[1]
CONE_G, CONE_S = CP.CONE[0], CP.CONE[1]


def section(kind, quote, **kw):
    return {"section_id": "td", "plane_name": "P", "target_solid_id": "k", "plane_kind": kind, "quote": quote, **kw}


def build(given, sol, sec_sentence, sec, question, goal, derived=None):
    text = f"{given} {sec_sentence} {question}"
    sim = [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "k", "quote": sol["quote"]},
           {"goal_id": "sg2", "kind": "construct_plane_section", "target_section_id": "td", "quote": sec["quote"]}]
    if derived:
        sim.append({"goal_id": "sg3", "kind": "construct_derived_solid", "derived_solid_id": "kn", "target_section_id": "td",
                    "apex_ref": "S", "quote": derived})
    return {"schema_version": "typed-fact-next/2", "problem_text": text, "length_unit": "1", "solids": [dict(sol)],
            "premises": [], "derived_sections": [sec], "relations": [], "simulation_goals": sim,
            "math_goals": [{**goal, "goal_id": "mg1", "quote": question.rstrip(".")}]}


AREA = {"kind": "measurement", "goal_type": "area", "target": {"section_id": "td"}}
RADIUS = {"kind": "measurement", "goal_type": "radius", "target": {"section_id": "td"}}
SEC_CYL = "Mặt phẳng (P) song song với đáy và cách đáy một khoảng bằng 2 cắt hình trụ theo một đường tròn."
SEC_CONE1 = "Mặt phẳng (P) song song với đáy và cách đáy một khoảng bằng 1 cắt hình nón theo một đường tròn."
SEC_CONE_MID = "Mặt phẳng (P) song song với đáy và đi qua trung điểm của đường cao SO cắt hình nón theo một đường tròn."
SEC_CONE2 = "Mặt phẳng (P) song song với đáy và cách đáy một khoảng bằng 2 cắt hình nón theo một đường tròn."
AX_CYL = "Cắt hình trụ bởi một mặt phẳng đi qua trục."
AX_CONE = "Cắt hình nón bởi một mặt phẳng đi qua trục."
DERIVED = "Mặt phẳng (P) chia hình nón thành một khối nón nhỏ đỉnh S và một khối nón cụt."


def dist(d, s):
    return section("parallel_to_base_at_distance", s.rstrip("."), distance_from_base=d, section_shape="circle")


CASES = [  # (id, payload, oracle or "REFUSE")
    ("cyl.par.S", build(CYL_G, CYL_S, SEC_CYL, dist("2", SEC_CYL), "Tính diện tích thiết diện.", AREA), "9π"),
    ("cyl.par.r", build(CYL_G, CYL_S, SEC_CYL, dist("2", SEC_CYL), "Tính bán kính của đường tròn thiết diện.", RADIUS), "3"),
    ("cone.par.S", build(CONE_G, CONE_S, SEC_CONE1, dist("1", SEC_CONE1), "Tính diện tích thiết diện.", AREA), "81π/16"),
    ("cone.par.r", build(CONE_G, CONE_S, SEC_CONE1, dist("1", SEC_CONE1), "Tính bán kính của đường tròn thiết diện.", RADIUS), "9/4"),
    ("cone.mid.S", build(CONE_G, CONE_S, SEC_CONE_MID,
                         section("parallel_to_base_at_ratio", SEC_CONE_MID.rstrip("."), ratio_from_apex="1/2",
                                 section_shape="circle"), "Tính diện tích thiết diện.", AREA), "9π/4"),
    ("cyl.ax.S", build(CYL_G, CYL_S, AX_CYL, section("axial_section", AX_CYL.rstrip("."), section_shape="polygon", plane_name="α"),
                       "Tính diện tích thiết diện.", AREA), "30"),
    ("cone.ax.S", build(CONE_G, CONE_S, AX_CONE, section("axial_section", AX_CONE.rstrip("."), section_shape="polygon", plane_name="α"),
                        "Tính diện tích thiết diện.", AREA), "12"),
    ("cone.ratio", build(CONE_G, CONE_S, SEC_CONE2 + " " + DERIVED, dist("2", SEC_CONE2),
                         "Tính tỉ số thể tích của khối nón nhỏ và khối nón ban đầu.",
                         {"kind": "volume_ratio", "numerator_solid_id": "kn", "denominator_solid_id": "k"},
                         derived=DERIVED.rstrip(".")), "1/8"),
    ("cone.ratio.inverse", build(CONE_G, CONE_S, SEC_CONE2 + " " + DERIVED, dist("2", SEC_CONE2),
                                 "Tính tỉ số thể tích của khối nón ban đầu và khối nón nhỏ.",
                                 {"kind": "volume_ratio", "numerator_solid_id": "k", "denominator_solid_id": "kn"},
                                 derived=DERIVED.rstrip(".")), "8"),
    ("cone.residual", build(CONE_G, CONE_S, SEC_CONE2 + " " + DERIVED, dist("2", SEC_CONE2),
                            "Tính thể tích của khối nón cụt.",
                            {"kind": "residual_volume", "parent_solid_id": "k", "cut_solid_id": "kn"},
                            derived=DERIVED.rstrip(".")), "21π/2"),
]


def _neg(cid, payload, mutate):
    mutate(payload)
    return (cid, payload, "REFUSE")


def _set(path_fn):
    return path_fn


NEGATIVES = [
    # the plane misses the solid / touches it: never a section
    _neg("n.cyl.d_above", build(CYL_G, CYL_S, SEC_CYL.replace("bằng 2", "bằng 7"), dist("7", SEC_CYL.replace("bằng 2", "bằng 7")),
                                "Tính diện tích thiết diện.", AREA), lambda p: None),
    _neg("n.cone.at_apex", build(CONE_G, CONE_S, SEC_CONE1.replace("bằng 1", "bằng 4"), dist("4", SEC_CONE1.replace("bằng 1", "bằng 4")),
                                 "Tính diện tích thiết diện.", AREA), lambda p: None),
    # a distance the text does not state; a distance from the APEX read as one from the base
    _neg("n.wrong_distance", build(CONE_G, CONE_S, SEC_CONE1, dist("2", SEC_CONE1), "Tính diện tích thiết diện.", AREA),
         lambda p: None),
    _neg("n.from_apex", build(CONE_G, CONE_S, SEC_CONE1.replace("cách đáy", "cách đỉnh"),
                              dist("1", SEC_CONE1.replace("cách đáy", "cách đỉnh")), "Tính diện tích thiết diện.", AREA),
         lambda p: None),
    # an unread qualifier in the section sentence; a section quote not parallel to the base
    _neg("n.unread_tail", build(CONE_G, CONE_S, SEC_CONE1.replace("đường tròn.", "đường tròn có bán kính gấp đôi."),
                                dist("1", SEC_CONE1.replace("đường tròn.", "đường tròn có bán kính gấp đôi.")),
                                "Tính diện tích thiết diện.", AREA), lambda p: None),
    _neg("n.not_parallel", build(CONE_G, CONE_S, SEC_CONE1.replace("song song với đáy", "vuông góc với đáy"),
                                 dist("1", SEC_CONE1.replace("song song với đáy", "vuông góc với đáy")),
                                 "Tính diện tích thiết diện.", AREA), lambda p: None),
    # inverted ratio: the question asks original : small but the call says small : original
    _neg("n.ratio_inverted", build(CONE_G, CONE_S, SEC_CONE2 + " " + DERIVED, dist("2", SEC_CONE2),
                                   "Tính tỉ số thể tích của khối nón ban đầu và khối nón nhỏ.",
                                   {"kind": "volume_ratio", "numerator_solid_id": "kn", "denominator_solid_id": "k"},
                                   derived=DERIVED.rstrip(".")), lambda p: None),
    # area asked, volume answered / a section "volume"; axial section of a sphere (no declared axis)
    _neg("n.volume_of_section", build(CYL_G, CYL_S, SEC_CYL, dist("2", SEC_CYL), "Tính thể tích thiết diện.",
                                      {"kind": "measurement", "goal_type": "volume", "target": {"section_id": "td"}}),
         lambda p: None),
    _neg("n.sphere_axial", build(CP.SPH[0], CP.SPH[1], "Cắt mặt cầu bởi một mặt phẳng đi qua trục.",
                                 section("axial_section", "Cắt mặt cầu bởi một mặt phẳng đi qua trục", section_shape="circle"),
                                 "Tính diện tích thiết diện.", AREA), lambda p: None),
    # the section is stated for a cylinder but the payload targets... a cone question on a cylinder section
    _neg("n.section_kind_mismatch", build(CYL_G, CYL_S, SEC_CONE1.replace("hình nón", "hình nón"), dist("1", SEC_CONE1),
                                          "Tính diện tích thiết diện.", AREA), lambda p: None),
]


def run():
    rows = []
    for cid, p, oracle in CASES + NEGATIVES:
        r = run_typed_fact_next_v2_route(p)
        got = (r.answer_exact or {}).get("mg1") if r.status == "SERVED" else None
        if oracle == "REFUSE":
            outcome = "REFUSED_CORRECT" if got is None else "WRONG_SERVED"
        elif got is None:
            outcome = "REFUSED"
        else:
            outcome = "SERVED_CORRECT" if parse_exact(got["coef"]) == parse_exact(oracle) else "WRONG_SERVED"
        rows.append({"id": cid, "status": r.status, "code": r.code, "answer": got, "oracle": oracle, "outcome": outcome,
                     "reason": (r.reason or "")[:200]})
    return rows


if __name__ == "__main__":
    rows = run()
    for x in rows:
        print(f"{x['id']:22s} {x['status']:8s} {str(x['code']):36s} {x.get('answer')} oracle {x['oracle']} {x['outcome']}")
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
            json.dump({"provider_calls": 0, "classification": "DEVELOPMENT_DIAGNOSTIC", "rows": rows}, f,
                      ensure_ascii=False, indent=1)
            f.write('\n')
