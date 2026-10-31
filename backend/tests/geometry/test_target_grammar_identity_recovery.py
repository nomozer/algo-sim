"""Owner-registered F1/F2 behavior oracles; inputs frozen before product edits."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from app.simulation.geometry_functions import typed_fact_next as T
from app.simulation.geometry_functions import typed_fact_next_bridge as B
from app.ai.adapter4_route import run_typed_fact_next_v2_route
import test_scope_census_closure as F
import test_cic_d1_locked_contract as D
import test_closed_input_contract as C

OUT = D.D1 / 'target-grammar-identity-recovery'
CASES = json.loads((OUT / 'cases.json').read_text(encoding='utf-8'))
REG = json.loads((OUT / 'registration.json').read_text(encoding='utf-8'))
def names(cls): return [k for k, c in CASES.items() if c['class'] == cls]

#: Sixth continuation (hybrid-master): curved sections moved the /4 boundary inward (layer 1); the seventh continuation's
#: audit corrects it (layer 2, `corrects` layer 1, which stays untouched). A layer may only move a cell between REFUSED codes,
#: and each layer's `before` must be the previous layer's `after` (asserted) — the composed cell runs registered → last layer.
def load_transitions() -> dict:
    run = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement"
    out: dict = {}
    for i, name in enumerate(("registered-curved-control-transitions.json", "registered-curved-control-transitions-2.json",
                                  "registered-curved-control-transitions-3.json")):
        for k, v in json.loads((run / name).read_text(encoding="utf-8"))["cells"].items():
            assert v["before"][0] == v["after"][0] == "REFUSED", (name, k)
            if i:                                  # a later layer only corrects cells an earlier layer holds
                assert k in out and out[k]["after"] == v["before"], (name, k)
                out[k] = {**v, "before": out[k]["before"]}
            else:
                out[k] = v
    return out


_TRANSITIONS = load_transitions()


def v2_input(p):
    p = deepcopy(p); p['schema_version'] = 'typed-fact-next/2'
    for s in p.get('derived_sections', []):
        named = s.pop('named_intersections', {})
        edges = s.pop('cut_edges', [])
        s['stated_intersections'] = [{'edge':list(T.split_edge_key(e)), 'point':v, 'quote':s['quote']}
                                     for e,v in named.items()]
        if edges: s['declared_boundary'] = edges
    return p


def test_frozen_inputs_and_registered_alternatives():
    assert hashlib.sha256((OUT / 'cases.json').read_bytes().replace(b'\r\n', b'\n')).hexdigest() == REG['input_sha256']
    assert {k: sorted(map(sorted, v)) for k,v in T.GOAL_TARGET_ALTERNATIVES.items()} == {
        k: sorted(v) for k,v in REG['registered_alternatives'].items()}


@pytest.mark.parametrize('case', names('F1'))
def test_unregistered_target_fails_at_schema_boundary(case):
    p = CASES[case]['payload']
    # Child model only: downstream geometry/capability refusal cannot kill this oracle.
    assert C.child_code(T.MathGoalSpec, p['math_goals'][-1]) == 'INVALID_MATH_GOAL'
    assert D.schema_code(p) == 'INVALID_MATH_GOAL'
    assert D.schema_code(v2_input(p)) == 'INVALID_MATH_GOAL'


@pytest.mark.parametrize('case', names('F2'))
def test_namespace_identity_is_validated_before_dispatch(case):
    p, code = CASES[case]['payload'], CASES[case]['expected_schema']
    assert D.schema_code(p) == code
    assert D.schema_code(v2_input(p)) == code


@pytest.mark.parametrize('case', names('F1') + names('F2'))
@pytest.mark.parametrize('route', ['a3','pl','a4'])
def test_invalid_targets_are_terminal_on_routes(case, route):
    c = CASES[case]
    assert F.outcome(F.ROUTES[route](deepcopy(c['payload']))) == ('REFUSED', c['expected_schema'])


@pytest.mark.parametrize('case', names('F2'))
def test_identity_refusal_on_direct_v2_route(case):
    c = CASES[case]
    assert F.outcome(run_typed_fact_next_v2_route(v2_input(c['payload']))) == ('REFUSED', c['expected_schema'])


@pytest.mark.parametrize('case', names('CONTROL') + names('IDENTITY_CONTROL'))
def test_registered_controls_keep_schema_and_exact_route_outcomes(case):
    c = CASES[case]
    before = json.loads((OUT / 'observed-red.json').read_text(encoding='utf-8'))['results'][case]
    p = c['payload']
    assert D.schema_code(p) == before['schema1']
    for name in ['a3','pl','a4']:
        r = F.ROUTES[name](deepcopy(p))
        expected = (before[name]['status'], before[name]['code'])
        if (moved := _TRANSITIONS.get(f"target-grammar-identity-recovery::{case}::{name}")) is not None:
            assert expected == tuple(moved["before"])          # the layer corrects exactly the registered value
            expected = tuple(moved["after"])
        if expected[1] == 'ADAPTER_INTERNAL_ERROR':   # the 8 F7 cells; Owner D1 re-pins them (f7-narrow-recovery)
            expected = ('REFUSED', 'BRIDGE_UNSUPPORTED_MEASUREMENT')
        assert (r.status, r.code) == expected, (case,name,r.reason)
        if r.status == 'SERVED':
            assert r.answer_exact == before[name]['answer']


def test_distinct_vertices_retain_nonzero_exact_distance():
    r = F.a3(CASES['I.distinct']['payload'])
    assert r.status == 'SERVED', (r.code,r.reason)
    assert r.answer_exact['identity']['coef'] == '6'


def test_identity_control_passes_schema_without_display_name_merging():
    for case in names('IDENTITY_CONTROL'):
        assert D.schema_code(CASES[case]['payload']) is None, case


def test_scope_only_mutant_is_caught_by_schema_behavior(monkeypatch):
    def oracle():
        assert C.child_code(T.MathGoalSpec, {'goal_id':'q','kind':'measurement','goal_type':'radius',
            'target':{'solid_id':'s1'},'quote':'q'}) == 'INVALID_MATH_GOAL'
    oracle()
    D.mutate_many(monkeypatch,T,'_validate_goal_target',[
        ('valid = any(set(target) == set(a) for a in alternatives)', 'valid = bool(set(target) & scopes)')])
    with pytest.raises(AssertionError): oracle()


def test_canonical_distinctness_mutant_is_caught_at_schema(monkeypatch):
    def oracle():
        assert D.schema_code(CASES['I.forward']['payload']) == 'INVALID_MATH_GOAL'
    oracle()
    monkeypatch.setattr(T,'_validate_goal_identities',lambda p: None)
    with pytest.raises(AssertionError): oracle()


def test_identity_scope_mutant_loses_valid_binding_at_schema(monkeypatch):
    def oracle():
        assert D.schema_code(CASES['I.scoped_nonidentity']['payload']) == 'INVALID_MATH_GOAL'
    oracle()
    D.mutate_many(monkeypatch,T,'canonical_vertex_ref',[
        ('solids.get(ns or parents.get(scope, scope))', 'solids.get(ns)')])
    with pytest.raises(AssertionError): oracle()


def test_s8_mutant_is_caught_by_preflight_behavior(monkeypatch):
    def oracle():
        assert D.s8_raises(D.CASES['N2v2.goal_solid_id']['payload']) == 'SOURCE_OBJECT_MISMATCH'
    oracle()
    monkeypatch.setattr(B,'_kiem_pham_vi_tien_de',lambda p,s: [])
    with pytest.raises(AssertionError): oracle()


def test_s8_identity_scope_mutant_is_caught_by_behavior(monkeypatch):
    p = deepcopy(CASES['I.different_solids_same_label']['payload'])
    p['premises'] = []
    p['math_goals'][0].update(solid_id='other', target={'segment':['A','B']})
    def oracle():
        assert D.s8_raises(p) is None
    oracle()
    # Same fault (scope ignored) at the identity authority the bridge now delegates to (hybrid-master Task 1).
    D.mutate_many(monkeypatch,B,'_kiem_pham_vi_tien_de',[
        ('return canonical_vertex_ref(p, ref, scope)', 'return canonical_vertex_ref(p, ref)')])
    with pytest.raises(AssertionError): oracle()


def test_capability_exit_cannot_bypass_semantic_validation(monkeypatch):
    # Existing CIC-D1 route-layer mutant and oracle independently exercise ordering.
    oracle, mutate = D.CIC_D1_MUTANTS['capability_before_s8']
    oracle(); mutate(monkeypatch)
    with pytest.raises(AssertionError): oracle()


def test_cross_solid_policy_does_not_override_declared_ownership():
    p = F.sup()
    g = {'goal_id':'cross','kind':'measurement','goal_type':'distance',
         'target':{'segment':['s1::S','s2::T']},'quote':'Tính độ dài ST.'}
    p['math_goals'] = [g]; p['problem_text'] += ' ' + g['quote']
    # An unscoped measurement may combine resolved identities in the common chart.
    assert D.s8_raises(p) is None
    for sid in ['s1','s2']:
        scoped = deepcopy(p); scoped['math_goals'][0]['solid_id'] = sid
        F.refused_everywhere(scoped,'SOURCE_OBJECT_MISMATCH')
    # Premise compilation requires one owning solid; cross-solid premises remain refused.
    p['math_goals'] = []
    p['premises'].append({'kind':'segment_length','args':{'segment':['s1::S','s2::T'],'value':'1'},
                          'quote':'Tính độ dài ST.'})
    F.refused_everywhere(p,'SOURCE_OBJECT_MISMATCH')
