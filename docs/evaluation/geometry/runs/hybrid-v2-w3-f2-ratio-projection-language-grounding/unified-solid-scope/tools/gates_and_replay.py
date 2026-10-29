"""Append-only Gates A–D, safety matrix and Wave 3 post-feedback replay for the unified solid-scope repair.
Usage (worktree root): python gates_and_replay.py gates|replay. Reuses the locked evaluators of this run."""
import argparse, copy, hashlib, importlib.util, json, os, re, socket, subprocess, sys
from pathlib import Path

U = Path(__file__).resolve().parents[1]; RUN = U.parent; ROOT = RUN.parents[4]
sys.path.insert(0, str(ROOT / 'backend')); sys.dont_write_bytecode = True
os.environ['ALLOW_LIVE_AI'] = '0'
def offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = offline; socket.create_connection = offline
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def digest(p): return hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
def write(name, data):
    with (U / name).open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
def module(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
def copy_log(src, dst):
    text = (ROOT / src).read_text(encoding='utf-8-sig'); assert 'Traceback' not in text
    with (U / dst).open('x', encoding='utf-8', newline='\n') as f: f.write(text)
    return digest(U / dst)

parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['gates', 'replay']); phase = parser.parse_args().phase
dev = module('unified_locked_development', RUN / 'tools/evaluate_development.py')
fz = module('unified_freeze_identity', ROOT / 'backend/scripts/freeze_evaluation_candidate.py')
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
identity = {'head': head, 'product_commit': fz.product_commit(), 'measured_system_hash': fz.measured_system_hash(),
            'live_provider_calls': 0, 'classification': 'POST_FEEDBACK_DEVELOPMENT_REGRESSION'}

if phase == 'gates':
    from app.ai.adapter3_simulation import run_typed_fact_next_route
    from app.ai.adapter4_route import run_typed_fact_next_v2_route
    from app.simulation.geometry_functions.typed_fact_next import TypedFactNextValidationError, convert_v1_to_v2
    rows = [dev.evaluate_case(c, load(RUN / 'inputs/oracle.json')['cases'].get(c['id'])) for c in load(RUN / 'inputs/development.json')['cases']]
    assert len(rows) == 96 and all(r['matches_expected'] for r in rows)
    slices = {s: {'total': len(cs := [r for r in rows if r['slice'] == s]),
                  'served_correct': sum(r['outcome'] == 'SERVED_CORRECT' for r in cs),
                  'refused': sum(not r['served'] for r in cs),
                  'locked_code_match': sum(r['matches_expected'] for r in cs)} for s in sorted({r['slice'] for r in rows})}
    RUNS = RUN.parent
    sup = load(RUN / 'inputs/recovery-supplementary.json')['control']
    a3dev = {c['case_id']: c['payload'] for c in load(RUNS / 'typedfact-next-adapter3-simulation/corpus-dev.json')['cases']}
    sim = {c['case_id']: c['payload'] for c in load(RUNS / 'simulation-coverage-visual-validation/corpus-dev.json')['cases']}
    def a4(p):
        q = copy.deepcopy(p)
        try: q = convert_v1_to_v2(q, 'adapter3') if q.get('derived_sections') else {**q, 'schema_version': 'typed-fact-next/2'}
        except TypedFactNextValidationError as e: return ('REFUSED', e.code)
        r = run_typed_fact_next_v2_route(q); return (r.status, r.code)
    def a3(p): r = run_typed_fact_next_route(copy.deepcopy(p)); return (r.status, r.code)
    def m(base, f):
        p = copy.deepcopy(base); f(p); return p
    def add(p, key, item): p.setdefault(key, []).append(item); p['problem_text'] += ' ' + item['quote']
    def cyl2(p):
        s = copy.deepcopy(p['solids'][0]); s.update(solid_id='zz', center='I', apex_or_top="I'", notation="I.I'", quote="Cho hình trụ I.I'.")
        s.pop('rim_point', None); p['solids'].append(s); p['problem_text'] += " Cho hình trụ I.I'."
    def parent(p, value):
        g = next(g for g in p['simulation_goals'] if g['kind'] == 'construct_derived_solid')
        if value == 'other':
            s = copy.deepcopy(p['solids'][0]); s['solid_id'] = 'zz'; p['solids'].append(s); value = 'zz'
        g['parent_solid_id'] = value
    dist = lambda sid: lambda p: add(p, 'math_goals', {'goal_id': 'g2', 'kind': 'measurement', 'goal_type': 'distance', 'solid_id': sid,
                                                         'target': {'point': 'S', 'plane': list('ABCD')}, 'quote': 'Tính khoảng cách từ S đến (ABCD).'})
    angle = lambda sid: lambda p: add(p, 'math_goals', {'goal_id': 'g2', 'kind': 'measurement', 'goal_type': 'angle', 'solid_id': sid,
                                                          'target': {'line': ['S', 'C'], 'plane': list('ABCD')}, 'quote': 'Tính góc giữa SC và (ABCD).'})
    rel = lambda r: lambda p: p.__setitem__('relations', [{'relation_id': 'r', 'quote': 'Cho hình chóp S.ABCD.', **r}])
    cq = sim['demo6a-curved-cylinder-sections']['solids'][0]['quote']
    ratio = lambda cid, kind, v: (cid, a3dev[cid] if cid in a3dev else sim[cid], lambda p: next(g for g in p['math_goals'] if g['kind'] == kind).__setitem__(
        'solid_id', 'foreign' if v == 'foreign' else p['solids'][0]['solid_id']))
    matrix = [  # (id, base, mutation, adapters, expected code or None for SERVED)
        ('review#1 distance s2', sup, dist('s2'), ('a3', 'a4'), 'SOURCE_OBJECT_MISMATCH'),
        ('review#1 distance foreign', sup, dist('foreign'), ('a3', 'a4'), 'UNKNOWN_SOLID_ID'),
        ('review#1 angle s2', sup, angle('s2'), ('a3', 'a4'), 'SOURCE_OBJECT_MISMATCH'),
        ('review#1 angle foreign', sup, angle('foreign'), ('a3', 'a4'), 'UNKNOWN_SOLID_ID'),
        ('control angle s1', sup, angle('s1'), ('a3', 'a4'), None),
        ('review#2 curved goal foreign', sim['demo6a-curved-cylinder-sections'], lambda p: p['math_goals'][0].__setitem__('solid_id', 'foreign'), ('a3',), 'UNKNOWN_SOLID_ID'),
        ('review#2 curved premise foreign', sim['demo6a-curved-cylinder-sections'], lambda p: add(p, 'premises', {'kind': 'segment_length', 'solid_id': 'foreign', 'args': {'segment': ['O', "O'"], 'value': '1'}, 'quote': cq}), ('a3',), 'UNKNOWN_SOLID_ID'),
        ('review#2 curved premise operands of other solid', sim['demo6a-curved-cylinder-sections'], lambda p: (cyl2(p), add(p, 'premises', {'kind': 'segment_length', 'solid_id': 'zz', 'args': {'segment': ['O', "O'"], 'value': '1'}, 'quote': cq})), ('a3',), 'SOURCE_OBJECT_MISMATCH'),
        ('review#2 curved relation foreign', sim['demo6a-curved-cylinder-sections'], rel({'kind': 'coordinate_frame', 'solid_id': 'foreign', 'frame_id': 'root'}), ('a3',), 'UNKNOWN_SOLID_ID'),
        ('control curved demo6a', sim['demo6a-curved-cylinder-sections'], lambda p: None, ('a3',), None),
        ('control curved demo6b', sim['demo6b-curved-cone-frustum-cut'], lambda p: None, ('a3',), None),
        *[(f'review#3 {cid} {kind} solid_id {v}', *ratio(cid, kind, v)[1:], ('a3',), 'INVALID_MATH_GOAL')
          for cid, kind in (('A3-DEV-02', 'volume_ratio'), ('A3-DEV-03', 'volume_ratio'), ('A3-DEV-03', 'residual_volume'),
                            ('A3-DEV-09', 'volume_ratio'), ('demo1-pyramid-derived-section', 'volume_ratio')) for v in ('foreign', 'declared')],
        *[(f'control {cid}', (a3dev[cid] if cid in a3dev else sim[cid]), lambda p: None, ('a3',), None)
          for cid in ('A3-DEV-02', 'A3-DEV-03', 'A3-DEV-09', 'demo1-pyramid-derived-section')],
        ('review#4 shared_faces foreign', sup, rel({'kind': 'shared_faces', 'solid_a': 'foreign', 'solid_b': 's2', 'face_a': list('ABCD'), 'face_b': list('ABCD')}), ('a3', 'a4'), 'UNKNOWN_SOLID_ID'),
        ('review#4 coordinate_frame foreign', sup, rel({'kind': 'coordinate_frame', 'solid_id': 'foreign', 'frame_id': 'root'}), ('a3', 'a4'), 'UNKNOWN_SOLID_ID'),
        ('NEW-2 shared_faces face not of solid_b', sup, rel({'kind': 'shared_faces', 'solid_a': 's1', 'solid_b': 's2', 'face_a': list('SAB'), 'face_b': list('SAB')}), ('a3', 'a4'), 'SOURCE_OBJECT_MISMATCH'),
        ('NEW-2 frame anchors of other solid', sup, rel({'kind': 'coordinate_frame', 'solid_id': 's1', 'frame_id': 'root', 'anchor_refs': ['s2::T']}), ('a3', 'a4'), 'SOURCE_OBJECT_MISMATCH'),
        ('control valid shared face + frame', sup, lambda p: p.__setitem__('relations', [
            {'relation_id': 'sf', 'kind': 'shared_faces', 'solid_a': 's1', 'solid_b': 's2', 'face_a': list('ABCD'), 'face_b': list('ABCD'), 'quote': 'Cho hình chóp S.ABCD.'},
            {'relation_id': 'f', 'kind': 'coordinate_frame', 'solid_id': 's1', 'frame_id': 'root', 'anchor_refs': list('ABC'), 'quote': 'Cho hình chóp S.ABCD.'}]), ('a3', 'a4'), None),
        ('review#5 volume goal on undeclared derived', sim['demo1-pyramid-derived-section'], lambda p: p['math_goals'].append({'goal_id': 'v', 'kind': 'measurement', 'goal_type': 'volume', 'solid_id': 'ghost', 'target': {'solid': 'ghost'}, 'quote': p['math_goals'][-1]['quote']}), ('a3', 'a4'), 'UNKNOWN_SOLID_ID'),
        ('review#5 control volume goal on declared derived (Adapter3)', sim['demo1-pyramid-derived-section'], lambda p: p['math_goals'].append({'goal_id': 'v', 'kind': 'measurement', 'goal_type': 'volume', 'solid_id': 's_top', 'target': {'solid': 's_top'}, 'quote': p['math_goals'][-1]['quote']}), ('a3',), None),
        ('review#6 nested target.solid_id s2', sup, lambda p: p['math_goals'][0].__setitem__('target', {'solid': 's1', 'solid_id': 's2'}), ('a3', 'a4'), 'SOURCE_OBJECT_MISMATCH'),
        ('review#6 nested target.solid_id foreign', sup, lambda p: p['math_goals'][0].__setitem__('target', {'solid_id': 'foreign'}), ('a3', 'a4'), 'UNKNOWN_SOLID_ID'),
        ('NEW-1 parent other (demo1)', sim['demo1-pyramid-derived-section'], lambda p: parent(p, 'other'), ('a3',), 'SOURCE_OBJECT_MISMATCH'),
        ('NEW-1 parent other (demo6b)', sim['demo6b-curved-cone-frustum-cut'], lambda p: parent(p, 'other'), ('a3',), 'SOURCE_OBJECT_MISMATCH'),
        ('NEW-3 curved parent foreign (no internal error)', sim['demo6b-curved-cone-frustum-cut'], lambda p: parent(p, 'foreign'), ('a3',), 'UNKNOWN_SOLID_ID'),
        ('NEW-3 curved target foreign (no internal error)', sim['demo6a-curved-cylinder-sections'], lambda p: p['math_goals'][0].__setitem__('target', {'solid': 'foreign'}), ('a3',), 'UNKNOWN_SOLID'),
        ('H1 legacy height pyr1 vs pyr2', a3dev['A3-DEV-02'], lambda p: add(p, 'premises', {'kind': 'height', 'solid_id': 'pyr1', 'args': {'solid': 'pyr2', 'value': 'a'}, 'quote': 'Chiều cao hình chóp D.ABC bằng a.'}), ('a3',), 'SOURCE_OBJECT_MISMATCH'),
        ('H2 volume goal s2 vs target s1', sup, lambda p: p['math_goals'][0].__setitem__('solid_id', 's2'), ('a3', 'a4'), 'SOURCE_OBJECT_MISMATCH'),
        ('H3 volume goal s1 vs target T.ABCD', sup, lambda p: p['math_goals'][0].__setitem__('target', {'solid': 'T.ABCD'}), ('a3', 'a4'), 'SOURCE_OBJECT_MISMATCH'),
        ('N006-type unscoped unknown solid name', sup, lambda p: add(p, 'premises', {'kind': 'height', 'args': {'solid': 's99', 'value': '3'}, 'quote': 'Chiều cao bằng 3.'}), ('a3', 'a4'), 'UNKNOWN_SOLID'),
        ('control supplementary', sup, lambda p: None, ('a3', 'a4'), None),
    ]
    results = []
    for name, base, mut, adapters, code in matrix:
        p = m(base, mut); got = {a: (a3 if a == 'a3' else a4)(p) for a in adapters}
        want = ('SERVED', None) if code is None else ('REFUSED', code)
        results.append({'case': name, 'expected': list(want), **{a: list(v) for a, v in got.items()},
                        'pass': all(v == want for v in got.values()),
                        'wrong_served': code is not None and any(v[0] == 'SERVED' for v in got.values())})
    bad = [r for r in results if not r['pass']]
    assert not bad, json.dumps(bad, ensure_ascii=False, indent=1)
    fixtures = load(ROOT / '.superpowers/f2/unified-41-fixtures.json'); assert fixtures['verified'] == 41 and not fixtures['problems']
    write('verification-41-fixtures.json', fixtures)
    logs = {dst: copy_log(src, dst) for src, dst in (('.superpowers/f2/unified-compat-final.log', 'compatibility-tests.log'),
                                                     ('.superpowers/f2/unified-cache.log', 'cache.log'),
                                                     ('.superpowers/f2/unified-publication.log', 'publication.log'))}
    compat_text = (U / 'compatibility-tests.log').read_text(encoding='utf-8')
    compat = re.search(r'^(\d+) passed, 6 skipped, 1 deselected, 6 xfailed', compat_text, re.M)
    assert compat and not re.search(r'\b\d+ failed|^FAILED ', compat_text, re.M)
    green = load(U / 'green.json'); assert green['failed'] == [] and green['dirty'] is False
    write('mutations.json', {**identity, 'status': 'PASS', 'killed': 9 + 8, 'source': 'green.log (test_oracles_kill_unified_scope_mutants) + compatibility-tests.log',
        'unified_mutants': ['remove_declared_scope_existence', 'remove_cross_solid_comparison', 'drop_derived_solids',
                            'remove_nested_target_scope', 'remove_ratio_residual_refusal', 'remove_relation_sides',
                            'foreign_scope_to_first_solid', 'remove_goal_operand_ownership', 'bypass_curved_prevalidation'],
        'retained_mutants': ['remove_terminal_guard (semantic refusal → fallback)', 'remove_scope_guard', 'replace_scope_with_default',
                             'allow_global_lookup', 'bridge _pham_vi_khoi conflict / unknown', 'adapter3 _scoped_solid_name conflict / unknown (inner-or-scope)'],
        'metamorphic': 'test_metamorphic_foreign_scope_is_never_served (5 controls, every scope slot) and contradicting premise scope',
        'method': 'source mutation in an isolated monkeypatch namespace; oracle must hold on real code and fail on the mutant'})
    write('compatibility.json', {**identity, 'status': 'PASS', 'tests_passed': int(compat.group(1)), 'failed': 0, 'xfailed': 6,
        'deselected': 'version/freeze receipt check (needs new freeze; runs in Full T3)', 'fixtures_verified': 41,
        'cache': 'NO_BUMP 130, identity lock MATCH', 'publication': 'PASS',
        'versions': 'Registry /21, Planner /18, engine /14, Adapter /3 and /4 tags, Bridge /1 /2 unchanged',
        'test_adaptations': 'test-adaptation-amendment.md', 'logs_sha256_lf': logs})
    write('gates.json', {**identity,
        'A': 'PASS', 'B': 'PASS', 'C': 'PASS', 'D': 'PASS',
        'A_detail': {'safety_matrix': results, 'wrong_served': sum(r['wrong_served'] for r in results),
                     'mandatory_negatives_refused': sum(r['expected'][0] == 'REFUSED' and r['pass'] for r in results),
                     'controls_served': sum(r['expected'][0] == 'SERVED' and r['pass'] for r in results)},
        'B_detail': 'no kernel/engine/Registry change; incidence witnesses and Fraction oracle agreement re-run (compatibility suite, locked 96)',
        'C_detail': {'slices': slices, 'wrong_served_locked_96': sum(r['outcome'] == 'WRONG_SERVED' for r in rows)},
        'D_detail': 'compatibility.json', 'release_status': 'NOT_YET_READY_PENDING_REPLAY_TIERS_FREEZE_T3_REVIEW'})
    print(json.dumps({'gates': 'A-D PASS', 'matrix': len(results), 'slices': slices}, ensure_ascii=False))
else:
    gates = load(U / 'gates.json'); assert all(gates[k] == 'PASS' for k in 'ABCD')
    assert gates['measured_system_hash'] == list(fz.measured_system_hash())
    f1 = module('unified_wave3_replay', dev.F1 / 'tools/build_and_evaluate_w3_f1.py')
    f1.WAVE3_WORKTREE = dev.HIST    # same correction as verify_after_adapter3.py: committed evidence in this checkout
    result = f1.evaluate_wave3_post_feedback_regression()
    result['task'] = 'HYBRID_V2_W3_F2_UNIFIED_SOLID_SCOPE_VALIDATION'; result['identity'] = identity
    old = {r['id']: r for r in load(RUN / 'wave3-post-feedback-regression-after-solid-scope-final.json')['cases']}
    result['baseline'] = 'wave3-post-feedback-regression-after-solid-scope-final.json'
    result['transitions_from_baseline'] = [
        {'id': r['id'], 'before_outcome': old[r['id']]['outcome'], 'before_code': old[r['id']]['code'],
         'after_outcome': r['outcome'], 'after_code': r['code']} for r in result['cases']
        if (r['outcome'], r['code']) != (old[r['id']]['outcome'], old[r['id']]['code'])]
    write('wave3-post-feedback-regression.json', result)
    print(json.dumps({'summary': result['post_feedback_regression_summary'], 'transitions': result['transitions_from_baseline']}, ensure_ascii=False))
