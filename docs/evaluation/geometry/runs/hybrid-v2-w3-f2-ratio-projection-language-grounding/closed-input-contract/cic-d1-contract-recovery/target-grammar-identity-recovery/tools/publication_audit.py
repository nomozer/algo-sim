"""Read the exact proposed historical blobs; publish metadata only, never log contents or credentials."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[2].parents[4]
spec=importlib.util.spec_from_file_location('publication_scanner',ROOT/'backend/scripts/check_publication_safety.py')
scanner=importlib.util.module_from_spec(spec); spec.loader.exec_module(scanner)
proposal=json.loads((OUT.parent/'publication-exception-proposal.json').read_text(encoding='utf-8'))
entries=[]
for e in proposal['entries']:
    raw=subprocess.check_output(['git','cat-file','blob',e['blob']],cwd=ROOT)
    digest=hashlib.sha256(raw).hexdigest()
    assert digest==e['sha256'] and len(raw)==e['bytes']
    path_blob=subprocess.check_output(['git','rev-parse',e['first_commit']+':'+e['path']],cwd=ROOT,text=True).strip()
    assert path_blob==e['blob']
    text=raw.decode('utf-8')
    paths=re.findall(r'[A-Za-z]:[\\/][^\s"<>]+',text)
    findings=scanner.findings_in(raw)
    entries.append({'historical_commit':e['first_commit'],'path':e['path'],'blob':e['blob'],
        'sha256_bytes':digest,'bytes':len(raw),'matches_proposal':True,
        'traceback_type':'pytest unhandled subprocess reader-thread exception; Windows cp1252 UnicodeDecodeError',
        'traceback_frame_basenames':sorted(set(re.findall(r'File "[^"\r\n]*[/\\]([^/\\"\r\n]+)", line',text))),
        'product_exception_stack_present':False,
        'scanner_findings':[{'rule':rule,'line':line} for rule,line in findings],
        'credential_rule_findings':[{'rule':rule,'line':line} for rule,line in findings if rule!='PY_TRACEBACK'],
        'private_absolute_path_occurrences':len(paths),'private_paths_present':bool(paths),
        'profile_username_in_paths':any(re.search(r'(?i)[/\\]users[/\\]',s) for s in paths),
        'other_sensitive_fields':'No credential, token, private key, email or personal payload observed in contextual review; regex scan alone is not proof of absence.',
        'narrowness':'Exact path/blob/content digest and PY_TRACEBACK rule are narrow; no wildcard exception proposed.',
        'technical_justification':'Low-risk standard-library diagnostic, not model output; proposal omits local-profile and repository-path disclosure.',
        'recommendation':'Keep pending. Owner may consider an exact-blob exception only after explicitly accepting local path/profile disclosure; do not approve the proposal under a claim of no private paths.',
        'status':'BLOCKED_PENDING_OWNER_DECISION'})
result={'audit':'READ_ONLY_HISTORICAL_BLOBS','history_modified':False,'registry_modified':False,
        'publication_status':'BLOCKED_PENDING_OWNER_DECISION','entries':entries,
        'without_history_rewrite':'An Owner-authorized exact exception can resolve the scanner gate but does not redact historical paths. A separately authorized sanitized source export can omit history; it is not a pass for publication of this branch history.',
        'full_history_without_path_disclosure':'NOT_POSSIBLE_WITH_CURRENT_BLOBS',
        'live_provider_calls':0}
with (OUT/'publication-risk.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print('read-only audit:',len(entries),'exact blobs;',sum(len(e['scanner_findings']) for e in entries),'scanner findings; private paths present in both')
