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
    python select_by_seed.py --seed <seed2> --exclude-measured   # lượt #2

LOẠI TRỪ CHO LƯỢT #2 (`--exclude-measured`, thêm 2026-08-23)
────────────────────────────────────────────────────────────
40 ID của lượt chính thức #1 đã **lộ ra cho người sửa mã**: các lớp lỗi chúng
phơi ra (`spec_version`, `container`, độ sâu lồng…) là thứ đã dẫn dắt bản vá.
Rút lại chính chúng thì tập mới không còn là held-out, và con số đo được sẽ nói
về "hệ đã được vá theo đúng những bài này" chứ không nói về năng lực.

Cờ này đọc `MEASURED_RUN1_IDS.json` (có fingerprint riêng) và loại đúng tập đó,
còn **49 bài chưa từng đo**. Payload ghi lại `excluded_fingerprint` và
`effective_pool_size`, nên phép chọn vẫn tái lập và kiểm được.

⚠️ Cờ này được thêm **TRƯỚC khi biết seed #2** — nếu thêm sau, nó là một tham số
được chỉnh sau khi đã thấy kết quả, tức thao túng phép chọn.
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
DA_DO = HERE / "MEASURED_RUN1_IDS.json"
DA_DO_FP = HERE / "MEASURED_RUN1_IDS_FINGERPRINT.txt"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", required=True, help="seed do GVHD cung cấp")
    p.add_argument("--n", type=int, default=40)
    p.add_argument("--write", action="store_true",
                   help="ghi EXTERNAL_SELECTION.json (mặc định chỉ in ra)")
    p.add_argument("--exclude-measured", action="store_true",
                   help="loại 40 ID đã đo ở lượt #1 (BẮT BUỘC cho lượt #2)")
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

    loai_tru: list[str] = []
    loai_tru_fp = None
    if a.exclude_measured:
        if not DA_DO.exists():
            print(f"Thiếu {DA_DO.name} — không biết bài nào đã đo.", file=sys.stderr)
            return 2
        # Fingerprint kiểm TRƯỚC khi dùng: tập loại trừ mà sửa được im lặng thì
        # "held-out" chỉ còn là lời nói.
        fp_thuc = hashlib.sha256(DA_DO.read_bytes()).hexdigest()
        fp_dong = DA_DO_FP.read_text(encoding="utf-8").strip()
        if fp_thuc != fp_dong:
            print("TẬP ĐÃ ĐO ĐÃ ĐỔI so với fingerprint đã đóng băng — không chọn.\n"
                  f"  đóng băng: {fp_dong}\n  hiện tại : {fp_thuc}", file=sys.stderr)
            return 1
        loai_tru = sorted(json.loads(DA_DO.read_text(encoding="utf-8"))["source_ids"])
        loai_tru_fp = fp_thuc
        con_lai = [i for i in ids if i not in set(loai_tru)]
        print(f"Loại {len(ids) - len(con_lai)} bài đã đo ở lượt #1 · "
              f"còn {len(con_lai)} bài chưa từng đo.", file=sys.stderr)
        ids = con_lai

    if len(ids) < a.n:
        print(f"Pool khả dụng chỉ có {len(ids)} < {a.n}.", file=sys.stderr)
        return 1

    # RNG khoá theo pool fingerprint + seed. Với `--exclude-measured`, KHÔNG GIAN
    # MẪU đã khác nên cùng seed cho tập khác — đó là đúng, và `excluded_fingerprint`
    # dưới đây là thứ nói cho người kiểm biết không gian mẫu nào đã được dùng.
    rng = random.Random(f"{thuc}:{a.seed}")
    chon = sorted(rng.sample(ids, a.n))

    payload = {
        "selector_role": "external_GVHD_or_custodian",
        "selection_method": "deterministic_seed",
        "seed": a.seed,
        "selection_count": len(chon),
        "source_universe_fingerprint": d["source_universe_fingerprint"],
        "selection_pool_fingerprint": thuc,
        "excluded_measured_count": len(loai_tru),
        "excluded_fingerprint": loai_tru_fp,
        "effective_pool_size": len(ids),
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
