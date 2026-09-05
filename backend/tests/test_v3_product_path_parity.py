# -*- coding: utf-8 -*-
"""V3_PRODUCT_PATH_PARITY — runner V3 chấm ở SAI TẦNG. **0 lượt gọi model.**

    `docs/V3_PRODUCT_PATH_PARITY_CORRECTION.md`, 2026-09-05.

Runner V3 đọc đại lượng từ `outcome.envelope["scene3d"]` sau khi gọi
`verify_and_compile`. Nhưng `route` **cố ý** không dựng `scene3d` — hướng phụ
thuộc một chiều, và `test_scene3d.py` cấm mọi module dưới `app/simulation`
import nó. Người dựng cảnh là `pipeline._dung_scene3d`, chạy SAU route.

Hệ quả: phép chiếu ấy trả **rỗng cho mọi ca**, nên `dap_so_khop` không bao giờ
True được — kể cả với một chương trình đúng hoàn toàn. Đúng một ca của V3 chạy
tới được tầng ấy (`c7a`), và nó bị chấm sai vì lý do này.

Thẩm quyền đúng cho ĐÁP SỐ là `acceptance_verdict.trich_ket_qua` →
`outcome.final_memory`. Nó đã có sẵn trong scorer; runner chỉ không gọi.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC / "scripts"))

REPO = GOC.parent
OUT = REPO / "docs" / "evaluation" / "geometry" / "curved-acceptance-v3"
CV3 = REPO / "docs" / "evaluation" / "geometry" / "curved-v3"
DINH_CHINH = CV3 / "V3_PRODUCT_PATH_PARITY_CORRECTION.json"

#: Băm artifact NGUỒN của lượt V3. Chúng là bằng chứng lịch sử và **không được
#: đổi** — bản đính chính là một lớp MỚI đặt cạnh, không phải một bản ghi đè.
BAM_NGUON = {
    "attribution.json":
        "280a3fe1290305b5c21deea4c035bf0a423ce280cc975a9c34839df411d85610",
    "curved_acceptance.json":
        "70d47a9542561209ce5f4f0d50184e638866eca27f49f8594eb6b6e4e05a49b5",
    "manifest.json":
        "b2a454f0b285c5f1061798a52dc367efcba5ebb3d0a4f30da6eb0e38776c146a",
    "stage_8a_one_shot.json":
        "f3439fb6db1d568b3ac2723ad52b6a58358bc9786012dffdff4a0fc4122f53bb",
}
CANDIDATE_V3 = ("a696200e8f8c668c82a1675eab09b4e1845e3c499edaf90c95790f108"
                "fe244c2")


def _bam(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def dc():
    assert DINH_CHINH.exists(), "chưa sinh artifact đính chính"
    return json.loads(DINH_CHINH.read_text(encoding="utf-8"))


# ══ ① ARTIFACT NGUỒN GIỮ NGUYÊN ═══════════════════════════════════════════
@pytest.mark.parametrize("ten,bam", sorted(BAM_NGUON.items()))
def test_01_artifact_V3_goc_KHONG_doi_mot_byte(ten, bam):
    assert _bam(OUT / ten) == bam, (
        f"{ten} đã đổi — artifact V3 là bằng chứng lịch sử của một candidate "
        f"không còn tồn tại; đính chính phải là một LỚP MỚI đặt cạnh")


def test_02_dinh_chinh_ghi_dung_bam_nguon(dc):
    for ten, bam in BAM_NGUON.items():
        assert dc["source_artifact_hashes"][ten] == bam, ten


# ══ ② REPLAY DÙNG ĐÚNG CANDIDATE CŨ ═══════════════════════════════════════
def test_03_replay_chay_tren_candidate_V3_CU(dc):
    assert dc["replay_measured_system_hash"] == CANDIDATE_V3
    assert dc["old_candidate_hash"] == CANDIDATE_V3
    assert dc["replay_dung_candidate_cu"] is True
    assert dc["replay_measured_system_files"] == 89


def test_04_candidate_HIEN_TAI_khong_duoc_dung_lam_nen_replay(dc):
    """Tiêm ⑨ — candidate hiện tại KHÁC candidate V3; lẫn lộn là vô hiệu."""
    import freeze_evaluation_candidate as F

    hien_tai, _n = F.measured_system_hash()
    assert hien_tai != CANDIDATE_V3, (
        "candidate hiện tại trùng candidate V3 — test này mất ý nghĩa")
    assert dc["replay_measured_system_hash"] != hien_tai


# ══ ③ 0 LƯỢT GỌI ══════════════════════════════════════════════════════════
def test_05_khong_luot_goi_model_nao(dc):
    assert dc["application_llm_calls"] == 0
    assert dc["physical_api_attempts"] == 0
    assert dc["provider_guard_trips"] == 0, (
        "guard đã bị chạm — nghĩa là có đường gọi model trong replay")


# ══ ④ HAI ĐƯỜNG, VÀ CHÚNG KHÁC NHAU ═══════════════════════════════════════
def test_06_route_KHONG_dung_scene3d_con_pipeline_thi_CO():
    """Gốc rễ, đo bằng AST chứ không bằng lời."""
    import ast

    r = ast.parse((GOC / "app" / "simulation" / "semantic_program"
                   / "route.py").read_text(encoding="utf-8"))
    ten_route = {n.id for n in ast.walk(r) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(r) if isinstance(n, ast.Attribute)}
    assert "build_scene3d" not in ten_route, (
        "`route` KHÔNG được dựng scene3d — hướng phụ thuộc một chiều")

    p = ast.parse((GOC / "app" / "ai" / "pipeline.py").read_text(
        encoding="utf-8"))
    ten_pipe = {n.id for n in ast.walk(p) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(p) if isinstance(n, ast.Attribute)}
    assert "_dung_scene3d" in ten_pipe and "build_scene3d" in ten_pipe


def test_07_legacy_projection_tai_hien_quantity_list_RONG(dc):
    """Tiêm ⑦ — bỏ bước scene composition ⇒ đúng con số gốc quay lại."""
    c7 = [h for h in dc["per_case"] if h["case_id"] == "c7a"][0]
    assert c7["legacy_dai_luong_from_route_envelope"] == []
    assert c7["original_scene3d"] is False
    assert c7["original_exact_match"] is False


def test_08_product_path_chay_them_scene_composition(dc):
    c7 = [h for h in dc["per_case"] if h["case_id"] == "c7a"][0]
    assert len(c7["replay_scene_quantities"]) == 3
    assert c7["replay_scene3d"] is True


# ══ ⑤ THẨM QUYỀN ĐÁP SỐ ═══════════════════════════════════════════════════
def test_09_dap_so_doc_tu_final_memory_KHONG_tu_scene3d(dc):
    """Tiêm ⑧ — Scene3D là bằng chứng HIỂN THỊ, không phải thẩm quyền toán."""
    for h in dc["per_case"]:
        if h.get("exact_result_authority") is not None:
            assert h["exact_result_authority"] == "outcome.final_memory", h


def test_10_c7a_dung_TRON_ba_dap_so(dc):
    c7 = [h for h in dc["per_case"] if h["case_id"] == "c7a"][0]
    assert set(c7["expected"]) == {"13", "100π", "65π"}
    assert set(c7["expected"]) <= set(c7["replay_dai_luong_final_memory"])
    assert c7["replay_exact_match"] is True


def test_11_c7a_KHONG_servable_vi_verification_gap(dc):
    """Đúng hoàn toàn về toán mà VẪN không servable — và đó là lỗi HỆ.

    `distance` trên `curved_solid` không chứng thực được, nên route trả
    `postcondition_violated` / `verification_gap`. Đây là cùng hình dạng với
    `duong_4_he_hut_verification` của certifier.
    """
    c7 = [h for h in dc["per_case"] if h["case_id"] == "c7a"][0]
    assert c7["replay_executable"] is True
    assert c7["replay_servable"] is False
    assert c7["replay_failure_category"] == "verification_gap"
    assert c7["replay_verdict_pinned_scorer"] == "SYSTEM_VERIFICATION_FAILURE"


def test_12_hai_bo_phan_lop_LECH_va_dieu_do_duoc_GHI_RA(dc):
    """Bộ 7 lớp của runner mù với `servable`; ghi cả hai thay vì chọn im lặng."""
    x = dc["phan_lop_hai_tham_quyen_LECH_NHAU"]
    assert x["c7a_runner"] == "CORRECT_EXECUTABLE_IR"
    assert x["c7a_pinned_scorer"] == "SYSTEM_VERIFICATION_FAILURE"
    assert "4f7cae90" in x["tham_quyen_chon"]


# ══ ⑥ PHẠM VI ĐÍNH CHÍNH ══════════════════════════════════════════════════
def test_13_chi_MOT_ca_doi(dc):
    assert dc["cases_changed"] == ["c7a"]
    assert sum(1 for h in dc["per_case"] if h["verdict_changed"]) == 1


def test_14_moi_ca_khac_tai_hien_Y_NGUYEN(dc):
    for h in dc["per_case"]:
        if h["case_id"] == "c7a":
            continue
        assert h["verdict_changed"] is False, h["case_id"]
        if h.get("replay_executable") is not None:
            assert h["replay_executable"] == h["original_executable"], h["case_id"]


def test_15_verdict_tong_KHONG_doi(dc):
    tv = dc["threshold_verdict"]
    assert tv["GENERAL_CURVED_SYNTHESIS_ACCEPTANCE"].startswith("FAIL")
    for k in ("BALL", "CYLINDER", "CONE"):
        assert tv[f"PRODUCT_PROMOTION_ELIGIBLE_{k}"] == "NO"


def test_16_pham_vi_hieu_luc_khai_dung_hai_cot_hong(dc):
    v = dc["validity_scope"]
    assert v["V3_GENERATION_EVIDENCE_VALID"] is True
    assert v["V3_GROUNDING_EVIDENCE_VALID"] is True
    assert v["V3_EXACT_SCORING_VALID"] is False
    assert v["V3_SCENE3D_SCORING_VALID"] is False


def test_17_artifact_tu_khai_la_LOP_DINH_CHINH(dc):
    """Tên và nội dung phải nói rõ: không phải một lượt V3 mới."""
    assert dc["loai_artifact"] == "CORRECTION_LAYER"
    assert "KHÔNG phải một lượt V3 mới" in dc["khai"]
    assert dc["measurement_class"].startswith("INTERNAL_ONE_SHOT_ACCEPTANCE")
    assert "OPERATOR_WAIVED" in dc["evaluator"]


def test_18_con_dau_V3_khong_doi(dc):
    dau = json.loads((CV3 / "V3_SEAL.json").read_text(encoding="utf-8"))
    assert dc["case_set_hash"] == dau["case_set_hash"]
    assert dc["pool_hash"] == dau["pool_hash"]
    assert dc["seed"] == dau["seed"] == 5324284654432805119
