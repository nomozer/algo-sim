"""Fresh Adapter /4 export after the section display identity fix (0 model calls, network denied).

Runs the 47 locked `hybrid-contract-v2/grammar-set.json` cases through the existing consumer boundary checker
(`hybrid-disabled-integration/check_adapter4_consumer.py`), writes NEW files only (`open(..., 'x')`), and compares
with the historical served envelopes: learner-facing names may differ, everything else must not.

Outputs (in `<out>`): `adapter4-fixtures.json` (served envelopes), `fixtures.json` (same shape as
`hybrid-offline-consumer/results/fixtures.json`, for the browser harnesses) and `before-after.json`.

Run from `backend/`: python ../docs/evaluation/geometry/runs/scene3d-plane-section-display-identity/export_fixtures.py <out>
"""
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
SPEC.loader.exec_module(boundary)
HISTORY = OLD / 'results/adapter4-consumer-after-review/adapter4-frontend-fixtures.json'
SESSION5 = ROOT / 'docs/evaluation/geometry/runs/hybrid-offline-consumer/results/fixtures.json'
#: Learner-facing name fields. Every other field of every object, event and step must be byte-equal to history.
NAME_FIELDS = {'label', 'display_label', 'reference', 'notation', 'role', 'learner_text', 'explanation'}


def digest(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def name_diff(old, new, path=''):
    """(path, before, after) for differing name fields; raises if anything else differs."""
    if isinstance(old, dict) and isinstance(new, dict):
        if set(old) != set(new):
            raise AssertionError(f'keys differ at {path}: {sorted(set(old) ^ set(new))}')
        out = []
        for k in old:
            if k in NAME_FIELDS and old[k] != new[k]:
                out.append((f'{path}.{k}', old[k], new[k]))
            elif k == 'formula' and isinstance(old[k], dict) and old[k].get('text') != new[k].get('text'):
                if {**old[k], 'text': None} != {**new[k], 'text': None}:
                    raise AssertionError(f'formula differs beyond text at {path}')
                out.append((f'{path}.formula.text', old[k]['text'], new[k]['text']))
            else:
                out += name_diff(old[k], new[k], f'{path}.{k}')
        return out
    if isinstance(old, list) and isinstance(new, list):
        if len(old) != len(new):
            raise AssertionError(f'length differs at {path}')
        return [d for i, (a, b) in enumerate(zip(old, new))
                for d in name_diff(a, b, f"{path}[{a.get('id', i) if isinstance(a, dict) else i}]")]
    if old != new:
        raise AssertionError(f'non-name value differs at {path}: {str(old)[:80]} -> {str(new)[:80]}')
    return []


def main(out):
    from app.ai.hybrid_preview import classify_refusal
    network = []

    def deny(event, args):
        if event in {'socket.connect', 'socket.getaddrinfo'}:
            network.append(event)
            raise RuntimeError('OFFLINE_NETWORK_DENIED')
    sys.addaudithook(deny)
    history = {f['id']: f for f in json.loads(HISTORY.read_text(encoding='utf-8'))['fixtures']}
    s5 = {f['id']: f for f in json.loads(SESSION5.read_text(encoding='utf-8'))['fixtures']}
    served, rows, fixtures, compare = [], [], [], []
    for case in boundary.load_lock():
        row, fx = boundary.check(case)
        rows.append(row)
        if fx:
            served.append(fx)
            old = history[case['id']]
            assert row['route_d']['sections'] == old['route_d']['sections'], case['id']
            changes = name_diff(old['envelope'], fx['envelope'], 'envelope')
            compare.append({'id': case['id'], 'route_d_equal': row['route_d'] == old['route_d'],
                            'name_changes': [{'path': p, 'before': a, 'after': b} for p, a, b in changes]})
        else:
            assert row['route_d'] == s5[case['id']]['route_d'], f"refusal changed: {case['id']}"
    out.mkdir(parents=True, exist_ok=False)
    bundle = out / 'adapter4-fixtures.json'
    with bundle.open('x', encoding='utf-8') as f:
        json.dump({'schema': 'adapter4_frontend_fixtures/1', 'fixtures': served}, f, ensure_ascii=False, indent=1)
        f.write('\n')
    by_id = {fx['id']: i for i, fx in enumerate(served)}
    for case, row in zip(boundary.load_lock(), rows):
        if case['id'] in by_id:
            reference = {'file': bundle.relative_to(ROOT).as_posix(), 'index': by_id[case['id']],
                         'envelope_sha256': digest(served[by_id[case['id']]]['envelope'])}
            envelope = None
        else:
            kind = classify_refusal(row['code'], problem_text=case['payload']['problem_text'])
            reference = None
            envelope = {'status': 'unsupported', 'reason_code': row['code'], 'reason': kind.message,
                        'learner_reason': kind.message, 'failure_category': kind.failure_category,
                        'refusal_cause': kind.refusal_cause}
            assert envelope == s5[case['id']]['envelope'], f"refusal envelope changed: {case['id']}"
        fixtures.append({'id': case['id'], 'input_sha256': digest(case['payload']), 'expected': case['expected'],
                         'category': case['category'], 'schema_version': row['route_d']['schema_version'],
                         'route_d': deepcopy(row['route_d']), 'reference': reference, 'envelope': envelope})
    assert len(rows) == 47 and len(served) == 22
    assert all((r['status'] == 'SERVED') == (r['expected'] == 'SERVE') for r in rows)
    assert all(not r.get('internal_ids_in_learner_text') and not r.get('envelope_config_errors')
               and all(r.get('oracle_answers_match', {}).values()) for r in rows)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    meta = {'source_commit': head, 'provider_calls': 0, 'network_attempts': len(network),
            'classification': 'DEVELOPMENT_EVALUATION_NOT_BLIND'}
    with (out / 'fixtures.json').open('x', encoding='utf-8') as f:
        json.dump({'schema': 'adapter4_offline_consumer/1', **meta,
                   'original_fixture_sha256': hashlib.sha256(bundle.read_bytes()).hexdigest(),
                   'fixture_reuse': 'fresh export after the section display identity fix; history kept unchanged',
                   'checks': rows, 'fixtures': fixtures}, f, ensure_ascii=False, indent=1)
        f.write('\n')
    with (out / 'before-after.json').open('x', encoding='utf-8') as f:
        json.dump({'schema': 'adapter4_name_diff/1', **meta, 'before': HISTORY.relative_to(ROOT).as_posix(),
                   'rule': 'only label/display_label/reference/notation/role/learner_text/explanation/formula.text '
                           'may differ; every other value, key and list length is asserted equal',
                   'refusals_equal_session5': 47 - len(served), 'served': compare}, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(json.dumps({'cases': len(rows), 'served': len(served), 'changed_scenes': sum(bool(c['name_changes'])
                      for c in compare), 'name_changes': sum(len(c['name_changes']) for c in compare),
                      'network_attempts': len(network)}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('output', type=Path)
    main(p.parse_args().output.resolve())
