"""Append-only gates and post-feedback replay after the solid-scope repair (Claude takeover); reuses the locked
evaluators of `verify_after_adapter3.py`, writes only new file names, never overwrites an earlier receipt."""
import argparse, copy, hashlib, importlib.util, json, os, re, socket, subprocess, sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]; ROOT = RUN.parents[4]
sys.path.insert(0, str(ROOT / 'backend')); sys.dont_write_bytecode = True
os.environ['ALLOW_LIVE_AI'] = '0'
def offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = offline; socket.create_connection = offline
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def digest(p): return hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
def write(name, data):
    with (RUN / name).open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
def module(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
def copy_log(src, dst):
    text = (ROOT / src).read_text(encoding='utf-8-sig'); assert 'Traceback' not in text
    with (RUN / dst).open('x', encoding='utf-8', newline='\n') as f: f.write(text)
    return digest(RUN / dst)

parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['gates', 'replay'])
parser.add_argument('--tag', default='', help="output suffix ('' = first round on 393864d1, e.g. '-final')")
args = parser.parse_args(); T = args.tag
dev = module('solid_scope_locked_development', RUN / 'tools/evaluate_development.py')
fz = module('solid_scope_freeze_identity', ROOT / 'backend/scripts/freeze_evaluation_candidate.py')
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
identity = {'head': head, 'product_commit': fz.product_commit(), 'measured_system_hash': fz.measured_system_hash(),
            'live_provider_calls': 0, 'classification': 'POST_FEEDBACK_DEVELOPMENT_REGRESSION'}

if args.phase == 'gates':
    from app.ai.adapter3_simulation import run_typed_fact_next_route
    from app.ai.adapter4_route import run_typed_fact_next_v2_route
    from app.simulation.geometry_functions.typed_fact_next_bridge import bridge
    doc = load(RUN / 'inputs/development.json'); oracle = load(RUN / 'inputs/oracle.json')['cases']
    rows = [dev.evaluate_case(c, oracle.get(c['id'])) for c in doc['cases']]
    assert len(rows) == 96 and all(r['matches_expected'] for r in rows)
    slices = {s: {'total': len(cs := [r for r in rows if r['slice'] == s]),
                  'served_correct': sum(r['outcome'] == 'SERVED_CORRECT' for r in cs),
                  'refused': sum(not r['served'] for r in cs),
                  'locked_code_match': sum(r['matches_expected'] for r in cs)} for s in sorted({r['slice'] for r in rows})}
    # Takeover H1–H3 boundary matrix (codex-to-claude-takeover.md §3), replayed on the product commit.
    sup = load(RUN / 'inputs/recovery-supplementary.json')['control']
    a3 = next(c for c in load(RUN.parent / 'typedfact-next-adapter3-simulation/corpus-dev.json')['cases'] if c['case_id'] == 'A3-DEV-02')
    def mutate(base, prem=None, goal_index=0, **goal):
        p = copy.deepcopy(base)
        if prem: p['premises'].append(prem); p['problem_text'] += ' ' + prem['quote']
        p['math_goals'][goal_index].update(goal); return p
    height = {'kind': 'height', 'solid_id': 'pyr1', 'args': {'solid': 'pyr2', 'value': 'a'}, 'quote': 'Chiều cao hình chóp D.ABC bằng a.'}
    matrix = [('H1', mutate(a3['payload'], height), False, 'SOURCE_OBJECT_MISMATCH'),
              ('H2a', mutate(sup, solid_id='s2'), True, 'SOURCE_OBJECT_MISMATCH'),
              ('H2b', mutate(sup, solid_id='foreign'), True, 'UNKNOWN_SOLID_ID'),
              ('H2c', mutate(a3['payload'], goal_index=1, solid_id='pyr2'), False, 'SOURCE_OBJECT_MISMATCH'),
              ('H2d', mutate(a3['payload'], goal_index=1, solid_id='foreign'), False, 'UNKNOWN_SOLID_ID'),
              ('H3', mutate(sup, target={'solid': 'T.ABCD'}), True, 'SOURCE_OBJECT_MISMATCH'),
              ('A3-DEV-02 control', copy.deepcopy(a3['payload']), False, None),
              ('supplementary control', copy.deepcopy(sup), True, None)]
    boundary = []
    for name, p, v4, code in matrix:
        try: bridge(copy.deepcopy(p)); b = 'OK'
        except Exception as e: b = getattr(e, 'code', type(e).__name__)
        r3 = run_typed_fact_next_route(copy.deepcopy(p))
        row = {'case': name, 'expected': code or 'SERVED', 'bridge': b, 'adapter3': [r3.status, r3.code]}
        ok = (r3.status, r3.code) == (('REFUSED', code) if code else ('SERVED', None))
        if v4:
            r4 = run_typed_fact_next_v2_route({**copy.deepcopy(p), 'schema_version': 'typed-fact-next/2'})
            row['adapter4'] = [r4.status, r4.code]; ok &= (r4.status, r4.code) == (r3.status, r3.code)
        if name == 'A3-DEV-02 control': ok &= r3.answer_exact == a3['oracle_exact']
        row['pass'] = ok; boundary.append(row)
    assert all(r['pass'] for r in boundary), boundary
    fixtures = load(ROOT / f'.superpowers/f2/claude-41-fixtures{T}.json')
    assert fixtures['verified'] == 41 and fixtures['problems'] == []
    write(f'verification/solid-scope{T}-41-fixtures.json', fixtures)
    logs = {dst: copy_log(src, dst) for src, dst in (
        (f'.superpowers/f2/claude-solid-scope-compat{T}.log', f'verification/solid-scope{T}-compat-tests.log'),
        (f'.superpowers/f2/claude-solid-scope-{"green" + T if T else "green2"}.log', f'verification/solid-scope{T}-green-tests.log'),
        (f'.superpowers/f2/claude-cache{T}.log', f'verification/solid-scope{T}-cache.log'))}
    def summary(name):
        text = (RUN / f'verification/solid-scope{T}-{name}-tests.log').read_text(encoding='utf-8')
        m = re.search(r'^(\d+) passed(?:, 1 deselected, 6 xfailed)?', text, re.M); assert m and ' failed' not in m.group(0)
        assert not re.search(r'^\d+ failed|^FAILED ', text, re.M); return int(m.group(1))
    passed, green = summary('compat'), summary('green')
    write(f'solid-scope{T}-safety-gates.json', {
        **identity, 'corrects': 'final-safety-gates.json (Gate A recorded PASS before the final-review MAJOR)',
        'A': 'PASS', 'B': 'PASS_UNAFFECTED', 'C': 'PASS', 'D': 'PASS',
        'B_note': 'No incidence/engine/Registry change since the independently adjudicated f7dd5580; witness tests rerun in the compat suite.',
        'boundary_matrix': boundary, 'slices': slices,
        'wrong_served_locked_96': sum(r['outcome'] == 'WRONG_SERVED' for r in rows),
        'tests': {'passed': passed, 'failed': 0, 'xfailed': 6, 'deselected': 1, 'safety_file_passed': green,
                  'deferred': 'version/freeze receipt check needs the new freeze; runs in Full T3'},
        'mutants_killed': ['remove_terminal_guard', 'remove_scope_guard', 'replace_scope_with_default', 'allow_global_lookup',
                           'bridge_remove_operand_conflict', 'bridge_remove_unknown_scope',
                           'adapter3_remove_operand_conflict', 'adapter3_remove_unknown_scope'],
        'fixtures_verified': 41, 'cache_decision': 'NO_BUMP 130: cache identity lock MATCH; cached LLM_ONLY path untouched.',
        'versions': 'unchanged (Registry /21, Planner /18, Adapter /3, Bridge /1 and /2): restored invalid-input refusal, no new schema or capability',
        'logs_sha256_lf': logs, 'test_source_sha256_lf': digest(ROOT / 'backend/tests/geometry/test_adapter3_fallback_safety.py'),
        'release_status': 'NOT_YET_READY_PENDING_REPLAY_T0_T2_FREEZE_T3_FINAL_REVIEW'})
    print(json.dumps({'gates': 'A-D PASS', 'boundary': [(r['case'], r['pass']) for r in boundary], 'slices': slices}, ensure_ascii=False))
else:
    gates = load(RUN / f'solid-scope{T}-safety-gates.json'); assert gates['A'] == 'PASS'
    assert gates['measured_system_hash'] == list(fz.measured_system_hash())
    f1 = module('solid_scope_wave3_replay', dev.F1 / 'tools/build_and_evaluate_w3_f1.py')
    f1.WAVE3_WORKTREE = dev.HIST    # same correction as verify_after_adapter3.py: committed evidence in this checkout
    result = f1.evaluate_wave3_post_feedback_regression()
    result['task'] = 'HYBRID_V2_W3_F2_ADAPTER3_SEMANTIC_FALLBACK_SAFETY_HARDENING (Claude takeover, solid scope)'
    result['identity'] = identity
    for key, path in (('W3_F1', dev.F1 / 'results/wave3-post-feedback-regression.json'),
                      ('after_adapter3', RUN / 'wave3-post-feedback-regression-after-adapter3.json')):
        old = {r['id']: r for r in load(path)['cases']}
        result[f'transitions_from_{key}'] = [
            {'id': r['id'], 'before_outcome': old[r['id']]['outcome'], 'before_code': old[r['id']]['code'],
             'after_outcome': r['outcome'], 'after_code': r['code']} for r in result['cases']
            if (r['outcome'], r['code']) != (old[r['id']]['outcome'], old[r['id']]['code'])]
    result['original_A06'] = {'classification': 'F2_LANGUAGE_GROUNDING_RESOLVED_BUT_DOWNSTREAM_RADICAL_LIMIT_REMAINS',
                              'actual': next(r for r in result['cases'] if r['id'] == 'W3-A06')}
    write(f'wave3-post-feedback-regression-after-solid-scope{T}.json', result)
    print(json.dumps({'summary': result['post_feedback_regression_summary'],
                      'transitions_from_after_adapter3': result['transitions_from_after_adapter3']}, ensure_ascii=False))
