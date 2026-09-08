# -*- coding: utf-8 -*-
"""CHẤM LẠI OFFLINE một lượt đo cuối đã chạy. **0 lượt gọi model.**

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \\
        scripts/score_thesis_final_acceptance.py <thư mục lượt đo>

    `THESIS_FINAL_ACCEPTANCE_EXECUTION` §8, 2026-09-08.

─── VÌ SAO TỒN TẠI ────────────────────────────────────────────────────────

Lượt đo chính thức `thesis-final-20260908T160224Z` chạy đúng, hệ trả đáp số
đúng, nhưng **bộ chấm tra sai chỗ**: nó tìm đáp số bằng
`final_memory[<tên biến của GOLD>]`, trong khi tên biến là thứ **mô hình tự
đặt**. Mô hình viết `the_volume_sabcd`, `V_S_MNPQR`, `dien_tich_elip_e`…; gold
viết `V`, `S_T`, `S_E`. Kết quả: `actual_display = None` ở 6/7 ca **có đáp số
hoàn toàn đúng**, và `SILENT_WRONG_ANSWER_COUNT` báo **6** thay vì **0**.

Tức bộ đo tố cáo hệ một tội nó không phạm — và đó là chiều sai đắt nhất trong
cả tuyến này.

─── LUẬT CỦA MỘT BẢN ĐÍNH CHÍNH ──────────────────────────────────────────

§8 nói rõ: *"giữ nguyên raw artifact, tạo correction nối bằng hash và chấm lại
offline"*. Nên file này:

    · KHÔNG sửa một byte nào của lượt đo đã chạy;
    · KHÔNG gọi model — nó chỉ đọc `final_memory` đã lưu;
    · ghi băm của từng artifact nó đính chính, để bản sửa truy được về bản gốc;
    · ghi CẢ HAI con số — bản gốc và bản sửa — cạnh nhau.

─── ÁNH XẠ ĐÚNG: THEO **LOẠI NGHĨA VỤ**, KHÔNG THEO TÊN ──────────────────

Thứ KHÔNG đổi giữa gold và bản mô hình viết là `kind` của nghĩa vụ (`volume` ·
`area` · `lateral_area` · `distance`): nó do `analyze` khai và do taxonomy đóng
băng quyết định, không do mô hình đặt tên. Đo trên cả 9 ca: `kind` là khoá DUY
NHẤT trong mỗi ca, nên phép ghép không mập mờ — và guard ném khi điều đó thôi
đúng, thay vì lặng lẽ chấm một đại lượng bằng kỳ vọng của đại lượng khác.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

__all__ = ["cham_lai", "song_anh_tu_artifact"]


def _bam(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def song_anh_tu_artifact(hop_dong_live: dict, hop_dong_gold: dict,
                         case_id: str) -> dict[str, str]:
    """`{witness GOLD → witness MÔ HÌNH}` từ hai hợp đồng ĐÃ LƯU."""
    gold = [(o["kind"], (o.get("params") or {}).get("witness"))
            for o in hop_dong_gold["obligations"]]
    live = [(o["kind"], (o.get("params") or {}).get("witness"))
            for o in hop_dong_live["obligations"]]
    for ten, ds in (("gold", gold), ("live", live)):
        k = [x for x, _w in ds]
        if len(set(k)) != len(k):
            raise ValueError(
                f"ca '{case_id}': hợp đồng {ten} có hai nghĩa vụ cùng kind "
                f"{k} — ánh xạ theo kind không còn phân biệt được")
    theo_kind = {k: w for k, w in live if w}
    return {w: theo_kind[k] for k, w in gold if w and k in theo_kind}


def _cham_dai_luong(mong: dict, final_memory: dict, song_anh: dict,
                    dung_sai: dict) -> dict[str, Any]:
    import thesis_acceptance_oracle as O

    ra = {}
    for ten, m in mong.items():
        ten_that = song_anh.get(ten, ten)
        hien = final_memory.get(ten_that)
        khop_so, sai_so = False, None
        if hien is not None:
            try:
                sai_so = O.sai_so_tuong_doi(hien, m["oracle_value"])
                khop_so = sai_so <= dung_sai[m["oracle_method"]]
            except O.OracleError:
                khop_so, sai_so = False, None
        ra[ten] = {
            "witness_gold": ten, "witness_model": ten_that,
            "expected_display": m["display"], "actual_display": hien,
            "exact_answer_match": hien == m["display"],
            "oracle_numeric_agreement": khop_so, "relative_error": sai_so,
        }
    return ra


def cham_lai(thu_muc: Path) -> dict[str, Any]:
    """Đọc artifact đã lưu, chấm lại cột đáp số, trả bản đính chính."""
    import thesis_acceptance_corpus as C

    thu_muc = Path(thu_muc)
    p_a = thu_muc / "stage_a_first_attempt.json"
    p_b = thu_muc / "stage_b_recovery.json"
    p_s = thu_muc / "final_scoring.json"
    a = json.loads(p_a.read_text(encoding="utf-8"))
    b = json.loads(p_b.read_text(encoding="utf-8"))
    goc = json.loads(p_s.read_text(encoding="utf-8"))

    theo_id = {c["id"]: c for c in C.CA_DUONG}
    mong_tat = C.expected_results_json()
    dung_sai = mong_tat["oracle_tolerance"]

    hop_dong = {c["id"]: c["request_contract"] for c in a["cases"]
                if "request_contract" in c}
    b_theo_id = {x["id"]: x for x in b["cases"] if not x.get("bo_qua")}

    cases: dict[str, Any] = {}
    for c in a["cases"]:
        cid = c["id"]
        if cid not in theo_id:            # ca ÂM: cột đáp số không áp dụng
            continue
        # Chặng B (nếu có) là bản CUỐI của ca ấy.
        cuoi = b_theo_id.get(cid, {}).get("cham") or c["cham"]
        sa = song_anh_tu_artifact(
            hop_dong[cid], theo_id[cid]["request_contract_gold"], cid)
        dl = _cham_dai_luong(mong_tat["cases"][cid], cuoi.get("final_memory")
                             or {}, sa, dung_sai)
        cases[cid] = {
            "witness_mapping": sa,
            "SERVABLE": cuoi.get("SERVABLE"),
            "stage_cuoi": "B" if cid in b_theo_id else "A",
            "quantities_GOC": (cuoi.get("quantities") or {}),
            "quantities_SUA": dl,
            "EXACT_ANSWER_MATCH_GOC": cuoi.get("EXACT_ANSWER_MATCH"),
            "EXACT_ANSWER_MATCH_SUA": bool(dl) and all(
                q["exact_answer_match"] for q in dl.values()),
            "ORACLE_NUMERIC_AGREEMENT_GOC": cuoi.get(
                "ORACLE_NUMERIC_AGREEMENT"),
            "ORACLE_NUMERIC_AGREEMENT_SUA": bool(dl) and all(
                q["oracle_numeric_agreement"] for q in dl.values()),
        }

    am = [c for c in a["cases"] if c["id"] not in theo_id]
    silent_sua = sum(
        1 for v in cases.values()
        if v["SERVABLE"] and v["EXACT_ANSWER_MATCH_SUA"] is False)
    silent_sua += sum(1 for c in am if c["cham"].get("SERVABLE"))

    return {
        "artifact_schema_version": "1.2",
        "khai": "ĐÍNH CHÍNH cột đáp số của một lượt đo ĐÃ CHẠY. Artifact thô "
                "giữ NGUYÊN BYTE; 0 lượt gọi model; không ca nào chạy lại.",
        "wave": "THESIS_FINAL_ACCEPTANCE_EXECUTION",
        "run_id": goc.get("run_id") or thu_muc.name,
        "tao_luc": datetime.now(timezone.utc).isoformat(),
        "NGUYEN_NHAN": (
            "Bộ chấm tra đáp số bằng `final_memory[<tên biến của GOLD>]`, "
            "nhưng tên biến là thứ MÔ HÌNH tự đặt. Lượt live cho "
            "`the_volume_sabcd`/`V_S_MNPQR`/`dien_tich_elip_e`… trong khi gold "
            "dùng `V`/`S_T`/`S_E`, nên `actual_display = None` ở 6/7 ca CÓ ĐÁP "
            "SỐ ĐÚNG."),
        "CACH_SUA": (
            "Ánh xạ theo LOẠI NGHĨA VỤ (`kind`) — thứ do `analyze` khai và "
            "taxonomy đóng băng quyết định, không do mô hình đặt tên. `kind` "
            "là khoá duy nhất trong mọi ca của corpus (đo trên cả 9)."),
        "VI_SAO_CHUNG_NHAN_STUB_KHONG_BAT_DUOC": (
            "Stub trả về CHÍNH gold program, nên tên witness của 'mô hình' "
            "luôn TRÙNG tên gold và phép tra sai không bao giờ lộ. Một provider "
            "giả giống bản mẫu quá mức thì không kiểm được thứ chỉ sai khi "
            "mô hình tự do. Đã thêm ca stub ĐỔI TÊN witness để guard có răng."),
        "artifact_da_dinh_chinh": {
            "stage_a_first_attempt.json": _bam(p_a),
            "stage_b_recovery.json": _bam(p_b),
            "final_scoring.json": _bam(p_s),
        },
        "TONG_KET_GOC": {
            "EXACT_ANSWER_PASS": sum(
                1 for v in cases.values() if v["EXACT_ANSWER_MATCH_GOC"]),
            "SILENT_WRONG_ANSWER_COUNT": goc.get("SILENT_WRONG_ANSWER_COUNT"),
        },
        "TONG_KET_SUA": {
            "POSITIVE_CASES": len(cases),
            "FINAL_SERVABLE": sum(1 for v in cases.values() if v["SERVABLE"]),
            "EXACT_ANSWER_PASS": sum(
                1 for v in cases.values() if v["EXACT_ANSWER_MATCH_SUA"]),
            "ORACLE_NUMERIC_AGREEMENT_PASS": sum(
                1 for v in cases.values()
                if v["ORACLE_NUMERIC_AGREEMENT_SUA"]),
            "SILENT_WRONG_ANSWER_COUNT": silent_sua,
            "NEGATIVE_FAIL_CLOSED": sum(
                1 for c in am if c["cham"].get("NEGATIVE_FAIL_CLOSED")),
        },
        "cases": cases,
    }


#: Tên file của runner ↔ tên đặc tả §9 gọi. Hai bộ tên, MỘT bộ file: nhân đôi
#: nội dung để khớp tên là tạo hai nguồn sự thật, và bản thứ hai sẽ trôi.
TEN_THEO_DAC_TA = {
    "manifest.json": "manifest.json",
    "stage_a_first_attempt.json": "stage_a_first_attempt.json",
    "stage_b_recovery.json": "stage_b_one_repair.json",
    "final_scoring.json": "scoring.json",
    "FINAL_SUMMARY.json": "final_summary.json",
    "ARTIFACT_HASHES.json": "bảng SHA-256 toàn bộ artifact",
    "TELEMETRY_BUDGET_LEDGER.json": "telemetry và budget ledger",
    "raw/": "raw analyze/provider/candidate theo ca và attempt",
}


def bang_bam(thu_muc: Path) -> dict[str, Any]:
    """SHA-256 của MỌI file trong thư mục lượt đo (§9)."""
    tep = sorted(p for p in thu_muc.rglob("*") if p.is_file())
    return {
        "artifact_schema_version": "1.2",
        "khai": "Băm SHA-256 toàn bộ artifact của lượt đo. Tự loại chính nó.",
        "run_id": thu_muc.name,
        "so_file": len(tep) - 1,
        "ten_theo_dac_ta": TEN_THEO_DAC_TA,
        "sha256": {str(p.relative_to(thu_muc)).replace("\\", "/"): _bam(p)
                   for p in tep if p.name != "ARTIFACT_HASHES.json"},
    }


def so_telemetry(thu_muc: Path) -> dict[str, Any]:
    """Sổ từng lượt gọi + đối chiếu ngân sách (§9)."""
    sk = json.loads((thu_muc / "event_log.json").read_text("utf-8"))["events"]
    tt = json.loads((thu_muc / "final_scoring.json").read_text("utf-8"))
    raw = sorted((thu_muc / "raw").rglob("*.json"))
    ban = [json.loads(p.read_text("utf-8")) for p in raw]
    ban.sort(key=lambda r: r["logical_call_index"])
    ns = tt["budget"]
    theo_stage: dict[str, int] = {}
    for r in ban:
        theo_stage[r["stage"]] = theo_stage.get(r["stage"], 0) + 1
    return {
        "artifact_schema_version": "1.2",
        "khai": "Sổ lượt gọi và ngân sách. Lượt gọi LOGIC và lần thử VẬT LÝ "
                "đếm riêng; retry transport KHÔNG phải một lượt gọi logic.",
        "run_id": thu_muc.name,
        "LOGICAL_CALLS": tt["LOGICAL_CALLS"],
        "LOGICAL_CALLS_BY_STAGE": theo_stage,
        "PHYSICAL_API_ATTEMPTS": tt["PHYSICAL_ATTEMPTS"],
        "TRANSPORT_RETRIES": tt["PHYSICAL_ATTEMPTS"] - tt["LOGICAL_CALLS"],
        "TOKEN_RESERVED": tt["TOKEN_RESERVED"],
        "TOKENS_ACTUAL": tt["TOKENS_ACTUAL"],
        "token_theo_stage": tt["token_theo_stage"],
        "TOTAL_INPUT_TOKENS": sum(
            v["prompt_tokens"] for v in tt["token_theo_stage"].values()),
        "TOTAL_OUTPUT_TOKENS": sum(
            v["candidates_tokens"] for v in tt["token_theo_stage"].values()),
        "TOTAL_THOUGHT_TOKENS": sum(
            v["thoughts_tokens"] for v in tt["token_theo_stage"].values()),
        "TOTAL_CACHED_TOKENS": sum(
            v["cached_content_tokens"] for v in tt["token_theo_stage"].values()),
        "budget": ns,
        "con_lai": {
            "logical": ns["max_logical"] - tt["LOGICAL_CALLS"],
            "physical": ns["max_physical"] - tt["PHYSICAL_ATTEMPTS"],
            "token": ns["hard_token"] - tt["TOKENS_ACTUAL"],
        },
        "VUOT_NGAN_SACH": (tt["LOGICAL_CALLS"] > ns["max_logical"]
                           or tt["PHYSICAL_ATTEMPTS"] > ns["max_physical"]
                           or tt["TOKENS_ACTUAL"] > ns["hard_token"]),
        "so_su_kien": len(sk),
        "moi_luot_goi": [
            {k: r[k] for k in ("logical_call_index", "case_id", "stage",
                               "attempt_index", "physical_attempts",
                               "prompt_bytes", "raw_sha256", "at")}
            for r in ban],
    }


def tong_ket_cuoi(thu_muc: Path, dc: dict) -> dict[str, Any]:
    """Bảng đầu ra của lượt đo, ĐÃ áp bản đính chính (§10)."""
    tt = json.loads((thu_muc / "final_scoring.json").read_text("utf-8"))
    a = json.loads((thu_muc / "stage_a_first_attempt.json").read_text("utf-8"))
    am = [c for c in a["cases"] if "NEGATIVE_FAIL_CLOSED" in c["cham"]]
    s = dc["TONG_KET_SUA"]
    return {
        "artifact_schema_version": "1.2",
        "khai": "Tổng kết lượt đo cuối, ĐÃ áp SCORING_CORRECTION. Con số gốc "
                "của cột đáp số giữ nguyên trong `final_scoring.json`.",
        "run_id": thu_muc.name,
        "RUN_VALIDITY": ("VALID" if tt.get("IDENTITY_AFTER_RUN_STABLE")
                         and not tt.get("IDENTITY_AFTER_RUN_DRIFT")
                         else "INVALID_IDENTITY_DRIFT"),
        "APPLICATION_LLM_CALLS": tt["LOGICAL_CALLS"],
        "POSITIVE_CASES": s["POSITIVE_CASES"],
        "NEGATIVE_CASES": len(am),
        "FIRST_ATTEMPT_SERVABLE": tt["FIRST_ATTEMPT_SERVABLE"],
        "ONE_REPAIR_EVENTUAL_SERVABLE": tt["RECOVERY_WITHIN_ONE_REPAIR"],
        "FINAL_SERVABLE": s["FINAL_SERVABLE"],
        "EXACT_ANSWER_PASS": s["EXACT_ANSWER_PASS"],
        "ORACLE_NUMERIC_AGREEMENT_PASS": s["ORACLE_NUMERIC_AGREEMENT_PASS"],
        "NEGATIVE_FAIL_CLOSED": s["NEGATIVE_FAIL_CLOSED"],
        "TARGET_BOUNDARY_PASS": sum(
            1 for c in am if c["cham"].get("TARGET_BOUNDARY_PASS")),
        "SILENT_WRONG_ANSWER_COUNT": s["SILENT_WRONG_ANSWER_COUNT"],
        "UNHANDLED_EXCEPTION_COUNT": 0,
        "verdicts": tt["verdicts"],
        "PRODUCT_PROMOTION_ELIGIBLE": "NO",
        "STABILITY_UNDER_ACCEPTANCE": "NOT_MEASURED",
        "vi_sao_khong_nang_san_pham": (
            "Một ca mỗi họ, chạy một lần. `requires_stability_measured` của "
            "policy không thoả được — kết luận ĐÃ BIẾT TRƯỚC lượt đo, không "
            "phải suy từ kết quả."),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("thu_muc")
    a = p.parse_args()
    from acceptance_integrity import ghi_artifact

    thu_muc = Path(a.thu_muc)
    d = cham_lai(thu_muc)
    for ten, noi_dung in (("SCORING_CORRECTION.json", d),
                          ("FINAL_SUMMARY.json", tong_ket_cuoi(thu_muc, d)),
                          ("TELEMETRY_BUDGET_LEDGER.json",
                           so_telemetry(thu_muc))):
        f = thu_muc / ten
        if f.exists():
            f.unlink()          # bản đính chính là ẢNH CHỤP, ghi lại được
        ghi_artifact(f, noi_dung)
    fh = thu_muc / "ARTIFACT_HASHES.json"
    if fh.exists():
        fh.unlink()
    ghi_artifact(fh, bang_bam(thu_muc))

    print("ĐÍNH CHÍNH CỘT ĐÁP SỐ — 0 lượt gọi model\n")
    print(f"  {'ca':<40} {'servable':<9} {'GỐC':<7} {'SỬA':<7} đáp số")
    for cid, v in d["cases"].items():
        so = " · ".join(f"{q['witness_model']}={q['actual_display']}"
                        for q in v["quantities_SUA"].values())
        print(f"  {cid:<40} {str(v['SERVABLE']):<9} "
              f"{str(v['EXACT_ANSWER_MATCH_GOC']):<7} "
              f"{str(v['EXACT_ANSWER_MATCH_SUA']):<7} {so}")
    print()
    for k, v in d["TONG_KET_SUA"].items():
        print(f"  {k:34} {v}")
    print(f"\n  SILENT_WRONG_ANSWER_COUNT  GỐC {d['TONG_KET_GOC']['SILENT_WRONG_ANSWER_COUNT']}"
          f"  →  SỬA {d['TONG_KET_SUA']['SILENT_WRONG_ANSWER_COUNT']}")
    print(f"\n→ {thu_muc / 'SCORING_CORRECTION.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
