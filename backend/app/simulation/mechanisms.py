"""M15 — taxonomy cơ chế canonical namespaced (nguồn DUY NHẤT) + alias boundary.

Khóa 1: canonical_mechanism là compatibility boundary duy nhất — legacy sorting
(live-verified M14) → canonical; canonical passthrough; alias MỘT CHIỀU, không
phải taxonomy thứ hai. Gate/descriptor/cross-lock CHỈ so canonical.
Khóa 2: giá trị analyze-exposed unowned phải nằm trong INTENTIONAL_GAP_MECHANISMS.
KHÔNG import catalog (chống vòng import — cross-lock với catalog ở test).
"""
from __future__ import annotations

from app.simulation.descriptor import FamilyId

NO_PRESCRIPTION = "none"

FAMILY_MECHANISMS: dict[FamilyId, tuple[str, ...]] = {
    FamilyId.COMPARISON_SORT: (
        "comparison_sort.adjacent_compare_swap",
        "comparison_sort.shift_into_sorted_prefix",
        "comparison_sort.select_extreme_repeated",
        "comparison_sort.partition_recursive",
        "comparison_sort.other_unspecified",
    ),
    FamilyId.POSITIONAL_REPRESENTATION: (
        "positional_representation.binary_positional_weights",
        "positional_representation.non_binary_base",
        # M17 W3 — tra BẢNG MÃ ký tự ↔ số. Chuỗi năng lực:
        # character_code_mapping → non_binary_base (đổi mã số sang nhị phân).
        # KHÔNG dùng binary_positional_weights: nó gắn với decimal_to_binary vốn
        # chặn ở 0–255 / 8 bit, không chở nổi BMP (tới 65535).
        "positional_representation.character_code_mapping",
        # W5A — GHÉP BA KÊNH 0..255 THÀNH MỘT MÀU.
        #
        # Vì sao nằm trong POSITIONAL_REPRESENTATION chứ không đẻ family mới: cơ
        # chế ẩn ở đây đúng là biểu diễn theo VỊ TRÍ — mỗi kênh là một byte, và
        # ba byte đứng theo thứ tự R,G,B mới ra một màu (cặp chữ số hex của mỗi
        # kênh là chính cách viết vị trí ấy). Đẻ family mới sẽ tách nó khỏi
        # `non_binary_base`, đúng cái nó phải dùng để giải thích #RRGGBB.
        #
        # Nhưng KHÔNG dùng lại `binary_positional_weights`: cơ chế đó gắn với
        # decimal_to_binary (một số, một bàn cân bit), còn ở đây bài học là BA
        # đại lượng độc lập TRỘN lại — thứ không tồn tại trong bài kia.
        "positional_representation.rgb_channel_composition",
    ),
    FamilyId.INTERVAL_ELIMINATION: ("interval_elimination.halve_sorted_interval",),
    # M17 W2B — truy vấn BẢNG QUAN HỆ hữu hạn. Cơ chế ẩn ở đây KHÁC
    # single_pass_scan ở KHUNG QUAN HỆ (lược đồ, kiểu cột, vị từ trên BẢN GHI,
    # phép chiếu, sắp xếp ỔN ĐỊNH), dù phần tích luỹ (đếm/tổng/cực trị) trùng
    # cơ chế với quét-một-lượt — ghi rõ chỗ trùng thay vì nhận là năng lực mới
    # hoàn toàn (xem docs/COVERAGE.md).
    FamilyId.RELATIONAL_TABLE_QUERY: (
        "relational_table_query.row_predicate_filter",
        "relational_table_query.column_projection",
        "relational_table_query.stable_sort_by_key",
        "relational_table_query.bounded_limit",
        "relational_table_query.aggregate_accumulate",
    ),
    FamilyId.SINGLE_PASS_SCAN: (
        "single_pass_scan.track_extreme",
        "single_pass_scan.accumulate_conditional",
        "single_pass_scan.count_conditional",
        "single_pass_scan.find_equal_early_stop",
        "single_pass_scan.configured_single_pass",
    ),
    FamilyId.BOOLEAN_COMPOSITION: (
        "boolean_composition.single_gate_truth_table",
        "boolean_composition.composed_rule_dag",
        # M17 W1 — mạch nhiều cổng AND/OR/NOT/XOR bounded (logic.boolean_dag)
        "boolean_composition.bounded_gate_dag",
    ),
    FamilyId.GRAPH_TRAVERSAL: (
        "graph_traversal.unweighted_hop_bfs",
        # M17 W1 — duyệt đồ thị tổng quát BFS/DFS (network.graph_traversal)
        "graph_traversal.breadth_first",
        "graph_traversal.depth_first",
    ),
    FamilyId.LAYERED_PDU_TRANSFORM: (
        "layered_pdu_transform.encapsulate_decapsulate_4layer",
    ),
    FamilyId.STRUCTURAL_PROGRESSIVE_REPRESENTATION: (
        "structural_progressive_representation.reveal_sequence",
        "structural_progressive_representation.move_along_path",
        "structural_progressive_representation.step_sequence",
    ),
    # M17 W2A — duyệt cây nhị phân bounded (4 biến thể). Prefix = family_id
    # (bắt buộc theo canonical convention: mechanism_family() phải khớp family).
    FamilyId.TREE_TRAVERSAL: (
        "tree_traversal.preorder",
        "tree_traversal.inorder",
        "tree_traversal.postorder",
        "tree_traversal.level_order",
    ),
    # M17 W2C — luồng điều khiển hữu hạn. Ba cơ chế ẩn của lập trình cấu trúc:
    # gán giá trị, rẽ nhánh theo điều kiện, lặp có biên. Prefix = family_id.
    FamilyId.BOUNDED_CONTROL_FLOW: (
        "bounded_control_flow.assignment",
        "bounded_control_flow.conditional_branch",
        "bounded_control_flow.bounded_loop",
    ),
    # W4B-2Z — mô hình thuộc tính trình bày có ràng buộc. MỘT cơ chế phục vụ
    # nhiều bài CSS (đổi màu nền, đổi cỡ chữ, trang trí thẻ) — khác dữ liệu đã
    # validate, KHÔNG khác renderer.
    FamilyId.WEB_PRESENTATION: (
        "web_presentation.bounded_style_properties",
    ),
}

# Khóa 2 — giá trị CỐ Ý không target nào sở hữu (gap-trigger, khai tường minh)
# M17 W1: select_extreme_repeated flip → OWNED (algorithm.selection_sort);
#         non_binary_base flip → OWNED (binary.base_conversion).
INTENTIONAL_GAP_MECHANISMS: frozenset[str] = frozenset({
    "comparison_sort.partition_recursive",
    "comparison_sort.other_unspecified",
})

# Khóa 1 — alias MỘT CHIỀU legacy→canonical, CHỈ namespace comparison_sort (M14 compat)
LEGACY_ALIASES: dict[str, str] = {
    "adjacent_compare_swap": "comparison_sort.adjacent_compare_swap",
    "shift_into_sorted_prefix": "comparison_sort.shift_into_sorted_prefix",
    "select_extreme_repeated": "comparison_sort.select_extreme_repeated",
    "partition_recursive": "comparison_sort.partition_recursive",
    "other_unspecified": "comparison_sort.other_unspecified",
}

# Registry tiến độ formalization — wave sau MỞ RỘNG; W5 lock == toàn bộ FamilyId
FORMALIZED_FAMILIES: frozenset[FamilyId] = frozenset({
    FamilyId.COMPARISON_SORT,           # M14 (reference)
    FamilyId.POSITIONAL_REPRESENTATION, # W1
    FamilyId.INTERVAL_ELIMINATION,      # W1
    FamilyId.SINGLE_PASS_SCAN,          # W2 (Task 12) — KHÔNG selector, scan = catch-all
    FamilyId.BOOLEAN_COMPOSITION,       # W3 (Task 13) — dual surface, owned tách bạch
    FamilyId.GRAPH_TRAVERSAL,           # W4 (Task 14) — routing owned unweighted BFS only
    FamilyId.LAYERED_PDU_TRANSFORM,     # W4 (Task 14) — encap owned 4-layer encap/decap
    FamilyId.STRUCTURAL_PROGRESSIVE_REPRESENTATION,  # W5 (Task 15) — owned dẫn xuất manifest process_types()
    FamilyId.TREE_TRAVERSAL,             # M17 W2A — duyệt cây nhị phân
    FamilyId.RELATIONAL_TABLE_QUERY,     # M17 W2B — truy vấn bảng quan hệ
    FamilyId.BOUNDED_CONTROL_FLOW,       # M17 W2C — luồng điều khiển hữu hạn
    FamilyId.WEB_PRESENTATION,           # W4B-2Z — thuộc tính trình bày bounded
})  # đủ == frozenset(FamilyId) — K1 lock kích hoạt ĐẦY ĐỦ (test_formalized_families_owned_khong_rong)


def canonical_mechanism(raw: str | None) -> str | None:
    """Boundary DUY NHẤT legacy→canonical. None/"none" → None (không ép cơ chế)."""
    if raw is None or raw == NO_PRESCRIPTION:
        return None
    return LEGACY_ALIASES.get(raw, raw)


def mechanism_family(canonical: str) -> str:
    return canonical.split(".", 1)[0]


def analyze_exposed_values() -> tuple[str, ...]:
    """Nguồn enum `prescribed_procedure` của ANALYZE_SCHEMA (dẫn xuất — anti-pattern #1).
    M15: legacy sorting GIỮ NGUYÊN (rev2 điểm 2) + none + positional namespaced.

    M17 W3-LIVE-C1: họ positional TỪNG được liệt kê bằng hai string VIẾT TAY, nên
    khi W3 thêm `character_code_mapping` vào `FAMILY_MECHANISMS` thì enum analyze
    KHÔNG đi theo — đúng anti-pattern #1 (tiền lệ `_GENERIC_SCHEMA` thiếu `drag`:
    Gemini KHÔNG THỂ phát ra giá trị dù prompt cho phép). Hệ quả đo được: cơ chế
    DUY NHẤT mà `binary.character_encoding` sở hữu là bất khả phát, nên nhánh
    direct-ownership của mechanism gate KHÔNG BAO GIỜ thoả mãn được và target chỉ
    lọt khi analyze tình cờ trả "none"; khi analyze ép cơ chế nó chọn hàng xóm gần
    nhất còn lại (`binary_positional_weights`) → `capability_gap`.
    Nay SPLAT thẳng từ taxonomy: thêm cơ chế positional mới là enum tự theo."""
    return (
        NO_PRESCRIPTION,
        *LEGACY_ALIASES.keys(),
        *FAMILY_MECHANISMS[FamilyId.POSITIONAL_REPRESENTATION],
        # M17 W2A — phơi bày cơ chế duyệt cây để route-consistency (khóa 3 M15)
        # bắt được misroute sang generic bằng MECHANISM + OWNERSHIP (không
        # keyword): analyze nói tree_traversal.* mà classify trả generic →
        # mismatch họ → 1 reclassify bounded → vẫn lệch thì fail-closed.
        *FAMILY_MECHANISMS[FamilyId.TREE_TRAVERSAL],
        # M17 W2C — cùng lý do: đề "chạy từng bước đoạn chương trình có if/while"
        # mà classify trả generic → mismatch họ → 1 reclassify bounded → fail-closed.
        *FAMILY_MECHANISMS[FamilyId.BOUNDED_CONTROL_FLOW],
        # W4B-2Z — cùng lý do, và đây là family ĐANG bị misroute thật: đề
        # "đổi màu nền / cỡ chữ của thẻ" xưa nay rơi vào `generic.rule_scene`
        # rồi bị dựng thành các bước hé lộ. Không phơi cơ chế ra enum thì
        # `_family_mismatch` KHÔNG THỂ nhìn thấy sai lệch đó — sửa định tuyến
        # bằng SỞ HỮU NĂNG LỰC, không bằng dò chuỗi tiêu đề.
        *FAMILY_MECHANISMS[FamilyId.WEB_PRESENTATION],
    )
