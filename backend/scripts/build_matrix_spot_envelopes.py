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
        # KHÔNG còn vá của bộ đo: `visual_adapter` nay đi qua `transport.py`,
        # nên envelope THẬT phải serialize được. Dòng này là phép kiểm, không
        # phải phép chuyển đổi.
        json.dumps(env, ensure_ascii=False)
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
