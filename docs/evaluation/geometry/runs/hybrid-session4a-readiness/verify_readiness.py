"""Bounded sequential checks; only sanitized summaries/hashes enter the receipt."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def git(root,*args):
    r=subprocess.run(['git','-c',f'safe.directory={root.as_posix()}','-C',str(root),*args],
                     capture_output=True,text=True,encoding='utf-8',errors='replace')
    if r.returncode:raise RuntimeError('GIT_CHECK_FAILED')
    return r.stdout.strip()


def main(work,source,original):
    run=work/'docs/evaluation/geometry/runs/hybrid-session4a-readiness'
    env=os.environ.copy()
    env.update(ALLOW_LIVE_AI='0',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',
               OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
               PYTHONPATH=str(source/'backend'),SESSION4A_SOURCE_ROOT=str(source))
    n=int(env.get('GIT_CONFIG_COUNT','0'));env.update({f'GIT_CONFIG_KEY_{n}':'safe.directory',
        f'GIT_CONFIG_VALUE_{n}':source.as_posix(),'GIT_CONFIG_COUNT':str(n+1)})
    before={'source_head':git(source,'rev-parse','HEAD'),'source_status':git(source,'status','--short'),
            'main':git(original,'rev-parse','main'),'origin_main':git(original,'rev-parse','origin/main'),
            'original_head':git(original,'rev-parse','HEAD'),'original_status':git(original,'status','--short')}
    assert before['source_head']=='84c729e0b0df7868dfcc0a6e48cac457d7959e92'
    assert before['source_status']==''
    checks=[]
    def command(name,args,cwd):
        t=time.monotonic()
        r=subprocess.run([sys.executable,*args],cwd=cwd,env=env,capture_output=True,timeout=180)
        text=r.stdout.decode('utf-8',errors='replace')
        checks.append({'name':name,'command':[sys.executable,*args],'cwd':str(cwd),'exit_code':r.returncode,
                       'elapsed_seconds':round(time.monotonic()-t,3),
                       'summary':[x for x in text.splitlines() if re.search(r'\d+ passed|\d+ failed|Candidate |khớp',x)],
                       'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),
                       'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()})
        print(json.dumps(checks[-1],ensure_ascii=True),flush=True)
    command('candidate_verify',['backend/scripts/freeze_evaluation_candidate.py','--verify'],source)
    tests=['backend/tests/geometry/test_hybrid_contract_v2.py',
           'backend/tests/geometry/test_hybrid_contract_unification.py',
           'backend/tests/geometry/test_goal_directed_function_composition.py',
           'backend/tests/test_route_aware_cache.py',
           'backend/tests/geometry/test_hybrid_backend_integration.py::test_version_constants_surface_fingerprints_and_historical_receipt_preservation',
           'backend/tests/semantic_program/test_evaluation_candidate.py',str(run/'test_offline_replay.py')]
    command('targeted_source_and_replay',['-m','pytest','-q','-p','no:cacheprovider','--tb=no',
            '--basetemp',str(work/'.superpowers/verification-pytest-temp'),*tests],source)
    command('documentation_invariants',['-m','pytest','-q','-p','no:cacheprovider','--tb=no',
            'backend/tests/geometry/test_docs_information_architecture.py','-k',
            'inv_06 or inv_07 or inv_08 or inv_10 or inv_11 or inv_12 or inv_23 or inv_24'],work)
    spec=importlib.util.spec_from_file_location('freeze',source/'backend/scripts/freeze_evaluation_candidate.py')
    freeze=importlib.util.module_from_spec(spec);spec.loader.exec_module(freeze)
    measured=freeze.measured_system_hash();entries=freeze._measured_system_files()
    sources=json.loads((run/'results/receipt-audit-attempt2.json').read_text(encoding='utf-8'))['immutable_sources']
    mutations=[name for name,meta in sources.items() if hashlib.sha256((original/'.superpowers/worktrees/hybrid-backend-s3'/name).read_bytes()).hexdigest()!=meta['sha256']]
    after={'source_head':git(source,'rev-parse','HEAD'),'source_status':git(source,'status','--short'),
           'main':git(original,'rev-parse','main'),'origin_main':git(original,'rev-parse','origin/main'),
           'original_head':git(original,'rev-parse','HEAD'),'original_status':git(original,'status','--short')}
    product_diff=git(work,'diff','--name-only','--','backend/app','frontend')
    result={'schema':'session4a_verification/1','provider_calls':0,'workers':1,'blas_threads':1,
            'before':before,'after':after,'preserved':before==after,'checks':checks,
            'measured_system':{'sha256':measured[0],'entries':measured[1],'unique_files':len(set(entries)),
              'entry_prefix_counts':dict(Counter(p.relative_to(source).parts[0] for p in entries))},
            'historical_artifact_mutations':mutations,'product_diff':product_diff,
            'status':'PASS' if all(x['exit_code']==0 for x in checks) and before==after and not mutations
              and not product_diff and measured==('413ee525d20874aa346b13df7e51019266f7d4701af56719c2a2ee736266b5df',116) else 'FAIL'}
    with (run/'results/final-verification.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
    print(result['status'])
    return int(result['status']!='PASS')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('work',type=Path);p.add_argument('source',type=Path);p.add_argument('original',type=Path)
    a=p.parse_args();raise SystemExit(main(a.work.resolve(),a.source.resolve(),a.original.resolve()))
