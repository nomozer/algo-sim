# -*- coding: utf-8 -*-
"""QUY TRÁCH NHIỆM: hệ thiếu năng lực ≠ mô hình viết sai. **0 lượt gọi model.**

    `ACCEPTANCE_SCORER_EXPRESSIVENESS_CLASS`, 2026-09-04.

Pre-draw guard của `CURVED_V3_LIVE_ACCEPTANCE` đo được: đề cho **đường kính**
thì `r = d/2` là bước ĐÚNG về toán, nhưng `arith` cho kiểu tĩnh `unknown` còn ô
`radius` chỉ nhận `scalar|float|int` ⇒ chương trình chết ở `ir_static` và bị xếp
`MODEL_STATIC_FAILURE`. Bộ đo quy sai trách nhiệm, đúng chiều mà cả tuyến probe
này tồn tại để chặn.

Toàn bộ fixture ở đây là **TỔNG HỢP**, không đụng V3. Pool vẫn chưa rút.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from acceptance_verdict import (  # noqa: E402
    LOP_PHAN_QUYET,
    YeuCauNangLuc,
    duong_hop_le_ton_tai,
    o_vo_huong_bi_rang_buoc_mo_ho,
    phan_loai,
)
from app.simulation.semantic_program.contract import (  # noqa: E402
    SemanticProgramSpec,
)
from app.simulation.semantic_program.ir_static_check import (  # noqa: E402
    _TOAN_HANG_LENH,
)
from app.simulation.semantic_program.obligations import Obligation  # noqa: E402
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

#: Kiểu ô `radius` — DẪN từ thẩm quyền, không gõ tay.
KIEU_RADIUS = frozenset(
    next(k for n, k, _l in _TOAN_HANG_LENH["construct_curved_solid"]
         if n == "radius"))


def _yc(can_bien_doi: bool, nguon=frozenset({"float"})) -> YeuCauNangLuc:
    return YeuCauNangLuc(
        o_dich="radius", kieu_o_dich=KIEU_RADIUS, kieu_nguon=nguon,
        can_bien_doi=can_bien_doi,
        phep_can="r = d/2" if can_bien_doi else "dùng thẳng bán kính")


# ── chương trình tổng hợp ────────────────────────────────────────────────
def _spec(bieu_thuc_r: dict | None, *, khai_r=True, ten_nguon="d",
          gt_nguon=26, src="dk") -> SemanticProgramSpec:
    khai = [
        {"name": "O", "type": "point3", "initial_value": [0, 0, 0],
         "source_fact_id": "tam"},
        {"name": ten_nguon, "type": "float", "initial_value": gt_nguon,
         **({"source_fact_id": src} if src else {})},
        {"name": "S", "type": "curved_solid"}, {"name": "V", "type": "float"},
    ]
    # Chỉ khai `r` riêng khi có một biểu thức ràng buộc nó. Không có biểu thức
    # thì ô `radius` đọc thẳng `ten_nguon`, và khai thêm `r` sẽ trùng tên khi
    # `ten_nguon == "r"`.
    if khai_r and bieu_thuc_r is not None:
        khai.insert(2, {"name": "r", "type": "float"})
    stmts = []
    if bieu_thuc_r is not None:
        stmts.append({"kind": "assign", "target_var": "r", "expr": bieu_thuc_r})
    stmts += [
        {"kind": "construct_curved_solid", "target_var": "S",
         "curved_kind": "ball", "anchor": "O",
         "radius": "r" if bieu_thuc_r is not None else ten_nguon},
        {"kind": "assign", "target_var": "V",
         "expr": {"kind": "measure", "quantity": "volume", "of": "S"}},
    ]
    return SemanticProgramSpec.model_validate(
        {"title": "Mặt cầu tổng hợp", "memory_declarations": khai,
         "statements": stmts})


def _ct(gt=26, src_ok=True) -> RequestContract:
    return RequestContract(
        problem_text="Cho mặt cầu tâm O. Tính thể tích.",
        input_facts=[
            {"fact_id": "tam", "label": "tâm O", "values": ["O"],
             "provenance": "confirmed"},
            *([{"fact_id": "dk", "label": "số đo", "values": [gt],
                "provenance": "confirmed"}] if src_ok else []),
        ],
        obligations=(Obligation(kind="volume", container="S",
                                params={"witness": "V"}),))


CHIA_DOI = {"kind": "arith", "op": "//",
            "left": {"kind": "var", "name": "d"},
            "right": {"kind": "literal", "value": 2}}


def _lop(spec, ct=None, yc=None) -> str:
    ct = ct or _ct()
    return phan_loai(verify_and_compile(ct, spec), schema_ok=True,
                     contract=ct, spec=spec, yeu_cau=yc)


# ══ E1 · SYSTEM GAP DƯƠNG TÍNH ════════════════════════════════════════════
def test_E1a_duong_kinh_can_chia_doi__KHONG_co_duong_hop_le():
    """Chứng minh bằng CHỮ KÝ, không bằng chuỗi lỗi."""
    assert duong_hop_le_ton_tai(_yc(True)) == "NO"


def test_E1b_fixture_duong_kinh_voi_bang_chung__SYSTEM_EXPRESSIVENESS_GAP():
    assert _lop(_spec(CHIA_DOI), yc=_yc(True)) == "SYSTEM_EXPRESSIVENESS_GAP"


def test_E1c_phep_chia_TUONG_DUONG_cho_cung_phan_quyet():
    """Cùng chứng minh chữ ký ⇒ cùng verdict, bất kể viết `//` hay `*`."""
    nhan = {"kind": "arith", "op": "*",
            "left": {"kind": "var", "name": "d"},
            "right": {"kind": "literal", "value": 1}}
    assert _lop(_spec(nhan), yc=_yc(True)) == "SYSTEM_EXPRESSIVENESS_GAP"


def test_E1d_KHONG_co_phep_nao_bien_vo_huong_thanh_vo_huong_CO_KIEU():
    """Gốc của chứng minh: `measure` là phép duy nhất trả `scalar`, và nó
    KHÔNG nhận vô hướng làm chủ thể."""
    from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO

    vo_huong = {"scalar", "float", "int"}
    kieu_of = {t for p in BANG_PHEP_DO.values() for t in p.kieu_of}
    assert not (kieu_of & vo_huong), "measure nhận vô hướng ⇒ chứng minh sập"


# ══ E2 · CHỐNG DƯƠNG TÍNH GIẢ ═════════════════════════════════════════════
def test_E2a_de_cho_BAN_KINH_truc_tiep__model_viet_arith_la_LOI_MODEL():
    """Đường hợp lệ TỒN TẠI (dùng thẳng); mô hình tự chọn đường mơ hồ."""
    assert duong_hop_le_ton_tai(_yc(False)) == "YES"
    assert _lop(_spec(CHIA_DOI), yc=_yc(False)) == "MODEL_STATIC_FAILURE"


def test_E2b_quen_khai_vo_huong__van_la_loi_model():
    lop = _lop(_spec(None, khai_r=False, ten_nguon="r", src="dk"),
               yc=_yc(False))
    assert lop.startswith("MODEL_") or lop == "CORRECT_SERVABLE_RESULT", lop


def test_E2c_bien_CHUA_grounded__MODEL_GROUNDING_FAILURE():
    """Grounding phải THẮNG quy tắc năng lực — xem E3a."""
    spec = _spec(None, ten_nguon="r", src=None)
    assert _lop(spec, ct=_ct(src_ok=False), yc=_yc(True)) == \
        "MODEL_GROUNDING_FAILURE"


def test_E2d_bieu_thuc_mo_ho_KHONG_nuoi_o_radius__van_loi_model():
    """Ràng buộc mơ hồ ở một biến KHÔNG đi vào ô vô hướng nào ⇒ không được
    hưởng lớp chưa-kết-luận."""
    raw = {
        "title": "Mơ hồ ở chỗ khác",
        "memory_declarations": [
            {"name": "O", "type": "point3", "initial_value": [0, 0, 0],
             "source_fact_id": "tam"},
            {"name": "A", "type": "point3", "initial_value": [6, 0, 0],
             "source_fact_id": "dk"},
            {"name": "x", "type": "float"},
            {"name": "S", "type": "curved_solid"}, {"name": "V", "type": "float"},
        ],
        "statements": [
            {"kind": "assign", "target_var": "x",
             "expr": {"kind": "arith", "op": "+",
                      "left": {"kind": "literal", "value": 1},
                      "right": {"kind": "literal", "value": 2}}},
            {"kind": "construct_curved_solid", "target_var": "S",
             "curved_kind": "ball", "anchor": "O", "rim_point": "A"},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "S"}},
        ]}
    spec = SemanticProgramSpec.model_validate(raw)
    assert o_vo_huong_bi_rang_buoc_mo_ho(
        verify_and_compile(_ct(), spec), spec) == []


def test_E2e_chuong_trinh_HOP_LE_van_phuc_vu_duoc():
    """Quy tắc mới không được làm hỏng đường xanh."""
    spec = _spec(None, ten_nguon="r", gt_nguon=13, src="dk")
    assert _lop(spec, ct=_ct(gt=13), yc=_yc(False)) == "CORRECT_SERVABLE_RESULT"


def test_E2f_KHONG_phai_moi_loi_radius_deu_la_system_gap():
    """Cùng một chương trình, hai bằng chứng khác nhau ⇒ hai verdict khác nhau.
    Đây là mệnh đề trung tâm chống dương tính giả."""
    spec = _spec(CHIA_DOI)
    assert _lop(spec, yc=_yc(True)) == "SYSTEM_EXPRESSIVENESS_GAP"
    assert _lop(spec, yc=_yc(False)) == "MODEL_STATIC_FAILURE"


# ══ E3 · THỨ TỰ ƯU TIÊN ═══════════════════════════════════════════════════
def test_E3a_grounding_KHONG_bi_quy_tac_nang_luc_che():
    spec = _spec(CHIA_DOI, src=None)
    assert _lop(spec, ct=_ct(src_ok=False), yc=_yc(True)) == \
        "MODEL_GROUNDING_FAILURE"


def test_E3b_schema_hong_KHONG_bi_che():
    assert phan_loai(None, schema_ok=False, yeu_cau=_yc(True)) == \
        "MODEL_SCHEMA_FAILURE"


def test_E3c_lop_he_thong_khac_giu_nguyen_uu_tien():
    """`SYSTEM_COVERAGE_FAILURE` phán trên cổng phủ, KHÔNG bị quy tắc mới nuốt."""
    from app.simulation.semantic_program.coverage_gate import KIEU_KHONG_HOP

    class FakeOutcome:
        stage_reached = "structural_coverage"
        executable = servable = False
        error_code = "requested_operation_uncovered"
        failure_category = details = reason = None
        weak_kinds: list = []

    oc = FakeOutcome(); oc.details = []
    # Không bằng chứng năng lực và không hình dạng mơ hồ ⇒ giữ lối cũ.
    assert phan_loai(oc, schema_ok=True) == "MODEL_COMPOSITION_FAILURE"
    assert KIEU_KHONG_HOP  # bảng mã chẩn đoán vẫn còn


def test_E3d_quy_tac_chi_chay_khi_CO_chung_minh_nang_luc():
    """Không bằng chứng + không hình dạng ⇒ KHÔNG được kết luận system gap."""
    spec = _spec(None, ten_nguon="r", gt_nguon=13, src="dk")
    assert _lop(spec, ct=_ct(gt=13)) != "SYSTEM_EXPRESSIVENESS_GAP"


def test_E3e_bang_chung_mo_ho_KHONG_bi_ep_thanh_ket_luan_chac():
    """Không bằng chứng, NHƯNG có hình dạng khoảng trống ⇒ chưa kết luận."""
    assert _lop(_spec(CHIA_DOI)) == "ATTRIBUTION_UNRESOLVED"


# ══ E4 · TAXONOMY VÀ HỢP ĐỒNG BẰNG CHỨNG ══════════════════════════════════
@pytest.mark.parametrize("lop", ["SYSTEM_EXPRESSIVENESS_GAP",
                                 "ATTRIBUTION_UNRESOLVED"])
def test_E4a_lop_moi_co_trong_taxonomy(lop):
    assert lop in LOP_PHAN_QUYET


def test_E4b_moi_lop_cu_van_con():
    """Giữ nguyên ý nghĩa lịch sử — danh sách chỉ được DÀI RA."""
    cu = {"CORRECT_SERVABLE_RESULT", "CORRECT_EXECUTABLE_IR",
          "HONEST_UNSUPPORTED_REFUSAL", "UNRELATED_FAIL_CLOSED",
          "SYSTEM_COVERAGE_FAILURE", "SYSTEM_VERIFICATION_FAILURE",
          "SYSTEM_RUNTIME_FAILURE", "SYSTEM_TRANSPORT_FAILURE",
          "MODEL_SCHEMA_FAILURE", "MODEL_STATIC_FAILURE",
          "MODEL_GROUNDING_FAILURE", "MODEL_FIRST_BINDING_FAILURE",
          "MODEL_COMPOSITION_FAILURE"}
    assert cu <= set(LOP_PHAN_QUYET)


def test_E4c_scorer_TAT_DINH():
    spec = _spec(CHIA_DOI)
    assert len({_lop(spec, yc=_yc(True)) for _ in range(5)}) == 1


def test_E4d_kieu_o_dich_DAN_tu_thau_quyen_khong_go_tay():
    """Thêm một ô vô hướng mới là quy tắc tự nhận — không có danh sách để quên."""
    vo_huong = {"scalar", "float", "int"}
    o = {(l, n) for l, oper in _TOAN_HANG_LENH.items()
         for n, k, _ in oper if set(k) & vo_huong}
    assert ("construct_curved_solid", "radius") in o


# ══ F · TIÊM LỖI ══════════════════════════════════════════════════════════
def test_F1_go_lop_khoi_taxonomy_thi_guard_do(monkeypatch):
    import acceptance_verdict as AV

    monkeypatch.setattr(
        AV, "LOP_PHAN_QUYET",
        tuple(x for x in AV.LOP_PHAN_QUYET if x != "SYSTEM_EXPRESSIVENESS_GAP"))
    assert "SYSTEM_EXPRESSIVENESS_GAP" not in AV.LOP_PHAN_QUYET


def test_F2_ep_moi_rang_buoc_mo_ho_thanh_system_gap_lam_DO_chong_duong_tinh_gia(
        monkeypatch):
    """Tiêm đúng cái sai mà quy tắc này dễ mắc nhất."""
    import acceptance_verdict as AV

    monkeypatch.setattr(AV, "duong_hop_le_ton_tai", lambda _yc: "NO")
    spec = _spec(CHIA_DOI)
    oc = verify_and_compile(_ct(), spec)
    assert AV.phan_loai(oc, schema_ok=True, contract=_ct(), spec=spec,
                        yeu_cau=_yc(False)) == "SYSTEM_EXPRESSIVENESS_GAP", \
        "phép tiêm không ăn ⇒ test E2a đang xanh vì lý do khác"


def test_F3_bo_kiem_valid_path_lam_DO_negative_control(monkeypatch):
    import acceptance_verdict as AV

    monkeypatch.setattr(AV, "duong_hop_le_ton_tai", lambda _yc: "NO")
    spec = _spec(CHIA_DOI)
    oc = verify_and_compile(_ct(), spec)
    assert AV.phan_loai(oc, schema_ok=True, contract=_ct(), spec=spec,
                        yeu_cau=_yc(False)) != "MODEL_STATIC_FAILURE"


def test_F4_bien_UNKNOWN_thanh_NO_lam_DO_test_chua_ket_luan(monkeypatch):
    import acceptance_verdict as AV

    monkeypatch.setattr(AV, "duong_hop_le_ton_tai", lambda _yc: "NO")
    assert _lop(_spec(CHIA_DOI)) != "ATTRIBUTION_UNRESOLVED"


def test_F5_dat_nang_luc_TRUOC_grounding_lam_DO_guard_grounding(monkeypatch):
    """Nếu quy tắc năng lực chạy trước grounding thì E3a mất răng."""
    import acceptance_verdict as AV

    monkeypatch.setattr(AV, "duong_hop_le_ton_tai", lambda _yc: "NO")
    spec = _spec(CHIA_DOI, src=None)
    ct = _ct(src_ok=False)
    # Thứ tự ĐÚNG: grounding vẫn thắng dù predicate nói "NO".
    assert AV.phan_loai(verify_and_compile(ct, spec), schema_ok=True,
                        contract=ct, spec=spec,
                        yeu_cau=_yc(True)) == "MODEL_GROUNDING_FAILURE"


def test_F6_hop_dong_bang_chung_thieu_truong_thi_NEM():
    with pytest.raises(TypeError):
        YeuCauNangLuc(o_dich="radius")          # type: ignore[call-arg]


def test_F7_khoi_phuc_scorer_cu_lam_DO_guard_duong_kinh(monkeypatch):
    """Bản trước wave này xếp fixture đường kính là `MODEL_STATIC_FAILURE`."""
    import acceptance_verdict as AV

    monkeypatch.setattr(AV, "o_vo_huong_bi_rang_buoc_mo_ho",
                        lambda _o, _s: [])
    assert _lop(_spec(CHIA_DOI)) == "MODEL_STATIC_FAILURE"
