"""M14 §E4 — mechanism-consistency gate (điểm 3).

So CƠ CHẾ đề YÊU CẦU (analysis.prescribed_procedure — tín hiệu ngữ nghĩa CÓ CẤU
TRÚC từ analyze) với cơ chế family THỰC SỰ SỞ HỮU (selector.owned_mechanisms).
Sibling của computation-ownership gate M13: KHÔNG đọc text đề, KHÔNG keyword-patch
tên thuật toán.

RANH GIỚI "vắng tín hiệu vs tín hiệu-lạ" (làm rõ so với chữ 'thiếu→gap' của E4/N7
— chữ đó siết quá tay, sẽ từ chối oan mọi đề 'sắp xếp tăng dần'):
- prescribed ∈ {null, "none"}  → KHÔNG ép cơ chế → permissive (bubble/insertion
  đều là minh hoạ hợp lệ của "sắp xếp"). Vắng tín hiệu KHÔNG phải bằng chứng
  của cơ chế ngoài phạm vi.
- prescribed ∈ owned            → cơ chế được sở hữu → qua tầng 1 (tầng 2 kiểm variant).
- prescribed ∉ owned (select/partition/other_unspecified) → CÓ tín hiệu cơ chế
  KHÔNG sở hữu → capability_gap. Đây mới là chỗ fail-closed đúng nghĩa.
"""

from __future__ import annotations

from app.simulation.error_codes import ErrorCode
from app.simulation.families.base import FamilySelector
from app.simulation.mechanisms import canonical_mechanism, mechanism_family


def check_mechanism_ownership(
    analysis: dict, selector: FamilySelector
) -> tuple[ErrorCode, str] | None:
    """Tầng 1 (TRƯỚC simulate): cơ chế đề yêu cầu có được family sở hữu không?
    Trả (code, message) khi gap; None khi được phép đi tiếp.

    M15: chuẩn hoá đầu vào qua `canonical_mechanism` (legacy sorting bare →
    canonical namespaced) TRƯỚC khi so — `owned_mechanisms` nay là canonical."""
    prescribed = canonical_mechanism(analysis.get("prescribed_procedure"))
    if prescribed is None:
        return None
    if prescribed in selector.owned_mechanisms:
        return None
    return (
        ErrorCode.GATE_MECHANISM_OWNERSHIP,
        "Đề yêu cầu một cách sắp xếp mà chưa có engine tất định nào sở hữu cơ chế "
        "đó — hệ từ chối trung thực thay vì minh hoạ bằng thuật toán khác.",
    )


def check_variant_consistency(
    analysis: dict, selector: FamilySelector, variant_id: str
) -> tuple[ErrorCode, str] | None:
    """Tầng 2 (SAU khi FamilySpec validate): variant LLM chọn có khớp cơ chế đề
    yêu cầu không? So analysis × variant (KHÔNG chỉ nhìn FamilySpec). Trả
    (code, message) → retry khi lệch; None khi khớp/không ràng buộc.

    M15: chuẩn hoá qua `canonical_mechanism` — `var.mechanism_id` nay canonical."""
    prescribed = canonical_mechanism(analysis.get("prescribed_procedure"))
    if prescribed is None:
        return None  # không ép cơ chế → variant nào cũng được
    if prescribed not in selector.owned_mechanisms:
        return None  # đã bị tầng 1 chặn — không báo trùng ở đây
    var = next((v for v in selector.variants if v.variant_id == variant_id), None)
    if var is None:
        return None  # variant lạ đã bị validate_family_spec bắt
    if var.mechanism_id != prescribed:
        return (
            ErrorCode.MECHANISM_VARIANT_MISMATCH,
            f"Đề yêu cầu cơ chế '{prescribed}' nhưng biến thể '{variant_id}' biểu diễn "
            "cơ chế khác — chọn đúng biến thể khớp cơ chế đề yêu cầu.",
        )
    return None


def check_mechanism_consistency_for_target(analysis, spec):
    prescribed = canonical_mechanism(analysis.get("prescribed_procedure"))
    if prescribed is None:
        return None
    fam = mechanism_family(prescribed)
    fams = {m.family_id.value for m in spec.family_memberships}
    if fam not in fams:
        return (
            ErrorCode.ROUTE_MECHANISM_FAMILY_MISMATCH,
            "Cơ chế đề yêu cầu thuộc một họ năng lực khác với mô phỏng đã chọn — "
            "cần chọn lại mô phỏng đúng họ hoặc từ chối trung thực.",
        )
    owned: set[str] = set()
    for m in spec.family_memberships:
        if m.family_id.value == fam:
            owned |= set(m.owned_mechanisms)
    if prescribed not in owned:
        return (
            ErrorCode.GATE_MECHANISM_OWNERSHIP,
            "Đề yêu cầu một cơ chế mà engine tất định của mô phỏng này không sở hữu "
            "— hệ từ chối trung thực thay vì minh hoạ bằng cơ chế khác.",
        )
    return None
