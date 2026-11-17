# -*- coding: utf-8 -*-
"""SQLAlchemy persistence models for editable construction steps, revisions, and verified feedback.

Separated from `db.py` and `classroom_models.py` so workspace step-editing state
and verified feedback records evolve cleanly on shared `Base` metadata without
touching core problem cache or account/session tables.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base, _now, engine, sqlite_owns_schema

STEP_FEEDBACK_SCHEMA_VERSION = "axo-step-feedback/1"


class StepEditSessionRecord(Base):
    """Per-owner, per-session committed step-edit state for deterministic reload recovery."""

    __tablename__ = "step_edit_sessions"
    __table_args__ = (
        UniqueConstraint(
            "owner_scope",
            "session_id",
            name="uq_step_edit_session_owner_sid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_scope: Mapped[str] = mapped_column(String(96), index=True)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    problem_key: Mapped[str] = mapped_column(String(160), default="")
    base_scene_sha256: Mapped[str] = mapped_column(String(64), default="")
    committed_scene_json: Mapped[str] = mapped_column(Text, default="{}")
    step_overrides_json: Mapped[str] = mapped_column(Text, default="{}")
    dependency_graph_json: Mapped[str] = mapped_column(Text, default="{}")
    revision_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class StepEditRevisionRecord(Base):
    """Append-only versioned history of every step edit attempt (committed or rolled back)."""

    __tablename__ = "step_edit_revisions"
    __table_args__ = (
        UniqueConstraint(
            "owner_scope",
            "session_id",
            "version_number",
            name="uq_step_edit_revision_version",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    revision_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    owner_scope: Mapped[str] = mapped_column(String(96), index=True)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    step_id: Mapped[str] = mapped_column(String(80))
    step_index: Mapped[int] = mapped_column(Integer)
    previous_instruction: Mapped[str] = mapped_column(Text)
    edited_instruction: Mapped[str] = mapped_column(Text)
    normalized_intent_json: Mapped[str] = mapped_column(Text, default="{}")
    affected_dependencies_json: Mapped[str] = mapped_column(Text, default="[]")
    validation_status: Mapped[str] = mapped_column(String(32))
    execution_status: Mapped[str] = mapped_column(String(32))
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    learner_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    stage_timings_json: Mapped[str] = mapped_column(Text, default="{}")
    before_scene_digest: Mapped[str] = mapped_column(String(64), default="")
    after_scene_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_now)


class VerifiedStepFeedbackRecord(Base):
    """Structured learner step-correction record with explicit verification & dataset eligibility."""

    __tablename__ = "step_edit_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feedback_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    revision_id: Mapped[str] = mapped_column(String(64), index=True)
    owner_scope: Mapped[str] = mapped_column(String(96), index=True)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    problem_group_key: Mapped[str] = mapped_column(String(96), index=True)
    original_step: Mapped[str] = mapped_column(Text)
    corrected_step: Mapped[str] = mapped_column(Text)
    original_intent_json: Mapped[str] = mapped_column(Text, default="{}")
    corrected_intent_json: Mapped[str] = mapped_column(Text, default="{}")
    geometry_context_json: Mapped[str] = mapped_column(Text, default="{}")
    dependency_context_json: Mapped[str] = mapped_column(Text, default="{}")
    registry_operations_json: Mapped[str] = mapped_column(Text, default="[]")
    validation_result_json: Mapped[str] = mapped_column(Text, default="{}")
    execution_result_json: Mapped[str] = mapped_column(Text, default="{}")
    user_acceptance_status: Mapped[str] = mapped_column(
        String(32),
        default="PENDING_VERIFICATION",
        index=True,
    )
    dataset_eligibility: Mapped[str] = mapped_column(
        String(32),
        default="INELIGIBLE",
        index=True,
    )
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    schema_version: Mapped[str] = mapped_column(
        String(32),
        default=STEP_FEEDBACK_SCHEMA_VERSION,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


STEP_EDIT_TABLES = (
    StepEditSessionRecord.__table__,
    StepEditRevisionRecord.__table__,
    VerifiedStepFeedbackRecord.__table__,
)


def ensure_step_edit_tables(target_engine=None) -> None:
    """Create step-editing tables idempotently on SQLite engines."""
    eng = engine if target_engine is None else target_engine
    if sqlite_owns_schema(eng):
        Base.metadata.create_all(bind=eng, tables=list(STEP_EDIT_TABLES))
