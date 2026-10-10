# -*- coding: utf-8 -*-
"""Chạy MỌI fixture text → function calls qua `run_function_route` và ghi bằng chứng. offline · **0 API call**.

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/run_text_to_functions_fixtures.py --out-dir <thư mục>

Ghi `<out>/results.json` (mỗi ca: kết cục, mã, đáp số, so với nhãn đăng ký trước, trace, lời gọi) và
`<out>/scenes/<id>.json` cho ca được phục vụ — đầu vào của kiểm biến đổi renderer
(`runs/text-to-geometry-functions/scene_world_metric_check.ts`). Thoát 1 khi một ca lệch nhãn.

`--fixtures <tên tệp trong tests/geometry/fixtures>` chọn bộ fixture (mặc định bộ 27 ca gốc). `--via-fake-gemini`
(run ai-function-route): bọc lời gọi của fixture thành thân phản hồi `generateContent` thật (các phần `functionCall`
song song, `finishReason = STOP`) và chạy qua `app/ai/function_calling.run_ai_function_route` — provider GIẢ, 0 lượt gọi.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
FIXTURES = BACKEND / "tests" / "geometry" / "fixtures" / "text_to_functions_cases.json"


def phan_hoi_gemini_gia(calls: list[dict]) -> dict:
    """Lời gọi của fixture → thân phản hồi `generateContent`: MỘT ứng viên, mọi lời gọi là phần `functionCall` song song."""
    parts = [{"functionCall": {"name": c["fn"], "args": {
        **c["args"], "call_id": c["id"], "quotes": c["source"].get("quotes") or [c["source"]["quote"]],
        **({"depends_on": c["depends_on"]} if c.get("depends_on") else {})}}} for c in calls]
    return {"candidates": [{"content": {"role": "model", "parts": parts}, "finishReason": "STOP"}],
            "usageMetadata": {"note": "provider giả — không có token thật"}}


def main() -> int:
    from app.ai.function_calling import run_ai_function_route, surface_fingerprint
    from app.ai.function_route import run_function_route
    from app.simulation.geometry_functions import ENGINE_VERSION, REGISTRY_VERSION

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out-dir", required=True)
    p.add_argument("--fixtures", default=FIXTURES.name)
    p.add_argument("--via-fake-gemini", action="store_true")
    a = p.parse_args()
    out, fx = Path(a.out_dir), FIXTURES.parent / a.fixtures
    (out / "scenes").mkdir(parents=True, exist_ok=True)
    rows, lech = [], 0
    for c in json.loads(fx.read_text(encoding="utf-8"))["cases"]:
        if a.via_fake_gemini:
            goi = []
            r = run_ai_function_route(c["text"], lambda payload: goi.append(1) or phan_hoi_gemini_gia(c["calls"]))
            assert len(goi) == 1
        else:
            r = run_function_route(c["text"], {"calls": c["calls"]})
        e = c["expect"]
        khop = r.status == e["status"] and (r.code == e.get("code") if r.status == "REFUSED"
                                            else set(r.answers) == set(e["answers"]))
        lech += not khop
        rows.append({"id": c["id"], "group": c["group"], "status": r.status, "code": r.code, "reason": r.reason,
                     "answers": r.answers, "expect": e, "status_and_code_match": khop,
                     "trace": r.trace, "failed_calls": list(r.failed_calls), "n_calls": len(c["calls"]),
                     **({"answer_exact": r.answer_exact, "ai": r.ai} if a.via_fake_gemini else {})})
        if r.scene3d:
            (out / "scenes" / f"{c['id']}.json").write_text(json.dumps(r.scene3d, ensure_ascii=False), encoding="utf-8")
        print(f"{c['id']:<26} {r.status:<8} {r.code or '':<28} {json.dumps(r.answers, ensure_ascii=False)}")
    (out / "results.json").write_text(json.dumps(
        {"engine": ENGINE_VERSION, "registry": REGISTRY_VERSION, "fixtures": str(fx.relative_to(BACKEND.parent)),
         "model_calls": 0, **({"via": "fake Gemini function calling (app/ai/function_calling)",
                               "surface_sha256": surface_fingerprint()} if a.via_fake_gemini else {}),
         "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(rows) - lech}/{len(rows)} khớp kết cục đăng ký trước")
    return 1 if lech else 0


if __name__ == "__main__":
    raise SystemExit(main())
