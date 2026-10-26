"""Offline-only Route D boundary. Imported only by explicitly declared preview/diagnostic gates."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
import logging
import re
from typing import Any, Literal, NamedTuple
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

#: /2 (run `hybrid-preview-contract-hardening`): refusals carry `refusal_cause` and a classified `failure_category`.
ADAPTER_VERSION = "hybrid-preview-adapter/2"
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


class RefusalClass(NamedTuple):
    group: str
    failure_category: str
    refusal_cause: str
    message: str


#: Refusal groups (run `hybrid-preview-contract-hardening`): WHAT failed, in the vocabularies the product already emits and
#: the frontend already labels — `failure_category` of `error_codes.SEMANTIC_FAILURE_CATEGORY` / `pipeline` and
#: `refusal_cause` of `semantic_program/refusal_cause.py`. The group name is server-side only; `reason_code` stays exact.
#: `capability_gap` answers "can the machine execute this? — no"; it is never the verdict for a fault in the system's own
#: output, an unverified source or a missing certificate (`error_codes.py`).
_NHOM: tuple[tuple[str, str, frozenset[str], str], ...] = (
    ("CAPABILITY", "capability_gap", frozenset({
        "UNSUPPORTED_CAPABILITY", "UNSUPPORTED_BASE_SHAPE", "UNSUPPORTED_CENTROID", "UNSUPPORTED_MULTIPLE_BASES",
        "UNSUPPORTED_MULTIPLE_HEIGHTS", "UNSUPPORTED_PLANE", "UNSUPPORTED_REGULAR_POLYGON", "QUESTION_CONTEXT_UNSUPPORTED",
        "UNSUPPORTED_IRRATIONAL_LAYOUT", "UNSUPPORTED_VOLUME_RATIO", "IR_MEMORY_BUDGET_EXCEEDED",
        "BRIDGE_UNSUPPORTED_LENGTH_UNIT", "BRIDGE_CUT_EDGES_NOT_STATED", "BRIDGE_UNSUPPORTED_CURVED",
        "BRIDGE_UNSUPPORTED_DERIVED_SOLID", "BRIDGE_UNSUPPORTED_MEASUREMENT", "BRIDGE_UNSUPPORTED_PLANE_KIND",
        "BRIDGE_UNSUPPORTED_PREMISE", "BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY", "BRIDGE_UNSUPPORTED_RELATION",
        "PLAN_TOO_LARGE", "NO_SOLID", "NON_HOMOGENEOUS_LENGTHS", "CONDITIONAL_CLAUSE", "NEGATED_CLAUSE",
        "METRIC_REQUIRES_EUCLIDEAN_CHART",
        # Route D's OUT_OF_SCOPE is the extraction escape `unsupported` ("this clause does not map to the function
        # library"), not the subject verdict of the scope gate: the preview runs no domain detection. `out_of_scope` would
        # tell the learner a geometry problem "belongs to another subject" (`learner_messages`: never).
        "OUT_OF_SCOPE"}),
     "Đề này cần một phép dựng hoặc một dạng câu hỏi mà hệ chưa hỗ trợ, nên hệ không dựng một hình gần đúng."),
    ("MISSING_DATA", "insufficient_specification", frozenset({
        "MISSING_DIMENSION", "UNDERDETERMINED_POINT", "PLANE_NOT_UNIQUE", "FOOT_NOT_DETERMINED", "AMBIGUOUS_FACT",
        "AMBIGUOUS_REFERENCE", "SECTION_NOT_CLOSED_ON_LATERAL_EDGES"}),
     "Dữ kiện hiện có chưa xác định được duy nhất hình cần dựng hoặc còn hiểu theo nhiều cách. AlgoSim không tự chọn số "
     "liệu hay cách hiểu thay em, nên không dựng hình."),
    ("INVALID_DATA", "geometry_generation_failed", frozenset({
        "INCONSISTENT_FACTS", "NON_POSITIVE_LENGTH", "INVALID_RATIO", "DEGENERATE_LINE", "PARALLEL_PLANES", "SKEW_NO_INTERSECTION",
        "SKEW_CLAIM_CONTRADICTED",
        "NON_COPLANAR_POINTS", "SECTION_EMPTY", "SECTION_PLANE_IS_FACE", "DERIVED_PLANE_IS_REFERENCE",
        "REGULAR_PYRAMID_NEEDS_REGULAR_BASE", "QUESTION_LOCAL_GIVEN_CONFLICT", "FOOT_NOT_IN_PLANE", "LINE_CONTAINED_IN_PLANE",
        "DEGENERATE_SOLID", "NON_POSITIVE_RESIDUAL_VOLUME", "OVERLAPPING_SUBTRACTED_SOLIDS", "RESIDUAL_CONTAINMENT_UNPROVED",
        # polyhedral kernel (`GeometryError` codes Route D passes through unchanged)
        "DEGENERATE_POINTS", "COLLINEAR_POINTS", "PARALLEL_NO_INTERSECTION", "CONTAINED_INFINITE_INTERSECTION",
        "ZERO_VECTOR", "PLANE_EQUATION_DEGENERATE", "POLYGON_CHAIN_NOT_CONVEX", "MEASURE_UNDEFINED", "METRIC_NOT_EUCLIDEAN",
        "PLANE_DOES_NOT_CUT", "PLANE_TOUCHES_VERTEX", "PLANE_TOUCHES_EDGE", "SECTION_INTERSECTION_DEGENERATE",
        # stated cut edges of a derived plane (`DINH_CAT_CANH`) that the built figure contradicts
        "SECTION_VERTEX_OFF_EDGE", "LINE_PARALLEL_TO_PLANE", "DEGENERATE_DERIVED_SECTION", "SECTION_BOUNDARY_INCOMPLETE"}),
     "Các dữ kiện dùng để dựng hình mâu thuẫn nhau hoặc làm hình suy biến, nên không có hình nào thoả tất cả. AlgoSim "
     "dừng lại thay vì dựng một hình sai."),
    ("SOURCE_UNVERIFIED", "verification_gap", frozenset({
        "QUOTE_NOT_IN_SOURCE", "UNKNOWN_LABEL", "PREDICATE_NOT_IN_QUOTE", "PLANE_NOT_IN_QUOTE", "ROLE_NOT_IN_QUOTE",
        "OBJECT_NOT_IN_QUOTE", "AMBIGUOUS_VALUE_QUOTE", "UNGROUNDED_VALUE", "SOURCE_OBJECT_MISMATCH",
        "SOURCE_PREMISE_UNREAD", "REQUEST_NOT_ANSWERED", "NOT_ASKED_IN_SOURCE", "QUESTION_LOCAL_GIVEN_UNVERIFIED",
        "GOAL_CLAUSE_NOT_PREMISE", "QUESTION_CLAUSE_NOT_PREMISE", "RESULT_BINDING_UNVERIFIED",
        "REPLAY_SOURCE_IDENTITY_MISMATCH"}),
     "Hệ chưa đối chiếu được đầy đủ dữ kiện với đề bài nên tạm dừng dựng hình."),
    ("RESULT_UNVERIFIED", "verification_gap", frozenset({
        "ENGINE_SELF_CHECK_FAILED", "ENGINE_IR_INVALID", "SCENE_BUILD_FAILED", "PREVIEW_RESULT_INVALID",
        "PREVIEW_METRIC_MISMATCH", "PREVIEW_DEPENDENCY_INVALID", "PREVIEW_ENVELOPE_INVALID", "PREVIEW_LENGTH_UNIT_INVALID",
        "PREVIEW_PROOF_TEXT_INVALID", "PREVIEW_VALIDATION_FAILED", "EXTRACTOR_INTERNAL_ERROR",
        "HYBRID_DEADLINE_EXCEEDED", "HYBRID_CANCELLED",
        # interpreter / kernel failures while building the figure: not an identity fault, not provably the data
        "ENGINE_EXECUTION_FAILED", "ROUTE_INTERNAL_ERROR", "MALFORMED_SOLID", "SECTION_CONSTRUCTION_INTERNAL_FAILURE", "POLYHEDRON_BOUNDARY_OPEN",
        "POLYHEDRON_NON_ORIENTABLE", "POLYHEDRON_DEGENERATE", "POLYHEDRON_FACE_NOT_PLANAR", "POLYHEDRON_FACE_NOT_SIMPLE"}),
     "Hệ đã thử dựng nhưng kết quả chưa qua được khâu kiểm chứng, nên không hiển thị hình chưa được kiểm."),
    ("INCONCLUSIVE", "verification_gap", frozenset({"PROOF_UNVERIFIABLE", "FIGURE_NOT_UNIQUE"}),
     "Hệ chưa có chứng chỉ để kết luận từ dữ kiện: kiểm tra trên một hình dựng chưa đủ để kết luận cho mọi hình thoả đề, "
     "nên hệ không đưa ra kết luận."),
    ("EXTRACTION_FAILED", "geometry_generation_failed", frozenset({
        "LIVE_AI_DISABLED", "PROVIDER_ERROR", "PROVIDER_BLOCKED", "PROVIDER_REFUSED", "PROVIDER_RESPONSE_INVALID",
        "RESPONSE_TRUNCATED", "MAX_TOKENS", "NO_CANDIDATE", "JSON_INVALID", "MALFORMED_RESPONSE_PART",
        "RESPONSE_CONTRACT_INVALID", "SCHEMA_INVALID", "FACT_INCOMPLETE", "DANGLING_DEPENDENCY", "DUPLICATE_CALL_ID",
        "DEPENDENCY_CYCLE", "UNKNOWN_DERIVED_REFERENCE", "DERIVED_REFERENCE_TYPE_MISMATCH", "AUXILIARY_LABEL_COLLISION",
        "AUXILIARY_RULE_MISMATCH", "AUXILIARY_ONLY_FUNCTION", "UNKNOWN_SOLID", "PRECONDITION_FAILED",
        "INTERNAL_FIELD_FROM_PROVIDER", "INVALID_TYPED_FACT_NEXT", "INVALID_PREMISE_ARGS",
        "INVALID_DERIVED_SECTION", "INVALID_RELATION_SPEC", "UNKNOWN_SOLID_ID", "UNKNOWN_VERTEX_REF",
        "BRIDGE_INCONSISTENT_SECTION", "SCHEMA_VERSION_MISMATCH", "ROUTE_LABEL_REQUIRED",
        "DUPLICATE_GOAL_ID", "DUPLICATE_SECTION_ID", "DUPLICATE_SOLID_ID", "EMPTY_SIMULATION_GOALS",
        "EMPTY_SOLIDS", "INVALID_MATH_GOAL", "INVALID_QUALIFIED_REF", "INVALID_SIMULATION_GOAL",
        "NO_RECORDED_EXTRACTION",
        "INVALID_SOLID_NOTATION", "INVALID_VERTEX_BINDING", "INVALID_VERTEX_CHAIN", "UNKNOWN_SECTION_ID"}),
     "Hệ chưa chuyển được đề này thành các dữ kiện dựng hình kiểm chứng được, nên không dựng hình."),
    ("INTEGRITY", "geometry_generation_failed", frozenset({
        "PREVIEW_IDENTITY_CHANGED", "PREVIEW_SURFACE_CHANGED", "PREVIEW_PROOF_STATUS_INVALID", "PREVIEW_DISABLED"}),
     "Kết quả dựng hình không còn khớp với phiên bản hoặc chứng nhận mà hệ đã kiểm, nên hệ không hiển thị hình."),
)
_FALLBACK = RefusalClass("FALLBACK", "geometry_generation_failed", "UNKNOWN",
                         "Hệ chưa dựng được hình đã kiểm chứng cho đề này, nên không hiển thị hình.")


def _de_ghi_do_dai_khong_duong(problem_text: str) -> bool:
    """The SERVER's own reader finds a length ≤ 0 in the premises of the text. The extracted value alone proves nothing:
    `doc_so` refuses 0 before the source gate compares the value with its quote (review of this run)."""
    from types import SimpleNamespace

    from app.simulation.semantic_program.refusal_cause import do_dai_de_ghi_khong_duong

    return bool(problem_text) and do_dai_de_ghi_khong_duong(SimpleNamespace(problem_text=problem_text)) is not None


def classify_refusal(code: str, planner: dict | None = None, *, adapter: bool = False,
                     problem_text: str = "") -> RefusalClass:
    """Group of a refusal from structured data only (never the `reason` prose). `adapter=True`: the preview's own check on
    a SERVED result raised it, so the code describes the system's output (a non-Euclidean chart there is a tampered scene,
    not contradictory givens). A `NEGATED_CLAUSE` that carries a negated observation was constructed and has no
    certificate (`function_route.run_fact_route`); without one the planner refused the clause as unsupported.
    `refusal_cause` is SOURCE only when the server reads the cause in `problem_text` itself."""
    if adapter and code == "METRIC_NOT_EUCLIDEAN":
        code = "PREVIEW_RESULT_INVALID"
    if code == "NEGATED_CLAUSE" and (planner or {}).get("negated_checks"):
        code = "PROOF_UNVERIFIABLE"
    group = next(((name, category, message) for name, category, codes, message in _NHOM if code in codes), None)
    if group is None:
        return _FALLBACK
    name, category, message = group
    if code == "NON_POSITIVE_LENGTH" and _de_ghi_do_dai_khong_duong(problem_text):
        return RefusalClass(name, category, "SOURCE", learner_reason(
            {"status": "unsupported", "reason_code": code, "failure_category": category, "refusal_cause": "SOURCE"}))
    return RefusalClass(name, category, "UNKNOWN", message)


def _refusal(code: str, policy, planner: dict | None = None, *, adapter: bool = False,
             problem_text: str = "") -> HybridPreviewEnvelope:
    kind = classify_refusal(code, planner, adapter=adapter, problem_text=problem_text)
    # Only verified observations survive a refusal: calls / trace / auxiliary carry model-supplied quotes that never
    # passed the source check (review of this run).
    kept = {k: deepcopy(v) for k, v in (planner or {}).items() if k in ("version", "goal_checks", "negated_checks")}
    return HybridPreviewEnvelope(envelope={"status": "unsupported", "reason_code": code, "reason": kind.message,
                                           "learner_reason": kind.message, "failure_category": kind.failure_category,
                                           "refusal_cause": kind.refusal_cause},
                                 route_d={"runtime_identity": preview_runtime_identity(policy), "planner": kept})


#: Backstop against narrative that presents a one-configuration observation as a proof; the primary guard is structural
#: (`proof_status` / `can_present_as_proven` in `adapt_result`). Matching runs on a DETECTION copy — NFKC (fullwidth
#: letters, compatibility dashes, Vietnamese letters composed), format characters (zero-width, soft hyphen) and the
#: combining marks NFKC could not compose (stray, e.g. U+034F) dropped, every dash folded to "-" — and never changes the
#: text that is served. Minus signs are math symbols (Sm) that NFKC keeps, so they are folded by name.
_GACH_TRU = frozenset("−➖˗⁃")   # MINUS SIGN, HEAVY MINUS SIGN, MODIFIER LETTER MINUS, HYPHEN BULLET
_CHUNG_MINH = r"chứng[\s\-_]*minh"
_LOI_CHUNG_MINH = re.compile(
    rf"(?:đã|được)\s*{_CHUNG_MINH}|{_CHUNG_MINH}\s*(?:thành\s*công|được|xong)|điều\s*phải\s*{_CHUNG_MINH}|đpcm")


def _ban_do(text: Any) -> str:
    """Detection copy of `text` (see `_LOI_CHUNG_MINH`)."""
    return "".join("-" if ch in _GACH_TRU or unicodedata.category(ch) == "Pd" else ch
                   for ch in unicodedata.normalize("NFKC", str(text))
                   if unicodedata.category(ch) not in ("Cf", "Mn")).casefold()


def _noi_chung_minh(text: Any) -> bool:
    return _LOI_CHUNG_MINH.search(_ban_do(text)) is not None


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
        # Quantity/construction events may have no rendered object (existing Scene3D contract). A group event creates the
        # objects it lists (lateral edges of a derived solid): births are read as the timeline reads them (`objectsAt`).
        for obj in (event.get("object"), *(event.get("objects") or ())):
            if obj:
                born.setdefault(obj, index)
    for oid, obj in objects.items():
        for dep in obj.get("depends") or ():
            if dep not in objects or dep in born and (oid not in born or born[dep] >= born[oid]):
                raise PreviewInvalid("PREVIEW_DEPENDENCY_INVALID")
    return metric


def adapt_result(result, policy, problem_text: str = "") -> HybridPreviewEnvelope:
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
        return _refusal(result.code or "PREVIEW_RESULT_INVALID", policy, planner, problem_text=problem_text)
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
        return adapt_result(result, policy, problem_text)
    except PreviewInvalid as exc:
        return _refusal(str(exc), policy, adapter=True)
    except Exception as exc:  # noqa: BLE001
        # The boundary refuses malformed/tampered deterministic output, with no raw error/model text in HTTP; the
        # exception TYPE is logged server-side so an operator can tell an adapter bug from a tampered result.
        _log.warning("Route D preview validation failed: %s", type(exc).__name__)
        return _refusal("PREVIEW_VALIDATION_FAILED", policy, adapter=True)
