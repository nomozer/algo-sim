# -*- coding: utf-8 -*-
"""PURPOSE ANALYSIS — *bước nào phục vụ câu hỏi của đề?* **0 API call.**

VÌ SAO TỒN TẠI (Phase 6 §5): hệ biết **đề hỏi gì** (`RequestContract`) *và*
**mỗi đối tượng dựng từ gì** (`_phu_thuoc`). Ghép hai thứ ấy cho ra một câu hỏi
mà một bảng liệt kê bước dựng — kể cả *Construction Protocol* của GeoGebra —
**không đặt được**, vì nó không có khái niệm "đề bài hỏi gì".

    Bước nào thật sự phục vụ đáp án, và bước nào là đường cụt?

─── KHÔNG SỬA IR, KHÔNG THÊM TRƯỜNG `why` ─────────────────────────────────

Tất cả dẫn xuất từ dữ liệu đã có: `obligations` · `_phu_thuoc` · `_producers`.
Thêm một trường `why` để LLM khai là mời nó **nói dối về mục đích** — và mục
đích tự khai thì không kiểm được. Bao đóng phụ thuộc thì kiểm được.

─── BA NHÃN, VÀ VÌ SAO PHẢI TÁCH BA ───────────────────────────────────────

Đo trên IR thật của lượt `8b4025e` cho thấy hai bệnh **rất khác nhau** đang bị
gộp thành một:

    geo_02   dựng `giao_tuyen` rồi KHÔNG dùng tới     → bước thừa THẬT
    geo_05   hợp đồng gọi `(ABCD)`, chương trình khai
             `ABCD_plane`                             → LỆCH DANH XƯNG

Gộp chúng lại thì `geo_05` bị đọc thành *"mô hình dựng hai bước vô ích"*, trong
khi lỗi thuộc **hợp đồng của ta** (Wave 4 đã ghi nhận). Một chỉ số vu oan cho
mô hình ở đúng chỗ ta sai là chỉ số tệ hơn không có.

Nên `NHAN_THUA` chỉ được phát khi **mọi tên trong nghĩa vụ đều giải được**.
"""
from __future__ import annotations

from typing import Any

from .contract import SemanticProgramSpec
from .coverage_gate import _bao_dong, _phu_thuoc, _producers
from .request_contract import RequestContract

#: Bước nằm trong bao đóng phụ thuộc của một nghĩa vụ — đáp án cần nó.
NHAN_CAN = "serves"
#: Bước tạo ra một đối tượng mà không nghĩa vụ nào cần tới.
NHAN_THUA = "redundant"
#: Nghĩa vụ gọi một tên chương trình không có. KHÔNG phải lỗi của bước nào.
NHAN_LECH_TEN = "name_mismatch"


def purpose_analysis(
    contract: RequestContract, spec: SemanticProgramSpec
) -> dict[str, Any]:
    """Mỗi bước dựng phục vụ nghĩa vụ nào — hoặc không phục vụ gì.

    ⚠️ **QUAN TRẮC, KHÔNG GÁC CỬA.** Không cổng nào được đọc kết quả này để
    phán quyết: một chương trình có bước thừa vẫn là một chương trình ĐÚNG, và
    "thừa" là nhận xét sư phạm chứ không phải lỗi. Dùng nó để chặn là biến một
    nhận xét thành một bản án.
    """
    tao_ra = _producers(spec.statements)
    dep = _phu_thuoc(spec.statements, frozenset())
    khai = {d.name for d in spec.memory_declarations}

    theo_nghia_vu: list[dict[str, Any]] = []
    can_toan_bo: set[str] = set()
    co_lech_ten = False

    for ob in contract.obligations:
        ten = [t for t in (ob.container, ob.witness) if t]
        # LỆCH DANH XƯNG kiểm TRƯỚC: nếu hợp đồng gọi một tên chương trình
        # không có, thì bao đóng rỗng KHÔNG nói lên điều gì về các bước — nó
        # chỉ nói hai lượt LLM đặt tên khác nhau.
        thieu = [t for t in ten if t not in khai]
        if thieu:
            co_lech_ten = True
            theo_nghia_vu.append({
                "kind": ob.kind, "container": ob.container,
                "witness": ob.witness, "trang_thai": NHAN_LECH_TEN,
                "ten_khong_giai_duoc": thieu,
                "chuong_trinh_khai": sorted(khai),
                "phuc_vu": [],
            })
            continue

        can: set[str] = set()
        for t in ten:
            can |= _bao_dong(dep, t) | {t}
        phuc_vu = sorted(can & tao_ra)
        can_toan_bo |= set(phuc_vu)
        theo_nghia_vu.append({
            "kind": ob.kind, "container": ob.container, "witness": ob.witness,
            "trang_thai": NHAN_CAN, "phuc_vu": phuc_vu,
        })

    # Bước "thừa" CHỈ có nghĩa khi mọi nghĩa vụ đều giải được tên. Còn một
    # nghĩa vụ lệch tên thì bao đóng của nó rỗng, và mọi bước trông như thừa.
    thua = sorted(tao_ra - can_toan_bo) if not co_lech_ten else []

    return {
        "khai": "QUAN TRẮC sư phạm — KHÔNG gác cửa. Chương trình có bước thừa "
                "vẫn là chương trình đúng.",
        "theo_nghia_vu": theo_nghia_vu,
        "buoc_can": sorted(can_toan_bo),
        "buoc_thua": thua,
        "co_lech_danh_xung": co_lech_ten,
        "tom_tat": {
            "so_buoc_dung": len(tao_ra),
            "so_buoc_can": len(can_toan_bo),
            "so_buoc_thua": len(thua),
            # `None` chứ không phải 0 khi có lệch tên: "không đo được" và
            # "không có bước thừa nào" là hai kết luận khác hẳn nhau.
            "ti_le_huu_ich": None if co_lech_ten or not tao_ra
            else round(len(can_toan_bo) / len(tao_ra), 3),
        },
    }
