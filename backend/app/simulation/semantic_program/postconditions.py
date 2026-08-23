# -*- coding: utf-8 -*-
"""C₂ — hậu điều kiện SERVER-OWNED, executable.

Chạy SAU execution, CHỈ trên nghĩa vụ đã qua C₁a **và** C₁b.

Ý NGHĨA CHÍNH XÁC CỦA `POSTCONDITION_VIOLATED` (spec §3.6): "hậu điều kiện
server-owned bị vi phạm". KHÔNG diễn giải thành "chứng minh AI hiểu sai đề" —
hậu điều kiện do LLM đề xuất mà vi phạm thì chỉ chứng minh chương trình TỰ MÂU
THUẪN, một kết luận yếu hơn hẳn. Oracle độc lập thật nằm ở đối chứng module
(§3.7) và held-out benchmark (§7.1).

VÌ SAO CHECKER Ở ĐÂY LÀ SERVER-OWNED THẬT: mỗi hàm dưới đây tính lại tính chất
TỪ TRẠNG THÁI CUỐI, bằng phép toán sơ cấp — KHÔNG cài lại thuật toán của chương
trình. Nghĩa vụ nào chỉ kiểm được bằng cách cài lại chính thuật toán đang kiểm
thì đã bị loại khỏi taxonomy từ đầu (`predicate_verdict`), vì lúc đó oracle mất
tính độc lập.
"""
from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, Field

from .obligations import Obligation
from .request_contract import RequestContract


class PostconditionResult(BaseModel):
    ok: bool
    error_code: str | None = None
    violations: list[str] = Field(default_factory=list)
    #: Nghĩa vụ mà checker KHÔNG biểu diễn được ⇒ mức yếu (`verification_gap`).
    #: Tách hẳn khỏi `violations`: "tôi không biết" ≠ "chương trình sai".
    weak_kinds: list[str] = Field(default_factory=list)


def _final(exec_result) -> dict[str, Any]:
    trace = getattr(exec_result, "trace", ()) or ()
    return trace[-1].memory_snapshot if trace else {}


def _phang(value: Any) -> list[Any]:
    """Ma trận trải phẳng để đếm/so cực trị dùng chung một đường."""
    if not isinstance(value, (list, tuple)):
        return []
    if value and isinstance(value[0], (list, tuple)):
        return [x for row in value for x in row]
    return list(value)


_PREDS: dict[str, Callable[[Any, Any], bool]] = {
    "even": lambda x, _: isinstance(x, int) and x % 2 == 0,
    "odd": lambda x, _: isinstance(x, int) and x % 2 == 1,
    "gt": lambda x, t: x > t,
    "ge": lambda x, t: x >= t,
    "lt": lambda x, t: x < t,
    "le": lambda x, t: x <= t,
    "eq": lambda x, t: x == t,
    "any": lambda x, _: True,
}


class KhongKiemChungDuoc(Exception):
    """Checker KHÔNG biểu diễn được thứ nghĩa vụ đòi ⇒ mức yếu, không phải vi phạm.

    Tách hẳn khỏi "vi phạm" vì hai câu trả lời khác nhau về bản chất: một cái
    nói *chương trình sai*, cái kia nói *tôi không biết*. Trộn chúng là kết tội
    một chương trình đúng.
    """


def _pred_of(ob: Obligation) -> Callable[[Any], bool]:
    """Vị từ lọc của nghĩa vụ. Không biểu diễn được ⇒ NÉM, không đoán.

    TỪNG SAI VÀ SAI ĐẮT (đo được ở lượt pilot 4): bản cũ mặc định về `any` khi
    `pred` lạ. Với `aggregate_matching(count)` thì "đếm mọi phần tử" chính là
    `len(container)`, nên checker bịa ra một kỳ vọng bằng đúng số phần tử rồi
    kết tội chương trình:

        đếm cặp nghịch đảo [3,2,1,5,4]  → hệ 4 (ĐÚNG), checker đòi 5
        đếm bạn cao hơn TB (8 số đo)     → hệ 4 (ĐÚNG), checker đòi 8

    Hai case đúng bị từ chối. Đây là cùng một lớp lỗi đã lặp nhiều lần trong dự
    án: **giá trị mặc định thầm lặng ở chỗ đáng lẽ fail-closed.**

    Vắng `pred` KHÁC với `pred` lạ: đề chỉ nói "đếm số phần tử" thì không có vị
    từ nào, và đếm tất cả là ĐÚNG. Chỉ khi đề khai một vị từ mà bảng không có
    mới là không kiểm chứng được.
    """
    raw = ob.params.get("pred")
    if raw is None:
        fn = _PREDS["any"]
    else:
        fn = _PREDS.get(str(raw))
        if fn is None:
            raise KhongKiemChungDuoc(
                f"vị từ '{raw}' không nằm trong tập kiểm được "
                f"({', '.join(sorted(_PREDS))})"
            )
    nguong = ob.params.get("threshold", ob.params.get("value"))
    return lambda x: bool(fn(x, nguong))


def _co_ast_chua_tinh(value: Any) -> bool:
    """Trạng thái có chứa NODE BIỂU THỨC chưa được tính không?

    `sealed_038` của lượt pilot 4: chương trình đẩy nguyên object biểu thức vào
    mảng thay vì giá trị của nó —

        [{"kind": "index", "container": "day_so_a",
          "index": {"kind": "var", "name": "i"}}, … lặp 6 lần]

    Validator, P2, C₁a, C₁b và C₂ đều cho qua, nên hệ TỰ CHO LÀ PHÁT ĐƯỢC một
    kết quả là rác. Kiểm hình thức của container mà không nhìn vào PHẦN TỬ thì
    không bắt được điều đó.
    """
    if isinstance(value, dict):
        return "kind" in value or any(_co_ast_chua_tinh(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(_co_ast_chua_tinh(v) for v in value)
    return False


def _nghia_vu_vo_hieu(ob: Obligation) -> str:
    """Container của nghĩa vụ RỖNG ⇒ nghĩa vụ không nói được gì về lượt chạy.

    Vì sao phải có thông điệp riêng: với `sum`/`count`/`product`, tập rỗng vẫn
    cho ra một giá trị "đúng" (0, 0, 1). Checker khi ấy so witness với con số
    ấy và báo *"witness 's' = 15, đúng phải là 0"* — đọc y như "đáp án của bạn
    sai". Trên SEALED `7e5df014…` case `T11CS-C6-041` bị đúng câu đó trong khi
    oracle độc lập xác nhận 15 ĐÚNG.

    Đây KHÔNG phải lối thoát cho C₂: hàm chỉ đổi CÁCH NÓI, vi phạm vẫn là vi
    phạm và `servable` vẫn False. Container có dữ liệu thì không đi qua đây.
    """
    return (
        f"{ob.describe()}: nghĩa vụ VÔ HIỆU — container '{ob.container}' rỗng, "
        f"chương trình chưa từng ghi dữ liệu vào nó. Không kết luận được gì về "
        f"witness '{ob.witness}'; nghĩa vụ này khai sai chỗ chứ không phải kết "
        f"quả sai."
    )


def _extremum(snap: dict, ob: Obligation) -> str | None:
    seq = _phang(snap.get(ob.container))
    if not seq:
        return f"extremum({ob.container}): container rỗng hoặc sai kiểu"
    want = max(seq) if ob.params.get("cmp") == "max" else min(seq)
    got = snap.get(ob.witness)
    return None if got == want else (
        f"extremum({ob.container}, {ob.params.get('cmp')}): witness "
        f"'{ob.witness}' = {got!r}, đúng phải là {want!r}"
    )


def _aggregate_matching(snap: dict, ob: Obligation) -> str | None:
    seq = _phang(snap.get(ob.container))
    # Chặn TRƯỚC khi gộp: `sum([])`/`len([])`/tích rỗng đều ra một con số trông
    # như đáp án đúng, và đó là nguồn của thông điệp gây hiểu nhầm.
    if not seq:
        return _nghia_vu_vo_hieu(ob)
    khop = [x for x in seq if _pred_of(ob)(x)]
    op = str(ob.params.get("op") or "count")
    if op == "count":
        want: Any = len(khop)
    elif op == "sum":
        want = sum(khop)
    elif op == "product":
        want = 1
        for x in khop:
            want *= x
    elif op in ("max", "min"):
        if not khop:
            return f"aggregate_matching({ob.container}): không phần tử nào thoả"
        want = max(khop) if op == "max" else min(khop)
    else:
        return f"aggregate_matching({ob.container}): phép gộp lạ '{op}'"

    got = snap.get(ob.witness)
    return None if got == want else (
        f"aggregate_matching({ob.container}, {op}): witness '{ob.witness}' = "
        f"{got!r}, đúng phải là {want!r}"
    )


def _ordering(snap: dict, ob: Obligation) -> str | None:
    seq = snap.get(ob.witness if ob.witness in snap else ob.container)
    if not isinstance(seq, (list, tuple)):
        return f"ordering({ob.container}): sai kiểu"
    tang = ob.params.get("cmp", "asc") == "asc"
    ok = all(
        (seq[i] <= seq[i + 1]) if tang else (seq[i] >= seq[i + 1])
        for i in range(len(seq) - 1)
    )
    return None if ok else (
        f"ordering({ob.container}, {ob.params.get('cmp', 'asc')}): dãy chưa đúng "
        f"thứ tự — {list(seq)!r}"
    )


def _membership(snap: dict, ob: Obligation) -> str | None:
    box = snap.get(ob.container)
    if box is None:
        return f"membership({ob.container}): container không tồn tại"
    # Cùng lý do với `_aggregate_matching`: "x phải có mặt" trong một container
    # RỖNG không phải phát hiện về thuật toán, nó là nghĩa vụ chưa có dữ liệu.
    if isinstance(box, (list, tuple, set, dict, str)) and len(box) == 0:
        return _nghia_vu_vo_hieu(ob)
    item = ob.params.get("item")
    mong = bool(ob.params.get("expected", True))
    try:
        co = item in box
    except TypeError:
        return f"membership({ob.container}): không kiểm được quan hệ thuộc"
    return None if co == mong else (
        f"membership({ob.container}): {item!r} "
        f"{'phải' if mong else 'không được'} có mặt"
    )


def _first_match_index(snap: dict, ob: Obligation) -> str | None:
    seq = _phang(snap.get(ob.container))
    hop = _pred_of(ob)
    want = next((i for i, x in enumerate(seq) if hop(x)), None)
    got = snap.get(ob.witness)
    if want is None:
        return None if got in (None, -1) else (
            f"first_match_index({ob.container}): không phần tử nào thoả nhưng "
            f"witness '{ob.witness}' = {got!r}"
        )
    return None if got == want else (
        f"first_match_index({ob.container}): witness '{ob.witness}' = {got!r}, "
        f"vị trí ĐẦU TIÊN thoả là {want!r}"
    )


def _total_mapping(snap: dict, ob: Obligation) -> str | None:
    m = snap.get(ob.container)
    if not isinstance(m, dict):
        return f"total_mapping({ob.container}): không phải bảng ánh xạ"
    mien = ob.params.get("domain")
    nguon = snap.get(mien) if isinstance(mien, str) else None
    if nguon is None:
        return None  # không khai miền ⇒ chỉ kiểm được tới đây
    thieu = sorted({str(k) for k in _phang(nguon)} - {str(k) for k in m})
    return None if not thieu else (
        f"total_mapping({ob.container}): thiếu khoá {thieu!r}"
    )


def _derived_sequence(snap: dict, ob: Obligation) -> str | None:
    # NGUỒN: `params.src` nếu có, NGƯỢC LẠI là `ob.container`.
    #
    # Trước 2026-08-23 chỉ đọc `params.src`. Nghĩa vụ nào khai container mà không
    # khai `src` (LLM khai `derived_sequence(container='day_so',
    # witness='day_so_dao_nguoc')` — đúng hình dạng taxonomy) thì `snap.get("")`
    # ra None, `_phang` ra `[]`, `transform` mặc định `identity` cho `want = []`,
    # rồi so với một witness cũng `[]` và **CHO QUA**.
    #
    # Đo được trên đường sản phẩm (probe E2E `serve`, đề "đảo dãy bằng ngăn
    # xếp"): envelope PHÁT ĐI có khung cuối `ngan_xep.items = []`,
    # `day_so_dao_nguoc.items = []` — mô phỏng chạy 5 bước, không gì đổi, đáp án
    # không bao giờ hiện, mà `servable = True`. Đây là chiều IM LẶNG CHẤP NHẬN
    # của cùng lớp "nghĩa vụ vô hiệu" mà `T11CS-C6-041` phơi ra ở chiều tố cáo
    # sai — và chiều này nguy hiểm hơn, vì nó không kêu lên.
    ten_src = str(ob.params.get("src") or ob.container or "")
    src = _phang(snap.get(ten_src))
    dest = _phang(snap.get(ob.witness))
    # Chặn TRƯỚC khi biến đổi: mọi phép trên tập rỗng đều ra tập rỗng, nên witness
    # rỗng khớp một cách vô nghĩa. Cùng chốt mà `_aggregate_matching` đã có.
    if not src:
        return _nghia_vu_vo_hieu(ob)
    phep = str(ob.params.get("transform") or "identity")
    if phep == "reverse":
        want = list(reversed(src))
    elif phep == "identity":
        want = list(src)
    elif phep == "distinct":
        seen: list[Any] = []
        for x in src:
            if x not in seen:
                seen.append(x)
        want = seen
    elif phep == "filter":
        want = [x for x in src if _pred_of(ob)(x)]
    else:
        return None  # `map` cần hàm biến đổi — chưa khai được trong IR hiện tại
    return None if dest == want else (
        f"derived_sequence({ob.witness}, {phep}): = {dest!r}, đúng phải là {want!r}"
    )


def _reachability(snap: dict, ob: Obligation) -> str | None:
    g = snap.get(ob.container)
    if not isinstance(g, dict):
        return f"reachability({ob.container}): không phải đồ thị"
    src = ob.params.get("src")
    if src is None:
        return None
    # BFS ĐỘC LẬP — vài dòng phép toán trên đồ thị, không phải cài lại chương
    # trình đang kiểm (chương trình có thể dùng DFS, hàng đợi, đệ quy…).
    tham: set[Any] = set()
    hang = [src]
    while hang:
        u = hang.pop(0)
        if u in tham:
            continue
        tham.add(u)
        hang.extend(g.get(u, []) or [])
    got = snap.get(ob.witness)
    if got is None:
        return None
    thuc = {str(x) for x in (got if isinstance(got, (list, tuple, set)) else [got])}
    return None if thuc == {str(x) for x in tham} else (
        f"reachability({ob.container}, từ {src!r}): tập đến được là "
        f"{sorted(str(x) for x in tham)!r}, witness cho {sorted(thuc)!r}"
    )


CHECKERS: dict[str, Callable[[dict, Obligation], str | None]] = {
    "extremum": _extremum,
    "aggregate_matching": _aggregate_matching,
    "ordering": _ordering,
    "membership": _membership,
    "first_match_index": _first_match_index,
    "total_mapping": _total_mapping,
    "derived_sequence": _derived_sequence,
    "reachability": _reachability,
    # `structural_traversal` chưa có checker: kiểm nó cần cấu trúc cây trong
    # snapshot ở dạng duyệt được, mà IR hiện lưu `tree_node` dạng lồng nhau —
    # để đó còn hơn dựng một checker chỉ đúng với một hình dạng cây.
}


def check_postconditions(
    contract: RequestContract, spec, exec_result
) -> PostconditionResult:
    """Kiểm mọi nghĩa vụ CÓ checker server-owned. Không có ⇒ bỏ qua.

    Bỏ qua ở đây KHÔNG phải khoan dung: nghĩa vụ không có checker đã bị C₁a xử
    bằng `SEMANTIC_VERIFICATION_UNAVAILABLE` (mức yếu). Kết tội nó lần nữa dưới
    nhãn "vi phạm hậu điều kiện" là nói sai bản chất.
    """
    snap = _final(exec_result)
    violations: list[str] = []
    weak: list[str] = []
    for ob in contract.obligations:
        # Kiểm TRƯỚC mọi checker, cho MỌI nghĩa vụ: trạng thái chứa node biểu
        # thức chưa được tính là rác, bất kể kind là gì. Để từng checker tự lo
        # thì mỗi checker mới lại là một lỗ (xem `_co_ast_chua_tinh`).
        for ten in (ob.container, ob.witness):
            if ten and _co_ast_chua_tinh(snap.get(ten)):
                violations.append(
                    f"{ob.describe()}: biến '{ten}' chứa node biểu thức CHƯA "
                    "ĐƯỢC TÍNH, không phải giá trị"
                )

        fn = CHECKERS.get(ob.kind)
        if fn is None:
            continue
        try:
            msg = fn(snap, ob)
        except KhongKiemChungDuoc as e:
            # KHÔNG phải vi phạm: checker tự nhận là không biểu diễn được.
            weak.append(ob.kind)
            continue
        except (TypeError, ValueError, KeyError) as e:
            msg = f"{ob.describe()}: không kiểm được hậu điều kiện ({e})"
        if msg:
            violations.append(msg)

    if violations:
        return PostconditionResult(
            ok=False, error_code="POSTCONDITION_VIOLATED",
            violations=violations, weak_kinds=sorted(set(weak)),
        )
    if weak:
        return PostconditionResult(
            ok=False, error_code="SEMANTIC_VERIFICATION_UNAVAILABLE",
            weak_kinds=sorted(set(weak)),
        )
    return PostconditionResult(ok=True)
