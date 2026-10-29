import json, sys
from pathlib import Path
D = Path(__file__).parent
H, M, P = (json.loads((D / f'out_{n}.json').read_text(encoding='utf-8')) for n in ('head', 'main', 'pre'))
C = json.loads((D / 'cases_probe.json').read_text(encoding='utf-8'))
SCOPE = {'solid', 'solid_id'}
INTERNAL = {'ADAPTER_INTERNAL_ERROR', 'ROUTE_INTERNAL_ERROR', 'EXCEPTION'}
lines = []
def out(*a): lines.append(' '.join(str(x) for x in a))
geo_scope_served, internal, losses, unexpected_serve, schema_route_mismatch, diffs = [], [], [], [], [], []
for name, c in C.items():
    h = H[name]; exp = c['expect']
    tgt = c['payload']['math_goals'][-1].get('target') or {}
    operands = set(tgt) - SCOPE if isinstance(tgt, dict) else set()
    for r in ('a3', 'pl', 'a4'):
        st, code = h[r][0], h[r][1]
        if st == 'EXCEPTION' or code in INTERNAL:
            internal.append((name, r, code, h[r][3]))
        if st == 'SERVED' and operands and set(tgt) & SCOPE:
            geo_scope_served.append((name, r))
        if st == 'SERVED' and exp == 'REFUSE':
            unexpected_serve.append((name, r, h[r][2]))
        for tn, T in (('main', M), ('pre', P)):
            if T[name][r][0] == 'SERVED' and st != 'SERVED':
                losses.append((name, r, tn, code, h[r][3][:120]))
            if T[name][r][0] == 'SERVED' and st == 'SERVED' and T[name][r][2] != h[r][2]:
                diffs.append((name, r, tn, T[name][r][2], h[r][2]))
    if h['schema1'] != h['schema2']:
        schema_route_mismatch.append((name, h['schema1'], h['schema2']))
    if h['schema1'] is not None and any(h[r][1] != h['schema1'] for r in ('a3', 'pl')):
        schema_route_mismatch.append((name, 'route!=schema', h['schema1'], [h[r][1] for r in ('a3', 'pl', 'a4')]))
out('cases', len(C))
for title, rows in (('GEOMETRIC TARGET + SCOPE KEY SERVED', geo_scope_served), ('INTERNAL/EXCEPTION', internal),
                    ('EXPECTED-REFUSE BUT SERVED', unexpected_serve), ('SERVED ON BASELINE, NOT ON HEAD', losses),
                    ('SERVED BOTH, ANSWER DIFFERS', diffs), ('SCHEMA /1 vs /2 or route vs schema mismatch', schema_route_mismatch)):
    out(f'\n## {title}: {len(rows)}')
    for row in rows:
        out('  ', json.dumps(row, ensure_ascii=False))
out('\n## FULL TABLE name | schema1 schema2 | a3 | pl | a4 || main a3/pl/a4 || pre a3/pl/a4')
f = lambda x: f"{x[0][:3]}:{x[1]}"
for name in C:
    h = H[name]
    out(name, '|', h['schema1'], h['schema2'], '|', f(h['a3']), f(h['pl']), f(h['a4']), '|| M', f(M[name]['a3']), f(M[name]['pl']), f(M[name]['a4']),
        '|| P', f(P[name]['a3']), f(P[name]['pl']), f(P[name]['a4']))
(D / 'analysis.txt').write_text('\n'.join(lines), encoding='utf-8')
print('\n'.join(lines[: lines.index(next(l for l in lines if l.startswith('\n## FULL')))]))
