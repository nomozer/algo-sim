# -*- coding: utf-8 -*-
"""Thẻ văn phạm KHÔNG ĐƯỢC trôi khỏi hợp đồng.

Thẻ này thay `responseSchema` — thứ Gemini không nhận được vì schema IR đệ quy
và nội suy `$ref` nổ ~10× mỗi bậc. Nó là hợp đồng giao diện DUY NHẤT mà mô hình
nhìn thấy, nên một `kind` mới bị bỏ sót trong thẻ nghĩa là mô hình không bao giờ
biết `kind` ấy tồn tại — và nó im lặng, vì validator chỉ nói "chương trình sai",
không nói "tại thẻ thiếu".

Vì thẻ SINH TỪ Pydantic nên nó tự đúng; các test dưới đây khoá đúng điều đó lại,
để lần sau ai đó viết tay một bản "cho gọn" thì ĐỎ.
"""
from __future__ import annotations

import typing

from pydantic import BaseModel

from app.simulation.semantic_program import contract as C
from app.simulation.semantic_program.grammar_card import grammar_card


def _nhan_cua(alias) -> set[str]:
    ra = set()
    for arg in typing.get_args(typing.get_args(alias)[0]):
        m = typing.get_args(arg)[0] if typing.get_args(arg) else arg
        if isinstance(m, type) and issubclass(m, BaseModel):
            k = m.model_fields.get("kind")
            if k:
                ra.add(typing.get_args(k.annotation)[0])
    return ra


def test_the_liet_ke_DU_moi_statement_kind():
    the = grammar_card()
    thieu = [k for k in _nhan_cua(C.SemanticStatement) if f"  {k}:" not in the]
    assert not thieu, (
        f"thẻ thiếu statement kind: {thieu}. Mô hình sẽ không bao giờ biết "
        "chúng tồn tại, và nó hỏng CÂM."
    )


def test_the_liet_ke_DU_moi_bieu_thuc_va_dieu_kien():
    the = grammar_card()
    for alias, ten in ((C.ValueExpr, "biểu thức"), (C.ConditionExpr, "điều kiện")):
        thieu = [k for k in _nhan_cua(alias) if f"  {k}:" not in the]
        assert not thieu, f"thẻ thiếu {ten} kind: {thieu}"


def test_the_liet_ke_DU_moi_MemoryType_va_primitive():
    the = grammar_card()
    for t in typing.get_args(C.MemoryType):
        assert t in the, f"thẻ thiếu MemoryType `{t}`"
    prims = typing.get_args(
        C.VisualContainerBinding.model_fields["primitive"].annotation
    )
    for p in prims:
        assert p in the, f"thẻ thiếu visual primitive `{p}`"


def test_the_neu_dung_ten_truong_cap_cao_nhat():
    """Đúng ba trường bắt buộc này là chỗ mô hình đã đặt sai tên ở lượt pilot 2."""
    the = grammar_card()
    for truong in ("title", "memory_declarations", "statements"):
        assert truong in the, truong


def test_the_CHAN_DUNG_cac_ten_mo_hinh_da_tu_bia():
    """Lượt pilot 2 đo được: mô hình bọc trong `semantic_program` và gọi
    `variables`. Thẻ phải nói thẳng là không có hai thứ đó."""
    the = grammar_card()
    assert "KHÔNG có khoá" in the
    assert "`variables`" in the and "`semantic_program`" in the


def test_the_du_gon_de_khong_thanh_nhoi_prompt():
    """Nó là hợp đồng giao diện, không phải chỗ chép luật. Phình lên nghĩa là ai
    đó đang nhồi văn xuôi vào — thứ đề tài này cố ý tránh."""
    n = len(grammar_card().encode("utf-8"))
    # 2600 → 3400 (2026-08-22): thêm nhãn KIỂU cho từng trường (`:tên`,
    # `:biểu thức`, `:khối lệnh`). Không phải văn xuôi — đó là thứ đã sửa 11+
    # case trượt vì mô hình điền biểu thức vào chỗ đòi tên biến.
    #
    # 3400 → 3800 (2026-08-24): miền HÌNH HỌC KHÔNG GIAN thêm 8 kind — 5 biểu
    # thức + 3 câu lệnh dựng — và 6 `MemoryType`. Thẻ phình vì **từ vựng**, không
    # vì văn xuôi: nó in `intersect_line_plane: line:tên plane:tên`, không in
    # một câu giải thích nào. Đã thử rút gọn `description` của tám model mới
    # trước khi nâng trần — vô ích, vì thẻ KHÔNG đọc `description`, nó dẫn xuất
    # từ tên trường và KIỂU.
    #
    # 3800 → 3900 (2026-08-25): thêm ĐÚNG MỘT biểu thức, `intersect_line_line`
    # (~48 byte). Một lượt live trên đề học sinh gửi thật cho thấy mô hình viết
    # đúng nó ở CẢ BA lượt thử — `Q = d ∩ AD`, dạng cực phổ biến của bài thiết
    # diện — và cả ba lần hợp đồng từ chối vì thiếu tag. Kernel đã có phép ấy từ
    # đầu; đây thuần tuý là bỏ sót ở tầng nối.
    #
    # Guard chống nhồi văn xuôi THẬT SỰ là `test_the_khong_phai_van_ban_viet_tay`
    # ngay dưới đây; trần byte chỉ là lưới thứ hai, chặn ca ai đó thêm 50 kind —
    # đúng như dòng trên đã ghi, và một từ vựng mới không phải ca ấy.
    # 3900 → 4000 (2026-08-26, Phase 6.6): thêm ĐÚNG MỘT câu lệnh,
    # `construct_polygon` (~62 byte). Bốn lượt smoke cho thấy mô hình với tay
    # tìm "đáy ABCD" ở 2/4 lượt qua hai đường khác nhau — hợp đồng không có từ
    # cho một MIỀN PHẲNG HỮU HẠN, chỉ có mặt phẳng vô hạn và khối.
    #
    # Vẫn là TỪ VỰNG, không phải văn xuôi — đúng ca mà dòng dưới đã ghi là
    # trần byte KHÔNG nhắm tới.
    #
    # 4000 → 4200 (2026-08-31): HAI câu lệnh + một nhãn kiểu đúng hơn, đo được:
    #   `declare_point`      ~115 byte — khai điểm gốc NGAY TRONG dòng chương
    #                        trình. 3/4 ca live đốt trọn lượt tổng hợp đầu tiên
    #                        vì IR không có từ cho câu ấy.
    #   `vector_from_points`  ~64 byte — toán hạng CÓ HƯỚNG cho `angle_cos`.
    #   nhãn `[x,y,z]`        ~40 byte — thay "danh sách giá trị". Thẻ từng gọi
    #                        `at` là "khối lệnh", đúng lớp lỗi mà chú thích ở
    #                        `grammar_card._kieu` đã kể một lần rồi.
    #
    # Ba khoản đều là TỪ VỰNG hoặc SỬA NHÃN SAI — không khoản nào là văn xuôi,
    # và mỗi khoản đổi lấy một lượt sửa không phải tiêu. Guard chống nhồi văn
    # xuôi vẫn là `test_the_khong_phai_van_ban_viet_tay` bên dưới.
    #
    # 4200 → 4400 (2026-09-01, NAMED_GEOMETRY_OPERAND_ERGONOMICS): ~175 byte,
    # KHÔNG một từ vựng mới nào — chỉ đổi nhãn `tên` thành `tên<point3>` ở 23 ô
    # toán hạng, dẫn từ `hoisting.O_TEN`.
    #
    # Vì sao đáng: `tên` nói *điền một chuỗi* và im lặng về hai điều mô hình cần
    # — chuỗi ấy trỏ MỘT VẬT ĐÃ CÓ, và vật ấy phải đúng kiểu.
    # `FRESH_TRANSLATION_COMPOSITION_PROBE` đo được cái giá của sự im lặng ấy:
    # 5 lần lồng `vector_from_points` thẳng vào `translate.vector`, 2 lượt sửa,
    # 10.705 token. Đây đúng là ca "SỬA NHÃN SAI" mà lần nâng trước đã ghi là
    # đáng, và lần này nhãn sai nằm ở ô toán hạng của MỌI phép dựng.
    # 4400 → 4450 (2026-09-02, G4_CONSTRUCTION_EXPRESSIVENESS_BRIDGE): thẻ đi
    # từ 4364 → 4431 byte, tức **+67**, cho ĐÚNG MỘT từ vựng —
    # `plane_perpendicular_to_line`. (Bản đầu của chú thích này ghi "+31",
    # là phần vượt TRẦN CŨ chứ không phải mức tăng; sửa 2026-09-03.)
    #
    # Vì sao chỉ một, khi kernel có BỐN phép cùng nhóm: cổng hợp thành hỏi từng
    # phép *"IR hiện tại diễn đạt được không"* bằng chương trình chạy thật, và
    # ba phép kia CÓ (đường ∥ đường · mặt ∥ mặt · đường ⊥ mặt), nên chúng không
    # được thêm — thêm một cửa cho thứ đã nói được là nhồi thẻ.
    #
    # Phép này thì không, và không phải vì dài: mọi phép sinh điểm của IR bảo
    # toàn bao affine của các điểm đã khai, còn mặt phẳng cần dựng nằm ngoài bao
    # ấy, nên ba điểm lấy được luôn thẳng hàng. Đo được: 24 điểm sinh ở độ sâu 2
    # từ `{A,B,M}`, 0 điểm ngoài `(ABM)`; và lối thoát duy nhất — khai thêm điểm
    # phụ — bị `grounding_gate` từ chối đúng theo thiết kế.
    # 4450 → 4750 (2026-09-03, PHASE_2_CURVED_SOLID_FOUNDATION): 4436 → 4703,
    # tức **+267**, cho một HỌ HÌNH HỌC MỚI trọn vẹn:
    #   `construct_curved_solid`  155 byte — MỘT câu lệnh cho cả ba hình (cầu ·
    #                             trụ · nón). Ba câu lệnh riêng sẽ tốn gấp ba và
    #                             đẻ ba nhánh ở mọi tầng phía sau.
    #   `intersect_plane_curved`   69 byte — phép giao, MỘT kiểu trả về.
    #   `radius` + `lateral_area`  ~43 byte enum + hai dòng chữ ký.
    #
    # Vì sao KHÔNG có `height`/`slant`, dù đề THPT hỏi chúng liên tục: chiều cao
    # trụ = `distance(anchor, apex_or_top)`, đường sinh nón =
    # `distance(apex_or_top, rim_point)`, và cả bốn toán hạng đều là ĐIỂM CÓ TÊN
    # trong chính chương trình đã dựng khối. Cổng hợp thành G4 đã cấm thêm cửa
    # cho thứ nói được rồi; luật ấy áp ở đây y nguyên.
    #
    # Vì sao KHÔNG có `surface_area`: `S_tp` nón `= πrl + πr²` có hai căn thức
    # khác nhau, và miền số cố ý từ chối tổng ấy. Một lượng đo mà ca hợp lệ
    # thường gặp cũng ném là dạy mô hình một cửa dẫn thẳng vào lỗi runtime.
    # 4750 → 5500 (2026-09-04, OPERAND_ROLE_HINTS): 4703 → 5436 byte. CÙNG một
    # nguyên nhân với trần thẻ hình học bên dưới — `_truong` dùng chung, nên
    # gợi ý VAI TRÒ đọc từ `Field(description=…)` xuất hiện ở cả hai bản thẻ.
    # Không từ vựng mới, không văn xuôi viết tay. Bản đầy đủ (Tin học) hiện
    # KHÔNG được gửi cho mô hình ở đường sản phẩm, nhưng guard vẫn canh nó nên
    # trần phải đi theo.
    # 5500 → 5600 (2026-09-04, CENTER_RADIUS_CURVED_CONSTRUCTION_FOUNDATION):
    # 5436 → 5526 byte. Nguyên nhân đã PHÂN LOẠI trước khi nới, theo đúng luật
    # OPERAND_ROLE_HINTS đặt ra: đây là **từ vựng mới thật** — ô `radius` của
    # `construct_curved_solid`, sinh từ lược đồ, không phải văn xuôi viết tay.
    # Đã trừ phần nới được: mô tả trường chỉ nói VAI TRÒ, còn luật "đúng một
    # trong hai" để validator giữ (chính doctrine trong thông điệp assert này) —
    # cắt được 45 byte, phần còn lại là không nén thêm được.
    # Thẻ THẬT gửi cho mô hình (`hinh_hoc`) là 5410 byte, VẪN DƯỚI 5500; con số
    # vượt trần thuộc bản đầy đủ mà đường sản phẩm không gửi.
    # 5600 → 5660 (2026-09-05, CURVED_CONSTRUCTION_GROUNDING_FOUNDATION):
    # 5526 → 5588 byte, +62. PHÂN LOẠI TRƯỚC KHI NỚI, và cả 62 byte là **từ
    # vựng mới thật**, sinh từ lược đồ:
    #   · ô `height` — không có nó thì trụ/nón khai bằng (bán kính, chiều cao)
    #     KHÔNG diễn đạt được, mà đó là cách SGK phát biểu gần như mọi bài;
    #   · gợi ý "bỏ trống" ở `anchor` — không có nó thì mô hình không có cách
    #     nào biết đường pose canonical tồn tại.
    # Lượt V3 held-out đo được cái giá của việc THIẾU hai thứ này: 0/9 ca dương
    # servable (`docs/CURVED_V3_LIVE_ACCEPTANCE.md` §8). Không phải văn xuôi:
    # mọi luật tổ hợp vẫn do validator giữ.
    assert n <= 5660, (
        f"thẻ = {n} byte. Luật nào mã hoá được thì để validator giữ, đừng viết "
        "vào thẻ."
    )

    # ⚠️ Con số ở trên là thẻ ĐẦY ĐỦ, và **không phải thứ mô hình nhận**: đường
    # sản phẩm chỉ phát đề hình học, nên thẻ thật là `grammar_card("hinh_hoc")`.
    # Assert thứ hai này thêm 2026-09-03 để guard canh đúng cái được gửi đi —
    # trước đó nó canh một biến thể mà sản phẩm không dùng tới.
    # 4200 → 4650 (2026-09-04, CARD_CATEGORY_AFFORDANCE): 4035 → 4587 byte,
    # tức **+552**, KHÔNG một từ vựng mới nào và KHÔNG một câu văn xuôi nào —
    # chỉ một nhãn LOẠI đứng đầu mỗi dòng phép, sinh từ `_tap_hinh_hoc()` và
    # `_cua_tieu_thu()`:
    #
    #   [LỆNH] construct_section: …
    #   [BIỂU THỨC→assign] intersect_plane_curved: …
    #   [BIỂU THỨC→assign|construct_point] midpoint: …
    #
    # Vì sao đáng, đo được: `AUDIT_MODEL_FACING_SCHEMA_SURFACE` chỉ ra thẻ chia
    # nhóm bằng TIÊU ĐỀ, còn từng dòng thì im lặng về loại của nó.
    # `intersect_plane_curved` cách tiêu đề nhóm 5 dòng và cách `assign` 15
    # dòng; `construct_section` — CÂU LỆNH, cùng toán hạng `solid`+`plane`,
    # hình dạng gần trùng — nằm cách 9 dòng. `cylinder_2` (probe V2) viết phép
    # đầu như một câu lệnh, và chín lượt sửa không cứu được ca nào.
    #
    # Đây là ca "SỬA NHÃN SAI" mà hai lần nâng trần trước đã ghi là đáng, chỉ
    # khác chỗ: lần này nhãn thiếu là LOẠI của chính phép, và nó thiếu trên MỌI
    # dòng. Cửa tiêu thụ dẫn từ model (`construct_point` tự hiện ra ở phép sinh
    # điểm), không viết tay.
    # 4650 → 5400 (2026-09-04, OPERAND_ROLE_HINTS): 4587 → 5320 byte, tức
    # **+733**, KHÔNG một từ vựng mới nào và KHÔNG một câu văn xuôi viết tay
    # nào — mỗi ô toán hạng nay in kèm VAI TRÒ, đọc thẳng từ
    # `Field(description=…)` đã có sẵn trong `contract.py`:
    #
    #   from_point:tên<point3>[điểm gốc] to_point:tên<point3>[điểm ngọn]
    #   a:tên<point3>[điểm đầu] b:tên<point3>[điểm cuối]        ← divide_segment
    #   anchor:tên<point3>[TÂM (cầu) hoặc TÂM ĐÁY (trụ, nón)]
    #
    # Vì sao đáng, đo được: `OPERAND_NAME_CONVERGENCE_AUDIT` chứng minh bằng
    # kernel rằng **bốn trên năm** phép nhận hai `point3` đặt tên ĐÚNG theo ngữ
    # nghĩa (đảo thứ tự: `midpoint`/`construct_line` không đổi kết quả,
    # `vector_from_points`/`divide_segment` đổi). Nên việc phải làm là NÓI RA
    # vai trò, không phải hội tụ tên. Thẻ trước đó nói ô ấy nhận *một cái tên,
    # kiểu point3* và im lặng về vai trò — `circumsphere` gửi sai tên toán hạng
    # ở lượt sửa, và cùng lỗi ấy tôi mắc khi viết bài chứng nhận.
    #
    # Đây là ca "SỬA NHÃN SAI / THÊM NHÃN THIẾU" mà ba lần nâng trần trước đã
    # ghi là đáng. Không phải từ vựng, không phải ví dụ theo dạng bài (khoá bởi
    # `test_operand_role_hints.test_H13_*`), không phải chữ ký chép lại (mọi
    # gợi ý phải BẰNG `Field.description`, khoá bởi `test_H6_*`).
    #
    # ⚠️ NỢ ĐÃ BIẾT: vài mô tả chỉ lặp lại chính kiểu vừa in
    # (`line:tên<line3>[đường thẳng]`). Không rút ở tầng THẺ vì mọi phép rút
    # theo từng phép sẽ thành một thẩm quyền thứ hai; chỗ sửa đúng là **mô tả ở
    # `contract.py`**, và đó là một lượt dọn riêng.
    # 5400 → 5450 (2026-09-04, CENTER_RADIUS_CURVED_CONSTRUCTION_FOUNDATION):
    # 5320 → 5410 byte. Cùng phân loại với trần bản đầy đủ ở trên: **từ vựng
    # mới thật**, sinh từ lược đồ — ô `radius` mở lớp bài *"mặt cầu tâm O bán
    # kính r"* mà ba-điểm KHÔNG diễn đạt nổi (chứng minh ở
    # `docs/CENTER_RADIUS_CURVED_CONSTRUCTION_FOUNDATION.md`). Đây là thẻ mô
    # hình THẬT SỰ nhận, nên 90 byte ấy là thứ duy nhất mở được đường đi.
    # 5450 → 5510 (2026-09-05, CURVED_CONSTRUCTION_GROUNDING_FOUNDATION):
    # 5410 → 5472 byte. Cùng 62 byte, cùng phân loại với trần bản đầy đủ.
    #
    # 5510 → 5720 (2026-09-05, MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT):
    # 5472 → 5675 byte, tức **+203**. PHÂN LOẠI TRƯỚC KHI NỚI, và cả 203 byte
    # là **NHÃN THIẾU** — đúng hạng mục mà bốn lần nâng trần trước đã ghi là
    # đáng, không phải từ vựng mới, không phải ví dụ theo dạng bài:
    #
    #   178 byte — `→<kiểu>` trên 17 dòng phép. Thẻ vốn in TOÁN HẠNG của mọi
    #     phép và KHÔNG in kiểu KẾT QUẢ của phép nào, dù cả hai vế đã nằm sẵn
    #     trong thẩm quyền (`_CHU_KY` vế phải, `_KIEU_DUNG`). Đo được ở
    #     `CURVED_SECTION_MODEL_DISCOVERABILITY_PROBE`: lượt tổng hợp ĐẦU chọn
    #     `construct_section` 8/8 ca kể cả sáu ca khối cong, và `circle3` xuất
    #     hiện trong khai báo 0/8 — nó chỉ tồn tại với tư cách kiểu KẾT QUẢ,
    #     tức đúng thứ thẻ không nói.
    #    25 byte — danh sách kiểu khai được nay DẪN XUẤT (`_kieu_khai_duoc`).
    #     Bản viết tay đã trôi: `MemoryType` thêm `circle3`/`curved_solid` ở
    #     wave cong 2026-09-03 mà danh sách không được sửa, nên thẻ tự mâu
    #     thuẫn — viết `tên<curved_solid>` trong khi phần khai báo nói kiểu ấy
    #     không tồn tại. `int` cũng vào theo, và đúng: thẻ vẫn luôn nhận
    #     `tên<scalar|float|int>`.
    #
    # Trần bản ĐẦY ĐỦ không đổi (5588 byte): mũi tên chỉ áp cho thẻ hình học.
    m = len(grammar_card("hinh_hoc").encode("utf-8"))
    assert m <= 5720, (
        f"thẻ hình học = {m} byte — đây mới là thẻ mô hình THẬT SỰ nhận.")


def test_the_khong_phai_van_ban_viet_tay():
    """Sinh từ nguồn ⇒ thêm một kind vào contract là thẻ tự có. Test này khoá
    tính chất ấy bằng cách đối chiếu SỐ LƯỢNG."""
    the = grammar_card()
    tong = (len(_nhan_cua(C.SemanticStatement))
            + len(_nhan_cua(C.ValueExpr))
            + len(_nhan_cua(C.ConditionExpr)))
    dem = sum(1 for d in the.splitlines() if d.startswith("  ") and ":" in d)
    assert dem >= tong, f"thẻ liệt kê {dem} dòng kind, contract có {tong}"


def test_the_liet_ke_GIA_TRI_cua_truong_enum():
    """Tên trường nói được *chỗ nào điền*, không nói được *điền gì*.

    Đo được ở lượt kiểm sau khi thêm thẻ: mô hình dựng đúng cấu trúc lồng nhưng
    viết `op: "add"` thay vì `"+"`, nên chương trình vẫn trượt thẩm định.
    """
    the = grammar_card()
    for gt in ("+", "//", "==", "<=", "and", "or"):
        assert gt in the, f"thẻ thiếu giá trị toán tử `{gt}`"


def test_the_neu_KIEU_cua_tung_truong():
    """Tên trường nói *chỗ nào điền*; kiểu nói *điền cái gì vào đó*.

    Lượt pilot 3: mô hình nhét cả object biểu thức vào `index.container` —
    trong khi nó là `str`, tức TÊN BIẾN. 11+ case trượt vì đúng nhầm lẫn này.
    """
    the = grammar_card()
    assert "index: container:tên" in the, "thiếu nhãn kiểu cho `container`"
    assert "expr:biểu thức" in the
    assert "body:khối lệnh" in the


def test_the_khong_gan_nhan_kieu_cho_truong_enum():
    """Trường enum đã liệt kê giá trị rồi — gắn thêm nhãn kiểu là thừa."""
    the = grammar_card()
    assert "op(+|-|*|//|%)" in the
    assert "op(+|-|*|//|%):" not in the


def test_khong_in_duong_dan_module_vao_the():
    """Bẫy đã sập một lần: `typing.get_args` của union phân biệt trả về
    `Annotated[...]`, và nếu nhận nhầm chúng là giá trị enum thì thẻ in ra cả
    đường dẫn module — 19.759 byte thay vì ~2 KB."""
    the = grammar_card()
    for rac in ("typing.Annotated", "app.simulation", "Tag(tag="):
        assert rac not in the, f"thẻ lọt rác kiểu: {rac}"
