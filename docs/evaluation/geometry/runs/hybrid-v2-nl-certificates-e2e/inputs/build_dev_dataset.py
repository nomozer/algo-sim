# -*- coding: utf-8 -*-
"""Builds `nl_dev_authored.json` — the DEV_AUTHORED wording-metamorphic dataset of run `hybrid-v2-nl-certificates-e2e`.

Authored by the SAME agent that implemented the pipeline ⇒ `author_kind = SAME_AGENT`, never an independent holdout.
Gold values come from closed-form formulas written here (no product import); gold payloads are the V2 extraction a
faithful reader would emit for each wording. Usage (from backend/):  python <this file> <out.json>
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction as F
from math import isqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))


def rad(v2: F) -> str:
    """Exact label of sqrt(v2) for a positive rational: `p`, `p/q`, `c√r`, `c√r/q` (c, r, q integers, r square-free)."""
    n, d = v2.numerator * v2.denominator, v2.denominator          # sqrt(p/q) = sqrt(p·q)/q
    c, r = 1, n
    for k in range(isqrt(n), 1, -1):
        if n % (k * k) == 0:
            c, r = k, n // (k * k)
            break
    g = 1
    from math import gcd
    g = gcd(c, d)
    c, d = c // g, d // g
    head = (str(c) if c != 1 or r == 1 else "") + (f"√{r}" if r != 1 else "")
    return head + (f"/{d}" if d != 1 else "")


def item(iid, family, text, payload, expect, *, contradiction=False, note="", stress=()):
    """`payload` = the extraction a FAITHFUL reader emits; `stress` = unfaithful extractions (a non-premise clause turned
    into a premise, ...) that the deterministic gate must still not serve."""
    return {"id": iid, "family": family, "split": "DEV_AUTHORED", "problem_text": text,
            "provenance": {"author_kind": "SAME_AGENT", "origin": "HAND_AUTHORED_WORDING_VARIANT", "author": "implementing-agent",
                           "created": "2026-10-27", "note": note},
            "exposure": {"label": "EXPOSED", "in_tests": True, "in_prompt": False, "seen_by_implementer": True},
            "gold": {"payload": payload, "expectation": expect, "contradiction": contradiction},
            "stress_payloads": list(stress)}


SERVE = lambda **values: {"disposition": "SERVE", "values": values}
REFUSE = lambda cat, *codes: {"disposition": "REFUSE", "category": cat, "allowed_codes": list(codes)}


# ── family 1: pyramid S.ABCD, square base side s, SA ⊥ base, SA = h ───────────────────────────────────────────────────

def pyramid(labels="SABCD", s=4, h=3, base=None, perp=None, ln=None, goal=None, gt="distance", target=None,
            drop=(), extra=(), solid=None, nopremise=()):
    S, A, B, C, D = labels
    bl = [A, B, C, D]
    solid = solid or f"Cho hình chóp {S}.{A}{B}{C}{D}."
    base = base or f"Đáy {A}{B}{C}{D} là hình vuông cạnh {s}."
    perp = perp or f"{S}{A} vuông góc với mặt phẳng ({A}{B}{C}{D})."
    ln = ln or f"{S}{A} = {h}."
    if goal is None:
        goal, gt, target = f"Tính khoảng cách từ {S} đến {B}{D}.", "distance", {"point": S, "line": [B, D]}
    prem = {"base": {"kind": "base_is_square", "args": {"vertices": bl, "side": str(s)}, "quote": base},
            "perp": {"kind": "perpendicular_line_plane", "args": {"line": [S, A], "plane": bl}, "quote": perp},
            "len": {"kind": "segment_length", "args": {"segment": [S, A], "value": str(h)}, "quote": ln}}
    sentences = {"base": base, "perp": perp, "len": ln}
    texts = [solid] + [sentences[k] for k in ("base", "perp", "len") if k not in drop] + [q for q, _ in extra] + [goal]
    premises = [prem[k] for k in ("base", "perp", "len") if k not in drop and k not in nopremise] + [p for _, p in extra]
    return {"schema_version": "typed-fact-next/2", "problem_text": " ".join(texts), "length_unit": "1",
            "solids": [{"solid_id": "py", "solid_type": "pyramid", "notation": f"{S}.{A}{B}{C}{D}", "quote": solid}],
            "premises": premises,
            "simulation_goals": [{"goal_id": "draw", "kind": "construct_object", "target_solid_id": "py", "quote": solid}],
            "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": gt, "target": target, "quote": goal}]}


def dist_sbd(s, h):      # d²(S, BD) = h² + s²/2  (the foot is the base centre O, SO² = SA² + AO²)
    return rad(F(h * h) + F(s * s, 2))


def cos2_sc(s, h):       # cos²(SC, (ABCD)) = AC²/SC² = 2s²/(2s²+h²)
    return str(F(2 * s * s, 2 * s * s + h * h))


# ── family 2: right prism ABC.A'B'C', right angle at A, AB = x, AC = y, AA' = h; plane named by four labels ─────────────

def prism(goal, target, x=6, y=8, h=12, labels="ABC"):
    a, b, c = labels
    base, top = list(labels), [v + "'" for v in labels]
    name = f"{labels}.{''.join(top)}"
    solid, shape = f"Cho lăng trụ đứng {name}.", f"Đáy {labels} là tam giác vuông tại {a}."
    qs = [solid, shape, f"{a}{b} = {x}.", f"{a}{c} = {y}.", f"{a}{a}' = {h}.", goal]
    prem = [{"kind": "right_angle", "args": {"vertex": a, "rays": [b, c]}, "quote": shape},
            {"kind": "segment_length", "args": {"segment": [a, b], "value": str(x)}, "quote": qs[2]},
            {"kind": "segment_length", "args": {"segment": [a, c], "value": str(y)}, "quote": qs[3]},
            {"kind": "right_prism", "args": {"base": base, "top": top}, "quote": solid},
            {"kind": "segment_length", "args": {"segment": [a, a + "'"], "value": str(h)}, "quote": qs[4]}]
    return {"schema_version": "typed-fact-next/2", "problem_text": " ".join(qs), "length_unit": "1",
            "solids": [{"solid_id": "pr", "solid_type": "prism", "notation": name, "quote": solid}], "premises": prem,
            "simulation_goals": [{"goal_id": "draw", "kind": "construct_object", "target_solid_id": "pr", "quote": solid}],
            "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": "distance", "target": target, "quote": goal}]}


def build():
    out = []
    # 2. multi-label plane wordings: d²(A, (BCC'B')) = x²y²/(x²+y²)
    for i, (g, plane) in enumerate([("Tính khoảng cách từ A đến mặt phẳng (BCC'B').", ["B", "C", "C'", "B'"]),
                                    ("Tính khoảng cách từ A đến mặt phẳng (BCC′B′).", ["B", "C", "C'", "B'"]),
                                    ("Tính khoảng cách từ A đến mặt phẳng (B'BCC').", ["B'", "B", "C", "C'"]),
                                    ("Tính khoảng cách từ A đến mặt bên BCC'B'.", ["B", "C", "C'", "B'"]),
                                    ("Tính khoảng cách từ A đến mp(BCC'B').", ["B", "C", "C'", "B'"]),
                                    ("Tính khoảng cách từ A đến (BCC'B').", ["B", "C", "C'", "B'"])]):
        p = prism(g, {"point": "A", "plane": plane})
        out.append(item(f"pr-plane-{i}", "right-prism-lateral-face", p["problem_text"], p, SERVE(q=rad(F(36 * 64, 36 + 64)))))
    p = prism("Tính khoảng cách từ điểm A đến mặt phẳng chứa mặt bên (BCC'B').", {"point": "A", "plane": ["B", "C", "C'", "B'"]})
    out.append(item("pr-gap-plane-containing-face", "right-prism-lateral-face", p["problem_text"], p, SERVE(q=rad(F(36 * 64, 36 + 64))),
                    note="KNOWN_GAP"))
    # 1a. goal wordings (distance) — gold SERVE
    GOALS_D = ["Tính khoảng cách từ S đến BD.", "Tìm khoảng cách từ S đến BD.", "Tìm khoảng cách từ S tới BD.",
               "Khoảng cách từ S đến đường thẳng BD bằng bao nhiêu?", "Tính khoảng cách từ điểm S đến đường thẳng BD."]
    for i, g in enumerate(GOALS_D):
        p = pyramid(goal=g, gt="distance", target={"point": "S", "line": ["B", "D"]})
        out.append(item(f"py-dist-goal-{i}", "pyramid-sa-perp-base", p["problem_text"], p, SERVE(q=dist_sbd(4, 3))))
    # 1b. goal wordings (angle) — gold SERVE, value stated as exact cos² (the product's own quantity for "góc")
    GOALS_A = ["Tính góc giữa SC và mặt phẳng (ABCD).", "Tính góc giữa đường thẳng SC và mặt đáy.", "Tính góc tạo bởi SC và (ABCD).",
               "Góc giữa SC và đáy bằng bao nhiêu?"]
    T_A = {"line": ["S", "C"], "plane": list("ABCD")}
    for i, g in enumerate(GOALS_A):
        p = pyramid(goal=g, gt="angle", target=T_A)
        out.append(item(f"py-angle-goal-{i}", "pyramid-sa-perp-base", p["problem_text"], p, SERVE(q=cos2_sc(4, 3))))
    # 1c. premise wordings — gold SERVE
    BASES = ["Đáy ABCD là hình vuông cạnh 4.", "Đáy là hình vuông ABCD cạnh 4.", "Đáy ABCD là hình vuông có cạnh bằng 4.",
             "Đáy ABCD là hình vuông, cạnh 4.", "Đáy ABCD là hình vuông với cạnh 4.", "Đáy ABCD là hình vuông và có cạnh 4.",
             "Đáy ABCD là hình vuông có độ dài cạnh bằng 4.", "Đáy ABCD là hình vuông có cạnh là 4."]
    for i, b in enumerate(BASES):
        p = pyramid(base=b)
        out.append(item(f"py-base-{i}", "pyramid-sa-perp-base", p["problem_text"], p, SERVE(q=dist_sbd(4, 3))))
    PERPS = ["SA vuông góc với đáy.", "SA ⊥ (ABCD).", "SA vuông góc với mặt đáy (ABCD).", "Cạnh bên SA vuông góc với đáy ABCD.",
             "SA vuông góc với mặt phẳng đáy."]
    for i, q in enumerate(PERPS):
        p = pyramid(perp=q)
        out.append(item(f"py-perp-{i}", "pyramid-sa-perp-base", p["problem_text"], p, SERVE(q=dist_sbd(4, 3))))
    LENS = ["SA bằng 3.", "SA = 3 cm.", "Cạnh bên SA có độ dài bằng 3.", "Cho SA = 3."]
    for i, q in enumerate(LENS):
        p = pyramid(ln=q)
        out.append(item(f"py-len-{i}", "pyramid-sa-perp-base", p["problem_text"], p, SERVE(q=dist_sbd(4, 3))))
    # 1d. renamed labels and other numbers (metamorphic: the value follows the formula, not the text)
    for labels, s, h in (("PKLMN", 2, 5), ("SABCD", 6, 1), ("OPQRT", 5, 12)):
        S, A, B, C, D = labels
        p = pyramid(labels, s, h)
        out.append(item(f"py-rename-{labels}-{s}-{h}", "pyramid-sa-perp-base", p["problem_text"], p, SERVE(q=dist_sbd(s, h))))
        g = f"Tính góc giữa {S}{C} và mặt phẳng ({A}{B}{C}{D})."
        p = pyramid(labels, s, h, goal=g, gt="angle", target={"line": [S, C], "plane": list(A + B + C + D)})
        out.append(item(f"py-rename-angle-{labels}-{s}-{h}", "pyramid-sa-perp-base", p["problem_text"], p, SERVE(q=cos2_sc(s, h))))
    # 1e. KNOWN valid-wording gaps (gold SERVE) — they must stay visible as INCORRECT_REFUSED until fixed
    p = pyramid(goal="Tính d(S, BD).", gt="distance", target={"point": "S", "line": ["B", "D"]})
    out.append(item("py-gap-notation-d", "pyramid-sa-perp-base", p["problem_text"], p, SERVE(q=dist_sbd(4, 3)), note="KNOWN_GAP"))
    p = pyramid(goal="Tính góc giữa đường thẳng SC và mặt phẳng đáy (ABCD).", gt="angle", target=T_A)
    out.append(item("py-gap-plane-day-labelled", "pyramid-sa-perp-base", p["problem_text"], p, SERVE(q=cos2_sc(4, 3)), note="KNOWN_GAP"))
    p = pyramid(base="Đáy ABCD là hình vuông (cạnh 4).")
    out.append(item("py-gap-side-in-parentheses", "pyramid-sa-perp-base", p["problem_text"], p, SERVE(q=dist_sbd(4, 3)), note="KNOWN_GAP"))
    # 1f. refusals that MUST stay refusals
    D = {"point": "S", "line": ["B", "D"]}
    p = pyramid(drop=("len",)); out.append(item("py-neg-no-height", "pyramid-sa-perp-base", p["problem_text"], p, REFUSE("INSUFFICIENT", "MISSING_DIMENSION")))
    p = pyramid(drop=("perp",)); out.append(item("py-neg-no-perp", "pyramid-sa-perp-base", p["problem_text"], p, REFUSE("INSUFFICIENT", "UNDERDETERMINED_POINT")))
    # non-premise clauses: the faithful reader leaves them out (⇒ insufficient data); the STRESS extraction wrongly turns
    # them into premises and the gate must refuse by role, never serve
    for key, bad, cat, code in (
            ("prove-perp", "Chứng minh rằng SA vuông góc với mặt phẳng (ABCD).", "UNPROVEN_RELATION", "GOAL_CLAUSE_NOT_PREMISE"),
            ("conditional-perp", "Nếu SA vuông góc với mặt phẳng (ABCD) thì SA = 3.", "NOT_A_PREMISE", "CONDITIONAL_CLAUSE"),
            ("negated-perp", "SA không vuông góc với mặt phẳng (ABCD).", "NOT_A_PREMISE", "NEGATED_CLAUSE")):
        p = pyramid(perp=bad, nopremise=("perp",))
        out.append(item(f"py-neg-{key}", "pyramid-sa-perp-base", p["problem_text"], p,
                        REFUSE(cat, "UNDERDETERMINED_POINT", code), stress=[pyramid(perp=bad)]))
    p = pyramid(extra=[("SA = 5.", {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "5"}, "quote": "SA = 5."})])
    out.append(item("py-neg-two-heights", "pyramid-sa-perp-base", p["problem_text"], p, REFUSE("CONTRADICTORY", "INCONSISTENT_FACTS"), contradiction=True))
    p = pyramid(extra=[("AC = 4.", {"kind": "segment_length", "args": {"segment": ["A", "C"], "value": "4"}, "quote": "AC = 4."})])
    out.append(item("py-neg-side-vs-diagonal", "pyramid-sa-perp-base", p["problem_text"], p, REFUSE("CONTRADICTORY", "INCONSISTENT_FACTS"), contradiction=True))
    p = pyramid(goal="Tính khoảng cách từ S đến BX.", gt="distance", target={"point": "S", "line": ["B", "X"]})
    out.append(item("py-neg-unknown-label", "pyramid-sa-perp-base", p["problem_text"], p, REFUSE("AMBIGUOUS", "UNDERDETERMINED_POINT")))
    p = pyramid(goal="Tính số đo góc giữa SC và mặt phẳng (ABCD).", gt="angle", target=T_A)
    out.append(item("py-neg-degree-measure", "pyramid-sa-perp-base", p["problem_text"], p, REFUSE("UNSUPPORTED", "QUESTION_CONTEXT_UNSUPPORTED"),
                    note="the product returns cos² of the angle, never the degree measure: asking the measure is refused by design"))
    # 1g. STRESS only: extractor mistakes that must never be served (the faithful payload for these texts IS a serve, so
    # they are attached as stress payloads of an ordinary item, with the REFUSE expectation applying to the stress arm)
    base_item = out[0]
    wrong = []
    for label, mutate in (("target-differs-from-quote", lambda p: p["math_goals"][0].update(target={"point": "S", "line": ["B", "C"]})),
                          ("height-value-differs-from-quote", lambda p: p["premises"][2]["args"].update(value="4")),
                          ("side-value-differs-from-quote", lambda p: p["premises"][0]["args"].update(side="5")),
                          ("plane-differs-from-quote", lambda p: p["premises"][1]["args"].update(plane=["A", "B", "C"]))):
        p = json.loads(json.dumps(base_item["gold"]["payload"]))
        mutate(p)
        wrong.append(p)
    base_item["stress_payloads_must_refuse"] = wrong
    return out


if __name__ == "__main__":
    data = build()
    Path(sys.argv[1]).write_text(json.dumps({"schema": "nl-eval-dataset/1", "items": data}, ensure_ascii=False, indent=1) + "\n",
                                 encoding="utf-8")
    print(len(data), "items")
