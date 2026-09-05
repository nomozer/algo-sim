# -*- coding: utf-8 -*-
"""CURVED_CONSTRUCTION_GROUNDING — khối cong khai bằng VÔ HƯỚNG. 0 lượt gọi.

    Nguồn: lượt V3 held-out 2026-09-05 (`docs/CURVED_V3_LIVE_ACCEPTANCE.md`),
    0/9 ca dương servable.

Lượt ấy chứng minh một mâu thuẫn ở tầng dựng, không phải ở mô hình:

    `construct_curved_solid` BẮT BUỘC một `anchor: point3`
    grounding gate CẤM khai `point3` cho đề không đặt tên điểm nào
    ⇒ đề "khối cầu bán kính 9" không có chương trình hợp lệ nào.

Và với trụ/nón còn nặng hơn: `radius` chỉ mở cho khối cầu, nên trụ/nón buộc
phải có `rim_point` — một điểm trên vành, thứ đề SGK không bao giờ đặt tên.

Hai thứ tách bạch và test này khoá đúng ranh giới giữa chúng:

    HÌNH HỌC NGỮ NGHĨA   dữ kiện của đề, hoặc vật DỰNG bằng phép của IR
    POSE TRÌNH BÀY       một hệ quy chiếu tất định, KHÔNG phải dữ kiện

Pose canonical không bao giờ trở thành một `point3` có tên trong bộ nhớ ngữ
nghĩa — nên nó không thể làm chứng cứ cho một phép đo hay quan hệ nào.
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GOC))

from app.simulation.geometry.curved import (  # noqa: E402
    KHOI_CONG,
    CurvedSolid,
    dien_tich_mat_cong,
    the_tich,
)
from app.simulation.geometry.exact import Point3  # noqa: E402
from app.simulation.semantic_program.contract import (  # noqa: E402
    SemanticProgramSpec,
)
from app.simulation.semantic_program.obligations import Obligation  # noqa: E402
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

VB = {"containers": [], "pointers": [], "value_boxes": []}


def _spec(decls, stmts, **kw):
    return SemanticProgramSpec.model_validate({
        "spec_version": "1.0",
        "title": kw.get("title", "Khối cong"),
        "description": "Dựng khối cong rồi đo.",
        "pedagogical_intent": "Thấy vô hướng quyết định phép đo.",
        "memory_declarations": decls, "statements": stmts,
        "visual_bindings": VB})


def _dl(r):
    """Giá trị ĐO ĐƯỢC, đọc từ `final_memory`.

    ⚠️ KHÔNG đọc `scene3d`: `route` cố ý không dựng nó (hướng phụ thuộc một
    chiều — `pipeline._dung_scene3d` mới là người đổ). Khẳng định trên
    `scene3d` ở đây sẽ đo tầng trình bày thay vì đo phép tính, và sẽ đỏ vì một
    lý do không liên quan gì tới điều test muốn khoá.
    """
    mem = getattr(r, "final_memory", None) or {}
    ra = []
    for v in mem.values():
        if isinstance(v, dict):
            v = v.get("value", v)
        ra.append(str(v))
    return ra


# ══ D1 — NỀN TẢNG DƯƠNG ═══════════════════════════════════════════════════
DE_CAU = ("Cho khối cầu (S) có bán kính bằng 9. Tính thể tích khối cầu và "
          "diện tích mặt cầu (S).")


def _hd_cau():
    return RequestContract(
        problem_text=DE_CAU,
        input_facts=[{"fact_id": "r", "label": "bán kính khối cầu (S)",
                      "values": [9], "provenance": "confirmed"}],
        obligations=(Obligation(kind="volume", container="S",
                                params={"witness": "V"}),
                     # ⚠️ `lateral_area`, KHÔNG phải `area`: nghĩa vụ `area`
                     # nhận `polygon3|section|circle3`, cố ý tách khỏi mặt
                     # cong (`measure_contract` §NGHIA_VU_DO). Lượt V3 cho
                     # thấy `analyze` phát `area` cho "diện tích mặt cầu" —
                     # đó là lệch phía ANALYZE, ngoài phạm vi wave này.
                     Obligation(kind="lateral_area", container="S",
                                params={"witness": "A"})))


def test_D1_1_cau_CHI_co_ban_kinh_khong_co_diem_nao():
    """`c1a` của V3 — ca đơn giản nhất, và ca đã giết cả lượt đo."""
    spec = _spec(
        [{"name": "r", "type": "float", "initial_value": 9,
          "source_fact_id": "r"},
         {"name": "S", "type": "curved_solid"},
         {"name": "V", "type": "float"}, {"name": "A", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "S",
          "curved_kind": "ball", "radius": "r", "label": "(S)"},
         {"kind": "assign", "target_var": "V",
          "expr": {"kind": "measure", "quantity": "volume", "of": "S"}},
         {"kind": "assign", "target_var": "A",
          "expr": {"kind": "measure", "quantity": "lateral_area", "of": "S"}}])
    out = verify_and_compile(_hd_cau(), spec)
    assert out.executable, getattr(out, "reason", None)
    assert set(_dl(out)) >= {"972π", "324π"}, _dl(out)


def test_D1_2_cau_co_TAM_grounded_thi_dung_tam_that():
    """Pose canonical KHÔNG được thay thế một tâm đề đã cho."""
    de = "Cho mặt cầu tâm I bán kính bằng 3, biết I(1;0;0)."
    hd = RequestContract(
        problem_text=de,
        input_facts=[{"fact_id": "tam", "label": "tâm I", "values": ["I"],
                      "provenance": "confirmed"},
                     {"fact_id": "r", "label": "bán kính", "values": [3],
                      "provenance": "confirmed"}],
        obligations=(Obligation(kind="volume", container="S",
                                params={"witness": "V"}),))
    spec = _spec(
        [{"name": "r", "type": "float", "initial_value": 3,
          "source_fact_id": "r"},
         {"name": "I", "type": "point3", "initial_value": [1, 0, 0],
          "source_fact_id": "tam",
          "model_assumption": "Đặt I trên Ox."},
         {"name": "S", "type": "curved_solid"}, {"name": "V", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "S",
          "curved_kind": "ball", "anchor": "I", "radius": "r"},
         {"kind": "assign", "target_var": "V",
          "expr": {"kind": "measure", "quantity": "volume", "of": "S"}}])
    out = verify_and_compile(hd, spec)
    assert out.executable, getattr(out, "reason", None)
    kh = (out.final_memory or {}).get("S")
    assert kh is not None
    # Tâm THẬT của đề, KHÔNG phải gốc canonical — và vật tự khai điều đó.
    assert kh.pose_canonical is False
    assert [kh.anchor.x, kh.anchor.y, kh.anchor.z] == [1, 0, 0]


DE_TRU_TAM = ("Một hình trụ có hai đáy tâm P và P′ với PP′ = 5, bán kính đáy "
              "bằng 6. Tính diện tích xung quanh của hình trụ và thể tích "
              "khối trụ.")


def test_D1_3_tru_co_hai_tam_grounded_va_ban_kinh_THANG():
    """`c4b` của V3 — trước wave này lược đồ CẤM `radius` cho trụ."""
    hd = RequestContract(
        problem_text=DE_TRU_TAM,
        input_facts=[{"fact_id": "pp", "label": "PP'", "values": [5],
                      "provenance": "confirmed"},
                     {"fact_id": "r", "label": "bán kính đáy", "values": [6],
                      "provenance": "confirmed"},
                     {"fact_id": "tam", "label": "tâm hai đáy",
                      "values": ["P", "P′"], "provenance": "confirmed"}],
        obligations=(Obligation(kind="lateral_area", container="T",
                                params={"witness": "Sxq"}),
                     Obligation(kind="volume", container="T",
                                params={"witness": "V"})))
    spec = _spec(
        [{"name": "r", "type": "float", "initial_value": 6,
          "source_fact_id": "r"},
         {"name": "P", "type": "point3", "initial_value": [0, 0, 0],
          "source_fact_id": "tam",
          "model_assumption": "Đặt P tại gốc."},
         {"name": "P_prime", "type": "point3", "initial_value": [0, 0, 5],
          "source_fact_id": "tam",
          "model_assumption": "Đặt P′ trên Oz, PP′ = 5."},
         {"name": "T", "type": "curved_solid"},
         {"name": "Sxq", "type": "float"}, {"name": "V", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "T",
          "curved_kind": "cylinder", "anchor": "P", "apex_or_top": "P_prime",
          "radius": "r"},
         {"kind": "assign", "target_var": "Sxq",
          "expr": {"kind": "measure", "quantity": "lateral_area", "of": "T"}},
         {"kind": "assign", "target_var": "V",
          "expr": {"kind": "measure", "quantity": "volume", "of": "T"}}])
    out = verify_and_compile(hd, spec)
    assert out.executable, getattr(out, "reason", None)
    assert set(_dl(out)) >= {"60π", "180π"}, _dl(out)


def _hd_scalar(de, obl, extra=()):
    facts = [{"fact_id": "r", "label": "bán kính đáy", "values": [7],
              "provenance": "confirmed"},
             {"fact_id": "h", "label": "chiều cao", "values": [10],
              "provenance": "confirmed"}]
    return RequestContract(problem_text=de, input_facts=facts + list(extra),
                           obligations=obl)


def _spec_scalar(kind):
    return _spec(
        [{"name": "r", "type": "float", "initial_value": 7,
          "source_fact_id": "r"},
         {"name": "h", "type": "float", "initial_value": 10,
          "source_fact_id": "h"},
         {"name": "K", "type": "curved_solid"},
         {"name": "V", "type": "float"}, {"name": "S", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "K",
          "curved_kind": kind, "radius": "r", "height": "h"},
         {"kind": "assign", "target_var": "V",
          "expr": {"kind": "measure", "quantity": "volume", "of": "K"}},
         {"kind": "assign", "target_var": "S",
          "expr": {"kind": "measure", "quantity": "lateral_area", "of": "K"}}])


def test_D1_4_tru_CHI_co_ban_kinh_va_chieu_cao():
    de = "Cho hình trụ có bán kính đáy bằng 7 và chiều cao bằng 10."
    hd = _hd_scalar(de, (Obligation(kind="volume", container="K",
                                    params={"witness": "V"}),
                         Obligation(kind="lateral_area", container="K",
                                    params={"witness": "S"})))
    out = verify_and_compile(hd, _spec_scalar("cylinder"))
    assert out.executable, getattr(out, "reason", None)
    assert set(_dl(out)) >= {"490π", "140π"}, _dl(out)


def test_D1_5_non_CHI_co_ban_kinh_va_chieu_cao():
    """`c8b` — nón r=7, h=10. `Sxq = πrl` với `l = √149` ⇒ phải giữ Radical."""
    de = "Cho hình nón có bán kính đáy bằng 7 và chiều cao bằng 10."
    hd = _hd_scalar(de, (Obligation(kind="volume", container="K",
                                    params={"witness": "V"}),
                         Obligation(kind="lateral_area", container="K",
                                    params={"witness": "S"})))
    out = verify_and_compile(hd, _spec_scalar("cone"))
    assert out.executable, getattr(out, "reason", None)
    dl = _dl(out)
    assert "490π/3" in dl, dl
    assert any("√149" in str(x) for x in dl), dl


def test_D1_6_duong_rim_point_CU_khong_doi():
    """Hồi quy: đường gốc phải cho y hệt kết quả cũ."""
    de = "Cho hình trụ đáy tâm O đi qua A, đỉnh trên O′."
    hd = RequestContract(
        problem_text=de,
        input_facts=[{"fact_id": "f", "label": "ba điểm",
                      "values": ["O", "O′", "A"], "provenance": "confirmed"}],
        obligations=(Obligation(kind="volume", container="T",
                                params={"witness": "V"}),))
    spec = _spec(
        [{"name": "O", "type": "point3", "initial_value": [0, 0, 0],
          "source_fact_id": "f"},
         {"name": "O_prime", "type": "point3", "initial_value": [0, 0, 3],
          "source_fact_id": "f"},
         {"name": "A", "type": "point3", "initial_value": [2, 0, 0],
          "source_fact_id": "f"},
         {"name": "T", "type": "curved_solid"}, {"name": "V", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "T",
          "curved_kind": "cylinder", "anchor": "O", "apex_or_top": "O_prime",
          "rim_point": "A"},
         {"kind": "assign", "target_var": "V",
          "expr": {"kind": "measure", "quantity": "volume", "of": "T"}}])
    out = verify_and_compile(hd, spec)
    assert out.executable, getattr(out, "reason", None)
    assert "12π" in _dl(out), _dl(out)


# ══ D2 — AN TOÀN GROUNDING ════════════════════════════════════════════════
def test_D2_1_vo_huong_TU_KHAI_khong_co_nguon_thi_DO():
    """Bán kính không truy được về đề ⇒ cổng xuất xứ phải chặn."""
    spec = _spec(
        [{"name": "r", "type": "float", "initial_value": 9},   # KHÔNG có fact
         {"name": "S", "type": "curved_solid"},
         {"name": "V", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "S",
          "curved_kind": "ball", "radius": "r"},
         {"kind": "assign", "target_var": "V",
          "expr": {"kind": "measure", "quantity": "volume", "of": "S"}}])
    out = verify_and_compile(_hd_cau(), spec)
    assert not out.executable


def test_D2_2_diem_suy_ra_khai_thang_toa_do_VAN_bi_chan():
    """R0 không được nới: pose canonical KHÔNG mở cửa cho điểm bịa."""
    from app.simulation.semantic_program.grounding_gate import (
        ERR_RUA_NANG_LUC,
        check_grounding,
    )

    spec = _spec(
        [{"name": "r", "type": "float", "initial_value": 9,
          "source_fact_id": "r"},
         {"name": "P_bia", "type": "point3", "initial_value": [2, 2, 2],
          "model_assumption": "điểm đối diện trong hình hộp bao quanh"},
         {"name": "S", "type": "curved_solid"}, {"name": "V", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "S",
          "curved_kind": "ball", "radius": "r"},
         {"kind": "assign", "target_var": "V",
          "expr": {"kind": "measure", "quantity": "volume", "of": "S"}}])
    kq = check_grounding(_hd_cau(), spec)
    assert not kq.ok
    assert kq.error_code == ERR_RUA_NANG_LUC


def test_D2_3_pose_canonical_KHONG_vao_bo_nho_ngu_nghia():
    """Không có tên nào trỏ pose ⇒ không phép đo nào lấy nó làm chứng cứ."""
    spec = _spec(
        [{"name": "r", "type": "float", "initial_value": 9,
          "source_fact_id": "r"},
         {"name": "S", "type": "curved_solid"},
         {"name": "V", "type": "float"}, {"name": "A", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "S",
          "curved_kind": "ball", "radius": "r"},
         {"kind": "assign", "target_var": "V",
          "expr": {"kind": "measure", "quantity": "volume", "of": "S"}},
         {"kind": "assign", "target_var": "A",
          "expr": {"kind": "measure", "quantity": "lateral_area", "of": "S"}}])
    out = verify_and_compile(_hd_cau(), spec)
    assert out.executable
    mem = (out.envelope or {}).get("final_memory") or {}
    diem = {k: v for k, v in mem.items()
            if isinstance(v, dict) and v.get("type") == "point3"}
    assert not diem, f"pose lọt vào bộ nhớ ngữ nghĩa: {diem}"


def test_D2_4_de_DAT_TEN_tam_thi_lien_ket_do_phai_giu():
    """Có tâm grounded thì vật KHÔNG được tự nhận là pose canonical."""
    out = verify_and_compile(*_D2_4())
    assert out.executable
    kh = (out.final_memory or {}).get("S")
    assert kh is not None and kh.pose_canonical is False


def _D2_4():
    de = "Cho mặt cầu tâm I bán kính bằng 3, biết I(1;0;0)."
    hd = RequestContract(
        problem_text=de,
        input_facts=[{"fact_id": "tam", "label": "tâm I", "values": ["I"],
                      "provenance": "confirmed"},
                     {"fact_id": "r", "label": "bán kính", "values": [3],
                      "provenance": "confirmed"}],
        obligations=(Obligation(kind="volume", container="S",
                                params={"witness": "V"}),))
    spec = _spec(
        [{"name": "r", "type": "float", "initial_value": 3,
          "source_fact_id": "r"},
         {"name": "I", "type": "point3", "initial_value": [1, 0, 0],
          "source_fact_id": "tam",
          "model_assumption": "Đặt I trên Ox."},
         {"name": "S", "type": "curved_solid"}, {"name": "V", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "S",
          "curved_kind": "ball", "anchor": "I", "radius": "r"},
         {"kind": "assign", "target_var": "V",
          "expr": {"kind": "measure", "quantity": "volume", "of": "S"}}])
    return hd, spec


# ══ D3 — AN TOÀN MIỀN GIÁ TRỊ ═════════════════════════════════════════════
@pytest.mark.parametrize("r", [0, -1])
def test_D3_1_ban_kinh_khong_duong_thi_NEM(r):
    from app.simulation.geometry.curved import GeometryError

    with pytest.raises(GeometryError):
        CurvedSolid("ball", Point3(Fraction(0), Fraction(0), Fraction(0)),
                    None, None, Fraction(r))


@pytest.mark.parametrize("h", [0, -1])
def test_D3_2_chieu_cao_khong_duong_thi_NEM(h):
    from app.simulation.geometry.curved import GeometryError

    with pytest.raises(GeometryError):
        CurvedSolid("cylinder", Point3(Fraction(0), Fraction(0), Fraction(0)),
                    None, None, Fraction(4), height_sq_khai=Fraction(h))


def test_D3_3_khai_ca_rim_lan_radius_thi_LUOC_DO_chan():
    with pytest.raises(Exception):
        _spec([{"name": "S", "type": "curved_solid"}],
              [{"kind": "construct_curved_solid", "target_var": "S",
                "curved_kind": "ball", "anchor": "O", "rim_point": "A",
                "radius": "r"}])


def test_D3_4_thieu_ca_rim_lan_radius_thi_LUOC_DO_chan():
    with pytest.raises(Exception):
        _spec([{"name": "S", "type": "curved_solid"}],
              [{"kind": "construct_curved_solid", "target_var": "S",
                "curved_kind": "ball", "anchor": "O"}])


def test_D3_5_tru_thieu_ca_height_lan_apex_thi_chan():
    """Không trục thì không có khối — phải chặn ở lược đồ."""
    with pytest.raises(Exception):
        _spec([{"name": "S", "type": "curved_solid"}],
              [{"kind": "construct_curved_solid", "target_var": "S",
                "curved_kind": "cylinder", "radius": "r"}])


def test_D3_6_cau_mang_height_thi_chan():
    with pytest.raises(Exception):
        _spec([{"name": "S", "type": "curved_solid"}],
              [{"kind": "construct_curved_solid", "target_var": "S",
                "curved_kind": "ball", "radius": "r", "height": "h"}])


# ══ AUTHORITY — một bảng, không nhánh theo tên hình ═══════════════════════
def test_A1_moi_family_khai_nang_luc_cua_chinh_no():
    for k in ("ball", "cylinder", "cone"):
        kc = KHOI_CONG[k]
        assert kc.khai_bang_ban_kinh is True, f"{k} phải nhận `radius`"
        assert kc.cho_pose_canonical is True, f"{k} phải nhận pose canonical"
    assert KHOI_CONG["ball"].can_chieu_cao is False
    assert KHOI_CONG["cylinder"].can_chieu_cao is True
    assert KHOI_CONG["cone"].can_chieu_cao is True


def test_A2_kernel_do_dung_khi_khai_bang_vo_huong():
    """Đo thẳng trên kernel — tách khỏi mọi tầng phía trên."""
    g = Point3(Fraction(0), Fraction(0), Fraction(0))
    cau = CurvedSolid("ball", g, None, None, Fraction(81))
    assert str(the_tich(cau)) == "972π"
    assert str(dien_tich_mat_cong(cau)) == "324π"
    tru = CurvedSolid("cylinder", g, None, None, Fraction(49),
                      height_sq_khai=Fraction(100))
    assert str(the_tich(tru)) == "490π"
    assert str(dien_tich_mat_cong(tru)) == "140π"
    non = CurvedSolid("cone", g, None, None, Fraction(49),
                      height_sq_khai=Fraction(100))
    assert str(the_tich(non)) == "490π/3"
    assert "√149" in str(dien_tich_mat_cong(non))


def test_A3_height_sq_co_MOT_cua_duy_nhat():
    g = Point3(Fraction(0), Fraction(0), Fraction(0))
    tren = Point3(Fraction(0), Fraction(0), Fraction(3))
    a = CurvedSolid("cylinder", g, tren, None, Fraction(4))
    b = CurvedSolid("cylinder", g, None, None, Fraction(4),
                    height_sq_khai=Fraction(9))
    assert a.height_sq == b.height_sq == Fraction(9)
    assert a.radius_sq == b.radius_sq == Fraction(4)
