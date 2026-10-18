"""Preview contract hardening: refusal classification in the existing vocabularies, the proof-text backstop, and the
offline envelope fixtures. Every refusal here goes through the real endpoint (`tests/test_hybrid_preview_api.py`)."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import re
import unicodedata

import pytest

import app.main as main
from tests.test_hybrid_preview_api import CORPUS, ROOT, URL, ask, preview, proof_case, provider_body  # noqa: F401

HOLD = {c['id']: c for c in json.loads(
    (ROOT / 'backend/tests/geometry/fixtures/hybrid_holdout_cases.json').read_text(encoding='utf-8'))['cases']}


def hold(case_id):
    return {'text': HOLD[case_id]['text'], 'payload': {'facts': deepcopy(HOLD[case_id]['b_facts'])}}


def corpus(case_id, group='negative'):
    case = next(c for c in CORPUS[group] if c['id'] == case_id)
    return {'text': case['text'], 'payload': deepcopy(case['payload'])}


def proof_only():
    """The committed derivation of `test_hybrid_safety_readiness.test_proof_only_request_without_certificate_refuses`."""
    case = HOLD['H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED']
    text = case['text']
    for fact in case['b_facts']:
        if fact['kind'] == 'question':
            for quote in fact['quotes']:
                text = text.replace(quote, '')
    return {'text': text, 'payload': {'facts': [f for f in deepcopy(case['b_facts']) if f['kind'] != 'question']}}


def zero_height():
    from tests.geometry.test_hybrid_backend_integration import _regular_pyramid_facts
    text, payload = _regular_pyramid_facts('height', 'chiều cao', '0')
    return {'text': text, 'payload': payload}


def not_json():
    return {'text': CORPUS['positive'][0]['text'],
            'body': {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': 'không phải JSON'}]}}]}}


def _served_fault(mutate):
    def install(monkeypatch):
        from app.ai import hybrid_preview as HP
        real = HP.run_ai_fact_route

        def corrupt(*a, **kw):
            result = real(*a, **kw)
            assert result.status == 'SERVED'
            mutate(result, monkeypatch)
            return result
        monkeypatch.setattr(HP, 'run_ai_fact_route', corrupt)
    install.__name__ = mutate.__name__   # the fixture exporter records the injection by this name
    return install


def _engine_self_check(monkeypatch):
    from app.simulation.geometry_functions import engine
    monkeypatch.setattr(engine._Dung, '_dt2_tam_giac', lambda *a: Fraction(-1))


def _change_registry_version(result, monkeypatch):
    from app.simulation.geometry_functions import registry
    monkeypatch.setattr(registry, 'REGISTRY_VERSION', registry.REGISTRY_VERSION + '-changed-mid-request')


def _promote(result, monkeypatch):
    result.planner['goal_checks']['f7']['proof_status'] = 'PROVEN'


def _scene_metric(result, monkeypatch):
    result.scene3d['chart_metric'] = [['1', '0', '0'], ['0', '-1', '0'], ['0', '0', '1']]


def _kernel_check(result, monkeypatch):
    result.kernel_check = False


def _surface(result, monkeypatch):
    result.ai['surface'] = 'different-surface'


GG, VG, IS, CG = 'geometry_generation_failed', 'verification_gap', 'insufficient_specification', 'capability_gap'

#: (id, input, fault, reason_code, failure_category, refusal_cause) — one row per refusal group, each a real input or a
#: declared fault on a real served result.
CASES = [
    # capability gap
    ('capability-unsupported', lambda: hold('H08_PLANE_PLANE_NOT_BASE'), None, 'UNSUPPORTED_CAPABILITY', CG, 'UNKNOWN'),
    ('capability-conditional', lambda: corpus('conditional-question'), None, 'CONDITIONAL_CLAUSE', CG, 'UNKNOWN'),
    ('capability-negated-question', lambda: corpus('negated-question'), None, 'NEGATED_CLAUSE', CG, 'UNKNOWN'),
    # missing / ambiguous data
    ('missing-dimension', lambda: hold('H10_CUBOID_MISSING_HEIGHT'), None, 'MISSING_DIMENSION', IS, 'UNKNOWN'),
    ('missing-underdetermined', lambda: hold('H06_QUANTITY_NOT_UNIQUE'), None, 'UNDERDETERMINED_POINT', IS, 'UNKNOWN'),
    ('missing-ambiguous', lambda: corpus('ambiguous-fact'), None, 'AMBIGUOUS_FACT', IS, 'UNKNOWN'),
    # contradictory / degenerate data
    ('invalid-contradiction', lambda: hold('H09_CUBE_CONTRADICTION'), None, 'INCONSISTENT_FACTS', GG, 'UNKNOWN'),
    ('invalid-collinear', lambda: corpus('collinear-triangle-unnamed-midpoint'), None, 'COLLINEAR_POINTS', GG, 'UNKNOWN'),
    ('invalid-zero-length', zero_height, None, 'NON_POSITIVE_LENGTH', GG, 'SOURCE'),
    # source not verified
    ('source-object-mismatch', lambda: corpus('wrong-source-target'), None, 'SOURCE_OBJECT_MISMATCH', VG, 'UNKNOWN'),
    ('source-goal-as-premise', lambda: corpus('prove-role'), None, 'GOAL_CLAUSE_NOT_PREMISE', VG, 'UNKNOWN'),
    ('source-request-unanswered', lambda: corpus('unread-second-ask'), None, 'REQUEST_NOT_ANSWERED', VG, 'UNKNOWN'),
    # result / certificate not verified
    ('result-kernel-check', proof_case, _served_fault(_kernel_check), 'PREVIEW_RESULT_INVALID', VG, 'UNKNOWN'),
    ('result-scene-metric', proof_case, _served_fault(_scene_metric), 'METRIC_NOT_EUCLIDEAN', VG, 'UNKNOWN'),
    ('result-engine-self-check', lambda: deepcopy(CORPUS['positive'][0]), _engine_self_check,
     'ENGINE_SELF_CHECK_FAILED', VG, 'UNKNOWN'),
    # cannot conclude
    ('inconclusive-figure', lambda: hold('H05_FIGURE_NOT_UNIQUE_QUANTITY_UNIQUE'), None, 'FIGURE_NOT_UNIQUE', VG, 'UNKNOWN'),
    ('inconclusive-negated', lambda: hold('H13_NEGATED_RELATION_CONTRADICTS'), None, 'NEGATED_CLAUSE', VG, 'UNKNOWN'),
    ('inconclusive-proof-only', proof_only, None, 'PROOF_UNVERIFIABLE', VG, 'UNKNOWN'),
    # extraction / provider output
    ('extraction-fact-incomplete', lambda: corpus('missing-target-point'), None, 'FACT_INCOMPLETE', GG, 'UNKNOWN'),
    ('extraction-not-json', not_json, None, 'JSON_INVALID', GG, 'UNKNOWN'),
    # integrity / identity
    ('integrity-identity', proof_case, _served_fault(_change_registry_version), 'PREVIEW_IDENTITY_CHANGED', GG, 'UNKNOWN'),
    ('integrity-proof-status', proof_case, _served_fault(_promote), 'PREVIEW_PROOF_STATUS_INVALID', GG, 'UNKNOWN'),
    ('integrity-surface', proof_case, _served_fault(_surface), 'PREVIEW_SURFACE_CHANGED', GG, 'UNKNOWN'),
]


def _post(client, case):
    body = case.get('body') or provider_body(case['payload'])
    main.app.state.hybrid_preview_fixtures = {case['text']: body}
    r = client.post(URL, json={'problem_text': case['text']})
    assert r.status_code == 200, r.text
    return r.json()


def _quotes(case):
    return [q for f in (case.get('payload') or {}).get('facts', []) for q in f.get('quotes') or ()]


@pytest.mark.parametrize('cid,build,fault,code,category,cause', CASES, ids=[c[0] for c in CASES])
def test_refusal_is_classified_in_the_existing_vocabulary(preview, monkeypatch, cid, build, fault, code, category,
                                                          cause):
    case = build()
    if fault:
        fault(monkeypatch)
    data = _post(preview, case)
    env = data['envelope']
    assert (env['status'], env['reason_code'], env['failure_category'], env.get('refusal_cause')) == \
        ('unsupported', code, category, cause), env
    assert set(env) == {'status', 'reason_code', 'reason', 'learner_reason', 'failure_category', 'refusal_cause'}
    assert set(data['route_d']['planner']) <= {'version', 'goal_checks', 'negated_checks'}
    assert 'scene3d' not in env and 'answers' not in data['route_d']
    # learner text: Vietnamese, no machine token, no template field, no trace, no model-supplied quote
    text = env['learner_reason']
    assert text == env['reason'] and re.search('[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]', text)
    assert '_' not in text and '{' not in text and code not in text
    assert not re.search(r'Error|Exception|Traceback|capability|verification|PREVIEW', text)
    assert not [q for q in _quotes(case) if len(q) > 12 and q in text]


def test_integrity_and_unknown_codes_are_never_a_capability_verdict():
    from app.ai.hybrid_preview import classify_refusal
    for code in ('PREVIEW_IDENTITY_CHANGED', 'PREVIEW_SURFACE_CHANGED', 'PREVIEW_PROOF_STATUS_INVALID',
                 'PREVIEW_VALIDATION_FAILED', 'A_CODE_NOBODY_EMITS_YET'):
        assert classify_refusal(code, adapter=code.startswith('PREVIEW_')).failure_category != 'capability_gap', code
    unknown = classify_refusal('A_CODE_NOBODY_EMITS_YET')
    assert (unknown.group, unknown.failure_category, unknown.refusal_cause) == \
        ('FALLBACK', 'geometry_generation_failed', 'UNKNOWN')


#: Literals in the Route D modules that are not refusal codes.
_NOT_REFUSAL = {'TRUE_ON_CONFIGURATION', 'FALSE_ON_CONFIGURATION', 'LAYOUT_DERIVED', 'GEOMETRY_CONSTRUCTION'}
_ROUTE_D_SOURCES = ('app/simulation/geometry_functions/registry.py', 'app/simulation/geometry_functions/planner.py',
                    'app/simulation/geometry_functions/engine.py', 'app/simulation/geometry_functions/__init__.py',
                    'app/ai/function_route.py', 'app/ai/fact_extraction.py')
#: The polyhedral kernel Route D executes; its `GeometryError` codes reach the preview unchanged (`TuChoi(e.code, …)`).
_KERNEL_SOURCES = ('app/simulation/geometry/exact.py', 'app/simulation/geometry/kernel.py',
                   'app/simulation/geometry/measure.py', 'app/simulation/geometry/metric.py',
                   'app/simulation/geometry/section.py', 'app/simulation/geometry/predicates.py',
                   'app/simulation/geometry/radical.py')


def _route_d_refusal_literals():
    backend = ROOT / 'backend'
    codes = set()
    for rel in _ROUTE_D_SOURCES:
        codes |= set(re.findall(r'["\']([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)["\']', (backend / rel).read_text(encoding='utf-8')))
    for rel in _KERNEL_SOURCES:
        path = backend / rel
        if path.exists():
            codes |= set(re.findall(r'^ERR_[A-Z_]+\s*=\s*"([A-Z0-9_]+)"', path.read_text(encoding='utf-8'), re.M))
    return codes - _NOT_REFUSAL


def test_every_literal_route_d_refusal_code_is_classified():
    """Lock: a new Route D / kernel refusal code must be placed in a group before it can ship (else FALLBACK)."""
    from app.ai.hybrid_preview import classify_refusal
    codes = _route_d_refusal_literals()
    assert {'INCONSISTENT_FACTS', 'COLLINEAR_POINTS', 'QUOTE_NOT_IN_SOURCE', 'PROOF_UNVERIFIABLE'} <= codes
    missing = sorted(c for c in codes if classify_refusal(c).group == 'FALLBACK')
    assert missing == [], missing


def test_every_adapter_refusal_code_is_classified():
    from app.ai import hybrid_preview as HP
    source = Path(HP.__file__).read_text(encoding='utf-8')
    codes = set(re.findall(r'(?:PreviewInvalid|_refusal)\(\s*"([A-Z0-9_]+)"', source))
    assert {'PREVIEW_IDENTITY_CHANGED', 'METRIC_NOT_EUCLIDEAN', 'PREVIEW_VALIDATION_FAILED'} <= codes
    assert sorted(c for c in codes if HP.classify_refusal(c, adapter=True).group == 'FALLBACK') == []


# ── proof-text backstop ─────────────────────────────────────────────────────────────────────────────────────────


def _with_title(monkeypatch, title):
    from app.ai import hybrid_preview as HP
    real = HP.run_ai_fact_route

    def retitle(*a, **kw):
        result = real(*a, **kw)
        result.spec = result.spec.model_copy(update={'title': title})
        return result
    monkeypatch.setattr(HP, 'run_ai_fact_route', retitle)


@pytest.mark.parametrize('text', [
    'Đã chứng−minh xong',          # U+2212 MINUS SIGN (review NIT of hybrid-route-d-preview-wiring)
    'Đã chứng − minh xong',
    'Đã chứng➖minh xong',          # U+2796 HEAVY MINUS SIGN
    'Đã chứng﹣minh xong',          # U+FE63 SMALL HYPHEN-MINUS
    'Đã chứng－minh xong',          # U+FF0D FULLWIDTH HYPHEN-MINUS
    'Đã chứng⸺minh xong',          # U+2E3A TWO-EM DASH (Pd outside U+2010–U+2015)
    'Đã chứng˗minh xong',          # U+02D7 MODIFIER LETTER MINUS SIGN
    'Đã ｃｈứｎｇ minh',  # fullwidth Latin letters
    'Chứng minh thành công',        # NO-BREAK SPACE
    'Đã chứng­minh xong',           # SOFT HYPHEN (format character)
])
def test_proof_claim_variants_are_refused(preview, monkeypatch, text):
    _with_title(monkeypatch, text)
    data = ask(preview, proof_case()).json()
    assert data['envelope']['reason_code'] == 'PREVIEW_PROOF_TEXT_INVALID', (text, data['envelope'])
    assert data['envelope']['failure_category'] == 'verification_gap'


@pytest.mark.parametrize('text', [
    'Tính AB − CD và thể tích khối chóp',
    'Cần chứng minh rằng SC ⊥ BD; hình chỉ minh họa',
    'Hình dựng chứng tỏ một cấu hình thoả đề',
    'Độ dài a−b, góc 90°, x² − 1',
])
def test_valid_mathematical_text_is_served_unchanged(preview, monkeypatch, text):
    _with_title(monkeypatch, text)
    data = ask(preview, proof_case()).json()
    assert data['envelope']['status'] == 'ok', data['envelope']
    assert data['envelope']['title'] == text   # normalisation is for detection only: the served text is byte-identical


def test_promoted_proof_status_is_refused_without_the_text_backstop(preview, monkeypatch):
    """The regex is a backstop: the structural invariant refuses a promoted observation on its own."""
    from app.ai import hybrid_preview as HP
    monkeypatch.setattr(HP, '_noi_chung_minh', lambda text: False)
    _served_fault(_promote)(monkeypatch)
    data = ask(preview, proof_case()).json()
    assert data['envelope']['reason_code'] == 'PREVIEW_PROOF_STATUS_INVALID'


SERVED_INPUTS = ([(c['id'], lambda c=c: {'text': c['text'], 'payload': deepcopy(c['payload'])}) for c in CORPUS['positive']]
                 + [(k, lambda k=k: hold(k)) for k in sorted(HOLD) if HOLD[k]['expect_b']['status'] == 'SERVED'])


@pytest.mark.parametrize('cid,build', SERVED_INPUTS, ids=[c[0] for c in SERVED_INPUTS])
def test_every_served_observation_stays_unverifiable(preview, cid, build):
    data = ask(preview, build()).json()
    assert data['envelope']['status'] == 'ok', data['envelope']
    for group in ('goal_checks', 'negated_checks'):
        for observation in data['route_d']['planner'].get(group, {}).values():
            assert observation['proof_status'] == 'UNVERIFIABLE' and observation['can_present_as_proven'] is False
    assert data['envelope']['description'] == \
        'Quan sát mô hình dựng từ dữ kiện; các kiểm tra trên hình không phải chứng minh tổng quát.'
    assert unicodedata.normalize('NFC', data['envelope']['description']) == data['envelope']['description']
