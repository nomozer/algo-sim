"""Semantic Types and Visual Binding Verification IR (G1, G2).

Định nghĩa hệ thống kiểu dữ liệu đại số và xác thực tính toàn vẹn liên kết giữa
trạng thái tất định (Canonical State) và các đối tượng trực quan (Visual Objects).
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from typing import Any


class SemanticType(str, Enum):
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    STRING = "string"
    BRACKET_SYMBOL = "bracket_symbol"
    SEQUENCE = "sequence"
    STACK = "stack"
    QUEUE = "queue"
    GRID = "grid"
    UNKNOWN = "unknown"


@dataclass
class BindingTypeViolation:
    violation_code: str
    object_id: str
    message: str
    details: dict[str, Any]


def is_bracket_char(s: Any) -> bool:
    return isinstance(s, str) and len(s) == 1 and s in "()[]{}<>"


def infer_semantic_type(val: Any) -> SemanticType:
    if isinstance(val, bool):
        return SemanticType.BOOLEAN
    if isinstance(val, int):
        return SemanticType.INTEGER
    if isinstance(val, float):
        return SemanticType.FLOAT
    if is_bracket_char(val):
        return SemanticType.BRACKET_SYMBOL
    if isinstance(val, str):
        return SemanticType.STRING
    if isinstance(val, list):
        if val and all(is_bracket_char(x) for x in val):
            return SemanticType.SEQUENCE
        return SemanticType.SEQUENCE
    return SemanticType.UNKNOWN


def validate_visual_binding_types(
    objects: list[dict[str, Any]],
    state: dict[str, Any],
    expected_bindings: dict[str, str] | None = None,
) -> list[BindingTypeViolation]:
    """Kiểm tra tính nhất quán giữa kiểu dữ liệu của visual object và canonical state.
    
    Quy tắc G1 & G2:
    - Nếu visual object là `array_strip` hoặc liên kết với một `sequence`, dữ liệu phải là sequence.
      Cấm trường hợp sequence bị coerce thành dummy 0.
    - Nếu visual object là `pointer`, target phải trỏ vào một object_id tồn tại.
    - Không cấm giá trị 0 đối với các kiểu số (integer/float).
    """
    violations: list[BindingTypeViolation] = []
    object_ids = {o.get("id") for o in objects if isinstance(o, dict) and o.get("id")}
    bindings = expected_bindings or {}

    for obj in objects:
        if not isinstance(obj, dict):
            continue
        obj_id = obj.get("id", "unknown")
        obj_type = obj.get("type", "")

        # 1. Target Reference Integrity (G2)
        target = obj.get("target") or obj.get("target_id")
        if target and target not in object_ids:
            violations.append(
                BindingTypeViolation(
                    violation_code="ORPHAN_TARGET_REFERENCE",
                    object_id=obj_id,
                    message=f"Đối tượng {obj_id} trỏ đến target không tồn tại: '{target}'.",
                    details={"target": target, "available_ids": list(object_ids)},
                )
            )

        # 2. Sequence Visual Binding Type Consistency (G1)
        if obj_type == "array_strip":
            items = obj.get("items")
            raw_val = obj.get("value")

            # Nếu có liên kết với state
            bound_var = bindings.get(obj_id)
            if bound_var and bound_var in state:
                state_val = state[bound_var]
                if isinstance(state_val, (list, tuple)):
                    if items is None and raw_val == 0:
                        violations.append(
                            BindingTypeViolation(
                                violation_code="TYPE_MISMATCH_COERCION",
                                object_id=obj_id,
                                message=(
                                    f"Visual object '{obj_id}' (array_strip) liên kết với sequence '{bound_var}' "
                                    f"nhưng lại nhận giá trị dummy 0 thay vì danh sách phần tử."
                                ),
                                details={"expected_type": "sequence", "actual_value": raw_val},
                            )
                        )
            else:
                # Nếu không có explicit binding nhưng obj là array_strip và items bị thiếu còn value là 0
                if items is None and raw_val == 0:
                    violations.append(
                        BindingTypeViolation(
                            violation_code="TYPE_MISMATCH_COERCION",
                            object_id=obj_id,
                            message=f"array_strip '{obj_id}' không có items hợp lệ và bị gán value = 0.",
                            details={"expected_type": "sequence", "actual_value": raw_val},
                        )
                    )

        # 3. Stack / Queue Type Consistency
        if obj_type in ("stack_view", "queue_view"):
            items = obj.get("items")
            raw_val = obj.get("value")
            if items is None and raw_val == 0:
                # Stack/Queue có thể rỗng ([]), nhưng không được ép thành số 0
                violations.append(
                    BindingTypeViolation(
                        violation_code="TYPE_MISMATCH_COERCION",
                        object_id=obj_id,
                        message=f"{obj_type} '{obj_id}' bị gán dummy value = 0 thay vì mảng phần tử.",
                        details={"expected_type": "sequence", "actual_value": raw_val},
                    )
                )

    return violations
