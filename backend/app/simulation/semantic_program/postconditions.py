# -*- coding: utf-8 -*-
"""C₂ — hậu điều kiện SERVER-OWNED, executable.

Chạy SAU execution, CHỈ trên nghĩa vụ đã qua C₁a **và** C₁b.

Ý NGHĨA CHÍNH XÁC CỦA `POSTCONDITION_VIOLATED` (spec §3.6): "hậu điều kiện
server-owned bị vi phạm". KHÔNG diễn giải thành "chứng minh AI hiểu sai đề" —
hậu điều kiện do LLM đề xuất mà vi phạm thì chỉ chứng minh chương trình TỰ MÂU
THUẪN, một kết luận yếu hơn hẳn. Oracle độc lập thật nằm ở đối chứng module
(§3.7) và held-out benchmark (§7.1).

VÌ SAO CHECKER Ở ĐÂY LÀ SERVER-OWNED THẬT: mỗi hàm dưới đây tính lại tính chất
bằng phép toán sơ cấp, TỪ DỮ LIỆU chứ không từ witness — witness chỉ được đem
SO, không bao giờ được dùng để suy ra đáp án.

MỘT NGOẠI LỆ VỀ NGUỒN DỮ LIỆU, ghi rõ vì nó là điểm thiết kế: mọi checker khác
đọc TRẠNG THÁI CUỐI, riêng `_predicate_verdict` phải tính lại từ CONTAINER ĐẦU
VÀO. Lý do: trạng thái cuối không chứng minh được một phán quyết — ngăn xếp rỗng
ở cuối cũng đúng với một chương trình không bao giờ push. Đây là ràng buộc về
*nguồn dữ liệu*, không phải nhượng bộ về tính độc lập; xem docstring
`obligations.py` để biết vì sao phản đối cũ với `predicate_verdict` không đứng.
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
    #: RÀNG BUỘC NGUỒN đã chạy qua một checker tất định — mẫu số của
    #: `SOURCE_CONSTRAINT_PRESERVATION_RATE`. Nghĩa vụ không có checker KHÔNG
    #: nằm ở đây: nó chưa từng được thi hành, nên đưa vào mẫu số là tính một
    #: phép kiểm chưa xảy ra.
    checked: list[str] = Field(default_factory=list)
    #: Trong `checked`, những cái checker nói ĐẠT. Tử số của cùng tỉ lệ ấy.
    #: `weak` nằm trong `checked` mà không nằm đây — đúng như nó phải thế.
    verified: list[str] = Field(default_factory=list)


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


def _huong_bat_buoc(ob: Obligation, hop_le: tuple[str, ...]) -> str:
    """`cmp` phải TƯỜNG MINH — thiếu thì NÉM, không đoán.

    Đo được trên DEV `dev_01` (tìm nhiệt độ cao nhất): nghĩa vụ `extremum` phát
    ra không kèm `cmp`, và nhánh cũ `max(seq) if cmp == "max" else min(seq)` âm
    thầm hiểu thành **min**, rồi báo:

        extremum(day, None): witness 'w' = 35, đúng phải là 27

    Chương trình ĐÚNG (35 là max thật) bị kết tội. Đây đúng lớp lỗi mà `_pred_of`
    ngay trên đã ghi bài học: **giá trị mặc định thầm lặng ở chỗ đáng lẽ
    fail-closed** — lớp ấy từng làm trượt 2 case đúng ở pilot 4.

    Thiếu hướng thì câu trả lời trung thực là *"tôi không kiểm được"* (mức yếu),
    KHÔNG phải *"chương trình sai"*. Hai câu đó khác nhau về bản chất, và trộn
    chúng là kết tội một chương trình đúng.

    ⚠️ CÒN SÓT CÙNG LỚP, khai để lần sau khỏi tưởng đã sạch:
    `derived_sequence.transform` mặc định `identity` và `aggregate_matching.op`
    mặc định `count`. Chưa đụng vì chưa đo được ca hỏng thật, và sửa mù thì đổi
    một lỗ lấy một lỗ khác.
    """
    v = ob.params.get("cmp")
    if v not in hop_le:
        raise KhongKiemChungDuoc(
            f"{ob.describe()}: thiếu hướng so sánh `cmp` "
            f"({'/'.join(hop_le)}) — không suy được từ kết quả, vì suy như thế "
            f"là để chương trình tự chấm chính nó"
        )
    return str(v)


def _extremum(snap: dict, ob: Obligation) -> str | None:
    huong = _huong_bat_buoc(ob, ("max", "min"))
    seq = _phang(snap.get(ob.container))
    if not seq:
        return f"extremum({ob.container}): container rỗng hoặc sai kiểu"
    want = max(seq) if huong == "max" else min(seq)
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
    # Cùng luật với `_extremum`: `asc` và `desc` là hai chiều NGƯỢC nhau, nên mặc
    # định thầm lặng sang `asc` sẽ kết tội mọi bài sắp giảm dần mà quên khai.
    huong = _huong_bat_buoc(ob, ("asc", "desc"))
    tang = huong == "asc"
    ok = all(
        (seq[i] <= seq[i + 1]) if tang else (seq[i] >= seq[i + 1])
        for i in range(len(seq) - 1)
    )
    return None if ok else (
        f"ordering({ob.container}, {huong}): dãy chưa đúng "
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


# ── VỊ TỪ KIỂM ĐƯỢC ────────────────────────────────────────────────────────
#
# ADMISSIBILITY ≠ VERIFIABILITY. `predicate_verdict` được KHAI cho mọi vị từ,
# nhưng chỉ vị từ có mặt ở đây mới được KIỂM. Vị từ lạ ⇒ `KhongKiemChungDuoc`
# ⇒ mức yếu ⇒ `verification_gap`: `executable=True`, `servable=False`.
#
# Đó là chỗ luật "LLM nói đáp án gì thì checker tin đáp án đó" bị chặn — và nó
# phải chặn được, nếu không việc mở kind này chỉ là hạ chuẩn cho một bài.

#: Cặp ngoặc chuẩn. Không lấy từ chương trình: chương trình tự khai bảng ghép
#: của nó thì checker mất tính độc lập ngay tại đây.
_CAP_NGOAC = {")": "(", "]": "[", "}": "{"}


def _can_bang_ngoac(chuoi: Any) -> bool:
    """Chuỗi/dãy ký tự ngoặc có cân bằng và lồng đúng thứ tự không?

    Một lượt quét với ngăn xếp — phép sơ cấp, chạy TRÊN DỮ LIỆU ĐỀ, không đọc
    witness và không đọc bất kỳ biến nào của chương trình. Cùng khuôn độc lập
    với `_extremum` (tính lại `max`) hay `_membership` (tính lại `in`).

    Ký tự KHÔNG phải ngoặc bị bỏ qua: đề thường cho cả chuỗi có chữ xen kẽ, và
    vị từ chỉ nói về quan hệ đóng-mở.
    """
    if isinstance(chuoi, str):
        day = list(chuoi)
    elif isinstance(chuoi, (list, tuple)):
        day = [str(x) for x in chuoi]
    else:
        raise KhongKiemChungDuoc("balanced_delimiters: đầu vào không phải chuỗi/dãy")

    ngan_xep: list[str] = []
    for c in day:
        if c in _CAP_NGOAC.values():
            ngan_xep.append(c)
        elif c in _CAP_NGOAC:
            if not ngan_xep or ngan_xep.pop() != _CAP_NGOAC[c]:
                return False
    return not ngan_xep


#: tên vị từ → hàm tính lại phán quyết TỪ DỮ LIỆU ĐỀ.
PREDICATE_CHECKERS: dict[str, Callable[[Any], bool]] = {
    "balanced_delimiters": _can_bang_ngoac,
}


def _predicate_verdict(snap: dict, ob: Obligation) -> str | None:
    """C₂ cho một phán quyết đúng/sai trên toàn bộ dữ liệu vào.

    KHÁC MỌI CHECKER KHÁC ở nguồn dữ liệu: không kiểm được từ TRẠNG THÁI CUỐI.
    Ngăn xếp rỗng ở cuối không chứng minh gì — một chương trình không bao giờ
    push cũng kết thúc rỗng. Nên checker tính lại từ chính container đầu vào.
    """
    # HAI CHỦ THỂ, hai đường kiểm. Chủ thể VÔ HƯỚNG ("n chẵn hay lẻ") đi qua tập
    # `_PREDS` sơ cấp; chủ thể TẬP HỢP ("chuỗi ngoặc có cân không") đi qua
    # `PREDICATE_CHECKERS`. Tách theo KIỂU THẬT của giá trị trong snapshot, không
    # theo khai báo — snapshot là thứ đã chạy.
    chu_the = snap.get(ob.container)
    if isinstance(chu_the, (int, float)) and not isinstance(chu_the, bool):
        return _predicate_verdict_vo_huong(snap, ob)

    ten = ob.params.get("pred")
    fn = PREDICATE_CHECKERS.get(ten)
    if fn is None:
        raise KhongKiemChungDuoc(
            f"predicate_verdict: chưa có bộ kiểm độc lập cho vị từ {ten!r}"
        )

    dau_vao = snap.get(ob.container)
    if dau_vao is None:
        return f"predicate_verdict({ob.container}): container không tồn tại"

    dung = fn(dau_vao)
    return _so_phan_quyet(ob, ten, dung, snap)


def _predicate_verdict_vo_huong(snap: dict, ob: Obligation) -> str | None:
    """Vị từ trên MỘT SỐ — "n chẵn hay lẻ", "n có lớn hơn ngưỡng không".

    Đi qua `_pred_of` để dùng lại tập `_PREDS` ĐÓNG và sơ cấp đã có từ trước,
    nên mở chiều vô hướng KHÔNG đẻ thêm checker nào. Vị từ ngoài tập ấy ném
    `KhongKiemChungDuoc` ⇒ mức yếu ⇒ `verification_gap`.
    """
    fn = _pred_of(ob)  # ném nếu `pred` lạ — fail-closed, không đoán
    x = snap.get(ob.container)
    if x is None:
        return f"predicate_verdict({ob.container}): biến không tồn tại"
    return _so_phan_quyet(ob, str(ob.params.get("pred")), bool(fn(x)), snap)


def _so_phan_quyet(ob: Obligation, ten: str, dung: bool, snap: dict) -> str | None:
    """Đọc witness thành phán quyết rồi SO với kết quả tính lại độc lập."""
    got = snap.get(ob.witness)

    # Witness phải là PHÁN QUYẾT, không phải một nhãn tuỳ ý. Chấp nhận `bool`
    # thật và cả nhãn tiếng Việt đã chuẩn hoá — bề mặt học sinh nói tiếng Việt,
    # nên chương trình đặt `result = "HỢP LỆ"` là hợp lý, không phải sai kiểu.
    if isinstance(got, bool):
        khai = got
    elif isinstance(got, str):
        t = got.strip().lower()
        if t in ("hợp lệ", "true", "đúng", "yes"):
            khai = True
        elif t in ("không hợp lệ", "false", "sai", "no"):
            khai = False
        else:
            return (
                f"predicate_verdict({ten}): witness '{ob.witness}' = {got!r} "
                "không phải một phán quyết đọc được"
            )
    else:
        return (
            f"predicate_verdict({ten}): witness '{ob.witness}' = {got!r}, "
            "phải là phán quyết đúng/sai"
        )

    return None if khai == dung else (
        f"predicate_verdict({ten}) trên '{ob.container}': witness "
        f"'{ob.witness}' = {khai}, tính lại độc lập ra {dung}"
    )


#: Số hạng của phép tích luỹ — mỗi phép là một biểu thức SƠ CẤP trên `k`.
_TERMS: dict[str, Callable[[int], Any]] = {
    "identity": lambda k: k,
    "square": lambda k: k * k,
    "cube": lambda k: k * k * k,
    "reciprocal": lambda k: 1 / k,
}


def _scalar_accumulation(snap: dict, ob: Obligation) -> str | None:
    """C₂ cho vòng lặp tích luỹ trên một BIÊN SỐ: `S = 1 + 2 + … + n`.

    ĐỘC LẬP THEO ĐÚNG NGHĨA ĐÃ DÙNG Ở KHẮP FILE NÀY: checker gấp lại tổng/tích
    từ **biên đề cho**, bằng một vòng lặp sơ cấp, không đọc witness để suy ra
    đáp án và không đánh giá biểu thức nào của chương trình.

    ĐÓNG là điều kiện của tính độc lập ấy: `op` và `term` đều lấy từ tập đóng.
    Mở cho một biểu thức bất kỳ thì checker buộc phải ĐÁNH GIÁ biểu thức của
    chương trình — tức chạy lại chính chương trình, và oracle mất nghĩa ngay
    tại đó. Số hạng ngoài tập ⇒ mức yếu, không phải kết tội.
    """
    from .obligations import AGGREGATE_OPS, TERM_TRANSFORMS

    op = ob.params.get("op")
    if op not in ("sum", "product"):
        raise KhongKiemChungDuoc(
            f"scalar_accumulation: `op` phải là sum/product (nhận {op!r}); "
            f"tập gộp đóng là {sorted(AGGREGATE_OPS)}"
        )
    term = ob.params.get("term", "identity")
    if term not in TERM_TRANSFORMS:
        raise KhongKiemChungDuoc(
            f"scalar_accumulation: số hạng {term!r} ngoài tập đóng "
            f"{sorted(TERM_TRANSFORMS)} — kiểm nó đòi đánh giá biểu thức của "
            f"chương trình, tức chạy lại chính nó"
        )

    n = snap.get(ob.container)
    if not isinstance(n, (int, float)) or isinstance(n, bool):
        return f"scalar_accumulation({ob.container}): biên không phải một số"
    n = int(n)

    tu = ob.params.get("from", 1)
    tu = int(tu) if isinstance(tu, (int, float)) and not isinstance(tu, bool) else 1
    if n < tu:
        return _nghia_vu_vo_hieu(ob)

    f = _TERMS[term]
    if term == "reciprocal" and tu <= 0:
        raise KhongKiemChungDuoc("scalar_accumulation: nghịch đảo với biên chứa 0")

    dung: Any = 0 if op == "sum" else 1
    for k in range(tu, n + 1):
        dung = dung + f(k) if op == "sum" else dung * f(k)

    got = snap.get(ob.witness)
    if not isinstance(got, (int, float)) or isinstance(got, bool):
        return (
            f"scalar_accumulation({op},{term}): witness '{ob.witness}' = {got!r}, "
            "phải là một số"
        )
    # Dung sai cho số thực: `1/2 + 1/3` tích luỹ theo thứ tự khác nhau cho sai
    # số bit khác nhau, và kết tội một chương trình vì bit cuối là kết tội sai.
    khop = abs(got - dung) < 1e-9 if isinstance(dung, float) or isinstance(got, float) else got == dung
    return None if khop else (
        f"scalar_accumulation({op},{term}) trên biên '{ob.container}'={n}: "
        f"witness '{ob.witness}' = {got!r}, tính lại độc lập ra {dung!r}"
    )


from .geometry_obligations import GEOMETRY_CHECKERS  # noqa: E402

CHECKERS: dict[str, Callable[[dict, Obligation], str | None]] = {
    "predicate_verdict": _predicate_verdict,
    "scalar_accumulation": _scalar_accumulation,
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
    #
    # ── MIỀN HÌNH HỌC: tám checker, KHÔNG cái nào ở mức yếu ─────────────────
    # Khác hẳn miền Tin học, nơi `predicate_verdict` phải để mức yếu vì kiểm nó
    # đòi cài lại chính thuật toán đang kiểm. Ở hình học, kiểm là một PHÉP TÍNH
    # giải tích (`u·v == 0`), không phải một lời giải — nên tính độc lập không
    # mất. Xem `geometry_obligations.py`.
    **GEOMETRY_CHECKERS,
}


ERR_NGUON_BI_VI_PHAM = "NORMALIZED_SOURCE_VIOLATED"


class SourceInvariantResult(BaseModel):
    """Kết quả `NormalizedSourceInvariantGate` — bốn con số, không gộp.

    `not_checkable` tách hẳn khỏi `violated`: *"tôi không dựng lại được phép
    kiểm này"* và *"chương trình dựng sai hình"* là hai câu khác nhau, và gộp
    chúng là kết tội oan — đúng lỗi đã phải viết ba bản đính chính.
    """

    ok: bool
    error_code: str | None = None
    checked: int = 0
    passed: int = 0
    violated: list[str] = Field(default_factory=list)
    not_checkable: list[str] = Field(default_factory=list)


def check_source_invariants(
    contract: RequestContract, exec_result, ten_da_hoa_giai=None
) -> SourceInvariantResult:
    """Hình dựng ra có thoả DỮ KIỆN ĐỀ CHO không — hỏi trên trạng thái cuối.

    ─── VÌ SAO CẦN, QUAN SÁT ĐƯỢC Ở `wave6-canary-b/w3-thang` ──────────────

    Hợp đồng đã chốt `AB = 1`, `SA = 4/5`. Chương trình dựng
    `A(−16,0,0) B(9,0,0) S(0,0,12)` — tức `AB = 25`, `SA = 20`. Hình **đúng**
    về quan hệ, **sai** về thang, và học sinh đọc `12` cho bài có đáp án
    `12a/25`.

    Không cổng nào bắt được, vì các điểm ấy đi qua kênh tự do hệ trục
    (`model_assumption`) nên chẳng ghim về mục dữ kiện nào. Ở một lượt khác
    cùng đề, mô hình CÓ ghim và bị bắt — tức phép bắt đang phụ thuộc **trí nhớ
    của mô hình**, không phải một bất biến.

    ─── VÌ SAO KHÔNG ĐỌC `source_fact_id` ─────────────────────────────────

    Đó chính là chỗ hỏng. Cổng chạy trên `contract.source_invariants` — dữ
    liệu **server tự phát từ câu văn của đề** — nên không có đường nào để một
    chương trình tránh bị kiểm bằng cách im lặng. `source_fact_id` của mô hình
    chỉ dùng khi VIẾT LỜI GIẢI THÍCH.

    ─── SO BẰNG BÌNH PHƯƠNG, KHÔNG KHAI CĂN ───────────────────────────────

    `distance_sq(A,B) == q²` với `q` hữu tỉ. Khai căn thì `AB = √2` không biểu
    diễn được và cổng sẽ phải bó tay ở đúng những bài phổ biến nhất; so bình
    phương thì phép kiểm luôn nằm trong `Fraction`. Không `float`, không dung sai.
    """
    from fractions import Fraction

    from app.simulation.geometry.exact import Vec3
    from app.simulation.geometry.measure import distance_sq

    snap = _final(exec_result)
    doi = ten_da_hoa_giai or {}
    vi_pham: list[str] = []
    khong_kiem: list[str] = []
    dat = 0

    for bt in contract.source_invariants or ():
        if bt.kind != "segment_length":
            khong_kiem.append(f"{bt.source_text}: chưa có checker cho '{bt.kind}'")
            continue
        # THẨM QUYỀN VỀ TÊN dùng chung, không viết lưới hoà giải thứ chín.
        diem = []
        for ten in bt.points:
            v = snap.get(ten)
            if v is None and ten in doi:
                v = snap.get(doi[ten])
            diem.append(v)
        if not all(isinstance(v, Vec3) for v in diem):
            khong_kiem.append(
                f"{bt.source_text}: không tìm đủ hai điểm {list(bt.points)} "
                "trong trạng thái cuối")
            continue
        try:
            q = Fraction(bt.expected)
        except (ValueError, ZeroDivisionError):
            khong_kiem.append(f"{bt.source_text}: '{bt.expected}' không hữu tỉ")
            continue
        that = distance_sq(diem[0], diem[1])
        if that == q * q:
            dat += 1
        else:
            vi_pham.append(
                f"{bt.source_text}: đề cho {bt.expected}, hình dựng có "
                f"{bt.points[0]}{bt.points[1]}² = {that} (cần {q * q})")

    n = dat + len(vi_pham) + len(khong_kiem)
    return SourceInvariantResult(
        ok=not vi_pham,
        error_code=ERR_NGUON_BI_VI_PHAM if vi_pham else None,
        checked=n, passed=dat, violated=vi_pham, not_checkable=khong_kiem,
    )


def check_postconditions(
    contract: RequestContract, spec, exec_result, ten_da_hoa_giai=None
) -> PostconditionResult:
    """Kiểm mọi nghĩa vụ CÓ checker server-owned. Không có ⇒ bỏ qua.

    Bỏ qua ở đây KHÔNG phải khoan dung: nghĩa vụ không có checker đã bị C₁a xử
    bằng `SEMANTIC_VERIFICATION_UNAVAILABLE` (mức yếu). Kết tội nó lần nữa dưới
    nhãn "vi phạm hậu điều kiện" là nói sai bản chất.
    """
    snap = _final(exec_result)
    # ─── DÙNG LẠI ÁNH XẠ CỦA C₁a, KHÔNG HOÀ GIẢI LẦN THỨ HAI ────────────────
    #
    # C₁a đã trả lời câu *"tên này của hợp đồng là vật nào trong chương trình"*.
    # Viết bản thứ hai ở đây là hai nguồn sự thật, và chúng SẼ trôi khỏi nhau.
    #
    # Đo được ở lượt smoke 2026-08-25: C₁a nối `AD ≡ line_AD` rồi cho qua; C₂
    # tra thẳng `AD`, không thấy, và báo *"cần một `line3` và một `point3`"* —
    # trong khi bộ nhớ có ĐÚNG một `line3` (`line_AD`) và ĐÚNG một `point3`
    # (`Q`). Học sinh đọc ra "chương trình tự mâu thuẫn với nghĩa vụ nó tự
    # khai": một lời vu oan sinh ra từ một lưới nửa vời.
    #
    # BÍ DANH, không ghi đè: tên chương trình vẫn nguyên trong `snap`, chỉ thêm
    # lối vào theo tên hợp đồng. Không checker nào duyệt `snap`, nên thêm khoá
    # là an toàn — và nếu mai có checker duyệt, nó vẫn thấy đúng các giá trị.
    for ten_hd, ten_ct in (ten_da_hoa_giai or {}).items():
        if ten_hd not in snap and ten_ct in snap:
            snap[ten_hd] = snap[ten_ct]
    violations: list[str] = []
    weak: list[str] = []
    da_kiem: list[str] = []
    da_dat: list[str] = []
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
        da_kiem.append(ob.describe())
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
        else:
            da_dat.append(ob.describe())

    dem = {"checked": da_kiem, "verified": da_dat}
    if violations:
        return PostconditionResult(
            ok=False, error_code="POSTCONDITION_VIOLATED",
            violations=violations, weak_kinds=sorted(set(weak)), **dem,
        )
    if weak:
        return PostconditionResult(
            ok=False, error_code="SEMANTIC_VERIFICATION_UNAVAILABLE",
            weak_kinds=sorted(set(weak)), **dem,
        )
    return PostconditionResult(ok=True, **dem)
