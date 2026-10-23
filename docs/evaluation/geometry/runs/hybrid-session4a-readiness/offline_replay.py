"""Local extraction-output replay; no provider transport, prompts, answers or oracle inputs.

Run with --source-root pointing to the clean pinned Session 3 worktree. Read only the
sanitized `facts` field of archived manifests; never copy raw model responses.
"""
from collections import Counter
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


class ReplayExtractor:
    """Provider-independent seam: extract(problem_text) -> recorded decoded object or None."""
    def __init__(self, outputs):
        self.outputs = outputs

    def extract(self, problem_text):
        return deepcopy(self.outputs.get(problem_text))


def failure_stage(code):
    from app.ai.hybrid_preview import classify_refusal
    if code in {'SCENE_BUILD_FAILED', 'PREVIEW_RESULT_INVALID', 'PREVIEW_VALIDATION_FAILED'}:
        return 'SCENE_VALIDATION_FAILURE'
    if code.endswith('_INTERNAL_ERROR') or code in {'ENGINE_EXECUTION_FAILED', 'ENGINE_IR_INVALID', 'ENGINE_SELF_CHECK_FAILED'}:
        return 'TECHNICAL_FAILURE'
    group = classify_refusal(code).group
    return {'SOURCE_UNVERIFIED': 'SOURCE_MISMATCH', 'MISSING_DATA': 'MISSING_PREMISE',
            'CAPABILITY': 'PLANNER_LIMITATION', 'INVALID_DATA': 'KERNEL_REFUSAL',
            'EXTRACTION_FAILED': 'EXTRACTION_FAILURE'}.get(group, 'UNCLASSIFIED_REFUSAL')


def replay_one(problem_text, extractor):
    from app.ai.adapter4_route import run_typed_fact_next_v2_route
    from app.ai.hybrid_preview import PreviewInvalid, _validate_scene
    from app.simulation.geometry_functions.typed_fact_next import parse_typed_fact_next_v2, TypedFactNextValidationError
    start=time.perf_counter()
    row={'stage':None,'code':None,'provider_calls':0,'provider_tokens':'UNKNOWN',
         'provider_latency_seconds':'UNKNOWN','provider_cost_usd':'UNKNOWN','renderer':'NOT_REACHED'}
    def done(stage,code=None):
        row.update(stage=stage,code=code,offline_seconds=round(time.perf_counter()-start,6))
        return row
    raw=extractor.extract(problem_text)
    if raw is None:
        return done('EXTRACTION_FAILURE','NO_RECORDED_EXTRACTION')
    if not isinstance(raw,dict) or raw.get('schema_version') != 'typed-fact-next/2':
        return done('EXTRACTION_FAILURE','SCHEMA_VERSION_MISMATCH')
    if raw.get('problem_text') != problem_text:
        return done('SOURCE_MISMATCH','REPLAY_SOURCE_IDENTITY_MISMATCH')
    try:
        parse_typed_fact_next_v2(raw)
    except TypedFactNextValidationError as e:
        return done('EXTRACTION_FAILURE',e.code)
    r=run_typed_fact_next_v2_route(raw)
    if r.status != 'SERVED':
        return done(failure_stage(r.code),r.code)
    row['source_authority']=(r.route_d or {}).get('source_verification',{}).get('authority')
    if row['source_authority'] != 'registry.kiem_nguon':
        return done('SOURCE_MISMATCH','SOURCE_AUTHORITY_MISSING')
    try:
        _validate_scene(deepcopy(r.scene3d))
    except PreviewInvalid:
        return done('SCENE_VALIDATION_FAILURE','SCENE_VALIDATION_FAILED')
    row['renderer']='UNKNOWN_NOT_EXECUTED'
    return done('VERIFIED_SCENE')


def main(source_root, archive_root, output):
    sys.path.insert(0,str(source_root/'backend'))
    network_attempts=[]
    def deny_network(event,args):
        if event in {'socket.connect','socket.getaddrinfo'}:
            network_attempts.append(event)
            raise RuntimeError('OFFLINE_NETWORK_DENIED')
    sys.addaudithook(deny_network)
    run=archive_root/'docs/evaluation/geometry/runs/independent-nlu-extraction-evaluation'
    corpus_file=run/'inputs/corpus-authoring/corpus.json'
    archive_file=run/'results/live-locked/manifest.json'
    corpus={c['id']:c for c in json.loads(corpus_file.read_text(encoding='utf-8'))['cases']}
    archive=json.loads(archive_file.read_text(encoding='utf-8'))
    rows=[]
    for old in archive['rows']:
        case=corpus[old['case_id']]
        text=case['source_text']
        # `facts` are already parsed/sanitized in the authorized historical archive.
        raw={'facts':old['facts']} if old.get('facts') is not None else None
        r=replay_one(text,ReplayExtractor({text:raw}))
        rows.append({'case_id':old['case_id'],'input_class':'ARCHIVED_PROVIDER_FLAT_OUTPUT',
                     'source_text_sha256':hashlib.sha256(text.encode()).hexdigest(),
                     'archived_parse_code':old.get('parse_code'),**r})
    # Authored typed fixtures exercise only the seam, never extraction accuracy.
    fixtures=source_root/'docs/evaluation/geometry/runs/hybrid-contract-v2/grammar-set.json'
    seam=[]
    for c in json.loads(fixtures.read_text(encoding='utf-8'))['cases']:
        text=c['payload']['problem_text']
        seam.append({'case_id':c['id'],'input_class':'AUTHORED_TYPEDFACTS_NOT_PROVIDER_OUTPUT',
                     **replay_one(text,ReplayExtractor({text:c['payload']}))})
    result={'schema':'session4a_offline_replay/1','classification':'REPLAY_DIAGNOSTIC_NOT_NLU_EVALUATION',
            'provider_calls':0,'network_attempts':len(network_attempts),
            'inputs':{str(p.relative_to(archive_root) if p.is_relative_to(archive_root) else p):
                      hashlib.sha256(p.read_bytes()).hexdigest() for p in (corpus_file,archive_file,fixtures)},
            'archived_outputs':{'rows':rows,'stages':dict(Counter(r['stage'] for r in rows))},
            'authored_seam':{'rows':seam,'stages':dict(Counter(r['stage'] for r in seam))},
            'new_v2_extraction_quality':'UNKNOWN_NO_V2_PROVIDER_OUTPUTS', 'browser_rendering':'UNKNOWN_NOT_EXECUTED'}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:v['stages'] for k,v in result.items() if k in ('archived_outputs','authored_seam')},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--archive-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.source_root.resolve(),a.archive_root.resolve(),a.output.resolve())
