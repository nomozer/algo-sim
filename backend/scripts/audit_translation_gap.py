# -*- coding: utf-8 -*-
"""§1 — `Q = P + v` có biểu diễn được bằng IR HIỆN TẠI không? 0 API call.

─── VÌ SAO KHÔNG DÙNG "MÔ HÌNH HỎNG" LÀM BẰNG CHỨNG ───────────────────────

`SYNTHESIS_STABILITY_K3` thấy 10 lần mô hình viết
`construct_point X = arith(+, var(P), vector_from_points(A,B))` rồi chết ở
schema. Đó là bằng chứng mô hình MUỐN phép ấy — **không** phải bằng chứng IR
thiếu nó. Hai câu khác nhau, và chỉ câu thứ hai biện minh cho việc thêm một
primitive.

Script này chứng minh câu thứ hai **từ chính văn phạm**, cơ học:

    ① Phép nào SINH RA một điểm?          → đọc `_CHU_KY`, vế phải == point3
    ② Trong số ấy, phép nào NHẬN vectơ?   → đọc vế trái
    ③ Câu lệnh dựng nào nhận vectơ?       → đọc `_TOAN_HANG_LENH`

Nếu ② và ③ đều rỗng thì **không đường nào** đưa một vectơ vào một phép sinh
điểm, nên `Q = P + v` không diễn đạt được — không cần bàn tới chuyện mô hình
giỏi hay kém.

─── ĐƯỜNG VÒNG CUỐI CÙNG, VÀ VÌ SAO NÓ ĐÓNG ───────────────────────────────

Còn một lối trên lý thuyết: dựng đường thẳng qua `P` có phương `v`, rồi lấy
giao hoặc chia đoạn. `construct_line` nhận **hai TÊN ĐIỂM**, không nhận
phương — nên để có đường ấy phải có sẵn một điểm thứ hai trên nó, tức chính
điểm ta đang muốn dựng. Vòng tròn.

Script kiểm luôn điều đó: có câu lệnh nào dựng đường/mặt từ MỘT điểm + MỘT
vectơ không.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))

from app.simulation.semantic_program.ir_static_check import (  # noqa: E402
    _CHU_KY,
    _TOAN_HANG_LENH,
    DIEM,
    DUONG,
    MAT,
    VECTO,
)


def audit() -> dict:
    sinh_diem = {k: v for k, v in _CHU_KY.items() if v[1] == DIEM}
    nhan_vecto_expr = {
        k: [t for t, kieu in v[0] if VECTO in kieu]
        for k, v in _CHU_KY.items() if any(VECTO in kieu for _, kieu in v[0])}
    nhan_vecto_lenh = {
        k: [t for t, kieu, _ in v if VECTO in kieu]
        for k, v in _TOAN_HANG_LENH.items()
        if any(VECTO in kieu for _, kieu, _ in v)}
    # Đường vòng: dựng ĐƯỜNG hay MẶT từ một điểm + một vectơ?
    duong_tu_vecto = {
        k: v for k, v in _TOAN_HANG_LENH.items()
        if any(VECTO in kieu for _, kieu, _ in v)
        and k in ("construct_line", "construct_plane")}
    sinh_duong_mat = {k: v[1] for k, v in _CHU_KY.items()
                      if v[1] in (DUONG, MAT)}
    return {
        "phep_sinh_diem": {k: {"toan_hang": [
            {"truong": t, "kieu": list(kieu)} for t, kieu in v[0]]}
            for k, v in sinh_diem.items()},
        "phep_sinh_diem_NHAN_vecto": {
            k: v for k, v in nhan_vecto_expr.items() if k in sinh_diem},
        "moi_phep_nhan_vecto": nhan_vecto_expr,
        "cau_lenh_nhan_vecto": nhan_vecto_lenh,
        "duong_hoac_mat_tu_vecto": duong_tu_vecto,
        "phep_sinh_duong_hoac_mat": sinh_duong_mat,
        "expressible": bool(
            {k: v for k, v in nhan_vecto_expr.items() if k in sinh_diem}
            or duong_tu_vecto),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", type=Path)
    a = p.parse_args()
    d = audit()

    print("━━ §1 `Q = P + v` — IR HIỆN TẠI có diễn đạt được không? ━━\n")
    print("① Phép SINH RA một điểm và toán hạng của chúng:")
    for k, v in d["phep_sinh_diem"].items():
        th = ", ".join(f"{x['truong']}:{'|'.join(x['kieu'])}"
                       for x in v["toan_hang"])
        print(f"    {k:24s} ({th})")
    print(f"\n② Trong số ấy, phép NHẬN vectơ: "
          f"{d['phep_sinh_diem_NHAN_vecto'] or 'KHÔNG CÓ'}")
    print(f"③ Câu lệnh dựng NHẬN vectơ:      "
          f"{d['cau_lenh_nhan_vecto'] or 'KHÔNG CÓ'}")
    print(f"④ Dựng ĐƯỜNG/MẶT từ điểm + vectơ: "
          f"{d['duong_hoac_mat_tu_vecto'] or 'KHÔNG CÓ'}")
    print(f"\n   (phép nhận vectơ ở nơi KHÁC: {d['moi_phep_nhan_vecto']})")

    print(f"\nCURRENT_IR_TRANSLATION_EXPRESSIBLE: "
          f"{'YES' if d['expressible'] else 'NO'}")
    if not d["expressible"]:
        print("\n  Không phép sinh điểm nào nhận vectơ, và không câu lệnh nào")
        print("  dựng được đường/mặt từ một điểm + một phương. Đường vòng")
        print("  'dựng đường qua P phương v rồi chia đoạn' vì thế ĐÓNG:")
        print("  `construct_line` cần hai TÊN ĐIỂM, tức cần sẵn chính điểm")
        print("  ta đang muốn dựng. Vòng tròn.")
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(
            {"khai": "§1 — chứng minh khoảng trống TỪ VĂN PHẠM, không từ việc "
                     "mô hình hỏng. 0 API call.", **d},
            ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"\n→ {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
