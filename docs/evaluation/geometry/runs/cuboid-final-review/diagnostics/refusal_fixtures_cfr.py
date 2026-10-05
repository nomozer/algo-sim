"""cuboid-final-review — fixtures of the refusal-card check (task 5). 0 model calls.

Each case is a frozen corpus program sent through the production pipeline (`run_pipeline` with the analyze and
program stages replaced by the frozen contract and program, `call_gemini` forbidden — the same route as
`backend/scripts/generate_generic_tier_a_fixtures.py`), then through the API boundary (`attach_learner_reason`).
Before writing a fixture the script checks the structured refusal and, for the new code, the exact learner message,
so the browser run only has to prove the card SHOWS what the backend decided.

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
        ../docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/refusal_fixtures_cfr.py --out <dir>

Writes <dir>/fixtures/<case>.json and <dir>/CASES.json (case → mode, fixture, expected, sha256).
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "backend"))

from app.learner_messages import attach_learner_reason  # noqa: E402
from app.simulation.semantic_program.validator import validate_semantic_program  # noqa: E402
from scripts import generate_generic_tier_a_fixtures as GEN  # noqa: E402
from tests.geometry import test_construction_binding as CB  # noqa: E402
from tests.geometry import test_construction_binding_literal as LT  # noqa: E402

TOA_DO = "CONSTRUCTION_REPLACED_BY_COORDINATES"
DUNG_LAI = " Hệ tạm dừng để tránh đưa ra kết quả chưa kiểm chứng."


def _refusal(code: str, cause: str, label: str, message: str | None = None) -> dict:
    return {"product_error_code": "input_not_grounded", "stage_reached": "construction_binding",
            "reason_code": code, "refusal_cause": cause, "problem_label": label,
            **({"learner_reason": message} if message else {})}


CASES = (
    ("cfr_projection_by_coordinates", "negative", LT.CA["L14_proj_outside_wrong_coords"],
     _refusal(TOA_DO, "CONSTRUCTION", "chưa kiểm chứng được phép dựng",
              "Hệ chưa kiểm chứng được H là hình chiếu của S lên BD, vì điểm này được đặt bằng toạ độ thay vì dựng "
              "từ quan hệ trong đề." + DUNG_LAI)),
    ("cfr_projection_alias_vertex", "negative", LT.CA["L17_proj_outside_alias_to_vertex"],
     _refusal(TOA_DO, "CONSTRUCTION", "chưa kiểm chứng được phép dựng",
              "Hệ chưa kiểm chứng được H là hình chiếu của S lên BD, vì điểm này được lấy trùng với điểm A thay vì "
              "dựng từ quan hệ trong đề." + DUNG_LAI)),
    ("cfr_midpoint_by_coordinates", "negative", LT.CA["L16_mid_U3_literal_then_constructed"],
     _refusal(TOA_DO, "CONSTRUCTION", "chưa kiểm chứng được phép dựng",
              "Hệ chưa kiểm chứng được M là trung điểm của SA, vì điểm này được đặt bằng toạ độ thay vì dựng từ quan "
              "hệ trong đề." + DUNG_LAI)),
    # Controls: a proven mismatch and an unverified construction keep their labels; a correct one is served.
    ("w18_projection_mismatch", "negative", CB.CA["B11_proj_line_wrong_BC"],
     _refusal("CONSTRUCTION_NOT_TEXT_BOUND", "CONSTRUCTION", "hệ dựng lệch với đề bài")),
    ("w18_unverified", "negative", CB.CA["B16_out_of_vocab_ok"],
     _refusal("CONSTRUCTION_BINDING_UNVERIFIED", "UNKNOWN", "hệ chưa đối chiếu được phép dựng với đề")),
    ("w18_projection_line", "served", CB.CA["B10_proj_line_ok"], {"answer": "3√6", "annotation_id": "d_kq"}),
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out.resolve()
    (out / "fixtures").mkdir(parents=True, exist_ok=True)
    rows = []
    for name, mode, build, expected in CASES:
        contract, program = build()
        v = validate_semantic_program(program)
        assert v.ok and v.spec is not None, (name, v.error)
        env = attach_learner_reason(asyncio.run(GEN._run_frozen_program(contract.problem_text, contract, v.spec)))
        if mode == "served":
            d = next(o for o in env["scene3d"]["objects"] if o["id"] == expected["annotation_id"])
            assert env["status"] == "ok" and d.get("value") == expected["answer"], (name, env["status"], d.get("value"))
        else:
            got = (env["status"], env.get("error_code"), env.get("stage_reached"), env.get("reason_code"),
                   env.get("refusal_cause"))
            assert got == ("unsupported", expected["product_error_code"], expected["stage_reached"],
                           expected["reason_code"], expected["refusal_cause"]), (name, got)
            assert not (env.get("scene3d") or {}).get("objects"), (name, "a refusal carries no scene")
            if "learner_reason" in expected:
                assert env["learner_reason"] == expected["learner_reason"], (name, env["learner_reason"])
        path = out / "fixtures" / f"{name}.json"
        path.write_text(json.dumps(GEN._wrapper(name, contract.problem_text, env, "cfr_corpus_frozen_program_through_"
                                                "production_route"), ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        rows.append({"case": name, "mode": mode, "fixture": f"fixtures/{name}.json", "expected": expected,
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        print(f"{name}: {env['status']} {env.get('reason_code') or ''}")
    (out / "CASES.json").write_text(json.dumps({
        "schema_version": "cfr-refusal-cases/1", "product_commit_sha": GEN.PRODUCT_COMMIT_SHA,
        "product_tree_sha": GEN.PRODUCT_TREE_SHA, "application_llm_calls": 0, "cases": rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
