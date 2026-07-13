# -*- coding: utf-8 -*-
"""Test pipeline analyze → classify → simulate → validate (mock Gemini —
không cần mạng, không cần key). Khóa chặt các bất biến M3:
- LLM chỉ sinh config; envelope chỉ phát hành sau validation;
- classify không gán bừa; retry khi LLM trả sai; fail sau 3 lần → lỗi.
"""

import json

import asyncio

import pytest

from app.ai import pipeline

VALID_ANALYSIS = {
    "objects": ["dãy số"],
    "data": [{"description": "dãy điểm", "values": [7, 9, 6], "labels": None}],
    "relations": [],
    "processes": ["duyệt dãy"],
    "constraints": [],
    "goal": "Tìm phần tử lớn nhất",
    "input_description": "Dãy 3 số",
    "output_description": "Giá trị lớn nhất",
    "notes": None,
}

VALID_CLASSIFY = {"status": "ok", "simulation_id": "algorithm.find_max", "reason": None}

VALID_CONFIG = {
    "problem": {"summary": "Tìm max", "input": "Dãy 3 số", "output": "Giá trị lớn nhất"},
    "data": {"array": [7, 9, 6], "labels": None, "target": None, "condition": None, "order": None},
    "data_generated": False,
    "notes": None,
}


def _fake_gemini(responses: list[str]):
    """Tạo fake call_gemini trả lần lượt từng phần tử; ghi lại prompt nhận được."""
    calls: list[dict] = []

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2):
        calls.append({"system": system_prompt, "user": user_text})
        if not responses:
            raise AssertionError("fake Gemini bị gọi nhiều hơn số response chuẩn bị")
        return responses.pop(0)

    return fake, calls


def test_analyze_schema_co_required_capabilities():
    """M7.9: analyze phải trích required_capabilities + scene_construction để
    classify đối chiếu năng lực."""
    props = pipeline.ANALYZE_SCHEMA["properties"]
    assert "required_capabilities" in props
    assert "scene_construction" in props
    assert set(props["scene_construction"]["enum"]) == {"prebuilt", "step_by_step"}


def test_classify_skill_co_capability_adequacy():
    """M7.9: classify.md phải có quy tắc kiểm ĐỦ NĂNG LỰC của specialized —
    cần dựng từng bước thì specialized không đủ → generic."""
    from app.ai.gemini import load_skill

    c = load_skill("classify")
    assert "step_by_step" in c
    assert "reveal_sequence" in c
    assert "generic.rule_scene" in c


def test_classify_prompt_co_capability_manifest(monkeypatch):
    """M7.8: stage classify PHẢI thấy năng lực generic (điểm→node, đoạn→edge,
    reveal_sequence) để định tuyến theo capability, không theo tên môn học."""
    captured = {}

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2):
        captured["user"] = user_text
        captured["temp"] = temperature
        return json.dumps({"status": "ok", "simulation_id": "generic.rule_scene", "reason": None})

    monkeypatch.setattr(pipeline, "call_gemini", fake)
    asyncio.run(pipeline.stage_classify("Dựng tam giác ABC.", VALID_ANALYSIS, "khóa-giả"))

    u = captured["user"]
    assert "reveal_sequence" in u  # năng lực hình thành từng bước
    assert "node" in u and "edge" in u  # ánh xạ điểm/đoạn
    assert "KHÔNG dựa vào tên môn học" in u or "NĂNG LỰC" in u
    assert captured["temp"] == 0.0  # classify tất định hơn


def test_pipeline_duong_vui(monkeypatch):
    fake, calls = _fake_gemini(
        [json.dumps(VALID_ANALYSIS), json.dumps(VALID_CLASSIFY), json.dumps(VALID_CONFIG)]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Cho dãy 7, 9, 6. Tìm phần tử lớn nhất.", "khóa-giả"))

    assert env["status"] == "ok"
    assert env["simulation_id"] == "algorithm.find_max"
    assert env["domain"] == "algorithm"
    assert env["config"]["algorithm_id"] == "find_max"  # validator đã chuẩn hóa
    assert env["config"]["data"]["array"] == [7, 9, 6]
    assert env["analysis"]["goal"] == "Tìm phần tử lớn nhất"
    assert env["title"] == "Tìm max"
    assert len(calls) == 3  # đúng 3 stage, không thừa


def test_classify_unsupported_thi_dung_pipeline(monkeypatch):
    fake, calls = _fake_gemini(
        [
            json.dumps(VALID_ANALYSIS),
            json.dumps({"status": "unsupported", "simulation_id": None, "reason": "Bài hình học"}),
        ]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Tính diện tích tam giác ABC.", "khóa-giả"))
    assert env["status"] == "unsupported"
    assert env["reason"] == "Bài hình học"
    assert len(calls) == 2  # KHÔNG gọi stage simulate


def test_classify_id_ngoai_danh_muc_thanh_unsupported(monkeypatch):
    """LLM chọn id KHÔNG có trong catalog → không gán bừa, trả unsupported."""
    fake, _ = _fake_gemini(
        [
            json.dumps(VALID_ANALYSIS),
            json.dumps({"status": "ok", "simulation_id": "chemistry.reaction", "reason": None}),
        ]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Cân bằng phản ứng hóa học.", "khóa-giả"))
    assert env["status"] == "unsupported"


def test_simulate_sai_duoc_retry_kem_thong_bao_loi(monkeypatch):
    bad_config = {**VALID_CONFIG, "data": {"array": list(range(20))}}  # 20 phần tử → validator chặn
    fake, calls = _fake_gemini(
        [
            json.dumps(VALID_ANALYSIS),
            json.dumps(VALID_CLASSIFY),
            json.dumps(bad_config),
            json.dumps(VALID_CONFIG),
        ]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Cho dãy 7, 9, 6. Tìm phần tử lớn nhất.", "khóa-giả"))
    assert env["status"] == "ok"
    assert len(calls) == 4
    # Prompt lần retry phải chứa thông báo lỗi validation
    assert "bị từ chối vì" in calls[3]["user"]
    assert "15" in calls[3]["user"]


def test_simulate_sinh_timeline_bi_chan(monkeypatch):
    """LLM cố sinh diễn biến → validator từ chối, retry; sai mãi → RuntimeError."""
    with_timeline = {**VALID_CONFIG, "timeline": [{"step": 1}]}
    fake, calls = _fake_gemini(
        [
            json.dumps(VALID_ANALYSIS),
            json.dumps(VALID_CLASSIFY),
            json.dumps(with_timeline),
            json.dumps(with_timeline),
            json.dumps(with_timeline),
        ]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    with pytest.raises(RuntimeError, match="3 lần"):
        asyncio.run(pipeline.run_pipeline("Cho dãy 7, 9, 6. Tìm phần tử lớn nhất.", "khóa-giả"))
    assert len(calls) == 5  # analyze + classify + 3 lần simulate


# ── M7.11: representation plan + semantic compatibility ───────

# M7.12: 'structural'+'textual' giờ COVER được (container/heading/paragraph) →
# web KHÔNG còn capability_gap mà render được.
ANALYSIS_WEB = {**VALID_ANALYSIS, "visual_needs": ["structural", "textual"]}
# Vai trò 'relational' cover được (node/edge) → không gap, đi tiếp bình thường.
ANALYSIS_GRAPH = {**VALID_ANALYSIS, "relation_roles": ["relational"]}

GENERIC_CLASSIFY = {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None}

# M7.12: spec cấu trúc/nội dung ĐÚNG cho web — cover {structural, textual}.
SPEC_WEB = {
    "dsl_version": "1.0", "title": "Trang giới thiệu",
    "objects": [
        {"id": "page", "type": "container", "text": "Trang giới thiệu"},
        {"id": "h", "type": "heading", "text": "Xin chào", "parent": "page"},
        {"id": "p", "type": "paragraph", "text": "Đây là đoạn văn giới thiệu.", "parent": "page"},
    ],
    "rules": [], "interactions": [], "processes": [],
}

# spec generic HỢP LỆ cú pháp nhưng chỉ cover {interactive,logical,numeric} —
# THIẾU relational → semantic mismatch, phải bị từ chối + retry.
SPEC_SWITCH_LAMP = {
    "dsl_version": "1.0", "title": "gate",
    "objects": [
        {"id": "a", "type": "switch", "value": 0, "x": 10, "y": 10},
        {"id": "b", "type": "switch", "value": 0, "x": 30, "y": 10},
        {"id": "y", "type": "lamp", "x": 50, "y": 50},
    ],
    "rules": [{"type": "boolean", "op": "and", "inputs": ["a", "b"], "target": "y"}],
    "interactions": [{"type": "toggle", "target": "a"}], "processes": [],
}
# spec generic cover relational (node/edge) → khớp vai trò đề cần.
SPEC_GRAPH = {
    "dsl_version": "1.0", "title": "graph",
    "objects": [
        {"id": "n1", "type": "node", "node_type": "client", "x": 10, "y": 10},
        {"id": "n2", "type": "node", "node_type": "server", "x": 80, "y": 10},
        {"id": "e", "type": "edge", "from": "n1", "to": "n2"},
    ],
    "rules": [], "interactions": [], "processes": [],
}


def test_pipeline_web_structural_render_duoc_khong_gap(monkeypatch):
    """M7.12: đề web (structural+textual) giờ CÓ primitive → KHÔNG capability_gap,
    đi tiếp classify+simulate, ra generic.rule_scene với container/heading/paragraph
    (KHÔNG switch/lamp), semantic compat PASS."""
    fake, calls = _fake_gemini(
        [json.dumps(ANALYSIS_WEB), json.dumps(GENERIC_CLASSIFY), json.dumps(SPEC_WEB)]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Hiển thị cấu trúc trang web có tiêu đề và đoạn văn.", "khóa-giả"))
    assert env["status"] == "ok"
    assert env["simulation_id"] == "generic.rule_scene"
    assert env["representation_plan"]["unsupported_capabilities"] == []
    assert len(calls) == 3  # analyze + classify + simulate (không dừng sớm, không retry)
    types = {o["type"] for o in env["config"]["objects"]}
    assert types == {"container", "heading", "paragraph"}
    assert "switch" not in types and "lamp" not in types


def test_pipeline_semantic_mismatch_thi_retry(monkeypatch):
    """§3: spec sinh ra đúng cú pháp nhưng THIẾU vai trò relational đề cần →
    semantic compat từ chối + retry kèm thông báo vai trò còn thiếu."""
    fake, calls = _fake_gemini(
        [
            json.dumps(ANALYSIS_GRAPH),
            json.dumps(GENERIC_CLASSIFY),
            json.dumps(SPEC_SWITCH_LAMP),  # mismatch: thiếu relational
            json.dumps(SPEC_GRAPH),        # sửa: có node/edge
        ]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Vẽ đồ thị hai nút nối nhau.", "khóa-giả"))
    assert env["status"] == "ok"
    assert env["simulation_id"] == "generic.rule_scene"
    assert len(calls) == 4  # analyze + classify + 2 lần simulate
    assert "vai trò ngữ nghĩa" in calls[3]["user"]
    assert "relational" in calls[3]["user"]


def test_pipeline_envelope_co_representation_plan(monkeypatch):
    """§2: envelope thành công KÈM representation_plan (bước trung gian tất định)."""
    fake, _ = _fake_gemini(
        [json.dumps(VALID_ANALYSIS), json.dumps(VALID_CLASSIFY), json.dumps(VALID_CONFIG)]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Cho dãy 7, 9, 6. Tìm phần tử lớn nhất.", "khóa-giả"))
    plan = env["representation_plan"]
    assert set(plan) == {
        "semantic_roles", "required_dsl_capabilities", "scene_mode",
        "mapping_intent", "unsupported_capabilities",
    }
    assert plan["scene_mode"] in {"exploratory", "progressive", "hybrid"}


# ── M7.13A: scene-mode consistency trong stage simulate ───────

ANALYSIS_WEB_STATIC = {
    **VALID_ANALYSIS,
    "visual_needs": ["structural", "textual"],
    "temporal_needs": [],
    "scene_construction": "prebuilt",
}
ANALYSIS_WEB_BUILD = {
    **VALID_ANALYSIS,
    "visual_needs": ["structural", "textual"],
    "temporal_needs": ["temporal"],
    "scene_construction": "step_by_step",
}
SPEC_WEB_FAKE_REVEAL = {
    **SPEC_WEB,
    "processes": [{"type": "reveal_sequence", "steps": [{"objects": ["h"]}, {"objects": ["p"]}]}],
}


def test_simulate_prompt_co_scene_mode(monkeypatch):
    """M7.13A §9: plan.scene_mode PHẢI được truyền vào prompt simulate của
    generic — root cause của reveal giả là prompt không biết chế độ cảnh."""
    fake, calls = _fake_gemini(
        [json.dumps(ANALYSIS_WEB_STATIC), json.dumps(GENERIC_CLASSIFY), json.dumps(SPEC_WEB)]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Hiển thị cấu trúc một trang web.", "khóa-giả"))
    assert env["status"] == "ok"
    assert env["representation_plan"]["scene_mode"] == "exploratory"
    assert "CHẾ ĐỘ CẢNH" in calls[2]["user"]
    assert "exploratory" in calls[2]["user"]


def test_exploratory_reveal_gia_bi_tu_choi_va_retry(monkeypatch):
    """Điều chỉnh #1+#3: cảnh TĨNH mà spec chèn reveal giả → consistency check
    tất định từ chối + retry kèm lý do; lần 2 bỏ process → OK."""
    fake, calls = _fake_gemini(
        [
            json.dumps(ANALYSIS_WEB_STATIC),
            json.dumps(GENERIC_CLASSIFY),
            json.dumps(SPEC_WEB_FAKE_REVEAL),  # reveal giả cho cảnh tĩnh
            json.dumps(SPEC_WEB),              # sửa: bỏ process
        ]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Hiển thị cấu trúc một trang web.", "khóa-giả"))
    assert env["status"] == "ok"
    assert env["config"]["processes"] == []
    assert len(calls) == 4  # analyze + classify + 2 lần simulate
    assert "TĨNH" in calls[3]["user"]  # retry kèm lý do exploratory


def test_progressive_thieu_temporal_process_bi_tu_choi(monkeypatch):
    """Chiều ngược: đề 'quá trình tạo từng bước' (progressive) mà spec KHÔNG có
    process diễn biến → từ chối + retry; lần 2 có reveal → OK."""
    fake, calls = _fake_gemini(
        [
            json.dumps(ANALYSIS_WEB_BUILD),
            json.dumps(GENERIC_CLASSIFY),
            json.dumps(SPEC_WEB),              # thiếu process
            json.dumps(SPEC_WEB_FAKE_REVEAL),  # progressive thì reveal là ĐÚNG
        ]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Mô phỏng quá trình tạo trang web từng bước.", "khóa-giả"))
    assert env["status"] == "ok"
    assert env["representation_plan"]["scene_mode"] == "progressive"
    assert env["config"]["processes"][0]["type"] == "reveal_sequence"
    assert len(calls) == 4
    assert "diễn biến" in calls[3]["user"]


def test_hybrid_prebuilt_voi_move_khong_can_reveal(monkeypatch):
    """Điều chỉnh #1: topology CHO SẴN + gói tin chạy = hybrid; move_along_path
    thuộc HỌ temporal nên thỏa consistency — KHÔNG bắt buộc reveal_sequence."""
    analysis_pkt = {
        **VALID_ANALYSIS,
        "relation_roles": ["relational"],
        "process_roles": ["movement", "temporal"],
        "scene_construction": "prebuilt",
    }
    spec_graph_move = {
        **SPEC_GRAPH,
        "objects": SPEC_GRAPH["objects"] + [{"id": "pkt", "type": "moving_entity"}],
        "processes": [{"type": "move_along_path", "entity": "pkt", "path": ["n1", "n2"]}],
    }
    fake, calls = _fake_gemini(
        [json.dumps(analysis_pkt), json.dumps(GENERIC_CLASSIFY), json.dumps(spec_graph_move)]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Gói tin đi trên topology cho sẵn.", "khóa-giả"))
    assert env["status"] == "ok"
    assert env["representation_plan"]["scene_mode"] == "hybrid"
    assert len(calls) == 3  # pass ngay lần đầu, không retry


def test_analyze_json_hong_duoc_retry(monkeypatch):
    fake, calls = _fake_gemini(
        [
            "đây không phải json",
            json.dumps(VALID_ANALYSIS),
            json.dumps(VALID_CLASSIFY),
            json.dumps(VALID_CONFIG),
        ]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Cho dãy 7, 9, 6. Tìm phần tử lớn nhất.", "khóa-giả"))
    assert env["status"] == "ok"
    assert len(calls) == 4
