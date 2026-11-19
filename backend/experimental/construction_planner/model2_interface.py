# -*- coding: utf-8 -*-
"""Read-only Model 2 readiness interface (`model2-action-interface/1`) — Phase I.

Reads a verified `(ConstructionProofGraph, PresentationStepGraph)` and computes:
- Available verified steps, allowed next actions, dependency constraints, and current presentation state.
- A fail-closed zero-trust `validate_model2_action` enforcing all security boundaries (§17)
  without importing, loading, or depending on Needle 3 or any runtime LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import MODEL2_DETERMINISTIC_SELECTOR_VERSION, MODEL2_INTERFACE_SCHEMA
from .construction_graph import (
    ConstructionProofGraph,
    PresentationStep,
    PresentationStepGraph,
    validate_construction_graph,
)
from .construction_objects import _json_safe


@dataclass(frozen=True)
class Model2ActionCandidate:
    action_id: str
    step_id: str
    action_type: str
    target_object_ids: tuple[str, ...]
    prerequisite_steps: tuple[str, ...]
    proof_node_refs: tuple[str, ...]
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "step_id": self.step_id,
            "action_type": self.action_type,
            "target_object_ids": list(self.target_object_ids),
            "prerequisite_steps": list(self.prerequisite_steps),
            "proof_node_refs": list(self.proof_node_refs),
            "description": self.description,
        }


@dataclass(frozen=True)
class Model2Observation:
    """Structured state-action space read by future Model 2 (strictly bounded to verified graph)."""

    schema_version: str
    proof_graph_id: str
    presentation_graph_id: str
    requested_goal: dict[str, Any]
    completed_step_ids: tuple[str, ...]
    available_verified_steps: tuple[str, ...]
    allowed_actions: tuple[Model2ActionCandidate, ...]
    step_dependencies: dict[str, tuple[str, ...]]
    object_references: tuple[str, ...]
    valid_transition_constraints: tuple[str, ...]
    security_boundaries: tuple[str, ...] = (
        "CANNOT_CREATE_SOURCE_PREMISES",
        "CANNOT_ASSERT_UNPROVEN_GEOMETRIC_RELATION",
        "CANNOT_SKIP_DEPENDENCY",
        "CANNOT_INVOKE_OPERATOR_WITH_MISSING_PRECONDITION",
        "CANNOT_MUTATE_EXACT_KERNEL_RESULTS",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "proof_graph_id": self.proof_graph_id,
            "presentation_graph_id": self.presentation_graph_id,
            "requested_goal": _json_safe(self.requested_goal),
            "completed_step_ids": list(self.completed_step_ids),
            "available_verified_steps": list(self.available_verified_steps),
            "allowed_actions": [a.to_dict() for a in self.allowed_actions],
            "step_dependencies": {k: list(v) for k, v in sorted(self.step_dependencies.items())},
            "object_references": list(self.object_references),
            "valid_transition_constraints": list(self.valid_transition_constraints),
            "security_boundaries": list(self.security_boundaries),
        }


@dataclass(frozen=True)
class Model2ActionDecision:
    accepted: bool
    reason_code: str
    detail: str
    selected_step: PresentationStep | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reason_code": self.reason_code,
            "detail": self.detail,
            "selected_step_id": self.selected_step.step_id if self.selected_step else None,
        }


def build_model2_observation(
    *,
    proof_graph: ConstructionProofGraph,
    presentation_graph: PresentationStepGraph,
    completed_step_ids: tuple[str, ...],
    requested_goal: dict[str, Any],
) -> Model2Observation:
    """Compute valid next presentation actions from a verified `(ConstructionProofGraph, PresentationStepGraph)`."""
    report = validate_construction_graph(proof_graph, require_verified_goal_closure=True)
    if not report.valid:
        raise ValueError(f"Cannot build Model 2 observation from unverified proof graph: {report.failure_codes}")

    completed = set(completed_step_ids)
    deps: dict[str, tuple[str, ...]] = {s.step_id: s.prerequisite_steps for s in presentation_graph.steps}
    allowed: list[Model2ActionCandidate] = []
    avail_steps: list[str] = []
    for step in presentation_graph.steps:
        if step.step_id in completed:
            continue
        if all(req in completed for req in step.prerequisite_steps):
            avail_steps.append(step.step_id)
            allowed.append(
                Model2ActionCandidate(
                    action_id=f"reveal::{step.step_id}",
                    step_id=step.step_id,
                    action_type=step.action_type,
                    target_object_ids=step.object_ids,
                    prerequisite_steps=step.prerequisite_steps,
                    proof_node_refs=step.construction_graph_refs,
                    description=step.learner_text,
                )
            )

    return Model2Observation(
        schema_version=MODEL2_INTERFACE_SCHEMA,
        proof_graph_id=proof_graph.graph_id,
        presentation_graph_id=presentation_graph.graph_id,
        requested_goal=dict(requested_goal),
        completed_step_ids=tuple(completed_step_ids),
        available_verified_steps=tuple(avail_steps),
        allowed_actions=tuple(allowed),
        step_dependencies=deps,
        object_references=tuple(sorted(proof_graph.objects.keys())),
        valid_transition_constraints=(
            "selected action_id MUST appear in observation.allowed_actions",
            "all prerequisite_steps MUST exist in completed_step_ids",
            "no mutation of object coordinates, metric tensor, or exact goal answer permitted",
        ),
    )


def validate_model2_action(
    observation: Model2Observation,
    presentation_graph: PresentationStepGraph,
    proposed_payload: dict[str, Any],
) -> Model2ActionDecision:
    """Fail-closed gate rejecting unverified, out-of-dependency, or mutating Model 2 proposals."""
    forbidden_fields = {"override_answer", "add_premise", "invented_objects", "bypass_preconditions", "mutate_coordinates"}
    bad_keys = sorted(forbidden_fields & set(proposed_payload.keys()))
    if bad_keys:
        return Model2ActionDecision(
            False,
            "MODEL2_SECURITY_BOUNDARY_VIOLATION",
            f"Proposed Model 2 action attempts forbidden boundary mutations: {bad_keys}",
        )

    action_id = proposed_payload.get("action_id")
    allowed_map = {a.action_id: a for a in observation.allowed_actions}
    if not isinstance(action_id, str) or action_id not in allowed_map:
        step_id = proposed_payload.get("step_id")
        if isinstance(step_id, str) and step_id in observation.step_dependencies and step_id not in observation.available_verified_steps:
            missing_reqs = [r for r in observation.step_dependencies[step_id] if r not in set(observation.completed_step_ids)]
            if missing_reqs:
                return Model2ActionDecision(
                    False,
                    "MODEL2_DEPENDENCY_VIOLATION",
                    f"Proposed step {step_id!r} cannot run before prerequisites {missing_reqs}.",
                )
        return Model2ActionDecision(
            False,
            "MODEL2_ACTION_NOT_ALLOWED",
            f"Action {action_id!r} is not in observation.allowed_actions.",
        )

    cand = allowed_map[action_id]
    step = next((s for s in presentation_graph.steps if s.step_id == cand.step_id), None)
    return Model2ActionDecision(True, "ACCEPTED", f"Verified step {cand.step_id!r} accepted safely.", selected_step=step)


@dataclass(frozen=True)
class DeterministicPresentationState:
    """Interactive presentation state tracked by the deterministic selector baseline."""

    active_plan_index: int
    completed_step_ids: tuple[str, ...]
    highlighted_object_ids: tuple[str, ...]
    shown_explanations: tuple[str, ...]


class DeterministicModel2BaselineSelector:
    """Zero-AI deterministic baseline policy for Model 2 action selection (§19).

    Future Needle 3 / Model 2 must demonstrably outperform this baseline on a stated metric
    while passing every fail-closed `validate_model2_action` check.
    """

    selector_version: str = MODEL2_DETERMINISTIC_SELECTOR_VERSION

    @staticmethod
    def select_next_action(
        *,
        observation: Model2Observation,
        presentation_graph: PresentationStepGraph,
        interaction_state: DeterministicPresentationState,
        available_plans_count: int = 1,
        request_switch_plan: int | None = None,
        request_replay_step_id: str | None = None,
    ) -> dict[str, Any]:
        """Select a deterministic verified UI/pedagogical action from `observation`."""
        if request_switch_plan is not None and 0 <= request_switch_plan < available_plans_count and request_switch_plan != interaction_state.active_plan_index:
            return {
                "kind": "switch_plan",
                "target_plan_index": request_switch_plan,
                "reason": "Student requested alternative verified plan comparison.",
            }
        if request_replay_step_id and request_replay_step_id in observation.completed_step_ids:
            step = next((s for s in presentation_graph.steps if s.step_id == request_replay_step_id), None)
            return {
                "kind": "replay_step",
                "step_id": request_replay_step_id,
                "highlight_object_ids": list(step.visual_emphasis if step else ()),
                "explanation_text": step.learner_text if step else "",
            }
        if not observation.allowed_actions:
            return {"kind": "complete", "reason": "All verified presentation steps completed."}

        # Deterministic topological-first selection preferring INIT -> CONSTRUCT_AUXILIARY -> ESTABLISH_RELATION -> MEASURE_GOAL
        priority = {"INIT_GIVEN": 0, "CONSTRUCT_DERIVED": 1, "CONSTRUCT_AUXILIARY": 2, "ESTABLISH_RELATION": 3, "MEASURE_GOAL": 4}
        ordered = sorted(
            observation.allowed_actions,
            key=lambda a: (priority.get(a.action_type, 9), a.step_id),
        )
        chosen = ordered[0]
        decision = validate_model2_action(observation, presentation_graph, {"action_id": chosen.action_id, "step_id": chosen.step_id})
        step = decision.selected_step
        return {
            "kind": "reveal_step",
            "action_id": chosen.action_id,
            "step_id": chosen.step_id,
            "action_type": chosen.action_type,
            "highlight_object_ids": list(chosen.target_object_ids),
            "explanation_text": step.learner_text if step else chosen.description,
            "accepted": decision.accepted,
            "reason_code": decision.reason_code,
        }

    @classmethod
    def run_deterministic_walkthrough(
        cls,
        *,
        proof_graph: ConstructionProofGraph,
        presentation_graph: PresentationStepGraph,
        requested_goal: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a full verified walkthrough from pstep_0 to goal without any AI model."""
        completed: list[str] = []
        trace: list[dict[str, Any]] = []
        state = DeterministicPresentationState(active_plan_index=0, completed_step_ids=(), highlighted_object_ids=(), shown_explanations=())
        for _ in range(len(presentation_graph.steps) + 2):
            obs = build_model2_observation(
                proof_graph=proof_graph,
                presentation_graph=presentation_graph,
                completed_step_ids=tuple(completed),
                requested_goal=requested_goal,
            )
            act = cls.select_next_action(observation=obs, presentation_graph=presentation_graph, interaction_state=state)
            trace.append(act)
            if act["kind"] == "complete":
                break
            if act["kind"] == "reveal_step" and act.get("accepted"):
                completed.append(act["step_id"])
                state = DeterministicPresentationState(
                    active_plan_index=state.active_plan_index,
                    completed_step_ids=tuple(completed),
                    highlighted_object_ids=tuple(act["highlight_object_ids"]),
                    shown_explanations=(*state.shown_explanations, act["explanation_text"]),
                )
        return {
            "selector_version": cls.selector_version,
            "completed_all_steps": len(completed) == len(presentation_graph.steps),
            "steps_executed": len(completed),
            "total_steps": len(presentation_graph.steps),
            "trace": trace,
        }
