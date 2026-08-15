/**
 * var-label.ts — TÊN BIẾN CỦA ENGINE KHÔNG PHẢI TIẾNG NÓI CỦA HỌC SINH.
 *
 * ─── LỖI CÓ THẬT, TÌM BẰNG QUÉT TOÀN DANH MỤC ────────────────────────────
 *
 * Hai template thuyết minh nội suy THẲNG tên biến engine vào câu tiếng Việt:
 *
 *   core/scan.ts        `Khởi tạo ${seed.varName} = …`
 *   core/algorithms.ts  `Khởi tạo ${varName} = 0. …`
 *
 * Trên màn thật, `algorithm.scan` đọc ra: **"Khởi tạo nguong = 4."** — học sinh
 * nhận một định danh không dấu, không phải một khái niệm. Cùng khuôn ở
 * `sum_if`/`count_if` (`tong`, `dem`).
 *
 * Đây đúng anti-pattern #10 (định danh kỹ thuật lọt lên UI) mà `ui-hygiene`
 * sinh ra để chặn — nhưng guard ấy soi TÊN FILE/CHUỖI TĨNH, không soi chuỗi
 * ĐƯỢC NỘI SUY LÚC CHẠY. Nên lỗ này sống sót qua mọi wave.
 *
 * ─── VÌ SAO KHÔNG "TỰ THÊM DẤU" ───────────────────────────────────────────
 *
 * Không thể suy `nguong → ngưỡng` một cách tổng quát: bỏ dấu là phép ánh xạ mất
 * thông tin (`tong` có thể là "tổng", "tông", "tống"). Nên bảng dưới đây chỉ
 * phủ các biến ENGINE tự đặt — thứ ta biết chắc nghĩa. Tên do ĐẶC TẢ cấp
 * (`seed.varName`, do LLM sinh) trả `null`, và bên gọi phải nói bằng KHÁI NIỆM
 * thay vì đoán bừa một cách viết có dấu.
 */

/**
 * ─── PHẠM VI ĐÃ THU HẸP SAU KHI TRA MÃ GIẢ ────────────────────────────────
 *
 * Bản đầu của file này dịch cả `tong`, `dem`, `max`, `vt` sang tiếng Việt. SAI,
 * và một contract test đã bắt được: `core/pseudocode.ts` in ra ĐÚNG những token
 * ấy cho học sinh đọc —
 *
 *     max ← a[1]; vt ← 1        tong ← 0
 *     nếu a[i] > max thì        tong ← tong + a[i]
 *
 * Thuyết minh nói "giá trị lớn nhất" trong khi mã giả nói `max` thì học sinh
 * mất chính cây cầu giữa hai biểu diễn. Biến ĐƯỢC MÃ GIẢ NEO là từ vựng hợp lệ
 * của bài, không phải định danh rò rỉ.
 *
 * Rò rỉ THẬT chỉ còn một họ: tên biến do ĐẶC TẢ cấp (`core/scan.ts::seed.varName`,
 * LLM sinh) — `algorithm.scan` không có bảng mã giả nào neo chúng, nên
 * "Khởi tạo nguong = 4." là một chuỗi máy đứng trơ trước mặt người học.
 *
 * Vì vậy bảng dưới đây CỐ Ý RỖNG: không biến engine nào cần dịch. File tồn tại
 * để giữ ranh giới ấy có tên và có cổng — thêm một dòng vào đây phải kèm chứng
 * minh rằng biến đó KHÔNG xuất hiện trong `pseudocode.ts`.
 */
const ENGINE_VAR_LABEL: Record<string, string> = {};

/**
 * Nhãn đọc lên được của một biến engine. `null` = KHÔNG CÓ NHÃN RIÊNG — bên gọi
 * dùng chính tên biến (khi mã giả neo nó) hoặc một cụm khái niệm (khi không).
 */
export function varLabel(name: string): string | null {
  return ENGINE_VAR_LABEL[name] ?? null;
}

/**
 * Cụm danh từ cho câu thuyết minh khi tên biến KHÔNG được mã giả neo.
 *
 * Chỉ dùng ở chỗ tên do đặc tả cấp. Đừng áp cho biến của 9 bài chuyên biệt —
 * chúng có mã giả, và đổi lời ở đó là cắt cầu nối chứ không phải sửa lỗi.
 */
export function varPhrase(name: string, fallback = "giá trị theo dõi"): string {
  return varLabel(name) ?? fallback;
}

/** Biến engine có nhãn riêng. Rỗng là ĐÚNG — xem giải thích ở trên. */
export const KNOWN_ENGINE_VARS = Object.keys(ENGINE_VAR_LABEL);
