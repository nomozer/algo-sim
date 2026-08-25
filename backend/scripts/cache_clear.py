# -*- coding: utf-8 -*-
"""Xoá cache phân tích đề. **0 API call.**

    python scripts/cache_clear.py --liet-ke
    python scripts/cache_clear.py --de "Cho hình chóp S.ABCD…"
    python scripts/cache_clear.py --cu          # mọi row KHÁC CACHE_VERSION hiện tại
    python scripts/cache_clear.py --tat-ca

─── VÌ SAO CẦN MỘT CÔNG CỤ RIÊNG ──────────────────────────────────────────

Có **bốn** tầng giữ "bản cũ", và chúng gỡ bằng bốn cách khác nhau:

    ① module Python đã import   →  restart, hoặc DEV_RELOAD=1
    ② `gemini._skill_cache`     →  restart (cùng lệnh với ①)
    ③ cache exact ở Postgres    →  ← ĐÂY. restart KHÔNG chạm tới nó.
    ④ history localStorage (FE) →  mở phiên mới, đừng mở lại phiên cũ

Tầng ③ là tầng lừa người nhất: sửa mã xong, restart xong, gửi **lại đúng đề cũ**
và vẫn nhận y nguyên kết quả cũ — vì khoá cache là *(text đề đã chuẩn hoá +
`CACHE_VERSION`)*, không dính dáng gì tới mã nguồn. Không lỗi, không cảnh báo.

`CACHE_VERSION` là đường chính thức để vô hiệu hoá cache khi ĐỔI PROMPT hoặc
CHÍNH SÁCH ĐỊNH TUYẾN, và luật ấy vẫn đứng — bump là một tuyên bố về hợp đồng,
đọc được trong lịch sử. Script này dành cho việc khác: **thử đi thử lại một đề
trong lúc đang sửa**, nơi bump số cho mỗi lần lưu file là vô nghĩa.

⚠️ Xoá cache là xoá **kết quả đã trả cho người học**, không phải xoá file tạm.
Nên `--tat-ca` phải gõ thêm `--toi-chac-chan`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--liet-ke", action="store_true",
                   help="Chỉ xem, không xoá.")
    g.add_argument("--de", help="Xoá đúng một đề (khớp CHÍNH XÁC text đã lưu).")
    g.add_argument("--cu", action="store_true",
                   help="Xoá mọi row có policy_version KHÁC bản hiện tại.")
    g.add_argument("--tat-ca", action="store_true")
    p.add_argument("--toi-chac-chan", action="store_true",
                   help="Bắt buộc kèm --tat-ca.")
    a = p.parse_args()

    from app.main import CACHE_VERSION, _cache_key
    from app.persistence.db import SessionLocal, SimulationCache, init_db

    init_db()
    with SessionLocal() as s:
        if a.liet_ke:
            rows = s.query(SimulationCache).all()
            print(f"{len(rows)} row · CACHE_VERSION hiện tại = {CACHE_VERSION}")
            for r in rows:
                dau = "  " if r.policy_version == CACHE_VERSION else "cũ"
                print(f" {dau} [{r.policy_version}] {r.simulation_id or '—':<28} "
                      f"hit={r.hit_count} · {(r.problem_text or '')[:70]}")
            return 0

        if a.de:
            n = s.query(SimulationCache).filter_by(key=_cache_key(a.de)).delete()
            if n == 0:
                # Khoá băm theo text ĐÃ CHUẨN HOÁ — lệch một dấu cách là lệch
                # khoá. Nói ra, đừng để người dùng tưởng đã xoá.
                print("Không khớp row nào. Khoá băm theo text đã chuẩn hoá — "
                      "chép lại ĐÚNG đề (dùng --liet-ke để xem bản đã lưu).")
        elif a.cu:
            n = (s.query(SimulationCache)
                 .filter(SimulationCache.policy_version != CACHE_VERSION)
                 .delete(synchronize_session=False))
        else:
            if not a.toi_chac_chan:
                print("--tat-ca xoá KẾT QUẢ ĐÃ TRẢ CHO NGƯỜI HỌC. "
                      "Gõ thêm --toi-chac-chan nếu thật sự muốn.")
                return 2
            n = s.query(SimulationCache).delete()
        s.commit()
        print(f"Đã xoá {n} row.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
