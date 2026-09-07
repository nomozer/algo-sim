# -*- coding: utf-8 -*-
"""Đọc TOẠ ĐỘ ĐIỂM đề cho tường minh, phát `SourceInvariant`.

Đặt cạnh `plane_equation.py` và `segment_relation.py` vì cả ba làm **một
việc**: đọc câu văn của đề rồi phát một ràng buộc SERVER sở hữu. Khác nhau ở
chỗ đọc gì — thang đọc `AB = a`, chia đoạn đọc *"M trên AB sao cho…"*, mặt
phẳng đọc `2x − z + 10 = 0`, tầng này đọc `A(0,0,0)`.

─── LỖ NÓ BỊT, ĐO ĐƯỢC 2026-09-08 ────────────────────────────────────────

`NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY` đo được: đề cho `B(6,0,0)`,
chương trình khai `B(99,7,0)`, `source_fact_id` trỏ một fact CÓ THẬT, và hệ
**phục vụ** `V = 540` thay vì `45` với `unjustified_literals = []`.

Nguyên nhân KHÔNG phải *"analyze quên trích toạ độ"* — đo lại với hợp đồng có
đủ toạ độ trong fact thì kết quả **y hệt**. Nguyên nhân là: `source_fact_id`
được kiểm **SỰ TỒN TẠI**, không kiểm **SỰ KHỚP**. Một trích dẫn nêu tên một
fact; không ai kiểm con số có đúng bằng fact ấy không.

Kho đã có bất biến nguồn cho `segment_length` · `segment_division` ·
`plane_equation` · thang đo. Không có cái nào cho **toạ độ điểm**. Đây là nó.

─── VÌ SAO ĐỌC TỪ `problem_text`, KHÔNG ĐỌC TỪ FACT ──────────────────────

Cùng lý do `check_source_invariants` đã ghi: đọc từ fact là tin vào thứ
`analyze` chọn trích. Lượt live của wave trước trích **ba fact kể chuyện**,
không fact nào mang toạ độ — nếu bộ phát phụ thuộc fact thì nó im lặng đúng
lúc cần nhất. Đọc từ câu văn thì một chương trình không tránh được phép kiểm
bằng cách để analyze quên.

─── CHỈ NHỮNG TOẠ ĐỘ ĐỀ NÊU TƯỜNG MINH ───────────────────────────────────

Đề KHÔNG cho toạ độ ⇒ **không phát gì**, và quyền chọn hệ trục bằng
`model_assumption` còn nguyên. Đề CÓ cho ⇒ hệ trục đã do đề quyết, nên một
toạ độ khác là sai chứ không phải "một cách chọn khác".
"""
from __future__ import annotations

import re
from fractions import Fraction

from .scale_normalization import SourceInvariant

#: `kind` của bất biến này. Một chuỗi, một chỗ khai, một checker.
KIND = "point_coordinate"
#: Đề nêu toạ độ cho cùng một điểm ở HAI chỗ MÂU THUẪN — trạng thái CHẶN.
KIND_CHUA_GIAI = "point_coordinate_unresolved"

#: Ký hiệu điểm: một CHỮ HOA, kèm chỉ số và/hoặc phẩy.
#:
#: `A` · `A1` · `A_1` · `A₁` · `A'` · `A′`. Cùng lưới với `_MAU_DOAN_THANG`
#: của `scale_normalization`, nới thêm chỉ số dưới Unicode.
_TEN = r"[A-Z](?:_?\d+|[₀-₉]+)?['′’]?"

#: Số HỮU TỈ CHÍNH XÁC: nguyên · thập phân dấu CHẤM · phân số.
#:
#: ⚠️ Thập phân **dấu phẩy** cố ý KHÔNG nhận. `A(1,5, 2, 3)` đọc được thành
#: hai cách — `(1,5 · 2 · 3)` hoặc `(1 · 5 · 2 · 3)` — và một bộ phát đoán
#: giữa hai cách là đặt phép đoán vào giữa đường gác cửa. Ghi vào giới hạn,
#: không đoán.
_SO = r"[-−+]?\d+(?:\.\d+)?(?:\s*/\s*[-−+]?\d+(?:\.\d+)?)?"

#: `A(1,2,3)` · `A = (1; 2; 3)` · `A(-1/2, 0, 3)`.
#:
#: `(?<![A-Za-z0-9_])` là thứ chặn `AB(1,2,3)` bị đọc thành điểm `B`: một
#: vectơ viết bằng hai chữ cái KHÔNG phải một điểm, và đọc nhầm nó là phát một
#: ràng buộc **không ai viết**.
_MAU = re.compile(
    rf"(?<![A-Za-z0-9_])({_TEN})\s*(?:=|≡)?\s*"
    rf"\(\s*({_SO})\s*[,;]\s*({_SO})\s*[,;]\s*({_SO})\s*\)"
)

#: Chỉ số dưới Unicode → chữ số thường, để tên khớp lưới hoà giải đã có.
_HA = {chr(0x2080 + i): str(i) for i in range(10)}


def _chuan_ten(t: str) -> str:
    t = "".join(_HA.get(c, c) for c in t)
    return t.replace("_", "").replace("′", "'").replace("’", "'")


def _phan_so(s: str) -> Fraction | None:
    """Chuỗi → `Fraction` CHÍNH XÁC, hoặc `None` nếu ngoài ngưỡng đọc."""
    t = s.replace("−", "-").replace(" ", "")
    if t.startswith("+"):
        t = t[1:]
    try:
        return Fraction(t)
    except (ValueError, ZeroDivisionError):
        return None


def doc_toa_do(manh: list[str]) -> dict[str, set[tuple[Fraction, ...]]]:
    """Mọi toạ độ điểm đọc được, gom theo TÊN đã chuẩn hoá.

    Trả về TẬP các bộ ba cho mỗi tên: một tên có thể xuất hiện nhiều lần (đề
    và mục dữ kiện thường lặp lại nhau), và chỉ khi hai lần ấy **khác nhau**
    thì mới có mâu thuẫn.
    """
    ra: dict[str, set[tuple[Fraction, ...]]] = {}
    for van in manh:
        for m in _MAU.finditer(van or ""):
            bo = tuple(_phan_so(m.group(i)) for i in (2, 3, 4))
            if any(x is None for x in bo):
                continue
            ra.setdefault(_chuan_ten(m.group(1)), set()).add(bo)
    return ra


def _nguon(contract, ten: str) -> str:
    """Mục dữ kiện nhắc tới điểm này — CHỈ để truy vết, không để quyết định."""
    for f in getattr(contract, "input_facts", ()) or ():
        van = " ".join([str(getattr(f, "label", "") or "")]
                       + [str(v) for v in (getattr(f, "values", ()) or ())])
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(ten)}(?![A-Za-z0-9_])", van):
            return f.fact_id
    return ""


def bat_bien_toa_do(contract, problem_text: str | None) -> tuple:
    """`SourceInvariant(kind="point_coordinate")` cho mỗi điểm đề cho toạ độ.

    ─── HAI VERDICT, KHÔNG PHẢI MỘT ───────────────────────────────────────

    · đọc trọn, một giá trị duy nhất ⇒ `KIND` + `coefficients = (x, y, z)`;
    · **mâu thuẫn** — cùng một tên, hai bộ ba khác nhau ⇒ `KIND_CHUA_GIAI`,
      và cổng **chặn**. Hệ không biết đề muốn điểm nào, và phục vụ một hình
      đoán bừa còn tệ hơn từ chối. Cùng chính sách với
      `plane_equation.KIND_CHUA_GIAI`.

    Cú pháp ngoài ngưỡng đọc ⇒ **im lặng bỏ qua**, không chặn: một đề viết
    toạ độ theo lối lạ không phải một đề mâu thuẫn, và chặn nó là chặn oan.
    Giới hạn ấy được khai trong báo cáo wave thay vì giấu trong mã.
    """
    from .segment_relation import _van_ban

    manh = _van_ban(contract, problem_text)
    if not manh:
        return ()
    ra: list[SourceInvariant] = []
    for ten, bo in sorted(doc_toa_do(manh).items()):
        nguon = _nguon(contract, ten)
        if len(bo) > 1:
            ta = " · ".join(
                "(" + ", ".join(str(x) for x in b) + ")" for b in sorted(bo))
            ra.append(SourceInvariant(
                kind=KIND_CHUA_GIAI, points=(ten,), expected="",
                coefficients=(), source_fact_id=nguon, scale_symbol="",
                source_text=f"{ten}: {ta}"))
            continue
        (x, y, z), = bo
        ra.append(SourceInvariant(
            kind=KIND, points=(ten,), expected="",
            coefficients=(str(x), str(y), str(z)),
            source_fact_id=nguon, scale_symbol="",
            source_text=f"{ten}({x}, {y}, {z})"))
    return tuple(ra)
