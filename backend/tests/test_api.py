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
    # 37: schema `analyze` ngữ nghĩa đổi hai chỗ — taxonomy thêm
    # `predicate_verdict`/`scalar_accumulation`, và `pred` thành ENUM vị từ kiểm
    # được. Live 24/08 cho thấy đề chuỗi ngoặc `executable=True` rồi rơi mức yếu
    # chỉ vì thiếu `pred`: trường ấy là chuỗi tự do nên mô hình chưa từng biết có
    # vị từ nào để gọi. Không bump thì phân tích cache theo schema cũ vẫn về
    # không kèm `pred`, và bản sửa đọc như không ăn thua.
    # 38: MIỀN HÌNH HỌC KHÔNG GIAN (đổi đề tài, `STATUS_LEDGER §0-2026-08-24`).
    # IR mở 6 `MemoryType` + 5 biểu thức + 3 câu lệnh dựng, và **thẻ văn phạm
    # dẫn xuất từ contract nên nó đi thẳng vào user message** — tức bề mặt prompt
    # đã đổi. Không bump thì mọi đề đã phân tích trả về envelope sinh dưới từ
    # vựng CŨ, nơi `point3`/`plane3` chưa tồn tại, và bản mở IR đọc như không ăn
    # thua.
    # 39: bề mặt `analyze` nay CÓ MIỀN — bài hình học đi qua `geometry_analyze.md`
    # với enum 8 nghĩa vụ, thay vì `semantic_analyze.md` với enum 19. Phase 5
    # (2026-08-24) đo được cái giá của việc không tách: 3/6 chương trình hình học
    # HỢP LỆ khai nghĩa vụ TIN HỌC — `derived_sequence` cho một bài hỏi
    # `point_on_line`, `structural_traversal` cho một bài hỏi `coplanar`. Không
    # bump thì đề hình học đã phân tích vẫn trả hợp đồng khai dưới enum cũ, và
    # bản tách miền đọc như không ăn thua ngay trên chính các đề nó nhắm tới.
    # 40: `geometry_analyze.md` đổi nội dung — gỡ một RÒ RỈ ĐÁP ÁN. Ví dụ cho
    # `params.value` viết "biết rằng thể tích bằng 2/3", mà `2/3` đúng là đáp án
    # `geo_09`/`geo_10`, và nó đứng ngay cạnh câu dạy mô hình khi nào được điền
    # đáp số. Bump theo nghĩa đen của luật (đổi `skills/*.md` ⇒ bump), không vì
    # có cache cần dọn — v39 chưa từng chạy live.
    # 41: mô tả `container`/`witness` trong schema `analyze` nay THEO MIỀN. Bản
    # cũ bắt snake_case cho cả hai — đúng ở Tin học, sai ở hình học (điểm gọi
    # bằng CHỮ HOA). `geo_01` ở Phase 5.5: hợp đồng `witness='m'`, chương trình
    # `M`, C₁a từ chối, và cả hai lượt LLM đều làm ĐÚNG luật được giao. Mô tả
    # trường đi thẳng vào structured output nên nó LÀ bề mặt prompt; không bump
    # thì đề đã phân tích vẫn trả `witness` hạ chữ thường.
    # 42: định tuyến MIỀN nối vào đường sản phẩm — `domain` đi xuống cả hai lượt
    # LLM của route sinh, và `stage_semantic_program` thôi viết cứng tên skill.
    # Khác mọi bump trước ở một điểm: lần này CÓ cache thật cần dọn. Đề hình học
    # nào đã gửi qua sản phẩm đều đang mang sẵn một lời từ chối "ngoài danh mục"
    # trong bảng cache; không bump thì học sinh gửi lại vẫn nhận đúng lời ấy và
    # bản vá đọc như không ăn thua ngay trên chính các đề nó nhắm tới.
    # 43: IR thêm `intersect_line_line`. Thẻ văn phạm sinh từ `contract.py` nên
    # bề mặt prompt đổi mà không file `.md` nào bị sửa — ca dễ quên nhất của luật
    # bump, vì thay đổi nằm ở một model Pydantic.
    # 44: `detect_domain` nhận thêm mệnh đề phủ quyết bằng từ vựng Tin học. Đây
    # là POLICY ĐỊNH TUYẾN — cùng một đề nay có thể đi sang miền khác, nên mọi
    # envelope cache dưới bộ dò cũ đều không còn định danh được bản đã sinh ra
    # nó. Đo được: 4/5 đề Tin học hợp lệ có mượn từ vựng hình học từng bị kéo
    # sang route hình học rồi trả về "ngoài danh mục" — tức bản vá này ĐỔI KẾT
    # QUẢ cho những đề ấy, đúng ca mà bump tồn tại để dọn.
    # 45: IR thêm `construct_polygon` (Phase 6.6). Thẻ văn phạm sinh từ
    # `contract.py` ⇒ bề mặt prompt đổi mà không file `.md` nào bị sửa.
    # 46: `ConstructPointStmt.expr` thu hẹp xuống `PointExpr`; thẻ văn phạm gọi
    # trường ấy là "phép dựng ĐIỂM" ⇒ bề mặt prompt đổi.
    # 47: `geometry_program_generator.md` thêm luật XUẤT XỨ ĐẦY ĐỦ cho mọi
    # điểm khai toạ độ, cộng một bước tự soát trước khi trả lời. Đo được ở
    # CONFIRMATION_V2: 6/10 chi tiết grounding là "có initial_value nhưng
    # thiếu source_fact_id" trên các đỉnh DẪN XUẤT (C, D, B', C', D', S) —
    # mô hình khai `model_assumption` cho hai đỉnh đầu rồi quên phần còn lại.
    # Prompt đổi ⇒ đề cũ trong cache sẽ trả chương trình sinh bằng bản prompt
    # cũ, tức đo nhầm bản.
    # 48: CHUẨN HOÁ THANG (`scale_normalization.py`). `build_request_contract`
    # nay viết lại dữ kiện hình học `AB = a`, `SA = 4a/5` thành `1`, `4/5`
    # TRƯỚC khi mô hình nhìn thấy hợp đồng, và khối dữ kiện trong prompt khai
    # thẳng `a = 1` là do SERVER chốt. Không file `.md` nào bị sửa nhưng đầu
    # vào của lượt sinh chương trình đổi hẳn — cache cũ sẽ trả chương trình
    # viết dưới thang mô hình TỰ chọn (đã quan sát: `a = 25`), tức đo nhầm bản.
    # 49: THẨM ĐỊNH TĨNH vào vòng sửa (`ir_static_check`). Lỗi toán hạng —
    # điểm chưa dựng, `ratio` `2:1`, sai kiểu — trước đây chết ở kernel SAU khi
    # vòng sửa đã đóng, nên mô hình không bao giờ được biết. Nay chúng thành
    # một lời từ chối gửi ngược, tức LƯỢT SINH THỨ HAI nhận prompt khác hẳn.
    # Cache cũ sẽ trả chương trình của bản chưa có đường phản hồi ấy.
    # 50: P0 `NormalizedSourceInvariantGate` — cổng MỚI giữa C₁b và C₂, kiểm
    # hình dựng ra có thoả DỮ KIỆN đề cho không (`AB = 1`, `SA = 4/5`), bất kể
    # chương trình có gắn `source_fact_id` hay không. Đây là đổi CHÍNH SÁCH
    # ĐỊNH TUYẾN: cùng một đề, một chương trình từng được phục vụ nay có thể
    # bị từ chối. Envelope cache sinh dưới luật cũ sẽ được trả lại mà KHÔNG
    # đi qua cổng — đúng ca bump tồn tại để dọn.
    # 51: MỞ NĂNG LỰC — `distance` nay đo được đường×đường (chéo/song song/
    # cắt), đường×mặt và mặt×mặt. Kernel đã có phép tính từ đầu; wave này nối
    # cầu. Đề "khoảng cách giữa hai đường chéo nhau" TỪNG chết ở
    # `GEOMETRY_OPERAND_TYPE` nay chạy tới một con số — tức cùng một đề, cùng
    # một prompt, mà phán quyết ĐỔI. Envelope cache cũ giữ lời từ chối của bản
    # chưa có cầu nối, và trả lại nó là nói rằng hệ vẫn không làm được.
    # 52: THIẾT DIỆN thành kết quả HẠNG NHẤT — thêm kiểu bộ nhớ `section`
    # (schema đổi, tức prompt mô hình đọc đổi) và nghĩa vụ thứ chín
    # `section_matches` (menu classify đổi). Đề thiết diện sinh dưới luật cũ
    # khai thiết diện là `polygon3` và chỉ được kiểm bằng `coplanar` — phép
    # kiểm gần như luôn xanh. Trả lại envelope ấy là phục vụ một chương trình
    # chưa từng đi qua cổng mới, đúng ca bump tồn tại để dọn.
    # 53: HỢP ĐỒNG WITNESS — `witness` nay NULLABLE, và schema analyze có thêm
    # `solid`/`plane`. Cả hai đổi thứ MÔ HÌNH NHÌN THẤY, nên envelope cache cũ
    # sinh dưới schema chật hơn: ở đó "nghĩa vụ không có witness" là câu không
    # nói được (lượt live geo_03 cho ra chuỗi "null"), và `section_matches`
    # không có đường phát hai toán hạng nên checker mạnh nhất của miền hình học
    # chưa từng chấm được lần nào. Trả lại envelope ấy là phục vụ một hợp đồng
    # đã biết là biểu diễn thiếu.
    # 54: PROMPT SINH HÌNH HỌC ĐỔI LUẬT. Bản cũ dạy *"gặp a√2 thì chọn hệ toạ
    # độ khác cho nó thành hữu tỉ"* — đúng khi miền số chỉ có ℚ, và SAI từ khi
    # `EXACT_RADICAL_SUPPORT` đóng: nó dạy mô hình NÉ những đề mà hệ nay trả
    # lời được chính xác. Thêm `angle_cos` + `vector_from_points` vào bảng đại
    # lượng cũng đổi thứ mô hình nhìn thấy. Envelope cache sinh dưới prompt cũ
    # mang dấu vết của một hệ hẹp hơn hệ hiện tại ⇒ phải MISS.
    # 55: BỀ MẶT TỔNG HỢP ĐỔI. Thêm `declare_point` (khai điểm gốc ngay trong
    # dòng chương trình) và `vector_from_points`; thẻ văn phạm nay giới thiệu
    # cả hai, và prompt dạy dùng chúng. Envelope cache sinh dưới bề mặt cũ đến
    # từ một hệ mà mô hình KHÔNG CÓ TỪ để khai điểm gốc — 3/4 ca live đốt trọn
    # lượt tổng hợp đầu tiên vì đúng chỗ ấy. Trả lại envelope ấy là phục vụ một
    # hợp đồng đã biết là chật.
    # 56: BỀ MẶT TỔNG HỢP ĐỔI LẦN NỮA, và lần này là SỬA HAI CHỖ TA NÓI SAI.
    # ① Thẻ văn phạm giới thiệu `construct_plane.through` là `[x,y,z]` toạ độ
    # trong khi trường ấy nhận TÊN ba điểm — tức ta dạy mô hình viết đúng thứ
    # cổng trung thực năng lực vừa dựng để chặn. ② Bảng prompt gắn chữ "nhị
    # diện" cạnh `angle_cos`, và tên phép đo tự nó chứa "cos", nên đề hỏi
    # "côsin" là mô hình chọn nó bất kể toán hạng là đường thẳng — 14 lượt
    # hỏng / 220.898 token trong AUDIT. Thẻ nay còn THEO MIỀN: đề hình học
    # không thấy IR Tin học nữa. Envelope cache sinh dưới bề mặt cũ đến từ một
    # hệ dạy sai kiểu; trả lại mù là phục vụ đúng lỗi đó.
    # 57: ĐỔI KẾT QUẢ, không chỉ đổi lời. `angle_cos_sq` từng mang HAI đại
    # lượng — cos² cho ba cặp toán hạng, sin² cho cặp (đường, mặt) — và bộ
    # chấm mang bản sao của chính lỗi ấy nên không bắt được. Nay cos² ở cả bốn
    # cặp. Cùng một JSON của `fp_5` cho 1/3 trước và 2/3 sau, nên envelope
    # cache sinh dưới luật cũ mang một số đo SAI ĐẠI LƯỢNG, không phải một số
    # đo cũ. Trả lại mù là phục vụ đúng con bug vừa sửa.
    # 58: thẻ hình học GIẤU MẤT `construct_point` suốt nhiều wave — nó dẫn từ
    # `_TOAN_HANG_LENH`, bảng cố ý không chứa câu lệnh ấy (toán hạng của nó
    # nằm trong `expr`). Mô hình dựng mọi điểm phụ bằng `assign`, lối DUY NHẤT
    # nó thấy, rồi chết ở runtime. Nay thẻ dẫn từ `_KIEU_DUNG`, và `assign`
    # hình học được chuẩn hoá thành dạng chuẩn tắc trước khi chạy. Envelope
    # cache sinh dưới thẻ cũ đến từ một hệ thiếu một câu lệnh.
    assert main_module.CACHE_VERSION == "58"
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


def test_ghi_de_cache_cu_sau_bump_KHONG_vo_khoa(monkeypatch):
    """Đề ĐÃ TỪNG phân tích, gặp `CACHE_VERSION` mới ⇒ phải ghi đè, không 500.

    LỖI THẬT, CÂM SUỐT NHIỀU LẦN BUMP: tra cứu trượt vì `policy_version` khác,
    nhánh ghi lại tìm thấy hàng cũ theo `key` và `session.delete(...)` rồi
    `session.add(...)` trong CÙNG một flush — SQLAlchemy phát INSERT **trước**
    DELETE, nên đụng `UNIQUE(key)`. Người dùng nhận 500 cho đúng những đề họ đã
    xem trước đó.

    Không lộ ra suốt thời gian dài vì test luôn chạy trên DB sạch; nó chỉ hiện
    khi DB còn hàng của lần bump trước. Test này DỰNG LẠI đúng tình huống ấy.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    init_db()
    text = "Đề đã từng phân tích ở phiên bản cache cũ, nay gặp bump mới"
    key = _cache_key(text)

    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(
            key=key, problem_text=text, simulation_id="generic.rule_scene",
            envelope_json='{"status":"ok"}', dsl_version=DSL_VERSION,
            policy_version="1",  # phiên bản CŨ ⇒ tra cứu sẽ trượt
        ))
        s.commit()

    async def fake_ok(t, api_key, pattern_store=None, **kw):
        return {"status": "ok", "simulation_id": "generic.rule_scene",
                "config": {"objects": [], "frames": []}, "source": "composed"}

    monkeypatch.setattr(main_module, "run_pipeline", fake_ok)
    res = client.post("/api/analyze",
                      json={"input": {"type": "text", "content": text}})
    assert res.status_code == 200, res.text

    with SessionLocal() as s:
        rows = s.query(SimulationCache).filter_by(key=key).all()
        assert len(rows) == 1, "phải còn ĐÚNG một hàng — ghi đè, không nhân bản"
        assert rows[0].policy_version == main_module.CACHE_VERSION
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
