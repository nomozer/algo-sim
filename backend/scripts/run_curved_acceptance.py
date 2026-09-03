# -*- coding: utf-8 -*-
"""PHÉP ĐO NĂNG LỰC CONG — 9 ca, MỚI, không phải chạy lại benchmark lịch sử.

    cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 \\
        .venv/Scripts/python.exe scripts/run_curved_acceptance.py --out-dir <thư mục>

⚠️ **TIÊU QUOTA THẬT.** Xem `docs/PHASE_3_CURVED_PRODUCT_INTEGRATION.md`.

─── CHÍNH SÁCH TIẾT KIỆM, VÀ VÌ SAO NÓ TÁCH LÀM HAI CHẶNG ─────────────────

**8A — MỘT lượt tổng hợp mỗi ca, KHÔNG sửa.** Hạ `MAX_SEMANTIC_PROGRAM_ATTEMPTS`
xuống `1`; đó là **hằng số của sản phẩm**, không phải một runner riêng — mọi
cổng, mọi phán quyết, mọi thông điệp giữ nguyên. Kết quả one-shot được ghi
**TRƯỚC** khi có bất kỳ lượt sửa nào, nên con số one-shot không bao giờ bị một
lượt sửa về sau làm đẹp lên.

**8B — chỉ sửa những ca mà ĐƯỜNG SẢN PHẨM thật sự gửi lỗi ngược.** Đọc thẳng
`pipeline._sinh_chuong_trinh`: chỉ ba lớp lỗi đi vào `_prompt_sua` —

    schema (`validate_semantic_program`) · ir_static (`kiem_tinh`) ·
    grounding (khi mã lỗi KHÔNG thuộc `KHONG_DUOC_SUA`)

Lỗi **runtime** (interpreter, `GeometryError`) xảy ra ở `verify_and_compile`,
**ngoài** vòng sửa, nên nó KHÔNG repair-eligible. Cho một ca runtime đi sửa là
dựng một hành vi mà sản phẩm không có — và con số thu được sẽ nói về runner chứ
không nói về hệ.

─── ĐIỀU RUNNER NÀY TỰ CẤM ────────────────────────────────────────────────

Không k=3/k=5. Không đổi prompt giữa các ca. Không chạy lại ca đã ĐẠT. Không
sửa mã nguồn khi phép đo đang chạy — gặp lỗi nền THẬT thì **DỪNG** và báo, vì
vá giữa chừng làm mọi con số phía trước nói về một hệ khác con số phía sau.

Artifact **từ chối ghi đè** thư mục đã có, cùng lệ mọi bộ đo hình học.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))


# ══ BỘ CA CỐ ĐỊNH — khoá bằng băm, không sửa giữa chừng ══════════════════
#
# Đề viết MỚI, không lấy từ ví dụ trong prompt và không lấy từ tập DEV/holdout.
# `mong` là đáp số tính TAY; runner so chuỗi hiển thị của đại lượng.
CA: list[dict[str, Any]] = [
    {
        "id": "ball_1", "hinh": "ball", "loai": "duong",
        "de": "Cho mặt cầu (S) có tâm I và đi qua điểm A, biết IA = 6. "
              "Tính bán kính và thể tích khối cầu (S).",
        "mong": {"6", "288π"},
    },
    {
        "id": "ball_2", "hinh": "ball", "loai": "duong",
        "de": "Cho mặt cầu tâm O bán kính bằng 13. Một mặt phẳng (P) cách tâm "
              "O một khoảng bằng 5 và cắt mặt cầu theo một đường tròn (C). "
              "Tính bán kính của (C) và diện tích hình tròn (C).",
        "mong": {"12", "144π"},
    },
    {
        "id": "cylinder_1", "hinh": "cylinder", "loai": "duong",
        "de": "Một hình trụ có hai đáy tâm O và O′ với OO′ = 7, bán kính đáy "
              "bằng 4. Tính thể tích khối trụ và diện tích xung quanh của "
              "hình trụ.",
        "mong": {"112π", "56π"},
    },
    {
        "id": "cylinder_2", "hinh": "cylinder", "loai": "duong",
        "de": "Cho hình trụ có hai đáy tâm O và O′, bán kính đáy bằng 5 và "
              "chiều cao OO′ = 8. Mặt phẳng vuông góc với trục tại trung điểm "
              "của OO′ cắt hình trụ theo đường tròn (C). Tính bán kính của (C).",
        "mong": {"5"},
    },
    {
        "id": "cone_1", "hinh": "cone", "loai": "duong",
        "de": "Cho hình nón đỉnh S, tâm đáy O, chiều cao SO = 8 và bán kính "
              "đáy bằng 6. Tính độ dài đường sinh, thể tích khối nón và diện "
              "tích xung quanh của hình nón.",
        "mong": {"10", "96π", "60π"},
    },
    {
        "id": "cone_2", "hinh": "cone", "loai": "duong",
        "de": "Cho hình nón đỉnh S, tâm đáy O, chiều cao bằng 9 và bán kính "
              "đáy bằng 4. Một mặt phẳng đi qua trục của hình nón cắt hình nón "
              "theo một tam giác cân. Tính diện tích tam giác đó.",
        "mong": {"36"},
    },
    {
        # LỚP `gm_10`, viết mới. Tâm PHẢI được DỰNG, không được khai toạ độ.
        "id": "circumsphere", "hinh": "ball", "loai": "duong",
        "de": "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc và "
              "OA = OB = OC = 2. Tính bán kính mặt cầu ngoại tiếp tứ diện OABC.",
        "mong": {"√3"},
    },
    {
        "id": "refuse_oblique", "hinh": "cylinder", "loai": "am",
        "de": "Cho hình trụ có bán kính đáy bằng 3 và chiều cao bằng 10. Một "
              "mặt phẳng cắt hình trụ theo một đường elip (mặt phẳng này không "
              "vuông góc với trục và không chứa trục). Hãy dựng elip đó và "
              "tính diện tích hình elip.",
        "mong": set(),
    },
    {
        "id": "refuse_line_curved", "hinh": "ball", "loai": "am",
        "de": "Cho mặt cầu tâm I bán kính bằng 5 và một đường thẳng d cắt mặt "
              "cầu tại hai điểm P và Q. Hãy dựng hai giao điểm P, Q của d với "
              "mặt cầu rồi tính độ dài đoạn PQ.",
        "mong": set(),
    },
]

#: Băm bộ ca — vào artifact. Đổi một chữ trong đề ⇒ băm đổi ⇒ không so được
#: với lượt trước, và đó là điều ĐÚNG.
CA_HASH = hashlib.sha256(
    json.dumps([{k: (sorted(v) if isinstance(v, set) else v)
                 for k, v in c.items()} for c in CA],
               ensure_ascii=False, sort_keys=True).encode()
).hexdigest()

#: Ba lớp lỗi mà `pipeline._sinh_chuong_trinh` THẬT SỰ gửi ngược cho mô hình.
#: Đọc từ mã, không đoán. Runtime KHÔNG có trong này.
LOP_SUA_DUOC = ("schema", "ir_static", "grounding")


def _moi_truong() -> dict[str, Any]:
    from app.main import CACHE_VERSION
    from app.runtime_identity import (
        semantic_environment_fingerprint,
        semantic_environment_hash,
        stable_capability_hash,
    )

    return {
        "cache_version": CACHE_VERSION,
        "semantic_environment_hash": semantic_environment_hash(),
        "stable_capability_hash": stable_capability_hash(),
        "components": semantic_environment_fingerprint(),
        "case_set_hash": CA_HASH,
    }


def _phan_lop_loi(err: str | None) -> str:
    """Lỗi one-shot thuộc lớp nào — quyết định ca có repair-eligible không."""
    if not err:
        return "khong"
    h = err
    if "validation error" in h and "SemanticProgramSpec" in h:
        return "schema"
    if "không thực thi được" in h:
        return "ir_static"
    if "xuất xứ dữ liệu chưa đủ" in h:
        return "grounding"
    # Mã trong `KHONG_DUOC_SUA` — cố ý KHÔNG sửa.
    if "[" in h and "]" in h:
        return "grounding_khong_sua"
    return "khac"


async def _chay_mot(c: dict, api_key: str) -> dict[str, Any]:
    """Một ca đi ĐÚNG đường sản phẩm: analyze → tổng hợp → verify_and_compile."""
    from app.ai import pipeline
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
    from app.simulation.semantic_program.route import verify_and_compile

    ra: dict[str, Any] = {
        "id": c["id"], "hinh": c["hinh"], "loai": c["loai"], "de": c["de"],
        "contract_ok": False, "schema_ok": False, "executable": False,
        "dai_luong": [], "mong": sorted(c["mong"]), "dap_so_khop": None,
        "tu_choi": None, "loi": None, "lop_loi": "khong",
        "chuong_trinh": None, "dung_phep_cong": [],
    }
    contract, err = await pipeline.stage_semantic_analyze(
        c["de"], api_key, domain=DOMAIN_HINH_HOC)
    if contract is None:
        ra.update(loi=err, lop_loi="analyze")
        return ra
    ra["contract_ok"] = True

    spec, serr = await pipeline.stage_semantic_program(
        c["de"], {}, api_key, contract, domain=DOMAIN_HINH_HOC)
    if spec is None:
        ra.update(loi=serr, lop_loi=_phan_lop_loi(serr))
        return ra
    ra["schema_ok"] = True
    ra["chuong_trinh"] = spec.model_dump(mode="json")
    ra["dung_phep_cong"] = sorted({
        st.get("curved_kind") for st in ra["chuong_trinh"].get("statements", [])
        if st.get("kind") == "construct_curved_solid"} - {None})

    outcome = verify_and_compile(contract, spec)
    ra["executable"] = bool(outcome.executable)
    if not outcome.executable:
        ra.update(loi=getattr(outcome, "reason", None) or "không thực thi được",
                  lop_loi="runtime")
        return ra
    env = getattr(outcome, "envelope", None) or {}
    canh = (env.get("scene3d") or {}).get("objects") or []
    ra["dai_luong"] = [o.get("value") for o in canh
                       if o.get("type") == "quantity"]
    if c["mong"]:
        ra["dap_so_khop"] = c["mong"] <= set(ra["dai_luong"])
    return ra


def _cham_am(r: dict) -> tuple[bool, str]:
    """Ca ÂM đạt khi hệ TỪ CHỐI, không phải khi nó dựng gần đúng.

    Ba đường từ chối đều hợp lệ: mô hình tự nói không diễn đạt được (không sinh
    chương trình), cổng tĩnh/xuất xứ chặn, hoặc runtime từ chối bằng mã cong.
    Đường KHÔNG hợp lệ: một envelope chạy được kèm đáp số — nghĩa là hệ đã dựng
    một thứ nó không biểu diễn nổi.
    """
    if not r["executable"]:
        return True, f"từ chối ở lớp '{r['lop_loi']}'"
    if r["dai_luong"]:
        return False, f"DỰNG GẦN ĐÚNG — trả đại lượng {r['dai_luong']}"
    return False, "envelope chạy được cho một đề ngoài bao đóng"


async def main_async(args) -> int:
    from app.ai import gemini, telemetry

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if os.environ.get("ALLOW_LIVE_AI") != "1" or not api_key:
        print("DỪNG: cần ALLOW_LIVE_AI=1 và GEMINI_API_KEY", file=sys.stderr)
        return 2
    out = Path(args.out_dir)
    if out.exists() and any(out.iterdir()):
        print(f"DỪNG: {out} đã có nội dung — bộ đo KHÔNG ghi đè lượt cũ",
              file=sys.stderr)
        return 2

    mt = _moi_truong()
    print(f"MÔI TRƯỜNG  cache {mt['cache_version']} · "
          f"env {mt['semantic_environment_hash'][:16]}… · "
          f"capability {mt['stable_capability_hash'][:16]}…")
    print(f"BỘ CA       {len(CA)} ca · băm {CA_HASH[:16]}…\n")

    from app.ai import pipeline

    telemetry.reset_usage()
    # Trần cứng: 9 ca × 2 lượt (analyze + tổng hợp) = 18, cộng biên cho 8B.
    gemini.set_budget(gemini.ApiBudget(max_api_calls=40, max_logical_calls=32))

    # ══ 8A — MỘT lượt, KHÔNG sửa ════════════════════════════════════════
    goc_tran = pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS = 1
    mot_luot: list[dict] = []
    dung_som = None
    try:
        for i, c in enumerate(CA, 1):
            print(f"[8A {i}/{len(CA)}] {c['id']}", flush=True)
            mot_luot.append(await _chay_mot(c, api_key))
    except gemini.BudgetExceeded as e:
        dung_som = f"BUDGET_EXHAUSTED: {e}"
        print(dung_som)
    finally:
        pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS = goc_tran

    token_8a = telemetry.usage_report()
    # GHI NGAY, trước mọi lượt sửa. Con số one-shot không được phép đẹp lên.
    out.mkdir(parents=True, exist_ok=True)
    (out / "stage_8a_one_shot.json").write_text(json.dumps(
        {"moi_truong": mt, "dung_som": dung_som, "token": token_8a,
         "ca": mot_luot}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n→ {out / 'stage_8a_one_shot.json'} (ghi TRƯỚC mọi lượt sửa)\n")

    # ══ 8B — chỉ sửa ca mà ĐƯỜNG SẢN PHẨM gửi lỗi ngược ═════════════════
    can_sua = [r for r in mot_luot
               if not r["executable"] and r["lop_loi"] in LOP_SUA_DUOC
               and r["loai"] == "duong"]
    print(f"REPAIR_ELIGIBLE_FAILURES {len(can_sua)}"
          + (f" — {[r['id'] for r in can_sua]}" if can_sua else ""))
    sua: list[dict] = []
    if can_sua and not args.chi_8a:
        for i, r in enumerate(can_sua, 1):
            c = next(x for x in CA if x["id"] == r["id"])
            print(f"[8B {i}/{len(can_sua)}] {c['id']}", flush=True)
            try:
                sua.append(await _chay_mot(c, api_key))
            except gemini.BudgetExceeded as e:
                dung_som = f"BUDGET_EXHAUSTED (8B): {e}"
                print(dung_som)
                break
    gemini.set_budget(None)

    cuoi = {r["id"]: r for r in mot_luot}
    for r in sua:
        cuoi[r["id"]] = r

    def _dat(r: dict) -> bool:
        if r["loai"] == "am":
            return _cham_am(r)[0]
        return bool(r["executable"]) and r["dap_so_khop"] is True

    tk = telemetry.usage_report()
    tong_in = sum(v.get("input", 0) for v in tk.values())
    tong_out = sum(v.get("output", 0) for v in tk.values())
    dung_ok = [r for r in cuoi.values() if _dat(r) and r["loai"] == "duong"]
    bao = {
        "moi_truong": mt,
        "MODEL_CASES_TOTAL": len(CA),
        "ONE_SHOT_CORRECT": sum(1 for r in mot_luot if _dat(r)),
        "ONE_SHOT_EXECUTABLE_IR": sum(1 for r in mot_luot if r["executable"]),
        "ONE_SHOT_HONEST_REFUSALS": sum(
            1 for r in mot_luot if r["loai"] == "am" and _cham_am(r)[0]),
        "REPAIR_ELIGIBLE_FAILURES": len(can_sua),
        "REPAIR_CALLS": len(sua),
        "FINAL_CORRECT_AFTER_REPAIR": sum(1 for r in cuoi.values() if _dat(r)),
        "TOTAL_INPUT_TOKENS": tong_in,
        "TOTAL_OUTPUT_TOKENS": tong_out,
        "TOTAL_TOKENS": telemetry.total_tokens(),
        "TOKENS_PER_CORRECT_EXECUTABLE_IR": (
            round(telemetry.total_tokens() / len(dung_ok)) if dung_ok else None),
        "theo_hinh": {
            h: {
                "duong_dat": sum(1 for r in cuoi.values()
                                 if r["hinh"] == h and r["loai"] == "duong"
                                 and _dat(r)),
                "duong_tong": sum(1 for r in CA
                                  if r["hinh"] == h and r["loai"] == "duong"),
            } for h in ("ball", "cylinder", "cone")
        },
        "am": {r["id"]: _cham_am(r)[1] for r in cuoi.values()
               if r["loai"] == "am"},
        "dung_som": dung_som,
        "token_theo_stage": tk,
    }
    (out / "curved_acceptance.json").write_text(json.dumps(
        {"tom_tat": bao, "one_shot": mot_luot, "sau_sua": sua,
         "cuoi": list(cuoi.values())}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    print("\n── KẾT QUẢ ──")
    for k in ("MODEL_CASES_TOTAL", "ONE_SHOT_CORRECT", "ONE_SHOT_EXECUTABLE_IR",
              "ONE_SHOT_HONEST_REFUSALS", "REPAIR_ELIGIBLE_FAILURES",
              "REPAIR_CALLS", "FINAL_CORRECT_AFTER_REPAIR",
              "TOTAL_INPUT_TOKENS", "TOTAL_OUTPUT_TOKENS", "TOTAL_TOKENS",
              "TOKENS_PER_CORRECT_EXECUTABLE_IR"):
        print(f"  {k:34} {bao[k]}")
    for h, v in bao["theo_hinh"].items():
        print(f"  {h:34} {v['duong_dat']}/{v['duong_tong']}")
    for i, m in bao["am"].items():
        print(f"  {i:34} {m}")
    print(f"\n→ {out / 'curved_acceptance.json'}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--chi-8a", action="store_true",
                   help="chỉ chạy one-shot, không sửa")
    return asyncio.run(main_async(p.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
