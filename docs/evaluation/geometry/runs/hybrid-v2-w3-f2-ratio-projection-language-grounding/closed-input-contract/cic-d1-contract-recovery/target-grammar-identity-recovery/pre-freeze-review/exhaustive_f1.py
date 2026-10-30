"""Exhaustive child-schema grammar check: every subset of all target keys (+ an unknown key) for every goal_type.
Accepted key sets must equal the independently written registered alternatives (owner F1), nothing more."""
import itertools, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, 'D:/Documents/projects/algo-sim/.superpowers/worktrees/w3-f2-ratio-projection-language-grounding/backend')
from app.simulation.geometry_functions import typed_fact_next as T

REGISTERED = {  # written from the owner decision / contract-audit.md table, not from runtime tables
    'distance': [{'segment'}, {'point', 'plane'}, {'point', 'line'}, {'line1', 'line2'}, {'line', 'plane'}, {'plane1', 'plane2'}],
    'angle': [{'line', 'plane'}, {'line1', 'line2'}, {'plane1', 'plane2'}],
    'volume': [{'solid'}, {'solid_id'}], 'radius': [{'solid'}, {'section_id'}],
    'lateral_area': [{'solid'}], 'area': [{'polygon'}, {'section_id'}, {'solid'}]}
VAL = {'point': "A'", 'segment': ['A', 'B'], 'line': ['A', 'B'], 'line1': ['A', 'B'], 'line2': ["A'", "C'"],
       'plane': ['A', 'B', 'C'], 'plane1': ['A', 'B', 'C'], 'plane2': ["A'", "B'", "C'"], 'polygon': ['A', 'B', 'C'],
       'solid': 'pr', 'solid_id': 'pr', 'section_id': 'sec', 'foo': 'x'}
keys = list(VAL)
bad, n = [], 0
for gt in REGISTERED:
    for r in range(1, len(keys) + 1):
        for combo in itertools.combinations(keys, r):
            n += 1
            g = {'goal_id': 'q', 'kind': 'measurement', 'goal_type': gt, 'quote': 'q', 'target': {k: VAL[k] for k in combo}}
            try:
                T.MathGoalSpec.model_validate(g); ok = True
            except Exception:
                ok = False
            if ok != (set(combo) in REGISTERED[gt]):
                bad.append((gt, combo, ok))
out = {'checked': n, 'mismatches': bad}
Path(__file__).with_name('exhaustive_f1.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
print(n, 'checked; mismatches:', bad)
