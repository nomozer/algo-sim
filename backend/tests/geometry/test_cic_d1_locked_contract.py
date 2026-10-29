"""CIC-D1 — the locked V2 target grammar on every route, and N2 v2 ownership before capability.

Registered in closed-input-contract/cic-d1-contract-recovery/preregistration.md before the product edit. Inputs are the
concrete payloads of cases.json (SHA in registration.json); controls must keep the outcome observed at RED (1490e3cd).
"""
from copy import deepcopy
import hashlib
import inspect
import json
import textwrap

import pytest

from app.ai import adapter3_simulation as A
from app.simulation.geometry_functions import typed_fact_next as T
from app.simulation.geometry_functions import typed_fact_next_bridge as B
import test_scope_census_closure as F

D1 = F.RUN / 'closed-input-contract/cic-d1-contract-recovery'
REG = json.loads((D1 / 'registration.json').read_text(encoding='utf-8'))
CASES = json.loads((D1 / 'cases.json').read_text(encoding='utf-8'))['cases']
OBSERVED = json.loads((D1 / REG['controls_observed_at_red']).read_text(encoding='utf-8'))['results']
ROUTES = ('a3', 'pl', 'a4')
def names(cls): return [k for k, c in CASES.items() if c['class'] == cls]
def v1(p): return {**deepcopy(p), 'schema_version': 'typed-fact-next/1'}
def route(name, p): return F.ROUTES[name](v1(p))       # a4 relabels /1 back to /2 (test_scope_census_closure.a4)
def answer(r): return {k: [v.get('coef'), v.get('dim'), v.get('unit')] for k, v in (r.answer_exact or {}).items()} \
    if r.status == 'SERVED' else {}


def schema_code(payload):
    parse = T.parse_typed_fact_next_v2 if payload['schema_version'].endswith('/2') else T.parse_typed_fact_next
    try:
        parse(deepcopy(payload))
    except T.TypedFactNextValidationError as e:
        return e.code
    return None


def test_cases_are_registered():
    for name, sha in REG['sha256_lf'].items():
        assert hashlib.sha256((D1 / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == sha, name


# ── CIC-D1-A/B: scope keys inside a geometric target are refused at the schema, on /1 and /2 ────────────────────────

@pytest.mark.parametrize('case', names('NEG_LOCKED_GRAMMAR'))
def test_scope_key_inside_geometric_target_fails_at_schema(case):
    p = CASES[case]['payload']
    assert schema_code(p) == schema_code(v1(p)) == 'INVALID_MATH_GOAL'


@pytest.mark.parametrize('rname', ROUTES)
@pytest.mark.parametrize('case', names('NEG_LOCKED_GRAMMAR'))
def test_scope_key_inside_geometric_target_refused_on_every_route(case, rname):
    assert F.outcome(route(rname, CASES[case]['payload'])) == tuple(CASES[case]['expected'][rname])


@pytest.mark.parametrize('rname', ROUTES)
@pytest.mark.parametrize('case', names('CONTROL_UNCHANGED'))
def test_valid_targets_keep_their_outcome(case, rname):
    r, want = route(rname, CASES[case]['payload']), OBSERVED[case][rname]
    assert (r.status, r.code, answer(r)) == (want['status'], want['code'], want.get('answer', {}))


# ── N2 v2: valid-shape ownership violations are refused by S8 before any capability refusal or fallback ───────────

def s8_raises(p):
    parsed = T.parse_typed_fact_next(deepcopy(p))                         # (1) the payload passes schema and shape
    try:
        B._kiem_pham_vi_tien_de(parsed, {s.solid_id: s for s in parsed.solids})
    except A.TuChoi as e:
        return e.code
    return None


@pytest.mark.parametrize('rname', ROUTES)
@pytest.mark.parametrize('case', names('NEG_OWNERSHIP'))
def test_n2v2_ownership_refused_before_capability(monkeypatch, case, rname):
    p = CASES[case]['payload']; entered = []; original = B._kiem_pham_vi_tien_de
    def spy(*a, **k):
        entered.append(True); return original(*a, **k)
    monkeypatch.setattr(B, '_kiem_pham_vi_tien_de', spy)
    r = route(rname, p)
    assert entered                                                         # (2) S8 ran on this route
    assert F.outcome(r) == ('REFUSED', 'SOURCE_OBJECT_MISMATCH') and answer(r) == {}, (r.code, r.reason)
    assert 'mb' in (r.reason or '')                                        # the refusal names the measurement goal
    monkeypatch.setattr(B, '_kiem_pham_vi_tien_de', original)
    assert s8_raises(p) == 'SOURCE_OBJECT_MISMATCH'                       # (3) S8 itself detects the foreign point
    # (4) the same shape with the point's own solid reaches the capability layer on this route: semantics came first
    ctrl = CASES['N2v2.control_own_point']
    assert F.outcome(route(rname, ctrl['payload'])) == tuple(ctrl['expected'][rname])


def gate_code(p):
    try:
        A._shared_source_gate(T.parse_typed_fact_next(deepcopy(p)))
    except A.TuChoi as e:
        return e.code
    return None


@pytest.mark.parametrize('case', names('NEG_OWNERSHIP'))
def test_n2v2_adapter3_gate_is_terminal_not_fallback(case):
    assert gate_code(CASES[case]['payload']) == 'SOURCE_OBJECT_MISMATCH'   # (5) no LEGACY_SOURCE_AUTHORITY fallback


def test_n2v2_qualified_namespace_has_no_global_resolution():
    p = CASES['N2v2.qualified_namespace']['payload']                      # (6) M exists only in pyr1; pyr2::M never finds it
    assert all(F.outcome(route(n, p)) == ('REFUSED', 'SOURCE_OBJECT_MISMATCH') for n in ROUTES)


def test_n2v2_valid_constructed_point_is_served_with_exact_oracle():
    c = CASES['N2v2.control_own_point']; o = c['oracle']
    assert s8_raises(c['payload']) is None
    r = route('a3', c['payload'])
    assert F.outcome(r) == ('SERVED', None), (r.code, r.reason)
    assert answer(r)[o['goal']] == [o['coef'], o['dim'], o['unit']]


# ── CIC-D1 mutants: each oracle holds on the real code and fails on its mutant ─────────────────────────────────────

def mutate_many(monkeypatch, owner, name, pairs):
    source = textwrap.dedent(inspect.getsource(getattr(owner, name)))
    for needle, replacement in pairs:
        assert source.count(needle) == 1, (name, needle); source = source.replace(needle, replacement)
    namespace = dict(vars(T if owner is T else B if owner is B else A))
    exec(compile(source, f'<{name}-mutant>', 'exec'), namespace)
    monkeypatch.setattr(owner, name, namespace[name])
    for module in (B, A):
        if owner is T and name in vars(module):
            monkeypatch.setattr(module, name, namespace[name])


RULE = ('if operands and set(target) & scopes:', 'if False:')
S8_CALL = 'scoped = _kiem_pham_vi_tien_de(p, solids)  # semantic ownership precedes every capability refusal/fallback'


def oracle_closed_target():                       # schema layer alone guards /1 Adapter /3
    p = CASES['F.distance_point_plane.solid']['payload']
    assert schema_code(v1(p)) == 'INVALID_MATH_GOAL' and F.outcome(route('a3', p)) == ('REFUSED', 'INVALID_MATH_GOAL')


def oracle_locked_target8():                      # the locked Adapter /4 outcome
    p = CASES['F.distance_point_plane.solid']['payload']
    assert F.outcome(route('a4', p)) == ('REFUSED', 'INVALID_MATH_GOAL')


def oracle_n2v2_planner():
    assert F.outcome(route('pl', CASES['N2v2.goal_solid_id']['payload'])) == ('REFUSED', 'SOURCE_OBJECT_MISMATCH')


def oracle_n2v2_terminal():
    test_n2v2_adapter3_gate_is_terminal_not_fallback('N2v2.goal_solid_id')


CIC_D1_MUTANTS = {
    'remove_closed_target_rule': (oracle_closed_target, lambda mp: mutate_many(mp, T, '_validate_goal_target', [RULE])),
    'remove_s8': (oracle_n2v2_planner, lambda mp: mutate_many(mp, B, '_bridge', [(S8_CALL, 'scoped = []')])),
    'capability_before_s8': (oracle_n2v2_planner, lambda mp: mutate_many(mp, B, '_bridge', [
        (S8_CALL, 'scoped = []'),
        ('theo_ten = {s.notation: f for s, f in zip(p.solids, facts)}',
         'theo_ten = {s.notation: f for s, f in zip(p.solids, facts)}; scoped = _kiem_pham_vi_tien_de(p, solids)')])),
    'semantic_fallback': (oracle_n2v2_terminal, lambda mp: mutate_many(mp, A, '_shared_source_gate', [
        ('if exc.code not in _LEGACY_BRIDGE_CAPABILITIES:', 'if False:')])),
    'discard_target_scope_keys': (oracle_locked_target8, lambda mp: (
        mutate_many(mp, T, '_validate_goal_target', [RULE]),
        mutate_many(mp, B, '_distance_question', [('t = g.target', 't = {k: v for k, v in g.target.items() if k not in ("solid", "solid_id")}')]))),
}


@pytest.mark.parametrize('name', CIC_D1_MUTANTS)
def test_cic_d1_mutants_are_killed(monkeypatch, name):
    oracle, mutate = CIC_D1_MUTANTS[name]
    oracle(); mutate(monkeypatch)
    with pytest.raises(AssertionError):
        oracle()
