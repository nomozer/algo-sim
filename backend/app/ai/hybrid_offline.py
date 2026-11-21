"""Official Hybrid `/4` execution orchestrator (`live` default and `staging-replay` development/test replay).

`POST /api/analyze` routes through `prepare_live_hybrid` (`HYBRID_ROUTE_MODE=live`, default) or `prepare_staging_replay`
(`HYBRID_ROUTE_MODE=staging-replay`). There is no fallback to any legacy `LLM_ONLY` pipeline. Only SERVED results are
cached by `main` under `ROUTE_D_CACHE_POLICY` (`prepare_live_hybrid(...).cache_key` / `prepare_staging_replay(...).cache_key`).
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import time
from time import perf_counter
from typing import Any, Callable, Mapping
from uuid import uuid4

from app.ai import typed_fact_next_extraction as _tfn_extraction
from app.ai.adapter4_route import (
    ADAPTER_V4_VERSION, ROUTE_D_SIMULATION_V4_SCHEMA_VERSION,
    adapter_fault_response, build_adapter4_response, run_typed_fact_next_v2_route,
)
from app.ai.route_policy import RoutePolicy, route_policy_snapshot
from app.ai.typed_fact_next_extraction import (
    Extractor, ReplayExtractor, TransportExtractor, extract_typed_fact_next_v2,
)
from app.ingestion.input import MAX_TEXT_CHARS
from app.simulation.geometry_functions import KetQuaTuyen
from app.simulation.geometry_functions.typed_fact_next import TYPED_FACT_NEXT_V2_SCHEMA_VERSION


#: Provider, transport, schema-framing and internal technical fault codes on the Hybrid `/4` route.
#: Surfaced as recoverable HTTP infrastructure errors (`502`/`503`/`504`), never mislabeled as mathematical refusals.
HYBRID_INFRASTRUCTURE_CODES = frozenset({
    "LIVE_AI_DISABLED", "MISSING_API_KEY", "STAGING_CORPUS_UNAVAILABLE", "INVALID_HYBRID_ROUTE_MODE",
    "LOCAL_ONLY_GENERAL_NOT_APPROVED", "LOCAL_ONLY_CLOUD_VISION_DISABLED",
    "MODEL_RUNTIME_UNAVAILABLE", "MODEL_CHECKSUM_MISMATCH", "LOCAL_SLM_BUSY",
    "LOCAL_SLM_TIMEOUT", "LOCAL_SLM_PROCESS_CRASHED", "LOCAL_SLM_RESPONSE_INVALID",
    "INVALID_LOCAL_SLM_MODEL",
    "PROVIDER_ERROR", "PROVIDER_BLOCKED", "PROVIDER_REFUSED", "NO_CANDIDATE",
    "PROVIDER_RESPONSE_INVALID", "MALFORMED_RESPONSE_PART", "JSON_INVALID",
    "RESPONSE_TRUNCATED", "MAX_TOKENS",
    "HYBRID_DEADLINE_EXCEEDED", "HYBRID_CANCELLED",
    "EXTRACTOR_INTERNAL_ERROR", "ROUTE_INTERNAL_ERROR", "ADAPTER_INTERNAL_ERROR",
    "ENGINE_EXECUTION_FAILED", "ENGINE_SELF_CHECK_FAILED", "ENGINE_IR_INVALID",
    "SCENE_BUILD_FAILED", "SECTION_CONSTRUCTION_INTERNAL_FAILURE",
    "PREVIEW_IDENTITY_CHANGED", "PREVIEW_DISABLED",
})


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
    Past argument validation this boundary never raises: any other fault of ours is the typed technical refusal
    `ROUTE_INTERNAL_ERROR`, built from constants — never a 500, a scene, or a fallback (review M-3).
    """
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) \
            or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError('timeout_seconds must be finite and positive')
    try:
        return _run_hybrid_offline(problem_text, extractor, policy, timeout_seconds, cancelled)
    except Exception:  # noqa: BLE001 — our fault outside every stage guard; no exception prose is kept
        source = problem_text if isinstance(problem_text, str) else ''
        return HybridOfflineResult(adapter_fault_response('ROUTE_INTERNAL_ERROR'), {
            'schema': 'hybrid-offline-execution/1', 'request_id': uuid4().hex,
            'classification': 'OFFLINE_INTEGRATION_NOT_LIVE_NLU_EVALUATION',
            'source_sha256': sha256(source.encode('utf-8')).hexdigest(), 'provider_performance': 'NOT_MEASURED',
            'cache': 'NOT_USED', 'stages': [], 'source_gate': {'status': 'NOT_CERTIFIED'},
            'planner': {'status': 'NOT_CERTIFIED'}, 'engine': {'status': 'NOT_CERTIFIED'}, 'status': 'REFUSED',
            'code': 'ROUTE_INTERNAL_ERROR', 'failure_stage': 'unknown', 'failure_kind': 'TECHNICAL_FAILURE',
            'source_references': []})


def _run_hybrid_offline(problem_text: str, extractor: Extractor, policy: RoutePolicy | None, timeout_seconds: float,
                        cancelled: Callable[[], bool] | None) -> HybridOfflineResult:
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
        'source_references': [],   # offsets of every validated quote; locates text, certifies nothing (Source Gate does)
    }

    def finish(result: KetQuaTuyen, failure_stage: str | None = None,
               failure_kind: str | None = None) -> HybridOfflineResult:
        try:
            response = build_adapter4_response(result, source)
        except Exception:  # noqa: BLE001 — our fault while wrapping; the handler re-runs nothing that can fail (M-3)
            result = KetQuaTuyen('REFUSED', 'ADAPTER_INTERNAL_ERROR')
            failure_stage, failure_kind = 'adapter4', 'TECHNICAL_FAILURE'
            response = adapter_fault_response(result.code)
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
    receipt['source_references'] = [{'path': list(r.path), 'spans': [list(s) for s in r.spans]}
                                    for r in extraction.source_references]
    stopped = interruption('extraction')
    if stopped is not None:
        return stopped
    if extraction.payload is None:
        code = extraction.code or 'INVALID_TYPED_FACT_NEXT'
        technical_codes = {'EXTRACTOR_INTERNAL_ERROR', 'PROVIDER_ERROR', 'PROVIDER_RESPONSE_INVALID',
                           'PROVIDER_BLOCKED', 'PROVIDER_REFUSED', 'NO_CANDIDATE', 'MALFORMED_RESPONSE_PART',
                           'JSON_INVALID', 'RESPONSE_TRUNCATED', 'MAX_TOKENS', 'HYBRID_DEADLINE_EXCEEDED'}
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

        det_audit = result.details.get('determinacy_audit') if isinstance(result.details, dict) else None
        if isinstance(det_audit, dict):
            receipt['determinacy_audit'] = deepcopy(det_audit)
        technical = (result.code or '').endswith('_INTERNAL_ERROR') or result.code in {
            'ENGINE_EXECUTION_FAILED', 'ENGINE_SELF_CHECK_FAILED', 'ENGINE_IR_INVALID', 'SCENE_BUILD_FAILED',
            'SECTION_CONSTRUCTION_INTERNAL_FAILURE'}
        receipt.update(
            failure_stage='deterministic_route',
            failure_kind='TECHNICAL_FAILURE' if technical else classify_refusal(
                result.code or '', result.planner, problem_text=source, details=result.details
            ).group,
        )
    stopped = interruption('adapter4')
    return stopped if stopped is not None else outcome


#: Schema of the authored replay corpus file `run_local_replay` reads (`scripts/export_hybrid_v2_local_corpus.py`).
LOCAL_REPLAY_SCHEMA = 'hybrid-v2-local-replay-corpus/1'


@dataclass(frozen=True)
class LocalReplay:
    """One request's corpus read, policy snapshot and Route D cache identity — read ONCE, so the identity a result is
    stored under is the identity it was computed from."""
    problem_text: str
    outputs: dict
    policy: RoutePolicy
    cache_key: str | None

    def run(self) -> HybridOfflineResult:
        return run_hybrid_offline(self.problem_text, ReplayExtractor(self.outputs), policy=self.policy)


def prepare_local_replay(problem_text: str, corpus_path: str) -> LocalReplay:
    """A text the corpus does not hold is refused `NO_RECORDED_EXTRACTION` at run time — the offline mode has no language
    understanding, so it never guesses. An unreadable or foreign corpus file is an empty corpus, not an error page.

    `cache_key` (D-02): sha256 of the route, the Route D surface (Registry/Planner/Engine/contract/adapter/envelope
    versions), the recorded extraction and the EXACT source text — not the normalized `LLM_ONLY` key, because quotes
    are grounded verbatim. `None` when nothing is recorded: such a request can only be refused, and refusals are not
    cached."""
    try:
        data = json.loads(Path(corpus_path).read_text(encoding='utf-8'))
        outputs = data['outputs'] if data.get('schema') == LOCAL_REPLAY_SCHEMA and isinstance(data['outputs'], dict) \
            else {}
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        outputs = {}
    policy = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})
    recorded = outputs.get(problem_text) if isinstance(problem_text, str) else None
    key = None
    if recorded is not None:
        identity = {'route': 'HYBRID_V2_LOCAL_OFFLINE_REPLAY', 'surface': dict(policy.preview_surface),
                    'response_contract': policy.response_contract, 'recorded_extraction': recorded,
                    'source': problem_text}
        key = sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    return LocalReplay(problem_text, outputs, policy, key)


def run_local_replay(problem_text: str, corpus_path: str) -> HybridOfflineResult:
    """Stage 2 opt-in local route: verbatim source → recorded `typed-fact-next/2` (authored replay corpus, keyed by the
    exact problem text) → the same validation, Source Gate, planner, exact engine and /4 wrapper as `run_hybrid_offline`."""
    return prepare_local_replay(problem_text, corpus_path).run()


_REPLAY_CORPUS_CACHE: dict[tuple[str, int, int], dict[str, dict]] = {}
HybridTransportTimeout = _tfn_extraction.HybridTransportTimeout


def _finite_pos(value: object, default: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        return default
    return float(value)


def resolve_hybrid_gemini_model(env: Mapping[str, str] | None = None) -> str:
    """Single source of truth for the Hybrid live Gemini model name (empty/whitespace falls back to default)."""
    import os

    raw = (os.environ if env is None else env).get('GEMINI_MODEL')
    cleaned = raw.strip() if isinstance(raw, str) else ''
    return cleaned or 'gemini-2.5-flash'


def load_replay_corpus(corpus_path: str) -> dict[str, dict] | None:
    """Read and validate an authored `hybrid-v2-local-replay-corpus/1` file; memoized by `(path, mtime_ns, size)`."""
    if not corpus_path:
        return None
    try:
        p = Path(corpus_path)
        st = p.stat()
        cache_id = (str(p.resolve()), st.st_mtime_ns, st.st_size)
        cached = _REPLAY_CORPUS_CACHE.get(cache_id)
        if cached is not None:
            return cached
        data = json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(data, dict) or data.get('schema') != LOCAL_REPLAY_SCHEMA or not isinstance(data.get('outputs'), dict):
        return None
    if len(_REPLAY_CORPUS_CACHE) >= 8:
        _REPLAY_CORPUS_CACHE.clear()
    _REPLAY_CORPUS_CACHE[cache_id] = data['outputs']
    return data['outputs']


@dataclass(frozen=True)
class StagingReplay:
    """Selectable staging/integration Hybrid run (`HYBRID_ROUTE_MODE=staging-replay`), explicitly marked as simulated."""
    problem_text: str
    recorded: dict | None
    policy: RoutePolicy
    cache_key: str | None

    def run(self, *, timeout_seconds: float = 15.0) -> HybridOfflineResult:
        single = {self.problem_text: self.recorded} if self.recorded is not None else {}
        res = run_hybrid_offline(self.problem_text, ReplayExtractor(single),
                                 policy=self.policy, timeout_seconds=_finite_pos(timeout_seconds, 15.0))
        response = dict(res.response)
        route_d = dict(response['route_d'])
        route_d['extraction_mode'] = 'REPLAY_STAGING_SIMULATED'
        response['route_d'] = route_d
        receipt = {**res.receipt, 'classification': 'STAGING_REPLAY_SIMULATED_NOT_LIVE_NLU'}
        return HybridOfflineResult(response, receipt)


def prepare_staging_replay(problem_text: str, corpus_path: str) -> StagingReplay | None:
    outputs = load_replay_corpus(corpus_path)
    if outputs is None:
        return None
    policy = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})
    recorded = outputs.get(problem_text) if isinstance(problem_text, str) else None
    key = None
    if recorded is not None:
        identity = {
            'route': 'HYBRID_V2_STAGING_REPLAY',
            'surface': dict(policy.preview_surface),
            'response_contract': policy.response_contract,
            'recorded_extraction': recorded,
            'source': problem_text,
        }
        key = sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    return StagingReplay(problem_text, recorded, policy, key)


def _live_provider_transport(
    api_key: str,
    model: str | None = None,
    timeout_seconds: float = 60.0,
    *,
    deadline_seconds: float | None = None,
    sleep=time.sleep,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Bounded Gemini `generateContent` transport (`x-goog-api-key` header, `ALLOW_LIVE_AI=0` kill-switch respected,
    deadline-aware transient retries, proper `ApiBudget` retry accounting, zero model fallback)."""
    import httpx

    from app.ai import gemini
    from app.ai.function_calling import ProviderHTTPError, live_transport

    per_attempt = _finite_pos(timeout_seconds, 60.0)
    total_deadline = _finite_pos(deadline_seconds, per_attempt * 3.0)
    resolved_model = (model or '').strip() or gemini.MODEL
    try:
        send_once = live_transport(
            api_key, model=resolved_model, timeout_seconds=per_attempt, require_allow_live_ai=False
        )
    except TypeError:
        send_once = live_transport(api_key, model=resolved_model, timeout_seconds=per_attempt)

    def send(request: dict[str, Any]) -> dict[str, Any]:
        deadline_at = perf_counter() + total_deadline
        for attempt in range(gemini.MAX_ATTEMPTS):
            rem = deadline_at - perf_counter()
            if rem <= 0:
                raise HybridTransportTimeout('hybrid live deadline exceeded')
            attempt_timeout = min(per_attempt, rem)
            try:
                return send_once(request, is_retry=(attempt > 0), timeout_override=attempt_timeout)
            except ProviderHTTPError as exc:
                if exc.status_code not in gemini.TRANSIENT_STATUS or attempt == gemini.MAX_ATTEMPTS - 1:
                    raise
                if gemini.BUDGET is not None:
                    gemini.BUDGET.note_transient()
            except httpx.TimeoutException:
                if attempt == gemini.MAX_ATTEMPTS - 1 or (deadline_at - perf_counter()) <= 0:
                    raise HybridTransportTimeout('hybrid live upstream timeout') from None
                if gemini.BUDGET is not None:
                    gemini.BUDGET.note_transient()
            except httpx.NetworkError:
                if attempt == gemini.MAX_ATTEMPTS - 1:
                    raise
                if gemini.BUDGET is not None:
                    gemini.BUDGET.note_transient()
            backoff = gemini.BACKOFF_BASE_SECONDS * (2 ** attempt)
            if (deadline_at - perf_counter()) <= backoff:
                raise HybridTransportTimeout('hybrid live deadline exceeded before retry')
            sleep(backoff)
        raise HybridTransportTimeout('hybrid live deadline exceeded')

    return send


@dataclass(frozen=True)
class LiveHybridRun:
    """Selectable live Hybrid `/4` run (`HYBRID_ROUTE_MODE=live`), bound to model + extraction/route surfaces."""
    problem_text: str
    model: str
    extraction_surface: str
    policy: RoutePolicy
    cache_key: str

    def run(
        self,
        api_key: str,
        *,
        per_attempt_timeout_s: float = 60.0,
        deadline_seconds: float | None = None,
    ) -> HybridOfflineResult:
        eff_per = _finite_pos(per_attempt_timeout_s, 60.0)
        eff_deadline = _finite_pos(deadline_seconds, eff_per * 3.0)
        transport = _live_provider_transport(
            api_key, model=self.model, timeout_seconds=eff_per, deadline_seconds=eff_deadline
        )
        res = run_hybrid_offline(
            self.problem_text,
            TransportExtractor(transport),
            policy=self.policy,
            timeout_seconds=eff_deadline,
        )
        response = dict(res.response)
        route_d = dict(response['route_d'])
        route_d['extraction_mode'] = 'LIVE_GEMINI_STRUCTURED'
        route_d['extraction_model'] = self.model
        response['route_d'] = route_d
        receipt = {
            **res.receipt,
            'classification': 'LIVE_STRUCTURED_EXTRACTION',
            'provider_performance': 'MEASURED_IN_TELEMETRY',
        }
        return HybridOfflineResult(response, receipt)


def prepare_live_hybrid(problem_text: str, *, model: str | None = None) -> LiveHybridRun:
    resolved_model = (model or '').strip() or 'gemini-2.5-flash'
    policy = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})
    ext_fp = _tfn_extraction.typed_fact_next_surface_fingerprint()
    identity = {
        'route': 'HYBRID_V2_LIVE',
        'model': resolved_model,
        'extraction_surface': ext_fp,
        'surface': dict(policy.preview_surface),
        'response_contract': policy.response_contract,
        'source': problem_text,
    }
    key = sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    return LiveHybridRun(problem_text, resolved_model, ext_fp, policy, key)


@dataclass(frozen=True)
class LocalFirstHybridRun:
    """Selectable Local-First Hybrid `/4` run (`HYBRID_ROUTE_MODE=local-first` or `HYBRID_LOCAL_FIRST=1`)."""
    problem_text: str
    model: str
    extraction_surface: str
    policy: RoutePolicy
    cache_key: str

    def run(
        self,
        api_key: str | None = None,
        *,
        allow_live_ai: bool = True,
        per_attempt_timeout_s: float = 60.0,
        deadline_seconds: float | None = None,
    ) -> HybridOfflineResult:
        from app.ai.adaptive_input_router import route_text_input

        eff_per = _finite_pos(per_attempt_timeout_s, 60.0)
        eff_deadline = _finite_pos(deadline_seconds, eff_per * 3.0)
        fallback_ext: Extractor | None = None
        if allow_live_ai and api_key:
            transport = _live_provider_transport(
                api_key, model=self.model, timeout_seconds=eff_per, deadline_seconds=eff_deadline
            )
            fallback_ext = TransportExtractor(transport)
        outcome = route_text_input(
            self.problem_text,
            fallback_extractor=fallback_ext,
            allow_live_ai=allow_live_ai,
            fallback_unavailable_code=("MISSING_API_KEY" if allow_live_ai and not api_key else None),
            input_kind='text',
            model=self.model,
            policy=self.policy,
            timeout_seconds=eff_deadline,
        )
        return HybridOfflineResult(outcome.response, outcome.receipt)


def prepare_local_first_hybrid(problem_text: str, *, model: str | None = None) -> LocalFirstHybridRun:
    from app.ai.adaptive_input_router import ADAPTIVE_INPUT_ROUTER_VERSION
    from app.ai.local_geometry_parser import LOCAL_GEOMETRY_PARSER_VERSION

    resolved_model = (model or '').strip() or 'gemini-2.5-flash'
    policy = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})
    ext_fp = _tfn_extraction.typed_fact_next_surface_fingerprint()
    identity = {
        'route': 'HYBRID_V4_LOCAL_FIRST',
        'router_version': ADAPTIVE_INPUT_ROUTER_VERSION,
        'parser_version': LOCAL_GEOMETRY_PARSER_VERSION,
        'model': resolved_model,
        'extraction_surface': ext_fp,
        'surface': dict(policy.preview_surface),
        'response_contract': policy.response_contract,
        'source': problem_text,
    }
    key = sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    return LocalFirstHybridRun(problem_text, resolved_model, ext_fp, policy, key)


@dataclass(frozen=True)
class LocalSlmHybridRun:
    """Selectable Local-SLM Hybrid `/5` run (`HYBRID_ROUTE_MODE=local-slm`, `external_ai_calls = 0`)."""
    problem_text: str
    model_key: str
    strategy: str
    extraction_surface: str
    policy: RoutePolicy
    cache_key: str

    def run(
        self,
        *,
        timeout_seconds: float = 30.0,
        allow_download: bool = False,
    ) -> HybridOfflineResult:
        from app.ai.adaptive_input_router import route_text_input_local_slm

        outcome = route_text_input_local_slm(
            self.problem_text,
            model_key=self.model_key,
            strategy=self.strategy,
            allow_download=allow_download,
            policy=self.policy,
            timeout_seconds=_finite_pos(timeout_seconds, 30.0),
        )
        return HybridOfflineResult(outcome.response, outcome.receipt)


def prepare_local_slm_hybrid(
    problem_text: str,
    *,
    model_key: str | None = None,
    strategy: str | None = None,
) -> LocalSlmHybridRun:
    from app.ai.adaptive_input_router import ADAPTIVE_INPUT_ROUTER_VERSION
    from app.ai.local_geometry_parser import LOCAL_GEOMETRY_PARSER_VERSION
    from app.ai.local_slm_extractor import (
        LOCAL_SLM_EXTRACTOR_VERSION,
        SLM_COMPACT_SCHEMA_VERSION,
        SLM_GROUNDING_VALIDATOR_VERSION,
        resolve_local_slm_strategy,
    )
    from app.ai.local_slm_runtime import LOCAL_SLM_CACHE_NAMESPACE, LOCAL_SLM_RUNTIME_VERSION, resolve_local_slm_model_spec

    spec = resolve_local_slm_model_spec(model_key)
    eff_strategy = resolve_local_slm_strategy(strategy)
    policy = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})
    ext_fp = _tfn_extraction.typed_fact_next_surface_fingerprint()
    is_v6 = eff_strategy in ('compact_clause', 'compact_clause_per_clause')
    identity = {
        'route': LOCAL_SLM_CACHE_NAMESPACE if is_v6 else 'HYBRID_V5_LOCAL_SLM',
        'router_version': ADAPTIVE_INPUT_ROUTER_VERSION,
        'parser_version': LOCAL_GEOMETRY_PARSER_VERSION,
        'runtime_version': LOCAL_SLM_RUNTIME_VERSION,
        'extractor_version': LOCAL_SLM_EXTRACTOR_VERSION,
        'schema_version': SLM_COMPACT_SCHEMA_VERSION if is_v6 else eff_strategy,
        'validator_version': SLM_GROUNDING_VALIDATOR_VERSION,
        'model_key': spec.model_key,
        'model_sha256': spec.sha256,
        'strategy': eff_strategy,
        'extraction_surface': ext_fp,
        'surface': dict(policy.preview_surface),
        'response_contract': policy.response_contract,
        'source': problem_text,
    }
    key = sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    return LocalSlmHybridRun(problem_text, spec.model_key, eff_strategy, ext_fp, policy, key)


@dataclass(frozen=True)
class LocalSlmV9HybridRun:
    """Selectable Hybrid `/9` local-only run (`offline-lab`, `local-only-scoped`, `local-only-general`, 0 external AI)."""
    problem_text: str
    mode_tag: str
    model_key: str
    strategy: str
    extraction_surface: str
    policy: RoutePolicy
    cache_key: str

    def run(
        self,
        *,
        timeout_seconds: float = 30.0,
        allow_download: bool = False,
    ) -> HybridOfflineResult:
        from app.ai.adaptive_input_router import route_text_input_local_slm
        from app.ai.local_slm_extractor import V9_CLOSURE_MODE

        outcome = route_text_input_local_slm(
            self.problem_text,
            model_key=self.model_key,
            strategy=self.strategy,
            closure_mode=V9_CLOSURE_MODE,
            normalizer_version='v3',
            allow_download=allow_download,
            policy=self.policy,
            timeout_seconds=_finite_pos(timeout_seconds, 30.0),
        )
        return HybridOfflineResult(outcome.response, outcome.receipt)


def prepare_local_slm_v9_hybrid(
    problem_text: str,
    *,
    mode_tag: str = 'local-only-scoped',
    model_key: str | None = None,
    strategy: str | None = None,
) -> LocalSlmV9HybridRun:
    from app.ai.adaptive_input_router import ADAPTIVE_INPUT_ROUTER_VERSION
    from app.ai.local_geometry_parser import LOCAL_GEOMETRY_PARSER_VERSION
    from app.ai.local_slm_extractor import (
        LOCAL_SLM_EXTRACTOR_V9_VERSION,
        SLM_COMPACT_SCHEMA_VERSION,
        SLM_GROUNDING_VALIDATOR_V9_VERSION,
        V9_CLOSURE_MODE,
        resolve_local_slm_strategy,
    )
    from app.ai.local_slm_runtime import (
        LOCAL_SLM_CACHE_V9_NAMESPACE,
        LOCAL_SLM_RUNTIME_V9_VERSION,
        resolve_local_slm_model_spec,
    )
    from app.ai.slm_verified_normalizer import SLM_VERIFIED_NORMALIZER_V3_VERSION

    req_model = model_key or os.getenv('LOCAL_SLM_MODEL') or 'v9-active'
    spec = resolve_local_slm_model_spec(req_model)
    eff_strategy = resolve_local_slm_strategy(strategy)
    policy = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})
    ext_fp = _tfn_extraction.typed_fact_next_surface_fingerprint()
    identity = {
        'route': LOCAL_SLM_CACHE_V9_NAMESPACE,
        'mode_tag': mode_tag,
        'router_version': ADAPTIVE_INPUT_ROUTER_VERSION,
        'parser_version': LOCAL_GEOMETRY_PARSER_VERSION,
        'normalizer_version': SLM_VERIFIED_NORMALIZER_V3_VERSION,
        'closure_mode': V9_CLOSURE_MODE,
        'runtime_version': LOCAL_SLM_RUNTIME_V9_VERSION,
        'extractor_version': LOCAL_SLM_EXTRACTOR_V9_VERSION,
        'schema_version': SLM_COMPACT_SCHEMA_VERSION,
        'validator_version': SLM_GROUNDING_VALIDATOR_V9_VERSION,
        'model_key': spec.model_key,
        'model_sha256': spec.sha256,
        'strategy': eff_strategy,
        'extraction_surface': ext_fp,
        'surface': dict(policy.preview_surface),
        'response_contract': policy.response_contract,
        'source': problem_text,
    }
    key = sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    return LocalSlmV9HybridRun(problem_text, mode_tag, spec.model_key, eff_strategy, ext_fp, policy, key)


@dataclass(frozen=True)
class LocalShadowHybridRun:
    """Authoritative Live Gemini run + non-blocking Local SLM `/9` shadow comparison."""
    problem_text: str
    live_run: LiveHybridRun
    cache_key: str

    def run(
        self,
        api_key: str,
        *,
        per_attempt_timeout_s: float = 60.0,
        deadline_seconds: float | None = None,
    ) -> HybridOfflineResult:
        live_res = self.live_run.run(
            api_key,
            per_attempt_timeout_s=per_attempt_timeout_s,
            deadline_seconds=deadline_seconds,
        )
        response = dict(live_res.response)
        route_d = dict(response.get('route_d') or {})
        receipt = dict(live_res.receipt)
        t_sh0 = perf_counter()
        shadow_info: dict[str, Any] = {'slm_status': 'UNAVAILABLE', 'agreed_with_live': False, 'slm_ms': 0.0}
        try:
            eff_slm_timeout = min(_finite_pos(deadline_seconds, 15.0) if deadline_seconds is not None else 15.0, 15.0)
            shadow_run = prepare_local_slm_v9_hybrid(self.problem_text, mode_tag='local-shadow')
            shadow_res = shadow_run.run(timeout_seconds=eff_slm_timeout, allow_download=False)
            slm_rd = (shadow_res.response or {}).get('route_d') or {}
            slm_st = str(slm_rd.get('status') or 'REFUSED')
            live_st = str(route_d.get('status') or 'REFUSED')
            agreed = slm_st == live_st and (
                slm_st != 'SERVED' or (slm_rd.get('answers') or {}) == (route_d.get('answers') or {})
            )
            shadow_info = {
                'slm_status': slm_st,
                'agreed_with_live': agreed,
                'slm_ms': round((perf_counter() - t_sh0) * 1000.0, 2),
                'model_key': shadow_run.model_key,
            }
        except Exception:
            shadow_info = {
                'slm_status': 'SHADOW_SKIPPED',
                'agreed_with_live': False,
                'slm_ms': round((perf_counter() - t_sh0) * 1000.0, 2),
            }
        route_d['local_shadow'] = shadow_info
        response['route_d'] = route_d
        receipt['local_shadow'] = shadow_info
        return HybridOfflineResult(response, receipt)


def prepare_local_shadow_hybrid(problem_text: str, *, model: str | None = None) -> LocalShadowHybridRun:
    live_run = prepare_live_hybrid(problem_text, model=model)
    return LocalShadowHybridRun(problem_text=problem_text, live_run=live_run, cache_key=live_run.cache_key)


LOCAL_ONLY_HYBRID_MODES = ('local-slm', 'offline-lab', 'local-only-scoped', 'local-only-general')


def local_slm_ready_status(env: Mapping[str, str], mode: str) -> dict[str, Any]:
    """Non-throwing readiness summary for `/api/health` and runtime diagnostics."""
    local_only = mode in LOCAL_ONLY_HYBRID_MODES
    pref = str(env.get('LOCAL_SLM_MODEL') or ('v9-active' if mode != 'local-slm' else 'finetuned')).strip() or 'v9-active'
    model_key: str | None = None
    ready = False
    try:
        from app.ai.local_slm_runtime import ensure_local_slm_provisioned, resolve_local_slm_model_spec

        spec = resolve_local_slm_model_spec(pref)
        model_key = spec.model_key
        ensure_local_slm_provisioned(model_key=spec.model_key, allow_download=False)
        ready = True
    except Exception:
        ready = False
    if local_only:
        backend = 'local_slm_v9' if mode in ('offline-lab', 'local-only-scoped', 'local-only-general') else 'local_slm_v7'
    elif mode == 'local-first':
        backend = 'local_first_with_cloud_fallback'
    elif mode == 'local-shadow':
        backend = 'live_gemini_with_local_shadow'
    elif mode == 'staging-replay':
        backend = 'staging_replay'
    elif mode == 'live':
        backend = 'live_gemini'
    else:
        backend = 'invalid'
    return {
        'localOnlyMode': local_only,
        'localSlmReady': ready,
        'localSlmModel': model_key,
        'extractionBackend': backend,
    }


def build_local_ai_ux_descriptor(*, status_code: int, body: Mapping[str, Any], local_only: bool) -> dict[str, str]:
    """Map runtime & analysis payloads into one of 10 clean Vietnamese learner UX states (zero internal tokens)."""
    reason_code = str(body.get('reason_code') or body.get('error_code') or '').strip()
    if body.get('warming_up') or reason_code == 'LOCAL_SLM_WARMING_UP':
        return {
            'ux_state': 'WARMING_UP_MODEL',
            'learner_title': 'Đang khởi động bộ đọc đề ngoại tuyến',
            'learner_message': 'Hệ thống đang nạp mô hình trên máy. Em vui lòng đợi trong giây lát rồi thử lại.',
        }
    if reason_code == 'LOCAL_ONLY_CLOUD_VISION_DISABLED':
        return {
            'ux_state': 'CLOUD_OCR_DISABLED_OFFLINE',
            'learner_title': 'Chế độ ngoại tuyến không đọc ảnh trực tuyến',
            'learner_message': 'Chế độ hiện tại không gửi ảnh lên mạng. Em hãy nhập trực tiếp đề bài bằng chữ hoặc tải tệp PDF/DOCX có lớp văn bản.',
        }
    if reason_code in (
        'MODEL_RUNTIME_UNAVAILABLE', 'MODEL_CHECKSUM_MISMATCH', 'INVALID_LOCAL_SLM_MODEL', 'LOCAL_ONLY_GENERAL_NOT_APPROVED',
    ):
        return {
            'ux_state': 'MODEL_NOT_PROVISIONED',
            'learner_title': 'Bộ đọc đề ngoại tuyến chưa sẵn sàng',
            'learner_message': 'Mô hình xử lý trên máy chưa được cài đặt đầy đủ hoặc chưa bật. Em vẫn có thể xem các bài mô phỏng mẫu.',
        }
    if status_code in (502, 503, 504) or reason_code in (
        'LOCAL_SLM_BUSY', 'LOCAL_SLM_TIMEOUT', 'LOCAL_SLM_PROCESS_CRASHED',
        'LOCAL_SLM_RESPONSE_INVALID', 'HYBRID_DEADLINE_EXCEEDED', 'ROUTE_INTERNAL_ERROR',
    ):
        return {
            'ux_state': 'RUNTIME_BUSY_OR_TIMEOUT',
            'learner_title': 'Hệ thống xử lý trên máy đang bận',
            'learner_message': 'Quá trình phân tích đề mất nhiều thời gian hơn dự kiến hoặc đang có nhiều lượt xử lý cùng lúc. Em hãy nhấn thử lại sau vài giây.',
        }

    route_d = body.get('route_d') if isinstance(body.get('route_d'), Mapping) else {}
    envelope = body.get('envelope') if isinstance(body.get('envelope'), Mapping) else {}
    rd_status = str(route_d.get('status') or '')
    if status_code == 200 and rd_status == 'SERVED':
        return {
            'ux_state': 'SERVED_OFFLINE_VERIFIED',
            'learner_title': 'Đã dựng hình và kiểm chứng thành công',
            'learner_message': 'Hình không gian 3D và đáp số chính xác đã sẵn sàng từ quá trình xử lý ngay trên máy.',
        }

    refusal = route_d.get('refusal') if isinstance(route_d.get('refusal'), Mapping) else {}
    rc = str(refusal.get('reason_code') or refusal.get('code') or reason_code or envelope.get('reason_code') or '').strip()
    fcat = str(body.get('failure_category') or envelope.get('failure_category') or '').strip()

    if body.get('status') == 'unsupported' or fcat in ('out_of_scope', 'capability_gap') or rc in (
        'OUT_OF_SCOPE', 'GATE_OUT_OF_SCOPE', 'CURVED_WORDING_UNSUPPORTED', 'UNSUPPORTED_CAPABILITY', 'EXACT_DOMAIN_EXCEEDED',
    ) or rc.startswith('BRIDGE_UNSUPPORTED'):
        return {
            'ux_state': 'OUT_OF_SUPPORTED_SCOPE',
            'learner_title': 'Đề bài nằm ngoài phạm vi hỗ trợ hiện tại',
            'learner_message': 'Hệ thống hiện tập trung dựng và giải hình học không gian khối đa diện bậc trung học phổ thông với các phép đo được hỗ trợ.',
        }

    if fcat == 'geometry_generation_failed' or rc in (
        'INCONSISTENT_FACTS', 'NON_POSITIVE_LENGTH', 'DEGENERATE_SOLID', 'COLLINEAR_POINTS',
        'NON_COPLANAR_POINTS', 'PARALLEL_NO_INTERSECTION', 'PLANE_DOES_NOT_CUT',
        'NO_CIRCUMSCRIBED_SPHERE', 'NO_INSCRIBED_SPHERE',
    ):
        return {
            'ux_state': 'CONTRADICTORY_GEOMETRY_DATA',
            'learner_title': 'Giả thiết hình học có mâu thuẫn hoặc suy biến',
            'learner_message': 'Các số đo hoặc quan hệ hình học trong đề bài không thể cùng tồn tại trong không gian. Em hãy kiểm tra lại các điều kiện đã nhập.',
        }

    if fcat == 'insufficient_specification' or rc in (
        'MISSING_DIMENSION', 'UNDERDETERMINED_POINT', 'PLANE_NOT_UNIQUE',
        'FOOT_NOT_DETERMINED', 'FACT_INCOMPLETE', 'SECTION_NOT_CLOSED_ON_LATERAL_EDGES',
    ):
        return {
            'ux_state': 'MISSING_GEOMETRY_DATA',
            'learner_title': 'Đề bài còn thiếu dữ kiện để dựng hình duy nhất',
            'learner_message': 'Hệ thống chưa đủ độ dài, góc hoặc vị trí điểm cố định để xác định hình không gian. Em hãy bổ sung phần giả thiết còn thiếu.',
        }

    if status_code == 200 and 'ok' in body and 'route_d' not in body:
        return {
            'ux_state': 'READY_OFFLINE',
            'learner_title': 'Sẵn sàng dựng hình ngoại tuyến',
            'learner_message': 'Hệ thống đang chạy bằng mô hình trên máy, không cần khóa kết nối đám mây.',
        }

    return {
        'ux_state': 'CLARIFICATION_NEEDED',
        'learner_title': 'Cần viết rõ hơn một phần diễn đạt trong đề',
        'learner_message': 'Một số cụm từ hoặc ký hiệu trong đề bài còn chưa rõ để đối chiếu chắc chắn. Em hãy diễn đạt tách câu ngắn gọn hơn rồi gửi lại.',
    }


def hybrid_route_identity(mode: str, env: Mapping[str, str]) -> dict[str, Any]:
    """Diagnostics snapshot for `/api/diagnostics/runtime` (never exposes secrets)."""
    from app.ai.adaptive_input_router import ADAPTIVE_INPUT_ROUTER_VERSION
    from app.ai.local_geometry_parser import LOCAL_GEOMETRY_PARSER_VERSION

    surface = _surface()
    known = ('staging-replay', 'live', 'local-first', 'local-slm', 'offline-lab', 'local-shadow', 'local-only-scoped', 'local-only-general')
    valid = mode in known and (mode != 'local-only-general' or env.get('AXO_ALLOW_GENERAL_LOCAL_CUTOVER') == '1')
    mode_map = {
        'staging-replay': 'REPLAY_STAGING_SIMULATED',
        'local-slm': 'LOCAL_FIRST_SLM_GROUNDED',
        'offline-lab': 'LOCAL_ONLY_V9_OFFLINE_LAB',
        'local-only-scoped': 'LOCAL_ONLY_V9_SCOPED',
        'local-only-general': 'LOCAL_ONLY_V9_GENERAL',
        'local-shadow': 'LIVE_GEMINI_WITH_LOCAL_V9_SHADOW',
        'local-first': 'LOCAL_FIRST_DETERMINISTIC_WITH_AI_FALLBACK',
        'live': 'LIVE_GEMINI_STRUCTURED',
    }
    extraction_mode = mode_map.get(mode, 'INVALID_HYBRID_ROUTE_MODE')
    local_stat = local_slm_ready_status(env, mode)
    return {
        'mode': mode,
        'enabled': valid,
        'simulated': mode == 'staging-replay',
        'local_only': local_stat['localOnlyMode'],
        'local_slm_model_key': local_stat['localSlmModel'],
        'local_slm_provisioned': local_stat['localSlmReady'],
        'extraction_mode': extraction_mode,
        'local_parser_version': LOCAL_GEOMETRY_PARSER_VERSION,
        'adaptive_router_version': ADAPTIVE_INPUT_ROUTER_VERSION,
        'registry_version': surface['registry_version'],
        'planner_version': surface['planner_version'],
        'engine_version': surface['engine_version'],
        'adapter_version': surface['adapter_version'],
        'envelope_version': surface['envelope_version'],
        'response_contract': surface['response_contract'],
        'extraction_surface': _tfn_extraction.typed_fact_next_surface_fingerprint(),
        'gemini_model': resolve_hybrid_gemini_model(env),
        'allow_live_ai': env.get('ALLOW_LIVE_AI') != '0',
        'replay_corpus_configured': bool(env.get('HYBRID_REPLAY_CORPUS')),
    }
