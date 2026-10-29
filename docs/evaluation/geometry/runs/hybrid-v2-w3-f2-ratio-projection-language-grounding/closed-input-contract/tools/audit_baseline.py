"""Offline, exclusive-create reproduction of the previous review's seeds; no product edits.

Usage: python -B audit_baseline.py BACKEND_DIR OUTPUT_NAME
This is an exploratory baseline audit, not Gate A or an independent review.
"""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from types import SimpleNamespace


OUT = Path(__file__).resolve().parents[1]
RUN = OUT.parent
ROOT = RUN.parents[4]
SEEDS = RUN / 'unified-solid-scope-closure/pre-freeze-review'
BACKEND = Path(sys.argv[1]).resolve()
DEST = OUT / sys.argv[2]
assert DEST.parent == OUT and not DEST.exists()
sys.path[:0] = [str(BACKEND), str(BACKEND / 'tests/geometry')]
sys.dont_write_bytecode = True
os.environ['ALLOW_LIVE_AI'] = '0'


def offline(*_args, **_kwargs):
    raise RuntimeError('OFFLINE_ONLY')


socket.socket.connect = offline
socket.create_connection = offline

from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_typed_fact_next_planner_route
from app.simulation.geometry_functions.typed_fact_next import (
    TypedFactNextValidationError, convert_v1_to_v2,
)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def a4(p):
    try:
        q = convert_v1_to_v2(p, 'adapter3') if p.get('derived_sections') else {
            **p, 'schema_version': 'typed-fact-next/2'}
    except TypedFactNextValidationError as e:
        return SimpleNamespace(status='REFUSED', code=e.code, answers=None, answer_exact=None)
    return run_typed_fact_next_v2_route(q)


ROUTES = {'a3': run_typed_fact_next_route, 'pl': run_typed_fact_next_planner_route, 'a4': a4}
FIXTURES = ROOT / 'docs/evaluation/geometry/runs'
F = SimpleNamespace(
    SUP=load(RUN / 'inputs/recovery-supplementary.json')['control'],
    A3DEV={c['case_id']: c for c in load(FIXTURES / 'typedfact-next-adapter3-simulation/corpus-dev.json')['cases']},
    SIM={c['case_id']: c for c in load(FIXTURES / 'simulation-coverage-visual-validation/corpus-dev.json')['cases']},
    DEV=load(RUN / 'inputs/development.json'),
)


def run(p):
    result = {}
    for name, route in ROUTES.items():
        try:
            r = route(deepcopy(p))
            result[name] = {'status': r.status, 'code': r.code,
                            'answers': getattr(r, 'answers', None),
                            'answer_exact': getattr(r, 'answer_exact', None)}
        except Exception as e:
            # Record an escaped exception as a defect, without storing a raw traceback.
            result[name] = {'status': 'RAISED', 'code': type(e).__name__}
    return result


rows = []
for i in range(1, 6):
    m = module(f'previous_review_probes_{i}', SEEDS / f'probes{i}.py')
    for name, expected, build, base in m.probes(F):
        p = build()
        rows.append({'probe': name, 'expected_class': expected, 'got': run(p),
                     'base': run(base()) if base else None,
                     'input_sha256': sha256(json.dumps(p, sort_keys=True, ensure_ascii=False).encode()).hexdigest()})

assert len(rows) == 203 and len({r['probe'] for r in rows}) == len(rows)
served_negatives = [{'probe': r['probe'], 'routes': [n for n, v in r['got'].items() if v['status'] == 'SERVED']}
                    for r in rows if r['expected_class'] == 'NEG' and any(v['status'] == 'SERVED' for v in r['got'].values())]
internals = [{'probe': r['probe'], 'route': n, 'code': v['code']} for r in rows for n, v in r['got'].items()
             if v['status'] == 'RAISED' or v['code'] in ('ADAPTER_INTERNAL_ERROR', 'ROUTE_INTERNAL_ERROR')]
census_path = BACKEND / 'tests/geometry/scope_field_census.py'
if census_path.exists():
    census = module('baseline_scope_census', census_path)
    target_keys = sorted(census.target_keys_read_by_routes())
    census_result = {'discovered_fields': len(census.field_paths()), 'target_keys': target_keys,
                     'missing_known_indirect_reads': sorted({'plane1', 'plane2'} - set(target_keys)),
                     'exhaustiveness_claim': False}
else:
    census_result = {'status': 'TOOL_NOT_PRESENT_ON_BASELINE', 'exhaustiveness_claim': False}
product_paths = ['app/simulation/geometry_functions/typed_fact_next.py',
                 'app/simulation/geometry_functions/typed_fact_next_bridge.py', 'app/ai/adapter3_simulation.py']
result = {
    'classification': 'EXPLORATORY_BASELINE_REPRODUCTION_NOT_GATE_A',
    'backend': str(BACKEND),
    'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=BACKEND, text=True).strip(),
    'live_provider_calls': 0,
    'seeds': {f'probes{i}.py': sha256((SEEDS / f'probes{i}.py').read_bytes()).hexdigest() for i in range(1, 6)},
    'product_sha256_bytes': {p: sha256((BACKEND / p).read_bytes()).hexdigest() for p in product_paths},
    'summary': {'total': len(rows), 'classes': dict(Counter(r['expected_class'] for r in rows)),
                'served_negative_probes': len(served_negatives), 'internal_results': len(internals)},
    'served_negatives': served_negatives, 'internals': internals,
    'census': census_result,
    'cases': rows,
}
with DEST.open('x', encoding='utf-8', newline='\n') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
    f.write('\n')
print(json.dumps({'output': str(DEST), 'summary': result['summary'], 'census': result['census']}, ensure_ascii=False))
