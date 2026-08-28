# -*- coding: utf-8 -*-
"""MỘT lệnh cho cả tuyến dữ liệu Phase 7B. **0 API call.**

    python scripts/run_phase7b_data_pipeline.py <gói>.txt          # soi
    python scripts/run_phase7b_data_pipeline.py <gói>.txt --ghi    # ghi thật

Chạy: `validate gói → ingest → capability → oracle → pool → trùng id →
coverage → ngưỡng ≥40 → readiness`, rồi báo đang ở mốc M mấy.

─── VÌ SAO KHÔNG VIẾT LẠI SÁU CHẶNG ───────────────────────────────────────

Sáu chặng giữa đã có ở `run_m1_pipeline`, đã có test, và đã chạy thật. Script
này **gọi lại** chúng chứ không chép: hai bản sao của cùng một dây chuyền là
hai bản sẽ trôi khỏi nhau, và cái trôi ở đây là *tập đo được niêm phong theo
luật nào*. Phần riêng của nó là hai đầu — **soi gói** ở trước (gói phát dư
nên khối trống là bình thường, `ingest` thì từ chối cả lô khi thấy chỗ trống)
và **ngưỡng + mốc M** ở sau.

─── NGUYÊN TỬ, KHÔNG PARTIAL ──────────────────────────────────────────────

Giao thức hiện tại **đòi nguyên tử**: một lỗi ⇒ không ghi bài nào. Cố ý, và
không nới: pool ghi một nửa thì lần chạy sau thấy một pool lai giữa hai lượt
chép, và `pool_hash` trong con dấu không còn nói được nó niêm phong cái gì.
Đổi lại, gói **soi được giữa chừng** miễn phí bao nhiêu lần cũng được —
`validate_human_copy_packet.py` chính là chỗ để lặp.
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

#: Mốc của `HOLDOUT_EXPANSION_PLAN §5` — báo đang ở đâu thay vì chỉ báo số.
#: `(accepted tối thiểu, số ô tối thiểu, tên)`; xét từ dưới lên.
MOC = ((40, 20, "M4 — đủ điều kiện rút, chạy được `--chi-kiem-pool`"),
       (0, 14, "M3 — 14 ô tầng A đã có bài, phần khó xong"),
       (3, 0, "M2 — một ô đầy, ma trận đổi màu"),
       (1, 0, "M1 — cả dây chạy thật lần đầu"),
       (0, 0, "M0 — chưa có bài nào"))


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        ten, Path(__file__).resolve().parent / f"{ten}.py")
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[ten] = m
    spec.loader.exec_module(m)
    return m


def moc_hien_tai(nhan: int, so_o: int) -> str:
    for n, o, ten in MOC:
        if nhan >= n and so_o >= o:
            return ten
    return MOC[-1][2]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("goi", help="Gói chép tay do NGƯỜI điền")
    p.add_argument("--ghi", action="store_true",
                   help="Ghi thật. Không có cờ này thì chỉ soi.")
    a = p.parse_args()

    SH = _nap("seal_geometry_holdout")
    IN = _nap("ingest_holdout_batch")
    VL = _nap("validate_human_copy_packet")
    M1 = _nap("run_m1_pipeline")
    MT = _nap("holdout_coverage_matrix")

    goc = Path(a.goi)
    print(f"═══ TUYẾN DỮ LIỆU PHASE 7B · {'GHI' if a.ghi else 'SOI'} ═══\n")

    # ── [0] soi gói: bỏ khối chưa điền, giữ phần đã điền ─────────────────
    print("[0] soi gói chép tay")
    r = VL.soi(goc.read_text(encoding="utf-8"), SH, IN)
    print(f"    {r['tong_khoi']} khối · {len(r['bai'])} đã điền · "
          f"{r['bo_trong']} còn trống")
    if r["loi"] or r["trung"]:
        for d in (r["loi"] + [f"trùng case_id: {x}" for x in r["trung"]])[:8]:
            print("    ·", d)
        # FAILED_CASE nêu đích danh bài hỏng: với 47 khối, "có lỗi ở đâu đó"
        # là câu không dùng được.
        ca = sorted({d.split(":")[0].strip() for d in r["loi"]
                     if d.split(":")[0].strip().startswith("hp_")}
                    | set(r["trung"]))
        print(f"\nFAILED_CASE:  {', '.join(ca) if ca else '(không rõ bài — lỗi ở mức gói)'}")
        print("FAILED_STAGE: validate_packet")
        print(f"REASON:       {len(r['loi'])} lỗi · {len(r['trung'])} trùng id")
        print("FIX_REQUIRED: Sửa DỮ LIỆU trong gói. KHÔNG sửa validator.")
        return 2
    for x in r["canh"][:10]:
        print("    ⚠️ ", x)
    if not r["bai"]:
        print("\nFAILED_STAGE: validate_packet")
        print("REASON:       chưa khối nào được điền")
        print("FIX_REQUIRED: Gõ ít nhất một đề vào gói rồi chạy lại.")
        return 2

    # ── [1–6] mượn nguyên dây chuyền đã có ───────────────────────────────
    # Ghi phần ĐÃ ĐIỀN ra file tạm cạnh gói: `run_m1_pipeline` nhận đường dẫn,
    # và phần đã điền mới là thứ nạp được (gói gốc còn khối trống).
    da_dien, _ = VL.go_khoi_trong(goc.read_text(encoding="utf-8"))
    tam = goc.with_suffix(".dadien.txt")
    tam.write_text(da_dien, encoding="utf-8")
    print(f"\n    (phần đã điền → {tam.name})\n")
    try:
        ma = M1.main.__wrapped__ if hasattr(M1.main, "__wrapped__") else M1.main
        sys.argv = ["run_m1_pipeline", str(tam)] + (["--ghi"] if a.ghi else [])
        rc = ma()
    finally:
        tam.unlink(missing_ok=True)
    if rc != 0:
        return rc

    # ── [7] ngưỡng + mốc ─────────────────────────────────────────────────
    cases = json.loads(POOL.read_text(encoding="utf-8"))["cases"]
    if not a.ghi:
        # Chế độ soi: pool trên đĩa CHƯA có bài mới, nên đọc thẳng nó thì
        # ngưỡng báo 0 ngay sau khi chặng coverage vừa báo 2 — hai con số
        # cùng màn hình cãi nhau. Cộng thêm phần *sẽ* ghi để soi đúng thứ
        # `--ghi` sắp làm.
        them, _ = IN.loc_trung([IN.thanh_case(b, r["nguoi"], SH)
                                for b in r["bai"]], cases)
        cases = cases + them
    theo_o, chua_du = SH.kiem_du_dieu_kien_rut(cases)
    nhan = sum(len(v) for v in theo_o.values())
    so_o = len([o for o in SH.BANG_O if theo_o.get(o)])
    print(f"\n[7/7] ngưỡng rút")
    for d in chua_du:
        print("      ·", d)
    if a.ghi:
        (GEO / "holdout" / "COVERAGE_MATRIX.md").write_text(
            MT._md(MT.ma_tran(cases)), encoding="utf-8")

    print(f"\n═══ {nhan}/{SH.TONG_TOI_THIEU} bài · {so_o}/{len(SH.BANG_O)} ô "
          f"· {moc_hien_tai(nhan, so_o)} ═══")
    if chua_du:
        print("Chưa rút được. Điền thêm khối trong gói rồi chạy lại.")
        return 1
    print("Đủ điều kiện rút. Bước sau: scaffold expectation → freeze check →")
    print("commit cuối → rebuild runtime → runtime_doctor → SEED CỦA GVHD → seal.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
