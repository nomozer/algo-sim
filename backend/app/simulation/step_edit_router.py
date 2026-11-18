# -*- coding: utf-8 -*-
"""FastAPI endpoints for deterministic local step-editing, session persistence, and feedback curation."""
from __future__ import annotations

from collections import OrderedDict
import hashlib
import json
import os
import re
import threading
import time
import uuid
from typing import Any

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.accounts import service as accounts_service
from app.persistence.db import SessionLocal, _now, sqlite_owns_schema
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
from app.ai.step_edit_route import execute_step_edit
from app.simulation.geometry_functions.step_editor import (
    StepEditRefusal,
    parse_vietnamese_construction_step,
)

router = APIRouter(prefix="/api/simulation", tags=["simulation-step-edit"])

_SESSION_LOCKS_GUARD = threading.Lock()
_SESSION_LOCKS: OrderedDict[tuple[str, str], threading.RLock] = OrderedDict()
_CANCELLED_REQUESTS: OrderedDict[tuple[str, str, str], bool] = OrderedDict()
_LATEST_CLIENT_SEQ: OrderedDict[tuple[str, str], int] = OrderedDict()
_LAST_COMMIT_SNAPSHOT: OrderedDict[tuple[str, str, str], dict[str, Any]] = OrderedDict()
_MAX_SESSION_LOCKS = 2048


def _bounded_od_put(od: OrderedDict[Any, Any], key: Any, value: Any) -> None:
    if key in od:
        od.move_to_end(key)
    od[key] = value
    if len(od) > _MAX_SESSION_LOCKS:
        od.popitem(last=False)


def _strip_internal_dep_keys(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    return {str(k): v for k, v in raw.items() if not str(k).startswith("_")}


def _parse_json_dict(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _build_head_snapshot_dep(prev_dep_json: str) -> str:
    """Keep 1-level head metadata for cascading single-step undo without recursive bloat."""
    parsed = _parse_json_dict(prev_dep_json)
    parsed.pop("_prev_snapshot", None)
    return json.dumps(parsed, ensure_ascii=False, sort_keys=True)


def _assert_single_worker_runtime() -> JSONResponse | None:
    """Fail closed if unsafe multi-worker process env is configured for in-process lock state."""
    for env_key in ("WEB_CONCURRENCY", "UVICORN_WORKERS"):
        raw = (os.environ.get(env_key) or "").strip()
        if raw.isdigit() and int(raw) > 1:
            return JSONResponse(
                status_code=503,
                headers={"Cache-Control": "no-store"},
                content={
                    "status": "configuration_error",
                    "error_code": "UNSUPPORTED_MULTI_WORKER_TOPOLOGY",
                    "failed_stage": "topology_guard",
                    "learner_error": "Chế độ chỉnh sửa bước hiện chỉ hỗ trợ máy chủ đơn worker; cấu hình multi-worker không được hỗ trợ.",
                    "draft_preserved": True,
                    "llm_calls": 0,
                    "quota_charged": False,
                },
            )
    g_args = os.environ.get("GUNICORN_CMD_ARGS") or ""
    m = re.search(r"(?:--workers[=\s]+|-w[=\s]*)(\d+)", g_args)
    if m and int(m.group(1)) > 1:
        return JSONResponse(
            status_code=503,
            headers={"Cache-Control": "no-store"},
            content={
                "status": "configuration_error",
                "error_code": "UNSUPPORTED_MULTI_WORKER_TOPOLOGY",
                "failed_stage": "topology_guard",
                "learner_error": "Chế độ chỉnh sửa bước hiện chỉ hỗ trợ máy chủ đơn worker; cấu hình multi-worker không được hỗ trợ.",
                "draft_preserved": True,
                "llm_calls": 0,
                "quota_charged": False,
            },
        )
    return None


def _get_session_lock(owner_scope: str, session_id: str) -> threading.RLock:
    """Return a bounded per-session RLock to serialize concurrent edits on one session."""
    key = (owner_scope, session_id)
    with _SESSION_LOCKS_GUARD:
        lock = _SESSION_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _SESSION_LOCKS[key] = lock
            if len(_SESSION_LOCKS) > _MAX_SESSION_LOCKS:
                for old_key, old_lock in list(_SESSION_LOCKS.items()):
                    if old_key != key and old_lock.acquire(blocking=False):
                        old_lock.release()
                        _SESSION_LOCKS.pop(old_key, None)
                        break
        else:
            _SESSION_LOCKS.move_to_end(key)
        return lock


def _is_request_cancelled(owner_scope: str, session_id: str, client_request_id: str | None) -> bool:
    if not client_request_id:
        return False
    with _SESSION_LOCKS_GUARD:
        return bool(_CANCELLED_REQUESTS.get((owner_scope, session_id, client_request_id), False))


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
    prior_step_ids: list[str] = Field(default_factory=list)
    scene3d: dict[str, Any]
    client_request_id: str | None = Field(default=None, max_length=80)
    client_seq: int | None = Field(default=None, ge=1)
    expected_committed_version: int | None = Field(default=None, ge=0)


class StepEditCancelRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    client_request_id: str = Field(..., min_length=1, max_length=80)
    only_if_uncommitted: bool = False


class FeedbackApproveRequest(BaseModel):
    approved: bool = True
    promote_to_training: bool = True
    reviewer_note: str | None = Field(default=None, max_length=500)


def _assert_verified_step_edit_result(result: dict[str, Any]) -> None:
    """Enforce explicit positive validation, continuity, and target presence before DB commit."""
    if result.get("status") != "committed":
        raise StepEditRefusal("VALIDATION_INCOMPLETE", "validation", "Trạng thái dựng hình chưa ở trạng thái committed.")
    val = result.get("validation_result")
    dep = result.get("dependency_summary")
    scene = result.get("scene3d")
    primary_id = result.get("primary_target_id")
    if not isinstance(val, dict) or not isinstance(dep, dict) or not isinstance(scene, dict):
        raise StepEditRefusal("VALIDATION_INCOMPLETE", "validation", "Thiếu dữ liệu kiểm chứng hoặc đồ thị phụ thuộc.")
    if (
        val.get("passed") is not True
        or val.get("valid") is not True
        or val.get("exact_arithmetic") is not True
        or not isinstance(val.get("continuity"), dict)
        or val["continuity"].get("passed") is not True
        or not isinstance(val.get("checks_passed"), list)
        or len(val["checks_passed"]) == 0
    ):
        raise StepEditRefusal(
            "VALIDATION_INCOMPLETE",
            "validation",
            "Kết quả dựng hình chưa đủ chứng chỉ kiểm chứng hình học và tính liên tục.",
        )
    if dep.get("cycle_detected") is not False:
        raise StepEditRefusal("DEPENDENCY_CYCLE", "validation", "Phát hiện phụ thuộc vòng trong đồ thị dựng hình.")
    objs = scene.get("objects")
    steps = (scene.get("formation") or {}).get("steps")
    if not isinstance(objs, list) or not objs or not isinstance(steps, list) or not steps:
        raise StepEditRefusal("VALIDATION_INCOMPLETE", "validation", "Cảnh Scene3D hoặc chuỗi bước dựng bị rỗng.")
    obj_ids = {o.get("id") for o in objs if isinstance(o, dict) and o.get("id")}
    if not isinstance(primary_id, str) or primary_id not in obj_ids:
        raise StepEditRefusal("VALIDATION_INCOMPLETE", "validation", "Thiếu đối tượng đích hợp lệ trong Scene3D sau dựng lại.")


def _concurrent_conflict_response() -> JSONResponse:
    return JSONResponse(
        status_code=409,
        headers={"Cache-Control": "no-store"},
        content={
            "status": "conflict",
            "error_code": "CONCURRENT_STEP_EDIT_CONFLICT",
            "failed_stage": "persistence",
            "learner_error": "Phiên đang xử lý một chỉnh sửa bước dựng khác; vui lòng thử lại sau giây lát.",
            "draft_preserved": True,
            "llm_calls": 0,
            "quota_charged": False,
        },
    )


def _stale_revision_conflict_response(committed_version: int) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        headers={"Cache-Control": "no-store"},
        content={
            "status": "conflict",
            "error_code": "STALE_REVISION_CONFLICT",
            "failed_stage": "persistence",
            "learner_error": "Phiên làm việc đã có bản cập nhật mới hơn; vui lòng tải lại trước khi chỉnh sửa.",
            "committed_version": committed_version,
            "draft_preserved": True,
            "llm_calls": 0,
            "quota_charged": False,
        },
    )


def _cancelled_or_superseded_response(error_code: str, learner_error: str) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        headers={"Cache-Control": "no-store"},
        content={
            "status": "rolled_back",
            "error_code": error_code,
            "failed_stage": "cancelled" if error_code == "EDIT_CANCELLED" else "superseded",
            "learner_error": learner_error,
            "draft_preserved": True,
            "llm_calls": 0,
            "quota_charged": False,
        },
    )


def _persistence_unavailable_response() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        headers={"Cache-Control": "no-store"},
        content={
            "status": "persistence_error",
            "error_code": "PERSISTENCE_UNAVAILABLE",
            "failed_stage": "persistence",
            "learner_error": "Không thể lưu phiên chỉnh sửa bước dựng vào cơ sở dữ liệu; trạng thái hợp lệ trước đó vẫn được giữ nguyên.",
            "draft_preserved": True,
            "llm_calls": 0,
            "quota_charged": False,
        },
    )


def _execute_locked_step_edit(
    req: StepEditRequest,
    response: Response,
    db: Session,
    owner_scope: str,
) -> dict[str, Any] | JSONResponse:
    stmt = select(StepEditSessionRecord).where(
        StepEditSessionRecord.owner_scope == owner_scope,
        StepEditSessionRecord.session_id == req.session_id,
    )
    if db.bind is not None and not sqlite_owns_schema(db.bind):
        stmt = stmt.with_for_update()
    session_row = db.execute(stmt).scalar_one_or_none()

    incoming_digest = _scene_sha256(req.scene3d)
    if session_row is None:
        session_row = StepEditSessionRecord(
            owner_scope=owner_scope,
            session_id=req.session_id,
            problem_key=req.problem_key[:160],
            base_scene_sha256=incoming_digest,
            committed_scene_json="",
            step_overrides_json="{}",
            dependency_graph_json="{}",
            revision_count=0,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(session_row)
        db.flush()
    elif (req.problem_key and session_row.problem_key and req.problem_key != session_row.problem_key) or (
        not session_row.committed_scene_json and session_row.base_scene_sha256 != incoming_digest
    ):
        # Reset snapshot cleanly when problem changes or no revision has committed yet under stale base hash;
        # keep revision_count monotonic so step_edit_revisions unique (owner_scope, session_id, version_number) holds.
        session_row.problem_key = (req.problem_key or session_row.problem_key or "")[:160]
        session_row.base_scene_sha256 = incoming_digest
        session_row.committed_scene_json = ""
        session_row.step_overrides_json = "{}"
        session_row.dependency_graph_json = "{}"
        session_row.updated_at = _now()
        db.flush()

    raw_existing_dep = _parse_json_dict(session_row.dependency_graph_json)
    persisted_seq = int(raw_existing_dep.get("_latest_client_seq") or 0)
    current_committed_ver = (
        len(
            db.execute(
                select(StepEditRevisionRecord.id).where(
                    StepEditRevisionRecord.owner_scope == owner_scope,
                    StepEditRevisionRecord.session_id == req.session_id,
                    StepEditRevisionRecord.execution_status == "COMMITTED",
                )
            )
            .scalars()
            .all()
        )
        if session_row.committed_scene_json
        else 0
    )
    if req.expected_committed_version is not None and req.expected_committed_version != current_committed_ver:
        db.rollback()
        return _stale_revision_conflict_response(current_committed_ver)
    if req.client_seq is not None and persisted_seq > 0 and req.client_seq <= persisted_seq:
        db.rollback()
        return _cancelled_or_superseded_response(
            "EDIT_SUPERSEDED",
            "Yêu cầu cũ đã được thay thế bởi lượt chỉnh sửa mới hơn.",
        )

    working_scene = (
        json.loads(session_row.committed_scene_json)
        if session_row.committed_scene_json
        else req.scene3d
    )
    pre_commit_snapshot = {
        "problem_key": session_row.problem_key,
        "base_scene_sha256": session_row.base_scene_sha256,
        "committed_scene_json": session_row.committed_scene_json,
        "step_overrides_json": session_row.step_overrides_json,
        "dependency_graph_json": _build_head_snapshot_dep(session_row.dependency_graph_json),
    }
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
            prior_step_ids=req.prior_step_ids,
        )
        _assert_verified_step_edit_result(result)
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

        if _is_request_cancelled(owner_scope, req.session_id, req.client_request_id):
            db.rollback()
            return _cancelled_or_superseded_response("EDIT_CANCELLED", "Đã hủy lượt chỉnh sửa đang chạy.")

        session_row.revision_count = next_version
        session_row.updated_at = _now()

        rb_timings: dict[str, Any] = {}
        if req.client_request_id:
            rb_timings["_client_request_id"] = req.client_request_id
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
            stage_timings_json=json.dumps(rb_timings, ensure_ascii=False, sort_keys=True),
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
        if req.client_seq is not None:
            seq_key = (owner_scope, req.session_id)
            with _SESSION_LOCKS_GUARD:
                cur = _LATEST_CLIENT_SEQ.get(seq_key, 0)
                if req.client_seq > cur:
                    _bounded_od_put(_LATEST_CLIENT_SEQ, seq_key, req.client_seq)

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

    if _is_request_cancelled(owner_scope, req.session_id, req.client_request_id):
        db.rollback()
        return _cancelled_or_superseded_response("EDIT_CANCELLED", "Đã hủy lượt chỉnh sửa đang chạy.")

    prior_committed_count = len(
        db.execute(
            select(StepEditRevisionRecord.id).where(
                StepEditRevisionRecord.owner_scope == owner_scope,
                StepEditRevisionRecord.session_id == req.session_id,
                StepEditRevisionRecord.execution_status == "COMMITTED",
            )
        )
        .scalars()
        .all()
    )
    committed_ver_num = prior_committed_count + 1

    # Atomic commit of rebuilt Scene3D & append-only revision/feedback logs
    t_persist0 = time.perf_counter()
    clean_dep_summary = _strip_internal_dep_keys(result["dependency_summary"])
    dep_to_persist: dict[str, Any] = dict(clean_dep_summary)
    if req.client_request_id:
        dep_to_persist["_client_request_id"] = req.client_request_id
    if req.client_seq is not None:
        dep_to_persist["_latest_client_seq"] = max(persisted_seq, req.client_seq)
    dep_to_persist["_head_revision_id"] = revision_id
    dep_to_persist["_head_version_number"] = next_version
    dep_to_persist["_head_committed_version"] = committed_ver_num
    dep_to_persist["_prev_snapshot"] = pre_commit_snapshot

    stored_timings = dict(result["stage_timings_ms"])
    if req.client_request_id:
        stored_timings["_client_request_id"] = req.client_request_id

    session_row.committed_scene_json = json.dumps(result["scene3d"], ensure_ascii=False)
    session_row.step_overrides_json = json.dumps(result["step_overrides"], ensure_ascii=False, sort_keys=True)

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
        affected_dependencies_json=json.dumps(clean_dep_summary, ensure_ascii=False, sort_keys=True),
        validation_status="PASSED",
        execution_status="COMMITTED",
        error_code=None,
        learner_error=None,
        stage_timings_json=json.dumps(stored_timings, ensure_ascii=False, sort_keys=True),
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
        dependency_context=clean_dep_summary,
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
    dep_to_persist["_head_feedback_id"] = fb.feedback_id
    dep_to_persist["_head_response_meta"] = {
        "mode": result["mode"],
        "equivalence_info": result.get("equivalence_info"),
        "feedback_status": fb.user_acceptance_status,
        "dataset_eligibility": fb.dataset_eligibility,
        "problem_group_key": problem_group_key,
        "primary_target_id": result["primary_target_id"],
        "normalized_intent": result["normalized_intent"],
        "registry_operations": result["registry_operations"],
        "validation_result": result["validation_result"],
        "before_after_diff": result["before_after_diff"],
        "before_scene_digest": result["before_scene_digest"],
        "after_scene_digest": result["after_scene_digest"],
        "stage_timings_ms": result["stage_timings_ms"],
    }
    session_row.dependency_graph_json = json.dumps(dep_to_persist, ensure_ascii=False, sort_keys=True)
    session_row.revision_count = next_version
    session_row.updated_at = _now()
    db.commit()
    if req.client_seq is not None:
        seq_key = (owner_scope, req.session_id)
        with _SESSION_LOCKS_GUARD:
            cur = _LATEST_CLIENT_SEQ.get(seq_key, 0)
            if req.client_seq > cur:
                _bounded_od_put(_LATEST_CLIENT_SEQ, seq_key, req.client_seq)
    persistence_commit_ms = round((time.perf_counter() - t_persist0) * 1000.0, 3)

    resp_timings = dict(result["stage_timings_ms"])
    resp_timings["persistence_commit_ms"] = persistence_commit_ms

    response.headers["Cache-Control"] = "no-store"
    return {
        "status": "committed",
        "idempotent_replay": False,
        "mode": result["mode"],
        "equivalence_info": result.get("equivalence_info"),
        "session_id": req.session_id,
        "owner_scope": owner_scope,
        "revision_id": revision_id,
        "feedback_id": fb.feedback_id,
        "feedback_status": fb.user_acceptance_status,
        "dataset_eligibility": fb.dataset_eligibility,
        "version_number": next_version,
        "committed_version": committed_ver_num,
        "problem_group_key": problem_group_key,
        "primary_target_id": result["primary_target_id"],
        "scene3d": result["scene3d"],
        "step_overrides": result["step_overrides"],
        "normalized_intent": result["normalized_intent"],
        "registry_operations": result["registry_operations"],
        "dependency_summary": clean_dep_summary,
        "validation_result": result["validation_result"],
        "before_after_diff": result["before_after_diff"],
        "before_scene_digest": result["before_scene_digest"],
        "after_scene_digest": result["after_scene_digest"],
        "stage_timings_ms": resp_timings,
        "llm_calls": 0,
        "quota_charged": False,
    }


def _find_request_revision(
    db: Session,
    owner_scope: str,
    session_id: str,
    client_request_id: str,
) -> StepEditRevisionRecord | None:
    rows = (
        db.execute(
            select(StepEditRevisionRecord)
            .where(
                StepEditRevisionRecord.owner_scope == owner_scope,
                StepEditRevisionRecord.session_id == session_id,
            )
            .order_by(StepEditRevisionRecord.version_number.desc())
        )
        .scalars()
        .all()
    )
    for r in rows:
        if _parse_json_dict(r.stage_timings_json).get("_client_request_id") == client_request_id:
            return r
    return None


def _replay_existing_request(
    db: Session,
    req: StepEditRequest,
    response: Response,
    owner_scope: str,
) -> dict[str, Any] | JSONResponse | None:
    if not req.client_request_id:
        return None
    stmt = select(StepEditSessionRecord).where(
        StepEditSessionRecord.owner_scope == owner_scope,
        StepEditSessionRecord.session_id == req.session_id,
    )
    if db.bind is not None and not sqlite_owns_schema(db.bind):
        stmt = stmt.with_for_update()
    session_row = db.execute(stmt).scalar_one_or_none()
    if session_row is not None and session_row.committed_scene_json:
        raw_dep = _parse_json_dict(session_row.dependency_graph_json)
        if raw_dep.get("_client_request_id") == req.client_request_id:
            meta = raw_dep.get("_head_response_meta") if isinstance(raw_dep.get("_head_response_meta"), dict) else {}
            clean_dep = _strip_internal_dep_keys(raw_dep)
            committed_scene = json.loads(session_row.committed_scene_json)
            overrides = _parse_json_dict(session_row.step_overrides_json)
            committed_ver = raw_dep.get("_head_committed_version")
            if not isinstance(committed_ver, int):
                committed_ver = len(
                    db.execute(
                        select(StepEditRevisionRecord.id).where(
                            StepEditRevisionRecord.owner_scope == owner_scope,
                            StepEditRevisionRecord.session_id == req.session_id,
                            StepEditRevisionRecord.execution_status == "COMMITTED",
                        )
                    )
                    .scalars()
                    .all()
                )
            ver_num = raw_dep.get("_head_version_number")
            if not isinstance(ver_num, int):
                ver_num = session_row.revision_count
            response.headers["Cache-Control"] = "no-store"
            return {
                "status": "committed",
                "idempotent_replay": True,
                "mode": meta.get("mode", "IDEMPOTENT_REPLAY"),
                "equivalence_info": meta.get("equivalence_info"),
                "session_id": req.session_id,
                "owner_scope": owner_scope,
                "revision_id": raw_dep.get("_head_revision_id", ""),
                "feedback_id": raw_dep.get("_head_feedback_id", ""),
                "feedback_status": meta.get("feedback_status", "GEOMETRY_VERIFIED"),
                "dataset_eligibility": meta.get("dataset_eligibility", "ELIGIBLE"),
                "version_number": ver_num,
                "committed_version": committed_ver,
                "problem_group_key": meta.get("problem_group_key", ""),
                "primary_target_id": meta.get("primary_target_id", req.step_id),
                "scene3d": committed_scene,
                "step_overrides": overrides,
                "normalized_intent": meta.get("normalized_intent", {}),
                "registry_operations": meta.get("registry_operations", []),
                "dependency_summary": clean_dep,
                "validation_result": meta.get("validation_result"),
                "before_after_diff": meta.get("before_after_diff"),
                "before_scene_digest": meta.get("before_scene_digest", ""),
                "after_scene_digest": meta.get("after_scene_digest"),
                "stage_timings_ms": meta.get("stage_timings_ms", {"total_ms": 0.0}),
                "llm_calls": 0,
                "quota_charged": False,
            }

    existing_rev = _find_request_revision(db, owner_scope, req.session_id, req.client_request_id)
    if existing_rev is None:
        return None
    if existing_rev.execution_status == "COMMITTED":
        return _cancelled_or_superseded_response(
            "EDIT_SUPERSEDED",
            "Yêu cầu cũ đã được thay thế bởi lượt chỉnh sửa mới hơn.",
        )
    if existing_rev.error_code == "EDIT_CANCELLED":
        return _cancelled_or_superseded_response("EDIT_CANCELLED", "Đã hủy lượt chỉnh sửa đang chạy.")
    return JSONResponse(
        status_code=422,
        headers={"Cache-Control": "no-store"},
        content={
            "status": "rolled_back",
            "idempotent_replay": True,
            "error_code": existing_rev.error_code or "VALIDATION_FAILED",
            "failed_stage": "validation",
            "learner_error": existing_rev.learner_error or "Không thể dựng hình với nội dung bước vừa chỉnh.",
            "revision_id": existing_rev.revision_id,
            "feedback_id": "",
            "version_number": existing_rev.version_number,
            "preserved_scene_digest": existing_rev.before_scene_digest,
            "draft_preserved": True,
            "llm_calls": 0,
            "quota_charged": False,
            "details": {},
        },
    )


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
    mw_err = _assert_single_worker_runtime()
    if mw_err is not None:
        return mw_err
    owner_scope = _resolve_owner_scope(db, algosim_session, x_axo_client_session)
    # Close any implicit read snapshot from cookie lookup before waiting on the per-session lock.
    db.rollback()
    with _get_session_lock(owner_scope, req.session_id):
        if _is_request_cancelled(owner_scope, req.session_id, req.client_request_id):
            return _cancelled_or_superseded_response("EDIT_CANCELLED", "Đã hủy lượt chỉnh sửa đang chạy.")
        try:
            replayed = _replay_existing_request(db, req, response, owner_scope)
            if replayed is not None:
                if req.client_seq is not None and getattr(replayed, "status_code", 200) == 200:
                    with _SESSION_LOCKS_GUARD:
                        cur = _LATEST_CLIENT_SEQ.get((owner_scope, req.session_id), 0)
                        if req.client_seq > cur:
                            _bounded_od_put(_LATEST_CLIENT_SEQ, (owner_scope, req.session_id), req.client_seq)
                return replayed

            if req.client_seq is not None:
                seq_key = (owner_scope, req.session_id)
                with _SESSION_LOCKS_GUARD:
                    latest_seq = _LATEST_CLIENT_SEQ.get(seq_key)
                    if latest_seq is not None and req.client_seq <= latest_seq:
                        return _cancelled_or_superseded_response(
                            "EDIT_SUPERSEDED",
                            "Yêu cầu cũ đã được thay thế bởi lượt chỉnh sửa mới hơn.",
                        )

            return _execute_locked_step_edit(req, response, db, owner_scope)
        except IntegrityError:
            db.rollback()
            return _concurrent_conflict_response()
        except OperationalError as exc:
            db.rollback()
            msg = str(exc).lower()
            if "locked" in msg or "busy" in msg:
                return _concurrent_conflict_response()
            return _persistence_unavailable_response()
        except ProgrammingError:
            db.rollback()
            return _persistence_unavailable_response()


@router.post("/steps/cancel")
def cancel_construction_step_edit(
    req: StepEditCancelRequest,
    response: Response,
    db: Session = Depends(get_db),
    algosim_session: str | None = Cookie(default=None, alias=accounts_service.SESSION_COOKIE),
    x_axo_client_session: str | None = Header(default=None, alias="X-Axo-Client-Session"),
):
    """Cancel an in-flight edit request or roll back ONLY if `client_request_id` is still active head."""
    mw_err = _assert_single_worker_runtime()
    if mw_err is not None:
        return mw_err
    response.headers["Cache-Control"] = "no-store"
    owner_scope = _resolve_owner_scope(db, algosim_session, x_axo_client_session)
    db.rollback()
    canc_key = (owner_scope, req.session_id, req.client_request_id)
    with _SESSION_LOCKS_GUARD:
        _bounded_od_put(_CANCELLED_REQUESTS, canc_key, True)

    rolled_back_commit = False
    already_committed = False
    noop_reason: str | None = None
    cancelled_result = True

    with _get_session_lock(owner_scope, req.session_id):
        session_row = db.execute(
            select(StepEditSessionRecord).where(
                StepEditSessionRecord.owner_scope == owner_scope,
                StepEditSessionRecord.session_id == req.session_id,
            )
        ).scalar_one_or_none()
        raw_dep = _parse_json_dict(session_row.dependency_graph_json if session_row else "{}")
        req_rev = _find_request_revision(db, owner_scope, req.session_id, req.client_request_id)
        latest_committed_rev = db.execute(
            select(StepEditRevisionRecord)
            .where(
                StepEditRevisionRecord.owner_scope == owner_scope,
                StepEditRevisionRecord.session_id == req.session_id,
                StepEditRevisionRecord.execution_status == "COMMITTED",
            )
            .order_by(StepEditRevisionRecord.version_number.desc())
        ).scalars().first()

        is_head_commit = bool(
            session_row is not None
            and session_row.committed_scene_json
            and raw_dep.get("_client_request_id") == req.client_request_id
            and latest_committed_rev is not None
            and latest_committed_rev.revision_id == raw_dep.get("_head_revision_id")
            and latest_committed_rev.version_number == raw_dep.get("_head_version_number")
        )
        was_previously_committed = bool(req_rev is not None and req_rev.execution_status == "COMMITTED")

        if req.only_if_uncommitted:
            if is_head_commit or was_previously_committed:
                already_committed = True
                cancelled_result = False
                noop_reason = "ALREADY_COMMITTED"
        elif is_head_commit:
            snap = raw_dep.get("_prev_snapshot")
            if isinstance(snap, dict):
                session_row.problem_key = snap["problem_key"]
                session_row.base_scene_sha256 = snap["base_scene_sha256"]
                session_row.committed_scene_json = snap["committed_scene_json"]
                session_row.step_overrides_json = snap["step_overrides_json"]
                session_row.dependency_graph_json = snap["dependency_graph_json"]
                session_row.updated_at = _now()
                if latest_committed_rev is not None:
                    latest_committed_rev.validation_status = "FAILED"
                    latest_committed_rev.execution_status = "ROLLED_BACK"
                    latest_committed_rev.error_code = "EDIT_CANCELLED"
                    latest_committed_rev.learner_error = "Đã hủy lượt chỉnh sửa trước khi hoàn tất trên giao diện."
                    latest_committed_rev.after_scene_digest = None
                head_fb_id = raw_dep.get("_head_feedback_id")
                if head_fb_id:
                    fb_row = db.execute(
                        select(VerifiedStepFeedbackRecord).where(
                            VerifiedStepFeedbackRecord.feedback_id == head_fb_id,
                        )
                    ).scalar_one_or_none()
                    if fb_row is not None:
                        fb_row.user_acceptance_status = "REJECTED"
                        fb_row.dataset_eligibility = "INELIGIBLE"
                db.commit()
                rolled_back_commit = True
            else:
                already_committed = True
                cancelled_result = False
                noop_reason = "NO_PREV_SNAPSHOT_FOR_HEAD"
        elif was_previously_committed:
            already_committed = True
            cancelled_result = False
            noop_reason = "SUPERSEDED_BY_NEWER_COMMIT"

        if not cancelled_result:
            with _SESSION_LOCKS_GUARD:
                _CANCELLED_REQUESTS.pop(canc_key, None)

    return {
        "cancelled": cancelled_result,
        "already_committed": already_committed,
        "rolled_back_commit": rolled_back_commit,
        "noop_reason": noop_reason,
        "session_id": req.session_id,
        "client_request_id": req.client_request_id,
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
    mw_err = _assert_single_worker_runtime()
    if mw_err is not None:
        return mw_err
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
            "committed_version": 0,
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

    committed_ver = (
        sum(1 for r in revisions if r.execution_status == "COMMITTED")
        if session_row.committed_scene_json
        else 0
    )
    raw_dep = _parse_json_dict(session_row.dependency_graph_json)
    last_committed_request_id = raw_dep.get("_client_request_id") if session_row.committed_scene_json else None
    clean_dep = _strip_internal_dep_keys(raw_dep)
    return {
        "found": True,
        "session_id": session_id,
        "owner_scope": owner_scope,
        "problem_key": session_row.problem_key,
        "base_scene_sha256": session_row.base_scene_sha256,
        "revision_count": session_row.revision_count,
        "committed_version": committed_ver,
        "last_committed_request_id": last_committed_request_id,
        "committed_scene": json.loads(session_row.committed_scene_json) if session_row.committed_scene_json else None,
        "step_overrides": json.loads(session_row.step_overrides_json or "{}"),
        "dependency_summary": clean_dep,
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
