/**
 * header-identity.ts — DẢI NHẬN DIỆN Ở ĐẦU THẺ MÔ PHỎNG (nhãn miền · phụ đề).
 *
 * ─── SỞ HỮU ────────────────────────────────────────────────────────────────
 *
 * Ba dòng đầu mỗi thẻ mô phỏng — NHÃN MIỀN, TIÊU ĐỀ ĐỀ BÀI, PHỤ ĐỀ CƠ CHẾ — là
 * thứ học sinh đọc trước tiên và là thứ phải GIỐNG NHAU ở cả 24 target. File này
 * sở hữu hai trong ba dòng đó (dòng giữa là `envelope.title`, thuộc về đề bài).
 *
 * ─── VÌ SAO TÁCH RA KHỎI `SimulationWorkspace.tsx` ─────────────────────────
 *
 * Vì luật phải kiểm được bằng HÀM THUẦN. Chừng nào phép quyết định còn nằm lẫn
 * trong JSX thì muốn khoá nó phải dựng DOM cho từng target — đắt tới mức không
 * ai chạy, nên rốt cuộc không có gì khoá cả và mỗi miền lại tự nghĩ ra một kiểu.
 *
 * ─── HAI LỚP LỖI ĐÃ ĐO ĐƯỢC (W5Z, quét cả 24 target) ──────────────────────
 *
 *   1. NHÃN MIỀN THIẾU ⇒ RÒ ĐỊNH DANH KỸ THUẬT. Bảng cũ khai
 *      `Record<string, string>` kèm fallback `domain.toUpperCase()`. Thiếu một
 *      miền thì KHÔNG đỏ ở đâu — nó lặng lẽ in "WEB" (và `geometry` sẽ in
 *      "GEOMETRY") giữa 8 miền nói tiếng Việt. `Record<Domain, string>` bên dưới
 *      làm `tsc -b` gãy nếu thêm miền mà quên nhãn: cưỡng chế ở trình biên dịch,
 *      không phải ở trí nhớ người sửa.
 *
 *   2. PHỤ ĐỀ LẶP NGUYÊN VĂN TIÊU ĐỀ. Có đề mà đề bài CHÍNH LÀ tên cơ chế
 *      ("Cổng logic AND", "Mô hình màu RGB"); khi ấy dòng phụ đề in lại đúng câu
 *      vừa đọc, ngay dưới nó. Đọc như lỗi hiển thị. Luật ẩn phải nằm ở SHELL —
 *      để 24 module tự nhớ thì đó chính là cách bề mặt sinh ra "mỗi cái một kiểu".
 */
import type { Domain } from "../simulations/types";

/**
 * Nhãn miền cho HỌC SINH — không phải `simulation_id`, không phải tên miền kỹ
 * thuật. TOÀN PHẦN theo `Domain`: thêm miền mới mà quên nhãn ⇒ `tsc -b` gãy.
 */
export const DOMAIN_BADGE: Record<Domain, string> = {
  generic: "MÔ PHỎNG THEO MÔ TẢ",
  algorithm: "THUẬT TOÁN",
  network: "MẠNG",
  tree: "CÂY",
  binary: "HỆ CƠ SỐ",
  logic: "LOGIC",
  database: "TRUY VẤN BẢNG",
  color: "MÀU SẮC",
  web: "TRANG WEB",
  geometry: "HÌNH HỌC",
};

/** Bỏ hoa/thường và gộp khoảng trắng — hai chuỗi chỉ khác thế thì mắt vẫn đọc ra một câu. */
const norm = (s: string) => s.trim().replace(/\s+/g, " ").toLocaleLowerCase("vi");

/**
 * Phụ đề cơ chế, hoặc `null` khi nó KHÔNG nói thêm được gì so với tiêu đề.
 *
 * Trả `null` chứ không trả chuỗi rỗng: chỗ gọi phải quyết định KHÔNG DỰNG phần
 * tử, chứ không phải dựng một `<span>` rỗng — span rỗng vẫn ăn khoảng cách của
 * lưới và đẩy bố cục lệch đúng bằng một dòng ở 2 target so với 22 target kia.
 */
export function headerSubtitle(modTitle: string, envelopeTitle: unknown): string | null {
  const sub = String(modTitle ?? "").trim();
  if (!sub) return null;
  return norm(sub) === norm(String(envelopeTitle ?? "")) ? null : sub;
}
