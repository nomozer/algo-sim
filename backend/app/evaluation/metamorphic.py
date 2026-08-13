# -*- coding: utf-8 -*-
"""WAVE 2B — PHÉP BIẾN HÌNH GIỮ NGUYÊN NGỮ NGHĨA.

─── VÌ SAO CÓ FILE NÀY ────────────────────────────────────────────────────

Muốn biết hệ có ĐỌC ĐƯỢC CƠ CHẾ hay chỉ khớp mẫu chữ, cách rẻ nhất không phải
viết thêm hàng trăm đề rời rạc — mà lấy MỘT đề đã phân loại rồi biến đổi bề mặt
theo cách KHÔNG đụng tới cơ chế, và đòi phán quyết giữ nguyên.

Một hệ khớp mẫu sẽ vỡ ở đây: đổi "An/Bình" thành "Minh/Lan", đổi "máy tính"
thành "điện thoại", đổi 8 thành 7 — cơ chế y hệt, chữ khác đi.

─── LUẬT ──────────────────────────────────────────────────────────────────

Mọi phép ở đây phải TẤT ĐỊNH (cùng đầu vào → cùng đầu ra) và phải giữ:
  · cùng `curriculum_area`
  · cùng `capability_family`
  · cùng phán quyết phạm vi (`domain_scope`)
  · cùng `simulatability`

Phép nào đổi cơ chế thì KHÔNG thuộc file này — nó là một case khác.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

#: Tên người: đổi TÊN, không đổi SỐ LƯỢNG người (đổi số lượng là đổi dữ liệu).
_PEOPLE = {
    "An": "Minh", "Bình": "Lan", "Chi": "Hoa", "Dũng": "Phúc",
    "Em": "Khoa", "Giang": "Thảo", "Hà": "Tuấn", "Khang": "Ngọc",
}
#: Thiết bị: đổi VẬT, giữ VAI TRÒ trong mạng.
_DEVICES = {
    "máy tính": "máy trạm", "máy chủ": "máy phục vụ", "điện thoại": "máy tính bảng",
    "switch": "bộ chuyển mạch", "router": "bộ định tuyến",
}
#: Cách nói tương đương trong tiếng Việt học đường.
_PHRASES = {
    "lớn nhất": "cao nhất", "nhỏ nhất": "thấp nhất",
    "từ 8 trở lên": "không dưới 8", "sắp xếp": "sắp thứ tự",
    "tìm kiếm": "tra tìm",
}


@dataclass(frozen=True)
class Transform:
    """Một phép biến hình có tên, để báo cáo nói được phép nào đã chạy."""

    name: str
    describe: str
    apply: Callable[[str], str]


def _swap_words(mapping: dict[str, str]) -> Callable[[str], str]:
    """Thay theo từ điển, ưu tiên khoá DÀI trước để không cắt nhầm cụm."""
    keys = sorted(mapping, key=len, reverse=True)

    def run(text: str) -> str:
        out = text
        for k in keys:
            out = re.sub(re.escape(k), mapping[k], out)
        return out

    return run


def _shift_numbers(delta: int) -> Callable[[str], str]:
    """Cộng `delta` vào MỌI số nguyên.

    ⚠️ Giữ nguyên số 0 và 1: ở các đề logic/nhị phân chúng là GIÁ TRỊ BIT, đổi
    chúng là đổi cơ chế chứ không phải đổi bề mặt.
    """
    def run(text: str) -> str:
        def bump(m: re.Match[str]) -> str:
            n = int(m.group(0))
            return m.group(0) if n <= 1 else str(n + delta)
        return re.sub(r"\d+", bump, text)

    return run


def _reverse_list(text: str) -> str:
    """Đảo thứ tự một dãy số liệt kê bằng dấu phẩy.

    Chỉ đụng dãy có ≥3 số để không đảo nhầm "13, 2" trong một câu văn.
    Với tìm-max/đếm/tổng, đảo thứ tự KHÔNG đổi kết quả — đó là điều đáng kiểm.
    """
    def run(m: re.Match[str]) -> str:
        nums = [p.strip() for p in m.group(0).split(",")]
        return ", ".join(reversed(nums))

    return re.sub(r"\d+(?:\s*,\s*\d+){2,}", run, text)


def _squeeze_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _pad_space(text: str) -> str:
    """Thêm khoảng trắng và dấu câu thừa — mô phỏng cách học sinh gõ thật."""
    return "  " + re.sub(r",", " , ", text) + " "


TRANSFORMS: tuple[Transform, ...] = (
    Transform("rename_people", "đổi tên người", _swap_words(_PEOPLE)),
    Transform("rename_devices", "đổi tên thiết bị", _swap_words(_DEVICES)),
    Transform("equivalent_phrasing", "cách nói tương đương", _swap_words(_PHRASES)),
    Transform("shift_numbers", "đổi giá trị số (giữ 0/1)", _shift_numbers(1)),
    Transform("reverse_sequence", "đảo thứ tự dãy liệt kê", _reverse_list),
    Transform("squeeze_whitespace", "gộp khoảng trắng", _squeeze_space),
    Transform("noisy_whitespace", "thêm khoảng trắng/dấu thừa", _pad_space),
)


def variants(text: str) -> list[tuple[str, str]]:
    """Mọi biến thể của một đề. Bỏ biến thể TRÙNG bản gốc (phép không chạm được).

    Trả `[(tên_phép, văn_bản)]`. Biến thể trùng gốc bị loại vì nó không kiểm
    thêm gì mà lại làm con số phủ trông to hơn thực tế.
    """
    out: list[tuple[str, str]] = []
    for t in TRANSFORMS:
        got = t.apply(text)
        if got != text:
            out.append((t.name, got))
    return out
