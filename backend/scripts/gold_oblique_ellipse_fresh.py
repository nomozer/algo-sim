# -*- coding: utf-8 -*-
"""Đề + oracle + gold cho `OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION`.

Câu hỏi đo: **pipeline sản phẩm — analyze + synthesis + vòng sửa — có TỰ tìm
ra `intersect_plane_curved_ellipse` trên một đề elip xiên MỚI không?**

Wave trước (`CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_CYLINDER_ELLIPSE_
FOUNDATION`) chứng minh **hệ** diễn đạt và tính đúng. Wave này hỏi câu còn lại,
và chỉ câu ấy: **mô hình** có dùng được năng lực vừa mở không.

─── ORACLE ────────────────────────────────────────────────────────────────

    n = (2, 0, −1)   u = (0, 0, 20)   r = 4
    b² = r²                        = 16          ⇒ b = 4
    a² = r²|n|²|u|²/(n·u)²  = 16·5·400/400 = 80  ⇒ a = 4√5
    S  = π√(a²b²) = π√1280                       = 16√5π
    tâm = trục ∩ (α) = (0, 0, 10)
    nửa trục dọc² = r²(|n|²|u|² − (n·u)²)/(n·u)² = 64 ⇒ z ∈ [2, 18] ⊂ [0, 20]

─── ĐỀ KHÁC HAI ĐỀ TRƯỚC Ở MỘT ĐIỂM CÓ CHỦ ĐÍCH ──────────────────────────

Nó cho **toạ độ tường minh** và cho mặt phẳng bằng **phương trình**, thay vì
cho ba điểm có tên. Đó là cách SGK phát biểu lớp bài này, và nó hỏi thêm một
câu mà hai đề trước không hỏi: mô hình có dựng nổi một mặt phẳng từ phương
trình bằng IR hiện có không — IR **không** có phép `plane_from_equation`.
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
      / "oblique-ellipse-fresh-confirmation")

CASE_ID = "cylinder_oblique_ellipse_area"

PROBLEM_TEXT = (
    "Trong hệ trục Oxyz, cho hình trụ tròn xoay có tâm đáy dưới O(0,0,0), tâm "
    "đáy trên O'(0,0,20) và bán kính đáy bằng 4. Mặt phẳng (α): 2x - z + 10 = "
    "0 cắt hình trụ theo một elip (E) nằm hoàn toàn giữa hai đáy. Tính diện "
    "tích elip (E)."
)

#: ⚠️ Oracle sống ở BỘ CHẤM, không đi vào payload gửi cho model.
ORACLE = {
    "center": "(0, 0, 10)",
    "minor_semiaxis": "4",
    "major_semiaxis": "4√5",
    "area": "16√5π",
    "area_display": "16π√5",
    "z_range": "[2, 18]",
    "dan_xuat": "b² = r² = 16 · a² = r²|n|²|u|²/(n·u)² = 80 · S = π√(a²b²) = 16√5π",
}

WITNESS = "dien_tich_E"
CONTAINER = "(E)"

#: Hợp đồng cho **GOLD PREFLIGHT** — dựng tay, 0 lượt gọi. Lượt live KHÔNG
#: dùng cái này: nó lấy hợp đồng từ `analyze` thật.
REQUEST_CONTRACT_GOLD = {
    "problem_text": PROBLEM_TEXT,
    "input_facts": [
        {"fact_id": "tam_day_duoi", "label": "Tâm đáy dưới O(0,0,0)",
         "values": ["O", "(0,0,0)"], "provenance": "confirmed"},
        {"fact_id": "tam_day_tren", "label": "Tâm đáy trên O'(0,0,20)",
         "values": ["O'", "(0,0,20)"], "provenance": "confirmed"},
        {"fact_id": "ban_kinh_day", "label": "Bán kính đáy hình trụ",
         "values": [4], "provenance": "confirmed"},
        {"fact_id": "mat_phang_alpha",
         "label": "Mặt phẳng (α): 2x - z + 10 = 0",
         "values": ["2x - z + 10 = 0"], "provenance": "confirmed"},
        {"fact_id": "thiet_dien",
         "label": "(α) cắt hình trụ theo elip (E) nằm hoàn toàn giữa hai đáy",
         "values": ["(E)"], "provenance": "confirmed"},
    ],
    "obligations": [
        {"kind": "area", "container": CONTAINER,
         "params": {"witness": WITNESS}},
    ],
}

LY_DO_MP = ("Ba điểm thoả phương trình (α): 2x - z + 10 = 0 — đề cho mặt phẳng "
            "bằng phương trình, và IR dựng mặt phẳng qua ba điểm.")

#: Gold. Ba điểm của `(α)` neo vào chính dữ kiện phương trình:
#: `(0,0,10)` · `(1,0,12)` · `(0,1,10)` đều thoả `2x − z + 10 = 0`.
GOLD = {
    "spec_version": "1.0",
    "title": "Thiết diện elip của hình trụ",
    "description": "Dựng hình trụ, cắt bằng mặt phẳng xiên, đo diện tích elip.",
    "memory_declarations": [
        {"name": "O", "type": "point3", "initial_value": [0, 0, 0],
         "source_fact_id": "tam_day_duoi"},
        {"name": "Oprime", "type": "point3", "initial_value": [0, 0, 20],
         "source_fact_id": "tam_day_tren"},
        {"name": "r", "type": "float", "initial_value": 4,
         "source_fact_id": "ban_kinh_day"},
        {"name": "tru", "type": "curved_solid"},
        {"name": "P1", "type": "point3", "initial_value": [0, 0, 10],
         "source_fact_id": "mat_phang_alpha", "model_assumption": LY_DO_MP},
        {"name": "P2", "type": "point3", "initial_value": [1, 0, 12],
         "source_fact_id": "mat_phang_alpha", "model_assumption": LY_DO_MP},
        {"name": "P3", "type": "point3", "initial_value": [0, 1, 10],
         "source_fact_id": "mat_phang_alpha", "model_assumption": LY_DO_MP},
        {"name": "alpha", "type": "plane3"},
        {"name": "E", "type": "ellipse3"},
        {"name": WITNESS, "type": "float"},
    ],
    "statements": [
        {"kind": "construct_curved_solid", "target_var": "tru",
         "curved_kind": "cylinder", "anchor": "O", "apex_or_top": "Oprime",
         "radius": "r", "label": "Hình trụ"},
        {"kind": "construct_plane", "target_var": "alpha",
         "through": ["P1", "P2", "P3"], "label": "(α)"},
        {"kind": "assign", "target_var": "E",
         "expr": {"kind": "intersect_plane_curved_ellipse", "solid": "tru",
                  "plane": "alpha"}},
        {"kind": "assign", "target_var": WITNESS,
         "expr": {"kind": "measure", "quantity": "area", "of": "E"}},
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
