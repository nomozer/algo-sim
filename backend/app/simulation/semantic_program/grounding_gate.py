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

from typing import Any

from pydantic import BaseModel, Field

from .contract import SemanticProgramSpec
# Tái dùng write-set của C₁a thay vì viết bản thứ hai: nó đã biết mọi dạng câu
# lệnh tạo ra một biến (`assign`, `pop`, `push`, `map_set`, biến chạy vòng lặp…)
# và hai bản rời nhau chắc chắn sẽ lệch khi thêm primitive.
from .coverage_gate import _producers
from .request_contract import RequestContract, norm_value
from .scale_normalization import bang_huu_ti, la_so_huu_ti
from .source_entities import la_ten_nguon, la_ten_suy_ra

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


def check_grounding(
    contract: RequestContract, spec: SemanticProgramSpec
) -> GroundingResult:
    """P2 — mọi giá trị khởi tạo phải truy được về ĐÚNG mục dữ liệu đã chỉ."""
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
        if _is_seed(decl.initial_value):
            continue  # hạt khởi tạo, không mang thông tin của đề

        # CHƯƠNG TRÌNH TỰ TÍNH RA. Có câu lệnh ghi vào biến này ⇒ giá trị khởi
        # tạo không gánh thông tin, nó chỉ là điểm xuất phát. Câu hỏi "phép tính
        # ấy có thoả nghĩa vụ không" là của C₁/C₂, không phải của P2.
        if decl.name in computed:
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
        if thua:
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
        else:
            _ghi(decl, "B", f"ghim về '{fid}' ({fact.label})")

    if unresolved:
        return GroundingResult(
            ok=False,
            error_code=ma_loi or "INPUT_NOT_GROUNDED",
            unresolved=unresolved,
            assumptions=gia_thiet,
            unresolved_citations=trich_dan_hong,
            justified_literals=biet_minh,
            unjustified_literals=vo_can,
        )
    return GroundingResult(
        ok=True, assumptions=gia_thiet, unresolved_citations=trich_dan_hong,
        justified_literals=biet_minh, unjustified_literals=vo_can,
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
