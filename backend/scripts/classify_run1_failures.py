# -*- coding: utf-8 -*-
"""Phân loại từng lỗi Pydantic của các ca trượt thẩm định ở SEALED #1, đối chiếu
với bốn biên chuẩn hoá hiện có. **0 API call.**

VÌ SAO TỒN TẠI: sau lượt #1, mã đổi ở bốn lớp cách viết. Câu hỏi *"bốn bản vá
ấy đáng giá bao nhiêu"* trước đây chỉ trả lời được bằng cách tiêu 520 lượt LLM
cho lượt #2. Nhưng `sealed_cases.json` giữ **nguyên văn khối lỗi Pydantic** của
từng ca, mà khối ấy liệt kê ĐỦ mọi lỗi của chương trình — nên phân loại cơ học
từng lỗi là đủ để biết ca nào nay qua được tầng cú pháp.

Đây là CHẨN ĐOÁN, không phải phép đo:

- Nó nói **chạm tới cổng kế**, KHÔNG nói chạy đúng. Qua Pydantic rồi còn
  `validate_semantic_program` (tầng ngữ nghĩa) → interpreter → C₁a → C₁b → C₂.
- Nó chạy trên **40 ca đã lộ**, nên con số ở đây **không bao giờ** được trình
  bày như kết quả held-out. Số held-out chỉ đến từ SEALED #2.
- Ca hỏng vì lỗi parse (JSON cụt) không kết luận được: không có khối lỗi để đọc.

    python backend/scripts/classify_run1_failures.py
    python backend/scripts/classify_run1_failures.py --json
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

_KQ = (
    Path(__file__).resolve().parents[2]
    / "docs" / "evaluation" / "semantic-benchmark" / "results" / "sealed_cases.json"
)

#: Dạng biểu thức MANG ĐƯỢC bool — `canonical_condition` chỉ gấp đúng những kind
#: này. `arith`/`length`/`neighbors` KHÔNG nằm đây vì `2+3` làm điều kiện là lỗi
#: KIỂU thật, không phải lỗi ký pháp.
BOOL_KINDS = frozenset({"var", "field", "index", "map_get", "literal"})


def tach_loi(reason: str) -> list[tuple[str, str]] | None:
    """Khối lỗi Pydantic → danh sách `(đường_dẫn, mô_tả)`.

    `None` khi không phải lỗi schema (JSON hỏng / cụt) — phân biệt với `[]` là
    "có khối lỗi nhưng rỗng", vì hai thứ đó dẫn tới hai kết luận khác nhau.
    """
    phan = reason.split("for SemanticProgramSpec", 1)
    if len(phan) < 2:
        return None
    ra: list[tuple[str, str]] = []
    duong_dan: str | None = None
    for dong in phan[1].splitlines():
        if not dong.strip():
            continue
        if not dong.startswith(" "):
            duong_dan = dong.strip()
        elif duong_dan and "For further information" not in dong:
            ra.append((duong_dan, dong.strip()))
            duong_dan = None
    return ra


def phan_loai(duong_dan: str, mo_ta: str) -> str:
    """Một lỗi → tên biên đã gộp (`GOP:…`) hoặc lý do vẫn trượt (`TRUOT:…`)."""
    if duong_dan == "spec_version" and "input_value=1.0" in mo_ta:
        return "GOP:spec_version"

    if (duong_dan.endswith(".container")
            and "string_type" in mo_ta and "'kind': 'var'" in mo_ta):
        return "GOP:container_var"

    if duong_dan.endswith(".step") and ("int_type" in mo_ta or "'kind': 'literal'" in mo_ta):
        return "GOP:step_literal"

    if ".condition" in duong_dan and "union_tag_invalid" in mo_ta:
        m = re.search(r"Input tag '([^']+)'", mo_ta)
        if m and m.group(1) in BOOL_KINDS:
            return "GOP:condition_bool"
        return f"TRUOT:condition_kind_la_{m.group(1) if m else '?'}"

    if "str" in mo_ta and "container" in duong_dan and "string_type" not in mo_ta:
        return "GOP:str_container"

    if "union_tag_invalid" in mo_ta:
        m = re.search(r"Input tag '([^']+)'", mo_ta)
        return f"TRUOT:kind_bia_ra_{m.group(1) if m else '?'}"

    if duong_dan.endswith(".field") and "literal_error" in mo_ta:
        return "TRUOT:field_ngoai_left_right_val_data"

    if "Field required" in mo_ta:
        return "TRUOT:thieu_truong_bat_buoc"

    return "TRUOT:khac"


def chay() -> dict:
    ds = json.loads(_KQ.read_text(encoding="utf-8"))
    qua, van_truot, khong_ket_luan = [], [], []
    lop_gop, ly_do_truot = collections.Counter(), collections.Counter()

    for c in ds:
        s = c.get("semantic") or {}
        if s.get("error_code") != "semantic_program_invalid":
            continue
        loi = tach_loi(s.get("reason") or "")
        if not loi:
            khong_ket_luan.append(c["case_id"])
            continue
        nhan = [phan_loai(p, m) for p, m in loi]
        for n in nhan:
            (lop_gop if n.startswith("GOP:") else ly_do_truot)[n] += 1
        if all(n.startswith("GOP:") for n in nhan):
            qua.append(c["case_id"])
        else:
            van_truot.append(
                {"case_id": c["case_id"],
                 "ly_do": sorted({n for n in nhan if n.startswith("TRUOT:")})}
            )

    return {
        "khai": "CHẨN ĐOÁN trên 40 ca ĐÃ LỘ — không phải số held-out. Nói 'chạm "
                "tới cổng kế', KHÔNG nói chạy đúng.",
        "nguon": str(_KQ.relative_to(_KQ.parents[4])),
        "tong_truot_tham_dinh": len(qua) + len(van_truot) + len(khong_ket_luan),
        "nay_qua_tang_pydantic": len(qua),
        "van_truot": len(van_truot),
        "khong_ket_luan_duoc": len(khong_ket_luan),
        "case_qua": qua,
        "case_van_truot": van_truot,
        "case_khong_ket_luan": khong_ket_luan,
        "lop_da_gop_dem_theo_loi": dict(lop_gop.most_common()),
        "ly_do_van_truot": dict(ly_do_truot.most_common()),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true", help="in JSON thay vì bảng")
    a = p.parse_args()
    r = chay()

    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0

    print("=" * 68)
    print("Ca trượt thẩm định ở SEALED #1 — soi bằng hợp đồng HIỆN TẠI")
    print("=" * 68)
    print(f"\n  tổng trượt thẩm định                  {r['tong_truot_tham_dinh']:3}")
    print(f"  mọi lỗi đã gộp → qua tầng Pydantic    {r['nay_qua_tang_pydantic']:3}")
    print(f"  còn lỗi ngoài bốn biên → vẫn trượt    {r['van_truot']:3}")
    print(f"  lỗi parse, không kết luận được        {r['khong_ket_luan_duoc']:3}")

    print("\n--- lớp đã gộp (đếm theo LỖI, không phải ca) ---")
    for k, v in r["lop_da_gop_dem_theo_loi"].items():
        print(f"  {v:3}  {k}")

    print("\n--- vì sao ba ca kia VẪN trượt ---")
    for k, v in r["ly_do_van_truot"].items():
        print(f"  {v:3}  {k}")
    for c in r["case_van_truot"]:
        print(f"       {c['case_id']:16} {c['ly_do']}")

    if r["case_khong_ket_luan"]:
        print(f"\n--- không kết luận được ---\n       {r['case_khong_ket_luan']}")

    print("\n⚠️  Qua Pydantic mới là CHẠM cổng kế. Sau đó còn "
          "validate_semantic_program → interpreter → C₁a → C₁b → C₂.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
