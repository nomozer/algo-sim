"""Chạy đánh giá LIVE với Gemini thật (M7 §7).

    python -m app.evaluation.live

Cần GEMINI_API_KEY (đọc từ backend/.env hoặc biến môi trường). KHÔNG chạy
trong CI. Chỉ sau lệnh này mới có metric AI composition THẬT (§8).
"""

from __future__ import annotations

import asyncio
import os

from app.persistence.db import init_db  # noqa: F401 (đảm bảo .env được nạp qua db module)
from app.evaluation.harness import DATASET_ITEMS, format_report, run_eval


async def _main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CHƯA có GEMINI_API_KEY — không thể chạy live evaluation.")
        print("Tạo backend/.env với GEMINI_API_KEY=<key> rồi chạy lại.")
        return
    print(f"Đang chạy live evaluation trên {len(DATASET_ITEMS)} đề với Gemini thật...\n")
    report = await run_eval(DATASET_ITEMS, api_key)
    print(format_report(report))


if __name__ == "__main__":
    asyncio.run(_main())
