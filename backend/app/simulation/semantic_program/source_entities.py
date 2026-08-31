# -*- coding: utf-8 -*-
"""TÊN NÀO CÓ TRONG ĐỀ — thẩm quyền neo nguồn cho thực thể hình học.

─── LỖ NÓ BỊT: RỬA NĂNG LỰC ───────────────────────────────────────────────

GENERALIZATION MATRIX, `gm_10` (mặt cầu ngoại tiếp — runtime KHÔNG có mặt
cầu). Mô hình khai:

    declare_point P_opposite = [2,2,2]
      model_assumption: "điểm đối diện với A trong hình hộp bao quanh"
    P = midpoint(A, P_opposite)      ← tâm mặt cầu
    R = distance(P, A)               ← √3, ĐÚNG

Đáp số đúng, nhưng runtime chưa bao giờ biểu diễn hay kiểm chứng khái niệm
*"mặt cầu ngoại tiếp"*. Mô hình tự giải trong đầu rồi **giấu định lý vào toạ
độ** của một điểm nó tự bịa, và `model_assumption` hợp thức hoá điều đó.

Cổng xuất xứ cũ không chặn được vì nó hỏi bốn câu — *có phải witness không ·
kiểu có được phép không · có lý do không · có `source_fact_id` không* — mà
không câu nào hỏi **"cái tên này có trong đề không"**.

─── VÌ SAO TRÍCH TỪ ĐỀ, KHÔNG ĐOÁN THEO HÌNH DẠNG TÊN ─────────────────────

Luật "tên một chữ cái in hoa thì là đỉnh" sẽ cho `X`, `H`, `O`, `T1` đi qua —
đúng những tên mà một lượt rửa năng lực đổi sang là lách được. Nên thẩm quyền
phải là **văn bản đề**: `S.ABCD` trong đề cho ra `{S, A, B, C, D}`;
`P_opposite` không có trong đề thì không có trong tập, dù nó trông hiền lành
đến đâu.

─── NỬA THỨ HAI: TÊN CÓ TRONG ĐỀ NHƯNG LÀ ĐIỂM SUY RA ─────────────────────

Chỉ hỏi *"có trong đề không"* thì hụt đúng một nửa. Đề viết *"Gọi H là hình
chiếu của S lên (ABCD)"* — `H` CÓ trong đề, nên nó qua được chốt trên; rồi mô
hình khai `H = [0,0,0]` bằng toạ độ tự tính. Vẫn là rửa năng lực, chỉ khác chỗ
cái tên được đề tặng cho.

`nhan_suy_ra` bắt đúng lớp đó: đề *giới thiệu* nhãn này bằng một mệnh đề định
nghĩa (*"Gọi … là"*, *"Lấy … là"*, *"H là trung điểm"*), tức nó là hệ quả của
hình chứ không phải dữ kiện của hình. Hệ quả thì phải DỰNG.

─── GIỚI HẠN, KHAI THẲNG ──────────────────────────────────────────────────

Bộ trích này KHÔNG hiểu đề — nó khớp mẫu chữ, không phân tích cú pháp. Một đề
định nghĩa điểm phụ bằng lối viết ngoài các mẫu dưới đây sẽ lọt. Nói thẳng chỗ
hở đúng hơn là để một con số 100% che nó đi.

Đổi lại, hai chốt bù nhau và không chốt nào một mình đủ: chốt ① chặn thực thể
**tự bịa**, chốt ② chặn thực thể **đề nêu nhưng là hệ quả**.
"""
from __future__ import annotations

import re

__all__ = ["nhan_hinh_hoc", "nhan_suy_ra", "chuan_hoa_ten", "la_ten_nguon",
           "la_ten_suy_ra"]

#: Một NHÃN HÌNH HỌC trong văn bản: chuỗi chữ in hoa, có thể kèm dấu phẩy
#: trên, chỉ số, và dấu chấm ngăn (`S.ABCD`, `ABCD.A'B'C'D'`, `A₁B₁C₁`).
#:
#: Chữ in hoa có dấu tiếng Việt KHÔNG nằm trong lớp này — `Cho`, `Tính`,
#: `Gọi` đều bắt đầu bằng chữ in hoa nhưng chỉ có MỘT chữ hoa rồi tới chữ
#: thường, nên `_TU_THUONG` loại chúng.
_NHAN = re.compile(r"[A-Z][A-Z0-9₀-₉'’.]*")

#: Chuỗi bắt đầu bằng hoa rồi toàn chữ thường là TỪ TIẾNG VIỆT, không phải nhãn.
_TU_THUONG = re.compile(r"^[A-Z][a-zà-ỹ]")

#: Tiền tố mô hình hay thêm vào tên biến. Bóc ra rồi mới đối chiếu.
_TIEN_TO = ("point_", "p_", "diem_", "vertex_", "dinh_", "pt_")

#: Hậu tố diễn tả dấu phẩy trên.
_HAU_TO_PHAY = ("_prime", "_phay", "prime")


def nhan_hinh_hoc(de: str) -> frozenset[str]:
    """Mọi tên đỉnh xuất hiện trong đề. `S.ABCD` → `{S, A, B, C, D}`.

    Tách từng nhãn thành các đỉnh RIÊNG LẺ vì đề viết gộp: *"hình chóp
    S.ABCD"* nêu năm đỉnh trong một chuỗi. Không tách thì `A` không bao giờ
    khớp và mọi bài đều trượt.
    """
    ra: set[str] = set()
    van = de or ""
    for m in _NHAN.finditer(van):
        tho = m.group(0)
        if _TU_THUONG.match(tho):
            continue
        # MỘT CHỮ HOA rồi tới chữ thường là ĐẦU MỘT TỪ TIẾNG VIỆT, không phải
        # nhãn: `Tính` cho ra `T` vì `í` không thuộc lớp nhãn, nên `_TU_THUONG`
        # (cần hai ký tự) không bắt được. Bỏ sót nó là để một điểm tên `T` rửa
        # được năng lực qua chữ "Tính" trong chính đề bài.
        sau = van[m.end():m.end() + 1]
        if len(tho) == 1 and sau and sau.islower():
            continue
        for cum in tho.replace("’", "'").split("."):
            if not cum:
                continue
            # Một cụm là dãy đỉnh viết liền: `ABCD`, `A'B'C'D'`, `A₁B₁C₁`.
            for m in re.finditer(r"[A-Z]['₀-₉0-9]*", cum):
                ra.add(m.group(0))
    return frozenset(ra)


#: Đề GIỚI THIỆU một điểm phụ: *"Gọi H là …"*, *"Lấy M, N lần lượt là …"*.
#: Cụm giữa bị chặn độ dài và cấm dấu câu để không nuốt sang mệnh đề sau.
_GIOI_THIEU = re.compile(r"(?:gọi|lấy)\s+([^.;:,]{1,40}?(?:,[^.;:]{1,40}?)?)"
                         r"\s+(?:lần lượt\s+)?là", re.IGNORECASE)

#: Vai trò HỆ QUẢ: nhãn đứng ngay trước một danh từ chỉ phép dựng.
_VAI_HE_QUA = re.compile(
    r"([A-Z]['’₀-₉0-9]*)\s+là\s+(?:trung điểm|hình chiếu|giao điểm|trọng tâm|"
    r"chân đường|tâm\b|điểm đối xứng)", re.IGNORECASE)


def nhan_suy_ra(de: str) -> frozenset[str]:
    """Nhãn mà ĐỀ giới thiệu như một điểm DỰNG RA, không phải dữ kiện.

    *"Cho hình chóp S.ABCD … Gọi M là trung điểm của SA"* → `{M}`. `S`, `A`…
    là dữ kiện của hình nên KHÔNG nằm ở đây; `M` là hệ quả nên có.

    Ranh giới quan trọng: hàm này KHÔNG thay `nhan_hinh_hoc`. Một nhãn có thể
    nằm ở cả hai tập, và khi ấy nó là hệ quả — vì đề đã tự nói ra điều đó.
    """
    van = de or ""
    ra: set[str] = set()
    for m in _GIOI_THIEU.finditer(van):
        ra |= nhan_hinh_hoc(m.group(1))
    for m in _VAI_HE_QUA.finditer(van):
        ra.add(m.group(1).replace("’", "'"))
    return frozenset(ra)


def chuan_hoa_ten(ten: str) -> frozenset[str]:
    """Tên biến trong IR → các nhãn đề có thể tương ứng.

    Mô hình đặt tên theo thói quen lập trình (`point_A`, `A_prime`,
    `line_AB`), còn đề viết theo thói quen toán (`A`, `A'`). Bóc tiền tố và
    quy dấu phẩy về một dạng. Trả về TẬP vì một tên có thể khớp nhiều cách, và
    khớp một cách là đủ.
    """
    t = (ten or "").strip()
    if not t:
        return frozenset()
    ung: set[str] = {t}
    thap = t.lower()
    for tt in _TIEN_TO:
        if thap.startswith(tt):
            ung.add(t[len(tt):])
    them: set[str] = set()
    for x in ung:
        for ht in _HAU_TO_PHAY:
            if x.lower().endswith(ht):
                them.add(x[: -len(ht)].rstrip("_") + "'")
    ung |= them
    # Bỏ gạch dưới còn sót: `A_1` → `A1`.
    ung |= {x.replace("_", "") for x in ung}
    return frozenset(x for x in ung if x)


def la_ten_nguon(ten: str, de: str) -> bool:
    """Tên này có neo được vào đề không?

    Đề rỗng ⇒ `True` — "chưa kiểm được", KHÔNG phải "không có nguồn". Cùng quy
    ước `InputFact.provenance="unchecked"`: một hợp đồng dựng bằng tay không
    có đề để đối chiếu, và kết luận FAIL ở đó là phạt một đường gọi hợp lệ.
    """
    if not (de or "").strip():
        return True
    co = nhan_hinh_hoc(de)
    return bool(chuan_hoa_ten(ten) & co)


def la_ten_suy_ra(ten: str, de: str) -> bool:
    """Tên này được ĐỀ giới thiệu như một điểm phải dựng ra?

    Đề rỗng ⇒ `False`, cùng quy ước "chưa kiểm được" với `la_ten_nguon`: không
    có đề thì không có căn cứ để buộc tội, và một hợp đồng dựng tay không đáng
    bị phạt vì thiếu thứ nó không cần.
    """
    if not (de or "").strip():
        return False
    return bool(chuan_hoa_ten(ten) & nhan_suy_ra(de))
