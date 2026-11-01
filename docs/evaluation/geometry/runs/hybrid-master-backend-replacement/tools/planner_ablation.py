"""Sixteenth continuation (§V.5.4): where does each served plan come from? Ablation in THIS process only (monkeypatch);
the production defaults are untouched.

Arms on the same cases (the C13 /4 probe positives, the R-1 pilot gold and the C11 route-B matrix):
  B  planner /24 as shipped;
  C  every declared decomposition off — the three derived-plane rules and `DINH_CAT_CANH` refuse, and contracts whose
     source policy is a declared rule's (the foot of distance(point,line), section vertices, declared intersections)
     are hidden from the effect resolver;
  D  search budget cut to depth 1 / 4 needs / 2 candidates.
A (planner /23) differs from B only in `search_telemetry` (commit b70995db diff; 41/41 preview fixtures verify), so it is
not re-run. A case "survives" an arm when it is still served with the same exact answers.
IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC, offline, 0 provider calls. Usage: planner_ablation.py [out.json]
"""
import collections, contextlib, importlib.util, io, json, os, socket, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend' / 'scripts')]
os.environ['ALLOW_LIVE_AI'] = '0'
def _offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = _offline; socket.create_connection = _offline

from app.ai.function_route import run_fact_route  # noqa: E402
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402
from app.simulation.geometry_functions import planner  # noqa: E402
from app.simulation.geometry_functions.registry import TuChoi  # noqa: E402

POLICY = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f'{name}.py')
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(m)
    return m


def cases():
    src = (HERE / 'r1_described_point_probe.py').read_text(encoding='utf-8')
    ns = {'__file__': str(HERE / 'r1_described_point_probe.py'), '__name__': 'r1_defs'}
    exec(compile(src[:src.index('rows = [run(r) for r in ROWS]')], 'r1_described_point_probe.py', 'exec'), ns)
    for r in ns['ROWS']:
        if r['want'] is not None and r['id'] not in ('D1', 'D2'):
            yield 'C13/4', r['id'], ('d4', r['text'], r['payload'])
    for c in json.loads((HERE.parent / 'r1-live-pilot-corpus.json').read_text(encoding='utf-8'))['cases']:
        if c['expected']['outcome'] == 'SERVED':
            yield 'R1/4', c['id'], ('d4', c['problem_text'], c['gold_extraction'])
    for c in _load('planner_recomposition_probe')._build_cases():
        yield 'C11/B', c['id'], ('b', c['text'], c['facts'])


def run(kind, text, data):
    if kind == 'd4':
        route = run_hybrid_offline(text, ReplayExtractor({text: data}), policy=POLICY).response['route_d']
        ans = {k: v.get('coef') for k, v in (route.get('answer_exact') or {}).items()} if route['status'] == 'SERVED' else None
        return route['status'], ans
    r = run_fact_route(text, {'facts': data})
    return r.status, (sorted(map(str, (r.answers or {}).values())) if r.status == 'SERVED' and hasattr(r, 'answers') else
                      r.status)


@contextlib.contextmanager
def arm(name):
    saved = {k: getattr(planner, k) for k in ('_mat_qua_diem', '_mat_vuong_duong', '_dinh_cat_canh', 'planning_contracts',
                                               'MAX_EFFECT_DEPTH', 'MAX_EFFECT_NEEDS', 'MAX_EFFECT_CANDIDATES')}
    if name == 'C':
        def off(*a, **k):
            raise TuChoi('UNSUPPORTED_CAPABILITY', 'ablation C: declared decompositions off')
        planner._mat_qua_diem = planner._mat_vuong_duong = planner._dinh_cat_canh = off
        planner.planning_contracts = lambda s: tuple(c for c in saved['planning_contracts'](s)
                                                     if c.source_policy not in planner._RULE_POLICIES)
    if name == 'D':
        planner.MAX_EFFECT_DEPTH, planner.MAX_EFFECT_NEEDS, planner.MAX_EFFECT_CANDIDATES = 1, 4, 2
    try:
        yield
    finally:
        for k, v in saved.items():
            setattr(planner, k, v)


rows = []
for group, cid, (kind, text, data) in cases():
    base = run(kind, text, data)
    row = {'set': group, 'id': cid, 'B': base[0]}
    for name in ('C', 'D'):
        with arm(name):
            got = run(kind, text, data)
        row[name] = 'SURVIVES' if got == base and base[0] == 'SERVED' else got[0] if base[0] == 'SERVED' else 'n/a'
    rows.append(row)
    print(f"{group:6s} {cid[:48]:48s} B={row['B']:8s} C={row['C']:9s} D={row['D']}")
served = [r for r in rows if r['B'] == 'SERVED']
summary = {'served_in_B': len(served),
           'C_declared_rules_off': dict(collections.Counter(r['C'] for r in served)),
           'D_low_budget': dict(collections.Counter(r['D'] for r in served))}
print(json.dumps(summary, ensure_ascii=False))
if len(sys.argv) > 1:
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'provider_calls': 0,
                   'production_defaults_changed': False, 'summary': summary, 'rows': rows}, f, ensure_ascii=False, indent=1)
        f.write('\n')
