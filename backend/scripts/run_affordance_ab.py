# -*- coding: utf-8 -*-
"""A/B ghép cặp cho `MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT`.

**TIÊU QUOTA THẬT.** `ALLOW_LIVE_AI=1` + `GEMINI_API_KEY` trong `backend/.env`.

    MEASUREMENT_CLASS = DEVELOPMENT_AB   ·   HELD_OUT_CLAIM = NO

─── GHÉP CẶP: MỘT `analyze`, HAI `synthesis` ────────────────────────────

`analyze` chạy **đúng một lần** cho mỗi đề, và `RequestContract` sinh ra được
dùng **y nguyên** cho cả hai arm. Nếu mỗi arm tự chạy analyze thì hai arm sẽ
nhận hai hợp đồng khác nhau — và khác biệt đo được sẽ lẫn nhiễu của một tầng
mà wave này không đụng tới.

Hai arm **chỉ** khác thẻ văn phạm. Cùng đề, cùng hợp đồng, cùng phần prompt còn
lại, cùng tham số giải mã, cùng engine thực thi.

─── ONE-SHOT LÀ CẤU HÌNH CỦA RUNNER, KHÔNG PHẢI CỦA SẢN PHẨM ───────────

Thí nghiệm hỏi *"lượt ĐẦU chọn gì"*, nên mỗi arm sinh đúng một ứng viên. Trần
ấy áp bằng cách hạ `MAX_SEMANTIC_PROGRAM_ATTEMPTS` **trong tiến trình runner**;
hằng số của sản phẩm không đổi, và `test_runner_affordance_ab` chứng minh điều
đó tại biên gọi provider.
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

from gold_affordance_ab import CORPUS, RA, _bam  # noqa: E402

MAX_LOGICAL = 24          # 8 analyze + 16 tổng hợp (2 arm × 8 đề)
MAX_PHYSICAL = 96         # × MAX_ATTEMPTS của transport


def _h(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


#: LỊCH CHẠY — khoá TRƯỚC khi xem kết quả.
#:
#: Luân phiên theo chỉ số ca: chẵn thì A trước, lẻ thì B trước. Thứ tự trong
#: một cặp không được là hằng, vì nếu provider có bất kỳ hiệu ứng thứ tự nào
#: thì nó sẽ dồn hết vào một arm.
def lich_chay(i: int) -> tuple[str, str]:
    return ("A", "B") if i % 2 == 0 else ("B", "A")


class NganSach:
    def __init__(self) -> None:
        self.physical = 0
        self.theo_stage: dict[str, int] = {}

    def ghi(self, stage: str) -> None:
        self.physical += 1
        self.theo_stage[stage] = self.theo_stage.get(stage, 0) + 1
        if self.physical > MAX_PHYSICAL:
            raise RuntimeError(f"VƯỢT TRẦN VẬT LÝ {MAX_PHYSICAL}")


class Quan:
    def __init__(self) -> None:
        self.su_kien: list[dict] = []

    def emit(self, loai: str, data: dict) -> None:
        self.su_kien.append({"loai": loai, **{
            k: (v if isinstance(v, (int, float, bool, type(None)))
                else str(v)[:8000]) for k, v in data.items()}})

    def raw_dau(self) -> str | None:
        for e in self.su_kien:
            if e["loai"] == "semantic_program_candidate":
                return e.get("raw")
        return None


# ══ CHẤM — truy TỪ KẾT QUẢ ĐƯỢC HỎI về producer của nó ═══════════════════
def _lenh_sinh(spec: dict, ten: str) -> dict | None:
    for st in spec.get("statements", []):
        if st.get("target_var") == ten:
            return st
    return None


def _kind_cua(st: dict | None) -> str | None:
    if not st:
        return None
    if st.get("kind") == "assign":
        return (st.get("expr") or {}).get("kind")
    if st.get("kind") == "construct_point":
        return (st.get("expr") or {}).get("kind")
    return st.get("kind")


def toan_tu_cho_ket_qua(spec: dict, ob: list[dict]) -> dict[str, Any]:
    """Phép nào SINH RA cái vật mà nghĩa vụ hỏi tới?

    ⚠️ Không đếm `intersect_plane_curved` ở bất kỳ đâu trong chương trình. Một
    phép giao dựng ra một vật phụ rồi đáp số lấy từ chỗ khác **không phải** là
    chọn đúng phép cho kết quả — nó chỉ là "có xuất hiện". Hai chuyện khác
    nhau, và gộp chúng là tự cho điểm.

    Đường truy: nghĩa vụ → `witness` → câu lệnh sinh witness (một `measure`)
    → toán hạng `of` của nó → câu lệnh sinh toán hạng ấy → `kind`.
    """
    ra: dict[str, Any] = {"per_obligation": [], "xuat_hien_bat_ky": False}
    for st in spec.get("statements", []):
        if _kind_cua(st) == "intersect_plane_curved":
            ra["xuat_hien_bat_ky"] = True
    for o in ob:
        w = (o.get("params") or {}).get("witness")
        m = _lenh_sinh(spec, w) if w else None
        e = (m or {}).get("expr") or {}
        of = e.get("of") if e.get("kind") == "measure" else None
        sinh = _lenh_sinh(spec, of) if of else None
        ra["per_obligation"].append({
            "kind": o.get("kind"), "witness": w, "of": of,
            "producer": _kind_cua(sinh),
            "declared_result_type": next(
                (d.get("type") for d in spec.get("memory_declarations", [])
                 if d.get("name") == of), None),
        })
    prods = {p["producer"] for p in ra["per_obligation"]}
    ra["producer_set"] = sorted(x for x in prods if x)
    return ra


def cham(ca: dict, spec: dict | None, out: Any, ob: list[dict],
         canh_ok: Any) -> dict[str, Any]:
    NR, NO = "NOT_REACHED", "NOT_OBSERVED"
    c: dict[str, Any] = {}
    if spec is None:
        c.update({k: NO for k in (
            "FIRST_ATTEMPT_OPERATOR_CORRECT", "ASSIGN_WRAPPER_CORRECT",
            "DECLARED_RESULT_TYPE", "INFERRED_RESULT_TYPE")})
        c["SCHEMA_VALIDATION_RESULT"] = "FAIL"
        for k in ("GROUNDING_RESULT", "COVERAGE_RESULT", "RUNTIME_RESULT",
                  "POSTCONDITIONS_RESULT", "EXACT_MATCH", "SCENE3D_RESULT"):
            c[k] = NR
        c["SERVABLE"] = "FAIL"
        return c

    c["SCHEMA_VALIDATION_RESULT"] = "PASS"
    tt = toan_tu_cho_ket_qua(spec, ob)
    c["_trace"] = tt
    mong = ca["expected_operator_class"]
    prods = tt["producer_set"]
    if mong == "refusal":
        c["FIRST_ATTEMPT_OPERATOR_CORRECT"] = NO       # ca âm chấm bằng BIÊN
    else:
        c["FIRST_ATTEMPT_OPERATOR_CORRECT"] = (
            "PASS" if prods == [mong] else "FAIL")
    c["INTERSECT_APPEARS_ANYWHERE"] = tt["xuat_hien_bat_ky"]
    c["DECLARED_RESULT_TYPE"] = sorted(
        {p["declared_result_type"] for p in tt["per_obligation"]} - {None})
    c["INFERRED_RESULT_TYPE"] = prods
    # `assign` là cửa tiêu thụ đúng của `intersect_plane_curved`.
    dung_assign = [
        (_lenh_sinh(spec, p["of"]) or {}).get("kind") == "assign"
        for p in tt["per_obligation"] if p["producer"] == "intersect_plane_curved"]
    c["ASSIGN_WRAPPER_CORRECT"] = ("PASS" if all(dung_assign) else "FAIL") \
        if dung_assign else NO

    stage = out.stage_reached
    c["GROUNDING_RESULT"] = "FAIL" if stage == "grounding" else (
        NR if stage in ("ir_static",) else "PASS")
    c["COVERAGE_RESULT"] = ("FAIL" if stage == "structural_coverage" else
                            (NR if stage in ("ir_static", "grounding") else "PASS"))
    c["RUNTIME_RESULT"] = ("FAIL" if stage == "execution" else
                           ("PASS" if out.executable else NR))
    c["POSTCONDITIONS_RESULT"] = ("PASS" if out.servable else
                                  ("FAIL" if stage == "postconditions" else NR))
    c["SERVABLE"] = "PASS" if out.servable else "FAIL"

    if mong == "refusal":
        ma = ca["expected_boundary"]
        c["BOUNDARY_RESULT"] = "PASS" if (
            not out.servable and any(ma in str(x)
                                     for x in (out.details or []))) else "FAIL"
        c["EXACT_MATCH"] = NO
    else:
        c["BOUNDARY_RESULT"] = NO
        if out.servable:
            mem = {str(v) for v in (out.final_memory or {}).values()}
            c["EXACT_MATCH"] = "PASS" if all(
                v in mem for v in ca["exact_expected_results"].values()) else "FAIL"
        else:
            c["EXACT_MATCH"] = NR
    c["SCENE3D_RESULT"] = ("PASS" if canh_ok else
                           ("FAIL" if out.servable else NR))
    return c


# ══ MỘT ARM ══════════════════════════════════════════════════════════════
async def chay_arm(ca, contract, the: str, api_key, ns) -> dict[str, Any]:
    from app.ai import pipeline
    from app.simulation.semantic_program import grammar_card as GC
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
    from app.simulation.semantic_program.route import verify_and_compile

    q = Quan()
    goc = GC.grammar_card
    GC.grammar_card = lambda domain=None: the       # type: ignore[assignment]
    try:
        spec, err = await pipeline.stage_semantic_program(
            ca["problem_text"], {}, api_key, contract,
            domain=DOMAIN_HINH_HOC, observer=q)
    finally:
        GC.grammar_card = goc                       # type: ignore[assignment]

    raw = q.raw_dau()
    ra: dict[str, Any] = {"card_hash": _h(the), "card_bytes": len(the.encode()),
                          "raw_candidate": raw, "loi": err,
                          "su_kien": q.su_kien}
    spec_json = None
    if spec is not None:
        spec_json = spec.model_dump(mode="json")
    elif raw:
        # Chương trình KHÔNG qua được lược đồ vẫn phải chấm được lựa chọn phép
        # — đó là toàn bộ lý do bộ chấm đọc raw.
        try:
            spec_json = json.loads(raw)
        except Exception:                                         # noqa: BLE001
            spec_json = None
    ra["chuong_trinh"] = spec_json

    class _Rong:
        stage_reached, executable, servable = "semantic_program", False, False
        error_code, details, final_memory = "semantic_program_invalid", [], {}

    out, canh_ok = _Rong(), False
    if spec is not None:
        out = verify_and_compile(contract, spec)
        try:
            canh = pipeline._dung_scene3d(spec, contract) or {}
            canh_ok = bool(out.servable and canh.get("objects"))
            ra["scene3d_objects"] = len(canh.get("objects", []))
        except Exception as e:                                    # noqa: BLE001
            ra["scene3d_loi"] = f"{type(e).__name__}: {str(e)[:200]}"
    ra.update(stage=out.stage_reached, servable=bool(out.servable),
              error_code=out.error_code,
              details=[str(x)[:300] for x in (out.details or [])],
              final_memory={k: str(v) for k, v in (out.final_memory or {}).items()})
    ob = [o.model_dump(mode="json") for o in contract.obligations]
    # Bộ chấm chỉ đọc `spec_json` — nếu lược đồ hỏng thì nó đọc raw đã parse,
    # và mọi cờ hạ nguồn là NOT_REACHED chứ không phải FAIL.
    ra["cham"] = cham(ca, spec_json if spec is not None else
                      (spec_json if spec_json else None), out, ob, canh_ok)
    if spec is None and spec_json is not None:
        ra["cham"]["SCHEMA_VALIDATION_RESULT"] = "FAIL"
    return ra


async def main_async(args) -> int:
    from acceptance_integrity import kiem_moi_truong, moi_truong_hien_tai
    from app.ai import gemini as G
    from app.ai import pipeline as PL
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
    from app.simulation.semantic_program.grammar_card import grammar_card

    if os.environ.get("ALLOW_LIVE_AI") != "1":
        print("ALLOW_LIVE_AI != 1 — từ chối tiêu quota."); return 2
    api_key = os.environ.get("GEMINI_API_KEY")
    print(f"GEMINI_API_KEY: {'PRESENT' if api_key else 'ABSENT'}")
    if not api_key:
        return 2

    card_A = (RA / "card_A.txt").read_text(encoding="utf-8")
    card_B = grammar_card("hinh_hoc")
    THE = {"A": card_A, "B": card_B}
    if _h(card_A) == _h(card_B):
        print("THẺ A ≡ THẺ B — không có gì để đo."); return 2

    moi_truong = moi_truong_hien_tai()
    ns = NganSach()
    goc_call = G.call_gemini

    async def dem(*a, **kw):
        from app.ai.telemetry import current_stage
        try:
            ns.ghi(str(current_stage()))
        except Exception:                                         # noqa: BLE001
            ns.ghi("?")
        return await goc_call(*a, **kw)

    ca_chay = [c for c in CORPUS
               if not args.ca or c["case_id"] in args.ca.split(",")]
    run_id = datetime.now(timezone.utc).strftime("ab-v1-%Y%m%dT%H%M%SZ")
    lich = {c["case_id"]: lich_chay(i) for i, c in enumerate(CORPUS)}
    manifest = {
        "run_id": run_id, "measurement_class": "DEVELOPMENT_AB",
        "held_out_claim": False,
        "baseline_candidate_hash": "a5b63aa3cb38e81f",
        "execution_candidate_hash": "67ad7f4ffb1a97ee",
        "card_A_hash": _h(card_A), "card_A_bytes": len(card_A.encode()),
        "card_B_hash": _h(card_B), "card_B_bytes": len(card_B.encode()),
        "corpus_hash": _bam([{k: v for k, v in c.items()
                              if k in ("case_id", "family", "feature",
                                       "problem_text")} for c in CORPUS]),
        "expected_results_hash": _bam([
            {k: v for k, v in c.items()
             if k in ("case_id", "expected_obligations",
                      "expected_operator_class", "expected_result_type",
                      "exact_expected_results", "expected_boundary")}
            for c in CORPUS]),
        "policy_hash": _bam(json.loads(
            (RA / "registration.json").read_text(encoding="utf-8"))),
        "runner_hash": _h(Path(__file__).read_text(encoding="utf-8")),
        "scorer_hash": _h(Path(__file__).read_text(encoding="utf-8")),
        "model_provider": "google-generativelanguage-v1beta",
        "model_name": G.MODEL, "model_version_or_snapshot": "",
        "temperature_analyze": 0.1, "temperature_synthesis": 0.1,
        "top_p": None, "max_output_tokens": None,
        "repair_calls_configured": 0,
        "product_repair_limit_unchanged": PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS,
        "transport_max_attempts": G.MAX_ATTEMPTS,
        "logical_budget": MAX_LOGICAL, "physical_budget": MAX_PHYSICAL,
        "case_order": {k: list(v) for k, v in lich.items()},
        "moi_truong": moi_truong,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    RA.mkdir(parents=True, exist_ok=True)
    (RA / f"manifest_{run_id}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MANIFEST trước lượt gọi đầu → manifest_{run_id}.json")
    print(f"  A={manifest['card_A_hash'][:16]}… ({manifest['card_A_bytes']}B)"
          f"  B={manifest['card_B_hash'][:16]}… ({manifest['card_B_bytes']}B)")
    print(f"  corpus={manifest['corpus_hash'][:16]}…  lịch={manifest['case_order']}\n")

    G.call_gemini = dem                             # type: ignore[assignment]
    PL.call_gemini = dem                            # type: ignore[assignment]
    goc_tran = PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS = 1            # ONE-SHOT, chỉ ở runner
    kq = []
    try:
        for c in ca_chay:
            print(f"── {c['case_id']} ({c['family']})", flush=True)
            kiem_moi_truong(moi_truong, nhan=c["case_id"])
            contract, err = await PL.stage_semantic_analyze(
                c["problem_text"], api_key, domain=DOMAIN_HINH_HOC)
            r: dict[str, Any] = {"case_id": c["case_id"],
                                 "thu_tu": list(lich[c["case_id"]])}
            if contract is None:
                r.update(analyze_loi=err, arms={})
                print(f"   ANALYZE HỎNG: {str(err)[:120]}")
                kq.append(r); continue
            r["request_contract"] = {
                "problem_text": contract.problem_text,
                "input_facts": [f.model_dump(mode="json")
                                for f in contract.input_facts],
                "obligations": [o.model_dump(mode="json")
                                for o in contract.obligations]}
            arms = {}
            for arm in lich[c["case_id"]]:
                arms[arm] = await chay_arm(c, contract, THE[arm], api_key, ns)
                a = arms[arm]["cham"]
                print(f"   [{arm}] op={a.get('FIRST_ATTEMPT_OPERATOR_CORRECT')}"
                      f" producer={a.get('INFERRED_RESULT_TYPE')}"
                      f" kiểu={a.get('DECLARED_RESULT_TYPE')}"
                      f" stage={arms[arm]['stage']}"
                      f" servable={arms[arm]['servable']}"
                      f" exact={a.get('EXACT_MATCH')}")
            r["arms"] = arms
            kq.append(r)
    finally:
        G.call_gemini = goc_call                    # type: ignore[assignment]
        PL.call_gemini = goc_call                   # type: ignore[assignment]
        PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS = goc_tran

    from app.ai.telemetry import total_tokens, usage_report
    try:
        tk = {"theo_stage": usage_report(), "tong": total_tokens()}
    except Exception:                                             # noqa: BLE001
        tk = {}
    logic = sum(v.get("calls", 0) for v in (tk.get("theo_stage") or {}).values())
    out = {"manifest": {**manifest,
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                        "logical_calls_used_telemetry": logic,
                        "physical_attempts_used": ns.physical,
                        "physical_by_stage": ns.theo_stage},
           "tokens": tk, "ket_qua": kq}
    (RA / f"ab_{run_id}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nLOGICAL={logic}/{MAX_LOGICAL}  PHYSICAL={ns.physical}/{MAX_PHYSICAL}")
    print(f"→ {RA / f'ab_{run_id}.json'}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ca", default=None)
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass
    return asyncio.run(main_async(p.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
