# M17-RC1 §C — Catalog Archetype Matrix

Coverage THẬT của toàn danh mục: mỗi target × 8 archetype slot. Case chạy
qua **production `run_pipeline`** (bất biến #22) với provider kịch bản.

> **Ranh giới claim.** Provider là kịch bản ⇒ mọi số dưới đây đo **tầng
> quyết định phía server** (route handling / gate / validator / completeness)
> khi analyze đã cho trước — KHÔNG đo năng lực classify của LLM thật.
> Độ chính xác classify live đo riêng ở live smoke W1/W2A.

## Số tổng

- Target: **20** · family: **10**
- Slot: **160** = ✓ 110 · ✗ 0 · ○ 47 · – 3
- Coverage = pass / (pass+fail+gap) = **110/157** = **0.7006** (NOT_APPLICABLE KHÔNG nằm trong mẫu số)
- Target phủ đủ: **0** · phủ một phần: **20** · có gap chặn: **0**
- Case đã chạy: **103** · route đúng: **75/75**

### Chỉ số an toàn (mọi số phải là 0)

| Chỉ số | Giá trị |
|---|---|
| generic_leak | **0** |
| false_positive_simulation | **0** |
| false_refusal | **0** |
| semantic_loss | **0** |
| result_leakage | **0** |

Engine authenticity: REAL **19** · PARTIAL **1** · BROKEN **0**

## Ma trận

Ký hiệu: ✓ COVERED_PASS · ✗ COVERED_FAIL · ○ COVERAGE_GAP · – NOT_APPLICABLE

| Target | Family | supp… | supp… | insu… | unsu… | cros… | sema… | exec… | resu… | engine | visual |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `algorithm.binary_search` | interval_elimination | ✓ | ✓ | ✓ | ○ | ○ | – | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `algorithm.bubble_sort` | comparison_sort | ✓ | ✓ | ✓ | ✓ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `algorithm.count_if` | single_pass_scan | ✓ | ○ | ✓ | ○ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `algorithm.find_max` | single_pass_scan | ✓ | ○ | ✓ | ○ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `algorithm.find_min` | single_pass_scan | ✓ | ○ | ✓ | ○ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `algorithm.insertion_sort` | comparison_sort | ✓ | ○ | ✓ | ✓ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `algorithm.linear_search` | single_pass_scan | ✓ | ○ | ✓ | ○ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `algorithm.scan` | single_pass_scan | ✓ | ○ | ✓ | ○ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `algorithm.selection_sort` | comparison_sort | ✓ | ○ | ✓ | ✓ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `algorithm.sum_if` | single_pass_scan | ✓ | ○ | ✓ | ○ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `binary.base_conversion` | positional_representation | ✓ | ✓ | ✓ | ○ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `binary.decimal_to_binary` | positional_representation | ✓ | ✓ | ✓ | ○ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `database.relational_table_query` | relational_table_query | ✓ | ✓ | ✓ | ○ | ○ | ○ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `generic.rule_scene` | boolean_composition, structural_progressive_representation | ✓ | ✓ | ✓ | ○ | ✓ | ✓ | ✓ | ✓ | PARTIAL | NEEDS_VISUAL_REVIEW |
| `logic.and_gate` | boolean_composition | ✓ | ○ | – | ○ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `logic.boolean_dag` | boolean_composition | ✓ | ✓ | ✓ | ○ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `network.graph_traversal` | graph_traversal | ✓ | ✓ | ✓ | ○ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `network.packet_routing` | graph_traversal | ✓ | ○ | ✓ | ○ | ○ | ✓ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `network.protocol_encapsulation` | layered_pdu_transform | ✓ | ○ | – | ✓ | ○ | ○ | ✓ | ✓ | REAL | NEEDS_VISUAL_REVIEW |
| `tree.traversal` | tree_traversal | ✓ | ✓ | ✓ | ○ | ✓ | ✓ | ✓ | ✓ | REAL | REAL_VISUAL |

Cột theo thứ tự: supp… = `supported_canonical` · supp… = `supported_boundary` · insu… = `insufficient_input` · unsu… = `unsupported_variant_or_parameter` · cros… = `cross_family_near_miss` · sema… = `semantic_completeness` · exec… = `executor_authenticity` · resu… = `result_leakage`

## Coverage gap

| Target | Slot | Loại | Chặn? | Lý do |
|---|---|---|---|---|
| `algorithm.binary_search` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `algorithm.binary_search` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `algorithm.bubble_sort` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `algorithm.count_if` | supported_boundary | `missing_boundary` | không | chưa có fixture archetype supported_boundary cho target này |
| `algorithm.count_if` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `algorithm.count_if` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `algorithm.find_max` | supported_boundary | `missing_boundary` | không | chưa có fixture archetype supported_boundary cho target này |
| `algorithm.find_max` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `algorithm.find_max` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `algorithm.find_min` | supported_boundary | `missing_boundary` | không | chưa có fixture archetype supported_boundary cho target này |
| `algorithm.find_min` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `algorithm.find_min` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `algorithm.insertion_sort` | supported_boundary | `missing_boundary` | không | chưa có fixture archetype supported_boundary cho target này |
| `algorithm.insertion_sort` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `algorithm.linear_search` | supported_boundary | `missing_boundary` | không | chưa có fixture archetype supported_boundary cho target này |
| `algorithm.linear_search` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `algorithm.linear_search` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `algorithm.scan` | supported_boundary | `missing_boundary` | không | chưa có fixture archetype supported_boundary cho target này |
| `algorithm.scan` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `algorithm.scan` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `algorithm.selection_sort` | supported_boundary | `missing_boundary` | không | chưa có fixture archetype supported_boundary cho target này |
| `algorithm.selection_sort` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `algorithm.sum_if` | supported_boundary | `missing_boundary` | không | chưa có fixture archetype supported_boundary cho target này |
| `algorithm.sum_if` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `algorithm.sum_if` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `binary.base_conversion` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `binary.base_conversion` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `binary.decimal_to_binary` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `binary.decimal_to_binary` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `database.relational_table_query` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `database.relational_table_query` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `database.relational_table_query` | semantic_completeness | `missing_semantic_completeness` | không | family biểu đạt được nhưng chưa có fixture end-to-end |
| `generic.rule_scene` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `logic.and_gate` | supported_boundary | `missing_boundary` | không | chưa có fixture archetype supported_boundary cho target này |
| `logic.and_gate` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `logic.and_gate` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `logic.boolean_dag` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `logic.boolean_dag` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `network.graph_traversal` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `network.graph_traversal` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `network.packet_routing` | supported_boundary | `missing_boundary` | không | chưa có fixture archetype supported_boundary cho target này |
| `network.packet_routing` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
| `network.packet_routing` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `network.protocol_encapsulation` | supported_boundary | `missing_boundary` | không | chưa có fixture archetype supported_boundary cho target này |
| `network.protocol_encapsulation` | cross_family_near_miss | `missing_cross_family` | không | chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác |
| `network.protocol_encapsulation` | semantic_completeness | `missing_semantic_completeness` | không | family biểu đạt được nhưng chưa có fixture end-to-end |
| `tree.traversal` | unsupported_variant_or_parameter | `missing_unsupported` | không | family chưa có near-miss fixture cấp cơ chế (INTENTIONAL_GAP_MECHANISMS không phủ family này) |
