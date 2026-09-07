# -*- coding: utf-8 -*-
"""Chấm LẠI artifact bất biến của lượt live, 0 lượt gọi model.

Vì sao cần: bộ chấm của lượt chạy **tụt lại sau hệ đúng một wave**. Nó chỉ
biết `construct_plane` qua ba điểm, nên khi mô hình dùng
`construct_plane_from_equation` — phép mà `PLANE_FROM_EQUATION_REPRESENTATION`
vừa thêm — nó chấm `PLANE_CONSTRUCTION_CORRECT = FAIL` cho một chương trình
**dựng mặt phẳng ĐÚNG TỪNG HỆ SỐ**.

Đó đúng lớp lỗi *"bộ đo không nằm trên đường chạy thật"*. Artifact lượt chạy
**giữ nguyên từng byte**; kết quả đúng ghi sang `SCORING.json` cạnh nó, kèm
băm của artifact nguồn để liên kết đọc ngược được.
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from score_oblique_ellipse_fresh import (  # noqa: E402
    cham_analyze, cham_synthesis,
)

RA = (BACKEND.parent / "docs" / "evaluation" / "geometry"
      / "oblique-ellipse-after-axis-scale-repair")


def main() -> int:
    art = sorted(glob.glob(str(RA / "e2e_*.json")))
    if not art:
        print("Khong tim thay artifact luot chay.")
        return 1
    p = Path(art[-1])
    tho = p.read_text(encoding="utf-8")
    d = json.loads(tho)

    raw_an = (d["raw_theo_tang"].get("semantic_analyze") or [None])[0]
    uv = [u["raw"] for u in d.get("ung_vien_tho", [])]

    attempts = []
    for i, raw in enumerate(uv):
        muc = {"attempt": i,
               "raw_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest()}
        muc.update(cham_synthesis(json.loads(raw)))
        su = next((a for a in d.get("attempts", []) if a.get("n") == i), {})
        muc["STAGE_CUOI"] = su.get("gate")
        muc["LOI_DAU_TIEN"] = su.get("message")
        muc["REPAIRABLE"] = su.get("repairable")
        attempts.append(muc)

    dr = sum(1 for a in attempts if a.get("DIRECT_RADIUS_USED"))
    rim = sum(1 for a in attempts if a.get("RIM_POINT_USED"))
    rim_ko_neo = sum(1 for a in attempts
                     if a.get("RIM_POINT_USED")
                     and a.get("RIM_POINT_GROUNDED") is False)

    ra = {
        "khai": "Cham lai artifact BAT BIEN, 0 luot goi model.",
        "wave": "OBLIQUE_ELLIPSE_E2E_AFTER_AXIS_SCALE_REPAIR",
        "artifact": p.name,
        "sha256_artifact": hashlib.sha256(tho.encode("utf-8")).hexdigest(),
        "vi_sao_cham_lai": (
            "Bo cham cua luot chay chi biet `construct_plane` qua ba diem, nen "
            "no cham FAIL cho mot chuong trinh dung mat phang DUNG bang "
            "`construct_plane_from_equation`. Bo do tut lai sau he dung mot "
            "wave. Artifact luot chay giu nguyen tung byte."),
        "analyze": cham_analyze(json.loads(raw_an)) if raw_an else None,
        "attempts": attempts,
        "rim_point_affordance": {
            "DIRECT_RADIUS_CANDIDATES": dr,
            "RIM_POINT_CANDIDATES": rim,
            "UNGROUNDED_RIM_POINT_CANDIDATES": rim_ko_neo,
            "REPAIRS_FROM_RIM_TO_RADIUS": 0,
        },
        "ket_qua": {
            "FIRST_ATTEMPT_SERVABLE": False,
            "EVENTUAL_SERVABLE": False,
            "CANDIDATE_PROGRAM_ATTEMPTS": len(uv),
            "REPAIR_CALLS": 0,
            "STAGE": d["cham"]["ket_qua"]["STAGE"],
            "ERROR_CODE": d["cham"]["ket_qua"]["ERROR_CODE"],
            "EXACT_ANSWER": "NOT_REACHED",
        },
    }
    out = RA / "SCORING.json"
    out.write_text(json.dumps(ra, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print("→", out)
    print(json.dumps(ra["attempts"], ensure_ascii=False, indent=1)[:2200])
    print(json.dumps(ra["rim_point_affordance"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
