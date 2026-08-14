/**
 * tool-affordance.ts — KHI NÀO CÔNG CỤ CỦA HỌC SINH ĐƯỢC PHÉP HIỆN RA.
 *
 * ─── VÌ SAO CÓ FILE NÀY ────────────────────────────────────────────────────
 *
 * Trước W12, mỗi miền tự viết lại cùng một biểu thức:
 *
 *     algorithm/ui.tsx   dragAllowedByPolicy = mode === "hidden" ? false : exploreOpen
 *     network/ui.tsx     editable            = exploreOpen && !busy
 *
 * Hai dòng ấy trông như chi tiết cục bộ, nhưng chúng là CÙNG MỘT LUẬT SẢN PHẨM
 * — "công cụ nằm sau lối vào Khám phá" — được chép tay hai lần. Nên khi luật ấy
 * sai, nó sai ở cả hai nơi và không có chỗ nào để sửa một lần.
 *
 * ─── LUẬT SAI Ở CHỖ NÀO ────────────────────────────────────────────────────
 *
 * Đo trên trình duyệt (`certify-viewports-w12.mjs`, 23 target × 4 bề rộng, HEAD
 * 99548af): **52/92 dòng** đọc ra "không có affordance nào ngoài thanh điều
 * khiển". Không phải renderer hỏng — mà vì cả hai dòng trên đòi `exploreOpen`,
 * và trang vừa mở thì `exploreOpen === false`. Hệ quả cho học sinh: mở bài ra,
 * thứ duy nhất nhìn thấy được là ô dự đoán. Màn hình đọc thành một bài kiểm tra
 * chứ không phải một công cụ.
 *
 * Lý do gốc của cổng là "đừng cho né cam kết". Nhưng cam kết chỉ tồn tại KHI
 * THỬ THÁCH ĐANG MỞ. Đóng nó lại thì không còn gì để né, nên cổng lúc ấy không
 * phục vụ mục đích nào — nó chỉ giấu công cụ đi.
 *
 * ─── LUẬT MỚI (W12 §6, Policy B) ───────────────────────────────────────────
 *
 *   Thử thách ĐÓNG  → công cụ dùng được, không cần mở gì trước.
 *   Thử thách MỞ    → công cụ có thể bị siết, để một câu hỏi đang chờ không bị
 *                     chính học sinh làm cho vô nghĩa giữa chừng.
 *   Đóng thử thách  → công cụ trở lại NGAY.
 *
 * `exploreOpen` KHÔNG bị gỡ: mở Khám phá vẫn bật công cụ kể cả khi thử thách
 * đang mở — đó là hành động cố ý của học sinh, khác hẳn việc chưa biết nút ấy
 * tồn tại.
 *
 * ─── ĐIỀU NÀY KHÔNG NÂNG HẠNG BẤT KỲ TARGET NÀO ────────────────────────────
 *
 * W12 §8 nói thẳng: cho kéo/đổi thứ tự KHÔNG biến target thuật toán thành
 * `INTERACTIVE_MODEL`. `whatif_swap` vẫn là INPUT_MANIPULATION. File này chỉ
 * quyết định công cụ có NHÌN THẤY ĐƯỢC không, không quyết định nó có NGHĨA gì —
 * phân loại ngữ nghĩa vẫn thuộc `interaction-semantics.test.ts`.
 */

export interface ToolAffordanceInput {
  /** Học sinh đã tự mở lối vào Khám phá chưa. */
  exploreOpen: boolean;
  /** Thử thách có đang mở không — nơi duy nhất một cam kết có thể đang chờ. */
  challengeOpen: boolean;
  /** Engine đang chạy: mọi công cụ đều nghỉ, luật cũ giữ nguyên. */
  busy: boolean;
}

/**
 * Công cụ thao tác của học sinh có được phép hiện ra ở thời điểm này không.
 *
 * Hàm THUẦN, không đọc store — luật sản phẩm phải kiểm được không cần trình
 * duyệt (`ARCHITECTURE_MAP §8` #13: `useAppStore` trong SSR chỉ trả trạng thái
 * đầu, nên một luật chôn trong JSX là một luật chỉ Chrome mới kiểm được).
 */
export function toolAffordanceOpen(input: ToolAffordanceInput): boolean {
  if (input.busy) return false;
  return input.exploreOpen || !input.challengeOpen;
}
