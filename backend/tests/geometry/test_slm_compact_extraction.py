# -*- coding: utf-8 -*-
"""Comprehensive tests for AXO HYBRID /6 compact extraction, Verified Normalizer, 9-field cache & local-slm route."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main as main_module
from app.ai import adaptive_input_router as AIR
from app.ai.local_slm_extractor import (
    DEFAULT_LOCAL_SLM_STRATEGY,
    SLM_COMPACT_SCHEMA_VERSION,
    SLM_GROUNDING_VALIDATOR_VERSION,
    build_compact_clause_context,
    build_compact_grammar_for_context,
    compute_local_slm_capability_identity,
    run_local_slm_extraction,
    validate_and_lower_compact_clause,
)
from app.ai.local_slm_runtime import (
    DEFAULT_LOCAL_SLM_MODEL_KEY,
    LOCAL_SLM_CACHE_NAMESPACE,
    LOCAL_SLM_RUNTIME_VERSION,
    LocalSlmExtractionCache,
    LocalSlmRuntimeError,
    build_local_slm_cache_identity,
    ensure_local_slm_provisioned,
    get_shared_local_slm_extraction_cache,
    shutdown_global_local_slm_runtimes,
)
from app.ai.slm_verified_normalizer import (
    SLM_VERIFIED_NORMALIZER_VERSION,
    normalize_for_slm_grounding,
)
from app.main import app, hybrid_route_mode
from app.persistence import db as db_module
from app.persistence.db import Base
from tests.route_client import route_client


@pytest.fixture
def isolated_compact_slm_db(tmp_path, monkeypatch):
    test_db = tmp_path / "slm_v6_route_test.db"
    test_engine = create_engine(f"sqlite:///{test_db}", connect_args={"check_same_thread": False})
    TestSession = sessionmaker(bind=test_engine, autoflush=False)
    Base.metadata.create_all(test_engine)
    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "SessionLocal", TestSession)
    monkeypatch.setattr(main_module, "SessionLocal", TestSession)
    import app.accounts.router as router_module

    monkeypatch.setattr(router_module, "SessionLocal", TestSession)
    yield TestSession
    test_engine.dispose()


@pytest.fixture(autouse=True)
def cleanup_slm_state():
    get_shared_local_slm_extraction_cache().clear()
    yield
    get_shared_local_slm_extraction_cache().clear()
    shutdown_global_local_slm_runtimes()


def test_verified_normalizer_provenance_typos_and_guards():
    # 1. Valid paraphrase canonicalizes with span-audited provenance
    raw = "Xét chóp S.ABCD nhận hình vuông cạnh a làm đáy ABCD. Cạnh SA vuông góc với đáy, góc tạo bởi SC và (ABCD) đo được 45 độ. Hãy tính thể tích khối chóp S.ABCD."
    vn = normalize_for_slm_grounding(raw)
    assert not vn.typo_detected
    assert vn.changed
    assert vn.normalizer_version == SLM_VERIFIED_NORMALIZER_VERSION
    assert "45°" in vn.canonical_text
    assert "góc giữa SC và (ABCD) bằng 45°" in vn.canonical_text
    prov = vn.to_provenance_dict()
    assert prov["applied_rule_ids"]
    assert all(s["validation_result"] == "VALIDATED_MEANING_PRESERVING" for s in prov["steps"])

    # 2. Ambiguous diacritic typos must fail-closed without rewriting or calling SLM
    for typo_txt in (
        "Cho hình chóp S.ABC có đáy ABC đều cạnh a, SA vuôg góc đáy, SA=a. Tính thể tích.",
        "Cho hình chop S.ABC có đáy ABC đều cạnh a, SA vuông góc đáy, SA=a. Tính thể tích.",
        "Cho lăng tru đứng ABC.A'B'C' có đáy ABC đều cạnh a, AA'=a. Tính thể tích.",
    ):
        vt = normalize_for_slm_grounding(typo_txt)
        assert vt.typo_detected is True
        assert vt.changed is False
        assert vt.canonical_text == vt.original_text
        res = run_local_slm_extraction(typo_txt, strategy="compact_clause", use_verified_normalizer=True, use_cache=False)
        assert not res.ok
        assert res.reason_code == "AMBIGUOUS_FACT"
        assert res.failure_taxonomy == "TYPO_REQUIRES_CONFIRMATION"
        assert res.inference is None

    # 3. Conditionals & universal lateral wording preserved safely
    cond_txt = "Cho hình chóp S.ABC có đáy ABC đều cạnh a. Nếu SA=2a thì nhận hình vuông BCDE làm đáy."
    vc = normalize_for_slm_grounding(cond_txt)
    assert "Nếu SA=2a thì nhận hình vuông BCDE làm đáy" in vc.canonical_text

    lat_txt = "Cho hình chóp tam giác đều S.ABC có cạnh đáy là a và tất cả các cạnh bên đều bằng a. Tính thể tích."
    vl = normalize_for_slm_grounding(lat_txt)
    assert "các cạnh bên bằng a" in vl.canonical_text


def test_compact_clause_context_grammar_and_lowerings():
    txt = (
        "Cho hình chóp P.UVW có đáy UVW vuông cân tại V, UV=a. "
        "PU vuông góc đáy, PU=2a. Tính thể tích khối chóp P.UVW."
    )
    ctx = build_compact_clause_context(txt)
    assert [e.label for e in ctx.entities if e.kind == "solid"] == ["P.UVW"]
    assert "UVW" in [e.label for e in ctx.entities if e.kind == "poly"]
    assert "UV" in [e.label for e in ctx.entities if e.kind == "seg"]

    grammar = build_compact_grammar_for_context(ctx)
    assert '"\\"pyr\\""' in grammar
    assert '"\\"cube\\""' not in grammar  # Pyramid P.UVW cannot generate cube stype
    assert 'solid0 ::= "[" ("0"' in grammar
    assert '"\\"P.UVW\\""' in grammar
    assert "relc2" not in grammar  # Pure question clause [2] cannot host premise relations

    # Composite lowering of right_iso_tri expands to right_angle + equal_length
    valid_json = {
        "s": [0, "pyr", "P.UVW", 0],
        "r": [
            {"c": 0, "p": "right_iso_tri", "a": "UVW", "pt": "V"},
            {"c": 0, "p": "len", "a": "UV", "q": "a"},
            {"c": 1, "p": "perp_lp", "a": "PU", "b": "UVW"},
            {"c": 1, "p": "len", "a": "PU", "q": "2a"},
        ],
        "g": [{"c": 2, "t": "vol", "tgt": "P.UVW"}],
        "u": [],
    }
    canon, diag = validate_and_lower_compact_clause(ctx=ctx, raw_slm_json=valid_json)
    assert canon is not None
    assert diag["grounding_status"] == "GROUNDED_AND_LOWERED"
    kinds = [p["kind"] for p in canon["premises"]]
    assert "right_angle" in kinds and "equal_length" in kinds

    # Regular pyramid "các cạnh bên bằng a" selects lateral sub-clause quote cleanly
    reg_txt = "Cho hình chóp tam giác đều S.ABC có cạnh đáy là a và các cạnh bên bằng a. Tính thể tích khối chóp S.ABC."
    reg_ctx = build_compact_clause_context(reg_txt)
    reg_canon, reg_diag = validate_and_lower_compact_clause(
        ctx=reg_ctx,
        raw_slm_json={
            "s": [0, "pyr", "S.ABC", 1],
            "r": [
                {"c": 0, "p": "reg_poly", "a": "ABC", "q": "a"},
                {"c": 0, "p": "len", "a": "SA", "q": "a"},
            ],
            "g": [{"c": 1, "t": "vol", "tgt": "S.ABC"}],
            "u": [],
        },
    )
    assert reg_canon is not None and reg_diag["grounding_status"] == "GROUNDED_AND_LOWERED"
    seg_prems = [p for p in reg_canon["premises"] if p["kind"] == "segment_length"]
    assert len(seg_prems) == 1 and "cạnh bên bằng a" in seg_prems[0]["quote"]

    # Sub-clause length conflict/proximity check rejects cross-segment quantity binding
    multi_len_ctx = build_compact_clause_context(
        "Cho hình chóp S.ABC có đáy ABC vuông tại B, AB=a, BC=2a, SA vuông góc (ABC), SA=3a. Tính thể tích S.ABC."
    )
    bad_canon, bad_diag = validate_and_lower_compact_clause(
        ctx=multi_len_ctx,
        raw_slm_json={
            "s": [0, "pyr", "S.ABC", 0],
            "r": [{"c": 0, "p": "len", "a": "AB", "q": "3a"}],
            "g": [{"c": 1, "t": "vol", "tgt": "S.ABC"}],
            "u": [],
        },
    )
    assert bad_canon is None
    assert bad_diag["reason_code"] == "UNGROUNDED_VALUE"


def test_nine_field_cache_identity_invalidation_and_lru():
    base_kwargs = {
        "exact_input_text": "Cho hình chóp S.ABC...",
        "model_key": DEFAULT_LOCAL_SLM_MODEL_KEY,
        "model_sha256": "abc123",
        "runtime_version": LOCAL_SLM_RUNTIME_VERSION,
        "strategy": "compact_clause",
        "schema_version": SLM_COMPACT_SCHEMA_VERSION,
        "schema_sha256": "def456",
        "grounding_policy_version": f"{SLM_GROUNDING_VALIDATOR_VERSION}|norm={SLM_VERIFIED_NORMALIZER_VERSION}",
        "parser_version": "local-geometry-parser/2",
        "capability_identity": compute_local_slm_capability_identity(),
        "namespace": LOCAL_SLM_CACHE_NAMESPACE,
    }
    base_key, meta = build_local_slm_cache_identity(**base_kwargs)
    assert len(base_key) == 64 and meta["namespace"] == LOCAL_SLM_CACHE_NAMESPACE

    mutations = [
        ("exact_input_text", "Cho hình chóp S.ABCD..."),
        ("model_key", "other-slm-0.5b"),
        ("model_sha256", "changed_sha"),
        ("runtime_version", "local-slm-runtime/99"),
        ("strategy", "minimal_ops"),
        ("schema_version", "slm-compact-clause/99"),
        ("schema_sha256", "changed_schema_sha"),
        ("grounding_policy_version", f"{SLM_GROUNDING_VALIDATOR_VERSION}|norm=none"),
        ("parser_version", "local-geometry-parser/99"),
        ("capability_identity", {**base_kwargs["capability_identity"], "registry_version": "changed"}),
    ]
    for field_name, alt_val in mutations:
        mut_key, _ = build_local_slm_cache_identity(**{**base_kwargs, field_name: alt_val})
        assert mut_key != base_key, f"Cache key did not invalidate on {field_name}"

    cache = LocalSlmExtractionCache(max_entries=2)
    cache.put("k1", "v1")
    cache.put("k2", "v2")
    assert cache.get("k1") == "v1"  # Refreshes k1
    cache.put("k3", "v3")
    assert cache.get("k2") is None and cache.get("k1") == "v1" and cache.get("k3") == "v3"


def test_compact_clause_escalation_policy():
    from types import SimpleNamespace

    assert DEFAULT_LOCAL_SLM_STRATEGY == "compact_clause"
    # 1. Full unambiguous problem solves locally without SLM
    full_text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, "
        "SA vuông góc với (ABC) và SA=2a. Tính thể tích khối chóp S.ABC."
    )
    det = AIR.route_text_input(full_text, allow_live_ai=False)
    assert det.status == "SERVED"
    assert not AIR._should_escalate_to_compact_slm(det, full_text)

    # 2. Out-of-scope non-geometry requests never escalate to local SLM
    oos_text = "Tính đạo hàm của hàm số y = x^3 - 3x + 2 trên tập số thực."
    det_oos = AIR.route_text_input(oos_text, allow_live_ai=False)
    assert det_oos.telemetry.chosen_route == "LOCAL_OUT_OF_SCOPE_GATE"
    assert not AIR._should_escalate_to_compact_slm(det_oos, oos_text)

    # 3. Contrastive "còn ... thì ..." under LOCAL_DETERMINISTIC_HYBRID CONDITIONAL_CLAUSE escalates;
    # genuine "nếu ... thì ..." does not.
    cond_stub = lambda txt: SimpleNamespace(
        status="REFUSED",
        telemetry=SimpleNamespace(chosen_route="LOCAL_DETERMINISTIC_HYBRID"),
        local_parse_result=None,
        response={"route_d": {"refusal": {"code": "CONDITIONAL_CLAUSE", "reason_code": "CONDITIONAL_CLAUSE"}}},
    )
    contrastive = (
        "Cho hình chóp S.ABC có đáy ABC đều cạnh a, còn SA thì vuông góc với đáy và SA=2a. "
        "Tính thể tích khối chóp S.ABC."
    )
    conditional = (
        "Cho hình chóp S.ABC có đáy ABC đều cạnh a. Nếu SA=2a thì tính thể tích khối chóp S.ABC."
    )
    assert AIR._should_escalate_to_compact_slm(cond_stub(contrastive), contrastive)
    assert not AIR._should_escalate_to_compact_slm(cond_stub(conditional), conditional)


def test_compact_clause_live_cpu_api_cache_hit_and_refusal(monkeypatch, isolated_compact_slm_db):
    try:
        ensure_local_slm_provisioned(model_key=DEFAULT_LOCAL_SLM_MODEL_KEY, allow_download=False)
    except LocalSlmRuntimeError:
        pytest.skip("Local SLM runtime/GGUF not provisioned in test environment")

    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-slm")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    assert hybrid_route_mode() == "local-slm"

    client = route_client(app)
    paraphrased = (
        "Khối chóp S.ABCD nhận ABCD làm hình vuông cạnh a. "
        "Cạnh SA vuông góc với đáy, góc tạo bởi SC và (ABCD) đo được 45 độ. "
        "Tính thể tích khối chóp S.ABCD."
    )
    # 1. Warm live compact_clause solve
    r1 = client.post("/api/analyze", json={"input": {"type": "text", "content": paraphrased}})
    assert r1.status_code == 200
    b1 = r1.json()
    assert b1["route_d"]["status"] == "SERVED"
    assert b1["route_d"]["answers"]["q1"] == "a³√2/3"
    assert b1["route_d"]["extraction_mode"] == "LOCAL_SLM_GROUNDED"
    assert b1["route_d"]["slm_grounding_envelope"]["strategy"] == "compact_clause"
    assert b1["route_d"]["slm_grounding_envelope"]["cache_hit"] is False
    assert b1["route_d"]["adaptive_telemetry"]["total_provider_calls"] == 0

    # 2. Second identical request hits singleton LocalSlmExtractionCache
    r2 = client.post("/api/analyze", json={"input": {"type": "text", "content": paraphrased}})
    assert r2.status_code == 200
    b2 = r2.json()
    assert b2["route_d"]["status"] == "SERVED"
    assert b2["route_d"]["answers"]["q1"] == "a³√2/3"

    # 3. Typo confirmation fails closed without invoking SLM or solving
    typo_q = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuôg góc với đáy và SA = 2a. Tính thể tích khối chóp S.ABCD."
    r_typo = client.post("/api/analyze", json={"input": {"type": "text", "content": typo_q}})
    assert r_typo.status_code == 200
    assert r_typo.json()["route_d"]["status"] != "SERVED"
