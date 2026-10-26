from pathlib import Path
import hashlib
import json

root=Path('D:/Documents/projects/algo-sim/.superpowers/worktrees/scene3d-codex-takeover')
run=root/'docs/evaluation/geometry/runs/scene3d-codex-takeover'
suite_path=run/'visual/official-inputs/suite.json'
suite=json.loads(suite_path.read_text(encoding='utf-8'))
continued=json.loads((run/'visual/official-continuation/BROWSER_EVIDENCE.json').read_text(encoding='utf-8'))
assert continued['product_commit_sha']==suite['product_commit_sha']
assert continued['product_tree_sha']==suite['product_tree_sha']
suite_hash=hashlib.sha256(suite_path.read_bytes()).hexdigest()
assert continued['suite_manifest_sha256']==suite_hash
def failures(value,path=''):
    result=[]
    if isinstance(value,dict):
        if value.get('pass') is False and path:
            result.append(path)
        for key,item in value.items(): result.extend(failures(item,path+'.'+key if path else key))
    elif isinstance(value,list):
        for index,item in enumerate(value): result.extend(failures(item,path+f'[{index}]'))
    return result
rows=[]
for scenario in suite['scenarios']:
    name=scenario['id']
    old=run/'visual/official-authoritative'/(name+'.json')
    new=run/'visual/official-continuation'/(name+'.json')
    assert old.exists() != new.exists(), name
    path=old if old.exists() else new
    data=json.loads(path.read_text(encoding='utf-8'))
    assert isinstance(data.get('pass'),bool),name
    if new.exists(): assert data==continued['scenarios'][name]
    rows.append({'scenario':name,'pass':data['pass'],'source':str(path.relative_to(run)).replace('\\','/'),
                 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'failed_gate_paths':failures(data),
                 'process':'interrupted full run, completed scenario' if old.exists() else 'completed scoped continuation'})
result={'schema':'scene3d-official-scenario-aggregation/1','classification':'DERIVED_SUMMARY_OF_UNCHANGED_OFFICIAL_SCENARIO_RESULTS',
        'not_one_uninterrupted_suite_process':True,'product_commit':suite['product_commit_sha'],
        'product_tree_sha':suite['product_tree_sha'],'suite_sha256':suite_hash,'oracle_changes':0,'envelope_changes':0,
        'application_llm_calls':0,'total':len(rows),'passed':sum(row['pass'] for row in rows),
        'rows':rows,'note':'The five completed scenario JSON files are preserved from the interrupted full run; the same candidate, build, suite and locked oracles continued for the remaining three. This is an explicit aggregation, not a fabricated full-run receipt.'}
(run/'verification/official-scenarios.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
