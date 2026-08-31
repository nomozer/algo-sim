# -*- coding: utf-8 -*-
"""RequestContract — server ĐÓNG BĂNG nghĩa vụ do `analyze` khai.

`stage_semantic_program` KHÔNG có quyền khai lại hay sửa nghĩa vụ. Đây là R0 áp
cho chính khâu chấm điểm: tiêu chuẩn chấm được cố định TRƯỚC khi chương trình
được viết ra, nên chương trình không thể nới tiêu chuẩn cho vừa nó.

GIỚI HẠN PHẢI ĐỌC KÈM (spec §5.2): đây là **separation of responsibility**,
KHÔNG phải **independent oracle**. Nó chặn được việc chương trình tự sửa đề cho
vừa mình. Nó KHÔNG chặn được việc cùng một model hiểu sai đề một cách nhất quán
ở cả hai lượt — nghĩa vụ sai và chương trình khớp với nghĩa vụ sai đó vẫn qua
hết mọi cổng. Oracle độc lập thật nằm ở đối chứng module (§3.7) và held-out
benchmark (§7.1).

`frozen=True` không phải trang trí: nó là chỗ luật "không được khai lại" trở
thành bất khả thay vì lời dặn.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from .obligations import Obligation
# Một chiều: `scale_normalization` không import ngược file này (nó nhận hợp
# đồng theo giao diện), nên khai kiểu thật ở đây không tạo vòng.
from .scale_normalization import ScaleBinding, SourceInvariant


def norm_value(v: Any) -> Any:
    """Chuẩn hoá một giá trị để so khớp được giữa HAI NGUỒN KHÁC KIỂU.

    `analyze` trả dữ liệu đề cho dưới dạng chuỗi (schema JSON của Gemini không
    có kiểu "số hoặc chuỗi"), còn IR khai `initial_value` đúng kiểu — `12` chứ
    không phải `"12"`. So thẳng thì P2 trượt sạch dù chương trình hoàn toàn
    đúng, và trượt CÂM: mã lỗi sẽ nói "đề không cho những giá trị này".

    Chỉ nới đúng một bậc: chuỗi trông như số thì thành số. Không đoán gì thêm —
    `"true"` vẫn là chuỗi, vì `bool` trong `int` là cái bẫy sẵn có của Python.
    """
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip()
        try:
            return int(s)
        except ValueError:
            pass
        try:
            return float(s)
        except ValueError:
            pass
        return s
    return v


class InputFact(BaseModel):
    """Một mục dữ liệu đề cho, đã được `analyze` trích và server đóng băng.

    `fact_id` là thứ mà literal trong IR phải THAM CHIẾU tới — ghim *cái nào*,
    không phải *có tồn tại đâu đó* (chuỗi provenance P2, spec §3.4).
    """

    model_config = ConfigDict(frozen=True)

    fact_id: str
    label: str
    values: tuple[Any, ...] = ()

    # ── P1 — BẰNG CHỨNG NGUỒN ────────────────────────────────────────────────
    #
    # Bốn trạng thái, và sự khác nhau giữa chúng là toàn bộ giá trị của P1:
    #
    #   "unchecked" — không có `problem_text` để đối chiếu (đường gọi cũ, test
    #                 dựng contract bằng tay). KHÔNG kết luận gì; giữ nguyên
    #                 hành vi trước vNext.
    #   "extracted" — `analyze` bỏ trống ô giá trị, extractor tất định tìm thấy
    #                 literal trong đề và server lấy nó. Đây là ca đã quan sát
    #                 được: `values=null` trong khi đề ghi rõ `{[()]}`.
    #   "confirmed" — `analyze` có khai, và MỌI giá trị khai đều truy được về
    #                 một span trong đề.
    #   "claimed"   — `analyze` khai giá trị mà đề không có bằng chứng. Đây là
    #                 thứ P1 sinh ra để bắt: model tự thêm dữ liệu rồi chương
    #                 trình khớp với dữ liệu tự thêm đó, và mọi cổng phía sau
    #                 đều xanh vì chúng chỉ so chương trình với hợp đồng.
    provenance: str = "unchecked"
    source_start: int | None = None
    source_end: int | None = None
    source_text: str | None = None
    #: Đúng những giá trị KHÔNG chứng minh được. Rỗng ⇔ không có gì để trách.
    unproven_values: tuple[Any, ...] = ()

    # ── CHUẨN HOÁ THANG (`scale_normalization.py`) ──────────────────────────
    #
    # Chuỗi xuất xứ phải đọc ngược được ba chặng, nếu không phép chuẩn hoá tự
    # nó thành một chỗ dữ liệu bốc hơi:
    #
    #     values (đã chuẩn hoá) → original_values (nguyên văn) → scale_symbol
    #
    # `fact_id` KHÔNG đổi: nó là thứ IR ghim vào, và đổi nó thì mọi trích dẫn
    # của chương trình trượt hàng loạt vì một lý do chẳng liên quan gì tới đề.
    #: Ký hiệu thang đã buộc về 1. `None` ⇔ mục này chưa từng bị viết lại.
    scale_symbol: str | None = None
    #: `values` TRƯỚC khi chuẩn hoá — `('4a/5',)`. Rỗng ⇔ không có phép viết lại.
    original_values: tuple[Any, ...] = ()


class RequestContract(BaseModel):
    """Hợp đồng yêu cầu — bất biến sau khi server đóng băng."""

    model_config = ConfigDict(frozen=True)

    obligations: tuple[Obligation, ...] = ()
    input_facts: tuple[InputFact, ...] = ()
    #: Phép buộc thang do SERVER quyết, không do LLM. `None` ⇔ không chuẩn hoá.
    scale_binding: ScaleBinding | None = None
    #: RÀNG BUỘC DỮ KIỆN NGUỒN có cấu trúc, do SERVER phát từ chính câu văn của
    #: đề. `NormalizedSourceInvariantGate` kiểm chúng trên trạng thái cuối, và
    #: kiểm **bất kể** chương trình có gắn `source_fact_id` hay không.
    source_invariants: tuple[SourceInvariant, ...] = ()
    #: ĐỀ BÀI NGUYÊN VĂN — thẩm quyền cuối cùng của câu *"thứ này có trong đề
    #: không"*.
    #:
    #: Trước bản này `build_request_contract` nhận `problem_text`, dùng nó để
    #: trích span rồi VỨT. Hệ quả đo được ở GENERALIZATION MATRIX (`gm_10`):
    #: mô hình khai một điểm `P_opposite` chưa từng có trong đề, gắn
    #: `model_assumption`, rồi lấy trung điểm để ra tâm mặt cầu — một khái niệm
    #: runtime KHÔNG có. Không cổng nào chặn được, vì không cổng nào còn giữ đề
    #: để đối chiếu.
    #:
    #: Rỗng = "chưa kiểm được", KHÔNG phải "không có nguồn" — cùng quy ước với
    #: `InputFact.provenance="unchecked"`. Đường gọi cũ (test dựng hợp đồng
    #: bằng tay) giữ nguyên hành vi.
    problem_text: str = ""

    def fact(self, fact_id: str) -> InputFact | None:
        for f in self.input_facts:
            if f.fact_id == fact_id:
                return f
        return None

    def fact_noi_long(self, fact_id: str) -> tuple["InputFact | None", str]:
        """Giải một `source_fact_id`, nới ĐÚNG một bậc TẤT ĐỊNH.

        Trả `(fact, cách_khớp)` với `cách_khớp ∈ {exact, chuan_hoa, khong_khop}`.

        ─── VÌ SAO CẦN, ĐO ĐƯỢC Ở PHASE 5 LƯỢT 2 (2026-08-25) ──────────────

        6/10 bài chết vì `source_fact_id` không giải được: mô hình trích dẫn
        `canh_day`, `abcd_hinh_vuong`, `sa_vuong_goc_day` — những id **hợp lý**
        mà lượt `analyze` không đặt. Hai lượt LLM không dùng chung không gian tên.

        ─── VÌ SAO CHỈ NỚI TỚI ĐÂY, KHÔNG KHỚP NGỮ NGHĨA ───────────────────

        Có đề nghị khớp theo `semantic_type`/`entities`/`attributes`. Không làm,
        và lý do là cơ chế chứ không phải khẩu vị: **cả hai phía của phép khớp
        ấy đều do cùng một model đặt tên**, nên nó là model tự đối chiếu nhãn
        của chính nó — đúng chế độ hỏng mà `RequestContract` sinh ra để chặn
        (xem docstring module). Cụ thể hơn: một biến `float` giữ `2/3` sẽ khớp
        một fact `semantic_type: volume`, tức mở thẳng đường tuồn đáp án.

        Bậc `chuan_hoa` ở đây **không có phán đoán ngữ nghĩa nào**: bỏ dấu tiếng
        Việt, thường hoá, gộp `-_ `. `CANH-DAY` ≡ `canh_day` ≡ `cạnh đáy`. Máy
        kiểm được, người đọc lại được, không ai phải tin một model nào cả.
        """
        f = self.fact(fact_id)
        if f is not None:
            return f, "exact"
        khoa = _chuan_hoa_id(fact_id)
        for g in self.input_facts:
            if _chuan_hoa_id(g.fact_id) == khoa:
                return g, "chuan_hoa"
        return None, "khong_khop"


#: Dấu tiếng Việt → chữ không dấu. Bảng tay, không phụ thuộc `unicodedata`
#: normalize form nào — id do LLM đặt có thể ở NFC hoặc NFD, và `str.translate`
#: trên cả hai dạng thì phải xử lý cả tổ hợp lẫn ký tự dựng sẵn.
_DAU = str.maketrans(
    "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
    "ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ",
    "a" * 17 + "e" * 11 + "i" * 5 + "o" * 17 + "u" * 11 + "y" * 5 + "d"
    + "A" * 17 + "E" * 11 + "I" * 5 + "O" * 17 + "U" * 11 + "Y" * 5 + "D",
)


def _chuan_hoa_id(s: str) -> str:
    """Dạng chuẩn của một định danh — TẤT ĐỊNH, không đoán nghĩa."""
    import unicodedata

    s = unicodedata.normalize("NFC", str(s)).translate(_DAU).lower()
    return "".join(c for c in s if c.isalnum())
