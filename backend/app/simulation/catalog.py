"""Bản chiếu registry phía backend — danh mục simulation_id hệ đang hỗ trợ.

Mỗi entry khai báo: domain, visual_mode, mô tả (cho stage classify),
schema structured-output + hợp đồng chữ (cho stage simulate), validator
(chốt chặn server-side) và cách đặt tiêu đề. Thêm domain mới (logic.*,
binary.*, network.*...) = thêm entry + validator riêng — KHÔNG sửa pipeline.
"""

from __future__ import annotations

from functools import partial
from typing import Callable

from app.simulation.descriptor import (
    FamilyId,
    FamilyMembership,
    ReachabilityLevel,
    ResultAuthority,
)
from app.simulation.families import (
    FAMILY_SELECTORS,
    SELECTOR_FAMILY_IDS,
    selector_for_token,
)
from app.simulation.families.sorting import (
    MECH_ADJACENT_SWAP,
    MECH_SELECT_EXTREME,
    MECH_SHIFT_INSERT,
    SORT_FAMILY_VERSION,
)
from app.simulation.authenticity import authenticity_descriptor
from app.simulation.mechanisms import FAMILY_MECHANISMS
from app.simulation.dsl.validator import validate_generic_config
from app.simulation.dsl.manifest import (
    bool_ops,
    interaction_types,
    manifest_contract_text,
    object_types,
    process_types,
    rule_types,
)
from app.simulation.scan_engine import (
    CONDITION_OPS as SCAN_OPS,
    MARKINGS as SCAN_MARKINGS,
    SCAN_VERSION,
    STOPS as SCAN_STOPS,
    UPDATE_KINDS as SCAN_UPDATES,
)
from app.simulation.table_query_engine import (
    AGGREGATE_FUNCS as _TQ_AGGREGATE_FUNCS,
    COLUMN_TYPES as _TQ_COLUMN_TYPES,
    COMPARE_OPS as _TQ_COMPARE_OPS,
    LOGIC_OPS as _TQ_LOGIC_OPS,
    MAX_COLUMNS as _TQ_MAX_COLUMNS,
    MAX_PREDICATE_DEPTH as _TQ_MAX_PREDICATE_DEPTH,
    MAX_PREDICATES as _TQ_MAX_PREDICATES,
    MAX_ROWS as _TQ_MAX_ROWS,
    MISSING_VALUE_MARKERS as _TQ_MISSING_MARKERS,
    PIPELINE_STAGE_ORDER as _TQ_STAGE_ORDER,
    SORT_DIRECTIONS as _TQ_SORT_DIRECTIONS,
    SPEC_VERSION as _TQ_SPEC_VERSION,
)
from app.simulation.character_encoding import (
    ASCII_MAX as _CE_ASCII_MAX,
    BMP_MAX as _CE_BMP_MAX,
    MAX_TEXT_CODE_POINTS as _CE_MAX_CP,
    SPEC_VERSION as _CE_SPEC_VERSION,
    encoding_enum as _ce_encodings,
)
from app.simulation.program_spec import (
    ARITHMETIC_OPS as _PG_ARITH,
    COMPARE_OPS as _PG_COMPARE,
    LOGIC_OPS as _PG_LOGIC,
    OPERAND_KINDS as _PG_OPERAND_KINDS,
    INT_MAX as _PG_INT_MAX,
    INT_MIN as _PG_INT_MIN,
    LIMITS as _PG_LIMITS,
    SPEC_VERSION as _PG_SPEC_VERSION,
    VALUE_TYPES as _PG_VALUE_TYPES,
    statement_kind_enum as _pg_statement_kinds,
)
from app.validation.character_encoding import validate_character_encoding_config
from app.validation.program import validate_program_config
from app.validation.table_query import validate_table_query_config
from app.validation.simulation import (
    ALGORITHM_IDS,
    ALGORITHM_NAMES_VI,
    validate_algorithm_config,
    validate_base_conversion_config,
    validate_binary_config,
    validate_boolean_dag_config,
    validate_color_config,
    validate_encapsulation_config,
    validate_logic_config,
    validate_web_style_config,
    web_style_domain,
    validate_network_config,
    validate_scan_config,
    validate_traverse_config,
    validate_tree_traversal_config,
)

# ── Domain algorithm ──────────────────────────────────────────

_ALGO_DESCRIPTIONS = {
    "find_max": "tìm giá trị lớn nhất trong một dãy số",
    "find_min": "tìm giá trị nhỏ nhất trong một dãy số",
    "sum_if": "tính tổng các phần tử của dãy thỏa một điều kiện so sánh",
    "count_if": "đếm số phần tử của dãy thỏa một điều kiện so sánh",
    "linear_search": "tìm một giá trị trong dãy bằng cách duyệt tuần tự từ đầu",
    "binary_search": "tìm một giá trị bằng cách CHIA ĐÔI vùng xét — tìm kiếm nhị phân (đề thường gợi ý 'tìm nhanh', 'chia đôi'). Dãy chưa sắp thứ tự VẪN chọn được: hệ tự sắp dãy trước và chú thích cho học sinh (không từ chối vì dãy chưa sắp)",
    "bubble_sort": "sắp xếp dãy bằng cách so sánh và đổi chỗ các cặp kề nhau (nổi bọt)",
    "insertion_sort": "sắp xếp dãy bằng cách rút từng phần tử chèn vào phần đã sắp (chèn)",
    "selection_sort": "sắp xếp dãy bằng cách mỗi lượt CHỌN phần tử cực trị của phần chưa sắp đưa về đầu (chọn)",
}

# Schema structured output (định dạng Gemini) cho config domain algorithm
_ALGO_CONFIG_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "problem": {
            "type": "OBJECT",
            "properties": {
                "summary": {"type": "STRING"},
                "input": {"type": "STRING"},
                "output": {"type": "STRING"},
            },
            "required": ["summary", "input", "output"],
        },
        "data": {
            "type": "OBJECT",
            "properties": {
                "array": {"type": "ARRAY", "items": {"type": "NUMBER"}},
                "labels": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
                "target": {"type": "NUMBER", "nullable": True},
                "condition": {
                    "type": "OBJECT",
                    "nullable": True,
                    "properties": {
                        "op": {"type": "STRING", "enum": [">", ">=", "<", "<=", "==", "!="]},
                        "value": {"type": "NUMBER"},
                    },
                    "required": ["op", "value"],
                },
                "order": {"type": "STRING", "enum": ["asc", "desc"], "nullable": True},
            },
            "required": ["array"],
        },
        "data_generated": {"type": "BOOLEAN", "nullable": True},
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": ["problem", "data"],
}

_ALGO_CONTRACT = """HỢP ĐỒNG CONFIG (domain algorithm):
- problem.summary/input/output: xác định bài toán theo SGK (tiếng Việt).
- data.array: dãy số của bài, 2–15 phần tử, đúng thứ tự đề cho. Đề cho nhiều hơn → lấy 12 phần tử đầu + ghi notes. Đề không cho số cụ thể → sinh 10 phần tử mẫu hợp ngữ cảnh + data_generated=true + ghi notes.
- data.labels: chỉ đặt khi đề nêu tên người/vật gắn với từng giá trị; độ dài phải khớp array; không bịa tên.
- data.target: BẮT BUỘC với linear_search/binary_search (giá trị cần tìm).
- data.condition {op, value}: BẮT BUỘC với sum_if/count_if.
- data.order "asc"/"desc": BẮT BUỘC với bubble_sort/insertion_sort.
- Trường không áp dụng → để null.
- KHÔNG sinh steps/timeline/kết quả — engine tự chạy."""


def _algo_title(config: dict, analysis: dict) -> str:
    summary = config.get("problem", {}).get("summary")
    if isinstance(summary, str) and summary:
        return summary
    goal = analysis.get("goal")
    return goal if isinstance(goal, str) and goal else "Mô phỏng thuật toán"


VISUAL_MODES: tuple[str, ...] = ("2d", "3d")
"""Từ vựng ĐÓNG cho chế độ trình bày (M17 P0). Thêm chế độ = thêm ở đây (một nguồn)."""


class SimSpec:
    """Đặc tả một mô phỏng RUNTIME trong danh mục backend (§C0: runtime target).

    M14 (§C1.2): mở rộng bằng metadata descriptor cấp-entry — `family_memberships`
    (quan hệ cơ chế↔family), `executor_id`, `reachability`, `curriculum_anchor`
    (§O2 bắt buộc cho public/AI-reachable), `known_gaps`. Mặc định rỗng để entry
    chưa khai không vỡ; lock (Task 2) buộc khai đủ cho 14 entry.
    """

    def __init__(
        self,
        simulation_id: str,
        domain: str,
        visual_modes: tuple[str, ...],
        description: str,
        config_schema: dict,
        contract: str,
        validate: Callable[[object], tuple[dict | None, str | None]],
        make_title: Callable[[dict, dict], str],
        *,
        family_memberships: tuple = (),
        executor_id: str | None = None,
        reachability: tuple = (),
        curriculum_anchor: str = "",
        known_gaps: tuple = (),
        config_contract_version: str = "",
    ) -> None:
        self.simulation_id = simulation_id
        self.domain = domain
        # M17 P0 — chế độ trình bày là DANH SÁCH ĐÓNG, không phải một chuỗi.
        # Audit authenticity phát hiện: khai cứng "2d" cho cả 22 entry khiến bảng
        # năng lực sinh tự động báo 3D = 0/22, tự phản chứng tên đề tài "2D/3D".
        # Danh sách này là NGUỒN; `visual_mode` (payload API) dẫn xuất từ nó, nên
        # không thể tồn tại một entry vừa khai 3d vừa khai scalar "2d" mâu thuẫn.
        # Parity FE↔BE khóa ở `capability-descriptors.test.ts`.
        unknown = [m for m in visual_modes if m not in VISUAL_MODES]
        if unknown:
            raise ValueError(f"{simulation_id}: chế độ trình bày lạ {unknown}")
        if not visual_modes or visual_modes[0] != "2d":
            raise ValueError(f"{simulation_id}: visual_modes phải bắt đầu bằng '2d'")
        if len(set(visual_modes)) != len(visual_modes):
            raise ValueError(f"{simulation_id}: visual_modes trùng lặp")
        self.visual_modes = tuple(visual_modes)
        self.description = description
        self.config_schema = config_schema
        self.contract = contract
        self.validate = validate
        self.make_title = make_title
        # M14 descriptor (§C1.2)
        self.family_memberships = family_memberships
        self.executor_id = executor_id if executor_id is not None else simulation_id
        self.reachability = reachability
        self.curriculum_anchor = curriculum_anchor
        self.known_gaps = known_gaps
        # M15 Task 2 — id phiên bản hợp đồng config (shape + VALIDATION POLICY,
        # §C2 rev2). Mặc định "" cho entry chưa khai; lock (test_family_registry)
        # buộc khai đủ cho 14 entry.
        self.config_contract_version = config_contract_version

    @property
    def visual_mode(self) -> str:
        """Chế độ MẶC ĐỊNH cho payload API — luôn dẫn xuất, không bao giờ khai tay.

        Giữ nguyên hình dạng payload cũ (`"2d"`) để không đổi hợp đồng API; khả
        năng 3D nằm ở `visual_modes` và đi ra descriptor. Frontend chọn chế độ
        render từ hợp đồng module (`effectiveVisualMode`), không từ trường này.
        """
        return self.visual_modes[0]

    def supports_3d(self) -> bool:
        return "3d" in self.visual_modes


CATALOG: dict[str, SimSpec] = {}

# M14 §C1 — reachability chung + metadata descriptor per-id cho 8 algorithm.
_R_FULL = (
    ReachabilityLevel.REGISTERED,
    ReachabilityLevel.LIBRARY_DISCOVERABLE,
    ReachabilityLevel.AI_REACHABLE_PUBLIC,
)


def _scan_member(owned: tuple[str, ...]) -> tuple[FamilyMembership, ...]:
    return (
        FamilyMembership(
            FamilyId.SINGLE_PASS_SCAN, ResultAuthority.COMPUTATION,
            owned_mechanisms=owned,
        ),
    )


# family_memberships + curriculum_anchor cho từng thuật toán (§O2). bubble/insertion
# mang variant_id/family_spec_version/mechanism_id → cross-lock với SORTING_SELECTOR.
# find_max/find_min/sum_if/count_if/linear_search (M15 W2 Task 12): mỗi bài SỞ HỮU
# đúng một cơ chế canonical trong single_pass_scan — KHÔNG selector (khóa 10), 5 bài
# vẫn là choice độc lập trên menu classify; algorithm.scan là catch-all trong-family.
_ALGO_META: dict[str, dict] = {
    "find_max": {
        "memberships": _scan_member(("single_pass_scan.track_extreme",)),
        "anchor": "T10 CĐ5 · T11CS B17",
    },
    "find_min": {
        "memberships": _scan_member(("single_pass_scan.track_extreme",)),
        "anchor": "T10 CĐ5 · T11CS B17",
    },
    "sum_if": {
        "memberships": _scan_member(("single_pass_scan.accumulate_conditional",)),
        "anchor": "T10 CĐ5 · T11CS B17",
    },
    "count_if": {
        "memberships": _scan_member(("single_pass_scan.count_conditional",)),
        "anchor": "T10 CĐ5 · T11CS B17",
    },
    "linear_search": {
        "memberships": _scan_member(("single_pass_scan.find_equal_early_stop",)),
        "anchor": "T10 CĐ5 · T11CS B17",
    },
    "binary_search": {
        "memberships": (
            FamilyMembership(
                FamilyId.INTERVAL_ELIMINATION, ResultAuthority.COMPUTATION,
                owned_mechanisms=("interval_elimination.halve_sorted_interval",),
            ),
        ),
        "anchor": "T11CS B19",
    },
    "bubble_sort": {
        "memberships": (
            FamilyMembership(
                FamilyId.COMPARISON_SORT, ResultAuthority.COMPUTATION,
                variant_id="bubble", family_spec_version=SORT_FAMILY_VERSION,
                mechanism_id=MECH_ADJACENT_SWAP,
                owned_mechanisms=(MECH_ADJACENT_SWAP,),
            ),
        ),
        "anchor": "T11CS B21–22",
    },
    "insertion_sort": {
        "memberships": (
            FamilyMembership(
                FamilyId.COMPARISON_SORT, ResultAuthority.COMPUTATION,
                variant_id="insertion", family_spec_version=SORT_FAMILY_VERSION,
                mechanism_id=MECH_SHIFT_INSERT,
                owned_mechanisms=(MECH_SHIFT_INSERT,),
            ),
        ),
        "anchor": "T11CS B21–22",
    },
    # M17 W1 — Selection Sort (gap flip → owned). reachability KHÔNG có
    # library_discoverable (tiền lệ algorithm.scan): chưa có mẫu offline công
    # khai; AI-reachable qua selector token.
    "selection_sort": {
        "memberships": (
            FamilyMembership(
                FamilyId.COMPARISON_SORT, ResultAuthority.COMPUTATION,
                variant_id="selection", family_spec_version=SORT_FAMILY_VERSION,
                mechanism_id=MECH_SELECT_EXTREME,
                owned_mechanisms=(MECH_SELECT_EXTREME,),
            ),
        ),
        "anchor": "T11CS B21–22",
        # W4B-3D — nay có mẫu offline công khai.
        "reachability": _R_FULL,
    },
}

for _aid in ALGORITHM_IDS:
    _sim_id = f"algorithm.{_aid}"
    CATALOG[_sim_id] = SimSpec(
        simulation_id=_sim_id,
        domain="algorithm",
        visual_modes=("2d",),
        description=f"{ALGORITHM_NAMES_VI[_aid]} — {_ALGO_DESCRIPTIONS[_aid]}",
        config_schema=_ALGO_CONFIG_SCHEMA,
        contract=_ALGO_CONTRACT,
        validate=partial(validate_algorithm_config, _aid),
        make_title=_algo_title,
        family_memberships=_ALGO_META[_aid]["memberships"],
        reachability=_ALGO_META[_aid].get("reachability", _R_FULL),
        curriculum_anchor=_ALGO_META[_aid]["anchor"],
        config_contract_version="algo-cfg-1",
    )


# ── Domain logic (M5) ─────────────────────────────────────────

# Gemini structured output không nhận enum kiểu số (bắt buộc STRING) → bỏ enum,
# giữ INTEGER; validator server (validate_logic_config) vẫn ép inputA/inputB ∈ {0,1}.
_LOGIC_AND_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "inputA": {"type": "INTEGER"},
        "inputB": {"type": "INTEGER"},
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": ["inputA", "inputB"],
}

_LOGIC_AND_CONTRACT = """HỢP ĐỒNG CONFIG (logic.and_gate):
- inputA, inputB: giá trị đầu vào ban đầu của hai chân, mỗi cái là 0 hoặc 1.
- Đề không nói giá trị cụ thể → để cả hai bằng 0 (người học sẽ tự bật/tắt).
- KHÔNG sinh output, state, bảng chân trị — engine tự tính output = A AND B."""

CATALOG["logic.and_gate"] = SimSpec(
    simulation_id="logic.and_gate",
    domain="logic",
    visual_modes=("2d",),
    description="cổng logic AND — mô phỏng hai đầu vào bật/tắt và đầu ra; AND chỉ ra 1 khi cả hai đầu vào đều là 1",
    config_schema=_LOGIC_AND_SCHEMA,
    contract=_LOGIC_AND_CONTRACT,
    validate=validate_logic_config,
    make_title=lambda config, analysis: "Cổng logic AND",
    family_memberships=(
        FamilyMembership(
            FamilyId.BOOLEAN_COMPOSITION, ResultAuthority.COMPUTATION,
            owned_mechanisms=("boolean_composition.single_gate_truth_table",),
        ),
    ),
    reachability=_R_FULL,
    curriculum_anchor="T10 B5 · T10 B9",
    config_contract_version="logic-cfg-1",
)


# ── logic.boolean_dag (M17 W1) — mạch nhiều cổng + bảng chân trị ──

_LOGIC_DAG_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "inputs": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "label": {"type": "STRING", "nullable": True},
                    "value": {"type": "INTEGER"},
                },
                "required": ["id", "value"],
            },
        },
        "gates": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "op": {"type": "STRING", "enum": ["AND", "OR", "NOT", "XOR"]},
                    "inputs": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["id", "op", "inputs"],
            },
        },
        "output": {"type": "STRING"},
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": ["inputs", "gates", "output"],
}

_LOGIC_DAG_CONTRACT = """HỢP ĐỒNG CONFIG (logic.boolean_dag):
- inputs: 1–4 đầu vào {id, label?, value 0/1}. Đề không cho giá trị → value 0.
- gates: 1–8 cổng {id, op, inputs}. op ∈ {AND, OR, NOT, XOR}; NOT đúng 1 đầu vào, còn lại đúng 2. "inputs" là id của đầu vào hoặc cổng KHÁC (KHÔNG vòng — DAG).
- output: id của cổng đầu ra (khai báo rõ). Mọi cổng phải góp vào đầu ra.
- Biểu thức đề cho (vd A ∧ (B ∨ ¬C)) → dựng đúng cây cổng tương ứng.
- KHÔNG sinh giá trị cổng / bảng chân trị / kết quả — engine tự đánh giá topo và sinh đủ bảng chân trị."""

CATALOG["logic.boolean_dag"] = SimSpec(
    simulation_id="logic.boolean_dag",
    domain="logic",
    visual_modes=("2d",),
    description=(
        "mạch logic NHIỀU cổng AND/OR/NOT/XOR nối nhau (tối đa 4 đầu vào, 8 cổng) "
        "+ BẢNG CHÂN TRỊ do engine sinh — dùng khi đề cho mạch/biểu thức logic "
        "nhiều phép (kể cả XOR) hoặc yêu cầu bảng chân trị. Một cổng AND hai đầu "
        "vào đơn lẻ → logic.and_gate; cảnh đèn-công tắc tự dàn dựng → generic"
    ),
    config_schema=_LOGIC_DAG_SCHEMA,
    contract=_LOGIC_DAG_CONTRACT,
    validate=validate_boolean_dag_config,
    make_title=lambda config, analysis: "Mạch logic nhiều cổng",
    family_memberships=(
        FamilyMembership(
            FamilyId.BOOLEAN_COMPOSITION, ResultAuthority.COMPUTATION,
            owned_mechanisms=("boolean_composition.bounded_gate_dag",),
        ),
    ),
    # W4B-3D — nay CÓ mẫu offline công khai (Thư viện học sinh), nên
    # `library_discoverable` là khai ĐÚNG SỰ THẬT, không phải nâng hạng.
    reachability=_R_FULL,
    curriculum_anchor="T10 B5 · T12CS B22–24",
    config_contract_version="logic-dag-1.0",
)


# ── Domain binary (M5) ────────────────────────────────────────

_BINARY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "decimalValue": {"type": "INTEGER"},
        "bitWidth": {"type": "INTEGER"},
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": ["decimalValue", "bitWidth"],
}

_BINARY_CONTRACT = """HỢP ĐỒNG CONFIG (binary.decimal_to_binary):
- decimalValue: số thập phân cần đổi sang nhị phân, nguyên từ 0 đến 255.
- bitWidth: số bit hiển thị (1–8). Chọn đủ để chứa giá trị (vd 13 → 4 bit).
- KHÔNG sinh bits, state, giá trị từng bit — engine tự tính biểu diễn nhị phân."""

CATALOG["binary.decimal_to_binary"] = SimSpec(
    simulation_id="binary.decimal_to_binary",
    domain="binary",
    visual_modes=("2d",),
    description="đổi số thập phân sang nhị phân — mô phỏng các bit trọng số 8/4/2/1 bật/tắt và giá trị thập phân tương ứng",
    config_schema=_BINARY_SCHEMA,
    contract=_BINARY_CONTRACT,
    validate=validate_binary_config,
    make_title=lambda config, analysis: f"Đổi {config.get('decimalValue', '')} sang nhị phân",
    family_memberships=(
        FamilyMembership(
            FamilyId.POSITIONAL_REPRESENTATION, ResultAuthority.COMPUTATION,
            owned_mechanisms=("positional_representation.binary_positional_weights",),
        ),
    ),
    reachability=_R_FULL,
    curriculum_anchor="T10 B4",
    config_contract_version="binary-cfg-1",
)


# ── binary.base_conversion (M17 W1) — đổi cơ số tổng quát {2,8,10,16} ──

_BASECONV_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "sourceBase": {"type": "INTEGER"},
        "targetBase": {"type": "INTEGER"},
        "inputValue": {"type": "STRING"},
        "strategy": {
            "type": "STRING",
            "enum": ["quotient_remainder", "positional_weights", "two_stage"],
            "nullable": True,
        },
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": ["sourceBase", "targetBase", "inputValue"],
}

_BASECONV_CONTRACT = """HỢP ĐỒNG CONFIG (binary.base_conversion):
- sourceBase, targetBase: cơ số nguồn/đích, MỖI cái thuộc {2, 8, 10, 16}, PHẢI khác nhau.
- inputValue: CHUỖI chữ số của số cần đổi, viết theo sourceBase (vd "2026" cơ số 10, "9C" cơ số 16, "755" cơ số 8, "101101" cơ số 2). Giá trị tối đa 65535.
- strategy: BỎ TRỐNG — hệ tự dẫn xuất (10→X: chia lấy dư; X→10: trọng số vị trí; X→Y: hai giai đoạn qua thập phân).
- KHÔNG sinh các bước chia/tổng/kết quả — engine tất định tự tính toàn bộ trace và đáp số."""

CATALOG["binary.base_conversion"] = SimSpec(
    simulation_id="binary.base_conversion",
    domain="binary",
    visual_modes=("2d",),
    description=(
        "đổi một số giữa các hệ cơ số 2, 8, 10, 16 (nhị phân/bát phân/thập phân/"
        "thập lục phân) — engine tất định dựng trace chia-lấy-dư, trọng số vị trí "
        "hoặc hai giai đoạn qua thập phân và tự tính kết quả. Dùng khi đề yêu cầu "
        "ĐỔI CƠ SỐ (kể cả hex/octal); riêng bài 'bật bit trọng số 8/4/2/1' trực "
        "quan thì dùng binary.decimal_to_binary"
    ),
    config_schema=_BASECONV_SCHEMA,
    contract=_BASECONV_CONTRACT,
    validate=validate_base_conversion_config,
    make_title=lambda config, analysis: (
        f"Đổi {config.get('inputValue', '')} từ cơ số {config.get('sourceBase', '')} "
        f"sang cơ số {config.get('targetBase', '')}"
    ),
    family_memberships=(
        FamilyMembership(
            FamilyId.POSITIONAL_REPRESENTATION, ResultAuthority.COMPUTATION,
            # Sở hữu CẢ HAI cơ chế positional: non_binary_base (gap flip W1) +
            # binary_positional_weights (dec↔bin cũng là đổi cơ số hợp lệ —
            # nhiều target cùng own một cơ chế có tiền lệ find_max/find_min).
            owned_mechanisms=(
                "positional_representation.binary_positional_weights",
                "positional_representation.non_binary_base",
            ),
        ),
    ),
    # Như scan/selection: AI-reachable, KHÔNG library_discoverable (chưa có mẫu offline)
    # W4B-3D — nay CÓ mẫu offline công khai (Thư viện học sinh), nên
    # `library_discoverable` là khai ĐÚNG SỰ THẬT, không phải nâng hạng.
    reachability=_R_FULL,
    curriculum_anchor="T10 B4",
    config_contract_version="baseconv-1.0",
)


# ── Domain color (W5A) — mô hình màu RGB ──────────────────────
#
# VÌ SAO TARGET NÀY TỒN TẠI. Đề "màu RGB" xưa nay rơi vào `generic.rule_scene`
# và bị dựng thành các bước hé lộ đối tượng — tức học sinh xem một cảnh kể về
# màu thay vì TRỘN màu. Cơ chế ẩn thật của bài này là ba đại lượng độc lập 0..255
# cộng ánh sáng lại thành một màu nhìn thấy được; không có kênh kéo được và
# không có ô màu đổi theo thì cơ chế ấy chưa từng xuất hiện trên màn hình.
#
# `visual_modes=("2d",)`: màu là thuộc tính bề mặt, không có chiều thứ ba nào
# mang nghĩa — bày toggle 3D ở đây là hỏi một câu học sinh không có cơ sở trả lời
# (chính sách W4B-2R).

_COLOR_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "red": {"type": "INTEGER"},
        "green": {"type": "INTEGER"},
        "blue": {"type": "INTEGER"},
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": ["red", "green", "blue"],
    # Hợp đồng ĐÓNG ngay từ tầng schema: không để LLM điền `hex`/`colorName`
    # rồi bị validator từ chối ở lượt sau (một vòng retry tiêu quota để học lại
    # điều schema nói được từ đầu).
    "additionalProperties": False,
}

_COLOR_CONTRACT = """HỢP ĐỒNG CONFIG (color.rgb_model):
- red, green, blue: BA số nguyên, mỗi số từ 0 đến 255 — cường độ của một kênh.
- Đề nêu một màu bằng tên (đỏ, trắng, vàng…) → quy về ba kênh tương ứng (đỏ = 255,0,0; trắng = 255,255,255; vàng = 255,255,0).
- Đề KHÔNG nêu màu cụ thể → cho một màu trộn để học sinh thấy cả ba kênh cùng làm việc (vd 120, 90, 200).
- KHÔNG sinh mã HEX, tên màu, ô màu hay bước nào — engine tất định tính màu kết quả, HEX và rgb() từ ba kênh."""

CATALOG["color.rgb_model"] = SimSpec(
    simulation_id="color.rgb_model",
    domain="color",
    visual_modes=("2d",),
    description=(
        "mô hình màu RGB — học sinh kéo cường độ ba kênh đỏ/lục/lam trong khoảng "
        "0–255 và thấy ngay màu kết quả cùng cách viết rgb() và mã HEX; dùng cho "
        "đề về biểu diễn màu, trộn màu ánh sáng, mã màu trong HTML/CSS"
    ),
    config_schema=_COLOR_SCHEMA,
    contract=_COLOR_CONTRACT,
    validate=validate_color_config,
    make_title=lambda config, analysis: "Mô hình màu RGB",
    family_memberships=(
        FamilyMembership(
            FamilyId.POSITIONAL_REPRESENTATION, ResultAuthority.COMPUTATION,
            owned_mechanisms=("positional_representation.rgb_channel_composition",),
        ),
    ),
    reachability=_R_FULL,
    curriculum_anchor="T10 B3 (biểu diễn hình ảnh) · T12 CĐ4 (mã màu HTML/CSS)",
    config_contract_version="color-cfg-1",
)


# ── Domain network (M5) ───────────────────────────────────────

_NETWORK_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "nodes": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "type": {
                        "type": "STRING",
                        "enum": ["client", "router", "server", "switch", "isp"],
                    },
                },
                "required": ["id", "type"],
            },
        },
        "links": {"type": "ARRAY", "items": {"type": "ARRAY", "items": {"type": "STRING"}}},
        "source": {"type": "STRING"},
        "destination": {"type": "STRING"},
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": ["nodes", "links", "source", "destination"],
}

_NETWORK_CONTRACT = """HỢP ĐỒNG CONFIG (network.packet_routing):
- nodes: 2–8 nút, mỗi nút {id, type} với type là client/router/server/switch/isp.
- links: danh sách cặp [id1, id2] nối hai nút CÓ THẬT (đồ thị vô hướng).
- source, destination: id nút nguồn và đích (khác nhau), phải có đường đi.
- Đề không cho topo cụ thể → dựng topo hợp lý (vd client–router–isp–server).
- KHÔNG sinh route, timeline, packet, frame — engine tự tìm đường và dựng diễn biến."""

CATALOG["network.packet_routing"] = SimSpec(
    simulation_id="network.packet_routing",
    domain="network",
    # W4B-2R: 2D_ONLY. Bản 3D cũ (M8) tự khai `role: "architectural_poc"` với
    # `meaningOfZ = "bố cục, KHÔNG mang nghĩa khái niệm"` — tức chính module thừa
    # nhận chiều sâu ở đây không chở ngữ nghĩa nào. Cơ chế của bài là TOPOLOGY +
    # ĐƯỜNG ĐI, đọc trọn vẹn trên mặt phẳng. Giữ toggle chỉ để chứng minh "sản
    # phẩm có 3D" chính là `2D_AND_3D_BY_DEFAULT` mà chính sách biểu diễn cấm.
    # 3D sư phạm còn nguyên ở `network.protocol_encapsulation` (Z = tầng giao thức).
    visual_modes=("2d",),
    description="định tuyến gói tin trên MỘT MẠNG CHO SẴN đầy đủ — mô phỏng gói tin đi từng chặng từ máy nguồn qua các router tới máy đích. CHỈ dùng khi topology có sẵn ngay; KHÔNG dựng mạng từng bước (không tạo từng thiết bị/liên kết dần). Cơ chế ẩn là ĐƯỜNG ĐI qua các NÚT thiết bị; bài hỏi dữ liệu được ĐÓNG GÓI/THÁO GÓI qua các TẦNG giao thức (thêm/gỡ TCP, IP, header) → network.protocol_encapsulation",
    config_schema=_NETWORK_SCHEMA,
    contract=_NETWORK_CONTRACT,
    validate=validate_network_config,
    make_title=lambda config, analysis: "Đường đi của gói tin trong mạng",
    family_memberships=(
        FamilyMembership(
            FamilyId.GRAPH_TRAVERSAL, ResultAuthority.COMPUTATION,
            owned_mechanisms=("graph_traversal.unweighted_hop_bfs",),
        ),
    ),
    reachability=_R_FULL,
    curriculum_anchor="T10 CĐ2 · T12 CĐ2",
    known_gaps=("đường đi ngắn nhất có trọng số (Dijkstra)", "dựng topo từng bước"),
    config_contract_version="net-cfg-1",
)


# ── network.graph_traversal (M17 W1) — duyệt đồ thị BFS/DFS tổng quát ──

_TRAVERSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "nodes": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "label": {"type": "STRING", "nullable": True},
                },
                "required": ["id"],
            },
        },
        "edges": {"type": "ARRAY", "items": {"type": "ARRAY", "items": {"type": "STRING"}}},
        "directed": {"type": "BOOLEAN", "nullable": True},
        "start": {"type": "STRING"},
        "goal": {"type": "STRING", "nullable": True},
        "variant": {"type": "STRING", "enum": ["bfs", "dfs"]},
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": ["nodes", "edges", "start", "variant"],
}

_TRAVERSE_CONTRACT = """HỢP ĐỒNG CONFIG (network.graph_traversal):
- nodes: 2–10 nút {id, label?}.
- edges: tối đa 20 cạnh [idA, idB] nối hai nút CÓ THẬT (không tự nối).
- directed: true nếu đồ thị CÓ hướng (cạnh một chiều A→B); mặc định false (vô hướng).
- start: id nút bắt đầu duyệt. goal: id nút đích (BỎ TRỐNG nếu chỉ duyệt toàn bộ, không tìm đường).
- variant: "bfs" (theo chiều rộng — hàng đợi) hoặc "dfs" (theo chiều sâu — ngăn xếp) theo yêu cầu đề.
- KHÔNG sinh thứ tự thăm / đường đi / kết quả — engine tự duyệt và dựng lại đường đi. Không-đến-được là kết quả hợp lệ.
- KHÔNG dùng cho đường đi ngắn nhất CÓ TRỌNG SỐ (Dijkstra) — cơ chế đó chưa hỗ trợ."""

CATALOG["network.graph_traversal"] = SimSpec(
    simulation_id="network.graph_traversal",
    domain="network",
    visual_modes=("2d",),
    description=(
        "duyệt đồ thị TỔNG QUÁT bằng BFS (chiều rộng) hoặc DFS (chiều sâu) trên "
        "đồ thị có/không hướng KHÔNG trọng số — mô phỏng frontier (hàng đợi/ngăn "
        "xếp), thứ tự thăm, và tìm đường + dựng lại đường đi khi có đích (không "
        "đến được là kết quả hợp lệ). Dùng cho bài duyệt đồ thị/cây bằng BFS/DFS "
        "hoặc tìm đường KHÔNG trọng số. Bài định tuyến gói tin qua thiết bị mạng "
        "cho sẵn → network.packet_routing; đường đi NGẮN NHẤT CÓ TRỌNG SỐ chưa hỗ trợ"
    ),
    config_schema=_TRAVERSE_SCHEMA,
    contract=_TRAVERSE_CONTRACT,
    validate=validate_traverse_config,
    make_title=lambda config, analysis: (
        f"Duyệt đồ thị {str(config.get('variant', '')).upper()}"
    ),
    family_memberships=(
        FamilyMembership(
            FamilyId.GRAPH_TRAVERSAL, ResultAuthority.COMPUTATION,
            owned_mechanisms=(
                "graph_traversal.breadth_first",
                "graph_traversal.depth_first",
            ),
        ),
    ),
    # W4B-3D — nay CÓ mẫu offline công khai (Thư viện học sinh), nên
    # `library_discoverable` là khai ĐÚNG SỰ THẬT, không phải nâng hạng.
    reachability=_R_FULL,
    curriculum_anchor="T11CS B17 · T12 CĐ2",
    known_gaps=("đường đi ngắn nhất có trọng số (Dijkstra) — future family",),
    config_contract_version="traverse-1.0",
)


# ── tree.traversal (M17 W2A) — duyệt cây nhị phân bounded ──────

_TREE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "specVersion": {"type": "STRING", "enum": ["tree-1.0"]},
        "variant": {"type": "STRING", "enum": ["preorder", "inorder", "postorder", "level_order"]},
        "rootId": {"type": "STRING"},
        "nodes": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "label": {"type": "STRING", "nullable": True},
                    "left": {"type": "STRING", "nullable": True},
                    "right": {"type": "STRING", "nullable": True},
                },
                "required": ["id"],
            },
        },
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": ["specVersion", "variant", "rootId", "nodes"],
}

_PREDICATE_LEAF = {
    "type": "OBJECT",
    "properties": {
        "op": {"type": "STRING", "enum": list(_TQ_COMPARE_OPS)},
        "column": {"type": "STRING"},
        # Gemini structured output không có union type — nhận CHUỖI rồi validator
        # ép về kiểu cột đã khai (một chỗ ép, không đoán rải rác).
        "value": {"type": "STRING"},
    },
    "required": ["op", "column", "value"],
}
_TABLE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "specVersion": {"type": "STRING", "enum": [_TQ_SPEC_VERSION]},
        "schema": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "type": {"type": "STRING", "enum": list(_TQ_COLUMN_TYPES)},
                    "label": {"type": "STRING", "nullable": True},
                    # W2B-PATCH §C — cột này có được phép có ô trống không.
                    # Bỏ trống = mặc định theo kiểu (số/đúng-sai nhận ô trống,
                    # cột chữ giữ nguyên literal).
                    "nullable": {"type": "BOOLEAN", "nullable": True},
                },
                "required": ["name", "type"],
            },
        },
        # Mỗi dòng là mảng ô THEO ĐÚNG THỨ TỰ cột trong schema — mảng-của-mảng
        # tránh được giới hạn "object không có khoá động" của structured output.
        "rows": {"type": "ARRAY", "items": {"type": "ARRAY", "items": {"type": "STRING"}}},
        "filter": {
            "type": "OBJECT",
            "properties": {
                "op": {"type": "STRING", "enum": list(_TQ_COMPARE_OPS) + list(_TQ_LOGIC_OPS)},
                "column": {"type": "STRING", "nullable": True},
                "value": {"type": "STRING", "nullable": True},
                "clauses": {"type": "ARRAY", "items": _PREDICATE_LEAF, "nullable": True},
            },
            "required": ["op"],
            "nullable": True,
        },
        "projection": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        "sort": {
            "type": "OBJECT",
            "properties": {
                "column": {"type": "STRING"},
                "direction": {"type": "STRING", "enum": list(_TQ_SORT_DIRECTIONS)},
            },
            "required": ["column"],
            "nullable": True,
        },
        "limit": {"type": "INTEGER", "nullable": True},
        "aggregate": {
            "type": "OBJECT",
            "properties": {
                "func": {"type": "STRING", "enum": list(_TQ_AGGREGATE_FUNCS)},
                "column": {"type": "STRING", "nullable": True},
            },
            "required": ["func"],
            "nullable": True,
        },
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": ["specVersion", "schema", "rows"],
}

_TABLE_CONTRACT = f"""HỢP ĐỒNG CONFIG (database.relational_table_query — TRUY VẤN BẢNG):
- specVersion: đúng "{_TQ_SPEC_VERSION}".
- schema: 1–{_TQ_MAX_COLUMNS} cột {{name, type, label?, nullable?}}. type ∈ {', '.join(_TQ_COLUMN_TYPES)}. Lấy ĐÚNG tên cột đề cho. nullable: bỏ trống là đủ (cột số/đúng-sai mặc định nhận ô trống); chỉ đặt false khi đề nói rõ cột đó BẮT BUỘC có dữ liệu.
- rows: 1–{_TQ_MAX_ROWS} dòng. MỖI dòng là MẢNG ô theo ĐÚNG thứ tự cột của schema, mọi ô ghi dạng CHUỖI (số vẫn ghi "8.5"). Ô đề KHÔNG cho dữ liệu: để chuỗi rỗng, hoặc chép nguyên chữ đề dùng ({', '.join(_TQ_MISSING_MARKERS)}) — hệ tự hiểu là ô trống, KHÔNG được thay bằng 0. CHÉP ĐÚNG dữ liệu đề cho — TUYỆT ĐỐI không bịa thêm dòng, không tạo bảng mẫu.
- filter (tuỳ chọn): một so sánh {{op, column, value}} hoặc một phép {{op:"and"|"or", clauses:[…]}} với ≤{_TQ_MAX_PREDICATES} so sánh, lồng ≤{_TQ_MAX_PREDICATE_DEPTH} tầng. op so sánh ∈ {', '.join(_TQ_COMPARE_OPS)}; toán tử phải hợp kiểu cột (">" chỉ cho số).
- projection (tuỳ chọn): danh sách cột cần hiển thị.
- sort (tuỳ chọn): MỘT khoá {{column, direction}} — sắp xếp ổn định do engine làm.
- limit (tuỳ chọn): số nguyên ≥1, KHÔNG lớn hơn số dòng.
- aggregate (tuỳ chọn): MỘT hàm {{func, column?}}. func ∈ {', '.join(_TQ_AGGREGATE_FUNCS)}. sum/avg cần cột kiểu số; count có thể không cột.
- THỨ TỰ CHẠY CỐ ĐỊNH (engine sở hữu, không đổi được): {' → '.join(_TQ_STAGE_ORDER)}. Nghĩa là aggregate tính TRÊN các dòng CÒN LẠI SAU limit. Đề cần thứ tự khác (vd lọc theo một giá trị phải tính từ chính bảng đó) là TRUY VẤN LỒNG — ngoài phạm vi, phải từ chối chứ không đổi thứ tự.
- ĐỦ TẦNG: đề hỏi bao nhiêu tầng thì spec phải có đủ bấy nhiêu. Hỏi "lấy 3 bạn đầu rồi tính trung bình" mà bỏ limit hoặc bỏ aggregate là trả lời thiếu — hệ sẽ từ chối, không nhận spec nửa vời.
- KHÔNG sinh: dòng kết quả, tập đã lọc, kết quả sắp xếp, giá trị tổng hợp, hay phán quyết giữ/loại từng dòng — engine tính tất định và dựng timeline.
- CHỈ dùng cho truy vấn MỘT bảng. KHÔNG dùng cho: JOIN nhiều bảng, truy vấn lồng, thêm/sửa/xoá dữ liệu, SQL tự do, GROUP BY nhiều nhóm, kết nối CSDL thật."""

_TREE_CONTRACT = """HỢP ĐỒNG CONFIG (tree.traversal — duyệt CÂY NHỊ PHÂN):
- specVersion: đúng "tree-1.0".
- variant: "preorder" (trước — gốc/trái/phải), "inorder" (giữa — trái/gốc/phải), "postorder" (sau — trái/phải/gốc), "level_order" (theo mức — BFS). Chọn ĐÚNG theo đề.
- rootId: id node GỐC (không node nào trỏ tới nó).
- nodes: 1–15 node {id, label?, left?, right?}. left/right là id con TRÁI/PHẢI hoặc bỏ trống. Cây nhị phân THẬT: mỗi node có tối đa 1 cha, không cycle, không rời rạc, sâu ≤5 tầng. Lấy ĐÚNG cấu trúc + nhãn đề cho, KHÔNG bịa node/cây mặc định.
- KHÔNG sinh thứ tự duyệt / stack / queue / kết quả — engine tự duyệt tất định và dựng timeline.
- CHỈ dùng cho DUYỆT cây nhị phân. KHÔNG dùng cho: chèn/tìm/xoá BST, cân bằng AVL, heap, cây biểu thức, cây n-nhánh, duyệt ĐỒ THỊ chung (→ network.graph_traversal)."""

CATALOG["tree.traversal"] = SimSpec(
    simulation_id="tree.traversal",
    domain="tree",
    visual_modes=("2d",),
    description=(
        "duyệt CÂY NHỊ PHÂN hữu hạn theo 4 thứ tự: preorder (trước — gốc/trái/"
        "phải), inorder (giữa — trái/gốc/phải), postorder (sau — trái/phải/gốc), "
        "level_order (theo mức/BFS) — engine dựng ngăn xếp/hàng đợi, thứ tự thăm, "
        "timeline, kết quả. Dùng khi đề DUYỆT một cây nhị phân theo thứ tự trước/"
        "giữa/sau/theo mức. KHÔNG dùng cho chèn/tìm/xoá BST, cân bằng AVL/đỏ-đen, "
        "heap, cây biểu thức, cây n-nhánh, hay duyệt ĐỒ THỊ chung (đồ thị đỉnh-"
        "cạnh, BFS/DFS tổng quát → network.graph_traversal)"
    ),
    config_schema=_TREE_SCHEMA,
    contract=_TREE_CONTRACT,
    validate=validate_tree_traversal_config,
    make_title=lambda config, analysis: (
        f"Duyệt cây nhị phân — {config.get('variant', '')}"
    ),
    family_memberships=(
        FamilyMembership(
            FamilyId.TREE_TRAVERSAL, ResultAuthority.COMPUTATION,
            owned_mechanisms=(
                "tree_traversal.preorder",
                "tree_traversal.inorder",
                "tree_traversal.postorder",
                "tree_traversal.level_order",
            ),
        ),
    ),
    # W4B-3D — nay CÓ mẫu offline công khai (Thư viện học sinh), nên
    # `library_discoverable` là khai ĐÚNG SỰ THẬT, không phải nâng hạng.
    reachability=_R_FULL,
    curriculum_anchor="T11CS B17 · T11 CĐ (cấu trúc dữ liệu cây)",
    known_gaps=(
        "BST/AVL/heap/cây biểu thức/cây n-nhánh — ngoài phạm vi duyệt cây nhị phân",
    ),
    config_contract_version="tree-1.0",
)


CATALOG["database.relational_table_query"] = SimSpec(
    simulation_id="database.relational_table_query",
    domain="database",
    visual_modes=("2d",),
    description=(
        "truy vấn MỘT BẢNG dữ liệu hữu hạn cho sẵn (bảng có lược đồ: tên cột + "
        "kiểu text/số/đúng-sai): LỌC dòng theo điều kiện, CHỌN cột cần hiển thị, "
        "SẮP XẾP ổn định theo một cột, LẤY n dòng đầu, và TÍNH đếm/tổng/trung "
        "bình/nhỏ nhất/lớn nhất — engine duyệt từng dòng, tự quyết giữ hay loại, "
        "tự tích luỹ và dựng timeline. Dùng khi đề CHO SẴN một bảng (danh sách "
        "học sinh, sản phẩm, nhân viên…) rồi hỏi lọc/sắp xếp/thống kê trên bảng "
        "đó. KHÔNG dùng cho: ghép nhiều bảng (JOIN), truy vấn lồng, thêm/sửa/xoá "
        "dữ liệu, SQL tự do, gom nhóm nhiều nhóm (GROUP BY), kết nối CSDL thật, "
        "hay đề chỉ có một DÃY SỐ đơn lẻ không phải bảng (→ dùng bài quét dãy)"
    ),
    config_schema=_TABLE_SCHEMA,
    contract=_TABLE_CONTRACT,
    validate=validate_table_query_config,
    make_title=lambda config, analysis: "Truy vấn bảng dữ liệu",
    family_memberships=(
        FamilyMembership(
            FamilyId.RELATIONAL_TABLE_QUERY, ResultAuthority.COMPUTATION,
            owned_mechanisms=(
                "relational_table_query.row_predicate_filter",
                "relational_table_query.column_projection",
                "relational_table_query.stable_sort_by_key",
                "relational_table_query.bounded_limit",
                "relational_table_query.aggregate_accumulate",
            ),
        ),
    ),
    # W2B ĐANG DỞ: engine + validator + hợp đồng đã xong và có oracle chứng
    # minh, NHƯNG module frontend (mirror validator + renderer) CHƯA có. Giữ ở
    # mức REGISTERED — KHÔNG mở cho LLM — vì cross-lock FE đòi mỗi target
    # AI-reachable phải có module render thật; route tới target không vẽ được
    # là trả cho học sinh một màn hình hỏng. Lật sang AI_REACHABLE_PUBLIC ngay
    # khi renderer xong.
    # W4B-3D — nay CÓ mẫu offline công khai (Thư viện học sinh), nên
    # `library_discoverable` là khai ĐÚNG SỰ THẬT, không phải nâng hạng.
    reachability=_R_FULL,
    curriculum_anchor="T11 CĐ CSDL (bảng, truy vấn cơ bản)",
    known_gaps=(
        "JOIN nhiều bảng · truy vấn lồng · thêm/sửa/xoá dữ liệu · SQL tự do · "
        "GROUP BY nhiều nhóm · kết nối CSDL thật — ngoài phạm vi v1",
        "phần tích luỹ (đếm/tổng/cực trị) TRÙNG cơ chế với single_pass_scan; "
        "cái mới ở đây là KHUNG QUAN HỆ (lược đồ, kiểu cột, vị từ trên bản ghi, "
        "phép chiếu, sắp xếp ổn định)",
    ),
    # W2B-PATCH: LUẬT VALIDATE đổi (chuẩn hoá marker ô trống, cột khai
    # `nullable`, đòi đủ tầng pipeline) nên version HỢP ĐỒNG lên 1.1. Version
    # trên dây (`specVersion` trong config) GIỮ "table-1.0" vì thay đổi chỉ
    # THÊM trường tuỳ chọn — mọi config cũ đã lưu trong lịch sử vẫn hợp lệ
    # (bất biến #17: mở lại từ lịch sử không được vỡ).
    config_contract_version="table-1.1",
)


# ── network.protocol_encapsulation (M10-AI-ROUTE) ─────────────
# Engine tất định 9 bước (frontend encap-model.ts) sở hữu TOÀN BỘ mô hình:
# 4 tầng TCP/IP cố định, PDU, delta thêm/gỡ, timeline, kết quả. LLM chỉ điền
# nhãn ngữ cảnh — bề mặt v1 nhỏ đúng bằng validateEncapConfig phía frontend.

# ── algorithm.scan (M12) — quét dãy MỘT LƯỢT, cấu hình khai báo ──
# Enum DẪN XUẤT từ scan_engine (một nguồn — anti-pattern #1: enum viết tay từng
# làm Gemini không thể phát giá trị mới). Interpreter frontend (core/scan.ts)
# sở hữu vòng lặp/điểm dừng/kết quả; LLM chỉ điền cấu hình + dãy số của đề.

_SCAN_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "scan_version": {"type": "STRING", "enum": [SCAN_VERSION]},
        "array": {"type": "ARRAY", "items": {"type": "NUMBER"}},
        "labels": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        "seed": {
            "type": "OBJECT",
            "properties": {
                "from": {"type": "STRING", "enum": ["first_element", "constant"]},
                "varName": {"type": "STRING"},
                "value": {"type": "NUMBER", "nullable": True},
                "trackIndexVar": {"type": "STRING", "nullable": True},
            },
            "required": ["from", "varName"],
        },
        "compare": {
            "type": "OBJECT",
            "properties": {
                "kind": {"type": "STRING", "enum": ["to_accumulator", "to_constant"]},
                "op": {"type": "STRING", "enum": list(SCAN_OPS)},
                "value": {"type": "NUMBER", "nullable": True},
            },
            "required": ["kind", "op"],
        },
        "update": {
            "type": "OBJECT",
            "properties": {"kind": {"type": "STRING", "enum": list(SCAN_UPDATES)}},
            "required": ["kind"],
        },
        "marking": {"type": "STRING", "enum": list(SCAN_MARKINGS)},
        "stop": {"type": "STRING", "enum": list(SCAN_STOPS)},
    },
    "required": ["scan_version", "array", "seed", "compare", "update", "marking", "stop"],
}

_SCAN_CONTRACT = f"""HỢP ĐỒNG CONFIG (algorithm.scan — quét dãy MỘT LƯỢT, scan_version "{SCAN_VERSION}"):
Bạn chỉ CẤU HÌNH việc quét; interpreter tất định sở hữu vòng lặp, thứ tự duyệt, điểm dừng và kết quả.
- array: dãy số CỦA ĐỀ, đúng thứ tự (không bịa). labels: nhãn từng phần tử nếu đề nêu (cùng độ dài).
- seed (biến tích lũy): {{"from": "first_element", "varName": ..., "trackIndexVar": ...}} khi giá trị khởi đầu là phần tử đầu (kiểu tìm lớn/nhỏ nhất); {{"from": "constant", "value": c, "varName": ...}} khi khởi từ hằng (đếm/tổng: 0; so ngưỡng: giá trị ngưỡng).
- compare (mỗi phần tử được so thế nào): to_accumulator (so với biến đang giữ, vd a[i] > max) hoặc to_constant (so với hằng của đề). op thuộc {"/".join(SCAN_OPS)}.
- update khi so sánh TRÚNG: replace_with_current (giữ phần tử mới) / add_current (cộng dồn) / increment (đếm) / none (không đổi biến — kiểu tìm kiếm).
- marking: running_winner (theo dõi phần tử "đang dẫn đầu") / match_highlight (tô phần tử thỏa).
- stop: end_of_array (duyệt hết dãy) / first_match (DỪNG NGAY lần trúng đầu tiên — đề kiểu "tìm phần tử ĐẦU TIÊN ...").
- varName ngắn, tiếng Việt không dấu, đặt theo đề (nguong, dem, tong, max...).
- Ràng buộc: marking running_winner và compare to_accumulator đều đòi update replace_with_current.
- TUYỆT ĐỐI KHÔNG sinh steps/timeline/kết quả/vị trí tìm thấy — interpreter tự tính khi chạy.
Ví dụ (đề "tìm số ĐẦU TIÊN nhỏ hơn 50 trong dãy"): seed {{"from": "constant", "value": 50, "varName": "nguong"}}; compare {{"kind": "to_constant", "op": "<", "value": 50}}; update {{"kind": "none"}}; marking "match_highlight"; stop "first_match"."""

CATALOG["algorithm.scan"] = SimSpec(
    simulation_id="algorithm.scan",
    domain="algorithm",
    visual_modes=("2d",),
    description=(
        "quét dãy số MỘT LƯỢT theo cấu hình khai báo — CHỈ cho biến thể single-pass mà "
        "các bài chuyên biệt không khớp, điển hình: tìm phần tử ĐẦU TIÊN thỏa BẤT đẳng thức "
        "(lớn hơn/nhỏ hơn ngưỡng — tìm kiếm tuần tự chỉ so BẰNG) hoặc đánh dấu-rồi-dừng-sớm. "
        "KHÔNG dùng khi đề khớp bài chuyên biệt sẵn có (tìm max/min, đếm/tổng theo điều kiện "
        "duyệt hết dãy, tìm giá trị bằng x, sắp xếp); KHÔNG dùng cho vòng lặp trên biến tự do "
        "không có dãy số (unsupported)"
    ),
    config_schema=_SCAN_SCHEMA,
    contract=_SCAN_CONTRACT,
    validate=validate_scan_config,
    make_title=lambda config, analysis: "Quét dãy một lượt",
    # algorithm.scan = catch-all TRONG-family (M15 W2 Task 12): owned là TOÀN BỘ
    # không gian cơ chế single_pass_scan — dẫn xuất từ FAMILY_MECHANISMS (một
    # nguồn), không hand-written, vì scan CHÍNH LÀ toàn bộ family space.
    family_memberships=(
        FamilyMembership(
            FamilyId.SINGLE_PASS_SCAN, ResultAuthority.COMPUTATION,
            owned_mechanisms=FAMILY_MECHANISMS[FamilyId.SINGLE_PASS_SCAN],
        ),
    ),
    # scan KHÔNG có sample offline (discovery A) → không library_discoverable
    reachability=(ReachabilityLevel.REGISTERED, ReachabilityLevel.AI_REACHABLE_PUBLIC),
    curriculum_anchor="T10 CĐ5 · T11CS B17",
    # M17-RC1 §C — BACKLOG NĂNG LỰC (user duyệt, KHÔNG triển khai trong RC1):
    # `single_pass_scan.multi_accumulator`. Đề "tìm CẢ max lẫn min trong một
    # lượt" cần MỘT lượt quét mang NHIỀU biến tích luỹ; ScanSpec hiện chỉ mang
    # một. Hệ quả đo được (RC1-C, case rc1c-scan-max-and-min): đề như vậy hiện
    # trả ok cho MỘT nửa và bỏ im lặng nửa còn lại — gate §D không bắt được vì
    # `single_pass_scan.*` không nằm trong analyze_exposed_values() và max/min
    # dùng CHUNG cơ chế `track_extreme` (taxonomy không phân biệt được chiều).
    known_gaps=(
        "một lượt quét nhiều biến tích luỹ (vd tìm cả max lẫn min) — "
        "single_pass_scan.multi_accumulator, BACKLOG",
    ),
    config_contract_version="scan-1.0",
)


# ── algorithm.bounded_control_flow (M17 W2C) — luồng điều khiển hữu hạn ──
#
# Cấu trúc PHẲNG + tham chiếu id (đúng tiền lệ `logic.boolean_dag`): structured
# output của Gemini KHÔNG biểu diễn được schema đệ quy, nên câu lệnh lồng nhau
# diễn đạt bằng danh sách id, không bằng object lồng object.
# Mọi enum DẪN XUẤT từ `simulation/program_spec.py` (anti-pattern #1).

_PG_OPERAND = {
    "type": "OBJECT",
    "properties": {
        "kind": {"type": "STRING", "enum": list(_PG_OPERAND_KINDS)},
        "int_value": {"type": "INTEGER", "nullable": True},
        "bool_value": {"type": "BOOLEAN", "nullable": True},
        "name": {"type": "STRING", "nullable": True},
    },
    "required": ["kind"],
}

# ValueExpr — PHI ĐỆ QUY: hai toán hạng, một toán tử. Sâu hơn thì dùng câu lệnh
# trung gian (giữ ngữ pháp đóng, structured output sinh được).
_PG_VALUE = {
    "type": "OBJECT",
    "properties": {
        "left": _PG_OPERAND,
        "op": {"type": "STRING", "enum": list(_PG_ARITH), "nullable": True},
        "right": {**_PG_OPERAND, "nullable": True},
    },
    "required": ["left"],
}

_PG_ATOM = {
    "type": "OBJECT",
    "properties": {
        "left": _PG_VALUE,
        "op": {"type": "STRING", "enum": list(_PG_COMPARE), "nullable": True},
        "right": {**_PG_VALUE, "nullable": True},
        "negated": {"type": "BOOLEAN", "nullable": True},
    },
    "required": ["left"],
}

_PG_CONDITION = {
    "type": "OBJECT",
    "properties": {
        "op": {"type": "STRING", "enum": list(_PG_LOGIC), "nullable": True},
        "atoms": {"type": "ARRAY", "items": _PG_ATOM},
    },
    "required": ["atoms"],
}

_PROGRAM_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "program_version": {"type": "STRING", "nullable": True},
        "variables": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "type": {"type": "STRING", "enum": list(_PG_VALUE_TYPES)},
                    "int_value": {"type": "INTEGER", "nullable": True},
                    "bool_value": {"type": "BOOLEAN", "nullable": True},
                },
                "required": ["name", "type"],
            },
        },
        "statements": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "kind": {"type": "STRING", "enum": _pg_statement_kinds()},
                    "target": {"type": "STRING", "nullable": True},
                    "value": {**_PG_VALUE, "nullable": True},
                    "condition": {**_PG_CONDITION, "nullable": True},
                    "then_body": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
                    "else_body": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
                    "body": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
                    "max_iterations": {"type": "INTEGER", "nullable": True},
                },
                "required": ["id", "kind"],
            },
        },
        "main": {"type": "ARRAY", "items": {"type": "STRING"}},
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": ["variables", "statements", "main"],
}

_PROGRAM_CONTRACT = f"""HỢP ĐỒNG CONFIG (algorithm.bounded_control_flow — CHẠY TỪNG BƯỚC MỘT ĐOẠN CHƯƠNG TRÌNH):
- program_version: "{_PG_SPEC_VERSION}".
- variables: 1–{_PG_LIMITS['max_variables']} biến {{name, type, int_value?, bool_value?}}. type ∈ {list(_PG_VALUE_TYPES)}.
  · Đề CÓ cho giá trị ban đầu → điền int_value (trong {_PG_INT_MIN}..{_PG_INT_MAX}) cho biến số nguyên, hoặc bool_value cho biến đúng/sai.
  · Đề KHÔNG nói biến đó ban đầu bằng mấy (vd biến kết quả `y` trong "nếu x>0 thì y=1 ngược lại y=-1") → khai type và ĐỂ TRỐNG CẢ HAI giá trị. TUYỆT ĐỐI KHÔNG bịa 0/false thay đề.
  · KHÔNG tự đổi kiểu: 1 KHÔNG phải true, "5" KHÔNG phải 5.
- statements: bảng PHẲNG {{id, kind, ...}}. kind ∈ {_pg_statement_kinds()}. Biểu thức viết TRỰC TIẾP tại chỗ (KHÔNG có bảng expressions, KHÔNG tự đặt id biểu thức):
  · Toán hạng: {{kind:"int", int_value}} | {{kind:"bool", bool_value}} | {{kind:"var", name}}
  · Biểu thức giá trị: {{left: toán hạng, op: một trong {list(_PG_ARITH)} (bỏ trống nếu chỉ có một toán hạng), right: toán hạng}}
  · assign → target (tên biến) + value (biểu thức giá trị)
  · output → value (biểu thức giá trị)
  · if → condition + then_body (≥1 id câu lệnh) + else_body (có thể rỗng)
  · while → condition + body (≥1) + max_iterations (1..{_PG_LIMITS['max_while_iterations']}) — BẮT BUỘC
  · condition = {{op: "and"|"or" (bỏ trống nếu chỉ một vế), atoms: [vế…]}}; mỗi vế = {{left: biểu thức giá trị, op: một trong {list(_PG_COMPARE)} (bỏ trống nếu vế đã là đúng/sai), right: biểu thức giá trị, negated: true nếu phủ định}}. Tối đa {_PG_LIMITS['max_condition_atoms']} vế, KHÔNG lồng nhóm trong nhóm.
- Biểu thức nhiều tầng (vd y = x*2 + 1) → TÁCH thành câu lệnh trung gian: một câu tính x*2, một câu cộng 1.
- main: danh sách id câu lệnh mức ngoài cùng THEO THỨ TỰ CHẠY. Mỗi câu lệnh thuộc ĐÚNG MỘT khối.
- Giới hạn: ≤ {_PG_LIMITS['max_statement_nodes']} câu lệnh, lồng ≤ {_PG_LIMITS['max_nesting_depth']} tầng.
- Biến chỉ được ĐỌC khi chắc chắn đã có giá trị (được gán ở CẢ HAI nhánh if/else, hoặc có giá trị ban đầu).
- KHÔNG hỗ trợ (đề cần thì trả unsupported): hàm, đệ quy, danh sách/mảng, chuỗi, số thực, nhập từ bàn phím, đọc/ghi tệp, break/continue, try/except, import, lớp/đối tượng.
- TUYỆT ĐỐI KHÔNG sinh: môi trường biến sau từng bước, kết quả điều kiện, số lượt lặp thực tế, giá trị hiển thị, kết quả cuối, trace hay timeline — engine tất định tự chạy."""

CATALOG["algorithm.bounded_control_flow"] = SimSpec(
    simulation_id="algorithm.bounded_control_flow",
    domain="algorithm",
    visual_modes=("2d",),
    description=(
        "chạy TỪNG BƯỚC một đoạn chương trình HỮU HẠN do đề cho sẵn — engine "
        "thực hiện lần lượt các câu lệnh gán, rẽ nhánh if/else và vòng lặp while "
        "có biên, cho thấy câu lệnh đang chạy, biểu thức được tính, điều kiện "
        "đúng hay sai, nhánh nào được chọn, biến đổi giá trị ra sao qua từng "
        "lượt. Dùng khi đề CHO SẴN đoạn chương trình/thuật toán bằng lời có biến "
        "ban đầu + câu lệnh cụ thể và hỏi 'chạy từng bước', 'giá trị cuối cùng "
        "là bao nhiêu', 'lặp mấy lần', 'nhánh nào chạy'. KHÔNG dùng cho: bài có "
        "DÃY SỐ cho sẵn cần duyệt (→ các bài quét/sắp xếp/tìm kiếm chuyên biệt), "
        "hàm/thủ tục, đệ quy, danh sách/mảng/chuỗi, số thực, nhập xuất dữ liệu, "
        "hay yêu cầu chạy mã Python tự do"
    ),
    config_schema=_PROGRAM_SCHEMA,
    contract=_PROGRAM_CONTRACT,
    validate=validate_program_config,
    make_title=lambda config, analysis: "Chạy từng bước đoạn chương trình",
    family_memberships=(
        FamilyMembership(
            FamilyId.BOUNDED_CONTROL_FLOW, ResultAuthority.COMPUTATION,
            owned_mechanisms=FAMILY_MECHANISMS[FamilyId.BOUNDED_CONTROL_FLOW],
        ),
    ),
    # W4B-3D — nay CÓ mẫu offline công khai (Thư viện học sinh), nên
    # `library_discoverable` là khai ĐÚNG SỰ THẬT, không phải nâng hạng.
    reachability=_R_FULL,
    curriculum_anchor="T10 B16–B19 (cấu trúc rẽ nhánh, lặp) · T11CS CĐ",
    known_gaps=(
        "hàm/thủ tục và đệ quy — ngoài phạm vi luồng điều khiển hữu hạn",
        "danh sách/mảng, chuỗi, số thực, nhập xuất — chưa có trong ngữ pháp v1",
    ),
    config_contract_version="program-2.0",
)



# ── binary.character_encoding (M17 W3) — ký tự → mã → nhị phân ──
#
# Schema NHỎ NHẤT dự án từng có: một chuỗi + một enum. Engine tất định nằm ở
# FRONTEND (`domains/binary/encoding-module.tsx`) và dùng LẠI `toBase()` của
# `base_conversion`; backend chỉ kiểm định. Vì thế config KHÔNG mang mã, không
# mang nhị phân, không mang bảng kết quả.

_CHAR_ENC_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "spec_version": {"type": "STRING", "nullable": True},
        "text": {"type": "STRING"},
        "encoding": {"type": "STRING", "enum": _ce_encodings()},
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": ["text", "encoding"],
}

_CHAR_ENC_CONTRACT = f"""HỢP ĐỒNG CONFIG (binary.character_encoding — MÃ HOÁ KÝ TỰ):
- spec_version: "{_CE_SPEC_VERSION}".
- text: chuỗi ký tự LẤY ĐÚNG TỪ ĐỀ, 1–{_CE_MAX_CP} ký tự. Chép nguyên văn, KHÔNG bỏ dấu tiếng Việt, KHÔNG đổi hoa/thường, KHÔNG thay ký tự lạ bằng "?" hay ký tự gần giống.
  · Đề hỏi mã của CHỮ SỐ thì text là ký tự đó trong dấu nháy, ví dụ đề "mã ASCII của chữ số 7" → text = "7" (KHÔNG phải số 7).
- encoding: {_ce_encodings()}.
  · "ascii" — chỉ dùng khi mọi ký tự có mã 0..{_CE_ASCII_MAX} (chữ Latin không dấu, chữ số, dấu câu).
  · "unicode_codepoint" — dùng cho ký tự tiếng Việt có dấu và các ký tự Unicode khác, mã tối đa {_CE_BMP_MAX}.
  · Đề KHÔNG nói rõ bảng mã nào thì ĐỪNG TỰ CHỌN — trả unsupported để hệ hỏi lại.
- KHÔNG hỗ trợ (đề cần thì trả unsupported): emoji và ký tự ngoài vùng cơ bản (mã > {_CE_BMP_MAX}), dãy byte UTF-8/UTF-16, Base64, nén, mã hoá bảo mật, mã hoá ảnh/âm thanh, phông chữ.
- TUYỆT ĐỐI KHÔNG sinh: code point, giá trị thập phân, dãy bit, bảng kết quả, số bước hay trace — engine tất định tự tra mã và tự đổi sang nhị phân."""

CATALOG["binary.character_encoding"] = SimSpec(
    simulation_id="binary.character_encoding",
    domain="binary",
    visual_modes=("2d",),
    description=(
        "mã hoá ký tự — mô phỏng TỪNG BƯỚC việc tra mã của mỗi ký tự trong một "
        "chuỗi ngắn rồi đổi mã đó sang nhị phân: ký tự → mã ký tự (ASCII hoặc "
        "Unicode code point) → giá trị thập phân → dãy bit. Dùng khi đề hỏi 'mã "
        "ASCII của chữ A là bao nhiêu', 'mã Unicode của ký tự ế', 'biểu diễn nhị "
        "phân của ký tự', hay vì sao máy tính lưu chữ bằng số. KHÔNG dùng khi đề "
        "cho sẵn MỘT CON SỐ và chỉ hỏi đổi số đó sang nhị phân (→ đổi số thập "
        "phân sang nhị phân) hoặc sang hệ khác (→ đổi cơ số). KHÔNG hỗ trợ emoji, "
        "dãy byte UTF-8, Base64, nén hay mã hoá bảo mật"
    ),
    config_schema=_CHAR_ENC_SCHEMA,
    contract=_CHAR_ENC_CONTRACT,
    validate=validate_character_encoding_config,
    make_title=lambda config, analysis: "Mã hoá ký tự",
    family_memberships=(
        FamilyMembership(
            FamilyId.POSITIONAL_REPRESENTATION, ResultAuthority.COMPUTATION,
            # Sở hữu ĐÚNG cơ chế mới; việc đổi mã số sang nhị phân vẫn thuộc
            # `non_binary_base` của base_conversion — KHÔNG giành quyền sở hữu.
            owned_mechanisms=("positional_representation.character_code_mapping",),
        ),
    ),
    # Chưa có đề mẫu công khai trong Thư viện ⇒ KHÔNG khai library_discoverable
    # (đúng tiền lệ algorithm.scan / bounded_control_flow: không quảng bá một
    # affordance chưa tồn tại). Thêm mẫu là việc nhỏ, để checkpoint sau.
    # W4B-3D — nay CÓ mẫu offline công khai (Thư viện học sinh), nên
    # `library_discoverable` là khai ĐÚNG SỰ THẬT, không phải nâng hạng.
    reachability=_R_FULL,
    curriculum_anchor="T10 B3 · T10 B6 (mã hoá văn bản)",
    known_gaps=(
        "emoji và ký tự ngoài BMP (mã > 65535) — ngoài phạm vi v1",
        "dãy byte UTF-8/UTF-16, Base64, nén, mã hoá bảo mật — ngoài phạm vi",
    ),
    config_contract_version="charenc-1.0",
)


_ENCAP_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "payloadLabel": {"type": "STRING", "nullable": True},
        "appProtocol": {"type": "STRING", "nullable": True},
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": [],
}

_ENCAP_CONTRACT = """HỢP ĐỒNG CONFIG (network.protocol_encapsulation):
- payloadLabel: nhãn NGẮN (≤80 ký tự) cho dữ liệu ứng dụng lấy từ đề (vd "Thư gửi bạn Lan"); đề không nêu → bỏ trống, hệ thống dùng mặc định "Dữ liệu ứng dụng".
- appProtocol: tên giao thức ứng dụng CHỈ ĐỂ HIỂN THỊ NGỮ CẢNH (vd "HTTP", "Email") nếu đề nêu rõ; không nêu → null. KHÔNG mô hình hoá hành vi giao thức.
- notes: ghi chú ngắn (tùy chọn).
- Mô hình v1 CỐ ĐỊNH do engine tất định sở hữu: 4 tầng TCP/IP (Ứng dụng → Giao vận → Internet → Truy cập mạng), 9 bước đóng gói → truyền → tháo gói.
- KHÔNG sinh layers, pdu, headers, steps, timeline, trạng thái hay kết quả — engine tự dựng toàn bộ diễn biến từ config."""

CATALOG["network.protocol_encapsulation"] = SimSpec(
    simulation_id="network.protocol_encapsulation",
    domain="network",
    # 3D THẬT và có NGHĨA MIỀN: `encap-ui3d.layerDepth()` đặt trục Z = chỉ số
    # tầng giao thức, nên "đi xuống các tầng" là chuyển động thật, không ẩn dụ.
    visual_modes=("2d", "3d"),
    description="đóng gói dữ liệu qua các tầng giao thức TCP/IP — dữ liệu từ tầng ứng dụng được THÊM DẦN thông tin giao thức (TCP, IP, thông tin liên kết) khi đi xuống từng tầng ở máy gửi, truyền đi, rồi được GỠ DẦN (tháo gói) ở máy nhận. Dùng khi cơ chế ẩn là BIẾN ĐỔI PDU qua từng TẦNG. Bài hỏi ĐƯỜNG ĐI của gói tin qua các thiết bị (router/switch/ISP) → network.packet_routing. KHÔNG hỗ trợ chi tiết bắt tay TCP ba bước, số sequence/ACK, phân mảnh, retransmission, congestion control, DNS — các đề đó vượt năng lực v1, trả unsupported",
    config_schema=_ENCAP_SCHEMA,
    contract=_ENCAP_CONTRACT,
    validate=validate_encapsulation_config,
    make_title=lambda config, analysis: "Đóng gói dữ liệu qua các tầng TCP/IP",
    family_memberships=(
        FamilyMembership(
            FamilyId.LAYERED_PDU_TRANSFORM, ResultAuthority.COMPUTATION,
            owned_mechanisms=("layered_pdu_transform.encapsulate_decapsulate_4layer",),
        ),
    ),
    reachability=_R_FULL,
    curriculum_anchor="T12 B4 · 12CS B22–24",
    known_gaps=("bắt tay TCP ba bước", "phân mảnh", "retransmission", "congestion", "DNS"),
    config_contract_version="encap-cfg-1",
)


# ── Domain generic (M6) — engine rule-based, AI compose bằng DSL ──────

_GENERIC_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "dsl_version": {"type": "STRING"},
        "title": {"type": "STRING"},
        "objects": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    # Enum DẪN XUẤT từ manifest (M7.13A) — schema viết tay từng
                    # drift (thiếu drag) khiến Gemini KHÔNG THỂ phát primitive mới.
                    "type": {"type": "STRING", "enum": sorted(object_types())},
                    "x": {"type": "NUMBER", "nullable": True},
                    "y": {"type": "NUMBER", "nullable": True},
                    "label": {"type": "STRING", "nullable": True},
                    "value": {"type": "NUMBER", "nullable": True},
                    "node_type": {"type": "STRING", "nullable": True},
                    "from": {"type": "STRING", "nullable": True},
                    "to": {"type": "STRING", "nullable": True},
                    # M8-PRE (S2): chiều của edge (luồng dữ liệu / request→response).
                    # Thiếu field này trong schema = Gemini KHÔNG THỂ phát ra dù prompt
                    # cho phép — đúng anti-pattern #1 đã từng gây bug với `drag`.
                    "directed": {"type": "BOOLEAN", "nullable": True},
                    # M7.12: nội dung chữ + lồng nhau
                    "text": {"type": "STRING", "nullable": True},
                    "parent": {"type": "STRING", "nullable": True},
                },
                "required": ["id", "type"],
            },
        },
        "rules": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "type": {"type": "STRING", "enum": sorted(rule_types())},
                    "op": {"type": "STRING", "enum": sorted(bool_ops()), "nullable": True},
                    "inputs": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "weights": {"type": "ARRAY", "items": {"type": "NUMBER"}, "nullable": True},
                    "target": {"type": "STRING"},
                },
                "required": ["type", "target", "inputs"],
            },
        },
        "interactions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "type": {"type": "STRING", "enum": sorted(interaction_types())},
                    "target": {"type": "STRING"},
                    "label": {"type": "STRING", "nullable": True},
                    # M7.13A: constraints của drag (bounds/axis/snap)
                    "constraints": {
                        "type": "OBJECT",
                        "nullable": True,
                        "properties": {
                            "bounds": {
                                "type": "OBJECT",
                                "nullable": True,
                                "properties": {
                                    "min_x": {"type": "NUMBER", "nullable": True},
                                    "max_x": {"type": "NUMBER", "nullable": True},
                                    "min_y": {"type": "NUMBER", "nullable": True},
                                    "max_y": {"type": "NUMBER", "nullable": True},
                                },
                            },
                            "axis": {"type": "STRING", "enum": ["x", "y"], "nullable": True},
                            "snap": {"type": "NUMBER", "nullable": True},
                        },
                    },
                },
                "required": ["type", "target"],
            },
        },
        "processes": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "type": {"type": "STRING", "enum": sorted(process_types())},
                    # move_along_path
                    "entity": {"type": "STRING", "nullable": True},
                    "path": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
                    # reveal_sequence
                    "steps": {
                        "type": "ARRAY",
                        "nullable": True,
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "objects": {"type": "ARRAY", "items": {"type": "STRING"}},
                                "narration": {"type": "STRING", "nullable": True},
                            },
                            "required": ["objects"],
                        },
                    },
                },
                "required": ["type"],
            },
        },
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": ["title", "objects"],
}

# Contract DẪN XUẤT từ manifest (M7 §2) — không viết tay, chống drift với validator
_GENERIC_CONTRACT = manifest_contract_text()

CATALOG["generic.rule_scene"] = SimSpec(
    simulation_id="generic.rule_scene",
    domain="generic",
    visual_modes=("2d",),
    description="mô phỏng TỔNG QUÁT do AI tự dựng từ đối tượng/quy tắc/tương tác — dùng khi bài KHÔNG khớp mô phỏng chuyên biệt nào ở trên nhưng vẫn mô tả được bằng các nút, công tắc, đèn, ô giá trị, quy tắc logic/tổng có trọng số, hoặc thực thể di chuyển theo đường",
    config_schema=_GENERIC_SCHEMA,
    contract=_GENERIC_CONTRACT,
    validate=validate_generic_config,
    make_title=lambda config, analysis: config.get("title") or "Mô phỏng tổng quát",
    # §C1: HAI membership, result_authority khác nhau (computation + representation)
    family_memberships=(
        FamilyMembership(
            FamilyId.BOOLEAN_COMPOSITION, ResultAuthority.COMPUTATION, family_spec_version="dsl-1",
            owned_mechanisms=("boolean_composition.composed_rule_dag",),
        ),
        FamilyMembership(
            FamilyId.STRUCTURAL_PROGRESSIVE_REPRESENTATION, ResultAuthority.REPRESENTATION,
            family_spec_version="dsl-1",
            # W5 (Task 15): owned DẪN XUẤT trực tiếp từ manifest process_types()
            # (một nguồn — không viết tay); sorted() để tất định (thứ tự không
            # mang ý nghĩa — mọi lock chỉ so SET, xem FAMILY_MECHANISMS ở
            # mechanisms.py và test_membership_owned_mechanisms_canonical_...).
            owned_mechanisms=tuple(
                f"structural_progressive_representation.{p}" for p in sorted(process_types())
            ),
        ),
    ),
    reachability=_R_FULL,
    curriculum_anchor="T11 B10 · T12CS B29 · T12 CĐ4",
    config_contract_version="dsl-1.0",
)


def llm_choices() -> list[str]:
    """M14 §C2 — tập LỰA CHỌN classifier (DẪN XUẤT, không cờ tay).

    = {sim_id runtime target KHÔNG có membership thuộc family có selector}
    ∪ {selector_token của mỗi FamilySelector}.
    Hệ quả: bubble_sort/insertion_sort (thuộc comparison_sort có selector) bị
    ẩn khỏi menu; token comparison_sort thay chỗ. generic/logic/scan giữ nguyên.
    """
    out: list[str] = []
    for sim_id, spec in CATALOG.items():
        if any(m.family_id.value in SELECTOR_FAMILY_IDS for m in spec.family_memberships):
            continue
        out.append(sim_id)
    for sel in FAMILY_SELECTORS.values():
        out.append(sel.selector_token)
    return out


def capability_descriptors() -> dict:
    """M14 §C4 — descriptor SINH-TỪ-NGUỒN (CATALOG + FAMILY_SELECTORS).

    Xuất ra `frontend/src/simulations/capability-descriptors.json` (artifact
    TEST/GENERATED). Production FE KHÔNG import file này (điểm 6) — nó chỉ để
    test cross-lock BE↔FE. Ordering theo CATALOG (ổn định cho sync-lock).
    """
    def _member(m) -> dict:
        return {
            "family_id": m.family_id.value,
            "result_authority": m.result_authority.value,
            "variant_id": m.variant_id,
            "family_spec_version": m.family_spec_version,
            "mechanism_id": m.mechanism_id,
            "owned_mechanisms": list(m.owned_mechanisms),
        }

    targets = {
        sim_id: {
            "domain": spec.domain,
            "executor_id": spec.executor_id,
            # M17 P0 — khả năng trình bày ĐI RA descriptor để frontend cross-lock
            # được (capability-descriptors.test.ts). Không có bảng viết tay thứ hai.
            "visual_modes": list(spec.visual_modes),
            "reachability": [r.value for r in spec.reachability],
            "curriculum_anchor": spec.curriculum_anchor,
            "known_gaps": list(spec.known_gaps),
            "family_memberships": [_member(m) for m in spec.family_memberships],
            "config_contract_version": spec.config_contract_version,
            # M17-Lite W0 — authenticity contract (app/simulation/authenticity.py)
            "authenticity": authenticity_descriptor(sim_id),
        }
        for sim_id, spec in CATALOG.items()
    }
    selectors = {
        fid: {
            "selector_token": sel.selector_token,
            "family_spec_version": sel.family_spec_version,
            "owned_mechanisms": list(sel.owned_mechanisms),
            "variants": [
                {
                    "variant_id": v.variant_id,
                    "concrete_simulation_id": v.concrete_simulation_id,
                    "mechanism_id": v.mechanism_id,
                }
                for v in sel.variants
            ],
        }
        for fid, sel in FAMILY_SELECTORS.items()
    }
    return {
        "runtime_targets": targets,
        "family_selectors": selectors,
        "llm_choices": llm_choices(),
        # W4B-2Z — MIỀN GIÁ TRỊ có ràng buộc của các domain "đổi tham số".
        # Không phải metadata trình bày: đây là HỢP ĐỒNG mà cả hai tầng validate
        # phải nói giống nhau, nên nó phải đo được chứ không chỉ mô tả được.
        "bounded_domains": {"web.style_model": web_style_domain()},
    }


def catalog_text() -> str:
    """Danh mục dạng chữ đưa vào prompt của stage classify — DẪN XUẤT từ
    llm_choices (§C2): concrete llm-facing + selector token. Hai sort concrete bị
    ẩn (nằm sau selector), token comparison_sort thay chỗ."""
    lines = ["DANH MỤC MÔ PHỎNG ĐANG HỖ TRỢ:"]
    for choice in llm_choices():
        spec = CATALOG.get(choice)
        if spec is not None:
            lines.append(f"- {choice}: {spec.description}")
        else:
            sel = selector_for_token(choice)
            if sel is not None:
                lines.append(f"- {choice}: {sel.description}")
    return "\n".join(lines)

# ── web.style_model (W4B-2Z) — MÔ HÌNH THUỘC TÍNH TRÌNH BÀY CÓ RÀNG BUỘC ──
#
# Vì sao đây là một CƠ CHẾ, không phải một đề bài mới: học sinh không xem một
# tiến trình chạy mà ĐỔI THAM SỐ rồi đọc hệ quả ngay — cùng khuôn khám phá với
# logic.and_gate, khác miền. Trước wave này, đề HTML/CSS bị đẩy vào
# generic.rule_scene và dựng thành "Bước 1/3 → hiện khung", tức BỊA một trục
# thời gian mà cơ chế không hề có.
#
# ĐÂY KHÔNG PHẢI code_experiment (vẫn DEFERRED, ARCHITECTURE_MAP §10):
# spec KHÔNG chứa mã nguồn HTML/CSS. Nó mô tả một MÔ HÌNH có tập thuộc tính
# ĐÓNG; trình duyệt chỉ vẽ lại state, không diễn giải code tuỳ ý.
_WEB_STYLE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    # M20 — DI TRÚ DỞ DANG, và đây là lỗi nặng nhất tìm được trong W12.
    # W4B-3F đổi hợp đồng web từ `content` (một khối chữ) sang `heading` +
    # `paragraph` — validator ĐÃ chuyển, schema đưa cho LLM thì KHÔNG. Hệ quả:
    # LLM được bảo hãy điền `content`, validator không nhận `content` và
    # fail-closed với khoá lạ ⇒ **mọi spec web do AI sinh đều bị từ chối**, tức
    # `web.style_model` không tới được qua đường sinh của chính hệ thống.
    # Lỗi `headingSize`/`headingColor` sửa trước đó chỉ là triệu chứng bề mặt
    # của cùng một lần di trú này.
    # Giới hạn độ dài lấy đúng `_WEB_CONTENT_MAX` / `_WEB_PARAGRAPH_MAX`.
    # Khoá chống tái phát: `tests/test_web_contract_sync.py`.
    "required": ["heading"],
    "properties": {
        "heading": {"type": "string", "minLength": 1, "maxLength": 120},
        "paragraph": {"type": "string", "maxLength": 240},
        "style": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "backgroundColor": {"type": "string"},
                "color": {"type": "string"},
                "fontSize": {"type": "integer", "minimum": 12, "maximum": 48},
                # M20 — HAI TRƯỜNG NÀY TỪNG BỊ BỎ QUÊN, và đó là lỗi chí mạng
                # của luận điểm đề tài chứ không phải thiếu sót nhỏ.
                # `_WEB_NUMERIC` chấp nhận chúng, UI có ô điều khiển cho chúng,
                # comment bump 26→27 gọi thẳng chúng là "bề mặt LLM điền" — mà
                # schema đưa cho LLM lại KHÔNG có. Hệ quả: mọi bài CSS do AI
                # sinh KHÔNG BAO GIỜ cho học sinh đổi kiểu chữ TIÊU ĐỀ, tức mất
                # đúng bài học phân cấp (`.trang h1` khác `.trang p`) mà bản mẫu
                # dựng ra để dạy. Bản mẫu làm được, bài AI sinh thì không.
                # Khoá chống tái phát: `tests/test_web_contract_sync.py`.
                "headingColor": {"type": "string"},
                "headingSize": {"type": "integer", "minimum": 16, "maximum": 56},
                "padding": {"type": "integer", "minimum": 0, "maximum": 48},
                "borderRadius": {"type": "integer", "minimum": 0, "maximum": 40},
            },
        },
        "notes": {"type": ["string", "null"]},
    },
}

_WEB_STYLE_CONTRACT = """web.style_model — mô hình thuộc tính trình bày CÓ RÀNG BUỘC.
- content: một dòng chữ hiển thị trong khối (<= 120 ký tự).
- style: CHỈ các khoá backgroundColor, color, fontSize, padding, borderRadius.
- Màu phải nằm trong bảng đã khai; số phải trong biên đã khai.
- KHÔNG sinh mã HTML/CSS/JS, KHÔNG chuỗi style tự do, KHÔNG thuộc tính ngoài danh sách.
- Đây là mô phỏng KHÁM PHÁ: không có bước, không timeline."""

CATALOG["web.style_model"] = SimSpec(
    simulation_id="web.style_model",
    domain="web",
    visual_modes=("2d",),
    description="thay đổi thuộc tính trình bày (CSS) của một khối và quan sát kết quả đổi ngay: màu nền, màu chữ, cỡ chữ, đệm trong, bo góc. Dùng khi đề hỏi VỀ HIỆU QUẢ của thuộc tính CSS. KHÔNG dùng cho dựng cấu trúc trang từng bước (đó là generic.rule_scene)",
    config_schema=_WEB_STYLE_SCHEMA,
    contract=_WEB_STYLE_CONTRACT,
    validate=validate_web_style_config,
    make_title=lambda config, analysis: "Thay đổi kiểu hiển thị (CSS)",
    family_memberships=(
        FamilyMembership(
            FamilyId.WEB_PRESENTATION, ResultAuthority.REPRESENTATION,
            owned_mechanisms=("web_presentation.bounded_style_properties",),
        ),
    ),
    reachability=_R_FULL,
    curriculum_anchor="T12 CĐ4 · HTML/CSS",
    config_contract_version="web-style-1",
)
