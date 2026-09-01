# -*- coding: utf-8 -*-
"""Thẻ văn phạm IR — hợp đồng giao diện gửi kèm đề bài, SINH TỪ PYDANTIC.

VÌ SAO TỒN TẠI (2026-08-22, sau lượt chạy pilot thứ hai với API thật): schema
IR **không diễn đạt được** bằng dialect structured-output của Gemini. Nó có 37
`$defs`, 421 `$ref`, 40 `oneOf` kèm `discriminator`, và **đệ quy** — nội suy
`$ref` nổ ~10× mỗi bậc (296 KB ở độ sâu 2, 3 MB ở độ sâu 3), mà độ sâu 2 còn
quá nông cho một `for_range` có `if` bên trong. Đây là giới hạn thiết kế, không
phải một trường viết sai.

Hệ quả đo được: bỏ schema thì mô hình bọc đầu ra trong khoá `semantic_program`,
gọi `variables` thay `memory_declarations`, dùng `type: "number"` thay `int`, và
bịa `element_element_type` — 38/40 case trượt thẩm định. Prompt cố ý KHÔNG nhắc
tên trường vì nó tin schema cưỡng chế chúng; giả định đó không còn đúng.

Thẻ này mang đúng thứ `responseSchema` từng mang, và **không** phải nhồi prompt:

- Nó sinh từ chính `contract.py`, nên KHÔNG THỂ trôi khỏi hợp đồng. Thêm một
  statement kind là thẻ tự có, không ai phải nhớ sửa.
- Nó ghép vào **user message**, không vào `skills/*.md`, nên ngân sách prompt
  tĩnh vẫn đo đúng thứ nó sinh ra để đo (luật viết tay do người thêm).
- Tiền lệ có sẵn trong kho: `catalog_text()` và `manifest_capability_summary()`
  cũng là tóm tắt dẫn xuất ghép vào user message của `classify`.

Nó KHÔNG thay validator: `validate_semantic_program` vẫn là thứ bảo đảm, thẻ chỉ
làm tăng tỉ lệ trúng.
"""
from __future__ import annotations

import re
import typing

from pydantic import BaseModel

from . import contract as C
from .measure_contract import mo_ta_phep_do


#: Chỉ những thứ này mới là GIÁ TRỊ literal. Không siết thì `typing.get_args`
#: của một union phân biệt (Annotated[…, Tag(…)]) cũng lọt vào và thẻ in ra cả
#: đường dẫn module — đo được 19.759 byte thay vì ~2 KB.
_VO_HUONG = (str, int, float, bool, type(None))


def _gia_tri_dong(annotation) -> tuple[str, ...]:
    """Các giá trị của một `Literal`, kể cả khi bọc trong `Optional`."""
    def _tu(args) -> tuple[str, ...]:
        if args and all(isinstance(a, _VO_HUONG) for a in args):
            return tuple(str(a) for a in args if a is not None)
        return ()

    args = typing.get_args(annotation)
    truc_tiep = _tu(args)
    if truc_tiep:
        return truc_tiep
    for a in args:  # Optional[Literal[...]]
        con = _tu(typing.get_args(a))
        if con:
            return con
    return ()


def _tag(annotation) -> frozenset[str]:
    """Tập `kind` của một union phân biệt; rỗng nếu không phải union như thế.

    Nhận HAI hình dạng, và phải nhận cả hai: alias gốc là
    `Annotated[Union[...], Discriminator]`, nhưng Pydantic **bóc lớp ngoài** khi
    trả `model_fields[...].annotation`, để lại `Union[...]` trần. Chỉ xử một
    dạng thì hàm im lặng trả rỗng ở đúng chỗ nó được gọi.
    """
    for ung_vien in (annotation, *typing.get_args(annotation)[:1]):
        ra = frozenset(
            a.__metadata__[0].tag for a in typing.get_args(ung_vien)
            if hasattr(a, "__metadata__") and a.__metadata__
            and hasattr(a.__metadata__[0], "tag"))
        if ra:
            return ra
    return frozenset()


def _bo_annotated(a):
    """`Annotated[str, …]` ⇒ `str`. Pydantic bóc lớp này ở trường TRẦN nhưng
    KHÔNG bóc được khi nó nằm trong một union."""
    return typing.get_args(a)[0] if typing.get_origin(a) is not None and \
        getattr(a, "__metadata__", None) else a


def _la_ten(annotation) -> bool:
    """`str` hay `Optional[str]`, kể cả khi bọc `Annotated`.

    ⚠️ Phép so cũ là `annotation == typing.Optional[str]`, và nó IM LẶNG thành
    sai khi `MeasureExpr.wrt` đổi sang `Optional[GeometryName]`: Pydantic bóc
    `Annotated` ở trường trần nhưng không bóc được bên trong union, nên `wrt`
    mất sạch nhãn kiểu trên thẻ — một trường không nhãn thì mô hình tự đoán,
    và đó đúng là cơ chế đã đẻ ra mọi lỗi mà `_kieu` này tồn tại để chặn.
    """
    if _bo_annotated(annotation) is str:
        return True
    args = {_bo_annotated(x) for x in typing.get_args(annotation)}
    return bool(args) and args <= {str, type(None)}


def _kieu(annotation) -> str:
    """Nhãn KIỂU gọn cho một trường — thứ tên trường không nói được.

    Đo được ở lượt pilot 3: mô hình điền cả một object biểu thức vào
    `index.container`, `map_get.container`, `write_index.container` — trong khi
    chúng là `str`, tức TÊN BIẾN. 11+ case trượt vì đúng nhầm lẫn này. Thẻ liệt
    kê tên trường mà không nói kiểu thì mô hình phải tự đoán.
    """
    if _la_ten(annotation):
        return "tên"
    txt = repr(annotation)
    if txt.startswith("list["):
        # `list[Model]` KHÔNG phải khối lệnh trừ khi Model LÀ câu lệnh.
        # `memory_declarations: list[MemoryDeclaration]` từng được giới thiệu
        # với mô hình là "khối lệnh" — cùng lớp nhãn sai ba khối chú thích dưới
        # đây kể, và là cái duy nhất còn sót lại ở mức GỐC của hợp đồng.
        con = typing.get_args(annotation)
        if con and isinstance(con[0], type) and issubclass(con[0], BaseModel):
            return "danh sách"
        # `list[…]` KHÔNG phải lúc nào cũng là thân vòng lặp. Trước bản này thẻ
        # gọi MỌI list là "khối lệnh", nên `construct_plane.through: list[str]`
        # — ba TÊN ĐIỂM — được giới thiệu với mô hình như một thân câu lệnh.
        #
        # Đo được ở lượt live 2026-08-25 trên đề học sinh gửi thật: cả BA lượt
        # thử đều điền `{"kind": "literal", "value": ["A","B","C"]}` vào
        # `through`, `vertices` và `faces`. Mô hình không bịa — nó đang cố nhét
        # một giá trị vào chỗ thẻ bảo là khối lệnh, và bọc nó lại là cách duy
        # nhất hợp lý. Nhãn sai của TA đẻ ra lỗi của NÓ.
        ben_trong = typing.get_args(annotation)
        if ben_trong and ben_trong[0] is str:
            return "danh sách TÊN"
        if ben_trong and repr(ben_trong[0]).startswith("list["):
            return "danh sách các danh sách"
        # `list[Any]` KHÔNG phải khối lệnh. `declare_point.at` là TOẠ ĐỘ, và
        # thẻ từng giới thiệu nó với mô hình là "khối lệnh" — đúng lớp lỗi mà
        # khối chú thích trên vừa kể, chỉ khác một nhánh. Nhãn sai của TA đẻ ra
        # lỗi của NÓ, và lần này nhãn sai nằm ngay trong bản vá cho lần trước.
        if ben_trong and ben_trong[0] is typing.Any:
            return "danh sách giá trị"
        return "khối lệnh"
    if "Cond" in txt:
        return "điều kiện"
    if "Expr" in txt or "Stmt" in txt:
        # `PointExpr` là TẬP CON THẬT SỰ của `ValueExpr` — chỉ năm phép dựng
        # sinh ra một điểm. Gọi nó là "biểu thức" như mọi chỗ khác là nói với mô
        # hình rằng chỗ ấy nhận bất kỳ biểu thức nào, đúng cái hiểu đã đẻ ra
        # `construct_point C = arith(B + D)` ở hai vòng đo độc lập.
        #
        # So bằng TẬP TAG, không so tên: đổi tên alias thì nhãn vẫn đúng.
        if _tag(annotation) and _tag(annotation) < _tag(C.ValueExpr):
            return "phép dựng ĐIỂM"
        return "biểu thức"
    # Trường nhận JSON THÔ (`Any`, hoặc union của các kiểu nền). Phải nói rõ,
    # nếu không mô hình cho rằng chỗ nào cũng điền được biểu thức: lượt kiểm
    # sau bản sửa danh xưng cho thấy nó viết
    # `initial_value: {"kind": "literal", "value": 1}` thay vì `1`, và P2 báo
    # "giá trị ['literal'] không có trong mục đề cho".
    args = typing.get_args(annotation)
    nen = (int, str, bool, float, list, dict, type(None))
    if annotation is typing.Any or (args and all(a in nen for a in args)):
        return "giá trị thô, KHÔNG phải biểu thức"
    return ""


def _dai_co_dinh(f) -> int | None:
    """Độ dài BẮT BUỘC của một trường danh sách, hoặc `None`.

    Đọc từ metadata Pydantic chứ không từ tên trường: dẫn xuất thì thêm một
    trường toạ độ mới tự có nhãn đúng, chép tay thì không.
    """
    lo = hi = None
    for m in getattr(f, "metadata", ()) or ():
        lo = getattr(m, "min_length", lo)
        hi = getattr(m, "max_length", hi)
    return lo if lo is not None and lo == hi else None


#: Trường VĂN XUÔI — người đọc, không phải máy. Nhãn `tên` (mọi `str` đều nhận)
#: nói sai về chúng, và chỗ sai ấy tốn OUTPUT TOKEN: mô hình không biết ta muốn
#: một câu hay một đoạn, nên nó viết một đoạn. Một lượt live 2026-08-31 mất cả
#: chương trình vì `description` dài 1200 ký tự.
#:
#: Viết tay vì Pydantic không mang khái niệm "văn xuôi" — bù lại
#: `test_measure_contract.py` khoá mọi khoá ở đây phải là trường CÓ THẬT.
#: Nhãn phải ngắn hơn chính thứ nó tả — ngân sách thẻ là 4200 byte và `label`
#: xuất hiện ở tám câu lệnh, nên mỗi ký tự ở đây nhân lên tám lần.
_VAN_XUOI = {
    "title": "1 dòng",
    "description": "1 câu",
    "pedagogical_intent": "1 câu",
    "label": "nhãn",
}


def _o_ten(kind: str | None) -> dict[str, tuple[tuple[str, ...], bool]]:
    """Ô toán hạng TÊN của một `kind`, DẪN từ bảng bộ nâng dùng.

    Một thẩm quyền, hai người đọc: `hoisting` quyết cái gì được nâng, thẻ này
    quyết mô hình ĐỌC THẤY gì. Tách hai bảng ra là bảo đảm chúng sẽ lệch — và
    lệch ở đây nghĩa là ta dạy mô hình một hợp đồng khác hợp đồng ta cưỡng chế.
    """
    if not kind:
        return {}
    from .hoisting import O_TEN

    return O_TEN.get(kind, {})


def _truong(model: type[BaseModel], bo: frozenset[str] = frozenset(),
            kind: str | None = None) -> str:
    """Tên trường, `?` = tuỳ chọn, và LIỆT KÊ GIÁ TRỊ cho trường enum.

    Giá trị enum là bắt buộc phải có: lượt kiểm sau khi thêm thẻ cho thấy mô
    hình dựng đúng cấu trúc lồng nhưng viết `op: "add"` thay vì `"+"`. Tên
    trường nói được *chỗ nào điền*, không nói được *điền gì*.
    """
    o_ten = _o_ten(kind)
    ra = []
    for ten, f in model.model_fields.items():
        if ten == "kind" or ten in bo:
            continue
        nhan = ten if f.is_required() else ten + "?"
        if ten in _VAN_XUOI:
            ra.append(f"{nhan}:{_VAN_XUOI[ten]}")
            continue
        if ten in o_ten:
            # ─── KIỂU CẤU TRÚC CHO Ô TÊN: `tên<point3>`, KHÔNG PHẢI `tên` ───
            #
            # Nhãn `tên` nói *chỗ này điền một chuỗi* và im lặng về hai điều mô
            # hình thật sự cần: chuỗi ấy phải trỏ MỘT VẬT ĐÃ CÓ, và vật ấy phải
            # đúng kiểu. `FRESH_TRANSLATION_COMPOSITION_PROBE` đo được cái giá:
            # 5 lần mô hình lồng thẳng `vector_from_points` vào `translate.
            # vector` — nó biết cần một vectơ, không biết cần một CÁI TÊN.
            #
            # Kiểu lấy từ `hoisting.O_TEN`, tức đúng bảng bộ nâng cưỡng chế.
            kieu, la_ds = o_ten[ten]
            t = f"tên<{'|'.join(kieu)}>"
            if la_ds:
                n = _dai_co_dinh(f)
                t = f"[{t}, …]" + (f" (đúng {n})" if n else "")
            ra.append(f"{nhan}:{t}")
            continue
        gt = _gia_tri_dong(f.annotation)
        # Bỏ qua enum quá dài (vd MemoryType) — chúng đã có mục riêng.
        if gt and len(gt) <= 8:
            nhan += "(" + "|".join(gt) + ")"
        else:
            k = _kieu(f.annotation)
            # Danh sách CỐ ĐỊNH ba phần tử: nói thẳng kích thước, vì mô hình
            # không đoán được nó từ một nhãn chung và điền thiếu/thừa một thành
            # phần là một lượt sửa tiêu cho không.
            #
            # ⚠️ NHƯNG PHẢI HỎI KIỂU PHẦN TỬ, KHÔNG CHỈ HỎI ĐỘ DÀI. Bản trước
            # dán "[x,y,z] số hoặc chuỗi phân số" cho MỌI list dài đúng 3, và
            # `construct_plane.through` — `list[str]`, **tên ba điểm** — rơi
            # trúng: nhãn đúng ("danh sách TÊN") vừa tính xong đã bị đè.
            #
            # Đây là lớp lỗi hai khối chú thích trong `_kieu` vừa kể, lần thứ
            # ba: nhãn sai của TA đẻ ra lỗi của NÓ. Và lần này nặng hơn hai lần
            # trước — `construct_plane` có mặt trong gần như mọi chương trình
            # hình học, còn thứ nó dạy mô hình viết vào đó là TOẠ ĐỘ THÔ, tức
            # đúng hành vi cổng trung thực năng lực vừa dựng để chặn.
            if k and _dai_co_dinh(f) == 3:
                ben_trong = typing.get_args(f.annotation)
                if not (ben_trong and ben_trong[0] is str):
                    k = "[x,y,z] số hoặc chuỗi phân số"
                else:
                    k += " (đúng 3)"
            if k:
                nhan += ":" + k
        ra.append(nhan)
    return " ".join(ra)


def _cac_kind(alias) -> list[tuple[str, type[BaseModel]]]:
    """Rút (nhãn kind, model) từ một union phân biệt của contract."""
    ra: list[tuple[str, type[BaseModel]]] = []
    for arg in typing.get_args(typing.get_args(alias)[0]):
        model = typing.get_args(arg)[0] if typing.get_args(arg) else arg
        if not (isinstance(model, type) and issubclass(model, BaseModel)):
            continue
        k = model.model_fields.get("kind")
        nhan = typing.get_args(k.annotation)[0] if k else model.__name__
        ra.append((nhan, model))
    return sorted(ra)


def _khoi(ten: str, alias) -> str:
    dong = [f"  {nhan}: {_truong(m, kind=nhan)}".rstrip()
            for nhan, m in _cac_kind(alias)]
    return f"{ten}\n" + "\n".join(dong)


#: IR mà một chương trình HÌNH HỌC dùng tới. Ba nguồn, hai dẫn xuất một khai:
#:
#:   · phép dựng   ← `_CHU_KY` (bảng chữ ký hình học)      DẪN XUẤT
#:   · câu lệnh dựng ← `_TOAN_HANG_LENH`                    DẪN XUẤT
#:   · lõi dùng chung — khai tay, danh sách dưới đây
#:
#: VÌ SAO THU HẸP (§4 — giảm không gian chọn của mô hình): thẻ đầy đủ liệt kê
#: cả `enqueue`, `map_set`, `write_index`, `neighbors`, `swap`… — toàn bộ IR
#: Tin học. Với một đề hình học chúng không chỉ là byte thừa: chúng là **lựa
#: chọn sai đang được mời gọi**, cùng đúng cơ chế đã đo được ở `analyze` khi
#: enum nghĩa vụ mời cả 9 nghĩa vụ Tin học và mô hình chọn `derived_sequence`
#: cho một câu hỏi `point_on_line` (xem `domain_profile`).
#:
#: `visual_bindings` cũng biến mất, và đó KHÔNG phải cắt bớt: cảnh 3D dựng tất
#: định từ bộ nhớ (`build_scene3d`), nên chương trình hình học **không khai
#: binding và đúng khi không khai** — `learner_surface._tren_canh_3d` đã ghi
#: điều đó thành luật. Thẻ vẫn đòi là đòi mô hình sinh ra thứ server tự suy —
#: token output tiêu cho một trường sẽ bị bỏ qua.
_LOI_DUNG_CHUNG_LENH = ("assign", "declare_point")
_LOI_DUNG_CHUNG_BIEU_THUC = ("literal", "var", "arith", "measure", "unary")


def _loc(alias, giu: frozenset[str]):
    """Bản `_cac_kind` đã lọc — giữ đúng thứ miền dùng tới."""
    return [(n, m) for n, m in _cac_kind(alias) if n in giu]


def _khoi_loc(ten: str, alias, giu: frozenset[str]) -> str:
    dong = [f"  {nhan}: {_truong(m, kind=nhan)}".rstrip()
            for nhan, m in _loc(alias, giu)]
    return f"{ten}\n" + "\n".join(dong)


def _tap_hinh_hoc() -> tuple[frozenset[str], frozenset[str]]:
    """Tập câu lệnh + biểu thức mà một chương trình hình học dùng tới.

    ⚠️ DẪN TỪ `_KIEU_DUNG`, KHÔNG từ `_TOAN_HANG_LENH`.

    `_TOAN_HANG_LENH` liệt kê câu lệnh dựng có toán hạng là TÊN, và
    `construct_point` **cố ý không có mặt** ở đó — toán hạng của nó nằm trong
    `expr`, do `_CHU_KY` lo. Dẫn thẻ từ bảng ấy nên thẻ hình học chưa bao giờ
    liệt kê `construct_point`.

    Hệ quả đo được ở `CLEAN_BASELINE_V1`: mô hình dựng mọi điểm phụ bằng
    `assign M = midpoint(...)` — không phải vì nó chọn nhầm giữa hai lối, mà
    vì **thẻ chỉ bày ra một lối**, và lối ấy chết ở runtime. 4/6 ca mất trắng
    vì một cái tên vắng mặt trong một danh sách.

    `_KIEU_DUNG` là bảng *"câu lệnh nào SINH RA vật gì"* — đúng câu hỏi cần
    hỏi ở đây, và nó có đủ sáu `construct_*`.
    """
    from .ir_static_check import _CHU_KY, _KIEU_DUNG

    lenh = frozenset(_KIEU_DUNG) | frozenset(_LOI_DUNG_CHUNG_LENH)
    bt = frozenset(_CHU_KY) | frozenset(_LOI_DUNG_CHUNG_BIEU_THUC)
    return lenh, bt


def grammar_card(domain: str | None = None) -> str:
    """Hợp đồng IR ở dạng gọn, tiếng Việt, dẫn xuất 100% từ `contract.py`.

    `domain="hinh_hoc"` trả bản THU HẸP: chỉ IR hình học, không `visual_bindings`.
    Mặc định `None` giữ bản đầy đủ — tức **hành vi Tin học nguyên vẹn**, cùng
    khuôn fail-safe với `detect_domain` (cửa duy nhất mở là cửa sang hình học).
    """
    if domain == "hinh_hoc":
        return _the_hinh_hoc()
    return _the_day_du()


def manh_hop_dong(loi: str, domain: str | None = None, *, toi_da: int = 12) -> str:
    """Chỉ những DÒNG của thẻ mà thông điệp lỗi thật sự nói tới.

    ─── VÌ SAO KHÔNG GỬI LẠI CẢ THẺ (§8) ──────────────────────────────────

    Lượt sửa cũ gửi nguyên `base` — đề bài + dữ kiện + nghĩa vụ + **toàn bộ thẻ
    văn phạm**, rồi thêm chương trình hỏng và lời từ chối. Với đề hình học đó là
    ~8 KB input cho một lượt mà mô hình chỉ cần sửa một trường.

    Nặng hơn chuyện tiền: cả thẻ gửi lại là cả thẻ được cân nhắc lại. Bản ghi
    từng lượt của bốn ca probe cho thấy lượt sửa vấp một lỗi **KHÁC** lượt đầu —
    mô hình viết lại chương trình thay vì sửa nó. Thu hẹp ngữ cảnh xuống đúng
    phần liên quan là cách nói *"chỗ này, không phải chỗ khác"* bằng cấu trúc
    thay vì bằng lời dặn.

    ─── CÁCH CHỌN: KHỚP ĐỊNH DANH, KHÔNG ĐOÁN NGỮ NGHĨA ───────────────────

    Lấy mọi định danh trong lời từ chối (`angle_cos`, `construct_plane`,
    `through`…) rồi giữ dòng nào của thẻ chứa một trong số đó. Dẫn xuất hoàn
    toàn: thêm một primitive thì mảnh của nó tự có, không ai phải nhớ.

    Không khớp được gì ⇒ trả rỗng, và nơi gọi gửi lời từ chối trần. Đó đúng hơn
    là đoán bừa một mảnh: một mảnh SAI dẫn mô hình đi sửa nhầm chỗ.
    """
    the = grammar_card(domain)
    dinh_danh = {t for t in re.findall(r"[a-z][a-z0-9_]{3,}", loi or "")
                 if t not in _TU_CHUNG}
    if not dinh_danh:
        return ""
    giu = [d for d in the.splitlines()
           if any(t in d for t in dinh_danh) and d.strip()]
    return "\n".join(giu[:toi_da])


#: Từ tiếng Anh/kỹ thuật xuất hiện trong LỜI TỪ CHỐI mà không phải tên trường.
#: Thiếu bộ lọc này thì `validation`, `input`, `value` khớp gần hết thẻ và mảnh
#: trở lại thành cả thẻ — tức mất đúng thứ hàm trên tồn tại để làm.
_TU_CHUNG = frozenset({
    "value", "input", "should", "validation", "errors", "error", "type",
    "found", "using", "match", "expected", "tags", "valid", "input_value",
    "value_error", "union_tag_invalid", "name", "kind", "none", "null",
})


def _the_hinh_hoc() -> str:
    lenh, bt = _tap_hinh_hoc()
    bat_buoc = [n for n, f in C.SemanticProgramSpec.model_fields.items()
                if f.is_required()]
    kieu_hh = [k for k in typing.get_args(C.MemoryType)
               if k in ("point3", "vector3", "line3", "plane3", "polygon3",
                        "solid", "section", "float", "bool")]
    # Bỏ hẳn khỏi thẻ thay vì nhắc "đừng dùng": một trường được LIỆT KÊ rồi bị
    # cấm bằng lời vẫn là một trường mô hình thấy và cân nhắc. `element_type`,
    # `key_type`, `val_type` chỉ có nghĩa với array/map — không kiểu hình học
    # nào nhận chúng.
    return (
        "HỢP ĐỒNG JSON — dùng ĐÚNG các tên dưới đây, không đặt tên khác, không "
        "bọc thêm một tầng nào ở ngoài.\n\n"
        "Đối tượng gốc: "
        f"{_truong(C.SemanticProgramSpec, frozenset({'visual_bindings'}))}\n"
        f"  BẮT BUỘC phải có đủ: {', '.join(bat_buoc)} — thiếu một cái là hỏng.\n"
        "  `?` = tuỳ chọn. KHÔNG có khoá `semantic_program`, `variables` hay "
        "`program` ở ngoài cùng.\n"
        "  Cảnh 3D dựng TỰ ĐỘNG từ các phép dựng của bạn — không khai gì thêm "
        "để hiển thị.\n\n"
        "memory_declarations[]: "
        + _truong(C.MemoryDeclaration,
                  frozenset({"element_type", "key_type", "val_type"})) + "\n"
        f"  type nhận đúng một trong: {' '.join(kieu_hh)}\n\n"
        + _khoi_loc("statements[] — mỗi phần tử có `kind` và các trường:",
                    C.SemanticStatement, lenh)
        + "\n\n"
        + _khoi_loc("biểu thức giá trị — cũng có `kind`:", C.ValueExpr, bt)
        + "\n"
        + "  kiểu toán hạng của `measure` — chọn theo NGỮ NGHĨA, "
          "không theo chữ trong đề:\n"
        + mo_ta_phep_do()
        + "\n"
    )


def _the_day_du() -> str:
    bat_buoc = [n for n, f in C.SemanticProgramSpec.model_fields.items()
                if f.is_required()]
    spec = _truong(C.SemanticProgramSpec)
    khai = _truong(C.MemoryDeclaration)
    kieu = " ".join(typing.get_args(C.MemoryType))
    prim = " ".join(
        typing.get_args(C.VisualContainerBinding.model_fields["primitive"].annotation)
    )

    return (
        "HỢP ĐỒNG JSON — dùng ĐÚNG các tên dưới đây, không đặt tên khác, không "
        "bọc thêm một tầng nào ở ngoài.\n\n"
        f"Đối tượng gốc: {spec}\n"
        f"  BẮT BUỘC phải có đủ: {', '.join(bat_buoc)} — thiếu một cái là hỏng.\n"
        "  `?` = tuỳ chọn. KHÔNG có khoá `semantic_program`, `variables` hay "
        "`program` ở ngoài cùng.\n\n"
        f"memory_declarations[]: {khai}\n"
        f"  type nhận đúng một trong: {kieu}\n"
        "  element_type dùng cho array/stack/queue/set/matrix; key_type và "
        "val_type dùng cho map.\n\n"
        + _khoi("statements[] — mỗi phần tử có `kind` và các trường:",
                C.SemanticStatement)
        + "\n\n"
        # ⚠️ KHÔNG thêm bảng kiểu của `measure` vào bản ĐẦY ĐỦ. `measure` là
        # biểu thức hình học; một đề Tin học không bao giờ phát nó, nên bảng ấy
        # ở đây là byte thuần tuý thừa — và ngân sách thẻ (4200) tồn tại đúng để
        # chặn kiểu thêm-vì-tiện này. Nó nằm ở `_the_hinh_hoc`, cạnh chỗ dùng.
        + _khoi("biểu thức giá trị — cũng có `kind`:", C.ValueExpr)
        + "\n\n"
        + _khoi("điều kiện — cũng có `kind`:", C.ConditionExpr)
        + "\n\n"
        "visual_bindings: containers[] pointers[] value_boxes[]\n"
        f"  containers[]: {_truong(C.VisualContainerBinding)}\n"
        f"    primitive nhận đúng một trong: {prim}\n"
        f"  pointers[]: {_truong(C.VisualPointerBinding)}\n"
        f"  value_boxes[]: {_truong(C.VisualValueBoxBinding)}\n"
    )
