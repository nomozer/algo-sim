# -*- coding: utf-8 -*-
"""Bằng chứng MÁY KIỂM ĐƯỢC: băm `grammar_card` đổi CHỈ vì mệnh đề khoá khai báo.

SYNTHESIS_MEMORY_DECLARATION_SCHEMA_PROMPT_ALIGNMENT (2026-09-15) thêm vào dòng `memory_declarations[]` của thẻ
hình học đúng một mệnh đề khẳng định. Thành phần `grammar_card` của `semantic_environment_fingerprint` băm GỘP
thẻ mặc định + thẻ hình học, nên nó đổi — kéo theo ô ghim danh tính của các lượt đo đã đóng (thesis-final).

Những ô ấy KHÔNG được sửa artifact cho khớp. Module này DỰNG LẠI băm lịch sử từ thẻ hiện tại, chỉ bỏ đúng mệnh đề
ấy. Khớp ⇒ mọi dòng khác của cả hai thẻ giữ nguyên từng byte. Không phải file test (không có tiền tố `test_`);
`test_memory_declaration_contract_alignment.py::test_M_*` khoá nó, kèm phép tiêm cho thấy nó đỏ được.
"""

from __future__ import annotations

import json

#: Mệnh đề wave thêm vào dòng `memory_declarations[]` của thẻ hình học.
MENH_DE_KHOA_DUNG = " — mỗi mục có ĐÚNG các khoá này"

#: `semantic_environment_fingerprint()["grammar_card"]` tại e51901d — trùng `cache_identity.lock.json` trước wave và
#: `GRAMMAR_CARD_HASH` của con dấu thesis-final.
GRAMMAR_CARD_TRUOC_WAVE = "6cbba1885b2073fa920f82e6b952108f68824f19f444792cc4fc0b8b190af4f4"


def grammar_card_neu_chua_them_menh_de() -> str:
    """Băm `grammar_card` của hệ HIỆN TẠI nếu mệnh đề khoá khai báo chưa được thêm (cùng công thức `runtime_identity`)."""
    from app.runtime_identity import _bam
    from app.simulation.semantic_program.grammar_card import grammar_card

    hinh_hoc = grammar_card("hinh_hoc")
    assert hinh_hoc.count(MENH_DE_KHOA_DUNG) == 1, "mệnh đề không còn đúng một lần — bằng chứng vô nghĩa"
    return _bam(json.dumps({
        "mac_dinh": _bam(grammar_card()),
        "hinh_hoc": _bam(hinh_hoc.replace(MENH_DE_KHOA_DUNG, "", 1)),
    }, sort_keys=True))
