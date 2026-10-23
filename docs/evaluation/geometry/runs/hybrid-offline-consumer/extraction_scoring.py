"""Source-only V2 extraction seam and post-extraction curator scoring. No provider transport.

CLI records contain sanitized decoded outputs, never raw responses. Curator rubrics are read only AFTER
all extractor calls, and never passed to extract(). Structural checks are curator-authored, not an NLP oracle.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
from typing import Protocol

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT/'backend'))
spec = importlib.util.spec_from_file_location('session4a_replay', Path(__file__).parents[1]/'hybrid-session4a-readiness/offline_replay.py')
replay = importlib.util.module_from_spec(spec); spec.loader.exec_module(replay)
AXES = ('premise', 'goal', 'negation', 'conditional')


class ExtractionResult:
    def __init__(self, decoded, usage=None):
        self.decoded, self.usage = decoded, usage


class Extractor(Protocol):
    def extract(self, problem_text: str) -> ExtractionResult | dict | None: ...


def observe(problem_text: str, extractor: Extractor):
    from app.simulation.geometry_functions.typed_fact_next import parse_typed_fact_next_v2, TypedFactNextValidationError
    start = time.perf_counter()
    timing = {'extraction_seconds': 'NOT_EXECUTED', 'source_identity_seconds': 'NOT_EXECUTED', 'schema_seconds': 'NOT_EXECUTED',
              'planner_seconds': 'UNKNOWN_NOT_INSTRUMENTED', 'kernel_seconds': 'UNKNOWN_NOT_INSTRUMENTED',
              'scene_seconds': 'NOT_EXECUTED', 'browser_seconds': 'NOT_EXECUTED'}
    metrics = {'track': 'NL_TO_TYPEDFACTS_V2', 'source_sha256': hashlib.sha256(problem_text.encode()).hexdigest(),
               'provider_usage': 'UNKNOWN', 'timings': timing}
    def done(stage, code=None, payload=None):
        metrics.update(stage=stage, code=code)
        timing['total_seconds'] = time.perf_counter()-start
        return {'metrics': metrics, 'payload': payload}
    try:
        raw = extractor.extract(problem_text)
    except Exception:
        timing['extraction_seconds'] = time.perf_counter()-start
        return done('TECHNICAL_FAILURE', 'EXTRACTOR_INTERNAL_ERROR')
    timing['extraction_seconds'] = time.perf_counter()-start
    if isinstance(raw, ExtractionResult):
        usage = raw.usage
        if usage is not None:
            counters = {'input_tokens', 'output_tokens', 'thinking_tokens', 'cost_usd', 'provider_latency_seconds'}
            if not isinstance(usage, dict) or any(k not in counters or type(v) not in (int, float)
                or not math.isfinite(v) or v < 0 or (k.endswith('_tokens') and type(v) is not int) for k, v in usage.items()):
                return done('TECHNICAL_FAILURE', 'USAGE_METADATA_INVALID')
            metrics['provider_usage'] = deepcopy(usage) if usage else 'UNKNOWN'
        raw = raw.decoded
    if raw is None: return done('EXTRACTION_FAILURE', 'NO_RECORDED_EXTRACTION')
    if not isinstance(raw, dict) or raw.get('schema_version') != 'typed-fact-next/2':
        return done('EXTRACTION_FAILURE', 'SCHEMA_VERSION_MISMATCH')
    t = time.perf_counter(); same = raw.get('problem_text') == problem_text
    timing['source_identity_seconds'] = time.perf_counter()-t
    if not same: return done('SOURCE_MISMATCH', 'REPLAY_SOURCE_IDENTITY_MISMATCH')
    t = time.perf_counter()
    try:
        parsed = parse_typed_fact_next_v2(raw)
    except TypedFactNextValidationError as e:
        timing['schema_seconds'] = time.perf_counter()-t
        return done('EXTRACTION_FAILURE', e.code)
    timing['schema_seconds'] = time.perf_counter()-t
    return done('SCHEMA_AND_SOURCE_VALID', payload=parsed.model_dump(mode='json'))


def public_receipt(observation):
    """Validated facts stay in memory for scoring; neither raw output nor error text is persisted."""
    return deepcopy(observation['metrics'])


def _at(value, path):
    try:
        for key in path: value = value[key]
        return value
    except (KeyError, IndexError, TypeError):
        return object()


def _premise(p):
    # Quotes are source evidence, checked by the source gate separately; preserve semantic role/negation fields.
    return json.dumps({k: v for k, v in p.items() if k != 'quote' and v is not None}, sort_keys=True, ensure_ascii=False)


def score(observation, rubric):
    result = {'track': 'NL_TO_TYPEDFACTS_V2', 'quality': 'UNKNOWN_PENDING_INDEPENDENT_ANNOTATIONS',
              'axes': {axis: 'UNKNOWN' for axis in AXES}, 'invented_premises': 'UNKNOWN'}
    if rubric is None: return result
    if not isinstance(rubric, dict): raise ValueError('RUBRIC_INVALID')
    if rubric.get('source_sha256') != observation['metrics']['source_sha256']:
        raise ValueError('RUBRIC_SOURCE_MISMATCH')
    checks = rubric.get('checks')
    if not isinstance(checks, list): raise ValueError('RUBRIC_CHECKS_REQUIRED')
    payload = observation['payload']
    for check in checks:
        if not isinstance(check, dict): raise ValueError('RUBRIC_CHECK_INVALID')
        axis = check.get('axis')
        if (axis not in AXES or not isinstance(check.get('path'), list) or not check['path']
            or any(not (isinstance(k, str) and k or type(k) is int and k >= 0) for k in check['path'])
            or not isinstance(check.get('accepted'), list) or not check['accepted']):
            raise ValueError('RUBRIC_CHECK_INVALID')
        if result['axes'][axis] == 'UNKNOWN': result['axes'][axis] = {'matched': 0, 'total': 0}
        result['axes'][axis]['total'] += 1
        result['axes'][axis]['matched'] += int(_at(payload, check['path']) in check['accepted'])
    allowed = rubric.get('allowed_premises')
    if allowed is not None:
        if not isinstance(allowed, list) or any(not isinstance(p, dict) or not isinstance(p.get('kind'), str)
            or not isinstance(p.get('args', {}), dict) for p in allowed): raise ValueError('RUBRIC_PREMISES_INVALID')
        accepted = {_premise(p) for p in allowed}
        result['invented_premises'] = sum(_premise(p) not in accepted for p in (payload or {}).get('premises', [])) if payload else 'NOT_SCORABLE'
    result['quality'] = 'CURATOR_STRUCTURAL_CHECKS_ONLY'
    return result


def main(records_file, rubric_file, output):
    def deny(event, args):
        if event in {'socket.connect', 'socket.getaddrinfo'}: raise RuntimeError('OFFLINE_NETWORK_DENIED')
    sys.addaudithook(deny)
    records = json.loads(records_file.read_text(encoding='utf-8'))
    observations = []
    for row in records:
        text = row['source_text']
        extractor = replay.ReplayExtractor({text: ExtractionResult(row.get('decoded'), row.get('usage'))})
        observations.append((row['case_id'], observe(text, extractor)))
    rubrics = json.loads(rubric_file.read_text(encoding='utf-8')) if rubric_file else {}
    result = {'schema': 'extraction_scoring/1', 'classification': 'OFFLINE_RECORDED_DECODED_OUTPUTS_NOT_NEW_AI_EXTRACTION',
              'provider_calls': 0, 'scheduled': len(records),
              'inputs': {'records_sha256': hashlib.sha256(records_file.read_bytes()).hexdigest(),
                         'rubric_sha256': hashlib.sha256(rubric_file.read_bytes()).hexdigest() if rubric_file else 'PENDING_CURATOR'},
              'rows': [{'case_id': case, 'observation': public_receipt(o), 'score': score(o, rubrics.get(case))} for case, o in observations],
              'typedfacts_to_scene3d': 'SEPARATE_TRACK', 'full_nl_to_scene3d': 'NOT_MEASURED'}
    with output.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--records', type=Path, required=True)
    p.add_argument('--rubrics', type=Path); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); main(a.records, a.rubrics, a.output)
