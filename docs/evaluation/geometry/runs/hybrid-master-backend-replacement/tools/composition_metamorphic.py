"""Continuation 18 — metamorphic relations of the composition corpus on `/4` (no hand-picked cases: every non-degenerate
case of the first pyramid and the prism). The answer must not move under:
  rename      every label renamed (pyramid S.ABCD, M, N → K.PQRT, U, V; prism ABC.A'B'C', M, N → EFG.E'F'G', U, V);
  order       the triangle's vertices written in the reverse order ("tam giác MDC" for "tam giác CDM");
  premises    the premises listed in reverse order.
Scored against the oracle's own answer for the ORIGINAL case.
Usage: composition_metamorphic.py [out.json]   (`IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC`, 0 provider calls)
"""
import collections, copy, json, re, sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import composition_probe as P  # noqa: E402
import composition_oracle as O  # noqa: E402

RENAME = {'pyramid(2,2)': {'S': 'K', 'A': 'P', 'B': 'Q', 'C': 'R', 'D': 'T', 'M': 'U', 'N': 'V'},
          'prism(3,4,2)': {'A': 'E', 'B': 'F', 'C': 'G', "A'": "E'", "B'": "F'", "C'": "G'", 'M': 'U', 'N': 'V'}}
_CLUSTER = re.compile(r"(?<![A-Za-zÀ-ỹ])(?:[A-Z]'?)+(?![a-zà-ỹ])")      # a run of labels: "ABC", "A'B'", "BC'M"


def _ren_text(s, m):
    return _CLUSTER.sub(lambda x: ''.join(m.get(t, t) for t in re.findall(r"[A-Z]'?", x[0])), s)


def _ren(v, m):
    if isinstance(v, str):
        return m.get(v, _ren_text(v, m) if ' ' in v or '.' in v else v)
    if isinstance(v, list):
        return [_ren(x, m) for x in v]
    if isinstance(v, dict):
        return {k: (_ren_text(x, m) if k in ('quote', 'problem_text', 'notation') else _ren(x, m)) for k, x in v.items()}
    return v


def variants(c):
    m = RENAME.get(c['topology'])
    if m:
        p = _ren(copy.deepcopy(c['payload']), m)
        yield 'rename', p['problem_text'], p
    tri = c['triangle']
    old, new = ''.join(tri), ''.join(tri[::-1])
    p = copy.deepcopy(c['payload'])
    p['problem_text'] = p['problem_text'].replace(f'tam giác {old}', f'tam giác {new}')
    p['math_goals'][0]['quote'] = p['math_goals'][0]['quote'].replace(f'tam giác {old}', f'tam giác {new}')
    p['described_points'][0].update(quote=p['described_points'][0]['quote'].replace(f'tam giác {old}', f'tam giác {new}'),
                                    polygon=tri[::-1])
    yield 'order', p['problem_text'], p
    p = copy.deepcopy(c['payload'])
    p['premises'] = p['premises'][::-1]
    yield 'premises', p['problem_text'], p


if __name__ == '__main__':
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    from app.ai.typed_fact_next_extraction import ReplayExtractor
    policy = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})
    rows = []
    for c in O.cases(topologies=(O.TOPOLOGIES[0], O.TOPOLOGIES[2]), search=False):
        if c['necessity'] == 'DEGENERATE_TRIANGLE':
            continue
        for rel, text, payload in variants(c):
            route = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=policy).response['route_d']
            got = ([P.squared(str(v.get('coef'))) for v in (route.get('answer_exact') or {}).values()]
                   if route['status'] == 'SERVED' else None)
            rows.append({'id': c['id'], 'relation': rel, 'status': route['status'],
                         'holds': got == [F(c['want2'])], 'code': (route.get('refusal') or {}).get('code')})
    s = {'cases': len(rows), 'holds': dict(collections.Counter(f"{r['relation']}|{r['holds']}" for r in rows)),
         'refusals': dict(collections.Counter(f"{r['relation']}|{r['code']}" for r in rows if r['status'] != 'SERVED'))}
    print(json.dumps(s, ensure_ascii=False, indent=1))
    if len(sys.argv) > 1:
        import subprocess
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=P.ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--', 'backend'], cwd=P.ROOT, text=True).strip())
        with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
            json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'provider_calls': 0, 'head': head,
                       'backend_tree_dirty': dirty, 'summary': s, 'rows': rows}, f, ensure_ascii=False, indent=1)
            f.write('\n')
