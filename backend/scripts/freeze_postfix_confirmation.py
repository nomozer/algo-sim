# -*- coding: utf-8 -*-
"""ĐÓNG BĂNG tập xác nhận POSTFIX — 6 ca reserve. **0 API call.**

    python scripts/freeze_postfix_confirmation.py            # soi
    python scripts/freeze_postfix_confirmation.py --ghi      # đóng băng

─── VÌ SAO KHÔNG ĐI TÌM NGUỒN MỚI ────────────────────────────────────────

Pool Phase 7B có **42 bài accepted**; con dấu rút **20**. Còn **22 bài dự
trữ** thoả ba điều kiện, kiểm được bằng máy chứ không bằng trí nhớ:

  ① chưa từng gửi tới hệ được đo — không artifact lượt chạy nào nhắc tên;
  ② chưa từng dùng làm ca hồi quy DEV — không test nào mang đề của chúng;
  ③ tồn tại TRƯỚC mọi phép sửa sau Phase 7B — commit của `pool.json` là tổ
     tiên của commit sửa.

Điều kiện ③ là chỗ đắt giá: những bài này được soạn khi **chưa ai biết hệ V2
sẽ hỏng ở đâu**. Đi tìm đề mới bây giờ thì không có tính chất ấy, vì người
soạn đã đọc taxonomy thất bại của lượt chính thức.

─── VÌ SAO ĐÓNG BĂNG TRƯỚC LỜI GỌI ĐẦU TIÊN ──────────────────────────────

Chọn xong mới chạy thì không ai chứng minh được là đã không chọn lại. File
này ghi `case_ids` + luật chọn + băm + dấu thời gian, và **từ chối ghi đè**.
Nó chạy khi tuyến live còn đang bị nhà cung cấp chặn — tức tại thời điểm
chưa tồn tại một con số V2 nào để mà chọn theo.

─── LUẬT CHỌN, TẤT ĐỊNH ──────────────────────────────────────────────────

Sáu ô cấu trúc, mỗi ô lấy **case_id nhỏ nhất theo thứ tự chữ** trong nhóm
ứng viên. Không xếp theo độ khó, không xếp theo cảm giác — thứ tự chữ không
mang thông tin về việc bài dễ hay khó, và đó chính là điều cần.

  ① A09  góc đường–đường          ④ quan hệ ∥ hoặc ⊥ (A03–A08)
  ② A10  góc đường–mặt            ⑤ đo lường (A11 · A14)
  ③ ký hiệu PHẨY/dẫn xuất         ⑥ nhiều bước phụ thuộc (A13 · A02)

Ô ③ nhận diện bằng chính đề: có `'` hoặc `′`, hoặc có chỉ số kiểu `A1B1C1`.
Một ca đã được chọn cho ô trước thì không được chọn lại cho ô sau.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
GEO = ROOT / "docs" / "evaluation" / "geometry"
RA = GEO / "postfix-confirmation" / "CONFIRMATION_SELECTION.json"
RA_V2 = GEO / "postfix-confirmation-v2" / "CONFIRMATION_SELECTION.json"

_PHAY = re.compile(r"['′’]")
#: Ký hiệu dẫn xuất kiểu `A1B1C1D1` — chữ hoa kèm chỉ số, lặp ít nhất ba lần.
_CHI_SO = re.compile(r"(?:[A-Z]\d){3,}")


def _co_ky_hieu_dan_xuat(de: str) -> bool:
    return bool(_PHAY.search(de) or _CHI_SO.search(de))


#: `(tên ô cấu trúc, hàm lọc)`. Thứ tự CÓ nghĩa: ô trước chọn trước, và ca đã
#: chọn bị loại khỏi các ô sau.
O_CAU_TRUC = (
    ("goc_duong_duong", lambda c: c["slot"] == "A09"),
    ("goc_duong_mat", lambda c: c["slot"] == "A10"),
    ("ky_hieu_dan_xuat", lambda c: _co_ky_hieu_dan_xuat(c["problem_text"])),
    ("quan_he_song_song_vuong_goc",
     lambda c: c["slot"] in ("A03", "A04", "A05", "A06", "A07", "A08")),
    ("do_luong", lambda c: c["slot"] in ("A11", "A14")),
    ("nhieu_buoc", lambda c: c["slot"] in ("A13", "A02")),
)


def reserve(loai_tru: set[str] | None = None) -> list[dict]:
    """Reserve còn NGUYÊN. `loai_tru` gạt thêm những ca đã dùng ở vòng trước.

    V2 phải loại cả 20 ca chính thức LẪN 6 ca của `POSTFIX_CONFIRMATION_V1`:
    sáu ca ấy đã đi qua hệ được đo, nên chúng mất đúng tính chất làm nên giá
    trị của tập xác nhận. Chúng vẫn chỉ ra được HỌ lỗi, nhưng không bao giờ
    được dùng làm ca xác nhận lần nữa.
    """
    seal = json.loads((GEO / "holdout" / "HOLDOUT_SEAL.json").read_text(encoding="utf-8"))
    pool = json.loads((GEO / "holdout" / "pool.json").read_text(encoding="utf-8"))
    bo = set(seal["case_ids"]) | set(loai_tru or ())
    return sorted(
        (c for c in pool["cases"]
         if c.get("status", "accepted") == "accepted"
         and c["case_id"] not in bo),
        key=lambda c: c["case_id"])


def chon(res: list[dict]) -> tuple[list[dict], list[str]]:
    """Sáu ô, mỗi ô một ca. Trả `(đã chọn, ghi chú ô thiếu)`."""
    con = list(res)
    ra: list[dict] = []
    thieu: list[str] = []
    for ten, loc in O_CAU_TRUC:
        ung = [c for c in con if loc(c)]
        if not ung:
            thieu.append(ten)
            continue
        c = ung[0]                       # `con` đã xếp theo case_id
        ra.append({**c, "__o_cau_truc__": ten})
        con.remove(c)
    # Ô thiếu ⇒ bù bằng ca reserve còn lại, vẫn theo thứ tự chữ. KHÔNG viết đề
    # mới chỉ để đủ ô — đề mới thì mất luôn tính chất "có trước phép sửa".
    while len(ra) < 6 and con:
        c = con.pop(0)
        ra.append({**c, "__o_cau_truc__": "bu_tat_dinh"})
    return ra, thieu


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ghi", action="store_true")
    p.add_argument("--v2", action="store_true",
                   help="Vòng HAI: loại thêm 6 ca của CONFIRMATION_V1.")
    a = p.parse_args()

    dich = RA
    da_dung: set[str] = set()
    if a.v2:
        dich = RA_V2
        da_dung = set(json.loads(RA.read_text(encoding="utf-8"))["case_ids"])
    res = reserve(da_dung)
    ra, thieu = chon(res)
    print(f"RESERVE: {len(res)} · chọn {len(ra)}")
    for c in ra:
        print(f"  {c['__o_cau_truc__']:<28} {c['case_id']:<14} {c['slot']} "
              f"| {c['problem_text'][:62]}")
    if thieu:
        print(f"  ô KHÔNG có ứng viên reserve: {thieu} → bù tất định")

    than = {
        "khai": ("Tập XÁC NHẬN POSTFIX. KHÔNG phải Phase 7B chính thức. Chọn "
                 "và đóng băng TRƯỚC lời gọi model đầu tiên của hệ V2."),
        "nguon": "PRE_EXISTING_UNUSED_PHASE7B_RESERVE",
        "luat_chon": [f"{i+1}. {ten}" for i, (ten, _) in enumerate(O_CAU_TRUC)]
        + ["thứ tự trong mỗi ô: case_id nhỏ nhất theo THỨ TỰ CHỮ — không xếp "
           "theo độ khó", "ca đã chọn bị loại khỏi các ô sau",
           "ô không có ứng viên: bù bằng reserve còn lại theo thứ tự chữ; "
           "KHÔNG viết đề mới"],
        "k": 2,
        "case_ids": [c["case_id"] for c in ra],
        "theo_o_cau_truc": {c["__o_cau_truc__"]: c["case_id"] for c in ra},
        "slot": {c["case_id"]: c["slot"] for c in ra},
        "o_thieu_ung_vien": thieu,
        "reserve_size": len(res),
        "vong": 2 if a.v2 else 1,
        "loai_tru_vong_truoc": sorted(da_dung),
        "pool_hash_luc_chon": hashlib.sha256(
            (GEO / "holdout" / "pool.json").read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "dong_bang_luc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    than["selection_hash"] = hashlib.sha256(
        json.dumps({k: than[k] for k in ("case_ids", "luat_chon", "k")},
                   ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    print(f"\nselection_hash {than['selection_hash'][:16]}…")

    if not a.ghi:
        print("(soi thôi — thêm `--ghi` để đóng băng)")
        return 0
    if dich.exists():
        print(f"ĐÃ ĐÓNG BĂNG: {dich}")
        print("Chọn lại sau khi đã thấy kết quả là bỏ đúng thứ file này bảo vệ.")
        return 1
    dich.parent.mkdir(parents=True, exist_ok=True)
    dich.write_text(json.dumps(than, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(f"Đã ghi {dich}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
