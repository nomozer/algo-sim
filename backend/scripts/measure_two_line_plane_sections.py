"""Replay preregistered two-line corpus via real Hybrid route and independent exact oracle; no live AI.

Run --split heldout only after product freeze. Refuse existing output directories.
"""
import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
os.environ.setdefault('ALLOW_LIVE_AI', '0')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--split', choices=('development','heldout'), required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit('refusing to overwrite output')
    from app.ai.function_route import run_fact_route
    from tests.geometry.test_two_line_plane_section import problem, assert_oracle_geometry
    from freeze_evaluation_candidate import build
    identity = build()
    candidate = json.loads((ROOT/'docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json').read_text(encoding='utf-8'))
    assert identity['measured_system'] == candidate['measured_system']
    assert identity['product_commit_sha'] == candidate['product_commit_sha']
    path = ROOT/'docs/evaluation/geometry/runs/two-line-plane-section/inputs'/('heldout.json' if args.split=='heldout' else 'math-corpus.json')
    rows = json.loads(path.read_text(encoding='utf-8'))['cases']
    totals = Counter(); groups = {}; results = []; failures = []
    for i,row in enumerate(rows):
        r = run_fact_route(*problem(row['family'],row['mid'],row['lines']))
        positive = row['expected']=='SERVED'
        outcome = ('correct_served' if positive else 'wrong_served') if r.status=='SERVED' else ('false_refusal' if positive else 'correct_refusal')
        exact = None
        if positive and r.status=='SERVED':
            try:
                assert_oracle_geometry(r,row)
                exact = 'PASS'
            except AssertionError:
                outcome = 'wrong_served'; exact = 'FAIL'
        if outcome in ('wrong_served','false_refusal') or (not positive and row['expected']!='NO_POLYGON' and r.code!=row['expected']):
            failures.append(i)
        totals[outcome] += 1
        stratum = 'positive' if positive else 'boundary'
        groups.setdefault(stratum,Counter())[outcome] += 1
        results.append({'index':i,'family':row['family'],'stratum':stratum,'expected':row['expected'],
                        'status':r.status,'code':r.code,'outcome':outcome,'oracle':exact,'answers':r.answers})
    args.out.mkdir(parents=True)
    report = {'schema':'two_line_measurement/1','split':args.split,'cases':len(rows),
              'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'product_commit':identity['product_commit_sha'],
              'candidate':identity['measured_system']['tree_hash'],'live_calls':0,
              'oracle':'exact facet-pair halfspace intersections + projected convex hull + Gram area; same author, different algorithm',
              'counts':dict(totals),'groups':{k:dict(v) for k,v in groups.items()},'failures':failures,'rows':results}
    (args.out/'metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('split','cases','counts','failures')}))
    return bool(failures)


if __name__=='__main__':
    sys.exit(main())
