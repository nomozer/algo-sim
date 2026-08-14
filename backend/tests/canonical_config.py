"""Nguồn CONFIG HỢP LỆ ĐẠI DIỆN cho từng target — hạ tầng KIỂM CHỨNG hợp đồng.

─── VÌ SAO CÓ FILE NÀY ────────────────────────────────────────────────────

Muốn đóng schema an toàn thì phải chứng minh được "config hợp lệ hiện tại VẪN
hợp lệ sau khi đóng". Không có nguồn config hợp lệ theo target ở backend thì
mọi phép chứng minh ấy đều là lời nói suông — và đóng schema mù chính là FAULT D
(một mẫu đang chạy bỗng thành không hợp lệ).

Đo trước khi dựng: `validate({})` chỉ qua được **1/23** target, nên không thể
dựa vào cơ chế điền-mặc-định của validator. Đường còn lại là DẪN TỪ SCHEMA.

─── AI LÀ ORACLE ─────────────────────────────────────────────────────────

File này **KHÔNG** tự phán một ứng viên là hợp lệ. Nó chỉ *dựng* ứng viên; thứ
phán quyết luôn là **validator production** (`spec.validate`). Nếu validator từ
chối thì kết quả là `CANONICAL_CONFIG_INVALID` kèm lý do thật — không có đường
nào để một ứng viên "được coi là hợp lệ" mà chưa đi qua cổng thật.

─── KHÔNG ĐẺ BẢN SAO THỨ HAI CỦA SỰ THẬT ─────────────────────────────────

Ràng buộc trường vẫn thuộc schema/validator. Ở đây chỉ có **điều phối + xuất
xứ**: mỗi ứng viên dựng từ `config_schema` của chính target, nên schema đổi thì
ứng viên đổi theo — không có danh sách 23 config chép tay để trôi.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.simulation.catalog import CATALOG

SOURCE_SCHEMA_DERIVED = "SCHEMA_DERIVED"


@dataclass(frozen=True)
class CanonicalConfig:
    target_id: str
    candidate: dict
    source_kind: str
    source_reference: str
    normalized: dict | None
    status: str  # VALID | CANONICAL_CONFIG_INVALID
    reason: str | None


def _unique(value: Any, index: int) -> Any:
    """Làm một phần tử mảng khác các phần tử khác, không cần biết trường nào là id."""
    if index == 0:
        return value
    if isinstance(value, str):
        return f"{value}{index}"
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value + index
    if isinstance(value, dict):
        return {k: _unique(v, index) for k, v in value.items()}
    if isinstance(value, list):
        return [_unique(v, index) for v in value]
    return value


def _representative(node: dict, depth: int = 0) -> Any:
    """Giá trị ĐẠI DIỆN cho một nút schema — ưu tiên thứ schema tự khai.

    Thứ tự: `default` → `example` → `enum[0]` → theo kiểu. Với số thì lấy giá
    trị GIỮA miền chứ không lấy biên: biên là chỗ dễ trúng lỗi off-by-one của
    validator, và một ứng viên trúng biên sẽ đổ lỗi cho hợp đồng thay vì cho
    chính nó.
    """
    if depth > 6:  # đệ quy có trần — schema lồng sâu bất thường thì dừng
        return None
    if "default" in node:
        return node["default"]
    if "example" in node:
        return node["example"]
    if node.get("enum"):
        return node["enum"][0]

    kinds = node.get("type")
    kind = kinds[0] if isinstance(kinds, list) else kinds
    # HAI PHƯƠNG NGỮ SCHEMA CÙNG TỒN TẠI TRONG CATALOG — phát hiện của lượt này:
    #   logic.and_gate    "OBJECT" / "INTEGER"   (kiểu Gemini, chữ HOA)
    #   web.style_model   "object" / "integer"   (JSON Schema, chữ thường)
    # Chúng cùng đi tới một đường sinh, nên bất kỳ ai đọc schema bằng máy đều
    # phải biết cả hai — nếu không thì im lặng dựng ra rỗng, đúng như bản đầu
    # của hàm này (0/23). Đây lại là "hai bản sao của một sự thật".
    kind = kind.lower() if isinstance(kind, str) else kind

    if kind == "object":
        props = node.get("properties") or {}
        required = set(node.get("required") or props.keys())
        return {k: _representative(v, depth + 1) for k, v in props.items() if k in required}
    if kind == "array":
        item = node.get("items") or {}
        n = max(int(node.get("minItems") or 0), 2)
        # PHẦN TỬ PHẢI KHÁC NHAU. Bản đầu sinh n bản sao giống hệt, và validator
        # từ chối vì "id trùng" ở sáu target — một lỗi của BỘ SINH bị đọc nhầm
        # thành lỗi hợp đồng. Đánh số hậu tố cho mọi chuỗi bên trong để phần tử
        # phân biệt được mà không cần biết trường nào là id.
        return [_unique(_representative(item, depth + 1), i) for i in range(n)]
    if kind in ("integer", "number"):
        lo, hi = node.get("minimum"), node.get("maximum")
        if lo is not None and hi is not None:
            mid = (lo + hi) / 2
            return int(mid) if kind == "integer" else mid
        return int(lo if lo is not None else (hi if hi is not None else 1))
    if kind == "boolean":
        return True
    if kind == "string":
        return "x"
    return None


def canonical_valid_config(target_id: str) -> CanonicalConfig:
    """Ứng viên đại diện cho một target, ĐÃ đi qua validator production."""
    spec = CATALOG[target_id]
    schema = getattr(spec, "config_schema", None) or {}
    candidate = _representative(schema)
    if not isinstance(candidate, dict) or not candidate:
        return CanonicalConfig(
            target_id, {}, SOURCE_SCHEMA_DERIVED, "config_schema", None,
            "CANONICAL_CONFIG_INVALID", "CONTRACT_SOURCE_EMPTY: schema không dựng nổi ứng viên",
        )
    try:
        normalized, err = spec.validate(candidate)
    except Exception as exc:  # validator ném là dữ kiện, không được nuốt
        return CanonicalConfig(
            target_id, candidate, SOURCE_SCHEMA_DERIVED, "config_schema", None,
            "CANONICAL_CONFIG_INVALID", f"{type(exc).__name__}: {exc}",
        )
    if err or not normalized:
        return CanonicalConfig(
            target_id, candidate, SOURCE_SCHEMA_DERIVED, "config_schema", None,
            "CANONICAL_CONFIG_INVALID", err or "validator trả config rỗng",
        )
    return CanonicalConfig(
        target_id, candidate, SOURCE_SCHEMA_DERIVED, "config_schema", normalized, "VALID", None,
    )


def coverage() -> dict[str, CanonicalConfig]:
    """Ma trận đầy đủ, DẪN TỪ CATALOG — target mới tự động có mặt."""
    return {t: canonical_valid_config(t) for t in sorted(CATALOG)}
