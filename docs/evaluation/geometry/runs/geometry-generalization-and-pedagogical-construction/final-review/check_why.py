"""Independent exact re-check of every section-edge 'why' in committed scenes. usage: check_why.py <file>..."""
import json, sys
from fractions import Fraction as Q

def scenes(x):
    if isinstance(x, dict):
        if 'objects' in x and 'events' in x and isinstance(x['objects'], list):
            yield x
        for v in x.values():
            yield from scenes(v)
    elif isinstance(x, list):
        for v in x:
            yield from scenes(v)

def q(v): return tuple(Q(str(c)) for c in v)
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def det3(u, v, w):
    return (u[0] * (v[1] * w[2] - v[2] * w[1]) - u[1] * (v[0] * w[2] - v[2] * w[0]) + u[2] * (v[0] * w[1] - v[1] * w[0]))
def rank1(u, v):  # all 2x2 minors vanish
    return all(u[i] * v[j] - u[j] * v[i] == 0 for i in range(3) for j in range(i + 1, 3))

tot = dict(scenes=0, sections=0, edges=0, why=0, bad=0, nonextend_why=0, missing_possible=0)
bad = []
for f in sys.argv[1:]:
    data = json.load(open(f, encoding='utf-8'))
    for sc in scenes(data):
        tot['scenes'] += 1
        by = {o['id']: o for o in sc['objects']}
        name = lambda vid: (by.get(vid, {}).get('notation') or by.get(vid, {}).get('reference') or vid)
        for e in sc['events']:
            if e.get('justification_text') and e.get('action') != 'EXTEND':
                tot['nonextend_why'] += 1; bad.append((f, 'non-EXTEND why', e.get('step_index')))
        for sec in (o for o in sc['objects'] if o.get('type') == 'section'):
            tot['sections'] += 1
            evs = [e for e in sc['events'] if e.get('object') == sec['id'] and e.get('action') == 'EXTEND']
            for st in sec.get('steps') or []:
                tot['edges'] += 1
            for e in evs:
                d = e.get('details') or {}
                j = d.get('justification')
                if not j:
                    continue
                tot['why'] += 1
                try:
                    solid, plane = by[d['khoi']], by[d['mat_phang']]
                    k, mat = d['canh'], d['mat']
                    st = sec['steps'][k]
                    assert st['face_index'] == mat, 'face idx mismatch'
                    assert q(st['a']) == q(d['a']) and q(st['b']) == q(d['b']), 'event a/b != step'
                    V = [q(v) for v in solid['vertices']]
                    nm = [name(v) for v in solid['vertex_ids']]
                    face = solid['faces'][mat]
                    assert ''.join(nm[i] for i in face) == j['face'], ('face name', j['face'], ''.join(nm[i] for i in face))
                    edges = [(face[i], face[(i + 1) % len(face)]) for i in range(len(face))]
                    hit = [(x, y) for x, y in edges if nm[x] + nm[y] == j['line']]
                    assert len(hit) == 1, ('line not a unique face edge', j['line'])
                    x, y = hit[0]
                    X, Y = V[x], V[y]
                    p0, n = q(plane['point']), q(plane['normal'])
                    a, b = q(st['a']), q(st['b'])
                    F0, F1, F2 = V[face[0]], V[face[1]], V[face[2]]
                    on_a = lambda P: sum(c * w for c, w in zip(n, sub(P, p0))) == 0
                    on_f = lambda P: det3(sub(F1, F0), sub(F2, F0), sub(P, F0)) == 0
                    assert all(on_f(V[i]) for i in face), 'face not planar'
                    assert a != b and on_a(a) and on_a(b) and on_f(a) and on_f(b), 'segment not on alpha ∩ face'
                    assert not on_a(X) and sum(c * w for c, w in zip(n, sub(Y, X))) == 0, 'XY not strictly parallel to alpha'
                    assert rank1(sub(b, a), sub(Y, X)), 'section edge not parallel to XY'
                    assert j['plane'] == (plane.get('notation') or 'mặt phẳng cắt'), 'plane name'
                    assert j['plane'] in e['justification_text'] and j['line'] in e['justification_text'] and j['face'] in e['justification_text']
                except (AssertionError, KeyError, IndexError) as ex:
                    tot['bad'] += 1; bad.append((f, e.get('step_index'), repr(ex)[:200]))
print(json.dumps(tot)); [print('BAD', b) for b in bad[:30]]
