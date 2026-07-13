"""Representation Plan (M7.11) — bước trung gian TẤT ĐỊNH giữa analysis và
SimulationSpec.

analysis (semantic requirements) → representation plan → SimulationSpec.

Plan suy TỪ manifest role taxonomy (không LLM, không hard-code môn học): gom
vai trò ngữ nghĩa đề cần, ánh xạ sang năng lực DSL, xác định scene_mode và
các vai trò KHÔNG biểu diễn được (capability gap).
"""

from __future__ import annotations

from app.simulation.dsl.manifest import (
    SEMANTIC_ROLES,
    all_coverable_roles,
    primitives_for_role,
    temporal_process_types,
)

_ROLE_FIELDS = [
    "entity_roles",
    "relation_roles",
    "process_roles",
    "interaction_needs",
    "visual_needs",
    "temporal_needs",
]


def required_roles(analysis: dict) -> set[str]:
    """Hợp mọi vai trò ngữ nghĩa từ các trường requirement của analysis."""
    roles: set[str] = set()
    for field in _ROLE_FIELDS:
        for r in analysis.get(field) or []:
            if r in SEMANTIC_ROLES:
                roles.add(r)
    return roles


def _scene_mode(analysis: dict, roles: set[str]) -> str:
    """Chế độ cảnh tất định (M7.13A):
    - exploratory: không diễn biến theo thời gian (cảnh tĩnh / chỉ tương tác).
    - progressive: sự HÌNH THÀNH cảnh là nội dung chính (dựng từng bước).
    - hybrid: diễn biến + tương tác, HOẶC cảnh cho sẵn (prebuilt) làm nền
      cho một quá trình chạy trên đó (vd topology có sẵn + gói tin di chuyển).
    """
    has_temporal = "temporal" in roles or analysis.get("scene_construction") == "step_by_step"
    has_interactive = "interactive" in roles
    prebuilt = analysis.get("scene_construction") == "prebuilt"
    if has_temporal and (has_interactive or prebuilt):
        return "hybrid"
    if has_temporal:
        return "progressive"
    return "exploratory"


def scene_mode_guidance(scene_mode: str) -> str:
    """Chỉ dẫn scene_mode chèn vào prompt simulate (M7.13A) — plan là nguồn
    quyết định, LLM không tự chọn chế độ cảnh."""
    if scene_mode == "exploratory":
        return (
            "CHẾ ĐỘ CẢNH (scene_mode) đã xác định: exploratory — cảnh TĨNH/khám phá. "
            "Mọi object hiện từ đầu; KHÔNG thêm bất kỳ process nào (không reveal_sequence, "
            "không move_along_path). Interactions (toggle/drag) vẫn dùng khi bài cần thao tác."
        )
    if scene_mode == "progressive":
        return (
            "CHẾ ĐỘ CẢNH (scene_mode) đã xác định: progressive — sự hình thành cảnh là nội "
            "dung chính. PHẢI có ít nhất một process diễn biến (vd reveal_sequence hé lộ dần)."
        )
    return (
        "CHẾ ĐỘ CẢNH (scene_mode) đã xác định: hybrid — cảnh nền + diễn biến + tương tác. "
        "PHẢI có ít nhất một process diễn biến; thêm interactions (toggle/drag) khi bài "
        "cần học sinh thao tác trực tiếp."
    )


def check_scene_consistency(scene_mode: str, spec: dict) -> str | None:
    """Kiểm tất định spec ↔ scene_mode (M7.13A §9) — trả lỗi tiếng Việt cho
    LLM retry, None nếu nhất quán.

    KHÔNG hard-code tên process: "diễn biến" = mọi process thuộc họ temporal
    (suy từ role taxonomy trong manifest), gồm cả process tương lai.
    Chỉ check điều chắc chắn để tránh over-reject: exploratory cấm temporal
    process; progressive/hybrid cần ít nhất một temporal process; interactions
    tự do ở mọi mode (toggle trong cảnh tĩnh là hợp lệ — vd cổng AND).
    """
    temporal = temporal_process_types()
    has_temporal_proc = any(p.get("type") in temporal for p in spec.get("processes", []))
    if scene_mode == "exploratory" and has_temporal_proc:
        return (
            "Cảnh này là TĨNH/khám phá (exploratory) — mọi object hiện từ đầu, "
            "KHÔNG được thêm process diễn biến theo thời gian "
            f"({', '.join(sorted(temporal))}). Hãy bỏ processes."
        )
    if scene_mode in ("progressive", "hybrid") and not has_temporal_proc:
        return (
            f"Cảnh này cần diễn biến ({scene_mode}) — spec phải có ít nhất một "
            f"process diễn biến theo thời gian ({', '.join(sorted(temporal))})."
        )
    return None


def build_representation_plan(analysis: dict) -> dict:
    """Trả representation plan tất định (dùng trước khi sinh SimulationSpec)."""
    roles = required_roles(analysis)
    coverable = all_coverable_roles()
    unsupported = sorted(roles - coverable)
    caps = sorted({p for r in roles for p in primitives_for_role(r)})
    return {
        "semantic_roles": sorted(roles),
        "required_dsl_capabilities": caps,
        "scene_mode": _scene_mode(analysis, roles),
        "mapping_intent": {r: primitives_for_role(r) for r in sorted(roles)},
        "unsupported_capabilities": unsupported,
    }
