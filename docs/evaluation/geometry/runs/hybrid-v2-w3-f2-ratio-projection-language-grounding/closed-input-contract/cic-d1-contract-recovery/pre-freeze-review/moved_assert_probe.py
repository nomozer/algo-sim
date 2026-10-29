"""Re-apply the assertion removed from test_bridge_preserves_input_constraints_or_refuses (in memory) and run its params."""
import os, sys
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), 'tests', 'geometry'))
import pytest
import test_typedfactnext_planner_bridge as M
import app.ai.function_route as FR
orig = FR.run_typed_fact_next_planner_route
def checked(p):
    r = orig(p)
    if r.status != 'SERVED':
        assert r.scene3d is None and not r.answers, ('refusal carries output', r.code)
    return r
FR.run_typed_fact_next_planner_route = checked
params = [m for m in M.test_bridge_preserves_input_constraints_or_refuses.pytestmark if m.name == 'parametrize'][0].args[1]
bad = []
for case, code in params:
    try:
        M.test_bridge_preserves_input_constraints_or_refuses(case, code)
    except AssertionError as e:
        bad.append((case, str(e)[:120]))
print('params', len(params), 'violations', bad)
