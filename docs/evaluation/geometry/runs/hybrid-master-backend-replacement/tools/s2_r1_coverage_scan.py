"""Fourteenth continuation (§5.2): how much of R-1 / planner recomposition can the LOCKED S-2 corpus exercise at all?

Per case: (1) `described_points` declared in its gold extraction; (2) the twelfth-continuation usage regex
(`described_point_usage_scan.py`, same pattern, Gọi/Lấy/Cho sentences skipped) over its problem text — a goal phrased
through an UNNAMED described point; (3) the planner's `search_telemetry.classification` when its gold extraction is
replayed on the production opt-in `/4` path. The S-2 corpus was never in that scan's glob (it is not under `inputs/`).
IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC, offline, 0 provider calls. Usage: s2_r1_coverage_scan.py [out.json]
"""
import collections, json, os, re, socket, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'backend'))
os.environ['ALLOW_LIVE_AI'] = '0'
def _offline(*_a, **_k): raise RuntimeError('OFFLINE_ONLY')
socket.socket.connect = _offline; socket.create_connection = _offline

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402

PAT = re.compile(r'(từ|nối|đến|giữa|và|qua|của)\s+(điểm\s+)?(trung điểm|trọng tâm|hình chiếu( vuông góc)?|giao điểm)\s+'
                 r'(của|cạnh|đoạn|[A-Z])', re.I)          # = described_point_usage_scan.PAT
CORPUS = HERE.parent / 's2-student-language-pilot-corpus.json'
POLICY = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})

rows = []
for c in json.loads(CORPUS.read_text(encoding='utf-8'))['cases']:
    text, gold = c['problem_text'], c.get('gold_extraction')
    unnamed = sorted({m.group(0).strip() for m in re.finditer(r'[^.?!"\n]*' + PAT.pattern + r'[^.?!"\n]*', text, re.I)
                      if not re.match(r'(Gọi|Lấy|Cho)\b', m.group(0).strip())})
    route = {}
    if gold:
        route = run_hybrid_offline(text, ReplayExtractor({text: gold}), policy=POLICY).response['route_d']
    rows.append({'id': c['id'], 'stratum': c['stratum'], 'expected': c['expected']['outcome'],
                 'gold_described_points': len((gold or {}).get('described_points') or []),
                 'unnamed_described_phrasing': unnamed, 'gold_route_status': route.get('status'),
                 'search_classification': ((route.get('planner') or {}).get('search_telemetry') or {}).get('classification')})

summary = {'cases': len(rows),
           'gold_with_described_points': sum(r['gold_described_points'] > 0 for r in rows),
           'texts_with_unnamed_described_phrasing': sum(bool(r['unnamed_described_phrasing']) for r in rows),
           'search_classification_of_gold_served': dict(sorted(collections.Counter(
               str(r['search_classification']) for r in rows if r['gold_route_status'] == 'SERVED').items()))}
print(json.dumps(summary, ensure_ascii=False, indent=1))
if len(sys.argv) > 1:
    import hashlib, subprocess
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--', 'backend/app'], cwd=ROOT, text=True).strip())
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'provider_calls': 0,
                   'corpus_sha256': hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
                   'identity': {'head': head, 'product_uncommitted': dirty}, 'summary': summary, 'rows': rows},
                  f, ensure_ascii=False, indent=1)
        f.write('\n')
