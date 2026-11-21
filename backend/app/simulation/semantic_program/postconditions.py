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


class KhongKiemChungDuoc(Exception):
    """Checker KHÔNG biểu diễn được thứ nghĩa vụ đòi ⇒ mức yếu, không phải vi phạm.

    Tách hẳn khỏi "vi phạm" vì hai câu trả lời khác nhau về bản chất: một cái
    nói *chương trình sai*, cái kia nói *tôi không biết*. Trộn chúng là kết tội
    một chương trình đúng.
    """


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


# (/13) Checker của miền Tin học (extremum, aggregate_matching, ordering, membership, first_match_index,
# total_mapping, derived_sequence, reachability, predicate_verdict + PREDICATE_CHECKERS, scalar_accumulation) đã gỡ.


from .geometry_obligations import GEOMETRY_CHECKERS  # noqa: E402
from .coverage_gate import phan_giai_witness  # noqa: E402
from .measure_contract import nghia_vu_chinh_tac  # noqa: E402


def _kieu_khai(spec) -> dict:
    """`tên → MemoryType` từ khai báo — resolver cần để kiểm chữ ký."""
    return {m.name: m.type for m in (spec.memory_declarations or ())}


def _lien_ket_khong_truc_tiep(ob, snap: dict) -> bool:
    """Chủ thể có nhận được nghĩa vụ này một cách TRỰC TIẾP không?

    Chỉ khi KHÔNG, mới đi tìm phép đo qua witness. Thứ tự này giữ đường
    unary hiện hành nguyên vẹn: `radius(ball)`, `volume(curved_solid)`,
    `lateral_area(curved_solid)` vẫn chấm thẳng như trước.
    """
    from .obligations import accepts_container_type

    x = snap.get(ob.container)
    if x is None:
        return False
    return not accepts_container_type(ob.kind, _kieu_runtime(x))


def _kieu_runtime(x) -> str | None:
    """MemoryType suy từ giá trị thật trong snapshot."""
    from ..geometry.curved import CurvedSolid
    from ..geometry.exact import Line3, Plane3, Vec3

    return {Vec3: 'point3', Line3: 'line3', Plane3: 'plane3',
            CurvedSolid: 'curved_solid'}.get(type(x))

CHECKERS: dict[str, Callable[[dict, Obligation], str | None]] = {
    # ── MIỀN HÌNH HỌC — miền duy nhất (/13). Kiểm là một PHÉP TÍNH giải tích (`u·v == 0`), không phải một lời giải,
    # nên tính độc lập không mất. Xem `geometry_obligations.py`.
    **GEOMETRY_CHECKERS,
}


ERR_NGUON_BI_VI_PHAM = "NORMALIZED_SOURCE_VIOLATED"
#: Đề CÓ nói về một quan hệ chia đoạn, hệ nhận ra nhưng KHÔNG giải được nó.
#: Khác hẳn `not_checkable`: xem docstring `SourceInvariantResult`.
ERR_NGUON_CHUA_KIEM_DUOC = "SOURCE_INVARIANT_NOT_CHECKABLE"


class SourceInvariantResult(BaseModel):
    """Kết quả `NormalizedSourceInvariantGate` — năm con số, không gộp.

    `not_checkable` tách hẳn khỏi `violated`: *"tôi không dựng lại được phép
    kiểm này"* và *"chương trình dựng sai hình"* là hai câu khác nhau, và gộp
    chúng là kết tội oan — đúng lỗi đã phải viết ba bản đính chính.

    ─── VÀ `unresolved` TÁCH KHỎI CẢ HAI (2026-09-06) ──────────────────────

    `SEGMENT_RELATION_COVERAGE_HARDENING`. Ba câu khác nhau, ba kết cục khác
    nhau, và chỉ có hai câu đầu là an toàn khi im lặng:

        not_checkable  bất biến có, nhưng trạng thái cuối thiếu vật để đo
                       (vd điểm chưa dựng) ⇒ KHÔNG chặn: hệ không có ý kiến
        unresolved     ĐỀ CÓ nói về một phép chia đoạn — bộ ba (A,B,M) neo
                       được, có mảnh quan hệ nói đúng hai nhánh, có nguồn —
                       mà hệ KHÔNG tính ra `t` ⇒ **CHẶN**
        violated       tính ra `t` và hình dựng không khớp ⇒ CHẶN

    Vì sao `unresolved` phải chặn: nếu im lặng thì một đề mà hệ **đọc hiểu
    một nửa** sẽ đi tiếp và được phục vụ, tức đúng lớp lỗi `r3/A` — hệ trả
    lời tự tin về một hình nó chưa chứng minh được là hình của đề. Ranh giới
    ở đây là *"có tín hiệu chắc chắn"*, không phải *"có nghi ngờ"*.

    ⚠️ Quan hệ mà hệ **không nhận ra** thì không đến được đây (`NOT_EXTRACTED`
    ở `segment_relation`) — và đó là giới hạn phải khai, không phải fail-closed.
    """

    ok: bool
    error_code: str | None = None
    checked: int = 0
    passed: int = 0
    violated: list[str] = Field(default_factory=list)
    not_checkable: list[str] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)


def _he_so(pl):
    """`Plane3(P, n)` → `(a, b, c, d)` của `ax+by+cz+d = 0`.

    `n·(X − P) = 0` ⇔ `n·X − n·P = 0`, nên `d = −n·P`. Toàn `Fraction`, và đây
    là chiều ĐỌC NGƯỢC duy nhất: kernel giữ `(điểm, pháp tuyến)`, tầng này cần
    bốn hệ số để so với đề. Không dựng thẩm quyền thứ hai — hàm này không dựng
    mặt phẳng nào, nó chỉ viết lại thứ kernel đã giữ.
    """
    from fractions import Fraction as F

    n, p = pl.normal, pl.point
    return F(n.x), F(n.y), F(n.z), F(-n.dot(p))


def _viet_he(he) -> str:
    """Bốn hệ số → `"2x - z + 10 = 0"`. CHỈ để đọc trong thông báo lỗi."""
    from .geometry_exec import _viet_pt

    from fractions import Fraction as F

    return _viet_pt(*[F(x) for x in he])


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

    from app.simulation.geometry.exact import Plane3, Vec3
    from app.simulation.geometry.measure import distance_sq
    from app.simulation.geometry.radical import parse_exact, square

    from .plane_equation import KIND as PLANE_EQUATION
    from .plane_equation import KIND_CHUA_GIAI as PLANE_UNRESOLVED
    from .plane_equation import tuong_duong
    from .point_coordinate import KIND as POINT_COORDINATE
    from .point_coordinate import KIND_CHUA_GIAI as POINT_UNRESOLVED
    from .segment_relation import KIND as SEGMENT_DIVISION
    from .segment_relation import KIND_CHUA_GIAI

    snap = _final(exec_result)
    doi = ten_da_hoa_giai or {}
    vi_pham: list[str] = []
    khong_kiem: list[str] = []
    chua_giai: list[str] = []
    dat = 0

    def _diem(bt):
        """Tên hợp đồng → điểm trong trạng thái cuối. Lưới hoà giải DÙNG CHUNG.

        ─── BA NẤC, VÀ NẤC BA DÙNG THẨM QUYỀN ĐÃ CÓ ───────────────────────

        ① tên đề trùng tên biến · ② lưới hoà giải của cổng phủ (C₁a) ·
        ③ `source_entities.chuan_hoa_ten` — *"tên biến IR ứng với nhãn đề
        nào"*.

        Nấc ③ thêm 2026-09-08 (`POINT_COORDINATE_SOURCE_INVARIANT`) vì một ca
        đo được: đề viết `O'(0,0,20)`, chương trình đặt biến `Oprime`, lưới
        C₁a không nối hai tên ấy ⇒ bất biến rơi vào `not_checkable`. Nó không
        phục vụ sai, nhưng nó **im lặng đúng lúc cần nói**.

        KHÔNG viết lưới chính tả thứ chín: `chuan_hoa_ten` đã sở hữu đúng tri
        thức ấy (`A_prime` → `A'`, `point_A` → `A`, `A_1` → `A1`), và dựng bản
        thứ hai là cách hai bản lệch nhau rồi lệch câm.
        """
        from .source_entities import chuan_hoa_ten

        ra = []
        for ten in bt.points:
            v = snap.get(ten)
            if v is None and ten in doi:
                v = snap.get(doi[ten])
            if v is None:
                # DUY NHẤT hoặc KHÔNG — không bao giờ "chọn cái đầu tiên".
                # Hai biến cùng quy về một nhãn đề (`A_prime` và `pointA'`) là
                # một tình huống MƠ HỒ; đoán giữa chúng là đặt một phép đoán
                # vào giữa đường gác cửa. Không phân giải được ⇒ điểm vắng ⇒
                # `not_checkable`, tức KHÔNG kết tội.
                khop = [k for k in snap if ten in chuan_hoa_ten(k)]
                if len(khop) == 1:
                    v = snap[khop[0]]
            ra.append(v)
        return ra

    for bt in contract.source_invariants or ():
        # ─── QUAN HỆ CHIA ĐOẠN ────────────────────────────────────────────
        #
        # `SEGMENT_RELATION_CONSISTENCY_VERIFICATION`, 2026-09-06. Đọc `points`
        # theo hợp đồng của `kind` này — `(A, B, M)`, hướng A→B do ĐỀ quyết —
        # rồi giải `M = A + t·(B − A)` trong ℚ và so `t` bằng phân số chính xác.
        #
        # Lỗ nó bịt: `r3/A` dựng `P` sai vị trí mà vẫn `served`, vì
        # `check_distance` đo ĐÚNG khoảng cách tới điểm SAI. Phép kiểm ở đây
        # hỏi câu khác hẳn — *"điểm ấy có đúng là điểm đề nói tới không"* — và
        # nó phải hỏi trên HÌNH, không trên chuỗi `ratio` chương trình khai:
        # `divide_segment(F, E, 4/5)` và `divide_segment(E, F, 1/5)` là hai
        # cách viết CÙNG một điểm, và cả hai đều đúng.
        # ─── ĐỀ CÓ QUAN HỆ, HỆ ĐỌC HIỂU MỘT NỬA ⇒ CHẶN ────────────────────
        #
        # Không phải "không có ý kiến" mà là *"tôi thấy đề ràng buộc điểm này,
        # và tôi KHÔNG chứng minh được hình dựng thoả nó"*. Đi tiếp ở đây là
        # phục vụ một hình chưa được chứng minh — đúng lớp lỗi `r3/A`.
        if bt.kind == KIND_CHUA_GIAI:
            ten = list(bt.points)
            chua_giai.append(
                f"{bt.source_text}: đề ràng buộc "
                f"{ten[2] if len(ten) > 2 else '?'} trên đoạn "
                f"{''.join(ten[:2])}, nhưng hệ KHÔNG tính được tỉ lệ chia — "
                f"thiếu độ dài cả đoạn hoặc quan hệ nêu mơ hồ "
                f"(nguồn: {bt.source_fact_id or 'không nêu'})")
            continue

        if bt.kind == SEGMENT_DIVISION:
            if len(bt.points) != 3:
                khong_kiem.append(
                    f"{bt.source_text}: '{bt.kind}' cần đúng 3 tên (A, B, M), "
                    f"có {len(bt.points)}")
                continue
            A, B, M = _diem(bt)
            if not all(isinstance(v, Vec3) for v in (A, B, M)):
                khong_kiem.append(
                    f"{bt.source_text}: không tìm đủ ba điểm {list(bt.points)} "
                    "trong trạng thái cuối")
                continue
            d, v = B - A, M - A
            if d.x == 0 and d.y == 0 and d.z == 0:
                khong_kiem.append(
                    f"{bt.source_text}: {bt.points[0]} ≡ {bt.points[1]} — "
                    "đoạn suy biến, không có hướng để chia")
                continue
            try:
                q = Fraction(bt.expected)
            except (ValueError, ZeroDivisionError):
                khong_kiem.append(f"{bt.source_text}: '{bt.expected}' không hữu tỉ")
                continue
            # Giải `t` trên trục có thành phần khác 0 rồi ĐỐI CHIẾU LẠI cả ba
            # thành phần: phép đối chiếu ấy chính là phép kiểm THẲNG HÀNG, nên
            # không cần một phép cross riêng và không có đường nào để một điểm
            # lệch khỏi đường thẳng lọt qua.
            truc = "x" if d.x != 0 else ("y" if d.y != 0 else "z")
            t_that = getattr(v, truc) / getattr(d, truc)
            if v != d.scale(t_that):
                vi_pham.append(
                    f"{bt.source_text}: {bt.points[2]} KHÔNG thẳng hàng với "
                    f"{bt.points[0]}{bt.points[1]} — hình dựng đặt nó ngoài "
                    f"đường thẳng (nguồn: {bt.source_fact_id or 'không nêu'})")
                continue
            if t_that == q:
                dat += 1
            else:
                def _mn(x: Fraction) -> str:
                    return (f"{x.numerator}:{x.denominator - x.numerator}"
                            if 0 < x < 1 else "ngoài đoạn")
                vi_pham.append(
                    f"{bt.source_text}: đề cho {bt.points[0]}{bt.points[2]}:"
                    f"{bt.points[2]}{bt.points[1]} = {_mn(q)} (t = {q}), "
                    f"hình dựng có {_mn(t_that)} (t = {t_that}); "
                    f"điểm sai: {bt.points[2]}"
                    f" (nguồn: {bt.source_fact_id or 'không nêu'})")
            continue

        # ─── PHƯƠNG TRÌNH MẶT PHẲNG ──────────────────────────────────────
        #
        # `PLANE_FROM_EQUATION_REPRESENTATION`, 2026-09-07. Hỏi trên HÌNH, y
        # như hai kind trên: *"mặt phẳng đề cho bằng phương trình có thật sự
        # nằm trong hình dựng ra không"*.
        #
        # KHÔNG đọc câu lệnh. Bốn hệ số mô hình viết trong
        # `construct_plane_from_equation` là **lời khai**; thứ được kiểm là
        # `Plane3` trong trạng thái cuối. Nhờ vậy cổng phủ luôn cả đường dựng
        # QUA BA ĐIỂM — một chương trình dựng đúng mặt phẳng ấy bằng ba điểm
        # cũng đạt, và một chương trình dựng sai thì trượt dù dùng lối nào.
        if bt.kind == PLANE_UNRESOLVED:
            chua_giai.append(
                f"{bt.source_text}: đề nêu một mặt phẳng bằng phương trình, "
                "nhưng hệ KHÔNG giải được hệ số — phương trình có tham số, "
                "hoặc viết ở dạng ngoài ngưỡng đọc "
                f"(nguồn: {bt.source_fact_id or 'không nêu'})")
            continue

        if bt.kind == PLANE_EQUATION:
            mp = [(t, v) for t, v in snap.items() if isinstance(v, Plane3)]
            if not mp:
                # KHÔNG phải vi phạm: không có mặt phẳng nào thì không có gì
                # mâu thuẫn với đề. *"Đáng lẽ phải dựng"* là câu hỏi của cổng
                # phủ và của nghĩa vụ, không phải của bất biến nguồn.
                khong_kiem.append(
                    f"{bt.source_text}: chương trình không dựng mặt phẳng nào "
                    "để đối chiếu")
                continue
            khop = [t for t, v in mp
                    if tuong_duong(bt.coefficients, _he_so(v))]
            if khop:
                dat += 1
            else:
                ta = ", ".join(
                    f"{t}: {_viet_he(_he_so(v))}" for t, v in sorted(mp))
                vi_pham.append(
                    f"{bt.source_text}: đề cho mặt phẳng "
                    f"{_viet_he(bt.coefficients)}, hình dựng KHÔNG có mặt "
                    f"phẳng nào tỉ lệ với nó — đang có {ta} "
                    f"(nguồn: {bt.source_fact_id or 'không nêu'})")
            continue

        # ─── TOẠ ĐỘ ĐIỂM ĐỀ CHO TƯỜNG MINH ───────────────────────────────
        #
        # `POINT_COORDINATE_SOURCE_INVARIANT`, 2026-09-08. Hỏi trên HÌNH, y
        # như ba kind trên: *"điểm đề cho toạ độ có đúng ở chỗ ấy trong hình
        # dựng ra không"*.
        #
        # KHÔNG đọc `memory_declarations`, KHÔNG đọc `source_fact_id`. Nhờ vậy
        # mọi ĐƯỜNG BIỂU DIỄN chịu chung một luật: khai thẳng · qua bí danh ·
        # dựng bằng một phép — điểm nằm sai chỗ thì trượt, dùng lối nào cũng
        # thế. Đó cũng là lý do nó bắt được ca mà grounding bỏ qua: grounding
        # soi LỜI KHAI, cổng này soi TRẠNG THÁI CUỐI.
        if bt.kind == POINT_UNRESOLVED:
            chua_giai.append(
                f"{bt.source_text}: đề nêu toạ độ của {bt.points[0]} ở HAI "
                "chỗ MÂU THUẪN — hệ không biết đề muốn điểm nào "
                f"(nguồn: {bt.source_fact_id or 'không nêu'})")
            continue

        if bt.kind == POINT_COORDINATE:
            if len(bt.points) != 1 or len(bt.coefficients) != 3:
                khong_kiem.append(
                    f"{bt.source_text}: '{bt.kind}' cần đúng 1 tên và 3 toạ "
                    f"độ, có {len(bt.points)} và {len(bt.coefficients)}")
                continue
            (P,) = _diem(bt)
            if not isinstance(P, Vec3):
                # KHÔNG phải vi phạm: đề nhắc một điểm mà chương trình không
                # dựng thì không có gì MÂU THUẪN với đề. *"Đáng lẽ phải dựng"*
                # là câu hỏi của cổng phủ, không phải của bất biến nguồn.
                khong_kiem.append(
                    f"{bt.source_text}: không tìm thấy điểm {bt.points[0]} "
                    "trong trạng thái cuối")
                continue
            try:
                mong = tuple(Fraction(c) for c in bt.coefficients)
            except (ValueError, ZeroDivisionError):
                khong_kiem.append(
                    f"{bt.source_text}: toạ độ '{list(bt.coefficients)}' "
                    "không hữu tỉ")
                continue
            that = (P.x, P.y, P.z)
            if that == mong:
                dat += 1
            else:
                lech = [t for t, a, b in zip("xyz", that, mong) if a != b]
                vi_pham.append(
                    f"{bt.source_text}: đề cho {bt.points[0]}"
                    f"({', '.join(str(c) for c in mong)}), hình dựng đặt nó ở "
                    f"({', '.join(str(c) for c in that)}) — lệch "
                    f"{'/'.join(lech)} (nguồn: {bt.source_fact_id or 'không nêu'})")
            continue

        if bt.kind != "segment_length":
            khong_kiem.append(f"{bt.source_text}: chưa có checker cho '{bt.kind}'")
            continue
        # THẨM QUYỀN VỀ TÊN dùng chung, không viết lưới hoà giải thứ chín.
        diem = _diem(bt)
        if not all(isinstance(v, Vec3) for v in diem):
            khong_kiem.append(
                f"{bt.source_text}: không tìm đủ hai điểm {list(bt.points)} "
                "trong trạng thái cuối")
            continue
        # §18.3: độ dài nguồn có thể là căn `k√n` — so BÌNH PHƯƠNG (hữu tỉ), không ép về `Fraction`.
        q = parse_exact(bt.expected)
        if q is None:
            khong_kiem.append(f"{bt.source_text}: '{bt.expected}' không đọc được thành số chính xác")
            continue
        that, can = distance_sq(diem[0], diem[1]), square(q)
        if that == can:
            dat += 1
        else:
            vi_pham.append(
                f"{bt.source_text}: đề cho {bt.expected}, hình dựng có "
                f"{bt.points[0]}{bt.points[1]}² = {that} (cần {can})")

    n = dat + len(vi_pham) + len(khong_kiem) + len(chua_giai)
    return SourceInvariantResult(
        ok=not (vi_pham or chua_giai),
        # VI PHẠM thắng khi có cả hai: *"hình sai"* là kết luận mạnh hơn
        # *"chưa đọc hiểu"*, và người đọc cần biết cái mạnh hơn trước.
        error_code=(ERR_NGUON_BI_VI_PHAM if vi_pham else
                    (ERR_NGUON_CHUA_KIEM_DUOC if chua_giai else None)),
        checked=n, passed=dat, violated=vi_pham, not_checkable=khong_kiem,
        unresolved=chua_giai,
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

        # NGHĨA VỤ CHÍNH TẮC — cùng helper mà cổng phủ dùng.
        #
        # Nếu ở đây đọc `ob.kind` thô còn cổng phủ đọc bản quy đổi (hay ngược
        # lại), hai cổng sẽ nói hai điều khác nhau về CÙNG một nghĩa vụ: một
        # bên cho qua, một bên không tìm ra checker. `test_F_hai_consumer_cung
        # _goi_MOT_helper` khoá đúng ràng buộc ấy bằng cách quét nguồn.
        _x = snap.get(ob.container)
        _ho = getattr(_x, "kind", None) if _x.__class__.__name__ ==             "CurvedSolid" else None
        _kind = nghia_vu_chinh_tac(
            ob.kind, "curved_solid" if _ho else None, _ho)
        if _kind != ob.kind:
            ob = ob.model_copy(update={"kind": _kind})
        # ─── WITNESS DẪN TỚI PHÉP ĐO THẬT ────────────────────────────────
        #
        # `c7a` khai `distance(container="hinh_non", witness="l")` để nói
        # *"đường sinh"*. `distance` là phép đo QUAN HỆ, nên chấm thẳng trên
        # `hinh_non: curved_solid` trả *"cặp đối tượng không hợp lệ"* — một
        # chương trình đúng trọn vẹn bị bác. Phép đo thật nằm ở câu lệnh sinh
        # witness: `l = measure(distance, of=T, wrt=A)`.
        #
        # Chấm bằng cách dựng một nghĩa vụ TƯƠNG ĐƯƠNG trên đúng toán hạng ấy,
        # rồi gọi CHECKER CŨ — không viết phép đo thứ hai. Checker vẫn tính
        # lại từ hình; `l` chỉ là giá trị khai để đối chiếu.
        if spec is not None and _lien_ket_khong_truc_tiep(ob, snap):
            pg = phan_giai_witness(spec, ob, _kieu_khai(spec))
            if pg.diagnostic_status == "OK" and len(pg.operands) > 1:
                ob = ob.model_copy(update={
                    "container": pg.operands["of"],
                    "params": {**ob.params, "wrt": pg.operands["wrt"]}})
        fn = CHECKERS.get(ob.kind)
        if fn is None:
            continue
        da_kiem.append(ob.describe())
        # ─── BÍ DANH KHÔNG ĐỦ KHI TÊN HỢP ĐỒNG ĐÃ CÓ CHỦ ──────────────────
        #
        # Phép gán bí danh phía trên chỉ chạy khi `ten_hd not in snap`. C₁a đã
        # học đúng bài này ngày 2026-08-29 (*"hoà giải CŨNG phải chạy khi tên
        # CÓ mà sai kiểu"*), C₂ thì chưa — nên hai cổng nói hai điều khác nhau
        # về cùng một vật, đúng lớp lỗi mà `ten_da_hoa_giai` sinh ra để dẹp.
        #
        # Đo được ở `circumsphere` (2026-09-04): hợp đồng hỏi `radius(OABC)`,
        # chương trình có `OABC` là TỨ DIỆN và quả cầu tên `circumsphere`. C₁a
        # nối `OABC ≡ circumsphere` rồi cho qua; ở đây `"OABC" in snap` là
        # True nên bí danh không gán, `check_radius` nhận tứ diện và báo *"cần
        # một `circle3` hoặc một `curved_solid`"* — vu oan một chương trình đã
        # tính đúng `R = √3`.
        #
        # Buộc lại TỪNG NGHĨA VỤ thay vì ghi đè `snap`: `snap` dùng chung, và
        # ghi đè `OABC` sẽ phá một nghĩa vụ khác nói đúng về tứ diện (vd
        # `volume(OABC)`). Ánh xạ chỉ tồn tại khi C₁a đã kết luận tên hợp đồng
        # KHÔNG trỏ đúng vật — nên có ánh xạ là đủ điều kiện buộc lại.
        thay = (ten_da_hoa_giai or {}).get(ob.container)
        ob_kiem = (ob.model_copy(update={"container": thay})
                   if thay and thay in snap else ob)
        try:
            msg = fn(snap, ob_kiem)
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
