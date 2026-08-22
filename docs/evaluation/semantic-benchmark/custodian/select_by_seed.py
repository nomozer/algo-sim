# -*- coding: utf-8 -*-
"""Chọn 40 ID từ pool bằng SEED do GVHD cung cấp — tất định, tái lập được.

Đây là phương án B trong `EXTERNAL_SELECTION_INSTRUCTIONS.md`. Nó tồn tại để
**giảm chủ quan lựa chọn**: GVHD chỉ cần đưa một seed, không cần đọc 89 bài, và
bất kỳ ai cũng chạy lại được để kiểm.

Tất định hoàn toàn: cùng pool fingerprint + cùng seed ⇒ cùng 40 ID. Không dùng
giờ hệ thống, không dùng `random` mặc định không seed.

Script TỪ CHỐI chạy nếu pool fingerprint không khớp file đã đóng băng — chọn
trên một pool đã đổi thì con số tái lập được cũng vô nghĩa.

    python select_by_seed.py --seed 20260823
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
POOL = HERE / "EXTERNAL_SELECTION_POOL.json"
POOL_FP = HERE / "EXTERNAL_SELECTION_POOL_FINGERPRINT.txt"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", required=True, help="seed do GVHD cung cấp")
    p.add_argument("--n", type=int, default=40)
    p.add_argument("--write", action="store_true",
                   help="ghi EXTERNAL_SELECTION.json (mặc định chỉ in ra)")
    a = p.parse_args()

    if not POOL.exists():
        print("Chưa có pool. Chạy build_selection_pool.py trước.", file=sys.stderr)
        return 2
    thuc = hashlib.sha256(POOL.read_bytes()).hexdigest()
    da_dong = POOL_FP.read_text(encoding="utf-8").strip()
    if thuc != da_dong:
        print("POOL ĐÃ ĐỔI so với fingerprint đã đóng băng — không chọn.\n"
              f"  đóng băng: {da_dong}\n  hiện tại : {thuc}", file=sys.stderr)
        return 1

    d = json.loads(POOL.read_text(encoding="utf-8"))
    ids = sorted(r["source_id"] for r in d["records"])
    if len(ids) < a.n:
        print(f"Pool chỉ có {len(ids)} < {a.n}.", file=sys.stderr)
        return 1

    rng = random.Random(f"{thuc}:{a.seed}")
    chon = sorted(rng.sample(ids, a.n))

    payload = {
        "selector_role": "external_GVHD_or_custodian",
        "selection_method": "deterministic_seed",
        "seed": a.seed,
        "selection_count": len(chon),
        "source_universe_fingerprint": d["source_universe_fingerprint"],
        "selection_pool_fingerprint": thuc,
        "source_ids": chon,
    }
    if a.write:
        out = HERE / "EXTERNAL_SELECTION.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        fp = hashlib.sha256(out.read_bytes()).hexdigest()
        (HERE / "EXTERNAL_SELECTION_FINGERPRINT.txt").write_text(
            fp + "\n", encoding="utf-8")
        print(f"Đã ghi {out.name} · fingerprint {fp}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
