# -*- coding: utf-8 -*-
"""W20 — probe ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET qua BIÊN SẢN PHẨM, offline, 0 lượt gọi model.

Mỗi hàng của `literal_target_corpus/LABELS.json` (nhãn ghi TRƯỚC lượt chạy đầu và trước mọi sửa sản phẩm)
dựng bằng builder của `backend/tests/geometry/test_construction_binding.py`, rồi chạy qua:
- `app.ai.pipeline.run_pipeline(..., semantic_route="serve")` với hai chặng LLM thay bằng hợp đồng +
  chương trình đóng băng (`scripts/generate_generic_tier_a_fixtures._run_frozen_program`) → envelope,
  lời người học, con số người học thấy;
- `route.verify_and_compile` (`tests/geometry/w14_cases.chay`) → chặng dừng, mã, nguyên nhân, trạng thái
  đối chiếu phép dựng, chi tiết grounding.

Chạy từ backend/ (pipeline chạm tầng lưu trữ):
  .venv/Scripts/python.exe ../docs/evaluation/geometry/runs/w20-cleanup-premerge/diagnostics/probe_literal_target.py --tag before
Ghi `results/LITERAL_TARGET_PROBE_<tag>_<head8>.json`; tệp đã có thì dừng (không ghi đè).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

DIAG = Path(__file__).resolve().parent
RUN = DIAG.parent
ROOT = RUN.parents[4]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "scripts"))

from app.learner_messages import attach_learner_reason  # noqa: E402
from app.simulation.semantic_program.validator import validate_semantic_program  # noqa: E402
from scripts import generate_generic_tier_a_fixtures as GEN  # noqa: E402
from tests.geometry import test_construction_binding as T  # noqa: E402
from tests.geometry import w14_cases as W  # noqa: E402

LABELS = json.loads((DIAG / "literal_target_corpus" / "LABELS.json").read_text(encoding="utf-8"))
FD = LABELS["fixed_data"]
VAN_M = "Gọi M là trung điểm của SA. Tính độ dài đoạn MC."
VAN_M_NGOAI = "Gọi M là trung điểm của SA. Tính khoảng cách từ M đến đường thẳng BC."
VAN_H = "Gọi H là hình chiếu vuông góc của S lên đường thẳng BD. Tính độ dài đoạn SH."
MA_M, MA_H = "đặt M tại toạ độ tự tính", "đặt H tại toạ độ tự tính"
M_DEF = {"id": "M_def", "kind": "str", "label": "Trung điểm M", "value": ["M là trung điểm của SA"]}
H_DEF = {"id": "H_def", "kind": "str", "label": "Hình chiếu H",
         "value": ["H là hình chiếu vuông góc của S lên đường thẳng BD"]}


def lit(t: str, at: list, *, ma: str | None = None, fid: str | None = None) -> dict:
    s = {"kind": "declare_point", "target_var": t, "at": list(at)}
    if ma:
        s["model_assumption"] = ma
    if fid:
        s["source_fact_id"] = fid
    return s


def u3_m(them, **kw):
    return T._p1(VAN_M, them, "M", "C", **kw)


def u3_h(them, **kw):
    return T._p1(VAN_H, [T._duong("BD", "B", "D")] + them, "S", "H", **kw)


def out_m(them, **kw):
    return T._p1(VAN_M_NGOAI, [T._duong("BC", "B", "C")] + them, "M", "BC", nen=T.NGOAI_VUNG, co_khoi=False, **kw)


def out_h(them, **kw):
    return T._p1(VAN_H, [T._duong("BD", "B", "D")] + them, "S", "H", nen=T.NGOAI_VUNG, co_khoi=False, **kw)


M_OK, M_SAI, H_OK, H_SAI = FD["midpoint_M_of_SA"], FD["wrong_M"], FD["projection_H_of_S_on_BD"], FD["wrong_H_on_line_BD"]
CA = {
    "C1_mid_constructed_U3": T.CA["B1_mid_ok"],
    "C2_proj_constructed_U3": T.CA["B10_proj_line_ok"],
    "C3_mid_divide_half_U3": T.CA["B20_divide_half_ok"],
    "C4_relation_not_realized_U3": T.CA["B21_not_realized"],
    "C5_mid_constructed_outside": lambda: out_m([T._mid("M", "S", "A")]),
    "C6_proj_constructed_outside": lambda: out_h([T._proj("H", "S", "BD")]),
    "C7_layout_only_outside": lambda: T._p1("Tính độ dài đoạn SC.", [], "S", "C", nen=T.NGOAI_VUNG, co_khoi=False),
    "L1_mid_U3_assumption": lambda: u3_m([lit("M", M_OK, ma=MA_M)]),
    "L2_mid_U3_bogus_fid": lambda: u3_m([lit("M", M_OK, ma=MA_M, fid="M_toa_do")]),
    "L3_mid_U3_relation_fact": lambda: u3_m([lit("M", M_OK, fid="M_def")], facts=(M_DEF,)),
    "L4_mid_U3_wrong_coords": lambda: u3_m([lit("M", M_SAI, ma=MA_M, fid="M_toa_do")]),
    "L5_mid_outside_assumption": lambda: out_m([lit("M", M_OK, ma=MA_M)]),
    "L6_mid_outside_bogus_fid": lambda: out_m([lit("M", M_OK, ma=MA_M, fid="M_toa_do")]),
    "L7_mid_outside_relation_fact": lambda: out_m([lit("M", M_OK, fid="M_def")], facts=(M_DEF,)),
    "L8_mid_outside_wrong_coords": lambda: out_m([lit("M", M_SAI, ma=MA_M, fid="M_toa_do")]),
    "L9_proj_U3_assumption": lambda: u3_h([lit("H", H_OK, ma=MA_H)]),
    "L10_proj_U3_bogus_fid": lambda: u3_h([lit("H", H_OK, ma=MA_H, fid="H_toa_do")]),
    "L11_proj_U3_relation_fact": lambda: u3_h([lit("H", H_OK, fid="H_def")], facts=(H_DEF,)),
    "L12_proj_outside_bogus_fid": lambda: out_h([lit("H", H_OK, ma=MA_H, fid="H_toa_do")]),
    "L13_proj_outside_relation_fact": lambda: out_h([lit("H", H_OK, fid="H_def")], facts=(H_DEF,)),
    "L14_proj_outside_wrong_coords": lambda: out_h([lit("H", H_SAI, ma=MA_H, fid="H_toa_do")]),
    "L15_mid_U3_literal_twin_of_constructed": lambda: u3_m([lit("M", M_OK, ma=MA_M, fid="M_toa_do"),
                                                            T._mid("N", "S", "A")]),
    "L16_mid_U3_literal_then_constructed": lambda: u3_m([lit("M", M_OK, ma=MA_M, fid="M_toa_do"),
                                                         T._mid("M", "S", "A")]),
    "C8_alias_to_constructed_U3": T.CA["B8_alias_ok"],
    "C9_layout_only_outside_distance_clue": lambda: T._p1("Tính khoảng cách từ S đến đường thẳng BC.",
                                                          [T._duong("BC", "B", "C")], "S", "BC",
                                                          nen=T.NGOAI_VUNG, co_khoi=False),
    "L17_proj_outside_alias_to_vertex": lambda: out_h([T._gan("H", "A")], khai=({"name": "H", "type": "point3"},)),
    "L18_proj_outside_alias_to_cited_literal": lambda: out_h([lit("Q", H_OK, fid="H_def"), T._gan("H", "Q")],
                                                             khai=({"name": "H", "type": "point3"},), facts=(H_DEF,)),
}


def mot_hang(cid: str) -> dict:
    contract, program = CA[cid]()
    nhan = LABELS["rows"][cid]
    hang: dict = {"id": cid, "expect": nhan["expect"], "note": nhan["note"], "source_text": contract.problem_text}
    v = validate_semantic_program(program)
    if v.spec is None:
        hang["validation"] = {"ok": False, "errors": [str(e)[:200] for e in (v.errors or [])][:5]}
        hang["observed"] = "refused@validation"
        return hang
    try:
        _sp, out, _sc = W.chay(contract, program)
        hang["route"] = {"servable": out.servable, "stage": out.stage_reached, "reason_code": out.reason_code,
                         "refusal_cause": out.refusal_cause, "construction_binding": out.construction_binding,
                         "subjects": list(out.reason_subjects or []), "details": [str(d)[:220] for d in out.details[:8]]}
    except Exception as e:  # noqa: BLE001 — một ca nổ là một quan sát, không giết cả lượt dò
        hang["route"] = {"error": f"{type(e).__name__}: {e}"[:300]}
    env = attach_learner_reason(asyncio.run(GEN._run_frozen_program(contract.problem_text, contract, v.spec)))
    gt = {o["id"]: o.get("value") for o in (env.get("scene3d") or {}).get("objects", []) if o.get("type") == "quantity"}
    hang["response"] = {"status": env.get("status"), "stage_reached": env.get("stage_reached"),
                        "error_code": env.get("error_code"), "reason_code": env.get("reason_code"),
                        "refusal_cause": env.get("refusal_cause"), "learner_reason": env.get("learner_reason"),
                        "shown_d_kq": gt.get("d_kq")}
    served = env.get("status") == "ok"
    hang["observed"] = "served" if served else f"refused@{env.get('stage_reached')}"
    hang["matches_label"] = (served and nhan["expect"] == "served") or (
        not served and nhan["expect"] == "refused" and env.get("refusal_cause") != "SOURCE")
    return hang


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True, help="before | after")
    a = ap.parse_args()
    sha = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    ra = RUN / "results" / f"LITERAL_TARGET_PROBE_{a.tag}_{sha}.json"
    if ra.exists():
        raise SystemExit(f"{ra.name} đã có — không ghi đè")
    rows = [mot_hang(c) for c in LABELS["rows"]]
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(json.dumps({"probe": "W20_LITERAL_TARGET", "tag": a.tag, "measured_at_commit": sha, "model_calls": 0,
                              "boundary": "app.ai.pipeline.run_pipeline (semantic_route=serve, LLM_ONLY) + route.verify_and_compile",
                              "rows_matching_label": sum(1 for r in rows if r.get("matches_label")), "rows": rows},
                             ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    for r in rows:
        rt = r.get("route", {})
        print(f"{r['id']:42} expect {r['expect']:8} | {r['observed']:30} | route {rt.get('stage')} {rt.get('reason_code')}"
              f" {rt.get('construction_binding')} | d_kq {r.get('response', {}).get('shown_d_kq')} | ok={r.get('matches_label')}")
    print("wrote", ra.relative_to(ROOT).as_posix(), "| matching", sum(1 for r in rows if r.get("matches_label")), "/", len(rows))


if __name__ == "__main__":
    main()
