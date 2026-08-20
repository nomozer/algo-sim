# -*- coding: utf-8 -*-
"""`stage_semantic_program` — LLM tổng hợp IR, ĐÚNG MỘT LƯỢT.

R0 giữ nguyên: LLM viết *chương trình*, interpreter mới là authority của kết
quả. Cấu trúc và enum do `responseSchema` cưỡng chế (constrained decoding đã
bật sẵn ở `gemini.py`), nên prompt chỉ còn phần KHÔNG mã hoá được.

L1 KHÔNG phải đảm bảo tuyệt đối — có ghi nhận Flash rơi vào vòng lặp lặp token
trong literal số cho tới MAX_TOKENS rồi trả JSON không parse được. Vì vậy phải
có đường xử lý lỗi parse, không được giả định luôn hợp lệ.

0 API call thật: thay `call_gemini` ở biên module.
"""
import asyncio
import json

from app.ai import pipeline

_HOP_LE = {
    "spec_version": "1.0",
    "title": "Tìm giá trị lớn nhất",
    "description": "Quét dãy, giữ lại giá trị lớn nhất đã gặp.",
    "pedagogical_intent": "Thấy biến tích luỹ đổi giá trị qua từng bước.",
    "memory_declarations": [
        {"name": "a", "type": "array", "element_type": "int", "initial_value": [3, 9, 2]},
        {"name": "m", "type": "int", "initial_value": 0},
    ],
    "statements": [
        {
            "kind": "assign",
            "target_var": "m",
            "expr": {"kind": "index", "container": "a", "index": {"kind": "literal", "value": 0}},
        }
    ],
    "visual_bindings": {
        "containers": [{"semantic_id": "a", "primitive": "array_strip", "label": "Dãy"}],
        "pointers": [],
        "value_boxes": [{"box_id": "box_m", "var_ref": "m", "label": "Lớn nhất"}],
    },
}


def _gia_lap(monkeypatch, raw: str) -> dict:
    """Thay call_gemini; trả về dict ghi lại đối số để kiểm hợp đồng gọi."""
    ghi: dict = {}

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
        ghi["system_prompt"] = system_prompt
        ghi["user_text"] = user_text
        ghi["response_schema"] = response_schema
        return raw

    monkeypatch.setattr(pipeline, "call_gemini", fake)
    return ghi


def test_tra_ve_spec_khi_llm_tra_json_hop_le(monkeypatch):
    _gia_lap(monkeypatch, json.dumps(_HOP_LE, ensure_ascii=False))
    spec, err = asyncio.run(pipeline.stage_semantic_program("Tìm max của 3, 9, 2", {}, "k"))
    assert err is None, err
    assert spec is not None
    assert spec.title == "Tìm giá trị lớn nhất"
    assert [d.name for d in spec.memory_declarations] == ["a", "m"]


def test_luon_ep_constrained_decoding(monkeypatch):
    """Không truyền response_schema thì JSON mode chỉ là GỢI Ý, không cưỡng chế."""
    ghi = _gia_lap(monkeypatch, json.dumps(_HOP_LE, ensure_ascii=False))
    asyncio.run(pipeline.stage_semantic_program("đề bất kỳ", {}, "k"))
    schema = ghi["response_schema"]
    assert isinstance(schema, dict) and schema, "Thiếu response_schema"
    assert "properties" in schema and "statements" in schema["properties"]


def test_de_bai_duoc_dua_vao_user_text_khong_nhet_vao_system_prompt(monkeypatch):
    """Đề bài là DỮ LIỆU, không phải luật — nhét vào system prompt là lẫn tầng."""
    ghi = _gia_lap(monkeypatch, json.dumps(_HOP_LE, ensure_ascii=False))
    asyncio.run(pipeline.stage_semantic_program("ĐỀ ĐẶC BIỆT 12345", {}, "k"))
    assert "ĐỀ ĐẶC BIỆT 12345" in ghi["user_text"]
    assert "ĐỀ ĐẶC BIỆT 12345" not in ghi["system_prompt"]


def test_bao_loi_khi_json_khong_parse_duoc(monkeypatch):
    """Chế độ hỏng đã ghi nhận của Flash: cụt giữa chừng ở MAX_TOKENS."""
    _gia_lap(monkeypatch, '{"title": "hong')
    spec, err = asyncio.run(pipeline.stage_semantic_program("đề bất kỳ", {}, "k"))
    assert spec is None
    assert "SEMANTIC_PROGRAM_INVALID" in err


def test_bao_loi_khi_json_hop_le_nhung_sai_hop_dong(monkeypatch):
    """Biến dùng trong biểu thức mà không khai báo → validator tĩnh chặn."""
    xau = json.loads(json.dumps(_HOP_LE))
    xau["memory_declarations"] = [
        {"name": "m", "type": "int", "initial_value": 0}
    ]  # bỏ 'a' nhưng statement vẫn tham chiếu 'a'
    _gia_lap(monkeypatch, json.dumps(xau, ensure_ascii=False))
    spec, err = asyncio.run(pipeline.stage_semantic_program("đề bất kỳ", {}, "k"))
    assert spec is None
    assert "SEMANTIC_PROGRAM_INVALID" in err


def test_json_khong_phai_object_thi_bao_loi_khong_no(monkeypatch):
    _gia_lap(monkeypatch, "[1, 2, 3]")
    spec, err = asyncio.run(pipeline.stage_semantic_program("đề bất kỳ", {}, "k"))
    assert spec is None
    assert "SEMANTIC_PROGRAM_INVALID" in err
