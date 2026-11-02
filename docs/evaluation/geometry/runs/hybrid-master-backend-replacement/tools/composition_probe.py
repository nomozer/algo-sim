"""Continuation 18 — the property-defined points of `composition_oracle.py` run through the production opt-in path
`run_hybrid_offline` (verbatim quotes, bridge, Source Gate, planner, exact engine, Adapter /4), scored against that
independent oracle — never against the planner's own label.

Verdicts per case:
  SERVED_CORRECT / WRONG_SERVED          served; the squared answer equals / differs from the oracle's;
  CORRECT_REFUSAL                         a degenerate triangle (collinear) refused;
  REPRESENTATION_BLOCKED                  reachable, refused before planning (`INVALID_TYPED_FACT_NEXT`, bridge);
  SEARCH_EXHAUSTED                        reachable, refused on a search bound (`PLAN_TOO_LARGE`);
  REACHABLE_BUT_SEARCH_MISSED             reachable and representable, refused by the planner / engine otherwise.
Composition of a served case (from the CERTIFICATE it was served with, checked against the oracle):
  NECESSARY_COMPOSITION_SERVED            the oracle says composition is NECESSARY for the GOAL (no single Registry call
                                          on the named points reaches the centre, and the goal is not the same for every
                                          point of the triangle's plane — review MINOR-3), the chain has ≥ 2 distinct
                                          functions, and every fresh point of the chain is consumed by a later step;
  COMPOSED_NOT_NECESSARY                  served by the same search, but the centre or the goal is one call away.
Necessity is not discovery: whether the plan was DISCOVERED is the provenance question (review MAJOR-1/2), answered by
the planner's step provenance and by the C15 rule (`c15_rule_label`), both recorded per row.
Usage: composition_probe.py [out.json] [--arm NAME]   (`IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC`, 0 provider calls)
"""
import collections, functools, json, os, re, socket, sys, time
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(HERE))
os.environ['ALLOW_LIVE_AI'] = '0'
def _offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = _offline; socket.create_connection = _offline

import composition_oracle as O  # noqa: E402


def squared(x):
    m = re.fullmatch(r'(?P<p>\d+)?(?:√(?P<r>\d+))?(?:/(?P<q>\d+))?', x or '')
    if not m or not (m['p'] or m['r']):
        return F(0) if x == '0' else None
    p, r, q = F(m['p'] or 1), F(m['r'] or 1), F(m['q'] or 1)
    return p * p * r / (q * q)


def chain_of(route):
    aux = (route.get('planner') or {}).get('auxiliary') or ()
    return next((d for d in aux if d.get('rule') == 'effect-chain'), None)


def composition(route, case):
    """From the served certificate: the chain's functions, its fresh points and whether each is consumed downstream."""
    d = chain_of(route)
    if d is None:
        return 'NOT_ESTABLISHED', {}
    calls = {c['id']: c for c in (route.get('planner') or {}).get('calls') or ()}
    fresh = d.get('labels') or []

    def labels(v):
        return [v] if isinstance(v, str) else [x for u in v for x in labels(u)] if isinstance(v, (list, tuple)) else []

    def output(c):
        a = c['args']
        return a.get('image') if 'image' in a else a.get('point') if not c['fn'].startswith('ask_') else None
    chain_calls = [calls[e['call']] for e in d['chain'] if e['call'] in calls]
    used = {x: any(output(c) != x and x in labels(list(c['args'].values())) for c in chain_calls) for x in fresh}
    fns = sorted({e['fn'] for e in d['chain'] if not e['fn'].startswith('ask_')})
    # the plan up to fresh-label names: each step's function and its arguments that are source labels
    src = set(case['triangle'])
    plan = sorted(f"{c['fn']}({','.join(sorted(x for x in labels(list(c['args'].values())) if x in src))})"
                  for c in chain_calls if not c['fn'].startswith('ask_'))
    info = {'chain_functions': fns, 'plan': plan, 'fresh_points': fresh, 'fresh_consumed': used,
            'search_generated_steps': (route['planner'].get('search_telemetry') or {}).get('search_generated_steps')}
    if case['necessity'] != 'COMPOSITION_NECESSARY' or case['goal_direct']:
        return 'COMPOSED_NOT_NECESSARY', info
    ok = len(fns) >= 2 and fresh and all(used.values())
    return ('NECESSARY_COMPOSITION_SERVED' if ok else 'NOT_ESTABLISHED'), info


@functools.lru_cache(maxsize=1)
def _runner():
    import importlib.util
    spec = importlib.util.spec_from_file_location('s2_runner', ROOT / 'backend/scripts/run_s2_student_language_pilot.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def c15_rule_label(route, payload):
    """The reviewed C15 rule, COMPUTED by the S-2/R-1 runner's own `composition_label` (written before C18, unchanged) on
    the planner-made steps of the served route — never the planner's label."""
    runner = _runner()
    tel = route['planner'].get('search_telemetry') or {}
    own = set(tel.get('planner_originated_steps') or ())
    row = {'technical_failure': False, 'observed': {'status': 'SERVED'}, 'end_to_end_correct': True,
           'expected': {'outcome': 'SERVED'}, 'raw_extraction': payload,
           'search': {'planner_steps': [{k: c.get(k) for k in ('id', 'fn', 'args')}
                                        for c in route['planner'].get('calls') or () if c.get('id') in own]}}
    return runner.composition_label(row)


def run_all(arm=None):
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    from app.ai.typed_fact_next_extraction import ReplayExtractor
    policy = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})
    rows = []
    for c in O.cases(search=False):
        t0 = time.perf_counter()
        out = run_hybrid_offline(c['text'], ReplayExtractor({c['text']: c['payload']}), policy=policy).response
        ms = round((time.perf_counter() - t0) * 1000, 1)
        route = out['route_d']
        code = out['envelope'].get('reason_code')
        served = route['status'] == 'SERVED'
        got = [squared(str(v.get('coef'))) for v in (route.get('answer_exact') or {}).values()] if served else None
        want = F(c['want2']) if c['want2'] is not None else None
        if served:
            verdict = 'SERVED_CORRECT' if want is not None and got == [want] else 'WRONG_SERVED'
        elif c['necessity'] == 'DEGENERATE_TRIANGLE':
            verdict = 'CORRECT_REFUSAL'
        elif code in ('INVALID_TYPED_FACT_NEXT', 'INVALID_DESCRIBED_POINT') or (code or '').startswith('BRIDGE_'):
            verdict = 'REPRESENTATION_BLOCKED'
        elif code == 'PLAN_TOO_LARGE':
            verdict = 'SEARCH_EXHAUSTED'
        else:
            verdict = 'REACHABLE_BUT_SEARCH_MISSED'
        comp, info = composition(route, c) if served else (None, {})
        tel = (route.get('planner') or {}).get('search_telemetry') or {}
        rows.append({k: c[k] for k in ('id', 'topology', 'center', 'triangle', 'goal', 'necessity', 'goal_direct', 'want2')} | {
            'status': route['status'], 'code': code, 'verdict': verdict, 'got2': [str(g) for g in got] if got else None,
            'composition': comp, 'planner_label': tel.get('classification') if served else None,
            'c15_rule_label': c15_rule_label(route, c['payload']) if served else None,
            'explored_states': tel.get('explored_states'), 'search_depth': tel.get('search_depth'),
            'candidate_evaluations': tel.get('candidate_evaluations'), 'ms': ms, **info})
    return rows


def summary(rows):
    served = [r for r in rows if r['status'] == 'SERVED']
    return {'cases': len(rows),
            'verdicts': dict(collections.Counter(r['verdict'] for r in rows)),
            'verdict_by_necessity': {n: dict(collections.Counter(r['verdict'] for r in rows if r['necessity'] == n))
                                     for n in sorted({r['necessity'] for r in rows})},
            'refusal_codes': dict(collections.Counter(r['code'] for r in rows if r['status'] != 'SERVED')),
            'composition_of_served': dict(collections.Counter(r['composition'] for r in served)),
            'planner_label_vs_composition': dict(collections.Counter(f"{r['planner_label']} | {r['composition']}"
                                                                     for r in served)),
            'c15_rule_label_vs_composition': dict(collections.Counter(f"{r.get('c15_rule_label')} | {r['composition']}"
                                                                      for r in served)),
            'chain_functions_of_necessary': dict(collections.Counter(
                '+'.join(r['chain_functions']) for r in served if r['composition'] == 'NECESSARY_COMPOSITION_SERVED')),
            'max_explored_states': max((r['explored_states'] or 0 for r in rows), default=0),
            'max_search_depth': max((r['search_depth'] or 0 for r in rows), default=0),
            'ms_max': max(r['ms'] for r in rows), 'ms_median': sorted(r['ms'] for r in rows)[len(rows) // 2]}


if __name__ == '__main__':
    rows = run_all()
    s = summary(rows)
    print(json.dumps(s, ensure_ascii=False, indent=1))
    if len(sys.argv) > 1:
        import subprocess
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--', 'backend'], cwd=ROOT, text=True).strip())
        with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
            json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'provider_calls': 0, 'head': head,
                       'backend_tree_dirty': dirty, 'summary': s, 'rows': rows}, f, ensure_ascii=False, indent=1)
            f.write('\n')
