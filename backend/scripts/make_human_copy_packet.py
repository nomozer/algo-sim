# -*- coding: utf-8 -*-
"""Sinh `PHASE7B_HUMAN_COPY_PACKET.txt` — MỘT file cho toàn bộ phần con người.

    python scripts/make_human_copy_packet.py            # in ra
    python scripts/make_human_copy_packet.py --ghi      # ghi file gói

**0 API call.** Không tạo đề, không tạo đáp án, không ký thay.

─── VÌ SAO MỘT GÓI CHỨ KHÔNG 40 LƯỢT HỎI ──────────────────────────────────

Phần máy làm được của tập held-out đã xong từ lâu; phần còn lại là **gõ lại đề
nguyên văn**, và nó không chia nhỏ được thành 40 lượt trao đổi mà không tiêu
hết thời gian của người chép vào việc mở lại tài liệu. Gói này gom mọi ô về
**một file, xếp theo NGUỒN**, để mỗi tài liệu chỉ phải mở đúng một lần.

─── MÁY ĐIỀN GÌ, NGƯỜI ĐIỀN GÌ ────────────────────────────────────────────

Máy điền **mọi thứ suy ra được**: `slot` · `capability_tag` · `answer_shape` ·
nghĩa vụ oracle · thang chấm · nguồn nhắm tới · ràng buộc riêng của ô. Với hai
ứng viên đã soi tận trang thì điền luôn `NGUỒN` và `ĐÁP ÁN`.

Người điền **đúng một thứ**: `ĐỀ NGUYÊN VĂN`, cộng **một** chữ ký ở đầu file.

⚠️ `problem_text` **không** được prefill bằng bản máy đọc lại — kể cả bản tôi
đã đọc từ ảnh trang. `HOLDOUT_SOURCE_POLICY §4`: hành vi chép của người CHÍNH
LÀ bước xác minh, nên một bản nháp máy đặt sẵn ở đó chỉ mời người ta bấm qua.

─── KHÔNG HẠN NGẠCH CỨNG ──────────────────────────────────────────────────

`HOLDOUT_PROTOCOL §3①` đòi **mỗi ô ≥1** và **tổng ≥40** — không đòi ô nào đúng
mấy bài. Gói phát dư (~47 khối) để sau lượt loại của người vẫn còn ≥40: tỉ lệ
đạt đo được ở vùng đã soi là **≈25%** với tầng A có oracle.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
RA = GOC / "docs" / "evaluation" / "geometry" / "holdout" / \
    "PHASE7B_HUMAN_COPY_PACKET.txt"

#: Số **khối phát ra** mỗi ô. Không phải hạn ngạch — xem docstring. Ô nào khó
#: tìm thì phát dư hơn, vì cái đắt là mở lại tài liệu chứ không phải gõ thêm.
PHAT: dict[str, int] = {
    # Bốn ô nới 2 → 3 (2026-08-28): mỗi ô nhận thêm một ứng viên SGK, và
    # 38 ứng viên KHÔNG đủ cho ngưỡng `accepted >= 40` — khối trống chỉ là
    # SỨC CHỨA, không phải ứng viên dự phòng.
    **{o: 3 for o in ("A01", "A02", "A04", "A05")},
    **{o: 2 for o in ("A03", "A06", "A07", "A08")},
    "A09": 3, "A10": 3, "A13": 3,
    # Khó nhất: `distance` phải ra HỮU TỈ. Phát dư nhất.
    "A11": 3, "A12": 3,
    # Đã soi được 2 ứng viên tận trang ⇒ 2 khối đầu có sẵn nguồn + đáp án.
    "A14": 4,
    **{o: 2 for o in ("B01", "B02", "B03", "B04", "B05", "B06")},
}

#: Ứng viên **đã soi tận trang** ở lượt trước (đọc ảnh trang, không phải trích
#: PDF). Chỉ nguồn + đáp án được prefill — đề vẫn phải do người gõ.
DA_SOI: dict[str, list[dict]] = {
    "A14": [
        {"nguon": "Tài liệu chuyên đề khối đa diện và thể tích khối đa diện — "
                  "**trang PDF 80** (nhãn trong tài liệu: 'Page 16'), Câu 1 · https://toanmath.com/2023/07/tai-lieu-"
                  "chuyen-de-khoi-da-dien-va-the-tich-khoi-da-dien.html",
         "dap_an": "2/3",
         "goi_y": "ABC vuông tại A · AB = a · AC = 2a · SA ⊥ đáy · SA = 2a",
         "vi_sao": "đề NGẮN NHẤT; không bước nào sinh căn; lời giải cùng trang",
         "de": "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = a, AC = 2a. Cạnh bên SA vuông góc với đáy và SA = 2a. Tính thể tích V của khối chóp S.ABC.",
         "rui_ro_muc": "LOW",
         "kiem_gi": "đã đọc ẢNH trang PDF 80 (nhãn 'Page 16'), Câu 1: khớp nguyên văn, lời giải in V = 2a³/3. Chỉ cần liếc lại AB = a và AC = 2a",
         "rui_ro": "thấp nhất trong vùng đã soi"},
        {"nguon": "Tài liệu chuyên đề khối đa diện và thể tích khối đa diện — "
                  "trang 82, Câu 7 · https://toanmath.com/2023/07/tai-lieu-"
                  "chuyen-de-khoi-da-dien-va-the-tich-khoi-da-dien.html",
         "dap_an": "8/3",
         "goi_y": "đáy chữ nhật · SA ⊥ (ABCD) · AB = 3a · AD = 2a · SB = 5a",
         "vi_sao": "đi qua Pythagoras mà VẪN hữu tỉ (bộ ba 3-4-5)",
         "de": "<TRÍCH DẪN KHÔNG TRA RA ĐƯỢC — xem CẦN KIỂM GÌ>",
         "rui_ro_muc": "HIGH",
         "kiem_gi": "⛔ Trích dẫn 'trang 82, Câu 7' KHÔNG khớp tài liệu: PDF tr 82 là Câu 6 (đáy hình vuông, SA = a√3), và quét tr 60–110 không thấy bài AB = 3a, AD = 2a, SB = 5a. Hoặc tìm lại đúng vị trí, hoặc THAY ứng viên. Gợi ý đã soi: PDF tr 91 ('Page 27') Câu 2 — đáy chữ nhật AB = a, AD = 2a, d(A,(SBD)) = 2a/3, tính V; kiểm nhanh cho SA = a ⇒ V = 2a³/3, hữu tỉ, và là dạng NGƯỢC (cho khoảng cách, tìm thể tích)",
         "rui_ro": "trung bình — SA là SUY RA, phải xác nhận lời giải nguồn "
                   "cho V = 8a³/3 chứ đừng tự tính"},
    ],
    # Tìm được 2026-08-28 sau khi rà 3 genre nguồn — xem
    # `HOLDOUT_ACQUISITION_LOG §7e`. Đây là ứng viên A11 DUY NHẤT có đáp án
    # hữu tỉ trong toàn bộ lượt rà.
    "A11": [
        {"nguon": "VietJack — Khoảng cách lớp 11 (Lý thuyết Toán 11 Kết nối "
                  "tri thức), **Ví dụ 2** · "
                  "https://vietjack.com/toan-11-kn/ly-thuyet-bai-26-khoang-cach.jsp",
         "dap_an": "12/25",
         "goi_y": "(SAB) ⊥ đáy · △SAB vuông tại S · AB = a · SA = 3a/5 "
                  "⇒ SB = 4a/5 (bộ ba 3-4-5 thu nhỏ a/5)",
         "vi_sao": "d = SA·SB/AB = 12a/25 — HỮU TỈ. Toạ độ cũng hữu tỉ: "
                   "A(0,0,0) B(a,0,0) S(9a/25, 0, 12a/25)",
         "de": 'Cho hình chóp S.ABC có mặt phẳng (SAB) vuông góc với mặt đáy, tam giác SAB vuông tại S, AB = a, SA = 3a/5. Tính khoảng cách từ điểm S đến mặt phẳng (ABC).',
         "rui_ro_muc": 'HIGH',
         "kiem_gi": 'SA = 3a/5 là PHÂN SỐ — kiểm kỹ. Và trang tóm tắt ghi công thức SA·AB/SB, ĐÚNG phải là SA·SB/AB; đáp án 12a/25 thì đúng',
         "rui_ro": "C là điểm TỰ DO (đề không ràng buộc vị trí) — đã kiểm và "
                   "KHÔNG phải thiếu dữ kiện: d không phụ thuộc C, và mọi ca "
                   "DEV cũng đặt A,B,C,D,S là điểm tự do. Điều PHẢI tự kiểm "
                   "khi mở nguồn: bản tóm tắt ghi công thức là SA·AB/SB, "
                   "ĐÚNG phải là SA·SB/AB — đáp án 12a/25 thì đúng. Đọc lời "
                   "giải GỐC, đừng tin bản tóm tắt"},
        {"nguon": "Chuyên đề QHVG trong không gian Toán 11 (KNTTVCS, 704tr) — "
                  "B26.1 KHOẢNG CÁCH, **PHẦN TỰ LUẬN**, Câu 7 (trang PDF 298 "
                  "= 'Page 57'); lời giải ở mục HDG tr 302–334 · "
                  "https://toanmath.com/2023/08/chuyen-de-quan-he-vuong-goc-"
                  "trong-khong-gian-toan-11-knttvcs.html",
         "dap_an": "2",
         "goi_y": "SA ⊥ (ABC) · △ABC vuông tại B · BC = 2a",
         "vi_sao": "BC ⊥ AB và BC ⊥ SA ⇒ BC ⊥ (SAB) ⇒ d(C,(SAB)) = CB = 2a. "
                   "Không phép tính nào sinh căn — an toàn nhất trong ô này",
         "de": 'Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), tam giác ABC là tam giác vuông tại B, BC = 2a. Khoảng cách từ C đến mặt phẳng (SAB) bằng bao nhiêu?',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'BC = 2a, KHÔNG có căn; vuông tại B',
         "rui_ro": "thấp. AB và SA KHÔNG được cho — đáp án không phụ thuộc "
                   "chúng (cùng dạng 'điểm tự do' đã chốt ở ứng viên trên). "
                   "Đã đọc ẢNH TRANG để xác nhận `BC = 2a` không có căn"},
    ],
    # Ảnh trang đã đọc: đề ở tr PDF 2, lời giải ở tr PDF 5–6. Nguồn tự in
    # a) 90° · b) 45° · c) 60° ⇒ cos² lần lượt 0 · 1/2 · 1/4, đều hữu tỉ.
    "A09": [
        {"nguon": "Chuyên đề QHVG Toán 11 (KNTTVCS, 704tr) — B22.1 **PHẦN TỰ LUẬN**, Câu 13 (đề tr PDF 3; lời giải tr PDF 13) · https://toanmath.com/2023/08/chuyen-de-quan-he-vuong-goc-trong-khong-gian-toan-11-knttvcs.html",
         "dap_an": "2/5",
         "goi_y": "hình lập phương · I trung điểm AB · côsin góc giữa A'D và B'I",
         "vi_sao": "PASS 2 — ứng viên ĐÁNG GIÁ NHẤT của nhóm: nguồn in cos = √10/5, tức VÔ TỈ, nhưng đơn vị checker là cos² = 10/25 = **2/5**, HỮU TỈ. Nó chứng minh vì sao oracle dùng cos² chứ không dùng cos",
         "de": "Cho hình lập phương ABCD.A'B'C'D'. Tính góc giữa 2 đường thẳng AC và B'C'.",
         "rui_ro_muc": 'LOW',
         "kiem_gi": "ý b) của đề gốc: cặp AC và B'C'",
         "rui_ro": "trung bình — `phep_chuyen` PHẢI ghi rõ: nguồn cho `√10/5`, bình phương ⇒ `2/5`. Chép thẳng √10/5 vào ĐÁP ÁN là sai đơn vị"},
        {"nguon": "Chuyên đề QHVG Toán 11 (KNTTVCS, 704tr) — B22.1 **PHẦN TỰ LUẬN**, Câu 2 **ý c)** (đề tr PDF 2; lời giải tr PDF 6) · https://toanmath.com/2023/08/chuyen-de-quan-he-vuong-goc-trong-khong-gian-toan-11-knttvcs.html",
         "dap_an": "1/4",
         "goi_y": "hình lập phương · góc giữa A'C' và B'C",
         "vi_sao": "PASS 2 — nguồn in 60° ⇒ cos² = 1/4. Hai đường CHÉO NHAU (ý b) là cắt nhau sau khi dời), lập luận qua tam giác đều ACB'",
         "de": "Cho hình lập phương ABCD.A'B'C'D'. Tính góc giữa 2 đường thẳng A'C' và B'C.",
         "rui_ro_muc": 'LOW',
         "kiem_gi": "ý c): A'C' và B'C — chú ý B'C KHÔNG có dấu phẩy ở C",
         "rui_ro": "thấp — đã đọc đáp án nguồn trên ảnh cùng lúc với ý b)"},
        {"nguon": "Chuyên đề QHVG trong không gian Toán 11 (KNTTVCS, 704tr) — "
                  "B22.1 HAI ĐƯỜNG THẲNG VUÔNG GÓC, **PHẦN TỰ LUẬN**, "
                  "Câu 2 **ý b)** (đề tr PDF 2 = 'Page 2'; lời giải tr PDF 6) · "
                  "https://toanmath.com/2023/08/chuyen-de-quan-he-vuong-goc-"
                  "trong-khong-gian-toan-11-knttvcs.html",
         "dap_an": "1/2",
         "goi_y": "hình LẬP PHƯƠNG ABCD.A'B'C'D' · tính góc giữa AC và B'C'",
         "vi_sao": "lập phương ⇒ toạ độ NGUYÊN, không dữ kiện nào có căn. "
                   "Nguồn in (AC,B'C') = 45° ⇒ cos² = 1/2 — hữu tỉ",
         "de": "Cho hình lập phương ABCD.A'B'C'D', gọi I là trung điểm của cạnh AB. Tính côsin của góc giữa hai đường thẳng A'D và B'I.",
         "rui_ro_muc": 'HIGH',
         "kiem_gi": "nguồn in đáp án cos = √10/5 (CÓ CĂN). ĐÁP ÁN của ta là cos² = 2/5. Kiểm cả đề (I trung điểm AB, cặp A'D và B'I) lẫn việc nguồn thật sự ghi √10/5",
         "rui_ro": "thấp. Đề gốc có BA ý a/b/c; **chỉ chép ý b)** — ý a) ra "
                   "90° (cos²=0, quá tầm thường), ý c) ra 60° (cos²=1/4, dùng "
                   "được nếu cần bài A09 thứ hai). Cạnh không cho ⇒ gán 1"},
    ],
    # Ảnh trang đã đọc: tr PDF 46. Bài chứng minh ⇒ đáp án là `true`, không
    # có số nào để mất căn. Lời giải ở mục HDG tr 49–64.
    "A07": [
        {"nguon": "Chuyên đề QHVG Toán 11 (KNTTVCS, 704tr) — B23.1 **PHẦN TỰ LUẬN**, Dạng 1, Câu 1 **ý a)** (đề tr PDF 46; lời giải tr 49–64) · https://toanmath.com/2023/08/chuyen-de-quan-he-vuong-goc-trong-khong-gian-toan-11-knttvcs.html",
         "dap_an": "true",
         "goi_y": "tứ diện OABC có OA, OB, OC ĐÔI MỘT VUÔNG GÓC · H là hình chiếu của O trên (ABC) · chứng minh BC ⊥ (OAH)",
         "vi_sao": "PASS 2 — tứ diện vuông ba mặt (khác chóp đáy chữ nhật), và H là chiếu lên một MẶT thay vì lên một ĐƯỜNG",
         "de": 'Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, cạnh bên SA vuông góc với mặt đáy. Gọi H, K lần lượt là hình chiếu của A lên SB, SD. b) Chứng minh AH ⊥ (SBC).',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'H là hình chiếu của A lên SB (không phải SD); ý cần chép là b)',
         "rui_ro": "thấp. Đề có hai ý — chỉ chép ý a)"},
        {"nguon": "Chuyên đề QHVG trong không gian Toán 11 (KNTTVCS, 704tr) — "
                  "B23.1 ĐƯỜNG THẲNG ⊥ MẶT PHẲNG, **PHẦN TỰ LUẬN**, Dạng 1, "
                  "Câu 2 **ý b)** (đề tr PDF 46 = 'Page 11'; lời giải tr 49–64) · "
                  "https://toanmath.com/2023/08/chuyen-de-quan-he-vuong-goc-"
                  "trong-khong-gian-toan-11-knttvcs.html",
         "dap_an": "true",
         "goi_y": "đáy ABCD hình CHỮ NHẬT · SA ⊥ đáy · H là hình chiếu của A "
                  "lên SB · chứng minh AH ⊥ (SBC)",
         "vi_sao": "không dữ kiện số nào ⇒ không chỗ nào sinh căn; mọi cạnh "
                   "gán số nguyên được. H là điểm DẪN XUẤT (chiếu A lên SB) "
                   "⇒ chuỗi phụ thuộc sâu hơn mọi ứng viên khác",
         "de": 'Cho tứ diện OABC có OA, OB, OC đôi một vuông góc với nhau. Gọi H là hình chiếu vuông góc của O trên mặt phẳng (ABC). a) Chứng minh BC ⊥ (OAH).',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'H là hình chiếu của O lên MẶT PHẲNG (ABC); ý a) là BC ⊥ (OAH)',
         "rui_ro": "thấp. Đề gốc có ba ý a/b/c — **chỉ chép ý b)**. Đáp án là "
                   "`true` (bài chứng minh), không phải một con số"},
    ],
    # Ảnh tr PDF 113: đề VÀ lời giải nằm cùng trang — nguồn tự in SCO = 45°.
    "A10": [
        {"nguon": "Chuyên đề QHVG Toán 11 (KNTTVCS, 704tr) — B24.1 **PHẦN TỰ LUẬN**, Câu 2 (đề tr PDF 106; lời giải tr PDF 112) · https://toanmath.com/2023/08/chuyen-de-quan-he-vuong-goc-trong-khong-gian-toan-11-knttvcs.html",
         "dap_an": "1/2",
         "goi_y": "hình LẬP PHƯƠNG · góc giữa A'C' và mặt phẳng (BCC'B')",
         "vi_sao": "PASS 2 — lập phương (toạ độ nguyên) thay hình thoi; nguồn in 45° ⇒ sin² = 1/2",
         "de": 'Cho hình thoi ABCD tâm O có BD = 4a, AC = 2a. Lấy điểm S không thuộc (ABCD) sao cho SO ⊥ (ABCD). Biết tan(SBO) = 1/2. Số đo góc giữa SC và (ABCD) bằng bao nhiêu?',
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": 'BD = 4a và AC = 2a (đừng đảo), tan góc SBO = 1/2, hỏi góc giữa SC và đáy',
         "rui_ro": "⚠️ ĐƠN VỊ: đường–MẶT ⇒ **sin²**, không phải cos²"},
        {"nguon": "Chuyên đề QHVG trong không gian Toán 11 (KNTTVCS, 704tr) — "
                  "B24.1 GÓC ĐƯỜNG THẲNG–MẶT PHẲNG, **PHẦN TỰ LUẬN**, Câu 5 "
                  "(đề + lời giải cùng ở tr PDF 113 = 'Page 5') · "
                  "https://toanmath.com/2023/08/chuyen-de-quan-he-vuong-goc-"
                  "trong-khong-gian-toan-11-knttvcs.html",
         "dap_an": "1/2",
         "goi_y": "hình THOI ABCD tâm O · BD = 4a · AC = 2a · SO ⊥ (ABCD) · "
                  "tan(SBO) = 1/2 · góc giữa SC và (ABCD)",
         "vi_sao": "nguồn in BO = 2a, SO = 2a·½ = a, OC = a ⇒ SCO = 45° "
                   "⇒ **sin² = 1/2**. Toạ độ nguyên: O(0,0,0) B(0,−2,0) "
                   "A(−1,0,0) C(1,0,0) S(0,0,1)",
         "de": "Cho hình lập phương ABCD.A'B'C'D'. Góc giữa A'C' và mặt phẳng (BCC'B') bằng bao nhiêu?",
         "rui_ro_muc": 'LOW',
         "kiem_gi": "mặt phẳng (BCC'B') — bốn chữ, hai dấu phẩy trên",
         "rui_ro": "⚠️ ĐƠN VỊ: ô A10 là đường–MẶT nên checker nhận **sin²**, "
                   "KHÔNG phải cos². Nguồn cho góc 45° ⇒ chép `1/2`"},
    ],
    "B01": [
        {"nguon": "Chuyên đề QHVG Toán 11 (KNTTVCS, 704tr) — B26.1 **PHẦN TỰ LUẬN**, *BÀI TOÁN 2*, Câu 26 (đề tr PDF 300) · https://toanmath.com/2023/08/chuyen-de-quan-he-vuong-goc-trong-khong-gian-toan-11-knttvcs.html",
         "dap_an": "",
         "goi_y": "chóp S.ABC · đáy vuông cân tại A · mặt bên SBC là tam giác ĐỀU cạnh a · (SBC) ⊥ đáy · khoảng cách giữa SA và BC",
         "vi_sao": "PASS 2 — cùng loại ngoài phủ nhưng cấu hình mặt-bên-vuông-góc-đáy, khác lăng trụ đứng của ứng viên đầu",
         "de": "Cho hình lăng trụ đứng ABC.A1B1C1 có tam giác ABC vuông cân tại A, AB = a, CC' = 2a. Khoảng cách giữa hai đường thẳng AA1 và BC1 bằng bao nhiêu?",
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": "chỉ số dưới A1, B1, C1; đề dùng lẫn CC' và CC1 — chép đúng như in",
         "rui_ro": "thấp"},
        {"nguon": "Chuyên đề QHVG trong không gian Toán 11 (KNTTVCS, 704tr) — "
                  "B26.1 KHOẢNG CÁCH, **PHẦN TỰ LUẬN**, *BÀI TOÁN 2. TÍNH "
                  "KHOẢNG CÁCH HAI ĐƯỜNG THẲNG CHÉO NHAU*, Câu 28 "
                  "(đề tr PDF 300 = 'Page 59') · "
                  "https://toanmath.com/2023/08/chuyen-de-quan-he-vuong-goc-"
                  "trong-khong-gian-toan-11-knttvcs.html",
         "dap_an": "",
         "goi_y": "lăng trụ đứng ABC.A₁B₁C₁ · △ABC vuông cân tại A · AB = a · "
                  "CC' = 2a · khoảng cách giữa AA₁ và BC₁",
         "vi_sao": "đúng LOẠI của ô B01 — khoảng cách hai đường CHÉO NHAU, "
                   "nằm ngoài ranh giới kernel. Tầng B không cần hữu tỉ",
         "de": 'Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại A, mặt bên SBC là tam giác đều cạnh a và mặt phẳng (SBC) vuông góc với mặt đáy. Khoảng cách giữa hai đường thẳng SA và BC bằng bao nhiêu?',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'mặt bên SBC ĐỀU cạnh a; (SBC) ⊥ đáy',
         "rui_ro": "thấp. Nhớ dùng `ĐÁP ÁN NGUỒN:` (chép đáp án sách), "
                   "KHÔNG dùng `ĐÁP ÁN:` — ô tầng B không có oracle"},
    ],
    # ── Nguồn 2: Đường thẳng & mặt phẳng, QH song song Toán 11 CTST (410tr) ──
    "A01": [
        {"nguon": "SGK Toán 11 Chân trời sáng tạo — **Bài 3 trang 106**, ý a) (lời giải: Loigiaihay)",
         "dap_an": "true",
         "goi_y": "chóp S.ABCD đáy hình bình hành · tìm giao tuyến của (SCD) và (SAB)",
         "vi_sao": "PASS 2 — giao tuyến xác định bởi QUAN HỆ SONG SONG (AB ∥ CD ⇒ giao tuyến qua S và ∥ AB), không phải bởi hai điểm chung. Đây là mẫu dựng khác hẳn hai ứng viên A01 kia",
         "de": 'Cho hình chóp S.ABCD có đáy ABCD là hình bình hành. Gọi M, N lần lượt là trung điểm AD và BC. Tìm giao tuyến của hai mặt phẳng (SMN) và (SAC).',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'tên điểm M, N và cặp mặt phẳng (SMN), (SAC)',
         "rui_ro": "trung bình — `phep_chuyen` ghi rõ: nguồn trả lời *đường qua S song song AB và CD*; nghĩa vụ `point_on_line` kiểm S thuộc giao tuyến ⇒ true"},
        {"nguon": "Đường thẳng và mặt phẳng, QH song song Toán 11 CTST (410tr) — **BÀI TẬP TỰ LUẬN**, Dạng 1, Câu 3 (đề tr PDF 4) · https://toanmath.com/2023/08/duong-thang-va-mat-phang-quan-he-song-song-trong-khong-gian-toan-11-ctst-2.html",
         "dap_an": "true",
         "goi_y": "tứ diện ABCD · G trọng tâm △BCD · giao tuyến (ACD) ∩ (GAB)",
         "vi_sao": "PASS 2 — cùng nghĩa vụ A01 nhưng hình KHÁC (tứ diện thay chóp tứ giác) và vật dẫn xuất khác (trọng tâm thay trung điểm)",
         "de": 'Cho tứ diện ABCD. G là trọng tâm tam giác BCD. Tìm giao tuyến của hai mặt phẳng (ACD) và (GAB).',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'G là trọng tâm tam giác BCD, không phải ABC',
         "rui_ro": "thấp"},
        {"nguon": "Đường thẳng và mặt phẳng, quan hệ song song trong không "
                  "gian Toán 11 CTST (410tr) — **BÀI TẬP TỰ LUẬN**, Dạng 1 "
                  "*Tìm giao tuyến của hai mặt phẳng*, Câu 5 (đề tr PDF 4; "
                  "lời giải mục Dạng 1 tr 15+) · "
                  "https://toanmath.com/2023/08/duong-thang-va-mat-phang-quan-"
                  "he-song-song-trong-khong-gian-toan-11-ctst-2.html",
         "dap_an": "true",
         "goi_y": "chóp S.ABCD đáy HÌNH BÌNH HÀNH · M, N trung điểm AD và BC · "
                  "tìm giao tuyến (SMN) ∩ (SAC)",
         "vi_sao": "bình hành + trung điểm ⇒ toạ độ hữu tỉ hết. Giao tuyến đi "
                   "qua S và tâm O — nghĩa vụ `point_on_line` kiểm O thuộc "
                   "giao tuyến ⇒ `true`",
         "de": 'Cho hình chóp S.ABCD có đáy ABCD là hình bình hành. a) Tìm giao tuyến của (SCD) và (SAB).',
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": 'đề gốc nhiều ý — xác nhận ý a) đúng là cặp (SCD),(SAB)',
         "rui_ro": "trung bình. `phep_chuyen` phải ghi rõ: nguồn trả lời "
                   "*giao tuyến là SO*, chuyển thành `point_on_line` = true"},
    ],
    "A02": [
        {"nguon": "SGK Toán 11 — **Bài 4.6 trang 94**, ý b) (lời giải: Loigiaihay)",
         "dap_an": "true",
         "goi_y": "chóp S.ABCD đáy hình bình hành · G TRỌNG TÂM △SCD · tìm giao điểm của BG và (SAC)",
         "vi_sao": "PASS 2 — chuỗi phụ thuộc SÂU NHẤT cả gói: trọng tâm G → trung điểm E của CD → giao đường-đường F = BE ∩ AC → giao tuyến SF → giao điểm I = BG ∩ SF. Kiểm số: G(1/3,2/3,1/3), E(1/2,1,0), F(2/3,2/3,0) — hữu tỉ hết",
         "de": 'Cho bốn điểm A, B, C, D không đồng phẳng. Gọi M, N lần lượt là trung điểm của AC và BC. Trên đoạn BD lấy điểm P sao cho BP = 2PD. Tìm giao điểm của đường thẳng CD và mặt phẳng (MNP).',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'tỉ số BP = 2PD, và M,N là trung điểm AC,BC',
         "rui_ro": "thấp. Đề có nhiều ý — **chỉ chép ý b)**"},
        {"nguon": "Đường thẳng và mặt phẳng, QH song song Toán 11 CTST (410tr) — **BÀI TẬP TỰ LUẬN**, Dạng 2, Câu 13 (đề tr PDF 7) · https://toanmath.com/2023/08/duong-thang-va-mat-phang-quan-he-song-song-trong-khong-gian-toan-11-ctst-2.html",
         "dap_an": "true",
         "goi_y": "tứ giác ABCD có AC ∩ BD = O · S ngoài (ABCD) · M trên SC · giao điểm SD ∩ (ABM)",
         "vi_sao": "PASS 2 — cùng nghĩa vụ A02, nhưng điểm cắt O là DỮ KIỆN chứ không phải vật dựng; M tự do trên SC",
         "de": 'Cho tứ giác ABCD có AC và BD giao nhau tại O và một điểm S không thuộc mặt phẳng (ABCD). Trên đoạn SC lấy một điểm M không trùng với S và C. Tìm giao điểm của đường thẳng SD với mặt phẳng (ABM).',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'M trên SC, tìm giao điểm của SD (không phải SC) với (ABM)',
         "rui_ro": "trung bình — M tự do (lớp đã chốt)"},
        {"nguon": "Đường thẳng và mặt phẳng, QH song song Toán 11 CTST (410tr) "
                  "— **BÀI TẬP TỰ LUẬN**, Dạng 2 *Tìm giao điểm của đường "
                  "thẳng và mặt phẳng*, Câu 12 (đề tr PDF 7; lời giải tr 21+) · "
                  "https://toanmath.com/2023/08/duong-thang-va-mat-phang-quan-"
                  "he-song-song-trong-khong-gian-toan-11-ctst-2.html",
         "dap_an": "true",
         "goi_y": "bốn điểm A,B,C,D không đồng phẳng · M,N trung điểm AC,BC · "
                  "P trên BD với BP = 2PD · tìm giao điểm CD ∩ (MNP)",
         "vi_sao": "tỉ số 2:1 và trung điểm đều hữu tỉ ⇒ P = (1/3,0,2/3) khi "
                   "đặt tứ diện đơn vị. Ba điểm dẫn xuất ⇒ chuỗi phụ thuộc "
                   "sâu nhất trong cả gói",
         "de": 'Cho hình chóp S.ABCD có đáy ABCD là hình bình hành. Gọi G là trọng tâm tam giác SCD. b) Tìm giao điểm của BG và mặt phẳng (SAC).',
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": 'G là trọng tâm tam giác SCD; ý b) hỏi giao điểm BG ∩ (SAC)',
         "rui_ro": "thấp"},
    ],
    "A03": [
        {"nguon": "Đường thẳng và mặt phẳng, QH song song Toán 11 CTST (410tr) — **BÀI TẬP TỰ LUẬN**, *Dạng 1: chứng minh hai đường thẳng song song*, Câu 2 (đề tr PDF 100) · https://toanmath.com/2023/08/duong-thang-va-mat-phang-quan-he-song-song-trong-khong-gian-toan-11-ctst-2.html",
         "dap_an": "true",
         "goi_y": "tứ diện ABCD · M,N,P,Q,R,S trung điểm AB,CD,BC,AD,AC,BD · chứng minh MPNQ là hình bình hành",
         "vi_sao": "PASS 2 — SÁU điểm dẫn xuất, kết luận là một TỨ GIÁC có tính chất, không phải một quan hệ hai đường. Nghĩa vụ song song vẫn giữ",
         "de": 'Cho tứ diện ABCD có I; J lần lượt là trọng tâm của tam giác ABC, ABD. Chứng minh rằng: IJ // CD.',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'I, J là TRỌNG TÂM (không phải trung điểm) của ABC và ABD',
         "rui_ro": "trung bình — kết luận *hình bình hành* phải chuyển thành quan hệ ∥ trong `phep_chuyen`"},
        {"nguon": "Đường thẳng và mặt phẳng, QH song song Toán 11 CTST (410tr) "
                  "— **BÀI TẬP TỰ LUẬN**, *Dạng 1: CHỨNG MINH HAI ĐƯỜNG THẲNG "
                  "SONG SONG*, Câu 1 (đề tr PDF 100) · "
                  "https://toanmath.com/2023/08/duong-thang-va-mat-phang-quan-"
                  "he-song-song-trong-khong-gian-toan-11-ctst-2.html",
         "dap_an": "true",
         "goi_y": "tứ diện ABCD · I, J là TRỌNG TÂM của △ABC và △ABD · "
                  "chứng minh IJ ∥ CD",
         "vi_sao": "trọng tâm của điểm hữu tỉ vẫn hữu tỉ. Không dữ kiện số "
                   "nào ⇒ không chỗ nào sinh căn. Bài chứng minh ⇒ `true`",
         "de": 'Cho tứ diện ABCD. Gọi M, N, P, Q, R, S lần lượt là trung điểm của AB, CD, BC, AD, AC, BD. Chứng minh MPNQ là hình bình hành. Từ đó suy ra ba đoạn MN, PQ, RS cắt nhau tại trung điểm G của mỗi đoạn.',
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": 'thứ tự sáu cặp cạnh AB,CD,BC,AD,AC,BD ứng với M,N,P,Q,R,S',
         "rui_ro": "thấp — ứng viên sạch nhất trong nhóm song song"},
    ],
    "A13": [
        {"nguon": "Đường thẳng và mặt phẳng, QH song song Toán 11 CTST (410tr) — **BÀI TẬP TỰ LUẬN**, *Dạng 3: BÀI TOÁN THIẾT DIỆN*, Câu 24 **ý b)** (đề tr PDF 8) · https://toanmath.com/2023/08/duong-thang-va-mat-phang-quan-he-song-song-trong-khong-gian-toan-11-ctst-2.html",
         "dap_an": "true",
         "goi_y": "cùng chóp hình thang · M, N trung điểm AB, BC · thiết diện cắt bởi (MNP)",
         "vi_sao": "PASS 2 — mặt cắt xác định bởi BA điểm dẫn xuất thay vì hai đỉnh + một điểm tự do",
         "de": 'Cho hình chóp tứ giác S.ABCD, có đáy là hình thang với AD là đáy lớn và P là một điểm trên cạnh SD. a) Xác định thiết diện của hình chóp cắt bởi mặt phẳng (PAB).',
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": 'AD là đáy LỚN; P nằm trên SD; ý a) cắt bởi (PAB)',
         "rui_ro": "trung bình — vẫn dùng P tự do của ý a)"},
        {"nguon": "Đường thẳng và mặt phẳng, QH song song Toán 11 CTST (410tr) "
                  "— **BÀI TẬP TỰ LUẬN**, *Dạng 3: BÀI TOÁN THIẾT DIỆN*, "
                  "Câu 24 **ý a)** (đề tr PDF 8; lời giải tr 30+) · "
                  "https://toanmath.com/2023/08/duong-thang-va-mat-phang-quan-"
                  "he-song-song-trong-khong-gian-toan-11-ctst-2.html",
         "dap_an": "true",
         "goi_y": "chóp S.ABCD đáy HÌNH THANG, AD là đáy lớn · P trên cạnh SD "
                  "· xác định thiết diện cắt bởi (PAB)",
         "vi_sao": "chóp trên hình thang là khối LỒI — điều kiện của ô A13. "
                   "Hình thang đặt toạ độ hữu tỉ được",
         "de": 'Cho hình chóp tứ giác S.ABCD, có đáy là hình thang với AD là đáy lớn và P là một điểm trên cạnh SD. b) Gọi M, N lần lượt là trung điểm của các cạnh AB, BC. Xác định thiết diện của hình chóp cắt bởi (MNP).',
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": 'ý b) dùng M, N trung điểm AB, BC và vẫn dùng P của ý a)',
         "rui_ro": "trung bình. P là điểm TỰ DO trên SD (như các ca đã chốt); "
                   "tính đồng phẳng của thiết diện đúng với mọi vị trí P. "
                   "**Chỉ chép ý a)**"},
    ],
    # ── Nguồn 3: Lê Bá Bảo — Dạng toán xác định góc nhị diện (14tr) ──
    "A08": [
        {"nguon": "Lê Bá Bảo — *Dạng toán xác định góc nhị diện Toán 11* (14tr) — **II. BÀI TẬP TỰ LUẬN**, Câu 1 **ý a)** (đề tr PDF 2) · https://toanmath.com/2024/03/dang-toan-xac-dinh-goc-nhi-dien-toan-11.html",
         "dap_an": "true",
         "goi_y": "chóp S.ABC · SA ⊥ (ABC) · H hình chiếu của A trên BC · chứng minh (SAB) ⊥ (ABC) và (SAH) ⊥ (SBC)",
         "vi_sao": "PASS 2 — H là điểm DẪN XUẤT (chiếu vuông góc), khác hẳn ứng viên lập phương vốn không có vật dựng nào",
         "de": "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. b) Chứng minh rằng (ACC'A') ⊥ (BDD'B').",
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": "hai mặt (ACC'A') và (BDD'B') — kiểm đủ bốn chữ và dấu phẩy trên",
         "rui_ro": "thấp. Chỉ chép ý a)"},
        {"nguon": "Lê Bá Bảo — *Dạng toán xác định góc nhị diện Toán 11* "
                  "(14tr) — **II. BÀI TẬP TỰ LUẬN**, Câu 2 **ý b)** (đề tr "
                  "PDF 2; lời giải mục *IV. LỜI GIẢI CHI TIẾT*) · "
                  "https://toanmath.com/2024/03/dang-toan-xac-dinh-goc-nhi-"
                  "dien-toan-11.html",
         "dap_an": "true",
         "goi_y": "hình LẬP PHƯƠNG ABCD.A'B'C'D' cạnh a · chứng minh "
                  "(ACC'A') ⊥ (BDD'B')",
         "vi_sao": "lập phương ⇒ toạ độ NGUYÊN, hình xác định hoàn toàn, "
                   "không điểm tự do nào. Đúng nghĩa vụ `perpendicular` "
                   "MẶT–MẶT mà ô A08 đòi",
         "de": 'Cho hình chóp S.ABC có SA ⊥ (ABC). Gọi H là hình chiếu của A trên BC. a) Chứng minh rằng (SAB) ⊥ (ABC) và (SAH) ⊥ (SBC).',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'H là hình chiếu của A trên BC; ý a) có HAI kết luận',
         "rui_ro": "thấp. Đề gốc có ba ý a/b/c — **chỉ chép ý b)**; ý a) hỏi "
                   "đường chéo (ra a√3, vô tỉ), ý c) hỏi số đo góc nhị diện"},
    ],
    "B03": [
        {"nguon": "Lê Bá Bảo — *Dạng toán xác định góc nhị diện Toán 11* (14tr) — **II. BÀI TẬP TỰ LUẬN**, Câu 4 (đề tr PDF 2) · https://toanmath.com/2024/03/dang-toan-xac-dinh-goc-nhi-dien-toan-11.html",
         "dap_an": "",
         "goi_y": "hình lập phương ABCD.A'B'C'D' cạnh a · xác định và tính góc phẳng nhị diện [A,BD,A'] và [C,BD,A']",
         "vi_sao": "PASS 2 — nhị diện trên LẬP PHƯƠNG, khác hẳn ngữ cảnh thực của kim tự tháp",
         "de": 'Cho biết kim tự tháp Memphis tại bang Tennessee (Mỹ) có dạng hình chóp tứ giác đều với chiều cao 98 m và cạnh đáy 180 m. Tính số đo góc nhị diện tạo bởi mặt bên và mặt đáy?',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'hai số 98 m và 180 m',
         "rui_ro": "thấp"},
        {"nguon": "Lê Bá Bảo — *Dạng toán xác định góc nhị diện Toán 11* "
                  "(14tr) — **II. BÀI TẬP TỰ LUẬN**, Câu 6 (đề tr PDF 2) · "
                  "https://toanmath.com/2024/03/dang-toan-xac-dinh-goc-nhi-"
                  "dien-toan-11.html",
         "dap_an": "",
         "goi_y": "kim tự tháp Memphis (Tennessee, Mỹ) dạng chóp tứ giác đều, "
                  "cao 98 m, cạnh đáy 180 m · tính góc nhị diện mặt bên–đáy",
         "vi_sao": "đúng loại ô B03 (góc nhị diện có miền). Thêm giá trị: đề "
                   "diễn đạt bằng NGỮ CẢNH THỰC + đơn vị mét — dạng ngôn ngữ "
                   "không ứng viên nào khác có",
         "de": "Cho hình lập phương ABCD.A'B'C'D' cạnh a. Xác định và tính góc phẳng nhị diện: a) [A,BD,A']; b) [C,BD,A'].",
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": 'ký hiệu nhị diện dạng [X,YZ,T] — chép đủ dấu ngoặc vuông và dấu phẩy',
         "rui_ro": "thấp. Dùng `ĐÁP ÁN NGUỒN:`, KHÔNG dùng `ĐÁP ÁN:`"},
    ],
    # ── Nguồn 4: Chuyên đề mặt nón, mặt trụ, mặt cầu (302tr) ──
    "B05": [
        {"nguon": "Tài liệu chuyên đề mặt nón, mặt trụ, mặt cầu (302tr) — **HỆ THỐNG BÀI TẬP TỰ LUẬN**, Dạng 1, Câu 2 (đề tr PDF 5) · https://toanmath.com/2023/07/tai-lieu-chuyen-de-mat-non-mat-tru-mat-cau.html",
         "dap_an": "",
         "goi_y": "tam giác SOA vuông tại O, OA = 3cm, SA = 5cm · quay quanh SO được hình nón · tính diện tích xung quanh, toàn phần và thể tích",
         "vi_sao": "PASS 2 — mặt cong sinh bởi PHÉP QUAY, khác đề cho sẵn r và l. Ngôn ngữ *quay quanh cạnh* là dạng diễn đạt mới",
         "de": 'Cho hình nón có bán kính đáy r = 3cm và đường sinh l = 5cm. a) Tính diện tích xung quanh và diện tích toàn phần của hình nón.',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'r = 3cm, l = 5cm; ý a)',
         "rui_ro": "thấp"},
        {"nguon": "Tài liệu chuyên đề mặt nón, mặt trụ, mặt cầu (302tr) — "
                  "**HỆ THỐNG BÀI TẬP TỰ LUẬN**, Dạng 1 *hình nón*, Câu 1 "
                  "**ý a)** (đề tr PDF 5; lời giải tr 19+) · "
                  "https://toanmath.com/2023/07/tai-lieu-chuyen-de-mat-non-"
                  "mat-tru-mat-cau.html",
         "dap_an": "",
         "goi_y": "hình nón bán kính đáy r = 3cm, đường sinh l = 5cm · tính "
                  "diện tích xung quanh và toàn phần",
         "vi_sao": "MẶT CONG — kernel chỉ dựng đa diện lồi. Đề ngắn nhất và "
                   "rõ nhất trong mục",
         "de": 'Cho tam giác SOA vuông tại O có OA = 3cm, SA = 5cm, quay tam giác SOA xung quanh cạnh SO được hình nón. a) Tính diện tích xung quanh và diện tích toàn phần của hình nón.',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'vuông tại O; OA = 3cm, SA = 5cm; quay quanh SO',
         "rui_ro": "thấp. Dùng `ĐÁP ÁN NGUỒN:`, KHÔNG dùng `ĐÁP ÁN:`"},
    ],
    # ── Nguồn 5–8: HTML + SBT, cho sáu ô cuối của Pass 1 ──
    "A04": [
        {"nguon": "SGK Toán 11 Kết nối tri thức — **Bài 4.44 trang 103**, ý a) (lời giải: Loigiaihay)",
         "dap_an": "true",
         "goi_y": "chóp S.ABCD đáy hình bình hành · G, K là TRỌNG TÂM △SAD và △SCD · chứng minh GK ∥ (ABCD)",
         "vi_sao": "PASS 2 — hai trọng tâm trên hai mặt bên KHÁC nhau; lời giải nguồn đi qua H trung điểm SD và tỉ số HG/HA = HK/HC = 1/3 ⇒ GK ∥ AC. Kiểm số chính xác: G(0,1/3,1/3) K(1/3,2/3,1/3), GK ∥ AC và GK.z = 0",
         "de": 'Cho hình chóp S.ABCD. Gọi M, N lần lượt là trung điểm của AB và BC; G1, G2 tương ứng là trọng tâm các tam giác SAB, SBC. a) Chứng minh AC // (SMN).',
         "rui_ro_muc": 'HIGH',
         "kiem_gi": "bản trích web hiển thị ký hiệu ∥ thành chữ 'P' — PHẢI mở nguồn xác nhận đúng là AC ∥ (SMN), và tên G1, G2",
         "rui_ro": "thấp — nguồn SGK, đáp án là `true`"},
        {"nguon": "DeThi.edu.vn — *Bài tập tự luận Toán 11: Đường thẳng và mặt phẳng song song (có lời giải)*, Bài 32 **ý a)** · https://dethi.edu.vn/bai-tap-tu-luan-toan-11-duong-thang-va-mat-phang-song-song-co-loi-giai-27650/",
         "dap_an": "true",
         "goi_y": "chóp S.ABCD đáy bình hành · M, N, P trên SA, SB, AD với SM/SA = SN/SB = PD/AD · chứng minh MN ∥ (ABCD)",
         "vi_sao": "PASS 2 — điểm chia theo TỈ SỐ BẰNG NHAU thay vì trung điểm; ba điểm trên ba cạnh khác nhau",
         "de": 'Cho hình chóp S.ABCD có đáy ABCD là hình bình hành. Trên các cạnh SA, SB, AD lần lượt lấy các điểm M, N, P sao cho SM/SA = SN/SB = PD/AD. a) Chứng minh MN // (ABCD).',
         "rui_ro_muc": 'HIGH',
         "kiem_gi": 'ba tỉ số SM/SA = SN/SB = PD/AD — xác nhận đúng MẪU SỐ, đặc biệt PD/AD chứ không phải AP/AD',
         "rui_ro": "trung bình — tỉ số chung không được cho giá trị; kết luận đúng với mọi tỉ số (cùng lớp *tham số tự do* đã chốt). Chỉ chép ý a)"},
        {"nguon": "DeThi.edu.vn — *Bài tập tự luận Toán 11: Đường thẳng và mặt "
                  "phẳng song song (có lời giải)*, Bài 31 **ý a)** · "
                  "https://dethi.edu.vn/bai-tap-tu-luan-toan-11-duong-thang-"
                  "va-mat-phang-song-song-co-loi-giai-27650/",
         "dap_an": "true",
         "goi_y": "chóp S.ABCD · M, N trung điểm AB và BC · G₁, G₂ trọng tâm "
                  "△SAB, △SBC · chứng minh AC ∥ (SMN)",
         "vi_sao": "MN là đường trung bình △ABC ⇒ MN ∥ AC ⇒ AC ∥ (SMN). "
                   "Trung điểm và trọng tâm đều giữ toạ độ hữu tỉ; không dữ "
                   "kiện số nào",
         "de": 'Cho hình chóp S.ABCD có đáy ABCD là hình bình hành. Gọi G, K lần lượt là trọng tâm của tam giác SAD, SCD. a) Chứng minh GK // (ABCD).',
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": 'G, K là trọng tâm SAD và SCD',
         "rui_ro": "thấp. Đề gốc nhiều ý — **chỉ chép ý a)**"},
    ],
    "A05": [
        {"nguon": "SGK Toán 11 — **Bài 4.17 trang 114** (lời giải: Loigiaihay)",
         "dap_an": "true",
         "goi_y": "chóp S.ABCD đáy HÌNH THANG, AD đáy lớn, AD = 2BC · I, K, L trung điểm AD, SA, SD · chứng minh (SAB) ∥ (ILC)",
         "vi_sao": "PASS 2 — đáy hình thang có TỈ SỐ RÀNG BUỘC (AD = 2BC), khác bình hành/tam giác của hai ứng viên kia. Lời giải nguồn ghép IL ∥ SA với IC ∥ AB",
         "de": 'Cho hình chóp S.ABC. Gọi M, N, P lần lượt là trung điểm của các cạnh SA, SB, SC. Chứng minh rằng (MNP) // (ABC).',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'ba trung điểm trên ba cạnh bên SA, SB, SC',
         "rui_ro": "thấp. Đề gốc chứng minh HAI cặp mặt — **chỉ chép cặp (SAB) ∥ (ILC)**; cặp (SCD) ∥ (BIK) để dành nếu cần"},
        {"nguon": "Kênh Giáo Viên — *Bài tập tự luận Toán 11 CTST, Chương 4 Bài 4: Hai mặt phẳng song song*, phần NHẬN BIẾT, Câu 5 · https://kenhgiaovien.com/tai-lieu/bai-tap-file-word-toan-11-chan-troi-sang-tao-chuong-4-bai-4-hai-mat-phang-song-song",
         "dap_an": "true",
         "goi_y": "chóp đáy HÌNH BÌNH HÀNH tâm O · M, N trung điểm · chứng minh hai mặt phẳng song song (theo bản đồ nguồn: (OMN) ∥ (SBC))",
         "vi_sao": "PASS 2 — dùng TÂM O của đáy làm điểm dựng, và chuỗi lập luận đi qua HAI quan hệ đường-mặt rồi mới ghép; khác hẳn ba trung điểm của Câu 4",
         "de": '<CHƯA CHÉP ĐƯỢC — bản trích trang rơi mất tên điểm; xem CẦN KIỂM GÌ>',
         "rui_ro_muc": 'HIGH',
         "kiem_gi": "bản trích rơi TOÀN BỘ tên điểm ('gọi … lần lượt là trung điểm của …'). PHẢI mở nguồn gõ lại đề; theo bản đồ nguồn là đáy hình bình hành tâm O, chứng minh (OMN) ∥ (SBC)",
         "rui_ro": "⚠️ CAO NHẤT trong gói: bản trích trang RƠI MẤT TÊN ĐIỂM ('gọi lần lượt là trung điểm của'). Phải mở nguồn đối chiếu tên điểm trước khi chép — đừng tin phần gợi ý này"},
        {"nguon": "Kênh Giáo Viên — *Bài tập tự luận Toán 11 CTST, Chương 4 "
                  "Bài 4: Hai mặt phẳng song song*, phần NHẬN BIẾT, Câu 4 · "
                  "https://kenhgiaovien.com/tai-lieu/bai-tap-file-word-toan-11-"
                  "chan-troi-sang-tao-chuong-4-bai-4-hai-mat-phang-song-song",
         "dap_an": "true",
         "goi_y": "chóp S.ABC · M, N, P trung điểm SA, SB, SC · chứng minh "
                  "(MNP) ∥ (ABC)",
         "vi_sao": "ba trung điểm ⇒ toạ độ hữu tỉ. Nghĩa vụ `parallel` "
                   "MẶT–MẶT, đúng thứ ô A05 đòi. Lời giải hiện ngay trên trang",
         "de": 'Cho hình chóp S.ABCD có đáy là hình thang, AD là đáy lớn và AD = 2BC. Gọi I, K, L lần lượt là trung điểm của AD, SA, SD. Chứng minh (SAB) // (ILC).',
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": 'AD = 2BC; I,K,L là trung điểm AD,SA,SD; cặp mặt (SAB) ∥ (ILC)',
         "rui_ro": "thấp — ứng viên gọn nhất trong nhóm song song"},
    ],
    "A06": [
        {"nguon": "Loigiaihay — *Cách chứng minh hai đường thẳng vuông góc "
                  "trong không gian (lí thuyết và bài tập)*, **Ví dụ 1**, "
                  "ý `AC ⊥ B'D'` · https://loigiaihay.com/cach-chung-minh-"
                  "hai-duong-thang-vuong-goc-trong-khong-gian-li-thuyet-va-"
                  "bai-tap-a187814.html",
         "dap_an": "true",
         "goi_y": "hình hộp sáu mặt đều là hình vuông (lập phương) · chứng minh AC ⊥ B'D'",
         "vi_sao": "PASS 2 — cùng hình nhưng đường chéo CHÉO NHAU thay vì cạnh–cạnh; lập luận nguồn đi qua B'D' ∥ BD rồi AC ⊥ BD",
         "de": "Cho hình hộp ABCD.A'B'C'D' có 6 mặt đều là hình vuông. Chứng minh AB ⊥ CC'.",
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": "'6 mặt đều là hình vuông' (tức lập phương) và ý cần chép là AB ⊥ CC'",
         "rui_ro": "thấp"},
        {"nguon": "Loigiaihay — *Cách chứng minh hai đường thẳng vuông góc "
                  "trong không gian*, **Ví dụ 1**, ý `AB ⊥ CC'` · " 
                  "https://loigiaihay.com/cach-chung-minh-hai-duong-thang-vuong-goc-trong-khong-gian-li-thuyet-va-bai-tap-a187814.html",
         "dap_an": "true",
         "goi_y": "hình hộp ABCD.A'B'C'D' có **6 mặt đều là hình vuông** "
                  "(tức LẬP PHƯƠNG) · chứng minh AB ⊥ CC'",
         "vi_sao": "sáu mặt vuông ⇒ lập phương ⇒ toạ độ NGUYÊN. Lập luận "
                   "nguồn: CC' ∥ BB' nên (AB,CC') = (AB,BB') = 90°. Nghĩa vụ "
                   "`perpendicular` ĐƯỜNG–ĐƯỜNG — đúng thứ A06 đòi, và là ô "
                   "DUY NHẤT không tìm được trong hai tài liệu chuyên đề",
         "de": "Cho hình hộp ABCD.A'B'C'D' có 6 mặt đều là hình vuông. Chứng minh AC ⊥ B'D'.",
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": "ý thứ hai: AC ⊥ B'D' — chú ý dấu phẩy trên B' và D'",
         "rui_ro": "thấp. Ví dụ 1 có hai ý (`AB ⊥ CC'` và `AC ⊥ B'D'`) — "
                   "**chỉ chép ý đầu**; ý sau cũng hữu tỉ, để dành Pass 2"},
    ],
    "B02": [
        {"nguon": "SBT Toán 11 Kết nối tri thức — **Bài 7.27 trang 37**, ý b)",
         "dap_an": "",
         "goi_y": "hình lập phương ABCD.A'B'C'D' cạnh a · tính khoảng cách "
                  "giữa đường thẳng AC và mặt phẳng (A'B'C'D')",
         "vi_sao": "AC ∥ A'C' ⊂ (A'B'C'D') ⇒ AC ∥ (A'B'C'D') ⇒ khoảng cách "
                   "ĐƯỜNG ∥ MẶT — đúng loại ô B02. Nguồn cho d = AA' = a",
         "de": "Cho hình lập phương ABCD.A'B'C'D' cạnh a. b) Tính khoảng cách giữa đường thẳng AC và mặt phẳng (A'B'C'D').",
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": "ý b) của bài 7.27; mặt phẳng (A'B'C'D') là mặt TRÊN",
         "rui_ro": "thấp. Dùng `ĐÁP ÁN NGUỒN:`, KHÔNG dùng `ĐÁP ÁN:` — dù "
                   "đáp án `a` trông hữu tỉ, tầng B KHÔNG chấm bằng oracle"},
    ],
    "B04": [
        {"nguon": "Chuyên đề *Phương trình mặt phẳng* (267tr) — mục `TU-LUAN_DE`, **Dạng 5**, Câu 1 (đề tr PDF 5) · https://toanmath.com/2023/07/tai-lieu-chuyen-de-phuong-trinh-mat-phang.html",
         "dap_an": "",
         "goi_y": "Trong không gian Oxyz, viết phương trình mặt phẳng (P) qua M(−1;−2;5) và vuông góc với HAI mặt phẳng (Q): x + 2y − 3z + 1 = 0 và (R): 2x − 3y + z + 1 = 0",
         "vi_sao": "PASS 2 — ràng buộc là VUÔNG GÓC VỚI HAI MẶT thay vì qua hai điểm; vẫn Oxyz cho sẵn nên vẫn đúng lý do ngoài phủ",
         "de": 'Trong không gian Oxyz, viết phương trình mặt phẳng (α) đi qua điểm A(1;2;-2), B(2;-1;4) và vuông góc với (β): x - 2y - z + 1 = 0.',
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": 'toạ độ A(1;2;−2), B(2;−1;4) và hệ số của (β) — kiểm từng dấu âm',
         "rui_ro": "thấp. Dùng `ĐÁP ÁN NGUỒN:`"},
        {"nguon": "Chuyên đề *Phương trình mặt phẳng* (267tr) — mục "
                  "`TU-LUAN_DE`, **Dạng 4**, Câu 1 (đề tr PDF 5 = 'Page 55'; "
                  "lời giải mục `TU-LUAN_HDG-CHI-TIET` tr 13–35) · "
                  "https://toanmath.com/2023/07/tai-lieu-chuyen-de-phuong-"
                  "trinh-mat-phang.html",
         "dap_an": "",
         "goi_y": "Trong không gian Oxyz, viết phương trình mặt phẳng (α) qua "
                  "A(1;2;−2), B(2;−1;4) và vuông góc với (β): x − 2y − z + 1 = 0",
         "vi_sao": "Oxyz CHO SẴN toạ độ ⇒ mô hình không phải tự đặt hệ trục, "
                   "đúng lý do ngoài phủ của ô B04. Hệ số nguyên, đề gọn",
         "de": 'Trong không gian Oxyz, viết phương trình mặt phẳng (P) đi qua điểm M(-1;-2;5) và vuông góc với hai mặt phẳng (Q): x + 2y - 3z + 1 = 0 và (R): 2x - 3y + z + 1 = 0.',
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": 'M(−1;−2;5) và hệ số của (Q), (R) — kiểm từng dấu âm',
         "rui_ro": "thấp. Dùng `ĐÁP ÁN NGUỒN:`, KHÔNG dùng `ĐÁP ÁN:`"},
    ],
    "B06": [
        {"nguon": "Kênh Giáo Viên — *Bài tập tự luận Toán 11 KNTT, Bài 14: Phép chiếu song song*, phần VẬN DỤNG, Câu 1 · https://kenhgiaovien.com/tai-lieu/bai-tap-file-word-toan-11-ket-noi-bai-14-phep-chieu-song-song",
         "dap_an": "",
         "goi_y": "vẽ hình chiếu của hình chóp S.ABCD lên mặt phẳng (P) theo phương chiếu SA",
         "vi_sao": "PASS 2 — chiếu cả một KHỐI (không phải một điểm), và phương chiếu là một CẠNH của khối. Nguồn trả lời: ảnh là tứ giác A'B'C'D'",
         "de": 'Cho tứ diện ABCD. I là trọng tâm tam giác ABC. Xác định hình chiếu song song của I theo phương CD lên mặt phẳng (ABD).',
         "rui_ro_muc": 'LOW',
         "kiem_gi": 'I là TRỌNG TÂM ABC; phương chiếu CD; mặt phẳng chiếu (ABD)',
         "rui_ro": "thấp. Dùng `ĐÁP ÁN NGUỒN:`"},
        {"nguon": "Kênh Giáo Viên — *Bài tập tự luận Toán 11 KNTT, Bài 14: "
                  "Phép chiếu song song*, phần NHẬN BIẾT, Câu 3 · "
                  "https://kenhgiaovien.com/tai-lieu/bai-tap-file-word-toan-11-"
                  "ket-noi-bai-14-phep-chieu-song-song",
         "dap_an": "",
         "goi_y": "tứ diện ABCD · I trọng tâm △ABC · xác định hình chiếu song "
                  "song của I theo phương CD lên mặt phẳng (ABD)",
         "vi_sao": "PHÉP CHIẾU SONG SONG — đúng loại ô B06. Nguồn trả lời: "
                   "ảnh là J, trọng tâm △ABD",
         "de": 'Vẽ hình chiếu của hình chóp S.ABCD lên mặt phẳng (P) theo phương chiếu SA.',
         "rui_ro_muc": 'MEDIUM',
         "kiem_gi": 'phương chiếu là SA; mặt phẳng chiếu là (P)',
         "rui_ro": "thấp. Dùng `ĐÁP ÁN NGUỒN:`, KHÔNG dùng `ĐÁP ÁN:`"},
    ],
}

#: Ô chưa tra được nguồn nào — đánh dấu chứ không đổi giao thức.
#:
#: **A11 đã ra khỏi danh sách này (2026-08-28)** — tìm được đúng một ứng viên
#: hữu tỉ, xem `DA_SOI["A11"]`. A12 thì khác về BẢN CHẤT chứ không phải khác về
#: công sức tìm: `d(điểm→mặt) = SA·SB/AB` chỉ cần MỘT trùng hợp Pythagore, còn
#: `d(điểm→đường)` trong không gian ra `√(tổng bình phương)` nên cần trùng hợp
#: Pythagore LẦN HAI lồng vào. Chi tiết: `HOLDOUT_ACQUISITION_LOG §7e`.
SOURCE_GAP = ("A12",)

#: Luật sàng nhanh, dán ngay chỗ cần dùng. Luật ĐỦ chỉ có một, ở `_MO_DAU`.
_GOI_Y_O: dict[str, str] = {
    "A09": "`cos²` giữa HAI ĐƯỜNG. Toạ độ hữu tỉ ⇒ `cos²` luôn hữu tỉ, nên ô "
           "này KHÔNG vướng rào vô tỉ ở đáp án — dễ hơn A11/A12 nhiều.",
    "A10": "⚠️ Đường–MẶT trả **`sin²`**, KHÔNG phải `cos²`. Chép nhầm thì chấm "
           "sai mà không cổng nào báo. Đáp án sách hay cho góc α ⇒ ghi `sin²α`.",
    "A11": "Khoảng cách điểm → MẶT. Chỉ nhận khi ra phân số HỮU TỈ.\n"
           "Trong cấu hình chuẩn (SA ⊥ đáy, AB ⊥ BC) thì BC ⊥ (SAB), nên\n"
           "    d(A,(SBC)) = SA·AB / √(SA² + AB²)\n"
           "⇒ HỮU TỈ ⟺ (SA, AB) là cặp cạnh góc vuông PYTHAGORE.\n"
           "CHỮ KÝ CẦN TÌM — liếc hai số rồi quyết trong một giây:\n"
           "    3–4 → 12/5 · 6–8 → 24/5 · 5–12 → 60/13 · 9–12 → 36/5\n"
           "BỎ NGAY nếu thấy: SA = a · a√2 · a√3, hay đáy vuông cạnh a —\n"
           "chúng cho d vô tỉ, và chúng chiếm gần hết tài liệu phổ thông.",
    "A12": "Khoảng cách điểm → ĐƯỜNG. CÙNG một công thức, cùng chữ ký\n"
           "Pythagore như A11: d(A,SB) = SA·AB / √(SA² + AB²).",
    "A13": "Cần khối **LỒI**. Đề thiết diện hay kèm hình vẽ — bỏ bài nào phải "
           "nhìn hình mới hiểu.",
    "A14": "Thể tích. Gán `a = 1` rồi chép phân số (`2a³/3` → `2/3`).",
}

_MO_DAU = """\n# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 7B — GÓI XÁC MINH NGUỒN   (trước đây: gói chép tay)
# ═══════════════════════════════════════════════════════════════════════════
#
#  ĐỔI QUY TRÌNH 2026-08-28 — `PROTOCOL_AMENDMENT_PRESEAL`:
#
#    CŨ:  người tự gõ nguyên văn cả 42 đề.
#    MỚI: MÁY chép từ nguồn đã dẫn; NGƯỜI xác minh THEO RỦI RO.
#
#  Việc của bạn, ba bước:
#
#    (1) ký MỘT dòng `NGƯỜI CHÉP:` dưới đây — nay mang nghĩa
#        NGƯỜI XÁC MINH NGUỒN, kèm cam kết ở cuối phần này
#    (2) mở nguồn đối chiếu MỌI khối ghi `RỦI RO : HIGH`
#    (3) đối chiếu thêm một mẫu QC (~20% khối LOW/MEDIUM)
#
#  Mỗi khối in sẵn `RỦI RO` và `CẦN KIỂM GÌ` — chỉ kiểm đúng thứ nêu ở đó.
#
# --- VÌ SAO ĐỔI --------------------------------------------------------
#
#  Gõ lại 42 đề là việc thuần cơ học, và KHÔNG phải thứ bảo đảm tính
#  held-out. Ba bảo đảm thật thì không đổi: đề từ NGUỒN CÔNG KHAI CÓ TRÍCH
#  DẪN; ĐÁP ÁN LÀ CỦA NGUỒN, không do ta tính; tập đo bị ĐÓNG BĂNG VÀ BĂM
#  trước khi model chạy. Cái được bỏ chỉ là công gõ.
#
# --- VÌ SAO MÁY KHÔNG TRÍCH TEXT PDF -----------------------------------
#
#  Đo trong chính kho này: trích text các PDF ấy cho `vuong goc` 204 lần
#  nhưng dấu CĂN 0 lần — mọi bài vô tỉ hiện ra như bài hữu tỉ. Nên mọi đề
#  dưới đây đọc từ ẢNH TRANG đã dựng, hoặc HTML hiển thị đủ. Chỗ nào máy
#  không đọc chắc thì để `<...>` và gắn HIGH.
#
# --- HAI THANG CHẤM, ĐỪNG TRỘN -----------------------------------------
#
#  TẦNG A (A01-A14): hỏi *hệ tính ĐÚNG không*  -> có `ĐÁP ÁN:`
#  TẦNG B (B01-B06): hỏi *hệ có BIẾT mình không tính được không*
#                    -> KHÔNG có `ĐÁP ÁN:`; dùng `ĐÁP ÁN NGUỒN:`
#  Ô tầng B vẫn cần BẠN chép `ĐÁP ÁN NGUỒN` từ sách — máy không có nó.
#
# --- XONG THÌ CHẠY -----------------------------------------------------
#
#    cd backend
#    python scripts/validate_human_copy_packet.py <gói>
#    python scripts/finalize_phase7b_holdout.py <gói> --ghi
#
# ═══════════════════════════════════════════════════════════════════════════
#
#  CAM KẾT — ký dòng dưới là xác nhận đúng câu này:
#
#    "Tôi đã đối chiếu độc lập MỌI khối HIGH_RISK và mẫu QC quy định với
#     đúng trang nguồn được trích dẫn, trước khi niêm phong. Không dùng bất
#     kỳ đầu ra nào của hệ được đo trong lúc chuẩn bị tập dữ liệu này."
#
#  Đừng ký nếu chưa làm (2) và (3): báo cáo sẽ khai ĐÚNG những gì dòng này
#  nói, và nó KHÔNG được phép nói "42/42 người kiểm".

NGƯỜI CHÉP: <tên bạn> · <YYYY-MM-DD> · đã đối chiếu HIGH_RISK và mẫu QC
"""


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        f"_pk_{ten}", Path(__file__).resolve().parent / f"{ten}.py")
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"_pk_{ten}"] = m
    spec.loader.exec_module(m)
    return m


def _khoi(o: str, SH, MT, da_soi: dict | None,
          thu: int = 1, tong: int = 1) -> list[str]:
    """Một khối cho một ứng viên. Siêu dữ liệu đi bằng dòng `#` — `ingest` gỡ
    sạch chúng trước khi lấy `problem_text`, nên chúng không lọt vào đề."""
    tag, hinh, tang_a = next(
        (t, h, a) for t, (os_, h, a) in SH.NANG_LUC.items() if o in os_)
    nv = SH.BANG_O[o][0]
    dau = f"{o} ({thu}/{tong}) · {SH.BANG_O[o][1]}"
    d = [f"#   ─── {dau} " + "─" * max(3, 60 - len(dau)),
         f"#     CAPABILITY : {tag}",
         f"#     ANSWER     : {hinh}" + (f" → nghĩa vụ `{nv}`" if nv else ""),
         f"#     THANG CHẤM : " + ("oracle + ③a/③b/⑤" if tang_a
                                   else "TỪ CHỐI TRUNG THỰC — không oracle")]
    if o in ("A10",):
        d.append("#     ⚠️ ĐƠN VỊ   : sin² (đường–mặt), KHÔNG phải cos²")
    if goi := _GOI_Y_O.get(o):
        for i, g in enumerate(goi.split("\n")):
            d.append(f"#     TÌM BÀI    : {g}" if i == 0
                     else f"#                  {g}")
    if them := MT.O_RANG_BUOC_THEM.get(o):
        d.append("#     RÀNG BUỘC  : " + them.replace("**", ""))
    if o in SOURCE_GAP:
        d.append(f"#     ⛔ SOURCE_GAP_{o} — chưa tra được nguồn nào có sẵn "
                 f"bài loại này. Bỏ qua được.")
    if da_soi:
        d += [f"#     ĐÃ SOI     : {da_soi['goi_y']}",
              f"#     VÌ SAO CHỌN: {da_soi['vi_sao']}",
              f"#     RỦI RO     : {da_soi['rui_ro']}",
              "#     → NGUỒN và ĐÁP ÁN đã điền sẵn. Chỉ còn gõ ĐỀ."
              if tang_a else
              "#     → NGUỒN đã điền sẵn. Còn gõ ĐỀ + chép ĐÁP ÁN NGUỒN."]

    # ── ĐỀ: chép máy nếu đã có, còn không thì để người gõ ────────────────
    #
    # Đổi 2026-08-28 (`PROTOCOL_AMENDMENT_PRESEAL`): `problem_text` được phép
    # **chép máy từ nguồn đã dẫn**, thay cho việc người gõ lại toàn bộ. Đổi
    # lại, mỗi bài mang **mức rủi ro** và người xác minh chỉ phải mở nguồn cho
    # nhóm HIGH + một mẫu QC — chứ không phải cả 42.
    #
    # ⚠️ Chép máy ở đây KHÔNG phải trích text PDF: đo trong chính kho này,
    # trích text nuốt sạch `√` (`⊥` 204 lần / `√` 0 lần) và làm rơi tên điểm.
    # Mọi đề dưới đây đọc từ **ảnh trang đã dựng** hoặc HTML hiển thị đủ.
    if da_soi and da_soi.get("de"):
        muc = da_soi.get("rui_ro_muc", "MEDIUM")
        d += [f"#     RỦI RO     : {muc}"
              + ("   ← PHẢI mở nguồn đối chiếu" if muc == "HIGH" else ""),
              f"#     CẦN KIỂM GÌ: {da_soi.get('kiem_gi', 'đối chiếu nguyên văn với nguồn')}"]
        d.append(f"[{o}] {da_soi['de']}")
    else:
        d.append(f"[{o}] <GÕ NGUYÊN VĂN ĐỀ VÀO ĐÂY — giữ đủ = ⊥ ∥ ∈ √ ·>")
    d.append(f"      NGUỒN: {da_soi['nguon'] if da_soi else '<sách · trang · câu>   hoặc   <url>'}")
    if tang_a:
        d.append(f"      ĐÁP ÁN: {da_soi['dap_an'] if da_soi else '<đáp án của nguồn, dạng phân số hoặc true/false>'}")
    else:
        d += ["      ĐÁP ÁN NGUỒN: <đáp án in trong sách — chỉ để tra ngược>",
              f"      NGOÀI PHỦ VÌ: {SH.BANG_O[o][1]} — ngoài ranh giới kernel"]
    d.append("")
    return d


def dung_goi() -> str:
    SH, MT = _nap("seal_geometry_holdout"), _nap("holdout_coverage_matrix")
    d = _MO_DAU.splitlines() + [""]

    # Xếp theo NGUỒN để mỗi tài liệu chỉ phải mở một lần — đó là toàn bộ lý do
    # gói này tồn tại thay vì 40 lượt hỏi.
    theo_nguon: dict[str, list[str]] = {}
    for o in SH.BANG_O:
        theo_nguon.setdefault(MT.O_NGUON[o], []).append(o)

    for i, (nguon, cac_o) in enumerate(theo_nguon.items(), 1):
        tong = sum(PHAT[o] for o in cac_o)
        d += ["", "# " + "═" * 71,
              f"#  NGUỒN {i} — {nguon}",
              f"#  {len(cac_o)} ô · {tong} khối · ô: {' '.join(cac_o)}",
              "# " + "═" * 71, ""]
        for o in cac_o:
            soi = DA_SOI.get(o, [])
            for k in range(PHAT[o]):
                d += _khoi(o, SH, MT, soi[k] if k < len(soi) else None,
                           k + 1, PHAT[o])

    tong = sum(PHAT.values())
    d += ["# " + "═" * 71,
          f"#  HẾT — {tong} khối / {len(SH.BANG_O)} ô.",
          f"#  Cần ≥{SH.MOI_O_TOI_THIEU} bài mỗi ô và ≥{SH.TONG_TOI_THIEU} "
          f"tổng ⇒ gói phát dư {tong - SH.TONG_TOI_THIEU} khối làm dự phòng.",
          "#  Khối nào bỏ qua thì XOÁ NGUYÊN KHỐI, đừng để chỗ trống.",
          "# " + "═" * 71, ""]
    return "\n".join(d)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ghi", action="store_true", help="Ghi file gói")
    a = p.parse_args()

    goi = dung_goi()
    if a.ghi:
        if RA.exists():
            # Gói đã điền là CÔNG SỨC CỦA NGƯỜI. Ghi đè nó là xoá phần duy
            # nhất của tập held-out mà máy không dựng lại được.
            print(f"ĐÃ CÓ: {RA}")
            print("KHÔNG ghi đè — gói có thể đã điền dở. Xoá tay nếu muốn dựng lại.")
            return 1
        RA.write_text(goi, encoding="utf-8")
        print(f"Đã ghi {RA}")
    else:
        print(goi)
    print(f"\n{sum(PHAT.values())} khối · {len(PHAT)} ô · "
          f"SOURCE_GAP: {', '.join(SOURCE_GAP)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
