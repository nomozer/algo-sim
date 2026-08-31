# -*- coding: utf-8 -*-
"""Package semantic_program: Hợp đồng, kiểm định, interpreter, visual trace adapter và pipeline adapter."""
from .contract import (
    SemanticProgramSpec,
    MemoryDeclaration,
    ValueExpr,
    ConditionExpr,
    SemanticStatement,
    VisualBindings,
    generate_json_schema,
)
from .validator import validate_semantic_program, ValidationResult
from .interpreter import SemanticProgramInterpreter, SemanticExecutionResult, SemanticTraceStep
from .visual_adapter import VisualTraceAdapter, VisualFrame
from .pipeline_adapter import (
    SIMULATION_ID,
    compile_semantic_program_to_envelope,
    validate_semantic_envelope_config,
)

__all__ = [
    "SemanticProgramSpec",
    "MemoryDeclaration",
    "ValueExpr",
    "ConditionExpr",
    "SemanticStatement",
    "VisualBindings",
    "generate_json_schema",
    "validate_semantic_program",
    "ValidationResult",
    "SemanticProgramInterpreter",
    "SemanticExecutionResult",
    "SemanticTraceStep",
    "VisualTraceAdapter",
    "VisualFrame",
    "compile_semantic_program_to_envelope",
    "SIMULATION_ID",
    "validate_semantic_envelope_config",
]
