# -*- coding: utf-8 -*-
"""W14 Task 5a — phân loại TỪNG nơi gọi `check_grounding` / `verify_and_compile` dưới chính
sách nguồn đề tường minh (`NguonDe.CAN_DE` mặc định; `FIXTURE_TIN_CAY` phải khai).

Test: bảng phân loại viết tay bên dưới (mỗi hàng một lý do), đối chiếu với vết của lượt
full suite có plugin `w14_trace_thieu_de` (mọi nút test mà grounding từ chối
`SOURCE_TEXT_MISSING`, kể cả nút vẫn xanh). Script: quét tĩnh + trạng thái chạy trong W14.
0 lượt gọi model. Chạy từ gốc kho (không ghi đè):
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/trust_policy_callers.py \
    <trace.json> <out.json>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
KHONG_DO = ["source evidence (problem text)", "assumption gate"]

#: Lớp: PRODUCTION_BEHAVIOR (gắn đề thật, chạy đủ grounding) · ISOLATED_UNIT_FIXTURE (khai
#: `FIXTURE_TIN_CAY`, đo một cổng khác) · POLICY_UNDER_TEST · EXPECTATION_EXTENDED_BY_PLAN.
TESTS = [
    ("backend/tests/geometry/test_prism_production_route.py", "_pyramid_control_contract", "PRODUCTION_BEHAVIOR",
     "canonical contract of the triangular-pyramid family already returned its text but did not carry it; now problem_text=text (also the tier-A generator, formula-provenance and learner-surface fixtures)"),
    ("backend/tests/geometry/test_geometry_wave2.py", "_hop_dong_geo_09", "PRODUCTION_BEHAVIOR",
     "canonical contract of dev case geo_09 now carries that case's real text (docs/evaluation/geometry/dev/cases.json); served with full source checks; used by geo_09 route tests, face_vertex_resolver, scene3d_integration and the Phase 5 harness tests"),
    ("backend/tests/geometry/test_grounding_feedback_loop.py", "_HOP_DONG", "PRODUCTION_BEHAVIOR",
     "the repair loop is production code and always sees a contract with text; the contract now carries the text the tests pass to stage_semantic_program; the corrected program is grounded by 'AB = 1'"),
    ("backend/tests/geometry/test_failure_details.py", "test_C1a_details_noi_ro_CAI_GI_lech, test_BON_dang_hong_deu_co_du_hinh_dang", "PRODUCTION_BEHAVIOR",
     "harness stubs now return contracts carrying the geo_09 text; the four-layer test asserts the INTENDED stage per case (two cases had stayed green while being stopped earlier) and gained the W14 formation layer"),
    ("backend/tests/geometry/test_model_assumption_boundary.py", "module", "ISOLATED_UNIT_FIXTURE",
     "model-assumption boundary rules of grounding on synthetic contracts that never had a text"),
    ("backend/tests/semantic_program/test_grounding_gate.py", "module", "ISOLATED_UNIT_FIXTURE",
     "P2 grounding citation/value rules on synthetic contracts"),
    ("backend/tests/geometry/test_literal_justification.py", "module", "ISOLATED_UNIT_FIXTURE",
     "literal justification classes A/B/C on synthetic contracts"),
    ("backend/tests/geometry/test_coordinate_grounding.py", "module", "ISOLATED_UNIT_FIXTURE",
     "coordinate grounding rules on synthetic contracts"),
    ("backend/tests/geometry/test_fact_identity.py", "module", "ISOLATED_UNIT_FIXTURE",
     "fact identity / citation normalisation rules on synthetic contracts"),
    ("backend/tests/geometry/test_geometry_wave2.py", "grounding-rule tests on _HD_RONG + test_CHUONG_TRINH_KHAI_DAP_AN_bi_chan_o_dung_tang_dau", "ISOLATED_UNIT_FIXTURE",
     "model-assumption channel rules and the answer-as-assumption refusal on synthetic contracts"),
    ("backend/tests/semantic_program/test_ir_ergonomics.py", "module", "ISOLATED_UNIT_FIXTURE",
     "declare_point provenance must still be enforced by grounding (synthetic contract)"),
    ("backend/tests/geometry/test_validator_name_normalization.py", "module", "ISOLATED_UNIT_FIXTURE",
     "historical phase7a pilot artifacts store no problem text (pre-W12, immutable) + synthetic grounding checks; the regression target is name normalisation; 62 rename-invariance nodes had stayed green comparing two missing-text refusals"),
    ("backend/tests/geometry/test_evaluation_integrity_7a1.py", "module", "ISOLATED_UNIT_FIXTURE",
     "historical phase7a pilot artifacts store no problem text; the regression target is learner-surface name resolution"),
    ("backend/tests/geometry/test_name_authority.py", "module", "ISOLATED_UNIT_FIXTURE",
     "name-authority map plumbing on a synthetic contract"),
    ("backend/tests/semantic_program/test_predicate_verdict.py", "module", "ISOLATED_UNIT_FIXTURE",
     "predicate verdict and learner-surface gating on synthetic programs"),
    ("backend/tests/semantic_program/test_learner_surface.py", "test_route_van_serve_khi_be_mat_du, test_route_ha_servable_va_giu_executable", "ISOLATED_UNIT_FIXTURE",
     "learner-surface gate on the synthetic p02 contract"),
    ("backend/tests/geometry/test_prism_primitive_compiler.py", "test_provenance_strict_invariants", "ISOLATED_UNIT_FIXTURE",
     "LAYOUT_DERIVED provenance rule on a synthetic prism contract"),
    ("backend/tests/semantic_program/test_capability_honesty.py", "test_gm10_KHONG_bi_chan_khi_KHONG_co_de", "ISOLATED_UNIT_FIXTURE",
     "control experiment 'without the text the honesty rule stops concluding': the unchecked path now exists only when declared"),
    ("backend/tests/geometry/test_assumption_gate.py", "test_hop_dong_san_pham_thieu_de_bi_tu_choi, trust-policy tests", "POLICY_UNDER_TEST",
     "the default refusal SOURCE_TEXT_MISSING and the explicit trusted fixture are what these tests assert"),
    ("backend/tests/geometry/test_source_grounding_closure.py", "test_grounding_refusal_codes_are_a_closed_stable_set", "EXPECTATION_EXTENDED_BY_PLAN",
     "the closed source-code set gains SOURCE_TEXT_MISSING exactly as Task 5a Step 2 specifies (and it is in KHONG_SUA_NGUON)"),
]

#: Script chạy TRONG W14 (T3 hoặc bộ sinh bằng chứng) — trạng thái đã kiểm.
SCRIPT_DA_KIEM = {
    "replay_demo_cases.py": ("T3", "stored demo contracts carry their text; DEMO_REPLAY_PASS 5/5 and the n4 refusal unchanged under CAN_DE"),
    "audit_demo_crash_surface.py": ("T3", "no direct route call; BIÊN ĐÚNG KỲ VỌNG 6/6, 0 escaped 500s under CAN_DE"),
    "generate_generic_tier_a_fixtures.py": ("W14_EVIDENCE_PRODUCER", "canonical contracts carry text (triangular pyramid via the fixed factory); exercised by its tests"),
    "cross_domain_matrix.py": ("ISOLATED_UNIT_FIXTURE", "synthetic per-class payloads without text; `servable` would have silently turned False — now declares FIXTURE_TIN_CAY at its one route call"),
}


def _quet_script() -> list[dict]:
    ra = []
    tests = "\n".join(p.read_text(encoding="utf-8", errors="replace")
                      for p in (ROOT / "backend" / "tests").rglob("*.py"))
    goc = sorted({*(ROOT / "backend" / "scripts").glob("*.py"), ROOT / "backend/scripts/audit_demo_crash_surface.py"})
    for p in goc:
        t = p.read_text(encoding="utf-8", errors="replace")
        if p.name not in SCRIPT_DA_KIEM and not re.search(r"verify_and_compile|check_grounding", t):
            continue
        s = re.escape(p.stem)
        # Chỉ tính khi test THẬT SỰ nạp/chạy script (import hoặc đường dẫn), không tính lời nhắc tên.
        dung = bool(re.search(rf"scripts\.{s}\b|from scripts import [^\n]*\b{s}\b|scripts[/\\]+{s}\.py|[\"']{s}\.py[\"']"
                              rf"|^\s*from {s} import|^\s*import {s}\b", tests, re.M))
        lop, ly_do = SCRIPT_DA_KIEM.get(p.name, (
            "EXERCISED_BY_TESTS_NO_TEXTLESS_CALL_OBSERVED" if dung else "NOT_EXERCISED_IN_W14",
            ("referenced by the test suite; the traced full run saw no SOURCE_TEXT_MISSING from it" if dung else
             "historical measurement/live script, not run in W14; under CAN_DE a textless contract now fails closed "
             "(SOURCE_TEXT_MISSING) instead of skipping source checks silently")))
        ra.append({"caller": p.relative_to(ROOT).as_posix(), "class": lop, "reason": ly_do,
                   "static_signal": {"problem_text_mentions": len(re.findall(r"problem_text", t)),
                                     "build_request_contract": len(re.findall(r"build_request_contract\(", t)),
                                     "RequestContract_direct": len(re.findall(r"RequestContract\(", t))}})
    return ra


def run(trace: dict) -> dict:
    return {
        "inventory": "W14_TRUST_POLICY_CALLERS", "model_calls": 0,
        "policy": "check_grounding / verify_and_compile take nguon: NguonDe = CAN_DE; an empty problem_text "
                  "under CAN_DE is refused SOURCE_TEXT_MISSING (stage grounding, never sent to repair); only an "
                  "explicit NguonDe.FIXTURE_TIN_CAY argument takes the unchecked path and records "
                  "source_check = UNCHECKED_TRUSTED_FIXTURE",
        "isolated_fixture_entry": "backend/tests/nguon_fixture.py (a module importing from it declares ISOLATED_UNIT_FIXTURE)",
        "not_measured_by_isolated_callers": KHONG_DO,
        "tests": [{"caller": f, "scope": s, "class": c, "reason": r} for f, s, c, r in TESTS],
        "scripts": _quet_script(),
        "observed_source_text_missing_nodes_after_classification": trace,
    }


if __name__ == "__main__":
    trace = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}; pass a new output path")
    out.write_text(json.dumps(run(trace), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(out)
