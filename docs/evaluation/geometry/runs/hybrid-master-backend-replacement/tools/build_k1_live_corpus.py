"""Continuation 19 — the K-1 live corpus (constraint-defined planes, points named by a property) in the S-2/R-1 runner's
format, converted from the C18 pilot corpus committed BEFORE any live run (`constraint-extraction-pilot-corpus.json`,
16 cases, selection fixed by `build_constraint_extraction_pilot.py`). Nothing is re-selected here.

Expected outcomes (protocol `constraint-extraction-pilot-protocol.md` §2, in the runner's vocabulary, fixed from the
capability contract, not from any run):
  K-A, K-C  SERVED, oracle = √(oracle square) from the C17 / C18 independent oracles (area, distance);
  K-B01     the stated constraints fix no plane (NOT_UNIQUE)      → REFUSED_UNDERDETERMINED (refusal group MISSING_DATA);
  K-B02     the stated constraints contradict (NO_PLANE)          → REFUSED_INCONSISTENT;
  K-D       a centre of a collinear "triangle" (the givens contradict the word "tam giác") → REFUSED_INCONSISTENT;
  K-E       an ambiguous reference                                 → CLARIFY [AMBIGUOUS, MISSING_DATA]; its gold is the
            honest exit: the source's gold without the ambiguous object and its goal, plus one `unresolved` entry.
Revision before any live run (C19): the first conversion mapped K-B01 to CLARIFY, which contradicts the C18 protocol
(K-B → REFUSED) — only the engine can see that a stated plane is not unique — and wrote no gold for K-E, so the gold
replay had nothing to run. Both were found by the offline gold replay, never by a model output.
Usage: build_k1_live_corpus.py <out.json>   (refuses to overwrite; offline, 0 provider calls)
"""
import json, math, sys
from fractions import Fraction as F
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
SRC = RUN / 'constraint-extraction-pilot-corpus.json'


def exact_sqrt(sq: F) -> str:
    """√(a/b) in the oracle grammar: k√r/q with r square-free."""
    a, b = sq.numerator * sq.denominator, sq.denominator          # √(a/b) = √(a·b)/b
    k, r = 1, a
    for p in range(2, math.isqrt(a) + 1):
        while r % (p * p) == 0:
            r //= p * p
            k *= p
    g = math.gcd(k, b)
    k, b = k // g, b // g
    s = ('' if k == 1 and r != 1 else str(k)) + (f'√{r}' if r != 1 else '')
    return s + (f'/{b}' if b != 1 else '')


def expected(case: dict) -> dict:
    s, cid = case['stratum'], case['id']
    if s in ('K-A', 'K-C'):
        kind = 'area' if s == 'K-A' else 'distance'
        return {'outcome': 'SERVED', 'is_ambiguous': False, 'oracle': {kind: [exact_sqrt(F(case['oracle']))]}}
    if s == 'K-E':
        return {'outcome': 'CLARIFY', 'is_ambiguous': True, 'allowed_clarification_codes': ['AMBIGUOUS', 'MISSING_DATA']}
    if cid == 'K-B01':
        return {'outcome': 'REFUSED_UNDERDETERMINED', 'is_ambiguous': False}
    return {'outcome': 'REFUSED_INCONSISTENT', 'is_ambiguous': False}


#: K-E honest exits: the ambiguous phrase, what is missing, and which readings the extractor saw.
_AMBIGUOUS = {'K-E01': ('vuông góc với một mặt bên', ['target_line_or_plane'], ['perpendicular']),
              'K-E02': ('trực tâm của một tam giác có ba đỉnh thuộc hình chóp', ['goal_object'], [])}


def honest_exit(case: dict, sources: dict) -> dict:
    """The source case's gold minus the ambiguous object (its section / described point) and the goal on it, plus the
    `unresolved` entry; the problem text is K-E's own."""
    g = json.loads(json.dumps(sources[case['source_row']]['gold']))
    quote, roles, rel = _AMBIGUOUS[case['id']]
    assert quote in case['text'], case['id']
    g.update(problem_text=case['text'], derived_sections=[], described_points=[], math_goals=[],
             unresolved=[{'unresolved_id': 'u1', 'kind': 'ambiguous', 'quote': quote, 'missing_roles': roles,
                          'candidate_relations': rel}])
    return g


if __name__ == '__main__':
    assert exact_sqrt(F(9, 2)) == '3√2/2' and exact_sqrt(F(1)) == '1' and exact_sqrt(F(673, 64)) == '√673/8'
    src = json.loads(SRC.read_text(encoding='utf-8'))
    by_id = {c['id']: c for c in src['cases']}
    cases = [{'id': c['id'], 'stratum': c['stratum'], 'source': f"constraint-extraction-pilot-corpus.json ({c['source_row']})",
              'problem_text': c['text'], 'expected': expected(c),
              'gold_extraction': c['gold'] if c['gold'] is not None else honest_exit(c, by_id)} for c in src['cases']]
    out = {'schema': 'k1-live-pilot-corpus/1', 'study': 'K-1', 'measurement_class_if_run_live': 'LIVE_DEVELOPMENT_PILOT',
           'author': 'implementer (agent), eighteenth continuation generators — not independent, not held-out',
           'protocol': 'constraint-extraction-pilot-protocol.md', 'cases': cases}
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(len(cases), [c['expected']['outcome'] for c in cases])
