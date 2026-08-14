/**
 * W7 — CHẾ ĐỘ TRANSPORT LÀ CHÍNH SÁCH SƯ PHẠM, KHÔNG PHẢI THUỘC TÍNH KĨ THUẬT.
 *
 * ─── LUẬT ─────────────────────────────────────────────────────────────────
 *
 * Chế độ được KHAI cho từng target kèm lý do cơ chế. Nó TUYỆT ĐỐI không được
 * suy ra từ:
 *   · `steps.length > 0`      · module có `timeline` không
 *   · có component Play không · tên target / tên family
 *
 * Vì sao luật này đáng một file riêng: W6 đã mắc đúng lỗi ấy một lần. Bảng
 * phân loại lúc đó mặc định "module có timeline ⇒ FULL_TRACE" và cho ra con số
 * 18 — nghe gọn nhưng chỉ là phép đếm thuộc tính kĩ thuật đội lốt phán quyết sư
 * phạm. Khai đủ theo cơ chế thì con số thật là 13 / 7 / 3.
 *
 * ─── BA CHẾ ĐỘ ────────────────────────────────────────────────────────────
 *
 *   FULL_TRACE      tiến trình theo thời gian LÀ cơ chế đang dạy
 *                   ⇒ đủ bộ điều khiển: lùi · chạy · tiến · tua · tốc độ
 *   OPTIONAL_TRACE  target là CÔNG CỤ, kết quả đọc được ngay; dòng thời gian
 *                   chỉ giải thích quá trình
 *                   ⇒ mặc định gập: chỉ Đặt lại + lối vào "Xem cách thực hiện"
 *   RESET_ONLY      không có tiến trình nào để tua
 *                   ⇒ chỉ Đặt lại; KHÔNG chừa chỗ trống cho thanh tua/tốc độ
 *
 * ─── NGUỒN DUY NHẤT ───────────────────────────────────────────────────────
 *
 * `experience-manifest.test.ts` import TỪ ĐÂY. Bảng ở đó từng là bản gốc, và
 * để nguyên như thế thì mã sản phẩm sẽ phải giữ một bản sao thứ hai — hai bảng
 * cùng nói về chế độ hiển thị mà trôi khỏi nhau là kiểu trôi tệ nhất, vì triệu
 * chứng của nó là "test xanh mà học sinh thấy khác".
 */

export type TransportMode = "FULL_TRACE" | "OPTIONAL_TRACE" | "RESET_ONLY";

/** Chế độ + LÝ DO CƠ CHẾ. Không có mặc định — thiếu khai là lỗi, xem `transportModeOf`. */
export const TRANSPORT_POLICY: Record<string, readonly [TransportMode, string]> = {
  // ── Tiến trình LÀ cơ chế ────────────────────────────────────────────────
  "network.protocol_encapsulation": ["FULL_TRACE",
    "Thứ tự đóng gói qua từng tầng LÀ nội dung bài học; xem trạng thái cuối " +
    "không nói được gì về việc tiêu đề nào được thêm ở tầng nào."],
  "network.packet_routing": ["FULL_TRACE",
    "Gói tin ĐI QUA từng nút theo thứ tự; thấy nó ở đích không nói được nó đã " +
    "qua đường nào, mà chính đường đi mới là bài học định tuyến."],
  "network.graph_traversal": ["FULL_TRACE",
    "BFS/DFS khác nhau ĐÚNG Ở THỨ TỰ thăm đỉnh; bỏ trình tự là bỏ luôn phân " +
    "biệt giữa hai thuật toán."],
  "tree.traversal": ["FULL_TRACE",
    "Bốn kiểu duyệt cây cho cùng một cây nhưng khác dãy kết quả; trình tự thăm " +
    "nút CHÍNH LÀ định nghĩa của từng kiểu."],
  "algorithm.bubble_sort": ["FULL_TRACE",
    "Bài học là TRÌNH TỰ đổi chỗ do thuật toán quyết định, không phải dãy đã sắp."],
  "algorithm.insertion_sort": ["FULL_TRACE",
    "Phần đã sắp LỚN DẦN sang phải và mỗi phần tử mới được chèn vào đúng chỗ " +
    "của nó; nhìn dãy đã sắp không cho biết nó được chèn vào đâu và đẩy ai đi."],
  "algorithm.selection_sort": ["FULL_TRACE",
    "Mỗi lượt QUÉT hết phần còn lại để chọn phần tử nhỏ nhất rồi mới đổi chỗ " +
    "một lần; bỏ trình tự thì mất luôn phân biệt với sắp xếp nổi bọt."],
  "algorithm.binary_search": ["FULL_TRACE",
    "Khoảng tìm kiếm CO LẠI qua từng lượt; kết quả cuối giấu mất chính cơ chế."],
  "algorithm.linear_search": ["FULL_TRACE",
    "Bài học là DUYỆT LẦN LƯỢT tới khi gặp; biết vị trí tìm thấy không cho " +
    "biết đã phải xét bao nhiêu phần tử trước đó."],
  "algorithm.find_max": ["FULL_TRACE",
    "Kết quả là MỘT số; nó không cho biết vì sao số ấy thắng. Bài học nằm ở " +
    "chuỗi SO SÁNH và ở việc giá trị lớn nhất được cập nhật mấy lần."],
  "algorithm.find_min": ["FULL_TRACE",
    "Cùng cơ chế với find_max, chỉ đảo chiều so sánh — nên cùng lý do: một số " +
    "ở cuối không giải thích được đường đi tới nó."],
  "algorithm.scan": ["FULL_TRACE",
    "Cơ chế là QUÉT có trạng thái mang theo (biến tích luỹ đổi qua từng phần " +
    "tử); chỉ nhìn giá trị cuối thì biến tích luỹ không bao giờ xuất hiện."],
  "algorithm.bounded_control_flow": ["FULL_TRACE",
    "Bài học là RẼ NHÁNH và ĐIỀU KIỆN DỪNG: giá trị biến sau mỗi vòng và lý do " +
    "vòng lặp kết thúc chỉ tồn tại trong trình tự, không có trong kết quả."],

  // ── Công cụ: kết quả đọc được ngay, trình tự chỉ giải thích ─────────────
  "binary.base_conversion": ["OPTIONAL_TRACE",
    "Sau W5 kết quả và bảng trọng số đọc được ngay ở cursor 0; dòng thời gian " +
    "chỉ còn giải thích phép chia/trọng số."],
  "binary.character_encoding": ["OPTIONAL_TRACE",
    "Sau W5 bảng mã hoá đầy đủ hiện ngay; trace giải thích ký tự đang xét."],
  "algorithm.count_if": ["OPTIONAL_TRACE",
    "Kết quả là TẬP các phần tử thoả điều kiện, và nhìn tập ấy cạnh dãy gốc là " +
    "đã đọc ra tiêu chí lọc; trình tự duyệt chỉ giải thích thêm, không cần để hiểu."],
  "algorithm.sum_if": ["OPTIONAL_TRACE",
    "Như count_if — tập được cộng đã tự nói lên điều kiện; dòng thời gian giải " +
    "thích cách tổng dồn lên, là phần bổ sung chứ không phải đường duy nhất."],
  "logic.boolean_dag": ["OPTIONAL_TRACE",
    "Đầu ra của mạch tính được ngay khi đổi đầu vào; dòng thời gian giải thích " +
    "TÍN HIỆU LAN qua từng cổng — hữu ích nhưng không phải đường duy nhất tới đáp án."],
  "database.relational_table_query": ["OPTIONAL_TRACE",
    "Bảng kết quả là câu trả lời và nó hiện ngay khi đổi bộ lọc; trình tự " +
    "lọc → chiếu → sắp chỉ giải thích vì sao còn lại chừng ấy hàng."],
  "generic.rule_scene": ["OPTIONAL_TRACE",
    "Cảnh generic phục vụ nhiều cơ chế khác nhau; phần lớn cho xem trạng thái " +
    "đầy đủ ngay, dòng thời gian chỉ cần khi cảnh được DỰNG dần theo bước."],

  // ── Không có tiến trình nào để tua ──────────────────────────────────────
  "logic.and_gate": ["RESET_ONLY",
    "Bật/tắt công tắc là quan hệ TỨC THÌ đầu vào → đầu ra; không có tiến trình " +
    "nào để tua, chỉ cần đường về trạng thái ban đầu."],
  "binary.decimal_to_binary": ["RESET_ONLY",
    "Học sinh bật/tắt từng bit và thấy tổng đổi ngay — đây là bàn cân trọng số, " +
    "không phải một quá trình có bước."],
  "web.style_model": ["RESET_ONLY",
    "Không có tiến trình theo bước — chỉ cần đường quay về trang gốc để so sánh " +
    "trang em vừa sửa với trang ban đầu."],
};

/**
 * Chế độ của một target.
 *
 * Target chưa khai trả `null` — người gọi phải xử lý tường minh. KHÔNG trả một
 * mặc định "an toàn": mặc định chính là cách con số 18 của W6 ra đời.
 */
export function transportModeOf(simulationId: string): TransportMode | null {
  return TRANSPORT_POLICY[simulationId]?.[0] ?? null;
}

export function transportReasonOf(simulationId: string): string | null {
  return TRANSPORT_POLICY[simulationId]?.[1] ?? null;
}
