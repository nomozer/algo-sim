# -*- coding: utf-8 -*-
"""Trace volume formula provenance through every product layer, offline.

canonical input → RequestContract → FactGraph → SemanticProgram → Scene3D
events/readouts → learner causal panel. Uses the same product boundaries as
``generate_generic_tier_a_fixtures.py`` (0 model calls). Output is JSON.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.simulation.geometry_compiler.compiler import bien_dich  # noqa: E402
from app.simulation.geometry_compiler.contract_adapter import build_fact_graph  # noqa: E402
from scripts import generate_generic_tier_a_fixtures as G  # noqa: E402


def _learner_label(obj: dict) -> str:
    return obj.get("reference") or obj.get("notation") or obj.get("label") or ""


def _panel(scene: dict, obj: dict, event: dict | None) -> dict:
    """What the causal card and the 'Dựa trên' line can show — same rules as
    ``coherentFormula`` / ``basisAt`` in the frontend, restated for the trace."""
    by_id = {o["id"]: o for o in scene["objects"]}
    formula = obj.get("formula") or {}
    refs = formula.get("references") or []
    coherent = bool(formula.get("text", "").strip()) and all(
        r.get("entity_id") in by_id and r.get("display_label", "").strip()
        and r["display_label"] in formula["text"] for r in refs)
    numerical = [e["source_id"] for e in obj.get("dependency_edges", [])
                 if e.get("relation") == "numerical" and e.get("source_id") in by_id]
    basis = numerical or list((event or {}).get("depends", []))
    return {
        "formula_card": formula.get("text") if coherent else None,
        "dua_tren": [_learner_label(by_id[i]) for i in basis if i in by_id],
    }


def _scene_layer(envelope: dict) -> dict:
    scene = envelope.get("scene3d") or {}
    by_id = {o["id"]: o for o in scene.get("objects", [])}
    quantities = [o for o in scene.get("objects", []) if o["type"] == "quantity"]
    volumes = [o for o in quantities if o.get("producer") == "measure.volume"]
    out = {
        "status": envelope.get("status"),
        "init_learner_text": next((e.get("learner_text") for e in scene.get("events", [])
                                   if e.get("action") == "INIT"), None),
        "readouts": [f"{_learner_label(o)} = {o.get('value')}" for o in quantities
                     if o.get("render") == "readout"],
        "volumes": [],
    }
    for volume in volumes:
        event = next((e for e in scene.get("events", [])
                      if e.get("object") == volume["id"]
                      and e.get("semantic_kind") == "FINAL_RESULT"), None) or next(
            (e for e in scene.get("events", []) if e.get("object") == volume["id"]), None)
        edges = volume.get("dependency_edges", [])
        closure, todo = set(), [volume["id"]]
        while todo:
            for e in by_id.get(todo.pop(), {}).get("dependency_edges", []):
                if e.get("relation") == "numerical" and e["source_id"] not in closure:
                    closure.add(e["source_id"])
                    todo.append(e["source_id"])
        out["volumes"].append({
            "id": volume["id"],
            "value": volume.get("value"),
            "numerical_edges": [e["source_id"] for e in edges if e.get("relation") == "numerical"],
            "structural_edges": [e["source_id"] for e in edges if e.get("relation") == "structural"],
            "numerical_closure": sorted(closure),
            "formula": (volume.get("formula") or {}).get("text"),
            "event_learner_text": (event or {}).get("learner_text"),
            "learner_panel": _panel(scene, volume, event),
        })
    return out


def _compiler_case(name: str, factory) -> dict:
    text, contract = factory()
    graph = build_fact_graph(contract).graph
    compiled = bien_dich(graph)
    program = compiled.program or {}
    envelope = G.asyncio.run(G._run_compiler(text, contract))
    return {
        "case": name,
        "canonical_input": text,
        "request_contract": {
            "source_invariants": [
                {"points": list(s.points), "expected": s.expected, "source_fact_id": s.source_fact_id}
                for s in contract.source_invariants],
            "relations": [r.kind for r in contract.geometric_relations],
        },
        "fact_graph": {
            "length_facts": [
                {"args": list(f.args), "value": f.value, "status": f.status,
                 "source_fact_id": f.source_fact_id}
                for f in graph.fact_theo_loai("length")],
        },
        "semantic_program": {
            "status": compiled.status,
            "quantity_memory": [
                {k: d[k] for k in ("name", "provenance", "source_fact_id", "initial_value") if k in d}
                for d in program.get("memory_declarations", []) if d.get("type") == "float"],
            "measure_statements": [
                f"{s['target_var']} := measure.{s['expr']['quantity']}({s['expr']['of']})"
                for s in program.get("statements", [])
                if (s.get("expr") or {}).get("kind") == "measure"],
        },
        "scene3d": _scene_layer(envelope),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    cases = [
        _compiler_case("triangular_pyramid", G._pyramid_control_contract),
        _compiler_case("triangular_prism", G._prism_p01_contract),
        _compiler_case("rectangular_pyramid", G._rect_pyramid_contract),
        _compiler_case("cuboid", G._cuboid_contract),
        _compiler_case("cube", G._cube_contract),
    ]
    cross_text, cross = G._cross_section_positive()
    cases.append({"case": "cross_section", "canonical_input": cross_text,
                  "route": "canonical_program_through_current_production_replay",
                  "scene3d": _scene_layer(cross)})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True,  # noqa: E731
                                    text=True).stdout.strip()
    args.out.write_text(json.dumps({
        "schema_version": "formula-provenance-trace/1",
        "git_head": git("rev-parse", "HEAD"),
        "product_paths_dirty": bool(git("status", "--porcelain", "--", "backend/app", "frontend/src")),
        "candidate_product_commit_sha": G.PRODUCT_COMMIT_SHA,
        "application_llm_calls": 0,
        "cases": cases,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(cases)} traces to {args.out}")


if __name__ == "__main__":
    main()
