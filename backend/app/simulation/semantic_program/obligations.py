# -*- coding: utf-8 -*-
"""Obligation taxonomy — khoá vào HỆ KIỂU của IR, không khoá vào catalog.

VÌ SAO KHÔNG KHOÁ VÀO CATALOG: số target chương trình là MỞ (đề mới đẻ ra hoài),
nên taxonomy dựa trên nó sẽ phình theo số bài — đúng cái vừa gỡ ở
`completeness_gate`. Số cấu trúc dữ liệu trong IR thì ĐÓNG và nhỏ.

BA NGUỒN, không phải một (spec §5.1):
    IR type semantics + expression/statement semantics + reusable server-owned checker

Điều kiện thứ ba là điều kiện CHẶN: nghĩa vụ không có bộ kiểm tất định do server
sở hữu thì KHÔNG được vào bảng, dù tên nghe hợp lý tới đâu.

ĐÓNG BĂNG TRƯỚC SEALED. Chọn từ phân tích DEV
(`docs/evaluation/semantic-benchmark/dev/DEV_TAXONOMY_ANALYSIS.md`), không phải
từ nhu cầu của từng ca. Sau khi SEALED niêm phong: KHÔNG thêm checker để cứu
held-out case — hard scope lock §1.1.

Ba thứ CỐ Ý không có mặt, ghi lại để lần sau khỏi "bổ sung cho đủ":
- `predicate_verdict` (kiểu "dấu ngoặc có hợp lệ không") — kiểm nó đòi cài lại
  chính thuật toán đang kiểm, nên oracle mất tính độc lập. `verification_gap`.
- `distinct_preserving_order` — là một phép của `derived_sequence`.
- `connected_components` — tổ hợp được từ `reachability` lặp.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

#: Cấu trúc duyệt được — miền của các nghĩa vụ đếm/gộp.
TRAVERSABLE = frozenset({"array", "matrix", "set", "map", "tree_node"})

#: kind → miền kiểu container hợp lệ. Nghĩa vụ nào không có mặt ở đây là
#: KHÔNG có checker server-owned ⇒ mức yếu (spec §5.4).
OBLIGATION_KINDS: dict[str, frozenset[str]] = {
    "extremum": frozenset({"array", "matrix"}),
    # Bao trùm `count_matching` cũ: đếm = gộp với phép `count`. Thêm nó làm
    # taxonomy GỌN đi chứ không phình ra.
    "aggregate_matching": TRAVERSABLE,
    "ordering": frozenset({"array"}),
    "membership": frozenset({"array", "set", "map"}),
    # Khác `membership` ở chỗ đòi VỊ TRÍ ĐẦU TIÊN — thứ tự duyệt là một phần
    # của câu trả lời (điểm nghẽn nhận thức #3).
    "first_match_index": frozenset({"array"}),
    "total_mapping": frozenset({"map"}),
    "derived_sequence": frozenset({"array", "stack", "queue"}),
    "reachability": frozenset({"graph"}),
    "structural_traversal": frozenset({"tree_node"}),
}

#: Phép gộp đóng của `aggregate_matching`.
AGGREGATE_OPS = frozenset({"count", "sum", "product", "max", "min"})

#: Phép biến đổi đóng của `derived_sequence` — mỗi phép kiểm được TẤT ĐỊNH mà
#: không cài lại thuật toán sinh ra nó.
SEQUENCE_TRANSFORMS = frozenset({"reverse", "distinct", "filter", "map", "identity"})


class Obligation(BaseModel):
    """Một nghĩa vụ ngữ nghĩa do `analyze` khai, server đóng băng."""

    model_config = ConfigDict(frozen=True)

    kind: str
    container: str
    params: dict[str, Any] = {}

    @property
    def witness(self) -> str | None:
        """Biến mà chương trình phải tạo ra để chứng tỏ đã làm nghĩa vụ này."""
        w = self.params.get("witness")
        return w if isinstance(w, str) else None

    def describe(self) -> str:
        return f"{self.kind}({self.container})"


def is_supported(kind: str) -> bool:
    """Nghĩa vụ có checker server-owned không? Không → mức yếu (§5.4)."""
    return kind in OBLIGATION_KINDS


def accepts_container_type(kind: str, container_type: str | None) -> bool:
    allowed = OBLIGATION_KINDS.get(kind)
    return bool(allowed and container_type in allowed)
