# -*- coding: utf-8 -*-
"""PHÂN TÍCH LẠI MATRIX, 0 TOKEN — tách LỖI CỦA BỘ ĐO khỏi lỗi của hệ (§17).

Lượt live bỏ tầng `analyze` để tiết kiệm token, nên `RequestContract` RỖNG và
mọi `source_fact_id` mô hình khai đều không có chỗ neo. `grounding_gate` từ chối
đúng theo luật của nó — nhưng nó đang từ chối vì **bộ đo thiếu một tầng**, không
vì chương trình sai. 6/9 ca chết ở đó.

File này chạy lại CHÍNH chương trình đã sinh, bỏ đúng một cổng ấy, để trả lời:

    chương trình mô hình viết ra có ĐÚNG không, nếu tầng analyze có mặt?

⚠️ Đây KHÔNG phải cách nâng điểm. Kết quả ghi thành một cột RIÊNG
(`offline_class`), không đè `class` của lượt live. Bộ đo hỏng là lỗi của bộ đo,
và giấu nó đi thì con số sau này không ai kiểm lại được.
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.simulation.geometry.radical import Radical, radical  # noqa: E402
from app.simulation.semantic_program.interpreter import (  # noqa: E402
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.ir_static_check import kiem_tinh  # noqa: E402
from app.simulation.semantic_program.scene3d import build_scene3d  # noqa: E402
from app.simulation.semantic_program.simulation_state import (  # noqa: E402
    build_simulation_state,
)
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)
from scripts.generalization_matrix_cases import CASES  # noqa: E402

MA_TRAN = (Path(__file__).resolve().parents[2] / "docs" / "evaluation"
           / "geometry" / "generalization-matrix" / "matrix.json")


def _mong(x):
    if x is None:
        return None
    k, v = x
    return Fraction(v) if k == "rational" else radical(v[0], v[1])


def main() -> int:
    d = json.loads(MA_TRAN.read_text(encoding="utf-8"))
    oracle = {c["id"]: c.get("dap_so") for c in CASES}
    ra = []
    for c in d["cases"]:
        m = _mong(oracle.get(c["case_id"]))
        kq = {"case_id": c["case_id"], "live_class": c.get("class"),
              "live_taxonomy": c.get("taxonomy"), "offline_class": None,
              "offline_note": None, "scene3d_ok": None}
        for raw in reversed(c.get("programs") or []):
            try:
                v = validate_semantic_program(json.loads(raw))
            except Exception as e:  # noqa: BLE001
                kq["offline_note"] = f"SCHEMA: {e}"[:200]
                continue
            if not v.ok:
                kq["offline_note"] = f"SCHEMA: {v.error}"[:200]
                continue
            t = kiem_tinh(v.spec)
            if not t.ok:
                kq.update(offline_class="STATIC_VALIDATION",
                          offline_note=t.phan_hoi()[:200])
                break
            try:
                r = SemanticProgramInterpreter().execute(v.spec)
            except Exception as e:  # noqa: BLE001
                kq.update(offline_class="RUNTIME",
                          offline_note=f"{type(e).__name__}: {e}"[:200])
                break
            so = [x for x in r.final_memory.values()
                  if isinstance(x, (Fraction, Radical)) and not isinstance(x, bool)]
            try:
                st = build_simulation_state(v.spec, r)
                json.dumps(build_scene3d(st), ensure_ascii=False)
                kq["scene3d_ok"] = True
                kq["trace_steps"] = len(st.get("timeline") or [])
            except Exception as e:  # noqa: BLE001
                kq["scene3d_ok"] = False
                kq["offline_note"] = f"SCENE: {type(e).__name__}"[:120]
            if m is None:
                kq["offline_class"] = "RAN_BUT_OUT_OF_SCOPE"
                kq["offline_note"] = (
                    "đề NGOÀI năng lực nhưng chương trình chạy trót lọt — "
                    f"đo được {[str(x) for x in so][:2]}")
            elif any(x == m for x in so):
                kq["offline_class"] = "CORRECT"
                kq["offline_note"] = f"khớp oracle {m}"
            else:
                kq["offline_class"] = "EXECUTABLE_BUT_INCORRECT"
                kq["offline_note"] = (
                    f"đo {[str(x) for x in so][:3]}, oracle {m}")
            break
        else:
            kq["offline_class"] = kq["offline_class"] or "NO_PROGRAM"
        ra.append(kq)

    trong = [x for x in ra if x["case_id"] != "gm_10_ngoai_nang_luc"]
    dung = sum(1 for x in trong if x["offline_class"] == "CORRECT")
    bao = {
        "khai": "Phân tích lại 0 token: chạy lại chương trình ĐÃ SINH, bỏ cổng "
                "grounding vì lượt live thiếu tầng analyze nên RequestContract "
                "rỗng. Cột riêng, KHÔNG đè kết quả live.",
        "gioi_han": "Bỏ grounding là bỏ một cổng THẬT của sản phẩm. Con số ở "
                    "đây trả lời 'chương trình có đúng không', KHÔNG trả lời "
                    "'sản phẩm có chạy được không'.",
        "in_scope": len(trong), "offline_correct": dung,
        "cases": ra,
    }
    out = MA_TRAN.parent / "matrix-offline-reanalysis.json"
    out.write_text(json.dumps(bao, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    for x in ra:
        print(f"  {x['case_id']:28} live={str(x['live_class']):24} "
              f"offline={str(x['offline_class']):26} scene3d={x['scene3d_ok']}")
    print(f"\n→ {out}\nđúng (offline, bỏ grounding): {dung}/{len(trong)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
