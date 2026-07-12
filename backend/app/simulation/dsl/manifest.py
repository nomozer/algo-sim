"""DSL Capability Manifest (M7 §2) — NGUỒN CHÂN LÝ DUY NHẤT cho DSL v1.

Mọi nơi khác (validator dsl.py, contract prompt trong catalog) đều DẪN XUẤT
từ manifest này — không viết tay allowlist ở nhiều chỗ (chống drift).
Thêm primitive/rule tương lai chỉ sửa ở đây; version hóa qua SUPPORTED_VERSIONS.
"""

from __future__ import annotations

DSL_VERSION = "1.0"
SUPPORTED_VERSIONS = {"1.0"}

# ── Semantic role taxonomy (M7.11) — NGUỒN CHÂN LÝ ────────────
# Mỗi primitive DSL khai báo các VAI TRÒ NGỮ NGHĨA nó biểu diễn được.
# Dùng để: (a) suy Representation Plan, (b) phát hiện semantic mismatch TRƯỚC
# render, (c) xác định capability_gap (vai trò không primitive nào cover).
SEMANTIC_ROLES = [
    "structural",   # KHUNG CHỨA/bố cục LỒNG NHAU (vùng trang, container phân cấp)
                    # — KHÔNG phải hình học/đồ thị (đó là relational)
    "textual",      # nội dung chữ dài (tiêu đề/đoạn văn)
    "logical",      # giá trị/quan hệ logic (đúng-sai, cổng)
    "numeric",      # giá trị số, phép tính số
    "interactive",  # người dùng thao tác thay đổi (bật/tắt, kéo)
    "relational",   # quan hệ nút-cạnh, điểm-đoạn, liên kết giữa đối tượng
    "movement",     # đối tượng di chuyển trong không gian
    "temporal",     # diễn biến theo thời gian/hình thành từng bước
]

# Vai trò mỗi primitive (object/rule/process) ĐẠI DIỆN được.
# Lưu ý: KHÔNG primitive nào cover "structural" → đây là capability_gap thật
# (vd nội dung web cần khung chứa/bố cục phân cấp).
PRIMITIVE_ROLES: dict[str, set[str]] = {
    # object types
    "switch": {"interactive", "logical", "numeric"},
    "lamp": {"logical", "numeric"},
    "value_box": {"numeric"},
    "node": {"relational"},
    "edge": {"relational"},
    "moving_entity": {"movement"},
    "label": {"textual"},
    # object types — cấu trúc/nội dung (M7.12): structural + textual giờ CÓ primitive
    "container": {"structural"},
    "group": {"structural"},
    "heading": {"textual"},
    "paragraph": {"textual"},
    "text": {"textual"},
    # rule types
    "boolean": {"logical"},
    "weighted_sum": {"numeric"},
    # process types
    "reveal_sequence": {"temporal"},
    "move_along_path": {"movement", "temporal"},
}

MANIFEST: dict = {
    "dsl_version": DSL_VERSION,
    "object_types": {
        "switch": "công tắc bật/tắt (value 0/1); người học toggle được",
        "lamp": "đèn hiển thị giá trị 0/1 (thường là target của rule)",
        "value_box": "ô hiển thị một con số (thường là target của rule)",
        "node": "nút mạng (có node_type: client/router/server/switch/isp)",
        "edge": "cạnh nối hai object (from → to)",
        "moving_entity": "thực thể di chuyển theo process (gói tin...)",
        "label": "nhãn chữ tĩnh ngắn",
        "container": "khung chứa/bố cục — gom các object con qua \"parent\"; \"text\" là tiêu đề khung (tùy chọn)",
        "group": "nhóm logic gom các object con qua \"parent\" (không khung nổi bật)",
        "heading": "tiêu đề nổi bật — \"text\" là nội dung",
        "paragraph": "đoạn văn nhiều dòng — \"text\" là nội dung",
        "text": "dòng chữ thường — \"text\" là nội dung",
    },
    "rule_types": {
        "boolean": "giá trị dẫn xuất bằng phép logic (op: and/or/not/xor) trên inputs",
        "weighted_sum": "giá trị dẫn xuất bằng tổng inputs nhân weights tương ứng",
    },
    "bool_ops": ["and", "or", "not", "xor"],
    "interaction_types": {
        "toggle": "bật/tắt giá trị của một object (không phải target của rule)",
    },
    "process_types": {
        "move_along_path": "thực thể entity đi qua path (danh sách node) — engine bung thành các bước",
        "reveal_sequence": "hình thành cảnh TỪNG BƯỚC — mỗi step hé lộ thêm object; visibility tích lũy tất định",
    },
    "limits": {
        "max_objects": 20,
        "max_rules": 20,
        "max_interactions": 20,
        "max_processes": 8,
        "max_path": 12,
        "max_reveal_steps": 20,
        "max_text_len": 500,
        "max_nesting_depth": 4,
    },
    "top_keys": ["dsl_version", "title", "objects", "rules", "interactions", "processes", "notes"],
}


def object_types() -> set[str]:
    return set(MANIFEST["object_types"])


def rule_types() -> set[str]:
    return set(MANIFEST["rule_types"])


def bool_ops() -> set[str]:
    return set(MANIFEST["bool_ops"])


def interaction_types() -> set[str]:
    return set(MANIFEST["interaction_types"])


def process_types() -> set[str]:
    return set(MANIFEST["process_types"])


def top_keys() -> set[str]:
    return set(MANIFEST["top_keys"])


def limit(name: str) -> int:
    return MANIFEST["limits"][name]


# ── Semantic role helpers (M7.11) ─────────────────────────────

def roles_of_primitive(prim_type: str) -> set[str]:
    return set(PRIMITIVE_ROLES.get(prim_type, set()))


def all_coverable_roles() -> set[str]:
    """Hợp mọi vai trò mà ÍT NHẤT một primitive biểu diễn được."""
    covered: set[str] = set()
    for roles in PRIMITIVE_ROLES.values():
        covered |= roles
    return covered


def known_gap_roles() -> set[str]:
    """Vai trò trong taxonomy nhưng KHÔNG primitive nào cover → gap thật."""
    return set(SEMANTIC_ROLES) - all_coverable_roles()


def primitives_for_role(role: str) -> list[str]:
    """Các primitive có thể đại diện cho một vai trò (cho mapping_intent)."""
    return sorted(p for p, roles in PRIMITIVE_ROLES.items() if role in roles)


def manifest_capability_summary() -> str:
    """Tóm tắt NĂNG LỰC biểu diễn của generic.rule_scene cho stage CLASSIFY
    (M7.8) — dẫn xuất từ manifest, KHÔNG viết tay theo từng bài.

    Kèm ánh xạ ngôn ngữ tự nhiên → primitive DSL (điểm→node, đoạn thẳng→edge...)
    để classifier quyết định theo NĂNG LỰC THỰC TẾ, không theo tên môn học.
    """
    objs = ", ".join(MANIFEST["object_types"].keys())
    rules = ", ".join(MANIFEST["rule_types"].keys())
    procs = ", ".join(MANIFEST["process_types"].keys())
    return (
        "NĂNG LỰC BIỂU DIỄN của generic.rule_scene (đối chiếu năng lực bài cần với danh sách này "
        "để quyết định — KHÔNG dựa vào tên môn học):\n"
        f"- Đối tượng ({objs}). Ánh xạ ngôn ngữ tự nhiên: ĐIỂM → node; ĐOẠN THẲNG / CẠNH / "
        "đường nối hai điểm → edge; ô/hộp giá trị số → value_box; công tắc / bit → switch; "
        "đèn / đầu ra 0-1 → lamp; nhãn chữ ngắn → label; gói tin / vật di chuyển → moving_entity; "
        "KHUNG CHỨA / BỐ CỤC / phần trang → container; NHÓM → group; TIÊU ĐỀ → heading; "
        "ĐOẠN VĂN → paragraph; DÒNG CHỮ → text.\n"
        f"- Quy tắc dẫn xuất ({rules}): logic and/or/not/xor; tổng có trọng số.\n"
        f"- Tiến trình ({procs}): move_along_path (vật đi theo đường); reveal_sequence "
        "(HÌNH THÀNH CẢNH TỪNG BƯỚC — tạo/hiện đối tượng lần lượt, ví dụ dựng hình học bằng cách "
        "hiện các điểm rồi vẽ dần các đoạn thẳng).\n"
        "→ Nếu bài mô tả được bằng các năng lực trên — KỂ CẢ bài Toán/hình học dựng hình, mạch logic, "
        "đồ thị nút-cạnh, NỘI DUNG CÓ CẤU TRÚC/BỐ CỤC (trang web, tài liệu có tiêu đề/đoạn văn/khung chứa), "
        "hay quá trình hình thành từng bước — thì chọn generic.rule_scene. "
        "CHỈ trả unsupported khi cần năng lực THẬT SỰ CHƯA CÓ trong danh sách trên "
        "(đồ thị hàm số liên tục, quỹ đạo/chuyển động vật lý theo thời gian thực, phản ứng hóa học, "
        "tính toán ký hiệu/đạo hàm)."
    )


def manifest_contract_text() -> str:
    """Sinh phần contract cho prompt simulate — DẪN XUẤT từ manifest (§2)."""
    lim = MANIFEST["limits"]
    obj_lines = "\n".join(f"  - {k}: {v}" for k, v in MANIFEST["object_types"].items())
    rule_lines = "\n".join(f"  - {k}: {v}" for k, v in MANIFEST["rule_types"].items())
    inter_lines = "\n".join(f"  - {k}: {v}" for k, v in MANIFEST["interaction_types"].items())
    proc_lines = "\n".join(f"  - {k}: {v}" for k, v in MANIFEST["process_types"].items())
    return (
        f"HỢP ĐỒNG CONFIG (generic.rule_scene — DSL phiên bản {DSL_VERSION}). "
        "Bạn mô tả mô phỏng bằng đối tượng/quy tắc/tương tác/tiến trình; engine tất định tự tính diễn biến.\n\n"
        f"dsl_version PHẢI là \"{DSL_VERSION}\".\n\n"
        f"object_types cho phép (chỉ dùng trong danh sách này):\n{obj_lines}\n"
        "  Toạ độ x,y trong 0–100 để bố trí; switch có \"value\" khởi tạo 0/1; node có \"node_type\"; edge có \"from\"/\"to\".\n"
        f"  heading/paragraph/text CẦN \"text\" (nội dung chữ, ≤ {lim['max_text_len']} ký tự). "
        f"container/group gom nội dung bằng cách cho mỗi object CON một \"parent\" = id của container/group "
        f"chứa nó (lồng nhau, KHÔNG chu trình, độ sâu ≤ {lim['max_nesting_depth']}).\n\n"
        f"rule_types (giá trị DẪN XUẤT, có \"target\" là id một object):\n{rule_lines}\n"
        "  boolean cần \"op\" và \"inputs\"; weighted_sum cần \"inputs\" và \"weights\" cùng độ dài.\n\n"
        f"interaction_types:\n{inter_lines}\n  toggle chỉ áp cho object KHÔNG phải target của rule.\n\n"
        f"process_types:\n{proc_lines}\n"
        "  move_along_path: {entity: id moving_entity, path: [id node]}.\n"
        "  reveal_sequence: {steps: [{objects: [id object], narration?}]} — dùng khi cảnh phải HÌNH THÀNH TỪNG BƯỚC "
        "(vd dựng hình: bước 1 hé lộ điểm A,B; bước 2 hé lộ đoạn AB; bước 3 điểm C; bước 4 đoạn AC; bước 5 đoạn BC). "
        "Object không nằm trong reveal step nào sẽ hiện ngay từ đầu.\n\n"
        f"GIỚI HẠN: tối đa {lim['max_objects']} object, {lim['max_rules']} rule, "
        f"{lim['max_interactions']} interaction, {lim['max_processes']} process, path ≤ {lim['max_path']} nút, "
        f"reveal_sequence ≤ {lim['max_reveal_steps']} bước.\n\n"
        "Ví dụ: cổng AND = 2 switch + 1 lamp + rule boolean op=and. "
        "Đổi nhị phân = switch bit (có weight) + value_box + rule weighted_sum. "
        "Gói tin = node + edge + moving_entity + process move_along_path. "
        "Dựng hình tam giác = point/line (label) + reveal_sequence hé lộ dần. "
        "Trang web/tài liệu có bố cục = container + heading(text) + paragraph(text), "
        "mỗi con đặt parent = id container; muốn HÌNH THÀNH TỪNG BƯỚC thì thêm reveal_sequence.\n"
        "TUYỆT ĐỐI KHÔNG dùng object/rule/interaction/process ngoài manifest. "
        "KHÔNG sinh steps/timeline/state/frames/kết quả — engine tự dựng."
    )
