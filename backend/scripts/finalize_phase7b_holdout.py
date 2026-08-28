# -*- coding: utf-8 -*-
"""MỘT lệnh chạy sau khi người chép xong gói. **0 API call.**

    python scripts/finalize_phase7b_holdout.py <gói>.txt          # soi
    python scripts/finalize_phase7b_holdout.py <gói>.txt --ghi    # ghi thật

─── VÌ SAO CÓ FILE NÀY KHI ĐÃ CÓ `run_phase7b_data_pipeline` ──────────────

Nó **không** thêm chặng nào. Nó gọi lại đúng dây chuyền ấy rồi trả lời **một
câu mà dây chuyền kia không trả lời**: *sau khi nạp, còn thiếu bao nhiêu bài
và vì sao bài nào bị loại*.

Khác biệt ấy quan trọng vì một con số đã sai một lần: **42 ứng viên KHÔNG phải
42 `accepted`**. Ứng viên chỉ thành `accepted` sau khi qua `capability` +
`oracle` + `kiem_pool`. Báo cáo ở đây tách bạch **CANDIDATES / ACCEPTED /
REJECTED** và **không bao giờ** in một con số gộp.

⚠️ Khối RESERVE để trống **không phải ứng viên**. Chúng là sức chứa, dùng khi
có ứng viên bị loại. Đếm chúng vào pool là tự khai đủ.
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
POOL = GOC / "docs" / "evaluation" / "geometry" / "holdout" / "pool.json"


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        ten, Path(__file__).resolve().parent / f"{ten}.py")
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[ten] = m
    spec.loader.exec_module(m)
    return m


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("goi", help="Gói chép tay ĐÃ ĐIỀN")
    p.add_argument("--ghi", action="store_true", help="Ghi thật vào pool")
    a = p.parse_args()

    SH = _nap("seal_geometry_holdout")
    IN = _nap("ingest_holdout_batch")
    VL = _nap("validate_human_copy_packet")
    DP = _nap("run_phase7b_data_pipeline")

    goc = Path(a.goi)
    r = VL.soi(goc.read_text(encoding="utf-8"), SH, IN)
    n_ung_vien = len(r["bai"]) + len(r["can_chep"])

    print("═" * 66)
    print(f"CANDIDATES_INPUT : {len(r['bai'])} đã chép / {n_ung_vien} ứng viên")
    print(f"RESERVE_BLOCKS   : {r['reserve']}  (sức chứa, KHÔNG phải ứng viên)")
    if r["can_chep"]:
        print(f"⚠️  CHƯA CHÉP XONG — còn {len(r['can_chep'])} ứng viên. "
              "Chạy `validate_human_copy_packet.py` để xem còn ô nào.")
    print("═" * 66 + "\n")

    # ── Dây chuyền: mượn nguyên, không chép lại nghiệp vụ ────────────────
    sys.argv = ["run_phase7b_data_pipeline", str(goc)] + (
        ["--ghi"] if a.ghi else [])
    rc = DP.main()
    # `rc == 1` nghĩa là *chưa đủ ngưỡng* — đó CHÍNH LÀ lúc cần báo cáo
    # nhận/loại nhất, nên không thoát. Chỉ `rc == 2` (hỏng dữ liệu, đã in
    # `FAILED_CASE`/`FAILED_STAGE`) mới dừng.
    if rc >= 2:
        return rc

    # ── Báo cáo NHẬN / LOẠI — phần riêng của lệnh này ────────────────────
    cases = json.loads(POOL.read_text(encoding="utf-8"))["cases"]
    if not a.ghi:
        them, _ = IN.loc_trung(
            [IN.thanh_case(b, r["nguoi"], SH) for b in r["bai"]], cases)
        cases = cases + them

    nhan = [c for c in cases if SH.duoc_rut(c)]
    loai = [c for c in cases if not SH.duoc_rut(c)]
    theo_o = collections.Counter(c["slot"] for c in nhan)
    trong = [o for o in SH.BANG_O if not theo_o.get(o)]

    print("\n" + "═" * 66)
    print(f"CANDIDATES : {len(cases)}")
    print(f"ACCEPTED   : {len(nhan)}")
    print(f"REJECTED   : {len(loai)}")
    if loai:
        print("\nREJECTION_BY_REASON:")
        for ly, k in collections.Counter(
                (c.get("status") or "?") for c in loai).most_common():
            print(f"   {ly:<34} {k}")
        for c in loai[:10]:
            print(f"     · {c['case_id']:<18} {(c.get('reason') or '')[:60]}")

    print(f"\nCOVERAGE   : {len(SH.BANG_O) - len(trong)}/{len(SH.BANG_O)}")
    if trong:
        print(f"EMPTY_SLOTS: {' '.join(trong)}")
        # BA loại ô trống, và gộp chúng là giấu mất loại nguy hiểm nhất:
        #   · A12 — chưa từng có nguồn, đã biết trước;
        #   · chưa chép — người chép còn đang làm, KHÔNG phải lỗi;
        #   · DATA_GAP MỚI — đã chép nhưng nạp vào mất sạch. Chỉ loại này
        #     mới là dấu hiệu có gì vừa hỏng.
        chua_chep = set(r["can_chep"])
        da_chep_o = {b["o"] for b in r["bai"]}
        if "A12" in trong:
            print("             · A12 → BLOCKED_BY_A12 (đã biết trước, không "
                  "phải lỗi nạp — chờ quyết định GVHD)")
        if cho := sorted(o for o in trong if o != "A12" and o in chua_chep):
            print(f"             · chưa chép: {' '.join(cho)} — bình thường, "
                  "không phải lỗi")
        if gap := sorted(o for o in trong
                         if o != "A12" and o not in chua_chep
                         and o in da_chep_o):
            print(f"             · ⚠️ DATA_GAP MỚI: {' '.join(gap)} — đã chép "
                  "nhưng mất sạch sau khi nạp. Xem lý do loại ở trên.")

    du = len(nhan) >= SH.TONG_TOI_THIEU
    print(f"\nPOOL_THRESHOLD: {'PASS' if du else 'FAIL'} "
          f"({len(nhan)}/{SH.TONG_TOI_THIEU})")
    if not du:
        thieu = SH.TONG_TOI_THIEU - len(nhan)
        if r["can_chep"]:
            # Đang chép dở: phần lớn chỗ thiếu sẽ tự đầy khi chép nốt. Nói
            # "cần thu thêm N ứng viên" lúc này là báo một việc không có.
            print(f"   Thiếu {thieu} bài, nhưng còn {len(r['can_chep'])} ứng "
                  "viên CHƯA CHÉP — chép nốt rồi chạy lại trước khi kết luận.")
        else:
            print(f"   Thiếu {thieu} bài. Còn {r['reserve']} khối reserve — "
                  f"cần thu thêm {thieu + 1} ứng viên (dư 1 làm đệm).")
    print("═" * 66)
    return 0 if du else 1


if __name__ == "__main__":
    raise SystemExit(main())
