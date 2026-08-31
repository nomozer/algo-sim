# -*- coding: utf-8 -*-
"""THẨM QUYỀN KIỂU — một hợp đồng, một chỗ khai. **0 API call.**

─── LỖI ĐÃ LẶP HAI LẦN, LẦN SAU ĐẮT HƠN LẦN TRƯỚC ─────────────────────────

Cùng một hợp đồng kiểu được khai ở nhiều bảng, và chúng trôi khỏi nhau:

  · thêm `section`   — `_KIEU_DUNG` biết, `MemoryType` chưa ⇒ `coplanar` rơi
    khỏi nhóm hình học, lộ ra ở một lượt live.
  · thêm `vector3`   — `_CHU_KY` (SINH RA) biết, `_KIEU_DO` (ĐƯỢC NHẬN) chưa
    ⇒ chương trình dựng vectơ hoàn toàn đúng bị từ chối bằng *"cần point3 hoặc
    line3 … có vector3"*. Hệ nói sai, mô hình làm đúng, **cả bốn ca live chết**.

Chú thích trong `ir_static_check` từng khai có một guard tên
`test_chu_ky_phu_het_bieu_thuc_hinh_hoc` — **guard ấy không tồn tại**. Một lời
hứa trong chú thích không chặn được gì; file này là guard thật.

─── HAI CÁCH CHỐNG TRÔI, DÙNG CẢ HAI ──────────────────────────────────────

① DẪN XUẤT — `validator._BIEU_THUC_HINH_HOC` nay sinh ra từ `_CHU_KY`, nên
   thêm một biểu thức chỉ phải sửa MỘT bảng.
② ĐỐI CHIẾU — những bảng không dẫn xuất được (runtime dispatch là `if/elif`)
   thì test này so chúng với nhau.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

from app.simulation.semantic_program import geometry_exec as GX
from app.simulation.semantic_program.contract import MemoryType
from app.simulation.semantic_program.ir_static_check import _CHU_KY, _KIEU_DO
from app.simulation.semantic_program.validator import _BIEU_THUC_HINH_HOC
from tests.source_scan import than_ma

try:  # Python 3.8+ — `Literal` args
    from typing import get_args
except ImportError:  # pragma: no cover
    get_args = None


def _kind_trong_runtime() -> set[str]:
    """Mọi `kind` mà `eval_geometry_expr` THẬT SỰ xử lý.

    Đọc bằng AST, không bằng chuỗi: bản chép tay sẽ trôi đúng như hai bảng nó
    đang canh, và một guard tự trôi thì tệ hơn không có guard.
    """
    cay = ast.parse(than_ma(GX.eval_geometry_expr))
    ra: set[str] = set()
    for n in ast.walk(cay):
        if not isinstance(n, ast.Compare) or len(n.comparators) != 1:
            continue
        trai, phai = n.left, n.comparators[0]
        if (isinstance(trai, ast.Name) and trai.id == "kind"
                and isinstance(phai, ast.Constant) and isinstance(phai.value, str)):
            ra.add(phai.value)
    return ra


def test_bang_DAN_XUAT_khong_the_lech_khoi_chu_ky():
    """`_BIEU_THUC_HINH_HOC` sinh ra từ `_CHU_KY` ⇒ không thể thiếu mục nào."""
    for kind, (truong, _) in _CHU_KY.items():
        assert kind in _BIEU_THUC_HINH_HOC, f"{kind} vắng ở bảng dẫn xuất"
        assert _BIEU_THUC_HINH_HOC[kind] == tuple(t for t, _ in truong)


def test_runtime_va_CHU_KY_phu_het_nhau():
    """Bảng KIỂU và bảng THỰC THI phải nói về cùng một tập biểu thức.

    Lệch một chiều: thẩm định tĩnh nói OK rồi kernel ném *"biểu thức hình học
    lạ"*. Lệch chiều kia: một phép dựng chạy được mà không tầng nào kiểm kiểu.
    """
    runtime = _kind_trong_runtime()
    tinh = set(_CHU_KY) | {"measure"}
    assert runtime, "đọc AST hỏng — không lấy được kind nào"
    thieu_tinh = runtime - tinh
    thieu_runtime = tinh - runtime
    assert not thieu_tinh, f"kernel chạy được nhưng không có chữ ký kiểu: {thieu_tinh}"
    assert not thieu_runtime, f"có chữ ký kiểu nhưng kernel không chạy: {thieu_runtime}"


def test_moi_kieu_CHU_KY_sinh_ra_deu_la_MemoryType_hop_le():
    """Một biểu thức sinh ra kiểu mà `MemoryType` không biết thì chương trình
    không khai nổi biến để nhận nó — bảng đúng, hệ vẫn dùng không được."""
    hop_le = set(get_args(MemoryType))
    for kind, (_, sinh_ra) in _CHU_KY.items():
        assert sinh_ra in hop_le, f"{kind} sinh kiểu '{sinh_ra}' ngoài MemoryType"


def test_moi_kieu_TOAN_HANG_deu_la_MemoryType_hop_le():
    """Chiều ngược lại: bảng ĐƯỢC NHẬN không được đòi một kiểu không tồn tại —
    đòi thế thì không chương trình nào qua nổi, và lỗi trông như lỗi mô hình."""
    hop_le = set(get_args(MemoryType))
    for kind, (truong, _) in _CHU_KY.items():
        for ten, nhan in truong:
            for k in nhan:
                assert k in hop_le, f"{kind}.{ten} đòi kiểu '{k}' ngoài MemoryType"
    for q, (nhan_of, nhan_wrt) in _KIEU_DO.items():
        for nhom in (nhan_of, nhan_wrt or ()):
            for k in nhom:
                assert k in hop_le, f"measure '{q}' đòi kiểu '{k}' ngoài MemoryType"


def test_moi_quantity_trong_hop_dong_deu_co_bang_KIEU_DO():
    """Thêm một đại lượng đo mà quên `_KIEU_DO` thì nó rơi vào nhánh mặc định
    `(_DOI_TUONG, _DOI_TUONG)` — tức KHÔNG kiểm kiểu, im lặng."""
    from app.simulation.semantic_program.contract import MeasureExpr

    khai = set(get_args(MeasureExpr.model_fields["quantity"].annotation))
    thieu = khai - set(_KIEU_DO)
    assert not thieu, f"đại lượng không có luật kiểu, sẽ lọt kiểm im lặng: {thieu}"


def test_angle_cos_doi_VECTO_o_CA_HAI_cong():
    """Hai cổng phải nói cùng một luật — đây là ca đã giết bốn lượt live.

    ─── CƠ CHẾ ĐỔI 2026-08-31, BẤT BIẾN THÌ KHÔNG ─────────────────────────

    Bản cũ chứng minh "cùng một luật" bằng cách soi mã validator tìm chuỗi
    `angle_cos` và `vector3`. Phép ấy đo SỰ TRÙNG LẶP: nó xanh **vì** luật
    được viết hai lần, nên nó không phân biệt nổi *"hai bản chép đang khớp"*
    với *"chỉ có một bản"*. Bản thứ hai vẫn có thể trôi ngay sau lượt chạy.

    Nay luật ở `measure_contract.BANG_PHEP_DO` và cả hai cổng ĐỌC nó, nên câu
    hỏi đúng không còn là *"hai chỗ có giống nhau không"* mà là *"có còn chỗ
    thứ hai nào không"*. Đó là điều kiện mạnh hơn: không có bản sao thì không
    có gì để trôi.
    """
    from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO

    assert BANG_PHEP_DO["angle_cos"].kieu_of == ("vector3",)
    assert BANG_PHEP_DO["angle_cos"].kieu_wrt == ("vector3",)
    # Thẩm định tĩnh phải là bản DẪN XUẤT, không phải bản chép thứ hai.
    assert _KIEU_DO["angle_cos"] == (("vector3",), ("vector3",))

    # Và validator phải ĐỌC bảng chứ không tự khai lại. Soi `import`, không soi
    # thân hàm: thân hàm nay cố ý KHÔNG chứa tên phép đo nào
    # (`test_measure_contract.test_validator_khong_con_viet_cung_ten_phep_do`).
    src = than_ma(Path(inspect.getfile(GX)).with_name("validator.py"))
    assert "measure_contract" in src, (
        "validator không còn đọc thẩm quyền phép đo — luật đã tách ra bản thứ "
        "hai, đúng hình đã giết bốn lượt live")
