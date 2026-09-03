# -*- coding: utf-8 -*-
"""PROBE ECGÔNÔMI CONG — LƯỢT V2, đi qua tầng toàn vẹn. **TIÊU QUOTA THẬT.**

    cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 \\
        .venv/Scripts/python.exe scripts/run_curved_ergonomics_v2.py \\
        --out-dir ../docs/evaluation/geometry/curved-ergonomics-v2

    `CURVED_ERGONOMICS_PROBE_V2`, 2026-09-04.

⚠️ **DỮ LIỆU PHÁT TRIỂN.** Không dùng để bật năng lực sản phẩm, không phải
nghiệm thu. V3 **không** chạy ở đây và pool V3 giữ nguyên niêm phong.

─── KHÁC GÌ `run_curved_acceptance.py` ────────────────────────────────────

Runner cũ **không** bị viết lại (bằng chứng lịch sử giữ nguyên), nhưng nó mang
đúng hai lỗi mà `ACCEPTANCE_RUNNER_INTEGRITY` vừa dựng cổng để chặn:

    kết quả đọc từ `envelope["scene3d"]`   → phán quyết dựng trên tầng VẼ
    phân loại lỗi bằng khớp chuỗi tiếng Việt → đổi một chữ là đổi con số

Lượt này đi qua `acceptance_integrity` + `acceptance_verdict`, nên:

  · manifest ghi TRƯỚC lượt gọi đầu tiên, môi trường kiểm TRƯỚC MỖI lượt gọi;
  · artifact ghi nguyên khối, từ chối đè, thư mục mới hoàn toàn;
  · kết quả trích từ `outcome.final_memory`;
  · phân loại từ `stage_reached` + `error_code`;
  · repair-eligible đọc từ luật sản phẩm, không phải luật của runner;
  · token dẫn từ một thẩm quyền chuẩn hoá, thiếu ≠ 0;
  · tóm tắt dẫn từ artifact trên đĩa rồi TỰ KIỂM lại.

─── BỘ CA ─────────────────────────────────────────────────────────────────

Bốn ca phát triển, **định nghĩa lấy thẳng từ `run_curved_acceptance.CA`** chứ
không chép lại: chép là mở đường cho một chữ khác nhau, và khi ấy hai lượt
không so được nữa. `CA_HASH` phải khớp bản §18 (`8c6a184f…`) mới cho chạy.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND))
sys.path.insert(0, str(_BACKEND / "scripts"))

from acceptance_integrity import (  # noqa: E402
    ARTIFACT_SCHEMA_VERSION,
    IntegrityError,
    chuan_hoa_telemetry,
    ghi_artifact,
    kiem_bat_bien_token,
    kiem_bo_ca,
    kiem_moi_truong,
    mo_run,
    moi_truong_hien_tai,
    tom_tat_tu_artifact,
    tu_kiem_tom_tat,
)
from acceptance_verdict import (  # noqa: E402
    cham_ca_am,
    co_giai_doan,
    phan_loai,
    sua_duoc,
    trich_ket_qua,
)
from curved_ergonomics_metrics import do_hinh_dang, gop_hinh_dang  # noqa: E402

#: Bộ ca §18 — băm phải khớp, nếu không thì hai lượt không so được.
CA_HASH_MONG = "8c6a184f1c17596464be410ab60a238206f3b2c929e7316b757d2305683145ba"
PROBE_SUBSET = ("ball_2", "cylinder_2", "ball_1", "circumsphere")


def _nap_env() -> str:
    """Đọc `GEMINI_API_KEY` từ `backend/.env` vào môi trường — KHÔNG in ra."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    f = _BACKEND / ".env"
    if f.exists():
        for dong in f.read_text(encoding="utf-8").splitlines():
            dong = dong.strip()
            if dong.startswith("GEMINI_API_KEY=") and "=" in dong:
                key = dong.split("=", 1)[1].strip().strip('"').strip("'")
                os.environ["GEMINI_API_KEY"] = key
                break
    return key


def _tien_dieu_kien(ca4: list[dict], ca_hash: str) -> dict[str, Any]:
    """Mọi thứ phải xác nhận được bằng MÁY trước lượt gọi đầu tiên."""
    from app.ai import gemini

    if ca_hash != CA_HASH_MONG:
        raise IntegrityError(
            f"BỘ CA ĐÃ ĐỔI khỏi bản §18.\n  nay  {ca_hash}\n  §18  "
            f"{CA_HASH_MONG}\nHai lượt không so được nữa.")
    thieu = [i for i in PROBE_SUBSET if i not in {c["id"] for c in ca4}]
    if thieu:
        raise IntegrityError(f"thiếu ca: {thieu}")

    mt = moi_truong_hien_tai()
    # Prompt phải là bản TRÊN ĐĨA. Tiến trình này vừa khởi động nên
    # `gemini._skill_cache` rỗng — điều kiện mạnh hơn restart backend.
    from acceptance_integrity import _git, phan_loai_dirty

    da_nap = list(getattr(gemini, "_skill_cache", {}))
    skill = gemini.load_skill("geometry_program_generator")
    dirty = phan_loai_dirty()
    print(f"HEAD                 {_git('rev-parse', '--short', 'HEAD')}")
    print(f"cây làm việc         "
          f"{'SẠCH' if dirty['sach'] else 'bẩn: ' + str(dirty['duong_ban'])}")
    print(f"CACHE_VERSION        {mt['cache_version']}")
    print(f"STABLE_CAPABILITY    {mt['stable_capability_hash'][:16]}…")
    print(f"SEMANTIC_ENV         {mt['semantic_environment_hash'][:16]}…")
    for k, v in mt["components"].items():
        print(f"  {k:<18} {v[:16]}…")
    print(f"CASE_SET_HASH        {ca_hash[:16]}…  (khớp §18)")
    print(f"skill đã nạp trước   {da_nap or '(rỗng — tiến trình mới)'}")
    print(f"geometry_program_generator  {len(skill.encode('utf-8'))} byte")
    return mt


async def _analyze(c: dict, key: str):
    from app.ai import pipeline
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC

    return await pipeline.stage_semantic_analyze(
        c["de"], key, domain=DOMAIN_HINH_HOC)


async def _synth(c: dict, key: str, contract):
    from app.ai import pipeline
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC

    return await pipeline.stage_semantic_program(
        c["de"], {}, key, contract, domain=DOMAIN_HINH_HOC)


def _contract_json(contract) -> dict:
    return {
        "problem_text": contract.problem_text,
        "input_facts": [f.model_dump(mode="json") for f in contract.input_facts],
        "obligations": [o.model_dump(mode="json") for o in contract.obligations],
    }


def _phan_quyet(c: dict, contract, spec, loi_synth: str | None) -> dict:
    """Chạy route THẬT rồi phán quyết bằng `acceptance_verdict`."""
    from app.simulation.semantic_program.route import verify_and_compile

    schema_ok = spec is not None
    outcome = verify_and_compile(contract, spec) if schema_ok else None
    la_am = c["loai"] == "am"
    bien = cham_ca_am(c, outcome, schema_ok=schema_ok) if la_am else None
    lop = phan_loai(outcome, schema_ok=schema_ok, la_ca_am=la_am,
                    boundary_ok=(bien or {}).get("target_boundary_demonstrated"))
    ok_sua, ly_do = sua_duoc(outcome, schema_ok=schema_ok,
                             error_code=None if schema_ok else "schema")
    ra = {
        "id": c["id"], "loai": c["loai"], "de": c["de"],
        "mong": sorted(c["mong"]),
        "chuong_trinh": spec.model_dump(mode="json") if schema_ok else None,
        "loi_schema": None if schema_ok else loi_synth,
        "giai_doan": co_giai_doan(outcome, schema_ok=schema_ok),
        "ket_qua": (trich_ket_qua(outcome) if outcome else
                    {"nguon": "outcome.final_memory", "dai_luong": {}}),
        "error_code": getattr(outcome, "error_code", None),
        "failure_category": getattr(outcome, "failure_category", None),
        "stage_reached": getattr(outcome, "stage_reached", None),
        "details": list(getattr(outcome, "details", None) or []),
        "reason": getattr(outcome, "reason", None),
        "weak_kinds": list(getattr(outcome, "weak_kinds", None) or []),
        "phan_lop": lop,
        "repair_eligible": ok_sua, "repair_reason": ly_do,
        "hinh_dang": do_hinh_dang(spec.model_dump(mode="json")
                                  if schema_ok else None),
    }
    if bien:
        ra.update(bien)
    # §"PRODUCT SUCCESS" — sáu cờ, không rút thành một.
    g = ra["giai_doan"]
    ra["product_success"] = bool(
        g["static_valid"] and g["grounding_pass"] and g["coverage_pass"]
        and g["runtime_executable"] and g["postconditions_pass"] and g["servable"])
    # Đáp số đúng nhưng KHÔNG phục vụ được ⇒ **không** phải thành công sản phẩm.
    ra["dap_so_khop"] = (set(ra["mong"]) <= set(ra["ket_qua"]["dai_luong"].values())
                         if ra["mong"] else None)
    return ra


def _gop_raw(*bao_cao: dict) -> dict:
    gop: dict[str, dict[str, int]] = {}
    for b in bao_cao:
        for stage, so in (b or {}).items():
            d = gop.setdefault(stage, {})
            for k, v in so.items():
                d[k] = d.get(k, 0) + v
    return gop


async def main_async(a) -> int:
    from app.ai import gemini, telemetry
    import run_curved_acceptance as RCA

    key = _nap_env()
    if os.environ.get("ALLOW_LIVE_AI") != "1" or not key:
        print("DỪNG: cần ALLOW_LIVE_AI=1 và GEMINI_API_KEY", file=sys.stderr)
        return 2

    ca4 = [c for c in RCA.CA if c["id"] in PROBE_SUBSET]
    ca4.sort(key=lambda c: PROBE_SUBSET.index(c["id"]))
    mt = _tien_dieu_kien(ca4, RCA.CA_HASH)

    out = Path(a.out_dir)
    mf = mo_run(
        out, run_id=out.name,
        muc_dich="CURVED_ERGONOMICS_PROBE_V2 — DỮ LIỆU PHÁT TRIỂN, không "
                 "nghiệm thu, không bật năng lực sản phẩm",
        runner=str(Path(__file__).resolve()), ca=ca4,
        model={"provider": "gemini", "skill": "geometry_program_generator",
               "one_shot_attempts": 1, "repair_attempts": "mặc định sản phẩm"},
        chinh_sach_sua="acceptance_verdict.sua_duoc — đọc luật sản phẩm",
        ngan_sach_goi=a.budget)
    ghi_artifact(out / "case_set.json", {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "case_set_hash_full": RCA.CA_HASH, "probe_subset": list(PROBE_SUBSET),
        "ca": ca4_json(ca4)})
    print(f"\nrun_id {mf.run_id} · manifest đã ghi TRƯỚC lượt gọi đầu tiên\n")

    gemini.set_budget(gemini.ApiBudget(max_logical_calls=a.budget))
    ket: dict[str, dict] = {}
    tel: dict[str, dict] = {}
    dung_som = None

    # ══ PASS A — MỘT lượt tổng hợp, KHÔNG sửa ═════════════════════════════
    import app.ai.pipeline as PL

    goc_tran = PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS = 1
    try:
        for i, c in enumerate(ca4, 1):
            kiem_bo_ca(mf.seal, ca4)
            kiem_moi_truong(mt, nhan=f"pass A · {c['id']}")
            telemetry.reset_usage()
            print(f"[A {i}/{len(ca4)}] {c['id']}", flush=True)
            try:
                contract, err = await _analyze(c, key)
                if contract is None:
                    raise IntegrityError(f"analyze hỏng: {err}")
                ghi_artifact(out / "cases" / c["id"] / "analyze.json", {
                    "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
                    "id": c["id"], "de": c["de"],
                    "request_contract": _contract_json(contract)})
                spec, serr = await _synth(c, key, contract)
            except gemini.BudgetExceeded as e:
                dung_som = f"BUDGET_EXHAUSTED (pass A): {e}"
                print(dung_som)
                break
            r = _phan_quyet(c, contract, spec, serr)
            r["request_contract"] = _contract_json(contract)
            tel[c["id"]] = telemetry.usage_report()
            ghi_artifact(out / "cases" / c["id"] / "synthesis-one-shot.json", {
                "artifact_schema_version": ARTIFACT_SCHEMA_VERSION, **r,
                "telemetry": chuan_hoa_telemetry(tel[c["id"]])})
            ket[c["id"]] = r
            print(f"      {r['phan_lop']} · servable={r['giai_doan']['servable']}")
            if r["phan_lop"].startswith("SYSTEM_"):
                dung_som = (f"SYSTEM_FAILURE bất ngờ ở '{c['id']}' "
                            f"({r['error_code']}) — DỪNG theo luật, KHÔNG sửa "
                            f"mã rồi chạy tiếp cùng run_id")
                print(dung_som)
                break
    finally:
        PL.MAX_SEMANTIC_PROGRAM_ATTEMPTS = goc_tran

    pass_a = {i: dict(r) for i, r in ket.items()}

    # ══ PASS B — CHỈ luật sản phẩm ════════════════════════════════════════
    can_sua = [i for i, r in ket.items()
               if r["repair_eligible"] and not r["product_success"]]
    print(f"\nREPAIR_ELIGIBLE {len(can_sua)} — {can_sua or '(không)'}")
    if dung_som:
        print("bỏ qua pass B vì đã dừng sớm")
        can_sua = []
    for i, cid in enumerate(can_sua, 1):
        c = next(x for x in ca4 if x["id"] == cid)
        kiem_moi_truong(mt, nhan=f"pass B · {cid}")
        telemetry.reset_usage()
        print(f"[B {i}/{len(can_sua)}] {cid}", flush=True)
        try:
            from app.simulation.semantic_program.request_contract import (
                RequestContract,
            )

            contract = RequestContract.model_validate(ket[cid]["request_contract"])
            spec, serr = await _synth(c, key, contract)
        except gemini.BudgetExceeded as e:
            dung_som = f"BUDGET_EXHAUSTED (pass B): {e}"
            print(dung_som)
            telemetry.reset_usage()
            break
        r = _phan_quyet(c, contract, spec, serr)
        r["request_contract"] = ket[cid]["request_contract"]
        tel_b = telemetry.usage_report()
        ghi_artifact(out / "cases" / cid / "repair-01.json", {
            "artifact_schema_version": ARTIFACT_SCHEMA_VERSION, **r,
            "telemetry": chuan_hoa_telemetry(tel_b)})
        tel[cid] = _gop_raw(tel[cid], tel_b)
        ket[cid] = r
        print(f"      {r['phan_lop']} · servable={r['giai_doan']['servable']}")
    gemini.set_budget(None)

    # ══ FINAL + TÓM TẮT ══════════════════════════════════════════════════
    for cid, r in ket.items():
        chuan = chuan_hoa_telemetry(tel[cid])
        sp = chuan["theo_stage"].get("semantic_program", {}).get("calls", 0)
        goi = {
            "analyze": chuan["theo_stage"].get("semantic_analyze", {}).get("calls", 0),
            # Pass A luôn đúng MỘT lượt tổng hợp (trần hạ xuống 1). Phần dôi ra
            # của `semantic_program` là lượt SỬA — đếm từ bản ghi, không suy.
            "synthesis": min(1, sp) if cid in can_sua else sp,
            "repair": max(0, sp - 1) if cid in can_sua else 0,
        }
        ghi_artifact(out / "cases" / cid / "final.json", {
            "artifact_schema_version": ARTIFACT_SCHEMA_VERSION, **r,
            "pass_a_phan_lop": pass_a[cid]["phan_lop"],
            "pass_a_hinh_dang": pass_a[cid]["hinh_dang"],
            "pass_a_product_success": pass_a[cid]["product_success"],
            "goi_provider": goi, "telemetry": chuan,
            "token_bat_bien_loi": kiem_bat_bien_token(chuan)})

    # §22 — `summary.json` là bản DẪN THUẦN, không thêm một trường nào; nếu
    # thêm thì `tu_kiem_tom_tat` (tính lại từ đĩa) sẽ lệch ở đúng những trường
    # ấy và cổng tự kiểm mất tác dụng. Số riêng của probe đi file khác, và cũng
    # DẪN TỪ ĐĨA chứ không lấy từ bộ nhớ.
    ghi_artifact(out / "summary.json", tom_tat_tu_artifact(out))
    tt = tu_kiem_tom_tat(out)                   # §23
    ec = _ergonomics_tu_dia(out, dung_som=dung_som, tong_ca=len(ca4))
    ghi_artifact(out / "ergonomics.json", ec)

    print("\n── TÓM TẮT (dẫn từ artifact, đã tự kiểm) ──")
    for k in ("SYSTEM_FAILURES", "APPLICATION_LLM_CALLS"):
        print(f"  {k:<28} {tt[k]}")
    for k in ("DEVELOPMENT_CASES_TOTAL", "ONE_SHOT_PRODUCT_SUCCESS",
              "FINAL_PRODUCT_SUCCESS", "FINAL_EXECUTABLE",
              "CURVED_GEOMETRY_LAUNDERING"):
        print(f"  {k:<28} {ec[k]}")
    print(f"  tokens                       {tt['tokens']}")
    print(f"  goi_theo_loai                {tt['goi_theo_loai']}")
    print(f"  ONE_SHOT                     {ec['ONE_SHOT_PHAN_LOP']}")
    print(f"  FINAL                        {ec['FINAL_PHAN_LOP']}")
    print(f"  hình dạng one-shot           "
          f"{ {k: v for k, v in ec['hinh_dang_one_shot'].items() if not k.startswith('_')} }")
    print(f"  TELEMETRY_MISSING            {tt['TELEMETRY_MISSING'] or '(không)'}")
    if dung_som:
        print(f"\n  ⚠️ DỪNG SỚM: {dung_som}")
    return 0


def _ergonomics_tu_dia(out: Path, *, dung_som: str | None,
                       tong_ca: int) -> dict[str, Any]:
    """Số riêng của probe — cũng DẪN TỪ ĐĨA, không lấy từ bộ nhớ (§22).

    Đọc `final.json` của từng ca; mỗi file đã chở CẢ hình dạng one-shot
    (`pass_a_hinh_dang`) lẫn hình dạng cuối, nên bảng trước→sau dựng lại được
    từ artifact mà không cần tiến trình sinh ra nó.
    """
    from acceptance_integrity import doc_artifact

    mf = doc_artifact(out / "manifest.json")
    ca = {}
    for i in mf["seal"]["ids"]:
        f = out / "cases" / i / "final.json"
        if f.exists():
            ca[i] = doc_artifact(f)

    return {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "run_id": mf["run_id"], "dung_som": dung_som,
        "DEVELOPMENT_CASES_TOTAL": tong_ca,
        "CASES_WITH_ARTIFACT": len(ca),
        "ONE_SHOT_PHAN_LOP": {i: r["pass_a_phan_lop"] for i, r in sorted(ca.items())},
        "FINAL_PHAN_LOP": {i: r["phan_lop"] for i, r in sorted(ca.items())},
        "ONE_SHOT_PRODUCT_SUCCESS": sum(
            1 for r in ca.values() if r.get("pass_a_product_success")),
        "FINAL_PRODUCT_SUCCESS": sum(
            1 for r in ca.values() if r.get("product_success")),
        "FINAL_EXECUTABLE": sum(
            1 for r in ca.values() if r["giai_doan"]["runtime_executable"]),
        "hinh_dang_one_shot": gop_hinh_dang(
            {i: r["pass_a_hinh_dang"] for i, r in ca.items()}),
        "hinh_dang_final": gop_hinh_dang(
            {i: r["hinh_dang"] for i, r in ca.items()}),
        "hinh_dang_theo_ca_one_shot": {
            i: r["pass_a_hinh_dang"] for i, r in sorted(ca.items())},
        # R0 còn giữ không: có điểm toạ độ không nguồn nào lọt tới mức PHỤC VỤ
        # được không. Phải bằng 0.
        "CURVED_GEOMETRY_LAUNDERING": sum(
            r["hinh_dang"]["INVENTED_HELPER_POINT"] for r in ca.values()
            if r["giai_doan"]["servable"]),
        "REPAIR_ELIGIBLE": sorted(i for i, r in ca.items()
                                  if r.get("repair_eligible")),
        "REPAIR_REASONS": {i: r.get("repair_reason") for i, r in sorted(ca.items())},
    }


def ca4_json(ca4: list[dict]) -> list[dict]:
    return [{k: (sorted(v) if isinstance(v, set) else v) for k, v in c.items()}
            for c in ca4]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--budget", type=int, default=24,
                   help="trần lượt gọi LOGIC (mặc định 24)")
    return asyncio.run(main_async(p.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
