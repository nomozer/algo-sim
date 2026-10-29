"""Unified declared-solid-scope policy (Owner GO HYBRID_V2_W3_F2_UNIFIED_SOLID_SCOPE_VALIDATION).

Preregistered in `unified-solid-scope/preregistration.md`; census `solid-scope-census.md`. Inputs are committed
fixtures only; every mutation is built here, none is known to product code.
"""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.ai import adapter3_simulation as A
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions import typed_fact_next_bridge as B
from app.simulation.geometry_functions.typed_fact_next import convert_v1_to_v2

RUNS = Path(__file__).resolve().parents[3] / 'docs/evaluation/geometry/runs'
RUN = RUNS / 'hybrid-v2-w3-f2-ratio-projection-language-grounding'
SUP = json.loads((RUN / 'inputs/recovery-supplementary.json').read_text(encoding='utf-8'))['control']
A3DEV = {c['case_id']: c for c in json.loads(
    (RUNS / 'typedfact-next-adapter3-simulation/corpus-dev.json').read_text(encoding='utf-8'))['cases']}
SIM = {c['case_id']: c for c in json.loads(
    (RUNS / 'simulation-coverage-visual-validation/corpus-dev.json').read_text(encoding='utf-8'))['cases']}
DEV = {c['id']: c for c in json.loads((RUN / 'inputs/development.json').read_text(encoding='utf-8'))['cases']}


def sup(): return deepcopy(SUP)
def a3(p): return A.run_typed_fact_next_route(deepcopy(p))
def a4(p):
    q = deepcopy(p)
    q = convert_v1_to_v2(q, 'adapter3') if q.get('derived_sections') else {**q, 'schema_version': 'typed-fact-next/2'}
    return run_typed_fact_next_v2_route(q)
def outcome(r): return (r.status, r.code)
def refused(code): return ('REFUSED', code)
SERVED = ('SERVED', None)
SCOPE_CODES = {'UNKNOWN_SOLID_ID', 'UNKNOWN_SOLID', 'SOURCE_OBJECT_MISMATCH', 'AMBIGUOUS_REFERENCE', 'INVALID_MATH_GOAL'}


def assert_both(p, expected):
    """Negatives: both adapters refuse with the same scope code. Controls: Adapter /4 serves and Adapter /3 serves or
    refuses only for its own pre-existing capability limits (Adapter /3 `ask_distance_point_plane` is SCHEMA_INVALID
    on main too) — never for scope."""
    r3, r4 = a3(p), a4(p)
    if expected == SERVED:
        assert outcome(r4) == SERVED, (r4.code, r4.reason)
        assert r3.status == 'SERVED' or r3.code not in SCOPE_CODES, (r3.code, r3.reason)
    else:
        assert outcome(r3) == outcome(r4) == expected, (outcome(r3), outcome(r4))


def add_goal(p, goal):
    p['math_goals'].append(goal); p['problem_text'] += ' ' + goal['quote']; return p


def add_premise(p, prem):
    p['premises'] = [*p.get('premises', []), prem]; p['problem_text'] += ' ' + prem['quote']; return p


# ── MAJOR 1: distance / angle goal operands vs declared goal scope, both adapters ─────────────────────────────────
DIST = {'goal_type': 'distance', 'target': {'point': 'S', 'plane': list('ABCD')}, 'quote': 'Tính khoảng cách từ S đến (ABCD).'}
ANGLE = {'goal_type': 'angle', 'target': {'line': ['S', 'C'], 'plane': list('ABCD')}, 'quote': 'Tính góc giữa SC và (ABCD).'}


def scoped_goal(base, sid, **target):
    g = {'goal_id': 'g2', 'kind': 'measurement', **deepcopy(base)}
    if sid is not None: g['solid_id'] = sid
    g['target'].update(target)
    return add_goal(sup(), g)


@pytest.mark.parametrize('base', [DIST, ANGLE], ids=['distance', 'angle'])
@pytest.mark.parametrize('sid,target,expected', [
    ('s1', {}, SERVED), (None, {}, SERVED), ('s1', {'point': 's1::S'}, SERVED),
    ('s2', {}, refused('SOURCE_OBJECT_MISMATCH')), ('foreign', {}, refused('UNKNOWN_SOLID_ID')),
    ('s2', {'point': 's1::S'}, refused('SOURCE_OBJECT_MISMATCH'))])
def test_goal_operands_must_belong_to_declared_goal_scope(base, sid, target, expected):
    if base is ANGLE and 'point' in target:
        target = {'line': ['s1::S', 'C']}
    assert_both(scoped_goal(base, sid, **target), expected)


@pytest.mark.parametrize('sid,expected', [('s1', SERVED), ('s2', refused('SOURCE_OBJECT_MISMATCH'))])
def test_constructed_point_goal_operand_keeps_producer_scope(sid, expected):
    p = add_premise(sup(), {'kind': 'midpoint', 'solid_id': 's1', 'args': {'point': 'M', 'segment': ['S', 'A']},
                            'quote': 'M là trung điểm của SA.'})
    p = add_goal(p, {'goal_id': 'g2', 'kind': 'measurement', 'goal_type': 'distance', 'solid_id': sid,
                     'target': {'point': 'M', 'plane': list('ABCD')}, 'quote': 'Tính khoảng cách từ M đến (ABCD).'})
    assert_both(p, expected)


# ── MAJOR 2: curved route never runs before the declared scope is validated ──────────────────────────────────────
def cyl(): return deepcopy(SIM['demo6a-curved-cylinder-sections'])


def second_cylinder(p):
    s = deepcopy(p['solids'][0]); s.update(solid_id='zz', center='I', apex_or_top="I'", notation="I.I'",
                                          quote="Cho hình trụ I.I'.")
    s.pop('rim_point', None); p['solids'].append(s); p['problem_text'] += " Cho hình trụ I.I'."
    return p


def test_curved_controls_are_served_with_registered_answers():
    for cid in ('demo6a-curved-cylinder-sections', 'demo6b-curved-cone-frustum-cut'):
        r = a3(SIM[cid]['payload'])
        assert r.status == 'SERVED', (cid, r.code, r.reason)


def test_curved_explicit_valid_scopes_keep_the_answer():
    base = a3(cyl()['payload'])
    p = cyl()['payload']
    for g in p['math_goals']:
        if 'solid' in g['target']: g['solid_id'] = g['target']['solid']
    p['relations'] = [{'relation_id': 'f', 'kind': 'coordinate_frame', 'solid_id': 'cyl', 'frame_id': 'root',
                       'quote': p['solids'][0]['quote']}]
    r = a3(p)
    assert r.status == 'SERVED' and r.answer_exact == base.answer_exact


@pytest.mark.parametrize('mutation,code', [
    ('goal_foreign', 'UNKNOWN_SOLID_ID'), ('premise_foreign', 'UNKNOWN_SOLID_ID'), ('relation_foreign', 'UNKNOWN_SOLID_ID'),
    ('target_foreign', 'UNKNOWN_SOLID'), ('goal_other_vs_target', 'SOURCE_OBJECT_MISMATCH'),
    ('premise_qualified_other', 'SOURCE_OBJECT_MISMATCH'), ('premise_operands_of_other', 'SOURCE_OBJECT_MISMATCH')])
def test_curved_scope_violations_refuse_before_the_curved_route(monkeypatch, mutation, code):
    entered = []
    original = A._Adapter3Compiler._run_curved_route
    monkeypatch.setattr(A._Adapter3Compiler, '_run_curved_route', lambda c: entered.append(1) or original(c))
    p = cyl()['payload']; q = p['solids'][0]['quote']
    if mutation == 'goal_foreign': p['math_goals'][0]['solid_id'] = 'foreign'
    elif mutation == 'premise_foreign':
        add_premise(p, {'kind': 'segment_length', 'solid_id': 'foreign', 'args': {'segment': ['O', "O'"], 'value': '1'}, 'quote': q})
    elif mutation == 'relation_foreign':
        p['relations'] = [{'relation_id': 'f', 'kind': 'coordinate_frame', 'solid_id': 'foreign', 'frame_id': 'root', 'quote': q}]
    elif mutation == 'target_foreign': p['math_goals'][0]['target'] = {'solid': 'foreign'}
    elif mutation == 'goal_other_vs_target': second_cylinder(p); p['math_goals'][0]['solid_id'] = 'zz'
    elif mutation == 'premise_qualified_other':
        second_cylinder(p)
        add_premise(p, {'kind': 'segment_length', 'solid_id': 'cyl', 'args': {'segment': ['zz::I', "zz::I'"], 'value': '1'}, 'quote': q})
    else:
        second_cylinder(p)
        add_premise(p, {'kind': 'segment_length', 'solid_id': 'zz', 'args': {'segment': ['O', "O'"], 'value': '1'}, 'quote': q})
    assert outcome(a3(p)) == refused(code)
    assert not entered


def test_curved_route_runs_the_ownership_validator_first(monkeypatch):
    calls = []
    original = B._kiem_pham_vi_tien_de
    monkeypatch.setattr(B, '_kiem_pham_vi_tien_de', lambda p, s: calls.append(1) or original(p, s))
    assert a3(cyl()['payload']).status == 'SERVED' and calls


# ── MAJOR 3: goal-level solid_id on ratio / residual goals has no meaning (Owner Decision A) ─────────────────────
RATIO_CASES = [('A3', 'A3-DEV-02'), ('A3', 'A3-DEV-03'), ('A3', 'A3-DEV-09'), ('SIM', 'demo1-pyramid-derived-section')]


def ratio_case(src, cid):
    c = deepcopy((A3DEV if src == 'A3' else SIM)[cid]); return c, c['payload']


@pytest.mark.parametrize('src,cid', RATIO_CASES)
def test_unscoped_ratio_and_residual_controls_serve(src, cid):
    c, p = ratio_case(src, cid)
    r = a3(p)
    assert r.status == 'SERVED', (r.code, r.reason)
    if src == 'A3': assert r.answer_exact == c['oracle_exact']


@pytest.mark.parametrize('src,cid', RATIO_CASES)
@pytest.mark.parametrize('kind', ['volume_ratio', 'residual_volume'])
@pytest.mark.parametrize('value', ['foreign', 'declared'])
def test_goal_level_solid_id_on_ratio_or_residual_is_refused(src, cid, kind, value):
    _c, p = ratio_case(src, cid)
    goals = [g for g in p['math_goals'] if g['kind'] == kind]
    if not goals: pytest.skip(f'{cid} has no {kind} goal')
    goals[0]['solid_id'] = 'foreign' if value == 'foreign' else p['solids'][0]['solid_id']
    assert outcome(a3(p)) == refused('INVALID_MATH_GOAL')


# ── MINOR 4 / NEW-2: relation sides exist and own what the relation says they own ──────────────────────────────
Q = 'Cho hình chóp S.ABCD.'
@pytest.mark.parametrize('relation,code', [
    ({'kind': 'shared_faces', 'solid_a': 'foreign', 'solid_b': 's2', 'face_a': list('ABCD'), 'face_b': list('ABCD')}, 'UNKNOWN_SOLID_ID'),
    ({'kind': 'coordinate_frame', 'solid_id': 'foreign', 'frame_id': 'root'}, 'UNKNOWN_SOLID_ID'),
    ({'kind': 'shared_faces', 'solid_a': 's1', 'solid_b': 's2', 'face_a': list('SAB'), 'face_b': list('SAB')}, 'SOURCE_OBJECT_MISMATCH'),
    ({'kind': 'coordinate_frame', 'solid_id': 's1', 'frame_id': 'root', 'anchor_refs': ['s2::T']}, 'SOURCE_OBJECT_MISMATCH'),
    ({'kind': 'coordinate_frame', 'solid_id': 's1', 'frame_id': 'root', 'anchor_refs': ['T']}, 'SOURCE_OBJECT_MISMATCH')])
def test_relation_sides_are_validated_on_both_adapters(relation, code):
    p = sup(); p['relations'] = [{'relation_id': 'r', 'quote': Q, **relation}]
    assert outcome(a3(p)) == refused(code)
    assert outcome(a4(p)) == refused(code)


def test_valid_multi_solid_relations_are_kept():
    p = sup(); p['relations'] = [
        {'relation_id': 'sf', 'kind': 'shared_faces', 'solid_a': 's1', 'solid_b': 's2', 'face_a': list('ABCD'),
         'face_b': list('ABCD'), 'quote': Q},
        {'relation_id': 'f1', 'kind': 'coordinate_frame', 'solid_id': 's1', 'frame_id': 'root', 'anchor_refs': list('ABC'), 'quote': Q}]
    assert outcome(a3(p)) == SERVED and outcome(a4(p)) == SERVED
    c = deepcopy(A3DEV['A3-DEV-02'])
    assert a3(c['payload']).answer_exact == c['oracle_exact']


# ── MINOR 5 / NEW-1: declared derived solids are known; ancestry must agree with the section ───────────────────
def demo1(): return deepcopy(SIM['demo1-pyramid-derived-section']['payload'])
VQ = 'tỉ số thể tích khối chóp cắt bởi (α) so với S.ABCD'


@pytest.mark.parametrize('sid,known', [('s_top', True), ('ghost', False)])
def test_volume_goal_on_derived_solid(sid, known):
    p = demo1(); p['math_goals'].append({'goal_id': 'v_top', 'kind': 'measurement', 'goal_type': 'volume',
                                         'solid_id': sid, 'target': {'solid': sid}, 'quote': VQ})
    r3, r4 = a3(p), a4(p)
    if known:
        assert r3.status == 'SERVED', (r3.code, r3.reason)
        assert r4.code != 'UNKNOWN_SOLID_ID'
    else:
        assert outcome(r3) == outcome(r4) == refused('UNKNOWN_SOLID_ID')


@pytest.mark.parametrize('cid', ['demo1-pyramid-derived-section', 'demo6b-curved-cone-frustum-cut'])
@pytest.mark.parametrize('parent,code', [('section', None), ('foreign', 'UNKNOWN_SOLID_ID'), ('other', 'SOURCE_OBJECT_MISMATCH')])
def test_derived_solid_parent_must_be_the_sections_solid(cid, parent, code):
    p = deepcopy(SIM[cid]['payload'])
    g = next(g for g in p['simulation_goals'] if g['kind'] == 'construct_derived_solid')
    section_solid = next(s['target_solid_id'] for s in p['derived_sections'] if s['section_id'] == g['target_section_id'])
    if parent == 'section': g['parent_solid_id'] = section_solid
    elif parent == 'foreign': g['parent_solid_id'] = 'foreign'
    else:
        other = deepcopy(next(s for s in p['solids'] if s['solid_id'] == section_solid)); other['solid_id'] = 'zz'
        p['solids'].append(other); g['parent_solid_id'] = 'zz'
    r = a3(p)
    assert outcome(r) == (SERVED if code is None else refused(code)), r.reason


# ── MINOR 6: nested target scope ───────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize('goal_sid,target,expected', [
    ('s1', {'solid': 's1', 'solid_id': 's2'}, refused('SOURCE_OBJECT_MISMATCH')),
    ('s1', {'solid_id': 'foreign'}, refused('UNKNOWN_SOLID_ID')),
    (None, {'solid': 'T.ABCD', 'solid_id': 's1'}, refused('SOURCE_OBJECT_MISMATCH')),
    ('s1', {'solid_id': 's1'}, SERVED)])
def test_nested_target_solid_id_is_part_of_the_goal_scope(goal_sid, target, expected):
    p = sup(); g = p['math_goals'][0]; g['target'] = target
    if goal_sid is None: g.pop('solid_id', None)
    else: g['solid_id'] = goal_sid
    assert outcome(a3(p)) == expected
    assert outcome(a4(p)) == expected


# ── metamorphic: one valid scope value → foreign / contradicting solid is never served ─────────────────────────
def scope_slots(p):
    """Every declared solid-scope value of a payload, as (path, getter-container, key)."""
    for i, x in enumerate(p.get('premises', [])):
        if 'solid_id' in x: yield f'premises[{i}].solid_id', x, 'solid_id'
    for i, x in enumerate(p.get('math_goals', [])):
        if 'solid_id' in x: yield f'math_goals[{i}].solid_id', x, 'solid_id'
        for k in ('numerator_solid_id', 'denominator_solid_id', 'parent_solid_id', 'cut_solid_id'):
            if k in x: yield f'math_goals[{i}].{k}', x, k
    for i, x in enumerate(p.get('relations', [])):
        for k in ('solid_id', 'solid_a', 'solid_b'):
            if k in x: yield f'relations[{i}].{k}', x, k
    for i, x in enumerate(p.get('simulation_goals', [])):
        for k in ('target_solid_id', 'parent_solid_id'):
            if k in x: yield f'simulation_goals[{i}].{k}', x, k
    for i, x in enumerate(p.get('derived_sections', [])):
        yield f'derived_sections[{i}].target_solid_id', x, 'target_solid_id'


CONTROLS = [SUP, A3DEV['A3-DEV-02']['payload'], A3DEV['A3-DEV-03']['payload'],
            SIM['demo1-pyramid-derived-section']['payload'], SIM['demo6a-curved-cylinder-sections']['payload']]


@pytest.mark.parametrize('index', range(len(CONTROLS)))
def test_metamorphic_foreign_scope_is_never_served(index):
    base = CONTROLS[index]
    assert a3(base).status == 'SERVED'
    for path, _c, _k in list(scope_slots(deepcopy(base))):
        p = deepcopy(base)
        slot = next(s for s in scope_slots(p) if s[0] == path)
        slot[1][slot[2]] = 'foreign'
        assert a3(p).status != 'SERVED', path


def owned_only_by(p, label, sid):
    solids = {s['solid_id']: s for s in p['solids']}
    owners = {s for s, spec in solids.items() if label in B.parse_typed_fact_next(p).solids[list(solids).index(s)].local_vertices()}
    return owners == {sid}


def test_metamorphic_contradicting_premise_scope_is_never_served():
    base = SUP
    for i, prem in enumerate(base['premises']):
        sid = prem['solid_id']; other = 's2' if sid == 's1' else 's1'
        labels = {x.split('::')[-1] for v in prem['args'].values() for x in (v if isinstance(v, list) else [v])
                  if isinstance(x, str) and x[:1].isupper()}
        if not any(owned_only_by(base, lab, sid) for lab in labels):
            continue
        p = deepcopy(base); p['premises'][i]['solid_id'] = other
        assert a3(p).status != 'SERVED', i
        assert a4(p).status != 'SERVED', i
