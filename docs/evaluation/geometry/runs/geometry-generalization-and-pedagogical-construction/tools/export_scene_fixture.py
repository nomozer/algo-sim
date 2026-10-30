"""Export the Scene3D of one served dev case as a frontend fixture (offline, x mode). Usage: export_scene_fixture.py <case>"""
import json, os, sys
from pathlib import Path
W = Path(__file__).resolve().parents[1]; ROOT = W.parents[4]
sys.path.insert(0, str(ROOT / 'backend')); sys.dont_write_bytecode = True; os.environ['ALLOW_LIVE_AI'] = '0'
from app.ai.adapter4_route import run_typed_fact_next_v2_route
cid = sys.argv[1]
r = run_typed_fact_next_v2_route(json.loads((W / 'dev-corpus/cases.json').read_text(encoding='utf-8'))[cid]['payload'])
assert r.status == 'SERVED'
with (W / f'dev-corpus/scene-{cid}.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump({'case': cid, 'scene3d': r.scene3d}, f, ensure_ascii=False, indent=1); f.write('\n')
print('ok', sum(1 for e in r.scene3d['events'] if e.get('justification_text')))
