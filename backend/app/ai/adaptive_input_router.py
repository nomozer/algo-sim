# -*- coding: utf-8 -*-
"""Adaptive Input Router (`adaptive-input-router/1`) — Local-First Geometry Understanding & Verified AI Fallback.

Implements the deterministic routing architecture across text, document, image, and user-edited inputs:
1. **Route T1 (Text / PDF Text / DOCX -> Local Parser -> Hybrid `/4`)**:
   - Runs `parse_geometry_problem_locally(problem_text)` (`0` AI calls).
   - If `LOCAL_PARSE_COMPLETE` or `LOCAL_PARSE_AMBIGUOUS`: executes `Source Gate -> FactGraph -> Planner -> Registry ->
     Exact Kernel -> Adapter /4` directly with **`0` provider calls**.
   - If `LOCAL_PARSE_UNSUPPORTED` with `GATE_OUT_OF_SCOPE`: returns deterministic out-of-scope refusal (`0` AI calls).
   - If `LOCAL_PARSE_PARTIAL` or `LOCAL_PARSE_UNSUPPORTED` (in-domain geometry phrasing outside local grammar):
     - If `allow_live_ai` is enabled and a `fallback_extractor` is provided, invokes `Gemini TypedFactNext` (`1` AI call)
       and passes its output through the identical `Source Gate -> FactGraph -> Planner -> Registry -> Exact Kernel ->
       Adapter /4` pipeline.
     - If `ALLOW_LIVE_AI=0` (or no fallback extractor is available), fails closed cleanly without guessing.
2. **Route I1 (Image / Scanned Page -> CV Preprocessing -> 1 Vision Call -> Local Parser -> Hybrid `/4`)**:
   - Runs local CV preprocessing and region detection (`0` AI calls).
   - Rejects blank/unreadable/diagram-only images or prompts region selection locally (`0` AI calls).
   - Calls `Gemini Vision` (`1` AI call) to transcribe Vietnamese problem text (with crop-to-full-image retry and
     equality-conflict confirmation guard).
   - Feeds the transcribed text into **Route T1** (`Deterministic Geometry Parser -> Hybrid /4`), solving standard
     geometry images with **`1` AI call total** (`50%` reduction vs `I0`'s `2` AI calls).
3. **Route I2 (Local OCR Gate — `LOCAL_OCR_DIAGNOSTIC_ONLY`)**:
   - Evaluates strict cross-engine agreement (`tesseract` + `vietocr`) on math tokens (`⊥, ∥, √, ∠, △, ′, =`) and
     numeric literals. Keeps `LOCAL_OCR_DIAGNOSTIC_ONLY` in production whenever math-symbol recall is below gate.
4. **User Edits & Confirmation Loop**:
   - Treats user-edited text as authoritative (`0` Vision re-calls) and routes through `Deterministic Geometry Parser`
     first (`0` `TypedFactNext` AI calls when `LOCAL_PARSE_COMPLETE` or `LOCAL_PARSE_AMBIGUOUS`).
   - Incorporates `LOCAL_GEOMETRY_PARSER_VERSION` and `ADAPTIVE_INPUT_ROUTER_VERSION` into cache identity.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from hashlib import sha256
import json
import os
import re
import time
from typing import Any, Callable, Literal, Sequence

from app.ai.adapter4_route import ADAPTER_V4_VERSION, ROUTE_D_SIMULATION_V4_SCHEMA_VERSION
from app.ai.hybrid_offline import HybridOfflineResult, hybrid_offline_policy, run_hybrid_offline
from app.ai.local_failure_diagnostics import diagnose
from app.ai.local_geometry_parser import (
    LOCAL_GEOMETRY_PARSER_VERSION,
    LOCAL_PARSE_AMBIGUOUS,
    LOCAL_PARSE_COMPLETE,
    LOCAL_PARSE_PARTIAL,
    LOCAL_PARSE_UNSUPPORTED,
    LocalParseResult,
    normalize_problem_text,
    parse_geometry_problem_locally,
    tokenize_problem_text,
)
from app.ai.route_policy import RoutePolicy
from app.ai.typed_fact_next_extraction import (
    Extractor,
    LiveAIDisabled,
    ReplayExtractor,
)
from app.simulation.error_codes import ErrorCode
from app.simulation.geometry_functions import engine, planner, registry
from app.simulation.geometry_functions.determinacy_audit import audit_determinacy_from_typed_facts
from app.simulation.geometry_functions.typed_fact_next import TYPED_FACT_NEXT_V2_SCHEMA_VERSION

ADAPTIVE_INPUT_ROUTER_VERSION = "adaptive-input-router/1"
LOCAL_OCR_PRODUCTION_STATUS = "LOCAL_OCR_DIAGNOSTIC_ONLY"

InputKind = Literal["text", "pdf_text", "docx", "image", "pdf_scan", "user_edited_text"]

ChosenRoute = Literal[
    "LOCAL_DETERMINISTIC_HYBRID",
    "LOCAL_OCR_VERIFIED_ZERO_AI",
    "LOCAL_AMBIGUOUS_CLARIFICATION",
    "LOCAL_OUT_OF_SCOPE_GATE",
    "AI_TYPED_FACT_FALLBACK",
    "LOCAL_SLM_FALLBACK",
    "VISION_THEN_LOCAL_DETERMINISTIC",
    "VISION_THEN_AI_FALLBACK",
    "VISION_NEEDS_CONFIRMATION",
    "LOCAL_CV_REJECTED_OR_SELECTION",
    "FAIL_CLOSED_LIVE_AI_DISABLED",
]


@dataclass(frozen=True)
class AdaptiveRouteTelemetry:
    router_version: str
    parser_version: str
    input_kind: InputKind
    local_parse_status: str
    chosen_route: ChosenRoute
    fallback_reason: str | None
    gemini_vision_calls: int
    gemini_typed_fact_calls: int
    total_provider_calls: int
    local_parse_ms: float
    vision_ms: float
    typed_fact_ai_ms: float
    hybrid_execution_ms: float
    total_ms: float
    source_coverage: dict[str, Any]
    cache_key_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "router_version": self.router_version,
            "parser_version": self.parser_version,
            "input_kind": self.input_kind,
            "local_parse_status": self.local_parse_status,
            "chosen_route": self.chosen_route,
            "fallback_reason": self.fallback_reason,
            "gemini_vision_calls": self.gemini_vision_calls,
            "gemini_typed_fact_calls": self.gemini_typed_fact_calls,
            "total_provider_calls": self.total_provider_calls,
            "local_parse_ms": round(self.local_parse_ms, 3),
            "vision_ms": round(self.vision_ms, 3),
            "typed_fact_ai_ms": round(self.typed_fact_ai_ms, 3),
            "hybrid_execution_ms": round(self.hybrid_execution_ms, 3),
            "total_ms": round(self.total_ms, 3),
            "source_coverage": self.source_coverage,
            "cache_key_metadata": self.cache_key_metadata,
        }


@dataclass(frozen=True)
class AdaptiveRouteOutcome:
    status: str
    response: dict[str, Any]
    receipt: dict[str, Any]
    telemetry: AdaptiveRouteTelemetry
    local_parse_result: LocalParseResult | None
    cache_key: str | None


def build_local_first_cache_identity(
    problem_text: str,
    *,
    extraction_route: str,
    model: str | None = None,
    local_parse_status: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Compute a deterministic cache key incorporating parser version, router version, extraction route, and Hybrid `/4` surface."""
    norm_text = normalize_problem_text(problem_text)
    metadata = {
        "route": "HYBRID_V4_LOCAL_FIRST",
        "router_version": ADAPTIVE_INPUT_ROUTER_VERSION,
        "parser_version": LOCAL_GEOMETRY_PARSER_VERSION,
        "extraction_route": extraction_route,
        "local_parse_status": local_parse_status or "UNKNOWN",
        "model": (model or "none") if extraction_route != "LOCAL_DETERMINISTIC_PARSER" else "none",
        "surface": {
            "registry_version": registry.REGISTRY_VERSION,
            "planner_version": planner.PLANNER_VERSION,
            "engine_version": engine.ENGINE_VERSION,
            "response_contract": TYPED_FACT_NEXT_V2_SCHEMA_VERSION,
            "adapter_version": ADAPTER_V4_VERSION,
            "envelope_version": ROUTE_D_SIMULATION_V4_SCHEMA_VERSION,
        },
        "source": norm_text,
    }
    digest = sha256(json.dumps(metadata, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return digest, metadata


class LocalFirstHybridExtractor(Extractor):
    """`Extractor` implementation that runs `parse_geometry_problem_locally` first (`0` AI calls) and only calls
    `fallback_extractor` when the local parser returns `LOCAL_PARSE_PARTIAL` or `LOCAL_PARSE_UNSUPPORTED`."""

    def __init__(
        self,
        *,
        fallback_extractor: Extractor | None = None,
        allow_live_ai: bool | None = None,
        precomputed_local: LocalParseResult | None = None,
    ) -> None:
        self.fallback_extractor = fallback_extractor
        self._allow_live_ai = allow_live_ai
        self._precomputed_local = precomputed_local
        self.last_local_result: LocalParseResult | None = None
        self.gemini_typed_fact_calls: int = 0
        self.typed_fact_ai_ms: float = 0.0
        self.used_fallback: bool = False

    def _is_fallback_allowed(self) -> bool:
        if self._allow_live_ai is not None:
            return self._allow_live_ai
        return os.environ.get("ALLOW_LIVE_AI", "1") != "0"

    def extract(self, problem_text: str) -> dict[str, Any] | None:
        local_res = (
            self._precomputed_local
            if self._precomputed_local is not None
            else parse_geometry_problem_locally(problem_text)
        )
        self.last_local_result = local_res

        if local_res.status in (LOCAL_PARSE_COMPLETE, LOCAL_PARSE_AMBIGUOUS) and local_res.payload is not None:
            self.used_fallback = False
            return local_res.payload

        # Fallback required
        if self.fallback_extractor is not None and self._is_fallback_allowed():
            t0 = time.perf_counter()
            self.gemini_typed_fact_calls += 1
            self.used_fallback = True
            out = self.fallback_extractor.extract(problem_text)
            self.typed_fact_ai_ms += (time.perf_counter() - t0) * 1000.0
            return out

        self.used_fallback = False
        if not self._is_fallback_allowed():
            raise LiveAIDisabled("ALLOW_LIVE_AI=0")
        return None


def _out_of_scope_response(problem_text: str) -> dict[str, Any]:
    return {
        "status": "unsupported",
        "reason": (
            "Hệ thống này mô phỏng HÌNH HỌC KHÔNG GIAN (Toán 11–12). "
            "Đề bạn gửi không thuộc phạm vi ấy."
        ),
        "failure_category": "out_of_scope",
        "error_code": ErrorCode.GATE_OUT_OF_SCOPE.value,
        "stage_reached": "domain",
        "route_d": {
            "status": "REFUSED",
            "adapter_version": ADAPTER_V4_VERSION,
            "schema_version": ROUTE_D_SIMULATION_V4_SCHEMA_VERSION,
            "extraction_mode": "LOCAL_DETERMINISTIC_PARSER",
            "refusal": {
                "code": ErrorCode.GATE_OUT_OF_SCOPE.value,
                "reason_code": ErrorCode.GATE_OUT_OF_SCOPE.value,
                "failure_category": "out_of_scope",
            },
        },
        "envelope": {
            "status": "unsupported",
            "failure_category": "out_of_scope",
            "error_code": ErrorCode.GATE_OUT_OF_SCOPE.value,
            "reason_code": ErrorCode.GATE_OUT_OF_SCOPE.value,
        },
    }


_TRAILING_MC_OPTIONS_RE = re.compile(
    r"(?P<stem_end>(?:(?<!\w)(?i:bằng|là)|[.?:)])\s*:?)"
    r"\s+(?<![\w'])A\s*[.)]\s*\S.*?"
    r"\s+(?<![\w'])B\s*[.)]\s*\S.*?"
    r"\s+(?<![\w'])C\s*[.)]\s*\S.*?"
    r"\s+(?<![\w'])D\s*[.)]\s*\S+\s*$",
    re.DOTALL,
)


def strip_trailing_multiple_choice_options(text: str) -> str:
    """Strip trailing multiple-choice answer key blocks (including out-of-order OCR scan blocks)."""
    from .local_geometry_parser import strip_mc_options_block

    return strip_mc_options_block(text)


def route_text_input(
    problem_text: str,
    *,
    fallback_extractor: Extractor | None = None,
    allow_live_ai: bool | None = None,
    fallback_unavailable_code: str | None = None,
    input_kind: InputKind = "text",
    previous_vision_calls: int = 0,
    previous_vision_ms: float = 0.0,
    model: str | None = None,
    policy: RoutePolicy | None = None,
    timeout_seconds: float = 15.0,
) -> AdaptiveRouteOutcome:
    """Route a Vietnamese problem text (`T1` or post-Vision `I1` / user-edited text) local-first into Hybrid `/4`."""
    t_total0 = time.perf_counter()
    norm_text = strip_trailing_multiple_choice_options(normalize_problem_text(problem_text))
    local_res = parse_geometry_problem_locally(norm_text)
    local_ms = local_res.parse_latency_ms
    eff_policy = policy if policy is not None else hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})

    is_fallback_allowed = (
        allow_live_ai if allow_live_ai is not None else (os.environ.get("ALLOW_LIVE_AI", "1") != "0")
    )

    # Case 1: Out-of-scope non-geometry rejected at local domain gate (`0` AI calls)
    if local_res.status == LOCAL_PARSE_UNSUPPORTED and local_res.reason_code == "GATE_OUT_OF_SCOPE":
        total_ms = (time.perf_counter() - t_total0) * 1000.0 + previous_vision_ms
        cache_key, cache_meta = build_local_first_cache_identity(
            norm_text,
            extraction_route="LOCAL_DETERMINISTIC_PARSER",
            model=model,
            local_parse_status=local_res.status,
        )
        telemetry = AdaptiveRouteTelemetry(
            router_version=ADAPTIVE_INPUT_ROUTER_VERSION,
            parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
            input_kind=input_kind,
            local_parse_status=local_res.status,
            chosen_route="LOCAL_OUT_OF_SCOPE_GATE",
            fallback_reason=None,
            gemini_vision_calls=previous_vision_calls,
            gemini_typed_fact_calls=0,
            total_provider_calls=previous_vision_calls,
            local_parse_ms=local_ms,
            vision_ms=previous_vision_ms,
            typed_fact_ai_ms=0.0,
            hybrid_execution_ms=0.0,
            total_ms=total_ms,
            source_coverage=local_res.source_coverage.to_dict(),
            cache_key_metadata=cache_meta,
        )
        resp = _out_of_scope_response(norm_text)
        resp["route_d"]["adaptive_telemetry"] = telemetry.to_dict()
        receipt = {
            "schema": "adaptive-input-route-receipt/1",
            "status": "REFUSED",
            "code": ErrorCode.GATE_OUT_OF_SCOPE.value,
            "telemetry": telemetry.to_dict(),
        }
        return AdaptiveRouteOutcome(
            status="REFUSED",
            response=resp,
            receipt=receipt,
            telemetry=telemetry,
            local_parse_result=local_res,
            cache_key=None,
        )

    # Case 2: Local parse complete or ambiguous -> execute Hybrid /4 directly with 0 TypedFactNext AI calls
    if local_res.status in (LOCAL_PARSE_COMPLETE, LOCAL_PARSE_AMBIGUOUS) and local_res.payload is not None:
        t_hyb0 = time.perf_counter()
        extractor = ReplayExtractor({norm_text: local_res.payload})
        hyb_out: HybridOfflineResult = run_hybrid_offline(
            norm_text, extractor, policy=eff_policy, timeout_seconds=timeout_seconds
        )
        hyb_ms = (time.perf_counter() - t_hyb0) * 1000.0
        total_ms = (time.perf_counter() - t_total0) * 1000.0 + previous_vision_ms

        route_d_raw = hyb_out.response.get("route_d") or {}
        status_str = str(route_d_raw.get("status") or "REFUSED")
        refusal_raw = route_d_raw.get("refusal") or {}
        env_raw = hyb_out.response.get("envelope") or {}
        ref_code = str(
            refusal_raw.get("code")
            or refusal_raw.get("reason_code")
            or env_raw.get("reason_code")
            or ""
        )

        det_audit: dict[str, Any] | None = None
        diag: dict[str, Any] | None = None
        reclassified_env: dict[str, Any] | None = None
        reclassified_group: str | None = None

        if status_str != "SERVED":
            raw_det = hyb_out.receipt.get("determinacy_audit")
            if isinstance(raw_det, dict):
                det_audit = deepcopy(raw_det)
            unresolved_items = list((local_res.payload or {}).get("unresolved") or [])
            unresolved_kinds = [str(u.get("kind") or "") for u in unresolved_items if isinstance(u, dict)]
            only_dim_missing = bool(unresolved_items) and all(
                isinstance(u, dict)
                and u.get("kind") == "missing_operand"
                and list(u.get("missing_roles") or []) == ["dimension"]
                for u in unresolved_items
            )
            if det_audit is None and (
                ref_code in ("MISSING_DIMENSION", "UNDERDETERMINED_POINT", "FOOT_NOT_DETERMINED", "PLANE_NOT_UNIQUE", "FIGURE_NOT_UNIQUE")
                or (local_res.status == LOCAL_PARSE_AMBIGUOUS and only_dim_missing)
            ):
                det_audit = audit_determinacy_from_typed_facts(
                    norm_text,
                    local_res.payload,
                    terminal_code=ref_code or "AMBIGUOUS_FACT",
                )
            diag = diagnose(
                parse_status=local_res.status,
                parse_reason=local_res.reason_code,
                fallback_reason=local_res.fallback_reason,
                source_coverage=local_res.source_coverage.to_dict(),
                terminal_code=ref_code or None,
                fallback_allowed=is_fallback_allowed,
                planner=route_d_raw.get("planner"),
                unresolved_kinds=unresolved_kinds,
                determinacy_audit=det_audit,
            )
            if hyb_out.receipt.get("failure_stage") != "adapter4" and ref_code:
                from app.ai.hybrid_preview import RefusalClass, classify_refusal

                if diag.get("root_cause") == "UNSUPPORTED_GOAL_KIND":
                    kind = RefusalClass(
                        "CAPABILITY",
                        "capability_gap",
                        "UNKNOWN",
                        "Hệ chưa hỗ trợ yêu cầu chứng minh hình học; hiện chỉ dựng hình và tính các đại lượng hình học không gian.",
                    )
                else:
                    is_proven_local_complete = (
                        local_res.status == LOCAL_PARSE_COMPLETE
                        or (
                            local_res.status == LOCAL_PARSE_AMBIGUOUS
                            and only_dim_missing
                            and (det_audit or {}).get("status") == "PROVED_UNDERDETERMINED"
                        )
                    )
                    kind = classify_refusal(
                        ref_code,
                        route_d_raw.get("planner"),
                        problem_text=norm_text,
                        details={"determinacy_audit": det_audit} if det_audit is not None else None,
                        local_complete=is_proven_local_complete,
                    )
                reclassified_env = {
                    "status": "unsupported",
                    "reason_code": ref_code,
                    "reason": kind.message,
                    "learner_reason": kind.message,
                    "failure_category": kind.failure_category,
                    "refusal_cause": kind.refusal_cause,
                }
                if hyb_out.receipt.get("failure_kind") != "TECHNICAL_FAILURE":
                    reclassified_group = kind.group

        eff_env = reclassified_env or env_raw
        fail_cat = str(
            refusal_raw.get("failure_category")
            or eff_env.get("failure_category")
            or ""
        )
        is_clarification_or_missing = (
            fail_cat == "insufficient_specification"
            or (
                local_res.status == LOCAL_PARSE_AMBIGUOUS
                and (diag or {}).get("taxonomy_class") != "CAPABILITY_UNSUPPORTED"
            )
        )
        chosen_route: ChosenRoute = (
            "VISION_THEN_LOCAL_DETERMINISTIC"
            if previous_vision_calls > 0
            else (
                "LOCAL_AMBIGUOUS_CLARIFICATION"
                if is_clarification_or_missing
                else "LOCAL_DETERMINISTIC_HYBRID"
            )
        )
        cache_key, cache_meta = build_local_first_cache_identity(
            norm_text,
            extraction_route="LOCAL_DETERMINISTIC_PARSER",
            model=model,
            local_parse_status=local_res.status,
        )
        telemetry = AdaptiveRouteTelemetry(
            router_version=ADAPTIVE_INPUT_ROUTER_VERSION,
            parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
            input_kind=input_kind,
            local_parse_status=local_res.status,
            chosen_route=chosen_route,
            fallback_reason=None,
            gemini_vision_calls=previous_vision_calls,
            gemini_typed_fact_calls=0,
            total_provider_calls=previous_vision_calls,
            local_parse_ms=local_ms,
            vision_ms=previous_vision_ms,
            typed_fact_ai_ms=0.0,
            hybrid_execution_ms=hyb_ms,
            total_ms=total_ms,
            source_coverage=local_res.source_coverage.to_dict(),
            cache_key_metadata=cache_meta,
        )
        response = dict(hyb_out.response)
        if reclassified_env is not None:
            response["envelope"] = reclassified_env
        route_d = dict(response.get("route_d") or {})
        route_d["extraction_mode"] = "LOCAL_DETERMINISTIC_PARSER"
        route_d["local_parser_version"] = LOCAL_GEOMETRY_PARSER_VERSION
        route_d["adaptive_router_version"] = ADAPTIVE_INPUT_ROUTER_VERSION
        route_d["adaptive_telemetry"] = telemetry.to_dict()
        if det_audit is not None:
            route_d["determinacy_audit"] = det_audit
        if diag is not None:
            # root cause ≠ terminal reason (run `semantic-failure-safe-image-segmentation`); refusals are never cached
            route_d["local_diagnostics"] = diag
        response["route_d"] = route_d
        receipt = {
            **hyb_out.receipt,
            **({"failure_kind": reclassified_group} if reclassified_group is not None else {}),
            **({"determinacy_audit": deepcopy(det_audit)} if det_audit is not None else {}),
            "adaptive_telemetry": telemetry.to_dict(),
        }
        return AdaptiveRouteOutcome(
            status=status_str,
            response=response,
            receipt=receipt,
            telemetry=telemetry,
            local_parse_result=local_res,
            cache_key=cache_key if status_str == "SERVED" else None,
        )

    # Case 3: Local parser returned LOCAL_PARSE_PARTIAL or LOCAL_PARSE_UNSUPPORTED -> AI Fallback or Fail-Closed
    if fallback_extractor is not None and is_fallback_allowed:
        lf_ext = LocalFirstHybridExtractor(
            fallback_extractor=fallback_extractor,
            allow_live_ai=True,
            precomputed_local=local_res,
        )
        t_hyb0 = time.perf_counter()
        hyb_out = run_hybrid_offline(norm_text, lf_ext, policy=eff_policy, timeout_seconds=timeout_seconds)
        hyb_total_ms = (time.perf_counter() - t_hyb0) * 1000.0
        ai_ms = lf_ext.typed_fact_ai_ms
        hyb_exec_ms = max(0.0, hyb_total_ms - ai_ms)
        total_ms = (time.perf_counter() - t_total0) * 1000.0 + previous_vision_ms

        chosen_route = "VISION_THEN_AI_FALLBACK" if previous_vision_calls > 0 else "AI_TYPED_FACT_FALLBACK"
        cache_key, cache_meta = build_local_first_cache_identity(
            norm_text,
            extraction_route="AI_TYPED_FACT_FALLBACK",
            model=model,
            local_parse_status=local_res.status,
        )
        telemetry = AdaptiveRouteTelemetry(
            router_version=ADAPTIVE_INPUT_ROUTER_VERSION,
            parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
            input_kind=input_kind,
            local_parse_status=local_res.status,
            chosen_route=chosen_route,
            fallback_reason=local_res.fallback_reason or local_res.reason_code,
            gemini_vision_calls=previous_vision_calls,
            gemini_typed_fact_calls=lf_ext.gemini_typed_fact_calls,
            total_provider_calls=previous_vision_calls + lf_ext.gemini_typed_fact_calls,
            local_parse_ms=local_ms,
            vision_ms=previous_vision_ms,
            typed_fact_ai_ms=ai_ms,
            hybrid_execution_ms=hyb_exec_ms,
            total_ms=total_ms,
            source_coverage=local_res.source_coverage.to_dict(),
            cache_key_metadata=cache_meta,
        )
        response = dict(hyb_out.response)
        route_d = dict(response.get("route_d") or {})
        route_d["extraction_mode"] = "AI_TYPED_FACT_FALLBACK"
        route_d["local_parser_version"] = LOCAL_GEOMETRY_PARSER_VERSION
        route_d["adaptive_router_version"] = ADAPTIVE_INPUT_ROUTER_VERSION
        route_d["adaptive_telemetry"] = telemetry.to_dict()
        response["route_d"] = route_d
        receipt = {
            **hyb_out.receipt,
            "adaptive_telemetry": telemetry.to_dict(),
        }
        status_str = str(route_d.get("status") or "REFUSED")
        return AdaptiveRouteOutcome(
            status=status_str,
            response=response,
            receipt=receipt,
            telemetry=telemetry,
            local_parse_result=local_res,
            cache_key=cache_key if status_str == "SERVED" else None,
        )

    # Case 4: Fail-closed when ALLOW_LIVE_AI=0 or no fallback extractor is configured
    fail_code = (
        "LIVE_AI_DISABLED"
        if not is_fallback_allowed
        else (fallback_unavailable_code or local_res.reason_code or "LOCAL_PARSE_FALLBACK_REQUIRED")
    )
    is_infra_block = fail_code in ("LIVE_AI_DISABLED", "MISSING_API_KEY")
    total_ms = (time.perf_counter() - t_total0) * 1000.0 + previous_vision_ms
    _, cache_meta = build_local_first_cache_identity(
        norm_text,
        extraction_route="FAIL_CLOSED_NO_FALLBACK",
        model=model,
        local_parse_status=local_res.status,
    )
    telemetry = AdaptiveRouteTelemetry(
        router_version=ADAPTIVE_INPUT_ROUTER_VERSION,
        parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
        input_kind=input_kind,
        local_parse_status=local_res.status,
        chosen_route="FAIL_CLOSED_LIVE_AI_DISABLED",
        fallback_reason=local_res.fallback_reason or local_res.reason_code,
        gemini_vision_calls=previous_vision_calls,
        gemini_typed_fact_calls=0,
        total_provider_calls=previous_vision_calls,
        local_parse_ms=local_ms,
        vision_ms=previous_vision_ms,
        typed_fact_ai_ms=0.0,
        hybrid_execution_ms=0.0,
        total_ms=total_ms,
        source_coverage=local_res.source_coverage.to_dict(),
        cache_key_metadata=cache_meta,
    )
    response = {
        "schema_version": ROUTE_D_SIMULATION_V4_SCHEMA_VERSION,
        "route_d": {
            "status": "REFUSED",
            "adapter_version": ADAPTER_V4_VERSION,
            "schema_version": ROUTE_D_SIMULATION_V4_SCHEMA_VERSION,
            "extraction_mode": "FAIL_CLOSED_NO_FALLBACK",
            "local_parser_version": LOCAL_GEOMETRY_PARSER_VERSION,
            "adaptive_router_version": ADAPTIVE_INPUT_ROUTER_VERSION,
            "adaptive_telemetry": telemetry.to_dict(),
            "refusal": {
                "code": fail_code,
                "reason_code": fail_code,
                "fallback_reason": local_res.fallback_reason,
            },
            # the terminal reason above says the fallback was blocked; this says what the local route did not read
            "local_diagnostics": diagnose(
                parse_status=local_res.status, parse_reason=local_res.reason_code, fallback_reason=local_res.fallback_reason,
                source_coverage=local_res.source_coverage.to_dict(), terminal_code=fail_code,
                fallback_allowed=is_fallback_allowed),
        },
        "envelope": {
            "status": "refused",
            "reason_code": fail_code,
            "failure_kind": "INFRASTRUCTURE_FAILURE" if is_infra_block else "EXTRACTION_FALLBACK_REQUIRED",
        },
    }
    receipt = {
        "schema": "adaptive-input-route-receipt/1",
        "status": "REFUSED",
        "code": fail_code,
        "failure_kind": "TECHNICAL_FAILURE" if is_infra_block else "EXTRACTION_FAILURE",
        "adaptive_telemetry": telemetry.to_dict(),
    }
    return AdaptiveRouteOutcome(
        status="REFUSED",
        response=response,
        receipt=receipt,
        telemetry=telemetry,
        local_parse_result=local_res,
        cache_key=None,
    )


def route_edited_text_input(
    edited_problem_text: str,
    *,
    previous_vision_calls: int = 0,
    fallback_extractor: Extractor | None = None,
    allow_live_ai: bool | None = None,
    model: str | None = None,
    policy: RoutePolicy | None = None,
    timeout_seconds: float = 15.0,
) -> AdaptiveRouteOutcome:
    """Section VII — Route user-edited / confirmed problem text as authoritative (`0` new Vision calls, `0` TypedFactNext
    AI calls when `LOCAL_PARSE_COMPLETE` or `LOCAL_PARSE_AMBIGUOUS`)."""
    outcome = route_text_input(
        edited_problem_text,
        fallback_extractor=fallback_extractor,
        allow_live_ai=allow_live_ai,
        input_kind="user_edited_text",
        previous_vision_calls=0,  # 0 new Vision calls on edited text re-submission
        previous_vision_ms=0.0,
        model=model,
        policy=policy,
        timeout_seconds=timeout_seconds,
    )
    # Record historical vision provenance in cache_key_metadata without charging a new provider call
    meta = {
        **outcome.telemetry.cache_key_metadata,
        "authoritative_source": "user_edited_text",
        "prior_session_vision_calls_not_repeated": previous_vision_calls,
    }
    updated_tel = AdaptiveRouteTelemetry(
        router_version=outcome.telemetry.router_version,
        parser_version=outcome.telemetry.parser_version,
        input_kind="user_edited_text",
        local_parse_status=outcome.telemetry.local_parse_status,
        chosen_route=outcome.telemetry.chosen_route,
        fallback_reason=outcome.telemetry.fallback_reason,
        gemini_vision_calls=0,
        gemini_typed_fact_calls=outcome.telemetry.gemini_typed_fact_calls,
        total_provider_calls=outcome.telemetry.gemini_typed_fact_calls,
        local_parse_ms=outcome.telemetry.local_parse_ms,
        vision_ms=0.0,
        typed_fact_ai_ms=outcome.telemetry.typed_fact_ai_ms,
        hybrid_execution_ms=outcome.telemetry.hybrid_execution_ms,
        total_ms=outcome.telemetry.total_ms,
        source_coverage=outcome.telemetry.source_coverage,
        cache_key_metadata=meta,
    )
    resp = dict(outcome.response)
    rd = dict(resp.get("route_d") or {})
    rd["adaptive_telemetry"] = updated_tel.to_dict()
    resp["route_d"] = rd
    rec = {**outcome.receipt, "adaptive_telemetry": updated_tel.to_dict()}
    return AdaptiveRouteOutcome(
        status=outcome.status,
        response=resp,
        receipt=rec,
        telemetry=updated_tel,
        local_parse_result=outcome.local_parse_result,
        cache_key=outcome.cache_key,
    )


_MATH_TOKEN_GATE_RE = re.compile(
    r"(?:⊥|∥|√\d+|∠|△|[A-Z][0-9']*'[0-9']*(?:\.[A-Z0-9']+)?|[A-Z]\.[A-Z]{3,6}|=\s*\d+(?:√\d+)?(?:/\d+)?|\d+°)"
)

_OCR_CORRUPTION_ARTIFACT_RE = re.compile(
    r"(?:Œ|”|“|(?:(?:\b[0-9a-z]+[Vv]\d+\b)|(?:=\s*[Vv]\d+\b))"
    r"|\b[0O][Oo]\b|\b1[lI]\b|\.\.\.+"
    r"|\b[A-Z],[A-Z]{3,6}\b|\b[A-Z]{3,6}-[A-Z]{3,6}\b"
    r"|\b\d{2,}[A-Z]{1,5}\b|\b\d+[A-Z]{2,5}\b"
    r"|\b[A-Z]\.[A-Z]*[08][A-Z]+\b|\([A-Z]*[08][A-Z]+\)"
    r"|\b\d+(?:/\d+){2,}\b|\n\s*[-─—–]{2,}\s*\n"
    r"|[A-Z]{3,4}\.[A-Z]'[A-Z]'[A-Z](?!'[A-Z]?)\b"
    r"|[A-Z]{3,6}\.(?=[A-Z0-9']*')(?:[A-Z]'?)*[A-Z]{2}[A-Z0-9']*"
    r"|[A-Z][0-9']*°[A-Z0-9']*)"
)
_DIAGRAM_DEPENDENCY_RE = re.compile(
    r"(?:hình\s+vẽ\s+bên|như\s+hình\s+(?:vẽ|bên)|trong\s+hình\s+vẽ|ở\s+hình\s+bên"
    r"|tham\s+khảo\s+hình(?:\s+vẽ|\s+bên)?|xem\s+hình(?:\s+vẽ|\s+bên)?|ghi\s+trên\s+hình)",
    re.IGNORECASE,
)


def extract_structured_math_tokens(text: str) -> dict[str, Any]:
    """Extract all 12 critical math symbol categories from Vietnamese problem text for Input Fidelity & Conflict checks."""
    norm = normalize_problem_text(text or "")
    solids = sorted(
        set(
            re.findall(
                r"(?<![A-Za-z0-9'])(?:[A-Z]\.[A-Z]{3,6}|[A-Z]{3,6}\.[A-Z0-9']{3,12})(?![A-Za-z0-9'])",
                norm,
            )
        )
    )
    primed_labels = sorted(set(re.findall(r"(?<![A-Za-z0-9])[A-Z][0-9]*'[0-9']*", norm)))
    subscript_labels = sorted(
        set(re.findall(r"\b[A-Za-z]_[0-9]+\b|\b[A-Za-z][₀₁₂₃₄₅₆₇₈₉]+\b", text or ""))
    )
    radicals = sorted(set(re.findall(r"(?:[0-9a-zA-Z]+)?√\d+(?:/\d+)?", norm)))
    assignments: dict[str, str] = {}
    for m_asg in re.finditer(
        r"\b([A-Za-z0-9_'′₁₂₃]+(?:\s*=\s*[A-Za-z0-9_'′₁₂₃]+)*)\s*=\s*(-?[^\s,.;:]+)",
        norm,
    ):
        lhs_chain = [p.strip().replace("′", "'") for p in m_asg.group(1).split("=") if p.strip()]
        rhs_val = m_asg.group(2).strip().rstrip(".,;:")
        for lhs_item in lhs_chain:
            assignments[lhs_item] = rhs_val

    relations = sorted(
        set(
            re.findall(
                r"(?:⊥|∥|\bvuông\s+góc\b|\bsong\s+song\b)",
                norm,
                flags=re.IGNORECASE,
            )
        )
    )
    planes = sorted(set(re.findall(r"\([A-Z0-9']{3,9}\)|\([αβγPQR]\)", norm)))
    angles_degrees = sorted(set(re.findall(r"\b\d+\s*°|∠[A-Z0-9']{1,6}", norm)))
    fractions = sorted(set(re.findall(r"\b[0-9a-zA-Z√]+\s*/\s*\d+\b", norm)))
    decimals = sorted(set(re.findall(r"\b\d+[.,]\d+\b", text or "")))
    negatives = sorted(set(re.findall(r"(?<![A-Za-z0-9])-\d+(?:[.,]\d+)?\b", norm)))
    variables = sorted(set(re.findall(r"\b[abchRrxzy]\b", norm)))

    return {
        "solids": solids,
        "primed_labels": primed_labels,
        "subscript_labels": subscript_labels,
        "radicals": radicals,
        "assignments": assignments,
        "relations": [r.lower() for r in relations],
        "planes": planes,
        "angles_degrees": angles_degrees,
        "fractions": fractions,
        "decimals": decimals,
        "negatives": negatives,
        "variables": variables,
    }


def reconcile_dual_ocr_texts(
    primary_vi_ocr_text: str,
    secondary_math_ocr_text: str | None,
    *,
    has_diagram: bool = False,
    is_degraded_image: bool = False,
    is_handwritten: bool = False,
) -> dict[str, Any]:
    """Deterministically reconcile `primary_vi_ocr_text` (e.g. Tesseract `vie+eng` with full Vietnamese diacritics)
    and `secondary_math_ocr_text` (e.g. RapidOCR PP-OCRv6 with exact ASCII/prime math tokens) without any ground truth.

    Safety Rules (Zero-AI Gate):
    1. Never uses ground truth or problem IDs (`used_ground_truth = False`).
    2. Immediately refuses if `is_degraded_image=True`, `has_diagram=True`, `is_handwritten=True`, or `secondary_math_ocr_text` is missing/empty.
    3. Requires exact line-count and problem-header (`Câu N` / `Bài N`) alignment and at most 1 problem header.
    4. Requires 100% agreement between both engines on all numeric assignments (`=`), planes, radicals, fractions,
       angles, decimals, negatives, and subscript labels.
    5. Repairs a syntactically broken prism/box token `<BASE>.<CORRUPTED_TOP>` in `primary_vi_ocr_text` (such as
       `ABCD.A'B°C'D'`) ONLY when `secondary_math_ocr_text` contains the exact canonical `<BASE>.<PRIMED_BASE>` token
       (`ABCD.A'B'C'D'`) matching `<BASE>`.
    """
    if is_degraded_image or is_handwritten or has_diagram:
        reason = (
            "DEGRADED_IMAGE_REQUIRES_VISION_FALLBACK"
            if is_degraded_image
            else (
                "HANDWRITTEN_IMAGE_REQUIRES_VISION_FALLBACK"
                if is_handwritten
                else "DIAGRAM_CONTEXT_REQUIRES_VISION_FALLBACK"
            )
        )
        return {
            "reconciled": False,
            "reconciled_text": None,
            "reason_code": reason,
            "repairs": [],
            "used_ground_truth": False,
        }
    p_raw = strip_trailing_multiple_choice_options((primary_vi_ocr_text or "").strip())
    s_raw = strip_trailing_multiple_choice_options((secondary_math_ocr_text or "").strip())
    if not p_raw or not s_raw:
        return {
            "reconciled": False,
            "reconciled_text": None,
            "reason_code": "MISSING_SECONDARY_OCR",
            "repairs": [],
            "used_ground_truth": False,
        }

    p_lines = [ln.strip() for ln in p_raw.splitlines() if ln.strip()]
    s_lines = [ln.strip() for ln in s_raw.splitlines() if ln.strip()]
    if len(p_lines) != len(s_lines):
        return {
            "reconciled": False,
            "reconciled_text": None,
            "reason_code": "LINE_COUNT_MISMATCH",
            "repairs": [],
            "used_ground_truth": False,
        }

    p_headers = re.findall(r"\b(?:Câu|Cau|Bài|Bai)\s*(\d+)\b", p_raw, flags=re.IGNORECASE)
    s_headers = re.findall(r"\b(?:Câu|Cau|Bài|Bai)\s*(\d+)\b", s_raw, flags=re.IGNORECASE)
    if len(p_headers) > 1 or len(s_headers) > 1 or p_headers != s_headers:
        return {
            "reconciled": False,
            "reconciled_text": None,
            "reason_code": "PROBLEM_HEADER_MISMATCH_OR_MULTI_PROBLEM",
            "repairs": [],
            "used_ground_truth": False,
        }

    p_tok = extract_structured_math_tokens(p_raw)
    s_tok = extract_structured_math_tokens(s_raw)
    for key in (
        "assignments",
        "planes",
        "radicals",
        "angles_degrees",
        "fractions",
        "decimals",
        "negatives",
        "subscript_labels",
    ):
        if p_tok[key] != s_tok[key]:
            return {
                "reconciled": False,
                "reconciled_text": None,
                "reason_code": f"CROSS_ENGINE_DISAGREEMENT:{key}",
                "repairs": [],
                "used_ground_truth": False,
            }

    reconciled_text = p_raw
    repairs: list[dict[str, str]] = []
    for m_prism in re.finditer(
        r"(?<![A-Za-z0-9'])(?P<base>[A-Z]{3,6})\.(?P<top>[A-Z0-9'′°*`´Œ”\"](?:[A-Z0-9'′°*`´Œ”\"]|\s(?=[0-9A-Z'′°Œ”\"])){1,12}[A-Z]['′°”\"])(?![A-Za-z0-9'′°*`´Œ”\"])",
        p_raw,
    ):
        base_str = m_prism.group("base")
        top_str = m_prism.group("top")
        expected_top = "".join(f"{ch}'" for ch in base_str)
        expected_solid = f"{base_str}.{expected_top}"
        full_tok = m_prism.group(0)
        if full_tok.replace("′", "'") != expected_solid and expected_solid in s_tok["solids"]:
            reconciled_text = reconciled_text.replace(full_tok, expected_solid, 1)
            repairs.append(
                {
                    "corrupted_token": full_tok,
                    "repaired_token": expected_solid,
                    "evidence": "secondary_ocr_exact_solid_match",
                }
            )

    fid = verify_ocr_input_fidelity(
        reconciled_text,
        secondary_ocr_text=s_raw,
        has_diagram=has_diagram,
        is_degraded_image=is_degraded_image,
        is_handwritten=is_handwritten,
    )
    return {
        "reconciled": bool(fid["fidelity_passed"]),
        "reconciled_text": reconciled_text if fid["fidelity_passed"] else None,
        "reason_code": None if fid["fidelity_passed"] else fid["reason_code"],
        "repairs": repairs,
        "used_ground_truth": False,
        "fidelity_report": fid,
    }


def verify_ocr_input_fidelity(
    ocr_text: str,
    *,
    secondary_ocr_text: str | None = None,
    has_diagram: bool = False,
    is_degraded_image: bool = False,
    is_handwritten: bool = False,
) -> dict[str, Any]:
    """Evaluate the 6-criteria Input Fidelity Gate (`Phase 2.6`) before trusting Local OCR without Gemini Vision.

    Criteria:
    1. `vertex_and_solid_consistency`: Declared solid notation is well-formed and all referenced vertices/planes are consistent; no OCR corruption artifacts (`Œ`, `2V3`, broken prism notation).
    2. `dimension_and_number_fidelity`: Every `=` assignment has a valid exact positive numeric/symbolic value and no truncated decimals, negatives, or corrupted radicals.
    3. `geometric_relation_syntax`: All perpendicular/parallel/midpoint/projection relations parse cleanly without unparsed fact candidates.
    4. `goal_sentence_completeness`: At least one complete goal is parsed and bound to a valid target without unparsed goal candidates.
    5. `source_span_coverage`: `parse_geometry_problem_locally` returns `LOCAL_PARSE_COMPLETE` with `0` unparsed clauses and `coverage_ratio >= 0.85`.
    6. `diagram_dependency_and_cross_engine`: Problem does not depend on an external diagram (`như hình vẽ`), is not a degraded image, and if `secondary_ocr_text` is provided, structured math tokens agree 100%.
    """
    raw = strip_trailing_multiple_choice_options((ocr_text or "").strip())
    norm = normalize_problem_text(raw)
    tokens = extract_structured_math_tokens(raw)
    local_res = parse_geometry_problem_locally(norm) if norm else None

    has_ocr_artifacts = bool(_OCR_CORRUPTION_ARTIFACT_RE.search(raw))
    payload = local_res.payload if (local_res and local_res.payload) else {}
    solids_payload = payload.get("solids") or []
    goals_payload = (
        (payload.get("math_goals") or [])
        + (payload.get("simulation_goals") or [])
        + (payload.get("derived_sections") or [])
    )
    cov = local_res.source_coverage if local_res else None
    unparsed_facts = list(cov.unparsed_fact_candidates) if cov else []
    unparsed_goals = list(cov.unparsed_goal_candidates) if cov else []

    # 1. Vertex & solid consistency
    c1_vertex_solid = bool(
        norm
        and not has_ocr_artifacts
        and len(solids_payload) >= 1
        and (local_res is not None and local_res.reason_code != "UNPARSED_SOLID_OR_GOAL")
    )

    # 2. Dimension & number fidelity
    # Check that raw text has no corrupted numbers (`2V3`), comma-decimal truncation, negative lengths, or zero lengths
    has_comma_decimal = bool(re.search(r"\b\d+,\d+\b", raw))
    has_non_positive_length = bool(tokens["negatives"]) or any(
        v in ("0", "0.0", "-0") or v.startswith("-") for v in tokens["assignments"].values()
    )
    valid_angle_degrees = all(
        0 < int(m_deg.group(1)) < 180
        for ang in tokens["angles_degrees"]
        for m_deg in [re.match(r"^(\d+)\s*°$", ang)]
        if m_deg
    )
    c2_dimension_fidelity = bool(
        norm
        and not has_ocr_artifacts
        and not has_comma_decimal
        and not has_non_positive_length
        and valid_angle_degrees
        and all(
            re.match(
                r"^(?:[1-9]\d*(?:√\d+)?(?:/\d+)?|[1-9]?\d*√\d+a(?:/\d+)?|√\d+a?(?:/\d+)?|[1-9]?\d*\s*a(?:√\d+)?(?:/\d+)?)$",
                v,
            )
            for v in tokens["assignments"].values()
        )
    )

    # 3. Geometric relation syntax
    c3_relation_syntax = bool(
        norm
        and len(unparsed_facts) == 0
        and (local_res is not None and local_res.reason_code != "UNPARSED_FACT_CANDIDATE")
    )

    # 4. Goal sentence completeness (auto-added construct_object from "Cho ..." alone does not count without explicit sim verb)
    has_explicit_sim_verb = bool(
        re.search(r"\b(?:vẽ|dựng|mô\s+phỏng|biểu\s+diễn|cho\s+(?:mình|em|tôi)\s+xem)\b", norm, re.IGNORECASE)
    )
    has_real_goal = (
        len(payload.get("math_goals") or []) >= 1
        or len(payload.get("derived_sections") or []) >= 1
        or (has_explicit_sim_verb and len(payload.get("simulation_goals") or []) >= 1)
    )
    c4_goal_complete = bool(
        norm
        and has_real_goal
        and len(unparsed_goals) == 0
        and (local_res is not None and local_res.reason_code != "UNPARSED_GOAL_CANDIDATE")
    )

    # 5. Source span coverage
    c5_source_coverage = bool(
        local_res is not None
        and local_res.status == LOCAL_PARSE_COMPLETE
        and cov is not None
        and cov.coverage_complete
    )

    # 6. Diagram dependency & optional cross-engine agreement across all math-critical token categories
    has_diag_phrase = bool(_DIAGRAM_DEPENDENCY_RE.search(raw))
    cross_agree = True
    if secondary_ocr_text is not None:
        sec_tokens = extract_structured_math_tokens(secondary_ocr_text)
        # Note: secondary OCR (e.g. PP-OCRv6 without Vietnamese diacritics) may spell "vuong goc" instead of "vuông góc";
        # compare symbolic relations (`⊥`, `∥`) and all notation/numeric categories strictly.
        p_sym_rel = [r for r in tokens["relations"] if r in ("⊥", "∥")]
        s_sym_rel = [r for r in sec_tokens["relations"] if r in ("⊥", "∥")]
        cross_agree = bool(
            tokens["solids"] == sec_tokens["solids"]
            and tokens["primed_labels"] == sec_tokens["primed_labels"]
            and tokens["subscript_labels"] == sec_tokens["subscript_labels"]
            and tokens["assignments"] == sec_tokens["assignments"]
            and tokens["planes"] == sec_tokens["planes"]
            and tokens["radicals"] == sec_tokens["radicals"]
            and tokens["angles_degrees"] == sec_tokens["angles_degrees"]
            and tokens["fractions"] == sec_tokens["fractions"]
            and tokens["decimals"] == sec_tokens["decimals"]
            and tokens["negatives"] == sec_tokens["negatives"]
            and p_sym_rel == s_sym_rel
        )
    c6_diagram_and_engine = bool(
        not has_diag_phrase
        and not has_diagram
        and not is_degraded_image
        and not is_handwritten
        and cross_agree
    )

    checks = {
        "vertex_and_solid_consistency": c1_vertex_solid,
        "dimension_and_number_fidelity": c2_dimension_fidelity,
        "geometric_relation_syntax": c3_relation_syntax,
        "goal_sentence_completeness": c4_goal_complete,
        "source_span_coverage": c5_source_coverage,
        "diagram_dependency_and_cross_engine": c6_diagram_and_engine,
    }
    failed_checks = [k for k, ok in checks.items() if not ok]
    fidelity_passed = len(failed_checks) == 0

    return {
        "fidelity_passed": fidelity_passed,
        "checks": checks,
        "failed_checks": failed_checks,
        "local_parse_status": local_res.status if local_res else "EMPTY",
        "reason_code": None
        if fidelity_passed
        else (
            "DEGRADED_IMAGE_REQUIRES_VISION_FALLBACK"
            if is_degraded_image
            else (
                "HANDWRITTEN_IMAGE_REQUIRES_VISION_FALLBACK"
                if is_handwritten
                else (
                    local_res.reason_code
                    if local_res and local_res.reason_code
                    else "OCR_FIDELITY_GATE_FAILED"
                )
            )
        ),
        "structured_tokens": tokens,
    }


def compare_ocr_and_vision_facts(ocr_text: str, vision_text: str) -> dict[str, Any]:
    """Compare structured math facts between Local OCR and Gemini Vision (`Phase 2.7`).

    Detects critical discrepancies across all 13 math symbol classes where silent selection could produce a wrong result:
    - `NUMERIC_ASSIGNMENT_CONFLICT`: Same segment/variable assigned different values (e.g. `SA=3` vs `SA=8` or `SA=5`).
    - `PRIME_OR_PLANE_LABEL_CONFLICT`: Plane or primed vertex notation differs (e.g. `(ABC)` vs `(A'BC)` or `AC` vs `AC'`).
    - `SOLID_NOTATION_CONFLICT`: Declared solid differs (e.g. `ABC.A'B'C'` vs `ABC.ABC` or `S.ABC` vs `S.ABCD`).
    - `RELATION_SYMBOL_CONFLICT`: Geometric relation differs (`⊥` vs `∥` or `vuông góc` vs `song song`).
    - `RADICAL_OR_FRACTION_CONFLICT`: Radical (`√2` vs `√3`) or fraction (`1/2` vs `1/3`) differs.
    - `ANGLE_OR_SIGN_CONFLICT`: Angle degree (`60°` vs `30°`), negative sign, or subscript (`d_1` vs `d_2`) differs.
    """
    ocr_tok = extract_structured_math_tokens(ocr_text or "")
    vis_tok = extract_structured_math_tokens(vision_text or "")
    conflicts: list[dict[str, Any]] = []
    conflict_codes: list[str] = []

    # 1. Numeric assignment conflict on shared LHS targets
    ocr_asg = ocr_tok["assignments"]
    vis_asg = vis_tok["assignments"]
    for lhs, vis_val in vis_asg.items():
        if lhs in ocr_asg and ocr_asg[lhs] != vis_val:
            conflicts.append(
                {
                    "code": "NUMERIC_ASSIGNMENT_CONFLICT",
                    "target": lhs,
                    "ocr_value": ocr_asg[lhs],
                    "vision_value": vis_val,
                }
            )
            if "NUMERIC_ASSIGNMENT_CONFLICT" not in conflict_codes:
                conflict_codes.append("NUMERIC_ASSIGNMENT_CONFLICT")

    # Worded dimensions ("cạnh 2a") have no '=' assignment; preserve their values too.
    def worded_dimensions(text: str) -> list[tuple[str, str]]:
        normalized = re.sub(r"(?<=\d)\s+(?=a(?:\b|√))", "", normalize_problem_text(text or ""))
        dimensions = []
        for token in tokenize_problem_text(normalized):
            if token.kind != "value":
                continue
            prefix = re.search(
                r"(?P<target>cạnh(?:\s+(?:đáy|bên))?|chiều\s+(?:cao|dài|rộng)|đường\s+(?:cao|chéo|kính)|bán\s+kính)"
                r"(?:\s+(?:là|bằng)|\s*=)?\s*$", normalized[:token.start], re.IGNORECASE,
            )
            if prefix:
                dimensions.append((" ".join(prefix.group("target").lower().split()), token.text))
        return sorted(dimensions)

    ocr_values = worded_dimensions(ocr_text)
    vis_values = worded_dimensions(vision_text)
    if ocr_values != vis_values:
        conflicts.append({"code": "NUMERIC_ASSIGNMENT_CONFLICT", "ocr_values": ocr_values, "vision_values": vis_values})
        if "NUMERIC_ASSIGNMENT_CONFLICT" not in conflict_codes:
            conflict_codes.append("NUMERIC_ASSIGNMENT_CONFLICT")

    # 2. Plane / prime label conflict (e.g. `(ABC)` in OCR vs `(A'BC)` in Vision, or `AC` vs `AC'`)
    ocr_planes = set(ocr_tok["planes"])
    vis_planes = set(vis_tok["planes"])
    if ocr_planes and vis_planes and ocr_planes != vis_planes:
        for vp in sorted(vis_planes - ocr_planes):
            vp_unprimed = vp.replace("'", "")
            for op in sorted(ocr_planes - vis_planes):
                if op.replace("'", "") == vp_unprimed or op != vp:
                    conflicts.append(
                        {
                            "code": "PRIME_OR_PLANE_LABEL_CONFLICT",
                            "ocr_plane": op,
                            "vision_plane": vp,
                        }
                    )
                    if "PRIME_OR_PLANE_LABEL_CONFLICT" not in conflict_codes:
                        conflict_codes.append("PRIME_OR_PLANE_LABEL_CONFLICT")
    if ocr_tok["primed_labels"] != vis_tok["primed_labels"] and (ocr_tok["primed_labels"] or vis_tok["primed_labels"]):
        conflicts.append(
            {
                "code": "PRIME_OR_PLANE_LABEL_CONFLICT",
                "ocr_primed_labels": ocr_tok["primed_labels"],
                "vision_primed_labels": vis_tok["primed_labels"],
            }
        )
        if "PRIME_OR_PLANE_LABEL_CONFLICT" not in conflict_codes:
            conflict_codes.append("PRIME_OR_PLANE_LABEL_CONFLICT")

    # 3. Solid notation conflict
    if ocr_tok["solids"] and vis_tok["solids"] and ocr_tok["solids"] != vis_tok["solids"]:
        conflicts.append(
            {
                "code": "SOLID_NOTATION_CONFLICT",
                "ocr_solids": ocr_tok["solids"],
                "vision_solids": vis_tok["solids"],
            }
        )
        if "SOLID_NOTATION_CONFLICT" not in conflict_codes:
            conflict_codes.append("SOLID_NOTATION_CONFLICT")

    # 4. Relation conflict (`⊥` / `vuông góc` vs `∥` / `song song`)
    def _norm_rels(rels: Sequence[str]) -> set[str]:
        out: set[str] = set()
        for r in rels:
            if r in ("⊥", "vuông góc"):
                out.add("PERP")
            elif r in ("∥", "song song"):
                out.add("PARALLEL")
        return out

    if _norm_rels(ocr_tok["relations"]) != _norm_rels(vis_tok["relations"]):
        conflicts.append(
            {
                "code": "RELATION_SYMBOL_CONFLICT",
                "ocr_relations": ocr_tok["relations"],
                "vision_relations": vis_tok["relations"],
            }
        )
        if "RELATION_SYMBOL_CONFLICT" not in conflict_codes:
            conflict_codes.append("RELATION_SYMBOL_CONFLICT")

    # 5. Radical or fraction conflict
    if ocr_tok["radicals"] != vis_tok["radicals"] or ocr_tok["fractions"] != vis_tok["fractions"]:
        conflicts.append(
            {
                "code": "RADICAL_OR_FRACTION_CONFLICT",
                "ocr_radicals": ocr_tok["radicals"],
                "vision_radicals": vis_tok["radicals"],
                "ocr_fractions": ocr_tok["fractions"],
                "vision_fractions": vis_tok["fractions"],
            }
        )
        if "RADICAL_OR_FRACTION_CONFLICT" not in conflict_codes:
            conflict_codes.append("RADICAL_OR_FRACTION_CONFLICT")

    # 6. Angle, subscript, decimal, or sign conflict
    if (
        ocr_tok["angles_degrees"] != vis_tok["angles_degrees"]
        or ocr_tok["subscript_labels"] != vis_tok["subscript_labels"]
        or ocr_tok["decimals"] != vis_tok["decimals"]
        or ocr_tok["negatives"] != vis_tok["negatives"]
    ):
        conflicts.append(
            {
                "code": "ANGLE_OR_SIGN_CONFLICT",
                "ocr_angles": ocr_tok["angles_degrees"],
                "vision_angles": vis_tok["angles_degrees"],
                "ocr_subscripts": ocr_tok["subscript_labels"],
                "vision_subscripts": vis_tok["subscript_labels"],
                "ocr_decimals": ocr_tok["decimals"],
                "vision_decimals": vis_tok["decimals"],
                "ocr_negatives": ocr_tok["negatives"],
                "vision_negatives": vis_tok["negatives"],
            }
        )
        if "ANGLE_OR_SIGN_CONFLICT" not in conflict_codes:
            conflict_codes.append("ANGLE_OR_SIGN_CONFLICT")

    has_conflict = len(conflicts) > 0
    return {
        "has_conflict": has_conflict,
        "requires_user_confirmation": has_conflict,
        "conflict_codes": conflict_codes,
        "conflicts": conflicts,
        "ocr_tokens": ocr_tok,
        "vision_tokens": vis_tok,
    }


def route_image_or_prepare_outcome(
    prepare_outcome_dict: dict[str, Any],
    *,
    fallback_typed_fact_extractor: Extractor | None = None,
    allow_live_ai: bool | None = None,
    model: str | None = None,
    policy: RoutePolicy | None = None,
    timeout_seconds: float = 15.0,
    local_ocr_text: str | None = None,
    secondary_ocr_text: str | None = None,
    allow_verified_local_ocr: bool = False,
    has_diagram: bool = False,
    is_degraded_image: bool = False,
    is_handwritten: bool = False,
    user_confirmed_conflict: bool = False,
) -> AdaptiveRouteOutcome:
    """Route the output of `prepare_unified_input` (Image / Scanned PDF / PDF Text / DOCX) into `Route T1` (`I1`/`I2` flow).

    Supports all 4 Adaptive Vision Fallback cases (`Phase 2.6–2.7`):
    - **Case A (`LOCAL_OCR_VERIFIED_ZERO_AI`)**: When `local_ocr_text` (or dual-engine reconciled OCR text when
      `secondary_ocr_text` is provided and `not is_degraded_image`) passes `verify_ocr_input_fidelity` and
      `allow_verified_local_ocr=True`, routes directly through `Deterministic Geometry Parser -> Hybrid /4` (`0` AI calls).
    - **Case B (`VISION_THEN_LOCAL_DETERMINISTIC`)**: Local OCR fails fidelity gate -> `1` Vision call ->
      `Deterministic Geometry Parser` (`LOCAL_PARSE_COMPLETE`) -> `Hybrid /4` (`1` AI call total).
    - **Case C (`VISION_THEN_AI_FALLBACK`)**: Vision text is outside local parser grammar (`LOCAL_PARSE_PARTIAL`) ->
      `Gemini TypedFactNext` fallback (`1` Vision + `1` `TypedFactNext` call, `0` Vision re-calls).
    - **Case D (`LOCAL_AMBIGUOUS_CLARIFICATION`)**: Ambiguous or missing-data problem text -> deterministic clarification (`0` TypedFactNext calls).
    - **OCR-vs-Vision Conflict Guard (`VISION_NEEDS_CONFIRMATION`)**: When `local_ocr_text` and Vision text have a
      critical math conflict (`SA=3` vs `SA=8` or `(ABC)` vs `(A'BC)`) and `not user_confirmed_conflict`, pauses for
      explicit user confirmation instead of silently guessing.
    """
    prep_status = str(prepare_outcome_dict.get("status") or "rejected")
    source_kind = str(prepare_outcome_dict.get("source_kind") or "image")
    metrics = prepare_outcome_dict.get("metrics") or {}
    prov = prepare_outcome_dict.get("provenance") or {}
    vlm_calls = int(metrics.get("vlm_calls", 1 if prov.get("extraction_method") == "vlm" else 0))
    vision_ms = float(metrics.get("processing_ms", 0.0))

    input_kind: InputKind = (
        "pdf_text"
        if source_kind == "pdf" and vlm_calls == 0
        else ("pdf_scan" if source_kind == "pdf" else ("docx" if source_kind == "docx" else "image"))
    )

    eff_has_diagram = bool(
        has_diagram
        or prepare_outcome_dict.get("has_figure")
        or any(
            isinstance(c, dict) and c.get("has_figure")
            for c in (prepare_outcome_dict.get("candidates") or ())
        )
    )

    # Case A: Check if Local OCR passes the 6-criteria Input Fidelity Gate (`0` Vision calls)
    fidelity_report: dict[str, Any] | None = None
    effective_ocr_text = local_ocr_text
    if local_ocr_text is not None:
        fidelity_report = verify_ocr_input_fidelity(
            local_ocr_text,
            secondary_ocr_text=secondary_ocr_text,
            has_diagram=eff_has_diagram,
            is_degraded_image=is_degraded_image,
            is_handwritten=is_handwritten,
        )
        if (
            not fidelity_report["fidelity_passed"]
            and secondary_ocr_text is not None
            and not is_degraded_image
            and not eff_has_diagram
            and not is_handwritten
        ):
            reconcile_res = reconcile_dual_ocr_texts(
                local_ocr_text,
                secondary_ocr_text,
                has_diagram=eff_has_diagram,
                is_degraded_image=is_degraded_image,
                is_handwritten=is_handwritten,
            )
            if reconcile_res["reconciled"] and reconcile_res["reconciled_text"]:
                effective_ocr_text = reconcile_res["reconciled_text"]
                fidelity_report = dict(reconcile_res["fidelity_report"])
                fidelity_report["dual_ocr_reconciliation"] = {
                    "reconciled": True,
                    "repairs": reconcile_res["repairs"],
                    "used_ground_truth": False,
                }
        if allow_verified_local_ocr and fidelity_report["fidelity_passed"] and effective_ocr_text is not None:
            outcome_a = route_text_input(
                effective_ocr_text,
                fallback_extractor=fallback_typed_fact_extractor,
                allow_live_ai=allow_live_ai,
                input_kind=input_kind,
                previous_vision_calls=0,
                previous_vision_ms=0.0,
                model=model,
                policy=policy,
                timeout_seconds=timeout_seconds,
            )
            meta_a = {
                **outcome_a.telemetry.cache_key_metadata,
                "ocr_fidelity_gate": "PASSED",
                "ocr_failed_checks": [],
            }
            tel_a = AdaptiveRouteTelemetry(
                router_version=outcome_a.telemetry.router_version,
                parser_version=outcome_a.telemetry.parser_version,
                input_kind=input_kind,
                local_parse_status=outcome_a.telemetry.local_parse_status,
                chosen_route="LOCAL_OCR_VERIFIED_ZERO_AI",
                fallback_reason=None,
                gemini_vision_calls=0,
                gemini_typed_fact_calls=0,
                total_provider_calls=0,
                local_parse_ms=outcome_a.telemetry.local_parse_ms,
                vision_ms=0.0,
                typed_fact_ai_ms=0.0,
                hybrid_execution_ms=outcome_a.telemetry.hybrid_execution_ms,
                total_ms=outcome_a.telemetry.total_ms,
                source_coverage=outcome_a.telemetry.source_coverage,
                cache_key_metadata=meta_a,
            )
            resp_a = dict(outcome_a.response)
            rd_a = dict(resp_a.get("route_d") or {})
            rd_a["adaptive_telemetry"] = tel_a.to_dict()
            rd_a["ocr_fidelity_report"] = fidelity_report
            resp_a["route_d"] = rd_a
            rec_a = {
                **outcome_a.receipt,
                "adaptive_telemetry": tel_a.to_dict(),
                "ocr_fidelity_report": fidelity_report,
            }
            return AdaptiveRouteOutcome(
                status=outcome_a.status,
                response=resp_a,
                receipt=rec_a,
                telemetry=tel_a,
                local_parse_result=outcome_a.local_parse_result,
                cache_key=outcome_a.cache_key,
            )

    if prep_status != "ready":
        chosen: ChosenRoute = (
            "VISION_NEEDS_CONFIRMATION" if prep_status == "needs_confirmation" else "LOCAL_CV_REJECTED_OR_SELECTION"
        )
        tel = AdaptiveRouteTelemetry(
            router_version=ADAPTIVE_INPUT_ROUTER_VERSION,
            parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
            input_kind=input_kind,
            local_parse_status="NOT_RUN",
            chosen_route=chosen,
            fallback_reason=prepare_outcome_dict.get("reason_code"),
            gemini_vision_calls=vlm_calls,
            gemini_typed_fact_calls=0,
            total_provider_calls=vlm_calls,
            local_parse_ms=0.0,
            vision_ms=vision_ms,
            typed_fact_ai_ms=0.0,
            hybrid_execution_ms=0.0,
            total_ms=vision_ms,
            source_coverage={},
            cache_key_metadata={"prepare_status": prep_status, "source_kind": source_kind},
        )
        return AdaptiveRouteOutcome(
            status=prep_status.upper(),
            response={"prepare_outcome": prepare_outcome_dict, "adaptive_telemetry": tel.to_dict()},
            receipt={"schema": "adaptive-input-route-receipt/1", "status": prep_status.upper(), "adaptive_telemetry": tel.to_dict()},
            telemetry=tel,
            local_parse_result=None,
            cache_key=None,
        )

    problem_text = str(prepare_outcome_dict.get("problem_text") or "")

    # Phase 2.7: Conflict check between Local OCR and Vision when both exist and local OCR had a valid structure
    # (Only trigger conflict confirmation when Local OCR was structurally clean enough to compete on math tokens,
    # or when an explicit numeric/plane conflict is detected and not yet confirmed by the user).
    if local_ocr_text is not None and vlm_calls > 0 and not user_confirmed_conflict:
        conflict_report = compare_ocr_and_vision_facts(local_ocr_text, problem_text)
        # Note: if local OCR failed fidelity due to obvious OCR corruption artifacts (`2V3`, `Œ`), Vision is authoritative;
        # if local OCR had clean syntax on a competing numeric value (`SA=3` vs `SA=8`) or plane (`(ABC)` vs `(A'BC)`),
        # require user confirmation!
        ocr_has_corrupt_artifact = bool(
            is_handwritten or _OCR_CORRUPTION_ARTIFACT_RE.search(local_ocr_text)
        )
        if conflict_report["has_conflict"] and not ocr_has_corrupt_artifact:
            tel_c = AdaptiveRouteTelemetry(
                router_version=ADAPTIVE_INPUT_ROUTER_VERSION,
                parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
                input_kind=input_kind,
                local_parse_status=fidelity_report["local_parse_status"] if fidelity_report else "CONFLICT",
                chosen_route="VISION_NEEDS_CONFIRMATION",
                fallback_reason="OCR_VISION_MATH_CONFLICT",
                gemini_vision_calls=vlm_calls,
                gemini_typed_fact_calls=0,
                total_provider_calls=vlm_calls,
                local_parse_ms=0.0,
                vision_ms=vision_ms,
                typed_fact_ai_ms=0.0,
                hybrid_execution_ms=0.0,
                total_ms=vision_ms,
                source_coverage={},
                cache_key_metadata={
                    "prepare_status": "needs_confirmation",
                    "conflict_codes": conflict_report["conflict_codes"],
                },
            )
            return AdaptiveRouteOutcome(
                status="NEEDS_CONFIRMATION",
                response={
                    "status": "needs_confirmation",
                    "reason_code": "OCR_VISION_MATH_CONFLICT",
                    "ocr_text": local_ocr_text,
                    "vision_text": problem_text,
                    "conflict_report": conflict_report,
                    "adaptive_telemetry": tel_c.to_dict(),
                },
                receipt={
                    "schema": "adaptive-input-route-receipt/1",
                    "status": "NEEDS_CONFIRMATION",
                    "code": "OCR_VISION_MATH_CONFLICT",
                    "conflict_report": conflict_report,
                    "adaptive_telemetry": tel_c.to_dict(),
                },
                telemetry=tel_c,
                local_parse_result=None,
                cache_key=None,
            )

    return route_text_input(
        problem_text,
        fallback_extractor=fallback_typed_fact_extractor,
        allow_live_ai=allow_live_ai,
        input_kind=input_kind,
        previous_vision_calls=vlm_calls,
        previous_vision_ms=vision_ms,
        model=model,
        policy=policy,
        timeout_seconds=timeout_seconds,
    )


def evaluate_local_ocr_gate(
    primary_ocr_text: str,
    secondary_ocr_text: str | None = None,
    *,
    reference_math_tokens: Sequence[str] | None = None,
    has_diagram: bool = False,
    is_degraded_image: bool = False,
    is_handwritten: bool = False,
) -> dict[str, Any]:
    """Evaluate the `I2` Local OCR acceptance gate (`LOCAL_OCR_DIAGNOSTIC_ONLY` by default).

    Strict requirements before any Local OCR text could bypass Vision:
    1. Both primary (`tesseract`) and secondary (`vietocr`) texts must be non-empty.
    2. Extracted math symbol & notation tokens (`⊥, ∥, √, ′, S.ABCD, A', = value`) must agree 100% between engines.
    3. If `reference_math_tokens` are provided (benchmark mode), 100% of reference math tokens must be preserved.
    4. Even if synthetically clean, `production_status` remains `LOCAL_OCR_DIAGNOSTIC_ONLY` unless explicitly enabled.
    """
    p_norm = normalize_problem_text(primary_ocr_text or "")
    s_norm = normalize_problem_text(secondary_ocr_text or "") if secondary_ocr_text is not None else ""
    p_tokens = sorted(set(_MATH_TOKEN_GATE_RE.findall(p_norm)))
    s_tokens = sorted(set(_MATH_TOKEN_GATE_RE.findall(s_norm))) if s_norm else []

    cross_engine_agree = bool(p_norm and s_norm and p_tokens == s_tokens and len(p_tokens) >= 2)
    ref_recall_ok = True
    if reference_math_tokens is not None:
        ref_set = {normalize_problem_text(t) for t in reference_math_tokens if t}
        ref_recall_ok = ref_set.issubset(set(p_tokens))

    fidelity = verify_ocr_input_fidelity(
        primary_ocr_text,
        secondary_ocr_text=secondary_ocr_text,
        has_diagram=has_diagram,
        is_degraded_image=is_degraded_image,
        is_handwritten=is_handwritten,
    )
    parse_complete = bool(fidelity["fidelity_passed"])

    gate_passed = bool(cross_engine_agree and ref_recall_ok and parse_complete)
    return {
        "production_status": LOCAL_OCR_PRODUCTION_STATUS,
        "gate_passed": gate_passed,
        "cross_engine_math_tokens_agree": cross_engine_agree,
        "reference_math_tokens_preserved": ref_recall_ok,
        "local_parser_complete": parse_complete,
        "fidelity_checks": fidelity["checks"],
        "failed_fidelity_checks": fidelity["failed_checks"],
        "primary_math_tokens": p_tokens,
        "secondary_math_tokens": s_tokens,
        "local_parse_status": fidelity["local_parse_status"],
    }


def is_local_parse_semantically_complete(local_res: LocalParseResult) -> bool:
    """True when Local Parser resolved every sentence/clause and produced a validated TypedFactNext payload."""
    return (
        local_res.status == LOCAL_PARSE_COMPLETE
        and local_res.payload is not None
        and bool(local_res.source_coverage.coverage_complete)
    )


def route_text_input_local_slm(
    problem_text: str,
    *,
    model_key: str | None = None,
    strategy: str | None = None,
    runtime: Any = None,
    allow_download: bool = False,
    input_kind: InputKind = "text",
    previous_vision_calls: int = 0,
    previous_vision_ms: float = 0.0,
    policy: RoutePolicy | None = None,
    timeout_seconds: float = 30.0,
) -> AdaptiveRouteOutcome:
    """Local-first router with local sub-1B SLM fallback (`external_ai_calls = 0`).

    1. Runs deterministic Local Parser (`route_text_input(..., allow_live_ai=False)`).
    2. Only invokes local CPU SLM when deterministic parsing cannot complete safely
       (`chosen_route == "FAIL_CLOSED_LIVE_AI_DISABLED"`).
    3. Validates SLM extraction through Source Grounding (`slm-grounding-validator/1`)
       and feeds ONLY grounded `TypedFactNext /2` facts into Hybrid `/4`.
    """
    from app.ai.local_slm_extractor import (
        LOCAL_SLM_EXTRACTOR_VERSION,
        resolve_local_slm_strategy,
        run_local_slm_extraction,
    )
    from app.ai.local_slm_runtime import (
        LOCAL_SLM_RUNTIME_VERSION,
        LocalSlmRuntimeError,
        resolve_local_slm_model_spec,
    )

    spec = resolve_local_slm_model_spec(model_key)
    eff_strategy = resolve_local_slm_strategy(strategy)
    eff_policy = policy or hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})

    t0 = time.perf_counter()
    det = route_text_input(
        problem_text,
        allow_live_ai=False,
        input_kind=input_kind,
        previous_vision_calls=previous_vision_calls,
        previous_vision_ms=previous_vision_ms,
        model=f"local-slm:{spec.model_key}",
        policy=eff_policy,
        timeout_seconds=timeout_seconds,
    )
    if det.telemetry.chosen_route != "FAIL_CLOSED_LIVE_AI_DISABLED":
        return det

    local_res = det.local_parse_result
    assert local_res is not None
    norm_text = local_res.payload["problem_text"] if local_res.payload else normalize_problem_text(
        strip_trailing_multiple_choice_options(problem_text)
    )
    local_ms = det.telemetry.local_parse_ms
    cov_dict = local_res.source_coverage.to_dict()

    try:
        slm_res = run_local_slm_extraction(
            norm_text,
            model_key=spec.model_key,
            strategy=eff_strategy,
            runtime=runtime,
            allow_download=allow_download,
        )
    except LocalSlmRuntimeError as exc:
        total_ms = (time.perf_counter() - t0) * 1000.0 + previous_vision_ms
        _, cache_meta = build_local_first_cache_identity(
            norm_text,
            extraction_route="LOCAL_SLM_INFRA_ERROR",
            model=spec.model_key,
            local_parse_status=local_res.status,
        )
        tel_err = AdaptiveRouteTelemetry(
            router_version=ADAPTIVE_INPUT_ROUTER_VERSION,
            parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
            input_kind=input_kind,
            local_parse_status=local_res.status,
            chosen_route="LOCAL_SLM_FALLBACK",
            fallback_reason=local_res.fallback_reason or local_res.reason_code,
            gemini_vision_calls=previous_vision_calls,
            gemini_typed_fact_calls=0,
            total_provider_calls=previous_vision_calls,
            local_parse_ms=local_ms,
            vision_ms=previous_vision_ms,
            typed_fact_ai_ms=0.0,
            hybrid_execution_ms=0.0,
            total_ms=total_ms,
            source_coverage=cov_dict,
            cache_key_metadata=cache_meta,
        )
        resp_err = {
            "schema_version": ROUTE_D_SIMULATION_V4_SCHEMA_VERSION,
            "route_d": {
                "status": "REFUSED",
                "adapter_version": ADAPTER_V4_VERSION,
                "schema_version": ROUTE_D_SIMULATION_V4_SCHEMA_VERSION,
                "extraction_mode": "LOCAL_SLM_INFRA_ERROR",
                "local_parser_version": LOCAL_GEOMETRY_PARSER_VERSION,
                "adaptive_router_version": ADAPTIVE_INPUT_ROUTER_VERSION,
                "adaptive_telemetry": tel_err.to_dict(),
                "refusal": {"code": exc.reason_code, "reason_code": exc.reason_code},
            },
            "envelope": {
                "status": "refused",
                "reason_code": exc.reason_code,
                "failure_kind": "INFRASTRUCTURE_FAILURE",
            },
        }
        rec_err = {
            "schema": "adaptive-input-route-receipt/1",
            "status": "REFUSED",
            "code": exc.reason_code,
            "failure_kind": "TECHNICAL_FAILURE",
            "adaptive_telemetry": tel_err.to_dict(),
        }
        return AdaptiveRouteOutcome(
            status="REFUSED",
            response=resp_err,
            receipt=rec_err,
            telemetry=tel_err,
            local_parse_result=local_res,
            cache_key=None,
        )

    slm_ms = float(slm_res.inference.inference_time_ms if slm_res.inference else 0.0)
    slm_id = {
        "route": "HYBRID_V5_LOCAL_SLM",
        "router_version": ADAPTIVE_INPUT_ROUTER_VERSION,
        "parser_version": LOCAL_GEOMETRY_PARSER_VERSION,
        "runtime_version": LOCAL_SLM_RUNTIME_VERSION,
        "extractor_version": LOCAL_SLM_EXTRACTOR_VERSION,
        "model_key": slm_res.model_key,
        "model_sha256": slm_res.model_sha256,
        "strategy": slm_res.strategy,
        "source": slm_res.norm_text,
    }
    slm_cache_key = sha256(json.dumps(slm_id, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

    if not slm_res.ok or slm_res.canonical_payload is None:
        total_ms = (time.perf_counter() - t0) * 1000.0 + previous_vision_ms
        fail_code = slm_res.reason_code or "AMBIGUOUS_FACT"
        tel_ref = AdaptiveRouteTelemetry(
            router_version=ADAPTIVE_INPUT_ROUTER_VERSION,
            parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
            input_kind=input_kind,
            local_parse_status=local_res.status,
            chosen_route="LOCAL_SLM_FALLBACK",
            fallback_reason=local_res.fallback_reason or local_res.reason_code,
            gemini_vision_calls=previous_vision_calls,
            gemini_typed_fact_calls=0,
            total_provider_calls=previous_vision_calls,
            local_parse_ms=local_ms,
            vision_ms=previous_vision_ms,
            typed_fact_ai_ms=slm_ms,
            hybrid_execution_ms=0.0,
            total_ms=total_ms,
            source_coverage=cov_dict,
            cache_key_metadata=slm_id,
        )
        resp_ref = {
            "schema_version": ROUTE_D_SIMULATION_V4_SCHEMA_VERSION,
            "route_d": {
                "status": "REFUSED",
                "adapter_version": ADAPTER_V4_VERSION,
                "schema_version": ROUTE_D_SIMULATION_V4_SCHEMA_VERSION,
                "extraction_mode": "LOCAL_SLM_GROUNDING_REJECTED",
                "local_parser_version": LOCAL_GEOMETRY_PARSER_VERSION,
                "adaptive_router_version": ADAPTIVE_INPUT_ROUTER_VERSION,
                "adaptive_telemetry": tel_ref.to_dict(),
                "slm_grounding_envelope": slm_res.grounding_envelope,
                "refusal": {
                    "code": fail_code,
                    "reason_code": fail_code,
                    "failure_taxonomy": slm_res.failure_taxonomy,
                },
            },
            "envelope": {
                "status": "refused",
                "reason_code": fail_code,
                "failure_kind": "EXTRACTION_FALLBACK_REQUIRED",
            },
        }
        rec_ref = {
            "schema": "adaptive-input-route-receipt/1",
            "status": "REFUSED",
            "code": fail_code,
            "failure_kind": "EXTRACTION_FAILURE",
            "adaptive_telemetry": tel_ref.to_dict(),
            "slm_grounding_envelope": slm_res.grounding_envelope,
        }
        return AdaptiveRouteOutcome(
            status="REFUSED",
            response=resp_ref,
            receipt=rec_ref,
            telemetry=tel_ref,
            local_parse_result=local_res,
            cache_key=None,
        )

    t_hyb0 = time.perf_counter()
    hyb_out = run_hybrid_offline(
        slm_res.norm_text,
        ReplayExtractor({slm_res.norm_text: slm_res.canonical_payload}),
        policy=eff_policy,
        timeout_seconds=timeout_seconds,
    )
    hyb_exec_ms = (time.perf_counter() - t_hyb0) * 1000.0
    total_ms = (time.perf_counter() - t0) * 1000.0 + previous_vision_ms

    tel_ok = AdaptiveRouteTelemetry(
        router_version=ADAPTIVE_INPUT_ROUTER_VERSION,
        parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
        input_kind=input_kind,
        local_parse_status=local_res.status,
        chosen_route="LOCAL_SLM_FALLBACK",
        fallback_reason=local_res.fallback_reason or local_res.reason_code,
        gemini_vision_calls=previous_vision_calls,
        gemini_typed_fact_calls=0,
        total_provider_calls=previous_vision_calls,
        local_parse_ms=local_ms,
        vision_ms=previous_vision_ms,
        typed_fact_ai_ms=slm_ms,
        hybrid_execution_ms=hyb_exec_ms,
        total_ms=total_ms,
        source_coverage=cov_dict,
        cache_key_metadata=slm_id,
    )
    resp_ok = dict(hyb_out.response)
    route_d = dict(resp_ok.get("route_d") or {})
    route_d["extraction_mode"] = "LOCAL_SLM_GROUNDED"
    route_d["local_parser_version"] = LOCAL_GEOMETRY_PARSER_VERSION
    route_d["adaptive_router_version"] = ADAPTIVE_INPUT_ROUTER_VERSION
    route_d["adaptive_telemetry"] = tel_ok.to_dict()
    route_d["slm_grounding_envelope"] = slm_res.grounding_envelope
    resp_ok["route_d"] = route_d
    rec_ok = {
        **hyb_out.receipt,
        "adaptive_telemetry": tel_ok.to_dict(),
        "slm_grounding_envelope": slm_res.grounding_envelope,
    }
    status_str = str(route_d.get("status") or "REFUSED")
    return AdaptiveRouteOutcome(
        status=status_str,
        response=resp_ok,
        receipt=rec_ok,
        telemetry=tel_ok,
        local_parse_result=local_res,
        cache_key=slm_cache_key if status_str == "SERVED" else None,
    )
