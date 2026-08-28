# -*- coding: utf-8 -*-
"""PHASE 7 TASK 2 — thiết kế tập HELD-OUT 20 bài. **0 API call.**

File này khoá **thiết kế**, không khoá kết quả: chưa có pool, chưa có seed của
GVHD, nên chưa có số nào để kiểm. Cái kiểm được ngay bây giờ — và chỉ kiểm được
*trước* khi chạy — là **bốn bảo đảm của giao thức**:

    ① 20 ô đích danh, phủ đủ tám nghĩa vụ hình học   (đa dạng do THIẾT KẾ)
    ② đáp án đến từ NGOÀI, tra ngược được            (oracle độc lập)
    ③ không bài nào trùng tập DEV                    (không dùng lại DEV)
    ④ hệ không đổi giữa niêm phong và chạy           (không sửa theo từng bài)

Sau khi chạy thì ba trong bốn cái trên không kiểm lại được nữa — nên chúng phải
đỏ được từ bây giờ.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from app.simulation.semantic_program.domain_profile import (
    geometry_obligation_kinds,
)

GOC = Path(__file__).resolve().parents[3]
GEO = GOC / "docs" / "evaluation" / "geometry"


def _nap(ten: str):
    dd = GOC / "backend" / "scripts" / f"{ten}.py"
    spec = importlib.util.spec_from_file_location(f"_t_{ten}", dd)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def SH():
    return _nap("seal_geometry_holdout")


def _bai(**kw) -> dict:
    """Một bài tầng A hợp lệ. Test làm hỏng ĐÚNG MỘT trường mỗi lần."""
    goc = {
        "case_id": "hp_x", "slot": "A11",
        "chu_de": "Khoảng cách điểm–mặt",
        "problem_text": "Cho hình chóp S.ABCD …",
        "expected_obligations": ["distance"],
        "nguon": {"ten": "Đề tham khảo 2025", "url": "https://x/y", "vi_tri": "Câu 43"},
        "dap_an_chinh_thuc": "a√3/3",
        "phep_chuyen": "a=1 ⇒ d²=1/3",
        "oracle_result": {"distance": "1/3"},
        "chua_chay_he": True,
    }
    goc.update(kw)
    return goc


# ══ ① ĐA DẠNG LÀ TÍNH CHẤT CỦA THIẾT KẾ, KHÔNG PHẢI MAY RỦI CỦA SEED ═════
def test_dung_20_o_chia_14_A_va_6_B(SH):
    assert len(SH.BANG_O) == 20
    assert len(SH.O_TANG_A) == 14 and len(SH.O_TANG_B) == 6


def test_tang_A_phu_DU_tam_nghia_vu_hinh_hoc(SH):
    """Dẫn từ `geometry_obligation_kinds()`, KHÔNG chép danh sách thứ hai.

    Thêm một nghĩa vụ hình học vào taxonomy mà quên mở ô cho nó ⇒ ĐỎ ở đây —
    đúng lúc còn sửa được, thay vì phát hiện khi đọc kết quả và thấy một nghĩa
    vụ chưa từng được đo.
    """
    co = {SH.BANG_O[o][0] for o in SH.O_TANG_A}
    assert co == geometry_obligation_kinds(), co ^ geometry_obligation_kinds()


def test_o_tang_B_KHONG_gan_nghia_vu(SH):
    """Ô B chấm bằng *"có từ chối trung thực không"*, không bằng nghĩa vụ. Gán
    nghĩa vụ cho nó là mời người đọc cộng hai thang vào một cột."""
    assert all(SH.BANG_O[o][0] is None for o in SH.O_TANG_B)


def test_seed_KHONG_co_mac_dinh(SH):
    """Tôi chọn được seed thì tôi chọn được cả tập: chạy thử vài seed rồi lấy
    cái cho điểm đẹp nhất."""
    src = (GOC / "backend" / "scripts" / "seal_geometry_holdout.py").read_text(
        encoding="utf-8")
    assert '"--seed", type=int, required=True' in src
    assert "default=42" not in src and "seed or " not in src


def test_moi_o_rut_DOC_LAP_voi_o_khac(SH, tmp_path, monkeypatch):
    """Thêm bài vào ô A11 KHÔNG được làm đổi bài đã rút ở ô A12.

    Một `Random` dùng chung thì thứ tự tiêu số làm mọi ô sau nó trượt hết — và
    "pool lớn thêm một bài" sẽ lặng lẽ thay 19 bài của tập đo.
    """
    def rut(pool):
        theo = {}
        for c in pool:
            theo.setdefault(c["slot"], []).append(c)
        from random import Random
        return {o: Random(f"7:{o}").choice(
            sorted(theo[o], key=lambda c: c["case_id"]))["case_id"]
            for o in theo}

    pool = [_bai(case_id=f"a11_{i}", slot="A11") for i in range(4)]
    pool += [_bai(case_id=f"a12_{i}", slot="A12",
                  expected_obligations=["distance"]) for i in range(4)]
    truoc = rut(pool)
    pool.append(_bai(case_id="a11_9", slot="A11"))
    sau = rut(pool)
    assert truoc["A12"] == sau["A12"], "thêm bài ô A11 làm trượt phép rút ô A12"


# ══ ② ORACLE ĐỘC LẬP — ĐÁP ÁN ĐẾN TỪ NGOÀI, TRA NGƯỢC ĐƯỢC ═══════════════
def test_pool_hop_le_thi_khong_bao_loi(SH):
    assert SH.kiem_pool([_bai()]) == []


@pytest.mark.parametrize("hong,manh", [
    ({"nguon": {"ten": "x", "vi_tri": "Câu 1"}}, "url"),
    ({"dap_an_chinh_thuc": ""}, "dap_an_chinh_thuc"),
    ({"phep_chuyen": ""}, "phep_chuyen"),
    ({"oracle_result": {}}, "oracle_result"),
    ({"chua_chay_he": False}, "chua_chay_he"),
    ({"expected_obligations": ["volume"]}, "nghĩa vụ"),
])
def test_thieu_mot_truong_la_TU_CHOI(SH, hong, manh):
    loi = SH.kiem_pool([_bai(**hong)])
    assert any(manh in d for d in loi), loi


def test_phep_chuyen_bat_buoc_vi_don_vi_checker_KHAC_dap_an_nguon(SH):
    """Đáp án chính thức viết `a√3/3`; checker so phân số. Giấu phép đổi đi thì
    *"oracle độc lập"* chỉ còn là lời khai — không ai kiểm lại được."""
    assert any("phep_chuyen" in d for d in SH.kiem_pool([
        _bai(phep_chuyen=None)]))


def test_o_NGOAI_PHU_khong_duoc_mang_oracle_result(SH):
    """Ô B đo *từ chối trung thực*. Cho nó một đáp án là biến nó thành ô lấy
    điểm, và mất luôn thứ duy nhất nó đo được."""
    b = _bai(case_id="hp_b", slot="B01", expected_obligations=[],
             oracle_result=None, phep_chuyen=None,
             # `PROTOCOL_AMENDMENT_PRESEAL` 2026-08-28: tầng B đổi từ "phải có
             # `dap_an_chinh_thuc`" sang "phải chứng minh lời giải TỒN TẠI và
             # TRA ĐƯỢC" — bộ chấm không đọc đáp án nguồn của ô B.
             nguon_loi_giai="nguồn kiểm thử · trang 1, Câu 1",
             ly_do_ngoai_phu="measure chưa nối distance đường–đường")
    assert SH.kiem_pool([b]) == []
    xau = dict(b, oracle_result={"distance": "1/2"})
    assert any("NGOÀI phủ" in d for d in SH.kiem_pool([xau]))


def test_o_NGOAI_PHU_phai_ghi_LY_DO(SH):
    b = _bai(case_id="hp_b", slot="B01", expected_obligations=[],
             oracle_result=None, phep_chuyen=None)
    assert any("ly_do_ngoai_phu" in d for d in SH.kiem_pool([b]))


# ══ ③ KHÔNG DÙNG LẠI DEV ═════════════════════════════════════════════════
def test_de_TRUNG_DEV_bi_chan(SH):
    """Bốn wave đã sửa hệ theo đúng những đề này. Để lọt một bài DEV vào
    held-out là tự cho điểm ở chỗ mình đã ôn."""
    dev = json.loads((GEO / "dev" / "cases.json").read_text(encoding="utf-8"))
    de = dev["cases"][0]["problem_text"]
    assert any("TRÙNG tập DEV" in d
               for d in SH.kiem_pool([_bai(problem_text=de)]))


def test_chan_ca_khi_chi_khac_KHOANG_TRANG_va_HOA_THUONG(SH):
    """Chép lại đề rồi sửa một dấu cách không làm nó thành bài mới."""
    dev = json.loads((GEO / "dev" / "cases.json").read_text(encoding="utf-8"))
    de = dev["cases"][0]["problem_text"]
    doi = ("  " + de.upper().replace(" ", "  ") + "\n")
    assert any("TRÙNG tập DEV" in d for d in SH.kiem_pool([_bai(problem_text=doi)]))


# ══ ④ HỆ KHÔNG ĐƯỢC ĐỔI GIỮA NIÊM PHONG VÀ CHẠY ══════════════════════════
def test_con_dau_ghi_bam_HE_THONG_chu_khong_chi_tap_de(SH):
    """*"Không sửa hợp đồng theo từng bài"* mà chỉ là lời hứa thì không kiểm
    được. Ghi băm hệ vào con dấu biến nó thành thứ máy đối chiếu được."""
    src = (GOC / "backend" / "scripts" / "seal_geometry_holdout.py").read_text(
        encoding="utf-8")
    assert '"measured_system_hash": he_hash' in src


def test_bam_he_thong_MUON_dung_ham_cua_cong_dong_bang(SH):
    """Hai con số phải không bao giờ trôi khỏi nhau — nên chỉ được có MỘT hàm
    băm, và nó thuộc về cổng đóng băng."""
    fz = _nap("freeze_evaluation_candidate")
    assert SH._bam_he_thong() == fz.measured_system_hash()


def test_runner_TU_CHOI_chay_held_out_khi_he_da_doi(monkeypatch, tmp_path):
    R = _nap("run_geometry_dev_evaluation")
    seal = tmp_path / "HOLDOUT_SEAL.json"
    cases = [_bai()]
    SH = _nap("seal_geometry_holdout")
    seal.write_text(json.dumps({
        "seed": 7, "nguon_seed": "GVHD", "niem_phong_luc": "2026-08-25T00:00:00Z",
        "seal_hash": SH._bam(cases),
        "measured_system_hash": "0" * 64, "measured_system_files": 1,
    }, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(R, "HOLDOUT_SEAL", seal)

    with pytest.raises(R.DungSach) as e:
        R._kiem_con_dau(cases)
    assert "HỆ ĐÃ ĐỔI SAU KHI NIÊM PHONG" in str(e.value)


def test_runner_TU_CHOI_khi_TAP_DE_bi_doi(monkeypatch, tmp_path):
    R = _nap("run_geometry_dev_evaluation")
    SH = _nap("seal_geometry_holdout")
    seal = tmp_path / "HOLDOUT_SEAL.json"
    seal.write_text(json.dumps({
        "seal_hash": SH._bam([_bai()]),
        "measured_system_hash": SH._bam_he_thong()[0],
    }, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(R, "HOLDOUT_SEAL", seal)

    with pytest.raises(R.DungSach) as e:
        R._kiem_con_dau([_bai(case_id="da_bi_doi")])
    assert "TẬP ĐỀ LỆCH CON DẤU" in str(e.value)


def test_khong_co_con_dau_thi_KHONG_chay_duoc(monkeypatch, tmp_path):
    R = _nap("run_geometry_dev_evaluation")
    monkeypatch.setattr(R, "HOLDOUT_SEAL", tmp_path / "khong-co.json")
    with pytest.raises(R.DungSach):
        R._kiem_con_dau([_bai()])


# ══ NGÂN SÁCH DẪN THEO SỐ BÀI ════════════════════════════════════════════
def test_tran_n10_van_dung_60_80_nhu_da_duyet():
    """20 bài cần trần gấp đôi, nhưng trần ĐÃ DUYỆT cho DEV không được đổi một
    đơn vị — nếu không thì "cùng ngân sách" trong báo cáo là sai."""
    R = _nap("run_geometry_dev_evaluation")
    assert R.TRAN_LOGIC_MOI_CASE * 10 == 60
    assert R.TRAN_HTTP_MOI_CASE * 10 == 80
    assert R.TRAN_LOGIC_MOI_CASE * 20 == 120


def test_ket_qua_held_out_KHONG_ghi_de_len_dev_results():
    """Ghi đè `dev-results/` là mất một baseline không lấy lại được."""
    R = _nap("run_geometry_dev_evaluation")
    assert R.HOLDOUT.parent.name == "holdout"


# ══ KHUÔN POOL ═══════════════════════════════════════════════════════════
def test_khuon_pool_ton_tai_va_KHONG_the_dung_lam_pool_that(SH):
    """Khuôn phải đọc được, và phải KHÔNG rút được — nếu ai đó đổi tên nó thành
    `pool.json` thì phép rút phải dừng, không được im lặng rút 2 bài."""
    khuon = json.loads((GEO / "holdout" / "pool.template.json").read_text(
        encoding="utf-8"))
    cases = khuon["cases"]
    assert {c["slot"] for c in cases} < set(SH.BANG_O), "khuôn không được phủ đủ ô"
    assert len(cases) < 20
