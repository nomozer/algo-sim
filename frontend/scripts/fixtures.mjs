/**
 * fixtures.mjs — BỘ FIXTURE DÙNG CHUNG cho các runner Chrome/CDP.
 *
 * Tách ra từ `visual-stress-audit.mjs` ở W4B-1A (nguyên văn, không đổi dữ
 * liệu). Lý do: bản soát responsive cần ĐÚNG bộ fixture này để phủ những
 * target mà `offlineCatalog()` của app không có mẫu (app có 17 mẫu / 13
 * target). Chép sang script thứ hai sẽ tạo bộ fixture song song — thứ sẽ trôi
 * khỏi nhau ngay lượt sau. Một trách nhiệm, một nguồn.
 *
 * File này là DỮ LIỆU THUẦN: không CDP, không I/O, không side effect.
 */
/* ══════════════ FIXTURE ══════════════
 * canonical · boundary · stress cho MỖI renderer riêng biệt.
 * Config lấy đúng shape đã qua validator backend (không đoán).
 */
const env = (simulation_id, domain, title, config, extra = {}) => ({
  status: "ok", simulation_id, domain, visual_mode: "2d",
  title, description: null, notes: null, config, ...extra,
});
const N = (id, left = null, right = null, label = id) => ({ id, label, left, right });
const tree = (variant, rootId, nodes) =>
  ({ specVersion: "tree-1.0", variant, rootId, nodes, notes: null });
const gnode = (id, label = null) => ({ id, label });

/** Nhãn tiếng Việt DÀI + dấu — stress thật, không phải A–G. */
const VN = {
  a: "Trạm Hải Đăng", b: "Trạm Sương Mai", c: "Trạm Thông Xanh",
  d: "Trạm Suối Đá Vọng", e: "Trạm Mây Trắng Đỉnh Trời",
};


/* ══════════════ W2B-VR — fixture truy vấn bảng ══════════════
 * Config đúng shape validator; engine tự tính mọi phán quyết/thứ tự/tích luỹ.
 */
const TB = (schema, rows, q = {}) => ({ specVersion: "table-1.0", schema, rows, ...q });
const COL = (name, type, label = null) => ({ name, type, label });

/* 8 học sinh; Bình và Dũng CÙNG 8.0 để quan sát sắp xếp ổn định. */
const HS_SCHEMA = [COL("ten", "text", "Họ và tên"), COL("to", "text", "Tổ"),
                   COL("diem", "number", "Điểm")];
const HS_ROWS = [
  { ten: "Nguyễn An", to: "A", diem: 8.5 },
  { ten: "Trần Bình", to: "B", diem: 8.0 },
  { ten: "Lê Chi", to: "A", diem: 9.25 },
  { ten: "Phạm Dũng", to: "B", diem: 8.0 },
  { ten: "Đỗ Hà", to: "A", diem: 6.5 },
  { ten: "Vũ Khánh", to: "C", diem: 7.75 },
  { ten: "Bùi Linh", to: "B", diem: 9.0 },
  { ten: "Hoàng My", to: "C", diem: 5.5 },
];
/* Cột điểm có Ô TRỐNG — kiểm ô trống KHÔNG bị coi là 0. */
const KT_SCHEMA = [COL("ten", "text", "Họ và tên"), COL("diem_kt", "number", "Điểm kiểm tra")];
const KT_ROWS = [
  { ten: "Nguyễn An", diem_kt: 8 }, { ten: "Trần Bình", diem_kt: null },
  { ten: "Lê Chi", diem_kt: 10 }, { ten: "Phạm Dũng", diem_kt: null },
  { ten: "Đỗ Hà", diem_kt: 6 },
];
/* Gần biên: 12 dòng × 8 cột, nhãn dài, Unicode, số âm/thập phân, ô trống. */
const WIDE_SCHEMA = [
  COL("ho_ten", "text", "Họ và tên đầy đủ của học sinh"),
  COL("lop", "text", "Lớp"), COL("to", "text", "Tổ"),
  COL("diem_tb", "number", "Điểm trung bình học kỳ"),
  COL("chenh_lech", "number", "Chênh lệch so với trung bình lớp"),
  COL("ghi_chu", "text", "Ghi chú của giáo viên chủ nhiệm"),
  COL("noi_tru", "boolean", "Ở nội trú"),
  COL("so_buoi_vang", "number", "Số buổi vắng"),
];
const WIDE_ROWS = Array.from({ length: 12 }, (_, i) => ({
  ho_ten: ["Nguyễn Thị Ánh Tuyết", "Trần Quốc Bảo Long", "Lê Hoàng Phương Chi",
           "Phạm Đình Dũng Kiệt", "Đỗ Thị Thu Hà", "Vũ Khánh Duy Anh",
           "Bùi Thị Mỹ Linh", "Hoàng Minh Nhật My", "Đặng Văn Sơn Tùng",
           "Ngô Bảo Trâm Anh", "Lý Gia Huy Hoàng", "Chu Thị Kim Ngân"][i],
  lop: "11A" + ((i % 3) + 1), to: ["A", "B", "C"][i % 3],
  diem_tb: [8.5, 8.0, 9.25, 8.0, 6.5, 7.75, 9.0, 5.5, 7.25, 6.75, 8.25, 7.0][i],
  chenh_lech: [0.75, 0.25, 1.5, 0.25, -1.25, 0, 1.25, -2.25, -0.5, -1, 0.5, -0.75][i],
  ghi_chu: i % 4 === 0 ? "Tiến bộ rõ rệt trong học kỳ vừa qua" : (i % 4 === 2 ? "" : null),
  noi_tru: i % 2 === 0, so_buoi_vang: [0, 2, 1, 0, 3, 1, 0, 5, 2, 1, 0, 4][i],
}));

const dbEnv = (title, cfg) => env("database.relational_table_query", "database", title, cfg);
const dbFx = (id, kind, title, cfg) => ({
  id, renderer: "database", target: "database.relational_table_query",
  kind, title, envelope: dbEnv(title, cfg),
});

const DB_FIXTURES = [
  dbFx("vrdb1-filter-projection", "canonical", "Lọc điểm ≥8 và chỉ hiện tên, điểm",
    TB(HS_SCHEMA, HS_ROWS, { filter: { op: ">=", column: "diem", value: 8 },
                             projection: ["ten", "diem"] })),
  dbFx("vrdb2-stable-sort-desc", "canonical", "Lọc tổ B rồi sắp xếp điểm giảm dần",
    TB(HS_SCHEMA, HS_ROWS, { filter: { op: "=", column: "to", value: "B" },
                             sort: { column: "diem", direction: "desc" } })),
  dbFx("vrdb3-count-after-filter", "canonical", "Đếm số học sinh tổ A",
    TB(HS_SCHEMA, HS_ROWS, { filter: { op: "=", column: "to", value: "A" },
                             aggregate: { func: "count" } })),
  dbFx("vrdb4-avg-empty-cells", "boundary", "Điểm kiểm tra trung bình (có ô trống)",
    TB(KT_SCHEMA, KT_ROWS, { aggregate: { func: "avg", column: "diem_kt" } })),
  dbFx("vrdb5-combined-pipeline", "canonical", "Lọc → chọn cột → sắp xếp → lấy 3 → trung bình",
    TB(HS_SCHEMA, HS_ROWS, { filter: { op: ">=", column: "diem", value: 7 },
                             projection: ["ten", "to", "diem"],
                             sort: { column: "diem", direction: "desc" }, limit: 3,
                             aggregate: { func: "avg", column: "diem" } })),
  dbFx("vrdb6-boundary-wide", "stress", "Bảng gần biên: 12 dòng × 8 cột, nhãn dài",
    TB(WIDE_SCHEMA, WIDE_ROWS, { filter: { op: ">=", column: "diem_tb", value: 7 },
                                 sort: { column: "chenh_lech", direction: "desc" } })),
];

const FIXTURES = [
  /* ── A. network — RỦI RO CAO NHẤT (từng phantom token → cạnh vô hình) ── */
  {
    id: "graph-bfs-branching", renderer: "network", target: "network.graph_traversal",
    kind: "canonical", title: "BFS — đồ thị phân nhánh",
    envelope: env("network.graph_traversal", "network", "BFS — đồ thị phân nhánh", {
      nodes: ["A", "B", "C", "D", "E", "F"].map((i) => gnode(i)),
      edges: [["A", "B"], ["A", "C"], ["B", "D"], ["B", "E"], ["C", "F"]],
      directed: false, start: "A", goal: null, variant: "bfs", notes: null,
    }),
  },
  {
    id: "graph-dfs-same-topology", renderer: "network", target: "network.graph_traversal",
    kind: "canonical", title: "DFS — CÙNG topology để so sánh",
    envelope: env("network.graph_traversal", "network", "DFS — cùng topology", {
      nodes: ["A", "B", "C", "D", "E", "F"].map((i) => gnode(i)),
      edges: [["A", "B"], ["A", "C"], ["B", "D"], ["B", "E"], ["C", "F"]],
      directed: false, start: "A", goal: null, variant: "dfs", notes: null,
    }),
  },
  {
    id: "graph-cycle", renderer: "network", target: "network.graph_traversal",
    kind: "boundary", title: "Đồ thị có chu trình",
    envelope: env("network.graph_traversal", "network", "Đồ thị có chu trình", {
      nodes: ["A", "B", "C", "D"].map((i) => gnode(i)),
      edges: [["A", "B"], ["B", "C"], ["C", "D"], ["D", "A"], ["A", "C"]],
      directed: false, start: "A", goal: null, variant: "bfs", notes: null,
    }),
  },
  {
    id: "graph-unreachable", renderer: "network", target: "network.graph_traversal",
    kind: "boundary", title: "Đích KHÔNG thể tới (hai phần rời)",
    envelope: env("network.graph_traversal", "network", "Đích không thể tới", {
      nodes: ["A", "B", "X", "Y"].map((i) => gnode(i)),
      edges: [["A", "B"], ["X", "Y"]],
      directed: false, start: "A", goal: "Y", variant: "bfs", notes: null,
    }),
  },
  {
    id: "graph-vietnamese-long-labels", renderer: "network", target: "network.graph_traversal",
    kind: "stress", title: "Nhãn tiếng Việt dài",
    envelope: env("network.graph_traversal", "network", "Mạng trạm quan trắc", {
      nodes: [gnode("A", VN.a), gnode("B", VN.b), gnode("C", VN.c),
              gnode("D", VN.d), gnode("E", VN.e)],
      edges: [["A", "B"], ["A", "C"], ["B", "D"], ["C", "E"]],
      directed: false, start: "A", goal: null, variant: "bfs", notes: null,
    }),
  },
  {
    id: "graph-directed-dense", renderer: "network", target: "network.graph_traversal",
    kind: "stress", title: "Có hướng, nhiều cạnh",
    envelope: env("network.graph_traversal", "network", "Đồ thị có hướng dày", {
      nodes: ["A", "B", "C", "D", "E", "F", "G"].map((i) => gnode(i)),
      edges: [["A", "B"], ["A", "C"], ["A", "D"], ["B", "E"], ["C", "E"],
              ["D", "F"], ["E", "G"], ["F", "G"], ["B", "F"]],
      directed: true, start: "A", goal: null, variant: "dfs", notes: null,
    }),
  },
  {
    id: "routing-canonical", renderer: "network", target: "network.packet_routing",
    kind: "canonical", title: "Định tuyến gói tin",
    envelope: env("network.packet_routing", "network", "Đường đi gói tin", {
      nodes: [{ id: "pc", type: "client" }, { id: "sw", type: "switch" },
              { id: "r1", type: "router" }, { id: "isp", type: "isp" },
              { id: "srv", type: "server" }],
      links: [["pc", "sw"], ["sw", "r1"], ["r1", "isp"], ["isp", "srv"]],
      source: "pc", destination: "srv", notes: null,
    }),
  },
  {
    id: "encap-canonical", renderer: "network", target: "network.protocol_encapsulation",
    kind: "canonical", title: "Đóng gói dữ liệu qua các tầng",
    envelope: env("network.protocol_encapsulation", "network", "Đóng gói PDU", {
      payloadLabel: "Dữ liệu ứng dụng", appProtocol: null, notes: null,
    }),
  },


  /* ── W2B-VR: database.relational_table_query — 10 fixture bắt buộc ── */
  ...DB_FIXTURES,

  /* ── B. tree — regression sau bản sửa nhãn dài ── */
  {
    id: "tree-balanced-short", renderer: "tree", target: "tree.traversal",
    kind: "canonical", title: "Cây cân bằng, nhãn ngắn",
    envelope: env("tree.traversal", "tree", "Duyệt trước — cây cân bằng",
      tree("preorder", "A", [N("A", "B", "C"), N("B", "D", "E"), N("C", "F", "G"),
                             N("D"), N("E"), N("F"), N("G")])),
  },
  {
    id: "tree-single-node", renderer: "tree", target: "tree.traversal",
    kind: "boundary", title: "Cây một nút",
    envelope: env("tree.traversal", "tree", "Cây một nút", tree("preorder", "X", [N("X")])),
  },
  {
    id: "tree-skewed-deep", renderer: "tree", target: "tree.traversal",
    kind: "boundary", title: "Cây lệch sâu",
    envelope: env("tree.traversal", "tree", "Cây lệch trái sâu",
      tree("postorder", "A", [N("A", "B"), N("B", "C"), N("C", "D"), N("D", "E"), N("E")])),
  },
  {
    id: "tree-vietnamese-11-nodes", renderer: "tree", target: "tree.traversal",
    kind: "stress", title: "11 nút, nhãn tiếng Việt dài",
    envelope: env("tree.traversal", "tree", "Mạng lưới trạm — nhãn dài",
      tree("preorder", "hai-dang", [
        { id: "hai-dang", label: "Hải Đăng", left: "suong-mai", right: "hoang-hon" },
        { id: "suong-mai", label: "Sương Mai", left: "thong-xanh", right: "suoi-da" },
        { id: "thong-xanh", label: "Thông Xanh", left: null, right: null },
        { id: "suoi-da", label: "Suối Đá", left: "may-trang", right: null },
        { id: "may-trang", label: "Mây Trắng", left: null, right: "da-vong" },
        { id: "da-vong", label: "Đá Vọng", left: null, right: null },
        { id: "hoang-hon", label: "Hoàng Hôn", left: null, right: "doi-gio" },
        { id: "doi-gio", label: "Đồi Gió", left: "thac-bac", right: "rung-sau" },
        { id: "thac-bac", label: "Thác Bạc", left: null, right: null },
        { id: "rung-sau", label: "Rừng Sâu", left: "trang-khuyet", right: null },
        { id: "trang-khuyet", label: "Trăng Khuyết", left: null, right: null },
      ])),
  },
  {
    id: "tree-levelorder", renderer: "tree", target: "tree.traversal",
    kind: "canonical", title: "Duyệt theo mức (hàng đợi)",
    envelope: env("tree.traversal", "tree", "Duyệt theo mức",
      tree("level_order", "A", [N("A", "B", "C"), N("B", "D", "E"), N("C", "F"),
                                N("D"), N("E"), N("F")])),
  },

  /* ── C. generic — engine authenticity vẫn PARTIAL, KHÔNG được nâng ── */
  {
    id: "generic-reveal-scene", renderer: "generic", target: "generic.rule_scene",
    kind: "canonical", title: "Cảnh hiện dần (biểu diễn khai báo)",
    envelope: env("generic.rule_scene", "generic", "Dựng tam giác ABC từng bước", {
      dsl_version: "1.0", title: "Dựng tam giác ABC từng bước",
      objects: [
        { id: "A", type: "node", label: "A" }, { id: "B", type: "node", label: "B" },
        { id: "C", type: "node", label: "C" },
        { id: "AB", type: "edge", from: "A", to: "B" },
        { id: "AC", type: "edge", from: "A", to: "C" },
        { id: "BC", type: "edge", from: "B", to: "C" },
      ],
      rules: [], interactions: [],
      processes: [{ type: "reveal_sequence", steps: [
        { objects: ["A", "B", "AB"], narration: "Vẽ đoạn AB" },
        { objects: ["C"], narration: "Thêm điểm C" },
        { objects: ["AC", "BC"], narration: "Nối C với A và B" },
      ] }],
    }),
  },
  {
    id: "generic-vietnamese-labels", renderer: "generic", target: "generic.rule_scene",
    kind: "stress", title: "Nhãn tiếng Việt dài trong cảnh generic",
    envelope: env("generic.rule_scene", "generic", "Sơ đồ trạm quan trắc", {
      dsl_version: "1.0", title: "Sơ đồ trạm quan trắc",
      objects: [
        { id: "s1", type: "node", label: VN.a }, { id: "s2", type: "node", label: VN.b },
        { id: "s3", type: "node", label: VN.e },
        { id: "e1", type: "edge", from: "s1", to: "s2" },
        { id: "e2", type: "edge", from: "s2", to: "s3" },
      ],
      rules: [], interactions: [],
      processes: [{ type: "reveal_sequence", steps: [
        { objects: ["s1", "s2", "e1"], narration: "Nối trạm Hải Đăng với trạm Sương Mai" },
        { objects: ["s3", "e2"], narration: "Nối tiếp tới trạm Mây Trắng Đỉnh Trời" },
      ] }],
    }),
  },

  /* ── D. renderer còn lại theo registry ── */
  {
    id: "algorithm-find-max", renderer: "algorithm", target: "algorithm.find_max",
    kind: "canonical", title: "Tìm giá trị lớn nhất",
    envelope: env("algorithm.find_max", "algorithm", "Tìm giá trị lớn nhất", {
      problem: { summary: "Tìm giá trị lớn nhất", input: "Dãy số", output: "Kết quả" },
      algorithm_id: "find_max",
      data: { array: [12, 7, 25, 9, 18], labels: null, target: null, condition: null, order: null },
      data_generated: false, notes: null,
    }),
  },
  {
    id: "algorithm-negative-decimal", renderer: "algorithm", target: "algorithm.find_max",
    kind: "stress", title: "Số âm và thập phân",
    envelope: env("algorithm.find_max", "algorithm", "Nhiệt độ thấp nhất trong tuần", {
      problem: { summary: "Tìm nhiệt độ cao nhất", input: "Dãy nhiệt độ", output: "Kết quả" },
      algorithm_id: "find_max",
      data: { array: [-12.5, -3.25, -40, 7.75, -0.5], labels: null, target: null,
              condition: null, order: null },
      data_generated: false, notes: null,
    }),
  },
  {
    id: "algorithm-binary-search", renderer: "algorithm", target: "algorithm.binary_search",
    kind: "boundary", title: "Tìm kiếm nhị phân (thu hẹp khoảng)",
    envelope: env("algorithm.binary_search", "algorithm", "Tìm kiếm nhị phân", {
      problem: { summary: "Tìm kiếm nhị phân", input: "Dãy số", output: "Kết quả" },
      algorithm_id: "binary_search",
      data: { array: [3, 8, 15, 22, 30, 41, 55], labels: null, target: 30,
              condition: null, order: null },
      data_generated: false, notes: null,
    }),
  },
  {
    id: "algorithm-sort-labels", renderer: "algorithm", target: "algorithm.bubble_sort",
    kind: "stress", title: "Sắp xếp có nhãn tiếng Việt",
    envelope: env("algorithm.bubble_sort", "algorithm", "Sắp xếp điểm các bạn", {
      problem: { summary: "Sắp xếp tăng dần", input: "Dãy điểm", output: "Dãy đã sắp" },
      algorithm_id: "bubble_sort",
      data: { array: [9, 4, 7, 2, 6],
              labels: ["Nguyễn Vân", "Trần Bảo", "Lê Hoàng", "Phạm Chi", "Đỗ Quân"],
              target: null, condition: null, order: "asc" },
      data_generated: false, notes: null,
    }),
  },
  {
    id: "binary-decimal-to-binary", renderer: "binary", target: "binary.decimal_to_binary",
    kind: "canonical", title: "Đổi thập phân sang nhị phân",
    envelope: env("binary.decimal_to_binary", "binary", "Đổi 156 sang nhị phân", {
      decimalValue: 156, bitWidth: 8, notes: null,
    }),
  },
  {
    id: "binary-base-conversion-hex", renderer: "binary", target: "binary.base_conversion",
    kind: "stress", title: "Đổi cơ số tổng quát (giá trị lớn)",
    envelope: env("binary.base_conversion", "binary", "Đổi 2026 sang thập lục phân", {
      sourceBase: 10, targetBase: 16, inputValue: "2026",
      strategy: "quotient_remainder", notes: null,
    }),
  },
  {
    id: "logic-and-gate", renderer: "logic", target: "logic.and_gate",
    kind: "canonical", title: "Một cổng AND (khám phá)",
    envelope: env("logic.and_gate", "logic", "Cổng AND", { inputA: 1, inputB: 1, notes: null }),
  },
  {
    id: "logic-boolean-dag", renderer: "logic", target: "logic.boolean_dag",
    kind: "stress", title: "Mạch nhiều cổng + bảng chân trị",
    envelope: env("logic.boolean_dag", "logic", "Mạch (A AND B) OR NOT C", {
      inputs: [{ id: "A", label: null, value: 1 }, { id: "B", label: null, value: 0 },
               { id: "C", label: null, value: 1 }],
      gates: [{ id: "g1", op: "AND", inputs: ["A", "B"] },
              { id: "g2", op: "NOT", inputs: ["C"] },
              { id: "g3", op: "OR", inputs: ["g1", "g2"] }],
      output: "g3", notes: null,
    }),
  },
];

/* Thông điệp từ chối learner-facing (không phải envelope ok) */
const REFUSALS = [
  {
    id: "vrdb8-missing-table", renderer: "database",
    reason: "Đề chưa cho bảng dữ liệu cụ thể (tên các cột và các dòng dữ liệu). Em hãy chép rõ bảng vào đề — ví dụ: cột Tên, Điểm, Tổ; rồi từng dòng An 8.5 A, Bình 6.0 B… — hệ không tự tạo bảng thay em.",
  },
  {
    id: "vrdb9-join-unsupported", renderer: "database",
    failure_category: "capability_gap",
    reason: "Bài này cần ghép dữ liệu từ nhiều bảng, mà hệ hiện chỉ mô phỏng truy vấn trên MỘT bảng. Em có thể thử một câu hỏi chỉ dùng một bảng: lọc, sắp xếp, hoặc thống kê trên bảng đã cho.",
  },
  {
    id: "vrdb10-two-queries", renderer: "database",
    failure_category: "semantic_incomplete",
    reason: "Đề đang hỏi 2 truy vấn độc lập, nhưng mỗi lần mô phỏng chỉ trình bày được MỘT. Em hãy tách thành từng lần hỏi (giữ nguyên bảng, mỗi lần một yêu cầu) để xem đầy đủ từng bước.",
  },
  {
    id: "refusal-tree-insufficient", renderer: "tree",
    reason: "Đề yêu cầu duyệt cây nhưng chưa cho cấu trúc cây cụ thể (các nút có tên và quan hệ con trái/con phải giữa chúng). Hãy mô tả rõ cây (ví dụ: gốc A, A có con trái B và con phải C…) rồi thử lại — hệ không tự dựng cây thay bạn.",
  },
  {
    id: "refusal-sequence-insufficient", renderer: "algorithm",
    reason: "Đề chưa cho dãy số cụ thể để mô phỏng. Em hãy nêu rõ dãy (ví dụ: 12, 7, 25, 9) rồi thử lại — hệ không tự nghĩ ra số liệu thay em.",
  },
];

/* ══════════════ W4B-1A — BÙ 4 TARGET CHƯA CÓ FIXTURE NÀO ══════════════
 * `offlineCatalog()` của app phủ 13/22 target, bộ fixture stress phủ 13/22
 * (giao nhau), tổng 18/22. Bốn target dưới đây trước nay chỉ được kiểm bằng
 * unit test nên KHÔNG có mẫu nào mở được trong trình duyệt — tức là chúng
 * chưa từng nằm trong bất kỳ bản soát bố cục nào.
 * Config lấy NGUYÊN VĂN shape từ test đang xanh của chính module (không đoán):
 *   scan            → domains/algorithm/scan-module.test.ts
 *   bounded_control_flow → domains/algorithm/program-module.test.tsx
 *   character_encoding   → domains/binary/encoding-module.test.tsx
 *   selection_sort       → cùng khuôn legacy analysis với find_max
 */
const iv = (n) => ({ kind: "int", int_value: n });
const vr = (n) => ({ kind: "var", name: n });
const pval = (left, op, right) => (op === undefined ? { left } : { left, op, right });

const W4B1A_FIXTURES = [
  {
    id: "w4b1a-scan", renderer: "algorithm", target: "algorithm.scan",
    kind: "canonical", title: "Quét dãy tìm ngày vượt ngưỡng",
    envelope: env("algorithm.scan", "algorithm", "Quét dãy tìm ngày vượt ngưỡng", {
      scan_version: "1.0",
      array: [32, 31, 36, 30, 37],
      labels: ["Th 2", "Th 3", "Th 4", "Th 5", "Th 6"],
      seed: { from: "constant", value: 35, varName: "nguong" },
      compare: { kind: "to_constant", op: ">", value: 35 },
      update: { kind: "none" },
      marking: "match_highlight",
      stop: "first_match",
    }),
  },
  {
    id: "w4b1a-selection-sort", renderer: "algorithm", target: "algorithm.selection_sort",
    kind: "canonical", title: "Sắp xếp chọn",
    envelope: env("algorithm.selection_sort", "algorithm", "Sắp xếp chọn", {
      problem: { summary: "Sắp xếp dãy tăng dần bằng thuật toán chọn",
                 input: "Dãy số", output: "Dãy đã sắp xếp" },
      algorithm_id: "selection_sort",
      data: { array: [29, 10, 14, 37, 13], labels: null, target: null,
              condition: null, order: "asc" },
      data_generated: false, notes: null,
    }),
  },
  {
    id: "w4b1a-bounded-loop", renderer: "algorithm", target: "algorithm.bounded_control_flow",
    kind: "canonical", title: "Vòng lặp có điều kiện dừng",
    envelope: env("algorithm.bounded_control_flow", "algorithm", "Vòng lặp có điều kiện dừng", {
      program_version: "program-2.0",
      variables: [{ name: "x", type: "integer", int_value: 1 }],
      statements: [
        { id: "s_body", kind: "assign", target: "x", value: pval(vr("x"), "+", iv(1)) },
        { id: "s_while", kind: "while",
          condition: { atoms: [{ left: pval(vr("x")), op: "<", right: pval(iv(5)) }] },
          body: ["s_body"], max_iterations: 10 },
      ],
      main: ["s_while"],
    }),
  },
  {
    id: "w4b1a-char-encoding", renderer: "binary", target: "binary.character_encoding",
    kind: "canonical", title: "Mã hoá ký tự sang nhị phân",
    envelope: env("binary.character_encoding", "binary", "Mã hoá ký tự sang nhị phân", {
      spec_version: "charenc-1.0", text: "Tin", encoding: "ascii",
    }),
  },
];

FIXTURES.push(...W4B1A_FIXTURES);

export { FIXTURES, REFUSALS, DB_FIXTURES };
