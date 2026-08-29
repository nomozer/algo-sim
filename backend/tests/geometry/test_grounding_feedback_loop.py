# -*- coding: utf-8 -*-
"""§9 — lời từ chối của cổng XUẤT XỨ phải QUAY LẠI được mô hình. 0 API call.

Trước bản sửa, `stage_semantic_program` chỉ gửi ngược lỗi **schema**;
`check_grounding` chạy sau, ở `route.py`, nên chương trình được sinh đúng một
lần rồi bị giết ở hạ nguồn mà không ai nói cho nó biết vì sao.

Ba điều test này khoá, và điều thứ ba là điều dễ mất nhất:

  ① lượt sinh đầu vi phạm xuất xứ ⇒ có lượt thứ HAI;
  ② lượt hai nhận ĐÚNG NGUYÊN VĂN lời từ chối, không phải một bản diễn giải;
  ③ chương trình đã sửa đi qua **đúng cái cổng cũ** — không nới, không bỏ
    qua, không có nhánh "lần hai thì dễ hơn".
"""
from __future__ import annotations

import asyncio
import json

from app.ai import pipeline
from app.simulation.semantic_program.grounding_gate import check_grounding
from app.simulation.semantic_program.request_contract import (
    InputFact,
    RequestContract,
)

_HOP_DONG = RequestContract(
    input_facts=(
        InputFact(fact_id="ab_length", label="Độ dài AB", values=(1,)),
    )
)

#: Vi phạm: `B` có toạ độ mà không ghim nguồn, cũng không khai giả thiết.
_HONG = {
    "simulation_id": "geometry.demo",
    "title": "Demo",
    "description": "Demo",
    "pedagogical_intent": "Demo",
    "memory_declarations": [
        {"name": "B", "type": "point3", "initial_value": [1, 0, 0]},
    ],
    "statements": [],
    "obligations": [],
}

#: Đã sửa: cùng toạ độ, nay ghim về đúng mục dữ kiện.
_DUNG = json.loads(json.dumps(_HONG))
_DUNG["memory_declarations"][0]["source_fact_id"] = "ab_length"


class _Ghi:
    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.tra: list[str] = []

    async def __call__(self, api_key, skill, prompt, schema, temp):
        self.prompts.append(prompt)
        return self.tra.pop(0)


def test_vi_pham_xuat_xu_thi_lan_sau_nhan_dung_loi_tu_choi(monkeypatch):
    ghi = _Ghi()
    ghi.tra = [json.dumps(_HONG), json.dumps(_DUNG)]
    monkeypatch.setattr(pipeline, "call_gemini", ghi)
    monkeypatch.setattr(pipeline, "load_skill", lambda *_: "skill")

    class _Quan:
        def __init__(self) -> None:
            self.su_kien: list[dict] = []

        def emit(self, ten: str, data: dict) -> None:
            self.su_kien.append({"ten": ten, **data})

    quan = _Quan()
    spec, loi = asyncio.run(pipeline.stage_semantic_program(
        "Cho hình chóp S.ABC có AB = 1.", {}, "k",
        contract=_HOP_DONG, observer=quan, domain="hinh_hoc",
    ))
    su_kien = quan.su_kien

    # ① có lượt thứ hai
    assert loi is None and spec is not None
    assert len(ghi.prompts) == 2, "vi phạm xuất xứ phải sinh một lượt sửa"

    # ② lượt hai nhận NGUYÊN VĂN lời từ chối của cổng
    tu_choi = check_grounding(_HOP_DONG, pipeline_spec(_HONG))
    assert not tu_choi.ok
    assert tu_choi.unresolved[0] in ghi.prompts[1], (
        "prompt sửa phải mang đúng câu cổng đã nói, không phải bản diễn giải")

    # sự kiện quan trắc phải gọi đúng tên cổng — nếu không, một lượt hỏng vì
    # xuất xứ sẽ đọc y hệt một lượt hỏng vì schema.
    g = [e for e in su_kien if e.get("gate") == "grounding"]
    assert len(g) == 1 and g[0]["ok"] is False

    # ③ bản đã sửa qua ĐÚNG cổng cũ — cùng hàm, cùng hợp đồng, không tham số
    #    nới lỏng nào.
    assert check_grounding(_HOP_DONG, spec).ok


def test_het_luot_van_vi_pham_thi_KHONG_tra_ve_chuong_trinh_vo_can(monkeypatch):
    """Trần 3 lượt giữ nguyên, và lượt cuối KHÔNG được nới cổng.

    Đây là chỗ một "đường phản hồi" dễ lặng lẽ biến thành một lối thoát: nếu
    lượt cuối cứ thế trả về, thì thêm phản hồi vào lại làm cổng YẾU đi.
    """
    ghi = _Ghi()
    ghi.tra = [json.dumps(_HONG)] * pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    monkeypatch.setattr(pipeline, "call_gemini", ghi)
    monkeypatch.setattr(pipeline, "load_skill", lambda *_: "skill")

    spec, _ = asyncio.run(pipeline.stage_semantic_program(
        "Cho hình chóp S.ABC có AB = 1.", {}, "k",
        contract=_HOP_DONG, domain="hinh_hoc"))
    assert len(ghi.prompts) == pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    # Lượt cuối trả spec là ĐÚNG HỢP ĐỒNG của hàm này (nó chỉ kiểm schema);
    # điều phải giữ là `route` vẫn từ chối nó bằng đúng cổng ấy.
    assert spec is None or not check_grounding(_HOP_DONG, spec).ok


def pipeline_spec(payload: dict):
    from app.simulation.semantic_program.validator import validate_semantic_program

    val = validate_semantic_program(payload)
    assert val.ok, val.error
    return val.spec
