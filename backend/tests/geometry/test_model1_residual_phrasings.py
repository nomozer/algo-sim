"""/13 Model 1 residuals: phrase families that made the /12 local route refuse a fully specified problem.

Diagnosis (run `axo-hybrid-local-model1-finalization-test-consolidation`, MODEL1_RESIDUAL_FAILURE_AUDIT.json): for 15 of
the 17 incomplete /12 cases the same geometry in a canonical phrasing is served and oracle-valid, so the first failing
layer is reading the original phrasing (deterministic parser / Source Gate), not planning or the kernel. The cases below
are NEW sentences of those families (different labels and values from /12 and from the /13 holdout); each must be read
by the deterministic parser alone (no SLM in tests) and served with the exact answer. The Source Gate is not loosened:
negated and conditional premises stay refused (last tests).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "docs/evaluation/geometry/harness/live-acceptance"))
import scene_oracle  # noqa: E402

from app.ai.adaptive_input_router import route_text_input_local_slm  # noqa: E402
from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally  # noqa: E402
from app.ai.local_slm_extractor import V9_CLOSURE_MODE  # noqa: E402

R3 = math.sqrt(3)

CASES = [
    # family: dotted tetrahedron notation "tứ diện X.YZT" (/12 V027, V047, V104)
    ("tetra_dot", "Dựng tứ diện S.ABC có SA, SB, SC đôi một vuông góc và SA = 1, SB = 2, SC = 3.", None),
    ("tetra_dot_query", "Cho tứ diện D.EFG với DE, DF, DG đôi một vuông góc, DE = DF = DG = 2. Tính thể tích khối tứ diện D.EFG.", [4 / 3]),
    # family: three mutually perpendicular edges meeting at a vertex that is not the first letter (/12 V098)
    ("trirect_base_corner", "Cho tứ diện A.BCD có AB, BC, BD đôi một vuông góc, AB = 3, BC = 1, BD = 2. Tính thể tích khối tứ diện.", [1.0]),
    # family: "các cạnh … sao cho …" (/12 V027)
    ("edges_such_that", "Vẽ tứ diện OIJK có các cạnh OI, OJ, OK đôi một vuông góc sao cho OI = 1, OJ = 1, OK = 2.", None),
    # family: two lateral faces through one edge, both ⊥ the base ⇒ that edge ⊥ the base (/12 V030, V040, V088)
    ("two_faces_perp_square", "Vẽ hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3, hai mặt phẳng (SAB) và (SAD) cùng vuông góc với (ABCD) và SA = 1.", None),
    ("two_faces_perp_tri", "Cho hình chóp D.ABC có hai mặt bên (DAB) và (DAC) cùng vuông góc với đáy, tam giác ABC đều cạnh 2, DA = 1. Tính thể tích khối chóp.", [R3 / 3]),
    ("two_faces_perp_ascii", "Ve hinh chop S.ABCD biet hai mat phang (SAB) va (SAD) cung vuong goc voi mat day (ABCD), ABCD la hinh vuong canh 1 va SA = 3.", None),
    # family: meta clauses that only say "draw, do not compute" (/12 V006, V031)
    ("meta_prefix", "Chỉ cần vẽ hình, không tính toán gì: hình chóp S.ABCD có đáy là hình vuông cạnh 1, SB vuông góc với đáy và SB = 1.", None),
    ("meta_suffix", "Cho hình chóp S.ABC có đáy là tam giác vuông tại A, AB = 1, AC = 2, SA vuông góc với (ABC), SA = 2. Không cần tính toán, hãy vẽ hình.", None),
    # family: purpose tail "để hiển thị thêm điểm …" (/12 V032)
    ("purpose_tail", "Vẽ hình lập phương ABCD.A'B'C'D' cạnh 2; gọi M là trung điểm của đoạn AA' để hiển thị thêm điểm M.", None),
    # family: "với" introducing data, not a condition (/12 V008, V033)
    ("voi_data", "Vẽ lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A với AB = 1, AC = 3 và AA' = 2.", None),
    # family: "đường cao SA = …" names the altitude (/12 V067)
    ("altitude_named", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 1, đường cao SA = 2. Vẽ hình chóp rồi tính thể tích khối chóp.", [2 / 3]),
    # family: "Biểu diễn … biết … và tính …" (/12 V062)
    ("represent_knowing", "Biểu diễn hình chóp S.ABCD biết ABCD là hình thoi cạnh 1, góc BAD = 60°, SA vuông góc với đáy, SA = 1 và tính thể tích khối chóp S.ABCD.", [R3 / 6]),
    # family: "Em muốn xem … có đáy … với …" (/12 V008)
    ("em_muon_xem_voi", "Em muốn xem hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A với AB = 2, AC = 3 và AA' = 4.", None),
    # family: "Dựng hình tứ diện O.ABC …" (/12 V027)
    ("dung_hinh_tu_dien_dot", "Dựng hình tứ diện O.ABC có các cạnh OA, OB, OC đôi một vuông góc sao cho OA = 1, OB = 2, OC = 3.", None),
    # family: rhombus side-diagonal angle (/12 V029)
    ("rhombus_side_diag_angle", "Vẽ hình chóp P.EFGH biết EFGH là hình thoi cạnh 2, góc FEG bằng 60°, PE vuông góc với (EFGH) và PE = 2.", None),
    # family: "Biểu diễn đường cao XY và hình chóp … rồi tính …" (/12 V067)
    ("sim_alt_before_solid", "Cho hình chóp P.EFGH có đáy EFGH là hình vuông cạnh 3, đường cao PE = 2. Biểu diễn đường cao PE và hình chóp P.EFGH rồi tính thể tích khối chóp.", [6.0]),
    # family: "có cạnh đáy 2 … tính độ dài cạnh bên XY và thể tích …" (/12 V070)
    ("reg_pyr_compound_lat_vol", "Dựng hình chóp tứ giác đều P.EFGH có cạnh đáy 2 và chiều cao bằng 2; tính độ dài cạnh bên PE và thể tích khối chóp.", [math.sqrt(6), 8 / 3]),
    # family: "tính diện tích tam giác … cùng thể tích khối lăng trụ" (/12 V072)
    ("poly_area_cung_volume", "Mô phỏng lăng trụ đứng DEF.D'E'F' có đáy là tam giác đều cạnh 4, cạnh bên DD' = √3 và tính diện tích tam giác DEF cùng thể tích khối lăng trụ.", [4 * R3, 12.0]),
]


@pytest.mark.parametrize("name,text,gold", CASES, ids=[c[0] for c in CASES])
def test_residual_family_is_read_by_the_parser_and_served_exactly(name, text, gold, monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    lp = parse_geometry_problem_locally(text, use_cache=False)
    assert lp.status == LOCAL_PARSE_COMPLETE, (lp.status, lp.reason_code, lp.fallback_reason)
    out = route_text_input_local_slm(text, closure_mode=V9_CLOSURE_MODE, normalizer_version="v3", runtime=None,
                                     allow_download=False, use_cache=False)
    rd = out.response["route_d"]
    assert out.status == "SERVED", (rd.get("refusal"), rd.get("reason_code"))
    assert rd.get("extraction_mode") == "LOCAL_DETERMINISTIC_PARSER"
    if gold is not None:
        num = scene_oracle.numeric(rd.get("answers"), rd.get("answer_exact"), gold)
        assert num["status"] == "CORRECT", num


@pytest.mark.parametrize("text", [
    "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2, hai mặt phẳng (SAB) và (SAD) không cùng vuông góc với đáy, SA = 1. Vẽ hình.",
    "Nếu hai mặt phẳng (SAB) và (SAD) cùng vuông góc với đáy thì hãy vẽ hình chóp S.ABCD có đáy là hình vuông cạnh 2 và SA = 1.",
    "Không cần vẽ hình chóp S.ABCD có đáy là hình vuông cạnh 2, SA vuông góc với đáy và SA = 1.",
])
def test_negated_or_conditional_premises_stay_refused(text, monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    lp = parse_geometry_problem_locally(text, use_cache=False)
    assert lp.status != LOCAL_PARSE_COMPLETE, (text, lp.status)


@pytest.mark.parametrize("text", [
    "Vẽ hình chóp P.EFGH có đáy EFGH là hình thoi cạnh 2, góc FEG bằng 90°, PE vuông góc với đáy và PE = 2.",
    "Vẽ hình chóp P.EFGH có đáy EFGH là hình thoi cạnh 2, góc FEG bằng 120°, PE vuông góc với đáy và PE = 2.",
])
def test_invalid_rhombus_side_diagonal_angle_is_refused(text, monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    out = route_text_input_local_slm(text, closure_mode=V9_CLOSURE_MODE, normalizer_version="v3", runtime=None,
                                     allow_download=False, use_cache=False)
    assert out.status == "REFUSED"
    assert (out.response["route_d"].get("refusal") or {}).get("code") == "INCONSISTENT_FACTS"


@pytest.mark.parametrize("text", [
    "Dựng hình chóp K.DEFG với đáy hình chữ nhật DEFG, DE = 4, DG = 5, KD vuông góc với đáy, KD = 6, sau đó tính thể tích khối chóp K.DEFG.",
    "Cho hình chóp K.DEFG có đáy hình chữ nhật DEFG, DE = 4, DG = 5, KD vuông góc với đáy và KD = 6. Tính thể tích khối chóp K.DEFG.",
])
def test_nominal_rectangle_base_has_grounded_rectangle_and_exact_volume(text):
    lp = parse_geometry_problem_locally(text, use_cache=False)
    assert lp.status == LOCAL_PARSE_COMPLETE
    assert any(p["kind"] == "rectangle" for p in lp.payload["premises"])
    out = route_text_input_local_slm(text, closure_mode=V9_CLOSURE_MODE, normalizer_version="v3",
                                     allow_download=False, use_cache=False)
    assert out.status == "SERVED", out.response["route_d"].get("refusal")
    assert out.response["route_d"]["answers"]["q1"] == "40"


def test_negated_rectangle_base_does_not_supply_shape():
    text = "Vẽ hình chóp K.DEFG có đáy không phải hình chữ nhật DEFG, DE = 4, DG = 5, KD vuông góc với đáy, KD = 6."
    lp = parse_geometry_problem_locally(text, use_cache=False)
    assert not lp.payload or not any(p["kind"] == "rectangle" for p in lp.payload["premises"])


def test_named_symbolic_pyramid_after_3d_display_prefix_has_no_numeric_goal():
    text = "Mô hình 3D: chóp K.DEFG, đáy DEFG là hình vuông có cạnh 4a, KD ⊥ (DEFG), KD = 2a."
    lp = parse_geometry_problem_locally(text, use_cache=False)
    assert lp.status == LOCAL_PARSE_COMPLETE
    out = route_text_input_local_slm(text, closure_mode=V9_CLOSURE_MODE, normalizer_version="v3",
                                     allow_download=False, use_cache=False)
    assert out.status == "SERVED", out.response["route_d"].get("refusal")
    assert not out.response["route_d"].get("answers")


def test_extra_display_request_retains_source_grounded_center():
    text = "Vẽ hình chóp K.DEFG có đáy là hình vuông DEFG cạnh 4, KD vuông góc với đáy, KD = 3; O là giao điểm của DF và EG. Hiển thị cả điểm O nhé."
    lp = parse_geometry_problem_locally(text, use_cache=False)
    assert lp.status == LOCAL_PARSE_COMPLETE, lp.reason_code
    out = route_text_input_local_slm(text, closure_mode=V9_CLOSURE_MODE, normalizer_version="v3",
                                     allow_download=False, use_cache=False)
    assert out.status == "SERVED", out.response["route_d"].get("refusal")
    assert any(o["id"] == "O" and o["origin"] != "free"
               for o in out.response["envelope"]["scene3d"]["objects"])


def test_extra_display_request_cannot_create_a_point():
    text = "Vẽ hình chóp K.DEFG có đáy là hình vuông DEFG cạnh 4, KD vuông góc với đáy, KD = 3. Hiển thị cả điểm O nhé."
    lp = parse_geometry_problem_locally(text, use_cache=False)
    assert lp.status != LOCAL_PARSE_COMPLETE


@pytest.mark.parametrize("tail", ["Chỉ vẽ, không tính.", "Em chỉ cần hình vẽ thôi."])
def test_display_only_tail_never_adds_a_math_goal(tail):
    text = "Cho hình chóp K.DEFG, đáy DEFG là hình chữ nhật, DE = 5, DG = 6, KD vuông góc với đáy và KD = 4. " + tail
    lp = parse_geometry_problem_locally(text, use_cache=False)
    assert lp.status == LOCAL_PARSE_COMPLETE, lp.reason_code
    assert not lp.payload["math_goals"]
    out = route_text_input_local_slm(text, closure_mode=V9_CLOSURE_MODE, normalizer_version="v3",
                                     allow_download=False, use_cache=False)
    assert out.status == "SERVED"
    assert not out.response["route_d"].get("answers")


# /14 takeover (run `local-model1-recovery-offline-vision`, CACHE 154): phrase families that kept fully specified
# problems from being served in the CACHE 153 diagnosis. Sentences use labels and values absent from Holdout-1 and
# Holdout-2; each family has an opposite case below that must stay refused.
CASES_14 = [
    # "⟂" (U+27C2) is "⊥" (U+22A5): normalized once in `normalize_problem_text`
    ("perp_symbol_plane", "Cho hình chóp K.LMNP có đáy LMNP là hình vuông cạnh 3, KL ⟂ (LMNP) và KL = 4. Tính thể tích khối chóp.", [12.0]),
    ("perp_symbol_lines", "Vẽ tứ diện DEFG có DE ⟂ DF, DF ⟂ DG, DG ⟂ DE, DE = 1, DF = 2, DG = 3.", None),
    # "trong đó" opens the description of the solid the sentence named (Source Gate `_C_DAU`)
    ("trong_do_lead", "Vẽ hình chóp K.LMNP, trong đó đáy LMNP là hình vuông cạnh 5 và KL vuông góc với đáy, KL = 2.", None),
    # a sentence opening with a request for a quantity of the solid itself (Source Gate `_C_KHOI_HOI`, `_SAU_HOP_LE`)
    ("ask_solid_first_biet", "Tính thể tích khối chóp K.LMNP biết đáy LMNP là hình vuông cạnh 3, KL vuông góc với đáy và KL = 4.", [12.0]),
    ("ask_solid_first_co", "Tính thể tích khối chóp K.LMNP có đáy LMNP là hình vuông cạnh 3, KL vuông góc với đáy và KL = 4.", [12.0]),
]


@pytest.mark.parametrize("name,text,gold", CASES_14, ids=[c[0] for c in CASES_14])
def test_v14_family_is_served_exactly_without_slm(name, text, gold, monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    out = route_text_input_local_slm(text, closure_mode=V9_CLOSURE_MODE, normalizer_version="v3", runtime=None,
                                     allow_download=False, use_cache=False)
    rd = out.response["route_d"]
    assert out.status == "SERVED", (rd.get("refusal"), rd.get("reason_code"))
    assert rd.get("extraction_mode") in ("LOCAL_DETERMINISTIC_PARSER", "LOCAL_PARSER_AFTER_V3_NORMALIZER")
    if gold is not None:
        num = scene_oracle.numeric(rd.get("answers"), rd.get("answer_exact"), gold)
        assert num["status"] == "CORRECT", num


@pytest.mark.parametrize("text", [
    # a negated "⟂" is no premise
    "Cho hình chóp K.LMNP có đáy LMNP là hình vuông cạnh 3, KL không ⟂ (LMNP) và KL = 4. Vẽ hình.",
    # a request that itself carries a number leaves its sentence unread (height 5 against KL = 4)
    "Tính thể tích khối chóp K.LMNP có chiều cao 5 biết LMNP là hình vuông cạnh 3, KL vuông góc với đáy và KL = 4.",
    # a condition after the asked object is not a locative
    "Tính diện tích tam giác DFG khi DG thay đổi trong tứ diện DEFG có DE, DF, DG đôi một vuông góc. DE = 1, DF = 2.",
    # the side of the square is not given
    "Tính thể tích khối chóp K.LMNP biết đáy là hình vuông và KL vuông góc với đáy, KL = 4.",
    # a request about another object (a triangle) does not open a declaration: its unlabelled side binds nothing
    "Tính diện tích tam giác KLM biết đáy LMNP là hình vuông cạnh 3, KL vuông góc với đáy và KL = 4.",
    # "có" after a word, not a label, is no data lead
    "Cho hình chóp K.LMNP có đáy LMNP là hình vuông cạnh 3 và KL vuông góc với đáy. Tính độ dài KL có bằng 4 không.",
])
def test_v14_opposite_cases_stay_refused(text, monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    out = route_text_input_local_slm(text, closure_mode=V9_CLOSURE_MODE, normalizer_version="v3", runtime=None,
                                     allow_download=False, use_cache=False)
    assert out.status != "SERVED", out.response["route_d"].get("answers")


def test_v14_cache_policy_isolates_cache_153_rows():
    """The /14 grammar changes may bind a role in a sentence that bound none, so a scene cached under 153 is not reused."""
    from tests.cache_policy import assert_cache_policy_at_least, assert_route_d_row_misses

    assert_cache_policy_at_least(154)
    assert_route_d_row_misses("153:route-d")


# /15 (run `grounded-geometry-language-recovery`): families A–G read through the `VN12`–`VN17` normalizer rules; served
# without the SLM and exact. Opposite cases must stay refused. Labels/values are absent from Holdout-1/2/3.
CASES_15 = [
    ("edges_from_vertex", "Tứ diện IJKL có ba cạnh xuất phát từ I đôi một vuông góc, IJ = 2, IK = 3, IL = 4. Tính thể tích khối tứ diện IJKL.", [4.0]),
    ("three_right_angles", "Vẽ tứ diện IJKL có các góc JIK, KIL, LIJ đều vuông, IJ = 2, IK = 3, IL = 4.", None),
    ("seg_length_and_perp", "Cho hình chóp U.VWXY có đáy VWXY là hình chữ nhật, VW = 3, VY = 5, cạnh UV dài 2 và vuông góc với đáy. Tính thể tích khối chóp.", [10.0]),
    ("seg_is_altitude", "Cho hình chóp U.VWXY có đáy VWXY là hình chữ nhật, VW = 3, VY = 5, UV là đường cao và UV = 2. Vẽ hình.", None),
    ("respective_swapped", "Cho tứ diện IJKL có IJ, IK, IL đôi một vuông góc, IK, IL, IJ lần lượt bằng 2, 3, 4. Tính độ dài JK.", [2 * math.sqrt(5)]),
    ("legs_in_order", "Vẽ lăng trụ đứng GHI.JKL có đáy GHI vuông tại G, hai cạnh góc vuông GH, GI dài 2 và 5, GJ = 3.", None),
    ("prism_height_form", "Lăng trụ đứng GHI.JKL có đáy GHI vuông tại G, GH = 2, GI = 5, chiều cao lăng trụ bằng 3. Tính thể tích khối lăng trụ.", [15.0]),
    ("bare_request", "Cho hình chóp U.VWXY có đáy VWXY là hình chữ nhật, VW = 3, VY = 5, UV vuông góc với đáy và UV = 2. Hãy mô phỏng.", None),
    ("question_first_locative", "Tính diện tích tam giác IJK trong tứ diện IJKL có IJ, IK, IL đôi một vuông góc, IJ = 2, IK = 3, IL = 4.", [3.0]),
]


@pytest.mark.parametrize("name,text,gold", CASES_15, ids=[c[0] for c in CASES_15])
def test_v15_family_is_served_exactly(name, text, gold, monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    out = route_text_input_local_slm(text, closure_mode=V9_CLOSURE_MODE, normalizer_version="v3", runtime=None,
                                     allow_download=False, use_cache=False)
    rd = out.response["route_d"]
    assert out.status == "SERVED", (rd.get("refusal"), rd.get("reason_code"))
    assert rd.get("extraction_mode") in ("LOCAL_DETERMINISTIC_PARSER", "LOCAL_PARSER_AFTER_V3_NORMALIZER")
    if gold is not None:
        num = scene_oracle.numeric(rd.get("answers"), rd.get("answer_exact"), gold)
        assert num["status"] == "CORRECT", num
    else:
        assert not rd.get("answers")


@pytest.mark.parametrize("text", [
    "Cho tứ diện IJKL có IJ, IK, IL không đôi một vuông góc, IJ = 2, IK = 3, IL = 4. Vẽ hình.",
    "Tính thể tích khối tứ diện IJKL có IJ, IK, IL không đôi một vuông góc, IJ = 2, IK = 3, IL = 4.",
    "Cho tứ diện IJKL có IJ, IK, IL đôi một vuông góc, IJ, IK, IL lần lượt bằng 2 và 3. Vẽ hình.",
    "Cho hình chóp U.VWXY có đáy VWXY là hình chữ nhật, VW = 3, VY = 5, cạnh UV dài 2 và UW vuông góc với đáy. Vẽ hình.",
    "Tính diện tích tam giác ABC trong tứ diện IJKL có IJ, IK, IL đôi một vuông góc, IJ = 2, IK = 3, IL = 4.",
    "Vẽ lăng trụ GHI.JKL có đáy GHI vuông tại G, GH = 2, GI = 5, chiều cao lăng trụ bằng 3.",
])
def test_v15_opposite_cases_stay_refused(text, monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    out = route_text_input_local_slm(text, closure_mode=V9_CLOSURE_MODE, normalizer_version="v3", runtime=None,
                                     allow_download=False, use_cache=False)
    assert out.status != "SERVED", out.response["route_d"].get("answers")


@pytest.mark.parametrize("clause,negated", [
    ("IJ, IK, IL không đôi một vuông góc", True),
    ("SA không cùng vuông góc với đáy", True),
    ("IJ, IK, IL đôi một vuông góc", False),
    ("Không cần tính toán, IJ, IK, IL đôi một vuông góc", False),
])
def test_v15_source_gate_reads_negation_across_an_adverb(clause, negated):
    """The Source Gate itself (not the parser or the SLM) refuses a negated relation quote — the /14 CACHE 154 product
    served "IJ, IK, IL không đôi một vuông góc" as three right angles through a grounded AxoV9 lowering."""
    from app.simulation.geometry_functions import registry

    assert registry._phu_dinh(clause, 0, clause) is negated


def test_v15_cache_policy_isolates_cache_154_rows():
    """CACHE 154 could serve a negated pairwise perpendicularity; its rows are never reused under 155."""
    from tests.cache_policy import assert_cache_policy_at_least, assert_route_d_row_misses

    assert_cache_policy_at_least(155)
    assert_route_d_row_misses("154:route-d")
