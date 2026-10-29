"""Terminal semantic refusal and scoped legacy identity: Owner W3-F2 amendment."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.ai import adapter3_simulation as A
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions import typed_fact_next_bridge as B
from app.simulation.geometry_functions.registry import TuChoi

RUN=Path(__file__).resolve().parents[3]/'docs/evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding'
SUP=json.loads((RUN/'inputs/recovery-supplementary.json').read_text(encoding='utf-8'))
DEV=json.loads((RUN/'inputs/development.json').read_text(encoding='utf-8'))['cases']

def control():return deepcopy(SUP['control'])
def compiler(payload=None):
    c=A._Adapter3Compiler(B.parse_typed_fact_next(payload or control()))
    c._compile_solids()
    return c

@pytest.mark.parametrize('code',['SOURCE_OBJECT_MISMATCH','UNKNOWN_SOLID_ID','AMBIGUOUS_REFERENCE',
                               'INCONSISTENT_FACTS','BRIDGE_INCONSISTENT_SECTION','UNCLASSIFIED_BRIDGE_FAILURE'])
def test_semantic_bridge_refusal_is_terminal_without_legacy_compile(monkeypatch,code):
    invoked=[]
    def refuse(_p):raise TuChoi(code,'typed refusal')
    original=A._Adapter3Compiler._compile_solids
    def compile_spy(c):invoked.append(True);return original(c)
    monkeypatch.setattr(B,'bridge',refuse)
    monkeypatch.setattr(A._Adapter3Compiler,'_compile_solids',compile_spy)
    r=A.run_typed_fact_next_route(control())
    assert not invoked and (r.status,r.code)==('REFUSED',code)

def test_planner_semantic_refusal_is_terminal(monkeypatch):
    from app.simulation.geometry_functions import planner
    def refuse(*_a,**_k):raise TuChoi('AMBIGUOUS_REFERENCE','typed planner refusal')
    monkeypatch.setattr(planner,'lap_ke_hoach',refuse)
    r=A.run_typed_fact_next_route(control())
    assert (r.status,r.code)==('REFUSED','AMBIGUOUS_REFERENCE')

@pytest.mark.parametrize('ref,sid,code',[('S','s2','SOURCE_OBJECT_MISMATCH'),
    ('S','foreign','UNKNOWN_SOLID_ID'),('s1::S','s2','SOURCE_OBJECT_MISMATCH')])
def test_explicit_scope_never_uses_global_or_conflicting_namespace(ref,sid,code):
    with pytest.raises(TuChoi) as e:compiler().resolve_ref(ref,sid,'p3')
    assert e.value.code==code

def test_optional_scope_resolves_only_unique_identity():
    c=compiler()
    assert c.resolve_ref('S')=='S'
    assert c.resolve_ref('S','s1')=='S'
    c._bind_local_point('s2','S','S2')
    with pytest.raises(TuChoi) as e:c.resolve_ref('S')
    assert e.value.code=='AMBIGUOUS_REFERENCE'

def test_constructed_point_cannot_be_borrowed_by_other_scope():
    c=compiler();c._bind_local_point('s1','M','M')
    with pytest.raises(TuChoi) as e:c.resolve_ref('M','s2')
    assert e.value.code=='SOURCE_OBJECT_MISMATCH'

@pytest.mark.parametrize('cid',['DEV-NEG-08','DEV-NEG-23'])
@pytest.mark.parametrize('canonical',[False,True])
def test_original_unknown_scopes_agree_across_adapters(cid,canonical):
    p=deepcopy(next(c['payload'] for c in DEV if c['id']==cid))
    if canonical:
        for prem in p['premises']:
            a=prem['args'];old=prem['quote']
            if prem['kind']=='divide_segment':
                x,y=a['segment'];new=f"Gọi {a['point']} là điểm thuộc cạnh {x}{y} sao cho {x}{a['point']} = {a['ratio']} {x}{y}"
            elif prem['kind']=='orthogonal_projection':
                new=f"Hình chiếu vuông góc của {a['point']} lên mặt phẳng ({''.join(a['plane'])}) là {a['image']}"
            else:continue
            prem['quote']=new;p['problem_text']=p['problem_text'].replace(old,new)
    p['schema_version']='typed-fact-next/1'
    # These /2 sections use no stated cuts, hence are also valid /1 structures.
    for sec in p['derived_sections']:sec.pop('stated_intersections',None)
    r3=A.run_typed_fact_next_route(p)
    r4=run_typed_fact_next_v2_route({**p,'schema_version':'typed-fact-next/2'})
    assert (r3.status,r3.code)==(r4.status,r4.code)==('REFUSED','UNKNOWN_SOLID_ID')

def test_known_solid_scope_verdict_agrees_across_adapters():
    p=deepcopy(SUP['invalid_scope'])
    r3=A.run_typed_fact_next_route(p)
    r4=run_typed_fact_next_v2_route({**p,'schema_version':'typed-fact-next/2'})
    assert (r3.status,r3.code)==(r4.status,r4.code)==('REFUSED','SOURCE_OBJECT_MISMATCH')

def test_real_unsupported_qualified_identity_preserves_legacy_exact_positive():
    data=json.loads((RUN.parent/'typedfact-next-adapter3-simulation/corpus-dev.json').read_text(encoding='utf-8'))
    c=next(x for x in data['cases'] if x['case_id']=='A3-DEV-02')
    with pytest.raises(TuChoi) as e:B.bridge(c['payload'])
    assert e.value.code=='BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY'
    r=A.run_typed_fact_next_route(c['payload'])
    assert r.status=='SERVED' and r.answer_exact==c['oracle_exact']
    assert r.source_verification['authority']==A.LEGACY_SOURCE_AUTHORITY

@pytest.mark.parametrize('invalid',['scope','number'])
def test_unsupported_translation_still_checks_scope_and_source(monkeypatch,invalid):
    def unsupported(_p):raise TuChoi('BRIDGE_UNSUPPORTED_PREMISE','capability unavailable')
    monkeypatch.setattr(B,'bridge',unsupported)
    p=deepcopy(SUP['invalid_scope']) if invalid=='scope' else control()
    if invalid=='number':p['premises'][2]['args']['value']='4'
    r=A.run_typed_fact_next_route(p)
    assert (r.status,r.code)==('REFUSED','SOURCE_OBJECT_MISMATCH' if invalid=='scope' else 'SOURCE_NUMBER_MISMATCH')

@pytest.mark.parametrize('kind',['ratio','projection'])
def test_legacy_unsupported_cannot_mix_solid_operands(monkeypatch,kind):
    def unsupported(_p):raise TuChoi('BRIDGE_UNSUPPORTED_PREMISE','capability unavailable')
    monkeypatch.setattr(B,'bridge',unsupported)
    p=control()
    if kind=='ratio':
        prem={'kind':'divide_segment','solid_id':'s2','args':{'point':'M','segment':['S','A'],'ratio':'1/3'},
              'quote':'Gọi M thuộc đoạn SA sao cho SM = 1/3 SA.'}
    else:
        prem={'kind':'orthogonal_projection','solid_id':'s2','args':{'point':'S','image':'A','plane':list('ABCD')},
              'quote':'Hình chiếu vuông góc của S lên mặt phẳng (ABCD) là A.'}
    p['premises'].append(prem);p['problem_text']+=' '+prem['quote']
    r=A.run_typed_fact_next_route(p)
    assert (r.status,r.code)==('REFUSED','SOURCE_OBJECT_MISMATCH')
