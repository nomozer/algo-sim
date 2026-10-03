# -*- coding: utf-8 -*-
"""`semantic_input_grounding_gate` — thay `check_input_sufficiency` (target-bound).

Cổng cũ gọi `requirements_for(target_id)`, nên nó vô nghĩa khi không có target.
Bảo vệ mà nó giữ thì thật: đề thiếu dữ liệu thì phải HỎI LẠI, không được để LLM
tự bịa.

CHUỖI PROVENANCE HAI ĐOẠN (spec §3.4) — hai đoạn có mức đảm bảo KHÁC HẲN nhau:

    Original input --P1--> RequestContract fact --P2--> SemanticProgram reference

P2 (ở file này) kiểm được TẤT ĐỊNH và mạnh: `source_fact_id` phải tồn tại, và
giá trị phải khớp mục ĐƯỢC CHỈ ĐÍCH DANH. Cố ý KHÔNG làm kiểu "tìm xem giá trị
này có xuất hiện đâu đó trong hợp đồng không" — khớp theo giá trị đơn thuần dễ
trùng ngẫu nhiên, và cho qua cả trường hợp khai sai nguồn.

P1 chỉ mạnh nếu fact có bằng chứng nguồn (`source_span`, vị trí có cấu trúc,
hoặc extractor tất định). Chưa có thì P1 là KHẲNG ĐỊNH của `analyze`, không phải
sự kiện kiểm được — xem `docs/evaluation/semantic-benchmark/P1_LIMITATION.md`.
Gate này là điều kiện CẦN, CHƯA ĐỦ.
"""
from __future__ import annotations

import re
from enum import Enum
from fractions import Fraction
from typing import Any, Callable

from pydantic import BaseModel, Field

from .contract import SemanticProgramSpec
# Tái dùng write-set của C₁a thay vì viết bản thứ hai: nó đã biết mọi dạng câu
# lệnh tạo ra một biến (`assign`, `pop`, `push`, `map_set`, biến chạy vòng lặp…)
# và hai bản rời nhau chắc chắn sẽ lệch khi thêm primitive.
from .coverage_gate import _producers
from .literal_extractor import extract_literals, gia_tri_khong_chung_minh_duoc
from .request_contract import RequestContract, norm_value
from .scale_normalization import bang_huu_ti, la_so_huu_ti
from .segment_relation import do_dai_trong_de, nhan_doan_truoc
from .shape_constraint import che_muc_tieu, khoang_muc_tieu
from .source_entities import chuan_hoa_ten, dinh_danh_thuc_the, la_ten_nguon, la_ten_suy_ra

#: HẠT KHỞI TẠO — giá trị quy ước để bắt đầu, KHÔNG mang thông tin của đề.
#:
#: Phân biệt này là bắt buộc, không phải tinh chỉnh: một biến đếm khai
#: `initial_value = 0` là biến LÀM VIỆC, không phải dữ liệu đề cho. Bắt nó khai
#: `source_fact_id` thì mọi biến tích luỹ đều phải bịa ra một nguồn — và cổng
#: lập tức mất nghĩa vì ai cũng phải nói dối để đi qua.
#:
#: Ngưỡng đặt ở "giá trị quy ước": không thể tuồn dữ liệu đề qua `0`/`""`/rỗng.
#: Giá trị khác — kể cả `1` hay `-1` — vẫn phải ghim nguồn.
_SEED_SCALARS = (0, 0.0, False, "")


def _is_seed(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, tuple, dict, set)) and not value:
        return True
    # `is` cho bool để `False` không nuốt `0` và ngược lại; `==` cho số/chuỗi.
    if isinstance(value, bool):
        return value is False
    return any(
        value == s and not isinstance(s, bool) for s in _SEED_SCALARS
    )


#: Kiểu được phép mang GIẢ THIẾT MÔ HÌNH HOÁ.
#:
#: Chỉ hai, và giới hạn này là toàn bộ sức mạnh của kênh: thứ duy nhất mà người
#: giải hình học được tự chọn là **hệ toạ độ**, tức vị trí của vài điểm gốc.
#: Mặt phẳng, đường thẳng, khối, và mọi ĐẠI LƯỢNG đều SUY RA từ các điểm ấy —
#: cho phép giả thiết trên chúng là mở đúng cửa để mô hình khai thẳng đáp án.
_KIEU_DUOC_GIA_THIET = frozenset({"point3", "vector3"})

#: Ba mã lỗi riêng, không gộp vào `INPUT_NOT_GROUNDED`. Gộp thì thông điệp nói
#: "không truy được về đề bài" cho một chương trình đang khai đáp án — sai bệnh,
#: và vòng sửa sẽ đi tìm `source_fact_id` thay vì bỏ giá trị bịa đi.
#: Kiểu mang TOẠ ĐỘ — tập được đếm cho `JUSTIFIED_GEOMETRY_LITERAL_RATE`.
#:
#: Rộng hơn `_KIEU_DUOC_GIA_THIET` một cách CÓ CHỦ ĐÍCH: `plane3`/`line3` khai
#: literal thì đó vẫn là một giá trị hình học phải biện minh, dù kênh giả thiết
#: không nhận chúng. Đếm hẹp hơn tập phải biện minh là tự cho mình điểm.
_KIEU_HINH_HOC = frozenset({"point3", "vector3", "plane3", "line3"})

#: BA LỚP BIỆN MINH cho một literal hình học (§6 của chỉ thị). Không có lớp nào
#: khớp ⇒ literal bị TỪ CHỐI — đó là bất biến, còn tỉ lệ chỉ là phép đếm.
#:
#:   A  tự do hệ trục      — người giải được chọn hệ toạ độ, đề không cho.
#:   B  ghim về nguồn      — mọi nguyên tử truy được về mục dữ kiện đã chỉ.
#:   C  hiện thực mô hình  — ghim về một dữ kiện QUAN HỆ (không có số để đối
#:                           chiếu); ràng buộc của nó do hậu điều kiện/oracle
#:                           tất định kiểm sau, không phải P2.
#:
#: Buộc thang KHÔNG phải giả thiết tuỳ tiện: nó đi lối B, vì mục dữ kiện đã
#: mang đúng con số mà server tự chốt.
LOP_BIEN_MINH = ("A", "B", "C")

ERR_GIA_THIET_SAI_KIEU = "MODEL_ASSUMPTION_TYPE_NOT_ALLOWED"
ERR_GIA_THIET_LA_DAP_AN = "MODEL_ASSUMPTION_IS_ANSWER"
ERR_GIA_THIET_KHONG_LY_DO = "MODEL_ASSUMPTION_NO_REASON"
#: RỬA NĂNG LỰC — thực thể tự bịa, khai bằng toạ độ thô, gắn nhãn giả thiết.
#:
#: Tách khỏi ba mã trên vì nó là một LỚP KHÁC: ba mã kia nói *"giả thiết này
#: khai sai cách"*, mã này nói *"thứ được khai không phải một giả thiết mô hình
#: hoá, nó là một KẾT LUẬN"*. Đo được ở `gm_10` (GENERALIZATION MATRIX).
ERR_RUA_NANG_LUC = "UNANCHORED_DERIVED_ASSUMPTION"
#: HỆ QUẢ KHÔNG CÓ NGƯỜI DỰNG — đề tự nói nhãn này là điểm phải dựng ra
#: (*"Gọi H là hình chiếu…"*), mô hình lại khai thẳng toạ độ của nó.
#:
#: Tách khỏi `ERR_RUA_NANG_LUC` vì cách sửa khác nhau, và thông điệp sửa mới là
#: thứ mô hình dùng được: ở đây cái tên hợp lệ, chỉ thiếu phép dựng — nói "không
#: có trong đề" sẽ là một lời buộc tội SAI, và một lượt repair đi sai hướng.
ERR_THIEU_NGUOI_DUNG = "DERIVED_ENTITY_WITHOUT_PRODUCER"

#: ─── BA MÃ NGUỒN (W12) ────────────────────────────────────────────────────
#:
#: `build_request_contract` đã đánh dấu giá trị `analyze` khai mà đề không có
#: (`provenance="claimed"`, `unproven_values`) "để cổng phía sau có cái mà từ
#: chối" — và không cổng nào đọc. Một độ dài bịa vì thế thành GIVEN và được
#: phục vụ (`ISSUE-ARCH-LLM-ROUTE-LENGTH-NOT-TEXT-GROUNDED`).
#:
#: Ba mã này nói *nguồn không chứng minh được*, không nói *chương trình viết
#: sai*: viết lại chương trình không thêm được dữ kiện vào đề, nên `pipeline`
#: không gửi chúng đi sửa.
ERR_GIVEN_KHONG_CO_TRONG_DE = "GIVEN_VALUE_NOT_IN_SOURCE"
ERR_SPAN_LECH_DE = "SOURCE_SPAN_MISMATCH"
ERR_BANG_CHUNG_MAU_THUAN = "SOURCE_EVIDENCE_CONFLICT"
#: Hợp đồng không mang đề (W14 5a). Trước đây đề rỗng NGẦM nghĩa là "chưa kiểm",
#: nên một hợp đồng sản phẩm mất đề đi lọt mọi kiểm tra nguồn.
ERR_THIEU_DE = "SOURCE_TEXT_MISSING"
#: W17 §15.2: giá trị chỉ có trong mệnh đề MỤC TIÊU (`Chứng minh rằng SA = 5`) — đề nêu nó như
#: điều phải chứng minh, không như dữ kiện.
ERR_CHI_TRONG_MUC_TIEU = "GIVEN_ONLY_IN_GOAL_CLAUSE"
MA_LOI_NGUON = frozenset({ERR_GIVEN_KHONG_CO_TRONG_DE, ERR_SPAN_LECH_DE,
                          ERR_BANG_CHUNG_MAU_THUAN, ERR_THIEU_DE, ERR_CHI_TRONG_MUC_TIEU})


class NguonDe(str, Enum):
    """Chính sách NGUỒN ĐỀ của một lời gọi — một THAM SỐ PYTHON, không gì khác.

    `CAN_DE` (mặc định): hợp đồng phải mang đề; đề rỗng ⇒ từ chối `SOURCE_TEXT_MISSING`.
    `FIXTURE_TIN_CAY`: người gọi KHAI TƯỜNG MINH đây là fixture đáng tin không có đề,
    được đi đường không kiểm nguồn cũ — và kết quả ghi `UNCHECKED_TRUSTED_FIXTURE`.
    Không bao giờ đọc từ payload/header HTTP, đầu ra mô hình hay cấu hình người dùng;
    tuyến sản phẩm không nhắc tới `FIXTURE_TIN_CAY` (khoá: `test_assumption_gate`).
    """
    CAN_DE = "CAN_DE"
    FIXTURE_TIN_CAY = "FIXTURE_TIN_CAY"

#: Đơn vị độ dài — tập ĐÓNG. Engine không đổi đơn vị; nó chỉ phát hiện hai nguồn
#: nói hai đơn vị khác nhau cho cùng một con số.
_DON_VI = r"(mm|cm|dm|km|m)"
_DON_VI_SAU = re.compile(rf"^\s*{_DON_VI}(?![A-Za-zÀ-ỹ])")
_SO_KEM_DON_VI = re.compile(rf"^\s*(-?\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?)\s*(?:{_DON_VI})?\s*$")
#: Một CON SỐ của câu đề: nguyên · thập phân (`.`/`,`) · `a/b` · căn (`2√3`,
#: `√3`, `3√2/2`). Không bắt đầu/kết thúc giữa một số khác — `2.5` không bao giờ
#: đọc thành `2`, `2√3` không thành `2` — nhưng đơn vị dính liền (`3cm`) vẫn là
#: một số. Extractor literal chỉ đọc nguyên và thập phân chấm, nên phân số của
#: đề (`DE = 3/2`, ca B03) từng bị kết tội "không có trong đề".
_SO_DE = re.compile(
    rf"(?<![\w.,/√])(?P<so>(?:\d+(?:[.,]\d+)?\s*)?√\s*\d+(?:\s*/\s*\d+)?"
    rf"|\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?)"
    rf"(?![.,]\d)(?={_DON_VI}(?![A-Za-zÀ-ỹ0-9])|[^\w/√]|$)")


def _phan_so(v: Any) -> Fraction | None:
    if isinstance(v, bool):
        return None
    try:
        return Fraction(str(v).replace(",", ".").replace(" ", ""))
    except (ValueError, ZeroDivisionError):
        return None


def _so_va_don_vi(v: Any) -> tuple[Fraction | None, str | None]:
    """`'5 cm'` → `(5, 'cm')`; `5` → `(5, None)`; văn xuôi → `(None, None)`."""
    if isinstance(v, bool):
        return None, None
    if isinstance(v, (int, float)):
        return _phan_so(v), None
    m = _SO_KEM_DON_VI.match(str(v))
    return (_phan_so(m.group(1)), m.group(2)) if m else (None, None)


def _cung_doan(ten_khai: str, doan) -> bool:
    """`ten_khai` (`AA_prime_length`) là độ dài của đúng đoạn `doan` của đề?"""
    if len(doan) != 2:
        return False
    a, z = (dinh_danh_thuc_the(str(p))[0] for p in sorted(doan))
    return ten_khai in (f"{a}{z}_length", f"{z}{a}_length")


def _ky_hieu_doan(ten_khai: str) -> str:
    """`AA_prime_length` → `AA′` — ký hiệu học sinh, không phải tên máy."""
    return ten_khai.removesuffix("_length").replace("_prime", "′")


def _bang_chung_do_dai(de: str, ten_khai: str, v: Fraction | str,
                       don_vi_muc: str | None) -> tuple[str | None, dict[str, Any] | None, str]:
    """Bằng chứng NGUỒN cho `ten_khai = v` — đọc CHỈ từ câu đề.

    `v` là số hữu tỉ, hoặc chuỗi của một giá trị căn (`"2√3"`) — căn so bằng
    chữ viết sau khi bỏ khoảng trắng, không quy đổi.

    → `(mã lỗi | None, bằng chứng | None, lý do)`. Ba câu hỏi, theo thứ tự:

    ① đề có ghi độ dài của CHÍNH đoạn này không — ghi mà khác `v` là mâu thuẫn;
    ② `v` có xuất hiện trong đề không — không thì không có trong nguồn;
    ③ mọi lần `v` xuất hiện đều gắn nhãn một ĐOẠN KHÁC — mâu thuẫn.

    Số đứng một mình (*"có cạnh bằng 4"*) là bằng chứng hợp lệ: đề nói về cạnh
    của cả khối, và chương trình tự chọn một cạnh đại diện — các cạnh khác phải
    được TÍNH từ nó, nên chúng không đi qua đây. Không so khớp mờ: chỉ con số
    của đề, và nhãn đoạn ngay trước một từ nối của `segment_relation._NOI_DO_DAI`.
    """
    return _bang_chung(de, lambda doan: _cung_doan(ten_khai, doan), v, don_vi_muc)


def bang_chung_doan(de: str, doan: tuple[str, str], v: Fraction | str) -> bool:
    """Đề chứng minh được ĐỘ DÀI của CHÍNH đoạn `doan` bằng `v`?

    `doan` là hai định danh thực thể (`("A", "A_prime")`) — bằng chứng gắn với
    THỰC THỂ, không với tên bộ nhớ. Cùng ba luật ①②③ và cùng thân với bằng chứng
    GIVEN (`_bang_chung_do_dai`), không bản sao thứ hai (W14).
    """
    dich = frozenset(doan)

    def la_doan(d) -> bool:
        return len(d) == 2 and frozenset(dinh_danh_thuc_the(str(p))[0] for p in d) == dich

    return _bang_chung(de, la_doan, v, None)[0] is None


def _bang_chung(de: str, la_doan: Callable[[Any], bool], v: Fraction | str,
                don_vi_muc: str | None) -> tuple[str | None, dict[str, Any] | None, str]:
    """Thân chung của `_bang_chung_do_dai` và `bang_chung_doan`; `la_doan(doan)`
    trả lời *"đoạn này của đề có phải đoạn đang xét không"*."""
    huu_ti = isinstance(v, Fraction)
    if huu_ti:
        for doan, gt in do_dai_trong_de(de).items():
            if la_doan(doan) and gt != v:
                return (ERR_BANG_CHUNG_MAU_THUAN, None,
                        f"đề ghi {''.join(sorted(doan))} = {gt}, không phải {v}")

    def bang(chu: str) -> bool:
        gon = re.sub(r"\s+", "", chu)
        return _phan_so(gon) == v if huu_ti else gon == re.sub(r"\s+", "", str(v))

    ung = [m for m in _SO_DE.finditer(de) if bang(m.group("so"))]
    if not ung:
        return ERR_GIVEN_KHONG_CO_TRONG_DE, None, f"đề không có con số {v}"

    def nhan_doan(m) -> tuple[str, str] | None:
        return nhan_doan_truoc(de[:m.start()])

    hop = [m for m in ung if nhan_doan(m) is None or la_doan(nhan_doan(m))]
    if not hop:
        return (ERR_BANG_CHUNG_MAU_THUAN, None,
                f"con số {v} trong đề là độ dài của đoạn khác")
    hop.sort(key=lambda m: nhan_doan(m) is None)  # nhãn đúng đoạn trước số trơn
    c = hop[0]
    d = _DON_VI_SAU.match(de[c.end():])
    don_vi_de = d.group(1) if d else None
    if don_vi_muc and don_vi_de and don_vi_muc != don_vi_de:
        return (ERR_BANG_CHUNG_MAU_THUAN, None,
                f"đề ghi đơn vị {don_vi_de}, dữ kiện khai {don_vi_muc}")
    return None, {"span": [c.start("so"), c.end("so")], "span_text": c.group("so"),
                  "unit": don_vi_de or don_vi_muc}, ""


class GroundingResult(BaseModel):
    ok: bool
    error_code: str | None = None
    unresolved: list[str] = Field(default_factory=list)
    #: Giả thiết mô hình hoá đã CHẤP NHẬN — để đếm được, không để trang trí.
    #:
    #: P2 không chứng minh được rằng `A=(0,0,0)` là một hệ toạ độ *hợp lệ cho
    #: đề này* (muốn thế phải kiểm mọi ràng buộc hình học của đề, mà hợp đồng
    #: chưa mã hoá chúng). Thứ nó làm được là giữ kênh HẸP và ĐẾM ĐƯỢC: bao
    #: nhiêu giá trị đã đi vào chương trình mà không có nguồn từ đề. Rủi ro còn
    #: lại được khai ở đây thay vì giấu đi.
    assumptions: list[str] = Field(default_factory=list)
    #: Trích dẫn `source_fact_id` KHÔNG giải được, hoặc chỉ giải được sau chuẩn
    #: hoá. Không gác cửa — chỉ QUAN TRẮC, để lượt đo sau đếm được mức lệch danh
    #: xưng giữa hai lượt LLM thay vì phải suy từ dấu vết. Rỗng ⇔ hai lượt gọi
    #: tên dữ kiện y hệt nhau.
    unresolved_citations: list[str] = Field(default_factory=list)
    #: `"tên|kiểu|lớp|lý do"` cho từng literal ĐÃ biện minh được, và `"tên|kiểu|
    #: lý do"` cho từng literal KHÔNG. Hai danh sách này là mẫu số và tử số của
    #: `JUSTIFIED_GEOMETRY_LITERAL_RATE`; đếm lại từ `unresolved` thì không tách
    #: được literal hình học khỏi mọi lời từ chối khác.
    justified_literals: list[str] = Field(default_factory=list)
    unjustified_literals: list[str] = Field(default_factory=list)
    #: BẰNG CHỨNG NGUỒN của mỗi literal GIVEN đã nhận (W12): loại nguồn · mục ·
    #: giá trị · đơn vị · span trong đề · trạng thái P1. Kiểm lại được bằng máy:
    #: `problem_text[span[0]:span[1]] == span_text`.
    given_evidence: list[dict[str, Any]] = Field(default_factory=list)
    #: Ký hiệu HỌC SINH của GIVEN bị từ chối vì nguồn (`AD`) — để lời từ chối
    #: nói được *thiếu cái gì* mà không lộ tên máy.
    refused_givens: list[str] = Field(default_factory=list)


def _canon(value: Any) -> tuple[Any, ...]:
    """Rút mọi NGUYÊN TỬ vô hướng của một giá trị, đã chuẩn hoá kiểu.

    Hai bậc, mỗi bậc vá một chỗ P2 từ chối oan chương trình đúng:

    1. `norm_value` — `analyze` trả chuỗi, IR khai số. So thẳng thì `"12"` khác
       `12` và không đề nào truy được về chính nó.
    2. **Phẳng hoá sâu** — cây khai `{"val": "A", "left": {...}}`, còn đề chỉ
       liệt kê được các nhãn A, B, C. So nguyên khối thì mọi đề cây trượt P2,
       và trượt vì hình dạng chứ không vì dữ liệu.

    Ranh giới mà bậc 2 giữ đúng: P2 hỏi **dữ liệu** có từ đề không. HÌNH DẠNG
    thì không — chọn cây hay mảng, lồng ra sao, là việc của chương trình. Khoá
    của dict là tên trường do IR đặt nên không tính là dữ liệu; chỉ giá trị mới
    tính. `None` bỏ qua: nó là chỗ trống của cấu trúc, không phải một giá trị đề
    cho.
    """
    ra: list[Any] = []

    def di(v: Any) -> None:
        if v is None:
            return
        if isinstance(v, dict):
            for x in v.values():
                di(x)
        elif isinstance(v, (list, tuple, set)):
            for x in v:
                di(x)
        else:
            ra.append(norm_value(v))

    di(value)
    return tuple(ra)


def _do_dai_bat_bien(decl, fact_ids: set[str], contract) -> bool:
    """`XY_length` khớp một BẤT BIẾN ĐỘ DÀI của hợp đồng.

    Bất biến do server dựng (`bat_bien_do_dai` đọc `SA = 5` từ CÂU ĐỀ) và hậu
    điều kiện kiểm nó trên hình đã dựng. Server neo nó vào mục có nhắc S, A — có
    khi là mục QUAN HỆ không mang số, vì analyze bỏ sót mục độ dài (đo ở
    `test_J_bis…`). Con số vẫn có trong đề. Kênh hẹp: đúng đoạn (tên), đúng giá
    trị, đúng mục được trích — lệch một thứ thì vẫn là "đề không cho".
    """
    khai = _canon(decl.initial_value)
    if decl.type != "float" or not decl.name.endswith("_length") or len(khai) != 1:
        return False
    for b in getattr(contract, "source_invariants", None) or ():
        if (b.kind != "segment_length" or b.source_fact_id not in fact_ids
                or len(b.points or ()) != 2):
            continue
        a, z = (dinh_danh_thuc_the(str(p))[0] for p in b.points)
        try:
            cung_so = Fraction(str(khai[0])) == Fraction(str(b.expected))
        except (ValueError, ZeroDivisionError):
            cung_so = False
        if cung_so and decl.name in (f"{a}{z}_length", f"{z}{a}_length"):
            return True
    return False


def _diem_phai_dung(contract) -> frozenset[str]:
    """Điểm mà ĐỀ xác định vị trí bằng một quan hệ chia đoạn ĐÃ GIẢI ĐƯỢC.

    Đọc lại tín hiệu `segment_relation` đã vật chất hoá thành `SourceInvariant`
    trên hợp đồng — **không** dựng bộ nhận diện thứ hai, và **không** nới
    `nhan_suy_ra` (hàm ấy dùng chung với nhiều wave khác).

    Chỉ lấy vế thứ ba `M` của bộ ba `(A, B, M)`: hai đầu mút là **điểm đầu
    vào**, chúng giữ nguyên quyền khai toạ độ và quyền đặt hệ trục.

    Chỉ lấy bất biến **đã giải được**. `segment_division_unresolved` nghĩa là
    hệ mới thấy đề *nói về* một phép chia mà chưa biết chia thế nào — chưa đủ
    để kết luận `M` bắt buộc phải dựng.
    """
    from .segment_relation import KIND as CHIA_DOAN

    ra: set[str] = set()
    for bt in getattr(contract, "source_invariants", ()) or ():
        if bt.kind == CHIA_DOAN and len(bt.points) == 3:
            ra |= set(chuan_hoa_ten(bt.points[2]))
    return frozenset(ra)


def _extract_declared_vertex_universe(contract: RequestContract) -> set[str]:
    """DECLARED_VERTEX_UNIVERSE — xây dựng hoàn toàn từ dữ liệu có cấu trúc.

    Bảo vệ Gate 2 / Addendum A1: Tuyệt đối không đọc contract.problem_text.
    """
    universe: set[str] = set()
    topo = getattr(contract, "solid_topology", None)
    if topo is not None:
        universe.update(getattr(topo, "base_cycle", ()) or ())
        universe.update(getattr(topo, "top_cycle", ()) or ())
        for u, v in getattr(topo, "correspondence", ()) or ():
            universe.add(u)
            universe.add(v)
        if getattr(topo, "apex", None):
            universe.add(topo.apex)
    for rel in getattr(contract, "geometric_relations", ()) or ():
        universe.update(rel.line)
        universe.update(rel.other_line)
        universe.update(rel.plane)
    for inv in getattr(contract, "source_invariants", ()) or ():
        universe.update(inv.points)
    for fact in getattr(contract, "input_facts", ()) or ():
        for v in fact.values:
            if isinstance(v, str) and len(v) == 1 and v.isupper():
                universe.add(v)
    expanded = set(universe)
    for v in universe:
        if "'" in v or "′" in v:
            expanded.add(v.replace("'", "_prime").replace("′", "_prime"))
    return expanded


def check_grounding(
    contract: RequestContract, spec: SemanticProgramSpec, *, nguon: NguonDe = NguonDe.CAN_DE
) -> GroundingResult:
    """P2 — mọi giá trị khởi tạo phải truy được về ĐÚNG mục dữ liệu đã chỉ.

    Đề rỗng chỉ được đi đường không kiểm nguồn khi người gọi khai `FIXTURE_TIN_CAY`.

    W17 §15.2: bằng chứng GIVEN đọc trên đề đã CHE mệnh đề mục tiêu (`che_muc_tieu`, cùng độ dài
    nên span giữ nguyên) — một giá trị chỉ có trong yêu cầu chứng minh không bao giờ là dữ kiện.
    Lần đọc thứ hai, trên đề gốc, chỉ PHÂN LOẠI lời từ chối: qua được ở đó ⇒ mọi giá trị thiếu
    đều nằm trong mệnh đề mục tiêu (`GIVEN_ONLY_IN_GOAL_CLAUSE`). Nó không bao giờ cấp phép.
    """
    if not (contract.problem_text or "").strip() and nguon is not NguonDe.FIXTURE_TIN_CAY:
        return GroundingResult(ok=False, error_code=ERR_THIEU_DE, unresolved=[
            "hợp đồng không mang đề bài — không có nguồn để đối chiếu dữ kiện"])
    goc = contract.problem_text or ""
    kq = _kiem_grounding(contract, spec, che_muc_tieu(goc))
    if (not kq.ok and kq.error_code in MA_LOI_NGUON and khoang_muc_tieu(goc)
            and _kiem_grounding(contract, spec, goc).ok):
        return kq.model_copy(update={"error_code": ERR_CHI_TRONG_MUC_TIEU})
    return kq


def _kiem_grounding(contract: RequestContract, spec: SemanticProgramSpec, de: str) -> GroundingResult:
    """Thân của `check_grounding`; `de` là văn bản BẰNG CHỨNG (tên thực thể vẫn đọc trên đề gốc)."""
    unresolved: list[str] = []
    gia_thiet: list[str] = []
    trich_dan_hong: list[str] = []
    #: Biến nào mang CÂU TRẢ LỜI. Không bao giờ được là giả thiết.
    dap_an = {ob.witness for ob in contract.obligations if ob.witness}
    ma_loi: str | None = None
    biet_minh: list[str] = []
    vo_can: list[str] = []

    def _ghi(decl, lop: str, ly_do: str) -> None:
        biet_minh.append(f"{decl.name}|{decl.type}|{lop}|{ly_do}")

    def _bac(decl, ly_do: str) -> None:
        """Từ chối MỘT literal. Ghi vào cả hai chỗ: `unresolved` gác cửa,
        `vo_can` để đếm — trộn hai vai vào một danh sách thì lần thêm nhánh
        sau chắc chắn có chỗ quên một trong hai."""
        unresolved.append(f"{decl.name}: {ly_do}")
        vo_can.append(f"{decl.name}|{decl.type}|{ly_do}")

    vertex_universe = _extract_declared_vertex_universe(contract)

    # ── BẰNG CHỨNG NGUỒN (W12) ─────────────────────────────────────────────
    # Rỗng ⇔ hợp đồng dựng không qua biên đóng băng ("unchecked", cùng quy ước
    # `InputFact.provenance`): giữ hành vi cũ. Tuyến sản phẩm luôn có đề.
    bang_chung: list[dict[str, Any]] = []
    tu_choi_nguon: list[str] = []
    # P1 tính LẠI từ đề, không tin cờ lưu trên mục: hợp đồng đông cứng từ trước
    # (replay, fixture lịch sử) mang kết quả của extractor cũ.
    ung_vien_de = extract_literals(de) if de else ()

    def _chua_chung_minh(fact) -> tuple[Any, ...]:
        return gia_tri_khong_chung_minh_duoc(fact.values, ung_vien_de, de) if de else ()

    def _bac_nguon(decl, ma: str, ly_do: str) -> None:
        nonlocal ma_loi
        ma_loi = ma_loi or ma
        _bac(decl, ly_do)
        if decl.name.endswith("_length"):
            tu_choi_nguon.append(_ky_hieu_doan(decl.name))
        elif decl.type == "point3":
            tu_choi_nguon.append(decl.name.replace("_prime", "′"))

    def _ghi_bang_chung(decl, fid: str, fact, gia_tri: Any, *, don_vi=None,
                        span=None, span_text=None, loai: str | None = None) -> None:
        bang_chung.append({
            "name": decl.name, "type": decl.type,
            "source_kind": loai or ("problem_text" if de else "unchecked"),
            "source_fact_id": fid,
            "provenance": ("source_invariant" if fact is None
                           else "unchecked" if not de
                           else "claimed" if _chua_chung_minh(fact) else "confirmed"),
            "value": str(gia_tri), "unit": don_vi, "span": span, "span_text": span_text,
        })

    def _kiem_span(fact) -> tuple[str, str] | None:
        """Span P1 của mục phải CẮT RA ĐÚNG chữ đã ghi, và nói đúng giá trị của mục."""
        if not de or fact.provenance not in ("confirmed", "extracted") or fact.source_start is None:
            return None
        s, e = fact.source_start, fact.source_end
        if not (e is not None and 0 <= s < e <= len(de) and de[s:e] == fact.source_text):
            return ERR_SPAN_LECH_DE, (f"span nguồn [{s}:{e}] của mục '{fact.fact_id}' không "
                                      "khớp câu chữ của đề")
        so = _phan_so(fact.source_text)
        if so is not None and not any(_so_va_don_vi(c)[0] == so for c in fact.values):
            return ERR_BANG_CHUNG_MAU_THUAN, (f"span nguồn ghi '{fact.source_text}', mục "
                                              f"'{fact.fact_id}' khai {list(fact.values)!r}")
        return None

    def _xet_do_dai(decl, fid: str, fact, ly_do: str) -> None:
        """GIVEN `XY_length`: nhận khi và chỉ khi câu đề chứng minh được nó."""
        goc = _canon(decl.initial_value)[0]
        v = _phan_so(goc)
        don_vi = next((u for c in (fact.values if fact is not None else ())
                       for so, u in [_so_va_don_vi(c)] if so == v and u), None)
        thang = bool(fact is not None and fact.scale_symbol) or any(
            b.kind == "segment_length" and b.scale_symbol and _cung_doan(decl.name, frozenset(b.points))
            for b in getattr(contract, "source_invariants", ()) or ())
        if not de or thang:
            # Không có đề để đối chiếu, hoặc con số do SERVER buộc thang (`AB = a`
            # ⇒ 1): nguồn là phép buộc thang đã chứng minh, không phải một chữ số.
            _ghi(decl, "B", ly_do)
            _ghi_bang_chung(decl, fid, fact, v if v is not None else decl.initial_value,
                            don_vi=don_vi, loai="scale_binding" if thang else None)
            return
        # Giá trị không hữu tỉ (căn) vẫn phải CÓ trong đề — bản đầu W12 cho nó
        # qua không kiểm, tức một độ dài bịa dạng `2√3` lọt nguyên vẹn.
        v = v if v is not None else str(goc).strip()
        ma, bc, vi_sao = _bang_chung_do_dai(de, decl.name, v, don_vi)
        if ma:
            _bac_nguon(decl, ma, f"{vi_sao} — không nhận làm dữ kiện đề cho")
            return
        _ghi(decl, "B", ly_do)
        _ghi_bang_chung(decl, fid, fact, v, don_vi=bc["unit"], span=bc["span"],
                        span_text=bc["span_text"])

    def _chi_tu_loi_khai(khai: tuple[Any, ...], fact) -> bool:
        """Có nguyên tử nào CHỈ khớp một giá trị P1 không chứng minh được?"""
        chua = _chua_chung_minh(fact)
        if not chua:
            return False
        da = tuple(c for c in fact.values if c not in chua)

        def khop(v, c) -> bool:
            so = _so_va_don_vi(c)[0]
            return v == c or bang_huu_ti(v, c) or (so is not None and _phan_so(v) == so)

        return any(any(khop(v, u) for u in chua) and not any(khop(v, c) for c in da)
                   for v in khai)

    # MỘT lớp được miễn `source_fact_id`, và nó kiểm được ở phía server chứ
    # không do chương trình tự khai.
    #
    # VÌ SAO CẦN. P2 hỏi "dữ liệu này ở đâu ra". Bản đầu trả lời câu đó bằng đúng
    # một cách — phải ghim về một mục của đề — nên nó chặn luôn cả thứ KHÔNG
    # phải dữ liệu đề: `result = "HỢP LỆ"` là nhãn đầu ra khởi tạo lạc quan, sẽ
    # bị chính chương trình ghi đè.
    #
    # RANH GIỚI ĐÃ CÂN NHẮC VÀ KHÔNG VƯỢT: không miễn theo kiểu "mọi nguyên tử
    # của giá trị đều đã có trong hợp đồng". Nghe hợp lý nhưng đó chính là
    # tìm-theo-giá-trị mà docstring của `test_grounding_gate.py` bác bỏ tường
    # minh — nó biến P2 từ kiểm THAM CHIẾU thành trùng khớp ngẫu nhiên, và làm
    # hỏng ba test âm cùng lúc (ghim nhầm mục vẫn qua). Hệ quả còn lại: bảng tra
    # HẰNG của thuật toán (`pairs`, tập nguyên âm, chữ số La Mã, vector hướng
    # BFS) vẫn cần một mục dữ liệu để ghim. Đó là câu hỏi năng lực ngữ nghĩa,
    # thuộc §12, KHÔNG phải chỗ để nới một cổng đã được thiết kế có chủ đích.
    computed = _producers(spec.statements)

    for decl in spec.memory_declarations:
        if getattr(decl, "provenance", None) == "LAYOUT_DERIVED":
            if decl.source_fact_id is not None or decl.model_assumption is not None:
                _bac(decl, "LAYOUT_DERIVED không được chứa source_fact_id hoặc model_assumption.")
                continue
            if _is_seed(decl.initial_value):
                continue
            if decl.name in dap_an:
                ma_loi = ma_loi or ERR_GIA_THIET_LA_DAP_AN
                _bac(decl, "là WITNESS của một nghĩa vụ — không được khai là LAYOUT_DERIVED.")
            elif decl.type not in _KIEU_DUOC_GIA_THIET:
                ma_loi = ma_loi or ERR_GIA_THIET_SAI_KIEU
                _bac(decl, f"kiểu '{decl.type}' không được mang LAYOUT_DERIVED (chỉ {sorted(_KIEU_DUOC_GIA_THIET)}).")
            elif decl.name not in vertex_universe:
                _bac(decl, f"điểm '{decl.name}' với LAYOUT_DERIVED không nằm trong DECLARED_VERTEX_UNIVERSE của hợp đồng.")
            else:
                _ghi(decl, "A", "layout_derived_vertex")
            continue

        if _is_seed(decl.initial_value):
            continue  # hạt khởi tạo, không mang thông tin của đề

        # CHƯƠNG TRÌNH TỰ TÍNH RA. Có câu lệnh ghi vào biến này ⇒ giá trị khởi
        # tạo không gánh thông tin, nó chỉ là điểm xuất phát. Câu hỏi "phép tính
        # ấy có thoả nghĩa vụ không" là của C₁/C₂, không phải của P2.
        if decl.name in computed:
            continue

        # ─── ⑦ ĐIỂM DẪN XUẤT PHẢI ĐƯỢC DỰNG, KHÔNG ĐƯỢC KHAI THẲNG ─────────
        #
        # `DERIVED_POINT_CONSTRUCTION_ENFORCEMENT`, 2026-09-07.
        #
        # Chốt ⑥ ngay dưới hỏi đúng câu này rồi, nhưng nó đọc `nhan_suy_ra` —
        # bộ nhận diện chỉ khớp *"gọi/lấy X là …"* và *"X là trung điểm|hình
        # chiếu|…"*. Đề viết *"Điểm P nằm trên đoạn EF **sao cho** FP = 4·PE"*
        # thì không lối nào khớp, nên ⑥ im lặng. Đo được
        # (`FRAME_ORIGIN_PROVENANCE_AFFORDANCE`, phản ví dụ ⓐ): chương trình
        # khai thẳng toạ độ `P`, **bỏ câu lệnh dựng**, còn đúng một câu lệnh,
        # và vẫn `served` với đáp số ĐÚNG. Đáp số đúng vì bất biến
        # `segment_division` xác nhận vị trí — thứ mất là **BƯỚC DỰNG**, tức
        # đúng thứ đề tài hứa cho học sinh.
        #
        # ⚠️ Chốt ⑥ chỉ chạy trong nhánh `model_assumption`; lỗ này đi được cả
        # nhánh `source_fact_id` (đo: cả hai đều `served`). Nên chốt ⑦ đặt ở
        # ĐÂY — sau khi đã biết chương trình KHÔNG tính ra vật này, trước khi
        # rẽ theo kênh xuất xứ.
        #
        # ─── TÍN HIỆU DÙNG LẠI, KHÔNG DỰNG BỘ NHẬN DIỆN THỨ HAI ───────────
        #
        # `segment_relation` đã nhận ra bộ ba `(A, B, M)` và **giải được** tỉ
        # lệ; kết quả ấy đã nằm sẵn trên hợp đồng dưới dạng `SourceInvariant`.
        # Chốt này chỉ đọc lại nó. Nới `nhan_suy_ra` thay vì đọc tín hiệu có
        # sẵn sẽ đổi hành vi của mọi wave khác dùng chung hàm ấy.
        #
        # ─── RANH GIỚI, và nó hẹp có chủ đích ────────────────────────────
        #
        # · CHỈ bất biến **đã giải được** (`segment_division`). Bản chưa giải
        #   (`segment_division_unresolved`) nghĩa là hệ mới thấy đề *nói về*
        #   một phép chia chứ chưa biết chia thế nào — chưa đủ để kết luận
        #   `M` bắt buộc phải dựng.
        # · CHỈ điểm `M` (vế thứ ba). Hai đầu mút `A`, `B` là **điểm đầu vào**:
        #   chúng được quyền khai toạ độ, và quyền đặt hệ trục vẫn nguyên.
        # · CHỈ khi khai báo THẬT SỰ mang giá trị. Khai báo trống rồi dựng
        #   bằng câu lệnh đã bị chốt `computed` ở trên bỏ qua.
        if (decl.initial_value is not None
                and _diem_phai_dung(contract) & chuan_hoa_ten(decl.name)):
            ma_loi = ma_loi or ERR_THIEU_NGUOI_DUNG
            _bac(decl,
                 "được đề xác định bằng một QUAN HỆ CHIA ĐOẠN, nên vị trí của "
                 "nó là HỆ QUẢ phải dựng ra, không phải dữ kiện để khai. Hãy "
                 "dựng bằng `divide_segment(<đầu này>, <đầu kia>, <tỉ lệ>)` — "
                 "engine sẽ tính toạ độ và ghi bước dựng vào trace.")
            continue

        fid = decl.source_fact_id

        # ── GIẢ THIẾT MÔ HÌNH HOÁ (Wave 2, 2026-08-24) ──────────────────────
        #
        # VÌ SAO CẦN, ĐO ĐƯỢC Ở PHASE 5: 5/10 bài hình học chết ở đúng dòng bên
        # dưới. Đề hình học **không cho toạ độ** — prompt bảo mô hình tự đặt hệ
        # trục, còn cổng hỏi *"anh lấy dữ liệu này ở đâu ra?"*. Không có đường
        # nào thoả cả hai, nên mọi bài đều trượt, kể cả bài làm đúng.
        #
        # Ở Tin học, toạ độ là DỮ LIỆU ĐỀ CHO. Ở hình học, hệ toạ độ là LỰA
        # CHỌN MÔ HÌNH HOÁ. Đó là hai thứ khác nhau, và cổng cũ chỉ biết một.
        #
        # RANH GIỚI — vì sao đây KHÔNG phải "nới cổng cho dễ thở":
        #
        #   ① `source_fact_id` VẪN THẮNG. Ghim được về đề thì đi đường cũ,
        #      nghiêm ngặt như trước; giả thiết không được dùng để né kiểm.
        #   ② Chỉ `point3`/`vector3`. Đại lượng (`float`) không bao giờ là giả
        #      thiết — đó là chỗ đáp án sống.
        #   ③ KHÔNG BAO GIỜ cho biến mang câu trả lời. Đây là chốt cứng nhất:
        #      khai đáp án rồi gắn nhãn "giả thiết" là đúng thứ R0 cấm.
        #   ④ Phải có LÝ DO viết ra. Không kiểm được nội dung lý do, nhưng bắt
        #      viết ra thì biến một lựa chọn ngầm thành một lựa chọn KHAI BÁO.
        #
        # GIỚI HẠN CÒN LẠI, khai thẳng: cổng KHÔNG kiểm được `A=(0,0,0)` có
        # dựng nên đúng hình mà đề mô tả không (hợp đồng chưa mã hoá ràng buộc
        # "ABCD là hình vuông"). Nó giữ kênh hẹp và ĐẾM được, không hơn.
        if decl.model_assumption is not None and not fid:
            ly_do = str(decl.model_assumption).strip()
            if decl.name in dap_an:
                ma_loi = ma_loi or ERR_GIA_THIET_LA_DAP_AN
                _bac(decl,
                     "là WITNESS của một nghĩa vụ — câu trả lời không bao giờ "
                     "được khai làm giả thiết. Hãy để một câu lệnh tính ra nó.")
            elif decl.type not in _KIEU_DUOC_GIA_THIET:
                ma_loi = ma_loi or ERR_GIA_THIET_SAI_KIEU
                _bac(decl,
                     f"kiểu '{decl.type}' không được mang giả thiết mô hình hoá "
                     f"(chỉ {sorted(_KIEU_DUOC_GIA_THIET)}). Đối tượng này phải "
                     "được DỰNG từ các điểm đã chọn.")
            elif not ly_do:
                ma_loi = ma_loi or ERR_GIA_THIET_KHONG_LY_DO
                _bac(decl, "giả thiết mô hình hoá phải nêu LÝ DO chọn.")
            elif not la_ten_nguon(decl.name, contract.problem_text):
                # ⑤ CHỐT CHỐNG RỬA NĂNG LỰC — thêm sau `gm_10`.
                #
                # Bốn phép kiểm trên hỏi *giả thiết này khai đúng cách chưa*.
                # Không phép nào hỏi *thứ được khai có trong đề không*. Nên một
                # điểm mô hình TỰ BỊA — `P_opposite = [2,2,2]`, "điểm đối diện
                # trong hình hộp bao quanh" — đi lọt, rồi `midpoint` biến nó
                # thành tâm mặt cầu và `distance` cho ra đáp số ĐÚNG cho một
                # khái niệm runtime KHÔNG có.
                #
                # `model_assumption` chỉ được nói về CÁCH ĐẶT một vật đề đã
                # nêu, không được nói *"tôi suy ra còn có vật này nữa"*. Vật
                # suy ra thì phải DỰNG bằng một phép của IR — lúc ấy kernel
                # tính toạ độ, và điều được khẳng định trở thành điều kiểm
                # chứng được.
                ma_loi = ma_loi or ERR_RUA_NANG_LUC
                _bac(decl,
                     "không có trong đề bài. `model_assumption` chỉ nói về "
                     "CÁCH ĐẶT một đối tượng đề đã nêu; một điểm suy ra phải "
                     "được DỰNG (trung điểm, giao, hình chiếu…) để engine tính "
                     "toạ độ, không được khai thẳng toạ độ.")
            elif la_ten_suy_ra(decl.name, contract.problem_text):
                # ⑥ HỆ QUẢ KHÔNG CÓ NGƯỜI DỰNG — nửa còn lại của chốt ⑤.
                #
                # Chốt ⑤ hỏi *"tên này có trong đề không"*, nên nó hụt đúng ca
                # đề TẶNG tên cho điểm phụ: *"Gọi H là hình chiếu của S lên
                # (ABCD)"*. `H` có trong đề ⇒ ⑤ cho qua ⇒ mô hình khai
                # `H = [0,0,0]` bằng toạ độ nó tự tính. Vẫn là giấu một phép
                # dựng vào một con số, chỉ khác chỗ cái tên hợp lệ.
                #
                # Phân biệt được vì chính ĐỀ đã nói: một nhãn được giới thiệu
                # bằng mệnh đề định nghĩa là HỆ QUẢ của hình, không phải dữ
                # kiện của hình. Hệ quả thì kernel phải tính, không thì học
                # sinh xem một "mô phỏng" trong đó bước dựng quan trọng nhất đã
                # bị làm sẵn ngoài màn hình.
                ma_loi = ma_loi or ERR_THIEU_NGUOI_DUNG
                _bac(decl,
                     "được ĐỀ giới thiệu như một điểm phải dựng ra, nên không "
                     "được khai bằng toạ độ. Hãy dựng nó bằng một câu lệnh "
                     "(midpoint, project_onto, intersect…) để engine tính.")
            else:
                gia_thiet.append(f"{decl.name}: {ly_do}")
                _ghi(decl, "A", ly_do)
            continue

        if not fid:
            _bac(decl,
                 "có initial_value nhưng thiếu source_fact_id — không truy "
                 "được về đề bài")
            continue

        fact, cach = contract.fact_noi_long(fid)
        if fact is None and _do_dai_bat_bien(decl, {fid}, contract):
            # Mục chỉ sống trong bất biến độ dài (hợp đồng dựng không qua
            # analyze): bất biến CHÍNH LÀ bản ghi của hợp đồng cho mục ấy —
            # nhưng con số vẫn phải có trong câu đề (W12).
            _xet_do_dai(decl, fid, None, f"ghim về bất biến độ dài '{fid}'")
            continue
        if fact is None:
            # ── TRÍCH DẪN KHÔNG GIẢI ĐƯỢC (Wave 3, 2026-08-25) ─────────────
            #
            # ĐO ĐƯỢC Ở PHASE 5 LƯỢT 2: 6/10 bài chết đúng ở đây, và chúng chết
            # vì mô hình làm THÊM chứ không phải làm thiếu. `geo_09` khai
            # `B point3 [1,0,0]` kèm `model_assumption` hợp lệ, rồi gắn thêm
            # `source_fact_id='canh_day'` để nói toạ độ ấy bắt nguồn từ dữ kiện
            # nào. Id đó không có trong hợp đồng (hai lượt LLM không dùng chung
            # không gian tên), và luật Wave 2 — "`source_fact_id` VẪN THẮNG khi
            # khai cả hai" — biến một trích dẫn hỏng thành lỗi chí mạng, giết
            # một chương trình gần như trùng khít bản viết tay làm chuẩn.
            #
            # RANH GIỚI, và nó hẹp có chủ đích: hạ cấp CHỈ KHI khai báo đã tự
            # đứng vững bằng kênh giả thiết — tức đã qua ba khoá độc lập (chỉ
            # `point3`/`vector3` · KHÔNG BAO GIỜ là witness của một nghĩa vụ ·
            # phải có lý do viết ra). Khi ấy trích dẫn hỏng là **thông tin
            # thừa sai**, không phải **dữ liệu vô căn cứ**.
            #
            # Không có `model_assumption` ⇒ chết y như cũ. Một `float` giữ
            # `2/3` với `source_fact_id` bịa vẫn không đi qua được — đó là
            # đường tuồn đáp án, và nó vẫn đóng.
            if decl.model_assumption and str(decl.model_assumption).strip():
                if decl.name in dap_an:
                    ma_loi = ma_loi or ERR_GIA_THIET_LA_DAP_AN
                    _bac(decl,
                         "là WITNESS của một nghĩa vụ — không được khai làm "
                         "giả thiết, kể cả khi có source_fact_id.")
                elif decl.type not in _KIEU_DUOC_GIA_THIET:
                    ma_loi = ma_loi or ERR_GIA_THIET_SAI_KIEU
                    _bac(decl,
                         f"kiểu '{decl.type}' không được mang giả thiết mô "
                         f"hình hoá (chỉ {sorted(_KIEU_DUOC_GIA_THIET)}).")
                elif not la_ten_nguon(decl.name, contract.problem_text):
                    # ⑤ CHỐT CHỐNG RỬA NĂNG LỰC — bản của nhánh HẠ CẤP.
                    #
                    # Nhánh này nhận một khai báo có `source_fact_id` KHÔNG giải
                    # được rồi cho nó đi tiếp bằng kênh giả thiết. Nếu chốt ⑤
                    # chỉ đứng ở nhánh "không có fid", thì thêm đúng một trường
                    # `source_fact_id` bịa là lách qua được — cổng chống rửa
                    # năng lực sẽ có một cửa sau rộng bằng chính nó.
                    #
                    # Nên hai nhánh phải kiểm CÙNG bốn điều. Chép luật là mầm
                    # trôi, nhưng ở đây điều kiện hạ cấp khác nhau nên gộp thân
                    # hàm sẽ phải truyền cờ — dựng thẳng và khoá bằng test
                    # `test_gan_them_source_fact_id_bia_KHONG_lach_duoc`.
                    ma_loi = ma_loi or ERR_RUA_NANG_LUC
                    _bac(decl,
                         "không có trong đề bài. Gắn `source_fact_id` vào một "
                         "thực thể tự bịa không làm nó có nguồn — một điểm suy "
                         "ra phải được DỰNG để engine tính toạ độ.")
                else:
                    ly_do = str(decl.model_assumption).strip()
                    gia_thiet.append(f"{decl.name}: {ly_do}")
                    _ghi(decl, "A", ly_do)
                    trich_dan_hong.append(
                        f"{decl.name}: source_fact_id '{fid}' không giải được — "
                        "nhận theo kênh giả thiết mô hình hoá"
                    )
                continue
            _bac(decl,
                 f"source_fact_id '{fid}' không có trong RequestContract")
            continue
        if cach != "exact":
            trich_dan_hong.append(
                f"{decl.name}: '{fid}' khớp '{fact.fact_id}' sau chuẩn hoá"
            )

        khai = _canon(decl.initial_value)
        cho = fact.values

        # ── GIẢ THIẾT TOẠ ĐỘ (Wave 4, 2026-08-25) ──────────────────────────
        #
        # ĐO ĐƯỢC Ở PHASE 5.5: 5/10 bài chết ở đúng phép so bên dưới, và chúng
        # chết vì phép so hỏi SAI CÂU.
        #
        #   B: giá trị [0, 0] không có trong mục 'canh_day' (cạnh đáy)
        #   C: giá trị [1, 1, 0] không có trong mục 'abcd_hinh_vuong'
        #
        # Mô hình khai `B = (1,0,0)` rồi ghim về `canh_day` (values = `1`). P2
        # phẳng hoá toạ độ thành các nguyên tử `1, 0, 0` rồi đòi TỪNG CÁI có
        # trong mục. `1` có; `0` không — nên chương trình chết.
        #
        # Nhưng `0` ở đây KHÔNG phải dữ liệu lấy từ đề. Nó là **số không cấu
        # trúc của hệ trục**: "không dịch theo y, không dịch theo z". Bắt nó
        # truy về một mục dữ liệu là hỏi một câu không có câu trả lời đúng.
        #
        # Và `C = (1,1,0)` ghim về `abcd_hinh_vuong` — một fact QUAN HỆ,
        # `values` rỗng. Mô hình đang nói *"vị trí C suy ra từ ABCD là hình
        # vuông"*. Lập luận đúng, mà phép kiểm theo giá trị không diễn đạt được.
        #
        # ─── LUẬT MỚI, và nó HẸP ────────────────────────────────────────────
        #
        # Chỉ áp cho `point3`/`vector3` CÓ `model_assumption` — tức đã qua ba
        # khoá của kênh giả thiết (kiểu · không-là-witness · có lý do). Khi ấy
        # `source_fact_id` là **chỉ dẫn xuất xứ**, không phải hợp đồng giá trị:
        #
        #   · nguyên tử `0` bỏ qua — số không cấu trúc của hệ trục;
        #   · fact QUAN HỆ (`values` rỗng) chấp nhận, ghi vào quan trắc;
        #   · mọi nguyên tử KHÁC 0 vẫn phải có trong mục được ghim.
        #
        # Nên toạ độ bịa `H = (5,7,9)` ghim về `canh_day` (values = `1`) VẪN
        # chết: `{5,7,9}` không có cái nào trong `{1}`.
        #
        # RỦI RO CÒN LẠI, khai thẳng: một điểm KHÔNG phải witness, toạ độ sai,
        # ghim về một fact quan hệ thì đi qua được. Đó là lỗi ĐÚNG-SAI của hình,
        # và nó thuộc oracle/C₂ — không phải câu hỏi xuất xứ mà P2 trả lời.
        # ĐIỀU KIỆN dựa trên KIỂU, không dựa trên việc model có nhớ khai
        # `model_assumption` hay không.
        #
        # Bản đầu đòi cả hai, và đo lại trên Phase 5.5 cho thấy nó chỉ gỡ được
        # `geo_09` — bốn bài kia (`geo_05/06/07/10`) vẫn chết vì model gắn
        # `source_fact_id` mà QUÊN gắn `model_assumption` cho cùng một loại khai
        # báo. Nhưng ở miền này **đề không bao giờ cho toạ độ**: một `point3` có
        # toạ độ thì đó là hệ trục do người giải chọn, dù bản khai có nhớ nói ra
        # hay không. Bắt phép kiểm phụ thuộc vào trí nhớ của model là đo trí nhớ
        # chứ không đo tính có căn cứ.
        #
        # R0 vẫn giữ bằng một khoá TƯỜNG MINH thay chỗ: witness của bất kỳ nghĩa
        # vụ nào KHÔNG được đi lối này. Đáp án không bao giờ là một hệ trục.
        la_toa_do = (
            decl.type in _KIEU_DUOC_GIA_THIET and decl.name not in dap_an
        )
        if la_toa_do:
            # FACT QUAN HỆ = fact KHÔNG CÓ SỐ NÀO, chứ không phải fact rỗng.
            #
            # Bản đầu kiểm `not cho` và trượt ngay ở lượt thử: `abcd_hinh_vuong`
            # có `values = ("ABCD là hình vuông",)` — một mệnh đề, không phải
            # chỗ trống. Nguyên tử của một toạ độ là SỐ; một mục không chứa số
            # nào thì không thể cấp phép cũng không thể bác bỏ nó, nên đòi khớp
            # ở đó là một phép kiểm không có câu trả lời đúng.
            # `la_so_huu_ti`, không phải `isinstance(int|float)`: sau khi
            # chuẩn hoá thang, mục dữ kiện giữ `'4/5'` — một CON SỐ viết chính
            # xác. Hỏi bằng `isinstance` thì nó đọc ra "fact quan hệ", và mọi
            # toạ độ ghim vào đó đi qua mà không ai đối chiếu gì. Đúng thứ cửa
            # sau mà nhánh này được viết ra để KHÔNG mở.
            co_so = any(la_so_huu_ti(v) for v in cho)
            # W12: một mục mang CON SỐ mà đề không ghi (`S(0;0;6)` chỉ có trong
            # lời khai `analyze`) không phải fact quan hệ — nó là dữ kiện bịa,
            # và toạ độ ghim vào nó không có căn cứ. Mệnh đề không chứa chữ số
            # (kể cả bị diễn đạt lại) vẫn đi nhánh quan hệ như trước.
            so_bia = [c for c in _chua_chung_minh(fact) if re.search(r"\d", str(c))]
            if not co_so and so_bia:
                _bac_nguon(decl, ERR_GIVEN_KHONG_CO_TRONG_DE,
                           f"mục '{fid}' khai {so_bia!r} nhưng đề không ghi — "
                           "toạ độ không nhận làm dữ kiện đề cho")
                continue
            if not co_so:
                ly_do = str(decl.model_assumption or "").strip()
                if ly_do:
                    gia_thiet.append(f"{decl.name}: {ly_do}")
                _ghi(decl, "C",
                     f"hiện thực mô hình theo dữ kiện quan hệ '{fid}' "
                     f"({fact.label}) — ràng buộc do hậu điều kiện kiểm")
                trich_dan_hong.append(
                    f"{decl.name}: ghim về '{fid}' ({fact.label}) — fact QUAN HỆ "
                    "không có giá trị để đối chiếu, nhận theo giả thiết toạ độ"
                )
                continue
            khai = tuple(v for v in khai if v != 0 or isinstance(v, bool))

        # `v not in cho` là phép so THEO GIÁ TRỊ, và nó mù với cách viết: mục
        # đã chuẩn hoá thang giữ `'4/5'` (chính xác), còn IR chỉ viết được
        # `0.8` vì JSON không có kiểu phân số. Không có `bang_huu_ti` thì phép
        # chuẩn hoá thang tự bắn vào chân mình.
        thua = [
            v for v in khai
            if v not in cho and not any(bang_huu_ti(v, c) for c in cho)
        ]
        if thua and not la_toa_do and _do_dai_bat_bien(decl, {fid, fact.fact_id}, contract):
            _xet_do_dai(decl, fid, fact, f"ghim về '{fid}' ({fact.label}) — khớp bất biến độ dài")
        elif thua:
            # Với TOẠ ĐỘ, nói thêm đúng một điều: có hai kênh, và đây là kênh
            # sai. Không phải gợi ý cách giải — một toạ độ SUY RA từ ràng buộc
            # (chân đường cao, đỉnh của một tam giác vuông) không bằng số nào
            # trong mục độ dài, nên ghim vào mục ấy là khai sai XUẤT XỨ chứ
            # chưa chắc đã sai hình. Không nói ra thì vòng sửa đi chỉnh toạ độ
            # cho khớp một con số — tức là sửa đúng thứ đang đúng.
            them = (" — toạ độ suy ra từ ràng buộc thì ghim về dữ kiện QUAN HỆ "
                    "mô tả ràng buộc ấy" if la_toa_do else "")
            _bac(decl,
                 f"giá trị {thua!r} không có trong mục '{fid}' ({fact.label}) "
                 f"— đề không cho những giá trị này{them}")
        elif (loi_span := _kiem_span(fact)) is not None:
            _bac_nguon(decl, *loi_span)
        elif decl.type == "float" and decl.name.endswith("_length") and len(khai) == 1:
            _xet_do_dai(decl, fid, fact, f"ghim về '{fid}' ({fact.label})")
        elif _chi_tu_loi_khai(khai, fact):
            _bac_nguon(decl, ERR_GIVEN_KHONG_CO_TRONG_DE,
                       f"giá trị {list(khai)!r} chỉ có trong lời khai của mục '{fid}', "
                       "đề không ghi — không nhận làm dữ kiện đề cho")
        else:
            _ghi(decl, "B", f"ghim về '{fid}' ({fact.label})")
            _ghi_bang_chung(decl, fid, fact, "|".join(map(str, khai)),
                            span=[fact.source_start, fact.source_end]
                            if fact.source_start is not None else None,
                            span_text=fact.source_text)

    if unresolved:
        return GroundingResult(
            ok=False,
            error_code=ma_loi or "INPUT_NOT_GROUNDED",
            unresolved=unresolved,
            assumptions=gia_thiet,
            unresolved_citations=trich_dan_hong,
            justified_literals=biet_minh,
            unjustified_literals=vo_can,
            given_evidence=bang_chung,
            refused_givens=tu_choi_nguon,
        )
    return GroundingResult(
        ok=True, assumptions=gia_thiet, unresolved_citations=trich_dan_hong,
        justified_literals=biet_minh, unjustified_literals=vo_can,
        given_evidence=bang_chung,
    )


def ti_le_literal_hinh_hoc(kq: GroundingResult) -> tuple[int, int]:
    """`(số literal hình học ĐÃ biện minh, tổng literal hình học)`.

    Tách khỏi `check_grounding` để bộ đo gọi được mà không phải bóc chuỗi —
    và để định nghĩa "literal hình học" nằm ở ĐÚNG MỘT chỗ.
    """
    def dem(ds: list[str]) -> int:
        return sum(1 for d in ds if d.split("|")[1] in _KIEU_HINH_HOC)

    dat = dem(kq.justified_literals)
    return dat, dat + dem(kq.unjustified_literals)
