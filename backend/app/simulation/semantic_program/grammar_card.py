# -*- coding: utf-8 -*-
"""Thẻ văn phạm IR — hợp đồng giao diện gửi kèm đề bài, SINH TỪ PYDANTIC.

VÌ SAO TỒN TẠI (2026-08-22, sau lượt chạy pilot thứ hai với API thật): schema
IR **không diễn đạt được** bằng dialect structured-output của Gemini. Nó có 37
`$defs`, 421 `$ref`, 40 `oneOf` kèm `discriminator`, và **đệ quy** — nội suy
`$ref` nổ ~10× mỗi bậc (296 KB ở độ sâu 2, 3 MB ở độ sâu 3), mà độ sâu 2 còn
quá nông cho một `for_range` có `if` bên trong. Đây là giới hạn thiết kế, không
phải một trường viết sai.

Hệ quả đo được: bỏ schema thì mô hình bọc đầu ra trong khoá `semantic_program`,
gọi `variables` thay `memory_declarations`, dùng `type: "number"` thay `int`, và
bịa `element_element_type` — 38/40 case trượt thẩm định. Prompt cố ý KHÔNG nhắc
tên trường vì nó tin schema cưỡng chế chúng; giả định đó không còn đúng.

Thẻ này mang đúng thứ `responseSchema` từng mang, và **không** phải nhồi prompt:

- Nó sinh từ chính `contract.py`, nên KHÔNG THỂ trôi khỏi hợp đồng. Thêm một
  statement kind là thẻ tự có, không ai phải nhớ sửa.
- Nó ghép vào **user message**, không vào `skills/*.md`, nên ngân sách prompt
  tĩnh vẫn đo đúng thứ nó sinh ra để đo (luật viết tay do người thêm).
- Tiền lệ có sẵn trong kho: `catalog_text()` và `manifest_capability_summary()`
  cũng là tóm tắt dẫn xuất ghép vào user message của `classify`.

Nó KHÔNG thay validator: `validate_semantic_program` vẫn là thứ bảo đảm, thẻ chỉ
làm tăng tỉ lệ trúng.
"""
from __future__ import annotations

import typing

from pydantic import BaseModel

from . import contract as C


#: Chỉ những thứ này mới là GIÁ TRỊ literal. Không siết thì `typing.get_args`
#: của một union phân biệt (Annotated[…, Tag(…)]) cũng lọt vào và thẻ in ra cả
#: đường dẫn module — đo được 19.759 byte thay vì ~2 KB.
_VO_HUONG = (str, int, float, bool, type(None))


def _gia_tri_dong(annotation) -> tuple[str, ...]:
    """Các giá trị của một `Literal`, kể cả khi bọc trong `Optional`."""
    def _tu(args) -> tuple[str, ...]:
        if args and all(isinstance(a, _VO_HUONG) for a in args):
            return tuple(str(a) for a in args if a is not None)
        return ()

    args = typing.get_args(annotation)
    truc_tiep = _tu(args)
    if truc_tiep:
        return truc_tiep
    for a in args:  # Optional[Literal[...]]
        con = _tu(typing.get_args(a))
        if con:
            return con
    return ()


def _truong(model: type[BaseModel]) -> str:
    """Tên trường, `?` = tuỳ chọn, và LIỆT KÊ GIÁ TRỊ cho trường enum.

    Giá trị enum là bắt buộc phải có: lượt kiểm sau khi thêm thẻ cho thấy mô
    hình dựng đúng cấu trúc lồng nhưng viết `op: "add"` thay vì `"+"`. Tên
    trường nói được *chỗ nào điền*, không nói được *điền gì*.
    """
    ra = []
    for ten, f in model.model_fields.items():
        if ten == "kind":
            continue
        nhan = ten if f.is_required() else ten + "?"
        gt = _gia_tri_dong(f.annotation)
        # Bỏ qua enum quá dài (vd MemoryType) — chúng đã có mục riêng.
        if gt and len(gt) <= 8:
            nhan += "(" + "|".join(gt) + ")"
        ra.append(nhan)
    return " ".join(ra)


def _cac_kind(alias) -> list[tuple[str, type[BaseModel]]]:
    """Rút (nhãn kind, model) từ một union phân biệt của contract."""
    ra: list[tuple[str, type[BaseModel]]] = []
    for arg in typing.get_args(typing.get_args(alias)[0]):
        model = typing.get_args(arg)[0] if typing.get_args(arg) else arg
        if not (isinstance(model, type) and issubclass(model, BaseModel)):
            continue
        k = model.model_fields.get("kind")
        nhan = typing.get_args(k.annotation)[0] if k else model.__name__
        ra.append((nhan, model))
    return sorted(ra)


def _khoi(ten: str, alias) -> str:
    dong = [f"  {nhan}: {_truong(m)}".rstrip() for nhan, m in _cac_kind(alias)]
    return f"{ten}\n" + "\n".join(dong)


def grammar_card() -> str:
    """Hợp đồng IR ở dạng gọn, tiếng Việt, dẫn xuất 100% từ `contract.py`."""
    bat_buoc = [n for n, f in C.SemanticProgramSpec.model_fields.items()
                if f.is_required()]
    spec = _truong(C.SemanticProgramSpec)
    khai = _truong(C.MemoryDeclaration)
    kieu = " ".join(typing.get_args(C.MemoryType))
    prim = " ".join(
        typing.get_args(C.VisualContainerBinding.model_fields["primitive"].annotation)
    )

    return (
        "HỢP ĐỒNG JSON — dùng ĐÚNG các tên dưới đây, không đặt tên khác, không "
        "bọc thêm một tầng nào ở ngoài.\n\n"
        f"Đối tượng gốc: {spec}\n"
        f"  BẮT BUỘC phải có đủ: {', '.join(bat_buoc)} — thiếu một cái là hỏng.\n"
        "  `?` = tuỳ chọn. KHÔNG có khoá `semantic_program`, `variables` hay "
        "`program` ở ngoài cùng.\n\n"
        f"memory_declarations[]: {khai}\n"
        f"  type nhận đúng một trong: {kieu}\n"
        "  element_type dùng cho array/stack/queue/set/matrix; key_type và "
        "val_type dùng cho map.\n\n"
        + _khoi("statements[] — mỗi phần tử có `kind` và các trường:",
                C.SemanticStatement)
        + "\n\n"
        + _khoi("biểu thức giá trị — cũng có `kind`:", C.ValueExpr)
        + "\n\n"
        + _khoi("điều kiện — cũng có `kind`:", C.ConditionExpr)
        + "\n\n"
        "visual_bindings: containers[] pointers[] value_boxes[]\n"
        f"  containers[]: {_truong(C.VisualContainerBinding)}\n"
        f"    primitive nhận đúng một trong: {prim}\n"
        f"  pointers[]: {_truong(C.VisualPointerBinding)}\n"
        f"  value_boxes[]: {_truong(C.VisualValueBoxBinding)}\n"
    )
