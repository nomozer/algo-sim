"""Independently reproduce F7 on the caller's source tree; persist no raw traceback."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from observe import OUT
from app.ai.adapter3_simulation import run_typed_fact_next_route

cases=json.loads((OUT/'cases.json').read_text(encoding='utf-8'))
rows=[]
for name in ['V.radius.solid','V.radius.notation','V.lateral_area.solid','V.lateral_area.notation']:
    p=cases[name]['payload']; r=run_typed_fact_next_route(p)
    reason=r.reason or ''
    rows.append({'case':name,'status':r.status,'code':r.code,
                 'error_type':'KeyError' if 'KeyError' in reason else 'UNKNOWN',
                 'missing_key':'ask2' if 'ask2' in reason else 'UNKNOWN',
                 'reason_sha256':hashlib.sha256(reason.encode()).hexdigest()})
result={'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'live_provider_calls':0,'finding':'F7_UNRESOLVED','cases':rows}
with (OUT/sys.argv[1]).open('x',encoding='utf-8',newline='\n') as f:
    json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(result['head'],[(r['case'],r['code'],r['error_type'],r['missing_key']) for r in rows])
