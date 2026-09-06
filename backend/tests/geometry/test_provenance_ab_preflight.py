# -*- coding: utf-8 -*-
"""TIỀN KIỂM NỀN ĐO cho `PROVENANCE_AFFORDANCE_AB_4_LUOT`. **0 lượt gọi model.**

Phải xanh **TRƯỚC** bốn lượt live. Nền đo không tự đứng được thì con số lượt
live không nói lên điều gì — tiền lệ đã trả giá một lần
(`V3_LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL`).

Hai gold, viết theo đúng đặc tả wave (gốc toạ độ dùng **`model_assumption`**,
khác gold của corpus vốn dùng `source_fact_id`):

    RATIO     `CD = 10` · `CN:ND = 2:3` · dựng `N = divide_segment(C,D,2/5)` · `ND = 6`
    MULTIPLE  `EF = 10` · `FP = 4·PE`  · dựng `P = divide_segment(E,F,1/5)` · `PF = 8`

Bốn phản ví dụ khoá bốn cổng đã dựng qua ba wave trước — nếu một trong bốn
lỏng ra thì lượt live sẽ đo trên một nền khác với nền đã mô tả.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from app.ai.pipeline import _dung_scene3d
from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program import segment_relation as SR
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

GOC = Path(__file__).resolve().parents[2]
if str(GOC / "scripts") not in sys.path:
    sys.path.insert(0, str(GOC / "scripts"))

from gold_ratio_ab import CORPUS  # noqa: E402

CA = {c["case_id"]: c for c in CORPUS}
RATIO, MULTIPLE = "r2", "r3"
LY_DO = ("Đặt hệ trục: chọn điểm này làm gốc toạ độ vì đề không cho toạ độ; "
         "trục Ox dọc theo đoạn thẳng đã cho.")

#: `(ca, gốc, đầu kia, điểm dẫn xuất, t, witness, đáp số)`
BO = {
    RATIO: ("C", "D", "N", "2/5", "do_dai_nd", "6"),
    MULTIPLE: ("E", "F", "P", "1/5", "do_dai_pf", "8"),
}


def _hd(cid: str) -> RequestContract:
    """Hợp đồng cố định + source invariants, y như `build_request_contract`."""
    rc = RequestContract.model_validate(CA[cid]["request_contract"])
    return rc.model_copy(update={"source_invariants": (
        SR.bat_bien_do_dai(rc, rc.problem_text)
        + SR.bat_bien_chia_doan(rc, rc.problem_text))})


def _gold(cid: str) -> dict:
    """Gold ĐÚNG ĐẶC TẢ WAVE: gốc toạ độ đi kênh `model_assumption`."""
    goc, kia, diem, t, _, _ = BO[cid]
    p = json.loads(json.dumps(CA[cid]["gold"]))
    for m in p["memory_declarations"]:
        if m["name"] == goc:
            m.pop("source_fact_id", None)
            m["model_assumption"] = LY_DO
    for s in p["statements"]:
        if s.get("target_var") == diem:
            s["expr"] = {"kind": "divide_segment", "a": goc, "b": kia,
                         "ratio": t}
    return p


def _chay(cid: str, p: dict):
    return verify_and_compile(_hd(cid), SemanticProgramSpec.model_validate(p))


def _dl(oc):
    return {k: display(v) for k, v in (oc.final_memory or {}).items()
            if is_exact_number(v)}


def _sua(cid: str, **doi) -> dict:
    p = _gold(cid)
    for m in p["memory_declarations"]:
        if m["name"] in doi:
            for k, v in doi[m["name"]].items():
                if v is None:
                    m.pop(k, None)
                else:
                    m[k] = v
    return p


# ══ A · HAI GOLD ĐI TRỌN MỌI TẦNG ════════════════════════════════════════
@pytest.mark.parametrize("cid", [RATIO, MULTIPLE])
def test_A1_gold_served_va_dap_so_chinh_xac(cid):
    _, _, _, _, wit, dap = BO[cid]
    oc = _chay(cid, _gold(cid))
    assert oc.stage_reached == "served", oc.details
    assert oc.servable is True
    assert _dl(oc)[wit] == dap


@pytest.mark.parametrize("cid", [RATIO, MULTIPLE])
def test_A2_gold_qua_grounding_va_source_invariant(cid):
    """Hai tầng này là thứ ba wave trước dựng lên — phải còn nguyên."""
    oc = _chay(cid, _gold(cid))
    assert oc.stage_reached not in ("grounding", "source_invariant")
    bt = _hd(cid).source_invariants
    assert {b.kind for b in bt} == {"segment_length", SR.KIND}


@pytest.mark.parametrize("cid", [RATIO, MULTIPLE])
def test_A3_gold_co_BUOC_DUNG_trong_scene_va_dependency(cid):
    goc, kia, diem, _, _, _ = BO[cid]
    p = _gold(cid)
    sp = SemanticProgramSpec.model_validate(p)
    assert verify_and_compile(_hd(cid), sp).stage_reached == "served"
    objs = (_dung_scene3d(sp, _hd(cid)) or {}).get("objects") or []
    M = [o for o in objs if str(o.get("id")) == diem]
    assert M, [o.get("id") for o in objs]
    assert M[0].get("origin") == "derived"
    assert M[0].get("producer") == "construct_point.divide_segment"
    assert {goc, kia} <= set(M[0].get("depends") or [])


@pytest.mark.parametrize("cid", [RATIO, MULTIPLE])
def test_A4_gold_co_su_kien_sinh_diem_trong_trace(cid):
    _, _, diem, _, _, _ = BO[cid]
    p = _gold(cid)
    sp = SemanticProgramSpec.model_validate(p)
    canh = _dung_scene3d(sp, _hd(cid)) or {}
    sk = canh.get("events") or []
    assert any(diem in json.dumps(e, ensure_ascii=False) for e in sk), sk


# ══ B · BỐN PHẢN VÍ DỤ — bốn cổng phải còn chặt ══════════════════════════
@pytest.mark.parametrize("cid", [RATIO, MULTIPLE])
def test_B1_goc_toa_do_THIEU_ca_hai_kenh_bi_grounding_chan(cid):
    goc = BO[cid][0]
    oc = _chay(cid, _sua(cid, **{goc: {"model_assumption": None,
                                       "source_fact_id": None}}))
    assert oc.servable is False and oc.stage_reached == "grounding"


@pytest.mark.parametrize("cid", [RATIO, MULTIPLE])
def test_B2_diem_dan_xuat_khai_thang_toa_do_bi_chan(cid):
    """`model_assumption` KHÔNG hợp thức hoá được một điểm dẫn xuất."""
    goc, _, diem, _, _, _ = BO[cid]
    toa_do = [4, 0, 0] if cid == RATIO else [2, 0, 0]
    p = _sua(cid, **{diem: {"initial_value": toa_do,
                            "model_assumption": LY_DO,
                            "source_fact_id": None}})
    p["statements"] = [s for s in p["statements"]
                       if s.get("target_var") != diem]
    oc = _chay(cid, p)
    assert oc.servable is False and oc.stage_reached == "grounding"
    assert any("DERIVED_ENTITY_WITHOUT_PRODUCER" in str(x)
               for x in (oc.details or []))


@pytest.mark.parametrize("cid", [RATIO, MULTIPLE])
def test_B3_toa_do_TRAI_do_dai_de_cho_bi_source_invariant_chan(cid):
    """`model_assumption` KHÔNG hợp thức hoá được toạ độ trái dữ kiện."""
    kia = BO[cid][1]
    p = _sua(cid, **{kia: {"initial_value": [99, 0, 0],
                           "model_assumption": LY_DO,
                           "source_fact_id": None}})
    oc = _chay(cid, p)
    assert oc.servable is False and oc.stage_reached == "source_invariant"


@pytest.mark.parametrize("cid,t_sai", [(RATIO, "1/2"), (MULTIPLE, "1/4")])
def test_B4_ratio_SAI_trong_doan_bi_source_invariant_chan(cid, t_sai):
    goc, kia, diem, _, _, _ = BO[cid]
    p = _gold(cid)
    for s in p["statements"]:
        if s.get("target_var") == diem:
            s["expr"]["ratio"] = t_sai
    oc = _chay(cid, p)
    assert oc.servable is False and oc.stage_reached == "source_invariant"


def test_B5_dao_chieu_toan_hang_van_duoc_nhan():
    """Nền đo phải nhận cách dựng tương đương — nếu không sẽ chấm oan lượt live."""
    for cid, t_dao in ((RATIO, "3/5"), (MULTIPLE, "4/5")):
        goc, kia, diem, _, wit, dap = BO[cid]
        p = _gold(cid)
        for s in p["statements"]:
            if s.get("target_var") == diem:
                s["expr"] = {"kind": "divide_segment", "a": kia, "b": goc,
                             "ratio": t_dao}
        oc = _chay(cid, p)
        assert oc.stage_reached == "served", (cid, oc.details)
        assert _dl(oc)[wit] == dap
