"""Append-only gate receipts and post-feedback replay; never invokes an old report writer."""
import argparse,hashlib,importlib.util,json,os,socket,subprocess,sys
from pathlib import Path

RUN=Path(__file__).resolve().parents[1];ROOT=RUN.parents[4]
sys.path.insert(0,str(ROOT/'backend'));sys.dont_write_bytecode=True
os.environ['ALLOW_LIVE_AI']='0'
def offline(*_a,**_k):raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect=offline;socket.create_connection=offline
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def write(name,data):
    p=RUN/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def head():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
def copy_log(src,dst):
    text=(ROOT/src).read_text(encoding='utf-8-sig');assert 'Traceback' not in text
    with (RUN/dst).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['gates','replay']);args=parser.parse_args()
dev=module('adapter3_locked_development',RUN/'tools/evaluate_development.py')
fz=module('adapter3_freeze_identity',ROOT/'backend/scripts/freeze_evaluation_candidate.py')
identity={'head':head(),'product_commit':fz.product_commit(),'measured_system_hash':fz.measured_system_hash(),
          'live_provider_calls':0,'classification':'POST_FEEDBACK_DEVELOPMENT_REGRESSION'}
if args.phase=='gates':
    doc=load(RUN/'inputs/development.json');oracle=load(RUN/'inputs/oracle.json')['cases']
    rows=[dev.evaluate_case(c,oracle.get(c['id'])) for c in doc['cases']]
    assert len(rows)==96 and all(r['matches_expected'] for r in rows)
    slices={s:{'total':len(cs:=[r for r in rows if r['slice']==s]),
               'served_correct':sum(r['outcome']=='SERVED_CORRECT' for r in cs),
               'refused':sum(not r['served'] for r in cs),
               'locked_code_match':sum(r['matches_expected'] for r in cs)} for s in sorted({r['slice'] for r in rows})}
    fixtures=load(ROOT/'.superpowers/f2/adapter3-41-fixtures.json')
    assert fixtures['verified']==41 and fixtures['problems']==[]
    copy_log('.superpowers/f2/adapter3-final-compat.log','verification/adapter3-final-compat-tests.log')
    assert '619 passed, 1 deselected, 6 xfailed' in (RUN/'verification/adapter3-final-compat-tests.log').read_text(encoding='utf-8')
    write('verification/adapter3-41-fixtures.json',fixtures)
    write('adapter3-compatibility-results.json',{**identity,'status':'PASS_BEHAVIORAL_GATES',
          'tests':{'passed':619,'failed':0,'xfailed':6,'deselected':1,
                   'deferred':'live product vs old W3-F1 freeze, must pass after new freeze in Full T3'},
          'slices':slices,'cases':rows,'fixtures_verified':41,
          'qualified_constructed_point':'same exact points/trace as unqualified; unknown Z still refuses',
          'versions':{'registry':'geometry-functions/21','planner':'geometry-fact-planner/18',
             'engine':'geometry-function-engine/14','adapter3':'hybrid-simulation-adapter/3',
             'bridge':'typed-fact-next-bridge/1 and /2; validated scope receipt /1','cache':'130'},
          'version_decision':'Registry /21 identifies new language; Adapter/Bridge tags retain compatible public contracts. Restored invalid-input rejection is not a new schema. Measured product hash disambiguates implementation; no unchanged-version identity is claimed as an unchanged product tree.',
          'cache_decision':'No bump: Adapter3 and TypedFactNext planner routes are offline research, not wired into /api/analyze cached LLM_ONLY pipeline; Hybrid preview identity includes Registry /21. All 41 endpoint fixtures reproduce modulo declared identity deltas; source fingerprint explicitly differs.',
          'log_sha256_lf':digest(RUN/'verification/adapter3-final-compat-tests.log')})
    write('adapter3-fallback-mutation-results.json',{**identity,'status':'PASS','killed':4,
          'mutants':['remove_terminal_guard','remove_scope_guard','replace_scope_with_default','allow_global_lookup'],
          'terminal_oracle':'no legacy compilation after semantic Bridge refusal, even with scoped resolver defense',
          'resolver_oracle':'wrong-scope S under s2 must raise SOURCE_OBJECT_MISMATCH',
          'method':'mutate actual function source in isolated pytest monkeypatch namespace; restore after each test',
          'test_source_sha256_lf':digest(ROOT/'backend/tests/geometry/test_adapter3_fallback_safety.py'),
          'passing_run':'verification/adapter3-final-compat-tests.log'})
    write('final-safety-gates.json',{**identity,'A':'PASS','B':'PASS','C':'PASS','D':'PASS',
          'wrong_served_locked_96':sum(r['outcome']=='WRONG_SERVED' for r in rows),
          'gate_B_review':'verification/gate-b-independent-review.md',
          'gate_B_review_sha256_lf':digest(RUN/'verification/gate-b-independent-review.md'),
          'compatibility_sha256_lf':digest(RUN/'adapter3-compatibility-results.json'),
          'mutation_sha256_lf':digest(RUN/'adapter3-fallback-mutation-results.json'),
          'release_status':'NOT_YET_READY_PENDING_FULL_REPLAY_T2_FREEZE_T3_FINAL_REVIEW'})
    print(json.dumps({'gates':'A-D PASS','slices':slices,'fixtures':41}))
else:
    gates=load(RUN/'final-safety-gates.json');assert all(gates[k]=='PASS' for k in 'ABCD')
    assert gates['measured_system_hash']==list(fz.measured_system_hash())
    f1=module('adapter3_wave3_replay',dev.F1/'tools/build_and_evaluate_w3_f1.py')
    # The historical helper pins its original worktree path; use the identical committed evidence in this checkout.
    f1.WAVE3_WORKTREE=dev.HIST
    result=f1.evaluate_wave3_post_feedback_regression()
    result['task']='HYBRID_V2_W3_F2_ADAPTER3_SEMANTIC_FALLBACK_SAFETY_HARDENING'
    result['identity']=identity
    baseline=load(dev.F1/'results/wave3-post-feedback-regression.json')
    result['authoritative_W3_F1_baseline']=baseline['post_feedback_regression_summary']
    old={r['id']:r for r in baseline['cases']}
    result['transitions_from_W3_F1']=[{'id':r['id'],'before_outcome':old[r['id']]['outcome'],
          'before_code':old[r['id']]['code'],'after_outcome':r['outcome'],'after_code':r['code']} for r in result['cases']
          if (r['outcome'],r['code'])!=(old[r['id']]['outcome'],old[r['id']]['code'])]
    result['original_A06']={'classification':'F2_LANGUAGE_GROUNDING_RESOLVED_BUT_DOWNSTREAM_RADICAL_LIMIT_REMAINS',
                           'actual':next(r for r in result['cases'] if r['id']=='W3-A06')}
    write('wave3-post-feedback-regression-after-adapter3.json',result)
    print(json.dumps(result['post_feedback_regression_summary']))
