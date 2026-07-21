# -*- coding: utf-8 -*-
"""M17-RC1 §C — fixture BỔ SUNG cho slot `semantic_completeness`.

Vì sao module RIÊNG thay vì thêm vào ``authenticity_fixtures``: matrix W0/W1 là
bằng chứng ĐÃ CÔNG BỐ (73 case, artifact wave0/wave1). Thêm case vào đó làm
mọi artifact cũ đổi số — RC1-C giữ chúng BẤT BIẾN và chỉ CỘNG THÊM case của
mình, đúng luật "tái sử dụng artifact cũ: tham chiếu, không sửa".

Bốn case, mỗi case một family có ý nghĩa cardinality, expectation viết TRƯỚC
khi chạy (không chỉnh theo output):

- ``rc1c-scan-max-and-min``   — user chỉ định: "tìm CẢ max lẫn min".
- ``rc1c-tree-four-traversals`` — đề gốc đã quan sát ngoài đời (4 kiểu duyệt).
- ``rc1c-sort-two-algorithms``  — hai thuật toán sắp xếp trong một đề.
- ``rc1c-base-two-conversions`` — đổi sang HAI cơ số trong một đề.

Cả bốn dùng ĐÚNG bề mặt analyze production (`analyze_exposed_values()`); case
nào family không có bề mặt đó thì để ``requested_mechanisms`` RỖNG — đó chính
là hiện thực, và audit phải phơi ra hậu quả chứ không được vá bằng giá trị
tưởng tượng mà LLM không thể sinh.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.evaluation.authenticity_fixtures import (
    CaseScript,
    _algo_cfg,
    _analysis,
    _baseconv_cfg,
    _classify,
    _sort_spec,
    _tree_cfg,
)
from app.simulation.descriptor import FamilyId
from app.simulation.error_codes import ErrorCode


@dataclass(frozen=True)
class CompletenessFixture:
    """Case semantic-completeness end-to-end. ``expected_*`` viết theo HỢP ĐỒNG
    (bất biến §D: ok ⟹ dropped rỗng), KHÔNG theo hành vi hiện tại."""

    case_id: str
    family_id: str
    prompt: str
    script: CaseScript
    expected_status: str
    expected_error_code: str | None
    requested_operations: tuple[str, ...]  # mô tả người đọc: đề hỏi mấy thao tác
    note: str = ""


def _an(goal: str, requested: list[str], **kw) -> dict:
    """Analysis + `requested_mechanisms` (trường §D). Không sửa `_analysis`
    dùng chung — chỉ cộng thêm trường ở đây."""
    return {**_analysis(goal=goal, **kw), "requested_mechanisms": requested}


# (id, left, right) — đúng shape `_tree_cfg` của fixture W2A.
_TREE_NODES = [
    ("A", "B", "C"),
    ("B", "D", None),
    ("C", None, None),
    ("D", None, None),
]
_TREE_REL = [
    {"type": "left_child", "from": "A", "to": "B"},
    {"type": "right_child", "from": "A", "to": "C"},
    {"type": "left_child", "from": "B", "to": "D"},
]

COMPLETENESS_FIXTURES: tuple[CompletenessFixture, ...] = (
    # ── single_pass_scan: max + min (user chỉ định) ──────────────────
    # `requested_mechanisms` RỖNG vì single_pass_scan.* KHÔNG nằm trong
    # analyze_exposed_values() — LLM không có giá trị enum nào để khai. Đây là
    # HIỆN THỰC của bề mặt analyze, không phải fixture cẩu thả.
    CompletenessFixture(
        case_id="rc1c-scan-max-and-min",
        family_id=FamilyId.SINGLE_PASS_SCAN.value,
        prompt="Cho dãy số 4, 7, 2, 9, 5. Tìm cả giá trị lớn nhất và nhỏ nhất của dãy.",
        script=CaseScript(
            _an("Tìm cả giá trị lớn nhất và nhỏ nhất", []),
            [_classify("algorithm.find_max")],
            [_algo_cfg([4, 7, 2, 9, 5], summary="Tìm giá trị lớn nhất")],
        ),
        expected_status="unsupported",
        expected_error_code=ErrorCode.MULTIPLE_OPERATIONS_NOT_SUPPORTED.value,
        requested_operations=("tìm max", "tìm min"),
        note="Một lượt quét dựng được MỘT accumulator; đề hỏi hai.",
    ),
    # ── tree_traversal: 4 kiểu duyệt (đề gốc ngoài đời) ─────────────
    CompletenessFixture(
        case_id="rc1c-tree-four-traversals",
        family_id=FamilyId.TREE_TRAVERSAL.value,
        prompt=(
            "Cho cây nhị phân gốc A, con trái B, con phải C, B có con trái D. "
            "Hãy trình bày cả bốn cách duyệt: trước, giữa, sau và theo mức."
        ),
        script=CaseScript(
            _an(
                "Duyệt cây theo cả bốn thứ tự",
                ["tree_traversal.preorder", "tree_traversal.inorder",
                 "tree_traversal.postorder", "tree_traversal.level_order"],
                objects=["nút A", "nút B", "nút C", "nút D"],
                relations=_TREE_REL,
            ),
            [_classify("tree.traversal")],
            [_tree_cfg("preorder", "A", _TREE_NODES)],
        ),
        expected_status="unsupported",
        expected_error_code=ErrorCode.MULTIPLE_OPERATIONS_NOT_SUPPORTED.value,
        requested_operations=("preorder", "inorder", "postorder", "level_order"),
    ),
    # ── comparison_sort: hai thuật toán (bề mặt analyze bare legacy) ─
    CompletenessFixture(
        case_id="rc1c-sort-two-algorithms",
        family_id=FamilyId.COMPARISON_SORT.value,
        prompt=(
            "Cho dãy 5, 2, 9, 1. Hãy sắp xếp tăng dần bằng thuật toán nổi bọt, "
            "rồi làm lại bằng thuật toán chèn để so sánh."
        ),
        script=CaseScript(
            _an("Sắp xếp bằng hai thuật toán",
                ["adjacent_compare_swap", "shift_into_sorted_prefix"]),
            [_classify("algorithm.comparison_sort")],
            # selector token ⇒ config phải là FamilySpec (không phải config
            # legacy) — dùng đúng builder của fixture sorting đã live-proven.
            [_sort_spec("bubble", [5, 2, 9, 1])],
        ),
        expected_status="unsupported",
        expected_error_code=ErrorCode.MULTIPLE_OPERATIONS_NOT_SUPPORTED.value,
        requested_operations=("bubble", "insertion"),
    ),
    # ── positional_representation: hai lần đổi cơ số ────────────────
    CompletenessFixture(
        case_id="rc1c-base-two-conversions",
        family_id=FamilyId.POSITIONAL_REPRESENTATION.value,
        prompt="Đổi số 25 sang hệ nhị phân và sang hệ thập lục phân.",
        script=CaseScript(
            _an("Đổi 25 sang hai hệ cơ số",
                ["positional_representation.binary_positional_weights",
                 "positional_representation.non_binary_base"]),
            [_classify("binary.base_conversion")],
            [_baseconv_cfg(10, 2, "25")],
        ),
        expected_status="unsupported",
        expected_error_code=ErrorCode.MULTIPLE_OPERATIONS_NOT_SUPPORTED.value,
        requested_operations=("10→2", "10→16"),
    ),
)

COMPLETENESS_BY_FAMILY: dict[str, tuple[CompletenessFixture, ...]] = {}
for _fx in COMPLETENESS_FIXTURES:
    COMPLETENESS_BY_FAMILY.setdefault(_fx.family_id, ())
    COMPLETENESS_BY_FAMILY[_fx.family_id] += (_fx,)

__all__ = ["COMPLETENESS_BY_FAMILY", "COMPLETENESS_FIXTURES", "CompletenessFixture"]
