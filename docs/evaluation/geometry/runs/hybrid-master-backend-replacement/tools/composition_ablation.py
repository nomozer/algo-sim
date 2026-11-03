"""Continuation 18 — ablation of the definition regression (monkeypatches in THIS evaluation process only; the product is
untouched). Every arm re-runs the 504 cases of `composition_probe.py` through the production `/4` path and is scored
against the independent oracle.

Arms:
  candidate                 planner /26 as built;
  no_translate_locus        `translate_point`'s PerpLine contract removed (a locus through a point ON its side has no producer);
  no_foot_locus             `orthogonal_projection_line`'s PerpLine contract removed (every locus must be translated);
  no_direction              the PerpDir contract removed (translation has no direction producer);
  no_preconditions          structural preconditions ignored: the cheapest contract is taken even when the point is on the line;
  depth_3                   MAX_EFFECT_DEPTH = 3 (the C17 bound);
  reversed_loci             each definition's loci in reverse order (ties pick another pair of loci);
  no_definitions            POINT_DEFINITIONS emptied (the description has no realization at all).
Usage: composition_ablation.py [out.json]   (`IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC`, 0 provider calls)
"""
import collections, json, sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import composition_probe as P  # noqa: E402  (sets the offline guard and the backend path)

from app.simulation.geometry_functions import planner, registry  # noqa: E402


def _drop(fn, kind):
    s = registry.REGISTRY[fn]
    return fn, replace(s, planning_extra=tuple(c for c in s.planning_extra if c.effect.kind != kind))


def arms():
    yield 'candidate', {}, {}, None
    yield 'no_translate_locus', dict([_drop('translate_point', 'PerpLine')]), {}, None
    yield 'no_foot_locus', dict([_drop('orthogonal_projection_line', 'PerpLine')]), {}, None
    yield 'no_direction', dict([_drop('orthogonal_projection_line', 'PerpDir')]), {}, None
    yield 'no_preconditions', {}, {}, ('_unmet', lambda self, contract, env: None)
    yield 'depth_3', {}, {'MAX_EFFECT_DEPTH': 3}, None
    yield 'reversed_loci', {}, {}, ('defs', {k: replace(d, loci=d.loci[::-1]) for k, d in registry.POINT_DEFINITIONS.items()})
    yield 'no_definitions', {}, {}, ('defs', {})


def run_arm(specs, consts, patch):
    saved_r = {k: registry.REGISTRY[k] for k in specs}
    saved_c = {k: getattr(planner, k) for k in consts}
    saved_d = dict(registry.POINT_DEFINITIONS)
    saved_m = planner._EffectResolver._unmet
    try:
        registry.REGISTRY.update(specs)
        for k, v in consts.items():
            setattr(planner, k, v)
        if patch and patch[0] == '_unmet':
            planner._EffectResolver._unmet = patch[1]
        if patch and patch[0] == 'defs':
            registry.POINT_DEFINITIONS.clear()
            registry.POINT_DEFINITIONS.update(patch[1])
        return P.run_all()
    finally:
        registry.REGISTRY.update(saved_r)
        for k, v in saved_c.items():
            setattr(planner, k, v)
        registry.POINT_DEFINITIONS.clear()
        registry.POINT_DEFINITIONS.update(saved_d)
        planner._EffectResolver._unmet = saved_m


if __name__ == '__main__':
    out, base = {}, None
    for name, specs, consts, patch in arms():
        rows = run_arm(specs, consts, patch)
        by = {r['id']: r for r in rows}
        base = base or by
        s = P.summary(rows)
        served = [r for r in rows if r['status'] == 'SERVED']
        out[name] = {
            'verdicts': s['verdicts'],
            'verdict_by_necessity': s['verdict_by_necessity'],
            'refusal_codes': s['refusal_codes'],
            'served_with_same_answer_as_candidate': sum(r['got2'] == base[r['id']]['got2'] for r in served),
            'served_with_another_plan_than_candidate': sum(r['plan'] != base[r['id']].get('plan') for r in served),
            'chain_functions_of_served': dict(collections.Counter('+'.join(r['chain_functions']) for r in served)),
            'max_explored_states': s['max_explored_states'], 'ms_median': s['ms_median']}
        print(name, json.dumps(out[name]['verdicts']), out[name]['served_with_another_plan_than_candidate'], flush=True)
    if len(sys.argv) > 1:
        import subprocess
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=P.ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--', 'backend'], cwd=P.ROOT, text=True).strip())
        with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as f:
            json.dump({'classification': 'IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC', 'provider_calls': 0, 'head': head,
                       'backend_tree_dirty': dirty, 'arms': out}, f, ensure_ascii=False, indent=1)
            f.write('\n')
