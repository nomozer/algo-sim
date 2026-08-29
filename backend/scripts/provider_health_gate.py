# -*- coding: utf-8 -*-
"""CỔNG SỨC KHOẺ NHÀ CUNG CẤP — đúng MỘT request, KHÔNG retry. **1 API call.**

    ALLOW_LIVE_AI=1 python scripts/provider_health_gate.py

Trả lời đúng ba câu, trước khi tiêu bất kỳ đồng quota nào cho geometry:
credential còn hợp lệ · quota/credit dùng được · model gọi tới được.

─── VÌ SAO KHÔNG RETRY Ở ĐÂY ─────────────────────────────────────────────

Thang retry transport (`MAX_ATTEMPTS = 4`) tồn tại để nuốt sự cố NHẤT THỜI
của một lượt đo thật. Ở cổng này nó phản tác dụng: `429 credits depleted`
không phải nhất thời, nên bốn lần thử chỉ nhân bốn cái giá của một câu trả
lời đã biết — đo được ở lượt canary trước, 3 lượt logic × 4 HTTP = 12
request cho đúng một thông tin.

Nên cổng này ép `ApiBudget(max_attempts=1)`: một request, một câu trả lời.

─── CỐ Ý KHÔNG DÙNG SCHEMA, KHÔNG DÙNG SKILL ─────────────────────────────

Prompt ngắn nhất có thể và không kèm `responseSchema`. Mục tiêu là kiểm
ĐƯỜNG TRUYỀN, không kiểm khả năng — trộn hai thứ thì một lỗi schema sẽ đọc
ra như một lỗi credential.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


async def _chay() -> int:
    from app.ai import gemini, telemetry

    telemetry.reset_usage()
    # MỘT lần thử. Không nhân bốn cái giá của một câu trả lời đã biết.
    bd = gemini.ApiBudget(max_api_calls=2, max_logical_calls=1, max_attempts=1)
    gemini.set_budget(bd)
    try:
        raw = await gemini.call_gemini(
            os.environ["GEMINI_API_KEY"],
            "Trả lời đúng một từ.",
            "Nói: ok",
            None,
            0.2,
        )
        ok, loi = True, None
    except Exception as e:  # noqa: BLE001 — cổng sức khoẻ, muốn thấy cả sự cố
        raw, ok, loi = None, False, f"{type(e).__name__}: {e}"
    finally:
        gemini.set_budget(None)

    dung = telemetry.usage_report()
    tong = {"prompt_tokens": 0, "candidates_tokens": 0,
            "thoughts_tokens": 0, "total_tokens": 0}
    for chang in dung.values():
        for k in tong:
            tong[k] += int(chang.get(k) or 0)

    print(f"MODEL              : {gemini.MODEL}")
    print(f"HTTP_CALLS         : {bd.http_requests}")
    print(f"LOGICAL_CALLS      : {bd.logical_calls}")
    print(f"transient hits     : {bd.transient_hits}")
    print(f"PROVIDER_READY     : {'YES' if ok else 'NO'}")
    if ok:
        print(f"đáp ứng            : {str(raw)[:80]}")
        for k, v in tong.items():
            print(f"{k:<19}: {v}")
    else:
        print(f"lý do              : {str(loi)[:200]}")
    (BACKEND.parent / "docs" / "evaluation" / "geometry" / "wave1-canary"
     ).mkdir(parents=True, exist_ok=True)
    (BACKEND.parent / "docs" / "evaluation" / "geometry" / "wave1-canary"
     / "PROVIDER_HEALTH.json").write_text(json.dumps({
         "model": gemini.MODEL, "provider_ready": ok,
         "http_calls": bd.http_requests, "logical_calls": bd.logical_calls,
         "transient_hits": bd.transient_hits,
         "token": tong, "loi": loi,
     }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if ok else 2


def main() -> int:
    if os.environ.get("ALLOW_LIVE_AI") != "1":
        print("Thiếu ALLOW_LIVE_AI=1 — cổng này tiêu ĐÚNG MỘT call thật.")
        return 2
    try:
        from dotenv import load_dotenv
        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass
    if not os.environ.get("GEMINI_API_KEY"):
        print("PROVIDER_READY: NO — thiếu GEMINI_API_KEY")
        return 2
    return asyncio.run(_chay())


if __name__ == "__main__":
    raise SystemExit(main())
