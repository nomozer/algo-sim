"""F7 continuation: rerun the locked 203 probes (vs parent probes203.json) and the 96-case scorer. Writes only f7-narrow-recovery."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

OUT = Path(__file__).resolve().parents[1]
RUN = OUT.parents[3]
ROOT = RUN.parents[4]
sys.path[:0] = [str(ROOT/'backend'),str(ROOT/'backend/tests/geometry'),str(OUT.parent/'tools')]
from observe import observe, offline
import test_scope_census_closure as F

def load(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def put(n,v):
    with (OUT/n).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(v,f,ensure_ascii=False,indent=2,default=str); f.write('\n')
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod; spec.loader.exec_module(mod); return mod

identity={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          'live_provider_calls':0,'classification':'DEVELOPMENT_SECURITY_REGRESSION'}
fixtures=SimpleNamespace(SUP=F.SUP,A3DEV=F.A3DEV,SIM=F.SIM,DEV=load(RUN/'inputs/development.json'))
rows=[]
for i in range(1,6):
    mod=module(f'locked_probes_{i}',RUN/f'unified-solid-scope-closure/pre-freeze-review/probes{i}.py')
    for name,expected,build,base in mod.probes(fixtures):
        p=build(); got=observe(p)
        rows.append({'probe':name,'expected_class':expected,'got':got,
                     'input_sha256':hashlib.sha256(json.dumps(p,sort_keys=True,ensure_ascii=False).encode()).hexdigest()})
old={c['probe']:c for c in load(OUT.parent/'probes203.json')['cases']}
bad=[r['probe'] for r in rows if r['expected_class']=='NEG' and any(r['got'][n]['status']=='SERVED' for n in ['a3','pl','a4'])]
internal=[(r['probe'],n) for r in rows for n in ['a3','pl','a4'] if r['got'][n]['status']=='EXCEPTION' or r['got'][n]['code'] in ['ADAPTER_INTERNAL_ERROR','ROUTE_INTERNAL_ERROR']]
transitions=[]
for r in rows:
    before={n:(old[r['probe']]['got'][n]['status'],old[r['probe']]['got'][n]['code']) for n in ['a3','pl','a4']}
    after={n:(r['got'][n]['status'],r['got'][n]['code']) for n in ['a3','pl','a4']}
    if before!=after: transitions.append({'probe':r['probe'],'before':before,'after':after})
put('probes203.json',{**identity,'summary':{'total':len(rows),'served_negatives':bad,'internal_results':internal},'transitions':transitions,'cases':rows})
assert len(rows)==203 and not bad and not internal
dev=module('registered_development_evaluator',RUN/'tools/evaluate_development.py')
oracle=load(RUN/'inputs/oracle.json')['cases']
rows=[dev.evaluate_case(c,oracle.get(c['id'])) for c in load(RUN/'inputs/development.json')['cases']]
put('gate-c.json',{**identity,'gate':'C','status':'PASS' if all(r['matches_expected'] for r in rows) else 'FAIL',
                  'match':sum(r['matches_expected'] for r in rows),'total':len(rows),
                  'wrong_served':sum(r['outcome']=='WRONG_SERVED' for r in rows),
                  'input_sha256_lf':sha(RUN/'inputs/development.json'),'oracle_sha256_lf':sha(RUN/'inputs/oracle.json'),'cases':rows})
print('203 probes:',len(bad),'served negatives,',len(internal),'internal,',len(transitions),'transitions')
print('Gate C:',sum(r['matches_expected'] for r in rows),'/',len(rows),'wrong served',sum(r['outcome']=='WRONG_SERVED' for r in rows))
