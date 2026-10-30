"""Task 2 part 2: independently authored /4 gold payloads for distance, angle and volume questions, each scored against
a closed-form oracle written by hand (not from the engine). Offline, 0 provider calls. Usage: measurement_probe.py [out]

Solid: S.ABCD, square base of side 2, SA ⊥ (ABCD), SA = 2; chart A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) S(0,0,2).
Oracle (squared value, so every answer is rational): (SBC): x + z = 2.
  d(A,(SBC)) = √2 → 2 · SC = 2√3 → 12 · d(AB,SC) = √2 → 2 · d(A,SC) = |AS×SC|/|SC| = 2√6/3 → 8/3
  d(AD,(SBC)) = √2 (AD ∥ (SBC)) → 2 · d((SAB),(SCD)) = 0 (they meet) → 0
  angle SC,(ABCD): cos² = 2/3 · angle SB,CD (CD ∥ AB): cos² = 1/2 · dihedral (SBC),(ABCD): cos² = 1/2
  V(S.ABCD) = 4·2/3 = 8/3 → 64/9
"""
import json, re, sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / 'backend'))
from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402

GIVEN = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 2."
PREMISES = [
    {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "2"}, "quote": "đáy ABCD là hình vuông cạnh 2", "solid_id": "s1"},
    {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "quote": "SA vuông góc với mặt phẳng (ABCD)", "solid_id": "s1"},
    {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2"}, "quote": "SA = 2", "solid_id": "s1"},
]
# (id, goal_type, target, question sentence, squared oracle)
QUESTIONS = [
    ("d_point_plane", "distance", {"point": "A", "plane": ["S", "B", "C"]}, "Tính khoảng cách từ A đến mặt phẳng (SBC).", Fraction(2)),
    ("d_segment", "distance", {"segment": ["S", "C"]}, "Tính độ dài đoạn SC.", Fraction(12)),
    ("d_line_line", "distance", {"line1": ["A", "B"], "line2": ["S", "C"]}, "Tính khoảng cách giữa hai đường thẳng AB và SC.", Fraction(2)),
    ("d_point_line", "distance", {"point": "A", "line": ["S", "C"]}, "Tính khoảng cách từ A đến đường thẳng SC.", Fraction(8, 3)),
    ("d_line_plane", "distance", {"line": ["A", "D"], "plane": ["S", "B", "C"]}, "Tính khoảng cách giữa đường thẳng AD và mặt phẳng (SBC).", Fraction(2)),
    ("d_plane_plane", "distance", {"plane1": ["S", "A", "B"], "plane2": ["S", "C", "D"]}, "Tính khoảng cách giữa hai mặt phẳng (SAB) và (SCD).", Fraction(0)),
    ("a_line_plane", "angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]}, "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).", Fraction(2, 3)),
    ("a_line_line", "angle", {"line1": ["S", "B"], "line2": ["C", "D"]}, "Tính góc giữa hai đường thẳng SB và CD.", Fraction(1, 2)),
    ("a_plane_plane", "angle", {"plane1": ["S", "B", "C"], "plane2": ["A", "B", "C", "D"]}, "Tính góc giữa hai mặt phẳng (SBC) và (ABCD).", Fraction(1, 2)),
    ("v_solid", "volume", {"solid_id": "s1"}, "Tính thể tích khối chóp S.ABCD.", Fraction(64, 9)),
]


def payload(goal_type, target, question):
    text = f"{GIVEN} {question}"
    goal = {"goal_id": "mg1", "kind": "measurement", "goal_type": goal_type, "target": target, "quote": question.rstrip(".")}
    if "solid_id" not in target:
        goal["solid_id"] = "s1"
    return {"schema_version": "typed-fact-next/2", "problem_text": text, "length_unit": "1",
            "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
            "premises": PREMISES, "derived_sections": [], "relations": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
            "math_goals": [goal]}


def squared(coef: str) -> Fraction:
    """Independent reader of an exact display coefficient: p, p/q, p√r, p√r/q, √r/q (squared)."""
    m = re.fullmatch(r"(?P<p>\d+)?(?:√(?P<r>\d+))?(?:/(?P<q>\d+))?", coef)
    if not m or not (m["p"] or m["r"]):
        raise ValueError(coef)
    p, r, q = Fraction(m["p"] or 1), Fraction(m["r"] or 1), Fraction(m["q"] or 1)
    return p * p * r / (q * q)


rows = []
for qid, goal_type, target, question, oracle in QUESTIONS:
    r = run_typed_fact_next_v2_route(payload(goal_type, target, question))
    got = (r.answer_exact or {}).get("mg1") if r.status == "SERVED" else None
    value = None
    if got is not None:
        value = squared(got["coef"]) if goal_type != "angle" else Fraction(got["coef"])
    outcome = ("SERVED_CORRECT" if value == oracle else "WRONG_SERVED") if got is not None else "REFUSED"
    rows.append({"id": qid, "goal_type": goal_type, "target": target, "status": r.status, "code": r.code,
                 "reason": (r.reason or "")[:160], "answer": got, "oracle_squared": str(oracle), "outcome": outcome})
    print(qid, r.status, r.code, got, "oracle²", oracle, outcome)

# Negative controls on the same solid: each must be refused (no answer, no scene).
def wrong_value(p):
    p["premises"][2] = {**p["premises"][2], "args": {"segment": ["S", "A"], "value": "3"}}   # text says SA = 2
def undeclared_operand(p):
    p["math_goals"][0]["target"] = {"point": "X", "plane": ["S", "B", "C"]}
def question_not_in_source(p):
    p["math_goals"][0]["quote"] = "Tính khoảng cách từ B đến mặt phẳng (SCD)"
def degenerate_plane(p):
    p["math_goals"][0]["target"] = {"point": "D", "plane": ["S", "A", "S"]}
for name, mutate in (("n_wrong_value", wrong_value), ("n_undeclared_operand", undeclared_operand),
                     ("n_question_not_in_source", question_not_in_source), ("n_degenerate_plane", degenerate_plane)):
    p = payload("distance", {"point": "A", "plane": ["S", "B", "C"]}, "Tính khoảng cách từ A đến mặt phẳng (SBC).")
    p["premises"] = [dict(x) for x in p["premises"]]
    mutate(p)
    r = run_typed_fact_next_v2_route(p)
    outcome = "REFUSED_CORRECT" if r.status != "SERVED" and not r.answer_exact and r.scene3d is None else "SERVED_NEGATIVE"
    rows.append({"id": name, "status": r.status, "code": r.code, "reason": (r.reason or "")[:160], "outcome": outcome})
    print(name, r.status, r.code, outcome)
if len(sys.argv) > 1:
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump({"solid": GIVEN, "provider_calls": 0, "rows": rows}, f, ensure_ascii=False, indent=1); f.write('\n')
