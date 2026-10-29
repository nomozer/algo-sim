"""Route behaviour under the surviving reviewer mutant `pure_scope_any` (cwd=<head>/backend). Repo files untouched."""
import inspect, json, os, sys, textwrap
from copy import deepcopy
sys.path.insert(0, os.getcwd())
from app.ai import adapter3_simulation as A
from app.simulation.geometry_functions import typed_fact_next as T
from app.simulation.geometry_functions import typed_fact_next_bridge as B
sys.argv = ['x', 'D:/tmp/cic-d1-pre-freeze-review/cases_probe.json', 'D:/tmp/cic-d1-pre-freeze-review/out_pure_scope_mutant.json']
src = textwrap.dedent(inspect.getsource(T._validate_goal_target))
needle = 'valid = bool(set(target) & scopes) and any(set(a) <= scopes for a in alternatives)'
assert src.count(needle) == 1
ns = dict(vars(T)); exec(compile(src.replace(needle, 'valid = bool(set(target) & scopes)'), '<m>', 'exec'), ns)
T._validate_goal_target = ns['_validate_goal_target']
cases = json.load(open(sys.argv[1], encoding='utf-8'))
sel = {k: v for k, v in cases.items() if k in ('G.distance.only_solid', 'G.distance.only_solid_id')}
for gt in ('distance', 'angle'):
    for key in ('solid', 'solid_id'):
        p = deepcopy(cases['G.distance.segment.plain']['payload']); g = p['math_goals'][-1]
        g['goal_type'] = gt; g['target'] = {key: 'pr'}
        sel[f'mut.{gt}.{key}'] = {'payload': p}
json.dump(sel, open('D:/tmp/cic-d1-pre-freeze-review/cases_pure_scope.json', 'w', encoding='utf-8'), ensure_ascii=False)
sys.argv[1] = 'D:/tmp/cic-d1-pre-freeze-review/cases_pure_scope.json'
exec(open('D:/tmp/cic-d1-pre-freeze-review/runner.py', encoding='utf-8').read())
for k, row in res.items():
    print(k, row['schema1'], row['schema2'], [row[r][:2] for r in ('a3', 'pl', 'a4')])
