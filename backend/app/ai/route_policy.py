"""Immutable per-request route policy snapshot for AlgoSim post-cutover Hybrid architecture.

Hybrid `/4` (`typed-fact-next/2` -> Source Gate -> FactGraph -> Planner -> Registry -> IR -> Exact Kernel -> Adapter `/4`)
is the sole official production pipeline on `POST /api/analyze`. `RoutePolicy` captures the operator-only preview
toggle (`HYBRID_ROUTE_D_PREVIEW=1`) once per request without carrying retired `LLM_ONLY` or Compiler C state.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from typing import Mapping

#: Minimum length of `HYBRID_ROUTE_D_PREVIEW_TOKEN`; shorter or missing => every preview request is refused.
HYBRID_PREVIEW_TOKEN_MIN_LENGTH = 32


@dataclass(frozen=True)
class RoutePolicy:
    """Immutable route policy snapshot read once at the API boundary."""

    default_route_mode: str = "HYBRID"
    hybrid_preview_enabled: bool = False
    response_contract: str = "flat"
    preview_surface: tuple[tuple[str, str], ...] = ()

    def fingerprint(self) -> str | None:
        """`None` on the default production policy; sha256 digest when an explicit preview surface is active."""
        if self.hybrid_preview_enabled:
            source = json.dumps({"route": "HYBRID_ROUTE_D_PREVIEW", **dict(self.preview_surface)}, sort_keys=True)
            return hashlib.sha256(source.encode("utf-8")).hexdigest()
        return None


def route_policy_snapshot(env: Mapping[str, str] | None = None, *, preview: bool = False) -> RoutePolicy:
    """Snapshot route policy from `env` (defaults to `os.environ`)."""
    resolved_env = os.environ if env is None else env
    enabled = bool(preview and resolved_env.get("HYBRID_ROUTE_D_PREVIEW") == "1")
    surface: tuple[tuple[str, str], ...] = ()
    if enabled:
        from app.ai.hybrid_preview import preview_identity

        surface = tuple(sorted(preview_identity("flat").items()))
    return RoutePolicy(
        default_route_mode="HYBRID",
        hybrid_preview_enabled=enabled,
        response_contract="flat",
        preview_surface=surface,
    )
