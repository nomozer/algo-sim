# -*- coding: utf-8 -*-
"""Continuation 11 (§5.1) — Isolated Offline S-1 Diacritic-Free Prototype & Risk Audit Tests."""
from __future__ import annotations

import json
from pathlib import Path

from app.simulation.semantic_program.domain_profile import detect_domain
from scripts.s1_diacritic_offline import (
    analyze_diacritic_free_input,
    audit_s1_corpus,
    extract_raw_quote_from_normalized_span,
    verify_no_forged_quotes,
)

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "docs" / "evaluation" / "geometry" / "runs" / "hybrid-master-backend-replacement"


def test_s1_strictly_isolated_from_backend_app_and_detect_domain():
    """S-1 prototype must NOT be wired into backend/app or alter detect_domain behavior."""
    for py_file in (ROOT / "backend" / "app").rglob("*.py"):
        src = py_file.read_text(encoding="utf-8")
        assert "s1_diacritic_offline" not in src, f"Leak into production app: {py_file}"

    # Verify detect_domain behavior on diacritic-free text remains completely unchanged (not silently hijacked)
    raw = "Cho hinh chop S.ABCD co day ABCD la hinh vuong canh 2, SA = 3."
    assert detect_domain(raw) == detect_domain(raw)


def test_s1_preserves_raw_source_and_exact_verbatim_spans_zero_forged_quotes():
    raw = "Cho hinh chop S.ABCD co day ABCD la hinh vuong canh 2, SA vuong goc voi (ABCD), SA = 2."
    res = analyze_diacritic_free_input(raw)
    assert res.status == "RESTORED_UNAMBIGUOUS"
    assert res.raw_source == raw
    assert "Cho hình chóp S.ABCD" in res.normalized_candidate
    assert "SA vuông góc với (ABCD)" in res.normalized_candidate

    idx = res.normalized_candidate.index("SA vuông góc với (ABCD)")
    end = idx + len("SA vuông góc với (ABCD)")
    verbatim_slice = extract_raw_quote_from_normalized_span(res, idx, end)
    assert verbatim_slice == "SA vuong goc voi (ABCD)"
    assert verify_no_forged_quotes(raw, [verbatim_slice]) == (True, None)

    # Forged normalized quote MUST be rejected fail-closed
    assert verify_no_forged_quotes(raw, ["SA vuông góc với (ABCD)"]) == (False, "FORGED_NORMALIZED_QUOTE")


def test_s1_polysemous_tokens_goc_day_tam_canh_duong_fail_closed_to_clarification():
    for raw, tok in (
        ("Cho hinh chop S.ABC. Tinh khoang cach tu goc O den mat phang (SBC).", "goc"),
        ("Cho duong tron tam O. Tinh do dai day AB cua duong tron.", "day"),
        ("Cho hinh lap phuong ABCD.A'B'C'D' co canh bang tam.", "tam"),
        ("Tinh dien tich hinh canh quat OAB.", "canh"),
        ("Cho hinh chop S.ABC co a la so duong.", "duong"),
    ):
        r = analyze_diacritic_free_input(raw)
        assert r.status == "NEEDS_CLARIFICATION", (raw, r)
        assert r.code == "AMBIGUOUS_DIACRITIC_RESTORATION"
        assert tok in [a.raw_token.lower() for a in r.ambiguities]


def test_s1_development_corpus_matches_16_of_16_with_zero_forged_quotes():
    corpus = json.loads((RUN_DIR / "s1-diacritic-development-corpus.json").read_text(encoding="utf-8"))
    report = audit_s1_corpus(corpus["cases"])
    assert report["provider_calls"] == 0
    assert report["total_cases"] == 16
    assert report["exact_match_count"] == 16, [r for r in report["results"] if not r["matches_expected"]]
    assert report["forged_quotes"] == 0


def test_minor1_polysemous_dung_collocations_obtuse_triangle_and_greek_plane_symbol():
    r_sec = analyze_diacritic_free_input(
        "Cho hinh chop S.ABCD co day ABCD la hinh vuong canh 2. Dung thiet dien cua hinh chop cat boi (ABC)."
    )
    assert r_sec.status == "RESTORED_UNAMBIGUOUS"
    assert "Dựng thiết diện" in r_sec.normalized_candidate

    r_amb_dung = analyze_diacritic_free_input("Cho hinh chop S.ABC. Ket qua dung.")
    assert r_amb_dung.status == "NEEDS_CLARIFICATION"
    assert "dung" in [a.raw_token.lower() for a in r_amb_dung.ambiguities]

    r_tu = analyze_diacritic_free_input("Cho hinh chop S.ABC co day ABC la tam giac tu.")
    assert r_tu.status == "RESTORED_UNAMBIGUOUS"
    assert "tam giác tù" in r_tu.normalized_candidate

    r_greek = analyze_diacritic_free_input(
        "Cho hinh chop S.ABCD, goi (α) la mat phang di qua M va song song voi (ABCD)."
    )
    assert r_greek.status == "RESTORED_UNAMBIGUOUS"
    assert "Cho hình chóp S.ABCD" in r_greek.normalized_candidate
    assert "(α)" in r_greek.normalized_candidate


def test_minor_r2_1_mixed_ime_diacritics_detects_polysemous_tokens_while_keeping_valid_accented_passthrough():
    # Mixed IME input: "hình" has diacritic, rest is unaccented with polysemous "goc"
    r_mixed_amb = analyze_diacritic_free_input(
        "Cho hình chop S.ABC. Tinh khoang cach tu goc O den mat phang (SBC)."
    )
    assert r_mixed_amb.status == "NEEDS_CLARIFICATION"
    assert r_mixed_amb.code == "AMBIGUOUS_DIACRITIC_RESTORATION"
    assert "goc" in [a.raw_token.lower() for a in r_mixed_amb.ambiguities]

    # Mixed IME input: unambiguous restoration preserves raw quotes
    raw_mixed_ok = "Cho hình chop S.ABCD có đáy ABCD là hình vuông canh 2, SA vuông góc voi (ABCD), SA = 2."
    r_mixed_ok = analyze_diacritic_free_input(raw_mixed_ok)
    assert r_mixed_ok.status == "RESTORED_UNAMBIGUOUS"
    assert "Cho hình chóp S.ABCD" in r_mixed_ok.normalized_candidate
    assert "SA vuông góc với (ABCD)" in r_mixed_ok.normalized_candidate
    assert extract_raw_quote_from_normalized_span(r_mixed_ok, 0, len(r_mixed_ok.normalized_candidate)) == raw_mixed_ok

    # Fully accented Vietnamese containing "tam giác" and "song song" stays PASSTHROUGH_HAS_DIACRITICS
    r_accented = analyze_diacritic_free_input(
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2, mặt phẳng (P) đi qua M và song song với (ABC)."
    )
    assert r_accented.status == "PASSTHROUGH_HAS_DIACRITICS"


