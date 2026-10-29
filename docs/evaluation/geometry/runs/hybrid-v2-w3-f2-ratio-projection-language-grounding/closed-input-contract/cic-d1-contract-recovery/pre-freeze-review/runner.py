"""Generic route runner. cwd = <tree>/backend. Usage: python -B runner.py <cases.json> <out.json>
Each case: {"payload": {...}, "a4_direct": bool?}. Records schema(/1,/2) code and (status, code, answers) on a3, pl, a4."""
import json, sys, os, traceback
from copy import deepcopy
from types import SimpleNamespace
sys.path.insert(0, os.getcwd())
assert os.environ.get('ALLOW_LIVE_AI') == '0'
from app.ai import adapter3_simulation as A
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_typed_fact_next_planner_route
from app.simulation.geometry_functions import typed_fact_next as T


def v(p, n): return {**deepcopy(p), 'schema_version': f'typed-fact-next/{n}'}


def a4(p):
    q = v(p, 1)
    try:
        q = T.convert_v1_to_v2(q, 'adapter3') if q.get('derived_sections') else v(q, 2)
    except T.TypedFactNextValidationError as e:
        return SimpleNamespace(status='REFUSED', code=e.code, reason=e.detail, answer_exact=None)
    return run_typed_fact_next_v2_route(q)


ROUTES = {'a3': lambda p: A.run_typed_fact_next_route(v(p, 1)),
          'pl': lambda p: run_typed_fact_next_planner_route(v(p, 1)),
          'a4': a4}


def ans(r):
    if getattr(r, 'status', None) != 'SERVED':
        return None
    ex = getattr(r, 'answer_exact', None) or {}
    out = {k: [str(x.get('coef')), x.get('dim'), x.get('unit')] if isinstance(x, dict) else str(x) for k, x in ex.items()}
    if not out:
        out = {'answers': json.loads(json.dumps(getattr(r, 'answers', None), default=str))}
    return out


def schema(p, n):
    f = T.parse_typed_fact_next_v2 if n == 2 else T.parse_typed_fact_next
    try:
        f(v(p, n)); return None
    except T.TypedFactNextValidationError as e:
        return e.code
    except Exception as e:
        return f'EXC:{type(e).__name__}'


cases = json.load(open(sys.argv[1], encoding='utf-8'))
res = {}
for name, c in cases.items():
    p = c['payload']; row = {'schema1': schema(p, 1), 'schema2': schema(p, 2)}
    for rn, f in ROUTES.items():
        try:
            r = f(p)
            row[rn] = [r.status, r.code, ans(r), (getattr(r, 'reason', None) or '')[:200]]
        except Exception as e:
            row[rn] = ['EXCEPTION', type(e).__name__, None, str(e)[:200]]
    if c.get('direct_v2') is not None:            # a /2 payload sent directly (no conversion)
        try:
            r = run_typed_fact_next_v2_route(v(c['direct_v2'], 2))
            row['a4_direct'] = [r.status, r.code, ans(r), (r.reason or '')[:200]]
        except Exception as e:
            row['a4_direct'] = ['EXCEPTION', type(e).__name__, None, str(e)[:200]]
    res[name] = row
json.dump(res, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
print('done', len(res))
