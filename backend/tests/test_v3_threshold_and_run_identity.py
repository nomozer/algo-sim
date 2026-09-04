# -*- coding: utf-8 -*-
"""NGƯỠNG + DANH TÍNH LƯỢT ĐO, khoá TRƯỚC kết quả. **0 lượt gọi model.**

    `V3_THRESHOLD_AND_RUN_IDENTITY_POLICY`, 2026-09-04.

Ngưỡng phải khoá trước khi biết kết quả, nếu không nó chỉ mô tả lại kết quả.
Khoá được nghĩa là **băm được**, và cổng phải ĐỎ khi ai đó đổi ngưỡng, đổi bộ
chấm hay đổi rubric sau khi manifest đã ghi.

Toàn bộ fixture là tổng hợp. V3 pool **chưa rút, chưa đọc nội dung**.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import measurement_policy as MP  # noqa: E402
from acceptance_integrity import (  # noqa: E402
    ARTIFACT_SCHEMA_VERSION,
    IntegrityError,
    RunManifest,
    mo_run,
)

GOC = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def nguong():
    return MP.nap_nguong()[0]


@pytest.fixture(scope="module")
def rubric():
    return MP.nap_rubric()[0]


# ══ A · CHÍNH SÁCH TỒN TẠI VÀ ĐỦ TRƯỜNG ═══════════════════════════════════
def test_A1_hai_chinh_sach_ton_tai_va_bam_duoc():
    for duong in (MP.CHINH_SACH_NGUONG, MP.RUBRIC_QUY_TRACH_NHIEM):
        d, h = MP.doc_chinh_sach(duong)
        assert d and len(h) == 64


def test_A2_chinh_sach_nam_NGOAI_measured_system():
    import freeze_evaluation_candidate as F

    fs = {f.resolve() for f in F._measured_system_files()}
    for duong in (MP.CHINH_SACH_NGUONG, MP.RUBRIC_QUY_TRACH_NHIEM,
                  GOC / "scripts" / "measurement_policy.py"):
        assert duong.resolve() not in fs, f"{duong.name} lọt vào candidate"


def test_A3_du_truong_bat_buoc_va_tro_dung_he_dang_do(nguong):
    import json as J

    import freeze_evaluation_candidate as F
    import seal_curved_v3 as S

    he, _ = F.measured_system_hash()
    bai = J.loads(S.POOL.read_text(encoding="utf-8"))["bai"]
    assert MP.kiem_chinh_sach(nguong, candidate_hash=he,
                              pool_hash=S._bam(bai)) == []


def test_A4_khoa_TRUOC_ket_qua(nguong, rubric):
    assert nguong["created_before_live_run"] is True
    assert rubric["created_before_live_run"] is True


def test_A5_bam_CHINH_TAC_bat_bien_voi_thut_le_va_thu_tu_khoa(nguong):
    """Reformat file không được đổi băm; đổi một CON SỐ thì phải đổi."""
    dao = dict(reversed(list(nguong.items())))
    assert MP.bam_chinh_tac(dao) == MP.bam_chinh_tac(nguong)
    doi = json.loads(json.dumps(nguong))
    doi["family_thresholds"]["eventual_servable_rate"] = 0.9
    assert MP.bam_chinh_tac(doi) != MP.bam_chinh_tac(nguong)


# ══ B · NGƯỠNG ĐÚNG GIÁ TRỊ ĐÃ KHOÁ ═══════════════════════════════════════
def test_B1_run_validity(nguong):
    rv = nguong["run_validity"]
    assert rv["selected_cells_required"] == 13
    assert rv["selected_cases_required"] == 13
    assert rv["one_case_per_cell"] is True
    for k in ("artifact_completeness_rate", "raw_candidate_retention_rate",
              "attempt_accounting_rate"):
        assert rv[k] == 1.0
    for k in ("identity_drift_allowed", "missing_manifest_fields_allowed",
              "unclassified_failures_allowed", "r0_laundering_allowed"):
        assert rv[k] == 0
    ht = rv["infrastructure"]
    assert ht["provider_error_counts_as_model_error"] is False
    assert ht["runner_error_counts_as_model_error"] is False
    assert ht["incomplete_run_verdict"] == "INCONCLUSIVE_INFRASTRUCTURE"
    assert ht["incomplete_run_may_produce_product_verdict"] is False
    assert ht["case_set_and_seed_immutable_after_draw"] is True


def test_B2_family_thresholds(nguong):
    ft = nguong["family_thresholds"]
    assert sorted(ft["applies_to"]) == ["ball", "cone", "cylinder"]
    assert ft["minimum_selected_positive_cases"] == 3
    for k in ("eventual_servable_rate", "exact_answer_match_rate",
              "scene3d_generated_rate", "postconditions_pass_rate"):
        assert ft[k] == 1.0
    for k in ("system_runtime_error_allowed", "system_checker_error_allowed",
              "system_expressiveness_gap_allowed",
              "attribution_unresolved_allowed", "r0_laundering_allowed"):
        assert ft[k] == 0
    assert ft["insufficient_sample_verdict"] == "INSUFFICIENT_SAMPLE"
    assert ft["never_lower_denominator"] is True


def test_B3_general_acceptance(nguong):
    g = nguong["general_curved_acceptance"]
    assert g["required_family_passes"] == "3/3"
    assert g["positive_cases_expected"] == 9
    for k in ("positive_eventual_servable", "positive_exact_answer_match",
              "positive_scene3d_generated"):
        assert g[k] == "9/9"
    for k in ("system_errors_allowed", "system_expressiveness_gaps_allowed",
              "attribution_unresolved_allowed", "r0_laundering_allowed"):
        assert g[k] == 0


def test_B4_negative_thresholds(nguong):
    n = nguong["negative_thresholds"]
    assert n["negative_cases_expected"] == 4
    for k in ("correct_fail_closed", "honest_unsupported_refusal",
              "target_boundary_demonstrated"):
        assert n[k] == "4/4"
    assert n["unrelated_fail_closed_allowed"] == 0
    assert n["curved_geometry_laundering_allowed"] == 0


def test_B5_feature_thresholds(nguong):
    f = nguong["feature_thresholds"]
    assert sorted(f["applies_to"]) == ["area", "center_radius", "lateral_area"]
    assert f["minimum_selected_cases"] == 1
    for k in ("request_contract_preservation_rate", "valid_program_rate",
              "eventual_servable_rate", "exact_answer_match_rate"):
        assert f[k] == 1.0
    assert f["no_case_drawn_verdict"] == "NOT_MEASURED"


def test_B6_thiet_ke_mau_KHOP_con_dau_that(nguong):
    """Ngưỡng `3 ca/family` chỉ đúng nếu thiết kế mẫu đúng — đo, đừng tin."""
    import json as J
    from collections import Counter

    import seal_curved_v3 as S

    bai = J.loads(S.POOL.read_text(encoding="utf-8"))["bai"]
    o_hinh, o_dem, o_loai = {}, Counter(), {}
    for b in bai:
        o_dem[b["o"]] += 1
        o_hinh.setdefault(b["o"], set()).add(b["hinh"])
        o_loai[b["o"]] = b["loai"]
    sd = nguong["sample_design"]
    assert len(o_dem) == sd["total_cells"] == 13
    assert set(o_dem.values()) == {sd["cases_per_cell"]} == {2}
    duong = [o for o in o_dem if o_loai[o] == "duong"]
    assert len(duong) == sd["positive_cells"] == 9
    assert all(len(o_hinh[o]) == 1 for o in duong) is \
        sd["positive_cells_are_family_homogeneous"]
    c = Counter(next(iter(o_hinh[o])) for o in duong)
    assert dict(c) == sd["positive_cells_per_family"] == \
        {"ball": 3, "cylinder": 3, "cone": 3}


def test_B7_moi_attempt_nam_trong_mau_so(nguong):
    ea = nguong["error_accounting"]
    assert ea["every_attempt_in_denominator"] is True
    assert ea["raw_candidate_retained_for_every_attempt"] is True
    assert set(ea["attempts_counted"]) >= {
        "schema", "grounding", "static", "coverage", "runtime", "checker"}


def test_B8_lop_trong_error_accounting_deu_CO_THAT():
    from acceptance_verdict import LOP_PHAN_QUYET

    ea = MP.nap_nguong()[0]["error_accounting"]
    for nhom in ("model_error_classes", "system_error_classes",
                 "unresolved_classes"):
        for lop in ea[nhom]:
            assert lop in LOP_PHAN_QUYET, f"{lop} không có trong scorer"


# ══ C · RUBRIC ════════════════════════════════════════════════════════════
def test_C1_ba_nhanh_YES_NO_UNKNOWN(rubric):
    assert rubric["valid_path_no"]["verdict"] == "SYSTEM_EXPRESSIVENESS_GAP"
    assert rubric["valid_path_yes"]["verdict_family"] == "MODEL_*_FAILURE"
    assert rubric["valid_path_unknown"]["verdict"] == "ATTRIBUTION_UNRESOLVED"


def test_C2_NO_doi_du_SAU_dieu_kien(rubric):
    assert len(rubric["valid_path_no"]["conditions"]) == 6


def test_C3_dau_hieu_KHONG_du_de_ket_luan(rubric):
    xau = " ".join(rubric["valid_path_no"]["insufficient_signals"])
    assert "AMBIGUOUS_FIRST_BINDING" in xau and "radius" in xau


def test_C4_UNRESOLVED_khong_tinh_ve_ben_nao(rubric):
    u = rubric["valid_path_unknown"]
    assert u["counts_as_model_error"] is False
    assert u["counts_as_proven_system_gap"] is False
    assert u["family_verdict"] == "INCONCLUSIVE_ATTRIBUTION"
    assert u["blocks_product_promotion"] is True
    assert u["invalidates_run"] is False


def test_C5_grounding_va_schema_TRUOC_quy_tac_nang_luc(rubric):
    thu_tu = rubric["precedence"]["order"]

    def vi(ten):                     # mục có thể mang chú thích phía sau
        return next(i for i, x in enumerate(thu_tu) if x.startswith(ten))

    assert vi("MODEL_GROUNDING_FAILURE") < vi("SYSTEM_EXPRESSIVENESS_GAP")
    assert vi("MODEL_SCHEMA_FAILURE") < vi("SYSTEM_EXPRESSIVENESS_GAP")
    assert vi("SYSTEM_EXPRESSIVENESS_GAP") < vi("MODEL_STATIC_FAILURE")


def test_C6_thu_tuc_adjudication_khoa_truoc(rubric):
    pd = rubric["post_draw_adjudication"]
    assert len(pd["steps"]) == 8
    assert pd["case_id_decides_verdict"] is False
    assert set(pd["required_evidence_fields"]) >= {
        "case_id", "source_type", "target_type", "can_bien_doi",
        "valid_path_proof", "authority_hashes", "verdict", "reason"}


def test_C7_rubric_khop_hanh_vi_THUC_cua_scorer():
    """Rubric không được là một tờ giấy rời khỏi mã."""
    from acceptance_verdict import YeuCauNangLuc, duong_hop_le_ton_tai
    from app.simulation.semantic_program.ir_static_check import _TOAN_HANG_LENH

    kieu = frozenset(next(k for n, k, _l in
                          _TOAN_HANG_LENH["construct_curved_solid"]
                          if n == "radius"))
    yc = lambda bd: YeuCauNangLuc(  # noqa: E731
        o_dich="radius", kieu_o_dich=kieu, kieu_nguon=frozenset({"float"}),
        can_bien_doi=bd)
    assert duong_hop_le_ton_tai(yc(True)) == "NO"
    assert duong_hop_le_ton_tai(yc(False)) == "YES"
    assert duong_hop_le_ton_tai(None) == "UNKNOWN"


# ══ D · RUN MANIFEST ══════════════════════════════════════════════════════
def _mo(tmp, **kw):
    return mo_run(
        tmp / "run", run_id="test-run", muc_dich="test",
        runner=str(GOC / "scripts" / "run_curved_acceptance.py"),
        ca=[{"id": "x", "loai": "duong", "de": "d", "mong": ["1"]}],
        model=kw.pop("model", {"provider": "gia"}),
        chinh_sach_sua="test", ngan_sach_goi=0, bo_qua_dirty=True, **kw)


def test_D1_manifest_GHIM_scorer_threshold_rubric(tmp_path):
    mf = _mo(tmp_path)
    bam_scorer = hashlib.sha256(
        (GOC / "scripts" / "acceptance_verdict.py").read_bytes()).hexdigest()
    assert mf.scorer_hash == bam_scorer
    assert mf.threshold_policy_hash == MP.nap_nguong()[1]
    assert mf.attribution_rubric_hash == MP.nap_rubric()[1]
    assert mf.scorer_path == "acceptance_verdict.py"
    assert mf.threshold_policy_path == MP.CHINH_SACH_NGUONG.name
    # Ghim luôn CÁI TÍNH RA ba băm kia — nếu không, đổi phép băm trước lượt đo
    # thì manifest và certifier nhất trí với nhau và cùng sai.
    assert mf.policy_loader_hash == hashlib.sha256(
        Path(MP.__file__).read_bytes()).hexdigest()


def test_D2_schema_version_bump(tmp_path):
    assert ARTIFACT_SCHEMA_VERSION == "1.1"
    assert _mo(tmp_path).artifact_schema_version == "1.1"


def test_D3_round_trip_giu_du_truong(tmp_path):
    j = _mo(tmp_path).to_json()
    from acceptance_integrity import TRUONG_MANIFEST_1_1

    for t in (*TRUONG_MANIFEST_1_1, "artifact_schema_version"):
        assert t in j, t
    lai = json.loads(json.dumps(j, ensure_ascii=False))
    assert lai == j


def test_D4_manifest_ghi_ra_dia_va_doc_lai_duoc(tmp_path):
    _mo(tmp_path)
    d = json.loads((tmp_path / "run" / "manifest.json").read_text(
        encoding="utf-8"))
    assert d["scorer_hash"] and d["threshold_policy_hash"]
    assert d["attribution_rubric_hash"]


def test_D5_TU_CHOI_resume_vao_thu_muc_cu(tmp_path):
    _mo(tmp_path)
    with pytest.raises(IntegrityError, match="ĐÃ TỒN TẠI"):
        _mo(tmp_path)


def test_D6_artifact_lich_su_1_0_van_doc_duoc():
    """Version dispatch rõ ràng: manifest 1.0 thiếu ba trường mới, và thiếu là
    HỢP LỆ với nó — `None` chứ không phải lỗi đọc."""
    mf = RunManifest(
        run_id="cu", muc_dich="x", runner="r", runner_hash="h", model={},
        chinh_sach_sua="", ngan_sach_goi=0, seal={}, moi_truong={}, git={},
        artifact_schema_version="1.0")
    j = mf.to_json()
    assert j["artifact_schema_version"] == "1.0"
    assert j["scorer_hash"] is None


# ══ E · DANH TÍNH MODEL ═══════════════════════════════════════════════════
def test_E1_cau_hinh_repo_HIEN_TAI_la_alias_troi(nguong):
    """Đo cấu hình thật, không giả định."""
    from app.ai.gemini import MODEL

    v, thieu = MP.kiem_danh_tinh_model(
        {"provider": "gemini", "model_name": MODEL,
         "model_version_or_snapshot": None, "temperature": 0.2,
         "top_p": None, "max_output_tokens": None, "repair_limit": 3}, nguong)
    assert v == "MODEL_IDENTITY_UNPINNED"
    assert any("ALIAS TRÔI" in x for x in thieu)
    assert any("top_p" in x for x in thieu)
    assert any("max_output_tokens" in x for x in thieu)


def test_E2_snapshot_day_du_thi_PINNED(nguong):
    v, thieu = MP.kiem_danh_tinh_model(
        {"provider": "gemini", "model_name": "gemini-2.5-flash",
         "model_version_or_snapshot": "gemini-2.5-flash-001",
         "temperature": 0.2, "top_p": 0.95, "max_output_tokens": 8192,
         "repair_limit": 3}, nguong)
    assert (v, thieu) == ("PINNED", [])


def test_E2b_tham_so_ghi_bang_VAN_XUOI_khong_duoc_tinh_la_da_ghim(nguong):
    """Tiền lệ THẬT trong kho, không phải ca giả định.

    `run_curved_ergonomics_v2.py:297` ghi `"repair_attempts": "mặc định sản
    phẩm"`. Chuỗi ấy vượt qua mọi phép kiểm `is not None` mà không nói con số
    nào đã dùng — nên guard phải đọc nó là CHƯA ghim.
    """
    goc = {"provider": "gemini", "model_name": "gemini-2.5-flash",
           "model_version_or_snapshot": "gemini-2.5-flash-001",
           "temperature": 0.2, "top_p": 0.95, "max_output_tokens": 8192,
           "repair_limit": 3}
    assert MP.kiem_danh_tinh_model(goc, nguong) == ("PINNED", [])

    v, thieu = MP.kiem_danh_tinh_model(
        {**goc, "repair_limit": "mặc định sản phẩm"}, nguong)
    assert v == "DECODING_INCOMPLETE"
    assert any("VĂN XUÔI" in x for x in thieu)


def test_E2c_True_khong_duoc_tinh_la_mot_so(nguong):
    """`bool` là `int` trong Python — `top_p=True` sẽ lọt nếu chỉ kiểm kiểu."""
    v, _ = MP.kiem_danh_tinh_model(
        {"provider": "gemini", "model_name": "m",
         "model_version_or_snapshot": "m-001", "temperature": 0.2,
         "top_p": True, "max_output_tokens": 8192, "repair_limit": 3}, nguong)
    assert v == "DECODING_INCOMPLETE"


def test_E3_policy_DOI_snapshot_bat_bien(nguong):
    assert nguong["model_identity_policy"]["require_immutable_snapshot"] is True
    assert nguong["model_identity_policy"]["alias_verdict"] == \
        "MODEL_IDENTITY_UNPINNED"


def test_E4_quyet_dinh_LIMITED_de_TRONG_cho_nguoi_ngoai(nguong):
    """`null` có chủ đích — đây là quyết định học thuật, không phải của bộ đo."""
    assert nguong["model_identity_policy"]["limited_reproducibility_allowed"] \
        is None


# ══ F · TIÊM LỖI ══════════════════════════════════════════════════════════
def test_F1_doi_eventual_servable_rate_lam_DOI_BAM(nguong):
    doi = json.loads(json.dumps(nguong))
    doi["family_thresholds"]["eventual_servable_rate"] = 0.8
    assert MP.bam_chinh_tac(doi) != MP.nap_nguong()[1]


def test_F2_doi_scorer_SAU_khi_manifest_tao__lo_ra_TROI(tmp_path):
    """Ghim rồi mà sửa bộ chấm thì phải LỘ RA — đúng phép so certifier §F làm.

    Không tiêm `hashlib`: băm là thứ đang được kiểm, giả nó đi thì test chỉ
    còn kiểm chính bản giả.
    """
    mf = _mo(tmp_path)
    scorer = GOC / "scripts" / "acceptance_verdict.py"
    assert mf.scorer_hash == hashlib.sha256(scorer.read_bytes()).hexdigest()

    sua_len = scorer.read_bytes() + b"\n# doi nguong sau khi biet ket qua\n"
    assert mf.scorer_hash != hashlib.sha256(sua_len).hexdigest()


def test_F2b_manifest_DA_GHI_troi_thi_guard_liet_ke_DUNG_truong(tmp_path):
    """Trôi chỉ quan sát được trên bản ĐÃ GHI — nên guard đọc từ đĩa.

    Ghim rồi recompute trong cùng một tiến trình là phép so luôn đúng: giữa
    hai lần đọc file không có gì kịp đổi. Đây là hình thù phép kiểm mà lượt
    live cần.
    """
    from acceptance_integrity import kiem_ghim_bo_do

    _mo(tmp_path)
    duong = tmp_path / "run" / "manifest.json"
    d = json.loads(duong.read_text(encoding="utf-8"))
    assert kiem_ghim_bo_do(d) == []                    # nguyên vẹn ⇒ im lặng

    for truong in ("scorer_hash", "threshold_policy_hash",
                   "attribution_rubric_hash", "policy_loader_hash"):
        loi = kiem_ghim_bo_do({**d, truong: "0" * 64})
        assert len(loi) == 1 and truong in loi[0] and "TRÔI" in loi[0]

        thieu = kiem_ghim_bo_do({k: v for k, v in d.items() if k != truong})
        assert len(thieu) == 1 and "THIẾU" in thieu[0]


def test_F2c_manifest_1_0_khong_dung_de_nghiem_thu_duoc():
    """Artifact lịch sử vẫn ĐỌC được (D6) nhưng không ghim được bộ đo — hai
    câu khác nhau, và guard phải nói câu thứ hai thành tiếng."""
    from acceptance_integrity import kiem_ghim_bo_do

    cu = RunManifest(
        run_id="cu", muc_dich="x", runner="r", runner_hash="h", model={},
        chinh_sach_sua="", ngan_sach_goi=0, seal={}, moi_truong={}, git={},
        artifact_schema_version="1.0").to_json()
    loi = kiem_ghim_bo_do(cu)
    assert len(loi) == 4 and all("THIẾU" in x for x in loi)


def test_F2d_manifest_1_1_THIEU_truong_bat_buoc_thi_bi_TU_CHOI(tmp_path):
    from acceptance_integrity import TRUONG_MANIFEST_1_1, kiem_manifest_du_truong

    _mo(tmp_path)
    d = json.loads((tmp_path / "run" / "manifest.json").read_text(
        encoding="utf-8"))
    assert kiem_manifest_du_truong(d) == []
    for t in TRUONG_MANIFEST_1_1:
        loi = kiem_manifest_du_truong({k: v for k, v in d.items() if k != t})
        assert len(loi) == 1 and t in loi[0]


def test_F2e_manifest_1_0_KHONG_bi_doi_truong_1_1():
    """Version dispatch RÕ RÀNG: bản cũ đọc được, không bị đo bằng thước mới."""
    from acceptance_integrity import kiem_manifest_du_truong

    assert kiem_manifest_du_truong({"artifact_schema_version": "1.0"}) == []


def test_F2f_bang_chung_attribution_thieu_reason_hoac_authority_thi_DO(rubric):
    """§F9 — `verdict` không kèm `reason` + `authority_hashes` là lời phán
    không truy được về đâu, và `SYSTEM_EXPRESSIVENESS_GAP` là lời phán tốn
    kém nhất trong bộ này."""
    du = {"case_id": "x", "yeu_cau_dai_luong": "area", "source_type": "scalar",
          "target_type": "scalar", "can_bien_doi": True,
          "valid_path_proof": "signature reachability: không có đường",
          "authority_hashes": {"rubric": "abc"},
          "verdict": "SYSTEM_EXPRESSIVENESS_GAP", "reason": "vì …"}
    assert MP.kiem_bang_chung_quy_trach_nhiem(du, rubric) == []

    for t in ("reason", "authority_hashes", "valid_path_proof"):
        loi = MP.kiem_bang_chung_quy_trach_nhiem({**du, t: None}, rubric)
        assert loi and any(t in x for x in loi), (t, loi)

    la = MP.kiem_bang_chung_quy_trach_nhiem(
        {**du, "verdict": "MODEL_LAM_BIENG"}, rubric)
    assert any("không nằm trong rubric" in x for x in la)


def test_F2g_cau_hinh_THAT_cua_kho_chua_du_de_chay_live(nguong):
    """Đo cấu hình đang có, không giả định — và nó CHƯA đủ."""
    chua = MP.san_sang_live_tu_cau_hinh(nguong)
    assert any("ALIAS TRÔI" in x for x in chua)
    assert any("limited_reproducibility_allowed" in x for x in chua)


def test_F3_doi_rubric_UNKNOWN_thanh_MODEL_lam_DOI_BAM(rubric):
    doi = json.loads(json.dumps(rubric))
    doi["valid_path_unknown"]["verdict"] = "MODEL_STATIC_FAILURE"
    assert MP.bam_chinh_tac(doi) != MP.nap_rubric()[1]


def test_F4_giam_mau_so_lam_DOI_BAM(nguong):
    doi = json.loads(json.dumps(nguong))
    doi["error_accounting"]["every_attempt_in_denominator"] = False
    assert MP.bam_chinh_tac(doi) != MP.nap_nguong()[1]


def test_F5_coi_UNRELATED_FAIL_CLOSED_la_dat_lam_DOI_BAM(nguong):
    doi = json.loads(json.dumps(nguong))
    doi["negative_thresholds"]["unrelated_fail_closed_allowed"] = 4
    assert MP.bam_chinh_tac(doi) != MP.nap_nguong()[1]


def test_F6_thieu_file_chinh_sach_thi_NEM(monkeypatch, tmp_path):
    monkeypatch.setattr(MP, "CHINH_SACH_NGUONG", tmp_path / "khong_co.json")
    with pytest.raises(FileNotFoundError, match="thiếu chính sách đo"):
        MP.nap_nguong()


def test_F7_chinh_sach_tro_SAI_candidate_thi_bao_loi(nguong):
    loi = MP.kiem_chinh_sach(nguong, candidate_hash="0" * 64,
                             pool_hash=nguong["pool_hash"])
    assert loi and any("candidate" in x for x in loi)


def test_F8_chinh_sach_thieu_truong_thi_bao_loi(nguong):
    doi = {k: v for k, v in nguong.items() if k != "family_thresholds"}
    loi = MP.kiem_chinh_sach(doi, candidate_hash=nguong["candidate_hash"],
                             pool_hash=nguong["pool_hash"])
    assert any("family_thresholds" in x for x in loi)
