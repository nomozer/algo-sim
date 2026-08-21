# -*- coding: utf-8 -*-
"""Runner SEALED phải ĐÚNG TỪ LƯỢT ĐẦU — nó chỉ được chạy một lần.

Mọi script khác trong repo sai thì chạy lại; script này thì không. Chạy lại trên
SEALED là mua thêm một lần nhìn dữ liệu, và một benchmark được nhìn hai lần thì
không còn là held-out. Nên phần chấm, phần tổng kết và phần kiểm con dấu của nó
phải được kiểm TRƯỚC, offline, bằng dữ liệu giả.

Sáu điểm được sửa trước khi seal (2026-08-21), mỗi điểm có test riêng dưới đây:

    1. semantic shadow ĐỘC LẬP với phán quyết của classifier legacy
    2. trần lượt logic được CƯỠNG CHẾ, không chỉ đếm
    3. A−B phân rã theo nguyên nhân, không gọi gộp là `verification_gap`
    4. ground truth KHÔNG phụ thuộc tên biến do LLM đặt
    5. N=40 khoá; chạy thiếu thì không công bố A/B như kết quả chính
    6. D1 trả về đúng nghĩa CẤU TRÚC

Dữ liệu ở đây là BỊA HOÀN TOÀN và cố ý bịa thô — nó chỉ kiểm số học của runner,
không kiểm năng lực của hệ.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

RUNNER = Path(__file__).resolve().parents[2] / "scripts" / "run_sealed_evaluation.py"


@pytest.fixture(scope="module")
def rn():
    spec = importlib.util.spec_from_file_location("run_sealed_evaluation", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Out:
    def __init__(self, final_memory):
        self.final_memory = final_memory


#: Hợp đồng do server đóng băng — witness là tên biến LLM tự đặt.
HOP_DONG = {"obligations": [
    {"kind": "extremum", "container": "arr", "witness": "ket_qua_lon_nhat"},
]}


# ── 4. chấm KHÔNG phụ thuộc tên biến ─────────────────────────────
def test_cham_dung_khi_khop_ground_truth(rn):
    case = {"ground_truth": {"expected": [{"obligation_kind": "extremum", "value": 89}]}}
    kq = rn._cham(case, HOP_DONG, _Out({"ket_qua_lon_nhat": 89}))
    assert kq["verdict"] == "PASS", kq


def test_custodian_KHONG_phai_doan_ten_bien_cua_LLM(rn):
    """Điểm 4. Custodian chỉ khai nghĩa vụ + giá trị; tên biến đọc từ contract.

    Chương trình đúng gọi biến `ket_qua_lon_nhat`, custodian không hề biết tên
    ấy — trước bản sửa thì case này FAIL oan, và cái FAIL oan đi thẳng vào con
    số chính của luận văn.
    """
    case = {"ground_truth": {"expected": [{"obligation_kind": "extremum", "value": 89}]}}
    for ten_bien in ("ket_qua_lon_nhat", "max_val", "m", "gia_tri_max"):
        hop_dong = {"obligations": [
            {"kind": "extremum", "container": "arr", "witness": ten_bien},
        ]}
        kq = rn._cham(case, hop_dong, _Out({ten_bien: 89}))
        assert kq["verdict"] == "PASS", f"{ten_bien}: {kq}"


def test_cham_sai_thi_neu_ro_lech_o_dau(rn):
    case = {"ground_truth": {"expected": [{"obligation_kind": "extremum", "value": 89}]}}
    kq = rn._cham(case, HOP_DONG, _Out({"ket_qua_lon_nhat": 67}))
    assert kq["verdict"] == "FAIL"
    assert any("89" in d and "67" in d for d in kq["lech"])


def test_cham_khop_du_lech_kieu_so_va_chuoi(rn):
    """Ground truth do người viết tay thường là chuỗi. Trượt vì kiểu là oan."""
    case = {"ground_truth": {"expected": [
        {"obligation_kind": "extremum", "value": "89"},
    ]}}
    assert rn._cham(case, HOP_DONG, _Out({"ket_qua_lon_nhat": 89}))["verdict"] == "PASS"


def test_witness_khong_co_trong_bo_nho_la_FAIL(rn):
    case = {"ground_truth": {"expected": [{"obligation_kind": "extremum", "value": 89}]}}
    kq = rn._cham(case, HOP_DONG, _Out({"bien_khac": 1}))
    assert kq["verdict"] == "FAIL"


def test_he_khong_khai_nghia_vu_do_thi_UNGRADED_chu_khong_FAIL(rn):
    """Không có witness để tra ⇒ chưa kết luận được, KHÔNG phải trả lời sai."""
    case = {"ground_truth": {"expected": [
        {"obligation_kind": "reachability", "value": True},
    ]}}
    kq = rn._cham(case, HOP_DONG, _Out({"ket_qua_lon_nhat": 89}))
    assert kq["verdict"] == "UNGRADED"
    assert "KHÔNG khai" in kq["ly_do"]


def test_nhieu_nghia_vu_cung_loai_ma_thieu_index_thi_UNGRADED(rn):
    hop_dong = {"obligations": [
        {"kind": "extremum", "container": "a", "witness": "max_a"},
        {"kind": "extremum", "container": "b", "witness": "max_b"},
    ]}
    case = {"ground_truth": {"expected": [{"obligation_kind": "extremum", "value": 9}]}}
    assert rn._cham(case, hop_dong, _Out({"max_a": 9}))["verdict"] == "UNGRADED"


def test_co_index_thi_chi_dung_duoc_nghia_vu_nao(rn):
    hop_dong = {"obligations": [
        {"kind": "extremum", "container": "a", "witness": "max_a"},
        {"kind": "extremum", "container": "b", "witness": "max_b"},
    ]}
    case = {"ground_truth": {"expected": [
        {"obligation_kind": "extremum", "index": 1, "value": 42},
    ]}}
    kq = rn._cham(case, hop_dong, _Out({"max_a": 9, "max_b": 42}))
    assert kq["verdict"] == "PASS", kq


def test_sai_chung_minh_duoc_thang_thu_chua_cham_duoc(rn):
    """Một câu trả lời đã biết là SAI thì không còn là 'chưa kết luận'."""
    case = {"ground_truth": {"expected": [
        {"obligation_kind": "extremum", "value": 89},
        {"obligation_kind": "reachability", "value": True},
    ]}}
    kq = rn._cham(case, HOP_DONG, _Out({"ket_qua_lon_nhat": 1}))
    assert kq["verdict"] == "FAIL"
    assert kq["khong_cham"], "vẫn phải ghi lại phần không chấm được"


def test_ground_truth_dang_la_thi_UNGRADED_chu_khong_doan(rn):
    for gt in ({}, {"expected": None}, {"expected": []},
               {"expected": {"max_val": 89}}, {"expected": "max là 89"}):
        kq = rn._cham({"ground_truth": gt}, HOP_DONG, _Out({"ket_qua_lon_nhat": 89}))
        assert kq["verdict"] == "UNGRADED", gt


def test_khong_co_ket_qua_thi_NO_RESULT(rn):
    case = {"ground_truth": {"expected": [{"obligation_kind": "extremum", "value": 89}]}}
    assert rn._cham(case, HOP_DONG, None)["verdict"] == "NO_RESULT"


# ── tổng kết ─────────────────────────────────────────────────────
def _r(cid, *, executable, servable, verdict="PASS", legacy="unsupported",
       tokens=None, error_code=None, stage=None, buoc=10, luot=4):
    return {
        "case_id": cid,
        "legacy": {"status": legacy, "simulation_id": None, "failure_category": None},
        "semantic": {"executable": executable, "servable": servable,
                     "error_code": error_code, "stage_reached": stage,
                     "total_steps": buoc},
        "contract": HOP_DONG,
        "cham": {"verdict": verdict},
        "token": tokens or {"analyze": {"total_tokens": 100, "calls": 1},
                            "semantic_program": {"total_tokens": 300, "calls": 1}},
        "so_luot_llm": luot,
        "ngat_vi_ngan_sach": False,
    }


class _NganSach:
    logical_calls = 40
    http_requests = 44
    retry_requests = 4


def test_A_luon_lon_hon_hoac_bang_B(rn):
    ket_qua = [
        _r("c1", executable=True, servable=True),
        _r("c2", executable=True, servable=False, stage="verification",
           error_code="semantic_verification_unavailable"),
        _r("c3", executable=False, servable=False, verdict="NO_RESULT",
           error_code="semantic_program_invalid"),
    ]
    bc = rn._tong_ket(ket_qua, 3, {"commit_ngan": "abc1234", "cache_version": "34"},
                      "vantay", _NganSach(), None)
    assert bc["A_generative_executability"]["so"] == 2
    assert bc["B_internal_servable"]["so"] == 1
    assert bc["A_generative_executability"]["so"] >= bc["B_internal_servable"]["so"]


# ── 3. A−B phân rã theo nguyên nhân ──────────────────────────────
def test_A_tru_B_phan_ra_KHONG_goi_gop_la_verification_gap(rn):
    """Điểm 3. C₁b fail, C₂ fail và binding fail đều `servable=False`, nhưng chỉ
    MỘT nhánh là thiếu-cách-kiểm-chứng. Gộp cả khối là báo cáo sai."""
    ket_qua = [
        _r("c1", executable=True, servable=False, stage="verification",
           error_code="semantic_verification_unavailable"),
        _r("c2", executable=True, servable=False, stage="realized_coverage",
           error_code="obligation_witness_unrealized"),
        _r("c3", executable=True, servable=False, stage="postconditions",
           error_code="postcondition_violated"),
        _r("c4", executable=True, servable=False, stage="binding",
           error_code="semantic_program_invalid"),
    ]
    bc = rn._tong_ket(ket_qua, 4, {}, "v", _NganSach(), None)
    pr = bc["A_tru_B_phan_ra"]
    assert pr["tong"] == 4
    assert pr["theo_nguyen_nhan"] == {
        "verification_gap": 1,
        "C1b_witness_unrealized": 1,
        "C2_postcondition_violated": 1,
        "binding_unresolved": 1,
    }, pr["theo_nguyen_nhan"]
    assert pr["theo_nguyen_nhan"]["verification_gap"] != pr["tong"], (
        "verification_gap KHÔNG được bằng cả khối A−B"
    )


def test_B_khong_duoc_goi_la_dung(rn):
    bc = rn._tong_ket([_r("c1", executable=True, servable=True)], 1, {}, "v",
                      _NganSach(), None)
    assert "KHÔNG PHẢI" in bc["B_internal_servable"]["khai"]
    assert "B_safe_serve" not in bc, "nhãn cũ hứa nhiều hơn thứ đo được"


def test_phat_nhung_oracle_noi_sai_duoc_neu_dich_danh(rn):
    """Case hệ tự cho là phát được nhưng ground truth nói SAI — con số quan
    trọng nhất trong báo cáo, vì nó nói cổng nội bộ chưa đủ."""
    ket_qua = [
        _r("c1", executable=True, servable=True, verdict="PASS"),
        _r("c2", executable=True, servable=True, verdict="FAIL"),
    ]
    bc = rn._tong_ket(ket_qua, 2, {}, "v", _NganSach(), None)
    xau = bc["dung_theo_oracle_doc_lap"]["phat_nhung_oracle_noi_SAI"]
    assert xau["so"] == 1 and xau["case_id"] == ["c2"]


# ── 5. N khoá, accounting đóng ───────────────────────────────────
def test_chay_thieu_case_thi_khong_cong_bo_AB_nhu_ket_qua_chinh(rn):
    """Điểm 5. Mẫu số co lại thì A/B đọc như thể benchmark chỉ có ngần ấy bài."""
    ket_qua = [_r(f"c{i}", executable=True, servable=True) for i in range(27)]
    bc = rn._tong_ket(ket_qua, 40, {}, "v", _NganSach(), "BUDGET_EXHAUSTED: ...")
    assert bc["N_planned"] == 40
    assert bc["N_processed"] == 27
    assert bc["evaluation_complete"] is False
    assert "KHÔNG được công bố" in bc["canh_bao"]


def test_chay_du_40_thi_danh_dau_hoan_chinh(rn):
    ket_qua = [_r(f"c{i}", executable=True, servable=True) for i in range(40)]
    bc = rn._tong_ket(ket_qua, 40, {}, "v", _NganSach(), None)
    assert bc["evaluation_complete"] is True
    assert bc["canh_bao"] is None


def test_ground_truth_accounting_cong_ve_dung_N_processed(rn):
    """pass + fail + ungraded + no_result phải BẰNG N_processed. Trước bản sửa
    `NO_RESULT` rơi ra ngoài cả bốn ô và tổng không khớp."""
    ket_qua = [
        _r("c1", executable=True, servable=True, verdict="PASS"),
        _r("c2", executable=True, servable=True, verdict="FAIL"),
        _r("c3", executable=True, servable=False, verdict="UNGRADED"),
        _r("c4", executable=False, servable=False, verdict="NO_RESULT"),
    ]
    bc = rn._tong_ket(ket_qua, 4, {}, "v", _NganSach(), None)
    o = bc["dung_theo_oracle_doc_lap"]
    assert o["tong_kiem"] == bc["N_processed"] == 4
    assert (o["pass"], o["fail"], o["ungraded"], o["no_result"]) == (1, 1, 1, 1)


def test_ti_le_dung_chi_tinh_tren_so_cham_duoc(rn):
    ket_qua = [
        _r("c1", executable=True, servable=True, verdict="PASS"),
        _r("c2", executable=True, servable=True, verdict="FAIL"),
        _r("c3", executable=True, servable=True, verdict="UNGRADED"),
    ]
    o = rn._tong_ket(ket_qua, 3, {}, "v", _NganSach(), None)["dung_theo_oracle_doc_lap"]
    assert o["ti_le_tren_so_cham_duoc"] == 0.5, "UNGRADED không được vào mẫu số"


# ── 6. D1 đúng nghĩa cấu trúc ────────────────────────────────────
def test_D1_la_claim_cau_truc_khong_phai_gia_do_duoc(rn):
    """Điểm 6. Số bước trải rộng mà số lượt LLM đứng yên — đó mới là D1."""
    ket_qua = [
        _r("c1", executable=True, servable=True, buoc=8, luot=4),
        _r("c2", executable=True, servable=True, buoc=250, luot=4),
    ]
    bc = rn._tong_ket(ket_qua, 2, {}, "v", _NganSach(), None)
    d1 = bc["D1_structural_interpreter_khong_ton_token"]
    assert d1["so_luot_llm_phan_bo"] == [4], "số lượt LLM phải độc lập với số bước"
    assert d1["so_buoc_min_max"] == {"min": 8, "max": 250}
    assert "D1_token_case_ngu_nghia" not in bc, "D1 không phải token/case"
    assert bc["semantic_token_per_case"]["khai"].startswith("Telemetry hỗ trợ")


# ── D2 ───────────────────────────────────────────────────────────
def test_D2_tap_giao_rong_la_ket_qua_hop_le_khong_phai_loi(rn):
    ket_qua = [_r("c1", executable=True, servable=True, legacy="unsupported")]
    bc = rn._tong_ket(ket_qua, 1, {}, "v", _NganSach(), None)
    assert bc["D2_matched_subset"]["so_case"] == 0
    assert "hợp lệ" in bc["D2_matched_subset"]["ghi_chu"]


def test_D2_cat_toi_da_12_va_TAT_DINH(rn):
    ket_qua = [_r(f"c{i:02d}", executable=True, servable=True, legacy="ok")
               for i in range(30)]
    lan1 = rn._tong_ket(ket_qua, 30, {}, "v", _NganSach(), None)["D2_matched_subset"]
    lan2 = rn._tong_ket(list(reversed(ket_qua)), 30, {}, "v", _NganSach(),
                        None)["D2_matched_subset"]
    assert lan1["so_case"] == 12
    assert lan1["case_id"] == lan2["case_id"]


def test_phan_bo_that_bai_gom_theo_ma_loi(rn):
    ket_qua = [
        _r("c1", executable=True, servable=False, error_code="postcondition_violated"),
        _r("c2", executable=True, servable=False, error_code="postcondition_violated"),
        _r("c3", executable=False, servable=False, error_code="input_not_grounded"),
        _r("c4", executable=True, servable=True),
    ]
    bo = rn._tong_ket(ket_qua, 4, {}, "v", _NganSach(), None)["phan_bo_that_bai"]
    assert bo["postcondition_violated"] == 2
    assert bo["input_not_grounded"] == 1
    assert "c4" not in bo


def test_bao_cao_ghi_lai_ngan_sach_da_dung(rn):
    bc = rn._tong_ket([_r("c1", executable=True, servable=True)], 1, {}, "v",
                      _NganSach(), None)
    assert bc["ngan_sach"]["tran_logic"] == 440
    assert bc["ngan_sach"]["tran_http"] == 520
    assert bc["ngan_sach"]["logic_da_dung"] == 40


# ── một case chạy trọn, qua production orchestration ─────────────
def test_chay_mot_case_thu_duoc_ca_ba_thu(rn, monkeypatch):
    """Observer nối sai thì runner ghi 40 bản ghi RỖNG, lượt live tiêu sạch
    quota và không thu được gì."""
    import asyncio

    from app.ai import pipeline

    from .test_route_wiring import _kich_ban

    monkeypatch.setattr(pipeline, "call_gemini", _fake_llm(_kich_ban()))
    case = {
        "case_id": "gia_01",
        "problem_text": "Tìm giá trị lớn nhất trong dãy 12 45 67 23 89 34",
        "ground_truth": {"kind": "human",
                         "expected": [{"obligation_kind": "extremum", "value": 89}]},
    }
    r = asyncio.run(rn._chay_mot_case(case, "khoa-gia"))

    assert r["loi_runner"] is None, r["loi_runner"]
    assert r["semantic"] is not None, "không thu được bản ghi route ngữ nghĩa"
    assert r["semantic"]["servable"] is True
    assert r["contract"] is not None and r["contract"]["obligations"], (
        "không thu được hợp đồng ⇒ không có witness để chấm"
    )
    assert r["cham"]["verdict"] == "PASS", r["cham"]
    assert r["legacy"]["status"] == "unsupported"
    assert r["so_luot_llm"] == 4
    assert set(r["token"]) >= {"analyze", "classify", "semantic_analyze",
                               "semantic_program"}, r["token"]


def _fake_llm(responses):
    async def f(api_key, system_prompt, user_text, response_schema=None,
                temperature=0.2, image=None):
        from app.ai.telemetry import current_stage, record_usage

        assert responses, "gọi nhiều hơn scripted"
        record_usage(current_stage(), {"totalTokenCount": 100})
        return responses.pop(0)
    return f


# ── con dấu ──────────────────────────────────────────────────────
def test_khong_co_sealed_thi_dung_sach_chu_khong_no(rn, monkeypatch, tmp_path):
    monkeypatch.setattr(rn, "SEALED", tmp_path / "khong-co.json")
    with pytest.raises(rn.DungSach, match="CUSTODIAN"):
        rn._kiem_seal()


def test_sealed_khong_co_van_tay_thi_tu_choi_chay(rn, monkeypatch, tmp_path):
    cases = tmp_path / "cases.json"
    cases.write_text(json.dumps({"cases": []}), encoding="utf-8")
    monkeypatch.setattr(rn, "SEALED", cases)
    monkeypatch.setattr(rn, "FINGERPRINT", tmp_path / "khong-co.txt")
    with pytest.raises(rn.DungSach, match="niêm phong"):
        rn._kiem_seal()


def test_sealed_bi_sua_sau_khi_niem_phong_thi_tu_choi(rn, monkeypatch, tmp_path):
    cases = tmp_path / "cases.json"
    cases.write_text(json.dumps({"cases": [{"case_id": "x"}]}), encoding="utf-8")
    van_tay = tmp_path / "FINGERPRINT.txt"
    van_tay.write_text("0" * 64, encoding="utf-8")
    monkeypatch.setattr(rn, "SEALED", cases)
    monkeypatch.setattr(rn, "FINGERPRINT", van_tay)
    with pytest.raises(rn.DungSach, match="BỊ SỬA"):
        rn._kiem_seal()


def test_thieu_ALLOW_LIVE_AI_thi_khong_tieu_quota(rn, monkeypatch):
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    with pytest.raises(rn.DungSach, match="ALLOW_LIVE_AI"):
        rn._bat_buoc_live()


def test_ngan_sach_khop_ban_da_duyet(rn):
    """Ngân sách CUỐI, chốt 2026-08-22 trước khi niêm phong SEALED."""
    assert (rn.TRAN_LOGIC, rn.TRAN_HTTP) == (440, 520)
    assert rn.LUOT_TOI_THIEU_MOI_CASE == 4


def test_upper_bound_duoc_dan_xuat_khong_phai_uoc_luong(rn):
    """Điểm 2. Upper bound thật đọc từ call graph là 11, KHÔNG phải 4.

    Con số 11 phải có mặt trong mã để lần sau không ai lại tưởng 4 là bound.
    """
    assert rn.LUOT_TOI_DA_MOI_CASE == 11
    assert rn.LUOT_TOI_DA_MOI_CASE > rn.LUOT_TOI_THIEU_MOI_CASE


def test_tran_logic_du_cho_N40_o_worst_case(rn):
    """Ngân sách KHÔNG được xung đột với mục tiêu nghiên cứu đã khoá.

    Trần cũ 160 = 4 × 40 đúng bằng đường hạnh phúc, nên một lần retry duy nhất
    ở bất kỳ đâu cũng đủ làm `evaluation_complete=false` — tức ngân sách tự nó
    ngăn benchmark đạt N=40. Trần phải phủ được WORST case, không phải best.
    """
    assert rn.TRAN_LOGIC >= rn.LUOT_TOI_DA_MOI_CASE * 40, (
        f"{rn.TRAN_LOGIC} < {rn.LUOT_TOI_DA_MOI_CASE} × 40 — ngân sách có thể "
        "chặn evaluation trước khi đủ 40 case"
    )


def test_tran_HTTP_rong_hon_tran_logic_de_chiu_transient(rn):
    """Rộng hơn CHỈ để chịu 429/5xx, không phải để dò tìm kết quả tốt hơn."""
    assert rn.TRAN_HTTP > rn.TRAN_LOGIC
    headroom = (rn.TRAN_HTTP - rn.TRAN_LOGIC) / rn.TRAN_LOGIC
    assert 0.10 <= headroom <= 0.30, f"headroom {headroom:.0%} ngoài khoảng đã chốt"
