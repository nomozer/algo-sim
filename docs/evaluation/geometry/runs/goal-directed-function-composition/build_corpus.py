"""Deterministic builder of the corpora of run `goal-directed-function-composition` — no `app.*` import, 0 model calls.

    python build_corpus.py            # writes corpus-dev.json and corpus-holdout.json next to this file (refuses to overwrite)

Every case = premise template (text + typed facts + an oracle chart of its own) + one or more questions. Premise templates
reuse wordings already served by earlier corpora; what is new is the asked COMPOSITION. Positive cases carry `goals` for
`oracle.py` (expected values are computed there, never typed here); negative cases carry the refusal codes the current
contract defines. Provenance: AGENT_AUTHORED_WITH_INDEPENDENT_ORACLE_NOT_HUMAN_VALIDATED.
"""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
EUCLID = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def fact(fid, kind, quote, **kw):
    return {"id": fid, "kind": kind, "role": "premise", "quotes": [quote], **kw}


def T(text, facts, points, gram=EUCLID):
    return {"text": text, "facts": facts, "geometry": {"points": points, "gram": gram}}


# ── premise templates ────────────────────────────────────────────────────────────────────────────────────────────────
S1 = "Cho hình chóp S.ABCD."
SQ = T("Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 3.", [
    fact("f1", "solid", S1, solid="S.ABCD", solid_type="pyramid"),
    fact("f2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 2.", points=list("ABCD"), shape="square", value="2"),
    fact("f3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=list("ABCD")),
    fact("f4", "length", "SA = 3.", points=["S", "A"], measure="segment", value="3")],
    {"A": [0, 0, 0], "B": [2, 0, 0], "C": [2, 2, 0], "D": [0, 2, 0], "S": [0, 0, 3]})
CUBE_Q = "Cho hình lập phương ABCD.A'B'C'D' cạnh 2."
CUBE = T(CUBE_Q, [
    fact("f1", "solid", CUBE_Q, solid="ABCD.A'B'C'D'", solid_type="cube"),
    fact("f2", "length", CUBE_Q, solid="ABCD.A'B'C'D'", measure="edge", value="2")],
    {"A": [0, 0, 0], "B": [2, 0, 0], "C": [2, 2, 0], "D": [0, 2, 0],
     "A'": [0, 0, 2], "B'": [2, 0, 2], "C'": [2, 2, 2], "D'": [0, 2, 2]})
CUBOID = T("Cho hình hộp chữ nhật ABCD.A'B'C'D'. AB = 2. AD = 4. AA' = 3.", [
    fact("f1", "solid", "Cho hình hộp chữ nhật ABCD.A'B'C'D'.", solid="ABCD.A'B'C'D'", solid_type="cuboid"),
    fact("f2", "length", "AB = 2.", points=["A", "B"], value="2", measure="segment"),
    fact("f3", "length", "AD = 4.", points=["A", "D"], value="4", measure="segment"),
    fact("f4", "length", "AA' = 3.", points=["A", "A'"], value="3", measure="segment")],
    {"A": [0, 0, 0], "B": [2, 0, 0], "C": [2, 4, 0], "D": [0, 4, 0],
     "A'": [0, 0, 3], "B'": [2, 0, 3], "C'": [2, 4, 3], "D'": [0, 4, 3]})
PRISM_Q = "Cho lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều ABC cạnh 2."
PRISM = T(PRISM_Q + " AA' = 3.", [
    fact("f1", "solid", PRISM_Q, solid="ABC.A'B'C'", solid_type="prism", right=True),
    fact("f2", "polygon_shape", PRISM_Q, points=list("ABC"), shape="equilateral_triangle", value="2"),
    fact("f3", "length", "AA' = 3.", points=["A", "A'"], value="3", measure="segment")],
    # chart: A origin, B, C, A' basis; |AB| = |AC| = 2 at 60°, AA' = 3 orthogonal
    {"A": [0, 0, 0], "B": [1, 0, 0], "C": [0, 1, 0], "A'": [0, 0, 1], "B'": [1, 0, 1], "C'": [0, 1, 1]},
    [[4, 2, 0], [2, 4, 0], [0, 0, 9]])
REG_Q = "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2."
REGPYR = T(REG_Q + " SA = 3.", [
    fact("f1", "solid", REG_Q, solid="S.ABCD", solid_type="pyramid", regular=True),
    fact("f2", "polygon_shape", REG_Q, points=list("ABCD"), shape="square", value="2"),
    fact("f3", "length", "SA = 3.", points=["S", "A"], measure="segment", value="3")],
    # chart: unit square scaled by 2, height axis scaled by √7 (SO² = SA² − OA² = 9 − 2)
    {"A": [0, 0, 0], "B": [1, 0, 0], "C": [1, 1, 0], "D": [0, 1, 0], "S": ["1/2", "1/2", 1]},
    [[4, 0, 0], [0, 4, 0], [0, 0, 7]])
TET_Q = "Cho tứ diện đều ABCD cạnh 2."
TETRA = T(TET_Q, [
    fact("f1", "solid", TET_Q, solid="ABCD", solid_type="tetrahedron", regular=True),
    fact("f2", "length", TET_Q, solid="ABCD", measure="edge", value="2")],
    {"A": [0, 0, 0], "B": [1, 0, 0], "C": [0, 1, 0], "D": [0, 0, 1]}, [[4, 2, 2], [2, 4, 2], [2, 2, 4]])
RB_Q = "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B."
RIGHTB = T(RB_Q + " AB = 2. BC = 3. SA vuông góc với (ABC). SA = 4.", [
    fact("f1", "solid", RB_Q, solid="S.ABC", solid_type="pyramid"),
    fact("f2", "right_angle", RB_Q, at="B", points=["A", "C"]),
    fact("f3", "length", "AB = 2.", points=["A", "B"], measure="segment", value="2"),
    fact("f4", "length", "BC = 3.", points=["B", "C"], measure="segment", value="3"),
    fact("f5", "perpendicular", "SA vuông góc với (ABC).", points_a=["S", "A"], points_b=list("ABC")),
    fact("f6", "length", "SA = 4.", points=["S", "A"], measure="segment", value="4")],
    {"B": [0, 0, 0], "A": [2, 0, 0], "C": [0, 3, 0], "S": [2, 0, 4]})
T120 = T("Cho hình chóp S.ABC. AB = 3. AC = 5. BC = 7. SA vuông góc với (ABC). SA = 2.", [
    fact("f1", "solid", "Cho hình chóp S.ABC.", solid="S.ABC", solid_type="pyramid"),
    fact("f2", "length", "AB = 3.", points=["A", "B"], measure="segment", value="3"),
    fact("f3", "length", "AC = 5.", points=["A", "C"], measure="segment", value="5"),
    fact("f4", "length", "BC = 7.", points=["B", "C"], measure="segment", value="7"),
    fact("f5", "perpendicular", "SA vuông góc với (ABC).", points_a=["S", "A"], points_b=list("ABC")),
    fact("f6", "length", "SA = 2.", points=["S", "A"], measure="segment", value="2")],
    # chart: A origin, AB, AC, AS basis; AB·AC = 3·5·cos 120° = −15/2 (non-orthogonal metric, W2-EXP-15)
    {"A": [0, 0, 0], "B": [1, 0, 0], "C": [0, 1, 0], "S": [0, 0, 1]}, [[9, "-15/2", 0], ["-15/2", 25, 0], [0, 0, 4]])
EQ_Q = "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a."
EQA = T(EQ_Q + " SA vuông góc với (ABC). SA = a.", [
    fact("f1", "solid", EQ_Q, solid="S.ABC", solid_type="pyramid"),
    fact("f2", "polygon_shape", EQ_Q, points=list("ABC"), shape="equilateral_triangle", value="a"),
    fact("f3", "perpendicular", "SA vuông góc với (ABC).", points_a=["S", "A"], points_b=list("ABC")),
    fact("f4", "length", "SA = a.", points=["S", "A"], measure="segment", value="a")],
    {"A": [0, 0, 0], "B": [1, 0, 0], "C": [0, 1, 0], "S": [0, 0, 1]}, [[1, "1/2", 0], ["1/2", 1, 0], [0, 0, 1]])
REGA_Q = "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a và chiều cao bằng a."
REGA = T(REGA_Q, [
    fact("f1", "solid", REGA_Q, solid="S.ABCD", solid_type="pyramid", regular=True),
    fact("f2", "polygon_shape", REGA_Q, points=list("ABCD"), shape="square", value="a"),
    fact("f3", "length", REGA_Q, solid="S.ABCD", measure="height", value="a")],
    {"A": [0, 0, 0], "B": [1, 0, 0], "C": [1, 1, 0], "D": [0, 1, 0], "S": ["1/2", "1/2", 1]})
# The source gate binds ONE number per value quote (AMBIGUOUS_VALUE_QUOTE): the same premises in two sentences.
REGA2_Q = "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a."
REGA_SPLIT = T(REGA2_Q + " Chiều cao của hình chóp bằng a.", [
    fact("f1", "solid", REGA2_Q, solid="S.ABCD", solid_type="pyramid", regular=True),
    fact("f2", "polygon_shape", REGA2_Q, points=list("ABCD"), shape="square", value="a"),
    fact("f3", "length", "Chiều cao của hình chóp bằng a.", solid="S.ABCD", measure="height", value="a")],
    REGA["geometry"]["points"])


def D(desc, ops):
    return {"desc": desc, "of": list(ops)}


def mid(ops):
    return f"trung điểm của {ops}"


def cen(ops):
    return f"trọng tâm của tam giác {ops}"


def ask(kind, desc, ops, **kw):
    """(wording of the described point, question fields, oracle goal) for one closed question form."""
    pk = "midpoint" if desc == "mid" else "centroid"
    words = (mid if desc == "mid" else cen)(ops)
    pt = D(pk, _labels(ops))
    q = {"point_kind": pk, "points": _labels(ops)}
    if kind == "area":
        x, y = kw["to"]
        return (f"Tính diện tích tam giác tạo bởi {words} và hai điểm {x}, {y}.",
                {"quantity": "area", **q, "points_b": [x, y]}, {"measure": "area", "point": pt, "target": [x, y]})
    if kind == "length":
        return (f"Tính độ dài đoạn nối {words} với điểm {kw['to']}.", {"quantity": "length", **q, "points_b": [kw["to"]]},
                {"measure": "length", "point": pt, "target": kw["to"]})
    if kind == "dist_plane":
        return (f"Tính khoảng cách từ {words} đến ({kw['to']}).",
                {"quantity": "distance", **q, "points_b": _labels(kw["to"])},
                {"measure": "distance_plane", "point": pt, "target": _labels(kw["to"])})
    if kind == "dist_line":
        return (f"Tính khoảng cách từ {words} đến {kw['to']}.", {"quantity": "distance", **q, "points_b": _labels(kw["to"])},
                {"measure": "distance_line", "point": pt, "target": _labels(kw["to"])})
    p = kw["partner"]
    line = f"nối {words} với điểm {p}" if kw.get("reverse") else f"nối {p} với {words}"
    if kind == "angle_plane":
        return (f"Tính góc giữa đường thẳng {line} và ({kw['to']}).",
                {"quantity": "angle", **q, "points_a": [p], "points_b": _labels(kw["to"])},
                {"measure": "cos2_line_plane", "point": pt, "partner": p, "target": _labels(kw["to"])})
    return (f"Tính góc giữa đường thẳng {line} và đường thẳng {kw['to']}.",
            {"quantity": "angle", **q, "points_a": [p], "points_b": _labels(kw["to"])},
            {"measure": "cos2_lines", "point": pt, "partner": p, "target": _labels(kw["to"])})


def _labels(s):
    out = []
    for ch in s:
        if ch == "'":
            out[-1] += "'"
        else:
            out.append(ch)
    return out


def named_angle_lines(a, b):
    return (f"Tính góc giữa {a} và {b}.", {"quantity": "angle", "points_a": _labels(a), "points_b": _labels(b)},
            {"measure": "cos2_lines", "point": _labels(a)[0], "partner": _labels(a)[1], "target": _labels(b)})


def case(cid, tpl, questions, *, split, source="authored", composition=None, novelty=None, extra_text=""):
    text = tpl["text"] + extra_text + "".join(" " + q[0] for q in questions)
    facts = deepcopy(tpl["facts"])
    goals = {}
    for i, (wording, fields, goal) in enumerate(questions, 1):
        gid = "q" if len(questions) == 1 else f"q{i}"
        facts.append({"id": gid, "kind": "question", "role": "question", "quotes": [wording], **fields})
        if goal is not None:
            goals[gid] = goal
    return {"id": cid, "split": split, "kind": "positive", "source": source, "composition": composition,
            "novelty": novelty, "text": text, "payload": {"facts": facts},
            "geometry": tpl["geometry"], "goals": goals}


def negative(cid, base, patch, codes, *, split, source="authored", text_patch=None, note=""):
    c = deepcopy(base)
    c.update(id=cid, split=split, kind="negative", source=source, expected_codes=sorted(codes), note=note)
    for k in ("geometry", "goals", "composition", "novelty"):
        c.pop(k, None)
    q = c["payload"]["facts"][-1]
    for k, v in patch.items():
        q.pop(k, None) if v is None else q.__setitem__(k, v)
    if text_patch:
        old, new = text_patch
        c["text"] = c["text"].replace(old, new)
        q["quotes"] = [s.replace(old, new) for s in q["quotes"]]
    return c


NOVEL, PRIM, EXIST = "novel_function_combination", "new_primitive", "existing_capability_control"


def dev() -> list[dict]:
    c = [
        case("dev-sq-centroid-area", SQ, [ask("area", "cen", "SBC", to="AB")], split="dev", composition="centroid->ask_area", novelty=NOVEL),
        case("dev-sq-centroid-length", SQ, [ask("length", "cen", "SBC", to="A")], split="dev", composition="centroid->ask_length", novelty=NOVEL),
        case("dev-sq-centroid-dist-plane", SQ, [ask("dist_plane", "cen", "SBC", to="SAD")], split="dev",
             composition="centroid->ask_distance_point_plane", novelty=NOVEL),
        case("dev-sq-centroid-dist-line", SQ, [ask("dist_line", "cen", "SBC", to="AD")], split="dev",
             composition="centroid+orthogonal_projection_line->ask_length", novelty=NOVEL),
        case("dev-sq-centroid-angle-plane", SQ, [ask("angle_plane", "cen", "SBC", partner="A", to="ABCD")], split="dev",
             composition="centroid->ask_angle_line_plane", novelty=NOVEL),
        case("dev-sq-centroid-angle-lines", SQ, [ask("angle_lines", "cen", "SBC", partner="A", to="BD")], split="dev",
             composition="centroid->ask_angle_lines", novelty=NOVEL),
        case("dev-sq-midpoint-angle-plane", SQ, [ask("angle_plane", "mid", "SC", partner="A", reverse=True, to="ABCD")],
             split="dev", composition="midpoint->ask_angle_line_plane", novelty=NOVEL),
        case("dev-sq-midpoint-angle-lines", SQ, [ask("angle_lines", "mid", "SC", partner="B", to="AC")], split="dev",
             composition="midpoint->ask_angle_lines", novelty=NOVEL),
        case("dev-sq-named-angle-lines", SQ, [named_angle_lines("SB", "AC")], split="dev", composition="ask_angle_lines",
             novelty=PRIM),
        case("dev-sq-midpoint-area-control", SQ, [ask("area", "mid", "SC", to="AB")], split="dev",
             composition="midpoint->ask_area", novelty=EXIST),
        case("dev-sq-midpoint-dist-line-control", SQ, [ask("dist_line", "mid", "SC", to="AD")], split="dev",
             composition="midpoint+orthogonal_projection_line->ask_length", novelty=EXIST),
        # W2-EXP rows the current schema expresses and Wave 2A scopes (audit: w2-exp-audit.json)
        case("W2-EXP-01", EQA, [ask("area", "cen", "SBC", to="AB")], split="dev", source="W2-EXP-01",
             composition="centroid->ask_area", novelty=NOVEL),
        case("W2-EXP-02", REGA, [ask("angle_plane", "mid", "SC", partner="A", to="ABCD")], split="dev", source="W2-EXP-02",
             composition="midpoint->ask_angle_line_plane", novelty=NOVEL),
        case("W2-EXP-02-split", REGA_SPLIT, [ask("angle_plane", "mid", "SC", partner="A", to="ABCD")], split="dev",
             source="W2-EXP-02 (premises split one value per sentence)", composition="midpoint->ask_angle_line_plane",
             novelty=NOVEL),
        case("W2-EXP-15", T120, [named_angle_lines("SB", "AC"),
                                 ("Tính thể tích khối chóp S.ABC.", {"quantity": "volume", "solid": "S.ABC"},
                                  {"measure": "volume_tetrahedron", "point": "S", "target": list("ABC")}),
                                 ask("dist_plane", "cen", "SBC", to="ABC")],
             split="dev", source="W2-EXP-15", composition="ask_angle_lines | ask_volume | centroid->ask_distance_point_plane",
             novelty=NOVEL),
        case("W2-EXP-10A-2", EQA, [("Tính góc giữa AB và (ABC).", {"quantity": "angle", "points_a": ["A", "B"],
                                                                   "points_b": list("ABC")},
                                    {"measure": "cos2_line_plane", "point": "A", "partner": "B", "target": list("ABC")})],
             split="dev", source="W2-EXP-10A-2", composition="ask_angle_line_plane", novelty=EXIST),
    ]
    base = c[4]                                            # dev-sq-centroid-angle-plane
    neg = [
        negative("dev-neg-two-partners", base, {"points_a": ["A", "B"]}, {"FACT_INCOMPLETE"}, split="dev"),
        negative("dev-neg-partner-in-target", base, {"points_a": None, "points_b": ["A", "A", "B", "C"]},
                 {"FACT_INCOMPLETE"}, split="dev"),
        negative("dev-neg-centroid-of-four", base, {"points": list("SABC")}, {"FACT_INCOMPLETE"}, split="dev"),
        negative("dev-neg-negated", base, {"negated": True}, {"NEGATED_CLAUSE"}, split="dev"),
        negative("dev-neg-condition", base, {"role": "condition"}, {"CONDITIONAL_CLAUSE"}, split="dev"),
        negative("dev-neg-wrong-descriptor", base, {"point_kind": "midpoint", "points": ["S", "C"]},
                 {"SOURCE_OBJECT_MISMATCH"}, split="dev"),
        negative("dev-neg-wrong-target", base, {"points_b": list("SBC")}, {"SOURCE_OBJECT_MISMATCH"}, split="dev"),
        negative("W2-EXP-13A", c[2], {"point_kind": "midpoint", "points": ["S", "B"]}, {"SOURCE_OBJECT_MISMATCH"},
                 split="dev", source="W2-EXP-13A", text_patch=("trọng tâm của tam giác SBC", "A"),
                 note="descriptor fact attached to a quote that names a point, not a description"),
    ]
    return c + neg


def holdout() -> list[dict]:
    c = [
        case("ho-cube-centroid-angle-plane", CUBE, [ask("angle_plane", "cen", "A'BD", partner="C'", to="ABCD")],
             split="holdout", composition="centroid->ask_angle_line_plane", novelty=NOVEL),
        case("ho-cube-midpoint-angle-lines", CUBE, [ask("angle_lines", "mid", "C'D'", partner="A", to="BD")],
             split="holdout", composition="midpoint->ask_angle_lines", novelty=NOVEL),
        case("ho-tetra-centroid-angle-plane", TETRA, [ask("angle_plane", "cen", "BCD", partner="A", to="BCD")],
             split="holdout", composition="centroid->ask_angle_line_plane", novelty=NOVEL),
        case("ho-tetra-midpoint-angle-lines", TETRA, [ask("angle_lines", "mid", "CD", partner="A", to="BC")],
             split="holdout", composition="midpoint->ask_angle_lines", novelty=NOVEL),
        case("ho-prism-centroid-area", PRISM, [ask("area", "cen", "A'B'C'", to="BC")], split="holdout",
             composition="centroid->ask_area", novelty=NOVEL),
        case("ho-cuboid-centroid-dist-plane", CUBOID, [ask("dist_plane", "cen", "A'BD", to="ABCD")], split="holdout",
             composition="centroid->ask_distance_point_plane", novelty=NOVEL),
        case("ho-regpyr-centroid-length", REGPYR, [ask("length", "cen", "SAB", to="C")], split="holdout",
             composition="centroid->ask_length", novelty=NOVEL),
        case("ho-rightb-centroid-angle-plane", RIGHTB, [ask("angle_plane", "cen", "ABC", partner="S", to="ABC")],
             split="holdout", composition="centroid->ask_angle_line_plane", novelty=NOVEL),
        case("ho-t120-midpoint-angle-lines", T120, [ask("angle_lines", "mid", "BC", partner="S", to="AC")],
             split="holdout", composition="midpoint->ask_angle_lines", novelty=NOVEL),
        case("ho-cube-centroid-dist-line", CUBE, [ask("dist_line", "cen", "A'BD", to="AC")], split="holdout",
             composition="centroid+orthogonal_projection_line->ask_length", novelty=NOVEL),
        case("ho-prism-midpoint-angle-plane", PRISM, [ask("angle_plane", "mid", "B'C'", partner="A", to="BCC'")],
             split="holdout", composition="midpoint->ask_angle_line_plane", novelty=NOVEL),
        case("ho-regpyr-centroid-angle-lines-reversed", REGPYR,
             [ask("angle_lines", "cen", "SCD", partner="A", reverse=True, to="SB")], split="holdout",
             composition="centroid->ask_angle_lines", novelty=NOVEL),
        case("ho-t120-named-angle-lines", T120, [named_angle_lines("SC", "AB")], split="holdout",
             composition="ask_angle_lines", novelty=PRIM),
        case("ho-cuboid-named-angle-lines", CUBOID, [("Tính góc giữa hai đường thẳng A'C và BD.",
                                                      {"quantity": "angle", "points_a": ["A'", "C"], "points_b": ["B", "D"]},
                                                      {"measure": "cos2_lines", "point": "A'", "partner": "C",
                                                       "target": ["B", "D"]})],
             split="holdout", composition="ask_angle_lines", novelty=PRIM),
        case("ho-rightb-midpoint-area-control", RIGHTB, [ask("area", "mid", "SC", to="AB")], split="holdout",
             composition="midpoint->ask_area", novelty=EXIST),
        case("ho-tetra-centroid-dist-plane", TETRA, [ask("dist_plane", "cen", "ABC", to="ABD")], split="holdout",
             composition="centroid->ask_distance_point_plane", novelty=NOVEL),
    ]
    neg = [
        negative("ho-neg-cube-wrong-partner", c[0], {"points_a": ["B"]}, {"SOURCE_OBJECT_MISMATCH"}, split="holdout"),
        negative("ho-neg-tetra-centroid-of-two", c[2], {"points": ["B", "C"]}, {"FACT_INCOMPLETE"}, split="holdout"),
        negative("ho-neg-prism-unknown-plane-label", c[10], {"points_b": ["B", "C", "K"]},
                 {"UNKNOWN_LABEL", "SOURCE_OBJECT_MISMATCH"}, split="holdout"),
        negative("ho-neg-regpyr-negated", c[11], {"negated": True}, {"NEGATED_CLAUSE"}, split="holdout"),
        negative("ho-neg-t120-lines-vs-planes", c[12], {"points_a": ["S", "C"], "points_b": ["A", "B"]},
                 {"SOURCE_OBJECT_MISMATCH", "NOT_ASKED_IN_SOURCE", "REQUEST_NOT_ANSWERED"}, split="holdout",
                 text_patch=("Tính góc giữa SC và AB.", "Tính góc giữa (SBC) và (ABC)."),
                 note="facts encode two lines; the source asks two planes"),
        negative("ho-neg-cube-two-partners", c[1], {"points_a": ["A", "B"]}, {"FACT_INCOMPLETE"}, split="holdout"),
        negative("ho-neg-rightb-condition", c[7], {"role": "condition"}, {"CONDITIONAL_CLAUSE"}, split="holdout"),
        negative("ho-neg-cube-ambiguous", c[1], {"ambiguous": True}, {"AMBIGUOUS_FACT"}, split="holdout"),
    ]
    return c + neg


def main() -> int:
    for name, cases in (("corpus-dev.json", dev()), ("corpus-holdout.json", holdout())):
        out = HERE / name
        if out.exists():                                   # a locked corpus is never rewritten by its builder
            print(f"refusing to overwrite {out}")
            continue
        out.write_text(json.dumps({"schema": "goal-directed-composition-corpus/1", "run": "goal-directed-function-composition",
                                   "split": name.split("-")[1].split(".")[0],
                                   "provenance": "AGENT_AUTHORED_WITH_INDEPENDENT_ORACLE_NOT_HUMAN_VALIDATED",
                                   "cases": cases}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {out} ({len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
