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
    # interaction types (M7.13A) — tương tác cũng cover vai trò "interactive"
    "toggle": {"interactive"},
    "drag": {"interactive"},
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
    },
    "bool_ops": ["and", "or", "not", "xor"],
    "interaction_types": {
        "toggle": "bật/tắt giá trị 0/1 của một object CÓ \"value\" khởi tạo (không phải target của rule)",
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
        f"- Quy tắc dẫn xuất ({rules}): logic and/or/not/xor; tổng có trọng số.\n"
        f"- Tiến trình ({procs}): move_along_path (vật đi theo đường); reveal_sequence "
        "(HÌNH THÀNH CẢNH TỪNG BƯỚC — tạo/hiện đối tượng lần lượt, ví dụ dựng hình học bằng cách "
        "hiện các điểm rồi vẽ dần các đoạn thẳng).\n"
        "- Tương tác: toggle (bật/tắt công tắc có value 0/1); drag (học sinh KÉO/DI CHUYỂN "
        "một điểm/node, các cạnh nối tự cập nhật theo — dùng khi đề muốn thao tác trực tiếp lên hình; "
        "KHÔNG dùng toggle cho điểm/node).\n"
        "→ Nếu bài mô tả được bằng các năng lực trên — KỂ CẢ bài Toán/hình học dựng hình TƯỜNG MINH "
        "(vẽ các điểm/đoạn được nêu tên), mạch logic, đồ thị nút-cạnh, NỘI DUNG CÓ CẤU TRÚC/BỐ CỤC "
        "(trang web, tài liệu có tiêu đề/đoạn văn/khung chứa), SƠ ĐỒ HỆ THỐNG THÔNG TIN "
        "(người dùng/chức năng/kho dữ liệu/luồng dữ liệu — kể cả khi đề hỏi 'phân tích hệ thống', "
        "'xác định người dùng, dữ liệu lưu trữ, đầu vào, đầu ra, chức năng, mô tả hoạt động'), "
        "hay quá trình hình thành từng bước — thì chọn generic.rule_scene. "
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
        "  Toạ độ x,y trong 0–100 để bố trí; switch có \"value\" khởi tạo 0/1; edge có \"from\"/\"to\".\n"
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
        "  boolean cần \"op\" và \"inputs\"; weighted_sum cần \"inputs\" và \"weights\" cùng độ dài.\n"
        "  ĐIỀU KIỆN GHÉP/LỒNG NHAU — target của một rule ĐƯỢC PHÉP làm input của rule khác; "
        "engine tự tính lan truyền qua chuỗi. Khi đề có điều kiện ghép (một phần điều kiện phải "
        "tính TRƯỚC rồi mới kết hợp tiếp), hãy TÁCH thành chuỗi rule qua một object trung gian: "
        "thêm một lamp/value_box làm target của rule con, rồi dùng id đó trong inputs của rule "
        "ngoài. KHÔNG ép phẳng nhiều mức điều kiện vào một rule duy nhất — sai ngữ nghĩa. "
        "Ví dụ trừu tượng: rule con {\"op\": \"and\", \"inputs\": [\"dk1\", \"dk2\"], \"target\": \"kq_phu\"} "
        "(kq_phu là một lamp trung gian), rule ngoài {\"op\": \"or\", \"inputs\": [\"dk3\", \"kq_phu\"], "
        "\"target\": \"den_chinh\"}. Mỗi target chỉ được đúng MỘT rule sở hữu; không tạo chu trình. "
        "\"value\" khởi tạo chỉ đặt cho ĐẦU VÀO nguồn (switch học sinh bật/tắt) — KHÔNG gắn "
        "\"value\" cho object trung gian/đèn dẫn xuất (engine tự tính) hay label trang trí.\n\n"
        f"interaction_types:\n{inter_lines}\n"
        "  toggle chỉ áp cho object CÓ \"value\" khởi tạo (0/1) và KHÔNG phải target của rule. "
        "KHÔNG dùng toggle cho node/điểm — muốn học sinh DI CHUYỂN/KÉO điểm thì dùng drag.\n"
        f"  drag chỉ áp cho object type {'/'.join(sorted(MANIFEST['drag_target_types']))}; "
        "KHÔNG drag vật đang được process điều khiển. \"constraints\" tùy chọn: "
        '{"bounds": {"min_x", "max_x", "min_y", "max_y"} trong 0–100, "axis": "x"|"y", "snap": số > 0}. '
        "Chỉ thêm drag khi bài CẦN học sinh thao tác trực tiếp (kéo điểm để quan sát) — không thêm bừa.\n\n"
        f"process_types:\n{proc_lines}\n"
        "  move_along_path: {entity: id moving_entity, path: [id node]}.\n"
        "  reveal_sequence: {steps: [{objects: [id object], narration?}]} — dùng khi cảnh phải HÌNH THÀNH TỪNG BƯỚC "
        "(vd dựng hình: bước 1 hé lộ điểm A,B; bước 2 hé lộ đoạn AB; bước 3 điểm C; bước 4 đoạn AC; bước 5 đoạn BC). "
        "Object không nằm trong reveal step nào sẽ hiện ngay từ đầu.\n\n"
        f"GIỚI HẠN — ĐẾM CHO ĐÚNG: edge, moving_entity, heading, paragraph, label… TẤT CẢ đều nằm "
        f"trong \"objects\" nên đều TÍNH vào giới hạn {lim['max_objects']}. Một sơ đồ 6 thành phần "
        f"nối bằng 6 luồng đã tốn 12 object. Hãy chọn các thành phần CHÍNH và GỘP chi tiết phụ "
        f"(sơ đồ hệ thống: tối đa ~6 thành phần + các luồng giữa chúng); đừng vẽ mọi chi tiết rồi vượt hạn mức.\n"
        "  TIẾT KIỆM OBJECT — hai lỗi thường gặp làm vượt hạn mức:\n"
        "  (a) Muốn ghi chữ trên một CẠNH thì dùng chính trường \"label\" CỦA EDGE ĐÓ "
        "(vd {\"id\":\"f1\",\"type\":\"edge\",\"from\":\"a\",\"to\":\"b\",\"directed\":true,\"label\":\"gửi yêu cầu\"}) — "
        "TUYỆT ĐỐI KHÔNG tạo thêm object \"label\" riêng cho mỗi cạnh.\n"
        "  (b) Sơ đồ đã có \"title\" ở cấp cao nhất → KHÔNG cần thêm heading/paragraph/container trang trí.\n"
        f"GIỚI HẠN: tối đa {lim['max_objects']} object, {lim['max_rules']} rule, "
        f"{lim['max_interactions']} interaction, {lim['max_processes']} process, path ≤ {lim['max_path']} nút, "
        f"reveal_sequence ≤ {lim['max_reveal_steps']} bước.\n\n"
        "Ví dụ: cổng AND = 2 switch + 1 lamp + rule boolean op=and. "
        "Đổi nhị phân = switch bit (có weight) + value_box + rule weighted_sum. "
        "Gói tin = node + edge + moving_entity + process move_along_path. "
        "Dựng hình tam giác = point/line (label) + reveal_sequence hé lộ dần. "
        "Trang web/tài liệu có bố cục = container + heading(text) + paragraph(text), "
        "mỗi con đặt parent = id container; muốn HÌNH THÀNH TỪNG BƯỚC thì thêm reveal_sequence. "
        "Sơ đồ HỆ THỐNG THÔNG TIN = node(node_type actor/process/data_store/input/output) + "
        "edge directed=true cho từng LUỒNG DỮ LIỆU; muốn cho thấy dữ liệu CHẠY QUA các công đoạn "
        "thì thêm moving_entity + move_along_path đi theo đúng các node đó.\n"
        "TUYỆT ĐỐI KHÔNG dùng object/rule/interaction/process ngoài manifest. "
        "KHÔNG sinh steps/timeline/state/frames/kết quả — engine tự dựng."
    )
