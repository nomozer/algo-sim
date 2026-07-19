# -*- coding: utf-8 -*-
"""M16 Task 1 (W1) — lớp schema/contract cho case đánh giá M16 + khóa integrity
frozen dataset (thiết kế M16 §2, nguồn yêu cầu:
.superpowers/sdd/m16-task-1-brief.md).

`M16Expectation` gắn kỳ vọng CÓ CẤU TRÚC (family/route/gate/error_code/
mechanism canonical — M15 invariant #23) lên một `EvalItem` qua trường `m16`
(kiểu khai `object | None` bên dataset.py để tránh vòng import). Không sửa nội
dung 30 case DATASET — `frozen_dataset_fingerprint()` khóa điều đó bằng SHA-256
canonical JSON; `test_m16_schema.py` ghim hằng số PIN.

Chiều import: m16_schema → dataset (một chiều). KHÔNG import module này vào
dataset.py.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum

from app.evaluation.dataset import DATASET, EvalItem
from app.evaluation.datasets import check_admission
from app.simulation.descriptor import FamilyId

M16_DATASET_VERSION = "m16-v1"

# Hai family DUY NHẤT có tín hiệu analyze-exposed cho mechanism (M15 §claim
# boundary: machine-readable ownership 8/8 family ≠ runtime prescription-
# detection mọi family — chỉ comparison_sort + positional_representation).
_MECHANISM_EXPOSED_FAMILIES: frozenset[str] = frozenset(
    {FamilyId.COMPARISON_SORT.value, FamilyId.POSITIONAL_REPRESENTATION.value}
)


class M16Archetype(str, Enum):
    """Kiểu case đánh giá M16 — enum ĐÓNG (6 giá trị; thêm mới phải qua design,
    không tự ý mở rộng)."""

    EXPLICIT_POSITIVE = "explicit_positive"
    PARAPHRASE_POSITIVE = "paraphrase_positive"
    VALID_BOUNDARY = "valid_boundary"
    NEAR_MISS_GAP = "near_miss_gap"
    CROSS_FAMILY_RECOVERY = "cross_family_recovery"
    AUTHORITY_CONTROL = "authority_control"


# Archetype "positive": case kỳ vọng route THÀNH CÔNG tới một target cụ thể.
# cross_family_recovery được tính là positive CHỈ khi group cuối cùng không
# phải "unsupported" (recovery thành công) — xem check_m16_admission.
_POSITIVE_ARCHETYPES: frozenset[M16Archetype] = frozenset(
    {
        M16Archetype.EXPLICIT_POSITIVE,
        M16Archetype.PARAPHRASE_POSITIVE,
        M16Archetype.VALID_BOUNDARY,
        M16Archetype.CROSS_FAMILY_RECOVERY,
    }
)


@dataclass(frozen=True)
class M16Expectation:
    """Kỳ vọng CÓ CẤU TRÚC cho một case đánh giá M16 (thiết kế §2).

    `expected_initial_route`: token FAMILY_SELECTOR nếu target nằm sau một
    selector (vd sorting), else concrete simulation_id; None khi group cuối
    cùng là "unsupported". `expected_gate`: gate nào (nếu có) dự kiến chặn/
    phân loại case — "route_mechanism" (M15 E2 nhánh 3) | "mechanism" (M14 E4)
    | "computation" (M13) | None. `analyze_mechanism_expected`: mechanism
    canonical (namespaced `family.<mechanism>`, xem `app.simulation.mechanisms`)
    — CHỈ hợp lệ khi expected_family ∈ {comparison_sort, positional_representation}.
    """

    archetype: M16Archetype
    expected_family: str  # giá trị FamilyId (canonical)
    expected_initial_route: str | None
    expected_gate: str | None  # "route_mechanism" | "mechanism" | "computation" | None
    expected_error_code: str | None  # giá trị ErrorCode | None
    analyze_mechanism_expected: str | None
    algorithmic_request: bool = False
    recovery_route_exists: bool = False
    live_eligible: bool = False
    notes: str = ""


def check_m16_admission(item: EvalItem) -> list[str]:
    """Trả danh sách vi phạm luật kết nạp M16 (rỗng = hợp lệ).

    BỔ SUNG lên luật kết nạp cũ (`app.evaluation.datasets.check_admission`) —
    không thay thế; case phải qua CẢ hai bộ luật.
    """
    errs: list[str] = check_admission(item)

    m16 = item.m16
    if not isinstance(m16, M16Expectation):
        errs.append(f"{item.id}: thiếu m16 (phải là M16Expectation)")
        return errs

    if m16.expected_family not in {f.value for f in FamilyId}:
        errs.append(f"{item.id}: expected_family lạ {m16.expected_family!r} (∉ FamilyId)")

    if (
        m16.archetype in _POSITIVE_ARCHETYPES
        and item.group != "unsupported"
        and m16.expected_initial_route is None
    ):
        errs.append(
            f"{item.id}: archetype {m16.archetype.value} (group={item.group!r}) "
            "thiếu expected_initial_route"
        )

    if (
        m16.analyze_mechanism_expected is not None
        and m16.expected_family not in _MECHANISM_EXPOSED_FAMILIES
    ):
        errs.append(
            f"{item.id}: analyze_mechanism_expected chỉ hợp lệ khi expected_family "
            f"∈ {{comparison_sort, positional_representation}}, không phải "
            f"{m16.expected_family!r}"
        )

    if item.group == "unsupported" and m16.expected_gate is None and not m16.notes.strip():
        errs.append(f"{item.id}: unsupported thiếu cả expected_gate lẫn notes")

    return errs


def frozen_dataset_fingerprint() -> str:
    """SHA-256 hex của canonical JSON 30 case DATASET — khóa integrity nội dung.

    Đổi BẤT KỲ nội dung nào trong 30 case (id/text/group/expect_simulation_id/
    semantic/tags) làm hàm này trả giá trị khác → test PIN trong
    `test_m16_schema.py` đỏ. Theo chính sách (dataset.py docstring +
    docs/CURRENT_STATE.md), DATASET 30 case KHÔNG BAO GIỜ được sửa nội dung —
    nên không có quy trình "cập nhật PIN hợp lệ" trong vận hành bình thường;
    test đỏ nghĩa là DATASET đã bị sửa ngoài ý muốn, không phải việc tính lại.
    """
    payload = [
        {
            "id": it.id,
            "text": it.text,
            "group": it.group,
            "expect_simulation_id": it.expect_simulation_id,
            "semantic": it.semantic,
            "tags": list(it.tags),
        }
        for it in DATASET
    ]
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
