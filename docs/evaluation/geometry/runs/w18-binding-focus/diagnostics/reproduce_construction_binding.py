# -*- coding: utf-8 -*-
"""W18 Phase 1 — tái hiện lỗ binding phép dựng điểm qua BIÊN SẢN PHẨM, offline, 0 lượt gọi model.

Mỗi hàng là một ca có nhãn của `construction_corpus_w18/LABELS.json` (cùng builder với
`backend/tests/geometry/test_construction_binding.py`), thêm hai ca ngoài vùng đa diện và hai ca
thiết diện W17 (hồi quy). Mỗi hàng chạy `pipeline.run_pipeline(..., semantic_route="serve")` với hai
chặng LLM thay bằng hợp đồng + chương trình đóng băng (trình chạy fixture sản phẩm
`backend/scripts/generate_generic_tier_a_fixtures._run_frozen_program`), và lưu:
- đề, request, hợp đồng, chương trình;
- quan hệ đề yêu cầu: các câu "Gọi …" của đề, nguyên văn (chưa có bộ đọc nào trước bản sửa);
- quan hệ chương trình thực thi: mọi `construct_point` (đích, phép, toán hạng);
- chứng chỉ (`assumption_gate.danh_gia_doc_lap`);
- response (envelope có `learner_reason`) và giá trị `d_kq` người học thấy.

Chạy từ backend/ (đường pipeline chạm tầng lưu trữ; chạy từ gốc sẽ đẻ ./algosim.db):
  .venv/Scripts/python.exe ../docs/evaluation/geometry/runs/w18-binding-focus/diagnostics/reproduce_construction_binding.py
Không ghi đè: tệp kết quả đã có thì dừng.
"""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

DIAG = Path(__file__).resolve().parent
ROOT = DIAG.parents[5]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "scripts"))

from app.learner_messages import attach_learner_reason  # noqa: E402
from app.simulation.semantic_program import assumption_gate as AG  # noqa: E402
from app.simulation.semantic_program.validator import validate_semantic_program  # noqa: E402
from scripts import generate_generic_tier_a_fixtures as GEN  # noqa: E402
from tests.geometry import test_assumption_certificate as AC  # noqa: E402
from tests.geometry import test_construction_binding as T  # noqa: E402

NHAN = T.NHAN
HANG = dict(T.CA)
HANG["X1_outside_scope_mismatch"] = lambda: T._ngoai(
    "Gọi M là trung điểm của SA. Tính độ dài đoạn MC.", [T._mid("M", "S", "B")], "M", "C")
HANG["X2_outside_scope_out_of_vocab"] = lambda: T._ngoai(
    "Gọi M là điểm chính giữa của đoạn SA. Tính độ dài đoạn MC.", [T._mid("M", "S", "A")], "M", "C")
HANG["W17_O1_cut_alpha_text_beta"] = AC.PHEP_DUNG_SAI["O1_cat_bang_alpha_khi_de_noi_beta"]
HANG["W17_O1b_cut_beta_control"] = AC.PHEP_DUNG_DUNG["O1b_doi_chung_cat_bang_beta"]


def _phep_dung(program: dict) -> list[dict]:
    ra = []
    for s in program["statements"]:
        if s["kind"] != "construct_point":
            continue
        e = dict(s["expr"])
        ra.append({"target": s["target_var"], "kind": e.pop("kind"), "operands": e})
    return ra


def _mot_hang(cid: str, dung) -> dict:
    contract, program = dung()
    spec = validate_semantic_program(program).spec
    kq = AG.danh_gia_doc_lap(contract, spec)
    env = attach_learner_reason(asyncio.run(GEN._run_frozen_program(contract.problem_text, contract, spec)))
    # Con số NGƯỜI HỌC THẤY là giá trị của vật `quantity` trong cảnh (envelope không mang final_memory).
    gt = {o["id"]: o.get("value") for o in (env.get("scene3d") or {}).get("objects", []) if o.get("type") == "quantity"}
    nhan = NHAN.get(cid, {})
    return {
        "id": cid,
        "label": nhan.get("label"), "expect_after_fix": nhan.get("expect"), "binding_after_fix": nhan.get("binding"),
        "source_text": contract.problem_text,
        "request": {"problem_text": contract.problem_text, "boundary": "app.ai.pipeline.run_pipeline",
                    "semantic_route": "serve", "mode": "LLM_ONLY",
                    "llm_stages": "replaced by the frozen contract and program below (0 model calls)"},
        "contract": contract.model_dump(mode="json"),
        "program": program,
        "required_relation_text": [c.strip() + "." for c in re.split(r"\.\s*", contract.problem_text)
                                   if c.strip().startswith("Gọi ")],
        "executed_point_constructions": _phep_dung(program),
        "certificate": {"status": kq.status, "certificate": kq.certificate, "reason_code": kq.reason_code,
                        "subjects": list(kq.subjects), "details": list(kq.details)},
        "response": {"status": env.get("status"), "stage_reached": env.get("stage_reached"),
                     "error_code": env.get("error_code"), "reason_code": env.get("reason_code"),
                     "refusal_cause": env.get("refusal_cause"), "learner_reason": env.get("learner_reason"),
                     "shown_d_kq": gt.get("d_kq"), "shown_area_T": gt.get("area_T")},
    }


def main() -> None:
    sha = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], capture_output=True, text=True,
                         cwd=ROOT).stdout.strip()
    ra = DIAG / f"CONSTRUCTION_BINDING_REPRODUCTION_{sha}.json"
    if ra.exists():
        raise SystemExit(f"{ra.name} đã có — không ghi đè")
    rows = [_mot_hang(cid, dung) for cid, dung in HANG.items()]
    ra.write_text(json.dumps({"probe": "W18_CONSTRUCTION_BINDING_REPRODUCTION", "measured_at_commit": sha,
                              "model_calls": 0, "rows": rows}, ensure_ascii=False, indent=2) + "\n",
                  encoding="utf-8", newline="\n")
    for r in rows:
        print(f"{r['id']:34} {str(r['label']):12} | cert {r['certificate']['status']}/{r['certificate']['certificate']}"
              f" | {r['response']['status']} @ {r['response']['stage_reached']} {r['response']['reason_code']}"
              f" | d_kq {r['response']['shown_d_kq']} | expect {r['expect_after_fix']}")
    print("wrote", ra.name)


if __name__ == "__main__":
    main()
