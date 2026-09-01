# -*- coding: utf-8 -*-
"""Đồ thị phụ thuộc THẬT giữa các domain mô phỏng. **0 API call.**

`FINAL_THESIS_SCOPE_ALIGNMENT §1`. Luật của cả wave nằm ở một câu: **không xoá
một module vì TÊN nó không phải hình học**. Muốn xoá thì phải chứng minh nó
không còn ai gọi — và "chứng minh" nghĩa là đọc import, registry, route, tham
chiếu frontend và test, chứ không phải đọc tên thư mục.

Phân loại mỗi domain:

    GEOMETRY_CORE        · tuyến hình học đi thẳng qua nó
    SHARED_INFRASTRUCTURE· hình học/semantic nhập từ nó
    LEGACY_ACTIVE        · còn được đăng ký và còn có người ngoài nhập
    LEGACY_UNUSED        · còn đăng ký nhưng KHÔNG ai ngoài nhập
    TEST_ONLY            · chỉ test nhập
    HISTORICAL_ONLY      · không ai nhập, không đăng ký
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

GOC = pathlib.Path(__file__).resolve().parents[2]
SRC = GOC / "frontend" / "src"
DOM = SRC / "simulations" / "domains"

#: Tuyến hình học ở frontend, xác định bằng QUAN SÁT chứ không bằng tên:
#:   · `domains/geometry` — `Scene3DExplorer`, mounted thẳng bởi
#:     `SimulationWorkspace` khi envelope có `scene3d` hợp lệ (KHÔNG qua
#:     registry — đó là lý do nó vắng mặt trong `registerAllSimulations`);
#:   · `domains/semantic` — đăng ký `generic.semantic_program`, đúng
#:     `simulation_id` mà mọi envelope hình học mang.
HAT_NHAN = ("geometry", "semantic")

_IMPORT = re.compile(r"""(?:from|import)\s*\(?\s*["']([^"']+)["']""")


def _ts(p: pathlib.Path):
    return [f for f in p.rglob("*") if f.suffix in (".ts", ".tsx")]


def _la_test(f: pathlib.Path) -> bool:
    return ".test." in f.name or f.name.endswith(".d.mts")


def _giai(f: pathlib.Path, spec: str) -> pathlib.Path | None:
    """Đường dẫn tương đối → file thật (thử các đuôi/`index`)."""
    if not spec.startswith("."):
        return None
    goc = (f.parent / spec).resolve()
    for ung in (goc, *(goc.with_suffix(e) for e in (".ts", ".tsx")),
                goc / "index.ts", goc / "index.tsx"):
        if ung.is_file():
            return ung
    return None


def _domain_cua(f: pathlib.Path) -> str | None:
    try:
        r = f.relative_to(DOM)
    except ValueError:
        return None
    return r.parts[0] if len(r.parts) > 1 else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    doms = sorted(d.name for d in DOM.iterdir() if d.is_dir())
    # ai NHẬP domain X, từ đâu
    nguoi_dung: dict[str, dict[str, set[str]]] = {
        d: {"ngoai_san_pham": set(), "ngoai_test": set(), "domain_khac": set()}
        for d in doms}
    # domain X nhập gì từ NGOÀI thư mục của nó
    nhap_ra: dict[str, set[str]] = {d: set() for d in doms}

    for f in _ts(SRC):
        cua = _domain_cua(f)
        for spec in _IMPORT.findall(f.read_text(encoding="utf-8", errors="ignore")):
            dich = _giai(f, spec)
            if dich is None:
                continue
            d_dich = _domain_cua(dich)
            if d_dich and d_dich != cua:
                khoa = ("ngoai_test" if _la_test(f)
                        else "domain_khac" if cua else "ngoai_san_pham")
                nguoi_dung[d_dich][khoa].add(
                    str(f.relative_to(SRC)).replace("\\", "/"))
            if cua and not d_dich:
                nhap_ra[cua].add(str(dich.relative_to(SRC)).replace("\\", "/"))

    dang_ky = (SRC / "simulations" / "index.ts").read_text(encoding="utf-8")

    ra = {}
    for d in doms:
        u = nguoi_dung[d]
        co_dk = f'domains/{d}' in dang_ky
        nguoi_san_pham = u["ngoai_san_pham"] | u["domain_khac"]
        # Ai trong số người dùng ấy thuộc hạt nhân hình học?
        tu_hat_nhan = {x for x in u["domain_khac"]
                       if x.split("/")[2] in HAT_NHAN}
        if d in HAT_NHAN:
            loai = "GEOMETRY_CORE"
        elif tu_hat_nhan:
            loai = "SHARED_INFRASTRUCTURE"
        elif nguoi_san_pham:
            loai = "LEGACY_ACTIVE"
        elif co_dk:
            loai = "LEGACY_UNUSED"
        elif u["ngoai_test"]:
            loai = "TEST_ONLY"
        else:
            loai = "HISTORICAL_ONLY"
        ra[d] = {
            "loai": loai, "dang_ky": co_dk,
            "files": len(_ts(DOM / d)),
            "nguoi_dung_san_pham": sorted(nguoi_san_pham),
            "nguoi_dung_tu_hat_nhan": sorted(tu_hat_nhan),
            "nguoi_dung_test": len(u["ngoai_test"]),
            "nhap_ha_tang_chung": sorted(nhap_ra[d]),
        }

    if ns.json:
        print(json.dumps(ra, ensure_ascii=False, indent=2))
        return 0

    for d, x in sorted(ra.items(), key=lambda kv: kv[1]["loai"]):
        print(f"{d:12s} {x['loai']:22s} file={x['files']:3d} "
              f"đăng-ký={'✔' if x['dang_ky'] else '·'} "
              f"dùng-bởi-sp={len(x['nguoi_dung_san_pham'])} "
              f"test={x['nguoi_dung_test']}")
        for n in x["nguoi_dung_san_pham"][:4]:
            print(f"               ← {n}")
    print("\nHạ tầng chung mà HẠT NHÂN hình học nhập:")
    for d in HAT_NHAN:
        for m in ra[d]["nhap_ha_tang_chung"]:
            print(f"   {d} → {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
