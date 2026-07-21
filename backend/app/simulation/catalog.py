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
from app.validation.simulation import (
    ALGORITHM_IDS,
    ALGORITHM_NAMES_VI,
    validate_algorithm_config,
    validate_base_conversion_config,
    validate_binary_config,
    validate_boolean_dag_config,
    validate_encapsulation_config,
    validate_logic_config,
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
        visual_mode: str,
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
        self.visual_mode = visual_mode
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
        "reachability": (
            ReachabilityLevel.REGISTERED,
            ReachabilityLevel.AI_REACHABLE_PUBLIC,
        ),
    },
}

for _aid in ALGORITHM_IDS:
    _sim_id = f"algorithm.{_aid}"
    CATALOG[_sim_id] = SimSpec(
        simulation_id=_sim_id,
        domain="algorithm",
        visual_mode="2d",
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
    visual_mode="2d",
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
    visual_mode="2d",
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
    reachability=(
        ReachabilityLevel.REGISTERED,
        ReachabilityLevel.AI_REACHABLE_PUBLIC,
    ),
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
    visual_mode="2d",
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
    visual_mode="2d",
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
    reachability=(
        ReachabilityLevel.REGISTERED,
        ReachabilityLevel.AI_REACHABLE_PUBLIC,
    ),
    curriculum_anchor="T10 B4",
    config_contract_version="baseconv-1.0",
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
    visual_mode="2d",
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
    visual_mode="2d",
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
    reachability=(
        ReachabilityLevel.REGISTERED,
        ReachabilityLevel.AI_REACHABLE_PUBLIC,
    ),
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
    visual_mode="2d",
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
    reachability=(
        ReachabilityLevel.REGISTERED,
        ReachabilityLevel.AI_REACHABLE_PUBLIC,
    ),
    curriculum_anchor="T11CS B17 · T11 CĐ (cấu trúc dữ liệu cây)",
    known_gaps=(
        "BST/AVL/heap/cây biểu thức/cây n-nhánh — ngoài phạm vi duyệt cây nhị phân",
    ),
    config_contract_version="tree-1.0",
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
    visual_mode="2d",
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
    config_contract_version="scan-1.0",
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
    visual_mode="2d",
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
    visual_mode="2d",
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
