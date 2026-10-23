"""Preregistered development probes, not independent holdout. No product changes."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from audit_receipts import git


def verify_source(root):
    identity=git(root,'rev-parse','HEAD')
    assert identity['exit_code']==0 and identity['stdout']=='84c729e0b0df7868dfcc0a6e48cac457d7959e92', 'SOURCE_CANDIDATE_MISMATCH'
    status=git(root,'status','--porcelain','--untracked-files=no')
    assert status['exit_code']==0 and not status['stdout'], 'SOURCE_TRACKED_CHANGES'
    return identity['stdout']


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')


def prepare(root,out):
    candidate=verify_source(root)
    s1=load('s1_diagnostic',root/'docs/evaluation/geometry/runs/typedfactnext-planner-bridge/evaluate.py')
    g=load('composition_diagnostic',root/'backend/tests/geometry/test_goal_directed_function_composition.py')
    from app.simulation.geometry_functions.typed_fact_next import convert_v1_to_v2
    inputs=[];expectations={}
    for i,(shape,dims,plane,t) in enumerate([
        ('square',(F(5),),'parallel',F(2,5)),('square',(F(7),),'perpendicular',F(3,7)),
        ('rectangle',(F(5),F(7)),'parallel',F(2,5)),('rectangle',(F(7),F(11)),'perpendicular',F(3,7)),
        ('right',(F(5),F(12)),'parallel',F(2,5)),('equilateral',(F(7),),'perpendicular',F(3,7))]):
        p,meta=s1.variant(shape,dims,h=F(7),sym=False,t=t,plane=plane,residual=True)
        cid=f'section-new-{i+1}'
        inputs.append({'id':cid,'route':'canonical_v2','problem_text':p['problem_text'],
                       'payload':convert_v1_to_v2(p,route='bridge')})
        expectations[cid]={k:str(v) for k,v in s1.oracle(meta).items()}
    # Different dimensions, point support and targets; same six producer/consumer signatures.
    for i,(old_id,ask,q,*_) in enumerate(g.COMPOSITIONS[:6]):
        # Relabel the entire question and all corresponding operand slots, as a new authored problem.
        mapping={'A':'C','B':'D','C':'A','D':'B','S':'S'}
        import re
        new_ask=re.sub(r'[SABCD]',lambda m:mapping[m[0]],ask)
        new_q={k:([mapping[x] for x in v] if isinstance(v,list) else v) for k,v in q.items()}
        text,payload=g.problem(new_ask,**new_q)
        text=text.replace('cạnh 2.','cạnh 5.').replace('SA = 3.','SA = 7.')
        for f in payload['facts']:
            f['quotes']=[x.replace('cạnh 2.','cạnh 5.').replace('SA = 3.','SA = 7.') for x in f['quotes']]
            if f['id']=='f2':f['value']='5'
            if f['id']=='f4':f['value']='7'
        pts={'A':(0,0,0),'B':(5,0,0),'C':(5,5,0),'D':(0,5,0),'S':(0,0,7)}
        point=g._point('centroid',new_q['points'],pts)
        b=[pts[x] for x in new_q['points_b']]
        if i==0:want=g._oracle.area2(point,*b)
        elif i==1:want=g._oracle.len2(point,*b)
        elif i==2:want=g._oracle.dist2_plane(point,*b)
        elif i==3:want=g._oracle.dist2_line(point,*b)
        elif i==4:want=g._oracle.cos2_line_plane(pts[new_q['points_a'][0]],point,*b[:3])
        else:want=g._oracle.cos2_lines(pts[new_q['points_a'][0]],point,*b)
        cid=f'effect-new-{i+1}'
        inputs.append({'id':cid,'route':'flat_planner_diagnostic','problem_text':text,'payload':payload,
                       'signature_reused':old_id})
        expectations[cid]={'q':str(want)}
    write(out/'diagnostic-inputs.json',{'classification':'IMPLEMENTER_AUTHORED_NOT_BLIND','cases':inputs})
    write(out/'diagnostic-oracles.json',expectations)
    write(out/'diagnostic-lock.json',{'classification':'DEVELOPMENT_DIAGNOSTIC_NOT_HOLDOUT',
        'locked_utc':datetime.now(timezone.utc).isoformat(),'source_candidate':candidate,
        'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/'diagnostic-inputs.json',out/'diagnostic-oracles.json']}})
    print('LOCKED: 12 development probes, 6 canonical sections + 6 flat effect-chain probes')


def evaluate(root,out):
    candidate=verify_source(root)
    lock=json.loads((out/'diagnostic-lock.json').read_text(encoding='utf-8'))
    assert lock['source_candidate']==candidate, 'LOCK_CANDIDATE_MISMATCH'
    assert all(hashlib.sha256((out/name).read_bytes()).hexdigest()==h for name,h in lock['sha256'].items())
    from app.ai.adapter4_route import run_typed_fact_next_v2_route
    from app.ai.function_route import run_fact_route
    from tests.geometry import hybrid_compiler_benchmark as hb
    from offline_replay import failure_stage
    g=load('composition_diagnostic',root/'backend/tests/geometry/test_goal_directed_function_composition.py')
    s1=load('s1_diagnostic',root/'docs/evaluation/geometry/runs/typedfactnext-planner-bridge/evaluate.py')
    expected=json.loads((out/'diagnostic-oracles.json').read_text(encoding='utf-8'))
    rows=[]
    for c in json.loads((out/'diagnostic-inputs.json').read_text(encoding='utf-8'))['cases']:
        r=run_typed_fact_next_v2_route(c['payload']) if c['route']=='canonical_v2' else run_fact_route(c['problem_text'],c['payload'])
        got={k:str(g.value(r,k)) for k in r.answers} if r.status=='SERVED' else {}
        calls=(r.planner or {}).get('calls',[])
        rows.append({'id':c['id'],'route':c['route'],'status':r.status,'code':r.code,
                     'failure_stage':failure_stage(r.code) if r.status!='SERVED' else None,
                     'answer_squared_or_cos2':got,'exact_match':got==expected[c['id']],
                     'scene_structurally_valid':s1.scene_ok(r.scene3d)[0] if r.status=='SERVED' else None,
                     'functions':[x['fn'] for x in calls],
                     'effect_resolution_steps':[x for x in (r.planner or {}).get('trace',[]) if x.get('step')=='effect_resolution'],
                     'effect_chain_certificates':g.chain(r) if r.status=='SERVED' else []})
    benchmark=[]
    for c in hb.cases():
        for arm in ('facts','pipeline'):
            r=hb.run(c,arm)
            benchmark.append({'id':c['id'],'arm':arm,'gap':c.get('gap'),**hb.classify(c,r)})
    write(out/'planner-diagnostics.json',{'schema':'session4a_planner_diagnostics/1',
        'classification':'IMPLEMENTER_AUTHORED_DEVELOPMENT_NOT_BLIND','provider_calls':0,
        'lock_sha256':hashlib.sha256((out/'diagnostic-lock.json').read_bytes()).hexdigest(),
        'rows':rows,'exact_matches':sum(x['exact_match'] for x in rows),
        'route_b_rows':benchmark,'route_b_outcomes':dict(Counter(x['outcome'] for x in benchmark)),
        'route_b_false_refusals':[x for x in benchmark if x['outcome']=='false_refusal']})
    print(json.dumps({'exact_matches':sum(x['exact_match'] for x in rows),'rows':len(rows),
                      'route_b_false_refusals':[x for x in benchmark if x['outcome']=='false_refusal']},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','evaluate']);p.add_argument('source_root',type=Path);p.add_argument('output_dir',type=Path)
    a=p.parse_args();sys.path.insert(0,str(a.source_root/'backend'))
    (prepare if a.action=='prepare' else evaluate)(a.source_root,a.output_dir)
