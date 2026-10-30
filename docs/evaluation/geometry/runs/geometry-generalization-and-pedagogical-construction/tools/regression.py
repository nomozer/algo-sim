"""W4 regression gates via the locked W3-F2 evaluators: Wave 3 post-feedback replay (vs the F7 receipt), locked 96
development cases, and the 203 locked reviewer probes. Offline, 0 provider calls. Usage: regression.py <out-suffix>"""
import hashlib, importlib.util, json, os, socket, subprocess, sys
from pathlib import Path
from types import SimpleNamespace

W = Path(__file__).resolve().parents[1]; ROOT = W.parents[4]
RUN = ROOT / 'docs/evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding'
F7 = RUN / 'closed-input-contract/cic-d1-contract-recovery/target-grammar-identity-recovery/f7-narrow-recovery'
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/tests/geometry'), str(F7.parent / 'tools')]
sys.dont_write_bytecode = True
os.environ['ALLOW_LIVE_AI'] = '0'
def offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = offline; socket.create_connection = offline
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def module(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m

suffix = sys.argv[1]
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--', 'backend/app'], cwd=ROOT, text=True).strip())
ident = {'head': head, 'product_uncommitted': dirty, 'live_provider_calls': 0}

dev = module('w4_locked_development', RUN / 'tools/evaluate_development.py')
f1 = module('w4_wave3_replay', dev.F1 / 'tools/build_and_evaluate_w3_f1.py')
f1.WAVE3_WORKTREE = dev.HIST
w3 = f1.evaluate_wave3_post_feedback_regression()
old = {r['id']: r for r in load(F7 / 'wave3-post-feedback-regression.json')['cases']}
trans = [{'id': r['id'], 'before': [old[r['id']]['outcome'], old[r['id']]['code']], 'after': [r['outcome'], r['code']]}
         for r in w3['cases'] if (r['outcome'], r['code']) != (old[r['id']]['outcome'], old[r['id']]['code'])]
w3['identity'] = ident; w3['baseline'] = str((F7 / 'wave3-post-feedback-regression.json').relative_to(ROOT)); w3['transitions_from_baseline'] = trans

oracle = load(RUN / 'inputs/oracle.json')['cases']
rows = [dev.evaluate_case(c, oracle.get(c['id'])) for c in load(RUN / 'inputs/development.json')['cases']]
gc = {**ident, 'match': sum(r['matches_expected'] for r in rows), 'total': len(rows),
      'wrong_served': sum(r['outcome'] == 'WRONG_SERVED' for r in rows), 'mismatches': [r['id'] for r in rows if not r['matches_expected']]}

from observe import observe
import test_scope_census_closure as F
fixtures = SimpleNamespace(SUP=F.SUP, A3DEV=F.A3DEV, SIM=F.SIM, DEV=load(RUN / 'inputs/development.json'))
prows = []
for i in range(1, 6):
    mod = module(f'w4_probes_{i}', RUN / f'unified-solid-scope-closure/pre-freeze-review/probes{i}.py')
    for name, expected, build, _base in mod.probes(fixtures):
        prows.append({'probe': name, 'expected_class': expected, 'got': observe(build())})
pold = {c['probe']: c for c in load(F7 / 'probes203.json')['cases']}
ptrans = [r['probe'] for r in prows if {n: (r['got'][n]['status'], r['got'][n]['code']) for n in ('a3', 'pl', 'a4')}
          != {n: (pold[r['probe']]['got'][n]['status'], pold[r['probe']]['got'][n]['code']) for n in ('a3', 'pl', 'a4')}]
pr = {**ident, 'total': len(prows),
      'served_negatives': [r['probe'] for r in prows if r['expected_class'] == 'NEG' and any(r['got'][n]['status'] == 'SERVED' for n in ('a3', 'pl', 'a4'))],
      'internal': [(r['probe'], n) for r in prows for n in ('a3', 'pl', 'a4') if r['got'][n]['status'] == 'EXCEPTION'
                   or r['got'][n]['code'] in ('ADAPTER_INTERNAL_ERROR', 'ROUTE_INTERNAL_ERROR')],
      'transitions_from_f7': ptrans}

out = {'wave3_summary': w3['post_feedback_regression_summary'], 'wave3_transitions': trans, 'locked96': gc, 'probes203': pr}
for name, data in ((f'wave3-{suffix}.json', w3), (f'regression-{suffix}.json', out)):
    with (W / name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=1); f.write('\n')
s = w3['post_feedback_regression_summary']
print(json.dumps({'wave3': {k: s[k] for k in ('positive_served_correct', 'positive_false_refusal', 'negative_refused', 'negative_correct_reason', 'overall_wrong_served')},
                  'wave3_transitions': trans, 'locked96': [gc['match'], gc['total'], gc['wrong_served'], gc['mismatches']],
                  'probes': [pr['total'], len(pr['served_negatives']), len(pr['internal']), pr['transitions_from_f7']]}, ensure_ascii=False, indent=1))
