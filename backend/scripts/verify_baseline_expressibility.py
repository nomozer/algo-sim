# -*- coding: utf-8 -*-
"""§5 — `EXISTING_IR_EXPRESSIBLE` là một PHÉP ĐO, không phải một lời khai.

    lời giải chuẩn tắc (người viết) → validator → thẩm định tĩnh
        → grounding → thực thi → đối chiếu ORACLE TÍNH TAY

**0 API call.** Chạy TRƯỚC khi gọi model.

─── VÌ SAO ĐIỀU NÀY QUAN TRỌNG ────────────────────────────────────────────

Matrix xếp mọi ca hỏng là "mô hình kém" vì nó không có cách nào phân biệt

    IR biểu diễn được, mô hình không tìm ra
    IR KHÔNG biểu diễn được

Chạy được lời giải chuẩn tắc trước là cách biến phân biệt ấy thành dữ liệu.
Sau lượt live, một ca hỏng có lời giải chuẩn tắc XANH là
`EXISTING_IR_SYNTHESIS_FAILURE`; một ca hỏng mà chính lời giải chuẩn tắc cũng
đỏ là lỗi THIẾT KẾ PHÉP ĐO của ta, và phải khai như thế.

─── HAI NGUỒN CHO MỖI ORACLE ──────────────────────────────────────────────

`dap_so` tính tay và kết quả chạy kernel là hai nguồn ĐỘC LẬP. Script này đòi
chúng khớp. Một nguồn thì chỉ là một lần gõ phím; hai nguồn khớp nhau mới là
một con số.
"""
from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
GOC = BE.parent

from app.simulation.geometry.radical import Radical, radical  # noqa: E402
from app.simulation.semantic_program.grounding_gate import (  # noqa: E402
    check_grounding,
)
from app.simulation.semantic_program.interpreter import (  # noqa: E402
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.ir_static_check import kiem_tinh  # noqa: E402
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)
from scripts.clean_baseline_cases import CASES, check_contamination  # noqa: E402


def mong_doi(dap_so):
    loai, v = dap_so
    return Fraction(v) if loai == "rational" else radical(v[0], v[1])


def bang(a, b) -> bool:
    if a is None or b is None:
        return False
    if isinstance(a, Radical) or isinstance(b, Radical):
        return a == b
    try:
        return Fraction(a) == Fraction(b)
    except (TypeError, ValueError):
        return False


def kiem_mot(case: dict) -> dict:
    ghi = {"id": case["id"], "topology": case["topology"],
           "capability_mix": case["capability_mix"],
           "obligation_count": case["obligation_count"]}
    v = validate_semantic_program(case["chuan_tac"])
    ghi["validator"] = v.ok
    if not v.ok:
        return {**ghi, "expressible": False, "loi": v.error}

    t = kiem_tinh(v.spec)
    ghi["static"] = t.ok
    if not t.ok:
        return {**ghi, "expressible": False, "loi": t.phan_hoi()[:300]}

    # Grounding với ĐỀ BÀI — cổng trung thực bật thật, đúng như lượt live.
    g = check_grounding(RequestContract(problem_text=case["de"]), v.spec)
    ghi["grounding"] = g.ok
    if not g.ok:
        return {**ghi, "expressible": False,
                "loi": f"[{g.error_code}] " + "; ".join(g.unresolved[:3])}

    try:
        kq = SemanticProgramInterpreter().execute(v.spec)
    except Exception as e:  # noqa: BLE001
        return {**ghi, "expressible": False, "loi": f"{type(e).__name__}: {e}"}

    mem = kq.final_memory
    ghi["trace_steps"] = kq.total_steps
    ok = True
    for khoa, nhan in (("dap_so", "oracle"), ("dap_so_phu", "oracle_phu")):
        if khoa not in case:
            continue
        mong = mong_doi(case[khoa])
        khop = [k for k, val in mem.items() if bang(val, mong)]
        ghi[nhan] = str(mong)
        ghi[f"{nhan}_khop"] = khop
        ok = ok and bool(khop)
    return {**ghi, "expressible": ok,
            "loi": None if ok else "chạy được nhưng KHÔNG khớp oracle tính tay"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", type=Path)
    a = p.parse_args()

    nhiem = check_contamination()
    print(f"━━ NHIỄM CHÉO ━━\n  "
          f"{'SẠCH' if not nhiem else 'CÓ TRÙNG:'}")
    for x in nhiem:
        print(f"    · {x}")

    ket = [kiem_mot(c) for c in CASES]
    print(f"\n━━ §5 EXISTING_IR_EXPRESSIBLE — chạy lời giải chuẩn tắc ━━\n")
    print(f"{'đề':34s} {'val':>4s} {'stat':>5s} {'grnd':>5s} {'bước':>5s}  "
          f"oracle")
    print("─" * 92)
    for r in ket:
        print(f"{r['id']:34s} {str(r.get('validator')):>4s} "
              f"{str(r.get('static')):>5s} {str(r.get('grounding')):>5s} "
              f"{str(r.get('trace_steps', '')):>5s}  "
              f"{r.get('oracle', '')}"
              + (f" + {r['oracle_phu']}" if r.get("oracle_phu") else "")
              + ("" if r["expressible"] else f"   ✗ {r['loi']}"))
    n = sum(1 for r in ket if r["expressible"])
    print(f"\nEXISTING_IR_EXPRESSIBLE: {n}/{len(ket)}")
    ok = n == len(ket) and not nhiem

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(
            {"khai": "§5 — lời giải chuẩn tắc do NGƯỜI viết, chạy qua đúng "
                     "chuỗi cổng của sản phẩm, đối chiếu oracle tính tay. "
                     "KHÔNG gửi cho model, KHÔNG tính là thành công. "
                     "0 API call.",
             "nhiem_cheo": nhiem, "expressible": f"{n}/{len(ket)}",
             "cases": ket}, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")
        print(f"→ {a.json}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
