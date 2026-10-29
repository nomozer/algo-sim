"""Terminal semantic refusal and scoped legacy identity: Owner W3-F2 amendment."""
from copy import deepcopy
import json
from pathlib import Path
import inspect
import textwrap

import pytest

from app.ai import adapter3_simulation as A
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions import typed_fact_next_bridge as B
from app.simulation.geometry_functions.registry import TuChoi
from app.simulation.geometry_functions.typed_fact_next import PremiseSpec

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

@pytest.mark.parametrize('output',['s2::M','foreign::M','T'])
def test_legacy_construction_output_cannot_create_or_borrow_foreign_ownership(output):
    p=control()
    p['premises'].append({'kind':'orthogonal_projection','solid_id':'s1',
        'args':{'point':'S','image':output,'plane':list('ABCD')},
        'quote':f'Hình chiếu vuông góc của S lên mặt phẳng (ABCD) là {output}.'})
    p['problem_text']+=' '+p['premises'][-1]['quote']
    expected='UNKNOWN_SOLID_ID' if output.startswith('foreign') else 'SOURCE_OBJECT_MISMATCH'
    if '::' in output:
        # The unified scope policy now refuses the qualified declaration itself, with the same code ...
        r=A.run_typed_fact_next_route(p);assert (r.status,r.code)==('REFUSED',expected)
        # ... and the legacy producer-scope defence below it still holds when the schema is bypassed.
        base=B.parse_typed_fact_next(control())
        payload=base.model_copy(update={'problem_text':p['problem_text'],
                                        'premises':(*base.premises,PremiseSpec.model_construct(**p['premises'][-1]))})
        c=A._Adapter3Compiler(payload);c._compile_solids()
    else:
        c=compiler(p)
    with pytest.raises(TuChoi) as e:c._compile_premises()
    assert e.value.code==expected

def test_optional_scope_constructed_point_inherits_verified_producer_scope():
    p=control()
    p['premises'].append({'kind':'midpoint','args':{'point':'M','segment':['S','A']},'quote':'M là trung điểm của SA.'})
    p['problem_text']+=' M là trung điểm của SA.'
    c=compiler(p);c._compile_premises()
    assert c.resolve_ref('M','s1')=='M'
    with pytest.raises(TuChoi) as e:c.resolve_ref('M','s2')
    assert e.value.code=='SOURCE_OBJECT_MISMATCH'

def test_absent_unique_optional_scope_is_served_with_exact_answer():
    p=control();p['solids']=p['solids'][:1];p['premises']=p['premises'][:3]
    for prem in p['premises']:prem.pop('solid_id')
    p['problem_text']=p['problem_text'].split(' Cho hình chóp T.ABCD.')[0]
    r=A.run_typed_fact_next_route(p)
    # With numeric lengths, dim is the exponent of a symbolic unit (none), not the physical quantity's degree.
    assert r.status=='SERVED' and r.answer_exact['v']=={'coef':'4','dim':0,'unit':None}

def test_absent_ambiguous_scope_is_refused_with_reason():
    p=control()
    p['premises'][0].pop('solid_id')
    r=A.run_typed_fact_next_route(p)
    assert (r.status,r.code)==('REFUSED','AMBIGUOUS_REFERENCE')

def test_qualified_containment_chain_is_typed_geometry_not_a_single_vertex():
    solids={s.solid_id:s for s in B.parse_typed_fact_next(control()).solids}
    B._check_qualified_refs({'container_ref':'s1::SA'},solids)
    for value,code in [('foreign::SA','UNKNOWN_SOLID_ID'),('s1::TA','UNKNOWN_VERTEX_REF')]:
        with pytest.raises(TuChoi) as e:B._check_qualified_refs({'container_ref':value},solids)
        assert e.value.code==code
    with pytest.raises(TuChoi) as e:B._check_qualified_refs({'point':'s1::SA'},solids)
    assert e.value.code=='UNKNOWN_VERTEX_REF'

# Solid-valued operands (`height`/`altitude` `solid`, goal `target.solid`, section goals) vs the declared scope:
# final-review MAJOR reproduced at takeover (`codex-to-claude-takeover.md` §3, H1–H3).
A3DEV=json.loads((RUN.parent/'typedfact-next-adapter3-simulation/corpus-dev.json').read_text(encoding='utf-8'))['cases']
def a3dev02():return deepcopy(next(x for x in A3DEV if x['case_id']=='A3-DEV-02'))
def legacy_only(monkeypatch):
    def unsupported(_p):raise TuChoi('BRIDGE_UNSUPPORTED_PREMISE','capability unavailable')
    monkeypatch.setattr(B,'bridge',unsupported)
def refused_or_exact(r,code,exact):
    if code:assert (r.status,r.code)==('REFUSED',code)
    else:assert r.status=='SERVED' and r.answer_exact==exact

@pytest.mark.parametrize('sid,named,code',[('pyr1','pyr2','SOURCE_OBJECT_MISMATCH'),('pyr1','D.ABC','SOURCE_OBJECT_MISMATCH'),
    ('pyr2','pyr2',None),('pyr2','D.ABC',None),(None,'pyr2',None)])
def test_real_legacy_height_solid_must_agree_with_premise_scope(sid,named,code):
    c=a3dev02();p=c['payload'];quote='Chiều cao hình chóp D.ABC bằng a.'
    prem={'kind':'height','args':{'solid':named,'value':'a'},'quote':quote}
    if sid:prem['solid_id']=sid
    p['premises'].append(prem);p['problem_text']+=' '+quote
    with pytest.raises(TuChoi) as e:B.bridge(p)
    # Valid inputs reach the genuine capability gap; a contradiction is refused before it by the unified policy (I7).
    assert e.value.code==(code or 'BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY')
    refused_or_exact(A.run_typed_fact_next_route(p),code,c['oracle_exact'])

@pytest.mark.parametrize('kind',['height','altitude'])
def test_legacy_solid_operand_cannot_override_premise_scope(monkeypatch,kind):
    legacy_only(monkeypatch)
    p=control()
    args={'solid':'s2','value':'3'} if kind=='height' else {'solid':'s2','apex':'S','foot':'A'}
    quote='Chiều cao SA bằng 3.' if kind=='height' else 'SA là đường cao của hình chóp.'
    p['premises'].append({'kind':kind,'solid_id':'s1','args':args,'quote':quote});p['problem_text']+=' '+quote
    r=A.run_typed_fact_next_route(p)
    assert (r.status,r.code)==('REFUSED','SOURCE_OBJECT_MISMATCH')

VOLUME_SCOPES=[('s2','s1','SOURCE_OBJECT_MISMATCH'),('foreign','s1','UNKNOWN_SOLID_ID'),
               ('s1','T.ABCD','SOURCE_OBJECT_MISMATCH'),('s1','s1',None),(None,'s1',None)]
@pytest.mark.parametrize('legacy',[False,True])
@pytest.mark.parametrize('goal_sid,target,code',VOLUME_SCOPES)
def test_volume_goal_target_must_agree_with_goal_scope(monkeypatch,legacy,goal_sid,target,code):
    if legacy:legacy_only(monkeypatch)
    p=control();g=p['math_goals'][0];g['target']={'solid':target};g['solid_id']=goal_sid
    refused_or_exact(A.run_typed_fact_next_route(p),code,{'v':{'coef':'4','dim':0,'unit':None}})

@pytest.mark.parametrize('goal_sid,target,code',[x for x in VOLUME_SCOPES if x[2]])
def test_bridge_and_adapter4_refuse_conflicting_volume_goal_scope(goal_sid,target,code):
    p=control();g=p['math_goals'][0];g['target']={'solid':target};g['solid_id']=goal_sid
    with pytest.raises(TuChoi) as e:B.bridge(p)
    assert e.value.code==code
    r4=run_typed_fact_next_v2_route({**p,'schema_version':'typed-fact-next/2'})
    assert (r4.status,r4.code)==('REFUSED',code)

@pytest.mark.parametrize('goal_sid,code',[('pyr2','SOURCE_OBJECT_MISMATCH'),('foreign','UNKNOWN_SOLID_ID'),('pyr1',None)])
def test_real_legacy_volume_goal_scope(goal_sid,code):
    c=a3dev02();c['payload']['math_goals'][1]['solid_id']=goal_sid
    refused_or_exact(A.run_typed_fact_next_route(c['payload']),code,c['oracle_exact'])

@pytest.mark.parametrize('goal_sid',[None,'foreign'])
def test_legacy_section_area_goal_scope_must_exist(monkeypatch,goal_sid):
    legacy_only(monkeypatch)
    p=deepcopy(next(c['payload'] for c in DEV if c['id']=='W3-B02'));p['schema_version']='typed-fact-next/1'
    for sec in p['derived_sections']:sec.pop('stated_intersections',None)
    g=next(g for g in p['math_goals'] if g.get('goal_type')=='area')
    if goal_sid:g['solid_id']=goal_sid
    r=A.run_typed_fact_next_route(p)
    assert (r.status,r.code)==(('REFUSED','UNKNOWN_SOLID_ID') if goal_sid else ('SERVED',None))

@pytest.mark.parametrize('sid,code',[('s1','UNKNOWN_SOLID_ID'),(None,'UNKNOWN_SOLID')])
def test_unknown_named_solid_refuses_with_scope_or_planner_code(sid,code):
    # Without a declared scope the Bridge makes no scope claim; the planner's locked UNKNOWN_SOLID stands (N006).
    p=control();prem={'kind':'height','args':{'solid':'s99','value':'3'},'quote':'Chiều cao bằng 3.'}
    if sid:prem['solid_id']=sid
    p['premises'].append(prem);p['problem_text']+=' '+prem['quote']
    r4=run_typed_fact_next_v2_route({**p,'schema_version':'typed-fact-next/2'})
    assert (r4.status,r4.code)==('REFUSED',code)
    assert A.run_typed_fact_next_route(p).status=='REFUSED'

@pytest.mark.parametrize('owner,needle',[(B,'if sid is not None and sid != resolved[0]:'),(B,'if sid is not None and sid not in solids:'),
    (A._Adapter3Compiler,'if scope is not None and name != self.solid_canonical_name[scope]:'),
    (A._Adapter3Compiler,'if scope is not None and scope not in self.solid_canonical_name:')])
def test_solid_scope_oracles_kill_guard_removal(monkeypatch,owner,needle):
    name='_pham_vi_khoi' if owner is B else '_scoped_solid_name'
    source=textwrap.dedent(inspect.getsource(getattr(owner,name)))
    assert source.count(needle)==1
    namespace=dict(vars(B if owner is B else A));exec(compile(source.replace(needle,'if False:'),'<solid-scope-mutant>','exec'),namespace)
    monkeypatch.setattr(owner,name,namespace[name])
    # The unified schema policy now refuses these inputs first, so the oracle exercises this defence-in-depth layer
    # directly: named operand vs declared scope, same codes as before.
    solids={s.solid_id:s for s in B.parse_typed_fact_next(control()).solids};c=compiler()
    def oracle():
        for named,scope,code in (('s2','s1','SOURCE_OBJECT_MISMATCH'),('s1','foreign','UNKNOWN_SOLID_ID')):
            try:
                B._pham_vi_khoi(named,scope,solids,'g') if owner is B else c._scoped_solid_name(named,scope,'g')
            except TuChoi as e:
                assert e.code==code;continue
            except Exception as e:
                raise AssertionError(f'untyped failure {e!r}') from None
            assert False,'conflicting scope accepted'
    with pytest.raises(AssertionError):oracle()

@pytest.mark.parametrize('mutant',['remove_terminal_guard','remove_scope_guard','replace_scope_with_default','allow_global_lookup'])
def test_safety_oracles_kill_semantic_and_scope_mutants(monkeypatch,mutant):
    if mutant=='remove_terminal_guard':
        source=inspect.getsource(A._shared_source_gate)
        needle='if exc.code not in _LEGACY_BRIDGE_CAPABILITIES:'
        assert source.count(needle)==1
        source=source.replace(needle,'if False:')
        namespace=dict(vars(A));exec(compile(source,'<terminal-guard-mutant>','exec'),namespace)
        monkeypatch.setattr(A,'_shared_source_gate',namespace['_shared_source_gate'])
        def refuse(_p):raise TuChoi('SOURCE_OBJECT_MISMATCH','typed refusal')
        monkeypatch.setattr(B,'bridge',refuse)
        invoked=[];original=A._Adapter3Compiler._compile_solids
        def spy(c):invoked.append(True);return original(c)
        monkeypatch.setattr(A._Adapter3Compiler,'_compile_solids',spy)
        A.run_typed_fact_next_route(deepcopy(SUP['invalid_scope']))
        with pytest.raises(AssertionError):assert not invoked,'legacy invoked after semantic refusal'
        return
    source=textwrap.dedent(inspect.getsource(A._Adapter3Compiler.resolve_ref))
    needle='if sid is not None:'
    assert source.count(needle)==1
    if mutant=='remove_scope_guard':source=source.replace(needle,'if False:')
    elif mutant=='allow_global_lookup':source=source.replace(needle,'if sid is not None and label not in self.unqualified_map:')
    else:
        needle='sid = explicit_sid or default_solid_id'
        assert source.count(needle)==1
        source=source.replace(needle,'sid = explicit_sid or next(iter(self.solid_specs))')
    namespace=dict(vars(A));exec(compile(source,'<scope-mutant>','exec'),namespace)
    monkeypatch.setattr(A._Adapter3Compiler,'resolve_ref',namespace['resolve_ref'])
    c=compiler()
    def refusal_oracle():
        try:c.resolve_ref('S','s2','p3')
        except TuChoi as e:
            assert e.code=='SOURCE_OBJECT_MISMATCH';return
        assert False,'foreign reference resolved'
    with pytest.raises(AssertionError):refusal_oracle()
