"""Append-only, offline reproduction of the recovery stop; never freezes or replays Wave 3."""
import argparse
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

RUN=Path(__file__).resolve().parents[1]
ROOT=RUN.parents[4]
parser=argparse.ArgumentParser()
parser.add_argument('--baseline-root',type=Path)
args=parser.parse_args()
product=args.baseline_root or ROOT
sys.path.insert(0,str(product/'backend'))
os.environ['ALLOW_LIVE_AI']='0'
sys.dont_write_bytecode=True
def offline(*_a,**_k):raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect=offline
socket.create_connection=offline
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def write(name,data):
    p=RUN/name
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
from app.ai.adapter3_simulation import run_typed_fact_next_route, _shared_source_gate
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions import typed_fact_next_bridge as B
from app.simulation.geometry_functions.registry import TuChoi

inputs=load(RUN/'inputs/recovery-supplementary.json')
meta={'classification':'POST_FEEDBACK_DEVELOPMENT_SAFETY_REPRODUCTION',
      'product_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=product,text=True).strip(),
      'input_sha256_lf':digest(RUN/'inputs/recovery-supplementary.json'),'live_provider_calls':0,
      'product_files_sha256_lf':{p:digest(product/p) for p in (
          'backend/app/ai/adapter3_simulation.py',
          'backend/app/simulation/geometry_functions/registry.py',
          'backend/app/simulation/geometry_functions/typed_fact_next_bridge.py')}}
rows=[]
for key in ('control','invalid_scope'):
    p=inputs[key]
    try:B.bridge(p);verdict='ACCEPTED'
    except TuChoi as e:verdict=e.code
    r3=run_typed_fact_next_route(p)
    p2={**p,'schema_version':'typed-fact-next/2'}
    r4=run_typed_fact_next_v2_route(p2)
    rows.append({'input':key,'expected':'SERVED' if key=='control' else 'REFUSED',
                 'bridge':verdict,'adapter3':{'status':r3.status,'code':r3.code},
                 'adapter4':{'status':r4.status,'code':r4.code},
                 'adapter3_source_receipt':_shared_source_gate(B.parse_typed_fact_next(p))})
receipt={**meta,'gate_A':'FAIL','cases':rows,
         'wrong_served_adapter3':sum(x['input']=='invalid_scope' and x['adapter3']['status']=='SERVED' for x in rows)}
if args.baseline_root:
    write('verification/adapter3-baseline-scope-reproduction.json',receipt)
    print('BASELINE_REPRODUCTION_CAPTURED')
    sys.exit(0)

spec=importlib.util.spec_from_file_location('recovery_dev',RUN/'tools/evaluate_development.py')
dev=importlib.util.module_from_spec(spec);spec.loader.exec_module(dev)
cases={c['id']:c for c in load(RUN/'inputs/development.json')['cases']}
originals=[]
for cid in ('DEV-NEG-08','DEV-NEG-23'):
    for canonical in (False,True):
        c=dev.canonical_f2(cases[cid]) if canonical else cases[cid]
        r=run_typed_fact_next_v2_route(c['payload'])
        originals.append({'id':cid,'canonical':canonical,'status':r.status,'code':r.code})
receipt['original_scope_negatives']=originals
write('results/scope-repair-after.json',receipt)

from app.simulation.geometry_functions.engine import _Dung
original=_Dung._construction_relation
witnesses=[]
for payload in inputs['projection_witnesses']:
    observed=[]
    def inspect(engine,call):
        value=original(engine,call)
        if call.fn=='orthogonal_projection':
            observed.append({'foot':call.args.image,'all_solid_points_placed':set('ABCDS')<=set(engine.pts),
                             'construction_relation':value})
        return value
    with patch.object(_Dung,'_construction_relation',inspect):r=run_typed_fact_next_v2_route(payload)
    foot=payload['premises'][-1]['args']['image']
    point=(F(0),F(0),F(0)) if foot=='A' else (F(2),F(0),F(0))
    signed=F(3)*point[0]+F(2)*point[2]-F(6)
    witnesses.append({'foot':foot,'exact_plane':'3*x+2*z=6','signed_incidence_numerator':str(signed),
                      'perpendicular_dot_with_BC':'4' if foot=='B' else 'NOT_APPLICABLE_OFF_PLANE',
                      'status':r.status,'code':r.code,'engine_observations':observed})
neg20=dev.evaluate_case(cases['DEV-NEG-20'])
write('results/incidence-repair-after.json',{**meta,'supplementary_witnesses':witnesses,'original_NEG20':neg20,
      'original_mechanism':'Source Gate topology contradiction: opposite nondegenerate prism bases are disjoint; not a claim that original reaches the metric engine.',
      'review_status':'PROVISIONAL_NOT_INDEPENDENTLY_REVIEWED'})
write('results/tamper-retest-after.json',{**meta,'status':'PARTIAL_GATE_A_FAIL',
      'scope_cases':originals,'mandatory_24_full_retest':'NOT_RUN_AFTER_GATE_A_STOP',
      'mutation_tests':{'remove_scope_validation':2,'replace_foreign_with_default':2,'result':'PASS',
                        'source':'verification/recovery-stop-tests.log'},
      'extra_known_solid_wrong_served':1,'wrong_served_total_for_full_24':'UNKNOWN'})
print('RECOVERY_STOP_CAPTURED: GATE_A_FAIL; NO_FREEZE_OR_FULL_REPLAY')
