"""Sixteenth continuation (§V.5.3): does the planner miss sections a valid plan reaches? Systematic, not hand-picked.

Every "Mặt phẳng (P) đi qua M và vuông góc với d" on two topologies — the pyramid S.ABCD (square base, SA ⊥ base) and the
right prism ABC.A'B'C' (right angle at A) — with d = every pair of vertices and M = every vertex and every edge midpoint
(an unnamed described point). Each case runs the production opt-in Hybrid /4 path from a hand-built gold extraction.

ORACLE (independent of the product; no product import is used to compute it): exact Euclidean coordinates; the plane
n·(X − M) = 0 with n = the direction of d; the section is the convex polygon of the plane's crossings of the solid's
edges; area² by a fan of exact cross products (float angles only ORDER the vertices). Reachable ⇔ the plane cuts the
interior (vertices strictly on both sides). Witness plan (what the registered primitives can build, checked exactly):
two vertices Z₁, Z₂ off d whose directions Zᵢ − foot(Zᵢ, d) are independent — the oracle lists every such pair.

IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC, offline, 0 provider calls. Usage: plane_witness_reachability.py [out.json]
"""
import collections, itertools, json, math, os, socket, sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'backend'))
os.environ['ALLOW_LIVE_AI'] = '0'
def _offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = _offline; socket.create_connection = _offline

# ── oracle (pure fractions) ─────────────────────────────────────────────────────────────────────────────────────────
def sub(p, q): return tuple(a - b for a, b in zip(p, q))
def add(p, q): return tuple(a + b for a, b in zip(p, q))
def dot(p, q): return sum(a * b for a, b in zip(p, q))
def cross(p, q): return (p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0])
def mid(p, q): return tuple(F(a + b) / 2 for a, b in zip(p, q))     # F: int/2 would be a float


def foot(z, a, b):
    d = sub(b, a)
    t = dot(sub(z, a), d) / dot(d, d)
    return tuple(x + t * y for x, y in zip(a, d))


def section_area2(V, edges, m, n):
    f = {k: dot(n, sub(p, m)) for k, p in V.items()}
    if not (any(v > 0 for v in f.values()) and any(v < 0 for v in f.values())):
        return None                                            # misses / touches / is a face: no section
    pts = {V[k] for k in V if f[k] == 0}
    for a, b in edges:
        if f[a] * f[b] < 0:
            t = f[a] / (f[a] - f[b])
            pts.add(tuple(x + t * (y - x) for x, y in zip(V[a], V[b])))
    pts = list(pts)
    c = tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))
    u = sub(pts[0], c)
    w = cross(n, u)
    pts.sort(key=lambda p: math.atan2(float(dot(sub(p, c), w)), float(dot(sub(p, c), u))))
    s = (0, 0, 0)
    for q, r in zip(pts[1:], pts[2:]):
        s = add(s, cross(sub(q, pts[0]), sub(r, pts[0])))
    return dot(s, s) / 4


def witnesses(V, d):
    a, b = V[d[0]], V[d[1]]
    dirs = {z: sub(V[z], foot(V[z], a, b)) for z in V if z not in d}
    dirs = {z: v for z, v in dirs.items() if any(v)}
    return [(z1, z2) for z1, z2 in itertools.combinations(sorted(dirs), 2) if any(cross(dirs[z1], dirs[z2]))]


def squared(s):
    import re
    m = re.fullmatch(r'(?P<p>\d+)?(?:√(?P<r>\d+))?(?:/(?P<q>\d+))?', s)
    if not m or not (m['p'] or m['r']):
        return None
    p, r, q = F(m['p'] or 1), F(m['r'] or 1), F(m['q'] or 1)
    return p * p * r / (q * q)


# ── topologies ──────────────────────────────────────────────────────────────────────────────────────────────────────
def pyramid(a, h):
    a, h = F(a), F(h)
    V = {'A': (0, 0, 0), 'B': (a, 0, 0), 'C': (a, a, 0), 'D': (0, a, 0), 'S': (0, 0, h)}
    E = [('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'A'), ('S', 'A'), ('S', 'B'), ('S', 'C'), ('S', 'D')]
    text = f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh {a}, SA vuông góc với mặt phẳng (ABCD) và SA = {h}. '
    prem = [{'kind': 'regular_polygon', 'args': {'vertices': list('ABCD'), 'side': str(a)},
             'quote': f'đáy ABCD là hình vuông cạnh {a}', 'solid_id': 's1'},
            {'kind': 'perpendicular_line_plane', 'args': {'line': ['S', 'A'], 'plane': list('ABCD')},
             'quote': 'SA vuông góc với mặt phẳng (ABCD)', 'solid_id': 's1'},
            {'kind': 'segment_length', 'args': {'segment': ['S', 'A'], 'value': str(h)}, 'quote': f'SA = {h}', 'solid_id': 's1'}]
    return 'pyramid', 'S.ABCD', 'Cho hình chóp S.ABCD', 'hình chóp S.ABCD', V, E, text, prem


def prism(b, c, h):
    b, c, h = F(b), F(c), F(h)
    V = {'A': (0, 0, 0), 'B': (b, 0, 0), 'C': (0, c, 0), "A'": (0, 0, h), "B'": (b, 0, h), "C'": (0, c, h)}
    E = [('A', 'B'), ('B', 'C'), ('C', 'A'), ("A'", "B'"), ("B'", "C'"), ("C'", "A'"), ('A', "A'"), ('B', "B'"), ('C', "C'")]
    text = (f"Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = {b}, AC = {c} và AA' = {h}. ")
    prem = [{'kind': 'right_prism', 'args': {'base': list('ABC'), 'top': ["A'", "B'", "C'"]},
             'quote': "Cho hình lăng trụ đứng ABC.A'B'C'", 'solid_id': 's1'},
            {'kind': 'right_angle', 'args': {'vertex': 'A', 'rays': ['B', 'C']}, 'quote': 'đáy ABC là tam giác vuông tại A',
             'solid_id': 's1'},
            {'kind': 'segment_length', 'args': {'segment': ['A', 'B'], 'value': str(b)}, 'quote': f'AB = {b}', 'solid_id': 's1'},
            {'kind': 'segment_length', 'args': {'segment': ['A', 'C'], 'value': str(c)}, 'quote': f'AC = {c}', 'solid_id': 's1'},
            {'kind': 'segment_length', 'args': {'segment': ['A', "A'"], 'value': str(h)}, 'quote': f"AA' = {h}", 'solid_id': 's1'}]
    return 'prism', "ABC.A'B'C'", "Cho hình lăng trụ đứng ABC.A'B'C'", "hình lăng trụ ABC.A'B'C'", V, E, text, prem


def cases():
    for topo in (pyramid(2, 2), pyramid(3, 4), prism(3, 4, 2), prism(2, 2, 3)):
        kind, notation, solid_q, solid_name, V, E, base, prem = topo
        area_q = f'Xác định thiết diện của {solid_name} cắt bởi (P) và tính diện tích thiết diện đó'
        points = [(v, v, None, V[v]) for v in V] + [
            (f'@m_{a}{b}'.replace("'", 'p'), f'trung điểm của {a}{b}', (a, b), mid(V[a], V[b])) for a, b in E]
        for d in itertools.combinations(V, 2):
            for ref, phrase, seg, pm in points:
                s = f'Mặt phẳng (P) đi qua {phrase} và vuông góc với {d[0]}{d[1]}'
                text = base + s + '. ' + area_q + '.'
                sec = {'section_id': 'sec1', 'plane_name': 'P', 'target_solid_id': 's1', 'quote': s,
                       'through_point': ref, 'stated_intersections': [], 'plane_kind': 'through_point_perpendicular_line',
                       'perpendicular_line': list(d)}
                payload = {'schema_version': 'typed-fact-next/2', 'problem_text': text, 'length_unit': '1',
                           'solids': [{'solid_id': 's1', 'solid_type': kind, 'notation': notation, 'quote': solid_q}],
                           'premises': prem, 'derived_sections': [sec], 'relations': [],
                           'simulation_goals': [{'goal_id': 'sg1', 'kind': 'construct_object', 'target_solid_id': 's1',
                                                 'quote': solid_q}],
                           'math_goals': [{'goal_id': 'q1', 'kind': 'measurement', 'goal_type': 'area',
                                           'target': {'section_id': 'sec1'}, 'quote': area_q, 'solid_id': 's1'}]}
                if seg:
                    payload['described_points'] = [{'described_id': ref[1:], 'kind': 'midpoint', 'quote': phrase[0:] if False
                                                    else f'trung điểm của {seg[0]}{seg[1]}', 'segment': list(seg)}]
                n = sub(V[d[1]], V[d[0]])
                yield {'topology': f'{kind}{tuple(map(str, (V[list(V)[1]][0], V[list(V)[-1]][2])))}', 'line': ''.join(d),
                       'through': phrase, 'text': text, 'payload': payload,
                       'oracle_area2': section_area2(V, E, pm, n), 'witness_pairs': witnesses(V, d)}


if __name__ == '__main__':
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    from app.ai.typed_fact_next_extraction import ReplayExtractor
    policy = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})
    rows = []
    for c in cases():
        out = run_hybrid_offline(c['text'], ReplayExtractor({c['text']: c['payload']}), policy=policy).response
        route = out['route_d']
        got = None
        if route['status'] == 'SERVED':
            vals = [v for v in (route.get('answer_exact') or {}).values()]
            got = [squared(str(v.get('coef'))) if isinstance(v, dict) else None for v in vals]
        aux = next((x for x in (route.get('planner') or {}).get('auxiliary') or () if x.get('anchors')), {})
        reach = c['oracle_area2'] is not None and bool(c['witness_pairs'])
        verdict = ('SERVED_CORRECT' if route['status'] == 'SERVED' and reach and got == [c['oracle_area2']]
                   else 'WRONG_SERVED' if route['status'] == 'SERVED'
                   else 'REACHABLE_REFUSED' if reach else 'CORRECT_REFUSAL')
        rows.append({k: c[k] for k in ('topology', 'line', 'through')} | {
            'oracle_area2': str(c['oracle_area2']) if c['oracle_area2'] is not None else None,
            'oracle_witness_pairs': len(c['witness_pairs']), 'status': route['status'],
            'code': out['envelope'].get('reason_code'), 'anchors': aux.get('anchors'), 'verdict': verdict})
    summary = {'cases': len(rows), 'verdicts': dict(collections.Counter(r['verdict'] for r in rows)),
               'reachable_refused_codes': dict(collections.Counter(r['code'] for r in rows if r['verdict'] == 'REACHABLE_REFUSED'))}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    if len(sys.argv) > 1:
        import subprocess
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
            json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'provider_calls': 0, 'head': head,
                       'summary': summary, 'rows': rows}, f, ensure_ascii=False, indent=1)
            f.write('\n')
