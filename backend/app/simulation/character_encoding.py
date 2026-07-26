# -*- coding: utf-8 -*-
"""M17 W3 — HỢP ĐỒNG `CharacterEncodingSpec`: ký tự → mã → nhị phân.

NGUỒN DUY NHẤT của từ vựng + giới hạn cho `binary.character_encoding`. Schema
Gemini trong `catalog.py` và validator (`validation/character_encoding.py`) đều
DẪN XUẤT từ đây (anti-pattern #1).

RANH GIỚI BACKEND ↔ FRONTEND (quyết định kiến trúc W3):
- backend **chỉ** sở hữu hợp đồng + kiểm định + cổng. Backend **KHÔNG** có engine
  mã hoá, **KHÔNG** chuyển số sang nhị phân, **KHÔNG** dựng trace.
- frontend sở hữu engine tất định và timeline; nó dùng LẠI `toBase()` của
  `base_conversion` (`convert-module.tsx`) — **không** có bộ chuyển đổi thứ hai.
- `ord()` ở backend chỉ dùng để **kiểm khoảng** code point, không phải để sinh
  kết quả học tập.

Vì sao chain là `character_code_mapping → non_binary_base` chứ KHÔNG phải
`binary_positional_weights`: `binary.decimal_to_binary` giới hạn cứng
`decimalValue` 0–255 / `bitWidth` 1–8, trong khi BMP cần tới 65535. Đường
`base_conversion` có `CONV_MAX_VALUE = 65535` — trùng khít U+0000..U+FFFF.
"""
from __future__ import annotations

SPEC_VERSION = "charenc-1.0"

# ── Từ vựng ĐÓNG ────────────────────────────────────────────────────────────
ENCODING_ASCII = "ascii"
ENCODING_UNICODE = "unicode_codepoint"
ENCODINGS: tuple[str, ...] = (ENCODING_ASCII, ENCODING_UNICODE)

# ── GIỚI HẠN CỨNG — MỘT NGUỒN ───────────────────────────────────────────────
MAX_TEXT_CODE_POINTS = 12          # đếm theo CODE POINT, không theo UTF-16 unit
ASCII_MAX = 0x7F
BMP_MAX = 0xFFFF                   # == CONV_MAX_VALUE của base_conversion
SURROGATE_MIN = 0xD800
SURROGATE_MAX = 0xDFFF

# Khoá chỉ được xuất hiện trong KẾT QUẢ, cấm nằm trong spec ứng viên (R0).
FORBIDDEN_SPEC_KEYS: frozenset[str] = frozenset({
    "code_points", "codePoints", "decimal_values", "binary_values", "binary",
    "rows", "result", "results", "trace", "steps", "timeline", "output",
})


def encoding_enum() -> list[str]:
    """Cho schema Gemini — dẫn xuất, không viết tay."""
    return list(ENCODINGS)


def code_point_out_of_range(code_point: int, encoding: str) -> str | None:
    """Lý do (learner-facing) nếu code point nằm ngoài phạm vi; None nếu hợp lệ.

    MỘT NGUỒN cho cả kiểm định lẫn thông điệp từ chối — hai bên không thể lệch."""
    if SURROGATE_MIN <= code_point <= SURROGATE_MAX:
        return ("Chuỗi chứa một nửa cặp ký tự đặc biệt (surrogate) nên không "
                "phải một ký tự hoàn chỉnh. Em hãy nhập lại ký tự cần mã hoá.")
    if encoding == ENCODING_ASCII:
        if code_point > ASCII_MAX:
            return (f"Chế độ ASCII chỉ hỗ trợ các ký tự có mã từ 0 đến {ASCII_MAX}. "
                    "Nếu em muốn xem mã của ký tự tiếng Việt, hãy chọn chế độ "
                    "Unicode code point.")
        return None
    if code_point > BMP_MAX:
        return ("Mô phỏng hiện chỉ hỗ trợ ký tự Unicode trong vùng cơ bản "
                "(BMP, mã tối đa 65535), chưa hỗ trợ emoji hay ký tự nằm ngoài "
                "vùng này.")
    return None


__all__ = [
    "SPEC_VERSION", "ENCODING_ASCII", "ENCODING_UNICODE", "ENCODINGS",
    "MAX_TEXT_CODE_POINTS", "ASCII_MAX", "BMP_MAX", "SURROGATE_MIN",
    "SURROGATE_MAX", "FORBIDDEN_SPEC_KEYS", "encoding_enum",
    "code_point_out_of_range",
]
