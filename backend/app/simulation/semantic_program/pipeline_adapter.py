# -*- coding: utf-8 -*-
"""Pipeline Adapter: Tích hợp SemanticProgramSpec vào hệ thống SimulationEnvelope."""
from __future__ import annotations
from typing import Any, Optional

from .contract import SemanticProgramSpec
from .validator import validate_semantic_program
from .interpreter import SemanticProgramInterpreter, SemanticExecutionResult
from .visual_adapter import VisualTraceAdapter, VisualFrame


def compile_semantic_program_to_envelope(
    spec: SemanticProgramSpec,
    max_steps: int = 300,
) -> dict[str, Any]:
    """Biên dịch và thực thi tất định SemanticProgramSpec thành một SimulationEnvelope chuẩn."""
    # 1. Thẩm định tĩnh hợp đồng
    val_res = validate_semantic_program(spec)
    if not val_res.ok:
        raise ValueError(f"Thẩm định tĩnh SemanticProgramSpec thất bại: {val_res.error}")

    # 2. Thực thi tất định trên AST
    interpreter = SemanticProgramInterpreter(max_steps=max_steps)
    exec_res: SemanticExecutionResult = interpreter.execute(spec)

    # 3. Tiếp hợp chuyển đổi trực quan
    adapter = VisualTraceAdapter(spec)
    frames: list[VisualFrame] = adapter.adapt(exec_res)

    # 4. Định dạng timeline thành DSL process
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
        "objects": frames[0].objects if frames else [],
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

    return envelope
