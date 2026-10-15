"""Locked development corpus through the real fact route, never a direct-IR serve."""
from __future__ import annotations

import json
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

import pytest

from app.ai.function_route import run_fact_route

ROOT = Path(__file__).resolve().parents[3]
CORPUS_PATH = ROOT / "docs/evaluation/geometry/runs/goal-directed-planner-generalization-audit/next-slice-corpus.json"
CORPUS = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def squared(value):
    from app.simulation.geometry.radical import Radical
    return Fraction(value.he) ** 2 * value.can if isinstance(value, Radical) else Fraction(value) ** 2


@pytest.mark.parametrize("case", CORPUS["positive"], ids=lambda c: c["id"])
def test_locked_positive_real_route(case):
    r = run_fact_route(case["text"], case["payload"])
    assert r.status == "SERVED", (r.code, r.reason)
    asks = [f["id"] for f in case["payload"]["facts"] if f["kind"] == "question"]
    assert set(r.answers) == set(asks)
    for q in asks:
        assert squared(r.exec_result.final_memory[f"kq_{q}"]) == Fraction(case["expected_squared"])
    assert r.kernel_check and r.scene3d["objects"]
    statements = r.program["statements"]
    lines = [s for s in statements if s.get("expr", {}).get("kind") == "intersect_plane_plane"]
    feet = [s for s in statements if s.get("expr", {}).get("kind") == "project_onto" and s.get("kind") == "construct_point"]
    assert len(lines) == len(feet) == 1
    assert feet[0]["expr"]["target"] == lines[0]["target_var"]
    assert statements.index(lines[0]) < statements.index(feet[0])


@pytest.mark.parametrize("case", CORPUS["negative"], ids=lambda c: c["id"])
def test_locked_negative_fail_closed(case):
    r = run_fact_route(case["text"], case["payload"])
    assert r.status == "REFUSED", (r.answers, case["id"])
    expected = case["expected_code"]
    if expected == "closed source refusal":
        assert r.code in {"SOURCE_PREMISE_UNREAD", "SOURCE_OBJECT_MISMATCH", "LOCAL_SOURCE_BINDING_UNVERIFIED"}
    elif expected == "dependency cycle refusal":
        assert r.code == "DEPENDENCY_CYCLE"
    else:
        assert r.code == expected
    assert not r.answers and r.scene3d is None


def named_case(supplied=False):
    c = deepcopy(CORPUS['positive'][0])
    c['payload']['facts'] = [f for f in c['payload']['facts'] if f['id'] != 'g']
    q = c['payload']['facts'][-1]
    q.pop('line_ref')
    q.update(points_a=['S'], points_b=['B', 'D'], quotes=['Tính khoảng cách từ S đến BD.'])
    c['text'] = c['text'][:c['text'].index('Tìm giao tuyến')] + q['quotes'][0]
    if supplied:
        quote = 'Gọi J là hình chiếu vuông góc của S lên BD.'
        c['payload']['facts'].insert(0, {'id':'foot', 'kind':'projection', 'role':'premise',
                                       'point':'S','at':'J','points':['B','D'],'quotes':[quote]})
        c['text'] = c['text'].replace(q['quotes'][0], quote + ' ' + q['quotes'][0])
    return c


def test_registry_has_individual_planning_effects_not_a_recipe():
    from app.simulation.geometry_functions.registry import REGISTRY
    specs = [REGISTRY[n] for n in ('intersection_line','orthogonal_projection_line','ask_length')]
    assert all(getattr(s, 'planning', None) is not None for s in specs)
    assert {s.planning.effect.kind for s in specs} == {'Line','Foot','AnswerDistance'}


def test_supplied_named_foot_is_reused_even_before_its_inputs():
    c = named_case(supplied=True)
    r = run_fact_route(c['text'], c['payload'])
    assert r.status == 'SERVED', (r.code,r.reason)
    projections = [x for x in r.planner['calls'] if x['fn']=='orthogonal_projection_line']
    assert len(projections)==1
    ask = next(x for x in r.planner['calls'] if x['id']=='q')
    assert ask['args']['segment']==['S','J']
    assert squared(r.exec_result.final_memory['kq_q'])==11


def gram_dot(a,b,g):
    return sum(a[i]*g[i][j]*b[j] for i in range(3) for j in range(3))


def xyz(v):
    return v.x,v.y,v.z


@pytest.mark.parametrize('case',CORPUS['positive'],ids=lambda c:c['id'])
def test_independent_incidence_gram_and_causal_oracle(case):
    # Algorithm independence: affine covectors and Gram minimization, no Kernel projection/intersection helper.
    from tests.geometry.hybrid_compiler_benchmark import sub,cross,dot
    from app.simulation.geometry_functions.engine import ir_name
    r=run_fact_route(case['text'],case['payload'])
    assert r.status=='SERVED', (r.code,r.reason)
    line=r.exec_result.final_memory['gt_g']
    origin,direction=xyz(line.point),xyz(line.direction)
    g=tuple(tuple(Fraction(v) for v in row) for row in r.metric)
    producer=next(f for f in case['payload']['facts'] if f['id']=='g')
    for labels in (producer['points_a'],producer['points_b']):
        a,b,c=(r.points[v] for v in labels)
        covector=cross(sub(b,a),sub(c,a))
        assert any(covector) and any(direction)
        assert dot(covector,sub(origin,a))==dot(covector,direction)==0
    for cert in r.planner['auxiliary']:
        if not cert.get('effect_binding'):
            continue
        point,foot=r.points[cert['point']],r.points[cert['label']]
        assert not any(cross(sub(foot,origin),direction))
        assert gram_dot(sub(point,foot),direction,g)==0
        w=sub(point,origin)
        minimum=gram_dot(w,w,g)-gram_dot(w,direction,g)**2/gram_dot(direction,direction,g)
        assert minimum==Fraction(case['expected_squared'])
        assert gram_dot(sub(point,foot),sub(point,foot),g)==minimum
        obj=next(o for o in r.scene3d['objects'] if o['id']==ir_name(cert['label']))
        assert 'gt_g' in obj['depends']
        created={e['object']:e['step_index'] for e in r.scene3d['events'] if e.get('action')=='CREATE'}
        assert created['gt_g'] < created[obj['id']]
        if minimum:
            assert obj.get('perpendicular_witness')
        else:
            assert not obj.get('perpendicular_witness')
    resolved=next(i for i,s in enumerate(r.trace) if s['step']=='resolve_line')
    consumed=next(i for i,s in enumerate(r.trace) if s.get('result_binding')=='g')
    assert resolved < consumed


@pytest.mark.parametrize('variant',['registry-order','facts-order','plane-order','plane-orientation','rename','collision'])
def test_result_binding_metamorphic(variant,monkeypatch):
    from app.simulation.geometry_functions import registry
    c=deepcopy(CORPUS['positive'][0])
    if variant=='registry-order':
        monkeypatch.setattr(registry,'REGISTRY',dict(reversed(list(registry.REGISTRY.items()))))
        # Planner imports the same catalog object in production; replace its reference for this catalog mutation.
        from app.simulation.geometry_functions import planner
        monkeypatch.setattr(planner,'REGISTRY',registry.REGISTRY)
    elif variant=='facts-order':
        c['payload']['facts'].reverse()
    elif variant in ('plane-order','plane-orientation'):
        f=next(f for f in c['payload']['facts'] if f['id']=='g')
        if variant=='plane-order':
            f['points_a'],f['points_b']=f['points_b'],f['points_a']
        else:
            f['points_a'].reverse()
            f['points_b'].reverse()
    elif variant=='rename':
        # Simultaneous substitution; no geometry compared by generated auxiliary point names.
        import re
        names={'S':'V','A':'E','B':'F','C':'G','D':'K','M':'N'}
        def replace_names(v):
            if isinstance(v,dict):return {k:replace_names(x) for k,x in v.items()}
            if isinstance(v,list):return [replace_names(x) for x in v]
            if isinstance(v,str):return re.sub(r'[A-Z]+(?![a-z])',lambda m:''.join(names.get(x,x) for x in m[0]),v)
            return v
        c['text']=replace_names(c['text'])
        # Keep opaque IDs, kind, measure and shape unchanged.
        for f in c['payload']['facts']:
            for key in ('quotes','solid','points','points_a','points_b','point','at'):
                if key in f:f[key]=replace_names(f[key])
    else:
        c['text']=c['text'].replace('Gọi M','Gọi H là trung điểm AD. Gọi H1 là trung điểm BC. Gọi M')
        c['payload']['facts'] += [{'id':name,'kind':'point_def','role':'premise','point':name,'point_kind':'midpoint',
                                  'points':pts,'quotes':[f'Gọi {name} là trung điểm {"".join(pts)}.']}
                                 for name,pts in [('H',['A','D']),('H1',['B','C'])]]
    r=run_fact_route(c['text'],c['payload'])
    assert r.status=='SERVED',(r.code,r.reason)
    assert squared(r.exec_result.final_memory['kq_q'])==Fraction(10,11)
    if variant=='collision':
        assert next(d['label'] for d in r.planner['auxiliary'] if d.get('effect_binding'))=='H2'


@pytest.mark.parametrize('bound,value',[('MAX_EFFECT_DEPTH',1),('MAX_EFFECT_NEEDS',1),('MAX_EFFECT_CANDIDATES',1),
                                      ('MAX_RESULT_LINES',0),('MAX_RESULT_FEET',0),('MAX_CALLS',2)])
def test_effect_budgets_refuse_without_partial_result(bound,value,monkeypatch):
    from app.simulation.geometry_functions import planner
    monkeypatch.setattr(planner,bound,value)
    c=CORPUS['positive'][0]
    r=run_fact_route(c['text'],c['payload'])
    assert r.status=='REFUSED' and r.code=='PLAN_TOO_LARGE'
    assert not r.answers and r.scene3d is None


def test_catalog_effect_removal_cannot_be_bypassed_by_a_recipe(monkeypatch):
    from dataclasses import replace
    from app.simulation.geometry_functions.registry import REGISTRY
    monkeypatch.setitem(REGISTRY,'orthogonal_projection_line',replace(REGISTRY['orthogonal_projection_line'],planning=None))
    for c in (CORPUS['positive'][0],named_case()):
        r=run_fact_route(c['text'],c['payload'])
        assert r.status=='REFUSED' and r.code=='UNSUPPORTED_CAPABILITY'


def test_effect_dependency_cycle_is_detected(monkeypatch):
    from dataclasses import replace
    from app.simulation.geometry_functions.registry import REGISTRY
    spec=REGISTRY['orthogonal_projection_line']
    cyclic=replace(spec.planning,inputs=(spec.planning.effect,))
    monkeypatch.setitem(REGISTRY,spec.name,replace(spec,planning=cyclic))
    c=CORPUS['positive'][0]
    r=run_fact_route(c['text'],c['payload'])
    assert r.status=='REFUSED' and r.code=='DEPENDENCY_CYCLE'


def test_explicit_derived_foot_reuse_and_fake_provider():
    from app.ai.fact_extraction import run_ai_fact_route
    c=deepcopy(CORPUS['positive'][0])
    quote='Gọi J là hình chiếu vuông góc của M lên giao tuyến của (SAC) và (SBD).'
    c['text']=c['text'].replace('Tính khoảng cách',quote+' Tính khoảng cách')
    c['payload']['facts'].insert(0,{'id':'foot','kind':'projection','point':'M','at':'J','line_ref':'g',
                                  'role':'premise','quotes':[quote]})
    requests=[]
    def fake(request):
        requests.append(request)
        return {'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(c['payload'])}]}}]}
    r=run_ai_fact_route(c['text'],fake)
    assert r.status=='SERVED',(r.code,r.reason)
    assert len([x for x in r.planner['calls'] if x['fn']=='orthogonal_projection_line'])==1
    assert next(x for x in r.planner['calls'] if x['id']=='q')['args']['segment']==['M','J']
    schema=requests[0]['generationConfig']['responseSchema']['properties']['facts']['items']
    assert 'line_ref' in schema['properties']
    assert 'tools' not in requests[0] and 'PlanningContract' not in json.dumps(schema)


def test_segment_source_is_not_served_as_an_infinite_line():
    c=deepcopy(CORPUS['positive'][0])
    old=c['payload']['facts'][-1]['quotes'][0]
    new=old.replace('đến giao tuyến','đến đoạn giao tuyến')
    c['text']=c['text'].replace(old,new)
    c['payload']['facts'][-1]['quotes']=[new]
    r=run_fact_route(c['text'],c['payload'])
    assert r.status=='REFUSED' and r.code=='SOURCE_OBJECT_MISMATCH'


def test_route_a_cannot_claim_a_result_reference_certificate():
    from app.ai.function_route import run_function_route
    c=CORPUS['positive'][0]
    r=run_fact_route(c['text'],c['payload'])
    untrusted=run_function_route(c['text'],{'calls':r.planner['calls']})
    assert untrusted.status=='REFUSED' and untrusted.code=='RESULT_BINDING_UNVERIFIED'


@pytest.mark.parametrize('mutation',['missing-quote','source-proof','source-condition','source-negation','unread-outside-quote',
                                   'reference-and-endpoints','four-point-plane','wrong-binding'])
def test_result_reference_source_adversaries(mutation):
    from app.ai.function_route import run_function_route
    c=deepcopy(CORPUS['positive'][0])
    producer=next(f for f in c['payload']['facts'] if f['id']=='g')
    if mutation=='missing-quote':
        producer['quotes']=['Tìm giao tuyến của (SAB) và (SBD).']
    elif mutation.startswith('source-'):
        old=producer['quotes'][0]
        prefix={'source-proof':'Chứng minh rằng ', 'source-condition':'Nếu ', 'source-negation':'Không tồn tại '}[mutation]
        new=prefix+old
        c['text']=c['text'].replace(old,new)
        producer['quotes']=[new]  # lie about role/negation in transport; source authority must catch it
    elif mutation=='unread-outside-quote':
        c['text']=c['text'].replace('SA = 3.','SA = 3. SB vuông góc với (ABCD).')
    elif mutation=='reference-and-endpoints':
        c['payload']['facts'][-1]['points_b']=['B','D']
    elif mutation=='four-point-plane':
        producer['points_a']=['S','A','B','C']
    else:
        good=run_fact_route(c['text'],c['payload'])
        cert=deepcopy(good.planner['auxiliary'])
        cert[0]['point']='A'
        r=run_function_route(c['text'],{'calls':good.planner['calls']},tuple(cert))
        assert r.status=='REFUSED' and not r.answers
        return
    r=run_fact_route(c['text'],c['payload'])
    assert r.status=='REFUSED' and not r.answers and r.scene3d is None,(r.code,r.answers)


def test_source_request_role_for_line_producer_is_not_assumed_given():
    c=deepcopy(CORPUS['positive'][0])
    next(f for f in c['payload']['facts'] if f['id']=='g')['role']='question'
    r=run_fact_route(c['text'],c['payload'])
    assert r.status=='SERVED',(r.code,r.reason)
    assert next(s for s in r.trace if s['step']=='resolve_line')['provenance']=='DERIVED'


@pytest.mark.parametrize('scale',[2,3])
def test_source_dimension_scaling_changes_metric_not_recipe(scale):
    c=deepcopy(CORPUS['positive'][0])
    for f in c['payload']['facts']:
        if f.get('value'):
            old=f['quotes'][0]
            f['value']=str(int(f['value'])*scale)
            f['quotes']=[old.replace('cạnh 2',f'cạnh {2*scale}').replace('= 3',f'= {3*scale}')]
            c['text']=c['text'].replace(old,f['quotes'][0])
    r=run_fact_route(c['text'],c['payload'])
    assert r.status=='SERVED',(r.code,r.reason)
    assert squared(r.exec_result.final_memory['kq_q'])==Fraction(10,11)*scale**2
    assert len([x for x in r.planner['calls'] if x['fn']=='orthogonal_projection_line'])==1


def test_metric_translation_and_chart_scaling_of_real_planned_ir():
    # Full route produces the plan first. Replay its exact IR in a different affine chart; never count as a serve.
    from app.simulation.geometry import metric
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    from app.simulation.semantic_program.validator import validate_semantic_program
    c=CORPUS['positive'][2]  # oblique Gram: Euclidean coordinate dot would give the wrong answer
    r=run_fact_route(c['text'],c['payload'])
    program=deepcopy(r.program)
    # Inspect the public IR coordinate representation; use exact rationals only.
    for s in program['statements']:
        if s['kind']=='declare_point':
            s['at']=[str(2*Fraction(v)+offset) for v,offset in zip(s['at'],(3,-4,5))]
    gram=tuple(tuple(v/4 for v in row) for row in r.chart_metric.g)
    vr=validate_semantic_program(program)
    assert vr.ok,vr.error
    with metric.using(metric.Metric(gram)):
        replay=SemanticProgramInterpreter().execute(vr.spec)
    assert squared(replay.final_memory['kq_q'])==3
    assert xyz(replay.final_memory['M'])==tuple(2*v+o for v,o in zip(r.points['M'],(3,-4,5)))


def test_available_foot_candidates_are_also_budgeted():
    c=named_case()
    for i in range(9):
        label=f'J{i}'
        quote=f'Gọi {label} là hình chiếu vuông góc của S lên BD.'
        c['text'] += ' '+quote
        c['payload']['facts'].insert(0,{'id':f'foot{i}','kind':'projection','role':'premise','point':'S','at':label,
                                      'points':['B','D'],'quotes':[quote]})
    r=run_fact_route(c['text'],c['payload'])
    assert r.status=='REFUSED' and r.code=='PLAN_TOO_LARGE'


def test_type_incompatible_effect_candidate_is_excluded(monkeypatch):
    from dataclasses import replace
    from app.simulation.geometry_functions.registry import REGISTRY,PlanningTerm
    valid=REGISTRY['orthogonal_projection_line'].planning
    monkeypatch.setitem(REGISTRY,'orthogonal_projection_line',replace(REGISTRY['orthogonal_projection_line'],planning=None))
    wrong=replace(valid,inputs=(PlanningTerm('Plane',('P',)),)) # P is a point, not a three-label plane
    monkeypatch.setitem(REGISTRY,'translate_point',replace(REGISTRY['translate_point'],planning=wrong))
    c=CORPUS['positive'][0]
    r=run_fact_route(c['text'],c['payload'])
    assert r.status=='REFUSED' and r.code=='UNSUPPORTED_CAPABILITY'


@pytest.mark.parametrize('swapped',[False,True])
def test_equivalent_source_line_producers_share_one_verified_result(swapped):
    c=deepcopy(CORPUS['positive'][0])
    producer=deepcopy(next(f for f in c['payload']['facts'] if f['id']=='g'))
    producer['id']='h'
    if swapped:producer['points_a'],producer['points_b']=producer['points_b'],producer['points_a']
    goal=deepcopy(c['payload']['facts'][-1]);goal.update(id='q2',line_ref='h')
    c['payload']['facts'] += [producer,goal]
    r=run_fact_route(c['text'],c['payload'])
    assert r.status=='SERVED',(r.code,r.reason)
    assert set(r.answers)=={'q','q2'}
    statements=r.program['statements']
    assert len([s for s in statements if s.get('expr',{}).get('kind')=='intersect_plane_plane'])==1
    assert len([s for s in statements if s.get('expr',{}).get('kind')=='project_onto'])==1
    assert all(squared(r.exec_result.final_memory['kq_'+q])==Fraction(10,11) for q in r.answers)


def test_three_repeated_goals_reuse_memoized_needs_and_distinct_answers():
    c=deepcopy(CORPUS['positive'][0])
    for qid in ('q2','q3'):
        c['payload']['facts'].append({**deepcopy(c['payload']['facts'][-1]),'id':qid})
    r=run_fact_route(c['text'],c['payload'])
    assert r.status=='SERVED',(r.code,r.reason)
    assert set(r.answers)=={'q','q2','q3'}
    assert len([s for s in r.program['statements'] if s.get('expr',{}).get('kind')=='project_onto'])==1


def test_identical_explicit_foot_declarations_preserve_sources_and_one_construction():
    c=deepcopy(CORPUS['positive'][0])
    quote='Gọi J là hình chiếu vuông góc của M lên giao tuyến của (SAC) và (SBD).'
    c['text'] += ' '+quote
    for fid in ('foot1','foot2'):
        c['payload']['facts'].append({'id':fid,'kind':'projection','role':'premise','point':'M','at':'J',
                                      'line_ref':'g','quotes':[quote]})
    r=run_fact_route(c['text'],c['payload'])
    assert r.status=='SERVED',(r.code,r.reason)
    assert len([s for s in r.program['statements'] if s.get('expr',{}).get('kind')=='project_onto'])==1
    assert next(x for x in r.planner['calls'] if x['id']=='q')['args']['segment']==['M','J']


@pytest.mark.parametrize('location',['producer','goal','both'])
def test_source_plane_has_exactly_three_distinct_labels_before_set_normalization(location):
    c=deepcopy(CORPUS['positive'][0])
    for f in c['payload']['facts']:
        if f['id'] in ({'g'} if location=='producer' else {'q'} if location=='goal' else {'g','q'}):
            f['quotes']=[q.replace('(SAC)','(SAAC)') for q in f['quotes']]
    c['text']=' '.join(f['quotes'][0] for f in c['payload']['facts'])
    r=run_fact_route(c['text'],c['payload'])
    assert r.status=='REFUSED' and r.code=='SOURCE_OBJECT_MISMATCH'


@pytest.mark.parametrize('case_kind',[
    'unquoted-squared-goal',
    'unquoted-goal-tail',
    'unquoted-producer-tail',
    'unquoted-projection-tail',
    'named-line-squared-goal',
    'named-line-tail',
])
def test_enclosing_sentence_outside_truncated_quote_or_modifier_is_refused(case_kind):
    if case_kind.startswith('named-line-'):
        c = named_case()
        old = 'Tính khoảng cách từ S đến BD.'
        if case_kind == 'named-line-squared-goal':
            new = 'Tính bình phương khoảng cách từ S đến BD.'
            c['text'] = c['text'].replace(old, new)
            c['payload']['facts'][-1]['quotes'] = ['khoảng cách từ S đến BD.']
        else:
            new = 'Tính khoảng cách từ S đến BD đổi đáy thành hình thoi.'
            c['text'] = c['text'].replace(old, new)
            c['payload']['facts'][-1]['quotes'] = ['Tính khoảng cách từ S đến BD']
    else:
        c = deepcopy(CORPUS['positive'][0])
        if case_kind == 'unquoted-squared-goal':
            old = 'Tính khoảng cách từ M đến giao tuyến của (SAC) và (SBD).'
            c['text'] = c['text'].replace(old, 'Tính bình phương khoảng cách từ M đến giao tuyến của (SAC) và (SBD).')
            c['payload']['facts'][-1]['quotes'] = ['khoảng cách từ M đến giao tuyến của (SAC) và (SBD).']
        elif case_kind == 'unquoted-goal-tail':
            old = 'Tính khoảng cách từ M đến giao tuyến của (SAC) và (SBD).'
            c['text'] = c['text'].replace(old, 'Tính khoảng cách từ M đến giao tuyến của (SAC) và (SBD) đổi đáy thành hình thoi.')
            c['payload']['facts'][-1]['quotes'] = ['Tính khoảng cách từ M đến giao tuyến của (SAC) và (SBD)']
        elif case_kind == 'unquoted-producer-tail':
            old = 'Tìm giao tuyến của (SAC) và (SBD).'
            c['text'] = c['text'].replace(old, 'Tìm giao tuyến của (SAC) và (SBD) đổi đáy thành hình thoi.')
            next(f for f in c['payload']['facts'] if f['id'] == 'g')['quotes'] = ['Tìm giao tuyến của (SAC) và (SBD)']
        elif case_kind == 'unquoted-projection-tail':
            quote_full = 'Gọi J là hình chiếu vuông góc của M lên giao tuyến của (SAC) và (SBD) đổi M thành trung điểm BC.'
            quote_short = 'Gọi J là hình chiếu vuông góc của M lên giao tuyến của (SAC) và (SBD)'
            c['text'] = c['text'].replace('Tính khoảng cách', quote_full + ' Tính khoảng cách')
            c['payload']['facts'].insert(0, {'id': 'foot', 'kind': 'projection', 'role': 'premise',
                                             'point': 'M', 'at': 'J', 'line_ref': 'g', 'quotes': [quote_short]})
    r = run_fact_route(c['text'], c['payload'])
    assert r.status == 'REFUSED' and not r.answers and r.scene3d is None, (case_kind, r.status, r.code, r.answers)


def test_unreferenced_intersection_line_deduplication_and_coexistence():
    # 1. Duplicate unreferenced intersection_line facts alongside a named-line distance goal deduplicate to 1 IR statement.
    c1 = named_case()
    q_line = 'Tìm giao tuyến của (SAC) và (SBD).'
    c1['text'] = c1['text'].replace('Tính khoảng cách', q_line + ' Tính khoảng cách')
    for fid in ('g1', 'g2'):
        c1['payload']['facts'].insert(-1, {'id': fid, 'kind': 'intersection_line', 'role': 'premise',
                                           'points_a': ['S', 'A', 'C'], 'points_b': ['S', 'B', 'D'], 'quotes': [q_line]})
    r1 = run_fact_route(c1['text'], c1['payload'])
    assert r1.status == 'SERVED', (r1.code, r1.reason)
    assert len([s for s in r1.program['statements'] if s.get('expr', {}).get('kind') == 'intersect_plane_plane']) == 1

    # 2. An unreferenced atomic intersection_line fact alongside a line_ref goal is accepted by closed-source validation.
    c2 = deepcopy(CORPUS['positive'][0])
    extra_q = 'Tìm giao tuyến của (SAB) và (SCD).'
    c2['text'] = c2['text'].replace('Tính khoảng cách', extra_q + ' Tính khoảng cách')
    c2['payload']['facts'].insert(-1, {'id': 'g_extra', 'kind': 'intersection_line', 'role': 'premise',
                                       'points_a': ['S', 'A', 'B'], 'points_b': ['S', 'C', 'D'], 'quotes': [extra_q]})
    r2 = run_fact_route(c2['text'], c2['payload'])
    assert r2.status == 'SERVED', (r2.code, r2.reason)
    assert len([s for s in r2.program['statements'] if s.get('expr', {}).get('kind') == 'intersect_plane_plane']) == 2


def test_collinear_three_point_plane_in_intersection_line_is_refused():
    c = deepcopy(CORPUS['positive'][0])
    old_g = 'Tìm giao tuyến của (SAC) và (SBD).'
    new_g = 'Tìm giao tuyến của (AMB) và (SBD).'
    old_q = 'Tính khoảng cách từ M đến giao tuyến của (SAC) và (SBD).'
    new_q = 'Tính khoảng cách từ M đến giao tuyến của (AMB) và (SBD).'
    c['text'] = c['text'].replace(old_g, new_g).replace(old_q, new_q)
    g = next(f for f in c['payload']['facts'] if f['id'] == 'g')
    g['points_a'] = ['A', 'M', 'B']
    g['quotes'] = [new_g]
    c['payload']['facts'][-1]['quotes'] = [new_q]
    r = run_fact_route(c['text'], c['payload'])
    assert r.status == 'REFUSED' and r.code == 'COLLINEAR_POINTS' and not r.answers and r.scene3d is None

