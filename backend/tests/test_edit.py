# -*- coding: utf-8 -*-
"""Test NL edit nhẹ (M7.14A) — mock Gemini, không mạng.

Khóa hai chỉnh sửa kiến trúc đã duyệt:
A. PatchResult tách bạch (valid/structurally_invalid/unsupported_to_verify).
B. Server KHÔNG tin LLM tự quyết supported/unsupported — đối chiếu
   required_roles ∩ known_gap_roles một cách tất định, gap → không apply.
Và: edit KHÔNG chạy full analyze/classify/simulate (đúng 1 call LLM nhỏ).
"""

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from app.ai import edit as edit_module
from app.ai.edit import edit_simulation
from app.main import app

client = TestClient(app)


TRIANGLE = {
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

PATCH_ADD_D = {
    "required_roles": ["relational"],
    "operations": [
        {"op": "add_object", "object": {"id": "D", "type": "node", "label": "D", "x": 50, "y": 92}},
        {"op": "connect", "from": "A", "to": "D", "edge_id": "AD"},
    ],
    "note": None,
}

GEO_REFUSAL = {
    "required_roles": ["relational", "geometric_projection", "geometric_perpendicular"],
    "operations": [],
    "note": None,
}


def _fake_gemini(responses):
    calls = []

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
        calls.append({"system": system_prompt, "user": user_text, "schema": response_schema})
        if not responses:
            raise AssertionError("fake Gemini bị gọi nhiều hơn số response chuẩn bị")
        return responses.pop(0)

    return fake, calls


def test_edit_them_diem_noi_canh_mot_call(monkeypatch):
    """Case C (§11): 'thêm D nối A' → patch valid, ĐÚNG 1 call LLM, config mới
    có D/AD, spec gốc không bị mutate."""
    fake, calls = _fake_gemini([json.dumps(PATCH_ADD_D)])
    monkeypatch.setattr(edit_module, "call_gemini", fake)

    before = json.dumps(TRIANGLE, sort_keys=True)
    result = asyncio.run(edit_simulation(TRIANGLE, "Thêm điểm D và nối D với A.", "khóa-giả"))
    assert result["status"] == "valid"
    ids = {o["id"] for o in result["config"]["objects"]}
    assert {"D", "AD"} <= ids
    assert result["patch"]["operations"][0]["op"] == "add_object"
    assert len(calls) == 1  # KHÔNG analyze/classify/simulate
    assert json.dumps(TRIANGLE, sort_keys=True) == before
    # prompt nhỏ: có danh sách object + contract ops, KHÔNG kèm contract DSL dài
    assert "id=A" in calls[0]["user"] and "add_object" in calls[0]["user"]
    assert "HỢP ĐỒNG CONFIG" not in calls[0]["user"]


def test_edit_dan_xuat_server_quyet_gap_khong_tin_llm(monkeypatch):
    """Chỉnh sửa B: LLM khai required_roles chứa gap role → SERVER đối chiếu
    known_gap_roles và trả unsupported_to_verify — patch KHÔNG được áp,
    kể cả khi LLM có kèm operations."""
    sneaky = {
        **GEO_REFUSAL,
        # LLM "lỡ" vẫn đề xuất node D tọa độ đoán — server phải bỏ, không áp
        "operations": [{"op": "add_object", "object": {"id": "D", "type": "node", "x": 47, "y": 70}}],
    }
    fake, calls = _fake_gemini([json.dumps(sneaky)])
    monkeypatch.setattr(edit_module, "call_gemini", fake)

    result = asyncio.run(edit_simulation(TRIANGLE, "Thêm chân đường cao D từ A xuống BC.", "khóa-giả"))
    assert result["status"] == "unsupported_to_verify"
    assert "geometric_projection" in result["reason"]
    assert result["missing_roles"] == ["geometric_perpendicular", "geometric_projection"]
    assert "config" not in result  # KHÔNG có spec mới — không render xấp xỉ
    assert len(calls) == 1


def test_edit_patch_hong_retry_kem_loi_roi_thanh_cong(monkeypatch):
    bad = {"required_roles": ["relational"], "operations": [
        {"op": "connect", "from": "A", "to": "Zzz", "edge_id": "AZ"},
    ], "note": None}
    fake, calls = _fake_gemini([json.dumps(bad), json.dumps(PATCH_ADD_D)])
    monkeypatch.setattr(edit_module, "call_gemini", fake)

    result = asyncio.run(edit_simulation(TRIANGLE, "Nối A với D.", "khóa-giả"))
    assert result["status"] == "valid"
    assert len(calls) == 2
    assert "bị từ chối vì" in calls[1]["user"]  # retry kèm lý do


def test_edit_sai_mai_tra_structurally_invalid(monkeypatch):
    bad = {"required_roles": [], "operations": [{"op": "remove_object", "id": "Zzz"}], "note": None}
    fake, calls = _fake_gemini([json.dumps(bad), json.dumps(bad)])
    monkeypatch.setattr(edit_module, "call_gemini", fake)

    result = asyncio.run(edit_simulation(TRIANGLE, "Xóa Zzz.", "khóa-giả"))
    assert result["status"] == "structurally_invalid"
    assert "không tồn tại" in result["error"]
    assert len(calls) == 2


def test_edit_config_rac_bi_chan_truoc_khi_goi_llm(monkeypatch):
    async def boom(*a, **k):
        raise AssertionError("không được gọi LLM khi config đầu vào đã hỏng")

    monkeypatch.setattr(edit_module, "call_gemini", boom)
    result = asyncio.run(edit_simulation({"title": ""}, "Thêm D.", "khóa-giả"))
    assert result["status"] == "structurally_invalid"


def test_edit_schema_dan_xuat_tu_manifest():
    """Chống drift như bug M7.13A: enum type trong EDIT_SCHEMA phải == manifest."""
    from app.ai.edit import EDIT_SCHEMA
    from app.simulation.dsl.manifest import MANIFEST, SEMANTIC_ROLES

    props = EDIT_SCHEMA["properties"]
    obj_enum = set(props["operations"]["items"]["properties"]["object"]["properties"]["type"]["enum"])
    assert obj_enum == set(MANIFEST["object_types"])
    assert set(props["required_roles"]["items"]["enum"]) == set(SEMANTIC_ROLES)


def test_edit_skill_co_gap_role_va_luat_khong_xap_xi():
    from app.ai.gemini import load_skill

    s = load_skill("edit")
    assert "geometric_projection" in s and "numeric_threshold" in s
    assert "KHÔNG tự đặt tọa độ xấp xỉ" in s
    assert "KHÔNG sinh timeline" in s


# ── Endpoint /api/edit ────────────────────────────────────────

@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def test_api_edit_chi_nhan_generic():
    res = client.post("/api/edit", json={
        "simulation_id": "algorithm.find_max", "config": {}, "instruction": "Thêm cột.",
    })
    assert res.status_code == 400
    assert "generic" in res.json()["error"]


def test_api_edit_instruction_trong_va_thieu_key():
    res = client.post("/api/edit", json={
        "simulation_id": "generic.rule_scene", "config": TRIANGLE, "instruction": "  ",
    })
    assert res.status_code == 400
    res2 = client.post("/api/edit", json={
        "simulation_id": "generic.rule_scene", "config": TRIANGLE, "instruction": "Thêm điểm D.",
    })
    assert res2.status_code == 503
    assert "GEMINI_API_KEY" in res2.json()["error"]


def test_api_edit_happy_va_unsupported(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")

    async def fake_ok(config, instruction, api_key):
        return {"status": "valid", "config": {"title": "mới"}, "patch": {"operations": []}}

    from app import main as main_module

    monkeypatch.setattr(main_module, "edit_simulation", fake_ok)
    res = client.post("/api/edit", json={
        "simulation_id": "generic.rule_scene", "config": TRIANGLE, "instruction": "Thêm D.",
    })
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    async def fake_gap(config, instruction, api_key):
        return {"status": "unsupported_to_verify", "reason": "cần geometric_projection", "missing_roles": ["geometric_projection"]}

    monkeypatch.setattr(main_module, "edit_simulation", fake_gap)
    res2 = client.post("/api/edit", json={
        "simulation_id": "generic.rule_scene", "config": TRIANGLE, "instruction": "Thêm chân đường cao.",
    })
    assert res2.status_code == 200  # phán quyết learner-facing, không phải lỗi giao thức
    assert res2.json()["status"] == "unsupported_to_verify"

    async def fake_bad(config, instruction, api_key):
        return {"status": "structurally_invalid", "error": "id trùng"}

    monkeypatch.setattr(main_module, "edit_simulation", fake_bad)
    res3 = client.post("/api/edit", json={
        "simulation_id": "generic.rule_scene", "config": TRIANGLE, "instruction": "Thêm A.",
    })
    assert res3.status_code == 422
