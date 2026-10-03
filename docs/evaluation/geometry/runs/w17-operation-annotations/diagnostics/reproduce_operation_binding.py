# -*- coding: utf-8 -*-
"""W17 Phase 1 — tái hiện A′/A2b qua BIÊN SẢN PHẨM, offline, 0 lượt gọi model.

Đề nói "(β) cắt khối chóp theo thiết diện (T)"; chương trình cắt (T) bằng (α) đã ghim đúng phương
trình. Mỗi hàng chạy `pipeline.run_pipeline(..., semantic_route="serve")` với hai chặng LLM thay bằng
hợp đồng + chương trình đóng băng (cùng trình chạy với fixture sản phẩm,
`backend/scripts/generate_generic_tier_a_fixtures._run_frozen_program`), và lưu: đề, request,
hợp đồng, chương trình, chứng chỉ (`assumption_gate.danh_gia_doc_lap`), response (envelope có
`learner_reason`).

Chạy từ backend/:
  ../.venv… python ../docs/evaluation/geometry/runs/w17-operation-annotations/diagnostics/reproduce_operation_binding.py
Không ghi đè: tệp kết quả đã có thì dừng.
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

DIAG = Path(__file__).resolve().parent
BACKEND = DIAG.parents[5] / "backend"
sys.path.insert(0, str(BACKEND))

from app.learner_messages import attach_learner_reason  # noqa: E402
from app.simulation.semantic_program import assumption_gate as AG  # noqa: E402
from app.simulation.semantic_program.validator import validate_semantic_program  # noqa: E402
from scripts import generate_generic_tier_a_fixtures as GEN  # noqa: E402
from tests.geometry import test_assumption_certificate as AC  # noqa: E402

HANG = {
    "O1_cat_bang_alpha_khi_de_noi_beta": AC.PHEP_DUNG_SAI["O1_cat_bang_alpha_khi_de_noi_beta"],
    "O1b_doi_chung_cat_bang_beta": AC.PHEP_DUNG_DUNG["O1b_doi_chung_cat_bang_beta"],
}


def _mot_hang(cid: str, dung) -> dict:
    contract, program = dung()
    spec = validate_semantic_program(program).spec
    kq = AG.danh_gia_doc_lap(contract, spec)
    env = attach_learner_reason(asyncio.run(GEN._run_frozen_program(contract.problem_text, contract, spec)))
    # Con số NGƯỜI HỌC THẤY là giá trị của vật `quantity` trong cảnh (envelope không mang final_memory).
    fm = {o["id"]: o.get("value") for o in (env.get("scene3d") or {}).get("objects", []) if o.get("type") == "quantity"}
    return {
        "id": cid,
        "source_text": contract.problem_text,
        "request": {"problem_text": contract.problem_text, "boundary": "app.ai.pipeline.run_pipeline",
                    "semantic_route": "serve", "mode": "LLM_ONLY",
                    "llm_stages": "replaced by the frozen contract and program below (0 model calls)"},
        "contract": contract.model_dump(mode="json"),
        "program": program,
        "certificate": {"status": kq.status, "certificate": kq.certificate, "reason_code": kq.reason_code,
                        "subjects": list(kq.subjects), "details": list(kq.details)},
        "response": {"status": env.get("status"), "stage_reached": env.get("stage_reached"),
                     "error_code": env.get("error_code"), "reason_code": env.get("reason_code"),
                     "refusal_cause": env.get("refusal_cause"), "learner_reason": env.get("learner_reason"),
                     "shown_area_T": str(fm["area_T"]) if "area_T" in fm else None},
    }


def main() -> None:
    sha = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], capture_output=True, text=True,
                         cwd=BACKEND).stdout.strip()
    ra = DIAG / f"OPERATION_BINDING_REPRODUCTION_{sha}.json"
    if ra.exists():
        raise SystemExit(f"{ra.name} đã có — không ghi đè")
    rows = [_mot_hang(cid, dung) for cid, dung in HANG.items()]
    ra.write_text(json.dumps({"probe": "W17_OPERATION_BINDING_REPRODUCTION", "measured_at_commit": sha,
                              "model_calls": 0, "rows": rows}, ensure_ascii=False, indent=2) + "\n",
                  encoding="utf-8", newline="\n")
    for r in rows:
        print(r["id"], "| certificate:", r["certificate"]["status"], r["certificate"]["certificate"],
              "| response:", r["response"]["status"], r["response"]["stage_reached"],
              "| shown area_T:", r["response"]["shown_area_T"])
    print("wrote", ra.name)


if __name__ == "__main__":
    main()
