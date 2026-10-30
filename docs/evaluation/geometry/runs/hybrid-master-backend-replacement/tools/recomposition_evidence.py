"""Phase B: planner recomposition evidence on independently authored /4 payloads (pyramid from `measurement_probe.py`,
right prism from the locked test fixture). Reads the planner's own `calls` / `auxiliary` / `trace`; it scores nothing
by itself and invents no plan. Offline, 0 provider calls. Usage: recomposition_evidence.py [out.json]"""
import collections, json, sys
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path[:0] = [str(ROOT / 'backend'), str(HERE)]
from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402
from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism  # noqa: E402
_argv, sys.argv = sys.argv, sys.argv[:1]     # the probe writes its own receipt to argv[1] on import; keep it read-only
import measurement_probe as M  # noqa: E402  (runs its own scored probe on import; output is informational)
sys.argv = _argv


def plan(payload):
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == 'SERVED', (r.code, r.reason)
    calls = r.planner['calls']                       # `auxiliary` only annotates calls already listed here
    aux = {a['construct'] for a in r.planner.get('auxiliary') or []}
    return {'fns': [c['fn'] for c in calls], 'ids': [c['id'] for c in calls],
            'planner_derived': [c['fn'] for c in calls if c['id'] in aux], 'answers': r.answer_exact}


cases = {}
for qid, gt, target, question, _o in M.QUESTIONS:
    cases[f'pyramid.{qid}'] = plan(M.payload(gt, target, question))
cases['prism.d_point_plane'] = plan(_prism())
cases['prism.d_point_line'] = plan(_prism(ask=("Tính khoảng cách từ A' đến đường thẳng BC.",
                                                {"point": "A'", "line": ["B", "C"]})))

# Two goals on ONE payload that need the same foot of A on (SBC) and on SC: is any producer built twice?
both = M.payload('distance', {'point': 'A', 'plane': ['S', 'B', 'C']}, 'Tính khoảng cách từ A đến mặt phẳng (SBC).')
q2 = 'Tính khoảng cách từ A đến đường thẳng SC.'
both['problem_text'] += ' ' + q2
both['math_goals'].append({'goal_id': 'mg2', 'kind': 'measurement', 'goal_type': 'distance', 'solid_id': 's1',
                           'target': {'point': 'A', 'line': ['S', 'C']}, 'quote': q2.rstrip('.')})
cases['pyramid.two_goals'] = plan(both)
dup = collections.Counter(json.dumps({k: v for k, v in c.items() if k != 'id'}, sort_keys=True)
                          for c in run_typed_fact_next_v2_route(deepcopy(both)).planner['calls'])

pyr = set().union(*(set(v['fns']) for k, v in cases.items() if k.startswith('pyramid')))
pri = set().union(*(set(v['fns']) for k, v in cases.items() if k.startswith('prism')))
out = {'provider_calls': 0, 'cases': cases,
       'shared_primitives_pyramid_and_prism': sorted(pyr & pri),
       'pyramid_only': sorted(pyr - pri), 'prism_only': sorted(pri - pyr),
       'identical_calls_built_twice_in_two_goal_plan': [k for k, n in dup.items() if n > 1],
       'two_goal_answers': cases['pyramid.two_goals']['answers']}
print(json.dumps({k: v for k, v in out.items() if k != 'cases'}, ensure_ascii=False, indent=1))
for k, v in cases.items():
    print(k, v['fns'])
if len(sys.argv) > 1:
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1); f.write('\n')
