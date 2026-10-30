"""Owner-registered F7 (unmapped polyhedral measurement) and R1/R2 (identity order, derived parent) oracles.

Inputs are frozen in f7-narrow-recovery/cases.json before the product edit; expected codes come from the active
contract and the existing exact oracle, never from the runtime under test."""
from copy import deepcopy
import hashlib
import json

import pytest

from app.ai import adapter3_simulation as A
from app.simulation.geometry_functions import typed_fact_next as T
import test_cic_d1_locked_contract as D
import test_closed_input_contract as C
import test_scope_census_closure as F
import test_target_grammar_identity_recovery as G

OUT = G.OUT / 'f7-narrow-recovery'
CASES = json.loads((OUT / 'cases.json').read_text(encoding='utf-8'))
REG = json.loads((OUT / 'registration.json').read_text(encoding='utf-8'))
CAP = 'BRIDGE_UNSUPPORTED_MEASUREMENT'
def names(*classes): return [k for k, c in CASES.items() if c['class'] in classes]
ROUTED = [(k, r) for k, c in CASES.items() for r in (c['expected_routes'] or {})]


def test_frozen_inputs():
    assert hashlib.sha256((OUT / 'cases.json').read_bytes().replace(b'\r\n', b'\n')).hexdigest() == REG['input_sha256']


@pytest.mark.parametrize('case', list(CASES))
def test_schema_outcome_on_both_versions(case):
    c = CASES[case]
    assert D.schema_code(c['payload']) == c['expected_schema']
    assert D.schema_code(G.v2_input(c['payload'])) == c['expected_schema']


@pytest.mark.parametrize('case,route', ROUTED)
def test_route_outcome_and_refusal_hygiene(case, route):
    c = CASES[case]
    r = F.ROUTES[route](deepcopy(c['payload']))
    assert [r.status, r.code] == c['expected_routes'][route], (case, route, r.reason)
    if r.status == 'REFUSED':
        assert not any(getattr(r, f, None) for f in ('answers', 'answer_exact', 'scene3d')), (case, route)


@pytest.mark.parametrize('case', [k for k, c in CASES.items() if c['expected_a3_answer'] is not None])
def test_served_controls_keep_exact_oracle(case):
    r = F.a3(CASES[case]['payload'])
    assert r.status == 'SERVED', (r.code, r.reason)
    assert r.answer_exact == CASES[case]['expected_a3_answer']


@pytest.mark.parametrize('case', list(CASES))
def test_no_internal_error_on_any_route(case):
    for route in ('a3', 'pl', 'a4'):
        assert F.ROUTES[route](deepcopy(CASES[case]['payload'])).code not in F.INTERNAL, (case, route)


# ---- F7 root-cause guards -------------------------------------------------------------------------------------------
F7_RAISE = 'raise TuChoi("BRIDGE_UNSUPPORTED_MEASUREMENT", f"{mg.goal_id}: Adapter /3 chưa có phép đo "'


def test_unmapped_measurement_mutant_returns_the_internal_error():
    def oracle():
        assert F.outcome(F.a3(CASES['F7.prism.radius.solid']['payload'])) == ('REFUSED', CAP)
    oracle()
    with pytest.MonkeyPatch.context() as mp:
        D.mutate_many(mp, A._Adapter3Compiler, '_compile_derived_solids_and_goals',
                      [(F7_RAISE, F7_RAISE.replace('raise TuChoi(', 'None; ('))])
        with pytest.raises(AssertionError):
            oracle()


def test_internal_faults_are_not_masked_as_capability(monkeypatch):
    # The F7 refusal is a dispatch decision, not a KeyError handler: a planted KeyError still reaches the boundary.
    def boom(*a, **k):
        raise KeyError('planted')
    monkeypatch.setattr(A._Adapter3Compiler, '_compute_certified_math_goals', boom)
    r = F.a3(CASES['CTRL.G.distance.segment.plain']['payload'])
    assert (r.status, r.code) == ('REFUSED', 'ADAPTER_INTERNAL_ERROR') and 'planted' in r.reason


# ---- R1: namespace / ownership precede canonical identity distinctness ----------------------------------------------
@pytest.mark.parametrize('case', names('R1'))
def test_first_refusal_is_payload_layer_not_child_grammar(case):
    goal = CASES[case]['payload']['math_goals'][-1]
    assert C.child_code(T.MathGoalSpec, goal) is None
    assert D.schema_code(CASES[case]['payload']) == CASES[case]['expected_schema']


def test_identity_before_namespace_mutant_is_caught(monkeypatch):
    def oracle():
        assert D.schema_code(CASES['R1.unknown_ns_repeat']['payload']) == 'UNKNOWN_SOLID_ID'
        assert D.schema_code(CASES['R1.foreign_owner_repeat']['payload']) == 'SOURCE_OBJECT_MISMATCH'
    oracle()
    scope, identities = T._validate_declared_solid_scope, T._validate_goal_identities
    monkeypatch.setattr(T, '_validate_declared_solid_scope', lambda p, ids: (identities(p), scope(p, ids)))
    with pytest.raises(AssertionError):
        oracle()


# ---- R2: derived solids resolve to their own parent, never to another root ------------------------------------------
def _r2():
    # Goal-free copy: a mutant must fail the identity assertions below, not abort inside payload parsing.
    p = deepcopy(CASES['R2.derived_vs_other_root']['payload']); p['math_goals'] = []
    return T.parse_typed_fact_next(p)


def _ref(p, ref, scope=None):
    try:
        return T.canonical_vertex_ref(p, ref, scope)
    except T.TypedFactNextValidationError as e:
        return e.code


def _r2_identity_oracle():
    p = _r2()
    main = _ref(p, 'main_pyramid::S')
    assert main != 'AMBIGUOUS_REFERENCE'
    assert _ref(p, 'top_pyramid::S') == main
    assert _ref(p, 'S', 'top_pyramid') == main
    assert _ref(p, 'other::S') not in (main, 'AMBIGUOUS_REFERENCE')
    assert _ref(p, 'S') == 'AMBIGUOUS_REFERENCE'
    assert D.schema_code(CASES['R2.derived_alias_of_parent']['payload']) == 'INVALID_MATH_GOAL'
    assert D.schema_code(CASES['R2.derived_scoped_constructed']['payload']) is None


def test_derived_parent_mapping_with_two_roots():
    _r2_identity_oracle()


@pytest.mark.parametrize('case', [k for k in names('R2_POSITIVE') if CASES[k]['expected_routes'] is None])
def test_schema_valid_two_root_fixture_is_never_served(case):
    # The second root (S.EFG) has no premises: no route may serve from it; schema validity grants no capability.
    for route in ('a3', 'pl', 'a4'):
        r = F.ROUTES[route](deepcopy(CASES[case]['payload']))
        assert r.status == 'REFUSED' and not any(getattr(r, f, None) for f in ('answers', 'answer_exact', 'scene3d'))


@pytest.mark.parametrize('needle,replacement', [('ns = parents.get(ns, ns)', 'ns = ns'),
                                                ('parents.get(scope, scope)', 'scope')])
def test_derived_parent_mutants_are_caught(monkeypatch, needle, replacement):
    _r2_identity_oracle()
    D.mutate_many(monkeypatch, T, 'canonical_vertex_ref', [(needle, replacement)])
    with pytest.raises(AssertionError):
        _r2_identity_oracle()
