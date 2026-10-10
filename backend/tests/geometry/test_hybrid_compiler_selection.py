"""hybrid-compiler-selection — nhánh B (AI trích dữ kiện có kiểu → planner chọn hàm) so với nhánh A (AI chọn hàm). 0 API call.

Ca holdout tiền đăng ký (`f6b1a551`, TRƯỚC planner): `fixtures/hybrid_holdout_cases.json` — lời gọi A và dữ kiện B đều viết tay
(AI trích ĐÚNG giả định), kỳ vọng + hạng riêng từng nhánh, oracle tay độc lập. 58 ca cũ: dữ kiện B chuyển CƠ HỌC từ lời gọi A
(`scripts/hybrid_ab_offline.py::facts_from_calls`) ⇒ chỉ kiểm PARITY, không kiểm tổng quát hoá. Không gì ở đây đo năng lực Gemini.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.ai import fact_extraction as FE
from app.ai import function_route as FR
from app.simulation.geometry_functions import engine as EN
from app.simulation.geometry_functions import planner as PL

FX = Path(__file__).parent / "fixtures"
HOLD = {c["id"]: c for c in json.loads((FX / "hybrid_holdout_cases.json").read_text(encoding="utf-8"))["cases"]}
LEGACY = [c for f in ("text_to_functions_cases.json", "paraphrase_cases.json", "geometry_expansion_cases.json")
          for c in json.loads((FX / f).read_text(encoding="utf-8"))["cases"]]

_sp = importlib.util.spec_from_file_location("_t_hab", Path(__file__).resolve().parents[2] / "scripts" / "hybrid_ab_offline.py")
AB = importlib.util.module_from_spec(_sp)
sys.modules[_sp.name] = AB
_sp.loader.exec_module(AB)


def _len_sq(scene, a, b):
    P = {o["id"]: tuple(F(x) for x in o["xyz"]) for o in scene["objects"] if o["type"] == "point3" and "xyz" in o}
    G = [[F(x) for x in r] for r in scene["chart_metric"]]
    d = [P[EN.ir_name(b)][i] - P[EN.ir_name(a)][i] for i in range(3)]
    return sum(d[i] * G[i][j] * d[j] for i in range(3) for j in range(3))


def _kiem(e, r, ten):
    assert r.status == e["status"], (ten, r.code, r.reason)
    if r.status == "REFUSED":
        assert r.code == e["code"], (ten, r.code, r.reason)
        assert r.scene3d is None and not r.answers
        return
    assert AB.dap_so_khop(e["answers"], r), (ten, r.answers, r.answer_exact)
    for seg, v in {**e.get("lengths_sq", {}), **e.get("lengths_sq_in_a2", {})}.items():
        a, b = re.findall(r"[A-Z]'?", seg)
        assert _len_sq(r.scene3d, a, b) == F(v), (ten, seg)
    for fid, kq in (e.get("goal_checks") or {}).items():
        assert r.planner["goal_checks"][fid] == kq, (ten, fid, r.planner["goal_checks"])


# ── holdout: hai nhánh, kỳ vọng riêng ────────────────────────────────────────
@pytest.mark.parametrize("cid", sorted(HOLD))
def test_holdout_nhanh_A(cid):
    c = HOLD[cid]
    _kiem(c["expect_a"], FR.run_function_route(c["text"], {"calls": c["a_calls"]}), cid + "/A")


@pytest.mark.parametrize("cid", sorted(HOLD))
def test_holdout_nhanh_B(cid):
    c = HOLD[cid]
    _kiem(c["expect_b"], FR.run_fact_route(c["text"], {"facts": c["b_facts"]}), cid + "/B")


def test_hang_phan_loai_dung_tien_dang_ky():
    for c in HOLD.values():
        ra = FR.run_function_route(c["text"], {"calls": c["a_calls"]})
        rb = FR.run_fact_route(c["text"], {"facts": c["b_facts"]})
        assert AB.phan_hang(c["expect_a"], c["class_a"], ra) == c["class_a"], c["id"]
        assert AB.phan_hang(c["expect_b"], c["class_b"], rb) == c["class_b"], c["id"]


# ── parity trên 58 ca cũ (dữ kiện chuyển cơ học) ─────────────────────────────
@pytest.mark.parametrize("i", range(len(LEGACY)))
def test_parity_58_ca_cu(i):
    c = LEGACY[i]
    ra = FR.run_function_route(c["text"], {"calls": c["calls"]})
    rb = FR.run_fact_route(c["text"], {"facts": AB.facts_from_calls(c["calls"])})
    assert (rb.status, rb.code) == (ra.status, ra.code), (c["id"], rb.code, rb.reason, ra.code)
    if ra.status == "SERVED":
        assert {k: AB.khoa_dap_so(v) for k, v in ra.answers.items()} == {k: AB.khoa_dap_so(v) for k, v in rb.answers.items()}, c["id"]


# ── planner: luật riêng của nhánh B ───────────────────────────────────────────
def _f(cid):
    return copy.deepcopy(HOLD[cid]["b_facts"])


def test_planner_chon_ham_tu_loai_quan_he():
    """Cùng loại dữ kiện `perpendicular`, planner chọn hàm theo KIỂU toán hạng: đường–mặt, mặt bên–đáy."""
    k = PL.lap_ke_hoach({"facts": _f("H04_FACE_PERP_MIDPOINT_FOOT")})
    assert any(c["fn"] == "face_perpendicular_base" for c in k.calls)
    k = PL.lap_ke_hoach({"facts": _f("H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED")})
    assert [c["fn"] for c in k.calls if c["id"] == "f4"] == ["perpendicular_line_plane"]


def test_planner_khong_dung_dieu_phai_chung_minh_lam_tien_de():
    k = PL.lap_ke_hoach({"facts": _f("H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED")})
    assert not any(c["id"].startswith("f7") for c in k.calls)
    assert [g["fact"] for g in k.goals] == ["f7"]


def test_planner_mo_rong_dinh_nghia_va_vai_tro_do_dai():
    k = PL.lap_ke_hoach({"facts": _f("H14_REGULAR_TETRAHEDRON")})
    fns = sorted(c["fn"] for c in k.calls)
    assert fns == sorted(["regular_pyramid", "regular_polygon", "segment_length", "ask_volume"]), fns
    k = PL.lap_ke_hoach({"facts": _f("H03_REGULAR_SQUARE_PYRAMID_ROLE_LENGTHS")})
    canh_ben = [c for c in k.calls if c["fn"] == "segment_length"]
    assert canh_ben and canh_ben[0]["args"]["segment"] == ["S", "A"]


def test_canh_ben_chop_khong_deu_la_tham_chieu_mo_ho():
    f = _f("H06_QUANTITY_NOT_UNIQUE")
    f[1].update(measure="lateral_edge", points=None, solid="S.ABC")
    r = FR.run_fact_route(HOLD["H06_QUANTITY_NOT_UNIQUE"]["text"], {"facts": f})
    assert (r.status, r.code) == ("REFUSED", "AMBIGUOUS_REFERENCE")


@pytest.mark.parametrize("sua,ma", [
    ({"ambiguous": True}, "AMBIGUOUS_FACT"),
    ({"role": "condition"}, "CONDITIONAL_CLAUSE"),
    ({"kind": "tangent"}, "SCHEMA_INVALID"),
    ({"points_a": None}, "FACT_INCOMPLETE"),
])
def test_planner_tu_choi_co_ma(sua, ma):
    f = _f("H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED")
    f[3].update(sua)
    r = FR.run_fact_route(HOLD["H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED"]["text"], {"facts": f})
    assert (r.status, r.code) == ("REFUSED", ma), r.reason


def test_planner_co_tran_loi_goi():
    f = _f("H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED")
    them = [dict(f[1], id=f"x{i}") for i in range(PL.MAX_CALLS + 1)]
    r = FR.run_fact_route(HOLD["H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED"]["text"], {"facts": f + them})
    assert r.code == "PLAN_TOO_LARGE"


def test_dieu_phai_chung_minh_sai_thi_tu_choi():
    f = _f("H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED")
    f[6].update(points_a=["A", "C"], quotes=["BC vuông góc với (SAB)"])         # AC ⊥ (SAB) — sai trong hình
    r = FR.run_fact_route(HOLD["H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED"]["text"], {"facts": f})
    assert (r.status, r.code) == ("REFUSED", "PROOF_GOAL_FALSE"), r.reason


def test_hinh_khong_duy_nhat_khong_lay_mau():
    """Không chọn đại một vị trí đỉnh: H05 từ chối kể cả khi V bất biến, và ghi rõ vì sao."""
    r = FR.run_fact_route(HOLD["H05_FIGURE_NOT_UNIQUE_QUANTITY_UNIQUE"]["text"],
                          {"facts": _f("H05_FIGURE_NOT_UNIQUE_QUANTITY_UNIQUE")})
    assert r.code == "FIGURE_NOT_UNIQUE" and r.scene3d is None and "⅓" in r.reason
    assert r.details.get("quantity_invariant") == "volume = ⅓·S_đáy·h"


# ── adapter dữ kiện (provider giả) ───────────────────────────────────────────
def _body(facts, finish="STOP"):
    return {"candidates": [{"content": {"role": "model", "parts": [{"text": json.dumps({"facts": facts}, ensure_ascii=False)}]},
                            "finishReason": finish}],
            "usageMetadata": {"promptTokenCount": 900, "candidatesTokenCount": 400, "totalTokenCount": 1300}}


class _Gia:
    def __init__(self, body):
        self.body, self.goi = body, 0

    def __call__(self, payload):
        self.goi += 1
        self.payload = payload
        return copy.deepcopy(self.body)


def test_payload_du_kien_dung_tap_con_openapi_va_khong_khai_ham():
    p = FE.build_request("đề")
    gc = p["generationConfig"]
    assert gc["responseMimeType"] == "application/json" and gc["maxOutputTokens"] == FE.MAX_OUTPUT_TOKENS
    txt = json.dumps(gc["responseSchema"])
    for cam in ('"$ref"', '"anyOf"', '"title"', '"additionalProperties"', '"xyz"', '"coord'):
        assert cam not in txt, cam
    assert "tools" not in p                                            # nhánh B KHÔNG đưa thư viện hàm cho mô hình
    assert all(t.isupper() for t in re.findall(r'"type": "([^"]+)"', txt))


@pytest.mark.parametrize("cid", ["H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED", "H11_SKEW_DISTANCE_COMPOSITION", "H13_NEGATED_RELATION_CONTRADICTS"])
def test_adapter_du_kien_dau_cuoi(cid):
    c = HOLD[cid]
    gia = _Gia(_body(c["b_facts"]))
    r = FE.run_ai_fact_route(c["text"], gia)
    assert gia.goi == 1
    _kiem(c["expect_b"], r, cid)


def test_adapter_du_kien_tu_choi_phan_hoi_hong():
    c = HOLD["H01_CUBE"]
    assert FE.run_ai_fact_route(c["text"], _Gia(_body(c["b_facts"], "MAX_TOKENS"))).code == "RESPONSE_TRUNCATED"
    assert FE.run_ai_fact_route(c["text"], _Gia({"candidates": []})).code == "NO_CANDIDATE"
    hong = _body(c["b_facts"])
    hong["candidates"][0]["content"]["parts"][0]["text"] = "{facts: ["
    assert FE.run_ai_fact_route(c["text"], _Gia(hong)).code == "JSON_INVALID"
    assert FE.run_ai_fact_route(c["text"], _Gia(_body(c["b_facts"], "SAFETY"))).code == "PROVIDER_REFUSED"


def test_khong_lui_ve_llm_only(monkeypatch):
    from app.ai import gemini, pipeline

    def cam(*a, **k):
        raise AssertionError("đã chạm LLM_ONLY/provider")

    monkeypatch.setattr(gemini, "call_gemini", cam)
    monkeypatch.setattr(pipeline, "run_pipeline", cam)
    for c in HOLD.values():
        FE.run_ai_fact_route(c["text"], _Gia(_body(c["b_facts"])))
