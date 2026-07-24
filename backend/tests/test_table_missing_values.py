# -*- coding: utf-8 -*-
"""M17 W2B-PATCH §C (L3) — CHUẨN HOÁ MARKER THIẾU DỮ LIỆU, THEO LƯỢC ĐỒ.

Sự cố live L3 (`docs/evaluation/m17/rc1/live_table_query_report.md`): đề viết ô
numeric trống bằng CHỮ "trống"; LLM chép đúng nguyên văn (grounding ĐÚNG), nhưng
`_coerce` từ chối `"trống"` là số ⇒ cạn 3 lượt simulate ⇒ `status=error`, không
có mô phỏng nào. Ô thiếu dữ liệu là chuyện bình thường của bảng thật.

Nguyên tắc của bản vá (KHÔNG phải luật toàn cục "mọi 'trống' đều là null"):
- chuẩn hoá diễn ra ở ĐÚNG MỘT BIÊN: ô thô → chuẩn hoá theo lược đồ → ép kiểu →
  validate. Executor chỉ nhận `None` hoặc giá trị đã đúng kiểu;
- CHỈ cột nullable kiểu number/boolean mới coi marker là thiếu dữ liệu;
- cột text GIỮ NGUYÊN literal (chuỗi "trống" có thể là dữ liệu thật);
- 0 / "0" / false / "không" KHÔNG BAO GIỜ là thiếu dữ liệu;
- chữ số sai kiểu ("abc", "tám") vẫn FAIL-CLOSED — không hoá null cho tiện.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.ai import pipeline
from app.evaluation.authenticity_fixtures import _analysis, _classify, _table_cfg
from app.simulation.table_query_engine import run_table_query
from app.validation.table_query import validate_table_query_config

TARGET = "database.relational_table_query"

# Bảng L3 THẬT (live): 6 dòng, 2 ô trống, AVG chỉ tính trên ô có dữ liệu.
_L3_SCHEMA = [
    {"name": "hoc_sinh", "type": "text", "label": "Học sinh"},
    {"name": "diem", "type": "number", "label": "Điểm kiểm tra"},
]
_L3_MARKERS = ["An", "Bình", "Chi", "Dũng", "Hà", "Lan"]


def _rows(marker_binh: str, marker_ha: str) -> list[dict]:
    """Bảng L3 với hai ô trống ghi bằng marker do đề dùng."""
    diem = ["8", marker_binh, "9.5", "7", marker_ha, "8.5"]
    return [{"hoc_sinh": n, "diem": d} for n, d in zip(_L3_MARKERS, diem)]


def _cfg(rows, schema=None) -> dict:
    return {"specVersion": "table-1.0", "schema": schema or _L3_SCHEMA, "rows": rows}


# ── 1–3. marker phổ biến ở cột SỐ nullable → None ─────────────────
@pytest.mark.parametrize("marker", ["", "   ", "trống", "Trống", "—", "N/A", "n/a", "null"])
def test_marker_thieu_du_lieu_o_cot_so_thanh_none(marker):
    cfg, err = validate_table_query_config(_cfg(_rows(marker, marker)))
    assert err is None, f"marker {marker!r} bị từ chối thay vì coi là ô trống: {err}"
    assert cfg["rows"][1]["diem"] is None
    assert cfg["rows"][4]["diem"] is None
    # các ô CÓ dữ liệu không bị đụng
    assert [r["diem"] for r in cfg["rows"]] == [8, None, 9.5, 7, None, 8.5]


def test_evidence_ghi_lai_tung_o_da_chuan_hoa():
    """Chuẩn hoá phải để lại BẰNG CHỨNG máy-đọc — không âm thầm đổi dữ liệu."""
    cfg, err = validate_table_query_config(_cfg(_rows("trống", "—")))
    assert err is None
    ev = cfg["normalizations"]
    assert [e["row"] for e in ev] == [2, 5]
    assert [e["column"] for e in ev] == ["diem", "diem"]
    assert [e["original"] for e in ev] == ["trống", "—"]
    assert all(e["normalized"] is None for e in ev)
    assert all(e["column_type"] == "number" for e in ev)
    assert all(e["reason"] == "missing_value_marker" for e in ev)


# ── 4. cột TEXT giữ nguyên literal ────────────────────────────────
def test_cot_text_giu_nguyen_chu_trong_lam_du_lieu_that():
    schema = [{"name": "ten", "type": "text"}, {"name": "ghi_chu", "type": "text"}]
    cfg, err = validate_table_query_config(_cfg(
        [{"ten": "An", "ghi_chu": "trống"}, {"ten": "Bình", "ghi_chu": "—"}], schema))
    assert err is None
    assert cfg["rows"][0]["ghi_chu"] == "trống", "cột chữ KHÔNG được mất dữ liệu"
    assert cfg["rows"][1]["ghi_chu"] == "—"
    assert cfg.get("normalizations") == []


# ── 5–6. giá trị KHÔNG BAO GIỜ là thiếu dữ liệu ───────────────────
def test_so_khong_va_chuoi_khong_khong_bao_gio_thanh_none():
    schema = [{"name": "diem", "type": "number"}, {"name": "dat", "type": "boolean"},
              {"name": "ghi_chu", "type": "text"}]
    cfg, err = validate_table_query_config(_cfg(
        [{"diem": 0, "dat": False, "ghi_chu": "không"},
         {"diem": "0", "dat": "sai", "ghi_chu": "0"}], schema))
    assert err is None
    assert cfg["rows"][0]["diem"] == 0 and cfg["rows"][1]["diem"] == 0
    assert cfg["rows"][0]["dat"] is False and cfg["rows"][1]["dat"] is False
    assert cfg["rows"][0]["ghi_chu"] == "không" and cfg["rows"][1]["ghi_chu"] == "0"
    assert cfg["normalizations"] == []


# ── 7. chữ sai kiểu vẫn FAIL-CLOSED ───────────────────────────────
@pytest.mark.parametrize("bad", ["abc", "tám", "8 điểm", "không rõ"])
def test_chu_khong_phai_marker_van_bi_tu_choi(bad):
    cfg, err = validate_table_query_config(_cfg(_rows(bad, "trống")))
    assert cfg is None and err, f"{bad!r} phải bị từ chối, không được hoá null"
    assert "diem" in err


# ── 8. cột khai KHÔNG nullable → marker là lỗi ────────────────────
def test_cot_khai_khong_nullable_thi_marker_bi_tu_choi():
    schema = [{"name": "hoc_sinh", "type": "text"},
              {"name": "diem", "type": "number", "nullable": False}]
    cfg, err = validate_table_query_config(_cfg(_rows("trống", "trống"), schema))
    assert cfg is None and err
    assert "diem" in err


def test_cot_khong_nullable_van_nhan_gia_tri_that():
    schema = [{"name": "hoc_sinh", "type": "text"},
              {"name": "diem", "type": "number", "nullable": False}]
    rows = [{"hoc_sinh": n, "diem": v}
            for n, v in zip(_L3_MARKERS, ["8", "6", "9.5", "7", "5", "8.5"])]
    cfg, err = validate_table_query_config(_cfg(rows, schema))
    assert err is None and cfg["rows"][0]["diem"] == 8


# ── L3 đầu-cuối: AVG bỏ qua ô trống, engine sở hữu kết quả ────────
def test_L3_avg_bo_qua_o_trong_engine_tinh_dung():
    cfg, err = validate_table_query_config({
        **_cfg(_rows("trống", "trống")),
        "aggregate": {"func": "avg", "column": "diem"},
    })
    assert err is None
    out = run_table_query(cfg)
    agg = out["aggregateResult"]
    assert agg["counted"] == 4, "chỉ 4 ô có dữ liệu được tính"
    assert agg["value"] == pytest.approx(8.25), "(8+9.5+7+8.5)/4"
    assert sum(1 for r in cfg["rows"] if r["diem"] == 0) == 0, "empty→0 = 0"


def test_L3_qua_production_pipeline(monkeypatch):
    """Chạy qua `run_pipeline` THẬT (bất biến #22): LLM chép "trống" nguyên văn
    như live vẫn phải ra mô phỏng hợp lệ, KHÔNG cạn retry."""
    responses = [
        json.dumps({**_analysis(
            objects=["bảng điểm kiểm tra", "cột Học sinh", "cột Điểm kiểm tra"],
            data=[{"description": "điểm kiểm tra", "values": [8, 9.5, 7, 8.5],
                   "labels": _L3_MARKERS},
                  {"description": "tên học sinh", "labels": _L3_MARKERS}],
            goal="Tính điểm trung bình của các ô có dữ liệu"),
            "requested_operations": ["relational_table_query:avg"]}, ensure_ascii=False),
        json.dumps(_classify(TARGET)),
        _table_cfg(_L3_SCHEMA, _rows("trống", "trống"),
                   aggregate={"func": "avg", "column": "diem"}),
    ]

    async def fake(api_key, system_prompt, user_text, response_schema=None,
                   temperature=0.2, image=None):
        assert responses, "gọi nhiều hơn scripted → đã phải xong từ lượt 1"
        return responses.pop(0)

    monkeypatch.setattr(pipeline, "call_gemini", fake)
    env = asyncio.run(pipeline.run_pipeline("Cho bảng điểm…", "khoa-gia"))
    assert env["status"] == "ok", env.get("reason")
    assert env["simulation_id"] == TARGET
    out = run_table_query(env["config"])
    assert out["aggregateResult"]["value"] == pytest.approx(8.25)
    assert out["aggregateResult"]["counted"] == 4
    # KHÔNG rò rỉ kết quả vào candidate spec
    for leaked in ("aggregateResult", "result_rows", "steps"):
        assert leaked not in env["config"]
