from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_point_o_provenance_handoff_patch_applies_and_replaces_layout_derived_with_explicit_construction(tmp_path: Path) -> None:
    root = _repo_root()
    patch_path = (
        root
        / "docs/evaluation/geometry/runs/axo-hybrid-compositional-geometry-language-grounded-simulation/handoff/derived_point_o_provenance.patch"
    )
    assert patch_path.exists()

    chk = subprocess.run(["git", "apply", "--check", str(patch_path)], cwd=root, capture_output=True, text=True)
    assert chk.returncode == 0, f"git apply --check failed: {chk.stderr}"

    # Apply patch only onto a temporary copy of backend/app tree — never mutating locked engine.py
    engine_rel = Path("backend/app/simulation/geometry_functions/engine.py")
    tmp_engine = tmp_path / engine_rel
    tmp_engine.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / engine_rel, tmp_engine)

    # Apply the unified hunk in memory onto tmp_engine using python without touching git working tree
    src_text = tmp_engine.read_text(encoding="utf-8")
    anchor = (
        '                    khai.append(P.memory_declaration(ir_name(t), "point3", provenance="LAYOUT_DERIVED"))\n'
        "            else:\n"
        "                lenh.append(P.declare_point(ir_name(t), self.pts[t], t))\n"
        '                khai.append(P.memory_declaration(ir_name(t), "point3", provenance="LAYOUT_DERIVED"))\n'
    )
    assert anchor in src_text
    patch_text = patch_path.read_text(encoding="utf-8")
    assert "divide_segment" in patch_text and "midpoint" in patch_text

    # Reconstruct patched code directly from the patch's '+' lines in the single hunk
    patched_lines: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith(("+++", "---", "@@", "\\")):
            continue
        if line.startswith("+"):
            patched_lines.append(line[1:])
        elif line.startswith(" "):
            patched_lines.append(line[1:])
    orig_hunk = "\n".join(
        line[1:] for line in patch_text.splitlines()
        if not line.startswith(("+++", "---", "@@", "\\", "+"))
    ) + "\n"
    new_hunk = "\n".join(patched_lines) + "\n"
    assert orig_hunk in src_text
    tmp_engine.write_text(src_text.replace(orig_hunk, new_hunk, 1), encoding="utf-8")

    # Execute isolated patched module inside subprocess so sys.modules for main product engine stays untouched
    probe_py = f"""
import json, importlib.util, sys
sys.path.insert(0, {str(root / 'backend')!r})
import app.simulation.geometry_functions.engine as prod_eng
# Load patched copy under separate spec inside app.simulation.geometry_functions package namespace
spec = importlib.util.spec_from_file_location("app.simulation.geometry_functions.engine_patched_test", {str(tmp_engine)!r})
mod = importlib.util.module_from_spec(spec)
mod.__package__ = "app.simulation.geometry_functions"
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

from app.ai.local_geometry_parser import parse_geometry_problem_locally
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2
from app.simulation.geometry_functions import planner, registry

for txt in (
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2, cạnh bên bằng 3.",
    "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 2, cạnh bên bằng 3.",
):
    lp = parse_geometry_problem_locally(txt)
    b = bridge_v2(lp.payload)
    p = planner.lap_ke_hoach({{"facts": b["facts"]}}, txt)
    tok = registry._CHINH_SACH_XUAT.set(b["bridge"].get("output_policies"))
    try:
        kr = mod.dung_tu_loi_goi(
            txt,
            {{"calls": p.calls}},
            auxiliary=tuple(p.auxiliary),
            read_quotes=tuple(q for g in (*p.goals, *p.negated) if g.get("call") for q in g["call"]["source"]["quotes"]),
        )
    finally:
        registry._CHINH_SACH_XUAT.reset(tok)
    assert kr.status == "SERVED", kr
    sp = kr.spec.model_dump() if hasattr(kr.spec, "model_dump") else kr.spec
    decls = {{d["name"]: d for d in (sp.get("memory_declarations") or sp.get("memory") or sp.get("declarations") or [])}}
    stmts = [s for s in (sp.get("statements") or []) if s.get("target_var") == "O"]
    assert "O" in decls and decls["O"].get("provenance") != "LAYOUT_DERIVED", decls.get("O")
    assert len(stmts) == 1 and stmts[0]["kind"] == "construct_point", stmts
print("ISOLATED_PATCH_OK")
"""
    res = subprocess.run([sys.executable, "-c", probe_py], capture_output=True, text=True)
    assert res.returncode == 0, f"STDERR:\n{res.stderr}\nSTDOUT:\n{res.stdout}"
    assert "ISOLATED_PATCH_OK" in res.stdout
