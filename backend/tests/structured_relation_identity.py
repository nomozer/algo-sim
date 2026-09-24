# -*- coding: utf-8 -*-
"""Bằng chứng MÁY KIỂM ĐƯỢC: băm `analyze_schema` đổi CHỈ vì ô `geometric_relations`.

`FACT_GRAPH_CONTRACT_EXTENSION` (2026-09-20) thêm vào lược đồ `analyze` của MIỀN
HÌNH HỌC đúng một thuộc tính cấp cao — `geometric_relations`. Thành phần
`analyze_schema` của `semantic_environment_fingerprint` băm GỘP lược đồ Tin học
và lược đồ hình học, nên nó đổi, kéo theo ô ghim danh tính của mọi lượt đo đã
đóng (thesis-final, V3).

Những ô ấy KHÔNG được sửa artifact cho khớp — luật `spec §7.4`. Module này DỰNG
LẠI băm lịch sử từ lược đồ HIỆN TẠI, chỉ bỏ đúng thuộc tính ấy đi. Khớp ⇒ mọi
enum, mọi mô tả, mọi trường khác của CẢ HAI lược đồ giữ nguyên từng byte, và
lược đồ Tin học không bị chạm.

Cùng khuôn với `grammar_card_identity.py` và `photo_problem_identity.py`. Không
phải file test (không có tiền tố `test_`);
`test_structured_geometry_relations.py::test_V_*` khoá nó, kèm phép tiêm cho
thấy nó đỏ được.
"""

from __future__ import annotations

import json

#: Thuộc tính cấp cao wave thêm vào lược đồ `analyze` của miền hình học.
O_QUAN_HE = "geometric_relations"

#: `runtime_identity._bam` của
#: `git show e043ca6:backend/app/ai/skills/geometry_analyze.md` — bản TRƯỚC khi
#: wave thêm mục `## geometric_relations`.
GEOMETRY_ANALYZE_TAI_E043CA6 = (
    "bd7af7185aefb49cf3965bfd8ba55131ed1bd7447d9a346c1ff58d0f5415a665")

#: `semantic_environment_fingerprint()["analyze_schema"]` tại `e043ca6` — trùng
#: `cache_identity.lock.json` trước wave và `ANALYZE_SCHEMA_HASH` của con dấu
#: thesis-final/V3.
ANALYZE_SCHEMA_TRUOC_WAVE = (
    "515001b503af5c7c3fcd28826fc1f32f14bf4d31edbc09365bdbf9aafbb512d3")


def analyze_schema_neu_chua_them_quan_he() -> str:
    """Băm `analyze_schema` của hệ HIỆN TẠI nếu ô quan hệ chưa được thêm.

    Dùng ĐÚNG công thức của `runtime_identity.semantic_environment_fingerprint`
    — băm `json.dumps([tin_hoc, hinh_hoc], ensure_ascii=False, sort_keys=True)`.
    Chép một công thức thứ hai ở đây thì bằng chứng sẽ đúng cho một thứ không ai
    dùng.
    """
    from app.runtime_identity import _bam
    from app.simulation.semantic_program.analyze_contract import (
        SEMANTIC_ANALYZE_SCHEMA,
        analyze_schema_for,
    )

    hh = analyze_schema_for("hinh_hoc")
    assert O_QUAN_HE in hh["properties"], "ô quan hệ không còn ở đó — bằng chứng vô nghĩa"
    assert O_QUAN_HE not in SEMANTIC_ANALYZE_SCHEMA["properties"], (
        "lược đồ Tin học KHÔNG được mang ô hình học")

    truoc = dict(hh)
    truoc["properties"] = {k: v for k, v in hh["properties"].items()
                           if k not in (O_QUAN_HE, "solid_topology")}
    return _bam(json.dumps([SEMANTIC_ANALYZE_SCHEMA, truoc],
                           ensure_ascii=False, sort_keys=True))


def prompts_neu_chua_them_muc_quan_he(bam_transcribe: str | None = None) -> str:
    """Băm `prompts` của hệ HIỆN TẠI nếu `geometry_analyze.md` chưa thêm mục ấy.

    Ghép với `photo_problem_identity`: hai wave khác nhau đã sửa hai prompt khác
    nhau, và băm `prompts` gộp MỌI skill, nên phải áp CẢ HAI phép hoàn nguyên
    cùng lúc thì mới dựng lại được một giá trị lịch sử.

    `bam_transcribe` chọn mốc của `transcribe.md`; mặc định là `085cae6`. Tham
    số hoá vì kho có ba mốc lịch sử của tệp ấy, và mỗi mốc cho một băm `prompts`
    khác nhau mà các test danh tính đang ghim.
    """
    from app.runtime_identity import _bam, skill_fingerprint

    from tests.photo_problem_identity import TRANSCRIBE_TAI_085CAE6

    tren_dia = dict(skill_fingerprint()["tren_dia"])
    assert "geometry_analyze" in tren_dia, "không còn skill ấy — bằng chứng vô nghĩa"
    assert tren_dia["geometry_analyze"] != GEOMETRY_ANALYZE_TAI_E043CA6, (
        "prompt chưa đổi — bằng chứng vô nghĩa")
    tren_dia["geometry_analyze"] = GEOMETRY_ANALYZE_TAI_E043CA6
    tren_dia["transcribe"] = bam_transcribe or TRANSCRIBE_TAI_085CAE6
    return _bam(json.dumps(tren_dia, sort_keys=True))


#: `runtime_identity._bam` của
#: `git show eeacd67:backend/app/ai/skills/geometry_analyze.md` — bản TRƯỚC khi
#: `ANALYZE_DEFINITIONAL_NORMALIZATION_PROMPT_FIX` thêm luật chuẩn hoá theo
#: định nghĩa. 5311 byte.
GEOMETRY_ANALYZE_TAI_EEACD67 = (
    "5746c5e5804c9f3df0618602ad5b78c2c3d1f5f227b4e4cfa630d04d7c61e004")

#: `cache_identity.lock.json["components"]["prompts"]` trước wave ấy.
PROMPTS_TRUOC_LUAT_CHUAN_HOA = (
    "d157c6e10f9c6b31907be24ed610a6fdd365d0e4a3c94269ea576950268088f3")


def prompts_neu_chua_them_luat_chuan_hoa() -> str:
    """Băm `prompts` của hệ HIỆN TẠI nếu chưa thêm luật chuẩn hoá theo định nghĩa.

    `ANALYZE_DEFINITIONAL_NORMALIZATION_PROMPT_FIX` (2026-09-21) sửa ĐÚNG MỘT
    tệp skill. Dựng lại được `d157c6e1…` chỉ bằng cách trả băm tệp ấy về mốc
    `eeacd67` ⇒ **không skill nào khác bị chạm** — và đó là điều duy nhất phép
    kiểm này khẳng định.

    Khác `prompts_neu_chua_them_muc_quan_he` ở mốc: hàm kia lùi về `e043ca6`
    (trước cả ô `geometric_relations`), hàm này lùi đúng MỘT wave.
    """
    from app.runtime_identity import _bam, skill_fingerprint

    tren_dia = dict(skill_fingerprint()["tren_dia"])
    assert "geometry_analyze" in tren_dia, "không còn skill ấy — bằng chứng vô nghĩa"
    assert tren_dia["geometry_analyze"] != GEOMETRY_ANALYZE_TAI_EEACD67, (
        "prompt chưa đổi — bằng chứng vô nghĩa")
    tren_dia["geometry_analyze"] = GEOMETRY_ANALYZE_TAI_EEACD67
    return _bam(json.dumps(tren_dia, sort_keys=True))
