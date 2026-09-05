# -*- coding: utf-8 -*-
"""Corpus phát triển v1 + GOLD PREFLIGHT cho `CURVED_SECTION_MODEL_DISCOVERABILITY_PROBE`.

**0 lượt gọi model.** Script này chạy TRƯỚC mọi lượt gọi provider và quyết định
lượt đo có được mở hay không.

─── VÌ SAO GOLD PHẢI CHẠY TRƯỚC KHI TIÊU QUOTA ───────────────────────────

Một phép đo *"mô hình có tự tìm ra đường đúng không"* chỉ có nghĩa khi **đường
đúng thật sự đi được**. Nếu hệ hỏng trên một nhánh mà mô hình có quyền chọn hợp
lệ, thì mỗi ca rơi vào nhánh ấy sẽ bị chấm là hỏng vì một lý do **không liên
quan** tới câu hỏi đang đo — và con số cuối cùng không đo cái gì cả.

Gold ở đây là chương trình do NGƯỜI viết, đi đúng primitive tổng quát, chạy qua
đúng đường sản phẩm. Nó trả lời: *"nếu mô hình viết đúng như ta muốn, hệ có phục
vụ không?"* Câu trả lời phải là CÓ trước khi hỏi mô hình.

─── ĐĂNG KÝ TRƯỚC KẾT QUẢ ────────────────────────────────────────────────

Corpus, đáp số kỳ vọng và phân lớp toán tử đều ghi ở đây **trước** lượt gọi, rồi
băm. Runner chỉ gửi `problem_text`; `expected_*` chỉ thuộc scorer.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

GOC = Path(__file__).resolve().parents[1]
if str(GOC) not in sys.path:
    sys.path.insert(0, str(GOC))

from app.simulation.semantic_program.contract import (  # noqa: E402
    SemanticProgramSpec,
)
from app.simulation.semantic_program.obligations import Obligation  # noqa: E402
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

RA = GOC.parent / "docs" / "evaluation" / "geometry" / \
    "curved-section-discoverability-dev-v1"
VB = {"containers": [], "pointers": [], "value_boxes": []}


# ══ CORPUS ĐĂNG KÝ TRƯỚC ═════════════════════════════════════════════════
#
# Tám ca. Ký hiệu **cố ý đa dạng** — không ca nào dùng `C`, `r_C`, `O`, `S`, hay
# cách diễn đạt của V3, để phép đo không đo trúng một thói quen đặt tên.
#
# `expected_operator_class` là thứ wave này thật sự hỏi:
#   `intersect_plane_curved`  — khối cong, mặt phẳng ⊥ trục
#   `construct_section`       — khối ĐA DIỆN
#   `refusal`                 — ngoài bao đóng v1
CORPUS: list[dict[str, Any]] = [
    {
        "case_id": "d1",
        "family": "cylinder",
        "feature": "perpendicular_section_radius_and_area",
        "problem_text":
            "Cho hình trụ có hai đáy là hai đường tròn tâm I và tâm J, bán "
            "kính đáy bằng 12, đường cao IJ bằng 20. Gọi P là một điểm nằm "
            "trên đường tròn đáy tâm I. Gọi M là trung điểm của đoạn IJ. Mặt "
            "phẳng đi qua M và vuông góc với đường thẳng IJ cắt hình trụ theo "
            "một đường tròn (ω). Tính bán kính và diện tích của đường tròn (ω).",
        "expected_obligations": ["radius", "area"],
        "expected_operator_class": "intersect_plane_curved",
        "expected_result_type": "circle3",
        "exact_expected_results": {"radius": "12", "area": "144π"},
        "expected_boundary": None,
    },
    {
        "case_id": "d2",
        "family": "cylinder",
        "feature": "perpendicular_section_off_midpoint_radius_only",
        "problem_text":
            "Một hình trụ có trục là đoạn thẳng EF, bán kính đáy bằng 7 và "
            "EF = 24. Điểm G nằm trên đường tròn đáy tâm E. Lấy điểm H thuộc "
            "đoạn EF sao cho EH = 6. Mặt phẳng đi qua H và vuông góc với EF "
            "cắt hình trụ theo đường tròn (γ). Tính bán kính của đường tròn (γ).",
        "expected_obligations": ["radius"],
        "expected_operator_class": "intersect_plane_curved",
        "expected_result_type": "circle3",
        # Thiết diện ⊥ trục của hình TRỤ có bán kính không đổi — vị trí H không
        # ảnh hưởng. Ca này đo `RATIO_CONSTRUCTION` mà không để tỉ lệ sai làm
        # hỏng đáp số, nên tách được hai chiều.
        "exact_expected_results": {"radius": "7"},
        "expected_boundary": None,
    },
    {
        "case_id": "d3",
        "family": "cone",
        "feature": "similar_ratio_from_apex_distance",
        "problem_text":
            "Cho hình nón có đỉnh D và tâm đáy T, bán kính đáy bằng 15, chiều "
            "cao DT bằng 20. Điểm U nằm trên đường tròn đáy. Một mặt phẳng "
            "vuông góc với trục DT và cắt trục tại điểm V sao cho DV = 8. Mặt "
            "phẳng đó cắt hình nón theo đường tròn (σ). Tính bán kính của (σ).",
        "expected_obligations": ["radius"],
        "expected_operator_class": "intersect_plane_curved",
        "expected_result_type": "circle3",
        # Đồng dạng: r' = 15·(8/20) = 6. Bộ ba Pythagoras 15–20–25.
        "exact_expected_results": {"radius": "6"},
        "expected_boundary": None,
    },
    {
        "case_id": "d4",
        "family": "cone",
        "feature": "similar_ratio_from_fraction_of_axis",
        "problem_text":
            "Hình nón có đỉnh A và tâm đáy B, bán kính đáy bằng 9, chiều cao "
            "AB bằng 12. Gọi C là một điểm trên đường tròn đáy. Gọi K là điểm "
            "thuộc đoạn AB sao cho AK bằng hai phần ba AB. Mặt phẳng đi qua K "
            "và vuông góc với AB cắt hình nón theo đường tròn (δ). Tính bán "
            "kính của đường tròn (δ).",
        "expected_obligations": ["radius"],
        "expected_operator_class": "intersect_plane_curved",
        "expected_result_type": "circle3",
        # r' = 9·(2/3) = 6. Bộ ba Pythagoras 9–12–15.
        "exact_expected_results": {"radius": "6"},
        "expected_boundary": None,
    },
    {
        "case_id": "d5",
        "family": "ball",
        "feature": "plane_at_rational_distance_from_centre",
        "problem_text":
            "Cho mặt cầu tâm N có bán kính bằng 25. Gọi Q là một điểm sao cho "
            "NQ bằng 7. Mặt phẳng đi qua Q và vuông góc với NQ cắt mặt cầu "
            "theo một đường tròn (κ). Tính bán kính của đường tròn (κ).",
        "expected_obligations": ["radius"],
        "expected_operator_class": "intersect_plane_curved",
        "expected_result_type": "circle3",
        # 7–24–25: r'² = 625 − 49 = 576.
        "exact_expected_results": {"radius": "24"},
        "expected_boundary": None,
    },
    {
        "case_id": "d6",
        "family": "ball",
        "feature": "plane_section_radius_and_area",
        "problem_text":
            "Cho mặt cầu tâm W có bán kính bằng 17. Điểm Z nằm sao cho WZ "
            "bằng 8. Mặt phẳng đi qua Z và vuông góc với WZ cắt mặt cầu theo "
            "đường tròn (λ). Tính bán kính và diện tích của đường tròn (λ).",
        "expected_obligations": ["radius", "area"],
        "expected_operator_class": "intersect_plane_curved",
        "expected_result_type": "circle3",
        # 8–15–17: r'² = 289 − 64 = 225.
        "exact_expected_results": {"radius": "15", "area": "225π"},
        "expected_boundary": None,
    },
    {
        "case_id": "d7",
        "family": "polyhedron",
        "feature": "control__construct_section_is_the_correct_choice",
        "problem_text":
            "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 4. Mặt phẳng đi "
            "qua ba điểm A, C và B' cắt hình lập phương theo một thiết diện. "
            "Tính diện tích của thiết diện đó.",
        "expected_obligations": ["area"],
        # ĐỐI CHỨNG. Ở đây `construct_section` là lựa chọn ĐÚNG — nếu mô hình
        # chọn `intersect_plane_curved` thì nó đang khái quát hoá quá tay.
        "expected_operator_class": "construct_section",
        "expected_result_type": "section",
        # Tam giác đều cạnh 4√2 ⇒ S = (√3/4)·32 = 8√3. Ca trả RADICAL.
        "exact_expected_results": {"area": "8√3"},
        "expected_boundary": None,
    },
    {
        "case_id": "d8",
        "family": "cylinder",
        "feature": "negative__oblique_section_outside_v1_closure",
        "problem_text":
            "Cho hình trụ có hai đáy là hai đường tròn tâm O₁ và tâm O₂, bán "
            "kính đáy bằng 5 và O₁O₂ bằng 12. Gọi R là một điểm trên đường "
            "tròn đáy tâm O₁ và gọi T là một điểm trên đường tròn đáy tâm O₂ "
            "sao cho T không nằm trên đường thẳng đi qua R và song song với "
            "O₁O₂. Mặt phẳng đi qua ba điểm O₁, R, T cắt mặt xung quanh của "
            "hình trụ theo một đường cong. Tính bán kính của đường cong đó.",
        "expected_obligations": ["radius"],
        # Kết quả ĐÚNG là một lời TỪ CHỐI CÓ CẤU TRÚC, không phải một con số.
        "expected_operator_class": "refusal",
        "expected_result_type": None,
        "exact_expected_results": {},
        "expected_boundary": "CURVED_SECTION_OUTSIDE_V1_CLOSURE",
    },
]


# ══ GOLD — chương trình do NGƯỜI viết, đi primitive TỔNG QUÁT ════════════
def _d(name, kind, **kw):
    return {"name": name, "type": kind, **kw}


def _diem(name, xyz, fid):
    return _d(name, "point3", initial_value=list(xyz), source_fact_id=fid)


def _do(bien, luong, of):
    return {"kind": "assign", "target_var": bien,
            "expr": {"kind": "measure", "quantity": luong, "of": of}}


def _tron_xoay(*, ho, tam, dinh, vanh, ten_khoi, ten_tron, cat_bien, cat_expr,
               fid_diem, do, toa_do):
    """Trụ/nón: dựng bằng BA ĐIỂM (đường được ưu tiên), cắt ⊥ trục."""
    decls = [_diem(n, toa_do[n], fid_diem) for n in (tam, dinh, vanh)]
    decls += [_d(ten_khoi, "curved_solid"), _d("truc_", "line3"),
              _d(cat_bien, "point3"), _d("mp_", "plane3"),
              _d(ten_tron, "circle3")]
    stmts = [
        {"kind": "construct_curved_solid", "target_var": ten_khoi,
         "curved_kind": ho, "anchor": tam, "apex_or_top": dinh,
         "rim_point": vanh},
        {"kind": "construct_line", "target_var": "truc_",
         "through_a": dinh, "through_b": tam},
        {"kind": "construct_point", "target_var": cat_bien, "expr": cat_expr},
        {"kind": "assign", "target_var": "mp_",
         "expr": {"kind": "plane_perpendicular_to_line", "point": cat_bien,
                  "line": "truc_"}},
        {"kind": "assign", "target_var": ten_tron,
         "expr": {"kind": "intersect_plane_curved", "solid": ten_khoi,
                  "plane": "mp_"}}]
    for bien, luong in do:
        decls.append(_d(bien, "float"))
        stmts.append(_do(bien, luong, ten_tron))
    return decls, stmts


def _cau(*, tam, ngoai, ten_khoi, ten_tron, fid_diem, do, toa_do):
    """Cầu: tâm có tên + một điểm ngoài xác định phương và khoảng cách."""
    decls = [_diem(tam, toa_do[tam], fid_diem), _diem(ngoai, toa_do[ngoai],
                                                      fid_diem),
             _d("bk_", "float"), _d(ten_khoi, "curved_solid"),
             _d("truc_", "line3"), _d("mp_", "plane3"),
             _d(ten_tron, "circle3")]
    stmts = [
        {"kind": "construct_curved_solid", "target_var": ten_khoi,
         "curved_kind": "ball", "anchor": tam, "radius": "bk_"},
        {"kind": "construct_line", "target_var": "truc_",
         "through_a": tam, "through_b": ngoai},
        {"kind": "assign", "target_var": "mp_",
         "expr": {"kind": "plane_perpendicular_to_line", "point": ngoai,
                  "line": "truc_"}},
        {"kind": "assign", "target_var": ten_tron,
         "expr": {"kind": "intersect_plane_curved", "solid": ten_khoi,
                  "plane": "mp_"}}]
    for bien, luong in do:
        decls.append(_d(bien, "float"))
        stmts.append(_do(bien, luong, ten_tron))
    return decls, stmts


def _chia(a, b, ratio):
    return {"kind": "divide_segment", "a": a, "b": b, "ratio": ratio}


#: `case_id → (facts, decls, stmts, obligations)`.
#:
#: Toạ độ đặt trong ℚ³ và **grounded qua dữ kiện QUAN HỆ** — dữ kiện nêu vai trò
#: của từng điểm, đúng cách `grounding_gate` đòi cho toạ độ suy từ ràng buộc.
def gold(case_id: str):
    FK, FD = "f_kichthuoc", "f_diem"

    if case_id == "d1":
        td = {"I": (0, 0, 0), "J": (0, 0, 20), "P": (12, 0, 0)}
        d, s = _tron_xoay(
            ho="cylinder", tam="I", dinh="J", vanh="P", ten_khoi="Tru",
            ten_tron="w", cat_bien="M", cat_expr={"kind": "midpoint",
                                                  "a": "I", "b": "J"},
            fid_diem=FD, do=[("bk_w", "radius"), ("dt_w", "area")], toa_do=td)
        f = [{"fact_id": FK, "label": "bán kính đáy 12, đường cao IJ 20",
              "values": [12, 20], "provenance": "confirmed"},
             {"fact_id": FD, "label": "I và J là tâm hai đáy, P trên đường "
                                     "tròn đáy tâm I",
              "values": ["I", "J", "P"], "provenance": "confirmed"}]
        ob = [("radius", "w", "bk_w"), ("area", "w", "dt_w")]

    elif case_id == "d2":
        td = {"E": (0, 0, 0), "F": (0, 0, 24), "G": (7, 0, 0)}
        d, s = _tron_xoay(
            ho="cylinder", tam="E", dinh="F", vanh="G", ten_khoi="Tru",
            ten_tron="gam", cat_bien="H", cat_expr=_chia("E", "F", "1/4"),
            fid_diem=FD, do=[("bk_gam", "radius")], toa_do=td)
        f = [{"fact_id": FK, "label": "bán kính đáy 7, EF 24, EH 6",
              "values": [7, 24, 6], "provenance": "confirmed"},
             {"fact_id": FD, "label": "E và F là tâm hai đáy, G trên đường "
                                     "tròn đáy tâm E, H thuộc đoạn EF",
              "values": ["E", "F", "G", "H"], "provenance": "confirmed"}]
        ob = [("radius", "gam", "bk_gam")]

    elif case_id == "d3":
        td = {"T": (0, 0, 0), "D": (0, 0, 20), "U": (15, 0, 0)}
        d, s = _tron_xoay(
            ho="cone", tam="T", dinh="D", vanh="U", ten_khoi="Non",
            ten_tron="sigma", cat_bien="V", cat_expr=_chia("D", "T", "2/5"),
            fid_diem=FD, do=[("bk_sigma", "radius")], toa_do=td)
        f = [{"fact_id": FK, "label": "bán kính đáy 15, chiều cao DT 20, DV 8",
              "values": [15, 20, 8], "provenance": "confirmed"},
             {"fact_id": FD, "label": "D là đỉnh, T là tâm đáy, U trên đường "
                                     "tròn đáy, V thuộc trục DT",
              "values": ["D", "T", "U", "V"], "provenance": "confirmed"}]
        ob = [("radius", "sigma", "bk_sigma")]

    elif case_id == "d4":
        td = {"B": (0, 0, 0), "A": (0, 0, 12), "C": (9, 0, 0)}
        d, s = _tron_xoay(
            ho="cone", tam="B", dinh="A", vanh="C", ten_khoi="Non",
            ten_tron="delta", cat_bien="K", cat_expr=_chia("A", "B", "2/3"),
            fid_diem=FD, do=[("bk_delta", "radius")], toa_do=td)
        f = [{"fact_id": FK, "label": "bán kính đáy 9, chiều cao AB 12, "
                                     "AK bằng hai phần ba AB",
              "values": [9, 12], "provenance": "confirmed"},
             {"fact_id": FD, "label": "A là đỉnh, B là tâm đáy, C trên đường "
                                     "tròn đáy, K thuộc đoạn AB",
              "values": ["A", "B", "C", "K"], "provenance": "confirmed"}]
        ob = [("radius", "delta", "bk_delta")]

    elif case_id == "d5":
        td = {"N": (0, 0, 0), "Q": (0, 0, 7)}
        d, s = _cau(tam="N", ngoai="Q", ten_khoi="Cau", ten_tron="kappa",
                    fid_diem=FD, do=[("bk_kappa", "radius")], toa_do=td)
        d = [x if x["name"] != "bk_" else
             _d("bk_", "float", initial_value=25, source_fact_id=FK) for x in d]
        f = [{"fact_id": FK, "label": "bán kính mặt cầu 25, NQ 7",
              "values": [25, 7], "provenance": "confirmed"},
             {"fact_id": FD, "label": "N là tâm mặt cầu, Q là điểm cách N "
                                     "một khoảng 7",
              "values": ["N", "Q"], "provenance": "confirmed"}]
        ob = [("radius", "kappa", "bk_kappa")]

    elif case_id == "d6":
        td = {"W": (0, 0, 0), "Z": (0, 0, 8)}
        d, s = _cau(tam="W", ngoai="Z", ten_khoi="Cau", ten_tron="lam",
                    fid_diem=FD,
                    do=[("bk_lam", "radius"), ("dt_lam", "area")], toa_do=td)
        d = [x if x["name"] != "bk_" else
             _d("bk_", "float", initial_value=17, source_fact_id=FK) for x in d]
        f = [{"fact_id": FK, "label": "bán kính mặt cầu 17, WZ 8",
              "values": [17, 8], "provenance": "confirmed"},
             {"fact_id": FD, "label": "W là tâm mặt cầu, Z là điểm cách W "
                                     "một khoảng 8",
              "values": ["W", "Z"], "provenance": "confirmed"}]
        ob = [("radius", "lam", "bk_lam"), ("area", "lam", "dt_lam")]

    elif case_id == "d7":
        ten = ["A", "B", "C", "D", "A_", "B_", "C_", "D_"]
        xyz = [(0, 0, 0), (4, 0, 0), (4, 4, 0), (0, 4, 0),
               (0, 0, 4), (4, 0, 4), (4, 4, 4), (0, 4, 4)]
        d = [_diem(n, p, FD) for n, p in zip(ten, xyz)]
        d += [_d("LP", "solid"), _d("mp_", "plane3"), _d("td", "section"),
              _d("dt_td", "float")]
        s = [{"kind": "construct_solid", "target_var": "LP",
              "vertices": ten,
              "faces": [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
                        [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]},
             {"kind": "construct_plane", "target_var": "mp_",
              "through": ["A", "C", "B_"]},
             {"kind": "construct_section", "target_var": "td",
              "solid": "LP", "plane": "mp_"},
             _do("dt_td", "area", "td")]
        f = [{"fact_id": FK, "label": "cạnh hình lập phương bằng 4",
              "values": [4], "provenance": "confirmed"},
             {"fact_id": FD, "label": "ABCD.A'B'C'D' là hình lập phương",
              "values": ten, "provenance": "confirmed"}]
        ob = [("area", "td", "dt_td")]

    elif case_id == "d8":
        td = {"O1": (0, 0, 0), "O2": (0, 0, 12), "R": (5, 0, 0),
              "T": (0, 5, 12)}
        d = [_diem(n, td[n], FD) for n in td]
        d += [_d("Tru", "curved_solid"), _d("mp_", "plane3"),
              _d("cong", "circle3"), _d("bk_cong", "float")]
        s = [{"kind": "construct_curved_solid", "target_var": "Tru",
              "curved_kind": "cylinder", "anchor": "O1", "apex_or_top": "O2",
              "rim_point": "R"},
             {"kind": "construct_plane", "target_var": "mp_",
              "through": ["O1", "R", "T"]},
             {"kind": "assign", "target_var": "cong",
              "expr": {"kind": "intersect_plane_curved", "solid": "Tru",
                       "plane": "mp_"}},
             _do("bk_cong", "radius", "cong")]
        f = [{"fact_id": FK, "label": "bán kính đáy 5, O₁O₂ bằng 12",
              "values": [5, 12], "provenance": "confirmed"},
             {"fact_id": FD, "label": "O₁ và O₂ là tâm hai đáy, R trên đáy "
                                     "tâm O₁, T trên đáy tâm O₂",
              "values": ["O1", "O2", "R", "T"], "provenance": "confirmed"}]
        ob = [("radius", "cong", "bk_cong")]

    else:
        raise KeyError(case_id)

    spec = {"spec_version": "1.0", "title": f"Gold {case_id}",
            "description": "Chương trình gold do người viết cho preflight.",
            "pedagogical_intent": "Kiểm rằng đường đúng đi được trước khi đo.",
            "memory_declarations": d, "statements": s, "visual_bindings": VB}
    return f, spec, ob


# ══ PREFLIGHT ════════════════════════════════════════════════════════════
def _bam(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def chay_gold(ca: dict) -> dict[str, Any]:
    cid = ca["case_id"]
    f, spec_json, ob = gold(cid)
    hd = RequestContract(
        problem_text=ca["problem_text"], input_facts=f,
        obligations=tuple(Obligation(kind=k, container=c,
                                     params={"witness": w})
                          for k, c, w in ob))
    kq: dict[str, Any] = {"case_id": cid,
                          "expected_operator_class":
                              ca["expected_operator_class"]}
    try:
        spec = SemanticProgramSpec.model_validate(spec_json)
    except Exception as e:                                        # noqa: BLE001
        return {**kq, "stage": "schema", "servable": False,
                "loi": f"SCHEMA: {str(e)[:200]}"}
    try:
        out = verify_and_compile(hd, spec)
    except Exception as e:                                        # noqa: BLE001
        return {**kq, "stage": "NGOAI_LE_THOAT", "servable": False,
                "loi": f"{type(e).__name__}: {str(e)[:160]}"}

    mem = {k: str(v) for k, v in (out.final_memory or {}).items()}
    kq.update({
        "stage": out.stage_reached, "executable": out.executable,
        "servable": out.servable, "error_code": out.error_code,
        "failure_category": getattr(out, "failure_category", None),
        "details": [str(x)[:200] for x in (out.details or [])],
        "witness": {w: mem.get(w) for _, _, w in ob},
    })
    # Ca âm: kết quả ĐÚNG là từ chối mang đúng mã đã công bố.
    if ca["expected_operator_class"] == "refusal":
        ma = ca["expected_boundary"]
        kq["gold_ok"] = (not out.servable
                         and any(ma in x for x in (out.details or [])))
        return kq
    mong = ca["exact_expected_results"]
    thuc = {k: mem.get(w) for (k, _, w) in ob}
    kq["exact_match"] = thuc == mong
    kq["thuc_te"] = thuc

    # ── SCENE3D — đáp số phải TỚI ĐƯỢC học sinh, không chỉ tồn tại trong bộ nhớ
    #
    # `route` cố ý không dựng cảnh (phụ thuộc một chiều), nên phải gọi đúng hàm
    # mà sản phẩm gọi. Đây chính là chỗ `V3_PRODUCT_PATH_PARITY_CORRECTION` đã
    # phải đính chính một lần: đọc cảnh từ một phép chiếu luôn rỗng.
    from app.ai import pipeline

    try:
        canh = pipeline._dung_scene3d(spec, hd) or {}
        ten = {o.get("name") or o.get("id") for o in canh.get("objects", [])}
        thieu = [w for _, _, w in ob if w not in ten]
        kq["scene3d_objects"] = len(canh.get("objects", []))
        kq["scene3d_ok"] = not thieu
        if thieu:
            kq["scene3d_thieu"] = thieu
    except Exception as e:                                        # noqa: BLE001
        kq["scene3d_ok"] = False
        kq["scene3d_loi"] = f"{type(e).__name__}: {str(e)[:160]}"

    kq["gold_ok"] = bool(out.servable and kq["exact_match"]
                         and kq.get("scene3d_ok"))
    return kq


def main() -> int:
    RA.mkdir(parents=True, exist_ok=True)
    corpus_public = [{k: v for k, v in c.items()
                      if k in ("case_id", "family", "feature", "problem_text")}
                     for c in CORPUS]
    expected = [{k: v for k, v in c.items()
                 if k in ("case_id", "expected_obligations",
                          "expected_operator_class", "expected_result_type",
                          "exact_expected_results", "expected_boundary")}
                for c in CORPUS]
    corpus_hash, expected_hash = _bam(corpus_public), _bam(expected)

    kq = [chay_gold(c) for c in CORPUS]
    duong = [r for r, c in zip(kq, CORPUS)
             if c["expected_operator_class"] != "refusal"]
    am = [r for r, c in zip(kq, CORPUS)
          if c["expected_operator_class"] == "refusal"]
    dat = sum(1 for r in duong if r.get("gold_ok"))
    dat_am = sum(1 for r in am if r.get("gold_ok"))

    print(f"CORPUS_HASH           = {corpus_hash}")
    print(f"EXPECTED_RESULTS_HASH = {expected_hash}\n")
    print(f"{'ca':5} {'họ':11} {'stage':22} {'srv':5} {'gold':5} {'đáp số'}")
    for r, c in zip(kq, CORPUS):
        print(f"{r['case_id']:5} {c['family']:11} {str(r['stage']):22} "
              f"{str(r.get('servable')):5} "
              f"{'OK' if r.get('gold_ok') else 'HỎNG':5} "
              f"{r.get('thuc_te') or r.get('error_code') or ''}")
        if not r.get("gold_ok") and r.get("details"):
            print(f"      └ {r['details'][:2]}")
        if r.get("loi"):
            print(f"      └ {r['loi']}")

    canh = sum(1 for r in duong if r.get("scene3d_ok"))
    khop = sum(1 for r in duong if r.get("exact_match"))
    print(f"\nGOLD_POSITIVE_CASES_SERVABLE = {dat}/{len(duong)}")
    print(f"GOLD_EXACT_RESULTS           = {khop}/{len(duong)}")
    print(f"GOLD_SCENE3D                 = {canh}/{len(duong)}")
    print(f"GOLD_NEGATIVE_BOUNDARY       = {'PASS' if dat_am == len(am) else 'FAIL'}")
    mo = dat == len(duong) and dat_am == len(am)
    print(f"PRE_LIVE_GUARD               = {'OPEN' if mo else 'BLOCKED'}")

    (RA / "corpus.json").write_text(json.dumps(
        {"version": "dev-v1", "corpus_hash": corpus_hash,
         "cases": corpus_public}, ensure_ascii=False, indent=2), encoding="utf-8")
    (RA / "expected_results.json").write_text(json.dumps(
        {"version": "dev-v1", "expected_results_hash": expected_hash,
         "expected": expected}, ensure_ascii=False, indent=2), encoding="utf-8")
    (RA / "gold_preflight.json").write_text(json.dumps(
        {"corpus_hash": corpus_hash, "expected_results_hash": expected_hash,
         "gold_positive_servable": f"{dat}/{len(duong)}",
         "gold_negative_boundary": "PASS" if dat_am == len(am) else "FAIL",
         "pre_live_guard": "OPEN" if mo else "BLOCKED",
         "ket_qua": kq}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if mo else 1


if __name__ == "__main__":
    raise SystemExit(main())
