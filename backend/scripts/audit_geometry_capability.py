# -*- coding: utf-8 -*-
"""SOÁT NĂNG LỰC HÌNH HỌC — chạy thật, **0 API call**.

    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/audit_geometry_capability.py
    … --md          # bảng Markdown cho tài liệu

`GEOMETRY_CURRICULUM_COVERAGE.md §5` đã có một nhật ký đo, nhưng nó chạy trên
`8b4025e`. Chép lại con số ấy vào một bản soát mới là chép một sự thật CŨ —
đúng thứ `RULES` gọi là suy từ tên hàm. File này đo LẠI ở HEAD.

Một năng lực chỉ được gọi là **CÓ** khi đi trọn bốn chặng:

    biểu đạt được → thẩm định qua → CHẠY RA SỐ → kiểm chứng tất định được

Nên phép đo không hỏi *"kernel có hàm ấy không"* mà gọi thẳng **cầu nối IR**
(`geometry_exec._do`, `eval_geometry_expr`) và **checker server-owned** — đúng
hai cửa mà một chương trình do LLM sinh phải đi qua. Kernel có hàm mà cầu nối
không nối thì năng lực ấy KHÔNG tồn tại với hệ, và đó chính là ca
`hp_b01_032` chết ở V3 (*"cặp đối tượng không hợp lệ cho khoảng cách"*) trong
khi `measure.distance_sq_skew_lines` nằm sẵn trong kho.
"""
from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.simulation.geometry.exact import Line3, Plane3, Vec3  # noqa: E402
from app.simulation.semantic_program import geometry_exec as GX  # noqa: E402
from app.simulation.semantic_program.geometry_obligations import (  # noqa: E402
    GEOMETRY_CHECKERS,
)
from app.simulation.semantic_program.obligations import Obligation  # noqa: E402


def F(*x):
    return Vec3(*(Fraction(v) for v in x))


class _Node:
    """Giả một `MeasureExpr` — chỉ ba trường mà `_do` đọc."""

    def __init__(self, quantity, of, wrt=None):
        self.quantity, self.of, self.wrt = quantity, of, wrt


#: Bộ vật mẫu, chọn để MỌI cặp đều hợp lệ về hình học — nếu một cặp hỏng thì
#: đó là cầu nối thiếu, không phải hình suy biến.
def _mem() -> dict:
    A, B, C, D = F(0, 0, 0), F(1, 0, 0), F(0, 1, 0), F(0, 0, 1)
    return {
        "A": A, "B": B, "C": C, "D": D,
        "AB": Line3.through(A, B),
        "CD": Line3.through(C, D),               # chéo với AB
        "AB2": Line3.through(F(0, 1, 0), F(1, 1, 0)),   # song song AB
        "ABC": Plane3.through(A, B, C),
        "ABC2": Plane3.through(F(0, 0, 1), F(1, 0, 1), F(0, 1, 1)),  # ∥ ABC
        "OYZ": Plane3.through(A, C, D),          # cắt ABC theo Oy
        "AC": Line3.through(A, C),               # cắt AB tại A
        # Cặp chéo có khoảng cách HỮU TỈ (= 2). Cặp AB×CD thì VÔ TỈ — giữ cả
        # hai để ma trận nói được cả năng lực lẫn giới hạn của nó.
        "CHEO_HUU_TI": Line3.through(F(0, 0, 2), F(0, 1, 2)),
        "khoi": GX.build_initial("solid", {
            "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]],
            "faces": [[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]],
        }, "khoi"),
    }


#: `(nhãn, quantity, of, wrt)`. Nhãn là TÊN CHƯƠNG TRÌNH THPT của phép đo.
_PHEP_DO = [
    ("khoảng cách điểm–điểm", "distance", "A", "B"),
    ("khoảng cách điểm–đường", "distance", "D", "AB"),
    ("khoảng cách điểm–mặt", "distance", "D", "ABC"),
    ("khoảng cách đường–đường CHÉO (hữu tỉ)", "distance", "AB", "CHEO_HUU_TI"),
    ("khoảng cách đường–đường CHÉO (VÔ TỈ)", "distance", "AB", "CD"),
    ("khoảng cách đường–đường SONG SONG", "distance", "AB", "AB2"),
    ("khoảng cách đường–mặt (∥)", "distance", "AB", "ABC2"),
    ("khoảng cách mặt–mặt (∥)", "distance", "ABC", "ABC2"),
    ("góc đường–đường", "angle_cos_sq", "AB", "CD"),
    ("góc đường–mặt", "angle_cos_sq", "CD", "ABC"),
    ("góc mặt–mặt (nhị diện)", "angle_cos_sq", "ABC", "ABC2"),
    ("thể tích khối", "volume", "khoi", None),
]

#: `(nhãn, kind biểu thức, node)` — phép DỰNG, cửa thứ hai của cầu nối.
_PHEP_DUNG = [
    ("giao đường × mặt", "intersect_line_plane", {"line": "CD", "plane": "ABC"}),
    ("giao mặt × mặt", "intersect_plane_plane", {"plane_a": "ABC",
                                                 "plane_b": "OYZ"}),
    ("giao đường × đường", "intersect_line_line", {"line_a": "AB",
                                                   "line_b": "AC"}),
    ("trung điểm", "midpoint", {"a": "A", "b": "B"}),
    ("chia đoạn theo tỉ lệ", "divide_segment", {"a": "A", "b": "B",
                                                "ratio": "2/3"}),
    ("chiếu vuông góc lên mặt", "project_onto", {"point": "D", "target": "ABC"}),
    ("chiếu vuông góc lên đường", "project_onto", {"point": "C", "target": "AB"}),
    ("chiếu SONG SONG theo phương", "project_parallel", {"point": "D",
                                                         "target": "ABC"}),
    ("cộng / trừ vectơ", "vector_add", {"a": "A", "b": "B"}),
    ("tích vô hướng", "dot", {"a": "A", "b": "B"}),
]


def _thu(fn) -> tuple[str, str]:
    try:
        return "CÓ", str(fn())
    except Exception as e:  # noqa: BLE001 — bản soát, phân loại chứ không ném
        ma = getattr(e, "code", None) or type(e).__name__
        return "KHÔNG", f"{ma}: {str(e)[:70]}"


def do_phep_do() -> list[dict]:
    ra = []
    for nhan, q, of, wrt in _PHEP_DO:
        mem = _mem()
        tt, chi_tiet = _thu(lambda: GX._do(_Node(q, of, wrt), mem))
        ra.append({"nhom": "measure", "nhan": nhan, "trang_thai": tt,
                   "chi_tiet": chi_tiet})
    return ra


def do_phep_dung() -> list[dict]:
    ra = []
    for nhan, kind, truong in _PHEP_DUNG:
        mem = _mem()
        node = type("N", (), truong)()
        tt, chi_tiet = _thu(lambda: GX.eval_geometry_expr(kind, node, mem))
        ra.append({"nhom": "construct", "nhan": nhan, "trang_thai": tt,
                   "chi_tiet": chi_tiet})
    return ra


def do_checker() -> list[dict]:
    """Nghĩa vụ nào có checker TẤT ĐỊNH — cửa `kiểm chứng được`."""
    return [{"nhom": "checker", "nhan": k, "trang_thai": "CÓ",
             "chi_tiet": GEOMETRY_CHECKERS[k].__name__}
            for k in sorted(GEOMETRY_CHECKERS)]


def do_vo_ti() -> dict:
    """Khoảng cách VÔ TỈ — dạng phổ biến nhất của đề thật (`a√3/2`)."""
    mem = _mem()
    tt, chi_tiet = _thu(
        lambda: GX._do(_Node("distance", "B", "C"), mem))   # AB=AC=1 ⇒ BC=√2
    return {"nhom": "exact", "nhan": "khoảng cách VÔ TỈ (√2)",
            "trang_thai": tt, "chi_tiet": chi_tiet}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--md", action="store_true")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    hang = do_phep_do() + do_phep_dung() + [do_vo_ti()] + do_checker()
    if a.json:
        print(json.dumps(hang, ensure_ascii=False, indent=2))
        return 0
    if a.md:
        print("| Nhóm | Năng lực | Cầu nối IR | Chi tiết |")
        print("|---|---|:-:|---|")
        for h in hang:
            dau = "✅" if h["trang_thai"] == "CÓ" else "❌"
            print(f"| {h['nhom']} | {h['nhan']} | {dau} | `{h['chi_tiet'][:64]}` |")
        return 0

    for nhom in ("measure", "construct", "exact", "checker"):
        print(f"\n── {nhom.upper()} ──")
        for h in hang:
            if h["nhom"] != nhom:
                continue
            dau = "✅" if h["trang_thai"] == "CÓ" else "❌"
            print(f"  {dau} {h['nhan']:<36} {h['chi_tiet'][:72]}")
    co = sum(1 for h in hang if h["trang_thai"] == "CÓ" and h["nhom"] != "checker")
    tong = sum(1 for h in hang if h["nhom"] != "checker")
    print(f"\nCẦU NỐI IR: {co}/{tong} năng lực đi trọn tới số.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
