"""DEV prism goal decomposition: missing planner slice, independent rational section oracle.

These tests catch missing prism composition, duplicate auxiliary constructions, wrong metric area,
provider-order sensitivity and fail-open source/geometry boundaries. No provider calls.
"""
from copy import deepcopy
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path

import pytest

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
from app.ai.function_route import run_fact_route

RUN = Path(__file__).resolve().parents[3] / 'docs/evaluation/geometry/runs/hybrid-v2-planner-generalization'


def _module(name):
    spec = importlib.util.spec_from_file_location('prism_dev_'+name, RUN/'tools'/f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ROWS = json.loads((RUN/'inputs/development.json').read_text(encoding='utf-8'))['cases']
ORACLES = json.loads((RUN/'inputs/oracle.json').read_text(encoding='utf-8'))
POS = [r for r in ROWS if r['expected_status']=='SERVED']
NEG = [r for r in ROWS if r['expected_status']=='REFUSED']


def _run(row):
    return run_fact_route(row['text'],deepcopy(row['payload']))


def _square(result):
    v=result.exec_result.final_memory['kq_q']
    return F(v.he)**2*v.can if hasattr(v,'can') else F(v)**2


@pytest.mark.parametrize('row',POS,ids=lambda r:r['id'])
def test_prism_section_area_matches_independent_edge_clip(row):
    result=_run(row)
    assert result.status=='SERVED',(result.code,result.reason)
    assert _square(result)==F(row['expected_area_squared'])
    assert len([o for o in result.scene3d['objects'] if o['type']=='section'])==1
    calls=result.planner['calls']
    # Removing memoization between the construction and area goals duplicates these geometric producers.
    assert sum(c['fn']=='orthogonal_projection_line' for c in calls)==2
    assert sum(c['fn']=='translate_point' for c in calls)==2
    assert sum(c['fn']=='section' for c in calls)==1
    assert sum(c['fn']=='ask_section_area' for c in calls)==1
    order={c['id']:i for i,c in enumerate(calls)}
    mid=next(c for c in calls if c['id']=='mid')
    assert all(order[mid['id']]<order[c['id']] for c in calls if c['fn'] in ('translate_point','section','ask_section_area'))


@pytest.mark.parametrize('row',POS,ids=lambda r:r['id'])
def test_fixtures_have_sufficient_source_dimensions_without_the_new_goal(row):
    """Independent control prevents a fixture's unrelated construction failure masquerading as the planner gap."""
    row=deepcopy(row)
    fs=[f for f in row['payload']['facts'] if f['id'] not in ('sec','q')]
    name=next(f['solid'] for f in fs if f['id']=='solid')
    quote=f'Tính thể tích khối lăng trụ {name}.'
    fs.append(dict(id='volume',kind='question',role='question',quotes=[quote],quantity='volume',solid=name))
    source=' '.join(dict.fromkeys(q for f in fs for q in f['quotes']))
    result=run_fact_route(source,{'facts':fs})
    assert result.status=='SERVED',(result.code,result.reason)


@pytest.mark.parametrize('row',NEG,ids=lambda r:r['id'])
def test_unsupported_ungrounded_and_invalid_prism_sections_refuse(row):
    result=_run(row)
    assert result.status=='REFUSED'
    assert result.code in row['expected_codes'],(result.code,result.reason)
    assert result.exec_result is None


@pytest.mark.parametrize('row',[POS[0],POS[7]],ids=lambda r:r['id'])
def test_canonical_v2_existing_schema_serves_same_section_and_adapter4_fails_closed(row):
    """The V2 route serves the section exactly. The /4 consumer wrapper still refuses: a plane-only derived section has no
    `DINH_CAT_CANH` vertex certificate, which /4 requires of every section — pre-existing at 386d2149 for pyramids too
    (ADAPTER_INTEGRATION_GAP, run report). Pinned here so the gap cannot close or turn into a wrong serve silently."""
    payload=_module('corpus').canonical(row)
    result=run_typed_fact_next_v2_route(payload)
    assert result.status=='SERVED',(result.code,result.reason)
    assert _square(result)==F(row['expected_area_squared'])
    assert result.route_d['sections']==[]
    rd=build_adapter4_response(result,payload['problem_text'])['route_d']
    assert (rd['status'],rd['refusal'])==('REFUSED',{'code':'PREVIEW_RESULT_INVALID'})


@pytest.mark.parametrize('word,status',[('lăng trụ','SERVED'),('chóp','REFUSED'),('tứ diện','REFUSED')])
def test_bare_solid_word_without_symbol_must_name_the_right_kind(word,status):
    """Bare kind words are accepted in section phrases (registry /15); without a solid symbol the word still has to be the
    kind of the cut solid — "thiết diện của chóp" never names this prism."""
    row=deepcopy(POS[0])
    old="Tính diện tích thiết diện của lăng trụ đứng ABC.A'B'C' với (P)."
    new=f"Tính diện tích thiết diện của {word} với (P)."
    assert old in row['text']
    row['text']=row['text'].replace(old,new)
    for f in row['payload']['facts']: f['quotes']=[q.replace(old,new) for q in f['quotes']]
    result=_run(row)
    assert result.status==status,(result.code,result.reason)
    if status=='SERVED':
        assert _square(result)==F(POS[0]['expected_area_squared'])
    else:
        assert result.exec_result is None


@pytest.mark.parametrize('transform',['reverse-facts','reverse-line','reverse-midpoint'])
def test_equivalent_source_operands_and_provider_order_preserve_area(transform):
    row=deepcopy(POS[0])
    if transform=='reverse-facts': row['payload']['facts'].reverse()
    else:
        if transform=='reverse-line':
            old,new='vuông góc với AB','vuông góc với BA'
            for f in row['payload']['facts']:
                if f['id'] in ('sec','q'): f['points_b'].reverse()
        else:
            old,new="trung điểm của BC'","trung điểm của C'B"
            next(f for f in row['payload']['facts'] if f['id']=='mid')['points'].reverse()
        row['text']=row['text'].replace(old,new)
        for f in row['payload']['facts']: f['quotes']=[q.replace(old,new) for q in f['quotes']]
    result=_run(row)
    assert result.status=='SERVED',(result.code,result.reason)
    assert _square(result)==F(POS[0]['expected_area_squared'])


def test_independent_oracle_known_rectangular_triangle_and_hexagonal_sections():
    oracle=_module('oracle')
    assert oracle.section(POS[0]['geometry'])['area_squared']=='2304'  # x=3 rectangle: 4*12
    assert oracle.section(POS[2]['geometry'])['area_squared']=='576'   # z=6 triangle: 6*8/2
    assert oracle.section(POS[5]['geometry'])['area_squared']=='432'   # central cube hexagon: 12 sqrt(3)
    for row in POS:
        assert oracle.section(row['geometry'])==ORACLES[row['id']]
    scaled=deepcopy(POS[0]['geometry'])
    scaled['points']={k:[str(2*F(v)) for v in p] for k,p in scaled['points'].items()}
    assert F(oracle.section(scaled)['area_squared'])==16*F(POS[0]['expected_area_squared'])


@pytest.mark.parametrize('ask,status',[("hình lăng trụ đứng ABC.A'B'C'",'SERVED'),('hình chóp T.XYZ','REFUSED'),
                                        ('hình chóp S.ABC','REFUSED'),("lăng trụ DEF.D'E'F'",'REFUSED')])
def test_area_question_on_a_shared_plane_must_name_the_cut_solid(ask,status):
    """Fail-open at 386d2149: with a section goal and an area goal on one derived plane, the area question's solid was never
    compared with the cut solid — the merged quotes carried the right symbol, so any named solid was served."""
    row=deepcopy(POS[0])
    old="Tính diện tích thiết diện của lăng trụ đứng ABC.A'B'C' với (P)."
    new=f"Tính diện tích thiết diện của {ask} với (P)."
    row['text']=row['text'].replace(old,new)
    for f in row['payload']['facts']: f['quotes']=[q.replace(old,new) for q in f['quotes']]
    result=_run(row)
    assert result.status==status,(result.code,result.reason)
    if status=='REFUSED':
        assert result.code=='SOURCE_OBJECT_MISMATCH' and result.exec_result is None


@pytest.mark.parametrize('ask,status',[('hình chóp S.ABC','SERVED'),('hình chóp T.XYZ','REFUSED'),
                                        ("hình lăng trụ ABC.A'B'C'",'REFUSED'),('lăng trụ','REFUSED')])
def test_pyramid_shared_plane_area_question_must_name_the_cut_solid(ask,status):
    from tests.geometry import test_geometry_capability_expansion as T
    sec="Dựng thiết diện của hình chóp S.ABC với (P)."
    new=f"Tính diện tích thiết diện của {ask} với (P)."
    q=next(x for x in T.B_FACTS if x['id']=='q')
    facts=[x for x in T.B_FACTS if x['id']!='q']+[{**q,'id':'sec','kind':'section','quotes':[T.B_DEF+' '+sec]},
                                                   {**q,'quotes':[T.B_DEF+' '+new]}]
    text=T.B_TEXT.replace(T.B_DEF+' '+T.B_ASK,f'{T.B_DEF} {sec} {T.B_DEF} {new}')
    result=T.run(text,facts)
    assert result.status==status,(result.code,result.reason)
    if status=='REFUSED':
        assert result.code=='SOURCE_OBJECT_MISMATCH' and result.exec_result is None


def test_pyramid_perpendicular_section_regression():
    from tests.geometry.test_geometry_capability_expansion import test_section_by_plane_through_point_perpendicular_to_line
    test_section_by_plane_through_point_perpendicular_to_line()


def test_existing_dependency_authority_still_rejects_cycles_and_dangling_references():
    from tests.geometry.test_hybrid_wave1_dependency_planner import (
        test_dependency_cycle_rejected_fail_closed, test_missing_dependency_rejected_fail_closed)
    test_dependency_cycle_rejected_fail_closed()
    test_missing_dependency_rejected_fail_closed()
