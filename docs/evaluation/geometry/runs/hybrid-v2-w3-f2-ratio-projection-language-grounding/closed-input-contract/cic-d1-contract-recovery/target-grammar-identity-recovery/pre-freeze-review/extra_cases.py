import json, hashlib
from pathlib import Path
F = Path('D:/Documents/projects/algo-sim/.superpowers/worktrees/w3-f2-ratio-projection-language-grounding/docs/evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding/closed-input-contract/cic-d1-contract-recovery/pre-freeze-review/cases_extra.json')
h=json.load(open('corpus-head.json')); m=json.load(open('corpus-prev-emulated.json'))
d=json.loads(F.read_text(encoding='utf-8'))
items = d.items() if isinstance(d, dict) else enumerate(d)
for name, c in items:
    p = c.get('payload', c) if isinstance(c, dict) else c
    if not isinstance(p, dict) or 'solids' not in p: continue
    k=hashlib.sha256(json.dumps(p, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    if k in h and h[k]['code']!=m[k]['code']:
        print(name, m[k]['code'], '->', h[k]['code'], [ (g.get('goal_type'), g.get('target'), g.get('solid_id')) for g in p['math_goals'] if g.get('kind')=='measurement'])
