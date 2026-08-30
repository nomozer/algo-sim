# -*- coding: utf-8 -*-
"""WAVE 1 sau Phase 7B — nghĩa vụ phải NỐI ĐƯỢC tới oracle, cả tám loại.

Lượt chính thức để lộ 9 lượt `oracle = UNGRADED` ở tầng A: nghĩa vụ chạy
được nhưng **không nối được tới một khoá oracle**, nên chỉ số ② không chấm
nổi. Ba lượt A01 (`point_on_line`) và sáu lượt A09/A10 (`angle`).

Sáu lượt góc là **hệ quả** của lỗi `scope` (không có hợp đồng nào để nối —
xem `test_wave1_scope_goc`). Ba lượt A01 là chuyện khác: mô hình khai một
`kind` khác với `kind` mà đề đòi.

─── VÌ SAO FILE NÀY KIỂM CẤU TRÚC, KHÔNG KIỂM SỐ ─────────────────────────

`§6` đòi *"canonical obligation taxonomy là nguồn sự thật DUY NHẤT — đừng
nuôi thêm một bảng ánh xạ chép tay từng phần"*. Đã có một bảng như thế và nó
đã hỏng thật: `_khoa_oracle` của bộ nạp từng là dict viết tay chỉ có bốn thẻ
ĐO LƯỜNG, thiếu năm nghĩa vụ MỆNH ĐỀ, và 21/41 ứng viên rớt oan.

Nên các test dưới đây **dẫn** danh sách từ `GEOMETRY_CHECKERS` rồi bắt mọi
bảng khác khớp nó — thêm một loại nghĩa vụ mà quên một bảng là ĐỎ ở đây,
không phải đỏ ở một lượt đo đã tiêu quota.
"""
from __future__ import annotations

import importlib.util
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from app.simulation.semantic_program.coverage_gate import _QUAN_HE_HINH_HOC
from app.simulation.semantic_program.geometry_obligations import (
    GEOMETRY_CHECKERS,
)

BACKEND = Path(__file__).resolve().parents[2]

#: Chín mục §6 đòi phủ. Tám `kind` cộng phép tách đơn vị của `angle`.
#: `section_matches` thêm 2026-08-30 ⇒ CHÍN kind.
TAM_LOAI = ("point_on_line", "point_on_plane", "parallel", "perpendicular",
            "coplanar", "section_matches", "angle", "distance", "volume")

#: Kind KHÔNG có ô nào trong `BANG_O` đo tới, kèm LÝ DO — danh sách này chỉ
#: được phép ngắn đi.
#:
#: `section_matches` ra đời SAU khi tập held-out đã niêm phong. Ô A13 hiện đo
#: thiết diện bằng `coplanar` — đúng cái yếu mà nghĩa vụ mới sinh ra để thay.
#: Thêm một ô, hoặc gắn lại nhãn cho A13, đều là **sửa dụng cụ đo sau khi đã
#: niêm phong**, nên không làm. Hệ quả phải khai thẳng: trên tập held-out,
#: thiết diện vẫn được chấm bằng phép kiểm YẾU.
KHONG_CO_O_DO = {
    "section_matches": "sinh sau khi held-out niêm phong; ô A13 vẫn dùng "
                       "`coplanar` — không sửa dụng cụ đo đã niêm phong",
}


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        ten, BACKEND / "scripts" / f"{ten}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[ten] = m
    spec.loader.exec_module(m)
    return m


def test_taxonomy_chinh_tac_dung_TAM_loai():
    assert set(GEOMETRY_CHECKERS) == set(TAM_LOAI)


def test_QUAN_HE_va_DAI_LUONG_chia_het_taxonomy():
    """BA nhóm không giao nhau và phủ kín — không loại nào rơi ra ngoài.

    Nhóm thứ ba (CẤU TRÚC) thêm 2026-08-30 cùng `section_matches`: nó không
    trả đúng/sai về một quan hệ, cũng không trả một con số — nó hỏi chủ thể có
    BẰNG vật mà server dựng lại được không.
    """
    from app.simulation.semantic_program.coverage_gate import _CAU_TRUC_HINH_HOC

    dai_luong = set(GEOMETRY_CHECKERS) - _QUAN_HE_HINH_HOC - _CAU_TRUC_HINH_HOC
    assert _QUAN_HE_HINH_HOC <= set(GEOMETRY_CHECKERS)
    assert _CAU_TRUC_HINH_HOC <= set(GEOMETRY_CHECKERS)
    assert not (_QUAN_HE_HINH_HOC & _CAU_TRUC_HINH_HOC)
    assert dai_luong == {"distance", "angle", "volume"}
    assert _QUAN_HE_HINH_HOC | _CAU_TRUC_HINH_HOC | dai_luong \
        == set(GEOMETRY_CHECKERS)


def test_BANG_O_chi_dung_kind_co_trong_taxonomy():
    """Bảng 20 ô của bộ đo không được khai một nghĩa vụ không ai chấm nổi."""
    SH = _nap("seal_geometry_holdout")
    dung = {nv for nv, _ in SH.BANG_O.values() if nv}
    assert dung <= set(GEOMETRY_CHECKERS), dung - set(GEOMETRY_CHECKERS)


def test_moi_kind_TANG_A_deu_co_o_trong_BANG_O():
    """Chiều ngược lại: có checker mà không ô nào đo thì loại ấy không bao giờ
    được kiểm trên held-out, và chỗ trống ấy phải thấy được."""
    SH = _nap("seal_geometry_holdout")
    dung = {nv for nv, _ in SH.BANG_O.values() if nv}
    assert set(GEOMETRY_CHECKERS) - dung == set(KHONG_CO_O_DO), (
        "có kind không ô nào của BANG_O đo tới, và nó chưa được khai trong "
        "KHONG_CO_O_DO kèm lý do"
    )
    # Chiều còn lại: khai một ngoại lệ đã hết lý do cũng ĐỎ. Danh sách miễn
    # trừ chỉ được phép NGẮN ĐI.
    assert set(KHONG_CO_O_DO) <= set(GEOMETRY_CHECKERS) - dung, \
        "KHONG_CO_O_DO còn giữ một kind nay đã có ô đo — xoá dòng ấy đi"


def test_khoa_oracle_cua_bo_nap_DAN_tu_BANG_O_khong_chep_tay():
    """Hồi quy của lỗi cũ: bảng chép tay thiếu năm nghĩa vụ mệnh đề."""
    SH, IN = _nap("seal_geometry_holdout"), _nap("ingest_holdout_batch")
    for o in SH.BANG_O:
        assert IN._khoa_oracle(SH, o) == SH.BANG_O[o][0], o


# ══ ĐƠN VỊ GÓC — cái bẫy im lặng của ô A10 ═══════════════════════════════
def test_goc_duong_duong_dung_COS_BINH_goc_duong_mat_dung_SIN_BINH():
    """`check_angle` chọn công thức theo KIỂU cặp đối tượng, không theo tên ô.

    Đây là chỗ một oracle đúng-giá-trị vẫn sai-đơn-vị: đường–đường nhận
    `cos²`, đường–mặt nhận `sin²`. Ca 45° không phân biệt được hai quy ước
    (cả hai đều ra 1/2), nên test phải dùng góc ≠ 45°.
    """
    from app.simulation.geometry.exact import Line3, Plane3, Vec3
    from app.simulation.geometry import measure as M

    V = Vec3.of
    o = V(0, 0, 0)
    ox = Line3(o, V(1, 0, 0))
    cheo = Line3(o, V(1, 1, 0))                     # 45° với Ox
    assert M.cos_sq_between_lines(ox, cheo) == Fraction(1, 2)

    # đường–MẶT ở góc ≠ 45°, để hai quy ước PHÂN BIỆT ĐƯỢC: Oz với mặt z = 0
    # ⇒ góc 90° ⇒ sin² = 1. Dùng nhầm cos² thì ra 0.
    oz = Line3(o, V(0, 0, 1))
    mp = Plane3(o, V(0, 0, 1))
    assert M.sin_sq_line_plane(oz, mp) == Fraction(1)
    assert M.cos_sq_between_vectors(oz.direction, mp.normal) == Fraction(1)
    # Cùng một cặp, hai quy ước cho hai số khác nhau ở góc 0°/90° — ca 45°
    # thì không, và đó là lý do ca này không được chọn 45°.
    cheo_mp = Line3(o, V(1, 0, 1))
    assert M.sin_sq_line_plane(cheo_mp, mp) == Fraction(1, 2)


@pytest.mark.parametrize("kind", TAM_LOAI)
def test_moi_kind_co_checker_goi_duoc(kind):
    """Không loại nào chỉ tồn tại trong bảng mà không có hàm chấm."""
    assert callable(GEOMETRY_CHECKERS[kind])
