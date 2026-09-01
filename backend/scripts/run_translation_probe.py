# -*- coding: utf-8 -*-
"""FRESH_TRANSLATION_COMPOSITION_PROBE — mô hình có TỰ TÌM RA `translate`?

    đề mới → analyze → tổng hợp (1 + tối đa 1 sửa) → chuỗi cổng tất định

⚠️ **TIÊU QUOTA THẬT.** Trần 12 lượt: 4 analyze + 4 tổng hợp + tối đa 4 sửa.

─── CÂU HỎI, VÀ NÓ HẸP ────────────────────────────────────────────────────

Gặp bài mới cần dời một điểm theo một vectơ, mô hình có tự chọn
`translate(point, vector)` và ghép nó với các phép dựng khác không?

⚠️ Tịnh tiến **KHÔNG BẮT BUỘC** trong IR này — `divide_segment(R,
midpoint(P,S), 2)` cho cùng kết quả, và đường ấy đã mở từ trước khi `translate`
tồn tại (xem đính chính ở `STATUS_LEDGER`). Nên probe đo *"chọn gì khi cả hai
đường đều mở"*, không đo *"có làm nổi không"*.

─── ARTIFACT CHẠY LẠI ĐƯỢC NGAY TỪ LƯỢT ĐẦU (§8) ──────────────────────────

Bài học từ `CLEAN_BASELINE_V2`: một lượt đo đã tiêu 13 lượt provider hoá ra
không kiểm lại được vì hợp đồng chỉ được ghi dưới dạng TÓM TẮT. Ở đây hợp đồng
lưu nguyên (`raw`), payload chuẩn tắc lưu nguyên, và cả hai phải round-trip.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
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
from app.simulation.semantic_program.domain_profile import (  # noqa: E402
    DOMAIN_HINH_HOC,
    program_skill_for,
)
from app.simulation.semantic_program.grammar_card import grammar_card  # noqa: E402
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from scripts.capture_stability_seed import (  # noqa: E402
    _bam,
    _cham_repeat1,
    bam_payload,
    payload_chuan_tac,
)
from scripts.translation_probe_cases import CASES, check_contamination  # noqa: E402

TRAN = 12
_SKILL = "geometry_program_generator"
#: §19 — không được có nhánh theo DẠNG BÀI ở mã sản phẩm.
_CAM_DANG_BAI = ("prism", "parallelogram", "lang_tru", "binh_hanh",
                 "hop_chu_nhat", "lap_phuong")


def _dang_tinh_tien(raw: str) -> dict:
    """§12/§14 — mô hình dùng gì, và có ghép vectơ vào tịnh tiến không."""
    ra = {"translate_count": 0, "translate_targets": [],
          "vector_producers": {}, "construct_point_targets": [],
          "arith_point_vector": 0, "vector_to_translate": 0,
          "translated_used_downstream": []}
    try:
        p = json.loads(raw)
    except Exception:  # noqa: BLE001
        return ra
    stmts = [s for s in (p.get("statements") or []) if isinstance(s, dict)]
    for s in stmts:
        e = s.get("expr") or {}
        if s.get("kind") == "construct_point":
            ra["construct_point_targets"].append(s.get("target_var"))
            if e.get("kind") == "arith":
                ra["arith_point_vector"] += 1
        if e.get("kind") == "translate":
            ra["translate_count"] += 1
            ra["translate_targets"].append(s.get("target_var"))
        if e.get("kind") == "vector_from_points":
            ra["vector_producers"][s.get("target_var")] = "vector_from_points"

    # §14 — vectơ do `vector_from_points` sinh có được `translate` tiêu thụ?
    for s in stmts:
        e = s.get("expr") or {}
        if e.get("kind") == "translate" and e.get("vector") in ra["vector_producers"]:
            ra["vector_to_translate"] += 1

    # §15 — điểm tịnh tiến có được dùng TIẾP không?
    tt = set(ra["translate_targets"])
    van = json.dumps({"s": [s for s in stmts
                            if (s.get("expr") or {}).get("kind") != "translate"]},
                     ensure_ascii=False)
    ra["translated_used_downstream"] = sorted(
        t for t in tt if t and f'"{t}"' in van)
    return ra


def _phan_loai_tt(d: dict, can_tt: bool) -> str:
    if d["translate_count"]:
        return "TRANSLATE_SELECTED_CORRECTLY"
    if d["arith_point_vector"]:
        return "ARITH_POINT_VECTOR_REAPPEARED"
    return "TRANSLATE_NOT_SELECTED" if can_tt else "TRANSLATE_KHONG_CAN"


def tien_kiem() -> list[str]:
    loi = []
    try:
        if program_skill_for(DOMAIN_HINH_HOC) != _SKILL:
            loi.append("skill tổng hợp không phải bản hình học")
    except Exception as e:  # noqa: BLE001
        return [f"program_skill_for ném: {e}"]
    the = grammar_card(DOMAIN_HINH_HOC)
    if "translate: point:tên vector:tên" not in the:
        loi.append("thẻ hình học KHÔNG quảng cáo `translate`")
    # §19 — quét mã SẢN PHẨM tìm nhánh theo dạng bài.
    from tests.source_scan import than_ma

    for f in sorted((BE / "app").rglob("*.py")):
        try:
            than = than_ma(f).lower()
        except Exception:  # noqa: BLE001
            continue
        for tu in _CAM_DANG_BAI:
            if tu in than:
                loi.append(f"§19 nhánh theo DẠNG BÀI trong {f.name}: {tu!r}")
    return loi


class _Nhat:
    def __init__(self) -> None:
        self.events: list[dict] = []
        self.raws: list[str] = []
        self.tokens: list[int] = []

    def emit(self, event_type: str, data: dict) -> None:
        if event_type == "semantic_program_attempt":
            self.events.append({
                "attempt_index": data.get("n", 0), "gate": data.get("gate"),
                "repairable": data.get("repairable", True),
                "message": (data.get("message") or "")[:500]})


async def _mot_de(case: dict, api_key: str, con_lai: int) -> dict:
    reset_usage()
    dem = {"analyze": 0, "th": 0}
    nhat = _Nhat()
    t0 = time.monotonic()
    goc = PL.call_gemini
    pha = {"ten": "ANALYZE"}
    chup: dict = {}

    async def bao(k_, sysp, user, schema=None, temp=0.2, image=None):
        if pha["ten"] == "ANALYZE":
            dem["analyze"] += 1
            return await goc(k_, sysp, user, schema, temp, image)
        if dem["th"] >= 2 or dem["th"] >= con_lai:
            raise RuntimeError("chạm trần — dừng TRƯỚC khi gửi, 0 token")
        dem["th"] += 1
        if dem["th"] == 1:
            chup["payload"] = payload_chuan_tac(sysp, user, schema, temp)
        truoc = total_tokens()
        kq = await goc(k_, sysp, user, schema, temp, image)
        nhat.raws.append(kq if isinstance(kq, str) else repr(kq))
        nhat.tokens.append(total_tokens() - truoc)
        return kq

    ghi: dict = {k: case[k] for k in
                 ("topology", "capability_mix", "translation_required",
                  "translation_useful", "duong_vong",
                  "translated_point_count", "dependency_depth",
                  "obligation_count")}
    ghi.update({"case_id": case["id"], "problem_text": case["de"],
                "problem_hash": _bam(case["de"])})

    PL.call_gemini = bao
    try:
        contract, aerr = await PL.stage_semantic_analyze(
            case["de"], api_key, domain=DOMAIN_HINH_HOC)
        if contract is None:
            return {**ghi, "class": "SYSTEM_FAILURE", "stage": "ANALYZE",
                    "taxonomy": "PROVIDER", "error": aerr,
                    "provider_calls": dem["analyze"]}
        pha["ten"] = "SYNTHESIS"
        try:
            spec, serr = await PL.stage_semantic_program(
                case["de"], {}, api_key, contract, observer=nhat,
                domain=DOMAIN_HINH_HOC)
        except RuntimeError as e:
            spec, serr = None, str(e)
    finally:
        PL.call_gemini = goc

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
        "repair_calls": max(dem["th"] - 1, 0),
        "provider_calls": dem["analyze"] + dem["th"],
        "analyze_tokens": (u.get("semantic_analyze") or {}).get("total_tokens", 0),
        "initial_synthesis_tokens": (nhat.tokens or [0])[0],
        "repair_tokens": sum(nhat.tokens[1:]),
        "total_tokens": total_tokens(),
        "latency_s": round(time.monotonic() - t0, 2),
        "attempts_log": nhat.events, "programs": nhat.raws})

    # ── §10 — LƯỢT ĐẦU chấm ĐỘC LẬP với việc pipeline có sửa tiếp không ──
    can_tt = bool(case.get("translation_useful"))
    if nhat.raws:
        d0 = _dang_tinh_tien(nhat.raws[0])
        ghi["initial"] = {**_cham_repeat1(nhat.raws[0], contract, case),
                          "translate": d0,
                          "phan_loai": _phan_loai_tt(d0, can_tt)}
        ghi["initial"].pop("normalized_program", None)
    else:
        ghi["initial"] = {"correct": False, "stage": "NO_OUTPUT",
                          "taxonomy": "PROVIDER"}

    if spec is None:
        cuoi = _dang_tinh_tien(nhat.raws[-1]) if nhat.raws else {}
        return {**ghi, "class": "FAIL_AFTER_REPAIR", "stage": "SYNTHESIS",
                "error": serr, "translate_cuoi": cuoi,
                "taxonomy": (ghi["initial"].get("taxonomy") or "SYNTHESIS")}

    cuoi = _cham_repeat1(nhat.raws[-1], contract, case)
    d1 = _dang_tinh_tien(nhat.raws[-1])
    ghi["final"] = {**cuoi, "translate": d1,
                    "phan_loai": _phan_loai_tt(d1, can_tt)}
    ghi["final"].pop("normalized_program", None)
    ghi["normalized_program"] = spec.model_dump(mode="json")
    if not cuoi["correct"]:
        return {**ghi, "class": "EXECUTABLE_BUT_INCORRECT"
                if cuoi.get("runtime_pass") else "FAIL_AFTER_REPAIR",
                "stage": cuoi["stage"], "taxonomy": cuoi["taxonomy"],
                "error": cuoi.get("error")}
    return {**ghi, "stage": "DONE", "taxonomy": None,
            "class": "ONE_SHOT_CORRECT" if dem["th"] == 1
            else "REPAIRED_CORRECT"}


def tu_kiem(dich: Path) -> dict:
    """§8 — nạp artifact TỪ ĐĨA, dựng lại đầu vào, so hash. 0 provider."""
    from scripts.capture_stability_seed import dung_lai_payload

    d = json.loads(dich.read_text(encoding="utf-8"))
    ra = []
    for c in d["cases"]:
        si, an = c.get("synthesis_input") or {}, c.get("analyze") or {}
        m = {"case_id": c["case_id"],
             "raw": bool(an.get("raw_request_contract")),
             "roundtrip": bool(an.get("roundtrip_ok")),
             "payload": bool(si.get("payload"))}
        if not (m["raw"] and m["payload"]):
            ra.append({**m, "tu_chua": False, "dung_lai": False})
            continue
        m["tu_chua"] = bam_payload(si["payload"]) == si["model_input_hash"]
        try:
            m["dung_lai"] = bam_payload(dung_lai_payload(c)) == \
                si["model_input_hash"]
        except Exception:  # noqa: BLE001
            m["dung_lai"] = False
        ra.append(m)
    return {"cases": ra, "replayable": sum(
        1 for x in ra if all(x[k] for k in
                             ("raw", "roundtrip", "payload", "tu_chua",
                              "dung_lai")))}


async def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir",
                   default="../docs/evaluation/geometry/translation-probe")
    p.add_argument("--chi-tien-kiem", action="store_true")
    a = p.parse_args()

    ra = Path(a.out_dir).resolve()
    ra.mkdir(parents=True, exist_ok=True)
    dich = ra / "probe.json"
    if dich.exists():
        print(f"✗ {dich} đã có — bộ đo TỪ CHỐI đè lượt cũ.")
        return 3

    from app.main import CACHE_VERSION

    loi, nhiem = tien_kiem(), check_contamination()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=GOC,
                            capture_output=True, text=True).stdout.strip()
    sach = not subprocess.run(["git", "status", "--porcelain"], cwd=GOC,
                              capture_output=True, text=True).stdout.strip()
    seal = _bam(json.dumps([c["de"] for c in CASES], ensure_ascii=False))
    print("━━ TIỀN KIỂM · FRESH_TRANSLATION_COMPOSITION_PROBE ━━")
    print(f"  commit {commit[:8]} · cây sạch {sach} · CACHE_VERSION "
          f"{CACHE_VERSION}")
    print(f"  prompt {_bam(load_skill(_SKILL))} · thẻ "
          f"{_bam(grammar_card(DOMAIN_HINH_HOC))} · seal {seal}")
    print(f"  nhiễm chéo: {'SẠCH' if not nhiem else nhiem}")
    print(f"  PROBLEM_FAMILY_SPECIAL_CASES: "
          f"{len([x for x in loi if '§19' in x])}")
    if loi or nhiem:
        for x in loi + nhiem:
            print(f"    ✗ {x}")
        return 4
    print("  tiền kiểm: PASS")
    if a.chi_tien_kiem:
        return 0

    if os.getenv("ALLOW_LIVE_AI") != "1":
        print("✗ Cần ALLOW_LIVE_AI=1 — TIÊU QUOTA THẬT.")
        return 2
    try:
        from dotenv import load_dotenv

        load_dotenv(BE / ".env")
    except ImportError:
        pass
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("✗ Thiếu GEMINI_API_KEY.")
        return 2

    ket, da = [], 0
    for c in CASES:
        if da >= TRAN:
            ket.append({"case_id": c["id"], "class": "NOT_RUN"})
            continue
        print(f"\n━━ {c['id']} ━━")
        r = await _mot_de(c, key, TRAN - da)
        da += r.get("provider_calls", 0)
        ket.append(r)
        ini = r.get("initial") or {}
        print(f"  {r.get('class')} · provider {r.get('provider_calls')} "
              f"(sửa {r.get('repair_calls')}) · token {r.get('total_tokens')}")
        print(f"    lượt ĐẦU: {'đúng' if ini.get('correct') else 'hỏng ' + str(ini.get('taxonomy'))}"
              f" · {ini.get('phan_loai')} · translate="
              f"{(ini.get('translate') or {}).get('translate_targets')}")
        if r.get("error"):
            print(f"    {' '.join(str(r['error']).split())[:150]}")

    def dem(*l):
        return sum(1 for r in ket if r.get("class") in l)

    def bo(k):
        return sum(r.get(k, 0) or 0 for r in ket)

    ini = [r.get("initial") or {} for r in ket]
    fin = [r.get("final") or r.get("translate_cuoi") and {"translate": r["translate_cuoi"]} or {}
           for r in ket]
    can_tt = [r for r in ket if r.get("translation_useful")]
    dung = dem("ONE_SHOT_CORRECT", "REPAIRED_CORRECT")
    tok = bo("total_tokens")

    bao = {
        "khai": "FRESH_TRANSLATION_COMPOSITION_PROBE — mô hình có TỰ TÌM RA "
                "`translate` không. ⚠️ Tịnh tiến KHÔNG BẮT BUỘC trong IR này; "
                "probe đo lựa chọn, không đo khả năng.",
        "probe_id": "FRESH_TRANSLATION_COMPOSITION_PROBE",
        "chayLuc": datetime.now(timezone.utc).isoformat(),
        "frozen_commit": commit, "cay_sach": sach, "probe_seal": seal,
        "cache_version": CACHE_VERSION,
        "prompt_hash": _bam(load_skill(_SKILL)),
        "model_card_hash": _bam(grammar_card(DOMAIN_HINH_HOC)),
        "contamination": not nhiem,
        "canonical_executable": f"{len(CASES)}/{len(CASES)}",
        "translation_required_cases": sum(
            1 for r in ket if r.get("translation_required")),
        "translation_useful_cases": len(can_tt),
        "analyze_calls": bo("analyze_calls"),
        "initial_synthesis_calls": sum(
            1 for r in ket if r.get("synthesis_calls")),
        "repair_calls": bo("repair_calls"),
        "total_provider_calls": da, "provider_call_hard_cap": TRAN,
        "one_shot_correct": dem("ONE_SHOT_CORRECT"),
        "repaired_correct": dem("REPAIRED_CORRECT"),
        "correct_within_budget": dung,
        "system_failure": dem("SYSTEM_FAILURE"),
        "synthesis_failure": sum(1 for r in ket
                                 if r.get("taxonomy") == "SYNTHESIS"),
        "translate_selected_initial": sum(
            1 for x in ini if (x.get("translate") or {}).get("translate_count")),
        "translate_selected_after_repair": sum(
            1 for x in fin if (x.get("translate") or {}).get("translate_count")),
        "arith_point_vector_reappeared": sum(
            (x.get("translate") or {}).get("arith_point_vector", 0)
            for x in ini + fin),
        "vector_to_translate_compositions": sum(
            (x.get("translate") or {}).get("vector_to_translate", 0)
            for x in ini),
        "translated_points_used_downstream": sum(
            len((x.get("translate") or {}).get("translated_used_downstream")
                or []) for x in ini),
        "problem_family_special_cases": 0,
        "analyze_tokens": bo("analyze_tokens"),
        "initial_synthesis_tokens": bo("initial_synthesis_tokens"),
        "repair_tokens": bo("repair_tokens"), "total_tokens": tok,
        "tokens_per_correct_executable_ir": round(tok / dung) if dung else None,
        "new_code_required_during_probe": 0,
        "cases": ket,
    }
    dich.write_text(json.dumps(bao, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")

    k = tu_kiem(dich)
    bao["artifact_replayable"] = f"{k['replayable']}/{len(CASES)}"
    bao["self_check"] = k
    dich.write_text(json.dumps(bao, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")

    print("\n━━ KẾT QUẢ ━━")
    print(f"  ONE_SHOT_CORRECT           {bao['one_shot_correct']}/{len(CASES)}")
    print(f"  CORRECT_WITHIN_BUDGET      {dung}/{len(CASES)}")
    print(f"  SYSTEM_FAILURE             {bao['system_failure']}/{len(CASES)}")
    print(f"  TRANSLATE_SELECTED_INITIAL {bao['translate_selected_initial']}"
          f"/{len(CASES)}")
    print(f"  sau sửa                    "
          f"{bao['translate_selected_after_repair']}/{len(CASES)}")
    print(f"  ARITH_POINT_VECTOR_REAPPEARED  "
          f"{bao['arith_point_vector_reappeared']}")
    print(f"  VECTOR→TRANSLATE {bao['vector_to_translate_compositions']} · "
          f"điểm tịnh tiến dùng tiếp {bao['translated_points_used_downstream']}")
    print(f"  provider {da}/{TRAN} · token {tok}")
    print(f"  ARTIFACT_REPLAYABLE        {bao['artifact_replayable']}")
    print(f"\n→ {dich}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
