"""Twelfth continuation (§IX usage evidence): how often do authored corpora phrase a goal through an UNNAMED described
point ("khoảng cách từ trung điểm của SC đến (ABCD)")? A regex FILTER over every `problem_text` / `text` string of the
run inputs and independent-run JSON files that mentions a polyhedron; sentences opening with Gọi/Lấy/Cho (which name
the point) are skipped. The `text` field of some runs holds model OUTPUT JSON, so hits are grouped by DISTINCT matched
sentence and listed for hand reading — the counts in the report are those distinct problems, read by hand.
Offline, no imports from the product. Usage: described_point_usage_scan.py [out.json]   (run from the repository root)
"""
import glob, json, re, sys

PAT = re.compile(r'(từ|nối|đến|giữa|và|qua|của)\s+(điểm\s+)?(trung điểm|trọng tâm|hình chiếu( vuông góc)?|giao điểm)\s+'
                 r'(của|cạnh|đoạn|[A-Z])', re.I)
SOLIDS = ('hình chóp', 'lăng trụ', 'tứ diện', 'hình hộp', 'lập phương')


def strings(v):
    if isinstance(v, dict):
        for k, x in v.items():
            if k in ('problem_text', 'text') and isinstance(x, str):
                yield x
            else:
                yield from strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from strings(x)


files = sorted({f.replace(chr(92), '/') for f in glob.glob('docs/evaluation/geometry/runs/*/inputs/*.json')
                + glob.glob('docs/evaluation/geometry/runs/*independent*/**/*.json', recursive=True)})
runs = {}
for f in files:
    try:
        data = json.load(open(f, encoding='utf-8'))
    except (OSError, ValueError):
        continue
    run = f.split('/runs/')[1].split('/')[0]
    r = runs.setdefault(run, {'texts': set(), 'matched_sentences': set()})
    for t in strings(data):
        if not any(w in t.lower() for w in SOLIDS):
            continue
        r['texts'].add(t)
        for m in re.finditer(r'[^.?!"\n]*' + PAT.pattern + r'[^.?!"\n]*', t, re.I):
            s = m.group(0).strip()
            if not re.match(r'(Gọi|Lấy|Cho)\b', s):
                r['matched_sentences'].add(s)

out = {k: {'distinct_texts_mentioning_a_polyhedron': len(v['texts']),
           'distinct_matched_sentences': sorted(v['matched_sentences'])} for k, v in sorted(runs.items())}
for k, v in out.items():
    print(f"{k:62s} texts={v['distinct_texts_mentioning_a_polyhedron']:4d} matched={len(v['distinct_matched_sentences'])}")
if len(sys.argv) > 1:
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'method': 'regex filter, hand-read',
                   'runs': out}, f, ensure_ascii=False, indent=1)
        f.write('\n')
