"""Fresh real /4 execution; reuse byte-identical frozen scene envelopes instead of duplicating them."""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'backend'))
OLD = ROOT / 'docs/evaluation/geometry/runs/hybrid-disabled-integration'
SPEC = importlib.util.spec_from_file_location('consumer_boundary', OLD / 'check_adapter4_consumer.py')
boundary = importlib.util.module_from_spec(SPEC)
# Existing checker resolves its input from backend cwd.
SPEC.loader.exec_module(boundary)


def digest(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def main(out):
    from app.ai.hybrid_preview import classify_refusal
    network = []
    def deny(event, args):
        if event in {'socket.connect', 'socket.getaddrinfo'}:
            network.append(event)
            raise RuntimeError('OFFLINE_NETWORK_DENIED')
    sys.addaudithook(deny)
    original = OLD / 'results/adapter4-consumer-after-review/adapter4-frontend-fixtures.json'
    old = json.loads(original.read_text(encoding='utf-8'))['fixtures']
    by_id = {f['id']: (i, f) for i, f in enumerate(old)}
    fixtures, checks = [], []
    for case in boundary.load_lock():
        row, fx = boundary.check(case)
        checks.append(row)
        if fx:
            index, prior = by_id[case['id']]
            assert digest(fx) == digest(prior), 'FROZEN_FIXTURE_DIVERGENCE'
            reference = {'file': original.relative_to(ROOT).as_posix(), 'index': index,
                         'envelope_sha256': digest(fx['envelope'])}
            envelope = None
        else:
            kind = classify_refusal(row['code'], problem_text=case['payload']['problem_text'])
            reference = None
            envelope = {'status': 'unsupported', 'reason_code': row['code'], 'reason': kind.message,
                        'learner_reason': kind.message, 'failure_category': kind.failure_category,
                        'refusal_cause': kind.refusal_cause}
        fixtures.append({'id': case['id'], 'input_sha256': digest(case['payload']),
                         'expected': case['expected'], 'category': case['category'],
                         'schema_version': row['route_d']['schema_version'],
                         'route_d': deepcopy(row['route_d']), 'reference': reference, 'envelope': envelope})
    assert len(checks) == 47
    assert all((c['status'] == 'SERVED') == (c['expected'] == 'SERVE') for c in checks)
    assert all(not c.get('internal_ids_in_learner_text') and not c.get('envelope_config_errors')
               and all(c.get('oracle_answers_match', {}).values()) for c in checks)
    result = {'schema': 'adapter4_offline_consumer/1', 'classification': 'DEVELOPMENT_EVALUATION_NOT_BLIND',
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'provider_calls': 0, 'network_attempts': len(network),
              'original_fixture_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
              'fixture_reuse': '22 fresh producer results equal immutable historical fixtures; envelopes referenced by hash',
              'checks': checks, 'fixtures': fixtures}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=1); f.write('\n')
    print(json.dumps({'cases': len(checks), 'served': len(old), 'refused': len(checks)-len(old), 'network_attempts': len(network)}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('output', type=Path)
    main(p.parse_args().output.resolve())
