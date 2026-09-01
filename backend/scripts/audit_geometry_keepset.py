# -*- coding: utf-8 -*-
"""KEEP SET — module nào THẬT SỰ nằm trên đường sản phẩm hình học. 0 API call.

`LEGACY_INFORMATICS_REMOVAL §1/§14`. Đi đồ thị import từ đúng các điểm vào của
đường sản phẩm, gồm cả `import` nằm TRONG hàm (kho này dùng rất nhiều để cắt
vòng phụ thuộc — một bộ dò chỉ đọc import cấp module sẽ bỏ sót gần hết).

Ba tập, và phân biệt chúng là toàn bộ giá trị của script:

    KEEP    · với tới được từ đường hình học ⇒ **không được xoá**
    LEGACY  · không với tới được, và là mã môn Tin học ⇒ ứng viên xoá
    KHAC    · không với tới được, không thuộc hai loại trên (script, evaluation)

⚠️ "Với tới được" tính theo IMPORT THẬT, không theo tên thư mục. Một module tên
`generic` có thể nằm trong KEEP; một module tên nghe trung tính có thể là
LEGACY. Đó đúng là điều §5 bắt phải kiểm riêng.
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib

BE = pathlib.Path(__file__).resolve().parents[1]
APP = BE / "app"

#: Điểm vào của ĐƯỜNG SẢN PHẨM hình học — nơi một request thật đi vào.
DIEM_VAO = [
    "app.main",                                   # biên API + cổng miền
    "app.simulation.semantic_program.route",      # verify_and_compile
    "app.simulation.semantic_program.scene3d",    # cảnh 3D
]

#: Hàm của `pipeline` thuộc đường hình học. `pipeline` là module CHUNG (cả hai
#: nhánh cùng ở đó), nên nó luôn nằm trong KEEP — nhưng §2 đòi gỡ nhánh Tin học
#: BÊN TRONG nó, và đó là việc riêng, không phải việc của bộ dò này.
HAM_HINH_HOC = ("_chay_duong_hinh_hoc", "_semantic_route_attempt",
                "stage_semantic_analyze", "stage_semantic_program",
                "_dung_scene3d", "_envelope_tu_route_sinh",
                "_that_bai_hinh_hoc")


def _mod_cua(p: pathlib.Path) -> str:
    r = p.relative_to(BE).with_suffix("")
    parts = list(r.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _duong_cua(mod: str) -> pathlib.Path | None:
    r = BE / pathlib.Path(*mod.split("."))
    for ung in (r.with_suffix(".py"), r / "__init__.py"):
        if ung.is_file():
            return ung
    return None


def _nhap_cua(p: pathlib.Path, goc_mod: str) -> set[str]:
    """Mọi module `app.*` mà file này nhập — kể cả import TRONG hàm."""
    ra: set[str] = set()
    try:
        cay = ast.parse(p.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return ra
    goi = goc_mod.split(".")
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith("app."):
                    ra.add(a.name)
        elif isinstance(n, ast.ImportFrom):
            if n.level:                       # `from .x import y`
                nen = goi[:-n.level] if n.level <= len(goi) else []
                ten = ".".join(nen + ([n.module] if n.module else []))
            else:
                ten = n.module or ""
            if not ten.startswith("app."):
                continue
            ra.add(ten)
            # `from app.pkg import mod` — `mod` có thể là MODULE, không phải tên.
            for a in n.names:
                if _duong_cua(f"{ten}.{a.name}"):
                    ra.add(f"{ten}.{a.name}")
    return ra


def keep_set() -> set[str]:
    dat: set[str] = set()
    ngan = list(DIEM_VAO)
    while ngan:
        m = ngan.pop()
        if m in dat:
            continue
        p = _duong_cua(m)
        if p is None:
            continue
        dat.add(m)
        ngan.extend(_nhap_cua(p, m))
    return dat


#: Dấu hiệu mã MÔN TIN HỌC — dùng để PHÂN LOẠI phần ngoài KEEP, không dùng để
#: quyết định xoá (quyết định thuộc về đồ thị import).
DAU_HIEU_TIN_HOC = ("catalog", "dsl", "pattern", "descriptor")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    keep = keep_set()
    moi = {_mod_cua(p) for p in APP.rglob("*.py")
           if "__pycache__" not in p.parts}
    ngoai = sorted(moi - keep)

    legacy = [m for m in ngoai
              if any(t in m.split(".")[-1] or t in m for t in DAU_HIEU_TIN_HOC)]
    khac = [m for m in ngoai if m not in legacy]

    ra = {
        "KEEP_SET": sorted(keep),
        "KEEP_COUNT": len(keep),
        "NGOAI_KEEP": ngoai,
        "UNG_VIEN_LEGACY": legacy,
        "NGOAI_KEEP_KHAC": khac,
    }
    if ns.json:
        print(json.dumps(ra, ensure_ascii=False, indent=2))
        return 0

    print(f"KEEP_SET = {len(keep)} module (với tới được từ đường sản phẩm)")
    print(f"NGOÀI KEEP = {len(ngoai)}\n")
    print("── ứng viên LEGACY (ngoài KEEP, mang dấu hiệu Tin học):")
    for m in legacy:
        print("   ", m)
    print("\n── ngoài KEEP, KHÁC (phải xét riêng, đừng xoá theo tên):")
    for m in khac:
        print("   ", m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
