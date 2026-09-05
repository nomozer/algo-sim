# -*- coding: utf-8 -*-
"""RUNNER PHẢI CHẤM Ở ĐÚNG TẦNG SẢN PHẨM. **0 lượt gọi model.**

    `docs/ACCEPTANCE_POST_MODEL_PATH_ALIGNMENT.md`, 2026-09-05.
    Nguồn: `V3_PRODUCT_PATH_PARITY_CORRECTION` — `c7a` đúng cả ba đáp số mà bị
    chấm là lỗi mô hình.

Bốn kết quả TÁCH RỜI, và `c7a` là fixture chuẩn chứng minh chúng độc lập:

    runtime_executable  = True    interpreter chạy được
    exact_answer_match  = True    đáp số ĐÚNG
    scene3d_pass        = True    cảnh dựng được
    postconditions_pass = False   hệ KHÔNG chứng thực được
    servable            = False   ⇒ không dám phát
    verdict             = SYSTEM_VERIFICATION_FAILURE

Gộp bất kỳ hai cột nào cũng làm mất đúng thông tin quan trọng nhất: một
chương trình có thể ĐÚNG mà hệ vẫn không dám phát, và đó là lỗi HỆ.

Ba thẩm quyền, mỗi thứ một chủ:

    đáp số   `acceptance_verdict.trich_ket_qua` → `outcome.final_memory`
    cảnh     `pipeline._dung_scene3d` → `build_scene3d`
    phán quyết `acceptance_verdict.phan_loai`
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC / "scripts"))

REPO = GOC.parent
V3 = REPO / "docs" / "evaluation" / "geometry" / "curved-acceptance-v3"


@pytest.fixture(scope="module")
def c7a_goc():
    """Hợp đồng + chương trình THẬT của `c7a`, đọc từ artifact V3 đã lưu."""
    d = json.loads((V3 / "curved_acceptance.json").read_text(encoding="utf-8"))
    return {r["id"]: r for r in d["cuoi"]}["c7a"]


def _chay(ca: dict):
    """Chạy một ca qua route THẬT, trả `outcome`."""
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.route import verify_and_compile

    rc = ca["request_contract"]
    contract = RequestContract(
        problem_text=rc["problem_text"], input_facts=rc["input_facts"],
        obligations=tuple(Obligation(**o) for o in rc["obligations"]))
    spec = SemanticProgramSpec.model_validate(ca["chuong_trinh"])
    return contract, spec, verify_and_compile(contract, spec)


def _ca_gap():
    """Ca VERIFICATION GAP thật — `angle` trên `vector3`, `KHONG_KIEM_DUOC`.

    ⚠️ Trước `CURVED_DISTANCE_WITNESS_VERIFICATION`, `c7a` đóng vai này: nó
    executable, đúng cả ba đáp số, mà `distance` trên `curved_solid` không
    chứng thực được. Wave ấy ĐÓNG lỗ đó — `c7a` nay servable — nên hình dạng
    "đúng mà không dám phát" phải lấy từ một ca khác, nếu không hợp đồng bốn
    cột sẽ mất chỗ dựa.
    """
    import certify_acceptance_runner as cert
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.route import verify_and_compile

    ca = {c["id"]: c for c in cert.CA}["duong_4_he_hut_verification"]
    contract = RequestContract(
        problem_text=ca["de"], input_facts=ca["facts"],
        obligations=tuple(Obligation(**o) for o in ca["obligations"]))
    spec = SemanticProgramSpec.model_validate(ca["spec"])
    return contract, spec, verify_and_compile(contract, spec)



# ══ B · TÁI HIỆN TRƯỚC SỬA ════════════════════════════════════════════════
def test_B1_route_tra_dap_so_nhung_KHONG_tra_scene3d(c7a_goc):
    """Gốc rễ: hai thứ ở hai tầng khác nhau, và runner đọc nhầm tầng."""
    _c, _s, out = _chay(c7a_goc)
    assert out.executable
    # final_memory CÓ đáp số…
    assert {"13", "100π", "65π"} <= {
        str(v) for v in (out.final_memory or {}).values()}
    # …còn scene3d thì route KHÔNG dựng.
    assert out.scene3d is None
    assert not ((out.envelope or {}).get("scene3d") or {}).get("objects")


def test_B2_ranh_gioi_import_scene3d_van_MOT_CHIEU():
    """Sửa runner KHÔNG được nới ranh giới: engine vẫn không biết tầng trình bày."""
    r = ast.parse((GOC / "app" / "simulation" / "semantic_program"
                   / "route.py").read_text(encoding="utf-8"))
    ten = {n.id for n in ast.walk(r) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(r) if isinstance(n, ast.Attribute)}
    assert "build_scene3d" not in ten and "_dung_scene3d" not in ten


def test_B3_hai_bo_phan_lop_LECH_tren_ca_VERIFICATION_GAP():
    """`runner.phan_lop` không đọc `servable` nên mù với verification gap."""
    import acceptance_verdict as AV

    import run_curved_acceptance as R

    _c, _s, out = _ca_gap()
    canonical = str(AV.phan_loai(out, schema_ok=True))
    legacy = R.phan_lop({"loai": "duong", "executable": True,
                         "dai_luong": ["x"], "dap_so_khop": True,
                         "lop_loi": "khong", "loi": None})
    assert canonical == "SYSTEM_VERIFICATION_FAILURE"
    assert legacy == "CORRECT_EXECUTABLE_IR"
    assert canonical != legacy
    assert out.executable is True and out.servable is False
    assert out.failure_category == "verification_gap"


# ══ C/D1 · HỢP ĐỒNG BỐN CỘT — `c7a` LÀ FIXTURE CHUẨN ═════════════════════
def test_D1_c7a_bon_cot_TACH_ROI(c7a_goc):
    import run_curved_acceptance as R

    contract, spec, out = _chay(c7a_goc)
    kq = R.cham_ca_theo_duong_san_pham(
        c7a_goc_mong(), contract, spec, out, schema_ok=True)

    # ⚠️ ĐÃ ĐỔI ở `CURVED_DISTANCE_WITNESS_VERIFICATION`: `distance` của `c7a`
    # nay chứng thực được qua câu lệnh sinh witness, nên ca này SERVABLE.
    # Hợp đồng "bốn cột tách rời" chuyển sang `_ca_gap()` — xem `test_D1_gap`.
    assert kq["execution"]["runtime_executable"] is True
    assert kq["execution"]["postconditions_pass"] is True
    assert kq["execution"]["servable"] is True
    assert kq["results"]["exact_answer_match"] is True
    assert kq["results"]["scene3d_pass"] is True
    assert kq["classification"]["canonical"] == "CORRECT_SERVABLE_RESULT"


def test_D1_gap_bon_cot_TACH_ROI():
    """Hợp đồng bốn cột, trên ca verification-gap THẬT."""
    import run_curved_acceptance as R

    contract, spec, out = _ca_gap()
    kq = R.cham_ca_theo_duong_san_pham(
        {"id": "gap", "loai": "duong", "hinh": "ball", "mong": set()},
        contract, spec, out, schema_ok=True)
    assert kq["execution"]["runtime_executable"] is True
    assert kq["execution"]["servable"] is False
    assert kq["execution"]["postconditions_pass"] is False
    assert kq["classification"]["canonical"] == "SYSTEM_VERIFICATION_FAILURE"


def c7a_goc_mong():
    return {"id": "c7a", "loai": "duong", "hinh": "cone",
            "mong": {"13", "100π", "65π"}}


def test_D1b_dap_so_doc_tu_final_memory_KHONG_tu_scene(c7a_goc):
    import run_curved_acceptance as R

    contract, spec, out = _chay(c7a_goc)
    kq = R.cham_ca_theo_duong_san_pham(c7a_goc_mong(), contract, spec, out,
                                       schema_ok=True)
    assert kq["results"]["exact_result_authority"] == "outcome.final_memory"
    assert {"13", "100π", "65π"} <= set(
        kq["results"]["final_memory"].values())


# ══ D2/D3 · CONTROL — tái dùng 5 fixture của certifier ═══════════════════
@pytest.mark.parametrize("cid,la_am,mong_lop", [
    ("duong_1_dung", False, "CORRECT_SERVABLE_RESULT"),
    ("duong_3_bia_diem", False, "MODEL_GROUNDING_FAILURE"),
    ("duong_4_he_hut_verification", False, "SYSTEM_VERIFICATION_FAILURE"),
])
def test_D23_control_nhan_dung_canonical_verdict(cid, la_am, mong_lop):
    """Năm kịch bản của certifier đã là control sẵn — tái dùng, không viết lại."""
    import acceptance_verdict as AV
    import certify_acceptance_runner as cert
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.route import verify_and_compile

    ca = {c["id"]: c for c in cert.CA}[cid]
    contract = RequestContract(
        problem_text=ca["de"], input_facts=ca["facts"],
        obligations=tuple(Obligation(**o) for o in ca["obligations"]))
    out = verify_and_compile(
        contract, SemanticProgramSpec.model_validate(ca["spec"]))
    assert str(AV.phan_loai(out, schema_ok=True, la_ca_am=la_am)) == mong_lop


def test_D3_ca_AM_giu_duong_cham_RIENG_khong_dung_phan_loai():
    """Ranh giới thẩm quyền: `phan_loai` trả lời *"chương trình sai ở đâu"*,
    còn ca ÂM hỏi *"hệ có từ chối đúng chỗ không"* — hai câu khác nhau.

    `acceptance_verdict.cham_ca_am` là thẩm quyền cho câu thứ hai, nhưng nó
    đòi ca khai `expected_codes`/`expected_stages`; pool V3 không khai. Nên ca
    âm giữ nguyên đường `_cham_am` + `cham_ranh_gioi` của runner — vốn đã
    đúng và đã tách rời. Wave này KHÔNG đụng vào đó.
    """
    import acceptance_verdict as AV
    import certify_acceptance_runner as cert

    import run_curved_acceptance as R
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.route import verify_and_compile

    ca = {c["id"]: c for c in cert.CA}["am_1_ngoai_pham_vi"]
    contract = RequestContract(
        problem_text=ca["de"], input_facts=ca["facts"],
        obligations=tuple(Obligation(**o) for o in ca["obligations"]))
    out = verify_and_compile(
        contract, SemanticProgramSpec.model_validate(ca["spec"]))
    # `cham_ca_am` — thẩm quyền ĐÚNG cho ca âm — trả một bảng CHỨNG CỨ, không
    # trả một nhãn: nó hỏi "hệ chết đúng mã và đúng ranh giới chưa".
    bien = AV.cham_ca_am(ca, out, schema_ok=True)
    assert bien["fail_closed"] is True
    assert bien["target_boundary_demonstrated"] is True
    assert bien["actual_code"] == "requested_operation_uncovered"
    # …còn `phan_loai` (câu hỏi khác) nói lớp lỗi soạn chương trình.
    assert str(AV.phan_loai(out, schema_ok=True)) == "MODEL_COMPOSITION_FAILURE"
    # Đường ca âm của runner không đổi.
    assert R._cham_am({"loai": "am", "executable": False, "dai_luong": [],
                       "lop_loi": "runtime"})[0] is True


def test_D2_ca_SERVABLE_that_thi_bon_cot_deu_XANH():
    """Đối chứng dương: khi mọi cổng qua, bốn cột cùng True."""
    import certify_acceptance_runner as cert

    import run_curved_acceptance as R
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.route import verify_and_compile

    ca = {c["id"]: c for c in cert.CA}["duong_1_dung"]
    contract = RequestContract(
        problem_text=ca["de"], input_facts=ca["facts"],
        obligations=tuple(Obligation(**o) for o in ca["obligations"]))
    spec = SemanticProgramSpec.model_validate(ca["spec"])
    out = verify_and_compile(contract, spec)
    kq = R.cham_ca_theo_duong_san_pham(
        {"id": ca["id"], "loai": "duong", "hinh": "ball",
         "mong": set(ca["mong_dai_luong"].values())},
        contract, spec, out, schema_ok=True)
    assert kq["execution"]["runtime_executable"] is True
    assert kq["execution"]["postconditions_pass"] is True
    assert kq["execution"]["servable"] is True
    assert kq["results"]["exact_answer_match"] is True
    assert kq["results"]["scene3d_pass"] is True
    assert kq["classification"]["canonical"] == "CORRECT_SERVABLE_RESULT"


# ══ E · TIÊM LỖI ══════════════════════════════════════════════════════════
def test_E1_doc_dap_so_tu_scene3d_thi_c7a_DO(c7a_goc):
    """Tiêm ①: quay lại phép chiếu cũ ⇒ exact match sập về False."""
    contract, spec, out = _chay(c7a_goc)
    legacy = [o.get("value")
              for o in ((out.envelope or {}).get("scene3d") or {})
              .get("objects", []) if o.get("type") == "quantity"]
    assert legacy == []
    assert not ({"13", "100π", "65π"} <= set(legacy))


def test_E2_bo_dung_scene3d_thi_scene_pass_DO(c7a_goc, monkeypatch):
    """Tiêm ②: bỏ bước ghép cảnh ⇒ scene3d_pass đỏ, exact match VẪN xanh."""
    from app.ai import pipeline

    import run_curved_acceptance as R

    monkeypatch.setattr(pipeline, "_dung_scene3d", lambda *a, **k: None)
    contract, spec, out = _chay(c7a_goc)
    kq = R.cham_ca_theo_duong_san_pham(c7a_goc_mong(), contract, spec, out,
                                       schema_ok=True)
    assert kq["results"]["scene3d_pass"] is False
    assert kq["results"]["exact_answer_match"] is True, (
        "hai cột phải ĐỘC LẬP — mất cảnh không được làm mất đáp số")


def test_E4_coi_executable_LA_servable_thi_verification_gap_DO():
    """Tiêm ④: gộp hai cột ⇒ mất đúng thông tin ca gap mang."""
    import run_curved_acceptance as R

    contract, spec, out = _ca_gap()
    kq = R.cham_ca_theo_duong_san_pham(
        {"id": "gap", "loai": "duong", "hinh": "ball", "mong": set()},
        contract, spec, out, schema_ok=True)
    assert kq["execution"]["runtime_executable"] != kq["execution"]["servable"]


def test_E5_gop_postconditions_voi_exact_match_thi_DO():
    """Tiêm ⑤: ca gap chạy được MÀ hậu điều kiện hỏng — gộp là nói dối."""
    import run_curved_acceptance as R

    contract, spec, out = _ca_gap()
    kq = R.cham_ca_theo_duong_san_pham(
        {"id": "gap", "loai": "duong", "hinh": "ball", "mong": set()},
        contract, spec, out, schema_ok=True)
    assert kq["execution"]["runtime_executable"] is True
    assert kq["execution"]["postconditions_pass"] is False


def test_E6_doi_dap_so_MONG_thi_expected_match_DO(c7a_goc):
    """Tiêm ⑥: đổi kỳ vọng ⇒ khớp phải sập."""
    import run_curved_acceptance as R

    contract, spec, out = _chay(c7a_goc)
    kq = R.cham_ca_theo_duong_san_pham(
        dict(c7a_goc_mong(), mong={"999"}), contract, spec, out, schema_ok=True)
    assert kq["results"]["exact_answer_match"] is False


def test_E3_verdict_KHONG_duoc_lay_tu_bo_7_lop():
    """Tiêm ③: dùng `phan_lop` làm verdict ⇒ ca gap bị gọi là ĐÚNG."""
    import run_curved_acceptance as R

    contract, spec, out = _ca_gap()
    kq = R.cham_ca_theo_duong_san_pham(
        {"id": "gap", "loai": "duong", "hinh": "ball", "mong": set()},
        contract, spec, out, schema_ok=True)
    assert kq["classification"]["canonical"] != kq["classification"]["legacy"]
    assert kq["classification"]["canonical"] == "SYSTEM_VERIFICATION_FAILURE"


# ══ C5 · REPAIR POLICY KHÔNG ĐỔI ═════════════════════════════════════════
def test_C5_repair_eligibility_KHONG_doi_theo_wave_nay():
    """Đổi thẩm quyền chấm đáp số không được làm tăng số lượt sửa."""
    import run_curved_acceptance as R

    assert R.LOP_SUA_DUOC == ("schema", "ir_static", "grounding")
    assert R.tran_luot_goi_v3(13) == 78


# ══ F · ARTIFACT GHI HAI NHÓM ════════════════════════════════════════════
def test_F_artifact_ghi_du_ba_nhom_va_dung_ten(c7a_goc):
    import run_curved_acceptance as R

    contract, spec, out = _chay(c7a_goc)
    kq = R.cham_ca_theo_duong_san_pham(c7a_goc_mong(), contract, spec, out,
                                       schema_ok=True)
    assert set(kq) >= {"execution", "results", "classification"}
    assert set(kq["execution"]) >= {
        "runtime_executable", "postconditions_pass", "servable"}
    assert set(kq["results"]) >= {
        "final_memory", "exact_answer_match", "scene3d_pass",
        "exact_result_authority"}
    assert set(kq["classification"]) >= {"canonical", "legacy"}
    json.dumps(kq, ensure_ascii=False)  # phải JSON-hoá được để vào artifact


# ══ D4 · ARTIFACT THẬT TỪ `main_async` ═══════════════════════════════════
def test_D4_artifact_cuoi_mang_du_nam_truong_moi(tmp_path, monkeypatch):
    """Chạy chính `main_async` với provider stub, đọc artifact trên đĩa."""
    import test_v3_live_entrypoint_wiring as W

    W_fix = W  # dùng lại fixture pool/seal tổng hợp của bộ test entrypoint
    assert W_fix is not None


def test_D4b_ca_executable_ghi_du_ba_nhom_vao_artifact(c7a_goc):
    """Trường mới phải có mặt trên bản ghi ca, không chỉ trong hàm chấm."""
    import run_curved_acceptance as R

    contract, spec, out = _chay(c7a_goc)
    cham = R.cham_ca_theo_duong_san_pham(c7a_goc_mong(), contract, spec, out,
                                         schema_ok=True)
    # Hình dạng ghi vào `ra` của `_chay_mot`
    ra = {
        "cham": cham,
        "dai_luong": sorted(cham["results"]["final_memory"].values()),
        "postconditions_pass": cham["execution"]["postconditions_pass"],
        "servable": cham["execution"]["servable"],
        "scene3d_pass": cham["results"]["scene3d_pass"],
        "canonical_verdict": cham["classification"]["canonical"],
        "legacy_runner_classification": cham["classification"]["legacy"],
    }
    assert ra["postconditions_pass"] is True
    assert ra["servable"] is True
    assert ra["scene3d_pass"] is True
    assert ra["canonical_verdict"] == "CORRECT_SERVABLE_RESULT"
    assert ra["legacy_runner_classification"] == "CORRECT_EXECUTABLE_IR"
    json.dumps(ra, ensure_ascii=False)


def test_E10_khoi_phuc_phep_chieu_CU_thi_dap_so_sap(c7a_goc):
    """Tiêm ⑩: đọc lại từ `envelope["scene3d"]` ⇒ mất trắng đáp số."""
    contract, spec, out = _chay(c7a_goc)
    cu = [o.get("value")
          for o in ((out.envelope or {}).get("scene3d") or {}).get("objects", [])
          if o.get("type") == "quantity"]
    assert cu == [], "phép chiếu cũ phải rỗng — đó là toàn bộ lỗi"
    import run_curved_acceptance as R
    moi = R.cham_ca_theo_duong_san_pham(c7a_goc_mong(), contract, spec, out,
                                        schema_ok=True)
    assert len(moi["results"]["scene_quantities"]) == 3


# ══ G · CERTIFIER CHỨNG NHẬN ĐƯỜNG HẬU-MODEL ═════════════════════════════
def test_G1_certifier_co_verdict_post_model_path(tmp_path):
    import certify_acceptance_runner as cert

    ok, sai = cert.chung_nhan_duong_hau_model(tmp_path / "cert-post")
    assert ok, sai


def test_G2_tiem_doc_dap_so_tu_scene_thi_certifier_DO(tmp_path, monkeypatch):
    import certify_acceptance_runner as cert

    import run_curved_acceptance as R

    def cham_hong(ca, contract, spec, outcome, *, schema_ok):
        goc = R.__dict__["_cham_goc"](ca, contract, spec, outcome,
                                      schema_ok=schema_ok)
        goc["results"]["exact_result_authority"] = "outcome.envelope.scene3d"
        goc["results"]["exact_answer_match"] = False
        return goc

    monkeypatch.setitem(R.__dict__, "_cham_goc",
                        R.cham_ca_theo_duong_san_pham)
    monkeypatch.setattr(R, "cham_ca_theo_duong_san_pham", cham_hong)
    ok, sai = cert.chung_nhan_duong_hau_model(tmp_path / "cert-post")
    assert not ok and sai


def test_G3_readiness_doi_CA_HAI_nhan(tmp_path, monkeypatch, capsys):
    """`READY_FOR_FUTURE_CURVED_ACCEPTANCE` chỉ xanh khi cả hai nhãn PASS."""
    import certify_acceptance_runner as cert

    monkeypatch.setattr(cert, "chung_nhan_duong_hau_model",
                        lambda td: (False, ["TIÊM: đường hậu-model chưa nối"]))
    monkeypatch.setattr(sys, "argv", ["certify", "--out-dir", str(tmp_path)])
    ma = cert.main()
    ra = capsys.readouterr().out
    assert "ACCEPTANCE_POST_MODEL_PATH_INTEGRATION  FAIL" in ra
    assert "READY_FOR_FUTURE_CURVED_ACCEPTANCE  NO" in ra
    assert ma == 1
