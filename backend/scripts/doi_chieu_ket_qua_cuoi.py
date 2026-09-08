# -*- coding: utf-8 -*-
"""ĐỐI CHIẾU số liệu lượt đo cuối trước khi viết chương. **0 lượt gọi model.**

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \\
        scripts/doi_chieu_ket_qua_cuoi.py <thư mục lượt đo>

    `THESIS_RESULTS_ANALYSIS_AND_CHAPTER_DRAFTING` §3, 2026-09-08.

─── VÌ SAO PHẢI CÓ BƯỚC NÀY ───────────────────────────────────────────────

Báo cáo dùng để **định vị** bằng chứng; con số đi vào khoá luận phải **tái
tính** từ artifact có băm. Hai thứ đó khác nhau đúng vào lúc quan trọng nhất —
và wave trước đã cho thấy vì sao: một cột trong báo cáo gốc (`SILENT_WRONG_
ANSWER_COUNT = 6`) SAI, và nó chỉ lộ ra khi có người tính lại.

Nên file này KHÔNG đọc báo cáo. Nó đọc:

    manifest · stage A · stage B · raw/** · SCORING_CORRECTION
    → tự cộng lại từ đầu → so với BẢNG CHUẨN dưới đây

Bảng chuẩn chép từ đặc tả wave, tức từ một nguồn NGOÀI kho artifact. Trùng
nhau mới là bằng chứng; một file tự so với chính nó thì luôn đúng.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

__all__ = ["BANG_CHUAN", "doi_chieu", "tai_tinh"]

#: Giá trị CHUẨN, chép từ đặc tả wave `THESIS_RESULTS_ANALYSIS_AND_CHAPTER_
#: DRAFTING §3`. Cố ý KHÔNG đọc từ artifact: nguồn thứ hai phải nằm ngoài thứ
#: đang được kiểm.
BANG_CHUAN: dict[str, Any] = {
    "RUN_VALIDITY": "VALID",
    "RUN_ID": "thesis-final-20260908T160224Z",
    "APPLICATION_LLM_CALLS": 19,
    "ANALYZE_CALLS": 9,
    "SYNTHESIS_CALLS": 9,
    "REPAIR_CALLS": 1,
    "PHYSICAL_API_ATTEMPTS": 19,
    "TRANSPORT_RETRIES": 0,
    "INPUT_TOKENS": 49481,
    "OUTPUT_TOKENS": 14390,
    "THOUGHT_TOKENS": 33998,
    "CACHED_TOKENS": 1859,
    "TOTAL_TOKENS": 97869,
    "POSITIVE_CASES": 7,
    "NEGATIVE_CASES": 2,
    "FIRST_ATTEMPT_SERVABLE": 6,
    "EVENTUAL_SERVABLE": 7,
    "EXACT_ANSWER_PASS": 7,
    "SOURCE_INVARIANT_PASS": 7,
    "POSTCONDITIONS_PASS": 7,
    "TRACE_PASS": 7,
    "SCENE3D_PASS": 7,
    "NEGATIVE_FAIL_CLOSED": 2,
    "SILENT_WRONG_ANSWER_COUNT": 0,
    "UNHANDLED_EXCEPTION_COUNT": 0,
    "MODEL_FAILURE_COUNT": 1,
    "SYSTEM_FAILURE_COUNT": 0,
    "MEASUREMENT_FAILURE_COUNT": 1,
    "ATTRIBUTION_UNRESOLVED_COUNT": 0,
    "PRODUCT_PROMOTION_ELIGIBLE": "NO",
    "STABILITY_UNDER_ACCEPTANCE": "NOT_MEASURED",
}

#: Mười hai biểu thức chính xác, cũng chép từ đặc tả. Thứ tự KHÔNG quan trọng;
#: phép so là so TẬP, vì thứ tự trong báo cáo là một lựa chọn trình bày.
DAP_SO_CHUAN = ["72", "9", "3√6", "96", "4500π", "144π", "360π", "120π",
                "100π", "65π", "25π√5", "2π√6"]


def _bam(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _doc(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def kiem_bam(thu_muc: Path) -> dict[str, Any]:
    """§3.1–3.2 — 26 artifact còn nguyên byte không?"""
    bang = _doc(thu_muc / "ARTIFACT_HASHES.json")
    lech, thieu, thua = [], [], []
    tren_dia = {str(p.relative_to(thu_muc)).replace("\\", "/")
                for p in thu_muc.rglob("*") if p.is_file()
                and p.name != "ARTIFACT_HASHES.json"}
    for ten, bam in bang["sha256"].items():
        p = thu_muc / ten
        if not p.exists():
            thieu.append(ten)
        elif _bam(p) != bam:
            lech.append(ten)
    thua = sorted(tren_dia - set(bang["sha256"]))
    raw = [t for t in bang["sha256"] if t.startswith("raw/")]
    return {
        "SO_ARTIFACT": bang["so_file"],
        "SO_FILE_RAW": len(raw),
        "BAM_LECH": lech, "BAM_THIEU": thieu, "FILE_NGOAI_BANG": thua,
        "ARTIFACT_HASH_VERIFICATION": not (lech or thieu or thua),
    }


def kiem_lien_ket_dinh_chinh(thu_muc: Path) -> dict[str, Any]:
    """§3.3 — bản đính chính có trỏ đúng băm của artifact thô không?"""
    dc = _doc(thu_muc / "SCORING_CORRECTION.json")
    lech = {ten: {"trong_dinh_chinh": bam, "tren_dia": _bam(thu_muc / ten)}
            for ten, bam in dc["artifact_da_dinh_chinh"].items()
            if _bam(thu_muc / ten) != bam}
    return {
        "SO_ARTIFACT_DUOC_DINH_CHINH": len(dc["artifact_da_dinh_chinh"]),
        "LIEN_KET_LECH": lech,
        "CORRECTION_LINKAGE_OK": not lech,
    }


def tai_tinh(thu_muc: Path) -> dict[str, Any]:
    """§3.4 — cộng lại TỪ ĐẦU, không đọc bất kỳ tổng hợp nào đã ghi sẵn."""
    import score_thesis_final_acceptance as S
    import thesis_acceptance_corpus as C

    a = _doc(thu_muc / "stage_a_first_attempt.json")
    b = _doc(thu_muc / "stage_b_recovery.json")
    mf = _doc(thu_muc / "manifest.json")
    duong_id = {c["id"] for c in C.CA_DUONG}

    # ── lượt gọi: đếm từ cây `raw/`, không đọc bộ đếm nào ────────────────
    raw = [_doc(p) for p in (thu_muc / "raw").rglob("*.json")]
    theo_stage: dict[str, int] = {}
    for r in raw:
        theo_stage[r["stage"]] = theo_stage.get(r["stage"], 0) + 1
    vat_ly = sum(r["physical_attempts"] for r in raw)

    # ── token: cộng từ `token_theo_stage` của lượt chạy ──────────────────
    tk = _doc(thu_muc / "final_scoring.json")["token_theo_stage"]
    tong = {k: sum(v[k] for v in tk.values()) for k in
            ("prompt_tokens", "candidates_tokens", "thoughts_tokens",
             "cached_content_tokens", "total_tokens")}

    # ── cột từng ca: chấm LẠI bằng scorer chính tắc, không đọc kết quả cũ ─
    dc = S.cham_lai(thu_muc)
    b_id = {x["id"] for x in b["cases"] if not x.get("bo_qua")}
    cot = ("SOURCE_INVARIANTS_PASS", "POSTCONDITIONS_PASS", "TRACE_PASS",
           "SCENE3D_PASS")
    dem = {k: 0 for k in cot}
    for c in a["cases"]:
        if c["id"] not in duong_id:
            continue
        cuoi = next((x["cham"] for x in b["cases"]
                     if x["id"] == c["id"] and not x.get("bo_qua")), c["cham"])
        for k in cot:
            dem[k] += bool(cuoi.get(k))

    am = [c for c in a["cases"] if c["id"] not in duong_id]
    ném = sum(1 for c in a["cases"] if c["cham"].get("UNHANDLED_EXCEPTION"))
    lop = _doc(thu_muc / "final_scoring.json")["verdicts"]
    he = sum(1 for v in lop.values() if v.startswith("SYSTEM_"))
    mo_hinh = sum(1 for i, v in lop.items()
                  if i in duong_id and i in b_id)     # ca dương phải sửa
    chua_ket_luan = sum(1 for v in lop.values() if v == "ATTRIBUTION_UNRESOLVED")

    dap_so = sorted(q["actual_display"]
                    for v in dc["cases"].values()
                    for q in v["quantities_SUA"].values())
    return {
        "RUN_ID": mf["run_id"],
        "RUN_VALIDITY": _doc(thu_muc / "FINAL_SUMMARY.json")["RUN_VALIDITY"],
        "APPLICATION_LLM_CALLS": len(raw),
        "ANALYZE_CALLS": theo_stage.get("analyze", 0),
        "SYNTHESIS_CALLS": theo_stage.get("synthesis", 0),
        "REPAIR_CALLS": theo_stage.get("repair", 0),
        "PHYSICAL_API_ATTEMPTS": vat_ly,
        "TRANSPORT_RETRIES": vat_ly - len(raw),
        "INPUT_TOKENS": tong["prompt_tokens"],
        "OUTPUT_TOKENS": tong["candidates_tokens"],
        "THOUGHT_TOKENS": tong["thoughts_tokens"],
        "CACHED_TOKENS": tong["cached_content_tokens"],
        "TOTAL_TOKENS": tong["total_tokens"],
        "POSITIVE_CASES": len(dc["cases"]),
        "NEGATIVE_CASES": len(am),
        "FIRST_ATTEMPT_SERVABLE": sum(
            1 for c in a["cases"]
            if c["id"] in duong_id and c["cham"].get("SERVABLE")),
        "EVENTUAL_SERVABLE": sum(
            1 for v in dc["cases"].values() if v["SERVABLE"]),
        "EXACT_ANSWER_PASS": dc["TONG_KET_SUA"]["EXACT_ANSWER_PASS"],
        "SOURCE_INVARIANT_PASS": dem["SOURCE_INVARIANTS_PASS"],
        "POSTCONDITIONS_PASS": dem["POSTCONDITIONS_PASS"],
        "TRACE_PASS": dem["TRACE_PASS"],
        "SCENE3D_PASS": dem["SCENE3D_PASS"],
        "NEGATIVE_FAIL_CLOSED": sum(
            1 for c in am if c["cham"].get("NEGATIVE_FAIL_CLOSED")),
        "SILENT_WRONG_ANSWER_COUNT":
            dc["TONG_KET_SUA"]["SILENT_WRONG_ANSWER_COUNT"],
        "UNHANDLED_EXCEPTION_COUNT": ném,
        "MODEL_FAILURE_COUNT": mo_hinh,
        "SYSTEM_FAILURE_COUNT": he,
        # Một bản đính chính đã ghi = một lần bộ đo sai.
        "MEASUREMENT_FAILURE_COUNT": int(
            (thu_muc / "SCORING_CORRECTION.json").exists()),
        "ATTRIBUTION_UNRESOLVED_COUNT": chua_ket_luan,
        "PRODUCT_PROMOTION_ELIGIBLE":
            _doc(thu_muc / "FINAL_SUMMARY.json")["PRODUCT_PROMOTION_ELIGIBLE"],
        "STABILITY_UNDER_ACCEPTANCE":
            _doc(thu_muc / "FINAL_SUMMARY.json")["STABILITY_UNDER_ACCEPTANCE"],
        "_dap_so": dap_so,
        "_theo_ca": {i: {"servable": v["SERVABLE"], "chang": v["stage_cuoi"],
                         "dap_so": {q["witness_model"]: q["actual_display"]
                                    for q in v["quantities_SUA"].values()}}
                     for i, v in dc["cases"].items()},
    }


def doi_chieu(thu_muc: Path) -> dict[str, Any]:
    bam = kiem_bam(thu_muc)
    lk = kiem_lien_ket_dinh_chinh(thu_muc)
    that = tai_tinh(thu_muc)
    lech = {k: {"chuan": v, "tai_tinh": that.get(k)}
            for k, v in BANG_CHUAN.items() if that.get(k) != v}
    ds_lech = sorted(DAP_SO_CHUAN) != that["_dap_so"]
    ok = (bam["ARTIFACT_HASH_VERIFICATION"] and lk["CORRECTION_LINKAGE_OK"]
          and not lech and not ds_lech)
    return {
        "artifact_schema_version": "1.2",
        "khai": "Đối chiếu §3 — tái tính TỪ ARTIFACT rồi so với bảng chuẩn "
                "chép từ ĐẶC TẢ WAVE. Không đọc báo cáo. 0 lượt gọi model.",
        "wave": "THESIS_RESULTS_ANALYSIS_AND_CHAPTER_DRAFTING",
        "run_id": that["RUN_ID"],
        "DOCUMENTATION_INPUT_CONSISTENCY": "PASS" if ok else "FAIL",
        **bam, **lk,
        "SO_DAP_SO": len(that["_dap_so"]),
        "DAP_SO_KHOP": not ds_lech,
        "dap_so_tai_tinh": that["_dap_so"],
        "LECH": lech,
        "tai_tinh": {k: v for k, v in that.items() if not k.startswith("_")},
        "theo_ca": that["_theo_ca"],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("thu_muc")
    p.add_argument("--ghi", default=None, help="ghi artifact đối chiếu")
    a = p.parse_args()
    d = doi_chieu(Path(a.thu_muc))

    print("ĐỐI CHIẾU SỐ LIỆU TRƯỚC KHI VIẾT CHƯƠNG — 0 lượt gọi model\n")
    print(f"  ARTIFACT_HASH_VERIFICATION   "
          f"{'PASS' if d['ARTIFACT_HASH_VERIFICATION'] else 'FAIL'}"
          f"  ({d['SO_ARTIFACT']} file · {d['SO_FILE_RAW']} raw)")
    print(f"  CORRECTION_LINKAGE           "
          f"{'PASS' if d['CORRECTION_LINKAGE_OK'] else 'FAIL'}"
          f"  ({d['SO_ARTIFACT_DUOC_DINH_CHINH']} artifact được đính chính)")
    print(f"  DAP_SO_KHOP                  "
          f"{'PASS' if d['DAP_SO_KHOP'] else 'FAIL'}  ({d['SO_DAP_SO']}/12)")
    print(f"  SO_TRUONG_LECH               {len(d['LECH'])}/{len(BANG_CHUAN)}")
    for k, v in d["LECH"].items():
        print(f"    ✗ {k}: chuẩn {v['chuan']} · tái tính {v['tai_tinh']}")
    print(f"\n  DOCUMENTATION_INPUT_CONSISTENCY  "
          f"{d['DOCUMENTATION_INPUT_CONSISTENCY']}")
    if a.ghi:
        from acceptance_integrity import ghi_artifact

        f = Path(a.ghi)
        if f.exists():
            f.unlink()
        ghi_artifact(f, d)
        print(f"\n→ {f}")
    return 0 if d["DOCUMENTATION_INPUT_CONSISTENCY"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
