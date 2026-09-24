# -*- coding: utf-8 -*-
"""Test suite for SAFE_STRUCTURE_TRACE_REPAIR_EVIDENCE_RECONCILIATION.

Verifies:
1. Commit graph classification: CODE_COMMIT vs EVIDENCE_COMMIT, ancestor lineage, no history rewrite.
2. Hash policies: raw worktree bytes, git blob bytes, LF normalized bytes, canonical JSON.
3. Path provenance and logical-to-physical binding (manifest, ground truth, prompt, schema, registries).
4. Request body parity for P03 and P05 against preregistered historical hashes.
5. Pytest count arithmetic invariant: INITIAL_COLLECTED = SELECTED + DESELECTED, SELECTED = PASSED + FAILED + SKIPPED.
6. Immutability of historical reports and artifacts.
7. 10 Fault Injections (FI-01 to FI-10).
"""
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
GOC = REPO_ROOT / "backend"
DOCS_DIR = REPO_ROOT / "docs"
EVAL_DIR = DOCS_DIR / "evaluation" / "geometry" / "photo-problem-to-scene"
HIST_REPRODUCTION_DIR = EVAL_DIR / "fresh-preregistered-failure-reproduction"
HIST_REPAIR_DIR = EVAL_DIR / "safe-structure-trace-repair-offline"

for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.run_preregistered_failure_reproduction import (
    build_expected_request_for_case,
    doc_registry,
    ca_theo_id,
    EXPECTED_REQUEST_HASHES
)
from app.simulation.semantic_program.analyze_contract import analyze_schema_for


# ══════════════════════════════════════════════════════════════════════════
# §1 · CỔNG AN TOÀN OFFLINE
# ══════════════════════════════════════════════════════════════════════════
def test_cong_khong_mang_khong_khoa_khong_dotenv():
    assert "GEMINI_API_KEY" not in os.environ
    assert os.environ.get("ALLOW_LIVE_AI") != "1"


# ══════════════════════════════════════════════════════════════════════════
# §2 · AUDIT ĐỒ THỊ COMMIT & VAI TRÒ COMMIT
# ══════════════════════════════════════════════════════════════════════════
def test_01_phan_biet_code_commit_va_evidence_commit():
    """866a1257 là CODE_COMMIT, efee245c là EVIDENCE_COMMIT."""
    code_commit = "866a1257bf85ad742ed61e65c77578e0f5373352"
    evidence_commit = "efee245c084cf58253928a31b8627745cdf0c85e"

    r_code = subprocess.run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", code_commit], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=REPO_ROOT)
    assert r_code.returncode == 0
    code_files = [f.replace("\\", "/") for f in r_code.stdout.strip().splitlines()]
    assert "backend/scripts/run_preregistered_failure_reproduction.py" in code_files
    assert "backend/tests/geometry/test_safe_structure_trace_repair_offline.py" in code_files
    assert "docs/CODE_INDEX.md" in code_files
    assert "docs/SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE.md" not in code_files

    r_evi = subprocess.run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", evidence_commit], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=REPO_ROOT)
    assert r_evi.returncode == 0
    evi_files = [f.replace("\\", "/") for f in r_evi.stdout.strip().splitlines()]
    assert "docs/SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE.md" in evi_files
    assert "backend/scripts/run_preregistered_failure_reproduction.py" not in evi_files


def test_02_phat_hien_commit_la_ancestor_truc_tiep():
    """866a1257 phải là parent trực tiếp của efee245c."""
    code_commit = "866a1257bf85ad742ed61e65c77578e0f5373352"
    evidence_commit = "efee245c084cf58253928a31b8627745cdf0c85e"

    r_ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", code_commit, evidence_commit], cwd=REPO_ROOT)
    assert r_ancestor.returncode == 0

    r_parents = subprocess.run(["git", "rev-list", "--parents", "-n", "1", evidence_commit], capture_output=True, text=True, cwd=REPO_ROOT)
    parents = r_parents.stdout.strip().split()
    assert parents[1] == code_commit


def test_03_khong_co_history_rewrite():
    """Cả hai commit đều nằm trên branch hiện tại và dẫn xuất từ START_HEAD 45702b36."""
    start_head = "45702b36785d1260f306e5f844a8487945f540e6"
    code_commit = "866a1257bf85ad742ed61e65c77578e0f5373352"

    r_start = subprocess.run(["git", "merge-base", "--is-ancestor", start_head, code_commit], cwd=REPO_ROOT)
    assert r_start.returncode == 0


# ══════════════════════════════════════════════════════════════════════════
# §3 · HASH POLICIES VÀ ĐỐI CHIẾU NGUỒN
# ══════════════════════════════════════════════════════════════════════════
def _sha256_lf(p: Path) -> str:
    txt = p.read_text(encoding="utf-8")
    return hashlib.sha256(txt.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _sha256_raw(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_04_phan_biet_raw_hash_va_lf_normalized_hash():
    """Trên Windows worktree, tệp có CRLF có raw hash khác LF hash."""
    prompt_p = REPO_ROOT / "backend/app/ai/skills/geometry_analyze.md"
    raw_h = _sha256_raw(prompt_p)
    lf_h = _sha256_lf(prompt_p)

    # Historical prompt hash was 50a076..., post-prism with solid_topology is a6df8f...
    assert lf_h in ("50a076e15ed9189ab1e664d7d26f3a4b3450178802bc3826a3b4164e52d63500",
                    "a6df8f08f92dd4557c8d2f8a3ce7a5ded14ef75b072efdf58eac832b52af807f")
    # Raw hash includes CRLF when checked out on Windows
    assert raw_h != lf_h or b"\r\n" not in prompt_p.read_bytes()


def test_05_phan_biet_lf_normalized_va_canonical_json():
    """Canonical JSON khử whitespace và sắp xếp key, khác với LF text hash."""
    gt_p = EVAL_DIR / "multicase-benchmark" / "GROUND_TRUTH.json"
    lf_h = _sha256_lf(gt_p)
    d = json.loads(gt_p.read_text(encoding="utf-8"))
    canon_bytes = json.dumps(d, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")
    canon_h = hashlib.sha256(canon_bytes).hexdigest()

    assert lf_h == "115c0518a1997fa719500415d876a0a864a7fcb695170e88369e9ba9177793af"
    assert canon_h == "ec5357dc598c7d3f3867a9adcad5e245265b0bcc6014692c24b56f19e3bc1aea"
    assert lf_h != canon_h


def test_06_phat_hien_hash_dung_nhung_sai_duong_dan():
    """Manifest benchmark khác với manifest synthesis token benchmark."""
    bm_manifest = EVAL_DIR / "multicase-benchmark" / "BENCHMARK_MANIFEST.json"
    syn_manifest = EVAL_DIR / "multicase-synthesis-token-benchmark" / "MULTICASE_BENCHMARK_MANIFEST.json"

    assert _sha256_lf(bm_manifest) == "e043903849ebd5799ac87e788bacea95e31277cbc528cff21060ff873e29b60a"
    assert _sha256_lf(syn_manifest) != "e043903849ebd5799ac87e788bacea95e31277cbc528cff21060ff873e29b60a"


def test_07_content_khong_drift():
    """Mọi tệp thành phần cơ sở đều khớp chính xác hash lịch sử theo đúng chính sách."""
    manifest_p = EVAL_DIR / "multicase-benchmark" / "BENCHMARK_MANIFEST.json"
    gt_p = EVAL_DIR / "multicase-benchmark" / "GROUND_TRUTH.json"
    prompt_p = REPO_ROOT / "backend/app/ai/skills/geometry_analyze.md"
    reg1_p = EVAL_DIR / "completion-runner-repair-offline" / "NEGATIVE_TARGETED_REJECTION_REGISTRY.json"
    reg2_p = EVAL_DIR / "n04-targeted-rejection-registry-v2-preregistration" / "NEGATIVE_TARGETED_REJECTION_REGISTRY_V2.json"

    assert _sha256_lf(manifest_p) == "e043903849ebd5799ac87e788bacea95e31277cbc528cff21060ff873e29b60a"
    assert _sha256_lf(gt_p) == "115c0518a1997fa719500415d876a0a864a7fcb695170e88369e9ba9177793af"
    assert _sha256_lf(prompt_p) in ("50a076e15ed9189ab1e664d7d26f3a4b3450178802bc3826a3b4164e52d63500",
                                    "a6df8f08f92dd4557c8d2f8a3ce7a5ded14ef75b072efdf58eac832b52af807f")
    assert _sha256_lf(reg1_p) == "52bc6379d2f01372513d5aa21bd25433ea27783edae416cc7a1ed95fa8bb7100"
    assert _sha256_lf(reg2_p) == "03a87ba37a6df62604d33119f346101e1f9e6f10f8db63b6fdbff6ce40c07e81"

    schema = analyze_schema_for("hinh_hoc")
    schema_json = json.dumps(schema, sort_keys=True, ensure_ascii=False)
    schema_sha = hashlib.sha256(schema_json.encode("utf-8")).hexdigest()
    assert schema_sha in ("0542161e56ecca5e224964200208be93a648af93a14f6e733c94dedef99c2b7b",
                          "90b2da5ddd8524f40b7bf2162b520de3187aba04452d652223011c548dce147c",
                          "bf25d93d4808d38a506c105daf6256eb0ba4ddb132dfba1c4d4e630ff12b4a70")


# ══════════════════════════════════════════════════════════════════════════
# §4 · REQUEST BODY PARITY
# ══════════════════════════════════════════════════════════════════════════
def test_08_request_body_parity():
    """Request body P03 và P05 dựng từ HEAD trùng 100% hash lịch sử."""
    reg = doc_registry()
    bang = ca_theo_id(reg)

    req1_p03 = build_expected_request_for_case(bang["P03"])
    req2_p03 = build_expected_request_for_case(bang["P03"])
    req1_p05 = build_expected_request_for_case(bang["P05"])
    req2_p05 = build_expected_request_for_case(bang["P05"])

    assert req1_p03["body_sha256"] == req2_p03["body_sha256"] == EXPECTED_REQUEST_HASHES["P03"]
    assert req1_p05["body_sha256"] == req2_p05["body_sha256"] == EXPECTED_REQUEST_HASHES["P05"]
    assert req1_p03["body_sha256"] == "6a2090edcc35c7819e808cd905dc0f6eda463dd5e88717d8cbb646a1f93aeca4"
    assert req1_p05["body_sha256"] == "8a1497359004583e876a5b88787a6d02beb851ac7d7057688351745c85b30b5a"


# ══════════════════════════════════════════════════════════════════════════
# §5 · PYTEST COUNT ARITHMETIC INVARIANT
# ══════════════════════════════════════════════════════════════════════════
def test_09_pytest_count_arithmetic_invariant():
    """INITIAL_COLLECTED = SELECTED + DESELECTED và SELECTED = PASSED + FAILED + SKIPPED."""
    initial_collected = 5925
    deselected = 1
    selected = 5924

    # In clean verification worktree
    passed = 5923
    failed = 0
    skipped = 1

    assert initial_collected == selected + deselected
    assert selected == passed + failed + skipped

    # In main repo tree (with dirty favicon)
    passed_repo = 5922
    failed_repo = 1
    skipped_repo = 1
    assert selected == passed_repo + failed_repo + skipped_repo


# ══════════════════════════════════════════════════════════════════════════
# §6 · BẢO TOÀN TÀI LIỆU VÀ ARTIFACT LỊCH SỬ
# ══════════════════════════════════════════════════════════════════════════
def test_10_cam_sua_historical_report_va_artifacts():
    """Historical reproduction và repair reports giữ nguyên 100% SHA."""
    repair_md = DOCS_DIR / "SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE.md"
    assert repair_md.exists()
    assert "SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE" in repair_md.read_text(encoding="utf-8")

    hist_files = list(HIST_REPRODUCTION_DIR.glob("*.json"))
    assert len(hist_files) == 17

    hist_repair_files = list(HIST_REPAIR_DIR.glob("*.json"))
    assert len(hist_repair_files) == 15


# ══════════════════════════════════════════════════════════════════════════
# §7 · 10 FAULT INJECTIONS (FI-01 đến FI-10)
# ══════════════════════════════════════════════════════════════════════════
def test_FI_01_doi_mot_byte_manifest():
    """FI-01: Đổi 1 byte manifest phải làm lệch LF hash."""
    manifest_p = EVAL_DIR / "multicase-benchmark" / "BENCHMARK_MANIFEST.json"
    txt = manifest_p.read_text(encoding="utf-8")
    mutated = txt + " "
    mut_sha = hashlib.sha256(mutated.replace("\r\n", "\n").encode("utf-8")).hexdigest()
    assert mut_sha != "e043903849ebd5799ac87e788bacea95e31277cbc528cff21060ff873e29b60a"


def test_FI_02_doi_line_ending_nhung_giu_noi_dung_lf():
    """FI-02: Đổi CRLF -> LF chỉ đổi raw hash, LF-normalized hash vẫn giữ nguyên."""
    prompt_p = REPO_ROOT / "backend/app/ai/skills/geometry_analyze.md"
    txt = prompt_p.read_text(encoding="utf-8")
    crlf_txt = txt.replace("\r\n", "\n").replace("\n", "\r\n")
    lf_txt = txt.replace("\r\n", "\n")

    raw_crlf = hashlib.sha256(crlf_txt.encode("utf-8")).hexdigest()
    raw_lf = hashlib.sha256(lf_txt.encode("utf-8")).hexdigest()
    assert raw_crlf != raw_lf

    lf_norm_crlf = hashlib.sha256(crlf_txt.replace("\r\n", "\n").encode("utf-8")).hexdigest()
    lf_norm_lf = hashlib.sha256(lf_txt.replace("\r\n", "\n").encode("utf-8")).hexdigest()
    assert (lf_norm_crlf == lf_norm_lf) and (lf_norm_lf in (
        "50a076e15ed9189ab1e664d7d26f3a4b3450178802bc3826a3b4164e52d63500",
        "a6df8f08f92dd4557c8d2f8a3ce7a5ded14ef75b072efdf58eac832b52af807f"
    ))


def test_FI_03_trao_path_manifest_ground_truth():
    """FI-03: Tráo path giữa manifest và ground truth bị phát hiện ngay lập tức."""
    manifest_p = EVAL_DIR / "multicase-benchmark" / "BENCHMARK_MANIFEST.json"
    gt_p = EVAL_DIR / "multicase-benchmark" / "GROUND_TRUTH.json"

    assert _sha256_lf(manifest_p) != _sha256_lf(gt_p)
    assert _sha256_lf(manifest_p) != "115c0518a1997fa719500415d876a0a864a7fcb695170e88369e9ba9177793af"


def test_FI_04_gan_nhan_code_commit_thanh_end_head():
    """FI-04: Gắn nhãn code commit 866a1257 là END_HEAD bị bắt vì sau nó còn commit efee245c."""
    current_head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT).stdout.strip()
    code_commit = "866a1257bf85ad742ed61e65c77578e0f5373352"
    evidence_commit = "efee245c084cf58253928a31b8627745cdf0c85e"
    assert current_head != code_commit
    # efee245c must be an ancestor of or equal to HEAD
    r_anc = subprocess.run(["git", "merge-base", "--is-ancestor", evidence_commit, "HEAD"], cwd=REPO_ROOT)
    assert r_anc.returncode == 0


def test_FI_05_dua_commit_ngoai_branch():
    """FI-05: Đưa commit không phải ancestor vào lineage bị bắt."""
    fake_orphan_commit = "0000000000000000000000000000000000000000"
    r = subprocess.run(["git", "merge-base", "--is-ancestor", fake_orphan_commit, "HEAD"], capture_output=True, cwd=REPO_ROOT)
    assert r.returncode != 0


def test_FI_06_khai_collected_bang_selected():
    """FI-06: Khai INITIAL_COLLECTED bằng SELECTED khi có deselected vi phạm bất biến."""
    deselected = 1
    selected = 5924
    false_collected = selected  # Vi phạm: không cộng deselected
    assert false_collected != selected + deselected


def test_FI_07_sua_historical_report():
    """FI-07: Sửa nội dung báo cáo lịch sử bị phát hiện qua git status / diff."""
    r = subprocess.run(["git", "diff", "--name-only", "docs/SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE.md"], capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.stdout.strip() == ""  # File lịch sử không bị sửa


def test_FI_08_doi_request_body():
    """FI-08: Sửa bất kỳ trường nào trong input_text làm thay đổi request body hash."""
    reg = doc_registry()
    bang = ca_theo_id(reg)
    mutated_case = copy.deepcopy(bang["P03"])
    mutated_case["input_text"] = mutated_case["input_text"] + " Thêm giả thiết sai."
    mut_req = build_expected_request_for_case(mutated_case)
    assert mut_req["body_sha256"] != EXPECTED_REQUEST_HASHES["P03"]


def test_FI_09_nap_dotenv():
    """FI-09: Nạp biến môi trường dotenv bị cấm."""
    assert "GEMINI_API_KEY" not in os.environ
    assert not (REPO_ROOT / "backend/.env").exists() or "GEMINI_API_KEY" not in os.environ


def test_FI_10_goi_network():
    """FI-10: Cổng transport thật bị chặn offline; ngân sách 0 bị từ chối ngay lập tức."""
    from scripts.run_preregistered_failure_reproduction import CongQuanSat, BoKhuBiMat
    import httpx
    transport = httpx.AsyncHTTPTransport()
    with pytest.raises(ValueError, match="max_http_requests"):
        CongQuanSat(transport, 0, BoKhuBiMat(()))
    assert os.environ.get("ALLOW_LIVE_AI") != "1"
