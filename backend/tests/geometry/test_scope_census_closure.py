"""Scope census closure (Owner GO HYBRID_V2_W3_F2_SCOPE_CENSUS_CLOSURE_AND_HYPHENATED_ID_RECOVERY).

Preregistered in `unified-solid-scope-closure/preregistration.md`. Findings F1–F6 come from
`unified-solid-scope/review.md`; field coverage is enforced against `schema-field-inventory.json`.
Inputs are committed fixtures; every mutation is built here and none is known to product code.
"""
from copy import deepcopy
import inspect
import json
from pathlib import Path
import re
import textwrap
from types import SimpleNamespace

import pytest

from app.ai import adapter3_simulation as A
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_typed_fact_next_planner_route
from app.simulation.geometry_functions import typed_fact_next as T
from app.simulation.geometry_functions import typed_fact_next_bridge as B
from app.simulation.geometry_functions.typed_fact_next import TypedFactNextValidationError, convert_v1_to_v2

import scope_field_census as C

RUNS = Path(__file__).resolve().parents[3] / 'docs/evaluation/geometry/runs'
RUN = RUNS / 'hybrid-v2-w3-f2-ratio-projection-language-grounding'
INVENTORY = json.loads((RUN / 'unified-solid-scope-closure/schema-field-inventory.json').read_text(encoding='utf-8'))
SUP = json.loads((RUN / 'inputs/recovery-supplementary.json').read_text(encoding='utf-8'))['control']
A3DEV = {c['case_id']: c for c in json.loads((RUNS / 'typedfact-next-adapter3-simulation/corpus-dev.json').read_text(encoding='utf-8'))['cases']}
SIM = {c['case_id']: c for c in json.loads((RUNS / 'simulation-coverage-visual-validation/corpus-dev.json').read_text(encoding='utf-8'))['cases']}
SCOPE_CODES = {'UNKNOWN_SOLID_ID', 'UNKNOWN_SOLID', 'SOURCE_OBJECT_MISMATCH', 'AMBIGUOUS_REFERENCE', 'INVALID_MATH_GOAL',
               'INVALID_SIMULATION_GOAL', 'UNKNOWN_VERTEX_REF', 'INVALID_QUALIFIED_REF', 'UNKNOWN_SECTION_ID'}
INTERNAL = {'ADAPTER_INTERNAL_ERROR', 'ROUTE_INTERNAL_ERROR'}
Q = 'Cho hình chóp S.ABCD.'


def sup(): return deepcopy(SUP)
def a3(p): return A.run_typed_fact_next_route(deepcopy(p))
def pl(p): return run_typed_fact_next_planner_route(deepcopy(p))
def a4(p):
    q = deepcopy(p)
    try:
        q = convert_v1_to_v2(q, 'adapter3') if q.get('derived_sections') else {**q, 'schema_version': 'typed-fact-next/2'}
    except TypedFactNextValidationError as e:
        return SimpleNamespace(status='REFUSED', code=e.code, reason=e.detail, answers=None)
    return run_typed_fact_next_v2_route(q)
ROUTES = {'a3': a3, 'pl': pl, 'a4': a4}
def outcome(r): return (r.status, r.code)


def refused_everywhere(p, code, routes=('a3', 'pl', 'a4')):
    got = {n: outcome(ROUTES[n](p)) for n in routes}
    assert all(v == ('REFUSED', code) for v in got.values()), got


def never_scope_refused(p, routes=('a3', 'pl', 'a4'), must_serve=('a3',), base=None):
    """Control: the routes that must serve do. On the others the valid addition changes nothing: same outcome as the
    unmodified `base` (a capability or source-gate refusal of the base stays exactly that), or, without a base, no
    scope/internal refusal."""
    for n in routes:
        r = ROUTES[n](p)
        if n in must_serve:
            assert r.status == 'SERVED', (n, r.code, getattr(r, 'reason', None))
        elif base is not None:
            assert outcome(r) == outcome(ROUTES[n](base)), (n, r.code, getattr(r, 'reason', None))
        else:
            assert r.status == 'SERVED' or (r.code not in SCOPE_CODES | INTERNAL), (n, r.code, getattr(r, 'reason', None))


def same_outcome(r0, r1):
    """Renaming solid ids must not change the verdict: same status, code and (served) exact answers."""
    assert (r1.status, r1.code) == (r0.status, r0.code), (r1.code, r1.reason)
    if r0.status == 'SERVED':
        assert getattr(r1, 'answer_exact', None) == getattr(r0, 'answer_exact', None)
        assert getattr(r1, 'answers', None) == getattr(r0, 'answers', None)


def rename_ids(value, mapping):
    """Consistently rename solid ids everywhere: ids, `id::X` refs, `U-V` edge keys and dict keys."""
    def one(s):
        if s in mapping: return mapping[s]
        for old, new in mapping.items():
            s = re.sub(rf'(^|-){re.escape(old)}::', rf'\g<1>{new}::', s)
        return s
    if isinstance(value, dict): return {one(k): rename_ids(v, mapping) for k, v in value.items()}
    if isinstance(value, list): return [rename_ids(v, mapping) for v in value]
    return one(value) if isinstance(value, str) else value


# ── F1: hyphenated solid ids ───────────────────────────────────────────────────────────────────────────────────────
def hyphen_sup():
    p = rename_ids(sup(), {'s1': 'pyr-1', 's2': 'pyr-2'})
    p['premises'][2]['args']['segment'] = ['pyr-1::S', 'pyr-1::A']
    p['premises'][4]['args']['segment'] = ['pyr-2::T', 'pyr-2::A']
    return p


def hyphen_dev07():
    c = deepcopy(A3DEV['A3-DEV-07']); p = rename_ids(c['payload'], {'pyr_sabc': 'pyr-s-abc'})
    sec = next(s for s in p['derived_sections'] if s.get('named_intersections'))
    sec['named_intersections'] = {f'pyr-s-abc::{k.split("-")[0]}-pyr-s-abc::{k.split("-")[1]}': v
                                  for k, v in sec['named_intersections'].items()}
    return c, p


def test_split_edge_key_grammar():
    assert T.split_edge_key('S-B') == ('S', 'B')
    assert T.split_edge_key("pyr-1::A-pyr-1::B'") == ('pyr-1::A', "pyr-1::B'")
    assert T.split_edge_key('a-b-c::S-C') == ('a-b-c::S', 'C')
    for bad in ('S', 'S-B-C', 'pyr-1::A', 'x::a-y::b'):
        with pytest.raises(TypedFactNextValidationError):
            T.split_edge_key(bad)


def test_f1_hyphenated_ids_serve_on_every_route():
    base, p = a3(sup()), hyphen_sup()
    for n in ('a3', 'pl', 'a4'):
        r = ROUTES[n](p)
        assert r.status == 'SERVED', (n, r.code, r.reason)
    assert a3(p).answer_exact == base.answer_exact
    c, q = hyphen_dev07()          # qualified hyphenated edge keys: same verdict and reason as the original
    r0, r1 = a3(c['payload']), a3(q)
    same_outcome(r0, r1); assert r1.reason == r0.reason
    c2 = deepcopy(A3DEV['A3-DEV-02']); q2 = rename_ids(c2['payload'], {'pyr1': 'pyr-1-a', 'pyr2': 'pyr-2'})
    r = a3(q2); assert r.status == 'SERVED', (r.code, r.reason); assert r.answer_exact == c2['oracle_exact']


@pytest.mark.parametrize('mutation,code', [
    (lambda p: p['premises'][2]['args'].__setitem__('segment', ['pyr-9::S', 'pyr-1::A']), 'UNKNOWN_SOLID_ID'),
    (lambda p: p['premises'][2]['args'].__setitem__('segment', ['pyr-2::T', 'pyr-2::A']), 'SOURCE_OBJECT_MISMATCH'),
    (lambda p: p['premises'][0].__setitem__('solid_id', 'pyr-9'), 'UNKNOWN_SOLID_ID'),
    (lambda p: p['math_goals'][0].__setitem__('solid_id', 'pyr-2'), 'SOURCE_OBJECT_MISMATCH')])
def test_f1_hyphenated_scope_violations_refuse(mutation, code):
    p = hyphen_sup(); mutation(p)
    refused_everywhere(p, code)


def test_f1_shared_label_ambiguity_stays_fail_closed():
    p = hyphen_sup(); p['premises'][0].pop('solid_id')
    refused_everywhere(p, 'AMBIGUOUS_REFERENCE')


# ── premises / sections / measurement goals ──────────────────────────────────────────────────────────────────────
def test_premise_scope_controls_serve():
    never_scope_refused(sup(), must_serve=('a3', 'pl', 'a4'))


@pytest.mark.parametrize('mutation,code', [
    (lambda p: p['premises'][0].__setitem__('solid_id', 'zz'), 'UNKNOWN_SOLID_ID'),
    (lambda p: p['premises'][2]['args'].__setitem__('segment', ['s2::T', 's1::A']), 'SOURCE_OBJECT_MISMATCH')])
def test_premise_scope_violations_refuse(mutation, code):
    p = sup(); mutation(p); refused_everywhere(p, code)


def test_section_scope_controls_serve():
    base = a3(SIM['demo1-pyramid-derived-section']['payload']); assert base.status == 'SERVED'
    p = demo1(); sec = p['derived_sections'][0]
    sec['through_point'] = 's_abcd::M'; sec['parallel_plane'] = ['s_abcd::A', 'B', 'C']
    r = a3(p); assert r.status == 'SERVED' and r.answer_exact == base.answer_exact


@pytest.mark.parametrize('field', ['through_point', 'parallel_plane', 'named_key'])
def test_section_scope_violations_refuse(field):
    p = deepcopy(SIM['demo1-pyramid-derived-section']['payload'])
    other = deepcopy(p['solids'][0]); other.update(solid_id='zz', notation='T.ABCD', quote='Cho hình chóp T.ABCD.')
    p['solids'].append(other); p['problem_text'] += ' Cho hình chóp T.ABCD.'
    sec = p['derived_sections'][0]
    if field == 'through_point': sec['through_point'] = 'zz::T'
    elif field == 'parallel_plane': sec['parallel_plane'] = ['zz::A', 'B', 'C']
    else: sec['named_intersections'] = {'zz::T-B': 'N'}
    assert outcome(a3(p)) == ('REFUSED', 'SOURCE_OBJECT_MISMATCH')


def measurement(sid, **target):
    g = {'goal_id': 'g2', 'kind': 'measurement', 'goal_type': 'distance', 'target': target,
         'quote': 'Tính khoảng cách từ S đến (ABCD).'}
    if sid: g['solid_id'] = sid
    p = sup(); p['math_goals'].append(g); p['problem_text'] += ' ' + g['quote']; return p


def test_measurement_scope_controls_serve():
    # Distance: Adapter /4 serves; Bridge /1 (planner route) and Adapter /3 have no distance capability here.
    never_scope_refused(measurement('s1', point='S', plane=list('ABCD')), must_serve=('a4',),
                        base=measurement(None, point='S', plane=list('ABCD')))
    p = sup(); p['math_goals'][0]['target'] = {'solid': 'S.ABCD'}
    never_scope_refused(p, must_serve=('a3', 'pl', 'a4'))           # F6: notation alias on the Bridge too


@pytest.mark.parametrize('mutation,code', [
    (lambda p: p['math_goals'][0].__setitem__('solid_id', 'zz'), 'UNKNOWN_SOLID_ID'),
    (lambda p: p['math_goals'][0].__setitem__('target', {'solid': 's1', 'solid_id': 's2'}), 'SOURCE_OBJECT_MISMATCH')])
def test_measurement_scope_violations_refuse(mutation, code):
    p = sup(); mutation(p); refused_everywhere(p, code)


@pytest.mark.parametrize('target', [{'point': 'S', 'plane': list('ABCD')}, {'point': 's1::S', 'plane': list('ABCD')}])
def test_measurement_operand_violations_refuse(target):
    refused_everywhere(measurement('s2', **target), 'SOURCE_OBJECT_MISMATCH')


def test_ratio_residual_controls_serve():
    c = deepcopy(A3DEV['A3-DEV-03']); r = a3(c['payload'])
    assert r.status == 'SERVED' and r.answer_exact == c['oracle_exact']


def test_ratio_residual_scope_refused():
    p = deepcopy(A3DEV['A3-DEV-03']['payload'])
    next(g for g in p['math_goals'] if g['kind'] == 'volume_ratio')['numerator_solid_id'] = 'zz'
    assert outcome(a3(p)) == ('REFUSED', 'UNKNOWN_SOLID_ID')


# ── F2: every relation kind ──────────────────────────────────────────────────────────────────────────────────────
def relation(kind, **fields):
    p = sup(); p['relations'] = [{'relation_id': 'r', 'kind': kind, 'quote': Q, **fields}]; return p


# Per kind: one relation whose declared side/scope is contradicted by an operand owned only by the other solid.
RELATION_NEGATIVES = {
    'containment': dict(solid_id='s2', container_ref='s1::SA', member_ref='s1::S'),
    'shared_vertices': dict(solid_a='s2', solid_b='s2', pairs=[['s1::S', 's2::T']]),
    'shared_faces': dict(solid_a='s1', solid_b='s2', face_a=list('SAB'), face_b=list('SAB')),
    'parallel': dict(solid_id='s2', entity_a=['S', 'A'], entity_b=['T', 'A']),
    'perpendicular': dict(solid_id='s2', entity_a=['S', 'A'], entity_b=list('ABCD')),
    'section_membership': dict(solid_id='s2', section_id='nope', member_refs=['S']),
    'coordinate_frame': dict(solid_id='s1', frame_id='root', anchor_refs=['T']),
}
RELATION_CODES = {'section_membership': 'UNKNOWN_SECTION_ID'}


def test_every_relation_kind_has_a_negative_case():
    assert set(RELATION_NEGATIVES) == set(C.kinds()['relation'])


@pytest.mark.parametrize('kind', sorted(RELATION_NEGATIVES))
@pytest.mark.parametrize('variant', ['contradicted', 'foreign'])
def test_relation_scope_violations_refuse_every_kind(kind, variant):
    fields = deepcopy(RELATION_NEGATIVES[kind])
    if variant == 'foreign':
        key = next(k for k in ('solid_id', 'solid_a') if k in fields); fields[key] = 'zz'
        code = 'UNKNOWN_SOLID_ID'
    else:
        code = RELATION_CODES.get(kind, 'SOURCE_OBJECT_MISMATCH')
    refused_everywhere(relation(kind, **fields), code)


def test_relation_controls_serve():
    p = sup(); p['relations'] = [
        {'relation_id': 'sf', 'kind': 'shared_faces', 'solid_a': 's1', 'solid_b': 's2', 'face_a': list('ABCD'), 'face_b': list('ABCD'), 'quote': Q},
        {'relation_id': 'pp', 'kind': 'perpendicular', 'solid_id': 's1', 'entity_a': ['S', 'A'], 'entity_b': list('ABCD'),
         'quote': 'SA vuông góc với (ABCD).'},
        {'relation_id': 'f', 'kind': 'coordinate_frame', 'solid_id': 's1', 'frame_id': 'root', 'anchor_refs': list('ABC'), 'quote': Q}]
    never_scope_refused(p, must_serve=('a3', 'pl', 'a4'))
    c = deepcopy(A3DEV['A3-DEV-02']); r = a3(c['payload'])               # containment / shared_vertices / frames
    assert r.status == 'SERVED' and r.answer_exact == c['oracle_exact']


# ── F3: every simulation-goal kind ───────────────────────────────────────────────────────────────────────────────
def sim_goal(**fields):
    p = sup(); p['simulation_goals'].append({'goal_id': 'h', 'quote': Q, **fields}); return p


SIM_NEGATIVES = {
    'construct_object': (dict(target_solid_id='s2', target_refs=['s1::S']), 'SOURCE_OBJECT_MISMATCH'),
    'highlight_geometry': (dict(target_solid_id='s2', target_refs=['S']), 'SOURCE_OBJECT_MISMATCH'),
    'construction_sequence': (dict(target_solid_id='zz'), 'UNKNOWN_SOLID_ID'),
}


def test_every_simulation_goal_kind_has_a_negative_case():
    covered = set(SIM_NEGATIVES) | {'construct_plane_section', 'construct_derived_solid'}   # demo1-based cases below
    assert covered == set(C.kinds()['simulation_goal'])


@pytest.mark.parametrize('kind', sorted(SIM_NEGATIVES))
def test_simulation_goal_scope_violations_refuse_every_kind(kind):
    fields, code = SIM_NEGATIVES[kind]
    refused_everywhere(sim_goal(kind=kind, **fields), code)


def demo1(): return deepcopy(SIM['demo1-pyramid-derived-section']['payload'])
def with_second_pyramid(p):
    other = deepcopy(p['solids'][0]); other.update(solid_id='zz', notation='T.ABCD', quote='Cho hình chóp T.ABCD.')
    p['solids'].append(other); p['problem_text'] += ' Cho hình chóp T.ABCD.'; return p


@pytest.mark.parametrize('case,code', [
    ('plane_section_target_other_solid', 'SOURCE_OBJECT_MISMATCH'),
    ('derived_apex_other_solid', 'SOURCE_OBJECT_MISMATCH'),
    ('derived_target_solid_id', 'INVALID_SIMULATION_GOAL'),
    ('highlight_unknown_token', 'UNKNOWN_VERTEX_REF'),
    ('highlight_section_of_other_scope', 'SOURCE_OBJECT_MISMATCH')])
def test_section_and_derived_simulation_goals_refuse(case, code):
    p = with_second_pyramid(demo1())
    plane = next(g for g in p['simulation_goals'] if g['kind'] == 'construct_plane_section')
    derived = next(g for g in p['simulation_goals'] if g['kind'] == 'construct_derived_solid')
    if case == 'plane_section_target_other_solid': plane['target_solid_id'] = 'zz'
    elif case == 'derived_apex_other_solid': derived['apex_ref'] = 'T'
    elif case == 'derived_target_solid_id': derived['target_solid_id'] = 's_abcd'
    elif case == 'highlight_unknown_token':
        p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'target_refs': ['Q9'], 'quote': p['simulation_goals'][0]['quote']})
    else:
        p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'target_solid_id': 'zz',
                                      'target_refs': ['sec_alpha'], 'quote': p['simulation_goals'][0]['quote']})
    assert outcome(a3(p)) == ('REFUSED', code)


@pytest.mark.parametrize('kind', ['construct_object', 'construct_plane_section', 'highlight_geometry', 'construction_sequence'])
def test_parent_solid_id_outside_derived_solid_refused(kind):
    # Owner D-A: no documented meaning outside construct_derived_solid → refused when present, never ignored.
    p = demo1(); g = {'goal_id': 'x', 'kind': kind, 'quote': p['simulation_goals'][0]['quote'], 'parent_solid_id': 's_abcd'}
    if kind == 'construct_object': g['target_solid_id'] = 's_abcd'
    if kind == 'construct_plane_section': g['target_section_id'] = 'sec_alpha'
    if kind == 'highlight_geometry': g['target_refs'] = ['M']
    p['simulation_goals'].append(g)
    assert outcome(a3(p)) == ('REFUSED', 'INVALID_SIMULATION_GOAL')


def test_simulation_goal_controls_serve():
    p = demo1()
    p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'target_solid_id': 's_abcd',
                                  'target_refs': ['sec_alpha', 's_top', 's_abcd::M', 'M'], 'quote': p['simulation_goals'][0]['quote']})
    never_scope_refused(p, must_serve=('a3',), base=demo1())
    never_scope_refused(sim_goal(kind='highlight_geometry', target_solid_id='s2', target_refs=['s2::T', 'A']),
                        must_serve=('a3', 'pl', 'a4'))
    c = deepcopy(A3DEV['A3-DEV-02']); r = a3(c['payload'])              # highlight of qualified refs + a solid id
    assert r.status == 'SERVED' and r.answer_exact == c['oracle_exact']


# ── F4: curved ownership ─────────────────────────────────────────────────────────────────────────────────────────
def cones():
    p = deepcopy(SIM['demo6b-curved-cone-frustum-cut']['payload'])
    q = 'Cho hình nón đỉnh T, tâm đáy K, điểm B thuộc đường tròn đáy, bán kính đáy R = 3, chiều cao h = 4'
    p['problem_text'] += ' ' + q + '.'
    p['solids'].append({'solid_id': 'cone2', 'solid_type': 'cone', 'notation': 'T.K', 'center': 'K', 'apex_or_top': 'T',
                        'rim_point': 'B', 'radius': '3', 'height': '4', 'quote': q})
    return p


@pytest.mark.parametrize('case', ['apex_other_cone', 'apex_other_cone_qualified', 'highlight_other_cone',
                                  'highlight_other_cone_qualified', 'relation_operand_other_cone'])
def test_f4_curved_ownership_refuses(monkeypatch, case):
    entered = []; original = A._Adapter3Compiler._run_curved_route
    monkeypatch.setattr(A._Adapter3Compiler, '_run_curved_route', lambda c: entered.append(1) or original(c))
    p = cones(); derived = next(g for g in p['simulation_goals'] if g['kind'] == 'construct_derived_solid')
    q = p['solids'][0]['quote']
    if case == 'apex_other_cone': derived['apex_ref'] = 'T'
    elif case == 'apex_other_cone_qualified': derived['apex_ref'] = 'cone2::T'
    elif case.startswith('highlight'):
        p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'target_solid_id': 'cone_main',
                                      'target_refs': ['cone2::T' if case.endswith('qualified') else 'T'], 'quote': q})
    else:
        p['relations'] = [{'relation_id': 'r', 'kind': 'perpendicular', 'solid_id': 'cone_main', 'entity_a': ['T', 'K'],
                           'entity_b': ['S', 'O'], 'quote': q}]
    assert outcome(a3(p)) == ('REFUSED', 'SOURCE_OBJECT_MISMATCH')
    assert not entered


def test_f4_curved_controls_serve():
    base = a3(SIM['demo6b-curved-cone-frustum-cut']['payload'])
    r = a3(cones()); assert r.status == 'SERVED' and r.answer_exact == base.answer_exact


# ── F5 / F6: typed refusals and aliases ──────────────────────────────────────────────────────────────────────────
def test_f5_curved_target_notation_alias_served():
    base = a3(SIM['demo6b-curved-cone-frustum-cut']['payload'])
    p = deepcopy(SIM['demo6b-curved-cone-frustum-cut']['payload']); p['math_goals'][0]['target'] = {'solid': 'S.O'}
    r = a3(p); assert r.status == 'SERVED' and r.answer_exact == base.answer_exact


@pytest.mark.parametrize('src,mutation,code', [
    ('curved', lambda p: p['math_goals'][2]['target'].__setitem__('section_id', 5), 'INVALID_MATH_GOAL'),
    ('curved', lambda p: p['math_goals'][2]['target'].__setitem__('section_id', 'nope'), 'UNKNOWN_SECTION_ID'),
    ('poly', lambda p: p['math_goals'].append({'goal_id': 'g2', 'kind': 'measurement', 'goal_type': 'distance',
                                               'target': {'point': {'a': 1}, 'plane': list('ABCD')}, 'quote': Q}), 'INVALID_MATH_GOAL')])
def test_f5_malformed_targets_refuse_typed(src, mutation, code):
    p = deepcopy(SIM['demo6b-curved-cone-frustum-cut']['payload']) if src == 'curved' else sup()
    mutation(p)
    assert outcome(a3(p)) == ('REFUSED', code)


def test_f6_goal_operand_keys_cover_every_key_the_routes_read():
    routes_read = C.target_keys_read_by_routes() - {'solid', 'solid_id', 'section_id'}
    assert routes_read <= set(T.GOAL_OPERAND_KEYS)
    assert {'plane1', 'plane2'} <= set(T.GOAL_OPERAND_KEYS)   # contract-level: not read by any route today
    p = measurement('s2', plane1=['S', 'B', 'C'], plane2=list('ABC'))      # S belongs to s1 only
    with pytest.raises(TypedFactNextValidationError) as e:
        T.parse_typed_fact_next(p)
    assert e.value.code == 'SOURCE_OBJECT_MISMATCH'


# ── metamorphic ──────────────────────────────────────────────────────────────────────────────────────────────────
CONTROLS = {'sup': SUP, 'A3-DEV-02': A3DEV['A3-DEV-02']['payload'], 'A3-DEV-07': A3DEV['A3-DEV-07']['payload'],
            'demo1': SIM['demo1-pyramid-derived-section']['payload'], 'demo6b': SIM['demo6b-curved-cone-frustum-cut']['payload']}


@pytest.mark.parametrize('name', sorted(CONTROLS))
def test_metamorphic_hyphen_rename_preserves_answers(name):
    base = CONTROLS[name]; ids = [s['solid_id'] for s in base['solids']]
    ids += [g['derived_solid_id'] for g in base['simulation_goals'] if g.get('derived_solid_id')]
    p = rename_ids(deepcopy(base), {i: f'{i}-x-1' for i in ids})
    for route in ('a3', 'pl', 'a4'):
        same_outcome(ROUTES[route](base), ROUTES[route](p))


def scope_slots(p):
    for i, x in enumerate(p.get('premises', [])):
        if 'solid_id' in x: yield x, 'solid_id'
    for x in p.get('relations', []):
        for k in ('solid_id', 'solid_a', 'solid_b'):
            if k in x: yield x, k
    for x in p.get('simulation_goals', []):
        for k in ('target_solid_id', 'parent_solid_id'):
            if k in x: yield x, k
    for x in p.get('math_goals', []):
        if 'solid_id' in x: yield x, 'solid_id'


@pytest.mark.parametrize('name', sorted(CONTROLS))
def test_metamorphic_foreign_scope_never_served(name):
    base = CONTROLS[name]
    for i in range(len(list(scope_slots(deepcopy(base))))):
        p = deepcopy(base); obj, key = list(scope_slots(p))[i]; obj[key] = 'foreign'
        assert a3(p).status != 'SERVED', (name, key)


@pytest.mark.parametrize('fields,code', [
    (dict(container_ref='s1', member_ref='T'), 'SOURCE_OBJECT_MISMATCH'),                  # T belongs to s2 only
    (dict(container_ref='s1', member_ref='S', solid_id='s2'), 'SOURCE_OBJECT_MISMATCH'),    # container vs declared scope
    (dict(container_ref='s1', member_ref='S'), None)])                                      # valid: base outcome kept
def test_containment_whole_solid_container_scopes_its_members(fields, code):
    p = relation('containment', **fields)
    if code: refused_everywhere(p, code)
    else: never_scope_refused(p, must_serve=('a3',))      # Bridge routes: containment is a capability refusal


# ── mutants: every guard is load-bearing (oracle holds on real code, fails on the mutant) ────────────────────────
def mutate(monkeypatch, owner, name, needle, replacement):
    source = textwrap.dedent(inspect.getsource(getattr(owner, name)))
    assert source.count(needle) == 1, (name, needle)
    namespace = dict(vars(T if owner is T else B if owner is B else A))
    exec(compile(source.replace(needle, replacement), f'<{name}-mutant>', 'exec'), namespace)
    monkeypatch.setattr(owner, name, namespace[name])
    # A source mutation changes every importer of the function: rebind the names the Bridge / Adapter /3 imported too.
    for module in (B, A):
        if owner is T and name in vars(module):
            monkeypatch.setattr(module, name, namespace[name])


def oracle_hyphen_edge_keys():
    c, q = hyphen_dev07(); assert outcome(a3(q)) == outcome(a3(c['payload']))


def oracle_qualified_scope():
    assert outcome(a4(measurement('s2', point='s1::S', plane=list('ABCD')))) == ('REFUSED', 'SOURCE_OBJECT_MISMATCH')


def oracle_relation_side():
    assert outcome(a4(relation('shared_vertices', **RELATION_NEGATIVES['shared_vertices']))) == ('REFUSED', 'SOURCE_OBJECT_MISMATCH')


def oracle_sim_goal_scope():
    p = sim_goal(kind='highlight_geometry', target_solid_id='s2', target_refs=['S'])
    assert outcome(a4(p)) == ('REFUSED', 'SOURCE_OBJECT_MISMATCH')


def oracle_parent():       # a same-label copy: only the parent ↔ section agreement (S3) tells the solids apart
    p = demo1(); other = deepcopy(p['solids'][0]); other['solid_id'] = 'zz'; p['solids'].append(other)
    next(g for g in p['simulation_goals'] if g['kind'] == 'construct_derived_solid')['parent_solid_id'] = 'zz'
    assert outcome(a3(p)) == ('REFUSED', 'SOURCE_OBJECT_MISMATCH')


def oracle_highlight_token():
    p = demo1(); p['simulation_goals'].append({'goal_id': 'h', 'kind': 'highlight_geometry', 'target_refs': ['Q9'],
                                                'quote': p['simulation_goals'][0]['quote']})
    assert outcome(a3(p)) == ('REFUSED', 'UNKNOWN_VERTEX_REF')


def oracle_apex():
    p = cones(); next(g for g in p['simulation_goals'] if g['kind'] == 'construct_derived_solid')['apex_ref'] = 'T'
    assert outcome(a3(p)) == ('REFUSED', 'SOURCE_OBJECT_MISMATCH')


def oracle_d_a():
    p = sup(); p['simulation_goals'][0]['parent_solid_id'] = 's1'
    assert outcome(a3(p)) == ('REFUSED', 'INVALID_SIMULATION_GOAL')


CLOSURE_MUTANTS = {
    'naive_hyphen_split': (T, 'split_edge_key', 'if len(cuts) != 1:', 'cuts = [text.find("-")]\n    if len(cuts) != 1:',
                           oracle_hyphen_edge_keys),
    'remove_qualified_scope_guard': (T, '_validate_declared_solid_scope', 'if scope is not None and ns not in family(scope):',
                                     'if False:', oracle_qualified_scope),
    'remove_relation_side_scope': (T, 'scope_records', 'r.solid_a or r.solid_id,', 'None,', oracle_relation_side),
    'remove_sim_goal_target_scope': (T, 'scope_records', 'g.target_solid_id or (section.target_solid_id if section else None)',
                                     'None', oracle_sim_goal_scope),
    'remove_parent_validation': (T, '_validate_declared_solid_scope', 'if g.target_section_id in sections:', 'if False:', oracle_parent),
    'remove_highlight_token_validation': (T, '_validate_declared_solid_scope',
        'refuse("UNKNOWN_VERTEX_REF", g.goal_id, f"{token!r} không chỉ tới đối tượng nào đã khai")', 'pass', oracle_highlight_token),
    'remove_apex_ownership': (T, 'scope_records', 'refs = [x for x in (g.apex_ref, *g.target_refs) if x and x not in ids]',
                              'refs = [x for x in g.target_refs if x not in ids]', oracle_apex),
    'remove_owner_decision_d_a': (T, '_validate_declared_solid_scope',
        'if g.kind != "construct_derived_solid" and g.parent_solid_id is not None:', 'if False:', oracle_d_a),
}


@pytest.mark.parametrize('name', sorted(CLOSURE_MUTANTS))
def test_closure_mutants_are_killed(monkeypatch, name):
    owner, fn, needle, replacement, oracle = CLOSURE_MUTANTS[name]
    oracle()
    mutate(monkeypatch, owner, fn, needle, replacement)
    with pytest.raises(AssertionError):
        oracle()


# ── coverage gate: every model field classified; every scope field mapped to rules, tests and product code ───────
def test_census_inventory_complete():
    fields = C.field_paths(); inv = INVENTORY['fields']
    assert set(fields) == set(inv), {'unclassified': sorted(set(fields) - set(inv)), 'stale': sorted(set(inv) - set(fields))}
    source = Path(__file__).read_text(encoding='utf-8')
    product = inspect.getsource(T) + inspect.getsource(B)
    for path, row in inv.items():
        if row['category'] not in INVENTORY['scope_categories']:
            continue
        for test in (row['positive_test'], row['negative_test']):
            assert f'def {test}(' in source, (path, test)
        for rule in row['rules']:
            assert re.search(rf'#\s*{rule}\b', product), (path, rule)
    assert INVENTORY['kinds'] == C.kinds()
