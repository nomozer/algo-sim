# -*- coding: utf-8 -*-
"""WAVE 2C / 3A — CASE NÀO LÀ SẢN PHẨM, CASE NÀO LÀ ĐỒ NGHỀ NỘI BỘ.

─── VẤN ĐỀ ────────────────────────────────────────────────────────────────

Các pool đánh giá trộn hai loại case khác hẳn nhau về mục đích:

  · "Dựng tam giác ABC từng bước" — dùng để CHỨNG MINH DSL generic dựng được
    cảnh nhiều bước. Nó chứng minh ENGINE chạy. Nó KHÔNG chứng minh AlgoSim nên
    sinh nội dung hình học cho học sinh Tin học.
  · "Mô phỏng phản ứng hoá học natri và nước" — dùng để chứng minh hệ TỪ CHỐI
    trung thực. Nó cố ý ngoài phạm vi.

Trộn chúng vào một con số "phủ" sẽ nói dối theo hai hướng: đếm hình học vào phủ
chương trình Tin học, hoặc coi một fixture nội bộ là lỗi phạm vi.

─── BA LOẠI, KHAI TƯỜNG MINH ──────────────────────────────────────────────

Phân loại này KHÔNG xoá case nào. Nó chỉ nói mỗi case đang chứng minh điều gì,
và bề mặt công khai chỉ được lấy từ loại thứ nhất.
"""

from __future__ import annotations

from enum import Enum


class ProductScope(str, Enum):
    #: nội dung Tin học THPT — được bày cho học sinh, được tính vào phủ chương trình
    PUBLIC_THPT_INFORMATICS = "PUBLIC_THPT_INFORMATICS"
    #: chứng minh ENGINE/DSL chạy; KHÔNG bày, KHÔNG tính vào phủ chương trình
    INTERNAL_ENGINE_FIXTURE = "INTERNAL_ENGINE_FIXTURE"
    #: cố ý ngoài phạm vi — chứng minh hệ TỪ CHỐI trung thực
    OUT_OF_SCOPE_TEST = "OUT_OF_SCOPE_TEST"


#: Case đã soát và phân loại tay. Chỉ ghi những case KHÔNG phải mặc định
#: (`PUBLIC_THPT_INFORMATICS`), để danh sách này ngắn và đọc được.
#:
#: Mỗi dòng phải nói VÌ SAO — "nó vốn nằm trong pool khác" không phải lý do.
SCOPE_OVERRIDES: dict[str, tuple[ProductScope, str]] = {
    "b-triangle": (
        ProductScope.INTERNAL_ENGINE_FIXTURE,
        "Dựng tam giác từng bước — chứng minh DSL generic dựng được cảnh nhiều "
        "bước (reveal_sequence). Hình học KHÔNG thuộc chương trình Tin học THPT, "
        "nên nó chứng minh ENGINE, không chứng minh phạm vi sản phẩm.",
    ),
    "d-tridrag": (
        ProductScope.INTERNAL_ENGINE_FIXTURE,
        "Như trên, thêm kéo-thả điểm — chứng minh action `move` đi qua engine. "
        "Giá trị nằm ở cơ chế kéo, không ở nội dung hình học.",
    ),
    "m16-generic-reveal": (
        ProductScope.INTERNAL_ENGINE_FIXTURE,
        "Cùng nội dung dựng tam giác như `b-triangle`, chạy qua đường catalog "
        "m16 — chứng minh `generic.rule_scene` dựng được cảnh nhiều bước. Nội "
        "dung hình học, không thuộc chương trình Tin học THPT.",
    ),
    "m16-generic-move": (
        ProductScope.INTERNAL_ENGINE_FIXTURE,
        "Robot đi qua các trạm cho sẵn — chứng minh primitive `move_along_path` "
        "chạy qua engine. Không neo vào chủ đề SGK nào; giá trị nằm ở cơ chế di "
        "chuyển, không ở nội dung bài học.",
    ),
    "c-chem": (
        ProductScope.OUT_OF_SCOPE_TEST,
        "Phản ứng hoá học — cố ý ngoài phạm vi. Case tồn tại để khẳng định hệ "
        "TỪ CHỐI trung thực thay vì dựng một cảnh trông giống mô phỏng.",
    ),
    "c-geo-complex": (
        ProductScope.OUT_OF_SCOPE_TEST,
        "Bài hình học động (quỹ tích) — đúng gốc ý tưởng ban đầu của đề tài "
        "nhưng NGOÀI môn Tin học. Giữ để chứng minh ranh giới phạm vi có thật.",
    ),
}


def scope_of(case_id: str) -> ProductScope:
    """Loại của một case. Không khai ⇒ nội dung Tin học công khai."""
    entry = SCOPE_OVERRIDES.get(case_id)
    return entry[0] if entry else ProductScope.PUBLIC_THPT_INFORMATICS


def reason_of(case_id: str) -> str | None:
    entry = SCOPE_OVERRIDES.get(case_id)
    return entry[1] if entry else None
