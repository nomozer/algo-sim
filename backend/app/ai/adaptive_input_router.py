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

from dataclasses import dataclass, field
from hashlib import sha256
import json
import os
import re
import time
from typing import Any, Callable, Literal

from app.ai.adapter4_route import ADAPTER_V4_VERSION, ROUTE_D_SIMULATION_V4_SCHEMA_VERSION
from app.ai.hybrid_offline import HybridOfflineResult, hybrid_offline_policy, run_hybrid_offline
from app.ai.local_geometry_parser import (
    LOCAL_GEOMETRY_PARSER_VERSION,
    LOCAL_PARSE_AMBIGUOUS,
    LOCAL_PARSE_COMPLETE,
    LOCAL_PARSE_PARTIAL,
    LOCAL_PARSE_UNSUPPORTED,
    LocalParseResult,
    normalize_problem_text,
    parse_geometry_problem_locally,
)
from app.ai.route_policy import RoutePolicy
from app.ai.typed_fact_next_extraction import (
    Extractor,
    LiveAIDisabled,
    ReplayExtractor,
)
from app.simulation.error_codes import ErrorCode
from app.simulation.geometry_functions import engine, planner, registry
from app.simulation.geometry_functions.typed_fact_next import TYPED_FACT_NEXT_V2_SCHEMA_VERSION

ADAPTIVE_INPUT_ROUTER_VERSION = "adaptive-input-router/1"
LOCAL_OCR_PRODUCTION_STATUS = "LOCAL_OCR_DIAGNOSTIC_ONLY"

InputKind = Literal["text", "pdf_text", "docx", "image", "pdf_scan", "user_edited_text"]

ChosenRoute = Literal[
    "LOCAL_DETERMINISTIC_HYBRID",
    "LOCAL_AMBIGUOUS_CLARIFICATION",
    "LOCAL_OUT_OF_SCOPE_GATE",
    "AI_TYPED_FACT_FALLBACK",
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


def route_text_input(
    problem_text: str,
    *,
    fallback_extractor: Extractor | None = None,
    allow_live_ai: bool | None = None,
    input_kind: InputKind = "text",
    previous_vision_calls: int = 0,
    previous_vision_ms: float = 0.0,
    model: str | None = None,
    policy: RoutePolicy | None = None,
    timeout_seconds: float = 15.0,
) -> AdaptiveRouteOutcome:
    """Route a Vietnamese problem text (`T1` or post-Vision `I1` / user-edited text) local-first into Hybrid `/4`."""
    t_total0 = time.perf_counter()
    norm_text = normalize_problem_text(problem_text)
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

        chosen_route: ChosenRoute = (
            "VISION_THEN_LOCAL_DETERMINISTIC"
            if previous_vision_calls > 0
            else (
                "LOCAL_AMBIGUOUS_CLARIFICATION"
                if local_res.status == LOCAL_PARSE_AMBIGUOUS
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
        route_d = dict(response.get("route_d") or {})
        route_d["extraction_mode"] = "LOCAL_DETERMINISTIC_PARSER"
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
    fail_code = "LIVE_AI_DISABLED" if not is_fallback_allowed else (local_res.reason_code or "LOCAL_PARSE_FALLBACK_REQUIRED")
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
        },
        "envelope": {
            "status": "refused",
            "reason_code": fail_code,
            "failure_kind": "INFRASTRUCTURE_FAILURE" if fail_code == "LIVE_AI_DISABLED" else "EXTRACTION_FALLBACK_REQUIRED",
        },
    }
    receipt = {
        "schema": "adaptive-input-route-receipt/1",
        "status": "REFUSED",
        "code": fail_code,
        "failure_kind": "TECHNICAL_FAILURE" if fail_code == "LIVE_AI_DISABLED" else "EXTRACTION_FAILURE",
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


def route_image_or_prepare_outcome(
    prepare_outcome_dict: dict[str, Any],
    *,
    fallback_typed_fact_extractor: Extractor | None = None,
    allow_live_ai: bool | None = None,
    model: str | None = None,
    policy: RoutePolicy | None = None,
    timeout_seconds: float = 15.0,
) -> AdaptiveRouteOutcome:
    """Route the output of `prepare_unified_input` (Image / Scanned PDF / PDF Text / DOCX) into `Route T1` (`I1` flow).

    - If `prepare_outcome_dict["status"] != "ready"` (e.g. `rejected`, `needs_selection`, `needs_confirmation`):
      returns immediately with `0` `TypedFactNext` calls.
    - If `prepare_outcome_dict["status"] == "ready"`:
      runs `route_text_input` on `prepare_outcome_dict["problem_text"]`, charging `1` Vision call (if Vision was used)
      + `0` `TypedFactNext` calls when `Deterministic Geometry Parser` succeeds (`1` total AI call instead of `2`).
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


_MATH_TOKEN_GATE_RE = re.compile(
    r"(?:⊥|∥|√\d+|∠|△|[A-Z][0-9']*'[0-9']*(?:\.[A-Z0-9']+)?|[A-Z]\.[A-Z]{3,6}|=\s*\d+(?:√\d+)?(?:/\d+)?|\d+°)"
)


def evaluate_local_ocr_gate(
    primary_ocr_text: str,
    secondary_ocr_text: str | None = None,
    *,
    reference_math_tokens: Sequence[str] | None = None,
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

    # Check if local parser can parse `p_norm` with complete coverage
    local_parse = parse_geometry_problem_locally(p_norm) if p_norm else None
    parse_complete = bool(local_parse and local_parse.status == LOCAL_PARSE_COMPLETE)

    gate_passed = bool(cross_engine_agree and ref_recall_ok and parse_complete)
    return {
        "production_status": LOCAL_OCR_PRODUCTION_STATUS,
        "gate_passed": gate_passed,
        "cross_engine_math_tokens_agree": cross_engine_agree,
        "reference_math_tokens_preserved": ref_recall_ok,
        "local_parser_complete": parse_complete,
        "primary_math_tokens": p_tokens,
        "secondary_math_tokens": s_tokens,
        "local_parse_status": local_parse.status if local_parse else "EMPTY",
    }
