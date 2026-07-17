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


@dataclass(frozen=True)
class KnowledgeUnit:
    unit_id: str
    label: str
    curriculum_anchor: str
    status: CoverageStatus
    note: str = ""


# Curate từ COVERAGE.md §3 (Tier 1/2/3) + §7 (trang trí, cố ý không mô phỏng) +
# §7b (Dijkstra). Mỗi unit đúng MỘT status. KHÔNG yêu cầu tất cả SUPPORTED (O4).
KNOWLEDGE_UNITS: tuple[KnowledgeUnit, ...] = (
    # ── Tier 1 (COVERAGE §3) ──────────────────────────────────
    KnowledgeUnit("sorting", "Sắp xếp so sánh", "T11CS B21–22",
                  CoverageStatus.PILOT, "pilot M14 — comparison_sort family selector"),
    KnowledgeUnit("binary_search", "Tìm kiếm nhị phân", "T11CS B19",
                  CoverageStatus.SUPPORTED, "algorithm.binary_search"),
    KnowledgeUnit("single_pass_scan", "Quét dãy một lượt (tìm/đếm/tổng/tìm-đầu-tiên)",
                  "T10 CĐ5 · T11CS B17", CoverageStatus.SUPPORTED,
                  "algorithm.find_max/min/sum_if/count_if/linear_search + algorithm.scan"),
    KnowledgeUnit("loops_branch_variable", "Lặp / rẽ nhánh / biến", "T10 B17–21",
                  CoverageStatus.PARTIAL, "chỉ trong các thuật toán cố định, không phải code tự do"),
    KnowledgeUnit("binary_system", "Hệ nhị phân (trọng số vị trí)", "T10 B4",
                  CoverageStatus.SUPPORTED, "binary.decimal_to_binary"),
    KnowledgeUnit("logic_data", "Dữ liệu lôgic / bảng chân trị", "T10 B5",
                  CoverageStatus.SUPPORTED, "logic.and_gate + generic boolean composition"),
    KnowledgeUnit("packet_routing", "Định tuyến gói tin (BFS số chặng)", "T10 CĐ2 · T12 CĐ2",
                  CoverageStatus.SUPPORTED, "network.packet_routing"),
    KnowledgeUnit("info_system_dataflow", "Hệ thống thông tin / luồng dữ liệu có hướng",
                  "T11 B10 · T12CS B29", CoverageStatus.SUPPORTED, "generic.rule_scene + edge.directed"),
    # ── Tier 2 (COVERAGE §3) ──────────────────────────────────
    KnowledgeUnit("network_layering", "Giao thức / phân tầng mạng (đóng-mở gói)",
                  "T12 B4 · 12CS B22–24", CoverageStatus.SUPPORTED,
                  "network.protocol_encapsulation (2D+3D); TCP/UDP branching cố ý ngoài v1"),
    KnowledgeUnit("access_control", "Kiểm soát truy cập (quy tắc logic)", "T10 B9 · T11 B15",
                  CoverageStatus.SUPPORTED, "tái dụng boolean"),
    KnowledgeUnit("html_css", "HTML/CSS (quan hệ markup ↔ hiển thị)", "T12 CĐ4",
                  CoverageStatus.PARTIAL, "structural + reveal; thiếu practice tự dựng"),
    KnowledgeUnit("text_media_encoding", "Mã hoá văn bản/âm thanh/ảnh", "T10 B3, B6",
                  CoverageStatus.PARTIAL, "một phần; cần table/grid"),
    KnowledgeUnit("arrays_1d_2d", "Mảng 1D/2D (chỉ số ↔ giá trị)", "T11CS B17",
                  CoverageStatus.PARTIAL, "1D ngầm trong trace; 2D chưa có"),
    KnowledgeUnit("database_table_query", "CSDL: bảng, bản ghi, truy vấn", "T11 CĐ4",
                  CoverageStatus.CAPABILITY_GAP, "chưa có table/grid — gap trung thực, ứng viên post-M8"),
    KnowledgeUnit("os_process_fsm", "Hệ điều hành: tiến trình (máy trạng thái)", "T11 B1–2",
                  CoverageStatus.CAPABILITY_GAP, "chưa có FSM"),
    KnowledgeUnit("practice_activity", "Học sinh tự dựng/thao tác, engine kiểm được", "cross",
                  CoverageStatus.PARTIAL, "substrate (PredictionCapability), chưa phải một mode đầy đủ"),
    # ── §7b Dijkstra ──────────────────────────────────────────
    KnowledgeUnit("dijkstra_weighted_shortest_path", "Đường đi ngắn nhất CÓ TRỌNG SỐ (Dijkstra)",
                  "không có anchor SGK", CoverageStatus.CAPABILITY_GAP,
                  "COVERAGE §7b — ngoài phạm vi công khai; capability_gap là câu trả lời đúng dài hạn"),
    # ── §7 trang trí / cố ý không mô phỏng → OUT_OF_SCOPE ──────
    KnowledgeUnit("digital_ethics_law_culture", "Đạo đức/pháp luật/văn hoá số, bản quyền",
                  "CĐ3 (mọi khối)", CoverageStatus.OUT_OF_SCOPE, "không cơ chế ẩn động — static tốt hơn"),
    KnowledgeUnit("career_orientation", "Hướng nghiệp", "mọi khối",
                  CoverageStatus.OUT_OF_SCOPE, "không mô phỏng"),
    KnowledgeUnit("software_skills", "Kĩ năng phần mềm (đồ hoạ/ảnh/video)", "T10 CĐ4 · T11-ICT CĐ7",
                  CoverageStatus.OUT_OF_SCOPE, "chính phần mềm đó mới là 'mô phỏng'"),
    KnowledgeUnit("info_concepts_devices", "Thông tin & xử lí thông tin; thiết bị số", "T10 B1–2, B7",
                  CoverageStatus.OUT_OF_SCOPE, "khái niệm"),
    KnowledgeUnit("hardware_network_lookup", "Bên trong máy tính / thiết bị mạng", "T11 B4 · T12 B3",
                  CoverageStatus.OUT_OF_SCOPE, "sự kiện tra cứu — ảnh chú thích tốt hơn"),
    KnowledgeUnit("cloud_email_social", "Lưu trữ đám mây, email, mạng xã hội", "T11 B6–8",
                  CoverageStatus.OUT_OF_SCOPE, "thao tác công cụ"),
    KnowledgeUnit("ai_ml_datascience_overview", "Tổng quan AI / Học máy / KHDL", "T12 CĐ1 · 12CS CĐ7",
                  CoverageStatus.OUT_OF_SCOPE, "'mạng nơ-ron 3D xoay' là mô phỏng trang trí kinh điển"),
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
        }
        for u in KNOWLEDGE_UNITS
    ]
