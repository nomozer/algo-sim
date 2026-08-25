# -*- coding: utf-8 -*-
"""Rút + NIÊM PHONG tập held-out hình học. **0 API call.**

    python scripts/seal_geometry_holdout.py --seed <SỐ CỦA GVHD> [--n 10]

Giao thức đầy đủ: `docs/evaluation/geometry/HOLDOUT_PROTOCOL.md`.

─── VÌ SAO SEED PHẢI ĐẾN TỪ NGƯỜI NGOÀI ────────────────────────────────────

Rút tất định từ một seed nghe rất khách quan, nhưng nếu **tôi** chọn seed thì
tôi chọn được cả tập: chạy thử vài seed rồi lấy cái cho điểm đẹp nhất. Seed do
GVHD cho là thứ duy nhất làm phép rút trở nên độc lập, và script này **không có
seed mặc định** — thiếu là dừng, không tự sinh.

─── VÌ SAO PHÂN TẦNG, KHÔNG RÚT NGẪU NHIÊN THUẦN ──────────────────────────

Đề thi có rất nhiều bài thể tích/khoảng cách và rất ít bài thiết diện. Rút thuần
dễ ra một tập toàn thể tích — điểm cao mà không nói được gì.

Tầng hai (chủ đề NGOÀI phủ) **không phải để lấy điểm**: nó kiểm hệ gặp đề ngoài
khả năng thì **nói thẳng là không diễn đạt được** hay **bịa một hình gần giống**.
Hai tầng chấm bằng hai thang khác nhau, không gộp.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

GOC = Path(__file__).resolve().parents[2]
GEO = GOC / "docs" / "evaluation" / "geometry"
POOL = GEO / "holdout" / "pool.json"
SEAL = GEO / "holdout" / "HOLDOUT_SEAL.json"

#: Số bài mỗi tầng. Tổng mặc định 10.
TANG_MAC_DINH = {"trong_phu": 7, "ngoai_phu": 3}


def _bam(x) -> str:
    """Băm NỘI DUNG, chuẩn hoá CRLF→LF.

    Cùng lý do `freeze_evaluation_candidate.bam_noi_dung`: con dấu phải giống
    nhau trên mọi máy, và Windows sẽ lặng lẽ đổi cách xuống dòng khi Git chạm
    file — làm con dấu lệch mà nội dung không đổi một chữ.
    """
    s = json.dumps(x, ensure_ascii=False, sort_keys=True).replace("\r\n", "\n")
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, required=True,
                   help="SỐ NGUYÊN DO GVHD CHO. Không có mặc định — cố ý.")
    p.add_argument("--n", type=int, default=10)
    a = p.parse_args()

    if not POOL.exists():
        print(f"Chưa có pool: {POOL}")
        print("Soạn pool trước — xem HOLDOUT_PROTOCOL.md §3①. Pool phải trích")
        print("từ NGUỒN CÔNG KHAI và mang ĐÁP ÁN CHÍNH THỨC, không phải đáp án")
        print("do hệ tính ra.")
        return 2
    if SEAL.exists():
        # Niêm phong lại là làm hỏng chính thứ con dấu bảo đảm. Muốn đổi tập
        # thì phải nói ra, không được lặng lẽ ghi đè.
        print(f"ĐÃ NIÊM PHONG rồi: {SEAL}")
        print("Rút lại tập held-out sau khi đã thấy kết quả là VI PHẠM giao thức.")
        return 1

    pool = json.loads(POOL.read_text(encoding="utf-8"))["cases"]
    trong = [c for c in pool if c.get("trong_phu") is True]
    ngoai = [c for c in pool if c.get("trong_phu") is False]

    can = dict(TANG_MAC_DINH)
    if a.n != 10:
        can["trong_phu"] = max(1, round(a.n * 0.7))
        can["ngoai_phu"] = a.n - can["trong_phu"]
    thieu = [t for t, k in can.items()
             if len({"trong_phu": trong, "ngoai_phu": ngoai}[t]) < k]
    if thieu:
        print(f"Pool không đủ cho tầng: {thieu} "
              f"(có {len(trong)} trong phủ / {len(ngoai)} ngoài phủ)")
        return 2

    r = random.Random(a.seed)
    chon = (r.sample(trong, can["trong_phu"])
            + r.sample(ngoai, can["ngoai_phu"]))
    chon.sort(key=lambda c: c["case_id"])

    seal = {
        "khai": "Tập HELD-OUT đã niêm phong. Chạy MỘT LƯỢT. Sửa hệ rồi chạy "
                "lại trên chính tập này thì nó THÀNH DEV — và phải nói ra.",
        "seed": a.seed,
        "nguon_seed": "GVHD",
        "niem_phong_luc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pool_hash": _bam(pool),
        "pool_size": len(pool),
        "n": len(chon),
        "phan_tang": can,
        "case_ids": [c["case_id"] for c in chon],
        "seal_hash": _bam(chon),
    }
    SEAL.parent.mkdir(parents=True, exist_ok=True)
    SEAL.write_text(json.dumps(seal, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    (SEAL.parent / "cases.json").write_text(
        json.dumps({"khai": seal["khai"], "seal_hash": seal["seal_hash"],
                    "cases": chon}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    print(f"Đã niêm phong {len(chon)} bài · seed {a.seed}")
    print(f"  seal_hash {seal['seal_hash'][:16]}…")
    print(f"  {seal['case_ids']}")
    print("\nBƯỚC TIẾP: COMMIT con dấu TRƯỚC khi chạy. Không có con dấu trong")
    print("lịch sử thì không chứng minh được tập không bị sửa sau khi thấy kết quả.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
