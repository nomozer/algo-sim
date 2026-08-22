# -*- coding: utf-8 -*-
"""EXTERNAL SELECTION POOL — lọc universe bằng ĐÚNG các contamination guard đã khoá.

Pool này để GVHD/người thứ ba chỉ việc chọn 40 ID. Việc lọc **chỉ** dùng các
guard đã đóng băng từ trước, và mỗi lần loại đều ghi rõ **guard nào** đã loại.

TUYỆT ĐỐI KHÔNG dùng để lọc hay xếp hạng: kết quả pilot · checker support ·
expected success/failure · khả năng của IR hiện tại · hành vi prompt · hiểu
biết về dạng nào pipeline thường sinh thành công. Không có thứ nào trong số đó
xuất hiện ở file này.

`expressible_in_ir` giữ vai trò **metadata mô tả**; nó không quyết định một bài
có vào population hay không (sửa 2026-08-22, xem `eligibility_rubric.md`).

HAI GUARD ĐƯỢC ÁP:

1. **Trùng INTERNAL LIVE PILOT** — loại theo provenance (sách + trang + nhãn
   bài), đọc thẳng từ `pilot/sealed-pilot-34a10a9c/cases.json`.

2. **`no_specialized_module`** — loại bài thuộc dạng mà hệ ĐÃ CÓ module chuyên
   biệt. Bảng dưới dẫn xuất từ **tên 24 target trong `CATALOG`**, không từ hành
   vi hay kết quả chạy. Đây là guard về NHIỄM DỮ LIỆU: benchmark phải đo lớp
   bài hệ chưa có module dựng sẵn.

   Quy tắc cố ý nghiêng về phía LOẠI: loại nhầm một bài sạch chỉ làm pool nhỏ
   đi, còn giữ nhầm một bài đã có module thì làm hỏng chính thứ benchmark đo.

    python build_selection_pool.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
PILOT = BENCH / "pilot" / "sealed-pilot-34a10a9c" / "cases.json"

#: dạng bài đã có module chuyên biệt → mẫu nhận dạng trong đề.
#: Khoá bên trái là TÊN TARGET trong CATALOG; giá trị là mẫu văn bản.
GUARD_MODULE: dict[str, str] = {
    "algorithm.linear_search|binary_search":
        r"tìm kiếm (tuần tự|nhị phân)|thuật toán tìm kiếm|tìm ra phần tử có giá trị"
        r"|tìm kiếm phần tử|vị trí .{0,25}trong (dãy|danh sách)",
    "algorithm.bubble_sort|insertion_sort|selection_sort":
        r"sắp xếp|sắp thứ tự|thứ tự (tăng|giảm) dần|nổi bọt|chèn|chọn.{0,10}dãy",
    "algorithm.find_max|find_min":
        r"(lớn nhất|nhỏ nhất|cao nhất|thấp nhất|max|min)",
    "algorithm.count_if|sum_if|scan":
        r"đếm (số|xem)|tổng (các|của)|trung bình",
    "algorithm.bounded_control_flow":
        r"luỹ kế|theo từng mức|nếu .{0,40}thì giá|bậc thang",
    "binary.base_conversion|decimal_to_binary|character_encoding":
        r"nhị phân|hệ cơ số|mã ASCII|bảng mã|chuyển .{0,15}sang hệ|bit\b",
    "color.rgb_model": r"\bRGB\b|kênh màu|hệ màu",
    "database.relational_table_query":
        r"truy vấn|SELECT\b|cơ sở dữ liệu|bảng dữ liệu|CSDL",
    "logic.and_gate|boolean_dag":
        r"mạch lôgic|cổng (AND|OR|NOT)|biểu thức lôgic|phép toán lôgic",
    "network.graph_traversal|packet_routing|protocol_encapsulation":
        r"đồ thị|BFS|DFS|gói tin|giao thức|định tuyến",
    "tree.traversal": r"duyệt cây|cây nhị phân|tiền thứ tự|trung thứ tự",
    "web.style_model": r"HTML|CSS|trang web|thẻ <|<img|thuộc tính .{0,10}width",
}

_RX = {k: re.compile(v, re.I) for k, v in GUARD_MODULE.items()}


def _pilot_provenance() -> set[tuple[str, int, str]]:
    """(sách, trang, nhãn bài) của mọi case trong INTERNAL LIVE PILOT."""
    if not PILOT.exists():
        return set()
    ra = set()
    for c in json.loads(PILOT.read_text(encoding="utf-8"))["cases"]:
        src = c.get("source") or {}
        loc = str(src.get("location") or "")
        m = re.search(r"trang\s*(\d+)", loc)
        if not m:
            continue
        nhan = loc.split(",", 1)[1].strip().lower() if "," in loc else ""
        ra.add((str(src.get("book") or ""), int(m.group(1)), nhan))
    return ra


def _trung_pilot(rec: dict, pilot: set) -> bool:
    for book, page, nhan in pilot:
        if rec["book"] != book or rec["page"] != page:
            continue
        vt = rec["exercise_number_or_position"].lower()
        # Cùng trang + nhãn bài chồng nhau (một bên là tiền tố của bên kia).
        if not nhan or nhan.startswith(vt[:9]) or vt.startswith(nhan[:9]):
            return True
    return False


def guard_module(rec: dict) -> list[str]:
    txt = rec["problem_text"] + " " + rec.get("context_text", "")
    return [k for k, rx in _RX.items() if rx.search(txt)]


def _md_pool(n_uni: int, n_pool: int, n_loai: int, van_tay: str, bang: str) -> str:
    return f"""# EXTERNAL SELECTION POOL — chọn 40 ID từ bảng dưới

> Bảng này dành cho **GVHD/người thứ ba**. Quyền chọn 40 case thuộc về bạn.
> Development agent chỉ lọc theo các guard đã đóng băng và trình bày.

Bảng **cố ý không hiển thị**: checker support · IR support · dự đoán thành công
· chi tiết cài đặt · kết quả pilot. Chọn dựa trên **nội dung bài và nguồn**, chứ
không dựa trên phỏng đoán hệ làm được gì.

## Quy mô

| | |
|---|---|
| Source universe V2 | {n_uni} record |
| **Đủ điều kiện (pool)** | **{n_pool}** |
| Bị loại bởi guard | {n_loai} |

Cần chọn **40** trong {n_pool} — dư khoảng {n_pool / 40:.1f}×.

## Guard đã áp (chỉ hai, đều đã đóng băng từ trước)

1. **Trùng INTERNAL LIVE PILOT** — loại theo provenance (sách + trang + nhãn
   bài), đọc thẳng từ `pilot/sealed-pilot-34a10a9c/cases.json`. Tập pilot đã bị
   chạy bốn lượt nên tính held-out của nó bằng không.

2. **`no_specialized_module`** — loại bài thuộc dạng hệ **đã có module chuyên
   biệt**. Bảng mẫu dẫn xuất từ **tên 24 target trong `CATALOG`**, không từ hành
   vi hay kết quả chạy. Đây là guard chống **nhiễm dữ liệu**: benchmark phải đo
   lớp bài hệ chưa có module dựng sẵn.

`expressible_in_ir` **không** được dùng để lọc — nó chỉ là metadata mô tả. Bài
thoả rubric mà IR hiện tại có thể chịu thua vẫn ở trong pool; nếu được chọn và
hệ chịu thua thì đó là `capability_gap`, một kết quả nghiên cứu hợp lệ.

Danh sách bị loại kèm **lý do từng case**: `EXTERNAL_SELECTION_POOL_EXCLUDED.json`.

## Fingerprint

```
{van_tay}
```

SHA-256 của `EXTERNAL_SELECTION_POOL.json`. Selection chỉ được thực hiện **sau**
khi fingerprint này đã đóng băng.

Cách chọn: `EXTERNAL_SELECTION_INSTRUCTIONS.md`.

## Bảng chọn

{bang}
"""


def main() -> int:
    uni = json.loads((HERE / "source_universe.json").read_text(encoding="utf-8"))
    recs = uni["records"]
    pilot = _pilot_provenance()

    pool, loai = [], []
    for r in recs:
        ly_do = []
        if _trung_pilot(r, pilot):
            ly_do.append("trùng INTERNAL LIVE PILOT (sách + trang + nhãn bài)")
        mods = guard_module(r)
        if mods:
            ly_do.append("no_specialized_module: " + ", ".join(mods))
        (loai if ly_do else pool).append(
            {**r, "loai_vi": ly_do} if ly_do else r)

    payload = {
        "khai": (
            "Pool để GVHD/custodian độc lập chọn 40 ID. Lọc CHỈ bằng các "
            "contamination guard đã đóng băng; không dùng kết quả pilot, "
            "checker support, khả năng IR hay dự đoán thành công."
        ),
        "source_universe_fingerprint": hashlib.sha256(
            (HERE / "source_universe.json").read_bytes()).hexdigest(),
        "guards_applied": ["pilot_provenance_overlap", "no_specialized_module"],
        "eligible_count": len(pool),
        "excluded_count": len(loai),
        "records": pool,
    }
    js = HERE / "EXTERNAL_SELECTION_POOL.json"
    js.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                  encoding="utf-8")
    van_tay = hashlib.sha256(js.read_bytes()).hexdigest()
    (HERE / "EXTERNAL_SELECTION_POOL_FINGERPRINT.txt").write_text(
        van_tay + "\n", encoding="utf-8")

    (HERE / "EXTERNAL_SELECTION_POOL_EXCLUDED.json").write_text(
        json.dumps({"excluded": loai}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    LOP = {"tin-hoc-10.pdf": ("TH10", "10"),
           "tin-hoc-11-cs.pdf": ("TH11-KHMT", "11"),
           "tin-hoc-11-ict.pdf": ("TH11-ICT", "11"),
           "tin-hoc-12-cs.pdf": ("TH12-KHMT", "12"),
           "tin-hoc-12-ict.pdf": ("TH12-ICT", "12")}
    dong = ["| ID | SGK | Lớp | Chủ đề | Trang | Số bài/vị trí | Mô tả nhận diện ngắn |",
            "|---|---|---|---|---|---|---|"]
    for r in pool:
        sach, lop = LOP[r["book"]]
        cd = r["section_or_chapter"].split("—")[0].strip()
        mo_ta = " ".join(r["problem_text"].split())
        if len(mo_ta) > 100:
            mo_ta = mo_ta[:99].rsplit(" ", 1)[0] + "…"
        dong.append(f"| `{r['source_id']}` | {sach} | {lop} | {cd} | {r['page']} | "
                    f"{r['exercise_number_or_position']} | {mo_ta.replace('|', '/')} |")

    (HERE / "EXTERNAL_SELECTION_POOL.md").write_text(
        _md_pool(len(recs), len(pool), len(loai), van_tay, "\n".join(dong)),
        encoding="utf-8")

    print(f"universe : {len(recs)}")
    print(f"eligible : {len(pool)}")
    print(f"excluded : {len(loai)}")
    print(f"pool fingerprint: {van_tay}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
