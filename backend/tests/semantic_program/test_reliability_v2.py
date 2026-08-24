# -*- coding: utf-8 -*-
"""Phân loại Reliability V2 — mỗi case ĐÚNG MỘT tầng. **0 API call.**

Dữ liệu ở đây **bịa hoàn toàn và cố ý bịa thô**: nó kiểm số học của bộ phân
loại, không kiểm năng lực của hệ. Vài bản ghi lấy nguyên văn `reason` từ SEALED
`7e5df014…` vì chính chuỗi ấy là thứ bộ phân loại phải đọc đúng.

Nửa quan trọng của file là các ca **PHÂN BIỆT**: lớp 2 (ký pháp) và lớp 3 (ngữ
nghĩa) dùng CHUNG mã lỗi `semantic_program_invalid`. Gộp chúng thì bảng thất bại
chỉ sai chỗ phải sửa — lớp 2 chữa được bằng biên chuẩn hoá, lớp 3 thì không.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_M = Path(__file__).resolve().parents[2] / "scripts" / "reliability_v2.py"


@pytest.fixture(scope="module")
def rv():
    spec = importlib.util.spec_from_file_location("reliability_v2", _M)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["reliability_v2"] = mod
    spec.loader.exec_module(mod)
    return mod


#: Nguyên văn từ SEALED — 21/40 case chết với đúng chuỗi này.
LOI_PYDANTIC = (
    "SEMANTIC_PROGRAM_INVALID: Lỗi cú pháp schema SemanticProgramSpec: "
    "1 validation error for SemanticProgramSpec\nspec_version\n  "
    "Input should be '1.0' [type=literal_error, input_value=1.0, input_type=float]"
)
#: Validator NGỮ NGHĨA — câu khác hẳn, không mang dấu Pydantic.
LOI_NGU_NGHIA = (
    "SEMANTIC_PROGRAM_INVALID: push tham chiếu container không tồn tại: 'kho'."
)
LOI_PARSE = "SEMANTIC_PROGRAM_INVALID: JSON không parse được (Unterminated string)"


def _sr(**kw):
    return {"stage_reached": kw.pop("stage"), **kw}


# ── lớp 0: chưa tới bước sinh ─────────────────────────────────────────────
def test_scope_la_lop_0_KHONG_phai_that_bai_sinh(rv):
    """Chặn đề ngoài môn là hành vi ĐÚNG. Gộp vào tử số thất bại sinh là tự
    bôi bẩn số của chính mình."""
    l, c = rv.phan_loai(_sr(stage="scope", error_code="gate_out_of_scope"))
    assert l == rv.LAYER_CONTRACT and c == "gate_out_of_scope"


def test_grounding_la_lop_0(rv):
    l, _ = rv.phan_loai(_sr(stage="grounding", error_code="input_not_grounded"))
    assert l == rv.LAYER_CONTRACT


def test_lop_0_thi_G1_G2_la_None_khong_phai_False(rv):
    """`False` ở đây là đổ lỗi sinh cho một case chưa bao giờ tới bước sinh."""
    k = rv.chi_so_case("x", _sr(stage="scope", error_code="gate_out_of_scope"))
    assert k["G1_schema_pass"] is None
    assert k["G2_semantic_validation_pass"] is None


# ── lớp 1 vs 2 vs 3: cùng một mã lỗi, ba tầng khác nhau ───────────────────
def test_json_cut_la_lop_1_generation(rv):
    l, c = rv.phan_loai(_sr(stage="semantic_program",
                            error_code="semantic_program_invalid",
                            reason=LOI_PARSE))
    assert l == rv.LAYER_GENERATION and c == "llm_output_unusable"


def test_loi_pydantic_la_lop_2_schema(rv):
    l, _ = rv.phan_loai(_sr(stage="semantic_program",
                            error_code="semantic_program_invalid",
                            reason=LOI_PYDANTIC))
    assert l == rv.LAYER_SCHEMA


def test_loi_validator_la_lop_3_KHONG_phai_lop_2(rv):
    """Cùng `error_code` với lớp 2. Phân biệt bằng chuỗi lý do, không bằng mã."""
    l, _ = rv.phan_loai(_sr(stage="semantic_program",
                            error_code="semantic_program_invalid",
                            reason=LOI_NGU_NGHIA))
    assert l == rv.LAYER_SEMANTIC_VALIDATION


def test_ba_lop_nay_dung_CHUNG_ma_loi(rv):
    """Khoá chống trôi: nếu ai đó phân loại theo `error_code` thì test này đỏ."""
    ma = "semantic_program_invalid"
    ket = {rv.phan_loai(_sr(stage="semantic_program", error_code=ma, reason=r))[0]
           for r in (LOI_PARSE, LOI_PYDANTIC, LOI_NGU_NGHIA)}
    assert ket == {rv.LAYER_GENERATION, rv.LAYER_SCHEMA, rv.LAYER_SEMANTIC_VALIDATION}


def test_G1_phan_biet_dung_giua_lop_2_va_lop_3(rv):
    """Qua ký pháp nhưng trượt ngữ nghĩa ⇒ G1 đúng, G2 sai."""
    k2 = rv.chi_so_case("x", _sr(stage="semantic_program",
                                 error_code="semantic_program_invalid",
                                 reason=LOI_PYDANTIC))
    k3 = rv.chi_so_case("x", _sr(stage="semantic_program",
                                 error_code="semantic_program_invalid",
                                 reason=LOI_NGU_NGHIA))
    assert (k2["G1_schema_pass"], k2["G2_semantic_validation_pass"]) == (False, False)
    assert (k3["G1_schema_pass"], k3["G2_semantic_validation_pass"]) == (True, False)


# ── lớp 4 / 6 / 7 ─────────────────────────────────────────────────────────
def test_interpreter_la_lop_4(rv):
    l, _ = rv.phan_loai(_sr(stage="execution", error_code="semantic_execution_error"))
    assert l == rv.LAYER_INTERPRETER


def test_tran_thuc_thi_cung_la_lop_4(rv):
    l, _ = rv.phan_loai(_sr(stage="execution",
                            error_code="interpreter_budget_exhausted"))
    assert l == rv.LAYER_INTERPRETER


def test_C1a_la_lop_6_assurance(rv):
    l, _ = rv.phan_loai(_sr(stage="structural_coverage",
                            error_code="requested_operation_uncovered"))
    assert l == rv.LAYER_ASSURANCE


def test_C2_la_lop_6(rv):
    l, _ = rv.phan_loai(_sr(stage="postconditions",
                            error_code="postcondition_violated", executable=True))
    assert l == rv.LAYER_ASSURANCE


def test_binding_la_lop_7(rv):
    l, _ = rv.phan_loai(_sr(stage="binding", error_code="binding_unresolved"))
    assert l == rv.LAYER_RENDERING


# ── lớp 5: chỉ xét khi ĐÃ ĐO ──────────────────────────────────────────────
def test_served_ma_replay_truot_la_lop_5(rv):
    l, _ = rv.phan_loai(_sr(stage="served", executable=True, servable=True),
                        replay_ok=False)
    assert l == rv.LAYER_REPLAY


def test_served_va_replay_qua_thi_KHONG_co_tang_that_bai(rv):
    l, c = rv.phan_loai(_sr(stage="served", executable=True, servable=True),
                        replay_ok=True)
    assert (l, c) == (None, None)


def test_replay_CHUA_DO_thi_KHONG_bi_tinh_la_truot(rv):
    """`None` ≠ `False`. Trộn 'chưa đo' với 'trượt' là bịa thêm thất bại."""
    l, c = rv.phan_loai(_sr(stage="served", executable=True, servable=True),
                        replay_ok=None)
    assert (l, c) == (None, None)


def test_render_CHUA_DO_thi_KHONG_bi_tinh_la_truot(rv):
    l, c = rv.phan_loai(_sr(stage="served", executable=True, servable=True),
                        replay_ok=True, render_ok=None)
    assert (l, c) == (None, None)


# ── mỗi case ĐÚNG MỘT tầng ────────────────────────────────────────────────
def test_tong_phan_bo_bang_dung_N(rv):
    """Gán theo cổng CUỐI CÙNG chạm tới thì một case vào nhiều lớp và tổng > N."""
    khoi = [
        rv.chi_so_case("a", _sr(stage="scope", error_code="gate_out_of_scope")),
        rv.chi_so_case("b", _sr(stage="semantic_program",
                                error_code="semantic_program_invalid",
                                reason=LOI_PYDANTIC)),
        rv.chi_so_case("c", _sr(stage="structural_coverage",
                                error_code="requested_operation_uncovered")),
        rv.chi_so_case("d", _sr(stage="served", executable=True, servable=True),
                       replay_ok=True),
    ]
    t = rv.tong_hop(khoi)
    assert t["N"] == 4
    assert t["tong_kiem"] == 4, "một case bị đếm vào nhiều tầng"
    assert t["phan_bo_tang_that_bai"]["di_tron_duong"] == 1


# ── tổng hợp: ĐẾM, không phần trăm ────────────────────────────────────────
def test_tong_hop_KHONG_phat_ra_phan_tram(rv):
    """§3.3 cấm chia khi mẫu số < 20, mà mẫu số của R/O/V là số ca qua tầng
    trước. An toàn nhất: hàm này không chia, chỉ phát tử số và mẫu số."""
    t = rv.tong_hop([rv.chi_so_case("a", _sr(stage="served", executable=True,
                                             servable=True), replay_ok=True)])
    thanh_phan = [t[k] for k in t if isinstance(t[k], dict)]
    for tp in thanh_phan:
        assert "ti_le" not in tp and "rate" not in tp and "percent" not in tp


def test_mau_so_cua_R_la_so_ca_CO_A_khong_phai_N(rv):
    """Trộn hai mẫu số là bịa ra một con số không tồn tại."""
    khoi = [
        rv.chi_so_case("a", _sr(stage="semantic_program",
                                error_code="semantic_program_invalid",
                                reason=LOI_PYDANTIC)),
        rv.chi_so_case("b", _sr(stage="served", executable=True, servable=True),
                       replay_ok=True),
    ]
    t = rv.tong_hop(khoi)
    assert t["N"] == 2
    assert t["A_executable"]["tu_so"] == 1
    assert t["R_replay"]["mau_so"] == 1, "R phải tính trên ca CÓ A, không trên N"


def test_oracle_UNGRADED_khong_vao_tu_lan_mau(rv):
    k = rv.chi_so_case("a", _sr(stage="served", executable=True, servable=True),
                       cham={"verdict": "UNGRADED"})
    assert k["oracle_O"] is None
    t = rv.tong_hop([k])
    assert t["O_oracle"] == {"tu_so": 0, "mau_so": 0, "chua_do": 1}


# ── hình dạng khối per-case ───────────────────────────────────────────────
def test_khoi_case_co_du_muoi_truong_theo_protocol(rv):
    k = rv.chi_so_case("T10-C5-025", _sr(stage="served", executable=True,
                                         servable=True), replay_ok=True)
    for truong in ("source_id", "G1_schema_pass", "G2_semantic_validation_pass",
                   "executable_A", "replay_R", "assurance_B", "renderer_V",
                   "oracle_O", "failure_layer", "failure_code"):
        assert truong in k, f"thiếu trường {truong}"
    assert k["source_id"] == "T10-C5-025"


def test_tam_nhan_tang_dong_va_khop_protocol(rv):
    assert set(rv.TEN_TANG) == set(range(8))
    assert rv.TEN_TANG[0] == "contract_failure"
    assert rv.TEN_TANG[7] == "rendering_failure"
