"""Reviewer-3 probe harness. Usage: python -B harness.py <backend_dir> <probes_module> <out.json>
Imports `app` from <backend_dir>; fixtures always from the worktree docs (committed inputs)."""
import json, sys, os, importlib, traceback
from copy import deepcopy
from types import SimpleNamespace
from pathlib import Path

BACKEND = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(Path(__file__).parent))
os.environ['ALLOW_LIVE_AI'] = '0'

from app.ai import adapter3_simulation as A
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_typed_fact_next_planner_route
from app.simulation.geometry_functions.typed_fact_next import TypedFactNextValidationError, convert_v1_to_v2

WT = Path(r'D:/Documents/projects/algo-sim/.superpowers/worktrees/w3-f2-ratio-projection-language-grounding')
RUNS = WT / 'docs/evaluation/geometry/runs'
def _load(p): return json.loads(p.read_text(encoding='utf-8'))
SUP = _load(RUNS / 'hybrid-v2-w3-f2-ratio-projection-language-grounding/inputs/recovery-supplementary.json')['control']
A3DEV = {c['case_id']: c for c in _load(RUNS / 'typedfact-next-adapter3-simulation/corpus-dev.json')['cases']}
SIM = {c['case_id']: c for c in _load(RUNS / 'simulation-coverage-visual-validation/corpus-dev.json')['cases']}
DEV = _load(RUNS / 'hybrid-v2-w3-f2-ratio-projection-language-grounding/inputs/development.json')
INTERNAL = {'ADAPTER_INTERNAL_ERROR', 'ROUTE_INTERNAL_ERROR'}
SCOPE = {'UNKNOWN_SOLID_ID', 'UNKNOWN_SOLID', 'SOURCE_OBJECT_MISMATCH', 'AMBIGUOUS_REFERENCE', 'INVALID_MATH_GOAL',
         'INVALID_SIMULATION_GOAL', 'UNKNOWN_VERTEX_REF', 'INVALID_QUALIFIED_REF', 'UNKNOWN_SECTION_ID',
         'INVALID_DERIVED_SECTION', 'INVALID_VERTEX_CHAIN', 'INVALID_TYPED_FACT_NEXT'}


def a3(p): return A.run_typed_fact_next_route(deepcopy(p))
def pl(p): return run_typed_fact_next_planner_route(deepcopy(p))
def a4(p):
    q = deepcopy(p)
    try:
        q = convert_v1_to_v2(q, 'adapter3') if q.get('derived_sections') else {**q, 'schema_version': 'typed-fact-next/2'}
    except TypedFactNextValidationError as e:
        return SimpleNamespace(status='REFUSED', code=e.code, reason=e.detail)
    return run_typed_fact_next_v2_route(q)
ROUTES = {'a3': a3, 'pl': pl, 'a4': a4}


def run(p):
    out = {}
    for n, f in ROUTES.items():
        try:
            r = f(p)
            out[n] = [r.status, r.code, (getattr(r, 'reason', '') or '')[:160],
                      {k: str(v) for k, v in (getattr(r, 'answers', None) or {}).items()} if r.status == 'SERVED' else None]
        except Exception as e:  # escaped exception = boundary defect
            out[n] = ['RAISED', type(e).__name__, str(e)[:160], None]
    return out


def main():
    mod = importlib.import_module(sys.argv[2])
    results = []
    for name, expect, build, base in mod.probes(SimpleNamespace(SUP=SUP, A3DEV=A3DEV, SIM=SIM, DEV=DEV)):
        try:
            p = build()
        except Exception as e:
            results.append({'probe': name, 'expect': expect, 'build_error': repr(e)}); continue
        got = run(p)
        verdict = []
        for n, (st, code, _r, _a) in got.items():
            if st == 'RAISED' or code in INTERNAL:
                verdict.append(f'{n}:INTERNAL')
            elif expect == 'NEG' and st == 'SERVED':
                verdict.append(f'{n}:SERVED!')
        if expect == 'POS':
            bgot = run(base()) if base else None
            for n, (st, code, _r, _a) in got.items():
                if st != 'SERVED' and code in SCOPE and not (bgot and bgot[n][:2] == [st, code]):
                    verdict.append(f'{n}:FALSE_REFUSE({code})')
            if bgot:
                for n in got:
                    if bgot[n][0] == 'SERVED' and got[n][0] == 'SERVED' and bgot[n][3] != got[n][3]:
                        verdict.append(f'{n}:ANSWER_CHANGED')
        results.append({'probe': name, 'expect': expect, 'got': got, 'flags': verdict})
    Path(sys.argv[3]).write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding='utf-8')
    for r in results:
        g = r.get('got') or {}
        print(f"{r['probe']:<55} {r['expect']} " + ' '.join(f"{n}={v[0][:3]}/{v[1]}" for n, v in g.items())
              + (f"  <<{','.join(r['flags'])}>>" if r.get('flags') else '') + (f" BUILD_ERROR {r['build_error']}" if 'build_error' in r else ''))


if __name__ == '__main__':
    main()
