# -*- coding: utf-8 -*-
"""Cổng ĐÓNG BĂNG TẬP KỲ VỌNG — chạy TRƯỚC `seal`. **0 API call.**

    python scripts/freeze_expectation_check.py            # kiểm
    python scripts/freeze_expectation_check.py --bam      # in băm cho con dấu

─── VÌ SAO CẦN MỘT CỔNG RIÊNG ────────────────────────────────────────────

`geometry_expectations.nap()` kiểm được **một mình file kỳ vọng**: người phán
là ai, có `ly_do` cho từng nghĩa vụ không, ô `A*` có `oracle_ref` không. Nó
**không** kiểm được thứ chỉ lộ ra khi đặt cạnh `pool.json`:

    · bài trong pool mà KHÔNG có kỳ vọng  ⇒ chấm bằng tập rỗng ⇒ luôn trượt
    · kỳ vọng cho bài KHÔNG có trong pool ⇒ kỳ vọng mồ côi
    · `problem_text` LỆCH giữa hai file   ⇒ không biết bản nào được đo
    · nghĩa vụ kiểm không khớp `BANG_O`   ⇒ hoặc đề vào nhầm ô, hoặc kỳ vọng sai
    · nghĩa vụ DỰNG lẫn vào tập KIỂM      ⇒ đúng lỗi mà Phase 7A.2 đi tách

Cả năm đều **không sửa được sau khi niêm phong**, nên phải đỏ được từ trước.

─── VÀ VÌ SAO NÓ KHÔNG PHẢI MỘT PHẦN CỦA `seal` ──────────────────────────

`seal` cần chạy **một lần**, đúng lúc, với seed của GVHD. Cổng này thì cần
chạy **sau mỗi lô** trong lúc soạn — trộn hai nhịp ấy vào một lệnh nghĩa là
muốn kiểm kỳ vọng thì phải tiêu một seed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
GEO = GOC / "docs" / "evaluation" / "geometry"
KY_VONG = GEO / "expectations" / "holdout.json"
POOL = GEO / "holdout" / "pool.json"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        f"_fec_{ten}", Path(__file__).resolve().parent / f"{ten}.py")
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def bam_ky_vong() -> str:
    if not KY_VONG.exists():
        return "THIẾU_FILE"
    return hashlib.sha256(
        KY_VONG.read_text(encoding="utf-8").replace("\r\n", "\n").encode()
    ).hexdigest()


def kiem(ky_vong: dict, pool_cases: list[dict], SH, GE) -> list[str]:
    """Trả danh sách lỗi. Rỗng ⇒ tập kỳ vọng đủ điều kiện đóng băng."""
    loi: list[str] = []
    kv = {c["case_id"]: c for c in ky_vong.get("cases") or []}
    nhan = {c["case_id"]: c for c in pool_cases
            if c.get("status", "accepted") == "accepted"}

    # ① Bài được rút PHẢI có kỳ vọng. Thiếu ⇒ chấm bằng tập rỗng ⇒ luôn trượt,
    #    và cái trượt ấy vào báo cáo thành "mô hình sai".
    for ma in sorted(set(nhan) - set(kv)):
        loi.append(f"{ma}: có trong pool (`accepted`) mà KHÔNG có kỳ vọng")
    # ② Kỳ vọng mồ côi — soạn cho một bài không ai đo.
    for ma in sorted(set(kv) - set(nhan)):
        loi.append(f"{ma}: có kỳ vọng mà KHÔNG có bài `accepted` nào trong pool")

    for ma in sorted(set(kv) & set(nhan)):
        k, p = kv[ma], nhan[ma]
        o = k.get("slot")
        # ③ Ô phải khớp giữa hai file.
        if o != p.get("slot"):
            loi.append(f"{ma}: ô LỆCH — pool `{p.get('slot')}` vs kỳ vọng `{o}`")
        # ④ Nghĩa vụ kiểm của ô A* phải chứa nghĩa vụ mà BANG_O gán.
        if str(o).startswith("A"):
            can = SH.BANG_O.get(o, (None,))[0]
            if can and can not in GE.kinds_kiem(k):
                loi.append(f"{ma}: ô {o} đòi nghĩa vụ kiểm `{can}`, kỳ vọng "
                           f"khai {GE.kinds_kiem(k)}")
        # ⑤ HAI TẬP KHÔNG ĐƯỢC TRỘN — cổng chống quay lại lỗi 7A.2.
        for v in k.get("construction_obligations") or []:
            if v.get("ten_trong_de") in GE.kinds_kiem(k):
                loi.append(f"{ma}: vật dựng `{v['ten_trong_de']}` đang mang tên "
                           "một nghĩa vụ KIỂM — hai tập bị trộn")

    # ⑥ Con trỏ oracle trỏ vào chỗ có thật, và đề không lệch giữa hai file.
    loi += GE.kiem_noi_oracle(ky_vong, pool_cases)
    return loi


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bam", action="store_true", help="Chỉ in băm rồi thoát")
    a = p.parse_args()

    if a.bam:
        print(bam_ky_vong())
        return 0

    if not KY_VONG.exists():
        print(f"⛔ CHƯA CÓ {KY_VONG}")
        print("   Tập kỳ vọng chỉ soạn được SAU khi pool có bài `accepted` —")
        print("   soạn trước là soạn kỳ vọng cho những bài chưa biết có nhận")
        print("   được không. Xem HOLDOUT_PROTOCOL §2b.")
        return 2

    GE, SH = _nap("geometry_expectations"), _nap("seal_geometry_holdout")
    try:
        kv = GE.nap("holdout")
    except (ValueError, FileNotFoundError) as e:
        print(f"⛔ KỲ VỌNG KHÔNG NẠP ĐƯỢC: {e}")
        return 2

    pool = (json.loads(POOL.read_text(encoding="utf-8")).get("cases") or []
            if POOL.exists() else [])
    loi = kiem(kv, pool, SH, GE)
    nhan = sum(1 for c in pool if c.get("status", "accepted") == "accepted")
    print(f"pool `accepted`: {nhan} · kỳ vọng: {len(kv.get('cases') or [])}")
    print(f"người phán     : {kv['nguoi_danh_gia'].get('loai')} — "
          f"{kv['nguoi_danh_gia'].get('ai')}")
    if loi:
        print(f"\n⛔ {len(loi)} LỖI — chưa đóng băng được:")
        for d in loi:
            print("   ·", d)
        return 2
    print(f"\n✅ ĐỦ ĐIỀU KIỆN ĐÓNG BĂNG · expectation_hash = {bam_ky_vong()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
