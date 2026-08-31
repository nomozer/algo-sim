# -*- coding: utf-8 -*-
"""§19 — dựng envelope cho các ca ĐÚNG của CLEAN_BASELINE_V1. 0 API call.

Chỉ lấy `ONE_SHOT_CORRECT`/`REPAIRED_CORRECT`, tối đa hai ca: một nhiều tầng,
một có căn thức. Envelope dựng bằng **đúng hàm sản phẩm**
(`compile_semantic_program_to_envelope`) — không có bản dựng riêng cho bộ đo,
vì bản riêng là chỗ một lỗi serialize từng lẩn trốn cả một wave.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
GOC = BE.parent

from app.simulation.semantic_program.pipeline_adapter import (  # noqa: E402
    compile_semantic_program_to_envelope,
)
from app.ai.pipeline import _dung_scene3d  # noqa: E402
from app.simulation.semantic_program.transport import (  # noqa: E402
    check_envelope_transport,
)
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)

DUNG = {"ONE_SHOT_CORRECT", "REPAIRED_CORRECT"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--probe", type=Path,
                   default=GOC / "docs" / "evaluation" / "geometry"
                   / "clean-baseline-v1" / "probe.json")
    p.add_argument("--out", type=Path,
                   default=GOC / "docs" / "evaluation" / "geometry"
                   / "clean-baseline-v1" / "spot-envelopes.json")
    a = p.parse_args()

    d = json.loads(a.probe.read_text(encoding="utf-8"))
    ra = []
    for c in d["cases"]:
        if c.get("class") not in DUNG or len(ra) >= 2:
            continue
        v = validate_semantic_program(c["normalized_program"])
        if not v.ok:
            print(f"✗ {c['case_id']}: {v.error}")
            continue
        # ⚠️ HAI BƯỚC, đúng như `pipeline._envelope_tu_route`.
        #
        # `compile_semantic_program_to_envelope` một mình cho ra envelope
        # **2D** (`visual_mode: "2d"`, `domain: "generic"`) — nó dựng cho miền
        # Tin học. Cảnh 3D đến từ `verify_and_compile(...).scene3d` và được
        # GẮN THÊM; thiếu bước ấy thì học sinh mở bài ra thấy một bảng khung
        # 2D, không thấy hình.
        #
        # Bản đầu của script này chỉ gọi hàm thứ nhất và spot check ĐỎ 6/8 với
        # 0 lỗi console — đúng hình dạng của một envelope hợp lệ nhưng sai
        # miền. Không phải lỗi sản phẩm; lỗi của bộ đo, và nó chỉ lộ ra vì
        # spot check hỏi câu mà JSON không trả lời được.
        env = compile_semantic_program_to_envelope(v.spec)
        # `SemanticRouteOutcome.scene3d` chỉ là một Ô TRỐNG — route KHÔNG dựng
        # cảnh, vì engine không được biết tới tầng trình bày. Người đổ là
        # `pipeline._dung_scene3d`, và gọi đúng nó là điều kiện để envelope
        # này giống thứ sản phẩm gửi cho học sinh.
        scene = _dung_scene3d(v.spec)
        if scene:
            env["scene3d"] = scene
            env["domain"] = "geometry"
        loi = check_envelope_transport(env)
        if loi:
            print(f"✗ {c['case_id']}: {loi}")
            continue
        ra.append({"id": c["case_id"], "topology": c["topology"],
                   "oracle": c.get("oracle"), "envelope": env})
        print(f"✓ {c['case_id']} · {c['topology']} · oracle {c.get('oracle')}")

    a.out.write_text(json.dumps(
        {"khai": "§19 — envelope của các ca ĐÚNG, dựng bằng đúng hàm sản "
                 "phẩm. 0 API call.", "cases": ra},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n→ {a.out}  ({len(ra)} cảnh)")
    return 0 if ra else 1


if __name__ == "__main__":
    sys.exit(main())
