# -*- coding: utf-8 -*-
"""E2E HÌNH HỌC QUA ĐƯỜNG SẢN PHẨM THẬT, biên LLM mock. **0 API call.**

Cùng khuôn `tests/test_mocked_production_e2e.py`, cùng lý do: mọi thứ sau LLM là
tất định, nên nếu chúng hỏng thì tiêu quota live chỉ để phát hiện lại điều đã
biết. Đường đi là ĐƯỜNG THẬT, không tắt đoạn nào:

    POST /api/analyze → main.py → run_pipeline → _semantic_shadow
    → detect_domain → geometry_analyze → geometry_program_generator
    → validator → interpreter → C₁a/C₁b/C₂ → compile → Scene3D → envelope

Chỉ `call_gemini` bị thay, và nó trả về **IR hình học THẬT** mà mô hình đã sinh
ở lượt Wave 4 — không phải một spec tôi viết cho vừa test.

─── HAI ĐIỀU FILE NÀY KHOÁ MÀ KHÔNG FILE NÀO KHÁC KHOÁ ────────────────────

① Đề hình học đi qua **hai skill hình học**, không phải hai skill Tin học.
② Nó sống sót `domain_scope: OUT_OF_SCOPE` — nhãn mà `analyze.md` **buộc** mô
  hình phải chọn cho một đề hình học, vì enum của nó không có giá trị nào khác.

GIỚI HẠN PHẢI ĐỌC KÈM: mock trả về chương trình ĐÃ BIẾT LÀ ĐÚNG, nên tầng này
KHÔNG nói gì về việc LLM có sinh nổi chương trình ấy không — Wave 4 đo được
4/10. Nó chỉ nói: nếu LLM sinh đúng, sản phẩm sẽ phát ra cảnh 3D xem được.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.evaluation.m16_offline_scripts import _analysis

W4 = json.loads(
    (Path(__file__).resolve().parents[3] / "docs" / "evaluation" / "geometry"
     / "dev-results-w4" / "geometry_dev_results.json").read_text(encoding="utf-8"))

#: `geo_09` — thể tích khối chóp. Chọn nó vì ở Wave 4 nó đi TRỌN đường
#: (`executable` + oracle PASS), nên mọi thứ test này thấy đều là hành vi thật.
CASE = next(c for c in W4["cases"] if c["case_id"] == "geo_09")


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    monkeypatch.setenv("SEMANTIC_ROUTE_MODE", "serve")
    from app import main as main_module
    from app.main import app

    # CACHE_VERSION RIÊNG mỗi test — cùng khuôn `tests/test_api.py`.
    #
    # Không có nó thì test đầu tiên phân tích đề này rồi GHI VÀO CACHE, và mọi
    # test sau nhận lại envelope cũ mà **không gọi LLM lần nào** — nên phép kiểm
    # "đã dùng skill nào" thấy một danh sách rỗng và đỏ vì lý do sai. Tệ hơn:
    # cache là SQLite trên đĩa, nên nó sống qua cả các lượt `pytest` khác nhau,
    # và test sẽ xanh/đỏ tuỳ vào chuyện lượt trước đã chạy gì.
    monkeypatch.setattr(main_module, "CACHE_VERSION", f"test-{uuid.uuid4()}")
    return TestClient(app)


def _kich_ban() -> list[str]:
    """4 lượt, ĐÚNG THỨ TỰ THẬT: analyze · semantic_analyze · semantic_program
    · classify.

    `analyze` khai `OUT_OF_SCOPE` **có chủ đích** — đó là nhãn mà một mô hình
    trung thực buộc phải chọn cho đề hình học, vì `analyze.md` chỉ cho bốn giá
    trị và không giá trị nào là hình học không gian.
    """
    a = _analysis(goal="Tính thể tích khối chóp", ownership="algorithmic")
    a["domain_scope"] = "OUT_OF_SCOPE"
    return [
        json.dumps(a),
        json.dumps(CASE["request_contract"]),
        json.dumps(CASE["generated_program"]),
        # Catalog KHÔNG có target hình học — đây đúng là câu trả lời đã đẩy đề
        # của học sinh xuống "NGOÀI DANH MỤC MÔ PHỎNG".
        json.dumps({"status": "unsupported", "simulation_id": None,
                    "reason": "Bài này chưa có mô phỏng phù hợp trong danh mục."}),
    ]


def _fake(responses: list[str], da_dung: list[str]):
    """Mock biên LLM + GHI LẠI tên skill mỗi lượt.

    Ghi tên skill ở đây chứ không patch `load_skill`: cái chạy thật là chuỗi
    prompt đi vào `call_gemini`, và đó mới là thứ quyết định mô hình đọc luật
    nào. Patch `load_skill` rồi khẳng định nó được gọi đúng là kiểm lời gọi, chứ
    chưa kiểm rằng lời gọi ấy có tới nơi.
    """
    async def f(api_key, system_prompt, user_text, response_schema=None,
                temperature=0.2, image=None):
        da_dung.append(system_prompt)
        # Hết kịch bản ⇒ lặp lại lượt cuối. `classify_with_one_route_recovery`
        # có thể gọi thêm một lượt, và một `assert` ở đây sẽ đỏ vì lý do sai.
        return responses.pop(0) if responses else responses_cuoi[0]

    responses_cuoi = [responses[-1]]
    return f


def _goi(client) -> tuple[dict, list[str]]:
    da_dung: list[str] = []
    with patch("app.ai.pipeline.call_gemini", _fake(_kich_ban(), da_dung)):
        res = client.post("/api/analyze", json={
            "input": {"type": "text", "content": CASE["problem"]}})
    assert res.status_code == 200, res.text
    return res.json(), da_dung


# ══ ① HAI SKILL HÌNH HỌC, KHÔNG PHẢI HAI SKILL TIN HỌC ═══════════════════
def test_de_hinh_hoc_dung_dung_hai_prompt_hinh_hoc(client):
    """Trước bản vá: `stage_semantic_analyze` không nhận `domain` và
    `stage_semantic_program` viết cứng `load_skill("semantic_program")`, nên đề
    hình học được ĐỌC và VIẾT bằng luật Tin học.

    ─── SIẾT LẠI SAU GEOMETRY_PRODUCT_CUTOVER (2026-09-01) ────────────────

    Bản trước khẳng định `da_dung[1]` và `da_dung[2]` — tức chấp nhận rằng ô số
    **0** là một prompt Tin học (`analyze.md`), vì đường cũ chạy `stage_analyze`
    trước rồi hình học mới là nhánh shadow. Nay hình học là đường CHÍNH, nên
    phép kiểm đúng là **ĐÚNG HAI prompt, cả hai đều hình học, không có ô số 0**.

    Đây là siết, không phải nới: mọi khẳng định cũ vẫn đúng và có thêm một
    khẳng định mới — không một lượt LLM Tin học nào được tiêu cho đề hình học.
    """
    from app.ai.pipeline import load_skill

    _, da_dung = _goi(client)
    assert da_dung[0] == load_skill("geometry_analyze"), (
        "lượt ĐẦU TIÊN phải là đọc đề HÌNH HỌC — không còn ô số 0 nào cho "
        "`analyze.md` Tin học")
    # Các lượt sau đều là tổng hợp (có thể lặp vì vòng sửa) — và KHÔNG lượt nào
    # được là prompt Tin học.
    assert set(da_dung[1:]) == {load_skill("geometry_program_generator")}


def test_KHONG_dung_prompt_Tin_hoc_cho_de_hinh_hoc(client):
    from app.ai.pipeline import load_skill

    _, da_dung = _goi(client)
    for cam in ("semantic_analyze", "semantic_program"):
        assert load_skill(cam) not in da_dung[1:3], cam


# ══ ② SỐNG SÓT `OUT_OF_SCOPE` — VÀ ĐÓ LÀ CHỖ ĐỀ THẬT ĐÃ CHẾT ════════════
def test_envelope_ra_OK_chu_khong_phai_ngoai_danh_muc(client):
    body, _ = _goi(client)
    assert body["status"] == "ok", body.get("reason")
    assert body["simulation_id"] == "generic.semantic_program"


def test_classifier_TU_CHOI_van_khong_phu_quyet_duoc_route_sinh(client):
    """Kịch bản cho classify trả `unsupported` — đúng câu trả lời đã đẩy đề của
    học sinh xuống "NGOÀI DANH MỤC". Route sinh phải thắng nó."""
    body, _ = _goi(client)
    assert "danh mục" not in (body.get("reason") or "")


# ══ CẢNH 3D TỚI ĐƯỢC ENVELOPE ════════════════════════════════════════════
def test_envelope_mang_scene3d_co_doi_tuong(client):
    body, _ = _goi(client)
    canh = body.get("scene3d")
    assert canh, "chương trình hình học chạy trọn mà envelope không có cảnh"
    assert canh["objects"], canh
    assert canh["events"], "không có sự kiện thì không có gì để phát lại"


def test_canh_dung_loai_render_dong_cua_hop_dong(client):
    from app.simulation.semantic_program.scene3d import RENDER_HINT

    body, _ = _goi(client)
    for o in body["scene3d"]["objects"]:
        assert o["render"] in set(RENDER_HINT.values()), o


def test_khung_2D_van_con_nguyen_ben_canh_canh_3D(client):
    """Cảnh 3D đi KÈM envelope, không thay nó — đường 2D cũ phải nguyên vẹn."""
    body, _ = _goi(client)
    assert len(body["config"]["frames"]) > 1
    assert all((f.get("narration") or "").strip()
               for f in body["config"]["frames"])


def test_khong_ro_dinh_danh_ky_thuat_len_be_mat_hoc_sinh(client):
    from app.simulation.semantic_program.learner_surface import _ro_ri

    body, _ = _goi(client)
    assert _ro_ri({"config": {"frames": body["config"]["frames"]}}) == []
