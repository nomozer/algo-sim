# -*- coding: utf-8 -*-
"""Đo VÒNG SỬA của sản phẩm trên lỗi `at` đặt sai ô.

    `POINT_INITIALIZATION_REPAIR_EFFICACY`, 2026-09-07.
    MEASUREMENT_CLASS = DEVELOPMENT_REPAIR_PROBE   ·   HELD_OUT_CLAIM = NO

**TIÊU QUOTA THẬT — ĐÚNG MỘT LƯỢT.** `ALLOW_LIVE_AI=1` + `GEMINI_API_KEY`.

─── VÌ SAO KHÔNG DỰNG ĐƯỜNG SỬA RIÊNG ──────────────────────────────────

Câu hỏi của wave là *"vòng sửa **của sản phẩm** có sửa được lỗi này không"*.
Một đường sửa viết riêng cho phép đo sẽ trả lời một câu khác — và kho này đã
trả giá đúng một lần cho việc ấy (`V3_LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL`:
certifier xanh vì nó gọi tắt, chưa bao giờ chạy `main_async`).

Nên probe gọi thẳng `pipeline.stage_semantic_program`, và chỉ can thiệp ở
**biên provider**:

    lượt 0  →  trả về RAW CANDIDATE LỊCH SỬ   (0 lượt gọi thật)
    lượt 1  →  uỷ quyền cho `call_gemini` thật (1 lượt gọi thật)

Nhờ vậy `_prompt_sua`, chẩn đoán validator, thẻ văn phạm và `RequestContract`
đều là **bản của sản phẩm**, không phải bản dựng lại.

`MAX_SEMANTIC_PROGRAM_ATTEMPTS` hạ xuống **2 trong tiến trình probe** để trần
một-lượt-sửa là cưỡng chế, không phải lời hứa. Hằng số sản phẩm không đổi.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
for p in (str(BACKEND), str(BACKEND / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from gold_ratio_ab import CORPUS  # noqa: E402

RA = (BACKEND.parent / "docs" / "evaluation" / "geometry"
      / "point-initialization-repair-efficacy")
CA = {c["case_id"]: c for c in CORPUS}

#: Trần của wave. Một lượt sửa, không hơn.
REPAIR_LOGICAL_LIMIT = 1
#: Ngưỡng QUAN SÁT cho một lượt sửa — không phải cổng chặn cứng của provider.
TOKEN_QUAN_SAT = 7_500


def _h(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def _hop_dong(cid: str):
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.segment_relation import (
        bat_bien_chia_doan, bat_bien_do_dai,
    )

    rc = RequestContract.model_validate(CA[cid]["request_contract"])
    return rc.model_copy(update={"source_invariants": (
        bat_bien_do_dai(rc, rc.problem_text)
        + bat_bien_chia_doan(rc, rc.problem_text))})


def cham(spec, contract) -> dict[str, Any]:
    """Ba chiều độc lập: slot · provenance · hình học/mô phỏng."""
    from app.ai.pipeline import _dung_scene3d
    from app.simulation.geometry.radical import display, is_exact_number
    from app.simulation.semantic_program.route import verify_and_compile

    NR = "NOT_REACHED"
    c: dict[str, Any] = {}
    if spec is None:
        return {k: NR for k in (
            "SLOT_REPAIRED", "PROVENANCE_PRESERVED", "RATIO_PRESERVED",
            "GROUNDING", "SOURCE_INVARIANTS", "RUNTIME", "POSTCONDITIONS",
            "EXACT_ANSWER", "TRACE_CONSTRUCTION", "SCENE3D", "SERVABLE")}

    p = json.loads(spec.model_dump_json(exclude_none=True))
    # ─── SLOT: `at` không còn ở chỗ sai ───────────────────────────────────
    c["SLOT_REPAIRED"] = "PASS" if not any(
        "at" in m for m in p.get("memory_declarations", [])) else "FAIL"
    # ─── PROVENANCE ───────────────────────────────────────────────────────
    xx = {m["name"]: m for m in p.get("memory_declarations", [])}
    goc, kia, diem = "C", "D", "N"
    c["PROVENANCE_PRESERVED"] = "PASS" if (
        (xx.get(goc, {}).get("model_assumption")
         or xx.get(goc, {}).get("source_fact_id"))
        and xx.get(kia, {}).get("source_fact_id")
        and xx.get(diem, {}).get("initial_value") is None
        and not xx.get(diem, {}).get("model_assumption")
    ) else "FAIL"
    # ─── HÌNH HỌC: `t` đúng theo chiều THỰC TẾ ────────────────────────────
    from fractions import Fraction

    st = next((s for s in p.get("statements", [])
               if s.get("target_var") == diem), None)
    e = (st or {}).get("expr") or {}
    c["PRODUCER_KIND"] = e.get("kind") or (st or {}).get("kind") or "NOT_OBSERVED"
    mong = CA["r2"]["t_theo_thu_tu"].get(f"{e.get('a')}->{e.get('b')}")
    try:
        ok_t = mong is not None and Fraction(str(e.get("ratio"))) == Fraction(mong)
    except Exception:                                             # noqa: BLE001
        ok_t = False
    c["RATIO_PRESERVED"] = "PASS" if (e.get("kind") == "divide_segment"
                                      and ok_t) else "FAIL"
    c["OPERAND_ORDER"] = f"{e.get('a')}->{e.get('b')}"
    c["T_WRITTEN"] = str(e.get("ratio"))

    oc = verify_and_compile(contract, spec)
    stage = oc.stage_reached
    chua = ("semantic_program", "ir_static")
    c["GROUNDING"] = "FAIL" if stage == "grounding" else (
        NR if stage in chua else "PASS")
    c["SOURCE_INVARIANTS"] = "FAIL" if stage == "source_invariant" else (
        NR if stage in chua + ("grounding", "structural_coverage",
                               "execution") else "PASS")
    c["RUNTIME"] = "FAIL" if stage == "execution" else (
        "PASS" if oc.executable else NR)
    c["POSTCONDITIONS"] = "PASS" if oc.servable else (
        "FAIL" if stage == "postconditions" else NR)
    c["STAGE"] = stage
    mem = {k: display(v) for k, v in (oc.final_memory or {}).items()
           if is_exact_number(v)}
    c["ANSWER_OBSERVED"] = mem.get("do_dai_nd", NR)
    c["EXACT_ANSWER"] = ("PASS" if mem.get("do_dai_nd") == "6"
                         else ("FAIL" if oc.servable else NR))
    canh = _dung_scene3d(spec, contract) or {}
    objs = canh.get("objects") or []
    N = [o for o in objs if str(o.get("id")) == diem]
    c["DERIVED_POINT_PRODUCER"] = N[0].get("producer") if N else NR
    c["DERIVED_POINT_DEPENDS"] = N[0].get("depends") if N else NR
    c["TRACE_CONSTRUCTION"] = "PASS" if any(
        diem in json.dumps(x, ensure_ascii=False)
        for x in (canh.get("events") or [])) else ("FAIL" if oc.servable else NR)
    c["SCENE3D"] = "PASS" if (oc.servable and objs) else (
        "FAIL" if oc.servable else NR)
    c["SERVABLE"] = "PASS" if oc.servable else "FAIL"
    c["_details"] = [str(x)[:240] for x in (oc.details or [])][:2]
    return c


async def main_async(args) -> int:
    from app.ai import gemini as G
    from app.ai import pipeline as PL
    from app.ai.telemetry import reset_usage, total_tokens, usage_report
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
    from app.simulation.semantic_program.validator import validate_semantic_program

    if os.environ.get("ALLOW_LIVE_AI") != "1":
        print("ALLOW_LIVE_AI != 1 — từ chối tiêu quota.")
        return 2
    api_key = os.environ.get("GEMINI_API_KEY")
    print(f"GEMINI_API_KEY: {'PRESENT' if api_key else 'ABSENT'}")
    if not api_key:
        return 2

    dang_ky = json.loads((RA / "registration.json").read_text(encoding="utf-8"))
    raw_hong = (RA / "raw_candidate_nguon.json").read_text(encoding="utf-8")
    cid = dang_ky["nguon"]["case_id"]
    ca = CA[cid]
    contract = _hop_dong(cid)

    goc_call = G.call_gemini
    ghi: dict[str, Any] = {"payload": [], "physical": 0, "logical_that": 0}

    async def provider(api_key_, system_prompt, user_text, schema=None,
                       temperature=0.2, image=None):
        ghi["physical"] += 1
        n = len(ghi["payload"])
        ghi["payload"].append({"lan": n, "system_sha256": _h(system_prompt),
                               "user": user_text,
                               "user_sha256": _h(user_text),
                               "user_bytes": len(user_text.encode())})
        if n == 0:
            return raw_hong                       # ← lượt 0: KHÔNG gọi model
        ghi["logical_that"] += 1
        if ghi["logical_that"] > REPAIR_LOGICAL_LIMIT:
            raise RuntimeError(f"VƯỢT TRẦN SỬA {REPAIR_LOGICAL_LIMIT}")
        return await goc_call(api_key_, system_prompt, user_text, schema,
                              temperature, image)

    run_id = datetime.now(timezone.utc).strftime("repair-%Y%m%dT%H%M%SZ")
    manifest = {
        "run_id": run_id, **{k: dang_ky[k] for k in
                             ("measurement_class", "held_out_claim")},
        "case_id": cid,
        "raw_candidate_sha256": _h(raw_hong),
        "contract_sha256": _h(json.dumps(ca["request_contract"],
                                         ensure_ascii=False, sort_keys=True)),
        "policy_sha256": _h(json.dumps(dang_ky, ensure_ascii=False,
                                       sort_keys=True)),
        "runner_sha256": _h(Path(__file__).read_text(encoding="utf-8")),
        "model_name": G.MODEL, "model_version_or_snapshot": "",
        "temperature_repair": 0.1,
        "transport_max_attempts": G.MAX_ATTEMPTS,
        "initial_synthesis_calls_this_wave": 0,
        "repair_logical_call_limit": REPAIR_LOGICAL_LIMIT,
        "token_quan_sat_mot_luot": TOKEN_QUAN_SAT,
        "product_repair_limit_unchanged": PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    RA.mkdir(parents=True, exist_ok=True)
    (RA / f"manifest_{run_id}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MANIFEST trước lượt gọi đầu → manifest_{run_id}.json")
    print(f"  raw nguồn={manifest['raw_candidate_sha256'][:16]}…  ca={cid}")
    print(f"  trần sửa={REPAIR_LOGICAL_LIMIT}  ngưỡng token={TOKEN_QUAN_SAT}\n")

    reset_usage()
    G.call_gemini = provider                    # type: ignore[assignment]
    PL.call_gemini = provider                   # type: ignore[assignment]
    goc_tran = PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS = 2        # lượt 0 + ĐÚNG MỘT lượt sửa
    spec = err = None
    try:
        spec, err = await PL.stage_semantic_program(
            ca["problem_text"], {}, api_key, contract, domain=DOMAIN_HINH_HOC)
    finally:
        G.call_gemini = goc_call                # type: ignore[assignment]
        PL.call_gemini = goc_call               # type: ignore[assignment]
        PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS = goc_tran

    tk = {"theo_stage": usage_report(), "tong": total_tokens()}
    raw_sua = ghi["payload"][1]["user"] if len(ghi["payload"]) > 1 else None
    ket = cham(spec, contract)
    out = {
        "manifest": {**manifest,
                     "finished_at": datetime.now(timezone.utc).isoformat(),
                     "physical_attempts": ghi["physical"],
                     "repair_logical_calls": ghi["logical_that"],
                     "application_llm_calls": ghi["logical_that"]},
        "chan_doan_gui_di": validate_semantic_program(
            json.loads(raw_hong)).error,
        "repair_payload_user": raw_sua,
        "repair_payload_sha256": (_h(raw_sua) if raw_sua else None),
        "loi_pipeline": err,
        "chuong_trinh_sua": (json.loads(spec.model_dump_json(exclude_none=True))
                             if spec is not None else None),
        "cham": ket, "tokens": tk,
    }
    (RA / f"repair_{run_id}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"REPAIR_LOGICAL_CALLS={ghi['logical_that']}/{REPAIR_LOGICAL_LIMIT}"
          f"  PHYSICAL={ghi['physical']}  TOKENS={tk['tong']}")
    for k in ("SLOT_REPAIRED", "PROVENANCE_PRESERVED", "RATIO_PRESERVED",
              "GROUNDING", "SOURCE_INVARIANTS", "POSTCONDITIONS",
              "EXACT_ANSWER", "TRACE_CONSTRUCTION", "SCENE3D", "SERVABLE"):
        print(f"  {k:22} {ket.get(k)}")
    print(f"  STAGE                  {ket.get('STAGE')}")
    if ket.get("_details"):
        print(f"  chi tiết: {ket['_details'][0]}")
    print(f"→ {RA / f'repair_{run_id}.json'}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass
    return asyncio.run(main_async(p.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
