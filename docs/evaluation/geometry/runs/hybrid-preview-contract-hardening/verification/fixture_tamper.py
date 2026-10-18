"""Fault injection on a COPY of the fixture bundle: change one response field and re-hash the manifest so only the
regeneration comparison of `--verify` can catch it."""
import hashlib
import json
import sys
from pathlib import Path

d = Path(sys.argv[1])
m = json.loads((d / 'manifest.json').read_text(encoding='utf-8'))
f = d / 'refusal-integrity-identity.json'
x = json.loads(f.read_text(encoding='utf-8'))
x['response']['envelope']['failure_category'] = 'capability_gap'
t = json.dumps(x, ensure_ascii=False, sort_keys=True, indent=1) + '\n'
f.write_text(t, encoding='utf-8', newline='\n')
for r in m['fixtures']:
    if r['file'] == f.name:
        r['sha256'] = hashlib.sha256(t.encode()).hexdigest()
(d / 'manifest.json').write_text(json.dumps(m, ensure_ascii=False, sort_keys=True, indent=1) + '\n', encoding='utf-8',
                                 newline='\n')
