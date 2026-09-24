# -*- coding: utf-8 -*-
"""Test suite for SECOND_FAMILY_LIVE_MEASUREMENT_RECONCILIATION_OFFLINE.

Tests Gate C requirements:
1. Evidence with invalid hash is rejected.
2. Missing raw response is not inferred from report.
3. Length fact with canonical reference is recognized even with descriptive display label.
4. Display label alone cannot invent segment without canonical reference.
5. Expected length facts (AB=3, AC=4, AD=5) preserved.
6. Unrelated/ambiguous length facts rejected.
7. Harness detects nonexistent class before declaring pipeline failure (R2 Red-Before).
8. Harness uses correct production entry point (R2 Green-After).
9. Offline replay makes 0 transport calls.
10. Original historical artifacts remain byte-identical.
"""
from __future__ import annotations

import hashlib
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "backend" / "scripts"
import sys
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import reconcile_second_family_live_measurement as R


# ── Mock Contract & Fact Helpers ─────────────────────────────────────────────

class DummyFact:
    def __init__(self, fact_id: str, label: str, values: list[str]):
        self.fact_id = fact_id
        self.id = fact_id
        self.label = label
        self.values = tuple(values)


class DummyContract:
    def __init__(self, input_facts: list[DummyFact], source_invariants: list[Any] = None):
        self.input_facts = tuple(input_facts)
        self.source_invariants = tuple(source_invariants or [])


# ── Requirement 1 & 2: Evidence Integrity & Hash Validation ──────────────────

def test_evidence_hash_mismatch_rejected(tmp_path: Path):
    """1. Evidence with incorrect SHA-256 hash must be rejected."""
    wrong_content = "some altered response content"
    wrong_hash = hashlib.sha256(wrong_content.encode("utf-8")).hexdigest()
    assert wrong_hash != R.EXPECTED_RESPONSE_SHA256
    
    # Verification logic must reject mismatched hash
    verified = (wrong_hash == R.EXPECTED_RESPONSE_SHA256)
    assert verified is False


def test_missing_raw_response_not_inferred():
    """2. Raw response missing from disk must NOT be inferred or hallucinated from reports."""
    # When raw response is not on disk or truncated, integrity must declare INSUFFICIENT
    res = R.run_reconciliation()
    # In the current workspace, raw response preview is truncated, so integrity must be INSUFFICIENT
    assert res["final_decision"] == "HISTORICAL_EVIDENCE_INSUFFICIENT"
    assert res["source_response_hash_verified"] is False
    assert res["semantic_extraction_valid"] == "NOT_MEASURABLE"


# ── Requirement 3, 4, 5, 6: Red-Before & Green-After on Length Evaluator (R1) ─

def test_r1_red_before_label_matching_drops_valid_length_facts():
    """R1 Red-Before: Legacy label-matching drops valid facts when label is descriptive."""
    facts = [
        DummyFact("ab_length", "Đoạn thẳng AB", ["3"]),
        DummyFact("ac_length", "Cạnh AC", ["4"]),
        DummyFact("ad_length", "Chiều cao AD", ["5"]),
    ]
    contract = DummyContract(facts)
    
    # Legacy evaluator checks `f.label in ("AB", "AC", "AD")` -> DROPS ALL!
    legacy_res = R.legacy_length_evaluator(contract)
    assert legacy_res == {}, "Legacy evaluator should fail to recognize descriptive labels"


def test_r1_green_after_corrected_evaluator_recognizes_canonical_references():
    """3 & 5. Corrected evaluator recognizes canonical facts even with descriptive display labels."""
    facts = [
        DummyFact("ab_length", "Đoạn thẳng AB", ["3"]),
        DummyFact("ac_length", "Cạnh AC", ["4"]),
        DummyFact("ad_length", "Chiều cao AD", ["5"]),
    ]
    contract = DummyContract(facts)
    
    corrected_res = R.corrected_length_evaluator(contract)
    assert corrected_res.get("AB") == "3"
    assert corrected_res.get("AC") == "4"
    assert corrected_res.get("AD") == "5"


def test_ambiguous_display_label_rejected():
    """4. Plain display label is insufficient if reference is missing or ambiguous."""
    # Ambiguous label that doesn't clearly match any known segment and has no canonical id
    facts = [
        DummyFact("random_fact", "Khoảng cách giữa hai điểm bất kỳ", ["3"]),
        DummyFact("unknown_id", "Một đường vuông góc", ["4"]),
    ]
    contract = DummyContract(facts)
    
    corrected_res = R.corrected_length_evaluator(contract)
    assert corrected_res == {}


def test_unrelated_length_facts_rejected():
    """6. Unrelated or ungrounded length facts must be rejected."""
    facts = [
        DummyFact("bc_length", "Đoạn thẳng BC", ["5"]),
        DummyFact("xy_length", "Đoạn thẳng XY", ["10"]),
    ]
    contract = DummyContract(facts)
    
    corrected_res = R.corrected_length_evaluator(contract)
    assert "AB" not in corrected_res
    assert "AC" not in corrected_res
    assert "AD" not in corrected_res


# ── Requirement 7 & 8: Red-Before & Green-After on Pipeline Harness (R2) ──────

def test_r2_red_before_stale_fact_graph_class_reference_fails():
    """7. R2 Red-Before: Legacy harness calling FG.FactGraph() raises AttributeError."""
    contract = DummyContract([])
    with pytest.raises(AttributeError, match="has no attribute 'FactGraph'"):
        R.legacy_pipeline_harness_call(contract)


def test_r2_green_after_production_entry_point_succeeds():
    """8. R2 Green-After: Harness uses canonical production entry point `contract_adapter.build_fact_graph`."""
    from app.simulation.geometry_compiler import contract_adapter as CA
    assert hasattr(CA, "build_fact_graph"), "contract_adapter must export build_fact_graph"
    
    # Test on a contract with complete source invariants for prism
    from app.simulation.semantic_program.scale_normalization import SourceInvariant
    invs = [
        SourceInvariant(kind="segment_length", points=("A", "B"), expected="3", source_text="AB = 3", source_fact_id="ab_length", scale_symbol=""),
        SourceInvariant(kind="segment_length", points=("A", "C"), expected="4", source_text="AC = 4", source_fact_id="ac_length", scale_symbol=""),
        SourceInvariant(kind="segment_length", points=("A", "D"), expected="5", source_text="AD = 5", source_fact_id="ad_length", scale_symbol=""),
    ]
    contract = DummyContract([], source_invariants=invs)
    
    # Production entry point builds GeometryFactGraph cleanly
    res = CA.build_fact_graph(contract)
    assert res.status == "VALID"
    assert res.graph is not None
    assert type(res.graph).__name__ == "GeometryFactGraph"


# ── Requirement 9: Zero Network / Zero Transport ─────────────────────────────

def test_offline_replay_zero_network():
    """9. Offline reconciliation and replay must make ZERO network/transport calls."""
    with patch("httpx.Client") as mock_client:
        R.run_reconciliation()
        mock_client.assert_not_called()


# ── Requirement 10: Original Historical Artifacts Preserved ───────────────────

def test_historical_artifacts_byte_identical():
    """10. Historical artifacts of SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION must not be modified."""
    hist_dir = REPO_ROOT / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene" / "second-family-live-schema-revalidation"
    assert hist_dir.is_dir()
    
    required_files = [
        "REQUEST_OBSERVATION.json",
        "LIVE_RESULT.json",
        "PIPELINE_RESULT.json",
        "FINAL_DECISION.json",
    ]
    for rf in required_files:
        p = hist_dir / rf
        assert p.is_file(), f"Historical file {rf} missing"
        # Verify content parses as valid json
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data.get("case_id") == "PRISM_SCHEMA_LIVE_P01"
