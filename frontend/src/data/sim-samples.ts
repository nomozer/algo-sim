import type { SimulationEnvelope } from "../simulations/types";

/**
 * Mẫu OFFLINE — envelope dựng sẵn, nạp thẳng qua loadEnvelope, không cần AI.
 * Dùng để chạy/demo ngay. KHÁC với "đề mẫu thử pipeline AI" (SAMPLE_PROMPTS)
 * là văn bản đưa qua analyze→classify→simulate→validate thật (M5 §8).
 */

export interface OfflineSample {
  id: string;
  envelope: SimulationEnvelope;
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
    { id: "bit0", type: "switch", value: 1, weight: 8, x: 14, y: 45, label: "8" },
    { id: "bit1", type: "switch", value: 1, weight: 4, x: 34, y: 45, label: "4" },
    { id: "bit2", type: "switch", value: 0, weight: 2, x: 54, y: 45, label: "2" },
    { id: "bit3", type: "switch", value: 1, weight: 1, x: 74, y: 45, label: "1" },
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

/** M7.12: nội dung có CẤU TRÚC (container/heading/paragraph) — hình thành từng bước. */
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

OFFLINE_SAMPLES.push(
  { id: "gen-and", envelope: genericEnvelope("Cổng AND (tổng quát)", GENERIC_AND_SPEC) },
  { id: "gen-binary", envelope: genericEnvelope("Đổi 13 → nhị phân (tổng quát)", GENERIC_BINARY_SPEC) },
  { id: "gen-packet", envelope: genericEnvelope("Gói tin (tổng quát)", GENERIC_PACKET_SPEC) },
  { id: "gen-reveal", envelope: genericEnvelope("Dựng tam giác ABC (từng bước)", GENERIC_REVEAL_SPEC) },
  { id: "gen-web", envelope: genericEnvelope("Trang giới thiệu (từng bước)", GENERIC_WEB_SPEC) },
);

/** Đề mẫu để THỬ pipeline AI (§8) — điền vào ô nhập rồi bấm Phân tích. */
export const SAMPLE_PROMPTS: { id: string; label: string; text: string }[] = [
  { id: "p-logic", label: "Cổng AND (logic)", text: "Khi nào cổng AND có đầu ra bằng 1?" },
  {
    id: "p-binary",
    label: "Số 13 nhị phân (binary)",
    text: "Số 13 được biểu diễn dưới dạng nhị phân như thế nào?",
  },
  {
    id: "p-network",
    label: "Gói tin (network)",
    text: "Minh họa đường đi của một gói tin từ máy tính đến máy chủ.",
  },
];
