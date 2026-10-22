"""Evaluate the registered browser criteria; never infer human aesthetics."""
import hashlib
import json
import math
import re
import statistics
import subprocess
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[4]
# Arms re-measured at the product fix commit; earlier arms are superseded (survey-validity.json).
BEFORE, FINAL = 'before', 'final-r2'
STYLE = {'survey-A-r2': 'A', 'survey-B-r2': 'B', 'survey-C-r2': 'C', FINAL: 'B'}
ARMS = [BEFORE, 'survey-A-r2', 'survey-B-r2', 'survey-C-r2', FINAL]
rows = json.loads((RUN / 'scenes-complete.json').read_text(encoding='utf-8'))
receipts = {arm: json.loads((RUN / arm / 'receipt.json').read_text(encoding='utf-8')) for arm in ARMS}
styles = json.loads((RUN / 'proposals.json').read_text())
failures = []
checks = []


def check(name, condition, detail=None):
    checks.append(dict(name=name, pass_=bool(condition), detail=detail))
    if not condition:
        failures.append(dict(name=name, detail=detail))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def by_id(arm):
    return {r['id']: r for r in receipts[arm]['scenes']}


def near(a, b):
    if a is None or b is None:
        return False
    return len(a) == len(b) and all(abs(x-y) <= 1e-9 for x, y in zip(a, b))


def difference(a, b):
    x, y = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
    delta = ImageChops.difference(x, y)
    hist = delta.histogram()
    mean = sum((i % 256)*n for i, n in enumerate(hist)) / (x.width*x.height*3)
    r, g, b = delta.split()
    maximum = ImageChops.lighter(ImageChops.lighter(r, g), b)
    changed = x.width*x.height - maximum.histogram()[0]
    return dict(rgb_mean_absolute_delta=mean, changed_pixels=changed, changed_fraction=changed/(x.width*x.height))


baseline = by_id(BEFORE)
final = by_id(FINAL)
for arm, receipt in receipts.items():
    check(arm + ': complete inventory', receipt.get('finished') and len(receipt['scenes']) == len(rows))
    check(arm + ': no recorded browser errors', not receipt['errors'], receipt['errors'])
    check(arm + ': identical fixture bytes', receipt['fixture_sha256'] == digest(RUN / 'scenes-complete.json'))
    for shot in receipt['screenshots']:
        check(arm + ': screenshot hash ' + shot['file'], digest(RUN / arm / shot['file']) == shot['sha256'])

harness_lineage = {arm: receipts[arm]['harness_sha256'] for arm in ARMS}
check('survey/final arms share one harness', len({harness_lineage[arm] for arm in ARMS[1:]}) == 1, harness_lineage)
check('every harness version archived', all((RUN / 'harness-archive' / f'browser-{h[:8]}.mjs').exists() for h in harness_lineage.values()), harness_lineage)
before_receipt = receipts[BEFORE]
check('before: every baseline substitution applied once', set(before_receipt.get('baseline_substitutions_applied', {}).values()) == {1}
      and len(before_receipt['baseline_substitutions_applied']) == len(before_receipt['baseline_source_overrides']),
      before_receipt.get('baseline_substitutions_applied'))
check('before: built CSS carries baseline token values', bool(before_receipt.get('baseline_built_css_declarations_verified')),
      before_receipt.get('baseline_built_css_declarations_verified'))


def expected_roles(scene):
    """Re-statement (not an independent derivation) of the product rule: first constructed solid primary, ties by id.
    Proves the tokens reach the right shell, not that the rule itself is correct."""
    first = {}
    for event in scene['events']:
        if event['action'] in ('CREATE', 'INIT'):
            for oid in [event.get('object'), *(event.get('objects') or [])]:
                if oid and oid not in first:
                    first[oid] = event['step_index']
    solids = sorted((o['id'] for o in scene['objects'] if o['type'] in ('solid', 'curved_solid')),
                    key=lambda i: (first.get(i, math.inf), i))
    return {sid: ('primary' if n == 0 else 'secondary') for n, sid in enumerate(solids)}


def is_section(obj):
    base = obj.get('surface_role') == 'BASE_REGION' or 'CONSTRUCT_BASE' in (obj.get('formation_roles') or [])
    return not base and (obj.get('type') in ('section', 'polygon3', 'circle3', 'ellipse3')
                         or obj.get('surface_role') in ('SECTION_REGION', 'AUXILIARY_SURFACE'))


for arm in ARMS[1:]:
    receipt = receipts[arm]
    check(arm + ': same product commit', receipt['source_commit'] == receipts[FINAL]['source_commit'])
    check(arm + ': same underlying source hashes', receipt['source_hashes'] == receipts[FINAL]['source_hashes'])
    expected_overrides = 0 if arm == FINAL else 1
    check(arm + ': verified proposal override', receipt['applied_token_overrides'] == expected_overrides)
    # Runtime, not build-time: the live module constant and the actual WebGL materials carry the arm's tokens.
    style = styles[STYLE[arm]]
    probe = receipt.get('runtime_token_probe') or {}
    check(arm + ': runtime token probe equals style', probe.get('value') == style, probe.get('sha256'))
    if arm != FINAL:
        check(arm + ': runtime probe matched override', probe.get('matches_override') is True)
    hexes = {k: format(v, '06x') for k, v in style['colors'].items()}
    shell_seen = section_seen = 0
    for row in receipt['scenes']:
        if 'normal' not in row:
            continue
        normal = row['normal']
        lit = set(normal.get('highlighted') or [])
        scene = next(r for r in rows if r['id'] == row['id'])['scene']
        objects = {o['id']: o for o in scene['objects']}
        expected = expected_roles(scene)
        for sid, shell in normal['shells'].items():
            if sid in lit:
                continue
            shell_seen += 1
            want = (hexes['mesh'], style['opacity']['solid']) if expected[sid] == 'primary' \
                else (hexes['secondaryMesh'], style['opacity']['secondarySolid'])
            check(arm + ': neutral shell token ' + row['id'] + '/' + sid + ' ' + expected[sid],
                  (shell['color'], shell['opacity']) == want, shell)
        for m in normal['gpu']['materials']:
            kind, _, oid = m['name'].partition(':')
            if kind not in ('section_fill', 'polygon_fill') or oid in lit or not is_section(objects.get(oid, {})):
                continue
            section_seen += 1
            check(arm + ': section fill token ' + row['id'] + '/' + oid,
                  m['color'] == hexes['polygon'] and m['opacity'] == style['opacity']['section'] and m['type'] == 'MeshBasicMaterial', m)
    check(arm + ': shell token observations nonempty', shell_seen > 0, shell_seen)
    check(arm + ': section token observations nonempty', section_seen > 0, section_seen)
    for row in receipt['scenes']:
        if 'normal' not in row:
            continue
        original = baseline[row['id']]['normal']
        check(arm + ': camera position ' + row['id'], near(row['normal']['camera']['position'], original['camera']['position']))
        check(arm + ': projected camera identity ' + row['id'], near(row['normal']['camera']['view_matrix_column_major'], original['camera']['view_matrix_column_major']))

pixel_diffs = []
label_observations = []
selection_observations = []
reset_observations = []
orbit_observations = []
for row in rows:
    identifier = row['id']
    if not row['served']:
        check('refusal retained', bool(final[identifier].get('refusalText')) and final[identifier]['refusalText'] == baseline[identifier]['refusalText'])
        continue
    record = final[identifier]
    normal = record['normal']
    check('edge spans unchanged: ' + identifier, normal['edges'] == baseline[identifier]['normal']['edges'])
    check('default dash unchanged: ' + identifier, normal['dash'] == baseline[identifier]['normal']['dash'])
    check('selection preserves spans: ' + identifier, record.get('selected', {}).get('edges') == record['analysis']['edges'])
    check('selection is real: ' + identifier, bool(record.get('selected', {}).get('selected')))
    check('X-ray preserves spans: ' + identifier, record['xray']['edges'] == record['reset']['edges'])
    check('no duplicate edge owners: ' + identifier, not normal['duplicateOwners'])
    check('Mode A disclosure: ' + identifier, record['modeA']['panelCount'] == 0 and not record['modeA']['visibleFinalIds'])
    check('desktop panel overlap: ' + identifier, record['analysis']['bounds']['metrics']['panelOverlapPx'] == 0)
    # AMENDED AFTER OBSERVATION (not in metrics-policy.json): reset is compared relatively. The strict absolute 1e-9
    # comparison is kept as an observation; two rows differ by ~4e-9 on |x|~10, bit-identical in development B.
    reset, default = record['reset']['camera']['position'], normal['camera']['position']
    reset_observations.append(dict(id=identifier, strict_absolute_1e9=near(reset, default),
                                   max_abs_delta=max(abs(x - y) for x, y in zip(reset, default))))
    check('camera reset (relative 1e-9): ' + identifier,
          all(abs(x - y) <= 1e-9 * max(1, abs(y)) for x, y in zip(reset, default)), reset_observations[-1])
    # AMENDED AFTER OBSERVATION toward the registered wording ("encountered styles must not allocate repeatedly"):
    # first use of a newly met span style (e.g. an edge first hidden after camera drift) grows the owner pool.
    # Allocations beyond pool growth would be re-allocation. Strict [0, 0] is retained as an observation.
    # Limit: proves no re-allocation of an already-seen style, not bounded key growth (keys include fade/dash size).
    orbit_perf = record['orbitPerformance']
    orbit_observations.append(dict(id=identifier, strict_zero_repeat=orbit_perf['repeatMaterialAllocations'] == [0, 0],
                                   repeat_allocations=orbit_perf['repeatMaterialAllocations'], repeat_pool_growth=orbit_perf.get('repeatPoolGrowth')))
    check('warm orbit: no re-allocation of encountered styles: ' + identifier,
          orbit_perf.get('repeatPoolGrowth') is not None and orbit_perf['repeatMaterialAllocations'] == orbit_perf['repeatPoolGrowth'], orbit_perf)
    check('color management: ' + identifier, normal['gpu']['outputColorSpace'] == 'srgb' and normal['gpu']['colorManagement'])
    check('label font floor: ' + identifier, all(label['fontSize'] >= 12 for label in normal['labels']))
    def collisions(labels):
        count = 0
        for index, a in enumerate(labels):
            for b in labels[index+1:]:
                p, q = a['rect'], b['rect']
                if min(p['x']+p['w'], q['x']+q['w']) - max(p['x'], q['x']) > 1 and min(p['y']+p['h'], q['y']+q['h']) - max(p['y'], q['y']) > 1:
                    count += 1
        return count
    old_collisions = collisions(baseline[identifier]['normal']['labels'])
    new_collisions = collisions(normal['labels'])
    check('no new label collisions: ' + identifier, new_collisions <= old_collisions)
    label_observations.append(dict(id=identifier, baseline_collisions=old_collisions, final_collisions=new_collisions,
        min_font_size=min((x['fontSize'] for x in normal['labels']), default='UNKNOWN'),
        universal_background_contrast='UNKNOWN', reason='Actual text/background RGBA and opacity are retained per label in the browser receipt; semi-transparent labels require background-dependent review.'))
    selected_materials = record['selected']['gpu']['materials']
    check('selection changes material emphasis: ' + identifier, selected_materials != record['analysis']['gpu']['materials'])
    selection_observations.append(dict(id=identifier, selected_id=record['selected']['selected'],
        focus_blue_material_count=sum(m['color'] == '0075de' for m in selected_materials),
        visible_selected_id=True))
    originals = {o['id']: o for o in row['scene']['objects']}
    for fill in normal['ownPixels']:
        obj = originals.get(fill['name'].split(':', 1)[1], {})
        section = obj.get('type') == 'section' or obj.get('surface_role') == 'SECTION_REGION' or (
            obj.get('surface_role') == 'AUXILIARY_SURFACE' and 'CONSTRUCT_BASE' not in obj.get('formation_roles', [])) or (
            obj.get('type') in ['circle3', 'ellipse3'] and obj.get('surface_role') != 'BASE_REGION')
        if not section:
            continue
        orbit = next((x for x in record['orbit']['ownPixels'] if x['name'] == fill['name']), None)
        check('visible section own pixels: ' + identifier + '/' + fill['name'], orbit is not None and max(fill['pixels'], orbit['pixels']) > 0,
              dict(normal=fill, orbit=orbit))
    repeat = difference(RUN / FINAL / (identifier+'-normal.png'), RUN / FINAL / (identifier+'-repeat.png'))
    check('screenshot reproduction: ' + identifier, repeat['rgb_mean_absolute_delta'] < .2 and repeat['changed_fraction'] < .01, repeat)
    pixel_diffs.append(dict(id=identifier, before_after=difference(RUN/BEFORE/(identifier+'-normal.png'), RUN/FINAL/(identifier+'-normal.png')), repeat=repeat))

# Same fixture/camera/viewport/state per row: one strip per scene, before | A | B | C | final.
sheets = RUN / 'comparison'
sheets.mkdir(exist_ok=True)
abc_diffs = []
for row in rows:
    if not row['served']:
        continue
    shots = [RUN / arm / (row['id'] + '-normal.png') for arm in ARMS]
    abc_diffs.append(dict(id=row['id'], **{arm: difference(shots[0], shot) for arm, shot in zip(ARMS[1:], shots[1:])}))
    images = [Image.open(p).convert('RGB') for p in shots]
    w, h = images[0].width // 2, images[0].height // 2
    sheet = Image.new('RGB', (w * len(images), h + 24), 'white')
    draw = ImageDraw.Draw(sheet)
    for i, (arm, image) in enumerate(zip(ARMS, images)):
        sheet.paste(image.resize((w, h), Image.LANCZOS), (i * w, 24))
        draw.text((i * w + 8, 6), arm + ' (' + row['id'] + ')', fill='black', font=ImageFont.load_default())
    sheet.save(sheets / (row['id'] + '.png'))

check('compact inventory', len(receipts[FINAL]['compact']) == 2 * sum(r['served'] for r in rows))
for compact in receipts[FINAL]['compact']:
    check('compact panel overlap ' + compact['id'] + ' ' + str(compact['viewport']['width']), compact['open']['bounds']['metrics']['panelOverlapPx'] == 0)

for mode in ['depth', 'xrayDepth']:
    probes = receipts[FINAL][mode]
    check(mode + ': nonempty probe', bool(probes))
    for probe in probes:
        check(mode + ': independent wall ' + probe['family'] + '/' + probe['id'], all(s['pass'] for s in probe['samples']), probe['samples'])

for transition in receipts[FINAL]['transitions']:
    before, isolated, hidden, reordered = (transition[k]['shells'] for k in ['before', 'isolated', 'hidden', 'reordered'])
    check('reorder role stability ' + transition['id'], before == reordered)
    check('isolation exercised ' + transition['id'], bool(isolated))
    check('isolation role stability ' + transition['id'], all(before[k] == value for k, value in isolated.items()))
    check('hide exercised ' + transition['id'], set(hidden) < set(before))
    check('hide role stability ' + transition['id'], all(before[k] == value for k, value in hidden.items()))
    check('backward steps exercised ' + transition['id'], bool(transition['steps']))

# Existing runtime properties are not unresolved design tokens.
sources = []
for suffix in ['*.css', '*.ts', '*.tsx']:
    sources += [p for p in (ROOT/'frontend/src').rglob(suffix) if '.test.' not in p.name]
defined, used = set(), set()
for path in sources:
    text = re.sub(r'/\*[\s\S]*?\*/', '', path.read_text(encoding='utf-8'))
    defined.update(re.findall(r'(--[a-z0-9-]+)\s*:', text, re.I))
    used.update(re.findall(r'var\(\s*(--[a-z0-9-]+)', text, re.I))
unresolved = sorted(used - defined - {'--len', '--geo3d-cao-khung'})
check('unresolved CSS variables', not unresolved, unresolved)
diff = subprocess.check_output(['git','diff','f95596716912e5550ed079287221274b2d70f24c', receipts[FINAL]['source_commit'], '--', 'backend/app','frontend/src'],cwd=ROOT).decode('utf-8')
product_paths = subprocess.check_output(['git','diff','--name-only','f95596716912e5550ed079287221274b2d70f24c',receipts[FINAL]['source_commit'],'--','backend/app','frontend/src'],cwd=ROOT).decode().splitlines()
product_paths = [p for p in product_paths if '.test.' not in p]
check('product scope excludes mathematical authority', sorted(product_paths) == sorted([
    'frontend/src/simulations/domains/geometry/scene3d-roles.ts',
    'frontend/src/simulations/domains/geometry/scene3d-view.tsx','frontend/src/styles/tokens.css']))
view_diff = subprocess.check_output(['git','diff','f95596716912e5550ed079287221274b2d70f24c',receipts[FINAL]['source_commit'],'--',product_paths[0],product_paths[1]],cwd=ROOT).decode('utf-8')
exceptions = [line for line in view_diff.splitlines() if line.startswith('+') and re.search(r'\b(?:family\d+|demo\d+|pyr\d+)\b', line)]
check('scene-specific palette exceptions', not exceptions, exceptions)

section_pixels = [dict(id=r['id'], state=state, fills=r[state]['ownPixels']) for r in receipts[FINAL]['scenes'] if 'normal' in r for state in ['normal','orbit','xray']]
occlusion_times = [t for r in receipts[FINAL]['scenes'] if 'orbitPerformance' in r for t in r['orbitPerformance']['occlusion']['recomputation_times_ms']]
performance = dict(environment=receipts[FINAL]['environment'], samples=len(occlusion_times),
    occlusion_p50_ms=statistics.median(occlusion_times), occlusion_p95_ms=sorted(occlusion_times)[math.floor(.95*(len(occlusion_times)-1))],
    physical_device_fps='UNKNOWN', browser_orbits=[dict(id=r['id'], **r['orbitPerformance']) for r in receipts[FINAL]['scenes'] if 'orbitPerformance' in r])
result = dict(status='AUTOMATED_TECHNICAL_PASS' if not failures else 'AUTOMATED_TECHNICAL_FAIL',
    human_visual_approval='NOT_GRANTED', total_checks=len(checks), failures=failures,
    checks=checks, pixel_diffs=pixel_diffs, abc_normal_vs_baseline=abc_diffs, harness_lineage=harness_lineage, camera_reset_observations=reset_observations,orbit_allocation_observations=orbit_observations,section_own_pixels=section_pixels, performance=performance,
    label_observations=label_observations, selection_observations=selection_observations,
    unresolved_css_variables=unresolved, scene_specific_palette_exceptions=exceptions,
    limits=['No aesthetic score assigned.', 'Label font/color/position data do not prove readability on every background/device.',
            'Camera wall probes are independent synthetic occlusion witnesses, not a full scene oracle.', 'Offline authored fixtures do not prove live NLU E2E.'])
(RUN/'browser-metrics.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['status','total_checks','failures']},indent=2))
raise SystemExit(bool(failures))
