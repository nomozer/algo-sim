"""Reuse offline product scenes; never generate geometry or call providers here."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[4]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT / 'backend/scripts'))
from app.ai.pipeline import _dung_scene3d
from app.simulation.semantic_program.route import verify_and_compile


def load_module(rel):
    spec = importlib.util.spec_from_file_location('visual_' + Path(rel).stem + str(len(sys.modules)), ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


old = 'docs/evaluation/geometry/runs/geometric-visual-correctness-framing/demos/audit_scenes.json'
rows = json.loads((ROOT / old).read_text(encoding='utf-8'))
for row in rows:
    row['source'] = old
samples = json.loads((ROOT / 'frontend/src/data/geometry-samples.json').read_text(encoding='utf-8'))['samples']
for sample in samples:
    if sample['envelope'].get('scene3d'):
        rows.append(dict(id='public-' + sample['id'], served=True, category=sample['envelope']['title'],
                         problem_text=sample['problemText'], scene=sample['envelope']['scene3d'],
                         source='frontend/src/data/geometry-samples.json#' + sample['id']))


def add_verified(identifier, contract, program, source):
    outcome = verify_and_compile(contract, program)
    assert outcome.servable, (identifier, outcome.reason_code)
    rows.append(dict(id=identifier, served=True, category=program.title, problem_text=contract.problem_text,
                     scene=_dung_scene3d(program, contract), source=source, verification='verify_and_compile SERVABLE'))


for slug, picks in [('regular-hexagonal-pyramid', [None]), ('regular-prisms', [3, 6])]:
    source = f'docs/evaluation/geometry/runs/{slug}/diagnostics/cases.py'
    module = load_module(source)
    for pick in picks:
        rid = next(k for k, v in module.LABELS.items() if v['expect'].startswith('served') and (pick is None or v['k'] == pick))
        contract, program = module.hop_dong_va_chuong_trinh(rid)
        add_verified(f'{slug}-{pick or "hex"}', contract, program, source + '#' + rid)

for slug, filename in [('oblique-prism', 'test_oblique_prism.py'), ('polygon-chain-base', 'test_general_polygon_base.py')]:
    source = 'backend/tests/geometry/' + filename
    module = load_module(source)
    rid = next(k for k, v in module.ROWS.items() if v['expect']['llm'].startswith('served'))
    add_verified(slug, module.hop_dong(rid), module.chuong_trinh_kieu_llm(rid), source + '#' + rid)

source = 'backend/tests/geometry/test_nonconvex_polyhedron_volume.py'
module = load_module(source)
add_verified('concave-pentagonal-pyramid', module._ct_lom(), module._spec_lom(), source + '#_spec_lom')

source = 'docs/evaluation/geometry/runs/regular-triangular-pyramid-w01/inputs/fixtures/'
for name in ['regular_triangular_pyramid', 'regular_tetrahedron']:
    file = source + name + '_positive.json'
    doc = json.loads((ROOT / file).read_text(encoding='utf-8'))
    envelope = doc.get('envelope', doc)
    rows.append(dict(id=name, served=True, category=envelope['title'], problem_text=doc.get('problem_text', envelope.get('description', '')),
                     scene=envelope['scene3d'], source=file))

complete = '--complete' in sys.argv
if complete:
    source = 'backend/tests/geometry/test_oblique_cone_section.py'
    module = load_module(source)
    assert module._chay().servable
    rows.append(dict(id='cone-oblique-ellipse', served=True, category='Thiết diện elip của hình nón',
                     problem_text=module.DE, scene=module._canh(), source=source + '#GOLD', verification='verify_and_compile SERVABLE'))

assert len({r['id'] for r in rows}) == len(rows)
for row in rows:
    row['scene_sha256'] = digest(row.get('scene'))
    row['state_sha256'] = digest({k: row.get(k) for k in ['scene', 'route_d', 'served', 'reason', 'code']})
out = RUN / ('scenes-complete.json' if complete else 'scenes.json')
assert not out.exists(), 'Never overwrite a captured fixture inventory'
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(RUN / ('coverage-complete.json' if complete else 'coverage.json')).write_text(json.dumps({'classification': 'DEVELOPMENT_EVALUATION_NOT_BLIND', 'scenes': [
    {k: r.get(k) for k in ['id', 'served', 'source', 'verification', 'scene_sha256', 'state_sha256']} for r in rows
], 'limits': ['Offline authored scenes do not demonstrate live natural-language E2E.', 'Derived residual volume does not imply a residual solid mesh.', 'Each shape is a representative, not exhaustive geometry coverage.']}, indent=2) + '\n')
print(f'Exported {len(rows)} immutable offline scenes; {sum(bool(r["served"]) for r in rows)} served; no provider calls')
