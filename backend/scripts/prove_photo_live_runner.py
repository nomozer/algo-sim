# -*- coding: utf-8 -*-
"""BẰNG CHỨNG OFFLINE cho runner nghiệm thu ảnh đề bài — 0 request mạng, 0 quota.

`PHOTO_PROBLEM_LIVE_RUNNER_HARDENING` §13. Mọi phép đo đi qua ĐÚNG mã runner
(`run_photo_problem_live.main` / `CongHttp`) với provider giả đặt ở ranh giới HTTP,
bên trong `ChanMangThat`. Sinh bốn artifact cạnh `DRY_RUN_GROUND_TRUTH.json` (đăng
ký trước, không sinh ở đây):

  HTTP_BUDGET_PROOF.json  · 12 lượt gọi logic dưới trần 11 ⇒ 11 tới transport giả,
                            lượt thứ 12 bị chặn TRƯỚC transport
                          · đường xấu nhất mà cả ba ca vẫn ĐẠT dùng đúng 11 request
                          · cùng đường ấy dưới trần 10 ⇒ ảnh C03 bị chặn
  CER_PROOF.json          · cặp CER biết trước đáp số, và lỗi nhãn/công thức KHÔNG
                            bị một CER thấp che đi
  REDACTION_PROOF.json    · ba lỗi provider chở secret GIẢ qua ba tầng; chỉ ghi BĂM
  RUNNER_DRY_RUN.json     · `--dry-run --case all` trên ảnh TỔNG HỢP c01/c05/c11

Từ chối ghi đè. Chạy từ `backend/`:

    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/prove_photo_live_runner.py
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
for _p in (str(BE), str(BE / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import httpx  # noqa: E402

from app.ai import gemini, pipeline  # noqa: E402
from app.ai.telemetry import stage_scope  # noqa: E402
from app.ingestion import image_extraction as ie  # noqa: E402

import replay_negative_boundaries as RNB  # noqa: E402
import run_photo_problem_live as R  # noqa: E402

GOC = BE.parent
RA = GOC / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene" / "live-runner-hardening"
ANH_TONG_HOP = GOC / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene" / "corpus"
NGUON = "docs/evaluation/geometry/thesis-final-acceptance/CORPUS.json"
CA_PHAT_LAI = {"C01": "p1_chop_thiet_dien_khoang_cach", "C02": "p6_thiet_dien_elip_cua_hinh_tru"}
#: Secret GIẢ. Artifact chỉ mang BĂM của chúng, không bao giờ mang giá trị.
KHOA_GIA = "AIzaSyFAKE-SECRET-0123456789abcdef"
BI_MAT_GIA = (KHOA_GIA, "TOKEN-KHAC-987", "TOKEN-AUTH-555", "COOKIE-777", "QUERYKEY-999")
ENV_GIA = {"ALLOW_LIVE_AI": "1", "GEMINI_API_KEY": KHOA_GIA}
TEN_RA = ("HTTP_BUDGET_PROOF.json", "CER_PROOF.json", "REDACTION_PROOF.json", "RUNNER_DRY_RUN.json")
DUOI_ANH = {".png", ".jpg", ".jpeg", ".webp"}


def _sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8") if isinstance(b, str) else b).hexdigest()


def _git(*a: str) -> str | None:
    try:
        return subprocess.run(["git", *a], cwd=GOC, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _dau(ten: str) -> dict:
    return {
        "wave": R.WAVE,
        "artifact": ten,
        "source_artifact_path": NGUON,
        "generated_by": "backend/scripts/prove_photo_live_runner.py",
        "git_head": _git("rev-parse", "HEAD"),
        "runner_sha256": _sha((BE / "scripts" / "run_photo_problem_live.py").read_bytes()),
        "MEASUREMENT_CLASS": "OFFLINE_RUNNER_CERTIFICATION",
        "REAL_PROVIDER_CALLS": 0,
        "REAL_PROVIDER_EVIDENCE": "NOT_APPLICABLE_OFFLINE_PROOF",
    }


# ══════════════════════════════════════════════════════════════════════════
# NỀN — kịch bản provider và một lượt runner
# ══════════════════════════════════════════════════════════════════════════
def kich_ban(gt: dict[str, dict], thay: dict | None = None) -> dict:
    p1 = RNB.doc_raw_theo_thu_tu(CA_PHAT_LAI["C01"])
    p6 = RNB.doc_raw_theo_thu_tu(CA_PHAT_LAI["C02"])

    def doc_anh(cid: str) -> list[str]:
        return [json.dumps(R.ban_ghi_gia_lap(gt[cid]), ensure_ascii=False)]

    kb = {
        ("C01", "vision"): doc_anh("C01"),
        ("C01", "analyze"): p1["semantic_analyze"],
        ("C01", "synthesis"): p1["semantic_program"],
        ("C02", "vision"): doc_anh("C02"),
        ("C02", "analyze"): p6["semantic_analyze"],
        ("C02", "synthesis"): p6["semantic_program"],
        ("C03", "vision"): doc_anh("C03"),
    }
    kb.update(thay or {})
    return kb


def chay_runner(argv: list[str], kb: dict | None, env: dict[str, str]) -> dict:
    """Một lượt `R.main`; mọi dòng in ra — kể cả qua `sys.stdout` — đều bị bắt lại."""
    giu: dict = {}

    def nha_may(cong):
        giu["cong"] = cong
        giu["t"] = R.TransportKichBan(cong, kb)
        return giu["t"]

    out, err, sys_out, sys_err = io.StringIO(), io.StringIO(), io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(sys_out), contextlib.redirect_stderr(sys_err):
        ma = R.main(argv, inner_transport_factory=None if kb is None else nha_may,
                    env=env, stdout=out, stderr=err)
    return {"exit_code": ma, "stdout": out.getvalue() + sys_out.getvalue(),
            "stderr": err.getvalue() + sys_err.getvalue(), "transport": giu.get("t")}


def _argv(case: str, gt_path: Path, ra: Path, *them: str) -> list[str]:
    return ["--case", case, "--input-dir", str(ANH_TONG_HOP), "--ground-truth", str(gt_path),
            "--output-dir", str(ra), *them]


def _doc(ra: Path, ten: str) -> dict:
    return json.loads((ra / ten).read_text(encoding="utf-8"))


def _rut_gon(tt: dict) -> dict:
    khoa = ("run_mode", "cases_run", "cases_not_run", "MAX_HTTP_REQUESTS", "HTTP_REQUESTS_ATTEMPTED",
            "HTTP_REQUESTS_SENT", "HTTP_REQUESTS_BLOCKED", "VISION_HTTP_REQUESTS", "ANALYZE_HTTP_REQUESTS",
            "SYNTHESIS_HTTP_REQUESTS", "BLOCKED_BY_STAGE", "RETRIES", "APIBUDGET_RETRY_REQUESTS",
            "STAGE_SUM_EQUALS_SENT",
            "FAKE_OR_INNER_TRANSPORT_INVOCATIONS", "APIBUDGET_HTTP_COUNT", "APIBUDGET_MATCHES_GATE",
            "NETWORK_REQUESTS", "REAL_PROVIDER_CALLS", "ACCEPTANCE")
    return {k: tt.get(k) for k in khoa}


# ══════════════════════════════════════════════════════════════════════════
# 1 · TRẦN HTTP
# ══════════════════════════════════════════════════════════════════════════
async def _muoi_hai_luot() -> list[dict]:
    bi_chan = []
    for i in range(1, 13):
        try:
            with stage_scope("semantic_program"):
                await gemini.call_gemini("PROOF_KHONG_PHAI_KHOA", "system", f"lượt logic {i}")
        except R.HttpBudgetExceeded as err:
            bi_chan.append({"logical_call": i, "error": str(err)})
    return bi_chan


def bang_chung_ngan_sach(gt_path: Path, tam: Path) -> dict:
    dem = {"n": 0}

    def tra(_req: httpx.Request) -> httpx.Response:
        dem["n"] += 1
        return R._phan_hoi_gemini("{}")

    cong = R.CongHttp(httpx.MockTransport(tra), R.MAX_HTTP_REQUESTS, R.BoKhuBiMat())
    cong.dat_ca("C01")
    budget = gemini.ApiBudget(max_attempts=R.MAX_ATTEMPTS_PER_LOGICAL_CALL)
    with R.ChanMangThat() as chan, R.dung_ngan_sach(budget), R.cai_cong_http(cong):
        bi_chan = asyncio.run(_muoi_hai_luot())
    muc_cong = {
        "LOGICAL_CALLS_ISSUED": 12,
        "MAX_HTTP_REQUESTS": cong.max_http_requests,
        "HTTP_REQUESTS_ATTEMPTED": cong.attempted,
        "HTTP_REQUESTS_SENT": cong.sent,
        "HTTP_REQUESTS_BLOCKED": cong.blocked,
        "FAKE_TRANSPORT_INVOCATIONS": dem["n"],
        "NETWORK_REQUESTS": len(chan.attempts),
        "BLOCKED_LOGICAL_CALLS": bi_chan,
        "BLOCK_REASONS": [r["block_reason"] for r in cong.records if r["blocked"]],
        "APIBUDGET_HTTP_COUNT": budget.http_requests,
    }
    dat_cong = ((cong.attempted, cong.sent, cong.blocked, dem["n"], len(chan.attempts)) == (12, 11, 1, 11, 0)
                and [b["logical_call"] for b in bi_chan] == [12])

    gt = R.doc_ground_truth(gt_path, list(R.CASE_IDS))
    hong = "{ day khong phai json"
    p1 = RNB.doc_raw_theo_thu_tu(CA_PHAT_LAI["C01"])
    p6 = RNB.doc_raw_theo_thu_tu(CA_PHAT_LAI["C02"])
    xau = kich_ban(gt, {("C01", "synthesis"): [hong, hong, *p1["semantic_program"]],
                        ("C02", "synthesis"): [hong, hong, *p6["semantic_program"]]})
    l11 = chay_runner(_argv("all", gt_path, tam / "xau_nhat_tran_11"), xau, ENV_GIA)
    tt11 = _doc(tam / "xau_nhat_tran_11", "RUN_SUMMARY.json")
    l10 = chay_runner(_argv("all", gt_path, tam / "xau_nhat_tran_10", "--max-http-requests", "10"), xau, ENV_GIA)
    tt10 = _doc(tam / "xau_nhat_tran_10", "RUN_SUMMARY.json")
    dat_11 = (l11["exit_code"] == 0 and tt11["HTTP_REQUESTS_SENT"] == R.MAX_HTTP_REQUESTS
              and tt11["HTTP_REQUESTS_BLOCKED"] == 0 and tt11["NETWORK_REQUESTS"] == 0
              and tt11["RETRIES"] == tt11["APIBUDGET_RETRY_REQUESTS"] == 0)
    dat_10 = (l10["exit_code"] == 1 and (tt10["HTTP_REQUESTS_SENT"], tt10["HTTP_REQUESTS_BLOCKED"]) == (10, 1)
              and tt10["BLOCKED_BY_STAGE"]["vision"] == 1 and ("C03", "vision") not in l10["transport"].calls)

    truoc = 3 * ie.VISION_MAX_ATTEMPTS + 2 * (1 + pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS) * gemini.MAX_ATTEMPTS
    sau = R.MAX_ATTEMPTS_PER_LOGICAL_CALL * (3 + 2 * (1 + pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS))
    return {
        "GATE_LEVEL": muc_cong,
        "WORST_CASE_DERIVED_FROM_CONSTANTS": {
            "BEFORE_HARDENING_HTTP": truoc,
            "BEFORE_FORMULA": (f"3 vision × VISION_MAX_ATTEMPTS {ie.VISION_MAX_ATTEMPTS} + 2 ca × (1 analyze + "
                               f"{pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS} synthesis) × MAX_ATTEMPTS "
                               f"{gemini.MAX_ATTEMPTS}"),
            "AFTER_HARDENING_HTTP": sau,
            "AFTER_FORMULA": (f"MAX_ATTEMPTS_PER_LOGICAL_CALL {R.MAX_ATTEMPTS_PER_LOGICAL_CALL} × (3 vision + "
                              f"2 ca × (1 analyze + {pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS} synthesis))"),
            "AFTER_EQUALS_MAX_HTTP_REQUESTS": sau == R.MAX_HTTP_REQUESTS,
        },
        "RUNNER_WORST_PASSING_PATH": {
            "scenario": "tổng hợp C01 và C02 trả JSON hỏng hai lượt, lượt sửa thứ ba phát lại byte đóng băng",
            "cap_11": {"exit_code": l11["exit_code"], **_rut_gon(tt11)},
            "cap_10": {"exit_code": l10["exit_code"], **_rut_gon(tt10)},
        },
        "PROOF": "PASS" if dat_cong and dat_11 and dat_10 and sau == R.MAX_HTTP_REQUESTS else "FAIL",
    }


# ══════════════════════════════════════════════════════════════════════════
# 2 · CER
# ══════════════════════════════════════════════════════════════════════════
CAP_CER = [
    ("thay", "abc", "abd", 1 / 3),
    ("ref_rong", "", "xyz", 3.0),
    ("pred_rong", "abc", "", 1.0),
    ("trung", "abc", "abc", 0.0),
    ("dau_tieng_viet", "Hình chóp", "Hinh chop", 2 / 9),
    ("khoang_trang", "SA = 3", "SA=3", 2 / 6),
    ("crlf_khoang_trang_cuoi_dong", "dòng 1\ndòng 2", "dòng 1  \r\ndòng 2", 0.0),
    ("nfd", "Hình chóp", unicodedata.normalize("NFD", "Hình chóp"), 0.0),
    ("hoa_thuong", "ABCD", "abcd", 1.0),
    ("dau_tru", "x = -2", "x = 2", 1 / 6),
    ("kinh_dien", "kitten", "sitting", 3 / 6),
    ("mau_so_la_ref_1", "ab", "abcd", 1.0),
    ("mau_so_la_ref_2", "abcd", "ab", 0.5),
]


def bang_chung_cer(gt_path: Path) -> dict:
    cap = []
    for ten, ref, pred, mong in CAP_CER:
        thuc = R.cer(ref, pred)
        cap.append({"id": ten, "reference": ref, "prediction": pred,
                    "prediction_codepoints": len(pred), "expected_cer": round(mong, 6),
                    "actual_cer": round(thuc, 6), "match": abs(thuc - mong) < 1e-9})

    gt = R.doc_ground_truth(gt_path, ["C01"])["C01"]
    ref = gt["expected_text"]

    def ban(text: str, **thay) -> ie.ImageProblemExtraction:
        b = R.ban_ghi_gia_lap(gt)
        b.update(problem_text_verbatim=text, problem_text_normalized=text, **thay)
        return ie.parse_extraction(json.dumps(b, ensure_ascii=False))

    nhan = ref.replace("S.ABCD", "S.ABCE")
    cong_thuc = ref.replace("z = 3", "z = 8")
    che = []
    for ten, text, x in (
        ("doi_chung_dung", ref, ban(ref)),
        ("sai_nhan_S.ABCE", nhan, ban(nhan, named_points=["S", "A", "B", "C", "E"], named_solids=["S.ABCE"])),
        ("sai_cong_thuc_z_8", cong_thuc, ban(cong_thuc, math_expressions=[{"verbatim": "z = 8",
                                                                            "normalized": "z = 8"}])),
    ):
        k = R.cham_doc_anh("C01", gt, x, text)
        che.append({"id": ten, **{f: k[f] for f in (
            "CER_THRESHOLD", "RAW_TEXT_CER", "POINT_LABEL_ACCURACY", "FORMULA_ACCURACY", "OBJECT_ACCURACY",
            "RELATION_ACCURACY", "REQUEST_ACCURACY", "HALLUCINATED_CRITICAL_FACTS", "fail_reasons")},
            "CER_BELOW_THRESHOLD": k["RAW_TEXT_CER"] <= k["CER_THRESHOLD"],
            "VERDICT": "FAIL" if k["fail_reasons"] else "PASS"})
    dat_che = (che[0]["VERDICT"] == "PASS"
               and all(c["CER_BELOW_THRESHOLD"] and c["VERDICT"] == "FAIL" for c in che[1:]))
    return {
        "DEFINITION": "CER = Levenshtein(ref, pred) / max(1, len(ref)) sau đúng ba phép chuẩn hoá: NFC · "
                      "CRLF/CR → LF · bỏ khoảng trắng cuối dòng. Không hạ chữ, không bỏ dấu, không gộp khoảng trắng.",
        "CER_THRESHOLDS_PREREGISTERED": R.NGUONG_CER,
        "PAIRS": cap,
        "LOW_CER_DOES_NOT_MASK_CRITICAL_FACTS": che,
        "PROOF": "PASS" if all(c["match"] for c in cap) and dat_che else "FAIL",
    }


# ══════════════════════════════════════════════════════════════════════════
# 3 · KHỬ SECRET
# ══════════════════════════════════════════════════════════════════════════
def _than_chua_bi_mat(url: str = "") -> str:
    return (f"MARKER-DA-TOI {url} API {KHOA_GIA} x-goog-api-key: TOKEN-KHAC-987 "
            "Authorization: Bearer TOKEN-AUTH-555 Set-Cookie: sid=COOKIE-777 cb?key=QUERYKEY-999")


def bang_chung_khu_bi_mat(gt_path: Path, tam: Path) -> dict:
    gt = R.doc_ground_truth(gt_path, list(R.CASE_IDS))
    kich = {
        "vision_http_403_body": {("C01", "vision"): [httpx.Response(403, text=_than_chua_bi_mat())]},
        "analyze_http_403_body": {("C01", "analyze"): [httpx.Response(403, text=_than_chua_bi_mat())]},
        "synthesis_connect_error_with_request_url": {
            ("C01", "synthesis"): [lambda req: httpx.ConnectError(_than_chua_bi_mat(str(req.url)))]},
    }
    luot = []
    for ten, thay in kich.items():
        ra = tam / f"khu_{ten}"
        l = chay_runner(_argv("C01", gt_path, ra), kich_ban(gt, thay), ENV_GIA)
        be_mat = {"stdout": l["stdout"], "stderr": l["stderr"],
                  **{p.name: p.read_text(encoding="utf-8") for p in sorted(ra.iterdir())}}
        ro = {bm: sum(noi_dung.count(s) for s in BI_MAT_GIA) for bm, noi_dung in be_mat.items()}
        luot.append({
            "scenario": ten,
            "exit_code": l["exit_code"],
            "SURFACES_SCANNED": sorted(be_mat),
            "SECRET_OCCURRENCES_BY_SURFACE": ro,
            "SECRET_OCCURRENCES_TOTAL": sum(ro.values()),
            "MARKER_REACHED_STDOUT": "MARKER-DA-TOI" in l["stdout"],
            "MARKER_REACHED_RUN_SUMMARY": "MARKER-DA-TOI" in be_mat.get("RUN_SUMMARY.json", ""),
            "REDACTED_MARKERS_IN_ARTIFACTS": sum(v.count(R.REDACTED) for k, v in be_mat.items()
                                                 if k.endswith(".json")),
        })
    dat = all(x["SECRET_OCCURRENCES_TOTAL"] == 0 and x["MARKER_REACHED_STDOUT"]
              and x["MARKER_REACHED_RUN_SUMMARY"] and x["REDACTED_MARKERS_IN_ARTIFACTS"] > 0 for x in luot)
    return {
        "SECRET_NAMES_REDACTED": list(R.TEN_BI_MAT),
        "SECRET_VALUES_RECORDED": "SHA256_ONLY",
        "FAKE_SECRET_SHA256": [_sha(s) for s in BI_MAT_GIA],
        "WHY_MARKER": "MARKER-DA-TOI đi cùng secret trong thông điệp lỗi: nó có mặt ở stdout và RUN_SUMMARY chứng "
                      "minh thông điệp THẬT SỰ tới bề mặt, nên 0 lần lộ không phải vì không có gì để lộ.",
        "RUNS": luot,
        "PROOF": "PASS" if dat else "FAIL",
    }


# ══════════════════════════════════════════════════════════════════════════
# 4 · --dry-run TRÊN ẢNH TỔNG HỢP
# ══════════════════════════════════════════════════════════════════════════
def bang_chung_dry_run(gt_path: Path, tam: Path) -> dict:
    de = RNB.doc_de_bai()
    gt = R.doc_ground_truth(gt_path, list(R.CASE_IDS))
    khop_de = {cid: gt[cid]["expected_text"] == de[ca] for cid, ca in CA_PHAT_LAI.items()}
    ra = tam / "dry_run"
    l = chay_runner(_argv("all", gt_path, ra, "--dry-run"), None, {})
    tt, pc = _doc(ra, "RUN_SUMMARY.json"), _doc(ra, "PROVIDER_CALLS.json")
    tep = sorted(p.name for p in ra.iterdir())
    dat = (l["exit_code"] == 0 and all(khop_de.values()) and tt["ACCEPTANCE"] == "PASS"
           and tt["NETWORK_REQUESTS"] == 0 and tt["REAL_PROVIDER_CALLS"] == 0
           and tt["HTTP_REQUESTS_SENT"] == tt["FAKE_OR_INNER_TRANSPORT_INVOCATIONS"] == 7
           and tt["STAGE_SUM_EQUALS_SENT"] and not [t for t in tep if Path(t).suffix.lower() in DUOI_ANH])
    return {
        "command": ("run_photo_problem_live.py --dry-run --case all --input-dir <abs>/photo-problem-to-scene/corpus "
                    "--ground-truth <abs>/live-runner-hardening/DRY_RUN_GROUND_TRUTH.json --output-dir <thư mục tạm>"),
        "CORPUS_KIND": "SYNTHETIC_RENDERED",
        "GROUND_TRUTH_TEXT_MATCHES_SOURCE_CORPUS": khop_de,
        "exit_code": l["exit_code"],
        "stdout": l["stdout"].splitlines(),
        "OUTPUT_FILES": tep,
        "RUN_SUMMARY": {k: v for k, v in tt.items() if k != "cases"},
        "cases": tt["cases"],
        "PROVIDER_CALLS": pc["records"],
        "PROOF": "PASS" if dat else "FAIL",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="prove_photo_live_runner.py")
    ap.add_argument("--out-dir", default=str(RA))
    ns = ap.parse_args(argv)
    ra = Path(ns.out_dir).resolve()
    gt_path = ra / "DRY_RUN_GROUND_TRUTH.json"
    if not gt_path.is_file():
        print(f"THIẾU ground truth đăng ký trước: {gt_path}", file=sys.stderr)
        return 2
    da_co = [t for t in TEN_RA if (ra / t).exists()]
    if da_co:
        print(f"TỪ CHỐI GHI ĐÈ: {da_co}", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="photo-live-proof-") as t:
        tam = Path(t)
        ket = {
            "HTTP_BUDGET_PROOF.json": bang_chung_ngan_sach(gt_path, tam),
            "CER_PROOF.json": bang_chung_cer(gt_path),
            "REDACTION_PROOF.json": bang_chung_khu_bi_mat(gt_path, tam),
            "RUNNER_DRY_RUN.json": bang_chung_dry_run(gt_path, tam),
        }
    for ten, obj in ket.items():
        (ra / ten).write_text(json.dumps({**_dau(ten), **obj}, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
        print(f"{ten}: {obj['PROOF']}")
    return 0 if all(o["PROOF"] == "PASS" for o in ket.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
