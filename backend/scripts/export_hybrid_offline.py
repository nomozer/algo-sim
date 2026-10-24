"""Export fresh text-first offline integration receipts and actual product /4 wrappers. No provider calls.

The locked authored development corpus and its independent numeric oracle are reused without edits.
Neither expected dispositions nor oracle answers are passed to the extractor or product service.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))


def export_offline(out: Path) -> dict:
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    from app.ai.hybrid_preview import classify_refusal
    from app.ai.typed_fact_next_extraction import ReplayExtractor

    out.mkdir(parents=True, exist_ok=False)
    evaluator = runpy.run_path(str(ROOT / 'docs/evaluation/geometry/runs/hybrid-contract-v2/evaluate_grammar_set.py'))
    cases = evaluator['load_lock']()
    square_of = evaluator['square_of']
    policy = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})
    rows, fixtures = [], []
    classes = {'SOURCE_UNVERIFIED': 'REFUSE_SOURCE', 'MISSING_DATA': 'REFUSE_SOURCE',
               'INVALID_DATA': 'REFUSE_GEOMETRY', 'CAPABILITY': 'REFUSE_KERNEL'}
    for case in cases:
        raw = case['payload']
        source = raw['problem_text']
        result = run_hybrid_offline(source, ReplayExtractor({source: raw}), policy=policy)
        response, receipt = result.response, result.receipt
        served = response['route_d']['status'] == 'SERVED'
        code = response['envelope'].get('reason_code')
        observed = 'SERVE' if served else classes.get(classify_refusal(code).group, 'REFUSE_OTHER')
        answers = {k: str(square_of(a['coef'])) for k, a in response['route_d'].get('answer_exact', {}).items()}
        correct = served and answers == case.get('answers', {})
        row = {'id': case['id'], 'input_class': 'AUTHORED_V2_OFFLINE_REPLAY_NOT_PROVIDER_OUTPUT',
               'source_sha256': receipt['source_sha256'], 'expected': case['expected'],
               'observed': observed, 'status': response['route_d']['status'], 'code': code,
               'oracle_answers_match': correct if served else 'NOT_REACHED',
               'execution_receipt': receipt}
        rows.append(row)
        fixtures.append({'id': case['id'], **response})
    fixtures_bytes = (json.dumps({'schema': 'hybrid-offline-fixtures/1', 'fixtures': fixtures},
                                 ensure_ascii=False, indent=1) + '\n').encode('utf-8')
    wrong = [r['id'] for r in rows if r['status'] == 'SERVED'
             and (r['expected'] != 'SERVE' or r['oracle_answers_match'] is not True)]
    summary = {
        'schema': 'hybrid-offline-acceptance/1', 'classification': 'OFFLINE_REPLAY_DEVELOPMENT_NOT_BLIND',
        'source_commit': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True,
                                        encoding='utf-8', check=True).stdout.strip(),
        'corpus_sha256_lf': evaluator['LOCK_SHA'], 'cases': len(rows),
        'served': sum(r['status'] == 'SERVED' for r in rows),
        'refused': sum(r['status'] == 'REFUSED' for r in rows), 'wrong_served': wrong,
        'oracle_mismatches': [r['id'] for r in rows if r['oracle_answers_match'] is False],
        'false_refused': [r['id'] for r in rows if r['expected'] == 'SERVE' and r['status'] != 'SERVED'],
        'disposition_mismatches': [r['id'] for r in rows if r['observed'] != r['expected']],
        'refusal_codes': dict(Counter(r['code'] for r in rows if r['code'])),
        'fixtures_sha256': hashlib.sha256(fixtures_bytes).hexdigest(),
        'provider_calls': 0, 'live_extraction_quality': 'UNKNOWN', 'full_live_nl_e2e': 'NOT_MEASURED',
        'independent_holdout': 'NOT_EXECUTED', 'browser': 'NOT_EXECUTED_BY_THIS_SCRIPT', 'rows': rows,
    }
    (out / 'fixtures.json').write_bytes(fixtures_bytes)
    with (out / 'acceptance.json').open('x', encoding='utf-8') as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=1)
        stream.write('\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()

    def deny_network(event, args):
        if event in {'socket.connect', 'socket.getaddrinfo'}:
            raise RuntimeError('OFFLINE_NETWORK_DENIED')

    sys.addaudithook(deny_network)
    result = export_offline(args.out.resolve())
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, ensure_ascii=False, indent=1))
    raise SystemExit(bool(result['wrong_served'] or result['oracle_mismatches']))
