"""Independent Fraction oracles for source geometry; no application imports or screenshot oracle."""
import json
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
RUN = Path(__file__).resolve().parent
SAMPLES = {s['id']: s['envelope']['scene3d'] for s in json.loads((ROOT / 'frontend/src/data/geometry-samples.json').read_text(encoding='utf-8'))['samples']}
FIXTURES = {s['id']: s['scene3d'] for s in json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))}
rows = []

def vec(a): return tuple(F(x) for x in a)
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm2(a): return dot(a, a)
def objects(scene): return {o['id']: o for o in scene['objects']}
def answer_squared(q):
    e = q['exact']
    if e['kind'] == 'rational': return F(e['value']) ** 2
    assert not e.get('pi', 0)
    return F(e['coefficient']) ** 2 * F(e['radicand'])

def check(name, fn):
    try:
        rows.append({'name': name, 'status': 'PASS', 'evidence': fn()})
    except Exception as exc:
        rows.append({'name': name, 'status': 'FAIL', 'error': f'{type(exc).__name__}: {exc}'[:300]})

def sphere():
    o = objects(SAMPLES['cau-the-tich'])
    r2 = norm2(sub(vec(o['A']['xyz']), vec(o['I']['xyz'])))
    assert r2 == 9 and answer_squared(o['R']) == r2
    radius = F(o['R']['exact']['value'])
    volume_coefficient = F(4, 3) * radius ** 3
    e = o['V']['exact']
    assert e['pi'] == 1 and e['radicand'] == 1 and F(e['coefficient']) == volume_coefficient == 36
    return {'radius': str(radius), 'volume': f'{volume_coefficient}π', 'derivation': 'R² = IA·IA; V/π = (4/3)R³'}

def sphere_cut():
    o = objects(SAMPLES['cau-cat-mat-phang'])
    ball = o['cau']; plane = o['P']; n = vec(plane['normal'])
    d2 = dot(sub(vec(ball['anchor']), vec(plane['point'])), n) ** 2 / norm2(n)
    r2 = F(ball['radius_sq']) - d2
    assert d2 == 9 and r2 == 16 == F(o['C']['radius_sq']) == answer_squared(o['r'])
    e = o['S']['exact']; assert e['pi'] == 1 and e['radicand'] == 1 and F(e['coefficient']) == r2
    return {'d_squared': str(d2), 'circle_radius_squared': str(r2), 'circle_area': f'{r2}π'}

def pyramid():
    scene = SAMPLES['thiet-dien-chop']; o = objects(scene)
    for target, a, b in [('M', 'S', 'A'), ('N', 'S', 'B'), ('P', 'S', 'C')]:
        midpoint = tuple((x+y)/2 for x, y in zip(vec(o[a]['xyz']), vec(o[b]['xyz'])))
        assert vec(o[target]['xyz']) == midpoint
    sec = next(x for x in scene['objects'] if x['type'] == 'section')
    pts = list(map(vec, sec['polygon']))
    assert len(pts) == 4 and all(p[2] == 2 for p in pts)
    return {'midpoints': 'M,N,P exact', 'section_vertices': len(pts), 'section_plane_z': '2'}

def cube():
    scene = FIXTURES['cube-hexagon']; o = objects(scene)
    sec = o['td_hex']; pts = list(map(vec, sec['polygon'])); plane = o['mp_UVW']; n = vec(plane['normal'])
    assert len(pts) == 6 and sec['render'] == 'polygon'
    for p in pts:
        assert dot(sub(p, vec(plane['point'])), n) == 0
        assert sum(x in (F(0), F(2)) for x in p) == 2
    turns = []
    for i, p in enumerate(pts):
        q = pts[(i+1) % 6]; r = pts[(i+2) % 6]
        assert norm2(sub(q, p)) == 2
        turns.append(dot(cross(sub(q, p), sub(r, q)), n))
    assert all(t > 0 for t in turns) or all(t < 0 for t in turns)
    return {'vertices': 6, 'squared_edge_length': '2', 'coplanar': True, 'cyclic_order': True}

def prism():
    o = objects(FIXTURES['oblique-prism'])
    p = lambda k: vec(o[k]['xyz'])
    shift = sub(p('Ap'), p('A'))
    assert sub(p('Bp'), p('B')) == shift == sub(p('Cp'), p('C'))
    height = sub(p('Ap'), p('H')); ab = sub(p('B'), p('A')); ac = sub(p('C'), p('A'))
    assert dot(height, ab) == dot(height, ac) == 0 and norm2(height) == 16
    assert dot(shift, ab) != 0 and dot(shift, ac) != 0
    return {'parallel_bases_translation': list(map(str, shift)), 'height_squared': '16', 'lateral_edge_is_altitude': False}

def cylinder():
    scene = SAMPLES['tru-thiet-dien-tron']; o = objects(scene)
    ball = next(x for x in scene['objects'] if x['type'] == 'curved_solid')
    section = next(x for x in scene['objects'] if x['type'] == 'circle3')
    axis = sub(vec(ball['apex_or_top']), vec(ball['anchor']))
    assert norm2(cross(axis, vec(section['normal']))) == 0
    assert F(section['radius_sq']) == F(ball['radius_sq']) == 4
    return {'section_radius_squared': '4', 'section_plane_perpendicular_to_axis': True}

def cone():
    scene = SAMPLES['non-thiet-dien-truc']; o = objects(scene)
    area = next(x for x in scene['objects'] if x['type'] == 'quantity' and x.get('producer') == 'measure.area')
    sec = o[area['depends'][0]]; pts = list(map(vec, sec.get('polygon') or sec['vertices']))
    assert len(pts) == 3
    area2 = norm2(cross(sub(pts[1], pts[0]), sub(pts[2], pts[0]))) / 4
    assert area2 == 144 == answer_squared(area)
    return {'triangle_area': '12', 'independent_cross_product_area_squared': str(area2)}

def point_plane():
    scene = SAMPLES['mp-vuong-goc-duong']; o = objects(scene)
    for q in scene['objects']:
        if q['type'] != 'quantity' or not q.get('exact'): continue
        deps = [o[d] for d in q.get('depends', []) if d in o]
        points = [x for x in deps if x['type'] == 'point3']; planes = [x for x in deps if x['type'] == 'plane3']
        if not points or not planes: continue
        n = vec(planes[0]['normal']); d = sub(vec(points[0]['xyz']), vec(planes[0]['point']))
        expected = dot(d, n) ** 2 / norm2(n)
        assert answer_squared(q) == expected
        return {'quantity_id': q['id'], 'distance_squared': str(expected), 'method': '(n·(A-P))²/(n·n)'}
    raise AssertionError('No point-plane target found')

for name, fn in [('sphere radius and volume', sphere), ('sphere-plane circle radius and area', sphere_cut), ('pyramid section and midpoints', pyramid), ('cube closed hexagon', cube), ('oblique prism altitude and parallel bases', prism), ('cylinder perpendicular circular section', cylinder), ('cone axial triangle area', cone), ('point-plane distance', point_plane)]:
    check(name, fn)
result = {'method': 'independent Python standard-library Fraction algebra; no application imports', 'rows': rows}
(RUN / 'mathematics.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for row in rows: print(row['status'], row['name'], row.get('error', ''))
sys.exit(any(row['status'] != 'PASS' for row in rows))
