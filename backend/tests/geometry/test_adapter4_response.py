"""The product /4 response boundary uses real V2 → planner → exact-engine results."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.ai import adapter4_route as A


CASES = json.loads((Path(__file__).resolve().parents[3] /
    'docs/evaluation/geometry/runs/hybrid-contract-v2/grammar-set.json').read_text(encoding='utf-8'))['cases']


@pytest.fixture
def served():
    case = next(c for c in CASES if c['id'] == 'PARA-0')
    return deepcopy(case['payload']), A.run_typed_fact_next_v2_route(case['payload'])


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['id'])
def test_real_grammar_results_have_consumer_wrappers(case):
    r = A.run_typed_fact_next_v2_route(case['payload'])
    response = A.build_adapter4_response(r, case['payload']['problem_text'])
    assert response['schema_version'] == A.ROUTE_D_SIMULATION_V4_SCHEMA_VERSION
    assert response['route_d']['status'] == r.status
    if r.status == 'SERVED':
        assert response['envelope']['status'] == 'ok'
        assert response['envelope']['scene3d'] == r.scene3d
        assert response['route_d']['answer_exact'] == r.answer_exact
    else:
        assert response['envelope']['reason_code'] == r.code
        assert response['route_d']['refusal'] == {'code': r.code}
        assert 'scene3d' not in response['envelope']
        assert 'answers' not in response['route_d']


@pytest.mark.parametrize('fault', ['kernel', 'spec', 'metric', 'authority', 'answers', 'scene_answer', 'unit',
                                  'closure', 'sections', 'proof', 'proof_text', 'source', 'symbolic',
                                  'point', 'dimension', 'planner_version', 'missing_answer', 'closure_rule'])
def test_served_tampering_refuses_without_success_data(served, fault):
    payload, r = served
    text = payload['problem_text']
    if fault == 'kernel': r.kernel_check = False
    elif fault == 'spec': r.spec = None
    elif fault == 'metric': r.scene3d['chart_metric'][0][0] = '9'
    elif fault == 'authority': r.route_d['source_verification']['authority'] = 'legacy'
    elif fault == 'answers': r.route_d['answer_exact'] = {}
    elif fault == 'scene_answer':
        next(o for o in r.scene3d['objects'] if o['type'] == 'quantity')['value'] = '999'
    elif fault == 'unit': r.route_d['length_unit'] = 'b'
    elif fault == 'closure': r.route_d['sections'][0]['closure_certificate']['verified'] = False
    elif fault == 'closure_rule': r.route_d['sections'][0]['closure_certificate']['rule'] = 'invented-rule'
    elif fault == 'sections': r.route_d['sections'] = []
    elif fault == 'proof': r.planner['goal_checks'] = {'invented': {'proof_status': 'PROVED', 'can_present_as_proven': True}}
    elif fault == 'proof_text': r.scene3d['events'][0]['learner_text'] = 'Đã chứng minh thành công.'
    elif fault == 'source': text = 'Một đề khác không có các dữ kiện đã cho.'
    elif fault == 'symbolic':
        r.answers['g_ratio'] = r.route_d['answers']['g_ratio'] = '999'
    elif fault == 'point':
        next(o for o in r.scene3d['objects'] if o['id'] == 'S')['xyz'] = ['100', '100', '100']
    elif fault == 'dimension':
        for answer in (r.answer_exact['g_ratio'], r.route_d['answer_exact']['g_ratio']):
            answer.update(dim=3, unit='a')
    elif fault == 'planner_version': r.planner['version'] = 'obsolete-planner/0'
    elif fault == 'missing_answer':
        for answers in (r.answers, r.answer_exact, r.route_d['answers'], r.route_d['answer_exact']):
            answers.pop('g_ratio')
    response = A.build_adapter4_response(r, text)
    assert response['envelope']['status'] == 'unsupported'
    assert response['route_d']['status'] == 'REFUSED'
    assert response['route_d']['refusal']['code'] == response['envelope']['reason_code']
    assert set(response['route_d']) == {'schema_version', 'adapter_version', 'contract_version', 'status', 'refusal'}
    assert 'scene3d' not in response['envelope']


def test_response_copies_and_refusal_never_leaks_prior_scene_or_raw_error(served):
    payload, r = served
    first = A.build_adapter4_response(r, payload['problem_text'])
    first['envelope']['scene3d']['objects'].clear()
    assert r.scene3d['objects']
    r.status, r.code, r.reason = 'REFUSED', 'ROUTE_INTERNAL_ERROR', 'SECRET_TRACEBACK'
    r.failed_calls = ('SECRET_CALL',)
    response = A.build_adapter4_response(r, payload['problem_text'])
    assert 'SECRET' not in json.dumps(response)
    assert 'scene3d' not in response['envelope']
    assert 'sections' not in response['route_d']


def test_source_with_unread_new_goal_cannot_relabel_served_result(served):
    payload, r = served
    response = A.build_adapter4_response(r, payload['problem_text'] + ' Tính độ dài SB.')
    assert response['envelope']['status'] == 'unsupported'
    assert response['route_d']['status'] == 'REFUSED'
    assert 'scene3d' not in response['envelope']
