# -*- coding: utf-8 -*-
"""Application-layer Hybrid route wrapper binding Scene3D projection hooks into deterministic step editing."""
from __future__ import annotations

from typing import Any

from app.simulation.geometry_functions.step_editor import (
    SceneProjectionHooks,
    execute_step_edit as _execute_step_edit_core,
)
from app.simulation.semantic_program.scene3d import (
    _attach_formulas,
    _attach_topology,
    _build_formation,
    _cau_canh_thiet_dien,
    _cau_thiet_dien,
    _nhan_canh_thiet_dien,
)

DEFAULT_SCENE3D_HOOKS = SceneProjectionHooks(
    attach_topology=_attach_topology,
    attach_formulas=_attach_formulas,
    build_formation=_build_formation,
    cau_canh_thiet_dien=_cau_canh_thiet_dien,
    nhan_canh_thiet_dien=_nhan_canh_thiet_dien,
    cau_thiet_dien=_cau_thiet_dien,
)


def execute_step_edit(
    *,
    scene3d: dict[str, Any],
    step_id: str,
    step_index: int,
    previous_instruction: str,
    edited_instruction: str,
    target_ids: list[str] | None = None,
    absorbed_ids: list[str] | None = None,
    step_overrides: dict[str, str] | None = None,
    prior_step_ids: list[str] | None = None,
    force_full_rebuild: bool = False,
    scene_hooks: SceneProjectionHooks = DEFAULT_SCENE3D_HOOKS,
) -> dict[str, Any]:
    """Execute deterministic construction-step edit with canonical Scene3D projection hooks injected from app.ai."""
    return _execute_step_edit_core(
        scene3d=scene3d,
        step_id=step_id,
        step_index=step_index,
        previous_instruction=previous_instruction,
        edited_instruction=edited_instruction,
        target_ids=target_ids,
        absorbed_ids=absorbed_ids,
        step_overrides=step_overrides,
        prior_step_ids=prior_step_ids,
        force_full_rebuild=force_full_rebuild,
        scene_hooks=scene_hooks,
    )
