# -*- coding: utf-8 -*-
"""N04_TARGETED_REJECTION_REGISTRY_V2_PREREGISTRATION — chấm N04 đúng sau bản sửa an toàn.

Registry v1 (đăng ký trước bản sửa) ghim N04 bằng `INVALID_CONFLICT` — trạng thái
adapter, không phải mã từ chối. Sau `STRUCTURED_RELATION_SAFETY_REPAIR`, N04 AN TOÀN
nhưng TARGETED v1 báo NO oan. Registry v2 là OVERLAY: v1 giữ nguyên byte và vẫn là
kỳ vọng GỐC; v2 chỉ ghi đè N04 bằng một tuple hành vi CHÍNH XÁC. Bộ đo báo CẢ HAI.

Danh sách ca, số lượng, băm v1 và băm overlay viết CỨNG — không tự sinh tham số từ
chính registry cần bảo vệ. 0 request mạng.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_multicase_benchmark as B  # noqa: E402
import test_completion_runner_repair as TR  # noqa: E402

DGEO = REPO / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene"
V1 = DGEO / "completion-runner-repair-offline" / "NEGATIVE_TARGETED_REJECTION_REGISTRY.json"
V2 = DGEO / "n04-targeted-rejection-registry-v2-preregistration" / "NEGATIVE_TARGETED_REJECTION_REGISTRY_V2.json"
SHA_V1 = "52bc6379d2f01372513d5aa21bd25433ea27783edae416cc7a1ed95fa8bb7100"          # viết CỨNG
BLOB_V1 = "876d7f9e6c93be3d387f0b486f22ac2242a208fb"
SHA_V2 = "03a87ba37a6df62604d33119f346101e1f9e6f10f8db63b6fdbff6ce40c07e81"
CA_AM = ["N01", "N02", "N03", "N04"]
TUPLE_N04 = {"adapter_status": "INVALID_CONFLICT", "rejection_code": "STRUCTURED_RELATION_CONTRADICTION",
             "rule_id": "MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE", "rejection_phase": "FACT_GRAPH",
             "compiler_reached": False, "program_created": False, "scene_created": False,
             "final_memory_created": False, "answer_created": False}


def _TH():
    import aggregate_multicase_completion as TH
    return TH


def _dk():
    return _TH().doc_registry_tu_choi_v2()


def _ghi_overlay(tmp_path, sua) -> Path:
    d = json.loads(V2.read_text(encoding="utf-8"))
    sua(d)
    p = tmp_path / "V2.json"
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


# ══ V1 BẤT BIẾN · OVERLAY KHOÁ CỨNG ══════════════════════════════════════
def test_registry_v1_khong_doi_mot_byte():
    assert TR._sha_lf(V1) == SHA_V1
    blob = subprocess.run(["git", "rev-parse", f"HEAD:{V1.relative_to(REPO).as_posix()}"], cwd=REPO,
                          capture_output=True, text=True).stdout.strip()
    assert blob == BLOB_V1


def test_overlay_khoa_cung_va_chi_ghi_de_N04():
    assert TR._sha_lf(V2) == SHA_V2
    d = json.loads(V2.read_text(encoding="utf-8"))
    assert d["version"] == "negative-targeted-rejection/2"
    assert d["base_registry_version"] == "negative-targeted-rejection/1"
    assert d["base_registry_sha256"] == SHA_V1
    assert d["allowed_override_case_ids"] == ["N04"] and list(d["overrides"]) == ["N04"]
    assert d["overrides"]["N04"]["expected_rejection"] == TUPLE_N04
    assert d["overrides"]["N04"]["dataset_role"] == "DEVELOPMENT_REGRESSION_CASE"


def test_resolved_dung_bon_ca_N01_N03_trung_v1_tung_byte():
    dk = _dk()
    v1 = json.loads(V1.read_text(encoding="utf-8"))
    ca = dk["RESOLVED"]["CASES"]
    assert sorted(ca) == CA_AM and len(ca) == 4
    for cid in ("N01", "N02", "N03"):
        assert json.dumps(ca[cid], sort_keys=True) == json.dumps(v1["CASES"][cid], sort_keys=True), cid
    assert ca["N04"]["V2_EXPECTED_REJECTION"] == TUPLE_N04
    m = dk["META"]
    assert m["BASE_REGISTRY_SHA256"] == SHA_V1 and m["OVERLAY_SHA256"] == SHA_V2
    assert len(m["RESOLVED_REGISTRY_SHA256"]) == 64 and m["VERSION"] == "negative-targeted-rejection/2"
    assert m["DATASET_ROLES"]["N04"] == "DEVELOPMENT_REGRESSION_CASE"
    assert m["DATASET_ROLES"]["N02"] == "DEVELOPMENT_HOLDOUT_PILOT"
    assert _dk() == dk                                      # tất định


@pytest.mark.parametrize("ten,sua,ma", [
    ("base_thieu", lambda d: d.update(base_registry_path="docs/khong_ton_tai.json"), "BASE_REGISTRY_MISSING"),
    ("base_sai_bam", lambda d: d.update(base_registry_sha256="0" * 64), "BASE_REGISTRY_HASH_MISMATCH"),
    ("head_truoc_ban_sua", lambda d: d.update(product_behavior_head="35d84da0"), "PRODUCT_HEAD_INVALID"),
    ("head_khong_ton_tai", lambda d: d.update(product_behavior_head="f" * 40), "PRODUCT_HEAD_INVALID"),
    ("ca_khong_co_trong_base", lambda d: (d["overrides"].update(N99=d["overrides"]["N04"]),
                                          d.update(allowed_override_case_ids=["N04", "N99"])),
     "OVERRIDE_CASE_NOT_IN_BASE"),
    ("ghi_de_ca_ngoai_danh_sach", lambda d: d["overrides"].update(N01=d["overrides"]["N04"]),
     "OVERRIDE_CASE_NOT_ALLOWED"),
    ("mo_rong_danh_sach_cho_phep", lambda d: d.update(allowed_override_case_ids=["N01", "N04"]),
     "OVERRIDE_CASE_NOT_ALLOWED"),
    ("thieu_rule", lambda d: d["overrides"]["N04"]["expected_rejection"].pop("rule_id"), "REQUIRED_FIELD_MISSING"),
    ("thieu_code", lambda d: d["overrides"]["N04"]["expected_rejection"].pop("rejection_code"),
     "REQUIRED_FIELD_MISSING"),
    ("N04_la_holdout", lambda d: d["overrides"]["N04"].update(dataset_role="DEVELOPMENT_HOLDOUT_PILOT"),
     "DATASET_ROLE_INVALID"),
    ("sai_version", lambda d: d.update(version="negative-targeted-rejection/1"), "OVERLAY_VERSION_INVALID"),
])
def test_bo_nap_FAIL_CLOSED(tmp_path, ten, sua, ma):
    with pytest.raises(_TH().LoiRegistry) as e:
        _TH().doc_registry_tu_choi_v2(_ghi_overlay(tmp_path, sua))
    assert e.value.ma == ma


def test_bo_nap_bac_HAI_ghi_de_canh_tranh(tmp_path):
    t = V2.read_text(encoding="utf-8")
    i = t.index('"N04": {', t.index('"overrides"'))
    p = tmp_path / "V2.json"
    p.write_text(t[:i] + '"N04": {"dataset_role": "DEVELOPMENT_REGRESSION_CASE"},\n    ' + t[i:], encoding="utf-8")
    with pytest.raises(_TH().LoiRegistry) as e:
        _TH().doc_registry_tu_choi_v2(p)
    assert e.value.ma == "DUPLICATE_OVERRIDE"


# ══ N04 — QUA RUNNER THẬT ═════════════════════════════════════════════════
def test_A_N04_dung_ban_sua_V1_NO_V2_YES():
    r = TR._mot_ca("N04", TR.DOC_DUNG_CA_AM["N04"])
    assert r["SAFE_REJECTION"] is True
    assert r["TARGETED_REJECTION_MATCH"] == "NO"                    # kỳ vọng GỐC trước sửa — giữ nguyên
    assert r["TARGETED_REJECTION_V2"] == "YES", r.get("TARGETED_DETAIL_V2")
    assert r["DATASET_ROLE"] == "DEVELOPMENT_REGRESSION_CASE"
    assert r["BUILD"]["ADAPTER_RULE_ID"] == TUPLE_N04["rule_id"]
    assert r["BUILD"]["ADAPTER_PHASE"] == "FACT_GRAPH"
    assert r["TARGETED_REGISTRY_RESOLVED_SHA256"] == _dk()["META"]["RESOLVED_REGISTRY_SHA256"]


def test_B_N04_phan_hoi_rong_an_toan_nhung_V2_NO():
    r = TR._mot_ca("N04", "{}")
    assert r["SAFE_REJECTION"] is True and r["TARGETED_REJECTION_V2"] == "NO"
    assert r["ANALYZE_INFORMATION_COMPLETENESS"] == "FAIL"


def _ban_ghi_n04_that() -> dict:
    return TR._mot_ca("N04", TR.DOC_DUNG_CA_AM["N04"])


def _v2(r) -> str:
    TH = _TH()
    rel, _ = TH.doc_registry_ca_am()
    return TH.doi_chieu_tu_choi_v2(r, "N04", rel, _dk())["TARGETED_REJECTION_V2"]


def test_C_D_E_F_moi_lech_tuple_deu_lam_V2_NO():
    goc = _ban_ghi_n04_that()
    assert _v2(goc) == "YES"
    import copy
    c = copy.deepcopy(goc); c["REJECTION_CODE"] = "INVALID_CONFLICT"                       # C · đúng status, sai code
    assert _v2(c) == "NO"
    d = copy.deepcopy(goc); d["BUILD"]["ADAPTER_RULE_ID"] = "SOME_OTHER_RULE"              # D · đúng code, sai rule
    assert _v2(d) == "NO"
    e = copy.deepcopy(goc); e["BUILD"]["COMPILER_ELIGIBILITY"] = "SUPPORTED"               # E · compiler vẫn chạy
    assert _v2(e) == "NO"
    f = copy.deepcopy(goc)                                                                  # F · cảnh / đáp số được tạo
    f["BUILD"].update(COMPILE_STATUS="COMPILED", SCENE_NON_EMPTY=True, FINAL_MEMORY_OK=True,
                      PYDANTIC_PROGRAM_VALIDATION="PASS")
    f.update(SAFE_REJECTION=False, UNSAFE_ACCEPTANCE=True)
    assert _v2(f) == "NO" and f["SAFE_REJECTION"] is False
    g = copy.deepcopy(goc); g["BUILD"]["SCENE_NON_EMPTY"] = True                           # chỉ cảnh thôi cũng trượt
    assert _v2(g) == "NO"
    h = copy.deepcopy(goc); h["BUILD"]["ADAPTER_PHASE"] = "COMPILER_ELIGIBILITY"           # sai pha
    assert _v2(h) == "NO"


def test_G_hop_dong_chi_mot_goc_vuong_KHONG_tinh_la_targeted_va_compiler_van_chay():
    p = json.loads(json.dumps(TR.DOC_DUNG_CA_AM["N04"]))
    p["geometric_relations"] = [q for q in p["geometric_relations"] if q["source_fact_id"] != "vh"]
    r = TR._mot_ca("N04", p)
    assert r["BUILD"]["COMPILE_STATUS"] == "COMPILED"            # hợp lệ ⇒ compiler chạy như trước
    assert r["TARGETED_REJECTION_V2"] == "NO" and r["SAFE_REJECTION"] is False


# ══ N01–N03 — overlay KHÔNG chạm ══════════════════════════════════════════
@pytest.mark.parametrize("cid", ["N01", "N02", "N03"])
@pytest.mark.parametrize("dau_vao", ["dung", "rong"])
def test_N01_N03_V2_trung_V1(cid, dau_vao):
    r = TR._mot_ca(cid, TR.DOC_DUNG_CA_AM[cid] if dau_vao == "dung" else "{}")
    assert r["TARGETED_REJECTION_V2"] == r["TARGETED_REJECTION_MATCH"]
    assert r["DATASET_ROLE"] == "DEVELOPMENT_HOLDOUT_PILOT"
    assert r["TARGETED_REJECTION_V2"] == ("YES" if dau_vao == "dung" else "NO")


def test_N01_lop_dinh_chinh_giu_nguyen():
    k = _TH().tong_hop(None)
    assert k["CASES"]["N01"]["HALLUCINATED_CRITICAL_FACT_COUNT"] == 1
    assert k["CASES"]["N01"]["CORRECTION_APPLIED"] is True


def test_nap_that_bai_thi_chay_mot_ca_FAIL_CLOSED_khong_lui_ve_v1(monkeypatch, tmp_path):
    monkeypatch.setattr(_TH(), "REGISTRY_V2_PATH", tmp_path / "khong_co.json")
    with pytest.raises(_TH().LoiRegistry) as e:
        TR._mot_ca("N04", TR.DOC_DUNG_CA_AM["N04"])
    assert e.value.ma == "REGISTRY_V2_MISSING"


def test_bo_tong_hop_ca_khong_bi_ghi_de_V2_trung_V1_ca_khi_ban_ghi_chi_mang_ket_qua_v1():
    moi = [TR._rec_am("N02"), TR._rec_am("N03"), TR._rec_am("N04")]
    k = _TH().tong_hop(moi)
    for cid in ("N01", "N02", "N03"):
        c = k["CASES"][cid]
        assert c["TARGETED_REJECTION_V2"] == c["TARGETED_REJECTION_MATCH"], cid
    assert k["CASES"]["N02"]["TARGETED_REJECTION_V2"] == "YES"
    # N04 bị ghi đè: bản ghi không mang tuple ⇒ KHÔNG đoán, cũng không mượn kết quả v1
    assert k["CASES"]["N04"]["TARGETED_REJECTION_V2"] == "NOT_MEASURED"


def test_bo_tong_hop_FAIL_CLOSED_khi_v2_hong_khong_cham_theo_v1(monkeypatch, tmp_path):
    TH = _TH()
    monkeypatch.setattr(TH, "REGISTRY_V2_PATH", tmp_path / "khong_co.json")
    k = TH.tong_hop(None)
    assert k["CLASSIFICATION"] == "MEASUREMENT_INVALID"
    assert "TARGETED_REGISTRY_V2_INVALID:REGISTRY_V2_MISSING" in k["MEASUREMENT_INVALID_REASONS"]
    assert k["TARGETED_REGISTRY"] is None
    assert k["METRICS"]["TARGETED_REJECTION_V2"]["YES"] == 0


# ══ RUNNER — RÀNG BUỘC TRƯỚC REQUEST ĐẦU TIÊN ═════════════════════════════
def test_runner_ghi_rang_buoc_registry_TRUOC_request_dau_va_request_khong_doi(tmp_path):
    thay_luc_dau: list[bool] = []
    bodies: list[bytes] = []

    def xu_ly(req, cid):
        if not thay_luc_dau:
            thay_luc_dau.append((tmp_path / "REGISTRY_BINDING.json").exists())
        bodies.append(req.content)
        return TR._tra_loi("{}")
    _, thay = TR._chay_main(tmp_path, xu_ly)
    assert thay_luc_dau == [True], "registry phải được nạp và ghi TRƯỚC request đầu tiên"
    assert thay == TR.CON_LAI and len(bodies) == 6
    rb = TR._doc(tmp_path, "REGISTRY_BINDING.json")
    assert rb["VERSION"] == "negative-targeted-rejection/2"
    assert rb["BASE_REGISTRY_SHA256"] == SHA_V1 and rb["OVERLAY_SHA256"] == SHA_V2
    assert rb["DATASET_ROLES"]["N04"] == "DEVELOPMENT_REGRESSION_CASE"
    assert rb["PRODUCT_BEHAVIOR_HEAD"].startswith("cac49a0") and rb["LOADED_BEFORE_FIRST_REQUEST"] is True
    assert rb["EVIDENCE_CLASS"] == "MIXED_DEVELOPMENT_EVIDENCE"
    ky = {e["case_id"]: e["body_sha256"] for e in TR._doc(TR.REGD, "EXPECTED_REQUEST_HASHES.json")["EXPECTED"]}
    qs = TR._doc(tmp_path, "REQUEST_OBSERVATIONS.json")["OBSERVATIONS"]
    assert [q["case_id"] for q in qs] == TR.CON_LAI
    assert all(q["body_sha256"] == ky[q["case_id"]] for q in qs)
    assert TR._doc(tmp_path, "REQUEST_BUDGET_PROOF.json")["MAX_HTTP_REQUESTS"] == 6
    for b in bodies:                                                   # registry không lọt vào request
        assert b"negative-targeted-rejection" not in b and b"STRUCTURED_RELATION_CONTRADICTION" not in b
    kq = TR._doc(tmp_path, "COMPLETION_CASE_RESULTS_REDACTED.json")
    assert kq["TARGETED_REGISTRY"]["OVERLAY_SHA256"] == SHA_V2


@pytest.mark.parametrize("ca", ["v2_chua_commit", "v2_sua_do_trong_kho", "v2_vang_mat", "N04_holdout",
                                "san_pham_troi"])
def test_runner_CHAN_truoc_request_khi_rang_buoc_hong(tmp_path, monkeypatch, ca):
    TH = _TH()
    if ca == "v2_chua_commit":
        monkeypatch.setattr(TH, "REGISTRY_V2_PATH", _ghi_overlay(tmp_path, lambda d: None))
        ma = "REGISTRY_V2_NOT_COMMITTED"
    elif ca == "v2_sua_do_trong_kho":           # overlay THẬT trong kho nhưng lệch HEAD (không sửa tệp thật)
        that = TH._git
        monkeypatch.setattr(TH, "_git", lambda *a: subprocess.CompletedProcess(a, 1, "", "")
                            if a[0] == "diff" else that(*a))
        ma = "REGISTRY_V2_NOT_COMMITTED"
    elif ca == "v2_vang_mat":
        monkeypatch.setattr(TH, "REGISTRY_V2_PATH", tmp_path / "khong_co.json")
        ma = "REGISTRY_V2_MISSING"
    elif ca == "N04_holdout":
        monkeypatch.setattr(TH, "REGISTRY_V2_PATH", _ghi_overlay(
            tmp_path, lambda d: d["overrides"]["N04"].update(dataset_role="DEVELOPMENT_HOLDOUT_PILOT")))
        ma = "DATASET_ROLE_INVALID"
    else:
        import freeze_evaluation_candidate as F
        monkeypatch.setattr(F, "measured_system_hash", lambda: ("0" * 64, 103))
        ma = "PRODUCT_CANDIDATE_DRIFT"
    ra = tmp_path / "ra"
    ma_ra, thay = TR._chay_main(ra, lambda req, cid: TR._tra_loi("{}"))
    assert thay == [], f"{ca}: đã gửi request dù ràng buộc registry hỏng"
    assert ma_ra == B.EXIT_PRECHECK
    assert TR._doc(ra, "PRECHECK_REGISTRY_BINDING.json")["RESULT"] == ma


# ══ PHÂN LOẠI BENCHMARK CHÍNH KHÔNG ĐỔI ═══════════════════════════════════
def test_phan_loai_chinh_KHONG_doi_chi_truong_targeted_N04_doi():
    TH = _TH()
    moi = [TR._rec_duong("P06"), TR._rec_duong("P07"), TR._rec_duong("P08"),
           TR._rec_am("N02"), TR._rec_am("N03"), TR._rec_am("N04")]
    co_v2 = [dict(r, TARGETED_REJECTION_V2=r.get("TARGETED_REJECTION_MATCH")) if r["KIND"] == "negative" else r
             for r in moi]
    a, b = TH.tong_hop(moi), TH.tong_hop(co_v2)
    assert a["CLASSIFICATION"] == b["CLASSIFICATION"] == "NOT_READY"         # trần hiện tại
    bo = lambda m: {k: v for k, v in m.items() if not k.startswith("TARGETED")}  # noqa: E731
    assert bo(a["METRICS"]) == bo(b["METRICS"])
    assert a["METRICS"]["REPEATED_FAILURE_CLUSTERS"] == ["MODEL_MALFORMED_RELATION"]
    assert a["CLUSTERS"]["MODEL_MALFORMED_RELATION"] == ["P03", "P05"]
    assert a["EVIDENCE_CLASS"] == "MIXED_DEVELOPMENT_EVIDENCE" and a["UNTOUCHED_HOLDOUT_CLAIM"] is False
    assert a["CASES"]["N04"]["DATASET_ROLE"] == "DEVELOPMENT_REGRESSION_CASE"
    n04 = b["CASES"]["N04"]
    assert "ORIGINAL_PREREPAIR_EXPECTATION_RESULT" in n04 and "POST_REPAIR_REGRESSION_EXPECTATION_RESULT" in n04
