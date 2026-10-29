"""Append-only Gates B–D and Wave 3 replay for the adjudicated closed input contract.
Usage (worktree root): python -B gates_v2.py gates|replay. Reuses this run's locked evaluators; never overwrites."""
import hashlib, importlib.util, json, os, re, socket, subprocess, sys
from pathlib import Path

U = Path(__file__).resolve().parents[1]; CIC = U.parent; RUN = CIC.parent; ROOT = RUN.parents[4]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/tests/geometry')]; sys.dont_write_bytecode = True
os.environ['ALLOW_LIVE_AI'] = '0'
def offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = offline; socket.create_connection = offline
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def digest(p): return hashlib.sha256(Path(p).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
def write(name, data):
    with (U / name).open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
def copy_log(src, dst):
    text = (ROOT / src).read_text(encoding='utf-8-sig')
    with (U / dst).open('x', encoding='utf-8', newline='\n') as f: f.write(text)
    return digest(U / dst)
def module(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m

phase = sys.argv[1]; assert phase in ('gates', 'replay')
dev = module('cic_locked_development', RUN / 'tools/evaluate_development.py')
fz = module('cic_freeze_identity', ROOT / 'backend/scripts/freeze_evaluation_candidate.py')
git = lambda *a: subprocess.check_output(['git', *a], cwd=ROOT, text=True).strip()
identity = {'head': git('rev-parse', 'HEAD'), 'product_commit': fz.product_commit(),
            'measured_system_hash': fz.measured_system_hash(), 'live_provider_calls': 0,
            'classification': 'DEVELOPMENT_SECURITY_REGRESSION'}
L = '.superpowers/f2'

if phase == 'gates':
    assert load(U / 'gate-a-v2.json')['closed_input_contract_acceptance']['status'] == 'PASS'
    assert not git('status', '--porcelain', '--', 'backend/app', 'frontend/src')
    changed = git('diff', '--name-only', '5e44d5da', 'HEAD', '--', 'backend/app', 'frontend/src').splitlines()
    assert sorted(changed) == ['backend/app/ai/adapter3_simulation.py',
                               'backend/app/simulation/geometry_functions/typed_fact_next.py',
                               'backend/app/simulation/geometry_functions/typed_fact_next_bridge.py'], changed
    rows = [dev.evaluate_case(c, load(RUN / 'inputs/oracle.json')['cases'].get(c['id'])) for c in load(RUN / 'inputs/development.json')['cases']]
    assert len(rows) == 96 and all(r['matches_expected'] for r in rows)
    slices = {s: {'total': len(cs := [r for r in rows if r['slice'] == s]),
                  'served_correct': sum(r['outcome'] == 'SERVED_CORRECT' for r in cs),
                  'refused': sum(not r['served'] for r in cs),
                  'locked_code_match': sum(r['matches_expected'] for r in cs)} for s in sorted({r['slice'] for r in rows})}
    logs = {dst: copy_log(f'{L}/{src}', dst) for src, dst in (('cic-compat-full.log', 'compatibility-full-pytest.log'),
            ('cic-cache.log', 'cache.log'), ('cic-publication.log', 'publication.log'))}
    compat = (U / 'compatibility-full-pytest.log').read_text(encoding='utf-8')
    summary = [l for l in compat.splitlines() if re.match(r'^\d+ (passed|failed)', l)][-1]
    failed = re.findall(r'^FAILED (\S+)', compat, re.M)
    stale_freeze = load(U / 'compatibility-adjudication.json')['stale_freeze_identity_nodes']
    assert set(failed) == set(stale_freeze), sorted(set(failed) ^ set(stale_freeze))
    assert 'Khoá khớp · CACHE_VERSION 130' in (U / 'cache.log').read_text(encoding='utf-8')
    assert 'verdict=PASS' in (U / 'publication.log').read_text(encoding='utf-8')
    fixtures = load(ROOT / f'{L}/cic-41-fixtures.json'); assert fixtures['verified'] == 41 and not fixtures['problems']
    write('verification-41-fixtures.json', fixtures)
    write('compatibility.json', {**identity, 'status': 'PASS', 'suite': 'entire backend pytest (default markers)',
        'summary': summary, 'failed_only_stale_freeze_identity': failed,
        'stale_freeze_reason': 'product changed after the last freeze; these pass only after the new freeze (T0/T3)',
        'fixtures_verified': 41, 'cache': 'NO_BUMP 130, identity lock MATCH', 'publication': 'PASS', 'logs_sha256_lf': logs})
    write('gates-v2.json', {**identity, 'manifest': 'acceptance-manifest.json v2',
        'A': 'PASS', 'B': 'PASS', 'C': 'PASS', 'D': 'PASS',
        'A_detail': 'gate-a-v2.json (Closed Input Contract acceptance PASS; source-grammar diagnostics PENDING, reported separately)',
        'B_detail': {'product_files_changed_since_5e44d5da': changed,
                     'unchanged': 'kernel, engine, Registry /21, Planner /18, radical, renderer, UI'},
        'C_detail': {'slices': slices, 'wrong_served_locked_96': sum(r['outcome'] == 'WRONG_SERVED' for r in rows)},
        'D_detail': 'compatibility.json', 'release_status': 'PENDING_PRE_FREEZE_ADVERSARIAL_REVIEW'})
    print(json.dumps({'gates': 'A-D PASS', 'slices': slices, 'compat': summary}, ensure_ascii=False))
else:
    gates = load(U / 'gates-v2.json'); assert all(gates[k] == 'PASS' for k in 'ABCD')
    assert gates['measured_system_hash'] == list(fz.measured_system_hash())
    assert load(U / 'pre-freeze-review-verdict.json')['verdict'] == 'PRE_FREEZE_ADVERSARIAL_REVIEW_PASS'
    f1 = module('cic_wave3_replay', dev.F1 / 'tools/build_and_evaluate_w3_f1.py')
    f1.WAVE3_WORKTREE = dev.HIST
    result = f1.evaluate_wave3_post_feedback_regression()
    result['task'] = 'HYBRID_V2_W3_F2_CLOSED_INPUT_CONTRACT_AND_LEGACY_OWNERSHIP_SAFETY'; result['identity'] = identity
    base = 'unified-solid-scope/wave3-post-feedback-regression.json'          # last replay of this run
    old = {r['id']: r for r in load(RUN / base)['cases']}
    result['baseline'] = f'../../{base}'
    result['transitions_from_baseline'] = [
        {'id': r['id'], 'before_outcome': old[r['id']]['outcome'], 'before_code': old[r['id']]['code'],
         'after_outcome': r['outcome'], 'after_code': r['code']} for r in result['cases']
        if (r['outcome'], r['code']) != (old[r['id']]['outcome'], old[r['id']]['code'])]
    write('wave3-post-feedback-regression.json', result)
    print(json.dumps({'summary': result['post_feedback_regression_summary'], 'transitions': result['transitions_from_baseline']}, ensure_ascii=False))
