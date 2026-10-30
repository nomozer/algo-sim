"""Record a finished clean-source backend run as a digest, never commit raw pytest diagnostics."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[2].parents[4]
SCRATCH=ROOT/'.superpowers/target-grammar-identity-recovery'
COMPAT=Path(sys.argv[1])
raw=(SCRATCH/'full-backend.log').read_bytes(); text=raw.decode('utf-8-sig')
baseline=(SCRATCH/'baseline11.log').read_bytes(); btext=baseline.decode('utf-8-sig')
summary=re.findall(r'^(\d+ failed, .+? in [^\r\n]+)',text,re.M)[-1]
failures=sorted(set(re.findall(r'^FAILED (\S+)',text,re.M)))
old=sorted(set(re.findall(r'^FAILED (\S+)',btext,re.M)))
same=failures==old and len(failures)==11
assert not subprocess.check_output(['git','status','--porcelain'],cwd=COMPAT,text=True).strip()
cause=json.loads((OUT/'freeze-cause-current.json').read_text(encoding='utf-8'))
assert cause['only_reported_failing_check']==['CANDIDATE_VERIFY']
evidence={'gate':'D','source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=COMPAT,text=True).strip(),
    'product_commit':'6a09c06afcb247b71a5af11a49aa2dc6a31d3f46',
    'compatibility':'PRE_FREEZE_COMPATIBILITY_PASS' if same else 'FAIL',
    'overall_pass':False,'publication':'BLOCKED_PENDING_OWNER_DECISION',
    'full_backend':{'command':'python -B -m pytest -p no:cacheprovider --basetemp D:/Documents/projects/algo-sim/.superpowers/target-grammar-identity-full-temp -q --tb=short -rA',
        'cwd':str(COMPAT/'backend'),'exit_code':1,'summary':summary,'tree_clean_before':True,'tree_clean_after':True,
        'raw_log_local_only':'.superpowers/target-grammar-identity-recovery/full-backend.log',
        'raw_log_sha256_bytes':hashlib.sha256(raw).hexdigest(),
        'PENDING_NEW_FREEZE':failures if same else [],'unexplained_failures':sorted(set(failures)-set(old)),
        'warning':'This is backend compatibility, not Full T3 and not an overall Gate D PASS.'},
    'baseline_11':{'head':'5e44d5da434b1d1a8fd98a0f1f4527f40de3c6ed','failed_nodes_match':same,
        'raw_log_sha256_bytes':hashlib.sha256(baseline).hexdigest(),
        'cause_receipts':['freeze-cause-current.json','freeze-cause-baseline.json'],
        'cause_by_group':{'diagnosis_and_branch_precheck_6':'candidate verification alone fails; all other reported checks true',
            'docs_IA_and_telemetry_2':'freeze --verify refuses stale measured-system identity',
            'hybrid_backend_integration_1':'measured-system tuple differs from frozen tuple',
            'thesis_acceptance_1':'declared divergence hash is stale',
            'semantic_candidate_1':'live measured-system hash differs from frozen manifest'}},
    'locked_v2_targeted':'locked-v2.json (six explicitly listed files, 232 tests; all included again in full backend)',
    'cache':'MATCH 130, cache.json','fixtures':'41/41, fixtures41.json',
    'known_F7':'UNRESOLVED; separate from compatibility suite pass, not hidden by baseline attribution',
    'live_provider_calls':0}
with (OUT/'gate-d.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump(evidence,f,ensure_ascii=False,indent=2);f.write('\n')
print(evidence['compatibility'],summary,'publication BLOCKED, overall_pass false')
