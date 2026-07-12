# -*- coding: utf-8 -*-
"""Test M7.11 — semantic role taxonomy, Representation Plan tất định, và
semantic compatibility validator (phát hiện mismatch TRƯỚC render).

Không hard-code theo tên môn học: mọi quyết định suy từ manifest role taxonomy.
"""

from app.simulation.dsl.manifest import (
    SEMANTIC_ROLES,
    all_coverable_roles,
    known_gap_roles,
    primitives_for_role,
    roles_of_primitive,
)
from app.simulation.representation import build_representation_plan, required_roles
from app.simulation.semantic import (
    check_semantic_compatibility,
    roles_covered_by_spec,
)


# ── Role taxonomy ─────────────────────────────────────────────

def test_moi_role_deu_coverable_sau_m712():
    """M7.12: DSL v1.1 thêm container/group (structural) + heading/paragraph/text
    (textual) → CẢ 8 role đều có primitive cover, không còn gap role hiện tại."""
    assert all_coverable_roles() == set(SEMANTIC_ROLES)
    assert known_gap_roles() == set()
    assert roles_of_primitive("container") == {"structural"}
    assert roles_of_primitive("heading") == {"textual"}


def test_roles_of_primitive():
    assert roles_of_primitive("switch") == {"interactive", "logical", "numeric"}
    assert roles_of_primitive("node") == {"relational"}
    assert roles_of_primitive("label") == {"textual"}
    assert roles_of_primitive("khong_ton_tai") == set()


def test_primitives_for_role_sorted():
    assert primitives_for_role("relational") == ["edge", "node"]
    assert primitives_for_role("temporal") == ["move_along_path", "reveal_sequence"]
    assert primitives_for_role("structural") == ["container", "group"]  # M7.12
    assert primitives_for_role("textual") == ["heading", "label", "paragraph", "text"]


# ── required_roles từ analysis ────────────────────────────────

def test_required_roles_gom_moi_truong():
    analysis = {
        "entity_roles": ["logical", "numeric"],
        "relation_roles": ["relational"],
        "temporal_needs": ["temporal"],
        "visual_needs": ["not_a_role"],  # tag lạ bị lọc bỏ
    }
    assert required_roles(analysis) == {"logical", "numeric", "relational", "temporal"}


def test_required_roles_analysis_cu_khong_co_truong_moi():
    """Backward-compat: analysis M1–M7.10 thiếu 6 trường → không vai trò nào →
    không gap, không reject (pipeline cũ chạy nguyên vẹn)."""
    analysis = {"objects": ["x"], "goal": "y"}
    assert required_roles(analysis) == set()


# ── build_representation_plan ─────────────────────────────────

def test_plan_rong_la_exploratory():
    plan = build_representation_plan({"objects": ["x"]})
    assert plan["semantic_roles"] == []
    assert plan["unsupported_capabilities"] == []
    assert plan["scene_mode"] == "exploratory"


def test_plan_temporal_la_progressive():
    plan = build_representation_plan({"temporal_needs": ["temporal"]})
    assert plan["scene_mode"] == "progressive"


def test_plan_temporal_va_interactive_la_hybrid():
    plan = build_representation_plan(
        {"temporal_needs": ["temporal"], "interaction_needs": ["interactive"]}
    )
    assert plan["scene_mode"] == "hybrid"


def test_plan_scene_construction_step_by_step_la_progressive():
    plan = build_representation_plan({"scene_construction": "step_by_step"})
    assert plan["scene_mode"] == "progressive"


def test_plan_mapping_intent_va_caps():
    plan = build_representation_plan({"relation_roles": ["relational"]})
    assert plan["mapping_intent"]["relational"] == ["edge", "node"]
    assert "node" in plan["required_dsl_capabilities"]
    assert "edge" in plan["required_dsl_capabilities"]


def test_plan_structural_gio_coverable_sau_m712():
    """M7.12: đề cần bố cục (structural) + chữ (textual) giờ COVER được →
    plan KHÔNG còn unsupported; mapping_intent chỉ ra container/group + heading…"""
    plan = build_representation_plan({"visual_needs": ["structural", "textual"]})
    assert plan["unsupported_capabilities"] == []
    assert plan["mapping_intent"]["structural"] == ["container", "group"]
    assert "container" in plan["required_dsl_capabilities"]


# ── roles_covered_by_spec ─────────────────────────────────────

def _switch_lamp_spec():
    return {
        "objects": [
            {"id": "a", "type": "switch"},
            {"id": "y", "type": "lamp"},
        ],
        "rules": [{"type": "boolean", "op": "and", "inputs": ["a"], "target": "y"}],
        "processes": [],
    }


def _graph_spec():
    return {
        "objects": [
            {"id": "n1", "type": "node"},
            {"id": "n2", "type": "node"},
            {"id": "e", "type": "edge", "from": "n1", "to": "n2"},
        ],
        "rules": [],
        "processes": [],
    }


def _web_spec():
    """M7.12: spec cấu trúc/nội dung ĐÚNG cho web — container + heading + paragraph."""
    return {
        "objects": [
            {"id": "page", "type": "container", "text": "Trang giới thiệu"},
            {"id": "h", "type": "heading", "text": "Xin chào", "parent": "page"},
            {"id": "p", "type": "paragraph", "text": "Đây là đoạn văn.", "parent": "page"},
        ],
        "rules": [],
        "processes": [],
    }


def test_roles_covered_switch_lamp():
    assert roles_covered_by_spec(_switch_lamp_spec()) == {
        "interactive",
        "logical",
        "numeric",
    }


def test_roles_covered_graph():
    assert roles_covered_by_spec(_graph_spec()) == {"relational"}


# ── check_semantic_compatibility ──────────────────────────────

def test_compat_ok_khi_spec_du_vai_tro():
    res = check_semantic_compatibility({"logical", "numeric"}, _switch_lamp_spec())
    assert res["ok"]
    assert res["kind"] == "ok"


def test_roles_covered_web_spec():
    """M7.12: spec container/heading/paragraph cover {structural, textual}."""
    assert roles_covered_by_spec(_web_spec()) == {"structural", "textual"}


def test_compat_web_spec_dung_thi_pass():
    """M7.12 (ví dụ then chốt): đề cần {structural, textual} + spec ĐÚNG
    (container+heading+paragraph) → PASS, không còn capability_gap."""
    res = check_semantic_compatibility({"structural", "textual"}, _web_spec())
    assert res["ok"], res
    assert res["kind"] == "ok"


def test_compat_web_spec_sai_thi_mismatch():
    """M7.11×M7.12: đề cần {structural, textual} NHƯNG spec sinh ra switch/lamp
    (giao rỗng) → vẫn REJECT, nhưng giờ là 'mismatch' (RETRY được vì DSL ĐÃ có
    primitive đúng) chứ không phải capability_gap. KHÔNG ép web thành công tắc/đèn."""
    res = check_semantic_compatibility({"structural", "textual"}, _switch_lamp_spec())
    assert not res["ok"]
    assert res["kind"] == "mismatch"


def test_compat_gap_chi_cho_role_chua_co_primitive():
    """Nhánh capability_gap VẪN sống: role tương lai chưa có primitive nào cover
    → gap (phòng khi thêm role mới vào taxonomy mà chưa có primitive)."""
    res = check_semantic_compatibility({"__role_tuong_lai__"}, _web_spec())
    assert not res["ok"]
    assert res["kind"] == "capability_gap"
    assert "__role_tuong_lai__" in res["missing"]


def test_compat_mismatch_khi_lech_han_ho():
    """Đề cần quan hệ nút-cạnh (relational — cover được) nhưng spec chỉ có
    switch/lamp (giao rỗng với đề) → mismatch (retry bảo simulate dùng
    node/edge), KHÔNG phải gap."""
    res = check_semantic_compatibility({"relational"}, _switch_lamp_spec())
    assert not res["ok"]
    assert res["kind"] == "mismatch"
    assert res["missing"] == ["relational"]


def _graph_reveal_spec():
    """Spec dựng hình từng bước: node/edge (relational) + reveal (temporal).
    Cover {relational, temporal} — KHÔNG cover numeric."""
    s = _graph_spec()
    s["processes"] = [{"type": "reveal_sequence", "steps": [
        {"objects": ["n1", "n2"]}, {"objects": ["e"]},
    ]}]
    return s


def test_compat_vai_tro_phu_khong_gay_duong_tinh_gia():
    """CHỐNG DƯƠNG TÍNH GIẢ (bug live tam giác): analyze gắn thêm vai trò PHỤ
    'numeric' (toạ độ là số) nhưng spec node/edge/reveal chỉ cover
    {relational, temporal}. Vì spec CHIA SẺ vai trò cốt lõi (relational,
    temporal) với đề → KHÔNG được coi là mismatch."""
    required = {"numeric", "relational", "temporal"}
    res = check_semantic_compatibility(required, _graph_reveal_spec())
    assert res["ok"], res
    assert res["kind"] == "ok"


def test_compat_khong_yeu_cau_thi_luon_ok():
    """required rỗng (analysis cũ) → luôn ok (backward-compat)."""
    res = check_semantic_compatibility(set(), _switch_lamp_spec())
    assert res["ok"]
