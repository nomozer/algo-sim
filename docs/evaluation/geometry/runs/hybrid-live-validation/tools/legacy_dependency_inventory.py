"""Legacy LLM_ONLY dependency inventory (run `hybrid-live-validation`). Static AST import graph over `backend/app`,
function-level (lazy) imports included — an over-approximation of what each route can load. Offline, read-only.

Roots:
- LLM_ONLY: `app.ai.pipeline` (`run_pipeline`, the `/api/analyze` default) — the module closure.
- HYBRID:   `app.ai.hybrid_offline`, `app.ai.adapter4_route`, `app.ai.typed_fact_next_extraction` — with `app.ai.pipeline`
            NOT expanded: Hybrid imports only route-policy symbols from it (recorded separately, by symbol).
- SHELL:    `app.main` — the product entry point (everything a request can reach).

Classes: HYBRID_REQUIRED (Hybrid closure only), SHARED_COMPONENT (both closures, or route-independent product shell
reachable from `app.main` but from neither solver root), LEGACY_ONLY (LLM_ONLY closure only), UNCERTAIN_DEPENDENCY (not
reachable from `app.main` at all: scripts/tests/dynamic consumers only — never deleted on this evidence).
Usage: legacy_dependency_inventory.py <out.json>
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
APP = ROOT / "backend" / "app"
HYBRID_ROOTS = ("app.ai.hybrid_offline", "app.ai.adapter4_route", "app.ai.typed_fact_next_extraction")
LLM_ROOT = "app.ai.pipeline"
SHELL_ROOT = "app.main"


def module_name(p: Path) -> str:
    rel = p.relative_to(APP.parent).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


MODULES = {module_name(p): p for p in APP.rglob("*.py") if "__pycache__" not in p.parts}


def resolve(cur: str, node: ast.ImportFrom | ast.Import) -> list[tuple[str, tuple[str, ...]]]:
    out = []
    if isinstance(node, ast.Import):
        for a in node.names:
            out.append((a.name, ()))
        return out
    base = node.module or ""
    if node.level:
        pkg = cur.split(".")
        is_pkg = MODULES.get(cur, Path()).name == "__init__.py"
        pkg = pkg if is_pkg else pkg[:-1]
        pkg = pkg[: len(pkg) - (node.level - 1)]
        base = ".".join(pkg + ([base] if base else []))
    names = tuple(a.name for a in node.names)
    out.append((base, names))
    for n in names:                                   # `from pkg import submodule`
        if f"{base}.{n}" in MODULES:
            out.append((f"{base}.{n}", ()))
    return out


EDGES: dict[str, dict[str, set[str]]] = {}
for m, p in MODULES.items():
    tree = ast.parse(p.read_text(encoding="utf-8"), str(p))
    deps: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for target, names in resolve(m, node):
                while target and target not in MODULES and "." in target:
                    target = target.rsplit(".", 1)[0]
                if target in MODULES and target != m:
                    deps.setdefault(target, set()).update(names)
    EDGES[m] = deps


def closure(roots, stop=()):
    seen, todo = set(), list(roots)
    while todo:
        m = todo.pop()
        if m in seen:
            continue
        seen.add(m)
        if m in stop:
            continue
        todo.extend(EDGES.get(m, {}))
    return seen


L = closure([LLM_ROOT])
H = closure(HYBRID_ROOTS, stop={LLM_ROOT})
S = closure([SHELL_ROOT])
rows = []
for m in sorted(MODULES):
    if MODULES[m].name == "__init__.py" and not MODULES[m].read_text(encoding="utf-8").strip():
        continue                                      # empty package marker: no code to own or retire
    in_l, in_h, in_s = m in L, m in H, m in S
    if in_l and in_h:
        cls = "SHARED_COMPONENT"
    elif in_h:
        cls = "HYBRID_REQUIRED"
    elif in_l:
        cls = "LEGACY_ONLY"
    elif in_s:
        cls = "SHARED_COMPONENT"
    else:
        cls = "UNCERTAIN_DEPENDENCY"
    importers = sorted(k for k, v in EDGES.items() if m in v)
    rows.append({"module": m, "path": MODULES[m].relative_to(ROOT).as_posix(), "class": cls,
                 "in_llm_only_closure": in_l, "in_hybrid_closure": in_h, "reachable_from_main": in_s,
                 "route_independent_shell": cls == "SHARED_COMPONENT" and not (in_l or in_h),
                 "importers": importers,
                 "lines": sum(1 for _ in MODULES[m].open(encoding="utf-8"))})
hybrid_symbols_from_pipeline = sorted({n for r in HYBRID_ROOTS for n in EDGES.get(r, {}).get(LLM_ROOT, set())}
                                      | {n for m in H for n in EDGES.get(m, {}).get(LLM_ROOT, set())})
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--", "backend/app"], cwd=ROOT, text=True).strip())
counts: dict[str, int] = {}
for r in rows:
    counts[r["class"]] = counts.get(r["class"], 0) + 1
out = {"schema": "legacy-dependency-inventory/1", "head": head, "product_uncommitted": dirty, "method":
       "static AST import graph incl. function-level imports; over-approximates load closures", "roots":
       {"llm_only": LLM_ROOT, "hybrid": list(HYBRID_ROOTS), "shell": SHELL_ROOT},
       "hybrid_imports_from_pipeline_by_symbol": hybrid_symbols_from_pipeline, "counts": counts, "modules": rows}
Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(json.dumps({"counts": counts, "pipeline_symbols_used_by_hybrid": hybrid_symbols_from_pipeline}, ensure_ascii=False))
for r in rows:
    if r["class"] != "SHARED_COMPONENT" or r["module"] == LLM_ROOT:
        print(r["class"], r["module"], r["lines"], "importers:", ",".join(r["importers"])[:120])
