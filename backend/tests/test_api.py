# -*- coding: utf-8 -*-
"""Test API M3 bằng FastAPI TestClient — không cần mạng, không cần key.

Khóa chặt: contract /api/analyze (InputPayload) + /api/explain,
thông điệp khi thiếu key, ngân hàng bài (cache envelope),
endpoint tutor-flow cũ ĐÃ BỊ XÓA, skill mới tồn tại.
"""

import base64
import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.persistence.db import ReuseMetric, SessionLocal, SimulationCache, init_db
from app.simulation.dsl.manifest import DSL_VERSION
from app.main import _cache_key, app

client = TestClient(app)

PNG_HEADER = b"\x89PNG\r\n\x1a\n"


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    """Mặc định các test chạy trong trạng thái CHƯA cấu hình key."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def _analyze(text: str):
    return client.post("/api/analyze", json={"input": {"type": "text", "content": text}})


def _docx_b64(paragraphs) -> str:
    from docx import Document

    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["hasKey"] is False


def test_analyze_de_qua_ngan():
    res = _analyze("ngan")
    assert res.status_code == 400
    assert "quá ngắn" in res.json()["error"]


def test_analyze_input_sai_bi_400():
    """Lỗi chuẩn hóa input → 400 với thông điệp tiếng Việt (không phải 500)."""
    # docx giả (không phải zip)
    fake = base64.b64encode(b"khong phai docx").decode()
    res = client.post(
        "/api/analyze", json={"input": {"type": "document", "content": fake, "filename": "x.docx"}}
    )
    assert res.status_code == 400
    # ảnh mime sai
    img = base64.b64encode(PNG_HEADER + b"x").decode()
    res = client.post(
        "/api/analyze", json={"input": {"type": "image", "content": img, "mime_type": "image/gif"}}
    )
    assert res.status_code == 400


def test_analyze_anh_hop_le_thieu_key_bao_503():
    """Ảnh cần key để phiên dịch — chưa có key → 503 (không phải lỗi input)."""
    img = base64.b64encode(PNG_HEADER + b"data").decode()
    res = client.post(
        "/api/analyze", json={"input": {"type": "image", "content": img, "mime_type": "image/png"}}
    )
    assert res.status_code == 503
    assert "GEMINI_API_KEY" in res.json()["error"]


def test_moi_loai_input_di_qua_cung_pipeline(monkeypatch):
    """§1, §6: text/code/docx sau chuẩn hóa đều gọi CHUNG run_pipeline với text."""
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    # Cache key phụ thuộc CACHE_VERSION — dùng version riêng mỗi lần chạy để
    # test tất định (không trúng cache của lần chạy trước), dọn rows ở cuối.
    import uuid

    monkeypatch.setattr(main_module, "CACHE_VERSION", f"test-{uuid.uuid4()}")
    seen: list[str] = []

    async def fake_pipeline(text, api_key, pattern_store=None):
        seen.append(text)
        return {
            "status": "ok",
            "simulation_id": "algorithm.find_max",
            "domain": "algorithm",
            "visual_mode": "2d",
            "title": "t",
            "description": "d",
            "config": {"algorithm_id": "find_max", "data": {"array": [1, 2]}},
            "notes": None,
        }

    monkeypatch.setattr(main_module, "run_pipeline", fake_pipeline)
    init_db()

    # text
    r1 = client.post("/api/analyze", json={"input": {"type": "text", "content": "Tìm max dãy 3 1 2 nhé bạn"}})
    assert r1.status_code == 200
    # code — nội dung được bọc ```python``` nhưng vẫn là text vào pipeline
    r2 = client.post("/api/analyze", json={"input": {"type": "code", "content": "print(max([3,1,2]))", "filename": "a.py"}})
    assert r2.status_code == 200
    assert "```python" in seen[-1]
    # docx
    r3 = client.post("/api/analyze", json={"input": {"type": "document", "content": _docx_b64(["Tìm giá trị lớn nhất trong dãy số."]), "filename": "de.docx"}})
    assert r3.status_code == 200
    assert "Tìm giá trị lớn nhất" in seen[-1]

    assert len(seen) == 3  # cả ba loại đều tới pipeline
    with SessionLocal() as sess:
        for text in seen:
            sess.query(SimulationCache).filter_by(problem_text=text).delete()
        sess.commit()


def test_analyze_thieu_key_bao_huong_dan():
    res = _analyze("Lớp có 40 bạn, tìm bạn điểm cao nhất lớp")
    assert res.status_code == 503
    assert "GEMINI_API_KEY" in res.json()["error"]


def test_analyze_trung_de_lay_envelope_tu_ngan_hang():
    """Cache: đề trùng → envelope từ DB, không đụng Gemini, không cần key."""
    init_db()
    text = "Đề test cache M3: tìm số lớn nhất trong dãy 3; 1; 2 nhé"
    envelope = {
        "status": "ok",
        "simulation_id": "algorithm.find_max",
        "domain": "algorithm",
        "visual_mode": "2d",
        "title": "Tìm max",
        "description": "Dãy 3 số → giá trị lớn nhất",
        "config": {
            "problem": {"summary": "Tìm max", "input": "i", "output": "o"},
            "algorithm_id": "find_max",
            "data": {"array": [3, 1, 2], "labels": None, "target": None, "condition": None, "order": None},
            "data_generated": False,
            "notes": None,
        },
        "notes": None,
        "analysis": {"goal": "Tìm max"},
    }
    key = _cache_key(text)
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(
            key=key, problem_text=text, simulation_id="algorithm.find_max",
            envelope_json=json.dumps(envelope),
            dsl_version=DSL_VERSION, policy_version=main_module.CACHE_VERSION,
        ))
        s.commit()

    res = _analyze(text)
    assert res.status_code == 200
    body = res.json()
    assert body["cached"] is True
    assert body["source"] == "exact_cache"
    assert body["simulation_id"] == "algorithm.find_max"

    # M7.13B: hit phải tăng hit_count + counter exact_cache_hits
    with SessionLocal() as s:
        row = s.query(SimulationCache).filter_by(key=key).first()
        assert row.hit_count == 1
        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()


def test_cache_version_o_cot_lech_la_miss():
    """M7.13B (thay cơ chế M7.9 §7): version lưu ở CỘT thay vì nướng vào key —
    policy_version/dsl_version lệch → lookup MISS (không dùng mù), row vẫn
    nhìn thấy được để dọn/thống kê."""
    from app.main import _cache_lookup

    init_db()
    text = "Đề kiểm version-aware cache M7.13B nhé"
    key = _cache_key(text)
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(
            key=key, problem_text=text, simulation_id="x.y",
            envelope_json="{}", dsl_version=DSL_VERSION, policy_version="phiên-bản-cũ",
        ))
        s.commit()
        assert _cache_lookup(s, key) is None  # policy_version lệch → miss

        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(
            key=key, problem_text=text, simulation_id="x.y",
            envelope_json="{}", dsl_version="0.1", policy_version=main_module.CACHE_VERSION,
        ))
        s.commit()
        assert _cache_lookup(s, key) is None  # dsl_version không hỗ trợ → miss

        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(
            key=key, problem_text=text, simulation_id="x.y",
            envelope_json="{}", dsl_version=DSL_VERSION, policy_version=main_module.CACHE_VERSION,
        ))
        s.commit()
        assert _cache_lookup(s, key) is not None  # version khớp → hit

        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()


def test_cache_version_9_cu_bi_invalidate_sau_bump_10():
    """M13 Task 9: CACHE_VERSION bump "9" → "10" (computation-ownership gate) —
    envelope cache dưới chính sách LUẬT CŨ (policy_version="9", trước khi gate
    tồn tại) không bao giờ được trả lại mù; phải MISS để đề được phân tích lại
    dưới luật mới."""
    from app.main import _cache_lookup

    assert main_module.CACHE_VERSION == "10"
    init_db()
    text = "Đề kiểm invalidate cache sau khi thêm computation-ownership gate (M13)"
    key = _cache_key(text)
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(
            key=key, problem_text=text, simulation_id="generic.rule_scene",
            envelope_json="{}", dsl_version=DSL_VERSION, policy_version="9",
        ))
        s.commit()
        assert _cache_lookup(s, key) is None  # policy_version="9" (luật cũ) → miss

        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()


def test_khong_cache_ket_qua_unsupported(monkeypatch):
    """M7.8 §5: unsupported KHÔNG được cache → tránh kẹt kết quả cũ khi
    năng lực classify/DSL cải thiện."""
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    init_db()
    text = "Đề test không cache unsupported: một bài vượt năng lực hiện tại nhé"

    async def fake_unsupported(t, api_key, pattern_store=None):
        return {"status": "unsupported", "reason": "vượt năng lực"}

    monkeypatch.setattr(main_module, "run_pipeline", fake_unsupported)

    key = _cache_key(text)
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()

    res = _analyze(text)
    assert res.status_code == 200
    assert res.json()["status"] == "unsupported"

    # KHÔNG được lưu vào ngân hàng bài
    with SessionLocal() as s:
        assert s.query(SimulationCache).filter_by(key=key).first() is None


def test_exact_cache_lan_hai_khong_goi_pipeline(monkeypatch):
    """M7.13B case A: cùng đề ok gửi 2 lần → lần 2 exact cache hit, pipeline
    KHÔNG được gọi lại (0 call LLM), counter exact_cache_hits tăng."""
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    import uuid

    monkeypatch.setattr(main_module, "CACHE_VERSION", f"test-{uuid.uuid4()}")
    calls: list[str] = []

    async def fake_pipeline(text, api_key, pattern_store=None):
        calls.append(text)
        return {
            "status": "ok",
            "simulation_id": "algorithm.find_max",
            "domain": "algorithm",
            "visual_mode": "2d",
            "title": "t",
            "description": "d",
            "config": {"algorithm_id": "find_max", "data": {"array": [1, 2]}},
            "notes": None,
            "source": "composed",
        }

    monkeypatch.setattr(main_module, "run_pipeline", fake_pipeline)
    init_db()
    text = "Đề test exact cache M7.13B: tìm max dãy 5 2 8 nhé"

    with SessionLocal() as s:
        before = {r.name: r.count for r in s.query(ReuseMetric).all()}

    r1 = _analyze(text)
    assert r1.status_code == 200 and "cached" not in r1.json()
    r2 = _analyze(text)
    assert r2.status_code == 200
    assert r2.json()["cached"] is True
    assert r2.json()["source"] == "exact_cache"
    assert len(calls) == 1  # lần 2 KHÔNG chạy pipeline

    with SessionLocal() as s:
        after = {r.name: r.count for r in s.query(ReuseMetric).all()}
        assert after.get("exact_cache_hits", 0) == before.get("exact_cache_hits", 0) + 1
        assert after.get("compose_new_count", 0) == before.get("compose_new_count", 0) + 1
        assert after.get("estimated_llm_calls_saved", 0) >= before.get("estimated_llm_calls_saved", 0) + 3
        s.query(SimulationCache).filter_by(key=_cache_key(text)).delete()
        s.commit()


def test_endpoint_tutor_flow_da_xoa():
    """M3 §8: decompose/chat không còn tồn tại — không giữ code chết."""
    assert client.post("/api/decompose", json={"problemText": "x" * 20}).status_code == 404
    assert client.post("/api/chat", json={"message": "hi"}).status_code == 404


def test_explain_cau_hoi_trong():
    res = client.post(
        "/api/explain",
        json={"simulation_id": "algorithm.find_max", "explain_context": {}, "question": "  "},
    )
    assert res.status_code == 400


def test_explain_context_qua_lon():
    res = client.post(
        "/api/explain",
        json={
            "simulation_id": "algorithm.find_max",
            "explain_context": {"blob": "x" * 20000},
            "question": "Vì sao?",
        },
    )
    assert res.status_code == 400
    assert "quá lớn" in res.json()["error"]


def test_explain_context_phai_la_object():
    res = client.post(
        "/api/explain",
        json={"simulation_id": "a.b", "explain_context": [1, 2], "question": "Vì sao?"},
    )
    assert res.status_code == 422  # pydantic từ chối — không phải dict


def test_explain_thieu_key():
    res = client.post(
        "/api/explain",
        json={
            "simulation_id": "algorithm.find_max",
            "explain_context": {"current_step": 3, "array": [1, 2, 3]},
            "question": "Vì sao max chưa đổi?",
            "recent_history": [{"role": "user", "text": "chào"}],
        },
    )
    assert res.status_code == 503
    assert "GEMINI_API_KEY" in res.json()["error"]


def test_bo_skill_moi_ton_tai_skill_cu_da_xoa():
    from app.ai.gemini import SKILLS_DIR, load_skill

    for name in ("analyze", "classify", "simulate", "explain"):
        content = load_skill(name)
        assert len(content) > 200, f"skill {name} quá ngắn"
    # Skill tutor-flow cũ không còn file
    assert not Path(SKILLS_DIR / "decompose.md").exists()
    assert not Path(SKILLS_DIR / "tutor.md").exists()
    # explain không được điều khiển mô phỏng, không step_status
    explain = load_skill("explain")
    assert "KHÔNG điều khiển" in explain
    assert "step_status" not in explain
    # analyze mô tả đúng bản chất hệ thống, không còn 'gia sư'
    analyze = load_skill("analyze")
    assert "mô phỏng tương tác 2D/3D" in analyze
    assert "gia sư" not in analyze.lower()


def test_explain_schema_khong_co_step_status():
    from app.ai.explain import EXPLAIN_SCHEMA

    assert "step_status" not in json.dumps(EXPLAIN_SCHEMA)
    assert list(EXPLAIN_SCHEMA["properties"].keys()) == ["reply"]
