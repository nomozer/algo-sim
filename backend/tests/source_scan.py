# -*- coding: utf-8 -*-
"""ĐỌC MÃ NGUỒN CHO GUARD — bóc chú thích và docstring trước khi quét.

─── VÌ SAO TỒN TẠI: MỘT LỚP LỖI ĐÃ LẶP NĂM LẦN ────────────────────────────

Guard *"file X không được dùng Y"* quét thẳng nội dung rồi ĐỎ vì chính **câu
giải thích rằng nó không dùng Y**:

    scene3d-page.test.tsx        — chú thích *"vì sao không dùng visual_mode"*
    canvas-first-shell.test.tsx  — cùng câu ấy
    test_live_session_api.py     — docstring *"GeometryState do kernel sở hữu"*
    live-classroom.test.tsx      — *"«đang gặp khó» thì không"*
    test_spatial_distance.py     — docstring *"`int(n**0.5)**2 == n` thì sai"*

Phía frontend đã có `src/test-source.ts` cho đúng lớp lỗi này. Đây là bản sinh
đôi phía Python — cùng ý, khác cách bóc: ở đây dùng **AST**, không dùng biểu
thức chính quy, vì Python có docstring (một biểu thức chuỗi ở vị trí câu lệnh)
mà regex không phân biệt được với một chuỗi dữ liệu bình thường.

⚠️ KHÔNG dùng khi thứ bị cấm không được phép xuất hiện **kể cả trong lời bàn** —
ví dụ một nguyên thuỷ chiếu màn hình. Ở đó quét cả chú thích mới đúng, và đó là
một quyết định khác, không phải một cách dùng khác.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any


def _bo_docstring(node: ast.AST) -> None:
    """Xoá docstring khỏi mọi Module/Class/Function trong cây."""
    for n in ast.walk(node):
        if not isinstance(n, (ast.Module, ast.ClassDef,
                              ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        than = getattr(n, "body", None)
        if (than and isinstance(than[0], ast.Expr)
                and isinstance(than[0].value, ast.Constant)
                and isinstance(than[0].value.value, str)):
            than.pop(0)
            if not than:  # thân rỗng sau khi bỏ docstring ⇒ phải có `pass`
                than.append(ast.Pass())


def than_ma(muc_tieu: Any) -> str:
    """Mã THẬT của một hàm/lớp/module: không chú thích, không docstring.

    `ast.unparse` chuẩn hoá cách viết (`** 0.5` → `**0.5`), nên guard nào soi
    chuỗi ký tự phải kiểm CẢ HAI cách viết. Đó là cái giá của việc bóc bằng
    AST, và nó rẻ hơn cái giá của một guard đỏ oan mỗi lần ai đó viết chú thích.
    """
    if isinstance(muc_tieu, (str, Path)):
        ma = Path(muc_tieu).read_text(encoding="utf-8")
    else:
        ma = inspect.getsource(muc_tieu)
    cay = ast.parse(ma)
    _bo_docstring(cay)
    return ast.unparse(cay)


def con_du(ma: str, moc: str, toi_thieu: int = 60) -> bool:
    """Rỗng-là-hỏng: bóc sai thì mọi `not in` bên dưới xanh vô nghĩa.

    Gọi ngay sau `than_ma` trong mỗi guard. Một dòng, và nó là khác biệt giữa
    "đã kiểm" với "tưởng đã kiểm".
    """
    return moc in ma and len(ma) >= toi_thieu
