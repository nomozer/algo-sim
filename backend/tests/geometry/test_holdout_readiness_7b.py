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
    """Không bài giả. Mỗi bài phải TRA NGƯỢC ĐƯỢC — đó là toàn bộ thứ phân
    biệt một tập held-out với một tập tôi tự soạn.

    Hai loại xuất xứ, một bảo đảm. Bản trước chỉ nhận `url` bắt đầu bằng
    `http`, mà 5 bài đến từ SGK/SBT **in giấy** — chúng tra ngược được bằng
    *tên sách + trang + số bài*, và ép chúng có url thì lối dễ nhất là nhét
    một chuỗi bất kỳ vào trường `url` (đúng thứ đã xảy ra: `url` từng giữ
    nguyên cả câu trích dẫn). Nên kiểm theo `nguon.loai`, và `KHONG_TRA_NGUOC`
    là trạng thái ĐỎ chứ không phải giá trị hợp lệ.
    """
    for c in POOL_D["cases"]:
        n = c.get("nguon") or {}
        loai = n.get("loai")
        assert loai in ("web", "sach_in", "soan_noi_bo"),             f"{c['case_id']}: nguồn {loai!r}"
        if loai == "soan_noi_bo":
            # Bài TỰ SOẠN không có nguồn ngoài để tra — đó là lý do nó phải
            # tự khai `curated_preseal` + `suy_dan`, và bị trần ĐÚNG MỘT.
            assert c.get("curated_preseal") is True,                 f"{c['case_id']}: nguồn tự soạn mà không khai `curated_preseal`"
        elif loai == "web":
            assert n.get("url", "").startswith("http"), \
                f"{c['case_id']}: loại `web` mà url không phải url"
        else:
            assert re.search(r"\btrang\s*\d+", n.get("vi_tri", "")), \
                f"{c['case_id']}: sách in mà không chỉ được TRANG"
        # Tầng A chấm bằng ORACLE ⇒ phải có đáp án nguồn. Tầng B chấm bằng
        # *từ chối trung thực* ⇒ `PROTOCOL_AMENDMENT_PRESEAL` bỏ yêu cầu chép
        # một con số không ai chấm, và thay bằng `nguon_loi_giai` (chứng minh
        # lời giải TỒN TẠI và tra được). Cùng một luật `kiem_pool` áp, chỉ là
        # ở đầu kia — nên test phải tách y hệt, không đòi chung một trường.
        if str(c["slot"]).startswith("A"):
            assert c.get("dap_an_chinh_thuc"), f"{c['case_id']}: thiếu đáp án"
        else:
            assert c.get("nguon_loi_giai"), \
                f"{c['case_id']}: tầng B thiếu `nguon_loi_giai`"
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


def test_pool_THIEU_O_thi_KHONG_niem_phong_duoc(SH, POOL_D):
    """Cổng thật: thiếu ô ⇒ dừng, KHÔNG rút bù. Không con dấu nào ra đời.

    Bản trước khẳng định *"pool đang thiếu ô"* rồi tự dặn `cập nhật test này
    khi thật sự tới đó` — một test khoá trạng thái tạm, và nó đỏ đúng vào
    ngày pool phủ đủ (2026-08-29). Nay khoá HÀNH VI: bỏ một ô ra khỏi pool
    thì cổng rút phải từ chối, và phải từ chối **vì thiếu ô** chứ không vì
    thiếu số lượng.
    """
    cases = POOL_D["cases"]
    theo_o: dict[str, list] = {}
    for c in cases:
        if c.get("status", "accepted") == "accepted":
            theo_o.setdefault(c["slot"], []).append(c)
    assert not [o for o in SH.BANG_O if not theo_o.get(o)], "pool phải phủ đủ"

    bo = min(SH.BANG_O, key=lambda o: len(theo_o.get(o, [])))
    con = [c for c in cases if c["slot"] != bo]
    _, ly_do = SH.kiem_du_dieu_kien_rut(con)
    assert any(bo in x for x in ly_do), (bo, ly_do)
    assert any("KHÔNG rút bù" in x for x in ly_do), ly_do


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
    # A11 nay ĐÃ có bài `accepted` (nạp 2026-08-29), nên ô không còn trống —
    # nhưng `hp_a11_001` vẫn phải NẰM LẠI trong file và vẫn phải bị loại.
    # Điều kiện thật của test này là *bài bị loại không lấp ô*, không phải
    # *ô A11 trống*: bài bị loại mà lấp ô là pool tự khai đủ phủ bằng một bài
    # hệ không tính được.
    mt = MT.ma_tran(POOL_D["cases"])
    assert "A11" not in mt["o_trong"], "A11 đã nạp bài accepted"
    assert c["case_id"] not in {x for v in mt.get("theo_o", {}).values()
                                for x in (v if isinstance(v, list) else [])},         "bài BỊ LOẠI không được đếm vào độ phủ"


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
         "verification_mode": "NGƯỜI",
         "measured_output_used_for_source_verification": False,
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
      PHÉP CHUYỂN: nguồn in V = 4 (đã là phân số) — vào thẳng `volume`
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
      NGUỒN: fixture · bài 1 · https://vi.du/fixture1
      ĐÁP ÁN: 4
      PHÉP CHUYỂN: fixture — nguồn in V = 4, vào thẳng `volume`

[A09] Cho hình lập phương ABCD.A'B'C'D'. Tính góc giữa hai đường thẳng AB và
      B'C', biểu diễn kết quả bằng bình phương cosin của góc ấy.
      NGUỒN: fixture · bài 2 · https://vi.du/fixture2
      ĐÁP ÁN: 0
      PHÉP CHUYỂN: fixture — nguồn in góc 90°, cos²(90°) = 0
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


def test_bao_cao_NEU_RA_dung_blocker_CON_LAI(RP):
    """Blocker phải theo pool THẬT, không theo một danh sách viết cứng.

    Bản trước khoá *"phải có blocker POOL"* — đúng khi pool rỗng, và thành
    SAI ngay khi pool đủ 41/40. Một test khoá trạng thái tạm thời thì lần
    đóng mốc nào cũng phải sửa nó, và lần thứ ba người ta sửa bằng cách nới
    khẳng định. Nên khoá QUAN HỆ: blocker có mặt ⇔ điều kiện chưa đạt.
    """
    d = RP.thu_thap()
    b = RP.blockers(d)
    assert any("SEED" in x for x in b) == (not d["seal_ton_tai"])
    assert any("ĐỘ PHỦ" in x for x in b) == bool(d["o_trong"])
    assert any("POOL" in x and "40" in x for x in b) == (d["accepted"] < 40)


# ══ DUYỆT NGÂN SÁCH: CHÉP LẠI QUYẾT ĐỊNH, KHÔNG PHẢI TỰ DUYỆT ════════════
def test_duyet_ngan_sach_DOI_dung_con_so_hien_hanh(RP, SH, tmp_path, monkeypatch):
    """File duyệt phải khớp HẰNG SỐ, nếu không nó duyệt cho một ngân sách khác.

    `K_CHOT` là cỡ mẫu của lượt đo chính thức. Đổi nó = đổi ngân sách; nếu
    file duyệt vẫn nằm đó với con số cũ thì blocker im lặng ở trạng thái
    "đã duyệt", và lượt chạy tiêu quota theo một con số chưa ai nhìn.
    """
    assert RP._duyet_ngan_sach(SH), "file duyệt hiện tại phải khớp"

    class SHKhac:                       # k đổi ⇒ ngân sách đổi
        BANG_O, K_CHOT = SH.BANG_O, SH.K_CHOT + 1
        LOGIC_MOI_LUOT, HTTP_MOI_LUOT = SH.LOGIC_MOI_LUOT, SH.HTTP_MOI_LUOT
    assert not RP._duyet_ngan_sach(SHKhac), "k đổi mà vẫn đọc là đã duyệt"

    monkeypatch.setattr(RP, "DUYET", tmp_path / "khong-co.md")
    assert not RP._duyet_ngan_sach(SH), "không file mà vẫn đọc là đã duyệt"


def test_duyet_ngan_sach_KHONG_ha_blocker_SEED(RP, tmp_path, monkeypatch):
    """Hai cổng, hai quyết định. Duyệt tiền không phải là cấp seed."""
    d = dict(RP.thu_thap(), seal_ton_tai=False)
    assert any("SEED" in x for x in RP.blockers(d)), \
        "chưa niêm phong mà báo cáo không kêu thiếu seed"


def test_da_NIEM_PHONG_thi_KHONG_con_keu_thieu_seed(RP):
    """Kêu thiếu seed sau khi đã niêm phong là mời người ta niêm phong lần
    nữa — mà rút lại sau khi thấy kết quả chính là thứ `§5③` cấm."""
    d = RP.thu_thap()
    if not d["seal_ton_tai"]:
        pytest.skip("chưa niêm phong")
    assert not any("SEED" in x for x in RP.blockers(d)), RP.blockers(d)


# ══ HẾT BLOCKER ≠ HẾT ĐIỀU PHẢI KHAI ═════════════════════════════════════
def test_caveat_NEU_DU_ba_dieu_da_noi_luat(RP):
    """Wave này nới HAI luật của giao thức (`§1` cho ô A12, `§5②` cho nguồn
    seed) và nhận đề chép MÁY thay vì người gõ. Nới xong mà báo cáo chỉ in
    *"0 blocker"* thì người đọc luận văn không có cách nào biết — và đó đúng
    là cách một tuyên bố quá mạnh ra đời: không bằng nói dối, mà bằng im
    lặng đúng chỗ.
    """
    c = RP.caveats(RP.thu_thap())
    assert any("19/20" in x for x in c), "thiếu khai số held-out THẬT"
    assert any("KHÔNG phải GVHD" in x for x in c), "thiếu khai nguồn seed"
    assert any("người kiểm" in x for x in c), "thiếu khai chế độ xác minh"


def test_caveat_BIEN_MAT_khi_khong_con_gi_de_khai(RP):
    """Caveat phải dẫn từ dữ liệu, không phải ba dòng in cứng."""
    d = RP.thu_thap()
    sach = dict(d, nguon_seed="gvhd", che_do_xac_minh={"NGƯỜI"},
                cases=[c for c in d["cases"] if not c.get("curated_preseal")])
    assert RP.caveats(sach) == []


def test_bao_cao_MD_mang_du_caveat(RP):
    src = (GEO / "PHASE7B_READINESS_REPORT.md").read_text(encoding="utf-8")
    for x in RP.caveats(RP.thu_thap()):
        assert x in src, f"báo cáo thiếu caveat: {x[:60]}"


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


def test_che_do_MAY_ma_van_mang_chu_ky_NGUOI_thi_DO(SH):
    """`PROTOCOL_AMENDMENT_PRESEAL` cho chép máy, KHÔNG cho giả làm người.

    Hai trường cùng có mặt thì bên đọc artifact niêm phong về sau sẽ đọc ra
    cái mạnh hơn — tức một chữ ký người cho bài không người nào đọc.
    """
    b = _bai_a14(verification_mode="MÁY-TỪ-NGUỒN", machine_verifier="agent")
    loi = SH.kiem_pool([b])
    assert loi and "human_verifier" in loi[0], loi


def test_che_do_MAY_khai_dung_thi_QUA(SH):
    b = _bai_a14(verification_mode="MÁY-TỪ-NGUỒN", machine_verifier="agent")
    b.pop("human_verifier")
    assert SH.kiem_pool([b]) == []


def test_KHONG_khai_rang_buoc_chong_nhiem_thi_DO(SH):
    """`MEASURED_OUTPUT_USED_FOR_SOURCE_VERIFICATION` phải là TRƯỜNG.

    Nó là lời hứa nặng nhất của cả tập held-out — *không đầu ra nào của hệ
    đang đo được dùng để chuẩn bị tập đo*. Hứa bằng văn xuôi trong giao thức
    thì không ai kiểm được lúc niêm phong.
    """
    b = _bai_a14()
    b.pop("measured_output_used_for_source_verification")
    loi = SH.kiem_pool([b])
    assert loi and "measured_output_used_for_source_verification" in loi[0]
    b2 = _bai_a14(measured_output_used_for_source_verification=True)
    assert SH.kiem_pool([b2]), "khai `true` mà vẫn lọt"


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


def test_bam_ky_vong_KHONG_bao_gio_tra_bam_gia(FEC, tmp_path, monkeypatch):
    """Băm phải nói thẳng là thiếu, không trả một chuỗi trông như băm thật —
    con dấu mang một băm giả còn tệ hơn con dấu thiếu băm.

    `expectations/holdout.json` nay ĐÃ tồn tại, nên khẳng định cũ (*"băm phải
    bằng THIẾU_FILE"*) chỉ còn đo được một trạng thái đã qua. Cái phải khoá
    là HÀNH VI: có file ⇒ băm thật (64 hex); không file ⇒ nói thẳng.
    """
    b = FEC.bam_ky_vong()
    assert re.fullmatch(r"[0-9a-f]{64}", b), f"phải là băm thật, được {b!r}"
    monkeypatch.setattr(FEC, "KY_VONG", tmp_path / "khong-co", raising=False)
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
        "      NGUỒN: SGK fixture trang 80 · https://vi.du/fixture\n"
        "      ĐÁP ÁN: 2/3\n"
        "      PHÉP CHUYỂN: nguồn in V = 2a³/3, chuẩn hoá a = 1 ⇒ 2/3\n",
        encoding="utf-8")
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
    # Số accepted của lượt soi = pool THẬT + 1 bài của lô giả. Viết cứng `1`
    # là khoá trạng thái *pool rỗng*, và nó hết đúng ngay lượt nạp đầu tiên.
    da_nhan = sum(c.get("status", "accepted") == "accepted"
                  for c in POOL_D["cases"])
    assert f"accepted = {da_nhan + 1}" in ra, ra[-200:]


def test_bang_the_nang_luc_phu_DU_20_o(POOL_D, SH):
    """Ô không có thẻ nào ⇒ người soạn bài cho ô ấy không biết khai gì."""
    co = {o for t in POOL_D["__the_nang_luc__"].values()
          if isinstance(t, dict) for o in t.get("o", [])}
    assert co == set(SH.BANG_O), f"thiếu ô: {sorted(set(SH.BANG_O) - co)}"


def test_con_dau_va_cases_LUON_di_cung_nhau():
    """Bản trước khẳng định *chưa có* con dấu — đúng cho tới 2026-08-29, rồi
    đỏ vào đúng ngày niêm phong. Cái nó thật sự bảo vệ thì không hết hiệu
    lực: **con dấu và tập đề phải đi cùng nhau**. Có dấu mà không có đề là
    niêm phong một tập rỗng; có đề mà không có dấu là một tập không ai chứng
    minh được là chưa bị sửa sau khi thấy kết quả.
    """
    dau = GEO / "holdout" / "HOLDOUT_SEAL.json"
    de = GEO / "holdout" / "cases.json"
    assert dau.exists() == de.exists(), (dau.exists(), de.exists())
    if not dau.exists():
        pytest.skip("chưa niêm phong")
    s = json.loads(dau.read_text(encoding="utf-8"))
    ds = json.loads(de.read_text(encoding="utf-8"))
    ds = ds["cases"] if isinstance(ds, dict) else ds
    assert s["n"] == len(ds) == 20
    assert sorted(s["case_ids"]) == sorted(c["case_id"] for c in ds)
    pool = {c["case_id"] for c in json.loads(
        (GEO / "holdout" / "pool.json").read_text(encoding="utf-8"))["cases"]}
    assert set(s["case_ids"]) <= pool, "bài trong con dấu không có trong pool"


def test_con_dau_KHAI_seed_den_tu_dau_khong_ghi_cung(SH):
    """`nguon_seed` từng là chuỗi VIẾT CỨNG `"GVHD"`.

    Nó đúng đúng một lần. Lượt nào seed không do GVHD cấp thì artifact niêm
    phong mang lời khai SAI về chính thứ nó sinh ra để bảo đảm — *ai đã chọn
    tập* — và sai im lặng, vì không gì đối chiếu được một chuỗi viết cứng.
    """
    dau = GEO / "holdout" / "HOLDOUT_SEAL.json"
    if not dau.exists():
        pytest.skip("chưa niêm phong")
    s = json.loads(dau.read_text(encoding="utf-8"))
    assert s["nguon_seed"] in ("gvhd", "nguoi_van_hanh", "cong_khai")
    assert s.get("nguon_seed_khai"), "phải khai bằng câu người đọc được"
    if s["nguon_seed"] != "gvhd":
        assert "KHÔNG phải bên thứ ba" in s["nguon_seed_khai"] \
            or "không do người đo tuỳ ý" in s["nguon_seed_khai"], \
            "nới §5② mà không khai cái mất đi"


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


def test_tap_ky_vong_held_out_KHONG_do_nguoi_do_tu_dat():
    """Bản trước khẳng định `holdout.json` CHƯA tồn tại — một cổng "chưa làm
    tới", hết hiệu lực ngay khi soạn xong kỳ vọng (2026-08-29).

    Thứ nó thật sự bảo vệ thì không hết hiệu lực: kỳ vọng held-out KHÔNG
    được do người đo tự đặt. Nên khoá thẳng điều ấy.
    """
    f = KY_VONG / "holdout.json"
    if not f.exists():
        pytest.skip("chưa soạn kỳ vọng held-out")
    d = json.loads(f.read_text(encoding="utf-8"))
    assert d["nguoi_danh_gia"]["loai"] != "nguoi_do", (
        "kỳ vọng held-out do người đo tự đặt thì số đo không chứng minh gì")
    assert d.get("sinh_tu_model_output") is False
    assert d["nguoi_danh_gia"]["khai_han_che"], "phải khai hạn chế đã biết"


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


# ══ HAI NGƯỠNG POOL — ĐỘ PHỦ ≠ ĐỘ SÂU ════════════════════════════════════
#
# `HOLDOUT_PROTOCOL §3①` đòi **hai** thứ: *"≥40 bài, phủ ĐỦ 20/20 ô"*. Cổng
# rút chỉ canh vế sau. Pool 20 bài — đúng một bài mỗi ô — phủ đủ 20/20 và
# thoát 0, trong khi seed không còn gì để chọn: mọi seed cho ra CÙNG một tập.
# Lúc ấy câu *"seed quyết định bài nào"* thành lời khai suông.
def _bai_hop_le(SH, o: str, n: int = 1) -> dict:
    """Bài tối thiểu hợp lệ cho ô bất kỳ, dẫn thẳng từ BANG_O + NANG_LUC."""
    tag, hinh, tang_a = next(
        (t, h, a) for t, (os_, h, a) in SH.NANG_LUC.items() if o in os_)
    nv = SH.BANG_O[o][0]
    c = {"case_id": f"t_{o.lower()}_{n:03d}", "status": "accepted", "slot": o,
         "capability_tag": tag, "answer_shape": hinh,
         "problem_text": f"đề {o} #{n}", "problem_text_original": f"đề {o} #{n}",
         "problem_text_verified": True, "human_verifier": "Người kiểm thử",
         "verification_mode": "NGƯỜI",
         "measured_output_used_for_source_verification": False,
         "nguon": {"url": "https://x"}, "chua_chay_he": True}
    if tang_a:
        gt = {"predicate_boolean": True, "invariant_relation": True}.get(hinh, "4/3")
        c |= {"dap_an_chinh_thuc": str(gt), "phep_chuyen": "gán a = 2",
              "oracle_result": {nv: gt}, "oracle_ref": nv,
              "expected_obligations": [nv]}
    else:
        # Tầng B vẫn phải mang đáp án CỦA NGUỒN (để thấy hệ từ chối tính cái
        # gì) — chỉ không được mang `oracle_result`.
        # `PROTOCOL_AMENDMENT_PRESEAL`: tầng B chỉ cần chứng minh lời giải
        # TỒN TẠI và TRA ĐƯỢC; đáp án nguồn thành tuỳ chọn vì bộ chấm không
        # đọc nó và tầng B bị cấm có `oracle_result`.
        c |= {"nguon_loi_giai": "nguồn kiểm thử · trang 1, Câu 1",
              "source_solution_present": True,
              "ly_do_ngoai_phu": "ngoài ranh giới năng lực"}
    if tag in SH.DOI_DOMAIN_CONDITION:
        c["domain_condition"] = "hữu tỉ hoá được"
    return c


def _pool(SH, moi_o: int) -> list[dict]:
    return [_bai_hop_le(SH, o, n)
            for o in SH.BANG_O for n in range(1, moi_o + 1)]


def test_khuon_bai_cua_TEST_nay_thuc_su_hop_le(SH):
    """Chốt chặn: nếu khuôn sai thì mọi test dưới đỏ vì lý do KHÁC."""
    p = _pool(SH, 2)
    assert len(p) == 40
    assert SH.kiem_pool(p) == []
    assert [d for c in p for d in SH.check_capability_boundary(c)] == []


def test_PHU_du_20_o_ma_THIEU_bai_thi_KHONG_rut_duoc(SH):
    """20 bài, phủ đủ 20/20 ô — vẫn phải chặn: protocol đòi ≥40."""
    _, loi = SH.kiem_du_dieu_kien_rut(_pool(SH, 1))
    assert loi, "pool 20 bài phủ đủ 20 ô mà cổng cho qua — mất vế ≥40"
    assert any("40" in d for d in loi), loi


def test_du_ca_HAI_nguong_thi_rut_duoc(SH):
    theo_o, loi = SH.kiem_du_dieu_kien_rut(_pool(SH, 2))
    assert loi == []
    assert len(theo_o) == 20


def test_thieu_MOT_o_thi_chan_du_tong_bai_thua(SH):
    """Độ sâu KHÔNG bù được độ phủ — 60 bài mà hụt một ô vẫn chặn."""
    p = [c for c in _pool(SH, 3) if c["slot"] != "A07"]
    _, loi = SH.kiem_du_dieu_kien_rut(p)
    assert any("A07" in d for d in loi), loi


def test_bai_BI_LOAI_khong_duoc_tinh_vao_TONG(SH):
    """`len(cases)` ≠ số bài rút được. Đếm cả bài đã loại là tự khai đủ."""
    p = _pool(SH, 1)
    for c in _pool(SH, 1):
        p.append(c | {"case_id": c["case_id"] + "_x",
                      "status": "rejected_capability_boundary",
                      "reason": "ngoài ranh giới"})
    assert len(p) == 40
    _, loi = SH.kiem_du_dieu_kien_rut(p)
    assert loi, "40 dòng nhưng chỉ 20 bài rút được — cổng phải chặn"


def test_hai_NGUONG_khop_dung_giao_thuc(SH):
    t = (GEO / "HOLDOUT_PROTOCOL.md").read_text(encoding="utf-8")
    assert f"≥{SH.TONG_TOI_THIEU} bài" in t or f"≥ {SH.TONG_TOI_THIEU} bài" in t
    assert SH.MOI_O_TOI_THIEU == 1
    assert SH.TONG_TOI_THIEU >= len(SH.BANG_O) * SH.MOI_O_TOI_THIEU


def test_bao_cao_san_sang_KHONG_giu_nguong_RIENG(SH):
    """Hai cổng đọc cùng một pool; hai ngưỡng viết rời nhau là chờ trôi."""
    src = (SCRIPTS / "report_holdout_readiness.py").read_text(encoding="utf-8")
    assert "TONG_TOI_THIEU" in src, "báo cáo còn hằng số 40 viết tay"
    assert not re.search(r"(?<![\w.])40(?![\w])", src), \
        "còn số 40 trần trong báo cáo — phải dẫn từ seal_geometry_holdout"


# ══ Ô TẦNG B CÓ NẠP ĐƯỢC KHÔNG — HAI CỔNG TỪNG CÃI NHAU ══════════════════
#
# `ingest.phan_tich` CẤM ô B có dòng `ĐÁP ÁN:` (nó sẽ dựng `oracle_result`,
# mà tầng B chấm bằng từ chối trung thực). `kiem_pool` lại ĐÒI mọi bài
# `accepted` có `dap_an_chinh_thuc`. Hai luật đều đúng phần mình và cùng đọc
# một bài — nên B01–B06 (6/20 ô, đúng những ô kế hoạch gọi là *"dễ nhất về
# dữ liệu"*) **không nạp được bằng bất kỳ file lô nào**.
#
# Nặng hơn cả việc chặn: `FIX_REQUIRED` bảo *"Sửa dữ liệu lô"* — một việc
# không làm được. Cổng chặn đúng còn dạy sai thì tệ hơn cổng chặn sai.
def _lo_tang_b(dap_an_nguon: str = "S_xq = 15π", ly_do: str = "mặt cong") -> str:
    return (
        "NGƯỜI CHÉP: Người kiểm thử · 2026-08-28 · lô test\n\n"
        "[B05] Cho hình nón bán kính đáy r = 3, chiều cao h = 4. "
        "Tính diện tích xung quanh.\n"
        "      NGUỒN: nguồn kiểm thử · https://x\n"
        f"      ĐÁP ÁN NGUỒN: {dap_an_nguon}\n"
        f"      NGOÀI PHỦ VÌ: {ly_do}\n")


def test_o_tang_B_NAP_DUOC_qua_file_lo(SH):
    IN = _nap("ingest_holdout_batch")
    nguoi, bai, loi = IN.phan_tich(_lo_tang_b(), SH)
    assert loi == [], loi
    c = IN.thanh_case(bai[0], nguoi, SH)
    assert SH.check_capability_boundary(c) == []
    assert SH.kiem_pool([c]) == [], "ô tầng B vẫn không qua nổi kiem_pool"


def test_o_tang_B_van_KHONG_duoc_mang_oracle_result(SH):
    """Nới cho `dap_an_chinh_thuc` KHÔNG được nới luôn `oracle_result`."""
    IN = _nap("ingest_holdout_batch")
    nguoi, bai, _ = IN.phan_tich(_lo_tang_b(), SH)
    c = IN.thanh_case(bai[0], nguoi, SH)
    assert not c.get("oracle_result"), "tầng B mà có oracle_result — chấm nhầm thang"
    assert c["dap_an_chinh_thuc"] == "S_xq = 15π"
    assert c["ly_do_ngoai_phu"] == "mặt cong"


def test_o_tang_B_dung_dong_DAP_AN_thuong_thi_VAN_bi_chan(SH):
    """Dòng cũ vẫn cấm — nó là dòng dựng `oracle_result`."""
    IN = _nap("ingest_holdout_batch")
    lo = _lo_tang_b().replace("ĐÁP ÁN NGUỒN:", "ĐÁP ÁN:")
    _, _, loi = IN.phan_tich(lo, SH)
    assert any("KHÔNG được có `ĐÁP ÁN:`" in d for d in loi), loi


def test_o_tang_B_thieu_LY_DO_thi_bao_dung_cho_thieu(SH):
    IN = _nap("ingest_holdout_batch")
    lo = "\n".join(l for l in _lo_tang_b().splitlines()
                   if "NGOÀI PHỦ VÌ" not in l)
    _, _, loi = IN.phan_tich(lo, SH)
    assert any("NGOÀI PHỦ VÌ" in d for d in loi), loi


def test_o_tang_A_KHONG_duoc_dung_khuon_cua_tang_B(SH):
    """Hai dòng mới chỉ dành cho tầng B — dùng ở tầng A là lách oracle."""
    IN = _nap("ingest_holdout_batch")
    lo = ("NGƯỜI CHÉP: Người kiểm thử · 2026-08-28 · lô test\n\n"
          "[A14] Cho hình chóp S.ABC …\n"
          "      NGUỒN: nguồn kiểm thử · https://x\n"
          "      ĐÁP ÁN NGUỒN: 2a³/3\n"
          "      NGOÀI PHỦ VÌ: không lý do gì\n")
    _, _, loi = IN.phan_tich(lo, SH)
    for dong in ("ĐÁP ÁN NGUỒN", "NGOÀI PHỦ VÌ"):
        assert any(f"`{dong}:` chỉ dùng cho ô tầng B" in d for d in loi), \
            f"{dong} lọt vào ô tầng A — đó là lối lách oracle"


# ══ BẢNG KẾ HOẠCH TỪNG Ô — SINH RA, KHÔNG GÕ TAY ═════════════════════════
#
# Cùng nội dung này từng nằm trong `CANDIDATE_REVIEW §3` dưới dạng markdown gõ
# tay, và đã sai: nó khai hạn ngạch CỨNG cho từng ô trong khi
# `HOLDOUT_EXPANSION_PLAN §1` cố ý để MỀM (*"mỗi ô ≥1; tổng ≥40; ô nào dễ tìm
# thì lấy"*). Sai kiểu ấy không làm test nào đỏ — không cổng nào đọc markdown.
def test_bang_ke_hoach_phu_DU_20_o(MT, SH):
    d = "\n".join(MT._bang_ke_hoach(MT.ma_tran([])))
    for o in SH.BANG_O:
        assert f"| **{o}** |" in d, f"bảng kế hoạch sót ô {o}"


def test_bang_ke_hoach_KHAI_dung_the_nang_luc(MT, SH):
    """Mọi ô phải mang đúng `capability_tag` của nó — dẫn máy, không chép."""
    d = "\n".join(MT._bang_ke_hoach(MT.ma_tran([])))
    for tag, (os_, _, _) in SH.NANG_LUC.items():
        for o in os_:
            dong = next(l for l in d.splitlines() if l.startswith(f"| **{o}** |"))
            assert f"`{tag}`" in dong, f"{o}: bảng ghi sai thẻ, phải là {tag}"


def test_bang_ke_hoach_KHONG_dat_han_ngach_cung(MT, SH):
    """`≥1` chứ không phải một con số — kế hoạch cố ý để mềm."""
    d = "\n".join(MT._bang_ke_hoach(MT.ma_tran([])))
    for o in SH.BANG_O:
        dong = next(l for l in d.splitlines() if l.startswith(f"| **{o}** |"))
        assert f"≥{SH.MOI_O_TOI_THIEU}" in dong, o


def test_bang_ke_hoach_DANH_DAU_bay_sin_binh_o_A10(MT):
    d = "\n".join(MT._bang_ke_hoach(MT.ma_tran([])))
    dong = next(l for l in d.splitlines() if l.startswith("| **A10** |"))
    assert "sin²" in dong, "A10 mất cảnh báo sin² — chỗ sai im lặng duy nhất"
    dong9 = next(l for l in d.splitlines() if l.startswith("| **A09** |"))
    assert "sin²" not in dong9, "A09 dán nhầm cảnh báo sin²"


def test_bang_ke_hoach_TACH_hai_thang_cham(MT, SH):
    """Tầng B chấm bằng từ chối trung thực — không được mang chỉ số oracle."""
    d = "\n".join(MT._bang_ke_hoach(MT.ma_tran([])))
    for o in SH.BANG_O:
        dong = next(l for l in d.splitlines() if l.startswith(f"| **{o}** |"))
        if o.startswith("A"):
            assert "① ②" in dong, f"{o}: tầng A mất chỉ số oracle"
        else:
            assert "từ chối trung thực" in dong and "①" not in dong, \
                f"{o}: tầng B mang thang của tầng A"


def test_moi_o_deu_khai_NGUON(MT, SH):
    assert set(MT.O_NGUON) == set(SH.BANG_O), \
        "O_NGUON lệch BANG_O — ô mới thêm mà không ai nói lấy đề ở đâu"


def test_o_CHO_QUYET_DINH_deu_co_that(MT, SH):
    assert set(MT.O_CHO_QUYET_DINH) <= set(SH.BANG_O)


def test_ghi_bao_cao_RA_NGOAI_kho_thi_bi_tu_choi(MT, monkeypatch, capsys):
    """`../docs/…` từ `backend/` trỏ ra ngoài kho và từng dựng cây lạc thật."""
    monkeypatch.setattr(sys, "argv",
                        ["x", "--md", "../docs/evaluation/lac.md"])
    assert MT.main() == 2
    assert "NGOÀI kho" in capsys.readouterr().out


# ══ QUYẾT ĐỊNH A11/A12 ĐÃ CHỐT — nguồn sinh phải nói đúng ════════════════
def test_KHONG_con_o_nao_cho_quyet_dinh(MT):
    assert MT.O_CHO_QUYET_DINH == {}, \
        "quyết định ① đã chốt 2026-08-28 — để lại là báo một rào không còn"


def test_A11_A12_khai_RANG_BUOC_huu_ti_trong_bang_sinh(MT):
    d = "\n".join(MT._bang_ke_hoach(MT.ma_tran([])))
    for o in ("A11", "A12"):
        dong = next(l for l in d.splitlines() if l.startswith(f"| **{o}** |"))
        assert "hữu tỉ" in dong, f"{o}: mất ràng buộc chỉ-hữu-tỉ"
        assert "quyết định" not in dong, f"{o}: còn nói là đang chờ quyết định"


def test_VAN_dung_20_o_sau_quyet_dinh(MT, SH):
    """Quyết định là hẹp LUẬT NHẬN, không đổi số ô, không đổi năng lực."""
    assert len(SH.BANG_O) == 20
    assert len(MT.O_NGUON) == 20
    assert set(MT.O_RANG_BUOC_THEM) <= set(SH.BANG_O)
    assert SH.NANG_LUC["rational_distance"][0] == ("A11", "A12")


# ══ HAI CÁI GÓI 45 BÀI SẼ ĐỤNG NGAY ══════════════════════════════════════
def test_dong_CHU_THICH_trong_khoi_KHONG_chui_vao_de(SH):
    """Gói chép tay prefill siêu dữ liệu bằng dòng `#`. Lọt vào `problem_text`
    thì đề gửi cho mô hình mang sẵn lời mách — hỏng im lặng."""
    IN = _nap("ingest_holdout_batch")
    lo = ("NGƯỜI CHÉP: Người kiểm thử · 2026-08-28 · lô test\n\n"
          "#   CAPABILITY : rational_volume\n"
          "#   RỦI RO     : thấp — không bước nào sinh căn\n"
          "[A14] Cho hình chóp S.ABC có đáy ABC vuông tại A, AB = a, AC = 2a, "
          "SA vuông góc với đáy và SA = 2a. Tính thể tích khối chóp S.ABC.\n"
          "#     GỢI Ý NGOÀI LỀ: V = 2a³/3\n"
          "      NGUỒN: nguồn kiểm thử · https://x\n"
          "      ĐÁP ÁN: 2/3\n"
          "      PHÉP CHUYỂN: nguồn in V = 2a³/3, chuẩn hoá a = 1 ⇒ 2/3\n")
    _, bai, loi = IN.phan_tich(lo, SH)
    assert loi == [], loi
    de = bai[0]["de"]
    assert "GỢI Ý" not in de and "CAPABILITY" not in de and "#" not in de, de
    assert de.startswith("Cho hình chóp"), de


def test_trung_case_id_thi_BAO_LOI_chu_khong_bo_qua_im_lang(SH):
    """45 bài nạp một lượt: một va chạm id bị bỏ qua im lặng là mất bài mà
    không ai biết. `hp_a11_001` đã có thật trong pool."""
    IN = _nap("ingest_holdout_batch")
    them, va = IN.loc_trung([{"case_id": "hp_a14_001"},
                             {"case_id": "hp_a14_002"}],
                            [{"case_id": "hp_a14_001"}])
    assert [c["case_id"] for c in them] == ["hp_a14_002"]
    assert va == ["hp_a14_001"], "va chạm id phải TRẢ RA, không nuốt"


def test_trung_case_id_TRONG_CUNG_mot_goi_cung_bi_bat(SH):
    IN = _nap("ingest_holdout_batch")
    them, va = IN.loc_trung([{"case_id": "hp_b05_001"},
                             {"case_id": "hp_b05_001"}], [])
    assert len(them) == 1 and va == ["hp_b05_001"]


# ══ GÓI CHÉP TAY — MỘT FILE CHO TOÀN BỘ PHẦN CON NGƯỜI ═══════════════════
@pytest.fixture(scope="module")
def PK():
    return _nap("make_human_copy_packet")


@pytest.fixture(scope="module")
def VL():
    return _nap("validate_human_copy_packet")


@pytest.fixture(scope="module")
def GOI(PK):
    return PK.dung_goi()


def test_goi_phat_DU_moi_o_va_DU_nguong(PK, SH, GOI):
    assert set(PK.PHAT) == set(SH.BANG_O), "gói sót ô"
    assert all(n >= SH.MOI_O_TOI_THIEU for n in PK.PHAT.values())
    tong = sum(PK.PHAT.values())
    assert tong > SH.TONG_TOI_THIEU, \
        "gói phải phát DƯ — tỉ lệ đạt đo được ≈25%, phát đúng 40 là chắc hụt"
    assert len(re.findall(r"^\[([AB]\d{2})\]", GOI, re.M)) == tong


def test_de_chep_may_deu_co_MUC_RUI_RO_va_viec_can_kiem(PK):
    """`PROTOCOL_AMENDMENT_PRESEAL` (2026-08-28) thay *"người gõ 100%"* bằng
    *"máy chép + người xác minh theo rủi ro"*.

    Luật cũ (cấm prefill đề) hết hiệu lực. Luật thay thế: đề chép máy chỉ hợp
    lệ khi đi kèm **mức rủi ro** và **việc cần kiểm** — thiếu chúng thì người
    xác minh không biết mở nguồn cho bài nào, và cơ chế QC thành lời khai suông.
    """
    for o, v in PK.DA_SOI.items():
        for c in v:
            chep = PK.BAN_CHEP[PK._khoa_chep(c["nguon"])]
            assert chep.get("de"), f"{o}: ứng viên không có đề"
            assert chep.get("rui_ro_muc") in ("LOW", "MEDIUM", "HIGH"), o
            assert chep.get("kiem_gi"), f"{o}: không nói người cần kiểm gì"


def test_de_may_KHONG_doc_chac_thi_de_TRONG_va_gan_HIGH(PK):
    """Máy không đọc chắc thì phải NÓI RA, không đoán cho đủ chỗ."""
    for o, v in PK.DA_SOI.items():
        for c in v:
            chep = PK.BAN_CHEP[PK._khoa_chep(c["nguon"])]
            if chep["de"].lstrip().startswith("<"):
                assert chep["rui_ro_muc"] == "HIGH", \
                    f"{o}: đề còn chỗ trống mà không gắn HIGH"


def test_goi_prefill_dap_an_CHI_khi_da_soi_tan_trang(PK, GOI):
    """Ứng viên đã soi thì điền sẵn nguồn + đáp án; còn lại để trống.

    Chỉ đếm ô TẦNG A: ô tầng B có `DA_SOI` cũng không sinh dòng `ĐÁP ÁN:` —
    nó dùng `ĐÁP ÁN NGUỒN:`, và đáp án ấy do người chép từ sách."""
    da = sum(len(v) for o, v in PK.DA_SOI.items() if o.startswith("A"))
    assert len(re.findall(r"^\s+ĐÁP ÁN: (?!<)", GOI, re.M)) == da
    # Ô tầng B có DA_SOI thì phải được prefill NGUỒN, dù không có ĐÁP ÁN.
    for o in (o for o in PK.DA_SOI if o.startswith("B")):
        kh = next(k for k in re.split(r"(?=^\[[AB]\d{2}\])", GOI, flags=re.M)
                  if k.startswith(f"[{o}]"))
        assert re.search(r"^\s+NGUỒN: (?!<)", kh, re.M), o


def test_goi_XEP_THEO_NGUON_de_moi_tai_lieu_mo_mot_lan(MT, GOI):
    assert GOI.count("#  NGUỒN ") == len(set(MT.O_NGUON.values()))


def test_goi_danh_dau_SOURCE_GAP(PK, GOI):
    for o in PK.SOURCE_GAP:
        assert f"SOURCE_GAP_{o}" in GOI


def test_goi_dung_dung_LOAI_DONG_cho_tung_tang(SH, GOI):
    """Ô A phải có `ĐÁP ÁN:`; ô B phải có hai dòng riêng và KHÔNG có `ĐÁP ÁN:`."""
    for kh in re.split(r"(?=^\[[AB]\d{2}\])", GOI, flags=re.M)[1:]:
        o = kh[1:4]
        # Cắt dòng `#`: khối bị tách theo `[XNN]` nên đuôi nó ôm luôn phần
        # chú thích của khối SAU. Chú thích thì `ingest` gỡ sạch, nên luật
        # "đúng loại dòng" chỉ áp cho DÒNG DỮ LIỆU.
        kh = "\n".join(d for d in kh.splitlines()
                       if not d.lstrip().startswith("#"))
        if o.startswith("A"):
            assert re.search(r"^\s+ĐÁP ÁN:", kh, re.M), o
            assert "ĐÁP ÁN NGUỒN" not in kh and "NGOÀI PHỦ VÌ" not in kh, o
        else:
            assert not re.search(r"^\s+ĐÁP ÁN:", kh, re.M), o
            # `ĐÁP ÁN NGUỒN:` nay TUỲ CHỌN (amendment) — chỉ `NGOÀI PHỦ VÌ:`
            # còn bắt buộc, vì nó là phán đoán không suy hộ được.
            assert "NGOÀI PHỦ VÌ:" in kh, o


def test_goi_KHAI_CHE_DO_MAY_va_TUYET_DOI_khong_ky_thay_nguoi(SH, VL, GOI):
    """QC của người thôi là hàng rào cứng (2026-08-29) — nhưng đổi lại, gói
    phải khai ĐÚNG rằng không người nào ký.

    Bản trước gói mang `NGƯỜI CHÉP: <tên bạn>` để trống và chờ chữ ký. Bỏ
    hàng rào ấy mà giữ nguyên tên dòng thì lối dễ nhất là **điền hộ** — tức
    tự cấp một chứng nhận người, cho một tập không người nào đọc. Nên tên
    dòng đổi hẳn: gói khai `MÁY CHÉP:`, và bản ghi đi ra mang
    `machine_verifier`, không `human_verifier`.
    """
    IN = _nap("ingest_holdout_batch")
    assert re.search(r"^MÁY CHÉP: .+", GOI, re.M), "gói phải tự khai chép máy"
    assert not re.search(r"^NGƯỜI CHÉP:", GOI, re.M), \
        "gói KHÔNG được mang chữ ký người — không ai ký nó cả"
    r = VL.soi(GOI, SH, IN)
    assert r["loi"] == [], r["loi"]
    assert r["bai"], "gói phải đã có đề chép máy, không còn rỗng"

    # Gỡ khối reserve trước, đúng như `soi` làm: khối dự phòng còn `<...>` là
    # SỨC CHỨA, không phải việc chưa làm.
    da_dien, _ = VL.go_khoi_trong(GOI)
    nguoi, bai, loi = IN.phan_tich(da_dien, SH)
    assert loi == [], loi[:3]
    c = IN.thanh_case(next(b for b in bai if b["o"].startswith("A")), nguoi, SH)
    assert c["verification_mode"] == "MÁY-TỪ-NGUỒN"
    assert c["machine_verifier"] and "human_verifier" not in c
    assert c["measured_output_used_for_source_verification"] is False


def test_lo_mang_CA_HAI_dong_chu_ky_thi_DO(SH):
    """Hai chế độ cho cùng một lô ⇒ không bài nào biết mình thuộc chế độ nào."""
    IN = _nap("ingest_holdout_batch")
    lo = ("NGƯỜI CHÉP: Người kiểm thử · 2026-08-29 · lô test\n"
          "MÁY CHÉP: agent · 2026-08-29 · lô test\n\n"
          "[A14] Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, "
          "AB = a, AC = 2a, SA vuông góc với đáy và SA = 2a. Tính thể tích "
          "khối chóp S.ABC.\n"
          "      NGUỒN: nguồn kiểm thử · https://x\n"
          "      ĐÁP ÁN: 2/3\n"
          "      PHÉP CHUYỂN: nguồn in V = 2a³/3, chuẩn hoá a = 1 ⇒ 2/3\n")
    _, _, loi = IN.phan_tich(lo, SH)
    assert any("CẢ" in d and "LẪN" in d for d in loi), loi


def _goi_dien_mot_bai(GOI: str) -> str:
    # Ký bằng cách thay CẢ DÒNG, không thay một chuỗi cố định: nội dung mẫu
    # của dòng chữ ký đã đổi một lần theo amendment và sẽ còn đổi nữa.
    t = re.sub(r"^NGƯỜI CHÉP:.*$",
               "NGƯỜI CHÉP: Người kiểm thử · 2026-08-28 · lô test",
               GOI, count=1, flags=re.M)
    # Sau amendment, khối A14 đã mang đề chép máy — chỉ còn thiếu chữ ký.
    return t


def test_khoi_DA_DIEN_di_qua_duoc_ca_ba_cong(SH, VL, GOI):
    IN = _nap("ingest_holdout_batch")
    r = VL.soi(_goi_dien_mot_bai(GOI), SH, IN)
    assert r["loi"] == [], r["loi"]
    # Gói ĐÃ được nạp (2026-08-29), nên mọi id của nó nay trùng với pool —
    # đó là bộ dò trùng làm ĐÚNG việc, không phải lỗi gói. Khoá quan hệ:
    # tập trùng phải bằng đúng tập id đã `accepted` trong pool.
    da_co = {c["case_id"] for c in json.loads(
        (GEO / "holdout" / "pool.json").read_text(encoding="utf-8"))["cases"]}
    assert set(r["trung"]) <= da_co, set(r["trung"]) - da_co
    # Sau amendment gói đã chép máy nhiều khối, nên KHÔNG còn đúng một bài.
    # Cái cần khoá vẫn là: khối A14 đầu tiên đi qua ĐỦ BA cổng và ra đúng
    # đơn vị oracle — số khối chỉ là bối cảnh.
    a14 = [b for b in r["bai"] if b["o"] == "A14"]
    assert a14, "gói phải có ít nhất một khối A14 đã chép"
    c = IN.thanh_case(a14[0], r["nguoi"], SH)
    assert SH.check_capability_boundary(c) == [] and SH.kiem_pool([c]) == []
    assert c["oracle_result"] == {"volume": "2/3"}
    # Và mọi khối đã chép khác cũng phải qua được hai cổng tất định.
    hong = [b["ma"] for b in r["bai"]
            if SH.check_capability_boundary(IN.thanh_case(b, r["nguoi"], SH))]
    assert not hong, f"khối chép máy không qua cổng năng lực: {hong}"


def test_SIEU_DU_LIEU_cua_goi_khong_lot_vao_problem_text(SH, VL, GOI):
    IN = _nap("ingest_holdout_batch")
    de = VL.soi(_goi_dien_mot_bai(GOI), SH, IN)["bai"][0]["de"]
    for ro in ("CAPABILITY", "THANG CHẤM", "TÌM BÀI", "ĐÃ SOI", "RỦI RO", "#"):
        assert ro not in de, f"{ro!r} lọt vào đề: {de[:120]}"


@pytest.mark.parametrize("o,thieu", [("A06", "vuông góc"), ("A03", "song song"),
                                     ("A14", "thể tích")])
def test_de_MAT_ky_hieu_dac_trung_thi_canh_bao(SH, VL, GOI, o, thieu):
    """Trích PDF rơi sạch `⊥` mà văn bản vẫn đọc trôi chảy — hỏng IM LẶNG."""
    IN = _nap("ingest_holdout_batch")
    t = GOI.replace("NGƯỜI CHÉP: <tên bạn> · <YYYY-MM-DD> · <chép từ tài liệu nào>",
                    "NGƯỜI CHÉP: Người kiểm thử · 2026-08-28 · lô test")
    # Điền TRONG ĐÚNG khối của ô ấy: thay file-wide thì trúng khối đầu tiên
    # của file (A01), khối đích vẫn còn chỗ trống nên bị bỏ, và test xanh/đỏ
    # vì lý do khác hẳn thứ nó định đo.
    # Thay ĐÚNG dòng đề của khối đích bằng một đề thiếu ký hiệu đặc trưng.
    i = t.index(f"[{o}] ")
    j = t.index("\n", i)
    thay = (f"[{o}] Cho hình chóp S.ABCD có đáy là hình vuông cạnh a và cạnh "
            "bên SA bằng 2a. Hỏi kết luận nào sau đây là đúng?")
    r = VL.soi(t[:i] + thay + t[j:], SH, IN)
    assert any(thieu in c for c in r["canh"]), (thieu, r["canh"])


def test_moc_M_doc_dung_theo_so_bai_va_so_o():
    DP = _nap("run_phase7b_data_pipeline")
    assert DP.moc_hien_tai(0, 0).startswith("M0")
    assert DP.moc_hien_tai(1, 1).startswith("M1")
    assert DP.moc_hien_tai(3, 1).startswith("M2")
    assert DP.moc_hien_tai(20, 14).startswith("M3")
    assert DP.moc_hien_tai(40, 20).startswith("M4")


def test_goi_KHONG_bi_ghi_de_khi_da_ton_tai(PK, monkeypatch, capsys):
    """Gói đã điền là công sức của NGƯỜI — máy không dựng lại được."""
    monkeypatch.setattr(sys, "argv", ["x", "--ghi"])
    assert PK.RA.exists(), "gói chưa được sinh — sinh trước rồi chạy test này"
    assert PK.main() == 1
    assert "KHÔNG ghi đè" in capsys.readouterr().out


def test_PASS1_phu_19_tren_20_o_va_A12_la_o_DUY_NHAT_con_trong(PK, SH):
    """Chốt trạng thái Pass 1: 19/20 ô có ứng viên, chỉ A12 còn trống.

    Không phải test trang trí: nếu ai gỡ một ứng viên mà quên cập nhật
    `SOURCE_GAP`, gói sẽ im lặng phát một ô không có nguồn và người chép
    mất công mở tài liệu để rồi không tìm thấy gì.
    """
    trong = [o for o in SH.BANG_O if o not in PK.DA_SOI]
    assert trong == ["A12"], f"ô còn trống lệch kỳ vọng: {trong}"
    assert set(PK.SOURCE_GAP) == set(trong), \
        "SOURCE_GAP phải khớp ĐÚNG danh sách ô chưa có ứng viên"
    assert sum(len(v) for v in PK.DA_SOI.values()) >= 31


def test_moi_o_phat_DU_khoi_cho_so_ung_vien_da_co(PK):
    """`PHAT[o]` phải ≥ số ứng viên của ô — nếu không, ứng viên bị rơi lặng."""
    for o, v in PK.DA_SOI.items():
        assert PK.PHAT[o] >= len(v), \
            f"{o}: có {len(v)} ứng viên nhưng chỉ phát {PK.PHAT[o]} khối"


# ══ VALIDATOR PHẢI TÁCH "CẦN CHÉP" KHỎI "RESERVE" ════════════════════════
def test_validator_KHONG_dem_khoi_reserve_thanh_viec_phai_lam(PK, VL, SH, GOI):
    r"""Gói 51 khối / 42 ứng viên: khối reserve KHÔNG phải việc của người chép.

    Bản trước gộp cả hai thành một số "còn trống" nên báo 50 việc khi chỉ còn
    41 — đếm sai theo hướng làm nản. Nguyên nhân là `\s*` quay lui vô hiệu
    hoá lookahead `(?!<)`, khiến `NGUỒN: <…>` của khối reserve vẫn khớp.
    """
    IN = _nap("ingest_holdout_batch")
    t = GOI.replace("NGƯỜI CHÉP: <tên bạn> · <YYYY-MM-DD> · <chép từ tài liệu nào>",
                    "NGƯỜI CHÉP: Người kiểm thử · 2026-08-28 · lô test")
    r = VL.soi(t, SH, IN)
    ung_vien = sum(len(v) for v in PK.DA_SOI.values())
    assert len(r["can_chep"]) + len(r["bai"]) == ung_vien, \
        "đã chép + còn phải chép phải bằng ĐÚNG số ứng viên"
    assert r["reserve"] == sum(PK.PHAT.values()) - ung_vien
    assert r["reserve"] > 0, "gói phải còn khối dự phòng"


def test_bo_hoan_tat_KHONG_lap_lai_nghiep_vu_cua_duong_ong(PK):
    """`finalize` chỉ được ORCHESTRATE — nghiệp vụ nằm ở script gốc."""
    src = (SCRIPTS / "finalize_phase7b_holdout.py").read_text(encoding="utf-8")
    assert "DP.main()" in src, "phải gọi lại run_phase7b_data_pipeline"
    # Đo LỜI GỌI, không đo chữ: tên hàm nhắc trong docstring là giải thích,
    # không phải chép nghiệp vụ. Đo thô thì test đỏ vì một câu văn.
    for cam in ("check_capability_boundary", "kiem_pool", "eval_geometry_expr"):
        assert not re.search(rf"\b\w*\.?{cam}\s*\(", src), \
            f"{cam}() bị GỌI trong bộ hoàn tất — nghiệp vụ phải ở script gốc"


# ══ MỌI ỨNG VIÊN PHẢI TRA NGƯỢC ĐƯỢC ═════════════════════════════════════
def test_moi_ung_vien_co_URL_hoac_la_SACH_IN(PK):
    """Nguồn phải tra ngược được: hoặc có URL, hoặc là SGK/SBT (sách in).

    Không phải luật hình thức. `HOLDOUT_PROTOCOL §3①` đòi nguồn công khai, và
    `kiem_pool` đòi `nguon.url`; một ứng viên chỉ ghi tên trang mà không có
    đường dẫn thì người sau không tra lại được lời giải để kiểm đáp án — đúng
    chỗ đã làm hỏng ứng viên A12 (đáp án nguồn khác đáp án ta tính).
    """
    thieu = [(o, c["nguon"][:60]) for o, v in PK.DA_SOI.items() for c in v
             if "http" not in c["nguon"]
             and not re.search(r"\bSGK\b|\bSBT\b", c["nguon"])]
    assert not thieu, f"ứng viên không tra ngược được: {thieu}"


def test_moi_ung_vien_khai_DU_vi_tri_trong_nguon(PK):
    """Phải chỉ được đúng bài: trang / Câu / Bài / Dạng / Ví dụ."""
    mo = [(o, c["nguon"][:60]) for o, v in PK.DA_SOI.items() for c in v
          if not re.search(r"tr(ang)? ?PDF? ?\d|Bài [\d.]+|Câu \d|Dạng \d|Ví dụ",
                           c["nguon"])]
    assert not mo, f"ứng viên không chỉ rõ vị trí bài: {mo}"


# ══ KHOÁ AN TOÀN: HELD-OUT KHÔNG ĐƯỢC QUA MODEL TRƯỚC KHI NIÊM PHONG ═════
#
# Rủi ro có thật chứ không giả định: `run_geometry_dev_evaluation.py --holdout`
# GỌI MODEL và CÓ chạm miền held-out. Nếu nó chạy trước `seal`, 42 ứng viên
# công khai đi qua measured system một lượt không ai đếm — và không có cách nào
# lấy lại tính held-out sau đó. Ba khoá dưới đây phải còn nguyên và đúng THỨ TỰ.
_RUNNER = "run_geometry_dev_evaluation.py"


def test_bo_chay_MODEL_doc_cases_da_rut_chu_KHONG_doc_pool():
    """Runner chỉ được đọc `holdout/cases.json` (tập ĐÃ RÚT), không đọc pool.

    Pool là 42 ứng viên; `cases.json` là 20 bài seed đã chọn. Cho runner thấy
    pool là cho nó thấy gấp đôi tập đo, kể cả bài không bao giờ được rút.
    """
    src = (SCRIPTS / _RUNNER).read_text(encoding="utf-8")
    assert 'HOLDOUT = GEO / "holdout" / "cases.json"' in src
    assert "pool.json" not in src, "runner model KHÔNG được biết tới pool.json"


def test_bo_chay_MODEL_kiem_con_dau_TRUOC_khi_cham_api():
    """Thứ tự quan trọng hơn sự tồn tại: cổng con dấu phải đứng TRƯỚC bước
    đòi live/API key, nếu không thì quota đã tiêu trước khi cổng kịp chặn."""
    # Đo trong THÂN `_main`, và đo LỜI GỌI: `src.index("_bat_buoc_live(")`
    # trúng dòng ĐỊNH NGHĨA ở đầu file nên so ra thứ tự ngược.
    src = (SCRIPTS / _RUNNER).read_text(encoding="utf-8")
    than = src[src.index("async def _main("):]
    i_dau = than.index("_kiem_con_dau(cases)")
    i_live = than.index("\n    _bat_buoc_live(")
    i_key = than.index('os.environ.get("GEMINI_API_KEY")')
    assert i_dau < i_live < i_key, "cổng con dấu bị đẩy xuống sau bước tiêu quota"


def test_khong_co_con_dau_thi_TU_CHOI_chay_holdout():
    """Tiêm lỗi: chưa niêm phong ⇒ phải ném, không phải cảnh báo rồi chạy."""
    import importlib.util as _iu
    sp = _iu.spec_from_file_location("_rg", SCRIPTS / _RUNNER)
    m = _iu.module_from_spec(sp)
    sp.loader.exec_module(m)
    # TIÊM LỖI, không chờ hiện trường: trỏ đường dẫn con dấu sang chỗ không
    # có. Bản trước dựa vào việc kho CHƯA niêm phong, nên nó tự vô hiệu hoá
    # đúng vào ngày niêm phong — tức guard mất tác dụng đúng lúc cần nhất.
    m.HOLDOUT_SEAL = Path(str(m.HOLDOUT_SEAL) + ".khong-ton-tai")
    assert not m.HOLDOUT_SEAL.exists()
    with pytest.raises(Exception) as e:
        m._kiem_con_dau([{"case_id": "hp_a14_001"}])
    assert "con dấu" in str(e.value).lower()


def test_chuoi_FINALIZE_khong_module_nao_cham_model():
    """Toàn bộ dây chuyền nạp gói phải TẤT ĐỊNH — 0 API call, kể cả gián tiếp."""
    chuoi = ("finalize_phase7b_holdout", "run_phase7b_data_pipeline",
             "run_m1_pipeline", "ingest_holdout_batch", "seal_geometry_holdout",
             "scaffold_expectation", "freeze_expectation_check",
             "holdout_coverage_matrix", "validate_human_copy_packet")
    for ten in chuoi:
        src = (SCRIPTS / f"{ten}.py").read_text(encoding="utf-8")
        ma = "\n".join(d for d in src.splitlines()
                       if not d.lstrip().startswith("#"))
        for cam in ("app.ai.gemini", "from app.ai import", "run_pipeline(",
                    "ALLOW_LIVE_AI"):
            assert cam not in ma, f"{ten} chạm {cam!r} — dây chuyền hết tất định"


def test_DEV_smoke_KHONG_giao_voi_ung_vien_holdout(PK):
    """Muốn smoke chuỗi model→mô phỏng thì dùng DEV, và DEV phải RỜI hẳn.

    `geo_*` (DEV) vs `hp_*` (held-out): hai không gian tên tách biệt, nên một
    ca smoke không thể vô tình là một bài của tập đo.
    """
    dev = json.loads((GEO / "dev" / "cases.json").read_text(encoding="utf-8"))
    ids = {c["case_id"] for c in dev["cases"]}
    assert ids and all(i.startswith("geo_") for i in ids)
    pool = json.loads(POOL.read_text(encoding="utf-8"))["cases"]
    assert not (ids & {c["case_id"] for c in pool})


# ══ KHOÁ ORACLE PHẢI PHỦ ĐỦ TÁM NGHĨA VỤ ═════════════════════════════════
def test_khoa_oracle_phu_DU_moi_o_tang_A(SH):
    """`_khoa_oracle` phải dẫn từ `BANG_O`, không phải bảng chép tay.

    Bản chép tay cũ chỉ có bốn thẻ ĐO LƯỜNG và thiếu năm nghĩa vụ MỆNH ĐỀ
    (`point_on_line`, `point_on_plane`, `parallel`, `perpendicular`,
    `coplanar`). Đo được hậu quả: **21/41 ứng viên** — toàn bộ A01–A08 và
    A13 — rớt `kiem_pool` với *"tầng A phải có oracle_result"*, vì
    `thanh_case` chỉ dựng `oracle_result` và `phep_chuyen` khi có khoá.

    Bug sống sót lâu vì chưa ca mệnh đề nào từng đi qua ingest — mọi ứng viên
    trước đều là bài đo lường.
    """
    IN = _nap("ingest_holdout_batch")
    for o in SH.BANG_O:
        khoa = IN._khoa_oracle(SH, o)
        if o.startswith("A"):
            assert khoa == SH.BANG_O[o][0], f"{o}: khoá lệch BANG_O"
            assert khoa, f"{o}: ô tầng A mà không có khoá oracle"
        else:
            assert khoa is None, f"{o}: ô tầng B không được có khoá oracle"


def test_bai_MENH_DE_dung_qua_duoc_kiem_pool(SH):
    """Ca hồi quy trực tiếp: một bài A03 (`parallel`, đáp án `true`) phải qua."""
    IN = _nap("ingest_holdout_batch")
    lo = ("NGƯỜI CHÉP: Người kiểm thử · 2026-08-28 · lô test\n\n"
          "[A03] Cho tứ diện ABCD có I, J lần lượt là trọng tâm của tam giác "
          "ABC, ABD. Chứng minh rằng IJ song song CD.\n"
          "      NGUỒN: nguồn kiểm thử · https://x\n"
          "      ĐÁP ÁN: true\n"
          "      PHÉP CHUYỂN: nguồn khẳng định IJ ∥ CD ⇒ `parallel` = true\n")
    nguoi, bai, loi = IN.phan_tich(lo, SH)
    assert loi == [], loi
    c = IN.thanh_case(bai[0], nguoi, SH)
    assert c["oracle_result"] == {"parallel": "true"}, c.get("oracle_result")
    assert SH.check_capability_boundary(c) == [] and SH.kiem_pool([c]) == []


# ══ ĐỀ PHẢI THUỘC VỀ ĐÚNG TRÍCH DẪN ĐỨNG CẠNH NÓ ═════════════════════════
#
# Lớp bug tệ nhất của cả wave: `de` được gán theo **chỉ số** trong `DA_SOI[o]`
# còn `nguon` viết cùng dict. Mỗi lần chèn ứng viên mới vào ĐẦU danh sách,
# chỉ số dịch và đề dính sang trích dẫn khác — **18/41 bản ghi ghép chéo**.
# Một held-out mà `problem_text` không thuộc `source_citation` thì toàn bộ
# bộ máy xuất xứ trở thành trang trí: đáp án nguồn chấm một bài, mô hình đọc
# một bài khác.
#
# `BAN_CHEP` khoá theo chuỗi nguồn đã xoá *cơ chế* sinh lệch. Bảng dưới khoá
# *kết quả*: từng cặp đã soi tận trang, neo bằng một mẩu chữ chỉ có ở đúng
# bài đó. Đổi bản chép mà quên đổi neo ⇒ ĐỎ.
#
# Khoá nguồn ở đây (`"Câu 2"`, `"Câu 1"`…) KHÔNG duy nhất toàn cục — đó là
# lý do vòng ghép-theo-nội-dung trước sửa được 11 ca rồi ghép sai lại 3 ca.
# Ở đây chúng chỉ cần duy nhất **trong một vị trí đã biết**, nên đủ.
_NEO_NGUON_DE: dict[tuple[str, int], tuple[str, str]] = {
    ("A01", 0): ("Bài 3 trang 106", "Tìm giao tuyến của (SCD) và (SAB)"),
    ("A01", 1): ("Câu 3", "G là trọng tâm tam giác BCD"),
    ("A01", 2): ("Câu 5", "trung điểm AD và BC"),
    ("A02", 0): ("Bài 4.6", "G là trọng tâm tam giác SCD"),
    ("A02", 1): ("Câu 13", "AC và BD giao nhau tại O"),
    ("A02", 2): ("Câu 12", "bốn điểm A, B, C, D không đồng phẳng"),
    # tr PDF 100 của tài liệu CTST 410tr: Câu 1 = IJ//CD, Câu 2 = MPNQ.
    ("A03", 0): ("Câu 2", "MPNQ là hình bình hành"),
    ("A03", 1): ("Câu 1", "IJ // CD"),
    ("A04", 0): ("Bài 4.44", "trọng tâm của tam giác SAD"),
    ("A04", 1): ("Bài 32", "SM/SA"),
    ("A04", 2): ("Bài 31", "G1"),
    ("A05", 0): ("Bài 4.17", "AD = 2BC"),
    ("A05", 1): ("Câu 4", "(MNP) // (ABC)"),
    # A06: `nguon` tự ghi ý nào — lệch nhìn thấy được trong chính bản ghi.
    ("A06", 0): ("ý `AC ⊥ B'D'`", "AC ⊥ B'D'"),
    ("A06", 1): ("ý `AB ⊥ CC'`", "AB ⊥ CC'"),
    ("A07", 0): ("Câu 1", "BC ⊥ (OAH)"),
    ("A07", 1): ("Câu 2", "AH ⊥ (SBC)"),
    ("A08", 0): ("Câu 1", "(SAB) ⊥ (ABC)"),
    ("A08", 1): ("Câu 2", "(ACC'A')"),
    ("A09", 0): ("Câu 13", "A'D và B'I"),
    ("A09", 1): ("ý c", "A'C' và B'C"),
    ("A09", 2): ("ý b", "AC và B'C'"),
    ("A10", 0): ("Câu 2", "(BCC'B')"),
    ("A10", 1): ("Câu 5", "hình thoi ABCD tâm O"),
    ("A11", 0): ("Ví dụ 2", "SA = 3a/5"),
    ("A11", 1): ("Câu 7", "vuông tại B"),
    ("A13", 0): ("ý b", "(MNP)"),
    ("A13", 1): ("ý a", "(PAB)"),
    ("A14", 0): ("trang PDF 80", "AC = 2a"),
    ("A14", 1): ("trang PDF 91", "(SBD)"),
    ("B01", 0): ("Câu 26", "tam giác đều cạnh a"),
    ("B01", 1): ("Câu 28", "AA1"),
    ("B02", 0): ("Bài 7.27", "(A'B'C'D')"),
    ("B03", 0): ("Câu 4", "Memphis"),
    ("B03", 1): ("Câu 6", "[C,BD,A']"),
    ("B04", 0): ("Dạng 5", "M(-1;-2;5)"),
    ("B04", 1): ("Dạng 4", "A(1;2;-2)"),
    ("B05", 0): ("Dạng 1, Câu 2", "r = 3cm và đường sinh l = 5cm"),
    ("B05", 1): ("Câu 1 **ý a)", "tam giác SOA vuông tại O"),
    ("B06", 0): ("VẬN DỤNG", "trọng tâm tam giác ABC"),
    ("B06", 1): ("NHẬN BIẾT", "phương chiếu SA"),
}


def test_bang_neo_phu_HET_ung_vien_da_soi(PK):
    """Neo phải phủ 100% — thêm ứng viên mà quên neo là mở lại đúng lỗ cũ."""
    that = {(o, i) for o, ds in PK.DA_SOI.items() for i in range(len(ds))}
    assert set(_NEO_NGUON_DE) == that, {
        "thiếu neo": sorted(that - set(_NEO_NGUON_DE)),
        "neo thừa": sorted(set(_NEO_NGUON_DE) - that),
    }


@pytest.mark.parametrize("vi_tri", sorted(_NEO_NGUON_DE))
def test_de_thuoc_ve_dung_trich_dan_dung_canh_no(PK, vi_tri):
    o, i = vi_tri
    mau_nguon, mau_de = _NEO_NGUON_DE[vi_tri]
    ung = PK.DA_SOI[o][i]
    assert mau_nguon in ung["nguon"], f"{o}#{i}: nguồn không còn chứa {mau_nguon!r}"
    de = PK.BAN_CHEP[PK._khoa_chep(ung["nguon"])]["de"]
    assert mau_de in de, f"{o}#{i} [{mau_nguon}]: đề không nói {mau_de!r} → {de[:90]!r}"


def test_moi_ung_vien_TRA_DUOC_ban_chep_va_khong_co_muc_mo_coi(PK):
    """Song ánh `nguon` ⇄ `BAN_CHEP`: không mục mồ côi, không khoá đụng nhau."""
    khoa = [PK._khoa_chep(c["nguon"]) for ds in PK.DA_SOI.values() for c in ds]
    assert len(set(khoa)) == len(khoa), "hai ứng viên chung một khoá nguồn"
    assert set(khoa) == set(PK.BAN_CHEP), {
        "chưa có bản chép": sorted(set(khoa) - set(PK.BAN_CHEP)),
        "bản chép mồ côi": sorted(set(PK.BAN_CHEP) - set(khoa)),
    }


# ══ PHÉP CHUYỂN PHẢI NÓI VỀ ĐÚNG BÀI, KHÔNG PHẢI CÂU SINH SẴN ════════════
def test_tang_A_THIEU_phep_chuyen_thi_bi_chan(IN, SH):
    lo = _LO.replace("      PHÉP CHUYỂN: nguồn in V = 4 (đã là phân số) — "
                     "vào thẳng `volume`\n", "")
    _, _, loi = IN.phan_tich(lo, SH)
    assert any("PHÉP CHUYỂN" in x for x in loi), loi


def test_tang_B_MANG_phep_chuyen_thi_bi_chan(IN, SH):
    """Tầng B không có `oracle_result` ⇒ không có đơn vị nào để chuyển sang."""
    lo = ("NGƯỜI CHÉP: Người kiểm thử · 2026-08-28 · lô test\n\n"
          "[B05] Cho hình nón có bán kính đáy r = 3 và chiều cao h = 4. "
          "Tính diện tích xung quanh của hình nón đó.\n"
          "      NGUỒN: nguồn kiểm thử · https://x\n"
          "      PHÉP CHUYỂN: nguồn in 15π\n"
          "      NGOÀI PHỦ VÌ: mặt cong — kernel chỉ dựng khối đa diện lồi\n")
    _, _, loi = IN.phan_tich(lo, SH)
    assert any("PHÉP CHUYỂN" in x and "tầng A" in x for x in loi), loi


def test_dong_phep_chuyen_KHONG_chui_vao_de(IN, SH):
    """Sót một dòng siêu dữ liệu là đề gửi cho mô hình mang sẵn đáp án."""
    _, bai, loi = IN.phan_tich(_LO, SH)
    assert loi == [], loi
    assert "PHÉP CHUYỂN" not in bai[0]["de"] and "volume" not in bai[0]["de"]


def test_phep_chuyen_LA_dong_nguoi_khai_khong_phai_cau_sinh_san(IN, SH):
    """Trường này từng là MỘT câu giống hệt nhau cho mọi bài.

    Câu ấy khẳng định *"đáp án nguồn chép thẳng vào đơn vị checker"* — sai ở
    đúng những ca cần đúng nhất (A09 `cos → cos²`, A14 `a³ → a=1`, A03 *hình
    bình hành* → `∥`), và sai bên trong artifact ĐÃ NIÊM PHONG. `seal` chỉ
    kiểm trường CÓ MẶT nên câu sinh sẵn đi lọt tuyệt đối im lặng.
    """
    _, bai, _ = IN.phan_tich(_LO, SH)
    c = IN.thanh_case(bai[0], "Người kiểm thử", SH)
    assert c["phep_chuyen"] == bai[0]["chuyen"]
    assert "chép thẳng vào đơn vị checker" not in c["phep_chuyen"]


def test_moi_ung_vien_TANG_A_deu_da_co_phep_chuyen_soan_san(PK):
    for o, ds in PK.DA_SOI.items():
        for i, c in enumerate(ds):
            chep = PK.BAN_CHEP[PK._khoa_chep(c["nguon"])]
            if o.startswith("A"):
                assert chep.get("chuyen"), f"{o}#{i}: tầng A thiếu phép chuyển"
            else:
                assert "chuyen" not in chep, f"{o}#{i}: tầng B không được có"


@pytest.mark.parametrize("i", (0, 1))
def test_phep_chuyen_cua_A10_phai_NOI_RA_bay_sin_binh(PK, i):
    """A10 là góc đường–MẶT ⇒ **sin²**, còn A09 là cos². Bẫy im lặng của bảng ô
    chỉ vô hại khi mỗi bài A10 tự mang lời cảnh báo ấy."""
    c = PK.DA_SOI["A10"][i]
    t = PK.BAN_CHEP[PK._khoa_chep(c["nguon"])]["chuyen"]
    assert "sin²" in t and "cos²" in t, t


# ══ BÀI SOẠN NỘI BỘ: NHẬN, NHƯNG PHẢI MANG ĐÚNG TÊN CỦA NÓ ═══════════════
#
# Ô A12 (khoảng cách điểm–ĐƯỜNG, đáp án hữu tỉ) không lấp được bằng nguồn
# công khai: 3 lượt quét / 673 url / 9 tài liệu, hai ứng viên gần nhất đều
# rớt. Giao thức thì cấm rút bù từ ô khác. Nên nó được lấp bằng một bài TỰ
# SOẠN — và cả nhóm test này tồn tại để bài ấy không bao giờ đọc được như 19
# bài kia.
def _bai_curated(**doi) -> dict:
    c = {"case_id": "hp_a12_001", "status": "accepted", "slot": "A12",
         "capability_tag": "rational_distance", "answer_shape": "exact_fraction",
         "problem_text": "đề tự soạn", "problem_text_original": "đề tự soạn",
         "problem_text_verified": True, "verification_mode": "SOẠN-NỘI-BỘ",
         "internal_author": "tác giả khoá luận", "curated_preseal": True,
         "han_che": "KHÔNG phải held-out — xem A12_CURATED_DERIVATION.md",
         "suy_dan": ["① hệ thức lượng", "② tích có hướng", "③ oracle custodian"],
         "measured_output_used_for_source_verification": False,
         "nguon": {"ten": "SOẠN NỘI BỘ", "url": "", "vi_tri": "SOẠN NỘI BỘ",
                   "loai": "soan_noi_bo"},
         "dap_an_chinh_thuc": "12/5", "phep_chuyen": "ba suy dẫn đồng thuận",
         "oracle_result": {"distance": "12/5"}, "oracle_ref": "distance",
         "expected_obligations": ["distance"], "chua_chay_he": True,
         "domain_condition": "SB hữu tỉ vì tam giác SAB vuông có ba cạnh 3-4-5"}
    c.update(doi)
    return c


def test_bai_SOAN_NOI_BO_hop_le_thi_qua(SH):
    assert SH.kiem_pool([_bai_curated()]) == []


def test_bai_TU_SOAN_khong_duoc_DOI_LOT_nguon_ngoai(SH):
    """Bài tự soạn khai `loai: web` là mất sạch giá trị của cả bộ máy xuất xứ."""
    b = _bai_curated()
    b["nguon"] = {**b["nguon"], "loai": "web", "url": "https://x"}
    loi = SH.kiem_pool([b])
    assert loi and "đội lốt" in loi[0], loi


def test_bai_TU_SOAN_phai_TU_KHAI_han_che(SH):
    b = _bai_curated()
    b.pop("han_che")
    loi = SH.kiem_pool([b])
    assert loi and "han_che" in loi[0], loi


@pytest.mark.parametrize("sd", ([], ["chỉ một cách"]))
def test_bai_TU_SOAN_can_IT_NHAT_HAI_suy_dan_doc_lap(SH, sd):
    """Không nguồn ngoài ⇒ đáp án phải đến từ ≥2 cách. MỘT cách tự đồng ý với
    chính nó, và đó là toàn bộ vấn đề."""
    loi = SH.kiem_pool([_bai_curated(suy_dan=sd)])
    assert any("suy dẫn" in x or "suy_dan" in x for x in loi), loi


def test_TRAN_bai_tu_soan_la_DUNG_MOT(SH):
    """Ngoại lệ không có trần thì không còn là ngoại lệ.

    Lối rẻ nhất để "phủ đủ 20/20 ô" sẽ là tự soạn nốt phần khó — và tập
    held-out biến thành tập tự viết mà vẫn mang tên held-out.
    """
    hai = [_bai_curated(), _bai_curated(case_id="hp_a12_002", slot="A12")]
    loi = SH.kiem_pool(hai)
    assert any("trần là ĐÚNG MỘT" in x for x in loi), loi


def test_pool_THAT_co_DUNG_MOT_bai_tu_soan_va_no_o_o_A12(POOL_D):
    ts = [c for c in POOL_D["cases"] if c.get("curated_preseal")]
    assert len(ts) == 1, [c["case_id"] for c in ts]
    c = ts[0]
    assert c["slot"] == "A12"
    assert "human_verifier" not in c and "machine_verifier" not in c, \
        "bài tự soạn KHÔNG được mang chữ ký người hay dấu chép-từ-nguồn"
    assert len(c["suy_dan"]) >= 2
    assert c["measured_output_used_for_source_verification"] is False, \
        "đáp án suy dẫn bằng oracle custodian (bộ ĐO), KHÔNG bằng kernel"


def test_bien_ban_suy_dan_A12_ton_tai_va_KHAI_dung_cai_mat(POOL_D):
    f = GEO / "holdout" / "A12_CURATED_DERIVATION.md"
    assert f.exists(), "bài tự soạn mà không có biên bản suy dẫn"
    src = f.read_text(encoding="utf-8")
    # Ba mẩu này là lý do file tồn tại — mất mẩu nào thì nó thành lời quảng cáo.
    assert "KHÔNG** phải held-out" in src or "không** phải held-out" in src
    assert "19/20" in src and "20/20" in src, "phải nêu số ĐO HAI LẦN"
    assert "backend/app/simulation/geometry" in src, \
        "phải khai rõ đã KHÔNG dùng kernel để soạn đáp án"


def test_khong_hai_ung_vien_nao_dung_chung_mot_DE(PK):
    """Hoán vị sai kiểu 'copy đè' lộ ra ở đây: hai ô cùng một đề."""
    thay: dict[str, tuple[str, int]] = {}
    for o, ds in PK.DA_SOI.items():
        for i, c in enumerate(ds):
            de = PK.BAN_CHEP[PK._khoa_chep(c["nguon"])]["de"]
            assert de not in thay, f"{o}#{i} trùng đề với {thay[de]}"
            thay[de] = (o, i)
