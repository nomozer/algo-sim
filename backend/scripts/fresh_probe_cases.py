# -*- coding: utf-8 -*-
"""SÁU ĐỀ TƯƠI cho PROMPT BIAS PROBE (§13–§14). **Không có lời giải.**

─── VÌ SAO KHÔNG DÙNG LẠI BỐN ĐỀ NHỊ DIỆN HAY MƯỜI ĐỀ MATRIX ──────────────

Bốn đề nhị diện đã qua năm vòng đo và ba vòng sửa hệ. Mười đề matrix vừa được
dùng để *tìm ra* chính những bệnh mà wave này sửa — cộng thêm việc AUDIT đọc
lại từng lượt hỏng của chúng. Cả hai tập nay là **bằng chứng phát triển**: đo
lại một bản sửa trên chính tập đã dẫn tới bản sửa ấy là đo trí nhớ của ta, không
đo năng lực của mô hình.

─── SÁU ĐỀ NÀY ĐO GÌ ──────────────────────────────────────────────────────

Không đo *"mô hình giải được hình học không"* — điều đó matrix đã trả lời. Đo
đúng một câu hẹp hơn: **hợp đồng mới có làm giảm ma sát tổng hợp không.** Nên
sáu đề cố ý nằm TRONG năng lực IR hiện có: không mặt cong, không quỹ tích,
không Oxyz. Một đề ngoài năng lực sẽ fail-closed và không nói gì về câu hỏi.

Bề rộng theo §14, mỗi đề một hình dạng khác nhau — và ba trong sáu đề chạm
thẳng vào bệnh nặng nhất của AUDIT (`angle_cos` trên `line3`, 14 lượt), vì
một bản sửa thiên lệch phải được đo ở đúng chỗ nó nhắm tới.

⚠️ `dap_so` là oracle của BỘ ĐO, không bao giờ gửi cho mô hình. Nó tính TAY từ
hệ trục ghi ở `kiem_tay` — mỗi con số là một nguồn sai mới, nên phép tính được
viết ra để người sau kiểm lại, không phải để tin.

─── NHIỄM CHÉO ────────────────────────────────────────────────────────────

`check_contamination()` đối chiếu với pool holdout ĐÃ NIÊM PHONG. Bẫy này đã
cắn một lần: bốn đề matrix trùng pool và phải thay cả bốn. Chạy nó TRƯỚC khi
tiêu một call nào.
"""
from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

CAN = "radical"
HUU_TI = "rational"


def q(x) -> tuple[str, Fraction]:
    return (HUU_TI, Fraction(x))


def can(he, c: int) -> tuple[str, tuple[Fraction, int]]:
    return (CAN, (Fraction(he), c))


CASES: list[dict] = [
    {
        "id": "fp_1_tu_dien_nhieu_buoc",
        "hinh_dang": "tứ diện, nhiều bước dựng",
        "do_sau": "HIGH",
        "so_nghia_vu": 1,
        "nham": "chuỗi dựng dài — trung điểm của trung điểm",
        "de": (
            "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc và "
            "OA = OB = OC = 2. Gọi M là trung điểm của BC và N là trung điểm "
            "của OM. Tính khoảng cách từ N đến mặt phẳng (OAB)."
        ),
        "kiem_tay": (
            "O(0,0,0) A(2,0,0) B(0,2,0) C(0,0,2). M = (0,1,1); "
            "N = (0, 1/2, 1/2). Mặt (OAB) chứa O, A, B ⇒ z = 0. "
            "d = |1/2| = 1/2."
        ),
        "dap_so": q(Fraction(1, 2)),
    },
    {
        "id": "fp_2_lang_tru_goc",
        "hinh_dang": "lăng trụ đứng đáy tam giác vuông",
        "do_sau": "MEDIUM",
        "so_nghia_vu": 1,
        "nham": "GÓC — bẫy thiên lệch `angle_cos` trên line3",
        "de": (
            "Cho lăng trụ đứng ABC.A'B'C' có đáy ABC vuông tại A với "
            "AB = 2, AC = 2 và cạnh bên AA' = 2. Tính côsin của góc giữa hai "
            "đường thẳng AB' và BC'."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(0,2,0) A'(0,0,2) B'(2,0,2) C'(0,2,2). "
            "AB' = (2,0,2); BC' = (-2,2,2). tích vô hướng = -4+0+4 = 0 "
            "⇒ hai đường VUÔNG GÓC ⇒ cos = 0, cos² = 0."
        ),
        "dap_so": q(0),
    },
    {
        "id": "fp_3_hop_chu_nhat_can",
        "hinh_dang": "hình hộp chữ nhật, đáp số có căn",
        "do_sau": "MEDIUM",
        "so_nghia_vu": 1,
        "nham": "kết quả vô tỉ — mô hình hay né hoặc bẻ hệ trục",
        "de": (
            "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AD = 4 và "
            "AA' = 4. Tính khoảng cách từ đỉnh A đến đường thẳng BD."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) D(0,4,0). Tam giác ABD vuông tại A, "
            "BD = √(4+16) = √20 = 2√5. d = AB·AD/BD = 2·4/(2√5) "
            "= 4/√5 = 4√5/5."
        ),
        "dap_so": can(Fraction(4, 5), 5),
    },
    {
        "id": "fp_4_thiet_dien_hoi_tiep",
        "hinh_dang": "thiết diện + câu hỏi nối tiếp",
        "do_sau": "HIGH",
        "so_nghia_vu": 1,
        "nham": "dựng thiết diện rồi ĐO trên nó",
        "de": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
            "SA vuông góc với mặt phẳng đáy và SA = 2. Gọi (P) là mặt phẳng "
            "đi qua ba điểm A, B và trung điểm M của cạnh SC. Xác định thiết "
            "diện của hình chóp cắt bởi (P) và tính khoảng cách từ đỉnh S "
            "đến mặt phẳng (P)."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) S(0,0,2). M = (1,1,1). "
            "Mặt (P) qua A(0,0,0), B(2,0,0), M(1,1,1): pháp tuyến "
            "AB×AM = (2,0,0)×(1,1,1) = (0·1-0·1, 0·1-2·1, 2·1-0·1) "
            "= (0,-2,2) ∼ (0,-1,1). Mặt: -y+z = 0. "
            "d(S) = |-0+2|/√2 = 2/√2 = √2."
        ),
        "dap_so": can(1, 2),
    },
    {
        "id": "fp_5_goc_va_khoang_cach",
        "hinh_dang": "góc + khoảng cách trong một bài",
        "do_sau": "HIGH",
        "so_nghia_vu": 2,
        "nham": "HAI nghĩa vụ khác loại — góc phải chọn đúng phép đo",
        "de": (
            "Cho hình chóp S.ABC có đáy ABC vuông tại B với AB = 2, "
            "BC = 2, cạnh bên SA vuông góc với mặt phẳng đáy và SA = 2. "
            "Tính côsin của góc giữa đường thẳng SC và mặt phẳng (ABC), "
            "và tính khoảng cách từ điểm B đến mặt phẳng (SAC)."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(2,2,0) S(0,0,2). "
            "① SC = (2,2,-2), mặt (ABC) là z = 0, pháp tuyến (0,0,1). "
            "sin = |−2|/(2√3·1) = 1/√3 ⇒ cos² của GÓC = 1 − 1/3 = 2/3. "
            "② Mặt (SAC) qua A(0,0,0), C(2,2,0), S(0,0,2): pháp tuyến "
            "AC×AS = (2,2,0)×(0,0,2) = (4,-4,0) ∼ (1,-1,0). "
            "d(B) = |2−0|/√2 = 2/√2 = √2."
        ),
        "dap_so": can(1, 2),
        "dap_so_phu": q(Fraction(2, 3)),
    },
    {
        "id": "fp_6_nhieu_nghia_vu_sau",
        "hinh_dang": "nhiều nghĩa vụ, độ sâu cao",
        "do_sau": "HIGH",
        "so_nghia_vu": 2,
        "nham": "thể tích + quan hệ vuông góc trên cùng một hình",
        "de": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2 và "
            "SA vuông góc với mặt phẳng đáy, SA = 3. Chứng minh đường thẳng "
            "BD vuông góc với mặt phẳng (SAC) và tính thể tích khối chóp "
            "S.ABCD."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) S(0,0,3). "
            "① BD = (-2,2,0); mặt (SAC) có pháp tuyến (1,-1,0) "
            "(xem fp_5) ⇒ BD ∥ pháp tuyến ⇒ BD ⊥ (SAC). "
            "② V = (1/3)·S_đáy·h = (1/3)·4·3 = 4."
        ),
        "dap_so": q(4),
    },
]


# ── NHIỄM CHÉO ─────────────────────────────────────────────────────────────
GOC = Path(__file__).resolve().parents[2]
_POOL = GOC / "docs" / "evaluation" / "geometry" / "holdout"


def _van_ban(s: str) -> str:
    """Chuẩn hoá để so: bỏ dấu câu, gộp khoảng trắng, hạ chữ thường."""
    return re.sub(r"[^\wàáâãèéêìíòóôõùúýăđĩũơưạ-ỹ]+", " ", s.lower()).strip()


def _ngu(s: str, n: int = 8) -> set[str]:
    t = _van_ban(s).split()
    return {" ".join(t[i:i + n]) for i in range(max(len(t) - n + 1, 0))}


#: Mệnh đề HỎI bắt đầu ở đây. Câu trước nó là phần DỰNG HÌNH, và phần ấy là
#: văn mẫu: *"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2"* xuất
#: hiện gần như nguyên văn trong mọi sách. Đo trùng trên nó là đo tiếng Việt
#: của SGK, không đo trùng đề.
_HOI = re.compile(r"\b(tính|chứng minh|xác định|tìm)\b", re.IGNORECASE)


def _cau_hoi(de: str) -> str:
    m = _HOI.search(de)
    return de[m.start():] if m else de


def check_contamination() -> list[str]:
    """Đề nào trùng pool holdout đã niêm phong? Rỗng = sạch.

    ─── VÌ SAO HAI PHÉP, KHÔNG MỘT ────────────────────────────────────────

    Bản đầu so n-gram 8 từ trên CẢ đề và báo 5/6 nhiễm. Đọc ra thì mọi cụm
    trùng đều là câu dẫn: *"có đáy ABCD là hình vuông cạnh"*, *"cạnh bên SA
    vuông góc với mặt phẳng đáy"*. Một guard báo động ở đó thì hoặc ta hạ
    ngưỡng cho qua — và mất luôn khả năng bắt trùng thật — hoặc ta viết lại
    đề bằng tiếng Việt lạ để né guard, tức làm hỏng chính bộ đề.

    Nên hỏi hai câu tách bạch:

      ① **Chép nguyên văn?** — 14 từ liên tiếp giống nhau. Ngưỡng cao vì đây
         là câu hỏi về SAO CHÉP, và hai bài khác nhau không tình cờ trùng 14
         từ.
      ② **Cùng một câu hỏi?** — 8 từ liên tiếp trong MỆNH ĐỀ HỎI. Ngưỡng thấp
         vì đây mới là chỗ định danh một bài: cùng hình, cùng câu hỏi thì
         cùng bài, dù câu dẫn viết khác.

    Báo thừa thì người đọc lại; báo thiếu thì cả lượt đo mất giá trị. Nên khi
    lưỡng lự, phép ② được để nhạy.
    """
    kho_van: set[str] = set()
    kho_hoi: set[str] = set()
    for f in _POOL.glob("*.txt"):
        try:
            van = f.read_text(encoding="utf-8")
        except OSError:
            continue
        kho_van |= _ngu(van, 14)
        for dong in van.splitlines():
            if _HOI.search(dong):
                kho_hoi |= _ngu(_cau_hoi(dong), 8)

    ra = []
    for c in CASES:
        nguyen = _ngu(c["de"], 14) & kho_van
        hoi = _ngu(_cau_hoi(c["de"]), 8) & kho_hoi
        if nguyen:
            ra.append(f"{c['id']}: CHÉP NGUYÊN VĂN — {sorted(nguyen)[0][:70]}")
        if hoi and c["id"] not in DA_PHAN_XU:
            ra.append(f"{c['id']}: TRÙNG CÂU HỎI — {sorted(hoi)[0][:70]}")
    return ra


#: Ca đã được ĐỌC TAY và phán là KHÔNG trùng, kèm lý do kiểm lại được.
#:
#: ─── VÌ SAO CẦN MỘT DANH SÁCH NHƯ THẾ ──────────────────────────────────────
#:
#: Phép ② bắt cả **tên chuyên đề**: mọi bài A09 đều mở đầu bằng *"Tính côsin
#: của góc giữa hai đường thẳng"*, mọi bài A13 bằng *"Xác định thiết diện của
#: hình chóp cắt bởi"*. Hạ ngưỡng để chúng im là vứt luôn khả năng bắt trùng
#: thật; viết lại đề bằng tiếng Việt lạ để né guard là làm hỏng bộ đề.
#:
#: Nên đường thứ ba: guard cứ báo, người ĐỌC ĐỀ POOL rồi phán, và **phán quyết
#: nằm trong repo** — kèm lý do, kiểm lại được, không nằm trong đầu ai. Miễn
#: một ca mà không viết được lý do đối chiếu cụ thể thì đó là đang cho qua.
DA_PHAN_XU: dict[str, str] = {
    "fp_2_lang_tru_goc":
        "pool A09 (PHASE7B_HUMAN_COPY_PACKET:429) là hình LẬP PHƯƠNG với "
        "trung điểm I, hỏi góc (A'D, B'I). fp_2 là LĂNG TRỤ đứng đáy tam "
        "giác vuông, hỏi góc (AB', BC'), không có trung điểm. Trùng đúng "
        "cụm tên chuyên đề.",
    "fp_4_thiet_dien_hoi_tiep":
        "pool A13 (…:307) đáy HÌNH THANG, mặt cắt (PAB) với P trên SD, và "
        "chỉ hỏi thiết diện. fp_4 đáy HÌNH VUÔNG, mặt qua trung điểm SC, và "
        "có câu ĐO nối tiếp (khoảng cách từ S). Trùng đúng cụm tên chuyên đề.",
}


if __name__ == "__main__":
    v = check_contamination()
    print(f"6 đề · pool {_POOL}")
    print("SẠCH — không trùng pool holdout" if not v else "⚠️ NHIỄM CHÉO:")
    for x in v:
        print(f"  · {x}")
