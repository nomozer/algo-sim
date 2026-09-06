# -*- coding: utf-8 -*-
"""XUẤT XỨ KHI CHỌN GỐC TOẠ ĐỘ, và ĐỘ DÀI ĐỀ CHO PHẢI ĐƯỢC KIỂM.

    `FRAME_ORIGIN_PROVENANCE_AFFORDANCE`, 2026-09-07. **0 lượt gọi model.**

Wave này bắt đầu bằng một câu hỏi về affordance — *"hướng dẫn ngắn có giúp AI
khai đúng xuất xứ gốc toạ độ không"* — và **dừng phần live ở 0 lượt gọi** vì
replay tất định tìm ra một lỗ kiểm chứng nghiêm trọng hơn (§2 của brief:
*"nếu replay phát hiện lỗ kiểm chứng mới, kết thúc phần live"*).

Hai điều replay chứng minh:

  ① **Kênh xuất xứ đã đủ.** Chỉ cần MỘT trong hai trường trên khai báo gốc
    toạ độ — `model_assumption` **hoặc** `source_fact_id` — là chương trình
    qua grounding. Không cần trường mới, không cần đổi hợp đồng.

  ② **Nhưng độ dài đề cho KHÔNG được kiểm.** `EF = 10`, chương trình khai
    `F = [99,0,0]` kèm `model_assumption` hợp lệ, chia đoạn đúng tỉ lệ ⇒ hệ
    **`served`** với `396/5` thay vì `8`. Checker `segment_length` vốn hỏi
    đúng câu ấy và chạy đúng — nó chỉ chưa bao giờ được phát cho đề cho SỐ.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program import segment_relation as SR
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
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
    """Hợp đồng + CẢ HAI loại bất biến, đúng thứ tự đường sản phẩm."""
    rc = RequestContract.model_validate(CA[cid]["request_contract"])
    bt = (SR.bat_bien_do_dai(rc, rc.problem_text)
          + SR.bat_bien_chia_doan(rc, rc.problem_text))
    return rc.model_copy(update={"source_invariants": bt})


def _ct(cid: str, **doi) -> dict:
    """Gold, rồi áp các sửa đổi lên khai báo theo tên."""
    p = json.loads(json.dumps(CA[cid]["gold"]))
    for m in p["memory_declarations"]:
        if m["name"] in doi:
            for k, v in doi[m["name"]].items():
                if v is None:
                    m.pop(k, None)
                else:
                    m[k] = v
    return p


def _chay(cid: str, p: dict):
    return verify_and_compile(_hd(cid), SemanticProgramSpec.model_validate(p))


def _dap(oc, cid):
    mem = {k: display(v) for k, v in (oc.final_memory or {}).items()
           if is_exact_number(v)}
    return mem.get(CA[cid]["witness"])


# ══ A · KÊNH XUẤT XỨ — MỘT TRƯỜNG LÀ ĐỦ ══════════════════════════════════
@pytest.mark.parametrize("cid,goc,dap", [(RATIO, "C", "6"), (MULTIPLE, "E", "8")])
def test_A1_khong_khai_gi_thi_grounding_BAC(cid, goc, dap):
    oc = _chay(cid, _ct(cid, **{goc: {"source_fact_id": None,
                                      "model_assumption": None}}))
    assert oc.stage_reached == "grounding"
    assert any("thiếu source_fact_id" in str(x) for x in (oc.details or []))


@pytest.mark.parametrize("cid,goc,dap", [(RATIO, "C", "6"), (MULTIPLE, "E", "8")])
def test_A2_CHI_model_assumption_la_DU(cid, goc, dap):
    """Kênh *"đây là cách tôi đặt hệ trục"* — có sẵn, và nó đủ."""
    oc = _chay(cid, _ct(cid, **{goc: {"source_fact_id": None,
                                      "model_assumption": LY_DO}}))
    assert oc.stage_reached == "served", oc.details
    assert _dap(oc, cid) == dap


@pytest.mark.parametrize("cid,goc,dap", [(RATIO, "C", "6"), (MULTIPLE, "E", "8")])
def test_A3_CHI_source_fact_id_cung_DU(cid, goc, dap):
    oc = _chay(cid, _ct(cid, **{goc: {"source_fact_id": "doan_thang",
                                      "model_assumption": None}}))
    assert oc.stage_reached == "served", oc.details
    assert _dap(oc, cid) == dap


def test_A4_khong_can_TRUONG_MOI_nao():
    """Kết luận của replay: hợp đồng hiện tại đã đủ, không mở trường mới."""
    from app.simulation.semantic_program.contract import MemoryDeclaration
    assert {"source_fact_id", "model_assumption"} <= set(
        MemoryDeclaration.model_fields)


# ══ B · ĐỘ DÀI ĐỀ CHO NAY ĐƯỢC KIỂM ══════════════════════════════════════
def test_B1_phat_bat_bien_do_dai_cho_de_cho_SO():
    for cid, mong in ((RATIO, ("C", "D", "10")), (MULTIPLE, ("E", "F", "10"))):
        dd = [b for b in _hd(cid).source_invariants if b.kind == "segment_length"]
        assert (dd[0].points, dd[0].expected) == (mong[:2], mong[2]), (cid, dd)


def test_B2_TOA_DO_TRAI_DU_KIEN_bi_bac():
    """Phản ví dụ ⓑ — trước bản vá: `served` với `396/5` thay vì `8`."""
    p = _ct(MULTIPLE, E={"source_fact_id": None, "model_assumption": LY_DO},
            F={"initial_value": [99, 0, 0], "source_fact_id": None,
               "model_assumption": LY_DO})
    oc = _chay(MULTIPLE, p)
    assert oc.servable is False
    assert oc.stage_reached == "source_invariant"
    t = " ".join(str(x) for x in (oc.details or []))
    assert "NORMALIZED_SOURCE_VIOLATED" in t and "EF" in t


def test_B3_TIEM_go_bo_phat_do_dai_thi_phan_vi_du_SERVED_lai(monkeypatch):
    """Guard chưa từng đỏ là guard chưa được chứng minh."""
    monkeypatch.setattr(SR, "bat_bien_do_dai", lambda c, t: ())
    rc = RequestContract.model_validate(CA[MULTIPLE]["request_contract"])
    rc = rc.model_copy(update={
        "source_invariants": SR.bat_bien_chia_doan(rc, rc.problem_text)})
    p = _ct(MULTIPLE, E={"source_fact_id": None, "model_assumption": LY_DO},
            F={"initial_value": [99, 0, 0], "source_fact_id": None,
               "model_assumption": LY_DO})
    oc = verify_and_compile(rc, SemanticProgramSpec.model_validate(p))
    assert oc.stage_reached == "served"
    assert _dap(oc, MULTIPLE) == "396/5"          # đáp số SAI, phục vụ im lặng


def test_B4_do_dai_DUNG_thi_khong_can_tro(monkeypatch):
    for cid, dap in ((RATIO, "6"), (MULTIPLE, "8")):
        oc = _chay(cid, _ct(cid))
        assert oc.stage_reached == "served", (cid, oc.details)
        assert _dap(oc, cid) == dap


def test_B5_KHONG_phat_trung_voi_duong_chuan_hoa_thang():
    """`chuan_hoa_thang` phát trước; tầng này phải nhường, không nhân đôi."""
    hd = build_request_contract(
        {"input_facts": [{"id": "ab", "label": "AB", "value": "a"},
                         {"id": "sa", "label": "SA", "value": "4a/5"}],
         "obligations": []},
        problem_text="Cho hình chóp S.ABC có AB = a, SA = 4a/5.",
        domain=DOMAIN_HINH_HOC)
    cap = [tuple(sorted(b.points)) for b in hd.source_invariants
           if b.kind == "segment_length"]
    assert len(cap) == len(set(cap)), cap


def test_B6_hai_do_dai_MAU_THUAN_cho_cung_doan_thi_KHONG_phat():
    """Không ai phân xử được ⇒ không phát, chứ không đoán."""
    class _C:
        input_facts, problem_text = (), "Đoạn AB = 10. Đoạn AB = 12."
    assert SR.bat_bien_do_dai(_C(), _C.problem_text) == ()


# ══ C · LỖ CÒN LẠI, KHAI THẲNG ═══════════════════════════════════════════
def test_C1_LO_CON_LAI_diem_phai_dung_van_khai_thang_toa_do_duoc():
    """⚠️ `NOT_CLOSED` — ghi lại bằng một test ĐANG XANH, không phải bằng lời.

    Đề giới thiệu `P` như một điểm **phải dựng ra** (*"Điểm P nằm trên đoạn EF
    sao cho FP = 4·PE"*), nhưng `nhan_suy_ra` chỉ nhận hai lối nói —
    `"gọi/lấy X là …"` và `"X là trung điểm|hình chiếu|giao điểm|…"` — nên
    chốt ⑥ của `grounding_gate` không bắt được dạng này.

    Hệ quả: chương trình khai thẳng toạ độ `P`, **bỏ câu lệnh dựng**, và vẫn
    được phục vụ với đáp số ĐÚNG (bất biến `segment_division` xác nhận vị
    trí). Thứ mất không phải đáp số mà là **bước dựng** — đúng thứ chốt ⑥ sinh
    ra để giữ, và đúng thứ đề tài hứa cho học sinh.

    Test này xanh nghĩa là lỗ **vẫn còn**. Khi wave sau đóng nó, test này ĐỎ —
    và đỏ là đúng.
    """
    from app.simulation.semantic_program.grounding_gate import la_ten_suy_ra

    de = CA[MULTIPLE]["problem_text"]
    assert la_ten_suy_ra("P", de) is False        # ← gốc của lỗ

    p = _ct(MULTIPLE, E={"source_fact_id": None, "model_assumption": LY_DO},
            P={"initial_value": [2, 0, 0], "source_fact_id": None,
               "model_assumption": LY_DO})
    p["statements"] = [s for s in p["statements"] if s.get("target_var") != "P"]
    oc = _chay(MULTIPLE, p)
    assert oc.stage_reached == "served"
    assert _dap(oc, MULTIPLE) == "8"              # đáp số đúng, bước dựng MẤT


def test_C2_tin_hieu_de_dong_lo_ay_DA_CO_san_trong_kho():
    """Bộ neo của `segment_relation` nhận đúng lối nói mà `nhan_suy_ra` thiếu.

    Ghi lại để wave sau không phải đi tìm: đường sửa là dùng lại tín hiệu này,
    không dựng thẩm quyền thứ ba.
    """
    de = CA[MULTIPLE]["problem_text"]

    class _C:
        input_facts, problem_text = (), de
    bt = SR.bat_bien_chia_doan(_C(), de)
    assert [b.points[2] for b in bt] == ["P"]
