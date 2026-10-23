"""Read-only Session 3 receipt reconciliation. No benchmark or provider calls."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess


def git(root, *args):
    p = subprocess.run(['git', '-c', f'safe.directory={root.resolve().as_posix()}', '-C', str(root), *args],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return {'exit_code': p.returncode, 'stdout': p.stdout.strip(), 'stderr': p.stderr.strip()}


def main(repo, session3, output):
    run = session3 / 'docs/evaluation/geometry/runs/hybrid-contract-v2'
    summary = json.loads((run / 'verification/evaluation/session3-evaluation-summary.json').read_text(encoding='utf-8'))
    files = {}
    for p in sorted(run.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:
            b = p.read_bytes()
            files[p.relative_to(session3).as_posix()] = {
                'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(),
                'lf_sha256': hashlib.sha256(b.replace(b'\r\n', b'\n')).hexdigest()}
    fuzz = {}
    for p in sorted((run / 'verification/fuzz').glob('*.json')):
        d = json.loads(p.read_text(encoding='utf-8'))
        fuzz[p.name] = {k: d[k] for k in ('route', 'runs', 'escaped_exceptions', 'internal_errors')}
    # The report mixes payload counts, route rows and plan inspections: publish units explicitly.
    units = {'A_locked_payloads': 47, 'B_replayed_payloads': 60, 'C_parity_payloads': 316,
             'D_metamorphic_payloads': 33, 'E_payload_conventions': 20, 'F_budget_payloads': 8,
             'G_corpus_payloads': 16, 'H_two_arm_rows': 60}
    assert [summary['family_a_locked_grammar_v2']['cases'], summary['family_b_session1_dual_run']['cases'],
            summary['family_c_contract_parity']['cases'], len(json.loads((run / 'verification/evaluation/session3-evaluation-full.json').read_text(encoding='utf-8'))['family_d_rows']),
            summary['family_e_negative_controls']['payloads'], len(summary['family_f_ir_budget_and_composition']['budget']),
            summary['family_g_adapter3_dev_corpus']['cases'], summary['family_h_route_b_benchmark']['evaluations']] == list(units.values())
    refs = {'main', 'origin/main', 'HEAD', '82d3d255', '227d447f', '0f7b3a69', '69bd2fe4', '84c729e0'}
    refs.update(git(repo, 'for-each-ref', '--format=%(refname:short)', 'refs/heads')['stdout'].splitlines())
    identities = {ref: git(repo, 'show', '-s', '--format=%H %T %cI %s', ref) for ref in sorted(refs)}
    assert all(r['exit_code'] == 0 for r in identities.values()), 'REF_RESOLUTION_FAILED'
    worktrees = []
    for block in git(repo, 'worktree', 'list', '--porcelain')['stdout'].split('\n\n'):
        if not block: continue
        p = Path(block.splitlines()[0].removeprefix('worktree '))
        worktrees.append({'identity': block, 'status': git(p, 'status', '--short', '--untracked-files=normal'),
                          'backend_tree': git(p, 'rev-parse', 'HEAD:backend/app')['stdout'],
                          'frontend_tree': git(p, 'rev-parse', 'HEAD:frontend/src')['stdout']})
    ancestry = {}
    for a,b in [('origin/main','main'),('82d3d255','227d447f'),('227d447f','0f7b3a69'),('0f7b3a69','main'),('main','0f7b3a69')]:
        ancestry[f'{a} -> {b}'] = git(repo,'merge-base','--is-ancestor',a,b)['exit_code']
    base = git(repo,'merge-base','main','0f7b3a69')['stdout']
    assert base, 'MERGE_BASE_UNAVAILABLE'
    merge = git(repo,'merge-tree',base,'main','0f7b3a69')
    result = {'schema':'session4a_receipt_audit/1', 'provider_calls':0,
              'refs':identities, 'worktrees':worktrees, 'ancestry_exit_codes':ancestry,
              'remote_freshness':'LOCAL_TRACKING_REF_ONLY_NO_FETCH',
              'merge_analysis':{'base':base,'command':'git merge-tree BASE main 0f7b3a69 (read-only three-tree mode)',
                                'exit_code':merge['exit_code'],'conflict_markers':merge['stdout'].count('<<<<<<<'),
                                'output_sha256':hashlib.sha256(merge['stdout'].encode()).hexdigest()},
              'diff_main_s3':git(repo,'diff','--name-status','main','0f7b3a69','--','backend/app','frontend')['stdout'],
              'units':units,'mixed_unit_total':sum(units.values()),'claimed_562':'NOT_RECONCILED',
              'composition_plan_inspections':summary['family_f_ir_budget_and_composition']['composition']['plans'],
              'fuzz':fuzz,'grammar_expected':dict(Counter(c['expected'] for c in json.loads((run/'grammar-set.json').read_text(encoding='utf-8'))['cases'])),
              'immutable_sources':files}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'mixed_units':sum(units.values()),'plan_inspections':result['composition_plan_inspections'],'fuzz':fuzz},indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('repo',type=Path);p.add_argument('session3',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();main(a.repo,a.session3,a.output)
