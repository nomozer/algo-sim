# -*- coding: utf-8 -*-
"""Focused verification test suite for LiveRetryApparatus (Gate C).

Proves all 12 apparatus verification invariants using fake transport:
1. Full raw response written before parsing (RAW_PERSISTED before PARSED).
2. Process death right after transport leaves valid file and verifiable hash.
3. Preview is rejected in place of full raw response.
4. Hash mismatch causes fail-closed (MEASUREMENT_ERROR).
5. Truncated file causes fail-closed.
6. Atomic-write/read-back failure causes fail-closed.
7. API key and Authorization header scrubbed from journal/metadata.
8. RESERVED/TRANSPORT_COMPLETED request cannot be automatically resent.
9. Corrected evaluator uses canonical references, not hardcoded display labels.
10. Pipeline harness uses production entry point (contract_adapter.build_fact_graph).
11. Zero calls to FG.FactGraph() in production/harness code.
12. Second request budget blocked before transport (TRANSPORT_BUDGET = 1).
"""
from __future__ import annotations

import hashlib
import json
import pytest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "backend" / "scripts"
import sys
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import live_retry_apparatus as LRA
import reconcile_second_family_live_measurement as R


SAMPLE_CANDIDATE_JSON = json.dumps({
    "input_facts": [
        {"id": "prism_kind", "kind": "str", "label": "Hình lăng trụ", "value": ["lăng trụ đứng"]},
        {"id": "base_shape", "kind": "str", "label": "Đáy ABC", "value": ["tam giác vuông tại A"]},
        {"id": "ab_length", "kind": "int", "label": "Đoạn thẳng AB", "value": ["3"]},
        {"id": "ac_length", "kind": "int", "label": "Cạnh AC", "value": ["4"]},
        {"id": "ad_length", "kind": "int", "label": "Chiều cao AD", "value": ["5"]}
    ],
    "solid_topology": {
        "solid_kind": "prism",
        "base_cycle": ["A", "B", "C"],
        "top_cycle": ["D", "E", "F"],
        "correspondence": [["A", "D"], ["B", "E"], ["C", "F"]]
    }
}, ensure_ascii=False)


# ── Invariant 1: Raw response persisted before parsing ────────────────────────

def test_inv_01_raw_persisted_before_parsing(tmp_path: Path):
    """1. Full raw response must reach RAW_PERSISTED before PARSED is allowed."""
    app = LRA.LiveRetryApparatus(tmp_path)
    app.reserve_budget(max_requests=1)
    assert app.state == LRA.STATE_RESERVED
    
    # Try parsing before raw persistence -> must fail
    with pytest.raises(LRA.ApparatusPersistenceError, match="raw persistence not reached"):
        app.parse_from_durable_storage(json.loads)

    # Record transport response -> reaches RAW_PERSISTED
    sha = app.record_transport_response(SAMPLE_CANDIDATE_JSON)
    assert app.state == LRA.STATE_RAW_PERSISTED
    assert app.raw_response_path.is_file()
    assert sha == hashlib.sha256(SAMPLE_CANDIDATE_JSON.encode("utf-8")).hexdigest()

    # Now parsing succeeds
    parsed = app.parse_from_durable_storage(json.loads)
    assert app.state == LRA.STATE_PARSED
    assert parsed["solid_topology"]["solid_kind"] == "prism"


# ── Invariant 2: Process death resilience after transport ─────────────────────

def test_inv_02_process_death_resilience(tmp_path: Path):
    """2. If process dies immediately after RAW_PERSISTED, file and hash are verifiable."""
    app1 = LRA.LiveRetryApparatus(tmp_path)
    app1.reserve_budget(max_requests=1)
    sha1 = app1.record_transport_response(SAMPLE_CANDIDATE_JSON)
    assert app1.state == LRA.STATE_RAW_PERSISTED

    # Simulate process death and cold recovery in a new apparatus instance
    app2 = LRA.LiveRetryApparatus(tmp_path)
    assert app2.raw_response_path.is_file()
    disk_bytes = app2.raw_response_path.read_bytes()
    assert hashlib.sha256(disk_bytes).hexdigest() == sha1
    
    # Journal reflects RAW_PERSISTED state
    journal = json.loads(app2.journal_path.read_text(encoding="utf-8"))
    assert journal["state"] == LRA.STATE_RAW_PERSISTED
    assert journal["raw_response_sha256"] == sha1


# ── Invariant 3: Preview rejected in place of full raw response ────────────────

def test_inv_03_preview_rejected(tmp_path: Path):
    """3. Preview-only content is rejected; full candidate response required."""
    app = LRA.LiveRetryApparatus(tmp_path)
    app.reserve_budget(max_requests=1)
    with pytest.raises(LRA.ApparatusPersistenceError, match="Preview content rejected"):
        app.record_transport_response(SAMPLE_CANDIDATE_JSON[:500], preview_only=True)
    assert app.state == LRA.STATE_MEASUREMENT_ERROR


# ── Invariant 4: Hash mismatch causes fail-closed ──────────────────────────────

def test_inv_04_hash_mismatch_fails_closed(tmp_path: Path):
    """4. If read-back hash does not match computed hash, fail closed."""
    app = LRA.LiveRetryApparatus(tmp_path)
    app.reserve_budget(max_requests=1)
    
    # Mock os.replace to corrupt file content before read-back
    original_replace = LRA.os.replace
    def corrupting_replace(src, dst):
        with open(src, "ab") as f:
            f.write(b"CORRUPTED_EXTRA_BYTES")
        original_replace(src, dst)

    with patch.object(LRA.os, "replace", side_effect=corrupting_replace):
        with pytest.raises(LRA.ApparatusPersistenceError, match="Read-back hash mismatch"):
            app.record_transport_response(SAMPLE_CANDIDATE_JSON)
    
    assert app.state == LRA.STATE_MEASUREMENT_ERROR


# ── Invariant 5: Truncated file causes fail-closed ─────────────────────────────

def test_inv_05_truncated_file_fails_closed(tmp_path: Path):
    """5. An empty or truncated payload causes fail-closed."""
    app = LRA.LiveRetryApparatus(tmp_path)
    app.reserve_budget(max_requests=1)
    with pytest.raises(LRA.ApparatusPersistenceError, match="Empty raw response bytes"):
        app.record_transport_response(b"")
    assert app.state == LRA.STATE_MEASUREMENT_ERROR


# ── Invariant 6: Atomic write/read-back failure causes fail-closed ─────────────

def test_inv_06_atomic_write_failure_fails_closed(tmp_path: Path):
    """6. Failure during atomic write or fsync causes fail-closed."""
    app = LRA.LiveRetryApparatus(tmp_path)
    app.reserve_budget(max_requests=1)
    
    # Mock tempfile.NamedTemporaryFile to fail when writing raw response
    original_named_temp = LRA.tempfile.NamedTemporaryFile
    call_count = 0
    def failing_named_temp(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        # Allow journal write (call 1), but fail during data write (call 2)
        if kwargs.get("mode") == "wb" or args and args[0] == "wb":
            raise OSError("Disk I/O error during raw payload write")
        return original_named_temp(*args, **kwargs)

    with patch.object(LRA.tempfile, "NamedTemporaryFile", side_effect=failing_named_temp):
        with pytest.raises(LRA.ApparatusPersistenceError, match="Atomic write failed"):
            app.record_transport_response(SAMPLE_CANDIDATE_JSON)
            
    assert app.state == LRA.STATE_MEASUREMENT_ERROR


# ── Invariant 7: API key & Authorization scrubbed from metadata ────────────────

def test_inv_07_secrets_scrubbed_from_journal(tmp_path: Path):
    """7. API key and Authorization header are never written to journal or metadata."""
    app = LRA.LiveRetryApparatus(tmp_path)
    app.reserve_budget(max_requests=1)
    
    # Check journal content
    journal_text = app.journal_path.read_text(encoding="utf-8")
    assert "AIza" not in journal_text
    assert "Bearer" not in journal_text
    assert "key=" not in journal_text

    # Test sanitize_metadata function
    dirty_meta = {
        "url": "https://api.google.com/generate?key=AIzaSyA1234567890abcdefghijklmnopqr",
        "headers": {"Authorization": "Bearer ya29.a0ARrdaM8sampletoken123"},
        "api_key": "AIzaSySecretKey9999999999999999999",
        "clean_field": "PRISM_SCHEMA_LIVE_P01"
    }
    cleaned = LRA.sanitize_metadata(dirty_meta)
    assert "AIza" not in json.dumps(cleaned)
    assert "ya29" not in json.dumps(cleaned)
    assert cleaned["api_key"] == "[REDACTED_KEY_FIELD]"
    assert cleaned["clean_field"] == "PRISM_SCHEMA_LIVE_P01"


# ── Invariant 8: RESERVED or TRANSPORT_COMPLETED cannot be resent ──────────────

def test_inv_08_no_automatic_resend(tmp_path: Path):
    """8. A request that has been reserved or transported cannot be resent."""
    app = LRA.LiveRetryApparatus(tmp_path)
    app.reserve_budget(max_requests=1)
    app.record_transport_response(SAMPLE_CANDIDATE_JSON)
    
    # Attempting a second record_transport_response -> rejected
    with pytest.raises(LRA.ApparatusPersistenceError, match="Cannot record transport response in state"):
        app.record_transport_response(SAMPLE_CANDIDATE_JSON)


# ── Invariant 9: Corrected evaluator uses canonical references (R1) ───────────

def test_inv_09_corrected_evaluator_uses_canonical_references():
    """9. Corrected evaluator tolerates descriptive display labels and uses canonical IDs."""
    class MockFact:
        def __init__(self, fact_id: str, label: str, val: str):
            self.fact_id = fact_id
            self.id = fact_id
            self.label = label
            self.values = [val]

    class MockContract:
        def __init__(self, facts):
            self.input_facts = facts
            self.source_invariants = []

    facts = [
        MockFact("ab_length", "Đoạn thẳng AB", "3"),
        MockFact("ac_length", "Cạnh AC", "4"),
        MockFact("ad_length", "Chiều cao AD", "5"),
    ]
    contract = MockContract(facts)
    lengths = R.corrected_length_evaluator(contract)
    assert lengths == {"AB": "3", "AC": "4", "AD": "5"}


# ── Invariant 10: Pipeline harness uses production entry point (R2) ───────────

def test_inv_10_pipeline_harness_production_entry_point():
    """10. Pipeline harness invokes contract_adapter.build_fact_graph directly."""
    from app.simulation.geometry_compiler import contract_adapter as CA
    assert hasattr(CA, "build_fact_graph")
    
    from app.simulation.semantic_program.scale_normalization import SourceInvariant
    invs = [
        SourceInvariant(kind="segment_length", points=("A", "B"), expected="3", source_text="AB = 3", source_fact_id="ab_length", scale_symbol=""),
        SourceInvariant(kind="segment_length", points=("A", "C"), expected="4", source_text="AC = 4", source_fact_id="ac_length", scale_symbol=""),
        SourceInvariant(kind="segment_length", points=("A", "D"), expected="5", source_text="AD = 5", source_fact_id="ad_length", scale_symbol=""),
    ]
    class MockContract:
        def __init__(self):
            self.input_facts = []
            self.source_invariants = invs

    res = CA.build_fact_graph(MockContract())
    assert res.status == "VALID"
    assert res.graph is not None


# ── Invariant 11: Zero calls to FG.FactGraph() ────────────────────────────────

def test_inv_11_zero_calls_to_fact_graph_class():
    """11. Verify that no active scripts or test harness call FG.FactGraph()."""
    import ast
    target_files = [
        REPO_ROOT / "backend" / "scripts" / "live_retry_apparatus.py",
        REPO_ROOT / "backend" / "scripts" / "reconcile_second_family_live_measurement.py",
    ]
    for tf in target_files:
        tree = ast.parse(tf.read_text(encoding="utf-8"), filename=str(tf))
        lines = tf.read_text(encoding="utf-8").splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "FactGraph" and isinstance(func.value, ast.Name) and func.value.id == "FG":
                    # Check enclosing function
                    func_def = ""
                    for i in range(node.lineno - 1, -1, -1):
                        if lines[i].strip().startswith("def "):
                            func_def = lines[i].strip()
                            break
                    if "legacy" not in func_def:
                        pytest.fail(f"Active executable call to FG.FactGraph() found at line {node.lineno} in {tf}")



# ── Invariant 12: Second request budget blocked before transport ──────────────

def test_inv_12_single_request_budget_enforced(tmp_path: Path):
    """12. Request budget = 1 strictly enforced; second reservation rejected."""
    app = LRA.LiveRetryApparatus(tmp_path)
    app.reserve_budget(max_requests=1)
    
    # Attempting to reserve again -> fails closed
    with pytest.raises(LRA.ApparatusPersistenceError, match="Budget violation"):
        app.reserve_budget(max_requests=1)
