"""Reviewer-authored mutants against the new F7/R1/R2 oracles. usage: mutants.py <backend_dir> <out_json>. No network."""
import json, os, socket, sys, inspect, textwrap, traceback
def _deny(*a, **k): raise RuntimeError('network blocked')
socket.socket.connect = _deny; socket.create_connection = _deny; socket.getaddrinfo = _deny
os.environ.pop('ALLOW_LIVE_AI', None)
backend, out = sys.argv[1], os.path.abspath(sys.argv[2])
os.chdir(backend); sys.path[:0] = [backend, os.path.join(backend, 'tests', 'geometry')]
import pytest
import test_measurement_dispatch_and_identity_order as N
from app.ai import adapter3_simulation as A
from app.simulation.geometry_functions import typed_fact_next as T
D = N.D

def oracle_suite():
    """Run the new file's behavioural oracles (not its own mutant tests); return list of failing oracle names."""
    fails = []
    def chk(name, fn):
        try: fn()
        except BaseException as e: fails.append(f'{name}: {type(e).__name__} {str(e)[:120]}')
    for k, c in N.CASES.items():
        for r in (c['expected_routes'] or {}):
            chk(f'route[{k}-{r}]', lambda k=k, r=r: N.test_route_outcome_and_refusal_hygiene(k, r))
        chk(f'nointernal[{k}]', lambda k=k: N.test_no_internal_error_on_any_route(k))
        chk(f'schema[{k}]', lambda k=k: N.test_schema_outcome_on_both_versions(k))
        if c['expected_a3_answer'] is not None:
            chk(f'exact[{k}]', lambda k=k: N.test_served_controls_keep_exact_oracle(k))
    chk('r2_identity', N._r2_identity_oracle)
    for k in N.names('R1'):
        chk(f'r1[{k}]', lambda k=k: N.test_first_refusal_is_payload_layer_not_child_grammar(k))
    return fails

def src_mutant(mp, owner, name, pairs, ns_module):
    source = textwrap.dedent(inspect.getsource(getattr(owner, name)))
    for a, b in pairs:
        assert source.count(a) == 1, (name, a); source = source.replace(a, b)
    ns = dict(vars(ns_module)); exec(compile(source, f'<{name}-rev>', 'exec'), ns)
    mp.setattr(owner, name, ns[name])
    return ns[name]

MUT = {}
# R2: derived solids resolve to the FIRST root solid (main_pyramid happens to be first in the fixture)
MUT['R2_first_root'] = lambda mp: src_mutant(mp, T, 'canonical_vertex_ref',
    [('ns = parents.get(ns, ns)', 'ns = (p.solids[0].solid_id if ns in parents else ns)'),
     ('parents.get(scope, scope)', '(p.solids[0].solid_id if scope in parents else scope)')], T)
# R2: derived solids resolve to the LAST root solid (wrong root)
MUT['R2_last_root'] = lambda mp: src_mutant(mp, T, 'canonical_vertex_ref',
    [('ns = parents.get(ns, ns)', 'ns = (p.solids[-1].solid_id if ns in parents else ns)'),
     ('parents.get(scope, scope)', '(p.solids[-1].solid_id if scope in parents else scope)')], T)
# R1: identity distinctness checked BEFORE ownership/namespace inside the model validator body
def r1_swap(mp):
    scope, ident = T._validate_declared_solid_scope, T._validate_goal_identities
    def s(p, known): ident(p); return scope(p, known)
    mp.setattr(T, '_validate_declared_solid_scope', s)
MUT['R1_identity_first'] = r1_swap
# R1: namespace check dropped for unknown ns in canonical_vertex_ref only (no order change) -- control mutant
# F7: silently drop the unsupported goal (partial serve) instead of refusing
MUT['F7_silent_drop'] = lambda mp: src_mutant(mp, A._Adapter3Compiler, '_compile_derived_solids_and_goals',
    [(N.F7_RAISE, 'math_call_ids.pop(mg.goal_id); None and ("BRIDGE_UNSUPPORTED_MEASUREMENT", f"{mg.goal_id}: Adapter /3 chưa có phép đo "')], A)
# F7: wrong typed code (semantic instead of capability)
MUT['F7_semantic_code'] = lambda mp: src_mutant(mp, A._Adapter3Compiler, '_compile_derived_solids_and_goals',
    [(N.F7_RAISE, N.F7_RAISE.replace('BRIDGE_UNSUPPORTED_MEASUREMENT', 'INVALID_MATH_GOAL'))], A)
# F7 alt fix by MASKING: no else; KeyError around hoi[cid] converted to capability code
def mask(mp):
    src_mutant(mp, A._Adapter3Compiler, '_compile_derived_solids_and_goals', [(N.F7_RAISE, N.F7_RAISE.replace('raise TuChoi(', 'None; ('))], A)
    src_mutant(mp, A._Adapter3Compiler, '_compute_certified_math_goals',
        [('kq_var = hoi[cid]', 'kq_var = hoi[cid] if cid in hoi else (_ for _ in ()).throw(TuChoi("BRIDGE_UNSUPPORTED_MEASUREMENT", "masked"))')], A)
MUT['F7_mask_instead_of_dispatch'] = mask

res = {'baseline': oracle_suite()}
for name, m in MUT.items():
    with pytest.MonkeyPatch.context() as mp:
        try:
            m(mp); res[name] = oracle_suite()
        except BaseException:
            res[name] = ['MUTANT_SETUP_ERROR ' + traceback.format_exc()[-300:]]
# Does the file's own F7 mutant test + planted-fault test detect the masking alternative?
with pytest.MonkeyPatch.context() as mp:
    src_mutant(mp, A._Adapter3Compiler, '_compute_certified_math_goals',
        [('kq_var = hoi[cid]', 'kq_var = hoi[cid] if cid in hoi else (_ for _ in ()).throw(TuChoi("BRIDGE_UNSUPPORTED_MEASUREMENT", "masked"))')], A)
    own = {}
    for t in ('test_unmapped_measurement_mutant_returns_the_internal_error',):
        try: getattr(N, t)(); own[t] = 'PASS'
        except BaseException as e: own[t] = f'FAIL {type(e).__name__}'
    with pytest.MonkeyPatch.context() as mp2:
        try: N.test_internal_faults_are_not_masked_as_capability(mp2); own['planted'] = 'PASS'
        except BaseException as e: own['planted'] = f'FAIL {type(e).__name__}'
    res['own_tests_vs_mask_plus_else'] = own
summary = {k: (len(v) if isinstance(v, list) else v) for k, v in res.items()}
json.dump({'summary': summary, 'detail': res}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False, indent=1))
