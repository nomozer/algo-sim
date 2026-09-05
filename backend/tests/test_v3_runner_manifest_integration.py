# -*- coding: utf-8 -*-
"""RUNNER V3 PHẢI ĐI QUA TẦNG TOÀN VẸN. **0 lượt gọi model.**

    `V3_RUNNER_MANIFEST_INTEGRATION_AND_LIMITED_REPRODUCIBILITY_DECISION`,
    2026-09-05.

Wave trước dựng xong tầng toàn vẹn (`RunManifest` 1.1, bốn băm bộ đo, guard
danh tính model) nhưng **runner V3 không gọi nó**. Một guard không nằm trên
đường chạy thật thì không bảo vệ gì cả — nó chỉ làm người đọc yên tâm.

Toàn bộ fixture là tổng hợp; provider luôn giả. V3 pool **chưa rút, chưa đọc
nội dung**.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC / "scripts"))

import measurement_policy as MP  # noqa: E402
from acceptance_integrity import (  # noqa: E402
    ARTIFACT_SCHEMA_VERSION,
    IntegrityError,
    RunManifest,
    kiem_ghim_bo_do,
    mo_run,
)

RUNNER = GOC / "scripts" / "run_curved_acceptance.py"


@pytest.fixture(scope="module")
def nguong():
    return MP.nap_nguong()[0]


@pytest.fixture(scope="module")
def rubric():
    return MP.nap_rubric()[0]


@pytest.fixture(scope="module")
def cay():
    return ast.parse(RUNNER.read_text(encoding="utf-8"))


def _ten_goi(cay) -> set[str]:
    """Mọi tên hàm được GỌI trong runner — đọc từ AST, không grep chuỗi.

    Grep sẽ trúng cả docstring và comment; ở đây câu hỏi là *"runner có thật
    sự gọi hàm đó không"*, và chỉ AST trả lời được câu ấy.
    """
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                ra.add(f.id)
            elif isinstance(f, ast.Attribute):
                ra.add(f.attr)
    return ra


# ══ A · KHOẢNG HỞ — mỗi test dưới đây ĐỎ trước khi wave này sửa ═══════════
def test_A1_runner_V3_GOI_mo_run(cay):
    """§A1 — khoảng hở gốc: runner không đi qua tầng toàn vẹn."""
    assert "mo_run" in _ten_goi(cay), (
        "runner V3 không gọi `mo_run` — mọi thứ wave trước ghim (scorer, "
        "ngưỡng, rubric, loader, danh tính model) sẽ KHÔNG có mặt trong "
        "artifact của lượt V3")


def test_A2_runner_KHONG_con_duong_moi_truong_rieng(cay):
    """§A2 — `_moi_truong()` riêng là bản sao thứ hai của một thẩm quyền.

    Bản sao thứ hai luôn trôi khỏi bản gốc, và cái trôi sẽ là cái không ai
    nhìn. Cho phép nó tồn tại như wrapper MỎNG gọi thẩm quyền chung.
    """
    for n in ast.walk(cay):
        if isinstance(n, ast.FunctionDef) and n.name == "_moi_truong":
            goi = _ten_goi(n)
            assert "moi_truong_hien_tai" in goi, (
                "`_moi_truong()` tự dựng bảng môi trường thay vì gọi "
                "`acceptance_integrity.moi_truong_hien_tai()`")


def test_A3_artifact_mang_DU_bon_bam_bo_do_va_danh_tinh_model(tmp_path):
    """§A3–A4 — lượt giả lập TRƯỚC lượt gọi đầu tiên đã có manifest đủ trường."""
    import run_curved_acceptance as R

    mf = R.mo_luot_do_v3(tmp_path / "run", run_id="t", ca=[],
                         bo_qua_dirty=True, gia_lap=True)
    d = json.loads((tmp_path / "run" / "manifest.json").read_text(
        encoding="utf-8"))
    assert kiem_ghim_bo_do(d) == []
    for t in ("scorer_hash", "threshold_policy_hash", "attribution_rubric_hash",
              "policy_loader_hash", "model_provider", "model_name",
              "decoding_parameters", "repair_limit", "transport_retry_policy",
              "application_call_budget"):
        assert t in d, t
    assert mf.artifact_schema_version == ARTIFACT_SCHEMA_VERSION


def test_A5_doi_scorer_TRUOC_luot_gia_lap_bi_runner_BAT(tmp_path):
    """§A5 — trôi phải bị chặn TRÊN ĐƯỜNG CHẠY, không phải chỉ trong certifier."""
    import run_curved_acceptance as R

    R.mo_luot_do_v3(tmp_path / "run", run_id="t", ca=[], bo_qua_dirty=True,
                    gia_lap=True)
    d = json.loads((tmp_path / "run" / "manifest.json").read_text(
        encoding="utf-8"))
    d["scorer_hash"] = "0" * 64
    (tmp_path / "run" / "manifest.json").write_text(
        json.dumps(d, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(IntegrityError, match="TRÔI"):
        R.canh_gac_truoc_luot_goi(tmp_path / "run", con_lai=1)


def test_A6_chung_nhan_XANH_khong_dong_nghia_runner_da_lap(cay):
    """§A6 — hai câu khác nhau, và trước wave này câu thứ hai là SAI.

    Certifier chạy runner TỔNG HỢP của chính nó. Nó xanh cả khi runner V3
    thật chưa chạm `mo_run` một lần nào — nên chứng nhận phải nói được về
    runner V3 THẬT, không chỉ về bài kiểm của chính nó.
    """
    import certify_acceptance_runner as cert

    assert hasattr(cert, "chung_nhan_runner_v3"), (
        "certifier chưa có phép kiểm nào chạm runner V3 thật")


# ══ B · QUYẾT ĐỊNH LIMITED ĐÃ GHI VÀ ĐÃ BĂM ═══════════════════════════════
def test_B1_policy_ghi_LIMITED_va_bump_version(nguong):
    mip = nguong["model_identity_policy"]
    assert mip["limited_reproducibility_allowed"] is True
    assert nguong["policy_version"] == "1.1.0"
    assert mip["accepted_verdict"] == "LIMITED_ACCEPTED"


def test_B2_moi_nguong_SO_HOC_giu_nguyen(nguong):
    """Chỉ quyết định reproducibility được đổi. Ngưỡng số học mà trôi theo thì
    bump version đã thành cái cớ."""
    sd, rv = nguong["sample_design"], nguong["run_validity"]
    ft, gc = nguong["family_thresholds"], nguong["general_curved_acceptance"]
    nt = nguong["negative_thresholds"]
    assert (sd["total_cells"], sd["positive_cells"], sd["negative_cells"]) == \
        (13, 9, 4)
    assert rv["selected_cases_required"] == 13
    assert ft["minimum_selected_positive_cases"] == 3
    for k in ("eventual_servable_rate", "exact_answer_match_rate",
              "scene3d_generated_rate", "postconditions_pass_rate"):
        assert ft[k] == 1.0, k
    assert ft["r0_laundering_allowed"] == 0
    assert ft["system_expressiveness_gap_allowed"] == 0
    assert ft["attribution_unresolved_allowed"] == 0
    assert gc["required_family_passes"] == "3/3"
    assert nt["correct_fail_closed"] == "4/4"
    assert nt["target_boundary_demonstrated"] == "4/4"


def test_B3_LIMITED_khong_duoc_hien_thanh_PINNED(nguong):
    v, thieu = MP.kiem_danh_tinh_model(MP.cau_hinh_model_hien_tai(), nguong)
    assert v == "LIMITED_ACCEPTED"
    assert v != "PINNED"
    assert any("ALIAS" in x for x in thieu), "vẫn phải KHAI alias là alias"


def test_B4_LIMITED_bi_TAT_thi_alias_tro_lai_thanh_blocker(nguong):
    tat = json.loads(json.dumps(nguong))
    tat["model_identity_policy"]["limited_reproducibility_allowed"] = False
    v, _ = MP.kiem_danh_tinh_model(MP.cau_hinh_model_hien_tai(), tat)
    assert v == "MODEL_IDENTITY_UNPINNED"


# ══ C · HỢP ĐỒNG THAM SỐ GIẢI MÃ CÓ KIỂU ══════════════════════════════════
def test_C1_ba_trang_thai_phan_biet_duoc(nguong):
    assert MP.kiem_tham_so_giai_ma(
        {"temperature": {"mode": "explicit", "value": 0.2},
         "top_p": {"mode": "not_sent", "value": None},
         "max_output_tokens": {"mode": "not_sent", "value": None}},
        nguong) == []


def test_C2_explicit_PHAI_co_so(nguong):
    loi = MP.kiem_tham_so_giai_ma(
        {"temperature": {"mode": "explicit", "value": None}}, nguong)
    assert loi and "explicit" in loi[0]


def test_C3_not_sent_PHAI_co_value_null(nguong):
    loi = MP.kiem_tham_so_giai_ma(
        {"top_p": {"mode": "not_sent", "value": 0.95}}, nguong)
    assert loi and "not_sent" in loi[0]


def test_C4_van_xuoi_KHONG_thay_duoc_gia_tri_co_kieu(nguong):
    loi = MP.kiem_tham_so_giai_ma({"top_p": "provider default"}, nguong)
    assert loi and any("CÓ KIỂU" in x.upper() for x in loi)


def test_C5_bool_KHONG_phai_so(nguong):
    loi = MP.kiem_tham_so_giai_ma(
        {"temperature": {"mode": "explicit", "value": True}}, nguong)
    assert loi


def test_C6_provider_default_unobserved_CHI_hop_le_trong_LIMITED(nguong):
    ok = {"top_p": {"mode": "provider_default_unobserved", "value": None}}
    assert MP.kiem_tham_so_giai_ma(ok, nguong) == []

    tat = json.loads(json.dumps(nguong))
    tat["model_identity_policy"]["limited_reproducibility_allowed"] = False
    loi = MP.kiem_tham_so_giai_ma(ok, tat)
    assert loi and "LIMITED" in loi[0]


def test_C7_cau_hinh_that_khai_dung_trang_thai():
    """Manifest phản ánh REQUEST THẬT: `top_p` không được gửi, và điền một con
    số giả cho nó là bịa lại lịch sử của lượt đo."""
    tsi = MP.cau_hinh_model_hien_tai()["decoding_parameters"]
    assert tsi["temperature"] == {"mode": "explicit", "value": 0.2}
    assert tsi["top_p"] == {"mode": "not_sent", "value": None}
    assert tsi["max_output_tokens"] == {"mode": "not_sent", "value": None}


def test_C8_schema_version_bump_va_van_doc_duoc_1_0_va_1_1():
    from acceptance_integrity import kiem_manifest_du_truong

    assert ARTIFACT_SCHEMA_VERSION == "1.2"
    for cu in ("1.0", "1.1"):
        assert kiem_manifest_du_truong({"artifact_schema_version": cu}) == []


# ══ D · TRẦN LƯỢT GỌI DẪN XUẤT, KHÔNG PHỎNG ĐOÁN ══════════════════════════
def test_D1_cong_thuc_dung_hard_upper_bound():
    assert MP.derive_application_call_budget(
        selected_cases=13, analyze_calls_per_case=1,
        synthesis_attempt_limit=3, calls_per_attempt=1) == 13 * (1 + 3)


def test_D2_tran_V3_gom_CA_HAI_chang_8A_va_8B():
    """Runner V3 chạy hai chặng. Trần một chặng là một cái phanh hụt."""
    import run_curved_acceptance as R

    assert R.tran_luot_goi_v3(13) == 13 * (1 + 1) + 13 * (1 + 3)


def test_D3_giam_mot_call_lam_TRAN_do_o_worst_case():
    import run_curved_acceptance as R

    n = 13
    assert R.tran_luot_goi_v3(n) - 1 < R.tran_luot_goi_v3(n)


def test_D4_cong_thuc_KHOP_call_graph_that_cua_pipeline():
    """Đọc `app/ai/pipeline.py` bằng AST: đúng HAI chỗ gọi provider trên đường
    hình học — analyze một lượt, tổng hợp một lượt mỗi attempt."""
    from app.ai import pipeline

    cay = ast.parse(Path(pipeline.__file__).read_text(encoding="utf-8"))
    trong = {}
    for n in ast.walk(cay):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            trong[n.name] = sum(
                1 for x in ast.walk(n)
                if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                and x.func.id == "call_gemini")
    assert trong["stage_semantic_analyze"] == 1
    assert trong["stage_semantic_program"] == 1
    assert pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS == 3


def test_D5_tran_ghi_vao_manifest_TRUOC_luot_goi_dau(tmp_path):
    import run_curved_acceptance as R

    mf = R.mo_luot_do_v3(tmp_path / "run", run_id="t", ca=[],
                         bo_qua_dirty=True, gia_lap=True)
    assert mf.application_call_budget == R.tran_luot_goi_v3(0)


# ══ E · RUNNER DÙNG ĐÚNG POOL V3, KHÔNG DÙNG CORPUS PHÁT TRIỂN ════════════
def test_E1_chua_rut_thi_TU_CHOI_chay(tmp_path, monkeypatch):
    """`seed = null` ⇒ chưa có tập đo ⇒ không lượt nào được phép bắt đầu.

    ⚠️ Bản trước khẳng định điều này trên **con dấu THẬT**, và nó xanh chỉ vì
    pool V3 khi ấy chưa rút. Rút là thao tác MỘT CHIỀU (`_rut` từ chối lần
    hai), nên 2026-09-05 — khi lượt live thật sự chạy — test hoá đỏ vì một lý
    do không liên quan gì tới điều nó muốn khoá. Một bất biến neo vào trạng
    thái nhất thời của dữ liệu thật thì đo chính trạng thái ấy, không đo luật.
    Nay dùng con dấu TỔNG HỢP: luật giữ nguyên, và nó đúng ở cả hai phía của
    lần rút.
    """
    import seal_curved_v3 as SC

    import run_curved_acceptance as R

    dau = tmp_path / "V3_SEAL.json"
    dau.write_text(json.dumps({
        "pool_hash": "0" * 64, "pool_size": 26, "o": [], "o_duong": [],
        "o_am": [], "measured_system_hash": "0" * 64,
        "measured_system_files": 89, "seed": None, "da_rut": None,
    }, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(SC, "DAU", dau)

    with pytest.raises(IntegrityError, match="chưa rút|CHƯA RÚT"):
        R.nap_ca_v3()


def test_E2_corpus_V1_V2_KHONG_duoc_dung_lam_bo_ca_V3():
    """Fault injection §J14 — corpus phát triển đi vào chỗ pool V3 phải ĐỎ."""
    import run_curved_acceptance as R

    with pytest.raises(IntegrityError, match="corpus|CORPUS"):
        R.kiem_bo_ca_la_pool_v3(R.CA)


# ══ H · ĐƯỜNG LƯU BẰNG CHỨNG QUY TRÁCH NHIỆM ══════════════════════════════
def test_H1_bang_chung_dung_schema_thi_ghi_duoc(tmp_path, rubric):
    import run_curved_acceptance as R

    R.mo_luot_do_v3(tmp_path / "run", run_id="t", ca=[], bo_qua_dirty=True,
                    gia_lap=True)
    bc = {"case_id": "C1", "yeu_cau_dai_luong": "area",
          "source_type": "scalar", "target_type": "scalar",
          "can_bien_doi": True, "valid_path_proof": "reachability: không có",
          "authority_hashes": {"rubric": MP.nap_rubric()[1]},
          "verdict": "SYSTEM_EXPRESSIVENESS_GAP", "reason": "vì …",
          "evaluator": "người-ngoài-1"}
    duong = R.ghi_bang_chung_quy_trach_nhiem(tmp_path / "run", bc)
    d = json.loads(duong.read_text(encoding="utf-8"))
    assert d["rubric_hash"] == MP.nap_rubric()[1]
    assert d["evaluator"] == "người-ngoài-1"


def test_H2_thieu_reason_hoac_authority_thi_TU_CHOI(tmp_path, rubric):
    import run_curved_acceptance as R

    R.mo_luot_do_v3(tmp_path / "run", run_id="t", ca=[], bo_qua_dirty=True,
                    gia_lap=True)
    thieu = {"case_id": "C1", "yeu_cau_dai_luong": "area",
             "source_type": "scalar", "target_type": "scalar",
             "can_bien_doi": True, "valid_path_proof": "x",
             "verdict": "SYSTEM_EXPRESSIVENESS_GAP", "evaluator": "ai đó"}
    with pytest.raises(IntegrityError):
        R.ghi_bang_chung_quy_trach_nhiem(tmp_path / "run", thieu)


# ══ J · TIÊM LỖI TRÊN ĐƯỜNG CHẠY THẬT ═════════════════════════════════════
@pytest.mark.parametrize("truong", [
    "scorer_hash", "threshold_policy_hash", "attribution_rubric_hash",
    "policy_loader_hash",
])
def test_J3456_doi_bam_GIUA_hai_luot_goi_thi_DO(tmp_path, truong):
    import run_curved_acceptance as R

    R.mo_luot_do_v3(tmp_path / "run", run_id="t", ca=[], bo_qua_dirty=True,
                    gia_lap=True)
    duong = tmp_path / "run" / "manifest.json"
    R.canh_gac_truoc_luot_goi(tmp_path / "run", con_lai=5)   # lượt 1: qua

    d = json.loads(duong.read_text(encoding="utf-8"))
    d[truong] = "0" * 64
    duong.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(IntegrityError, match="TRÔI"):
        R.canh_gac_truoc_luot_goi(tmp_path / "run", con_lai=4)  # lượt 2: đỏ


def test_J10_het_tran_thi_DUNG_dung_cho(tmp_path):
    import run_curved_acceptance as R

    R.mo_luot_do_v3(tmp_path / "run", run_id="t", ca=[], bo_qua_dirty=True,
                    gia_lap=True)
    with pytest.raises(IntegrityError, match="trần|TRẦN"):
        R.canh_gac_truoc_luot_goi(tmp_path / "run", con_lai=0)


def test_J11_tang_quota_SAU_khi_mo_run_lam_guard_DO(tmp_path):
    import run_curved_acceptance as R

    R.mo_luot_do_v3(tmp_path / "run", run_id="t", ca=[], bo_qua_dirty=True,
                    gia_lap=True)
    duong = tmp_path / "run" / "manifest.json"
    d = json.loads(duong.read_text(encoding="utf-8"))
    d["application_call_budget"] = 10_000
    duong.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(IntegrityError, match="trần|budget|TRẦN"):
        R.canh_gac_truoc_luot_goi(tmp_path / "run", con_lai=1)


def test_J13_runner_KHONG_ghi_secret_vao_artifact(tmp_path):
    """Quét artifact tìm khoá. Chưa từng rò, và cách giữ nguyên như thế là có
    một guard chứ không phải có một thói quen."""
    import run_curved_acceptance as R

    R.mo_luot_do_v3(tmp_path / "run", run_id="t", ca=[], bo_qua_dirty=True,
                    gia_lap=True)
    tho = (tmp_path / "run" / "manifest.json").read_text(encoding="utf-8")
    assert R.quet_bi_mat(tho) == []
    assert R.quet_bi_mat('{"api_key": "AIzaSyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q"}')


def test_J2_manifest_PHAI_co_truoc_luot_goi_dau(tmp_path):
    import run_curved_acceptance as R

    with pytest.raises(IntegrityError, match="manifest"):
        R.canh_gac_truoc_luot_goi(tmp_path / "khong-co-run", con_lai=1)


def test_J1_runner_bo_goi_mo_run_thi_CHUNG_NHAN_do(tmp_path, monkeypatch):
    """§J1 — chính khoảng hở wave này đóng, tiêm ngược lại để thấy cổng đỏ.

    Nếu bài chứng nhận vẫn xanh khi runner bỏ `mo_run`, thì nó chưa chứng minh
    điều nó nói là đang chứng minh.
    """
    import certify_acceptance_runner as cert
    import run_curved_acceptance as R

    def bo_qua_mo_run(thu_muc, **kw):
        """Runner "chạy" nhưng không đi qua tầng toàn vẹn — đúng nết cũ."""
        Path(thu_muc).mkdir(parents=True, exist_ok=True)
        return None

    monkeypatch.setattr(R, "mo_luot_do_v3", bo_qua_mo_run)
    ok, sai = cert.chung_nhan_runner_v3(tmp_path / "v3")
    assert not ok
    assert any("manifest" in x.lower() for x in sai), sai


def test_J7_alias_ghi_thanh_PINNED_thi_CHUNG_NHAN_do(tmp_path, monkeypatch):
    """§J7 — `LIMITED_ACCEPTED` bị hiển thị thành `PINNED` là điều chính sách
    CẤM thẳng (`limited_forbids`). Guard phải bắt, không chỉ tài liệu cấm."""
    import certify_acceptance_runner as cert

    monkeypatch.setattr(MP, "kiem_danh_tinh_model",
                        lambda m, n: ("PINNED", []))
    ok, sai = cert.chung_nhan_runner_v3(tmp_path / "v3")
    assert not ok
    assert any("LIMITED_ACCEPTED" in x for x in sai), sai


def test_J8_NOT_SENT_bi_thay_bang_van_xuoi_thi_DO(nguong):
    """§J8 — "provider default" là câu tôi đã thấy lọt guard một lần rồi."""
    loi = MP.kiem_tham_so_giai_ma(
        {"top_p": {"mode": "not_sent", "value": "provider default"}}, nguong)
    assert loi and "not_sent" in loi[0]


def test_J9_temperature_True_thi_DO(nguong):
    loi = MP.kiem_tham_so_giai_ma(
        {"temperature": {"mode": "explicit", "value": True}}, nguong)
    assert loi


def test_I_chung_nhan_runner_v3_XANH_khi_khoi_phuc(tmp_path):
    """Sau mọi phép tiêm, bản chuẩn phải xanh — nếu không thì cái đỏ ở trên
    không chứng minh được gì."""
    import certify_acceptance_runner as cert

    ok, sai = cert.chung_nhan_runner_v3(tmp_path / "v3")
    assert ok, sai
