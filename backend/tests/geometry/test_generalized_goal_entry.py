"""Registered length goal slice through the real fact route, exact independent oracle."""
import hashlib
import json
import sys
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from app.ai.function_route import run_fact_route, run_function_route
from app.simulation.geometry_functions import planner, registry, engine
from tests.geometry.test_function_discovery_planning import squared, experimental_centroid_contract

ROOT=Path(__file__).resolve().parents[3]
RUN=ROOT/'docs/evaluation/geometry/runs/generalized-goal-entry'
C=json.loads((RUN/'corpus.json').read_text(encoding='utf-8'))


def run(c): return run_fact_route(c['text'],deepcopy(c['payload']))


def exact(r,c):
    assert r.status=='SERVED',(r.code,r.reason)
    assert set(r.answers)==set(c['expected_squared'])
    for q,x in c['expected_squared'].items():
        assert squared(r.exec_result.final_memory['kq_'+q])==Fraction(x)


@pytest.mark.parametrize('c',C['positive'],ids=lambda c:c['id'])
def test_length_goal_exact(c): exact(run(c),c)


_CODE_DEVIATION={'contradictory-length':'Registered code INCONSISTENT_CONSTRAINTS differs from existing INCONSISTENT_FACTS; label preserved',
                 # still refused (asserted in test_source_grounding_reliability.py); M1 names the dropped ask itself
                 'unread-second-ask':'Request coverage (M1, run hybrid-semantic-grounding-reliability) refuses REQUEST_NOT_ANSWERED, '
                                     'not the registered QUESTION_CONTEXT_UNSUPPORTED / NOT_ASKED_IN_SOURCE; label preserved'}
@pytest.mark.parametrize('c',[pytest.param(c,marks=pytest.mark.xfail(strict=True,reason=_CODE_DEVIATION[c['id']]))
                            if c['id'] in _CODE_DEVIATION else c for c in C['negative']],ids=lambda c:c['id'])
def test_length_goal_refusal(c):
    r=run(c); assert r.status=='REFUSED'
    assert r.code in c['expected_codes'],(r.code,r.reason)


@pytest.mark.parametrize('c',C['discovery'],ids=lambda c:c['id'])
def test_new_producer_contract_needs_no_planner_change(monkeypatch,c):
    # Wave 2A promoted the contract unchanged: the claim stays a data toggle on the same code.
    assert registry.REGISTRY['centroid'].planning==experimental_centroid_contract(registry).planning
    with monkeypatch.context() as m:
        m.setitem(registry.REGISTRY,'centroid',replace(registry.REGISTRY['centroid'],planning=None))
        assert run(c).status=='REFUSED'
    exact(run(c),c)
    assert {x['fn'] for x in run(c).planner['calls']} >= {'centroid','ask_length'}


def test_goal_contract_removal_and_registry_reversal(monkeypatch):
    c=C['positive'][0]; before=planner.lap_ke_hoach(c['payload'],c['text'])
    with monkeypatch.context() as m:
        m.setitem(registry.REGISTRY,'ask_length',replace(registry.REGISTRY['ask_length'],planning_extra=()))
        assert run(c).status=='REFUSED'
    with monkeypatch.context() as m:
        reversed_registry=dict(reversed(list(registry.REGISTRY.items())))
        m.setattr(planner,'REGISTRY',reversed_registry)
        assert planner.lap_ke_hoach(c['payload'],c['text']).calls==before.calls


def test_repeated_goals_share_only_construction():
    c=deepcopy(C['positive'][0]); f=deepcopy(c['payload']['facts'][-1]); f['id']='q2'
    c['payload']['facts'].append(f); c['expected_squared']['q2']=c['expected_squared']['q']
    r=run(c); exact(r,c)
    assert len([x for x in r.planner['calls'] if x['fn']=='midpoint'])==1


@pytest.mark.parametrize('transform',['reverse-points','reverse-facts','rename','scale'])
def test_metamorphic_lengths(transform):
    c=deepcopy(C['positive'][0])
    if transform=='reverse-points': c['payload']['facts'][-1]['points'].reverse()
    elif transform=='reverse-facts': c['payload']['facts'].reverse()
    elif transform=='rename':
        c=json.loads(json.dumps(c,ensure_ascii=False).replace('S','T').replace('C','E'))
    else:
        c['text']=c['text'].replace('cạnh 2','cạnh 4').replace('SA = 3','SA = 6')
        for f in c['payload']['facts']:
            f['quotes']=[q.replace('cạnh 2','cạnh 4').replace('SA = 3','SA = 6') for q in f['quotes']]
            if f.get('value') in ('2','3'): f['value']=str(int(f['value'])*2)
        c['expected_squared']={q:str(Fraction(x)*4) for q,x in c['expected_squared'].items()}
    exact(run(c),c)


@pytest.mark.parametrize('labels',[[],['S'],['GHOST'],['M','M']])
def test_certificate_labels_cannot_forge_scene_provenance(labels):
    old=json.loads((RUN.parent/'goal-directed-function-discovery/corpus.json').read_text(encoding='utf-8'))['positive'][0]
    k=planner.lap_ke_hoach(old['payload'],old['text']); aux=deepcopy(k.auxiliary)
    aux[0]['labels']=labels
    r=run_function_route(old['text'],{'calls':k.calls},tuple(aux))
    assert r.status=='REFUSED' and r.code=='AUXILIARY_RULE_MISMATCH'


@pytest.mark.parametrize('field',['target','effect','env','quotes','labels','missing'])
def test_length_certificate_tampering_refuses(field):
    c=C['positive'][0]; k=planner.lap_ke_hoach(c['payload'],c['text']); aux=deepcopy(k.auxiliary); d=aux[0]
    if field=='target': d['target']={'point':'D'}
    elif field=='effect': d['chain'][-1]['effect']='AnswerDistance'
    elif field=='env': d['chain'][-1]['env']['Q']='D'
    elif field=='quotes': d['quotes']=['SA = 3.']
    elif field=='labels': d['labels']=['S']
    else: aux=[]
    assert run_function_route(c['text'],{'calls':k.calls},tuple(aux)).status=='REFUSED'


def test_engine_answer_disagreement_refuses(monkeypatch):
    monkeypatch.setattr(engine._Dung,'kc2_dich',lambda self,d:Fraction(-1))
    assert run(C['positive'][0]).code=='ENGINE_SELF_CHECK_FAILED'


@pytest.mark.parametrize('bound',['MAX_EFFECT_DEPTH','MAX_EFFECT_NEEDS','MAX_EFFECT_CANDIDATES','MAX_RESULT_FEET','MAX_CALLS'])
def test_budget_exhaustion_never_serves_partial(monkeypatch,bound):
    monkeypatch.setattr(planner,bound,0)
    assert run(C['positive'][0]).code=='PLAN_TOO_LARGE'


def test_transport_schema_is_unchanged():
    pin=json.loads((RUN/'baseline/transport.json').read_text(encoding='utf-8'))
    value=json.dumps(planner.TypedFact.model_json_schema(),sort_keys=True,ensure_ascii=False).encode()
    assert hashlib.sha256(value).hexdigest()==pin['typed_fact_schema_sha256']


def test_registered_contradiction_code_deviation_is_safe():
    assert run(next(c for c in C['negative'] if c['id']=='contradictory-length')).code=='INCONSISTENT_FACTS'


@pytest.mark.parametrize('reverse',[False,True])
def test_mixed_length_and_distance_share_midpoint(reverse):
    c=deepcopy(C['positive'][0]); q='Tính khoảng cách từ trung điểm của SC đến (SAB).'
    c['text']+=' '+q
    c['payload']['facts'].append(dict(id='distance',kind='question',role='question',quantity='distance',
        point_kind='midpoint',points=['S','C'],points_b=['S','A','B'],quotes=[q]))
    c['expected_squared']['distance']='1'
    if reverse: c['payload']['facts'].reverse()
    r=run(c); exact(r,c)
    assert len([x for x in r.planner['calls'] if x['fn']=='midpoint'])==1


def test_lying_answer_template_is_caught_independently(monkeypatch):
    spec=registry.REGISTRY['ask_length']; c=spec.planning_extra[0]
    lie=replace(c,call=(('segment',('Q','Q')),))
    monkeypatch.setitem(registry.REGISTRY,'ask_length',replace(spec,planning_extra=(lie,)))
    assert run(C['positive'][0]).code=='ENGINE_SELF_CHECK_FAILED'


def test_lying_descriptor_contract_is_caught_independently(monkeypatch):
    c=experimental_centroid_contract(registry).planning
    lie=replace(c,call=(('point','G'),('segment',('A','B'))))
    monkeypatch.setitem(registry.REGISTRY,'midpoint',replace(registry.REGISTRY['midpoint'],planning=lie))
    # the honest centroid contract (Wave 2A) would win the tie by name: remove it so the lie is the only producer
    monkeypatch.setitem(registry.REGISTRY,'centroid',replace(registry.REGISTRY['centroid'],planning=None))
    assert run(C['discovery'][0]).code=='ENGINE_SELF_CHECK_FAILED'


def test_existing_named_midpoint_is_reused():
    c=deepcopy(C['positive'][0]); quote='Gọi N là trung điểm của SC.'
    c['text']=c['text'].replace('Tính độ dài',quote+' Tính độ dài')
    c['payload']['facts'].insert(4,dict(id='n',kind='point_def',role='premise',point='N',point_kind='midpoint',
        points=['S','C'],quotes=[quote]))
    r=run(c); exact(r,c)
    cert=r.planner['auxiliary'][0]
    assert cert['labels']==[] and cert['operand']['label']=='N'
