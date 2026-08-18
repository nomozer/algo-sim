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
    # ── M7.14C: vai trò QUAN HỆ DẪN XUẤT — cố ý KHÔNG primitive nào cover ──
    # Đề cần các quan hệ phải TÍNH RA bằng solver mà DSL chưa có → capability_gap
    # thật: THÀ TỪ CHỐI TRUNG THỰC còn hơn để LLM đoán tọa độ rồi render một
    # hình "nhìn có vẻ đúng" nhưng sai bản chất (kéo M mà E/F/P đứng yên).
    "geometric_projection",    # chân đường cao / hình chiếu vuông góc
    "geometric_perpendicular", # đường phải DỰNG vuông góc với đường khác
    "geometric_intersection",  # giao điểm phải TÍNH (kể cả "cắt lần thứ hai")
    "geometric_circle",        # đường tròn qua các điểm / ngoại tiếp / tiếp tuyến
    "geometric_locus",         # quỹ tích / "luôn nằm trên một đường cố định"
    "numeric_threshold",       # "ít nhất k trong n" / so sánh tổng với ngưỡng
    "continuous_motion",       # quỹ đạo / chuyển động liên tục theo thời gian thực
    "arbitrary_algorithm",     # thuật toán tự do không có engine tương ứng
]

# Vai trò mỗi primitive (object/rule/process/interaction) ĐẠI DIỆN được.
# Lưu ý (M7.14C): các vai trò geometric_*/numeric_threshold/continuous_motion/
# arbitrary_algorithm KHÔNG xuất hiện ở đây — known_gap_roles() trả về chúng
# và representation plan sẽ dừng sớm với capability_gap (xem docs/CORRECTNESS.md).
PRIMITIVE_ROLES: dict[str, set[str]] = {
    # object types
    "switch": {"interactive", "logical", "numeric"},
    "lamp": {"logical", "numeric"},
    "value_box": {"numeric"},
    "slider": {"interactive", "numeric"},
    "color_swatch": {"numeric"},
    "array_strip": {"numeric"},
    "metric_gauge": {"numeric"},
    "bar_chart": {"numeric"},
    "table_grid": {"numeric"},
    "stack_view": {"numeric"},
    "queue_view": {"numeric"},
    "tree_element": {"numeric"},
    "bit_register": {"logical", "numeric"},
    "logic_gate": {"logical"},
    "pointer": {"numeric"},
    "coordinate_plane": {"numeric"},
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
    "formula": {"numeric"},
    # interaction types (M7.13A) — tương tác cũng cover vai trò "interactive"
    "toggle": {"interactive"},
    "drag": {"interactive"},
    "set_param": {"interactive"},
    "button_action": {"interactive"},
    # process types
    "reveal_sequence": {"temporal"},
    "move_along_path": {"movement", "temporal"},
    "step_sequence": {"temporal"},
}

MANIFEST: dict = {
    "dsl_version": DSL_VERSION,
    "object_types": {
        "switch": "công tắc bật/tắt (value 0/1); người học toggle được",
        "lamp": "đèn hiển thị giá trị 0/1 (thường là target của rule)",
        "value_box": "ô hiển thị một con số (thường là target của rule)",
        "slider": "thanh trượt chỉnh giá trị số (value, min, max, step, unit); người học kéo/chỉnh được",
        "color_swatch": "ô hiển thị mẫu màu trực quan (nhận giá trị màu hex/rgb hoặc tính từ rule)",
        "array_strip": "dải ô mảng hiển thị danh sách phần tử (items)",
        "metric_gauge": "đồng hồ đo / thanh tiến độ hiển thị tỉ lệ phần trăm hoặc đại lượng",
        "bar_chart": "biểu đồ cột trực quan hiển thị dãy giá trị số (bars: [{id?, value, label?, color?}], max_val)",
        "table_grid": "bảng dữ liệu 2 chiều (headers: chuỗi[], rows: giá_trị[][], highlighted_cells?)",
        "stack_view": "ngăn xếp LIFO với đỉnh top (items: mảng giá trị, capacity?)",
        "queue_view": "hàng đợi FIFO với đầu front và đuôi rear (items: mảng giá trị, capacity?)",
        "tree_element": "nút cây nhị phân hoặc phân cấp (value, left?, right?, parent?, label?)",
        "bit_register": "thanh ghi bit nhị phân (bits: [0/1] hoặc value: số, size: 4/8/16, show_decimal?, show_hex?)",
        "logic_gate": "biểu tượng cổng logic chuẩn ANSI/IEEE (gate_type: and/or/not/xor/nand/nor, inputs: [id], target: id)",
        "pointer": "con trỏ chỉ mục thuật toán i, j, mid, top... (target_id, index?, label, color?)",
        "coordinate_plane": "hệ tọa độ Oxy mặt phẳng Descartes (min_x, max_x, min_y, max_y, show_grid?)",
        "node": (
            "nút/đỉnh — điểm hình học (không node_type) HOẶC một thành phần có vai trò "
            "(node_type, chuỗi tự do): mạng (client/router/server/switch/isp) hoặc "
            "hệ thống thông tin (actor/process/data_store/input/output)"
        ),
        "edge": (
            "cạnh nối hai object (from → to); \"directed\": true khi CHIỀU có ý nghĩa "
            "(luồng dữ liệu, request/response) — renderer vẽ mũi tên from → to"
        ),
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
        "formula": "giá trị dẫn xuất bằng biểu thức toán/chuỗi/màu an toàn (expression, inputs, target)",
    },
    "bool_ops": ["and", "or", "not", "xor"],
    "interaction_types": {
        "toggle": "bật/tắt giá trị 0/1 của một object CÓ \"value\" khởi tạo (không phải target của rule)",
        "set_param": "chỉnh giá trị của slider / tham số số",
        "button_action": "nút bấm tương tác kích hoạt thao tác / bước tiếp theo",
        "drag": (
            "kéo-thả một object trong canvas — vị trí do engine sở hữu, "
            "cạnh nối (edge) tự bám theo hai đầu; constraints tùy chọn: bounds/axis/snap"
        ),
    },
    # M7.13A: type được phép làm target của drag (v1 chỉ node — điểm hình học/đỉnh đồ thị).
    # KHÔNG drag: edge (vị trí dẫn xuất từ hai đầu), structural/textual (layout theo
    # luồng tài liệu), moving_entity (vị trí do process sở hữu — ownership rule).
    "drag_target_types": ["node"],
    # M8-PRE (S2): từ vựng GỢI Ý cho node_type — node_type là CHUỖI TỰ DO (validator
    # không ép enum); danh sách này chỉ để prompt không bó hẹp vào danh từ MẠNG.
    # Cùng một primitive (node+edge) phục vụ nhiều miền: mạng máy tính VÀ hệ thống
    # thông tin (actor/process/data_store) — tái sử dụng năng lực, KHÔNG thêm type mới.
    "node_type_vocabulary": {
        "network": ["client", "router", "server", "switch", "isp"],
        "system": ["actor", "process", "data_store", "input", "output"],
    },
    "process_types": {
        "move_along_path": "thực thể entity đi qua path (danh sách node) — engine bung thành các bước",
        "reveal_sequence": "hình thành cảnh TỪNG BƯỚC — mỗi step hé lộ thêm object; visibility tích lũy tất định",
        "step_sequence": "chuỗi các bước mô phỏng diễn tiến thuật toán (steps: [{action, targets?, state?, indices?, pointer_id?, to_index?, narration?}])",
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


def drag_target_types() -> set[str]:
    """Type được phép làm target của interaction drag (M7.13A)."""
    return set(MANIFEST["drag_target_types"])


def node_type_vocabulary() -> dict[str, list[str]]:
    """Từ vựng GỢI Ý cho node_type theo miền (M8-PRE S2).

    KHÔNG phải allowlist: validator chấp nhận node_type là chuỗi bất kỳ. Danh
    sách này chỉ dùng để SINH prompt — chống việc prompt chỉ nêu danh từ mạng
    khiến LLM không nghĩ tới actor/process/data_store (bug: cảnh phân tích hệ
    thống bị từ chối im lặng dù DSL biểu diễn được)."""
    return {k: list(v) for k, v in MANIFEST["node_type_vocabulary"].items()}


def temporal_process_types() -> set[str]:
    """Họ process DIỄN BIẾN THEO THỜI GIAN — dẫn xuất từ role taxonomy, KHÔNG
    hard-code tên process (M7.13A): mọi process có vai trò "temporal"."""
    return {p for p in MANIFEST["process_types"] if "temporal" in PRIMITIVE_ROLES.get(p, set())}


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
    sysv = "/".join(MANIFEST["node_type_vocabulary"]["system"])
    netv = "/".join(MANIFEST["node_type_vocabulary"]["network"])
    return (
        "NĂNG LỰC BIỂU DIỄN của generic.rule_scene (đối chiếu năng lực bài cần với danh sách này "
        "để quyết định — KHÔNG dựa vào tên môn học):\n"
        f"- Đối tượng ({objs}). Ánh xạ ngôn ngữ tự nhiên: ĐIỂM → node; ĐOẠN THẲNG / CẠNH / "
        "đường nối hai điểm → edge; ô/hộp giá trị số → value_box; công tắc / bit → switch; "
        "thanh trượt / tham số điều chỉnh (kênh màu, thanh cuộn giá trị) → slider; "
        "ô hiển thị màu sắc trực quan → color_swatch; mảng ô giá trị → array_strip; "
        "đồng hồ đo tỉ lệ / thanh tiến độ → metric_gauge; biểu đồ cột sắp xếp → bar_chart; "
        "bảng dữ liệu 2D / CSDL / quy hoạch động / bảng chân trị → table_grid; "
        "ngăn xếp LIFO → stack_view; hàng đợi FIFO → queue_view; cây nhị phân / phân cấp → tree_node; "
        "thanh ghi nhị phân (chuyển đổi cơ số Dec/Bin/Hex, phép toán bit) → bit_register; "
        "cổng logic chuẩn ANSI/IEEE (AND/OR/NOT/XOR/NAND/NOR) → logic_gate; "
        "con trỏ thuật toán (i, j, mid, top, front...) → pointer; "
        "hệ trục tọa độ Descartes Oxy → coordinate_plane; "
        "đèn / đầu ra 0-1 → lamp; nhãn chữ ngắn → label; gói tin / vật di chuyển → moving_entity; "
        "KHUNG CHỨA / BỐ CỤC / phần trang → container; NHÓM → group; TIÊU ĐỀ → heading; "
        "ĐOẠN VĂN → paragraph; DÒNG CHỮ → text.\n"
        f"- HỆ THỐNG THÔNG TIN / SƠ ĐỒ LUỒNG DỮ LIỆU (cùng primitive node+edge, node_type là "
        f"chuỗi tự do): NGƯỜI DÙNG / TÁC NHÂN → node (node_type actor); CHỨC NĂNG / XỬ LÍ / "
        f"công đoạn → node (node_type process); KHO DỮ LIỆU / nơi lưu trữ → node (node_type "
        f"data_store); ĐẦU VÀO / ĐẦU RA → node (node_type input/output). LUỒNG DỮ LIỆU / "
        f'yêu cầu / phản hồi giữa chúng → edge có "directed": true (vẽ mũi tên from → to). '
        f"Dữ liệu ĐI QUA các công đoạn → moving_entity + move_along_path. "
        f"Từ vựng node_type gợi ý: hệ thống ({sysv}); mạng ({netv}).\n"
        f"- Quy tắc dẫn xuất ({rules}): logic and/or/not/xor; tổng có trọng số; công thức biểu thức formula "
        "(tính toán phản ứng như pha màu rgb_to_hex(r,g,b), phép toán bitwise bit_and/bit_or/shift_left, clamp, min, max).\n"
        f"- Tiến trình ({procs}): move_along_path (vật đi theo đường); reveal_sequence (hình thành cảnh từng bước); "
        "step_sequence (DIỄN TIẾN THUẬT TOÁN TỪNG BƯỚC — highlight, swap đổi chỗ phần tử, di chuyển con trỏ pointer, gán giá trị).\n"
        "- Tương tác: toggle (bật/tắt công tắc có value 0/1); set_param (chỉnh slider / tham số số); "
        "button_action (nút bấm thao tác); drag (học sinh KÉO/DI CHUYỂN một điểm/node, các cạnh nối tự cập nhật theo).\n"
        "→ Nếu bài mô tả được bằng các năng lực trên — KỂ CẢ bài Thuật toán sắp xếp/tìm kiếm, Cấu trúc dữ liệu, "
        "Chuyển đổi cơ số / phép toán nhị phân, Bảng CSDL / quy hoạch động, mô hình màu sắc RGB / tham số liên tục, "
        "mạch logic, đồ thị nút-cạnh, NỘI DUNG CÓ CẤU TRÚC/BỐ CỤC, hay SƠ ĐỒ HỆ THỐNG THÔNG TIN — thì chọn generic.rule_scene. "
        "CHỈ trả unsupported khi cần năng lực THẬT SỰ CHƯA CÓ trong danh sách trên: "
        "QUAN HỆ HÌNH HỌC PHẢI TÍNH (chân đường cao/hình chiếu, đường dựng vuông góc, giao điểm, "
        "đường tròn ngoại tiếp/qua các điểm, tiếp tuyến, quỹ tích/điểm di động kéo theo hệ); "
        "điều kiện NGƯỠNG kiểu 'ít nhất k trong n'; đồ thị hàm số liên tục; quỹ đạo/chuyển động "
        "vật lý theo thời gian thực; phản ứng hóa học; tính toán ký hiệu/đạo hàm; "
        "thuật toán do người dùng tự nghĩ không có mô tả cụ thể."
    )


def manifest_contract_text() -> str:
    """Sinh phần contract cho prompt simulate — DẪN XUẤT từ manifest (§2)."""
    lim = MANIFEST["limits"]
    vocab = MANIFEST["node_type_vocabulary"]
    obj_lines = "\n".join(f"  - {k}: {v}" for k, v in MANIFEST["object_types"].items())
    rule_lines = "\n".join(f"  - {k}: {v}" for k, v in MANIFEST["rule_types"].items())
    inter_lines = "\n".join(f"  - {k}: {v}" for k, v in MANIFEST["interaction_types"].items())
    proc_lines = "\n".join(f"  - {k}: {v}" for k, v in MANIFEST["process_types"].items())
    return (
        f"HỢP ĐỒNG CONFIG (generic.rule_scene — DSL phiên bản {DSL_VERSION}). "
        "Bạn mô tả mô phỏng bằng đối tượng/quy tắc/tương tác/tiến trình; engine tất định tự tính diễn biến.\n\n"
        f"dsl_version PHẢI là \"{DSL_VERSION}\".\n\n"
        f"object_types cho phép (chỉ dùng trong danh sách này):\n{obj_lines}\n"
        "  Toạ độ x,y trong 0–100 để bố trí; switch có \"value\" khởi tạo 0/1; slider có \"value\", \"min\", \"max\", \"step\"; edge có \"from\"/\"to\".\n"
        "  color_swatch nhận màu qua rule target hoặc trường \"color\" (vd \"#ff0000\").\n"
        "  bar_chart: \"bars\": [{\"id\": str, \"value\": số, \"label\": str, \"color\": str}], \"max_val\": số.\n"
        "  table_grid: \"headers\": [str], \"rows\": [[giá_trị]], \"highlighted_cells\": [{\"row\": số, \"col\": số, \"color\": str}].\n"
        "  stack_view / queue_view: \"items\": [giá_trị], \"capacity\": số.\n"
        "  tree_element: \"value\": giá_trị, \"left\": id_con_trái, \"right\": id_con_phải, \"parent\": id_cha.\n"
        "  bit_register: \"bits\": [0, 1, ...], \"size\": 8|16, \"show_decimal\": bool, \"show_hex\": bool.\n"
        "  logic_gate: \"gate_type\": \"and\"|\"or\"|\"not\"|\"xor\"|\"nand\"|\"nor\", \"inputs\": [id], \"target\": id.\n"
        "  pointer: \"target_id\": id_object, \"index\": chỉ_số_trong_mảng, \"label\": nhãn_con_trỏ (vd \"i\", \"pivot\").\n"
        "  coordinate_plane: \"min_x\": số, \"max_x\": số, \"min_y\": số, \"max_y\": số, \"show_grid\": bool.\n"
        f"  node có \"node_type\" (chuỗi tự do) — mạng: {'/'.join(vocab['network'])}; "
        f"hệ thống thông tin: {'/'.join(vocab['system'])}; điểm hình học thì BỎ TRỐNG node_type.\n"
        "  edge có \"directed\": true khi CHIỀU mang ý nghĩa (luồng dữ liệu, yêu cầu → phản hồi, "
        "dữ liệu đi vào một chức năng rồi ra kho lưu trữ) — renderer vẽ mũi tên từ \"from\" tới \"to\". "
        "Quan hệ KHÔNG có chiều (đoạn thẳng hình học, liên kết mạng hai chiều) thì bỏ trống/false.\n"
        f"  BẮT BUỘC: nếu cảnh có từ 2 node vai trò HỆ THỐNG trở lên ({'/'.join(vocab['system'])}) "
        "thì MỌI edge nối chúng PHẢI có \"directed\": true — sơ đồ luồng dữ liệu mà không thấy "
        "hướng đi thì vô nghĩa. Spec thiếu điều này sẽ bị TỪ CHỐI.\n"
        "  Đặt tên hiển thị cho node bằng \"label\" (KHÔNG dùng \"text\" cho node).\n"
        f"  heading/paragraph/text CẦN \"text\" (nội dung chữ, ≤ {lim['max_text_len']} ký tự). "
        f"container/group gom nội dung bằng cách cho mỗi object CON một \"parent\" = id của container/group "
        f"chứa nó (lồng nhau, KHÔNG chu trình, độ sâu ≤ {lim['max_nesting_depth']}).\n\n"
        f"rule_types (giá trị DẪN XUẤT, có \"target\" là id một object):\n{rule_lines}\n"
        "  boolean cần \"op\" và \"inputs\"; weighted_sum cần \"inputs\" và \"weights\" cùng độ dài;\n"
        "  formula cần \"expression\" (biểu thức toán/chuỗi/bit) và \"inputs\" (danh sách id object đầu vào).\n"
        "  Ví dụ formula: {\"type\": \"formula\", \"expression\": \"rgb_to_hex(r, g, b)\", \"inputs\": [\"r\", \"g\", \"b\"], \"target\": \"swatch_color\"}.\n"
        "  Mỗi giá trị dẫn xuất (target) chỉ do đúng MỘT rule sở hữu (cấm hai rule cùng target).\n"
        "  ĐIỀU KIỆN GHÉP/LỒNG NHAU — target của một rule ĐƯỢC PHÉP làm input của rule khác; "
        "engine tự tính lan truyền qua chuỗi. Khi đề có điều kiện ghép (một phần điều kiện phải "
        "tính TRƯỚC rồi mới kết hợp tiếp), hãy TÁCH thành chuỗi rule qua một object trung gian: "
        "thêm một lamp/value_box làm target của rule con (vd: kq_phu), rồi dùng id đó trong inputs của rule "
        "ngoài. KHÔNG ép phẳng nhiều mức điều kiện vào một rule duy nhất — sai ngữ nghĩa.\n"
        "\"value\" khởi tạo chỉ đặt cho ĐẦU VÀO nguồn (switch/slider học sinh chỉnh) — KHÔNG gắn "
        "\"value\" cho object trung gian/đèn dẫn xuất (engine tự tính) hay label trang trí.\n\n"
        f"interaction_types:\n{inter_lines}\n"
        "  toggle chỉ áp cho object CÓ \"value\" khởi tạo (0/1) và KHÔNG phải target của rule.\n"
        "  set_param dùng cho slider/input số.\n"
        "  button_action dùng cho nút bấm kích hoạt thao tác.\n"
        f"  drag chỉ áp cho object type {'/'.join(sorted(MANIFEST['drag_target_types']))}; "
        "KHÔNG drag vật đang được process điều khiển. \"constraints\" tùy chọn: "
        '{"bounds": {"min_x", "max_x", "min_y", "max_y"} trong 0–100, "axis": "x"|"y", "snap": số > 0}.\n\n'
        f"process_types:\n{proc_lines}\n"
        "  move_along_path: {entity: id moving_entity, path: [id node]}.\n"
        "  reveal_sequence: {steps: [{objects: [id object], narration?}]}.\n"
        "  step_sequence: {steps: [{action: \"highlight\"|\"swap\"|\"set_value\"|\"move_pointer\", targets?, state?, indices?, pointer_id?, to_index?, narration?}]}.\n\n"
        f"GIỚI HẠN: tối đa {lim['max_objects']} object, {lim['max_rules']} rule, "
        f"{lim['max_interactions']} interaction, {lim['max_processes']} process, path ≤ {lim['max_path']} nút, "
        f"reveal_sequence ≤ {lim['max_reveal_steps']} bước, step_sequence ≤ {lim['max_reveal_steps']} bước.\n"
        "TUYỆT ĐỐI KHÔNG dùng object/rule/interaction/process ngoài manifest. "
        "Engine tất định sẽ tự tính toán timeline hoạt cảnh và cập nhật trạng thái trực quan từ các bước trong processes."
    )


# M13 hotfix: subtyping một chiều — bảng NGUỒN DUY NHẤT cho role_satisfies()
# và dsl_semantic_contract()["role_compatibility"]. Thêm cặp mới CHỈ khi có
# audit chứng minh (như logical→numeric ở đây); mặc định vẫn DENY mọi cặp
# khác role_satisfies chưa cover.
ROLE_COMPATIBILITY: list[dict[str, str]] = [
    {"produced": "logical", "accepted": "numeric"},
]


def role_satisfies(produced: str, accepted: str) -> bool:
    """M13 hotfix (FP live boolean→value_box): subtyping một chiều — True khi
    một giá trị mang vai trò `produced` được CHẤP NHẬN ở vị trí cần `accepted`.

    Exact match luôn đúng. Ngoài ra: `logical` SATISFIES `numeric` — boolean
    executor sinh đúng 0/1, giá trị 0/1 LÀ số, nên hợp lệ ở vị trí numeric.
    KHÔNG có runtime conversion nào chạy vì việc này — engine không đổi gì,
    đây thuần là nới validator theo MỘT CHIỀU.

    Chiều ngược lại (`numeric` KHÔNG satisfies `logical`) LUÔN False — đó
    chính là lớp coercion ngầm kiểu `v >= 1` mà M13 (Task 3) sinh ra để diệt,
    và phải giữ DENY (canary `test_derived_target_sai_role_bi_tu_choi_weighted_sum_nuoi_boolean`).

    Dẫn xuất từ ROLE_COMPATIBILITY — cùng bảng dữ liệu nguồn với
    `dsl_semantic_contract()["role_compatibility"]`, không viết tay hai nơi."""
    if produced == accepted:
        return True
    return any(c["produced"] == produced and c["accepted"] == accepted for c in ROLE_COMPATIBILITY)


def value_provider_types(role: str) -> set[str]:
    """M13: các OBJECT type có vai trò cung cấp giá trị `role` (vd "numeric").

    DẪN XUẤT từ PRIMITIVE_ROLES ∩ object_types — không viết tay allowlist
    (anti-pattern #1). node/edge chỉ relational → không bao giờ là provider.
    """
    object_types = set(MANIFEST["object_types"])
    return {t for t in object_types if role in PRIMITIVE_ROLES.get(t, set())}


# M13: vai trò input/output của mỗi rule type (không viết tay ở validator/frontend).
RULE_IO_ROLES = {
    "weighted_sum": {"input_role": "numeric", "output_role": "numeric"},
    "boolean": {"input_role": "logical", "output_role": "logical"},
    "formula": {"input_role": "numeric", "output_role": "numeric"},
}

# M13 Task 12b: field object được nhận khi add_object qua SimulationPatch v1.
# NGUỒN CHÂN LÝ DUY NHẤT — backend patch.py và frontend patch.ts đều tiêu thụ
# qua dsl_semantic_contract()/dsl-contract.json, chống lệch tay như "directed"
# từng lệch (backend có, frontend không — M8-PRE S2 không được mirror sang patch.ts).
PATCH_ADD_FIELDS: tuple[str, ...] = (
    "id", "type", "x", "y", "label", "text", "parent", "value", "node_type", "from", "to", "directed",
    "min", "max", "step", "unit", "color", "items", "expression",
    "bars", "max_val", "headers", "rows", "highlighted_cells", "capacity",
    "bits", "size", "show_decimal", "show_hex", "gate_type", "target_id", "index",
    "min_x", "max_x", "min_y", "max_y", "show_grid", "left", "right",
)


def patch_add_fields() -> set[str]:
    return set(PATCH_ADD_FIELDS)


def dsl_semantic_contract() -> dict:
    """M13: hợp đồng ngữ nghĩa CANONICAL — nguồn duy nhất cho cả hai tầng.
    Frontend tiêu thụ bản sinh (dsl-contract.json); test sync-lock chống drift."""
    object_types = set(MANIFEST["object_types"])
    return {
        "value_providers": {
            role: sorted(value_provider_types(role)) for role in ("numeric", "logical")
        },
        "rule_io": RULE_IO_ROLES,
        "object_roles": {
            t: sorted(PRIMITIVE_ROLES[t]) for t in sorted(object_types)
        },
        # M13 hotfix: subtyping một chiều (logical satisfies numeric); KHÔNG
        # runtime conversion. Dẫn xuất từ ROLE_COMPATIBILITY — nguồn duy nhất
        # cũng cấp cho role_satisfies().
        "role_compatibility": [dict(c) for c in ROLE_COMPATIBILITY],
        "patch_add_fields": sorted(PATCH_ADD_FIELDS),
    }
