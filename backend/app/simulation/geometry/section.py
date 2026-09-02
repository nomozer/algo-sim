# -*- coding: utf-8 -*-
"""Dựng THIẾT DIỆN — phép dựng cốt lõi, và bài có cơ chế ẩn lớn nhất.

VÌ SAO ĐÂY LÀ BÀI QUAN TRỌNG NHẤT: học sinh **không hình dung nổi** giao tuyến
trong đầu. Hình vẽ trong vở là một hình chiếu phẳng, và trên hình chiếu ấy hai
đường chéo nhau trông y hệt hai đường cắt nhau. Đây là chỗ mô phỏng 3D không
trang trí — nó cho thấy đúng thứ giấy không cho thấy được.

THUẬT TOÁN — đi theo MẶT, không đi theo ĐIỂM. Cách ngây thơ là gom mọi giao
điểm rồi sắp xếp quanh trọng tâm theo góc; cách ấy cần `atan2`, tức kéo vô tỉ
vào đúng chỗ đang cố giữ chính xác, **và** nó vứt mất thứ ta cần nhất: **thứ tự
dựng**. Đi theo mặt thì mỗi mặt cho **một cạnh** của thiết diện, và dãy cạnh ấy
chính là dãy bước mà học sinh phải làm trên giấy — timeline có sẵn, không phải
bịa ra sau.

Chỉ nhận **đa diện LỒI**. Đa diện lõm cho thiết diện có thể gồm nhiều mảnh rời,
và `RUN2`/roadmap đã khoanh phạm vi ở khối lồi.

FAIL-CLOSED: mặt phẳng không cắt khối → **NÉM**, không trả đa giác rỗng. Một
đa giác rỗng đi tiếp tới renderer sẽ thành một cảnh trống mà không ai nói là
đang trống — đúng lỗi đã sinh ra bất biến #31.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from .exact import GeometryError, Plane3, Point3

#: Mặt phẳng nằm hẳn ngoài khối — không một điểm chung nào.
ERR_KHONG_CAT = "PLANE_DOES_NOT_CUT"
#: Chạm khối ở ĐÚNG MỘT ĐỈNH. Có điểm chung, nhưng thiết diện suy biến thành
#: một điểm.
ERR_CHAM_DINH = "PLANE_TOUCHES_VERTEX"
#: Chạm khối ở ĐÚNG MỘT CẠNH. Thiết diện suy biến thành một đoạn thẳng.
ERR_CHAM_CANH = "PLANE_TOUCHES_EDGE"
#: Khối khai sai (mặt < 3 đỉnh, chỉ số ngoài biên…). **CHỈ** dùng cho khối
#: thật sự hỏng — không dùng cho một phép giao không ra đa giác.
ERR_KHOI_HONG = "MALFORMED_SOLID"
#: Giao CÓ TỒN TẠI nhưng không phải một đa giác 2D, và không rơi vào ba ca
#: chạm đã có tên ở trên. Tách khỏi `ERR_KHOI_HONG` vì hai điều khác hẳn nhau:
#: *"khối bạn khai sai"* và *"mặt phẳng này cắt khối theo một hình chiều thấp"*.
#: Trước 2026-09-02 cả hai dùng chung một mã, nên một khối đúng bị báo là hỏng.
ERR_SUY_BIEN = "SECTION_INTERSECTION_DEGENERATE"
#: Gom đủ đoạn nhưng không nối thành chu trình. Đây là **lỗi của chính hàm
#: này**, không phải lỗi của dữ liệu vào — sau khi khử trùng, một khối lồi hợp
#: lệ luôn nối được. Giữ lại làm lưới cuối, và giữ tên nói đúng ai sai.
ERR_NOI_VONG = "SECTION_CONSTRUCTION_INTERNAL_FAILURE"

#: BỐN mã suy biến, cố ý KHÔNG gộp thành một.
#:
#: Bản đầu gộp *"không cắt"* và *"chạm một đỉnh"* vào cùng `PLANE_DOES_NOT_CUT`
#: **với cùng một câu** — *"toàn bộ khối nằm về một phía"* — và câu ấy SAI cho
#: ca chạm đỉnh: khối có đúng một điểm nằm TRÊN mặt phẳng, không nằm về phía
#: nào cả. Kernel phân biệt được bốn ca này (đếm đỉnh có `signed_eval == 0` và
#: xem chúng có tạo thành một cạnh của khối không), nên gộp chúng lại là **vứt
#: đi thông tin đã có sẵn** — và đó đúng là thông tin học sinh cần: "mặt phẳng
#: của em đi qua đỉnh S" là một lời chẩn đoán, "không cắt" thì không.
#:
#: ⚠️ 2026-09-02: `CONTAINED_INFINITE_INTERSECTION` **rời khỏi danh sách**. Nó
#: từng đại diện ca *"mặt phẳng trùng một mặt của khối"*, mà ca ấy nay **không
#: suy biến**: nó cho ra chính mặt ấy làm thiết diện. `ERR_SUY_BIEN` vào thay —
#: giao có tồn tại nhưng ở chiều thấp hơn.
SECTION_DEGENERATE_CODES = (
    ERR_KHONG_CAT, ERR_CHAM_DINH, ERR_CHAM_CANH, ERR_SUY_BIEN,
)


@dataclass(frozen=True)
class Polyhedron:
    """Đa diện lồi: đỉnh + mặt (mỗi mặt là dãy chỉ số đỉnh, theo thứ tự vòng).

    Đặt ở đây chứ không ở `exact.py` vì hiện chỉ `section` dùng. Chuyển lên khi
    có người dùng thứ hai — chuyển sớm là suy đoán.
    """

    vertices: tuple[Point3, ...]
    faces: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        n = len(self.vertices)
        if n < 4:
            raise GeometryError(ERR_KHOI_HONG, f"đa diện cần ≥4 đỉnh, có {n}")
        for i, f in enumerate(self.faces):
            if len(f) < 3:
                raise GeometryError(
                    ERR_KHOI_HONG, f"mặt {i} có {len(f)} đỉnh, cần ≥3"
                )
            for j in f:
                if not 0 <= j < n:
                    raise GeometryError(
                        ERR_KHOI_HONG, f"mặt {i} trỏ đỉnh {j} ngoài [0,{n})"
                    )

    def edges_of_face(self, fi: int) -> list[tuple[int, int]]:
        f = self.faces[fi]
        return [(f[i], f[(i + 1) % len(f)]) for i in range(len(f))]


@dataclass(frozen=True)
class SectionStep:
    """Một bước dựng — đúng một cạnh của thiết diện, kèm mặt sinh ra nó.

    `face_index` không phải trang trí: lời kể *"trên mặt (SBC), nối M với N"*
    chỉ nói được khi biết cạnh này đến từ mặt nào.
    """

    face_index: int
    a: Point3
    b: Point3


@dataclass(frozen=True)
class Section:
    polygon: tuple[Point3, ...]
    steps: tuple[SectionStep, ...]

    @property
    def is_closed(self) -> bool:
        return len(self.polygon) >= 3


def _giao_canh(p: Point3, q: Point3, pl: Plane3) -> Point3| None:
    """Giao của ĐOẠN `pq` với mặt phẳng, hoặc `None` nếu đoạn không cắt.

    Đầu mút nằm trên mặt phẳng được trả về chính nó — không nội suy. Nội suy
    một điểm đã nằm sẵn trên mặt phẳng là cách sinh ra hai điểm "gần trùng"
    rồi thất bại khi nối vòng.
    """
    sp, sq = pl.signed_eval(p), pl.signed_eval(q)
    if sp == 0:
        return p
    if sq == 0:
        return q
    if (sp > 0) == (sq > 0):
        return None
    t = sp / (sp - sq)
    return p + (q - p).scale(t)


def _canh_tren_mat(sol: Polyhedron, fi: int, pl: Plane3) -> tuple[Point3, Point3] | None:
    """Mặt phẳng cắt mặt `fi` theo đoạn nào. `None` nếu không cắt / chỉ chạm.

    ⚠️ Đoạn trả về có thể **chính là một cạnh của khối** — khi cạnh ấy nằm trọn
    trong mặt phẳng cắt. Đó là một giao hoàn toàn hợp lệ, không phải dấu hiệu
    hỏng; và vì cạnh ấy thuộc **hai** mặt kề nên hai mặt sẽ cùng báo đúng một
    đoạn. Khử trùng là việc của `cross_section`, không phải của hàm này: ở đây
    ta chưa nhìn thấy các mặt khác.
    """
    diem: list[Point3] = []
    for i, j in sol.edges_of_face(fi):
        g = _giao_canh(sol.vertices[i], sol.vertices[j], pl)
        if g is not None and all(g != d for d in diem):
            diem.append(g)
    if len(diem) < 2:
        return None          # không cắt, hoặc chỉ chạm một đỉnh
    if len(diem) > 2:
        # Ca mặt NẰM TRỌN trong mặt phẳng cắt đã được `cross_section` chặn
        # trước bằng phép thử chính xác *"mọi đỉnh của mặt có `signed_eval`
        # bằng 0"*. Tới được đây nghĩa là ba điểm giao trở lên trên biên của
        # một mặt phẳng — chỉ xảy ra khi bản thân mặt ấy suy biến (ba đỉnh
        # thẳng hàng), và đó là lỗi của khối chứ không của phép cắt.
        raise GeometryError(
            ERR_KHOI_HONG,
            f"mặt {fi} cho {len(diem)} điểm giao trên biên — mặt này suy biến "
            f"(có đỉnh thẳng hàng), không phải một đa giác lồi",
        )
    return diem[0], diem[1]


def _thiet_dien_la_mat(sol: Polyhedron, fi: int) -> Section:
    """Mặt phẳng cắt TRÙNG một mặt của khối ⇒ thiết diện **chính là mặt ấy**.

    ─── VÌ SAO KHÔNG TỪ CHỐI ────────────────────────────────────────────────

    `intersection(khối, mặt phẳng)` ở đây hoàn toàn xác định và là một đa giác
    2D thật. Đề *"thiết diện của hình chóp cắt bởi mp(ABCD)"* với `ABCD` là đáy
    có một câu trả lời mà học sinh biết: chính cái đáy.

    Bản trước ném `CONTAINED_INFINITE_INTERSECTION` — mã ấy đúng cho *giao của
    hai mặt phẳng* (vô hạn), và sai ở đây: giao của một **khối** với một mặt
    phẳng thì bị chặn bởi khối, nên nó hữu hạn.

    Với khối LỒI, nhiều nhất một mặt nằm trong một mặt phẳng cho trước, nên
    không có chuyện phải chọn giữa hai đáp án.
    """
    dinh = tuple(sol.vertices[j] for j in sol.faces[fi])
    buoc = tuple(
        SectionStep(fi, dinh[i], dinh[(i + 1) % len(dinh)])
        for i in range(len(dinh))
    )
    return Section(dinh, buoc)


def _loi_suy_bien(sol: Polyhedron, pl: Plane3) -> GeometryError:
    """Chẩn đoán ca suy biến từ TIẾP XÚC THẬT, không từ số cạnh gom được.

    Câu hỏi phân loại là *"những đỉnh nào NẰM TRÊN mặt phẳng"* — `signed_eval`
    trả `Fraction`, nên `== 0` ở đây là một mệnh đề đúng-hoặc-sai, không phải
    một phép so gần đúng.

    Hai đỉnh nằm trên mặt phẳng **chưa chắc** là ca "chạm một cạnh": chúng phải
    là hai đầu của một cạnh THẬT của khối. Hai đỉnh đối nhau trên một mặt vuông
    thì mặt phẳng đi xuyên qua khối chứ không chạm — nên phải tra bảng mặt, và
    tra bảng mặt là thứ hàm này có mà tầng gọi không nên tự làm.

    ⚠️ **Không mã nào ở đây được đổ lỗi cho bảng mặt.** Tới được hàm này nghĩa
    là khối đã qua `Polyhedron.__post_init__`, tức bảng mặt hợp lệ về cấu trúc.
    Điều sai là *mặt phẳng người dùng chọn*, không phải *khối người dùng khai*
    — và bản trước nói ngược, khiến một khối đúng bị báo `MALFORMED_SOLID`.
    """
    tren = [i for i, v in enumerate(sol.vertices) if pl.signed_eval(v) == 0]
    if not tren:
        return GeometryError(
            ERR_KHONG_CAT,
            "mặt phẳng KHÔNG cắt khối — toàn bộ khối nằm về một phía, "
            "không có điểm chung nào",
        )
    if len(tren) == 1:
        return GeometryError(
            ERR_CHAM_DINH,
            f"mặt phẳng chỉ CHẠM khối ở đúng một đỉnh (đỉnh thứ {tren[0] + 1}) "
            "— thiết diện suy biến thành một điểm, không phải đa giác",
        )
    if len(tren) == 2:
        canh = {
            tuple(sorted(c))
            for fi in range(len(sol.faces))
            for c in sol.edges_of_face(fi)
        }
        if tuple(sorted(tren)) in canh:
            return GeometryError(
                ERR_CHAM_CANH,
                f"mặt phẳng chỉ CHẠM khối ở đúng một cạnh (đỉnh thứ "
                f"{tren[0] + 1} và {tren[1] + 1}) — thiết diện suy biến thành "
                "một đoạn thẳng, không phải đa giác",
            )
    return GeometryError(
        ERR_SUY_BIEN,
        f"mặt phẳng gặp khối ở {len(tren)} đỉnh nhưng phần chung không tạo "
        "thành một đa giác — giao nằm ở chiều thấp hơn (một điểm hoặc một "
        "đoạn thẳng), nên không có thiết diện để dựng. Khối vẫn hợp lệ; hãy "
        "chọn một mặt phẳng thật sự cắt qua ruột khối",
    )


def cross_section(sol: Polyhedron, pl: Plane3) -> Section:
    """Thiết diện của `pl` với đa diện lồi `sol`.

    Trả về **đa giác đã sắp thứ tự** cùng **dãy bước dựng** — mỗi bước là một
    cạnh, gắn với mặt sinh ra nó.
    """
    # ── ① MẶT TRÙNG MẶT PHẲNG CẮT ────────────────────────────────────────
    #
    # Thử TRƯỚC mọi thứ khác, và thử bằng mệnh đề chính xác *"mọi đỉnh của mặt
    # này nằm trên mặt phẳng"* thay vì bằng cách đếm điểm giao gom được. Đếm
    # điểm thì lẫn với ca một mặt suy biến, và hai ca ấy cần hai câu trả lời
    # khác nhau.
    for fi, f in enumerate(sol.faces):
        if all(pl.signed_eval(sol.vertices[j]) == 0 for j in f):
            return _thiet_dien_la_mat(sol, fi)

    # ── ② GOM ĐOẠN THEO MẶT, KHỬ TRÙNG THEO CẶP ĐẦU MÚT ──────────────────
    #
    # ĐÂY LÀ CHỖ `SECTION_COPLANAR_EDGE_GAP` SỐNG, và nó không phải một ca lạ:
    # một cạnh của khối nằm trọn trong mặt phẳng cắt thuộc về **hai** mặt kề,
    # nên cả hai mặt cùng báo đúng đoạn ấy. Thiết diện tam giác (SAC) của một
    # hình chóp vì thế gom được 5 đoạn cho 3 cạnh; vòng nối tiêu thụ hết 3 đoạn
    # thật rồi vấp 2 bản sao, không nối tiếp được, và bản trước quy tội cho
    # bảng mặt — một bảng mặt hoàn toàn đúng.
    #
    # Khử trùng bằng **cặp đầu mút chính xác**, không bằng chuỗi định dạng và
    # không bằng toạ độ làm tròn: `Point3` là `frozen dataclass` trên
    # `Fraction`, nên `frozenset` cho đúng quan hệ bằng hình học.
    #
    # An toàn với khối lồi: hai mặt phân biệt chung nhau nhiều nhất một cạnh,
    # nên hai mặt cho cùng một đoạn ⇔ đoạn ấy là cạnh chung của chúng. Khử
    # trùng vì thế không thể xoá mất một cạnh thật của thiết diện.
    doan: list[tuple[int, Point3, Point3]] = []
    da_gap: set[frozenset[Point3]] = set()
    for fi in range(len(sol.faces)):
        c = _canh_tren_mat(sol, fi, pl)
        if c is None:
            continue
        khoa = frozenset(c)
        if khoa in da_gap:
            continue
        da_gap.add(khoa)
        doan.append((fi, c[0], c[1]))

    if len(doan) < 3:
        raise _loi_suy_bien(sol, pl)

    # Nối vòng: mỗi cạnh phải khớp đầu mút với đúng một cạnh kế.
    thu_tu: list[SectionStep] = [SectionStep(doan[0][0], doan[0][1], doan[0][2])]
    con_lai = doan[1:]
    dinh = [doan[0][1], doan[0][2]]
    while con_lai:
        cuoi = dinh[-1]
        for k, (fi, a, b) in enumerate(con_lai):
            if a == cuoi or b == cuoi:
                tiep = b if a == cuoi else a
                thu_tu.append(SectionStep(fi, cuoi, tiep))
                dinh.append(tiep)
                con_lai.pop(k)
                break
        else:
            raise GeometryError(
                ERR_NOI_VONG,
                f"gom được {len(doan)} đoạn giao nhưng không nối tiếp được "
                f"thành chu trình (còn thừa {len(con_lai)}) — khối có thể "
                "KHÔNG LỒI",
            )

    if dinh[-1] != dinh[0]:
        raise GeometryError(
            ERR_NOI_VONG,
            "chu trình thiết diện không khép kín — khối có thể KHÔNG LỒI",
        )
    da_giac = tuple(dinh[:-1])
    _kiem_hau_dieu_kien(da_giac, pl)
    return Section(da_giac, tuple(thu_tu))


def _kiem_hau_dieu_kien(poly: tuple[Point3, ...], pl: Plane3) -> None:
    """Hậu điều kiện của chính `cross_section`, KHÔNG phải checker thứ hai.

    Đặt ở đây thay vì ở tầng nghĩa vụ là có chủ đích: ba mệnh đề dưới đây là
    lời hứa của **hàm này**, nên hàm này phải là chỗ nó vỡ. Một checker song
    song ở tầng trên sẽ kiểm lại cùng một điều bằng một cài đặt thứ hai — và
    hai cài đặt cùng một luật là hai chỗ để trôi khỏi nhau.
    """
    if len(poly) < 3:
        raise GeometryError(
            ERR_NOI_VONG,
            f"thiết diện chỉ có {len(poly)} đỉnh — cần ít nhất 3 để là đa giác",
        )
    if len(set(poly)) != len(poly):
        raise GeometryError(
            ERR_NOI_VONG, "thiết diện có đỉnh TRÙNG NHAU — vòng nối hỏng"
        )
    for i, v in enumerate(poly):
        if pl.signed_eval(v) != 0:
            raise GeometryError(
                ERR_NOI_VONG,
                f"đỉnh thứ {i + 1} của thiết diện KHÔNG nằm trên mặt phẳng cắt",
            )


# ── SO SÁNH HAI THIẾT DIỆN ────────────────────────────────────────────────
def _khoa(p: Point3) -> tuple[Fraction, Fraction, Fraction]:
    """Khoá sắp xếp CHÍNH XÁC. `Fraction` so trực tiếp — không có float ở đây."""
    return (p.x, p.y, p.z)


def canonical_cycle(poly: Sequence[Point3]) -> tuple[Point3, ...]:
    """Dạng chuẩn của một CHU TRÌNH đa giác — bất biến với xoay và với đảo hướng.

    `[A,B,C,D]`, `[B,C,D,A]`, `[D,C,B,A]` cho **cùng một** dạng chuẩn: chúng là
    cùng một đa giác, chỉ khác chỗ bắt đầu đọc và chiều đọc. `[A,C,B,D]` thì
    KHÁC — đó là một tứ giác khác, nối chéo.

    Cách làm: sinh cả **2n** ảnh của nhóm nhị diện (n phép xoay × 2 chiều) rồi
    lấy dãy nhỏ nhất theo khoá toạ độ. Chọn "xoay về đỉnh nhỏ nhất" thì rẻ hơn
    nhưng SAI khi có hai đỉnh cùng nhỏ nhất; ở đây `n ≤ vài chục` nên vét cạn
    là đúng và không đáng tiếc.

    ⚠️ Đây là so sánh HÌNH HỌC theo toạ độ chính xác, **không** phải so nhãn.
    Hai thiết diện cùng hình mà một bên đặt tên `MNPQ`, bên kia `PQMN` vẫn phải
    là một — nhãn là chuyện trình bày.
    """
    n = len(poly)
    if n == 0:
        return ()
    t = tuple(poly)
    ung = [c[i:] + c[:i] for c in (t, t[::-1]) for i in range(n)]
    return min(ung, key=lambda c: tuple(_khoa(p) for p in c))


def same_section_cycle(a: Sequence[Point3], b: Sequence[Point3]) -> bool:
    """Hai chu trình có phải cùng một đa giác không. Xoay/đảo hướng ⇒ CÙNG."""
    return len(a) == len(b) and canonical_cycle(a) == canonical_cycle(b)


# ── khối dựng sẵn, dùng cho demo và test ──────────────────────────────────
def box(w: Fraction | int = 1, d: Fraction | int = 1, h: Fraction | int = 1) -> Polyhedron:
    """Hình hộp chữ nhật, một góc ở gốc toạ độ. Mặt theo thứ tự vòng."""
    from .exact import Vec3

    v = tuple(
        Vec3.of(x, y, z)
        for x in (0, w) for y in (0, d) for z in (0, h)
    )  # chỉ số: (x,y,z) → 4x + 2y + z với 0/1
    return Polyhedron(
        vertices=v,
        faces=(
            (0, 2, 3, 1),  # x = 0
            (4, 5, 7, 6),  # x = w
            (0, 1, 5, 4),  # y = 0
            (2, 6, 7, 3),  # y = d
            (0, 4, 6, 2),  # z = 0
            (1, 3, 7, 5),  # z = h
        ),
    )


def pyramid_square(side: Fraction | int = 1, height: Fraction | int = 2) -> Polyhedron:
    """Chóp `S.ABCD` đáy vuông — cấu hình kinh điển của Toán 11.

    Đỉnh 0..3 = `A B C D` (đáy, `z=0`), đỉnh 4 = `S` trên `A`.
    """
    from .exact import Vec3

    return Polyhedron(
        vertices=(
            Vec3.of(0, 0, 0), Vec3.of(side, 0, 0),
            Vec3.of(side, side, 0), Vec3.of(0, side, 0),
            Vec3.of(0, 0, height),
        ),
        faces=((0, 3, 2, 1), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)),
    )
