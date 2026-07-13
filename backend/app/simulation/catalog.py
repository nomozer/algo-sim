"""Bản chiếu registry phía backend — danh mục simulation_id hệ đang hỗ trợ.

Mỗi entry khai báo: domain, visual_mode, mô tả (cho stage classify),
schema structured-output + hợp đồng chữ (cho stage simulate), validator
(chốt chặn server-side) và cách đặt tiêu đề. Thêm domain mới (logic.*,
binary.*, network.*...) = thêm entry + validator riêng — KHÔNG sửa pipeline.
"""

from __future__ import annotations

from functools import partial
from typing import Callable

from app.simulation.dsl.validator import validate_generic_config
from app.simulation.dsl.manifest import (
    bool_ops,
    interaction_types,
    manifest_contract_text,
    object_types,
    process_types,
    rule_types,
)
from app.validation.simulation import (
    ALGORITHM_IDS,
    ALGORITHM_NAMES_VI,
    validate_algorithm_config,
    validate_binary_config,
    validate_logic_config,
    validate_network_config,
)

# ── Domain algorithm ──────────────────────────────────────────

_ALGO_DESCRIPTIONS = {
    "find_max": "tìm giá trị lớn nhất trong một dãy số",
    "find_min": "tìm giá trị nhỏ nhất trong một dãy số",
    "sum_if": "tính tổng các phần tử của dãy thỏa một điều kiện so sánh",
    "count_if": "đếm số phần tử của dãy thỏa một điều kiện so sánh",
    "linear_search": "tìm một giá trị trong dãy bằng cách duyệt tuần tự từ đầu",
    "binary_search": "tìm một giá trị trong dãy ĐÃ SẮP THỨ TỰ bằng cách chia đôi vùng xét (đề thường gợi ý 'tìm nhanh', 'dãy đã sắp xếp')",
    "bubble_sort": "sắp xếp dãy bằng cách so sánh và đổi chỗ các cặp kề nhau (nổi bọt)",
    "insertion_sort": "sắp xếp dãy bằng cách rút từng phần tử chèn vào phần đã sắp (chèn)",
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
    """Đặc tả một mô phỏng trong danh mục backend."""

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
    ) -> None:
        self.simulation_id = simulation_id
        self.domain = domain
        self.visual_mode = visual_mode
        self.description = description
        self.config_schema = config_schema
        self.contract = contract
        self.validate = validate
        self.make_title = make_title


CATALOG: dict[str, SimSpec] = {}

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
    description="định tuyến gói tin trên MỘT MẠNG CHO SẴN đầy đủ — mô phỏng gói tin đi từng chặng từ máy nguồn qua các router tới máy đích. CHỈ dùng khi topology có sẵn ngay; KHÔNG dựng mạng từng bước (không tạo từng thiết bị/liên kết dần)",
    config_schema=_NETWORK_SCHEMA,
    contract=_NETWORK_CONTRACT,
    validate=validate_network_config,
    make_title=lambda config, analysis: "Đường đi của gói tin trong mạng",
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
                    "weight": {"type": "NUMBER", "nullable": True},
                    "node_type": {"type": "STRING", "nullable": True},
                    "from": {"type": "STRING", "nullable": True},
                    "to": {"type": "STRING", "nullable": True},
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
)


def catalog_text() -> str:
    """Danh mục dạng chữ đưa vào prompt của stage classify."""
    lines = ["DANH MỤC MÔ PHỎNG ĐANG HỖ TRỢ:"]
    for spec in CATALOG.values():
        lines.append(f"- {spec.simulation_id}: {spec.description}")
    return "\n".join(lines)
