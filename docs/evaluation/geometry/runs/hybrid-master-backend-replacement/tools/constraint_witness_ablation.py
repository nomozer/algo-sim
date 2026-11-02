"""Seventeenth continuation: which part of the planner does each served constrained plane depend on? Ablation in THIS
process only (monkeypatch); production defaults untouched. Cases: every oracle-UNIQUE case of
`constraint_witness_probe.py` (same generator, same oracle).
  C  the `Normal` contract hidden (`planning_contracts` filtered): a normal can only come from a stated premise line;
  D  the normal search capped to ONE candidate (`MAX_NORMAL_CANDIDATES = 1`): any choice ⇒ search exhausted.
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
    saved = (planner.planning_contracts, planner.MAX_NORMAL_CANDIDATES)
    if name == 'C':
        planner.planning_contracts = lambda s: tuple(c for c in saved[0](s) if c.effect.kind != 'Normal')
    if name == 'D':
        planner.MAX_NORMAL_CANDIDATES = 1
    try:
        yield
    finally:
        planner.planning_contracts, planner.MAX_NORMAL_CANDIDATES = saved


def run(c):
    out = run_hybrid_offline(c['text'], ReplayExtractor({c['text']: c['payload']}), policy=POLICY).response
    r = out['route_d']
    return r['status'], out['envelope'].get('reason_code'), (P.composition(r, c['text'], c['witness_needed'])
                                                              if r['status'] == 'SERVED' else None)


rows = []
for c in P.cases():
    if c['oracle'] != 'UNIQUE':
        continue
    b = run(c)
    row = {'topology': c['topology'], 'family': c['family'], 'contains': c['contains'], 'ref': c['ref'],
           'B': b[0], 'composition': b[2]}
    for name in ('C', 'D'):
        with arm(name):
            s, code, _ = run(c)
        row[name] = 'SURVIVES' if s == 'SERVED' else code
    rows.append(row)
summary = {arm_: {comp: dict(collections.Counter(r[arm_] for r in rows if r['composition'] == comp))
                  for comp in sorted({str(r['composition']) for r in rows})} for arm_ in ('C', 'D')}
summary['served_in_B'] = sum(r['B'] == 'SERVED' for r in rows)
print(json.dumps(summary, ensure_ascii=False, indent=1))
if len(sys.argv) > 1:
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'provider_calls': 0,
                   'production_defaults_changed': False, 'summary': summary, 'rows': rows}, f, ensure_ascii=False, indent=1)
        f.write('\n')
