# -*- coding: utf-8 -*-
"""regular-square-pyramid-w04 · yêu cầu 4 — ca đối chứng "đoạn được hỏi nằm trên cạnh có sẵn". 0 lượt gọi model.

Đề: chóp p1 (S.ABCD, toạ độ đề cho) + "Gọi M là trung điểm của SA. Tính độ dài đoạn SM." Chương trình kiểu LLM: dựng M
là trung điểm SA, đo d(S, M). Chạy qua route sản phẩm (`run_pipeline`, hai chặng LLM thay bằng hợp đồng/chương trình
đóng băng) ở mã HIỆN TẠI của kho, ghi fixture để quan sát trong trình duyệt TRƯỚC khi sửa — câu hỏi "có vẽ chồng thật
không" được trả lời bằng hành vi, không bằng issue đã mở.

  usage (từ backend/): python <this> --out <fixture json>     (từ chối ghi đè)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "backend"))

from app.learner_messages import attach_learner_reason  # noqa: E402
from app.simulation.semantic_program.validator import validate_semantic_program  # noqa: E402
from scripts import generate_generic_tier_a_fixtures as G  # noqa: E402
from tests.geometry import test_construction_binding as CB  # noqa: E402

VAN = "Gọi M là trung điểm của SA. Tính độ dài đoạn SM."


def ca_sm():
    return CB._p1(VAN, [CB._mid("M", "S", "A")], "S", "M")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    contract, program = ca_sm()
    v = validate_semantic_program(program)
    assert v.ok and v.spec is not None, v.error
    env = attach_learner_reason(asyncio.run(G._run_frozen_program(contract.problem_text, contract, v.spec)))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(G._wrapper("w04_sm_on_edge_sa", contract.problem_text, env,
                                         "w04_frozen_program_through_production_route"),
                              ensure_ascii=False, indent=2), encoding="utf-8")
    sc = env.get("scene3d") or {}
    seg = [o for o in sc.get("objects", []) if o.get("type") == "segment3"]
    print(env.get("status"), [(o["id"], o.get("endpoint_ids"), o.get("boundary_edge_ids"), o.get("render"))
                               for o in seg])


if __name__ == "__main__":
    main()
