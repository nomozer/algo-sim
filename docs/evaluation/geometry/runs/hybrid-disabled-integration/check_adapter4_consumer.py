"""Adapter /4 → consumer-boundary check + fixtures for a separate frontend session. 0 provider calls.

Adapter /4 has no HTTP endpoint and no frontend caller. This script runs the locked Session 3 grammar set
(`hybrid-contract-v2/grammar-set.json`, DEVELOPMENT_EVALUATION_NOT_BLIND) through `run_typed_fact_next_v2_route`
and, for every SERVED scene, applies the gates the Route-D preview applies before anything reaches the frontend:
`hybrid_preview._validate_scene`, metric agreement, `compile_semantic_program_to_envelope` +
`validate_semantic_envelope_config`. It also scans learner-visible text for internal identifiers. It is a
backend-boundary check, NOT browser acceptance.

Run from `backend/`:  python <this> <NEW-results-dir>
"""
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path.cwd()))

from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402
from app.ai.hybrid_preview import PreviewInvalid, _validate_scene  # noqa: E402
from app.simulation.geometry.metric import using  # noqa: E402
from app.simulation.semantic_program.pipeline_adapter import (  # noqa: E402
    compile_semantic_program_to_envelope, validate_semantic_envelope_config,
)

GRAMMAR = Path.cwd().parent / 'docs/evaluation/geometry/runs/hybrid-contract-v2/grammar-set.json'
sys.path.insert(0, str(GRAMMAR.parent))
# Session 3's evaluator owns lock verification and the squared-coefficient oracle format.
from evaluate_grammar_set import load_lock, square_of  # noqa: E402
#: Engine-internal names that must never be shown to a learner (fresh section labels, merged derived objects,
#: qualified solid ids, refusal/reason codes).
INTERNAL = re.compile(r'derived_|_fresh|canh_ben_|::|\b[A-Z]{2,}(?:_[A-Z0-9]{2,})+\b')


#: Any snake_case token (`khoi_S_ABCD`, `kq_g_res`, `A_prime`, `g_ratio` …) — learner text is Vietnamese prose and
#: notation, never an underscore identifier. Added after independent review: the first regex missed these families.
SNAKE = re.compile(r'\b\w+_\w+\b')


def leaks(scene, envelope):
    ids = {o['id'] for o in scene['objects']} | {e.get('id') for e in scene['events'] if e.get('id')}
    hits = set()
    for t in learner_texts(scene, envelope):
        hits |= set(INTERNAL.findall(t)) | set(SNAKE.findall(t)) | {i for i in ids if i in t and '_' in i}
    return sorted(hits)


def learner_texts(scene, envelope):
    texts = [o.get(k, '') for o in scene['objects'] for k in ('label', 'display_label', 'role', 'notation')]
    texts += [e.get(k, '') for e in scene['events'] for k in ('learner_text', 'explanation', 'display_label')]
    texts += [s.get('learner_text', '') for s in scene['formation']['steps']]
    texts += [envelope.get('title', ''), envelope.get('description', '')]
    texts += [f.get('narration', '') for f in envelope['config']['frames']]
    return [t for t in texts if isinstance(t, str)]


def check(case):
    r = run_typed_fact_next_v2_route(case['payload'])
    row = {'id': case['id'], 'expected': case['expected'], 'category': case['category'],
           'status': r.status, 'code': r.code, 'route_d': r.route_d}
    if r.status != 'SERVED':
        row['refusal_has_code'] = bool(r.route_d['refusal'] and r.route_d['refusal']['code'])
        return row, None
    scene = r.scene3d
    try:
        metric = _validate_scene(json.loads(json.dumps(scene)))
        row['scene_gate'] = 'PASS'
    except PreviewInvalid as exc:
        row['scene_gate'] = str(exc)
        return row, None
    row['metric_agrees'] = metric == r.chart_metric and metric.as_json() == r.metric
    with using(metric):
        envelope = compile_semantic_program_to_envelope(r.spec)
    errors = validate_semantic_envelope_config(envelope['config'])
    row['envelope_config_errors'] = errors
    row['execution_truncated'] = envelope['config']['execution_truncated']
    envelope.update(domain='geometry', source='adapter4_offline_fixture', scene3d=scene)
    row['internal_ids_in_learner_text'] = leaks(scene, envelope)
    got = {k: str(square_of(v['coef'])) for k, v in (r.answer_exact or {}).items()}
    row['oracle_answers_match'] = {k: got.get(k) == v for k, v in case.get('answers', {}).items()}
    dump = json.dumps(scene, ensure_ascii=False)
    row['answers_bound_in_scene'] = {k: k in dump for k in r.answers}
    row['object_types'] = sorted({o['type'] for o in scene['objects']})
    row['solid_objects'] = sum(o['type'] == 'solid' for o in scene['objects'])
    row['section_closure_certified'] = [bool(s['closure_certificate']) for s in r.route_d['sections']]
    return row, {'id': case['id'], 'route_d': r.route_d, 'envelope': envelope}


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    rows, fixtures = [], []
    for case in load_lock():
        row, fx = check(case)
        rows.append(row)
        if fx:
            fixtures.append(fx)
    served = [r for r in rows if r['status'] == 'SERVED']
    summary = {
        'schema': 'adapter4_consumer_boundary/1', 'provider_calls': 0,
        'classification': 'BACKEND_BOUNDARY_CHECK_NOT_BROWSER_ACCEPTANCE; DEVELOPMENT_EVALUATION_NOT_BLIND',
        'cases': len(rows), 'served': len(served),
        'expected_serve_served': sum(r['expected'] == 'SERVE' and r['status'] == 'SERVED' for r in rows),
        'expected_refuse_refused': sum(r['expected'] != 'SERVE' and r['status'] != 'SERVED' for r in rows),
        'wrong_serves': [r['id'] for r in rows if r['expected'] != 'SERVE' and r['status'] == 'SERVED'],
        'refusals_without_code': [r['id'] for r in rows if r['status'] != 'SERVED' and not r['refusal_has_code']],
        'scene_gate_failures': [r['id'] for r in served if r.get('scene_gate') != 'PASS'],
        'metric_disagreements': [r['id'] for r in served if r.get('metric_agrees') is False],
        'envelope_failures': [r['id'] for r in served if r.get('envelope_config_errors') or r.get('execution_truncated')],
        'learner_text_internal_id_leaks': {r['id']: r['internal_ids_in_learner_text'] for r in served
                                           if r.get('internal_ids_in_learner_text')},
        'oracle_mismatches': [r['id'] for r in served if not all(r.get('oracle_answers_match', {}).values())],
        'served_with_numeric_oracle': sum(bool(r.get('oracle_answers_match')) for r in served),
        'served_construct_only_no_oracle': [r['id'] for r in served if not r.get('oracle_answers_match')],
        'served_sections_without_closure_certificate': [r['id'] for r in served
                                                        if not all(r.get('section_closure_certified', []))],
        'answers_not_bound_in_scene': {r['id']: [k for k, v in r['answers_bound_in_scene'].items() if not v]
                                       for r in served if not all(r.get('answers_bound_in_scene', {}).values())},
        'max_solid_objects_per_scene': max((r.get('solid_objects', 0) for r in served), default=0),
        'rows': rows,
    }
    for name, data in (('adapter4-consumer-boundary.json', summary), ('adapter4-frontend-fixtures.json',
                       {'schema': 'adapter4_frontend_fixtures/1', 'source_cases': str(GRAMMAR.name),
                        'note': 'Offline fixtures for a separate frontend session; not a product caller.',
                        'fixtures': fixtures})):
        with (out / name).open('x', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'rows'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
