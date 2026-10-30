"""Read-only cause attribution for the eleven existing freeze-identity tests; does not freeze anything."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path.cwd()
OUT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/scripts')]
os.environ['ALLOW_LIVE_AI']='0'
os.environ['PYTHONUTF8']='1'
os.environ['PYTHONIOENCODING']='utf-8'
import freeze_evaluation_candidate as freeze
import diagnose_analyze_failure_cluster as diagnosis

pk=diagnosis.precheck()
check_keys=['SOURCE_TREE_DIRTY_ONLY_USER_FAVICON','NO_STAGED_FILES','CANDIDATE_VERIFY','CACHE_IDENTITY_VERIFY',
            'MANIFEST_LF_MATCH','GROUND_TRUTH_LF_MATCH','REGISTRY_V1_LF_MATCH','REGISTRY_V2_LF_MATCH']
checks={k:pk[k] for k in check_keys}
command=[sys.executable,'-B','backend/scripts/freeze_evaluation_candidate.py','--verify']
r=subprocess.run(command,cwd=ROOT,capture_output=True,encoding='utf-8')
measured,count=freeze.measured_system_hash()
frozen=json.loads(freeze.OUT.read_text(encoding='utf-8'))
result={'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'precheck_status':pk['PRECHECK_STATUS'],'reported_checks':checks,
        'only_reported_failing_check':[k for k,v in checks.items() if not v],
        'frozen_measured_tree_hash':frozen['measured_system']['tree_hash'],
        'current_measured_tree_hash':measured,'measured_files':count,
        'verify_exit_code':r.returncode,'verify_stdout_sha256':hashlib.sha256(r.stdout.encode()).hexdigest(),
        'cause':'CANDIDATE_MEASURED_SYSTEM_DRIFT','candidate_written':False,'live_provider_calls':0}
with (OUT/sys.argv[1]).open('x',encoding='utf-8',newline='\n') as f:
    json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(result['head'],result['only_reported_failing_check'],measured,r.returncode)
