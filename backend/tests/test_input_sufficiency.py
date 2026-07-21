# -*- coding: utf-8 -*-
"""M17-RC1 §C2 — lock CỔNG ĐỦ DỮ KIỆN DÙNG CHUNG.

Đóng lớp rủi ro ĐÃ XẢY RA THẬT ở live W2A: đề không cho cấu trúc cây, LLM bịa
nguyên một cây, hệ trả `ok`. RC1-C đo được 18/19 target chưa có phòng thủ
tương đương.

Hai điều test này phải giữ cân bằng:
1. đề KHÔNG cho dữ kiện ⇒ từ chối, executor không chạy, không bịa;
2. đề CÓ cho dữ kiện ⇒ KHÔNG được chặn oan (chặn oan một đề thật tệ hơn nhiều
   so với lọt một đề mơ hồ — đề mơ hồ còn validator phía sau).
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.ai import pipeline
from app.evaluation.authenticity_fixtures import _analysis, _classify
from app.evaluation.rc1c_fixtures import INSUFFICIENT_FIXTURES
from app.simulation.catalog import CATALOG
from app.simulation.descriptor import ReachabilityLevel
from app.simulation.error_codes import ErrorCode
from app.simulation.input_requirements import (
    APPLICABLE,
    INPUT_REQUIREMENTS,
    NOT_APPLICABLE,
    InputKind,
    applicability_of,
)
from app.simulation.sufficiency_gate import (
    EVIDENCE_NORMALIZERS,
    check_input_sufficiency,
    check_input_sufficiency_for_targets,
    sufficiency_evidence,
)


def _ai_reachable() -> list[str]:
    return sorted(sid for sid, s in CATALOG.items()
                  if ReachabilityLevel.AI_REACHABLE_PUBLIC in s.reachability)


# ── hợp đồng phủ đủ, không target nào lọt ────────────────────────
def test_moi_target_ai_reachable_deu_khai_hop_dong():
    """Thêm target thứ 20 mà quên khai hợp đồng dữ kiện ⇒ đỏ ở đây, không
    lặng lẽ chạy mà không có phòng thủ chống bịa."""
    for sid in _ai_reachable():
        assert sid in INPUT_REQUIREMENTS, f"{sid}: thiếu input_requirements"


def test_moi_InputKind_deu_co_normalizer():
    for kind in InputKind:
        assert kind in EVIDENCE_NORMALIZERS, f"{kind.value}: thiếu normalizer"


def test_NOT_APPLICABLE_phai_co_ly_do_dan_xuat_tu_hop_dong():
    """NOT_APPLICABLE KHÔNG được dùng để né fixture thiếu."""
    na = [sid for sid in _ai_reachable() if applicability_of(sid)[0] == NOT_APPLICABLE]
    assert na, "phải có ít nhất một target thật sự không cần dữ kiện"
    for sid in na:
        reason = applicability_of(sid)[1]
        assert len(reason) >= 60, f"{sid}: lý do N/A quá mỏng — {reason!r}"


def test_khong_co_gate_rieng_cho_tung_target():
    """Điều kiện cấu trúc §C2: một cổng dùng chung + normalizer theo NHÓM dữ
    kiện. `sort_sufficiency_gate.py`, `graph_sufficiency_gate.py`… không được
    tồn tại."""
    from pathlib import Path

    sim_dir = Path(CATALOG["tree.traversal"].__module__ and __file__).parent.parent / "app" / "simulation"
    bad = [p.name for p in sim_dir.glob("*_sufficiency_gate.py")
           if p.name != "sufficiency_gate.py"]
    assert bad == [], f"cổng riêng theo target đã xuất hiện: {bad}"


# ── normalizer: fault injection cả hai chiều ─────────────────────
@pytest.mark.parametrize("kind,co,khong", [
    (InputKind.FINITE_SEQUENCE,
     {"data": [{"description": "dãy", "values": [1, 2, 3]}]},
     {"data": [{"description": "dãy số của lớp em"}], "objects": []}),
    (InputKind.NUMERIC_VALUE,
     {"data": [{"description": "số cần đổi", "values": [25]}]},
     {"data": [], "objects": ["một số"]}),
    (InputKind.TREE_STRUCTURE,
     {"relations": ["B là con trái của A"]},
     {"relations": ["quan hệ cha-con giữa các nút trong cây"]}),
    (InputKind.GRAPH_STRUCTURE,
     {"objects": ["đỉnh A", "đỉnh B"], "relations": ["A nối B"]},
     {"objects": ["đồ thị"], "relations": []}),
    (InputKind.BOOLEAN_EXPRESSION,
     {"objects": ["đầu vào A", "cổng AND"]},
     {"objects": ["mạch logic"]}),
    (InputKind.REPRESENTATION_OBJECTS,
     {"objects": ["trạm 1"]},
     {"objects": []}),
])
def test_normalizer_phan_biet_duoc_co_va_khong(kind, co, khong):
    n = EVIDENCE_NORMALIZERS[kind]
    assert n(co)[0] is True, f"{kind.value}: bỏ sót bằng chứng CÓ THẬT (chặn oan)"
    assert n(khong)[0] is False, f"{kind.value}: nhận nhầm mô tả trừu tượng là dữ kiện"


def test_tree_normalizer_giu_nguyen_luat_da_chung_minh_live():
    """Luật W2A: mô tả TRỪU TƯỢNG ("quan hệ cha-con giữa các nút") KHÔNG phải
    cấu trúc; phải có ≥1 quan hệ giữa hai nút CÓ TÊN. Không nới, không siết."""
    n = EVIDENCE_NORMALIZERS[InputKind.TREE_STRUCTURE]
    assert n({"relations": [{"type": "left_child", "from": "A", "to": "B"}]})[0] is True
    assert n({"objects": ["nút (đỉnh) của cây"], "relations": []})[0] is False


# ── chặn / không chặn oan trên từng target ───────────────────────
def test_target_APPLICABLE_bi_chan_khi_analyze_trong():
    empty = {"objects": [], "data": [], "relations": [], "processes": [],
             "constraints": [], "goal": "làm bài", "input_description": "",
             "output_description": "", "result_ownership": "provided"}
    for sid in _ai_reachable():
        if applicability_of(sid)[0] != APPLICABLE:
            continue
        v = check_input_sufficiency(empty, sid)
        assert v is not None, f"{sid}: đề trống mà vẫn cho qua (nguy cơ bịa dữ liệu)"
        assert v[0] in (ErrorCode.INPUT_INSUFFICIENT, ErrorCode.STRUCTURE_INSUFFICIENT)
        assert v[2]["missing_inputs"], f"{sid}: chặn mà không nêu thiếu gì"


def test_target_NOT_APPLICABLE_khong_bao_gio_bi_chan():
    empty = {"objects": [], "data": [], "relations": []}
    for sid in _ai_reachable():
        if applicability_of(sid)[0] == APPLICABLE:
            continue
        assert check_input_sufficiency(empty, sid) is None, f"{sid}: chặn oan"


def test_nhanh_selector_dung_GIAO_khong_doi_thua():
    """Selector chưa biết variant nào sẽ resolve → chỉ đòi thứ MỌI biến thể đều
    cần. Đòi hợp (union) sẽ chặn oan."""
    sorts = ["algorithm.bubble_sort", "algorithm.insertion_sort", "algorithm.selection_sort"]
    co_day = {"data": [{"description": "dãy", "values": [5, 2, 9]}]}
    assert check_input_sufficiency_for_targets(co_day, sorts) is None
    v = check_input_sufficiency_for_targets({"data": [], "objects": []}, sorts)
    assert v is not None and v[2]["missing_inputs"] == ["finite_sequence"]


# ── thông điệp học sinh sạch ─────────────────────────────────────
def test_thong_diep_hoc_sinh_khong_lo_schema():
    empty = {"objects": [], "data": [], "relations": []}
    for sid in _ai_reachable():
        if applicability_of(sid)[0] != APPLICABLE:
            continue
        msg = check_input_sufficiency(empty, sid)[1]
        assert msg, f"{sid}: thiếu thông điệp học sinh"
        for banned in ("_", "{", "}", "None", "null", "schema", "JSON", "config"):
            assert banned not in msg, f"{sid}: thông điệp lộ '{banned}': {msg}"


def test_bang_chung_may_doc_du_truong():
    ev = sufficiency_evidence({"objects": [], "data": [], "relations": []}, "tree.traversal")
    for f in ("target_id", "declared", "applicability", "required", "missing",
              "generated_defaults_allowed"):
        assert f in ev, f


def test_generated_default_khong_thoa_required_input():
    """`generated_defaults_allowed` chỉ được bật cho target NOT_APPLICABLE —
    không target APPLICABLE nào được lấy mặc định hệ sinh làm dữ kiện."""
    for sid, req in INPUT_REQUIREMENTS.items():
        if req.generated_defaults_allowed:
            assert req.applicability == NOT_APPLICABLE, (
                f"{sid}: cho phép mặc định hệ sinh NHƯNG vẫn đòi dữ kiện bắt buộc")


# ── end-to-end: mọi target APPLICABLE có case, executor không chạy ──
def test_moi_target_APPLICABLE_deu_co_insufficient_fixture():
    applicable = {sid for sid in _ai_reachable() if applicability_of(sid)[0] == APPLICABLE}
    covered = {fx.target_id for fx in INSUFFICIENT_FIXTURES}
    assert applicable - covered == set(), f"target APPLICABLE thiếu fixture: {applicable - covered}"


def _fake(responses):
    async def f(api_key, system_prompt, user_text, response_schema=None,
                temperature=0.2, image=None):
        assert responses, "TỚI SIMULATE = sai: executor không được chạy khi thiếu dữ kiện"
        return responses.pop(0)
    return f


def test_e2e_thieu_du_kien_khong_tao_simulation(monkeypatch):
    """Đúng kịch bản live W2A đã hỏng, nay áp cho dãy số: đề không cho dãy →
    KHÔNG ok, KHÔNG generic, KHÔNG chạy simulate."""
    an = {**_analysis(goal="Sắp xếp dãy số của lớp em", objects=[], data=[], relations=[])}
    monkeypatch.setattr(pipeline, "call_gemini", _fake([
        # sorting route qua SELECTOR TOKEN (id concrete không phải lựa chọn
        # hợp lệ của classify) — cổng phải chặn trên chính nhánh đó.
        json.dumps(an), json.dumps(_classify("algorithm.comparison_sort")),
    ]))
    env = asyncio.run(pipeline.run_pipeline("Sắp xếp dãy số của lớp em", "k"))
    assert env["status"] == "unsupported"
    assert env["failure_category"] == "insufficient_specification"
    assert env["error_code"] == ErrorCode.INPUT_INSUFFICIENT.value
    assert env.get("simulation_id") is None and env.get("config") is None
    assert env["input_sufficiency"]["missing_inputs"] == ["finite_sequence"]


def test_e2e_co_du_kien_van_chay_binh_thuong(monkeypatch):
    """Chống chặn oan end-to-end."""
    from app.evaluation.authenticity_fixtures import _algo_cfg

    monkeypatch.setattr(pipeline, "call_gemini", _fake([
        json.dumps(_analysis(goal="Tìm giá trị lớn nhất")),
        json.dumps(_classify("algorithm.find_max")),
        _algo_cfg([12, 7, 25], summary="Tìm giá trị lớn nhất"),
    ]))
    env = asyncio.run(pipeline.run_pipeline("Cho dãy 12, 7, 25. Tìm số lớn nhất.", "k"))
    assert env["status"] == "ok" and env["simulation_id"] == "algorithm.find_max"
