"""Ordering-effect probes: an earlier semantic/data/provenance defect combined with an unsupported polyhedral radius.
usage: ordering.py <backend_dir> <parent_cases_json> <out_json> [--revert-f7]"""
import json, os, socket, sys, inspect, textwrap
from copy import deepcopy
def _deny(*a, **k): raise RuntimeError('network blocked')
socket.socket.connect = _deny; socket.create_connection = _deny; socket.getaddrinfo = _deny
os.environ.pop('ALLOW_LIVE_AI', None)
backend, cp, out = sys.argv[1], sys.argv[2], os.path.abspath(sys.argv[3])
os.chdir(backend); sys.path.insert(0, backend)
from app.ai import adapter3_simulation as A
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_typed_fact_next_planner_route
from app.simulation.geometry_functions import typed_fact_next as T
if '--revert-f7' in sys.argv:
    src = textwrap.dedent(inspect.getsource(A._Adapter3Compiler._compile_derived_solids_and_goals))
    i = src.index('else:  # F7'); i = src.rindex(chr(10), 0, i) + 1
    j = src.index('(mg.goal_id,))', i) + len('(mg.goal_id,))') + 1
    src = src[:i] + src[j:]; assert 'F7' not in src
    ns = dict(vars(A)); exec(compile(src, '<revert>', 'exec'), ns)
    A._Adapter3Compiler._compile_derived_solids_and_goals = ns['_compile_derived_solids_and_goals']
def a4(p):
    q = deepcopy(p)
    try: q = T.convert_v1_to_v2(q, 'adapter3') if q.get('derived_sections') else {**q, 'schema_version': 'typed-fact-next/2'}
    except T.TypedFactNextValidationError as e: return type('R', (), {'status': 'REFUSED', 'code': e.code, 'reason': e.detail})
    return run_typed_fact_next_v2_route(q)
R = {'a3': lambda p: A.run_typed_fact_next_route(deepcopy(p)), 'pl': lambda p: run_typed_fact_next_planner_route(deepcopy(p)), 'a4': a4}
C = json.load(open(cp, encoding='utf-8'))
prism = C['V.radius.solid']['payload']           # radius {solid: pr}
ctrl = C['G.distance.segment.plain']['payload']  # served prism distance control
cases = {}
def variants(base, tag):
    p = deepcopy(base); p['problem_text'] += ' BC = 11.'
    p['premises'].append({'kind': 'segment_length', 'args': {'segment': ['B', 'C'], 'value': '11'}, 'quote': 'BC = 11.'})
    cases[f'{tag}.contradiction_BC11'] = p                      # data contradiction (6-8-10 right triangle)
    p = deepcopy(base); p['premises'][1]['quote'] = 'AB bằng 6 không có trong đề.'
    cases[f'{tag}.premise_quote_absent'] = p                    # provenance defect on a premise
    p = deepcopy(base); p['math_goals'][-1]['quote'] = 'Câu hỏi không có trong đề.'
    cases[f'{tag}.goal_quote_absent'] = p                       # provenance defect on the goal itself
    p = deepcopy(base); p['premises'][1]['args']['value'] = '7'
    cases[f'{tag}.number_mismatch'] = p                         # value not in its quote
    p = deepcopy(base); p['length_unit'] = 'a'
    cases[f'{tag}.unit_mismatch'] = p
    cases[f'{tag}.plain'] = deepcopy(base)
variants(prism, 'radius')
lat = deepcopy(prism); lat['math_goals'][0]['goal_type'] = 'lateral_area'; variants(lat, 'lateral')
variants(ctrl, 'control_distance')
res = {}
for k, p in cases.items():
    row = {}
    for n, f in R.items():
        try: r = f(p); row[n] = [r.status, r.code]
        except BaseException as e: row[n] = ['EXCEPTION', type(e).__name__]
    res[k] = row
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in res.items(): print(k, v)
