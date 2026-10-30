import json
from pathlib import Path
H = Path(__file__).parent
R = {k: json.loads((H / f'out-{k}.json').read_text(encoding='utf-8')) for k in ('head', 'main', 'pre')}
def o(r): return (r['status'], r['code'], json.dumps(r.get('answer'), sort_keys=True) if r['status']=='SERVED' else None)
out=[]
for n in R['head']:
    for base in ('main','pre'):
        for rt in ('schema1','schema2','a3','pl','a4'):
            h, b = R['head'][n][rt], R[base][n][rt]
            if rt.startswith('schema'):
                if h != b: out.append(f'{n:40s} vs {base}: {rt} head={h} {base}={b}')
            elif o(h) != o(b):
                tag = 'NEWLY_REFUSED' if b['status']=='SERVED' and h['status']!='SERVED' else ('NEWLY_SERVED' if h['status']=='SERVED' and b['status']!='SERVED' else 'CHANGED')
                out.append(f'{n:40s} vs {base}: {rt} {tag} head={o(h)[:2]} {base}={o(b)[:2]} ans={o(b)[2] if b["status"]=="SERVED" else ""}')
leaks=[(n,t,rt) for t in R for n in R[t] for rt in ('a3','pl','a4') if R[t][n][rt].get('leak') or R[t][n][rt]['status']=='EXCEPTION']
out.append('LEAK_OR_EXCEPTION: '+str(leaks))
served_head_newly=[l for l in out if 'NEWLY_SERVED' in l]
out.append('NEWLY_SERVED_COUNT: %d' % len(served_head_newly))
(H/'diff.txt').write_text('\n'.join(out),encoding='utf-8'); print('\n'.join(out))
