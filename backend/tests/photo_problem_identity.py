# -*- coding: utf-8 -*-
"""Bằng chứng MÁY KIỂM ĐƯỢC: băm `prompts` đổi CHỈ vì `skills/transcribe.md`.

PHOTO_PROBLEM_TO_SCENE_END_TO_END_IMPLEMENTATION (2026-09-13) viết lại prompt
ĐỌC ẢNH. Thành phần `prompts` của `semantic_environment_fingerprint` băm GỘP mọi
`skills/*.md`, nên nó đổi — kéo theo mọi ô ghim danh tính của các lượt đo đã
đóng (oblique ellipse, nonconvex, thesis-final).

Những ô ấy KHÔNG được sửa artifact cho khớp, và cũng không được nới bằng lời
*"chỉ prompt ảnh đổi thôi"*. Module này DỰNG LẠI băm lịch sử từ skill hiện tại,
chỉ thay đúng một mục: băm của `transcribe.md` tại `085cae6` (đỉnh trước wave).
Khớp ⇒ mọi skill khác — kể cả toàn bộ prompt TẦNG B — giữ nguyên từng byte, và
không có file skill nào được thêm hay bớt.

Không phải file test (không có tiền tố `test_`); `test_photo_problem_identity.py`
khoá nó, kèm phép tiêm cho thấy nó đỏ được.
"""

from __future__ import annotations

import json

#: `semantic_environment_fingerprint()["prompts"]` tại `085cae6` — trùng giá trị
#: `cache_identity.lock.json` mang trước wave này, và trùng `model_facing.prompts`
#: mà các lượt đo 2026-09-07…09-10 đã ghi.
PROMPTS_TRUOC_WAVE = "55ac1ca6a6df92ce3ad76a3f76b216eced26ecdb4c4370a8c5610d0fd560bb66"

#: `runtime_identity._bam` của `git show 085cae6:backend/app/ai/skills/transcribe.md`.
TRANSCRIBE_TAI_085CAE6 = "b54fbc097ad66295276607a17cc62652adebf70f0804d4dbd1485808ca4aabe3"


#: `semantic_environment_fingerprint()["prompts"]` tại `d8ad614` — giá trị `cache_identity.lock.json` mang
#: trước VISION_DIAGRAM_ONLY_PROVENANCE_GUARD_FIX (2026-09-14), wave sửa luật 4 và 9 của `transcribe.md`.
PROMPTS_TRUOC_PROVENANCE_GUARD = "c50c8c6bb61db67bdd6911f1849fb5b81fe4afea4bd1fc62174ac106ae723588"

#: `runtime_identity._bam` của `git show d8ad614:backend/app/ai/skills/transcribe.md`.
TRANSCRIBE_TAI_D8AD614 = "b499dc7a29fec4a387074b89ccbce393970fdef69348641cff2d60ba850570d6"


def prompts_neu_transcribe_la(bam_transcribe: str) -> str:
    """Băm `prompts` của hệ HIỆN TẠI nếu `transcribe.md` mang băm `bam_transcribe` — mọi skill khác giữ nguyên."""
    from app.runtime_identity import _bam, skill_fingerprint

    tren_dia = dict(skill_fingerprint()["tren_dia"])
    assert "transcribe" in tren_dia, "không còn skill transcribe — bằng chứng vô nghĩa"
    tren_dia["transcribe"] = bam_transcribe
    return _bam(json.dumps(tren_dia, sort_keys=True))


def prompts_neu_transcribe_chua_doi() -> str:
    """Băm `prompts` của hệ HIỆN TẠI nếu `transcribe.md` chưa bị viết lại."""
    return prompts_neu_transcribe_la(TRANSCRIBE_TAI_085CAE6)
