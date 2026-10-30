"""Mixed curved+polyhedral payloads (curved route owns them): every goal type on the prism side. usage: mixed.py <backend> <parent_cases> <out>"""
import json, os, socket, sys
from copy import deepcopy
def _deny(*a, **k): raise RuntimeError('network blocked')
socket.socket.connect = _deny; socket.create_connection = _deny; socket.getaddrinfo = _deny
os.environ.pop('ALLOW_LIVE_AI', None)
b, cp, out = sys.argv[1], sys.argv[2], os.path.abspath(sys.argv[3]); os.chdir(b); sys.path.insert(0, b)
from app.ai import adapter3_simulation as A
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_typed_fact_next_planner_route
from app.simulation.geometry_functions import typed_fact_next as T
C = json.load(open(cp, encoding='utf-8'))
cyl, pr = C['K.cyl.radius.solid']['payload'], C['V.radius.solid']['payload']
base = deepcopy(cyl); base['problem_text'] = pr['problem_text'] + ' ' + cyl['problem_text']
base['solids'] += deepcopy(pr['solids']); base['premises'] = deepcopy(pr['premises'])
q = 'Tính bán kính.'
targets = {'radius.pr': ('radius', {'solid': 'pr'}), 'lateral.pr': ('lateral_area', {'solid': 'pr'}), 'volume.pr': ('volume', {'solid': 'pr'}),
           'radius.cyl': ('radius', {'solid': 'cyl'}), 'distance.prism_seg': ('distance', {'segment': ['A', "B'"]}),
           'area.pr': ('area', {'solid': 'pr'}), 'angle.pr': ('angle', {'line1': ['A', 'B'], 'line2': ["A'", "C'"]})}
res = {}
for k, (gt, t) in targets.items():
    p = deepcopy(base); p['math_goals'] = [{'goal_id': 'qx', 'kind': 'measurement', 'goal_type': gt, 'target': t, 'quote': q}]
    row = {'schema': None}
    try: T.parse_typed_fact_next(deepcopy(p))
    except T.TypedFactNextValidationError as e: row['schema'] = e.code
    for n, f in (('a3', A.run_typed_fact_next_route), ('pl', run_typed_fact_next_planner_route)):
        try: r = f(deepcopy(p)); row[n] = [r.status, r.code, (r.reason or '')[:90]]
        except BaseException as e: row[n] = ['EXCEPTION', type(e).__name__, str(e)[:90]]
    res[k] = row; print(k, row)
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
