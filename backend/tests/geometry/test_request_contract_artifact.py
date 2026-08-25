# -*- coding: utf-8 -*-
"""TASK 1 — `RequestContract` phải nằm trong artifact. **0 API call.**

Thiếu sót NẶNG NHẤT của PHASE 5 lượt 2, tự khai ở §6 báo cáo: artifact không lưu
hợp đồng, nên chẩn đoán hai ca C₁a chỉ là **suy từ dấu vết**. Không biết
`analyze` đặt `fact_id` gì và `witness` tên gì thì không xác nhận được cái nào
lệch — mà lệch danh xưng lại đúng là giả thuyết hàng đầu.

QUAN TRẮC THUẦN: không tầng chấm nào đọc khoá này, không đường thực thi nào đổi.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_BE = Path(__file__).resolve().parents[2]
_R = _BE / "scripts" / "run_geometry_dev_evaluation.py"
_CASES = json.loads(
    (_BE.parent / "docs" / "evaluation" / "geometry" / "dev" / "cases.json")
    .read_text(encoding="utf-8")
)["cases"]


@pytest.fixture(scope="module")
def rn():
    spec = importlib.util.spec_from_file_location("run_geometry_dev", _R)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_geometry_dev"] = mod
    spec.loader.exec_module(mod)
    return mod


def _chay(rn, monkeypatch, analyze, program=None):
    from app.ai import pipeline

    monkeypatch.setattr(pipeline, "stage_semantic_analyze", analyze)
    if program is not None:
        monkeypatch.setattr(pipeline, "stage_semantic_program", program)
    return asyncio.run(rn.chay_mot_case(_CASES[8], "khoa-gia"))  # geo_09


def _hd_day_du():
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import (
        InputFact,
        RequestContract,
    )

    return RequestContract(
        input_facts=(
            InputFact(fact_id="canh_day", label="cạnh đáy", values=(1,),
                      provenance="confirmed"),
            InputFact(fact_id="sa", label="SA", values=(2,),
                      provenance="claimed", unproven_values=(2,)),
        ),
        obligations=(
            Obligation(kind="volume", container="chop",
                       params={"witness": "V", "value": "2/3"}),
        ),
    )


def test_artifact_CO_request_contract(rn, monkeypatch):
    async def a(*x, **k):
        return _hd_day_du(), None

    async def p(*x, **k):
        return None, "1 validation error for SemanticProgramSpec"

    ra = _chay(rn, monkeypatch, a, p)
    rc = ra["request_contract"]
    assert rc is not None
    assert [f["fact_id"] for f in rc["facts"]] == ["canh_day", "sa"]
    assert rc["obligations"][0]["witness"] == "V"


def test_ghi_du_thu_CHAN_DOAN_can(rn, monkeypatch):
    """Hai thứ mà PHASE 5 lượt 2 không có, và thiếu chúng thì không kết luận
    được: `fact_id` (đối chiếu với `source_fact_id` trong IR) và `witness` (tên
    THẬT mà C₁a đối chiếu)."""
    async def a(*x, **k):
        return _hd_day_du(), None

    async def p(*x, **k):
        return None, "loi"

    rc = _chay(rn, monkeypatch, a, p)["request_contract"]
    f = rc["facts"][1]
    # `provenance` đi kèm vì P1 phân biệt "đề có thật" với "`analyze` tự khai",
    # và hai thứ ấy dẫn tới hai kết luận khác nhau về ai sai.
    assert f["provenance"] == "claimed" and f["unproven_values"] == [2]
    o = rc["obligations"][0]
    assert {"kind", "container", "witness", "params"} <= set(o)
    assert o["params"]["value"] == "2/3"


def test_hop_dong_RONG_van_ghi_duoc(rn, monkeypatch):
    """"Đề không cho dữ kiện nào" là một QUAN SÁT. Ghi `None` cho nó là biến
    quan sát ấy thành "không ghi lại được" — hai điều khác hẳn nhau."""
    from app.simulation.semantic_program.request_contract import RequestContract

    async def a(*x, **k):
        return RequestContract(), None

    async def p(*x, **k):
        return None, "loi"

    rc = _chay(rn, monkeypatch, a, p)["request_contract"]
    assert rc == {"facts": [], "obligations": []}


def test_case_HONG_van_giu_hop_dong(rn, monkeypatch):
    """Bài trượt là bài CẦN hợp đồng nhất — đó là lúc phải biết cái gì lệch."""
    async def a(*x, **k):
        return _hd_day_du(), None

    async def p(*x, **k):
        return None, "1 validation error for SemanticProgramSpec"

    ra = _chay(rn, monkeypatch, a, p)
    assert ra["schema_pass"] is False
    assert ra["request_contract"]["obligations"], "mất hợp đồng ở đúng ca cần nó"


def test_ANALYZE_hong_thi_KHONG_co_hop_dong_de_ghi(rn, monkeypatch):
    """Ranh giới ngược lại: `analyze` không trả hợp đồng thì `None` là đúng —
    ghi `{}` sẽ đọc như "đề không có dữ kiện", một kết luận sai."""
    async def a(*x, **k):
        return None, "SEMANTIC_ANALYZE_INVALID"

    ra = _chay(rn, monkeypatch, a)
    assert ra["request_contract"] is None and ra["failure_layer"] == 0


def test_them_khoa_nay_KHONG_doi_diem(rn, monkeypatch):
    """Backward compatible: `request_contract` là quan trắc, không được chạm
    vào bất kỳ trường chấm điểm nào.

    Hai dạng hỏng, hai kết quả chấm KHÁC NHAU — và cả hai phải giữ nguyên như
    trước Wave 3. Đây cũng là chỗ ghi lại một luật dễ đọc nhầm của runner:
    hỏng KHÔNG-phải-schema thì `schema_pass` vẫn `True`, vì IR đã qua Pydantic
    rồi mới trượt ở chỗ khác.
    """
    async def a(*x, **k):
        return _hd_day_du(), None

    async def p_schema(*x, **k):
        return None, "1 validation error for SemanticProgramSpec"

    async def p_khac(*x, **k):
        return None, "SEMANTIC_PROGRAM_INVALID: JSON không parse được"

    ra = _chay(rn, monkeypatch, a, p_schema)
    assert ra["schema_pass"] is False and ra["failure_layer"] == 2

    ra2 = _chay(rn, monkeypatch, a, p_khac)
    assert ra2["schema_pass"] is True and ra2["failure_layer"] == 3

    for r in (ra, ra2):
        assert r["executable"] is False
        assert r["oracle_pass"] is None
        assert r["request_contract"] is not None


def test_request_contract_complete_artifact(rn, monkeypatch):
    """TASK 3 — khoá ĐỦ BỘ TRƯỜNG, không chỉ sự tồn tại của khối.

    Thiếu một trường là mất một đường chẩn đoán: không `fact_id` thì không đối
    chiếu được `source_fact_id`; không `witness` thì không biết C₁a đòi gì;
    không `provenance` thì không phân biệt "đề có thật" với "`analyze` tự khai",
    mà hai thứ ấy dẫn tới hai kết luận khác nhau về **ai** sai.
    """
    async def a(*x, **k):
        return _hd_day_du(), None

    async def p(*x, **k):
        return None, "1 validation error for SemanticProgramSpec"

    rc = _chay(rn, monkeypatch, a, p)["request_contract"]
    assert set(rc) == {"facts", "obligations"}
    for f in rc["facts"]:
        assert {"fact_id", "label", "values", "provenance",
                "unproven_values"} <= set(f)
    for o in rc["obligations"]:
        assert {"kind", "container", "witness", "params"} <= set(o)


def test_moi_case_CO_hop_dong_khi_analyze_thanh_cong(rn, monkeypatch):
    """"Không có `request_contract=None`" chỉ đúng KHI `analyze` trả hợp đồng.

    ⚠️ Ranh giới có chủ đích, ngược với chữ của đặc tả: `analyze` HỎNG thì
    `None` mới là câu trả lời trung thực. Ghi `{"facts": [], "obligations": []}`
    ở đó sẽ đọc thành *"đề không cho dữ kiện nào"* — một kết luận về ĐỀ BÀI, rút
    ra từ một sự cố của LƯỢT GỌI. Đó là bịa dữ liệu quan trắc.
    """
    from app.simulation.semantic_program.request_contract import RequestContract

    async def ok(*x, **k):
        return RequestContract(), None

    async def p(*x, **k):
        return None, "loi"

    assert _chay(rn, monkeypatch, ok, p)["request_contract"] is not None

    async def hong(*x, **k):
        return None, "SEMANTIC_ANALYZE_INVALID"

    ra = _chay(rn, monkeypatch, hong)
    assert ra["request_contract"] is None
    assert ra["failure_layer"] == 0, "phải phân biệt được đây là hỏng ở analyze"


def test_hop_dong_SERIALIZE_duoc_ra_JSON(rn, monkeypatch):
    """Artifact là JSON. Một `tuple`/`Fraction` lọt vào sẽ làm cả lượt đo vỡ ở
    bước ghi file — sau khi đã tiêu hết quota."""
    async def a(*x, **k):
        return _hd_day_du(), None

    async def p(*x, **k):
        return None, "loi"

    ra = _chay(rn, monkeypatch, a, p)
    json.dumps(ra["request_contract"], ensure_ascii=False)
