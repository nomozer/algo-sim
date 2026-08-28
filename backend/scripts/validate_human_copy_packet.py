# -*- coding: utf-8 -*-
"""Soi `PHASE7B_HUMAN_COPY_PACKET.txt` — báo còn thiếu gì. **0 API call.**

    python scripts/validate_human_copy_packet.py <gói>.txt

Không ghi gì, không đụng pool. Chạy được **giữa chừng** khi gói mới điền một
phần — đó là mục đích chính: người chép muốn biết mình còn bao nhiêu khối và
đã đủ ngưỡng chưa mà không phải đếm tay.

─── RANH GIỚI: MÁY KIỂM ĐƯỢC GÌ ───────────────────────────────────────────

Kiểm được: chỗ trống · chữ ký · nguồn · slot hợp lệ · trùng id · đúng loại
dòng cho tầng A/B · hình dạng đáp án · **dấu vết ký hiệu bị rơi**.

**KHÔNG** kiểm được, và không giả vờ kiểm: *đề này có đúng nguyên văn nguồn
không*. Chỉ người mở nguồn trả lời được — đó là toàn bộ lý do cổng
`NGƯỜI CHÉP:` tồn tại. Validator xanh **không** có nghĩa đề đúng.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
POOL = GOC / "docs" / "evaluation" / "geometry" / "holdout" / "pool.json"

_KHOI = re.compile(r"^\s*\[([AB]\d{2})\]", re.M)
_NGUON = re.compile(r"^[ \t]*NGUỒN[ \t]*:[ \t]*(.+?)[ \t]*$", re.M)

#: Ký hiệu hình học **phải** xuất hiện ở ô nào — dạng chữ hoặc dạng ký tự.
#: Cảnh báo chứ không loại: đề có thể diễn đạt khác. Nhưng nó bắt đúng cái
#: hỏng đã đo được — trích PDF rơi sạch `⊥` (0 lần trong 217 trang về quan hệ
#: vuông góc) mà văn bản vẫn đọc trôi chảy.
_DAU_HIEU: dict[tuple[str, ...], tuple[str, str]] = {
    ("A03", "A04", "A05"): (r"song song|∥|//", "song song"),
    ("A06", "A07", "A08"): (r"vuông góc|⊥", "vuông góc"),
    ("A09", "A10"): (r"góc", "góc"),
    ("A11", "A12"): (r"khoảng cách|kho[aả]ng c[aá]ch", "khoảng cách"),
    ("A14",): (r"thể tích|the tich", "thể tích"),
}


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        f"_vl_{ten}", Path(__file__).resolve().parent / f"{ten}.py")
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"_vl_{ten}"] = m
    spec.loader.exec_module(m)
    return m


def _con_trong(s: str | None) -> bool:
    return bool(s) and bool(re.search(r"<[^>]*>|\bTODO\b", s))


def go_khoi_trong(van_ban: str) -> tuple[str, int]:
    """Bỏ mọi khối còn nguyên chỗ trống, trả phần ĐÃ ĐIỀN + số khối bỏ.

    Gói phát dư có chủ đích (47 khối cho ngưỡng 40), nên khối chưa điền là
    **trạng thái bình thường giữa chừng**, không phải lỗi. Nhưng `ingest` từ
    chối cả lô khi thấy một chỗ trống — đúng với một lô đã nộp, sai với một
    gói đang điền dở. Nên soi trên phần đã điền, và nói rõ đã bỏ mấy khối.
    """
    vt = [m.start() for m in _KHOI.finditer(van_ban)]
    if not vt:
        return van_ban, 0
    dau, giu, bo = van_ban[:vt[0]], [], 0
    for i, v in enumerate(vt):
        than = van_ban[v:vt[i + 1] if i + 1 < len(vt) else len(van_ban)]
        # Chỉ nhìn ba dòng dữ liệu; dòng `#` là siêu dữ liệu máy tự đặt.
        du_lieu = "\n".join(d for d in than.splitlines()
                            if not d.lstrip().startswith("#"))
        (bo := bo + 1) if _con_trong(du_lieu) else giu.append(than)
    return dau + "".join(giu), bo


def soi(van_ban: str, SH, IN) -> dict:
    da_dien, bo_trong = go_khoi_trong(van_ban)
    tong_khoi = len(_KHOI.findall(van_ban))
    nguoi, bai, loi = IN.phan_tich(da_dien, SH) if _KHOI.search(da_dien) \
        else (None, [], [])

    # Chữ ký kiểm RIÊNG: gói chưa điền khối nào vẫn phải báo thiếu chữ ký,
    # nhưng KHÔNG được báo "không đọc được bài nào" như một lỗi.
    loi = [d for d in loi if "Không đọc được bài nào" not in d]
    m = re.search(r"^\s*NGƯỜI CHÉP\s*:\s*(.+?)\s*$", van_ban, re.M)
    ky = m.group(1).strip() if m else None
    if not ky or _con_trong(ky):
        loi.insert(0, "THIẾU chữ ký `NGƯỜI CHÉP:` — hoặc còn là chỗ trống. "
                      "Một chữ ký `<tên bạn>` không chứng nhận gì cả.")

    canh: list[str] = []
    for b in bai:
        for os_, (mau, ten) in _DAU_HIEU.items():
            if b["o"] in os_ and not re.search(mau, b["de"], re.I):
                canh.append(f"{b['ma']} [{b['o']}]: đề không nhắc *{ten}* — "
                            "ký hiệu rơi lúc chép, hay chép nhầm ô?")
        if "�" in b["de"]:
            canh.append(f"{b['ma']}: có ký tự thay thế `�` — mã hoá hỏng")
        if re.search(r"\S {3,}\S", b["de"]):
            canh.append(f"{b['ma']}: có khoảng trắng dài giữa câu — chỗ ấy "
                        "thường là công thức bị rơi khi dán")
        canh += [f"{b['ma']}: {c}" for c in b["canh_bao"]]

    # Trùng id — với gói 47 khối, một va chạm im lặng là mất bài.
    co_san = json.loads(POOL.read_text(encoding="utf-8"))["cases"] \
        if POOL.exists() else []
    ids = [b["ma"] for b in bai]
    trung = sorted({i for i in ids if ids.count(i) > 1}
                   | ({c["case_id"] for c in co_san} & set(ids)))

    # ── PHÂN LOẠI khối chưa điền: CẦN CHÉP vs RESERVE ────────────────────
    #
    # Khối đã prefill `NGUỒN:` là **ứng viên máy đã tìm và xác minh** — người
    # chép phải gõ đề vào đó. Khối để trống hoàn toàn là **sức chứa dự phòng**,
    # dùng khi có ứng viên bị loại lúc `ingest`.
    #
    # Trước bản này validator gộp cả hai thành một số "còn trống", nên gói 51
    # khối / 42 ứng viên báo *"50 còn trống"* khi mới chép 1 — người chép tưởng
    # còn 50 việc trong khi chỉ còn 41. Đếm sai theo hướng làm nản.
    can_chep: list[str] = []
    reserve = 0
    for i, v in enumerate(vt := [m.start() for m in _KHOI.finditer(van_ban)]):
        than = van_ban[v:vt[i + 1] if i + 1 < len(vt) else len(van_ban)]
        du_lieu = "\n".join(d for d in than.splitlines()
                            if not d.lstrip().startswith("#"))
        if not _con_trong(du_lieu):
            continue                      # đã chép xong
        # BẮT giá trị rồi kiểm, KHÔNG dùng lookahead sau `\s*`: `\s*` quay lui
        # về rỗng rồi lookahead soi nhầm dấu cách, nên `NGUỒN: <…>` (khối
        # reserve) vẫn khớp và 9 khối reserve bị đếm thành việc phải làm.
        g = _NGUON.search(than)
        if g and not _con_trong(g.group(1)):
            can_chep.append(than[1:4])    # có nguồn thật ⇒ còn phải chép
        else:
            reserve += 1

    theo_o: dict[str, int] = {}
    for b in bai:
        theo_o[b["o"]] = theo_o.get(b["o"], 0) + 1
    return {"nguoi": ky, "bai": bai, "loi": loi, "canh": canh, "trung": trung,
            "can_chep": can_chep, "reserve": reserve,
            "tong_khoi": tong_khoi, "bo_trong": bo_trong, "theo_o": theo_o,
            "o_trong": [o for o in SH.BANG_O if not theo_o.get(o)],
            "da_co_trong_pool": len([c for c in co_san
                                     if c.get("status", "accepted") == "accepted"])}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("goi", help="File gói chép tay")
    a = p.parse_args()

    SH, IN = _nap("seal_geometry_holdout"), _nap("ingest_holdout_batch")
    r = soi(Path(a.goi).read_text(encoding="utf-8"), SH, IN)

    n = len(r["bai"])
    ung_vien = n + len(r["can_chep"])
    print(f"CHỮ KÝ    : {r['nguoi'] or '⛔ THIẾU'}")
    print(f"TIẾN ĐỘ   : đã chép {n}/{ung_vien} ứng viên · "
          f"còn {len(r['can_chep'])}")
    if r["can_chep"]:
        import collections as _c
        con = _c.Counter(r["can_chep"])
        print("            còn phải chép: "
              + " ".join(f"{o}×{k}" if k > 1 else o
                         for o, k in sorted(con.items())))
    print(f"            + {r['reserve']} khối RESERVE — bỏ trống là ĐÚNG, "
          f"chỉ dùng khi có ứng viên bị loại lúc ingest")
    du = n + r["da_co_trong_pool"]
    print(f"NGƯỠNG    : {du}/{SH.TONG_TOI_THIEU} bài · "
          f"phủ {len(SH.BANG_O) - len(r['o_trong'])}/{len(SH.BANG_O)} ô")
    if r["o_trong"]:
        print(f"            ô chưa có: {' '.join(r['o_trong'])}")

    for x in r["canh"]:
        print("  ⚠️ ", x)
    if r["trung"]:
        print(f"\n⛔ TRÙNG case_id: {', '.join(r['trung'])}")
    if r["loi"]:
        print(f"\n⛔ {len(r['loi'])} LỖI:")
        for d in r["loi"]:
            print("   ·", d)

    xong = not r["loi"] and not r["trung"] \
        and du >= SH.TONG_TOI_THIEU and not r["o_trong"]
    print(f"\nPACKET_READY: {'YES' if xong else 'NO'}")
    if not xong:
        print("Điền tiếp rồi chạy lại. Khối nào bỏ hẳn thì XOÁ NGUYÊN KHỐI.")
    else:
        print("Chạy: python scripts/run_phase7b_data_pipeline.py <gói> --ghi")
    # ⚠️ Xanh ở đây KHÔNG nói đề đúng nguyên văn nguồn — máy không kiểm được
    # điều đó, và giả vờ kiểm được là bỏ đúng cái cổng vừa dựng.
    return 0 if xong else 1


if __name__ == "__main__":
    raise SystemExit(main())
