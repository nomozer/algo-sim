# -*- coding: utf-8 -*-
"""MỘT THẨM QUYỀN KIỂU CHO `measure` — khoá cho nó không tách ra lần nữa.

─── LỖ NÓ BỊT ─────────────────────────────────────────────────────────────

Luật *"`angle_cos` chỉ nhận vectơ"* từng được viết **ba lần**: validator, bảng
`_KIEU_DO` của thẩm định tĩnh, và nhánh `isinstance` của kernel. Không bản nào
được gửi cho mô hình.

Giá của việc ấy đã trả hai lần, cùng một hình:

  · `vector3` thêm vào `_CHU_KY` (bảng SINH RA) mà quên `_KIEU_DO` (bảng ĐƯỢC
    NHẬN) ⇒ chương trình dựng vectơ ĐÚNG bị từ chối. Bốn lượt live chết.
  · Thẻ văn phạm không nói lượng đo nào nhận kiểu nào ⇒ `angle_cos` trên
    `line3` **14 lượt / 220.898 token** trong AUDIT 2026-08-31.

Nay `BANG_PHEP_DO` là nguồn, ba nơi đọc nó. File này khoá cả ba đường đọc —
guard không chạy trên mọi đường thì phần không được canh sẽ là phần trôi.

─── ĐIỀU CÁC TEST NÀY CỐ Ý KHÔNG LÀM ─────────────────────────────────────

Không khẳng định bảng phải khớp `isinstance` của kernel theo AST. Kernel diễn
đạt cặp hợp lệ bằng LUỒNG ĐIỀU KHIỂN (`Line×Line`, `Line×Plane`…), không bằng
dữ liệu, nên đọc ngược nó ra một tập kiểu là dựng bản sao thứ hai — đúng thứ
file này tồn tại để cấm. Thay vào đó khoá hướng YẾU HƠN mà chắc: model-facing
không bao giờ RỘNG hơn thứ kernel có nhánh.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from app.simulation.semantic_program import geometry_exec as GX
from app.simulation.semantic_program.grammar_card import grammar_card
from app.simulation.semantic_program.ir_static_check import _KIEU_DO
from app.simulation.semantic_program.measure_contract import (
    BANG_PHEP_DO,
    mo_ta_phep_do,
    quantity_trong_contract,
)


# ══ ① BẢNG PHỦ HẾT HỢP ĐỒNG ═════════════════════════════════════════════
def test_moi_quantity_trong_contract_deu_co_dong():
    """Thêm một lượng đo vào enum mà quên bảng ⇒ ĐỎ ở đây, không ở live."""
    assert set(quantity_trong_contract()) == set(BANG_PHEP_DO), (
        "enum `quantity` và bảng phép đo đã lệch — đúng hình lỗi mà "
        "`vector3` thiếu trong `_KIEU_DO` đã gây ra")


def test_khong_dong_nao_thua():
    """Bảng không được mang một lượng đo hợp đồng không có — nó sẽ được dạy
    cho mô hình rồi chết ở schema."""
    assert set(BANG_PHEP_DO) <= set(quantity_trong_contract())


@pytest.mark.parametrize("q", sorted(BANG_PHEP_DO))
def test_moi_dong_deu_co_NGHIA_viet_ra(q):
    p = BANG_PHEP_DO[q]
    assert p.kieu_of, f"{q} không khai kiểu `of`"
    assert len(p.nghia) > 20, f"{q} thiếu câu ngữ nghĩa"


# ══ ② THẨM ĐỊNH TĨNH DẪN XUẤT, KHÔNG CHÉP ═══════════════════════════════
def test_KIEU_DO_dan_xuat_dung_tu_bang():
    """`_KIEU_DO` là bản dẫn xuất — sửa một bên mà quên bên kia là bất khả."""
    assert set(_KIEU_DO) == set(BANG_PHEP_DO)
    for q, p in BANG_PHEP_DO.items():
        of, wrt = _KIEU_DO[q]
        assert of == p.kieu_of
        assert wrt == (p.kieu_wrt if p.hai_toan_hang else None)


def test_chi_volume_do_MOT_toan_hang():
    mot = {q for q, p in BANG_PHEP_DO.items() if not p.hai_toan_hang}
    assert mot == {"volume"}, (
        "đổi tập phép đo một-toán-hạng thì thông điệp lỗi của validator "
        "(tự sinh từ bảng) đổi theo — kiểm rằng đó là chủ ý")


# ══ ③ THẨM QUYỀN CỦA HƯỚNG NẰM Ở TẦNG KHAI ══════════════════════════════
def test_chi_angle_cos_doi_VECTO():
    """`vector3` và `point3` cùng là `Vec3` ở runtime, nên khác biệt 'có hướng'
    CHỈ tồn tại ở tầng đọc được `memory_declarations`."""
    doi_vecto = {q for q, p in BANG_PHEP_DO.items() if "vector3" in p.kieu_of}
    assert doi_vecto == {"angle_cos"}


def test_validator_khong_con_viet_cung_ten_phep_do():
    """Điều kiện canh hướng phải suy từ BẢNG, không từ chuỗi `"angle_cos"`.

    Viết cứng tên là cách luật thứ tư ra đời: thêm một phép đo nhận vectơ mà
    quên dòng `if` ấy thì nó không được canh, và không được canh ở ĐÚNG tầng
    duy nhất canh nổi.
    """
    src = Path(inspect.getfile(GX)).with_name("validator.py").read_text(
        encoding="utf-8")
    dau = src.index("RANH GIỚI TẦNG")
    khoi = src[dau:dau + 1800]
    assert '"angle_cos"' not in khoi and "'angle_cos'" not in khoi, (
        "validator lại viết cứng tên phép đo — điều kiện phải suy từ bảng")


# ══ ④ MODEL-FACING KHÔNG RỘNG HƠN KERNEL ════════════════════════════════
def test_model_facing_khong_rong_hon_nhanh_cua_kernel():
    """Dạy mô hình một cửa RỘNG hơn cửa thật là đẩy nó vào lỗi runtime — mà
    lỗi runtime KHÔNG được gửi ngược để sửa, nên nó giết cả ca.

    Kiểm theo hướng yếu mà chắc: mỗi kiểu ta khai phải xuất hiện trong nhánh
    `isinstance` của `_do`. Không đọc ngược kernel thành một tập (xem docstring
    đầu file) — chỉ hỏi 'kiểu này kernel có nhắc tới không'.
    """
    than = inspect.getsource(GX._do) if hasattr(GX, "_do") else inspect.getsource(GX)
    lop = {"point3": "Vec3", "vector3": "Vec3", "line3": "Line3",
           "plane3": "Plane3", "solid": "Polyhedron"}
    for q, p in BANG_PHEP_DO.items():
        for k in set(p.kieu_of) | set(p.kieu_wrt):
            assert lop[k] in than, (
                f"`{q}` khai nhận '{k}' nhưng kernel không có nhánh cho "
                f"`{lop[k]}` — mô hình sẽ được dạy một cửa không có thật")


# ══ ⑤ THẺ GỬI CHO MÔ HÌNH THẬT SỰ MANG BẢNG ═════════════════════════════
def test_the_hinh_hoc_mang_kieu_toan_hang():
    """Bảng đúng mà không tới tay mô hình thì không sửa được gì — đó chính là
    trạng thái trước wave này."""
    the = grammar_card("hinh_hoc")
    for q, p in BANG_PHEP_DO.items():
        assert q in the
        assert p.kieu_of[0] in the
    assert "không theo chữ trong đề" in the


def test_the_TIN_HOC_khong_mang_bang_phep_do():
    """`measure` là biểu thức hình học; đề Tin học không bao giờ phát nó, nên
    bảng ở đó là byte thừa — và ngân sách thẻ tồn tại đúng để chặn kiểu
    thêm-vì-tiện ấy."""
    assert "không theo chữ trong đề" not in grammar_card(None)


def test_bang_chung_offline_replay_con_nguyen_trong_the():
    """§11 — mỗi `CAN_NGAN` phải chỉ được ra một chuỗi CÓ THẬT trong thẻ.

    Không có test này thì báo cáo replay là lời tự khen: sửa thẻ làm mất
    `through:danh sách TÊN` thì script lặng lẽ hạ cấp và con số 22 tụt, nhưng
    không ai chạy lại nó để thấy. Ở đây thì ĐỎ.
    """
    import sys
    from pathlib import Path as _P

    sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "scripts"))
    from replay_contract_effect import thu_thap

    d = thu_thap()
    assert not d["thieu_bang_chung"], (
        "thẻ mất bằng chứng mà offline replay dựa vào: "
        f"{d['thieu_bang_chung']}")


def test_mo_ta_nghia_KHONG_nhac_dang_bai():
    """§2 — mô hình phải chọn theo NGỮ NGHĨA, không theo từ khoá đề.

    `gm_07` không có chữ 'nhị diện' nào mà mô hình vẫn chọn `angle_cos` cả hai
    lượt. Gắn tên một dạng bài cạnh một primitive là dựng lại đúng cái bẫy.
    """
    van = mo_ta_phep_do().lower()
    for tu in ("nhị diện", "côsin", "cosin", "nhọn", "tù"):
        assert tu not in van, f"mô tả phép đo dẫn theo từ khoá đề: {tu!r}"
