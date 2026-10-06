# -*- coding: utf-8 -*-
"""regular-square-pyramid-w05 — bằng chứng cho quyết định CACHE_VERSION. 0 lượt gọi model.

Chạy MỌI hàng của corpus chóp đều (lớp W1 + R2 + W05) qua route thật của MỘT cây backend (`<backend>` đứng đầu
`sys.path`), dùng builder chương trình của tệp test HIỆN TẠI (để hàng W05 có cùng chương trình ở cả hai cây). Ghi
kết cục từng hàng: phục vụ? giá trị? băm cảnh (JSON khoá sắp xếp) — hoặc giai đoạn + mã từ chối.

Cache chỉ giữ phản hồi `status == "ok"`: một hàng phục vụ ở CẢ hai cây mà băm cảnh khác ⇒ hàng cache cũ trả payload
cũ ⇒ phải bump. Hàng từ chối → phục vụ không làm cache cũ sai (từ chối không được cache).

usage: python proof_cache_rows_w05.py <backend dir> <current test_regular_square_pyramid.py> <out.json>
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

BACKEND = Path(sys.argv[1]).resolve()
TEST = Path(sys.argv[2]).resolve()
OUT = Path(sys.argv[3])
sys.path.insert(0, str(BACKEND))

spec = importlib.util.spec_from_file_location("rsp_cases_w05", TEST)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

#: Hàng CHẨN ĐOÁN (không phải nhãn): đề có chuỗi mà chương trình khai ĐÚNG đoạn đứng cạnh số — dạng duy nhất có thể đã
#: được phục vụ (và cache) trước bản sửa; nếu payload của nó đổi thì cache cũ sai.
_DE_X = ("Cho hình chóp tứ giác đều S.ABCD có AB = BC = 4 và chiều cao bằng 3. "
         "Tính thể tích khối chóp S.ABCD.")
EXTRA = {
    "X_chain_cites_last_member": lambda: m.chop_deu(
        "X", s=m.F(4), h=m.F(3), van=_DE_X, given=(("BC_length", "f_bc", "4"), ("chieu_cao", "f_chieu_cao", "3")),
        facts=(m._f("f_bc", "BC", "4"), m._f("f_chieu_cao", "chiều cao", "3"))),
}
for k, f in EXTRA.items():
    m.CA[k] = f
    m.NHAN[k] = {"text": _DE_X, "expect": "diagnostic"}

rows = {}
for ca in sorted(m.NHAN):
    kq = m.ket_qua(ca)
    if "served" in kq:
        out = kq["out"]
        # Kết cục route đầy đủ (telemetry chứng chỉ, bất biến nguồn…) — thứ bộ chuyển envelope đọc, không chỉ cảnh.
        dump = (out.model_dump() if hasattr(out, "model_dump")
                else __import__("dataclasses").asdict(out) if __import__("dataclasses").is_dataclass(out)
                else vars(out))
        rows[ca] = {"served": True, "value": kq["served"],
                    "scene_sha256": hashlib.sha256(json.dumps(kq["scene"], sort_keys=True, ensure_ascii=False)
                                                   .encode("utf-8")).hexdigest(),
                    "outcome_sha256": hashlib.sha256(json.dumps(dump, sort_keys=True, ensure_ascii=False, default=str)
                                                     .encode("utf-8")).hexdigest()}
    else:
        rows[ca] = {"served": False, "stage": kq.get("stage"), "reason_code": kq.get("reason_code")}

sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=BACKEND, capture_output=True, text=True).stdout.strip()
dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", "app"], cwd=BACKEND, capture_output=True,
                            text=True).stdout.strip())
OUT.write_text(json.dumps({"backend_head": sha, "backend_app_dirty": dirty, "rows": rows}, indent=1,
                          ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{sum(r['served'] for r in rows.values())}/{len(rows)} served -> {OUT}")
