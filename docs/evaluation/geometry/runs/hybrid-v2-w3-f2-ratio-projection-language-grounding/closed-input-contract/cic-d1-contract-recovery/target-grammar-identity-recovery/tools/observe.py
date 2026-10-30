"""Offline, append-only schema and route observations, including clean detached baselines."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

ROOT = Path.cwd()
OUT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/tests/geometry')]
os.environ['ALLOW_LIVE_AI'] = '0'
sys.dont_write_bytecode = True
def offline(*a, **kw):
    raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = offline
socket.create_connection = offline
from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_typed_fact_next_planner_route
from app.simulation.geometry_functions import typed_fact_next as T
from copy import deepcopy

def schema(p, version):
    q = deepcopy(p)
    try:
        if version == 2:
            q = T.convert_v1_to_v2(q, 'adapter3') if q.get('derived_sections') else {**q, 'schema_version': 'typed-fact-next/2'}
        (T.parse_typed_fact_next_v2 if version == 2 else T.parse_typed_fact_next)(q)
        return None
    except T.TypedFactNextValidationError as e:
        return e.code

def a4(p):
    q = T.convert_v1_to_v2(p, 'adapter3') if p.get('derived_sections') else {**p, 'schema_version': 'typed-fact-next/2'}
    return run_typed_fact_next_v2_route(q)

def observe(p):
    row = {f'schema{n}': schema(p, n) for n in (1, 2)}
    for name, route in [('a3', run_typed_fact_next_route), ('pl', run_typed_fact_next_planner_route), ('a4', a4)]:
        try:
            r = route(deepcopy(p))
            row[name] = {'status': r.status, 'code': r.code,
                         'answer': getattr(r, 'answer_exact', None) if r.status == 'SERVED' else None}
        except T.TypedFactNextValidationError as e:
            row[name] = {'status': 'REFUSED', 'code': e.code, 'answer': None}
        except Exception as e:
            row[name] = {'status': 'EXCEPTION', 'code': type(e).__name__, 'answer': None}
    return row

if __name__ == '__main__':
    cases = json.loads((OUT / 'cases.json').read_text(encoding='utf-8'))
    results = {name: observe(case['payload']) for name, case in cases.items()}
    result = {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'cases_sha256': hashlib.sha256((OUT / 'cases.json').read_bytes()).hexdigest(),
              'live_provider_calls': 0, 'results': results}
    with Path(sys.argv[1]).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        f.write('\n')
    print('observed', len(results), result['head'])
