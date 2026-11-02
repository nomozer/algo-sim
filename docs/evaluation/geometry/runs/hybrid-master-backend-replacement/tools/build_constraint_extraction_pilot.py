"""Continuation 18 — a SMALL development diagnostic for live extraction of what C17 and C18 opened in `typed-fact-next/2`:
a plane given only by constraints (`plane_kind = "constrained"`) and a point given only by a property (`orthocenter`,
`circumcenter`). Builds the corpus with its gold extractions and replays the gold OFFLINE through `/4` (0 provider calls);
it never calls a provider. A live run needs its own Owner approval (`constraint-extraction-pilot-protocol.md`).

Strata (16 cases = 16 requests):
  K-A  4  a constrained plane the oracle calls UNIQUE (contains points + ⊥ a face / ∥ an edge)            → SERVED
  K-B  2  constraints that fix no plane (NOT_UNIQUE) or contradict (NO_PLANE)                             → REFUSED
  K-C  6  a centre named by its property, composition NECESSARY by the oracle (both topologies, both kinds)→ SERVED
  K-D  2  a centre of a collinear triple                                                                  → REFUSED
  K-E  2  an ambiguous reference ("một mặt bên", "một tam giác") the model must not resolve itself       → CLARIFY
Gold rows come from the C17 generator (`constraint_witness_probe.cases`) and the C18 generator
(`composition_oracle.cases`), each scored by its own independent oracle; the selection rule is fixed below (first rows of
each stratum in generator order), never by looking at a model's output.
Usage: build_constraint_extraction_pilot.py <corpus.json> [gold_replay.jsonl]   (refuses to overwrite)
"""
import copy, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import composition_probe as P  # noqa: E402  (offline guard, backend path)
import composition_oracle as O  # noqa: E402
import constraint_witness_probe as CW  # noqa: E402


def corpus():
    cw = list(CW.cases())
    out = []

    def take(rows, n, stratum, expect):
        for r in rows[:n]:
            out.append({'id': f"{stratum}{len([x for x in out if x['stratum'] == stratum]) + 1:02d}", 'stratum': stratum,
                        'expected': expect, 'text': r['text'], 'gold': r['payload'],
                        'oracle': None if (v := r.get('oracle_area2') or r.get('want2')) is None else str(v), 'source_row': r.get('id') or f"{r['topology']}|{r['family']}|{r['contains']}|{r['ref']}"})
    take([r for r in cw if r['oracle'] == 'UNIQUE' and r['family'] == 'F1' and r['topology'] == 'pyramid(2,2)'], 2, 'K-A', 'SERVED')
    take([r for r in cw if r['oracle'] == 'UNIQUE' and r['family'] == 'F2' and r['topology'].startswith('prism')], 2, 'K-A', 'SERVED')
    take([r for r in cw if r['oracle'] == 'NOT_UNIQUE'], 1, 'K-B', 'REFUSED')
    take([r for r in cw if r['oracle'] == 'NO_PLANE'], 1, 'K-B', 'REFUSED')
    cc = list(O.cases(search=False))
    for topo in ('pyramid(2,2)', 'prism(3,4,2)'):
        for kind, n in (('orthocenter', 1), ('circumcenter', 2)) if topo.startswith('pyramid') else (('orthocenter', 2), ('circumcenter', 1)):
            take([c for c in cc if c['topology'] == topo and c['center'] == kind and c['necessity'] == 'COMPOSITION_NECESSARY'],
                 n, 'K-C', 'SERVED')
    take([c for c in cc if c['necessity'] == 'DEGENERATE_TRIANGLE' and c['goal'] == 'G1'], 2, 'K-D', 'REFUSED')
    for k, (old, new) in enumerate((('và vuông góc với \\(SCD\\)', 'và vuông góc với một mặt bên'),
                                    ("trực tâm của tam giác [A-Z']+", 'trực tâm của một tam giác có ba đỉnh thuộc hình chóp'))):
        src = out[0] if k == 0 else next(x for x in out if re.search(old, x['text']))
        if not re.search(old, src['text']):
            raise SystemExit(f'K-E source lacks {old!r}')
        out.append({'id': f'K-E{k + 1:02d}', 'stratum': 'K-E', 'expected': 'CLARIFY', 'text': re.sub(old, new, src['text'], 1),
                    'gold': None, 'oracle': None, 'source_row': src['id']})
    return out


if __name__ == '__main__':
    rows = corpus()
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'measurement_class': 'LIVE_DEVELOPMENT_PILOT',
                   'held_out_claim': None, 'provider_calls': 0, 'cases': rows}, f, ensure_ascii=False, indent=1)
        f.write('\n')
    if len(sys.argv) > 2:
        from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
        from app.ai.typed_fact_next_extraction import ReplayExtractor
        policy = hybrid_offline_policy({'HYBRID_ROUTE_D_PREVIEW': '1'})
        with open(sys.argv[2], 'x', encoding='utf-8', newline='\n') as f:
            for r in rows:
                if r['gold'] is None:
                    continue
                route = run_hybrid_offline(r['text'], ReplayExtractor({r['text']: copy.deepcopy(r['gold'])}),
                                           policy=policy).response['route_d']
                ok = (route['status'] == 'SERVED') == (r['expected'] == 'SERVED')
                f.write(json.dumps({'id': r['id'], 'expected': r['expected'], 'status': route['status'],
                                    'code': (route.get('refusal') or {}).get('code'), 'gold_matches_expectation': ok},
                                   ensure_ascii=False) + '\n')
                print(r['id'], r['expected'], route['status'], ok)
