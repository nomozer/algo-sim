"""Continuation 18 — the Registry's capability graph, read from its planning contracts (no hand table): which function
contract produces each effect kind, which consumes it as an input, and every TYPE-compatible chain
`Effect(A) → Need(B) → … → Answer` up to three producers deep. Type compatibility only: a chain listed here is not
claimed to be mathematically feasible — preconditions, existence and exact verification are the engine's (and the
probes measure them). Definitions (`POINT_DEFINITIONS`) are listed with the locus need they regress into.
Usage: contract_graph.py [out.json]   (offline, 0 provider calls)
"""
import collections, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[5] / 'backend'))
from app.simulation.geometry_functions.registry import POINT_DEFINITIONS, REGISTRY, planning_contracts  # noqa: E402


def contracts():
    """A `Point` input may be a DESCRIBED point, so it is a need produced by descriptor contracts (`Point*`); a
    definition is a pseudo-producer of `Point*` whose inputs are two of its loci, met by the `Point ← Line, Line` contract."""
    for s in sorted(REGISTRY.values(), key=lambda s: s.name):
        for c in planning_contracts(s):
            yield {'fn': s.name, 'effect': 'Point*' if c.descriptor else c.effect.kind,
                   'inputs': ['Point*' if t.kind == 'Point' else t.kind for t in c.inputs], 'policy': c.source_policy,
                   'descriptor': c.descriptor, 'free': list(c.free), 'requires': [list(r) for r in c.requires]}
    for k in POINT_DEFINITIONS:
        yield {'fn': f'definition:{k}', 'effect': 'Point*', 'inputs': ['PerpLine', 'PerpLine'], 'policy': 'point_definition',
               'descriptor': k, 'free': [], 'requires': []}


LEAVES = {'Line', 'Plane'}       # a named line / labelled plane is a leaf; a point is a label (leaf) or a description


def graph():
    cs = list(contracts())
    producers = collections.defaultdict(list)
    for i, c in enumerate(cs):
        producers[c['effect']].append(i)
    edges = sorted({(cs[p]['fn'] + ':' + cs[p]['effect'], c['fn'] + ':' + c['effect'])
                    for c in cs for k in c['inputs'] if k not in LEAVES for p in producers.get(k, ())})

    def chains(i, depth):
        nonleaf = [k for k in cs[i]['inputs'] if k not in LEAVES]
        if not nonleaf or depth == 0:
            return [[i]]
        out = []
        for k in nonleaf:
            for p in producers.get(k, ()):
                out += [[i] + ch for ch in chains(p, depth - 1)]
        return out or [[i]]
    answers = [i for i, c in enumerate(cs) if c['effect'].startswith('Answer')]
    multi = sorted({' → '.join(f"{cs[j]['fn']}:{cs[j]['effect']}" for j in reversed(ch))
                    for i in answers for ch in chains(i, 3) if len(ch) > 1})
    return {'contracts': cs, 'producers_by_effect': {k: [cs[i]['fn'] for i in v] for k, v in sorted(producers.items())},
            'edges_effect_to_need': edges, 'multi_step_type_chains_to_an_answer': multi,
            'definitions': {k: {'phrase': d.contract.phrase, 'loci': [{'through': l.through, 'perp': l.perp} for l in d.loci],
                                'regresses_into': 'PerpLine', 'realized_by_function': None}
                            for k, d in POINT_DEFINITIONS.items()}}


if __name__ == '__main__':
    g = graph()
    print(json.dumps({'contracts': len(g['contracts']), 'effects': list(g['producers_by_effect']),
                      'edges': len(g['edges_effect_to_need']), 'multi_step_chains': len(g['multi_step_type_chains_to_an_answer'])},
                     ensure_ascii=False))
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
            json.dump(g, f, ensure_ascii=False, indent=1)
            f.write('\n')
