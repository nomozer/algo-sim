# -*- coding: utf-8 -*-
"""TIỀN KIỂM TẤT ĐỊNH cho `RATIO_AFFORDANCE_STAGED_RECHECK`. **0 lượt gọi model.**

Phải xanh **TRƯỚC** bốn lượt live. Nếu nền đo không tự đứng được thì con số
lượt live không nói lên điều gì — tiền lệ ở kho này rất rõ
(`V3_LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL`).

Hai ca của phép đo, lấy nguyên từ `gold_ratio_ab.CORPUS`:

    RATIO     `r2`  CD = 10 · CN:ND = 2:3 · ND = 6 · t(C→D) = 2/5
    MULTIPLE  `r3`  EF = 10 · FP = 4·PE  · PF = 8 · t(E→F) = 1/5
"""
from __future__ import annotations

import json
from fractions import Fraction

import pytest

from app.ai.pipeline import _dung_scene3d
from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program import segment_relation as SR
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[2]
if str(GOC / "scripts") not in sys.path:
    sys.path.insert(0, str(GOC / "scripts"))

from gold_ratio_ab import CORPUS  # noqa: E402

CA = {c["case_id"]: c for c in CORPUS}
#: Ánh xạ tên phép đo → ca trong corpus. Một chỗ khai, dùng lại khắp file.
RATIO, MULTIPLE = "r2", "r3"


def _hd(cid: str) -> RequestContract:
    """Hợp đồng CỐ ĐỊNH + bất biến nguồn, y như đường sản phẩm gắn."""
    rc = RequestContract.model_validate(CA[cid]["request_contract"])
    bt = SR.bat_bien_chia_doan(rc, rc.problem_text)
    return rc.model_copy(update={
        "source_invariants": tuple(rc.source_invariants or ()) + bt})


def _ct(cid: str, a: str, b: str, t: str) -> SemanticProgramSpec:
    p = json.loads(json.dumps(CA[cid]["gold"]))
    diem = CA[cid]["diem_duoc_hoi"]
    for s in p["statements"]:
        if s.get("target_var") == diem:
            s["expr"]["a"], s["expr"]["b"], s["expr"]["ratio"] = a, b, t
    return SemanticProgramSpec.model_validate(p)


def _chay(cid: str, a: str, b: str, t: str):
    return verify_and_compile(_hd(cid), _ct(cid, a, b, t))


def _dl(oc):
    return {k: display(v) for k, v in (oc.final_memory or {}).items()
            if is_exact_number(v)}


# ══ ① · ② HAI CA CHUẨN ĐI TRỌN ĐƯỜNG SẢN PHẨM ═══════════════════════════
@pytest.mark.parametrize("cid,a,b,t,wit,dap", [
    (RATIO, "C", "D", "2/5", "do_dai_nd", "6"),
    (MULTIPLE, "E", "F", "1/5", "do_dai_pf", "8"),
])
def test_1_2_ti_le_dung_thi_served_va_qua_bat_bien_nguon(cid, a, b, t, wit, dap):
    oc = _chay(cid, a, b, t)
    assert oc.stage_reached == "served", oc.details
    assert _dl(oc)[wit] == dap
    assert (_dung_scene3d(_ct(cid, a, b, t), _hd(cid)) or {}).get("objects")


def test_1b_bat_bien_phat_ra_dung_cho_ca_hai_ca():
    for cid, mong in ((RATIO, "2/5"), (MULTIPLE, "1/5")):
        bt = [b for b in _hd(cid).source_invariants if b.kind == SR.KIND]
        assert len(bt) == 1 and bt[0].expected == mong, (cid, bt)


# ══ ③ TỈ LỆ SAI NHƯNG VẪN TRONG ĐOẠN ⇒ BỊ BÁC ═══════════════════════════
@pytest.mark.parametrize("cid,a,b,t", [
    (RATIO, "C", "D", "1/2"),        # N ở giữa — vẫn trong đoạn
    (MULTIPLE, "E", "F", "1/4"),     # đúng lỗi `r3/A` của lượt A/B
])
def test_3_ti_le_sai_trong_doan_bi_NORMALIZED_SOURCE_VIOLATED(cid, a, b, t):
    oc = _chay(cid, a, b, t)
    assert oc.servable is False
    assert oc.stage_reached == "source_invariant"
    assert any("NORMALIZED_SOURCE_VIOLATED" in str(x) for x in (oc.details or []))


# ══ ④ ĐẢO TOÁN HẠNG VỚI TỈ LỆ TƯƠNG ĐƯƠNG ⇒ CÙNG ĐIỂM, ĐƯỢC NHẬN ════════
@pytest.mark.parametrize("cid,a,b,t,wit,dap", [
    (RATIO, "D", "C", "3/5", "do_dai_nd", "6"),
    (MULTIPLE, "F", "E", "4/5", "do_dai_pf", "8"),
])
def test_4_dao_toan_hang_tuong_duong_van_duoc_chap_nhan(cid, a, b, t, wit, dap):
    oc = _chay(cid, a, b, t)
    assert oc.stage_reached == "served", oc.details
    assert _dl(oc)[wit] == dap


def test_4b_phan_so_tuong_duong_la_CUNG_mot_diem():
    """`2/10` ≡ `1/5` — so hữu tỉ, không so chuỗi."""
    assert Fraction("2/10") == Fraction("1/5")
    oc = _chay(MULTIPLE, "E", "F", "2/10")
    assert oc.stage_reached == "served", oc.details
    assert _dl(oc)["do_dai_pf"] == "8"


# ══ ⑤ DỮ KIỆN MÂU THUẪN VỚI ĐỀ ═══════════════════════════════════════════
class _F:
    def __init__(self, i, l, v):
        self.fact_id, self.label, self.values = i, l, v


def _voi_fact(cid: str, van: str) -> RequestContract:
    rc = RequestContract.model_validate(CA[cid]["request_contract"])
    them = rc.model_copy(update={"input_facts": rc.input_facts + (
        _F("f_them", "Vị trí điểm", (van,)),)})
    bt = SR.bat_bien_chia_doan(them, them.problem_text)
    return them.model_copy(update={"source_invariants": bt})


def test_5_du_kien_MAU_THUAN_khong_bien_hinh_SAI_thanh_hinh_DUNG():
    """THẨM QUYỀN khi hai nguồn mâu thuẫn: **không nguồn nào thắng** ⇒ CHẶN.

    Đề nói `FP = 4·PE` (`t = 1/5`); một `InputFact` nói `PE = 5` (`t = 1/2`).
    Nếu dữ kiện được ưu tiên thì chương trình dựng `t = 1/2` — SAI theo đề —
    sẽ được nhận. Nếu đề được ưu tiên thì mâu thuẫn bị nuốt im lặng.

    Hệ chọn cách thứ ba: **`segment_division_unresolved`**, chặn `served`. Hai
    lời khai khác nhau về cùng một điểm là chuyện phải fail-closed — chọn hộ
    một trong hai là dựng một kết quả không tra lại được.
    """
    rc = _voi_fact(MULTIPLE, "Độ dài PE = 5")
    assert [b.kind for b in rc.source_invariants] == [SR.KIND_CHUA_GIAI]

    # Chương trình theo DỮ KIỆN (t = 1/2) — KHÔNG được nhận.
    oc = verify_and_compile(rc, _ct(MULTIPLE, "E", "F", "1/2"))
    assert oc.servable is False and oc.stage_reached == "source_invariant"

    # Và chương trình theo ĐỀ (t = 1/5) cũng bị chặn — hệ không giả vờ đã
    # phân xử được. Đó là cái giá của fail-closed, và nó nói ra được.
    oc2 = verify_and_compile(rc, _ct(MULTIPLE, "E", "F", "1/5"))
    assert oc2.servable is False and oc2.stage_reached == "source_invariant"


def test_5b_du_kien_DONG_THUAN_thi_khong_doi_gi():
    rc = _voi_fact(MULTIPLE, "Độ dài PE = 2")
    bt = [b for b in rc.source_invariants if b.kind == SR.KIND]
    assert len(bt) == 1 and bt[0].expected == "1/5"
    assert verify_and_compile(rc, _ct(MULTIPLE, "E", "F", "1/5")
                              ).stage_reached == "served"


def test_5c_du_kien_KHONG_DOC_DUOC_bi_bo_qua_chu_khong_gay_chan():
    """`FP = PE` không có số ⇒ không mẫu nào khớp ⇒ bỏ qua, không chặn.

    Ghi lại để ranh giới rõ: chỉ mâu thuẫn **đọc được** mới chặn.
    """
    rc = _voi_fact(MULTIPLE, "P thuộc EF và FP = PE")
    bt = [b for b in rc.source_invariants if b.kind == SR.KIND]
    assert len(bt) == 1 and bt[0].expected == "1/5"
