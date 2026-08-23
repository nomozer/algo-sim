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

    async def fake_pipeline(text, api_key, pattern_store=None, **kw):
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

    # M17 W2B-PATCH (bump 19→20): hợp đồng simulate của truy vấn bảng đổi LUẬT
    # (marker ô trống, cột nullable, đòi ĐỦ TẦNG pipeline). Envelope cache sinh
    # dưới luật cũ có thể là spec THIẾU TẦNG — phải MISS để phân tích lại.
    # M17 W2C (bump 20→21): thêm family/target AI-reachable
    # `algorithm.bounded_control_flow` + enum analyze mới ⇒ chính sách classify
    # đổi, envelope cache dưới luật cũ phải MISS để đề được định tuyến lại.
    # M17 W3-LIVE-C1 (bump 23→24): CÙNG LÝ DO — enum `prescribed_procedure` nay
    # splat từ taxonomy nên analyze phát thêm được
    # `positional_representation.character_code_mapping`. Refusal vốn KHÔNG được
    # cache, nhưng envelope OK sinh dưới enum cũ có thể mang target kém phù hợp
    # (mã hoá ký tự từng chỉ lọt khi analyze tình cờ trả "none") ⇒ phải MISS.
    # M17 W3-LIVE-C2 (bump 24→25): `analyze.md` thêm luật phát cho họ positional
    # (quyết theo HÌNH DẠNG ĐẦU VÀO: ký tự ↔ số) và cho bounded_control_flow.
    # Chính sách analyze đổi ⇒ envelope OK sinh dưới luật cũ có thể mang target
    # kém phù hợp (đề mã hoá ký tự từng bị định tuyến theo cơ chế đổi cơ số).
    # W4B-3F (bump 26→27): hợp đồng config của `web.style_model` đổi HÌNH DẠNG —
    # `content` (một khối chữ) thành `heading` + `paragraph`, kèm hai thuộc tính
    # `headingColor`/`headingSize`. Đây là bề mặt LLM điền, nên envelope cache
    # sinh dưới hợp đồng cũ KHÔNG còn validate được; phải MISS để đề được phân
    # tích lại. Lý do đổi: một khối chữ không có tổ tiên/anh em nên bài HTML/CSS
    # không có gì để nói về quan hệ thẻ ↔ hiển thị.
    # W4B-2Z (bump 25→26): thêm family/target AI-reachable `web.style_model` +
    # phơi `web_presentation.*` vào enum `prescribed_procedure` và
    # `requested_operations` ⇒ chính sách định tuyến đổi. Envelope OK sinh dưới
    # luật cũ mang đúng những đề CSS đã bị `generic.rule_scene` nuốt — trả lại
    # mù thì bản sửa định tuyến này vô hiệu với chính các đề nó nhắm tới.
    # M20 W3 (bump 27→28): `analyze.md` + `ANALYZE_SCHEMA` thêm HAI trường bắt
    # buộc `domain_scope`/`simulatability`, và một cổng TẤT ĐỊNH mới đọc chúng
    # để từ chối đề ngoài môn hoặc đề không có cơ chế để mô phỏng. Envelope cache
    # sinh dưới luật cũ ra đời khi phán quyết phạm vi còn do LLM sở hữu — đúng
    # những đề cổng này nhắm tới lại là đúng những đề đã lọt và đã được cache.
    # Trả lại mù thì bản vá vô hiệu với chính chúng.
    # M20 W5 (bump 28→29): miền màu của `web.style_model` nới từ BẢY ô đóng sang
    # mọi mã hex 6 chữ số. Đây là bề mặt LLM ĐIỀN, nên envelope cache sinh dưới
    # luật cũ mang đúng những đề mà bản nới này nhắm tới — đề CSS/màu vốn chỉ
    # chọn được trong bảng. Trả lại mù thì học sinh vẫn nhận bản bảy-ô.
    # M20 (bump 29→30): schema web đưa cho LLM nay phơi thêm hai trường kiểu
    # chữ TIÊU ĐỀ — `headingSize`/`headingColor`. Validator và UI đã nhận chúng
    # từ W4B-3F, riêng schema thì bị bỏ quên, nên mọi bài CSS do AI sinh không
    # bao giờ nói được về kiểu của `<h1>` — mất đúng bài học phân cấp mà bản mẫu
    # dựng ra để dạy. Đây là bề mặt LLM ĐIỀN, nên envelope cache sinh dưới schema
    # cũ mang đúng những đề mà bản vá này nhắm tới; trả lại mù thì bản vá vô hiệu.
    # M20 (bump 30→31): schema web đưa cho LLM vẫn mô tả hợp đồng CŨ `content`,
    # trong khi validator đã chuyển sang `heading` + `paragraph` từ W4B-3F và
    # fail-closed với khoá lạ ⇒ MỌI spec web do AI sinh đều bị từ chối, tức
    # `web.style_model` không tới được qua đường sinh. Envelope cache sinh dưới
    # schema cũ mang đúng những đề mà bản vá này nhắm tới; trả lại mù thì vá vô hiệu.
    # W5A (bump 31→32): thêm family-member/target AI-reachable `color.rgb_model`
    # + phơi `positional_representation.rgb_channel_composition` vào enum
    # `prescribed_procedure` kèm luật phát trong `analyze.md` ⇒ chính sách định
    # tuyến đổi. Envelope OK sinh dưới luật cũ mang đúng những đề màu RGB đã bị
    # `generic.rule_scene` nuốt (dựng thành các bước hé lộ thay vì ba kênh trộn
    # được) — trả lại mù thì bản sửa định tuyến này vô hiệu với chính các đề nó
    # nhắm tới.
    # 33 (2026-08-20): `semantic_program.md` viết lại + `stage_semantic_program`
    # — bề mặt LLM đổi nên analysis cache cũ không còn đáng tin dưới luật mới.
    # 34 (2026-08-21): route ngữ nghĩa NỐI vào `run_pipeline` + thêm
    # `stage_semantic_analyze`. Chính sách định tuyến đổi thật: đề `algorithmic`
    # trước bị `computation_gate` từ chối, nay qua được `execution_authority_gate`
    # — envelope/analysis cache dưới luật cũ mang đúng lớp bài bị từ chối oan.
    # 35 (2026-08-23, vNext): route ngữ nghĩa nay THỰC SỰ được nối vào đường sản
    # phẩm — `main.py` trước đó gọi `run_pipeline` mà KHÔNG truyền
    # `semantic_route`, nên tham số rơi về mặc định `"off"` và
    # `stage_semantic_program` chưa từng chạy cho một người dùng thật. Chính sách
    # định tuyến đổi ở đúng nghĩa đen của nó. Envelope cache sinh dưới luật cũ là
    # kết quả của đường KHÔNG có route sinh — trả lại mù thì bản sửa này vô hiệu
    # với chính những đề nó nhắm tới (bài thuật toán rơi xuống
    # `generic.rule_scene` rồi hiện narration chạy trên hình đứng yên).
    # 36 (2026-08-23, vNext): prompt `semantic_program.md` thêm luật `container`
    # phải là TÊN vùng nhớ đã khai. Probe E2E sau khi bật `serve` bắt được LLM
    # viết `container: {"kind":"literal","value":"([{"}` — tham chiếu một vùng
    # nhớ chưa khai, nên chương trình bị Pydantic vứt trước mọi tầng ngữ nghĩa.
    # Đổi prompt mà không bump thì đề cũ vẫn trả chương trình sinh dưới prompt
    # cũ, và bản sửa đọc như không ăn thua.
    assert main_module.CACHE_VERSION == "36"
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

    async def fake_unsupported(t, api_key, pattern_store=None, **kw):
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

    async def fake_pipeline(text, api_key, pattern_store=None, **kw):
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
