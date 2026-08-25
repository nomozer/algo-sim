# -*- coding: utf-8 -*-
"""TASK 5 — thất bại phải mang `details`, không chỉ một câu chung. **0 API.**

ĐO ĐƯỢC Ở PHASE 5 LƯỢT 2: cả **sáu** ca grounding phát ra y hệt một câu —
*"Chương trình dùng dữ liệu không truy được về đề bài."* Câu ấy không phân biệt
được `geo_09` (trích dẫn hỏng, chương trình gần đúng) với `geo_05` (khai thẳng
`perpendicular = True`, vi phạm R0). Hai bệnh khác hẳn nhau, cùng một chẩn đoán.

Phải chạy lại cổng tất định OFFLINE mới lấy được chi tiết. Việc đó làm được vì
IR có lưu — nhưng nó là forensics, không phải đo, và không phải lúc nào cũng có.
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


def _chay_geo09(rn, monkeypatch, ct: dict):
    """Thả một IR qua đúng chuỗi cổng sản phẩm, không API."""
    from app.ai import pipeline
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from test_geometry_wave2 import _hop_dong_geo_09

    async def a(*x, **k):
        return _hop_dong_geo_09(), None

    async def p(*x, **k):
        return SemanticProgramSpec.model_validate(ct), None

    monkeypatch.setattr(pipeline, "stage_semantic_analyze", a)
    monkeypatch.setattr(pipeline, "stage_semantic_program", p)
    return asyncio.run(rn.chay_mot_case(_CASES[8], "khoa-gia"))


# ══ HÌNH DẠNG TRƯỜNG THẤT BẠI ════════════════════════════════════════════
def test_bon_truong_that_bai_deu_co_mat(rn, monkeypatch):
    """`{code, reason, details, layer}` — đặc tả TASK 5. Cộng `stage_reached`
    vì nó nói cổng NÀO chặn, thứ mà `layer` gộp lại."""
    from test_geometry_wave2 import _chuong_trinh_geo_09

    ct = _chuong_trinh_geo_09()
    ct["memory_declarations"] = [
        d if d["name"] != "S"
        else {"name": "S", "type": "point3", "initial_value": [0, 0, 2],
              "source_fact_id": "id_khong_ton_tai"}
        for d in ct["memory_declarations"]
    ]
    ra = _chay_geo09(rn, monkeypatch, ct)
    for k in ("failure_code", "failure_reason", "failure_details",
              "failure_layer", "stage_reached"):
        assert k in ra, f"thiếu {k}"
    assert ra["failure_code"] == "input_not_grounded"
    assert ra["stage_reached"] == "grounding"
    assert ra["failure_details"], "details rỗng — đúng lỗ của PHASE 5"
    assert any("id_khong_ton_tai" in d for d in ra["failure_details"])


def test_details_PHAN_BIET_duoc_hai_benh_cung_ma_loi(rn, monkeypatch):
    """Đây là điều `reason` không làm được, và là toàn bộ lý do TASK 5 tồn tại.

    Cùng `failure_code = input_not_grounded`, nhưng:
      · trích dẫn hỏng      → details nói tên id
      · khai đáp án         → details mở đầu bằng [MODEL_ASSUMPTION_IS_ANSWER]
    """
    from test_geometry_wave2 import _chuong_trinh_geo_09

    ct1 = _chuong_trinh_geo_09()
    ct1["memory_declarations"] = [
        d if d["name"] != "S"
        else {"name": "S", "type": "point3", "initial_value": [0, 0, 2],
              "source_fact_id": "id_bia"}
        for d in ct1["memory_declarations"]
    ]

    ct2 = _chuong_trinh_geo_09()
    ct2["statements"] = ct2["statements"][:1]
    ct2["memory_declarations"] = [
        d if d["name"] != "V"
        else {"name": "V", "type": "point3", "initial_value": [0, 0, 0],
              "model_assumption": "đáp số"}
        for d in ct2["memory_declarations"]
    ]

    r1 = _chay_geo09(rn, monkeypatch, ct1)
    r2 = _chay_geo09(rn, monkeypatch, ct2)
    assert r1["failure_code"] == r2["failure_code"] == "input_not_grounded"
    assert r1["failure_reason"] == r2["failure_reason"], "reason GIỐNG nhau"
    assert r1["failure_details"] != r2["failure_details"], "details phải KHÁC"
    assert any("MODEL_ASSUMPTION_IS_ANSWER" in d for d in r2["failure_details"])


def test_C1a_details_noi_ro_CAI_GI_lech(rn, monkeypatch):
    """PHASE 5 lượt 2: `geo_02` tạo ra mọi thứ nó khai mà C₁a vẫn từ chối, và
    thông điệp chỉ nói tên bên HỢP ĐỒNG. Phân tích phải SUY "chắc là lệch tên".

    Nay details kèm cả hai phía, nên lượt sau đọc ra ngay: hợp đồng đòi `X`,
    chương trình tạo `Y Z T` ⇒ lệch danh xưng, không phải thiếu phép dựng.
    """
    from app.ai import pipeline
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import RequestContract
    from test_geometry_wave2 import _chuong_trinh_geo_09

    hd = RequestContract(obligations=(
        Obligation(kind="volume", container="chop",
                   params={"witness": "ten_analyze_dat"}),
    ))

    async def a(*x, **k):
        return hd, None

    async def p(*x, **k):
        return SemanticProgramSpec.model_validate(_chuong_trinh_geo_09()), None

    monkeypatch.setattr(pipeline, "stage_semantic_analyze", a)
    monkeypatch.setattr(pipeline, "stage_semantic_program", p)
    ra = asyncio.run(rn.chay_mot_case(_CASES[8], "khoa-gia"))

    assert ra["failure_code"] == "requested_operation_uncovered"
    noi_dung = " ".join(ra["failure_details"])
    assert "ten_analyze_dat" in noi_dung, "phải nói tên hợp đồng đòi"
    assert "chương trình khai" in noi_dung, "phải nói chương trình có gì"
    assert "'V'" in noi_dung or "V" in noi_dung


def test_BON_dang_hong_deu_co_du_hinh_dang(rn, monkeypatch):
    """TASK 4 — grounding · schema · coverage · execution. Bốn tầng, một hình
    dạng. Thiếu `details` ở tầng nào thì tầng ấy trở lại thành "một chuỗi", và
    lượt đo sau lại phải chạy forensics như lần này.
    """
    from app.ai import pipeline
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import RequestContract
    from test_geometry_wave2 import _chuong_trinh_geo_09, _hop_dong_geo_09

    def _ir(bien_doi=None):
        ct = _chuong_trinh_geo_09()
        return bien_doi(ct) if bien_doi else ct

    # ① GROUNDING — trích dẫn không giải được, không có giả thiết đỡ
    def _g(ct):
        ct["memory_declarations"] = [
            d if d["name"] != "S"
            else {"name": "S", "type": "point3", "initial_value": [0, 0, 2],
                  "source_fact_id": "id_bia"}
            for d in ct["memory_declarations"]]
        return ct

    # ③ COVERAGE — witness hợp đồng đòi không có trong chương trình
    hd_lech = RequestContract(obligations=(
        Obligation(kind="volume", container="chop",
                   params={"witness": "ten_khac_han"}),))

    # ④ EXECUTION — khối trỏ chỉ số đỉnh ngoài biên ⇒ kernel NÉM
    def _e(ct):
        for s in ct["statements"]:
            if s["kind"] == "construct_solid":
                s["faces"] = [[0, 1, 2, 3], [0, 1, 9], [1, 2, 4], [2, 3, 4],
                              [3, 0, 4]]
        return ct

    ca = [
        ("grounding", _hop_dong_geo_09(), _ir(_g), None),
        ("schema", _hop_dong_geo_09(), None,
         "1 validation error for SemanticProgramSpec"),
        ("coverage", hd_lech, _ir(), None),
        ("execution", _hop_dong_geo_09(), _ir(_e), None),
    ]
    for ten, hd, ct, loi_schema in ca:
        async def a(*x, _h=hd, **k):
            return _h, None

        async def p(*x, _c=ct, _l=loi_schema, **k):
            if _l:
                return None, _l
            return SemanticProgramSpec.model_validate(_c), None

        monkeypatch.setattr(pipeline, "stage_semantic_analyze", a)
        monkeypatch.setattr(pipeline, "stage_semantic_program", p)
        ra = asyncio.run(rn.chay_mot_case(_CASES[8], "khoa-gia"))

        assert ra["executable"] is False, ten
        assert ra["failure_code"], f"{ten}: thiếu code"
        assert ra["failure_reason"], f"{ten}: thiếu reason"
        assert ra["failure_layer"] is not None, f"{ten}: thiếu layer"
        if ten != "schema":
            # Tầng schema: chi tiết nằm trong chính chuỗi lỗi Pydantic, và
            # `generated_raw` giữ vật chứng — nên `details` rỗng ở đó là ĐÚNG.
            assert ra["failure_details"], f"{ten}: details rỗng"
            assert ra["stage_reached"], f"{ten}: thiếu stage_reached"


def test_schema_fail_giu_VAT_CHUNG_thay_cho_details(rn, monkeypatch):
    """Ranh giới của test trên: tầng 2 không có `details` vì cổng tất định chưa
    chạy. Bù lại nó phải giữ `generated_raw` — nếu không, tầng schema là tầng
    DUY NHẤT không chẩn đoán được, và đó đúng là tầng lượt 1 hỏng nhiều nhất."""
    from app.ai import pipeline
    from test_geometry_wave2 import _hop_dong_geo_09

    async def a(*x, **k):
        return _hop_dong_geo_09(), None

    async def gia_call(*x, **k):
        return '{"memory_declarations": [{"name":"V","type":"volume"}]}'

    async def p(*x, **k):
        from app.ai.telemetry import stage_scope
        with stage_scope("semantic_program"):
            await pipeline.call_gemini("k", "s", "p", {}, 0.1)
        return None, "1 validation error for SemanticProgramSpec"

    monkeypatch.setattr(pipeline, "call_gemini", gia_call)
    monkeypatch.setattr(pipeline, "stage_semantic_analyze", a)
    monkeypatch.setattr(pipeline, "stage_semantic_program", p)
    ra = asyncio.run(rn.chay_mot_case(_CASES[8], "khoa-gia"))
    assert ra["failure_layer"] == 2
    assert '"type":"volume"' in ra["generated_raw"]


# ══ QUAN TRẮC GROUNDING ═══════════════════════════════════════════════════
def test_bai_DI_TRON_DUONG_van_ghi_quan_trac_grounding(rn, monkeypatch):
    """Chỉ gắn quan trắc vào nhánh hỏng thì bài chạy được — bài đáng đếm nhất —
    lại không đếm được nó dùng bao nhiêu giả thiết."""
    from test_geometry_wave2 import _chuong_trinh_geo_09

    ra = _chay_geo09(rn, monkeypatch, _chuong_trinh_geo_09())
    assert ra["executable"] is True
    assert len(ra["grounding_assumptions"]) == 5, ra["grounding_assumptions"]
    assert ra["grounding_unresolved_citations"] == []


def test_trich_dan_hong_duoc_DEM_chu_khong_bi_nuot(rn, monkeypatch):
    """Hạ cấp trích dẫn hỏng không được biến nó thành vô hình — nếu không, mức
    lệch danh xưng giữa hai lượt LLM lại không đo được, đúng như lượt 2."""
    from test_geometry_wave2 import _chuong_trinh_geo_09

    ct = _chuong_trinh_geo_09()
    ct["memory_declarations"] = [
        {**d, "source_fact_id": "id_khong_co_trong_hop_dong"}
        if d.get("model_assumption") else d
        for d in ct["memory_declarations"]
    ]
    ra = _chay_geo09(rn, monkeypatch, ct)
    assert ra["executable"] is True, ra["failure_details"]
    assert len(ra["grounding_unresolved_citations"]) == 5
