# -*- coding: utf-8 -*-
"""Test M7.13B — pattern reuse end-to-end trong pipeline (mock Gemini, fake store).

Khóa: reuse CHỈ sau classify + CHỈ cho generic.rule_scene; hybrid adaptation
(deterministic fill trước, 1 call LLM nhỏ); adapted spec qua đủ 4 cổng;
adaptation fail → fallback compose new (không crash, không poison store);
compose-new thành công → persist pattern.
"""

import asyncio
import json

from app.ai import pipeline
from app.simulation.patterns import extract_template

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
    # M13: ANALYSIS_WEB_STATIC (bên dưới) dẫn xuất từ đây — cảnh dựng/hiển thị
    # trang web CHO SẴN, không đòi tính toán → "provided".
    "result_ownership": "provided",
}
FINDMAX_CLASSIFY = {"status": "ok", "simulation_id": "algorithm.find_max", "reason": None}
FINDMAX_CONFIG = {
    "problem": {"summary": "Tìm max", "input": "Dãy 3 số", "output": "Giá trị lớn nhất"},
    "data": {"array": [7, 9, 6], "labels": None, "target": None, "condition": None, "order": None},
    "data_generated": False,
    "notes": None,
}

ANALYSIS_WEB_STATIC = {
    **VALID_ANALYSIS,
    "goal": "Hiển thị cấu trúc trang web",
    "visual_needs": ["structural", "textual"],
    "temporal_needs": [],
    "scene_construction": "prebuilt",
}
GENERIC_CLASSIFY = {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None}

SPEC_WEB = {
    "dsl_version": "1.0", "title": "Trang giới thiệu",
    "objects": [
        {"id": "page", "type": "container", "text": "Trang giới thiệu"},
        {"id": "h", "type": "heading", "text": "Xin chào", "parent": "page"},
        {"id": "p", "type": "paragraph", "text": "Đây là đoạn văn giới thiệu.", "parent": "page"},
    ],
    "rules": [], "interactions": [], "processes": [],
}

ADAPT_PARAMS = {
    "title": "Trang web về ẩm thực",
    "text_page": "Trang ẩm thực Việt",
    "text_h": "Phở Hà Nội",
    "text_p": "Giới thiệu món phở truyền thống của Hà Nội.",
}


class FakeRow:
    def __init__(self, pattern_key, name, template, schema):
        self.pattern_key = pattern_key
        self.name = name
        self.template_json = json.dumps(template, ensure_ascii=False)
        self.parameter_schema_json = json.dumps(schema, ensure_ascii=False)
        self.status = "validated"


class FakeStore:
    """Store trong bộ nhớ: match exact (scene_mode, roles) như DbPatternStore."""

    def __init__(self):
        self.rows: dict[tuple, FakeRow] = {}
        self.find_calls: list[tuple] = []
        self.usage_bumps: list[str] = []
        self.persist_calls: list[tuple] = []

    def seed_from_spec(self, scene_mode, roles, raw_spec):
        from app.simulation.dsl.validator import validate_generic_config

        cfg, err = validate_generic_config(raw_spec)
        assert err is None, err
        template, schema, _ = extract_template(cfg)
        row = FakeRow(f"pk-{scene_mode}", f"{scene_mode}-mẫu", template, schema)
        self.rows[(scene_mode, frozenset(roles))] = row
        return row

    def find(self, scene_mode, roles):
        self.find_calls.append((scene_mode, frozenset(roles)))
        return self.rows.get((scene_mode, frozenset(roles)))

    def bump_usage(self, pattern_key):
        self.usage_bumps.append(pattern_key)

    def persist_from_spec(self, scene_mode, roles, spec):
        self.persist_calls.append((scene_mode, frozenset(roles), spec))
        return "pk-new"


def _fake_gemini(responses):
    calls = []

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
        calls.append({"system": system_prompt, "user": user_text, "schema": response_schema})
        if not responses:
            raise AssertionError("fake Gemini bị gọi nhiều hơn số response chuẩn bị")
        return responses.pop(0)

    return fake, calls


def test_case_c_pattern_reuse_thay_stage_simulate(monkeypatch):
    """Case C: có pattern khớp → adapt 1 call nhỏ, KHÔNG gọi simulate;
    envelope source=pattern_reuse; spec adapted qua đủ 4 cổng."""
    store = FakeStore()
    store.seed_from_spec("exploratory", {"structural", "textual"}, SPEC_WEB)
    fake, calls = _fake_gemini(
        [json.dumps(ANALYSIS_WEB_STATIC), json.dumps(GENERIC_CLASSIFY), json.dumps(ADAPT_PARAMS)]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline(
        "Hiển thị cấu trúc trang web về ẩm thực có tiêu đề và đoạn văn.", "khóa-giả",
        pattern_store=store,
    ))
    assert env["status"] == "ok"
    assert env["source"] == "pattern_reuse"
    assert env["adapt_used"] is True
    assert env["pattern_key"] == "pk-exploratory"
    assert len(calls) == 3  # analyze + classify + adapt — KHÔNG có simulate
    # call thứ 3 là ADAPT: schema chỉ gồm đúng các slot, không phải contract DSL
    assert set(calls[2]["schema"]["properties"]) == set(ADAPT_PARAMS)
    assert "HỢP ĐỒNG CONFIG" not in calls[2]["user"]
    # nội dung đã adapt cho ĐỀ MỚI, cấu trúc giữ nguyên
    texts = {o["id"]: o.get("text") for o in env["config"]["objects"]}
    assert texts["h"] == "Phở Hà Nội"
    assert env["config"]["objects"][1]["parent"] == "page"
    assert store.usage_bumps == ["pk-exploratory"]
    assert store.persist_calls == []  # reuse thì không persist thêm


def test_case_i_adapt_hong_fallback_compose(monkeypatch):
    """Case I: adapt trả rác 2 lần → fallback compose new, không crash;
    envelope source=composed + reuse_fallback=True; compose xong vẫn persist."""
    store = FakeStore()
    store.seed_from_spec("exploratory", {"structural", "textual"}, SPEC_WEB)
    fake, calls = _fake_gemini(
        [
            json.dumps(ANALYSIS_WEB_STATIC),
            json.dumps(GENERIC_CLASSIFY),
            "không phải json",   # adapt lần 1
            "vẫn không phải json",  # adapt retry → RuntimeError → fallback
            json.dumps(SPEC_WEB),  # stage_simulate compose như cũ
        ]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline(
        "Hiển thị cấu trúc trang web có tiêu đề và đoạn văn.", "khóa-giả", pattern_store=store,
    ))
    assert env["status"] == "ok"
    assert env["source"] == "composed"
    assert env["reuse_fallback"] is True
    assert len(calls) == 5
    assert store.usage_bumps == []  # reuse fail thì không tính usage
    assert len(store.persist_calls) == 1  # compose thành công → persist pattern


def test_case_i2_adapt_tra_tham_so_rac_fallback(monkeypatch):
    """Adapt trả JSON hợp lệ nhưng SAI KIỂU (chuỗi rỗng) → validate_params
    chặn TRƯỚC instantiate → fallback compose."""
    store = FakeStore()
    store.seed_from_spec("exploratory", {"structural", "textual"}, SPEC_WEB)
    bad_params = {**ADAPT_PARAMS, "text_h": "   "}
    fake, calls = _fake_gemini(
        [
            json.dumps(ANALYSIS_WEB_STATIC),
            json.dumps(GENERIC_CLASSIFY),
            json.dumps(bad_params),
            json.dumps(SPEC_WEB),
        ]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline(
        "Hiển thị cấu trúc trang web có tiêu đề và đoạn văn.", "khóa-giả", pattern_store=store,
    ))
    assert env["status"] == "ok"
    assert env["source"] == "composed"
    assert env["reuse_fallback"] is True
    assert len(calls) == 4  # adapt 1 lần (JSON hợp lệ) + simulate


def test_case_g_specialized_khong_dung_store(monkeypatch):
    """Case G: bài specialized (find_max) → store KHÔNG được hỏi, routing
    và compose như cũ — reuse chỉ dành cho generic.rule_scene."""
    store = FakeStore()
    fake, calls = _fake_gemini(
        [json.dumps(VALID_ANALYSIS), json.dumps(FINDMAX_CLASSIFY), json.dumps(FINDMAX_CONFIG)]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline(
        "Cho dãy 7, 9, 6. Tìm phần tử lớn nhất.", "khóa-giả", pattern_store=store,
    ))
    assert env["status"] == "ok"
    assert env["simulation_id"] == "algorithm.find_max"
    assert env["source"] == "composed"
    assert store.find_calls == []  # KHÔNG hỏi pattern store
    assert store.persist_calls == []  # cũng KHÔNG persist specialized config
    assert len(calls) == 3


def test_case_d_khong_reuse_cheo_scene_mode(monkeypatch):
    """Case D: store chỉ có pattern PROGRESSIVE; đề TĨNH (exploratory) →
    matcher hỏi đúng (exploratory, roles) → miss → compose, không reuse nhầm."""
    store = FakeStore()
    store.seed_from_spec(
        "progressive", {"structural", "textual", "temporal"},
        {**SPEC_WEB, "processes": [{"type": "reveal_sequence", "steps": [
            {"objects": ["h"]}, {"objects": ["p"]},
        ]}]},
    )
    fake, calls = _fake_gemini(
        [json.dumps(ANALYSIS_WEB_STATIC), json.dumps(GENERIC_CLASSIFY), json.dumps(SPEC_WEB)]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline(
        "Hiển thị cấu trúc trang web có tiêu đề và đoạn văn.", "khóa-giả", pattern_store=store,
    ))
    assert env["status"] == "ok"
    assert env["source"] == "composed"
    assert env["reuse_fallback"] is False  # không có ứng viên → không tính fallback
    assert store.find_calls == [("exploratory", frozenset({"structural", "textual"}))]
    assert len(calls) == 3  # compose bình thường


def test_khong_store_hanh_vi_cu_nguyen_ven(monkeypatch):
    """Backward-compat: không truyền pattern_store → pipeline compose như cũ,
    envelope vẫn có source=composed."""
    fake, calls = _fake_gemini(
        [json.dumps(ANALYSIS_WEB_STATIC), json.dumps(GENERIC_CLASSIFY), json.dumps(SPEC_WEB)]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Hiển thị cấu trúc trang web nhé.", "khóa-giả"))
    assert env["status"] == "ok"
    assert env["source"] == "composed"
    assert env["reuse_fallback"] is False
    assert len(calls) == 3


def test_adapt_skill_ton_tai():
    from app.ai.gemini import load_skill

    content = load_skill("adapt")
    assert "tham số" in content.lower()
    assert "KHÔNG sinh timeline" in content
