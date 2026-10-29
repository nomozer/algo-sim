import hashlib, json, re, subprocess
from pathlib import Path

C = Path('docs/evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding/closed-input-contract')
U = C / 'cic-d1-contract-recovery'; L = Path('.superpowers/f2')
sha = lambda t: hashlib.sha256(t.replace('\r\n', '\n').encode()).hexdigest()
def put(name, obj):
    with (U / name).open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
def copy(src, dst):
    t = (L / src).read_text(encoding='utf-8')
    with (U / dst).open('x', encoding='utf-8', newline='\n') as f: f.write(t)
    return t, sha(t)
git = lambda *a: subprocess.check_output(['git', *a], text=True).strip()
head = git('rev-parse', 'HEAD'); prod = '717f8b2b1d284e3894af65190b13ba3619d5aff0'; assert head == prod
g, gs = copy('cic-d1-green-clean.log', 'green.log')
a, as_ = copy('cic-d1-gate-a.log', 'gate-a-acceptance.log')
d, ds = copy('cic-d1-diagnostics.log', 'gate-a-source-grammar-diagnostics.log')
obs = json.loads((L / 'cic-d1-observed-green.json').read_text(encoding='utf-8')); put('observed-green-717f8b2b.json', obs)
cases = json.loads((U / 'cases.json').read_text(encoding='utf-8'))['cases']
red = json.loads((U / 'observed-head-1490e3cd.json').read_text(encoding='utf-8'))['results']
R = obs['results']; o = lambda k, r: [R[k][r]['status'], R[k][r]['code']]
neg_ok = {k: all(o(k, r) == cases[k]['expected'][r] for r in R[k]) for k, c in cases.items() if c['class'] == 'NEG_LOCKED_GRAMMAR'}
ctrl_ok = {k: all((R[k][r]['status'], R[k][r]['code'], R[k][r].get('answer')) == (red[k][r]['status'], red[k][r]['code'], red[k][r].get('answer'))
                  for r in R[k]) for k, c in cases.items() if c['class'] == 'CONTROL_UNCHANGED'}
own = {k: {r: o(k, r) for r in R[k]} for k, c in cases.items() if c['class'] in ('NEG_OWNERSHIP', 'POS_OWNERSHIP_CONTROL')}
hist = {k: {r: o(k, r) for r in R[k]} for k, c in cases.items() if c['class'] == 'HISTORICAL_V1_SUPERSEDED'}
assert all(neg_ok.values()) and all(ctrl_ok.values())
assert all(v == ['REFUSED', 'INVALID_MATH_GOAL'] for h in hist.values() for v in h.values())
ctrl = R['N2v2.control_own_point']['a3']; assert ctrl['status'] == 'SERVED' and ctrl['answer']['mb'] == ['√5/2', 1, 'a']
put('green.json', {'phase': 'GREEN', 'head': head, 'product_commit': prod, 'tree_clean': True, 'live_provider_calls': 0,
    'command': 'python -B -m pytest -p no:cacheprovider test_cic_d1_locked_contract.py test_closed_input_contract.py '
               'test_typed_fact_next_v2_distance_bridge.py test_scope_census_closure.py test_unified_solid_scope.py '
               'test_adapter3_fallback_safety.py test_premise_scope_recovery.py -q -rA',
    'summary': g.strip().splitlines()[-1], 'failed': re.findall(r'^FAILED (\S+)', g, re.M), 'log': 'green.log', 'log_sha256_lf': gs,
    'locked_target8': 'PASS' if re.search(r'^PASSED .*test_malformed_distance_target_is_refused\[target8\]', g, re.M) else 'FAIL',
    'locked_malformed_distance_params_passed': len(re.findall(r'^PASSED .*test_malformed_distance_target_is_refused\[', g, re.M)),
    'attempts': [{'state': 'uncommitted fix, before the s8_preflight oracle addendum', 'summary': '1 failed, 790 passed, 6 skipped',
                  'failed': ['test_closed_input_contract.py::test_mandatory_mutants_are_killed[s8_preflight]'],
                  'cause': 'oracle used the superseded in-target N2 form (n2-amendment.md post-registration addendum)',
                  'log': 'not retained (console only)'}],
    'cases': {'receipt': 'observed-green-717f8b2b.json', 'neg_locked_grammar_refused_invalid': f'{sum(neg_ok.values())}/{len(neg_ok)}',
              'controls_unchanged_vs_red': f'{sum(ctrl_ok.values())}/{len(ctrl_ok)}', 'historical_v1_n2_now': hist}})
put('n2-ownership-proof.json', {'head': head, 'tests': 'backend/tests/geometry/test_cic_d1_locked_contract.py', 'route_outcomes': own,
    'proofs': {'1_schema_passes': 's8_raises() parses with parse_typed_fact_next before calling S8',
               '2_s8_ran': 'spy on typed_fact_next_bridge._kiem_pham_vi_tien_de entered on every route (test_n2v2_ownership_refused_before_capability)',
               '3_s8_detects': '_kiem_pham_vi_tien_de raises SOURCE_OBJECT_MISMATCH directly; route reason names goal mb',
               '4_semantic_before_capability': 'the same shape with the own point refuses BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY on pl/a4 while '
                                               'the negatives refuse SOURCE_OBJECT_MISMATCH; mutant capability_before_s8 killed',
               '5_no_fallback': '_shared_source_gate raises SOURCE_OBJECT_MISMATCH (no LEGACY_SOURCE_AUTHORITY); mutant semantic_fallback killed',
               '6_no_global_resolution': 'N2v2.qualified_namespace: pyr2::M (M only in pyr1) refused on every route'},
    'control': {'case': 'N2v2.control_own_point', 'a3': ctrl, 'oracle': cases['N2v2.control_own_point']['oracle']},
    'passed_nodes': sorted(set(re.findall(r'^PASSED \S+::(test_n2v2\S*)', g, re.M))), 'green_log_sha256_lf': gs})
mut = sorted(set(re.findall(r'^PASSED \S+::(test_(?:cic_d1_mutants_are_killed|mandatory_mutants_are_killed|closure_mutants_are_killed|'
                            r'oracles_kill_unified_scope_mutants)\[[^\]]+\])', g, re.M)))
put('mutation-results.json', {'head': head, 'status': 'PASS', 'cic_d1_mutants': [m for m in mut if 'cic_d1' in m],
    'mandatory_9': [m for m in mut if 'mandatory' in m],
    'retained_closure_and_unified': [m for m in mut if 'cic_d1' not in m and 'mandatory' not in m],
    'counts': {'cic_d1': sum('cic_d1' in m for m in mut), 'mandatory': sum('mandatory' in m for m in mut)},
    'method': 'source mutation in an isolated monkeypatch namespace; oracle passes on the real code and fails on the mutant', 'source_log': 'green.log'})
pr = json.loads((C / 'gate-a-cic-d1-probes.json').read_text(encoding='utf-8')); prev = json.loads((C / 'gate-a-v2-probes.json').read_text(encoding='utf-8'))
N = {r['probe']: r for r in pr['cases']}; V = {r['probe']: r for r in prev['cases']}
trans = [{'probe': k, 'class': N[k]['expected_class'],
          'before': {r: [V[k]['got'][r]['status'], V[k]['got'][r]['code']] for r in N[k]['got']},
          'after': {r: [N[k]['got'][r]['status'], N[k]['got'][r]['code']] for r in N[k]['got']}} for k in N if V[k]['got'] != N[k]['got']]
assert all(all(v == ['REFUSED', 'INVALID_MATH_GOAL'] for v in t['after'].values()) for t in trans)
put('gate-a.json', {'gate': 'A', 'status': 'PASS', 'head': head, 'live_provider_calls': 0,
    'closed_input_contract_acceptance': {'command': 'acceptance-manifest v2 files + test_cic_d1_locked_contract.py',
        'summary': a.strip().splitlines()[-1], 'failed': re.findall(r'^FAILED (\S+)', a, re.M), 'log': 'gate-a-acceptance.log', 'log_sha256_lf': as_},
    'reviewer_probes_203': {**pr['summary'], 'receipt': '../gate-a-cic-d1-probes.json', 'transitions_vs_gate_a_v2': trans,
        'served_positive_loss': ['S8.dev02_measure_target_solid_pyr1_M_control'],
        'reclassification': 'Every transition is an input with solid/solid_id inside a geometric target; all now REFUSED INVALID_MATH_GOAL. '
            'The one previously served POS probe uses {segment, solid: pyr1}, the form Owner rule CIC-D1-A declares invalid '
            '(not accepted because the solid exists and owns the operands). Its valid equivalent with goal-level solid_id is '
            'N2v2.control_own_point, SERVED (sqrt5/2)a. Recorded for the pre-freeze reviewer; not counted as a valid-positive loss.'},
    'source_grammar_diagnostics': {'status': 'PENDING_SOURCE_GRAMMAR_SUPPORT', 'summary': d.strip().splitlines()[-1], 'counted_as_pass': False,
        'log': 'gate-a-source-grammar-diagnostics.log', 'log_sha256_lf': ds},
    'mutants': 'mutation-results.json', 'not_combined': True})
changed = git('diff', '--name-only', '5e44d5da', head, '--', 'backend/app', 'frontend/src').splitlines()
put('gate-b.json', {'gate': 'B', 'status': 'PASS', 'head': head, 'product_changed_since_5e44d5da': changed,
    'cic_d1_product_diff': git('diff', '--stat', '1490e3cd', head, '--', 'backend/app').splitlines(),
    'unchanged': 'registry.py, Planner, Engine, radical kernel, Adapter /4 product code (adapter4_route.py), frontend',
    'adapter4_route_changed_vs_main': bool(git('diff', '--name-only', '996f114b', head, '--', 'backend/app/ai/adapter4_route.py'))})
gc = json.loads((L / 'cic-d1-gate-c.json').read_text(encoding='utf-8')); assert gc['match'] == 96 and gc['wrong_served'] == 0
put('gate-c.json', {'gate': 'C', 'status': 'PASS', 'head': head, **gc})
print('ok', a.strip().splitlines()[-1], len(trans), changed, {k: len(v) for k, v in {'cic': [m for m in mut if 'cic_d1' in m], 'mand': [m for m in mut if 'mandatory' in m]}.items()})
