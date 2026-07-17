"""M14 §C1.3 — kiểu cho FAMILY_SELECTORS (bề mặt LLM của một capability family).

FamilySelector giữ FACT KHÁC với CATALOG (§C0/§C1): schema/contract/resolve span
NHIỀU runtime target (vd bubble+insertion), không thuộc về SimSpec concrete nào.
Đây KHÔNG phải nguồn sự thật thứ hai — cross-lock với family_memberships
(`cross_lock_violations`) chống drift.

selector_token CHỈ là token classify enum, KHÔNG phải simulation_id, KHÔNG BAO
GIỜ là envelope id (adapter resolve trước khi có envelope — §D, §E).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from app.simulation.descriptor import FamilyId


@dataclass(frozen=True)
class VariantSpec:
    """Một biến thể của family → một runtime target concrete + cơ chế nó biểu diễn."""

    variant_id: str
    concrete_simulation_id: str
    mechanism_id: str


@dataclass(frozen=True)
class FamilySelector:
    """Bề mặt lựa chọn family cho LLM. config_schema/contract/validate_family_spec
    điền ở Task 5; resolve điền ở Task 7 (None ở khung Task 2)."""

    family_id: FamilyId
    selector_token: str
    family_spec_version: str
    owned_mechanisms: tuple[str, ...]
    variants: tuple[VariantSpec, ...]
    description: str = ""  # cho catalog_text (stage classify)
    config_schema: Optional[dict] = None
    contract: Optional[str] = None
    validate_family_spec: Optional[Callable[[object], tuple[dict | None, str | None]]] = None
    resolve: Optional[Callable[[dict, dict], tuple[str, dict]]] = None
