/**
 * Model: đóng gói/mở gói dữ liệu qua các tầng TCP/IP (M10). Progressive: có timeline.
 *
 * State RENDERER-NEUTRAL (M7.FREEZE): không toạ độ/camera/mesh. PDU là danh sách
 * PHÂN ĐOẠN CÓ THỨ TỰ — thứ tự là sự thật ngữ nghĩa duy nhất; renderer 2D/3D tự
 * đặt chỗ. Đây là bằng chứng: cùng state → 2D hoặc 3D, không fork engine.
 *
 * Đây là MÔ HÌNH SƯ PHẠM của đóng gói, không phải bộ mô phỏng chồng giao thức
 * đầy đủ: một transport (TCP), không bắt tay/seq/ack, không phân mảnh.
 */

export type LayerId = "application" | "transport" | "internet" | "network_access";

/** Thứ tự tầng trên → dưới (đóng gói đi xuống, mở gói đi lên). */
export const LAYERS: LayerId[] = ["application", "transport", "internet", "network_access"];

export const LAYER_LABEL: Record<LayerId, string> = {
  application: "Tầng Ứng dụng",
  transport: "Tầng Giao vận",
  internet: "Tầng Liên mạng",
  network_access: "Tầng Truy cập mạng",
};

export type PduRole = "payload" | "header" | "trailer";

export interface PduComponent {
  id: string; // "data" | "tcp" | "ip" | "link" | "fcs"
  label: string;
  role: PduRole;
  layer: LayerId; // tầng đã thêm thành phần này (để tô màu/quy nghĩa)
}

export type Phase =
  | "sender_application"
  | "sender_encapsulation"
  | "transmission"
  | "receiver_decapsulation"
  | "completed";

export type Side = "sender" | "medium" | "receiver";

/**
 * Delta TƯỜNG MINH của một bước (thay cho changed/changeKind đơn lẻ): hỗ trợ
 * NHIỀU thành phần đổi trong MỘT bước ngữ nghĩa — Network Access thêm/gỡ LINK
 * và FCS NGUYÊN TỬ (bất biến #4).
 */
export interface StepDelta {
  kind: "add" | "remove" | "transmit" | "deliver";
  layer: LayerId | null; // null chỉ khi truyền tin thuần
  componentIds: string[]; // vd ["link","fcs"]
}

export interface EncapStep {
  phase: Phase;
  side: Side;
  activeLayer: LayerId | null;
  pdu: PduComponent[]; // PDU SAU bước này
  delta: StepDelta;
  narration: string;
}

export interface EncapConfig {
  payloadLabel: string;
  /** CHỈ để hiển thị ngữ cảnh (vd "HTTP") — KHÔNG mô hình hoá thành PDU. */
  appProtocol: string | null;
  notes: string | null;
}

export interface EncapState {
  payloadLabel: string;
  appProtocol: string | null;
  layers: LayerId[];
  steps: EncapStep[];
  cursor: number;
}

/** "Mảnh thông tin giao thức" cho nhịp dự đoán — LINK+FCS là MỘT mảnh gộp. */
export interface ProtocolPiece {
  id: string; // "tcp" | "ip" | "link+fcs"
  label: string;
  componentIds: string[];
}

export const PROTOCOL_PIECES: ProtocolPiece[] = [
  { id: "tcp", label: "Phần đầu TCP", componentIds: ["tcp"] },
  { id: "ip", label: "Phần đầu IP", componentIds: ["ip"] },
  { id: "link+fcs", label: "Phần đầu LINK + phần đuôi FCS", componentIds: ["link", "fcs"] },
];

function comp(id: string, label: string, role: PduRole, layer: LayerId): PduComponent {
  return { id, label, role, layer };
}

const TCP = comp("tcp", "TCP", "header", "transport");
const IP = comp("ip", "IP", "header", "internet");
const LINK = comp("link", "LINK", "header", "network_access");
const FCS = comp("fcs", "FCS", "trailer", "network_access");

/** Dựng toàn bộ timeline 9 bước — tất định (bất biến #2). */
export function buildEncapState(config: EncapConfig): EncapState {
  const data = comp("data", config.payloadLabel, "payload", "application");
  const pApp = [data];
  const pTcp = [TCP, data];
  const pIp = [IP, TCP, data];
  const pFrame = [LINK, IP, TCP, data, FCS];

  const steps: EncapStep[] = [
    { phase: "sender_application", side: "sender", activeLayer: "application", pdu: pApp,
      delta: { kind: "add", layer: "application", componentIds: ["data"] },
      narration: "Máy gửi: ứng dụng tạo dữ liệu cần gửi đi." },
    { phase: "sender_encapsulation", side: "sender", activeLayer: "transport", pdu: pTcp,
      delta: { kind: "add", layer: "transport", componentIds: ["tcp"] },
      narration: "Tầng Giao vận thêm phần đầu TCP → dữ liệu trở thành đoạn TCP." },
    { phase: "sender_encapsulation", side: "sender", activeLayer: "internet", pdu: pIp,
      delta: { kind: "add", layer: "internet", componentIds: ["ip"] },
      narration: "Tầng Liên mạng thêm phần đầu IP → đoạn TCP trở thành gói IP." },
    { phase: "sender_encapsulation", side: "sender", activeLayer: "network_access", pdu: pFrame,
      delta: { kind: "add", layer: "network_access", componentIds: ["link", "fcs"] },
      narration: "Tầng Truy cập mạng thêm phần đầu LINK và phần đuôi FCS → gói IP trở thành khung." },
    { phase: "transmission", side: "medium", activeLayer: null, pdu: pFrame,
      delta: { kind: "transmit", layer: null, componentIds: [] },
      narration: "Khung được truyền qua đường truyền tới máy nhận — nội dung không đổi." },
    { phase: "receiver_decapsulation", side: "receiver", activeLayer: "network_access", pdu: pIp,
      delta: { kind: "remove", layer: "network_access", componentIds: ["link", "fcs"] },
      narration: "Máy nhận: tầng Truy cập mạng gỡ phần đầu LINK và phần đuôi FCS → còn lại gói IP." },
    { phase: "receiver_decapsulation", side: "receiver", activeLayer: "internet", pdu: pTcp,
      delta: { kind: "remove", layer: "internet", componentIds: ["ip"] },
      narration: "Tầng Liên mạng gỡ phần đầu IP → còn lại đoạn TCP." },
    { phase: "receiver_decapsulation", side: "receiver", activeLayer: "transport", pdu: pApp,
      delta: { kind: "remove", layer: "transport", componentIds: ["tcp"] },
      narration: "Tầng Giao vận gỡ phần đầu TCP → còn lại dữ liệu ứng dụng." },
    { phase: "completed", side: "receiver", activeLayer: "application", pdu: pApp,
      delta: { kind: "deliver", layer: "application", componentIds: ["data"] },
      narration: "Ứng dụng ở máy nhận nhận đúng dữ liệu ban đầu. Hoàn tất!" },
  ];

  return { payloadLabel: config.payloadLabel, appProtocol: config.appProtocol, layers: LAYERS, steps, cursor: 0 };
}

export function currentStep(state: EncapState): EncapStep {
  return state.steps[Math.max(0, Math.min(state.cursor, state.steps.length - 1))];
}

/** Mảnh giao thức khớp một tập componentIds (so khớp theo TẬP HỢP, không theo thứ tự). */
export function pieceForComponents(componentIds: string[]): ProtocolPiece | undefined {
  const key = [...componentIds].sort().join(",");
  return PROTOCOL_PIECES.find((p) => [...p.componentIds].sort().join(",") === key);
}
