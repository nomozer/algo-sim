# -*- coding: utf-8 -*-
"""W20 — điểm đề định nghĩa bằng quan hệ §16.1 mà chương trình đặt bằng TOẠ ĐỘ (ISSUE-ARCH-CONSTRUCTION-
BINDING-LITERAL-TARGET). 0 lượt gọi.

Nhãn ghi TRƯỚC bản sửa ở `docs/evaluation/geometry/runs/w20-cleanup-premerge/diagnostics/
literal_target_corpus/LABELS.json`; test đọc nhãn từ đó. Probe trước bản sửa (biên `run_pipeline`): hình
chiếu đặt bằng toạ độ ngoài vùng đa diện (L12–L14), toạ độ rồi mới dựng (L16) và bí danh của một điểm đặt
bằng toạ độ (L17, L18) đều được PHỤC VỤ — L14 với đáp số sai 2√14 (đúng: 3√6).

Luật: tên chương trình mang ký hiệu đích của quan hệ được lần theo chuỗi `assign X = var Y`; toạ độ ở bất
kỳ mắt nào của chuỗi (của chính nó, hay của điểm nó trỏ tới — kể cả một đỉnh đề cho) ⇒ quan hệ không được
dựng. Toạ độ hay giá trị bằng nhau không bao giờ là danh tính.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from tests.geometry import test_construction_binding as T
from tests.geometry import route_cases as W

_CORPUS = (Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/w20-cleanup-premerge"
           / "diagnostics/literal_target_corpus/LABELS.json")
_L = json.loads(_CORPUS.read_text(encoding="utf-8"))
NHAN, FD = _L["rows"], _L["fixed_data"]

MA_TOA_DO, TOA_DO = "CONSTRUCTION_REPLACED_BY_COORDINATES", "DEFINED_BY_COORDINATES"
VAN_M = "Gọi M là trung điểm của SA. Tính độ dài đoạn MC."
VAN_M_NGOAI = "Gọi M là trung điểm của SA. Tính khoảng cách từ M đến đường thẳng BC."
VAN_H = "Gọi H là hình chiếu vuông góc của S lên đường thẳng BD. Tính độ dài đoạn SH."
MA_M, MA_H = "đặt M tại toạ độ tự tính", "đặt H tại toạ độ tự tính"
M_DEF = {"id": "M_def", "kind": "str", "label": "Trung điểm M", "value": ["M là trung điểm của SA"]}
H_DEF = {"id": "H_def", "kind": "str", "label": "Hình chiếu H",
         "value": ["H là hình chiếu vuông góc của S lên đường thẳng BD"]}
M_OK, M_SAI = FD["midpoint_M_of_SA"], FD["wrong_M"]
H_OK, H_SAI = FD["projection_H_of_S_on_BD"], FD["wrong_H_on_line_BD"]


def lit(t: str, at: list, *, ma: str | None = None, fid: str | None = None) -> dict:
    return {"kind": "declare_point", "target_var": t, "at": list(at),
            **({"model_assumption": ma} if ma else {}), **({"source_fact_id": fid} if fid else {})}


def u3_m(them, **kw):
    return T._p1(VAN_M, them, "M", "C", **kw)


def u3_h(them, **kw):
    return T._p1(VAN_H, [T._duong("BD", "B", "D")] + them, "S", "H", **kw)


def out_m(them, **kw):
    return T._p1(VAN_M_NGOAI, [T._duong("BC", "B", "C")] + them, "M", "BC", nen=T.NGOAI_VUNG, co_khoi=False, **kw)


def out_h(them, **kw):
    return T._p1(VAN_H, [T._duong("BD", "B", "D")] + them, "S", "H", nen=T.NGOAI_VUNG, co_khoi=False, **kw)


_H = ({"name": "H", "type": "point3"},)
CA = {
    "C1_mid_constructed_U3": T.CA["B1_mid_ok"],
    "C2_proj_constructed_U3": T.CA["B10_proj_line_ok"],
    "C3_mid_divide_half_U3": T.CA["B20_divide_half_ok"],
    "C4_relation_not_realized_U3": T.CA["B21_not_realized"],
    "C5_mid_constructed_outside": lambda: out_m([T._mid("M", "S", "A")]),
    "C6_proj_constructed_outside": lambda: out_h([T._proj("H", "S", "BD")]),
    "C7_layout_only_outside": lambda: T._p1("Tính độ dài đoạn SC.", [], "S", "C", nen=T.NGOAI_VUNG, co_khoi=False),
    "C8_alias_to_constructed_U3": T.CA["B8_alias_ok"],
    "C9_layout_only_outside_distance_clue": lambda: T._p1(
        "Tính khoảng cách từ S đến đường thẳng BC.", [T._duong("BC", "B", "C")], "S", "BC",
        nen=T.NGOAI_VUNG, co_khoi=False),
    "L1_mid_U3_assumption": lambda: u3_m([lit("M", M_OK, ma=MA_M)]),
    "L2_mid_U3_bogus_fid": lambda: u3_m([lit("M", M_OK, ma=MA_M, fid="M_toa_do")]),
    "L3_mid_U3_relation_fact": lambda: u3_m([lit("M", M_OK, fid="M_def")], facts=(M_DEF,)),
    "L4_mid_U3_wrong_coords": lambda: u3_m([lit("M", M_SAI, ma=MA_M, fid="M_toa_do")]),
    "L5_mid_outside_assumption": lambda: out_m([lit("M", M_OK, ma=MA_M)]),
    "L6_mid_outside_bogus_fid": lambda: out_m([lit("M", M_OK, ma=MA_M, fid="M_toa_do")]),
    "L7_mid_outside_relation_fact": lambda: out_m([lit("M", M_OK, fid="M_def")], facts=(M_DEF,)),
    "L8_mid_outside_wrong_coords": lambda: out_m([lit("M", M_SAI, ma=MA_M, fid="M_toa_do")]),
    "L9_proj_U3_assumption": lambda: u3_h([lit("H", H_OK, ma=MA_H)]),
    "L10_proj_U3_bogus_fid": lambda: u3_h([lit("H", H_OK, ma=MA_H, fid="H_toa_do")]),
    "L11_proj_U3_relation_fact": lambda: u3_h([lit("H", H_OK, fid="H_def")], facts=(H_DEF,)),
    "L12_proj_outside_bogus_fid": lambda: out_h([lit("H", H_OK, ma=MA_H, fid="H_toa_do")]),
    "L13_proj_outside_relation_fact": lambda: out_h([lit("H", H_OK, fid="H_def")], facts=(H_DEF,)),
    "L14_proj_outside_wrong_coords": lambda: out_h([lit("H", H_SAI, ma=MA_H, fid="H_toa_do")]),
    "L15_mid_U3_literal_twin_of_constructed": lambda: u3_m([lit("M", M_OK, ma=MA_M, fid="M_toa_do"),
                                                            T._mid("N", "S", "A")]),
    "L16_mid_U3_literal_then_constructed": lambda: u3_m([lit("M", M_OK, ma=MA_M, fid="M_toa_do"),
                                                         T._mid("M", "S", "A")]),
    "L17_proj_outside_alias_to_vertex": lambda: out_h([T._gan("H", "A")], khai=_H),
    "L18_proj_outside_alias_to_cited_literal": lambda: out_h([lit("Q", H_OK, fid="H_def"), T._gan("H", "Q")],
                                                             khai=_H, facts=(H_DEF,)),
}
#: Đích của quan hệ ở mỗi hàng L (mọi hàng L đặt đích bằng toạ độ, trực tiếp hay qua bí danh).
DICH = {c: ("H" if "_proj_" in c else "M") for c in CA if c.startswith("L")}
#: Hàng L mà grounding (⑥/⑦, chạy trước) KHÔNG bắt — trước bản sửa: phục vụ, hay chỉ bị cổng giả định
#: (vùng U3) chặn với mã chung.
QUA_GROUNDING = ("L10_proj_U3_bogus_fid", "L11_proj_U3_relation_fact", "L12_proj_outside_bogus_fid",
                 "L13_proj_outside_relation_fact", "L14_proj_outside_wrong_coords",
                 "L16_mid_U3_literal_then_constructed", "L17_proj_outside_alias_to_vertex",
                 "L18_proj_outside_alias_to_cited_literal")


def _doi_chieu(ca: str):
    from app.simulation.semantic_program.construction_binding import doi_chieu_phep_dung
    from app.simulation.semantic_program.validator import validate_semantic_program

    contract, program = CA[ca]()
    v = validate_semantic_program(program)
    assert v.spec is not None, (ca, v.errors)
    return doi_chieu_phep_dung(contract, v.spec)


def test_moi_hang_nhan_co_mot_ca_va_nguoc_lai():
    assert set(CA) == set(NHAN)


@pytest.mark.parametrize("ca", sorted(CA))
def test_tuyen_san_pham_theo_nhan(ca):
    """Nhãn: phục vụ, hay từ chối với nguyên nhân KHÁC `SOURCE` (đề không sai). C7 ở biên pipeline bị cổng
    miền chặn vì lý do khác (LABELS amendment_1); ở route nó được phục vụ như nhãn."""
    _sp, out, _sc = W.chay(*CA[ca]())
    if NHAN[ca]["expect"] == "served":
        assert out.servable, (ca, out.stage_reached, out.reason_code, out.details[:4])
    else:
        assert not out.servable and out.refusal_cause != "SOURCE", (
            ca, out.servable, out.stage_reached, out.reason_code, out.refusal_cause)


@pytest.mark.parametrize("ca", QUA_GROUNDING)
def test_dich_dat_bang_toa_do_bi_tu_choi_o_doi_chieu_moi_vung(ca):
    _sp, out, _sc = W.chay(*CA[ca]())
    assert (out.servable, out.stage_reached, out.reason_code, out.refusal_cause) == (
        False, "construction_binding", MA_TOA_DO, "CONSTRUCTION"), (ca, out.stage_reached, out.reason_code,
                                                                     out.construction_binding, out.details[:4])
    assert out.construction_binding.get(DICH[ca]) == TOA_DO, (ca, out.construction_binding)


@pytest.mark.parametrize("ca", sorted(DICH))
def test_doi_chieu_mot_minh_van_bat_moi_dich_dat_bang_toa_do(ca):
    """Phòng thủ nhiều lớp: không nhờ grounding chạy trước — chính bước đối chiếu ghi và từ chối."""
    dc = _doi_chieu(ca)
    assert (dc.trang_thai.get(DICH[ca]), dc.reason_code) == (TOA_DO, MA_TOA_DO), (ca, dc.trang_thai, dc.details)


@pytest.mark.parametrize("ca", sorted(c for c in CA if c.startswith("C")))
def test_doi_chung_khong_bi_ghi_toa_do(ca):
    """Toạ độ bố cục (năm điểm đề cho), phép dựng tương đương (`divide_segment` 1/2, bí danh của một điểm
    ĐƯỢC DỰNG) và quan hệ chương trình không dùng tới: không trạng thái mới, không mã từ chối."""
    dc = _doi_chieu(ca)
    assert TOA_DO not in dc.trang_thai.values() and dc.reason_code is None, (ca, dc.trang_thai, dc.reason_code)


def test_trung_toa_do_khac_danh_tinh_khong_phai_bang_chung():
    """H đặt đúng toạ độ (3; 3; 0), K = hình chiếu của S lên BD dựng thật, ngoài vùng đa diện: K trùng toạ
    độ với H nhưng không phải H của đề."""
    _sp, out, _sc = W.chay(*out_h([lit("H", H_OK, fid="H_def"), T._proj("K", "S", "BD")], facts=(H_DEF,)))
    assert (out.servable, out.reason_code) == (False, MA_TOA_DO), (out.stage_reached, out.construction_binding)
    assert (out.construction_binding.get("H"), out.construction_binding.get("K")) == (TOA_DO, "AUXILIARY"), (
        out.construction_binding)


def test_khai_bao_khong_toa_do_roi_dung_van_khop():
    """Khai đích KHÔNG kèm toạ độ rồi dựng đúng: không phải lời khẳng định toạ độ."""
    _sp, out, _sc = W.chay(*u3_m([T._mid("M", "S", "A")], khai=({"name": "M", "type": "point3"},)))
    assert out.servable and out.construction_binding.get("M") == "MATCHED", (
        out.stage_reached, out.reason_code, out.construction_binding)


def test_chu_the_neu_quan_he_de_va_viec_chuong_trinh_da_lam():
    """Cặp [quan hệ đề nêu, cách chương trình đã đặt điểm ấy]. Từ run `cuboid-final-review` vế sau viết ở thể bị
    động, không kèm tên điểm (W20 ghi `đặt H bằng toạ độ cho sẵn`), để lời học sinh nói "vì điểm này được đặt bằng
    toạ độ" mà không ghép chuỗi theo ký hiệu."""
    _sp, out, _sc = W.chay(*CA["L13_proj_outside_relation_fact"]())
    assert out.reason_subjects == ["H là hình chiếu của S lên BD", "được đặt bằng toạ độ"], out.reason_subjects
    _sp, out, _sc = W.chay(*CA["L17_proj_outside_alias_to_vertex"]())
    assert out.reason_subjects == ["H là hình chiếu của S lên BD", "được lấy trùng với điểm A"], out.reason_subjects


def test_ma_moi_co_nguyen_nhan_dung_hinh_va_khong_gui_di_sua():
    from app.ai.pipeline import KHONG_SUA_NGUON
    from app.simulation.semantic_program.refusal_cause import theo_ma

    assert theo_ma(MA_TOA_DO) == "CONSTRUCTION"
    assert MA_TOA_DO in KHONG_SUA_NGUON


def _pipeline(ca: str) -> dict:
    from app.learner_messages import attach_learner_reason
    from app.simulation.semantic_program.validator import validate_semantic_program
    from scripts import generate_generic_tier_a_fixtures as GEN

    contract, program = CA[ca]()
    v = validate_semantic_program(program)
    assert v.spec is not None, v.errors
    return attach_learner_reason(asyncio.run(GEN._run_frozen_program(contract.problem_text, contract, v.spec)))


_DUNG_LAI = " Hệ tạm dừng để tránh đưa ra kết quả chưa kiểm chứng."


@pytest.mark.parametrize("ca,cau", [
    ("L14_proj_outside_wrong_coords", "Hệ chưa kiểm chứng được H là hình chiếu của S lên BD, vì điểm này được đặt "
                                      "bằng toạ độ thay vì dựng từ quan hệ trong đề."),
    ("L17_proj_outside_alias_to_vertex", "Hệ chưa kiểm chứng được H là hình chiếu của S lên BD, vì điểm này được "
                                         "lấy trùng với điểm A thay vì dựng từ quan hệ trong đề."),
    ("L16_mid_U3_literal_then_constructed", "Hệ chưa kiểm chứng được M là trung điểm của SA, vì điểm này được đặt "
                                            "bằng toạ độ thay vì dựng từ quan hệ trong đề."),
])
def test_bien_pipeline_khong_dua_dap_so_va_noi_dung_gioi_han_kiem_chung(ca, cau):
    """L14 phục vụ đáp số SAI và L17 đo SA thay cho SH trước bản sửa W20. Lời (cuboid-final-review): nêu quan hệ
    của đề và cách điểm bị đặt, nói hệ CHƯA KIỂM CHỨNG được — không nói hình khác, không bảo sửa đề, không hứa gửi
    lại sẽ được (chưa có cơ chế bảo đảm điều đó). L16 là cùng lời với tên và quan hệ khác: không ghép cứng."""
    env = _pipeline(ca)
    assert (env["status"], env.get("reason_code"), env.get("refusal_cause")) == (
        "unsupported", MA_TOA_DO, "CONSTRUCTION"), {k: env.get(k) for k in ("status", "stage_reached", "reason_code")}
    assert not (env.get("scene3d") or {}).get("objects"), "lời từ chối không mang cảnh hay đáp số"
    msg = env["learner_reason"]
    assert msg == cau + _DUNG_LAI, msg
    for cam in ("sửa đề", "kiểm tra lại đề", "đề sai", "đề bài sai", "gửi lại", "hình khác", "dựng lệch", "_"):
        assert cam not in msg, (cam, msg)


def test_loi_ghep_tu_chu_the_co_cau_truc():
    """Tên, quan hệ và cách đặt đều đọc từ `reason_subjects` — không ký hiệu nào viết cứng; nhiều cặp gộp
    lại; tên máy (có `_`) không bao giờ lên lời; không có chủ thể thì vẫn nói đúng giới hạn."""
    from app.learner_messages import learner_reason

    def loi(*chu_the: str) -> str:
        return learner_reason({"reason_code": MA_TOA_DO, "refusal_cause": "CONSTRUCTION",
                               "stage_reached": "construction_binding", "reason_subjects": list(chu_the)})

    assert loi("K là hình chiếu của P lên (XYZ)", "được đặt bằng toạ độ") == (
        "Hệ chưa kiểm chứng được K là hình chiếu của P lên (XYZ), vì điểm này được đặt bằng toạ độ thay vì dựng từ "
        "quan hệ trong đề." + _DUNG_LAI)
    assert loi("K là hình chiếu của P lên (XYZ)", "được đặt bằng toạ độ",
               "N là trung điểm của PQ", "được lấy trùng với điểm X") == (
        "Hệ chưa kiểm chứng được K là hình chiếu của P lên (XYZ) và N là trung điểm của PQ, vì các điểm này được "
        "đặt bằng toạ độ hoặc được lấy trùng với điểm X thay vì dựng từ quan hệ trong đề." + _DUNG_LAI)
    chung = ("Hệ chưa kiểm chứng được một điểm đề bài nêu bằng quan hệ, vì điểm này được đặt bằng toạ độ thay vì "
             "dựng từ quan hệ trong đề." + _DUNG_LAI)
    assert loi() == chung
    assert loi("K_tmp là hình chiếu của P lên (XYZ)", "được đặt bằng toạ độ") == chung
