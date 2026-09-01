# -*- coding: utf-8 -*-
"""NAME_ONLY_CONTRACT_LIVE_PROBE — `tên<T>` có đổi được cách mô hình VIẾT?

    đề mới → analyze → ĐÚNG MỘT lượt tổng hợp → chuỗi cổng tất định

⚠️ **TIÊU QUOTA THẬT.** Trần TUYỆT ĐỐI 8 lượt: 4 analyze + 4 tổng hợp.
**KHÔNG SỬA** (§19) — lượt thứ hai bị chặn TRƯỚC khi gửi, 0 token.

─── HAI CÂU, VÀ CHÚNG KHÔNG ĐƯỢC GỘP ──────────────────────────────────────

  A. `RAW_CONTRACT_COMPLIANT` — mô hình tự viết đúng ĐỊNH DANH ở đầu ra THÔ?
  B. `ONE_SHOT_CORRECT` — chương trình qua trọn chuỗi cổng sau chuẩn hoá?

Một chương trình có thể A = NO mà B = YES nhờ chuẩn hoá tất định. Đó là kết
quả HỢP LỆ và phải báo đúng — gọi nó là "raw-compliant" là tự khen bộ chuẩn
hoá bằng điểm của mô hình.

    .venv/Scripts/python.exe scripts/run_name_contract_probe.py --dry-run
    ALLOW_LIVE_AI=1 … scripts/run_name_contract_probe.py --out-dir <thư mục>
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
GOC = BE.parent

from app.ai import pipeline as PL  # noqa: E402
from app.ai.gemini import load_skill  # noqa: E402
from app.ai.telemetry import reset_usage, total_tokens, usage_report  # noqa: E402
from app.simulation.semantic_program import coercion_stats as CS  # noqa: E402
from app.simulation.semantic_program.domain_profile import (  # noqa: E402
    DOMAIN_HINH_HOC,
)
from app.simulation.semantic_program.grammar_card import grammar_card  # noqa: E402
from app.simulation.semantic_program.hoisting import TIEN_TO_TAM  # noqa: E402
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from scripts.capture_stability_seed import (  # noqa: E402
    _bam, _cham_repeat1, bam_payload, payload_chuan_tac,
)
from scripts.name_contract_probe_cases import CASES, check_contamination  # noqa: E402
from scripts.name_slot_classifier import (  # noqa: E402
    phan_loai_o_ten, toa_do_ky_hieu,
)

TRAN = 8
_SKILL = "geometry_program_generator"


def tien_kiem() -> list[str]:
    """Điều kiện TRƯỚC khi tiêu một lượt nào. Thiếu một cái là dừng."""
    loi = []
    if os.environ.get("ALLOW_LIVE_AI") != "1":
        loi.append("thiếu ALLOW_LIVE_AI=1")
    if not (BE / ".env").exists():
        loi.append("thiếu backend/.env")
    if (b := check_contamination()):
        loi += [f"NHIỄM CHÉO: {x}" for x in b]
    r = subprocess.run(["git", "status", "--porcelain"], cwd=GOC,
                       capture_output=True, text=True)
    if r.stdout.strip():
        loi.append("CÂY BẨN — probe đòi cây sạch để artifact gắn được vào mã")
    return loi


class _Nhat:
    """Quan sát viên của `stage_semantic_program`.

    ⚠️ Giao diện là `emit(event_type, data)`, KHÔNG phải `__call__`. Bản đầu
    của một runner trước dùng `__call__` và **vỡ giữa lượt live sau 6 lượt
    provider, không ghi được artifact nào**. Ghi lại ở đây vì cái giá đã trả
    một lần rồi.
    """

    def __init__(self) -> None:
        self.raws: list[str] = []
        self.events: list[dict] = []

    def emit(self, event_type: str, data: dict) -> None:
        self.events.append({"event": event_type, **(data or {})})


async def _mot_de(case: dict, api_key: str, con_lai: int) -> dict:
    reset_usage()
    CS.reset_coercion()
    dem = {"analyze": 0, "th": 0}
    nhat = _Nhat()
    t0 = time.monotonic()
    goc = PL.call_gemini
    pha = {"ten": "ANALYZE"}
    chup: dict = {}

    async def bao(k_, sysp, user, schema=None, temp=0.2, image=None):
        if pha["ten"] == "ANALYZE":
            if dem["analyze"] >= 1 or con_lai < 1:
                raise RuntimeError("chạm trần — dừng TRƯỚC khi gửi, 0 token")
            dem["analyze"] += 1
            return await goc(k_, sysp, user, schema, temp, image)
        # ── ĐÚNG MỘT lượt tổng hợp (§19). Chặn TRƯỚC khi gửi ─────────────
        if dem["th"] >= 1 or dem["analyze"] + dem["th"] >= con_lai:
            raise RuntimeError("KHÔNG SỬA — dừng TRƯỚC khi gửi, 0 token")
        dem["th"] += 1
        chup["payload"] = payload_chuan_tac(sysp, user, schema, temp)
        kq = await goc(k_, sysp, user, schema, temp, image)
        nhat.raws.append(kq if isinstance(kq, str) else repr(kq))
        return kq

    ghi: dict = {k: case[k] for k in
                 ("topology", "capability_mix", "name_slot_families",
                  "dependency_depth", "obligation_count")}
    ghi.update({"case_id": case["id"], "problem_text": case["de"],
                "problem_hash": _bam(case["de"])})

    PL.call_gemini = bao
    try:
        contract, aerr = await PL.stage_semantic_analyze(
            case["de"], api_key, domain=DOMAIN_HINH_HOC)
        if contract is None:
            return {**ghi, "class": "SYSTEM_FAILURE", "stage": "ANALYZE",
                    "taxonomy": "PROVIDER", "error": aerr,
                    "provider_calls": dem["analyze"], "synthesis_calls": 0,
                    "analyze_calls": dem["analyze"]}
        pha["ten"] = "SYNTHESIS"
        try:
            await PL.stage_semantic_program(
                case["de"], {}, api_key, contract, observer=nhat,
                domain=DOMAIN_HINH_HOC)
        except RuntimeError:
            pass          # trần lượt sửa — CHỜ ĐỢI, không phải lỗi hệ
    finally:
        PL.call_gemini = goc

    # ── §3 — artifact chạy lại được, ghi NGAY ────────────────────────────
    raw_hd = contract.model_dump(mode="json")
    ghi["analyze"] = {
        "raw_request_contract": raw_hd,
        "request_contract_hash": _bam(contract.model_dump_json()),
        "roundtrip_ok": RequestContract.model_validate(
            raw_hd).model_dump(mode="json") == raw_hd,
        "input_facts": len(contract.input_facts),
        "obligations": sorted({o.kind for o in contract.obligations})}
    ghi["synthesis_input"] = {
        "canonical_domain": DOMAIN_HINH_HOC, "selected_skill": _SKILL,
        "skill_hash": _bam(load_skill(_SKILL)),
        "model_card_hash": _bam(grammar_card(DOMAIN_HINH_HOC)),
        "payload": chup.get("payload"),
        "model_input_hash": (bam_payload(chup["payload"])
                             if chup.get("payload") else None)}

    u = usage_report()
    ghi.update({
        "analyze_calls": dem["analyze"], "synthesis_calls": dem["th"],
        "repair_calls": 0,
        "provider_calls": dem["analyze"] + dem["th"],
        "analyze_tokens": (u.get("semantic_analyze") or {}).get("total_tokens", 0),
        "total_tokens": total_tokens(),
        "latency_s": round(time.monotonic() - t0, 2),
        "attempts_log": nhat.events, "programs": nhat.raws})
    ghi["synthesis_tokens"] = ghi["total_tokens"] - ghi["analyze_tokens"]

    if not nhat.raws:
        return {**ghi, "class": "SYSTEM_FAILURE", "stage": "NO_OUTPUT",
                "taxonomy": "PROVIDER"}

    raw = nhat.raws[0]
    try:
        raw_json = json.loads(raw)
    except ValueError:
        raw_json = None

    # ── §10/§11 — ô TÊN của bản THÔ, trước mọi phép chuẩn hoá ────────────
    o = (phan_loai_o_ten(raw_json) if isinstance(raw_json, dict)
         else {"tong": 0, "dem": {}, "chi_tiet": []})
    ghi["raw_name_slots"] = o
    ghi["raw_contract_compliant"] = bool(
        o["tong"] and o["dem"].get("RAW_NAME", 0) == o["tong"])
    ghi["symbolic_coordinates"] = (toa_do_ky_hieu(raw_json)
                                   if isinstance(raw_json, dict) else [])

    # ── §16 — chấm chuỗi cổng trên bản đã chuẩn hoá ──────────────────────
    #
    # ⚠️ ĐẶT LẠI BỘ ĐẾM GỘP NGAY TRƯỚC LƯỢT CHẤM. Chương trình thô được thẩm
    # định HAI lần trong một ca — một lần bên trong `stage_semantic_program`,
    # một lần ở đây — nên `VAR_UNWRAPS` cộng dồn gấp đôi. Lượt chạy khô báo 6
    # trên 3 ô bọc `var`; đó là con số sẽ đi thẳng vào báo cáo nếu không chạy
    # khô. Đo MỘT lượt chuẩn hoá của bản thô, đúng thứ §12 hỏi.
    CS.reset_coercion()
    cham = _cham_repeat1(raw, contract, case)
    chuan = cham.pop("normalized_program", None)
    ghi["initial"] = cham
    ghi["normalized_program"] = chuan

    # ── §12 — bộ chuẩn hoá đã làm gì ─────────────────────────────────────
    temps = ([d["name"] for d in (chuan.get("memory_declarations") or [])
              if str(d.get("name", "")).startswith(TIEN_TO_TAM)]
             + [s["target_var"] for s in (chuan.get("statements") or [])
                if str(s.get("target_var", "")).startswith(TIEN_TO_TAM)]
             ) if chuan else []
    ghi["normalizer"] = {
        "VAR_UNWRAPS": CS.coercion_report().get(CS.LOP_GEOMETRY_REF, 0),
        "EXPR_HOISTS": o["dem"].get("NESTED_DERIVED_EXPR", 0),
        "SYNTHETIC_TEMPS_CREATED": len(set(temps)),
        # "Cứu" = bản THÔ không đúng hợp đồng nhưng bản chuẩn hoá đi hết cổng.
        "NORMALIZER_RESCUED_PROGRAM": bool(
            not ghi["raw_contract_compliant"] and cham.get("correct")),
    }
    ghi["class"] = ("ONE_SHOT_CORRECT" if cham.get("correct")
                    else f"FAIL_{cham.get('taxonomy') or 'UNKNOWN'}")
    ghi["stage"] = cham.get("stage")
    ghi["taxonomy"] = cham.get("taxonomy")
    return ghi


def _tong_hop(cases: list[dict]) -> dict:
    def dem(*l):
        return sum(1 for c in cases if c.get("class") in l)

    o_tong = sum((c.get("raw_name_slots") or {}).get("tong", 0) for c in cases)
    loai = {}
    for k in ("RAW_NAME", "WRAPPED_VAR", "NESTED_DERIVED_EXPR",
              "RAW_LITERAL", "WRONG_TYPE"):
        loai[k] = sum((c.get("raw_name_slots") or {}).get("dem", {}).get(k, 0)
                      for c in cases)
    dung = dem("ONE_SHOT_CORRECT")
    tok = sum(c.get("total_tokens", 0) for c in cases)
    return {
        "ONE_SHOT_CORRECT": f"{dung}/{len(cases)}",
        "RAW_CONTRACT_COMPLIANT_PROGRAMS":
            f"{sum(1 for c in cases if c.get('raw_contract_compliant'))}/{len(cases)}",
        "TOTAL_NAME_SLOTS_EMITTED": o_tong,
        **{f"{k}_SLOTS": v for k, v in loai.items()},
        "RAW_NAME_COMPLIANCE_RATE":
            round(loai["RAW_NAME"] / o_tong, 4) if o_tong else None,
        "VAR_UNWRAPS": sum((c.get("normalizer") or {}).get("VAR_UNWRAPS", 0)
                           for c in cases),
        "EXPR_HOISTS": sum((c.get("normalizer") or {}).get("EXPR_HOISTS", 0)
                           for c in cases),
        "SYNTHETIC_TEMPS_CREATED": sum(
            (c.get("normalizer") or {}).get("SYNTHETIC_TEMPS_CREATED", 0)
            for c in cases),
        "NORMALIZER_RESCUED_PROGRAMS": sum(
            1 for c in cases
            if (c.get("normalizer") or {}).get("NORMALIZER_RESCUED_PROGRAM")),
        "STATIC_FAILURE": f"{dem('FAIL_STATIC_VALIDATION')}/{len(cases)}",
        "RUNTIME_FAILURE": f"{dem('FAIL_RUNTIME')}/{len(cases)}",
        "SYSTEM_FAILURE": f"{dem('SYSTEM_FAILURE', 'FAIL_SYSTEM')}/{len(cases)}",
        "RAW_GEOMETRY_LITERAL_ATTEMPTS": loai["RAW_LITERAL"],
        "SYMBOLIC_COORDINATE_CASES": [
            c["case_id"] for c in cases if c.get("symbolic_coordinates")],
        "ANALYZE_CALLS": sum(c.get("analyze_calls", 0) for c in cases),
        "INITIAL_SYNTHESIS_CALLS": sum(c.get("synthesis_calls", 0) for c in cases),
        "REPAIR_CALLS": 0,
        "TOTAL_PROVIDER_CALLS": sum(c.get("provider_calls", 0) for c in cases),
        "ANALYZE_TOKENS": sum(c.get("analyze_tokens", 0) for c in cases),
        "SYNTHESIS_TOKENS": sum(c.get("synthesis_tokens", 0) for c in cases),
        "TOTAL_TOKENS": tok,
        "TOKENS_PER_CORRECT_INITIAL_IR": round(tok / dung, 1) if dung else None,
        "ARTIFACT_REPLAYABLE":
            f"{sum(1 for c in cases if (c.get('analyze') or {}).get('roundtrip_ok') and (c.get('synthesis_input') or {}).get('model_input_hash'))}/{len(cases)}",
    }


def tu_kiem(dich: Path) -> dict:
    """§3 — nạp artifact TỪ ĐĨA, dựng lại đầu vào, so hash. 0 provider."""
    from scripts.capture_stability_seed import dung_lai_payload

    d = json.loads(dich.read_text(encoding="utf-8"))
    ra = {"tu_chua": 0, "dung_lai": 0, "tong": len(d["cases"])}
    for c in d["cases"]:
        si = c.get("synthesis_input") or {}
        p = si.get("payload")
        if p and bam_payload(p) == si.get("model_input_hash"):
            ra["tu_chua"] += 1
        try:
            lai = dung_lai_payload(c)
            if lai and bam_payload(lai) == si.get("model_input_hash"):
                ra["dung_lai"] += 1
        except Exception:  # noqa: BLE001
            pass
    return ra


def _provider_gia(case_theo_de: dict):
    """Provider GIẢ cho `--dry-run`: 0 token, nhưng đi đúng đường mã thật.

    ─── VÌ SAO BẮT BUỘC CHẠY KHÔ TRƯỚC ─────────────────────────────────────

    Hai wave gần nhất đều **vỡ giữa lượt live vì lỗi BỘ ĐO**, không phải lỗi
    hệ: một lần dùng `__call__` thay `emit` (mất 6 lượt, 0 artifact), một lần
    giả định `translate.vector` là chuỗi rồi gặp dict (mất 5 lượt). Cả hai
    đáng lẽ chết trong 3 giây ở một lượt chạy khô.

    Bản giả cố ý phát chương trình **SAI HÌNH DẠNG WIRE**: lồng
    `vector_from_points` vào một ô TÊN và bọc `var` quanh một tên khác — tức
    ép đúng hai nhánh mà bộ đo dễ vỡ nhất, và bắt chúng phải cho ra một ca
    `raw_contract_compliant = False` mà vẫn `ONE_SHOT_CORRECT`.
    """
    async def gia(k_, sysp, user, schema=None, temp=0.2, image=None):
        case = next((c for c in CASES if c["de"][:60] in user), CASES[0])
        if schema and "input_facts" in json.dumps(schema):
            return json.dumps({
                "input_facts": [{"id": "f1", "kind": "float",
                                 "label": "toạ độ đề cho", "value": ["0"]}],
                "obligations": [{"kind": "distance", "container": "A"}],
            }, ensure_ascii=False)
        return json.dumps(case_theo_de[case["id"]], ensure_ascii=False)

    return gia


def _lam_sai_hinh_dang(spec: dict) -> dict:
    """Bản chuẩn tắc, viết lại cho SAI HÌNH DẠNG mà vẫn ĐÚNG NGHĨA."""
    import copy

    d = copy.deepcopy(spec)
    ten_vec = {s["target_var"]: s["expr"] for s in d["statements"]
               if s.get("kind") == "assign"
               and (s.get("expr") or {}).get("kind") == "vector_from_points"}
    st = []
    for s in d["statements"]:
        if s.get("kind") == "assign" and s.get("target_var") in ten_vec:
            continue                     # bỏ câu lệnh, đem biểu thức vào chỗ dùng
        if (s.get("kind") == "construct_point"
                and (s.get("expr") or {}).get("kind") == "translate"
                and s["expr"].get("vector") in ten_vec):
            s = {**s, "expr": {**s["expr"],
                               "vector": ten_vec[s["expr"]["vector"]]}}
        elif s.get("kind") == "construct_line":
            s = {**s, "through_a": {"kind": "var", "name": s["through_a"]}}
        st.append(s)
    d["statements"] = st
    return d


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="docs/evaluation/geometry/name-contract-probe")
    ap.add_argument("--dry-run", action="store_true",
                    help="chạy KHÔ với provider giả — 0 token, kiểm bộ đo")
    ns = ap.parse_args()

    if not ns.dry_run:
        if (loi := tien_kiem()):
            print("DỪNG TRƯỚC KHI TIÊU QUOTA:")
            for x in loi:
                print("  ·", x)
            return 2
        from dotenv import load_dotenv
        load_dotenv(BE / ".env")
    else:
        PL.call_gemini = _provider_gia(
            {c["id"]: _lam_sai_hinh_dang(c["chuan_tac"]) for c in CASES})
    key = os.environ.get("GEMINI_API_KEY", "dry")

    from app.main import CACHE_VERSION
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=GOC,
                         capture_output=True, text=True).stdout.strip()
    sach = not subprocess.run(["git", "status", "--porcelain"], cwd=GOC,
                              capture_output=True, text=True).stdout.strip()

    ket: list[dict] = []
    da_dung = 0
    for c in CASES:
        con = TRAN - da_dung
        if con < 2:
            print(f"  {c['id']}: BỎ QUA — còn {con} lượt, cần 2")
            break
        r = await _mot_de(c, key, con)
        da_dung += r.get("provider_calls", 0)
        ket.append(r)
        print(f"  {r['case_id']:32s} {r.get('class'):24s} "
              f"raw_compliant={r.get('raw_contract_compliant')} "
              f"ô={((r.get('raw_name_slots') or {}).get('tong'))} "
              f"lượt={r.get('provider_calls')}  tổng={da_dung}/{TRAN}")

    tong = _tong_hop(ket)
    dich = GOC / ns.out_dir / "probe.json"
    if dich.exists() and not ns.dry_run:
        print(f"TỪ CHỐI ghi đè artifact cũ: {dich}")
        return 3
    dich.parent.mkdir(parents=True, exist_ok=True)
    dich.write_text(json.dumps({
        "khai": "NAME_ONLY_CONTRACT_LIVE_PROBE. RAW vs NORMALIZED tách rời — "
                "một chương trình có thể raw KHÔNG đúng hợp đồng mà vẫn "
                "ONE_SHOT_CORRECT nhờ chuẩn hoá tất định.",
        "probe_id": "NAME_ONLY_CONTRACT_LIVE_PROBE",
        "chayLuc": datetime.now(timezone.utc).isoformat(),
        "frozen_commit": sha, "cay_sach": sach,
        "cache_version": CACHE_VERSION,
        "prompt_hash": _bam(load_skill(_SKILL)),
        "model_card_hash": _bam(grammar_card(DOMAIN_HINH_HOC)),
        "probe_seal": _bam("|".join(c["id"] + c["de"] for c in CASES)),
        "contamination": check_contamination() or "SACH",
        "provider_call_hard_cap": TRAN,
        "dry_run": ns.dry_run,
        **tong, "cases": ket,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n→ {dich}")
    for k, v in tong.items():
        print(f"  {k:34s} {v}")
    if not ns.dry_run:
        print("  TU_KIEM (0 provider):", tu_kiem(dich))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
