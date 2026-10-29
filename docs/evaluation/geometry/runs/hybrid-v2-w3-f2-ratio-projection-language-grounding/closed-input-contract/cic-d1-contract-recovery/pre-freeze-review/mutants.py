"""Reviewer-authored mutants. Each runs in a FRESH process: apply one in-memory source mutation (repo files untouched),
then run the targeted CIC/scope test files in-process. cwd=<head>/backend, PYTHONPATH=.;tests/geometry.
Usage: python -B mutants.py <name|none> <basetemp>"""
import inspect, os, sys, textwrap
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests', 'geometry'))
import pytest
from app.ai import adapter3_simulation as A
from app.simulation.geometry_functions import typed_fact_next as T
from app.simulation.geometry_functions import typed_fact_next_bridge as B

MUTANTS = {
    # drop goal-level ownership from the ONE scope resolver (S8 then sees no scope for N2v2.goal_solid_id)
    'mscope_ignore_goal': (T, 'measurement_scope', 'return (goal.solid_id or goal.target.get("solid_id")',
                           'return (goal.target.get("solid_id")'),
    # CIC-D1 rule only guards `solid`, so `solid_id` beside operands slips through to a stripped/ignored path
    'rule_solid_only': (T, '_validate_goal_target', 'if operands and set(target) & scopes:',
                        'if operands and set(target) & {"solid"}:'),
    # pure-scope target accepted for every goal type (e.g. distance {solid_id: pr})
    'pure_scope_any': (T, '_validate_goal_target',
                       'valid = bool(set(target) & scopes) and any(set(a) <= scopes for a in alternatives)',
                       'valid = bool(set(target) & scopes)'),
    # S8 forgets derived-solid membership (positive control D.top.SM should then be refused)
    'derived_members_off': (B, '_kiem_pham_vi_tien_de', "if goal.kind != 'construct_derived_solid':", 'if True:'),
    # S8 resolves unqualified refs globally instead of in the claimed scope
    'identity_ignores_scope': (B, '_kiem_pham_vi_tien_de', 'solid = solids.get(ns or scope)', 'solid = solids.get(ns)'),
    # S8 drops its final qualified-reference existence check
    'qualified_check_off': (B, '_kiem_pham_vi_tien_de', '_check_qualified_refs(p.model_dump(), solids, owners)', 'pass'),
    # S8 skips math goals that carry an explicit scope claim mismatch
    'claimed_scope_off': (B, '_kiem_pham_vi_tien_de', 'if claimed is not None and own and claimed not in own:', 'if False:'),
}


def apply(owner, name, needle, replacement):
    src = textwrap.dedent(inspect.getsource(getattr(owner, name)))
    assert src.count(needle) == 1, (name, needle)
    ns = dict(vars(owner))
    exec(compile(src.replace(needle, replacement), f'<{name}-reviewer-mutant>', 'exec'), ns)
    setattr(owner, name, ns[name])
    for module in (B, A):
        if owner is T and name in vars(module):
            setattr(module, name, ns[name])


name = sys.argv[1]
if name != 'none':
    apply(*MUTANTS[name])
FILES = ['tests/geometry/test_cic_d1_locked_contract.py', 'tests/geometry/test_closed_input_contract.py',
         'tests/geometry/test_typed_fact_next_v2_distance_bridge.py', 'tests/geometry/test_scope_census_closure.py',
         'tests/geometry/test_unified_solid_scope.py', 'tests/geometry/test_premise_scope_recovery.py',
         'tests/geometry/test_adapter3_fallback_safety.py']
rc = pytest.main(['-q', '-p', 'no:cacheprovider', f'--basetemp={sys.argv[2]}', '--no-header', '-rN', '-k', 'not mutants_are_killed and not mutation', *FILES])
print(f'MUTANT {name}: pytest exit {rc} ->', 'KILLED' if (name != 'none' and rc == 1) else ('BASELINE PASS' if rc == 0 and name == 'none' else ('SURVIVED' if rc == 0 else f'rc={rc}')))
