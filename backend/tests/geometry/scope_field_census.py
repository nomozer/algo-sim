"""Mechanical census of every TypedFactNext field (run `unified-solid-scope-closure`).

Walks the pydantic models (`/1` and `/2`, nested models), expands the open `PremiseSpec.args` from the schema's own
argument table and the open `MathGoalSpec.target` from the keys the routes actually read (AST of the route modules).
`field_paths()` is the ground truth the coverage test compares against the classification in
`docs/.../unified-solid-scope-closure/schema-field-inventory.json`; a field added to a model without a classification
makes that test fail.
"""
from __future__ import annotations

import ast
from pathlib import Path
import typing

from pydantic import BaseModel

from app.simulation.geometry_functions import typed_fact_next as T

ROOT = Path(__file__).resolve().parents[3]
ROUTE_MODULES = ('backend/app/ai/adapter3_simulation.py', 'backend/app/ai/adapter4_route.py',
                 'backend/app/simulation/geometry_functions/typed_fact_next_bridge.py',
                 'backend/app/simulation/geometry_functions/typed_fact_next.py')


def _models(annotation) -> list[type[BaseModel]]:
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return [annotation]
    return [m for arg in typing.get_args(annotation) for m in _models(arg)]


def _walk(model: type[BaseModel], out: dict[str, str]) -> None:
    for name, field in model.model_fields.items():
        path = f'{model.__name__}.{name}'       # keyed by the owning class: `/1` and `/2` share nested models
        if path in out:
            continue
        out[path] = str(field.annotation)
        for nested in _models(field.annotation):
            _walk(nested, out)


def target_keys_read_by_routes() -> set[str]:
    """String keys read from a math goal `target` (`t[...]`, `t.get(...)`, `... in t`, helper(target, "key"))."""
    keys: set[str] = set()

    def is_target(node) -> bool:
        return (isinstance(node, ast.Name) and node.id in ('t', 'target')) or \
               (isinstance(node, ast.Attribute) and node.attr == 'target')

    for rel in ROUTE_MODULES:
        for node in ast.walk(ast.parse((ROOT / rel).read_text(encoding='utf-8'))):
            if isinstance(node, ast.Subscript) and is_target(node.value) and isinstance(node.slice, ast.Constant):
                keys.add(node.slice.value)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'get' and is_target(node.func.value):
                    keys.update(a.value for a in node.args[:1] if isinstance(a, ast.Constant))
                elif any(is_target(a) for a in node.args):
                    keys.update(a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str))
            elif isinstance(node, ast.Compare) and any(isinstance(op, ast.In) for op in node.ops) \
                    and any(is_target(c) for c in node.comparators) and isinstance(node.left, ast.Constant):
                keys.add(node.left.value)
    return {k for k in keys if isinstance(k, str)}


def field_paths() -> dict[str, str]:
    out: dict[str, str] = {}
    for model in (T.TypedFactNextPayload, T.TypedFactNextPayloadV2):
        _walk(model, out)
    for kind, shape in T._ARGS_LOI.items():
        for key, s in shape.items():
            out[f'PremiseSpec.args[{kind}].{key}'] = s
    for i, shape in enumerate(T._ARGS_GOC_VUONG):
        for key, s in shape.items():
            out[f'PremiseSpec.args[right_angle#{i}].{key}'] = s
    for key in sorted(target_keys_read_by_routes()):
        out[f'MathGoalSpec.target.{key}'] = 'Any'
    return out


def kinds() -> dict[str, list[str]]:
    """Every kind literal of relations, simulation goals and math goals (their per-kind meaning is classified too)."""
    def literal(model, field):
        return list(typing.get_args(model.model_fields[field].annotation))
    return {'relation': literal(T.GeometricRelationSpec, 'kind'),
            'simulation_goal': literal(T.SimulationGoalSpec, 'kind'),
            'math_goal': literal(T.MathGoalSpec, 'kind')}


if __name__ == '__main__':
    import json
    print(json.dumps({'fields': field_paths(), 'kinds': kinds()}, ensure_ascii=False, indent=1))
