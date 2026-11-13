# -*- coding: utf-8 -*-
"""Root-cause localization and the targeted semantic repairs of run `semantic-failure-safe-image-segmentation`.

Diagnostics: the root cause is separated from the terminal reason, unread clauses are located by offset in the text the
parser read, a goal on a plane whose definition was unread is a downstream dependency (not the root), and "understood
but unsupported" (cos/tan of an angle, a proof) is not reported as "not understood".
Repairs (each with a positive case equal to an already supported wording, a negative case, and a construction check):
the base named "mặt phẳng đáy" in an angle question; a named point defined inside the plane clause; the question
"Thiết diện … cắt bởi (P) là hình gì?"; the exam stem "Diện tích thiết diện … bằng".
"""
from __future__ import annotations

import pytest

from app.ai.adaptive_input_router import normalize_problem_text, route_text_input, strip_trailing_multiple_choice_options
from app.ai.local_failure_diagnostics import clause_types

P = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
MSA = "Gọi M là trung điểm của SA. "
DEF_P = "Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD). "
SEC = "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P)."


def _r(text):
    r = route_text_input(text, allow_live_ai=False).response
    return r["route_d"], r


def _section(text):
    rd, r = _r(text)
    assert rd["status"] == "SERVED", rd.get("refusal")
    sec = [o for o in r["envelope"]["scene3d"]["objects"] if o["type"] == "section"]
    assert len(sec) == 1
    return sorted(tuple(p) for p in sec[0]["polygon"])


# ── diagnostics ───────────────────────────────────────────────────────────────────────────────────────────────────────
def test_root_cause_is_separate_from_the_terminal_reason_and_points_at_the_unread_clause():
    text = P + MSA + "Mặt phẳng (P) đi qua M và song song với AB. " + SEC
    rd, _ = _r(text)
    d = rd["local_diagnostics"]
    assert rd["refusal"]["code"] == "LIVE_AI_DISABLED" and d["terminal_reason"] == "LIVE_AI_DISABLED"
    assert d["root_cause"] == "UNRECOGNIZED_GEOMETRIC_ENTITY" and d["first_loss_layer"] == "PARSER"
    assert d["fallback"] == "LOCAL_PROVIDER_FALLBACK_DISABLED"
    norm = strip_trailing_multiple_choice_options(normalize_problem_text(text))
    lost = next(c for c in d["clauses"] if c["failure_reason"] == "UNRECOGNIZED_GEOMETRIC_ENTITY")
    assert norm[lost["start_offset"]:lost["end_offset"]].startswith("Mặt phẳng (P) đi qua M và song song với AB")
    goal = next(c for c in d["clauses"] if c["clause_type"] == "CONSTRUCTION_GOAL")
    assert goal["failure_reason"] == "DEPENDS_ON_UNREAD_CLAUSE" and goal["downstream_dependency"] == [lost["clause_id"]]
    assert all("_text" not in c for c in d["clauses"])                       # offsets only; the text is not repeated


@pytest.mark.parametrize("text,root,detected", [
    (P + "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (Q).", "UNRESOLVED_REFERENCE", "PARSER_COVERAGE"),
    (P + "Tính côsin của góc giữa đường thẳng SC và mặt phẳng (ABCD).", "UNSUPPORTED_GOAL_FUNCTION", None),
    (P + "Chứng minh rằng BC vuông góc với mặt phẳng (SAB).", "UNSUPPORTED_GOAL_KIND", "PARSER"),
    ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông, SA vuông góc với mặt phẳng đáy. Tính thể tích khối chóp S.ABCD.",
     "INSUFFICIENT_CONSTRAINTS", "PARSER"),
    ("Cho hình chóp S.ABCD như hình vẽ. Tính thể tích khối chóp S.ABCD.", "DIAGRAM_DEPENDENT_FACT", "SOURCE_GATE"),
    (P + "Mặt phẳng (P) chứa AB và song song với CD. " + SEC, "INSUFFICIENT_CONSTRAINTS", "SOURCE_FACTS"),
    ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, AB = 2a, SA vuông góc với mặt phẳng đáy và SA = a. "
     "Tính thể tích khối chóp S.ABCD.", "SOURCE_CONFLICT", None),
])
def test_refusals_are_attributed_to_the_layer_that_owns_them(text, root, detected):
    rd, _ = _r(text)
    d = rd["local_diagnostics"]
    assert rd["status"] != "SERVED" and d["root_cause"] == root, d
    if detected:
        assert d["detected_by"] == detected


def test_a_request_verb_opens_a_goal_not_a_definition():
    assert clause_types("Xác định trung điểm của SA")[0] == "CONSTRUCTION_GOAL"
    assert clause_types("Gọi M là trung điểm của SA")[0] == "POINT_DEFINITION"
    assert clause_types("Thể tích khối chóp S.ABCD bằng")[0] == "MEASUREMENT_GOAL"
    assert clause_types("A. 2a. B. 3a. C. a. D. 4a.")[0] == "MULTIPLE_CHOICE_OPTIONS"


def test_a_served_problem_carries_no_diagnostics():
    rd, _ = _r(P + "Tính thể tích khối chóp S.ABCD.")
    assert rd["status"] == "SERVED" and "local_diagnostics" not in rd


# ── repairs ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_base_named_mat_phang_day_in_an_angle_question_equals_the_named_base():
    a, _ = _r(P + "Góc giữa đường thẳng SC và mặt phẳng đáy bằng")
    b, _ = _r(P + "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).")
    assert a["status"] == b["status"] == "SERVED" and a["answers"] == b["answers"]
    c, _ = _r(P + "Tính góc giữa hai mặt phẳng (SBC) và mặt đáy.")
    d, _ = _r(P + "Tính góc giữa hai mặt phẳng (SBC) và (ABCD).")
    assert c["status"] == d["status"] == "SERVED" and c["answers"] == d["answers"]


def test_mat_day_is_never_read_without_a_declared_base():
    rd, _ = _r("Cho tứ diện ABCD có AB = AC = AD = a và đôi một vuông góc. Tính góc giữa đường thẳng BC và mặt đáy.")
    assert rd["status"] != "SERVED"


def test_a_named_point_defined_inside_the_plane_clause_builds_the_same_section():
    base = _section(P + MSA + DEF_P + SEC)
    rel = _section(P + "Mặt phẳng (P) đi qua trung điểm M của SA và song song với mặt phẳng (ABCD). " + SEC)
    assert rel == base


def test_a_point_already_defined_is_not_redefined_by_the_plane_clause():
    rd, _ = _r(P + "Gọi M là trung điểm của SB. Mặt phẳng (P) đi qua trung điểm M của SA và song song với mặt phẳng (ABCD). " + SEC)
    assert rd["status"] != "SERVED"


def test_the_question_la_hinh_gi_on_a_defined_plane_builds_the_section():
    base = _section(P + MSA + DEF_P + SEC)
    q = _section(P + MSA + DEF_P + "Thiết diện của hình chóp cắt bởi mặt phẳng (P) là hình gì?")
    assert q == base
    rd, _ = _r(P + MSA + DEF_P + "Thiết diện của hình chóp cắt bởi mặt phẳng (Q) là hình gì?")
    assert rd["status"] != "SERVED"


def test_the_exam_stem_dien_tich_thiet_dien_bang_asks_the_area_and_a_given_area_is_not_a_question():
    a, _ = _r(P + MSA + DEF_P + "Diện tích thiết diện của hình chóp cắt bởi mặt phẳng (P) bằng")
    b, _ = _r(P + MSA + DEF_P + "Tính diện tích thiết diện của hình chóp cắt bởi mặt phẳng (P).")
    assert a["status"] == b["status"] == "SERVED" and a["answers"] == b["answers"]
    c, _ = _r(P + MSA + DEF_P + "Diện tích thiết diện của hình chóp cắt bởi mặt phẳng (P) bằng 5.")
    assert c["status"] != "SERVED"


def test_renamed_vertices_keep_the_repairs():
    a, _ = _r(P + "Góc giữa đường thẳng SC và mặt phẳng đáy bằng")
    b, _ = _r("Cho hình chóp T.MNPQ có đáy MNPQ là hình vuông cạnh a, TM vuông góc với mặt phẳng đáy và TM = a. "
              "Góc giữa đường thẳng TP và mặt phẳng đáy bằng")
    assert a["status"] == b["status"] == "SERVED" and a["answers"] == b["answers"]
