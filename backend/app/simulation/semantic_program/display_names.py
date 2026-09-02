# -*- coding: utf-8 -*-
"""THẨM QUYỀN TÊN HIỂN THỊ — vật ngữ nghĩa được GỌI LÀ GÌ trước mặt học sinh.

    Semantic Program → Interpreter → **display_names** → Simulation State → Scene3D

─── VÌ SAO TỒN TẠI: MỘT THẨM QUYỀN ĐANG KHÔNG CÓ CHỦ ────────────────────────

`GEOMETRY_ARCHITECTURE_EXPRESSIVENESS_AUDIT §4` đo được: hợp đồng cảnh có đúng
**một** ô tên (`label`), và ô ấy gánh ba vai — ký hiệu ngắn in cạnh hình, tên
đọc được trong cây thành phần, mô tả trong ô soi. Khi mô hình không điền, `label`
**rơi về `id`**, và học sinh đọc `khoang_cach_hs √22` trên màn hình.

Hệ quả thứ hai, tệ hơn con số: tầng trình bày phải tự cắt gọt. `scene3d-
presentation.kyHieuNgan` đọc ngược `id` để có ký hiệu, `laVectoDangDiem` đọc
`producer` để đoán kiểu — renderer **suy lại ngữ nghĩa**, đúng thứ ranh giới R0
sinh ra để cấm.

Chỗ đúng để trả lời *"vật này gọi là gì"* là nơi biết **nó được dựng ra thế
nào**. Đó là tầng ngữ nghĩa, và đó là file này.

─── LUẬT SỐ MỘT: KHÔNG ĐỌC NGƯỢC ĐỊNH DANH ─────────────────────────────────

Tên hiển thị dẫn từ **phép dựng + toán hạng**, không từ hình dạng chuỗi của
`target_var`. Câu hỏi *"`A_prime` là ký hiệu gì"* có một thẩm quyền riêng đã tồn
tại — `source_entities.ky_hieu_toan` — và file này **gọi** nó chứ không tự bóc
tiền tố lần thứ hai.

─── LUẬT SỐ HAI: `id` KHÔNG BAO GIỜ LÀ TÊN MẶC ĐỊNH ────────────────────────

Thứ tự trả lời, đúng bốn bậc và **không có bậc thứ năm**:

    ① nhãn mô hình đã đặt, nếu nó thật sự là một cái tên;
    ② công thức gọi tên dẫn từ phép dựng (`_CACH_GOI`);
    ③ mô tả chung theo kiểu, kèm ký hiệu nếu có (*"Điểm A"*, *"Mặt phẳng"*);
    ✗ `id` thô — KHÔNG.

Bậc ① có một chốt: nhãn **trùng byte với `id`** chỉ được tin khi `id` ấy vốn là
một ký hiệu toán (`A`, `M`, `A'`). `label = "V_AMNP"` trùng `id = "V_AMNP"` thì
đó không phải mô hình đặt tên — đó là chưa ai đặt tên cả.

─── LUẬT SỐ BA: KÝ HIỆU CHỈ SINH KHI CÓ CĂN CỨ ────────────────────────────

`notation` là ký hiệu ngắn in cạnh vật trên khung 3D. Nó **được phép vắng**, và
`None` là câu trả lời đúng cho một khối tên `pyramid_S_ABCD`. Không bịa `M1`,
`P2` chỉ để có chữ — một nhãn bịa cạnh một vật là một mệnh đề sai về hình.

Hai nguồn hợp lệ, không có nguồn thứ ba:

  · **ghép từ ký hiệu của toán hạng** — `construct_plane(M,N,P)` → `(MNP)`,
    `measure.volume(khoi)` → `V(…)`. Đệ quy, và nó **đáy** ở ký hiệu của các
    điểm gốc.
  · **`ky_hieu_toan` của chính tên vật** — chỉ cho ĐIỂM và VECTƠ, những vật mà
    ký hiệu chính là tên. Với điểm gốc, `grounding_gate` đã chứng minh tên ấy
    **có trong đề** (`la_ten_nguon`, chốt ⑤ chống rửa năng lực), nên dùng nó
    không phải là tin lời mô hình.

─── ĐIỀU FILE NÀY KHÔNG LÀM ────────────────────────────────────────────────

Không hình học, không đọc `memory`, không chạm `exact`/`value`. Nó nhận **xuất
xứ** (`producer` + `sources` + `label`) và trả **chữ**. Bảng `_CACH_GOI` khoá
theo **phép dựng**, tuyệt đối không theo dạng bài: một nhánh `if "chóp" in …` ở
đây là special-case theo họ hình, đúng thứ `§7` của audit chứng minh là hiện
không có chỗ nào.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from .source_entities import ky_hieu_toan

__all__ = ["ten_hien_thi", "MO_TA_KIEU"]


#: Mô tả chung theo kiểu — bậc ③, khi không có nhãn lẫn công thức gọi tên.
#:
#: Cố ý **không** kèm ký hiệu ở đây; `_bac_ba` ghép ký hiệu vào nếu có. Tách ra
#: để bảng này thuần là "kiểu này gọi là gì trong tiếng Việt".
MO_TA_KIEU: dict[str, str] = {
    "point3": "Điểm",
    "vector3": "Vectơ",
    "line3": "Đường thẳng",
    "plane3": "Mặt phẳng",
    "polygon3": "Đa giác",
    "solid": "Khối đa diện",
    "section": "Thiết diện",
    "quantity": "Đại lượng đo",
}

#: Kiểu mà ký hiệu **chính là tên vật** — điểm và vectơ.
#:
#: Đường/mặt/khối KHÔNG nằm đây: `line_AB` không phải ký hiệu của đường `AB`,
#: và ký hiệu đúng của nó ghép được từ hai đầu mút. Cho chúng vào đây là mở
#: đường cho `plane_MNP` hiện nguyên si lên khung.
_KIEU_KY_HIEU_LA_TEN = ("point3", "vector3")


#: Danh từ NGẮN của mỗi kiểu, viết thường — dùng khi phải nhắc tới một vật
#: bên trong một câu khác mà nó không có ký hiệu.
#:
#: Tách khỏi `MO_TA_KIEU` (viết hoa, đứng một mình) vì hai vai khác nhau về
#: chính tả: *"Mặt phẳng"* mở đầu một câu, *"mặt phẳng"* nằm giữa một câu.
_DANH_TU_NGAN: dict[str, str] = {
    "point3": "điểm", "vector3": "vectơ", "line3": "đường thẳng",
    "plane3": "mặt phẳng", "polygon3": "đa giác", "solid": "khối",
    "section": "thiết diện", "quantity": "đại lượng",
}

#: Dấu bọc khi một CỤM TỪ được nhúng vào câu khác.
#:
#: ─── VÌ SAO CẦN, ĐO ĐƯỢC Ở WAVE G4 ─────────────────────────────────────
#:
#: Không bọc thì hai toán hạng dính vào nhau và câu thành mơ hồ:
#:
#:     Giao tuyến của Mặt phẳng qua B và vuông góc với SC và (ABCD)
#:                                   └── "và" của toán hạng ─┘ └── "và" nối ──┘
#:
#: Người đọc không tách được đâu là hết toán hạng thứ nhất. Bọc thì tách được
#: bằng CẤU TRÚC, không phải bằng cách đoán:
#:
#:     Giao tuyến của «Mặt phẳng qua B và vuông góc với SC» và (ABCD)
#:
#: Dùng guillemet chứ không dùng ngoặc đơn: ngoặc đơn đã mang nghĩa *mặt
#: phẳng* trong ký hiệu hình học (`(ABC)`), và mượn nó ở đây là dựng một nghĩa
#: thứ hai cho cùng một dấu.
_MO, _DONG = "«", "»"


def _boc(t: str) -> str:
    """Cụm nhiều chữ thì bọc; một ký hiệu thì để trần."""
    return f"{_MO}{t}{_DONG}" if " " in t else t


def _ghep(*phan: Optional[str]) -> Optional[str]:
    """Ghép ký hiệu toán hạng; thiếu **một** cái là hỏng cả — trả `None`.

    Fail-closed có chủ đích: `(M?P)` tệ hơn hẳn không có ký hiệu nào, vì nó
    trông như một ký hiệu thật.
    """
    return None if any(p is None for p in phan) else "".join(p for p in phan
                                                             if p is not None)


# ── ① CÔNG THỨC GỌI TÊN, khoá theo PHÉP DỰNG ───────────────────────────────
#
# Khoá là `producer` do `simulation_state._provenance` phát: `construct_point.
# <kind biểu thức>` cho điểm dựng, tên câu lệnh cho các phép dựng khác,
# `measure.<quantity>` cho phép đo, `<kind biểu thức>` cho `assign` hình học.
#
# Mỗi mục là `(dựng CÂU, dựng KÝ HIỆU)`. `None` ở vế thứ hai nghĩa là phép này
# không có ký hiệu ghép được — không phải quên.
#
# `s` là danh sách TÊN HIỂN THỊ của toán hạng, `k` là danh sách KÝ HIỆU của
# chúng (phần tử có thể `None`).
_CACH_GOI: dict[str, tuple[Callable[[list[str]], str],
                           Optional[Callable[[list[Optional[str]]], Optional[str]]]]] = {
    # ── điểm dựng ra ──────────────────────────────────────────────────────
    "construct_point.midpoint": (
        lambda s: f"Trung điểm của {s[0]} và {s[1]}", None),
    "construct_point.divide_segment": (
        lambda s: f"Điểm chia đoạn nối {s[0]} và {s[1]}", None),
    "construct_point.translate": (
        lambda s: f"Ảnh của {s[0]} qua phép tịnh tiến theo {s[1]}", None),
    "construct_point.project_onto": (
        lambda s: f"Hình chiếu của {s[0]} lên {s[1]}", None),
    "construct_point.intersect_line_plane": (
        lambda s: f"Giao điểm của {s[0]} và {s[1]}", None),
    "construct_point.intersect_line_line": (
        lambda s: f"Giao điểm của {s[0]} và {s[1]}", None),
    # ── vật dựng ra ───────────────────────────────────────────────────────
    "construct_line": (
        lambda s: f"Đường thẳng qua {s[0]} và {s[1]}", lambda k: _ghep(k[0], k[1])),
    "construct_plane": (
        lambda s: f"Mặt phẳng qua {', '.join(s)}",
        lambda k: _ghep("(", *k, ")")),
    "construct_polygon": (
        lambda s: f"Đa giác {', '.join(s)}", lambda k: _ghep(*k)),
    "construct_solid": (
        lambda s: f"Khối đa diện dựng từ {', '.join(s)}", None),
    "construct_section": (
        lambda s: f"Thiết diện của {s[0]} cắt bởi {s[1]}", None),
    "intersect_plane_plane": (
        lambda s: f"Giao tuyến của {s[0]} và {s[1]}", None),
    "plane_perpendicular_to_line": (
        lambda s: f"Mặt phẳng qua {s[0]} và vuông góc với {s[1]}", None),
    "vector_from_points": (
        lambda s: f"Vectơ từ {s[0]} đến {s[1]}", lambda k: _ghep(k[0], k[1])),
    # ── phép ĐO ───────────────────────────────────────────────────────────
    #
    # Tên phải nói đúng ĐẠI LƯỢNG, không nói đại lượng gần đúng: giá trị của
    # `angle_cos_sq` là **cos² của góc**, không phải góc. Gọi nó là "Góc giữa…"
    # rồi in ra `1/2` là để học sinh đọc một con số dưới một cái tên sai.
    "measure.distance": (
        lambda s: f"Khoảng cách giữa {s[0]} và {s[1]}",
        lambda k: _ghep("d(", k[0], ", ", k[1], ")")),
    "measure.angle_cos_sq": (
        lambda s: f"Côsin bình phương của góc giữa {s[0]} và {s[1]}",
        lambda k: _ghep("cos²(", k[0], ", ", k[1], ")")),
    "measure.angle_cos": (
        lambda s: f"Côsin của góc giữa {s[0]} và {s[1]}",
        lambda k: _ghep("cos(", k[0], ", ", k[1], ")")),
    "measure.volume": (
        lambda s: f"Thể tích {s[0]}", lambda k: _ghep("V(", k[0], ")")),
}


def _la_ten_that(nhan: Any, ten: str) -> bool:
    """Nhãn mô hình đặt có phải một cái TÊN, hay chỉ là định danh chép lại?

    Trùng byte với `id` thì chỉ tin khi `id` ấy vốn là ký hiệu toán. `label =
    "A"` trên điểm `A` là mô hình nói đúng; `label = "V_AMNP"` trên `V_AMNP` là
    chưa ai đặt tên cả.
    """
    if not isinstance(nhan, str) or not nhan.strip():
        return False
    return nhan != ten or ky_hieu_toan(ten) is not None


def ten_hien_thi(
    thong_tin: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Optional[str]]]:
    """`{tên: {type, producer, sources, label}}` → bốn trường hiển thị mỗi vật.

    ─── BỐN VAI, KHÔNG PHẢI MỘT TRƯỜNG GÁNH TẤT ────────────────────────────

        `label`      TÊN của vật — thứ đứng ở tiêu đề, ở cây thành phần.
        `notation`   KÝ HIỆU toán, hoặc `None`. In cạnh vật trên khung 3D.
        `reference`  CÁCH GỌI NGẮN khi vật này bị nhắc **trong câu của vật
                     khác**. Luôn có; không bao giờ là một câu dài.
        `role`       *"vật này là gì"* — một dòng dưới tên, không lặp lại tên.

    Trước 2026-09-03 chỉ có hai trường đầu, nên hai chỗ phải chữa cháy: câu
    của vật này nhúng **nguyên tên** của vật kia (đẻ ra *"Giao tuyến của Mặt
    phẳng qua B và vuông góc với SC và (ABCD)"*), và `role` phải dựng ở
    **frontend** bằng một bảng `producer → tiếng Việt` thứ hai. Cả hai biến
    mất khi tách đúng bốn vai.


    Nhận **toàn bộ** bảng một lần chứ không từng vật, vì ký hiệu của một vật
    dựng ghép từ ký hiệu các toán hạng — `(MNP)` cần biết `M`, `N`, `P` trước.
    Giải bằng đệ quy có ghi nhớ; toán hạng chưa có mặt trong bảng (đã bị lọc
    khỏi cảnh, hoặc là một hằng) thì coi như **không có ký hiệu**, và
    `_ghep` fail-closed lo phần còn lại.

    Đồ thị phụ thuộc của Semantic Program là DAG — `ir_static_check` cưỡng chế
    thứ tự định-nghĩa-trước-dùng — nhưng vòng lặp vẫn được chặn bằng `dang_giai`
    thay vì tin vào lời hứa ấy: một vòng ở đây là đệ quy vô hạn giữa lúc dựng
    cảnh, tức mất cả lượt chạy chứ không phải một nhãn xấu.
    """
    ky_hieu: dict[str, Optional[str]] = {}
    nhan: dict[str, str] = {}
    goi_ngan: dict[str, str] = {}
    vai: dict[str, str] = {}
    dang_giai: set[str] = set()

    def giai(ten: str) -> None:
        if ten in ky_hieu or ten in dang_giai:
            return
        dang_giai.add(ten)
        o = thong_tin[ten]
        loai = o.get("type") or ""
        prod = o.get("producer")
        nguon = [s for s in (o.get("sources") or []) if isinstance(s, str)]
        for s in nguon:
            if s in thong_tin:
                giai(s)

        cong_thuc = _CACH_GOI.get(prod or "")
        du_nguon = cong_thuc is not None and all(s in thong_tin for s in nguon)

        # ── KÝ HIỆU ────────────────────────────────────────────────────────
        kh: Optional[str] = None
        # ① Nhãn mô hình đặt, KHI nó tự nó đã là một ký hiệu toán. `S.ABCD` là
        #    ký hiệu chuẩn của một khối chóp và không phép ghép nào dựng lại
        #    được nó — thứ tự đỉnh–đáy không suy ra từ bảng mặt. `(ABCD)` hay
        #    `thiết diện` thì không phải ký hiệu, và `ky_hieu_toan` nói không.
        nhan_khai = o.get("label")
        if isinstance(nhan_khai, str):
            kh = ky_hieu_toan(nhan_khai.strip())
        # ② Tên vật, cho những kiểu mà ký hiệu CHÍNH LÀ tên.
        if kh is None and loai in _KIEU_KY_HIEU_LA_TEN:
            kh = ky_hieu_toan(ten)
        # ③ Ghép từ ký hiệu các toán hạng.
        if kh is None and du_nguon and cong_thuc[1] is not None:
            try:
                kh = cong_thuc[1]([ky_hieu.get(s) for s in nguon])
            except (IndexError, TypeError):
                kh = None
        ky_hieu[ten] = kh

        # ── CÂU GỌI TÊN, dựng ở HAI ĐỘ CHI TIẾT ──────────────────────────
        #
        # Cùng một công thức, hai bộ toán hạng — nên chỉ có MỘT bảng và không
        # có chỗ cho hai bản lệch nhau:
        #
        #   câu ĐẦY ĐỦ  toán hạng = ký hiệu, hoặc CÁCH GỌI NGẮN của nó (bọc
        #               nếu là cụm từ). Đây là tên của vật.
        #   cách gọi    toán hạng = ký hiệu, hoặc DANH TỪ theo kiểu. Không bao
        #   NGẮN        giờ nhúng một cụm từ, nên đệ quy dừng ở một tầng và
        #               không có câu nào dài vô hạn.
        cau: Optional[str] = None
        cau_ngan: Optional[str] = None
        if du_nguon:
            try:
                cau = cong_thuc[0](
                    [_boc(ky_hieu.get(s) or goi_ngan.get(s, s)) for s in nguon])
                cau_ngan = cong_thuc[0]([
                    ky_hieu.get(s)
                    or _DANH_TU_NGAN.get(thong_tin.get(s, {}).get("type") or "",
                                         "đối tượng")
                    for s in nguon])
            except (IndexError, TypeError):
                cau = cau_ngan = None

        # ── TÊN HIỂN THỊ ──────────────────────────────────────────────────
        # ① nhãn mô hình đặt · ② câu gọi tên · ③ mô tả chung theo kiểu
        if _la_ten_that(o.get("label"), ten):
            nhan[ten] = str(o["label"]).strip()
        elif cau is not None:
            nhan[ten] = cau
        else:
            nhan[ten] = _bac_ba(loai, kh)

        # ── CÁCH GỌI NGẮN — dùng khi vật này bị NHẮC TRONG một câu khác ───
        goi_ngan[ten] = kh or cau_ngan or _DANH_TU_NGAN.get(loai, "đối tượng")

        # ── VAI TRÒ — *"vật này là gì"*, một dòng dưới tên ────────────────
        #
        # Trùng tên thì nói danh từ theo kiểu thay vì lặp lại: hai dòng giống
        # hệt nhau không thêm thông tin nào, chỉ chiếm chỗ.
        vai[ten] = (MO_TA_KIEU.get(loai, "Đối tượng")
                    if cau is None or cau == nhan[ten] else cau)
        dang_giai.discard(ten)

    for ten in thong_tin:
        giai(ten)

    return {t: {"label": nhan[t], "notation": ky_hieu[t],
                "reference": goi_ngan[t], "role": vai[t]}
            for t in thong_tin}


def _bac_ba(loai: str, kh: Optional[str]) -> str:
    """Mô tả chung theo kiểu, kèm ký hiệu nếu có. **Không bao giờ trả `id`.**

    Kiểu lạ ⇒ *"Đối tượng"*. Nghèo nàn, và đó là điểm: một kiểu mới thêm vào
    `MemoryType` mà quên bảng này sẽ hiện ra ngay trên màn hình, thay vì lặng
    lẽ in định danh máy như bản trước.
    """
    goc = MO_TA_KIEU.get(loai, "Đối tượng")
    return f"{goc} {kh}" if kh else goc
