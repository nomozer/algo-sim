"""M14 — mô hình descriptor capability (design rev2 §C).

Tách BA khái niệm (§C0):
- runtime target: một mô phỏng concrete có module/executor FE (thành viên CATALOG);
- mechanism membership: cơ chế của target thuộc (những) capability family nào;
- LLM selection choice: thứ classifier chọn (derive ở `catalog.llm_choices`).

File này CHỈ định nghĩa KIỂU + enum ĐÓNG cho membership. Dữ liệu membership khai
trên từng SimSpec (catalog.py, Task 2); FAMILY_SELECTORS ở `simulation/families/`.
Không tạo nguồn sự thật thứ hai — chỉ là vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ResultAuthority(str, Enum):
    """Ai sở hữu KẾT QUẢ của một membership. representation = reveal/move do
    engine dựng frame, KHÔNG phải executable domain computation (§C3, quyết định 13)."""

    COMPUTATION = "computation"
    REPRESENTATION = "representation"


class ReachabilityLevel(str, Enum):
    """Mức với tới của một capability (§C1.2, §O2). Một entry có thể mang nhiều mức."""

    REGISTERED = "registered"
    LIBRARY_DISCOVERABLE = "library_discoverable"
    AI_REACHABLE_PUBLIC = "ai_reachable_public"
    INTERNAL_FIXTURE = "internal_fixture"


class FamilyId(str, Enum):
    """Taxonomy family ĐÓNG (§C3). Thêm family = thêm giá trị ở đây (một nguồn)."""

    SINGLE_PASS_SCAN = "single_pass_scan"
    INTERVAL_ELIMINATION = "interval_elimination"
    COMPARISON_SORT = "comparison_sort"
    BOOLEAN_COMPOSITION = "boolean_composition"
    POSITIONAL_REPRESENTATION = "positional_representation"
    GRAPH_TRAVERSAL = "graph_traversal"
    LAYERED_PDU_TRANSFORM = "layered_pdu_transform"
    STRUCTURAL_PROGRESSIVE_REPRESENTATION = "structural_progressive_representation"


@dataclass(frozen=True)
class FamilyMembership:
    """Một runtime target thuộc một mechanism family (§C1).

    `result_authority` có thể KHÁC nhau giữa các membership của cùng một target
    (vd generic.rule_scene: boolean_composition=computation +
    structural_progressive_representation=representation). `variant_id`/
    `family_spec_version`/`mechanism_id` chỉ đặt khi target được với qua một
    FamilySelector (vd sorting); None khi target là choice độc lập.
    """

    family_id: FamilyId
    result_authority: ResultAuthority
    variant_id: str | None = None
    family_spec_version: str | None = None
    mechanism_id: str | None = None
