# -*- coding: utf-8 -*-
"""Corpus + hợp đồng CỐ ĐỊNH + gold cho `DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB`.

Câu hỏi đo: **mô hình có hiểu `divide_segment.ratio` là tham số `t` không?**

    kernel:  divide_segment(a, b, t) = a + t·(b − a),  t=0 → a,  t=1 → b
    chia trong đoạn theo m:n  ⇒  t = m/(m+n)

Bốn đề **không cho toạ độ** và đều hỏi một ĐỘ DÀI. Cả hai tính chất là cố ý:
đáp số khi ấy **bất biến với hệ trục** mà mô hình tự chọn, nên oracle không phụ
thuộc vào một quy ước đặt hình nào. Đề ngắn để giữ token thấp.

`request_contract` ở đây là **cố định và đã kiểm** — runner KHÔNG gọi `analyze`
(`ANALYZE_LIVE_CALLS = 0`). Hai arm dùng chung đúng một hợp đồng cho mỗi đề,
nên khác biệt đo được không lẫn nhiễu của tầng trích xuất.

Mỗi ca mang `t_theo_thu_tu`: `t` ĐÚNG cho từng chiều `(a, b)` có thể xảy ra.
Nhờ vậy chấm được *"đúng `t` tương ứng với thứ tự `a`,`b` THỰC TẾ"* thay vì so
với một hằng số giả định chiều.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
RA = BACKEND.parent / "docs" / "evaluation" / "geometry" / "divide-segment-ratio-ab"


def _bam(o) -> str:
    return hashlib.sha256(
        json.dumps(o, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _facts(dau: str, cuoi: str, dai, diem: str, mo_ta_vi_tri: str):
    return [
        {"fact_id": "doan_thang", "label": f"Đoạn thẳng {dau}{cuoi}",
         "values": [f"{dau}{cuoi}"], "provenance": "confirmed"},
        {"fact_id": "do_dai_doan", "label": f"Độ dài đoạn {dau}{cuoi}",
         "values": [dai], "provenance": "confirmed"},
        {"fact_id": "vi_tri_diem", "label": f"Vị trí điểm {diem} trên đoạn {dau}{cuoi}",
         "values": [mo_ta_vi_tri], "provenance": "confirmed"},
    ]


def _gold(dau: str, cuoi: str, dai, diem: str, t: str, wit: str, moc: str):
    """Chương trình GOLD — đi trọn đường sản phẩm, đã kiểm tất định."""
    return {
        "spec_version": "1.0",
        "title": f"Điểm chia đoạn {dau}{cuoi}",
        "description": "Dựng điểm chia đoạn rồi đo khoảng cách.",
        "memory_declarations": [
            {"name": dau, "type": "point3", "initial_value": [0, 0, 0],
             "source_fact_id": "doan_thang"},
            {"name": cuoi, "type": "point3", "initial_value": [dai, 0, 0],
             "source_fact_id": "do_dai_doan"},
            {"name": diem, "type": "point3"},
            {"name": wit, "type": "float"},
        ],
        "statements": [
            {"kind": "construct_point", "target_var": diem,
             "expr": {"kind": "divide_segment", "a": dau, "b": cuoi, "ratio": t}},
            {"kind": "assign", "target_var": wit,
             "expr": {"kind": "measure", "quantity": "distance",
                      "of": diem, "wrt": moc}},
        ],
    }


def _ca(case_id, feature, problem_text, dau, cuoi, dai, diem, mo_ta,
        t_thuan, t_nguoc, wit, moc, dap_so):
    return {
        "case_id": case_id,
        "feature": feature,
        "problem_text": problem_text,
        "diem_duoc_hoi": diem,
        "moc_do": moc,
        "witness": wit,
        #: `t` đúng theo TỪNG chiều `(a, b)`. Chấm đọc chiều thực tế của
        #: chương trình rồi tra bảng này — không giả định mô hình chọn chiều nào.
        "t_theo_thu_tu": {f"{dau}->{cuoi}": t_thuan, f"{cuoi}->{dau}": t_nguoc},
        "exact_expected_results": {wit: dap_so},
        "request_contract": {
            "problem_text": problem_text,
            "input_facts": _facts(dau, cuoi, dai, diem, mo_ta),
            "obligations": [{"kind": "distance", "container": diem,
                             "params": {"witness": wit, "wrt": moc}}],
        },
        "gold": _gold(dau, cuoi, dai, diem, t_thuan, wit, moc),
    }


#: BỐN ĐỀ — ba ca mục tiêu + một đối chứng.
#:
#: `r3` là ca **bất đối xứng**: vị trí cho từ ĐẦU KIA của đoạn, nên `t` phụ
#: thuộc chiều `(a, b)` mà chương trình thật sự viết. Nếu bộ chấm giả định một
#: chiều cố định thì chính ca này sẽ chấm sai.
CORPUS = [
    _ca("r1", "do_dai_tu_dau_doan",
        "Cho đoạn thẳng AB có độ dài 12. Điểm M nằm trên đoạn AB sao cho "
        "AM = 9. Tính độ dài MB.",
        "A", "B", 12, "M", "M thuộc AB và AM = 9",
        "3/4", "1/4", "do_dai_mb", "B", "3"),
    _ca("r2", "ti_so_chia_doan_m_n",
        "Cho đoạn thẳng CD có độ dài 10. Điểm N nằm trên đoạn CD sao cho "
        "CN : ND = 2 : 3. Tính độ dài ND.",
        "C", "D", 10, "N", "N thuộc CD và CN:ND = 2:3",
        "2/5", "3/5", "do_dai_nd", "D", "6"),
    _ca("r3", "huong_bat_doi_xung",
        "Cho đoạn thẳng EF có độ dài 10. Điểm P nằm trên đoạn EF sao cho "
        "FP = 4·PE. Tính độ dài PF.",
        "E", "F", 10, "P", "P thuộc EF và FP = 4·PE",
        "1/5", "4/5", "do_dai_pf", "F", "8"),
    _ca("r4", "doi_chung_trung_diem",
        "Cho đoạn thẳng GH có độ dài 8. Điểm I là trung điểm của GH. "
        "Tính độ dài IH.",
        "G", "H", 8, "I", "I là trung điểm GH",
        "1/2", "1/2", "do_dai_ih", "H", "4"),
]

#: Ca mục tiêu = ba ca đầu; `r4` là ĐỐI CHỨNG (trung điểm — `midpoint` là cách
#: dựng tương đương hợp lệ, và luật quyết định đòi giữ đúng ca này).
CA_MUC_TIEU = ("r1", "r2", "r3")
CA_DOI_CHUNG = "r4"

CORPUS_HASH = _bam([{k: c[k] for k in ("case_id", "feature", "problem_text")}
                    for c in CORPUS])
CONTRACT_HASH = _bam([c["request_contract"] for c in CORPUS])
ORACLE_HASH = _bam([{k: c[k] for k in
                     ("case_id", "t_theo_thu_tu", "exact_expected_results",
                      "diem_duoc_hoi", "moc_do")} for c in CORPUS])
GOLD_HASH = _bam([c["gold"] for c in CORPUS])
