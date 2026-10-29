"""Preregistered N1–N7 oracles; see closed-input-contract/preregistration.md."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.ai import adapter3_simulation as A
from app.simulation.geometry_functions import typed_fact_next as T
from app.simulation.geometry_functions import typed_fact_next_bridge as B
import scope_field_census as C
import test_scope_census_closure as F

OUT = F.RUN / 'closed-input-contract'
POLICY = json.loads((OUT / 'allowed-fields.json').read_text(encoding='utf-8'))
MODELS = {'math_goal': T.MathGoalSpec, 'simulation_goal': T.SimulationGoalSpec, 'relation': T.GeometricRelationSpec}
CODES = {'math_goal': 'INVALID_MATH_GOAL', 'simulation_goal': 'INVALID_SIMULATION_GOAL', 'relation': 'INVALID_RELATION_SPEC'}
VALUES = dict(numerator_solid_id='s1', denominator_solid_id='s2', parent_solid_id='s1', cut_solid_id='s2',
              goal_type='volume', target={'solid': 's1'}, solid_id='s1', target_solid_id='s1', target_section_id='sec',
              derived_solid_id='top', apex_ref='S', target_refs=['A'], style_role='primary', container_ref='AB',
              member_ref='A', pairs=[['s1::A', 's2::A']], solid_a='s1', solid_b='s2', face_a=['A','B','C'],
              face_b=['A','B','C'], entity_a=['A','B'], entity_b=['A','C'], section_id='sec', member_refs=['A'],
              frame_id='root', anchor_refs=['A','B','C'])
REQUIRED = {
    'volume_ratio': ['numerator_solid_id','denominator_solid_id'], 'residual_volume': ['parent_solid_id','cut_solid_id'],
    'measurement': ['goal_type','target'], 'construct_object': ['target_solid_id'],
    'construct_plane_section': ['target_section_id'], 'construct_derived_solid': ['derived_solid_id','target_section_id','apex_ref'],
    'highlight_geometry': ['target_refs'], 'construction_sequence': [], 'containment': ['container_ref','member_ref'],
    'shared_vertices': ['pairs'], 'shared_faces': ['solid_a','solid_b','face_a','face_b'],
    'parallel': ['entity_a','entity_b'], 'perpendicular': ['entity_a','entity_b'],
    'section_membership': ['section_id','member_refs'], 'coordinate_frame': ['solid_id','frame_id'],
}


def minimal(group, kind):
    return {('relation_id' if group == 'relation' else 'goal_id'): 'probe', 'kind': kind, 'quote': 'q',
            **{k: deepcopy(VALUES[k]) for k in REQUIRED[kind]}}


def child_code(model, raw):
    try:
        model.model_validate(raw)
    except Exception as exc:
        if isinstance(exc, T.TypedFactNextValidationError):
            return exc.code
        for item in getattr(exc, 'errors', lambda: [])():
            inner = (item.get('ctx') or {}).get('error')
            if isinstance(inner, T.TypedFactNextValidationError):
                return inner.code
        return type(exc).__name__
    return None


ALLOWED = [(g,k,f) for g,ks in POLICY['allowed_fields'].items() for k,fs in ks.items() for f in fs]
FORBIDDEN = [(g,k,f) for g,ks in POLICY['allowed_fields'].items() for k,fs in ks.items()
             for f in MODELS[g].model_fields if f not in fs]


@pytest.mark.parametrize('group,kind,field', ALLOWED)
def test_allowed_kind_fields_remain_valid(group, kind, field):
    p = minimal(group, kind)
    if field in VALUES: p[field] = deepcopy(VALUES[field])
    assert child_code(MODELS[group], p) is None


@pytest.mark.parametrize('group,kind,field', FORBIDDEN)
@pytest.mark.parametrize('explicit', ['value', 'null'])
def test_inapplicable_kind_fields_are_typed(group, kind, field, explicit):
    p = minimal(group, kind); p[field] = deepcopy(VALUES.get(field)) if explicit == 'value' else None
    assert child_code(MODELS[group], p) == CODES[group]


@pytest.mark.parametrize('group', list(MODELS))
def test_unknown_kind_fields_are_typed(group):
    kind = next(iter(POLICY['allowed_fields'][group])); p = minimal(group, kind); p['unregistered'] = 's1'
    assert child_code(MODELS[group], p) == CODES[group]


@pytest.mark.parametrize('key,good', [('point','S'),('segment',['S','A']),('line',['S','A']),('line1',['S','A']),
    ('line2',['A','B']),('plane',['A','B','C']),('plane1',['A','B','C']),('plane2',['S','A','B']),('polygon',['A','B','C'])])
@pytest.mark.parametrize('bad', ['string', 'object', 'empty', 'wrong_arity', 'null'])
def test_operand_shapes_fail_before_routes(key, good, bad):
    target = {'segment':['S','A']} if key == 'segment' else {'polygon':['A','B','C']} if key == 'polygon' else \
        {'line1':['S','A'],'line2':['A','B']} if key in ('line1','line2') else \
        {'plane1':['A','B','C'],'plane2':['S','A','B']} if key in ('plane1','plane2') else {'point':'S','plane':['A','B','C']} if key in ('point','plane') else {'line':['S','A'],'plane':['A','B','C']}
    value = {'string': ''.join(good) if isinstance(good,list) else [good], 'object': {'ref':good},
             'empty': [], 'wrong_arity': ['S'] if key != 'point' else ['S','A'], 'null':None}[bad]
    target[key] = value
    p = F.sup(); p['math_goals'] = [{'goal_id':'bad','kind':'measurement','goal_type':'area' if key=='polygon' else 'distance',
                                   'target':target,'quote':F.Q}]
    F.refused_everywhere(p, 'INVALID_MATH_GOAL')


@pytest.mark.parametrize('key', ['solid_b','solids','plane','parent'])
def test_closed_target_keys_cannot_be_ignored(key):
    p = F.sup(); p['math_goals'][0]['target'][key] = 's2'
    F.refused_everywhere(p, 'INVALID_MATH_GOAL')


def legacy_m():
    p = deepcopy(F.A3DEV['A3-DEV-02']['payload'])
    p['problem_text'] += ' Gọi M là trung điểm của SB. Tính độ dài MB.'
    p['premises'].append({'kind':'point_is_midpoint','solid_id':'pyr1','args':{'point':'M','segment':['S','B']},
                          'quote':'Gọi M là trung điểm của SB.'})
    return p


# CIC-D1 amendment (cic-d1-contract-recovery/n2-amendment.md): the in-target `solid_id`/`solid` forms violate the locked
# V2 target grammar; their ownership coverage moved to test_cic_d1_locked_contract.py (N2 v2), inputs kept in cases.json.
@pytest.mark.parametrize('scope', ['goal'])
@pytest.mark.parametrize('qualified', [False,True])
def test_legacy_constructed_ownership_precedes_capability(scope, qualified):
    p = legacy_m(); g = {'goal_id':'foreign','kind':'measurement','goal_type':'distance','quote':'Tính độ dài MB.',
                         'target':{'segment':['pyr2::M' if qualified else 'M','B']}}
    if scope=='goal': g['solid_id']='pyr2'
    else: g['target'][scope]='pyr2'
    p['math_goals'].append(g); F.refused_everywhere(p, 'SOURCE_OBJECT_MISMATCH')


def test_legacy_positive_keeps_exact_oracle():
    p = legacy_m(); r = F.a3(p)
    assert r.status == 'SERVED', (r.code,r.reason)
    assert r.answer_exact == F.A3DEV['A3-DEV-02']['oracle_exact']


def test_legacy_containment_ownership_precedes_capability():
    p = legacy_m(); p['relations'].append({'relation_id':'foreign','kind':'containment','container_ref':'pyr2',
                                          'member_ref':'M','quote':'Gọi M là trung điểm của SB.'})
    F.refused_everywhere(p,'SOURCE_OBJECT_MISMATCH')


@pytest.mark.parametrize('kind', ['shared_vertices','containment'])
def test_curved_unknown_qualified_label_is_terminal(kind):
    p = F.cones(); rel = {'relation_id':'unknown','kind':kind,'quote':p['solids'][0]['quote']}
    rel.update({'pairs':[['cone_main::Z','cone2::T']]} if kind=='shared_vertices' else
               {'container_ref':'cone_main','member_ref':'cone_main::Z'})
    p['relations'] = [rel]; F.refused_everywhere(p,'UNKNOWN_VERTEX_REF')


def test_curved_unsupported_relation_is_not_ignored():
    p = F.cones(); p['relations'] = [{'relation_id':'r','kind':'parallel','entity_a':['S','O'],
                                    'entity_b':['T','K'],'quote':p['solids'][0]['quote']}]
    assert F.outcome(F.a3(p)) == ('REFUSED','BRIDGE_UNSUPPORTED_RELATION')


def test_curved_relation_missing_source_is_typed():
    p = F.cones(); p['relations'] = [{'relation_id':'r','kind':'parallel','entity_a':['S','O'],
                                    'entity_b':['T','K'],'quote':'not in source'}]
    assert F.outcome(F.a3(p)) == ('REFUSED','SOURCE_QUOTE_NOT_FOUND')


def test_curved_contradictory_identity_is_not_ignored():
    p = F.cones(); p['relations'] = [{'relation_id':'r','kind':'shared_vertices','pairs':[['cone_main::S','cone2::T']],
                                    'quote':p['solids'][0]['quote']}]
    assert F.outcome(F.a3(p)) == ('REFUSED','SHARED_ENTITY_MISMATCH')


def test_curved_positive_keeps_exact_answers():
    p = F.cones(); base = F.SIM['demo6b-curved-cone-frustum-cut']['payload']
    r0,r1 = F.a3(base),F.a3(p)
    assert r0.status == r1.status == 'SERVED'
    assert r1.answer_exact == r0.answer_exact


def derived_highlight():
    p = F.demo1(); p['simulation_goals'].append({'goal_id':'highlight','kind':'highlight_geometry',
        'target_solid_id':'s_top','target_refs':['M'],'quote':p['simulation_goals'][0]['quote']})
    return p


def test_derived_highlight_positive_and_renaming():
    base=F.a3(F.demo1()); p=derived_highlight(); r=F.a3(p)
    assert r.status=='SERVED',(r.code,r.reason)
    assert r.answer_exact==base.answer_exact
    F.same_outcome(r,F.a3(F.rename_ids(p,{'s_top':'derived-top-1','s_abcd':'parent-1'})))


def test_derived_highlight_foreign_scope_refuses():
    p=derived_highlight(); p['simulation_goals'][-1]['target_solid_id']='ghost'
    assert F.outcome(F.a3(p))==('REFUSED','UNKNOWN_SOLID_ID')


def test_indirect_target_reads_are_in_census():
    assert {'plane1','plane2'} <= C.target_keys_read_by_routes()


def test_census_follows_helper_partial_and_keysets():
    source = '''
from functools import partial
def read(data, key):
    return data[key]
def delegated(data, key):
    return read(data, key)
def route(goal):
    t = goal.target
    alias = t
    getter = partial(delegated, alias)
    getter('plane1')
    delegated(t, 'plane2')
    t.get('solid_id')
    t['point']
    return set(t) == {'line', 'plane'}
'''
    assert C.target_keys_in_source(source) == {'plane1','plane2','solid_id','point','line','plane'}


def test_policy_snapshot_covers_all_actual_kind_fields():
    for group,model in MODELS.items():
        import typing
        assert set(POLICY['allowed_fields'][group])==set(typing.get_args(model.model_fields['kind'].annotation))
        assert set().union(*(set(fs) for fs in POLICY['allowed_fields'][group].values()))==set(model.model_fields)
    assert T.KIND_ALLOWED_FIELDS == POLICY['allowed_fields']


def test_v1_conversion_preserves_explicit_presence():
    p = F.demo1(); converted = T.convert_v1_to_v2(p,'adapter3')
    for old,new in zip(p['math_goals'],converted['math_goals']):
        assert set(old)==set(new)
    assert F.a4(p).code != 'INVALID_MATH_GOAL'


# Acceptance manifest v2 (source-grammar-adjudication/amendment-1.md): the v1 fresh-source controls are
# PENDING_SOURCE_GRAMMAR_SUPPORT (source_grammar_pending_diagnostics.py); these registered positives replace them.
ADJ = OUT / 'source-grammar-adjudication'
MANIFEST = json.loads((ADJ / 'acceptance-manifest.json').read_text(encoding='utf-8'))['added_to_acceptance']
SUPPORTED = ADJ / 'supported-positive-controls.json'


def test_supported_positive_controls_are_registered():
    assert hashlib.sha256(SUPPORTED.read_bytes().replace(b'\r\n', b'\n')).hexdigest() == MANIFEST['inputs_sha256_lf']


@pytest.mark.parametrize('scope', MANIFEST['expected']['every_case'])
def test_supported_positive_scope_aliases(scope):
    want = MANIFEST['expected']; p = json.loads(SUPPORTED.read_text(encoding='utf-8'))['cases'][scope]
    for name in want['every_route']:
        r = F.ROUTES[name](p); assert r.status == want['status'], (name, r.code, r.reason)
        assert {k: x['coef'] for k, x in r.answer_exact.items()} == want['answer_coef']
    assert A.run_typed_fact_next_route(p).source_verification['authority'] == want['a3_source_authority']


@pytest.mark.parametrize('route_name', ['a3','pl','a4'])
@pytest.mark.parametrize('curved', [False,True])
def test_required_preflight_cannot_be_bypassed(monkeypatch, route_name, curved):
    original=B._kiem_pham_vi_tien_de; entered=[]
    def checked(*args,**kwargs):
        entered.append(True); return original(*args,**kwargs)
    monkeypatch.setattr(B,'_kiem_pham_vi_tien_de',checked)
    F.ROUTES[route_name](F.cones() if curved else legacy_m())
    assert entered


def oracle_shape():
    # CIC-D1 amendment: scope moved from the target to the goal so the shape guard alone decides (code unchanged)
    p=F.sup(); p['math_goals']=[{'goal_id':'bad','kind':'measurement','goal_type':'distance','quote':F.Q,
                                'solid_id':'s1','target':{'segment':'SA'}}]
    assert F.outcome(F.a3(p))==('REFUSED','INVALID_MATH_GOAL')


def oracle_field():
    p=F.sup();p['math_goals'][0]['parent_solid_id']='s2'
    assert F.outcome(F.a3(p))==('REFUSED','INVALID_MATH_GOAL')


def oracle_target():
    p=F.sup();p['math_goals'][0]['target']['solid_b']='s2'
    assert F.outcome(F.a3(p))==('REFUSED','INVALID_MATH_GOAL')


MUTATIONS = ['operand_shape','string_iteration','kind_fields','closed_keys','s8_preflight','semantic_fallback',
             'curved_existence','curved_relations','derived_resolution']


@pytest.mark.parametrize('name',MUTATIONS)
def test_mandatory_mutants_are_killed(monkeypatch,name):
    if name in ('operand_shape','string_iteration'):
        oracle=oracle_shape
        def mutate():
            if name=='string_iteration': monkeypatch.setitem(T.GOAL_OPERAND_SHAPES,'segment','ref')
            else: F.mutate(monkeypatch,T,'_validate_goal_target',
                          'if not valid or shape.startswith("refs") and len(set(value)) != len(value):','if False:')
    elif name=='kind_fields':
        oracle=oracle_field
        def mutate():
            policy=T.KIND_ALLOWED_FIELDS['math_goal'];monkeypatch.setitem(policy,'measurement',[*policy['measurement'],'parent_solid_id'])
    elif name=='closed_keys':
        oracle=oracle_target
        def mutate():
            F.mutate(monkeypatch,T,'_validate_goal_target',
                'raise TypedFactNextValidationError("INVALID_MATH_GOAL", f"{goal.goal_id}: unexpected target keys {sorted(set(target) - allowed)}")','return')
    elif name=='s8_preflight':
        # CIC-D1 amendment (post-registration, n2-amendment.md): the superseded in-target form became schema-invalid
        oracle=lambda:test_legacy_constructed_ownership_precedes_capability('goal',False)
        def mutate(): F.mutate(monkeypatch,B,'_bridge','scoped = _kiem_pham_vi_tien_de(p, solids)','scoped = []')
    elif name=='semantic_fallback':
        def semantic(*args,**kwargs):raise A.TuChoi('SOURCE_OBJECT_MISMATCH','semantic probe')
        monkeypatch.setattr(B,'bridge',semantic)
        def oracle():
            try:A._shared_source_gate(T.parse_typed_fact_next(F.sup()))
            except A.TuChoi as exc: assert exc.code=='SOURCE_OBJECT_MISMATCH'
            else: raise AssertionError('semantic refusal became fallback')
        def mutate():F.mutate(monkeypatch,A,'_shared_source_gate','if exc.code not in _LEGACY_BRIDGE_CAPABILITIES:','if False:')
    elif name=='curved_existence':
        oracle=lambda:test_curved_unknown_qualified_label_is_terminal('shared_vertices')
        def mutate():F.mutate(monkeypatch,B,'_check_qualified_refs',
            'if (sid not in solids or label not in solids[sid].local_vertices()) and sid not in (owned or {}).get(canonical, set()):','if False:')
    elif name=='curved_relations':
        oracle=test_curved_unsupported_relation_is_not_ignored
        def mutate():F.mutate(monkeypatch,A._Adapter3Compiler,'run','self._preflight_curved_relations()','pass')
    else:
        oracle=test_derived_highlight_positive_and_renaming
        def mutate():F.mutate(monkeypatch,A._Adapter3Compiler,'_compile_derived_solids_and_goals',
            'self.solid_local_to_canonical[g.derived_solid_id] =','self.solid_local_to_canonical[parent_sid] =')
    oracle();mutate()
    with pytest.raises(AssertionError):oracle()
