# -*- coding: utf-8 -*-
"""BỐN ĐỀ cho NAME_ONLY_CONTRACT_LIVE_PROBE. **0 API call.**

─── HAI CÂU HỎI, TÁCH RỜI ─────────────────────────────────────────────────

  A. Sau khi thẻ in `tên<point3>`/`tên<vector3>`, mô hình có tự viết đúng một
     ĐỊNH DANH ngay ở đầu ra THÔ không?
  B. Nếu nó vẫn lồng hoặc vẫn bọc `var`, bộ chuẩn hoá tất định có cứu được
     chương trình mà KHÔNG nới R0 không?

Hai câu này độc lập, và một chương trình có thể `RAW_CONTRACT_COMPLIANT = NO`
mà `ONE_SHOT_CORRECT = YES`. Đó là kết quả hợp lệ, không phải một lời bào chữa.

─── VÌ SAO KHÔNG ĐỀ NÀO NÓI "TỊNH TIẾN" ───────────────────────────────────

§5 cấm: nói "tịnh tiến" là đọc hộ mô hình phần khó. Đề chỉ mô tả HÌNH bằng ngôn
ngữ SGK (*"ABCD là hình bình hành"*, *"AA' song song và bằng BB'"*), rồi hỏi một
đại lượng. Việc *"muốn có D thì lấy A cộng vectơ BC"* là suy luận của mô hình.

Cũng không đề nào nói "vectơ" như một mệnh lệnh. `n3` cố ý **không cần** tịnh
tiến — nó tồn tại để hỏi câu A có tổng quát không, hay chỉ đúng với `translate`
vì mô hình vừa nhìn thấy phép ấy trong thẻ.

─── ORACLE ────────────────────────────────────────────────────────────────

`dap_so` tính TAY từ hệ trục ghi ở `kiem_tay`, rồi đối chiếu độc lập với kết
quả chạy `chuan_tac`. `chuan_tac` **không bao giờ** vào prompt.
"""
from __future__ import annotations

from scripts.translation_probe_cases import (  # noqa: F401
    _chu_ky, _de_cu, _ngu, can, q,
)

_THU_MUC_THEM = ("translation-probe", "named-operand-ergonomics")


def _d(t, xyz, ly_do):
    return {"kind": "declare_point", "target_var": t, "at": xyz,
            "model_assumption": ly_do}


def _vec(t, a, b):
    return {"kind": "assign", "target_var": t,
            "expr": {"kind": "vector_from_points", "from_point": a,
                     "to_point": b}}


def _tt(t, p, v):
    return {"kind": "construct_point", "target_var": t,
            "expr": {"kind": "translate", "point": p, "vector": v}}


def _do(t, luong, of, wrt=None):
    e = {"kind": "measure", "quantity": luong, "of": of}
    if wrt:
        e["wrt"] = wrt
    return {"kind": "assign", "target_var": t, "expr": e}


# ══════════════════════════════════════════════════════════════════════════
# n1 — HÌNH THOI trong không gian. Một đỉnh phải suy ra từ ba đỉnh kia.
#      Khác `t1` của translation probe: kia là hình bình hành ĐÁY của một
#      chóp và hỏi khoảng cách điểm–điểm; đây là hình thoi TỰ ĐỨNG trong
#      không gian và hỏi khoảng cách từ một đỉnh tới một ĐƯỜNG.
# ══════════════════════════════════════════════════════════════════════════
N1 = {
    "id": "n1_thoi_dinh_thu_tu",
    "topology": "rhombus_free_standing",
    "capability_mix": ["vector", "translate", "line", "distance"],
    "name_slot_families": ["vector_from_points", "translate",
                           "construct_line", "measure"],
    "dependency_depth": 4,
    "obligation_count": 1,
    "de": (
        "Trong không gian với hệ toạ độ Oxyz, cho ba đỉnh liên tiếp của một "
        "hình thoi MNPQ là M(1; 0; 2), N(4; 0; 2) và P(5; 2; 4). "
        "Tính khoảng cách từ đỉnh Q đến đường thẳng MP."
    ),
    # Q = M + vectơ NP  (hình thoi ⇒ MQ ∥ NP và MQ = NP)
    #   MN = (3,0,0) |MN|=3 ;  NP = (1,2,2) |NP|=3  ⇒ đúng là hình thoi
    #   Q = (2,2,4)
    # MQ = (1,2,2), MP = (4,2,2); MQ×MP = (0,6,−6), |·| = 6√2
    # |MP| = 2√6 ⇒ d = 6√2/(2√6) = 3/√3 = √3
    #
    # ⚠️ HAI ĐỈNH ĐẦU CỐ Ý KHÔNG NẰM TRÊN MỘT MẶT TOẠ ĐỘ. Bản đầu dùng
    # P(4,3,2) — cả hình nằm trong mặt z=2, và khi ấy MỘT Q PHẢN CHIẾU cho
    # ĐÚNG CÙNG khoảng cách (phản xạ qua mặt chứa đường thì bảo toàn khoảng
    # cách tới đường ấy). Oracle như thế nhận cả lời giải sai dấu vectơ —
    # tức nó không đo được thứ probe này tồn tại để đo.
    "kiem_tay": "M(1,0,2) N(4,0,2) P(5,2,4): MN=(3,0,0) và NP=(1,2,2) cùng "
                "dài 3 ⇒ hình thoi. Q = M + NP = (2,2,4); "
                "d(Q, MP) = |MQ×MP|/|MP| = 6√2/(2√6) = √3",
    "dap_so": can(1, 3),
    "chuan_tac": {
        "title": "Khoảng cách từ đỉnh thứ tư của hình thoi tới đường chéo",
        "memory_declarations": [{"name": "d_q_mp", "type": "float"}],
        "statements": [
            _d("M", [1, 0, 2], "toạ độ đề cho"),
            _d("N", [4, 0, 2], "toạ độ đề cho"),
            _d("P", [5, 2, 4], "toạ độ đề cho"),
            _vec("v_np", "N", "P"),
            _tt("Q", "M", "v_np"),
            {"kind": "construct_line", "target_var": "MP",
             "through_a": "M", "through_b": "P"},
            _do("d_q_mp", "distance", "Q", "MP"),
        ],
    },
}

# ══════════════════════════════════════════════════════════════════════════
# n2 — LĂNG TRỤ XIÊN. Hai vectơ dẫn xuất, một điểm tịnh tiến dùng tiếp.
#      Khác `t2`/`t3`: lăng trụ ở đây XIÊN (cạnh bên không vuông đáy) nên
#      toạ độ đỉnh trên KHÔNG hiển nhiên — mô hình không khai thẳng được.
# ══════════════════════════════════════════════════════════════════════════
N2 = {
    "id": "n2_lang_tru_xien_hai_vecto",
    "topology": "oblique_prism_chained",
    "capability_mix": ["vector", "translate", "midpoint", "line", "distance"],
    "name_slot_families": ["vector_from_points", "translate", "midpoint",
                           "construct_line", "measure"],
    "dependency_depth": 5,
    "obligation_count": 1,
    "de": (
        "Trong không gian Oxyz cho lăng trụ ABC.A'B'C' có A(0; 0; 0), "
        "B(4; 0; 0), C(0; 4; 0) và A'(1; 1; 3). Ba cạnh bên AA', BB', CC' đôi "
        "một song song và bằng nhau. Gọi I là trung điểm của B'C'. "
        "Tính khoảng cách từ A đến đường thẳng B'I."
    ),
    # AA' = (1,1,3) ⇒ B' = B + AA' = (5,1,3); C' = C + AA' = (1,5,3)
    # I = trung điểm B'C' = (3,3,3)
    # B'I = I − B' = (−2,2,0); AB' = (5,1,3)
    # AB' × B'I = (1*0−3*2, 3*(−2)−5*0, 5*2−1*(−2)) = (−6,−6,12)
    # |·| = 6√(1+1+4) = 6√6 ; |B'I| = 2√2 ⇒ d = 6√6/(2√2) = 3√3
    "kiem_tay": "AA'=(1,1,3) ⇒ B'=(5,1,3), C'=(1,5,3), I=(3,3,3); "
                "d(A, B'I) = |AB'×B'I|/|B'I| = 6√6/(2√2) = 3√3",
    "dap_so": can(3, 3),
    "chuan_tac": {
        "title": "Khoảng cách từ đỉnh đáy tới một đường của mặt trên",
        "memory_declarations": [{"name": "d_a_bi", "type": "float"}],
        "statements": [
            _d("A", [0, 0, 0], "toạ độ đề cho"),
            _d("B", [4, 0, 0], "toạ độ đề cho"),
            _d("C", [0, 4, 0], "toạ độ đề cho"),
            _d("A_prime", [1, 1, 3], "toạ độ đề cho"),
            _vec("v_aa", "A", "A_prime"),
            _tt("B_prime", "B", "v_aa"),
            _tt("C_prime", "C", "v_aa"),
            {"kind": "construct_point", "target_var": "I",
             "expr": {"kind": "midpoint", "a": "B_prime", "b": "C_prime"}},
            {"kind": "construct_line", "target_var": "BI",
             "through_a": "B_prime", "through_b": "I"},
            _do("d_a_bi", "distance", "A", "BI"),
        ],
    },
}

# ══════════════════════════════════════════════════════════════════════════
# n3 — KHÔNG cần tịnh tiến. Ô TÊN bị ép qua `construct_plane.through` và
#      `measure.of/wrt`, với một ĐIỂM DẪN XUẤT làm một trong ba đỉnh mặt.
#      Đây là ca trả lời câu *"NAME<T> có tổng quát không"*.
# ══════════════════════════════════════════════════════════════════════════
N3 = {
    "id": "n3_mat_qua_diem_dan_xuat",
    "topology": "plane_through_derived_point",
    "capability_mix": ["midpoint", "divide_segment", "plane", "distance"],
    "name_slot_families": ["midpoint", "divide_segment", "construct_plane",
                           "measure"],
    "dependency_depth": 4,
    "obligation_count": 1,
    "de": (
        "Trong không gian Oxyz cho bốn điểm S(0; 0; 6), A(0; 0; 0), "
        "B(6; 0; 0) và D(0; 6; 0). Gọi E là trung điểm của SB và F là điểm "
        "thuộc đoạn SD sao cho SF = 2FD. "
        "Tính khoảng cách từ điểm B đến mặt phẳng (AEF)."
    ),
    # E = (3,0,3); F = S + (2/3)(D−S) = (0,4,2)
    # pháp tuyến AE × AF = (3,0,3)×(0,4,2) = (−12,−6,12) ∝ (−2,−1,2), |n| = 3
    # n·(B−A) = −12 ⇒ d = 12/3 = 4
    #
    # ⚠️ CÂU HỎI ĐẦU LÀ *"cos² góc giữa AE và (AEF)"* — VÀ NÓ HỎNG. AE nằm
    # TRONG mặt ấy nên đáp số là 1 với BẤT KỲ mặt nào chứa A và E: một F dựng
    # sai vẫn cho đúng số. Oracle không phân biệt được lời giải sai thì nó
    # không đo được gì. Câu hỏi này phụ thuộc F thật sự.
    "kiem_tay": "E = trung điểm SB = (3,0,3); SF=2FD ⇒ F = S + (2/3)(D−S) = "
                "(0,4,2); pháp tuyến (AEF) ∝ (−2,−1,2), |n|=3; "
                "d(B,(AEF)) = |n·AB|/|n| = 12/3 = 4",
    "dap_so": q(4),
    "chuan_tac": {
        "title": "Khoảng cách từ một đỉnh tới mặt phẳng qua hai điểm dẫn xuất",
        "memory_declarations": [{"name": "d_b_aef", "type": "float"}],
        "statements": [
            _d("S", [0, 0, 6], "toạ độ đề cho"),
            _d("A", [0, 0, 0], "toạ độ đề cho"),
            _d("B", [6, 0, 0], "toạ độ đề cho"),
            _d("D", [0, 6, 0], "toạ độ đề cho"),
            {"kind": "construct_point", "target_var": "E",
             "expr": {"kind": "midpoint", "a": "S", "b": "B"}},
            {"kind": "construct_point", "target_var": "F",
             "expr": {"kind": "divide_segment", "a": "S", "b": "D",
                      "ratio": "2/3"}},
            {"kind": "construct_plane", "target_var": "AEF",
             "through": ["A", "E", "F"]},
            _do("d_b_aef", "distance", "B", "AEF"),
        ],
    },
}

# ══════════════════════════════════════════════════════════════════════════
# n4 — CHUỖI SÂU, hai họ primitive, không tịnh tiến.
#      điểm dẫn xuất → đường → mặt → giao điểm → đo. Độ sâu 5.
# ══════════════════════════════════════════════════════════════════════════
N4 = {
    "id": "n4_giao_duong_mat_roi_do",
    "topology": "line_plane_intersection_then_measure",
    "capability_mix": ["midpoint", "line", "plane", "intersect", "distance"],
    "name_slot_families": ["midpoint", "construct_line", "construct_plane",
                           "intersect_line_plane", "measure"],
    "dependency_depth": 5,
    "obligation_count": 1,
    "de": (
        "Trong không gian Oxyz cho hình chóp S.ABCD có đáy là hình vuông "
        "ABCD với A(0; 0; 0), B(2; 0; 0), C(2; 2; 0), D(0; 2; 0) và đỉnh "
        "S(0; 0; 4). Gọi M là trung điểm của cạnh SC. Đường thẳng BM cắt mặt "
        "phẳng (SAD) tại điểm K. Tính độ dài đoạn AK."
    ),
    # M = (1,1,2). Đường BM: B(2,0,0) + t(−1,1,2).
    # (SAD) là mặt x = 0 ⇒ 2 − t = 0 ⇒ t = 2 ⇒ K = (0,2,4).
    # AK = |(0,2,4)| = √20 = 2√5
    "kiem_tay": "M = (1,1,2); BM: (2,0,0)+t(−1,1,2); (SAD): x=0 ⇒ t=2 ⇒ "
                "K=(0,2,4); AK = √(4+16) = 2√5",
    "dap_so": can(2, 5),
    "chuan_tac": {
        "title": "Giao của một đường với mặt bên rồi đo khoảng cách",
        "memory_declarations": [{"name": "do_dai_ak", "type": "float"}],
        "statements": [
            _d("A", [0, 0, 0], "toạ độ đề cho"),
            _d("B", [2, 0, 0], "toạ độ đề cho"),
            _d("C", [2, 2, 0], "toạ độ đề cho"),
            _d("D", [0, 2, 0], "toạ độ đề cho"),
            _d("S", [0, 0, 4], "toạ độ đề cho"),
            {"kind": "construct_point", "target_var": "M",
             "expr": {"kind": "midpoint", "a": "S", "b": "C"}},
            {"kind": "construct_line", "target_var": "BM",
             "through_a": "B", "through_b": "M"},
            {"kind": "construct_plane", "target_var": "SAD",
             "through": ["S", "A", "D"]},
            {"kind": "construct_point", "target_var": "K",
             "expr": {"kind": "intersect_line_plane", "line": "BM",
                      "plane": "SAD"}},
            _do("do_dai_ak", "distance", "A", "K"),
        ],
    },
}

CASES = [N1, N2, N3, N4]


def check_contamination() -> list[str]:
    """Nhiễm chéo với MỌI bộ đề đã dùng, kể cả hai bộ mới nhất.

    Dùng lại chữ ký cấu hình của `translation_probe_cases` (khối + bội số +
    mệnh đề hỏi) chứ không đếm n-gram: n-gram bắt trúng văn mẫu SGK
    (*"trong không gian với hệ toạ độ Oxyz cho hình chóp"*) ở gần như mọi đề,
    nên nó báo động ở 4/6 ca mà không ca nào thật sự trùng.
    """
    import json as _json
    from pathlib import Path as _P

    goc = _P(__file__).resolve().parents[2]
    cu = list(_de_cu())
    for ten in _THU_MUC_THEM:
        d = goc / "docs" / "evaluation" / "geometry" / ten
        for f in (d.glob("*.json") if d.is_dir() else ()):
            try:
                x = _json.loads(f.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            ngan = [x]
            while ngan:
                n = ngan.pop()
                if isinstance(n, dict):
                    for k, v in n.items():
                        if (k in ("problem_text", "de", "problem")
                                and isinstance(v, str) and len(v) > 40):
                            cu.append(v)
                        else:
                            ngan.append(v)
                elif isinstance(n, list):
                    ngan.extend(n)

    chu_ky_cu = [(_chu_ky(v), v) for v in cu]
    ra = []
    for c in CASES:
        ck = _chu_ky(c["de"])
        for ck_cu, van in chu_ky_cu:
            if ck == ck_cu:
                ra.append(f"{c['id']}: TRÙNG ĐỀ — {van[:80]}")
                break
            if ck[:2] == ck_cu[:2] and ck[2] != ck_cu[2]:
                if (cn := _ngu(ck[2], 8) & _ngu(ck_cu[2], 8)):
                    ra.append(f"{c['id']}: cùng hình VÀ trùng câu hỏi — "
                              f"{sorted(cn)[0][:60]}")
                    break
    return ra
