# -*- coding: utf-8 -*-
"""BIÊN VẬN CHUYỂN — giá trị runtime → giá trị JSON. Một thẩm quyền, một chỗ.

    runtime (Fraction · Radical · Vec3 · Line3 · Plane3)
        → transport (dict/str/int JSON-an-toàn)
        → envelope → cache → API → frontend

─── LỖI NÓ BỊT, VÀ VÌ SAO NÓ LÀ LỖI 500 CHỨ KHÔNG PHẢI LỖI HIỂN THỊ ───────

`VisualTraceAdapter` đặt **thẳng** giá trị bộ nhớ vào `value_box.value`. Với
một biến `point3` đó là `Vec3`; với một số đo đó là `Fraction` hoặc `Radical`.
Cả ba không `json.dumps` được — và `main.py` serialize envelope để ghi cache
**sau khi cả pipeline đã thành công**. Nghĩa là: mọi cổng nói PASS, học sinh
vẫn nhận 500.

GENERALIZATION MATRIX tìm ra nó (2026-08-31): `check_learner_surface` cho qua
3/3 chương trình đã kiểm, nên không tầng nào chặn trước. Nặng hơn vẻ ngoài —
prompt DẠY mô hình gắn `visual_bindings` cho witness của mỗi nghĩa vụ, nên một
chương trình hình học **đúng** gần như chắc chắn rơi vào đây.

─── HAI HÀM, HAI CÂU HỎI KHÁC NHAU ────────────────────────────────────────

    to_transport(x)  →  CẤU TRÚC cho máy      {"kind": "radical", …}
    to_display(x)    →  MỘT SCALAR cho người  "3√2/5"

Tách vì frontend hiện làm `String(v)` trên `value_box.value` và trên từng
`items[i]`. Nhét một dict vào đó là in ra `[object Object]` — đúng thứ §14
cấm. Nên trường `value` giữ nguyên là scalar, còn cấu trúc đi ở trường SONG
SONG (`exact`), cùng khuôn `scene3d` đã dùng cho `quantity`.

─── FAIL CLOSED, KHÔNG `str()` ────────────────────────────────────────────

Gặp kiểu runtime chưa đăng ký thì **NÉM**, không rơi về `str(value)`. Fallback
`str()` che mất hợp đồng kiểu: nó biến một lỗi thiết kế thành một chuỗi trông
hợp lệ, và lần sau không ai biết dữ liệu đã mất hình dạng ở đâu.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from ..geometry.exact import Line3, Plane3, Vec3
from ..geometry.radical import Radical, display as _hien_so, to_json as _so_json

__all__ = [
    "TransportTypeError",
    "ERR_KIEU_LA",
    "to_transport",
    "to_display",
    "to_cell",
    "transport_pair",
    "is_json_native",
]

#: Mã lỗi khi một kiểu runtime chưa có đường ra biên.
ERR_KIEU_LA = "TRANSPORT_UNSERIALIZABLE_TYPE"


class TransportTypeError(TypeError):
    """Kiểu runtime chưa đăng ký đường ra biên vận chuyển.

    Là `TypeError` để nơi gọi bắt cùng chỗ nó vẫn bắt lỗi serialize, nhưng mang
    mã riêng: một envelope chết ở đây là LỖI HỆ THỐNG có địa chỉ, không phải
    một `json.dumps` nổ giữa lúc ghi cache.
    """

    def __init__(self, gia_tri: Any):
        self.code = ERR_KIEU_LA
        super().__init__(
            f"{ERR_KIEU_LA}: kiểu '{type(gia_tri).__name__}' chưa có biểu diễn "
            "vận chuyển. Đăng ký nó ở `transport.py` — KHÔNG rơi về str()."
        )


def is_json_native(x: Any) -> bool:
    """`x` đi thẳng qua `json.dumps` được không?

    `bool` phải xét TRƯỚC `int` ở mọi nơi khác, nhưng ở đây cả hai đều
    JSON-native nên không cần tách.
    """
    return x is None or isinstance(x, (bool, int, float, str))


def _vec3(v: Vec3) -> dict[str, Any]:
    """Toạ độ CHÍNH XÁC dạng chuỗi phân số, không float.

    `"1/2"` đọc ngược lại được bằng `Fraction`; `0.5` thì không, và mất đúng
    thứ phân biệt hệ này với một bộ vẽ hình. Renderer hoá float ở bước cuối
    trước GPU — đó là chuyện của renderer, không phải của biên này.
    """
    return {"kind": "vec3",
            "components": [str(v.x), str(v.y), str(v.z)],
            "display": f"({v.x}, {v.y}, {v.z})"}


def to_transport(x: Any) -> Any:
    """Giá trị runtime → CẤU TRÚC JSON-an-toàn. Đệ quy. Fail closed.

    JSON-native đi thẳng: một `int` trong `value_box` của bài Tin học phải vẫn
    là `int`, không được bọc thành dict — bọc là phá hợp đồng frontend đang có.
    """
    if is_json_native(x):
        return x
    if isinstance(x, (Fraction, Radical)):
        return {**_so_json(x), "display": _hien_so(x)}
    if isinstance(x, Vec3):
        return _vec3(x)
    if isinstance(x, Line3):
        return {"kind": "line3", "point": _vec3(x.point),
                "direction": _vec3(x.direction)}
    if isinstance(x, Plane3):
        return {"kind": "plane3", "point": _vec3(x.point),
                "normal": _vec3(x.normal)}
    if isinstance(x, dict):
        # Khoá về chuỗi: JSON không có khoá không-chuỗi, và một khoá `Fraction`
        # sẽ chết ở `json.dumps` đúng như giá trị.
        return {str(k): to_transport(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [to_transport(v) for v in x]
    raise TransportTypeError(x)


def to_display(x: Any) -> Any:
    """Giá trị runtime → MỘT SCALAR cho người đọc. Fail closed.

    Trả về `str` cho mọi kiểu runtime, và giữ nguyên JSON-native scalar. Dùng
    cho `value_box.value` và `items[i]` — hai chỗ frontend làm `String(v)`.

    Danh sách/từ điển KHÔNG có nghĩa hiển thị chung, nên chúng không đi qua đây:
    nơi gọi tự lặp từng phần tử.
    """
    if is_json_native(x):
        return x
    if isinstance(x, (Fraction, Radical)):
        return _hien_so(x)
    if isinstance(x, Vec3):
        return f"({x.x}, {x.y}, {x.z})"
    if isinstance(x, Line3):
        return f"đường qua ({x.point.x}, {x.point.y}, {x.point.z})"
    if isinstance(x, Plane3):
        return f"mặt phẳng pháp tuyến ({x.normal.x}, {x.normal.y}, {x.normal.z})"
    raise TransportTypeError(x)


def to_cell(x: Any) -> Any:
    """Một PHẦN TỬ trong `items`/`entries` → JSON-an-toàn, ưu tiên đọc được.

    Vì sao không dùng thẳng `to_display` hay `to_transport`:

      · `to_display` từ chối `dict` — nhưng một HÀNG của `table_grid` vốn là
        một dict, và frontend render nó như một hàng chứ không như một ô chữ.
      · `to_transport` biến `Vec3` thành dict — và frontend làm `String(v)`
        trên từng ô, nên nó sẽ in ra `[object Object]`.

    Nên luật ở đây theo HÌNH DẠNG: thứ có nghĩa như MỘT Ô (số, căn, điểm) thì
    thành chữ; thứ vốn là cấu trúc (hàng bảng, danh sách lồng) thì giữ cấu
    trúc. Kiểu lạ vẫn fail closed.
    """
    if isinstance(x, (dict, list, tuple, set)):
        return to_transport(x)
    return to_display(x)


def transport_pair(x: Any) -> tuple[Any, Any | None]:
    """`(value, exact)` — scalar cho người, cấu trúc cho máy.

    `exact` là `None` khi giá trị vốn đã JSON-native: bọc một `int` vào một dict
    chỉ để "cho đồng bộ" là thêm một hình dạng thứ hai cho cùng một thứ, và hai
    hình dạng thì sẽ có chỗ đọc nhầm.
    """
    if is_json_native(x):
        return x, None
    if isinstance(x, (dict, list, tuple, set)):
        # Một `tree_node` LÀ một dict, và renderer của nó đọc cấu trúc ấy. Ép
        # nó thành chữ là phá đúng thứ nó dùng để vẽ. Giữ cấu trúc (đã làm sạch
        # đệ quy), không đẻ thêm `exact` — cấu trúc CHÍNH LÀ giá trị.
        return to_transport(x), None
    return to_display(x), to_transport(x)


def check_envelope_transport(envelope: dict[str, Any]) -> str | None:
    """Envelope này có `json.dumps` được không? `None` = được.

    ─── VÌ SAO LÀ MỘT CỔNG RIÊNG, KHÔNG GỘP VÀO `learner_surface` ──────────

    `check_learner_surface` hỏi câu SƯ PHẠM: *học sinh có thấy đủ để hiểu
    không*. Serialize được hay không là câu VẬN CHUYỂN. Gộp hai câu vào một
    cổng thì một hôm nào đó ai đó nới cổng vì lý do sư phạm và vô tình mở luôn
    đường cho một `Vec3` đi tới `json.dumps`.

    ─── VÌ SAO CHẶN Ở ĐÂY CHỨ KHÔNG ĐỂ `main.py` NỔ ───────────────────────

    `main.py` serialize envelope để GHI CACHE, tức sau khi mọi cổng đã nói
    PASS và sau khi người dùng đã đợi hết một lượt pipeline. Nổ ở đó là một
    HTTP 500 không có địa chỉ. Chặn ở đây biến nó thành một phán quyết có mã,
    có tầng, và có thể ghi vào telemetry như mọi phán quyết khác.

    Kiểm bằng `json.dumps` THẬT, không bằng cách duyệt kiểu: duyệt kiểu là
    dựng bản sao thứ hai của luật serialize, và bản sao sẽ trôi.
    """
    import json

    try:
        json.dumps(envelope, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        return f"{ERR_KIEU_LA}: envelope không serialize được — {e}"
    return None
