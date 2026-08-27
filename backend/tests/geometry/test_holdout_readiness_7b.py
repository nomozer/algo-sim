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
import re
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
def test_moi_bai_trong_pool_deu_CO_NGUON_NGOAI(POOL_D):
    """Không bài giả. Mỗi bài phải tra ngược được về một url — đó là toàn bộ
    thứ phân biệt một tập held-out với một tập tôi tự soạn."""
    for c in POOL_D["cases"]:
        n = c.get("nguon") or {}
        assert n.get("url", "").startswith("http"), f"{c['case_id']}: thiếu url"
        assert c.get("dap_an_chinh_thuc"), f"{c['case_id']}: thiếu đáp án nguồn"
        assert c.get("evaluator"), f"{c['case_id']}: chưa khai ai ra đáp án"
        assert c.get("chua_chay_he") is True, f"{c['case_id']}: chua_chay_he"


def test_pool_TU_KHAI_dung_so_bai_theo_TUNG_TRANG_THAI(POOL_D):
    """Nhãn trạng thái là thứ người đọc tin trước khi chạy lệnh nào. Nó trôi
    khỏi `cases` là nói dối về mức sẵn sàng.

    Kiểm theo **từng trạng thái**, không kiểm tổng: một pool 40 bài mà 40 bài
    đều `rejected` thì con số tổng nói đúng mà nghĩa thì sai hoàn toàn.
    """
    nhan = POOL_D["__trang_thai__"]
    dem: dict[str, int] = {}
    for c in POOL_D["cases"]:
        tt = c.get("status", "accepted")
        dem[tt] = dem.get(tt, 0) + 1
    assert f"{dem.get('accepted', 0)} accepted" in nhan, (
        f"nhãn không khai đúng số bài accepted: {nhan!r}")
    for tt, n in dem.items():
        if tt != "accepted":
            assert f"{n} {tt}" in nhan, f"nhãn thiếu `{n} {tt}`"


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


def test_pool_CHUA_DU_thi_KHONG_niem_phong_duoc(SH, POOL_D):
    """Cổng thật: thiếu ô ⇒ dừng. Không có con dấu nào ra đời."""
    theo_o: dict[str, list] = {}
    for c in POOL_D["cases"]:
        theo_o.setdefault(c["slot"], []).append(c)
    thieu = [o for o in SH.BANG_O if not theo_o.get(o)]
    assert thieu, "pool đã phủ đủ 20 ô — cập nhật test này khi thật sự tới đó"


def test_bai_CHUA_DOI_CHIEU_TAY_thi_bi_chan(SH):
    """`can_kiem_tay` là NỢ ĐỐI CHIẾU, không phải ghi chú.

    Đề thu thập bằng công cụ đọc web đi qua một mô hình tóm tắt, nên
    `problem_text` là bản chép LẠI. Giao thức đòi chép NGUYÊN VĂN, và một chữ
    sai trong đề làm bài toán thành bài KHÁC — sau khi niêm phong thì không sửa
    được nữa.
    """
    goc = {"case_id": "x", "slot": "A11", "problem_text": "đề",
           "nguon": {"url": "https://x"}, "dap_an_chinh_thuc": "1",
           "phep_chuyen": "…", "oracle_result": {"distance": "1"},
           "expected_obligations": ["distance"], "chua_chay_he": True}
    assert SH.kiem_pool([goc]) == [], "bài không mang cờ thì phải qua"
    loi = SH.kiem_pool([{**goc, "can_kiem_tay": True}])
    assert loi and "can_kiem_tay" in loi[0]


def test_pool_HIEN_TAI_khong_co_loi_nao(SH, POOL_D):
    """Trạng thái thật lúc này: bài duy nhất mang `status` ngoài `accepted` nên
    không bị kiểm như bài thật. Test đổi màu khi thêm bài `accepted` hỏng."""
    assert SH.kiem_pool(POOL_D["cases"]) == []


# ══ PHASE 7A.5 — RANH GIỚI NĂNG LỰC ══════════════════════════════════════
_BOUNDARY = GEO / "CAPABILITY_BOUNDARY.md"
_REVIEW = GEO / "COVERAGE_MATRIX_BOUNDARY_REVIEW.md"


def test_tai_lieu_ranh_gioi_ton_tai_va_KHAI_ca_hai_phia():
    for f in (_BOUNDARY, _REVIEW):
        assert f.exists(), f"chưa có {f.name}"
    src = _BOUNDARY.read_text(encoding="utf-8")
    assert "## 1. SUPPORTED" in src and "## 2. UNSUPPORTED" in src
    # Luật đọc quan trọng nhất của cả tài liệu — bỏ nó đi thì tài liệu thành
    # một danh sách tính năng, và Phase 7B lại kết tội mô hình ở chỗ nó đúng.
    assert "lỗi của mô hình" in src
    assert src.lower().count("không phải lỗi ai") >= 5, (
        "mỗi mục UNSUPPORTED phải tự khai điều này, không chỉ nói một lần ở đầu")


@pytest.mark.parametrize("muc", [
    "GEOMETRY_IRRATIONAL_RESULT",      # §2.1 distance vô tỉ
    "a√3",                             # §2.2 tỉ số dữ kiện vô tỉ
    "distance_sq_skew_lines",          # §2.3 kernel có, IR chưa nối
    "nhị diện",                        # §2.4
    "GEOMETRY_CURRICULUM_COVERAGE",    # §2.6 mặt cong
])
def test_UNSUPPORTED_neu_du_cac_lop_da_biet(muc):
    assert muc in _BOUNDARY.read_text(encoding="utf-8"), f"thiếu lớp `{muc}`"


def test_bay_SIN_BINH_cua_o_A10_duoc_ghi_o_CA_HAI_tai_lieu():
    """Bẫy im lặng nhất: khai nhầm cos² cho ô A10 thì chấm sai mà không cổng
    nào báo. Ghi một chỗ là chưa đủ — người soạn pool đọc `REVIEW`, người soạn
    oracle đọc `BOUNDARY`."""
    for f in (_BOUNDARY, _REVIEW):
        assert "sin²" in f.read_text(encoding="utf-8"), f"{f.name} thiếu cảnh báo"


def test_protocol_khai_DIEU_KIEN_NHAN_BAI_tang_A():
    src = (GEO / "HOLDOUT_PROTOCOL.md").read_text(encoding="utf-8")
    assert "## 2b." in src
    doan = src.split("## 2b.")[1].split("## 3.")[0]
    assert "CAPABILITY_BOUNDARY" in doan
    assert "expectation độc lập" in doan
    assert "KHÔNG tự chuyển bài khó xuống tầng B" in doan


# ── status: bài bị loại được GIỮ, nhưng KHÔNG lấp ô ──────────────────────
def _bai(**doi) -> dict:
    c = {"case_id": "x", "slot": "A11", "problem_text": "đề",
         "nguon": {"url": "https://x"}, "dap_an_chinh_thuc": "1",
         "phep_chuyen": "…", "oracle_result": {"distance": "1"},
         "expected_obligations": ["distance"], "chua_chay_he": True}
    c.update(doi)
    return c


def test_status_VANG_MAT_van_duoc_coi_la_accepted(SH):
    """Tương thích ngược: bài soạn trước 7A.5 không phải sửa."""
    assert SH.duoc_rut(_bai()) is True
    assert SH.kiem_pool([_bai()]) == []


def test_bai_BI_LOAI_khong_bi_kiem_nhu_bai_that(SH):
    """Đòi `oracle_result` ở một bài vừa bị loại VÌ không có oracle biểu diễn
    được là một vòng lặp vô nghĩa."""
    b = _bai(status="rejected_capability_boundary", reason="vô tỉ")
    del b["oracle_result"], b["phep_chuyen"]
    assert SH.kiem_pool([b]) == []
    assert SH.duoc_rut(b) is False


def test_bai_BI_LOAI_ma_KHONG_neu_ly_do_thi_DO(SH):
    loi = SH.kiem_pool([_bai(status="rejected_capability_boundary")])
    assert loi and "loại im lặng" in loi[0]


def test_bai_BI_LOAI_van_phai_giu_URL(SH):
    b = _bai(status="rejected_capability_boundary", reason="vô tỉ", nguon={})
    loi = SH.kiem_pool([b])
    assert loi and "tra ngược" in loi[0]


def test_status_LA_thi_DO(SH):
    loi = SH.kiem_pool([_bai(status="hong")])
    assert loi and "không hợp lệ" in loi[0]


def test_bai_BI_LOAI_KHONG_lap_o_trong_ma_tran(MT):
    """Cốt lõi của 7A.5: giữ bài để tra ngược, nhưng ô vẫn phải hiện là TRỐNG.
    Đếm nó vào độ phủ là nói dối về mức sẵn sàng."""
    m = MT.ma_tran([{"case_id": "x", "slot": "A11",
                     "status": "rejected_capability_boundary"}])
    assert m["so_bai"] == 0 and m["so_bi_loai"] == 1
    assert "A11" in m["o_trong"], "bài bị loại đang lấp ô A11"


def test_pool_THAT_dang_o_dung_trang_thai_ay(POOL_D, MT, SH):
    """Hiện trường thật: `hp_a11_001` nằm trong file, mang `status`, và A11 vẫn
    trống."""
    c = {x["case_id"]: x for x in POOL_D["cases"]}["hp_a11_001"]
    assert c["status"] == "rejected_capability_boundary"
    assert c["reason"] and c["nguon"]["url"]
    assert "oracle_result" not in c, (
        "bài hệ KHÔNG trả ra giá trị nào thì không được khai oracle")
    assert "A11" in MT.ma_tran(POOL_D["cases"])["o_trong"]


def test_capability_tag_cua_moi_bai_deu_co_trong_bang(POOL_D):
    bang = POOL_D["__the_nang_luc__"]
    for c in POOL_D["cases"]:
        t = c.get("capability_tag")
        assert t in bang, f"{c['case_id']}: capability_tag {t!r} ngoài bảng"
        assert c["slot"] in bang[t]["o"], (
            f"{c['case_id']}: tag {t!r} không dùng cho ô {c['slot']}")


# ══ PHASE 7B-prep — check_capability_boundary() ══════════════════════════
def _bai_a14(**doi) -> dict:
    """Bài A14 tối thiểu HỢP LỆ — ô an toàn nhất (volume luôn hữu tỉ)."""
    c = {"case_id": "hp_a14_001", "status": "accepted", "slot": "A14",
         "capability_tag": "rational_volume", "answer_shape": "exact_fraction",
         "problem_text": "đề", "problem_text_original": "đề",
         "problem_text_verified": True, "human_verifier": "Người kiểm thử",
         "nguon": {"url": "https://x"}, "dap_an_chinh_thuc": "4/3",
         "phep_chuyen": "gán a = 2 ⇒ V = 4/3", "oracle_result": {"volume": "4/3"},
         "oracle_ref": "volume",
         "expected_obligations": ["volume"], "chua_chay_he": True}
    c.update(doi)
    return c


def test_bai_HOP_LE_thi_qua_ca_hai_cong(SH):
    b = _bai_a14()
    assert SH.check_capability_boundary(b) == []
    assert SH.kiem_pool([b]) == []


def test_the_nang_luc_KHONG_khop_O_thi_bi_bat(SH):
    """`slot` nói bài nằm ô nào, `capability_tag` nói nó ĐÒI năng lực gì. Ô
    A11 vừa cho thấy hai câu ấy lệch được."""
    loi = SH.check_capability_boundary(_bai_a14(slot="A11"))
    assert loi and "không dùng cho ô" in loi[0]


def test_answer_shape_NGOAI_TAP_DONG_bi_bat(SH):
    for xau in ("float", "rounded", "fraction"):
        loi = SH.check_capability_boundary(_bai_a14(answer_shape=xau))
        assert loi and "ngoài tập đóng" in loi[0], xau


@pytest.mark.parametrize("gt,dau", [
    ("2a³/3", "THAM SỐ"), ("2a^3/3", "THAM SỐ"), ("a³/6", "THAM SỐ"),
    ("a³√2/3", "CĂN THỨC"), ("√2", "CĂN THỨC"),
    ("0.667", "THẬP PHÂN"), ("7,35", "THẬP PHÂN"),
])
def test_BA_CHAN_DOAN_ORACLE_khong_bi_gop(SH, gt, dau):
    """Ba lỗi khác nhau, ba lối sửa khác nhau — gộp chúng là bảo người soạn
    vứt một bài tốt đi.

    Lỗi thật đã có: `2a³/3` và `2a^3/3` từng bị báo *"CĂN THỨC — ngoài ranh
    giới"*. Sai hẳn: bài ấy **trong** ranh giới, chỉ là đáp án còn tham số `a`
    chưa gán. Thông báo cũ đổ cho DỮ LIỆU cái lỗi thuộc về BỘ ĐO — đúng lớp
    sai lệch mà cả wave này đi sửa.
    """
    loi = SH.check_capability_boundary(_bai_a14(oracle_result={"volume": gt}))
    assert loi and dau in loi[0], loi


def test_ORACLE_dang_CAN_THUC_bi_bat(SH):
    """Lách bằng cách viết `3√6` thay vì loại bài — ngoài ranh giới là chuyện
    hệ KHÔNG trả ra giá trị nào, không phải chuyện đổi cách viết."""
    loi = SH.check_capability_boundary(
        _bai_a14(oracle_result={"volume": "3√6"}))
    assert loi and "CĂN THỨC" in loi[0]


def test_ORACLE_so_thap_phan_bi_bat(SH):
    """`7.35` là số đã LÀM TRÒN. Nhận nó là đưa sai số vào chỗ kernel vừa dựng
    bằng `Fraction` để tránh."""
    loi = SH.check_capability_boundary(
        _bai_a14(oracle_result={"volume": "1.3333"}))
    assert loi and "THẬP PHÂN" in loi[0]
    # `7,35` — đúng đáp án nguồn của bài đã bị loại, ở dấu phẩy kiểu Việt Nam.
    assert SH.check_capability_boundary(_bai_a14(oracle_result={"volume": "7,35"}))
    # Và `1/2` thì qua: cấm THẬP PHÂN, không phải cấm số không nguyên.
    assert SH.check_capability_boundary(_bai_a14(oracle_result={"volume": "1/2"})) == []


def test_A10_phai_khai_DIEU_KIEN_MIEN(SH):
    """`angle_sin_sq` chỉ đúng dưới một điều kiện (cặp đường–mặt trả sin²), và
    điều kiện ấy KHÔNG suy ra được từ `slot`."""
    b = _bai_a14(slot="A10", capability_tag="angle_sin_sq",
                 oracle_result={"angle": "1/2"}, expected_obligations=["angle"])
    assert any("domain_condition" in d for d in SH.check_capability_boundary(b))
    b["domain_condition"] = "cặp ĐƯỜNG–MẶT ⇒ engine trả sin², không phải cos²"
    assert SH.check_capability_boundary(b) == []


def test_o_tang_B_phai_mang_the_NGOAI_ranh_gioi(SH):
    b = _bai_a14(slot="B03", capability_tag="out_of_capability",
                 answer_shape="rejection_expected", oracle_result={})
    assert SH.check_capability_boundary(b) == []
    xau = _bai_a14(slot="B03", capability_tag="rational_volume")
    assert SH.check_capability_boundary(xau), "thẻ trong ranh giới lọt vào ô B"


def test_o_tang_A_KHONG_duoc_cham_bang_TU_CHOI(SH):
    """Trộn hai thang là gộp hai câu hỏi khác nhau vào một cột."""
    loi = SH.check_capability_boundary(
        _bai_a14(capability_tag="out_of_capability",
                 answer_shape="rejection_expected"))
    assert loi


def test_o_NGOAI_PHU_khong_duoc_mang_ORACLE(SH):
    loi = SH.check_capability_boundary(
        _bai_a14(slot="B03", capability_tag="out_of_capability",
                 answer_shape="rejection_expected",
                 oracle_result={"distance": "1"}))
    assert loi and "KHÔNG được mang oracle_result" in loi[0]


def test_de_CHUA_DOI_CHIEU_NGUYEN_VAN_thi_KHONG_vao_holdout(SH):
    """Điều kiện của Phase 7B, và là điều kiện KHÔNG kênh tự động nào thoả:
    công cụ đọc web tóm tắt, trích PDF rơi ký hiệu toán."""
    loi = SH.kiem_pool([_bai_a14(problem_text_verified=False)])
    assert loi and "problem_text_verified" in loi[0]


def test_rejected_unverified_la_trang_thai_HOP_LE(SH):
    b = _bai_a14(status="rejected_unverified", reason="không đối chiếu được")
    assert SH.kiem_pool([b]) == [] and SH.duoc_rut(b) is False


def test_bai_KHONG_khai_schema_7A5_van_di_qua(SH):
    """Tương thích ngược: đổi luật dưới chân một tập đã soạn là cách chắc chắn
    nhất để không ai soạn tiếp."""
    cu = {"case_id": "cu", "slot": "A11", "problem_text": "đề",
          "nguon": {"url": "https://x"}, "dap_an_chinh_thuc": "1",
          "phep_chuyen": "…", "oracle_result": {"distance": "1"},
          "expected_obligations": ["distance"], "chua_chay_he": True}
    assert SH.kiem_pool([cu]) == []


# ── con dấu phải mang danh tính ĐẦY ĐỦ ───────────────────────────────────
def test_con_dau_ghi_DU_bay_thanh_phan_danh_tinh(SH):
    """Băm hệ thôi chưa đủ: con dấu phải trả lời được *đo bản nào, bằng thước
    nào, kỳ vọng nào, cỡ mẫu bao nhiêu*."""
    import inspect

    src = inspect.getsource(SH.main)
    for khoa in ("commit", "metric_contract_hash", "capability_boundary_hash",
                 "expectation_hash", "pool_hash", '"k"', '"budget"'):
        assert khoa in src, f"con dấu thiếu `{khoa}`"


def test_k_va_ngan_sach_cua_con_dau_KHOP_K_FINAL(SH):
    assert (SH.K_CHOT, SH.LOGIC_MOI_LUOT, SH.HTTP_MOI_LUOT) == (3, 6, 8)
    assert len(SH.BANG_O) * SH.K_CHOT * SH.LOGIC_MOI_LUOT == 360
    assert len(SH.BANG_O) * SH.K_CHOT * SH.HTTP_MOI_LUOT == 480


def test_bang_NANG_LUC_trong_MA_va_trong_POOL_khong_troi(SH, POOL_D):
    """Hai bảng, một sự thật. `check_capability_boundary` đọc bảng trong mã;
    người soạn đọc bảng trong pool. Lệch là chuyện sẽ xảy ra, nên khoá."""
    bang = POOL_D["__the_nang_luc__"]
    for tag, (o, dang, _) in SH.NANG_LUC.items():
        assert tag in bang, f"pool thiếu thẻ {tag!r}"
        assert tuple(bang[tag]["o"]) == tuple(o), f"{tag}: ô lệch"
        assert bang[tag]["answer_shape"] == dang, f"{tag}: answer_shape lệch"


# ══ BỘ THU ỨNG VIÊN — ba cổng trung thực ═════════════════════════════════
@pytest.fixture(scope="module")
def HV():
    return _nap("harvest_holdout_candidates")


_TRANG = """<html><title>T</title><body>
<h3>Đề bài</h3><div class="math-box"><p>{de}</p></div><h3>Lời giải</h3>
</body></html>"""


def test_thu_duoc_de_NGUYEN_VAN_giu_nguyen_LaTeX(HV):
    """Điểm khác bản chất so với hai kênh đã hỏng: không bước nào diễn giải
    lại, nên không bước nào làm mất ký hiệu."""
    de = r"Cho hình chóp \(S.ABCD\) có \(SA \perp (ABCD)\), \(SA = a\sqrt{3}\)."
    x = HV.soi_mot_trang("https://x/1.html", _TRANG.format(de=de))
    assert x["sach"] is True
    assert r"\perp" in x["problem_text_original"]
    assert r"\sqrt{3}" in x["problem_text_original"]


def test_de_la_ANH_thi_bi_LOAI(HV):
    """Cổng quan trọng nhất: phần lớn nội dung toán trên web tiếng Việt là ảnh
    chụp, và `curl` cũng không đọc được ảnh."""
    x = HV.soi_mot_trang("https://x/2.html", _TRANG.format(
        de='<img src="de.png"> Cho hình chóp \\(S.ABCD\\) có đáy là hình vuông '
           'cạnh \\(a\\), cạnh bên \\(SA\\) vuông góc với mặt phẳng đáy.'))
    assert x["co_anh_trong_de"] is True and x["sach"] is False


def test_KHONG_co_dau_vet_LATEX_thi_KHONG_sach(HV):
    """Hoặc đề không chứa toán, hoặc toán đã mất ở đâu đó — cả hai đều là lý do
    để người đọc soát trước, không phải để nhận thẳng."""
    x = HV.soi_mot_trang("https://x/3.html", _TRANG.format(
        de="Cho hinh chop S.ABCD co day la hinh vuong canh a va SA vuong goc day."))
    assert x["co_latex"] is False and x["sach"] is False


def test_KHONG_tach_duoc_khoi_de_thi_BO_QUA(HV):
    """Không có khối đề tách được thì đang ĐOÁN đâu là đề — bỏ qua, đừng đoán."""
    assert HV.soi_mot_trang("https://x/4.html", "<html><p>lung tung</p></html>") is None


def test_bo_thu_KHONG_ghi_vao_pool():
    """Nó đặt đề lên bàn, không nhận bài. `problem_text_verified` vẫn do người
    hạ — tự động hoá bước ấy là bỏ đúng cái cổng vừa dựng."""
    src = (SCRIPTS / "harvest_holdout_candidates.py").read_text(encoding="utf-8")
    assert "pool.json" not in src.replace("`pool.json`", "")
    assert "problem_text_verified" in src, "phải nhắc rõ giới hạn của nó"


# ══ ĐƯỜNG NẠP LÔ ĐỀ DO NGƯỜI CHÉP ═══════════════════════════════════════
@pytest.fixture(scope="module")
def IN():
    return _nap("ingest_holdout_batch")


_LO = """NGƯỜI CHÉP: Nguyễn Văn A · 2026-08-28 · SGK Toán 11 tập 2 KNTT

[A14] Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, cạnh bên SA
      vuông góc với mặt phẳng đáy và SA = 3. Tính thể tích khối chóp S.ABCD.
      NGUỒN: SGK Toán 11 tập 2 KNTT, bài 7.15 trang 62
      ĐÁP ÁN: 4
"""


def test_lo_HOP_LE_thi_ra_case_qua_duoc_cong(IN, SH):
    nguoi, bai, loi = IN.phan_tich(_LO, SH)
    assert loi == [] and nguoi.startswith("Nguyễn Văn A")
    c = IN.thanh_case(bai[0], nguoi, SH)
    assert SH.check_capability_boundary(c) == []
    assert c["capability_tag"] == "rational_volume"
    assert c["answer_shape"] == "exact_fraction"
    assert c["oracle_result"] == {"volume": "4"}
    assert c["problem_text_verified"] is True


def test_THIEU_dong_NGUOI_CHEP_thi_TU_CHOI(IN, SH):
    """Cổng cốt lõi: không ai chịu trách nhiệm cho việc đề đúng nguyên văn thì
    không lô nào được vào. Mọi kênh tự động đã đo được là hỏng IM LẶNG."""
    _, _, loi = IN.phan_tich(_LO.split("\n", 1)[1], SH)
    assert loi and "NGƯỜI CHÉP" in loi[0]


def test_THIEU_NGUON_thi_TU_CHOI(IN, SH):
    _, _, loi = IN.phan_tich(
        _LO.replace("      NGUỒN: SGK Toán 11 tập 2 KNTT, bài 7.15 trang 62\n", ""),
        SH)
    assert any("NGUỒN" in d for d in loi)


def test_o_tang_A_THIEU_DAP_AN_thi_TU_CHOI(IN, SH):
    _, _, loi = IN.phan_tich(_LO.replace("      ĐÁP ÁN: 4\n", ""), SH)
    assert any("ĐÁP ÁN" in d for d in loi)


def test_o_tang_B_MANG_DAP_AN_thi_TU_CHOI(IN, SH):
    """Tầng B chấm bằng 'từ chối trung thực', chấm nó bằng đáp án là trộn hai
    thang."""
    _, _, loi = IN.phan_tich(_LO.replace("[A14]", "[B03]"), SH)
    assert any("tầng B" in d for d in loi)


@pytest.mark.parametrize("chen,dau", [
    ("Đáp án: A. 12. B. 6. C. 8. D. 4.", "TRẮC NGHIỆM"),
    ("và SA = a√3.", "CĂN THỨC"),
    ("(tham khảo hình vẽ)", "HÌNH VẼ"),
    ("Cho mặt cầu tâm O.", "MẶT CONG"),
    ("Trong không gian Oxyz, cho", "Oxyz"),
])
def test_canh_bao_dung_lop_de_KHONG_hop_luat(IN, SH, chen, dau):
    """Cảnh báo, KHÔNG tự loại: phán quyết cuối là của người, script chỉ chỉ chỗ."""
    _, bai, _ = IN.phan_tich(_LO.replace("Tính thể tích", chen + " Tính thể tích"), SH)
    assert any(dau in cb for cb in bai[0]["canh_bao"]), bai[0]["canh_bao"]


def test_ORACLE_dang_can_thuc_bi_CONG_chan(IN, SH):
    """Người chép đúng nguyên văn một đáp án CĂN THỨC vẫn bị chặn ở cổng sau —
    hai cổng, hai câu hỏi khác nhau."""
    nguoi, bai, loi = IN.phan_tich(_LO.replace("ĐÁP ÁN: 4", "ĐÁP ÁN: 4√3"), SH)
    assert loi == []
    c = IN.thanh_case(bai[0], nguoi, SH)
    assert any("CĂN THỨC" in d for d in SH.check_capability_boundary(c))


@pytest.mark.parametrize("cho_trong", ["<tên người chép>", "TODO",
                                       "<…> · <ngày>"])
def test_NGUOI_CHEP_con_CHO_TRONG_thi_TU_CHOI(IN, SH, cho_trong):
    """Một chứng nhận xác minh mang tên `<tên người chép>` thì không chứng nhận
    gì cả. Khuôn `batch_001.txt` mang sẵn chỗ trống, nên lỗ này là có thật."""
    _, _, loi = IN.phan_tich(
        _LO.replace("Nguyễn Văn A · 2026-08-28 · SGK Toán 11 tập 2 KNTT",
                    cho_trong), SH)
    assert loi and "CHỖ TRỐNG" in loi[0]


def test_dau_BA_CHAM_trong_de_THAT_khong_bi_coi_la_cho_trong(IN, SH):
    """Guard từng bắt nhầm `…`, và `…` xuất hiện hợp lệ trong đề thật. Từ chối
    dữ liệu ĐÚNG là đúng lớp lỗi "đổ cho dữ liệu cái lỗi của bộ đo"."""
    _, _, loi = IN.phan_tich(
        _LO.replace("Tính thể tích khối chóp S.ABCD.",
                    "Tính thể tích khối chóp S.ABCD… (làm tròn nếu cần)."), SH)
    assert loi == [], loi


@pytest.mark.parametrize("truong,dong_cu", [
    ("NGUỒN", "      NGUỒN: SGK Toán 11 tập 2 KNTT, bài 7.15 trang 62"),
    ("ĐÁP ÁN", "      ĐÁP ÁN: 4")])
def test_TRUONG_con_CHO_TRONG_thi_TU_CHOI(IN, SH, truong, dong_cu):
    """Thay cả DÒNG, không thay giá trị: thay `"4"` thì `[A14]` cũng thành
    `[A1<…>]` và mốc bài gãy — test đỏ vì lý do khác cái nó định kiểm."""
    _, _, loi = IN.phan_tich(
        _LO.replace(dong_cu, f"      {truong}: <…>"), SH)
    assert any("CHỖ TRỐNG" in d and truong in d for d in loi), loi


def test_dong_CHU_THICH_khong_bi_nuot_vao_DE_BAI(IN, SH):
    """Lỗi thật, bắt được khi chạy khuôn: khối hướng dẫn ở cuối file bị nuốt
    vào đề của bài CUỐI CÙNG. Đề dài ngoằng ấy vẫn qua mọi cổng về mặt kiểu,
    rồi vào tập đã niêm phong."""
    _, bai, _ = IN.phan_tich(_LO + "\n# Xong thì chạy: ingest --ghi\n# hết\n", SH)
    assert "#" not in bai[0]["de"] and "ingest" not in bai[0]["de"]


def test_KHUNG_batch_001_ton_tai_va_KHONG_the_nap_duoc(IN, SH):
    """Khung phải nằm sẵn ở chỗ giao thức chỉ, nhưng **không** nạp được chừng
    nào còn chỗ trống — nếu không thì nó là một lô đề giả."""
    f = GEO / "holdout" / "batch_001.txt"
    assert f.exists(), "chưa có khung batch_001.txt"
    _, _, loi = IN.phan_tich(f.read_text(encoding="utf-8"), SH)
    assert loi, "khung chưa điền mà nạp được — cổng xác minh thành ô trống"
    assert any("NGƯỜI CHÉP" in d for d in loi)


def test_bo_nap_KHONG_tu_viet_dong_NGUOI_CHEP():
    """Tôi tự viết dòng ấy là tự cấp cho mình một chứng nhận không có tư cách
    cấp. Docstring phải nói thẳng điều đó."""
    src = (SCRIPTS / "ingest_holdout_batch.py").read_text(encoding="utf-8")
    assert "do NGƯỜI viết" in src and "không có tư cách cấp" in src


# ══ LUỒNG ĐẦU-CUỐI — chứng minh từng chặng NỐI ĐƯỢC ══════════════════════
#
# VÌ SAO CẦN: sáu chặng (nguồn → pool → ranh giới → oracle → độ phủ → con dấu)
# đều có test riêng, nhưng **chưa chặng nào chạy nối vào chặng kia** — pool thật
# rỗng nên luồng chưa từng chạy trọn một lần. Một luồng chưa từng chạy trọn là
# một luồng chưa được chứng minh, và chỗ nó gãy sẽ lộ ra đúng lúc có dữ liệu
# thật, tức đúng lúc đắt nhất.
#
# Lô ở đây là lô GIẢ, sống trong `tmp_path`, KHÔNG chạm `pool.json` thật.
_LO_E2E = """NGƯỜI CHÉP: Người kiểm thử · 2026-08-28 · fixture của test

[A14] Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, cạnh bên SA
      vuông góc với mặt phẳng đáy và SA = 3. Tính thể tích khối chóp S.ABCD.
      NGUỒN: fixture · bài 1
      ĐÁP ÁN: 4

[A09] Cho hình lập phương ABCD.A'B'C'D'. Tính góc giữa hai đường thẳng AB và
      B'C', biểu diễn kết quả bằng bình phương cosin của góc ấy.
      NGUỒN: fixture · bài 2
      ĐÁP ÁN: 0
"""


def test_luong_DAU_CUOI_noi_duoc(IN, SH, MT, tmp_path):
    """Sáu chặng, chạy nối nhau một lần."""
    # ① nguồn → lô
    nguoi, bai, loi = IN.phan_tich(_LO_E2E, SH)
    assert loi == [], loi
    assert [b["o"] for b in bai] == ["A14", "A09"]

    # ② lô → case
    cases = [IN.thanh_case(b, nguoi, SH) for b in bai]
    assert all(c["problem_text_verified"] for c in cases)

    # ③ ranh giới năng lực
    assert [d for c in cases for d in SH.check_capability_boundary(c)] == []

    # ④ oracle đúng đơn vị — dẫn từ thẻ, không chép tay
    assert cases[0]["oracle_result"] == {"volume": "4"}
    assert cases[1]["oracle_result"] == {"angle": "0"}

    # ⑤ pool → độ phủ
    assert SH.kiem_pool(cases) == []
    m = MT.ma_tran(cases)
    assert m["so_bai"] == 2
    assert "A14" not in m["o_trong"] and "A09" not in m["o_trong"]

    # ⑥ con dấu VẪN từ chối — 18 ô còn trống. Đây là chặng cuối, và nó phải
    #    nói KHÔNG, nếu không thì 2 bài cũng niêm phong được.
    assert len(m["o_trong"]) == 18


def test_luong_DAU_CUOI_DO_DUOC_o_tung_chang(IN, SH, tmp_path):
    """Tiêm lỗi vào từng chặng — guard chưa từng đỏ là guard chưa được chứng
    minh (`ARCHITECTURE_MAP §8` #14)."""
    # chặng ①: mất chữ ký người chép
    assert IN.phan_tich(_LO_E2E.split("\n", 1)[1], SH)[2]

    # chặng ③: đề đúng, nhưng oracle là CĂN THỨC ⇒ ngoài ranh giới
    nguoi, bai, _ = IN.phan_tich(_LO_E2E.replace("ĐÁP ÁN: 4", "ĐÁP ÁN: 2√3"), SH)
    assert any("CĂN THỨC" in d
               for d in SH.check_capability_boundary(
                   IN.thanh_case(bai[0], nguoi, SH)))

    # chặng ③: thẻ đúng, ô sai
    nguoi, bai, _ = IN.phan_tich(_LO_E2E, SH)
    c = IN.thanh_case(bai[0], nguoi, SH)
    assert SH.check_capability_boundary({**c, "slot": "A11"})

    # chặng ⑤: bài chưa đối chiếu nguyên văn không vào được pool
    assert SH.kiem_pool([{**c, "problem_text_verified": False}])


# ══ BÁO CÁO SẴN SÀNG — sinh ra, không viết tay ═══════════════════════════
@pytest.fixture(scope="module")
def RP():
    return _nap("report_holdout_readiness")


def test_bao_cao_thu_thap_du_bay_bam(RP):
    d = RP.thu_thap()
    for k in ("git_sha", "cache_version", "skill_hash", "prompt_hash",
              "measured_system_hash", "metric_contract_hash",
              "capability_boundary_hash", "pool_hash"):
        assert d[k] and d[k] != "unknown", f"thiếu `{k}`"


def test_bao_cao_NEU_RA_blocker_khi_pool_rong(RP):
    d = RP.thu_thap()
    b = RP.blockers(d)
    assert any("POOL" in x for x in b) and any("SEED" in x for x in b)
    assert any("ĐỘ PHỦ" in x for x in b)


def test_bao_cao_da_sinh_va_KHONG_TROI(RP):
    """Báo cáo mang băm và số đếm. Viết tay thì nó đúng đúng một lần."""
    f = GEO / "PHASE7B_READINESS_REPORT.md"
    assert f.exists(), "chưa sinh PHASE7B_READINESS_REPORT.md"
    src = f.read_text(encoding="utf-8")
    d = RP.thu_thap()
    assert d["pool_hash"] in src, "báo cáo trôi khỏi pool — chạy lại script"
    assert f"accepted`: {d['accepted']}/40" in src
    assert ("READY_FOR_PHASE7B:  NO" in src) == bool(RP.blockers(d))


# ══ BÁO CÁO ỨNG VIÊN — không được MÂU THUẪN với pool ═════════════════════
def test_bao_cao_ung_vien_KHONG_nhan_bai_pool_DA_LOAI(POOL_D):
    """Dương tính giả đã xảy ra: bộ sàng đọc VĂN BẢN ĐỀ, nên nó không thấy cái
    vô tỉ nằm ở ĐÁP ÁN — bài lập phương `d = 3√6` có đề sạch trơn, không một
    dấu căn, và được đánh ✅ NHẬN trong khi pool đã phán
    `rejected_capability_boundary`.

    Hai nguồn sự thật thì bản dễ dãi hơn là bản người ta đọc. Nên phán quyết
    của pool THẮNG: nó đã tra tới tận kernel, bộ sàng thì chưa.
    """
    f = GEO / "HOLDOUT_CANDIDATE_REPORT.md"
    if not f.exists():
        pytest.skip("chưa sinh HOLDOUT_CANDIDATE_REPORT.md")
    src = f.read_text(encoding="utf-8")
    da_loai = {c.get("nguon", {}).get("url")
               for c in POOL_D["cases"] if c.get("status", "accepted") != "accepted"}
    for dong in src.splitlines():
        if "✅ NHẬN" not in dong:
            continue
        for u in da_loai:
            assert u and u not in dong, (
                f"báo cáo nhận một bài pool đã loại: {u}")


def test_bao_cao_ung_vien_khai_dung_READY_FOR_INGEST():
    f = GEO / "HOLDOUT_CANDIDATE_REPORT.md"
    if not f.exists():
        pytest.skip("chưa sinh HOLDOUT_CANDIDATE_REPORT.md")
    src = f.read_text(encoding="utf-8")
    m = re.search(r"ACCEPTABLE_CANDIDATES:\s*(\d+)", src)
    assert m, "báo cáo thiếu dòng ACCEPTABLE_CANDIDATES"
    co = int(m.group(1)) > 0
    assert (f"READY_FOR_INGEST:      {'YES' if co else 'NO'}") in src


# ══ human_verifier + oracle_ref là TRƯỜNG, không phải văn xuôi ═══════════
def test_ingest_sinh_du_human_verifier_va_oracle_ref(IN, SH):
    nguoi, bai, loi = IN.phan_tich(_LO, SH)
    assert loi == []
    c = IN.thanh_case(bai[0], nguoi, SH)
    assert c["human_verifier"] == nguoi, "danh tính người chép phải là TRƯỜNG"
    assert c["oracle_ref"] == "volume"
    assert c["oracle_ref"] in c["oracle_result"]


def test_XAC_MINH_true_ma_KHONG_ai_ky_thi_DO(SH):
    """Chữ ký không có người ký thì không phải chữ ký."""
    b = _bai_a14()
    b.pop("human_verifier", None)
    loi = SH.kiem_pool([b])
    assert loi and "human_verifier" in loi[0]


def test_co_ORACLE_ma_khong_biet_KHOA_NAO_la_oracle_thi_DO(SH):
    """`oracle_result` mang được nhiều khoá — khoá văn xuôi là ghi chú cho
    người đọc, không dùng để chấm. Dặn dò ấy từng chỉ nằm trong văn xuôi của
    `dev/cases.json`, mà bộ chấm không đọc văn xuôi."""
    b = _bai_a14(human_verifier="X")
    b.pop("oracle_ref", None)
    loi = SH.kiem_pool([b])
    assert loi and "thiếu `oracle_ref`" in loi[0]

    b2 = _bai_a14(human_verifier="X", oracle_ref="khong_ton_tai")
    loi2 = SH.kiem_pool([b2])
    assert loi2 and "không có trong" in loi2[0]


def test_bai_HOP_LE_day_du_van_qua(SH):
    b = _bai_a14(human_verifier="Người kiểm thử", oracle_ref="volume")
    assert SH.kiem_pool([b]) == []


# ══ CỔNG ĐÓNG BĂNG TẬP KỲ VỌNG ═══════════════════════════════════════════
@pytest.fixture(scope="module")
def FEC():
    return _nap("freeze_expectation_check")


def _pool_a11() -> dict:
    return {"case_id": "hp_a11_x", "slot": "A11", "status": "accepted",
            "problem_text": "Cho hình chóp…",
            "oracle_result": {"distance": "1"}}


def _kv_a11(**doi) -> dict:
    c = {"case_id": "hp_a11_x", "slot": "A11", "problem_text": "Cho hình chóp…",
         "construction_obligations": [],
         "verification_obligations": [
             {"kind": "distance", "ly_do": "đề hỏi khoảng cách điểm đến mặt"}],
         "oracle_ref": {"pool_case_id": "hp_a11_x", "khoa": "distance"}}
    c.update(doi)
    return {"cases": [c]}


def test_kY_VONG_KHOP_POOL_thi_khong_bao_loi(FEC, SH, GE):
    assert FEC.kiem(_kv_a11(), [_pool_a11()], SH, GE) == []


def test_BAI_TRONG_POOL_ma_KHONG_co_ky_vong_thi_DO(FEC, SH, GE):
    """Thiếu kỳ vọng ⇒ chấm bằng tập rỗng ⇒ bài LUÔN trượt, và cái trượt ấy
    vào báo cáo thành *"mô hình sai"*."""
    loi = FEC.kiem({"cases": []}, [_pool_a11()], SH, GE)
    assert loi and "KHÔNG có kỳ vọng" in loi[0]


def test_KY_VONG_MO_COI_thi_DO(FEC, SH, GE):
    loi = FEC.kiem(_kv_a11(), [], SH, GE)
    assert loi and "KHÔNG có bài `accepted`" in loi[0]


def test_O_LECH_giua_hai_file_thi_DO(FEC, SH, GE):
    loi = FEC.kiem(_kv_a11(slot="A12"), [_pool_a11()], SH, GE)
    assert any("ô LỆCH" in d for d in loi), loi


def test_NGHIA_VU_KHONG_KHOP_BANG_O_thi_DO(FEC, SH, GE):
    """Hoặc đề vào nhầm ô, hoặc kỳ vọng sai — cả hai đều phải dừng."""
    kv = _kv_a11(verification_obligations=[
        {"kind": "volume", "ly_do": "khai nhầm nghĩa vụ"}])
    loi = FEC.kiem(kv, [_pool_a11()], SH, GE)
    assert any("đòi nghĩa vụ kiểm" in d for d in loi), loi


def test_TRON_HAI_TAP_thi_DO(FEC, SH, GE):
    """Cổng chống quay lại đúng lỗi mà Phase 7A.2 đi tách."""
    kv = _kv_a11(construction_obligations=[
        {"ten_trong_de": "distance", "kieu": "point3", "ly_do": "x" * 30}])
    loi = FEC.kiem(kv, [_pool_a11()], SH, GE)
    assert any("hai tập bị trộn" in d for d in loi), loi


def test_DE_LECH_giua_hai_file_thi_DO(FEC, SH, GE):
    loi = FEC.kiem(_kv_a11(problem_text="Cho hình chóp… (đã sửa)"),
                   [_pool_a11()], SH, GE)
    assert any("LỆCH với pool" in d for d in loi), loi


def test_bam_ky_vong_khai_THIEU_FILE_khi_chua_co(FEC):
    """Băm phải nói thẳng là thiếu, không trả một chuỗi trông như băm thật —
    con dấu mang một băm giả còn tệ hơn con dấu thiếu băm."""
    assert FEC.bam_ky_vong() == "THIẾU_FILE"


def test_bao_cao_co_muc_METRIC_voi_du_NAM_chi_so(RP):
    src = (GEO / "PHASE7B_READINESS_REPORT.md").read_text(encoding="utf-8")
    assert "## 3. Metric" in src
    for m in ("served", "oracle", "construction_match", "verification_match",
              "construction_validity", "stability"):
        assert f"`{m}`" in src, f"báo cáo thiếu chỉ số `{m}`"


# ══ KHUNG KỲ VỌNG — máy điền thứ SUY RA ĐƯỢC, người điền thứ PHÁN ═══════
@pytest.fixture(scope="module")
def SC():
    return _nap("scaffold_expectation")


def _pool_accepted() -> list[dict]:
    return [{"case_id": "hp_a14_001", "slot": "A14", "status": "accepted",
             "capability_tag": "rational_volume", "answer_shape": "exact_fraction",
             "problem_text": "Cho hình chóp S.ABCD…", "oracle_ref": "volume",
             "oracle_result": {"volume": "2/3"}}]


def test_khung_DIEN_thu_suy_ra_duoc(SC, SH):
    k = SC.dung_khung(_pool_accepted(), SH)
    c = k["cases"][0]
    assert c["case_id"] == "hp_a14_001" and c["slot"] == "A14"
    # problem_text CHÉP từ pool ⇒ không bao giờ lệch giữa hai file.
    assert c["problem_text"] == "Cho hình chóp S.ABCD…"
    assert c["oracle_ref"]["khoa"] == "volume"
    # `kind` suy từ BANG_O — ô đã định nghĩa nghĩa vụ kiểm.
    assert [o["kind"] for o in c["verification_obligations"]] == ["volume"]


def test_khung_KHONG_doan_nghia_vu_DUNG(SC, SH):
    """`BANG_O` chỉ định nghĩa nghĩa vụ KIỂM. Nghĩa vụ DỰNG đọc từ ĐỘNG TỪ của
    đề — máy điền bừa là tái lập đúng lỗi Phase 7A.2 đi tách."""
    k = SC.dung_khung(_pool_accepted(), SH)
    assert k["cases"][0]["construction_obligations"] == []
    assert any("ĐỘNG TỪ" in d or "động từ" in d
               for d in k["cases"][0]["__can_nguoi_dien__"])


def test_khung_KHONG_tu_khai_nguoi_phan(SC, SH):
    k = SC.dung_khung(_pool_accepted(), SH)
    assert k["nguoi_danh_gia"]["loai"].startswith("<")
    assert "nguoi_do" in k["nguoi_danh_gia"]["loai"]  # nhắc điều bị cấm
    assert k["sinh_tu_model_output"] is False


def test_khung_CHUA_NAP_DUOC_chung_nao_con_cho_trong(SC, SH, GE, tmp_path):
    """Khung không phải tập kỳ vọng. Không chặn thì `ly_do: "<vì sao…>"` đi
    thẳng vào tập đã niêm phong như một lý do thật."""
    k = SC.dung_khung(_pool_accepted(), SH)
    (tmp_path / "holdout.json").write_text(
        json.dumps(k, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="CHỖ TRỐNG"):
        GE.nap("holdout", thu_muc=tmp_path)


def test_khoi_CHU_THICH_khong_bi_coi_la_cho_trong(GE, SC, SH):
    """Lỗi thật, bắt bằng cách chạy trọn chuỗi M1 trên pool tạm.

    `__khai__` của khung có câu *"Mọi chỗ <...> là chỗ NGƯỜI phải điền"*. Trước
    bản sửa, người điền xong **mọi** trường thật thì `nap()` VẪN từ chối và chỉ
    vào `__khai__[1]` — một dòng hướng dẫn. Đúng lúc M1, với thông báo không ai
    hiểu là phải sửa gì.
    """
    assert GE._tim_cho_trong({"__khai__": ["Mọi chỗ <...> phải điền"],
                              "that": "ok"}) == []
    # Nhưng trường THẬT còn chỗ trống thì vẫn phải bắt.
    assert GE._tim_cho_trong({"__khai__": ["<hướng dẫn>"], "that": "<x>"}) \
        == ["that"]


def test_khung_SAU_KHI_DIEN_thi_nap_duoc(GE, SC, SH, tmp_path):
    """Chuỗi M1 chạy trọn: scaffold → điền → nạp. Trước bản sửa, bước cuối
    không bao giờ tới được."""
    pool = [{"case_id": "hp_a14_001", "slot": "A14", "status": "accepted",
             "capability_tag": "rational_volume", "answer_shape": "exact_fraction",
             "problem_text": "Cho hình chóp…", "oracle_ref": "volume",
             "oracle_result": {"volume": "2/3"}}]
    k = SC.dung_khung(pool, SH)
    for c in k["cases"]:
        for o in c["verification_obligations"]:
            o["trich_de"] = "Tính thể tích V"
            o["ly_do"] = "đề hỏi một số, chủ thể là solid ⇒ nghĩa vụ volume"
        c["ghi_chu_dung"] = "đề chỉ TÍNH, không có động từ dựng"
    k["nguoi_danh_gia"] = {"loai": "sach_chuyen_de", "ai": "lời giải trong tài liệu"}
    (tmp_path / "holdout.json").write_text(
        json.dumps(k, ensure_ascii=False), encoding="utf-8")
    assert GE.nap("holdout", thu_muc=tmp_path)["tap"] == "holdout"


def test_bao_loi_CHO_TRONG_kem_DUONG_DAN(GE):
    """"Còn chỗ trống ở đâu đó" là thông tin vô dụng trên một tập 20 bài."""
    assert GE._tim_cho_trong({"a": "<x>", "b": [{"c": "ok"}, {"d": "TODO"}]}) \
        == ["a", "b[1].d"]


def test_pilot_VAN_nap_duoc_sau_khi_them_cong(GE):
    """Hồi quy: cổng chỗ trống không được làm hỏng tập đang dùng."""
    assert GE.nap("pilot")["tap"] == "pilot"


def test_khung_KHONG_dung_duoc_khi_pool_rong(SC, SH):
    assert SC.dung_khung([], SH)["cases"] == []


# ══ CHUỖI MỘT LỆNH ═══════════════════════════════════════════════════════
@pytest.fixture(scope="module")
def M1():
    return _nap("run_m1_pipeline")


def test_chuoi_KHONG_gop_seal(M1):
    """`seal` tiêu seed của GVHD và chỉ chạy được MỘT LẦN. Để nó trong một
    lệnh chạy-hàng-ngày là mời một cú `--ghi` lỡ tay tiêu mất con dấu."""
    src = (SCRIPTS / "run_m1_pipeline.py").read_text(encoding="utf-8")
    assert "seal_geometry_holdout" not in src.replace("`seal`", "") \
        or "KHÔNG gộp `seal`" in src
    assert "KHÔNG gộp `seal`" in src


def test_chuoi_DUNG_o_chang_dau_tien_hong(M1, tmp_path, capsys):
    """Hỏng thì phải nói CHẶNG NÀO — không để người đọc ngược log đi tìm."""
    f = tmp_path / "lo.txt"
    f.write_text("[A14] đề quá ngắn\n", encoding="utf-8")
    ma = M1.main.__globals__
    import sys as _s
    cu = _s.argv
    _s.argv = ["x", str(f)]
    try:
        assert M1.main() == 2
    finally:
        _s.argv = cu
    ra = capsys.readouterr().out
    assert "FAILED_STAGE:" in ra and "REASON:" in ra and "FIX_REQUIRED:" in ra
    assert "KHÔNG sửa validator" in ra


def test_chuoi_SOI_khong_ghi_gi(M1, POOL_D, tmp_path, capsys):
    """Chế độ soi phải hoàn toàn vô hại — đọc pool thật, không đụng vào nó."""
    f = tmp_path / "lo.txt"
    f.write_text(
        "NGƯỜI CHÉP: Test · 2026-08-28 · fixture\n\n"
        "[A14] Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, "
        "AB = a, AC = 2a. Cạnh bên SA vuông góc với đáy và SA = 2a. "
        "Tính thể tích V của khối chóp S.ABC.\n"
        "      NGUỒN: fixture trang 80\n      ĐÁP ÁN: 2/3\n", encoding="utf-8")
    truoc = (GEO / "holdout" / "pool.json").read_text(encoding="utf-8")
    import sys as _s
    cu = _s.argv
    _s.argv = ["x", str(f)]
    try:
        assert M1.main() == 0
    finally:
        _s.argv = cu
    assert (GEO / "holdout" / "pool.json").read_text(encoding="utf-8") == truoc
    ra = capsys.readouterr().out
    assert "[1/6]" in ra and "[6/6]" in ra
    assert "accepted = 1" in ra


def test_bang_the_nang_luc_phu_DU_20_o(POOL_D, SH):
    """Ô không có thẻ nào ⇒ người soạn bài cho ô ấy không biết khai gì."""
    co = {o for t in POOL_D["__the_nang_luc__"].values()
          if isinstance(t, dict) for o in t.get("o", [])}
    assert co == set(SH.BANG_O), f"thiếu ô: {sorted(set(SH.BANG_O) - co)}"


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


def test_bao_cao_ma_tran_da_sinh_va_KHONG_TROI_khoi_pool(MT):
    """Báo cáo đã sinh phải khớp pool ĐANG CÓ. Con số dẫn từ `ma_tran`, không
    ghim tay: ghim tay thì mỗi lần thêm bài là một test đỏ oan, và người ta sẽ
    sửa test thay vì sinh lại báo cáo."""
    f = GEO / "holdout" / "COVERAGE_MATRIX.md"
    assert f.exists(), "chưa sinh COVERAGE_MATRIX.md"
    src = f.read_text(encoding="utf-8")
    for h in MT.HO:
        assert h in src
    m = MT.ma_tran(MT.doc_pool())
    assert f"{20 - len(m['o_trong'])}/20 ô" in src, (
        "COVERAGE_MATRIX.md trôi khỏi pool — chạy lại holdout_coverage_matrix.py")
    assert ("CHƯA RÚT ĐƯỢC" in src) == bool(m["o_trong"])


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


# ══ PHASE 7A.3 — `k` VÀ GIAO THỨC ĐÃ ĐÓNG BĂNG ═══════════════════════════
_K_FINAL = GEO / "HOLDOUT_K_FINAL.md"
_PROTO = GEO / "HOLDOUT_PROTOCOL.md"
_METRIC = GEO / "PHASE7_METRIC_CONTRACT.md"

#: `k` đã chốt ở Phase 7A.3. Đổi hằng số này = đổi cỡ mẫu của lượt đo chính
#: thức, nên nó phải đỏ ở đây trước khi đỏ ở đâu khác.
K_CHOT = 3
LOGIC_MOI_LUOT, HTTP_MOI_LUOT = 6, 8


def test_k_da_duoc_CHOT_thanh_van_ban(SH):
    assert _K_FINAL.exists(), "chưa có HOLDOUT_K_FINAL.md"
    src = _K_FINAL.read_text(encoding="utf-8")
    assert f"k = {K_CHOT}" in src
    assert len(SH.BANG_O) == 20, "ngân sách dẫn từ số ô — số ô đổi thì phải chốt lại"


def test_ngan_sach_KHOP_PHEP_TINH_o_ca_HAI_tai_lieu(SH):
    """Con số phải **dẫn ra được**, và hai tài liệu không được nói hai số.

    Ngân sách trôi giữa `HOLDOUT_K_FINAL` và `HOLDOUT_PROTOCOL` là loại lỗi
    người ta chỉ phát hiện lúc quota cạn giữa phiên đo.
    """
    n = len(SH.BANG_O)
    logic, http = n * K_CHOT * LOGIC_MOI_LUOT, n * K_CHOT * HTTP_MOI_LUOT
    assert (logic, http) == (360, 480)
    for f in (_K_FINAL, _PROTO):
        src = f.read_text(encoding="utf-8")
        assert str(logic) in src, f"{f.name}: thiếu số logic {logic}"
        assert str(http) in src, f"{f.name}: thiếu số HTTP {http}"


def test_protocol_da_LAM_RO_nghia_cua_MOT_LUOT():
    """Cấm **lặp CÓ SỬA**, không cấm cỡ mẫu. Không làm rõ thì hai tài liệu đọc
    như chống nhau, và một trong hai sẽ bị phá lúc chạy."""
    src = _PROTO.read_text(encoding="utf-8")
    assert "một PHIÊN ĐO đã niêm phong" in src
    assert "lặp CÓ SỬA" in src
    assert "chạy đúng một lần cho mỗi bài rồi kết luận" in src


def test_metric_contract_ghi_day_la_DIEU_KIEN_LAY_MAU_khong_phai_dinh_nghia():
    """`§7` là nhật ký đổi chỉ số. Lần này **không** đổi định nghĩa nào, và
    việc ghi rõ điều đó quan trọng ngang việc ghi một lần đổi thật."""
    src = _METRIC.read_text(encoding="utf-8")
    assert "### 7A.3" in src
    doan = src.split("### 7A.3")[1]
    assert "KHÔNG ĐỔI" in doan and "ĐIỀU KIỆN LẤY MẪU" in doan


# ══ PHASE 7A.4 — ĐƠN VỊ ORACLE, DẪN TỪ MÃ ═══════════════════════════════
#
# VÌ SAO CẦN: bản đầu của pool khai `distance` bằng **bình phương** khoảng
# cách, chép theo khuôn — và khuôn ấy SAI. `geometry_exec._do` trả khoảng cách
# THẬT. Sai đơn vị thì oracle đúng cũng chấm ra sai, và sau khi niêm phong thì
# không sửa được. Nên quy ước phải được **chứng minh bằng mã**, không phải khai
# trong một đoạn văn.
def test_distance_VO_TI_thi_engine_NEM_chu_khong_tra_binh_phuong():
    """Hiện trường thật: bài từng suýt vào ô A11 (lập phương cạnh 6,
    `d(P,(MED)) = 3√6`). `d² = 54` hữu tỉ, nhưng `d` thì không."""
    from fractions import Fraction

    from app.simulation.geometry import measure as M
    from app.simulation.geometry.exact import Plane3, Point3
    from app.simulation.semantic_program.geometry_exec import _can_huu_ti

    mp, e, d_, p = (Point3(Fraction(0), Fraction(0), Fraction(6)),
                    Point3(Fraction(3), Fraction(0), Fraction(0)),
                    Point3(Fraction(0), Fraction(6), Fraction(0)),
                    Point3(Fraction(6), Fraction(6), Fraction(6)))
    d2 = M.distance_sq_point_plane(p, Plane3.through(mp, e, d_))
    assert Fraction(d2) == 54
    assert _can_huu_ti(Fraction(d2)) is None, (
        "√54 hữu tỉ hoá được?! Nếu đổi thì quy ước oracle của pool phải viết lại")


def test_goc_DUONG_MAT_tra_SIN_binh_khong_phai_COS_binh():
    """Bẫy im lặng: cùng tên `angle_cos_sq`, nhưng cặp đường–mặt đi qua
    `sin_sq_line_plane`. Ô A10 khai nhầm cos² thì chấm sai mà không ai biết."""
    import inspect

    from app.simulation.semantic_program import geometry_exec

    src = inspect.getsource(geometry_exec._do)
    assert "sin_sq_line_plane" in src and "cos_sq_between_lines" in src


def test_pool_KHAI_dung_quy_uoc_don_vi(POOL_D):
    dv = POOL_D.get("__don_vi_oracle__")
    assert dv, "pool chưa khai `__don_vi_oracle__`"
    assert "GEOMETRY_IRRATIONAL_RESULT" in dv["distance"]
    assert "sin²" in dv["angle"], "chưa cảnh báo bẫy đường–mặt"


def test_moi_oracle_distance_trong_pool_deu_HUU_TI(POOL_D):
    """Cổng cơ học cho đúng lớp lỗi vừa bắt được: một `distance` không phân số
    hoá được là một bài engine sẽ ném, tức một ô chắc chắn trượt."""
    from fractions import Fraction

    for c in POOL_D["cases"]:
        v = (c.get("oracle_result") or {}).get("distance")
        if v is None:
            continue
        Fraction(str(v))  # nổ ở đây = đề không thuộc phủ, phải loại


def test_bai_bi_loai_deu_co_LY_DO(POOL_D):
    """Loại im lặng là một dạng chọn tập."""
    for b in POOL_D.get("__bai_bi_loai__") or []:
        assert b.get("ly_do_loai"), f"{b.get('case_id_du_kien')}: loại mà không nêu lý do"
        assert b.get("nguon_url"), "bài bị loại vẫn phải tra ngược được"


def test_checklist_ton_tai_va_du_BAY_muc_bao_cao():
    f = GEO / "PHASE7B_CHECKLIST.md"
    assert f.exists(), "chưa có PHASE7B_CHECKLIST.md"
    src = f.read_text(encoding="utf-8")
    for muc in ("served", "oracle", "construction_match", "verification_match",
                "construction_validity", "stability", "Taxonomy lỗi"):
        assert muc in src, f"checklist thiếu mục báo cáo `{muc}`"
    # Câu kết luận bị cấm phải có mặt như một điều CẤM, không phải để dùng.
    assert "AI hiểu hình học" in src and "❌" in src
