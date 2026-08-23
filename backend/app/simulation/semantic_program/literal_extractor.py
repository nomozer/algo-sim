# -*- coding: utf-8 -*-
"""P1 — TRÍCH LITERAL TẤT ĐỊNH TỪ ĐỀ, KÈM BẰNG CHỨNG NGUỒN.

─── VÌ SAO TỒN TẠI ────────────────────────────────────────────────────────────

Probe E2E sản phẩm (2026-08-23) trên đề *"Kiểm tra tính hợp lệ của chuỗi đóng mở
ngoặc bằng Stack với chuỗi {[()]}"* cho ra:

    analysis.data[0].values = null
    analysis.notes          = "Đề bài cung cấp ví dụ cụ thể là chuỗi '{[()]}'"

LLM **đã đọc thấy** literal — nó chỉ không chép sang đúng ô. Và vì `InputFact`
lấy giá trị thẳng từ ô đó, `check_grounding` trượt với thông điệp *"đề không cho
những giá trị này"* trong khi đề cho rất rõ. Bài toán ở đây không phải nhận thức,
mà là **đường dẫn**: một giá trị bắt buộc của bài đang phụ thuộc vào việc model
nhớ copy-paste.

─── RANH GIỚI: XÁC MINH, KHÔNG PHẢI HIỂU ĐỀ ──────────────────────────────────

Module này **không suy vai trò ngữ nghĩa**. Nó không biết `{[()]}` là "đầu vào"
hay "ví dụ minh hoạ", không biết `10` là "số phần tử" hay "giá trị cần tìm". Đó
vẫn là việc của `analyze`.

Việc của nó đúng một câu: **liệt kê các literal CÓ THẬT trong đề, kèm span**.
Nhờ đó quan hệ bị lật ngược — thay vì "LLM phải nhớ chép giá trị", thành "mọi
giá trị LLM khai phải chứng minh được bằng một đoạn văn bản trong đề".

Cách đặt ranh giới này là có chủ đích. Một extractor *hiểu đề* ("nhãn nào ám chỉ
đầu vào") là bài NLP mở trên văn bản tiếng Việt tự do — không đóng được, không
kiểm được. Một extractor *chứng minh* thì quyết định được: chạy lại đúng luật
parse của kind trên `text[start:end]` và so kết quả.

─── VÌ SAO KHÔNG PHẢI PROVENANCE TOÀN DIỆN ───────────────────────────────────

`RULES §3b` xếp "fingerprint/provenance toàn diện" vào DEEP_HARDENING. Module này
cố ý **chỉ** đóng P1 cho các lớp literal hiển nhiên. Dữ liệu mô tả bằng văn xuôi
(một đồ thị kể bằng lời, một cây vẽ bằng hình) **không** có span và **không** bị
đòi span — xem `LITERAL_KINDS_DUOC_CUONG_CHE`.
"""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict

from .request_contract import norm_value

#: Các lớp literal mà extractor này CAM KẾT phủ hết. Chỉ trong các lớp này thì
#: "không có span" mới đồng nghĩa với "bịa" — ngoài chúng, vắng span là bình
#: thường (dữ liệu kể bằng văn xuôi). Đây là ranh giới khiến §3 kiểm được mà
#: không từ chối oan các đề đồ thị/cây mô tả bằng lời.
LITERAL_KINDS_DUOC_CUONG_CHE = ("array", "str", "int", "float", "bool")


class LiteralCandidate(BaseModel):
    """Một literal đọc được từ đề, kèm toạ độ chứng minh được."""

    model_config = ConfigDict(frozen=True)

    kind: str
    source_start: int
    source_end: int
    source_text: str
    normalized_value: tuple[Any, ...]
    #: Tên đứng ngay trước `=` nếu có (`n = 10` ⇒ `"n"`). GỢI Ý cho merge, không
    #: phải phán quyết: `analyze` vẫn là bên nói fact nào mang giá trị nào.
    label_hint: str | None = None


# ── Luật parse theo từng kind ─────────────────────────────────────────────────
#
# Mỗi kind có ĐÚNG MỘT hàm parse, và `verify_candidate` chạy lại chính hàm đó.
# Nhờ vậy bất biến P1 không phải lời hứa trong tài liệu mà là một phép so sánh.

_SO = r"-?\d+(?:\.\d+)?"


def _so_tu_chuoi(s: str) -> Any:
    return norm_value(s.strip())


def _parse_mang(s: str) -> tuple[Any, ...]:
    """`[3, 1, 4]` ⇒ `(3, 1, 4)`. Chỉ mảng số hoặc mảng chuỗi có nháy."""
    ruot = s.strip()[1:-1].strip()
    if not ruot:
        return ()
    phan = [p.strip() for p in ruot.split(",")]
    ra: list[Any] = []
    for p in phan:
        if len(p) >= 2 and p[0] in "\"'" and p[-1] == p[0]:
            ra.append(p[1:-1])
        else:
            ra.append(_so_tu_chuoi(p))
    return tuple(ra)


def _parse_chuoi_nhay(s: str) -> tuple[Any, ...]:
    """Bỏ đúng một lớp nháy ngoài cùng. Giữ nguyên phần bên trong."""
    return (s[1:-1],)


def _parse_nguyen_van(s: str) -> tuple[Any, ...]:
    """Token đứng một mình (chuỗi ngoặc `{[()]}`) — chính nó là giá trị."""
    return (s,)


def _parse_so(s: str) -> tuple[Any, ...]:
    return (_so_tu_chuoi(s),)


def _parse_bool(s: str) -> tuple[Any, ...]:
    return (s.strip().lower() == "true",)


#: (tên kind, regex, hàm parse, nhóm regex mang giá trị, nhóm regex mang nhãn)
#:
#: THỨ TỰ LÀ ƯU TIÊN và nó quan trọng: `[3, 1, 4]` phải được đọc là MỘT mảng
#: trước khi `3`, `1`, `4` kịp được đọc là ba số rời. Match nào chồng lên span
#: đã nhận thì bị bỏ.
_LUAT: tuple[tuple[str, re.Pattern[str], Any, int, int | None], ...] = (
    # Mảng số/chuỗi viết tường minh.
    ("array", re.compile(r"\[\s*(?:" + _SO + r"|\"[^\"]*\"|'[^']*')"
                         r"(?:\s*,\s*(?:" + _SO + r"|\"[^\"]*\"|'[^']*'))*\s*\]"),
     _parse_mang, 0, None),
    # Chuỗi ngoặc — lớp literal của chính bài Stack. Từ 2 ký tự trở lên để
    # không nuốt dấu ngoặc đơn thường gặp trong văn xuôi tiếng Việt.
    ("str", re.compile(r"[()\[\]{}]{2,}"), _parse_nguyen_van, 0, None),
    # Chuỗi trong nháy — kể cả nháy cong mà trình soạn thảo tiếng Việt hay chèn.
    ("str", re.compile(r"[\"“]([^\"”]+)[\"”]|'([^']+)'"), _parse_chuoi_nhay, 0, None),
    # Gán vô hướng: span chỉ ôm ĐÚNG con số, còn tên đi vào `label_hint`. Nhờ
    # thế `text[start:end]` vẫn bằng thẳng giá trị, không cần luật riêng.
    ("num_assign", re.compile(r"\b([A-Za-z_]\w*)\s*=\s*(" + _SO + r")"),
     _parse_so, 2, 1),
    ("bool", re.compile(r"\b(?:true|false)\b", re.IGNORECASE), _parse_bool, 0, None),
    ("num", re.compile(r"(?<![\w.])" + _SO + r"(?![\w.])"), _parse_so, 0, None),
)

#: Kind thật của một literal số được quyết bởi GIÁ TRỊ, không bởi regex đã bắt
#: nó — `n = 10` và `10` đứng lẻ đều phải ra `int`.
def _kind_so(v: Any) -> str:
    if isinstance(v, bool):
        return "bool"
    return "float" if isinstance(v, float) else "int"


def extract_literals(problem_text: str) -> tuple[LiteralCandidate, ...]:
    """Mọi literal đọc được từ đề, span không chồng nhau, theo thứ tự xuất hiện.

    Tất định hoàn toàn: cùng một `problem_text` luôn cho cùng một kết quả, không
    phụ thuộc mạng, model hay thời điểm.
    """
    if not problem_text:
        return ()

    da_nhan: list[tuple[int, int]] = []
    ra: list[LiteralCandidate] = []

    def chong(a: int, b: int) -> bool:
        return any(a < y and x < b for x, y in da_nhan)

    for ten_kind, rx, parse, nhom_gt, nhom_nhan in _LUAT:
        for m in rx.finditer(problem_text):
            s, e = m.span(nhom_gt) if nhom_gt else m.span()
            if chong(m.start(), m.end()):
                continue
            doan = problem_text[s:e]
            try:
                gia_tri = parse(doan)
            except (ValueError, IndexError):
                continue
            if not gia_tri:
                continue

            kind = ten_kind
            if ten_kind in ("num", "num_assign"):
                kind = _kind_so(gia_tri[0])

            # Nhận span của TOÀN BỘ match (không chỉ nhóm giá trị) để `n = 10`
            # không cho phép `10` được nhận thêm một lần nữa dưới dạng số lẻ.
            da_nhan.append((m.start(), m.end()))
            ra.append(
                LiteralCandidate(
                    kind=kind,
                    source_start=s,
                    source_end=e,
                    source_text=doan,
                    normalized_value=gia_tri,
                    label_hint=m.group(nhom_nhan) if nhom_nhan else None,
                )
            )

    return tuple(sorted(ra, key=lambda c: c.source_start))


def verify_candidate(cand: LiteralCandidate, problem_text: str) -> bool:
    """BẤT BIẾN P1 — `problem_text[start:end]` có chứng minh được `normalized_value`?

    Đây là lý do module tồn tại được ở dạng kiểm được: không tin bản ghi, mà
    **cắt lại đúng đoạn văn bản đó và chạy lại đúng luật parse của kind**. Một
    span sai, một giá trị bị sửa sau khi trích, một fact chép nhầm — đều rơi ở
    đây.
    """
    if not (0 <= cand.source_start < cand.source_end <= len(problem_text)):
        return False
    doan = problem_text[cand.source_start : cand.source_end]
    if doan != cand.source_text:
        return False
    for _, rx, parse, nhom_gt, _ in _LUAT:
        m = rx.fullmatch(doan) if not nhom_gt else None
        try:
            if m is not None or rx.fullmatch(doan):
                if parse(doan) == cand.normalized_value:
                    return True
        except (ValueError, IndexError):
            continue
    return False


def gia_tri_kem_ky_tu(cand: LiteralCandidate) -> tuple[Any, ...]:
    """Giá trị của một literal, CỘNG các ký tự của nó nếu nó là chuỗi.

    VÌ SAO CẦN: `check_grounding` so từng nguyên tử vô hướng mà chương trình
    khai. Bài Stack khai đầu vào là **mảng ký tự** `['{','[','(',')',']','}']`,
    còn đề viết literal là **một chuỗi** `{[()]}`. Không có bậc này thì mọi bài
    quét chuỗi — Stack, palindrome, đếm nguyên âm — trượt P2 vì **hình dạng**
    chứ không vì dữ liệu.

    Nới rộng đúng chỗ và không hơn: mỗi ký tự trả về đều nằm tại một sub-span
    của chính span đã chứng minh, nên nó vẫn là dữ liệu của đề. Cùng tinh thần
    với bậc "phẳng hoá sâu" mà `_canon` đã áp cho phía chương trình.
    """
    ra = list(cand.normalized_value)
    for v in cand.normalized_value:
        if isinstance(v, str) and len(v) > 1:
            ra.extend(list(v))
    return tuple(ra)
