# -*- coding: utf-8 -*-
"""Runner SEALED phải ĐÚNG TỪ LƯỢT ĐẦU — nó chỉ được chạy một lần.

Mọi script khác trong repo sai thì chạy lại; script này thì không. Chạy lại trên
SEALED là mua thêm một lần nhìn dữ liệu, và một benchmark được nhìn hai lần thì
không còn là held-out. Nên phần chấm, phần tổng kết và phần kiểm con dấu của nó
phải được kiểm TRƯỚC, offline, bằng dữ liệu giả.

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


# ── chấm ─────────────────────────────────────────────────────────
def test_cham_dung_khi_khop_ground_truth(rn):
    case = {"ground_truth": {"expected": {"max_val": 89}}}
    assert rn._cham(case, _Out({"max_val": 89}))["verdict"] == "PASS"


def test_cham_sai_thi_neu_ro_lech_o_dau(rn):
    case = {"ground_truth": {"expected": {"max_val": 89}}}
    kq = rn._cham(case, _Out({"max_val": 67}))
    assert kq["verdict"] == "FAIL"
    assert any("89" in d and "67" in d for d in kq["lech"])


def test_cham_khop_du_lech_kieu_so_va_chuoi(rn):
    """Ground truth do người viết tay thường là chuỗi. Trượt vì kiểu là oan."""
    case = {"ground_truth": {"expected": {"max_val": "89", "day": ["1", "2"]}}}
    assert rn._cham(case, _Out({"max_val": 89, "day": [1, 2]}))["verdict"] == "PASS"


def test_thieu_bien_la_FAIL_chu_khong_phai_bo_qua(rn):
    case = {"ground_truth": {"expected": {"max_val": 89}}}
    kq = rn._cham(case, _Out({"khac": 1}))
    assert kq["verdict"] == "FAIL"


def test_ground_truth_dang_la_thi_UNGRADED_chu_khong_doan(rn):
    """Đoán bừa rồi tính đạt thì B mất nghĩa; tính trượt thì vu oan cho hệ."""
    for gt in ({}, {"expected": None}, {"expected": {}}, {"expected": "max là 89"}):
        assert rn._cham({"ground_truth": gt}, _Out({"max_val": 89}))["verdict"] == "UNGRADED"


def test_khong_co_ket_qua_thi_NO_RESULT(rn):
    case = {"ground_truth": {"expected": {"max_val": 89}}}
    assert rn._cham(case, None)["verdict"] == "NO_RESULT"


# ── tổng kết ─────────────────────────────────────────────────────
def _r(cid, *, executable, servable, verdict="PASS", legacy="unsupported",
       tokens=None, error_code=None):
    return {
        "case_id": cid,
        "legacy": {"status": legacy, "simulation_id": None, "failure_category": None},
        "semantic": {"executable": executable, "servable": servable,
                     "error_code": error_code},
        "cham": {"verdict": verdict},
        "token": tokens or {"analyze": {"total_tokens": 100},
                            "semantic_program": {"total_tokens": 300}},
    }


class _NganSach:
    logical_calls = 40
    http_requests = 44
    retry_requests = 4


def test_A_luon_lon_hon_hoac_bang_B(rn):
    ket_qua = [
        _r("c1", executable=True, servable=True),
        _r("c2", executable=True, servable=False,
           error_code="semantic_verification_unavailable"),
        _r("c3", executable=False, servable=False, verdict="NO_RESULT",
           error_code="semantic_program_invalid"),
    ]
    bc = rn._tong_ket(ket_qua, {"commit_ngan": "abc1234", "cache_version": "34"},
                      "vantay", _NganSach(), None)
    assert bc["A_generative_executability"]["so"] == 2
    assert bc["B_safe_serve"]["so"] == 1
    assert bc["A_generative_executability"]["so"] >= bc["B_safe_serve"]["so"], (
        "A < B là bất khả thi: không phát canonical được thứ chưa chạy được"
    )


def test_ungraded_khong_lot_vao_tu_so_hay_mau_so(rn):
    ket_qua = [_r("c1", executable=True, servable=True, verdict="UNGRADED")]
    bc = rn._tong_ket(ket_qua, {}, "v", _NganSach(), None)
    d = bc["dung_so_voi_ground_truth"]
    assert d == {"pass": 0, "fail": 0, "ungraded": 1, "ghi_chu": d["ghi_chu"]}


def test_D2_tap_giao_rong_la_ket_qua_hop_le_khong_phai_loi(rn):
    """Case SEALED được chọn để KHÔNG có module chuyên biệt, nên đường cũ trượt
    gần hết là chuyện dự đoán được — và phải ghi đúng như thế."""
    ket_qua = [_r("c1", executable=True, servable=True, legacy="unsupported")]
    bc = rn._tong_ket(ket_qua, {}, "v", _NganSach(), None)
    assert bc["D2_matched_subset"]["so_case"] == 0
    assert "hợp lệ" in bc["D2_matched_subset"]["ghi_chu"]


def test_D2_cat_toi_da_12_va_TAT_DINH(rn):
    ket_qua = [_r(f"c{i:02d}", executable=True, servable=True, legacy="ok")
               for i in range(30)]
    lan1 = rn._tong_ket(ket_qua, {}, "v", _NganSach(), None)["D2_matched_subset"]
    lan2 = rn._tong_ket(list(reversed(ket_qua)), {}, "v", _NganSach(),
                        None)["D2_matched_subset"]
    assert lan1["so_case"] == 12
    assert lan1["case_id"] == lan2["case_id"], (
        "thứ tự đầu vào đổi mà tập chọn đổi theo ⇒ chọn không tất định"
    )


def test_phan_bo_that_bai_gom_theo_ma_loi(rn):
    ket_qua = [
        _r("c1", executable=True, servable=False, error_code="postcondition_violated"),
        _r("c2", executable=True, servable=False, error_code="postcondition_violated"),
        _r("c3", executable=False, servable=False, error_code="input_not_grounded"),
        _r("c4", executable=True, servable=True),
    ]
    bo = rn._tong_ket(ket_qua, {}, "v", _NganSach(), None)["phan_bo_that_bai"]
    assert bo["postcondition_violated"] == 2
    assert bo["input_not_grounded"] == 1
    assert "c4" not in bo


def test_bao_cao_ghi_lai_ngan_sach_da_dung(rn):
    bc = rn._tong_ket([_r("c1", executable=True, servable=True)], {}, "v",
                      _NganSach(), None)
    assert bc["ngan_sach"]["tran_logic"] == 160
    assert bc["ngan_sach"]["tran_http"] == 200
    assert bc["ngan_sach"]["logic_da_dung"] == 40


def test_dung_som_duoc_ghi_vao_bao_cao(rn):
    """Dừng vì hết ngân sách mà báo cáo không nói thì con số N đọc như đủ 40."""
    bc = rn._tong_ket([], {}, "v", _NganSach(), "BUDGET_EXHAUSTED: ...")
    assert bc["dung_som"].startswith("BUDGET_EXHAUSTED")


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


# ── một case chạy trọn, qua production orchestration ─────────────
def test_chay_mot_case_thu_duoc_ca_ba_thu(rn, monkeypatch):
    """Phần dễ hỏng câm nhất: observer nối sai thì runner ghi 40 bản ghi RỖNG,
    lượt live tiêu sạch quota và không thu được gì. Kiểm bằng LLM giả."""
    import asyncio

    from app.ai import pipeline

    from .test_route_wiring import _kich_ban  # cùng kịch bản 4 lượt

    monkeypatch.setattr(pipeline, "call_gemini", _fake_llm(_kich_ban()))
    case = {
        "case_id": "gia_01",
        "problem_text": "Tìm giá trị lớn nhất trong dãy 12 45 67 23 89 34",
        "ground_truth": {"kind": "human", "expected": {"max_val": 89}},
    }
    r = asyncio.run(rn._chay_mot_case(case, "khoa-gia"))

    assert r["loi_runner"] is None, r["loi_runner"]
    assert r["semantic"] is not None, "không thu được bản ghi route ngữ nghĩa"
    assert r["semantic"]["servable"] is True
    assert r["cham"]["verdict"] == "PASS", r["cham"]
    # SHADOW: đường cũ vẫn nói lời của nó, không bị route mới đè.
    assert r["legacy"]["status"] == "unsupported"
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


def test_ngan_sach_khop_ban_da_duyet(rn):
    """Sửa ba số này sau khi thấy kết quả = mua thêm lượt cho tới khi số đẹp."""
    assert (rn.TRAN_LOGIC, rn.TRAN_HTTP, rn.LUOT_MOI_CASE) == (160, 200, 4)
