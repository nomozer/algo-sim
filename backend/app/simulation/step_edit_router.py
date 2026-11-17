# -*- coding: utf-8 -*-
"""FastAPI endpoints for deterministic local step-editing, session persistence, and feedback curation."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts import service as accounts_service
from app.persistence.db import SessionLocal, _now
from app.persistence.step_edit_models import (
    StepEditRevisionRecord,
    StepEditSessionRecord,
    VerifiedStepFeedbackRecord,
    ensure_step_edit_tables,
)
from app.simulation.geometry import GeometryError
from app.simulation.geometry_functions.feedback_dataset import (
    approve_step_feedback,
    canonical_problem_group_key,
    get_feedback_system_status,
    record_step_feedback_attempt,
)
from app.simulation.geometry_functions.step_editor import (
    StepEditRefusal,
    execute_step_edit,
    parse_vietnamese_construction_step,
)

router = APIRouter(prefix="/api/simulation", tags=["simulation-step-edit"])


def get_db():
    db = SessionLocal()
    try:
        ensure_step_edit_tables(db.get_bind())
        yield db
    finally:
        db.close()


def _scene_sha256(scene: dict[str, Any] | None) -> str:
    payload = json.dumps(scene or {}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _scene_objects_digest(scene: dict[str, Any] | None) -> str:
    objs = (scene or {}).get("objects") or []
    payload = json.dumps(objs, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _resolve_owner_scope(
    db: Session,
    session_cookie: str | None,
    x_axo_client_session: str | None,
) -> str:
    if session_cookie:
        auth = accounts_service.load_session(db, session_cookie)
        if auth is not None and auth.user_id is not None:
            return f"user:{auth.user_id}"
    raw_client = (x_axo_client_session or "").strip()
    if raw_client:
        digest = hashlib.sha256(raw_client.encode("utf-8")).hexdigest()[:32]
        return f"client:{digest}"
    return "client:anonymous-default"


class StepEditRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    problem_key: str = Field(default="", max_length=160)
    step_id: str = Field(..., min_length=1, max_length=80)
    step_index: int = Field(..., ge=0)
    previous_instruction: str = ""
    edited_instruction: str
    target_ids: list[str] = Field(default_factory=list)
    absorbed_ids: list[str] = Field(default_factory=list)
    scene3d: dict[str, Any]


class FeedbackApproveRequest(BaseModel):
    approved: bool = True
    promote_to_training: bool = True
    reviewer_note: str | None = Field(default=None, max_length=500)


@router.post("/steps/edit")
def edit_construction_step(
    req: StepEditRequest,
    response: Response,
    db: Session = Depends(get_db),
    algosim_session: str | None = Cookie(default=None, alias=accounts_service.SESSION_COOKIE),
    x_axo_client_session: str | None = Header(default=None, alias="X-Axo-Client-Session"),
):
    """Deterministically parse, validate, partially rebuild, and persist a construction-step edit.

    Zero external LLM calls and zero AI analysis quota charges.
    """
    owner_scope = _resolve_owner_scope(db, algosim_session, x_axo_client_session)

    session_row = db.execute(
        select(StepEditSessionRecord).where(
            StepEditSessionRecord.owner_scope == owner_scope,
            StepEditSessionRecord.session_id == req.session_id,
        )
    ).scalar_one_or_none()

    incoming_digest = _scene_sha256(req.scene3d)
    if session_row is None:
        session_row = StepEditSessionRecord(
            owner_scope=owner_scope,
            session_id=req.session_id,
            problem_key=req.problem_key[:160],
            base_scene_sha256=incoming_digest,
            committed_scene_json=json.dumps(req.scene3d, ensure_ascii=False),
            step_overrides_json="{}",
            dependency_graph_json="{}",
            revision_count=0,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(session_row)
        db.flush()
    elif req.problem_key and session_row.problem_key and req.problem_key != session_row.problem_key:
        # Caller reused session_id on a different problem -> reset committed snapshot cleanly
        session_row.problem_key = req.problem_key[:160]
        session_row.base_scene_sha256 = incoming_digest
        session_row.committed_scene_json = json.dumps(req.scene3d, ensure_ascii=False)
        session_row.step_overrides_json = "{}"
        session_row.dependency_graph_json = "{}"
        session_row.updated_at = _now()
        db.flush()

    working_scene = (
        json.loads(session_row.committed_scene_json)
        if session_row.revision_count > 0 and session_row.committed_scene_json
        else req.scene3d
    )
    existing_overrides: dict[str, str] = json.loads(session_row.step_overrides_json or "{}")
    before_digest = _scene_objects_digest(working_scene)
    next_version = session_row.revision_count + 1
    revision_id = f"rev-{uuid.uuid4().hex[:16]}"
    problem_group_key = canonical_problem_group_key(working_scene, req.problem_key or session_row.problem_key)

    try:
        prev_intent_dict = parse_vietnamese_construction_step(req.previous_instruction).to_dict()
    except StepEditRefusal:
        prev_intent_dict = {"raw_text": req.previous_instruction}

    try:
        result = execute_step_edit(
            scene3d=working_scene,
            step_id=req.step_id,
            step_index=req.step_index,
            previous_instruction=req.previous_instruction,
            edited_instruction=req.edited_instruction,
            target_ids=req.target_ids,
            absorbed_ids=req.absorbed_ids,
            step_overrides=existing_overrides,
        )
    except (StepEditRefusal, GeometryError) as exc:
        if isinstance(exc, StepEditRefusal):
            error_code = exc.error_code
            failed_stage = exc.failed_stage
            learner_error = exc.learner_error
            details = exc.details
        else:
            error_code = getattr(exc, "code", None) or "GEOMETRY_EXECUTION_ERROR"
            failed_stage = "kernel"
            learner_error = str(exc) or "Không thể dựng hình với dữ kiện đã chỉnh."
            details = {}

        session_row.revision_count = next_version
        session_row.updated_at = _now()

        rev = StepEditRevisionRecord(
            revision_id=revision_id,
            owner_scope=owner_scope,
            session_id=req.session_id,
            version_number=next_version,
            step_id=req.step_id[:80],
            step_index=req.step_index,
            previous_instruction=req.previous_instruction,
            edited_instruction=req.edited_instruction,
            normalized_intent_json=json.dumps({"raw_text": req.edited_instruction}, ensure_ascii=False),
            affected_dependencies_json="[]",
            validation_status="FAILED",
            execution_status="ROLLED_BACK",
            error_code=error_code[:64],
            learner_error=learner_error,
            stage_timings_json="{}",
            before_scene_digest=before_digest,
            after_scene_digest=None,
            timestamp=_now(),
        )
        db.add(rev)

        fb = record_step_feedback_attempt(
            db,
            revision_id=revision_id,
            owner_scope=owner_scope,
            session_id=req.session_id,
            problem_group_key=problem_group_key,
            original_step=req.previous_instruction,
            corrected_step=req.edited_instruction,
            original_intent=prev_intent_dict,
            corrected_intent={"raw_text": req.edited_instruction, "error_code": error_code},
            before_scene=working_scene,
            dependency_context={"target_ids": req.target_ids, "absorbed_ids": req.absorbed_ids},
            registry_operations=[],
            validation_result={"passed": False, "error_code": error_code, "failed_stage": failed_stage},
            execution_result={"status": "rolled_back", "error_code": error_code, "learner_error": learner_error},
        )
        db.commit()

        return JSONResponse(
            status_code=422,
            headers={"Cache-Control": "no-store"},
            content={
                "status": "rolled_back",
                "error_code": error_code,
                "failed_stage": failed_stage,
                "learner_error": learner_error,
                "revision_id": revision_id,
                "feedback_id": fb.feedback_id,
                "version_number": next_version,
                "preserved_scene_digest": before_digest,
                "draft_preserved": True,
                "llm_calls": 0,
                "quota_charged": False,
                "details": details,
            },
        )

    # Atomic commit of rebuilt Scene3D & append-only revision/feedback logs
    session_row.committed_scene_json = json.dumps(result["scene3d"], ensure_ascii=False)
    session_row.step_overrides_json = json.dumps(result["step_overrides"], ensure_ascii=False, sort_keys=True)
    session_row.dependency_graph_json = json.dumps(result["dependency_summary"], ensure_ascii=False, sort_keys=True)
    session_row.revision_count = next_version
    session_row.updated_at = _now()

    rev = StepEditRevisionRecord(
        revision_id=revision_id,
        owner_scope=owner_scope,
        session_id=req.session_id,
        version_number=next_version,
        step_id=req.step_id[:80],
        step_index=req.step_index,
        previous_instruction=req.previous_instruction,
        edited_instruction=req.edited_instruction,
        normalized_intent_json=json.dumps(result["normalized_intent"], ensure_ascii=False, sort_keys=True),
        affected_dependencies_json=json.dumps(result["dependency_summary"], ensure_ascii=False, sort_keys=True),
        validation_status="PASSED",
        execution_status="COMMITTED",
        error_code=None,
        learner_error=None,
        stage_timings_json=json.dumps(result["stage_timings_ms"], ensure_ascii=False, sort_keys=True),
        before_scene_digest=result["before_scene_digest"],
        after_scene_digest=result["after_scene_digest"],
        timestamp=_now(),
    )
    db.add(rev)

    fb = record_step_feedback_attempt(
        db,
        revision_id=revision_id,
        owner_scope=owner_scope,
        session_id=req.session_id,
        problem_group_key=problem_group_key,
        original_step=req.previous_instruction,
        corrected_step=req.edited_instruction,
        original_intent=prev_intent_dict,
        corrected_intent=result["normalized_intent"],
        before_scene=working_scene,
        dependency_context=result["dependency_summary"],
        registry_operations=result["registry_operations"],
        validation_result=result["validation_result"],
        execution_result={
            "status": "committed",
            "mode": result["mode"],
            "primary_target_id": result["primary_target_id"],
            "before_after_diff": result["before_after_diff"],
            "before_scene_digest": result["before_scene_digest"],
            "after_scene_digest": result["after_scene_digest"],
        },
    )
    db.commit()

    response.headers["Cache-Control"] = "no-store"
    return {
        "status": "committed",
        "mode": result["mode"],
        "session_id": req.session_id,
        "owner_scope": owner_scope,
        "revision_id": revision_id,
        "feedback_id": fb.feedback_id,
        "feedback_status": fb.user_acceptance_status,
        "dataset_eligibility": fb.dataset_eligibility,
        "version_number": next_version,
        "problem_group_key": problem_group_key,
        "primary_target_id": result["primary_target_id"],
        "scene3d": result["scene3d"],
        "step_overrides": result["step_overrides"],
        "normalized_intent": result["normalized_intent"],
        "registry_operations": result["registry_operations"],
        "dependency_summary": result["dependency_summary"],
        "validation_result": result["validation_result"],
        "before_after_diff": result["before_after_diff"],
        "before_scene_digest": result["before_scene_digest"],
        "after_scene_digest": result["after_scene_digest"],
        "stage_timings_ms": result["stage_timings_ms"],
        "llm_calls": 0,
        "quota_charged": False,
    }


@router.get("/sessions/{session_id}/state")
def get_step_edit_session_state(
    session_id: str,
    response: Response,
    db: Session = Depends(get_db),
    algosim_session: str | None = Cookie(default=None, alias=accounts_service.SESSION_COOKIE),
    x_axo_client_session: str | None = Header(default=None, alias="X-Axo-Client-Session"),
):
    """Restore persisted committed Scene3D, step overrides, and revision history for a session."""
    response.headers["Cache-Control"] = "no-store"
    owner_scope = _resolve_owner_scope(db, algosim_session, x_axo_client_session)

    session_row = db.execute(
        select(StepEditSessionRecord).where(
            StepEditSessionRecord.owner_scope == owner_scope,
            StepEditSessionRecord.session_id == session_id,
        )
    ).scalar_one_or_none()
    if session_row is None:
        return {
            "found": False,
            "session_id": session_id,
            "owner_scope": owner_scope,
            "revision_count": 0,
            "committed_scene": None,
            "step_overrides": {},
            "dependency_summary": {},
            "revisions": [],
            "feedback_items": [],
        }

    revisions = db.execute(
        select(StepEditRevisionRecord)
        .where(
            StepEditRevisionRecord.owner_scope == owner_scope,
            StepEditRevisionRecord.session_id == session_id,
        )
        .order_by(StepEditRevisionRecord.version_number.asc())
    ).scalars().all()

    feedback_items = db.execute(
        select(VerifiedStepFeedbackRecord)
        .where(
            VerifiedStepFeedbackRecord.owner_scope == owner_scope,
            VerifiedStepFeedbackRecord.session_id == session_id,
        )
        .order_by(VerifiedStepFeedbackRecord.id.asc())
    ).scalars().all()

    return {
        "found": True,
        "session_id": session_id,
        "owner_scope": owner_scope,
        "problem_key": session_row.problem_key,
        "base_scene_sha256": session_row.base_scene_sha256,
        "revision_count": session_row.revision_count,
        "committed_scene": json.loads(session_row.committed_scene_json or "{}"),
        "step_overrides": json.loads(session_row.step_overrides_json or "{}"),
        "dependency_summary": json.loads(session_row.dependency_graph_json or "{}"),
        "revisions": [
            {
                "revision_id": r.revision_id,
                "version_number": r.version_number,
                "step_id": r.step_id,
                "step_index": r.step_index,
                "previous_instruction": r.previous_instruction,
                "edited_instruction": r.edited_instruction,
                "validation_status": r.validation_status,
                "execution_status": r.execution_status,
                "error_code": r.error_code,
                "learner_error": r.learner_error,
                "before_scene_digest": r.before_scene_digest,
                "after_scene_digest": r.after_scene_digest,
            }
            for r in revisions
        ],
        "feedback_items": [
            {
                "feedback_id": f.feedback_id,
                "revision_id": f.revision_id,
                "problem_group_key": f.problem_group_key,
                "original_step": f.original_step,
                "corrected_step": f.corrected_step,
                "user_acceptance_status": f.user_acceptance_status,
                "dataset_eligibility": f.dataset_eligibility,
            }
            for f in feedback_items
        ],
    }


@router.post("/feedback/{feedback_id}/approve")
def approve_feedback_endpoint(
    feedback_id: str,
    req: FeedbackApproveRequest,
    response: Response,
    db: Session = Depends(get_db),
    algosim_session: str | None = Cookie(default=None, alias=accounts_service.SESSION_COOKIE),
    x_axo_client_session: str | None = Header(default=None, alias="X-Axo-Client-Session"),
):
    """Record explicit human approval/rejection for a verified step edit."""
    response.headers["Cache-Control"] = "no-store"
    owner_scope = _resolve_owner_scope(db, algosim_session, x_axo_client_session)
    try:
        res = approve_step_feedback(
            db,
            feedback_id,
            approved=req.approved,
            reviewer_note=req.reviewer_note,
            owner_scope=owner_scope,
            promote_to_training=req.promote_to_training,
        )
        db.commit()
        return res
    except KeyError:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi phản hồi bước dựng.")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/feedback/status")
def feedback_status_endpoint(
    response: Response,
    db: Session = Depends(get_db),
    algosim_session: str | None = Cookie(default=None, alias=accounts_service.SESSION_COOKIE),
    x_axo_client_session: str | None = Header(default=None, alias="X-Axo-Client-Session"),
):
    """Report feedback readiness and honest local model status (MODEL_NOT_TRAINED)."""
    response.headers["Cache-Control"] = "no-store"
    owner_scope = _resolve_owner_scope(db, algosim_session, x_axo_client_session)
    return get_feedback_system_status(db, owner_scope=owner_scope)
