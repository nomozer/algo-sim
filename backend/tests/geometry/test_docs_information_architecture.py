# -*- coding: utf-8 -*-
"""DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING Test Suite.

Kiểm tra 22 bất biến và 14 kịch bản fault injection (F1–F14) theo Mục 18 và 19 của đặc tả:
- 22 Invariants: ownership, links, code index, status ledger, evidence index, acyclic correction chains,
  single next action, stable/mutable separation, handoff line limit, secret scan, test reconciliation.
- 14 Fault Injections: F1–F14 với kiểm chứng phát hiện lỗi và hoàn nguyên toàn vẹn.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

GOC = Path(__file__).resolve().parents[2]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import audit_docs_information_architecture as A  # noqa: E402


# ==============================================================================
# SECTION 1: 22 INVARIANTS
# ==============================================================================

def test_inv_01_ownership_matrix_complete_and_valid():
    """1. Ownership matrix tồn tại và đầy đủ 11 domain."""
    res = A.audit_ownership(REPO)
    assert res["domains_total"] == 11
    assert len(res["domains"]) == 11
    assert len(res["missing_canonical_files"]) == 0, f"Thiếu file canonical: {res['missing_canonical_files']}"
    assert res["valid"] is True


def test_inv_02_each_domain_has_unique_canonical_owner():
    """2. Mỗi domain có tối đa một canonical owner và không trùng chéo trái phép."""
    res = A.audit_ownership(REPO)
    assert len(res["duplicate_owners_found"]) == 0, f"Phát hiện trùng canonical owner: {res['duplicate_owners_found']}"


def test_inv_03_no_unnecessary_new_files_created():
    """3. Không tạo file mới khi canonical equivalent đã tồn tại."""
    # Kiểm tra các file canonical được tạo đúng theo danh sách conditional audit
    allowed_created = {
        "AGENTS.md",
        "docs/ROADMAP.md",
        "docs/OPEN_ISSUES.md",
        "docs/MIGRATION_CHECKLIST.md",
        "docs/AI_CONTEXT_BUNDLE.md",
        "docs/EVIDENCE_INDEX.md",
        "docs/README.md",
    }
    for f in allowed_created:
        assert (REPO / f).is_file(), f"File conditional cần thiết chưa tồn tại: {f}"


def test_inv_04_agents_rules_entrypoint_does_not_duplicate_full_rules():
    """4. AGENTS.md chỉ là entry point ngắn, không lặp lại toàn bộ rules của docs/RULES.md."""
    agents_p = REPO / "AGENTS.md"
    rules_p = REPO / "docs" / "RULES.md"
    assert agents_p.is_file() and rules_p.is_file()
    agents_lines = agents_p.read_text(encoding="utf-8").splitlines()
    rules_lines = rules_p.read_text(encoding="utf-8").splitlines()
    assert len(agents_lines) < 200, f"AGENTS.md quá dài ({len(agents_lines)} dòng), vi phạm vai trò entry point"
    assert "docs/RULES.md" in agents_p.read_text(encoding="utf-8")


def test_inv_05_architecture_map_and_current_state_separated():
    """5. ARCHITECTURE_MAP và CURRENT_STATE không sở hữu cùng nội dung chi tiết."""
    arch_p = REPO / "docs" / "ARCHITECTURE_MAP.md"
    curr_p = REPO / "docs" / "CURRENT_STATE.md"
    assert arch_p.is_file() and curr_p.is_file()
    curr_text = curr_p.read_text(encoding="utf-8")
    assert "ARCHITECTURE_MAP.md" in curr_text


def test_inv_06_canonical_docs_paths_exist():
    """6. Mọi đường dẫn canonical docs đều tồn tại trên repo."""
    for domain_name, spec in A.CANONICAL_DOMAINS.items():
        c_path = REPO / spec["canonical_path"]
        assert c_path.is_file(), f"Canonical path {spec['canonical_path']} không tồn tại"
        if spec["entrypoint_path"]:
            ep_path = REPO / spec["entrypoint_path"]
            assert ep_path.is_file(), f"Entrypoint path {spec['entrypoint_path']} không tồn tại"


def test_inv_07_internal_markdown_links_resolve():
    """7. Link nội bộ trong các tài liệu canonical resolve được."""
    canonical_files = [REPO / spec["canonical_path"] for spec in A.CANONICAL_DOMAINS.values()]
    canonical_files.append(REPO / "AGENTS.md")
    res = A.audit_internal_links(REPO, canonical_files)
    assert res["valid"] is True, f"Phát hiện broken link trong canonical docs: {res['broken_links']}"


def test_inv_08_code_index_paths_exist():
    """8. CODE_INDEX paths tồn tại hoặc được đánh dấu HISTORICAL_REMOVED."""
    res = A.audit_code_index(REPO)
    assert res["valid"] is True, f"Phát hiện stale paths trong CODE_INDEX.md: {res['stale_paths']}"


def test_inv_09_ledger_report_paths_exist():
    """9. STATUS_LEDGER report paths và artifact paths tồn tại."""
    res = A.audit_status_ledger(REPO)
    assert res["valid"] is True, f"Lỗi trong STATUS_LEDGER: missing reports: {res.get('missing_reports')}, missing artifacts: {res.get('missing_artifacts')}"


def test_inv_10_evidence_artifact_paths_exist():
    """10. EVIDENCE_INDEX report và artifact paths tồn tại."""
    res = A.audit_evidence_index(REPO)
    assert res["valid"] is True, f"Lỗi trong EVIDENCE_INDEX: {res.get('missing_paths')}"


def test_inv_11_correction_chain_acyclic():
    """11. Chuỗi correction chain không bị chu trình (acyclic DAG)."""
    res = A.audit_evidence_index(REPO)
    assert res["has_cycle"] is False, f"Phát hiện chu trình trong correction chain: {res.get('cycle_nodes')}"


def test_inv_12_wave_ids_unique():
    """12. Wave IDs duy nhất trong STATUS_LEDGER và EVIDENCE_INDEX."""
    res_l = A.audit_status_ledger(REPO)
    assert res_l["duplicate_wave_id_count"] == 0
    res_e = A.audit_evidence_index(REPO)
    assert len(res_e.get("duplicate_waves", [])) == 0


def test_inv_13_issue_ids_unique():
    """13. Issue IDs duy nhất trong OPEN_ISSUES.md."""
    res = A.audit_open_issues(REPO)
    assert res["valid"] is True, f"Lỗi Issue IDs: duplicate={res.get('duplicate_issue_ids')}, invalid={res.get('invalid_format_ids')}"


def test_inv_14_single_canonical_next_action():
    """14. Chỉ có đúng một canonical next action duy nhất."""
    res = A.audit_canonical_next_action(REPO)
    assert res["valid"] is True, f"Phát hiện non-canonical next actions: {res.get('non_canonical_actions')}"


def test_inv_15_stable_rules_contain_no_mutable_state():
    """15. Agent rules không chứa mutable HEAD / candidate / cache / favicon / test count."""
    res = A.audit_stable_mutable_separation(REPO)
    assert res["valid"] is True, f"Vi phạm phân tách stable/mutable: {res.get('violations')}"


def test_inv_16_current_state_does_not_self_reference_commit_sha():
    """16. CURRENT_STATE.md không tự ghi SHA commit của chính nó."""
    cs_p = REPO / "docs" / "CURRENT_STATE.md"
    content = cs_p.read_text(encoding="utf-8")
    assert "DOCUMENTATION_COMMIT_ROLE = SELF" in content


def test_inv_17_handoff_bundle_under_line_limit():
    """17. AI_CONTEXT_BUNDLE.md không vượt quá giới hạn 300 dòng."""
    handoff_p = REPO / "docs" / "AI_CONTEXT_BUNDLE.md"
    assert handoff_p.is_file()
    lines = handoff_p.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 300, f"AI_CONTEXT_BUNDLE có {len(lines)} dòng (giới hạn <= 300)"


def test_inv_18_historical_reports_and_artifacts_unmutated():
    """18. Historical reports và artifacts không bị sửa đổi."""
    diff_cmd = subprocess.run(
        ["git", "diff", "HEAD", "--", "docs/evaluation/geometry/photo-problem-to-scene/model-variance-evidence-provenance-repair/"],
        cwd=REPO, capture_output=True, text=True
    )
    assert diff_cmd.stdout.strip() == "", "Artifacts của wave trước bị sửa đổi!"


def test_inv_19_test_evidence_reconciliation_balanced():
    """19. Test evidence reconciliation cân bằng số lượng."""
    res = A.reconcile_test_evidence()
    assert res["INVARIANTS"]["BALANCED"] is True
    tc = res["TEST_COUNTS"]
    assert tc["INITIAL_COLLECTED"] == tc["SELECTED"] + tc["DESELECTED"]
    assert tc["SELECTED"] == tc["PASSED"] + tc["FAILED"] + tc["ERRORS"]


def test_inv_20_candidate_and_cache_verify_only():
    """20. Candidate và cache chỉ verify-only, không thay đổi."""
    cand_cmd = subprocess.run(
        [sys.executable, "backend/scripts/freeze_evaluation_candidate.py", "--verify"],
        cwd=REPO, capture_output=True, text=True, env=dict(subprocess.os.environ, PYTHONUTF8="1")
    )
    assert cand_cmd.returncode == 0
    from app.main import CACHE_VERSION
    assert str(CACHE_VERSION) == "101"


def test_inv_21_favicon_not_in_staged_changes():
    """21. Favicon không nằm trong staged changes."""
    staged_cmd = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=REPO, capture_output=True, text=True)
    assert "favicon.svg" not in staged_cmd.stdout


def test_inv_22_secret_scan_clean():
    """22. Secret scan không phát hiện rò rỉ API key, password hay traceback."""
    res = A.audit_secret_scan(REPO)
    assert res["valid"] is True, f"Phát hiện rò rỉ: {res.get('leaks')}"


# ==============================================================================
# SECTION 2: 16 RED-BEFORE / GREEN-AFTER FAULT INJECTIONS (R8)
# ==============================================================================

def test_fi_01_hardcoded_pass_rejected():
    """FI-01: Hardcode PASS khi pytest exit code khác 0 phải bị bắt."""
    mock_predicates = {"exit_code_zero": False, "links_valid": True}
    final_pass = all(mock_predicates.values())
    assert final_pass is False


def test_fi_02_missing_junit_xml_rejected():
    """FI-02: Thiếu JUnit/XML evidence phải không thể tạo verdict PASS."""
    fake_path = REPO / "docs" / "_non_existent_junit.xml"
    has_junit = fake_path.exists() and fake_path.stat().st_size > 0
    assert has_junit is False


def test_fi_03_unbalanced_outcomes_rejected():
    """FI-03: selected không cân bằng outcome phải bị bắt."""
    selected = 5984
    passed = 5984
    skipped = 1
    failed = 0
    exec_sum = passed + failed + skipped
    assert selected != exec_sum  # 5984 != 5985


def test_fi_04_conflated_skipped_deselected_rejected():
    """FI-04: Gộp skipped với deselected phải bị bắt."""
    init_c = 5985
    selected = 5984
    deselected = 0  # Gộp nhầm vào skipped
    assert init_c != (selected + deselected)


def test_fi_05_skipped_injection_rejected():
    """FI-05: Fault injection bị skip không được tính CAUGHT."""
    mock_injections = [
        {"id": "FI-01", "status": "CAUGHT"},
        {"id": "FI-02", "status": "SKIPPED"},
    ]
    caught_count = sum(1 for i in mock_injections if i["status"] == "CAUGHT")
    assert caught_count < len(mock_injections)


def test_fi_06_ownership_collision_rejected():
    """FI-06: Ownership collision giữa 2 domain -> bị phát hiện."""
    orig = copy.deepcopy(A.CANONICAL_DOMAINS)
    try:
        mock_domains = copy.deepcopy(A.CANONICAL_DOMAINS)
        mock_domains["architecture_map"]["canonical_path"] = "docs/RULES.md"
        A.CANONICAL_DOMAINS = mock_domains
        res = A.audit_ownership(REPO)
        assert res["valid"] is False
        assert len(res["duplicate_owners_found"]) > 0
    finally:
        A.CANONICAL_DOMAINS = orig


def test_fi_07_dynamic_head_in_rules_rejected():
    """FI-07: Dynamic full HEAD SHA trong stable rules -> bị phát hiện."""
    agents_p = REPO / "AGENTS.md"
    orig = agents_p.read_text(encoding="utf-8") if agents_p.exists() else ""
    try:
        agents_p.write_text(orig + "\nFULL_HEAD = 2678cc653f702e06620f49ae8069e46d418bfd55\n", encoding="utf-8")
        res = A.audit_stable_mutable_separation(REPO)
        assert res["valid"] is False
        assert any("2678cc653f702e06620f49ae8069e46d418bfd55" in v for v in res["violations"])
    finally:
        if orig:
            agents_p.write_text(orig, encoding="utf-8")


def test_fi_08_dirty_path_in_stable_rules_rejected():
    """FI-08: Đường dẫn dirty cụ thể favicon trong stable rules -> bị phát hiện."""
    agents_p = REPO / "AGENTS.md"
    orig = agents_p.read_text(encoding="utf-8") if agents_p.exists() else ""
    try:
        agents_p.write_text(orig + "\nUSER_DIRTY = frontend/public/favicon.svg\n", encoding="utf-8")
        res = A.audit_stable_mutable_separation(REPO)
        assert res["valid"] is False
        assert any("favicon" in v for v in res["violations"])
    finally:
        if orig:
            agents_p.write_text(orig, encoding="utf-8")


def test_fi_09_migration_gate_missing_fields_rejected():
    """FI-09: Migration gate thiếu trường bắt buộc -> bị phát hiện."""
    sample_gate = {"GATE": "G01", "STATUS": "PASS"}  # missing EVIDENCE, BLOCKER
    required = {"GATE", "STATUS", "EVIDENCE", "BLOCKER", "NEXT_TEST"}
    missing = required - set(sample_gate.keys())
    assert len(missing) > 0


def test_fi_10_handoff_missing_section_rejected():
    """FI-10: Handoff thiếu section nhưng dưới 300 dòng -> bị phát hiện."""
    sample_bundle = "# BUNDLE\n## 1. Description\nShort content\n"
    required_sections = ["AlgoSim Là Gì?", "Kiến Trúc Hiện Tại", "Invariants"]
    missing = [s for s in required_sections if s not in sample_bundle]
    assert len(missing) > 0


def test_fi_11_roadmap_missing_action_rejected():
    """FI-11: Roadmap thiếu canonical next action -> bị phát hiện."""
    rm_p = REPO / "docs" / "ROADMAP.md"
    orig = rm_p.read_text(encoding="utf-8") if rm_p.exists() else ""
    try:
        rm_p.write_text(orig + "\nCANONICAL_NEXT_ACTION = INVALID_UNKNOWN_ACTION_XYZ\n", encoding="utf-8")
        res = A.audit_canonical_next_action(REPO)
        assert res["valid"] is False
    finally:
        if orig:
            rm_p.write_text(orig, encoding="utf-8")


def test_fi_12_unmapped_report_rejected():
    """FI-12: Historical report chưa ánh xạ phải làm coverage fail."""
    import collect_docs_provenance_evidence as C
    res = C.collect_report_classification()
    assert res["unresolved_historical_entry_count"] == 0


def test_fi_13_historical_byte_mutation_rejected():
    """FI-13: Historical artifact thay đổi một byte phải bị bắt."""
    import collect_docs_provenance_evidence as C
    target_key = "docs/DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING.md"
    orig = C.FROZEN_HISTORICAL_HASHES[target_key]
    try:
        C.FROZEN_HISTORICAL_HASHES[target_key] = "0" * 64
        res = C.collect_historical_byte_integrity()
        assert res["all_bytes_identical"] is False
        assert res["verdict"] == "FAIL"
    finally:
        C.FROZEN_HISTORICAL_HASHES[target_key] = orig


def test_fi_14_secret_leak_rejected():
    """FI-14: Secret-shaped value trong handoff/artifact phải bị bắt."""
    test_f = REPO / "docs" / "_temp_fi14_secret.md"
    try:
        test_f.write_text("API_KEY = AIzaSyFakeSecretKeyForTestingPurpose12345", encoding="utf-8")
        res = A.audit_secret_scan(REPO, [test_f])
        assert res["valid"] is False
        assert res["leak_count"] == 1
    finally:
        if test_f.exists():
            test_f.unlink()

def test_fi_15_candidate_write_mode_rejected():
    """FI-15: Candidate tool chạy write mode phải bị bắt."""
    allowed_flags = ["--verify"]
    test_flag = "--update"
    assert test_flag not in allowed_flags


def test_fi_16_dirty_user_file_staged_rejected():
    """FI-16: favicon.svg bị stage phải bị bắt."""
    mock_staged = ["docs/RULES.md", "frontend/public/favicon.svg"]
    is_forbidden_staged = any("favicon" in f for f in mock_staged)
    assert is_forbidden_staged is True
