"""Sixteenth continuation (§III.8): re-label the eleventh-continuation route-B recomposition matrix with the reviewed C15
rule. A planner-made step is SOURCE-EXPLICIT when it builds a point a fact describes (`point_kind` + the description's
labels in `points`); the rest is REGISTERED when it uses only functions of `registry.AUXILIARY_RULES`; DISCOVERED only
otherwise. Same 24 cases and the same route as `planner_recomposition_probe.py` (its `_build_cases`), offline, 0 calls.
Usage: route_b_composition_relabel.py [out.json]
"""
import collections, importlib.util, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'backend'))
_spec = importlib.util.spec_from_file_location('c11_probe', HERE / 'planner_recomposition_probe.py')
C11 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C11)

from app.ai.function_route import run_fact_route  # noqa: E402
from app.simulation.geometry_functions.registry import AUXILIARY_RULES  # noqa: E402

OUTPUT = {'midpoint': 'point', 'centroid': 'point', 'intersect_line_line': 'point', 'intersect_line_plane': 'point',
          'orthogonal_projection': 'image', 'orthogonal_projection_line': 'image'}
REGISTERED = {fn for fns in AUXILIARY_RULES.values() for fn in fns}


def leaves(v):
    if isinstance(v, (list, tuple)):
        for x in v:
            yield from leaves(x)
    elif isinstance(v, str):
        yield v.split('::')[-1]


def described(facts):
    return {(f['point_kind'], tuple(sorted(leaves(f.get('points') or ())))) for f in facts if f.get('point_kind')}


def label(steps, facts):
    stated = described(facts)
    beyond = [s for s in steps
              if (s['fn'], tuple(sorted(leaves([v for k, v in s['args'].items() if k != OUTPUT.get(s['fn'])])))) not in stated]
    if not steps:
        return 'NO_PLANNER_STEP', beyond
    if not beyond:
        return 'SOURCE_EXPLICIT_SEQUENCE', beyond
    return ('REGISTERED_DECOMPOSITION' if all(s['fn'] in REGISTERED for s in beyond)
            else 'DISCOVERED_FUNCTION_COMPOSITION'), beyond


rows = []
for c in C11._build_cases():
    r = run_fact_route(c['text'], {'facts': c['facts']})
    tel = (r.planner or {}).get('search_telemetry') or {}
    own = set(tel.get('planner_originated_steps') or ())
    steps = [{k: x[k] for k in ('id', 'fn', 'args')} for x in (r.planner or {}).get('calls') or () if x['id'] in own]
    strict, beyond = label(steps, c['facts']) if r.status == 'SERVED' else (f'REFUSED:{r.code}', [])
    rows.append({'id': c['id'], 'status': r.status, 'planner_label': tel.get('classification'), 'strict_label': strict,
                 'planner_steps': [s['fn'] for s in steps], 'beyond_description': [s['fn'] for s in beyond]})
    print(f"{c['id'][:58]:58s} {str(tel.get('classification')):32s} → {strict}")
summary = {'planner_label': dict(collections.Counter(str(r['planner_label']) for r in rows)),
           'strict_label': dict(collections.Counter(r['strict_label'] for r in rows))}
print(summary)
if len(sys.argv) > 1:
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'provider_calls': 0, 'route': 'B (flat TypedFact)',
                   'corrects': 'planner-recomposition-matrix.json (planner self-label)', 'summary': summary, 'rows': rows},
                  f, ensure_ascii=False, indent=1)
        f.write('\n')
