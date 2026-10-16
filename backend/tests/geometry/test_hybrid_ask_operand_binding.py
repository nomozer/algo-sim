"""S1 (run `hybrid-semantic-hardening`): an `ask_*` is answered only when the asked OBJECT PHRASE of the quote names
exactly the call's operands — Source Clause → Requested Operation → Target Objects → Geometry Function.

Closes groups C and D of `ISSUE-ARCH-HYBRID-GATE-RESIDUAL-FALSE-SERVES` (independent review of `hybrid-slice-review`): the
gate checked that the quantity noun was asked, not WHICH objects the question names, nor modifiers that change the
quantity. Same gate for route A and route B. Offline typed facts; no model.

Expected values are hand-derived for the square pyramid of the benchmark (A=(0,0,0), side 2, SA=3 ⊥ base), compared
squared (`HB.answer_square`).
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.ai.function_route import run_fact_route, run_function_route
from tests.geometry import hybrid_compiler_benchmark as HB

f, ask = HB._f, HB._ask
MID = HB._mid("f5", "M", "S", "C")


def DPP(s, p="S", pl="ABCD"):
    return ask("q", s, "distance", points_a=[p], points_b=list(pl))


def VOL(s):
    return ask("q", s, "volume", solid="S.ABCD")


def LEN(s, seg="SC"):
    return ask("q", s, "length", points=list(seg))


def ANG(s):
    return ask("q", s, "angle", points_a=["S", "C"], points_b=list("ABCD"))


def DLL(s):
    return ask("q", s, "distance", points_a=["S", "C"], points_b=["B", "D"])


def AREA(s, pl):
    return ask("q", s, "area", points=list(pl))


def SAREA(s, pl="MAB"):
    return ask("q", s, "area", solid="S.ABCD", points=list(pl))


def _run(sentence, qf, mid=False, extra=()):
    q, fs = HB._square()
    if mid:
        q, fs = q + [MID["quotes"][0]], fs + [MID]
    return run_fact_route(" ".join(q) + " " + sentence, {"facts": fs + [qf(sentence), *extra]})


def _run_complete_requests(sentence, qf, mid):
    # These historical wording controls supplied only one request of a list. Keep the numeric oracle,
    # check the omission fails closed, then supply all requests for the positive control (M1).
    requests = {
        "Tính thể tích khối chóp S.ABCD và khoảng cách từ S đến (ABCD).": [VOL, DPP],
        "Tính độ dài các cạnh SB, SC.": [lambda s: LEN(s, "SB"), LEN],
        "Tính độ dài các cạnh bên SB, SC, SD.": [lambda s: LEN(s, "SB"), LEN, lambda s: LEN(s, "SD")],
        "Tính khoảng cách từ S đến (ABCD), từ đó suy ra thể tích khối chóp.": [DPP, VOL],
        "Tính khoảng cách từ S đến (ABCD), từ đó tính thể tích khối chóp.": [DPP, VOL],
    }
    primary = qf(sentence)
    extra = [dict(f(sentence), id=f"q_extra_{i}") for i, f in enumerate(requests.get(sentence, ()))
             if f(sentence) != primary]
    if extra:
        partial = _run(sentence, qf, mid)
        assert (partial.status, partial.code) == ("REFUSED", "REQUEST_NOT_ANSWERED"), partial.answers
    return _run(sentence, qf, mid, extra)


# ── must refuse: the asked phrase names other objects, or a modifier changes the quantity (groups C and D) ──────────
FALSE_SERVES = [
    # C — operands not those the question names
    ("Tính khoảng cách từ A đến (SBC).", DPP, False),
    ("Tính khoảng cách từ M đến (ABCD).", DPP, True),
    ("Tính khoảng cách từ trung điểm của SC đến (ABCD).", DPP, False),
    ("Tính thể tích khối chóp M.ABCD.", VOL, True),
    ("Tính thể tích khối chóp S.ABC.", VOL, False),
    ("Tính độ dài SM.", LEN, True),
    # C — a modifier changes the quantity, or the question is about another expression / a changed figure
    ("Tính độ dài hình chiếu của SC lên (ABCD).", LEN, False),
    ("Tính bình phương khoảng cách từ S đến (ABCD).", DPP, False),
    ("Tính nửa thể tích khối chóp S.ABCD.", VOL, False),
    ("Tính hai lần thể tích khối chóp S.ABCD.", VOL, False),
    ("Tính thể tích phần còn lại của khối chóp S.ABCD sau khi cắt bởi (MAB).", VOL, True),
    ("Tính SC + khoảng cách từ S đến (ABCD).", DPP, False),
    ("Tính khoảng cách từ S đến (ABCD) khi M thay đổi.", DPP, True),
    ("Tính khoảng cách từ S đến (ABCD) sau khi tăng SA lên gấp đôi.", DPP, False),
    ("Tính SC. Biết khoảng cách từ S đến (ABCD)?", DPP, False),
    ("Tính sin góc giữa SC và (ABCD).", ANG, False),
    # D — sections: the asked section is another one, or another quantity of it
    ("Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (MAB), biết diện tích thiết diện cắt bởi (SAC) bằng 3√2.",
     lambda s: SAREA(s, "SAC"), True),
    ("Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (SAC) rồi so sánh với thiết diện cắt bởi (MAB).",
     SAREA, True),
    ("Tính diện tích hình chiếu của thiết diện của hình chóp S.ABCD cắt bởi (MAB) lên đáy.", SAREA, True),
    ("Tính diện tích thiết diện lớn nhất của hình chóp S.ABCD cắt bởi (MAB) khi M chạy trên SC.", SAREA, True),
    ("Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (MAB) khi SA tăng gấp đôi.", SAREA, True),
    ("Tính diện tích thiết diện của hình chóp S.ABCD với mặt phẳng (MAB) song song với CD.", SAREA, True),
    ("Tính diện tích thiết diện của khối lập phương cắt bởi (MAB).", SAREA, True),
]


@pytest.mark.parametrize("sentence,qf,mid", FALSE_SERVES, ids=[s for s, _q, _m in FALSE_SERVES])
def test_ask_for_other_objects_or_another_quantity_is_refused(sentence, qf, mid):
    r = _run(sentence, qf, mid)
    assert r.status == "REFUSED", (r.answers, sentence)


# ── must stay served: common ways of asking, alone, in lists, with givens around them ───────────────────────────────
ASKED = [
    ("Tính khoảng cách từ S đến (ABCD).", DPP, False, F(9)),
    ("Tính khoảng cách từ S đến mặt phẳng (ABCD).", DPP, False, F(9)),
    ("Tính khoảng cách từ điểm S tới mp(ABCD).", DPP, False, F(9)),
    ("Tính khoảng cách từ S đến mặt đáy.", DPP, False, F(9)),
    ("Khoảng cách từ S đến (ABCD) bằng bao nhiêu?", DPP, False, F(9)),
    ("Hỏi khoảng cách từ S đến (ABCD) bằng bao nhiêu?", DPP, False, F(9)),
    ("Tính thể tích khối chóp S.ABCD và khoảng cách từ S đến (ABCD).", DPP, False, F(9)),
    ("Tính thể tích khối chóp S.ABCD và khoảng cách từ S đến (ABCD).", VOL, False, F(16)),
    ("Tính thể tích khối chóp S.ABCD.", VOL, False, F(16)),
    ("Tính thể tích của khối chóp S.ABCD.", VOL, False, F(16)),
    ("Tính thể tích khối chóp.", VOL, False, F(16)),
    ("Thể tích khối chóp S.ABCD bằng bao nhiêu?", VOL, False, F(16)),
    ("Tính độ dài SC.", LEN, False, F(17)),
    ("Tính SC.", LEN, False, F(17)),
    ("Tính độ dài đoạn thẳng SC.", LEN, False, F(17)),
    ("Tính độ dài cạnh SC.", LEN, False, F(17)),
    ("Độ dài SC bằng bao nhiêu?", LEN, False, F(17)),
    ("Tính SC rồi so sánh với SB.", LEN, False, F(17)),
    # the angle answer is cos² ("cos²=8/17"); `answer_square` reads that value as is
    ("Tính góc giữa SC và (ABCD).", ANG, False, F(8, 17)),
    ("Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).", ANG, False, F(8, 17)),
    ("Tính khoảng cách giữa hai đường thẳng SC và BD.", DLL, False, F(18, 17)),
    ("Tính khoảng cách giữa SC và BD.", DLL, False, F(18, 17)),
    ("Tính diện tích tam giác SAC.", lambda s: AREA(s, "SAC"), False, F(18)),
    ("Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB).", SAREA, True, F(117, 16)),
    ("Tính diện tích thiết diện với mặt phẳng (MAB) của hình chóp S.ABCD.", SAREA, True, F(117, 16)),
]


@pytest.mark.parametrize("sentence,qf,mid,sq", ASKED, ids=[f"{s}|{i}" for i, (s, *_r) in enumerate(ASKED)])
def test_common_asks_stay_served(sentence, qf, mid, sq):
    r = _run_complete_requests(sentence, qf, mid)
    assert r.status == "SERVED", (r.code, r.reason, sentence)
    assert HB.answer_square(r.answers["q"]) == sq, r.answers


def test_angle_measure_so_do_goc_is_refused_by_output_contract_policy():
    # Policy override (run `shared-ask-grammar-safety`, §5 IM-A): the engine returns `cos²=...` for angle asks,
    # which is not the angle measure ("số đo góc"), so "Tính số đo góc ..." fails closed (`QUESTION_CONTEXT_UNSUPPORTED`).
    r = _run("Tính số đo góc giữa SC và mặt đáy.", ANG, False)
    assert r.status == "REFUSED" and r.code == "QUESTION_CONTEXT_UNSUPPORTED", (r.status, r.code, r.answers)


# ── group B: a length value is a given only when the source states an EQUALITY (shared value authority) ───────────────
def _len_run(sentence, quote, v):
    q, fs = HB._square()
    q, fs = q[:3], fs[:3]                                                     # SA ⊥ (ABCD) but no SA length
    sc = LEN("Tính độ dài SC.")
    return run_fact_route(" ".join(q) + " " + sentence + " Tính độ dài SC.",
                          {"facts": fs + [f("f9", "length", quote, points=["S", "A"], measure="segment", value=v), sc]})


NOT_AN_EQUALITY = [("SA ≥ 3.", "SA ≥ 3.", "3"), ("SA > 3.", "SA > 3.", "3"), ("SA ≈ 3.", "SA ≈ 3.", "3"),
                   ("SA không bằng 4.", "SA không bằng 4.", "4"), ("SA ≠ 4.", "SA ≠ 4.", "4"),
                   ("SA bằng 3 lần AB.", "SA bằng 3 lần AB.", "3"), ("SA lớn hơn 3.", "SA lớn hơn 3.", "3"),
                   ("SA = 3 hoặc SA = 4.", "SA = 3", "3"), ("SA xấp xỉ 3.", "SA xấp xỉ 3.", "3"),
                   ("SA tối đa bằng 3.", "SA tối đa bằng 3.", "3"), ("SA = 3 là sai.", "SA = 3", "3"),
                   ("Độ dài SA bằng 3 khi M trùng S.", "Độ dài SA bằng 3", "3")]
EQUALITY = [("SA = 3.", "SA = 3."), ("SA bằng 3.", "SA bằng 3."), ("Độ dài SA bằng 3.", "Độ dài SA bằng 3."),
            ("SA có độ dài 3 cm.", "SA có độ dài 3 cm."),
            ("Cạnh SA dài 3.", "Cạnh SA dài 3."), ("SA = SB = 3.", "SA = SB = 3.")]
# run source-grounding-completeness: a second clause no call read ("… và SA vuông góc với AB", "… và khối chóp có thể tích
# bằng 4") is an unread premise — refused as a whole, even when it happens to be true on the figure.
UNREAD_SECOND_CLAUSE = [("len", "SA = 3 và SA vuông góc với AB.", "SA = 3"),
                        ("perp", "Cạnh bên SA vuông góc với (ABCD) và khối chóp có thể tích bằng 4.", None)]


@pytest.mark.parametrize("sentence,quote,v", NOT_AN_EQUALITY, ids=[s for s, *_r in NOT_AN_EQUALITY])
def test_value_not_stated_as_an_equality_is_not_a_given(sentence, quote, v):
    r = _len_run(sentence, quote, v)
    # a disjunction / a condition after the value is caught one layer earlier by the clause analyser; all refuse
    assert r.status == "REFUSED" and r.code in ("UNGROUNDED_VALUE", "NEGATED_CLAUSE", "CONDITIONAL_CLAUSE"), (r.answers, sentence)


@pytest.mark.parametrize("sentence,quote", EQUALITY, ids=[s for s, _q in EQUALITY])
def test_value_stated_as_an_equality_is_a_given(sentence, quote):
    r = _len_run(sentence, quote, "3")
    assert r.answers == {"q": "√17"}, (r.code, r.reason)


# ── group A: a clause that is not an unconditional assertion is not a given (shared clause analyser) ─────────────────
def _perp_run(sentence, quote):
    q, fs = HB._square()
    q, fs = [q[0], q[1], q[3]], [fs[0], fs[1], fs[3]]                       # SA = 3 but no SA ⊥ (ABCD)
    return run_fact_route(" ".join(q) + " " + sentence + " Tính độ dài SC.",
                          {"facts": fs + [f("f9", "perpendicular", quote, points_a=["S", "A"], points_b=list("ABCD")),
                                          LEN("Tính độ dài SC.")]})


PQ = "SA vuông góc với (ABCD)"
NOT_AN_ASSERTION = [
    ("Hãy chỉ ra rằng SA vuông góc với (ABCD).", PQ), ("Ta sẽ chỉ ra SA vuông góc với (ABCD).", PQ),
    ("Giải thích vì sao SA vuông góc với (ABCD).", PQ), ("Kiểm chứng rằng SA vuông góc với (ABCD).", PQ),
    ("Tìm điều kiện để SA vuông góc với (ABCD).", PQ), ("Muốn SA vuông góc với (ABCD) cần SA ⊥ AB.", PQ),
    ("Tại sao SA vuông góc với (ABCD)?", PQ), ("Liệu SA có vuông góc với (ABCD)?", "SA có vuông góc với (ABCD)"),
    ("Hễ SA vuông góc với (ABCD) là SC = 5.", PQ), ("Xét trường hợp SA vuông góc với (ABCD).", PQ),
    ("Cho rằng SA vuông góc với (ABCD), tìm lỗi sai.", PQ), ("Bạn An khẳng định SA vuông góc với (ABCD).", PQ),
    ("SA không hề vuông góc với (ABCD).", "SA không hề vuông góc với (ABCD)"),
    ("SA chẳng vuông góc với (ABCD).", "SA chẳng vuông góc với (ABCD)"),
    ("SA không nhất thiết vuông góc với (ABCD).", "SA không nhất thiết vuông góc với (ABCD)"),
    ("Không đúng là SA vuông góc với (ABCD).", PQ), ("SA có thể vuông góc với (ABCD).", "SA có thể vuông góc với (ABCD)"),
    ("SA vuông góc với (ABCD) hoặc SB vuông góc với (ABCD).", PQ),
]
ASSERTIONS = [
    ("SA vuông góc với (ABCD).", PQ), ("Biết SA vuông góc với (ABCD).", PQ),
    ("Biết SA vuông góc với (ABCD), SC bằng bao nhiêu?", PQ), ("Ta có SA vuông góc với (ABCD).", PQ),
    ("Chứng minh rằng SC = √17, biết SA vuông góc với (ABCD).", PQ),
]


@pytest.mark.parametrize("kind,sentence,quote", UNREAD_SECOND_CLAUSE, ids=[s for _k, s, _q in UNREAD_SECOND_CLAUSE])
def test_unread_second_clause_beside_a_given_is_refused(kind, sentence, quote):
    r = _len_run(sentence, quote, "3") if kind == "len" else _perp_run(sentence, PQ)
    assert (r.status, r.code) == ("REFUSED", "SOURCE_PREMISE_UNREAD"), (r.code, r.answers)


@pytest.mark.parametrize("sentence,quote", NOT_AN_ASSERTION, ids=[s for s, _q in NOT_AN_ASSERTION])
def test_clause_that_is_not_an_assertion_is_not_a_given(sentence, quote):
    r = _perp_run(sentence, quote)
    assert r.status == "REFUSED", (r.answers, sentence)


@pytest.mark.parametrize("sentence,quote", ASSERTIONS, ids=[s for s, _q in ASSERTIONS])
def test_assertions_stay_givens(sentence, quote):
    r = _perp_run(sentence, quote)
    assert r.answers == {"q": "√17"}, (r.code, r.reason, sentence)


# ── independent review of S1 (run `hybrid-semantic-hardening`): new false refusals I1, new false serve I2, open I4 / I5 ─
def SAREA_PL(s):
    return SAREA(s)


def DPP_D(s):
    return DPP(s, "D", "SBC")


def ANGPP(s):
    return ask("q", s, "angle", points_a=list("SBC"), points_b=list("ABCD"))


REVIEW_ASKED = [
    ("Tính khoảng cách từ đỉnh S đến mặt đáy.", DPP, False, F(9)),
    ("Tính khoảng cách từ đỉnh S đến mặt phẳng (ABCD).", DPP, False, F(9)),
    ("Tính góc giữa mặt bên (SBC) và mặt đáy.", ANGPP, False, None),
    ("Tính góc hợp bởi SC và mặt đáy.", ANG, False, F(8, 17)),
    ("Tính khoảng cách giữa hai đường thẳng chéo nhau SC và BD.", DLL, False, F(18, 17)),
    ("Tính thể tích khối chóp đã cho.", VOL, False, F(16)),
    ("Tính thể tích khối chóp đó.", VOL, False, F(16)),
    ("Tính độ dài các cạnh SB, SC.", LEN, False, F(17)),
    ("Tính độ dài các cạnh bên SB, SC, SD.", LEN, False, F(17)),
    ("Tính độ dài cạnh bên SC của hình chóp.", LEN, False, F(17)),
    ("Tính khoảng cách từ S đến (ABCD), từ đó suy ra thể tích khối chóp.", DPP, False, F(9)),
    ("Tính diện tích đáy ABCD.", lambda s: AREA(s, "ABCD"), False, F(16)),
    ("Tính diện tích ΔSAC.", lambda s: AREA(s, "SAC"), False, F(18)),
    ("Tính SC theo đơn vị cm.", LEN, False, F(17)),
    ("Tính: SC.", LEN, False, F(17)),
    ("Thể tích khối chóp S.ABCD bằng?", VOL, False, F(16)),
    ("Tính diện tích thiết diện tạo bởi mặt phẳng (MAB) và hình chóp S.ABCD.", SAREA_PL, True, F(117, 16)),
    ("Tính diện tích thiết diện của hình chóp S.ABCD bị cắt bởi mặt phẳng (MAB).", SAREA_PL, True, F(117, 16)),
    ("Tính diện tích thiết diện do mặt phẳng (MAB) cắt hình chóp S.ABCD.", SAREA_PL, True, F(117, 16)),
    ("Mặt phẳng (MAB) cắt hình chóp S.ABCD theo một thiết diện. Tính diện tích thiết diện đó.", SAREA_PL, True, F(117, 16)),
    ("Tính thể tích khối chóp S.ABCD bằng cách dùng công thức V = Bh/3.", VOL, False, F(16)),
]


@pytest.mark.parametrize("sentence,qf,mid,sq", REVIEW_ASKED, ids=[f"{s}|{i}" for i, (s, *_r) in enumerate(REVIEW_ASKED)])
def test_review_common_wordings_are_served(sentence, qf, mid, sq):
    r = _run_complete_requests(sentence, qf, mid)
    if sentence == "Tính khoảng cách từ S đến (ABCD), từ đó suy ra thể tích khối chóp.":
        # A complete extraction of "suy ra" remains a goal-clause refusal, not an answerable ask.
        assert (r.status, r.code) == ("REFUSED", "NOT_ASKED_IN_SOURCE"), r.answers
        sentence = sentence.replace("suy ra", "tính")
        r = _run_complete_requests(sentence, qf, mid)
    assert r.status == "SERVED", (r.code, r.reason, sentence)
    if sq is not None:
        assert HB.answer_square(r.answers["q"]) == sq, r.answers


# Policy override (run `shared-ask-grammar-safety`, closing review of 4acfc731, CR-2 & §6):
# - `theo a` requires `a` to be declared in the problem givens (`_co_tham_so_a(calls)`); on numeric `HB._square()` it is refused.
# - Requests for decimal rounding or angle representation in degrees/radians fail closed (`QUESTION_CONTEXT_UNSUPPORTED`)
#   because the deterministic engine only returns exact radical/rational expressions and `cos²=...` for angles.
POLICY_OVERRIDE_REFUSED = [
    ("Tính thể tích khối chóp S.ABCD theo a.", VOL, False),
    ("Tính SC, làm tròn kết quả đến hàng phần trăm.", LEN, False),
    ("Tính thể tích khối chóp S.ABCD, kết quả làm tròn đến hàng phần mười.", VOL, False),
    ("Tính góc giữa hai mặt phẳng (SBC) và (ABCD) theo độ.", ANGPP, False),
    ("Tính SC (làm tròn đến hàng phần trăm).", LEN, False),
]


@pytest.mark.parametrize("sentence,qf,mid", POLICY_OVERRIDE_REFUSED, ids=[s for s, *_r in POLICY_OVERRIDE_REFUSED])
def test_policy_override_undeclared_parameter_or_unsupported_format_is_refused(sentence, qf, mid):
    r = _run(sentence, qf, mid)
    assert r.status == "REFUSED" and r.code == "QUESTION_CONTEXT_UNSUPPORTED", (r.status, r.code, r.answers, sentence)


REVIEW_REFUSED = [
    ("Tính SC.SA.", LEN, False),                                       # I2: "." glued to the next label is not an end
    ("Tính SC: lấy hai lần kết quả.", LEN, False),
    ("Tính thể tích khối chóp S.ABCD; kết quả chia đôi.", VOL, False),
    ("Gọi V là thể tích khối chóp S.ABC. Tính V.", VOL, False),        # I4: V defined as another solid's volume
    ("Tính V(S.MAB).", VOL, True),
    ("Tính V (thể tích khối chóp M.ABCD).", VOL, True),
    ("Tính thể tích khối chóp S.ABCD (sau khi cắt bỏ khối chóp S.MAB).", VOL, True),   # a parenthesis that changes the figure
    ("Tính diện tích tam giác SAC (tính theo đơn vị mới gấp đôi).", lambda s: AREA(s, "SAC"), False),
]


@pytest.mark.parametrize("sentence,qf,mid", REVIEW_REFUSED, ids=[s for s, *_r in REVIEW_REFUSED])
def test_review_false_serves_are_refused(sentence, qf, mid):
    r = _run(sentence, qf, mid)
    assert r.status == "REFUSED", (r.answers, sentence)


REVIEW_NOT_ASSERTION = [
    ("SA không bao giờ vuông góc với (ABCD).", "SA không bao giờ vuông góc với (ABCD)"),
    ("SA không thể vuông góc với (ABCD).", "SA không thể vuông góc với (ABCD)"),
    ("SA chưa vuông góc với (ABCD).", "SA chưa vuông góc với (ABCD)"),
    ("SA không còn vuông góc với (ABCD).", "SA không còn vuông góc với (ABCD)"),
    ("Hãy kiểm tra rằng SA vuông góc với (ABCD).", PQ), ("Từ đó suy ra SA vuông góc với (ABCD).", PQ),
    ("Hãy suy ra SA vuông góc với (ABCD).", PQ), ("Xác minh SA vuông góc với (ABCD).", PQ),
    ("Vì sao SA vuông góc với (ABCD).", PQ), ("Giả định SA vuông góc với (ABCD).", PQ),
    ("Coi như SA vuông góc với (ABCD).", PQ), ("Bạn Bình cho là SA vuông góc với (ABCD).", PQ),
    ("Theo bạn An, SA vuông góc với (ABCD).", PQ),
    ("Cho biết SA có vuông góc với (ABCD) không.", "SA có vuông góc với (ABCD)"),
    ("SA vuông góc với (ABCD) khi M trùng S.", PQ), ("SA vuông góc với (ABCD) nếu M trùng S.", PQ),
    ("SA vuông góc với (ABCD) là sai.", PQ), ("SA vuông góc với (ABCD) khi và chỉ khi M trùng S.", PQ),
    ("SA vuông góc với (ABCD) là điều không đúng.", PQ), ("Hãy kiểm tra SA có vuông góc với (ABCD).", PQ),
    ("Hãy lập luận rằng SA vuông góc với (ABCD).", PQ),
]


@pytest.mark.parametrize("sentence,quote", REVIEW_NOT_ASSERTION, ids=[s for s, _q in REVIEW_NOT_ASSERTION])
def test_review_non_assertions_are_not_givens(sentence, quote):
    r = _perp_run(sentence, quote)
    assert r.status == "REFUSED", (r.answers, sentence)


REVIEW_VALUES_REFUSED = [("SA = 3 và SB = 3 là sai.", "SA = 3", "3"), ("SA = 3 và điều đó vô lí.", "SA = 3", "3"),
                         ("SA = 3.SB.", "SA = 3", "3")]
REVIEW_VALUES_SERVED = [("SA = 3 (cm).", "SA = 3 (cm)."), ("SA = 3 đơn vị.", "SA = 3 đơn vị."),
                        ("SA = 3 (đơn vị độ dài).", "SA = 3 (đơn vị độ dài).")]


@pytest.mark.parametrize("sentence,quote,v", REVIEW_VALUES_REFUSED, ids=[s for s, *_r in REVIEW_VALUES_REFUSED])
def test_review_values_that_are_not_givens(sentence, quote, v):
    assert _len_run(sentence, quote, v).status == "REFUSED"


@pytest.mark.parametrize("sentence,quote", REVIEW_VALUES_SERVED, ids=[s for s, _q in REVIEW_VALUES_SERVED])
def test_review_values_with_units_are_givens(sentence, quote):
    r = _len_run(sentence, quote, "3")
    assert r.answers == {"q": "√17"}, (r.code, r.reason)


def _mutant(monkeypatch, old, new):
    import sys
    import types
    from pathlib import Path

    from app.simulation.geometry_functions import engine as EN
    from app.simulation.geometry_functions import registry as RG

    src = Path(RG.__file__).read_text(encoding="utf-8")
    assert src.count(old) == 1, old
    m = types.ModuleType(RG.__name__ + "_mutant")
    m.__package__ = RG.__package__
    monkeypatch.setitem(sys.modules, m.__name__, m)
    exec(compile(src.replace(old, new), RG.__file__, "exec"), m.__dict__)
    m.TuChoi = RG.TuChoi
    monkeypatch.setattr(EN, "kiem_nguon", m.kiem_nguon)                  # the engine holds its own reference


MUTANTS = [
    ("point operand not bound", 'lambda m, a, k: m["p"] == a.point and _cung_mat', "lambda m, a, k: _cung_mat",
     ("Tính khoảng cách từ A đến (ABCD).", DPP, False)),
    ("plane operand not bound", 'm["p"] == a.point and _cung_mat(_mat_cua(m, "m", k), a.plane))',
     'm["p"] == a.point)', ("Tính khoảng cách từ S đến (SBC).", DPP, False)),
    ("solid symbol not bound", "if (sym := m[n + \"s\"]) and sym != solid:", "if (sym := m[n + \"s\"]) and False:",
     ("Tính thể tích khối chóp M.ABCD.", VOL, True)),
    # Re-pointed to `_vung_hoi` (run `shared-ask-grammar-safety`), which `_hoi_dung_cum` now delegates to.
    ("words before the phrase not checked", "if _GIUA_HOP_LE.fullmatch(_bo_cum(giua)) and sau else None", "if sau else None",
     ("Tính nửa thể tích khối chóp S.ABCD.", VOL, False)),
    ("section solid word not checked",
     '    if (kw := m[n + "k"]) and not sym and not tu and \\\n',
     '    if False and \\\n', ("Tính diện tích thiết diện của khối lập phương cắt bởi (MAB).", SAREA, True)),
]
VALUE_MUTANTS = [
    ("equality connector not checked", "if so and _NOI_BANG.fullmatch(de[dau + b:so.start()]) and ", "if so and ",
     ("SA ≥ 3.", "SA ≥ 3.", "3")),
    ("text after the value not checked", " and _DUOI_BANG.match(de[so.end():]):", ":", ("SA bằng 3 lần AB.", "SA bằng 3 lần AB.", "3")),
]


CLAUSE_MUTANTS = [
    # whole sentence quoted so that premise coverage is met and only the goal vocabulary decides
    ("new goal markers dropped", '"chứng tỏ", "chỉ ra", "giải thích", "kiểm chứng", "tìm điều kiện",', '"chứng tỏ",',
     ("Hãy chỉ ra rằng SA vuông góc với (ABCD).", "Hãy chỉ ra rằng SA vuông góc với (ABCD)")),
    ("non-assertion markers dropped", "or bool(_KHONG_KHANG_DINH.search(duoi + q))", "or False",
     ("SA có thể vuông góc với (ABCD).", "SA có thể vuông góc với (ABCD)")),
    # the whole sentence is quoted so that premise coverage (source-grounding-completeness) is met and only the
    # disjunction gate decides
    ("disjunction not checked", "or bool(_TUYEN.search(de[ma:mb]))", "or False",
     ("SA vuông góc với (ABCD) hoặc SB vuông góc với (ABCD).", "SA vuông góc với (ABCD) hoặc SB vuông góc với (ABCD)")),
]


def test_question_mark_clause_mutant_is_killed(monkeypatch):
    """Every sentence with "?" is now also read as a request context (two layers refuse "Liệu SA có vuông góc với
    (ABCD)?"), so the clause-role line is killed at its own level: the role read inside the "?" clause."""
    from app.simulation.geometry_functions import registry as RG

    de = "Liệu SA có vuông góc với (ABCD)?"
    assert RG._vai_tro_tai(de, de.index("vuông")) == "QUESTION"
    import sys
    import types
    from pathlib import Path

    src = Path(RG.__file__).read_text(encoding="utf-8")
    old = ' or de[ma:mb].rstrip().endswith("?") and not local_given\n'
    assert src.count(old) == 1
    m = types.ModuleType(RG.__name__ + "_mutant_q")
    m.__package__ = RG.__package__
    monkeypatch.setitem(sys.modules, m.__name__, m)
    exec(compile(src.replace(old, "\n"), RG.__file__, "exec"), m.__dict__)
    assert m._vai_tro_tai(de, de.index("vuông")) != "QUESTION", "mutant survived: question mark not a question clause"


@pytest.mark.parametrize("name,old,new,case", CLAUSE_MUTANTS, ids=[m[0] for m in CLAUSE_MUTANTS])
def test_clause_mutant_is_killed(monkeypatch, name, old, new, case):
    assert _perp_run(*case).status == "REFUSED", "the unmutated gate must refuse the kill case"
    _mutant(monkeypatch, old, new)
    assert _perp_run(*case).status == "SERVED", f"mutant survived: {name}"


@pytest.mark.parametrize("name,old,new,case", VALUE_MUTANTS, ids=[m[0] for m in VALUE_MUTANTS])
def test_value_mutant_is_killed(monkeypatch, name, old, new, case):
    assert _len_run(*case).status == "REFUSED", "the unmutated gate must refuse the kill case"
    _mutant(monkeypatch, old, new)
    assert _len_run(*case).status == "SERVED", f"mutant survived: {name}"


def test_equivalent_mutant_words_after_the_phrase_is_still_refused(monkeypatch):
    """Since run `shared-ask-grammar-safety` the question-context gate reads every word of an asking sentence, so an
    unread tail after the phrase is refused there too (defence in depth): dropping the tail check changes no outcome."""
    case = ("Tính thể tích phần còn lại của khối chóp S.ABCD.", VOL, False)
    assert _run(*case).status == "REFUSED"
    _mutant(monkeypatch, "sau = _SAU_HOP_LE.match(_bo_cum(de[b:c1]))", "sau = re.match('', '')")
    assert _run(*case).status == "REFUSED"


@pytest.mark.parametrize("name,old,new,case", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_mutant_is_killed(monkeypatch, name, old, new, case):
    assert _run(*case).status == "REFUSED", "the unmutated gate must refuse the kill case"
    _mutant(monkeypatch, old, new)
    assert _run(*case).status == "SERVED", f"mutant survived: {name}"


def test_solid_symbol_outranks_the_solid_word():
    """T3 of run `hybrid-semantic-hardening` (test_geometry_library_expansion): "Tính thể tích hình chóp ABCD.EFGH." names
    the prism by its exact symbol; the loose word "hình chóp" must not refuse it. The word is checked only when no symbol
    is given ("khối lập phương" for the single pyramid stays refused — FALSE_SERVES above)."""
    from app.simulation.geometry_functions import registry as RG

    m = RG._CUM_HOI["ask_volume"][0][0].search("Tính thể tích hình chóp ABCD.EFGH.")
    assert m and RG._khoi_khop(m, "k", "ABCD.EFGH", {"ABCD.EFGH": frozenset("ABCD")})
    m = RG._CUM_HOI["ask_volume"][0][0].search("Tính thể tích khối lập phương.")
    assert m and not RG._khoi_khop(m, "k", "S.ABCD", {"S.ABCD": frozenset("ABCD")})


def test_route_a_binds_ask_operands_too():
    t = ("Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 3. "
         "Tính khoảng cách từ A đến (SBC).")
    calls = [
        {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": list("ABCD")}, "source": {"quotes": ["Cho hình chóp S.ABCD."]}},
        {"id": "c2", "fn": "regular_polygon", "args": {"vertices": list("ABCD"), "side": "2"},
         "source": {"quotes": ["Đáy ABCD là hình vuông cạnh 2."]}},
        {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": list("ABCD")},
         "source": {"quotes": ["SA vuông góc với (ABCD)."]}},
        {"id": "c4", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "3"}, "source": {"quotes": ["SA = 3."]}},
        {"id": "c5", "fn": "ask_distance_point_plane", "args": {"point": "S", "plane": list("ABC")},
         "source": {"quotes": ["Tính khoảng cách từ A đến (SBC)."]}}]
    r = run_function_route(t, {"calls": calls})
    assert r.status == "REFUSED", r.answers
    calls[-1]["args"] = {"point": "A", "plane": list("SBC")}
    assert run_function_route(t, {"calls": calls}).status == "SERVED"
