import type { NodeType } from "./model";

/**
 * W4B-2S — HÌNH DẠNG CHỞ VAI TRÒ, CHỮ CHỈ XÁC NHẬN.
 *
 * VẤN ĐỀ ĐO ĐƯỢC (không phải cảm nhận): `packet_routing` vẽ cả năm vai trò miền
 * bằng **cùng một hình tròn**, chỉ khác màu viền + nhãn chữ. Học sinh đọc ra
 * "bốn vòng tròn nối bằng đường kẻ" chứ không phải "máy → router → nhà mạng →
 * máy chủ". Đây là `DOMAIN_ROLE_CARRIED_BY_TEXT`.
 *
 * Đây là target DUY NHẤT trong 22 mắc lỗi này (audit W4B-2S): mảng/cây/đồ thị
 * dùng hình trừu tượng là ĐÚNG (giá trị và đỉnh vốn trừu tượng), logic đã có
 * hình cổng, database đã dùng `<table>` thật, encapsulation đã có tầng/phong bì.
 * Nên đây KHÔNG phải "framework icon cho mọi domain" — nó là từ vựng hình của
 * MỘT miền mà vai trò vốn mang nghĩa vật lý.
 *
 * ── SỞ HỮU ──────────────────────────────────────────────────────────────────
 *   engine state (`NetNode.type`)  →  VAI TRÒ NGỮ NGHĨA  →  hình học trình bày
 *
 * Khoá theo `NodeType` — kiểu do ENGINE sở hữu, đã qua validate. KHÔNG bao giờ
 * suy từ nhãn/tiêu đề/đề bài (`if (label.includes("router"))` là anti-pattern #2
 * và có guard riêng). Hàm THUẦN, không React, không màu: màu là chuyện của
 * renderer, hình là chuyện của vai trò.
 *
 * VẼ THỦ CÔNG, KHÔNG ASSET. Không tải mesh/texture/thư viện icon: §4 đòi NHẬN
 * RA ĐƯỢC chứ không đòi giống thật, và một `path` vài trăm byte đủ để phân biệt
 * laptop với tủ máy chủ ở cỡ 60px.
 */

/** Hình vẽ trong hộp chuẩn 48×48 — renderer tự co giãn và đặt vị trí. */
export interface NodeGlyph {
  /** Nét vẽ ngoài (fill: nền nhạt của vai trò). */
  outline: string;
  /** Nét chi tiết bên trong (stroke, không fill) — khe cắm, ăng-ten, cổng… */
  details: string[];
  /** Tên vai trò để đặt `aria-label`/`<title>`; KHÔNG thay thế hình. */
  role: string;
}

export const GLYPH_BOX = 48;

const GLYPHS: Record<NodeType, NodeGlyph> = {
  // Máy khách — màn hình + đế, dáng laptop.
  client: {
    outline: "M9 11 h30 v20 h-30 z",
    details: ["M5 31 h38 l3 6 h-44 z", "M20 34 h8"],
    role: "Máy khách",
  },
  // Router — hộp thiết bị dẹt + hai ăng-ten chéo.
  router: {
    outline: "M6 26 h36 v12 h-36 z",
    details: ["M15 26 L10 13", "M33 26 L38 13", "M13 32 h6", "M29 32 h6"],
    role: "Router",
  },
  // Máy chủ — tủ rack đứng, ba khe.
  server: {
    outline: "M13 6 h22 v36 h-22 z",
    details: ["M17 13 h14", "M17 21 h14", "M17 29 h14", "M31 35 h2"],
    role: "Máy chủ",
  },
  // Switch — hộp dẹt nhiều cổng.
  switch: {
    outline: "M5 19 h38 v12 h-38 z",
    details: ["M11 31 v5", "M18 31 v5", "M25 31 v5", "M32 31 v5"],
    role: "Switch",
  },
  // ISP — vùng mạng/nhà cung cấp: đám mây, KHÔNG phải một thiết bị nữa.
  isp: {
    outline: "M13 36 a9 9 0 0 1 1-17 a11 11 0 0 1 20 2 a8 8 0 0 1 1 15 z",
    details: [],
    role: "Nhà mạng",
  },
};

export function nodeGlyph(type: NodeType): NodeGlyph {
  return GLYPHS[type];
}

/**
 * VAI TRÒ TRONG PHIÊN TRUYỀN — nguồn/đích, tách khỏi LOẠI THIẾT BỊ.
 *
 * §14 đòi đích phải phân biệt được mà không phải đọc chữ. Loại thiết bị không đủ:
 * một mạng có thể có hai máy chủ, hoặc gửi từ máy chủ này sang máy chủ khác.
 * Nên nguồn/đích là **vai trò thứ hai**, vẽ bằng dấu hiệu riêng chồng lên hình
 * thiết bị — hai kênh độc lập, đúng luật "màu không bao giờ là tín hiệu duy nhất".
 */
export type EndpointRole = "source" | "destination" | null;

export function endpointRoleOf(
  nodeId: string,
  source: string,
  destination: string,
): EndpointRole {
  if (nodeId === source) return "source";
  if (nodeId === destination) return "destination";
  return null;
}
