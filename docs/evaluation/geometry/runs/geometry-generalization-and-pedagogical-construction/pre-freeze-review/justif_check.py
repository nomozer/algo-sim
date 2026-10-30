"""Independent check of every section-edge 'why' over real scenes: dev corpus (all served), locked 96 dev payloads, offline samples.
Usage: justif_check.py <backend_root> <repo_root>"""
import json, os, re, socket, sys
from fractions import Fraction as F
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
os.environ['ALLOW_LIVE_AI'] = '0'
socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('OFFLINE_ONLY'))
from app.ai.adapter4_route import run_typed_fact_next_v2_route
REPO = sys.argv[2]
W4 = REPO + '/docs/evaluation/geometry/runs/geometry-generalization-and-pedagogical-construction'
RUN = REPO + '/docs/evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding'

def q(v):
    return tuple(F(str(x)) for x in v)
def sub(u, v): return tuple(x - y for x, y in zip(u, v))
def cross(u, v): return (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
def dot(u, v): return sum(x*y for x, y in zip(u, v))

def check_scene(tag, sc, stats, bad):
    objs = {o['id']: o for o in sc['objects']}
    for e in sc['events']:
        if e.get('action') != 'EXTEND':
            continue
        sec = objs.get(e.get('object'))
        if not sec or sec.get('type') != 'section':
            continue
        stats['ext'] += 1
        deps = [objs.get(d, {}) for d in sec.get('depends') or []]
        types = [d.get('type') for d in deps]
        if types.count('solid') > 1 or types.count('plane3') > 1:
            stats['multi_dep'] += 1
        j = (e.get('details') or {}).get('justification')
        if not e.get('justification_text'):
            continue
        stats['just'] += 1
        try:
            solid = next(d for d in deps if d.get('type') == 'solid'); plane = next(d for d in deps if d.get('type') == 'plane3')
            k = e['details']['canh']; st = sec['steps'][k]; a, b = q(st['a']), q(st['b'])
            face = solid['faces'][st['face_index']]; V = [q(solid['vertices'][i]) for i in face]
            p0, n = q(plane['point']), q(plane['normal'])
            # face plane from first non-collinear triple
            fn = next(cross(sub(V[i], V[0]), sub(V[i+1], V[0])) for i in range(1, len(V)-1) if any(cross(sub(V[i], V[0]), sub(V[i+1], V[0]))))
            probs = []
            if any(dot(fn, sub(P, V[0])) for P in V): probs.append('face_nonplanar')
            if dot(fn, sub(a, V[0])) or dot(fn, sub(b, V[0])): probs.append('edge_not_in_face')
            if dot(n, sub(a, p0)) or dot(n, sub(b, p0)): probs.append('edge_not_in_plane')
            if not any(cross(fn, n)): probs.append('face_parallel_or_equal_plane')
            m = re.search(r'Trên mặt (\S+),', e.get('learner_text') or '')
            if m and m.group(1) != j['face']: probs.append(f"face_name {m.group(1)}!={j['face']}")
            line = j['line']; text = e['justification_text']
            if line not in text or j['face'] not in text: probs.append('text_fields')
            if probs: bad.append((tag, e.get('step_index'), probs, text))
        except Exception as ex:  # noqa: BLE001
            bad.append((tag, e.get('step_index'), ['checker_exc ' + repr(ex)], e.get('justification_text')))

stats = {'scenes': 0, 'ext': 0, 'just': 0, 'multi_dep': 0}; bad = []
cases = json.load(open(W4 + '/dev-corpus/cases.json', encoding='utf-8'))
for cid, c in cases.items():
    r = run_typed_fact_next_v2_route(json.loads(json.dumps(c['payload'])))
    if r.status == 'SERVED' and r.scene3d: stats['scenes'] += 1; check_scene('dev:' + cid, r.scene3d, stats, bad)
for c in json.load(open(RUN + '/inputs/development.json', encoding='utf-8'))['cases']:
    try: r = run_typed_fact_next_v2_route(json.loads(json.dumps(c['payload'])))
    except Exception: continue
    if r.status == 'SERVED' and r.scene3d: stats['scenes'] += 1; check_scene('l96:' + c['id'], r.scene3d, stats, bad)
samp = json.load(open(REPO + '/frontend/src/data/geometry-samples.json', encoding='utf-8'))
def walk(x, path=''):
    if isinstance(x, dict):
        if 'events' in x and 'objects' in x: yield path, x
        for k, v in x.items(): yield from walk(v, path + '/' + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x): yield from walk(v, f'{path}[{i}]')
for path, sc in walk(samp):
    stats['scenes'] += 1; check_scene('sample:' + path, sc, stats, bad)
print(json.dumps(stats)); print(len(bad), 'problems')
for b in bad[:40]: print(b)
