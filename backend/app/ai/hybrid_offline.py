"""Internal opt-in Hybrid integration. No cache, live transport or automatic fallback.

The source-only injected extractor is trusted local code, not client-supplied code. The deadline/cancellation policy
is cooperative between synchronous stages; a future live transport needs its own bounded I/O timeout.

Migration Stage 2 (run `scene3d-to-hybrid-v2-replacement`): `run_local_replay` is reachable from `/api/analyze` only
when the server sets `HYBRID_V2_LOCAL=offline-replay` and the client is loopback (`main._hybrid_v2_local`). The default
route stays `LLM_ONLY`; nothing is cached; a Hybrid refusal is returned as a refusal, never re-run on `LLM_ONLY`.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import math
from pathlib import Path
from time import perf_counter
from typing import Callable
from uuid import uuid4

from app.ai.adapter4_route import (
    ADAPTER_V4_VERSION, ROUTE_D_SIMULATION_V4_SCHEMA_VERSION,
    build_adapter4_response, run_typed_fact_next_v2_route,
)
from app.ai.pipeline import RoutePolicy, route_policy_snapshot
from app.ai.typed_fact_next_extraction import Extractor, ReplayExtractor, extract_typed_fact_next_v2
from app.ingestion.input import MAX_TEXT_CHARS
from app.simulation.geometry_functions import KetQuaTuyen
from app.simulation.geometry_functions.typed_fact_next import TYPED_FACT_NEXT_V2_SCHEMA_VERSION


def _surface() -> dict[str, str]:
    from app.simulation.geometry_functions import engine, planner, registry

    return {
        'registry_version': registry.REGISTRY_VERSION, 'planner_version': planner.PLANNER_VERSION,
        'engine_version': engine.ENGINE_VERSION, 'response_contract': TYPED_FACT_NEXT_V2_SCHEMA_VERSION,
        'adapter_version': ADAPTER_V4_VERSION, 'envelope_version': ROUTE_D_SIMULATION_V4_SCHEMA_VERSION,
        'provider_mode': 'INJECTED_OFFLINE_EXTRACTOR',
    }


def hybrid_offline_policy(env: dict[str, str] | None = None) -> RoutePolicy:
    """Use the existing server-side research flag and immutable RoutePolicy, with this route's actual identities.

    No new runtime mode is registered. Preview policies are already excluded from the product cache by main.
    This helper grants no HTTP authorization and leaves the default pipeline's flat policy unchanged.
    """
    base = route_policy_snapshot(env, preview=True)
    return replace(base, response_contract=TYPED_FACT_NEXT_V2_SCHEMA_VERSION,
                   preview_surface=tuple(sorted(_surface().items())))


@dataclass(frozen=True)
class HybridOfflineResult:
    response: dict
    receipt: dict


def run_hybrid_offline(problem_text: str, extractor: Extractor, *, policy: RoutePolicy | None = None,
                       timeout_seconds: float = 15.0,
                       cancelled: Callable[[], bool] | None = None) -> HybridOfflineResult:
    """Verbatim source -> V2 extraction -> existing /4 deterministic route -> validated product wrapper.

    Callers must explicitly supply an enabled research policy. Environment flags alone do not activate a call.
    Receipts exclude source text, decoded extraction, exception prose and provider bodies. Source/Planner/Engine timing
    stays combined because the existing route owns their execution; individual latency values are not invented.
    """
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) \
            or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError('timeout_seconds must be finite and positive')
    start = perf_counter()
    policy = policy if policy is not None else route_policy_snapshot()
    source = problem_text if isinstance(problem_text, str) else ''
    receipt = {
        'schema': 'hybrid-offline-execution/1', 'request_id': uuid4().hex,
        'classification': 'OFFLINE_INTEGRATION_NOT_LIVE_NLU_EVALUATION',
        'source_sha256': sha256(source.encode('utf-8')).hexdigest(),
        'policy_fingerprint': policy.fingerprint(), 'runtime_identity': dict(policy.preview_surface),
        'provider_performance': 'NOT_MEASURED', 'cache': 'NOT_USED',
        'stages': [], 'source_gate': {'status': 'NOT_CERTIFIED'},
        'planner': {'status': 'NOT_CERTIFIED'}, 'engine': {'status': 'NOT_CERTIFIED'},
        'failure_stage': None, 'failure_kind': None,
        'individual_source_gate_planner_engine_latency': 'UNKNOWN_NOT_INSTRUMENTED',
    }

    def finish(result: KetQuaTuyen, failure_stage: str | None = None,
               failure_kind: str | None = None) -> HybridOfflineResult:
        response = build_adapter4_response(result, source)
        code = response['envelope'].get('reason_code')
        receipt.update(status=response['route_d']['status'], code=code,
                       failure_stage=failure_stage, failure_kind=failure_kind,
                       offline_seconds=max(0.0, perf_counter() - start))
        if result.status == 'SERVED' and response['route_d']['status'] != 'SERVED':
            receipt.update(failure_stage='adapter4', failure_kind='SCENE_VALIDATION_FAILURE')
        return HybridOfflineResult(response, receipt)

    def refuse(code: str, stage: str, kind: str) -> HybridOfflineResult:
        return finish(KetQuaTuyen('REFUSED', code), stage, kind)

    def interruption(stage: str) -> HybridOfflineResult | None:
        if cancelled is not None and cancelled():
            return refuse('HYBRID_CANCELLED', stage, 'TECHNICAL_FAILURE')
        if perf_counter() - start >= timeout_seconds:
            return refuse('HYBRID_DEADLINE_EXCEEDED', stage, 'TECHNICAL_FAILURE')
        if dict(policy.preview_surface) != _surface() or policy.response_contract != TYPED_FACT_NEXT_V2_SCHEMA_VERSION:
            return refuse('PREVIEW_IDENTITY_CHANGED', stage, 'INTEGRITY')
        return None

    if not policy.hybrid_preview_enabled:
        return refuse('PREVIEW_DISABLED', 'policy', 'DISABLED')
    stopped = interruption('policy')
    if stopped is not None:
        return stopped
    if not source.strip() or len(source) > MAX_TEXT_CHARS:
        return refuse('FACT_INCOMPLETE', 'input', 'EXTRACTION_FAILURE')

    before = perf_counter()
    extraction = extract_typed_fact_next_v2(source, extractor)
    receipt['stages'].append({'name': 'extraction', 'seconds': max(0.0, perf_counter() - before),
                              'code': extraction.code, 'validation': extraction.diagnostics})
    stopped = interruption('extraction')
    if stopped is not None:
        return stopped
    if extraction.payload is None:
        code = extraction.code or 'INVALID_TYPED_FACT_NEXT'
        technical_codes = {'EXTRACTOR_INTERNAL_ERROR', 'PROVIDER_ERROR', 'PROVIDER_RESPONSE_INVALID',
                           'PROVIDER_BLOCKED', 'PROVIDER_REFUSED', 'NO_CANDIDATE', 'MALFORMED_RESPONSE_PART',
                           'JSON_INVALID', 'RESPONSE_TRUNCATED', 'MAX_TOKENS'}
        kind = 'TECHNICAL_FAILURE' if code in technical_codes else 'EXTRACTION_FAILURE'
        return refuse(code, 'extraction', kind)

    before = perf_counter()
    result = run_typed_fact_next_v2_route(extraction.payload)
    receipt['stages'].append({'name': 'source_gate_planner_exact_engine',
                              'seconds': max(0.0, perf_counter() - before), 'code': result.code})
    stopped = interruption('deterministic_route')
    if stopped is not None:
        return stopped
    if result.status == 'SERVED':
        receipt['source_gate'] = {'status': 'VERIFIED', 'authority': 'registry.kiem_nguon'}
        receipt['planner'] = {'status': 'EXECUTED', 'version': result.planner.get('version')}
        receipt['engine'] = {'status': 'VERIFIED', 'kernel_check': result.kernel_check}
    before = perf_counter()
    outcome = finish(result)
    receipt['stages'].append({'name': 'adapter4', 'seconds': max(0.0, perf_counter() - before),
                              'code': outcome.response['envelope'].get('reason_code')})
    if result.status != 'SERVED':
        from app.ai.hybrid_preview import classify_refusal

        technical = (result.code or '').endswith('_INTERNAL_ERROR') or result.code in {
            'ENGINE_EXECUTION_FAILED', 'ENGINE_SELF_CHECK_FAILED', 'ENGINE_IR_INVALID', 'SCENE_BUILD_FAILED',
            'SECTION_CONSTRUCTION_INTERNAL_FAILURE'}
        receipt.update(failure_stage='deterministic_route',
                       failure_kind='TECHNICAL_FAILURE' if technical else classify_refusal(result.code or '').group)
    stopped = interruption('adapter4')
    return stopped if stopped is not None else outcome


#: Schema of the authored replay corpus file `run_local_replay` reads (`scripts/export_hybrid_v2_local_corpus.py`).
LOCAL_REPLAY_SCHEMA = 'hybrid-v2-local-replay-corpus/1'


def run_local_replay(problem_text: str, corpus_path: str) -> HybridOfflineResult:
    """Stage 2 opt-in local route: verbatim source → recorded `typed-fact-next/2` (authored replay corpus, keyed by the
    exact problem text) → the same validation, Source Gate, planner, exact engine and /4 wrapper as `run_hybrid_offline`.

    A text the corpus does not hold is refused `NO_RECORDED_EXTRACTION` — the offline mode has no language
    understanding, so it never guesses. An unreadable or foreign corpus file is an empty corpus, not an error page."""
    try:
        data = json.loads(Path(corpus_path).read_text(encoding='utf-8'))
        outputs = data['outputs'] if data.get('schema') == LOCAL_REPLAY_SCHEMA and isinstance(data['outputs'], dict) \
            else {}
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        outputs = {}
    policy = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})
    return run_hybrid_offline(problem_text, ReplayExtractor(outputs), policy=policy)
