# -*- coding: utf-8 -*-
"""M17-RC1 §C2 — HỢP ĐỒNG DỮ KIỆN ĐẦU VÀO (máy-đọc, một nguồn).

Lớp rủi ro đã xảy ra THẬT (live W2A run 1): đề "duyệt cây theo thứ tự trước"
KHÔNG cho cấu trúc cây, LLM **bịa nguyên một cây** rồi hệ trả `ok` → mô phỏng
một bài mà người học chưa hề nêu. RC1-C đo được: 18/19 target chưa có phòng thủ
tương đương — `structure_gate` chỉ chạy cho `tree.traversal`.

Hợp đồng này KHÔNG tạo gate riêng cho từng target. Mỗi target khai **loại dữ
kiện** nó cần; một cổng DÙNG CHUNG (`sufficiency_gate`) đọc khai báo rồi gọi
normalizer theo **loại đầu vào** (không theo target). Vì vậy KHÔNG có và không
được có `sort_sufficiency_gate.py`, `graph_sufficiency_gate.py`…

`required_grounded_inputs` RỖNG = NOT_APPLICABLE, và phải kèm `not_applicable_
reason` DẪN XUẤT TỪ HỢP ĐỒNG — không được dùng để che fixture thiếu.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.simulation.error_codes import ErrorCode


class InputKind(str, Enum):
    """Nhóm dữ kiện DÙNG CHUNG giữa các family (đóng). Normalizer đăng ký theo
    NHÓM này, nên thêm target mới thường KHÔNG cần code mới."""

    FINITE_SEQUENCE = "finite_sequence"
    NUMERIC_VALUE = "numeric_value"
    GRAPH_STRUCTURE = "graph_structure"
    TREE_STRUCTURE = "tree_structure"
    BOOLEAN_EXPRESSION = "boolean_expression"
    CONVERSION_PARAMETERS = "conversion_parameters"
    PACKET_OR_LAYER_DESCRIPTION = "packet_or_layer_description"
    REPRESENTATION_OBJECTS = "representation_objects"
    TABLE_SCHEMA_AND_ROWS = "table_schema_and_rows"   # W2B
    # W2C — chương trình hữu hạn: KHÔNG nhóm nào sẵn có biểu diễn được "biến ban
    # đầu + câu lệnh/điều kiện" (không phải dãy, không phải số lẻ, không phải
    # cây/đồ thị/bảng/mạch logic), nên đây là nhóm dữ kiện mới THẬT SỰ cần.
    PROGRAM_STATEMENTS = "program_statements"          # W2C
    # W3 — mã hoá ký tự cần HAI thứ đi kèm nhau: chuỗi cần mã hoá VÀ bảng mã.
    # Không nhóm nào sẵn có biểu diễn được (CONVERSION_PARAMETERS là cơ số,
    # NUMERIC_VALUE là một con số) nên đây là nhóm dữ kiện mới THẬT SỰ cần.
    TEXT_AND_ENCODING = "text_and_encoding"            # W3


APPLICABLE = "APPLICABLE"
NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class InputRequirements:
    """Hợp đồng dữ kiện của MỘT target."""

    required_grounded_inputs: tuple[InputKind, ...] = ()
    optional_inputs: tuple[InputKind, ...] = ()
    # Bằng chứng trong analyze được CHẤP NHẬN là "đề có cho" (máy-đọc; tài liệu
    # cho normalizer, không phải logic).
    accepted_evidence_types: tuple[str, ...] = ()
    # Mặc định do hệ sinh KHÔNG thoả required input — trừ khi target công khai
    # cho phép VÀ người học chủ động chọn đề mẫu (offline sample).
    generated_defaults_allowed: bool = False
    insufficiency_error_code: ErrorCode = ErrorCode.STRUCTURE_INSUFFICIENT
    learner_prompt_template: str = ""
    not_applicable_reason: str = ""

    @property
    def applicability(self) -> str:
        return APPLICABLE if self.required_grounded_inputs else NOT_APPLICABLE


_SEQ_EVIDENCE = ("data.values", "data.labels", "data.description_numeric_tokens")
_NODE_EVIDENCE = ("relations.named_pair", "objects.named_nodes")

_SEQUENCE = InputRequirements(
    required_grounded_inputs=(InputKind.FINITE_SEQUENCE,),
    accepted_evidence_types=_SEQ_EVIDENCE,
    insufficiency_error_code=ErrorCode.INPUT_INSUFFICIENT,
    learner_prompt_template=(
        "Đề chưa cho dãy số cụ thể để mô phỏng. Em hãy nêu rõ dãy (ví dụ: 12, 7, "
        "25, 9) rồi thử lại — hệ không tự nghĩ ra số liệu thay em."
    ),
)

INPUT_REQUIREMENTS: dict[str, InputRequirements] = {
    # ── single_pass_scan + interval_elimination + comparison_sort: cần DÃY ──
    "algorithm.find_max": _SEQUENCE,
    "algorithm.find_min": _SEQUENCE,
    "algorithm.sum_if": _SEQUENCE,
    "algorithm.count_if": _SEQUENCE,
    "algorithm.linear_search": _SEQUENCE,
    "algorithm.scan": _SEQUENCE,
    "algorithm.binary_search": _SEQUENCE,
    "algorithm.bubble_sort": _SEQUENCE,
    "algorithm.insertion_sort": _SEQUENCE,
    "algorithm.selection_sort": _SEQUENCE,
    # ── positional_representation: cần SỐ (và cơ số khi đổi tổng quát) ──
    "binary.decimal_to_binary": InputRequirements(
        required_grounded_inputs=(InputKind.NUMERIC_VALUE,),
        accepted_evidence_types=("data.values", "data.description_numeric_tokens"),
        insufficiency_error_code=ErrorCode.INPUT_INSUFFICIENT,
        learner_prompt_template=(
            "Đề chưa cho số cụ thể cần đổi sang nhị phân. Em hãy nêu số (ví dụ: "
            "25) rồi thử lại."
        ),
    ),
    "binary.base_conversion": InputRequirements(
        required_grounded_inputs=(InputKind.CONVERSION_PARAMETERS,),
        optional_inputs=(InputKind.NUMERIC_VALUE,),
        accepted_evidence_types=("data.values", "data.description_numeric_tokens"),
        insufficiency_error_code=ErrorCode.INPUT_INSUFFICIENT,
        learner_prompt_template=(
            "Đề chưa cho đủ dữ kiện để đổi cơ số (số cần đổi và hệ nguồn/hệ "
            "đích). Em hãy nêu rõ, ví dụ: đổi 25 từ hệ thập phân sang hệ nhị phân."
        ),
    ),
    # ── tree / graph: cần CẤU TRÚC có tên nút ──
    # ── W2C: cần CHƯƠNG TRÌNH cụ thể (biến ban đầu + câu lệnh) ──
    "algorithm.bounded_control_flow": InputRequirements(
        required_grounded_inputs=(InputKind.PROGRAM_STATEMENTS,),
        accepted_evidence_types=("objects.named_variables", "data.initial_values"),
        insufficiency_error_code=ErrorCode.INPUT_INSUFFICIENT,
        learner_prompt_template=(
            "Đề chưa cho đoạn chương trình cụ thể để chạy thử. Em hãy nêu rõ: "
            "giá trị ban đầu của các biến (ví dụ x = 1), điều kiện (ví dụ x < 5), "
            "và các câu lệnh trong thân (ví dụ x = x + 1) — hệ không tự nghĩ ra "
            "chương trình thay em."
        ),
    ),
    # ── W4B-2Z: cần ĐỐI TƯỢNG được trình bày (khối/thẻ và chữ trong nó) ──
    # Dùng lại REPRESENTATION_OBJECTS chứ KHÔNG đẻ InputKind mới: "một thẻ giới
    # thiệu có tiêu đề X" đúng là đối tượng cần biểu diễn — không có gì mới về
    # NHÓM dữ kiện, chỉ mới về cơ chế. Đề trống ⇒ chặn, vì hệ tự nghĩ ra nội
    # dung thì học sinh đang nhìn trang của MÁY, không phải trang của đề.
    "web.style_model": InputRequirements(
        required_grounded_inputs=(InputKind.REPRESENTATION_OBJECTS,),
        accepted_evidence_types=("objects.named_entities", "objects.quoted_characters"),
        insufficiency_error_code=ErrorCode.INPUT_INSUFFICIENT,
        learner_prompt_template=(
            "Đề chưa cho biết cần trình bày nội dung gì. Em hãy nêu rõ khối chữ "
            "cần đổi kiểu hiển thị (ví dụ: một thẻ có dòng chữ \"Chào các bạn\") "
            "rồi thử lại — hệ không tự nghĩ ra nội dung trang thay em."
        ),
    ),
    # ── W3: cần CHUỖI cần mã hoá + BẢNG MÃ ──
    "binary.character_encoding": InputRequirements(
        required_grounded_inputs=(InputKind.TEXT_AND_ENCODING,),
        accepted_evidence_types=("objects.quoted_characters", "constraints.encoding_name"),
        insufficiency_error_code=ErrorCode.INPUT_INSUFFICIENT,
        learner_prompt_template=(
            "Đề chưa nói rõ cần mã hoá ký tự nào và theo bảng mã nào. Em hãy nêu "
            "cụ thể ký tự hoặc chuỗi (ví dụ: chữ A) và chọn bảng mã — ASCII hay "
            "Unicode code point — rồi thử lại; hệ không tự chọn thay em."
        ),
    ),
    "tree.traversal": InputRequirements(
        required_grounded_inputs=(InputKind.TREE_STRUCTURE,),
        accepted_evidence_types=_NODE_EVIDENCE,
        insufficiency_error_code=ErrorCode.STRUCTURE_INSUFFICIENT,
        learner_prompt_template=(
            "Đề yêu cầu duyệt cây nhưng chưa cho cấu trúc cây cụ thể (các nút có "
            "tên và quan hệ con trái/con phải giữa chúng). Hãy mô tả rõ cây (ví "
            "dụ: gốc A, A có con trái B và con phải C…) rồi thử lại — hệ không tự "
            "dựng cây thay bạn."
        ),
    ),
    "network.graph_traversal": InputRequirements(
        required_grounded_inputs=(InputKind.GRAPH_STRUCTURE,),
        accepted_evidence_types=_NODE_EVIDENCE,
        insufficiency_error_code=ErrorCode.STRUCTURE_INSUFFICIENT,
        learner_prompt_template=(
            "Đề yêu cầu duyệt đồ thị nhưng chưa cho các đỉnh và cạnh cụ thể. Hãy "
            "nêu rõ đồ thị (ví dụ: các đỉnh A, B, C; A nối B, A nối C) rồi thử lại."
        ),
    ),
    "network.packet_routing": InputRequirements(
        required_grounded_inputs=(InputKind.GRAPH_STRUCTURE,),
        accepted_evidence_types=_NODE_EVIDENCE,
        insufficiency_error_code=ErrorCode.STRUCTURE_INSUFFICIENT,
        learner_prompt_template=(
            "Đề yêu cầu định tuyến gói tin nhưng chưa cho sơ đồ mạng cụ thể (các "
            "nút và đường nối, nơi gửi và nơi nhận). Hãy nêu rõ rồi thử lại."
        ),
    ),
    # ── boolean_composition: mạch phải do ĐỀ nêu ──
    "logic.boolean_dag": InputRequirements(
        required_grounded_inputs=(InputKind.BOOLEAN_EXPRESSION,),
        accepted_evidence_types=("objects.named_inputs_and_gates", "relations.wiring"),
        insufficiency_error_code=ErrorCode.INPUT_INSUFFICIENT,
        learner_prompt_template=(
            "Đề chưa mô tả mạch logic cụ thể (các đầu vào và các cổng nối với "
            "nhau thế nào). Em hãy nêu rõ rồi thử lại."
        ),
    ),
    "generic.rule_scene": InputRequirements(
        required_grounded_inputs=(InputKind.REPRESENTATION_OBJECTS,),
        accepted_evidence_types=("objects.named",),
        insufficiency_error_code=ErrorCode.INPUT_INSUFFICIENT,
        learner_prompt_template=(
            "Đề chưa nêu đối tượng cụ thể nào để dựng cảnh mô phỏng. Em hãy mô tả "
            "các đối tượng rồi thử lại."
        ),
    ),
    # ── W2B: bảng phải do ĐỀ cho, tuyệt đối không tự dựng bảng mẫu ──
    "database.relational_table_query": InputRequirements(
        required_grounded_inputs=(InputKind.TABLE_SCHEMA_AND_ROWS,),
        accepted_evidence_types=("data.values", "data.labels", "objects.named_columns"),
        insufficiency_error_code=ErrorCode.INPUT_INSUFFICIENT,
        learner_prompt_template=(
            "Đề chưa cho bảng dữ liệu cụ thể (tên các cột và các dòng dữ liệu). "
            "Em hãy chép rõ bảng vào đề — ví dụ: cột Tên, Điểm, Tổ; rồi từng dòng "
            "An 8.5 A, Bình 6.0 B… — hệ không tự tạo bảng thay em."
        ),
    ),
    # ── NOT_APPLICABLE: lý do DẪN XUẤT TỪ HỢP ĐỒNG, không phải né tránh ──
    "logic.and_gate": InputRequirements(
        optional_inputs=(InputKind.BOOLEAN_EXPRESSION,),
        generated_defaults_allowed=True,
        not_applicable_reason=(
            "Module KHÁM PHÁ (exploratory, không timeline): hai đầu vào là TRẠNG "
            "THÁI BAN ĐẦU mà người học tự bật/tắt để quan sát bảng chân trị, "
            "không phải dữ kiện đề bắt buộc cung cấp. Đặt mặc định false/false "
            "không bịa dữ liệu của ai."
        ),
    ),
    "network.protocol_encapsulation": InputRequirements(
        optional_inputs=(InputKind.PACKET_OR_LAYER_DESCRIPTION,),
        generated_defaults_allowed=True,
        not_applicable_reason=(
            "config_schema.required RỖNG: toàn bộ 9 bước PDU và các tầng do "
            "ENGINE tất định sở hữu; nhãn payload chỉ là nhãn hiển thị tuỳ chọn. "
            "Không có dữ kiện nào của đề để bịa."
        ),
    ),
}


def requirements_for(target_id: str) -> InputRequirements | None:
    return INPUT_REQUIREMENTS.get(target_id)


def applicability_of(target_id: str) -> tuple[str, str]:
    """(APPLICABLE|NOT_APPLICABLE, lý do). Target chưa khai hợp đồng → coi là
    APPLICABLE-nhưng-thiếu-hợp-đồng: KHÔNG được lặng lẽ bỏ qua."""
    req = INPUT_REQUIREMENTS.get(target_id)
    if req is None:
        return APPLICABLE, "chưa khai hợp đồng dữ kiện (phải bổ sung, không mặc định bỏ qua)"
    if req.applicability == NOT_APPLICABLE:
        return NOT_APPLICABLE, req.not_applicable_reason
    return APPLICABLE, ""


__all__ = [
    "APPLICABLE",
    "INPUT_REQUIREMENTS",
    "NOT_APPLICABLE",
    "InputKind",
    "InputRequirements",
    "applicability_of",
    "requirements_for",
]
