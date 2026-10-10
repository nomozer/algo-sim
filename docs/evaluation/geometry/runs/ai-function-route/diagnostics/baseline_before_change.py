"""Mốc TRƯỚC khi sửa (ai-function-route): chạy fixture tiền đăng ký qua engine của `ba6aedfb`/`99ecb815` (chưa có cổng
nguồn mới, chưa có hàm mới). Ca một quote đổi `quotes` → `quote` (dạng hợp đồng cũ); ca nhiều quote giữ nguyên ⇒ hợp đồng
cũ bác. 0 API call. Chạy từ backend/:  python <tệp này>"""
import json, sys
from pathlib import Path

sys.path.insert(0, ".")
from app.ai.function_route import run_function_route  # noqa: E402

FX = Path("tests/geometry/fixtures")
for f in ("paraphrase_cases.json", "geometry_expansion_cases.json"):
    for c in json.loads((FX / f).read_text(encoding="utf-8"))["cases"]:
        calls = json.loads(json.dumps(c["calls"]))
        for x in calls:
            q = x["source"].get("quotes") or []
            if len(q) == 1:
                x["source"] = {"quote": q[0]}
        r = run_function_route(c["text"], {"calls": calls})
        e = c["expect"]
        khop = r.status == e["status"] and (r.code == e.get("code") if r.status == "REFUSED" else True)
        print(f"{c['id']:<40} expect={e['status']}/{e.get('code') or ''} got={r.status}/{r.code or ''} "
              f"{'MATCH' if khop else 'DIFF'}")
