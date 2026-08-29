# -*- coding: utf-8 -*-
"""TẬP XÁC NHẬN POSTFIX — 6 ca reserve × k=2. **TIÊU QUOTA THẬT.**

    ALLOW_LIVE_AI=1 python scripts/run_postfix_confirmation.py

⚠️ **KHÔNG phải Phase 7B chính thức.** Lượt chính thức đã xong, gắn với băm
hệ `7ab25683…`, và `BASELINE_LOCK` giữ nó bất biến. Đây là lượt xác nhận
riêng trên hệ V2, và mọi báo cáo phải gọi đúng tên ấy.

─── SÁU CA NÀY LÀ AI ─────────────────────────────────────────────────────

Reserve của pool Phase 7B: `accepted` nhưng con dấu không rút. Ba điều kiện
đã kiểm bằng máy lúc đóng băng — chưa từng gửi tới hệ được đo · chưa từng
làm ca hồi quy DEV · commit của `pool.json` là **tổ tiên** của commit sửa.
Điều kiện ba là thứ không mua lại được: chúng được soạn khi chưa ai biết hệ
V2 sẽ hỏng ở đâu.

Tập đã đóng băng TRƯỚC lượt gọi model đầu tiên của V2
(`selection_hash 0b55e0f9…`), và bộ chạy **kiểm lại băm ấy** trước khi chạy.

─── BẪY ĐÃ VẤP NĂM LẦN, BỊT SẴN ──────────────────────────────────────────

Hợp đồng gọi vật bằng tên của ĐỀ (`B'D'`); chương trình gọi bằng tên của nó
(`B_prime_D_prime`). Lưới hoà giải `khop_ky_hieu` đã phải vá lần lượt ở C₁a,
C₁b, C₂, `learner_surface`, rồi ở bộ chấm DEV — mỗi lần vì một cổng mới đọc
`final_memory` **thô**.

`_snapshot_co_bi_danh` áp bí danh MỘT LẦN cho mọi tên mà hợp đồng nhắc tới,
trước khi giao cho bộ chấm. Không có nó, lượt xác nhận sẽ báo mô hình sai ở
đúng chỗ mô hình đúng — đã xảy ra ở MINI, và ở đó nó suýt thành cáo buộc
*"hệ nhận một diễn giải sai"*.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
GEO = ROOT / "docs" / "evaluation" / "geometry"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

SEL = GEO / "postfix-confirmation" / "CONFIRMATION_SELECTION.json"
RA = GEO / "postfix-confirmation"
#: Trần: 6 ca × 2 lượt × (6 logic, 8 HTTP) + đệm.
TRAN_LOGIC, TRAN_HTTP = 78, 104


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        ten, BACKEND / "scripts" / f"{ten}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[ten] = m
    spec.loader.exec_module(m)
    return m


M = _nap("measure_geometry_stability")
DEV = _nap("run_geometry_dev_evaluation")

_CASE: dict[str, dict] = {}


def _snapshot_co_bi_danh(fm: dict, hd) -> dict:
    """Thêm bí danh theo tên HỢP ĐỒNG. Không ghi đè tên chương trình."""
    from app.simulation.semantic_program.domain_profile import khop_ky_hieu
    snap = dict(fm)
    for ob in (hd.obligations if hd else []):
        ten = [ob.container, ob.witness] + [
            v for v in (ob.params or {}).values() if isinstance(v, str)]
        for t in ten:
            if t and t not in snap:
                if (thay := khop_ky_hieu(t, set(snap))) is not None:
                    snap[t] = snap[thay]
    return snap


def cham_oracle(case_id: str, fm: dict, hd=None):
    """Ba trạng thái. `UNGRADED` là **không chấm được**, không phải sai."""
    c = _CASE[case_id]
    if not c.get("oracle_result"):
        return None, "ô tầng B — chấm bằng từ chối trung thực, không bằng oracle"
    r = DEV.cham_oracle(c, hd, _snapshot_co_bi_danh(fm, hd))
    v = r["verdict"]
    return ({"PASS": True, "FAIL": False}.get(v),
            f"{v}: {r.get('ly_do') or r.get('lech')}")


async def _chay(cases: list[dict], k: int, key: str) -> list[dict]:
    ket, tl, th = [], 0, 0
    for i, c in enumerate(cases, 1):
        for lan in range(1, k + 1):
            f = RA / f"{c['case_id']}-lan{lan}.json"
            if f.exists():
                ket.append(json.loads(f.read_text(encoding="utf-8"))["ban_ghi"])
                continue
            if tl + 6 > TRAN_LOGIC or th + 8 > TRAN_HTTP:
                print(f"⛔ CHẠM TRẦN: {tl}/{TRAN_LOGIC} logic · {th}/{TRAN_HTTP} HTTP")
                return ket
            bai = {"id": c["case_id"], "de": c["problem_text"],
                   "oracle": c["case_id"]}
            r = await M.mot_luot(bai, lan, key)
            ket.append(r)
            tl += r.get("logical_calls") or 0
            th += r.get("http_requests") or 0
            print(f"{'✅' if r['servable'] else '❌'} [{i}/{len(cases)}] "
                  f"{c['case_id']:<14} {c['slot']} {lan}/{k} · "
                  f"{r['do_tre_giay']:>5}s · {str(r['stage_reached']):<18} "
                  f"oracle={r['oracle_dat']} kiểm={r['verification_match']} "
                  f"dựng={r['construction_match']} · {tl}/{TRAN_LOGIC} logic",
                  flush=True)
    return ket


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tien-kiem", action="store_true", help="0 API call.")
    a = p.parse_args()

    sel = json.loads(SEL.read_text(encoding="utf-8"))
    lai = hashlib.sha256(json.dumps(
        {k: sel[k] for k in ("case_ids", "luat_chon", "k")},
        ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    if lai != sel["selection_hash"]:
        print(f"⛔ selection_hash LỆCH: {lai[:16]}… ≠ {sel['selection_hash'][:16]}…")
        print("   Tập đã bị đổi sau khi đóng băng — đó là thứ file kia bảo vệ.")
        return 2

    pool = json.loads((GEO / "holdout" / "pool.json").read_text(encoding="utf-8"))
    theo = {c["case_id"]: c for c in pool["cases"]}
    cases = [theo[i] for i in sel["case_ids"]]
    _CASE.update({c["case_id"]: c for c in cases})
    dau = set(json.loads((GEO / "holdout" / "HOLDOUT_SEAL.json")
                         .read_text(encoding="utf-8"))["case_ids"])
    if giao := {c["case_id"] for c in cases} & dau:
        print(f"⛔ dùng lại ca CHÍNH THỨC: {sorted(giao)}")
        return 2

    print(f"TẬP XÁC NHẬN POSTFIX · {len(cases)} ca × k={sel['k']} "
          f"· hash {sel['selection_hash'][:16]}…")
    print("⚠️ KHÔNG phải Phase 7B chính thức — lượt riêng trên hệ V2.\n")
    for c in cases:
        print(f"  {c['case_id']:<14} {c['slot']} | {c['problem_text'][:66]}")
    if a.tien_kiem:
        return 0

    if os.environ.get("ALLOW_LIVE_AI") != "1":
        print(f"\nThiếu ALLOW_LIVE_AI=1 — {len(cases)}×{sel['k']} lượt tiêu quota.")
        return 2
    try:
        from dotenv import load_dotenv
        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("Thiếu GEMINI_API_KEY.")
        return 2

    M.RA, M.RUN_ID = RA, "postfix-confirmation-v2"
    M.TRAN_LOGIC, M.TRAN_HTTP = 6, 8
    M.cham_oracle = cham_oracle
    M.BAI = [{"id": c["case_id"], "de": c["problem_text"],
              "oracle": c["case_id"]} for c in cases]
    # Kỳ vọng đã ĐÓNG BĂNG trong con dấu — cùng file mà lượt chính thức dùng.
    M.TAP_KY_VONG = "holdout"
    M._KY_VONG_CACHE.clear()

    from app.runtime_identity import runtime_identity
    from app.ai import gemini
    r = runtime_identity()
    print(f"\nsha={r['git_sha'][:12]} cache={r['cache_version']} "
          f"model={gemini.MODEL}\n")

    mf = RA / "RUN_MANIFEST.json"
    if not mf.exists():
        mf.write_text(json.dumps({
            "khai": "Lượt XÁC NHẬN POSTFIX trên hệ V2. KHÔNG phải Phase 7B.",
            "selection_hash": sel["selection_hash"], "k": sel["k"],
            "case_ids": sel["case_ids"],
            "runtime": {"git_sha": r["git_sha"],
                        "cache_version": r["cache_version"],
                        "model": gemini.MODEL},
            "bat_dau": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ket = asyncio.run(_chay(cases, sel["k"], key))
    print(f"\n── XONG · {len(ket)}/{len(cases) * sel['k']} lượt ──")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
