"""Continuation 18 — INDEPENDENT reachability oracle for points defined by a PROPERTY (orthocenter, circumcenter).

No product import. Exact Euclidean coordinates (fractions), written here, not read from the kernel.

The question it answers, per case: can the point the source names only by its property be reached by composing the
Registry's point-producing functions, and is composition NECESSARY?

1. TARGET. X* solves the definition as a linear system (its own arithmetic):
   - orthocenter of ABC: X ∈ (ABC), (X − A)·(B − C) = 0, (X − B)·(C − A) = 0;
   - circumcenter of ABC: X ∈ (ABC), |XA|² = |XB|² = |XC|².
   `satisfies` re-checks the definition, including the third, unused condition.
2. DIRECT. One call of a Registry function on the points the source names (all vertices and stated midpoints of the solid)
   — midpoint, centroid, foot on a line, foot on a plane, translate, line ∩ line, line ∩ plane. If X* is a named point:
   SOURCE_POINT; if one call reaches it: DIRECT_FUNCTION_SOLUTION. Then composition is not necessary.
3. FORWARD SEARCH (the opposite direction of the planner's backward regression). Universe: the triangle's own three
   vertices. Ops: the in-plane point producers above (foot on a plane and line ∩ plane are identities inside the plane).
   Level 1 and level 2 are materialized EXHAUSTIVELY; at level 3 only the final operation is tested against X*:
   line ∩ line, midpoint and foot on a line exactly (direction classes / hashing), translate only with its vector taken
   from level ≤ 1 (the one incomplete check — stated in every verdict).
   Verdict: PROVEN_REACHABLE_WITHIN_BOUND (with a witness plan and its level), or UNKNOWN (never "unreachable": the bound
   is not exhausted at level 3).

Usage: composition_oracle.py [out.json]   (`IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC`, offline, 0 provider calls)
"""
import collections, itertools, json, sys
from fractions import Fraction as F

Z = F(0)


def sub(p, q): return tuple(a - b for a, b in zip(p, q))
def add(p, q): return tuple(a + b for a, b in zip(p, q))
def mul(k, p): return tuple(k * a for a in p)
def dot(p, q): return sum(a * b for a, b in zip(p, q))
def cross(p, q): return (p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0])


def solve3(rows, rhs):
    """Cramer on a 3×3 system; None when singular."""
    def det(m):
        return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
    d = det(rows)
    if d == 0:
        return None
    out = []
    for i in range(3):
        m = [list(r) for r in rows]
        for j in range(3):
            m[j][i] = rhs[j]
        out.append(F(det(m)) / d)
    return tuple(out)


# ── definitions ─────────────────────────────────────────────────────────────────────────────────────────────────────
def target(kind, A, B, C):
    n = cross(sub(B, A), sub(C, A))
    if not any(n):
        return None                                                   # collinear: no triangle
    if kind == 'orthocenter':
        return solve3([n, sub(B, C), sub(C, A)], [dot(n, A), dot(sub(B, C), A), dot(sub(C, A), B)])
    return solve3([n, mul(2, sub(B, A)), mul(2, sub(C, A))], [dot(n, A), dot(B, B) - dot(A, A), dot(C, C) - dot(A, A)])


def satisfies(kind, X, A, B, C):
    n = cross(sub(B, A), sub(C, A))
    if dot(n, sub(X, A)) != 0:
        return False
    if kind == 'orthocenter':
        return all(dot(sub(X, P), sub(Q, R)) == 0 for P, Q, R in ((A, B, C), (B, C, A), (C, A, B)))
    d = [dot(sub(X, P), sub(X, P)) for P in (A, B, C)]
    return d[0] == d[1] == d[2]


# ── the Registry's point producers, re-implemented (Euclidean) ──────────────────────────────────────────────────────
def foot_line(p, a, b):
    d = sub(b, a)
    return add(a, mul(dot(sub(p, a), d) / dot(d, d), d))


def foot_plane(p, a, b, c):
    n = cross(sub(b, a), sub(c, a))
    return sub(p, mul(dot(sub(p, a), n) / dot(n, n), n))


def meet_lines(a, b, c, d):
    u, v, w = sub(b, a), sub(d, c), sub(c, a)
    uv = cross(u, v)
    if not any(uv) or dot(w, uv) != 0:                               # parallel, or skew
        return None
    s = dot(cross(w, v), uv) / dot(uv, uv)
    return add(a, mul(s, u))


def meet_line_plane(a, b, p, q, r):
    n = cross(sub(q, p), sub(r, p))
    den = dot(n, sub(b, a))
    if den == 0:
        return None
    return add(a, mul(dot(n, sub(p, a)) / den, sub(b, a)))


def one_call(pool):
    """Every point ONE Registry call yields from `pool` (label → coords): {coords: (fn, args)} (first found)."""
    out = {}
    labels = list(pool)
    lines = [(a, b) for a, b in itertools.combinations(labels, 2) if pool[a] != pool[b]]
    planes = [t for t in itertools.combinations(labels, 3) if any(cross(sub(pool[t[1]], pool[t[0]]), sub(pool[t[2]], pool[t[0]])))]

    def put(x, how):
        if x is not None:
            out.setdefault(x, how)
    for a, b in lines:
        put(tuple(F(u + v) / 2 for u, v in zip(pool[a], pool[b])), ('midpoint', (a, b)))
    for t in planes:
        put(tuple(sum(pool[x][i] for x in t) / 3 for i in range(3)), ('centroid', t))
    for p in labels:
        for a, b in lines:
            put(foot_line(pool[p], pool[a], pool[b]), ('orthogonal_projection_line', (p, a, b)))
        for t in planes:
            put(foot_plane(pool[p], *(pool[x] for x in t)), ('orthogonal_projection', (p, *t)))
        for a, b in itertools.permutations(labels, 2):
            put(add(pool[p], sub(pool[b], pool[a])), ('translate_point', (p, a, b)))
    for (a, b), (c, d) in itertools.combinations(lines, 2):
        put(meet_lines(pool[a], pool[b], pool[c], pool[d]), ('intersect_line_line', (a, b, c, d)))
    for a, b in lines:
        for t in planes:
            put(meet_line_plane(pool[a], pool[b], *(pool[x] for x in t)), ('intersect_line_plane', (a, b, *t)))
    return out


# ── forward search over the triangle (in-plane producers) ───────────────────────────────────────────────────────────
def _in_plane_ops(pts, fresh):
    """Every in-plane op whose arguments come from `pts` with at least one in `fresh` (or all, when fresh is None)."""
    idx = list(range(len(pts)))
    new = set(fresh) if fresh is not None else set(idx)
    lines = [(i, j) for i, j in itertools.combinations(idx, 2)]
    for i, j in lines:
        if new & {i, j}:
            yield tuple(F(u + v) / 2 for u, v in zip(pts[i], pts[j])), ('midpoint', (i, j))
    for t in itertools.combinations(idx, 3):
        if new & set(t):
            yield tuple(sum(pts[x][k] for x in t) / 3 for k in range(3)), ('centroid', t)
    for p in idx:
        for i, j in lines:
            if new & {p, i, j} and p not in (i, j):
                yield foot_line(pts[p], pts[i], pts[j]), ('orthogonal_projection_line', (p, i, j))
        for i, j in itertools.permutations(idx, 2):
            if new & {p, i, j}:
                yield add(pts[p], sub(pts[j], pts[i])), ('translate_point', (p, i, j))
    for (i, j), (k, m) in itertools.combinations(lines, 2):
        if new & {i, j, k, m}:
            x = meet_lines(pts[i], pts[j], pts[k], pts[m])
            if x is not None:
                yield x, ('intersect_line_line', (i, j, k, m))


def forward(kind, tri, names=('A', 'B', 'C')):
    """Forward bounded search from the triangle's vertices (see module doc). Returns the verdict dict."""
    A, B, C = tri
    pts, how, level = [A, B, C], [None, None, None], [0, 0, 0]
    seen = {p: i for i, p in enumerate(pts)}
    xs = target(kind, A, B, C)
    explored = 0

    def plan(i):
        steps, order = {}, []

        def visit(j):
            if how[j] is None or j in steps:
                return
            for a in how[j][1]:
                visit(a)
            steps[j] = len(order)
            order.append(j)
        visit(i)
        name = {0: names[0], 1: names[1], 2: names[2], **{j: f'X{n + 1}' for n, j in enumerate(order)}}
        return [{'out': name[j], 'fn': how[j][0], 'args': [name[a] for a in how[j][1]]} for j in order]

    if xs in seen:
        return {'reach': 'PROVEN_REACHABLE_WITHIN_BOUND', 'level': 0, 'plan': [], 'explored': 0}
    fresh = None
    for lv in (1, 2):
        added = []
        for x, h in _in_plane_ops(pts, fresh):
            explored += 1
            if x not in seen:
                seen[x] = len(pts)
                pts.append(x)
                how.append(h)
                level.append(lv)
                added.append(len(pts) - 1)
        if xs in seen:
            return {'reach': 'PROVEN_REACHABLE_WITHIN_BOUND', 'level': lv, 'plan': plan(seen[xs]), 'explored': explored}
        fresh = added
    # level 3: the FINAL operation only, tested against X*
    found = None
    by_dir = collections.defaultdict(list)                       # line ∩ line: two direction classes through X*
    for i, p in enumerate(pts):
        d = sub(p, xs)
        g = next(v for v in d if v != 0)
        by_dir[tuple(v / g for v in d)].append(i)
    classes = [v for v in by_dir.values() if len(v) >= 2]
    explored += len(pts)
    if len(classes) >= 2:
        (i, j), (k, m) = classes[0][:2], classes[1][:2]
        found = ('intersect_line_line', (i, j, k, m))
    if found is None:                                            # midpoint: the mirror of P through X* is in the pool
        for i, p in enumerate(pts):
            q = sub(mul(2, xs), p)
            if q in seen and seen[q] != i:
                found = ('midpoint', (i, seen[q]))
                break
    if found is None:                                            # foot on a line: X* on line PQ and (R − X*) ⊥ PQ
        for cls in classes[:1] + classes[1:]:
            d = sub(pts[cls[1]], pts[cls[0]])
            r = next((i for i, p in enumerate(pts) if p != xs and dot(sub(p, xs), d) == 0 and i not in cls), None)
            if r is not None:
                found = ('orthogonal_projection_line', (r, cls[0], cls[1]))
                break
    if found is None:                                            # translate, vector from level ≤ 1 only (incomplete)
        small = [i for i in range(len(pts)) if level[i] <= 1]
        diffs = {sub(pts[j], pts[i]): (i, j) for i in small for j in small if i != j}
        for i, p in enumerate(pts):
            if sub(xs, p) in diffs:
                found = ('translate_point', (i, *diffs[sub(xs, p)]))
                break
    if found is None:
        return {'reach': 'UNKNOWN', 'level': None, 'plan': None, 'explored': explored,
                'bound': 'levels 1–2 exhaustive; level-3 final op partial (translate vector from level ≤ 1)'}
    pts.append(xs)
    how.append(found)
    return {'reach': 'PROVEN_REACHABLE_WITHIN_BOUND', 'level': 3, 'plan': plan(len(pts) - 1), 'explored': explored}


# ── topologies, corpus ──────────────────────────────────────────────────────────────────────────────────────────────
def _mid(p, q): return tuple(F(a + b) / 2 for a, b in zip(p, q))


def pyramid(a, h):
    a, h = F(a), F(h)
    V = {'A': (Z, Z, Z), 'B': (a, Z, Z), 'C': (a, a, Z), 'D': (Z, a, Z), 'S': (Z, Z, h)}
    text = (f'Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh {a}, SA vuông góc với mặt phẳng (ABCD) và SA = {h}. ')
    prem = [{'kind': 'regular_polygon', 'args': {'vertices': list('ABCD'), 'side': str(a)},
             'quote': f'đáy ABCD là hình vuông cạnh {a}', 'solid_id': 's1'},
            {'kind': 'perpendicular_line_plane', 'args': {'line': ['S', 'A'], 'plane': list('ABCD')},
             'quote': 'SA vuông góc với mặt phẳng (ABCD)', 'solid_id': 's1'},
            {'kind': 'segment_length', 'args': {'segment': ['S', 'A'], 'value': str(h)}, 'quote': f'SA = {h}', 'solid_id': 's1'}]
    faces = [list('ABCD'), list('SAB'), list('SBC'), list('SCD'), list('SDA')]
    return {'name': f'pyramid({a},{h})', 'kind': 'pyramid', 'notation': 'S.ABCD', 'quote': 'Cho hình chóp S.ABCD',
            'V': V, 'mids': (('M', ('A', 'B')), ('N', ('S', 'C'))), 'text': text, 'prem': prem, 'faces': faces}


def prism(b, c, h):
    b, c, h = F(b), F(c), F(h)
    V = {'A': (Z, Z, Z), 'B': (b, Z, Z), 'C': (Z, c, Z), "A'": (Z, Z, h), "B'": (b, Z, h), "C'": (Z, c, h)}
    text = f"Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = {b}, AC = {c} và AA' = {h}. "
    prem = [{'kind': 'right_prism', 'args': {'base': list('ABC'), 'top': ["A'", "B'", "C'"]},
             'quote': "Cho hình lăng trụ đứng ABC.A'B'C'", 'solid_id': 's1'},
            {'kind': 'right_angle', 'args': {'vertex': 'A', 'rays': ['B', 'C']}, 'quote': 'đáy ABC là tam giác vuông tại A',
             'solid_id': 's1'},
            {'kind': 'segment_length', 'args': {'segment': ['A', 'B'], 'value': str(b)}, 'quote': f'AB = {b}', 'solid_id': 's1'},
            {'kind': 'segment_length', 'args': {'segment': ['A', 'C'], 'value': str(c)}, 'quote': f'AC = {c}', 'solid_id': 's1'},
            {'kind': 'segment_length', 'args': {'segment': ['A', "A'"], 'value': str(h)}, 'quote': f"AA' = {h}", 'solid_id': 's1'}]
    faces = [list('ABC'), ["A'", "B'", "C'"], ['A', 'B', "B'", "A'"], ['B', 'C', "C'", "B'"], ['C', 'A', "A'", "C'"]]
    return {'name': f'prism({b},{c},{h})', 'kind': 'prism', 'notation': "ABC.A'B'C'", 'quote': "Cho hình lăng trụ đứng ABC.A'B'C'",
            'V': V, 'mids': (('M', ('B', 'C')), ('N', ("A'", "B'"))), 'text': text, 'prem': prem, 'faces': faces}


TOPOLOGIES = (pyramid(2, 2), pyramid(4, 3), prism(3, 4, 2))
WORD = {'orthocenter': 'trực tâm của tam giác', 'circumcenter': 'tâm đường tròn ngoại tiếp tam giác'}


def _plane_dist2(x, pl):
    a, b, c = pl[:3]
    n = cross(sub(b, a), sub(c, a))
    return dot(sub(x, a), n) ** 2 / dot(n, n)


def cases(topologies=TOPOLOGIES, search=True):
    """Every triangle of named points (vertices + stated midpoints) × {orthocenter, circumcenter} × two goals:
    G1 the distance from the centre to the first face not containing it; G2 the length from the first named point that is
    neither on the triangle nor the centre. Collinear triples are negative controls."""
    for topo in topologies:
        V = dict(topo['V'])
        prem = list(topo['prem'])
        intro = ''
        for lbl, (a, b) in topo['mids']:
            V[lbl] = _mid(V[a], V[b])
            intro += f'Gọi {lbl} là trung điểm của {a}{b}. '
            prem.append({'kind': 'midpoint', 'args': {'point': lbl, 'segment': [a, b]},
                         'quote': f'Gọi {lbl} là trung điểm của {a}{b}', 'solid_id': 's1'})
        direct = one_call(V)
        for tri in itertools.combinations(list(V), 3):
            for kind in ('orthocenter', 'circumcenter'):
                X = target(kind, *(V[t] for t in tri))
                desc = f"{WORD[kind]} {''.join(tri)}"
                for goal in ('G1', 'G2'):
                    if X is None:
                        face, other = topo['faces'][0], next(v for v in V if v not in tri)
                    else:
                        face = next((f for f in topo['faces'] if _plane_dist2(X, [V[p] for p in f])), None)
                        other = next((v for v in V if v not in tri and V[v] != X), None)
                    if goal == 'G1':
                        if face is None:
                            continue
                        ask = f"Tính khoảng cách từ {desc} đến mặt phẳng ({''.join(face)})"
                        tgt = {'point': '@h1', 'plane': list(face)}
                        want2 = _plane_dist2(X, [V[p] for p in face]) if X is not None else None
                    else:
                        if other is None:
                            continue
                        ask = f'Tính độ dài đoạn thẳng nối điểm {other} với {desc}'
                        tgt = {'segment': [other, '@h1']}
                        want2 = dot(sub(X, V[other]), sub(X, V[other])) if X is not None else None
                    text = topo['text'] + intro + ask + '.'
                    payload = {'schema_version': 'typed-fact-next/2', 'problem_text': text, 'length_unit': '1',
                               'solids': [{'solid_id': 's1', 'solid_type': topo['kind'], 'notation': topo['notation'],
                                           'quote': topo['quote']}],
                               'premises': prem, 'derived_sections': [], 'relations': [],
                               'simulation_goals': [{'goal_id': 'sg1', 'kind': 'construct_object', 'target_solid_id': 's1',
                                                     'quote': topo['quote']}],
                               'math_goals': [{'goal_id': 'q1', 'kind': 'measurement', 'goal_type': 'distance',
                                               'target': tgt, 'quote': ask, 'solid_id': 's1'}],
                               'described_points': [{'described_id': 'h1', 'kind': kind, 'quote': desc,
                                                     'polygon': list(tri)}]}
                    if X is None:
                        cls, fw = 'DEGENERATE_TRIANGLE', None
                    else:
                        assert satisfies(kind, X, *(V[t] for t in tri))
                        src = next((v for v in V if V[v] == X), None)
                        cls = ('SOURCE_POINT' if src else 'DIRECT_FUNCTION_SOLUTION' if X in direct
                               else 'COMPOSITION_NECESSARY')
                        fw = forward(kind, tuple(V[t] for t in tri), tri) if search else None
                    yield {'id': f"{topo['name']}|{kind}|{''.join(tri)}|{goal}", 'topology': topo['name'], 'center': kind,
                           'triangle': list(tri), 'goal': goal, 'text': text, 'payload': payload,
                           'target': [str(v) for v in X] if X is not None else None,
                           'want2': str(want2) if want2 is not None else None, 'necessity': cls,
                           'source_point': next((v for v in V if X is not None and V[v] == X), None),
                           'direct': ({'fn': direct[X][0], 'args': list(direct[X][1])} if X is not None and X in direct
                                      else None),
                           'forward': fw}


def summary(rows):
    return {'cases': len(rows),
            'necessity': dict(collections.Counter(r['necessity'] for r in rows)),
            'forward_reach': dict(collections.Counter((r['forward'] or {}).get('reach', 'n/a') for r in rows)),
            'forward_level_of_necessary': dict(collections.Counter(
                str(r['forward']['level']) for r in rows if r['necessity'] == 'COMPOSITION_NECESSARY')),
            'necessary_by_topology_center': dict(collections.Counter(
                f"{r['topology']}|{r['center']}" for r in rows if r['necessity'] == 'COMPOSITION_NECESSARY')),
            'witness_functions_of_necessary': dict(collections.Counter(
                '+'.join(sorted({s['fn'] for s in r['forward']['plan']})) for r in rows
                if r['necessity'] == 'COMPOSITION_NECESSARY'))}


if __name__ == '__main__':
    rows = list(cases())
    s = summary(rows)
    print(json.dumps(s, ensure_ascii=False, indent=1))
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
            json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'provider_calls': 0,
                       'product_imports': 0, 'summary': s,
                       'rows': [{k: v for k, v in r.items() if k != 'payload'} for r in rows]}, f, ensure_ascii=False, indent=1)
            f.write('\n')
