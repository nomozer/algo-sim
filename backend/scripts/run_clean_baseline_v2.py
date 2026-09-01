# -*- coding: utf-8 -*-
"""CLEAN_BASELINE_V2 — 6 đề mới, đường sản phẩm đầy đủ, sau bản sửa ràng buộc.

    đề → analyze (LLM, ĐÚNG MỘT LẦN) → RequestContract
       → tổng hợp (LLM, 1 + tối đa 1 sửa) → chuẩn hoá ràng buộc lần đầu
       → validator → tĩnh → grounding + trung thực → thực thi
       → hậu điều kiện → envelope + vận chuyển → oracle tính tay

⚠️ **TIÊU QUOTA THẬT.** `ALLOW_LIVE_AI=1` + `GEMINI_API_KEY`.
Trần: 6 analyze + tối đa 12 tổng hợp. Chạy ĐÚNG MỘT LẦN.

─── ĐÂY LÀ LẦN ĐẦU MÔ HÌNH THẤY `construct_point` ─────────────────────────

Trước 2026-09-01 thẻ văn phạm dẫn từ `_TOAN_HANG_LENH` — bảng **cố ý** không
chứa `construct_point` — nên thẻ giấu mất câu lệnh ấy và mô hình dựng mọi điểm
phụ bằng `assign`, lối duy nhất nó thấy, lối chết ở runtime.

Nên §17 không hỏi *"mô hình có ngoan không"* mà hỏi một câu đo được: **nó chọn
dạng nào khi cả hai đều hiện ra**, và bao nhiêu lần bộ chuẩn hoá phải ra tay.
Chuẩn hoá tất định KHÔNG phải một thất bại của mô hình.

─── ĐIỀU BỘ ĐO KHÔNG LÀM ──────────────────────────────────────────────────

Không sửa chương trình. Không gợi ý. Không gọi analyze lần hai. Không sửa lỗi
runtime/checker/trung thực. Không lượt thứ ba. Không đè artifact lượt cũ.
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
from app.simulation.semantic_program.ir_static_check import (  # noqa: E402
    _CHU_KY,
    DIEM,
    kiem_tinh,
)
from app.simulation.semantic_program.pipeline_adapter import (  # noqa: E402
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402
from app.simulation.semantic_program.transport import (  # noqa: E402
    check_envelope_transport,
)
from scripts.clean_baseline_v2_cases import CASES, check_contamination  # noqa: E402
from scripts.verify_baseline_expressibility import bang, mong_doi  # noqa: E402

TRAN_TONG_HOP = 12
TRAN_MOI_DE = 2
_KHONG_SUA = {ERR_RUA_NANG_LUC, ERR_THIEU_NGUOI_DUNG}
_SKILL = "geometry_program_generator"


def ghi_hop_dong(contract) -> dict:
    """`RequestContract` → bản ghi TÁI TẠO ĐƯỢC, không phải bản tóm tắt.

    ─── VÌ SAO PHẢI LƯU NGUYÊN, ĐO ĐƯỢC 2026-09-01 ────────────────────────

    Bản đầu chỉ ghi `{hash, số input_facts, tập nghĩa vụ}`. Nó đủ để đọc báo
    cáo, và **không** đủ để chạy lại: prompt tổng hợp nhúng `id`, `nhãn` và
    `giá trị` của từng dữ kiện (`pipeline._facts_for_prompt`), nên thiếu chúng
    thì lượt lặp nhận một prompt KHÁC lượt gốc.

    Wave đo độ ổn định vì thế **không chạy được**: nó đòi cùng một đầu vào cho
    ba lượt, và ta không dựng lại nổi đầu vào của lượt một. Gom `source_fact_id`
    từ chương trình cũng không cứu được — `v2_02` có hợp đồng 6 dữ kiện mà mô
    hình chỉ trích dẫn 4, nên bản dựng lại sẽ THIẾU hai mục và mọi nhãn/giá
    trị.

    Một artifact chỉ tóm tắt được thứ nó đo là một artifact **đọc được nhưng
    không kiểm lại được**. Giữ `hash` để đối chiếu nhanh, giữ `raw` để dựng
    lại thật.
    """
    return {
        "hash": hashlib.sha256(
            contract.model_dump_json().encode("utf-8")).hexdigest()[:16],
        "input_facts": len(contract.input_facts),
        "obligations": sorted({o.kind for o in contract.obligations}),
        "raw": contract.model_dump(mode="json"),
    }


def tien_kiem() -> list[str]:
    """§1 — chạy TRƯỚC khi tiêu một call nào."""
    loi = []
    try:
        sk = program_skill_for(DOMAIN_HINH_HOC)
    except Exception as e:  # noqa: BLE001
        return [f"program_skill_for({DOMAIN_HINH_HOC!r}) ném: {e}"]
    if sk != _SKILL:
        loi.append(f"skill tổng hợp là {sk!r}, mong {_SKILL!r}")
    for xau in ("geometry", "hinh hoc", ""):
        try:
            program_skill_for(xau)
        except Exception:
            continue
        loi.append(f"miền lạ {xau!r} KHÔNG ném — cửa `else` còn mở")
    the = grammar_card(DOMAIN_HINH_HOC)
    if "construct_point" not in the:
        loi.append("thẻ hình học KHÔNG có `construct_point` — đúng lỗi V1")
    if "angle_cos_sq" not in the:
        loi.append("thẻ thiếu bảng phép đo")
    return loi


class _Nhat:
    def __init__(self) -> None:
        self.events: list[dict] = []
        self.raws: list[str] = []
        self.tokens_moi_luot: list[int] = []

    def emit(self, event_type: str, data: dict) -> None:
        if event_type == "semantic_program_attempt":
            self.events.append({
                "attempt_index": data.get("n", 0), "ok": data.get("ok"),
                "gate": data.get("gate") or "schema",
                "repairable": data.get("repairable", True),
                "message": (data.get("message") or "")[:600]})


def _dang_rang_buoc(raw: str) -> dict:
    """§17 — mô hình CHỌN dạng nào, đọc trên chương trình THÔ.

    Phải đọc bản thô: bộ chuẩn hoá viết lại `assign` sinh điểm thành
    `construct_point`, nên bản đã chuẩn hoá không còn nói được mô hình đã
    chọn gì.
    """
    try:
        p = json.loads(raw)
    except Exception:  # noqa: BLE001
        return {}
    cp, ap, av = [], [], []
    for st in p.get("statements") or []:
        if not isinstance(st, dict):
            continue
        if st.get("kind") == "construct_point":
            cp.append(st.get("target_var"))
        elif st.get("kind") == "assign":
            k = (st.get("expr") or {}).get("kind")
            if k in _CHU_KY:
                (ap if _CHU_KY[k][1] == DIEM else av).append(st.get("target_var"))
    return {"construct_point": cp, "assign_diem": ap, "assign_hinh_khac": av}


def _taxonomy(stage: str, ma: str | None, su_kien: list[dict]) -> str:
    if ma in _KHONG_SUA:
        return "HONESTY"
    van = " ".join(str(e.get("message") or "") for e in su_kien)
    return {
        "ANALYZE": "PROVIDER",
        "SYNTHESIS": ("SCHEMA" if ("validation error" in van or "schema" in van)
                      else "SYNTHESIS"),
        "STATIC": "STATIC_VALIDATION", "GROUNDING": "GROUNDING",
        "EXEC": "RUNTIME", "CHECKER": "CHECKER", "TRANSPORT": "SYSTEM",
        "ORACLE": "SYNTHESIS",
    }.get(stage, "SYSTEM")


async def _mot_de(case: dict, api_key: str, con_lai: int) -> dict:
    reset_usage()
    dem = {"analyze": 0, "tong_hop": 0, "attempted": 0}
    nhat = _Nhat()
    t0 = time.monotonic()
    goc = PL.call_gemini
    pha = {"ten": "ANALYZE"}

    async def dem_call(*a, **kw):
        if pha["ten"] == "ANALYZE":
            dem["analyze"] += 1
            return await goc(*a, **kw)
        dem["attempted"] += 1
        if dem["attempted"] > TRAN_MOI_DE or dem["tong_hop"] >= con_lai:
            raise RuntimeError("chạm trần — dừng TRƯỚC khi gửi, 0 token")
        dem["tong_hop"] += 1
        truoc = total_tokens()
        kq = await goc(*a, **kw)
        nhat.raws.append(kq if isinstance(kq, str) else repr(kq))
        nhat.tokens_moi_luot.append(total_tokens() - truoc)
        return kq

    ghi: dict = {k: case[k] for k in
                 ("topology", "capability_mix", "derived_entity_count",
                  "expected_dependency_depth", "obligation_count")}
    ghi.update({"case_id": case["id"], "domain": DOMAIN_HINH_HOC,
                "selected_skill": _SKILL,
                "prompt_hash": hashlib.sha256(
                    load_skill(_SKILL).encode("utf-8")).hexdigest()[:16]})

    PL.call_gemini = dem_call
    try:
        contract, aerr = await PL.stage_semantic_analyze(
            case["de"], api_key, domain=DOMAIN_HINH_HOC)
        if contract is None:
            u = usage_report()
            return {**ghi, "class": "SYSTEM_FAILURE", "stage": "ANALYZE",
                    "error": aerr, "taxonomy": "PROVIDER",
                    "analyze_calls": dem["analyze"], "logical_calls": 0,
                    "usage": u, "total_tokens": total_tokens()}
        ghi["request_contract"] = ghi_hop_dong(contract)
        # §2 — analyze gọi ĐÚNG MỘT LẦN; vòng sửa nằm TRONG
        # `stage_semantic_program` và dùng lại chính hợp đồng này.
        pha["ten"] = "SYNTHESIS"
        spec, serr = await PL.stage_semantic_program(
            case["de"], {}, api_key, contract, observer=nhat,
            domain=DOMAIN_HINH_HOC)
    except RuntimeError as e:
        spec, serr = None, str(e)
    finally:
        PL.call_gemini = goc

    u = usage_report()
    ua = u.get("semantic_analyze") or {}
    us = u.get("semantic_program") or {}
    tok_sua = sum(nhat.tokens_moi_luot[1:])
    ghi.update({
        "analyze_calls": dem["analyze"], "logical_calls": dem["tong_hop"],
        "attempts": dem["attempted"], "one_shot": dem["attempted"] == 1,
        "analyze_tokens": {"input": ua.get("prompt_tokens", 0),
                           "output": ua.get("candidates_tokens", 0),
                           "total": ua.get("total_tokens", 0)},
        "synthesis_tokens": {"input": us.get("prompt_tokens", 0),
                             "output": us.get("candidates_tokens", 0),
                             "total": us.get("total_tokens", 0)},
        "initial_synthesis_tokens": (nhat.tokens_moi_luot or [0])[0],
        "repair_tokens": tok_sua,
        "total_tokens": total_tokens(),
        "tokens_per_attempt": nhat.tokens_moi_luot,
        "latency_s": round(time.monotonic() - t0, 2),
        "attempts_log": nhat.events, "programs": nhat.raws,
        "first_binding": _dang_rang_buoc(nhat.raws[-1]) if nhat.raws else {},
    })

    if spec is None:
        ma = next((h for e in nhat.events for h in _KHONG_SUA
                   if h in str(e.get("message") or "")), None)
        return {**ghi, "class": "FAIL_AFTER_REPAIR", "stage": "SYNTHESIS",
                "error": serr, "error_code": ma,
                "taxonomy": _taxonomy("SYNTHESIS", ma, nhat.events)}

    ghi["normalized_program"] = spec.model_dump(mode="json")
    ghi["program_hash"] = hashlib.sha256(
        json.dumps(ghi["normalized_program"], ensure_ascii=False,
                   sort_keys=True).encode("utf-8")).hexdigest()[:16]
    ghi["statements"] = [s.kind for s in spec.statements]
    ghi["normalized_first_bindings"] = ghi["first_binding"].get("assign_diem", [])

    t = kiem_tinh(spec)
    ghi["static_pass"] = t.ok
    if not t.ok:
        return {**ghi, "class": "FAIL_AFTER_REPAIR", "stage": "STATIC",
                "error": t.phan_hoi()[:400],
                "taxonomy": _taxonomy("STATIC", None, nhat.events)}

    g = check_grounding(contract, spec)
    ghi["grounding_pass"] = g.ok
    ghi["grounding_code"] = g.error_code
    if not g.ok:
        return {**ghi, "class": "FAIL_AFTER_REPAIR", "stage": "GROUNDING",
                "error": "; ".join(g.unresolved[:4]), "error_code": g.error_code,
                "taxonomy": _taxonomy("GROUNDING", g.error_code, nhat.events)}

    try:
        kq = SemanticProgramInterpreter().execute(spec)
    except Exception as e:  # noqa: BLE001
        return {**ghi, "class": "SYSTEM_FAILURE", "stage": "EXEC",
                "error": f"{type(e).__name__}: {e}", "taxonomy": "RUNTIME",
                "first_binding_runtime_failure":
                    "UNDECLARED" in str(getattr(e, "code", "") or "")}
    ghi["runtime_reached"] = True
    ghi["trace_steps"] = kq.total_steps
    ghi["first_binding_runtime_failure"] = False

    kr = verify_and_compile(contract, spec)
    ghi["checker_reached"] = True
    ghi["checker"] = {"checked": kr.constraints_checked,
                      "verified": kr.constraints_verified,
                      "executable": bool(kr.executable),
                      "servable": bool(kr.servable)}

    try:
        env = compile_semantic_program_to_envelope(spec)
        tr = check_envelope_transport(env)
    except Exception as e:  # noqa: BLE001
        tr = f"{type(e).__name__}: {e}"
    ghi["transport_pass"] = tr is None
    if tr is not None:
        return {**ghi, "class": "SYSTEM_FAILURE", "stage": "TRANSPORT",
                "error": str(tr)[:300], "taxonomy": "SYSTEM"}

    dung = True
    for khoa, nhan in (("dap_so", "oracle"), ("dap_so_phu", "oracle_phu")):
        if khoa not in case:
            continue
        mong = mong_doi(case[khoa])
        khop = [k for k, v in kq.final_memory.items() if bang(v, mong)]
        ghi[nhan] = str(mong)
        ghi[f"{nhan}_khop"] = khop
        dung = dung and bool(khop)
    if not dung:
        return {**ghi, "class": "EXECUTABLE_BUT_INCORRECT", "stage": "ORACLE",
                "error": "chạy được nhưng không khớp oracle tính tay",
                "taxonomy": "SYNTHESIS"}
    return {**ghi, "stage": "DONE", "taxonomy": None,
            "class": "ONE_SHOT_CORRECT" if ghi["one_shot"]
            else "REPAIRED_CORRECT"}


def _niem_phong(ra: Path) -> dict:
    prompt = BE / "app" / "ai" / "skills" / f"{_SKILL}.md"
    from app.main import CACHE_VERSION

    the = grammar_card(DOMAIN_HINH_HOC)
    d = {
        "khai": "CLEAN_BASELINE_V2 — niêm phong TRƯỚC khi gọi model.",
        "probe_id": "CLEAN_BASELINE_V2",
        "niem_phong_luc": datetime.now(timezone.utc).isoformat(),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=GOC,
                                 capture_output=True, text=True).stdout.strip(),
        "cay_sach": not subprocess.run(
            ["git", "status", "--porcelain"], cwd=GOC, capture_output=True,
            text=True).stdout.strip(),
        "canonical_domain": DOMAIN_HINH_HOC,
        "selected_skill": program_skill_for(DOMAIN_HINH_HOC),
        "cache_version": CACHE_VERSION,
        "prompt_hash": hashlib.sha256(prompt.read_bytes()).hexdigest()[:16],
        "prompt_bytes": len(prompt.read_bytes()),
        "model_card_hash": hashlib.sha256(
            the.encode("utf-8")).hexdigest()[:16],
        "model_card_bytes": len(the.encode("utf-8")),
        "hard_cap_tong_hop": TRAN_TONG_HOP, "tran_moi_de": TRAN_MOI_DE,
        "tien_kiem": tien_kiem(), "nhiem_cheo": check_contamination(),
        "manifest": [{"case_id": c["id"], "problem": c["de"],
                      "topology": c["topology"],
                      "capability_mix": c["capability_mix"],
                      "derived_entity_count": c["derived_entity_count"],
                      "expected_dependency_depth":
                          c["expected_dependency_depth"],
                      "obligation_count": c["obligation_count"],
                      "canonical_executable": True} for c in CASES],
    }
    d["probe_seal"] = hashlib.sha256(
        json.dumps(d["manifest"], ensure_ascii=False,
                   sort_keys=True).encode("utf-8")).hexdigest()[:16]
    (ra / "SEAL.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return d


async def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir",
                   default="../docs/evaluation/geometry/clean-baseline-v2")
    p.add_argument("--chi-niem-phong", action="store_true")
    a = p.parse_args()

    ra = Path(a.out_dir).resolve()
    ra.mkdir(parents=True, exist_ok=True)
    dich = ra / "probe.json"
    if dich.exists():
        print(f"✗ {dich} đã có — bộ đo TỪ CHỐI đè lượt cũ.")
        return 3

    d = _niem_phong(ra)
    print(f"━━ NIÊM PHONG · {d['probe_id']} ━━")
    print(f"  commit {d['commit'][:8]} · cây sạch {d['cay_sach']} · "
          f"CACHE_VERSION {d['cache_version']}")
    print(f"  miền {d['canonical_domain']} → {d['selected_skill']}")
    print(f"  prompt {d['prompt_bytes']}B ({d['prompt_hash']}) · "
          f"thẻ {d['model_card_bytes']}B ({d['model_card_hash']})")
    print(f"  seal {d['probe_seal']} · {len(d['manifest'])} đề")
    if d["tien_kiem"]:
        print("✗ TIỀN KIỂM ĐỎ — dừng, KHÔNG tiêu call:")
        for x in d["tien_kiem"]:
            print(f"    {x}")
        return 4
    print("  tiền kiểm: PASS")
    if d["nhiem_cheo"]:
        print("✗ NHIỄM CHÉO — dừng:")
        for x in d["nhiem_cheo"]:
            print(f"    {x}")
        return 4
    print("  nhiễm chéo: SẠCH")
    if a.chi_niem_phong:
        print(f"\n→ {ra / 'SEAL.json'} (0 call)")
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
        con_lai = TRAN_TONG_HOP - da_dung
        if con_lai <= 0:
            ket.append({"case_id": c["id"], "class": "NOT_RUN"})
            continue
        print(f"\n━━ {c['id']} ({c['topology']}) ━━")
        r = await _mot_de(c, key, con_lai)
        da_dung += r.get("logical_calls", 0)
        ket.append(r)
        fb = r.get("first_binding") or {}
        print(f"  {r.get('class')} · tổng hợp {r.get('logical_calls')} · "
              f"analyze {r.get('analyze_calls')} · token {r.get('total_tokens')}"
              f" · {r.get('taxonomy') or ''}")
        print(f"    ràng buộc: construct_point={fb.get('construct_point')} "
              f"assign_điểm={fb.get('assign_diem')}")
        if r.get("error"):
            print(f"    {' '.join(str(r['error']).split())[:170]}")

    def dem(*lop):
        return sum(1 for r in ket if r.get("class") in lop)

    def bo(k):
        return sum(r.get(k, 0) or 0 for r in ket)

    def bo2(a_, b_):
        return sum((r.get(a_) or {}).get(b_, 0) for r in ket)

    tax = [r.get("taxonomy") for r in ket]
    dung = dem("ONE_SHOT_CORRECT", "REPAIRED_CORRECT")
    mot = dem("ONE_SHOT_CORRECT")
    goi_th = bo("logical_calls")
    goi_an = bo("analyze_calls")
    tok = bo("total_tokens")
    cp = sum(len((r.get("first_binding") or {}).get("construct_point") or [])
             for r in ket)
    an = sum(len((r.get("first_binding") or {}).get("assign_diem") or [])
             for r in ket)
    he_lap = [x for x in set(tax) if x and tax.count(x) >= 2
              and x in ("SYSTEM", "RUNTIME", "PROVIDER")]

    bao = {
        "khai": "CLEAN_BASELINE_V2 — 6 đề mới, đường sản phẩm đầy đủ, sau bản "
                "sửa ràng buộc lần đầu. Chạy MỘT lần.",
        "probe_id": "CLEAN_BASELINE_V2",
        "chayLuc": datetime.now(timezone.utc).isoformat(),
        "seal": {k: d[k] for k in
                 ("commit", "cay_sach", "canonical_domain", "selected_skill",
                  "cache_version", "prompt_hash", "prompt_bytes",
                  "model_card_hash", "model_card_bytes", "probe_seal")},
        "new_code_required_during_probe": 0,
        "analyze_calls": goi_an, "initial_synthesis_calls": len(
            [r for r in ket if r.get("logical_calls")]),
        "repair_calls": max(goi_th - len(
            [r for r in ket if r.get("logical_calls")]), 0),
        "total_provider_calls": goi_an + goi_th,
        "one_shot_correct": mot, "repaired_correct": dem("REPAIRED_CORRECT"),
        "correct_within_budget": dung,
        "executable_but_incorrect": dem("EXECUTABLE_BUT_INCORRECT"),
        "fail_after_repair": dem("FAIL_AFTER_REPAIR"),
        "system_failure": dem("SYSTEM_FAILURE"),
        "synthesis_failure": tax.count("SYNTHESIS"),
        "schema_failure": tax.count("SCHEMA"),
        "grounding_failure": tax.count("GROUNDING"),
        "honesty_failure": tax.count("HONESTY"),
        "static_validation_failure": tax.count("STATIC_VALIDATION"),
        "first_binding_runtime_failures": sum(
            1 for r in ket if r.get("first_binding_runtime_failure")),
        "construct_point_selected": cp, "safe_assign_normalized": an,
        "unsafe_assign_rejected": tax.count("STATIC_VALIDATION"),
        "analyze_tokens": bo2("analyze_tokens", "total"),
        "initial_synthesis_tokens": bo("initial_synthesis_tokens"),
        "repair_tokens": bo("repair_tokens"),
        "total_tokens": tok,
        "tokens_per_correct_executable_ir": round(tok / dung) if dung else None,
        "tokens_per_one_shot_correct_ir": round(tok / mot) if mot else None,
        "average_provider_calls_per_success": (
            round((goi_an + goi_th) / dung, 2) if dung else None),
        "repair_token_share": (round(bo("repair_tokens") / tok, 3)
                               if tok else None),
        "envelope_transport": all(r.get("transport_pass", True) for r in ket),
        "system_pattern_repeated": bool(he_lap), "he_lap_lai": he_lap,
        "cases": ket,
    }
    dich.write_text(json.dumps(bao, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")

    print("\n━━ KẾT QUẢ · CLEAN_BASELINE_V2 ━━")
    print(f"  one-shot đúng        {mot}/{len(CASES)}")
    print(f"  đúng trong ngân sách {dung}/{len(CASES)}")
    print(f"  lỗi hệ               {dem('SYSTEM_FAILURE')}/{len(CASES)}")
    print(f"  tổng hợp sai         {tax.count('SYNTHESIS')} · schema "
          f"{tax.count('SCHEMA')} · grounding {tax.count('GROUNDING')} · "
          f"trung thực {tax.count('HONESTY')}")
    print(f"  FIRST_BINDING_RUNTIME_FAILURES  "
          f"{bao['first_binding_runtime_failures']}/{len(CASES)}")
    print(f"  construct_point chọn {cp} · assign điểm được chuẩn hoá {an}")
    print(f"  provider {goi_an + goi_th} lượt (analyze {goi_an} + tổng hợp "
          f"{goi_th}) · token {tok}")
    print(f"  SYSTEM_PATTERN_REPEATED: {bao['system_pattern_repeated']}")
    print(f"\n→ {dich}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
