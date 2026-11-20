from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

from app.ai.local_geometry_parser import parse_geometry_problem_locally
from app.simulation.geometry_functions import engine, planner, registry
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2


HANDOFF_BASE = "55c2eaaea"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_point_o_provenance_handoff_patch_applies_at_handoff_base_and_replaces_layout_derived(tmp_path: Path) -> None:
    root = _repo_root()
    patch_path = (
        root
        / "docs/evaluation/geometry/runs/axo-hybrid-compositional-geometry-language-grounded-simulation/handoff/derived_point_o_provenance.patch"
    )
    assert patch_path.exists()

    # Check the frozen /12 patch at the exact base commit it was written against (temp index, patch unmodified).
    index_env = {**os.environ, "GIT_INDEX_FILE": str(tmp_path / "handoff_base.index")}
    subprocess.run(["git", "read-tree", HANDOFF_BASE], cwd=root, env=index_env, check=True)
    lf_patch = patch_path.read_bytes().replace(b"\r\n", b"\n")
    chk = subprocess.run(["git", "apply", "--cached", "--check", "-"], cwd=root, env=index_env, input=lf_patch, capture_output=True)
    assert chk.returncode == 0, f"git apply --cached --check failed at {HANDOFF_BASE}: {chk.stderr!r}"

    # Apply patch only onto a temporary copy extracted from HANDOFF_BASE — never mutating locked files
    engine_rel = Path("backend/app/simulation/geometry_functions/engine.py")
    base_src = subprocess.run(
        ["git", "show", f"{HANDOFF_BASE}:{engine_rel.as_posix()}"],
        cwd=root,
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8").replace("\r\n", "\n")
    tmp_engine = tmp_path / engine_rel
    tmp_engine.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / engine_rel, tmp_engine)

    patch_text = lf_patch.decode("utf-8")
    assert "divide_segment" in patch_text and "midpoint" in patch_text

    patched_lines: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith(("+++", "---", "@@", "\\")):
            continue
        if line.startswith(("+", " ")):
            patched_lines.append(line[1:])
    orig_hunk = "\n".join(
        line[1:] for line in patch_text.splitlines()
        if not line.startswith(("+++", "---", "@@", "\\", "+"))
    ) + "\n"
    new_hunk = "\n".join(patched_lines) + "\n"
    assert orig_hunk in base_src
    tmp_engine.write_text(base_src.replace(orig_hunk, new_hunk, 1), encoding="utf-8")

    # Execute isolated patched module inside subprocess so sys.modules for main product engine stays untouched
    probe_py = f"""
import importlib.util, sys
sys.path.insert(0, {str(root / 'backend')!r})
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


def test_live_engine_constructs_implicit_point_o_without_layout_derived() -> None:
    """Product engine integrates §19 implicit center construction without LAYOUT_DERIVED for triangular, square, and hexagonal bases."""
    cases = [
        ("Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 2, cạnh bên bằng 3.", "divide_segment"),
        ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2, cạnh bên bằng 3.", "midpoint"),
        ("Cho hình chóp lục giác đều S.ABCDEF có cạnh đáy bằng 2, cạnh bên bằng 3.", "midpoint"),
    ]
    for txt, expected_expr_kind in cases:
        lp = parse_geometry_problem_locally(txt)
        assert lp.status == "LOCAL_PARSE_COMPLETE" and lp.payload is not None, lp.to_dict()
        b = bridge_v2(lp.payload)
        p = planner.lap_ke_hoach({"facts": b["facts"]}, txt)
        tok = registry._CHINH_SACH_XUAT.set(b["bridge"].get("output_policies"))
        try:
            kr = engine.dung_tu_loi_goi(
                txt,
                {"calls": p.calls},
                auxiliary=tuple(p.auxiliary),
                read_quotes=tuple(q for g in (*p.goals, *p.negated) if g.get("call") for q in g["call"]["source"]["quotes"]),
            )
        finally:
            registry._CHINH_SACH_XUAT.reset(tok)
        assert kr.status == "SERVED", kr
        sp = kr.spec.model_dump() if hasattr(kr.spec, "model_dump") else kr.spec
        decls = {d["name"]: d for d in (sp.get("memory_declarations") or [])}
        stmts = [s for s in (sp.get("statements") or []) if s.get("target_var") == "O"]
        assert "O" in decls and decls["O"].get("provenance") != "LAYOUT_DERIVED", decls.get("O")
        assert len(stmts) == 1 and stmts[0]["kind"] == "construct_point", stmts
        assert stmts[0]["expr"]["kind"] == expected_expr_kind, stmts[0]
