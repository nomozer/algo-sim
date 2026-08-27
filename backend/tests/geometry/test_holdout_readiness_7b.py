# -*- coding: utf-8 -*-
"""PHASE 7B-prep — TẬP HELD-OUT ĐÃ SẴN SÀNG NHẬN ĐỀ CHƯA? **0 API call.**

Không kiểm hệ, không kiểm mô hình. Kiểm **hạ tầng của lượt đo**: schema pool,
ma trận độ phủ, và cổng thẩm định kỳ vọng.

VÌ SAO ĐÁNG CÓ TEST RIÊNG: ba thứ trên chỉ chạy **một lần trong đời**, ngay
trước lượt held-out duy nhất. Một lỗi ở đó không có lượt thứ hai để lộ ra — nó
đi thẳng vào luận văn. Cùng lý do mà `HOLDOUT_PROTOCOL §2` nói ba trong bốn bảo
đảm *"không kiểm lại được sau khi chạy"*, nên phải đỏ được từ trước.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[3]
SCRIPTS = GOC / "backend" / "scripts"
GEO = GOC / "docs" / "evaluation" / "geometry"
POOL = GEO / "holdout" / "pool.json"
KY_VONG = GEO / "expectations"


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(ten, SCRIPTS / f"{ten}.py")
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[ten] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def GE():
    return _nap("geometry_expectations")


@pytest.fixture(scope="module")
def MT():
    return _nap("holdout_coverage_matrix")


@pytest.fixture(scope="module")
def SH():
    return _nap("seal_geometry_holdout")


@pytest.fixture(scope="module")
def POOL_D():
    return json.loads(POOL.read_text(encoding="utf-8"))


# ══ TASK 1 — POOL SCHEMA, RỖNG VÀ THỪA NHẬN LÀ RỖNG ══════════════════════
def test_pool_ton_tai_va_RONG(POOL_D):
    """Rỗng là trạng thái ĐÚNG lúc này. Có bài trong đây mà không ai soạn từ
    nguồn ngoài thì đó là bài giả, và một bài giả đủ để giết cả lượt đo."""
    assert POOL_D["cases"] == [], "pool phải rỗng cho tới khi có đề từ nguồn ngoài"
    assert POOL_D["__trang_thai__"] == "EMPTY"


def test_pool_KHAI_DU_moi_truong_Phase7B_doi(POOL_D):
    """Mười một trường của prompt 7B phải có mặt trong bảng ánh xạ — kể cả
    những trường chỉ đổi tên. Thiếu một dòng là lần soạn sau sẽ bỏ sót nó."""
    can = {"id", "source", "source_url", "problem_text", "domain", "difficulty",
           "geometry_family", "expected_construction_types",
           "expected_verification_types", "answer_available", "evaluator"}
    assert can <= set(POOL_D["__anh_xa_ten_truong__"]), (
        f"thiếu ánh xạ: {sorted(can - set(POOL_D['__anh_xa_ten_truong__']))}")


def test_khuon_mot_bai_NAM_NGOAI_cases(POOL_D):
    """Khuôn tham chiếu không được lọt vào con dấu — nó không phải một bài."""
    assert "__khuon_mot_bai__" in POOL_D
    assert POOL_D["__khuon_mot_bai__"] not in POOL_D["cases"]


def test_khuon_mang_DU_ca_hai_bo_ten(POOL_D):
    """Bộ tên máy đọc (`kiem_pool`) và bộ tên prompt 7B phải cùng có mặt: đổi
    tên trường máy đang đọc là làm chết cả dây niêm phong."""
    k = POOL_D["__khuon_mot_bai__"]
    for truong in ("case_id", "slot", "nguon", "dap_an_chinh_thuc",
                   "phep_chuyen", "oracle_result", "chua_chay_he",
                   "expected_obligations"):
        assert truong in k, f"khuôn thiếu khoá MÁY ĐỌC `{truong}`"
    for truong in ("domain", "difficulty", "geometry_family",
                   "expected_construction_types", "expected_verification_types",
                   "answer_available", "evaluator"):
        assert truong in k, f"khuôn thiếu khoá 7B `{truong}`"


def test_pool_RONG_thi_KHONG_niem_phong_duoc(SH, POOL_D):
    """Cổng thật: rỗng ⇒ không phủ ô nào ⇒ dừng. Không có con dấu nào ra đời."""
    assert SH.kiem_pool(POOL_D["cases"]) == [], "pool rỗng không có lỗi ĐỀ"
    theo_o = {}
    for c in POOL_D["cases"]:
        theo_o.setdefault(c["slot"], []).append(c)
    assert [o for o in SH.BANG_O if not theo_o.get(o)] == list(SH.BANG_O), (
        "pool rỗng phải để TRỐNG cả 20 ô")


def test_con_dau_CHUA_ton_tai():
    """Có con dấu mà chưa có đề nghĩa là ai đó đã niêm phong một tập rỗng."""
    assert not (GEO / "holdout" / "HOLDOUT_SEAL.json").exists()
    assert not (GEO / "holdout" / "cases.json").exists()


# ══ TASK 2 — MA TRẬN ĐỘ PHỦ ══════════════════════════════════════════════
def test_moi_o_cua_BANG_O_deu_duoc_anh_xa(MT, SH):
    """Ô không có ánh xạ sẽ **biến mất** khỏi bảng độ phủ, và thiếu một ô là
    thứ không ai nhận ra cho tới lúc rút."""
    assert set(MT.O_HO) == set(SH.BANG_O)


def test_bay_ho_cua_prompt_7B_deu_co_mat(MT):
    can = {"point_construction", "line_relation", "plane_construction",
           "intersection", "solid_geometry", "measurement", "proof_verification"}
    assert set(MT.HO) == can


def test_so_o_tang_A_van_la_14(MT, SH):
    a = [o for o in MT.O_HO if o.startswith("A")]
    assert len(a) == 14 and len(SH.O_TANG_A) == 14


def test_ma_tran_bao_dung_pool_RONG(MT):
    m = MT.ma_tran([])
    assert m["so_bai"] == 0
    assert len(m["o_trong"]) == 20


def test_ma_tran_DEM_DUNG_khi_co_bai(MT):
    """Tiêm bài giả **trong bộ nhớ** để chứng minh bộ đếm đỏ được — guard chưa
    từng đổi màu là guard chưa được chứng minh."""
    m = MT.ma_tran([{"case_id": "x1", "slot": "A11"},
                    {"case_id": "x2", "slot": "A11"},
                    {"case_id": "x3", "slot": "A01"}])
    assert m["so_bai"] == 3
    assert len(m["theo_o"]["A11"]) == 2
    assert "A11" not in m["o_trong"] and "A02" in m["o_trong"]
    assert m["theo_ho"]["measurement"]["so_bai"] == 2


def test_ma_tran_BAT_slot_la(MT):
    m = MT.ma_tran([{"case_id": "x", "slot": "Z99"}])
    assert m["slot_la"] == ["x"]


def test_phat_hien_hai_cho_KHONG_KHIT_duoc_DAN_TU_ANH_XA(MT):
    """Hai phát hiện của §4 phải **dẫn từ ánh xạ**, không chép tay — chép tay
    thì lần đổi `BANG_O` sau sẽ để lại một đoạn văn nói sai."""
    m = MT.ma_tran([])
    assert m["ho_khong_co_o_tang_a"] == ["proof_verification"]
    assert m["o_khong_thuoc_ho"] == ["B04"]


def test_bao_cao_ma_tran_da_sinh_va_khop_anh_xa(MT):
    f = GEO / "holdout" / "COVERAGE_MATRIX.md"
    assert f.exists(), "chưa sinh COVERAGE_MATRIX.md"
    src = f.read_text(encoding="utf-8")
    for h in MT.HO:
        assert h in src
    assert "0/20 ô" in src and "CHƯA RÚT ĐƯỢC" in src


# ══ TASK 3 — CỔNG THẨM ĐỊNH KỲ VỌNG ══════════════════════════════════════
def _ky_vong_holdout(**doi) -> dict:
    """Một tập kỳ vọng held-out TỐI THIỂU HỢP LỆ, để các test bẻ từng mảnh."""
    d = {
        "dataset": "geometry_expectation_set", "tap": "holdout", "version": 1,
        "nguoi_danh_gia": {"loai": "de_thi_cong_khai", "ai": "lời giải chính thức"},
        "sinh_tu_model_output": False,
        "cases": [{
            "case_id": "hp_a11_001", "slot": "A11",
            "problem_text": "Cho hình chóp…",
            "construction_obligations": [],
            "verification_obligations": [
                {"kind": "distance", "ly_do": "đề hỏi khoảng cách điểm đến mặt"}],
            "oracle_ref": {"pool_case_id": "hp_a11_001", "khoa": "distance"},
        }],
    }
    d.update(doi)
    return d


def _nap_tam(GE, tmp_path, d: dict):
    (tmp_path / f"{d['tap']}.json").write_text(
        json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return GE.nap(d["tap"], thu_muc=tmp_path)


def test_holdout_hop_le_thi_nap_duoc(GE, tmp_path):
    assert _nap_tam(GE, tmp_path, _ky_vong_holdout())["tap"] == "holdout"


def test_tang_A_THIEU_oracle_ref_bi_TU_CHOI(GE, tmp_path):
    """Nghĩa vụ không nối được tới đáp án thì `verification_match` đúng cũng
    không chứng minh được mô phỏng đúng — hai câu hỏi khác nhau."""
    d = _ky_vong_holdout()
    del d["cases"][0]["oracle_ref"]
    with pytest.raises(ValueError, match="tầng A phải có `oracle_ref`"):
        _nap_tam(GE, tmp_path, d)


@pytest.mark.parametrize("khoa", ["pool_case_id", "khoa"])
def test_oracle_ref_THIEU_MOT_KHOA_bi_TU_CHOI(GE, tmp_path, khoa):
    d = _ky_vong_holdout()
    del d["cases"][0]["oracle_ref"][khoa]
    with pytest.raises(ValueError, match=f"`oracle_ref` thiếu `{khoa}`"):
        _nap_tam(GE, tmp_path, d)


def test_THIEU_slot_bi_TU_CHOI(GE, tmp_path):
    d = _ky_vong_holdout()
    del d["cases"][0]["slot"]
    with pytest.raises(ValueError, match="thiếu `slot`"):
        _nap_tam(GE, tmp_path, d)


def test_o_B_CAM_mang_oracle_ref(GE, tmp_path):
    """Cùng luật `kiem_pool` áp cho `oracle_result`, chỉ ở đầu kia: ô B chấm
    bằng 'từ chối trung thực', chấm nó bằng đáp án là trộn hai thang."""
    d = _ky_vong_holdout()
    d["cases"][0].update(slot="B03", ghi_chu_kiem="chấm bằng từ chối trung thực")
    with pytest.raises(ValueError, match="không được có `oracle_ref`"):
        _nap_tam(GE, tmp_path, d)


def test_o_B_phai_ghi_VI_SAO_cham_bang_thang_khac(GE, tmp_path):
    d = _ky_vong_holdout()
    d["cases"][0].update(slot="B03")
    del d["cases"][0]["oracle_ref"]
    with pytest.raises(ValueError, match="phải ghi `ghi_chu_kiem`"):
        _nap_tam(GE, tmp_path, d)


def test_o_B_hop_le_thi_qua(GE, tmp_path):
    d = _ky_vong_holdout()
    d["cases"][0].update(slot="B03", ghi_chu_kiem="ngoài phủ — chấm từ chối")
    del d["cases"][0]["oracle_ref"]
    assert _nap_tam(GE, tmp_path, d)["cases"][0]["slot"] == "B03"


def test_PILOT_KHONG_bi_doi_oracle_ref(GE):
    """Hồi quy: luật oracle chỉ áp cho tập ngoài `pilot`. Pilot chấm BỘ ĐO và
    oracle của nó nằm trong runner, không nằm trong pool."""
    d = GE.nap("pilot")
    assert all("oracle_ref" not in c for c in d["cases"])


# ── nối con trỏ oracle sang pool ─────────────────────────────────────────
def _pool_case(**doi) -> dict:
    c = {"case_id": "hp_a11_001", "slot": "A11", "problem_text": "Cho hình chóp…",
         "oracle_result": {"distance": "1/3"}}
    c.update(doi)
    return c


def test_noi_oracle_KHOP_thi_khong_bao_loi(GE):
    assert GE.kiem_noi_oracle(_ky_vong_holdout(), [_pool_case()]) == []


def test_con_tro_TRO_VAO_HU_KHONG_bi_bat(GE):
    loi = GE.kiem_noi_oracle(_ky_vong_holdout(),
                             [_pool_case(case_id="hp_a11_999")])
    assert loi and "không có trong pool" in loi[0]


def test_con_tro_SAI_KHOA_bi_bat(GE):
    loi = GE.kiem_noi_oracle(
        _ky_vong_holdout(), [_pool_case(oracle_result={"volume": "12"})])
    assert loi and "không có khoá" in loi[0]


def test_DE_LECH_giua_hai_file_bi_bat(GE):
    """Hai file chép cùng một đề. Lệch một chữ nghĩa là một bản đã bị sửa, và
    sau khi niêm phong thì không còn biết bản nào."""
    loi = GE.kiem_noi_oracle(_ky_vong_holdout(),
                             [_pool_case(problem_text="Cho hình chóp… (đã sửa)")])
    assert loi and "LỆCH với pool" in loi[0]


# ══ KHUÔN KHÔNG ĐƯỢC DÙNG LÀM TẬP THẬT ═══════════════════════════════════
def test_khuon_ky_vong_ton_tai_va_KHONG_the_nap_lam_tap_that(GE, tmp_path):
    khuon = json.loads(
        (KY_VONG / "holdout.template.json").read_text(encoding="utf-8"))
    assert "<" in json.dumps(khuon, ensure_ascii=False), "khuôn phải còn chỗ trống"
    d = copy.deepcopy(khuon)
    d["tap"] = "holdout"
    # Khuôn mang `<…>` ở `case_id`/`problem_text` nên nạp được về mặt kiểu,
    # nhưng con trỏ oracle của nó KHÔNG trỏ vào pool nào có thật.
    assert GE.kiem_noi_oracle(d, []), "khuôn không được coi là tập đã nối oracle"


def test_chua_co_tap_ky_vong_held_out_that():
    assert not (KY_VONG / "holdout.json").exists(), (
        "có holdout.json nghĩa là ai đó đã soạn kỳ vọng — kiểm nguồn trước khi đo")
