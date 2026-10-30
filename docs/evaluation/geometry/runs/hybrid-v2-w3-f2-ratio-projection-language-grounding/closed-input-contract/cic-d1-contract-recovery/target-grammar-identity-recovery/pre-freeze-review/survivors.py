"""Distinguishing inputs for the 3 surviving reviewer mutants: HEAD vs mutant, schema + routes."""
import json, os, socket, sys
from copy import deepcopy
from pathlib import Path
HERE = Path(__file__).parent
BACKEND = 'D:/Documents/projects/algo-sim/.superpowers/worktrees/w3-f2-ratio-projection-language-grounding/backend'
os.environ['ALLOW_LIVE_AI'] = '0'; sys.dont_write_bytecode = True
socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('OFFLINE'))
sys.path[:0] = [BACKEND, str(HERE)]
from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.ai.function_route import run_typed_fact_next_planner_route
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions import typed_fact_next as T
import mutplugin as MP

P = json.loads((HERE / 'probes.json').read_text(encoding='utf-8'))
def setgoal(p, target, sid=None):
    p = deepcopy(p); g = p['math_goals'][-1]; g['target'] = target
    g.pop('solid_id', None)
    if sid: g['solid_id'] = sid
    return p
inputs = {}
inputs['ghost_repeat'] = setgoal(P['F2.ws.tab'], {'segment': ['ghost::A', 'A']})
inputs['ghost_repeat_rev'] = setgoal(P['F2.ws.tab'], {'segment': ['A', 'ghost::A']})
inputs['foreign_repeat_scoped'] = setgoal(P['F2.two.pr_vs_other_B'], {'segment': ['pr::B', 'B']}, sid='other')
D = deepcopy(P['F2.der.ctrl_SM_top'])
D['solids'].append({'solid_id': 'other', 'solid_type': 'pyramid', 'notation': 'S.EFG', 'quote': 'Cho hình chóp S.ABCD', 'vertex_bindings': {'S': 'T'}})
inputs['der2_pos_scoped_SM'] = setgoal(D, {'segment': ['S', 'M']}, sid='top_pyramid')
inputs['der2_pos_qual_SM'] = setgoal(D, {'segment': ['top_pyramid::S', 'M']})
inputs['der2_neg_qual_alias'] = setgoal(D, {'segment': ['top_pyramid::S', 'main_pyramid::S']})
inputs['der2_neg_scoped_alias'] = setgoal(D, {'segment': ['S', 'main_pyramid::S']}, sid='top_pyramid')

def schema(p):
    try: T.parse_typed_fact_next(deepcopy(p)); return None
    except T.TypedFactNextValidationError as e: return e.code
def routes(p):
    out = {}
    for n, f in (('a3', run_typed_fact_next_route), ('pl', run_typed_fact_next_planner_route)):
        r = f(deepcopy(p)); out[n] = (r.status, r.code, (r.answer_exact or {}).get('rv', {}).get('coef') if r.status == 'SERVED' else None)
    try:
        q = {**deepcopy(p), 'schema_version': 'typed-fact-next/2'} if not p.get('derived_sections') else T.convert_v1_to_v2(deepcopy(p), 'adapter3')
        r = run_typed_fact_next_v2_route(q); out['a4'] = (r.status, r.code)
    except T.TypedFactNextValidationError as e:
        out['a4'] = ('REFUSED', e.code)
    return out

orig = {k: getattr(T, k) for k in ('_validate_goal_identities', '_validate_declared_solid_scope', 'canonical_vertex_ref')}
res = {'HEAD': {k: (schema(v), routes(v)) for k, v in inputs.items()}}
for m in ('M_no_derived_parent_ns', 'M_no_derived_parent_scope', 'M_identity_before_scope'):
    for k, v in orig.items(): setattr(T, k, v)
    os.environ['REVIEW_MUTANT'] = m; MP.pytest_configure(None)
    res[m] = {k: (schema(v), routes(v)) for k, v in inputs.items()}
for k, v in orig.items(): setattr(T, k, v)
lines = []
for k in inputs:
    for m in res:
        lines.append(f'{k:24s} {m:28s} schema={res[m][k][0]} routes={res[m][k][1]}')
    lines.append('')
(HERE / 'survivors.txt').write_text('\n'.join(lines), encoding='utf-8'); print('\n'.join(lines))
