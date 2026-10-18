"""Offline-only Route D boundary. Imported only by explicitly declared preview/diagnostic gates."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
import logging
import re
from typing import Any, Literal
import unicodedata

from pydantic import BaseModel

from app.ai.fact_extraction import run_ai_fact_route, surface_fingerprint
from app.learner_messages import learner_reason
from app.simulation.geometry.exact import GeometryError
from app.simulation.geometry.metric import Metric, using
from app.simulation.semantic_program.pipeline_adapter import (
    compile_semantic_program_to_envelope, validate_semantic_envelope_config,
)

_log = logging.getLogger(__name__)

ADAPTER_VERSION = "hybrid-preview-adapter/1"
ENVELOPE_VERSION = "hybrid-route-d-preview/1"


class HybridPreviewEnvelope(BaseModel):
    schema_version: Literal["hybrid-route-d-preview/1"] = ENVELOPE_VERSION
    envelope: dict[str, Any]
    route_d: dict[str, Any]


def preview_identity(contract: str = "flat") -> dict[str, str]:
    # Read owning modules at call time, so a new snapshot sees version changes.
    from app.simulation.geometry_functions import engine, planner, registry

    return {"registry_version": registry.REGISTRY_VERSION, "planner_version": planner.PLANNER_VERSION,
            "engine_version": engine.ENGINE_VERSION, "response_contract": contract,
            "extraction_surface": surface_fingerprint(contract), "adapter_version": ADAPTER_VERSION,
            "envelope_version": ENVELOPE_VERSION, "provider_mode": "OFFLINE_FIXTURE_ONLY"}


def preview_runtime_identity(policy) -> dict[str, Any]:
    surface = dict(policy.preview_surface) if policy.hybrid_preview_enabled else preview_identity(policy.response_contract)
    return {**surface, "enabled": policy.hybrid_preview_enabled, "fingerprint": policy.fingerprint(),
            "default_product_mode": "LLM_ONLY", "product_enablement": "NO-GO"}


class PreviewInvalid(ValueError):
    pass


#: Route D source-grounding refusal codes (registry gate) — the learner is told the data could not be matched to the text.
_MA_NGUON = {"QUOTE_NOT_IN_SOURCE", "UNKNOWN_LABEL", "PREDICATE_NOT_IN_QUOTE", "PLANE_NOT_IN_QUOTE", "ROLE_NOT_IN_QUOTE",
             "OBJECT_NOT_IN_QUOTE", "AMBIGUOUS_VALUE_QUOTE", "UNGROUNDED_VALUE", "SOURCE_OBJECT_MISMATCH",
             "SOURCE_PREMISE_UNREAD", "REQUEST_NOT_ANSWERED", "NOT_ASKED_IN_SOURCE"}


def _refusal(code: str, policy, planner: dict | None = None) -> HybridPreviewEnvelope:
    if code in {"PROOF_UNVERIFIABLE", "PREVIEW_PROOF_STATUS_INVALID"}:
        message = "Chưa có chứng chỉ chứng minh tổng quát; kiểm tra trên một hình dựng chưa đủ để kết luận."
    elif code in _MA_NGUON:
        message = "Hệ chưa đối chiếu được đầy đủ dữ kiện với đề bài nên tạm dừng dựng hình."
    elif code == "NON_POSITIVE_LENGTH":
        message = learner_reason({"status": "unsupported", "reason_code": code,
                                  "failure_category": "capability_gap", "refusal_cause": "SOURCE"})
    else:
        message = "Hệ chưa đủ dữ kiện hoặc khả năng kiểm chứng để dựng hình và tính kết quả an toàn cho đề này."
    # Only verified observations survive a refusal: calls / trace / auxiliary carry model-supplied quotes that never
    # passed the source check (review of this run).
    kept = {k: deepcopy(v) for k, v in (planner or {}).items() if k in ("version", "goal_checks", "negated_checks")}
    return HybridPreviewEnvelope(envelope={"status": "unsupported", "reason_code": code, "reason": message,
                                           "learner_reason": message, "failure_category": "capability_gap"},
                                 route_d={"runtime_identity": preview_runtime_identity(policy), "planner": kept})


#: Backstop against narrative that presents a one-configuration observation as a proof. Text is NFC-normalised and
#: stripped of format characters (zero-width etc.) first; hyphens/spaces between the two syllables are equivalent.
_CHUNG_MINH = r"chứng[\s\-‐-―]*minh"
_LOI_CHUNG_MINH = re.compile(
    rf"(?:đã|được)\s*{_CHUNG_MINH}|{_CHUNG_MINH}\s*(?:thành\s*công|được|xong)|điều\s*phải\s*{_CHUNG_MINH}|đpcm")


def _noi_chung_minh(text: Any) -> bool:
    s = "".join(ch for ch in unicodedata.normalize("NFC", str(text)) if unicodedata.category(ch) != "Cf")
    return _LOI_CHUNG_MINH.search(s.casefold()) is not None


def _validate_scene(scene: dict) -> Metric:
    try:
        matrix = scene["chart_metric"]
        if len(matrix) != 3 or any(len(row) != 3 for row in matrix):
            raise ValueError("shape")
        metric = Metric(tuple(tuple(Fraction(v) for v in row) for row in matrix))
    except (KeyError, TypeError, ValueError, ArithmeticError, GeometryError):
        raise PreviewInvalid("METRIC_NOT_EUCLIDEAN") from None
    objects = {o["id"]: o for o in scene["objects"]}
    if not objects or len(objects) != len(scene["objects"]):
        raise PreviewInvalid("PREVIEW_DEPENDENCY_INVALID")
    born = {}
    steps = scene["formation"]["steps"]
    if not steps or not scene["events"]:
        raise PreviewInvalid("PREVIEW_DEPENDENCY_INVALID")
    for event in scene["events"]:
        index = event["step_index"]
        if type(index) is not int or not 0 <= index < len(steps):
            raise PreviewInvalid("PREVIEW_DEPENDENCY_INVALID")
        if event.get("object"):
            # Quantity/construction events may have no rendered object (existing Scene3D contract).
            born.setdefault(event["object"], index)
    for oid, obj in objects.items():
        for dep in obj.get("depends") or ():
            if dep not in objects or dep in born and (oid not in born or born[dep] >= born[oid]):
                raise PreviewInvalid("PREVIEW_DEPENDENCY_INVALID")
    return metric


def adapt_result(result, policy) -> HybridPreviewEnvelope:
    """Retain the complete deterministic result in an explicit preview representation."""
    planner = deepcopy(result.planner or {})
    # The response reports the snapshot identity; it is only true if the code that ran still has that identity
    # (a Registry/Planner/Engine/extraction change mid-request, e.g. a hot reload, would otherwise be mislabelled).
    # A refusal before planning carries no planner version; one that did plan must name the snapshot's.
    snapshot = dict(policy.preview_surface)
    ran_planner = planner.get("version", snapshot.get("planner_version"))
    if preview_identity(policy.response_contract) != snapshot or ran_planner != snapshot.get("planner_version"):
        raise PreviewInvalid("PREVIEW_IDENTITY_CHANGED")
    for group in ("goal_checks", "negated_checks"):
        for observation in planner.get(group, {}).values():
            if observation.get("proof_status") != "UNVERIFIABLE" or observation.get("can_present_as_proven") is not False:
                raise PreviewInvalid("PREVIEW_PROOF_STATUS_INVALID")
    if result.status != "SERVED":
        return _refusal(result.code or "PREVIEW_RESULT_INVALID", policy, planner)
    if "version" not in planner:   # every served Route D result planned; one without a planner version is unattributable
        raise PreviewInvalid("PREVIEW_IDENTITY_CHANGED")
    if result.kernel_check is not True or result.spec is None or not result.scene3d:
        raise PreviewInvalid("PREVIEW_RESULT_INVALID")
    scene = deepcopy(result.scene3d)
    metric = _validate_scene(scene)
    if metric != result.chart_metric or metric.as_json() != result.metric:
        raise PreviewInvalid("PREVIEW_METRIC_MISMATCH")
    if result.ai.get("surface") != dict(policy.preview_surface).get("extraction_surface"):
        raise PreviewInvalid("PREVIEW_SURFACE_CHANGED")
    unit = scene.get("length_unit")
    if result.length_unit and (not unit or unit.get("symbol") != result.length_unit or unit.get("is_given") is not False):
        raise PreviewInvalid("PREVIEW_LENGTH_UNIT_INVALID")
    if not result.length_unit and unit:
        raise PreviewInvalid("PREVIEW_LENGTH_UNIT_INVALID")
    if any(answer.get("unit") != (result.length_unit if answer.get("dim") else None)
           for answer in result.answer_exact.values()):
        raise PreviewInvalid("PREVIEW_LENGTH_UNIT_INVALID")
    with using(metric):
        envelope = compile_semantic_program_to_envelope(result.spec)
    if validate_semantic_envelope_config(envelope["config"]) or envelope["config"]["execution_truncated"]:
        raise PreviewInvalid("PREVIEW_ENVELOPE_INVALID")
    envelope.update(domain="geometry", source="hybrid_route_d_preview", scene3d=scene)
    # No narrative generated from a one-configuration observation is a proof.
    envelope["description"] = "Quan sát mô hình dựng từ dữ kiện; các kiểm tra trên hình không phải chứng minh tổng quát."
    texts = [envelope["title"], envelope["description"]]
    texts += [frame.get("narration", "") for frame in envelope["config"]["frames"]]
    texts += [event.get(key, "") for event in scene["events"] for key in ("learner_text", "explanation")]
    texts += [step.get("learner_text", "") for step in scene["formation"]["steps"]]
    if any(_noi_chung_minh(t) for t in texts):
        raise PreviewInvalid("PREVIEW_PROOF_TEXT_INVALID")
    return HybridPreviewEnvelope(envelope=envelope, route_d={
        "runtime_identity": preview_runtime_identity(policy), "geometry_ir": result.spec.model_dump(mode="json"),
        "answers": deepcopy(result.answers), "answer_exact": deepcopy(result.answer_exact),
        "source_provenance": deepcopy(result.calls), "construction_trace": deepcopy(result.trace),
        "planner": planner, "length_unit": deepcopy(unit), "kernel_check": result.kernel_check,
    })


def run_preview(problem_text: str, fixtures: Any, policy) -> HybridPreviewEnvelope | None:
    """Finite JSON fixture data only: neither client data nor an API key can install a network transport."""
    if not policy.hybrid_preview_enabled:
        raise PreviewInvalid("PREVIEW_DISABLED")
    if type(fixtures) is not dict or problem_text not in fixtures or type(fixtures[problem_text]) is not dict:
        return None
    try:
        body = json.loads(json.dumps(fixtures[problem_text], allow_nan=False))
    except (TypeError, ValueError):
        return None
    try:
        result = run_ai_fact_route(problem_text, lambda payload: deepcopy(body), contract=policy.response_contract)
        return adapt_result(result, policy)
    except PreviewInvalid as exc:
        return _refusal(str(exc), policy)
    except Exception as exc:  # noqa: BLE001
        # The boundary refuses malformed/tampered deterministic output, with no raw error/model text in HTTP; the
        # exception TYPE is logged server-side so an operator can tell an adapter bug from a tampered result.
        _log.warning("Route D preview validation failed: %s", type(exc).__name__)
        return _refusal("PREVIEW_VALIDATION_FAILED", policy)
