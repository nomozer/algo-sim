# -*- coding: utf-8 -*-
"""Chạy TRỌN chuỗi holdout bằng MỘT lệnh. **0 API call.**

    python scripts/run_m1_pipeline.py <lô>.txt          # soi cả chuỗi, không ghi
    python scripts/run_m1_pipeline.py <lô>.txt --ghi    # ghi thật

    ingest ──▶ pool ──▶ scaffold expectation ──▶ freeze check ──▶ coverage ──▶ readiness

─── VÌ SAO GỘP, VÀ VÌ SAO KHÔNG GỘP THÊM ─────────────────────────────────

Năm lệnh rời có một chỗ hỏng người dùng không thấy: chạy `ingest --ghi` rồi
**quên** chạy `scaffold`, hoặc chạy `coverage` mà quên `freeze_expectation_check`
— pool đổi mà báo cáo thì không, và lần sau đọc báo cáo là đọc một trạng thái
đã chết. Gộp lại thì chuỗi hoặc **chạy hết**, hoặc **dừng ở chặng đầu tiên
hỏng** và nói rõ chặng nào.

**KHÔNG gộp `seal` vào đây, có chủ đích.** `seal` tiêu seed của GVHD và chỉ
chạy được một lần; để nó trong một lệnh chạy-hàng-ngày là mời một cú `--ghi`
lỡ tay tiêu mất con dấu. `seal` giữ nguyên lệnh riêng.

─── DỪNG Ở ĐÂU THÌ NÓI CHẶNG ĐÓ ──────────────────────────────────────────

Mỗi chặng in `[n/6] tên chặng` rồi kết quả. Hỏng thì in `FAILED_STAGE`,
`REASON`, `FIX_REQUIRED` — ba dòng, đúng khuôn mà giao thức đòi, để không phải
đọc ngược log tìm xem nó chết ở đâu.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
GEO = GOC / "docs" / "evaluation" / "geometry"
POOL = GEO / "holdout" / "pool.json"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        f"_m1_{ten}", Path(__file__).resolve().parent / f"{ten}.py")
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _dung(chang: str, ly_do: str, sua: str) -> int:
    print(f"\nFAILED_STAGE: {chang}")
    print(f"REASON:       {ly_do}")
    print(f"FIX_REQUIRED: {sua}")
    return 2


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("file_lo", help="File lô đề do NGƯỜI chép")
    p.add_argument("--ghi", action="store_true",
                   help="Ghi thật. Không có cờ này thì chỉ soi.")
    a = p.parse_args()

    SH = _nap("seal_geometry_holdout")
    IN = _nap("ingest_holdout_batch")
    GE = _nap("geometry_expectations")
    SC = _nap("scaffold_expectation")
    FEC = _nap("freeze_expectation_check")
    MT = _nap("holdout_coverage_matrix")
    RP = _nap("report_holdout_readiness")

    che = "GHI" if a.ghi else "SOI (không ghi gì)"
    print(f"═══ CHUỖI HOLDOUT · chế độ {che} ═══\n")

    # ── [1/6] ingest ─────────────────────────────────────────────────────
    print("[1/6] ingest — đọc lô, kiểm nguồn + ranh giới + oracle")
    van_ban = Path(a.file_lo).read_text(encoding="utf-8")
    nguoi, bai, loi = IN.phan_tich(van_ban, SH)
    if loi:
        for d in loi[:8]:
            print("      ·", d)
        return _dung("ingest/parse", f"{len(loi)} lỗi trong file lô",
                     "Sửa DỮ LIỆU trong file lô. KHÔNG sửa validator.")
    cases = [IN.thanh_case(b, nguoi, SH) for b in bai]
    rg = [d for c in cases for d in SH.check_capability_boundary(c)]
    if rg:
        for d in rg[:8]:
            print("      ·", d)
        return _dung("capability_boundary", f"{len(rg)} bài ngoài ranh giới",
                     "Bỏ bài ấy khỏi lô và chọn bài khác. Xem CAPABILITY_BOUNDARY.")
    kp = SH.kiem_pool(cases)
    if kp:
        for d in kp[:8]:
            print("      ·", d)
        return _dung("kiem_pool", f"{len(kp)} lỗi xuất xứ/oracle",
                     "Sửa dữ liệu lô: nguồn · người chép · đơn vị đáp án.")
    print(f"      ✅ {len(cases)} bài qua cả ba cổng · người chép: {nguoi}")

    # ── [2/6] ghi pool ───────────────────────────────────────────────────
    print("[2/6] pool")
    d = json.loads(POOL.read_text(encoding="utf-8"))
    them, va = IN.loc_trung(cases, d["cases"])
    if va:
        for x in va:
            print("      ·", x)
        return _dung("pool/trung_id", f"{len(va)} bài trùng case_id",
                     "Trùng id là MẤT BÀI im lặng. Đổi thứ tự khối trong gói, "
                     "hoặc gỡ bài đã có khỏi pool trước.")
    if a.ghi:
        d["cases"] += them
        # Nhãn dựng LẠI TỪ `cases`, mượn đúng hàm của `ingest_holdout_batch`.
        #
        # File này có bộ ghi pool RIÊNG, song song với `ingest.main()`. Đó là
        # lý do nhãn `__trang_thai__` trôi: sửa một bộ ghi thì bộ kia vẫn
        # nối `cases` rồi ghi đè, và sau lượt nạp 41 bài nhãn vẫn đọc
        # *"0 accepted · 0/20 ô"* — khai THIẾU sẵn sàng, tức mời người sau đi
        # thu thập thêm rồi nạp trùng.
        d["__trang_thai__"] = IN._nhan_trang_thai(d["cases"])
        POOL.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        print(f"      ✅ ghi {len(them)} bài · nhãn: {d['__trang_thai__']}")
    else:
        d["cases"] = d["cases"] + them
        print(f"      (soi) sẽ ghi {len(them)} bài")
    nhan = [c for c in d["cases"] if c.get("status", "accepted") == "accepted"]
    print(f"      accepted = {len(nhan)}")

    # ── [3/6] khung kỳ vọng ──────────────────────────────────────────────
    print("[3/6] scaffold expectation")
    if SC.RA.exists():
        print(f"      (đã có {SC.RA.name} — không ghi đè)")
    else:
        khung = SC.dung_khung(d["cases"], SH)
        can = len(GE._tim_cho_trong(khung))
        if a.ghi:
            SC.RA.parent.mkdir(parents=True, exist_ok=True)
            SC.RA.write_text(json.dumps(khung, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
            print(f"      ✅ dựng khung {len(khung['cases'])} bài · "
                  f"{can} chỗ CẦN NGƯỜI ĐIỀN")
        else:
            print(f"      (soi) khung {len(khung['cases'])} bài · {can} chỗ cần người")

    # ── [4/6] freeze expectation check ───────────────────────────────────
    print("[4/6] freeze expectation check")
    if not FEC.KY_VONG.exists():
        print("      ⏸  chưa có expectations/holdout.json — bỏ qua, ĐÚNG quy trình")
    else:
        try:
            kv = GE.nap("holdout")
        except (ValueError, FileNotFoundError) as e:
            print("      ·", str(e)[:150])
            return _dung("freeze_expectation", "kỳ vọng chưa nạp được",
                         "Điền mọi chỗ <…> trong expectations/holdout.json.")
        # Chế độ SOI đối chiếu kỳ vọng với pool **ĐANG NẰM TRÊN ĐĨA**, không
        # với pool giả định sau khi nạp lô.
        #
        # Bài của lô soi chưa có kỳ vọng — đó là bình thường, vì kỳ vọng chỉ
        # được soạn SAU khi bài vào pool. Đối chiếu chúng ở đây thì mọi lượt
        # soi trên một pool đã đầy đều đỏ, và thông điệp *"sửa
        # expectations/holdout.json cho khớp pool"* bảo người ta soạn kỳ vọng
        # cho bài chưa quyết định nhận — đúng thứ tự ngược.
        fl = FEC.kiem(kv, d["cases"] if a.ghi else
                      json.loads(POOL.read_text(encoding="utf-8"))["cases"],
                      SH, GE)
        if fl:
            for x in fl[:8]:
                print("      ·", x)
            return _dung("freeze_expectation", f"{len(fl)} lệch giữa kỳ vọng và pool",
                         "Sửa expectations/holdout.json cho khớp pool.")
        print(f"      ✅ khớp pool · expectation_hash = {FEC.bam_ky_vong()[:24]}…")

    # ── [5/6] coverage ───────────────────────────────────────────────────
    print("[5/6] coverage")
    m = MT.ma_tran(d["cases"])
    co_bai = [o for o in m["bang_o"] if m["theo_o"].get(o)]
    print(f"      {m['so_bai']} bài · phủ {20 - len(m['o_trong'])}/20 ô"
          + (f" · có bài: {' '.join(co_bai)}" if co_bai else ""))
    if a.ghi:
        (GEO / "holdout" / "COVERAGE_MATRIX.md").write_text(
            MT._md(m), encoding="utf-8")
        print("      ✅ ghi COVERAGE_MATRIX.md")

    # ── [6/6] readiness ──────────────────────────────────────────────────
    print("[6/6] readiness report")
    if a.ghi:
        rd = RP.thu_thap()
        RP.RA.write_text(RP._md(rd), encoding="utf-8")
        b = RP.blockers(rd)
        print(f"      ✅ ghi · READY_FOR_PHASE7B = {'YES' if not b else 'NO'}"
              f" · còn {len(b)} blocker")
    else:
        print("      (soi)")

    print(f"\n═══ CHUỖI XONG · accepted = {len(nhan)}/40 ═══")
    if not a.ghi:
        print("Thêm `--ghi` để ghi thật.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
