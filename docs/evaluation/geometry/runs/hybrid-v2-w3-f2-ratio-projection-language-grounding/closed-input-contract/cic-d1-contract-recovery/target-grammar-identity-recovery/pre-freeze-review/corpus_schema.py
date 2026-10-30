"""Schema-only sweep: every embedded typed-fact-next payload in committed docs/evaluation JSON (read from the HEAD worktree),
parsed by the given backend tree. Usage: corpus_schema.py <backend_dir> <out.json>"""
import hashlib, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
BACKEND, OUT = sys.argv[1:3]
sys.path.insert(0, BACKEND)
from app.simulation.geometry_functions import typed_fact_next as T
ROOT = Path('D:/Documents/projects/algo-sim/.superpowers/worktrees/w3-f2-ratio-projection-language-grounding/docs/evaluation')
SKIP = 'target-grammar-identity-recovery'   # the task's own negatives

def walk(x):
    if isinstance(x, dict):
        if x.get('schema_version') in ('typed-fact-next/1', 'typed-fact-next/2') and 'solids' in x:
            yield x
        for v in x.values():
            yield from walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk(v)

res = {}
for f in ROOT.rglob('*.json'):
    if f.stat().st_size > 30_000_000:
        continue
    try:
        data = json.loads(f.read_text(encoding='utf-8'))
    except Exception:
        continue
    for p in walk(data):
        key = hashlib.sha256(json.dumps(p, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
        if key in res:
            continue
        parse = T.parse_typed_fact_next_v2 if p['schema_version'].endswith('/2') else T.parse_typed_fact_next
        try:
            parse(json.loads(json.dumps(p))); code = None
        except T.TypedFactNextValidationError as e:
            code = e.code
        except Exception as e:
            code = 'EXC:' + type(e).__name__
        res[key] = {'file': str(f.relative_to(ROOT)), 'own_run': SKIP in str(f), 'code': code}
Path(OUT).write_text(json.dumps(res, indent=0), encoding='utf-8')
print(len(res), 'payloads')
