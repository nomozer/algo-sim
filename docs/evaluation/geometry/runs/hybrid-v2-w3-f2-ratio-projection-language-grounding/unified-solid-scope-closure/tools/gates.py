"""Append-only Gates A–D for the scope census closure (and the Wave 3 replay: `gates.py replay`).
Reuses this run's locked evaluators; writes only new file names."""
import hashlib, importlib.util, json, os, re, socket, subprocess, sys
from pathlib import Path

U = Path(__file__).resolve().parents[1]; RUN = U.parent; ROOT = RUN.parents[4]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/tests/geometry')]; sys.dont_write_bytecode = True
os.environ['ALLOW_LIVE_AI'] = '0'
def offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = offline; socket.create_connection = offline
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def digest(p): return hashlib.sha256(Path(p).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
def write(name, data):
    with (U / name).open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
def copy_log(src, dst):
    text = (ROOT / src).read_text(encoding='utf-8-sig'); assert 'Traceback' not in text
    with (U / dst).open('x', encoding='utf-8', newline='\n') as f: f.write(text)
    return digest(U / dst)
def module(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m

phase = sys.argv[1]; assert phase in ('gates', 'replay')
dev = module('closure_locked_development', RUN / 'tools/evaluate_development.py')
fz = module('closure_freeze_identity', ROOT / 'backend/scripts/freeze_evaluation_candidate.py')
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
identity = {'head': head, 'product_commit': fz.product_commit(), 'measured_system_hash': fz.measured_system_hash(),
            'live_provider_calls': 0, 'classification': 'POST_FEEDBACK_DEVELOPMENT_REGRESSION'}
L = '.superpowers/f2'

if phase == 'gates':
    rows = [dev.evaluate_case(c, load(RUN / 'inputs/oracle.json')['cases'].get(c['id'])) for c in load(RUN / 'inputs/development.json')['cases']]
    assert len(rows) == 96 and all(r['matches_expected'] for r in rows)
    slices = {s: {'total': len(cs := [r for r in rows if r['slice'] == s]),
                  'served_correct': sum(r['outcome'] == 'SERVED_CORRECT' for r in cs),
                  'refused': sum(not r['served'] for r in cs),
                  'locked_code_match': sum(r['matches_expected'] for r in cs)} for s in sorted({r['slice'] for r in rows})}
    green = load(U / 'green.json'); assert not green['failed'] and not green['product_dirty']
    compat_hash = copy_log(f'{L}/closure-compat-final2.log', 'compatibility-tests.log')
    compat = (U / 'compatibility-tests.log').read_text(encoding='utf-8')
    m = re.search(r'^(\d+) passed, 6 skipped, 1 deselected, 6 xfailed', compat, re.M)
    assert m and not re.search(r'\b\d+ failed|^FAILED ', compat, re.M)
    fixtures = load(ROOT / f'{L}/closure-41-fixtures-final.json'); assert fixtures['verified'] == 41 and not fixtures['problems']
    write('verification-41-fixtures.json', fixtures)
    logs = {'compatibility-tests.log': compat_hash, 'cache.log': copy_log(f'{L}/closure-cache-final.log', 'cache.log'),
            'publication.log': copy_log(f'{L}/closure-publication-final.log', 'publication.log')}
    assert 'Khoá khớp · CACHE_VERSION 130' in (U / 'cache.log').read_text(encoding='utf-8')
    assert 'verdict=PASS' in (U / 'publication.log').read_text(encoding='utf-8')
    # Previous reviewer's 117 committed probes re-run on this product (independent adversarial matrix).
    probes = [json.loads(l) for l in (ROOT / f'{L}/closure-review1-probes-final.out').read_text(encoding='utf-8').splitlines()]
    with (U / 'closure-review1-probes-final.out').open('x', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(json.dumps(p, ensure_ascii=False) for p in probes) + '\n')
    adjudicated_valid = {'C1.premise_unscoped_cross_namespace', 'SEC1.ratio_den_other_solid'}   # preregistration-amendment-1
    neg_served = [p['probe'] for p in probes if p['kind'] == 'NEG' and p['probe'] not in adjudicated_valid
                  and any(p[k] == 'SERVED' for k in ('A3', 'PL', 'A4'))]
    internal = [p['probe'] for p in probes if any('EXC' in p[k] or 'INTERNAL' in p[k] for k in ('A3', 'PL', 'A4'))]
    assert not neg_served and not internal, (neg_served, internal)
    inv = load(U / 'schema-field-inventory-v2.json')
    coverage = {path: {**{k: row.get(k) for k in ('category', 'owner', 'rules', 'refusal_codes', 'positive_test', 'negative_test')},
                       'entry_points': row.get('entry_points'), 'status': 'PASS'}
                for path, row in inv['fields'].items() if row['category'] in inv['scope_categories']}
    write('scope-entrypoint-coverage.json', {**identity, 'inventory': 'schema-field-inventory-v2.json',
        'enforced_by': 'backend/tests/geometry/test_scope_census_closure.py::test_census_inventory_complete',
        'entry_points': '../unified-solid-scope/solid-scope-entrypoint-matrix.json (E0 schema policy runs before every route; '
                        'E1a curved route additionally runs the Bridge ownership validator; Bridge S8 on E1b/E2/E3)',
        'kinds': inv['kinds'], 'scope_bearing_fields': len(coverage), 'fields': coverage})
    write('mutation-results.json', {**identity, 'status': 'PASS', 'source': 'green.log + compatibility-tests.log',
        'closure_mutants': ['naive_hyphen_split', 'remove_qualified_scope_guard', 'remove_relation_side_scope',
                            'remove_sim_goal_target_scope', 'remove_parent_validation', 'remove_highlight_token_validation',
                            'remove_apex_ownership', 'remove_owner_decision_d_a', 'remove_residual_ancestry'],
        'retained_mutants': {'unified (9)': 'test_unified_solid_scope.py::test_oracles_kill_unified_scope_mutants incl. '
                             'bypass_curved_prevalidation and foreign_scope_to_first_solid',
                             'fallback (4+4)': 'test_adapter3_fallback_safety.py incl. remove_terminal_guard, replace_scope_with_default',
                             'premise scope (4)': 'test_premise_scope_recovery.py'},
        'metamorphic': ['test_metamorphic_hyphen_rename_preserves_answers (5 controls × 3 routes)',
                        'test_metamorphic_foreign_scope_never_served (5 controls, every scope slot)'],
        'oracle_adaptations': 'test-adaptation-amendment.md'})
    write('compatibility.json', {**identity, 'status': 'PASS', 'tests_passed': int(m.group(1)), 'failed': 0, 'xfailed': 6,
        'deferred': 'freeze-identity tests (stale until the new freeze) run in T0/T3', 'fixtures_verified': 41,
        'cache': 'NO_BUMP 130, identity lock MATCH', 'publication': 'PASS',
        'versions': 'Registry /21, Planner /18, engine /14, Adapter /3 and /4 tags, Bridge /1 and /2 unchanged', 'logs_sha256_lf': logs})
    write('gates.json', {**identity, 'A': 'PASS', 'B': 'PASS', 'C': 'PASS', 'D': 'PASS',
        'A_detail': {'closure_suite': green['summary'], 'previous_reviewer_probes': {'total': len(probes), 'neg_served': 0,
                     'internal_errors': 0, 'adjudicated_valid': sorted(adjudicated_valid)},
                     'findings_closed': ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7'], 'coverage': 'scope-entrypoint-coverage.json'},
        'B_detail': 'no kernel/engine/Registry change; incidence witnesses and Fraction oracle agreement in compatibility suite and locked 96',
        'C_detail': {'slices': slices, 'wrong_served_locked_96': sum(r['outcome'] == 'WRONG_SERVED' for r in rows)},
        'D_detail': 'compatibility.json', 'release_status': 'PENDING_PRE_FREEZE_ADVERSARIAL_REVIEW'})
    print(json.dumps({'gates': 'A-D PASS', 'probes': len(probes), 'slices': slices}, ensure_ascii=False))
else:
    assert load(U / 'pre-freeze-review-verdict.json')['verdict'] == 'PRE_FREEZE_ADVERSARIAL_REVIEW_PASS'
    f1 = module('closure_wave3_replay', dev.F1 / 'tools/build_and_evaluate_w3_f1.py')
    f1.WAVE3_WORKTREE = dev.HIST
    result = f1.evaluate_wave3_post_feedback_regression()
    result['task'] = 'HYBRID_V2_W3_F2_SCOPE_CENSUS_CLOSURE_AND_HYPHENATED_ID_RECOVERY'; result['identity'] = identity
    old = {r['id']: r for r in load(RUN / 'unified-solid-scope/wave3-post-feedback-regression.json')['cases']}
    result['baseline'] = '../unified-solid-scope/wave3-post-feedback-regression.json'
    result['transitions_from_baseline'] = [
        {'id': r['id'], 'before_outcome': old[r['id']]['outcome'], 'before_code': old[r['id']]['code'],
         'after_outcome': r['outcome'], 'after_code': r['code']} for r in result['cases']
        if (r['outcome'], r['code']) != (old[r['id']]['outcome'], old[r['id']]['code'])]
    write('wave3-post-feedback-regression.json', result)
    print(json.dumps({'summary': result['post_feedback_regression_summary'], 'transitions': result['transitions_from_baseline']}, ensure_ascii=False))
