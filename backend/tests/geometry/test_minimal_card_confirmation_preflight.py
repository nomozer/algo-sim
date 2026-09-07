# -*- coding: utf-8 -*-
"""TIỀN KIỂM NỀN ĐO cho `MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION`.

**0 lượt gọi model.** Phải xanh **TRƯỚC** bốn lượt live: nền đo không tự đứng
được thì con số lượt live không nói lên điều gì — kho này đã trả giá một lần
(`V3_LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL`).

Hai gold viết đúng đặc tả wave — gốc toạ độ đi kênh **`model_assumption`**,
đúng thứ mà dòng xuất xứ của thẻ C hướng tới:

    F1  `AB = 18` · `AM:MB = 5:4` · `M = divide_segment(A,B,5/9)` · `MB = 8`
    F2  `GH = 14` · `KH = 2·GK`   · `K = divide_segment(G,H,1/3)` · `KH = 28/3`

`F2` là ca duy nhất trong toàn bộ chuỗi wave có **đáp số hữu tỉ không nguyên**.
Nó ở đây để một phép làm tròn ẩn không thể đi qua mà không ai thấy.
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

from gold_minimal_card_confirmation import (  # noqa: E402
    BO, CORPUS, LY_DO_GOC,
)

CA = {c["case_id"]: c for c in CORPUS}
F1, F2 = "f1", "f2"


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
            m["model_assumption"] = LY_DO_GOC
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
@pytest.mark.parametrize("cid", [F1, F2])
def test_A1_gold_served_va_dap_so_chinh_xac(cid):
    _, _, _, _, wit, dap = BO[cid]
    oc = _chay(cid, _gold(cid))
    assert oc.stage_reached == "served", oc.details
    assert oc.servable is True
    assert _dl(oc)[wit] == dap


@pytest.mark.parametrize("cid", [F1, F2])
def test_A2_gold_qua_grounding_va_source_invariant(cid):
    oc = _chay(cid, _gold(cid))
    assert oc.stage_reached not in ("grounding", "source_invariant")
    bt = _hd(cid).source_invariants
    assert {b.kind for b in bt} == {"segment_length", SR.KIND}, (
        "thiếu một trong hai bất biến nguồn ⇒ phép đo sẽ báo served cho đúng "
        "lớp chương trình mà sản phẩm đang từ chối")


@pytest.mark.parametrize("cid", [F1, F2])
def test_A3_gold_co_BUOC_DUNG_trong_scene_va_dependency(cid):
    goc, kia, diem, _, _, _ = BO[cid]
    sp = SemanticProgramSpec.model_validate(_gold(cid))
    assert verify_and_compile(_hd(cid), sp).stage_reached == "served"
    objs = (_dung_scene3d(sp, _hd(cid)) or {}).get("objects") or []
    M = [o for o in objs if str(o.get("id")) == diem]
    assert M, [o.get("id") for o in objs]
    assert M[0].get("origin") == "derived"
    assert M[0].get("producer") == "construct_point.divide_segment"
    assert {goc, kia} <= set(M[0].get("depends") or [])


@pytest.mark.parametrize("cid", [F1, F2])
def test_A4_gold_co_su_kien_sinh_diem_trong_trace(cid):
    diem = BO[cid][2]
    sp = SemanticProgramSpec.model_validate(_gold(cid))
    sk = (_dung_scene3d(sp, _hd(cid)) or {}).get("events") or []
    assert any(diem in json.dumps(e, ensure_ascii=False) for e in sk), sk


def test_A5_F2_dap_so_la_HUU_TI_KHONG_NGUYEN():
    """Ca chống làm tròn — nếu ở đâu đó đi qua float, nó lộ ra ở đây."""
    oc = _chay(F2, _gold(F2))
    assert _dl(oc)["do_dai_kh"] == "28/3"
    assert "." not in _dl(oc)["do_dai_kh"]


# ══ B · BỐN PHẢN VÍ DỤ — bốn cổng phải còn chặt ══════════════════════════
@pytest.mark.parametrize("cid,t_sai", [(F1, "1/2"), (F2, "1/4")])
def test_B1_ratio_SAI_trong_doan_bi_source_invariant_chan(cid, t_sai):
    """Sai nhưng VẪN NẰM TRONG đoạn — không cổng hình học nào bắt được,
    chỉ bất biến nguồn bắt."""
    diem = BO[cid][2]
    p = _gold(cid)
    for s in p["statements"]:
        if s.get("target_var") == diem:
            s["expr"]["ratio"] = t_sai
    oc = _chay(cid, p)
    assert oc.servable is False and oc.stage_reached == "source_invariant"


@pytest.mark.parametrize("cid", [F1, F2])
def test_B2_diem_dan_xuat_khai_san_toa_do_bi_grounding_chan(cid):
    goc, _, diem, _, _, _ = BO[cid]
    toa_do = [10, 0, 0] if cid == F1 else [14, 0, 0]
    p = _sua(cid, **{diem: {"initial_value": toa_do,
                            "model_assumption": LY_DO_GOC,
                            "source_fact_id": None}})
    p["statements"] = [s for s in p["statements"]
                       if s.get("target_var") != diem]
    oc = _chay(cid, p)
    assert oc.servable is False and oc.stage_reached == "grounding"
    assert any("DERIVED_ENTITY_WITHOUT_PRODUCER" in str(x)
               for x in (oc.details or []))


@pytest.mark.parametrize("cid", [F1, F2])
def test_B3_toa_do_dau_mut_TRAI_do_dai_de_cho_bi_chan(cid):
    kia = BO[cid][1]
    p = _sua(cid, **{kia: {"initial_value": [99, 0, 0],
                           "model_assumption": LY_DO_GOC,
                           "source_fact_id": None}})
    oc = _chay(cid, p)
    assert oc.servable is False and oc.stage_reached == "source_invariant"


@pytest.mark.parametrize("cid,t_dao", [(F1, "4/9"), (F2, "2/3")])
def test_B4_dao_chieu_toan_hang_tuong_duong_VAN_duoc_nhan(cid, t_dao):
    """Nền đo phải nhận cách dựng tương đương — nếu không sẽ chấm oan lượt live."""
    goc, kia, diem, _, wit, dap = BO[cid]
    p = _gold(cid)
    for s in p["statements"]:
        if s.get("target_var") == diem:
            s["expr"] = {"kind": "divide_segment", "a": kia, "b": goc,
                         "ratio": t_dao}
    oc = _chay(cid, p)
    assert oc.stage_reached == "served", (cid, oc.details)
    assert _dl(oc)[wit] == dap


# ══ C · GỐC TOẠ ĐỘ THIẾU XUẤT XỨ — cổng của wave provenance ═════════════
@pytest.mark.parametrize("cid", [F1, F2])
def test_C1_goc_toa_do_THIEU_ca_hai_kenh_bi_grounding_chan(cid):
    goc = BO[cid][0]
    oc = _chay(cid, _sua(cid, **{goc: {"model_assumption": None,
                                       "source_fact_id": None}}))
    assert oc.servable is False and oc.stage_reached == "grounding"


# ══ D · ĐỀ MỚI THẬT ══════════════════════════════════════════════════════
def test_D1_hai_de_CHUA_TUNG_xuat_hien_trong_corpus_cu():
    from gold_ratio_ab import CORPUS as CU

    cu = {c["problem_text"] for c in CU}
    for c in CORPUS:
        assert c["problem_text"] not in cu, c["case_id"]


def test_D2_oracle_khop_dinh_nghia_chia_doan():
    """`t` phải nhất quán với đáp số — kiểm bằng số học, không bằng niềm tin."""
    from fractions import Fraction

    for cid, dai in ((F1, 18), (F2, 14)):
        _, _, _, t, wit, dap = BO[cid]
        # điểm chia ở `t` tính từ gốc ⇒ khoảng cách tới ĐẦU KIA = (1-t)·dài
        assert Fraction(dap) == (1 - Fraction(t)) * dai, (cid, wit)
