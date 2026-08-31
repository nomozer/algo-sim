# -*- coding: utf-8 -*-
"""MƯỜI ĐỀ CHƯA TỪNG THẤY cho GENERALIZATION MATRIX. **Không có lời giải.**

─── VÌ SAO KHÔNG DÙNG LẠI BỐN ĐỀ NHỊ DIỆN ─────────────────────────────────

Bốn đề ấy đã qua **năm** vòng đo và ba vòng sửa hệ. Chúng thành DEVELOPMENT
EVIDENCE, không còn là unseen — tiếp tục tune theo chúng là overfitting, và
mọi con số rút ra sẽ nói về bốn bài chứ không nói về năng lực.

─── VÌ SAO MỖI ĐỀ CHO SỐ ĐO CỤ THỂ ────────────────────────────────────────

Mô hình TỰ CHỌN hệ toạ độ, nên một đáp số tuyệt đối chỉ so được khi đề ghim
thang: `cạnh bằng 2` chứ không `cạnh bằng a`. Với góc thì không cần — `cos²`
bất biến theo tỉ lệ. Đề THPT vốn hay ghi số cụ thể, nên ràng buộc này không
làm đề bớt tự nhiên.

⚠️ `dap_so` là **oracle của bộ đo**, KHÔNG BAO GIỜ gửi cho mô hình. Nó tính TAY
từ hệ trục ghi ở `kiem_tay` — mỗi con số là một nguồn sai mới, nên phép tính
được viết ra để người sau kiểm lại được, không phải để tin.

`do_sau` và `nang_luc` chỉ phục vụ phân tích SAU khi chạy. Chúng không đi vào
prompt, và không được dùng để chọn nhánh xử lý nào.
"""
from __future__ import annotations

from fractions import Fraction

#: `(hệ số, căn thức)` — cùng quy ước `geometry/radical.radical()`.
CAN = "radical"
HUU_TI = "rational"


def q(x) -> tuple[str, Fraction]:
    return (HUU_TI, Fraction(x))


def can(he, c: int) -> tuple[str, tuple[Fraction, int]]:
    return (CAN, (Fraction(he), c))


CASES: list[dict] = [
    {
        "id": "gm_01_hop_chu_nhat",
        "topology": "hình hộp chữ nhật",
        "do_sau": "MEDIUM",
        "so_diem_goc": 8,
        "so_nghia_vu": 1,
        "nang_luc": ["midpoint", "construct_plane", "distance"],
        "de": (
            "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AD = 2 và "
            "AA' = 4. Gọi M là trung điểm của cạnh CC', N là trung điểm của "
            "đoạn AM. Tính khoảng cách từ N đến mặt phẳng (ABCD)."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) C'(2,2,4). M = (2,2,2); "
            "N = (1,1,1). Mặt (ABCD) là z = 0 ⇒ d = 1."
        ),
        "dap_so": q(1),
    },
    {
        "id": "gm_02_lang_tru",
        "topology": "lăng trụ đứng đáy tam giác vuông",
        "do_sau": "MEDIUM",
        "so_diem_goc": 4,
        "so_nghia_vu": 1,
        "nang_luc": ["midpoint", "construct_plane", "distance_point_plane"],
        "de": (
            "Cho lăng trụ đứng ABC.A'B'C' có đáy ABC vuông tại B với AB = 2, "
            "BC = 2 và cạnh bên AA' = 2. Gọi M là trung điểm của A'C'. Tính "
            "khoảng cách từ M đến mặt phẳng (ABB'A')."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(2,2,0) A'(0,0,2) C'(2,2,2). M = (1,1,2). "
            "Mặt (ABB'A') là y = 0 ⇒ d = 1."
        ),
        "dap_so": q(1),
    },
    {
        "id": "gm_03_chop_tu_giac",
        "topology": "chóp đáy vuông",
        "do_sau": "HIGH",
        "so_diem_goc": 5,
        "so_nghia_vu": 1,
        "nang_luc": ["midpoint", "construct_line", "distance_line_line_skew"],
        "de": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
            "góc với mặt phẳng đáy và SA = 2. Gọi M là trung điểm của SC, N là "
            "trung điểm của AD. Tính khoảng cách giữa hai đường thẳng MN và AB."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) S(0,0,2). M(1,1,1) N(0,1,0). "
            "u = AB = (1,0,0), v = MN = (-1,0,-1), u×v = (0,1,0), |u×v|² = 1; "
            "w = N - A = (0,1,0), w·(u×v) = 1 ⇒ d² = 1 ⇒ d = 1."
        ),
        "dap_so": q(1),
    },
    {
        "id": "gm_04_lap_phuong_can",
        "topology": "lập phương",
        "do_sau": "MEDIUM",
        "so_diem_goc": 8,
        "so_nghia_vu": 1,
        "nang_luc": ["construct_plane", "distance_point_plane", "radical"],
        "de": (
            "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2. Tính khoảng "
            "cách từ đỉnh A đến mặt phẳng (A'BD)."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) D(0,2,0) A'(0,0,2). A'B = (2,0,-2), "
            "A'D = (0,2,-2), n = (1,1,1); mặt qua B ⇒ x + y + z = 2. "
            "d(A) = 2/√3 = 2√3/3."
        ),
        "dap_so": can("2/3", 3),
    },
    {
        "id": "gm_05_thiet_dien_do_tiep",
        "topology": "chóp đáy vuông + mặt cắt",
        "do_sau": "HIGH",
        "so_diem_goc": 5,
        "so_nghia_vu": 1,
        "nang_luc": ["midpoint", "construct_plane", "intersect_line_plane",
                     "distance"],
        "de": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
            "góc với mặt phẳng đáy và SA = 2. Gọi M là trung điểm của SB. Mặt "
            "phẳng (ADM) cắt cạnh SC tại điểm N. Tính khoảng cách từ N đến mặt "
            "phẳng (ABCD)."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) S(0,0,2). M(1,0,1). Mặt (ADM) "
            "có pháp tuyến (2,0,-2) ⇒ x = z. SC: (2t,2t,2-2t) ⇒ t = 1/2 ⇒ "
            "N(1,1,1). Mặt đáy z = 0 ⇒ d = 1."
        ),
        "dap_so": q(1),
    },
    {
        "id": "gm_06_khoang_cach_dung_phu",
        "topology": "chóp đáy tam giác vuông",
        "do_sau": "MEDIUM",
        "so_diem_goc": 4,
        "so_nghia_vu": 1,
        "nang_luc": ["construct_plane", "distance_point_plane", "radical"],
        "de": (
            "Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), tam giác "
            "ABC vuông tại B với AB = 1, BC = 1 và SA = 1. Tính khoảng cách từ "
            "điểm A đến mặt phẳng (SBC)."
        ),
        "kiem_tay": (
            "A(0,0,0) B(1,0,0) C(1,1,0) S(0,0,1). SB = (1,0,-1), SC = (1,1,-1), "
            "n = (1,0,1); mặt qua B ⇒ x + z = 1. d(A) = 1/√2 = √2/2."
        ),
        "dap_so": can("1/2", 2),
    },
    {
        "id": "gm_07_goc_khong_noi_nhi_dien",
        "topology": "lập phương",
        "do_sau": "LOW",
        "so_diem_goc": 8,
        "so_nghia_vu": 1,
        "nang_luc": ["construct_line", "angle_cos_sq"],
        # CỐ Ý không có chữ "nhị diện": đây là phép thử thiên lệch prompt (§7).
        # Hai ĐƯỜNG THẲNG không có chiều ⇒ `angle_cos_sq` là phép đo đúng, và
        # chọn `angle_cos` ở đây là chọn sai — validator sẽ từ chối.
        "de": (
            "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 1. Tính côsin của "
            "góc giữa hai đường thẳng AC' và BC'."
        ),
        "kiem_tay": (
            "A(0,0,0) C'(1,1,1) B(1,0,0). AC' = (1,1,1), BC' = (0,1,1). "
            "cos² = 2²/(3·2) = 2/3."
        ),
        "dap_so": q("2/3"),
        "do_goc": True,
    },
    {
        "id": "gm_08_da_nghia_vu",
        "topology": "chóp đáy vuông",
        "do_sau": "MEDIUM",
        "so_diem_goc": 5,
        "so_nghia_vu": 2,
        "nang_luc": ["construct_plane", "perpendicular", "distance_point_plane",
                     "radical"],
        "de": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
            "góc với mặt phẳng đáy và SA = 2. Chứng minh đường thẳng BD vuông "
            "góc với mặt phẳng (SAC), rồi tính khoảng cách từ điểm B đến mặt "
            "phẳng (SAC)."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) S(0,0,2). Mặt (SAC): x − y = 0, "
            "pháp tuyến (1,−1,0) cùng phương BD = (−2,2,0) ⇒ BD ⊥ (SAC). "
            "d(B) = 2/√2 = √2."
        ),
        "dap_so": can(1, 2),
    },
    {
        "id": "gm_09_do_thi_sau",
        "topology": "chóp đáy vuông",
        "do_sau": "HIGH",
        "so_diem_goc": 5,
        "so_nghia_vu": 1,
        "nang_luc": ["midpoint", "construct_plane", "construct_line",
                     "intersect_line_plane", "distance"],
        "de": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
            "góc với mặt phẳng đáy và SA = 4. Gọi E là trung điểm của SB, F là "
            "trung điểm của SD. Đường thẳng SC cắt mặt phẳng (AEF) tại G. "
            "Tính khoảng cách từ G đến mặt phẳng (ABCD)."
        ),
        "kiem_tay": (
            "S(0,0,4) A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0). E(1,0,2) F(0,1,2). "
            "AE = (1,0,2), AF = (0,1,2), n = (−2,−2,1) ⇒ mặt (AEF): "
            "−2x − 2y + z = 0. SC: (2t,2t,4−4t) ⇒ −12t + 4 = 0 ⇒ t = 1/3 ⇒ "
            "G(2/3, 2/3, 8/3). Đáy z = 0 ⇒ d = 8/3."
        ),
        "dap_so": q("8/3"),
    },
    {
        "id": "gm_10_ngoai_nang_luc",
        "topology": "chóp đáy vuông + MẶT CẦU",
        "do_sau": "—",
        "so_diem_goc": 5,
        "so_nghia_vu": 1,
        "nang_luc": ["mặt cầu — NGOÀI IR"],
        # Đề THPT hoàn toàn hợp lệ, nhưng mặt cầu không biểu diễn được bằng
        # kernel đa diện hữu tỉ. Kết cục ĐÚNG là TỪ CHỐI TRUNG THỰC, không phải
        # một khối đa diện gần giống.
        "de": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
            "góc với mặt phẳng đáy và SA = 2. Tính bán kính mặt cầu ngoại tiếp "
            "hình chóp S.ABCD."
        ),
        "kiem_tay": "Ngoài năng lực: kernel chỉ có đa diện, không có mặt cong.",
        "dap_so": None,
        "ngoai_pham_vi": True,
    },
]


def in_scope() -> list[dict]:
    return [c for c in CASES if not c.get("ngoai_pham_vi")]
