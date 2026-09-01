# -*- coding: utf-8 -*-
"""E2E ĐƯỜNG SẢN PHẨM THẬT, biên LLM mock — chạy TRƯỚC mọi lượt live.

VÌ SAO TẦNG NÀY PHẢI CÓ TRƯỚC: mọi thứ sau LLM là tất định, nên nếu chúng hỏng
thì tiêu quota live chỉ để phát hiện lại điều đã biết. Bài học đo được: ba lượt
probe live liên tiếp chết ở ba tầng khác nhau, cả ba đều tái hiện được offline
mà không tốn một call nào.

Đường đi ở đây là ĐƯỜNG THẬT, không tắt đoạn nào:

    POST /api/analyze → main.py (cổng miền) → run_pipeline → _chay_duong_hinh_hoc
    → stage_semantic_analyze → RequestContract → stage_semantic_program
    → chuẩn hoá → validator → thẩm định tĩnh → grounding → interpreter
    → C₁a/C₁b/C₂ → compile → learner_surface → envelope + Scene3D

Chỉ `call_gemini` bị thay. Không inject envelope, không inject store.

─── VIẾT LẠI SAU GEOMETRY_PRODUCT_CUTOVER (2026-09-01) ────────────────────

Bản trước chạy BỐN ca Tin học (ngăn xếp · dãy · đồ thị · bảng) và một kịch bản
**bốn lượt** LLM (`analyze` → `semantic_analyze` → `semantic_program` →
`classify`). Cả hai đều không còn tồn tại: đường sản phẩm nay là hình học, rẽ
ngay đầu `run_pipeline`, và tiêu ĐÚNG HAI lượt.

Ý định của file thì không đổi một chữ — *nếu LLM sinh đúng, mọi tầng sau có
phát ra một mô phỏng xem được không* — và nó nay hỏi câu ấy về đúng miền mà
khoá luận nhận.

GIỚI HẠN PHẢI ĐỌC KÈM: mock trả về chương trình ĐÃ BIẾT LÀ ĐÚNG, nên tầng này
KHÔNG nói gì về việc LLM có sinh nổi chương trình ấy không. Nó chỉ nói: nếu LLM
sinh đúng, mọi tầng sau sẽ phát ra mô phỏng xem được. Câu còn lại thuộc lượt live.
"""
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    monkeypatch.setenv("SEMANTIC_ROUTE_MODE", "serve")
    from app.main import app

    return TestClient(app)


DE = ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông, A(0;0;0), B(2;0;0), "
      "C(2;2;0), D(0;2;0) và đỉnh S(0;0;4). Gọi M là trung điểm cạnh SC. "
      "Đường thẳng BM cắt mặt phẳng (SAD) tại K. Tính độ dài đoạn AK.")

#: Đầu ra `geometry_analyze` giả. Kiểu dữ kiện giới hạn trong
#: `INPUT_FACT_KINDS_HINH_HOC` — miền này không có `array`/`graph`.
PAYLOAD_ANALYZE = {
    "input_facts": [
        {"id": "day_vuong", "kind": "str", "label": "ABCD là hình vuông"},
        {"id": "m_trung_diem", "kind": "str", "label": "M là trung điểm SC"},
        {"id": "k_giao", "kind": "str", "label": "K là giao của BM với (SAD)"},
    ],
    # ⚠️ `witness`/`wrt` là trường CẤP MỘT ở ĐẦU VÀO của `analyze` (xem
    # `analyze_schema_for("hinh_hoc")`). Artifact đã commit in chúng dưới
    # `params` vì đó là hình dạng lúc DUMP model — chép theo bản dump thì
    # `build_request_contract` bỏ qua và `witness` ra `None`, rồi cổng phủ nói
    # *"không có đường tạo ra thứ đề bài yêu cầu"* ở một chỗ khó lần ra.
    #
    # `container` phải là tên chương trình KHAI (`memory_declarations` hoặc
    # `declare_point`), không phải tên do `construct_*` sinh ra — cổng phủ đọc
    # đúng bảng khai. Nên container là `A` (điểm gốc, đề cho) và `wrt` là `K`.
    "obligations": [{"kind": "distance", "container": "A",
                     "witness": "do_dai_ak", "wrt": "K"}],
}

#: Chương trình ĐÚNG cho đề trên. Kiểm tay: M=(1,1,2); BM: (2,0,0)+t(−1,1,2);
#: (SAD) là mặt x=0 ⇒ t=2 ⇒ K=(0,2,4); AK = √(4+16) = 2√5.
CHUONG_TRINH = {
    "title": "Giao của đường với mặt bên rồi đo khoảng cách",
    "memory_declarations": [{"name": "do_dai_ak", "type": "float"}],
    "statements": [
        {"kind": "declare_point", "target_var": "A", "at": [0, 0, 0],
         "model_assumption": "toạ độ đề cho"},
        {"kind": "declare_point", "target_var": "B", "at": [2, 0, 0],
         "model_assumption": "toạ độ đề cho"},
        {"kind": "declare_point", "target_var": "C", "at": [2, 2, 0],
         "model_assumption": "toạ độ đề cho"},
        {"kind": "declare_point", "target_var": "D", "at": [0, 2, 0],
         "model_assumption": "toạ độ đề cho"},
        {"kind": "declare_point", "target_var": "S", "at": [0, 0, 4],
         "model_assumption": "toạ độ đề cho"},
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "midpoint", "a": "S", "b": "C"}},
        {"kind": "construct_line", "target_var": "BM",
         "through_a": "B", "through_b": "M"},
        {"kind": "construct_plane", "target_var": "SAD",
         "through": ["S", "A", "D"]},
        {"kind": "construct_point", "target_var": "K",
         "expr": {"kind": "intersect_line_plane", "line": "BM", "plane": "SAD"}},
        {"kind": "assign", "target_var": "do_dai_ak",
         "expr": {"kind": "measure", "quantity": "distance",
                  "of": "K", "wrt": "A"}},
    ],
}

#: Vật MANG DIỄN TIẾN. `K` vắng mặt ở các khung đầu rồi xuất hiện — đúng thứ
#: một mô phỏng dựng hình phải cho thấy. Chọn nhầm vật thì test đỏ vì lý do sai,
#: và nới điều kiện cho nó xanh là đúng cách một cổng trở nên vô nghĩa.
OID_DONG = "K"


def _kich_ban():
    """ĐÚNG HAI lượt, đúng thứ tự thật: `geometry_analyze` · tổng hợp.

    Không còn `analyze` Tin học ở ô số 0 và không còn `classify` ở cuối — đường
    hình học không đi qua cái nào (`test_geometry_route_independence.py`).
    """
    return [json.dumps(PAYLOAD_ANALYZE), json.dumps(CHUONG_TRINH)]


def _fake(responses):
    async def f(api_key, system_prompt, user_text, response_schema=None,
                temperature=0.2, image=None):
        assert responses, "gọi nhiều hơn kịch bản"
        return responses.pop(0)

    return f


def _chay(client):
    with patch("app.ai.pipeline.call_gemini", _fake(_kich_ban())):
        res = client.post("/api/analyze",
                          json={"input": {"type": "text", "content": DE}})
    assert res.status_code == 200, res.text
    return res.json()


def test_e2e_mock_llm_phat_ra_mo_phong_XEM_DUOC(client):
    body = _chay(client)

    # 1. Đi đúng route sinh ngữ nghĩa.
    assert body["status"] == "ok", body.get("reason")
    assert body["simulation_id"] == "generic.semantic_program", body["simulation_id"]

    frames = body["config"]["frames"]
    assert len(frames) > 1, "một khung thì không có gì để xem"

    # 2. Diễn tiến phải NHÌN THẤY ĐƯỢC — triệu chứng gốc của cả wave sinh ra
    #    file này là hình đứng yên trong khi lời kể chạy.
    #
    #    ⚠️ HỎI ĐÚNG BỀ MẶT. Với chương trình hình học, `config.frames` KHÔNG
    #    mang object nào — nội dung nhìn thấy nằm trọn trong `scene3d`. Một
    #    phép kiểm soi `frames[].objects` ở đây sẽ luôn thấy rỗng và luôn đỏ,
    #    hoặc tệ hơn: luôn xanh nếu ai đó nới nó cho qua.
    su_kien = body["scene3d"]["events"]
    assert len(su_kien) == len(frames), (
        "bất biến #31 `frame k ⇔ trace[k]`: số sự kiện cảnh phải bằng số khung")
    assert [e["step_index"] for e in su_kien] == list(range(len(su_kien)))
    # Vật KHÔNG được có mặt hết ở bước 0 — chuỗi dựng phải trải ra theo thời gian.
    dung = [e for e in su_kien if e["action"] == "CREATE"]
    assert {e["object"] for e in dung} == {"M", "BM", "SAD", OID_DONG}
    assert min(e["step_index"] for e in dung) > 0, "không có bước khởi tạo?"
    # Và mỗi bước phải nói nó DỰA VÀO đâu — thứ phân biệt một chuỗi dựng với
    # một danh sách hình rời rạc.
    assert all(e["depends"] for e in dung)

    # 3. Lời kể có ở mọi khung và không rỗng.
    assert all((f.get("narration") or "").strip() for f in frames)

    # 4. Không rò chuỗi kỹ thuật lên bề mặt học sinh.
    from app.simulation.semantic_program.learner_surface import _ro_ri

    assert _ro_ri({"config": {"frames": frames}}) == []


def test_envelope_mang_canh_3D_that(client):
    """Đường hình học phải phát CẢNH, không chỉ khung 2D.

    Phép kiểm này chưa từng có ở bản Tin học vì miền ấy không có cảnh 3D — và
    nó là thứ phân biệt sản phẩm hiện tại với sản phẩm cũ.
    """
    body = _chay(client)
    canh = body.get("scene3d")
    assert canh and canh["objects"], "envelope hình học thiếu `scene3d`"
    assert body.get("domain") == "geometry"
    loai = {o["type"] for o in canh["objects"]}
    assert {"point3", "line3", "plane3"} <= loai, loai
    # Xuất xứ tới được mặt học sinh — thứ phân biệt hệ này với một bộ vẽ hình.
    assert any(o.get("producer") for o in canh["objects"])


def test_khong_khung_nao_ro_dinh_danh_ky_thuat_len_UI(client):
    """`simulation_id` kiểu `generic.semantic_program` KHÔNG được lọt vào lời kể."""
    body = _chay(client)
    for f in body["config"]["frames"]:
        assert "generic." not in (f.get("narration") or "")
        assert "semantic_program" not in (f.get("narration") or "")
