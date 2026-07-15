# -*- coding: utf-8 -*-
"""M10-AI-ROUTE — định tuyến NL cho network.protocol_encapsulation (mock, offline).

Khóa các bất biến:
- Backend CATALOG biết module encapsulation (trước đây frontend-only — M10 deferred);
- classify ĐƯỢC PHÉP trả id này (enum schema dẫn xuất từ CATALOG — anti-pattern #1:
  schema viết tay từng làm Gemini KHÔNG THỂ phát primitive mới);
- validator chỉ nhận bề mặt config v1 nhỏ (payloadLabel/appProtocol/notes) —
  LLM KHÔNG sở hữu tầng/PDU/timeline (R0);
- menu classify (catalog_text) MANG sự phân biệt ngữ nghĩa:
  đường đi qua nút (packet_routing) ↔ biến đổi PDU qua tầng (encapsulation) —
  phân biệt nằm ở DATA đưa vào prompt, không hard-code keyword trong code runtime.
"""

import json

import asyncio

from app.ai import pipeline
from app.simulation.catalog import CATALOG, catalog_text
from app.validation.simulation import validate_encapsulation_config

ENCAP_ID = "network.protocol_encapsulation"

NET_ANALYSIS = {
    "objects": ["dữ liệu ứng dụng", "các tầng TCP/IP", "máy gửi", "máy nhận"],
    "data": [],
    "relations": [{"description": "dữ liệu đi qua từng tầng"}],
    "processes": ["đóng gói qua các tầng", "truyền", "tháo gói"],
    "constraints": [],
    "goal": "Quan sát dữ liệu được đóng gói qua các tầng TCP/IP rồi truyền tới máy nhận",
    "input_description": "Mô tả quá trình gửi dữ liệu",
    "output_description": "Diễn biến đóng gói/tháo gói theo tầng",
    "notes": None,
}


def _fake_gemini(responses: list[str]):
    calls: list[dict] = []

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2):
        calls.append({"system": system_prompt, "user": user_text, "schema": response_schema})
        if not responses:
            raise AssertionError("fake Gemini bị gọi nhiều hơn số response chuẩn bị")
        return responses.pop(0)

    return fake, calls


# ── 1. Đăng ký catalog ────────────────────────────────────────

def test_catalog_dang_ky_encapsulation():
    assert ENCAP_ID in CATALOG
    spec = CATALOG[ENCAP_ID]
    assert spec.domain == "network"
    props = spec.config_schema["properties"]
    # Bề mặt v1 NHỎ đúng như frontend engine (encap.ts): 3 field, đều optional
    assert set(props) == {"payloadLabel", "appProtocol", "notes"}
    # Hợp đồng phải nói rõ engine sở hữu diễn biến (R0)
    assert "engine" in spec.contract
    assert "KHÔNG" in spec.contract


def test_classify_schema_enum_co_encapsulation():
    """Enum simulation_id trong structured output DẪN XUẤT từ CATALOG —
    thiếu là Gemini không thể phát id mới dù prompt cho phép."""
    enum = pipeline._classify_schema()["properties"]["simulation_id"]["enum"]
    assert ENCAP_ID in enum
    assert "network.packet_routing" in enum  # module cũ còn nguyên


def test_classify_skill_phan_biet_encapsulation():
    """Live smoke 2026-07-16 (5 case m10_route, 2/5 đúng) chứng minh: quy tắc
    "step_by_step → generic" của classify.md nuốt đề đóng gói, và đề TCP nâng
    cao bị ép về generic. classify.md phải mang quy tắc ngữ nghĩa (khuôn 3b):
    - biến đổi PDU qua tầng → network.protocol_encapsulation, KỂ CẢ khi đề tả
      tiến trình từng bước (engine chuyên biệt TỰ dựng tiến trình);
    - chi tiết động của giao thức (bắt tay/seq-ACK/retransmission/congestion)
      → unsupported, KHÔNG ép về generic."""
    from app.ai.gemini import load_skill

    c = load_skill("classify")
    assert "network.protocol_encapsulation" in c
    assert "bắt tay" in c  # giới hạn v1: protocol động → unsupported
    # tiến trình do engine chuyên biệt tự dựng ≠ dựng cảnh từng bước
    assert "tự dựng" in c or "TỰ DỰNG" in c


def test_catalog_text_mang_phan_biet_hai_module_mang():
    """Menu classify phải mang sự phân biệt: đường đi qua nút ↔ biến đổi PDU
    qua tầng, và nêu giới hạn v1 (không bắt tay TCP/congestion...)."""
    text = catalog_text()
    assert ENCAP_ID in text
    spec = CATALOG[ENCAP_ID]
    # encap: nói về tầng + đóng gói, và chỉ sang packet_routing cho bài đường đi
    assert "tầng" in spec.description
    assert "network.packet_routing" in spec.description
    # nêu giới hạn: các đề TCP nâng cao KHÔNG thuộc v1
    assert "bắt tay" in spec.description or "handshake" in spec.description
    # packet_routing: chỉ ngược lại sang encapsulation
    routing = CATALOG["network.packet_routing"]
    assert ENCAP_ID in routing.description


# ── 2. Validator — bề mặt v1 nhỏ, mặc định an toàn ───────────

def test_validate_config_rong_dung_mac_dinh():
    config, err = validate_encapsulation_config({})
    assert err is None
    assert config == {
        "payloadLabel": "Dữ liệu ứng dụng",
        "appProtocol": None,
        "notes": None,
    }


def test_validate_config_day_du_duoc_chuan_hoa():
    config, err = validate_encapsulation_config(
        {"payloadLabel": "  Thư gửi bạn Lan  ", "appProtocol": " HTTP ", "notes": "đề email"}
    )
    assert err is None
    assert config["payloadLabel"] == "Thư gửi bạn Lan"
    assert config["appProtocol"] == "HTTP"
    assert config["notes"] == "đề email"


def test_validate_tu_choi_khoa_cam_r0():
    for bad in ({"steps": []}, {"timeline": []}, {"state": {}}):
        config, err = validate_encapsulation_config(bad)
        assert config is None
        assert "cấm" in err


def test_validate_tu_choi_tu_dinh_nghia_tang():
    """v1 KHÔNG cho LLM tự định nghĩa tầng/PDU — engine sở hữu mô hình 4 tầng."""
    config, err = validate_encapsulation_config({"layers": ["App", "Transport"]})
    assert config is None
    assert "tầng" in err.lower() or "v1" in err


def test_validate_tu_choi_gia_tri_sai_kieu_va_qua_dai():
    config, err = validate_encapsulation_config({"payloadLabel": 123})
    assert config is None
    config, err = validate_encapsulation_config({"payloadLabel": "x" * 81})
    assert config is None
    config, err = validate_encapsulation_config({"appProtocol": "y" * 25})
    assert config is None
    config, err = validate_encapsulation_config("not a dict")
    assert config is None


# ── 3. End-to-end mock: NL tiếng Việt → envelope encapsulation ─

def test_run_pipeline_dinh_tuyen_encapsulation(monkeypatch):
    """Đề đóng gói → classify chọn encap → simulate điền config v1 → envelope
    hợp lệ. R0: envelope KHÔNG chứa timeline/steps — diễn biến là việc của engine."""
    fake, calls = _fake_gemini([
        json.dumps(NET_ANALYSIS),
        json.dumps({"status": "ok", "simulation_id": ENCAP_ID, "reason": None}),
        json.dumps({"payloadLabel": "Dữ liệu từ ứng dụng", "appProtocol": None, "notes": None}),
    ])
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    envelope = asyncio.run(pipeline.run_pipeline(
        "Mô phỏng cách dữ liệu từ ứng dụng được đóng gói qua các tầng TCP/IP rồi truyền tới máy nhận.",
        "fake-key",
    ))
    assert envelope["status"] == "ok"
    assert envelope["simulation_id"] == ENCAP_ID
    assert envelope["config"]["payloadLabel"] == "Dữ liệu từ ứng dụng"
    # R0: không một khóa diễn biến nào lọt vào envelope config
    assert not {"steps", "timeline", "state"} & envelope["config"].keys()
    # simulate phải được cho xem đúng hợp đồng encap
    assert ENCAP_ID in calls[2]["user"]


def test_run_pipeline_routing_van_ve_packet_routing(monkeypatch):
    """Đề ĐƯỜNG ĐI qua thiết bị vẫn về packet_routing — hành vi cũ nguyên vẹn."""
    routing_config = {
        "nodes": [
            {"id": "client", "type": "client"}, {"id": "router", "type": "router"},
            {"id": "isp", "type": "isp"}, {"id": "server", "type": "server"},
        ],
        "links": [["client", "router"], ["router", "isp"], ["isp", "server"]],
        "source": "client", "destination": "server", "notes": None,
    }
    fake, _calls = _fake_gemini([
        json.dumps({**NET_ANALYSIS, "goal": "Đường đi của gói tin từ client tới server"}),
        json.dumps({"status": "ok", "simulation_id": "network.packet_routing", "reason": None}),
        json.dumps(routing_config),
    ])
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    envelope = asyncio.run(pipeline.run_pipeline(
        "Gói tin đi từ client qua router và ISP tới server theo đường nào?", "fake-key",
    ))
    assert envelope["status"] == "ok"
    assert envelope["simulation_id"] == "network.packet_routing"
    # route/timeline KHÔNG nằm trong envelope — engine frontend tự dựng
    assert "route" not in envelope["config"]
