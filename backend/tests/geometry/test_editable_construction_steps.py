# -*- coding: utf-8 -*-
"""Comprehensive verification suite for AXO Editable Construction Steps & Feedback Pipeline.

Covers:
- Zero-LLM Vietnamese step parser & equivalence detection
- Dependency DAG cycle & missing-reference detection
- Topological partial rebuild on Sample 11 (chop-mat-cau-ngoai-tiep) and Sample 1 (chop-thiet-dien-ba-diem)
- Exact Kernel (Fraction / Radical / Gram Metric) verification & continuity checks
- Fail-closed HTTP 422 rollback preserving last committed Scene3D and revision logs
- Owner isolation, zero AI quota consumption, reload state restoration
- Verified feedback lifecycle, contradiction quarantine, leakage-free splits, and MODEL_NOT_TRAINED reporting
"""
from __future__ import annotations

import copy
import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func, select

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR / "scripts"))

import build_advanced_geometry_samples as adv_samples
from app.main import app
from app.persistence.classroom_models import AnalysisUsageLedger, AuthSession
from app.persistence.db import SessionLocal
from app.persistence.step_edit_models import (
    StepEditRevisionRecord,
    StepEditSessionRecord,
    VerifiedStepFeedbackRecord,
    ensure_step_edit_tables,
)
from app.simulation.geometry.exact import Point3, hf
from app.simulation.geometry_functions.feedback_dataset import (
    DATASET_SCHEMA_VERSION,
    FIXED_STEP_PARSER_BENCHMARK,
    MODEL_STATUS,
    UntrainedLocalStepIntentAdapter,
    approve_step_feedback,
    canonical_problem_group_key,
    export_step_feedback_dataset,
)
from app.simulation.geometry_functions.step_editor import (
    StepEditRefusal,
    build_construction_dependency_graph,
    execute_step_edit,
    parse_vietnamese_construction_step,
)


@pytest.fixture(scope="module")
def advanced_samples_by_id() -> dict[str, dict]:
    ensure_step_edit_tables()
    rows = adv_samples.build_all_advanced_samples()
    return {item["id"]: item for item in rows}


def _find_obj(scene: dict, oid: str) -> dict | None:
    return next((o for o in scene.get("objects") or [] if o.get("id") == oid), None)


def _exact_xyz_equal(a: list, b: list) -> bool:
    from app.simulation.geometry.radical import parse_exact

    return len(a) == len(b) == 3 and all(parse_exact(a[i]) == parse_exact(b[i]) for i in range(3))


# ── Test 3: Parser & Semantic Equivalence ─────────────────────────────────────


def test_parser_supports_compound_midpoint_and_perpendicular_plane():
    text = "Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB."
    parsed = parse_vietnamese_construction_step(text)
    assert [c.op for c in parsed.clauses] == ["midpoint", "plane_perpendicular_to_line"]
    assert parsed.clauses[0].output_symbol == "H"
    assert parsed.clauses[0].point_inputs == ("A", "B")
    assert parsed.clauses[1].output_symbol == "(α)"
    assert parsed.clauses[1].point_inputs == ("H", "A", "B")
    assert parsed.clauses[1].line_inputs == ()
    assert parsed.registry_operations == ("midpoint", "plane_perpendicular_to_line")


def test_parser_precondition_rejects_missing_inline_point_h(advanced_samples_by_id):
    scene = copy.deepcopy(advanced_samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    with pytest.raises(StepEditRefusal) as exc_info:
        execute_step_edit(
            scene3d=scene,
            step_id="mp_tt_AB",
            step_index=7,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
            target_ids=["mp_tt_AB"],
            absorbed_ids=["M_AB"],
        )
    assert exc_info.value.error_code == "MISSING_DEPENDENCY"
    assert exc_info.value.failed_stage == "planner"


# ── Test 4: Refusals (Unsupported, Cycle, Degenerate, Curved) ────────────────


def test_step_editor_rejects_cycle_and_collinear_and_curved(advanced_samples_by_id):
    scene = copy.deepcopy(advanced_samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])

    # Unsupported freeform phrasing
    with pytest.raises(StepEditRefusal) as e1:
        execute_step_edit(
            scene3d=scene,
            step_id="mp_tt_AB",
            step_index=7,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Làm đẹp hình chóp tự động.",
            target_ids=["mp_tt_AB"],
        )
    assert e1.value.error_code == "UNSUPPORTED_STEP_SYNTAX"

    # Curved out-of-scope refusal
    with pytest.raises(StepEditRefusal) as e2:
        execute_step_edit(
            scene3d=scene,
            step_id="mp_tt_AB",
            step_index=7,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Vẽ mặt nón ngoại tiếp đáy hình vuông.",
            target_ids=["mp_tt_AB"],
        )
    assert e2.value.error_code == "UNSUPPORTED_CURVED_OR_FREEFORM_STEP"

    # Cycle detection: editing early point M using downstream circumscribed center I
    with pytest.raises(StepEditRefusal) as e3:
        execute_step_edit(
            scene3d=scene,
            step_id="M",
            step_index=5,
            previous_instruction="Xác định trung điểm M của SA",
            edited_instruction="Xác định trung điểm M của I và A.",
            target_ids=["M"],
        )
    assert e3.value.error_code == "CYCLE_DEPENDENCY"

    # Zero-length segment operand ("OO") on valid existing point O
    with pytest.raises(StepEditRefusal) as e4:
        execute_step_edit(
            scene3d=scene,
            step_id="mp_tt_AB",
            step_index=7,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Dựng mặt phẳng (β) qua O và vuông góc với OO.",
            target_ids=["mp_tt_AB"],
        )
    assert e4.value.error_code == "INVALID_OPERAND"


# ── Test 5: Sample 11 Partial Topological Rebuild & Equivalence ──────────────


def test_sample11_compound_midpoint_and_perpendicular_plane_partial_rebuild(advanced_samples_by_id):
    base_scene = copy.deepcopy(advanced_samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])

    result = execute_step_edit(
        scene3d=base_scene,
        step_id="mp_tt_AB",
        step_index=7,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
    )

    assert result["status"] == "committed"
    assert result["mode"] == "PARTIAL_TOPOLOGICAL_REBUILD"
    assert "H" in result["dependency_summary"]["created_ids"]
    assert "M_AB" in result["dependency_summary"]["retired_ids"]

    recomputed = set(result["dependency_summary"]["recomputed_ids"])
    skipped = set(result["dependency_summary"]["skipped_unaffected_ids"])
    # Transitive closure downstream of mp_tt_AB must include truc_day, I, R, V_cau, cau_ngoai_tiep
    assert {"truc_day", "I", "cau_ngoai_tiep", "R", "V_cau"}.issubset(recomputed)
    # Earlier / parallel independent objects MUST be skipped cleanly
    assert {"O", "M", "mp_tt_AD", "mp_tt_SA", "S", "A", "B", "C", "D"}.issubset(skipped)

    rebuilt = result["scene3d"]
    h_obj = _find_obj(rebuilt, "H")
    assert h_obj is not None
    assert h_obj["type"] == "point3"
    assert h_obj["notation"] == "H"
    assert "Trung điểm" in h_obj["label"]
    assert h_obj["source"]["inline_step_parent"] == "mp_tt_AB"
    assert _find_obj(rebuilt, "M_AB") is None

    a_xyz = _find_obj(rebuilt, "A")["xyz"]
    b_xyz = _find_obj(rebuilt, "B")["xyz"]
    from app.simulation.geometry.radical import parse_exact

    expected_mid = [(parse_exact(a_xyz[i]) + parse_exact(b_xyz[i])) / 2 for i in range(3)]
    assert all(parse_exact(h_obj["xyz"][i]) == expected_mid[i] for i in range(3))

    # Validation checks pass including continuity and bisector verification
    assert result["validation_result"]["passed"] is True
    assert result["validation_result"]["continuity"]["passed"] is True

    # Follow-up wording-only equivalence edit (now H already exists on canvas!)
    equiv_result = execute_step_edit(
        scene3d=rebuilt,
        step_id="mp_tt_AB",
        step_index=7,
        previous_instruction="Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
        edited_instruction="Dựng mặt phẳng (α) qua H vuông góc với AB.",
        target_ids=["mp_tt_AB"],
        step_overrides=result["step_overrides"],
    )
    assert equiv_result["status"] == "committed"
    assert equiv_result["mode"] == "NO_OP_EQUIVALENT"
    assert equiv_result["before_after_diff"]["changed"] is False


def test_sample1_geometry_changing_edit_updates_downstream_section_diff(advanced_samples_by_id):
    base_scene = copy.deepcopy(advanced_samples_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])
    objs = base_scene["objects"]
    # Find divide/midpoint step in sample 1 (point K/M/N/P depends on edge)
    editable_pt = next(
        o
        for o in objs
        if o.get("type") == "point3"
        and o.get("origin") == "derived"
        and len(o.get("depends") or []) == 2
        and all(_find_obj(base_scene, d).get("type") == "point3" for d in o["depends"])
    )
    oid = editable_pt["id"]
    p1, p2 = editable_pt["depends"]

    result = execute_step_edit(
        scene3d=base_scene,
        step_id=oid,
        step_index=2,
        previous_instruction=editable_pt.get("label") or oid,
        edited_instruction=f"Lấy điểm {oid} trên {p1}{p2} sao cho {p1}{oid} = 2{oid}{p2}.",
        target_ids=[oid],
    )
    assert result["status"] == "committed"
    assert result["before_after_diff"]["changed"] is True
    assert oid in result["before_after_diff"]["changed_objects"]
    before_xyz = result["before_after_diff"]["changed_objects"][oid]["before"]["xyz"]
    after_xyz = result["before_after_diff"]["changed_objects"][oid]["after"]["xyz"]
    assert not _exact_xyz_equal(before_xyz, after_xyz)

    # Confirm skipped objects outside oid's downstream closure remained byte-identical
    for skipped_id in result["dependency_summary"]["skipped_unaffected_ids"][:10]:
        b_obj = _find_obj(base_scene, skipped_id)
        a_obj = _find_obj(result["scene3d"], skipped_id)
        if b_obj and a_obj and "xyz" in b_obj:
            assert b_obj["xyz"] == a_obj["xyz"]


# ── Test 6 & Test 7: HTTP Endpoints, Isolation, Persistence, Feedback & Model Status ──


def test_http_endpoints_commit_rollback_isolation_quota_and_dataset(advanced_samples_by_id):
    client = TestClient(app)
    base_scene = copy.deepcopy(advanced_samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    session_id = f"test-sid-{uuid.uuid4().hex[:10]}"
    client_hdr_a = {"X-Axo-Client-Session": f"owner-a-{uuid.uuid4().hex[:8]}"}
    client_hdr_b = {"X-Axo-Client-Session": f"owner-b-{uuid.uuid4().hex[:8]}"}

    with SessionLocal() as db:
        ledger_before = db.execute(select(func.count()).select_from(AnalysisUsageLedger)).scalar_one()

    # 1. Valid compound edit via API
    res_ok = client.post(
        "/api/simulation/steps/edit",
        headers=client_hdr_a,
        json={
            "session_id": session_id,
            "problem_key": "chop-mat-cau-ngoai-tiep",
            "step_id": "mp_tt_AB",
            "step_index": 7,
            "previous_instruction": "Dựng mặt phẳng trung trực (α) của cạnh AB",
            "edited_instruction": "Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
            "target_ids": ["mp_tt_AB"],
            "absorbed_ids": ["M_AB"],
            "scene3d": base_scene,
        },
    )
    assert res_ok.status_code == 200, res_ok.text
    body_ok = res_ok.json()
    assert body_ok["status"] == "committed"
    assert body_ok["llm_calls"] == 0
    assert body_ok["quota_charged"] is False
    assert body_ok["feedback_status"] == "GEOMETRY_VERIFIED"
    assert body_ok["dataset_eligibility"] == "INELIGIBLE"
    committed_digest = body_ok["after_scene_digest"]
    good_feedback_id = body_ok["feedback_id"]

    # 2. Invalid edit -> HTTP 422 rollback, committed Scene3D untouched!
    res_bad = client.post(
        "/api/simulation/steps/edit",
        headers=client_hdr_a,
        json={
            "session_id": session_id,
            "problem_key": "chop-mat-cau-ngoai-tiep",
            "step_id": "mp_tt_AB",
            "step_index": 7,
            "previous_instruction": "Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
            "edited_instruction": "Dựng mặt phẳng (α) đi qua Q và vuông góc với AB.",
            "target_ids": ["mp_tt_AB"],
            "scene3d": body_ok["scene3d"],
        },
    )
    assert res_bad.status_code == 422
    body_bad = res_bad.json()
    assert body_bad["status"] == "rolled_back"
    assert body_bad["error_code"] == "MISSING_DEPENDENCY"
    assert body_bad["draft_preserved"] is True
    assert body_bad["preserved_scene_digest"] == committed_digest
    bad_feedback_id = body_bad["feedback_id"]

    # 3. Reload state persistence restores committed scene with H, not rolled back!
    res_state = client.get(f"/api/simulation/sessions/{session_id}/state", headers=client_hdr_a)
    assert res_state.status_code == 200
    state_body = res_state.json()
    assert state_body["found"] is True
    assert state_body["revision_count"] == 2
    assert state_body["revisions"][0]["execution_status"] == "COMMITTED"
    assert state_body["revisions"][1]["execution_status"] == "ROLLED_BACK"
    assert _find_obj(state_body["committed_scene"], "H") is not None

    # 4. Owner isolation: owner B cannot read owner A's session or approve owner A's feedback
    res_iso = client.get(f"/api/simulation/sessions/{session_id}/state", headers=client_hdr_b)
    assert res_iso.status_code == 200
    assert res_iso.json()["found"] is False

    res_cross_approve = client.post(
        f"/api/simulation/feedback/{good_feedback_id}/approve",
        headers=client_hdr_b,
        json={"approved": True},
    )
    assert res_cross_approve.status_code == 404

    # 5. Rejected edit cannot be approved into training dataset
    res_fail_approve = client.post(
        f"/api/simulation/feedback/{bad_feedback_id}/approve",
        headers=client_hdr_a,
        json={"approved": True},
    )
    assert res_fail_approve.status_code == 422

    # 6. Verified edit CAN be approved to TRAINING_ELIGIBLE
    res_approve = client.post(
        f"/api/simulation/feedback/{good_feedback_id}/approve",
        headers=client_hdr_a,
        json={"approved": True, "promote_to_training": True, "reviewer_note": "Exact verified"},
    )
    assert res_approve.status_code == 200
    assert res_approve.json()["user_acceptance_status"] == "TRAINING_ELIGIBLE"
    assert res_approve.json()["dataset_eligibility"] == "ELIGIBLE"

    # 7. Honest local model status endpoint
    res_status = client.get("/api/simulation/feedback/status", headers=client_hdr_a)
    assert res_status.status_code == 200
    status_body = res_status.json()
    assert status_body["model_status"] == "MODEL_NOT_TRAINED"
    assert status_body["model_trained"] is False
    assert status_body["training_eligible_count"] >= 1

    # 8. Zero quota charged
    with SessionLocal() as db:
        ledger_after = db.execute(select(func.count()).select_from(AnalysisUsageLedger)).scalar_one()
        assert ledger_after == ledger_before


def test_feedback_dataset_dedup_quarantine_and_leakage_free_split():
    with SessionLocal() as db:
        ensure_step_edit_tables(db.get_bind())
        tag = uuid.uuid4().hex[:8]
        grp = f"grp-quarantine-{tag}"

        def _add_fb(fid: str, orig: str, corr: str, sig: str):
            row = VerifiedStepFeedbackRecord(
                feedback_id=fid,
                revision_id=f"rev-{fid}",
                owner_scope="test:dataset",
                session_id=f"sid-{tag}",
                problem_group_key=grp,
                original_step=orig,
                corrected_step=corr,
                original_intent_json='{"clauses": []}',
                corrected_intent_json=f'{{"intent_signature": "{sig}", "clauses": []}}',
                geometry_context_json="{}",
                dependency_context_json="{}",
                registry_operations_json='["midpoint"]',
                validation_result_json='{"passed": true}',
                execution_result_json='{"status": "committed"}',
                user_acceptance_status="TRAINING_ELIGIBLE",
                dataset_eligibility="ELIGIBLE",
            )
            db.add(row)
            return row

        # Duplicate pair -> should deduplicate into 1
        _add_fb(f"fb-d1-{tag}", "Dựng (α)", "Gọi H là trung điểm AB.", "sig-unique")
        _add_fb(f"fb-d2-{tag}", "Dựng (α)", "Gọi H là trung điểm AB.", "sig-unique")

        # Contradiction pair -> identical corrected text, differing intent_signature -> quarantined
        _add_fb(f"fb-c1-{tag}", "Dựng (β)", "Dựng (β) qua M.", "sig-A")
        _add_fb(f"fb-c2-{tag}", "Dựng (β)", "Dựng (β) qua M.", "sig-B")
        db.flush()

        manifest = export_step_feedback_dataset(db)
        assert manifest["schema_version"] == DATASET_SCHEMA_VERSION
        assert manifest["model_status"] == MODEL_STATUS == "MODEL_NOT_TRAINED"
        assert manifest["quarantined_count"] >= 2

        # Group-split invariant: no problem_group_key may appear in more than 1 split
        groups_by_split = {
            split_name: {item["problem_group_key"] for item in items}
            for split_name, items in manifest["splits"].items()
        }
        assert groups_by_split["train"].isdisjoint(groups_by_split["val"])
        assert groups_by_split["train"].isdisjoint(groups_by_split["test"])
        assert groups_by_split["val"].isdisjoint(groups_by_split["test"])

        # Clean up test synthetic rows so dev DB stays tidy
        db.rollback()


def test_local_model_adapter_benchmark_reports_not_trained():
    adapter = UntrainedLocalStepIntentAdapter()
    assert adapter.model_status == "MODEL_NOT_TRAINED"
    bench = adapter.evaluate_benchmark()
    assert len(FIXED_STEP_PARSER_BENCHMARK) == 24
    assert bench["model_status"] == "MODEL_NOT_TRAINED"
    assert bench["model_trained"] is False
    assert bench["case_count"] == 24
    assert bench["passed_count"] == 24, [c for c in bench["cases"] if not c["ok"]]
    assert bench["parser_baseline_accuracy"] == 1.0


# ── AXO V2.1 Semantic Stabilization, Role Verification & Counterexamples (§2.2, §8.B) ──


@pytest.mark.parametrize(
    "phrasing",
    [
        "Dựng mặt phẳng (α) đi qua O và vuông góc với AB.",
        "Dựng mặt phẳng (α) đi qua tâm O và vuông góc với AB.",
        "Dựng mặt phẳng (α) qua tâm O của hình vuông ABCD và vuông góc với AB.",
        "Dựng mặt phẳng (α) đi qua trung điểm O của AC và vuông góc với AB.",
        "Dựng (α) đi qua O và vuông góc với AB.",
        "Mặt phẳng (α) đi qua O và vuông góc với AB.",
        "Dựng mặt phẳng (alpha) đi qua O và vuông góc với ab.",
    ],
)
def test_v21_sample11_center_O_variants_rebuild_and_preserve_circumscribed_sphere(advanced_samples_by_id, phrasing):
    base_scene = copy.deepcopy(advanced_samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    res = execute_step_edit(
        scene3d=base_scene,
        step_id="mp_tt_AB",
        step_index=7,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction=phrasing,
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
    )
    assert res["status"] == "committed"
    assert res["mode"] == "PARTIAL_TOPOLOGICAL_REBUILD"
    assert "M_AB" in res["dependency_summary"]["retired_ids"]
    assert "O" in res["dependency_summary"]["reused_ids"]
    rebuilt = res["scene3d"]
    alpha = _find_obj(rebuilt, "mp_tt_AB")
    assert alpha is not None
    assert alpha["depends"] == ["O", "ab"]
    # Exact mathematical check: (α) passes through O and is identical to perpendicular bisector of AB (point (2,2,0) & normal parallel AB -> contains M_AB (2,0,0))
    from app.simulation.geometry import Plane3, Vec3, predicates as P

    pl = Plane3(Vec3.of(*alpha["point"]), Vec3.of(*alpha["normal"]))
    assert P.point_on_plane(Vec3.of(2, 0, 0), pl)
    assert _find_obj(rebuilt, "I")["xyz"] == ["2", "2", "2"]
    assert _find_obj(rebuilt, "R")["value"] == "2√3"


def test_v21_counterexamples_reject_non_bisector_M_false_center_A_and_missing_O(advanced_samples_by_id):
    base_scene = copy.deepcopy(advanced_samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])

    # 1. Counterexample: M is midpoint of SA, NOT equidistant from A and B -> breaks downstream circumscribed sphere!
    with pytest.raises(StepEditRefusal) as e_m:
        execute_step_edit(
            scene3d=copy.deepcopy(base_scene),
            step_id="mp_tt_AB",
            step_index=7,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Dựng mặt phẳng (α) đi qua M và vuông góc với AB.",
            target_ids=["mp_tt_AB"],
            absorbed_ids=["M_AB"],
        )
    assert e_m.value.error_code == "DOWNSTREAM_CIRCUMSCRIBED_SPHERE_BROKEN"

    # 2. Counterexample: vertex A falsely claimed to be "tâm A của hình vuông ABCD" -> refused!
    with pytest.raises(StepEditRefusal) as e_a:
        execute_step_edit(
            scene3d=copy.deepcopy(base_scene),
            step_id="mp_tt_AB",
            step_index=7,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Dựng mặt phẳng (α) qua tâm A của hình vuông ABCD và vuông góc với AB.",
            target_ids=["mp_tt_AB"],
            absorbed_ids=["M_AB"],
        )
    assert e_a.value.error_code == "ROLE_ASSERTION_FAILED"

    # 3. Counterexample: O falsely claimed to be midpoint of AB -> refused!
    with pytest.raises(StepEditRefusal) as e_mid:
        execute_step_edit(
            scene3d=copy.deepcopy(base_scene),
            step_id="mp_tt_AB",
            step_index=7,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Dựng mặt phẳng (α) đi qua trung điểm O của AB và vuông góc với AB.",
            target_ids=["mp_tt_AB"],
            absorbed_ids=["M_AB"],
        )
    assert e_mid.value.error_code in {"ROLE_ASSERTION_FAILED", "SYMBOL_CONFLICT"}

    # 4. Counterexample: scene where O does NOT exist before step -> missing dependency!
    scene_without_O = copy.deepcopy(base_scene)
    scene_without_O["objects"] = [
        o for o in scene_without_O["objects"] if o["id"] not in ("O", "doan_OI")
    ]
    scene_without_O["events"] = [
        ev for ev in scene_without_O["events"] if ev.get("object") not in ("O", "doan_OI")
    ]
    scene_without_O["formation"] = None
    with pytest.raises(StepEditRefusal) as e_no_o:
        execute_step_edit(
            scene3d=scene_without_O,
            step_id="mp_tt_AB",
            step_index=7,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Dựng mặt phẳng (α) đi qua O và vuông góc với AB.",
            target_ids=["mp_tt_AB"],
            absorbed_ids=["M_AB"],
        )
    assert e_no_o.value.error_code == "MISSING_DEPENDENCY"


def test_v21_prior_step_ids_and_early_middle_final_chain_plus_http_rollback(advanced_samples_by_id):
    base_scene = copy.deepcopy(advanced_samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])

    # Simulate pedagogical reorder where raw event of O appears after mp_tt_AB, yet UI prior_step_ids has O
    reordered_scene = copy.deepcopy(base_scene)
    evs = reordered_scene["events"]
    ev_o = next(e for e in evs if e.get("object") == "O")
    ev_doan_oi = next(e for e in evs if e.get("object") == "doan_OI")
    evs.remove(ev_o)
    idx_oi = evs.index(ev_doan_oi)
    evs.insert(idx_oi, ev_o)
    for k, e in enumerate(evs):
        e["step_index"] = k
    reordered_scene["formation"] = None

    # Without prior_step_ids, raw order puts O after mp_tt_AB -> CYCLE_DEPENDENCY
    with pytest.raises(StepEditRefusal) as e_raw:
        execute_step_edit(
            scene3d=copy.deepcopy(reordered_scene),
            step_id="mp_tt_AB",
            step_index=7,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Dựng mặt phẳng (α) đi qua O và vuông góc với AB.",
            target_ids=["mp_tt_AB"],
            absorbed_ids=["M_AB"],
        )
    assert e_raw.value.error_code == "CYCLE_DEPENDENCY"

    # With prior_step_ids from UI plan -> hoists O cleanly with zero continuity errors!
    res_hoisted = execute_step_edit(
        scene3d=copy.deepcopy(reordered_scene),
        step_id="mp_tt_AB",
        step_index=7,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Dựng mặt phẳng (α) đi qua O và vuông góc với AB.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
        prior_step_ids=["A", "B", "C", "D", "day_ABCD", "S", "O", "M"],
    )
    assert res_hoisted["status"] == "committed"
    assert res_hoisted["validation_result"]["passed"] is True

    # Early, middle, final step edits + multi-edit rollback chain over HTTP
    client = TestClient(app)
    sid = f"v21-chain-{uuid.uuid4().hex[:10]}"
    hdr = {"X-Axo-Client-Session": f"v21-owner-{uuid.uuid4().hex[:8]}"}

    # Step 1 (early polygon): edit day_ABCD
    r_early = client.post(
        "/api/simulation/steps/edit",
        headers=hdr,
        json={
            "session_id": sid,
            "problem_key": "chop-mat-cau-ngoai-tiep",
            "step_id": "day_ABCD",
            "step_index": 0,
            "previous_instruction": "Dựng mặt đáy ABCD",
            "edited_instruction": "Dựng đáy ABCD.",
            "target_ids": ["day_ABCD"],
            "absorbed_ids": [],
            "scene3d": base_scene,
        },
    )
    assert r_early.status_code == 200, r_early.text

    # Step 8 (middle): H + perp plane
    r_mid1 = client.post(
        "/api/simulation/steps/edit",
        headers=hdr,
        json={
            "session_id": sid,
            "problem_key": "chop-mat-cau-ngoai-tiep",
            "step_id": "mp_tt_AB",
            "step_index": 7,
            "previous_instruction": "Dựng mặt phẳng trung trực (α) của cạnh AB",
            "edited_instruction": "Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
            "target_ids": ["mp_tt_AB"],
            "absorbed_ids": ["M_AB"],
            "prior_step_ids": ["A", "B", "C", "D", "S", "O", "M"],
            "scene3d": r_early.json()["scene3d"],
        },
    )
    assert r_mid1.status_code == 200, r_mid1.text

    # Step 8 again: switch from H to O
    r_mid2 = client.post(
        "/api/simulation/steps/edit",
        headers=hdr,
        json={
            "session_id": sid,
            "problem_key": "chop-mat-cau-ngoai-tiep",
            "step_id": "mp_tt_AB",
            "step_index": 7,
            "previous_instruction": "Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
            "edited_instruction": "Dựng mặt phẳng (α) đi qua O và vuông góc với AB.",
            "target_ids": ["mp_tt_AB"],
            "absorbed_ids": [],
            "prior_step_ids": ["A", "B", "C", "D", "S", "O", "M"],
            "scene3d": r_mid1.json()["scene3d"],
        },
    )
    assert r_mid2.status_code == 200, r_mid2.text
    digest_after_o = r_mid2.json()["after_scene_digest"]

    # Step 8 invalid counterexample ("đi qua M") -> HTTP 422 rollback preserves O!
    r_bad_m = client.post(
        "/api/simulation/steps/edit",
        headers=hdr,
        json={
            "session_id": sid,
            "problem_key": "chop-mat-cau-ngoai-tiep",
            "step_id": "mp_tt_AB",
            "step_index": 7,
            "previous_instruction": "Dựng mặt phẳng (α) đi qua O và vuông góc với AB.",
            "edited_instruction": "Dựng mặt phẳng (α) đi qua M và vuông góc với AB.",
            "target_ids": ["mp_tt_AB"],
            "absorbed_ids": [],
            "prior_step_ids": ["A", "B", "C", "D", "S", "O", "M"],
            "scene3d": r_mid2.json()["scene3d"],
        },
    )
    assert r_bad_m.status_code == 422
    assert r_bad_m.json()["error_code"] == "DOWNSTREAM_CIRCUMSCRIBED_SPHERE_BROKEN"
    assert r_bad_m.json()["preserved_scene_digest"] == digest_after_o

    # Final step edit (doan_IA -> Nối đoạn thẳng IB)
    r_late = client.post(
        "/api/simulation/steps/edit",
        headers=hdr,
        json={
            "session_id": sid,
            "problem_key": "chop-mat-cau-ngoai-tiep",
            "step_id": "doan_IA",
            "step_index": 16,
            "previous_instruction": "Nối bán kính IA của mặt cầu",
            "edited_instruction": "Nối đoạn thẳng IB.",
            "target_ids": ["doan_IA"],
            "absorbed_ids": [],
            "prior_step_ids": ["A", "B", "C", "D", "S", "O", "M", "mp_tt_AB", "I"],
            "scene3d": r_mid2.json()["scene3d"],
        },
    )
    assert r_late.status_code == 200, r_late.text
    st = client.get(f"/api/simulation/sessions/{sid}/state", headers=hdr).json()
    assert st["revision_count"] == 5
    assert _find_obj(st["committed_scene"], "mp_tt_AB")["depends"] == ["O", "ab"]
    assert st["revisions"][3]["execution_status"] == "ROLLED_BACK"
    assert st["revisions"][4]["execution_status"] == "COMMITTED"


def test_v22_plane_notation_rename_propagates_to_downstream_steps(advanced_samples_by_id: dict[str, dict]) -> None:
    """V2.2 C.9 / #6: Renaming (α) -> (P) at Step 8 must also update downstream step labels/events."""
    base_scene = copy.deepcopy(advanced_samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    res = execute_step_edit(
        scene3d=base_scene,
        step_id="mp_tt_AB",
        step_index=7,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Dựng mặt phẳng (P) đi qua O và vuông góc với AB.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
        prior_step_ids=["A", "B", "C", "D", "S", "O", "M"],
    )
    assert res["status"] == "committed"
    assert res["mode"] == "PARTIAL_TOPOLOGICAL_REBUILD"
    truc = _find_obj(res["scene3d"], "truc_day")
    assert "(P)" in (truc.get("label") or "")
    assert "(P)" in (truc.get("display_label") or "")
    assert "(α)" not in (truc.get("label") or "")
    ev_truc = next(
        ev for ev in res["scene3d"]["events"]
        if ev.get("object") == "truc_day" and ev.get("action") == "CREATE"
    )
    assert "(P)" in (ev_truc.get("learner_text") or "")
    assert "(α)" not in (ev_truc.get("learner_text") or "")


