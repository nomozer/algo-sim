# -*- coding: utf-8 -*-
"""Hồ sơ MIỀN của route ngữ nghĩa — mỗi miền có từ vựng `analyze` riêng.

VÌ SAO TỒN TẠI, ĐO ĐƯỢC Ở PHASE 5 (2026-08-24): `stage_semantic_program` đã
được ép sang prompt hình học, nhưng `stage_semantic_analyze` thì không. Enum
nghĩa vụ của nó là `sorted(OBLIGATION_KINDS)` — **cả 19**, gồm 9 nghĩa vụ Tin
học. Hệ quả đo được trên 6 bài hình học hợp lệ:

    geo_02  đề hỏi `point_on_line`  → mô hình khai `derived_sequence`
    geo_03  đề hỏi `coplanar`       → mô hình khai `structural_traversal`
    geo_04  đề hỏi `point_on_plane` → mô hình khai `predicate_verdict`

`obligation_match` 3/6. Không phải mô hình kém: prompt phân tích **chưa từng
nhắc tới hình học**, mà enum thì mời gọi cả chín cái tên Tin học. Bắt ai đó
chọn đúng trong một danh sách sai là một bài kiểm tra hỏng.

─── LUẬT DẪN XUẤT, KHÔNG CHÉP TAY ────────────────────────────────────────────

Tập nghĩa vụ của mỗi miền **suy ra từ bảng kiểu container** trong
`obligations.OBLIGATION_KINDS`, không viết lại thành một danh sách thứ hai. Lý
do đã trả giá ở kho này nhiều lần: hai danh sách rời nhau thì lần thêm nghĩa vụ
tiếp theo sẽ lệch, và lệch **câm** — miền mới có checker mà `analyze` không có
từ để khai.

Phép thử: nghĩa vụ nào nhận TOÀN BỘ chủ thể là kiểu hình học thì thuộc miền
hình học. Nghĩa vụ nhận cả hai (không có cái nào hiện giờ) sẽ thuộc **cả hai** —
đó là hành vi đúng, không phải kẽ hở.

─── FAIL-SAFE CỦA BỘ NHẬN MIỀN ───────────────────────────────────────────────

`detect_domain` là **suy đoán**, và nó được thiết kế để đoán sai về phía an
toàn: không đủ dấu hiệu ⇒ trả `tin_hoc`, tức **đúng hành vi hiện tại**. 24
target Tin học không thể bị bộ nhận miền làm hỏng, vì cửa duy nhất nó mở là cửa
đi sang hình học.

Đường đo (`run_geometry_dev_evaluation.py`) **không dùng** bộ nhận miền — nó
truyền `domain` thẳng. Phép đo không được phụ thuộc vào một suy đoán.
"""
from __future__ import annotations

from .geometry_exec import GEOMETRY_TYPES
import re

from .obligations import OBLIGATION_KINDS

DOMAIN_TIN_HOC = "tin_hoc"
DOMAIN_HINH_HOC = "hinh_hoc"
DOMAINS = (DOMAIN_TIN_HOC, DOMAIN_HINH_HOC)


def geometry_obligation_kinds() -> frozenset[str]:
    """Nghĩa vụ nhận TOÀN BỘ chủ thể là kiểu hình học. Dẫn xuất, không chép."""
    return frozenset(
        k for k, chu_the in OBLIGATION_KINDS.items()
        if chu_the and chu_the <= GEOMETRY_TYPES
    )


def tin_hoc_obligation_kinds() -> frozenset[str]:
    """Phần bù. Nghĩa vụ dùng được ở CẢ HAI miền sẽ có mặt ở cả hai tập."""
    geo = geometry_obligation_kinds()
    return frozenset(
        k for k, chu_the in OBLIGATION_KINDS.items()
        if k not in geo or not (chu_the <= GEOMETRY_TYPES)
    )


def obligation_kinds_for(domain: str) -> frozenset[str]:
    if domain == DOMAIN_HINH_HOC:
        return geometry_obligation_kinds()
    return tin_hoc_obligation_kinds()


#: MANH MỐI VĂN BẢN → NGHĨA VỤ CHÍNH TẮC. Khoá phải có checker thật.
#:
#: ─── VÌ SAO CẦN, ĐO ĐƯỢC 2026-08-29 (canary V2) ─────────────────────────────
#:
#: Cổng phạm vi có HAI vế. Vế `domain_scope` đã được miễn cho hình học từ
#: Wave 2; vế `simulatability` thì chưa, và nó giết bài A10 (góc đường–mặt)
#: ngay trước tầng sinh với `gate_not_simulation_suitable`.
#:
#: Cùng một bệnh với vế kia: `REQUIRES_SIMULATION` =
#: {INTERACTIVE_MODEL, INTERACTIVE_ARTIFACT, MEANINGFUL_TRACE} — **không nhãn
#: nào cho một bài hình học tĩnh**. Mô hình buộc phải chọn một nhãn sai, và
#: một cổng tất định lại coi phán quyết rỗng nghĩa ấy là có thẩm quyền.
#:
#: ─── VÌ SAO KHÔNG MIỄN THẲNG CHO `hinh_hoc` ─────────────────────────────────
#:
#: *"Là hình học ⇒ luôn mô phỏng được"* là luật ÂM: nó miễn dựa trên việc bài
#: KHÔNG thuộc môn khác. Đề hình học ngoài năng lực (mặt cầu, góc nhị diện có
#: miền, phương trình mặt phẳng Oxyz) sẽ đi lọt tới tầng sinh rồi hỏng ở một
#: cổng sâu hơn, với một lời từ chối khó đọc hơn nhiều.
#:
#: Luật ở đây là DƯƠNG: miễn khi đề ánh xạ được tới một nghĩa vụ **có đường
#: biểu diễn và đường thực thi thật**. Khoá của bảng dẫn từ `GEOMETRY_CHECKERS`
#: — thêm một manh mối cho nghĩa vụ không có checker là mở năng lực, và test
#: khoá điều đó.
_MANH_MOI_NGHIA_VU: dict[str, tuple[str, ...]] = {
    "angle": ("góc giữa", "góc tạo bởi", "số đo góc", "côsin của góc",
              "cosin của góc", "tính góc", "hợp với nhau một góc",
              "góc phẳng nhị diện", "góc nhị diện"),
    "distance": ("khoảng cách",),
    "volume": ("thể tích",),
    "parallel": ("song song", "∥", "//"),
    "perpendicular": ("vuông góc", "⊥"),
    "coplanar": ("đồng phẳng", "thiết diện"),
    "point_on_line": ("giao tuyến", "thuộc đường thẳng", "nằm trên đường thẳng"),
    "point_on_plane": ("giao điểm", "thuộc mặt phẳng", "nằm trên mặt phẳng"),
}


def nghia_vu_ung_vien(text: str) -> frozenset[str]:
    """Nghĩa vụ hình học mà đề CÓ THỂ đang hỏi, dẫn từ manh mối văn bản.

    Đây **không** phải bộ trích nghĩa vụ — việc ấy thuộc `semantic_analyze` và
    cần LLM. Nó chỉ trả lời một câu hẹp hơn, và trả lời được ở phía server
    trước mọi lượt gọi: *"hệ có đường biểu diễn nào cho thứ đề này hỏi
    không?"*
    """
    if not text:
        return frozenset()
    t = text.lower()
    return frozenset(k for k, cum in _MANH_MOI_NGHIA_VU.items()
                     if any(c in t for c in cum))


def co_duong_thuc_thi(text: str, domain: str) -> bool:
    """Bài hình học này có nghĩa vụ nào hệ thực thi được không?

    Fail-closed ở cả ba chỗ: miền không phải hình học · không manh mối nào ·
    manh mối trỏ nghĩa vụ không có checker.
    """
    if domain != DOMAIN_HINH_HOC:
        return False
    from .geometry_obligations import GEOMETRY_CHECKERS
    return bool(nghia_vu_ung_vien(text) & set(GEOMETRY_CHECKERS))


#: Kiểu mục dữ liệu đề cho, theo miền.
#:
#: Miền hình học KHÔNG dùng `array`/`graph`/`tree_node`: dữ kiện của nó là *"cạnh
#: đáy bằng 1"*, *"SA ⊥ (ABCD)"* — một số đo hoặc một quan hệ, không phải một
#: cấu trúc dữ liệu. Cho `analyze` nguyên bảng kiểu Tin học là mời nó khai hình
#: chóp thành `array`, và mọi thứ phía sau sẽ hỏng theo một cách khó đọc.
INPUT_FACT_KINDS_HINH_HOC = ("float", "int", "str", "bool")


def analyze_skill_for(domain: str) -> str:
    """Skill nào đọc đề ở miền này."""
    return "geometry_analyze" if domain == DOMAIN_HINH_HOC else "semantic_analyze"


def program_skill_for(domain: str) -> str:
    """Skill nào viết chương trình ở miền này."""
    return (
        "geometry_program_generator"
        if domain == DOMAIN_HINH_HOC
        else "semantic_program"
    )


# ── Bộ nhận miền — TẤT ĐỊNH, và cố ý thiên về `tin_hoc` ───────────────────
#
# Hai hạng dấu hiệu, khác nhau ở mức RIÊNG BIỆT chứ không ở độ "quan trọng":
#
#   MẠNH  — cụm chỉ xuất hiện trong hình học không gian. Một cái là đủ.
#   YẾU   — cụm hình học nhưng dùng chung được với văn cảnh khác. Cần ba cái,
#           để một đề Tin học lỡ nhắc "song song" không bị kéo sang.
#
# Ngưỡng 3 không phải số đẹp: nó là số nhỏ nhất mà bài `geo_08` (hình vuông
# phẳng, không có cụm mạnh nào) vẫn qua được — `mặt phẳng`, `đường thẳng`,
# `đường chéo`, `góc giữa` = 4. Hạ xuống 2 là nới không có lý do.
#: CỤM MẠNH — một mình nó đủ kết luận `hinh_hoc`.
#:
#: ─── LỖ ĐO ĐƯỢC Ở PHASE 7B CHÍNH THỨC (2026-08-29) ──────────────────────────
#:
#: `hình lập phương` KHÔNG có trong danh sách này — khối phổ biến nhất của hình
#: học không gian THPT, và là khối mà bốn ô của `BANG_O` dùng (A06 · A08 · A09
#: · A10). Hậu quả đo được: hai ô GÓC chết ở cổng phạm vi **3/3 lượt mỗi ô**,
#: `stage_reached = "scope"`, 0 nghĩa vụ — đề bị loại TRƯỚC khi tầng sinh có
#: cơ hội nào, và học sinh nhận tấm thẻ *"bài này thuộc môn khác"* cho một đề
#: nằm đúng giữa chương trình Toán 11.
#:
#: Vì sao lỗ ấy sống được: đề góc trên hình lập phương thường RẤT NGẮN và chỉ
#: gom được hai cụm yếu (`góc giữa`, `đường thẳng`), dưới ngưỡng ba. Ngưỡng ba
#: không sai — nó là thứ chặn 4/5 đề Tin học bị kéo nhầm — nhưng nó đòi đề
#: hình học phải *dài*, và đề góc thì không.
#:
#: Thêm cả biến thể `khối …` cho những khối ĐÃ có tên ở đây: SGK gọi cùng một
#: vật bằng hai cách (`hình hộp` / `khối hộp`), và để sót một cách là để lại
#: đúng cái lỗ vừa vá.
#:
#: ⚠️ Đây **không** phải nới năng lực. Danh sách này quyết định MIỀN (Toán hay
#: Tin), không quyết định KHẢ NĂNG. `mặt cầu`/`hình nón`/`hình trụ` đã nằm đây
#: từ trước dù kernel không dựng được mặt cong — và đúng như vậy: định tuyến
#: về hình học rồi từ chối trung thực ở cổng sau thì tốt hơn nhiều so với dán
#: nhãn *"môn khác"*.
#: ─── HAI LỚP CỤM MẠNH, VÀ VÌ SAO PHẢI TÁCH ─────────────────────────────────
#:
#: Lớp ① — **quan hệ/phép dựng** chỉ có trong hình học không gian. `thiết
#: diện`, `giao tuyến`, `đồng phẳng`, `chéo nhau` không xuất hiện trong đề Tin
#: học ở bất kỳ nghĩa nào. Chúng THẮNG cả phủ quyết Tin học: một đề nói *"viết
#: chương trình dựng thiết diện của hình chóp"* vẫn là bài hình học được diễn
#: đạt bằng giọng lập trình.
#:
#: Lớp ② — **danh từ khối**. `hình chóp`, `lăng trụ`, `mặt cầu`, `hình lập
#: phương` xuất hiện tự nhiên trong đề Tin học: hình học tính toán, đồ thị trên
#: lăng trụ, đếm cặp mặt cầu giao nhau. Nên chúng KHÔNG thắng phủ quyết.
#:
#: Đo được 2026-08-29, ba đề Tin học hợp lệ bị kéo sang hình học vì lớp ② được
#: đối xử như lớp ①:
#:
#:     "Viết chương trình tính thể tích HÌNH CHÓP tam giác đều."
#:     "Viết chương trình duyệt đồ thị LĂNG TRỤ bằng BFS."
#:     "Cho mảng các MẶT CẦU, viết thuật toán đếm số cặp giao nhau."
#:
#: Ranh giới giữa hai lớp không phải cảm tính: lớp ① gọi tên một QUAN HỆ hoặc
#: PHÉP DỰNG, lớp ② gọi tên một VẬT. Đề hỏi *làm gì* chứ không hỏi *có vật
#: gì* — nên chỉ lớp ① mới là bằng chứng về việc.
_MANH_QUAN_HE = (
    "thiết diện", "giao tuyến", "mặt phẳng đáy",
    "vuông góc với đáy", "vuông góc với mặt phẳng", "hình chiếu vuông góc",
    "đồng phẳng", "chéo nhau",
)

#: ─── LỖ ĐO ĐƯỢC Ở PHASE 7B CHÍNH THỨC (2026-08-29) ──────────────────────────
#:
#: `hình lập phương` KHÔNG có ở đây — khối phổ biến nhất của hình học không
#: gian THPT, và là khối mà bốn ô của `BANG_O` dùng (A06 · A08 · A09 · A10).
#: Hậu quả đo được: hai ô GÓC chết ở cổng phạm vi **3/3 lượt mỗi ô**,
#: `stage_reached = "scope"`, 0 nghĩa vụ — đề bị loại TRƯỚC khi tầng sinh có
#: cơ hội nào, và học sinh nhận tấm thẻ *"bài này thuộc môn khác"* cho một đề
#: nằm đúng giữa chương trình Toán 11.
#:
#: Vì sao lỗ ấy sống được: đề góc trên hình lập phương thường RẤT NGẮN, chỉ
#: gom được hai cụm yếu (`góc giữa`, `đường thẳng`), dưới ngưỡng ba. Ngưỡng ba
#: không sai — nó chặn 4/5 đề Tin học bị kéo nhầm — nhưng nó đòi đề hình học
#: phải *dài*, và đề góc thì không.
#:
#: Thêm cả biến thể `khối …` cho khối ĐÃ có tên: SGK gọi cùng một vật bằng hai
#: cách (`hình hộp` / `khối hộp`), để sót một cách là để lại đúng lỗ vừa vá.
#:
#: ⚠️ Đây **không** phải nới năng lực. Danh sách này quyết định MIỀN (Toán hay
#: Tin), không quyết định KHẢ NĂNG. `mặt cầu`/`hình nón`/`hình trụ` đã nằm đây
#: từ trước dù kernel không dựng được mặt cong — và đúng như vậy: định tuyến
#: về hình học rồi từ chối trung thực ở cổng sau thì tốt hơn nhiều so với dán
#: nhãn *"môn khác"*.
_MANH_DANH_TU_KHOI = (
    "hình chóp", "khối chóp", "tứ diện", "lăng trụ", "hình hộp", "hình nón",
    "hình trụ", "mặt cầu",
    # ── bổ sung sau Phase 7B ─────────────────────────────────────────────
    "hình lập phương", "khối lập phương",
    "khối hộp", "khối lăng trụ", "khối đa diện", "hình đa diện",
    "khối cầu", "khối nón", "khối trụ",
)

#: Giữ tên cũ: nhiều test và bảng đồng bộ đọc nó như "toàn bộ cụm mạnh".
_DAU_HIEU_MANH = _MANH_QUAN_HE + _MANH_DANH_TU_KHOI
_DAU_HIEU_YEU = (
    "mặt phẳng", "đường thẳng", "đường chéo", "góc giữa", "trung điểm",
    "hình vuông", "hình chữ nhật", "tam giác", "thể tích", "khoảng cách từ",
    "song song", "vuông góc", "cạnh bên", "đáy",
)


#: DẤU HIỆU TIN HỌC — phủ quyết đường YẾU, và CHỈ đường yếu.
#
# ─── VÌ SAO CẦN, ĐO ĐƯỢC 2026-08-26 ──────────────────────────────────────────
#
# Bốn trên năm đề Tin học HỢP LỆ bị kéo sang hình học chỉ vì đủ ba cụm yếu:
#
#     "Cho toạ độ ba đỉnh một tam giác. VIẾT CHƯƠNG TRÌNH kiểm tra tam giác đó
#      có vuông góc ở đỉnh A không, và tính trung điểm cạnh BC."
#      → trung điểm · tam giác · vuông góc = 3 ⇒ hinh_hoc. Sai.
#
# Chúng không phải đề bịa: hình học tính toán, đồ hoạ và bài toán lưới đều nằm
# trong chương trình, và đều nói "tam giác", "song song", "thể tích" tự nhiên.
#
# Bản cũ ĐÃ khai giới hạn này và chấp nhận nó, với lý do *"thất bại lộ ra ở C₁a
# chứ không âm thầm"*. Phép đo cho thấy lý do ấy sai hai chỗ: nó KHÔNG hiếm, và
# "lộ ra" với học sinh nghĩa là tấm thẻ **NGOÀI DANH MỤC MÔ PHỎNG** giáng xuống
# một đề mà hệ vốn mô phỏng được — route hình học ăn mất chính 24 target đang
# chạy tốt. Một cổng chẩn đoán được với dev vẫn là một lời từ chối sai với học
# sinh.
#
# ─── VÌ SAO PHỦ QUYẾT, KHÔNG PHẢI NÂNG NGƯỠNG ────────────────────────────────
#
# Nâng ngưỡng 3 → 5 giết `geo_08` (hình vuông PHẲNG: 0 cụm mạnh, chỉ đủ cụm
# yếu) — đổi một lỗ lấy một lỗ khác. Đòi ít nhất một cụm mạnh cũng giết `geo_08`
# vì nó không có cụm nào. Cái thiếu không phải "ít cụm hình học hơn" mà là **bộ
# dò chưa từng đọc từ vựng Tin học**: "viết chương trình" là bằng chứng dứt
# khoát mà nó đang ném đi.
#
# CHỈ đường yếu: cụm MẠNH (`thiết diện`, `hình chóp`…) không xuất hiện trong đề
# Tin học, nên *"viết chương trình dựng thiết diện"* vẫn phải là hình học.
#
# Không đề nào trong 10 bài dev hình học chứa một cụm nào dưới đây (đã kiểm).
_DAU_HIEU_TIN_HOC = (
    "viết chương trình", "thuật toán", "ngăn xếp", "hàng đợi", "mảng",
    "duyệt", "sắp xếp", "đồ thị", "bfs", "dfs", "đệ quy", "vòng lặp",
    "cấu trúc dữ liệu", "độ phức tạp", "truy vấn", "cơ sở dữ liệu",
    "gói tin", "giao thức", "nhị phân", "mã hoá", "in ra", "nhập vào",
    "câu lệnh", "mã nguồn", "con trỏ", "python", "pascal", "c++",
)


#: Tiền tố mô tả mà một số bản khai gắn trước ký hiệu điểm.
_TIEN_TO_KY_HIEU = ("point_", "diem_", "p_", "pt_")

#: Ký hiệu điểm dài nhất được chấp nhận — `A`, `M`, `A1`, `M12`.
#:
#: Giới hạn này là thứ giữ cho phép đồng nhất KHÔNG lan ra: `volume` (6 ký tự)
#: không bao giờ thành một ký hiệu, nên `volume` ≢ `VOLUME`. Không có nó thì
#: quy tắc này biến thành so-không-phân-biệt-hoa-thường toàn cục, đúng thứ
#: `A != a` phải giữ.
_DAI_TOI_DA_KY_HIEU = 3


#: Bốn cách viết CÙNG một điểm bậc một, đo được ở lượt sinh thật:
#: `A'` (SGK cả ba bộ) · `A1` (mô hình hay hạ dấu phẩy thành chỉ số) ·
#: `A_prime` · `Aprime`. Chuẩn hoá về dạng CHỈ SỐ.
#:
#: ─── LỖ ĐO ĐƯỢC Ở PHASE 7B (2026-08-29) ─────────────────────────────────────
#:
#: `geometry_symbol_key("A'")` trả `None`: hàm bỏ `_`/`-` rồi đòi phần còn lại
#: `isalnum()`, mà `'` rớt cả hai vế. Nên **dấu phẩy — cách viết phổ biến nhất
#: của hình học không gian THPT — không được nhận là ký hiệu**, và
#: `khop_ky_hieu` không bao giờ nối được `A'` của hợp đồng với biến nào của
#: chương trình. Nghĩa vụ mang witness `A'` vì thế không có đường nào thoả, kể
#: cả khi chương trình dựng đúng điểm ấy dưới tên `A1`.
#:
#: Gộp `A'` ≡ `A1` an toàn vì `khop_ky_hieu` fail-closed sẵn: trùng khoá ⇒
#: `None`. Chương trình khai cả hai như hai điểm khác nhau thì cổng từ chối,
#: không đoán.
_PHAY = ("′", "'", "’", "`")
_HAU_TO_PHAY = ("_prime", "prime")


#: Tên GHÉP sau chuẩn hoá: một dãy `chữ cái + chỉ số`, nhiều nhất BA đoạn.
#:
#: Đây là thứ thay cho giới hạn "≤ 3 ký tự" cũ, và nó chặt hơn chứ không lỏng
#: hơn ở chỗ quan trọng: `volume` tách thành sáu đoạn một-chữ-cái ⇒ TRƯỢT,
#: `distance` tám đoạn ⇒ TRƯỢT, `abcd` bốn đoạn ⇒ TRƯỢT (giữ nguyên hành vi
#: cũ). Cái nó MỞ là tên ghép có chỉ số: `B1C1` bốn KÝ TỰ nhưng chỉ HAI đoạn —
#: giới hạn "≤ 3 ký tự" chặn nhầm nó, mà đó lại là cách gọi mọi đường thẳng
#: trong một đề hình lập phương.
_MAU_KY_HIEU_GHEP = re.compile(r"^(?:[A-Za-z]\d*){1,3}$")


def _chuan_hoa_phay(s: str) -> str:
    """Chuẩn hoá dấu phẩy **tại chỗ**, cho cả tên GHÉP.

    `A'`→`A1` · `A''`→`A2` · `B'C'`→`B1C1` · `B_prime_C_prime`→`B1C1`.

    ─── VÌ SAO PHẢI LÀ TẠI CHỖ, ĐO ĐƯỢC 2026-08-29 (canary V2) ────────────

    Bản trước chỉ gỡ phẩy ở **đuôi**, nên nó xử lý được ký hiệu ĐƠN (`A'`)
    mà bó tay với tên GHÉP. Hậu quả đo được: hợp đồng khai `B'C'`, chương
    trình khai `B_prime_C_prime`, cả hai cho khoá `None` ⇒ C₁a không nối
    được ⇒ C₂ không có bí danh để tra ⇒ `check_angle` báo *"cặp đối tượng
    không hợp lệ cho góc"* trong khi giá trị `goc_ac_b_c = 1/2` ĐÚNG.

    Học sinh sẽ đọc ra *"chương trình tự mâu thuẫn với nghĩa vụ nó tự khai"*
    — một lời vu oan, đúng loại mà `postconditions` đã ghi là phải tránh.

    Tên ghép là thường lệ chứ không phải ngoại lệ: mọi đường thẳng và mặt
    phẳng trong đề hình lập phương đều được gọi bằng hai hay ba đỉnh.
    """
    for h in _HAU_TO_PHAY:                    # `_prime` / `prime` → `1`
        s = re.sub(rf"{h}(?![A-Za-z])", "1", s, flags=re.I)
    # Mỗi CỤM dấu phẩy thành số bậc: `A'`→`A1`, `A''`→`A2`.
    return re.sub(f"[{re.escape(''.join(_PHAY))}]+",
                  lambda m: str(len(m.group(0))), s)


def geometry_symbol_key(ten: str) -> str | None:
    """KHOÁ ĐỒNG NHẤT của một ký hiệu hình học, hoặc `None` nếu không phải.

    ─── VÌ SAO TỒN TẠI, ĐO ĐƯỢC Ở PHASE 5.5 (`geo_01`) ─────────────────────

    Hợp đồng khai `witness = 'm'`, chương trình khai `M`. Cả hai lượt LLM đều
    tuân thủ đúng luật được giao — luật thì mâu thuẫn. Nguồn đã vá ở
    `analyze_contract.MO_TA_WITNESS_HINH_HOC`; hàm này là **lưới an toàn**, cho
    lần model vẫn hạ chữ thường.

    ─── VÌ SAO KHÔNG PHẢI `lower()` ────────────────────────────────────────

    `lower()` là phép của MỌI chuỗi. Đây là phép của **ký hiệu hình học**, và ba
    ràng buộc dưới đây giữ cho nó không lan ra thành so-không-phân-biệt-hoa-
    thường toàn cục:

      · sau khi bỏ tiền tố và gạch nối, phần còn lại phải **≤ 3 ký tự** và
        alnum ASCII — `A`, `M`, `A1`, `abcd`(4) ✗, `volume`(6) ✗;
      · chỉ được gọi khi nghĩa vụ thuộc miền hình học (C₁a tự khoá);
      · trùng khoá ⇒ **KHÔNG khớp** (xem `khop_ky_hieu`), vì mơ hồ thì thà
        từ chối còn hơn đoán.

    Nên `A ≢ a` ở miền thông thường vẫn đúng: một biến Tin học tên `a` không đi
    qua hàm này bao giờ.
    """
    s = str(ten).strip()
    thap = s.lower()
    for t in _TIEN_TO_KY_HIEU:
        if thap.startswith(t) and len(s) > len(t):
            s = s[len(t):]
            break
    s = _chuan_hoa_phay(s)
    s = s.replace("_", "").replace("-", "")
    if not s or not s.isascii():
        return None
    # MẪU thay cho giới hạn độ dài. Xem `_MAU_KY_HIEU_GHEP`: chặt hơn chứ
    # không lỏng hơn — `volume`/`distance` vẫn trượt, còn `ABCD` và `B1C1`
    # thì đúng là ký hiệu hình học và giới hạn cũ chặn nhầm chúng.
    if not _MAU_KY_HIEU_GHEP.match(s):
        return None
    return s.upper()


#: Phụ tố KIỂU mà lượt sinh hay gắn vào tên đối tượng — ĐÓNG, không mở rộng
#: bằng suy đoán. Mỗi mục ở đây phải đến từ một lượt live đã quan sát được.
#:
#: Quan sát 2026-08-25 (ba smoke qua đường sản phẩm):
#:     hợp đồng `SA`      → chương trình `SA_line`
#:     hợp đồng `AD`      → chương trình `line_AD`
#:     hợp đồng `(ABCD)`  → chương trình `plane_ABCD` / `ABCD_plane`
#:     hợp đồng `S.ABCD`  → chương trình `S_ABCD_solid`
_PHU_TO_KIEU = (
    "line", "duong", "plane", "mp", "mat", "solid", "khoi",
    "point", "diem", "segment", "doan", "section", "thiet_dien", "vector",
)


def ten_loi(ten: str) -> str | None:
    """LÕI của một tên đối tượng hình học, hoặc `None` nếu không rút được.

    Bỏ dấu ngoặc (hợp đồng viết `(ABCD)`), bỏ **một** phụ tố kiểu ở đầu hoặc
    cuối, rồi bỏ mọi dấu nối. `SA_line` · `line_AD` · `plane_ABCD` ·
    `S_ABCD_solid` đều rút về đúng thứ đề bài gọi.

    ⚠️ **KHÔNG viết hoa.** Đây là chỗ khác `geometry_symbol_key`, và khác vì một
    lý do cụ thể: một bài thiết diện có cả `d` (giao tuyến) lẫn `D` (đỉnh đáy).
    Viết hoa lõi là gộp hai đối tượng KHÁC NHAU vào một khoá, và khi ấy phép
    hoà giải sẽ nối `point_on_line(d)` vào đỉnh `D`. Hoà giải sai còn tệ hơn
    không hoà giải: nó dựng một kết quả không tra lại được.

    Trả `None` khi rút xong rỗng — không có lõi thì không có gì để so.
    """
    s = str(ten).strip().strip("()[]{}")
    thap = s.lower()
    for t in _PHU_TO_KIEU:
        if thap.startswith(t + "_") and len(s) > len(t) + 1:
            s = s[len(t) + 1:]
            break
        if thap.endswith("_" + t) and len(s) > len(t) + 1:
            s = s[: -(len(t) + 1)]
            break
    s = s.replace("_", "").replace("-", "").replace(".", "")
    return s or None


def khop_ten_doi_tuong(ten_hop_dong: str, ung_vien: set[str]) -> str | None:
    """Tên trong hợp đồng ↔ tên trong chương trình, theo LÕI TÊN.

    Hai lượt LLM đặt tên cho cùng một vật, và lượt viết chương trình hay gắn
    thêm phụ tố kiểu. Đó là lệch DANH XƯNG, không phải thiếu phép dựng — hai
    bệnh cần hai cách chữa, và trước bản này chúng bị gộp làm một.

    **Trùng lõi ⇒ trả `None`.** Chương trình khai cả `AD` lẫn `line_AD` thì
    không ai biết hợp đồng đang nói cái nào; đoán ở đó là dựng một kết quả
    không tra lại được. Cùng luật fail-closed với `khop_ky_hieu`.
    """
    loi = ten_loi(ten_hop_dong)
    if loi is None:
        return None
    trung = [t for t in ung_vien if ten_loi(t) == loi]
    return trung[0] if len(trung) == 1 else None


def tach_ky_hieu_diem(ten: str, diem_da_khai: set[str]) -> tuple[str, ...] | None:
    """Tên hợp đồng → DÃY KÝ HIỆU ĐIỂM, hoặc `None` nếu không đọc được như vậy.

    `AD` → `(A, D)` · `(ABCD)` → `(A, B, C, D)` · `S.ABCD` → `(S, A, B, C, D)`

    ─── ĐIỀU KIỆN CHẶT NHẤT NẰM Ở THAM SỐ THỨ HAI ─────────────────────────

    Mọi ký hiệu tách ra **phải là một điểm ĐÃ KHAI trong chương trình**. Không có
    điều kiện ấy thì `MAX` sẽ đọc thành `(M, A, X)` và hàm này biến thành một
    máy đoán. Có nó thì `MAX` chỉ đọc được như ba điểm khi chương trình thật sự
    khai ba điểm tên `M`, `A`, `X` — và khi ấy đọc như thế là ĐÚNG.

    Đòi ít nhất HAI ký hiệu: một điểm lẻ không phải một vật *dựng từ* các điểm.
    """
    goc = str(ten).strip().strip("()[]{}")
    for d in ("_", "-", "."):
        goc = goc.replace(d, "")
    if not goc:
        return None

    ra: list[str] = []
    i = 0
    while i < len(goc):
        c = goc[i]
        if not (c.isascii() and c.isalpha()):
            return None
        j = i + 1
        while j < len(goc) and goc[j].isdigit():
            j += 1
        ra.append(goc[i:j])
        i = j
    if len(ra) < 2 or any(t not in diem_da_khai for t in ra):
        return None
    return tuple(ra)


#: Bao nhiêu ĐIỂM xác định một vật, theo kiểu. Quyết định phép so là BẰNG hay
#: là TẬP CON — và đó là chỗ duy nhất trong resolver mang tri thức hình học.
#:
#: · một đường thẳng qua `A`, `D` được xác định bởi ĐÚNG hai điểm ấy ⇒ BẰNG
#: · một mặt phẳng gọi là `(ABCD)` được dựng từ BA trong bốn điểm ấy ⇒ TẬP CON
#: · một đa giác/khối `ABCD` có ĐÚNG bốn đỉnh ⇒ BẰNG
_SO_BANG_TAP_CON = frozenset({"plane3"})


def khop_theo_topo(
    ten_hop_dong: str,
    diem_da_khai: set[str],
    dinh_nghia: dict[str, tuple[str, frozenset[str]]],
    chap_nhan_kieu,
) -> str | None:
    """Tên hợp đồng ↔ tên chương trình, theo **TOPOLOGY** chứ không theo chính tả.

    ─── VÌ SAO KHÔNG DÙNG DANH SÁCH BÍ DANH ───────────────────────────────

    Đo được ở bốn lượt smoke 2026-08-26: cùng một vật, mỗi lượt một cái tên —
    `SA_line`, `line_AD`, `DA`, `AD_segment`. Một danh sách phụ tố phải dài thêm
    sau mỗi lượt đỏ, tức nó không bao giờ đóng, và mỗi lần dài thêm là một lần
    nới cổng theo một lỗi cụ thể.

    Hàm này hỏi câu khác hẳn, và câu ấy có câu trả lời hữu hạn:

        "Trong chương trình, vật nào ĐƯỢC DỰNG TỪ đúng những điểm này,
         và có kiểu mà nghĩa vụ này chấp nhận?"

    Tên gọi thành **không liên quan**. `DA` và `line_AD` cùng khớp vì cả hai
    được dựng từ `{A, D}` — không phải vì chuỗi của chúng giống nhau.

    ─── FAIL-CLOSED ───────────────────────────────────────────────────────

    Không đúng một ứng viên ⇒ `None`. Hai đường cùng qua `A` và `D` thì không ai
    biết hợp đồng nói cái nào, và đoán ở đó là dựng một kết quả không tra lại
    được.

    `dinh_nghia`: `tên → (kiểu, tập tên điểm dựng ra nó)`. Vật khai bằng
    `initial_value` không có tập ấy ⇒ không tham gia, và đó là đúng: không có
    topology thì không có gì để so.
    """
    ky_hieu = tach_ky_hieu_diem(ten_hop_dong, diem_da_khai)
    if ky_hieu is None:
        return None
    can = frozenset(ky_hieu)

    trung: list[str] = []
    for ten, (kieu, nguon) in dinh_nghia.items():
        if not nguon or not chap_nhan_kieu(kieu):
            continue
        khop = (nguon <= can and len(nguon) >= 3) if kieu in _SO_BANG_TAP_CON             else (nguon == can)
        if khop:
            trung.append(ten)
    return trung[0] if len(trung) == 1 else None


def khop_ky_hieu(ten_hop_dong: str, ung_vien: set[str]) -> str | None:
    """Tên trong hợp đồng ↔ tên trong chương trình, theo ký hiệu hình học.

    Trả tên của chương trình nếu đồng nhất được, `None` nếu không.

    **Trùng khoá ⇒ trả `None`.** Chương trình khai cả `a` lẫn `A` thì không ai
    biết hợp đồng đang nói cái nào; đoán ở đó là dựng một kết quả không tra lại
    được. Mơ hồ thì từ chối — cùng luật fail-closed của mọi cổng khác.
    """
    khoa = geometry_symbol_key(ten_hop_dong)
    if khoa is None:
        return None
    trung = [t for t in ung_vien if geometry_symbol_key(t) == khoa]
    return trung[0] if len(trung) == 1 else None


def detect_domain(text: str) -> str:
    """Đoán miền của một đề. Không chắc ⇒ `tin_hoc` (= hành vi hiện tại).

    KHÔNG dùng ở đường đo. Nó nhận diện **từ ngữ**, không nhận diện **bài
    toán** — giới hạn ấy vẫn còn, và vẫn phải đọc kèm.

    Ba luật, xếp theo sức mạnh của bằng chứng:

    1. có cụm MẠNH  ⇒ `hinh_hoc`. Dứt khoát: `thiết diện`, `hình chóp`, `tứ
       diện` không xuất hiện trong đề Tin học.
    2. đủ 3 cụm YẾU **và không có dấu hiệu Tin học** ⇒ `hinh_hoc`.
    3. còn lại ⇒ `tin_hoc` (fail-safe).

    Luật 2 mang mệnh đề phủ quyết vì bản không có nó kéo nhầm 4/5 đề Tin học
    hợp lệ có mượn từ vựng hình học — xem `_DAU_HIEU_TIN_HOC` để biết phép đo
    và vì sao phủ quyết chứ không nâng ngưỡng.

    Bản cũ ghi ở đây rằng kéo nhầm là *"thất bại lộ ra ở C₁a chứ không âm
    thầm"* nên chấp nhận được. Câu đó đã BỎ: với học sinh, "lộ ra" là tấm thẻ
    **NGOÀI DANH MỤC MÔ PHỎNG** trên một đề hệ vốn mô phỏng được.
    """
    if not text:
        return DOMAIN_TIN_HOC
    t = text.lower()
    # BỐN MỨC, không còn ba (sửa 2026-08-29 — xem `_MANH_QUAN_HE`).
    #
    # Cụm QUAN HỆ thắng cả phủ quyết Tin học; danh từ KHỐI thì không. Bản cũ
    # gộp hai lớp làm một nên ba đề Tin học hợp lệ đi thẳng sang hình học chỉ
    # vì có một danh từ khối.
    if any(d in t for d in _MANH_QUAN_HE):
        return DOMAIN_HINH_HOC
    if any(d in t for d in _DAU_HIEU_TIN_HOC):
        return DOMAIN_TIN_HOC
    if any(d in t for d in _MANH_DANH_TU_KHOI):
        return DOMAIN_HINH_HOC
    if sum(1 for d in _DAU_HIEU_YEU if d in t) >= 3:
        return DOMAIN_HINH_HOC
    return DOMAIN_TIN_HOC
