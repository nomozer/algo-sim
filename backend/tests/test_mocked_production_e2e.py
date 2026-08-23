# -*- coding: utf-8 -*-
"""E2E ĐƯỜNG SẢN PHẨM THẬT, biên LLM mock — chạy TRƯỚC mọi lượt live.

VÌ SAO TẦNG NÀY PHẢI CÓ TRƯỚC: mọi thứ sau LLM là tất định, nên nếu chúng hỏng
thì tiêu quota live chỉ để phát hiện lại điều đã biết. Bài học đo được của wave
này: ba lượt probe live liên tiếp chết ở ba tầng khác nhau, cả ba đều tái hiện
được offline mà không tốn một call nào.

Đường đi ở đây là ĐƯỜNG THẬT, không tắt đoạn nào:

    POST /api/analyze → main.py → run_pipeline → stage_semantic_analyze
    → RequestContract → stage_semantic_program → canonicalization → validator
    → interpreter → C₁a/C₁b/C₂ → compile → learner_surface → envelope

Chỉ `call_gemini` bị thay. Không inject envelope, không inject store.

GIỚI HẠN PHẢI ĐỌC KÈM: mock trả về chương trình ĐÃ BIẾT LÀ ĐÚNG, nên tầng này
KHÔNG nói gì về việc LLM có sinh nổi chương trình ấy không. Nó chỉ nói: nếu LLM
sinh đúng, mọi tầng sau sẽ phát ra mô phỏng xem được. Câu hỏi còn lại thuộc về
lượt live.
"""
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.evaluation.m16_offline_scripts import _analysis

from tests.semantic_program.fixtures_coverage_18 import ALL_18_COVERAGE_FIXTURES as F


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    monkeypatch.setenv("SEMANTIC_ROUTE_MODE", "serve")
    from app.main import app

    return TestClient(app)


def _ghim(spec, m: dict[str, str]):
    d = list(spec.memory_declarations)
    for i, x in enumerate(d):
        if x.name in m:
            d[i] = x.model_copy(update={"source_fact_id": m[x.name]})
    return spec.model_copy(update={"memory_declarations": d})


#: (tên miền, đề bài, spec đã ghim provenance, payload semantic_analyze,
#:  id đối tượng phải ĐỔI trên hình, đáp án kiểm tay)
CASES = [
    (
        # Ca BẮT BUỘC của §9 — và là bài đã dựng nên toàn bộ wave này. Trước khi
        # `predicate_verdict` được mở, nó `executable=True` mà không bao giờ
        # `servable`: taxonomy không có kind nào diễn đạt được "chuỗi này có hợp
        # lệ không". Không có gì hard-code riêng cho nó — chỉ một nghĩa vụ tổng
        # quát cộng một vị từ trong `PREDICATE_CHECKERS`.
        "stack",
        "Kiểm tra tính hợp lệ của chuỗi đóng mở ngoặc bằng Stack với chuỗi {[()]}.",
        _ghim(F[0], {"bracket_strip": "I1", "pairs": "I2"}),
        {
            "input_facts": [
                {"id": "I1", "kind": "array", "label": "chuỗi ngoặc",
                 "value": ["{", "[", "(", ")", "]", "}"]},
                {"id": "I2", "kind": "map", "label": "cặp ngoặc tương ứng",
                 "value": ["(", ")", "[", "]", "{", "}"]},
            ],
            "obligations": [{"kind": "predicate_verdict", "container": "bracket_strip",
                             "witness": "result", "pred": "balanced_delimiters"}],
        },
        "stack",
        {"result": "HỢP LỆ"},
    ),
    (
        "array",
        "Cho dãy 12, 45, 67, 23, 89, 34. Tìm phần tử lớn nhất.",
        _ghim(F[1], {"arr": "I1"}),
        {
            "input_facts": [{"id": "I1", "kind": "array", "label": "dãy số",
                             "value": ["12", "45", "67", "23", "89", "34"]}],
            "obligations": [{"kind": "extremum", "container": "arr",
                             "witness": "max_val", "cmp": "max"}],
        },
        # `arr` KHÔNG biến động — tìm max không sửa dãy. Thứ mang diễn tiến là ô
        # kết quả. Chọn nhầm đối tượng thì test đỏ vì lý do sai, và sửa cho nó
        # xanh bằng cách nới điều kiện là đúng cách một cổng trở nên vô nghĩa.
        "max_box",
        {"max_val": 89},
    ),
    (
        "graph",
        "Duyệt đồ thị theo chiều rộng từ đỉnh 1.",
        _ghim(F[8], {"g": "I1"}),
        {
            "input_facts": [{"id": "I1", "kind": "graph", "label": "đồ thị",
                             "value": ["1", "2", "3", "4", "5"]}],
            "obligations": [{"kind": "reachability", "container": "g",
                             "witness": "order"}],
        },
        "q",
        {"order": ["1", "2", "3", "4", "5"]},
    ),
    (
        "map",
        "Đếm tần suất xuất hiện của từng ký tự trong xâu.",
        _ghim(F[17], {"text": "I1"}),
        {
            "input_facts": [{"id": "I1", "kind": "array", "label": "xâu ký tự",
                             "value": ["a", "b", "a", "c", "b", "a"]}],
            "obligations": [{"kind": "total_mapping", "container": "freq",
                             "witness": "freq"}],
        },
        "freq",
        {},
    ),
]


def _kich_ban(spec, payload_analyze):
    """4 lượt, ĐÚNG THỨ TỰ THẬT: analyze · semantic_analyze · semantic_program
    · classify."""
    return [
        json.dumps(_analysis(goal="x", ownership="algorithmic")),
        json.dumps(payload_analyze),
        spec.model_dump_json(),
        json.dumps({"status": "ok", "simulation_id": "generic.rule_scene",
                    "reason": None}),
    ]


def _fake(responses):
    async def f(api_key, system_prompt, user_text, response_schema=None,
                temperature=0.2, image=None):
        assert responses, "gọi nhiều hơn kịch bản"
        return responses.pop(0)

    return f


@pytest.mark.parametrize(
    "ten,de,spec,payload,oid_dong,dap_an", CASES, ids=[c[0] for c in CASES]
)
def test_e2e_mock_llm_phat_ra_mo_phong_XEM_DUOC(
    client, ten, de, spec, payload, oid_dong, dap_an
):
    with patch("app.ai.pipeline.call_gemini", _fake(_kich_ban(spec, payload))):
        res = client.post("/api/analyze", json={"input": {"type": "text", "content": de}})

    assert res.status_code == 200, res.text
    body = res.json()

    # 1. Đi đúng route sinh ngữ nghĩa, không rơi về classifier legacy.
    assert body["status"] == "ok", body.get("reason")
    assert body["simulation_id"] == "generic.semantic_program", body["simulation_id"]

    frames = body["config"]["frames"]
    assert len(frames) > 1, "một khung thì không có gì để xem"

    # 2. Đối tượng mang diễn tiến phải ĐỔI giữa các khung — triệu chứng gốc của
    #    cả wave là hình đứng yên trong khi lời kể chạy.
    def hinh(fr):
        """Phép chiếu ngữ nghĩa của MỘT đối tượng, bất kể primitive nào.

        Ba kênh giá trị cùng tồn tại: `items` (dãy/ngăn xếp/hàng đợi),
        `entries` (bảng ánh xạ), `value` (ô vô hướng). Đọc thiếu một kênh thì
        test đỏ vì đọc nhầm chỗ, không phải vì hệ hỏng.
        """
        o = next((x for x in fr["objects"] if x.get("id") == oid_dong), None)
        if o is None:
            return "None"
        for k in ("items", "entries", "value"):
            if k in o:
                return json.dumps(o[k], ensure_ascii=False, sort_keys=True)
        return "None"

    assert len({hinh(f) for f in frames}) > 1, (
        f"{ten}: '{oid_dong}' đứng yên suốt {len(frames)} khung"
    )

    # 3. Lời kể có ở mọi khung và không rỗng.
    assert all((f.get("narration") or "").strip() for f in frames)

    # 4. Không rò chuỗi kỹ thuật lên bề mặt học sinh.
    from app.simulation.semantic_program.learner_surface import _ro_ri

    assert _ro_ri({"config": {"frames": frames}}) == []

    # 5. Đáp án đúng — kiểm tay, không chép từ đầu ra của hệ.
    for k, v in dap_an.items():
        assert body.get("final_memory", {}).get(k, v) == v


def test_khong_khung_nao_ro_dinh_danh_ky_thuat_len_UI(client):
    """`simulation_id` kiểu `generic.semantic_program` KHÔNG được lọt vào lời kể."""
    ten, de, spec, payload, _, _ = CASES[0]
    with patch("app.ai.pipeline.call_gemini", _fake(_kich_ban(spec, payload))):
        body = client.post("/api/analyze", json={"input": {"type": "text", "content": de}}).json()

    for f in body["config"]["frames"]:
        assert "generic." not in (f.get("narration") or "")
        assert "semantic_program" not in (f.get("narration") or "")
