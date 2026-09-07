# -*- coding: utf-8 -*-
"""Đề + oracle + gold cho `NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY`.

Câu hỏi đo, và chỉ câu này: **mô hình có tự viết nổi BẢNG MẶT của một khối
chóp đáy LÕM không?**

`NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION` đã đóng phần hệ — `SYSTEM_EXPRESSIBLE
= YES`, `DETERMINISTICALLY_CORRECT = YES`, `MODEL_DISCOVERABLE = NOT_MEASURED`.
Wave này chỉ trả nốt ô cuối.

─── VÌ SAO ĐỀ CHO THỨ TỰ ĐỈNH MÀ KHÔNG CHO BẢNG MẶT ──────────────────────

Bảng mặt là **thứ đang được đo**. Đề cho *"các đỉnh theo thứ tự quanh biên"* —
đúng như SGK phát biểu — rồi để mô hình tự suy ra rằng một khối chóp gồm một
đáy và năm mặt bên, mỗi mặt bên gồm một cạnh đáy cộng đỉnh `S`. Nếu fixture
đưa sẵn bảng mặt vào prompt thì phép đo hỏi một câu khác hẳn, dễ hơn, và
`MODEL_DISCOVERABLE` sẽ nói về thứ không phải nó.

Đáy lõm ở đúng một đỉnh: `D(3,1,0)` thụt vào giữa `C` và `E`.

─── ORACLE, DẪN ĐỘC LẬP VỚI KERNEL ───────────────────────────────────────

    shoelace ABCDE = ½|Σ (xᵢyᵢ₊₁ − xᵢ₊₁yᵢ)|
                   = ½|0 + 24 + (−6) + 12 + 0| = ½·30 = 15
    h = 9                      (S ở z = 9, đáy nằm trong z = 0)
    V = 15 · 9 / 3 = 45

⚠️ **Hai cách làm mất chỗ lõm cho hai con số KHÁC NHAU**, và cả hai khác `45`
đủ xa để không nhầm được — đo bằng máy, không suy:

    quạt tam giác từ `A` (lấp chỗ lõm)      shoelace 21  ⇒ V = 63
    bao lồi `ABCE` (bỏ hẳn đỉnh `D`)        shoelace 24  ⇒ V = 72

Một chương trình *"đúng hình dạng nhưng làm phẳng chỗ lõm"* lộ ngay ở đáp số,
và **lộ theo hai cách phân biệt được** — nên bộ chấm nói được mô hình đã hỏng
kiểu nào.

⚠️ Mặt bên KHÔNG xuyên qua nhau, và điều đó **phải kiểm** chứ không được coi
là hiển nhiên — nó là điều kiện duy nhất mà bao đóng v1 không soát được. Chứng
minh: mọi tia từ `S` cắt mặt phẳng `z = 0` tại đúng một điểm, nên hai mặt bên
`S-Pᵢ-Pᵢ₊₁` và `S-Pⱼ-Pⱼ₊₁` chỉ gặp nhau ở những điểm mà `PᵢPᵢ₊₁` và `PⱼPⱼ₊₁`
gặp nhau — mà đáy ĐƠN nên hai cạnh chỉ gặp nhau ở đỉnh chung. Vậy khối nằm
TRỌN trong phạm vi đã chứng minh.
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
      / "nonconvex-polyhedron-model-discoverability")

CASE_ID = "nonconvex_pyramid_volume"

PROBLEM_TEXT = (
    "Trong hệ trục Oxyz, cho khối chóp S.ABCDE có đáy ABCDE là một ngũ giác "
    "lõm nằm trong mặt phẳng z = 0. Các đỉnh của đáy theo thứ tự quanh biên "
    "là A(0,0,0), B(6,0,0), C(6,4,0), D(3,1,0), E(0,4,0), và đỉnh của khối "
    "chóp là S(2,2,9). Tính thể tích khối chóp S.ABCDE."
)

#: ⚠️ Oracle sống ở BỘ CHẤM, không đi vào payload gửi cho model.
ORACLE = {
    "base_shoelace_area": "15",
    "height": "9",
    "volume": "45",
    #: Khoá runner đọc để so đáp số. Tên chung, không theo họ hình.
    "dap_so_hien_thi": "45",
    "reflex_vertex": "D(3,1,0)",
    #: Hai cách làm mất chỗ lõm, hai đáp số SAI phân biệt được.
    "fan_trap": "quạt từ A lấp chỗ lõm ⇒ shoelace 21 ⇒ V = 63 (SAI)",
    "convex_hull_trap": "bao lồi ABCE, bỏ hẳn D ⇒ shoelace 24 ⇒ V = 72 (SAI)",
    "dan_xuat": "A = 15 · h = 9 · V = A·h/3 = 45",
    "lateral_faces_disjoint": (
        "mọi tia từ S cắt z=0 đúng một lần ⇒ hai mặt bên chỉ gặp nhau ở đỉnh "
        "chung của hai cạnh đáy kề; đáy ĐƠN ⇒ khối nằm trọn trong bao đóng v1"),
}

WITNESS = "V"
CONTAINER = "S.ABCDE"

#: Thứ tự đỉnh quanh biên — dùng để dựng GOLD và để bộ chấm kiểm bảng mặt của
#: mô hình theo HÌNH HỌC (chấp mọi thứ tự tương đương), không theo chính tả.
DINH_DAY = ["A", "B", "C", "D", "E"]
DINH = DINH_DAY + ["S"]
TOA_DO = {
    "A": [0, 0, 0], "B": [6, 0, 0], "C": [6, 4, 0],
    "D": [3, 1, 0], "E": [0, 4, 0], "S": [2, 2, 9],
}
#: Cạnh đáy dưới dạng cặp KHÔNG hướng — bộ chấm so bằng tập này.
CANH_DAY = frozenset(
    frozenset((DINH_DAY[i], DINH_DAY[(i + 1) % 5])) for i in range(5))

#: Hợp đồng cho **GOLD PREFLIGHT** — dựng tay, 0 lượt gọi. Lượt live KHÔNG
#: dùng cái này: nó lấy hợp đồng từ `analyze` thật.
REQUEST_CONTRACT_GOLD = {
    "problem_text": PROBLEM_TEXT,
    "input_facts": [
        {"fact_id": f"dinh_{t}", "label": f"Đỉnh {t}{tuple(TOA_DO[t])}",
         "values": [t, str(tuple(TOA_DO[t])).replace(" ", "")],
         "provenance": "confirmed"}
        for t in DINH
    ] + [
        {"fact_id": "day_lom",
         "label": "Đáy ABCDE là ngũ giác LÕM, đỉnh theo thứ tự quanh biên",
         "values": ["ABCDE"], "provenance": "confirmed"},
    ],
    "obligations": [
        {"kind": "volume", "container": CONTAINER,
         "params": {"witness": WITNESS}},
    ],
}

#: Gold. Đáy khai NGƯỢC (E→A) cho hướng ra ngoài; năm mặt bên dùng chung `S`.
#: Chiều khai **không** quan trọng — `dinh_huong_bien` tự định hướng lại — và
#: đó chính là điều làm hợp đồng khai mặt dễ cho mô hình.
MAT = [list(reversed(DINH_DAY))] + [
    [DINH_DAY[i], DINH_DAY[(i + 1) % 5], "S"] for i in range(5)]

GOLD = {
    "spec_version": "1.0",
    "title": "Thể tích khối chóp đáy ngũ giác lõm",
    "description": "Dựng khối chóp từ sáu đỉnh và bảng mặt, rồi đo thể tích.",
    "memory_declarations": [
        {"name": t, "type": "point3", "initial_value": TOA_DO[t],
         "source_fact_id": f"dinh_{t}"} for t in DINH
    ] + [
        {"name": "chop", "type": "solid"},
        {"name": WITNESS, "type": "float"},
    ],
    "statements": [
        {"kind": "construct_solid", "target_var": "chop",
         "vertices": DINH, "faces": MAT, "label": "S.ABCDE"},
        {"kind": "assign", "target_var": WITNESS,
         "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}},
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
