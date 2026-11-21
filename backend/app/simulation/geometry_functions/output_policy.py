# -*- coding: utf-8 -*-
"""Source-grounded Output Policy (`output-policy/1`):
    Exact Answer -> Requested Unit -> Requested Formatting -> Rounded Display.

Guarantees:
- Exact Kernel values (`Fraction` / `Radical`, `answer_exact[gid]["coef"]`, and `scene3d` quantity values)
  are 100% preserved and never rounded before mathematical verification.
- Exact degree display (`0°`, `30°`, `45°`, `60°`, `90°`) is served only when `cos²(θ) ∈ {1, 3/4, 1/2, 1/4, 0}`
  (by Niven's Theorem); non-special angles without an explicit rounding specification fail closed with
  `EXACT_DOMAIN_EXCEEDED` instead of floating-point `arccos` approximation.
- Decimal rounding (`ROUND_HALF_UP`) of exact radicals `v = (p/q)√r ≥ 0` is computed and certified using
  100% arbitrary-precision integer arithmetic (`math.isqrt`, zero `float`).
"""
from __future__ import annotations

from fractions import Fraction
import math
import re
from typing import Any

from app.simulation.geometry.radical import Radical

OUTPUT_POLICY_SCHEMA_VERSION = "output-policy/1"

_SPECIAL_COS2_TO_DEG: dict[Fraction, int] = {
    Fraction(1, 1): 0,
    Fraction(3, 4): 30,
    Fraction(1, 2): 45,
    Fraction(1, 4): 60,
    Fraction(0, 1): 90,
}


def exact_cos2_to_degrees(cos2: Fraction | int) -> tuple[bool, str | None, int | None]:
    """Convert an exact rational `cos²(θ)` in `[0, 1]` to an exact integer degree string when rational by Niven's Theorem."""
    q = Fraction(cos2)
    deg = _SPECIAL_COS2_TO_DEG.get(q)
    if deg is None:
        return False, None, None
    return True, f"{deg}°", deg


def round_exact_radical_half_up(
    value: Radical | Fraction | int,
    *,
    decimals: int,
    decimal_separator: str = ",",
) -> dict[str, Any]:
    """Round a non-negative `Radical` / `Fraction` to `decimals` decimal places (`ROUND_HALF_UP`)
    using 100% exact integer arithmetic (zero `float`).

    Let `v = √(num / den) ≥ 0` and `S = 10^decimals`.
    Then `k = ⌊S·v + 1/2⌋` is the unique non-negative integer satisfying:
        (2k - 1)² · den ≤ 4 · S² · num < (2k + 1)² · den   (for k ≥ 1; and 0 ≤ 4·S²·num < den for k = 0).
    """
    if not isinstance(decimals, int) or decimals < 0 or decimals > 6:
        raise ValueError(f"Unsupported rounding decimals: {decimals!r}")

    if isinstance(value, Radical):
        if value.he < 0:
            raise ValueError("Negative radical not supported for geometric distance/area/volume rounding")
        v_sq = (Fraction(value.he) * Fraction(value.he)) * Fraction(value.can)
    else:
        f_val = Fraction(value)
        if f_val < 0:
            raise ValueError("Negative value not supported")
        v_sq = f_val * f_val

    num = v_sq.numerator
    den = v_sq.denominator
    scale = 10**decimals
    scale_sq = scale * scale

    # Exact integer floor of `2 * S * den * √(num / den) = √(4 * S² * num * den)`:
    four_s2_num = 4 * scale_sq * num
    isqrt_val = math.isqrt(four_s2_num * den)
    k = (isqrt_val + den) // (2 * den)

    # Verify the two exact integer inequalities:
    lb_lhs = ((2 * k - 1) ** 2) * den if k > 0 else 0
    ub_rhs = ((2 * k + 1) ** 2) * den
    lb_ok = lb_lhs <= four_s2_num
    ub_ok = four_s2_num < ub_rhs
    if not (lb_ok and ub_ok):
        raise RuntimeError(f"Integer rounding bound check failed for v²={v_sq}, decimals={decimals}")

    if decimals == 0:
        formatted = str(k)
    else:
        int_part = k // scale
        frac_part = k % scale
        formatted = f"{int_part}{decimal_separator}{frac_part:0{decimals}d}"

    return {
        "rounded_display": formatted,
        "decimals": decimals,
        "mode": "ROUND_HALF_UP",
        "decimal_separator": decimal_separator,
        "scaled_integer": k,
        "lower_bound_verified": lb_ok,
        "upper_bound_verified": ub_ok,
        "lower_bound_lhs_int": str(lb_lhs),
        "middle_scaled_sq_int": str(four_s2_num),
        "upper_bound_rhs_int": str(ub_rhs),
        "used_floating_point": False,
    }


_ROUNDING_PLACE_PATTERNS: tuple[tuple[re.Pattern[str], int], ...] = (
    (re.compile(r"hàng\s+phần\s+mười|1\s+chữ\s+số\s+thập\s+phân|một\s+chữ\s+số\s+thập\s+phân", re.I), 1),
    (re.compile(r"hàng\s+phần\s+trăm|2\s+chữ\s+số\s+thập\s+phân|hai\s+chữ\s+số\s+thập\s+phân", re.I), 2),
    (re.compile(r"hàng\s+phần\s+nghìn|3\s+chữ\s+số\s+thập\s+phân|ba\s+chữ\s+số\s+thập\s+phân", re.I), 3),
    (re.compile(r"hàng\s+đơn\s+vị|số\s+nguyên\s+gần\s+nhất|0\s+chữ\s+số\s+thập\s+phân", re.I), 0),
)


def parse_rounding_spec_from_text(text: str) -> dict[str, Any] | None:
    """Extract a deterministic rounding specification from a Vietnamese clause, or `None` if no rounding is mentioned.
    If `'làm tròn'` is present without a recognized precision target, returns `{'mode': 'UNSPECIFIED_PRECISION', 'decimals': None}`."""
    if not text or not re.search(r"\blàm\s+tròn\b", text, re.IGNORECASE):
        return None
    matched_decimals: set[int] = set()
    for pat, dec in _ROUNDING_PLACE_PATTERNS:
        if pat.search(text):
            matched_decimals.add(dec)
    if len(matched_decimals) != 1:
        return {"mode": "UNSPECIFIED_PRECISION", "decimals": None}
    return {
        "mode": "ROUND_HALF_UP",
        "decimals": next(iter(matched_decimals)),
        "decimal_separator": ",",
    }


def has_degree_request_in_text(phrase_text: str, tail_text: str) -> bool:
    """Return True iff the asked phrase or its closed tail explicitly requests degree measure (`số đo góc`, `theo độ`, `(đơn vị: độ)`)."""
    if re.search(r"(?:^|\b)số\s+đo\s+(?:của\s+)?góc\b", phrase_text, re.IGNORECASE):
        return True
    if re.search(
        r"\btheo\s+(?:đơn\s+vị\s+(?:góc\s+)?)?độ\b|\(\s*đơn\s+vị(?:\s+góc)?\s*:?\s*độ\s*\)",
        tail_text,
        re.IGNORECASE,
    ):
        return True
    return False


def verify_goal_output_policy_in_source(
    *,
    fn: str,
    phrase_text: str,
    tail_text: str,
    policy: dict[str, Any] | None,
    has_param_a: bool,
) -> bool:
    """Verify that a declared `output_policy` on an `ask_*` call matches the verbatim source question 1-to-1."""
    if not policy:
        return False
    req_unit = policy.get("requested_unit")
    rounding = policy.get("rounding")
    if req_unit is None and rounding is None:
        return False

    is_angle = fn in ("ask_angle_lines", "ask_angle_line_plane", "ask_angle_plane_plane")
    source_asks_deg = has_degree_request_in_text(phrase_text, tail_text)
    if req_unit is not None:
        if req_unit != "deg" or not is_angle or not source_asks_deg:
            return False
    elif is_angle and source_asks_deg:
        return False

    source_rounding = parse_rounding_spec_from_text(tail_text)
    if rounding is not None:
        if not isinstance(rounding, dict) or rounding.get("mode") != "ROUND_HALF_UP":
            return False
        dec = rounding.get("decimals")
        if type(dec) is not int or not (0 <= dec <= 6):
            return False
        if source_rounding is None or source_rounding.get("decimals") != dec:
            return False
    elif source_rounding is not None:
        return False

    return True


def apply_output_policies_to_result(
    result: Any,
    output_policies: dict[str, dict[str, Any]] | None,
) -> Any:
    """Apply verified output policies (`Exact Answer -> Requested Unit -> Requested Formatting -> Rounded Display`)
    to a `SERVED` `KetQuaTuyen` without mutating Exact Kernel memory (`exec_result.final_memory`) or `answer_exact.coef`."""
    from app.simulation.geometry_functions import KetQuaTuyen

    if result.status != "SERVED" or not output_policies:
        return result

    fm = result.exec_result.final_memory if result.exec_result else {}
    calls_by_id = {c["id"]: c for c in (result.calls or ())}

    for gid, pol in output_policies.items():
        if gid not in result.answers or gid not in result.answer_exact:
            continue
        req_unit = pol.get("requested_unit")
        rounding = pol.get("rounding")
        if req_unit is None and rounding is None:
            continue

        call_info = calls_by_id.get(gid) or {}
        fn_name = str(call_info.get("fn") or "")
        raw_val = fm.get(f"kq_{gid}")
        exact_sym = str(result.answers[gid])
        exact_entry = dict(result.answer_exact[gid])

        if req_unit == "deg":
            if not fn_name.startswith("ask_angle_") or raw_val is None:
                return KetQuaTuyen(
                    "REFUSED",
                    "QUESTION_CONTEXT_UNSUPPORTED",
                    f"{gid}: đơn vị độ chỉ áp dụng cho mục tiêu góc",
                    (gid,),
                    planner=result.planner,
                )
            ok_deg, deg_str, deg_int = exact_cos2_to_degrees(Fraction(raw_val))
            if not ok_deg or deg_str is None:
                return KetQuaTuyen(
                    "REFUSED",
                    "EXACT_DOMAIN_EXCEEDED",
                    f"{gid}: cos²={exact_entry.get('coef')} không tương ứng số đo góc độ hữu tỉ chính xác trong {{0°, 30°, 45°, 60°, 90°}}",
                    (gid,),
                    planner=result.planner,
                )
            display_str = deg_str
            fmt_record: dict[str, Any] = {
                "kind": "exact_special_angle_deg",
                "degrees": deg_int,
            }
            if rounding is not None:
                dec = int(rounding["decimals"])
                sep = str(rounding.get("decimal_separator") or ",")
                rnd = round_exact_radical_half_up(Fraction(deg_int), decimals=dec, decimal_separator=sep)
                display_str = f"{rnd['rounded_display']}°"
                fmt_record["rounding"] = rnd

            exact_entry["exact_symbolic"] = exact_sym
            exact_entry["output_policy"] = {
                "schema_version": OUTPUT_POLICY_SCHEMA_VERSION,
                "exact_answer": exact_sym,
                "requested_unit": "deg",
                "requested_formatting": fmt_record,
                "rounded_display": display_str,
            }
            result.answer_exact[gid] = exact_entry
            result.answers[gid] = display_str
            continue

        if rounding is not None:
            if exact_entry.get("dim", 0) > 0 and result.length_unit:
                return KetQuaTuyen(
                    "REFUSED",
                    "QUESTION_CONTEXT_UNSUPPORTED",
                    f"{gid}: không làm tròn số thập phân cho biểu thức còn chứa tham số độ dài ký hiệu {result.length_unit!r}",
                    (gid,),
                    planner=result.planner,
                )
            if raw_val is None:
                return KetQuaTuyen(
                    "REFUSED",
                    "QUESTION_CONTEXT_UNSUPPORTED",
                    f"{gid}: thiếu giá trị chính xác để làm tròn",
                    (gid,),
                    planner=result.planner,
                )
            dec = int(rounding["decimals"])
            sep = str(rounding.get("decimal_separator") or ",")
            rnd = round_exact_radical_half_up(raw_val, decimals=dec, decimal_separator=sep)
            display_str = rnd["rounded_display"]
            exact_entry["exact_symbolic"] = exact_sym
            exact_entry["output_policy"] = {
                "schema_version": OUTPUT_POLICY_SCHEMA_VERSION,
                "exact_answer": exact_sym,
                "requested_unit": None,
                "requested_formatting": rnd,
                "rounded_display": display_str,
            }
            result.answer_exact[gid] = exact_entry
            result.answers[gid] = display_str

    return result
