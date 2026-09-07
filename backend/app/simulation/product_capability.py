# -*- coding: utf-8 -*-
"""THẨM QUYỀN NĂNG LỰC SẢN PHẨM — *"nút nào được hiện là ĐÃ HỖ TRỢ"*.

─── VÌ SAO TÁCH KHỎI NĂNG LỰC HỆ ──────────────────────────────────────────

Kho này đã đo được rằng hai câu dưới đây **khác nhau**, và trộn chúng là cách
một sản phẩm hứa quá:

    NĂNG LỰC HỆ      IR · runtime · thẩm định · vết · vận chuyển · vẽ chạy được
    NĂNG LỰC SẢN PHẨM  … VÀ mô hình thật sự sinh ra được chương trình ấy từ đề

`PHASE_2_CURVED_SOLID_FOUNDATION` đóng lại với `SYSTEM_CURVED_FOUNDATION =
CLOSED` mà `CURVED_PRODUCT_ENABLED = NO` — đúng khoảng cách ấy. Một khối cầu
dựng được bằng tay không nói gì về việc mô hình có dựng nổi nó từ một đề tiếng
Việt hay không, và chỉ một phép đo mới trả lời được.

─── VÌ SAO Ở BACKEND, KHÔNG Ở FRONTEND ────────────────────────────────────

Trước bản này frontend không có nơi nào để hỏi *"hình này đã hỗ trợ chưa"*, nên
câu trả lời sẽ là một danh sách viết tay trong một component — tức một **danh
sách mong muốn**, và nó sẽ trôi khỏi sự thật ngay lần đầu một phép đo trả kết
quả khác kỳ vọng. Bảng này là chỗ duy nhất câu ấy được trả lời.

⚠️ **Chỉ đổi khi có BẰNG CHỨNG ĐO ĐƯỢC.** Mỗi mục phải nêu artifact; không
artifact ⇒ không được `SUPPORTED`. Đây là cùng một luật mà `STATUS_LEDGER` áp
cho mọi dòng DONE.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

__all__ = [
    "TrangThai",
    "NangLucSanPham",
    "NANG_LUC_SAN_PHAM",
    "da_ho_tro",
    "bang_cho_frontend",
]

#: `supported` — đủ bằng chứng, hiện được như một năng lực.
#: `foundation_only` — hệ chạy được, **mô hình chưa được đo**. Không hiện.
#: `unsupported` — ngoài phạm vi, và sẽ ở ngoài.
TrangThai = Literal["supported", "foundation_only", "unsupported"]


@dataclass(frozen=True)
class NangLucSanPham:
    """Một năng lực nhìn từ phía người dùng."""

    ma: str
    #: Tên tiếng Việt hiện trên bề mặt. Học sinh đọc câu này, không đọc `ma`.
    ten: str
    trang_thai: TrangThai
    #: BẰNG CHỨNG, hoặc lý do chưa có. Trống ⇒ không được `supported`.
    bang_chung: str

    def __post_init__(self) -> None:
        if self.trang_thai == "supported" and not self.bang_chung.strip():
            raise ValueError(
                f"'{self.ma}' khai supported mà không nêu bằng chứng — "
                "STATUS_LEDGER cấm đúng hình này")


#: BẢNG DUY NHẤT. Frontend đọc bản dẫn xuất, không tự khai lại.
NANG_LUC_SAN_PHAM: dict[str, NangLucSanPham] = {
    n.ma: n for n in (
        NangLucSanPham(
            "polyhedron", "Hình chóp · lăng trụ · hộp", "supported",
            "PHASE_7B + 5 bài mẫu offline + tám phép đo trình duyệt"),
        NangLucSanPham(
            "section", "Thiết diện", "supported",
            "SECTION_COPLANAR_EDGE_RUNTIME_FIX · certify-section-coplanar-edge 7/7"),
        # ── HÌNH CONG ────────────────────────────────────────────────────
        #
        # Hệ chạy trọn (Phase 2: 63 ca, sáu nhân chứng đi hết đường IR) và có
        # sáu bài mẫu offline (Phase 3 §5). Thứ còn THIẾU là duy nhất một điều:
        # **chưa đo được mô hình có sinh ra chương trình ấy từ đề hay không**.
        # Cho tới khi có con số, ba dòng này là `foundation_only`.
        NangLucSanPham(
            "ball", "Hình cầu", "foundation_only",
            "hệ: Phase 2 CLOSED · offline: 2 bài mẫu · MÔ HÌNH: chưa đo"),
        NangLucSanPham(
            "cylinder", "Hình trụ", "foundation_only",
            "hệ: Phase 2 CLOSED · offline: 2 bài mẫu · MÔ HÌNH: chưa đo"),
        NangLucSanPham(
            "cone", "Hình nón", "foundation_only",
            "hệ: Phase 2 CLOSED · offline: 2 bài mẫu · MÔ HÌNH: chưa đo"),
        # ── NGOÀI PHẠM VI, và sẽ ở ngoài ─────────────────────────────────
        NangLucSanPham(
            "solid_of_revolution", "Khối tròn xoay", "unsupported",
            "thể tích cần tích phân — ngoài miền số ℚ(√, π)"),
        NangLucSanPham(
            "composite_subtractive", "Khối ghép · khối bù", "unsupported",
            "biên CSG cần phức hợp ô hỗn hợp; ngoài phạm vi khoá luận"),
        NangLucSanPham(
            # ⚠️ `unsupported` → `foundation_only` (2026-09-07,
            # `CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_CYLINDER_ELLIPSE_
            # FOUNDATION`). Lý do cũ — *"không có kiểu conic trong IR"* — nay
            # SAI: `ellipse3` + `intersect_plane_curved_ellipse` tồn tại, và
            # ca chuẩn cho `9√2π` CHÍNH XÁC qua trọn đường sản phẩm.
            #
            # `foundation_only`, KHÔNG phải `supported`: hệ diễn đạt và tính
            # đúng, nhưng **chưa ai đo** mô hình có tự tìm ra phép ấy không.
            # Chuyển sang `supported` cần một wave riêng có bằng chứng
            # discoverability và acceptance ổn định — cùng luật đang áp cho
            # ball/cylinder/cone.
            #
            # Phạm vi V1 hẹp và nói thẳng: chỉ HÌNH TRỤ, mặt phẳng xiên (không
            # ⊥, không ∥ trục), elip nằm TRỌN giữa hai đáy. Thiết diện xiên
            # của NÓN vẫn ngoài phạm vi — elip/parabol/hyperbol tuỳ độ dốc,
            # ba nhánh chưa phân xử.
            "curved_oblique_section", "Thiết diện xiên của hình trụ",
            "foundation_only",
            "hệ: elip đầy đủ của trụ CLOSED (kernel + IR + đo + trace + "
            "Scene3D, ca chuẩn 9√2π chính xác) · nón xiên: NGOÀI phạm vi · "
            "MÔ HÌNH: chưa đo"),
    )
}


def da_ho_tro(ma: str) -> bool:
    n = NANG_LUC_SAN_PHAM.get(ma)
    return n is not None and n.trang_thai == "supported"


def bang_cho_frontend() -> list[dict[str, str]]:
    """Bản dẫn xuất gửi sang giao diện. Không kèm `bang_chung`.

    Bằng chứng là chuyện của kho mã và của báo cáo, không phải chuyện của học
    sinh — bày nó lên màn hình là bắt người học đọc nhật ký kỹ thuật.
    """
    return [{"ma": n.ma, "ten": n.ten, "trang_thai": n.trang_thai}
            for n in NANG_LUC_SAN_PHAM.values()]
