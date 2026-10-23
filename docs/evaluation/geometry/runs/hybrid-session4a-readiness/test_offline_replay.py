import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest


def module():
    p = Path(__file__).with_name('offline_replay.py')
    assert p.exists(), 'offline replay boundary is not implemented'
    spec = importlib.util.spec_from_file_location('offline_replay', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_old_flat_outputs_do_not_silently_become_v2():
    m=module()
    r=m.replay_one('source', m.ReplayExtractor({'source': {'facts': []}}))
    assert r['stage'] == 'EXTRACTION_FAILURE'
    assert r['code'] == 'SCHEMA_VERSION_MISMATCH'
    assert r['renderer'] == 'NOT_REACHED'


def test_source_identity_is_exact_and_never_reauthored():
    m=module()
    r=m.replay_one('source',m.ReplayExtractor({'source': {'schema_version':'typed-fact-next/2','problem_text':'different'}}))
    assert (r['stage'],r['code']) == ('SOURCE_MISMATCH','REPLAY_SOURCE_IDENTITY_MISMATCH')


def test_missing_extraction_is_not_missing_premise():
    m=module()
    r=m.replay_one('source',m.ReplayExtractor({}))
    assert r['stage'] == 'EXTRACTION_FAILURE'
    assert r['code'] == 'NO_RECORDED_EXTRACTION'


@pytest.mark.parametrize('code,stage',[
    ('SOURCE_OBJECT_MISMATCH','SOURCE_MISMATCH'),('MISSING_DIMENSION','MISSING_PREMISE'),
    ('IR_MEMORY_BUDGET_EXCEEDED','PLANNER_LIMITATION'),('SECTION_BOUNDARY_INCOMPLETE','KERNEL_REFUSAL'),
    ('ROUTE_INTERNAL_ERROR','TECHNICAL_FAILURE'),('SCENE_BUILD_FAILED','SCENE_VALIDATION_FAILURE'),
    ('UNREGISTERED_CODE','UNCLASSIFIED_REFUSAL')])
def test_refusal_attribution_keeps_technical_and_unknown_failures_visible(code,stage):
    assert module().failure_stage(code) == stage


def test_canonical_fixture_reaches_verified_scene_without_claiming_browser_rendering():
    m=module()
    root=Path(os.environ['SESSION4A_SOURCE_ROOT'])
    c=json.loads((root/'docs/evaluation/geometry/runs/hybrid-contract-v2/grammar-set.json').read_text(encoding='utf-8'))['cases'][0]
    payload=c['payload']; text=payload['problem_text']
    r=m.replay_one(text,m.ReplayExtractor({text:payload}))
    assert r['stage'] == 'VERIFIED_SCENE'
    assert r['source_authority'] == 'registry.kiem_nguon'
    assert r['renderer'] == 'UNKNOWN_NOT_EXECUTED'
    assert r['provider_tokens'] == 'UNKNOWN'


def test_archive_reader_uses_verbatim_source_text_and_omits_raw_output(tmp_path):
    m=module()
    run=tmp_path/'docs/evaluation/geometry/runs/independent-nlu-extraction-evaluation'
    (run/'inputs/corpus-authoring').mkdir(parents=True)
    (run/'results/live-locked').mkdir(parents=True)
    (run/'inputs/corpus-authoring/corpus.json').write_text(json.dumps({'cases':[{'id':'x','source_text':'original'}]}),encoding='utf-8')
    (run/'results/live-locked/manifest.json').write_text(json.dumps({'rows':[{'case_id':'x','facts':[], 'raw_response':'DO_NOT_COPY'}]}),encoding='utf-8')
    out=tmp_path/'result.json'
    m.main(Path(os.environ['SESSION4A_SOURCE_ROOT']),tmp_path,out)
    result=json.loads(out.read_text(encoding='utf-8'))
    assert result['archived_outputs']['stages'] == {'EXTRACTION_FAILURE':1}
    assert 'DO_NOT_COPY' not in out.read_text(encoding='utf-8')
