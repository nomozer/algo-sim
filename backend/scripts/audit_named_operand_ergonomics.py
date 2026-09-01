# -*- coding: utf-8 -*-
"""Ô toán hạng TÊN của IR hình học — dẫn xuất, rồi đối chiếu với lịch sử.

Trả lời hai câu, **0 lượt gọi model**:

  ① Ô nào của IR hình học đòi một TÊN? — dẫn từ `ir_static_check`, không chép
    tay. Thêm một biểu thức là danh sách tự dài ra.
  ② Những lần mô hình LỒNG một biểu thức vào đúng các ô ấy có nâng an toàn
    được không? — đọc chương trình thô trong artifact live đã commit.

Câu ② là điều kiện của §5: nâng chỉ được bật nếu MỌI lần lồng quan sát được
đều thoả bốn tiêu chí an toàn. Một ca không thoả là đủ để dừng.

    .venv/Scripts/python.exe scripts/audit_named_operand_ergonomics.py
    .venv/Scripts/python.exe scripts/audit_named_operand_ergonomics.py --json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.simulation.semantic_program.ir_static_check import (  # noqa: E402
    _CHU_KY, _KIEU_DO, _TOAN_HANG_LENH,
)
from app.simulation.semantic_program.hoisting import (  # noqa: E402
    O_TEN, LY_DO_TU_CHOI, kiem_nang,
)

GOC = pathlib.Path(__file__).resolve().parents[2]
THU_MUC = GOC / "docs" / "evaluation" / "geometry"


def _o_ten_dan_xuat() -> list[dict]:
    """Mọi ô toán hạng NAME<T>, dẫn từ ba bảng thẩm quyền."""
    ra: list[dict] = []
    for k, (thamso, tra) in sorted(_CHU_KY.items()):
        for truong, kieu in thamso:
            ra.append({"nguon": "_CHU_KY", "chu": k, "truong": truong,
                       "kieu": list(kieu), "danh_sach": False, "tra_ve": tra})
    for k, ts in sorted(_TOAN_HANG_LENH.items()):
        for truong, kieu, la_ds in ts:
            ra.append({"nguon": "_TOAN_HANG_LENH", "chu": k, "truong": truong,
                       "kieu": list(kieu), "danh_sach": la_ds, "tra_ve": None})
    for q, (of, wrt) in sorted(_KIEU_DO.items()):
        ra.append({"nguon": "_KIEU_DO", "chu": f"measure[{q}]", "truong": "of",
                   "kieu": list(of), "danh_sach": False, "tra_ve": None})
        if wrt:
            ra.append({"nguon": "_KIEU_DO", "chu": f"measure[{q}]",
                       "truong": "wrt", "kieu": list(wrt),
                       "danh_sach": False, "tra_ve": None})
    return ra


def _chuong_trinh_tho(p: pathlib.Path):
    """Mọi chương trình THÔ (chuỗi JSON model phát ra) trong một artifact."""
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return
    ngan = [d]
    while ngan:
        node = ngan.pop()
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "programs" and isinstance(v, list):
                    for i, s in enumerate(v):
                        if isinstance(s, str):
                            try:
                                yield i, json.loads(s)
                            except ValueError:
                                pass
                else:
                    ngan.append(v)
        elif isinstance(node, list):
            ngan.extend(node)


def quet_lich_su() -> dict:
    """Đếm mọi lần LỒNG biểu thức vào một ô TÊN, trên artifact đã commit."""
    lan = []
    for p in sorted(THU_MUC.rglob("*.json")):
        for chi_muc, spec in _chuong_trinh_tho(p):
            if not isinstance(spec, dict):
                continue
            for hs in kiem_nang(spec):
                lan.append({
                    "artifact": str(p.relative_to(GOC)).replace("\\", "/"),
                    "program_index": chi_muc, **hs,
                })
    dem = {k: sum(1 for x in lan if x["xu_ly"] == k)
           for k in ("HOISTED", "NAME_REF_UNWRAPPED", "REJECTED")}
    return {
        "HISTORICAL_NESTED_EXPR_ATTEMPTS": len(lan),
        # NORMALIZED_SAFELY = mọi lần được đưa về dạng chuẩn tắc, bằng BẤT KỲ
        # cơ chế nào trong hai — nâng thành temp, hoặc gỡ bọc `var`.
        "NORMALIZED_SAFELY": dem["HOISTED"] + dem["NAME_REF_UNWRAPPED"],
        "HOISTED": dem["HOISTED"],
        "NAME_REF_UNWRAPPED": dem["NAME_REF_UNWRAPPED"],
        "STILL_REJECTED": dem["REJECTED"],
        "ly_do_tu_choi": sorted({x["ly_do"] for x in lan
                                 if x["xu_ly"] == "REJECTED"}),
        "lan": lan,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    o = _o_ten_dan_xuat()
    ls = quet_lich_su()
    ra = {
        "NAME_ONLY_OPERAND_AUTHORITY": [
            "ir_static_check._CHU_KY", "ir_static_check._TOAN_HANG_LENH",
            "ir_static_check._KIEU_DO ← measure_contract.BANG_PHEP_DO",
        ],
        "NAME_ONLY_OPERAND_SLOTS": len(o),
        "o": o,
        "O_TEN_RUNTIME": len(O_TEN),
        **ls,
    }
    if ns.json:
        print(json.dumps(ra, ensure_ascii=False, indent=2))
        return 0

    print(f"NAME_ONLY_OPERAND_SLOTS = {len(o)} "
          f"(bộ nâng thấy {len(O_TEN)} ô)")
    nguon = ""
    for s in o:
        if s["nguon"] != nguon:
            nguon = s["nguon"]
            print(f"  ── {nguon}")
        ds = " []" if s["danh_sach"] else ""
        print(f"    {s['chu']}.{s['truong']:12s} "
              f"NAME<{'|'.join(s['kieu'])}>{ds}")

    print(f"\nHISTORICAL_NESTED_EXPR_ATTEMPTS = "
          f"{ls['HISTORICAL_NESTED_EXPR_ATTEMPTS']}")
    print(f"NORMALIZED_SAFELY               = {ls['NORMALIZED_SAFELY']}"
          f"  (nâng {ls['HOISTED']} · gỡ bọc `var` {ls['NAME_REF_UNWRAPPED']})")
    print(f"STILL_REJECTED                  = {ls['STILL_REJECTED']}")
    nhan = {"HOISTED": "nâng   ", "NAME_REF_UNWRAPPED": "gỡ bọc ",
            "REJECTED": "TỪ CHỐI"}
    for x in ls["lan"]:
        print(f"  {nhan[x['xu_ly']]} {x['chu']}.{x['truong']} ← {x['kind_long']} "
              f"[{x['artifact']}#{x['program_index']}]"
              + (f"  {LY_DO_TU_CHOI.get(x['ly_do'], x['ly_do'])}"
                 if x["xu_ly"] == "REJECTED" else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
