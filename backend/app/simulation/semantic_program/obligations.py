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

#: Cấu trúc duyệt được — miền của các nghĩa vụ đếm/gộp.
TRAVERSABLE = frozenset({"array", "matrix", "set", "map", "tree_node"})

#: kind → miền kiểu container hợp lệ. Bảng này nói nghĩa vụ nào ĐƯỢC KHAI và
#: hợp với kiểu container nào — nó KHÔNG nói cái nào kiểm chứng được. Câu hỏi
#: sau do `CHECKERS` (postconditions.py) trả lời; xem `has_server_owned_checker`
#: để biết vì sao trộn hai câu đó lại từng làm mức yếu chết câm.
OBLIGATION_KINDS: dict[str, frozenset[str]] = {
    "extremum": frozenset({"array", "matrix"}),
    # Bao trùm `count_matching` cũ: đếm = gộp với phép `count`. Thêm nó làm
    # taxonomy GỌN đi chứ không phình ra.
    "aggregate_matching": TRAVERSABLE,
    "ordering": frozenset({"array"}),
    "membership": frozenset({"array", "set", "map"}),
    # Khác `membership` ở chỗ đòi VỊ TRÍ ĐẦU TIÊN — thứ tự duyệt là một phần
    # của câu trả lời (điểm nghẽn nhận thức #3).
    "first_match_index": frozenset({"array"}),
    "total_mapping": frozenset({"map"}),
    "derived_sequence": frozenset({"array", "stack", "queue"}),
    "reachability": frozenset({"graph"}),
    "structural_traversal": frozenset({"tree_node"}),
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
    "coplanar": frozenset({"polygon3", "solid"}),
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
    "distance": frozenset({"point3", "line3", "plane3"}),
    "angle": frozenset({"line3", "plane3"}),
    "volume": frozenset({"solid"}),
    # Phán quyết đúng/sai trên TOÀN BỘ dữ liệu vào. Miền rộng vì một vị từ có
    # thể hỏi về bất kỳ cấu trúc nào; cái hẹp là tập vị từ KIỂM ĐƯỢC, và nó do
    # `PREDICATE_CHECKERS` giữ chứ không phải bảng này (xem docstring module).
    "predicate_verdict": (
        TRAVERSABLE
        | frozenset({"stack", "queue", "graph"})
        # VÔ HƯỚNG, mở 2026-08-24. "n chẵn hay lẻ", "biểu thức này True hay
        # False" — chủ thể là MỘT SỐ, không phải một tập. Vị từ vô hướng đi qua
        # `_PREDS` (`postconditions.py`): tập ĐÓNG và sơ cấp (even/odd/gt/ge/
        # lt/le/eq) đã có sẵn từ trước, nên mở chiều này KHÔNG đẻ thêm checker
        # nào. Vị từ ngoài tập ấy — "năm nhuận" chẳng hạn — vẫn là
        # `verification_gap`, và đó là câu trả lời trung thực.
        | frozenset({"int", "float", "bool", "str"})
    ),
    # ── `scalar_accumulation`, mở 2026-08-24 ────────────────────────────────
    #
    # VÌ SAO: đo cơ học trên chính bảng này cho thấy **0/10 nghĩa vụ nhận được
    # một chủ thể vô hướng**. Toàn bộ taxonomy hình dạng *container*. Nhưng vòng
    # lặp tích luỹ trên một BIÊN SỐ — `S = 1 + 2 + … + n`, `1 × 2 × … × n`,
    # `S = 1³ + 2³ + … + n³` — là kiến trúc cơ bản nhất của chương trình Tin học
    # 10, và không kind nào diễn đạt được nó. Đây là khoảng trống của HỢP ĐỒNG,
    # đo được mà không cần nhìn bài nào.
    #
    # KHÁC `aggregate_matching` ở NGUỒN: kia gộp trên một container đã có, đây
    # gộp trên một DÃY SINH RA TỪ BIÊN. Chủ thể là biên `n`, nên miền là vô
    # hướng — không chồng lấn.
    "scalar_accumulation": frozenset({"int", "float"}),
}

#: Số hạng của phép tích luỹ — tập ĐÓNG, mỗi phép tính lại được bằng biểu thức
#: sơ cấp trên `k`. Đóng là điều kiện để checker giữ tính độc lập: mở cho một
#: biểu thức bất kỳ thì checker phải ĐÁNH GIÁ biểu thức của chương trình, tức
#: chạy lại chính chương trình.
TERM_TRANSFORMS = frozenset({"identity", "square", "cube", "reciprocal"})

#: Phép gộp đóng của `aggregate_matching`.
AGGREGATE_OPS = frozenset({"count", "sum", "product", "max", "min"})

#: Phép biến đổi đóng của `derived_sequence` — mỗi phép kiểm được TẤT ĐỊNH mà
#: không cài lại thuật toán sinh ra nó.
SEQUENCE_TRANSFORMS = frozenset({"reverse", "distinct", "filter", "map", "identity"})

#: Thủ tục mà đề có thể ÉP BUỘC, dùng cho route semantic.
#:
#: Tập ĐÓNG RIÊNG, cố ý KHÔNG dẫn xuất từ catalog: khoá phạm vi cũ nằm ngay
#: trong `enum: list(analyze_exposed_values())` của `ANALYZE_SCHEMA`, nên tái
#: dùng nó là kéo lại đúng cái vừa gỡ (spec E5). Catalog vocabulary vẫn sống
#: cho đường module; nó chỉ không được quyết định admissibility ở đây.
#:
#: `None` = đề KHÔNG ép thủ tục ⇒ oracle so tương đương ngữ nghĩa, chứ không so
#: canonical mechanism events (spec §5.5).
SEMANTIC_PRESCRIBED_PROCEDURES = frozenset({
    "adjacent_compare_swap",
    "select_extreme_repeated",
    "shift_into_sorted_prefix",
    "partition_recursive",
    "tree_traversal.preorder",
    "tree_traversal.inorder",
    "tree_traversal.postorder",
    "tree_traversal.level_order",
    "breadth_first",
    "depth_first",
})


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
    allowed = OBLIGATION_KINDS.get(kind)
    return bool(allowed and container_type in allowed)
