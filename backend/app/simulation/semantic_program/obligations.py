# -*- coding: utf-8 -*-
"""Obligation taxonomy — khoá vào HỆ KIỂU của IR, không khoá vào catalog.

VÌ SAO KHÔNG KHOÁ VÀO CATALOG: số target chương trình là MỞ (đề mới đẻ ra hoài),
nên taxonomy dựa trên nó sẽ phình theo số bài — đúng cái vừa gỡ ở
`completeness_gate`. Số cấu trúc dữ liệu trong IR thì ĐÓNG và nhỏ.

BA NGUỒN, không phải một (spec §5.1):
    IR type semantics + expression/statement semantics + reusable server-owned checker

Điều kiện thứ ba là điều kiện CHẶN: nghĩa vụ không có bộ kiểm tất định do server
sở hữu thì KHÔNG được vào bảng, dù tên nghe hợp lý tới đâu.

ĐÓNG BĂNG TRƯỚC SEALED. Chọn từ phân tích DEV
(`docs/evaluation/semantic-benchmark/dev/DEV_TAXONOMY_ANALYSIS.md`), không phải
từ nhu cầu của từng ca. Sau khi SEALED niêm phong: KHÔNG thêm checker để cứu
held-out case — hard scope lock §1.1.

Hai thứ CỐ Ý không có mặt, ghi lại để lần sau khỏi "bổ sung cho đủ":
- `distinct_preserving_order` — là một phép của `derived_sequence`.
- `connected_components` — tổ hợp được từ `reachability` lặp.

─── `predicate_verdict`: MỞ 2026-08-23, và vì sao phản đối cũ không đứng ────

Bản đầu loại nó với lý do: *"kiểm nó đòi cài lại chính thuật toán đang kiểm, nên
oracle mất tính độc lập"*. Lý do ấy nghe đúng nhưng **áp quá rộng** — theo đúng
tiêu chuẩn đó thì không checker nào trong bảng sống sót:

    `_extremum`        tính lại `max(seq)` từ container trong snapshot
    `_membership`      tính lại `item in box`
    `_total_mapping`   tính lại phép đếm

Cả ba đều "cài lại" phép toán mà chương trình vừa làm. Điều khiến chúng vẫn là
oracle là chỗ khác: chúng tính lại **TỪ DỮ LIỆU ĐỀ**, bằng phép sơ cấp, và
KHÔNG bao giờ đọc witness để suy ra đáp án — witness chỉ được đem SO. Vị từ cân
bằng ngoặc thoả đúng ba điều kiện ấy: một lượt quét đếm là phép sơ cấp, chạy
trên chuỗi đã grounded, độc lập hoàn toàn với chương trình.

Khác biệt THẬT mà phản đối cũ chạm tới: `predicate_verdict` không kiểm được từ
TRẠNG THÁI CUỐI (ngăn xếp rỗng ở cuối không chứng minh gì — một chương trình
không bao giờ push cũng kết thúc rỗng). Nó buộc phải tính lại từ đầu vào. Đó là
ràng buộc về *nguồn dữ liệu của checker*, không phải về tính độc lập.

Nguồn phát hiện: DEV (ma trận xuyên miền cho thấy bài ngoặc không có kind nào
diễn đạt được, nên `executable=True` mà không bao giờ `servable`). KHÔNG phải từ
một ca SEALED.

ADMISSIBILITY ≠ VERIFIABILITY, và ở đây hai thứ đó tách nhau rõ nhất: kind này
được KHAI cho mọi vị từ, nhưng chỉ vị từ nào có mặt trong `PREDICATE_CHECKERS`
(`postconditions.py`) mới được KIỂM. Vị từ lạ ⇒ mức yếu ⇒ `verification_gap`,
`executable=True` mà `servable=False`. Đó là chỗ luật "LLM nói gì checker tin
nấy" bị chặn.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

#: kind → miền kiểu container hợp lệ. Bảng này nói nghĩa vụ nào ĐƯỢC KHAI và
#: hợp với kiểu container nào — nó KHÔNG nói cái nào kiểm chứng được. Câu hỏi
#: sau do `CHECKERS` (postconditions.py) trả lời; xem `has_server_owned_checker`
#: để biết vì sao trộn hai câu đó lại từng làm mức yếu chết câm.
OBLIGATION_KINDS: dict[str, frozenset[str]] = {
    # (/13) Nghĩa vụ của miền Tin học (extremum, aggregate_matching, ordering, membership, first_match_index,
    # total_mapping, derived_sequence, reachability, structural_traversal, predicate_verdict, scalar_accumulation)
    # đã gỡ cùng checker của chúng: chủ thể của chúng là container/vô hướng của một chương trình thuật toán.
    # ── MIỀN HÌNH HỌC KHÔNG GIAN (2026-08-24) ────────────────────────────────
    #
    # Tám nghĩa vụ, chia hai nhóm theo ĐÚNG câu hỏi bài toán hỏi:
    #   quan hệ  → trả lời ĐÚNG/SAI  (thuộc · song song · vuông góc · đồng phẳng)
    #   đại lượng → trả lời MỘT SỐ   (khoảng cách · góc · thể tích)
    #
    # VÌ SAO TÁCH `point_on_line` KHỎI `point_on_plane` thay vì gộp thành một
    # `incidence`: hai cái nhận CHỦ THỂ khác nhau (`line3` ↔ `plane3`), và gộp
    # thì bảng kiểu bên dưới mất tác dụng — một đề hỏi "M có thuộc (SBC) không"
    # sẽ lọt qua khi LLM gắn nhầm vào một đường thẳng.
    #
    # VÌ SAO CẢ TÁM ĐỀU CÓ CHECKER SERVER-OWNED: ở miền này oracle là **giải
    # tích**, không phải cài lại thuật toán đang kiểm. Đó chính là cái khó đã
    # buộc loại `predicate_verdict` khỏi taxonomy hồi tháng 8, và miền hình học
    # thoát được nó.
    "point_on_line": frozenset({"line3"}),
    "point_on_plane": frozenset({"plane3"}),
    "parallel": frozenset({"line3", "plane3"}),
    "perpendicular": frozenset({"line3", "plane3"}),
    # `section` PHẢI có mặt ở đây. ĐO ĐƯỢC, lượt live geo_03 ngày 2026-08-30:
    # thêm `section` vào `MemoryType` mà quên dòng này ⇒ mô hình khai thiết
    # diện đúng kiểu mới, khai `coplanar` đúng như tập DEV mong, và cổng bác
    # với *"kiểu 'section' không hợp với nghĩa vụ này"* — một đề TỪNG CHẠY
    # ĐƯỢC thành không chạy được.
    #
    # `check_coplanar` chưa bao giờ từ chối một `Section` (nó đọc `.polygon`);
    # chỉ BẢNG KIỂU chưa được cập nhật. Đúng loại "hai bảng nói hai điều khác
    # nhau về cùng một vật" mà wave này sinh ra để dọn — và wave này tự tạo
    # thêm một cái. `test_moi_checker_nhan_Section_deu_khai_section` khoá lại.
    "coplanar": frozenset({"polygon3", "solid", "section"}),
    # THIẾT DIỆN — nghĩa vụ thứ chín, thêm 2026-08-30.
    #
    # VÌ SAO KHÔNG ĐỂ `coplanar` GÁNH: mọi đỉnh thiết diện sinh ra từ giao với
    # đúng MỘT mặt phẳng, nên chúng đồng phẳng theo định nghĩa — `coplanar`
    # trên một thiết diện gần như luôn xanh, kể cả khi đa giác thiếu đỉnh.
    # Nghĩa vụ này dựng lại thiết diện từ `params[solid] + params[plane]` rồi
    # so CHU TRÌNH, nên nó bắt được cả "thiếu một đỉnh" lẫn "cắt nhầm mặt".
    #
    # Nhận cả `section` (kiểu riêng) lẫn `polygon3`: chương trình sinh trước
    # 2026-08-30 khai thiết diện là `polygon3`, và một taxonomy chặt hơn ở đây
    # chỉ làm những chương trình ấy rơi xuống mức yếu chứ không làm chúng đúng
    # hơn.
    "section_matches": frozenset({"section", "polygon3"}),
    # ⚠️ `distance` · `angle` · `volume` **KHÔNG** viết ở đây nữa. Chúng là
    # nghĩa vụ ĐO, và kiểu chủ thể của chúng DẪN XUẤT từ `measure_contract`
    # ngay sau bảng này — xem khối `NGHIA_VU_DO` bên dưới.
}

# ── NGHĨA VỤ ĐO: DẪN XUẤT, không viết tay ────────────────────────────────
#
# `measure_contract.BANG_PHEP_DO` là **thẩm quyền duy nhất** của câu *"lượng đo
# này nhận kiểu nào"*. Trước 2026-09-03 bảng trên chép lại câu ấy cho
# `distance`/`angle`/`volume`, và bản sao đã trôi ở HAI chỗ:
#
#   volume  thiếu `curved_solid`  → ba chương trình cong ĐÚNG bị cổng phủ bác
#                                   (`CURVED_MODEL_ACCEPTANCE_V1`, 26 lượt model)
#   angle   thiếu `vector3`       → lệch có sẵn từ trước, chưa ai thấy
#
# Nạp sau khi bảng đã dựng chứ không nội suy vào literal: giữ literal thuần là
# **nghĩa vụ CẤU TRÚC**, còn nhóm ĐO thì nhìn thấy ngay là dẫn xuất.
def _nap_nghia_vu_do() -> None:
    from .measure_contract import NGHIA_VU_DO, kieu_chu_the_nghia_vu

    for nv in NGHIA_VU_DO:
        OBLIGATION_KINDS[nv] = kieu_chu_the_nghia_vu(nv)


_nap_nghia_vu_do()


# (/13) TERM_TRANSFORMS / AGGREGATE_OPS / SEQUENCE_TRANSFORMS / SEMANTIC_PRESCRIBED_PROCEDURES (thủ tục sắp xếp,
# duyệt cây/đồ thị mà đề Tin học có thể ép) đã gỡ cùng các nghĩa vụ dùng chúng.


class Obligation(BaseModel):
    """Một nghĩa vụ ngữ nghĩa do `analyze` khai, server đóng băng."""

    model_config = ConfigDict(frozen=True)

    kind: str
    container: str
    params: dict[str, Any] = {}

    @property
    def witness(self) -> str | None:
        """Biến mà chương trình phải tạo ra để chứng tỏ đã làm nghĩa vụ này."""
        w = self.params.get("witness")
        return w if isinstance(w, str) else None

    def describe(self) -> str:
        return f"{self.kind}({self.container})"


#: Nghĩa vụ KHÔNG CÓ witness — và không phải "chưa khai", mà là **không tồn tại**.
#:
#: ─── ĐO ĐƯỢC, lượt live `geo_03` 2026-08-30 ────────────────────────────────
#:
#: Schema `analyze` khai `witness` là `{"type": "STRING"}` và để nó trong
#: `required`. Structured output vì thế **không cho mô hình một cách hợp lệ nào
#: để nói "nghĩa vụ này không có witness"** — nên nó viết chuỗi `"null"`, và
#: C₁a bác với *"witness 'null' chưa khai báo"*.
#:
#: Đó không phải lỗi mô hình. Đó là một hợp đồng làm cho **câu trả lời đúng
#: không biểu diễn được**. Sửa ở nguồn: cho `witness` nhận JSON `null`, và khai
#: ở đây những kind mà `null` là câu trả lời ĐÚNG.
#:
#: `section_matches` là kind đầu tiên như thế: nó không hỏi *"vật thứ hai này
#: quan hệ thế nào với container"* mà hỏi *"container có ĐÚNG LÀ thiết diện của
#: khối K với mặt phẳng P không"*. Hai toán hạng ấy nằm ở `params`, không phải
#: ở witness.
WITNESS_FREE_KINDS: frozenset[str] = frozenset({"section_matches"})


def has_server_owned_checker(kind: str) -> bool:
    """Nghĩa vụ này có checker server-owned không? Không → mức yếu (§5.4).

    TỪNG SAI, và sai câm: bản đầu tên là `is_supported` và thân hàm trả
    `kind in OBLIGATION_KINDS` — tức hỏi "có trong taxonomy không". Hai tập ấy
    KHÁC NHAU: `structural_traversal` có trong taxonomy nhưng không có checker.
    Hệ quả là mức yếu chưa từng kích hoạt lần nào, nên `verification_gap` — thứ
    mà luận văn nêu như đóng góp — là mã chết trên đường C₁a, và tỉ lệ "phát
    canonical an toàn" bị thổi lên vì hệ phát kết quả duyệt cây mà không hề có
    cách kiểm độc lập.

    Bảng `CHECKERS` là nguồn sự thật duy nhất. Import trễ vì `postconditions`
    import ngược lại `Obligation` ở file này.
    """
    from .postconditions import CHECKERS

    return kind in CHECKERS


def accepts_container_type(kind: str, container_type: str | None) -> bool:
    """Nghĩa vụ này có nhận một chủ thể kiểu ấy không?

    MỘT cửa cho cả hai nhóm. Nhóm ĐO đã được nạp vào `OBLIGATION_KINDS` dưới
    dạng dẫn xuất (xem `_nap_nghia_vu_do`), nên hàm này không phải biết nghĩa
    vụ nào thuộc nhóm nào — và đó là lý do nó vẫn một dòng.
    """
    allowed = OBLIGATION_KINDS.get(kind)
    return bool(allowed and container_type in allowed)
