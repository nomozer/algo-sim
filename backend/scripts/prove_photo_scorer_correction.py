# -*- coding: utf-8 -*-
"""BẰNG CHỨNG TRƯỚC/SAU cho bộ chấm nghiệm thu ảnh đề bài — 0 request mạng, 0 quota.

`PHOTO_PROBLEM_ACCEPTANCE_SCORER_CORRECTION` §6. "Trước" không phải trí nhớ: script nạp
runner ở `684420d` thẳng từ blob git (`git show`) thành một module riêng, rồi đưa CÙNG
một đầu vào qua cả hai runner. Mọi lượt chạy runner dùng provider giả ở ranh giới HTTP
bên trong `ChanMangThat`.

    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/prove_photo_scorer_correction.py \
      --before-junit <tuyệt đối> --after-junit <tuyệt đối> --after-old-junit <tuyệt đối>

Sinh dưới `docs/evaluation/geometry/photo-problem-to-scene/acceptance-scorer-correction/`:
`BEFORE_AFTER_TESTS.json` · `FACT_MATCHING_PROOF.json` · `C03_REJECTION_PROOF.json` ·
`HUMAN_REVIEW_GATE_PROOF.json`. Từ chối ghi đè.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

BE = Path(__file__).resolve().parents[1]
for _p in (str(BE), str(BE / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import httpx  # noqa: E402
from PIL import Image  # noqa: E402

from app.ingestion import image_extraction as ie  # noqa: E402

import replay_negative_boundaries as RNB  # noqa: E402
import run_photo_problem_live as SAU  # noqa: E402

GOC = BE.parent
RA = GOC / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene" / "acceptance-scorer-correction"
MOC_TRUOC = "684420d"
DUONG_RUNNER = "backend/scripts/run_photo_problem_live.py"
TEP_TEST = "tests/test_photo_problem_acceptance_scorer.py"
CA_P1, CA_P6 = "p1_chop_thiet_dien_khoang_cach", "p6_thiet_dien_elip_cua_hinh_tru"
ENV_GIA = {"ALLOW_LIVE_AI": "1", "GEMINI_API_KEY": "AIzaSyFAKE-SECRET-0123456789abcdef"}
TRU = "−"
VANG = "KEY_ABSENT"
TEN_RA = ("BEFORE_AFTER_TESTS.json", "FACT_MATCHING_PROOF.json", "C03_REJECTION_PROOF.json",
          "HUMAN_REVIEW_GATE_PROOF.json")


def _sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8") if isinstance(b, str) else b).hexdigest()


def _git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=GOC, capture_output=True, text=True, encoding="utf-8",
                          check=True).stdout


def nap_runner_truoc(thu_muc: Path) -> tuple[Any, str]:
    """Runner ở `684420d`, nạp từ blob git — không từ bản sao ai đó có thể đã sửa."""
    nguon = subprocess.run(["git", "show", f"{MOC_TRUOC}:{DUONG_RUNNER}"], cwd=GOC, capture_output=True,
                           check=True).stdout
    p = thu_muc / "run_photo_problem_live_684420d.py"
    p.write_bytes(nguon)
    spec = importlib.util.spec_from_file_location("run_photo_problem_live_684420d", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # `@dataclass` tra module của lớp trong `sys.modules`
    spec.loader.exec_module(mod)
    return mod, _sha(nguon.replace(b"\r\n", b"\n"))


RUNNER_SHA = {}


def _dau(ten: str) -> dict:
    return {
        "wave": "PHOTO_PROBLEM_ACCEPTANCE_SCORER_CORRECTION",
        "artifact": ten,
        "generated_by": "backend/scripts/prove_photo_scorer_correction.py",
        "git_head": _git("rev-parse", "HEAD").strip(),
        "MEASURING_CODE_DIRTY_VS_GIT_HEAD": [d for d in _git("status", "--porcelain", "--", "backend/scripts",
                                                             "backend/tests").splitlines() if d],
        "runner_sha256": RUNNER_SHA,
        "evidence_class": "OFFLINE_TEST",
        "REAL_PROVIDER_CALLS": 0,
        "REAL_PROVIDER_EVIDENCE": "NOT_ESTABLISHED",
        "HUMAN_CRITICAL_FACT_REVIEW": "PENDING",
        "REAL_PHOTO_ACCEPTANCE": "NOT_RUN",
    }


def _phan_xu(mong: Any, truoc: Any, sau: Any) -> str:
    if sau != mong:
        return "NOT_FIXED"
    return "GUARD_ALREADY_PRESENT" if truoc == mong else "FIXED"


# ══════════════════════════════════════════════════════════════════════════
# 1 · TEST TRƯỚC / SAU — đọc JUnit XML của CÙNG một tệp test chạy trên hai runner
# ══════════════════════════════════════════════════════════════════════════
def _doc_junit(p: Path) -> dict[str, dict]:
    ra = {}
    for tc in ET.parse(p).getroot().iter("testcase"):
        loi = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
        if loi is None:
            ket = "skipped" if tc.find("skipped") is not None else "passed"
        else:
            ket = "failed" if loi.tag == "failure" else "error"
        thong_diep = None if loi is None else ((loi.get("message") or "").splitlines() or [""])[0][:300]
        ra[tc.get("name")] = {"outcome": ket, "message": thong_diep}
    return ra


THAY_DOI_TEST_CU = [
    {"file": "backend/tests/test_photo_problem_live_runner.py", "test": "_gt (fixture đầu vào)",
     "before": '{"case_id": "C03", "expected_outcome": "SAFE_REJECTION"}',
     "after": '{"case_id": "C03", "expected_outcome": "SAFE_REJECTION", "expected_rejection_codes": ["MISSING_PROBLEM_TEXT"]}',
     "reason": "trường bắt buộc mới của §4; đầu vào đổi theo lược đồ, không assertion nào dựa vào nó đổi đáp án"},
    *[{"file": "backend/tests/test_photo_problem_live_runner.py", "test": t,
       "before": 'tt["ACCEPTANCE"] == "PASS"',
       "after": 'tt["AUTOMATED_CHECKS"] == "PASS" và tt["ACCEPTANCE"] == "PENDING_HUMAN_REVIEW"',
       "reason": "đáp án cũ CHÍNH LÀ lỗi §5 — nghiệm thu đạt khi chưa có người duyệt; đáp án mới chặt hơn, "
                 "không lỏng hơn"}
      for t in ("test_01_case_C01_CHI_chay_C01", "test_02_case_all_chay_TUAN_TU_C01_C02_C03",
                "test_07_dry_run_KHONG_cham_mang")],
]


def bang_chung_test(truoc: Path, sau: Path, sau_cu: Path) -> dict:
    t, s, c = _doc_junit(truoc), _doc_junit(sau), _doc_junit(sau_cu)
    dong = []
    for ten in sorted(set(t) | set(s)):
        a, b = t.get(ten, {"outcome": "absent"}), s.get(ten, {"outcome": "absent"})
        dong.append({
            "test_name": f"{TEP_TEST}::{ten}",
            "input": "xem thân test — cùng một tệp test, hai runner",
            "expected": "passed",
            "actual_before": a["outcome"], "before_message": a.get("message"),
            "actual_after": b["outcome"], "after_message": b.get("message"),
            "classification": ("FIXED" if a["outcome"] != "passed" and b["outcome"] == "passed" else
                               "GUARD_ALREADY_PRESENT" if a["outcome"] == b["outcome"] == "passed" else
                               "REGRESSION" if a["outcome"] == "passed" else "STILL_FAILING"),
            "runner_sha256": RUNNER_SHA,
            "evidence_class": "OFFLINE_TEST",
        })

    def dem(d: dict) -> dict:
        return {k: sum(1 for v in d.values() if v["outcome"] == k) for k in ("passed", "failed", "error", "skipped")}

    phan_loai = {k: sum(1 for x in dong if x["classification"] == k)
                 for k in ("FIXED", "GUARD_ALREADY_PRESENT", "REGRESSION", "STILL_FAILING")}
    return {
        "method": (f"{TEP_TEST} viết TRƯỚC bản sửa. Lượt 'trước' chạy khi runner trong cây làm việc trùng "
                   f"blob {MOC_TRUOC} (git hash-object = git rev-parse {MOC_TRUOC}:{DUONG_RUNNER}); lượt 'sau' "
                   "chạy trên runner đã sửa. Hai JUnit XML là nguồn của bảng này."),
        "BEFORE_COUNTS": dem(t),
        "AFTER_COUNTS": dem(s),
        "CLASSIFICATION_COUNTS": phan_loai,
        "OLD_RUNNER_TEST_FILE_AFTER": {"file": "backend/tests/test_photo_problem_live_runner.py", **dem(c)},
        "OLD_TEST_CHANGES": THAY_DOI_TEST_CU,
        "tests": dong,
        "PROOF": "PASS" if phan_loai["REGRESSION"] == phan_loai["STILL_FAILING"] == 0 and dem(c)["failed"] == 0
        and dem(c)["error"] == 0 else "FAIL",
    }


# ══════════════════════════════════════════════════════════════════════════
# 2 · KHỚP DỮ KIỆN — cùng đầu vào qua `cham_doc_anh` của hai runner
# ══════════════════════════════════════════════════════════════════════════
def _ban_ghi(text="", diem=(), cong_thuc=(), khoi=(), quan_he=(), co_hinh=False, chuan_hoa=None) -> str:
    return json.dumps({
        "problem_text_verbatim": text, "problem_text_normalized": text if chuan_hoa is None else chuan_hoa,
        "math_expressions": [{"verbatim": f, "normalized": f} for f in cong_thuc],
        "named_points": list(diem), "named_lines": [], "named_planes": [], "named_solids": list(khoi),
        "given_relations": list(quan_he), "has_diagram": co_hinh,
        "diagram_observations": ["Chỉ có hình vẽ."] if co_hinh else [],
        "text_diagram_conflicts": [], "uncertain_tokens": [], "missing_regions": [], "confidence": 0.95,
    }, ensure_ascii=False)


def _lay(d: dict, khoa: str) -> Any:
    for phan in khoa.split("."):
        if not isinstance(d, dict) or phan not in d:
            return VANG
        d = d[phan]
    return d


DE_Z = "Cho mặt phẳng (P): z = 3 và điểm A."
DE_CHOP = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông."
S1A = "test_S1a_cong_thuc_khop_BIEU_THUC_HOAN_CHINH"
S1C = "test_S1c_nhan_diem_GIU_chi_so_va_dau_phay_tren"
S1D = "test_S1d_quan_he_DOI_TOAN_TU_khong_khop_va_la_MAU_THUAN"


def hang_du_kien() -> list[dict]:
    h = []
    for i, (doc, khop) in zip(["z=3_khop", "z=30", "z=-3", "z=3.1", "z=3+x"],
                              [("z=3", True), ("z = 30", False), ("z = -3", False), ("z = 3.1", False),
                               ("z = 3 + x", False)]):
        h.append((f"{S1A}[{i}]", f"công thức `z = 3` / đọc ra `{doc}`", DE_Z,
                  {"point_labels": ["A"], "formulas": ["z = 3"]}, DE_Z.replace("z = 3", doc),
                  {"diem": ["A"], "cong_thuc": [doc]}, {"FORMULA_ACCURACY": 1.0 if khop else 0.0}))
    h.append(("test_S1b_truong_cau_truc_KHONG_che_duoc_van_ban_sai",
              "văn bản ghi `z = 30` nhưng math_expressions khai `z = 3`", DE_Z,
              {"point_labels": ["A"], "formulas": ["z = 3"]}, DE_Z.replace("z = 3", "z = 30"),
              {"diem": ["A"], "cong_thuc": ["z = 3"]}, {"FORMULA_ACCURACY": 0.0}))
    for i, nhan, doc, khop in (("A_khop", ["A"], "điểm A.", True), ("A1_ca_hai", ["A1"], "điểm A1.", False),
                               ("A1_chi_van_ban", ["A"], "điểm A1.", False),
                               ("A'_ca_hai", ["A′"], "điểm A′.", False),
                               ("A'_chi_van_ban", ["A"], "điểm A′.", False)):
        h.append((f"{S1C}[{i}]", f"điểm `A` / named_points {nhan}, văn bản `{doc}`", DE_Z,
                  {"point_labels": ["A"], "formulas": ["z = 3"]}, DE_Z.replace("điểm A.", doc),
                  {"diem": nhan, "cong_thuc": ["z = 3"]}, {"POINT_LABEL_ACCURACY": 1.0 if khop else 0.0}))
    for i, de, gt, doc in (("vuong_goc_thanh_song_song", "Cho tứ diện SABC có AB ⊥ SC.", "AB ⊥ SC", "AB ∥ SC"),
                           ("thuoc_thanh_khong_thuoc", "Cho tứ diện SABC có A ∈ (SBC).", "A ∈ (SBC)", "A ∉ (SBC)")):
        h.append((f"{S1D}[{i}]", f"quan hệ `{gt}` / đọc ra `{doc}`", de, {"point_labels": ["A"], "relations": [gt]},
                  de.replace(gt, doc), {"diem": ["A"], "quan_he": [doc]},
                  {"RELATION_ACCURACY": 0.0, "details.relations_hallucinated": [doc]}))
    h += [
        ("test_S1e_khoang_trang_va_ky_hieu_tuong_duong_DA_KHAI", "`2x − z + 12 = 0`, `A₁` / `2x-z+12=0`, `A1`",
         f"Cho mặt phẳng (α): 2x {TRU} z + 12 = 0 và điểm A₁.",
         {"point_labels": ["A₁"], "formulas": [f"2x {TRU} z + 12 = 0"]}, "Cho mặt phẳng (α): 2x-z+12=0 và điểm A1.",
         {"diem": ["A1"], "cong_thuc": ["2x-z+12=0"]}, {"FORMULA_ACCURACY": 1.0, "POINT_LABEL_ACCURACY": 1.0}),
        ("test_S1f_ky_hieu_NGOAI_pham_vi_la_UNVERIFIABLE_khong_dung_khong_sai", "`a√3` — √ ngoài bảng token",
         "Cho tam giác đều ABC cạnh a√3.", {"point_labels": ["A"], "formulas": ["a√3"]},
         "Cho tam giác đều ABC cạnh a√3.", {"diem": ["A"], "cong_thuc": ["a√3"]},
         {"FORMULA_ACCURACY": None, "UNVERIFIABLE_FACTS": 1}),
        ("test_S2a_quan_he_dung_TOAN_NHAN_THAT_nhung_de_KHONG_xac_nhan_thi_CAN_NGUOI_XEM",
         "mục thêm `SA ⊥ BD`, mọi nhãn có trong đề, đề không nói", DE_CHOP, {"point_labels": ["S", "A"]}, DE_CHOP,
         {"diem": ["S", "A"], "quan_he": ["SA ⊥ BD"]},
         {"details.relations_unverified": ["SA ⊥ BD"], "HALLUCINATED_CRITICAL_FACTS": 0,
          "SILENT_HALLUCINATION_COUNT": SAU.KHONG_RO}),
        ("test_S2b_nguon_xac_nhan_la_GROUND_TRUTH_khong_phai_van_ban_cua_CHINH_model",
         "`SA ⊥ BD` có trong văn bản CỦA MODEL, không có trong ground truth", DE_CHOP,
         {"point_labels": ["S", "A"]}, DE_CHOP + " Biết SA ⊥ BD.", {"diem": ["S", "A"], "quan_he": ["SA ⊥ BD"]},
         {"details.relations_unverified": ["SA ⊥ BD"], "details.relations_confirmed": []}),
        ("test_S2c_muc_them_DUNG_theo_de_duoc_xac_nhan_khong_bi_danh_la_ao_giac",
         "mục thêm có nguyên văn trong ground truth", DE_CHOP, {"point_labels": ["S", "A"]}, DE_CHOP,
         {"diem": ["S", "A", "B"], "quan_he": ["ABCD là hình vuông"], "khoi": ["S.ABCD"]},
         {"details.relations_confirmed": ["ABCD là hình vuông"], "HALLUCINATED_CRITICAL_FACTS": 0,
          "SILENT_HALLUCINATION_COUNT": 0}),
        ("test_S2d_muc_them_mang_so_KHONG_co_trong_de_la_MAU_THUAN", "mục thêm `SA = 7`, số 7 không có trong đề",
         DE_CHOP, {"point_labels": ["S", "A"]}, DE_CHOP, {"diem": ["S", "A"], "quan_he": ["SA = 7"]},
         {"details.relations_hallucinated": ["SA = 7"], "HALLUCINATED_CRITICAL_FACTS": 1}),
    ]
    return h


def bang_chung_du_kien(TRUOC: Any) -> dict:
    dong = []
    for ten_test, mo_ta, de, cf, doc, kw, mong in hang_du_kien():
        day_du = {"point_labels": [], "formulas": [], "objects": [], "relations": [], "request": "", **cf}
        x = ie.parse_extraction(_ban_ghi(doc, **kw))
        g = {"expected_text": de, "critical_facts": day_du}
        truoc, sau = TRUOC.cham_doc_anh("C01", g, x, doc), SAU.cham_doc_anh("C01", g, x, doc)
        a = {k: _lay(truoc, k) for k in mong}
        b = {k: _lay(sau, k) for k in mong}
        dong.append({"test_name": f"{TEP_TEST}::{ten_test}", "description": mo_ta,
                     "input": {"ground_truth_text": de, "critical_facts": day_du, "reading": json.loads(_ban_ghi(doc, **kw))},
                     "expected": mong, "actual_before": a, "actual_after": b,
                     "raw_text_cer_after": sau["RAW_TEXT_CER"], "verdict": _phan_xu(mong, a, b),
                     "runner_sha256": RUNNER_SHA, "evidence_class": "OFFLINE_TEST"})
    return {
        "MATCHING_RULE": ("token hoá; dữ kiện phải là BIỂU THỨC HOÀN CHỈNH (hai bên là ranh giới) trong CẢ bản nguyên "
                          "văn LẪN bản chuẩn hoá; trường cấu trúc của model không bao giờ là nguồn khớp"),
        "DECLARED_EQUIVALENCES": SAU.TUONG_DUONG_DA_KHAI,
        "EXTRA_FACT_CLASSES": {SAU.CONFIRMED: "có nguyên biểu thức trong ground truth",
                               SAU.CONTRADICTED: "mang nhãn/số ground truth không có, hoặc khác đúng một số/một "
                                                 "toán tử quan hệ so với một đoạn ground truth",
                               SAU.UNVERIFIED: "còn lại — chờ người, không phải đúng cũng không phải sai"},
        "rows": dong,
        "VERDICT_COUNTS": {k: sum(1 for d in dong if d["verdict"] == k)
                           for k in ("FIXED", "GUARD_ALREADY_PRESENT", "NOT_FIXED")},
        "PROOF": "PASS" if all(d["verdict"] != "NOT_FIXED" for d in dong) else "FAIL",
    }


# ══════════════════════════════════════════════════════════════════════════
# NỀN LƯỢT RUNNER — ảnh giả, ground truth, provider kịch bản; dùng CHUNG cho hai runner
# ══════════════════════════════════════════════════════════════════════════
def dung_kho(tmp: Path) -> tuple[Path, dict[str, str]]:
    anh = tmp / "anh"
    anh.mkdir()
    for cid, mau in (("C01", (250, 250, 250)), ("C02", (225, 235, 255)), ("C03", (255, 235, 225))):
        buf = io.BytesIO()
        Image.new("RGB", (96, 64), mau).save(buf, format="PNG")
        (anh / f"{cid}.png").write_bytes(buf.getvalue())
    d = RNB.doc_de_bai()
    return anh, {"C01": d[CA_P1], "C02": d[CA_P6]}


def ground_truth(de: dict[str, str], ma_c03: list[str] | None) -> dict:
    c03 = {"case_id": "C03", "expected_outcome": "SAFE_REJECTION"}
    if ma_c03 is not None:
        c03["expected_rejection_codes"] = ma_c03
    return {"cases": [
        {"case_id": "C01", "expected_text": de["C01"], "critical_facts": {
            "point_labels": ["S", "A", "B", "C", "D"], "formulas": ["z = 3"], "objects": ["S.ABCD"],
            "relations": [["ABCD là hình vuông", "đáy ABCD là hình vuông"]],
            "request": "khoảng cách từ điểm S đến đường thẳng BD"}},
        {"case_id": "C02", "expected_text": de["C02"], "critical_facts": {
            "point_labels": ["O", "K", "A"], "formulas": [f"2x {TRU} z + 12 = 0"], "objects": [],
            "relations": [], "request": "Tính diện tích hình elip (E)"}},
        c03]}


def kich_ban(de: dict[str, str], thay: dict | None = None) -> dict:
    p1, p6 = RNB.doc_raw_theo_thu_tu(CA_P1), RNB.doc_raw_theo_thu_tu(CA_P6)
    kb = {("C01", "vision"): [_ban_ghi(de["C01"], "SABCD", ["z = 3"], ["S.ABCD"], ["ABCD là hình vuông"])],
          ("C01", "analyze"): p1["semantic_analyze"], ("C01", "synthesis"): p1["semantic_program"],
          ("C02", "vision"): [_ban_ghi(de["C02"], "OKA", [f"2x {TRU} z + 12 = 0"])],
          ("C02", "analyze"): p6["semantic_analyze"], ("C02", "synthesis"): p6["semantic_program"],
          ("C03", "vision"): [_ban_ghi(co_hinh=True)]}
    kb.update(thay or {})
    return kb


def chay_runner(M: Any, tmp: Path, anh: Path, ten: str, case: str, gt: dict, kb: dict, them=(),
                ngu_canh=None) -> dict:
    ra, gt_path = tmp / f"ra_{ten}", tmp / f"gt_{ten}.json"
    gt_path.write_text(json.dumps(gt, ensure_ascii=False), encoding="utf-8")
    giu: dict = {}

    def nha_may(cong):
        giu["t"] = M.TransportKichBan(cong, kb)
        return giu["t"]

    out, err = io.StringIO(), io.StringIO()
    with contextlib.ExitStack() as st:
        if ngu_canh is not None:
            st.enter_context(ngu_canh())
        st.enter_context(contextlib.redirect_stdout(io.StringIO()))
        st.enter_context(contextlib.redirect_stderr(io.StringIO()))
        ma = M.main(["--case", case, "--input-dir", str(anh), "--ground-truth", str(gt_path), "--output-dir", str(ra),
                     *them], inner_transport_factory=nha_may, env=ENV_GIA, stdout=out, stderr=err)
    tom_tat = json.loads((ra / "RUN_SUMMARY.json").read_text(encoding="utf-8")) if (ra / "RUN_SUMMARY.json").is_file() else None
    return {"exit_code": ma, "summary": tom_tat, "calls": giu["t"].calls if "t" in giu else None, "run_dir": ra,
            "stderr": err.getvalue()}


@contextlib.contextmanager
def ngoai_le_chua_phan_loai():
    goc = ie.parse_extraction

    def no(_raw):
        raise RuntimeError("ngoai le chua phan loai")

    ie.parse_extraction = no
    try:
        yield
    finally:
        ie.parse_extraction = goc


# ══════════════════════════════════════════════════════════════════════════
# 3 · C03 — mã đăng ký, và lỗi provider không phải từ chối an toàn
# ══════════════════════════════════════════════════════════════════════════
MA = ["MISSING_PROBLEM_TEXT"]
S3A, S3C = "test_S3a_C03_phai_DANG_KY_TRUOC_ma_tu_choi_THAT_cua_san_pham", "test_S3c_C03_tu_choi_bang_ma_NGOAI_danh_sach_KHONG_dat"
S3D = "test_S3d_C03_DAT_chi_khi_ma_that_TRONG_danh_sach_va_cong_HTTP_thay_0_request_tang_B"
S4 = "test_S4a_loi_provider_KHONG_BAO_GIO_la_tu_choi_an_toan + test_S4b_PASS_FAIL_ERROR_BLOCKED_duoc_PHAN_BIET"


def kich_ban_c03() -> list[tuple]:
    """`(id, test, mã đăng ký, ca, cờ thêm, phản hồi vision C03 | None, ngữ cảnh, kỳ vọng)`."""
    loi = {"http_401": (lambda: httpx.Response(401, text="unauthorized"), "ERROR"),
           "http_403": (lambda: httpx.Response(403, text="forbidden"), "ERROR"),
           "http_429": (lambda: httpx.Response(429, text="quota"), "ERROR"),
           "http_500": (lambda: httpx.Response(500, text="loi may chu"), "ERROR"),
           "http_503": (lambda: httpx.Response(503, text="qua tai"), "ERROR"),
           "timeout": (lambda: httpx.ReadTimeout("het gio"), "ERROR"),
           "loi_ket_noi": (lambda: httpx.ConnectError("khong ket noi duoc"), "ERROR"),
           "json_hong": (lambda: "day khong phai json", "FAIL"),
           "sai_luoc_do": (lambda: json.dumps({"foo": 1}), "FAIL")}
    ds = [
        ("ma_dang_ky_dung_MISSING_PROBLEM_TEXT", f"{S3D}[ma_dang_ky0]", MA, "C03", (), None, None,
         {"exit_is_pass": True, "counted_as_safe_rejection": True, "status": "PASS", "STAGE_B_HTTP_ATTEMPTS": 0}),
        ("ma_ngoai_danh_sach_UNSUPPORTED_PROBLEM", f"{S3C}[UNSUPPORTED_PROBLEM]", MA, "C03", (),
         lambda: _ban_ghi("Tính tổng các số nguyên dương từ 1 đến 100 bằng vòng lặp."), None,
         {"exit_is_pass": False, "counted_as_safe_rejection": False, "status": "FAIL"}),
        ("ma_ngoai_danh_sach_IMAGE_NOT_READABLE", f"{S3C}[IMAGE_NOT_READABLE]", MA, "C03", (), lambda: _ban_ghi(""),
         None, {"exit_is_pass": False, "counted_as_safe_rejection": False, "status": "FAIL"}),
        ("ground_truth_thieu_expected_rejection_codes", f"{S3A}[thieu_truong]", None, "C03", (), None, None,
         {"exit_code": 2}),
        ("ma_co_thong_bao_nhung_khong_bao_gio_phat_AMBIGUOUS_DIAGRAM",
         f"{S3A}[co_thong_bao_nhung_khong_bao_gio_phat]", ["AMBIGUOUS_DIAGRAM"], "C03", (), None, None,
         {"exit_code": 2}),
    ]
    ds += [(k, f"{S4}[{k}]", MA, "C03", (), f, None,
            {"exit_is_pass": False, "counted_as_safe_rejection": False, "status": s}) for k, (f, s) in loi.items()]
    ds += [("het_ngan_sach_http", f"{S4}[het_ngan_sach]", MA, "all", ("--max-http-requests", "6"), None, None,
            {"exit_is_pass": False, "counted_as_safe_rejection": False, "status": "BLOCKED"}),
           ("ngoai_le_chua_phan_loai", f"{S4}[ngoai_le_chua_phan_loai]", MA, "C03", (), None, ngoai_le_chua_phan_loai,
            {"exit_is_pass": False, "counted_as_safe_rejection": False, "status": "ERROR"})]
    return ds


def _quan_sat_c03(l: dict) -> dict:
    tt = l["summary"] or {}
    c03 = next((c for c in tt.get("cases", []) if c["case_id"] == "C03"), None)
    return {
        "exit_code": l["exit_code"],
        "exit_is_pass": l["exit_code"] == 0,
        "counted_as_safe_rejection": bool(c03 and c03.get("C03_SAFE_REJECTION") is True),
        "status": VANG if c03 is None else c03.get("status", VANG),
        "STAGE_B_HTTP_ATTEMPTS": VANG if c03 is None else c03.get("STAGE_B_HTTP_ATTEMPTS", VANG),
        "REJECTION_CODE": VANG if c03 is None else c03.get("REJECTION_CODE", VANG),
        "AUTOMATED_CHECKS": tt.get("AUTOMATED_CHECKS", VANG),
        "ACCEPTANCE": tt.get("ACCEPTANCE", VANG),
        "NETWORK_REQUESTS": tt.get("NETWORK_REQUESTS", VANG),
        "RUNNER_ERROR": tt.get("RUNNER_ERROR"),
        "fail_reasons": [] if c03 is None else c03.get("fail_reasons", [])[:2],
        "stage_b_calls_seen_by_fake_transport": None if l["calls"] is None else
        sum(1 for cid, tang in l["calls"] if cid == "C03" and tang in ("analyze", "synthesis")),
    }


def _so_sanh(mong: dict, truoc: dict, sau: dict) -> dict:
    theo_khoa = {k: _phan_xu(v, truoc.get(k, VANG), sau.get(k, VANG)) for k, v in mong.items()}
    tong = ("NOT_FIXED" if "NOT_FIXED" in theo_khoa.values() else
            "FIXED" if "FIXED" in theo_khoa.values() else "GUARD_ALREADY_PRESENT")
    return {"verdict_by_key": theo_khoa, "verdict": tong}


def bang_chung_c03(TRUOC: Any, tmp: Path, anh: Path, de: dict[str, str]) -> dict:
    dong = []
    for i, (ma_id, ten_test, ma, case, them, vision, ngu_canh, mong) in enumerate(kich_ban_c03()):
        quan_sat = {}
        for nhan, M in (("before", TRUOC), ("after", SAU)):
            thay = None if vision is None else {("C03", "vision"): [vision()]}
            l = chay_runner(M, tmp, anh, f"c03_{i}_{nhan}", case, ground_truth(de, ma), kich_ban(de, thay), them,
                            ngu_canh)
            quan_sat[nhan] = _quan_sat_c03(l)
        dong.append({"id": ma_id, "test_name": f"{TEP_TEST}::{ten_test}",
                     "input": {"case": case, "extra_flags": list(them), "expected_rejection_codes": ma,
                               "c03_vision_response": ("MISSING_PROBLEM_TEXT reading (chỉ có hình)" if vision is None
                                                       and case == "C03" and ngu_canh is None else
                                                       "parse_extraction ném RuntimeError" if ngu_canh else
                                                       "không gửi — C01+C02 dùng hết trần 6" if case == "all" else
                                                       repr(vision()))},
                     "expected": mong, "actual_before": quan_sat["before"], "actual_after": quan_sat["after"],
                     **_so_sanh(mong, quan_sat["before"], quan_sat["after"]),
                     "runner_sha256": RUNNER_SHA, "evidence_class": "OFFLINE_TEST"})
    loi_provider = [d for d in dong if d["id"] not in ("ma_dang_ky_dung_MISSING_PROBLEM_TEXT",
                                                       "ma_ngoai_danh_sach_UNSUPPORTED_PROBLEM",
                                                       "ma_ngoai_danh_sach_IMAGE_NOT_READABLE",
                                                       "ground_truth_thieu_expected_rejection_codes",
                                                       "ma_co_thong_bao_nhung_khong_bao_gio_phat_AMBIGUOUS_DIAGRAM")]
    return {
        "PRODUCT_REJECTION_CODES_FROM_AST": sorted(SAU.ma_tu_choi_san_pham()),
        "REJECTION_MESSAGES_KEYS": sorted(ie.REJECTION_MESSAGES),
        "C03_PASS_RULE": ("phản hồi đọc ảnh hợp lệ theo lược đồ · assess_extraction trả rejected với mã ∈ "
                          "expected_rejection_codes · cổng HTTP thấy 0 request analyze/synthesis của C03 · không có cảnh"),
        "STATUS_TAXONOMY": {"PASS": "đạt", "FAIL": "model trả lời và sai, kể cả sai JSON/lược đồ",
                            "ERROR": "provider/hạ tầng không cho câu trả lời: HTTP 4xx/5xx, timeout, kết nối, "
                                     "ngoại lệ chưa phân loại",
                            "BLOCKED": "cổng runner chặn request (trần HTTP, dừng sau lỗi provider)"},
        "HYPOTHESIS_4_PROVIDER_ERRORS_COUNTED_AS_SAFE_REJECTION_AT_684420D": (
            "NO — đã có guard: " + str(sum(d["verdict_by_key"]["counted_as_safe_rejection"] == "GUARD_ALREADY_PRESENT"
                                           for d in loi_provider)) + f"/{len(loi_provider)} lỗi provider/lược đồ/ngân sách "
            "không được tính là từ chối an toàn ở 684420d; cái THIẾU là phân biệt FAIL/ERROR/BLOCKED"),
        "rows": dong,
        "VERDICT_COUNTS": {k: sum(1 for d in dong if d["verdict"] == k)
                           for k in ("FIXED", "GUARD_ALREADY_PRESENT", "NOT_FIXED")},
        "NETWORK_REQUESTS_TOTAL": sum(d[f"actual_{n}"]["NETWORK_REQUESTS"] for d in dong for n in ("before", "after")
                                      if isinstance(d[f"actual_{n}"]["NETWORK_REQUESTS"], int)),
        "PROOF": "PASS" if all(d["verdict"] != "NOT_FIXED" for d in dong) else "FAIL",
    }


# ══════════════════════════════════════════════════════════════════════════
# 4 · CỔNG DUYỆT THỦ CÔNG — mọi bản duyệt ở đây là SIMULATED_REVIEW
# ══════════════════════════════════════════════════════════════════════════
S5 = "test_S5"


def kiem_ban_duyet(M: Any, run_dir: Path, ban: Path | None) -> dict:
    argv = ["--verify-review", "--run-dir", str(run_dir)] + (["--human-review", str(ban)] if ban else [])
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as se:
        ma = M.main(argv, env={}, stdout=out, stderr=err)
    try:
        kq = json.loads(out.getvalue())
    except ValueError:
        kq = {}
    return {"exit_code": ma, "exit_is_pass": ma == 0,
            **{k: kq.get(k, VANG) for k in ("HUMAN_CRITICAL_FACT_REVIEW", "BINDING_VALID", "REAL_PHOTO_ACCEPTANCE")},
            "problems": kq.get("problems", VANG),
            "stderr_first_line": ((err.getvalue() + se.getvalue()).strip().splitlines() or [None])[0]}


def bang_chung_duyet(TRUOC: Any, tmp: Path, anh: Path, de: dict[str, str]) -> dict:
    luot = {n: chay_runner(M, tmp, anh, f"duyet_{n}", "C01", ground_truth(de, MA), kich_ban(de))
            for n, M in (("before", TRUOC), ("after", SAU))}
    khoa_tt = ("AUTOMATED_CHECKS", "HUMAN_CRITICAL_FACT_REVIEW", "REAL_PHOTO_ACCEPTANCE", "ACCEPTANCE")
    quan_sat = {n: {**{k: (l["summary"] or {}).get(k, VANG) for k in khoa_tt},
                    "HUMAN_REVIEW_PACKET_WRITTEN": (l["run_dir"] / "HUMAN_REVIEW_PACKET.json").is_file(),
                    "exit_code": l["exit_code"]} for n, l in luot.items()}
    mong_a = {"AUTOMATED_CHECKS": "PASS", "HUMAN_CRITICAL_FACT_REVIEW": "PENDING", "REAL_PHOTO_ACCEPTANCE": "NOT_RUN",
              "ACCEPTANCE": "PENDING_HUMAN_REVIEW", "HUMAN_REVIEW_PACKET_WRITTEN": True}
    dong = [{"id": "run_summary_sau_luot_tu_dong_dat",
             "test_name": f"{TEP_TEST}::test_S5a_luot_tu_dong_DAT_van_CHO_nguoi_duyet_va_goi_duyet_GAN_dung_luot",
             "input": "--case C01, provider giả trả đúng đề, tầng B phát lại p1",
             "expected": mong_a, "actual_before": quan_sat["before"], "actual_after": quan_sat["after"],
             **_so_sanh(mong_a, quan_sat["before"], quan_sat["after"]),
             "runner_sha256": RUNNER_SHA, "evidence_class": "OFFLINE_TEST"}]

    goi = json.loads((luot["after"]["run_dir"] / "HUMAN_REVIEW_PACKET.json").read_text(encoding="utf-8"))
    mau = goi["review_template"]

    def ban_duyet(ten: str, **thay) -> tuple[Path, dict]:
        ban = {**mau, "review_kind": "SIMULATED_REVIEW", "reviewer": "PROOF_SCRIPT_SIMULATED_NOT_A_HUMAN",
               "reviewed_at": "2026-09-14T00:00:00+00:00", "decision": "PASS", "notes": "kiểm cơ chế, không phải duyệt",
               "cases": [{**c, "decision": "PASS"} for c in mau["cases"]]}
        for k, v in thay.items():
            if k.startswith("case_"):
                ban["cases"][0][k[5:]] = v
            else:
                ban[k] = v
        p = tmp / f"review_{ten}.json"
        p.write_text(json.dumps(ban, ensure_ascii=False), encoding="utf-8")
        return p, ban

    kich = [("khong_co_ban_duyet", "test_S5c_khong_co_ban_duyet_thi_PENDING", None,
             {"HUMAN_CRITICAL_FACT_REVIEW": "PENDING", "exit_is_pass": False}),
            ("ban_gia_hop_le", "test_S5d_ban_duyet_GIA_hop_le_KHONG_BAO_GIO_thanh_PASS", {},
             {"HUMAN_CRITICAL_FACT_REVIEW": "SIMULATED_REVIEW", "BINDING_VALID": True,
              "REAL_PHOTO_ACCEPTANCE": "NOT_RUN", "exit_is_pass": False})]
    for ten, thay in (("run_id", {"run_id": "luot-khac"}), ("ground_truth", {"ground_truth_sha256": "0" * 64}),
                      ("anh", {"case_image_sha256": "1" * 64}), ("dau_ra_model", {"case_raw_extraction_sha256": "2" * 64}),
                      ("ban_xac_nhan", {"case_confirmed_input_sha256": "3" * 64})):
        kich.append((f"ban_duyet_cu_lech_{ten}", f"test_S5e_ban_duyet_CU_bi_tu_choi_khi_rang_buoc_lech[{ten}]", thay,
                     {"HUMAN_CRITICAL_FACT_REVIEW": "STALE_REVIEW", "exit_is_pass": False}))
    for ten, thay in (("nguoi_that_cho_luot_khong_phai_provider_that", {"review_kind": "HUMAN"}),
                      ("thieu_nguoi_duyet", {"reviewer": ""}), ("quyet_dinh_la", {"decision": "OK"})):
        kich.append((f"ban_duyet_sai_khuon_{ten}", f"test_S5g_ban_duyet_SAI_KHUON_la_INVALID[{ten}]", thay,
                     {"HUMAN_CRITICAL_FACT_REVIEW": "INVALID_REVIEW", "exit_is_pass": False}))
    for ma_id, ten_test, thay, mong in kich:
        p, ban = (None, None) if thay is None else ban_duyet(ma_id, **thay)
        a, b = kiem_ban_duyet(TRUOC, luot["before"]["run_dir"], p), kiem_ban_duyet(SAU, luot["after"]["run_dir"], p)
        dong.append({"id": ma_id, "test_name": f"{TEP_TEST}::{ten_test}", "input": {"review": ban},
                     "expected": mong, "actual_before": a, "actual_after": b, **_so_sanh(mong, a, b),
                     "runner_sha256": RUNNER_SHA, "evidence_class": "OFFLINE_TEST"})

    # Cuối cùng vì nó SỬA tệp của lượt: đầu ra model đổi SAU khi đã duyệt.
    p, ban = ban_duyet("truoc_khi_dau_ra_doi")
    hop_le_truoc = kiem_ban_duyet(SAU, luot["after"]["run_dir"], p)
    tep = luot["after"]["run_dir"] / "C01_RAW_EXTRACTION.json"
    tep.write_text(tep.read_text(encoding="utf-8").replace("S.ABCD", "S.ABCE", 1), encoding="utf-8")
    mong = {"HUMAN_CRITICAL_FACT_REVIEW": "STALE_REVIEW", "exit_is_pass": False}
    b = kiem_ban_duyet(SAU, luot["after"]["run_dir"], p)
    a = kiem_ban_duyet(TRUOC, luot["before"]["run_dir"], p)
    dong.append({"id": "dau_ra_model_doi_sau_khi_duyet",
                 "test_name": f"{TEP_TEST}::test_S5f_dau_ra_model_DOI_SAU_khi_duyet_thi_ban_duyet_het_hieu_luc",
                 "input": {"review": ban, "mutation": "C01_RAW_EXTRACTION.json: S.ABCD → S.ABCE (lần đầu)",
                           "same_review_before_mutation": hop_le_truoc},
                 "expected": mong, "actual_before": a, "actual_after": b, **_so_sanh(mong, a, b),
                 "runner_sha256": RUNNER_SHA, "evidence_class": "OFFLINE_TEST"})
    return {
        "REVIEW_KIND_IN_THIS_ARTIFACT": "SIMULATED_REVIEW — không bản duyệt nào ở đây do người ký",
        "USER_VISUAL_APPROVAL": "NOT_GIVEN",
        "REVIEW_BINDING_FIELDS": ["run_id", "ground_truth_sha256", "cases[].image_sha256",
                                  "cases[].raw_extraction_sha256", "cases[].confirmed_input_sha256", "reviewer",
                                  "reviewed_at", "decision", "notes", "review_kind"],
        "REVIEWER_MUST_CHECK": goi["reviewer_must_check"],
        "PASS_RULE": ("HUMAN_CRITICAL_FACT_REVIEW = PASS chỉ khi review_kind = HUMAN trên lượt REAL_PROVIDER, ràng buộc "
                      "khớp tệp hiện tại, mọi ca decision PASS. REAL_PHOTO_ACCEPTANCE = PASS còn cần AUTOMATED_CHECKS = "
                      "PASS và REAL_PROVIDER_EVIDENCE = ESTABLISHED. Nhánh ấy chỉ kiểm được bằng hàm thuần trong test "
                      "S5h — không artifact nào ở đây mang PASS."),
        "rows": dong,
        "VERDICT_COUNTS": {k: sum(1 for d in dong if d["verdict"] == k)
                           for k in ("FIXED", "GUARD_ALREADY_PRESENT", "NOT_FIXED")},
        "PROOF": "PASS" if all(d["verdict"] != "NOT_FIXED" for d in dong) else "FAIL",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="prove_photo_scorer_correction.py")
    for co in ("--before-junit", "--after-junit", "--after-old-junit"):
        ap.add_argument(co, required=True)
    ap.add_argument("--out-dir", default=str(RA))
    ns = ap.parse_args(argv)
    ra = Path(ns.out_dir).resolve()
    ra.mkdir(parents=True, exist_ok=True)
    da_co = [t for t in TEN_RA if (ra / t).exists()]
    if da_co:
        print(f"TỪ CHỐI GHI ĐÈ: {da_co}", file=sys.stderr)
        return 2
    junit = [Path(p) for p in (ns.before_junit, ns.after_junit, ns.after_old_junit)]
    if any(not p.is_absolute() or not p.is_file() for p in junit):
        print("--*-junit phải là tệp TUYỆT ĐỐI có thật", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="photo-scorer-proof-") as t:
        tmp = Path(t)
        TRUOC, sha_truoc = nap_runner_truoc(tmp)
        RUNNER_SHA.update(before=sha_truoc, before_source=f"git show {MOC_TRUOC}:{DUONG_RUNNER}",
                          after=_sha((BE / "scripts" / "run_photo_problem_live.py").read_bytes()))
        anh, de = dung_kho(tmp)
        with SAU.ChanMangThat() as chan:
            ket = {
                "BEFORE_AFTER_TESTS.json": bang_chung_test(*junit),
                "FACT_MATCHING_PROOF.json": bang_chung_du_kien(TRUOC),
                "C03_REJECTION_PROOF.json": bang_chung_c03(TRUOC, tmp, anh, de),
                "HUMAN_REVIEW_GATE_PROOF.json": bang_chung_duyet(TRUOC, tmp, anh, de),
            }
        an = [str(tmp), tmp.as_posix(), str(tmp).replace("\\", "\\\\")]
    for ten, obj in ket.items():
        noi_dung = json.dumps({**_dau(ten), "NETWORK_REQUESTS_OUTSIDE_RUNNER": len(chan.attempts), **obj},
                              ensure_ascii=False, indent=2) + "\n"
        for s in an:
            noi_dung = noi_dung.replace(s, "<thư mục tạm>")
        # Thông điệp lỗi trong JUnit XML chở đường dẫn tạm của pytest — mang tên người dùng máy.
        import re

        noi_dung = re.sub(r"pytest-of-[^\\/'\"\s]+", "pytest-of-<user>",
                          re.sub(r"(?i)([A-Z]:(?:\\+|/)Users(?:\\+|/))[^\\/'\"\s]+", r"\1<user>", noi_dung))
        (ra / ten).write_text(noi_dung, encoding="utf-8")
        print(f"{ten}: {obj['PROOF']}")
    return 0 if all(o["PROOF"] == "PASS" for o in ket.values()) and not chan.attempts else 1


if __name__ == "__main__":
    sys.exit(main())
