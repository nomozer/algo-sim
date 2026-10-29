"""Schema-parse every TypedFactNext payload found in the HEAD repo corpora, using the CURRENT tree's parser (cwd=<tree>/backend).
Usage: python -B corpus_scan.py <repo_root_for_corpora> <out.json>"""
import json, os, sys
from pathlib import Path
from copy import deepcopy
sys.path.insert(0, os.getcwd())
from app.simulation.geometry_functions import typed_fact_next as T
root = Path(sys.argv[1]); out = {}


def walk(v, ptr):
    if isinstance(v, dict):
        sv = v.get('schema_version')
        if sv in ('typed-fact-next/1', 'typed-fact-next/2') and 'solids' in v:
            yield ptr, v
            return
        for k, x in v.items():
            yield from walk(x, f'{ptr}/{k}')
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from walk(x, f'{ptr}/{i}')


for base in ('docs/evaluation', 'backend/tests'):
    for f in (root / base).rglob('*.json'):
        if f.stat().st_size > 30_000_000:
            continue
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
        except Exception:
            continue
        for ptr, p in walk(data, ''):
            parse = T.parse_typed_fact_next_v2 if p['schema_version'].endswith('/2') else T.parse_typed_fact_next
            try:
                parse(deepcopy(p)); code = None
            except T.TypedFactNextValidationError as e:
                code = e.code + ' | ' + e.detail[:120]
            except Exception as e:
                code = 'EXC ' + type(e).__name__
            out[f'{f.relative_to(root).as_posix()}#{ptr}'] = code
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
print(len(out))
