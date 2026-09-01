# -*- coding: utf-8 -*-
"""REPLAYABLE_STABILITY_SEED — chụp đầu vào tổng hợp ĐỦ ĐỂ CHẠY LẠI.

    đề (6 ca của CLEAN_BASELINE_V2) → analyze → RequestContract ĐẦY ĐỦ
      → MỘT lượt tổng hợp → chuỗi cổng tất định → repeat 1

⚠️ **TIÊU QUOTA THẬT.** Trần TUYỆT ĐỐI 12 lượt: 6 analyze + 6 tổng hợp.
**KHÔNG sửa.** Không lượt thứ 13.

─── ĐÂY KHÔNG PHẢI CHẠY LẠI CLEAN_BASELINE_V2 ─────────────────────────────

Sáu đề này mô hình ĐÃ THẤY. Gọi lượt này là "đánh giá khái quát hoá" là nói
sai. Tên đúng: **hạt giống cho phép đo độ ổn định** — nó chụp lấy đầu vào dùng
lại được, cộng đúng một quan sát tổng hợp ban đầu cho mỗi ca.

Điểm lịch sử `CLEAN_BASELINE_V2 = 6/6` **không đổi**, và điểm của lượt này
**không được đem so** với nó.

─── VÌ SAO LƯỢT TRƯỚC PHẢI DỪNG ───────────────────────────────────────────

`probe.json` ghi hợp đồng dạng tóm tắt (`{hash, số fact, tập nghĩa vụ}`),
trong khi prompt tổng hợp nhúng `id`/`nhãn`/`giá trị` của TỪNG dữ kiện. Không
dựng lại nổi đầu vào thì ba lượt lặp không chạy trên cùng một đầu vào, tức đo
phương sai của prompt chứ không đo phương sai của tổng hợp.

─── VÌ SAO CHỤP CẢ PAYLOAD, KHÔNG CHỈ CHỤP MẢNH ───────────────────────────

Dựng lại từ `{đề, hợp đồng, thẻ}` phụ thuộc vào MÃ NGUỒN hiện tại. Mã đổi thì
bản dựng lại đổi theo, và ta mất khả năng nói *"đầu vào đã gửi là cái này"*.
Nên artifact giữ **cả** payload chuẩn tắc lẫn hash của nó: hash để đối chiếu
nhanh, payload để tự đứng vững khi mã đã refactor.

Không lưu `api_key`.
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
from app.simulation.semantic_program.grounding_gate import (  # noqa: E402
    ERR_RUA_NANG_LUC,
    ERR_THIEU_NGUOI_DUNG,
    check_grounding,
)
from app.simulation.semantic_program.interpreter import (  # noqa: E402
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.ir_static_check import kiem_tinh  # noqa: E402
from app.simulation.semantic_program.pipeline_adapter import (  # noqa: E402
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402
from app.simulation.semantic_program.transport import (  # noqa: E402
    check_envelope_transport,
)
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)
from scripts.clean_baseline_v2_cases import CASES  # noqa: E402
from scripts.verify_baseline_expressibility import bang, mong_doi  # noqa: E402

TRAN_PROVIDER = 12
_SKILL = "geometry_program_generator"
_KHONG_SUA = {ERR_RUA_NANG_LUC, ERR_THIEU_NGUOI_DUNG}
V2 = GOC / "docs" / "evaluation" / "geometry" / "clean-baseline-v2" / "probe.json"


def _bam(x: str) -> str:
    return hashlib.sha256(x.encode("utf-8")).hexdigest()[:16]


def payload_chuan_tac(system_prompt: str, user_text: str,
                      response_schema: dict | None, temperature: float) -> dict:
    """Đầu vào mô hình THẬT SỰ nhận, ở dạng chuẩn tắc — KHÔNG có `api_key`.

    `call_gemini(api_key, system_prompt, user_text, response_schema,
    temperature, image)`. Bốn trường giữa là toàn bộ thứ quyết định đầu ra;
    `api_key` là bí mật và `image` luôn `None` trên đường hình học.

    Khoá sắp xếp khi băm: `json.dumps(sort_keys=True)` để hai lượt chỉ khác
    thứ tự khoá vẫn cho cùng hash — nếu không thì phép so lượt lặp sẽ báo
    khác nhau vì một chi tiết không ai nhìn thấy.
    """
    return {"system_prompt": system_prompt, "user_text": user_text,
            "response_schema": response_schema, "temperature": temperature}


def bam_payload(p: dict) -> str:
    return _bam(json.dumps(p, ensure_ascii=False, sort_keys=True))


def dung_lai_payload(ca: dict) -> dict:
    """Dựng lại đầu vào tổng hợp TỪ ARTIFACT + thẩm quyền đóng băng.

    §13 — phép kiểm này là toàn bộ lý do wave tồn tại. Nó phải đi qua ĐÚNG
    đường mà `stage_semantic_program` dựng prompt, nếu không nó chỉ chứng minh
    rằng hai bản sao của một công thức khớp nhau.
    """
    from app.simulation.semantic_program.contract import generate_json_schema

    hd = RequestContract.model_validate(ca["analyze"]["raw_request_contract"])
    base = f'Đề bài:\n"""\n{ca["problem_text"]}\n"""'
    base = f"{base}\n\n{PL._facts_for_prompt(hd)}"
    base = f"{base}\n\n{PL._obligations_for_prompt(hd)}"
    base = f"{base}\n\n{grammar_card(ca['synthesis_input']['canonical_domain'])}"
    return payload_chuan_tac(load_skill(_SKILL), base,
                             generate_json_schema(), 0.1)


def tien_kiem() -> list[str]:
    loi = []
    try:
        if program_skill_for(DOMAIN_HINH_HOC) != _SKILL:
            loi.append("skill tổng hợp không phải bản hình học")
    except Exception as e:  # noqa: BLE001
        return [f"program_skill_for ném: {e}"]
    if "construct_point" not in grammar_card(DOMAIN_HINH_HOC):
        loi.append("thẻ hình học thiếu `construct_point`")
    if not V2.exists():
        loi.append("thiếu artifact CLEAN_BASELINE_V2 để đối chiếu đề")
        return loi
    # §2 — đề phải khớp BYTE với bộ V2.
    d = json.loads(V2.read_text(encoding="utf-8"))
    manifest = {c["case_id"]: c["problem"]
                for c in json.loads(
                    (V2.parent / "SEAL.json").read_text(encoding="utf-8")
                )["manifest"]}
    for c in CASES:
        if manifest.get(c["id"]) != c["de"]:
            loi.append(f"{c['id']}: đề LỆCH khỏi manifest V2")
    if len(d["cases"]) != len(CASES):
        loi.append("số ca không khớp V2")
    return loi


class _Chup:
    """Chụp payload của lượt TỔNG HỢP; analyze chỉ đếm."""

    def __init__(self) -> None:
        self.payload: dict | None = None
        self.raw: str | None = None


def _taxonomy(stage: str, ma: str | None) -> str:
    if ma in _KHONG_SUA:
        return "HONESTY"
    return {"SCHEMA": "SCHEMA", "STATIC": "STATIC_VALIDATION",
            "GROUNDING": "GROUNDING", "EXEC": "RUNTIME",
            "TRANSPORT": "SYSTEM", "ORACLE": "SYNTHESIS",
            "ANALYZE": "PROVIDER", "NO_OUTPUT": "PROVIDER"}.get(stage, "SYSTEM")


def _cham_repeat1(raw: str, contract, case: dict) -> dict:
    """Một quan sát tổng hợp BAN ĐẦU → phán quyết, qua đúng chuỗi cổng.

    Chấm ở ĐÂY chứ không tin `stage_semantic_program`: hàm ấy có vòng sửa, và
    khi ta chặn lượt thứ hai nó trả `None` cho cả những chương trình mà lượt
    ĐẦU đã viết đúng. Quan sát của wave này là *lượt đầu*, nên nó phải được
    chấm độc lập với việc pipeline có muốn sửa tiếp hay không.
    """
    r: dict = {}
    try:
        payload = json.loads(raw)
    except Exception as e:  # noqa: BLE001
        return {"correct": False, "stage": "SCHEMA",
                "taxonomy": "SCHEMA", "error": f"JSON không parse được: {e}"}
    v = validate_semantic_program(payload)
    r["schema_pass"] = v.ok
    if not v.ok:
        return {**r, "correct": False, "stage": "SCHEMA",
                "taxonomy": "SCHEMA", "error": (v.error or "")[:300]}

    r["normalized_program"] = v.spec.model_dump(mode="json")
    r["program_hash"] = _bam(json.dumps(r["normalized_program"],
                                        ensure_ascii=False, sort_keys=True))
    r["statements"] = [s.kind for s in v.spec.statements]
    r["construct_point_targets"] = [s.target_var for s in v.spec.statements
                                    if s.kind == "construct_point"]

    t = kiem_tinh(v.spec)
    r["static_pass"] = t.ok
    if not t.ok:
        return {**r, "correct": False, "stage": "STATIC",
                "taxonomy": "STATIC_VALIDATION", "error": t.phan_hoi()[:300]}

    g = check_grounding(contract, v.spec)
    r["grounding_pass"] = g.ok
    r["grounding_code"] = g.error_code
    if not g.ok:
        return {**r, "correct": False, "stage": "GROUNDING",
                "taxonomy": _taxonomy("GROUNDING", g.error_code),
                "error": "; ".join(g.unresolved[:3])}

    try:
        kq = SemanticProgramInterpreter().execute(v.spec)
    except Exception as e:  # noqa: BLE001
        return {**r, "correct": False, "stage": "EXEC", "taxonomy": "RUNTIME",
                "error": f"{type(e).__name__}: {e}"[:300]}
    r["runtime_pass"] = True
    r["trace_steps"] = kq.total_steps

    kr = verify_and_compile(contract, v.spec)
    r["checker"] = {"checked": kr.constraints_checked,
                    "verified": kr.constraints_verified,
                    "executable": bool(kr.executable),
                    "servable": bool(kr.servable)}

    try:
        tr = check_envelope_transport(compile_semantic_program_to_envelope(v.spec))
    except Exception as e:  # noqa: BLE001
        tr = f"{type(e).__name__}: {e}"
    r["transport_pass"] = tr is None
    if tr is not None:
        return {**r, "correct": False, "stage": "TRANSPORT",
                "taxonomy": "SYSTEM", "error": str(tr)[:300]}

    dung = True
    for khoa, nhan in (("dap_so", "oracle"), ("dap_so_phu", "oracle_phu")):
        if khoa not in case:
            continue
        mong = mong_doi(case[khoa])
        khop = [k for k, val in kq.final_memory.items() if bang(val, mong)]
        r[nhan] = str(mong)
        r[f"{nhan}_khop"] = khop
        dung = dung and bool(khop)
    return {**r, "correct": dung, "stage": "DONE" if dung else "ORACLE",
            "taxonomy": None if dung else "SYNTHESIS",
            "error": None if dung else "không khớp oracle tính tay"}


async def _mot_de(case: dict, api_key: str) -> dict:
    reset_usage()
    dem = {"analyze": 0, "tong_hop": 0}
    chup = _Chup()
    t0 = time.monotonic()
    goc = PL.call_gemini
    pha = {"ten": "ANALYZE"}

    async def bao(api_key_, system_prompt, user_text, schema=None,
                  temperature=0.2, image=None):
        if pha["ten"] == "ANALYZE":
            dem["analyze"] += 1
            return await goc(api_key_, system_prompt, user_text, schema,
                             temperature, image)
        # ── MỘT lượt tổng hợp, KHÔNG hơn (§4, §5) ───────────────────────
        if dem["tong_hop"] >= 1:
            raise RuntimeError("KHÔNG SỬA — dừng TRƯỚC khi gửi, 0 token")
        dem["tong_hop"] += 1
        chup.payload = payload_chuan_tac(system_prompt, user_text, schema,
                                         temperature)
        kq = await goc(api_key_, system_prompt, user_text, schema,
                       temperature, image)
        chup.raw = kq if isinstance(kq, str) else repr(kq)
        return kq

    ghi: dict = {"case_id": case["id"], "problem_text": case["de"],
                 "problem_hash": _bam(case["de"])}

    PL.call_gemini = bao
    try:
        contract, aerr = await PL.stage_semantic_analyze(
            case["de"], api_key, domain=DOMAIN_HINH_HOC)
        if contract is None:
            return {**ghi, "analyze": {"ok": False, "error": aerr},
                    "repeat_1": {"correct": False, "stage": "ANALYZE",
                                 "taxonomy": "PROVIDER", "error": aerr},
                    "provider_calls": dem["analyze"],
                    "usage": usage_report()}
        pha["ten"] = "SYNTHESIS"
        try:
            await PL.stage_semantic_program(
                case["de"], {}, api_key, contract, domain=DOMAIN_HINH_HOC)
        except RuntimeError:
            pass          # chạm trần "không sửa" — đúng thiết kế
    finally:
        PL.call_gemini = goc

    # ── §6 hợp đồng ĐẦY ĐỦ + round-trip ─────────────────────────────────
    raw_hd = contract.model_dump(mode="json")
    lai = RequestContract.model_validate(raw_hd).model_dump(mode="json")
    u = usage_report()
    ghi["analyze"] = {
        "ok": True,
        "raw_request_contract": raw_hd,
        "request_contract_hash": _bam(contract.model_dump_json()),
        "roundtrip_ok": lai == raw_hd,
        "input_facts": len(contract.input_facts),
        "obligations": sorted({o.kind for o in contract.obligations}),
        "usage": u.get("semantic_analyze") or {},
    }
    ghi["synthesis_input"] = {
        "canonical_domain": DOMAIN_HINH_HOC,
        "selected_skill": _SKILL,
        "skill_hash": _bam(load_skill(_SKILL)),
        "model_card_hash": _bam(grammar_card(DOMAIN_HINH_HOC)),
        "prompt_hash": _bam(load_skill(_SKILL)),
        "payload": chup.payload,
        "model_input_hash": bam_payload(chup.payload) if chup.payload else None,
    }
    ghi["provider_calls"] = dem["analyze"] + dem["tong_hop"]
    ghi["usage"] = {"analyze": u.get("semantic_analyze") or {},
                    "synthesis": u.get("semantic_program") or {},
                    "total_tokens": total_tokens()}
    ghi["latency_s"] = round(time.monotonic() - t0, 2)

    if chup.raw is None:
        ghi["repeat_1"] = {"correct": False, "stage": "NO_OUTPUT",
                           "taxonomy": "PROVIDER",
                           "error": "không có đầu ra tổng hợp nào"}
        return ghi
    ghi["repeat_1"] = {"raw_output": chup.raw, **_cham_repeat1(
        chup.raw, contract, case)}
    return ghi


def tu_kiem(dich: Path) -> dict:
    """§13 — nạp artifact TỪ ĐĨA, dựng lại đầu vào, so hash. 0 provider."""
    d = json.loads(dich.read_text(encoding="utf-8"))
    ra = []
    for c in d["cases"]:
        si = c.get("synthesis_input") or {}
        an = c.get("analyze") or {}
        m = {"case_id": c["case_id"],
             "raw_captured": bool(an.get("raw_request_contract")),
             "roundtrip": bool(an.get("roundtrip_ok")),
             "payload_captured": bool(si.get("payload"))}
        if not (m["raw_captured"] and m["payload_captured"]):
            ra.append({**m, "hash_replay": False,
                       "self_contained": False})
            continue
        # ① Payload lưu trong artifact có tự khớp hash của nó không?
        m["self_contained"] = bam_payload(si["payload"]) == si["model_input_hash"]
        # ② Dựng lại từ MẢNH (đề + hợp đồng + thẻ) có ra đúng payload ấy không?
        try:
            m["hash_replay"] = bam_payload(dung_lai_payload(c)) == \
                si["model_input_hash"]
        except Exception as e:  # noqa: BLE001
            m["hash_replay"] = False
            m["loi"] = f"{type(e).__name__}: {e}"[:120]
        ra.append(m)
    return {"cases": ra,
            "input_equivalence": all(
                x["raw_captured"] and x["roundtrip"] and x["payload_captured"]
                and x["self_contained"] and x["hash_replay"] for x in ra)}


async def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir",
                   default="../docs/evaluation/geometry/stability-seed")
    p.add_argument("--chi-tien-kiem", action="store_true")
    p.add_argument("--chi-tu-kiem", action="store_true")
    a = p.parse_args()

    ra = Path(a.out_dir).resolve()
    ra.mkdir(parents=True, exist_ok=True)
    dich = ra / "seed.json"

    if a.chi_tu_kiem:
        k = tu_kiem(dich)
        for x in k["cases"]:
            print(f"  {x['case_id']:36s} raw={x['raw_captured']!s:5s} "
                  f"rt={x['roundtrip']!s:5s} payload={x['payload_captured']!s:5s} "
                  f"tự-chứa={x['self_contained']!s:5s} "
                  f"dựng-lại={x['hash_replay']}")
        print(f"\nINPUT_EQUIVALENCE: "
              f"{'PASS' if k['input_equivalence'] else 'FAIL'}")
        return 0 if k["input_equivalence"] else 1

    if dich.exists():
        print(f"✗ {dich} đã có — bộ đo TỪ CHỐI đè lượt cũ.")
        return 3

    loi = tien_kiem()
    from app.main import CACHE_VERSION

    sach = not subprocess.run(["git", "status", "--porcelain"], cwd=GOC,
                              capture_output=True, text=True).stdout.strip()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=GOC,
                            capture_output=True, text=True).stdout.strip()
    print("━━ TIỀN KIỂM · REPLAYABLE_STABILITY_SEED ━━")
    print(f"  commit {commit[:8]} · cây sạch {sach} · CACHE_VERSION "
          f"{CACHE_VERSION}")
    print(f"  prompt {_bam(load_skill(_SKILL))} · thẻ "
          f"{_bam(grammar_card(DOMAIN_HINH_HOC))}")
    print(f"  đề khớp manifest V2: {'6/6' if not loi else 'LỆCH'}")
    if loi:
        for x in loi:
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

    ket, da_dung = [], 0
    for c in CASES:
        if da_dung + 2 > TRAN_PROVIDER:
            ket.append({"case_id": c["id"], "skipped": "chạm trần provider"})
            continue
        print(f"\n━━ {c['id']} ━━")
        r = await _mot_de(c, key)
        da_dung += r.get("provider_calls", 0)
        ket.append(r)
        r1 = r.get("repeat_1") or {}
        print(f"  provider {r.get('provider_calls')} · repeat1 "
              f"{'ĐÚNG' if r1.get('correct') else 'HỎNG ' + str(r1.get('taxonomy'))}"
              f" · hợp đồng raw={bool((r.get('analyze') or {}).get('raw_request_contract'))}"
              f" round-trip={(r.get('analyze') or {}).get('roundtrip_ok')}")
        if r1.get("error"):
            print(f"    {' '.join(str(r1['error']).split())[:160]}")

    def bo(f):
        return sum(f(r) for r in ket)

    dung = sum(1 for r in ket if (r.get("repeat_1") or {}).get("correct"))
    bao = {
        "khai": "REPLAYABLE_STABILITY_SEED — chụp đầu vào tổng hợp đủ để chạy "
                "lại, cộng MỘT quan sát tổng hợp ban đầu mỗi ca. KHÔNG phải "
                "một lượt đánh giá khái quát hoá: sáu đề này mô hình đã thấy.",
        "probe_id": "CLEAN_BASELINE_V2_STABILITY_SEED",
        "source_set": "CLEAN_BASELINE_V2",
        "chayLuc": datetime.now(timezone.utc).isoformat(),
        "frozen_commit": commit, "cay_sach": sach,
        "cache_version": CACHE_VERSION,
        "prompt_hash": _bam(load_skill(_SKILL)),
        "model_card_hash": _bam(grammar_card(DOMAIN_HINH_HOC)),
        "canonical_domain": DOMAIN_HINH_HOC,
        "provider_call_hard_cap": TRAN_PROVIDER,
        "analyze_calls": bo(lambda r: (r.get("analyze") or {}).get("ok") and 1 or 0),
        "initial_synthesis_calls": bo(
            lambda r: 1 if (r.get("repeat_1") or {}).get("raw_output") else 0),
        "repair_calls": 0,
        "total_provider_calls": da_dung,
        "repeat_1_correct": dung,
        "analyze_tokens": bo(
            lambda r: (r.get("usage") or {}).get("analyze", {}).get("total_tokens", 0)),
        "synthesis_tokens": bo(
            lambda r: (r.get("usage") or {}).get("synthesis", {}).get("total_tokens", 0)),
        "total_tokens": bo(lambda r: (r.get("usage") or {}).get("total_tokens", 0)),
        "historical_v2_score_changed": False,
        "new_code_required": 0,
        "cases": ket,
    }
    dich.write_text(json.dumps(bao, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")

    print("\n━━ TỰ KIỂM (§13) — nạp lại TỪ ĐĨA, 0 provider ━━")
    k = tu_kiem(dich)
    for x in k["cases"]:
        print(f"  {x['case_id']:36s} raw={x['raw_captured']!s:5s} "
              f"rt={x['roundtrip']!s:5s} payload={x['payload_captured']!s:5s} "
              f"tự-chứa={x['self_contained']!s:5s} dựng-lại={x['hash_replay']}")
    bao["self_check"] = k
    bao["input_equivalence"] = k["input_equivalence"]
    bao["artifact_replayable"] = k["input_equivalence"]
    dich.write_text(json.dumps(bao, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")

    print(f"\n━━ KẾT QUẢ ━━")
    print(f"  provider {da_dung}/{TRAN_PROVIDER} "
          f"(analyze {bao['analyze_calls']} + tổng hợp "
          f"{bao['initial_synthesis_calls']} + sửa 0)")
    print(f"  repeat_1 đúng {dung}/{len(CASES)}  ← KHÔNG so với V2")
    print(f"  token {bao['total_tokens']} (analyze {bao['analyze_tokens']} + "
          f"tổng hợp {bao['synthesis_tokens']})")
    print(f"  INPUT_EQUIVALENCE: "
          f"{'PASS' if k['input_equivalence'] else 'FAIL'}")
    print(f"\n→ {dich}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
