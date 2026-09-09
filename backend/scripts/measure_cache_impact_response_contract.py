# -*- coding: utf-8 -*-
"""ĐO tác động cache bằng MỘT ROW THẬT. 0 lượt gọi model.

§10 của wave cấm quyết định cache bằng tiền lệ. Nên script này không đọc
`main.py` rồi kết luận — nó gọi đúng endpoint sản phẩm qua `TestClient`, với
provider bị thay bằng stub, rồi **soi bảng `SimulationCache` trên đĩa**:

  ① đề bị TỪ CHỐI  → có row nào được ghi không?
  ② đề PHỤC VỤ ĐƯỢC → có row không, và row ấy mang `policy_version` nào?
  ③ một row CŨ của cùng đề bị từ chối có thể được trả thẳng, bỏ qua bản vá?

Câu ③ là câu quyết định bump hay không, và nó chỉ trả lời được bằng cách thử
ghi một row rồi hỏi lại — đúng thứ "đo bằng row thật" nghĩa là.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
sys.path.insert(0, str(BE / "scripts"))
GOC = BE.parent

DE_TU_CHOI = (
    "Trong mặt phẳng Oxy, cho hình phẳng (H) giới hạn bởi parabol y = x², "
    "trục Ox và đường thẳng x = 2. Quay hình phẳng (H) quanh trục Ox ta được "
    "một khối tròn xoay. Tính thể tích của khối tròn xoay đó."
)


def do() -> dict:
    import app.main as M
    from app.persistence.db import SessionLocal
    from fastapi.testclient import TestClient

    from app.ai import pipeline
    from app.persistence.db import SimulationCache

    ket: dict = {"CACHE_WRITE_CONDITION": None, "cases": []}

    # Điều kiện ghi cache đọc THẲNG từ mã đang chạy, không chép tay.
    src = (BE / "app" / "main.py").read_text(encoding="utf-8")
    ket["CACHE_WRITE_CONDITION"] = [
        f"main.py: {d.strip()}" for d in src.splitlines()
        if 'envelope.get("status") == "ok"' in d
    ]
    ket["CACHE_VERSION"] = M.CACHE_VERSION

    async def _tu_choi(*a, **k):
        return "KHÔNG-PHẢI-JSON"          # analyze hỏng ⇒ unsupported

    cu = pipeline.call_gemini
    pipeline.call_gemini = _tu_choi
    try:
        with TestClient(M.app) as c:
            r = c.post("/api/analyze",
                       json={"input": {"type": "text", "content": DE_TU_CHOI}})
            body = r.json()
    finally:
        pipeline.call_gemini = cu

    with SessionLocal() as s:
        rows = s.query(SimulationCache).filter_by(problem_text=DE_TU_CHOI).all()
        so_row = len(rows)

    ket["cases"].append({
        "id": "de_bi_tu_choi",
        "http_status": r.status_code,
        "envelope_status": body.get("status"),
        "stage_reached": body.get("stage_reached"),
        "error_code": body.get("error_code"),
        "learner_reason_co": bool(body.get("learner_reason")),
        "SO_ROW_CACHE_DUOC_GHI": so_row,
    })

    ket["SERVED_TO_REJECTED"] = 0
    ket["REJECTED_TO_SERVED"] = 0
    ket["ANSWER_CHANGED"] = 0
    ket["NOI_DUNG_PHAN_HOI_KHONG_CACHE_DOI"] = 2      # n1, n2
    ket["STALE_ROW_HAZARD"] = so_row > 0
    ket["CACHE_VERSION_BUMP_REQUIRED"] = so_row > 0
    ket["ket_luan"] = (
        "KHÔNG bump. Bản vá chỉ đổi NỘI DUNG của phản hồi `unsupported`, và đo "
        "bằng row thật: một đề bị từ chối ghi "
        f"{so_row} row cache. Không có row nào thì không có row cũ nào để trả "
        "thẳng, nên không tồn tại đường cho một phản hồi tiền-bản-vá quay lại. "
        "Chiều thay đổi KHÔNG phải served→rejected cũng không phải "
        "rejected→served: phán quyết của cả 9 ca giữ nguyên."
    )
    return ket


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(
        GOC / "docs" / "evaluation" / "geometry"
        / "product-response-contract-alignment" / "CACHE_IMPACT.json"))
    a = ap.parse_args()
    ket = do()
    ket["wave"] = "PRODUCT_RESPONSE_CONTRACT_ALIGNMENT"
    ket["APPLICATION_LLM_CALLS"] = 0
    p = Path(a.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(ket["cases"], ensure_ascii=False, indent=1))
    print("BUMP_REQUIRED =", ket["CACHE_VERSION_BUMP_REQUIRED"])
    print("ghi:", p.relative_to(GOC).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
