# -*- coding: utf-8 -*-
"""AUDIT NGỮ NGHĨA PHÉP ĐO GÓC — bảng sự thật + phạm vi migration. 0 API call.

─── VÌ SAO TỒN TẠI ────────────────────────────────────────────────────────

`fresh-probe fp_5` cho thấy `angle_cos_sq` trả **sin²** cho cặp (đường, mặt)
trong khi trả **cos²** cho ba cặp còn lại. Trước khi sửa phải biết CHÍNH XÁC
hiện trạng — sửa theo trí nhớ là cách đẻ ra một bản vá thứ hai lệch bản đầu.

Script đo trên hình BIẾT TRƯỚC đáp số, không đọc mã. Đo mới phân biệt được
*"tài liệu nói gì"* với *"máy làm gì"*, và cả wave này sinh ra vì hai thứ đó
đã lệch nhau.

─── CA QUYẾT ĐỊNH: 0° ─────────────────────────────────────────────────────

Ở 45° thì cos² = sin² = 1/2, nên ca ấy KHÔNG phân biệt được gì. Ca phân biệt
là đường **nằm trong** mặt: góc = 0°, cos² = 1, sin² = 0. Runtime trả `0`.

Một bộ đo chỉ chạy ca 45° sẽ báo XANH cho đúng con bug này — đó là lý do bảng
dưới đây bắt buộc có ca suy biến.
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

from app.simulation.geometry.exact import Line3, Plane3, Vec3  # noqa: E402
from app.simulation.semantic_program.contract import MeasureExpr  # noqa: E402
from app.simulation.semantic_program.geometry_exec import (  # noqa: E402
    eval_geometry_expr,
)
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)


def _v(x, y, z) -> Vec3:
    return Vec3(Fraction(x), Fraction(y), Fraction(z))


#: Hình mẫu — mọi góc đều biết trước, và mọi giá trị đều hữu tỉ.
HINH = {
    "Ox": Line3(_v(0, 0, 0), _v(1, 0, 0)),
    "Oy": Line3(_v(0, 0, 0), _v(0, 1, 0)),
    "Oz": Line3(_v(0, 0, 0), _v(0, 0, 1)),
    "d45": Line3(_v(0, 0, 0), _v(1, 0, 1)),
    "P": Plane3(_v(0, 0, 0), _v(0, 0, 1)),   # z = 0
    "Q": Plane3(_v(0, 0, 0), _v(1, 0, 1)),   # nghiêng 45° với P
    "u": _v(1, 0, 0),
    "v": _v(1, 0, 1),
    "w": _v(-1, 0, 1),
}

#: (nhãn, of, wrt, góc thật, cos² đúng, sin² đúng)
BO_GOC: list[tuple[str, str, str, str, Fraction, Fraction]] = [
    ("line×line  vuông góc", "Ox", "Oy", "90°", Fraction(0), Fraction(1)),
    ("line×line  45°", "Ox", "d45", "45°", Fraction(1, 2), Fraction(1, 2)),
    ("line×line  trùng phương", "Ox", "Ox", "0°", Fraction(1), Fraction(0)),
    # ↓ CA QUYẾT ĐỊNH — 45° không phân biệt được cos² với sin².
    ("line×plane ĐƯỜNG TRONG MẶT", "Ox", "P", "0°", Fraction(1), Fraction(0)),
    ("line×plane vuông góc mặt", "Oz", "P", "90°", Fraction(0), Fraction(1)),
    ("line×plane 45°", "d45", "P", "45°", Fraction(1, 2), Fraction(1, 2)),
    ("plane×line (đảo thứ tự)", "P", "d45", "45°", Fraction(1, 2), Fraction(1, 2)),
    ("plane×plane 45°", "P", "Q", "45°", Fraction(1, 2), Fraction(1, 2)),
    ("plane×plane trùng", "P", "P", "0°", Fraction(1), Fraction(0)),
]


def bang_su_that() -> list[dict]:
    ra = []
    for nhan, a, b, goc, cos2, sin2 in BO_GOC:
        try:
            v = eval_geometry_expr(
                "measure", MeasureExpr(quantity="angle_cos_sq", of=a, wrt=b),
                HINH)
            loi = None
        except Exception as e:  # noqa: BLE001
            v, loi = None, f"{type(e).__name__}: {e}"
        khop = ("cos²" if v == cos2 and cos2 != sin2 else
                "sin²" if v == sin2 and cos2 != sin2 else
                "KHÔNG PHÂN BIỆT" if cos2 == sin2 else "KHÁC CẢ HAI")
        ra.append({"nhan": nhan, "of": a, "wrt": b, "goc": goc,
                   "runtime": str(v) if loi is None else loi,
                   "cos_sq_dung": str(cos2), "sin_sq_dung": str(sin2),
                   "runtime_thuc_su_la": khop})
    return ra


def _kieu_cua(spec) -> dict[str, str]:
    """Tên → kiểu, gom từ CẢ HAI nguồn.

    ⚠️ `memory_declarations` một mình là KHÔNG ĐỦ, và cái sai ấy suýt cho ra
    một kết luận sạch sẽ nhưng rỗng: `fp_5` dựng `SC_line` bằng
    `construct_line` và `ABC_plane` bằng `construct_plane`, không khai cái nào
    trong `memory_declarations`. Bản quét đầu trả `'?'` cho cả hai và báo
    **0 ca cần migration** — trong khi ca ấy chính là ca sinh ra cả wave.
    """
    from app.simulation.semantic_program.ir_static_check import _KIEU_DUNG

    kieu = {d.name: d.type for d in spec.memory_declarations}
    for st in spec.statements:
        k = _KIEU_DUNG.get(getattr(st, "kind", ""))
        ten = getattr(st, "target_var", None)
        if k and ten:
            kieu.setdefault(ten, k)
        # `declare_point` không nằm trong `_KIEU_DUNG` (nó KHAI, không DỰNG).
        if getattr(st, "kind", "") == "declare_point" and ten:
            kieu.setdefault(ten, "point3")
    return kieu


def _measure_trong(spec) -> list[tuple[str, str, str, str]]:
    """`(quantity, of, wrt, 'kiểuOf×kiểuWrt')` cho mọi `measure` trong spec."""
    kieu = _kieu_cua(spec)
    ra: list[tuple[str, str, str, str]] = []

    def di(x, sau=0):
        if sau > 12 or x is None:
            return
        if getattr(x, "kind", None) == "measure":
            ra.append((x.quantity, x.of, x.wrt or "",
                       f"{kieu.get(x.of, '?')}×{kieu.get(x.wrt, '?')}"))
        for f in ("expr", "left", "right", "val", "index", "second_index"):
            c = getattr(x, f, None)
            if hasattr(c, "kind"):
                di(c, sau + 1)
        for f in ("body", "then_body", "else_body"):
            for c in (getattr(x, f, None) or []):
                di(c, sau + 1)

    for st in spec.statements:
        di(st)
    return ra


def _chuong_trinh_da_luu():
    """Mọi chuỗi JSON trông như một chương trình, trong mọi artifact.

    Khuôn artifact KHÔNG đồng nhất giữa các wave (`cases` có chỗ là list dict,
    có chỗ là list str), nên duyệt phòng thủ và bỏ qua thứ không đọc được —
    một `AttributeError` ở đây sẽ giấu mất đúng ca ta đang tìm.
    """
    for f in sorted(GOC.glob("docs/evaluation/**/*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        cases = d.get("cases") if isinstance(d, dict) else None
        for c in (cases or []):
            if not isinstance(c, dict):
                continue
            for raw in (c.get("programs") or []):
                if not isinstance(raw, str):
                    continue
                try:
                    v = validate_semantic_program(json.loads(raw))
                except Exception:  # noqa: BLE001
                    continue
                if v.ok:
                    yield f, c.get("case_id") or c.get("problem", "?")[:32], v.spec


def pham_vi_migration() -> dict:
    """§8 — chương trình ĐÃ LƯU nào dùng cặp (đường, mặt)?"""
    dinh, tong = [], 0
    for f, cid, spec in _chuong_trinh_da_luu():
        for q, of, wrt, kk in _measure_trong(spec):
            if q != "angle_cos_sq":
                continue
            tong += 1
            if {"line3", "plane3"} <= set(kk.split("×")):
                dinh.append({"file": str(f.relative_to(GOC)), "case": cid,
                             "of": of, "wrt": wrt, "kieu": kk})
    return {"tong_angle_cos_sq": tong, "cap_duong_mat": dinh}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", type=Path)
    a = p.parse_args()

    bang = bang_su_that()
    print("━━ §1 BẢNG SỰ THẬT — `angle_cos_sq` trả gì, đo trên hình biết "
          "trước ━━\n")
    print(f"{'toán hạng':28s} {'góc':>4s} {'runtime':>8s} {'cos²':>6s} "
          f"{'sin²':>6s}  thực sự là")
    print("─" * 86)
    for r in bang:
        print(f"{r['nhan']:28s} {r['goc']:>4s} {r['runtime']:>8s} "
              f"{r['cos_sq_dung']:>6s} {r['sin_sq_dung']:>6s}  "
              f"{r['runtime_thuc_su_la']}")

    print("\n━━ `angle_cos` (có dấu, chỉ vector3) ━━")
    ky = []
    for x, y, mong in (("u", "v", "cos45 = √2/2"), ("u", "w", "cos135 = −√2/2")):
        val = eval_geometry_expr(
            "measure", MeasureExpr(quantity="angle_cos", of=x, wrt=y), HINH)
        ky.append({"of": x, "wrt": y, "runtime": str(val), "mong": mong})
        print(f"  {x}·{y} → {val}   (mong {mong})")

    mig = pham_vi_migration()
    print(f"\n━━ §8 PHẠM VI MIGRATION ━━")
    print(f"  {mig['tong_angle_cos_sq']} lần dùng `angle_cos_sq` trong "
          f"artifact đã lưu")
    print(f"  {len(mig['cap_duong_mat'])} trong số đó là cặp (đường, mặt)")
    for x in mig["cap_duong_mat"]:
        print(f"    · {x['file']} · {x['case']} · {x['of']}×{x['wrt']}")

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(
            {"khai": "Audit ngữ nghĩa phép đo góc — đo trên hình biết trước "
                     "đáp số, KHÔNG đọc mã. Ca quyết định là 0°: ở 45° thì "
                     "cos² = sin² nên không phân biệt được. 0 API call.",
             "bang_su_that": bang, "angle_cos_co_dau": ky,
             "migration": mig}, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")
        print(f"\n→ {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
