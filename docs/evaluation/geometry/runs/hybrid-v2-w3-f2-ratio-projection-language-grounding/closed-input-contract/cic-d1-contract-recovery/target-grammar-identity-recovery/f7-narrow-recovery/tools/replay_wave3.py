"""Wave 3 POST_FEEDBACK_DEVELOPMENT_REGRESSION replay after F7, via the locked W3-F1 evaluator (same path correction
as unified-solid-scope/tools/gates_and_replay.py). Compares with the latest branch replay. 0 provider calls; writes once."""
import hashlib, importlib.util, json, os, socket, subprocess, sys
from pathlib import Path

U = Path(__file__).resolve().parents[1]; RUN = U.parents[3]; ROOT = RUN.parents[4]
sys.path.insert(0, str(ROOT / 'backend')); sys.dont_write_bytecode = True
os.environ['ALLOW_LIVE_AI'] = '0'
def offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = offline; socket.create_connection = offline
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def module(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m

dev = module('f7_locked_development', RUN / 'tools/evaluate_development.py')
fz = module('f7_freeze_identity', ROOT / 'backend/scripts/freeze_evaluation_candidate.py')
f1 = module('f7_wave3_replay', dev.F1 / 'tools/build_and_evaluate_w3_f1.py')
f1.WAVE3_WORKTREE = dev.HIST
result = f1.evaluate_wave3_post_feedback_regression()
result['task'] = 'HYBRID_V2_W3_F2_F7_NARROW_RECOVERY (technical continuation, publication blocked)'
result['identity'] = {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                      'product_commit': fz.product_commit(), 'measured_system_hash': fz.measured_system_hash(),
                      'live_provider_calls': 0, 'classification': 'POST_FEEDBACK_DEVELOPMENT_REGRESSION'}
base = RUN / 'unified-solid-scope/wave3-post-feedback-regression.json'
old = {r['id']: r for r in load(base)['cases']}
result['baseline'] = str(base.relative_to(RUN))
result['transitions_from_baseline'] = [
    {'id': r['id'], 'before_outcome': old[r['id']]['outcome'], 'before_code': old[r['id']]['code'],
     'after_outcome': r['outcome'], 'after_code': r['code']} for r in result['cases']
    if (r['outcome'], r['code']) != (old[r['id']]['outcome'], old[r['id']]['code'])]
with (U / 'wave3-post-feedback-regression.json').open('x', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
s = result['post_feedback_regression_summary']
print(json.dumps({k: s[k] for k in ('positive_served_correct', 'positive_false_refusal', 'negative_refused',
                                    'negative_correct_reason', 'overall_wrong_served')},
                 ensure_ascii=False), 'transitions:', result['transitions_from_baseline'])
