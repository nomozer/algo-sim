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
    _booldag_cfg,
    _classify,
    _sort_spec,
    _traverse_cfg,
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
    requested_operations: tuple[str, ...]  # đề hỏi mấy VIỆC (operation id)
    expected_route: str | None = None  # bắt buộc khi expected_status == "ok"
    note: str = ""


def _an(goal: str, requested: list[str], operations: list[str] | None = None, **kw) -> dict:
    """Analysis + `requested_mechanisms` (§D) + `requested_operations` (§C1).
    Không sửa `_analysis` dùng chung — chỉ cộng thêm trường ở đây."""
    a = {**_analysis(goal=goal, **kw), "requested_mechanisms": requested}
    if operations is not None:
        a["requested_operations"] = operations
    return a


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
    # §C1: `requested_mechanisms` VẪN rỗng (single_pass_scan.* không nằm trong
    # analyze_exposed_values()) — nhưng `requested_operations` nói được HAI mục
    # tiêu dù chúng dùng CHUNG mechanism `track_extreme`. Đúng chỗ §D thủng.
    CompletenessFixture(
        case_id="rc1c-scan-max-and-min",
        family_id=FamilyId.SINGLE_PASS_SCAN.value,
        prompt="Cho dãy số 4, 7, 2, 9, 5. Tìm cả giá trị lớn nhất và nhỏ nhất của dãy.",
        script=CaseScript(
            _an("Tìm cả giá trị lớn nhất và nhỏ nhất", [],
                ["single_pass_scan:find_max", "single_pass_scan:find_min"]),
            [_classify("algorithm.find_max")],
            [_algo_cfg([4, 7, 2, 9, 5], summary="Tìm giá trị lớn nhất")],
        ),
        expected_status="unsupported",
        expected_error_code=ErrorCode.MULTIPLE_OPERATIONS_NOT_SUPPORTED.value,
        requested_operations=("single_pass_scan:find_max", "single_pass_scan:find_min"),
        note="Một lượt quét dựng được MỘT accumulator; đề hỏi hai.",
    ),
    # ── graph_traversal: BFS + DFS ──────────────────────────────────
    CompletenessFixture(
        case_id="rc1c-graph-bfs-and-dfs",
        family_id=FamilyId.GRAPH_TRAVERSAL.value,
        prompt=(
            "Cho đồ thị các đỉnh A, B, C, D. Hãy duyệt bằng cả chiều rộng (BFS) "
            "lẫn chiều sâu (DFS) từ đỉnh A để so sánh."
        ),
        script=CaseScript(
            _an("Duyệt đồ thị bằng cả BFS lẫn DFS", [],
                ["graph_traversal:bfs", "graph_traversal:dfs"],
                objects=["đỉnh A", "đỉnh B", "đỉnh C", "đỉnh D"],
                relations=["A nối B", "A nối C", "B nối D"]),
            [_classify("network.graph_traversal")],
            [_traverse_cfg(
                ["A", "B", "C", "D"],
                [["A", "B"], ["A", "C"], ["B", "D"]], "A", "bfs",
            )],
        ),
        expected_status="unsupported",
        expected_error_code=ErrorCode.MULTIPLE_OPERATIONS_NOT_SUPPORTED.value,
        requested_operations=("graph_traversal:bfs", "graph_traversal:dfs"),
        note="BFS và DFS là hai lần duyệt — chưa có chế độ so sánh song song.",
    ),
    # ── boolean_composition: family MULTIPLE — nhiều việc là HỢP LỆ ─
    # Đối chứng quan trọng: cổng cardinality KHÔNG được chặn family khai
    # `multiple`. Một mạch chứa nhiều cổng là chuyện bình thường.
    CompletenessFixture(
        case_id="rc1c-boolean-multi-gate-allowed",
        family_id=FamilyId.BOOLEAN_COMPOSITION.value,
        prompt=(
            "Mạch logic: đèn sáng khi (A VÀ B) HOẶC (KHÔNG C). Mô phỏng mạch và "
            "lập bảng chân trị."
        ),
        script=CaseScript(
            _an("Mô phỏng mạch nhiều cổng", [],
                ["boolean_composition:boolean_dag"],
                objects=["đầu vào A", "đầu vào B", "đầu vào C", "cổng AND", "cổng OR"],
                relations=["A và B vào cổng AND", "AND và NOT C vào cổng OR"]),
            [_classify("logic.boolean_dag")],
            [_booldag_cfg(
                [{"id": "A", "value": 1}, {"id": "B", "value": 0}, {"id": "C", "value": 1}],
                [{"id": "g1", "op": "AND", "inputs": ["A", "B"]},
                 {"id": "g2", "op": "NOT", "inputs": ["C"]},
                 {"id": "g3", "op": "OR", "inputs": ["g1", "g2"]}],
                "g3",
            )],
        ),
        expected_status="ok",
        expected_error_code=None,
        requested_operations=("boolean_composition:boolean_dag",),
        expected_route="logic.boolean_dag",
        note="Family MULTIPLE: nhiều cổng trong một cảnh KHÔNG phải xung đột.",
    ),
    # ── ĐỐI CHỨNG chống chặn oan: đề chỉ hỏi MỘT việc ───────────────
    CompletenessFixture(
        case_id="rc1c-scan-max-only",
        family_id=FamilyId.SINGLE_PASS_SCAN.value,
        prompt="Cho dãy số 4, 7, 2, 9, 5. Tìm giá trị lớn nhất của dãy.",
        script=CaseScript(
            _an("Tìm giá trị lớn nhất", [], ["single_pass_scan:find_max"]),
            [_classify("algorithm.find_max")],
            [_algo_cfg([4, 7, 2, 9, 5], summary="Tìm giá trị lớn nhất")],
        ),
        expected_status="ok",
        expected_error_code=None,
        requested_operations=("single_pass_scan:find_max",),
        expected_route="algorithm.find_max",
        note="MỘT operation → PHẢI chạy bình thường (chống chặn oan).",
    ),
    CompletenessFixture(
        case_id="rc1c-tree-one-variant-only",
        family_id=FamilyId.TREE_TRAVERSAL.value,
        prompt=(
            "Cho cây nhị phân gốc A, con trái B, con phải C, B có con trái D. "
            "Hãy duyệt cây theo thứ tự giữa."
        ),
        script=CaseScript(
            _an("Duyệt cây theo thứ tự giữa", ["tree_traversal.inorder"],
                ["tree_traversal:inorder"],
                objects=["nút A", "nút B", "nút C", "nút D"], relations=_TREE_REL),
            [_classify("tree.traversal")],
            [_tree_cfg("inorder", "A", _TREE_NODES)],
        ),
        expected_status="ok",
        expected_error_code=None,
        requested_operations=("tree_traversal:inorder",),
        expected_route="tree.traversal",
        note="MỘT variant → PHẢI chạy bình thường (chống chặn oan).",
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

# ══════════════ §C2 — fixture THIẾU DỮ KIỆN, SINH TỪ REGISTRY ══════════════
@dataclass(frozen=True)
class InsufficientFixture:
    """Case "đề chưa cho dữ kiện bắt buộc" cho MỘT target APPLICABLE.

    SINH TỪ HỢP ĐỒNG, không viết tay danh sách target: thêm target mới có
    `required_grounded_inputs` ⇒ case tự xuất hiện; quên khai hợp đồng ⇒ target
    rơi vào nhánh "chưa khai" và audit báo, không lặng lẽ bỏ qua.

    Oracle KHÔNG phải executor production: kỳ vọng đọc thẳng từ hợp đồng
    (`insufficiency_error_code`), và bằng chứng thiếu là các `InputKind` mà
    normalizer không tìm thấy.
    """

    case_id: str
    target_id: str
    family_id: str
    prompt: str
    script: CaseScript
    missing_inputs: tuple[str, ...]
    expected_error_code: str


def _empty_evidence_analysis(goal: str) -> dict:
    """Analyze của đề KHÔNG cho dữ kiện: đúng hợp đồng analyze.md — "đề không
    cho số liệu cụ thể → để mảng RỖNG". Không object/quan hệ/số nào."""
    return {
        **_analysis(goal=goal, objects=[], data=[], relations=[]),
        "requested_operations": [],
        "notes": "Đề chưa cung cấp dữ kiện cụ thể.",
    }


def _selector_token_for(sim_id: str) -> str | None:
    from app.simulation.families import FAMILY_SELECTORS

    for sel in FAMILY_SELECTORS.values():
        if any(v.concrete_simulation_id == sim_id for v in sel.variants):
            return sel.selector_token
    return None


def _build_insufficient_fixtures() -> tuple[InsufficientFixture, ...]:
    from app.simulation.catalog import CATALOG
    from app.simulation.descriptor import ReachabilityLevel
    from app.simulation.input_requirements import APPLICABLE, INPUT_REQUIREMENTS, applicability_of
    from app.simulation.operations import operation_labels, operations_of_target

    out: list[InsufficientFixture] = []
    for sid in sorted(INPUT_REQUIREMENTS):
        spec = CATALOG.get(sid)
        if spec is None or ReachabilityLevel.AI_REACHABLE_PUBLIC not in spec.reachability:
            continue
        status, _ = applicability_of(sid)
        if status != APPLICABLE:
            continue
        req = INPUT_REQUIREMENTS[sid]
        ops = operations_of_target(sid)
        label = (operation_labels(ops) or ["mô phỏng bài này"])[0]
        fam = sorted({m.family_id.value for m in spec.family_memberships})[0]
        # Target nấp sau SELECTOR TOKEN (sorting) không phải là lựa chọn hợp lệ
        # của classify — phải route qua token, đúng như production.
        route = _selector_token_for(sid) or sid
        out.append(InsufficientFixture(
            case_id=f"rc1c-insufficient-{sid.replace('.', '-').replace('_', '-')}",
            target_id=sid,
            family_id=fam,
            # Đề THẬT của học sinh khi quên dán dữ liệu: nêu việc cần làm,
            # không nêu dữ kiện nào.
            prompt=f"Hãy {label} cho bài trên lớp của em.",
            script=CaseScript(
                _empty_evidence_analysis(f"Hãy {label}"),
                [_classify(route)],  # classify VẪN route đúng — cổng mới phải chặn
                [],                 # KHÔNG kịch bản simulate: tới simulate là sai
            ),
            missing_inputs=tuple(k.value for k in req.required_grounded_inputs),
            expected_error_code=req.insufficiency_error_code.value,
        ))
    return tuple(out)


INSUFFICIENT_FIXTURES: tuple[InsufficientFixture, ...] = _build_insufficient_fixtures()


COMPLETENESS_BY_FAMILY: dict[str, tuple[CompletenessFixture, ...]] = {}
for _fx in COMPLETENESS_FIXTURES:
    COMPLETENESS_BY_FAMILY.setdefault(_fx.family_id, ())
    COMPLETENESS_BY_FAMILY[_fx.family_id] += (_fx,)

__all__ = ["COMPLETENESS_BY_FAMILY", "COMPLETENESS_FIXTURES", "CompletenessFixture"]
