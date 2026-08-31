# -*- coding: utf-8 -*-
"""CLEAN_BASELINE_V1 — 6 đề mới, đường sản phẩm đầy đủ, runtime đóng băng.

    đề → analyze (LLM) → RequestContract → tổng hợp (LLM) → validator
       → thẩm định tĩnh → grounding + trung thực → thực thi → oracle
       → hậu điều kiện → envelope + cổng vận chuyển

⚠️ **TIÊU QUOTA THẬT.** `ALLOW_LIVE_AI=1` + `GEMINI_API_KEY`.
Trần cứng **12 lượt TỔNG HỢP**; analyze đếm riêng và báo riêng.

─── VÌ SAO CÓ ANALYZE, DÙ NÓ TỐN THÊM ─────────────────────────────────────

Ba tuyến đo trước đều bỏ `stage_semantic_analyze` để tiết kiệm token, nên
`RequestContract` **rỗng**: không `input_facts`, không nghĩa vụ. Hệ quả đo
được ở fresh-probe lượt 1: hai ca chết vì *"`source_fact_id` không có trong
RequestContract"* — mô hình trích dẫn đúng một dữ kiện mà hợp đồng không có,
vì ta đã bỏ tầng sinh ra dữ kiện.

Tiết kiệm token ở đó không phải tiết kiệm: nó đo một hệ khác hệ sản phẩm, rồi
tính lỗi của phép đo thành lỗi của mô hình.

─── TIỀN KIỂM (§1) — CHẠY TRƯỚC KHI TIÊU MỘT CALL NÀO ─────────────────────

Miền phải là hằng số của sản phẩm, và `program_skill_for` phải trả skill hình
học. Lỗi này đã cắn **ba** lần (chuỗi `"geometry"` ở hai runner, tham số bị bỏ
quên ở runner thứ ba), nên nó được kiểm ở đây chứ không được tin.

─── ĐIỀU BỘ ĐO KHÔNG LÀM ──────────────────────────────────────────────────

Không sửa chương trình mô hình sinh. Không gợi ý. Không chạy lại đề đã hỏng.
Không sửa code hay prompt giữa các đề. Không đè artifact lượt cũ.
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
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402
from app.simulation.semantic_program.transport import (  # noqa: E402
    check_envelope_transport,
)
from scripts.clean_baseline_cases import CASES, check_contamination  # noqa: E402
from scripts.verify_baseline_expressibility import bang, mong_doi  # noqa: E402

TRAN_TONG_HOP = 12
TRAN_MOI_DE = 2
_KHONG_SUA = {ERR_RUA_NANG_LUC, ERR_THIEU_NGUOI_DUNG}
_SKILL = "geometry_program_generator"


# ══ §1 TIỀN KIỂM ════════════════════════════════════════════════════════
def tien_kiem() -> list[str]:
    """Trả danh sách lỗi. Rỗng = được phép gọi API."""
    loi = []
    try:
        sk = program_skill_for(DOMAIN_HINH_HOC)
    except Exception as e:  # noqa: BLE001
        return [f"program_skill_for({DOMAIN_HINH_HOC!r}) ném: {e}"]
    if sk != _SKILL:
        loi.append(f"skill tổng hợp là {sk!r}, mong {_SKILL!r}")
    if sk == "semantic_program":
        loi.append("skill tổng hợp là bản TIN HỌC — đúng lỗi đã cắn ba lần")
    # Miền lạ phải NÉM, không được rơi vào Tin học.
    for xau in ("geometry", "hinh hoc", ""):
        try:
            program_skill_for(xau)
        except Exception:
            continue
        loi.append(f"miền lạ {xau!r} KHÔNG ném — cửa `else` còn mở")
    the = grammar_card(DOMAIN_HINH_HOC)
    if "measure" not in the or "angle_cos_sq" not in the:
        loi.append("thẻ văn phạm hình học thiếu bảng phép đo")
    if len(the) >= len(grammar_card(None)):
        loi.append("thẻ hình học không hẹp hơn thẻ đầy đủ")
    return loi


class _Nhat:
    """Observer THỤ ĐỘNG. Hợp đồng là `emit(event_type, data)`."""

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


def _taxonomy(stage: str, ma: str | None, su_kien: list[dict]) -> str:
    """§12 — chỉ chín nhãn. `SYNTHESIS` KHÔNG được gắn khi chương trình đúng
    mà hệ chặn sai; ca ấy là `SYSTEM`."""
    if ma in _KHONG_SUA:
        return "HONESTY"
    van = " ".join(str(e.get("message") or "") for e in su_kien)
    return {
        "ANALYZE": "PROVIDER", "SYNTHESIS": (
            "SCHEMA" if ("validation error" in van or "schema" in van)
            else "SYNTHESIS"),
        "STATIC": "STATIC_VALIDATION", "GROUNDING": "GROUNDING",
        "EXEC": "RUNTIME", "CHECKER": "CHECKER", "TRANSPORT": "SYSTEM",
        "ORACLE": "SYNTHESIS",
    }.get(stage, "SYSTEM")


async def _mot_de(case: dict, api_key: str, con_lai: int) -> dict:
    reset_usage()
    dem = {"analyze": 0, "tong_hop": 0, "attempted": 0}
    nhat = _Nhat()
    bat_dau = time.monotonic()
    goc = PL.call_gemini
    giai_doan = {"ten": "ANALYZE"}

    async def dem_call(*a, **kw):
        if giai_doan["ten"] == "ANALYZE":
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

    ghi: dict = {
        "case_id": case["id"], "topology": case["topology"],
        "capability_mix": case["capability_mix"],
        "expected_depth": case["expected_depth"],
        "obligation_count": case["obligation_count"],
        "domain": DOMAIN_HINH_HOC, "selected_skill": _SKILL,
        "prompt_hash": hashlib.sha256(
            load_skill(_SKILL).encode("utf-8")).hexdigest()[:16],
    }

    PL.call_gemini = dem_call
    try:
        # ── TẦNG 1: ANALYZE (đường sản phẩm, KHÔNG bỏ) ──────────────────
        contract, aerr = await PL.stage_semantic_analyze(
            case["de"], api_key, domain=DOMAIN_HINH_HOC)
        if contract is None:
            return {**ghi, "class": "SYSTEM_FAILURE", "stage": "ANALYZE",
                    "error": aerr, "taxonomy": "PROVIDER",
                    "analyze_calls": dem["analyze"], "logical_calls": 0,
                    "total_tokens": total_tokens()}
        ghi["request_contract"] = {
            "input_facts": len(contract.input_facts),
            "obligations": sorted({o.kind for o in contract.obligations}),
            "problem_text_len": len(contract.problem_text or "")}

        # ── TẦNG 2: TỔNG HỢP ────────────────────────────────────────────
        giai_doan["ten"] = "SYNTHESIS"
        spec, serr = await PL.stage_semantic_program(
            case["de"], {}, api_key, contract, observer=nhat,
            domain=DOMAIN_HINH_HOC)
    except RuntimeError as e:
        spec, serr = None, str(e)
    finally:
        PL.call_gemini = goc

    u = (usage_report() or {}).get("semantic_program") or {}
    ghi.update({
        "analyze_calls": dem["analyze"], "logical_calls": dem["tong_hop"],
        "attempts": dem["attempted"], "one_shot": dem["attempted"] == 1,
        "input_tokens": u.get("prompt_tokens", 0),
        "output_tokens": u.get("candidates_tokens", 0),
        "total_tokens": total_tokens(),
        "tokens_per_attempt": nhat.tokens_moi_luot,
        "latency_s": round(time.monotonic() - bat_dau, 2),
        "attempts_log": nhat.events, "programs": nhat.raws,
    })

    if spec is None:
        ma = next((h for e in nhat.events for h in _KHONG_SUA
                   if h in str(e.get("message") or "")), None)
        return {**ghi, "class": "FAIL_AFTER_REPAIR", "stage": "SYNTHESIS",
                "error": serr, "error_code": ma,
                "taxonomy": _taxonomy("SYNTHESIS", ma, nhat.events)}

    ghi["program_hash"] = hashlib.sha256(
        json.dumps(spec.model_dump(mode="json"), ensure_ascii=False,
                   sort_keys=True).encode("utf-8")).hexdigest()[:16]
    ghi["normalized_program"] = spec.model_dump(mode="json")
    ghi["statements"] = [s.kind for s in spec.statements]
    ghi["angle_measures"] = [
        {"quantity": st.expr.quantity, "of": st.expr.of, "wrt": st.expr.wrt}
        for st in spec.statements
        if getattr(getattr(st, "expr", None), "kind", "") == "measure"
        and "angle" in getattr(st.expr, "quantity", "")]

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
                "error": f"{type(e).__name__}: {e}", "taxonomy": "RUNTIME"}
    ghi["runtime_reached"] = True
    ghi["trace_steps"] = kq.total_steps

    # ── HẬU ĐIỀU KIỆN + BIÊN DỊCH (cùng cổng sản phẩm) ──────────────────
    kq_route = verify_and_compile(contract, spec)
    ghi["checker_reached"] = True
    ghi["checker_constraints"] = {
        "checked": kq_route.constraints_checked,
        "verified": kq_route.constraints_verified}
    ghi["route_executable"] = bool(kq_route.executable)
    ghi["route_servable"] = bool(kq_route.servable)

    # ── ORACLE ──────────────────────────────────────────────────────────
    mem = kq.final_memory
    dung = True
    for khoa, nhan in (("dap_so", "oracle"), ("dap_so_phu", "oracle_phu")):
        if khoa not in case:
            continue
        mong = mong_doi(case[khoa])
        khop = [k for k, v in mem.items() if bang(v, mong)]
        ghi[nhan] = str(mong)
        ghi[f"{nhan}_khop"] = khop
        dung = dung and bool(khop)

    # ── CỔNG VẬN CHUYỂN (§13 — bắt buộc cho "đúng") ────────────────────
    tr = None
    try:
        # Cùng hàm sản phẩm dùng để dựng envelope — nó tự thực thi lại spec,
        # nên đây là đường đi THẬT tới `json.dumps`, không phải một bản dựng
        # riêng cho bộ đo. `fp` của wave trước chết đúng ở chỗ này sau khi mọi
        # cổng đã nói PASS.
        from app.simulation.semantic_program.pipeline_adapter import (
            compile_semantic_program_to_envelope,
        )
        env = compile_semantic_program_to_envelope(spec)
        tr = check_envelope_transport(env)
    except Exception as e:  # noqa: BLE001
        tr = f"không dựng được envelope: {type(e).__name__}: {e}"
    ghi["transport_pass"] = tr is None
    if tr is not None:
        return {**ghi, "class": "SYSTEM_FAILURE", "stage": "TRANSPORT",
                "error": str(tr)[:300], "taxonomy": "SYSTEM"}

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
    dau = {
        "khai": "CLEAN_BASELINE_V1 — niêm phong TRƯỚC khi gọi model.",
        "probe_id": "CLEAN_BASELINE_V1",
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
        "the_hash": hashlib.sha256(the.encode("utf-8")).hexdigest()[:16],
        "the_bytes": len(the.encode("utf-8")),
        "hard_cap_tong_hop": TRAN_TONG_HOP, "tran_moi_de": TRAN_MOI_DE,
        "tien_kiem": tien_kiem(),
        "nhiem_cheo": check_contamination(),
        "manifest": [{"case_id": c["id"], "problem_text": c["de"],
                      "topology": c["topology"],
                      "capability_mix": c["capability_mix"],
                      "expected_depth": c["expected_depth"],
                      "obligation_count": c["obligation_count"]}
                     for c in CASES],
    }
    dau["seal_hash"] = hashlib.sha256(
        json.dumps(dau["manifest"], ensure_ascii=False,
                   sort_keys=True).encode("utf-8")).hexdigest()[:16]
    (ra / "SEAL.json").write_text(
        json.dumps(dau, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return dau


async def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir",
                   default="../docs/evaluation/geometry/clean-baseline-v1")
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
    print(f"  miền {d['canonical_domain']} → skill {d['selected_skill']}")
    print(f"  prompt {d['prompt_bytes']}B ({d['prompt_hash']}) · "
          f"thẻ {d['the_bytes']}B ({d['the_hash']})")
    print(f"  seal {d['seal_hash']} · {len(d['manifest'])} đề · "
          f"trần tổng hợp {d['hard_cap_tong_hop']}")
    if d["tien_kiem"]:
        print("✗ TIỀN KIỂM ĐỎ — dừng, KHÔNG tiêu call:")
        for x in d["tien_kiem"]:
            print(f"    {x}")
        return 4
    print("  tiền kiểm: PASS")
    if d["nhiem_cheo"]:
        print("✗ NHIỄM CHÉO — dừng, KHÔNG tiêu call:")
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
            ket.append({"case_id": c["id"], "class": "NOT_RUN",
                        "error": "chạm trần tổng hợp"})
            print(f"\n━━ {c['id']} — DỪNG: chạm trần {TRAN_TONG_HOP}")
            continue
        print(f"\n━━ {c['id']} ({c['topology']}) ━━")
        r = await _mot_de(c, key, con_lai)
        da_dung += r.get("logical_calls", 0)
        ket.append(r)
        print(f"  {r.get('class')} · tổng hợp {r.get('logical_calls')} · "
              f"analyze {r.get('analyze_calls')} · token {r.get('total_tokens')}"
              f" · {r.get('taxonomy') or ''}")
        if r.get("error"):
            print(f"    {' '.join(str(r['error']).split())[:170]}")

    def dem(*lop):
        return sum(1 for r in ket if r.get("class") in lop)

    def bo(k):
        return sum(r.get(k, 0) or 0 for r in ket)

    tax = [r.get("taxonomy") for r in ket]
    dung = dem("ONE_SHOT_CORRECT", "REPAIRED_CORRECT")
    mot = dem("ONE_SHOT_CORRECT")
    goi = bo("logical_calls")
    tok = bo("total_tokens")
    tok_sua = sum(sum(r.get("tokens_per_attempt", [])[1:]) for r in ket)

    bao = {
        "khai": "CLEAN_BASELINE_V1 — 6 đề mới, đường sản phẩm đầy đủ (có "
                "analyze), runtime đóng băng. Chạy MỘT lần.",
        "probe_id": "CLEAN_BASELINE_V1",
        "chayLuc": datetime.now(timezone.utc).isoformat(),
        "seal": {k: d[k] for k in ("commit", "cay_sach", "canonical_domain",
                                   "selected_skill", "cache_version",
                                   "prompt_hash", "prompt_bytes", "the_hash",
                                   "seal_hash", "hard_cap_tong_hop")},
        "new_code_required_during_probe": 0,
        "logical_call_hard_cap": TRAN_TONG_HOP,
        "logical_calls_used": goi, "analyze_calls": bo("analyze_calls"),
        "initial_calls": sum(1 for r in ket if r.get("logical_calls")),
        "repair_calls": max(goi - sum(1 for r in ket
                                      if r.get("logical_calls")), 0),
        "one_shot_correct": mot, "repaired_correct": dem("REPAIRED_CORRECT"),
        "correct_within_budget": dung,
        "executable_but_incorrect": dem("EXECUTABLE_BUT_INCORRECT"),
        "fail_after_repair": dem("FAIL_AFTER_REPAIR"),
        "system_failure": dem("SYSTEM_FAILURE"),
        "honesty_failure": tax.count("HONESTY"),
        "grounding_failure": tax.count("GROUNDING"),
        "schema_failure": tax.count("SCHEMA"),
        "synthesis_failure": tax.count("SYNTHESIS"),
        "static_validation_failure": tax.count("STATIC_VALIDATION"),
        "total_input_tokens": bo("input_tokens"),
        "total_output_tokens": bo("output_tokens"),
        "total_tokens": tok,
        "tokens_per_correct_executable_ir": round(tok / dung) if dung else None,
        "average_calls_per_success": round(goi / dung, 2) if dung else None,
        "repair_token_share": round(tok_sua / tok, 3) if tok else None,
        "one_shot_token_share": round(1 - tok_sua / tok, 3) if tok else None,
        "envelope_transport": all(r.get("transport_pass", True) for r in ket),
        "cases": ket,
    }
    dich.write_text(json.dumps(bao, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")

    print("\n━━ KẾT QUẢ · CLEAN_BASELINE_V1 ━━")
    print(f"  one-shot đúng        {mot}/{len(CASES)}")
    print(f"  đúng trong ngân sách {dung}/{len(CASES)}")
    print(f"  hỏng sau sửa         {dem('FAIL_AFTER_REPAIR')}/{len(CASES)}")
    print(f"  lỗi hệ               {dem('SYSTEM_FAILURE')}/{len(CASES)}")
    print(f"  schema {tax.count('SCHEMA')} · grounding "
          f"{tax.count('GROUNDING')} · trung thực {tax.count('HONESTY')} · "
          f"tổng hợp {tax.count('SYNTHESIS')}")
    print(f"  tổng hợp {goi}/{TRAN_TONG_HOP} · analyze "
          f"{bo('analyze_calls')} · token {tok}")
    print(f"\n→ {dich}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
