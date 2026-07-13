# -*- coding: utf-8 -*-
"""Test pattern store M7.13B — signature/extraction/instantiate/gates/matcher.

Khóa các quy tắc đã duyệt: matching tất định exact (không embedding), safe
deterministic allowlist (op ĐÓNG BĂNG), candidate không auto-reuse,
verified > validated, version lệch → deprecated, reuse không bypass validation.
"""

from app.persistence.db import SessionLocal, SimulationPattern, init_db
from app.simulation.dsl.validator import validate_generic_config
from app.simulation.patterns import (
    DbPatternStore,
    deterministic_fill,
    extract_template,
    instantiate,
    pattern_key_of,
    run_gates,
    spec_signature,
    validate_params,
)

init_db()


def _norm(raw: dict) -> dict:
    cfg, err = validate_generic_config(raw)
    assert err is None, err
    return cfg


WEB_SPEC = _norm({
    "dsl_version": "1.0",
    "title": "Trang giới thiệu",
    "objects": [
        {"id": "page", "type": "container", "text": "Trang giới thiệu"},
        {"id": "h", "type": "heading", "text": "Xin chào", "parent": "page"},
        {"id": "p", "type": "paragraph", "text": "Đây là đoạn văn giới thiệu.", "parent": "page"},
    ],
    "rules": [], "interactions": [], "processes": [],
})

AND_SPEC = _norm({
    "dsl_version": "1.0",
    "title": "Cổng AND",
    "objects": [
        {"id": "a", "type": "switch", "value": 0, "label": "Công tắc A"},
        {"id": "b", "type": "switch", "value": 1, "label": "Công tắc B"},
        {"id": "y", "type": "lamp"},
    ],
    "rules": [{"type": "boolean", "op": "and", "inputs": ["a", "b"], "target": "y"}],
    "interactions": [{"type": "toggle", "target": "a"}, {"type": "toggle", "target": "b"}],
    "processes": [],
})

TRIANGLE = {
    "dsl_version": "1.0",
    "title": "Tam giác",
    "objects": [
        {"id": "A", "type": "node", "x": 20, "y": 70, "label": "A"},
        {"id": "B", "type": "node", "x": 80, "y": 70, "label": "B"},
        {"id": "C", "type": "node", "x": 50, "y": 20, "label": "C"},
        {"id": "AB", "type": "edge", "from": "A", "to": "B"},
        {"id": "AC", "type": "edge", "from": "A", "to": "C"},
        {"id": "BC", "type": "edge", "from": "B", "to": "C"},
    ],
    "rules": [],
    "interactions": [],
    "processes": [{"type": "reveal_sequence", "steps": [
        {"objects": ["A", "B"]}, {"objects": ["AB"]}, {"objects": ["C"]}, {"objects": ["AC", "BC"]},
    ]}],
}
TRIANGLE_STATIC = _norm(TRIANGLE)
TRIANGLE_DRAG = _norm({
    **TRIANGLE,
    "interactions": [{"type": "drag", "target": "A"}, {"type": "drag", "target": "B"}],
})


def _cleanup(keys: list[str]) -> None:
    with SessionLocal() as s:
        for k in keys:
            s.query(SimulationPattern).filter_by(pattern_key=k).delete()
        s.commit()


# ── Signature / identity ──────────────────────────────────────

def test_signature_static_vs_draggable_khac_pattern():
    """Case K: static triangle ≠ draggable triangle — interaction semantics
    khác nhau thì KHÔNG cùng pattern (chữ ký gồm interaction:target-type)."""
    roles_static = {"relational", "temporal"}
    roles_drag = {"relational", "temporal", "interactive"}
    sig1 = spec_signature("progressive", roles_static, TRIANGLE_STATIC)
    sig2 = spec_signature("hybrid", roles_drag, TRIANGLE_DRAG)
    assert pattern_key_of(sig1) != pattern_key_of(sig2)
    assert sig2["interaction_types"] == ["drag:node"]
    assert sig1["interaction_types"] == []


def test_signature_tat_dinh_va_gom_du_truong():
    roles = {"structural", "textual"}
    sig = spec_signature("exploratory", roles, WEB_SPEC)
    assert set(sig) == {
        "scene_mode", "semantic_roles", "object_types", "rule_types",
        "rule_ops", "process_types", "interaction_types",
    }
    assert pattern_key_of(sig) == pattern_key_of(spec_signature("exploratory", roles, WEB_SPEC))
    # op nằm TRONG chữ ký: AND pattern không trùng key với OR pattern
    or_spec = _norm({**AND_SPEC, "rules": [{"type": "boolean", "op": "or", "inputs": ["a", "b"], "target": "y"}]})
    k_and = pattern_key_of(spec_signature("exploratory", {"logical"}, AND_SPEC))
    k_or = pattern_key_of(spec_signature("exploratory", {"logical"}, or_spec))
    assert k_and != k_or


# ── Extraction (safe allowlist) + instantiate ─────────────────

def test_extract_round_trip_va_dong_bang_cau_truc():
    template, schema, params = extract_template(WEB_SPEC)
    # slot đúng allowlist: title + 3 text
    assert set(schema) == {"title", "text_page", "text_h", "text_p"}
    assert instantiate(template, params) == WEB_SPEC  # round-trip
    # instantiate với nội dung MỚI: cấu trúc giữ nguyên, chỉ nội dung đổi
    new = instantiate(template, {**params, "text_h": "Bài học Tin học", "title": "Slide bài giảng"})
    assert new["objects"][1]["text"] == "Bài học Tin học"
    assert new["objects"][1]["parent"] == "page"
    assert WEB_SPEC["objects"][1]["text"] == "Xin chào"  # template/spec gốc không bị sửa


def test_extract_khong_tham_so_hoa_operator():
    """Điều chỉnh đã chốt: KHÔNG auto-generalize op — bool op đóng băng trong
    template, chỉ value/label thành slot."""
    template, schema, _ = extract_template(AND_SPEC)
    assert template["rules"][0]["op"] == "and"  # op là literal, không phải slot
    assert set(schema) == {"title", "label_a", "label_b", "value_a", "value_b"}
    assert schema["value_a"]["kind"] == "bit"


def test_validate_params_chan_gia_tri_rac():
    _, schema, params = extract_template(AND_SPEC)
    assert validate_params(schema, params) is None
    assert validate_params(schema, {**params, "value_a": 5}) is not None  # bit ≠ 5
    assert validate_params(schema, {**params, "label_a": "  "}) is not None
    missing = dict(params)
    missing.pop("title")
    assert validate_params(schema, missing) is not None


def test_deterministic_fill_weights_tu_analysis():
    wsum = _norm({
        "dsl_version": "1.0", "title": "Tổng trọng số",
        "objects": [
            {"id": "b0", "type": "switch", "value": 1},
            {"id": "b1", "type": "switch", "value": 0},
            {"id": "out", "type": "value_box"},
        ],
        "rules": [{"type": "weighted_sum", "inputs": ["b0", "b1"], "weights": [8, 4], "target": "out"}],
        "interactions": [], "processes": [],
    })
    _, schema, _ = extract_template(wsum)
    analysis = {"data": [{"description": "trọng số", "values": [5, 3]}]}
    filled, unresolved = deterministic_fill(schema, analysis)
    assert filled == {"weights_0": [5, 3]}  # mảng số suy thẳng từ analysis
    assert "title" in unresolved and "value_b0" in unresolved  # chuỗi/bit → LLM


# ── 4 cổng ────────────────────────────────────────────────────

def test_run_gates_khong_bypass_validation():
    # structural fail
    cfg, err = run_gates("exploratory", set(), {"title": ""})
    assert cfg is None and "structural" in err
    # scene-mode fail: exploratory mà có reveal
    cfg, err = run_gates("exploratory", set(), dict(TRIANGLE_STATIC))
    assert cfg is None and "scene_mode" in err
    # semantic fail: đề cần relational, spec toàn switch/lamp
    cfg, err = run_gates("exploratory", {"relational"}, dict(AND_SPEC))
    assert cfg is None and "semantic" in err
    # pass đủ 4 cổng
    cfg, err = run_gates("progressive", {"relational", "temporal"}, dict(TRIANGLE_STATIC))
    assert err is None and cfg is not None


# ── DbPatternStore: persist / match / status / version ────────

def test_persist_va_match_exact():
    store = DbPatternStore("test-policy")
    roles = {"structural", "textual"}
    key = store.persist_from_spec("exploratory", roles, WEB_SPEC)
    assert key is not None
    try:
        row = store.find("exploratory", roles)
        assert row is not None and row.pattern_key == key
        assert row.status == "validated"  # self-check pass → validated, KHÔNG verified
        # trùng pattern_key → tăng usage, không nhân bản
        assert store.persist_from_spec("exploratory", roles, WEB_SPEC) == key
        with SessionLocal() as s:
            assert s.query(SimulationPattern).filter_by(pattern_key=key).count() == 1
            assert s.query(SimulationPattern).filter_by(pattern_key=key).first().usage_count == 1
        # scene_mode lệch / đề cần vai trò template KHÔNG biểu diễn được → miss
        assert store.find("progressive", roles) is None
        assert store.find("exploratory", {"structural", "textual", "temporal"}) is None
        # CHỐNG NHIỄU ROLE (bug live): required là TẬP CON của vai trò template
        # cover được → vẫn match (analyze gắn thiếu/thừa role phụ không phá reuse)
        assert store.find("exploratory", {"structural"}) is not None
    finally:
        _cleanup([key])


def test_bool_op_pattern_la_candidate_khong_auto_reuse():
    """Op ĐÓNG BĂNG không kiểm chứng bảng chân trị được lúc live → pattern
    chứa bool op lưu status=candidate: KHÔNG auto-reuse (mẫu AND không được
    dùng cho đề OR); chỉ reuse sau khi người/benchmark nâng lên verified."""
    store = DbPatternStore("test-policy")
    roles = {"logical", "interactive"}
    key = store.persist_from_spec("exploratory", roles, AND_SPEC)
    assert key is not None
    try:
        with SessionLocal() as s:
            assert s.query(SimulationPattern).filter_by(pattern_key=key).first().status == "candidate"
        assert store.find("exploratory", roles) is None  # candidate KHÔNG auto-reuse
        with SessionLocal() as s:
            s.query(SimulationPattern).filter_by(pattern_key=key).first().status = "verified"
            s.commit()
        assert store.find("exploratory", roles).status == "verified"  # verified > validated
    finally:
        _cleanup([key])


def test_version_lech_bi_deprecated_khong_reuse():
    """Case H: pattern dsl_version không còn hỗ trợ → không auto-reuse,
    bị đánh dấu deprecated (lazy) thay vì dùng mù."""
    store = DbPatternStore("test-policy")
    roles = {"structural", "textual"}
    key = store.persist_from_spec("exploratory", roles, WEB_SPEC)
    assert key is not None
    try:
        with SessionLocal() as s:
            s.query(SimulationPattern).filter_by(pattern_key=key).first().dsl_version = "0.9"
            s.commit()
        assert store.find("exploratory", roles) is None
        with SessionLocal() as s:
            assert s.query(SimulationPattern).filter_by(pattern_key=key).first().status == "deprecated"
    finally:
        _cleanup([key])


def test_role_subset_nhung_khac_cau_truc_khong_reuse():
    """Case 1 (duyệt M7.13B): role subset CHỈ để chống nhiễu analyze — hai
    pattern cùng cover roles của query nhưng KHÁC chữ ký cấu trúc → pool mơ hồ
    → KHÔNG reuse (compose mới), không bao giờ đoán cấu trúc."""
    store = DbPatternStore("test-policy")
    # Pattern 1: web (container/heading/paragraph) — cover {structural, textual}
    k1 = store.persist_from_spec("exploratory", {"structural", "textual"}, WEB_SPEC)
    # Pattern 2: nhãn cạnh điểm (node/label) — cover {relational, textual}, cấu trúc KHÁC HẲN
    labeled_points = _norm({
        "dsl_version": "1.0", "title": "Hai điểm có chú thích",
        "objects": [
            {"id": "n1", "type": "node", "x": 20, "y": 50, "label": "A"},
            {"id": "n2", "type": "node", "x": 80, "y": 50, "label": "B"},
            {"id": "t1", "type": "label", "x": 50, "y": 20, "label": "Chú thích đoạn AB"},
        ],
        "rules": [], "interactions": [], "processes": [],
    })
    k2 = store.persist_from_spec("exploratory", {"relational", "textual"}, labeled_points)
    assert k1 is not None and k2 is not None and k1 != k2
    try:
        # required {textual} là TẬP CON coverage của CẢ HAI → mơ hồ cấu trúc → None
        assert store.find("exploratory", {"textual"}) is None
        # required đủ cụ thể để chỉ MỘT cấu trúc cover → reuse đúng pattern đó
        assert store.find("exploratory", {"structural", "textual"}).pattern_key == k1
        assert store.find("exploratory", {"relational", "textual"}).pattern_key == k2
    finally:
        _cleanup([k1, k2])


def test_cung_roles_process_khac_interaction_signature_khong_reuse_cheo():
    """Case 2 (duyệt M7.13B): cùng scene_mode + roles/process nhưng interaction
    signature khác (static vs draggable) → không reuse chéo."""
    store = DbPatternStore("test-policy")
    # Hai pattern HYBRID cùng reveal_sequence, chỉ khác drag — persist với move
    # để hybrid hợp lệ cần temporal process: dùng chính TRIANGLE reveal.
    k_static = store.persist_from_spec(
        "hybrid", {"relational", "temporal"}, TRIANGLE_STATIC
    )
    k_drag = store.persist_from_spec(
        "hybrid", {"relational", "temporal", "interactive"}, TRIANGLE_DRAG
    )
    assert k_static is not None and k_drag is not None and k_static != k_drag
    try:
        # Query subset (không exact với mẫu nào): CẢ HAI đều cover ⊇ nhưng
        # interaction signature khác nhau ([] vs [drag:node]) → mơ hồ → None
        assert store.find("hybrid", {"relational"}) is None
        # Query khớp EXACT plan-roles của một mẫu → chọn đúng mẫu đó (tầng exact
        # đứng trước subset), không bao giờ trả mẫu có interaction khác
        assert store.find("hybrid", {"relational", "temporal"}).pattern_key == k_static
        assert store.find("hybrid", {"relational", "temporal", "interactive"}).pattern_key == k_drag
        # scene_mode exact vẫn là hàng rào thứ nhất: progressive không thấy gì ở hybrid
        assert store.find("progressive", {"relational", "temporal"}) is None
    finally:
        _cleanup([k_static, k_drag])


def test_spec_co_notes_van_persist_duoc():
    """Bug live M7.13B: LLM hay điền notes → round-trip từng fail → pattern
    KHÔNG BAO GIỜ được lưu. notes là instance-specific, phải bị bỏ qua."""
    with_notes = _norm({
        "dsl_version": "1.0",
        "title": "Trang có ghi chú",
        "objects": [
            {"id": "page", "type": "container", "text": "Trang"},
            {"id": "h", "type": "heading", "text": "Tiêu đề", "parent": "page"},
        ],
        "rules": [], "interactions": [], "processes": [],
        "notes": "Mô phỏng hiển thị cấu trúc tĩnh.",
    })
    assert with_notes["notes"] is not None
    store = DbPatternStore("test-policy")
    key = store.persist_from_spec("exploratory", {"structural", "textual"}, with_notes)
    assert key is not None  # notes không được chặn persist
    _cleanup([key])


def test_spec_chi_co_title_khong_thanh_pattern():
    """Tính tổng quát: spec không có nội dung tham số hóa được (ngoài title)
    → chỉ cache exact, không lưu pattern."""
    bare = _norm({
        "dsl_version": "1.0", "title": "Hai nút",
        "objects": [
            {"id": "n1", "type": "node"}, {"id": "n2", "type": "node"},
            {"id": "e", "type": "edge", "from": "n1", "to": "n2"},
        ],
        "rules": [], "interactions": [], "processes": [],
    })
    assert DbPatternStore("test-policy").persist_from_spec("exploratory", {"relational"}, bare) is None
