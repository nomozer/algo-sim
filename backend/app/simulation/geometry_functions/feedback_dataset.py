# -*- coding: utf-8 -*-
"""Verified step-edit feedback storage lifecycle, leakage-free dataset exporter, and local model interface.

Note on model status:
    This repository currently has NO trained local ML weights (`MODEL_STATUS = "MODEL_NOT_TRAINED"`).
    All live runtime parsing and inference run through the deterministic Vietnamese parser baseline
    (`step_editor.parse_vietnamese_construction_step`) while this module collects verified,
    conflict-checked training records and prepares grouped train/val/test JSONL exports for
    future offline fine-tuning / evaluation.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.db import _now
from app.persistence.step_edit_models import (
    STEP_FEEDBACK_SCHEMA_VERSION,
    VerifiedStepFeedbackRecord,
)
from app.simulation.geometry_functions.step_editor import (
    StepEditRefusal,
    parse_vietnamese_construction_step,
)

DATASET_SCHEMA_VERSION = "axo-step-feedback-dataset/1"
MODEL_STATUS = "MODEL_NOT_TRAINED"

FEEDBACK_ACCEPTANCE_STATES: tuple[str, ...] = (
    "PENDING_VERIFICATION",
    "GEOMETRY_VERIFIED",
    "USER_APPROVED",
    "REJECTED",
    "TRAINING_ELIGIBLE",
)
DATASET_ELIGIBILITY_STATES: tuple[str, ...] = (
    "INELIGIBLE",
    "ELIGIBLE",
    "CONFLICT_QUARANTINED",
)


def _norm_clause_key(text: str) -> str:
    s = unicodedata.normalize("NFC", text or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s.rstrip(". ").lower()


def canonical_problem_group_key(
    scene3d: dict[str, Any] | None,
    explicit_key: str | None = None,
) -> str:
    """Compute a stable problem-family group key so paraphrases/revisions never leak across splits."""
    clean_explicit = (explicit_key or "").strip()
    objs = (scene3d or {}).get("objects") or []
    free_sig = [
        {
            "id": str(o.get("id") or ""),
            "type": str(o.get("type") or ""),
            "xyz": o.get("xyz"),
        }
        for o in sorted(
            (o for o in objs if isinstance(o, dict) and o.get("origin") == "free"),
            key=lambda x: str(x.get("id") or ""),
        )
    ]
    if free_sig:
        payload = json.dumps(free_sig, ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        prefix = re.sub(r"[^a-zA-Z0-9_-]+", "-", clean_explicit)[:40].strip("-") or "geom"
        return f"{prefix}:{digest}"
    if clean_explicit:
        return clean_explicit[:96]
    return "geom:unknown"


def _summarize_geometry_context(scene3d: dict[str, Any] | None) -> dict[str, Any]:
    objs = [o for o in ((scene3d or {}).get("objects") or []) if isinstance(o, dict)]
    return {
        "object_count": len(objs),
        "free_ids": [str(o.get("id") or "") for o in objs if o.get("origin") == "free"],
        "types_summary": {
            t: sum(1 for o in objs if o.get("type") == t)
            for t in sorted({str(o.get("type") or "") for o in objs if o.get("type")})
        },
        "metric_kind": ((scene3d or {}).get("metric") or {}).get("kind", "euclidean"),
    }


def _is_verified_validation_and_execution(
    validation_result: dict[str, Any] | None,
    execution_result: dict[str, Any] | None,
) -> bool:
    """Require explicit positive validation, continuity, and exact arithmetic before verification credit."""
    val = validation_result if isinstance(validation_result, dict) else {}
    exe = execution_result if isinstance(execution_result, dict) else {}
    continuity = val.get("continuity") if isinstance(val.get("continuity"), dict) else {}
    return (
        val.get("passed") is True
        and val.get("valid") is True
        and val.get("exact_arithmetic") is True
        and continuity.get("passed") is True
        and exe.get("status") == "committed"
    )


def record_step_feedback_attempt(
    db: Session,
    *,
    revision_id: str,
    owner_scope: str,
    session_id: str,
    problem_group_key: str,
    original_step: str,
    corrected_step: str,
    original_intent: dict[str, Any],
    corrected_intent: dict[str, Any],
    before_scene: dict[str, Any] | None,
    dependency_context: dict[str, Any],
    registry_operations: list[str],
    validation_result: dict[str, Any],
    execution_result: dict[str, Any],
) -> VerifiedStepFeedbackRecord:
    """Persist structured feedback with initial GEOMETRY_VERIFIED or REJECTED status."""
    passed = _is_verified_validation_and_execution(validation_result, execution_result)
    acceptance = "GEOMETRY_VERIFIED" if passed else "REJECTED"
    row = VerifiedStepFeedbackRecord(
        feedback_id=f"fb-{uuid.uuid4().hex[:16]}",
        revision_id=revision_id,
        owner_scope=owner_scope,
        session_id=session_id,
        problem_group_key=problem_group_key[:96],
        original_step=original_step,
        corrected_step=corrected_step,
        original_intent_json=json.dumps(original_intent, ensure_ascii=False, sort_keys=True),
        corrected_intent_json=json.dumps(corrected_intent, ensure_ascii=False, sort_keys=True),
        geometry_context_json=json.dumps(_summarize_geometry_context(before_scene), ensure_ascii=False, sort_keys=True),
        dependency_context_json=json.dumps(dependency_context, ensure_ascii=False, sort_keys=True),
        registry_operations_json=json.dumps(list(registry_operations), ensure_ascii=False),
        validation_result_json=json.dumps(validation_result, ensure_ascii=False, sort_keys=True),
        execution_result_json=json.dumps(execution_result, ensure_ascii=False, sort_keys=True),
        user_acceptance_status=acceptance,
        dataset_eligibility="INELIGIBLE",
        schema_version=STEP_FEEDBACK_SCHEMA_VERSION,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(row)
    db.flush()
    return row


def approve_step_feedback(
    db: Session,
    feedback_id: str,
    *,
    approved: bool,
    reviewer_note: str | None = None,
    owner_scope: str | None = None,
    promote_to_training: bool = True,
) -> dict[str, Any]:
    """Explicit human acceptance / rejection transition for a recorded feedback item.

    Rejected or unverified geometry records can NEVER become USER_APPROVED or TRAINING_ELIGIBLE.
    """
    stmt = select(VerifiedStepFeedbackRecord).where(
        VerifiedStepFeedbackRecord.feedback_id == feedback_id
    )
    if owner_scope is not None:
        stmt = stmt.where(VerifiedStepFeedbackRecord.owner_scope == owner_scope)
    row = db.execute(stmt).scalar_one_or_none()
    if row is None:
        raise KeyError(f"FEEDBACK_NOT_FOUND:{feedback_id}")

    val = json.loads(row.validation_result_json or "{}")
    exe = json.loads(row.execution_result_json or "{}")
    geom_ok = _is_verified_validation_and_execution(val, exe)

    if approved and not geom_ok:
        raise ValueError(
            "CANNOT_APPROVE_FAILED_GEOMETRY: Không thể duyệt bản sửa bước chưa vượt qua kiểm chứng hình học."
        )

    if not approved:
        row.user_acceptance_status = "REJECTED"
        row.dataset_eligibility = "INELIGIBLE"
    elif promote_to_training:
        row.user_acceptance_status = "TRAINING_ELIGIBLE"
        row.dataset_eligibility = "ELIGIBLE"
    else:
        row.user_acceptance_status = "USER_APPROVED"
        row.dataset_eligibility = "INELIGIBLE"

    if reviewer_note is not None:
        row.reviewer_note = reviewer_note.strip() or None
    row.updated_at = _now()
    db.flush()

    return {
        "feedback_id": row.feedback_id,
        "revision_id": row.revision_id,
        "problem_group_key": row.problem_group_key,
        "user_acceptance_status": row.user_acceptance_status,
        "dataset_eligibility": row.dataset_eligibility,
        "reviewer_note": row.reviewer_note,
        "schema_version": row.schema_version,
    }


def _assign_group_split(problem_group_key: str) -> str:
    bucket = int(hashlib.sha256(problem_group_key.encode("utf-8")).hexdigest()[:8], 16) % 10
    if bucket < 7:
        return "train"
    if bucket < 9:
        return "val"
    return "test"


def export_step_feedback_dataset(db: Session) -> dict[str, Any]:
    """Deduplicate, quarantine contradictions, and build deterministic grouped train/val/test splits."""
    rows = db.execute(
        select(VerifiedStepFeedbackRecord).order_by(VerifiedStepFeedbackRecord.id.asc())
    ).scalars().all()

    eligible_rows = [
        r
        for r in rows
        if r.user_acceptance_status == "TRAINING_ELIGIBLE"
        and r.dataset_eligibility == "ELIGIBLE"
    ]

    # Contradiction detection: same (problem_group_key, corrected_step_norm) producing different intent signatures
    signatures_by_text: dict[tuple[str, str], set[str]] = {}
    for r in eligible_rows:
        corr_intent = json.loads(r.corrected_intent_json or "{}")
        sig = str(corr_intent.get("intent_signature") or "")
        key = (r.problem_group_key, _norm_clause_key(r.corrected_step))
        signatures_by_text.setdefault(key, set()).add(sig)

    contradiction_keys = {k for k, sigs in signatures_by_text.items() if len(sigs) > 1}
    quarantined: list[dict[str, Any]] = []
    seen_dedup: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    for r in eligible_rows:
        corr_intent = json.loads(r.corrected_intent_json or "{}")
        sig = str(corr_intent.get("intent_signature") or "")
        text_key = (r.problem_group_key, _norm_clause_key(r.corrected_step))
        if text_key in contradiction_keys:
            r.dataset_eligibility = "CONFLICT_QUARANTINED"
            r.updated_at = _now()
            quarantined.append(
                {
                    "feedback_id": r.feedback_id,
                    "revision_id": r.revision_id,
                    "problem_group_key": r.problem_group_key,
                    "reason": "CONFLICTING_INTENT_FOR_IDENTICAL_CORRECTION",
                }
            )
            continue

        dedup_key = (
            r.problem_group_key,
            _norm_clause_key(r.original_step),
            _norm_clause_key(r.corrected_step),
            sig,
        )
        if dedup_key in seen_dedup:
            seen_dedup[dedup_key]["duplicate_count"] += 1
            seen_dedup[dedup_key]["merged_feedback_ids"].append(r.feedback_id)
            continue

        seen_dedup[dedup_key] = {
            "schema_version": DATASET_SCHEMA_VERSION,
            "feedback_id": r.feedback_id,
            "revision_id": r.revision_id,
            "problem_group_key": r.problem_group_key,
            "original_step": r.original_step,
            "corrected_step": r.corrected_step,
            "original_intent": json.loads(r.original_intent_json or "{}"),
            "corrected_intent": corr_intent,
            "geometry_context": json.loads(r.geometry_context_json or "{}"),
            "dependency_context": json.loads(r.dependency_context_json or "{}"),
            "registry_operations": json.loads(r.registry_operations_json or "[]"),
            "validation_result": json.loads(r.validation_result_json or "{}"),
            "execution_result": json.loads(r.execution_result_json or "{}"),
            "user_acceptance_status": r.user_acceptance_status,
            "dataset_eligibility": r.dataset_eligibility,
            "duplicate_count": 1,
            "merged_feedback_ids": [r.feedback_id],
        }

    db.flush()

    splits: dict[str, list[dict[str, Any]]] = {"train": [], "val": [], "test": []}
    for entry in seen_dedup.values():
        split_name = _assign_group_split(entry["problem_group_key"])
        entry["split"] = split_name
        splits[split_name].append(entry)

    status_counts = {s: 0 for s in FEEDBACK_ACCEPTANCE_STATES}
    for r in rows:
        status_counts[r.user_acceptance_status] = status_counts.get(r.user_acceptance_status, 0) + 1

    return {
        "schema_version": DATASET_SCHEMA_VERSION,
        "model_status": MODEL_STATUS,
        "total_records": len(rows),
        "status_counts": status_counts,
        "eligible_deduplicated_count": len(seen_dedup),
        "quarantined_count": len(quarantined),
        "quarantined": quarantined,
        "split_counts": {k: len(v) for k, v in splits.items()},
        "splits": splits,
    }


def get_feedback_system_status(db: Session, *, owner_scope: str | None = None) -> dict[str, Any]:
    """Summarize stored feedback readiness and explicit local model training status."""
    stmt = select(VerifiedStepFeedbackRecord)
    if owner_scope is not None:
        stmt = stmt.where(VerifiedStepFeedbackRecord.owner_scope == owner_scope)
    rows = db.execute(stmt.order_by(VerifiedStepFeedbackRecord.id.desc())).scalars().all()
    counts = {s: 0 for s in FEEDBACK_ACCEPTANCE_STATES}
    quarantined_count = 0
    for r in rows:
        counts[r.user_acceptance_status] = counts.get(r.user_acceptance_status, 0) + 1
        if r.dataset_eligibility == "CONFLICT_QUARANTINED":
            quarantined_count += 1
    return {
        "schema_version": STEP_FEEDBACK_SCHEMA_VERSION,
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "model_status": MODEL_STATUS,
        "model_trained": False,
        "total_records": len(rows),
        "counts_by_acceptance": counts,
        "training_eligible_count": sum(
            1
            for r in rows
            if r.user_acceptance_status == "TRAINING_ELIGIBLE"
            and r.dataset_eligibility == "ELIGIBLE"
        ),
        "quarantined_count": quarantined_count,
        "recent_feedback": [
            {
                "feedback_id": r.feedback_id,
                "revision_id": r.revision_id,
                "problem_group_key": r.problem_group_key,
                "original_step": r.original_step,
                "corrected_step": r.corrected_step,
                "user_acceptance_status": r.user_acceptance_status,
                "dataset_eligibility": r.dataset_eligibility,
            }
            for r in rows[:10]
        ],
    }


@dataclass(frozen=True)
class StepBenchmarkCase:
    case_id: str
    instruction: str
    expected_ops: tuple[str, ...]
    expected_error_code: str | None = None


FIXED_STEP_PARSER_BENCHMARK: tuple[StepBenchmarkCase, ...] = (
    StepBenchmarkCase("bm-01", "Gọi H là trung điểm của đoạn thẳng AB.", ("midpoint",)),
    StepBenchmarkCase("bm-02", "Xác định trung điểm M của BC.", ("midpoint",)),
    StepBenchmarkCase("bm-03", "Lấy điểm K trên SA sao cho SK = 2KA.", ("divide_segment",)),
    StepBenchmarkCase("bm-04", "Xác định trọng tâm G của tam giác ABC.", ("centroid",)),
    StepBenchmarkCase(
        "bm-05",
        "Dựng mặt phẳng trung trực (α) của cạnh AB.",
        ("perpendicular_bisector_plane",),
    ),
    StepBenchmarkCase(
        "bm-06",
        "Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
        ("midpoint", "plane_perpendicular_to_line"),
    ),
    StepBenchmarkCase(
        "bm-07",
        "Dựng mặt phẳng (α) qua H vuông góc với AB.",
        ("plane_perpendicular_to_line",),
    ),
    StepBenchmarkCase(
        "bm-08",
        "Dựng mặt phẳng (β) đi qua M và song song với (ABCD).",
        ("plane_parallel_to_plane",),
    ),
    StepBenchmarkCase(
        "bm-09",
        "Dựng mặt phẳng (P) đi qua ba điểm M, N, P.",
        ("plane_through_three_points",),
    ),
    StepBenchmarkCase(
        "bm-10",
        "Hạ hình chiếu vuông góc H của S xuống mặt phẳng (ABCD).",
        ("orthogonal_projection_plane",),
    ),
    StepBenchmarkCase(
        "bm-11",
        "Kẻ đường cao SH vuông góc với mặt phẳng (ABCD).",
        ("orthogonal_projection_plane",),
    ),
    StepBenchmarkCase(
        "bm-12",
        "Xác định hình chiếu K của A lên đường thẳng SC.",
        ("orthogonal_projection_line",),
    ),
    StepBenchmarkCase(
        "bm-13",
        "Tìm giao điểm I của đường thẳng SC và mặt phẳng (MNP).",
        ("intersect_line_plane",),
    ),
    StepBenchmarkCase(
        "bm-14",
        "Tìm giao điểm E của đường thẳng MN và đường thẳng CD.",
        ("intersect_line_line",),
    ),
    StepBenchmarkCase(
        "bm-15",
        "Tìm giao tuyến d của mặt phẳng (SBC) và mặt phẳng (MNP).",
        ("intersection_line",),
    ),
    StepBenchmarkCase(
        "bm-16",
        "Nối đoạn thẳng IH.",
        ("construct_segment",),
    ),
    StepBenchmarkCase(
        "bm-17",
        "Dựng đường thẳng Δ qua O và vuông góc với (ABCD).",
        ("construct_line",),
    ),
    StepBenchmarkCase(
        "bm-18",
        "Hoàn thiện đa giác thiết diện MNPQ.",
        ("construct_polygon",),
    ),
    StepBenchmarkCase(
        "bm-19",
        "Gọi H' là trung điểm của A'B'.",
        ("midpoint",),
    ),
    StepBenchmarkCase(
        "bm-20",
        "Xác định tâm mặt cầu ngoại tiếp I của hình chóp S.ABCD.",
        ("circumscribed_sphere",),
    ),
    StepBenchmarkCase(
        "bm-21",
        "Vẽ hình nón tròn xoay có đỉnh S và bán kính đáy R.",
        (),
        expected_error_code="UNSUPPORTED_CURVED_OR_FREEFORM_STEP",
    ),
    StepBenchmarkCase(
        "bm-22",
        "   ",
        (),
        expected_error_code="EMPTY_STEP_INSTRUCTION",
    ),
    StepBenchmarkCase(
        "bm-23",
        "Làm gì đó thật đẹp với hình này.",
        (),
        expected_error_code="UNSUPPORTED_STEP_SYNTAX",
    ),
    StepBenchmarkCase(
        "bm-24",
        "Dựng mặt phẳng (α) qua trung điểm H của AB và vuông góc với AB.",
        ("midpoint", "plane_perpendicular_to_line"),
    ),
)


class LocalStepIntentModel(Protocol):
    """Protocol for any future trained local model adapter replacing/assisting rule baseline."""

    model_status: str

    def predict_intent(self, instruction: str) -> dict[str, Any]:
        ...


class UntrainedLocalStepIntentAdapter:
    """Honest placeholder reporting MODEL_NOT_TRAINED while delegating predictions to the rule baseline."""

    model_status: str = MODEL_STATUS

    def predict_intent(self, instruction: str) -> dict[str, Any]:
        try:
            parsed = parse_vietnamese_construction_step(instruction)
            return {
                "model_status": self.model_status,
                "adapter_mode": "RULE_BASELINE_FALLBACK",
                "ok": True,
                "ops": [c.op for c in parsed.clauses],
                "intent": parsed.to_dict(),
            }
        except StepEditRefusal as exc:
            return {
                "model_status": self.model_status,
                "adapter_mode": "RULE_BASELINE_FALLBACK",
                "ok": False,
                "error_code": exc.error_code,
                "learner_error": exc.learner_error,
            }

    def evaluate_benchmark(self) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        passed = 0
        for case in FIXED_STEP_PARSER_BENCHMARK:
            pred = self.predict_intent(case.instruction)
            if case.expected_error_code is not None:
                ok = (not pred["ok"]) and (pred.get("error_code") == case.expected_error_code)
            else:
                ok = bool(pred["ok"]) and tuple(pred.get("ops") or ()) == case.expected_ops
            if ok:
                passed += 1
            results.append(
                {
                    "case_id": case.case_id,
                    "ok": ok,
                    "expected_ops": list(case.expected_ops),
                    "expected_error_code": case.expected_error_code,
                    "predicted_ops": pred.get("ops", []),
                    "predicted_error_code": pred.get("error_code"),
                }
            )
        total = len(FIXED_STEP_PARSER_BENCHMARK)
        return {
            "model_status": self.model_status,
            "model_trained": False,
            "adapter_mode": "RULE_BASELINE_FALLBACK",
            "case_count": total,
            "passed_count": passed,
            "parser_baseline_accuracy": round(passed / max(total, 1), 4),
            "cases": results,
        }
