"""M14 §O — Curriculum coverage matrix (enum ĐÓNG, machine-readable).

Ánh xạ mỗi ĐƠN VỊ KIẾN THỨC trong phạm vi đề tài đã tuyên bố (curate từ
`docs/COVERAGE.md` §3 Tier 1/2/3 + §7 + §7b) → đúng MỘT trạng thái enum đóng.

Nguyên tắc (§O):
- M14 KHÔNG claim phủ toàn chương trình Tin học THPT.
- Gap / out-of-scope khai TRUNG THỰC — không "phủ giả".
- KHÔNG thêm capability/executor mới chỉ để làm đẹp coverage (O5).
- Nguồn = SGK KNTT title-level (COVERAGE §1), không phải toàn văn GDPT 2018.

Đây là artifact machine-readable; `coverage_rows()` sinh bảng docs. Test
`test_coverage_matrix.py` khóa: enum đóng, mọi unit đúng một status, không trùng.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CoverageStatus(str, Enum):
    """Trạng thái phủ của một đơn vị kiến thức (§O3) — enum ĐÓNG, không tự do."""

    SUPPORTED = "SUPPORTED"          # có engine tất định sở hữu, đã ship, public
    PARTIAL = "PARTIAL"              # có phần, còn giới hạn khai
    PILOT = "PILOT"                  # đang là pilot M14
    CAPABILITY_GAP = "CAPABILITY_GAP"  # trong phạm vi nhưng CỐ Ý từ chối
    OUT_OF_SCOPE = "OUT_OF_SCOPE"    # ngoài phạm vi đề tài đã khoanh


class SupportKind(str, Enum):
    """W4B-3A — *KIỂU* hỗ trợ, trục THỨ HAI bên cạnh `CoverageStatus`.

    Hai trục trả lời hai câu hỏi khác nhau, và gộp chúng lại là chỗ bảng phủ hay
    nói quá nhất:

      - `CoverageStatus` : đơn vị kiến thức này CÓ được phủ không (và phủ tới đâu);
      - `SupportKind`    : nếu có thì học sinh thật sự LÀM ĐƯỢC GÌ.

    "Có mô phỏng" mà học sinh chỉ bấm Tiến để xem thì khác hẳn "có mô phỏng" mà
    học sinh đổi được mô hình rồi thấy hệ quả tất định. Một bảng chỉ có
    `SUPPORTED/PARTIAL` không phân biệt nổi hai ca đó — và "có mô phỏng" là câu
    dễ đọc thành lời hứa lớn hơn thứ sản phẩm đang làm được.

    Nguồn phân loại: `docs/evaluation/m17/w4b3a-after/after-matrix.md` (sinh từ
    registry + module thật + đo trình duyệt), KHÔNG phải cảm nhận.
    """

    #: Học sinh ĐỔI ĐƯỢC mô hình và engine tất định tính lại hệ quả.
    SUPPORTED_INTERACTIVE = "SUPPORTED_INTERACTIVE"
    #: Có diễn tiến từng bước tất định (có thể kèm cam kết được chấm), nhưng
    #: KHÔNG có thao tác tự do lên mô hình.
    SUPPORTED_TRACE = "SUPPORTED_TRACE"
    #: Học sinh sửa thuộc tính TRONG MIỀN ĐÓNG của một sản phẩm (vd style web).
    SUPPORTED_BOUNDED_ARTIFACT = "SUPPORTED_BOUNDED_ARTIFACT"
    #: Chỉ trình bày/giải thích — không có cơ chế ẩn nào để thao tác.
    SUPPORTED_EXPLANATION = "SUPPORTED_EXPLANATION"
    #: Có phần, còn giới hạn khai tường minh.
    PARTIAL = "PARTIAL"
    #: Trong phạm vi đề tài nhưng CHƯA/CỐ Ý không hỗ trợ.
    UNSUPPORTED = "UNSUPPORTED"
    #: Không phải thứ nên mô phỏng — mô phỏng ở đây là trang trí (COVERAGE §7).
    NOT_SIMULATION_SUITABLE = "NOT_SIMULATION_SUITABLE"


@dataclass(frozen=True)
class KnowledgeUnit:
    unit_id: str
    label: str
    curriculum_anchor: str
    status: CoverageStatus
    note: str = ""
    #: W4B-3A — mặc định là ca AN TOÀN NHẤT (chưa hỗ trợ); test bắt khai tường minh.
    support_kind: SupportKind = SupportKind.UNSUPPORTED
    #: Bằng chứng cho `support_kind` — target nào, ĐO ĐƯỢC hay chỉ KHAI BÁO.
    support_evidence: str = ""


# Curate từ COVERAGE.md §3 (Tier 1/2/3) + §7 (trang trí, cố ý không mô phỏng) +
# §7b (Dijkstra). Mỗi unit đúng MỘT status. KHÔNG yêu cầu tất cả SUPPORTED (O4).
KNOWLEDGE_UNITS: tuple[KnowledgeUnit, ...] = (
    # ── Tier 1 (COVERAGE §3) ──────────────────────────────────
    KnowledgeUnit("sorting", "Sắp xếp so sánh", "T11CS B21–22",
                  CoverageStatus.SUPPORTED,
                  "M14 pilot + M15 formalize (comparison_sort selector); M17 W1 thêm "
                  "biến thể selection (bubble/insertion/selection — quick vẫn gap); "
                  "targeted acceptance, KHÔNG phải bằng chứng thống kê",
                  support_kind=SupportKind.SUPPORTED_INTERACTIVE,
                  support_evidence="bubble/insertion/selection ĐO ĐƯỢC là INTERACTIVE_MODEL (kéo đổi chỗ → apply → engine chạy lại nhánh). W4B-3D: selection nay có mẫu offline nên đã đo trong trình duyệt, không còn chỉ khai báo"),
    KnowledgeUnit("binary_search", "Tìm kiếm nhị phân", "T11CS B19",
                  CoverageStatus.SUPPORTED, "algorithm.binary_search",
                  support_kind=SupportKind.SUPPORTED_INTERACTIVE,
                  support_evidence="INTERACTIVE_MODEL đo được: Khám phá cho phá tiền đề dãy đã sắp, Thử thách cho chọn nửa (4/13 bước)"),
    KnowledgeUnit("single_pass_scan", "Quét dãy một lượt (tìm/đếm/tổng/tìm-đầu-tiên)",
                  "T10 CĐ5 · T11CS B17", CoverageStatus.SUPPORTED,
                  "algorithm.find_max/min/sum_if/count_if/linear_search + algorithm.scan",
                  support_kind=SupportKind.SUPPORTED_INTERACTIVE,
                  support_evidence="find_max/find_min/linear_search INTERACTIVE_MODEL; sum_if/count_if chỉ COMMITMENT_TRACE — kéo ở hai bài đó là trang trí nên CỐ Ý không bày (COVERAGE §2.6)"),
    KnowledgeUnit("loops_branch_variable", "Lặp / rẽ nhánh / biến", "T10 B17–21",
                  CoverageStatus.PARTIAL,
                  "algorithm.bounded_control_flow (M17 W2C): engine tất định và "
                  "renderer đã kiểm chứng cho gán/if-else/while có biên trên NGỮ PHÁP "
                  "ĐÓNG. Tích hợp ngôn ngữ tự nhiên PARTIAL. KHÔNG chạy code Python "
                  "tự do; hàm/đệ quy ngoài phạm vi",
                  support_kind=SupportKind.PARTIAL,
                  support_evidence="bounded_control_flow ĐÃ có mẫu offline và đo được trong trình duyệt (W4B-3D). Vẫn PARTIAL vì tích hợp ngôn ngữ tự nhiên chưa đủ và không có predict/explore — TRACE thuần"),
    KnowledgeUnit("binary_system", "Hệ đếm & đổi cơ số (trọng số vị trí)", "T10 B4",
                  CoverageStatus.SUPPORTED,
                  "binary.decimal_to_binary (bit trọng số 8/4/2/1) + M17 W1 "
                  "binary.base_conversion (đổi cơ số 2/8/10/16 kể cả hex/octal — "
                  "cơ số ≠ 2 KHÔNG còn là gap)",
                  support_kind=SupportKind.SUPPORTED_INTERACTIVE,
                  support_evidence="decimal_to_binary INTERACTIVE_STAGE (bật/tắt bit, engine tính lại); base_conversion nay ĐÃ đo (W4B-3D) — TRACE từng bước chia lấy dư"),
    KnowledgeUnit("logic_data", "Dữ liệu lôgic / bảng chân trị", "T10 B5",
                  CoverageStatus.SUPPORTED,
                  "logic.and_gate (1 cổng) + M17 W1 logic.boolean_dag (mạch nhiều "
                  "cổng AND/OR/NOT/XOR + bảng chân trị) + generic boolean composition",
                  support_kind=SupportKind.SUPPORTED_INTERACTIVE,
                  support_evidence="and_gate INTERACTIVE_STAGE (gạt đầu vào → bảng chân trị tất định); boolean_dag nay ĐÃ đo (W4B-3D), mạch nhiều cổng + bảng chân trị đầy đủ"),
    KnowledgeUnit("packet_routing", "Định tuyến gói tin (BFS số chặng)", "T10 CĐ2 · T12 CĐ2",
                  CoverageStatus.SUPPORTED, "network.packet_routing",
                  support_kind=SupportKind.SUPPORTED_INTERACTIVE,
                  support_evidence="INTERACTIVE_MODEL đo được: ngắt/nối liên kết → BFS định tuyến lại; kèm predict chặng kế tiếp"),
    KnowledgeUnit("graph_traversal", "Duyệt đồ thị / tìm đường không trọng số (BFS/DFS)",
                  "T11CS B17 · T12 CĐ2", CoverageStatus.SUPPORTED,
                  "M17 W1 network.graph_traversal (BFS/DFS, có/không hướng, tìm đường "
                  "+ unreachable); đường đi ngắn nhất CÓ TRỌNG SỐ (Dijkstra) vẫn gap",
                  support_kind=SupportKind.SUPPORTED_TRACE,
                  support_evidence="BFS/DFS có timeline, nay ĐÃ đo trong trình duyệt (W4B-3D); không khai thao tác tự do nên là TRACE, không phải mô hình tương tác"),
    KnowledgeUnit("info_system_dataflow", "Hệ thống thông tin / luồng dữ liệu có hướng",
                  "T11 B10 · T12CS B29", CoverageStatus.SUPPORTED, "generic.rule_scene + edge.directed",
                  support_kind=SupportKind.SUPPORTED_INTERACTIVE,
                  support_evidence="generic.rule_scene INTERACTIVE_STAGE (hybrid — gạt công tắc, chuỗi rule tính lại)"),
    # ── Tier 2 (COVERAGE §3) ──────────────────────────────────
    KnowledgeUnit("network_layering", "Giao thức / phân tầng mạng (đóng-mở gói)",
                  "T12 B4 · 12CS B22–24", CoverageStatus.SUPPORTED,
                  "network.protocol_encapsulation (2D+3D); TCP/UDP branching cố ý ngoài v1",
                  support_kind=SupportKind.SUPPORTED_TRACE,
                  support_evidence="protocol_encapsulation TRACE_PLAYBACK: đóng/mở gói từng tầng, parity 2D↔3D đã đo trong trình duyệt; KHÔNG có thao tác tự do lên PDU"),
    KnowledgeUnit("access_control", "Kiểm soát truy cập (quy tắc logic)", "T10 B9 · T11 B15",
                  CoverageStatus.SUPPORTED, "tái dụng boolean",
                  support_kind=SupportKind.SUPPORTED_INTERACTIVE,
                  support_evidence="tái dụng bề mặt boolean (gạt điều kiện) — cùng đường tương tác với logic_data"),
    KnowledgeUnit("html_css", "HTML/CSS (quan hệ markup ↔ hiển thị)", "T12 CĐ4",
                  CoverageStatus.PARTIAL, "structural + reveal; thiếu practice tự dựng",
                  support_kind=SupportKind.SUPPORTED_BOUNDED_ARTIFACT,
                  support_evidence="web.style_model: sửa thuộc tính trong MIỀN ĐÓNG (hợp đồng FE≡BE có sync-lock); KHÔNG có đường viết CSS tự do"),
    KnowledgeUnit("text_media_encoding", "Mã hoá văn bản/âm thanh/ảnh", "T10 B3, B6",
                  CoverageStatus.PARTIAL,
                  "binary.character_encoding (M17 W3): ký tự → mã (ASCII / Unicode "
                  "code point trong BMP) → nhị phân, từng bước. Mã hoá ảnh/âm thanh "
                  "và dãy byte UTF-8 vẫn ngoài phạm vi",
                  support_kind=SupportKind.PARTIAL,
                  support_evidence="character_encoding nay ĐÃ có mẫu và đo được (W4B-3D); vẫn PARTIAL vì ảnh/âm thanh và dãy byte UTF-8 ngoài phạm vi"),
    KnowledgeUnit("arrays_1d_2d", "Mảng 1D/2D (chỉ số ↔ giá trị)", "T11CS B17",
                  CoverageStatus.PARTIAL, "1D ngầm trong trace; 2D chưa có",
                  support_kind=SupportKind.PARTIAL,
                  support_evidence="1D ngầm trong trace của mọi bài dãy; 2D chưa có target nào"),
    # W2B đã ship `database.relational_table_query` — mục này từng ghi "chưa có
    # table/grid" và trở nên LỖI THỜI (khai dè dặt hơn năng lực thật).
    KnowledgeUnit("database_table_query", "CSDL: bảng, bản ghi, truy vấn", "T11 CĐ4",
                  CoverageStatus.PARTIAL,
                  "database.relational_table_query (M17 W2B): truy vấn bảng đơn giản "
                  "VERIFIED (live lọc+chọn cột, sắp xếp ổn định); pipeline nhiều tầng "
                  "bằng ngôn ngữ tự nhiên PARTIAL/EXPERIMENTAL. Wave 2B NOT CLOSED",
                  support_kind=SupportKind.PARTIAL,
                  support_evidence="relational_table_query nay ĐÃ có mẫu và đo được (W4B-3D); vẫn PARTIAL vì pipeline nhiều tầng bằng ngôn ngữ tự nhiên chưa đạt"),
    KnowledgeUnit("os_process_fsm", "Hệ điều hành: tiến trình (máy trạng thái)", "T11 B1–2",
                  CoverageStatus.CAPABILITY_GAP, "chưa có FSM",
                  support_kind=SupportKind.UNSUPPORTED,
                  support_evidence="chưa có engine FSM nào sở hữu cơ chế này"),
    KnowledgeUnit("practice_activity", "Học sinh tự dựng/thao tác, engine kiểm được", "cross",
                  CoverageStatus.PARTIAL, "substrate (PredictionCapability), chưa phải một mode đầy đủ",
                  support_kind=SupportKind.PARTIAL,
                  support_evidence="substrate đã có (predict.check + explore/apply) nhưng chưa phải một mode học tập đầy đủ"),
    # ── §7b Dijkstra ──────────────────────────────────────────
    KnowledgeUnit("dijkstra_weighted_shortest_path", "Đường đi ngắn nhất CÓ TRỌNG SỐ (Dijkstra)",
                  "không có anchor SGK", CoverageStatus.CAPABILITY_GAP,
                  "COVERAGE §7b — ngoài phạm vi công khai; capability_gap là câu trả lời đúng dài hạn",
                  support_kind=SupportKind.UNSUPPORTED,
                  support_evidence="COVERAGE §7b — capability_gap là câu trả lời đúng, không phải thiếu sót cần vá"),
    # ── §7 trang trí / cố ý không mô phỏng → OUT_OF_SCOPE ──────
    KnowledgeUnit("digital_ethics_law_culture", "Đạo đức/pháp luật/văn hoá số, bản quyền",
                  "CĐ3 (mọi khối)", CoverageStatus.OUT_OF_SCOPE, "không cơ chế ẩn động — static tốt hơn",
                  support_kind=SupportKind.NOT_SIMULATION_SUITABLE,
                  support_evidence="không có cơ chế ẩn động để thao tác"),
    KnowledgeUnit("career_orientation", "Hướng nghiệp", "mọi khối",
                  CoverageStatus.OUT_OF_SCOPE, "không mô phỏng",
                  support_kind=SupportKind.NOT_SIMULATION_SUITABLE,
                  support_evidence="không có cơ chế ẩn động"),
    KnowledgeUnit("software_skills", "Kĩ năng phần mềm (đồ hoạ/ảnh/video)", "T10 CĐ4 · T11-ICT CĐ7",
                  CoverageStatus.OUT_OF_SCOPE, "chính phần mềm đó mới là 'mô phỏng'",
                  support_kind=SupportKind.NOT_SIMULATION_SUITABLE,
                  support_evidence="chính phần mềm đó mới là 'mô phỏng'"),
    KnowledgeUnit("info_concepts_devices", "Thông tin & xử lí thông tin; thiết bị số", "T10 B1–2, B7",
                  CoverageStatus.OUT_OF_SCOPE, "khái niệm",
                  support_kind=SupportKind.NOT_SIMULATION_SUITABLE,
                  support_evidence="khái niệm — hình tĩnh có chú thích tốt hơn"),
    KnowledgeUnit("hardware_network_lookup", "Bên trong máy tính / thiết bị mạng", "T11 B4 · T12 B3",
                  CoverageStatus.OUT_OF_SCOPE, "sự kiện tra cứu — ảnh chú thích tốt hơn",
                  support_kind=SupportKind.NOT_SIMULATION_SUITABLE,
                  support_evidence="sự kiện tra cứu"),
    KnowledgeUnit("cloud_email_social", "Lưu trữ đám mây, email, mạng xã hội", "T11 B6–8",
                  CoverageStatus.OUT_OF_SCOPE, "thao tác công cụ",
                  support_kind=SupportKind.NOT_SIMULATION_SUITABLE,
                  support_evidence="thao tác công cụ, không phải cơ chế"),
    KnowledgeUnit("ai_ml_datascience_overview", "Tổng quan AI / Học máy / KHDL", "T12 CĐ1 · 12CS CĐ7",
                  CoverageStatus.OUT_OF_SCOPE, "'mạng nơ-ron 3D xoay' là mô phỏng trang trí kinh điển",
                  support_kind=SupportKind.NOT_SIMULATION_SUITABLE,
                  support_evidence="'mạng nơ-ron 3D xoay' là mô phỏng trang trí kinh điển"),
)


def coverage_rows() -> list[dict]:
    """Bảng machine-readable (dùng cho docs-generate + test)."""
    return [
        {
            "unit_id": u.unit_id,
            "label": u.label,
            "curriculum_anchor": u.curriculum_anchor,
            "status": u.status.value,
            "note": u.note,
            "support_kind": u.support_kind.value,
            "support_evidence": u.support_evidence,
        }
        for u in KNOWLEDGE_UNITS
    ]


def curriculum_support_rows() -> list[dict]:
    """W4B-3A — bảng HƯỚNG CHƯƠNG TRÌNH: mỗi đơn vị kiến thức + KIỂU hỗ trợ.

    Tách khỏi `coverage_rows()` vì nó trả lời câu hỏi của giáo viên ("học sinh
    làm được gì với mục này"), không phải câu hỏi của kĩ sư ("mục này đã ship
    chưa"). Hai bảng, hai người đọc, cùng một nguồn.
    """
    order = {k: i for i, k in enumerate(SupportKind)}
    return sorted(
        (
            {
                "unit_id": u.unit_id,
                "label": u.label,
                "curriculum_anchor": u.curriculum_anchor,
                "coverage_status": u.status.value,
                "support_kind": u.support_kind.value,
                "support_evidence": u.support_evidence,
            }
            for u in KNOWLEDGE_UNITS
        ),
        key=lambda r: (order[SupportKind(r["support_kind"])], r["unit_id"]),
    )
