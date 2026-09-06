# -*- coding: utf-8 -*-
"""ĐIỂM DẪN XUẤT PHẢI ĐƯỢC DỰNG, KHÔNG ĐƯỢC KHAI THẲNG TOẠ ĐỘ.

    `DERIVED_POINT_CONSTRUCTION_ENFORCEMENT`, 2026-09-07. **0 lượt gọi model.**

Lỗ đã đo (`FRAME_ORIGIN_PROVENANCE_AFFORDANCE` phản ví dụ ⓐ): đề
*"EF = 10; P thuộc EF; FP = 4·PE"*, chương trình khai thẳng toạ độ `P`, **bỏ
câu lệnh dựng**, còn đúng MỘT câu lệnh, và vẫn `served` với đáp số **đúng**
(`8`). Đáp số đúng vì bất biến `segment_division` xác nhận vị trí — thứ mất là
**BƯỚC DỰNG**, tức đúng thứ đề tài hứa cho học sinh.

Ranh giới của wave, chốt trước khi sửa:

    điểm ĐẦU VÀO      đề cho toạ độ / dữ kiện tương ứng   → giữ nguyên quyền
    LỰA CHỌN HỆ TRỤC  đặt vị trí điểm đầu vào             → giữ nguyên quyền
    điểm DẪN XUẤT     vị trí do quan hệ chia đoạn ĐÃ GIẢI → **phải dựng**

Chỉ *"M thuộc AB"* thì **chưa đủ**: phải có quan hệ **giải được** ra `t`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from app.ai.pipeline import _dung_scene3d
from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program import grounding_gate as GG
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
LY_DO = "Đặt hệ trục: chọn điểm này làm gốc toạ độ; đề không cho toạ độ."


def _hd(cid: str) -> RequestContract:
    rc = RequestContract.model_validate(CA[cid]["request_contract"])
    return rc.model_copy(update={"source_invariants": (
        SR.bat_bien_do_dai(rc, rc.problem_text)
        + SR.bat_bien_chia_doan(rc, rc.problem_text))})


def _ct(cid: str, *, bo_lenh=(), lenh=None, **doi) -> dict:
    p = json.loads(json.dumps(CA[cid]["gold"]))
    for m in p["memory_declarations"]:
        if m["name"] in doi:
            for k, v in doi[m["name"]].items():
                if v is None:
                    m.pop(k, None)
                else:
                    m[k] = v
    if bo_lenh:
        p["statements"] = [s for s in p["statements"]
                           if s.get("target_var") not in bo_lenh]
    if lenh:
        p["statements"].insert(0, lenh)
    return p


def _chay(cid: str, p: dict):
    return verify_and_compile(_hd(cid), SemanticProgramSpec.model_validate(p))


def _dap(oc, cid):
    mem = {k: display(v) for k, v in (oc.final_memory or {}).items()
           if is_exact_number(v)}
    return mem.get(CA[cid]["witness"])


def _khong_dung(cid, diem="P"):
    """Chương trình khai thẳng toạ độ điểm dẫn xuất và BỎ phép dựng."""
    goc = "E" if cid == MULTIPLE else "C"
    toa_do = [2, 0, 0] if cid == MULTIPLE else [4, 0, 0]
    return _ct(cid, bo_lenh=(diem,),
               **{goc: {"source_fact_id": None, "model_assumption": LY_DO},
                  diem: {"initial_value": toa_do, "source_fact_id": None,
                         "model_assumption": LY_DO}})


# ══ A · CA THIẾU BƯỚC DỰNG BỊ CHẶN ═══════════════════════════════════════
@pytest.mark.parametrize("cid,diem", [(MULTIPLE, "P"), (RATIO, "N")])
def test_A1_khai_san_va_bo_phep_dung_thi_BI_CHAN(cid, diem):
    oc = _chay(cid, _khong_dung(cid, diem))
    assert oc.servable is False
    assert oc.stage_reached == "grounding"
    assert any("DERIVED_ENTITY_WITHOUT_PRODUCER" in str(x)
               for x in (oc.details or []))


def test_A2_bi_chan_DU_dap_so_van_dung():
    """Toạ độ khai sẵn là ĐÚNG (`PF` sẽ ra `8`) — vẫn bị chặn.

    Đây là cả điểm của wave: *"đáp số đúng"* và *"có bước dựng đúng"* là hai
    câu khác nhau, và hệ nay phân biệt được.
    """
    oc = _chay(MULTIPLE, _khong_dung(MULTIPLE))
    assert oc.servable is False
    assert _dap(oc, MULTIPLE) is None          # chưa tới tầng tính


def test_A3_thong_diep_neu_du_bon_thu():
    oc = _chay(MULTIPLE, _khong_dung(MULTIPLE))
    d = " ".join(str(x) for x in (oc.details or []))
    assert "P" in d                              # điểm cần dựng
    assert "QUAN HỆ CHIA ĐOẠN" in d              # quan hệ nguồn
    assert "HỆ QUẢ phải dựng ra" in d            # dữ liệu còn thiếu
    assert "divide_segment" in d                 # hướng sửa bằng cơ chế có sẵn


@pytest.mark.parametrize("kenh", [
    {"source_fact_id": None, "model_assumption": LY_DO},
    {"source_fact_id": "vi_tri_diem", "model_assumption": None},
    {"source_fact_id": "vi_tri_diem", "model_assumption": LY_DO},
])
def test_A4_CA_HAI_kenh_xuat_xu_deu_bi_chan(kenh):
    """Chốt ⑥ cũ chỉ chạy trong nhánh `model_assumption`; chốt ⑦ phải phủ cả hai."""
    p = _ct(MULTIPLE, bo_lenh=("P",),
            E={"source_fact_id": None, "model_assumption": LY_DO},
            P={"initial_value": [2, 0, 0], **kenh})
    oc = _chay(MULTIPLE, p)
    assert oc.servable is False and oc.stage_reached == "grounding"


# ══ B · CA DỰNG ĐÚNG VẪN ĐI TRỌN ═════════════════════════════════════════
@pytest.mark.parametrize("cid,a,b,t,dap", [
    (MULTIPLE, "E", "F", "1/5", "8"),
    (MULTIPLE, "F", "E", "4/5", "8"),      # ĐẢO CHIỀU — cùng một điểm
    (RATIO, "C", "D", "2/5", "6"),
    (RATIO, "D", "C", "3/5", "6"),
])
def test_B1_dung_bang_divide_segment_thi_served(cid, a, b, t, dap):
    diem = CA[cid]["diem_duoc_hoi"]
    goc = "E" if cid == MULTIPLE else "C"
    p = _ct(cid, bo_lenh=(diem,),
            lenh={"kind": "construct_point", "target_var": diem,
                  "expr": {"kind": "divide_segment", "a": a, "b": b,
                           "ratio": t}},
            **{goc: {"source_fact_id": None, "model_assumption": LY_DO}})
    oc = _chay(cid, p)
    assert oc.stage_reached == "served", oc.details
    assert _dap(oc, cid) == dap


def test_B2_dung_SAI_TI_LE_van_bi_source_invariant_chan():
    """Chốt ⑦ không thay bất biến — nó hỏi câu khác, và cả hai cùng phải đạt."""
    p = _ct(MULTIPLE, bo_lenh=("P",),
            lenh={"kind": "construct_point", "target_var": "P",
                  "expr": {"kind": "divide_segment", "a": "E", "b": "F",
                           "ratio": "1/4"}},
            E={"source_fact_id": None, "model_assumption": LY_DO})
    oc = _chay(MULTIPLE, p)
    assert oc.servable is False
    assert oc.stage_reached == "source_invariant"


def test_B3_khai_toa_do_NHUNG_van_co_lenh_dung_thi_qua():
    """Giá trị đến từ phép dựng ⇒ khai báo không gánh thông tin ⇒ không chặn."""
    p = _ct(MULTIPLE,
            E={"source_fact_id": None, "model_assumption": LY_DO},
            P={"initial_value": [2, 0, 0], "source_fact_id": None,
               "model_assumption": LY_DO})
    oc = _chay(MULTIPLE, p)
    assert oc.stage_reached == "served", oc.details
    assert _dap(oc, MULTIPLE) == "8"


# ══ C · CHỐNG BÁC OAN — ba lớp điểm giữ nguyên quyền ═════════════════════
def test_C1_diem_DAU_VAO_van_khai_toa_do_duoc():
    """`E`, `F` là hai đầu mút — điểm đầu vào, không phải hệ quả."""
    dx = GG._diem_phai_dung(_hd(MULTIPLE))
    assert "P" in dx and "E" not in dx and "F" not in dx


def test_C2_LUA_CHON_HE_TRUC_van_di_duoc():
    """Gốc toạ độ khai `model_assumption` ⇒ vẫn qua, y như trước wave."""
    oc = _chay(MULTIPLE, _ct(
        MULTIPLE, E={"source_fact_id": None, "model_assumption": LY_DO}))
    assert oc.stage_reached == "served", oc.details


def test_C3_quan_he_CHUA_GIAI_DUOC_thi_KHONG_bat_buoc_dung():
    """*"M thuộc AB"* mà chưa giải ra `t` ⇒ chưa đủ để kết luận M phải dựng.

    Ranh giới §2, và nó hẹp có chủ đích: `segment_division_unresolved` nghĩa
    là hệ mới thấy đề *nói về* một phép chia.
    """
    rc = RequestContract.model_validate(CA[MULTIPLE]["request_contract"])
    chua = SR.bat_bien_chia_doan(
        type("C", (), {"input_facts": (), "problem_text":
                       "Một mặt phẳng cắt PQ tại điểm T sao cho PT bằng 20."})(),
        None)
    assert [b.kind for b in chua] == [SR.KIND_CHUA_GIAI]
    assert GG._diem_phai_dung(rc.model_copy(
        update={"source_invariants": chua})) == frozenset()


def test_C4_hop_dong_KHONG_co_bat_bien_thi_khong_chan():
    """Hợp đồng dựng tay, không bất biến ⇒ hành vi y như trước wave."""
    rc = RequestContract.model_validate(CA[MULTIPLE]["request_contract"])
    assert GG._diem_phai_dung(rc) == frozenset()


def test_C5_HAI_DOAN_cung_xuat_hien_thi_rang_buoc_dung_bo_ba():
    de = ("Cho đoạn thẳng AB có độ dài 12. Điểm M nằm trên đoạn AB sao cho "
          "AM = 9. Cho đoạn thẳng CD có độ dài 10. Điểm N nằm trên đoạn CD "
          "sao cho CN : ND = 2 : 3.")

    class _C:
        input_facts, problem_text = (), de
    rc = RequestContract(problem_text=de,
                         source_invariants=SR.bat_bien_chia_doan(_C(), de))
    dx = GG._diem_phai_dung(rc)
    assert {"M", "N"} <= dx and not ({"A", "B", "C", "D"} & dx)


def test_C6_doi_TEN_va_doi_SO_thi_luat_van_chay():
    de = ("Cho đoạn thẳng XY có độ dài 35. Điểm Z nằm trên đoạn XY sao cho "
          "XZ = 15.")

    class _C:
        input_facts, problem_text = (), de
    rc = RequestContract(problem_text=de,
                         source_invariants=SR.bat_bien_chia_doan(_C(), de))
    assert "Z" in GG._diem_phai_dung(rc)


def test_C7_ba_duong_PRODUCER_GIA_deu_dong__moi_duong_MOT_tham_quyen():
    """§3 cảnh báo *"bí danh hoặc câu lệnh không liên quan không chứng minh
    được bước dựng"*. Đo từng đường thay vì gộp — và chốt ⑦ **không** cần nới:

        literal thẳng vào `P`        → `ir_static`  AMBIGUOUS_FIRST_BINDING
        bí danh sang điểm CÓ THẬT    → `source_invariant` (sai vị trí)
        bí danh qua điểm BỊA         → `grounding` ⑤ UNANCHORED_DERIVED_ASSUMPTION

    Ghi cả ba để lần sau khỏi mở rộng thừa: mỗi đường đã có chủ.
    """
    # ① literal — không suy ra kiểu hình học
    oc = _chay(MULTIPLE, _ct(
        MULTIPLE, bo_lenh=("P",),
        lenh={"kind": "assign", "target_var": "P",
              "expr": {"kind": "literal", "value": [2, 0, 0]}},
        E={"source_fact_id": None, "model_assumption": LY_DO}))
    assert oc.servable is False and oc.stage_reached == "ir_static"

    # ② bí danh sang một điểm CÓ THẬT — producer hợp lệ, nhưng SAI VỊ TRÍ
    oc = _chay(MULTIPLE, _ct(
        MULTIPLE, bo_lenh=("P",),
        lenh={"kind": "assign", "target_var": "P",
              "expr": {"kind": "var", "name": "E"}},
        E={"source_fact_id": None, "model_assumption": LY_DO}))
    assert oc.servable is False and oc.stage_reached == "source_invariant"

    # ③ bí danh qua một điểm BỊA đặt sẵn đúng vị trí — chốt ⑤ bác điểm bịa
    p = _ct(MULTIPLE, bo_lenh=("P",),
            lenh={"kind": "assign", "target_var": "P",
                  "expr": {"kind": "var", "name": "Q"}},
            E={"source_fact_id": None, "model_assumption": LY_DO})
    p["memory_declarations"].append(
        {"name": "Q", "type": "point3", "initial_value": [2, 0, 0],
         "model_assumption": LY_DO})
    oc = _chay(MULTIPLE, p)
    assert oc.servable is False and oc.stage_reached == "grounding"
    assert any("UNANCHORED_DERIVED_ASSUMPTION" in str(x)
               for x in (oc.details or []))


# ══ D · TRACE · PRODUCER · DEPENDENCY của ca đúng ════════════════════════
def test_D1_ca_dung_co_buoc_sinh_diem_trong_trace_va_scene():
    p = _ct(MULTIPLE, E={"source_fact_id": None, "model_assumption": LY_DO})
    sp = SemanticProgramSpec.model_validate(p)
    oc = verify_and_compile(_hd(MULTIPLE), sp)
    assert oc.stage_reached == "served", oc.details

    canh = _dung_scene3d(sp, _hd(MULTIPLE)) or {}
    objs = canh.get("objects") or []
    P = [o for o in objs if str(o.get("id")) == "P"]
    assert P, [o.get("id") for o in objs]
    # BƯỚC SINH: `P` là vật DẪN XUẤT, producer là đúng phép dựng của IR.
    assert P[0].get("origin") == "derived"
    assert P[0].get("producer") == "construct_point.divide_segment"
    # CHUỖI PHỤ THUỘC tới HAI đầu mút được giữ.
    assert {"E", "F"} <= set(P[0].get("depends") or [])


def test_D2_ca_THIEU_buoc_dung_khong_bao_gio_toi_scene():
    oc = _chay(MULTIPLE, _khong_dung(MULTIPLE))
    assert oc.stage_reached == "grounding"     # dừng TRƯỚC execution
    assert not (oc.final_memory or {})


# ══ E · PHÉP TIÊM ════════════════════════════════════════════════════════
def test_E1_TIEM_ngat_tin_hieu_thi_ca_khai_san_LOT_LAI(monkeypatch):
    """Guard chưa từng đỏ là guard chưa được chứng minh."""
    monkeypatch.setattr(GG, "_diem_phai_dung", lambda contract: frozenset())
    oc = _chay(MULTIPLE, _khong_dung(MULTIPLE))
    assert oc.stage_reached == "served"
    assert _dap(oc, MULTIPLE) == "8"            # đúng lỗ cũ, đúng đáp số cũ
