import hashlib, json, re, subprocess
from pathlib import Path

C = Path('docs/evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding/closed-input-contract')
U = C / 'cic-d1-contract-recovery'; L = Path('.superpowers/f2')
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_lf(t): return hashlib.sha256(t.replace('\r\n', '\n').encode()).hexdigest()
def put(name, obj):
    with (U / name).open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
git = lambda *a: subprocess.check_output(['git', *a], text=True).strip()
TB = re.compile(r'(?m)^[ \t]*(?:Traceback \(most recent call last\):|File "[^"\r\n]+", line \d+)')

full = (L / 'cic-d1-full.log').read_text(encoding='utf-8')
assert full.strip().splitlines()[-1] == '0' and 'exit=1' in full                 # tree stayed clean during the run
summary = [l for l in full.splitlines() if re.match(r'^\d+ (passed|failed)', l)][-1]
failed = sorted({x.split(' - ')[0] for x in re.findall(r'^FAILED (.+)$', full, re.M)})
pre = (C / 'source-grammar-adjudication/gate-d-pre-patch-5e44d5da-identity-12.log').read_text(encoding='utf-8')
prefail = {x.split(' - ')[0] for x in re.findall(r'^FAILED (.+)$', pre, re.M)}
assert set(failed) <= prefail and len(failed) == 11
digest_lines = [summary, *[f'FAILED {f}' for f in failed]]
assert not any(TB.search(l) for l in digest_lines)
with (U / 'gate-d-full-backend-pytest.summary.txt').open('x', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(digest_lines) + '\n')
v2 = (L / 'cic-d1-gate-d-locked-v2.log').read_text(encoding='utf-8'); assert not TB.search(v2) and 'failed' not in v2.strip().splitlines()[-1]
with (U / 'gate-d-locked-v2.log').open('x', encoding='utf-8', newline='\n') as f: f.write(v2)
fx = json.loads((L / 'cic-d1-41-fixtures-named-plane.json').read_text(encoding='utf-8')); assert fx['verified'] == 41 and not fx['problems']
put('verification-41-fixtures.json', fx)
cache = (L / 'cic-d1-cache.log').read_text(encoding='utf-8'); assert 'Khoá khớp · CACHE_VERSION 130' in cache
with (U / 'cache.log').open('x', encoding='utf-8', newline='\n') as f: f.write(cache)
pub = (L / 'cic-d1-publication.log').read_text(encoding='utf-8')
with (U / 'publication.log').open('x', encoding='utf-8', newline='\n') as f: f.write(pub)
viol = re.findall(r'^VIOLATION rule=(\S+) path=(\S+) blob=([0-9a-f]+) line=(\d+)', pub, re.M)
paths = sorted({(p, b) for _r, p, b, _l in viol})
proposal = []
for p, b in paths:
    raw = subprocess.check_output(['git', 'cat-file', 'blob', b])
    first = git('log', '--diff-filter=A', '--format=%H %cI', '--', p).splitlines()[-1].split()
    proposal.append({'path': p, 'blob': b, 'sha256': sha_bytes(raw), 'bytes': len(raw), 'rules': ['PY_TRACEBACK'],
                     'category': 'RAW_PYTHON_TRACEBACK_IN_LOG', 'scope': 'HISTORY_AND_TIP', 'first_commit': first[0],
                     'first_commit_date': first[1], 'already_public_on_origin_main': False,
                     'traceback_source': 'pytest PytestUnhandledThreadExceptionWarning: UnicodeDecodeError (cp1252) in a subprocess '
                                         'reader thread of test_docs_information_architecture::test_inv_20; no secret, no product stack',
                     'owner_decision': 'PENDING_OWNER_DECISION'})
put('publication-exception-proposal.json', {'schema': 'publication-exceptions/1 (proposal only)',
    'target_registry': 'docs/evaluation/geometry/runs/publication-safety-remediation/publication_exceptions.json',
    'note': 'Not written into the registry. Only the Owner may set owner_decision to APPROVED_BY_USER. Introduced by this '
            'agent in 1490e3cd (previous layer) by committing raw pytest logs; no later commit adds a traceback.',
    'entries': proposal})
head = git('rev-parse', 'HEAD')
put('gate-d.json', {'gate': 'D', 'head': head, 'product_commit': '717f8b2b1d284e3894af65190b13ba3619d5aff0', 'live_provider_calls': 0,
    'status': 'PRE_FREEZE_COMPATIBILITY_PASS; PUBLICATION_BLOCKED_PENDING_OWNER_EXCEPTION',
    'overall_pass': False,
    'cic_d1': 'PASS: test_malformed_distance_target_is_refused[target8] and all 16 locked params (gate-d-locked-v2.log)',
    'locked_v2_targeted': {'summary': v2.strip().splitlines()[-1], 'files': 'backend/tests/geometry/test_typed_fact_next_v2*.py (5 files)',
                           'log': 'gate-d-locked-v2.log', 'log_sha256_lf': sha_lf(v2)},
    'full_backend_pytest': {'summary': summary, 'tree_clean_during_run': True,
        'failed_all_PENDING_NEW_FREEZE': failed,
        'identical_failures_at_5e44d5da': True,
        'previous_dirty_tree_failure': 'test_holdout_readiness::test_bao_cao_da_sinh_va_KHONG_TROI passes on the clean tree',
        'real_product_regressions': [],
        'committed_digest': 'gate-d-full-backend-pytest.summary.txt',
        'raw_log': {'path': '.superpowers/f2/cic-d1-full.log (ignored, not committed: contains a pytest thread-exception traceback)',
                    'sha256_bytes': sha_bytes((L / 'cic-d1-full.log').read_bytes())}},
    'fixtures': {'set': 'docs/evaluation/geometry/runs/hybrid-v2-backend-generalization/fixtures-adapter-2-named-plane (current, referenced by tests)',
                 'verified': 41, 'problems': 0, 'receipt': 'verification-41-fixtures.json',
                 'harness_note': 'First checked the older sets fixtures-adapter-2 (12 problems) and fixtures-adapter-2-cache130 (4) by mistake; '
                                 'main 996f114b and 5e44d5da give the same problems on those older sets, so they are stale exports, not this product'},
    'cache': 'NO_BUMP 130, identity lock MATCH (cache.log)',
    'publication': {'command': 'backend/scripts/check_publication_safety.py --range 996f114b..HEAD', 'verdict': 'BLOCKED',
                    'violations': len(viol), 'blobs': [p for p, _b in paths], 'introduced_by': '1490e3cd (this agent, previous layer)',
                    'this_cycle_adds_violations': False, 'proposal': 'publication-exception-proposal.json',
                    'resolution': 'Owner decision only (APPROVED_BY_USER on exact path/blob/sha256); history is not rewritten'}})
print(summary, len(failed), len(viol), [p.split('/')[-1] for p, _ in paths])
