# -*- coding: utf-8 -*-
"""BỘ CA ĐÁNH GIÁ CUỐI của khoá luận — cố định, băm được. **0 lượt gọi model.**

    `THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION`, 2026-09-08.

Bộ đo, ở `scripts/` — ngoài `MEASURED_SYSTEM_PATHS`, nên nó cứng cáp thêm được
mà không phá đóng băng candidate.

─── VÌ SAO 7 CA DƯƠNG, KHÔNG PHẢI 12 ──────────────────────────────────────

Phạm vi có **mười hai họ hình** (`CAPABILITY_MATRIX.json`), trong đó mười họ
trong phạm vi và hai họ `OUT_OF_SCOPE`. Một ca một họ sẽ tốn mười lượt đo cho
một thứ mà bảy lượt đã nói hết — vì một đề tự nhiên thường CHẠM NHIỀU HỌ cùng
lúc, và chỉ chạm thật khi các stage của họ ấy **thực sự chạy**.

Bảy ca dưới đây là một lời giải **set-cover**: mỗi họ trong phạm vi được ít
nhất một ca phủ, và mỗi ca phủ ít nhất một họ mà không ca nào khác phủ nổi.
`test_thesis_acceptance_matrix.py` kiểm lại phép phủ ấy bằng máy, cả hai chiều
— thiếu một họ là ĐỎ, mà thừa một ca không phủ thêm gì cũng ĐỎ.

    p1  point_line_vector_plane · polygon_and_planar_section · convex_polyhedron
    p2  nonconvex_polyhedron
    p3  ball · curved_circular_section
    p4  cylinder
    p5  cone
    p6  oblique_cylinder_ellipse
    p7  oblique_cone_section

─── VÌ SAO KÝ HIỆU VÀ SỐ ĐỀU MỚI ─────────────────────────────────────────

Không ca nào trùng đề, trùng ký hiệu hay trùng con số với corpus phát triển
(`run_curved_acceptance.CA`, pool V3, `gold_*`, tập demo). Chấm một mô hình
trên bài nó đã có thể gặp trong quá trình phát triển hệ là chấm sai theo chiều
**luôn đẹp lên** — và đó là hỏng im lặng, vì con số vẫn ra.
`test_thesis_acceptance_matrix.py` đối chiếu băm đề với mọi corpus đang có.

⚠️ Nhưng bộ này **KHÔNG mang nhãn held-out** — xem `EVALUATION_CLASS` trong
`policies/thesis_final_acceptance_policy.json`. Đề do chính người triển khai
viết và nằm trong kho; điều đó khác *"mô hình chưa thấy"* nhưng không phải
*"người viết bộ đo chưa thấy"*.

─── ĐIỀU BỘ CA NÀY TỰ CẤM ────────────────────────────────────────────────

`payload_gui_model()` là đường DUY NHẤT được gửi cho mô hình, và nó trả về
**đúng một trường**: đề bài. Gold program, oracle, đáp số mong đợi và mọi siêu
dữ liệu chấm điểm đều ở lại phía bộ đo. Guard: `test_..._payload_chi_co_de`.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

__all__ = [
    "CA_AM",
    "CA_DUONG",
    "CORPUS_HASH",
    "EXPECTED_RESULTS_HASH",
    "HO_TRONG_PHAM_VI",
    "PHU_THEO_HO",
    "bam_chinh_tac",
    "corpus_json",
    "expected_results_json",
    "payload_gui_model",
    "theo_id",
]


def bam_chinh_tac(obj: Any) -> str:
    """Cùng phép băm `measurement_policy.bam_chinh_tac` dùng — một quy ước."""
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode("utf-8")).hexdigest()


#: Mười họ TRONG phạm vi. Hai họ `OUT_OF_SCOPE` không có mặt ở đây — chúng là
#: chủ đề của ca ÂM, và trộn chúng vào phép phủ dương sẽ đòi một ca không tồn
#: tại được.
HO_TRONG_PHAM_VI = (
    "point_line_vector_plane",
    "polygon_and_planar_section",
    "convex_polyhedron",
    "nonconvex_polyhedron",
    "ball",
    "cylinder",
    "cone",
    "curved_circular_section",
    "oblique_cylinder_ellipse",
    "oblique_cone_section",
)

_VB: dict[str, list] = {"containers": [], "pointers": [], "value_boxes": []}


def _md(ten: str, kieu: str, gt: Any = None, fact: str | None = None) -> dict:
    d: dict[str, Any] = {"name": ten, "type": kieu}
    if gt is not None:
        d["initial_value"] = gt
    if fact:
        d["source_fact_id"] = fact
    return d


def _f(fid: str, nhan: str, *gt: str) -> dict:
    return {"fact_id": fid, "label": nhan, "values": list(gt),
            "provenance": "confirmed"}


def _diem(toa_do: dict[str, list[int]]) -> list[dict]:
    return [_f(f"dinh_{t}", f"Điểm {t}", t, f"({v[0]};{v[1]};{v[2]})")
            for t, v in toa_do.items()]


def _do(ten: str, luong: str, of: str, wrt: str | None = None) -> dict:
    e: dict[str, Any] = {"kind": "measure", "quantity": luong, "of": of}
    if wrt:
        e["wrt"] = wrt
    return {"kind": "assign", "target_var": ten, "expr": e}


# ══════════════════════════════════════════════════════════════════════════
# CA DƯƠNG
# ══════════════════════════════════════════════════════════════════════════
#
# ⚠️ `expected[*].display` là chuỗi ĐÚNG QUY ƯỚC HIỂN THỊ của sản phẩm
# (`radical.display()`): hữu tỉ, rồi `π`, rồi `√`. Bản nháp đầu tiên của bộ ca
# này viết `25√5π` và bảy ca dương "sai" trong khi không con số nào lệch một
# li — nên quy ước ấy được ghi ra đây thành chữ, và `oracle_value` đứng cạnh
# để một lần đổi quy ước hiển thị không phá được phép kiểm SỐ.

_P1_TD = {"A": [0, 0, 0], "B": [6, 0, 0], "C": [6, 6, 0], "D": [0, 6, 0],
          "S": [0, 0, 6]}
_P2_TD = {"M": [0, 0, 0], "N": [8, 0, 0], "P": [8, 6, 0], "Q": [4, 2, 0],
          "R": [0, 6, 0], "S": [3, 3, 9]}
_P2_DAY = ["M", "N", "P", "Q", "R"]
_P3_TD = {"I": [0, 0, 0], "A": [15, 0, 0]}
_P4_TD = {"O": [0, 0, 0], "K": [0, 0, 10], "A": [6, 0, 0]}
_P5_TD = {"O": [0, 0, 0], "S": [0, 0, 12], "A": [5, 0, 0]}
_P6_TD = {"O": [0, 0, 0], "K": [0, 0, 24], "A": [5, 0, 0]}
_P7_TD = {"O": [0, 0, 0], "S": [0, 0, 12], "A": [6, 0, 0]}

CA_DUONG: list[dict[str, Any]] = [
    # ── p1 ───────────────────────────────────────────────────────────────
    {
        "id": "p1_chop_thiet_dien_khoang_cach",
        "families": ["point_line_vector_plane", "polygon_and_planar_section",
                     "convex_polyhedron"],
        "problem_text": (
            "Trong không gian Oxyz, cho khối chóp S.ABCD có đáy ABCD là hình "
            "vuông với A(0;0;0), B(6;0;0), C(6;6;0), D(0;6;0) và đỉnh "
            "S(0;0;6). Mặt phẳng (α): z = 3 cắt khối chóp theo thiết diện "
            "(T). Tính thể tích khối chóp S.ABCD, diện tích thiết diện (T) và "
            "khoảng cách từ điểm S đến đường thẳng BD."),
        "request_contract_gold": {
            "input_facts": _diem(_P1_TD) + [
                _f("day_vuong", "Đáy ABCD là hình vuông", "ABCD"),
                _f("mp_alpha", "Mặt phẳng (α): z = 3", "(α)", "z = 3"),
                _f("duong_BD", "Đường thẳng BD", "BD")],
            "obligations": [
                {"kind": "volume", "container": "S.ABCD",
                 "params": {"witness": "V"}},
                {"kind": "area", "container": "(T)",
                 "params": {"witness": "S_T"}},
                {"kind": "distance", "container": "S",
                 "params": {"witness": "d", "wrt": "BD"}}],
        },
        "gold_program": {
            "spec_version": "1.0",
            "title": "Khối chóp, thiết diện và khoảng cách",
            "description": "Dựng khối chóp từ năm đỉnh, cắt bởi (α), rồi đo.",
            "pedagogical_intent": "Thấy thiết diện là giao của mặt phẳng với khối.",
            "memory_declarations": [
                _md(t, "point3", _P1_TD[t], f"dinh_{t}") for t in _P1_TD
            ] + [_md("alpha", "plane3", fact="mp_alpha"),
                 _md("chop", "solid", fact="day_vuong"),
                 _md("T", "section", fact="mp_alpha"),
                 _md("BD", "line3", fact="duong_BD"),
                 _md("V", "float"), _md("S_T", "float"), _md("d", "float")],
            "statements": [
                {"kind": "construct_solid", "target_var": "chop",
                 "vertices": ["A", "B", "C", "D", "S"],
                 "faces": [["A", "B", "C", "D"], ["S", "B", "A"],
                           ["S", "C", "B"], ["S", "D", "C"], ["S", "A", "D"]],
                 "label": "S.ABCD"},
                {"kind": "construct_plane_from_equation", "target_var": "alpha",
                 "a": 0, "b": 0, "c": 1, "d": -3, "label": "(α)"},
                {"kind": "construct_section", "target_var": "T",
                 "solid": "chop", "plane": "alpha", "label": "(T)"},
                {"kind": "construct_line", "target_var": "BD",
                 "through_a": "B", "through_b": "D", "label": "BD"},
                _do("V", "volume", "chop"),
                _do("S_T", "area", "T"),
                _do("d", "distance", "S", "BD")],
            "visual_bindings": _VB,
        },
        "expected": {
            "V": {"display": "72", "oracle_value": 72.0,
                  "oracle_method": "CLOSED_FORM",
                  "oracle_derivation": "S_đáy = 6·6 = 36 · h = 6 ⇒ V = 36·6/3",
                  "oracle_call": ["the_tich_chop",
                                  [[0, 0], [6, 0], [6, 6], [0, 6]], 6]},
            "S_T": {"display": "9", "oracle_value": 9.0,
                    "oracle_method": "CLOSED_FORM",
                    "oracle_derivation": (
                        "(α) cắt mọi cạnh bên tại TRUNG ĐIỂM (z = 3 = 6/2) ⇒ "
                        "thiết diện là hình vuông cạnh 3"),
                    "oracle_call": ["dien_tich_da_giac_3d",
                                    [[0, 0, 3], [3, 0, 3], [3, 3, 3],
                                     [0, 3, 3]]]},
            "d": {"display": "3√6", "oracle_value": 7.348469228349535,
                  "oracle_method": "CLOSED_FORM",
                  "oracle_derivation": "|(S−B)×(D−B)|/|D−B| = 36√3/(6√2) = 3√6",
                  "oracle_call": ["khoang_cach_diem_duong",
                                  [0, 0, 6], [6, 0, 0], [0, 6, 0]]},
        },
        "expected_scene3d_kinds": ["solid", "section", "plane3", "line3",
                                   "point3", "quantity"],
    },
    # ── p2 ───────────────────────────────────────────────────────────────
    {
        "id": "p2_chop_day_ngu_giac_lom",
        "families": ["nonconvex_polyhedron"],
        "problem_text": (
            "Trong không gian Oxyz, cho khối chóp S.MNPQR có đáy MNPQR là một "
            "ngũ giác LÕM nằm trong mặt phẳng Oxy. Các đỉnh của đáy theo thứ "
            "tự quanh biên là M(0;0;0), N(8;0;0), P(8;6;0), Q(4;2;0), "
            "R(0;6;0); đỉnh của khối chóp là S(3;3;9). Tính thể tích khối "
            "chóp S.MNPQR."),
        "request_contract_gold": {
            "input_facts": _diem(_P2_TD) + [
                _f("day_lom", "Đáy MNPQR là ngũ giác LÕM, các đỉnh theo thứ "
                              "tự quanh biên", "MNPQR")],
            "obligations": [{"kind": "volume", "container": "S.MNPQR",
                             "params": {"witness": "V"}}],
        },
        "gold_program": {
            "spec_version": "1.0",
            "title": "Thể tích khối chóp đáy ngũ giác lõm",
            "description": "Dựng khối chóp từ sáu đỉnh và bảng mặt, rồi đo.",
            "pedagogical_intent": "Thấy chỗ lõm vẫn được tính đúng.",
            "memory_declarations": [
                _md(t, "point3", _P2_TD[t], f"dinh_{t}") for t in _P2_TD
            ] + [_md("chop", "solid", fact="day_lom"), _md("V", "float")],
            "statements": [
                {"kind": "construct_solid", "target_var": "chop",
                 "vertices": list(_P2_TD),
                 "faces": [list(reversed(_P2_DAY))] + [
                     [_P2_DAY[i], _P2_DAY[(i + 1) % 5], "S"] for i in range(5)],
                 "label": "S.MNPQR"},
                _do("V", "volume", "chop")],
            "visual_bindings": _VB,
        },
        "expected": {
            "V": {"display": "96", "oracle_value": 96.0,
                  "oracle_method": "CLOSED_FORM",
                  "oracle_derivation": (
                      "shoelace CÓ DẤU của MNPQR = 32 (đỉnh lõm Q) · h = 9 ⇒ "
                      "V = 32·9/3 = 96"),
                  "oracle_call": ["the_tich_chop",
                                  [[0, 0], [8, 0], [8, 6], [4, 2], [0, 6]], 9]},
        },
        # ⚠️ HAI CÁCH LÀM MẤT CHỖ LÕM cho hai con số KHÁC NHAU, và cả hai
        # khác `96` đủ xa để không nhầm được. Nhờ vậy bộ chấm nói được mô hình
        # hỏng KIỂU NÀO, không chỉ "sai".
        "bay_da_do": {
            "abs_tung_tu_dien": {"shoelace": 40, "volume": 120,
                                 "khai": "lấy `abs` từng tam giác quạt ⇒ lấp "
                                         "chỗ lõm"},
            "bao_loi": {"shoelace": 48, "volume": 144,
                        "khai": "bỏ hẳn đỉnh lõm Q ⇒ hình chữ nhật 8×6"},
        },
        "expected_scene3d_kinds": ["solid", "point3", "quantity"],
    },
    # ── p3 ───────────────────────────────────────────────────────────────
    {
        "id": "p3_mat_cau_va_thiet_dien_tron",
        "families": ["ball", "curved_circular_section"],
        "problem_text": (
            "Trong không gian Oxyz, cho mặt cầu (S) có tâm I(0;0;0) và đi qua "
            "điểm A(15;0;0). Mặt phẳng (P): z = 9 cắt mặt cầu (S) theo một "
            "đường tròn (C). Tính thể tích khối cầu (S) và diện tích hình "
            "tròn (C)."),
        "request_contract_gold": {
            "input_facts": _diem(_P3_TD) + [
                _f("mat_cau", "Mặt cầu (S) tâm I, đi qua A", "(S)"),
                _f("mp_P", "Mặt phẳng (P): z = 9", "(P)", "z = 9")],
            "obligations": [
                {"kind": "volume", "container": "(S)",
                 "params": {"witness": "V"}},
                {"kind": "area", "container": "(C)",
                 "params": {"witness": "S_C"}}],
        },
        "gold_program": {
            "spec_version": "1.0", "title": "Khối cầu và thiết diện tròn",
            "description": "Dựng mặt cầu từ tâm và một điểm, cắt bởi (P), rồi đo.",
            "pedagogical_intent": "Thấy mặt phẳng cắt mặt cầu theo đường tròn.",
            "memory_declarations": [
                _md(t, "point3", _P3_TD[t], f"dinh_{t}") for t in _P3_TD
            ] + [_md("cau", "curved_solid", fact="mat_cau"),
                 _md("Pmp", "plane3", fact="mp_P"),
                 _md("C", "circle3", fact="mp_P"),
                 _md("V", "float"), _md("S_C", "float")],
            "statements": [
                {"kind": "construct_curved_solid", "target_var": "cau",
                 "curved_kind": "ball", "anchor": "I", "rim_point": "A",
                 "label": "(S)"},
                {"kind": "construct_plane_from_equation", "target_var": "Pmp",
                 "a": 0, "b": 0, "c": 1, "d": -9, "label": "(P)"},
                {"kind": "assign", "target_var": "C",
                 "expr": {"kind": "intersect_plane_curved", "solid": "cau",
                          "plane": "Pmp"}},
                _do("V", "volume", "cau"),
                _do("S_C", "area", "C")],
            "visual_bindings": _VB,
        },
        "expected": {
            "V": {"display": "4500π", "oracle_value": 14137.166941154069,
                  "oracle_method": "CLOSED_FORM",
                  "oracle_derivation": "R = IA = 15 ⇒ V = 4/3·π·15³ = 4500π",
                  "oracle_call": ["khoi_cau", 15]},
            "S_C": {"display": "144π", "oracle_value": 452.3893421169302,
                    "oracle_method": "CLOSED_FORM",
                    "oracle_derivation": (
                        "d(I,(P)) = 9 ⇒ r² = 15² − 9² = 144 ⇒ S = 144π"),
                    "oracle_call": ["thiet_dien_tron_cau", 15, 9]},
        },
        "expected_scene3d_kinds": ["curved_solid", "circle3", "plane3",
                                   "point3", "quantity"],
    },
    # ── p4 ───────────────────────────────────────────────────────────────
    {
        "id": "p4_hinh_tru_the_tich_va_xung_quanh",
        "families": ["cylinder"],
        "problem_text": (
            "Trong không gian Oxyz, cho hình trụ có hai đáy là hai hình tròn "
            "tâm O(0;0;0) và K(0;0;10); điểm A(6;0;0) nằm trên đường tròn đáy "
            "tâm O. Tính thể tích khối trụ và diện tích xung quanh của hình "
            "trụ đó."),
        "request_contract_gold": {
            "input_facts": _diem(_P4_TD) + [
                _f("hinh_tru", "Hình trụ hai đáy tâm O và K, A nằm trên vành "
                               "đáy", "hình trụ")],
            "obligations": [
                {"kind": "volume", "container": "hình trụ",
                 "params": {"witness": "V"}},
                {"kind": "lateral_area", "container": "hình trụ",
                 "params": {"witness": "Sxq"}}],
        },
        "gold_program": {
            "spec_version": "1.0",
            "title": "Thể tích và diện tích xung quanh hình trụ",
            "description": "Dựng hình trụ từ hai tâm đáy và một điểm trên vành.",
            "pedagogical_intent": "Thấy bán kính và chiều cao quyết định hai đại lượng.",
            "memory_declarations": [
                _md(t, "point3", _P4_TD[t], f"dinh_{t}") for t in _P4_TD
            ] + [_md("tru", "curved_solid", fact="hinh_tru"),
                 _md("V", "float"), _md("Sxq", "float")],
            "statements": [
                {"kind": "construct_curved_solid", "target_var": "tru",
                 "curved_kind": "cylinder", "anchor": "O", "apex_or_top": "K",
                 "rim_point": "A", "label": "hình trụ"},
                _do("V", "volume", "tru"),
                _do("Sxq", "lateral_area", "tru")],
            "visual_bindings": _VB,
        },
        "expected": {
            "V": {"display": "360π", "oracle_value": 1130.9733552923256,
                  "oracle_method": "CLOSED_FORM",
                  "oracle_derivation": "r = 6 · h = 10 ⇒ V = π·36·10 = 360π",
                  "oracle_call": ["khoi_tru", 6, 10]},
            "Sxq": {"display": "120π", "oracle_value": 376.99111843077515,
                    "oracle_method": "CLOSED_FORM",
                    "oracle_derivation": "Sxq = 2π·6·10 = 120π",
                    "oracle_call": ["khoi_tru", 6, 10]},
        },
        "expected_scene3d_kinds": ["curved_solid", "point3", "quantity"],
    },
    # ── p5 ───────────────────────────────────────────────────────────────
    {
        "id": "p5_hinh_non_the_tich_va_xung_quanh",
        "families": ["cone"],
        "problem_text": (
            "Trong không gian Oxyz, cho hình nón có đỉnh S(0;0;12), tâm đáy "
            "O(0;0;0) và điểm A(5;0;0) nằm trên đường tròn đáy. Tính thể tích "
            "khối nón và diện tích xung quanh của hình nón đó."),
        "request_contract_gold": {
            "input_facts": _diem(_P5_TD) + [
                _f("hinh_non", "Hình nón đỉnh S, tâm đáy O, A nằm trên vành "
                               "đáy", "hình nón")],
            "obligations": [
                {"kind": "volume", "container": "hình nón",
                 "params": {"witness": "V"}},
                {"kind": "lateral_area", "container": "hình nón",
                 "params": {"witness": "Sxq"}}],
        },
        "gold_program": {
            "spec_version": "1.0",
            "title": "Thể tích và diện tích xung quanh hình nón",
            "description": "Dựng hình nón từ đỉnh, tâm đáy và một điểm trên vành.",
            "pedagogical_intent": "Thấy đường sinh dẫn ra diện tích xung quanh.",
            "memory_declarations": [
                _md(t, "point3", _P5_TD[t], f"dinh_{t}") for t in _P5_TD
            ] + [_md("non", "curved_solid", fact="hinh_non"),
                 _md("V", "float"), _md("Sxq", "float")],
            "statements": [
                {"kind": "construct_curved_solid", "target_var": "non",
                 "curved_kind": "cone", "anchor": "O", "apex_or_top": "S",
                 "rim_point": "A", "label": "hình nón"},
                _do("V", "volume", "non"),
                _do("Sxq", "lateral_area", "non")],
            "visual_bindings": _VB,
        },
        "expected": {
            "V": {"display": "100π", "oracle_value": 314.1592653589793,
                  "oracle_method": "CLOSED_FORM",
                  "oracle_derivation": "r = 5 · h = 12 ⇒ V = π·25·12/3 = 100π",
                  "oracle_call": ["khoi_non", 5, 12]},
            "Sxq": {"display": "65π", "oracle_value": 204.20352248333654,
                    "oracle_method": "CLOSED_FORM",
                    "oracle_derivation": (
                        "l = √(5²+12²) = 13 ⇒ Sxq = π·5·13 = 65π"),
                    "oracle_call": ["khoi_non", 5, 12]},
        },
        "expected_scene3d_kinds": ["curved_solid", "point3", "quantity"],
    },
    # ── p6 ───────────────────────────────────────────────────────────────
    {
        "id": "p6_thiet_dien_elip_cua_hinh_tru",
        "families": ["oblique_cylinder_ellipse"],
        "problem_text": (
            "Trong không gian Oxyz, cho hình trụ có hai đáy là hai hình tròn "
            "tâm O(0;0;0) và K(0;0;24); điểm A(5;0;0) nằm trên đường tròn đáy "
            "tâm O. Mặt phẳng (α): 2x − z + 12 = 0 cắt hình trụ theo một "
            "đường elip (E). Tính diện tích hình elip (E)."),
        "request_contract_gold": {
            "input_facts": _diem(_P6_TD) + [
                _f("hinh_tru", "Hình trụ hai đáy tâm O và K, A nằm trên vành "
                               "đáy", "hình trụ"),
                # ⚠️ Giá trị phải trùng BYTE với đề. Bản đầu viết dấu trừ
                # ASCII (`-`) trong khi đề dùng U+2212 (`−`), nên extractor
                # không chứng minh được và fact ra `provenance="claimed"` ⇒
                # bất biến nguồn của mặt phẳng ĐỎ. Đo được ở lượt chứng nhận
                # runner, không phải ở gold preflight — gold preflight dùng
                # thẳng hợp đồng này nên nó chưa bao giờ đi qua extractor.
                _f("mp_alpha", "Mặt phẳng (α): 2x − z + 12 = 0", "(α)",
                   "2x − z + 12 = 0")],
            "obligations": [{"kind": "area", "container": "(E)",
                             "params": {"witness": "S_E"}}],
        },
        "gold_program": {
            "spec_version": "1.0",
            "title": "Diện tích thiết diện elip của hình trụ",
            "description": "Cắt hình trụ bằng một mặt phẳng xiên rồi đo diện tích.",
            "pedagogical_intent": "Thấy mặt phẳng xiên cắt hình trụ theo elip.",
            "memory_declarations": [
                _md(t, "point3", _P6_TD[t], f"dinh_{t}") for t in _P6_TD
            ] + [_md("tru", "curved_solid", fact="hinh_tru"),
                 _md("alpha", "plane3", fact="mp_alpha"),
                 _md("E", "ellipse3", fact="mp_alpha"), _md("S_E", "float")],
            "statements": [
                {"kind": "construct_curved_solid", "target_var": "tru",
                 "curved_kind": "cylinder", "anchor": "O", "apex_or_top": "K",
                 "rim_point": "A", "label": "hình trụ"},
                {"kind": "construct_plane_from_equation", "target_var": "alpha",
                 "a": 2, "b": 0, "c": -1, "d": 12, "label": "(α)"},
                {"kind": "assign", "target_var": "E",
                 "expr": {"kind": "intersect_plane_curved_ellipse",
                          "solid": "tru", "plane": "alpha"}},
                _do("S_E", "area", "E")],
            "visual_bindings": _VB,
        },
        "expected": {
            # ⚠️ `oracle_value` là số do phép LẤY MẪU dẫn ra, KHÔNG phải số do
            # công thức bán trục dẫn ra. Bản nháp đầu để giá trị công thức ở
            # đây, và hậu quả đo được: hạ dung sai từ `1e-8` xuống `1e-12` vẫn
            # XANH — tức cột "oracle" đang so đáp số với chính công thức mà
            # kernel dùng, và tính độc lập chỉ có trên nhãn.
            "S_E": {"display": "25π√5", "oracle_value": 175.6203682470269,
                    "oracle_method": "SAMPLED",
                    "oracle_derivation": (
                        "LẤY MẪU 200 000 điểm trên giao tuyến + shoelace 3D. "
                        "Đối chiếu (KHÔNG dùng để chấm): b = r = 5, "
                        "a = r√(1+m²) = 5√5 với m = 2 ⇒ S = 25√5·π"),
                    "oracle_call": ["elip_lay_mau_tru",
                                    {"tam_day": [0, 0, 0],
                                     "tam_day_kia": [0, 0, 24],
                                     "ban_kinh": 5,
                                     "mat_phang": [2, 0, -1, 12]}]},
        },
        "expected_scene3d_kinds": ["curved_solid", "ellipse3", "plane3",
                                   "point3", "quantity"],
    },
    # ── p7 ───────────────────────────────────────────────────────────────
    {
        "id": "p7_thiet_dien_elip_cua_hinh_non",
        "families": ["oblique_cone_section"],
        "problem_text": (
            "Trong không gian Oxyz, cho hình nón có đỉnh S(0;0;12), tâm đáy "
            "O(0;0;0) và điểm A(6;0;0) nằm trên đường tròn đáy. Mặt phẳng "
            "(β): x + z − 9 = 0 cắt hình nón theo một đường elip (E). Tính "
            "diện tích hình elip (E)."),
        "request_contract_gold": {
            "input_facts": _diem(_P7_TD) + [
                _f("hinh_non", "Hình nón đỉnh S, tâm đáy O, A nằm trên vành "
                               "đáy", "hình nón"),
                # Cùng lỗi dấu trừ như `p6`. ⚠️ `p7` VẪN `served` với bản
                # sai — nó thoát nhờ may, và một lỗi chỉ bật ở một trong hai
                # ca cùng hình dạng là lỗi tệ hơn một lỗi bật ở cả hai.
                _f("mp_beta", "Mặt phẳng (β): x + z − 9 = 0", "(β)",
                   "x + z − 9 = 0")],
            "obligations": [{"kind": "area", "container": "(E)",
                             "params": {"witness": "S_E"}}],
        },
        "gold_program": {
            "spec_version": "1.0",
            "title": "Diện tích thiết diện elip của hình nón",
            "description": "Cắt hình nón bằng một mặt phẳng xiên rồi đo diện tích.",
            "pedagogical_intent": "Thấy mặt phẳng xiên cắt hình nón theo elip.",
            "memory_declarations": [
                _md(t, "point3", _P7_TD[t], f"dinh_{t}") for t in _P7_TD
            ] + [_md("non", "curved_solid", fact="hinh_non"),
                 _md("beta", "plane3", fact="mp_beta"),
                 _md("E", "ellipse3", fact="mp_beta"), _md("S_E", "float")],
            "statements": [
                {"kind": "construct_curved_solid", "target_var": "non",
                 "curved_kind": "cone", "anchor": "O", "apex_or_top": "S",
                 "rim_point": "A", "label": "hình nón"},
                {"kind": "construct_plane_from_equation", "target_var": "beta",
                 "a": 1, "b": 0, "c": 1, "d": -9, "label": "(β)"},
                {"kind": "assign", "target_var": "E",
                 "expr": {"kind": "intersect_plane_curved_ellipse",
                          "solid": "non", "plane": "beta"}},
                _do("S_E", "area", "E")],
            "visual_bindings": _VB,
        },
        "expected": {
            # Số LẤY MẪU, cùng lý do như `p6`.
            "S_E": {"display": "2π√6", "oracle_value": 15.390597958144966,
                    "oracle_method": "SAMPLED",
                    "oracle_derivation": (
                        "LẤY MẪU 200 000 điểm trên giao tuyến (đi theo TIA từ "
                        "đỉnh, không theo phương trình mặt nón) + shoelace 3D. "
                        "Đối chiếu (KHÔNG dùng để chấm): t = tan²α = 1/4, "
                        "m = 1, k = 3/4, c = 3 ⇒ a² = 8, b² = 3 ⇒ S = 2√6·π. "
                        "Elip nằm TRỌN trong z ∈ [6;10] ⊂ (0;12)"),
                    "oracle_call": ["elip_lay_mau_non",
                                    {"dinh": [0, 0, 12], "tam_day": [0, 0, 0],
                                     "ban_kinh": 6,
                                     "mat_phang": [1, 0, 1, -9]}]},
        },
        "expected_scene3d_kinds": ["curved_solid", "ellipse3", "plane3",
                                   "point3", "quantity"],
    },
]


# ══════════════════════════════════════════════════════════════════════════
# CA ÂM
# ══════════════════════════════════════════════════════════════════════════
#
# ⚠️ HAI CỘT, KHÔNG GỘP — bài học `CURVED_V3_LIVE_ACCEPTANCE` sự cố ⑥.
#
#     NEGATIVE_FAIL_CLOSED         hệ KHÔNG phát ra đáp số        ← bắt buộc 100%
#     TARGET_BOUNDARY_DEMONSTRATED lời từ chối chạm ĐÚNG ranh giới ← đo, không hứa
#
# V3 có một ca âm nhắm *"thiết diện cong xiên chưa hỗ trợ"* nhưng chết sớm ở R0;
# fail-closed thì đúng, mà nó **chưa bao giờ tới** chỗ định đo. Gọi đó là thành
# công là ghi công cho một phép thử chưa diễn ra.
#
# `expected_codes` dưới đây HẸP, và mỗi ca có lý do riêng cho tập của nó —
# không dùng chung một danh sách rộng cho cả hai, vì một danh sách rộng sẽ nhận
# mọi cái chết là bằng chứng.

CA_AM: list[dict[str, Any]] = [
    {
        "id": "n1_khoi_tron_xoay_tong_quat",
        "target_boundary": "solid_of_revolution_general",
        "problem_text": (
            "Trong mặt phẳng Oxy, cho hình phẳng (H) giới hạn bởi parabol "
            "y = x², trục Ox và đường thẳng x = 2. Quay hình phẳng (H) quanh "
            "trục Ox ta được một khối tròn xoay. Tính thể tích của khối tròn "
            "xoay đó."),
        # Ranh giới CÓ THẬT — chứng minh bằng VẮNG MẶT, kiểm được bằng máy.
        "absence_proof": {
            "no_symbolic_integration": {
                "quet": "app/simulation",
                "mau": ["sympy", "def tich_phan", "def integrate", "quad("],
                "mong_so_ket_qua": 0},
            "no_function_expression_type": {
                "thau_quyen": "contract.MemoryType",
                "mong_vang": ["function", "expression", "curve"]},
            "curved_kind_dong": {
                "thau_quyen": "contract · construct_curved_solid.curved_kind",
                "mong_dung_bang": ["ball", "cylinder", "cone"]},
        },
        # Đo TẤT ĐỊNH 2026-09-08 bằng hai chương trình mô hình DỄ viết nhất
        # (`docs/.../NEGATIVE_PROBE.json`). Cả hai fail-closed.
        "expected_codes": ["requested_operation_uncovered", "input_not_grounded"],
        "expected_stages": ["structural_coverage", "grounding"],
        "vi_sao_nhan_ca_hai_ma": (
            "Đề này KHÔNG nêu một điểm 3D nào có thể grounded. Nên hai đường "
            "chết đều nói đúng về ranh giới, chỉ ở hai tầng khác nhau: "
            "`requested_operation_uncovered` = *không có đường tạo ra vật đề "
            "đòi*; `input_not_grounded` = mô hình phải BỊA điểm mới dựng nổi "
            "một khối, và R0 chặn. Khác hẳn ca `n2`, nơi mọi dữ kiện ĐỀU "
            "grounded được nên một cái chết ở grounding sẽ là lạc đề."),
        "fail_closed_khong_tinh_ranh_gioi": [
            "semantic_program_invalid", "gate_out_of_scope",
            "postcondition_violated"],
    },
    {
        "id": "n2_khoi_ghep_bu_can_boolean",
        "target_boundary": "composite_boolean",
        "problem_text": (
            "Trong không gian Oxyz, cho khối hộp chữ nhật ABCD.A₁B₁C₁D₁ với "
            "A(0;0;0), B(8;0;0), C(8;6;0), D(0;6;0), A₁(0;0;10). Người ta "
            "khoan xuyên qua khối hộp một lỗ hình trụ tròn xoay có trục đi "
            "qua tâm hai mặt đáy và bán kính bằng 2. Tính thể tích phần vật "
            "thể còn lại."),
        "absence_proof": {
            "no_boolean_authority": {
                "quet": "app/simulation/geometry",
                "mau": ["def hieu", "def union", "def subtract", "def csg",
                        "boolean"],
                "mong_so_ket_qua": 0},
            "no_composite_memory_type": {
                "thau_quyen": "contract.MemoryType",
                "mong_vang": ["composite", "csg", "boolean_solid"]},
            "dieu_kien_toan_cuc_da_khai_la_khong_kiem_duoc": {
                "thau_quyen": "NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION",
                "khai": "hai MẶT KHÁC NHAU xuyên qua nhau — điều kiện TOÀN "
                        "CỤC, `kiem_mat_phang_don` đã khai là không kiểm được"},
        },
        # Mọi dữ kiện của đề này ĐỀU grounded được (tám đỉnh có toạ độ), nên
        # một cái chết ở `grounding` sẽ nói về chuyện khác, không về boolean.
        "expected_codes": ["requested_operation_uncovered"],
        "expected_stages": ["structural_coverage"],
        "vi_sao_nhan_mot_ma": (
            "Khối hộp dựng được và mọi toạ độ truy được về đề. Nên đường duy "
            "nhất còn lại để hệ nói KHÔNG là cổng phủ: nghĩa vụ hỏi thể tích "
            "*phần còn lại* — một vật mà không phép IR nào tạo ra được."),
        "fail_closed_khong_tinh_ranh_gioi": [
            "input_not_grounded", "semantic_program_invalid",
            "gate_out_of_scope", "postcondition_violated"],
        # ⚠️ BẪY ĐÃ ĐO: `n2-b` (bỏ hẳn cái lỗ, trả thể tích khối hộp) vẫn
        # fail-closed, NHƯNG `phan_loai` không-ca-âm xếp nó là
        # SYSTEM_COVERAGE_FAILURE — vì `nghia_vu_du_noi_dung_hut_ten` thấy
        # "đo đúng lượng, đúng kiểu chủ thể" và kết luận chỉ hụt TÊN. Ở ca âm
        # nhánh ấy không chạy (`la_ca_am=True` trả sớm), nên nó không sai số
        # đo; nhưng nó là một GIỚI HẠN THẬT của scorer và được ghi vào
        # `docs/THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION.md §9`.
        "gioi_han_scorer_da_do": "SCORER_CONTAINER_NAME_ONLY_HEURISTIC",
    },
]


# ══ PHÉP PHỦ — dẫn xuất, không gõ tay ════════════════════════════════════
PHU_THEO_HO: dict[str, list[str]] = {
    ho: [c["id"] for c in CA_DUONG if ho in c["families"]]
    for ho in HO_TRONG_PHAM_VI
}


def theo_id(ma: str) -> dict[str, Any]:
    for c in (*CA_DUONG, *CA_AM):
        if c["id"] == ma:
            return c
    raise KeyError(f"không có ca '{ma}' trong bộ đánh giá cuối")


def payload_gui_model(ca: dict[str, Any]) -> dict[str, str]:
    """ĐƯỜNG DUY NHẤT được gửi cho mô hình. Đúng một trường: đề bài.

    Không gold program, không oracle, không đáp số, không tên họ hình, không
    `expected_codes`. Bất kỳ thứ nào trong số đó lọt vào prompt sẽ biến phép đo
    *"mô hình có tự làm được không"* thành một phép đo dễ hơn hẳn — và con số
    thu về vẫn ra, nên hỏng im lặng.
    """
    return {"problem_text": ca["problem_text"]}


def corpus_json() -> dict[str, Any]:
    """Bản đem BĂM và đem GHI. Cố ý KHÔNG chứa `expected` — đáp số nằm ở
    `EXPECTED_RESULTS`, băm riêng, để hai thứ trôi độc lập được phát hiện."""
    return {
        "khai": "Bộ ca đánh giá cuối của khoá luận. Cố định, không rút thăm.",
        "wave": "THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION",
        "positive_cases": [
            {"id": c["id"], "families": c["families"],
             "problem_text": c["problem_text"],
             "problem_hash": hashlib.sha256(
                 c["problem_text"].encode("utf-8")).hexdigest(),
             "obligations": [o["kind"] for o in
                             c["request_contract_gold"]["obligations"]],
             "request_contract_gold": c["request_contract_gold"],
             "gold_program": c["gold_program"],
             "expected_scene3d_kinds": c["expected_scene3d_kinds"]}
            for c in CA_DUONG],
        "negative_cases": [
            {k: v for k, v in c.items()} | {
                "problem_hash": hashlib.sha256(
                    c["problem_text"].encode("utf-8")).hexdigest()}
            for c in CA_AM],
        "family_coverage": PHU_THEO_HO,
        "families_in_scope": list(HO_TRONG_PHAM_VI),
    }


def expected_results_json() -> dict[str, Any]:
    return {
        "khai": "Đáp số mong đợi + oracle ĐỘC LẬP. KHÔNG gửi cho mô hình.",
        "display_convention": "radical.display() — hữu tỉ · π · √, theo thứ tự ấy",
        "oracle_module": "scripts/thesis_acceptance_oracle.py",
        "oracle_tolerance": {"CLOSED_FORM": 1e-12, "SAMPLED": 1e-8},
        "cases": {c["id"]: c["expected"] for c in CA_DUONG},
        "negative_expectations": {
            c["id"]: {"target_boundary": c["target_boundary"],
                      "expected_codes": c["expected_codes"],
                      "expected_stages": c["expected_stages"],
                      "fail_closed_khong_tinh_ranh_gioi":
                          c["fail_closed_khong_tinh_ranh_gioi"]}
            for c in CA_AM},
    }


CORPUS_HASH = bam_chinh_tac(corpus_json())
EXPECTED_RESULTS_HASH = bam_chinh_tac(expected_results_json())
