"""Offline append-only boundary reproduction for the Adapter3 Owner amendment."""
import argparse,hashlib,json,os,socket,subprocess,sys
from pathlib import Path
from unittest.mock import patch

RUN=Path(__file__).resolve().parents[1];ROOT=RUN.parents[4]
sys.path.insert(0,str(ROOT/'backend'));sys.dont_write_bytecode=True
os.environ['ALLOW_LIVE_AI']='0'
def offline(*_a,**_k):raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect=offline;socket.create_connection=offline
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def write(name,data):
    with (RUN/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['red','green']);args=parser.parse_args()
from app.ai import adapter3_simulation as A
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions import typed_fact_next_bridge as B
from app.simulation.geometry_functions.registry import TuChoi
p=load(RUN/'inputs/recovery-supplementary.json')['invalid_scope']
try:B.bridge(p);bridge='ACCEPTED'
except TuChoi as e:bridge=e.code
events=[];gate=A._shared_source_gate;resolve=A._Adapter3Compiler.resolve_ref;compile_=A._Adapter3Compiler._compile_solids
def gate_spy(payload):
    try:
        result=gate(payload);events.append({'operation':'shared_source_gate','receipt':result});return result
    except TuChoi as e:
        events.append({'operation':'shared_source_gate','terminal_code':e.code});raise
def compile_spy(c):events.append({'operation':'legacy_compile_invoked'});return compile_(c)
def resolve_spy(c,ref,default_solid_id=None,context_id='ref'):
    result=resolve(c,ref,default_solid_id,context_id)
    if context_id=='p3':events.append({'operation':'resolve_ref','ref':ref,'declared_solid_id':default_solid_id,'result':result})
    return result
with patch.object(A,'_shared_source_gate',gate_spy),patch.object(A._Adapter3Compiler,'resolve_ref',resolve_spy),patch.object(A._Adapter3Compiler,'_compile_solids',compile_spy):
    r=A.run_typed_fact_next_route(p)
r4=run_typed_fact_next_v2_route({**p,'schema_version':'typed-fact-next/2'})
head=git('rev-parse','HEAD')
inventory=[]
if args.phase=='red':
    for name in git('ls-tree','-r','--name-only','a318a598',str(RUN.relative_to(ROOT)).replace('\\','/')).splitlines():
        blob=subprocess.check_output(['git','show',f'a318a598:{name}'],cwd=ROOT)
        sha=hashlib.sha256(blob.replace(b'\r\n',b'\n')).hexdigest()
        assert digest(ROOT/name)==sha,name
        inventory.append({'path':name,'sha256_lf':sha})
else:
    inventory=load(RUN/'adapter3-fallback-red.json')['prior_run_inventory']
    for row in inventory:assert digest(ROOT/row['path'])==row['sha256_lf'],row['path']
log=ROOT/f'.superpowers/f2/adapter3-{args.phase}.log'
assert 'Traceback' not in log.read_text(encoding='utf-8-sig')
outlog=f'verification/adapter3-{args.phase}-tests.log'
with (RUN/outlog).open('x',encoding='utf-8',newline='\n') as f:f.write(log.read_text(encoding='utf-8-sig'))
write(f'adapter3-fallback-{args.phase}.json',{
    'classification':'POST_FEEDBACK_DEVELOPMENT_SAFETY_REPRODUCTION','phase':args.phase,'head':head,
    'adapter3_sha256_lf':digest(ROOT/'backend/app/ai/adapter3_simulation.py'),
    'input_sha256_lf':digest(RUN/'inputs/recovery-supplementary.json'),
    'identities':{'s1':'S.ABCD','s2':'T.ABCD','offending_premise':'p3','segment':['S','A'],'declared_scope':'s2','S_owners':['s1']},
    'expected':{'status':'REFUSED','code':'SOURCE_OBJECT_MISMATCH'},'bridge_code':bridge,
    'adapter3':{'status':r.status,'code':r.code},'adapter4':{'status':r4.status,'code':r4.code},
    'boundary_events':events,'first_failing_operation_red':"resolve_ref('S', 's2', 'p3') returns S after semantic rejection",
    'prior_run_inventory':inventory,'test_log':outlog,'test_log_sha256_lf':digest(RUN/outlog),'live_provider_calls':0})
print(json.dumps({'phase':args.phase,'adapter3':r.status,'code':r.code,'prior_run_files':len(inventory)}))
