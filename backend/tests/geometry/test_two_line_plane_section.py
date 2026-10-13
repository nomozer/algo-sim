"""Preregistered two-line plane section acceptance: real Hybrid route, independent exact oracle."""
import json
import re
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.ai.function_route import run_fact_route
from app.simulation.geometry_functions.planner import lap_ke_hoach
from tests.geometry import hybrid_compiler_benchmark as HB
from tests.geometry.two_line_plane_oracle import section, fixture_model, dot, sub

RUN = Path(__file__).resolve().parents[3] / 'docs/evaluation/geometry/runs/two-line-plane-section'
CASES = json.loads((RUN/'inputs/math-corpus.json').read_text())['cases']


def assert_oracle_geometry(r,row):
    pts,faces,gram=fixture_model(row['family'])
    assert {k:r.points[k] for k in pts}==pts
    assert tuple(tuple(map(F,v)) for v in r.metric)==gram
    anchor=tuple((F(pts[row['mid'][0]][i])+pts[row['mid'][1]][i])/2 for i in range(3))
    assert r.points['M']==anchor
    oracle=section(pts,faces,anchor,row['lines'],gram)
    sec=next(o for o in r.scene3d['objects'] if o['type']=='section')
    ring=[(p.x,p.y,p.z) for p in r.exec_result.final_memory[sec['id']].polygon]
    expected=oracle['vertices']
    assert set(ring)==set(expected) and len(ring)==len(expected)>=3
    edges=lambda ps:{frozenset((a,b)) for a,b in zip(ps,ps[1:]+ps[:1])}
    assert edges(ring)==edges(expected)  # invariant to starting vertex / normal orientation
    assert all(dot(oracle['normal'],p)==oracle['offset'] for p in ring)
    for a,b in row['lines']:
        assert dot(oracle['normal'],sub(pts[b],pts[a]))==0
        assert dot(oracle['normal'],pts[a])!=oracle['offset']
    plane=next(o for o in r.scene3d['objects'] if o['type']=='plane3')
    assert all(dot(oracle['normal'],r.points[k])==oracle['offset'] for k in plane['depends'])
    assert HB.answer_square(r.answers['q'])==oracle['area_sq']
    auxiliary=[o for o in r.scene3d['objects'] if o['source'].get('binding')=='AUXILIARY' and o['type']=='point3']
    assert len(auxiliary)==2 and all(o['role']=='Điểm dựng phụ' for o in auxiliary)


def problem(family='pyramid', mid=('S','B'), lines=(('A','B'),('S','D')), build=True):
    if family == 'pyramid':
        sentences,facts=HB._square()
        solid='S.ABCD'; noun='hình chóp'
    elif family == 'triangular_pyramid':
        sentences=['Cho hình chóp S.ABC.','Đáy ABC là tam giác đều cạnh 2.','SA vuông góc với (ABC).','SA = 3.']
        facts=[HB._f('f1','solid',sentences[0],solid='S.ABC',solid_type='pyramid'),
               HB._f('f2','polygon_shape',sentences[1],points=list('ABC'),shape='equilateral_triangle',value='2'),
               HB._f('f3','perpendicular',sentences[2],points_a=list('SA'),points_b=list('ABC')),
               HB._f('f4','length',sentences[3],points=list('SA'),value='3',measure='segment')]
        solid='S.ABC'; noun='hình chóp'
    elif family == 'prism':
        sentences=["Cho lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều ABC cạnh 2.","AA' = 3."]
        facts=[HB._f('f1','solid',sentences[0],solid="ABC.A'B'C'",solid_type='prism',right=True),
               HB._f('f2','polygon_shape',sentences[0],points=list('ABC'),shape='equilateral_triangle',value='2'),
               HB._f('f3','length',sentences[1],points=['A',"A'"],value='3',measure='segment')]
        solid="ABC.A'B'C'"; noun='hình lăng trụ'
    else:
        sentences=["Cho hình hộp chữ nhật ABCD.A'B'C'D'.",'AB = 2.','AD = 4.',"AA' = 3."]
        solid="ABCD.A'B'C'D'"; noun='hình hộp'
        facts=[HB._f('f1','solid',sentences[0],solid=solid,solid_type='cuboid')]
        for i,(pair,val) in enumerate(((['A','B'],'2'),(['A','D'],'4'),(['A',"A'"],'3')),2):
            facts.append(HB._f(f'f{i}','length',sentences[i-1],points=pair,value=val,measure='segment'))
    point=HB._mid('fm','M',*mid)
    definition=f"Dựng mặt phẳng (P) đi qua M và song song với {''.join(lines[0])} và {''.join(lines[1])}."
    construct=f'Xác định thiết diện của {noun} {solid} với (P).'
    ask=f'Tính diện tích thiết diện của {noun} {solid} với (P).'
    common={'solid':solid,'point':'M','points_a':list(lines[0]),'points_b':list(lines[1]),
            'plane_relation':'parallel_two_lines','plane_name':'P'}
    facts+=[point]
    if build:
        facts.append(HB._f('sec','section',definition,**common))
        facts[-1]['quotes']=[definition,construct]
    facts.append(HB._ask('q',ask,'area',**common))
    facts[-1]['quotes']=[definition,ask]
    return ' '.join(sentences+point['quotes']+[definition]+([construct] if build else [])+[ask]),{'facts':facts}


@pytest.mark.parametrize('row',CASES,ids=lambda r:r['family']+'-'+r['expected']+'-'+''.join(r['mid'])+'-'+','.join(''.join(x) for x in r['lines']))
def test_preregistered_math_strata(row):
    text,facts=problem(row['family'],row['mid'],row['lines'])
    r=run_fact_route(text,facts)
    if row['expected']=='SERVED':
        assert r.status=='SERVED',(r.code,r.reason)
        assert HB.answer_square(r.answers['q'])==F(row['area_sq'])
        assert r.scene3d
        assert [o['label'] for o in r.scene3d['objects'] if o['type']=='plane3']==['(P)']
        assert_oracle_geometry(r,row)
    else:
        assert r.status=='REFUSED',(row,r.answers)
        if row['expected']!='NO_POLYGON':
            assert r.code==row['expected'],r.reason
        assert not r.answers and not r.scene3d


def test_multi_goal_shares_two_translates_and_one_section():
    text,facts=problem()
    plan=lap_ke_hoach(facts,text)
    assert sum(c['fn']=='translate_point' for c in plan.calls)==2
    r=run_fact_route(text,facts)
    assert r.status=='SERVED',(r.code,r.reason)
    assert sum(s.kind=='construct_section' for s in r.spec.statements)==1
    assert len(plan.derived_planes)==1
    assert len([s for s in r.trace if s.get('step')=='construct_plane' and s.get('relation_verified')])==1


def test_scene_section_reference_keeps_the_verified_plane_name():
    r=run_fact_route(*problem())
    assert r.status=='SERVED'
    obj=next(o for o in r.scene3d['objects'] if o['type']=='section')
    assert '(P)' in obj['label'] and '(MHH1)' not in obj['label']
    assert '(MHH1)' not in (obj.get('role') or '')


@pytest.mark.parametrize('extra',["Dựng mặt phẳng (P) qua M và song song với (SBC).", "(P) là mặt phẳng (SBC)."])
def test_another_definition_of_the_same_plane_refuses(extra):
    text,payload=problem()
    text=text.replace('Xác định thiết diện',extra+' Xác định thiết diện')
    r=run_fact_route(text,payload)
    assert r.status=='REFUSED' and not r.scene3d


def test_a_request_for_two_planes_cannot_be_reduced_to_one():
    text,payload=problem()
    text=text.replace('với (P).','với (P) và (Q).')
    for f in payload['facts']:
        f['quotes']=[q.replace('với (P).','với (P) và (Q).') for q in f['quotes']]
    r=run_fact_route(text,payload)
    assert r.status=='REFUSED' and not r.scene3d


@pytest.mark.parametrize('variant',['swap','reverse_first','reverse_second','rename','collision','construction_only'])
def test_metamorphic_goal_controls(variant):
    text,payload=problem()
    expected=run_fact_route(text,payload)
    if variant=='swap':
        text,payload=problem(lines=(('S','D'),('A','B')))
    elif variant.startswith('reverse'):
        text,payload=problem(lines=(('B','A'),('S','D')) if variant=='reverse_first' else (('A','B'),('D','S')))
    elif variant=='rename':
        ren=str.maketrans('SABCDMP','TEFGKNQ')
        rename=lambda s:re.sub(r"(?<!\w)[A-Z][A-Z0-9'.]*(?!\w)",lambda m:m[0].translate(ren),s)
        text=rename(text)
        payload=json.loads(rename(json.dumps(payload,ensure_ascii=False)))
    elif variant=='collision':
        text=text.replace('Gọi M','Gọi H').replace('qua M','qua H')
        payload=json.loads(json.dumps(payload,ensure_ascii=False).replace('"M"','"H"').replace('Gọi M','Gọi H').replace('qua M','qua H'))
    elif variant=='construction_only':
        text=text[:text.index('Tính diện tích')]
        payload['facts']=[f for f in payload['facts'] if f['id']!='q']
    r=run_fact_route(text,payload)
    assert expected.status==r.status=='SERVED',(r.code,r.reason)
    if variant!='construction_only':
        assert list(r.answers.values())==list(expected.answers.values())


@pytest.mark.parametrize('extra',["Chứng minh SC ⊥ BD và đáy là hình chữ nhật.",
                                "Chứng minh SC ⊥ BD song đáy là hình chữ nhật.","Suy ra SB = 7.",
                                'Đổi SA thành 5.'])
def test_declared_source_residuals_cannot_serve_new_goal(extra):
    text,payload=problem()
    text=text.replace('Dựng mặt phẳng',extra+' Dựng mặt phẳng')
    r=run_fact_route(text,payload)
    assert r.status=='REFUSED' and not r.answers and not r.scene3d


@pytest.mark.parametrize('claim',['SA vuông góc với (ABCD) và SB vuông góc với (ABCD).',
                               'SA = 3 và mọi kích thước gấp đôi.','SA = 3 và SB = 3.',
                               'SA vuông góc với (ABCD), SB vuông góc với (ABCD).',
                               'SA vuông góc với (ABCD), SB song song CD.',
                               'SA vuông góc với (ABCD), các cạnh bên bằng nhau.',
                               'SA = 3, SB = SC = SD.',
                               'SA vuông góc với (ABCD) SB song song CD.',
                               'SA = 3 SB = SC = SD.'])
def test_long_quote_does_not_license_unverified_relation(claim):
    text,payload=problem()
    idx=2 if claim.startswith('SA vuông') else 3
    old=payload['facts'][idx]['quotes'][0]
    text=text.replace(old,claim)
    payload['facts'][idx]['quotes']=[claim]
    r=run_fact_route(text,payload)
    assert r.status=='REFUSED' and not r.answers and not r.scene3d


@pytest.mark.parametrize('fid',['f1','f2','fm'])
@pytest.mark.parametrize('suffix',[' SB song song CD.',' các cạnh bên bằng nhau.',' SB = SC = SD.',' mọi kích thước gấp đôi.'])
def test_all_admitted_premise_quotes_require_complete_grounding(fid,suffix):
    text,payload=problem()
    f=next(f for f in payload['facts'] if f['id']==fid)
    old=f['quotes'][0]; new=old.rstrip('.')+suffix
    text=text.replace(old,new); f['quotes']=[new]
    r=run_fact_route(text,payload)
    assert r.status=='REFUSED' and not r.answers and not r.scene3d


@pytest.mark.parametrize('prefix',['Các cạnh bên bằng nhau. ','Các cạnh bên bằng nhau, ','Mọi kích thước được nhân ba, '])
@pytest.mark.parametrize('reverse_quotes',[False,True])
def test_auxiliary_quote_cannot_hide_an_unread_premise(prefix,reverse_quotes):
    text,payload=problem()
    definition=next(f for f in payload['facts'] if f['id']=='sec')['quotes'][0]
    text=text.replace(definition,prefix+definition)
    for f in payload['facts']:
        f['quotes']=[prefix+q if q==definition else q for q in f['quotes']]
        if reverse_quotes: f['quotes'].reverse()
    r=run_fact_route(text,payload)
    assert r.status=='REFUSED' and not r.answers and not r.scene3d


@pytest.mark.parametrize('change',['wrong_line','wrong_name','missing_quote','negated','prove','conditional','finite_segment','unknown_point','degenerate'])
def test_source_and_operand_adversaries(change):
    text,payload=problem()
    for f in payload['facts']:
        if f.get('plane_relation'):
            if change=='wrong_line': f['points_b']=['S','C']
            if change=='wrong_name': f['plane_name']='Q'
            if change=='missing_quote': f['quotes']=f['quotes'][1:]
            if change=='negated': f['negated']=True
            if change=='prove': f['role']='prove'
            if change=='conditional': f['role']='condition'
            if change=='unknown_point': f['point']='N'
            if change=='degenerate': f['points_a']=['A','A']
    if change=='finite_segment':
        text=text.replace('với AB và SD','với hai đoạn thẳng AB và SD')
        for f in payload['facts']:
            f['quotes']=[q.replace('với AB và SD','với hai đoạn thẳng AB và SD') for q in f['quotes']]
    r=run_fact_route(text,payload)
    assert r.status=='REFUSED' and not r.answers and not r.scene3d


def test_oracle_translation_scaling_normal_and_metric():
    pts={'A':(0,0,0),'B':(1,0,0),'C':(1,1,0),'D':(0,1,0),'S':(0,0,1)}
    faces=[list('ABCD'),list('SAB'),list('SBC'),list('SCD'),list('SDA')]
    g=((4,0,0),(0,4,0),(0,0,9)); m=(F(1,2),0,F(1,2)); lines=(('A','B'),('S','D'))
    r=section(pts,faces,m,lines,g)
    assert r['status']=='SERVED'
    assert section(pts,faces,m,lines,g,flip=True)['area_sq']==r['area_sq']
    moved={k:tuple(F(x)+v for x,v in zip(p,(7,-3,2))) for k,p in pts.items()}
    assert section(moved,faces,tuple(x+v for x,v in zip(m,(7,-3,2))),lines,g)['area_sq']==r['area_sq']
    scaled={k:tuple(F(x)*3 for x in p) for k,p in pts.items()}
    assert section(scaled,faces,tuple(x*3 for x in m),lines,g)['area_sq']==r['area_sq']*81


def test_translating_the_engine_chart_preserves_the_exact_result(monkeypatch):
    from app.simulation.geometry_functions.engine import _Dung
    original=_Dung.giai_phu_thuoc
    def translated(self):
        original(self)
        self.pts={name:tuple(x+d for x,d in zip(p,(7,-3,2))) for name,p in self.pts.items()}
    expected=run_fact_route(*problem())
    monkeypatch.setattr(_Dung,'giai_phu_thuoc',translated)
    r=run_fact_route(*problem())
    assert r.status=='SERVED',(r.code,r.reason)
    assert r.answers==expected.answers
    assert r.points['M']==tuple(x+d for x,d in zip(expected.points['M'],(7,-3,2)))


def test_scaling_source_lengths_scales_area_with_the_same_section_topology():
    text,payload=problem()
    original=run_fact_route(text,payload)
    text=text.replace('cạnh 2','cạnh 6').replace('SA = 3','SA = 9')
    for f in payload['facts']:
        if f.get('value') in ('2','3'): f['value']=str(int(f['value'])*3)
        f['quotes']=[q.replace('cạnh 2','cạnh 6').replace('SA = 3','SA = 9') for q in f['quotes']]
    r=run_fact_route(text,payload)
    assert r.status=='SERVED',(r.code,r.reason)
    assert HB.answer_square(r.answers['q'])==81*HB.answer_square(original.answers['q'])
    assert len(next(o for o in r.scene3d['objects'] if o['type']=='section')['polygon'])==len(next(o for o in original.scene3d['objects'] if o['type']=='section')['polygon'])


def test_tangent_apex_cannot_serve_a_polygon():
    text,payload=problem(lines=(('A','B'),('A','D')))
    mid=next(f for f in payload['facts'] if f['id']=='fm')
    text=text.replace(mid['quotes'][0],'').replace('qua M','qua S')
    payload['facts']=[f for f in payload['facts'] if f['id']!='fm']
    for f in payload['facts']:
        if f.get('plane_relation'):
            f['point']='S'; f['quotes']=[q.replace('qua M','qua S') for q in f['quotes']]
    r=run_fact_route(text,payload)
    assert r.status=='REFUSED' and not r.scene3d and not r.answers
    assert r.code not in ('ENGINE_EXECUTION_FAILED','SCENE_BUILD_FAILED')


def test_coincident_lines_are_not_two_independent_directions():
    r=run_fact_route(*problem(lines=(('A','B'),('B','A'))))
    assert r.status=='REFUSED' and r.code=='PLANE_NOT_UNIQUE' and not r.scene3d


def test_distinct_labels_with_identical_points_are_a_degenerate_line():
    text,payload=problem(lines=(('M','N'),('S','D')))
    fact=HB._mid('fn','N','S','B')
    text=text.replace('Dựng mặt phẳng',fact['quotes'][0]+' Dựng mặt phẳng')
    payload['facts'].insert(5,fact)
    r=run_fact_route(text,payload)
    assert r.status=='REFUSED' and r.code=='DEGENERATE_LINE' and not r.scene3d


def test_default_display_path_keeps_its_previous_names():
    from app.simulation.semantic_program.simulation_state import build_simulation_state
    from app.simulation.semantic_program.scene3d import build_scene3d
    r=run_fact_route(*problem())
    scene=build_scene3d(build_simulation_state(r.spec,r.exec_result,r.declared_topology))
    plane=next(o for o in scene['objects'] if o['type']=='plane3')
    assert plane['label']=='(P)' and plane['notation']=='(MHH1)'
    section_obj=next(o for o in scene['objects'] if o['type']=='section')
    assert '(MHH1)' in section_obj['label']


@pytest.mark.parametrize('fault',['translate','parallel','collision','direction','target','nonunique','budget'])
def test_independent_checks_reject_plan_or_kernel_faults(fault,monkeypatch):
    from app.simulation.geometry_functions import engine as E
    from app.ai.function_route import run_function_route
    from app.simulation.geometry.exact import Vec3
    text,payload=problem(); plan=lap_ke_hoach(payload,text)
    if fault=='translate':
        old=E.K.translate
        monkeypatch.setattr(E.K,'translate',lambda p,v:old(p,v)+Vec3(1,0,0))
    elif fault=='parallel': monkeypatch.setattr(E,'parallel_line_plane',lambda *_:False)
    elif fault=='collision': plan.auxiliary[0]['labels'][0]='M'
    elif fault=='direction': plan.calls[-3]['args']['vector']=['A','D']
    elif fault=='target': plan.auxiliary[0]['targets']=['missing']
    elif fault=='nonunique':
        text,payload=problem(lines=(('A','B'),('C','D'))); plan=lap_ke_hoach(payload,text)
    else:
        from app.simulation.geometry_functions import planner as PL
        monkeypatch.setattr(PL,'MAX_DERIVED_PLANES',0)
        r=run_fact_route(text,payload)
        assert r.status=='REFUSED' and r.code=='PLAN_TOO_LARGE'
        return
    r=run_function_route(text,{'calls':plan.calls},tuple(plan.auxiliary))
    assert r.status=='REFUSED' and not r.scene3d and not r.answers


def test_fake_provider_extracts_new_schema_without_geometry_functions():
    from app.ai.fact_extraction import run_ai_fact_route
    text,payload=problem()
    seen=[]
    def transport(request):
        seen.append(request)
        return {'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(payload,ensure_ascii=False)}]}}]}
    r=run_ai_fact_route(text,transport=transport)
    assert r.status=='SERVED',(r.code,r.reason)
    schema=seen[0]['generationConfig']['responseSchema']
    assert 'parallel_two_lines' in json.dumps(schema) and 'plane_name' in json.dumps(schema)
    assert 'tools' not in seen[0] and 'translate_point' not in json.dumps(schema)
