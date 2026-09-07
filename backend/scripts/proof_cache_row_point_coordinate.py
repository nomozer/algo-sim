# -*- coding: utf-8 -*-
"""§10 — BẰNG CHỨNG cache bằng một ROW THẬT. 0 lượt gọi model.

Câu hỏi không phải *"có nên bump không"* mà là *"một envelope sinh TRƯỚC bản
vá có còn được trả lại không"*. Lập luận trả lời được câu đầu; chỉ một row
thật trả lời được câu sau.

Dựng đúng cảnh huống: một row `status = "ok"` mang `V = 540` — con số mà hệ
HÔM NAY từ chối — rồi hỏi `_cache_lookup` xem nó còn HIT không.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.main import (  # noqa: E402
    CACHE_VERSION, DSL_VERSION, SessionLocal, SimulationCache, _cache_key,
    _cache_lookup, init_db,
)

RA = (BACKEND.parent / "docs" / "evaluation" / "geometry"
      / "point-coordinate-source-invariant")

#: Envelope SAI, đúng hình dạng thứ `main.py` từng cache: `status = "ok"`.
ENVELOPE_SAI = {
    "status": "ok",
    "simulation_id": "generic.semantic_program",
    "ghi_chu": "Envelope mo phong: B(99,7,0) — he TRUOC ban va phuc vu V=540.",
    "final_memory": {"V": "540"},
}


def main() -> int:
    init_db()
    de = ("Cho khối chóp S.ABCDE có đáy ABCDE là ngũ giác lõm, "
          "A(0,0,0), B(6,0,0), C(6,4,0), D(3,1,0), E(0,4,0), S(2,2,9). "
          "Tính thể tích. [PROOF_CACHE_ROW point-coordinate]")
    key = _cache_key(de)

    ra: dict = {
        "khai": "Bang chung CACHE bang ROW THAT. 0 luot goi model.",
        "wave": "POINT_COORDINATE_SOURCE_INVARIANT",
        "luc": datetime.now(timezone.utc).isoformat(),
        "cache_version_hien_tai": CACHE_VERSION,
        "cache_key": key,
    }

    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(
            key=key, problem_text=de,
            simulation_id="generic.semantic_program",
            envelope_json=json.dumps(ENVELOPE_SAI, ensure_ascii=False),
            dsl_version=DSL_VERSION,
            # Row sinh DƯỚI version hiện tại — tức "trước bản vá" theo đúng
            # nghĩa vận hành: cùng một `CACHE_VERSION`, khác hành vi hệ.
            policy_version=CACHE_VERSION))
        s.commit()

        row = _cache_lookup(s, key)
        ra["row_duoi_version_HIEN_TAI"] = {
            "HIT": row is not None,
            "policy_version": getattr(row, "policy_version", None),
            "envelope": json.loads(row.envelope_json) if row else None,
        }

        # …và điều gì xảy ra nếu bump: row cũ giữ nguyên `policy_version`.
        moi = str(int(CACHE_VERSION) + 1)
        import app.main as M
        goc = M.CACHE_VERSION
        try:
            M.CACHE_VERSION = moi
            ra["row_sau_khi_BUMP"] = {
                "CACHE_VERSION_gia_lap": moi,
                "HIT": _cache_lookup(s, key) is not None,
            }
        finally:
            M.CACHE_VERSION = goc

        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()

    hit_cu = ra["row_duoi_version_HIEN_TAI"]["HIT"]
    hit_moi = ra["row_sau_khi_BUMP"]["HIT"]
    ra["KET_LUAN"] = {
        "ENVELOPE_SAI_VAN_HIT_DUOI_VERSION_CU": hit_cu,
        "BUMP_LAM_ROW_CU_MISS": not hit_moi,
        "CACHE_DECISION": ("BUMP — envelope `ok` mang so SAI van duoc tra lai "
                           "duoi cung version, nen row cu PHAI miss"
                           if hit_cu and not hit_moi else
                           "KHONG DU BANG CHUNG — do lai truoc khi quyet"),
    }
    ra["sha256"] = hashlib.sha256(
        json.dumps(ra, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()

    RA.mkdir(parents=True, exist_ok=True)
    f = RA / "PROOF_CACHE_ROW.json"
    if f.exists():
        print(f"⚠️  {f.name} da ton tai — KHONG ghi de artifact luot cu.")
    else:
        f.write_text(json.dumps(ra, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        print("→", f)
    print(json.dumps(ra["KET_LUAN"], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
