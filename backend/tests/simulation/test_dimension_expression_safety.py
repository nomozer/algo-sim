# -*- coding: utf-8 -*-
"""Unit, minimal-pair, metamorphic, negative-domain, bridge/planner, and OCR safety tests
for the Phase 3–5 Dimension-Aware Mathematical Expression Model (Stage P1a)."""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json

import pytest

from app.ai import fact_extraction, function_calling
from app.ingestion.ocr_reconcile import (
    has_shared_corruption,
    is_mathlike,
    norm_math,
    reconcile_local_ocr,
)
from app.simulation.geometry.expression import (
    ANGLE,
    AREA,
    DerivedQuantityRecord,
    ExprDimensionError,
    ExprDomainError,
    ExprParseError,
    FactRole,
    LENGTH,
    SCALAR,
    SlotQuantityEntry,
    SymbolEnvironment,
    VOLUME,
    dim_add,
    dim_div,
    dim_mul,
    dim_pow,
    dim_sqrt,
    evaluate_quantity,
    parse_measurement_unit,
    parse_quantity_expr,
    scan_expression_prefix,
    substitute_symbol,
    validate_unit_consistency,
)
from app.simulation.geometry.radical import Radical, display as radical_display, radical, sqrt_rational
from app.simulation.geometry_functions import engine, planner, registry
from app.simulation.geometry_functions.typed_fact_next import parse_typed_fact_next_v2
from app.simulation.geometry_functions.typed_fact_next_bridge import (
    bridge_v2,
    quantity_premise_provenance,
)


# ── 1. EXACT PARSING, KERNEL REUSE & PROVENANCE ───────────────────────────────


@pytest.mark.parametrize(
    "raw,expected_coeff,expected_syms,expected_dim,expected_canon",
    [
        ("a", Fraction(1), (("a", 1),), LENGTH, "a"),
        ("2a", Fraction(2), (("a", 1),), LENGTH, "2a"),
        ("2 a", Fraction(2), (("a", 1),), LENGTH, "2a"),
        ("a√3", radical(1, 3), (("a", 1),), LENGTH, "a√3"),
        ("a*sqrt(3)", radical(1, 3), (("a", 1),), LENGTH, "a√3"),
        ("2√13a", radical(2, 13), (("a", 1),), LENGTH, "2a√13"),
        ("a/√3", radical(Fraction(1, 3), 3), (("a", 1),), LENGTH, "a√3/3"),
        ("a²", Fraction(1), (("a", 2),), AREA, "a²"),
        ("a^2", Fraction(1), (("a", 2),), AREA, "a²"),
        ("a ^ 2", Fraction(1), (("a", 2),), AREA, "a²"),
        ("a*a", Fraction(1), (("a", 2),), AREA, "a²"),
        ("3a²", Fraction(3), (("a", 2),), AREA, "3a²"),
        ("3,5a²", Fraction(7, 2), (("a", 2),), AREA, "7a²/2"),
        ("a²/2", Fraction(1, 2), (("a", 2),), AREA, "a²/2"),
        ("(2a)²", Fraction(4), (("a", 2),), AREA, "4a²"),
        ("(a√3)²", Fraction(3), (("a", 2),), AREA, "3a²"),
        ("a³", Fraction(1), (("a", 3),), VOLUME, "a³"),
        ("a^3", Fraction(1), (("a", 3),), VOLUME, "a³"),
        ("a³/3", Fraction(1, 3), (("a", 3),), VOLUME, "a³/3"),
        ("27√13a³/2", radical(Fraction(27, 2), 13), (("a", 3),), VOLUME, "27a³√13/2"),
        ("(a√2)³", radical(2, 2), (("a", 3),), VOLUME, "2a³√2"),
        ("4πa³/3", radical(Fraction(4, 3), 1, mu=1), (("a", 3),), VOLUME, "4πa³/3"),
    ],
)
def test_exact_vietnamese_expression_parsing_and_kernel_monomials(
    raw, expected_coeff, expected_syms, expected_dim, expected_canon
):
    q = parse_quantity_expr(raw)
    ev = evaluate_quantity(
        q,
        symbol_dims={"a": LENGTH},
        certified_positive_symbols={"a"},
        expected_dim=expected_dim,
        require_positive=True,
    )
    assert isinstance(ev.coeff, (Fraction, Radical))
    assert ev.coeff == expected_coeff
    assert ev.symbols == expected_syms
    assert ev.dimension == expected_dim
    assert ev.format_canonical() == expected_canon


def test_exact_character_span_and_operand_provenance():
    sentence = "Cho hình chóp tứ giác đều có diện tích đáy bằng (2a)² (tham khảo hình bên dưới)."
    idx = sentence.index("(2a)²")
    scanned = scan_expression_prefix(sentence, idx)
    assert scanned is not None
    qexpr, end_pos = scanned
    assert sentence[qexpr.provenance.source_span[0] : qexpr.provenance.source_span[1]] == "(2a)²"
    assert end_pos == idx + len("(2a)²")
    assert qexpr.provenance.original_expr == "(2a)²"
    assert qexpr.provenance.normalized_expr == "(2a)²"
    assert qexpr.provenance.role == FactRole.SOURCE_QUANTITY
    assert ("num:2", idx + 1, idx + 2) in qexpr.provenance.operand_spans
    assert ("sym:a", idx + 2, idx + 3) in qexpr.provenance.operand_spans


# ── 2. MINIMAL PAIRS (§7.5) & PREFIX SCANNER COMPLETENESS ────────────────────


def test_minimal_pairs_distinguished_exactly():
    env = {"a": LENGTH}
    pos = {"a"}

    # Minimal pair 1: 2a² vs (2a)²
    ev_2a2 = evaluate_quantity(parse_quantity_expr("2a²"), symbol_dims=env, certified_positive_symbols=pos)
    ev_p2a2 = evaluate_quantity(parse_quantity_expr("(2a)²"), symbol_dims=env, certified_positive_symbols=pos)
    assert (ev_2a2.coeff, ev_2a2.coeff_sq, ev_2a2.dimension) == (Fraction(2), Fraction(4), AREA)
    assert (ev_p2a2.coeff, ev_p2a2.coeff_sq, ev_p2a2.dimension) == (Fraction(4), Fraction(16), AREA)

    # Minimal pair 2: a²/2 vs a/(2²) vs (a/2)²
    ev_half_a2 = evaluate_quantity(parse_quantity_expr("a²/2"), symbol_dims=env, certified_positive_symbols=pos)
    ev_a_div_4 = evaluate_quantity(parse_quantity_expr("a/(2²)"), symbol_dims=env, certified_positive_symbols=pos)
    ev_a_div_2sq = evaluate_quantity(parse_quantity_expr("a/2²"), symbol_dims=env, certified_positive_symbols=pos)
    ev_half_a_sq = evaluate_quantity(parse_quantity_expr("(a/2)²"), symbol_dims=env, certified_positive_symbols=pos)
    assert (ev_half_a2.coeff, ev_half_a2.dimension) == (Fraction(1, 2), AREA)
    assert (ev_a_div_4.coeff, ev_a_div_4.dimension) == (Fraction(1, 4), LENGTH)
    assert (ev_a_div_2sq.coeff, ev_a_div_2sq.dimension) == (Fraction(1, 4), LENGTH)
    assert (ev_half_a_sq.coeff, ev_half_a_sq.dimension) == (Fraction(1, 4), AREA)

    # Minimal pair 3: a√3 vs √(3a)
    ev_a_rt3 = evaluate_quantity(parse_quantity_expr("a√3"), symbol_dims=env, certified_positive_symbols=pos)
    assert (ev_a_rt3.coeff, ev_a_rt3.dimension) == (radical(1, 3), LENGTH)
    for bad_rad in ("√(3a)", "sqrt(3a)", "√a"):
        with pytest.raises(ExprDimensionError) as exc:
            evaluate_quantity(parse_quantity_expr(bad_rad), symbol_dims=env, certified_positive_symbols=pos)
        assert exc.value.code == "FRACTIONAL_DIMENSION"

    # Minimal pair 4: 3,5 vs 3,5,6
    ev_dec = evaluate_quantity(parse_quantity_expr("3,5"), expected_dim=LENGTH, require_positive=True)
    assert ev_dec.coeff == Fraction(7, 2)
    with pytest.raises(ExprParseError) as exc_list:
        parse_quantity_expr("3,5,6")
    assert exc_list.value.code == "INVALID_DECIMAL_LIST"


@pytest.mark.parametrize(
    "bad_token,expected_code",
    [
        ("a2", "AMBIGUOUS_POSTFIX_NUMBER"),
        ("a3", "AMBIGUOUS_POSTFIX_NUMBER"),
        ("(2a)2", "AMBIGUOUS_POSTFIX_NUMBER"),
        ("3 5", "ADJACENT_NUMBERS"),
        ("AB", "INVALID_IDENTIFIER"),
        ("ABCD", "INVALID_IDENTIFIER"),
        ("a²ln2", "INVALID_IDENTIFIER"),
        ("a²³", "AMBIGUOUS_EXPONENT"),
        ("-3", "SIGNED_VALUE_FORBIDDEN"),
        ("-a", "SIGNED_VALUE_FORBIDDEN"),
    ],
)
def test_malformed_or_corrupted_tokens_fail_closed(bad_token, expected_code):
    with pytest.raises(ExprParseError) as exc:
        parse_quantity_expr(bad_token, allow_signed=False)
    assert exc.value.code == expected_code
    assert scan_expression_prefix(bad_token, 0) is None


# ── 3. DIMENSION ALGEBRA & DISPLAY-UNIT SEPARATION ────────────────────────────


def test_dimension_lattice_and_unit_separation_without_conversion():
    assert dim_add(AREA, AREA) == AREA
    assert dim_mul(LENGTH, AREA) == VOLUME
    assert dim_div(VOLUME, AREA) == LENGTH
    assert dim_pow(LENGTH, 3) == VOLUME
    assert dim_sqrt(AREA) == LENGTH
    assert dim_div(ANGLE, ANGLE) == SCALAR

    with pytest.raises(ExprDimensionError):
        dim_add(LENGTH, AREA)
    with pytest.raises(ExprDimensionError):
        dim_add(ANGLE, SCALAR)
    with pytest.raises(ExprDimensionError):
        dim_mul(ANGLE, LENGTH)
    with pytest.raises(ExprDimensionError):
        dim_sqrt(VOLUME)

    u_cm2 = parse_measurement_unit("cm²")
    u_m2 = parse_measurement_unit("(m^2)")
    u_mm3 = parse_measurement_unit("mm3")
    assert u_cm2 is not None and u_m2 is not None and u_mm3 is not None
    assert u_cm2.dimension == AREA and u_m2.dimension == AREA
    assert u_cm2.base_metric_unit == "cm" and u_m2.base_metric_unit == "m"
    assert u_mm3.dimension == VOLUME and u_mm3.canonical_unit == "mm³"

    # Same metric base ('cm' and 'cm²') is consistent; mixing 'cm²' and 'm²' refuses fail-closed.
    u_cm = parse_measurement_unit("cm")
    assert u_cm is not None
    assert validate_unit_consistency([u_cm, u_cm2]) == "cm"
    with pytest.raises(ExprDimensionError) as exc_mix:
        validate_unit_consistency([u_cm2, u_m2])
    assert exc_mix.value.code == "UNIT_SYSTEM_MISMATCH"

    # Unit dimension must match slot dimension (e.g. cm³ cannot sit in LENGTH).
    with pytest.raises(ExprDimensionError) as exc_slot:
        validate_unit_consistency([u_mm3], expected_dim=LENGTH)
    assert exc_slot.value.code == "UNIT_DIMENSION_MISMATCH"


# ── 4. NEGATIVE RULES (§6.6) & DOMAIN OBLIGATIONS ─────────────────────────────


def test_negative_rules_inhomogeneous_sum_volume_on_segment_and_linear_on_area():
    # L + L^2 inside an expression
    with pytest.raises(ExprDimensionError) as exc_sum:
        evaluate_quantity(
            parse_quantity_expr("a + a²"),
            symbol_dims={"a": LENGTH},
            certified_positive_symbols={"a"},
        )
    assert exc_sum.value.code == "DIMENSION_MISMATCH"

    # SCALAR + LENGTH (`2 + a`)
    with pytest.raises(ExprDimensionError) as exc_sc:
        evaluate_quantity(
            parse_quantity_expr("2 + a"),
            symbol_dims={"a": LENGTH},
            certified_positive_symbols={"a"},
        )
    assert exc_sc.value.code == "DIMENSION_MISMATCH"

    # Volume expression assigned to segment_length alongside SA = a
    with pytest.raises(ExprDimensionError) as exc_vol_seg:
        SymbolEnvironment.bind_slots(
            [
                SlotQuantityEntry("p1", "value", "a", LENGTH),
                SlotQuantityEntry("p2", "value", "a³", LENGTH),
            ]
        )
    assert exc_vol_seg.value.code == "DIMENSION_MISMATCH"

    # Linear expression `4a` assigned to polygon_area alongside SA = a (closes prior doc_so bug!)
    with pytest.raises(ExprDimensionError) as exc_lin_area:
        SymbolEnvironment.bind_slots(
            [
                SlotQuantityEntry("p1", "value", "a", LENGTH),
                SlotQuantityEntry("p2", "value", "4a", AREA),
            ]
        )
    assert exc_lin_area.value.code == "DIMENSION_MISMATCH"


def test_negative_radicand_zero_divisor_and_cancellation_domain_loss():
    # Negative radicand
    for neg_rad in ("√(-4)", "sqrt(2 - 5)"):
        with pytest.raises(ExprDomainError) as exc_neg:
            evaluate_quantity(parse_quantity_expr(neg_rad, allow_signed=True))
        assert exc_neg.value.code == "NEGATIVE_RADICAND"

    # Zero divisor (including eager check on `0 * (1/0)` and `0^0`)
    for zero_div in ("1/0", "a/0", "2a√3/0", "a/(2 - 2)", "0*(1/0)", "(2 - 2)^0"):
        with pytest.raises(ExprDomainError) as exc_zd:
            evaluate_quantity(
                parse_quantity_expr(zero_div, allow_signed=True),
                symbol_dims={"a": LENGTH},
                certified_positive_symbols={"a"},
            )
        assert exc_zd.value.code == "ZERO_DIVISOR"

    # Domain loss 1: √(a²) without positivity certificate must NOT simplify |a| -> a
    with pytest.raises(ExprDomainError) as exc_abs:
        evaluate_quantity(
            parse_quantity_expr("√(4a²)"),
            symbol_dims={"a": LENGTH},
            certified_positive_symbols=frozenset(),
        )
    assert exc_abs.value.code == "DOMAIN_SIGN_UNPROVED"

    # With certified a > 0, √(4a²) == 2a and records positive_obligations={'a'}
    ev_pos = evaluate_quantity(
        parse_quantity_expr("√(4a²)"),
        symbol_dims={"a": LENGTH},
        certified_positive_symbols={"a"},
        expected_dim=LENGTH,
        require_positive=True,
    )
    assert ev_pos.coeff == Fraction(2) and ev_pos.positive_obligations == frozenset({"a"})

    # Domain loss 2: x/x or a*(x/x) with ungrounded symbol x must NOT silently erase x
    with pytest.raises(ExprDomainError) as exc_cancel:
        SymbolEnvironment.bind_slots(
            [
                SlotQuantityEntry("p1", "value", "a", LENGTH),
                SlotQuantityEntry("p2", "ratio", "x/x", SCALAR),
            ]
        )
    assert exc_cancel.value.code == "UNGROUNDED_SYMBOL"

    # Domain loss 3: dividing by symbol `a` without nonzero certificate fails closed
    with pytest.raises(ExprDomainError) as exc_nz:
        evaluate_quantity(
            parse_quantity_expr("2a / a"),
            symbol_dims={"a": LENGTH},
            certified_positive_symbols=frozenset(),
            certified_nonzero_symbols=frozenset(),
        )
    assert exc_nz.value.code == "UNCERTAIN_DIVISOR_ZERO"


def test_ungrounded_symbols_and_non_homogeneous_premises_fail_closed():
    # Free symbol in scalar ratio slot
    with pytest.raises(ExprDomainError) as exc_free:
        SymbolEnvironment.bind_slots([SlotQuantityEntry("p1", "ratio", "2x", SCALAR)])
    assert exc_free.value.code == "UNGROUNDED_SYMBOL"

    # Mixing numeric metric and symbolic metric premises
    with pytest.raises(ExprDomainError) as exc_mix:
        SymbolEnvironment.bind_slots(
            [
                SlotQuantityEntry("p1", "value", "3", LENGTH),
                SlotQuantityEntry("p2", "value", "a²", AREA),
            ]
        )
    assert exc_mix.value.code == "NON_HOMOGENEOUS_LENGTHS"

    # Two independent unlinked length symbols ('a' and 'b')
    with pytest.raises(ExprDomainError) as exc_two:
        SymbolEnvironment.bind_slots(
            [
                SlotQuantityEntry("p1", "value", "a", LENGTH),
                SlotQuantityEntry("p2", "value", "b", LENGTH),
            ]
        )
    assert exc_two.value.code == "NON_HOMOGENEOUS_LENGTHS"

    # UNVERIFIED_CANDIDATE hard-blocked
    with pytest.raises(ExprDomainError):
        SymbolEnvironment.bind_slots(
            [
                SlotQuantityEntry(
                    "p1", "value", "a", LENGTH, role=FactRole.UNVERIFIED_CANDIDATE
                )
            ]
        )


# ── 5. CONTEXT-DRIVEN TYPING & NON-LENGTH SINGLE-SYMBOL GUARD (#17 §3.2) ──────


def test_symbol_names_never_dictate_dimension_and_non_length_symbol_guard():
    # Symbol named 'V' used in a LENGTH slot + 'V³/3' in a VOLUME slot -> V is typed as LENGTH!
    plan_v_len = SymbolEnvironment.bind_slots(
        [
            SlotQuantityEntry("p1", "value", "V", LENGTH),
            SlotQuantityEntry("p2", "value", "V³/3", VOLUME),
            SlotQuantityEntry("p3", "ratio", "2/3", SCALAR),
        ]
    )
    assert plan_v_len.symbol_dims == {"V": LENGTH}
    assert plan_v_len.length_unit_symbol == "V"
    assert plan_v_len.non_length_scale_symbol is None
    plan_v_len.check_goal_admissibility([1, 2, 3])

    # Single-premise area symbol ('S' OR 'a'!) gets dim=AREA, NEVER coerced to length_unit_symbol!
    for sym_name in ("S", "a"):
        plan_area_only = SymbolEnvironment.bind_slots(
            [SlotQuantityEntry("p1", "value", sym_name, AREA)]
        )
        assert plan_area_only.symbol_dims == {sym_name: AREA}
        assert plan_area_only.length_unit_symbol is None
        assert plan_area_only.non_length_scale_symbol == (sym_name, AREA)
        for pos_deg in (1, 2, 3):
            with pytest.raises(ExprDomainError) as exc_guard:
                plan_area_only.check_goal_admissibility([pos_deg])
            assert exc_guard.value.code == "EXACT_DOMAIN_EXCEEDED"
        # Certified scale-invariant L^0 goal is admissible
        plan_area_only.check_goal_admissibility([0], target_invariant=True)

    # Single-premise volume symbol ('V' OR 'a'!) gets dim=VOLUME, NEVER coerced to length_unit_symbol!
    for sym_name in ("V", "a"):
        plan_vol_only = SymbolEnvironment.bind_slots(
            [SlotQuantityEntry("p1", "value", sym_name, VOLUME)]
        )
        assert plan_vol_only.symbol_dims == {sym_name: VOLUME}
        assert plan_vol_only.length_unit_symbol is None
        assert plan_vol_only.non_length_scale_symbol == (sym_name, VOLUME)
        with pytest.raises(ExprDomainError) as exc_vguard:
            plan_vol_only.check_goal_admissibility([1])
        assert exc_vguard.value.code == "EXACT_DOMAIN_EXCEEDED"


# ── 6. DIMENSIONAL METAMORPHIC SCALING (§11.1) ────────────────────────────────


@pytest.mark.parametrize("scale_str,k", [("2a", Fraction(2)), ("3a", Fraction(3)), ("(5/2)a", Fraction(5, 2))])
def test_dimensional_metamorphic_scaling_laws(scale_str, k):
    cases = [
        ("2a√3", LENGTH, 1),
        ("3,5a²", AREA, 2),
        ("27√13a³/2", VOLUME, 3),
        ("2a/(3a)", SCALAR, 0),
    ]
    for expr_str, dim, deg in cases:
        orig = parse_quantity_expr(expr_str)
        scaled = substitute_symbol(orig, "a", scale_str)
        ev_orig = evaluate_quantity(
            orig, symbol_dims={"a": LENGTH}, certified_positive_symbols={"a"}, expected_dim=dim
        )
        ev_scaled = evaluate_quantity(
            scaled, symbol_dims={"a": LENGTH}, certified_positive_symbols={"a"}, expected_dim=dim
        )
        assert ev_scaled.dimension == dim
        assert ev_scaled.coeff_sq == ev_orig.coeff_sq * (k ** (2 * deg))


# ── 7. BRIDGE, PLANNER PASSTHROUGH & FROZEN PROVIDER FINGERPRINTS ─────────────


def test_bridge_and_planner_preserve_source_quantities_and_frozen_schemas():
    problem_text = (
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 2, "
        "diện tích đáy bằng 4 và thể tích khối chóp S.ABCD bằng 4/3. "
        "Tính khoảng cách từ A đến mặt phẳng (SBC)."
    )
    raw_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": problem_text,
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp tứ giác đều S.ABCD",
            }
        ],
        "premises": [
            {
                "kind": "regular_pyramid",
                "args": {"apex": "S", "base": ["A", "B", "C", "D"]},
                "quote": "Cho hình chóp tứ giác đều S.ABCD",
                "solid_id": "s1",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["S", "A"], "value": "2"},
                "quote": "cạnh bên bằng 2",
                "solid_id": "s1",
            },
            {
                "kind": "face_area",
                "args": {"polygon": ["A", "B", "C", "D"], "value": "4", "shape": "polygon"},
                "quote": "diện tích đáy bằng 4",
                "solid_id": "s1",
            },
            {
                "kind": "solid_volume",
                "args": {"solid": "S.ABCD", "value": "4/3"},
                "quote": "thể tích khối chóp S.ABCD bằng 4/3",
                "solid_id": "s1",
            },
        ],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": "Cho hình chóp tứ giác đều S.ABCD",
            }
        ],
        "math_goals": [
            {
                "goal_id": "g1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "A", "plane": ["S", "B", "C"]},
                "quote": "Tính khoảng cách từ A đến mặt phẳng (SBC).",
                "solid_id": "s1",
            }
        ],
    }
    validated = parse_typed_fact_next_v2(raw_payload)
    prov = quantity_premise_provenance(validated)
    assert [(r["kind"], r["slot_dimension"], r["role"]) for r in prov] == [
        ("segment_length", "LENGTH", "SOURCE_QUANTITY"),
        ("face_area", "AREA", "SOURCE_QUANTITY"),
        ("solid_volume", "VOLUME", "SOURCE_QUANTITY"),
    ]
    for r in prov:
        s, e = r["source_span"]
        assert problem_text[s:e] == r["original_expr"]

    bridged = bridge_v2(raw_payload)
    fact_kinds = [f["kind"] for f in bridged["facts"]]
    # AREA(base) stays polygon_area and VOLUME(solid) stays solid_volume — NEVER rewritten into side/height!
    assert "polygon_area" in fact_kinds
    assert "solid_volume" in fact_kinds
    assert not any(
        f["kind"] == "length" and f.get("measure") in ("base_edge", "height")
        for f in bridged["facts"]
    )

    plan = planner.lap_ke_hoach(bridged, problem_text=problem_text)
    call_fns = [c["fn"] for c in plan.calls]
    assert "polygon_area" in call_fns
    assert "solid_volume" in call_fns
    reg_base = next(c for c in plan.calls if c["fn"] == "regular_polygon")
    assert "side" not in reg_base["args"]

    rec = DerivedQuantityRecord(
        rule_id="SQUARE_AREA_TO_SIDE",
        target_entity="ABCD",
        target_dimension=LENGTH,
        premise_call_ids=("p2_prem",),
        value_sq_unit=Fraction(4),
        symbolic_unit=None,
    ).to_dict()
    assert rec["role"] == "VERIFIED_DERIVED_QUANTITY"
    assert rec["value_sq_unit"] == "4"

    # Verify all 5 frozen provider fingerprints & pinned component versions remain byte-identical.
    assert registry.REGISTRY_VERSION == "geometry-functions/33"
    assert planner.PLANNER_VERSION == "geometry-fact-planner/26"
    assert engine.ENGINE_VERSION == "geometry-function-engine/24"
    assert (
        fact_extraction.surface_fingerprint("flat")
        == "485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a"
    )
    assert (
        fact_extraction.surface_fingerprint("v3")
        == "4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f"
    )
    assert (
        function_calling.surface_fingerprint()
        == "7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25"
    )
    tf_sha = hashlib.sha256(
        json.dumps(planner.TypedFact.model_json_schema(), sort_keys=True, ensure_ascii=False).encode(
            "utf-8"
        )
    ).hexdigest()
    assert tf_sha.startswith("aa9d93eeac")
    fn_sha = hashlib.sha256(
        json.dumps(registry.function_declarations(), sort_keys=True, ensure_ascii=False).encode(
            "utf-8"
        )
    ).hexdigest()
    assert fn_sha == "5ceb0f999d4d7c1ee37c02207ea6470a7f972a168d6c52fa597392934d86f169"


# ── 8. OCR EXPONENT / SUPERSCRIPT FIDELITY & METRIC UNIT BOUNDARY ─────────────


def _ocr_line(words: list[str], y: int = 10) -> dict:
    x = 10
    ws = []
    for w in words:
        w_px = max(12, len(w) * 10)
        ws.append({"text": w, "bbox": [x, y, x + w_px, y + 20], "conf": 0.99})
        x += w_px + 8
    return {"text": " ".join(words), "bbox": [10, y, x, y + 20], "conf": 0.99, "words": ws}


def _ocr_raw(r_lines: list[dict], t_lines: list[dict]) -> dict:
    return {
        "width": 800,
        "height": 200,
        "engines": {"rapidocr": {"lines": r_lines}, "tesseract": {"lines": t_lines}},
    }


def test_ocr_superscript_math_classification_and_unit_vs_variable_boundary():
    assert is_mathlike("a²") is True
    assert is_mathlike("a³") is True
    assert norm_math("mm2") == "mm²"
    assert norm_math("4mm3") == "4mm³"
    assert norm_math("cm2") == "cm²"

    for bad in ("a2", "a3", "2a2", "27√13a3/2", "a”", 'a"'):
        assert has_shared_corruption(bad) is True, bad
    for clean in ("a²", "a³", "2a²", "27√13a³/2", "mm2", "cm2", "dm2", "km2", "m2", "4mm3", "scene3d", '"chóp"', '"góc"'):
        assert has_shared_corruption(clean) is False, clean

    # Cross-reader disagreement on superscript ('a²' vs 'a2') -> EXPONENT_SUPERSCRIPT_DISAGREEMENT
    rec_dis = reconcile_local_ocr(
        _ocr_raw([_ocr_line(["bằng", "a²."])], [_ocr_line(["bằng", "a2."])]),
        min_agreeing_families=2,
    )
    assert rec_dis["extraction_verified"] is False
    unc = {s["text"]: s for s in rec_dis["uncertain_spans"]}
    assert "a²." in unc and unc["a²."]["reason"] == "EXPONENT_SUPERSCRIPT_DISAGREEMENT"

    # Agreed broken superscript ('a2' + 'a2') -> never auto-verified!
    rec_corrupt = reconcile_local_ocr(
        _ocr_raw([_ocr_line(["bằng", "a2."])], [_ocr_line(["bằng", "a2."])]),
        min_agreeing_families=2,
    )
    assert rec_corrupt["extraction_verified"] is False

    # Agreed valid superscript ('a²' + 'a²') and metric unit ('4mm2' + '4mm²') -> verified!
    rec_ok = reconcile_local_ocr(
        _ocr_raw([_ocr_line(["bằng", "a²", "và", "4mm2."])], [_ocr_line(["bằng", "a²", "và", "4mm²."])]),
        min_agreeing_families=2,
    )
    assert rec_ok["extraction_verified"] is True, rec_ok["uncertain_spans"]


# ── 9. STAGE P1b END-TO-END VIETNAMESE CLAUSES & MINIMAL PAIRS (§7.1–7.5) ─────


@pytest.mark.parametrize(
    "text,expected_answer",
    [
        # "Diện tích đáy bằng a²" (unnamed base area)
        (
            "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a². "
            "Tính khoảng cách từ A đến mặt phẳng (SBC).",
            "a√6/3",
        ),
        # "Diện tích tam giác ABC bằng a²/2" (named right-isosceles triangle area)
        (
            "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại A, diện tích tam giác ABC bằng a²/2, "
            "SA vuông góc với mặt phẳng đáy và SA = a. Tính thể tích khối chóp S.ABC.",
            "a³/6",
        ),
        # "Thể tích hình chóp bằng a³/3" (unnamed solid volume -> derives height SA = a)
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy, "
            "thể tích hình chóp bằng a³/3. Tính khoảng cách từ A đến mặt phẳng (SBC).",
            "a√2/2",
        ),
        # "Cạnh đáy bằng 2a" + "Độ dài đường cao bằng a√3" (standalone role sentences)
        (
            "Cho hình chóp tứ giác đều S.ABCD. Cạnh đáy bằng 2a. Độ dài đường cao bằng a√3. "
            "Tính thể tích khối chóp S.ABCD.",
            "4a³√3/3",
        ),
        # "Tỉ số hai cạnh AB và BC bằng 2/3" (explicit ordered segment ratio)
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 2a, tỉ số hai cạnh AB và BC bằng 2/3, "
            "SA vuông góc với mặt phẳng đáy và SA = a. Tính thể tích khối chóp S.ABCD.",
            "2a³",
        ),
        # "Tỉ số giữa cạnh bên và cạnh đáy bằng 3/2" (role-ordered segment ratio)
        (
            "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2a, tỉ số giữa cạnh bên và cạnh đáy bằng 3/2. "
            "Tính thể tích khối chóp S.ABCD.",
            "4a³√7/3",
        ),
    ],
)
def test_end_to_end_vietnamese_quantity_clauses_serve_exact_answers(text: str, expected_answer: str):
    from app.ai.adaptive_input_router import route_text_input
    from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally

    lp = parse_geometry_problem_locally(text, use_cache=False)
    assert lp.status == LOCAL_PARSE_COMPLETE, lp.to_dict()
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "SERVED", out.response
    assert out.telemetry.total_provider_calls == 0
    assert out.response["route_d"]["answers"]["q1"] == expected_answer


def test_unordered_ambiguous_ratio_and_corrupted_values_fail_closed():
    from app.ai.adaptive_input_router import route_text_input
    from app.ai.local_geometry_parser import (
        LOCAL_PARSE_AMBIGUOUS,
        LOCAL_PARSE_COMPLETE,
        parse_geometry_problem_locally,
    )

    # Unordered "Tỉ số hai cạnh bằng 2/3" -> explicit LOCAL_PARSE_AMBIGUOUS / AMBIGUOUS_FACT (never silently picks an order)
    ambig_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 2a, tỉ số hai cạnh bằng 2/3, "
        "SA vuông góc với mặt phẳng đáy và SA = a. Tính thể tích khối chóp S.ABCD."
    )
    lp_ambig = parse_geometry_problem_locally(ambig_text, use_cache=False)
    assert lp_ambig.status == LOCAL_PARSE_AMBIGUOUS
    assert lp_ambig.reason_code == "AMBIGUOUS_FACT"
    out_ambig = route_text_input(ambig_text, allow_live_ai=False)
    assert out_ambig.status == "REFUSED"
    assert out_ambig.response["envelope"]["reason_code"] == "AMBIGUOUS_FACT"
    assert out_ambig.response["route_d"]["refusal"]["clarification"]["nlu_class"] == "AMBIGUOUS"

    # Unparseable / corrupted quantity tokens keep UNREAD_VALUE@ and NEVER claim LOCAL_PARSE_COMPLETE
    for bad_text in (
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a²ln2. Tính thể tích khối chóp S.ABCD.",
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a2. Tính thể tích khối chóp S.ABCD.",
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 5 và cạnh đáy bằng 3,5,6. Tính thể tích khối chóp S.ABCD.",
    ):
        lp_bad = parse_geometry_problem_locally(bad_text, use_cache=False)
        assert lp_bad.status != LOCAL_PARSE_COMPLETE and lp_bad.payload is None, (bad_text, lp_bad.to_dict())
        assert any(
            str(n).startswith("UNREAD_VALUE@")
            for c in lp_bad.source_coverage.clauses
            for n in (c.get("notes") or ())
        ), (bad_text, lp_bad.source_coverage.clauses)


def test_end_to_end_vietnamese_minimal_pairs():
    from app.ai.adaptive_input_router import route_text_input

    # Minimal pair 1: 2a² vs (2a)²
    out_2a2 = route_text_input(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3a và diện tích đáy bằng 2a². "
        "Tính thể tích khối chóp S.ABCD.",
        allow_live_ai=False,
    )
    out_p2a2 = route_text_input(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3a và diện tích đáy bằng (2a)². "
        "Tính thể tích khối chóp S.ABCD.",
        allow_live_ai=False,
    )
    assert out_2a2.status == "SERVED" and out_2a2.response["route_d"]["answers"]["q1"] == "4a³√2/3"
    assert out_p2a2.status == "SERVED" and out_p2a2.response["route_d"]["answers"]["q1"] == "4a³√7/3"
    assert out_2a2.response["route_d"]["answers"]["q1"] != out_p2a2.response["route_d"]["answers"]["q1"]

    # Minimal pair 2: a²/2 vs (a/2)² vs a/(2²)
    out_a2_2 = route_text_input(
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại A, diện tích tam giác ABC bằng a²/2, "
        "SA vuông góc với mặt phẳng đáy và SA = a. Tính thể tích khối chóp S.ABC.",
        allow_live_ai=False,
    )
    out_pa_2_sq = route_text_input(
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại A, diện tích tam giác ABC bằng (a/2)², "
        "SA vuông góc với mặt phẳng đáy và SA = a. Tính thể tích khối chóp S.ABC.",
        allow_live_ai=False,
    )
    out_a_div_4 = route_text_input(
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại A, diện tích tam giác ABC bằng a/(2²), "
        "SA vuông góc với mặt phẳng đáy và SA = a. Tính thể tích khối chóp S.ABC.",
        allow_live_ai=False,
    )
    assert out_a2_2.status == "SERVED" and out_a2_2.response["route_d"]["answers"]["q1"] == "a³/6"
    assert out_pa_2_sq.status == "SERVED" and out_pa_2_sq.response["route_d"]["answers"]["q1"] == "a³/12"
    # `a/(2²)` is L^1 assigned to L^2 area slot alongside SA = a -> dimension mismatch refused!
    assert out_a_div_4.status == "REFUSED"
    assert out_a_div_4.response["envelope"]["reason_code"] == "INCONSISTENT_FACTS"

    # Minimal pair 3: a√3 vs √(3a)
    out_a_rt3 = route_text_input(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2a và chiều cao bằng a√3. "
        "Tính thể tích khối chóp S.ABCD.",
        allow_live_ai=False,
    )
    out_rt_3a = route_text_input(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2a và chiều cao bằng √(3a). "
        "Tính thể tích khối chóp S.ABCD.",
        allow_live_ai=False,
    )
    assert out_a_rt3.status == "SERVED" and out_a_rt3.response["route_d"]["answers"]["q1"] == "4a³√3/3"
    assert out_rt_3a.status == "REFUSED"
    assert out_rt_3a.response["envelope"]["reason_code"] == "INCONSISTENT_FACTS"

    # Minimal pair 4: 3,5 (decimal) vs 3,5,6 (list)
    out_dec = route_text_input(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 3,5 và chiều cao bằng 3. "
        "Tính thể tích khối chóp S.ABCD.",
        allow_live_ai=False,
    )
    out_list = route_text_input(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 3,5,6 và chiều cao bằng 3. "
        "Tính thể tích khối chóp S.ABCD.",
        allow_live_ai=False,
    )
    assert out_dec.status == "SERVED" and out_dec.response["route_d"]["answers"]["q1"] == "49/4"
    assert out_list.status == "REFUSED"


# ── 10. FACT ROLES, CERTIFIED DERIVATIONS & CONTRADICTIONS (§8.1–8.5) ─────────


def test_certified_derivation_rules_record_verified_derived_quantity_and_block_uncertified_or_contradictory():
    from app.ai.adapter4_route import run_typed_fact_next_v2_route
    from app.ai.adaptive_input_router import route_text_input
    from app.ai.local_geometry_parser import parse_geometry_problem_locally

    # 1. Equilateral triangle area -> side (`EQUILATERAL_TRIANGLE_AREA_TO_SIDE`)
    eq_text = (
        "Cho hình chóp tam giác đều S.ABC có cạnh bên bằng a và diện tích đáy bằng a²√3/4. "
        "Tính thể tích khối chóp S.ABC."
    )
    lp_eq = parse_geometry_problem_locally(eq_text, use_cache=False)
    res_eq = run_typed_fact_next_v2_route(lp_eq.payload)
    assert res_eq.status == "SERVED" and res_eq.answer_exact["q1"]["coef"] == "√2/12"
    dq_eq = (res_eq.details or {}).get("derived_quantities") or []
    assert any(d["rule_id"] == "EQUILATERAL_TRIANGLE_AREA_TO_SIDE" and d["role"] == "VERIFIED_DERIVED_QUANTITY" for d in dq_eq)

    # 2. Rectangle area + known side -> adjacent side (`RECTANGLE_AREA_AND_SIDE_TO_ADJACENT_SIDE`)
    rect_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = a, diện tích đáy bằng 2a², "
        "SA vuông góc với mặt phẳng đáy và SA = a. Tính thể tích khối chóp S.ABCD."
    )
    lp_rect = parse_geometry_problem_locally(rect_text, use_cache=False)
    res_rect = run_typed_fact_next_v2_route(lp_rect.payload)
    assert res_rect.status == "SERVED" and res_rect.answer_exact["q1"]["coef"] == "2/3"
    dq_rect = (res_rect.details or {}).get("derived_quantities") or []
    assert any(d["rule_id"] == "RECTANGLE_AREA_AND_SIDE_TO_ADJACENT_SIDE" and d["value_sq_unit"] == "4" for d in dq_rect)

    # 3. Solid volume + base area -> height (`SOLID_VOLUME_AND_BASE_AREA_TO_HEIGHT`)
    vol_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy, "
        "thể tích khối chóp S.ABCD bằng a³/3. Tính độ dài cạnh SB."
    )
    lp_vol = parse_geometry_problem_locally(vol_text, use_cache=False)
    res_vol = run_typed_fact_next_v2_route(lp_vol.payload)
    assert res_vol.status == "SERVED" and res_vol.answer_exact["q1"]["coef"] == "√2"
    dq_vol = (res_vol.details or {}).get("derived_quantities") or []
    assert any(d["rule_id"] == "SOLID_VOLUME_AND_BASE_AREA_TO_HEIGHT" and d["role"] == "VERIFIED_DERIVED_QUANTITY" for d in dq_vol)

    # 4. Illustrative construction quantity (`ILLUSTRATIVE_CONSTRUCTION_QUANTITY`) is never treated as SOURCE_QUANTITY
    illus_out = route_text_input(
        "Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB. "
        "Tính góc giữa hai mặt phẳng (SBC) và (ABC).",
        allow_live_ai=False,
    )
    assert illus_out.status == "SERVED"
    cfg = illus_out.response["route_d"]["scene_configuration"]
    assert cfg["kind"] == "TARGET_INVARIANT_ILLUSTRATIVE"
    assert cfg["source_length_supplied"] is False
    assert any(
        st.get("fact_role") == "ILLUSTRATIVE_CONSTRUCTION_QUANTITY"
        for st in illus_out.response["route_d"]["construction_trace"]
    )

    # 4b. Uncertified derivation blocked: general quadrilateral ABCD (not certified square) with area a² NEVER derives side = a
    uncert_res = engine.dung_tu_loi_goi(
        "Cho hình chóp S.ABCD có SA vuông góc với mặt phẳng đáy, SA = a và diện tích đáy bằng a². "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
        {
            "calls": [
                {"id": "s1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Cho hình chóp S.ABCD"]}},
                {"id": "p1", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["SA vuông góc với mặt phẳng đáy"]}},
                {"id": "p2", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}, "source": {"quotes": ["SA = a"]}},
                {"id": "p3", "fn": "polygon_area", "args": {"polygon": ["A", "B", "C", "D"], "value": "a²"}, "source": {"quotes": ["diện tích đáy bằng a²"]}},
                {"id": "q1", "fn": "ask_distance_point_plane", "args": {"point": "A", "plane": ["S", "B", "C"]}, "source": {"quotes": ["Tính khoảng cách từ A đến mặt phẳng (SBC)."]}},
            ]
        },
    )
    assert uncert_res.status == "REFUSED" and uncert_res.code == "MISSING_DIMENSION"
    assert not ((uncert_res.details or {}).get("derived_quantities") or [])

    # 5. Contradictions fail closed (`INCONSISTENT_FACTS`)
    for contra_text in (
        "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a, cạnh bên bằng 2a và diện tích đáy bằng 4a². "
        "Tính thể tích khối chóp S.ABCD.",
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy, SA = a "
        "và thể tích khối chóp S.ABCD bằng a³. Tính độ dài cạnh SB.",
        "Cho hình chóp tứ giác đều S.ABCD có diện tích đáy bằng s và chiều cao bằng s. "
        "Tính thể tích khối chóp S.ABCD.",
    ):
        out_c = route_text_input(contra_text, allow_live_ai=False)
        assert out_c.status == "REFUSED", contra_text
        assert out_c.response["envelope"]["reason_code"] == "INCONSISTENT_FACTS", out_c.response


# ── 11. END-TO-END DIMENSIONAL METAMORPHICS (§11.1) ───────────────────────────


def test_end_to_end_dimensional_metamorphics():
    from app.ai.adaptive_input_router import route_text_input

    # 1. Alpha-renaming of length parameter (`a -> x`, `a -> v`)
    out_x = route_text_input(
        "Cho hình chóp tứ giác đều S.ABCD có độ dài cạnh bên bằng x và diện tích đáy bằng x². "
        "Tính khoảng cách từ A đến mặt phẳng (SBC) theo x.",
        allow_live_ai=False,
    )
    assert out_x.status == "SERVED" and out_x.response["route_d"]["answers"]["q1"] == "x√6/3"

    # Symbol letter `v` in a LENGTH slot (`cạnh bên bằng v`) + `v²` in AREA slot -> typed by context as LENGTH, not VOLUME!
    out_v = route_text_input(
        "Cho hình chóp tứ giác đều S.ABCD có độ dài cạnh bên bằng v và diện tích đáy bằng v². "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
        allow_live_ai=False,
    )
    assert out_v.status == "SERVED" and out_v.response["route_d"]["answers"]["q1"] == "v√6/3"

    # 2. Vertex & solid renaming (`S.ABCD -> T.MNPQ`) + clause reordering (`A -> M, B -> N, C -> P, D -> Q, S -> T`)
    out_renamed = route_text_input(
        "Cho hình chóp tứ giác đều T.MNPQ có diện tích đáy bằng a² và độ dài cạnh bên bằng a. "
        "Tính khoảng cách từ M đến mặt phẳng (TNP).",
        allow_live_ai=False,
    )
    assert out_renamed.status == "SERVED" and out_renamed.response["route_d"]["answers"]["q1"] == "a√6/3"

    # 3. Algebraic surface equivalence (`a²`, `a^2`, `a*a`, `(a)²`)
    for area_expr in ("a²", "a^2", "a*a", "(a)²"):
        out_eq = route_text_input(
            f"Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng {area_expr}. "
            "Tính khoảng cách từ A đến mặt phẳng (SBC).",
            allow_live_ai=False,
        )
        assert out_eq.status == "SERVED", (area_expr, out_eq.response)
        assert out_eq.response["route_d"]["answers"]["q1"] == "a√6/3"

    # 4. Consistent metric display units (`3cm` and `9cm²` -> side = 3, distance = √6)
    out_cm = route_text_input(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3cm và diện tích đáy bằng 9cm². "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
        allow_live_ai=False,
    )
    assert out_cm.status == "SERVED" and out_cm.response["route_d"]["answers"]["q1"] == "√6"

    # 5. Inhomogeneous sum `a + a²` rejected fail-closed
    out_inhom = route_text_input(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a + a². "
        "Tính thể tích khối chóp S.ABCD.",
        allow_live_ai=False,
    )
    assert out_inhom.status == "REFUSED"
    assert out_inhom.response["envelope"]["reason_code"] == "INCONSISTENT_FACTS"


# ── 12. ALL 8 SOURCE GATE MUTATION CLASSES FROM VERIFIED `SERVED` BASELINES (§11.3) ──


def _served_baseline_calls(stem: str) -> list[dict]:
    from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally
    from app.simulation.geometry_functions import planner
    from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2

    lp = parse_geometry_problem_locally(stem, use_cache=False)
    assert lp.status == LOCAL_PARSE_COMPLETE, (stem, lp.to_dict())
    bridged = bridge_v2(lp.parsed_contract)
    planned = planner.lap_ke_hoach({"facts": bridged["facts"]}, stem)
    base_res = engine.dung_tu_loi_goi(stem, {"calls": planned.calls})
    assert base_res.status == "SERVED", (stem, base_res)
    return planned.calls


def test_goal_degrees_exact_parity_with_registry_and_engine():
    from app.simulation.geometry.expression import Dimension, GOAL_DEGREES, goal_dimension

    ask_fns_in_registry = {k for k, v in registry.REGISTRY.items() if v.kind == "ask"}
    assert set(GOAL_DEGREES) == ask_fns_in_registry
    assert GOAL_DEGREES == engine.BAC_DAI_LUONG == registry._BAC_HAM_HOI_TAT_CA
    for fn, deg in GOAL_DEGREES.items():
        dim = goal_dimension(fn)
        if fn.startswith("ask_angle"):
            assert dim == ANGLE
        else:
            assert dim == Dimension(deg, False)


def test_wrong_dimension_and_mixed_metric_units_refused_end_to_end_and_in_source_gate():
    from copy import deepcopy
    from app.ai.adaptive_input_router import route_text_input

    # Positive controls: consistent metric scales (`3cm` + `9cm²`, `3km` + `9km²`) SERVE exact `√6`
    for ok_stem in (
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3cm và diện tích đáy bằng 9cm². "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3km và diện tích đáy bằng 9km². "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
    ):
        ok_out = route_text_input(ok_stem, allow_live_ai=False)
        assert ok_out.status == "SERVED", ok_out.response
        assert ok_out.response["route_d"]["answers"]["q1"] == "√6"
        assert ok_out.telemetry.total_provider_calls == 0

    # P1b-1 & P1b-2: Wrong-dimension metric units and mixed metric base scales MUST deterministically REFUSE
    # (`INCONSISTENT_FACTS`, 0 provider calls, never `SERVED`, never HTTP 503 `LIVE_AI_DISABLED` fallback).
    for bad_stem in (
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3cm và diện tích đáy bằng 9cm. "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3cm, SA vuông góc với mặt phẳng đáy, "
        "thể tích khối chóp S.ABCD bằng 9cm. Tính độ dài cạnh SB.",
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3cm² và diện tích đáy bằng 9cm². "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3cm³, SA vuông góc với mặt phẳng đáy và SA = 4cm. "
        "Tính thể tích khối chóp S.ABCD.",
        "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 2cm, tỉ số hai cạnh AB và BC bằng 2cm, "
        "SA vuông góc với mặt phẳng đáy và SA = 3cm. Tính thể tích khối chóp S.ABCD.",
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3km và diện tích đáy bằng 9cm². "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3m và diện tích đáy bằng 9cm². "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3mm và diện tích đáy bằng 9cm². "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
    ):
        bad_out = route_text_input(bad_stem, allow_live_ai=False)
        assert bad_out.status == "REFUSED", (bad_stem, bad_out.response)
        assert bad_out.telemetry.total_provider_calls == 0
        assert bad_out.response["envelope"]["reason_code"] == "INCONSISTENT_FACTS", (bad_stem, bad_out.response)

    # Direct Source Gate check even when caller truncates the wrong unit out of `quotes` (`"diện tích đáy bằng 9"` on `"9cm"`)
    ok_calls = _served_baseline_calls(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3cm và diện tích đáy bằng 9cm². "
        "Tính khoảng cách từ A đến mặt phẳng (SBC)."
    )
    trunc_calls = deepcopy(ok_calls)
    for c in trunc_calls:
        if c["fn"] == "polygon_area":
            c["source"] = {"quotes": ["diện tích đáy bằng 9"]}
    direct_bad = engine.dung_tu_loi_goi(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3cm và diện tích đáy bằng 9cm. "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
        {"calls": trunc_calls},
    )
    assert direct_bad.status == "REFUSED" and direct_bad.code == "INCONSISTENT_FACTS"


def test_hallucinated_shape_on_unnamed_base_area_refused_at_source_gate():
    rhom_stem = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thoi, góc BAD bằng 60°, "
        "SA vuông góc với mặt phẳng đáy, SA = a và diện tích đáy bằng a². "
        "Tính thể tích khối chóp S.ABCD."
    )
    for bad_shape in ("square", "rectangle"):
        res = engine.dung_tu_loi_goi(
            rhom_stem,
            {
                "calls": [
                    {"id": "s1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Cho hình chóp S.ABCD"]}},
                    {"id": "p0", "fn": "rhombus", "args": {"vertices": ["A", "B", "C", "D"]}, "source": {"quotes": ["đáy ABCD là hình thoi"]}},
                    {"id": "p1", "fn": "vertex_angle", "args": {"vertex": "A", "rays": ["B", "D"], "value": "60", "unit": "deg"}, "source": {"quotes": ["góc BAD bằng 60°"]}},
                    {"id": "p2", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quotes": ["SA vuông góc với mặt phẳng đáy"]}},
                    {"id": "p3", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}, "source": {"quotes": ["SA = a"]}},
                    {"id": "p4", "fn": "polygon_area", "args": {"polygon": ["A", "B", "C", "D"], "value": "a²", "shape": bad_shape}, "source": {"quotes": ["diện tích đáy bằng a²"]}},
                    {"id": "q1", "fn": "ask_volume", "args": {"solid": "S.ABCD"}, "source": {"quotes": ["Tính thể tích khối chóp S.ABCD."]}},
                ]
            },
        )
        assert res.status == "REFUSED", (bad_shape, res)
        assert res.code == "PREDICATE_NOT_IN_QUOTE", (bad_shape, res)
        assert res.reason.startswith("p4:"), (bad_shape, res.reason)

    tri_stem = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = a, "
        "SA vuông góc với mặt phẳng đáy, SA = a và diện tích đáy bằng a²/2. "
        "Tính thể tích khối chóp S.ABC."
    )
    res_tri = engine.dung_tu_loi_goi(
        tri_stem,
        {
            "calls": [
                {"id": "s1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]}, "source": {"quotes": ["Cho hình chóp S.ABC"]}},
                {"id": "p0", "fn": "right_angle", "args": {"vertex": "B", "rays": ["A", "C"]}, "source": {"quotes": ["đáy ABC là tam giác vuông tại B"]}},
                {"id": "p1", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "a"}, "source": {"quotes": ["AB = a"]}},
                {"id": "p2", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]}, "source": {"quotes": ["SA vuông góc với mặt phẳng đáy"]}},
                {"id": "p3", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}, "source": {"quotes": ["SA = a"]}},
                {"id": "p4", "fn": "polygon_area", "args": {"polygon": ["A", "B", "C"], "value": "a²/2", "shape": "equilateral_triangle"}, "source": {"quotes": ["diện tích đáy bằng a²/2"]}},
                {"id": "q1", "fn": "ask_volume", "args": {"solid": "S.ABC"}, "source": {"quotes": ["Tính thể tích khối chóp S.ABC."]}},
            ]
        },
    )
    assert res_tri.status == "REFUSED" and res_tri.code == "PREDICATE_NOT_IN_QUOTE"
    assert res_tri.reason.startswith("p4:"), res_tri.reason


def test_all_eight_source_gate_mutation_classes_isolated_from_served_baselines():
    from copy import deepcopy

    b1_stem = (
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a². "
        "Tính khoảng cách từ A đến mặt phẳng (SBC)."
    )
    b1_calls = _served_baseline_calls(b1_stem)

    # M1 (`altered_quote`): perturb ONLY `polygon_area`'s quote -> `QUOTE_NOT_IN_SOURCE` on that call
    m1_calls = deepcopy(b1_calls)
    m1_id = next(c["id"] for c in m1_calls if c["fn"] == "polygon_area")
    for c in m1_calls:
        if c["id"] == m1_id:
            c["source"] = {"quotes": ["diện tích mặt đáy ABCD bằng a²"]}
    r_m1 = engine.dung_tu_loi_goi(b1_stem, {"calls": m1_calls})
    assert r_m1.status == "REFUSED" and r_m1.code == "QUOTE_NOT_IN_SOURCE" and r_m1.reason.startswith(f"{m1_id}:")

    # M2 (`swapped_entity`): perturb ONLY `polygon_area`'s target polygon on a SERVED named-area baseline -> `OBJECT_NOT_IN_QUOTE`
    b2_stem = (
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích hình vuông ABCD bằng a². "
        "Tính thể tích khối chóp S.ABCD."
    )
    b2_calls = _served_baseline_calls(b2_stem)
    m2_calls = deepcopy(b2_calls)
    m2_id = next(c["id"] for c in m2_calls if c["fn"] == "polygon_area")
    for c in m2_calls:
        if c["id"] == m2_id:
            c["args"] = {"polygon": ["S", "A", "B"], "value": "a²"}
    r_m2 = engine.dung_tu_loi_goi(b2_stem, {"calls": m2_calls})
    assert r_m2.status == "REFUSED" and r_m2.code == "OBJECT_NOT_IN_QUOTE" and r_m2.reason.startswith(f"{m2_id}:")

    # M3 (`area_rewritten_as_length_premise`): rewrite ONLY `polygon_area` into `segment_length(AB, "a")` -> `UNGROUNDED_VALUE`
    m3_calls = deepcopy(b1_calls)
    for c in m3_calls:
        if c["id"] == m1_id:
            c["fn"] = "segment_length"
            c["args"] = {"segment": ["A", "B"], "value": "a"}
    r_m3 = engine.dung_tu_loi_goi(b1_stem, {"calls": m3_calls})
    assert r_m3.status == "REFUSED" and r_m3.code == "UNGROUNDED_VALUE" and r_m3.reason.startswith(f"{m1_id}:")

    # M4 (`ungrounded_number` & `exponent_mutation`): perturb ONLY `polygon_area`'s value (`"2a²"` and `"a³"`) -> `UNGROUNDED_VALUE`
    for bad_val in ("2a²", "a³"):
        m4_calls = deepcopy(b1_calls)
        for c in m4_calls:
            if c["id"] == m1_id:
                c["args"]["value"] = bad_val
        r_m4 = engine.dung_tu_loi_goi(b1_stem, {"calls": m4_calls})
        assert r_m4.status == "REFUSED" and r_m4.code == "UNGROUNDED_VALUE" and r_m4.reason.startswith(f"{m1_id}:")

    # M5 (`dropped_negation`): start from SERVED perpendicular baseline, negate ONLY the altitude sentence -> `NEGATED_CLAUSE`
    b5_stem = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a và SA = a. "
        "Biết SA vuông góc với mặt phẳng đáy. Tính thể tích khối chóp S.ABCD."
    )
    b5_calls = _served_baseline_calls(b5_stem)
    m5_stem = b5_stem.replace("SA vuông góc", "SA không vuông góc")
    m5_calls = deepcopy(b5_calls)
    m5_id = next(c["id"] for c in m5_calls if c["fn"] == "perpendicular_line_plane")
    for c in m5_calls:
        if c["id"] == m5_id:
            c["source"] = {"quotes": ["SA không vuông góc với mặt phẳng đáy"]}
    r_m5 = engine.dung_tu_loi_goi(m5_stem, {"calls": m5_calls})
    assert r_m5.status == "REFUSED" and r_m5.code == "NEGATED_CLAUSE" and r_m5.reason.startswith(f"{m5_id}:")

    # M6 (`goal_turned_into_premise`): start from SERVED baseline, append `Chứng minh ...` and inject premise -> `GOAL_CLAUSE_NOT_PREMISE`
    b6_stem = (
        "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a và cạnh bên bằng 2a. "
        "Tính thể tích khối chóp S.ABCD."
    )
    b6_calls = _served_baseline_calls(b6_stem)
    m6_stem = (
        "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a và cạnh bên bằng 2a. "
        "Chứng minh diện tích đáy ABCD bằng a². Tính thể tích khối chóp S.ABCD."
    )
    m6_calls = deepcopy(b6_calls) + [
        {
            "id": "p_goal",
            "fn": "polygon_area",
            "args": {"polygon": ["A", "B", "C", "D"], "value": "a²"},
            "source": {"quotes": ["Chứng minh diện tích đáy ABCD bằng a²."]},
        }
    ]
    r_m6 = engine.dung_tu_loi_goi(m6_stem, {"calls": m6_calls})
    assert r_m6.status == "REFUSED" and r_m6.code == "GOAL_CLAUSE_NOT_PREMISE" and r_m6.reason.startswith("p_goal:")

    # M7 (`silent_dropped_quantity_clause`): start from SERVED baseline, drop `SB = a√2` call -> `SOURCE_PREMISE_UNREAD`
    b7_stem = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy, "
        "SA = a và SB = a√2. Tính thể tích khối chóp S.ABCD."
    )
    b7_calls = _served_baseline_calls(b7_stem)
    m7_calls = [
        c for c in deepcopy(b7_calls)
        if not (c["fn"] == "segment_length" and set(c["args"]["segment"]) == {"S", "B"})
    ]
    r_m7 = engine.dung_tu_loi_goi(b7_stem, {"calls": m7_calls})
    assert r_m7.status == "REFUSED" and r_m7.code == "SOURCE_PREMISE_UNREAD"

    # M8 (`symbol_dimension_conflict`): start from SERVED baseline, change `"a²"` -> `"4a"` in BOTH text & call -> `INCONSISTENT_FACTS`
    m8_stem = b1_stem.replace("diện tích đáy bằng a²", "diện tích đáy bằng 4a")
    m8_calls = deepcopy(b1_calls)
    for c in m8_calls:
        if c["id"] == m1_id:
            c["args"]["value"] = "4a"
            c["source"] = {"quotes": ["diện tích đáy bằng 4a"]}
    r_m8 = engine.dung_tu_loi_goi(m8_stem, {"calls": m8_calls})
    assert r_m8.status == "REFUSED" and r_m8.code == "INCONSISTENT_FACTS"


# ── 13. EXPOSED DEVELOPMENT REGRESSION `vmmu_r537` (§10.1) ────────────────────


def test_exposed_development_case_area_a_squared_end_to_end_text_and_confirmed_ocr():
    from pathlib import Path
    from app.ai.adapter4_route import run_typed_fact_next_v2_route
    from app.ai.adaptive_input_router import route_edited_text_input, route_text_input
    from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally

    # Independent hand-derived Euclidean oracle in Q(√2, √3):
    # Square ABCD of area 1 => side s = 1: A=(0,0,0), B=(1,0,0), C=(1,1,0), D=(0,1,0), center O=(1/2, 1/2, 0).
    # AO^2 = 1/2; lateral edge SA = 1 => SO^2 = SA^2 - AO^2 = 1/2 => S = (1/2, 1/2, 1/√2).
    # Plane (SBC) contains B=(1,0,0), C=(1,1,0), S=(1/2,1/2,1/√2): normal n = (1, 0, 1/√2), n(B)=1, n(A)=0.
    # Therefore d(A, (SBC))^2 = (1 - 0)^2 / (1^2 + 0^2 + (1/√2)^2) = 1 / (3/2) = 2/3 => d = √(2/3)a = a√6/3.
    ao_sq = Fraction(1, 2)
    so_sq = Fraction(1, 1) - ao_sq
    om_sq = Fraction(1, 4)
    sm_sq = so_sq + om_sq
    d_o_sq = (so_sq * om_sq) / sm_sq
    d_a_sq_oracle = Fraction(4, 1) * d_o_sq
    assert d_a_sq_oracle == Fraction(2, 3)
    oracle_display = f"a{radical_display(sqrt_rational(d_a_sq_oracle))}"
    assert oracle_display == "a√6/3"

    # Real OCR/source text of exposed development case `vmmu_r537` (tested generically with zero case-ID hardcoding)
    source_text = (
        "Cho hình chóp tứ giác đều S.ABCD có độ dài cạnh bên bằng a và diện tích đáy bằng a² "
        "(tham khảo hình bên dưới). Khoảng cách từ A đến mặt phẳng (SBC) bằng"
    )
    lp = parse_geometry_problem_locally(source_text, use_cache=False)
    assert lp.status == LOCAL_PARSE_COMPLETE, lp.to_dict()
    assert lp.payload["length_unit"] == "a"
    # Source premise MUST stay `face_area` (`a²`), never rewritten into `segment_length(AB, a)`
    prem_kinds = [(p["kind"], p["args"]) for p in lp.payload["premises"]]
    assert any(k == "face_area" and a.get("value") == "a²" for k, a in prem_kinds)
    assert not any(k == "segment_length" and set(a.get("segment") or ()) == {"A", "B"} for k, a in prem_kinds)

    # Verify kernel derivation & exact answer
    kres = run_typed_fact_next_v2_route(lp.payload)
    assert kres.status == "SERVED" and kres.kernel_check is True
    assert kres.answer_exact["q1"] == {"coef": "√6/3", "dim": 1, "unit": "a"}
    dqs = (kres.details or {}).get("derived_quantities") or []
    assert any(
        d["rule_id"] == "SQUARE_AREA_TO_SIDE"
        and d["role"] == "VERIFIED_DERIVED_QUANTITY"
        and d["value_sq_unit"] == "1"
        and d["symbolic_unit"] == "a"
        for d in dqs
    )

    # Verify text route + Scene3D + output-policy/1
    out_txt = route_text_input(source_text, allow_live_ai=False)
    assert out_txt.status == "SERVED"
    assert out_txt.telemetry.total_provider_calls == 0
    assert out_txt.response["route_d"]["answers"]["q1"] == oracle_display
    scene = out_txt.response["envelope"]["scene3d"]
    pt_ids = {o["id"] for o in scene["objects"] if o["type"] == "point3"}
    assert {"S", "A", "B", "C", "D"} <= pt_ids
    assert len(scene.get("events") or []) >= 2

    # Verify local dual-OCR superscript fidelity + Rule 5 diagram-reference confirmation gate + confirmed OCR route
    ocr_check = reconcile_local_ocr(
        _ocr_raw([_ocr_line(source_text.split())], [_ocr_line(source_text.split())]),
        min_agreeing_families=2,
    )
    assert ocr_check["draft_text"] == source_text
    assert ocr_check["uncertain_spans"] == []
    assert ocr_check["blocking_reasons"] == ["DIAGRAM_FACTS_UNVERIFIED"]
    out_ocr = route_edited_text_input(ocr_check["draft_text"], allow_live_ai=False)
    assert out_ocr.status == "SERVED"
    assert out_ocr.response["route_d"]["answers"]["q1"] == oracle_display

    # Verify zero case-ID hardcoding anywhere under backend/app/
    app_root = Path(__file__).resolve().parents[2] / "app"
    for py_file in app_root.rglob("*.py"):
        src = py_file.read_text(encoding="utf-8")
        assert "r537" not in src and "r460" not in src and "r463" not in src, str(py_file)

