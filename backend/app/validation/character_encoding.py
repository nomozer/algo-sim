# -*- coding: utf-8 -*-
"""M17 W3 — Validator FAIL-CLOSED cho `binary.character_encoding`.

Backend **chỉ kiểm định**: hợp đồng, kiểu, phạm vi code point. Nó KHÔNG mã hoá,
KHÔNG chuyển sang nhị phân, KHÔNG dựng trace — engine tất định nằm ở frontend
(`domains/binary/encoding-module.tsx`) và dùng lại `toBase()` của
`base_conversion`.

`ord()` ở đây chỉ để **kiểm khoảng**. Python lặp chuỗi theo CODE POINT nên
`len("😀") == 1`; frontend phải dùng `Array.from` để có cùng ngữ nghĩa (khoá bằng
test hai phía).

KHÔNG coercion: `7` không thành `"7"`, `None` không thành `""`, `"utf8"` không
thành `unicode_codepoint`, ký tự ngoài ASCII không bị thay bằng `e`/`?`.
"""
from __future__ import annotations

from app.simulation.character_encoding import (
    ENCODINGS,
    FORBIDDEN_SPEC_KEYS,
    MAX_TEXT_CODE_POINTS,
    SPEC_VERSION,
    code_point_out_of_range,
)

_ALLOWED_KEYS = {"spec_version", "text", "encoding", "notes"}


def validate_character_encoding_config(raw) -> tuple[dict | None, str | None]:
    """`(config_sạch, None)` hoặc `(None, lý_do)`.

    Lý do viết cho VÒNG RETRY của `stage_simulate` **và** đủ thân thiện để làm
    thông điệp học sinh — không lộ target id, enum nội bộ, JSON path hay
    exception."""
    if not isinstance(raw, dict):
        return None, "Config phải là một đối tượng JSON."

    leaked = sorted(k for k in raw if k in FORBIDDEN_SPEC_KEYS)
    if leaked:
        return None, (
            f"Config KHÔNG được chứa kết quả đã tính sẵn: {', '.join(leaked)}. "
            "Chỉ nêu chuỗi cần mã hoá và bảng mã; hệ thống tự tra mã và tự đổi "
            "sang nhị phân."
        )
    extra = sorted(set(raw) - _ALLOWED_KEYS)
    if extra:
        return None, (
            f"Config có trường không thuộc hợp đồng: {', '.join(extra)}. "
            "Chỉ dùng 'text' và 'encoding'."
        )

    version = raw.get("spec_version") or SPEC_VERSION
    if version != SPEC_VERSION:
        return None, f"spec_version phải là '{SPEC_VERSION}'."

    encoding = raw.get("encoding")
    if encoding not in ENCODINGS:
        return None, (
            "Trường 'encoding' phải là 'ascii' hoặc 'unicode_codepoint'. "
            "Đề chưa nói rõ dùng bảng mã nào thì đừng tự chọn."
        )

    text = raw.get("text")
    if not isinstance(text, str):
        # KHÔNG coercion: số 7 KHÁC ký tự '7'.
        return None, (
            "Trường 'text' phải là chuỗi ký tự cần mã hoá. Số 7 và ký tự '7' là "
            "hai thứ khác nhau — hãy đặt ký tự trong dấu nháy."
        )
    if text == "":
        return None, "Chưa có ký tự nào để mã hoá — 'text' đang rỗng."

    code_points = [ord(ch) for ch in text]      # Python lặp theo CODE POINT
    if len(code_points) > MAX_TEXT_CODE_POINTS:
        return None, (
            f"Mô phỏng chỉ chạy tối đa {MAX_TEXT_CODE_POINTS} ký tự một lần, "
            f"chuỗi đang có {len(code_points)} ký tự. Em hãy thử chuỗi ngắn hơn."
        )

    for ch, cp in zip(text, code_points):
        reason = code_point_out_of_range(cp, encoding)
        if reason:
            # Nêu ĐÍCH DANH ký tự vướng, nhưng không lộ chi tiết kỹ thuật.
            return None, f"Ký tự '{ch}' không mã hoá được. {reason}"

    return {
        "spec_version": SPEC_VERSION,
        "text": text,
        "encoding": encoding,
        **({"notes": raw["notes"]} if isinstance(raw.get("notes"), str) else {}),
    }, None


__all__ = ["validate_character_encoding_config"]
