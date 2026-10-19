"""Actual offline HTTP preview acceptance; expected quantities come from the problem/oracle, not the adapter."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import re
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

import app.main as main
from app.ai import pipeline as PL

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'docs/evaluation/geometry/runs/contract-driven-goal-composition'
CORPUS = json.loads((RUN / 'corpus.json').read_text(encoding='utf-8'))
URL = '/api/preview/hybrid'
TOKEN = 'offline-test-token-with-at-least-32-characters'


def provider_body(payload):
    return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
        {'text': json.dumps(payload, ensure_ascii=False)}]}}]}


def independent_square(coef):
    """Read the public single-radical number format using Fraction only, independently of product arithmetic."""
    if '√' not in coef:
        return Fraction(coef) ** 2
    match = re.fullmatch(r'(\d*)√(\d+)(?:/(\d+))?', coef)
    assert match, coef
    numerator, radical, denominator = match.groups()
    return Fraction(int(numerator or 1) ** 2 * int(radical), int(denominator or 1) ** 2)


@pytest.fixture
def preview(monkeypatch):
    monkeypatch.setenv('ALLOW_LIVE_AI', '0')
    monkeypatch.setenv('HYBRID_ROUTE_D_PREVIEW', '1')
    monkeypatch.setenv('HYBRID_ROUTE_D_PREVIEW_TOKEN', TOKEN)
    monkeypatch.setattr(main.app.state, 'hybrid_preview_fixtures', {}, raising=False)
    return TestClient(main.app, client=('127.0.0.1', 43210),
                      headers={'X-AlgoSim-Preview-Token': TOKEN})


def ask(client, case):
    main.app.state.hybrid_preview_fixtures = {case['text']: provider_body(deepcopy(case['payload']))}
    return client.post(URL, json={'problem_text': case['text']})


def test_preview_off_refuses_before_route_d_work(preview, monkeypatch):
    monkeypatch.delenv('HYBRID_ROUTE_D_PREVIEW')
    r = preview.post(URL, json={'problem_text': 'Cho hình chóp S.ABCD.'})
    assert r.status_code == 404
    assert r.json().get('reason_code') == 'PREVIEW_DISABLED'


def test_preview_on_serves_a_validated_envelope_without_cache(preview, monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError('preview touched production cache/database')
    monkeypatch.setattr(main, '_cache_lookup', forbidden)
    monkeypatch.setattr(main, 'SessionLocal', forbidden)
    r = ask(preview, CORPUS['positive'][0])
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['schema_version'] == 'hybrid-route-d-preview/1'
    env = data['envelope']
    assert env['status'] == 'ok', env
    assert env['simulation_id'] == 'generic.semantic_program'
    assert env['scene3d']['objects'] and env['scene3d']['events']
    assert env['config']['frames'] and env['config']['view_steps']
    assert data['route_d']['geometry_ir']['statements']
    assert data['route_d']['answer_exact'] and data['route_d']['source_provenance']
    assert data['route_d']['runtime_identity']['response_contract'] == 'flat'
    assert r.headers['cache-control'] == 'no-store'


@pytest.mark.parametrize('setting', ['missing-token', 'wrong-token', 'short-server-token', 'external-peer'])
def test_preview_requires_explicit_operator_access(preview, monkeypatch, setting):
    client = preview
    if setting == 'missing-token': client.headers.pop('X-AlgoSim-Preview-Token')
    if setting == 'wrong-token': client.headers['X-AlgoSim-Preview-Token'] = 'wrong'
    if setting == 'short-server-token': monkeypatch.setenv('HYBRID_ROUTE_D_PREVIEW_TOKEN', 'short')
    if setting == 'external-peer':
        client = TestClient(main.app, client=('203.0.113.9', 1234),
                            headers={'X-AlgoSim-Preview-Token': TOKEN, 'X-Forwarded-For': '127.0.0.1'})
    r = ask(client, CORPUS['positive'][0])
    assert r.status_code == 403, r.text
    assert 'envelope' not in r.json()


def test_api_key_does_not_install_a_live_transport(preview, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'present-but-must-never-be-used')
    r = preview.post(URL, json={'problem_text': CORPUS['positive'][0]['text']})
    assert r.status_code == 503
    assert r.json().get('reason_code') == 'OFFLINE_FIXTURE_REQUIRED'


def test_clients_cannot_supply_model_facts_or_enable_live(preview):
    r = preview.post(URL, json={'problem_text': CORPUS['positive'][0]['text'],
                               'facts': CORPUS['positive'][0]['payload'], 'allow_live_ai': True})
    assert r.status_code == 422


def test_llm_only_byte_parity_against_pre_wiring_baseline(monkeypatch):
    from tests.geometry.test_prism_production_route import _prism_p01_contract
    from app.simulation.geometry_compiler.routing import quyet_dinh_dinh_tuyen
    text, contract = _prism_p01_contract()
    program = quyet_dinh_dinh_tuyen(contract, {'GEOMETRY_COMPILER_MODE': 'DETERMINISTIC_FIRST'}).program
    async def analyze(*a, **k): return contract, None
    async def synthesize(*a, **k): return json.dumps(program)
    monkeypatch.setattr(PL, 'stage_semantic_analyze', analyze)
    monkeypatch.setattr(PL, 'call_gemini', synthesize)
    monkeypatch.setattr(main, '_cache_lookup', lambda *a: None)
    monkeypatch.setenv('GEMINI_API_KEY', 'offline-key')
    monkeypatch.delenv('GEOMETRY_COMPILER_MODE', raising=False)
    monkeypatch.setenv('SEMANTIC_TELEMETRY', '0')
    replies = []
    for enabled in ('0', '1'):
        monkeypatch.setenv('HYBRID_ROUTE_D_PREVIEW', enabled)
        r = TestClient(main.app).post('/api/analyze', json={'input': {'type': 'text', 'content': text}})
        assert r.status_code == 200 and r.json()['status'] == 'ok', r.text
        replies.append(r.json())
    assert replies[0] == replies[1]
    # Run `segment-witness-cache-invalidation` (CACHE_VERSION 127): the served prism scene now carries a certified
    # `segment3.perpendicular_witness` on each lateral edge AD, BE, CF — the ONLY intended difference from the
    # pre-wiring baseline. The historical digest is unchanged; it is compared with the witness removed.
    seg = [o for o in replies[0]['scene3d']['objects'] if o['type'] == 'segment3']
    assert {o['perpendicular_witness']['from']: o['perpendicular_witness']['foot_id']
            for o in seg if 'perpendicular_witness' in o} == {'D': 'A', 'E': 'B', 'F': 'C'}
    baseline = json.loads(json.dumps(replies[0]))
    for o in baseline['scene3d']['objects']:
        if o['type'] == 'segment3':
            o.pop('perpendicular_witness', None)
    digest = hashlib.sha256(json.dumps(baseline, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    print('PRE_WIRING_LLM_ONLY_SHA256=' + digest)
    # Captured on clean 6592306d before any product edit (canonical full HTTP response).
    assert digest == 'e6695fe6f9dfe2cdce9c005bd2b61fe42853b6eef87e6d6deae7d0250ad39f05'


@pytest.mark.parametrize('case', CORPUS['positive'], ids=lambda c: c['id'])
def test_endpoint_answers_match_independent_problem_expectations(preview, case):
    r = ask(preview, case)
    data = r.json()
    assert data['envelope']['status'] == 'ok', data
    for key, expected in case['expected_squared'].items():
        answer = data['route_d']['answer_exact'][key]
        assert independent_square(answer['coef']) == Fraction(expected)
    from tests.geometry.test_hybrid_backend_integration import _timeline_violations, verify_integrated_scene_mathematics
    assert _timeline_violations(data['envelope']['scene3d']) == []
    audit = verify_integrated_scene_mathematics(data['envelope']['scene3d'], scene_id=case['id'])
    assert audit.verdict == 'VERIFIED', audit.errors


@pytest.mark.parametrize('case', CORPUS['negative'], ids=lambda c: c['id'])
def test_endpoint_grounding_and_unsupported_inputs_fail_closed(preview, case):
    data = ask(preview, case).json()
    assert data['envelope']['status'] == 'unsupported', data
    assert data['envelope']['reason_code'] in case['expected_codes'], data
    assert 'scene3d' not in data['envelope'] and 'answers' not in data['route_d']
    assert 'source_fact_id' not in data['envelope']['learner_reason']


def proof_case():
    cases = json.loads((ROOT / 'backend/tests/geometry/fixtures/hybrid_holdout_cases.json').read_text(encoding='utf-8'))['cases']
    case = next(c for c in cases if c['id'] == 'H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED')
    return {'text': case['text'], 'payload': {'facts': deepcopy(case['b_facts'])}}


def test_symbolic_unit_and_goal_observation_survive_http_without_proof_promotion(preview):
    data = ask(preview, proof_case()).json()
    assert data['envelope']['status'] == 'ok', data
    meta = data['route_d']
    goal = meta['planner']['goal_checks']['f7']
    assert goal == {'evidence_state': 'TRUE_ON_CONFIGURATION', 'proof_status': 'UNVERIFIABLE',
                    'can_present_as_proven': False}
    assert meta['length_unit']['symbol'] == 'a' and meta['length_unit']['is_given'] is False
    assert data['envelope']['scene3d']['length_unit'] == meta['length_unit']
    assert meta['answer_exact']['f8']['dim'] == 3
    assert meta['answer_exact']['f8']['unit'] == 'a'
    assert independent_square(meta['answer_exact']['f8']['coef']) == Fraction(1, 3)
    assert 'đã chứng minh' not in data['envelope']['description'].lower()


@pytest.mark.parametrize('fault,code', [
    ('metric', 'METRIC_NOT_EUCLIDEAN'),
    ('unit', 'PREVIEW_LENGTH_UNIT_INVALID'),
    ('proof', 'PREVIEW_PROOF_STATUS_INVALID'),
    ('dependency', 'PREVIEW_DEPENDENCY_INVALID'),
    ('proof_text', 'PREVIEW_PROOF_TEXT_INVALID'),
    ('metric_mismatch', 'PREVIEW_METRIC_MISMATCH'),
    ('answer_unit', 'PREVIEW_LENGTH_UNIT_INVALID'),
    ('duplicate_object', 'PREVIEW_DEPENDENCY_INVALID'),
    ('surface', 'PREVIEW_SURFACE_CHANGED'),
    # review finding 3: each of these checks could be removed without any test failing
    ('proof_status', 'PREVIEW_PROOF_STATUS_INVALID'),
    ('negated_proven', 'PREVIEW_PROOF_STATUS_INVALID'),
    ('dependency_order', 'PREVIEW_DEPENDENCY_INVALID'),
    ('kernel_check', 'PREVIEW_RESULT_INVALID'),
    ('result_metric', 'PREVIEW_METRIC_MISMATCH'),
])
def test_adapter_refuses_corrupted_outputs_through_http(preview, monkeypatch, fault, code):
    from app.ai import hybrid_preview as HP
    real = HP.run_ai_fact_route
    def corrupt(*a, **kw):
        result = real(*a, **kw)
        assert result.status == 'SERVED'
        if fault == 'metric': result.scene3d['chart_metric'] = [['1','0','0'],['0','-1','0'],['0','0','1']]
        if fault == 'unit': result.scene3d.pop('length_unit')
        if fault == 'proof': result.planner['goal_checks']['f7']['can_present_as_proven'] = True
        if fault == 'dependency': result.scene3d['objects'][0]['depends'] = ['missing_object']
        if fault == 'proof_text': result.spec = result.spec.model_copy(update={'title': 'Đã chứng minh khẳng định trong đề'})
        if fault == 'metric_mismatch': result.scene3d['chart_metric'][0][0] = '999'
        if fault == 'answer_unit': result.answer_exact['f8']['unit'] = 'b'
        if fault == 'duplicate_object': result.scene3d['objects'].append(deepcopy(result.scene3d['objects'][0]))
        if fault == 'surface': result.ai['surface'] = 'different-surface'
        if fault == 'proof_status': result.planner['goal_checks']['f7']['proof_status'] = 'PROVEN'
        if fault == 'negated_proven':
            result.planner['negated_checks'] = {'fx': {'evidence_state': 'TRUE_ON_CONFIGURATION',
                                                       'proof_status': 'UNVERIFIABLE', 'can_present_as_proven': True}}
        if fault == 'dependency_order':
            s = result.scene3d
            born = {e['object'] for e in s['events'] if e.get('object')}
            o = next(o for o in s['objects'] if o['id'] in born and any(d in born for d in o.get('depends') or ()))
            dep = next(d for d in o['depends'] if d in born)
            last = max(e['step_index'] for e in s['events'])
            for e in s['events']:
                if e.get('object') == dep:
                    e['step_index'] = last
        if fault == 'kernel_check': result.kernel_check = False
        if fault == 'result_metric': result.metric = [['9', '0', '0'], ['0', '9', '0'], ['0', '0', '9']]
        return result
    monkeypatch.setattr(HP, 'run_ai_fact_route', corrupt)
    data = ask(preview, proof_case()).json()
    assert data['envelope']['status'] == 'unsupported', data
    assert data['envelope']['reason_code'] == code
    assert 'scene3d' not in data['envelope']


@pytest.mark.parametrize('tamper,code', [('planning','AUXILIARY_RULE_MISMATCH'), ('engine','ENGINE_SELF_CHECK_FAILED')])
def test_endpoint_catches_real_planning_and_engine_tampering(preview, monkeypatch, tamper, code):
    from dataclasses import replace
    from app.simulation.geometry_functions import registry, engine
    if tamper == 'planning':
        spec = registry.REGISTRY['ask_area']
        monkeypatch.setitem(registry.REGISTRY, 'ask_area', replace(spec, planning=replace(spec.planning, verifier='length')))
    else:
        monkeypatch.setattr(engine._Dung, '_dt2_tam_giac', lambda *a: Fraction(-1))
    data = ask(preview, CORPUS['positive'][0]).json()
    assert data['envelope']['status'] == 'unsupported', data
    assert data['envelope']['reason_code'] == code


def test_one_request_keeps_its_policy_contract_and_identity_during_env_flip(preview, monkeypatch):
    # Env and the module-global contract flip mid-request: the request keeps its snapshot. (A Registry/Planner/Engine
    # version change mid-request is refused instead — `test_route_d_identity_change_during_a_request_refuses`.)
    from app.ai import hybrid_preview as HP, fact_extraction
    policy = PL.route_policy_snapshot(preview=True)
    real = HP.run_ai_fact_route
    def flip(*a, **kw):
        assert kw['contract'] == 'flat'
        monkeypatch.setenv('HYBRID_ROUTE_D_PREVIEW', '0')
        monkeypatch.setattr(fact_extraction, 'RESPONSE_CONTRACT', 'v3')
        return real(*a, **kw)
    monkeypatch.setattr(HP, 'run_ai_fact_route', flip)
    data = ask(preview, CORPUS['positive'][0]).json()
    assert data['envelope']['status'] == 'ok'
    identity = data['route_d']['runtime_identity']
    assert identity['fingerprint'] == policy.fingerprint()
    assert identity['response_contract'] == 'flat'
    assert ask(preview, CORPUS['positive'][0]).status_code == 404


@pytest.mark.parametrize('module_name,attr', [('registry', 'REGISTRY_VERSION'), ('planner', 'PLANNER_VERSION'),
                                              ('engine', 'ENGINE_VERSION'), ('fact_extraction', 'SYSTEM_PROMPT'),
                                              ('hybrid_preview', 'ADAPTER_VERSION')])
def test_route_d_identity_change_during_a_request_refuses(preview, monkeypatch, module_name, attr):
    """Takeover (Claude): the snapshot names the Registry/Planner/Engine (and extraction surface / adapter) that the
    response claims to come from. If any differs once the request has executed, refuse."""
    from app.ai import fact_extraction, hybrid_preview as HP
    from app.simulation.geometry_functions import engine, planner, registry
    module = {'registry': registry, 'planner': planner, 'engine': engine, 'fact_extraction': fact_extraction,
              'hybrid_preview': HP}[module_name]
    real = HP.run_ai_fact_route

    def change_version(*a, **kw):
        monkeypatch.setattr(module, attr, getattr(module, attr) + '-changed-mid-request')
        return real(*a, **kw)

    monkeypatch.setattr(HP, 'run_ai_fact_route', change_version)
    data = ask(preview, CORPUS['positive'][0]).json()
    assert data['envelope']['status'] == 'unsupported', data
    assert data['envelope']['reason_code'] == 'PREVIEW_IDENTITY_CHANGED'
    assert 'scene3d' not in data['envelope'] and 'answers' not in data['route_d']


@pytest.mark.parametrize('state', ['off', 'unauthorized'])
@pytest.mark.parametrize('body', [{'problem_text': 'x', 'facts': []}, {'unexpected': 1}, 'not-json'])
def test_gate_answers_before_body_validation(preview, monkeypatch, state, body):
    """Takeover (Claude): FastAPI validated the body before the handler, so a disabled or unauthorized caller got a
    422 listing the body schema. The gate must answer first: 404 when off, 403 when not authorized."""
    if state == 'off':
        monkeypatch.delenv('HYBRID_ROUTE_D_PREVIEW')
    else:
        preview.headers['X-AlgoSim-Preview-Token'] = 'wrong'
    r = (preview.post(URL, content=body, headers={'content-type': 'application/json'}) if isinstance(body, str)
         else preview.post(URL, json=body))
    assert r.status_code == (404 if state == 'off' else 403), r.text
    assert 'problem_text' not in r.text and 'detail' not in r.json()


@pytest.mark.parametrize('body,code', [
    ({'candidates': [{'finishReason': 'MAX_TOKENS', 'content': {'parts': [{'text': '{}'}]}}]}, 'RESPONSE_TRUNCATED'),
    ({'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': 'không phải JSON'}]}}]}, 'JSON_INVALID'),
    ({'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': '{"facts": 3}'}]}}]}, 'MALFORMED_RESPONSE_PART'),
    ({'candidates': []}, 'NO_CANDIDATE'),
    ({'candidates': [{'finishReason': 'SAFETY'}]}, 'PROVIDER_REFUSED'),
])
def test_invalid_provider_responses_fail_closed_through_http(preview, body, code):
    """Takeover (Claude): malformed / truncated / refused provider responses keep their machine code and serve nothing."""
    text = CORPUS['positive'][0]['text']
    main.app.state.hybrid_preview_fixtures = {text: body}
    data = preview.post(URL, json={'problem_text': text}).json()
    assert data['envelope']['status'] == 'unsupported' and data['envelope']['reason_code'] == code, data
    assert 'scene3d' not in data['envelope'] and 'answers' not in data['route_d']


@pytest.mark.parametrize('value', ['0', '√0', '0a'])
def test_zero_length_source_value_is_refused_with_its_code_and_a_learner_message(preview, value):
    """Takeover (Claude): a degenerate given keeps NON_POSITIVE_LENGTH end to end; the learner text is Vietnamese with
    no unfilled template field or technical id."""
    from tests.geometry.test_hybrid_backend_integration import _regular_pyramid_facts
    text, payload = _regular_pyramid_facts('height', 'chiều cao', value)
    main.app.state.hybrid_preview_fixtures = {text: provider_body(payload)}
    env = preview.post(URL, json={'problem_text': text}).json()['envelope']
    assert (env['status'], env['reason_code']) == ('unsupported', 'NON_POSITIVE_LENGTH') and 'scene3d' not in env
    assert '{' not in env['learner_reason'] and 'NON_POSITIVE' not in env['learner_reason']


def test_health_with_preview_off_never_loads_route_d():
    """Review finding 1: `/api/health` (Docker healthcheck every 30 s, frontend) calls `runtime_identity()`, which loaded
    Route D even with the preview OFF — a research import error would make the product container unhealthy."""
    import os
    import subprocess
    import sys
    code = '''
import socket, sys
def blocked(*a, **kw): raise AssertionError('network forbidden')
socket.getaddrinfo = socket.create_connection = blocked
from fastapi.testclient import TestClient
from app.main import app
c = TestClient(app)
assert c.get('/api/health').status_code == 200
d = c.get('/api/diagnostics/runtime').json()
assert d['hybrid_route_d_preview'] == {'enabled': False}, d['hybrid_route_d_preview']
loaded = [m for m in sys.modules if m.startswith(('app.ai.hybrid_preview','app.ai.fact_extraction',
          'app.ai.function_calling','app.ai.function_route','app.simulation.geometry_functions'))]
assert not loaded, loaded
'''
    env = {k: v for k, v in os.environ.items() if k not in ('HYBRID_ROUTE_D_PREVIEW', 'HYBRID_ROUTE_D_PREVIEW_TOKEN')}
    env.update(ALLOW_LIVE_AI='0')
    r = subprocess.run([sys.executable, '-c', code], cwd=ROOT / 'backend', env=env, capture_output=True, text=True,
                       timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]


def test_diagnostics_say_whether_the_operator_token_is_usable(preview, monkeypatch):
    """Review finding 8: `enabled: true` with a missing/short token means every request is 403 — say so."""
    assert preview.get('/api/diagnostics/runtime').json()['hybrid_route_d_preview']['token_configured'] is True
    monkeypatch.setenv('HYBRID_ROUTE_D_PREVIEW_TOKEN', 'short')
    assert preview.get('/api/diagnostics/runtime').json()['hybrid_route_d_preview']['token_configured'] is False


def test_browser_origin_is_refused_even_with_the_token(preview):
    """Review finding 6: CORS allows any origin, and a page in the operator's browser connects from loopback; the
    token is then the only gate. An operator tool sends no Origin: refuse any request that carries one."""
    r = preview.post(URL, json={'problem_text': CORPUS['positive'][0]['text']},
                     headers={'Origin': 'https://evil.example'})
    assert r.status_code == 403 and r.json()['reason_code'] == 'PREVIEW_FORBIDDEN'


def test_refusal_does_not_echo_unverified_model_text(preview):
    """Review finding 2: on refusals the planner metadata carried model-supplied quotes that never passed the source
    check. A refusal keeps only the planner version and the goal/negated observations."""
    case = deepcopy(CORPUS['positive'][0])
    case['payload']['facts'][0]['quotes'] = ['INJECTED_NOT_IN_INPUT <script>']
    data = ask(preview, case).json()
    assert data['envelope']['status'] == 'unsupported', data
    assert 'INJECTED_NOT_IN_INPUT' not in json.dumps(data, ensure_ascii=False)
    assert set(data['route_d']['planner']) <= {'version', 'goal_checks', 'negated_checks'}
    # review finding 8: the grounding message branch named codes Route D never emits; it must fire for real ones
    assert data['envelope']['reason_code'] == 'QUOTE_NOT_IN_SOURCE'
    assert 'đối chiếu' in data['envelope']['learner_reason']


@pytest.mark.parametrize('text', [
    'Ta chứng minh được khẳng định',
    'Đã​chứng minh khẳng định',
    __import__('unicodedata').normalize('NFD', 'Đã chứng minh khẳng định'),
    'Vậy SC ⊥ BD (đpcm)',
    'Điều phải chứng minh',
    'Đã chứng-minh xong',
])
def test_proof_text_backstop_catches_variants(preview, monkeypatch, text):
    """Review finding 4: NFD, zero-width characters and common phrasings slipped past the proof-text backstop."""
    from app.ai import hybrid_preview as HP
    real = HP.run_ai_fact_route
    def corrupt(*a, **kw):
        result = real(*a, **kw)
        result.spec = result.spec.model_copy(update={'title': text})
        return result
    monkeypatch.setattr(HP, 'run_ai_fact_route', corrupt)
    data = ask(preview, proof_case()).json()
    assert data['envelope']['reason_code'] == 'PREVIEW_PROOF_TEXT_INVALID', data['envelope']


def test_live_flag_and_api_key_still_cannot_reach_a_provider(preview, monkeypatch):
    """Takeover (Claude): even ALLOW_LIVE_AI=1 with a key present, the preview has only fixture data — no transport."""
    import socket
    monkeypatch.setenv('ALLOW_LIVE_AI', '1')
    monkeypatch.setenv('GEMINI_API_KEY', 'present-but-must-never-be-used')

    def no_network(*a, **k):
        raise AssertionError('preview attempted network access')

    monkeypatch.setattr(socket, 'getaddrinfo', no_network)
    monkeypatch.setattr(socket, 'create_connection', no_network)
    r = preview.post(URL, json={'problem_text': CORPUS['positive'][0]['text']})
    assert r.status_code == 503 and r.json()['reason_code'] == 'OFFLINE_FIXTURE_REQUIRED'
    assert ask(preview, CORPUS['positive'][0]).json()['envelope']['status'] == 'ok'


def test_preview_policy_does_not_change_analyze_or_default_cache_identity(preview, monkeypatch):
    default = PL.route_policy_snapshot({})
    assert main._policy_identity(default) == main.CACHE_VERSION
    assert main._policy_identity(PL.route_policy_snapshot()) == main.CACHE_VERSION
    active = PL.route_policy_snapshot(preview=True)
    assert active.fingerprint() != default.fingerprint()
    with pytest.raises(ValueError): main._policy_identity(active)
    from app.simulation.geometry_functions import engine, planner, registry
    from app.ai import fact_extraction
    for module, name in [(engine,'ENGINE_VERSION'),(planner,'PLANNER_VERSION'),(registry,'REGISTRY_VERSION')]:
        with monkeypatch.context() as change:
            change.setattr(module, name, getattr(module, name) + '-changed')
            assert PL.route_policy_snapshot(preview=True).fingerprint() != active.fingerprint()
    with monkeypatch.context() as change:
        change.setattr(fact_extraction, 'SYSTEM_PROMPT', fact_extraction.SYSTEM_PROMPT + '\nchanged in test')
        assert PL.route_policy_snapshot(preview=True).fingerprint() != active.fingerprint()


def test_diagnostics_report_versions_and_state_but_no_secret(preview):
    from app.ai.hybrid_preview import preview_identity
    data = preview.get('/api/diagnostics/runtime').json()
    assert data['route_policy']['geometry_compiler_mode'] == 'LLM_ONLY'
    identity = data['hybrid_route_d_preview']
    assert identity['enabled'] is True
    for key, value in preview_identity().items(): assert identity[key] == value
    assert TOKEN not in json.dumps(data)
    assert URL not in preview.get('/openapi.json').json()['paths']


def test_default_runtime_never_loads_route_d_even_with_preview_flag_on(tmp_path, monkeypatch):
    from tests.geometry.test_structured_geometry_relations import _module_nap_luc_chay, _ROUTE_D
    monkeypatch.setenv('HYBRID_ROUTE_D_PREVIEW', '1')
    loaded = _module_nap_luc_chay(tmp_path)
    assert not any(name.startswith(_ROUTE_D) for name in loaded)


def test_endpoint_takes_one_policy_snapshot(preview, monkeypatch):
    calls = []
    real = main.route_policy_snapshot
    def snapshot(*a, **kw):
        calls.append(kw)
        return real(*a, **kw)
    monkeypatch.setattr(main, 'route_policy_snapshot', snapshot)
    assert ask(preview, CORPUS['positive'][0]).json()['envelope']['status'] == 'ok'
    assert calls == [{'preview': True}]


def test_disabled_http_request_does_not_import_route_d_or_use_network():
    import os
    import subprocess
    import sys
    code = '''
import socket, sys
def blocked(*a, **kw): raise AssertionError('network forbidden')
socket.getaddrinfo = socket.create_connection = blocked
from fastapi.testclient import TestClient
from app.main import app
r = TestClient(app, client=('127.0.0.1',1234)).post('/api/preview/hybrid', json={'problem_text':'Cho hình chóp S.ABCD.'})
assert r.status_code == 404, r.text
assert r.json()['reason_code'] == 'PREVIEW_DISABLED'
assert not any(m.startswith(('app.ai.hybrid_preview','app.ai.fact_extraction','app.ai.function_route','app.simulation.geometry_functions')) for m in sys.modules)
'''
    env = {**os.environ, 'HYBRID_ROUTE_D_PREVIEW': '0', 'ALLOW_LIVE_AI': '0'}
    r = subprocess.run([sys.executable, '-c', code], cwd=ROOT/'backend', env=env, capture_output=True, text=True, timeout=90)
    assert r.returncode == 0, r.stderr[-2000:]
