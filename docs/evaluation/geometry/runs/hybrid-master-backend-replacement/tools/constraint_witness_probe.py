"""Seventeenth continuation: constraint-to-witness planes on Hybrid /4, measured systematically against an independent
exact oracle — never against the planner's own label.

Families (every combination, generated, not hand-picked):
  F1 "Mặt phẳng (P) đi qua X, Y và vuông góc với (Q)"  — X, Y over the solid's vertices and two named edge midpoints M, N;
                                                         Q over the faces and the diagonal planes.
  F2 "Mặt phẳng (P) chứa XY và song song với UV"        — X, Y as above; UV over the edges and diagonals.
Topologies: pyramid S.ABCD (square base, SA ⊥ (ABCD)) at two sizes; right prism ABC.A'B'C' (right angle at A).

ORACLE (no product import; exact fractions): the constraint vectors (Y − X, the normal of Q, UV) decide the plane —
rank < 2: NOT_UNIQUE; a vector off the span: NO_PLANE; ∥ line inside the plane: LINE_IN_PLANE; plane holding a face or
missing the interior: NO_SECTION; otherwise UNIQUE with the section's area² (convex polygon from the edge crossings).
A witness plan exists for every UNIQUE plane from the Registry's primitives: the normal of any Q is Z − foot(Z, Q) for a
vertex Z off Q (there always is one), and ∥ UV is the anchor + UV.

COMPOSITION (from the CERTIFICATE the product served with, not from telemetry). Under the reviewed C15 rule every plan
here is REGISTERED_DECOMPOSITION: `MAT_RANG_BUOC` is a declared rule (C17 review MAJOR-3). The detail label says which
part of the rule served it, a witness counting only where the oracle shows it NECESSARY (the stated points alone do not
span the plane), else VERIFICATION_WITNESS_ONLY:
  RULE_PARAMETER_CONSTRUCTED_NORMAL — the rule's free vertex Z bound by the Normal contract, its foot built;
  RULE_PREMISE_NORMAL — the normal is a stated premise line ⊥ Q;
  RULE_STATED_LINE — only translations along a stated line (as MAT_HAI_DUONG).
  `foot_is_vertex` records a foot that coincides with a vertex of the solid (review MINOR-2).
IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC, offline, 0 provider calls. Usage: constraint_witness_probe.py [out.json]
"""
import collections, itertools, json, math, os, re, socket, sys
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
def mid(p, q): return tuple(F(a + b) / 2 for a, b in zip(p, q))


def oracle(V, E, faces, points, normal_of=None, line=None):
    """(verdict, area²) of the plane through `points` ⊥ the plane `normal_of` (labels) or ∥ the line `line`."""
    P = [V[x] for x in points]
    vec = [sub(p, P[0]) for p in P[1:]]
    if normal_of is not None:
        a, b, c = (V[x] for x in normal_of[:3])
        vec.append(cross(sub(b, a), sub(c, a)))
    else:
        vec.append(sub(V[line[1]], V[line[0]]))
    pair = next(((u, w) for i, u in enumerate(vec) for w in vec[i + 1:] if any(cross(u, w))), None)
    if pair is None:
        return 'NOT_UNIQUE', None
    n = cross(*pair)
    if any(dot(n, v) for v in vec):
        return 'NO_PLANE', None
    if line is not None and dot(n, sub(V[line[0]], P[0])) == 0:
        return 'LINE_IN_PLANE', None
    f = {k: dot(n, sub(p, P[0])) for k, p in V.items()}
    if not (any(v > 0 for v in f.values()) and any(v < 0 for v in f.values())):
        return 'NO_SECTION', None
    pts = {V[k] for k in V if f[k] == 0}
    for a, b in E:
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
    return 'UNIQUE', dot(s, s) / 4


def squared(x):
    m = re.fullmatch(r'(?P<p>\d+)?(?:√(?P<r>\d+))?(?:/(?P<q>\d+))?', x or '')
    if not m or not (m['p'] or m['r']):
        return None
    p, r, q = F(m['p'] or 1), F(m['r'] or 1), F(m['q'] or 1)
    return p * p * r / (q * q)


# ── topologies ──────────────────────────────────────────────────────────────────────────────────────────────────────
Z = F(0)


def pyramid(a, h):
    a, h = F(a), F(h)
    V = {'A': (Z, Z, Z), 'B': (a, Z, Z), 'C': (a, a, Z), 'D': (Z, a, Z), 'S': (Z, Z, h)}
    E = [('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'A'), ('S', 'A'), ('S', 'B'), ('S', 'C'), ('S', 'D')]
    planes = [list('ABCD'), list('SAB'), list('SBC'), list('SCD'), list('SDA'), list('SAC'), list('SBD'),
              list('SAM'), list('MBC'), list('SMN')]     # review MINOR-1: Q named through the stated midpoints
    lines = [list(x) for x in ('AB', 'BC', 'SA', 'SB', 'SC', 'SD', 'AC', 'BD')]
    mids = (('M', ('A', 'B')), ('N', ('S', 'C')))
    text = f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh {a}, SA vuông góc với mặt phẳng (ABCD) và SA = {h}. '
    prem = [{'kind': 'regular_polygon', 'args': {'vertices': list('ABCD'), 'side': str(a)},
             'quote': f'đáy ABCD là hình vuông cạnh {a}', 'solid_id': 's1'},
            {'kind': 'perpendicular_line_plane', 'args': {'line': ['S', 'A'], 'plane': list('ABCD')},
             'quote': 'SA vuông góc với mặt phẳng (ABCD)', 'solid_id': 's1'},
            {'kind': 'segment_length', 'args': {'segment': ['S', 'A'], 'value': str(h)}, 'quote': f'SA = {h}', 'solid_id': 's1'}]
    return f'pyramid({a},{h})', 'pyramid', 'S.ABCD', 'Cho hình chóp S.ABCD', 'hình chóp S.ABCD', V, E, planes, lines, mids, text, prem


def prism(b, c, h):
    b, c, h = F(b), F(c), F(h)
    V = {'A': (Z, Z, Z), 'B': (b, Z, Z), 'C': (Z, c, Z), "A'": (Z, Z, h), "B'": (b, Z, h), "C'": (Z, c, h)}
    E = [('A', 'B'), ('B', 'C'), ('C', 'A'), ("A'", "B'"), ("B'", "C'"), ("C'", "A'"), ('A', "A'"), ('B', "B'"), ('C', "C'")]
    planes = [list('ABC'), ["A'", "B'", "C'"], ['A', 'B', "B'", "A'"], ['B', 'C', "C'", "B'"], ['C', 'A', "A'", "C'"],
              ['A', 'B', "C'"], ["A'", 'B', 'C'], ['A', 'M', "A'"]]   # review MINOR-1: Q through midpoint M
    lines = [['A', 'B'], ['B', 'C'], ['A', "A'"], ['B', "B'"], ["A'", 'B'], ['A', "C'"], ["B'", 'C']]
    mids = (('M', ('B', 'C')), ('N', ("A'", "B'")))
    text = f"Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = {b}, AC = {c} và AA' = {h}. "
    prem = [{'kind': 'right_prism', 'args': {'base': list('ABC'), 'top': ["A'", "B'", "C'"]},
             'quote': "Cho hình lăng trụ đứng ABC.A'B'C'", 'solid_id': 's1'},
            {'kind': 'right_angle', 'args': {'vertex': 'A', 'rays': ['B', 'C']}, 'quote': 'đáy ABC là tam giác vuông tại A',
             'solid_id': 's1'},
            {'kind': 'segment_length', 'args': {'segment': ['A', 'B'], 'value': str(b)}, 'quote': f'AB = {b}', 'solid_id': 's1'},
            {'kind': 'segment_length', 'args': {'segment': ['A', 'C'], 'value': str(c)}, 'quote': f'AC = {c}', 'solid_id': 's1'},
            {'kind': 'segment_length', 'args': {'segment': ['A', "A'"], 'value': str(h)}, 'quote': f"AA' = {h}", 'solid_id': 's1'}]
    return f'prism({b},{c},{h})', 'prism', "ABC.A'B'C'", "Cho hình lăng trụ đứng ABC.A'B'C'", "hình lăng trụ ABC.A'B'C'", V, E, planes, lines, mids, text, prem


def cases():
    for topo in (pyramid(2, 2), pyramid(4, 3), prism(3, 4, 2)):
        name, kind, notation, solid_q, solid_name, V0, E, planes, lines, mids, base, prem0 = topo
        V = dict(V0)
        prem = list(prem0)
        intro = ''
        for lbl, (a, b) in mids:
            V[lbl] = mid(V0[a], V0[b])
            intro += f'Gọi {lbl} là trung điểm của {a}{b}. '
            prem.append({'kind': 'midpoint', 'args': {'point': lbl, 'segment': [a, b]},
                         'quote': f'Gọi {lbl} là trung điểm của {a}{b}', 'solid_id': 's1'})
        area_q = f'Xác định thiết diện của {solid_name} cắt bởi (P) và tính diện tích thiết diện đó'
        faces = [frozenset(p) for p in planes]
        combos = [((x, y), fam, ref) for x, y in itertools.combinations(list(V), 2)
                  for fam, ref in [('F1', q) for q in planes] + [('F2', ln) for ln in lines]]
        # F3: three stated points AND ⊥ Q — over-determined: a plane exists only if the three points' plane is ⊥ Q
        combos += [(xyz, 'F3', q) for xyz in itertools.combinations(list(V), 3) for q in (planes[0], planes[2], planes[-1])]
        for pts_, fam, ref in combos:
            if fam == 'F3':
                s = f'Mặt phẳng (P) đi qua {", ".join(pts_)} và vuông góc với ({"".join(ref)})'
                cons = [{'kind': 'contains_points', 'operands': list(pts_)},
                        {'kind': 'perpendicular_to_plane', 'operands': list(ref)}]
                verdict, a2 = oracle(V, E, faces, list(pts_), normal_of=ref)
                x, y = pts_[:2]
            else:
                x, y = pts_
            if fam == 'F1':
                s = f'Mặt phẳng (P) đi qua {x}, {y} và vuông góc với ({"".join(ref)})'
                cons = [{'kind': 'contains_points', 'operands': [x, y]},
                        {'kind': 'perpendicular_to_plane', 'operands': list(ref)}]
                verdict, a2 = oracle(V, E, faces, [x, y], normal_of=ref)
            elif fam == 'F2':
                if {x, y} == set(ref):
                    continue
                s = f'Mặt phẳng (P) chứa {x}{y} và song song với {"".join(ref)}'
                cons = [{'kind': 'contains_points', 'operands': [x, y]},
                        {'kind': 'parallel_to_line', 'operands': list(ref)}]
                verdict, a2 = oracle(V, E, faces, [x, y], line=ref)
            text = base + intro + s + '. ' + area_q + '.'
            payload = {'schema_version': 'typed-fact-next/2', 'problem_text': text, 'length_unit': '1',
                       'solids': [{'solid_id': 's1', 'solid_type': kind, 'notation': notation, 'quote': solid_q}],
                       'premises': prem, 'relations': [],
                       'derived_sections': [{'section_id': 'sec1', 'plane_name': 'P', 'target_solid_id': 's1', 'quote': s,
                                             'plane_kind': 'constrained', 'constraints': cons,
                                             'stated_intersections': []}],
                       'simulation_goals': [{'goal_id': 'sg1', 'kind': 'construct_object', 'target_solid_id': 's1',
                                             'quote': solid_q}],
                       'math_goals': [{'goal_id': 'q1', 'kind': 'measurement', 'goal_type': 'area',
                                       'target': {'section_id': 'sec1'}, 'quote': area_q, 'solid_id': 's1'}]}
            P = [V[x] for x in pts_]                          # do the stated points alone span the plane? (oracle)
            spans = any(any(cross(sub(P[i], P[0]), sub(P[j], P[0]))) for i in range(1, len(P)) for j in range(i + 1, len(P)))
            yield {'topology': name, 'family': fam, 'contains': list(pts_), 'ref': list(ref), 'text': text,
                   'payload': payload, 'oracle': verdict, 'oracle_area2': a2, 'witness_needed': not spans, 'V': V}


def composition(route, text, needed=True):
    aux = next((d for d in (route.get('planner') or {}).get('auxiliary') or () if d.get('rule', '').startswith('section(plane defined')), None)
    if aux is None:
        return 'NOT_ESTABLISHED'
    nguon = {w.get('producer') for w in aux.get('witnesses') or ()}
    built = [w for w in aux.get('witnesses') or () if w.get('call') and w.get('foot')
             and not re.search(rf"(?<![\w']){re.escape(w['foot'])}(?![\w'])", text)]
    if built:                                          # constructed, and NECESSARY: the stated points do not span
        return 'RULE_PARAMETER_CONSTRUCTED_NORMAL' if needed else 'VERIFICATION_WITNESS_ONLY'
    if 'premise' in nguon:
        return 'RULE_PREMISE_NORMAL' if needed else 'VERIFICATION_WITNESS_ONLY'
    return 'RULE_STATED_LINE'


def _foot_is_vertex(V, z, q):
    a, b, c = (V[x] for x in q[:3])
    n = cross(sub(b, a), sub(c, a))
    t = dot(sub(V[z], a), n) / dot(n, n)
    h = tuple(x - t * y for x, y in zip(V[z], n))
    return any(h == V[v] for v in V)


def run_all(rows_out=None):
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    from app.ai.typed_fact_next_extraction import ReplayExtractor
    policy = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})
    rows = []
    for c in cases():
        out = run_hybrid_offline(c['text'], ReplayExtractor({c['text']: c['payload']}), policy=policy).response
        route = out['route_d']
        served = route['status'] == 'SERVED'
        got = [squared(str(v.get('coef'))) for v in (route.get('answer_exact') or {}).values()] if served else None
        if served:
            verdict = 'SERVED_CORRECT' if c['oracle'] == 'UNIQUE' and got == [c['oracle_area2']] else 'WRONG_SERVED'
        else:
            verdict = 'CORRECT_REFUSAL' if c['oracle'] != 'UNIQUE' else 'REACHABLE_REFUSED'
        tel = (route.get('planner') or {}).get('search_telemetry') or {}
        aux = next((d for d in (route.get('planner') or {}).get('auxiliary') or () if 'witnesses' in d), {})
        rows.append({k: c[k] for k in ('topology', 'family', 'contains', 'ref', 'oracle')} | {
            'oracle_area2': str(c['oracle_area2']) if c['oracle_area2'] is not None else None, 'status': route['status'],
            'code': out['envelope'].get('reason_code'), 'verdict': verdict,
            'witness_needed': c['witness_needed'],
            'composition': composition(route, c['text'], c['witness_needed']) if served else None,
            'planner_label': tel.get('classification') if served else None,
            'normal_search': (aux.get('search') or {}).get('subgoals') if served else None,
            'foot_is_vertex': any(_foot_is_vertex(c['V'], w['point'], c['ref']) for w in aux.get('witnesses') or ()
                                  if w.get('call')) if served else None})
    return rows


if __name__ == '__main__':
    rows = run_all()
    served = [r for r in rows if r['status'] == 'SERVED']
    summary = {'cases': len(rows), 'verdicts': dict(collections.Counter(r['verdict'] for r in rows)),
               'oracle': dict(collections.Counter(r['oracle'] for r in rows)),
               'refusal_codes_by_oracle': {o: dict(collections.Counter(r['code'] for r in rows if r['oracle'] == o and r['status'] != 'SERVED'))
                                           for o in sorted({r['oracle'] for r in rows})},
               'c15_rule_label_of_served': {'REGISTERED_DECOMPOSITION': len(served), 'DISCOVERED_FUNCTION_COMPOSITION': 0},
               'composition_of_served': dict(collections.Counter(r['composition'] for r in served)),
               'constructed_normal_foot_is_a_vertex': sum(bool(r['foot_is_vertex']) for r in served
                                                         if r['composition'] == 'RULE_PARAMETER_CONSTRUCTED_NORMAL'),
               'planner_label_vs_composition': dict(collections.Counter(f"{r['planner_label']} | {r['composition']}" for r in served))}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    if len(sys.argv) > 1:
        import subprocess
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
            json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'provider_calls': 0, 'head': head,
                       'summary': summary, 'rows': rows}, f, ensure_ascii=False, indent=1)
            f.write('\n')
