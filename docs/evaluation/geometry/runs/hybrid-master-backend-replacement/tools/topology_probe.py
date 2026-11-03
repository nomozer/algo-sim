"""Phase C (fourth continuation): DEVELOPMENT probe of /4 measurement questions on four topologies beyond the single
S.ABCD of `measurement_probe.py`, each scored against a closed-form oracle written by hand before any run (squared for
lengths, cos² for angles, V² for volumes, so every oracle is rational). Offline, 0 provider calls. Not held-out: the
cases are authored by the implementer and only locate capability gaps. Usage: topology_probe.py [out.json]

T1 regular S.ABC, side 6, height 4: OA² = 12, SA² = 28, inradius² = 3, slant² = 19, V = 12√3.
T2 right prism ABCD.A'B'C'D', square side 2, AA' = 2 (a cube): chart A(0,0,0) … A'(0,0,2).
T3 S.ABC, ABC right at B, AB = 3, BC = 4, SA ⊥ (ABC), SA = 4: chart A(0,0,0) B(3,0,0) C(3,4,0) S(0,0,4).
T4 S.ABCD, square side 2, (SAB) ⊥ (ABCD), SAB equilateral: S(1,0,√3); (SCD): √3·y + 2z = 2√3.
"""
import json, re, sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / 'backend'))
from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402


def P(kind, quote, **args):
    return {"kind": kind, "args": args, "quote": quote, "solid_id": "s1"}


T = {
    "T1": ("Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 6 và chiều cao bằng 4.", "pyramid", "S.ABC",
           "Cho hình chóp tam giác đều S.ABC",
           [P("regular_pyramid", "hình chóp tam giác đều S.ABC", apex="S", base=["A", "B", "C"]),
            P("regular_polygon", "hình chóp tam giác đều S.ABC có cạnh đáy bằng 6", vertices=["A", "B", "C"], side="6"),
            P("height", "chiều cao bằng 4", value="4")],
           [("v", "volume", {"solid_id": "s1"}, "Tính thể tích khối chóp S.ABC.", F(432)),
            ("SA", "distance", {"segment": ["S", "A"]}, "Tính độ dài cạnh bên SA.", F(28)),
            ("a_SA_base", "angle", {"line": ["S", "A"], "plane": ["A", "B", "C"]},
             "Tính góc giữa đường thẳng SA và mặt phẳng (ABC).", F(3, 7)),
            ("a_dihedral", "angle", {"plane1": ["S", "B", "C"], "plane2": ["A", "B", "C"]},
             "Tính góc giữa hai mặt phẳng (SBC) và (ABC).", F(3, 19)),
            ("d_A_SBC", "distance", {"point": "A", "plane": ["S", "B", "C"]},
             "Tính khoảng cách từ A đến mặt phẳng (SBC).", F(432, 19)),
            ("d_SA_BC", "distance", {"line1": ["S", "A"], "line2": ["B", "C"]},
             "Tính khoảng cách giữa hai đường thẳng SA và BC.", F(108, 7))]),
    "T2": ("Cho lăng trụ đứng ABCD.A'B'C'D' có đáy ABCD là hình vuông cạnh 2 và AA' = 2.", "prism", "ABCD.A'B'C'D'",
           "Cho lăng trụ đứng ABCD.A'B'C'D'",
           [P("right_prism", "Cho lăng trụ đứng ABCD.A'B'C'D'", base=["A", "B", "C", "D"], top=["A'", "B'", "C'", "D'"]),
            P("regular_polygon", "đáy ABCD là hình vuông cạnh 2", vertices=["A", "B", "C", "D"], side="2"),
            P("segment_length", "AA' = 2", segment=["A", "A'"], value="2")],
           [("v", "volume", {"solid_id": "s1"}, "Tính thể tích khối lăng trụ.", F(64)),
            ("d_A_A'BD", "distance", {"point": "A", "plane": ["A'", "B", "D"]},
             "Tính khoảng cách từ A đến mặt phẳng (A'BD).", F(4, 3)),
            ("d_AB'_BC'", "distance", {"line1": ["A", "B'"], "line2": ["B", "C'"]},
             "Tính khoảng cách giữa hai đường thẳng AB' và BC'.", F(4, 3)),
            ("d_AC'_BD", "distance", {"line1": ["A", "C'"], "line2": ["B", "D"]},
             "Tính khoảng cách giữa hai đường thẳng AC' và BD.", F(2, 3)),
            ("d_A'_BD", "distance", {"point": "A'", "line": ["B", "D"]},
             "Tính khoảng cách từ A' đến đường thẳng BD.", F(6)),
            ("a_A'C_base", "angle", {"line": ["A'", "C"], "plane": ["A", "B", "C", "D"]},
             "Tính góc giữa đường thẳng A'C và mặt phẳng (ABCD).", F(2, 3)),
            ("a_A'BD_base", "angle", {"plane1": ["A'", "B", "D"], "plane2": ["A", "B", "C", "D"]},
             "Tính góc giữa hai mặt phẳng (A'BD) và (ABCD).", F(1, 3)),
            ("A'I", "distance", {"segment": ["A'", "I"]},
             "Gọi I là giao điểm của AC và BD. Tính độ dài A'I.", F(6),
             [P("intersect_line_line", "Gọi I là giao điểm của AC và BD", point="I", line1=["A", "C"],
                line2=["B", "D"])]),
            ("d_I_A'BD", "distance", {"point": "C", "plane": ["A'", "B", "D"]},
             # C(2,2,0); (A'BD): x + y + z = 2 ⇒ d = 2/√3
             "Tính khoảng cách từ C đến mặt phẳng (A'BD).", F(4, 3))]),
    "T3": ("Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = 3, BC = 4, SA vuông góc với mặt phẳng (ABC) "
           "và SA = 4.", "pyramid", "S.ABC", "Cho hình chóp S.ABC",
           [P("right_angle", "đáy ABC là tam giác vuông tại B", vertex="B", rays=["A", "C"]),
            P("segment_length", "AB = 3", segment=["A", "B"], value="3"),
            P("segment_length", "BC = 4", segment=["B", "C"], value="4"),
            P("perpendicular_line_plane", "SA vuông góc với mặt phẳng (ABC)", line=["S", "A"], plane=["A", "B", "C"]),
            P("segment_length", "SA = 4", segment=["S", "A"], value="4")],
           [("v", "volume", {"solid_id": "s1"}, "Tính thể tích khối chóp S.ABC.", F(64)),
            ("SC", "distance", {"segment": ["S", "C"]}, "Tính độ dài đoạn SC.", F(41)),
            ("d_A_SBC", "distance", {"point": "A", "plane": ["S", "B", "C"]},
             "Tính khoảng cách từ A đến mặt phẳng (SBC).", F(144, 25)),
            ("d_SA_BC", "distance", {"line1": ["S", "A"], "line2": ["B", "C"]},
             "Tính khoảng cách giữa hai đường thẳng SA và BC.", F(9)),
            ("d_A_SC", "distance", {"point": "A", "line": ["S", "C"]},
             "Tính khoảng cách từ A đến đường thẳng SC.", F(400, 41)),
            ("a_SC_base", "angle", {"line": ["S", "C"], "plane": ["A", "B", "C"]},
             "Tính góc giữa đường thẳng SC và mặt phẳng (ABC).", F(25, 41)),
            ("a_dihedral", "angle", {"plane1": ["S", "B", "C"], "plane2": ["A", "B", "C"]},
             "Tính góc giữa hai mặt phẳng (SBC) và (ABC).", F(9, 25)),
            ("a_SB_AC", "angle", {"line1": ["S", "B"], "line2": ["A", "C"]},
             "Tính góc giữa hai đường thẳng SB và AC.", F(81, 625)),
            ("d_M_base", "distance", {"point": "M", "plane": ["A", "B", "C"]},
             "Gọi M là trung điểm của SC. Tính khoảng cách từ M đến mặt phẳng (ABC).", F(4),
             [P("midpoint", "Gọi M là trung điểm của SC", point="M", segment=["S", "C"])]),
            # multi-step: goals over constructed intermediates (M(3/2,2,2), N(3/2,0,0), G(2,4/3,4/3),
            # H = proj of A on SB, K = proj of A on SC; AH ⊥ (SBC) so HK² = AK² − AH² = 400/41 − 144/25)
            *[(qid, gt, tg, f"Gọi M là trung điểm của SC và N là trung điểm của AB. {q}", o,
               [P("midpoint", "Gọi M là trung điểm của SC", point="M", segment=["S", "C"]),
                P("midpoint", "N là trung điểm của AB", point="N", segment=["A", "B"])])
              for qid, gt, tg, q, o in [
                  ("MN", "distance", {"segment": ["M", "N"]}, "Tính độ dài đoạn MN.", F(8)),
                  ("a_MN_base", "angle", {"line": ["M", "N"], "plane": ["A", "B", "C"]},
                   "Tính góc giữa đường thẳng MN và mặt phẳng (ABC).", F(1, 2)),
                  ("d_M_SAB", "distance", {"point": "M", "plane": ["S", "A", "B"]},
                   "Tính khoảng cách từ M đến mặt phẳng (SAB).", F(4)),
                  ("d_N_SC", "distance", {"point": "N", "line": ["S", "C"]},
                   "Tính khoảng cách từ N đến đường thẳng SC.", F(8))]],
            ("d_G_base", "distance", {"point": "G", "plane": ["A", "B", "C"]},
             "Gọi G là trọng tâm tam giác SBC. Tính khoảng cách từ G đến mặt phẳng (ABC).", F(16, 9),
             [P("centroid", "Gọi G là trọng tâm tam giác SBC", point="G", polygon=["S", "B", "C"])]),
            ("AH", "distance", {"segment": ["A", "H"]},
             "Gọi H là hình chiếu vuông góc của A trên SB. Tính độ dài AH.", F(144, 25),
             [P("orthogonal_projection_line", "Gọi H là hình chiếu vuông góc của A trên SB", point="A", image="H",
                line=["S", "B"])]),
            ("HK", "distance", {"segment": ["H", "K"]},
             "Gọi H, K lần lượt là hình chiếu vuông góc của A trên SB, SC. Tính độ dài HK.", F(4096, 1025),
             [P("orthogonal_projection_line", "Gọi H, K lần lượt là hình chiếu vuông góc của A trên SB, SC",
                point="A", image="H", line=["S", "B"]),
              P("orthogonal_projection_line", "Gọi H, K lần lượt là hình chiếu vuông góc của A trên SB, SC",
                point="A", image="K", line=["S", "C"])]),
            ("d_H_SAC", "distance", {"point": "H", "plane": ["S", "A", "C"]},
             "Gọi H là hình chiếu vuông góc của A trên SB. Tính khoảng cách từ H đến mặt phẳng (SAC).",
             # H(48/25, 0, 36/25); (SAC): 4x − 3y = 0 ⇒ d = (4·48/25)/5 = 192/125
             F(192 ** 2, 125 ** 2),
             [P("orthogonal_projection_line", "Gọi H là hình chiếu vuông góc của A trên SB", point="A", image="H",
                line=["S", "B"])])]),
    "T4": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, tam giác SAB đều và nằm trong mặt phẳng vuông góc "
           "với mặt phẳng (ABCD).", "pyramid", "S.ABCD", "Cho hình chóp S.ABCD",
           [P("regular_polygon", "đáy ABCD là hình vuông cạnh 2", vertices=["A", "B", "C", "D"], side="2"),
            P("regular_polygon", "tam giác SAB đều", vertices=["S", "A", "B"]),
            P("face_perpendicular_base", "tam giác SAB đều và nằm trong mặt phẳng vuông góc với mặt phẳng (ABCD)",
              face=["S", "A", "B"], base=["A", "B", "C", "D"])],
           [("v", "volume", {"solid_id": "s1"}, "Tính thể tích khối chóp S.ABCD.", F(16, 3)),
            ("d_A_SCD", "distance", {"point": "A", "plane": ["S", "C", "D"]},
             "Tính khoảng cách từ A đến mặt phẳng (SCD).", F(12, 7)),
            ("a_SC_base", "angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]},
             "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).", F(5, 8)),
            ("a_dihedral", "angle", {"plane1": ["S", "C", "D"], "plane2": ["A", "B", "C", "D"]},
             "Tính góc giữa hai mặt phẳng (SCD) và (ABCD).", F(4, 7))]),
}


def payload(given, solid_type, notation, solid_quote, premises, goal_type, target, question, extra=()):
    goal = {"goal_id": "mg1", "kind": "measurement", "goal_type": goal_type, "target": target,
            "quote": question.split(". ")[-1].rstrip(".")}
    if "solid_id" not in target:
        goal["solid_id"] = "s1"
    return {"schema_version": "typed-fact-next/2", "problem_text": f"{given} {question}", "length_unit": "1",
            "solids": [{"solid_id": "s1", "solid_type": solid_type, "notation": notation, "quote": solid_quote}],
            "premises": [*premises, *extra], "derived_sections": [], "relations": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1",
                                  "quote": solid_quote}],
            "math_goals": [goal]}


def squared(exact) -> F | None:
    """Independent reader of the exact display form {"coef": "p", "p/q", "p√r", "p√r/q", "√r/q"} (squared)."""
    m = re.fullmatch(r"(?P<p>\d+)?(?:√(?P<r>\d+))?(?:/(?P<q>\d+))?", exact.get("coef", ""))
    if not m or not (m["p"] or m["r"]):
        return None
    p, r, q = F(m["p"] or 1), F(m["r"] or 1), F(m["q"] or 1)
    return p * p * r / (q * q)


rows = []
for tid, (given, solid_type, notation, solid_quote, premises, questions) in T.items():
    for q in questions:
        qid, goal_type, target, question, oracle = q[:5]
        r = run_typed_fact_next_v2_route(payload(given, solid_type, notation, solid_quote, premises, goal_type,
                                                 target, question, q[5] if len(q) > 5 else ()))
        got = (r.answer_exact or {}).get("mg1") if r.status == "SERVED" else None
        value = None if got is None else (F(got["coef"]) if goal_type == "angle" and "√" not in got.get("coef", "")
                                          else squared(got))
        outcome = "REFUSED" if got is None else ("SERVED_CORRECT" if value == oracle else "WRONG_SERVED")
        rows.append({"id": f"{tid}.{qid}", "status": r.status, "code": r.code, "reason": (r.reason or "")[:200],
                     "answer": got, "oracle": str(oracle), "outcome": outcome})
        print(f"{tid}.{qid:12s} {r.status:8s} {str(r.code):40s} {got} oracle {oracle} {outcome}")
if len(sys.argv) > 1:
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump({"provider_calls": 0, "classification": "DEVELOPMENT_DIAGNOSTIC", "rows": rows}, f,
                  ensure_ascii=False, indent=1)
        f.write('\n')
