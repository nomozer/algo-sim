# -*- coding: utf-8 -*-
"""Probe phát triển: mô hình có TỰ TÌM RA `intersect_plane_curved` không?

**TIÊU QUOTA THẬT.** Cần `ALLOW_LIVE_AI=1` và `GEMINI_API_KEY` trong `backend/.env`.

    MEASUREMENT_CLASS = DEVELOPMENT_DIAGNOSTIC
    HELD_OUT_CLAIM    = NO       (corpus do người viết, đã công bố)
    V3 KHÔNG bị đụng tới ở bất kỳ đường nào.

─── RANH GIỚI RUNNER ↔ SCORER ────────────────────────────────────────────

Runner gửi cho mô hình **đúng `problem_text`** và không gì khác — cùng hai
stage mà sản phẩm gọi (`stage_semantic_analyze`, `stage_semantic_program`).
`expected_operator_class`, `expected_result_type`, `exact_expected_results`
**chỉ** được scorer đọc, sau khi chương trình đã sinh xong. Trộn hai vai là
cách một phép đo tự cho mình điểm.

─── VÌ SAO CHỌN TOÁN TỬ ĐƯỢC CHẤM TỪ VĂN BẢN IR ─────────────────────────

Không từ `servable`. Câu hỏi của wave là *"mô hình có tìm ra phép đúng không"*,
và câu ấy trả lời được ngay cả khi một tầng hạ nguồn hỏng. Buộc nó vào kết quả
thực thi là để một lỗi kernel viết lại kết luận về hành vi mô hình — đúng thứ
`measurement_policy.json` đăng ký hazard để tránh.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
for p in (str(BACKEND), str(BACKEND / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from gold_section_discoverability import CORPUS, RA, _bam  # noqa: E402

MAX_LOGICAL = 32          # 8 analyze + 8 tổng hợp đầu + 16 lượt sửa
MAX_PHYSICAL = 128        # × MAX_ATTEMPTS của transport


class NganSach:
    """Trần lượt gọi — **cứng**. Vượt là NÉM, không phải cảnh báo.

    Đếm ở biên `call_gemini`, tức đếm lượt gọi VẬT LÝ thật sự rời tiến trình,
    không đếm ý định gọi. Một trần chỉ được kiểm ở tầng ý định sẽ bỏ sót đúng
    phần retry mà nó sinh ra để chặn.
    """

    def __init__(self) -> None:
        self.logical = 0
        self.logical_telemetry = 0
        self.physical = 0
        self.theo_stage: dict[str, int] = {}

    def ghi(self, stage: str) -> None:
        self.physical += 1
        self.theo_stage[stage] = self.theo_stage.get(stage, 0) + 1
        if self.physical > MAX_PHYSICAL:
            raise RuntimeError(
                f"VƯỢT TRẦN VẬT LÝ {MAX_PHYSICAL} — dừng để không tiêu thêm")


class Quan:
    """Observer THỤ ĐỘNG — chỉ ghi, không đổi hành vi (bất biến #22)."""

    def __init__(self) -> None:
        self.su_kien: list[dict] = []

    def emit(self, loai: str, data: dict) -> None:
        self.su_kien.append({"loai": loai, **{
            k: (v if isinstance(v, (int, float, bool, type(None)))
                else str(v)[:4000]) for k, v in data.items()}})


# ══ CHẤM — mọi cờ của §5 ═════════════════════════════════════════════════
def _cac_lenh(spec_json: dict) -> list[dict]:
    return spec_json.get("statements", []) if spec_json else []


def _toan_tu_da_chon(spec_json: dict) -> dict[str, Any]:
    """Đọc lựa chọn toán tử từ VĂN BẢN chương trình.

    Ba hình dạng phải phân biệt được, vì chúng là ba câu trả lời khác nhau:
      · `construct_section`                      — câu lệnh, khối đa diện
      · `assign ← intersect_plane_curved`        — ĐÚNG cho khối cong
      · `intersect_plane_curved` như CÂU LỆNH    — lược đồ không có, nhưng mô
        hình có thể bịa; phải đếm riêng chứ không gộp vào 'sai toán tử'
    """
    ra = {"construct_section": 0, "intersect_in_assign": 0,
          "intersect_as_statement": 0, "target_circle3": [],
          "target_section": []}
    for st in _cac_lenh(spec_json):
        k = st.get("kind")
        if k == "construct_section":
            ra["construct_section"] += 1
            ra["target_section"].append(st.get("target_var"))
        elif k == "intersect_plane_curved":
            ra["intersect_as_statement"] += 1
        elif k == "assign":
            if (st.get("expr") or {}).get("kind") == "intersect_plane_curved":
                ra["intersect_in_assign"] += 1
                ra["target_circle3"].append(st.get("target_var"))
    return ra


def _kieu_khai(spec_json: dict) -> dict[str, str]:
    return {d["name"]: d.get("type")
            for d in (spec_json or {}).get("memory_declarations", [])}


def _cach_khai_khoi(spec_json: dict) -> list[str]:
    """Khai khối cong bằng ĐIỂM hay bằng VÔ HƯỚNG? — hazard đã đăng ký."""
    ra = []
    for st in _cac_lenh(spec_json):
        if st.get("kind") != "construct_curved_solid":
            continue
        if st.get("height"):
            ra.append("height_scalar")
        elif st.get("apex_or_top"):
            ra.append("apex_point")
        else:
            ra.append("ball_or_other")
    return ra


def cham(ca: dict, ra: dict) -> dict[str, Any]:
    """Chấm một ca theo đúng các chiều §5. KHÔNG đọc kết quả để suy toán tử."""
    spec_json = ra.get("chuong_trinh")
    tt = _toan_tu_da_chon(spec_json) if spec_json else {}
    khai = _kieu_khai(spec_json) if spec_json else {}
    mong_lop = ca["expected_operator_class"]

    c: dict[str, Any] = {}
    c["ANALYZE_CONTRACT_CORRECT"] = ra.get("contract_ok", False)
    got = sorted({o["kind"] for o in
                  (ra.get("request_contract") or {}).get("obligations", [])})
    c["OBLIGATIONS_COMPLETE"] = got == sorted(ca["expected_obligations"])
    c["OBLIGATIONS_SEEN"] = got
    c["SYNTHESIS_SCHEMA_VALID"] = ra.get("schema_ok", False)

    if not spec_json:
        c["SELECTED_OPERATOR"] = None
        c["OPERATOR_CLASS_CORRECT"] = False
    else:
        if tt["intersect_in_assign"] or tt["intersect_as_statement"]:
            chon = "intersect_plane_curved"
        elif tt["construct_section"]:
            chon = "construct_section"
        else:
            chon = "none"
        c["SELECTED_OPERATOR"] = chon
        if mong_lop == "refusal":
            # Ca âm: "đúng" nghĩa là hệ từ chối có cấu trúc; mô hình được phép
            # thử đường cong — nó không có cách nào biết trước bao đóng v1.
            c["OPERATOR_CLASS_CORRECT"] = None
        else:
            c["OPERATOR_CLASS_CORRECT"] = (chon == mong_lop)

    c["USED_ASSIGN_WRAPPER"] = (bool(tt.get("intersect_in_assign"))
                                and not tt.get("intersect_as_statement")
                                if spec_json else None)
    c["INTERSECT_AS_STATEMENT"] = bool(tt.get("intersect_as_statement"))
    tgt = (tt.get("target_circle3") or []) + (tt.get("target_section") or [])
    c["DECLARED_RESULT_TYPE"] = sorted({khai.get(t) for t in tgt} - {None})
    c["RESULT_TYPE_IS_CIRCLE3"] = (
        all(khai.get(t) == "circle3" for t in (tt.get("target_circle3") or []))
        if tt.get("target_circle3") else False)
    c["CURVED_SOLID_DECLARATION"] = _cach_khai_khoi(spec_json) if spec_json else []

    c["GROUNDED"] = ra.get("stage") not in ("grounding",) and ra.get("schema_ok")
    c["STATIC_VALID"] = ra.get("stage") not in ("ir_static",)
    c["COVERAGE_PASS"] = ra.get("stage") not in ("structural_coverage",)
    c["RUNTIME_EXECUTABLE"] = ra.get("executable", False)
    c["POSTCONDITIONS_PASS"] = ra.get("stage") == "served" or ra.get("servable")
    c["SCENE3D_PASS"] = ra.get("scene3d_ok", False)
    c["REPAIR_COUNT"] = ra.get("repair_count", 0)
    c["FIRST_ATTEMPT_SERVABLE"] = bool(ra.get("servable")) and c["REPAIR_COUNT"] == 0
    c["EVENTUAL_SERVABLE"] = bool(ra.get("servable"))

    if mong_lop == "refusal":
        ma = ca["expected_boundary"]
        c["BOUNDARY_CORRECT"] = (not ra.get("servable") and any(
            ma in str(x) for x in (ra.get("details") or [])))
        c["EXACT_ANSWER_MATCH"] = None
    else:
        c["BOUNDARY_CORRECT"] = None
        mem = ra.get("final_memory") or {}
        mong = ca["exact_expected_results"]
        # Đối chiếu theo GIÁ TRỊ có mặt trong bộ nhớ cuối: tên witness do mô
        # hình đặt, nên khoá theo tên là khoá vào chính tả của nó.
        co = set(mem.values())
        c["EXACT_ANSWER_MATCH"] = bool(mong) and all(v in co for v in mong.values())
        c["FINAL_MEMORY_SCALARS"] = sorted(co)

    # ── QUY KẾT ─────────────────────────────────────────────────────────
    if c["EVENTUAL_SERVABLE"] or c["BOUNDARY_CORRECT"]:
        c["FAILURE_OWNER"] = None
    elif "[ZeroDivisionError]" in str(ra.get("details")):
        # Hazard ĐÃ ĐĂNG KÝ TRƯỚC LƯỢT ĐO — xem `measurement_policy.json`.
        c["FAILURE_OWNER"] = "SYSTEM"
        c["SYSTEM_FAILURE_ID"] = "CURVED_SCALAR_DECLARED_SOLID_CANNOT_BE_CUT"
    elif c["OPERATOR_CLASS_CORRECT"] is False or not c["SYNTHESIS_SCHEMA_VALID"]:
        c["FAILURE_OWNER"] = "MODEL"
    elif not c["GROUNDED"] or not c["STATIC_VALID"] or not c["COVERAGE_PASS"]:
        c["FAILURE_OWNER"] = "MODEL"
    else:
        c["FAILURE_OWNER"] = "UNRESOLVED"
    return c


# ══ MỘT CA ═══════════════════════════════════════════════════════════════
async def chay_mot(ca: dict, api_key: str, ns: NganSach) -> dict[str, Any]:
    from app.ai import pipeline
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
    from app.simulation.semantic_program.route import verify_and_compile
    from acceptance_integrity import kiem_moi_truong

    kiem_moi_truong(MOI_TRUONG, nhan=ca["case_id"])

    ra: dict[str, Any] = {"case_id": ca["case_id"], "contract_ok": False,
                          "schema_ok": False, "executable": False,
                          "servable": False, "repair_count": 0}
    q = Quan()
    t0 = time.time()

    contract, err = await pipeline.stage_semantic_analyze(
        ca["problem_text"], api_key, domain=DOMAIN_HINH_HOC)
    ns.logical += 1
    if contract is None:
        ra.update(loi=err, stage="semantic_analyze", su_kien=q.su_kien)
        return ra
    ra["contract_ok"] = True
    ra["request_contract"] = {
        "problem_text": contract.problem_text,
        "input_facts": [f.model_dump(mode="json") for f in contract.input_facts],
        "obligations": [o.model_dump(mode="json") for o in contract.obligations]}

    spec, serr = await pipeline.stage_semantic_program(
        ca["problem_text"], {}, api_key, contract, domain=DOMAIN_HINH_HOC,
        observer=q)
    ra["repair_count"] = max(0, sum(
        1 for e in q.su_kien if e["loai"] == "semantic_program_attempt") - 1)
    ns.logical += 1 + ra["repair_count"]
    ra["su_kien"] = q.su_kien
    if spec is None:
        ra.update(loi=serr, stage="semantic_program", giay=round(time.time()-t0, 1))
        return ra
    ra["schema_ok"] = True
    ra["chuong_trinh"] = spec.model_dump(mode="json")

    outcome = verify_and_compile(contract, spec)
    ra.update(stage=outcome.stage_reached, executable=bool(outcome.executable),
              servable=bool(outcome.servable), error_code=outcome.error_code,
              failure_category=getattr(outcome, "failure_category", None),
              details=[str(x)[:300] for x in (outcome.details or [])],
              final_memory={k: str(v) for k, v in
                            (outcome.final_memory or {}).items()})
    try:
        canh = pipeline._dung_scene3d(spec, contract) or {}
        ra["scene3d_objects"] = len(canh.get("objects", []))
        ra["scene3d_ok"] = bool(outcome.servable and canh.get("objects"))
        ra["scene3d"] = canh
    except Exception as e:                                        # noqa: BLE001
        ra["scene3d_ok"] = False
        ra["scene3d_loi"] = f"{type(e).__name__}: {str(e)[:200]}"
    ra["giay"] = round(time.time() - t0, 1)
    return ra


MOI_TRUONG: dict[str, Any] = {}


async def main_async(args) -> int:
    global MOI_TRUONG
    from acceptance_integrity import moi_truong_hien_tai
    from app.ai import gemini as G

    if os.environ.get("ALLOW_LIVE_AI") != "1":
        print("ALLOW_LIVE_AI != 1 — từ chối tiêu quota."); return 2
    api_key = os.environ.get("GEMINI_API_KEY")
    print(f"GEMINI_API_KEY: {'PRESENT' if api_key else 'ABSENT'}")
    if not api_key:
        return 2

    MOI_TRUONG = moi_truong_hien_tai()
    ns = NganSach()
    goc_call = G.call_gemini

    async def dem(*a, **kw):
        from app.ai.telemetry import current_stage
        try:
            st = current_stage()
        except Exception:                                         # noqa: BLE001
            st = "?"
        ns.ghi(str(st))
        return await goc_call(*a, **kw)

    ca_chay = [c for c in CORPUS
               if not args.ca or c["case_id"] in args.ca.split(",")]
    run_id = datetime.now(timezone.utc).strftime("dev-v1-%Y%m%dT%H%M%SZ")
    corpus_public = [{k: v for k, v in c.items()
                      if k in ("case_id", "family", "feature", "problem_text")}
                     for c in CORPUS]
    expected = [{k: v for k, v in c.items()
                 if k in ("case_id", "expected_obligations",
                          "expected_operator_class", "expected_result_type",
                          "exact_expected_results", "expected_boundary")}
                for c in CORPUS]
    manifest = {
        "run_id": run_id,
        "measurement_class": "DEVELOPMENT_DIAGNOSTIC",
        "held_out_claim": False,
        "candidate_hash": "d105f83e5f7de0cc",
        "corpus_hash": _bam(corpus_public),
        "expected_results_hash": _bam(expected),
        "measurement_policy_hash": _bam(json.loads(
            (RA / "measurement_policy.json").read_text(encoding="utf-8"))),
        "runner_hash": _bam(Path(__file__).read_text(encoding="utf-8")),
        "gold_hash": _bam((BACKEND / "scripts" /
                           "gold_section_discoverability.py").read_text(
                              encoding="utf-8")),
        "model_provider": "google-generativelanguage-v1beta",
        "model_name": G.MODEL,
        "model_version_or_snapshot": "",     # ALIAS TRÔI — khai đúng như thế
        "temperature_analyze": 0.1,
        "temperature_synthesis": 0.1,
        "top_p": None, "max_output_tokens": None,
        "repair_limit": 3,
        "transport_max_attempts": G.MAX_ATTEMPTS,
        "logical_budget": MAX_LOGICAL, "physical_budget": MAX_PHYSICAL,
        "moi_truong": MOI_TRUONG,
        "cases": [c["case_id"] for c in ca_chay],
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    RA.mkdir(parents=True, exist_ok=True)
    (RA / f"manifest_{run_id}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MANIFEST ghi trước lượt gọi đầu tiên → manifest_{run_id}.json")
    print(f"  corpus={manifest['corpus_hash'][:16]}… "
          f"expected={manifest['expected_results_hash'][:16]}…")
    print(f"  model={manifest['model_name']} temp=0.1 repair_limit=3 "
          f"budget={MAX_LOGICAL}/{MAX_PHYSICAL}\n")

    # ⚠️ Vá ở CẢ HAI chỗ. `pipeline` làm `from app.ai.gemini import call_gemini`,
    # tức nó giữ một tham chiếu ĐÃ BIND lúc import — vá mình `gemini.call_gemini`
    # thì bộ đếm nằm ngoài đường chạy thật và luôn báo 0. Đúng hình dạng lỗi mà
    # cả loạt wave vừa rồi đuổi theo, lần này ở trong chính bộ đo.
    from app.ai import pipeline as _pl

    G.call_gemini = dem                       # type: ignore[assignment]
    _pl.call_gemini = dem                     # type: ignore[assignment]
    try:
        kq = []
        for c in ca_chay:
            print(f"── {c['case_id']} ({c['family']}) …", flush=True)
            try:
                r = await chay_mot(c, api_key, ns)
            except Exception as e:                                # noqa: BLE001
                r = {"case_id": c["case_id"], "loi_runner":
                     f"{type(e).__name__}: {str(e)[:300]}"}
            r["cham"] = cham(c, r)
            kq.append(r)
            cc = r["cham"]
            print(f"   op={cc.get('SELECTED_OPERATOR')} "
                  f"circle3={cc.get('RESULT_TYPE_IS_CIRCLE3')} "
                  f"khai={cc.get('CURVED_SOLID_DECLARATION')} "
                  f"stage={r.get('stage')} servable={r.get('servable')} "
                  f"repair={cc.get('REPAIR_COUNT')} "
                  f"exact={cc.get('EXACT_ANSWER_MATCH')} "
                  f"owner={cc.get('FAILURE_OWNER')}")
    finally:
        G.call_gemini = goc_call              # type: ignore[assignment]
        _pl.call_gemini = goc_call            # type: ignore[assignment]

    from app.ai.telemetry import total_tokens, usage_report
    try:
        tk = {"theo_stage": usage_report(), "tong": total_tokens()}
    except Exception:                                             # noqa: BLE001
        tk = {}
    # ⚠️ LƯỢT LOGIC ĐỌC TỪ TELEMETRY SẢN PHẨM, không từ bộ đếm của runner.
    #
    # Bản đầu suy `1 + repair_count`, mà `repair_count` đếm sự kiện
    # `semantic_program_attempt` — sự kiện ấy chỉ phát khi một lượt HỎNG. Lượt
    # cuối thành công không phát gì, nên mọi ca đậu bị đếm thiếu một lượt.
    # Một bộ đếm ngân sách đếm thiếu là bộ đếm không bảo vệ gì; `telemetry.calls`
    # là thẩm quyền vì nó đếm ở chỗ token thật sự được ghi.
    ns.logical_telemetry = sum(v.get("calls", 0)
                               for v in (tk.get("theo_stage") or {}).values())
    out = {"manifest": {**manifest,
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                        "logical_calls_used_telemetry": ns.logical_telemetry,
                        "logical_calls_used_runner_counter": ns.logical,
                        "physical_attempts_used": ns.physical,
                        "physical_by_stage": ns.theo_stage},
           "tokens": tk, "ket_qua": kq}
    (RA / f"probe_{run_id}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nLOGICAL={ns.logical}/{MAX_LOGICAL} "
          f"PHYSICAL={ns.physical}/{MAX_PHYSICAL}")
    print(f"→ {RA / f'probe_{run_id}.json'}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ca", default=None, help="tập con id, phẩy ngăn")
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass
    return asyncio.run(main_async(p.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
