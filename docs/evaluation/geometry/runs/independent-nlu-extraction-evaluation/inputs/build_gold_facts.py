# -*- coding: utf-8 -*-
"""Build `gold_facts.json`: the implementer-authored faithful Typed-Fact extraction of every corpus case.

Rule: encode what the text says, following the PRODUCT prompt rules (`app/ai/fact_extraction.py::SYSTEM_PROMPT`).
What the TypedFact schema cannot express (trapezoid/parallelogram bases, distance to a SEGMENT, face centres,
display/interaction, explanation, optimisation, context references) is an `unsupported` fact — never a nearby
expressible approximation. Authoring errors may be fixed before the lock (logged in `gold_authoring_log.md`);
an encoding is never changed only because the deterministic route refuses it.

    python build_gold_facts.py      # writes gold_facts.json next to this file, verifying every quote
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS = json.loads((HERE / "corpus-authoring" / "corpus.json").read_text(encoding="utf-8"))
TEXT = {c["id"]: c["source_text"] for c in CORPUS["cases"]}
CASES: dict[str, dict] = {}
_cur: dict = {}


def case(cid: str, **meta) -> None:
    global _cur
    _cur = {"facts": [], **meta}
    CASES[cid] = _cur
    _cur["_id"] = cid


def _f(kind: str, role: str, quote: str | list[str], **kw) -> dict:
    quotes = [quote] if isinstance(quote, str) else quote
    for q in quotes:
        assert q in TEXT[_cur["_id"]], f"{_cur['_id']}: quote not in source: {q!r}"
    f = {"id": f"f{len(_cur['facts']) + 1}", "kind": kind, "role": role, "quotes": quotes,
         **{k: v for k, v in kw.items() if v is not None}}
    _cur["facts"].append(f)
    return f


def solid(q, name, typ, **kw): return _f("solid", "premise", q, solid=name, solid_type=typ, **kw)
def shape(q, pts, sh, value=None): return _f("polygon_shape", "premise", q, points=list(pts), shape=sh, value=value)
def perp(q, a, b, negated=None): return _f("perpendicular", "premise", q, points_a=list(a), points_b=list(b), negated=negated)
def seg(q, pts, v, role="premise"): return _f("length", role, q, points=list(pts), measure="segment", value=v)
def edge(q, name, v, role="premise"): return _f("length", role, q, solid=name, measure="edge", value=v)
def right(q, at, pts): return _f("right_angle", "premise", q, at=at, points=list(pts))
def mid(q, p, pts): return _f("point_def", "premise", q, point=p, point_kind="midpoint", points=list(pts))
def proj(q, p, at, pts): return _f("projection", "premise", q, point=p, at=at, points=list(pts))
def unsup(q, role="question", reason=None, rid=None): return _f("unsupported", role, q, reason=reason, rid=rid)
def ask(rid, q, quantity, **kw): return _f("question", "question", q, quantity=quantity, rid=rid, **kw)
def inter(rid, q, a, b): return _f("intersection_line", "question", q, points_a=list(a), points_b=list(b), rid=rid)


def alt(f: dict, **override) -> None:
    f.setdefault("alternatives", []).append(override)


def aa(q, v, solid_name):
    """The vertical edge AA' of a box/prism: a named segment, or equally the solid's height / lateral edge."""
    f = seg(q, ("A", "A'"), v)
    alt(f, points=None, measure="height", solid=solid_name)
    alt(f, points=None, measure="lateral_edge", solid=solid_name)
    return f


PYR = ("S", "A")
ABCD, SBC, ABC = "ABCD", "SBC", "ABC"

# ── dev ───────────────────────────────────────────────────────────────────────────────────────────────────────────
case("D01")
solid("Cho hình chóp S.ABCD", "S.ABCD", "pyramid"); shape("đáy ABCD là hình vuông cạnh 2", ABCD, "square", "2")
perp("SA vuông góc với mặt phẳng đáy", PYR, ABCD); seg("SA = 2", PYR, "2")
ask("r1", "Tính khoảng cách từ điểm A đến mặt phẳng (SBC)", "distance", points_a=["A"], points_b=list(SBC))

case("D02")
solid("Hình chóp S.ABCD", "S.ABCD", "pyramid"); shape("Hình chóp S.ABCD đáy là hình vuông cạnh bằng 2", ABCD, "square", "2")
perp("SA ⊥ (ABCD)", PYR, ABCD); seg("SA = 2", PYR, "2")
ask("r1", "Hỏi điểm A cách mặt phẳng SBC một khoảng bằng bao nhiêu?", "distance", points_a=["A"], points_b=list(SBC))

case("D03")
solid("cho chóp S.ABCD", "S.ABCD", "pyramid"); shape("cho chóp S.ABCD, đáy hình vuông cạnh 2", ABCD, "square", "2")
seg("SA=2", PYR, "2"); perp("SA vuông góc đáy", PYR, ABCD)
ask("r1", "khoảng cách từ A tới mp(SBC) là bao nhiêu vậy ạ", "distance", points_a=["A"], points_b=list(SBC))

for cid, quote, rid_kind in (("D04", "Tính khoảng cách từ S đến đường thẳng BC", "line"),
                             ("D05", "Tính khoảng cách từ S đến đoạn thẳng BC", "segment")):
    case(cid, schema_gap_rids=["r1"] if rid_kind == "segment" else [])
    solid("Cho hình chóp S.ABCD", "S.ABCD", "pyramid")
    # Audit amendment: the two right angles are expressible (prompt rule 1) and, in the plane, force AB ∥ CD.
    right("đáy ABCD là hình thang vuông tại A và D", "A", "BD"); right("đáy ABCD là hình thang vuông tại A và D", "D", "AC")
    seg("AB = AD = 2", "AB", "2"); seg("AB = AD = 2", "AD", "2"); seg("CD = 4", "CD", "4")
    perp("Cạnh SA vuông góc với đáy", PYR, ABCD); seg("SA = 2", PYR, "2")
    if rid_kind == "line":
        ask("r1", quote, "distance", points_a=["S"], points_b=["B", "C"])
    else:
        unsup(quote, reason="distance to a segment: no schema quantity", rid="r1")

case("D06")
solid("Hình chóp S.ABCD", "S.ABCD", "pyramid"); shape("Hình chóp S.ABCD có đáy là hình vuông cạnh 2", ABCD, "square", "2")
perp("SA ⊥ (ABCD)", PYR, ABCD); seg("SA = 2", PYR, "2")
ask("r1", "Tính cos² của góc giữa đường thẳng SC và mặt phẳng (ABCD)", "angle", points_a=["S", "C"], points_b=list(ABCD))

case("D07")
solid("Cho hình chóp S.ABCD", "S.ABCD", "pyramid"); shape("Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2", ABCD, "square", "2")
perp("SA vuông góc với đáy", PYR, ABCD); seg("SA = 2", PYR, "2")
ask("r1", "Tính khoảng cách từ trung điểm của cạnh SC đến mặt phẳng (ABCD)", "distance", point_kind="midpoint",
    points=["S", "C"], points_b=list(ABCD))


def tetra_perp(q):
    for a, b in (("A", "B"), ("A", "C"), ("B", "C")):
        perp(q, ("O", a), ("O", b))


case("D08")
solid("Tứ diện OABC", "OABC", "tetrahedron"); tetra_perp("OA, OB, OC đôi một vuông góc")
seg("OA = 2", "OA", "2"); seg("OB = 3", "OB", "3"); seg("OC = 6", "OC", "6")
proj("Gọi H là hình chiếu vuông góc của O lên mặt phẳng (ABC)", "O", "H", ABC)
q = ask("r1", "Tính độ dài OH", "length", points=["O", "H"]); alt(q, quantity="distance", points=None, points_a=["O"], points_b=list(ABC))

CUBE = "ABCD.A'B'C'D'"
case("D09")
solid("Cho hình lập phương ABCD.A'B'C'D' cạnh 2", CUBE, "cube"); edge("Cho hình lập phương ABCD.A'B'C'D' cạnh 2", CUBE, "2")
q = ask("r1", "Tính khoảng cách từ trọng tâm tam giác A'BD đến đỉnh C'", "length", point_kind="centroid",
        points=["A'", "B", "D"], points_b=["C'"])
alt(q, quantity="distance")

case("D10")
solid("Cho hình chóp S.ABC", "S.ABC", "pyramid"); right("đáy ABC là tam giác vuông tại B", "B", "AC")
seg("AB = 3", "AB", "3"); seg("BC = 4", "BC", "4"); perp("SA vuông góc với (ABC)", PYR, ABC); seg("SA = 4", PYR, "4")
ask("r1", "Tính thể tích khối chóp S.ABC", "volume", solid="S.ABC")
ask("r2", "khoảng cách từ A đến mặt phẳng (SBC)", "distance", points_a=["A"], points_b=list(SBC))

PRISM = "ABC.A'B'C'"
case("D11")
solid("Cho lăng trụ đứng ABC.A'B'C'", PRISM, "prism", right=True); right("đáy ABC vuông tại A", "A", "BC")
seg("AB = 3", "AB", "3"); seg("AC = 4", "AC", "4"); aa("cạnh bên AA' = 6", "6", PRISM)
proj("Hãy dựng hình chiếu vuông góc của A lên đường thẳng BC, gọi điểm đó là H", "A", "H", "BC")
ask("r2", "sau đó tính độ dài đoạn A'H", "length", points=["A'", "H"])

case("D12")
solid("Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a", CUBE, "cube"); edge("Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a", CUBE, "a")
ask("r1", "Tính độ dài đường chéo AC'", "length", points=["A", "C'"])
ask("r2", "Tính góc giữa hai đường thẳng AB' và BC'", "angle", points_a=["A", "B'"], points_b=["B", "C'"])
ask("r3", "Tính khoảng cách giữa hai đường thẳng đó", "distance", points_a=["A", "B'"], points_b=["B", "C'"])

case("D13")
ask("r1", "Giờ tính độ dài đoạn AH vừa dựng giúp mình", "length", points=["A", "H"])
case("D14")
unsup("Cho điểm đó nhấp nháy để mình dễ theo dõi", reason="display interaction on an unresolved reference", rid="r1")

case("D15")
solid("Cho hình chóp S.ABC", "S.ABC", "pyramid"); right("đáy ABC là tam giác vuông tại A", "A", "BC")
seg("AB = 3", "AB", "3"); seg("AC = 4", "AC", "4"); seg("BC = 6", "BC", "6")
perp("SA vuông góc với đáy", PYR, ABC); seg("SA = 2", PYR, "2")
ask("r1", "Tính thể tích khối chóp", "volume", solid="S.ABC")

case("D16")
solid("Cho hình chóp S.ABCD", "S.ABCD", "pyramid"); shape("đáy là hình vuông cạnh 3", ABCD, "square", "3")
perp("SA vuông góc với mặt đáy", PYR, ABCD)
ask("r1", "Tính thể tích khối chóp S.ABCD", "volume", solid="S.ABCD")

# ── locked ────────────────────────────────────────────────────────────────────────────────────────────────────────
for cid, sq, a, b, c, qq in (
        ("L01", "Cho hình hộp chữ nhật ABCD.A'B'C'D'", "AB = 3", "AD = 4", "AA' = 12", "Tính độ dài đường chéo AC'"),
        ("L02", "Một hình hộp chữ nhật ABCD.A'B'C'D'", "AB = 3", "AD = 4", "AA' = 12", "Đường chéo AC' dài bao nhiêu?"),
        ("L03", "hình hộp chữ nhật ABCD.A'B'C'D'", "AB=3", "AD=4", "AA'=12", "đoạn AC' bằng mấy")):
    case(cid)
    solid(sq, CUBE, "cuboid"); seg(a, "AB", "3"); seg(b, "AD", "4"); aa(c, "12", CUBE)
    ask("r1", qq, "length", points=["A", "C'"])

case("L04")
solid("Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2", CUBE, "cube"); edge("Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2", CUBE, "2")
ask("r1", "Tính khoảng cách từ A đến mặt phẳng (A'BD)", "distance", points_a=["A"], points_b=["A'", "B", "D"])
case("L05")
solid("ABCD.A'B'C'D' là hình lập phương có cạnh 2", CUBE, "cube"); edge("ABCD.A'B'C'D' là hình lập phương có cạnh 2", CUBE, "2")
ask("r1", "Điểm A cách mặt phẳng (A'BD) bao nhiêu", "distance", points_a=["A"], points_b=["A'", "B", "D"])


def rect345(sq, sh, a, b, p, sa):
    solid(sq, "S.ABCD", "pyramid"); shape(sh, ABCD, "rectangle"); seg(a, "AB", "3"); seg(b, "AD", "4")
    perp(p, PYR, ABCD); seg(sa, PYR, "5")


case("L06")
rect345("Cho hình chóp S.ABCD", "đáy ABCD là hình chữ nhật", "AB = 3", "AD = 4", "Cạnh bên SA vuông góc với đáy", "SA = 5")
ask("r1", "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD)", "angle", points_a=["S", "C"], points_b=list(ABCD))
case("L07", asks_degrees=["r1"])
rect345("Hình chóp S.ABCD", "Hình chóp S.ABCD: đáy hình chữ nhật", "AB = 3", "AD = 4", "SA ⊥ (ABCD)", "SA = 5")
ask("r1", "Đường thẳng SC tạo với mặt đáy một góc bằng bao nhiêu độ?", "angle", points_a=["S", "C"], points_b=list(ABCD))
case("L08", schema_gap_rids=["r1", "r2"])
rect345("Cho chóp S.ABCD", "đáy là hcn ABCD", "AB = 3", "AD = 4", "SA vuông góc mp đáy", "SA = 5")
unsup("Vẽ cho mình góc giữa SC và mặt phẳng ABCD", reason="construct an angle: no schema request", rid="r1")
unsup("rồi giải thích vì sao đó chính là góc cần tìm", reason="explanation: no schema request", rid="r2")
for cid, qq in (("L09", "Tính độ dài SC"), ("L10", "Tính SC²")):
    case(cid, schema_gap_rids=["r1"] if cid == "L10" else [])
    rect345("Cho hình chóp S.ABCD", "đáy là hình chữ nhật ABCD", "AB = 3", "AD = 4", "SA vuông góc với đáy", "SA = 5")
    if cid == "L09":
        ask("r1", qq, "length", points=["S", "C"])
    else:   # audit amendment: a squared length has no schema quantity; `length SC` would be an approximation
        unsup(qq, reason="squared length: no schema quantity", rid="r1")

for cid, qq, gap in (("L11", "Tính khoảng cách từ B đến đường thẳng SD", False),
                     ("L12", "Tính khoảng cách từ B đến đoạn thẳng SD", True)):
    case(cid, schema_gap_rids=["r1"] if gap else [])
    solid("Cho hình chóp S.ABCD", "S.ABCD", "pyramid")
    unsup("đáy ABCD là hình bình hành", role="premise", reason="parallelogram base: no schema shape")
    seg("AB = 2", "AB", "2"); seg("AD = √2", "AD", "√2")
    unsup("góc BAD = 135°", role="premise", reason="angle premise: no schema fact")
    perp("SA vuông góc với mặt phẳng đáy", PYR, ABCD); seg("SA = 1", PYR, "1")
    if gap:
        unsup(qq, reason="distance to a segment: no schema quantity", rid="r1")
    else:
        ask("r1", qq, "distance", points_a=["B"], points_b=["S", "D"])

for cid, qq in (("L13", "Tính cos² của góc giữa đường chéo AC' và mặt phẳng (ABCD)"),
                ("L14", "Tính góc giữa đường chéo AC' và mặt phẳng (ABCD)")):
    case(cid)
    solid("Cho hình hộp chữ nhật ABCD.A'B'C'D'", CUBE, "cuboid"); seg("AB = 3", "AB", "3"); seg("AD = 4", "AD", "4")
    aa("AA' = 12", "12", CUBE)
    ask("r1", qq, "angle", points_a=["A", "C'"], points_b=list(ABCD))

for cid, qq, plane in (("L15", "Tính khoảng cách từ điểm A' đến mặt phẳng (ABC'D')", ["A", "B", "C'", "D'"]),
                       ("L16", "Tính khoảng cách từ điểm A' đến mặt phẳng (ABC'D)", ["A", "B", "C'", "D"])):
    case(cid)
    solid("Cho hình lập phương ABCD.A'B'C'D' cạnh 2", CUBE, "cube"); edge("Cho hình lập phương ABCD.A'B'C'D' cạnh 2", CUBE, "2")
    ask("r1", qq, "distance", points_a=["A'"], points_b=plane)

case("L17")
solid("Cho hình chóp S.ABCD", "S.ABCD", "pyramid"); shape("đáy là hình chữ nhật ABCD", ABCD, "rectangle")
perp("SA vuông góc với đáy", PYR, ABCD)
inter("r1", "Tìm giao tuyến của hai mặt phẳng (SAB) và (SCD)", "SAB", "SCD")
case("L18")
solid("Cho hình chóp S.ABCD", "S.ABCD", "pyramid")
unsup("đáy là hình bình hành", role="premise", reason="parallelogram base: no schema shape")
inter("r1", "Tìm giao tuyến của mặt phẳng (SAC) với mặt phẳng (SBD)", "SAC", "SBD")

case("L19")
solid("Tứ diện OABC", "OABC", "tetrahedron"); tetra_perp("OA, OB, OC đôi một vuông góc")
for e in ("OA", "OB", "OC"):
    seg("OA = OB = OC = 3", e, "3")
q = ask("r1", "Tính khoảng cách từ O đến trọng tâm của tam giác ABC", "length", point_kind="centroid",
        points=list(ABC), points_b=["O"])
alt(q, quantity="distance")

case("L20")
solid("Cho hình lập phương ABCD.A'B'C'D' cạnh a", CUBE, "cube"); edge("Cho hình lập phương ABCD.A'B'C'D' cạnh a", CUBE, "a")
mid("Lấy trung điểm của cạnh CC' rồi đặt tên nó là M", "M", ("C", "C'"))
ask("r1", "Tính độ dài đoạn AM", "length", points=["A", "M"])

case("L21", schema_gap_rids=["r1"])
solid("Cho lăng trụ đứng ABC.A'B'C'", PRISM, "prism", right=True); right("đáy là tam giác vuông cân tại A", "A", "BC")
seg("AB = AC = 2", "AB", "2"); seg("AB = AC = 2", "AC", "2"); aa("cạnh bên AA' = 4", "4", PRISM)
unsup("Tính khoảng cách từ C đến tâm của mặt bên ABB'A'", reason="face centre: no schema point kind", rid="r1")

case("L22")
solid("Cho hình chóp S.ABC", "S.ABC", "pyramid"); perp("SA vuông góc với mặt phẳng (ABC)", PYR, ABC)
right("tam giác ABC vuông tại B", "B", "AC"); seg("AB = BC = 2", "AB", "2"); seg("AB = BC = 2", "BC", "2"); seg("SA = 2", PYR, "2")
ask("r1", "Tính độ dài đoạn nối A với chân đường vuông góc hạ từ A xuống mặt phẳng (SBC)", "distance",
    points_a=["A"], points_b=list(SBC))

case("L23")
solid("Tứ diện OABC", "OABC", "tetrahedron"); tetra_perp("ba cạnh OA, OB, OC đôi một vuông góc")
seg("OA = 1", "OA", "1"); seg("OB = OC = 2", "OB", "2"); seg("OB = OC = 2", "OC", "2")
ask("r1", "Tính thể tích tứ diện", "volume", solid="OABC")
ask("r2", "diện tích tam giác ABC", "area", points=list(ABC))
ask("r3", "rồi suy ra khoảng cách từ O đến (ABC)", "distance", points_a=["O"], points_b=list(ABC))

case("L24")
solid("Cho lăng trụ đứng ABC.A'B'C'", PRISM, "prism", right=True); right("đáy ABC là tam giác vuông tại A", "A", "BC")
seg("AB = 1", "AB", "1"); seg("AC = 2", "AC", "2"); aa("chiều cao AA' = 2", "2", PRISM)
ask("r1", "a) Tính thể tích khối lăng trụ", "volume", solid=PRISM)
ask("r2", "b) Tính góc giữa hai mặt phẳng (A'BC) và (ABC)", "angle", points_a=["A'", "B", "C"], points_b=list(ABC))

case("L25")
rect345("Cho hình chóp S.ABCD", "đáy ABCD là hình chữ nhật", "AB = 3", "AD = 4", "SA ⊥ (ABCD)", "SA = 5")
proj("Hãy dựng hình chiếu vuông góc của A trên mặt phẳng (SBC), gọi là H", "A", "H", SBC)
ask("r2", "rồi tính độ dài AH", "length", points=["A", "H"])

case("L26")
solid("Cho hình chóp S.ABCD", "S.ABCD", "pyramid"); shape("đáy là hình vuông cạnh a", ABCD, "square", "a")
perp("SA ⊥ đáy", PYR, ABCD); seg("SA = a", PYR, "a")
ask("r1", "Tính thể tích khối chóp", "volume", solid="S.ABCD")
ask("r2", "góc giữa SB với mặt phẳng đáy", "angle", points_a=["S", "B"], points_b=list(ABCD))

case("L27")
solid("Cho hình hộp chữ nhật ABCD.A'B'C'D'", CUBE, "cuboid"); seg("AB = 1", "AB", "1"); seg("AD = 2", "AD", "2")
aa("AA' = 2", "2", CUBE)
ask("r1", "Tính BD'", "length", points=["B", "D'"])
ask("r2", "tính thể tích khối hộp", "volume", solid=CUBE)
ask("r3", "tính khoảng cách giữa hai đường thẳng AA' và BD'", "distance", points_a=["A", "A'"], points_b=["B", "D'"])

case("L28")
solid("Cho hình chóp S.ABC", "S.ABC", "pyramid"); perp("SA vuông góc với đáy", PYR, ABC)
right("đáy ABC là tam giác vuông cân tại A", "A", "BC"); seg("AB = AC = 2", "AB", "2"); seg("AB = AC = 2", "AC", "2")
seg("SA = 2", PYR, "2"); mid("Gọi M là trung điểm BC", "M", "BC")
ask("r1", "Tính độ dài SM", "length", points=["S", "M"])
ask("r2", "dựa vào SM tính diện tích tam giác SBC", "area", points=list(SBC))

case("L29")
solid("Cho hình lập phương ABCD.A'B'C'D' cạnh a", CUBE, "cube"); edge("Cho hình lập phương ABCD.A'B'C'D' cạnh a", CUBE, "a")
ask("r1", "Tính khoảng cách giữa hai đường thẳng BD và B'C", "distance", points_a=["B", "D"], points_b=["B'", "C"])
ask("r2", "hai đường thẳng này hợp với nhau một góc bao nhiêu?", "angle", points_a=["B", "D"], points_b=["B'", "C"])

case("L30")
solid("Cho hình chóp S.ABCD", "S.ABCD", "pyramid"); shape("đáy ABCD là hình vuông cạnh 4", ABCD, "square", "4")
perp("SA vuông góc với đáy", PYR, ABCD); seg("SA = 3", PYR, "3")
ask("r1", "Tính SC", "length", points=["S", "C"])
ask("r2", "tính cos² góc giữa SC và đáy", "angle", points_a=["S", "C"], points_b=list(ABCD))
ask("r3", "tính thể tích khối chóp", "volume", solid="S.ABCD")

# Group E: only the current turn is sent (the product is single-turn); context references are unsupported.
case("L31")
unsup("Khoảng cách từ giao điểm ấy tới mặt đáy ABCD bằng bao nhiêu?", reason="context reference 'giao điểm ấy'", rid="r1")
case("L32", schema_gap_rids=["r1", "r2"])
unsup("Đổi màu đường thẳng vừa dựng sang đỏ", reason="display interaction", rid="r1")
unsup("ẩn mặt đáy đi cho dễ nhìn", reason="display interaction", rid="r2")
case("L33")
unsup("Tính tiếp độ dài của đoạn mình vừa dựng ở trên nhé", reason="context reference", rid="r1")
case("L34", schema_gap_rids=["r1"])
unsup("Làm nổi bật điểm đó giúp mình", reason="display interaction on a context reference", rid="r1")
case("L35", schema_gap_rids=["r1"])
unsup("Quay hình sao cho nhìn thẳng từ trên xuống mặt (OAB) nhé", reason="camera interaction", rid="r1")
case("L36", schema_gap_rids=["r1"])
unsup("Ẩn tên các điểm khác, chỉ giữ lại tên điểm vừa dựng", reason="display interaction", rid="r1")
ask("r2", "sau đó tính SM", "length", points=["S", "M"])

case("L37")
solid("Cho hình chóp S.ABCD", "S.ABCD", "pyramid"); shape("đáy ABCD là hình chữ nhật", ABCD, "rectangle")
seg("AB = 2", "AB", "2"); seg("AD = 5", "AD", "5"); seg("SA = 4", PYR, "4")
perp("SA không vuông góc với mặt đáy", PYR, ABCD, negated=True)
ask("r1", "Tính thể tích khối chóp S.ABCD", "volume", solid="S.ABCD")

case("L38")
solid("Cho hình lập phương ABCD.A'B'C'D'", CUBE, "cube")
edge("Nếu cạnh của hình lập phương bằng 3", CUBE, "3", role="condition")
ask("r1", "thì đường chéo AC' bằng bao nhiêu?", "length", points=["A", "C'"])

case("L39")
solid("Cho hình hộp chữ nhật ABCD.A'B'C'D'", CUBE, "cuboid")
inter("r1", "Tìm giao tuyến của mặt phẳng (ABCD) và mặt phẳng (A'B'C'D')", ABC, ["A'", "B'", "C'"])   # rule 7: ba điểm

case("L40")
solid("Cho hình chóp S.ABC", "S.ABC", "pyramid"); shape("đáy ABC là tam giác đều cạnh 2", ABC, "equilateral_triangle", "2")
seg("SA = SB = 3", PYR, "3"); seg("SA = SB = 3", ("S", "B"), "3")
ask("r1", "Tính thể tích khối chóp S.ABC", "volume", solid="S.ABC")

case("L41")
solid("Cho hình chóp S.ABC", "S.ABC", "pyramid"); perp("SA vuông góc với đáy", PYR, ABC)
right("tam giác ABC vuông cân tại A", "A", "BC"); seg("AB = AC = 2", "AB", "2"); seg("AB = AC = 2", "AC", "2")
seg("SA = 2", PYR, "2"); mid("Gọi M là trung điểm của BC", "M", "BC")
_f("perpendicular", "prove", "Chứng minh BC vuông góc với mặt phẳng (SAM)", points_a=["B", "C"], points_b=["S", "A", "M"], rid="r1")
ask("r2", "tính khoảng cách từ A đến mặt phẳng (SBC)", "distance", points_a=["A"], points_b=list(SBC))

case("L42", schema_gap_rids=["r1"])
solid("Cho hình lập phương ABCD.A'B'C'D' cạnh 1", CUBE, "cube"); edge("Cho hình lập phương ABCD.A'B'C'D' cạnh 1", CUBE, "1")
unsup("M là điểm di động trên cạnh CD", role="premise", reason="moving point")
unsup("Tìm giá trị lớn nhất của diện tích tam giác A'BM", reason="optimisation over a moving point", rid="r1")

case("L43")
solid("Cho hình chóp S.ABCD", "S.ABCD", "pyramid"); shape("đáy là hình chữ nhật", ABCD, "rectangle")
seg("AB = 2", "AB", "2"); seg("AD = 3", "AD", "3"); perp("SA ⊥ (ABCD)", PYR, ABCD); seg("SA = 4", PYR, "4")
mid("Gọi M là trung điểm của SB", "M", "SB"); mid("M là trung điểm của SD", "M", "SD")
ask("r1", "Tính độ dài đoạn AM", "length", points=["A", "M"])

case("L44")
solid("Cho hình lập phương ABCD.A'B'C'D'", CUBE, "cube"); edge("có cạnh bằng 2", CUBE, "2")
seg("đường chéo AC' = 4", ("A", "C'"), "4")
ask("r1", "Tính thể tích khối lập phương", "volume", solid=CUBE)

# ── write ─────────────────────────────────────────────────────────────────────────────────────────────────────────
missing = set(TEXT) - set(CASES)
assert not missing, f"cases without gold: {sorted(missing)}"
for c in CASES.values():
    c.pop("_id")
    for f in c["facts"]:
        for k in ("points", "points_a", "points_b"):
            if isinstance(f.get(k), str):
                f[k] = list(f[k])
out = {"schema": "NLU_GOLD_FACTS/1", "author": "main agent (implementer), faithful to the product prompt rules",
       "independence": "IMPLEMENTER_AUTHORED; corpus semantics and values are the blind author's", "cases": CASES}
(HERE / "gold_facts.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"gold_facts.json: {len(CASES)} cases, {sum(len(c['facts']) for c in CASES.values())} facts")
