# -*- coding: utf-8 -*-
"""Deterministic mutation fuzz of the public TypedFactNext route boundaries (run `hybrid-contract-v2`, P1).

Seeds: the Adapter /3 dev corpus SERVED cases + authored payloads of `test_hybrid_contract_unification.py` (and, for the
`/2` route, their `/2` conversions). Every mutable site (premise args, section fields, goal ids, solid fields) is set to
each value of a fixed list and deleted. A route must RETURN a result for every mutant: an exception escaping the public
function is a crash; a returned `*_INTERNAL_ERROR` refusal is a technical fault recorded at the boundary (must be 0 too).
0 provider calls. Run from `backend/`:  python <this file> <route: adapter3|bridge|v2> <out.json>
"""
from __future__ import annotations

import collections
import copy
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from tests.geometry.test_hybrid_contract_unification import _payload  # noqa: E402

VALUES = [[], "", 5, None, ["X"], {"a": 1}, "ZZ", ["S"], [["S", "A"]], "1/0", "-1", "0", [5], [None], "S::", "x::A",
          ["S", "S"], "A-B-C"]
DEL = "<DEL>"


def seeds() -> list[tuple[str, dict]]:
    corpus = json.loads(Path("../docs/evaluation/geometry/runs/typedfact-next-adapter3-simulation/corpus-dev.json")
                        .read_text(encoding="utf-8"))
    out = [("u4", _payload("ABCD", cut=["SA", "SB", "SC", "SD"])), ("u3p", _payload("ABC", "perpendicular", cut=["SA", "SB", "SC"])),
           ("b4", _payload("ABCD", residual=True))]
    return out + [(c["case_id"], c["payload"]) for c in corpus["cases"]]


def sites(p: dict):
    for i, s in enumerate(p.get("solids", [])):
        for k in ("notation", "vertex_bindings", "solid_type", "center", "radius"):
            yield ("solids", i, k)
    for i, pr in enumerate(p.get("premises", [])):
        yield ("premises", i, "kind")
        for k in list((pr.get("args") or {}).keys()):
            yield ("premises", i, "args", k)
    for i, s in enumerate(p.get("derived_sections", [])):
        for k in ("through_point", "parallel_plane", "perpendicular_line", "parallel_line_a", "cut_edges",
                  "named_intersections", "stated_intersections", "declared_boundary", "plane_kind", "target_solid_id"):
            if k in s:
                yield ("derived_sections", i, k)
    for grp in ("simulation_goals", "math_goals", "relations"):
        for i, g in enumerate(p.get(grp, [])):
            for k in g:
                if k not in ("quote", "goal_id", "relation_id", "kind"):
                    yield (grp, i, k)


def route(name: str):
    if name == "adapter3":
        from app.ai.adapter3_simulation import run_typed_fact_next_route
        return run_typed_fact_next_route, lambda p: p
    if name == "bridge":
        from app.ai.function_route import run_typed_fact_next_planner_route
        return run_typed_fact_next_planner_route, lambda p: p
    from app.ai.adapter4_route import run_typed_fact_next_v2_route
    from app.simulation.geometry_functions.typed_fact_next import convert_v1_to_v2
    return run_typed_fact_next_v2_route, lambda p: convert_v1_to_v2(p, "adapter3")


def main(name: str, out: Path) -> None:
    fn, prep = route(name)
    crash, internal, codes, ex = collections.Counter(), collections.Counter(), collections.Counter(), {}
    runs = skipped = 0
    for sid, seed in seeds():
        try:
            base = prep(copy.deepcopy(seed))
        except Exception:  # noqa: BLE001 — a seed the converter refuses is not a mutant of this route
            skipped += 1
            continue
        for site in list(sites(base)):
            for v in [*VALUES, DEL]:
                p = copy.deepcopy(base)
                o = p
                for s in site[:-1]:
                    o = o[s]
                if v == DEL:
                    o.pop(site[-1], None) if isinstance(o, dict) else None
                else:
                    o[site[-1]] = v
                runs += 1
                try:
                    r = fn(p)
                except Exception as e:  # noqa: BLE001 — the measurement: an exception escaping the public boundary
                    tb = traceback.extract_tb(e.__traceback__)
                    key = f"{type(e).__name__} @ {tb[-1].name}"
                    crash[key] += 1
                    ex.setdefault(key, {"seed": sid, "site": list(map(str, site)), "value": repr(v)[:40]})
                    continue
                codes[str(r.code)] += 1
                if str(r.code).endswith("INTERNAL_ERROR"):
                    internal[str(r.reason)[:80]] += 1
                    ex.setdefault(f"internal: {str(r.reason)[:60]}", {"seed": sid, "site": list(map(str, site)), "value": repr(v)[:40]})
    res = {"route": name, "runs": runs, "skipped_seeds": skipped, "escaped_exceptions": sum(crash.values()),
           "escaped_by_kind": dict(crash), "internal_errors": sum(internal.values()), "internal_by_reason": dict(internal),
           "examples": ex, "result_codes": dict(codes.most_common())}
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("route", "runs", "escaped_exceptions", "escaped_by_kind", "internal_errors")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2]))
