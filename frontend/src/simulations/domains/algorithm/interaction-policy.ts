import type { AlgorithmId } from "../../../core/types";

/**
 * CHÍNH SÁCH TƯƠNG TÁC THEO CƠ CHẾ (M9-S1) — chấm dứt "một swap cho cả tám bài".
 *
 * LUẬT QUYẾT ĐỊNH (bất biến M9-S1, khoá bằng interaction-policy.test.ts):
 * một thao tác của người học chỉ được bày ra khi trả lời được chuỗi:
 *   hành động → hệ quả tất định từ engine → thay đổi state nhìn thấy được
 *   hoặc bất biến có nghĩa → làm rõ mục tiêu học.
 * Thao tác mà "hầu như không có gì đổi và không ai giải thích vì sao" là
 * TRANG TRÍ → không bày (không admitted).
 *
 * Bốn mode:
 * - "free":      thao tác CHÍNH LÀ cơ chế đang học → luôn bật (sắp xếp: đổi chỗ).
 * - "framed":    có hệ quả thật nhưng cần KHUNG câu hỏi đi kèm để hệ quả có
 *                nghĩa (tìm tuần tự: vị trí target ↔ số lần so sánh).
 * - "challenge": chỉ có nghĩa như THÍ NGHIỆM có chủ đích — phá bất biến hoặc
 *                phá tiền điều kiện; ẨN mặc định, mở bằng nút thí nghiệm kèm
 *                khung giải thích (find_max/min: bất biến vùng-đã-duyệt;
 *                binary_search: tiền điều kiện dãy đã sắp).
 * - "hidden":    không nhắm cơ chế (sum/count bất biến theo thứ tự duyệt trừ
 *                trường hợp biên khó thấy) → không bày.
 *
 * Gating theo ĐỊNH DANH NGỮ NGHĨA `algorithm_id` trong config đã validate —
 * KHÔNG theo tiêu đề/tên bài (anti-pattern #2, ARCHITECTURE_MAP §8).
 */

export type WhatIfMode = "free" | "framed" | "challenge" | "hidden";

export interface WhatIfPolicy {
  mode: WhatIfMode;
  /** Gợi ý hiển thị khi kéo-thả đang bật (free/framed/challenge-đang-mở). */
  hint?: string;
  /** Nhãn nút mở thí nghiệm (chỉ mode "challenge"). */
  challengeLabel?: string;
  /** Khung giải thích thí nghiệm — nói rõ bất biến/tiền điều kiện đang thử. */
  framing?: string;
  /** Vì sao thao tác này KHÔNG phải trang trí (tự khai, phục vụ audit). */
  rationale: string;
}

const POLICIES: Record<AlgorithmId, WhatIfPolicy> = {
  bubble_sort: {
    mode: "free",
    hint: 'Kéo một cột thả lên cột khác để thử "nếu đổi chỗ thì sao?" — đổi chỗ chính là cơ chế của sắp xếp nổi bọt.',
    rationale:
      "Đổi chỗ là chính cơ chế đang học; engine chạy tiếp tất định trên dãy đã đổi, hệ quả nhìn thấy ngay trong nhánh thử nghiệm.",
  },
  insertion_sort: {
    mode: "free",
    hint: 'Kéo một cột thả lên cột khác để thử "nếu đổi chỗ thì sao?" — quan sát thứ tự dời/chèn thay đổi theo.',
    rationale:
      "Thứ tự phần tử quyết định số lần dời và vị trí chèn; đổi chỗ làm hệ quả đó hiện ra tất định trong nhánh thử nghiệm.",
  },
  linear_search: {
    mode: "framed",
    hint: "Kéo đổi chỗ để đưa giá trị cần tìm tới sớm hơn hay muộn hơn — số lần so sánh sẽ thay đổi thế nào?",
    rationale:
      "Vị trí của giá trị cần tìm quyết định CHI PHÍ tìm kiếm (số lần so sánh) — hệ quả tất định, nhìn thấy ở kết quả nhánh.",
  },
  binary_search: {
    mode: "challenge",
    challengeLabel: "🧪 Thí nghiệm: nếu dãy không còn được sắp thứ tự?",
    framing:
      "Tìm kiếm nhị phân chỉ đúng khi dãy đã sắp thứ tự. Hãy đổi chỗ hai phần tử để phá thứ tự đó, rồi quan sát: thuật toán có thể bỏ sót giá trị có thật trong dãy.",
    hint: "Kéo đổi chỗ hai cột để phá thứ tự sắp — rồi xem thuật toán còn tìm thấy đúng không.",
    rationale:
      "Đổi chỗ tự do phá tiền điều kiện mà không ai giải thích → gây hiểu lầm; đóng khung thành thí nghiệm tiền-điều-kiện thì hệ quả (bỏ sót giá trị) là bài học tất định.",
  },
  find_max: {
    mode: "challenge",
    challengeLabel: "🧪 Thí nghiệm: thử đánh lừa thuật toán",
    framing:
      "Thuật toán chỉ nhớ giá trị tốt nhất ĐÃ GẶP và không bao giờ quay lại vùng đã duyệt. Hãy đổi một phần tử chưa duyệt vào vùng đã duyệt rồi xem kết quả cuối.",
    hint: "Kéo một cột chưa duyệt thả vào vùng đã duyệt (các cột xám) — kết quả cuối có còn đúng với dãy mới không?",
    rationale:
      "Đổi chỗ thường không đổi kết quả (max bất biến theo thứ tự) → tự do là trang trí; đóng khung quanh bất biến vùng-đã-duyệt thì hệ quả (thuật toán bị lừa) là bài học tất định về vòng lặp.",
  },
  find_min: {
    mode: "challenge",
    challengeLabel: "🧪 Thí nghiệm: thử đánh lừa thuật toán",
    framing:
      "Thuật toán chỉ nhớ giá trị tốt nhất ĐÃ GẶP và không bao giờ quay lại vùng đã duyệt. Hãy đổi một phần tử chưa duyệt vào vùng đã duyệt rồi xem kết quả cuối.",
    hint: "Kéo một cột chưa duyệt thả vào vùng đã duyệt (các cột xám) — kết quả cuối có còn đúng với dãy mới không?",
    rationale:
      "Như find_max: chỉ có nghĩa khi đóng khung quanh bất biến vùng-đã-duyệt; đổi chỗ tự do hầu như không đổi kết quả.",
  },
  sum_if: {
    mode: "hidden",
    rationale:
      "Tổng có điều kiện bất biến theo thứ tự duyệt (trừ trường hợp biên vắt qua ranh giới đã-duyệt, quá khó thấy để tự khám phá) — swap không nhắm cơ chế tích luỹ; cơ chế được nhắm bằng DỰ ĐOÁN cộng-hay-không.",
  },
  count_if: {
    mode: "hidden",
    rationale:
      "Như sum_if: biến đếm bất biến theo thứ tự duyệt; swap là trang trí. Cơ chế đếm được nhắm bằng dự đoán tăng-hay-giữ-nguyên.",
  },
};

export function whatIfPolicyOf(algorithmId: AlgorithmId): WhatIfPolicy {
  return POLICIES[algorithmId];
}
