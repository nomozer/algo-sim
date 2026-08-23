# -*- coding: utf-8 -*-
"""`derived_sequence` KHÔNG được cho qua bằng một nghĩa vụ tự thoả mãn rỗng.

─── SỰ CỐ ĐO ĐƯỢC (probe E2E `serve`, 2026-08-23) ─────────────────────────

Đề *"Cho dãy 5, 2, 8, 1 — dùng ngăn xếp để đảo ngược"* được route sinh **PHÁT
ĐI** (`status=ok`, `source=semantic_program`, 5 khung). Envelope phát đi, khung
cuối:

    ngan_xep.items        = []
    day_so_dao_nguoc.items = []
    phan_tu_box.value      = ""

Tức: học sinh bấm hết 5 bước, lời kể chạy tới *"Xét phần tử: p = '1'"*, mà ngăn
xếp rỗng suốt và **đáp án không bao giờ hiện**. `servable = True`.

Nguyên nhân: checker đọc nguồn từ `ob.params["src"]`. Nghĩa vụ khai
`derived_sequence(container='day_so', witness='day_so_dao_nguoc')` — đúng hình
dạng taxonomy — nhưng không có `src`, nên `snap.get("")` ra None, `_phang` ra
`[]`, `transform` mặc định `identity` cho `want = []`, và `[] == []` **cho qua**.

Đây là chiều **IM LẶNG CHẤP NHẬN** của cùng lớp "nghĩa vụ vô hiệu" mà
`T11CS-C6-041` phơi ra ở chiều tố cáo sai (xem
`test_vacuous_obligation_diagnosis.py`). Chiều này nguy hiểm hơn: nó không kêu
lên, và thứ đi ra là một mô phỏng dạy sai — đúng thứ `CORRECTNESS.md §1` cấm.

─── HAI VẾ, KHÔNG TÁCH RỜI ────────────────────────────────────────────────

Vế một: nguồn rỗng ⇒ VÔ HIỆU, không được pass.
Vế hai: nguồn CÓ dữ liệu thì checker phải vẫn kiểm THẬT — bắt đúng khi witness
sai, và im lặng khi witness đúng. Sửa vế một mà làm hỏng vế hai là đổi một lỗ
lấy một lỗ khác.
"""
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.postconditions import _derived_sequence


def _ob(**params) -> Obligation:
    """`witness` là PROPERTY đọc từ `params`, không phải field — nên nó phải nằm
    trong params. Gộp chứ không thay, nếu không mỗi lần đổi `transform` là mất
    witness và test tự dựng một nghĩa vụ không giống thứ đang chạy thật."""
    p = {"witness": "day_so_dao_nguoc", "transform": "reverse"}
    p.update(params)
    return Obligation(kind="derived_sequence", container="day_so", params=p)


# ── Vế một: vô hiệu KHÔNG được pass ───────────────────────────────────────
def test_nguon_rong_bi_goi_la_nghia_vu_vo_hieu():
    """Đúng hình dạng đã được PHÁT ĐI trên đường sản phẩm."""
    snap = {"day_so": [], "day_so_dao_nguoc": []}
    loi = _derived_sequence(snap, _ob())
    assert loi is not None, "nghĩa vụ tự thoả mãn rỗng KHÔNG được cho qua"
    assert "VÔ HIỆU" in loi


def test_nguon_khong_ton_tai_trong_bo_nho_cung_la_vo_hieu():
    snap = {"day_so_dao_nguoc": []}
    loi = _derived_sequence(snap, _ob())
    assert loi is not None and "VÔ HIỆU" in loi


def test_thieu_params_src_thi_lay_container_lam_nguon():
    """Chính ca đã lọt: không có `params.src`, nhưng container CÓ dữ liệu.

    Trước bản vá, nhánh này cho qua vì `want` dựng từ tập rỗng.
    """
    snap = {"day_so": [5, 2, 8, 1], "day_so_dao_nguoc": []}
    loi = _derived_sequence(snap, _ob())
    assert loi is not None, "witness rỗng trong khi nguồn có 4 phần tử phải bị bắt"
    assert "[1, 8, 2, 5]" in loi.replace("'", "")


# ── Vế hai: nguồn có dữ liệu thì vẫn kiểm THẬT ────────────────────────────
def test_dao_dung_thi_khong_bao_loi():
    snap = {"day_so": [5, 2, 8, 1], "day_so_dao_nguoc": [1, 8, 2, 5]}
    assert _derived_sequence(snap, _ob()) is None


def test_dao_sai_thi_bao_loi():
    snap = {"day_so": [5, 2, 8, 1], "day_so_dao_nguoc": [5, 2, 8, 1]}
    assert _derived_sequence(snap, _ob()) is not None


def test_params_src_van_duoc_ton_trong_khi_co():
    """`src` tường minh vẫn thắng container — không phá hành vi đang có."""
    snap = {"day_so": [9, 9], "nguon_that": [5, 2], "day_so_dao_nguoc": [2, 5]}
    ob = _ob(src="nguon_that")
    assert _derived_sequence(snap, ob) is None


def test_identity_van_kiem_that():
    snap = {"day_so": [1, 2, 3], "day_so_dao_nguoc": [1, 2, 3]}
    ob = _ob(transform="identity")
    assert _derived_sequence(snap, ob) is None
    snap_sai = {"day_so": [1, 2, 3], "day_so_dao_nguoc": [3, 2, 1]}
    assert _derived_sequence(snap_sai, ob) is not None
