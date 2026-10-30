import json, sys
from pathlib import Path
H = Path(__file__).parent
R = {k: json.loads((H / f'out-{k}.json').read_text(encoding='utf-8')) for k in ('head', 'main', 'pre')}
def cell(r):
    s = r['status'][0] + ':' + str(r['code'] or '')
    if r['status'] == 'SERVED':
        s += '=' + ','.join(f"{v['coef']}{'a^'+str(v['dim']) if v.get('unit') else ''}" for k, v in (r.get('answer') or {}).items() if k == 'rv')
    if r.get('leak'):
        s += ' LEAK'
    if r['status'] == 'EXCEPTION':
        s += ' ' + r.get('msg', '')[:60]
    return s
lines = []
for name in R['head']:
    for t in ('head', 'main', 'pre'):
        x = R[t][name]
        lines.append(f"{name:42s} {t:4s} s1={x['schema1']} s2={x['schema2']} | a3 {cell(x['a3'])} | pl {cell(x['pl'])} | a4 {cell(x['a4'])}")
    lines.append('')
out = '\n'.join(lines)
(H / 'table.txt').write_text(out, encoding='utf-8')
print(out)
