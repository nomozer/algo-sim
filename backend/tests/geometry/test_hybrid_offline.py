"""Problem text -> replay extraction -> real /4 backend. Authored development fixtures, not NLU measurements."""
from copy import deepcopy
import importlib
import json
from pathlib import Path

import pytest


CASES = json.loads((Path(__file__).resolve().parents[3] /
    'docs/evaluation/geometry/runs/hybrid-contract-v2/grammar-set.json').read_text(encoding='utf-8'))['cases']


def api():
    return importlib.import_module('app.ai.hybrid_offline')


def enabled():
    return api().hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})


def replay(raw):
    from app.ai.typed_fact_next_extraction import ReplayExtractor
    return ReplayExtractor({raw['problem_text']: raw})


def test_offline_orchestrator_exists():
    assert importlib.util.find_spec('app.ai.hybrid_offline') is not None


def test_disabled_and_default_policy_never_invoke_extractor(monkeypatch):
    class Bomb:
        def extract(self, text):
            pytest.fail('disabled route invoked extractor')
    monkeypatch.setenv('HYBRID_ROUTE_D_PREVIEW', '1')
    for policy in (None, api().hybrid_offline_policy({})):
        result = api().run_hybrid_offline('Cho hình chóp.', Bomb(), policy=policy)
        assert result.response['envelope']['reason_code'] == 'PREVIEW_DISABLED'
        assert result.receipt['stages'] == []


def test_offline_policy_uses_existing_route_snapshot_and_cannot_enter_default_cache():
    from app.ai.pipeline import RoutePolicy, route_policy_snapshot
    from app.main import _policy_identity, CACHE_VERSION
    policy = enabled()
    assert isinstance(policy, RoutePolicy)
    assert policy.geometry_compiler_mode == 'LLM_ONLY'
    assert policy.response_contract == 'typed-fact-next/2'
    assert dict(policy.preview_surface)['adapter_version'] == 'hybrid-simulation-adapter/4'
    assert route_policy_snapshot({}).response_contract == 'flat'
    assert _policy_identity(route_policy_snapshot({})) == CACHE_VERSION
    with pytest.raises(ValueError):
        _policy_identity(policy)


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['id'])
def test_source_text_drives_the_existing_deterministic_route(case):
    raw = deepcopy(case['payload'])
    result = api().run_hybrid_offline(raw['problem_text'], replay(raw), policy=enabled())
    response, receipt = result.response, result.receipt
    assert response['schema_version'] == 'hybrid-route-d-simulation/4'
    assert receipt['source_sha256']
    assert receipt['classification'] == 'OFFLINE_INTEGRATION_NOT_LIVE_NLU_EVALUATION'
    assert receipt['provider_performance'] == 'NOT_MEASURED'
    assert receipt['stages'][0]['name'] == 'extraction'
    if case['id'] == 'PARA-0':
        assert response['envelope']['status'] == 'ok'
        assert response['route_d']['answer_exact']['g_ratio']['coef'] == '1/8'
        assert receipt['source_gate']['authority'] == 'registry.kiem_nguon'
        assert receipt['engine']['kernel_check'] is True
    if response['envelope']['status'] != 'ok':
        assert 'scene3d' not in response['envelope']
        assert 'answers' not in response['route_d']


@pytest.mark.parametrize('suffix', [
    ' Chứng minh rằng SB vuông góc với (ABC).',
    ' Nếu SB = 2a thì SC = 3a.',
    ' SB không vuông góc với (ABC).',
    ' Tính độ dài SB.',
])
def test_omitted_source_obligation_is_not_a_served_partial_solution(suffix):
    raw = deepcopy(CASES[0]['payload'])
    raw['problem_text'] += suffix
    result = api().run_hybrid_offline(raw['problem_text'], replay(raw), policy=enabled())
    assert result.response['envelope']['status'] == 'unsupported'
    assert result.response['envelope']['reason_code']


def test_extraction_fault_keeps_technical_stage_and_never_leaks_body():
    class Broken:
        def extract(self, text):
            raise RuntimeError('PRIVATE_RAW_BODY')
    result = api().run_hybrid_offline('Cho hình chóp.', Broken(), policy=enabled())
    assert result.receipt['failure_kind'] == 'TECHNICAL_FAILURE'
    assert result.receipt['failure_stage'] == 'extraction'
    assert 'PRIVATE' not in repr(result)
    assert 'scene3d' not in result.response['envelope']


def test_source_spoof_is_rejected_before_route(monkeypatch):
    raw = deepcopy(CASES[0]['payload'])
    class Spoof:
        def extract(self, text):
            return raw
    def bomb(*args):
        pytest.fail('source mismatch reached geometry')
    monkeypatch.setattr(api(), 'run_typed_fact_next_v2_route', bomb)
    result = api().run_hybrid_offline('Nguồn khác.', Spoof(), policy=enabled())
    assert result.response['envelope']['reason_code'] == 'REPLAY_SOURCE_IDENTITY_MISMATCH'


def test_deadline_after_extraction_and_cancellation_never_publish_a_scene(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(api(), 'perf_counter', lambda: now[0])
    raw = deepcopy(CASES[0]['payload'])
    class Slow:
        def extract(self, text):
            now[0] = 2.0
            return raw
    result = api().run_hybrid_offline(raw['problem_text'], Slow(), policy=enabled(), timeout_seconds=1)
    assert result.response['envelope']['reason_code'] == 'HYBRID_DEADLINE_EXCEEDED'
    assert result.receipt['failure_kind'] == 'TECHNICAL_FAILURE'
    result = api().run_hybrid_offline(raw['problem_text'], Slow(), policy=enabled(), cancelled=lambda: True)
    assert result.response['envelope']['reason_code'] == 'HYBRID_CANCELLED'
    assert result.receipt['stages'] == []


def test_invalid_source_is_not_silently_truncated():
    from app.ingestion.input import MAX_TEXT_CHARS
    class Bomb:
        def extract(self, text):
            pytest.fail('invalid source reached extractor')
    for source in ('', '   ', 'x' * (MAX_TEXT_CHARS + 1), None):
        result = api().run_hybrid_offline(source, Bomb(), policy=enabled())
        assert result.response['envelope']['reason_code'] == 'FACT_INCOMPLETE'


def test_policy_identity_change_refuses_before_work():
    from dataclasses import replace
    class Bomb:
        def extract(self, text):
            pytest.fail('stale policy reached extractor')
    stale = replace(enabled(), preview_surface=())
    result = api().run_hybrid_offline('Cho hình chóp.', Bomb(), policy=stale)
    assert result.response['envelope']['reason_code'] == 'PREVIEW_IDENTITY_CHANGED'


@pytest.mark.parametrize('body', [
    {'candidates': []},
    {'candidates': [{'finishReason': 'MAX_TOKENS'}]},
    {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': '{'}]}}]},
])
def test_provider_output_failure_is_not_scored_as_geometry_refusal(body):
    from app.ai.typed_fact_next_extraction import TransportExtractor
    result = api().run_hybrid_offline('Cho hình chóp.', TransportExtractor(lambda request: body), policy=enabled())
    assert result.receipt['failure_kind'] == 'TECHNICAL_FAILURE'
    assert result.receipt['failure_stage'] == 'extraction'
