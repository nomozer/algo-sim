# -*- coding: utf-8 -*-
"""Chạy đánh giá LIVE với Gemini thật (M7 §7, M7.14T).

BẮT BUỘC OPT-IN — không có ALLOW_LIVE_AI=1 thì ABORT trước call đầu tiên:

    ALLOW_LIVE_AI=1 python -m app.evaluation.live --suite smoke
    ALLOW_LIVE_AI=1 python -m app.evaluation.live --suite full --max-api-calls 150

Cần GEMINI_API_KEY (đọc từ backend/.env hoặc biến môi trường). KHÔNG chạy
trong CI. Chỉ sau lệnh này mới có metric AI composition THẬT (§8).

Chính sách chạy live (docs/CORRECTNESS.md §8 / CLAUDE.md): thay đổi UI/CSS/
viewport → KHÔNG cần live; engine/validator tất định → offline trước, live có
mục tiêu nếu chạm hợp đồng AI; prompt/schema/classifier → smoke; kết thúc
milestone lớn/lấy số liệu → full. Không chạy full theo thói quen.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from app.persistence.db import init_db  # noqa: F401 (đảm bảo .env được nạp qua db module)
from app.ai import gemini
from app.ai.gemini import ApiBudget
from app.evaluation.datasets import POOLS, get_pool
from app.evaluation.harness import format_report, run_eval, select_suite

SUITES = ("smoke", "full", "boundary", "smoke_v2", "flagship", "L3", "system_flow", "m10_route", "m11_compose", "m12_scan", "m13_soundness", "m14_sorting", "m15_wave1", "m16_offline", "m16_catalog_live")
DATASETS = tuple(sorted(POOLS))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m app.evaluation.live",
        description="Đánh giá AI composition với Gemini THẬT (cần ALLOW_LIVE_AI=1).",
    )
    p.add_argument("--dataset", choices=DATASETS, default="regression",
                   help="regression (mặc định — 30 case lịch sử, ĐÓNG BĂNG) | curriculum | "
                        "capability | cross_domain | thesis (bộ flagship)")
    p.add_argument("--suite", choices=SUITES, default="smoke",
                   help="full (toàn bộ pool) | hoặc lọc theo tag: smoke | boundary | "
                        "smoke_v2 | flagship | L3 | system_flow")
    p.add_argument("--max-cases", type=int, default=None, help="Chỉ chạy N đề đầu của suite.")
    p.add_argument("--case", default=None,
                   help="Chỉ chạy ĐÚNG MỘT đề theo id (rerun có mục tiêu sau vá — M15 T11).")
    p.add_argument("--max-api-calls", type=int, default=None,
                   help="Trần request HTTP thật; chạm trần → dừng sạch và vẫn in report.")
    p.add_argument("--max-retries", type=int, default=None,
                   help="Trần retry TRANSIENT (429/5xx) mỗi call. KHÔNG đụng 3 lần retry "
                        "validation của pipeline (đó là ngữ nghĩa sản phẩm).")
    return p.parse_args(argv)


async def _main(args: argparse.Namespace) -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CHƯA có GEMINI_API_KEY — không thể chạy live evaluation.")
        print("Tạo backend/.env với GEMINI_API_KEY=<key> rồi chạy lại.")
        return 1

    pool = get_pool(args.dataset)
    items = select_suite(args.suite, pool)
    if args.case is not None:
        items = [it for it in items if it.id == args.case]
    if args.max_cases is not None:
        items = items[: max(0, args.max_cases)]
    if not items:
        print(f"Dataset '{args.dataset}' + suite '{args.suite}': không có đề nào.")
        return 1

    budget = ApiBudget(
        max_api_calls=args.max_api_calls,
        max_attempts=(args.max_retries + 1) if args.max_retries is not None else None,
    )
    gemini.set_budget(budget)
    print(f"Dataset '{args.dataset}' · suite '{args.suite}': {len(items)} đề với Gemini THẬT "
          f"(trần API: {args.max_api_calls or 'không giới hạn'})...\n")
    try:
        report = await run_eval(items, api_key, budget=budget)
    finally:
        gemini.set_budget(None)  # không để trần rò sang tiến trình khác

    print(format_report(report))
    return 2 if report.aborted_reason else 0


def main(argv: list[str] | None = None) -> int:
    # OPT-IN CỨNG (M7.14T §6): không có cờ thì DỪNG, không phải cảnh báo rồi chạy.
    if os.getenv("ALLOW_LIVE_AI") != "1":
        print("TỪ CHỐI: live evaluation gọi Gemini THẬT (tốn quota).")
        print("Chạy lại với opt-in tường minh, ví dụ:")
        print("    ALLOW_LIVE_AI=1 python -m app.evaluation.live --suite smoke")
        return 1
    return asyncio.run(_main(_parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
