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
 * ─── LUẬT W12 §6 (Policy B), NAY ĐÃ TỰ TIÊU ────────────────────────────────
 *
 * W12 chữa nửa vời vì còn phải sống chung với Thử thách:
 *
 *   Thử thách ĐÓNG  → công cụ dùng được, không cần mở gì trước.
 *   Thử thách MỞ    → công cụ bị siết, để một câu hỏi đang chờ không bị chính
 *                     học sinh làm cho vô nghĩa giữa chừng.
 *
 * W13 gỡ hẳn Thử thách, nên vế thứ hai KHÔNG CÒN ĐỐI TƯỢNG và biểu thức co lại
 * còn đúng một điều: **engine đang chạy thì công cụ nghỉ**. Không còn chế độ nào
 * phải mở trước mới thao tác được.
 *
 * Vì sao vẫn giữ hàm này thay vì viết `!busy` tại chỗ: nó là CHỦ SỞ HỮU DUY NHẤT
 * của câu hỏi "khi nào công cụ hiện ra", dùng chung bởi hai miền. Chép `!busy`
 * ra hai nơi là dựng lại đúng cái trùng lặp mà file này sinh ra để xoá — và lần
 * trước, cái trùng lặp ấy tốn 52/92 dòng ma trận mới phát hiện ra.
 *
 * ─── ĐIỀU NÀY KHÔNG NÂNG HẠNG BẤT KỲ TARGET NÀO ────────────────────────────
 *
 * W12 §8 nói thẳng: cho kéo/đổi thứ tự KHÔNG biến target thuật toán thành
 * `INTERACTIVE_MODEL`. `whatif_swap` vẫn là INPUT_MANIPULATION. File này chỉ
 * quyết định công cụ có NHÌN THẤY ĐƯỢC không, không quyết định nó có NGHĨA gì —
 * phân loại ngữ nghĩa vẫn thuộc `interaction-semantics.test.ts`.
 */

export interface ToolAffordanceInput {
  /** Engine đang chạy: mọi công cụ đều nghỉ, luật này có từ đầu và không đổi. */
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
  return !input.busy;
}
