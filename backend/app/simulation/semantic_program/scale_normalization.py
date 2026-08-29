# -*- coding: utf-8 -*-
"""`SOURCE_SYMBOL_BINDING` — chuẩn hoá THANG TỰ DO của đề hình học.

    AB = a          →   AB = 1
    SA = 4a/5       →   SA = 4/5

─── VÌ SAO PHẢI CÓ MỘT KÊNH RIÊNG, KHÔNG NỚI `model_assumption` ──────────

`grounding_gate._KIEU_DUOC_GIA_THIET` chỉ cho `point3`/`vector3` mang giả
thiết mô hình hoá, và giới hạn ấy **giữ nguyên**: đại lượng vô hướng là chỗ
đáp án sống, mở nó ra là mở thẳng đường cho một chương trình khai `V = 2/3`
dưới nhãn "giả thiết".

Nhưng đề hình học phổ thông gần như luôn viết `AB = a` — một **ký hiệu**, cố
ý không cho số, vì đáp án tính theo `a`. Hệ V2 đo được hệ quả: mô hình muốn
khai `a_val = 1.0` mà không có đường nào hợp lệ (`model_assumption` sai kiểu ·
`source_fact_id` trượt vì mục dữ kiện giữ chuỗi `'a'` chứ không giữ `1.0`).
Đó là **khoảng trống biểu diễn**, không phải mô hình sai.

Chỗ đúng để bịt nó không phải ở LLM. Chọn thang là một phép TẤT ĐỊNH:
`a → 1`. Server làm việc ấy TRƯỚC khi mô hình nhìn thấy hợp đồng, nên mô
hình không còn gì để chọn — nó nhận `AB = 1`, `SA = 4/5` như dữ kiện số bình
thường và đi đường `source_fact_id` nghiêm ngặt như mọi dữ kiện khác.

    Thẩm quyền buộc thang thuộc hệ TẤT ĐỊNH. LLM không được tự chọn `a = 5`,
    `a = 25`, hay bất kỳ giá trị nào.

─── VÌ SAO CHUẨN HOÁ VỀ 1 LÀ AN TOÀN ────────────────────────────────────

Mọi thứ đề hỏi ở lớp này — quan hệ song song/vuông góc, tỉ số, **cos² góc** —
bất biến theo phép vị tự. Khoảng cách và thể tích thì KHÔNG bất biến, nhưng
chúng tỉ lệ với `a` (bậc 1) và `a³` (bậc 3), nên đáp án theo `a` khôi phục
được từ đáp án ở thang 1. Bộ chấm oracle đã làm đúng phép ấy từ wave trước
(`run_geometry_dev_evaluation._thang_do`); file này chuyển việc đó lên phía
TRƯỚC, để cả chương trình lẫn bộ chấm nói cùng một thang.

─── FAIL CLOSED ─────────────────────────────────────────────────────────

Không chứng minh được thì KHÔNG chuẩn hoá — hợp đồng đi tiếp y nguyên và
cổng grounding từ chối như trước. Cụ thể, năm chỗ trả `None`:

  ① không có mục dữ kiện nào là biểu thức thang;
  ② HAI ký hiệu tự do trở lên — nguồn không chứng minh chúng cùng một thang
    (`a` và `b` có thể độc lập), nên không được tự kết luận;
  ③ đề GÁN số cho ký hiệu (`a = 5`) — khi ấy nó không tự do;
  ④ ký hiệu chính là **đại lượng cần tìm** ("tìm a") — buộc nó về 1 là xoá
    mất câu hỏi;
  ⑤ có token lượng nhắc ký hiệu mà KHÔNG phân tích được (`a√2`, `a^2`,
    `3/2a`) — biểu thức vô tỉ hoặc nhập nhằng, không được đoán.
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import Any

from pydantic import BaseModel, ConfigDict

#: Một BIỂU THỨC THANG: hệ số nguyên tuỳ chọn · ký hiệu thường · mẫu tuỳ chọn.
#:
#: Dạng `3/2a` cố ý KHÔNG khớp: nó đọc được thành `(3/2)·a` lẫn `3/(2a)`, và
#: đoán một trong hai là đúng cái §8-H gọi là nhập nhằng. Không khớp ⇒ rơi vào
#: nhánh ⑤ ở docstring, tức fail closed chứ không phải bỏ qua.
_MAU_THANG = re.compile(r"^\s*(\d+)?\s*\*?\s*([a-z])\s*(?:/\s*(\d+))?\s*$")

#: Một TOKEN LƯỢNG — không khoảng trắng, không dấu tiếng Việt, đủ ngắn.
#:
#: Ranh giới này tách *đại lượng* khỏi *văn xuôi*. `"tam giác SAB vuông tại S"`
#: là mô tả quan hệ, không phải một con số, nên nó không bao giờ được kéo vào
#: phép chuẩn hoá thang — kể cả khi trong đó có chữ cái nào đó.
_TOKEN_LUONG = re.compile(r"^[0-9A-Za-z√^*/·.()+\-]{1,12}$")

#: Ký hiệu THƯỜNG đứng riêng. Chữ số ĐƯỢC phép đứng trước (`4a`, `2a`), chữ cái
#: thì không (`abc` là một từ, không phải ba ký hiệu).
#:
#: `[^\W\d_]` = "chữ cái Unicode", và lookbehind phải dùng ĐÚNG lớp ấy chứ
#: không phải `[A-Za-z]`: tiếng Việt có `chưa`, `mưa`, `giữa` — chữ `a` đứng
#: sau một chữ cái CÓ DẤU. Chặn theo ASCII thì mọi từ như thế biến thành một
#: "ký hiệu tự do", và hệ sẽ đi chuẩn hoá thang cho một bài không có thang nào.
_KY_HIEU_RIENG = re.compile(r"(?<![^\W\d_])([a-z])(?![^\W_]|\d)")

#: `a = 5`, `a = 5cm`. Có số gán ⇒ ký hiệu KHÔNG tự do.
_GAN_SO = r"(?<!\w){sym}\s*=\s*\d"

#: "tìm a", "tính giá trị của a". Ký hiệu là ĐÁP ÁN ⇒ không được buộc về 1.
_LA_AN_SO = r"(?:tính|tìm|xác định)\s+(?:giá\s+trị\s+)?(?:của\s+)?{sym}(?!\w)"


class ScaleBinding(BaseModel):
    """Một phép buộc thang đã CHỨNG MINH được, do server sở hữu."""

    model_config = ConfigDict(frozen=True)

    #: Ký hiệu tự do của đề, ví dụ `'a'`.
    symbol: str
    #: Thang chuẩn. Luôn là `"1"` — hằng số của chính sách, không phải lựa chọn.
    canonical_value: str = "1"
    #: Các mục dữ kiện đã được viết lại. `fact_id` KHÔNG đổi.
    fact_ids: tuple[str, ...] = ()
    #: Cặp `(nguyên văn → đã chuẩn hoá)`, để đọc ngược được chuỗi xuất xứ.
    rewrites: tuple[tuple[str, str, str], ...] = ()


def _ky_hieu_rieng(s: str) -> set[str]:
    return set(_KY_HIEU_RIENG.findall(s))


def _got(s: str) -> str:
    """Bỏ dấu câu cuối. `analyze` trích `"2a."` khi đại lượng đứng cuối câu.

    Đây là vệ sinh TÁCH TỪ, không phải phép đoán: `.` `,` `;` `:` không bao giờ
    là một phần của biểu thức thang. Không gọt thì `"2a."` rơi vào nhánh ⑤ và
    một dấu chấm câu đủ để giết phép chuẩn hoá của cả bài.
    """
    return s.strip().rstrip(".,;:")


def _viet(fr: Fraction) -> Any:
    """Cách viết CHÍNH XÁC của một số hữu tỉ. Không đi qua `float`.

    Mẫu bằng 1 thì trả `int` — để `norm_value` của hợp đồng nhìn thấy đúng một
    con số chứ không phải chuỗi `"1"`. Ngược lại giữ nguyên `p/q`: `4/5` viết
    thành `0.8` là mất tính chính xác đúng ở chỗ hệ này hứa không mất.
    """
    return fr.numerator if fr.denominator == 1 else f"{fr.numerator}/{fr.denominator}"


def _quet(contract) -> tuple[dict[str, list[tuple[str, str, Fraction]]], set[str]]:
    """`({ký hiệu: [(fact_id, nguyên văn, hệ số)]}, {ký hiệu HỎNG})`."""
    ung: dict[str, list[tuple[str, str, Fraction]]] = {}
    hong: set[str] = set()
    for f in contract.input_facts:
        for v in f.values:
            s = _got(str(v))
            if not _TOKEN_LUONG.fullmatch(s):
                continue  # văn xuôi — không phải đại lượng
            m = _MAU_THANG.fullmatch(s)
            if m is None:
                hong |= _ky_hieu_rieng(s)
                continue
            he_so = Fraction(int(m.group(1) or 1), int(m.group(3) or 1))
            ung.setdefault(m.group(2), []).append((f.fact_id, s, he_so))
    return ung, hong


def tim_thang(contract, problem_text: str | None) -> ScaleBinding | None:
    """Ký hiệu thang tự do DUY NHẤT của đề, hoặc `None`. Không bao giờ đoán."""
    if not problem_text:
        return None
    ung, hong = _quet(contract)
    ung = {k: v for k, v in ung.items() if k not in hong}
    if len(ung) != 1:
        # 0 ⇒ đề cho số cụ thể. ≥2 ⇒ hai đại lượng ký hiệu ĐỘC LẬP; nguồn không
        # nói chúng cùng một thang, nên buộc cả hai về 1 là bịa ra `a = b`.
        return None
    sym, muc = next(iter(ung.items()))

    if any(he_so <= 0 for _, _, he_so in muc):
        return None
    # `a)`, `b)` là NHÃN Ý HỎI, không phải ký hiệu đại lượng — và đề nhiều ý
    # thì gần như đề nào cũng có chúng. Đòi ít nhất một lần xuất hiện KHÔNG
    # phải nhãn, nếu không phép kiểm "ký hiệu có thật trong đề" luôn đúng và
    # do đó không kiểm gì cả.
    if not re.search(rf"(?<![^\W\d_]){re.escape(sym)}(?![^\W_]|\d|\))",
                     problem_text):
        return None
    if re.search(_GAN_SO.format(sym=re.escape(sym)), problem_text):
        return None
    if re.search(_LA_AN_SO.format(sym=re.escape(sym)), problem_text, re.IGNORECASE):
        return None
    for ob in contract.obligations:
        ten = [ob.container, ob.witness] + [
            v for v in (ob.params or {}).values() if isinstance(v, str)
        ]
        if any(t == sym for t in ten if t):
            return None  # ký hiệu chính là đại lượng nghĩa vụ đang hỏi

    return ScaleBinding(
        symbol=sym,
        fact_ids=tuple(dict.fromkeys(fid for fid, _, _ in muc)),
        rewrites=tuple((fid, goc, str(_viet(he_so))) for fid, goc, he_so in muc),
    )


def ap_dung(contract, binding: ScaleBinding):
    """Viết lại các mục dữ kiện theo thang chuẩn. `fact_id` giữ nguyên."""
    goc_theo_fact = {fid: goc for fid, goc, _ in binding.rewrites}
    he_so_theo_goc = {
        goc: Fraction(int(m.group(1) or 1), int(m.group(3) or 1))
        for _, goc, _ in binding.rewrites
        if (m := _MAU_THANG.fullmatch(goc)) is not None
    }
    facts = []
    for f in contract.input_facts:
        if f.fact_id not in goc_theo_fact:
            facts.append(f)
            continue
        moi = []
        for v in f.values:
            s = _got(str(v))
            moi.append(_viet(he_so_theo_goc[s]) if s in he_so_theo_goc else v)
        facts.append(
            f.model_copy(update={
                "values": tuple(moi),
                "original_values": tuple(f.values),
                "scale_symbol": binding.symbol,
            })
        )
    return contract.model_copy(update={
        "input_facts": tuple(facts), "scale_binding": binding,
    })


def chuan_hoa_thang(contract, problem_text: str | None):
    """Điểm vào duy nhất. Không chứng minh được ⇒ trả nguyên hợp đồng."""
    binding = tim_thang(contract, problem_text)
    return contract if binding is None else ap_dung(contract, binding)


#: `"4/5"` và `0.8` là CÙNG MỘT SỐ, viết hai cách. Hợp đồng giữ cách chính xác;
#: IR chỉ viết được `float` vì JSON không có kiểu phân số. Không có phép so này
#: thì chuẩn hoá thang tự bắn vào chân mình: mục ghi `4/5`, chương trình khai
#: `0.8`, và P2 kết luận "đề không cho giá trị này".
_HUU_TI = re.compile(r"^-?\d+/\d+$")


def la_so_huu_ti(v: Any) -> bool:
    """`v` có phải MỘT CON SỐ không — `2`, `0.8`, hay `'4/5'` viết chính xác.

    Cổng grounding hỏi câu này để biết một mục dữ kiện có gì để đối chiếu hay
    không. Chỉ hỏi bằng `isinstance(int|float)` là bỏ sót đúng thứ phép chuẩn
    hoá thang vừa tạo ra: `'4/5'` là một con số, và coi nó là "dữ kiện quan hệ
    không có gì để so" biến kênh giả thiết toạ độ thành cửa sau.
    """
    return _fr(v) is not None


def bang_huu_ti(a: Any, b: Any) -> bool:
    """So hai giá trị như số hữu tỉ. `False` khi một bên không phải số."""
    try:
        fa, fb = _fr(a), _fr(b)
    except (TypeError, ValueError, ZeroDivisionError):
        return False
    return fa is not None and fb is not None and fa == fb


def _fr(v: Any) -> Fraction | None:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, int):
        return Fraction(v)
    if isinstance(v, float):
        return Fraction(v).limit_denominator(10**6)
    if isinstance(v, str) and _HUU_TI.fullmatch(v.strip()):
        return Fraction(v.strip())
    return None
