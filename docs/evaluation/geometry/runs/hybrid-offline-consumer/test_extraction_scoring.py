"""Tool unit tests only; authored fixtures are not AI extraction samples or a blind holdout."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]


def module():
    spec = importlib.util.spec_from_file_location('extraction_scoring', Path(__file__).with_name('extraction_scoring.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def payload():
    return json.loads((ROOT/'docs/evaluation/geometry/runs/hybrid-contract-v2/grammar-set.json').read_text(encoding='utf-8'))['cases'][0]['payload']


def test_source_only_extractor_and_unknown_quality_without_curator():
    m = module(); p = payload(); seen = []
    class Extractor:
        def extract(self, text):
            seen.append(text); return deepcopy(p)
    o = m.observe(p['problem_text'], Extractor())
    assert seen == [p['problem_text']]
    assert o['metrics']['stage'] == 'SCHEMA_AND_SOURCE_VALID'
    assert o['metrics']['provider_usage'] == 'UNKNOWN'
    assert 'payload' not in m.public_receipt(o)
    assert m.score(o, None)['quality'] == 'UNKNOWN_PENDING_INDEPENDENT_ANNOTATIONS'


@pytest.mark.parametrize('axis', ['premise', 'goal', 'negation', 'conditional'])
def test_independent_rubric_scores_omissions_and_role_fidelity_after_extraction(axis):
    m = module(); p = payload()
    o = m.observe(p['problem_text'], m.replay.ReplayExtractor({p['problem_text']: p}))
    rubric = {'source_sha256': o['metrics']['source_sha256'], 'checks': [
        {'axis': axis, 'path': ['premises', 0, 'kind'], 'accepted': [p['premises'][0]['kind']]}
    ], 'allowed_premises': p['premises']}
    assert m.score(o, rubric)['axes'][axis] == {'matched': 1, 'total': 1}
    o['payload']['premises'] = []
    assert m.score(o, rubric)['axes'][axis] == {'matched': 0, 'total': 1}


def test_invented_premises_are_explicit_not_hidden_by_downstream_acceptance():
    m = module(); p = payload()
    o = m.observe(p['problem_text'], m.replay.ReplayExtractor({p['problem_text']: p}))
    rubric = {'source_sha256': o['metrics']['source_sha256'], 'checks': [], 'allowed_premises': p['premises']}
    assert m.score(o, rubric)['invented_premises'] == 0
    o['payload']['premises'].append({'kind': 'equal_length', 'args': {'line': ['A', 'S']}, 'quote': 'invented'})
    assert m.score(o, rubric)['invented_premises'] == 1


def test_source_schema_usage_failures_and_timing_are_distinct():
    m = module(); p = payload(); text = p['problem_text']
    p['problem_text'] = 'changed'
    assert m.observe(text, m.replay.ReplayExtractor({text: p}))['metrics']['stage'] == 'SOURCE_MISMATCH'
    assert m.observe(text, m.replay.ReplayExtractor({text: {'facts': []}}))['metrics']['stage'] == 'EXTRACTION_FAILURE'
    assert m.observe(text, m.replay.ReplayExtractor({}))['metrics']['code'] == 'NO_RECORDED_EXTRACTION'
    o = m.observe(text, m.replay.ReplayExtractor({text: m.ExtractionResult(payload(), {'input_tokens': 12, 'cost_usd': 0.02})}))
    assert o['metrics']['provider_usage'] == {'input_tokens': 12, 'cost_usd': 0.02}
    assert all(o['metrics']['timings'][key] >= 0 for key in ['extraction_seconds', 'source_identity_seconds', 'schema_seconds', 'total_seconds'])
    with pytest.raises(ValueError, match='RUBRIC_SOURCE_MISMATCH'):
        m.score(o, {'source_sha256': 'wrong', 'checks': []})


def test_curator_axes_and_missing_allowed_premises_fail_visibly():
    m = module(); p = payload(); o = m.observe(p['problem_text'], m.replay.ReplayExtractor({p['problem_text']: p}))
    r = m.score(o, {'source_sha256': o['metrics']['source_sha256'], 'checks': []})
    assert r['invented_premises'] == 'UNKNOWN'
    assert r['axes']['negation'] == 'UNKNOWN'


def test_extractor_faults_and_bad_usage_never_persist_error_or_raw_values():
    m = module(); text = payload()['problem_text']
    class Broken:
        def extract(self, text): raise RuntimeError('SENSITIVE_VALUE_DO_NOT_STORE')
    o = m.observe(text, Broken())
    assert o['metrics']['stage'] == 'TECHNICAL_FAILURE'
    assert 'SENSITIVE_VALUE' not in json.dumps(o)
    class BadUsage:
        def extract(self, text): return m.ExtractionResult(payload(), {'input_tokens': -1, 'raw_response': 'DO_NOT_STORE'})
    assert m.observe(text, BadUsage())['metrics']['code'] == 'USAGE_METADATA_INVALID'


def test_unexecuted_stage_times_are_not_fabricated_zeroes():
    m = module(); o = m.observe('source', m.replay.ReplayExtractor({}))
    assert o['metrics']['timings']['source_identity_seconds'] == 'NOT_EXECUTED'
    assert o['metrics']['timings']['schema_seconds'] == 'NOT_EXECUTED'


@pytest.mark.parametrize('invalid', [[], {'checks': [None]}, {'checks': [{'axis': 'premise', 'path': [], 'accepted': [True]}]}, {'checks': [], 'allowed_premises': [1]}])
def test_malformed_private_rubrics_are_controlled_failures(invalid):
    m = module(); p = payload(); o = m.observe(p['problem_text'], m.replay.ReplayExtractor({p['problem_text']: p}))
    if isinstance(invalid, dict): invalid['source_sha256'] = o['metrics']['source_sha256']
    with pytest.raises(ValueError, match='RUBRIC_'): m.score(o, invalid)
