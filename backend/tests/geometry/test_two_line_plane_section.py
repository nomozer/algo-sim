"""Preregistered two-line plane section acceptance: real Hybrid route, independent exact oracle."""
import copy
import json
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.ai.function_route import run_fact_route
from app.simulation.geometry_functions.planner import lap_ke_hoach
from tests.geometry import hybrid_compiler_benchmark as HB
from tests.geometry.two_line_plane_oracle import section

RUN = Path(__file__).resolve().parents[3] / 'docs/evaluation/geometry/runs/two-line-plane-section'
CASES = json.loads((RUN/'inputs/math-corpus.json').read_text())['cases']


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
        text=text.translate(ren)
        payload=json.loads(json.dumps(payload).translate(ren))
    elif variant=='collision':
        text=text.replace('Gọi M','Gọi H').replace('qua M','qua H')
        payload=json.loads(json.dumps(payload).replace('"M"','"H"').replace('Gọi M','Gọi H').replace('qua M','qua H'))
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
                               'SA = 3 và mọi kích thước gấp đôi.','SA = 3 và SB = 3.'])
def test_long_quote_does_not_license_unverified_relation(claim):
    text,payload=problem()
    idx=2 if claim.startswith('SA vuông') else 3
    old=payload['facts'][idx]['quotes'][0]
    text=text.replace(old,claim)
    payload['facts'][idx]['quotes']=[claim]
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
