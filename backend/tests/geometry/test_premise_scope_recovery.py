"""Recovery of declared ownership and exact, reachable plane-projection contradictions."""
from copy import deepcopy
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions import typed_fact_next_bridge as B
from app.simulation.geometry_functions.registry import TuChoi

RUN = Path(__file__).resolve().parents[3] / 'docs/evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding'
CASES = {c['id']:c for c in json.loads((RUN/'inputs/development.json').read_text(encoding='utf-8'))['cases']}
spec=importlib.util.spec_from_file_location('recovery_development',RUN/'tools/evaluate_development.py')
DEV=importlib.util.module_from_spec(spec);spec.loader.exec_module(DEV)


def scoped_payload(premise, other=None):
    solids=[{'solid_id':'s1','solid_type':'pyramid','notation':'S.ABC','quote':'Cho hình chóp S.ABC.'}]
    if other:
        solids.append({'solid_id':'s2','solid_type':'pyramid','notation':other,'quote':f'Cho hình chóp {other}.'})
    return {'schema_version':'typed-fact-next/2','problem_text':' '.join([x['quote'] for x in solids]+[premise['quote']]),
            'solids':solids,'premises':[premise],'derived_sections':[],'relations':[],
            'simulation_goals':[{'goal_id':'g','kind':'construct_object','target_solid_id':'s1','quote':solids[0]['quote']}],
            'math_goals':[]}


def ratio(**patch):
    return {'kind':'divide_segment','solid_id':'s1','args':{'point':'M','segment':['S','A'],'ratio':'1/3'},
            'quote':'Lấy M thuộc cạnh SA với SM = 1/3 SA.',**patch}


@pytest.mark.parametrize('cid',['DEV-NEG-08','DEV-NEG-23'])
@pytest.mark.parametrize('canonical',[False,True])
def test_original_unknown_scope_never_served(cid,canonical):
    c=DEV.canonical_f2(CASES[cid]) if canonical else deepcopy(CASES[cid])
    r=run_typed_fact_next_v2_route(c['payload'])
    assert (r.status,r.code)==('REFUSED','UNKNOWN_SOLID_ID')


@pytest.mark.parametrize('schema',['typed-fact-next/1','typed-fact-next/2'])
@pytest.mark.parametrize('sid',['foreign','','bad scope'])
def test_unknown_or_malformed_explicit_scope_is_not_optional(schema,sid):
    p=scoped_payload(ratio(solid_id=sid));p['schema_version']=schema
    with pytest.raises(TuChoi) as e:
        (B.bridge if schema.endswith('/1') else B.bridge_v2)(p)
    assert e.value.code in ('UNKNOWN_SOLID_ID','INVALID_TYPED_FACT_NEXT','SCHEMA_INVALID')


@pytest.mark.parametrize('premise',[
    ratio(args={'point':'M','segment':['T','D'],'ratio':'1/3'}),
    {'kind':'orthogonal_projection','solid_id':'s1','args':{'point':'S','image':'D','plane':['D','E','F']},
     'quote':'D là chân đường cao hạ từ S xuống mặt phẳng (DEF).'},
    {'kind':'orthogonal_projection','solid_id':'s1','args':{'point':'S','image':'D','plane':['A','B','C']},
     'quote':'D là chân đường cao hạ từ S xuống mặt phẳng (ABC).'},
])
def test_known_scope_cannot_borrow_other_solid_operands(premise):
    with pytest.raises(TuChoi) as e:B.bridge_v2(scoped_payload(premise,'T.DEF'))
    assert e.value.code=='SOURCE_OBJECT_MISMATCH'


def test_same_local_labels_do_not_license_a_qualified_other_scope():
    p=scoped_payload(ratio(args={'point':'M','segment':['s2::T','s2::A'],'ratio':'1/3'}),'T.ABD')
    with pytest.raises(TuChoi) as e:B.bridge_v2(p)
    assert e.value.code=='SOURCE_OBJECT_MISMATCH'


def test_derived_point_ownership_follows_its_definition_not_a_consumers_scope():
    p=scoped_payload(ratio(),'T.DEF')
    p['premises']=[{'kind':'midpoint','solid_id':'s2','args':{'point':'N','segment':['D','E']},
                    'quote':'N là trung điểm của DE.'},ratio(args={'point':'M','segment':['S','N'],'ratio':'1/3'})]
    p['problem_text']+=' N là trung điểm của DE.'
    with pytest.raises(TuChoi) as e:B.bridge_v2(p)
    assert e.value.code=='SOURCE_OBJECT_MISMATCH'


def test_absent_optional_scope_is_served_when_unambiguous():
    p=deepcopy(CASES['DEV-RATIO-03']['payload'])
    for prem in p['premises']:prem.pop('solid_id',None)
    assert run_typed_fact_next_v2_route(p).status=='SERVED'


def test_absent_optional_scope_does_not_guess_between_solids():
    prem=ratio(solid_id=None,args={'point':'M','segment':['A','B'],'ratio':'1/3'})
    with pytest.raises(TuChoi) as e:B.bridge_v2(scoped_payload(prem,'T.ABD'))
    assert e.value.code=='AMBIGUOUS_REFERENCE'


def test_explicit_valid_scope_survives_in_receipt_with_its_quote():
    p=deepcopy(CASES['DEV-RATIO-03']['payload']);out=B.bridge_v2(p)
    scopes=out['bridge']['validated_premise_scopes']
    assert len(scopes)==len(p['premises'])
    assert all(x['declared_solid_id']=='s1' and x['quote']==prem['quote'] for x,prem in zip(scopes,p['premises']))


def test_missing_quote_cannot_establish_ownership():
    p=deepcopy(CASES['DEV-RATIO-03']['payload']);p['premises'][-1]['quote']='Lấy M thuộc đoạn XY với XM = 1/3 XY.'
    r=run_typed_fact_next_v2_route(p)
    assert r.status=='REFUSED' and r.code=='QUOTE_NOT_IN_SOURCE'


@pytest.mark.parametrize('mutant',['remove_validation','replace_with_default'])
@pytest.mark.parametrize('cid',['DEV-NEG-08','DEV-NEG-23'])
def test_scope_safety_oracle_kills_bypass_and_default_scope_mutants(monkeypatch,mutant,cid):
    p=deepcopy(CASES[cid]['payload'])
    assert run_typed_fact_next_v2_route(p).status=='REFUSED'
    original=B._kiem_pham_vi_tien_de
    def broken(payload,solids):
        if mutant=='remove_validation':return []
        premises=tuple(x.model_copy(update={'solid_id':next(iter(solids))}) if x.solid_id not in solids else x for x in payload.premises)
        return original(payload.model_copy(update={'premises':premises}),solids)
    monkeypatch.setattr(B,'_kiem_pham_vi_tien_de',broken)
    assert run_typed_fact_next_v2_route(p).status=='SERVED', 'mutant must expose the original unsafe path'


def incidence_payload(foot='A'):
    qs=['Cho hình chóp S.ABCD.','Đáy ABCD là hình vuông cạnh 2.','SA vuông góc với (ABCD).','SA = 3.',
        f'{foot} là chân đường cao hạ từ D xuống mặt phẳng (SBC).','Tính thể tích hình chóp S.ABCD.']
    return {'schema_version':'typed-fact-next/2','problem_text':' '.join(qs),'length_unit':'1',
            'solids':[{'solid_id':'s1','solid_type':'pyramid','notation':'S.ABCD','quote':qs[0]}],
            'premises':[{'kind':kind,'args':a,'quote':q,'solid_id':'s1'} for kind,a,q in [
                ('base_is_square',{'vertices':list('ABCD'),'side':'2'},qs[1]),
                ('perpendicular_line_plane',{'line':['S','A'],'plane':list('ABCD')},qs[2]),
                ('segment_length',{'segment':['S','A'],'value':'3'},qs[3]),
                ('orthogonal_projection',{'point':'D','image':foot,'plane':list('SBC')},qs[4])]],
            'derived_sections':[],'relations':[],
            'simulation_goals':[{'goal_id':'g','kind':'construct_object','target_solid_id':'s1','quote':qs[0]}],
            'math_goals':[{'goal_id':'v','kind':'measurement','goal_type':'volume','solid_id':'s1','target':{'solid':'s1'},'quote':qs[5]}]}


def test_fully_placed_projection_incidence_witness_reaches_geometric_verification():
    # Independent exact Euclidean frame: A=(0,0,0), B=(2,0,0), C=(2,2,0), D=(0,2,0), S=(0,0,3).
    # Plane SBC: 3x+2z=6. A has signed numerator -6, so cannot be its projection foot.
    assert 3*F(0)+2*F(0)-6 == -6
    r=run_typed_fact_next_v2_route(incidence_payload())
    assert r.status=='REFUSED' and r.code=='INCONSISTENT_FACTS', (r.code,r.reason)
    assert r.code!='UNDERDETERMINED_POINT'


def test_original_neg20_top_vertex_cannot_lie_on_non_degenerate_prism_base():
    row=DEV.evaluate_case(CASES['DEV-NEG-20'])
    assert row['matches_expected'] and row['code']=='INCONSISTENT_FACTS', (row['code'],row.get('reason'))
