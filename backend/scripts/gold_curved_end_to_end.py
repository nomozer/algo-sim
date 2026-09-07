# -*- coding: utf-8 -*-
"""Đề + oracle + gold cho `CURVED_END_TO_END_FRESH_CONFIRMATION`.

Câu hỏi đo: **Card C — vừa áp dụng sau bốn lượt trên họ ĐOẠN THẲNG — có còn
đứng vững trên một bài HÌNH CONG mới, đi trọn đường sản phẩm (analyze →
synthesis → repair → kiểm chứng → trace → Scene3D) không?**

Khác mọi wave A/B trước ở hai điều, và cả hai là chủ đích:

    ANALYZE_CALLS = 1     hợp đồng do MÔ HÌNH trích, không phải hợp đồng cố định
    REPAIR_LIMIT  = 3     vòng sửa THẬT của sản phẩm, không tắt

Nên phép đo này trả lời được câu mà bốn lượt trước **cố ý** không hỏi: đường
sản phẩm đầy đủ có phục vụ được bài này không.

─── ORACLE ────────────────────────────────────────────────────────────────

    ST : TO = 1 : 2   ⇒  t(S→O) = 1/(1+2) = 1/3
    bán kính nón giảm TUYẾN TÍNH từ 12 ở đáy `O` về 0 ở đỉnh `S`
    T cách `S` một phần ba trục  ⇒  r(c) = 12 × 1/3 = 4

Kiểm chéo bằng toạ độ gold: `O = (0,0,0)`, `S = (0,0,18)` ⇒ `T = (0,0,12)`,
tức cao 12 trên đáy; `r = 12 · (1 − 12/18) = 4`. Hai lối tính, một đáp số.

─── VÌ SAO ĐỀ NÀY ─────────────────────────────────────────────────────────

Nó buộc dùng **cả năm** mảnh mà ba wave gần đây dựng lên, mỗi mảnh đúng một
lần: `radius` của `construct_curved_solid` (bán kính cho bằng SỐ, không có
điểm vành nào được đặt tên — đúng lớp mà `CENTER_RADIUS_CURVED_CONSTRUCTION_
FOUNDATION` mở) · `divide_segment` với `t` quy từ `m:n` (delta ratio của Card
C) · xuất xứ gốc toạ độ (delta xuất xứ của Card C) · `plane_perpendicular_to_
line` · `intersect_plane_curved → circle3 → measure(radius)`.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

RA = (BACKEND.parent / "docs" / "evaluation" / "geometry"
      / "curved-end-to-end-fresh-confirmation")

CASE_ID = "cone_section_r"

PROBLEM_TEXT = (
    "Hình nón có đỉnh S, tâm đáy O, bán kính đáy bằng 12 và chiều cao SO bằng "
    "18. Điểm T nằm trên đoạn SO sao cho ST:TO = 1:2. Mặt phẳng qua T và vuông "
    "góc với SO cắt hình nón theo đường tròn (c). Tính bán kính của đường tròn "
    "(c)."
)

#: Đáp số CHÍNH XÁC, không phải xấp xỉ.
ORACLE = {
    "t_S_den_O": "1/3",
    "ban_kinh_day": "12",
    "chieu_cao": "18",
    "radius_c": "4",
    "dan_xuat": "r(c) = 12 · (ST/SO) = 12 · 1/3 = 4",
}

WITNESS = "ban_kinh_c"
CONTAINER = "(c)"

#: Hợp đồng dùng cho **GOLD PREFLIGHT** — dựng tay, 0 lượt gọi. Lượt live
#: KHÔNG dùng cái này: nó lấy hợp đồng từ `analyze` thật.
REQUEST_CONTRACT_GOLD = {
    "problem_text": PROBLEM_TEXT,
    "input_facts": [
        {"fact_id": "hinh_non",
         "label": "Hình nón đỉnh S, tâm đáy O",
         "values": ["SO"], "provenance": "confirmed"},
        {"fact_id": "ban_kinh_day", "label": "Bán kính đáy hình nón",
         "values": [12], "provenance": "confirmed"},
        {"fact_id": "chieu_cao", "label": "Chiều cao SO",
         "values": [18], "provenance": "confirmed"},
        {"fact_id": "vi_tri_diem",
         "label": "Vị trí điểm T trên đoạn SO",
         "values": ["T thuộc SO và ST:TO = 1:2"], "provenance": "confirmed"},
        {"fact_id": "mp_cat",
         "label": "Mặt phẳng qua T vuông góc SO, cắt nón theo đường tròn (c)",
         "values": ["(c)"], "provenance": "confirmed"},
    ],
    "obligations": [
        {"kind": "radius", "container": CONTAINER,
         "params": {"witness": WITNESS}},
    ],
}

LY_DO_GOC = ("Đặt hệ trục: chọn tâm đáy O làm gốc toạ độ vì đề không cho toạ "
             "độ; trục Oz dọc theo trục SO của hình nón.")

#: Gold — **năm** phép dựng, đúng thứ tự phụ thuộc.
GOLD = {
    "spec_version": "1.0",
    "title": "Thiết diện tròn của hình nón",
    "description": "Dựng nón, cắt bằng mặt phẳng vuông góc trục, đo bán kính.",
    "memory_declarations": [
        {"name": "O", "type": "point3", "initial_value": [0, 0, 0],
         "model_assumption": LY_DO_GOC},
        {"name": "S", "type": "point3", "initial_value": [0, 0, 18],
         "source_fact_id": "chieu_cao"},
        {"name": "r_day", "type": "float", "initial_value": 12,
         "source_fact_id": "ban_kinh_day"},
        {"name": "non", "type": "curved_solid"},
        {"name": "truc_SO", "type": "line3"},
        {"name": "T", "type": "point3"},
        {"name": "mp_cat", "type": "plane3"},
        {"name": "c", "type": "circle3"},
        {"name": WITNESS, "type": "float"},
    ],
    "statements": [
        {"kind": "construct_curved_solid", "target_var": "non",
         "curved_kind": "cone", "anchor": "O", "apex_or_top": "S",
         "radius": "r_day", "label": "Hình nón"},
        {"kind": "construct_line", "target_var": "truc_SO",
         "through_a": "S", "through_b": "O", "label": "Trục SO"},
        {"kind": "construct_point", "target_var": "T",
         "expr": {"kind": "divide_segment", "a": "S", "b": "O",
                  "ratio": "1/3"},
         "label": "Điểm T trên SO"},
        {"kind": "assign", "target_var": "mp_cat",
         "expr": {"kind": "plane_perpendicular_to_line", "point": "T",
                  "line": "truc_SO"}},
        {"kind": "assign", "target_var": "c",
         "expr": {"kind": "intersect_plane_curved", "solid": "non",
                  "plane": "mp_cat"}},
        {"kind": "assign", "target_var": WITNESS,
         "expr": {"kind": "measure", "quantity": "radius", "of": "c"}},
    ],
}


def _bam(o) -> str:
    return hashlib.sha256(
        json.dumps(o, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


PROBLEM_HASH = hashlib.sha256(PROBLEM_TEXT.encode("utf-8")).hexdigest()
ORACLE_HASH = _bam(ORACLE)
CONTRACT_GOLD_HASH = _bam(REQUEST_CONTRACT_GOLD)
GOLD_HASH = _bam(GOLD)
