"""Exploratory: locked V2 distance malformed target8 and scope-key variants on a4 (locked route) plus a3/pl."""
import json, sys
from copy import deepcopy
sys.path.insert(0, 'tests/geometry')
import test_typed_fact_next_v2_distance_bridge as D
from app.ai import adapter3_simulation as A
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_typed_fact_next_planner_route

ASK = "Tính khoảng cách từ A' đến mặt phẳng (ABC)."
variants = {'target8_solid_pr': {"point": "A'", "plane": ["A", "B", "C"], "solid": "pr"},
            'solid_id_pr': {"point": "A'", "plane": ["A", "B", "C"], "solid_id": "pr"},
            'solid_foreign': {"point": "A'", "plane": ["A", "B", "C"], "solid": "zz"},
            'control_no_scope': {"point": "A'", "plane": ["A", "B", "C"]}}
out = {}
for name, t in variants.items():
    p = D._prism(ask=(ASK, t))
    v1 = {**deepcopy(p), 'schema_version': 'typed-fact-next/1'}
    res = {'a4': run_typed_fact_next_v2_route(deepcopy(p))}
    for r, f in (('a3', A.run_typed_fact_next_route), ('pl', run_typed_fact_next_planner_route)):
        try: res[r] = f(deepcopy(v1))
        except Exception as e: res[r] = type('X', (), {'status': 'EXC', 'code': type(e).__name__})()
    out[name] = {r: [x.status, x.code] for r, x in res.items()}
print(json.dumps(out))
