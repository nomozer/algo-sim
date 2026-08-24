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
ERR_GIA_THIET_SAI_KIEU = "MODEL_ASSUMPTION_TYPE_NOT_ALLOWED"
ERR_GIA_THIET_LA_DAP_AN = "MODEL_ASSUMPTION_IS_ANSWER"
ERR_GIA_THIET_KHONG_LY_DO = "MODEL_ASSUMPTION_NO_REASON"


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
    #: Biến nào mang CÂU TRẢ LỜI. Không bao giờ được là giả thiết.
    dap_an = {ob.witness for ob in contract.obligations if ob.witness}
    ma_loi: str | None = None

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
                unresolved.append(
                    f"{decl.name}: là WITNESS của một nghĩa vụ — câu trả lời "
                    "không bao giờ được khai làm giả thiết. Hãy để một câu "
                    "lệnh tính ra nó."
                )
            elif decl.type not in _KIEU_DUOC_GIA_THIET:
                ma_loi = ma_loi or ERR_GIA_THIET_SAI_KIEU
                unresolved.append(
                    f"{decl.name}: kiểu '{decl.type}' không được mang giả thiết "
                    f"mô hình hoá (chỉ {sorted(_KIEU_DUOC_GIA_THIET)}). Đối "
                    "tượng này phải được DỰNG từ các điểm đã chọn."
                )
            elif not ly_do:
                ma_loi = ma_loi or ERR_GIA_THIET_KHONG_LY_DO
                unresolved.append(
                    f"{decl.name}: giả thiết mô hình hoá phải nêu LÝ DO chọn."
                )
            else:
                gia_thiet.append(f"{decl.name}: {ly_do}")
            continue

        if not fid:
            unresolved.append(
                f"{decl.name}: có initial_value nhưng thiếu source_fact_id — "
                "không truy được về đề bài"
            )
            continue

        fact = contract.fact(fid)
        if fact is None:
            unresolved.append(
                f"{decl.name}: source_fact_id '{fid}' không có trong RequestContract"
            )
            continue

        khai = _canon(decl.initial_value)
        cho = fact.values
        thua = [v for v in khai if v not in cho]
        if thua:
            unresolved.append(
                f"{decl.name}: giá trị {thua!r} không có trong mục '{fid}' "
                f"({fact.label}) — đề không cho những giá trị này"
            )

    if unresolved:
        return GroundingResult(
            ok=False,
            error_code=ma_loi or "INPUT_NOT_GROUNDED",
            unresolved=unresolved,
            assumptions=gia_thiet,
        )
    return GroundingResult(ok=True, assumptions=gia_thiet)
