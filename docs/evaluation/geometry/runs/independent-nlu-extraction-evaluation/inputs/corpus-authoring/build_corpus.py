# Builds corpus.json from the hand-authored case table below. Stdlib only.
# Expected values here are hand-computed; agent1_oracle.py recomputes them from coordinates.
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
CB = "agent1_oracle.py"


def E(kind, ref, named=True):
    return {"kind": kind, "ref": ref, "named_in_text": named}


def P(rel, ops, val, quote, where=None):
    d = {"relation": rel, "operands": ops, "value": val, "quote": quote}
    if where:
        d["quote_in"] = where
    return d


def R(rid, intent, qty, ops, quote, **extra):
    d = {"rid": rid, "intent": intent, "quantity": qty,
         "operands": [{"kind": k, "ref": r} for k, r in ops], "quote": quote}
    d.update(extra)
    return d


def LEN(vs, exact, unit=None):
    d = {"value_squared": vs, "exact": exact, "computed_by": CB}
    if unit:
        d["unit"] = unit
    return d


def SQ(v, vs):  # quantity length_squared: the value itself is rational
    return {"value": v, "value_squared": vs, "exact": v, "computed_by": CB}


def VOL(v, vs, exact, unit=None):
    d = {"value": exact, "value_squared": vs, "exact": exact, "computed_by": CB}
    if unit:
        d["unit"] = unit
    return d


def AREA(vs, exact):
    return {"value": exact, "value_squared": vs, "exact": exact, "computed_by": CB}


def ANG(c2, deg, exact):
    return {"cos_squared": c2, "degrees": deg, "exact": exact, "computed_by": CB}


def COS2(c2):  # quantity cos_squared_angle: the requested value IS cos^2
    return {"value": c2, "cos_squared": c2, "computed_by": CB}


cases = []


def C(split, group, sid, text, ents, prem, reqs, disp, traps, exp=None, n=None,
      missing=None, notes="", context=None, **extra):
    d = {"split": split, "group": group, "structure_id": sid, "source_text": text,
         "context": context, "entities": ents, "premises": prem, "requests": reqs,
         "n_source_requests": len(reqs) if n is None else n,
         "missing_or_ambiguous": missing or [], "gold_disposition": disp,
         "hallucination_traps": traps, "expected_values": exp or {}, "notes": notes}
    d.update(extra)
    cases.append(d)


SABCD = E("solid", "S.ABCD")
SABC = E("solid", "S.ABC")
CUBE = E("solid", "ABCD.A'B'C'D'")
OABC = E("solid", "OABC")
PRISM = E("solid", "ABC.A'B'C'")
PERP_SA = "perpendicular_line_plane"

# ============================ DEV =================================
# P1: S.ABCD square side 2, SA ⊥ base, SA = 2
for text, q_sq, q_perp, q_sa, q_req in [
    ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng đáy và SA = 2. Tính khoảng cách từ điểm A đến mặt phẳng (SBC).",
     "đáy ABCD là hình vuông cạnh 2", "SA vuông góc với mặt phẳng đáy", "SA = 2",
     "Tính khoảng cách từ điểm A đến mặt phẳng (SBC)"),
    ("Hình chóp S.ABCD đáy là hình vuông cạnh bằng 2, cạnh bên SA ⊥ (ABCD), SA = 2. Hỏi điểm A cách mặt phẳng SBC một khoảng bằng bao nhiêu?",
     "đáy là hình vuông cạnh bằng 2", "SA ⊥ (ABCD)", "SA = 2",
     "điểm A cách mặt phẳng SBC một khoảng bằng bao nhiêu"),
    ("cho chóp S.ABCD, đáy hình vuông cạnh 2, SA=2 và SA vuông góc đáy. khoảng cách từ A tới mp(SBC) là bao nhiêu vậy ạ",
     "đáy hình vuông cạnh 2", "SA vuông góc đáy", "SA=2",
     "khoảng cách từ A tới mp(SBC) là bao nhiêu"),
]:
    C("dev", "A", "S01", text, [SABCD, E("point", "A"), E("plane", "(SBC)")],
      [P("square_base", ["ABCD"], "2", q_sq), P(PERP_SA, ["SA", "(ABCD)"], None, q_perp),
       P("length", ["SA"], "2", q_sa)],
      [R("r1", "compute_value", "distance_point_plane", [("point", "A"), ("plane", "(SBC)")], q_req)],
      "answer_all", ["regular pyramid (hình chóp đều)", "distance equals SA or AB (=2)"],
      {"r1": LEN("2", "√2")},
      notes="Three surface forms (textbook, '⊥' + 'cách ... bao nhiêu', casual lower-case 'mp(SBC)') of one request.")

TRAP_TXT = "Cho hình chóp S.ABCD có đáy ABCD là hình thang vuông tại A và D, AB = AD = 2, CD = 4. Cạnh SA vuông góc với đáy và SA = 2. "
TRAP_PREM = [P("right_trapezoid", ["ABCD", "A", "D"], None, "đáy ABCD là hình thang vuông tại A và D"),
             P("length", ["AB", "AD"], "2", "AB = AD = 2"), P("length", ["CD"], "4", "CD = 4"),
             P(PERP_SA, ["SA", "(ABCD)"], None, "SA vuông góc với đáy"), P("length", ["SA"], "2", "SA = 2")]
C("dev", "B", "S02", TRAP_TXT + "Tính khoảng cách từ S đến đường thẳng BC.",
  [SABCD, E("point", "S"), E("line", "BC")], TRAP_PREM,
  [R("r1", "compute_value", "distance_point_line", [("point", "S"), ("line", "BC")],
     "Tính khoảng cách từ S đến đường thẳng BC")],
  "answer_all", ["distance to segment BC (=SB)", "foot of perpendicular is B"],
  {"r1": LEN("6", "√6")},
  notes="Contrast with D05. Foot of the perpendicular from S to line BC is the projection of A, lying on the extension of CB beyond B (angle ABC is obtuse).")
C("dev", "B", "S03", TRAP_TXT + "Tính khoảng cách từ S đến đoạn thẳng BC.",
  [SABCD, E("point", "S"), E("segment", "BC")], TRAP_PREM,
  [R("r1", "compute_value", "distance_point_segment", [("point", "S"), ("segment", "BC")],
     "Tính khoảng cách từ S đến đoạn thẳng BC")],
  "answer_all", ["distance to line BC (=√6)"],
  {"r1": LEN("8", "2√2")},
  notes="Contrast with D04: perpendicular foot falls outside segment BC, so the nearest point of the segment is the endpoint B; answer SB.")
C("dev", "B", "S04",
  "Hình chóp S.ABCD có đáy là hình vuông cạnh 2, SA ⊥ (ABCD) và SA = 2. Tính cos² của góc giữa đường thẳng SC và mặt phẳng (ABCD).",
  [SABCD, E("line", "SC"), E("plane", "(ABCD)")],
  [P("square_base", ["ABCD"], "2", "đáy là hình vuông cạnh 2"), P(PERP_SA, ["SA", "(ABCD)"], None, "SA ⊥ (ABCD)"),
   P("length", ["SA"], "2", "SA = 2")],
  [R("r1", "compute_value", "cos_squared_angle", [("line", "SC"), ("plane", "(ABCD)")],
     "Tính cos² của góc giữa đường thẳng SC và mặt phẳng (ABCD)", of="angle_line_plane")],
  "answer_all", ["answer the angle itself instead of cos²", "45° (that is SB, not SC)"],
  {"r1": COS2("2/3")},
  notes="Asks cos² explicitly; returning the angle (arccos(√6/3)) or cos (√6/3) is a wrong quantity.")

C("dev", "C", "S05",
  "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2, SA vuông góc với đáy, SA = 2. Tính khoảng cách từ trung điểm của cạnh SC đến mặt phẳng (ABCD).",
  [SABCD, E("derived_point", "trung điểm của cạnh SC", False), E("plane", "(ABCD)")],
  [P("square_base", ["ABCD"], "2", "đáy là hình vuông cạnh 2"), P(PERP_SA, ["SA", "(ABCD)"], None, "SA vuông góc với đáy"),
   P("length", ["SA"], "2", "SA = 2"),
   P("midpoint_def", ["?", "SC"], None, "trung điểm của cạnh SC")],
  [R("r1", "compute_value", "distance_point_plane", [("derived_point", "midpoint(SC)"), ("plane", "(ABCD)")],
     "Tính khoảng cách từ trung điểm của cạnh SC đến mặt phẳng (ABCD)")],
  "answer_all", ["midpoint of SC named (e.g. M) in the text", "distance from S (=2)"],
  {"r1": LEN("1", "1")}, notes="Unnamed midpoint; answer SA/2.")
C("dev", "C", "S06",
  "Tứ diện OABC có OA, OB, OC đôi một vuông góc, OA = 2, OB = 3, OC = 6. Gọi H là hình chiếu vuông góc của O lên mặt phẳng (ABC). Tính độ dài OH.",
  [OABC, E("derived_point", "H", True), E("plane", "(ABC)"), E("segment", "OH")],
  [P("pairwise_perpendicular", ["OA", "OB", "OC"], None, "OA, OB, OC đôi một vuông góc"),
   P("length", ["OA"], "2", "OA = 2"), P("length", ["OB"], "3", "OB = 3"), P("length", ["OC"], "6", "OC = 6"),
   P("projection_def", ["H", "O", "(ABC)"], None, "Gọi H là hình chiếu vuông góc của O lên mặt phẳng (ABC)")],
  [R("r1", "compute_value", "length", [("segment", "OH")], "Tính độ dài OH",
     accept_equivalent_quantities=["distance_point_plane"])],
  "answer_all", ["H is the centroid of ABC (only true when OA=OB=OC)", "H is the midpoint of an edge"],
  {"r1": LEN("18/7", "3√14/7")}, notes="H defined by words then named; OH = d(O,(ABC)).")
C("dev", "C", "S07",
  "Cho hình lập phương ABCD.A'B'C'D' cạnh 2. Tính khoảng cách từ trọng tâm tam giác A'BD đến đỉnh C'.",
  [CUBE, E("derived_point", "trọng tâm tam giác A'BD", False), E("point", "C'")],
  [P("cube", ["ABCD.A'B'C'D'"], "2", "hình lập phương ABCD.A'B'C'D' cạnh 2"),
   P("centroid_def", ["?", "A'BD"], None, "trọng tâm tam giác A'BD")],
  [R("r1", "compute_value", "length", [("derived_point", "centroid(A'BD)"), ("point", "C'")],
     "Tính khoảng cách từ trọng tâm tam giác A'BD đến đỉnh C'")],
  "answer_all", ["distance from centroid to A (=2√3/3)", "centroid of the whole cube"],
  {"r1": LEN("16/3", "4√3/3")}, notes="Point-to-point distance labeled 'length'. Centroid lies on AC' at 1/3 from A.")

C("dev", "D", "S08",
  "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = 3, BC = 4, SA vuông góc với (ABC) và SA = 4. Tính thể tích khối chóp S.ABC và khoảng cách từ A đến mặt phẳng (SBC).",
  [SABC, E("point", "A"), E("plane", "(SBC)")],
  [P("right_angle", ["ABC", "B"], None, "đáy ABC là tam giác vuông tại B"), P("length", ["AB"], "3", "AB = 3"),
   P("length", ["BC"], "4", "BC = 4"), P(PERP_SA, ["SA", "(ABC)"], None, "SA vuông góc với (ABC)"),
   P("length", ["SA"], "4", "SA = 4")],
  [R("r1", "compute_value", "volume", [("solid", "S.ABC")], "Tính thể tích khối chóp S.ABC"),
   R("r2", "compute_value", "distance_point_plane", [("point", "A"), ("plane", "(SBC)")],
     "khoảng cách từ A đến mặt phẳng (SBC)")],
  "answer_all", ["right angle at A", "AC = 4"],
  {"r1": VOL("8", "64", "8"), "r2": LEN("144/25", "12/5")}, notes="Two independent requests joined by 'và'.")
C("dev", "D", "S09",
  "Cho lăng trụ đứng ABC.A'B'C' có đáy ABC vuông tại A, AB = 3, AC = 4, cạnh bên AA' = 6. Hãy dựng hình chiếu vuông góc của A lên đường thẳng BC, gọi điểm đó là H, sau đó tính độ dài đoạn A'H.",
  [PRISM, E("derived_point", "H", True), E("line", "BC"), E("segment", "A'H")],
  [P("right_prism", ["ABC.A'B'C'"], None, "lăng trụ đứng ABC.A'B'C'"),
   P("right_angle", ["ABC", "A"], None, "đáy ABC vuông tại A"), P("length", ["AB"], "3", "AB = 3"),
   P("length", ["AC"], "4", "AC = 4"), P("length", ["AA'"], "6", "AA' = 6"),
   P("projection_def", ["H", "A", "BC"], None, "hình chiếu vuông góc của A lên đường thẳng BC, gọi điểm đó là H")],
  [R("r1", "construct", "projection", [("point", "A"), ("line", "BC")],
     "dựng hình chiếu vuông góc của A lên đường thẳng BC"),
   R("r2", "compute_value", "length", [("segment", "A'H")], "tính độ dài đoạn A'H", depends_on=["r1"])],
  "answer_all", ["H is the midpoint of BC", "compute only AH (=12/5)"],
  {"r2": LEN("1044/25", "6√29/5")},
  expected_objects={"r1": "H = chân đường cao từ A của tam giác ABC trên BC, BH = 9/5"},
  notes="r2 depends on the object H defined by r1.")
C("dev", "D", "S10",
  "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. Tính độ dài đường chéo AC'. Tính góc giữa hai đường thẳng AB' và BC'. Tính khoảng cách giữa hai đường thẳng đó.",
  [CUBE, E("segment", "AC'"), E("line", "AB'"), E("line", "BC'")],
  [P("cube", ["ABCD.A'B'C'D'"], "a", "hình lập phương ABCD.A'B'C'D' có cạnh bằng a")],
  [R("r1", "compute_value", "length", [("segment", "AC'")], "Tính độ dài đường chéo AC'"),
   R("r2", "compute_value", "angle_line_line", [("line", "AB'"), ("line", "BC'")],
     "Tính góc giữa hai đường thẳng AB' và BC'"),
   R("r3", "compute_value", "distance_line_line", [("line", "AB'"), ("line", "BC'")],
     "Tính khoảng cách giữa hai đường thẳng đó")],
  "answer_all", ["AB' and BC' are perpendicular (90°)", "lines intersect (distance 0)"],
  {"r1": LEN("3", "a√3", "a"), "r2": ANG("1/4", "60", "60°"), "r3": LEN("1/3", "a√3/3", "a")},
  notes="Three independent requests in separate sentences; 'đó' in r3 resolves to AB', BC' within the text.")

C("dev", "E", "S11", "Giờ tính độ dài đoạn AH vừa dựng giúp mình.",
  [E("segment", "AH (from context)", True)],
  [P("square_base", ["ABCD"], "2", "đáy là hình vuông cạnh 2", "context.prior_turn"),
   P(PERP_SA, ["SA", "(ABCD)"], None, "SA ⊥ (ABCD)", "context.prior_turn"),
   P("length", ["SA"], "2", "SA = 2", "context.prior_turn"),
   P("projection_def", ["H", "A", "SB"], None, "hình chiếu vuông góc H của A lên đường thẳng SB", "context.prior_turn")],
  [R("r1", "compute_value", "length", [("segment", "AH")], "tính độ dài đoạn AH vừa dựng")],
  "answer_all", ["H is foot on SC", "AH = 2"],
  {"r1": LEN("2", "√2")},
  context={"prior_turn": "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 2. Dựng hình chiếu vuông góc H của A lên đường thẳng SB.",
           "prior_result": "Đã dựng điểm H trên SB sao cho AH ⊥ SB."},
  notes="Premise quotes come from context.prior_turn (quote_in). Reference resolvable.")
C("dev", "E", "S12", "Cho điểm đó nhấp nháy để mình dễ theo dõi.",
  [E("point", "'điểm đó' (unresolved)", False)], [],
  [R("r1", "interaction", "other", [("point", "<unresolved: điểm đó>")], "Cho điểm đó nhấp nháy")],
  "clarification_required", ["pick any vertex (e.g. S or A)"],
  missing=["No prior scene: 'điểm đó' has no antecedent"], notes="Pure interaction with null context.")

C("dev", "F", "S13",
  "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A với AB = 3, AC = 4, BC = 6; SA vuông góc với đáy, SA = 2. Tính thể tích khối chóp.",
  [SABC],
  [P("right_angle", ["ABC", "A"], None, "tam giác vuông tại A"), P("length", ["AB"], "3", "AB = 3"),
   P("length", ["AC"], "4", "AC = 4"), P("length", ["BC"], "6", "BC = 6"),
   P(PERP_SA, ["SA", "(ABC)"], None, "SA vuông góc với đáy"), P("length", ["SA"], "2", "SA = 2")],
  [R("r1", "compute_value", "volume", [("solid", "S.ABC")], "Tính thể tích khối chóp")],
  "refuse_contradictory", ["ignore BC and answer V = 4", "ignore the right angle and use Heron"],
  missing=["AB² + AC² = 25 ≠ 36 = BC²: right angle at A contradicts the lengths"],
  notes="Over-determined base; any numeric answer silently drops one premise.")
C("dev", "F", "S14",
  "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 3 và SA vuông góc với mặt đáy. Tính thể tích khối chóp S.ABCD.",
  [SABCD],
  [P("square_base", ["ABCD"], "3", "đáy là hình vuông cạnh 3"), P(PERP_SA, ["SA", "(ABCD)"], None, "SA vuông góc với mặt đáy")],
  [R("r1", "compute_value", "volume", [("solid", "S.ABCD")], "Tính thể tích khối chóp S.ABCD")],
  "refuse_missing_info", ["SA = 3 (= side)", "SA = 3√2"],
  missing=["Height SA not given"])

# ============================ LOCKED ==============================
BOX_PREM = lambda q1, q2, q3, qb: [P("rectangular_box", ["ABCD.A'B'C'D'"], None, qb),
                                   P("length", ["AB"], "3", q1), P("length", ["AD"], "4", q2), P("length", ["AA'"], "12", q3)]
for text, q, qb in [
    ("Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 12. Tính độ dài đường chéo AC'.",
     ("AB = 3", "AD = 4", "AA' = 12", "Tính độ dài đường chéo AC'"), "hình hộp chữ nhật ABCD.A'B'C'D'"),
    ("Một hình hộp chữ nhật ABCD.A'B'C'D' có ba kích thước AB = 3, AD = 4 và AA' = 12. Đường chéo AC' dài bao nhiêu?",
     ("AB = 3", "AD = 4", "AA' = 12", "Đường chéo AC' dài bao nhiêu"), "hình hộp chữ nhật ABCD.A'B'C'D'"),
    ("hình hộp chữ nhật ABCD.A'B'C'D' với AB=3, AD=4, AA'=12 thì đoạn AC' bằng mấy",
     ("AB=3", "AD=4", "AA'=12", "đoạn AC' bằng mấy"), "hình hộp chữ nhật ABCD.A'B'C'D'"),
]:
    C("locked", "A", "S20", text, [E("solid", "ABCD.A'B'C'D'"), E("segment", "AC'")],
      BOX_PREM(q[0], q[1], q[2], qb),
      [R("r1", "compute_value", "length", [("segment", "AC'")], q[3])],
      "answer_all", ["AC' is the face diagonal AC (=5)"], {"r1": LEN("169", "13")})
for text, qc, qr in [
    ("Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2. Tính khoảng cách từ A đến mặt phẳng (A'BD).",
     "hình lập phương ABCD.A'B'C'D' có cạnh bằng 2", "Tính khoảng cách từ A đến mặt phẳng (A'BD)"),
    ("Điểm A cách mặt phẳng (A'BD) bao nhiêu, biết ABCD.A'B'C'D' là hình lập phương có cạnh 2?",
     "ABCD.A'B'C'D' là hình lập phương có cạnh 2", "Điểm A cách mặt phẳng (A'BD) bao nhiêu"),
]:
    C("locked", "A", "S21", text, [CUBE, E("point", "A"), E("plane", "(A'BD)")],
      [P("cube", ["ABCD.A'B'C'D'"], "2", qc)],
      [R("r1", "compute_value", "distance_point_plane", [("point", "A"), ("plane", "(A'BD)")], qr)],
      "answer_all", ["distance = AA' (=2)", "half the space diagonal (=√3)"], {"r1": LEN("4/3", "2√3/3")},
      notes="Question precedes the premise in the second wording." if "biết" in text else "")
for text, qr, qs, qp, qsa, qab, qad in [
    ("Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 3, AD = 4. Cạnh bên SA vuông góc với đáy và SA = 5. Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).",
     "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD)", "đáy ABCD là hình chữ nhật", "SA vuông góc với đáy", "SA = 5", "AB = 3", "AD = 4"),
    ("Hình chóp S.ABCD: đáy hình chữ nhật với AB = 3, AD = 4; SA ⊥ (ABCD), SA = 5. Đường thẳng SC tạo với mặt đáy một góc bằng bao nhiêu độ?",
     "Đường thẳng SC tạo với mặt đáy một góc bằng bao nhiêu độ", "đáy hình chữ nhật", "SA ⊥ (ABCD)", "SA = 5", "AB = 3", "AD = 4"),
]:
    C("locked", "A", "S22", text, [SABCD, E("line", "SC"), E("plane", "(ABCD)")],
      [P("rectangle_base", ["ABCD"], None, qs), P("length", ["AB"], "3", qab), P("length", ["AD"], "4", qad),
       P(PERP_SA, ["SA", "(ABCD)"], None, qp), P("length", ["SA"], "5", qsa)],
      [R("r1", "compute_value", "angle_line_plane", [("line", "SC"), ("plane", "(ABCD)")], qr)],
      "answer_all", ["angle SCB or SCD instead of SCA"], {"r1": ANG("1/2", "45", "45°")})
C("locked", "A", "S60",
  "Cho chóp S.ABCD đáy là hcn ABCD (AB = 3, AD = 4), SA = 5 và SA vuông góc mp đáy. Vẽ cho mình góc giữa SC và mặt phẳng ABCD, rồi giải thích vì sao đó chính là góc cần tìm.",
  [SABCD, E("line", "SC"), E("plane", "(ABCD)")],
  [P("rectangle_base", ["ABCD"], None, "đáy là hcn ABCD"), P("length", ["AB"], "3", "AB = 3"),
   P("length", ["AD"], "4", "AD = 4"), P("length", ["SA"], "5", "SA = 5"),
   P(PERP_SA, ["SA", "(ABCD)"], None, "SA vuông góc mp đáy")],
  [R("r1", "construct", "angle_line_plane", [("line", "SC"), ("plane", "(ABCD)")],
     "Vẽ cho mình góc giữa SC và mặt phẳng ABCD"),
   R("r2", "explain", "angle_line_plane", [("line", "SC"), ("plane", "(ABCD)")],
     "giải thích vì sao đó chính là góc cần tìm", depends_on=["r1"])],
  "answer_all", ["user asked for the numeric value (45°)"],
  expected_objects={"r1": "góc SCA (AC là hình chiếu của SC lên (ABCD))"},
  notes="Same geometry as S22 but intents construct + explain: deliberately a different structure_id. Giving only '45°' does not satisfy it.")

PYR35 = "Cho hình chóp S.ABCD có đáy là hình chữ nhật ABCD với AB = 3, AD = 4, SA vuông góc với đáy, SA = 5. "
PYR35_PREM = [P("rectangle_base", ["ABCD"], None, "đáy là hình chữ nhật ABCD"), P("length", ["AB"], "3", "AB = 3"),
              P("length", ["AD"], "4", "AD = 4"), P(PERP_SA, ["SA", "(ABCD)"], None, "SA vuông góc với đáy"),
              P("length", ["SA"], "5", "SA = 5")]
C("locked", "B", "S23", PYR35 + "Tính độ dài SC.", [SABCD, E("segment", "SC")], PYR35_PREM,
  [R("r1", "compute_value", "length", [("segment", "SC")], "Tính độ dài SC")],
  "answer_all", ["answer SC² = 50"], {"r1": LEN("50", "5√2")}, notes="Contrast with L10 (SC²).")
C("locked", "B", "S24", PYR35 + "Tính SC².", [SABCD, E("segment", "SC")], PYR35_PREM,
  [R("r1", "compute_value", "length_squared", [("segment", "SC")], "Tính SC²")],
  "answer_all", ["answer SC = 5√2"], {"r1": SQ("50", "2500")},
  notes="Contrast with L09: requested value is SC² = 50 (value_squared of that is 2500).")
PAR_TXT = "Cho hình chóp S.ABCD có đáy ABCD là hình bình hành với AB = 2, AD = √2, góc BAD = 135°; SA vuông góc với mặt phẳng đáy và SA = 1. "
PAR_PREM = [P("parallelogram_base", ["ABCD"], None, "đáy ABCD là hình bình hành"), P("length", ["AB"], "2", "AB = 2"),
            P("length", ["AD"], "√2", "AD = √2"), P("angle", ["BAD"], "135°", "góc BAD = 135°"),
            P(PERP_SA, ["SA", "(ABCD)"], None, "SA vuông góc với mặt phẳng đáy"), P("length", ["SA"], "1", "SA = 1")]
C("locked", "B", "S26", PAR_TXT + "Tính khoảng cách từ B đến đường thẳng SD.",
  [SABCD, E("point", "B"), E("line", "SD")], PAR_PREM,
  [R("r1", "compute_value", "distance_point_line", [("point", "B"), ("line", "SD")],
     "Tính khoảng cách từ B đến đường thẳng SD")],
  "answer_all", ["distance to segment (=BS=√5)", "foot is the midpoint of SD"],
  {"r1": LEN("14/3", "√42/3")},
  notes="Contrast with L12. Foot of perpendicular from B to line SD lies beyond S (parameter t = -1/3 from S toward D).")
C("locked", "B", "S27", PAR_TXT + "Tính khoảng cách từ B đến đoạn thẳng SD.",
  [SABCD, E("point", "B"), E("segment", "SD")], PAR_PREM,
  [R("r1", "compute_value", "distance_point_segment", [("point", "B"), ("segment", "SD")],
     "Tính khoảng cách từ B đến đoạn thẳng SD")],
  "answer_all", ["distance to the line SD (=√42/3)"],
  {"r1": LEN("5", "√5")}, notes="Contrast with L11: perpendicular foot is outside the segment; nearest point is S.")
BOX_T = "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 12. "
BOX_P = BOX_PREM("AB = 3", "AD = 4", "AA' = 12", "hình hộp chữ nhật ABCD.A'B'C'D'")
C("locked", "B", "S28", BOX_T + "Tính cos² của góc giữa đường chéo AC' và mặt phẳng (ABCD).",
  [E("solid", "ABCD.A'B'C'D'"), E("line", "AC'"), E("plane", "(ABCD)")], BOX_P,
  [R("r1", "compute_value", "cos_squared_angle", [("line", "AC'"), ("plane", "(ABCD)")],
     "Tính cos² của góc giữa đường chéo AC' và mặt phẳng (ABCD)", of="angle_line_plane")],
  "answer_all", ["give the angle", "give cos (=5/13)", "sin² (=144/169)"], {"r1": COS2("25/169")},
  notes="Contrast with L14.")
C("locked", "B", "S29", BOX_T + "Tính góc giữa đường chéo AC' và mặt phẳng (ABCD).",
  [E("solid", "ABCD.A'B'C'D'"), E("line", "AC'"), E("plane", "(ABCD)")], BOX_P,
  [R("r1", "compute_value", "angle_line_plane", [("line", "AC'"), ("plane", "(ABCD)")],
     "Tính góc giữa đường chéo AC' và mặt phẳng (ABCD)")],
  "answer_all", ["round to a 'nice' angle such as 60° or 67.5°"],
  {"r1": ANG("25/169", None, "arccos(5/13) ≈ 67.38°")},
  notes="Contrast with L13; non-standard angle (tan = 12/5).")
CUBE2 = "Cho hình lập phương ABCD.A'B'C'D' cạnh 2. "
CUBE2_P = [P("cube", ["ABCD.A'B'C'D'"], "2", "hình lập phương ABCD.A'B'C'D' cạnh 2")]
C("locked", "B", "S30", CUBE2 + "Tính khoảng cách từ điểm A' đến mặt phẳng (ABC'D').",
  [CUBE, E("point", "A'"), E("plane", "(ABC'D')")], CUBE2_P,
  [R("r1", "compute_value", "distance_point_plane", [("point", "A'"), ("plane", "(ABC'D')")],
     "Tính khoảng cách từ điểm A' đến mặt phẳng (ABC'D')")],
  "answer_all", ["treat four-label plane as invalid"], {"r1": LEN("2", "√2")},
  notes="Valid four-label plane (A, B, C', D' coplanar: a diagonal rectangle). Contrast with L16.")
C("locked", "B", "S31", CUBE2 + "Tính khoảng cách từ điểm A' đến mặt phẳng (ABC'D).",
  [CUBE, E("point", "A'"), E("plane", "(ABC'D) — not a plane", True)], CUBE2_P,
  [R("r1", "compute_value", "distance_point_plane", [("point", "A'"), ("plane", "(ABC'D)")],
     "Tính khoảng cách từ điểm A' đến mặt phẳng (ABC'D)")],
  "refuse_nonexistent_object", ["silently read it as (ABC'D') and answer √2", "read it as (ABCD) and answer 2"],
  missing=["A, B, C', D are not coplanar, so '(ABC'D)' names no plane"],
  notes="One-prime difference from L15. A clarification asking whether (ABC'D') was meant is also acceptable behaviour.")
C("locked", "B", "S32",
  "Cho hình chóp S.ABCD có đáy là hình chữ nhật ABCD và SA vuông góc với đáy. Tìm giao tuyến của hai mặt phẳng (SAB) và (SCD).",
  [SABCD, E("plane", "(SAB)"), E("plane", "(SCD)"), E("derived_line", "giao tuyến (SAB)∩(SCD)", False)],
  [P("rectangle_base", ["ABCD"], None, "đáy là hình chữ nhật ABCD"), P(PERP_SA, ["SA", "(ABCD)"], None, "SA vuông góc với đáy")],
  [R("r1", "construct", "intersection_line", [("plane", "(SAB)"), ("plane", "(SCD)")],
     "Tìm giao tuyến của hai mặt phẳng (SAB) và (SCD)")],
  "answer_all", ["answer a line through two named points such as SC or SD", "the planes are parallel"],
  expected_objects={"r1": "đường thẳng qua S song song với AB (và CD)"},
  notes="Intersection line of two planes is not a line through two labeled points; only S is shared.")

C("locked", "C", "S33",
  "Cho hình chóp S.ABCD có đáy là hình bình hành. Tìm giao tuyến của mặt phẳng (SAC) với mặt phẳng (SBD).",
  [SABCD, E("plane", "(SAC)"), E("plane", "(SBD)"), E("derived_point", "giao điểm của AC và BD (không có tên trong đề)", False)],
  [P("parallelogram_base", ["ABCD"], None, "đáy là hình bình hành")],
  [R("r1", "construct", "intersection_line", [("plane", "(SAC)"), ("plane", "(SBD)")],
     "Tìm giao tuyến của mặt phẳng (SAC) với mặt phẳng (SBD)")],
  "answer_all", ["use point O as if the text had named it", "SA ⊥ base"],
  expected_objects={"r1": "đường thẳng nối S với giao điểm của hai đường chéo AC và BD"},
  notes="Requires creating an unnamed point (diagonal intersection); naming it O in the answer is fine.")
C("locked", "C", "S34",
  "Tứ diện OABC có OA, OB, OC đôi một vuông góc và OA = OB = OC = 3. Tính khoảng cách từ O đến trọng tâm của tam giác ABC.",
  [OABC, E("point", "O"), E("derived_point", "trọng tâm của tam giác ABC", False)],
  [P("pairwise_perpendicular", ["OA", "OB", "OC"], None, "OA, OB, OC đôi một vuông góc"),
   P("length", ["OA", "OB", "OC"], "3", "OA = OB = OC = 3"),
   P("centroid_def", ["?", "ABC"], None, "trọng tâm của tam giác ABC")],
  [R("r1", "compute_value", "length", [("point", "O"), ("derived_point", "centroid(ABC)")],
     "Tính khoảng cách từ O đến trọng tâm của tam giác ABC")],
  "answer_all", ["distance from O to a vertex (=3)"], {"r1": LEN("3", "√3")},
  notes="Here the centroid coincides with the foot from O, so distance_point_plane gives the same number by coincidence.")
C("locked", "C", "S35",
  "Cho hình lập phương ABCD.A'B'C'D' cạnh a. Lấy trung điểm của cạnh CC' rồi đặt tên nó là M. Tính độ dài đoạn AM.",
  [CUBE, E("derived_point", "M", True), E("segment", "AM")],
  [P("cube", ["ABCD.A'B'C'D'"], "a", "hình lập phương ABCD.A'B'C'D' cạnh a"),
   P("midpoint_def", ["M", "CC'"], None, "Lấy trung điểm của cạnh CC' rồi đặt tên nó là M")],
  [R("r1", "compute_value", "length", [("segment", "AM")], "Tính độ dài đoạn AM")],
  "answer_all", ["M midpoint of C'D' or of CD"], {"r1": LEN("9/4", "3a/2", "a")},
  notes="Object described first, named afterwards.")
C("locked", "C", "S36",
  "Cho lăng trụ đứng ABC.A'B'C' có đáy là tam giác vuông cân tại A, AB = AC = 2, cạnh bên AA' = 4. Tính khoảng cách từ C đến tâm của mặt bên ABB'A'.",
  [PRISM, E("point", "C"), E("derived_point", "tâm của mặt bên ABB'A'", False)],
  [P("right_prism", ["ABC.A'B'C'"], None, "lăng trụ đứng ABC.A'B'C'"),
   P("right_isosceles", ["ABC", "A"], None, "tam giác vuông cân tại A"),
   P("length", ["AB", "AC"], "2", "AB = AC = 2"), P("length", ["AA'"], "4", "AA' = 4")],
  [R("r1", "compute_value", "length", [("point", "C"), ("derived_point", "center(ABB'A')")],
     "Tính khoảng cách từ C đến tâm của mặt bên ABB'A'")],
  "answer_all", ["distance from C to plane (ABB'A') (=2)"], {"r1": LEN("9", "3")},
  notes="'Tâm' of a rectangle face = intersection of its diagonals A'B and AB'.")
C("locked", "C", "S37",
  "Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), tam giác ABC vuông tại B, AB = BC = 2, SA = 2. Tính độ dài đoạn nối A với chân đường vuông góc hạ từ A xuống mặt phẳng (SBC).",
  [SABC, E("point", "A"), E("derived_point", "chân đường vuông góc hạ từ A xuống (SBC)", False)],
  [P(PERP_SA, ["SA", "(ABC)"], None, "SA vuông góc với mặt phẳng (ABC)"),
   P("right_angle", ["ABC", "B"], None, "tam giác ABC vuông tại B"), P("length", ["AB", "BC"], "2", "AB = BC = 2"),
   P("length", ["SA"], "2", "SA = 2"),
   P("projection_def", ["?", "A", "(SBC)"], None, "chân đường vuông góc hạ từ A xuống mặt phẳng (SBC)")],
  [R("r1", "compute_value", "length", [("point", "A"), ("derived_point", "foot(A,(SBC))")],
     "Tính độ dài đoạn nối A với chân đường vuông góc hạ từ A xuống mặt phẳng (SBC)",
     accept_equivalent_quantities=["distance_point_plane"])],
  "answer_all", ["foot lies on SC", "foot is B"], {"r1": LEN("2", "√2")},
  notes="Unnamed foot; it lies on SB (midpoint here).")

C("locked", "D", "S38",
  "Tứ diện OABC có ba cạnh OA, OB, OC đôi một vuông góc; OA = 1, OB = OC = 2. Tính thể tích tứ diện, diện tích tam giác ABC, rồi suy ra khoảng cách từ O đến (ABC).",
  [OABC, E("plane", "(ABC)"), E("point", "O")],
  [P("pairwise_perpendicular", ["OA", "OB", "OC"], None, "OA, OB, OC đôi một vuông góc"),
   P("length", ["OA"], "1", "OA = 1"), P("length", ["OB", "OC"], "2", "OB = OC = 2")],
  [R("r1", "compute_value", "volume", [("solid", "OABC")], "Tính thể tích tứ diện"),
   R("r2", "compute_value", "area", [("triangle", "ABC")], "diện tích tam giác ABC"),
   R("r3", "compute_value", "distance_point_plane", [("point", "O"), ("plane", "(ABC)")],
     "suy ra khoảng cách từ O đến (ABC)", depends_on=["r1", "r2"])],
  "answer_all", ["area of OBC (=2)"],
  {"r1": VOL("2/3", "4/9", "2/3"), "r2": AREA("6", "√6"), "r3": LEN("2/3", "√6/3")},
  notes="Chained: r3 'suy ra' from r1, r2.")
C("locked", "D", "S39",
  "Cho lăng trụ đứng ABC.A'B'C', đáy ABC là tam giác vuông tại A có AB = 1 và AC = 2, chiều cao AA' = 2. a) Tính thể tích khối lăng trụ. b) Tính góc giữa hai mặt phẳng (A'BC) và (ABC).",
  [PRISM, E("plane", "(A'BC)"), E("plane", "(ABC)")],
  [P("right_prism", ["ABC.A'B'C'"], None, "lăng trụ đứng ABC.A'B'C'"),
   P("right_angle", ["ABC", "A"], None, "tam giác vuông tại A"), P("length", ["AB"], "1", "AB = 1"),
   P("length", ["AC"], "2", "AC = 2"), P("length", ["AA'"], "2", "AA' = 2")],
  [R("r1", "compute_value", "volume", [("solid", "ABC.A'B'C'")], "Tính thể tích khối lăng trụ"),
   R("r2", "compute_value", "angle_plane_plane", [("plane", "(A'BC)"), ("plane", "(ABC)")],
     "Tính góc giữa hai mặt phẳng (A'BC) và (ABC)")],
  "answer_all", ["pyramid volume formula (1/3)", "angle A'BA"],
  {"r1": VOL("2", "4", "2"), "r2": ANG("1/6", None, "arctan(√5) ≈ 65.91°")},
  notes="Enumerated sub-questions a), b).")
C("locked", "D", "S40",
  "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 3, AD = 4, SA ⊥ (ABCD), SA = 5. Hãy dựng hình chiếu vuông góc của A trên mặt phẳng (SBC), gọi là H, rồi tính độ dài AH.",
  [SABCD, E("derived_point", "H", True), E("plane", "(SBC)"), E("segment", "AH")],
  [P("rectangle_base", ["ABCD"], None, "đáy ABCD là hình chữ nhật"), P("length", ["AB"], "3", "AB = 3"),
   P("length", ["AD"], "4", "AD = 4"), P(PERP_SA, ["SA", "(ABCD)"], None, "SA ⊥ (ABCD)"), P("length", ["SA"], "5", "SA = 5"),
   P("projection_def", ["H", "A", "(SBC)"], None, "hình chiếu vuông góc của A trên mặt phẳng (SBC), gọi là H")],
  [R("r1", "construct", "projection", [("point", "A"), ("plane", "(SBC)")],
     "dựng hình chiếu vuông góc của A trên mặt phẳng (SBC)"),
   R("r2", "compute_value", "length", [("segment", "AH")], "tính độ dài AH", depends_on=["r1"])],
  "answer_all", ["H on SC", "H = B"], {"r2": LEN("225/34", "15√34/34")},
  expected_objects={"r1": "H thuộc SB, AH ⊥ SB (vì BC ⊥ (SAB))"},
  notes="Construct then compute on the constructed object.")
C("locked", "D", "S41",
  "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a, SA ⊥ đáy và SA = a. Tính thể tích khối chóp và góc giữa SB với mặt phẳng đáy.",
  [SABCD, E("line", "SB"), E("plane", "(ABCD)")],
  [P("square_base", ["ABCD"], "a", "đáy là hình vuông cạnh a"), P(PERP_SA, ["SA", "(ABCD)"], None, "SA ⊥ đáy"),
   P("length", ["SA"], "a", "SA = a")],
  [R("r1", "compute_value", "volume", [("solid", "S.ABCD")], "Tính thể tích khối chóp"),
   R("r2", "compute_value", "angle_line_plane", [("line", "SB"), ("plane", "(ABCD)")],
     "góc giữa SB với mặt phẳng đáy")],
  "answer_all", ["V = a³ (forgetting 1/3)"],
  {"r1": VOL("1/3", "1/9", "a³/3", "a^3"), "r2": ANG("1/2", "45", "45°")},
  notes="Two requests in one sentence sharing the verb 'Tính'.")
C("locked", "D", "S42",
  "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 1, AD = 2, AA' = 2. Tính BD', tính thể tích khối hộp, và tính khoảng cách giữa hai đường thẳng AA' và BD'.",
  [E("solid", "ABCD.A'B'C'D'"), E("segment", "BD'"), E("line", "AA'"), E("line", "BD'")],
  [P("rectangular_box", ["ABCD.A'B'C'D'"], None, "hình hộp chữ nhật ABCD.A'B'C'D'"),
   P("length", ["AB"], "1", "AB = 1"), P("length", ["AD"], "2", "AD = 2"), P("length", ["AA'"], "2", "AA' = 2")],
  [R("r1", "compute_value", "length", [("segment", "BD'")], "Tính BD'"),
   R("r2", "compute_value", "volume", [("solid", "ABCD.A'B'C'D'")], "tính thể tích khối hộp"),
   R("r3", "compute_value", "distance_line_line", [("line", "AA'"), ("line", "BD'")],
     "tính khoảng cách giữa hai đường thẳng AA' và BD'")],
  "answer_all", ["AA' and BD' intersect", "distance = AB (=1)"],
  {"r1": LEN("9", "3"), "r2": VOL("4", "16", "4"), "r3": LEN("4/5", "2√5/5")},
  notes="Three independent requests.")
C("locked", "D", "S43",
  "Cho hình chóp S.ABC có SA vuông góc với đáy, đáy ABC là tam giác vuông cân tại A với AB = AC = 2, SA = 2. Gọi M là trung điểm BC. Tính độ dài SM, sau đó dựa vào SM tính diện tích tam giác SBC.",
  [SABC, E("derived_point", "M", True), E("segment", "SM"), E("triangle", "SBC")],
  [P(PERP_SA, ["SA", "(ABC)"], None, "SA vuông góc với đáy"), P("right_isosceles", ["ABC", "A"], None, "tam giác vuông cân tại A"),
   P("length", ["AB", "AC"], "2", "AB = AC = 2"), P("length", ["SA"], "2", "SA = 2"),
   P("midpoint_def", ["M", "BC"], None, "Gọi M là trung điểm BC")],
  [R("r1", "compute_value", "length", [("segment", "SM")], "Tính độ dài SM"),
   R("r2", "compute_value", "area", [("triangle", "SBC")], "dựa vào SM tính diện tích tam giác SBC", depends_on=["r1"])],
  "answer_all", ["area of ABC (=2)"], {"r1": LEN("6", "√6"), "r2": AREA("12", "2√3")},
  notes="r2 explicitly uses r1 (SM is the altitude of isosceles SBC).")
C("locked", "D", "S44",
  "Cho hình lập phương ABCD.A'B'C'D' cạnh a. Tính khoảng cách giữa hai đường thẳng BD và B'C. Ngoài ra, hai đường thẳng này hợp với nhau một góc bao nhiêu?",
  [CUBE, E("line", "BD"), E("line", "B'C")],
  [P("cube", ["ABCD.A'B'C'D'"], "a", "hình lập phương ABCD.A'B'C'D' cạnh a")],
  [R("r1", "compute_value", "distance_line_line", [("line", "BD"), ("line", "B'C")],
     "Tính khoảng cách giữa hai đường thẳng BD và B'C"),
   R("r2", "compute_value", "angle_line_line", [("line", "BD"), ("line", "B'C")],
     "hai đường thẳng này hợp với nhau một góc bao nhiêu")],
  "answer_all", ["BD ⊥ B'C (90°)", "distance = a"],
  {"r1": LEN("1/3", "a√3/3", "a"), "r2": ANG("1/4", "60", "60°")},
  notes="Second request in a separate sentence with anaphora 'hai đường thẳng này'.")
C("locked", "D", "S45",
  "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với đáy, SA = 3. Tính SC rồi tính cos² góc giữa SC và đáy, sau đó tính thể tích khối chóp.",
  [SABCD, E("segment", "SC"), E("plane", "(ABCD)")],
  [P("square_base", ["ABCD"], "4", "đáy ABCD là hình vuông cạnh 4"), P(PERP_SA, ["SA", "(ABCD)"], None, "SA vuông góc với đáy"),
   P("length", ["SA"], "3", "SA = 3")],
  [R("r1", "compute_value", "length", [("segment", "SC")], "Tính SC"),
   R("r2", "compute_value", "cos_squared_angle", [("line", "SC"), ("plane", "(ABCD)")],
     "tính cos² góc giữa SC và đáy", of="angle_line_plane"),
   R("r3", "compute_value", "volume", [("solid", "S.ABCD")], "tính thể tích khối chóp")],
  "answer_all", ["SC = 5 (using side instead of diagonal)"],
  {"r1": LEN("41", "√41"), "r2": COS2("32/41"), "r3": VOL("16", "256", "16")},
  notes="'rồi' / 'sau đó' chain, but requests are computationally independent.")

C("locked", "E", "S46", "Khoảng cách từ giao điểm ấy tới mặt đáy ABCD bằng bao nhiêu?",
  [E("derived_point", "giao điểm của AC' và BD' (from context)", False), E("plane", "(ABCD)")],
  [P("cube", ["ABCD.A'B'C'D'"], "2", "Hình lập phương ABCD.A'B'C'D' cạnh 2", "context.prior_turn")],
  [R("r1", "compute_value", "distance_point_plane", [("derived_point", "AC'∩BD'"), ("plane", "(ABCD)")],
     "Khoảng cách từ giao điểm ấy tới mặt đáy ABCD bằng bao nhiêu")],
  "answer_all", ["intersection point is a vertex"], {"r1": LEN("1", "1")},
  context={"prior_turn": "Hình lập phương ABCD.A'B'C'D' cạnh 2. Nối A với C' và nối B với D'.",
           "prior_result": "Đã vẽ hai đường chéo AC' và BD'; hai đường này cắt nhau tại một điểm."},
  notes="'giao điểm ấy' resolves to the (unnamed) cube center.")
C("locked", "E", "S47", "Đổi màu đường thẳng vừa dựng sang đỏ và ẩn mặt đáy đi cho dễ nhìn.",
  [E("derived_line", "d (from context)", False), E("plane", "(ABCD)")],
  [P("square_base", ["ABCD"], None, "đáy là hình vuông", "context.prior_turn"),
   P(PERP_SA, ["SA", "(ABCD)"], None, "SA ⊥ (ABCD)", "context.prior_turn")],
  [R("r1", "interaction", "other", [("derived_line", "d")], "Đổi màu đường thẳng vừa dựng sang đỏ"),
   R("r2", "interaction", "other", [("plane", "(ABCD)")], "ẩn mặt đáy đi")],
  "answer_all", ["recompute or re-construct the intersection line"],
  context={"prior_turn": "Cho hình chóp S.ABCD có đáy là hình vuông, SA ⊥ (ABCD). Dựng giao tuyến của (SAB) và (SCD).",
           "prior_result": "Đã dựng đường thẳng d đi qua S và song song với AB."},
  notes="Two pure display requests; no geometry computation expected.")
C("locked", "E", "S48", "Tính tiếp độ dài của đoạn mình vừa dựng ở trên nhé.",
  [E("segment", "'đoạn mình vừa dựng' (unresolved)", False)], [],
  [R("r1", "compute_value", "length", [("segment", "<unresolved>")], "Tính tiếp độ dài của đoạn mình vừa dựng")],
  "clarification_required", ["invent a figure and a segment"],
  missing=["No prior turn: the segment and the figure are unknown"])
C("locked", "E", "S49", "Làm nổi bật điểm đó giúp mình.",
  [E("point", "'điểm đó' (H or K)", False)],
  [P(PERP_SA, ["SA", "(ABC)"], None, "SA ⊥ (ABC)", "context.prior_turn"),
   P("right_angle", ["ABC", "B"], None, "tam giác ABC vuông tại B", "context.prior_turn"),
   P("projection_def", ["H", "A", "SB"], None, "Gọi H, K lần lượt là hình chiếu của A lên SB và SC", "context.prior_turn")],
  [R("r1", "interaction", "other", [("point", "<ambiguous: H or K>")], "Làm nổi bật điểm đó")],
  "clarification_required", ["pick H (first mentioned)", "pick K (last mentioned)"],
  missing=["Prior turn introduced two points H and K; 'điểm đó' does not select one"],
  context={"prior_turn": "Hình chóp S.ABC có SA ⊥ (ABC), tam giác ABC vuông tại B. Gọi H, K lần lượt là hình chiếu của A lên SB và SC.",
           "prior_result": "Đã dựng H trên SB và K trên SC."},
  notes="Context exists but the reference is ambiguous between two candidates.")
C("locked", "E", "S50", "Quay hình sao cho nhìn thẳng từ trên xuống mặt (OAB) nhé.",
  [E("plane", "(OAB)")],
  [P("pairwise_perpendicular", ["OA", "OB", "OC"], None, "OA, OB, OC đôi một vuông góc", "context.prior_turn")],
  [R("r1", "interaction", "other", [("plane", "(OAB)")], "Quay hình sao cho nhìn thẳng từ trên xuống mặt (OAB)")],
  "answer_all", ["compute something about (OAB)"],
  context={"prior_turn": "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc, OA = OB = OC = 3. Vẽ tứ diện này.",
           "prior_result": "Đã vẽ tứ diện OABC."},
  notes="'hình' resolves to the drawn tetrahedron; pure camera request.")
C("locked", "E", "S51", "Ẩn tên các điểm khác, chỉ giữ lại tên điểm vừa dựng; sau đó tính SM.",
  [E("derived_point", "M (from context)", True), E("segment", "SM")],
  [P(PERP_SA, ["SA", "(ABC)"], None, "SA ⊥ (ABC)", "context.prior_turn"), P("length", ["SA"], "3", "SA = 3", "context.prior_turn"),
   P("right_angle", ["ABC", "A"], None, "đáy ABC vuông tại A", "context.prior_turn"),
   P("length", ["AB"], "3", "AB = 3", "context.prior_turn"), P("length", ["AC"], "4", "AC = 4", "context.prior_turn"),
   P("midpoint_def", ["M", "BC"], None, "trung điểm M của cạnh BC", "context.prior_turn")],
  [R("r1", "interaction", "other", [("derived_point", "M")], "Ẩn tên các điểm khác, chỉ giữ lại tên điểm vừa dựng"),
   R("r2", "compute_value", "length", [("segment", "SM")], "tính SM")],
  "answer_all", ["SM = SA (=3)", "M is midpoint of AB"], {"r2": LEN("61/4", "√61/2")},
  context={"prior_turn": "Cho hình chóp S.ABC có SA ⊥ (ABC), SA = 3, đáy ABC vuông tại A với AB = 3, AC = 4. Dựng trung điểm M của cạnh BC.",
           "prior_result": "Đã dựng điểm M là trung điểm của BC."},
  notes="Interaction + computation in one follow-up.")

C("locked", "F", "S52",
  "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 2, AD = 5, SA = 4 nhưng SA không vuông góc với mặt đáy. Tính thể tích khối chóp S.ABCD.",
  [SABCD],
  [P("rectangle_base", ["ABCD"], None, "đáy ABCD là hình chữ nhật"), P("length", ["AB"], "2", "AB = 2"),
   P("length", ["AD"], "5", "AD = 5"), P("length", ["SA"], "4", "SA = 4"),
   P("negated:perpendicular_line_plane", ["SA", "(ABCD)"], None, "SA không vuông góc với mặt đáy")],
  [R("r1", "compute_value", "volume", [("solid", "S.ABCD")], "Tính thể tích khối chóp S.ABCD")],
  "refuse_missing_info", ["SA ⊥ base (V = 40/3)"],
  missing=["Height unknown: SA is explicitly not perpendicular, no angle or other data"],
  notes="Negated premise; the habitual reading 'SA ⊥ đáy' gives 40/3.")
C("locked", "F", "S53",
  "Cho hình lập phương ABCD.A'B'C'D'. Nếu cạnh của hình lập phương bằng 3 thì đường chéo AC' bằng bao nhiêu?",
  [CUBE, E("segment", "AC'")],
  [P("cube", ["ABCD.A'B'C'D'"], None, "hình lập phương ABCD.A'B'C'D'"),
   P("conditional:edge_length", ["ABCD.A'B'C'D'"], "3", "Nếu cạnh của hình lập phương bằng 3")],
  [R("r1", "compute_value", "length", [("segment", "AC'")], "đường chéo AC' bằng bao nhiêu")],
  "answer_all", ["answer symbolically (a√3) ignoring the condition", "refuse for missing edge"],
  {"r1": LEN("27", "3√3")},
  notes="Conditional clause supplies the dimension; it is answerable, not missing.")
C("locked", "F", "S54",
  "Cho hình hộp chữ nhật ABCD.A'B'C'D'. Tìm giao tuyến của mặt phẳng (ABCD) và mặt phẳng (A'B'C'D').",
  [E("solid", "ABCD.A'B'C'D'"), E("plane", "(ABCD)"), E("plane", "(A'B'C'D')")],
  [P("rectangular_box", ["ABCD.A'B'C'D'"], None, "hình hộp chữ nhật ABCD.A'B'C'D'")],
  [R("r1", "construct", "intersection_line", [("plane", "(ABCD)"), ("plane", "(A'B'C'D')")],
     "Tìm giao tuyến của mặt phẳng (ABCD) và mặt phẳng (A'B'C'D')")],
  "refuse_nonexistent_object", ["answer some line such as AA' or AB"],
  missing=["(ABCD) ∥ (A'B'C'D'): distinct parallel planes have no intersection line"])
C("locked", "F", "S55",
  "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2, SA = SB = 3. Tính thể tích khối chóp S.ABC.",
  [SABC],
  [P("equilateral_base", ["ABC"], "2", "đáy ABC là tam giác đều cạnh 2"), P("length", ["SA", "SB"], "3", "SA = SB = 3")],
  [R("r1", "compute_value", "volume", [("solid", "S.ABC")], "Tính thể tích khối chóp S.ABC")],
  "refuse_missing_info", ["regular pyramid / SC = 3 (V = √69/3)", "SA ⊥ base"],
  missing=["SC (or height) not given; S can rotate about AB keeping SA = SB = 3"],
  notes="Text tempts 'hình chóp đều' but never states it.")
C("locked", "F", "S56",
  "Cho hình chóp S.ABC có SA vuông góc với đáy, tam giác ABC vuông cân tại A, AB = AC = 2 và SA = 2. Gọi M là trung điểm của BC. Chứng minh BC vuông góc với mặt phẳng (SAM) và tính khoảng cách từ A đến mặt phẳng (SBC).",
  [SABC, E("derived_point", "M", True), E("plane", "(SAM)"), E("plane", "(SBC)")],
  [P(PERP_SA, ["SA", "(ABC)"], None, "SA vuông góc với đáy"), P("right_isosceles", ["ABC", "A"], None, "tam giác ABC vuông cân tại A"),
   P("length", ["AB", "AC"], "2", "AB = AC = 2"), P("length", ["SA"], "2", "SA = 2"),
   P("midpoint_def", ["M", "BC"], None, "Gọi M là trung điểm của BC")],
  [R("r1", "prove", "other", [("line", "BC"), ("plane", "(SAM)")], "Chứng minh BC vuông góc với mặt phẳng (SAM)"),
   R("r2", "compute_value", "distance_point_plane", [("point", "A"), ("plane", "(SBC)")],
     "tính khoảng cách từ A đến mặt phẳng (SBC)")],
  "answer_supported_part_and_flag_rest", ["treat the proof as already done / skip it silently"],
  {"r2": LEN("4/3", "2√3/3")},
  notes="Proof request is outside ordinary computation; compute r2 and flag r1 (a visual check of BC ⊥ (SAM) is not a proof).")
C("locked", "F", "S57",
  "Cho hình lập phương ABCD.A'B'C'D' cạnh 1, M là điểm di động trên cạnh CD. Tìm giá trị lớn nhất của diện tích tam giác A'BM.",
  [CUBE, E("point", "M (moving)", True), E("triangle", "A'BM")],
  [P("cube", ["ABCD.A'B'C'D'"], "1", "hình lập phương ABCD.A'B'C'D' cạnh 1"),
   P("moving_point_on_segment", ["M", "CD"], None, "M là điểm di động trên cạnh CD")],
  [R("r1", "compute_value", "other", [("triangle", "A'BM")], "Tìm giá trị lớn nhất của diện tích tam giác A'BM",
     of="max_area_over_moving_point")],
  "out_of_scope_request", ["fix M at a vertex or midpoint and report one area as the maximum"],
  notes="Optimization over a moving point; not a single static construction.")
C("locked", "F", "S58",
  "Cho hình chóp S.ABCD có đáy là hình chữ nhật, AB = 2, AD = 3, SA ⊥ (ABCD), SA = 4. Gọi M là trung điểm của SB và M là trung điểm của SD. Tính độ dài đoạn AM.",
  [SABCD, E("point", "M (doubly defined)", True)],
  [P("rectangle_base", ["ABCD"], None, "đáy là hình chữ nhật"), P("length", ["AB"], "2", "AB = 2"),
   P("length", ["AD"], "3", "AD = 3"), P(PERP_SA, ["SA", "(ABCD)"], None, "SA ⊥ (ABCD)"), P("length", ["SA"], "4", "SA = 4"),
   P("midpoint_def", ["M", "SB"], None, "Gọi M là trung điểm của SB"),
   P("midpoint_def", ["M", "SD"], None, "M là trung điểm của SD")],
  [R("r1", "compute_value", "length", [("segment", "AM")], "Tính độ dài đoạn AM")],
  "refuse_ambiguous", ["use the first definition (AM = √5)", "use the last definition (AM = 5/2)"],
  missing=["Label M bound to two different points (midpoints of SB and SD differ)"])
C("locked", "F", "S59",
  "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2 và đường chéo AC' = 4. Tính thể tích khối lập phương.",
  [CUBE],
  [P("cube", ["ABCD.A'B'C'D'"], "2", "hình lập phương ABCD.A'B'C'D' có cạnh bằng 2"),
   P("length", ["AC'"], "4", "AC' = 4")],
  [R("r1", "compute_value", "volume", [("solid", "ABCD.A'B'C'D'")], "Tính thể tích khối lập phương")],
  "refuse_contradictory", ["answer 8 ignoring AC'", "answer 64/(3√3) from AC'"],
  missing=["Edge 2 forces AC' = 2√3 ≠ 4"])

# ids
cnt = {"dev": 0, "locked": 0}
for c in cases:
    cnt[c["split"]] += 1
    c["id"] = ("D" if c["split"] == "dev" else "L") + f"{cnt[c['split']]:02d}"
ordered = [{"id": c.pop("id"), **c} for c in cases]
out = {"schema": "NLU_EVAL_CORPUS/1",
       "author": "independent-agent-1 (Claude subagent, blind to system under test)",
       "created": "2026-10-17", "cases": ordered}
with open(os.path.join(HERE, "corpus.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("wrote", len(ordered), "cases", cnt)
