# -*- coding: utf-8 -*-
"""`CURVED_RADIUS_SLOT_AFFORDANCE_ADJUDICATION` — Nhánh A.

Thẻ nay nói **hai mệnh đề** mà validator cưỡng chế nhưng thẻ chưa diễn đạt:

    P1  đề cho bằng SỐ ⇒ dùng ô ĐẠI LƯỢNG (`radius`, `height`)
    P3  mỗi cặp `rim_point`/`radius` và `apex_or_top`/`height` chọn ĐÚNG MỘT

─── VÌ SAO PHÉP PARITY PHẢI DẪN XUẤT, KHÔNG CHÉP TAY ──────────────────────

Một test liệt kê tay `("rim_point", "radius")` sẽ xanh mãi mãi kể cả khi
validator mọc thêm một cặp loại trừ thứ ba — đúng lớp lỗi mà `_KIEU_TIN_HOC`
và `_TOAN_HANG_LENH` đã đi dọn. Nên `_cap_loai_tru()` **dò chính validator**:
với mỗi cặp ô tuỳ chọn, thử khai CẢ HAI và khai KHÔNG ô nào; cặp nào bị từ
chối ở cả hai phía là một cặp XOR, và thẻ phải nói về nó.
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import pytest

from app.simulation.geometry.curved import KHOI_CONG
from app.simulation.semantic_program.contract import (
    ConstructCurvedSolidStmt, SemanticProgramSpec,
)
from app.simulation.semantic_program.grammar_card import grammar_card

GOC = Path(__file__).resolve().parents[2]
if str(GOC / "scripts") not in sys.path:
    sys.path.insert(0, str(GOC / "scripts"))

#: Ô tuỳ chọn của câu lệnh, trừ những ô không thuộc luật loại trừ nào.
_O = ("rim_point", "radius", "apex_or_top", "height")
_GIA = {"rim_point": "P", "radius": "r", "apex_or_top": "S", "height": "h"}


def _hop_le(kind: str, **o) -> bool:
    d = {"kind": "construct_curved_solid", "target_var": "x",
         "curved_kind": kind, "anchor": "O", **o}
    try:
        ConstructCurvedSolidStmt.model_validate(d)
        return True
    except Exception:                                             # noqa: BLE001
        return False


def _tap_chap_nhan(kind: str) -> list[frozenset[str]]:
    """Mọi tổ hợp ô mà validator NHẬN — 2⁴ phép thử, không đoán nền."""
    ra = []
    for n in range(len(_O) + 1):
        for tap in itertools.combinations(_O, n):
            if _hop_le(kind, **{k: _GIA[k] for k in tap}):
                ra.append(frozenset(tap))
    return ra


def _cap_loai_tru(kind: str) -> set[frozenset[str]]:
    """DÒ validator: cặp `{a,b}` là XOR ⇔ **mọi** tổ hợp được nhận đều chứa
    ĐÚNG MỘT trong hai.

    Dẫn từ TẬP CHẤP NHẬN chứ không từ một cấu hình nền đoán trước — bản đầu
    của test này dựng nền bằng *"hai ô còn lại"*, mà hai ô ấy chính là cặp XOR
    kia, nên nền luôn bất hợp lệ và phép dò trả RỖNG. Một `test_01` chạy trên
    tập rỗng thì xanh mà không khẳng định gì; `test_02` có mặt để bắt đúng ca
    ấy.
    """
    nhan = _tap_chap_nhan(kind)
    if not nhan:
        return set()
    return {frozenset((a, b)) for a, b in itertools.combinations(_O, 2)
            if all(len({a, b} & s) == 1 for s in nhan)}


def _dong_khoi_cong() -> str:
    return next(d for d in grammar_card("hinh_hoc").splitlines()
                if d.strip().startswith("Khối cong:"))


# ══ PARITY DẪN XUẤT: validator ↔ thẻ ═══════════════════════════════════
def test_01_moi_cap_LOAI_TRU_cua_validator_deu_co_trong_the():
    """Thêm một cặp XOR thứ ba mà quên thẻ ⇒ test này ĐỎ."""
    dong = _dong_khoi_cong()
    cap = _cap_loai_tru("cylinder") | _cap_loai_tru("cone")
    assert cap, "không dò được cặp loại trừ nào — phép dò đã hỏng"
    for c in cap:
        for o in c:
            assert f"`{o}`" in dong, (sorted(c), o, dong)
    assert "ĐÚNG MỘT" in dong


def test_02_cap_do_duoc_dung_bang_hai_cap_da_biet():
    """Neo phép dò vào sự thật đã đọc từ `contract.py` — nếu phép dò tự nó
    hỏng và trả rỗng, `test_01` sẽ xanh giả."""
    assert _cap_loai_tru("cylinder") == {
        frozenset({"rim_point", "radius"}),
        frozenset({"apex_or_top", "height"}),
    }
    # Khối cầu KHÔNG có trục ⇒ chỉ một cặp.
    assert _cap_loai_tru("ball") == {frozenset({"rim_point", "radius"})}


def test_03_the_noi_luat_CHON_khong_chi_luat_hop_le():
    """P1 — thứ không validator nào encode được."""
    dong = _dong_khoi_cong()
    assert "bằng SỐ" in dong
    assert "`radius`" in dong and "`height`" in dong


def test_04_dong_the_la_quy_tac_CHUNG():
    """Không tên vật, không fact id, không đáp số, không cách giải đề nào."""
    dong = _dong_khoi_cong()
    for cam in ("P_rim", "O_prime", "16", "√5", "elip", "(α)", "2x",
                "ban_kinh_day", "hình trụ tròn xoay"):
        assert cam not in dong, cam
    # Nói cho CẢ HAI cặp, không riêng ca bán kính.
    assert "apex_or_top" in dong and "height" in dong


def test_05_card_C_va_hai_affordance_cu_NGUYEN_VAN():
    the = grammar_card("hinh_hoc")
    assert "t = m/(m+n)" in the
    assert any(d.strip().startswith("Xuất xứ:") for d in the.splitlines())


# ══ §10 · HỢP ĐỒNG THẬT GIỮ NGUYÊN ═════════════════════════════════════
def test_06_direct_radius_cylinder_hop_le():
    assert _hop_le("cylinder", radius="r", apex_or_top="S")
    assert _hop_le("cylinder", radius="r", height="h")


def test_07_direct_radius_cone_hop_le_theo_bang_tham_quyen():
    assert KHOI_CONG["cone"].khai_bang_ban_kinh
    assert _hop_le("cone", radius="r", apex_or_top="S")
    assert _hop_le("cone", radius="r", height="h")


def test_08_rim_point_van_hop_le():
    assert _hop_le("cylinder", rim_point="P", apex_or_top="S")
    assert _hop_le("ball", rim_point="P")


def test_09_radius_VA_rim_point_bi_tu_choi():
    assert not _hop_le("cylinder", radius="r", rim_point="P", apex_or_top="S")
    assert not _hop_le("ball", radius="r", rim_point="P")


def test_10_khong_o_nao_bi_tu_choi():
    assert not _hop_le("cylinder", apex_or_top="S")
    assert not _hop_le("ball")


def test_11_cau_KHONG_nhan_chieu_cao():
    assert not KHOI_CONG["ball"].can_chieu_cao
    assert not _hop_le("ball", radius="r", height="h")


# ══ §10 · GROUNDING GIỮ NGUYÊN ĐỘ CHẶT ═════════════════════════════════
def _ct_rim(source_fact_id: str | None) -> dict:
    from gold_oblique_ellipse_fresh import GOLD

    import copy

    g = copy.deepcopy(GOLD)
    g["memory_declarations"] = [d for d in g["memory_declarations"]
                                if d["name"] not in ("P1", "P2", "P3", "r")]
    d = {"name": "P_rim", "type": "point3", "initial_value": [4, 0, 0]}
    if source_fact_id:
        d["source_fact_id"] = source_fact_id
    else:
        d["model_assumption"] = "Chọn một điểm trên vành đáy dưới."
    g["memory_declarations"].append(d)
    g["statements"] = [
        {"kind": "construct_plane_from_equation", "target_var": "alpha",
         "a": 2, "b": 0, "c": -1, "d": 10}
        if s.get("kind") == "construct_plane" else s
        for s in g["statements"]]
    for s in g["statements"]:
        if s.get("kind") == "construct_curved_solid":
            s.pop("radius", None)
            s["rim_point"] = "P_rim"
    return g


def _hd():
    from app.simulation.semantic_program.plane_equation import (
        bat_bien_mat_phang,
    )
    from app.simulation.semantic_program.request_contract import RequestContract

    from gold_oblique_ellipse_fresh import PROBLEM_TEXT, REQUEST_CONTRACT_GOLD

    c = RequestContract.model_validate(REQUEST_CONTRACT_GOLD)
    return c.model_copy(update={
        "source_invariants": tuple(c.source_invariants or ())
        + bat_bien_mat_phang(c, PROBLEM_TEXT)})


def test_12_rim_point_KHONG_neo_van_bi_bac():
    """Bản vá là VĂN PHẠM, không phải nới cổng. Verdict giữ nguyên."""
    from app.simulation.semantic_program.grounding_gate import check_grounding

    r = check_grounding(_hd(), SemanticProgramSpec.model_validate(
        _ct_rim(None)))
    assert not r.ok
    assert r.error_code == "UNANCHORED_DERIVED_ASSUMPTION"


def test_13_rim_point_CO_neo_thi_qua_grounding():
    """Điểm vành có nguồn vẫn là một lối hợp lệ — thẻ không cấm nó."""
    from app.simulation.semantic_program.grounding_gate import check_grounding

    r = check_grounding(_hd(), SemanticProgramSpec.model_validate(
        _ct_rim("ban_kinh_day")))
    assert not any(x.startswith("P_rim|") for x in r.unjustified_literals), (
        r.unjustified_literals)


def test_14_chan_doan_HIEN_TAI_khong_nhac_radius():
    """⚠️ Ô ĐO, không phải ô mong muốn — Nhánh A không đụng diagnostic.

    Ghi lại để Nhánh B (`CURVED_RIM_POINT_REPAIR_EFFICACY`) có mốc so, và để
    ai đó sửa diagnostic thì test này đỏ và buộc cập nhật kết luận wave.
    """
    from app.simulation.semantic_program.grounding_gate import check_grounding

    r = check_grounding(_hd(), SemanticProgramSpec.model_validate(
        _ct_rim(None)))
    msg = "; ".join(r.unresolved)
    assert "P_rim" in msg
    assert "radius" not in msg          # DIAGNOSTIC_IDENTIFIES_RADIUS_SLOT = NO


def test_15_repair_policy_VAN_khong_tach_lop_con():
    from app.ai.pipeline import KHONG_DUOC_SUA

    assert "UNANCHORED_DERIVED_ASSUMPTION" in KHONG_DUOC_SUA


# ══ §10 · TIÊM LỖI ═════════════════════════════════════════════════════
def test_TIEM_1_bo_mot_menh_de_khoi_the__parity_DO(monkeypatch):
    """Tiêm: xoá tên `radius` khỏi dòng thẻ ⇒ `test_01` mất căn cứ."""
    import app.simulation.semantic_program.grammar_card as GC

    monkeypatch.setattr(GC, "_DONG_KHOI_CONG",
                        "  Khối cong: mỗi cặp chọn ĐÚNG MỘT.")
    dong = next(d for d in GC.grammar_card("hinh_hoc").splitlines()
                if d.strip().startswith("Khối cong:"))
    cap = _cap_loai_tru("cylinder")
    thieu = [o for c in cap for o in c if f"`{o}`" not in dong]
    assert thieu, "tiêm không có hiệu lực — test_01 chưa chứng minh gì"


def test_TIEM_2_bo_luat_CHON__P1_mat(monkeypatch):
    """Tiêm: giữ luật loại trừ nhưng bỏ *"đề cho bằng SỐ"* ⇒ P1 biến mất."""
    import app.simulation.semantic_program.grammar_card as GC

    monkeypatch.setattr(
        GC, "_DONG_KHOI_CONG",
        "  Khối cong: mỗi cặp `rim_point`/`radius` và `apex_or_top`/`height` "
        "chọn ĐÚNG MỘT.")
    dong = next(d for d in GC.grammar_card("hinh_hoc").splitlines()
                if d.strip().startswith("Khối cong:"))
    assert "bằng SỐ" not in dong


def test_TIEM_3_doi_capability_mot_ho__validator_va_phep_do_theo(monkeypatch):
    """Tiêm: `cone.khai_bang_ban_kinh = False` ⇒ `radius` hết hợp lệ cho nón,
    và phép dò cặp loại trừ phản ánh ngay."""
    import app.simulation.semantic_program.contract as C

    import dataclasses

    monkeypatch.setitem(KHOI_CONG, "cone", dataclasses.replace(
        KHOI_CONG["cone"], khai_bang_ban_kinh=False))
    assert not _hop_le("cone", radius="r", apex_or_top="S")
    assert _hop_le("cone", rim_point="P", apex_or_top="S")
    # ⚠️ Cặp `{rim_point, radius}` VẪN là XOR — và kỳ vọng ngược lại là sai:
    # bỏ `radius` đi thì MỌI tổ hợp được nhận đều chứa đúng `rim_point`, nên
    # tính "đúng một trong hai" thoả một cách tầm thường. Thứ thật sự đổi là
    # TẬP CHẤP NHẬN co lại — không tổ hợp nào còn dùng `radius`.
    assert all("radius" not in t for t in _tap_chap_nhan("cone"))
    assert any("radius" in t for t in _tap_chap_nhan("cylinder"))
    assert C is not None


# ══ ARTIFACT PHÂN XỬ ═══════════════════════════════════════════════════
ADJ = (GOC.parent / "docs" / "evaluation" / "geometry"
       / "radius-slot-affordance" / "ADJUDICATION.json")


@pytest.mark.skipif(not ADJ.exists(), reason="chưa có artifact phân xử")
def test_16_artifact_phan_xu_khop_ket_luan():
    d = json.loads(ADJ.read_text(encoding="utf-8"))
    assert d["hai_raw_candidate"]["RAW_FAILURES_MATCH"] is True
    assert d["hai_raw_candidate"]["CURVED_RIM_POINT_AFFORDANCE"] == "REPLICATED"
    md = d["minimal_delta"]
    assert md["FIELDS_CHANGED"] == 2
    assert md["replay"]["servable"] is True
    assert md["replay"]["exact_answer"] == "16π√5"
    assert d["chan_doan"]["DIAGNOSTIC_IDENTIFIES_RADIUS_SLOT"] == "NO"
    assert d["chan_doan"]["REPAIR_POLICY_DISTINGUISHES_SAFE_SUBCASE"] == "NO"
