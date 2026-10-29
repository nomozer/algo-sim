"""A parsed /2 MODEL (as the extraction path hands it over, model_copy with verbatim problem_text) vs the dict path."""
import json, os, sys
from copy import deepcopy
sys.path.insert(0, os.getcwd())
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions import typed_fact_next as T
C = json.load(open('D:/tmp/cic-d1-pre-freeze-review/cases_probe.json', encoding='utf-8'))
for name in ('G.distance.point_plane.plain', 'G.distance.segment.plain', 'G.angle.line_plane.goal_sid', 'G.distance.line_plane.plain'):
    p = {**deepcopy(C[name]['payload']), 'schema_version': 'typed-fact-next/2'}
    d = run_typed_fact_next_v2_route(deepcopy(p))
    src = '  ' + p['problem_text'] + '\n'
    m = T.parse_typed_fact_next_v2(deepcopy(p)).model_copy(update={'problem_text': src})
    r = run_typed_fact_next_v2_route(m)
    print(name, 'dict', d.status, d.code, d.answers, '| model+ws', r.status, r.code, r.answers, '| sha_is_verbatim',
          r.ai.get('source_sha256') == __import__('hashlib').sha256(src.encode()).hexdigest())
