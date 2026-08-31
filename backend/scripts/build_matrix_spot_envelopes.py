# -*- coding: utf-8 -*-
"""Ba envelope cho SPOT CHECK trình duyệt (§19) — từ chương trình AI đã sinh.

Ghép ĐÚNG như sản phẩm ghép: `compile_semantic_program_to_envelope` cho phần
khung hình, rồi `pipeline._dung_scene3d` đổ cảnh 3D vào ô trống. Hai bước tách
rời có chủ đích — `route` không được import `scene3d` (hướng phụ thuộc một
chiều), nên adapter một mình KHÔNG cho ra envelope sản phẩm.

Ba ca chọn theo §19: một topology đơn giản · một nhiều tầng · một có căn thức.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.pipeline import _dung_scene3d  # noqa: E402
from app.simulation.semantic_program.pipeline_adapter import (  # noqa: E402
    SIMULATION_ID,
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)
from fractions import Fraction  # noqa: E402

from app.simulation.geometry.exact import Line3, Plane3, Vec3  # noqa: E402
from app.simulation.geometry.radical import Radical  # noqa: E402


def _sach(x):
    """Làm sạch `Vec3`/`Line3`/`Plane3` khỏi `config.frames` — VÁ CỦA BỘ ĐO.

    ⚠️ ĐÂY KHÔNG PHẢI BẢN SỬA. Nó tồn tại để §19 chạy được, và nó CHE một bug
    sản phẩm thật mà matrix vừa tìm ra:

        `VisualTraceAdapter` đặt THẲNG giá trị bộ nhớ vào `value_box.value`.
        Với biến hình học đó là `Vec3`; với một số đo đó là `Fraction` hoặc
        `Radical`. Cả ba đều KHÔNG `json.dumps` được — và `main.py` serialize
        envelope để ghi cache SAU KHI cả pipeline đã thành công.

        Phạm vi rộng hơn vẻ ngoài: prompt DẠY mô hình gắn `visual_bindings` cho
        "witness của mỗi nghĩa vụ", tức một chương trình hình học ĐÚNG gần như
        chắc chắn rơi vào đây. Cổng `check_learner_surface` cho qua (đã kiểm cả
        ba chương trình), nên không tầng nào chặn trước.

    Bản sửa thật thuộc `visual_adapter`, và phải có vòng xác minh riêng. Vá ở
    đây rồi im lặng là biến một sự cố 500 thành một dòng không ai đọc.
    """
    if isinstance(x, Vec3):
        return [str(x.x), str(x.y), str(x.z)]
    if isinstance(x, (Line3, Plane3, Fraction, Radical)):
        return str(x)
    if isinstance(x, dict):
        return {k: _sach(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_sach(v) for v in x]
    return x

GOC = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "geometry" \
    / "generalization-matrix"
CHON = ["gm_02_lang_tru", "gm_09_do_thi_sau", "gm_08_da_nghia_vu"]


def main() -> int:
    d = json.loads((GOC / "matrix.json").read_text(encoding="utf-8"))
    ra = []
    for cid in CHON:
        c = next(x for x in d["cases"] if x["case_id"] == cid)
        v = validate_semantic_program(json.loads(c["programs"][-1]))
        if not v.ok:
            print(f"  ✗ {cid}: {v.error}")
            return 1
        env = compile_semantic_program_to_envelope(v.spec)
        env["scene3d"] = _dung_scene3d(v.spec)
        env["simulation_id"] = SIMULATION_ID
        env["domain"] = "geometry"
        env["visual_mode"] = "3d"
        env["config"] = _sach(env["config"])
        json.dumps(env, ensure_ascii=False)   # sau khi vá bộ đo thì mới được
        vat = len((env["scene3d"] or {}).get("objects", []))
        ra.append({"id": cid, "envelope": env})
        print(f"  {cid:26} khung={len(env['config']['frames'])} · {vat} vật 3D")
    out = GOC / "spot-envelopes.json"
    out.write_text(json.dumps({"cases": ra}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
