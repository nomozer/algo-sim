"""Content Hygiene Gate (G4).

Kiểm tra tính vệ sinh nội dung trên canvas:
- 0 tiêu đề trùng lặp với envelope title
- 0 nhãn mồ côi hoặc nhãn rỗng vô nghĩa
- 0 nhãn độc lập trùng lặp với thuộc tính label của component
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class HygieneViolation:
    code: str
    object_id: str
    message: str
    details: dict[str, Any]


@dataclass
class HygieneReport:
    ok: bool
    violations: list[HygieneViolation]


def check_content_hygiene(
    objects: list[dict[str, Any]],
    envelope_title: str | None = None,
) -> HygieneReport:
    violations: list[HygieneViolation] = []
    clean_env_title = (envelope_title or "").strip().lower()

    # Thu thập tất cả các nhãn đã có sẵn trong các component
    component_labels: set[str] = set()
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        obj_type = obj.get("type", "")
        lbl = obj.get("label")
        if lbl and isinstance(lbl, str) and obj_type != "label":
            component_labels.add(lbl.strip().lower())

    for obj in objects:
        if not isinstance(obj, dict):
            continue
        obj_id = obj.get("id", "unknown")
        obj_type = obj.get("type", "")
        text = str(obj.get("text") or "").strip()
        label = str(obj.get("label") or "").strip()

        # 1. Redundant canvas heading duplicating outer title
        if obj_type == "heading":
            if clean_env_title and text.lower() == clean_env_title:
                violations.append(
                    HygieneViolation(
                        code="DUPLICATE_CANVAS_HEADING",
                        object_id=obj_id,
                        message=f"Đối tượng heading '{obj_id}' trùng lặp hoàn toàn với tiêu đề ngoài trang: '{text}'.",
                        details={"heading_text": text, "envelope_title": envelope_title},
                    )
                )

        # 2. Empty or whitespace-only label
        if obj_type == "label":
            if not text and not label:
                violations.append(
                    HygieneViolation(
                        code="EMPTY_LABEL",
                        object_id=obj_id,
                        message=f"Đối tượng label '{obj_id}' rỗng hoặc chỉ chứa khoảng trắng.",
                        details={},
                    )
                )
            else:
                lbl_val = (text or label).lower()
                # 3. Redundant standalone label when component already has this label
                if lbl_val in component_labels:
                    violations.append(
                        HygieneViolation(
                            code="REDUNDANT_STANDALONE_LABEL",
                            object_id=obj_id,
                            message=f"Đối tượng label '{obj_id}' có nội dung '{text or label}' bị trùng với thuộc tính label của một component khác.",
                            details={"label_text": text or label},
                        )
                    )

    return HygieneReport(ok=len(violations) == 0, violations=violations)
