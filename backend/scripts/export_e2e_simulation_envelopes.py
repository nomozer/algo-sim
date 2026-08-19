# -*- coding: utf-8 -*-
"""Xuất các SimulationEnvelope từ SemanticProgramSpec để kiểm thử E2E Renderer & Playwright."""
from pathlib import Path
import json
import sys

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.visual_adapter import VisualTraceAdapter
from tests.semantic_program.fixtures_coverage_18 import (
    P01_STACK_BRACKET,
    P03_BINARY_SEARCH,
    P04_BUBBLE_SORT,
    P09_GRAPH_BFS,
)

def export_e2e_fixtures():
    interpreter = SemanticProgramInterpreter()
    fixtures = [
        ("stack_bracket", P01_STACK_BRACKET),
        ("binary_search", P03_BINARY_SEARCH),
        ("bubble_sort", P04_BUBBLE_SORT),
        ("graph_bfs", P09_GRAPH_BFS),
    ]

    out_data = {}
    for key, spec in fixtures:
        res = interpreter.execute(spec)
        adapter = VisualTraceAdapter(spec)
        frames = adapter.adapt(res)

        # Convert VisualFrames into GenericSimulationSpec processes
        steps = []
        for f in frames:
            steps.append({
                "narration": f.narration,
                "targets": f.highlighted_object_ids if f.highlighted_object_ids else [cb.semantic_id for cb in spec.visual_bindings.containers[:1]],
                "action": "step",
            })

        config = {
            "dsl_version": "1.0",
            "title": spec.title,
            "objects": frames[0].objects,
            "rules": [],
            "interactions": [],
            "processes": [
                {
                    "type": "step_sequence",
                    "steps": steps,
                }
            ],
        }

        envelope = {
            "status": "ok",
            "simulation_id": "generic.rule_scene",
            "domain": "generic",
            "visual_mode": "2d",
            "title": spec.title,
            "description": spec.description or spec.title,
            "config": config,
            "notes": None,
        }
        out_data[key] = envelope

    out_file = backend_dir.parent / "frontend" / "public" / "fixtures" / "e2e_semantic_candidates.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(out_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Exported {len(fixtures)} E2E semantic candidate envelopes to {out_file}")

if __name__ == "__main__":
    export_e2e_fixtures()
