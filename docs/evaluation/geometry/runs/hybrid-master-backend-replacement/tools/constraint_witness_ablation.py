"""Seventeenth continuation: which part of the planner does each served constrained plane depend on? Ablation in THIS
process only (monkeypatch); production defaults untouched. Cases: every oracle-UNIQUE case of
`constraint_witness_probe.py` (same generator, same oracle).
  C      the `Normal` contract hidden (`planning_contracts` filtered): a normal can only come from a stated premise line;
  LAST   the normal subgoal takes its LAST candidate instead of the cheapest (review MAJOR-2: does the choice matter?);
  NOPREM premise normals ignored: the normal is always constructed.
(The C17 arm D — one candidate allowed — only showed that ≥ 2 candidates exist; it is withdrawn, review MAJOR-2.)
Baseline A (planner /24, candidate 3154a696) is run separately on its own detached worktree: `constraint-witness-baseline-24.json`.
IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC, offline, 0 provider calls. Usage: constraint_witness_ablation.py [out.json]
"""
import collections, contextlib, importlib.util, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('cw_probe', HERE / 'constraint_witness_probe.py')
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402
from app.simulation.geometry_functions import planner  # noqa: E402

POLICY = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})


@contextlib.contextmanager
def arm(name):
    saved = (planner.planning_contracts, planner._phap_tuyen)
    if name == 'C':
        planner.planning_contracts = lambda s: tuple(c for c in saved[0](s) if c.effect.kind != 'Normal')
    if name in ('LAST', 'NOPREM'):
        pick = ((lambda it, key=None: sorted(list(it), key=key)[-1]) if name == 'LAST' else
                (lambda it, key=None: min([u for u in it if u.get('producer') != 'premise'] or list(it), key=key)))

        def chon(q, kh, k):                            # the selection inside `_phap_tuyen` only (its `min`)
            planner.min = pick
            try:
                return saved[1](q, kh, k)
            finally:
                del planner.min
        planner._phap_tuyen = chon
    try:
        yield
    finally:
        planner.planning_contracts, planner._phap_tuyen = saved


def run(c):
    out = run_hybrid_offline(c['text'], ReplayExtractor({c['text']: c['payload']}), policy=POLICY).response
    r = out['route_d']
    ans = {k: v.get('coef') for k, v in (r.get('answer_exact') or {}).items()}
    return r['status'], out['envelope'].get('reason_code'), (P.composition(r, c['text'], c['witness_needed'])
                                                              if r['status'] == 'SERVED' else None), ans


rows = []
for c in P.cases():
    if c['oracle'] != 'UNIQUE':
        continue
    b = run(c)
    row = {'topology': c['topology'], 'family': c['family'], 'contains': c['contains'], 'ref': c['ref'],
           'B': b[0], 'composition': b[2]}
    for name in ('C', 'LAST', 'NOPREM'):
        with arm(name):
            s, code, _, ans = run(c)
        row[name] = ('SURVIVES' if s == 'SERVED' and ans == b[3] else 'CHANGED_ANSWER' if s == 'SERVED' else code)
    rows.append(row)
summary = {arm_: {comp: dict(collections.Counter(r[arm_] for r in rows if r['composition'] == comp))
                  for comp in sorted({str(r['composition']) for r in rows})} for arm_ in ('C', 'LAST', 'NOPREM')}
summary['served_in_B'] = sum(r['B'] == 'SERVED' for r in rows)
print(json.dumps(summary, ensure_ascii=False, indent=1))
if len(sys.argv) > 1:
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'provider_calls': 0,
                   'production_defaults_changed': False, 'summary': summary, 'rows': rows}, f, ensure_ascii=False, indent=1)
        f.write('\n')
