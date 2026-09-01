# -*- coding: utf-8 -*-
"""SYNTHESIS_STABILITY_K3 — cùng MỘT đầu vào, ba lần sinh. 12 lượt provider.

    R1  đọc từ `stability-seed/seed.json` (KHÔNG gọi lại)
    R2  gọi mới, payload dựng từ artifact, hash phải khớp R1 TRƯỚC KHI GỬI
    R3  như R2

⚠️ **TIÊU QUOTA THẬT.** Trần TUYỆT ĐỐI 12 lượt. Không analyze, không sửa,
không lượt thứ hai cho cùng một repeat.

─── CÂU HỎI, VÀ NÓ HẸP ────────────────────────────────────────────────────

    Với CHÍNH XÁC cùng một đầu vào tổng hợp, mô hình sinh ra chương trình
    đúng ổn định đến mức nào?

Không đo phương sai của `analyze`, không đo khả năng sửa, không đo khái quát
hoá. Sáu đề này mô hình ĐÃ THẤY — chúng là **tập đo độ ổn định**, và gọi chúng
là held-out là nói sai.

─── VÌ SAO GỌI THẲNG `call_gemini` ────────────────────────────────────────

`stage_semantic_program` tự dựng prompt và tự chạy vòng sửa. Đi qua nó thì
đầu vào phụ thuộc mã hiện tại và một lượt hỏng sẽ kéo theo lượt thứ hai —
hai điều wave này cấm. Gọi thẳng biên provider với payload đọc từ artifact là
cách duy nhất giữ được *"chính xác cùng một đầu vào"* thành một khẳng định
kiểm được, không phải một hy vọng.

Không có cache nào trên đường ấy: cache của sản phẩm nằm ở `main.py` quanh
`analyze`, và wave này không gọi `analyze`.

─── ĐIỀU KHÔNG BAO GIỜ ĐI VÀO PAYLOAD ─────────────────────────────────────

Số hiệu repeat, nonce, timestamp. Thêm bất kỳ thứ nào là tự phá điều kiện của
phép đo — và phá theo cách trông vẫn chạy.
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
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
GOC = BE.parent

from app.ai.gemini import call_gemini, load_skill  # noqa: E402
from app.simulation.semantic_program.domain_profile import (  # noqa: E402
    DOMAIN_HINH_HOC,
)
from app.simulation.semantic_program.grammar_card import grammar_card  # noqa: E402
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from scripts.capture_stability_seed import (  # noqa: E402
    _bam,
    _cham_repeat1,
    bam_payload,
    dung_lai_payload,
)
from scripts.clean_baseline_v2_cases import CASES  # noqa: E402

SEED = GOC / "docs" / "evaluation" / "geometry" / "stability-seed" / "seed.json"
TRAN = 12
_SKILL = "geometry_program_generator"
_ORACLE = {c["id"]: c for c in CASES}

#: Hash đóng băng của hạt giống. Lệch ⇒ DỪNG trước API (§4).
_MONG = {"prompt_hash": "b8bb766b4d3dbfc2",
         "model_card_hash": "d409584f6156776b",
         "cache_version": "58"}


def _do_sau(spec) -> int:
    """Độ sâu chuỗi phụ thuộc — vật gốc = 0, vật dựng = 1 + max(nguồn).

    Đo trên CHƯƠNG TRÌNH, không trên đề: hai chương trình cùng đúng có thể
    khác độ sâu, và chính khác biệt ấy là thứ §13 gọi là tổ hợp thay thế.
    """
    from app.simulation.semantic_program.validator import _BIEU_THUC_HINH_HOC
    from app.simulation.semantic_program.ir_static_check import _TOAN_HANG_LENH

    sau: dict[str, int] = {}
    for st in spec.statements:
        tv = getattr(st, "target_var", None)
        if not tv:
            continue
        nguon: list[str] = []
        k = getattr(st, "kind", "")
        if k in _TOAN_HANG_LENH:
            for truong, _, ds in _TOAN_HANG_LENH[k]:
                gt = getattr(st, truong, None)
                nguon += list(gt or ()) if ds else ([gt] if gt else [])
        e = getattr(st, "expr", None)
        ek = getattr(e, "kind", None)
        if ek in _BIEU_THUC_HINH_HOC:
            nguon += [x for x in (getattr(e, f, None)
                                  for f in _BIEU_THUC_HINH_HOC[ek])
                      if isinstance(x, str)]
        sau[tv] = 1 + max([sau.get(n, 0) for n in nguon] or [0])
    return max(sau.values() or [0])


def _hinh_dang(raw: str) -> dict:
    """§9 — hình dạng CẤU TRÚC của một chương trình, đọc trên bản THÔ."""
    from app.simulation.semantic_program.validator import (
        validate_semantic_program,
    )

    ra: dict = {"raw_hash": _bam(raw)}
    try:
        p = json.loads(raw)
    except Exception:  # noqa: BLE001
        return ra
    stmts = [s for s in (p.get("statements") or []) if isinstance(s, dict)]
    ra["statement_count"] = len(stmts)
    ra["primitive_multiset"] = dict(
        Counter(s.get("kind") for s in stmts))
    ra["construct_point_count"] = sum(
        1 for s in stmts if s.get("kind") == "construct_point")
    ra["assign_count"] = sum(1 for s in stmts if s.get("kind") == "assign")
    ra["measure_opcodes"] = sorted({
        (s.get("expr") or {}).get("quantity") for s in stmts
        if (s.get("expr") or {}).get("kind") == "measure"} - {None})
    # §12 — `arith` đặt vào `construct_point`, khuôn đã hỏng ở R1.
    ra["arith_as_point_expr"] = sum(
        1 for s in stmts
        if s.get("kind") == "construct_point"
        and (s.get("expr") or {}).get("kind") == "arith")
    v = validate_semantic_program(p)
    if v.ok:
        ra["normalized_program_hash"] = _bam(json.dumps(
            v.spec.model_dump(mode="json"), ensure_ascii=False, sort_keys=True))
        ra["dependency_depth"] = _do_sau(v.spec)
    return ra


def tien_kiem() -> list[str]:
    loi = []
    if not SEED.exists():
        return ["thiếu `stability-seed/seed.json` — chưa có R1"]
    d = json.loads(SEED.read_text(encoding="utf-8"))
    from app.main import CACHE_VERSION

    hien = {"prompt_hash": _bam(load_skill(_SKILL)),
            "model_card_hash": _bam(grammar_card(DOMAIN_HINH_HOC)),
            "cache_version": CACHE_VERSION}
    for k, v in _MONG.items():
        if hien[k] != v:
            loi.append(f"{k} LỆCH: hạt giống {v}, hiện tại {hien[k]}")
        if d.get(k) != v:
            loi.append(f"{k} trong artifact là {d.get(k)}, mong {v}")
    if not d.get("input_equivalence"):
        loi.append("hạt giống chưa PASS `input_equivalence`")
    if len(d.get("cases") or []) != 6:
        loi.append("hạt giống không đủ 6 ca")
    return loi


async def _mot_repeat(ca_seed: dict, nhan: str, api_key: str) -> dict:
    """Một lượt sinh mới. Hash phải khớp R1 TRƯỚC KHI GỬI (§3)."""
    cid = ca_seed["case_id"]
    mong_hash = ca_seed["synthesis_input"]["model_input_hash"]
    payload = dung_lai_payload(ca_seed)
    hien_hash = bam_payload(payload)

    ghi = {"repeat": nhan, "model_input_hash": hien_hash,
           "model_input_hash_r1": mong_hash,
           "input_hash_match": hien_hash == mong_hash}
    if not ghi["input_hash_match"]:
        # DỪNG TRƯỚC KHI GỬI. Không "chuẩn hoá thêm" để ép khớp — làm thế là
        # sửa phép đo cho vừa kết quả.
        return {**ghi, "sent": False, "correct": False,
                "taxonomy": "SYSTEM",
                "error": "đầu vào lệch R1 — dừng trước khi gửi"}

    t0 = time.monotonic()
    raw = await call_gemini(api_key, payload["system_prompt"],
                            payload["user_text"], payload["response_schema"],
                            payload["temperature"])
    ghi.update({"sent": True, "cache_hit": False,
                "provider_call_confirmed": True,
                "latency_s": round(time.monotonic() - t0, 2)})

    hd = RequestContract.model_validate(
        ca_seed["analyze"]["raw_request_contract"])
    cham = _cham_repeat1(raw, hd, _ORACLE[cid])
    hinh = _hinh_dang(raw if isinstance(raw, str) else repr(raw))
    return {**ghi, "raw_output": raw, **hinh,
            "correct": cham["correct"], "stage": cham["stage"],
            "taxonomy": cham["taxonomy"], "error": cham.get("error"),
            "checker": cham.get("checker")}


def _r1_tu_seed(ca: dict) -> dict:
    r = ca["repeat_1"]
    hinh = _hinh_dang(r["raw_output"]) if r.get("raw_output") else {}
    return {"repeat": "R1", "sent": False, "from_seed": True,
            "model_input_hash": ca["synthesis_input"]["model_input_hash"],
            "model_input_hash_r1": ca["synthesis_input"]["model_input_hash"],
            "input_hash_match": True, **hinh,
            "correct": bool(r.get("correct")), "stage": r.get("stage"),
            "taxonomy": r.get("taxonomy"), "error": r.get("error"),
            "checker": r.get("checker")}


async def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir",
                   default="../docs/evaluation/geometry/stability-k3")
    p.add_argument("--chi-tien-kiem", action="store_true")
    a = p.parse_args()

    ra = Path(a.out_dir).resolve()
    ra.mkdir(parents=True, exist_ok=True)
    dich = ra / "stability.json"
    if dich.exists():
        print(f"✗ {dich} đã có — bộ đo TỪ CHỐI đè lượt cũ.")
        return 3

    loi = tien_kiem()
    from app.main import CACHE_VERSION

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=GOC,
                            capture_output=True, text=True).stdout.strip()
    sach = not subprocess.run(["git", "status", "--porcelain"], cwd=GOC,
                              capture_output=True, text=True).stdout.strip()
    print("━━ TIỀN KIỂM · SYNTHESIS_STABILITY_K3 ━━")
    print(f"  commit {commit[:8]} · cây sạch {sach} · CACHE_VERSION "
          f"{CACHE_VERSION}")
    print(f"  prompt {_bam(load_skill(_SKILL))} · thẻ "
          f"{_bam(grammar_card(DOMAIN_HINH_HOC))}")
    if loi:
        for x in loi:
            print(f"    ✗ {x}")
        return 4
    print("  khớp hạt giống: PASS")
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

    seed = json.loads(SEED.read_text(encoding="utf-8"))
    ket, da_dung = [], 0
    for ca in seed["cases"]:
        cid = ca["case_id"]
        print(f"\n━━ {cid} ━━")
        lan = [_r1_tu_seed(ca)]
        print(f"  R1 (hạt giống) {'ĐÚNG' if lan[0]['correct'] else 'HỎNG ' + str(lan[0]['taxonomy'])}")
        for nhan in ("R2", "R3"):
            if da_dung >= TRAN:
                lan.append({"repeat": nhan, "sent": False,
                            "error": "chạm trần provider"})
                continue
            r = await _mot_repeat(ca, nhan, key)
            if r.get("sent"):
                da_dung += 1
            lan.append(r)
            print(f"  {nhan} hash={'khớp' if r['input_hash_match'] else 'LỆCH'}"
                  f" · {'ĐÚNG' if r.get('correct') else 'HỎNG ' + str(r.get('taxonomy'))}"
                  f" · hash chương trình {r.get('normalized_program_hash')}")
            if r.get("error"):
                print(f"     {' '.join(str(r['error']).split())[:150]}")
        dung = sum(1 for x in lan if x.get("correct"))
        hashes = {x.get("normalized_program_hash") for x in lan
                  if x.get("normalized_program_hash")}
        ket.append({
            "case_id": cid, "success_count": f"{dung}/3",
            "label": {3: "STABLE", 2: "MOSTLY_STABLE", 1: "UNSTABLE",
                      0: "CONSISTENT_FAILURE"}[dung],
            "distinct_normalized_programs": len(hashes),
            "alternative_valid_composition": bool(
                len({x["normalized_program_hash"] for x in lan
                     if x.get("correct") and x.get("normalized_program_hash")})
                > 1),
            "repeats": lan})
        print(f"  → {dung}/3 · {ket[-1]['label']} · "
              f"{len(hashes)} chương trình khác nhau")

    moi = [x for c in ket for x in c["repeats"] if x.get("sent")]
    tat_ca = [x for c in ket for x in c["repeats"]]
    dung18 = sum(1 for x in tat_ca if x.get("correct"))
    n_lop = lambda L: sum(1 for c in ket if c["label"] == L)  # noqa: E731
    it_nhat_2 = sum(1 for c in ket if int(c["success_count"][0]) >= 2)
    he = sum(1 for x in tat_ca if x.get("taxonomy") == "SYSTEM")
    arith = {n: sum(x.get("arith_as_point_expr", 0) for c in ket
                    for x in c["repeats"] if x["repeat"] == n)
             for n in ("R1", "R2", "R3")}
    on_dinh = ("SUPPORTIVE" if it_nhat_2 >= 5 and he == 0 else
               "WEAK" if it_nhat_2 <= 2 else
               "MIXED" if he == 0 else "WEAK")

    bao = {
        "khai": "SYNTHESIS_STABILITY_K3 — cùng MỘT đầu vào tổng hợp, ba lần "
                "sinh. R1 đọc từ hạt giống, R2/R3 gọi mới. Không analyze, "
                "không sửa. Sáu đề là TẬP ĐO ĐỘ ỔN ĐỊNH, không phải held-out.",
        "source_set": "CLEAN_BASELINE_V2_STABILITY_SEED",
        "chayLuc": datetime.now(timezone.utc).isoformat(),
        "frozen_commit": commit, "cay_sach": sach,
        "cache_version": CACHE_VERSION,
        "prompt_hash": _bam(load_skill(_SKILL)),
        "model_card_hash": _bam(grammar_card(DOMAIN_HINH_HOC)),
        "r1_from_seed": True, "new_analyze_calls": 0, "new_repair_calls": 0,
        "provider_call_hard_cap": TRAN, "provider_calls_used": da_dung,
        "input_hash_pre_send": all(x["input_hash_match"] for x in moi),
        "input_equivalence": all(x["input_hash_match"] for x in tat_ca),
        "initial_correct_total": f"{dung18}/18",
        "one_shot_synthesis_reliability": f"{dung18}/18",
        "case_stable_3_of_3": n_lop("STABLE"),
        "case_at_least_2_of_3": it_nhat_2,
        "case_unstable_1_of_3": n_lop("UNSTABLE"),
        "case_failed_0_of_3": n_lop("CONSISTENT_FAILURE"),
        "system_failure_total": he,
        "arith_as_point_expr_failures": arith,
        "construct_point_selected": sum(
            x.get("construct_point_count", 0) for x in tat_ca),
        "safe_assign_normalized": sum(
            x.get("assign_count", 0) for x in tat_ca),
        "first_binding_runtime_failures": sum(
            1 for x in tat_ca if x.get("taxonomy") == "RUNTIME"),
        "total_distinct_normalized_programs": len({
            x["normalized_program_hash"] for x in tat_ca
            if x.get("normalized_program_hash")}),
        "alternative_valid_compositions": sum(
            1 for c in ket if c["alternative_valid_composition"]),
        "r1_historical_seed": {"correct": sum(
            1 for c in ket for x in c["repeats"]
            if x["repeat"] == "R1" and x.get("correct"))},
        "synthesis_stability": on_dinh,
        "new_code_required": 0,
        "cases": ket,
    }
    dich.write_text(json.dumps(bao, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")

    print("\n━━ KẾT QUẢ · SYNTHESIS_STABILITY_K3 ━━")
    for c in ket:
        print(f"  {c['case_id'][:34]:34s} {c['success_count']} "
              f"{c['label']:18s} {c['distinct_normalized_programs']} chương trình")
    print(f"\n  INITIAL_CORRECT_TOTAL      {dung18}/18")
    print(f"  CASE_STABLE_3_OF_3         {n_lop('STABLE')}/6")
    print(f"  CASE_AT_LEAST_2_OF_3       {it_nhat_2}/6")
    print(f"  CASE_UNSTABLE_1_OF_3       {n_lop('UNSTABLE')}/6")
    print(f"  CASE_FAILED_0_OF_3         {n_lop('CONSISTENT_FAILURE')}/6")
    print(f"  SYSTEM_FAILURE_TOTAL       {he}/18")
    print(f"  arith-trong-construct_point R1={arith['R1']} R2={arith['R2']} "
          f"R3={arith['R3']}")
    print(f"  provider {da_dung}/{TRAN} · input hash khớp: "
          f"{bao['input_hash_pre_send']}")
    print(f"  SYNTHESIS_STABILITY: {on_dinh}")
    print(f"\n→ {dich}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
