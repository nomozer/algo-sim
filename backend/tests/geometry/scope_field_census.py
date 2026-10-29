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


def target_keys_in_source(source: str) -> set[str]:
    """Propagate target/key values through assignments, helpers and partial bindings to actual reads.

    This bounded static analysis reports discovered literal keys; it is not a proof about arbitrary Python.
    The coverage gate separately compares registry/schema and executes all mapped entry points.
    """
    tree = ast.parse(source)
    functions = {n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    target = "@target"
    inputs = {name: {} for name in functions}
    keys: set[str] = set()
    returns_target = {name for name, fn in functions.items() if any(
        isinstance(n, ast.Attribute) and n.attr == 'target' for ret in ast.walk(fn)
        if isinstance(ret, ast.Return) for n in ast.walk(ret))}

    for _ in range(len(functions) + 2):
        changed = False
        for name, fn in functions.items():
            env = {k: set(v) for k, v in inputs[name].items()}
            # Existing route functions use t/target for target parameters; helper parameters are tainted by callers.
            for arg in fn.args.args:
                if arg.arg in ('t', 'target'):
                    env.setdefault(arg.arg, set()).add(target)
            partials = {}

            def values(node):
                if isinstance(node, ast.Name): return env.get(node.id, set())
                if isinstance(node, ast.Constant) and isinstance(node.value, str): return {node.value}
                if isinstance(node, ast.Attribute) and node.attr == 'target': return {target}
                if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
                    return set().union(*(values(n) for n in node.elts)) if node.elts else set()
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id == 'set' and node.args: return values(node.args[0])
                    if node.func.id in returns_target: return {target}
                return set()

            for node in ast.walk(fn):
                if isinstance(node, ast.Assign):
                    for dest in node.targets:
                        if isinstance(dest, ast.Name):
                            env.setdefault(dest.id, set()).update(values(node.value))
                            if (isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                                    and node.value.func.id == 'partial' and node.value.args
                                    and isinstance(node.value.args[0], ast.Name)):
                                partials[dest.id] = (node.value.args[0].id, node.value.args[1:])
                elif isinstance(node, ast.Subscript) and target in values(node.value):
                    keys.update(values(node.slice) - {target})
                elif isinstance(node, ast.Compare):
                    sides = [node.left, *node.comparators]
                    if any(target in values(side) for side in sides):
                        for side in sides: keys.update(values(side) - {target})
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute) and node.func.attr == 'get' and target in values(node.func.value):
                        if node.args: keys.update(values(node.args[0]) - {target})
                    if not isinstance(node.func, ast.Name): continue
                    callee = node.func.id; args = list(node.args)
                    if callee in partials:
                        callee, bound = partials[callee]; args = [*bound, *args]
                    if callee not in functions: continue
                    for arg, formal in zip(args, functions[callee].args.args):
                        slot = inputs[callee].setdefault(formal.arg, set())
                        before = set(slot); slot.update(values(arg)); changed |= before != slot
        if not changed: break
    return keys


def target_keys_read_by_routes() -> set[str]:
    return set().union(*(target_keys_in_source((ROOT / rel).read_text(encoding='utf-8')) for rel in ROUTE_MODULES))


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
