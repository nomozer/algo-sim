# -*- coding: utf-8 -*-
"""NÂNG biểu thức lồng ở một ô toán hạng TÊN — tiền-chuẩn-tắc, TRƯỚC schema.

─── LỖ NÓ BỊT, ĐO ĐƯỢC Ở FRESH_TRANSLATION_COMPOSITION_PROBE ──────────────

2/4 lượt tổng hợp đầu tiên chết ở schema, và **cả hai là cùng một thứ**:

    {"kind": "translate", "point": "B",
     "vector": {"kind": "vector_from_points", "from_point": "A", "to_point": "D"}}

Ý định dựng hình **đúng hoàn toàn** — đúng phép, đúng toán hạng, đúng thứ tự
phụ thuộc. Sai đúng một điều: `vector` phải là một TÊN. 5 lần trên 4 đề, và một
lượt sửa cục bộ đủ cho cả hai ca.

Ràng buộc *"mọi toán hạng hình học là TÊN"* là bất biến R0
(`test_R0_bieu_thuc_hinh_hoc_chi_nhan_TEN`), và **không được nới**: nhận cấu
trúc ở đó là mở đường cho toạ độ đi thẳng từ LLM vào bộ nhớ hình học. Nhưng nó
đã có mặt trong thẻ văn phạm (`vector:tên`) VÀ trong prompt (*"không nhận biểu
thức lồng"*), và mô hình vẫn lồng. Nói to hơn không phải là một phép sửa.

⇒ Nên chỗ sửa là ở đây: một lớp **chuẩn hoá tiện dụng** chạy trước khi schema
kiểm, biến dạng lồng thành đúng dạng chuẩn tắc mà mô hình lẽ ra phải viết.

    translate(A, vector_from_points(B,D))

    ── nâng ──▸  assign  _tam_1 = vector_from_points(B,D)
                construct_point Q = translate(A, "_tam_1")

Sau lớp này, IR canonical vẫn thoả *mọi toán hạng hình học là TÊN*. R0 không bị
nới một li — nó được **giữ bằng một phép biến đổi tất định** thay vì bằng một
lời dặn mà mô hình không nghe.

─── VÌ SAO ĐÂY KHÔNG PHẢI CỬA SAU CỦA CỔNG TRUNG THỰC ────────────────────

Vì thứ được nâng phải **đã nằm trong văn phạm biểu thức**. Nâng một biểu thức
DỰNG là đổi chỗ viết của một phép dựng; nhận một mảng toạ độ thì mới là tự đăng
ký một giá trị mô hình bịa ra. Bốn điều kiện ở `_an_toan` canh đúng ranh ấy, và
`translate(A, [1,2,3])` vẫn chết — nay chết kèm một lời chỉ đường.

─── TỔNG QUÁT, KHÔNG RIÊNG `translate` ───────────────────────────────────

Bảng ô TÊN dẫn từ `_CHU_KY` · `_TOAN_HANG_LENH` · `_KIEU_DO`, nên một phép
tương lai có toán hạng `NAME<vector3>` tự hưởng cùng luật, không ai phải nhớ.
Không có một dòng nào hỏi *"đây có phải `translate` không"*.
"""
from __future__ import annotations

from typing import Any

from .ir_static_check import (
    DIEM, _CHU_KY, _KIEU_DO, _TOAN_HANG_LENH, _DOI_TUONG,
)

#: Tiền tố tên do SERVER sinh. Mô hình không sở hữu, không nhắc tới, và không
#: có cách nào phát ra một tên như thế mà không bị đổi (xem `_ten_tam`).
#:
#: Gạch dưới đứng đầu: không tên hình học nào của SGK bắt đầu như vậy, nên đây
#: vừa là chỗ tránh va chạm vừa là dấu hiệu *"vật này do hệ dựng"* mà tầng
#: trình bày đọc được (§13 — `scene3d._nhom` phát nhóm `internal`).
TIEN_TO_TAM = "_tam_"

#: Ô toán hạng đòi một TÊN, theo `kind`. DẪN XUẤT — thêm một biểu thức vào
#: `_CHU_KY` là bảng này tự dài ra.
#:
#: `measure` không có ở đây: kiểu toán hạng của nó phụ thuộc `quantity`, nên nó
#: được tra thẳng từ `_KIEU_DO` lúc duyệt (`_o_cua`).
O_TEN: dict[str, dict[str, tuple[tuple[str, ...], bool]]] = {
    **{k: {truong: (kieu, False) for truong, kieu in thamso}
       for k, (thamso, _) in _CHU_KY.items()},
    **{k: {truong: (kieu, la_ds) for truong, kieu, la_ds in ts}
       for k, ts in _TOAN_HANG_LENH.items()},
}

#: Vì sao một biểu thức lồng KHÔNG được nâng. Mỗi mã là một phép sửa khác nhau.
LY_DO_TU_CHOI = {
    "NESTED_NAME_REF": "tham chiếu `var` — biên cấp trường gỡ bọc, không cần temp",
    "NESTED_RAW_LITERAL": "giá trị thô (toạ độ/mảng/literal), không phải phép dựng",
    "NESTED_UNKNOWN_KIND": "`kind` không có trong văn phạm biểu thức hình học",
    "NESTED_WRONG_TYPE": "phép dựng trả về kiểu khác kiểu ô này nhận",
    "NESTED_CARRIES_ASSUMPTION": "mang `model_assumption` — giả định phải khai ở điểm gốc",
    "NESTED_TOO_DEEP": "lồng sâu quá giới hạn tất định",
}

#: Thân của một câu lệnh có nhánh. Temp KHÔNG được vượt qua ranh giới này.
_NHANH = ("body", "then_body", "else_body")

#: Trần độ sâu đệ quy (§10). Không phải giới hạn kỹ thuật mà là **ranh giới
#: tất định**: mỗi bậc sinh một temp, và một cây lồng sâu hơn thế chưa từng
#: được quan sát ở bất kỳ artifact live nào (đo được: sâu nhất là 1).
SAU_TOI_DA = 4


def _la_gia_tri_tho(v: Any) -> bool:
    """Toạ độ/mảng/literal — thứ TUYỆT ĐỐI không được thành một thực thể ngầm."""
    if isinstance(v, (list, tuple, int, float, bool)):
        return True
    return isinstance(v, dict) and v.get("kind") in (None, "literal", "var")


def _o_cua(node: Any) -> dict[str, tuple[tuple[str, ...], bool]]:
    """Các ô TÊN của một nút, kể cả `measure` (kiểu tuỳ `quantity`)."""
    k = node.get("kind") if isinstance(node, dict) else None
    if k == "measure":
        of, wrt = _KIEU_DO.get(node.get("quantity", ""), (_DOI_TUONG, _DOI_TUONG))
        ra = {"of": (of, False)}
        if wrt:
            ra["wrt"] = (wrt, False)
        return ra
    return O_TEN.get(k, {})


def _la_tham_chieu(v: Any) -> bool:
    """`{"kind":"var","name":X}` — chính cái TÊN, viết dài ra."""
    return (isinstance(v, dict) and v.get("kind") == "var"
            and isinstance(v.get("name"), str) and bool(v["name"]))


def _an_toan(v: Any, nhan: tuple[str, ...]) -> str | None:
    """`None` nếu nâng được; ngược lại MÃ lý do. Bốn câu hỏi của §5."""
    if _la_tham_chieu(v):
        # KHÔNG nâng, và cũng không phải một lời từ chối: `var` không cần một
        # temp nào cả — nó đã là một tên. `contract.canonical_geometry_name`
        # gỡ bọc nó ở biên cấp TRƯỜNG. Trả một mã riêng để bộ audit đừng đếm
        # nó chung với toạ độ thô: gộp hai thứ ấy là báo cáo sai chuyện gì
        # đang thật sự xảy ra.
        return "NESTED_NAME_REF"
    if _la_gia_tri_tho(v):
        return "NESTED_RAW_LITERAL"
    if not isinstance(v, dict):
        return "NESTED_UNKNOWN_KIND"
    k = v.get("kind")
    if k not in _CHU_KY:
        return "NESTED_UNKNOWN_KIND"
    if _CHU_KY[k][1] not in nhan:
        return "NESTED_WRONG_TYPE"
    if v.get("model_assumption") is not None:
        # Một giả định mô hình tự đặt phải được KHAI ở một điểm gốc, nơi
        # `grounding_gate` hỏi nó. Chở nó lậu trong một biểu thức lồng rồi để
        # phép nâng biến thành thực thể là đúng khuôn rửa năng lực.
        return "NESTED_CARRIES_ASSUMPTION"
    return None


def dang_chuan_tac(ten: str, e: dict) -> tuple[dict, dict | None]:
    """`(câu lệnh, khai báo|None)` — dạng CHUẨN TẮC của một ràng buộc hình học.

    Cùng phép rẽ hai đường mà `contract._rang_buoc_lan_dau` làm, và cùng đọc từ
    một thẩm quyền (`_CHU_KY`): điểm thì `construct_point` (vào memory, xuất xứ
    đầy đủ), còn lại thì `assign` + khai báo với kiểu suy TĨNH (§11 — không bao
    giờ `unknown`), vì IR không có `construct_vector`.
    """
    kieu = _CHU_KY[e["kind"]][1]
    if kieu == DIEM:
        return {"kind": "construct_point", "target_var": ten, "expr": e}, None
    return ({"kind": "assign", "target_var": ten, "expr": e},
            {"name": ten, "type": kieu})


def _moi_ten(node: Any, ra: set[str]) -> None:
    """Mọi chuỗi trong cây — trần nhưng đúng: va chạm tên phải tuyệt đối không."""
    if isinstance(node, dict):
        for v in node.values():
            _moi_ten(v, ra)
    elif isinstance(node, list):
        for v in node:
            _moi_ten(v, ra)
    elif isinstance(node, str):
        ra.add(node)


class _Bo:
    """Bộ sinh tên tạm — TẤT ĐỊNH theo thứ tự duyệt, không va chạm."""

    def __init__(self, da_dung: set[str]) -> None:
        self.da_dung = da_dung
        self.dem = 0

    def ten(self) -> str:
        while True:
            self.dem += 1
            t = f"{TIEN_TO_TAM}{self.dem}"
            if t not in self.da_dung:
                self.da_dung.add(t)
                return t


def _nang_nut(node: Any, bo: _Bo, truoc: list, khai: list, sau: int,
              bo_qua: tuple[str, ...] = ()) -> Any:
    """Nâng mọi ô TÊN bị lồng dưới `node`, HẬU THỨ TỰ (trong ra ngoài).

    Hậu thứ tự là điều kiện của §10: temp của biểu thức bên trong phải tồn tại
    TRƯỚC câu lệnh dùng nó, nên nó phải được sinh trước. Cây biểu thức JSON
    không có chu trình, nên thứ tự tôpô ở đây chính là thứ tự duyệt.

    Đi HẾT cây chứ không chỉ các ô TÊN của tầng một: một `measure` có thể nằm
    dưới `arith`, và ô `of` của nó vẫn là một ô TÊN. Chỉ dừng ở `bo_qua` —
    thân nhánh, do `_nang_khoi` lo để temp không vượt scope (§14).
    """
    if isinstance(node, list):
        return [_nang_nut(x, bo, truoc, khai, sau) for x in node]
    if not isinstance(node, dict):
        return node
    o = _o_cua(node)
    moi = dict(node)
    for khoa, v in node.items():
        if khoa not in o and khoa not in bo_qua:
            moi[khoa] = _nang_nut(v, bo, truoc, khai, sau)
    for truong, (nhan, la_ds) in o.items():
        gt = node.get(truong)
        if la_ds and isinstance(gt, list):
            moi[truong] = [_nang_mot(x, nhan, bo, truoc, khai, sau) for x in gt]
        else:
            moi[truong] = _nang_mot(gt, nhan, bo, truoc, khai, sau)
    return moi


def _nang_mot(gt: Any, nhan: tuple[str, ...], bo: _Bo, truoc: list,
              khai: list, sau: int) -> Any:
    """Một ô: TÊN thì để yên, biểu thức nâng được thì nâng, còn lại giữ nguyên."""
    if isinstance(gt, str) or gt is None:
        return gt
    if sau >= SAU_TOI_DA or _an_toan(gt, nhan) is not None:
        # KHÔNG nâng, và cũng KHÔNG ném ở đây: lời từ chối của một ô TÊN thuộc
        # về `contract.canonical_geometry_name` — biên cấp TRƯỜNG, nơi mọi ô
        # TÊN đi qua dù có nâng hay không. Ném ở cả hai chỗ là hai câu chữ cho
        # cùng một luật, và chúng sẽ trôi khỏi nhau.
        return gt
    trong = _nang_nut(gt, bo, truoc, khai, sau + 1)
    ten = bo.ten()
    st, kb = dang_chuan_tac(ten, trong)
    truoc.append(st)
    if kb:
        khai.append(kb)
    return ten


def _nang_khoi(stmts: list, bo: _Bo, khai: list) -> tuple[list, bool]:
    """Nâng trong MỘT khối lệnh. Temp sinh ra ở ĐÚNG khối ấy (§14).

    Không bao giờ đẩy temp ra scope ngoài: một `if` không chạy thì cả câu lệnh
    dùng temp lẫn temp đều không chạy, nên câu hỏi *"tên này đã có giá trị
    chưa"* không hề mở ra — `CONTROL_FLOW_DEFINITE_ASSIGNMENT` giữ nguyên trạng.
    """
    ra, doi = [], False
    for st in stmts or ():
        if not isinstance(st, dict):
            ra.append(st)
            continue
        truoc: list = []
        moi = _nang_nut(st, bo, truoc, khai, 0, bo_qua=_NHANH)
        for nhanh in _NHANH:
            if isinstance(moi.get(nhanh), list):
                con, c_doi = _nang_khoi(moi[nhanh], bo, khai)
                moi[nhanh] = con
                doi = doi or c_doi
        ra.extend(truoc)
        ra.append(moi)
        doi = doi or bool(truoc) or moi != st
    return ra, doi


def nang_bieu_thuc_long(data: Any) -> Any:
    """Chuẩn hoá TIỆN DỤNG: biểu thức lồng ở ô TÊN → ràng buộc có tên.

    Trả về `data` nguyên vẹn khi không có gì để nâng — nên đường đi của mọi
    chương trình đã đúng dạng chuẩn tắc không đổi một byte.
    """
    if not isinstance(data, dict) or not isinstance(data.get("statements"), list):
        return data
    da_dung: set[str] = set()
    _moi_ten(data, da_dung)
    bo = _Bo(da_dung)
    khai: list = []
    stmts, doi = _nang_khoi(data["statements"], bo, khai)
    if not doi:
        return data
    kb = [dict(d) if isinstance(d, dict) else d
          for d in (data.get("memory_declarations") or [])]
    return {**data, "memory_declarations": kb + khai, "statements": stmts}


def kiem_nang(spec: dict) -> list[dict]:
    """Mọi lần LỒNG ở một ô TÊN, kèm phán quyết an toàn. Cho bộ audit — KHÔNG
    sửa gì, và cố ý tách khỏi đường nâng để audit không tự khẳng định chính nó.
    """
    ra: list[dict] = []

    def _di(node: Any, chu: str) -> None:
        if isinstance(node, list):
            for x in node:
                _di(x, chu)
            return
        if not isinstance(node, dict):
            return
        o = _o_cua(node)
        k = node.get("kind")
        for truong, (nhan, la_ds) in o.items():
            gt = node.get(truong)
            for x in (gt if la_ds and isinstance(gt, list) else [gt]):
                # Đếm MỌI thứ không phải TÊN, kể cả mảng toạ độ thô: câu hỏi
                # của §5 là *"những lần mô hình không điền một tên"*, và bỏ qua
                # các lần thô nhất là tự bào chữa cho phép nâng.
                if x is None or isinstance(x, str):
                    continue
                ly = _an_toan(x, nhan)
                ra.append({
                    "chu": k, "truong": truong, "nhan": list(nhan),
                    "kind_long": (x.get("kind") or "<không có kind>")
                                 if isinstance(x, dict) else type(x).__name__,
                    "an_toan": ly is None, "ly_do": ly or "",
                    # BA kết cục, không phải hai. Xem `_an_toan`.
                    "xu_ly": ("HOISTED" if ly is None else
                              "NAME_REF_UNWRAPPED" if ly == "NESTED_NAME_REF"
                              else "REJECTED"),
                })
        for v in node.values():
            _di(v, chu)

    _di(spec.get("statements") or [], "statements")
    return ra
