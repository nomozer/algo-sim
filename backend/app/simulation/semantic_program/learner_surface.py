# -*- coding: utf-8 -*-
"""CỔNG BỀ MẶT HỌC SINH — thứ CHẠY ĐƯỢC chưa chắc thứ XEM ĐƯỢC.

─── VÌ SAO CẦN MỘT CỔNG NỮA ───────────────────────────────────────────────────

Chuỗi cổng hiện có kiểm rất kỹ *chương trình*: cú pháp (validator), dữ liệu đề
(P1/P2), phủ nghĩa vụ (C₁a/C₁b), hậu điều kiện (C₂), và binding có phân giải
được không (`_assert_bindings_resolvable`). Qua hết chuỗi đó, `servable=True`.

Nhưng mọi cổng ấy đều nhìn về phía CHƯƠNG TRÌNH. Không cổng nào quay lại hỏi câu
của người học:

    những gì thuật toán làm CÓ HIỆN RA trên màn hình không?

Sự cố vNext đã chụp được màn hình chính là câu đó bị bỏ trống: chương trình chạy
đúng, lời kể đúng, envelope biên dịch sạch — và ngăn xếp trên hình vẫn rỗng suốt
bảy bước.

─── CHIỀU CÒN THIẾU CỦA HỢP ĐỒNG THỊ GIÁC ────────────────────────────────────

`_assert_bindings_resolvable` (bất biến #34) hỏi: *mỗi binding đã khai có phân
giải về một biến không?* Đó là chiều **binding → bộ nhớ**.

Chiều ngược lại chưa ai hỏi: *mỗi biến ĐÁNG THẤY có được khai binding không?*

Thiếu chiều này, một chương trình hoàn toàn hợp lệ vẫn có thể đẩy/lấy một ngăn
xếp suốt 20 bước, chỉ bind mỗi ô kết quả, rồi được phát đi. Học sinh nghe kể về
một ngăn xếp không có trên hình. Cả hai cổng đều xanh vì cả hai đều đúng — chúng
chỉ không cùng nhìn về phía màn hình.

─── VÌ SAO CHỈ ĐÒI ĐÚNG HAI LỚP, KHÔNG ĐÒI MỌI BIẾN ──────────────────────────

Đòi mọi biến phải có hình là từ chối oan hàng loạt mô phỏng đúng: biến đếm vòng
lặp, biến tạm khi hoán đổi, cờ nội bộ — chúng không phải nội dung bài học, và bắt
vẽ hết chỉ làm màn hình rối thêm.

Hai lớp bị đòi, và cả hai đều có lý do hẹp:

  1. **Container BIẾN ĐỘNG** — một tập hợp thay đổi qua các bước CHÍNH LÀ cơ chế
     mà bài đang dạy. Ngăn xếp, hàng đợi, mảng đang sắp: không thấy chúng đổi thì
     không còn gì để xem. Container đứng yên cả lượt thì không đòi — nó là dữ
     liệu nền, không phải diễn tiến.

  2. **Witness của nghĩa vụ** — chỗ chứa CÂU TRẢ LỜI. Phát một mô phỏng mà học
     sinh không bao giờ thấy đáp án thì `servable` đang nói dối về chính nghĩa
     của nó.

Ngoài hai lớp đó, cổng im lặng. Một cổng kêu oan là một cổng sẽ bị tắt.
"""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from .contract import SemanticProgramSpec
from .interpreter import SemanticExecutionResult
from .request_contract import RequestContract

#: Chuỗi kỹ thuật KHÔNG BAO GIỜ được đi tới bề mặt học sinh. Cùng danh sách với
#: `frontend/src/simulations/learner-gate.ts` — hai đầu của cùng một luật.
PLACEHOLDER_LEAKS = ("undefined", "null", "[object Object]", "NaN", "Infinity")

#: CHÍNH SÁCH HIỂN THỊ cho MỌI `MemoryType` đã admit — mỗi kiểu một quyết định
#: TƯỜNG MINH, kèm lý do khi quyết định là "không đòi".
#:
#: VÌ SAO LÀ BẢNG CHỨ KHÔNG PHẢI MỘT `frozenset`: bản đầu viết thẳng bảy tên vào
#: một hằng số, và nó bỏ sót `tree_node` — một `ContainerType` đầy đủ tư cách.
#: Bỏ sót đó KHÔNG ồn ào: cây dựng dần qua các bước mà không có hình thì gate vẫn
#: nói `servable=True`. Đúng lớp lỗi mà chính gate này sinh ra để chặn, lọt ngay
#: trong gate.
#:
#: `test_learner_surface_type_coverage` duyệt `typing.get_args(MemoryType)` và
#: đòi mọi kiểu có mặt ở đây. Thêm một `MemoryType` mà quên bảng này là ĐỎ — nên
#: lần sau câu hỏi "kiểu này có cần hiện không" bị bắt buộc phải trả lời.
SURFACE_POLICY: dict[str, str] = {
    # ── PHẢI HIỆN khi biến động: tập hợp thay đổi CHÍNH LÀ cơ chế bài đang dạy.
    "array": "container",
    "stack": "container",
    "queue": "container",
    "matrix": "container",
    "map": "container",
    "set": "container",
    "graph": "container",
    "tree_node": "container",
    # ── KHÔNG đòi, và mỗi dòng phải nói VÌ SAO ────────────────────────────────
    "int": "vô hướng — biến đếm/chỉ số/tạm. Đòi vẽ hết thì màn hình đầy thứ "
           "không phải nội dung bài, và cổng sẽ bị tắt vì kêu oan.",
    "float": "vô hướng — như `int`.",
    "bool": "vô hướng — cờ nội bộ. Nếu nó mang CÂU TRẢ LỜI thì đã bị luật "
            "witness bắt phải hiện, không cần luật thứ hai.",
    "str": "vô hướng — nhãn/kết quả dạng chữ. Cùng lý do với `bool`.",
    "node_ref": "con trỏ tới một đỉnh, không phải dữ liệu. Đường lên màn hình "
                "của nó là `pointers` binding, không phải một container.",
    "null": "vắng mặt của giá trị — không có gì để hiện.",
    # ── MIỀN HÌNH HỌC (2026-08-24) ───────────────────────────────────────────
    # Quyết định ở đây KHÔNG suy được từ miền cũ: một `array` biến động là cơ
    # chế bài đang dạy, còn một `point3` đứng yên vẫn là thứ học sinh phải nhìn
    # thấy suốt bài. Nên trục phân loại đổi từ "có biến động không" sang "có
    # phải đối tượng hình học đề cho / dựng ra không".
    "solid": "container",
    "polygon3": "container",
    "point3": "container",
    "line3": "container",
    "plane3": "container",
    "vector3": "vô hướng có hướng — phương/pháp tuyến là ĐẠI LƯỢNG TRUNG GIAN "
               "của phép dựng, không phải đối tượng học sinh cần thấy. Vẽ mọi "
               "pháp tuyến ra màn hình là lấp kín hình bằng mũi tên không ai "
               "đọc. Khi nó thật sự mang nghĩa (vector chỉ phương của một "
               "đường cần nêu) thì đường ấy đã là `line3` và đã phải hiện.",
}

#: Kiểu mà "đổi giá trị" nghĩa là DIỄN TIẾN. DẪN XUẤT từ bảng trên, không viết
#: tay lần thứ hai — hai danh sách rời nhau chắc chắn sẽ lệch.
CONTAINER_TYPES = frozenset(
    t for t, v in SURFACE_POLICY.items() if v == "container"
)

#: Mỗi kiểu phải-hiện đi được ra ÍT NHẤT MỘT visual primitive. Đây là vế thứ hai
#: của bất biến §1: *đã admit và biến động* ⇒ *biểu diễn được*. `map` từng vi
#: phạm đúng vế này suốt nhiều milestone — admit từ lâu, không primitive nào vẽ
#: được, nên mọi bài có đáp án là bảng đều chạy được mà không xem được.
TYPE_TO_PRIMITIVES: dict[str, tuple[str, ...]] = {
    "array": ("array_strip", "bar_chart", "table_grid"),
    "stack": ("stack_view",),
    "queue": ("queue_view",),
    "matrix": ("table_grid",),
    "map": ("map_view",),
    # `set` đi qua `array_strip`: adapter đã phẳng hoá `set` thành list. Thứ tự
    # do adapter sắp, không phải thứ tự chèn.
    "set": ("array_strip",),
    "graph": ("graph_view",),
    "tree_node": ("tree_element",),
}


class LearnerSurfaceResult(BaseModel):
    ok: bool
    error_code: str | None = None
    #: Mỗi mục là MỘT câu nói rõ cái gì không thấy được, để telemetry (§5) chỉ
    #: thẳng chỗ sửa thay vì báo "không phát được".
    invisible: list[str] = Field(default_factory=list)


def _bound_names(spec: SemanticProgramSpec) -> set[str]:
    """Mọi tên bộ nhớ có ÍT NHẤT MỘT đường lên màn hình."""
    vb = spec.visual_bindings
    if vb is None:
        return set()
    ra: set[str] = set()
    for cb in vb.containers or ():
        ra.add(cb.semantic_id)
        # `graph_view` tô trạng thái qua hai biến phụ — chúng cũng là đường lên
        # màn hình, nên biến được tham chiếu ở đây coi như đã hiện.
        for phu in (getattr(cb, "visited_ref", None), getattr(cb, "current_ref", None)):
            if phu:
                ra.add(phu)
    for pb in vb.pointers or ():
        ra.add(pb.var_ref)
    for box in vb.value_boxes or ():
        ra.add(box.var_ref)
    return ra


def _bien_dong(exec_res: SemanticExecutionResult, ten: str) -> bool:
    """Biến này có ĐỔI giá trị trong lượt chạy không?

    So bằng `repr` chứ không bằng `==`: giá trị có thể là list/dict lồng nhau, và
    một vài kiểu không so sánh trực tiếp được. `repr` đủ để trả lời câu hỏi duy
    nhất ở đây — *có khác đi không* — mà không cần biết kiểu.
    """
    thay: set[str] = set()
    for step in exec_res.trace:
        thay.add(repr((step.memory_snapshot or {}).get(ten)))
        if len(thay) > 1:
            return True
    return False


#: Khoá KHÔNG đi ra màn hình — định danh, kiểu, tham số hình học. Quét chúng chỉ
#: tạo dương tính giả.
#:
#: VÌ SAO LÀ DANH SÁCH LOẠI TRỪ, KHÔNG PHẢI DANH SÁCH CHO PHÉP: bản đầu chỉ soi
#: `items` và `value`, nên `entries` (map), `nodes`/`edges` (graph), ô của
#: `table_grid` — tất cả đều KHÔNG được quét. Với danh sách cho phép, mỗi
#: primitive mới lại lặng lẽ mở một lỗ; với danh sách loại trừ, primitive mới
#: được quét MẶC ĐỊNH và chỉ được miễn khi ai đó nói rõ nó là kỹ thuật. Sai lầm
#: an toàn phải nghiêng về phía bắt nhầm, không phải bỏ sót.
NON_LEARNER_KEYS = frozenset(
    {
        "id",
        "type",
        "primitive",
        "capacity",
        "target",
        "target_index",
        "highlight_indices",
        "highlighted_object_ids",
        "step_index",
        "semantic_id",
    }
)

#: Trong CÂU KỂ thì giá trị rò ra nằm giữa câu, nên phải khớp theo biên từ chứ
#: không so bằng nhau.
#: Biên TỪ, không phải biên "không-phải-dấu-chấm": bản đầu viết `(?![\w.])` nên
#: `"… là undefined."` — đúng dạng hay gặp nhất — trượt vì dấu chấm cuối câu.
_RX_TRONG_CAU = re.compile(
    r"\b(?:" + "|".join(re.escape(x) for x in PLACEHOLDER_LEAKS if x.isalnum()) + r")\b"
    r"|" + re.escape("[object Object]")
)


def _quet_sau(node: Any, duong: str, ra: list[str]) -> None:
    """Đi hết cây payload hiển thị, bắt chuỗi kỹ thuật ở MỌI độ sâu.

    Bắt lồng nhau là bắt buộc chứ không phải cho đẹp: một `entries` của map là
    `[[khoá, giá_trị], …]`, một `edges` của graph là `[[u, v], …]`. Chỉ nhìn
    tầng một thì giá trị hỏng nằm ở tầng hai đi qua tự do.
    """
    if isinstance(node, dict):
        for k, v in node.items():
            if k in NON_LEARNER_KEYS:
                continue
            _quet_sau(v, f"{duong}.{k}", ra)
    elif isinstance(node, (list, tuple)):
        for i, v in enumerate(node):
            _quet_sau(v, f"{duong}[{i}]", ra)
    elif isinstance(node, str):
        # So BẰNG NHAU cho một giá trị dữ liệu: chuỗi dữ liệu thật có thể chứa
        # chữ "null" như nội dung, và bắt nó là kêu oan.
        if node.strip() in PLACEHOLDER_LEAKS:
            ra.append(f'{duong}: "{node}"')
    # Số (kể cả 0) và bool đi qua: `0` THẬT là dữ liệu hợp lệ, và nuốt nó chính
    # là bẫy ngược chiều của `?? 0` mà kho này đã dính một lần.


def _ro_ri(envelope: dict[str, Any]) -> list[str]:
    """Chuỗi kỹ thuật lọt lên bề mặt học sinh, ở bất kỳ khung và độ sâu nào."""
    ra: list[str] = []
    for i, frame in enumerate(envelope.get("config", {}).get("frames", ()) or ()):
        for obj in frame.get("objects", ()) or ():
            _quet_sau(obj, f"khung{i}.{obj.get('id')}", ra)
        # Lời kể cũng là bề mặt học sinh, và là chỗ dễ rò nhất: một giá trị hỏng
        # được nội suy vào câu thì nằm GIỮA câu, không đứng một mình.
        for k in ("narration", "tier1_fact", "tier2_intent"):
            v = frame.get(k)
            if isinstance(v, str) and _RX_TRONG_CAU.search(v):
                ra.append(f"khung{i}.{k}: \"{v[:60]}\"")
    return sorted(set(ra))


def check_learner_surface(
    contract: RequestContract,
    spec: SemanticProgramSpec,
    exec_res: SemanticExecutionResult,
    envelope: dict[str, Any],
) -> LearnerSurfaceResult:
    """Chạy được RỒI, nhưng học sinh có thấy đủ để hiểu không?

    Chạy SAU `compile` vì nó cần envelope đã dựng: câu hỏi là về những khung sẽ
    thật sự được phát, không phải về ý định của chương trình.
    """
    thieu: list[str] = []
    da_bind = _bound_names(spec)

    # (1) Container BIẾN ĐỘNG mà không có đường lên màn hình.
    for decl in spec.memory_declarations:
        if decl.type not in CONTAINER_TYPES:
            continue
        if decl.name in da_bind:
            continue
        if _bien_dong(exec_res, decl.name):
            thieu.append(
                f"'{decl.name}' ({decl.type}) đổi giá trị trong lượt chạy nhưng "
                "không có binding nào — học sinh nghe kể về nó mà không thấy nó"
            )

    # (2) DỮ LIỆU ĐỀ CHO phải nhìn thấy được, dù nó có biến động hay không.
    #
    # VÌ SAO CẦN LUẬT RIÊNG: luật (1) chỉ chạm container BIẾN ĐỘNG, nên một dãy
    # chỉ-đọc — `arr` của bài tìm max, `chars` của bài đối xứng, `g` của bài BFS
    # — biến mất khỏi màn hình mà không ai kêu. Mà mất đầu vào thì học sinh
    # không còn gì để bám: con trỏ chạy trên một dãy vô hình, lời kể nói "so 45
    # với 89" trong khi trên hình không có số nào.
    #
    # Ma trận xuyên miền phơi ra chỗ này: gỡ binding của container đầu tiên mà
    # 6/7 lớp VẪN XANH. Một cổng để lọt sáu trên bảy ca là một cổng chưa chặn gì.
    #
    # Neo vào `source_fact_id` chứ không vào "có initial_value": bảng tra HẰNG
    # (`pairs`) cũng có giá trị khởi tạo mà không phải dữ liệu đề, và đòi nó
    # phải hiện là quay lại kêu oan. `source_fact_id` là chỗ chương trình TỰ KHAI
    # "cái này lấy từ đề", và đường sản phẩm bắt buộc phải khai (P2).
    # KHÔNG lọc theo `CONTAINER_TYPES` ở luật này — cố ý. Miễn trừ vô hướng ở
    # luật (1) là để tha biến ĐẾM/TẠM, không phải để tha dữ liệu đề. Bài "kiểm
    # tra bit thứ k của số n" có đầu vào là hai số; giấu chúng đi thì học sinh
    # xem một mô phỏng không biết đang xét số nào. `source_fact_id` phân biệt
    # được đúng hai loại đó, nên luật này neo vào nó chứ không neo vào kiểu.
    for decl in spec.memory_declarations:
        if not decl.source_fact_id:
            continue
        if decl.name not in da_bind:
            thieu.append(
                f"'{decl.name}' mang dữ liệu đề (mục '{decl.source_fact_id}') "
                "nhưng không có binding — học sinh không thấy đầu vào để theo dõi"
            )

    # (3) Chỗ chứa CÂU TRẢ LỜI phải nhìn thấy được.
    for ob in contract.obligations:
        witness = (ob.params or {}).get("witness")
        if witness and witness not in da_bind:
            thieu.append(
                f"witness '{witness}' của nghĩa vụ '{ob.kind}' không hiện trên "
                "màn hình — mô phỏng chạy xong mà học sinh không thấy đáp án"
            )

    # (3) Không có khung nào thì không có gì để xem, dù mọi tầng trên đều xanh.
    frames = envelope.get("config", {}).get("frames") or ()
    if not frames:
        thieu.append("envelope không có khung nào để trình bày")

    # (4) Giá trị kỹ thuật rò lên bề mặt.
    thieu.extend(_ro_ri(envelope))

    if thieu:
        return LearnerSurfaceResult(
            ok=False, error_code="LEARNER_SURFACE_INCOMPLETE", invisible=thieu
        )
    return LearnerSurfaceResult(ok=True)
