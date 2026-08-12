import type { SimulationEnvelope } from "../simulations/types";

/**
 * Mẫu OFFLINE — envelope dựng sẵn, nạp thẳng qua loadEnvelope, không cần AI.
 * Dùng để chạy/demo ngay. KHÁC với "đề mẫu thử pipeline AI" (SAMPLE_PROMPTS)
 * là văn bản đưa qua analyze→classify→simulate→validate thật (M5 §8).
 */

/**
 * M9-UX2 — phạm vi luận văn: kiến trúc tổng quát, TRẢI NGHIỆM CÔNG KHAI khoanh
 * trong Tin học THPT. Phân loại bằng METADATA TƯỜNG MINH (không lọc tiêu đề):
 * - "public" (mặc định khi không khai): mẫu học đại diện Tin học THPT.
 * - "internal_fixture": chứng minh năng lực generic / parity với module chuyên
 *   biệt — vẫn dùng cho test/dev/regression, KHÔNG quảng bá cho học sinh.
 * (Case "evaluation_only" sống ở backend `evaluation/datasets/` — không ở đây.)
 */
export type SampleVisibility = "public" | "internal_fixture";

export interface OfflineSample {
  id: string;
  envelope: SimulationEnvelope;
  /** Không khai = "public". */
  visibility?: SampleVisibility;
  /** Gợi ý preview tường minh khi simulation_id không tự nói lên (vd generic). */
  preview?: string;
}

export const OFFLINE_SAMPLES: OfflineSample[] = [
  {
    id: "logic-and",
    envelope: {
      status: "ok",
      simulation_id: "logic.and_gate",
      domain: "logic",
      visual_mode: "2d",
      title: "Cổng logic AND",
      description: "Hai đầu vào bật/tắt → một đầu ra",
      config: { inputA: 0, inputB: 0, notes: null },
      notes: null,
    },
  },
  {
    id: "binary-13",
    envelope: {
      status: "ok",
      simulation_id: "binary.decimal_to_binary",
      domain: "binary",
      visual_mode: "2d",
      title: "Đổi 13 sang nhị phân",
      description: "Số thập phân 13 biểu diễn bằng 4 bit",
      config: { decimalValue: 13, bitWidth: 4, notes: null },
      notes: null,
    },
  },
  {
    id: "network-packet",
    envelope: {
      status: "ok",
      simulation_id: "network.packet_routing",
      domain: "network",
      visual_mode: "2d",
      title: "Đường đi của gói tin",
      description: "Gói tin từ máy khách qua router, ISP tới máy chủ",
      config: {
        nodes: [
          { id: "client", type: "client" },
          { id: "router", type: "router" },
          { id: "isp", type: "isp" },
          { id: "server", type: "server" },
        ],
        links: [
          ["client", "router"],
          ["router", "isp"],
          ["isp", "server"],
        ],
        source: "client",
        destination: "server",
        notes: null,
      },
      notes: null,
    },
  },
  {
    // M10 flagship — 3D sư phạm: đóng gói/mở gói TCP/IP. Công khai (Tin học THPT).
    id: "network-encapsulation",
    envelope: {
      status: "ok",
      simulation_id: "network.protocol_encapsulation",
      domain: "network",
      visual_mode: "2d",
      title: "Dữ liệu được đóng gói qua các tầng TCP/IP như thế nào?",
      description: "Đóng gói ở máy gửi, truyền đi, rồi mở gói ở máy nhận",
      config: { payloadLabel: "Dữ liệu ứng dụng", appProtocol: "HTTP", notes: null },
      notes: null,
    },
  },
];

/**
 * Spec DSL generic tái tạo 3 case study M5 (benchmark M6 §6) — dùng làm demo
 * offline VÀ fixture test so hành vi generic ≡ module chuyên biệt.
 */
export const GENERIC_AND_SPEC = {
  dsl_version: "1.0",
  title: "Cổng AND (tổng quát)",
  objects: [
    { id: "a", type: "switch", value: 0, x: 12, y: 28, label: "A" },
    { id: "b", type: "switch", value: 0, x: 12, y: 70, label: "B" },
    { id: "y", type: "lamp", x: 82, y: 49, label: "Đầu ra" },
  ],
  rules: [{ type: "boolean", op: "and", inputs: ["a", "b"], target: "y" }],
  interactions: [
    { type: "toggle", target: "a" },
    { type: "toggle", target: "b" },
  ],
  processes: [],
};

export const GENERIC_BINARY_SPEC = {
  dsl_version: "1.0",
  title: "Đổi 13 sang nhị phân (tổng quát)",
  objects: [
    { id: "bit0", type: "switch", value: 1, x: 14, y: 45, label: "8" },
    { id: "bit1", type: "switch", value: 1, x: 34, y: 45, label: "4" },
    { id: "bit2", type: "switch", value: 0, x: 54, y: 45, label: "2" },
    { id: "bit3", type: "switch", value: 1, x: 74, y: 45, label: "1" },
    { id: "out", type: "value_box", x: 92, y: 45, label: "Thập phân" },
  ],
  rules: [
    { type: "weighted_sum", inputs: ["bit0", "bit1", "bit2", "bit3"], weights: [8, 4, 2, 1], target: "out" },
  ],
  interactions: [
    { type: "toggle", target: "bit0" },
    { type: "toggle", target: "bit1" },
    { type: "toggle", target: "bit2" },
    { type: "toggle", target: "bit3" },
  ],
  processes: [],
};

export const GENERIC_PACKET_SPEC = {
  dsl_version: "1.0",
  title: "Đường đi gói tin (tổng quát)",
  objects: [
    { id: "client", type: "node", node_type: "client", x: 12, y: 50, label: "Máy khách" },
    { id: "router", type: "node", node_type: "router", x: 38, y: 50, label: "Router" },
    { id: "isp", type: "node", node_type: "isp", x: 64, y: 50, label: "ISP" },
    { id: "server", type: "node", node_type: "server", x: 90, y: 50, label: "Máy chủ" },
    { id: "e1", type: "edge", from: "client", to: "router" },
    { id: "e2", type: "edge", from: "router", to: "isp" },
    { id: "e3", type: "edge", from: "isp", to: "server" },
    { id: "pkt", type: "moving_entity", label: "Gói tin" },
  ],
  rules: [],
  interactions: [],
  processes: [{ type: "move_along_path", entity: "pkt", path: ["client", "router", "isp", "server"] }],
};

/**
 * Benchmark PROGRESSIVE (M7.7): dựng tam giác ABC từng bước bằng reveal_sequence.
 * Điểm = node, đoạn = edge. Cảnh HÌNH THÀNH DẦN, không hiện cả tam giác ngay.
 */
export const GENERIC_REVEAL_SPEC = {
  dsl_version: "1.0",
  title: "Dựng tam giác ABC (từng bước)",
  objects: [
    { id: "A", type: "node", x: 22, y: 78, label: "A" },
    { id: "B", type: "node", x: 78, y: 78, label: "B" },
    { id: "C", type: "node", x: 50, y: 20, label: "C" },
    { id: "AB", type: "edge", from: "A", to: "B" },
    { id: "AC", type: "edge", from: "A", to: "C" },
    { id: "BC", type: "edge", from: "B", to: "C" },
  ],
  rules: [],
  interactions: [],
  processes: [
    {
      type: "reveal_sequence",
      steps: [
        { objects: ["A", "B"], narration: "Dựng hai điểm A và B." },
        { objects: ["AB"], narration: "Vẽ đoạn thẳng AB." },
        { objects: ["C"], narration: "Dựng điểm C." },
        { objects: ["AC"], narration: "Vẽ đoạn AC." },
        { objects: ["BC"], narration: "Vẽ đoạn BC — hoàn thành tam giác ABC." },
      ],
    },
  ],
};

/**
 * M7.12: nội dung có CẤU TRÚC (container/heading/paragraph) — hình thành từng bước.
 *
 * W4B-3F — NAY LÀ FIXTURE CỦA ENGINE GENERIC, KHÔNG CÒN LÀ BÀI HỌC CÔNG KHAI.
 * Nó vẫn chứng minh `reveal_sequence` chạy đúng (`generic.test.ts`), nhưng nó
 * thôi được bày cho học sinh dưới tên "Trang giới thiệu": HTML không hình thành
 * theo bước, và dựng nó thành "Bước 1/3" là bịa một trục thời gian. Bài học
 * HTML/CSS thật nay thuộc `web.style_model` (xem mẫu `web-intro-page`).
 */
export const GENERIC_WEB_SPEC = {
  dsl_version: "1.0",
  title: "Trang giới thiệu (từng bước)",
  objects: [
    { id: "page", type: "container", text: "Trang giới thiệu bản thân" },
    { id: "h", type: "heading", text: "Xin chào, tôi là học sinh lớp 11", parent: "page" },
    {
      id: "p",
      type: "paragraph",
      text: "Đây là đoạn văn giới thiệu sở thích của tôi: lập trình, đọc sách và chơi cờ vua.",
      parent: "page",
    },
  ],
  rules: [],
  interactions: [],
  processes: [
    {
      type: "reveal_sequence",
      steps: [
        { objects: ["page"], narration: "Tạo khung trang." },
        { objects: ["h"], narration: "Thêm tiêu đề trang." },
        { objects: ["p"], narration: "Thêm đoạn văn giới thiệu." },
      ],
    },
  ],
};

/**
 * W4B-3F — MẪU CÔNG KHAI THẬT của `generic.rule_scene`.
 *
 * Trước wave này bài generic duy nhất bày cho học sinh là "Trang giới thiệu
 * (từng bước)" — một `reveal_sequence` bịa trục thời gian cho HTML. Gỡ nó đi
 * thì target mất mẫu công khai, và guard `library_discoverable ⟹ có mẫu` đỏ
 * ĐÚNG: một năng lực bày trong Thư viện mà không có gì để mở là một lời hứa
 * suông.
 *
 * Thay bằng thứ generic LÀM ĐƯỢC THẬT: quy tắc hợp thành. Học sinh gạt các điều
 * kiện, engine tất định tính lại kết luận — không bước giả, không trục thời
 * gian. Đúng đơn vị `access_control` (T10 B9 · T11 B15) và cùng cơ chế
 * `boolean_composition` mà catalog đã khai.
 */
export const GENERIC_RULE_SPEC = {
  dsl_version: "1.0",
  title: "Quy tắc mượn sách thư viện",
  objects: [
    { id: "the", type: "switch", value: 1, x: 12, y: 24, label: "Có thẻ thư viện" },
    { id: "no_qua_han", type: "switch", value: 0, x: 12, y: 52, label: "Đang nợ sách quá hạn" },
    { id: "khong_no", type: "lamp", x: 44, y: 52, label: "Không nợ sách" },
    { id: "duoc_muon", type: "lamp", x: 84, y: 38, label: "Được mượn sách" },
  ],
  rules: [
    { type: "boolean", op: "not", inputs: ["no_qua_han"], target: "khong_no" },
    { type: "boolean", op: "and", inputs: ["the", "khong_no"], target: "duoc_muon" },
  ],
  interactions: [
    { type: "toggle", target: "the" },
    { type: "toggle", target: "no_qua_han" },
  ],
  processes: [],
};

function genericEnvelope(title: string, spec: object): SimulationEnvelope {
  return {
    status: "ok",
    simulation_id: "generic.rule_scene",
    domain: "generic",
    visual_mode: "2d",
    title,
    description: "Do engine tổng quát dựng từ SimulationSpec (DSL v1)",
    config: spec,
    notes: null,
  };
}

/* W4B-2Z — HAI bài CSS dùng CHUNG cơ chế `web.style_model`, khác nhau CHỈ ở
   config đã validate. Đây là bằng chứng tái dụng: "đổi màu nền" và "trang trí
   thẻ" KHÔNG đẻ hai renderer. */
OFFLINE_SAMPLES.push(
  {
    id: "web-style-basic",
    envelope: {
      status: "ok", simulation_id: "web.style_model", domain: "web",
      visual_mode: "2d", title: "Đổi màu nền và cỡ chữ (CSS)",
      description: "Chỉnh thuộc tính, khối bên phải đổi ngay",
      config: {
        heading: "Xin chào, đây là trang của em!",
        paragraph: "Đổi thuộc tính bên trái để xem khung, tiêu đề và đoạn văn đổi theo.",
        style: {
          backgroundColor: "#bfdbfe", color: "#1f2937",
          headingColor: "#1f2937", headingSize: 28,
          fontSize: 20, padding: 16, borderRadius: 8,
        },
        notes: null,
      },
      notes: null,
    },
  },
  {
    id: "web-style-card",
    envelope: {
      status: "ok", simulation_id: "web.style_model", domain: "web",
      visual_mode: "2d", title: "Trang trí thẻ giới thiệu (CSS)",
      description: "Cùng cơ chế, khác dữ liệu đã kiểm định",
      config: {
        heading: "Nguyễn Văn A — Lớp 11A1",
        paragraph: "Sở thích: lập trình, đọc sách và chơi cờ vua.",
        style: {
          backgroundColor: "#fde68a", color: "#1f2937",
          headingColor: "#b91c1c", headingSize: 32,
          fontSize: 18, padding: 24, borderRadius: 20,
        },
        notes: null,
      },
      notes: null,
    },
  },
);

OFFLINE_SAMPLES.push(
  // Ba bản "(tổng quát)" là FIXTURE PARITY: chứng minh generic engine tái tạo
  // được hành vi module chuyên biệt — giá trị cho test/dev, trùng lặp và gây
  // nhiễu với học sinh (đã có bản chuyên biệt ở trên) → internal.
  {
    id: "gen-and",
    envelope: genericEnvelope("Cổng AND (tổng quát)", GENERIC_AND_SPEC),
    visibility: "internal_fixture",
  },
  {
    id: "gen-binary",
    envelope: genericEnvelope("Đổi 13 → nhị phân (tổng quát)", GENERIC_BINARY_SPEC),
    visibility: "internal_fixture",
  },
  {
    id: "gen-rule-library",
    envelope: genericEnvelope("Quy tắc mượn sách thư viện", GENERIC_RULE_SPEC),
    preview: "generic-rules",
  },
  {
    id: "gen-packet",
    envelope: genericEnvelope("Gói tin (tổng quát)", GENERIC_PACKET_SPEC),
    visibility: "internal_fixture",
  },
  // Tam giác = ví dụ LIÊN MIỀN (toán) có trước khi phạm vi luận văn khoanh về
  // Tin học THPT — giữ làm fixture reveal/node-edge, không quảng bá cho học sinh.
  {
    id: "gen-reveal",
    envelope: genericEnvelope("Dựng tam giác ABC (từng bước)", GENERIC_REVEAL_SPEC),
    visibility: "internal_fixture",
  },
  /* W4B-3F — "Trang giới thiệu" RỜI KHỎI `generic.rule_scene`.
   *
   * Bài này từng là một `reveal_sequence` ba bước: hiện khung → hiện tiêu đề →
   * hiện đoạn văn. Đó là một TRỤC THỜI GIAN BỊA RA — HTML không "chạy" theo
   * bước, và W4B-2Z đã gỡ đúng lỗi đó cho phần CSS rồi để lại phần cấu trúc.
   * Hệ quả đo được: sân khấu 1622px chỉ lấp 37% bề ngang bằng MỘT ô ở bước 1.
   *
   * Chủ sở hữu đúng là `web.style_model` — nay nó mô hình hoá một TRANG (khung
   * + h1 + p), nên cùng nội dung ấy thành thao tác thật: đổi thuộc tính, xem
   * trang đổi ngay, đọc được bộ chọn nào ảnh hưởng phần nào. */
  {
    id: "web-intro-page",
    envelope: {
      status: "ok", simulation_id: "web.style_model", domain: "web",
      visual_mode: "2d", title: "Trang giới thiệu bản thân (HTML/CSS)",
      description: "Khung trang, tiêu đề, đoạn văn — đổi thuộc tính, xem đổi ngay",
      config: {
        heading: "Xin chào, tôi là học sinh lớp 11",
        paragraph: "Đây là đoạn văn giới thiệu sở thích của tôi: lập trình, đọc sách và chơi cờ vua.",
        style: {
          backgroundColor: "#ffffff", color: "#1f2937",
          headingColor: "#1d4ed8", headingSize: 32,
          fontSize: 18, padding: 32, borderRadius: 12,
        },
        notes: null,
      },
      notes: null,
    },
    preview: "web-structure",
  },
);

/* ── W4B-3D — MẪU CHO CHÍN TARGET CÒN THIẾU BẰNG CHỨNG TRÌNH DUYỆT ────────
 *
 * Trước wave này, 14/23 target có mẫu offline. Chín target còn lại
 * `ai_reachable_public` (học sinh CÓ THỂ tới được bằng đề bài) nhưng không có
 * mẫu nào, nên **không lượt đo trình duyệt nào từng chạm chúng** — engine và
 * validator đã khoá kĩ, còn phần học sinh NHÌN THẤY thì chưa ai đo.
 *
 * Config ở đây KHÔNG bịa: lấy đúng những cấu hình đã được `validateConfig`
 * THẬT chấp nhận trong `authenticity-cross-lock.test.ts`, nên mẫu và
 * cross-lock không thể trôi khỏi nhau.
 *
 * NGỮ CẢNH khác nhau là CỐ Ý (§11): cùng một cơ chế, dữ liệu đời sống khác —
 * điểm số, nhiệt độ, giá tiền. Đó là bằng chứng tái dụng. Nó **chỉ là dữ liệu**:
 * không renderer nào được rẽ nhánh theo ngữ cảnh (khoá ở `spec-reuse.test.tsx`).
 *
 * VISIBILITY giữ đúng sự thật sản phẩm: những bài là nội dung Tin học THPT thì
 * `public`; `algorithm.scan` là bề mặt TỔNG QUÁT bắt các đề ngoài tám bài
 * chuyên biệt — đưa nó vào Thư viện học sinh sẽ trùng nghĩa với chính tám bài
 * ấy, nên nó là `internal_fixture`: có bằng chứng, không quảng bá.
 */
OFFLINE_SAMPLES.push(
  {
    id: "algo-selection-sort",
    envelope: {
      status: "ok",
      simulation_id: "algorithm.selection_sort",
      domain: "algorithm",
      visual_mode: "2d",
      title: "Xếp hạng 5 vận động viên theo thời gian chạy",
      description: "Mỗi lượt chọn thời gian nhỏ nhất còn lại rồi đưa lên đầu",
      config: {
        problem: {
          summary: "Xếp hạng 5 vận động viên theo thời gian chạy",
          input: "Thời gian chạy (giây) của 5 vận động viên",
          output: "Danh sách đã xếp từ nhanh đến chậm",
        },
        data: { array: [9, 4, 7, 2, 6], order: "asc" },
        notes: null,
      },
      notes: null,
    },
  },
  {
    id: "algo-scan-first-hot-day",
    envelope: {
      status: "ok",
      simulation_id: "algorithm.scan",
      domain: "algorithm",
      visual_mode: "2d",
      title: "Ngày đầu tiên nhiệt độ vượt 4 độ so với trung bình",
      description: "Quét một lượt, dừng ngay ở phần tử đầu tiên thoả điều kiện",
      config: {
        scan_version: "1.0",
        array: [3, 6, 2, 8, 5],
        seed: { from: "constant", value: 4, varName: "nguong" },
        compare: { kind: "to_constant", op: ">", value: 4 },
        update: { kind: "none" },
        marking: "match_highlight",
        stop: "first_match",
      },
      notes: null,
    },
    visibility: "internal_fixture",
  },
  {
    id: "algo-bounded-control-flow",
    envelope: {
      status: "ok",
      simulation_id: "algorithm.bounded_control_flow",
      domain: "algorithm",
      visual_mode: "2d",
      title: "Cộng dồn 3 cho tới khi vượt 14",
      description: "Gán, lặp CÓ BIÊN và điều kiện — từng bước, biến hiện rõ",
      /* Config lấy NGUYÊN VĂN từ `program-normalized-envelope.json` — artifact
         do CHÍNH `validate_program_config` của backend sinh ra. Dạng chuẩn hoá
         của `program-2.0` (biểu thức tách thành bảng có id, thân lệnh tham
         chiếu theo id) không phải thứ nên chép tay: bản viết tay đầu tiên đã bị
         validator từ chối ngay. */
      config: {
              "program_version": "program-2.0",
              "variables": [
                      {
                              "name": "x",
                              "type": "integer",
                              "int_value": 2,
                              "bool_value": null,
                              "initialized": true
                      }
              ],
              "expressions": [
                      {
                              "id": "_e1",
                              "kind": "var",
                              "name": "x"
                      },
                      {
                              "id": "_e2",
                              "kind": "int",
                              "int_value": 14
                      },
                      {
                              "id": "_e3",
                              "kind": "compare",
                              "op": "<=",
                              "left": "_e1",
                              "right": "_e2"
                      },
                      {
                              "id": "_e4",
                              "kind": "int",
                              "int_value": 3
                      },
                      {
                              "id": "_e5",
                              "kind": "binary",
                              "op": "+",
                              "left": "_e1",
                              "right": "_e4"
                      }
              ],
              "statements": [
                      {
                              "id": "s_while",
                              "kind": "while",
                              "target": null,
                              "value": null,
                              "condition": "_e3",
                              "then_body": [],
                              "else_body": [],
                              "body": [
                                      "s_body"
                              ],
                              "max_iterations": 10
                      },
                      {
                              "id": "s_body",
                              "kind": "assign",
                              "target": "x",
                              "value": "_e5",
                              "condition": null,
                              "then_body": [],
                              "else_body": [],
                              "body": [],
                              "max_iterations": null
                      }
              ],
              "main": [
                      "s_while"
              ]
      },
      notes: null,
    },
  },
  {
    id: "binary-base-conversion",
    envelope: {
      status: "ok",
      simulation_id: "binary.base_conversion",
      domain: "binary",
      visual_mode: "2d",
      title: "Đổi năm 2026 sang hệ thập lục phân",
      description: "Chia lấy dư liên tiếp — từng bước một",
      config: { sourceBase: 10, targetBase: 16, inputValue: "2026", notes: null },
      notes: null,
    },
  },
  {
    id: "binary-character-encoding",
    envelope: {
      status: "ok",
      simulation_id: "binary.character_encoding",
      domain: "binary",
      visual_mode: "2d",
      title: "Chữ \"Tin\" được máy tính lưu thành các bit nào",
      description: "Ký tự → mã → nhị phân, từng ký tự một",
      config: { text: "Tin", encoding: "ascii", notes: null },
      notes: null,
    },
  },
  {
    id: "logic-boolean-dag",
    envelope: {
      status: "ok",
      simulation_id: "logic.boolean_dag",
      domain: "logic",
      visual_mode: "2d",
      title: "Cửa tự động: mở khi ĐÚNG MỘT trong hai cảm biến báo",
      description: "Mạch XOR hai đầu vào kèm bảng chân trị đầy đủ",
      config: {
        inputs: [
          { id: "A", value: 1 },
          { id: "B", value: 0 },
        ],
        gates: [{ id: "g", op: "XOR", inputs: ["A", "B"] }],
        output: "g",
        notes: null,
      },
      notes: null,
    },
  },
  {
    id: "network-graph-traversal",
    envelope: {
      status: "ok",
      simulation_id: "network.graph_traversal",
      domain: "network",
      visual_mode: "2d",
      title: "Tìm đường ít chặng nhất giữa hai điểm trong mạng lưới",
      description: "Duyệt theo chiều rộng (BFS), có đường đi và thứ tự thăm",
      config: {
        nodes: [{ id: "A" }, { id: "B" }, { id: "C" }, { id: "D" }, { id: "E" }],
        edges: [["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"], ["D", "E"]],
        directed: false,
        start: "A",
        goal: "E",
        variant: "bfs",
        notes: null,
      },
      notes: null,
    },
  },
  {
    id: "db-table-query",
    envelope: {
      status: "ok",
      simulation_id: "database.relational_table_query",
      domain: "database",
      visual_mode: "2d",
      title: "Lọc học sinh có điểm từ 8 trở lên rồi sắp theo điểm",
      description: "Lọc — chọn cột — sắp xếp, mỗi dòng được xét một lần",
      config: {
        specVersion: "table-1.0",
        schema: [
          { name: "ten", type: "text", label: "Họ tên" },
          { name: "diem", type: "number", label: "Điểm" },
          { name: "to", type: "number", label: "Tổ" },
        ],
        rows: [
          { ten: "An", diem: 7.5, to: 1 },
          { ten: "Bình", diem: 9, to: 2 },
          { ten: "Chi", diem: 6.5, to: 1 },
          { ten: "Dũng", diem: 8, to: 2 },
          { ten: "Em", diem: 8.5, to: 1 },
        ],
        filter: { kind: "compare", column: "diem", op: ">=", value: 8 },
        projection: ["ten", "diem"],
        sort: { column: "diem", direction: "desc" },
        limit: null,
        aggregate: null,
        normalizations: [],
        notes: null,
      },
      notes: null,
    },
  },
  {
    id: "tree-traversal-preorder",
    envelope: {
      status: "ok",
      simulation_id: "tree.traversal",
      domain: "tree",
      visual_mode: "2d",
      title: "Duyệt cây thư mục theo thứ tự trước",
      description: "Thăm gốc rồi nhánh trái, nhánh phải — ngăn xếp hiện rõ",
      config: {
        specVersion: "tree-1.0",
        variant: "preorder",
        rootId: "A",
        nodes: [
          { id: "A", label: "Gốc", left: "B", right: "C" },
          { id: "B", label: "Tài liệu", left: "D", right: "E" },
          { id: "C", label: "Hình ảnh", left: "F", right: "G" },
          { id: "D", label: "Bài tập", left: null, right: null },
          { id: "E", label: "Đề thi", left: null, right: null },
          { id: "F", label: "Ảnh lớp", left: null, right: null },
          { id: "G", label: "Ảnh sân trường", left: null, right: null },
        ],
        notes: null,
      },
      notes: null,
    },
  },
);

/** Đề mẫu để THỬ pipeline AI (§8) — điền vào ô nhập rồi bấm Phân tích. */
/**
 * Đề mẫu để THỬ PIPELINE AI thật (analyze→classify→simulate→validate) — khác với
 * OFFLINE_SAMPLES (envelope dựng sẵn, chạy ngay, 0 gọi AI).
 * M9-UX4: hiện thành chip dưới ô nhập ở Trang chủ; bấm chip chỉ ĐIỀN SẴN đề vào ô,
 * học sinh vẫn phải tự bấm gửi — không lén tiêu một lượt gọi AI.
 * Nhãn giữ tiếng Việt thuần: không lộ tên domain kĩ thuật (logic/binary/network).
 */
export const SAMPLE_PROMPTS: { id: string; label: string; text: string }[] = [
  { id: "p-logic", label: "Cổng logic AND", text: "Khi nào cổng AND có đầu ra bằng 1?" },
  {
    id: "p-binary",
    label: "Số 13 sang nhị phân",
    text: "Số 13 được biểu diễn dưới dạng nhị phân như thế nào?",
  },
  {
    id: "p-network",
    label: "Đường đi của gói tin",
    text: "Minh họa đường đi của một gói tin từ máy tính đến máy chủ.",
  },
];
