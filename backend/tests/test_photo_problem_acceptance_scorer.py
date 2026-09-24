# -*- coding: utf-8 -*-
"""BỘ CHẤM NGHIỆM THU ẢNH ĐỀ BÀI — test phản chứng cho bốn lỗ đã khai. 0 request mạng.

`PHOTO_PROBLEM_ACCEPTANCE_SCORER_CORRECTION` §2–§5. Tệp này viết TRƯỚC bản sửa và chạy
trên runner ở `684420d` để lưu kết quả "trước". Mọi test đi qua giao diện đã có ở
`684420d` khi có thể (`cham_doc_anh`, `main` + transport tiêm), để kết quả "trước" là
HÀNH VI chứ không phải một lỗi import.

Bốn câu hỏi, kiểm riêng:
  S1  `z = 3` có lọt khi đọc ra `z = 30` không?
  S2  quan hệ không được đề xác nhận nhưng dùng toàn nhãn thật có lọt không?
  S3  C03 có nhận một mã từ chối ngoài danh sách đăng ký không?
  S4  lỗi provider / timeout / lược đồ có bị tính là từ chối an toàn không? (GIẢ THUYẾT)
và cổng duyệt thủ công (§5).

⚠️ Không test nào ở đây chứng minh Gemini đọc đúng ảnh thật.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from PIL import Image

from app.ai import gemini
from app.ingestion import image_extraction as ie

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import replay_negative_boundaries as RNB  # noqa: E402
import run_photo_problem_live as R  # noqa: E402

CA_P1 = "p1_chop_thiet_dien_khoang_cach"
CA_P6 = "p6_thiet_dien_elip_cua_hinh_tru"
KHOA_GIA = "AIzaSyFAKE-SECRET-0123456789abcdef"
ENV_LIVE = {"ALLOW_LIVE_AI": "1", "GEMINI_API_KEY": KHOA_GIA}
TRU = "−"
KHONG_RO = "UNKNOWN_PENDING_HUMAN_REVIEW"


@pytest.fixture(autouse=True)
def _khong_cho_backoff(monkeypatch):
    monkeypatch.setattr(gemini, "BACKOFF_BASE_SECONDS", 0.0)


def _ban_ghi(text="", diem=(), cong_thuc=(), khoi=(), quan_he=(), co_hinh=False, chuan_hoa=None,
             tin_cay=0.95) -> str:
    return json.dumps({
        "problem_text_verbatim": text,
        "problem_text_normalized": text if chuan_hoa is None else chuan_hoa,
        "math_expressions": [{"verbatim": f, "normalized": f} for f in cong_thuc],
        "named_points": list(diem), "named_lines": [], "named_planes": [], "named_solids": list(khoi),
        "given_relations": list(quan_he), "has_diagram": co_hinh,
        "diagram_observations": ["Chỉ có hình vẽ."] if co_hinh else [],
        "text_diagram_conflicts": [], "uncertain_tokens": [], "missing_regions": [], "confidence": tin_cay,
    }, ensure_ascii=False)


def _cham(de: str, cf: dict, doc: str, **ban_ghi) -> dict:
    """`cham_doc_anh` trên một ground truth tối thiểu — giao diện có sẵn ở `684420d`."""
    day_du = {"point_labels": [], "formulas": [], "objects": [], "relations": [], "request": "", **cf}
    x = ie.parse_extraction(_ban_ghi(doc, **ban_ghi))
    return R.cham_doc_anh("C01", {"expected_text": de, "critical_facts": day_du}, x, doc)


# ══ S1 · KHỚP DỮ KIỆN: biểu thức HOÀN CHỈNH, không phải chuỗi con ═══════════
DE_Z = "Cho mặt phẳng (P): z = 3 và điểm A."


@pytest.mark.parametrize("doc_ra, khop", [
    ("z=3", True),
    ("z = 30", False),
    ("z = -3", False),
    ("z = 3.1", False),
    ("z = 3 + x", False),
], ids=["z=3_khop", "z=30", "z=-3", "z=3.1", "z=3+x"])
def test_S1a_cong_thuc_khop_BIEU_THUC_HOAN_CHINH(doc_ra, khop):
    doc = DE_Z.replace("z = 3", doc_ra)
    k = _cham(DE_Z, {"point_labels": ["A"], "formulas": ["z = 3"]}, doc, diem=["A"], cong_thuc=[doc_ra])
    assert k["FORMULA_ACCURACY"] == (1.0 if khop else 0.0), k["details"]
    assert any("FORMULA_ACCURACY" in x for x in k["fail_reasons"]) is (not khop)


def test_S1b_truong_cau_truc_KHONG_che_duoc_van_ban_sai():
    """Tầng B chỉ nhận VĂN BẢN. `math_expressions` khai `z = 3` mà văn bản ghi `z = 30` là đọc SAI."""
    doc = DE_Z.replace("z = 3", "z = 30")
    k = _cham(DE_Z, {"point_labels": ["A"], "formulas": ["z = 3"]}, doc, diem=["A"], cong_thuc=["z = 3"])
    assert k["FORMULA_ACCURACY"] == 0.0, k["details"]


@pytest.mark.parametrize("nhan_doc, doc, khop", [
    (["A"], "Cho mặt phẳng (P): z = 3 và điểm A.", True),
    (["A1"], "Cho mặt phẳng (P): z = 3 và điểm A1.", False),
    (["A"], "Cho mặt phẳng (P): z = 3 và điểm A1.", False),
    (["A′"], "Cho mặt phẳng (P): z = 3 và điểm A′.", False),
    (["A"], "Cho mặt phẳng (P): z = 3 và điểm A′.", False),
], ids=["A_khop", "A1_ca_hai", "A1_chi_van_ban", "A'_ca_hai", "A'_chi_van_ban"])
def test_S1c_nhan_diem_GIU_chi_so_va_dau_phay_tren(nhan_doc, doc, khop):
    k = _cham(DE_Z, {"point_labels": ["A"], "formulas": ["z = 3"]}, doc, diem=nhan_doc, cong_thuc=["z = 3"])
    assert k["POINT_LABEL_ACCURACY"] == (1.0 if khop else 0.0), k["details"]


@pytest.mark.parametrize("de, gt, doc_ra", [
    ("Cho tứ diện SABC có AB ⊥ SC.", "AB ⊥ SC", "AB ∥ SC"),
    ("Cho tứ diện SABC có A ∈ (SBC).", "A ∈ (SBC)", "A ∉ (SBC)"),
], ids=["vuong_goc_thanh_song_song", "thuoc_thanh_khong_thuoc"])
def test_S1d_quan_he_DOI_TOAN_TU_khong_khop_va_la_MAU_THUAN(de, gt, doc_ra):
    doc = de.replace(gt, doc_ra)
    k = _cham(de, {"point_labels": ["A"], "relations": [gt]}, doc, diem=["A"], quan_he=[doc_ra])
    assert k["RELATION_ACCURACY"] == 0.0, k["details"]
    dung = _cham(de, {"point_labels": ["A"], "relations": [gt]}, de, diem=["A"], quan_he=[gt])
    assert dung["RELATION_ACCURACY"] == 1.0 and dung["fail_reasons"] == [], dung  # cửa sổ chứng
    # Cùng toán hạng, khác đúng MỘT toán tử quan hệ so với nguồn ⇒ mâu thuẫn rõ, không phải "chưa rõ".
    assert k["details"]["relations_hallucinated"] == [doc_ra], k["details"]


def test_S1e_khoang_trang_va_ky_hieu_tuong_duong_DA_KHAI():
    de = f"Cho mặt phẳng (α): 2x {TRU} z + 12 = 0 và điểm A₁."
    doc = "Cho mặt phẳng (α): 2x-z+12=0 và điểm A1."
    k = _cham(de, {"point_labels": ["A₁"], "formulas": [f"2x {TRU} z + 12 = 0"]}, doc,
              diem=["A1"], cong_thuc=["2x-z+12=0"])
    assert (k["FORMULA_ACCURACY"], k["POINT_LABEL_ACCURACY"]) == (1.0, 1.0), k["details"]


def test_S1f_ky_hieu_NGOAI_pham_vi_la_UNVERIFIABLE_khong_dung_khong_sai():
    de = "Cho tam giác đều ABC cạnh a√3."
    k = _cham(de, {"point_labels": ["A"], "formulas": ["a√3"]}, de, diem=["A"], cong_thuc=["a√3"])
    assert k["FORMULA_ACCURACY"] is None, k
    assert k["UNVERIFIABLE_FACTS"] == 1 and not any("FORMULA_ACCURACY" in x for x in k["fail_reasons"])
    assert {"group": "formulas", "item": "a√3", "status": "UNVERIFIABLE_AUTOMATICALLY"}.items() <= \
        k["review_items"][0].items()


def test_S1g_van_ban_nguyen_van_va_chuan_hoa_DEU_phai_dung():
    """`problem_text` đi xuống tầng B là bản chuẩn hoá; CER khoá trên bản nguyên văn."""
    doc_sai = DE_Z.replace("z = 3", "z = 30")
    k = _cham(DE_Z, {"point_labels": ["A"], "formulas": ["z = 3"]}, DE_Z, diem=["A"], cong_thuc=["z = 3"],
              chuan_hoa=doc_sai)
    assert k["FORMULA_ACCURACY"] == 0.0, k["details"]


def test_S1h_CER_thap_KHONG_che_sai_quan_he():
    de = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông và SA ⊥ BD."
    doc = de.replace("⊥", "∥")
    k = _cham(de, {"point_labels": ["S", "A"], "relations": ["SA ⊥ BD"]}, doc, diem=["S", "A"],
              quan_he=["SA ∥ BD"])
    assert k["RAW_TEXT_CER"] < R.NGUONG_CER["C01"] and k["RELATION_ACCURACY"] == 0.0
    assert k["fail_reasons"], k


# ══ S2 · MỤC THÊM NGOÀI DANH SÁCH KỲ VỌNG ═════════════════════════════════
DE_CHOP = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông."


def test_S2a_quan_he_dung_TOAN_NHAN_THAT_nhung_de_KHONG_xac_nhan_thi_CAN_NGUOI_XEM():
    k = _cham(DE_CHOP, {"point_labels": ["S", "A"]}, DE_CHOP, diem=["S", "A"], quan_he=["SA ⊥ BD"])
    d = k["details"]
    assert d["relations_unverified"] == ["SA ⊥ BD"], d
    assert d["relations_hallucinated"] == [] and d["relations_confirmed"] == []
    assert k["UNVERIFIED_EXTRA_FACTS"] == 1
    # Chưa xác minh KHÔNG được làm căn cứ báo 0 ảo giác.
    assert k["SILENT_HALLUCINATION_COUNT"] == KHONG_RO
    assert any(i["item"] == "SA ⊥ BD" and i["status"] == "UNVERIFIED" for i in k["review_items"])


def test_S2b_nguon_xac_nhan_la_GROUND_TRUTH_khong_phai_van_ban_cua_CHINH_model():
    doc = DE_CHOP + " Biết SA ⊥ BD."
    k = _cham(DE_CHOP, {"point_labels": ["S", "A"]}, doc, diem=["S", "A"], quan_he=["SA ⊥ BD"])
    assert k["details"]["relations_unverified"] == ["SA ⊥ BD"], k["details"]
    assert k["details"]["relations_confirmed"] == []


def test_S2c_muc_them_DUNG_theo_de_duoc_xac_nhan_khong_bi_danh_la_ao_giac():
    k = _cham(DE_CHOP, {"point_labels": ["S", "A"]}, DE_CHOP, diem=["S", "A", "B"],
              quan_he=["ABCD là hình vuông"], khoi=["S.ABCD"])
    d = k["details"]
    assert (d["relations_confirmed"], d["objects_confirmed"], d["point_labels_confirmed"]) == (
        ["ABCD là hình vuông"], ["S.ABCD"], ["B"]), d
    assert (k["HALLUCINATED_CRITICAL_FACTS"], k["UNVERIFIED_EXTRA_FACTS"]) == (0, 0)
    assert k["SILENT_HALLUCINATION_COUNT"] == 0 and k["fail_reasons"] == []


def test_S2d_muc_them_mang_so_KHONG_co_trong_de_la_MAU_THUAN():
    k = _cham(DE_CHOP, {"point_labels": ["S", "A"]}, DE_CHOP, diem=["S", "A"], quan_he=["SA = 7"])
    assert k["details"]["relations_hallucinated"] == ["SA = 7"] and k["HALLUCINATED_CRITICAL_FACTS"] == 1
    assert any("HALLUCINATED_CRITICAL_FACTS" in x for x in k["fail_reasons"])


# ══ NỀN CHO LƯỢT RUNNER ĐẦY ĐỦ ════════════════════════════════════════════
@pytest.fixture(scope="module")
def de() -> dict[str, str]:
    d = RNB.doc_de_bai()
    return {"C01": d[CA_P1], "C02": d[CA_P6]}


def _gt(de: dict[str, str], ma_c03=("MISSING_PROBLEM_TEXT",)) -> dict:
    c03 = {"case_id": "C03", "expected_outcome": "SAFE_REJECTION"}
    if ma_c03 is not None:
        c03["expected_rejection_codes"] = list(ma_c03)
    return {"cases": [
        {"case_id": "C01", "expected_text": de["C01"], "critical_facts": {
            "point_labels": ["S", "A", "B", "C", "D"], "formulas": ["z = 3"], "objects": ["S.ABCD"],
            "relations": [["ABCD là hình vuông", "đáy ABCD là hình vuông"]],
            "request": "khoảng cách từ điểm S đến đường thẳng BD"}},
        {"case_id": "C02", "expected_text": de["C02"], "critical_facts": {
            "point_labels": ["O", "K", "A"], "formulas": [f"2x {TRU} z + 12 = 0"], "objects": [],
            "relations": [], "request": "Tính diện tích hình elip (E)"}},
        c03,
    ]}


@pytest.fixture
def kho(tmp_path, de):
    anh = tmp_path / "anh"
    anh.mkdir()
    for cid, mau in (("C01", (250, 250, 250)), ("C02", (225, 235, 255)), ("C03", (255, 235, 225))):
        buf = io.BytesIO()
        Image.new("RGB", (96, 64), mau).save(buf, format="PNG")
        (anh / f"{cid}.png").write_bytes(buf.getvalue())
    gt = tmp_path / "GROUND_TRUTH.json"
    gt.write_text(json.dumps(_gt(de), ensure_ascii=False), encoding="utf-8")
    return SimpleNamespace(tmp=tmp_path, anh=anh, gt=gt, ra=tmp_path / "ra")


def _vision(de, cid) -> str:
    if cid == "C01":
        return _ban_ghi(de["C01"], "SABCD", ["z = 3"], ["S.ABCD"], ["ABCD là hình vuông"])
    if cid == "C02":
        return _ban_ghi(de["C02"], "OKA", [f"2x {TRU} z + 12 = 0"])
    return _ban_ghi(co_hinh=True)


def _kich_ban(de, thay: dict | None = None) -> dict:
    p1, p6 = RNB.doc_raw_theo_thu_tu(CA_P1), RNB.doc_raw_theo_thu_tu(CA_P6)
    kb = {
        ("C01", "vision"): [_vision(de, "C01")], ("C01", "analyze"): p1["semantic_analyze"],
        ("C01", "synthesis"): p1["semantic_program"],
        ("C02", "vision"): [_vision(de, "C02")], ("C02", "analyze"): p6["semantic_analyze"],
        ("C02", "synthesis"): p6["semantic_program"],
        ("C03", "vision"): [_vision(de, "C03")],
    }
    kb.update(thay or {})
    return kb


def _chay(kho, case, *them, kich_ban, env=ENV_LIVE, ra=None, argv=None):
    ra = ra or kho.ra
    giu: dict = {}

    def nha_may(cong):
        giu["prov"] = R.TransportKichBan(cong, kich_ban)
        return giu["prov"]

    out, err = io.StringIO(), io.StringIO()
    code = R.main(argv if argv is not None else ["--case", case, "--input-dir", str(kho.anh), "--ground-truth",
                                                 str(kho.gt), "--output-dir", str(ra), *them],
                  inner_transport_factory=nha_may, env=env, stdout=out, stderr=err)
    return SimpleNamespace(code=code, out=out.getvalue(), err=err.getvalue(), prov=giu.get("prov"), ra=ra)


def _json(r, ten: str) -> dict:
    return json.loads((r.ra / ten).read_text(encoding="utf-8"))


def _ca(tt: dict, cid: str) -> dict | None:
    return next((c for c in tt.get("cases", []) if c["case_id"] == cid), None)


# ══ S3 · C03 — MÃ TỪ CHỐI ĐĂNG KÝ TRƯỚC ═══════════════════════════════════
@pytest.mark.parametrize("ma", [None, [], ["NOT_A_REAL_CODE"], ["AMBIGUOUS_DIAGRAM"]],
                         ids=["thieu_truong", "rong", "khong_ton_tai", "co_thong_bao_nhung_khong_bao_gio_phat"])
def test_S3a_C03_phai_DANG_KY_TRUOC_ma_tu_choi_THAT_cua_san_pham(kho, de, ma):
    kho.gt.write_text(json.dumps(_gt(de, ma), ensure_ascii=False), encoding="utf-8")
    r = _chay(kho, "C03", kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_USAGE, (r.out, r.err)
    assert r.prov is None and not kho.ra.exists()


def test_S3b_ma_tu_choi_hop_le_doc_tu_CHINH_assess_extraction():
    ma = R.ma_tu_choi_san_pham()
    assert ma == {"IMAGE_NOT_READABLE", "MISSING_PROBLEM_TEXT", "UNSUPPORTED_PROBLEM"}
    assert ma < set(ie.REJECTION_MESSAGES), "REJECTION_MESSAGES có cả mã KHÔNG bao giờ được phát"


@pytest.mark.parametrize("doc, ma_that", [
    (_ban_ghi("Tính tổng các số nguyên dương từ 1 đến 100 bằng vòng lặp."), "UNSUPPORTED_PROBLEM"),
    (_ban_ghi(""), "IMAGE_NOT_READABLE"),
], ids=["UNSUPPORTED_PROBLEM", "IMAGE_NOT_READABLE"])
def test_S3c_C03_tu_choi_bang_ma_NGOAI_danh_sach_KHONG_dat(kho, de, doc, ma_that):
    r = _chay(kho, "C03", kich_ban=_kich_ban(de, {("C03", "vision"): [doc]}))
    c03 = _ca(_json(r, "RUN_SUMMARY.json"), "C03")
    assert c03["REJECTION_CODE"] == ma_that, c03  # sản phẩm THẬT SỰ đã từ chối…
    assert c03["C03_SAFE_REJECTION"] is False, c03  # …nhưng không bằng mã đã đăng ký
    assert r.code != R.EXIT_PASS


@pytest.mark.parametrize("ma_dang_ky", [["MISSING_PROBLEM_TEXT"], ["IMAGE_NOT_READABLE", "MISSING_PROBLEM_TEXT"]])
def test_S3d_C03_DAT_chi_khi_ma_that_TRONG_danh_sach_va_cong_HTTP_thay_0_request_tang_B(kho, de, ma_dang_ky):
    kho.gt.write_text(json.dumps(_gt(de, ma_dang_ky), ensure_ascii=False), encoding="utf-8")
    p1 = RNB.doc_raw_theo_thu_tu(CA_P1)
    # Kịch bản CÓ SẴN phản hồi tầng B cho C03 — gọi thì sẽ được phục vụ.
    r = _chay(kho, "C03", kich_ban=_kich_ban(de, {("C03", "analyze"): p1["semantic_analyze"],
                                                  ("C03", "synthesis"): p1["semantic_program"]}))
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    c03 = _ca(_json(r, "RUN_SUMMARY.json"), "C03")
    assert (c03["status"], c03["C03_SAFE_REJECTION"], c03["VISION_SCHEMA_VALID"]) == ("PASS", True, True)
    assert c03["EXPECTED_REJECTION_CODES"] == ma_dang_ky
    # Tầng B không được gọi: đo ở CỔNG HTTP, không phải lời khai của runner.
    assert c03["STAGE_B_HTTP_ATTEMPTS"] == 0 and r.prov.calls == [("C03", "vision")]
    assert not (r.ra / "C03_SCENE_RESULT.json").exists() and "scene_object_count" not in c03


# ══ S4 · LỖI PROVIDER / TIMEOUT / LƯỢC ĐỒ KHÔNG PHẢI TỪ CHỐI AN TOÀN ════════
LOI_C03 = {
    "http_401": (lambda: httpx.Response(401, text="unauthorized"), "ERROR"),
    "http_403": (lambda: httpx.Response(403, text="forbidden"), "ERROR"),
    "http_429": (lambda: httpx.Response(429, text="quota"), "ERROR"),
    "http_500": (lambda: httpx.Response(500, text="loi may chu"), "ERROR"),
    "http_503": (lambda: httpx.Response(503, text="qua tai"), "ERROR"),
    "timeout": (lambda: httpx.ReadTimeout("het gio"), "ERROR"),
    "loi_ket_noi": (lambda: httpx.ConnectError("khong ket noi duoc"), "ERROR"),
    "json_hong": (lambda: "day khong phai json", "FAIL"),
    "sai_luoc_do": (lambda: json.dumps({"foo": 1}), "FAIL"),
    "het_ngan_sach": (None, "BLOCKED"),
    "ngoai_le_chua_phan_loai": (None, "ERROR"),
}


def _chay_loi_c03(kho, de, kieu, monkeypatch):
    if kieu == "het_ngan_sach":  # C01 + C02 dùng đúng 6 ⇒ ảnh C03 bị chặn trước transport
        return _chay(kho, "all", "--max-http-requests", "6", kich_ban=_kich_ban(de))
    if kieu == "ngoai_le_chua_phan_loai":
        def no(_raw):
            raise RuntimeError("ngoai le chua phan loai")
        monkeypatch.setattr(ie, "parse_extraction", no)
        return _chay(kho, "C03", kich_ban=_kich_ban(de))
    return _chay(kho, "C03", kich_ban=_kich_ban(de, {("C03", "vision"): [LOI_C03[kieu][0]()]}))


@pytest.mark.parametrize("kieu", list(LOI_C03))
def test_S4a_loi_provider_KHONG_BAO_GIO_la_tu_choi_an_toan(kho, de, kieu, monkeypatch):
    r = _chay_loi_c03(kho, de, kieu, monkeypatch)
    tt = _json(r, "RUN_SUMMARY.json")
    c03 = _ca(tt, "C03")
    assert r.code != R.EXIT_PASS, (kieu, r.out, r.err)
    assert c03 is None or c03.get("C03_SAFE_REJECTION") is not True, c03
    assert tt["ACCEPTANCE"] != "PASS"


@pytest.mark.parametrize("kieu", list(LOI_C03))
def test_S4b_PASS_FAIL_ERROR_BLOCKED_duoc_PHAN_BIET(kho, de, kieu, monkeypatch):
    r = _chay_loi_c03(kho, de, kieu, monkeypatch)
    tt = _json(r, "RUN_SUMMARY.json")
    c03 = _ca(tt, "C03")
    mong = LOI_C03[kieu][1]
    assert c03 is not None and c03["status"] == mong, (kieu, c03, tt.get("RUNNER_ERROR"))
    assert tt["AUTOMATED_CHECKS"] == mong and c03["C03_SAFE_REJECTION"] is False


def test_S4c_loi_provider_o_TANG_B_la_ERROR_va_van_DUNG_luot(kho, de):
    r = _chay(kho, "all", kich_ban=_kich_ban(de, {("C01", "synthesis"): [httpx.Response(400, text="bad")]}))
    tt = _json(r, "RUN_SUMMARY.json")
    c01 = _ca(tt, "C01")
    assert (c01["status"], c01["result"], tt["AUTOMATED_CHECKS"]) == ("ERROR", "FAIL", "ERROR"), c01
    assert tt["cases_run"] == ["C01"] and r.code != R.EXIT_PASS


# ══ S5 · DUYỆT THỦ CÔNG BẮT BUỘC ══════════════════════════════════════════
def _sha_tep(p: Path) -> str:
    import hashlib

    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_S5a_luot_tu_dong_DAT_van_CHO_nguoi_duyet_va_goi_duyet_GAN_dung_luot(kho, de):
    r = _chay(kho, "C01", kich_ban=_kich_ban(de))
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    tt = _json(r, "RUN_SUMMARY.json")
    assert (tt["AUTOMATED_CHECKS"], tt["HUMAN_CRITICAL_FACT_REVIEW"], tt["REAL_PHOTO_ACCEPTANCE"]) == (
        "PASS", "PENDING", "NOT_RUN")
    assert tt["ACCEPTANCE"] == "PENDING_HUMAN_REVIEW"
    goi = _json(r, "HUMAN_REVIEW_PACKET.json")
    b = goi["binding"]
    assert b["run_id"] == tt["run_id"] and b["ground_truth_sha256"] == tt["GROUND_TRUTH_SHA256"]
    c = b["cases"][0]
    assert c["raw_extraction_sha256"] == _sha_tep(r.ra / "C01_RAW_EXTRACTION.json")
    assert c["confirmed_input_sha256"] == _sha_tep(r.ra / "C01_CONFIRMED_INPUT.json")
    assert c["image_sha256"] == _json(r, "C01_RAW_EXTRACTION.json")["image"]["IMAGE_SHA256"]
    mau = goi["review_template"]
    assert (mau["decision"], mau["reviewer"], mau["reviewed_at"]) == ("PENDING", "", "")


def test_S5b_goi_duyet_liet_ke_thu_nguoi_duyet_PHAI_xem_va_muc_chua_ro_KHONG_dung_luot(kho, de):
    them = _ban_ghi(de["C01"], "SABCD", ["z = 3"], ["S.ABCD"], ["ABCD là hình vuông", "SA ⊥ BD"])
    p = kho.tmp / "xac_nhan.json"
    p.write_text(json.dumps({"C01": de["C01"].replace("Oxyz, cho", "Oxyz cho")}, ensure_ascii=False),
                 encoding="utf-8")
    r = _chay(kho, "all", "--confirmed-text", str(p), kich_ban=_kich_ban(de, {("C01", "vision"): [them]}))
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    tt = _json(r, "RUN_SUMMARY.json")
    assert tt["cases_run"] == ["C01", "C02", "C03"] and tt["ACCEPTANCE"] == "PENDING_HUMAN_REVIEW"
    c01 = next(c for c in _json(r, "HUMAN_REVIEW_PACKET.json")["cases"] if c["case_id"] == "C01")
    assert [i["item"] for i in c01["extra_facts_unverified"]] == ["SA ⊥ BD"]
    assert c01["facts_missing_or_misread"] == []
    assert c01["model_vs_confirmed_text"]["EDITED"] is True and c01["model_vs_confirmed_text"]["diff"]
    assert c01["scene"]["scene_object_count"] > 0


def _ban_duyet(r, tmp: Path, ten="review.json", **thay) -> Path:
    mau = _json(r, "HUMAN_REVIEW_PACKET.json")["review_template"]
    ban = {**mau, "review_kind": "SIMULATED_REVIEW", "reviewer": "TEST_FIXTURE",
           "reviewed_at": "2026-09-14T00:00:00+00:00", "decision": "PASS", "notes": "kiểm cơ chế",
           "cases": [{**c, "decision": "PASS"} for c in mau["cases"]]}
    for k, v in thay.items():
        if k.startswith("case_"):
            ban["cases"][0][k[5:]] = v
        else:
            ban[k] = v
    p = tmp / ten
    p.write_text(json.dumps(ban, ensure_ascii=False), encoding="utf-8")
    return p


def _kiem_duyet(r, p: Path | None = None) -> tuple[int, dict]:
    argv = ["--verify-review", "--run-dir", str(r.ra)] + (["--human-review", str(p)] if p else [])
    out, err = io.StringIO(), io.StringIO()
    code = R.main(argv, env={}, stdout=out, stderr=err)
    try:
        return code, json.loads(out.getvalue())
    except ValueError:
        return code, {"_stdout": out.getvalue(), "_stderr": err.getvalue()}


def test_S5c_khong_co_ban_duyet_thi_PENDING(kho, de):
    r = _chay(kho, "C01", kich_ban=_kich_ban(de))
    code, kq = _kiem_duyet(r)
    assert kq.get("HUMAN_CRITICAL_FACT_REVIEW") == "PENDING", kq
    assert code != R.EXIT_PASS


def test_S5d_ban_duyet_GIA_hop_le_KHONG_BAO_GIO_thanh_PASS(kho, de):
    r = _chay(kho, "C01", kich_ban=_kich_ban(de))
    code, kq = _kiem_duyet(r, _ban_duyet(r, kho.tmp))
    assert (kq.get("BINDING_VALID"), kq.get("HUMAN_CRITICAL_FACT_REVIEW"), kq.get("REAL_PHOTO_ACCEPTANCE")) == (
        True, "SIMULATED_REVIEW", "NOT_RUN"), kq
    assert code != R.EXIT_PASS


@pytest.mark.parametrize("thay", [
    {"run_id": "luot-khac"},
    {"ground_truth_sha256": "0" * 64},
    {"case_image_sha256": "1" * 64},
    {"case_raw_extraction_sha256": "2" * 64},
    {"case_confirmed_input_sha256": "3" * 64},
], ids=["run_id", "ground_truth", "anh", "dau_ra_model", "ban_xac_nhan"])
def test_S5e_ban_duyet_CU_bi_tu_choi_khi_rang_buoc_lech(kho, de, thay):
    r = _chay(kho, "C01", kich_ban=_kich_ban(de))
    code, kq = _kiem_duyet(r, _ban_duyet(r, kho.tmp, **thay))
    assert kq.get("HUMAN_CRITICAL_FACT_REVIEW") == "STALE_REVIEW", kq
    assert code != R.EXIT_PASS


def test_S5f_dau_ra_model_DOI_SAU_khi_duyet_thi_ban_duyet_het_hieu_luc(kho, de):
    r = _chay(kho, "C01", kich_ban=_kich_ban(de))
    p = _ban_duyet(r, kho.tmp)
    assert _kiem_duyet(r, p)[1].get("BINDING_VALID") is True  # cửa sổ chứng
    tep = r.ra / "C01_RAW_EXTRACTION.json"
    tep.write_text(tep.read_text(encoding="utf-8").replace("S.ABCD", "S.ABCE", 1), encoding="utf-8")
    code, kq = _kiem_duyet(r, p)
    assert kq.get("HUMAN_CRITICAL_FACT_REVIEW") == "STALE_REVIEW", kq


@pytest.mark.parametrize("thay", [
    {"review_kind": "HUMAN"},
    {"reviewer": ""},
    {"reviewed_at": "hôm qua"},
    {"decision": "OK"},
    {"cases": []},
], ids=["nguoi_that_cho_luot_khong_phai_provider_that", "thieu_nguoi_duyet", "thoi_diem_sai", "quyet_dinh_la",
        "thieu_ca"])
def test_S5g_ban_duyet_SAI_KHUON_la_INVALID(kho, de, thay):
    r = _chay(kho, "C01", kich_ban=_kich_ban(de))
    code, kq = _kiem_duyet(r, _ban_duyet(r, kho.tmp, **thay))
    assert kq.get("HUMAN_CRITICAL_FACT_REVIEW") == "INVALID_REVIEW", kq
    assert code != R.EXIT_PASS


def test_S5h_REAL_PHOTO_ACCEPTANCE_chi_PASS_khi_DU_ba_dieu_kien():
    rang_buoc = {"run_id": "R1", "ground_truth_sha256": "g", "cases": [
        {"case_id": "C01", "image_sha256": "i", "raw_extraction_sha256": "x", "confirmed_input_sha256": "c"}]}
    tom_tat = {"run_id": "R1", "run_mode": "REAL_PROVIDER", "REAL_PROVIDER_EVIDENCE": "ESTABLISHED",
               "AUTOMATED_CHECKS": "PASS", "GROUND_TRUTH_SHA256": "g"}
    ban = {**{k: v for k, v in rang_buoc.items() if k != "cases"}, "review_kind": "HUMAN",
           "reviewer": "TEST_FIXTURE_NOT_A_HUMAN", "reviewed_at": "2026-09-14T00:00:00+00:00",
           "decision": "PASS", "notes": "", "cases": [{**rang_buoc["cases"][0], "decision": "PASS", "notes": ""}]}

    def xet(**thay_tom_tat):
        return R.phan_quyet_duyet({**tom_tat, **thay_tom_tat}, rang_buoc, ban)

    assert (xet()["HUMAN_CRITICAL_FACT_REVIEW"], xet()["REAL_PHOTO_ACCEPTANCE"]) == ("PASS", "PASS")
    assert xet(AUTOMATED_CHECKS="FAIL")["REAL_PHOTO_ACCEPTANCE"] == "FAIL"
    assert xet(REAL_PROVIDER_EVIDENCE="NOT_ESTABLISHED")["REAL_PHOTO_ACCEPTANCE"] != "PASS"
    ban["decision"] = "FAIL"
    assert (xet()["HUMAN_CRITICAL_FACT_REVIEW"], xet()["REAL_PHOTO_ACCEPTANCE"]) == ("FAIL", "FAIL")
