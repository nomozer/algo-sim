import json, hashlib, collections
from pathlib import Path, PureWindowsPath
ROOT = Path('D:/Documents/projects/algo-sim/.superpowers/worktrees/w3-f2-ratio-projection-language-grounding/docs/evaluation')
h=json.load(open('corpus-head.json')); m=json.load(open('corpus-prev-emulated.json'))
changed={k for k,v in h.items() if m[k]['code']!=v['code'] and not v['own_run']}
def walk(x):
    if isinstance(x, dict):
        if x.get('schema_version') in ('typed-fact-next/1','typed-fact-next/2') and 'solids' in x: yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x, list):
        for v in x: yield from walk(v)
shapes=collections.Counter()
for f in sorted({h[k]['file'] for k in changed}):
    for p in walk(json.loads((ROOT/f).read_text(encoding='utf-8'))):
        k=hashlib.sha256(json.dumps(p, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
        if k in changed:
            for g in p.get('math_goals',[]):
                if g.get('kind')=='measurement':
                    t=g['target']; refs=[r for v in t.values() if isinstance(v,list) for r in v]
                    reg=any(set(t)==set(a) for a in {'distance':[['segment'],['point','plane'],['point','line'],['line1','line2'],['line','plane'],['plane1','plane2']],'angle':[['line','plane'],['line1','line2'],['plane1','plane2']],'volume':[['solid'],['solid_id']],'radius':[['solid'],['section_id']],'lateral_area':[['solid']],'area':[['polygon'],['section_id'],['solid']]}[g['goal_type']])
                    shapes[(PureWindowsPath(f).name, g['goal_type'], tuple(sorted(t)), 'registered' if reg else 'UNREGISTERED', str(refs) if reg else '')]+=1
for s,n in sorted(shapes.items()): print(n, s)
