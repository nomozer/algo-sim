# -*- coding: utf-8 -*-
"""Capability-boundary / correctness audit tests (M7.14C).

Khóa ranh giới: đề cần QUAN HỆ DẪN XUẤT (hình học phải tính, ngưỡng, chuyển
động liên tục, thuật toán tự do) → capability_gap TRUNG THỰC — dừng TRƯỚC
classify, không chạm pattern store, không render node/edge xấp xỉ.
Chiều ngược (precision guard): dựng hình TƯỜNG MINH không được gap oan.

Mock call_gemini — không mạng. Quyết định gap là TẤT ĐỊNH một khi analysis
có vai trò (LLM chỉ gắn vai trò; live eval khóa phần đó).
"""

import asyncio
import json

from app.ai import pipeline

BASE_ANALYSIS = {
    "objects": [],
    "data": [],
    "relations": [],
    "processes": [],
    "constraints": [],
    "goal": "",
    "input_description": "",
    "output_description": "",
    "notes": None,
}


def _fake_gemini(responses):
    calls = []

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
        calls.append({"user": user_text})
        if not responses:
            raise AssertionError("fake Gemini bị gọi nhiều hơn số response chuẩn bị")
        return responses.pop(0)

    return fake, calls


class SpyStore:
    """Store giả chỉ để khẳng định pattern reuse KHÔNG bị chạm khi gap."""

    def __init__(self):
        self.find_calls = []
        self.persist_calls = []

    def find(self, scene_mode, roles):
        self.find_calls.append((scene_mode, frozenset(roles)))
        return None

    def bump_usage(self, key):
        raise AssertionError("không được bump usage trong các case boundary")

    def persist_from_spec(self, scene_mode, roles, spec):
        self.persist_calls.append((scene_mode, frozenset(roles)))
        return None


GENERIC_PICK = {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None}


def _run_gap_case(monkeypatch, roles_fields: dict) -> tuple[dict, list, SpyStore]:
    """Chạy run_pipeline với analysis chứa vai trò cho trước; trả (env, calls, store).

    Mock classify CHỌN generic (trường hợp lạc quan nhất) — gap của DSL vẫn
    phải chặn: chứng minh phán quyết là TẤT ĐỊNH, không phụ thuộc classify."""
    analysis = {**BASE_ANALYSIS, **roles_fields}
    fake, calls = _fake_gemini([json.dumps(analysis), json.dumps(GENERIC_PICK)])
    monkeypatch.setattr(pipeline, "call_gemini", fake)
    store = SpyStore()
    env = asyncio.run(pipeline.run_pipeline("Đề boundary.", "khóa-giả", pattern_store=store))
    return env, calls, store


# ── Case 1: hình học dẫn xuất (bài audit gốc) ─────────────────

def test_geometry_dan_xuat_gap_truoc_classify_khong_cham_store(monkeypatch):
    """Boundary #1: projection/perpendicular/intersection/circle/locus →
    capability_gap, CHỈ 1 call LLM (analyze) — classify/simulate/pattern store
    không được chạm; reason nêu đúng vai trò thiếu."""
    env, calls, store = _run_gap_case(monkeypatch, {
        "entity_roles": ["relational", "geometric_projection"],
        "relation_roles": ["geometric_perpendicular", "geometric_intersection", "geometric_circle"],
        "process_roles": ["geometric_locus", "temporal"],
        "interaction_needs": ["interactive"],
    })
    assert env["status"] == "unsupported"
    assert env["failure_category"] == "capability_gap"
    # M7.14C-fix: classify VẪN chạy (để specialized không bị vạ lây) nhưng
    # simulate/pattern-store tuyệt đối không được chạm
    assert len(calls) == 2
    assert store.find_calls == [] and store.persist_calls == []
    for role in ("geometric_projection", "geometric_perpendicular",
                 "geometric_intersection", "geometric_circle", "geometric_locus"):
        assert role in env["reason"]
    # plan vẫn được trả kèm để giải thích/telemetry
    assert set(env["representation_plan"]["unsupported_capabilities"]) >= {"geometric_projection"}


# ── Case 2–4: threshold / orbit / freealgo ────────────────────

def test_threshold_gap(monkeypatch):
    """Boundary #2: 'ít nhất k trong n' chưa có rule → gap, KHÔNG ép weighted_sum sai."""
    env, calls, _ = _run_gap_case(monkeypatch, {
        "entity_roles": ["logical", "interactive"],
        "relation_roles": ["numeric_threshold"],
    })
    assert env["status"] == "unsupported"
    assert env["failure_category"] == "capability_gap"
    assert "numeric_threshold" in env["reason"]
    assert len(calls) == 2


def test_orbit_gap(monkeypatch):
    """Boundary #3: chuyển động liên tục/quỹ đạo → gap (move_along_path là RỜI RẠC)."""
    env, calls, _ = _run_gap_case(monkeypatch, {
        "entity_roles": ["movement"],
        "process_roles": ["continuous_motion", "temporal"],
    })
    assert env["status"] == "unsupported"
    assert "continuous_motion" in env["reason"]
    assert len(calls) == 2


def test_freealgo_gap(monkeypatch):
    """Boundary #4: thuật toán tự nghĩ không có engine → gap."""
    env, calls, _ = _run_gap_case(monkeypatch, {
        "process_roles": ["arbitrary_algorithm"],
    })
    assert env["status"] == "unsupported"
    assert "arbitrary_algorithm" in env["reason"]
    assert len(calls) == 2


def test_gap_role_khong_va_lay_specialized(monkeypatch):
    """Bug live M7.14: 'tính tổng các số lớn hơn 4' bị analyze gắn
    numeric_threshold → gap OAN dù algorithm.sum_if có engine chuyên biệt
    (không dùng DSL). Fix: gap chỉ chặn ĐƯỜNG GENERIC — classify chọn
    specialized thì pipeline đi tiếp bình thường."""
    analysis = {
        **BASE_ANALYSIS,
        "data": [{"description": "dãy số", "values": [5, 8, 3, 9, 4], "labels": None}],
        "goal": "Tính tổng các số lớn hơn 4",
        "relation_roles": ["numeric_threshold"],  # tag oan từ analyze
        "entity_roles": ["numeric"],
    }
    classify = {"status": "ok", "simulation_id": "algorithm.sum_if", "reason": None}
    config = {
        "problem": {"summary": "Tổng có điều kiện", "input": "Dãy 5 số", "output": "Tổng các số > 4"},
        "data": {"array": [5, 8, 3, 9, 4], "labels": None, "target": None,
                 "condition": {"op": ">", "value": 4}, "order": None},
        "data_generated": False,
        "notes": None,
    }
    fake, calls = _fake_gemini([json.dumps(analysis), json.dumps(classify), json.dumps(config)])
    monkeypatch.setattr(pipeline, "call_gemini", fake)
    store = SpyStore()

    env = asyncio.run(pipeline.run_pipeline("Tính tổng các số lớn hơn 4.", "khóa-giả", pattern_store=store))
    assert env["status"] == "ok"
    assert env["simulation_id"] == "algorithm.sum_if"
    assert len(calls) == 3  # analyze + classify + simulate — không bị gap chặn
    assert store.find_calls == []  # reuse vẫn chỉ dành cho generic


# ── Cổng thứ hai: semantic compat trong stage simulate ────────

def test_cong_hai_semantic_compat_bao_gap():
    """Nếu vai trò dẫn xuất lọt tới stage simulate (phòng hờ), semantic compat
    cũng trả capability_gap — hai lớp chặn độc lập."""
    from app.simulation.semantic import check_semantic_compatibility

    res = check_semantic_compatibility(
        {"relational", "geometric_projection"},
        {"objects": [{"id": "a", "type": "node"}], "rules": [], "interactions": [], "processes": []},
    )
    assert not res["ok"]
    assert res["kind"] == "capability_gap"
    assert res["missing"] == ["geometric_projection"]


# ── Precision guards: KHÔNG gap oan bài tường minh ────────────

TRIANGLE_ANALYSIS = {
    **BASE_ANALYSIS,
    "goal": "Dựng tam giác ABC từng bước",
    "entity_roles": ["relational"],
    "process_roles": ["temporal"],
    "scene_construction": "step_by_step",
    # M13: điểm/cạnh NÊU TÊN tường minh — cảnh dựng dần, không tính toán.
    "result_ownership": "provided",
}
GENERIC_CLASSIFY = {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None}
TRIANGLE_SPEC = {
    "dsl_version": "1.0",
    "title": "Tam giác ABC",
    "objects": [
        {"id": "A", "type": "node", "x": 20, "y": 70},
        {"id": "B", "type": "node", "x": 80, "y": 70},
        {"id": "C", "type": "node", "x": 50, "y": 20},
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


def test_precision_guard_tam_giac_tuong_minh_khong_gap(monkeypatch):
    """Boundary #6: dựng điểm/cạnh ĐƯỢC NÊU TÊN tường minh = relational+temporal
    → KHÔNG gap, pipeline đi tiếp bình thường tới envelope ok."""
    fake, calls = _fake_gemini(
        [json.dumps(TRIANGLE_ANALYSIS), json.dumps(GENERIC_CLASSIFY), json.dumps(TRIANGLE_SPEC)]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Dựng tam giác ABC từng bước.", "khóa-giả"))
    assert env["status"] == "ok"
    assert env["simulation_id"] == "generic.rule_scene"
    assert env["representation_plan"]["unsupported_capabilities"] == []
    assert len(calls) == 3


def test_precision_guard_web_structural_khong_gap(monkeypatch):
    """Boundary #8: web structural (structural+textual) vẫn OK như M7.12."""
    # M13: hiển thị cấu trúc trang web CHO SẴN — cảnh dựng/hiển thị, không tính toán.
    analysis = {**BASE_ANALYSIS, "visual_needs": ["structural", "textual"], "result_ownership": "provided"}
    spec = {
        "dsl_version": "1.0", "title": "Trang web",
        "objects": [
            {"id": "page", "type": "container", "text": "Trang web"},
            {"id": "h", "type": "heading", "text": "Xin chào", "parent": "page"},
        ],
        "rules": [], "interactions": [], "processes": [],
    }
    fake, calls = _fake_gemini([json.dumps(analysis), json.dumps(GENERIC_CLASSIFY), json.dumps(spec)])
    monkeypatch.setattr(pipeline, "call_gemini", fake)
    env = asyncio.run(pipeline.run_pipeline("Hiển thị cấu trúc trang web.", "khóa-giả"))
    assert env["status"] == "ok"
    assert env["representation_plan"]["unsupported_capabilities"] == []


# ── Prompt guards: analyze/classify phải NÓI về ranh giới ─────

def test_analyze_skill_day_du_8_gap_role():
    from app.ai.gemini import load_skill

    a = load_skill("analyze")
    for role in ("geometric_projection", "geometric_perpendicular", "geometric_intersection",
                 "geometric_circle", "geometric_locus", "numeric_threshold",
                 "continuous_motion", "arbitrary_algorithm"):
        assert role in a, f"analyze.md thiếu hướng dẫn gắn {role}"
    # chống gap oan: phải có luật phân biệt tường minh vs dẫn xuất
    assert "TƯỜNG MINH" in a


def test_capability_summary_liet_ke_ranh_gioi_moi():
    """Phòng tuyến 2 (classify): danh sách 'THẬT SỰ CHƯA CÓ' phải nêu các quan hệ
    dẫn xuất + ngưỡng + thuật toán tự nghĩ."""
    from app.simulation.dsl.manifest import manifest_capability_summary

    s = manifest_capability_summary()
    for cum in ("chân đường cao", "giao điểm", "ngoại tiếp", "quỹ tích",
                "ít nhất k trong n", "tự nghĩ"):
        assert cum in s, f"capability summary thiếu ranh giới: {cum}"
