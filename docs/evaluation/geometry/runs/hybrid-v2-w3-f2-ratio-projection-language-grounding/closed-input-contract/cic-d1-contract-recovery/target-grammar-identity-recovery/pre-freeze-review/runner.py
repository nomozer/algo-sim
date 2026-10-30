"""Reviewer runner: python runner.py <backend_dir> <probes.json> <out.json>. Offline, read-only on the repo."""
import json, os, socket, sys, traceback
from copy import deepcopy
from types import SimpleNamespace

BACKEND, PROBES, OUT = sys.argv[1:4]
os.environ['ALLOW_LIVE_AI'] = '0'
os.environ.pop('GEMINI_API_KEY', None)
sys.dont_write_bytecode = True
def _offline(*a, **k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = _offline
socket.create_connection = _offline
sys.path.insert(0, BACKEND)


from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_typed_fact_next_planner_route
from app.simulation.geometry_functions import typed_fact_next as T


def to_v2(p):
    return T.convert_v1_to_v2(deepcopy(p), 'adapter3') if p.get('derived_sections') else {**deepcopy(p), 'schema_version': 'typed-fact-next/2'}


def schema(p, v):
    try:
        q = to_v2(p) if v == 2 else deepcopy(p)
        (T.parse_typed_fact_next_v2 if v == 2 else T.parse_typed_fact_next)(q)
        return None
    except T.TypedFactNextValidationError as e:
        return e.code
    except Exception as e:
        return 'EXC:' + type(e).__name__


def run(fn, p):
    try:
        r = fn(p)
    except T.TypedFactNextValidationError as e:
        return {'status': 'REFUSED', 'code': e.code, 'raised': True}
    except Exception as e:
        return {'status': 'EXCEPTION', 'code': type(e).__name__, 'msg': str(e)[:200]}
    ans = getattr(r, 'answer_exact', None) or None
    out = {'status': r.status, 'code': r.code, 'reason': (r.reason or '')[:160]}
    if r.status == 'SERVED':
        out['answer'] = ans
        out['answers'] = getattr(r, 'answers', None)
    else:
        out['leak'] = bool(getattr(r, 'scene3d', None) or getattr(r, 'answers', None) or ans)
    return out


def a4(p):
    try:
        q = to_v2(p)
    except T.TypedFactNextValidationError as e:
        return SimpleNamespace(status='REFUSED', code=e.code, reason=e.detail, answers=None, scene3d=None)
    return run_typed_fact_next_v2_route(q)


probes = json.loads(open(PROBES, encoding='utf-8').read())
res = {}
for name, p in probes.items():
    row = {'schema1': schema(p, 1), 'schema2': schema(p, 2)}
    row['a3'] = run(lambda q: run_typed_fact_next_route(deepcopy(q)), p)
    row['pl'] = run(lambda q: run_typed_fact_next_planner_route(deepcopy(q)), p)
    row['a4'] = run(a4, p)
    res[name] = row
with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(res, f, ensure_ascii=False, indent=1, default=str)
print('done', len(res), OUT)
