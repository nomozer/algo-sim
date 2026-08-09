import type { AlgorithmId } from "../../../core/types";
import { sortInteractionOf } from "./decision";
import type { AlgorithmSimState } from "./model";

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
  /** Câu mời-thử NGẮN hiện TRƯỚC khi mở (PhET/CLT: affordance tự giải thích,
   *  giảm tải "loay hoay vận hành công cụ"). Nêu bất biến/tiền-điều-kiện đang
   *  thử mà KHÔNG lộ hệ quả — hệ quả để dành cho `framing` khi đã mở. */
  challengeTeaser?: string;
  /** Khung giải thích thí nghiệm — nói rõ bất biến/tiền điều kiện đang thử. */
  framing?: string;
  /** Vì sao thao tác này KHÔNG phải trang trí (tự khai, phục vụ audit). */
  rationale: string;
  /**
   * W4B-2B §5 — CỔNG THÍ NGHIỆM CHO **MỌI** CÔNG CỤ CỦA HỌC SINH.
   *
   * `mode` trả lời "kéo-thả có nghĩa gì ở bài này". Cờ này trả lời một câu KHÁC:
   * *"công cụ của học sinh có phải tự mở mới hiện không"* — và khi bật thì nó áp
   * cho **cả vùng cam kết lẫn kéo-thả**, không riêng kéo.
   *
   * Vì sao là cờ riêng chứ không nhét thêm một `mode`: hai bài pilot có `mode`
   * KHÁC NHAU vì lý do chính đáng (`find_max` = `challenge` — kéo chỉ có nghĩa
   * như phép thử bất biến; `insertion_sort` = `free` — kéo CHÍNH LÀ cơ chế đang
   * học). Gộp chúng thành một mode sẽ xoá đúng phân biệt mà `mode` sinh ra để
   * giữ. Cổng là chuyện TRÌNH BÀY; `mode` là chuyện NGỮ NGHĨA.
   *
   * KHÔNG bật cho bài nào khác. `find_min` và `binary_search` vẫn là `challenge`
   * (kéo sau cổng, vùng cam kết hiện thẳng ở Quan sát) — hành vi của chúng
   * không đổi một dòng trong wave này. Đây là pilot, không phải rollout.
   */
  experimentGated?: boolean;
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
    /* W4B-2B — PILOT. `mode` giữ nguyên `free`: kéo vẫn CHÍNH LÀ cơ chế đang
       học, lý do đó không hề sai đi. Đổi là chỗ ĐẶT nó: công cụ nay nằm sau
       cổng Thí nghiệm để màn mặc định chỉ còn mô phỏng. */
    experimentGated: true,
    challengeLabel: "Thí nghiệm: tự làm bước chèn",
    challengeTeaser:
      "Quân bài đang giữ phải nằm đúng chỗ của nó — em thử tự quyết định chỗ đó xem.",
    framing:
      "Ở bước này em quyết định thay thuật toán: quân bài đang giữ nên dời tiếp sang phải, hay dừng lại và chèn vào đây? Em cũng có thể kéo đổi chỗ hai cột để thử một thứ tự khác.",
  },
  selection_sort: {
    mode: "free",
    hint: 'Kéo một cột thả lên cột khác để thử "nếu đổi chỗ thì sao?" — vị trí phần tử nhỏ nhất/lớn nhất của phần chưa sắp sẽ đổi theo.',
    rationale:
      "Thứ tự phần tử quyết định vị trí cực trị được CHỌN mỗi lượt và số lần đổi chỗ; engine chạy tiếp tất định trên dãy đã đổi nên hệ quả nhìn thấy ngay trong nhánh thử nghiệm.",
  },
  linear_search: {
    mode: "framed",
    hint: "Kéo đổi chỗ để đưa giá trị cần tìm tới sớm hơn hay muộn hơn — số lần so sánh sẽ thay đổi thế nào?",
    rationale:
      "Vị trí của giá trị cần tìm quyết định CHI PHÍ tìm kiếm (số lần so sánh) — hệ quả tất định, nhìn thấy ở kết quả nhánh.",
  },
  binary_search: {
    mode: "challenge",
    challengeLabel: "Thí nghiệm: nếu dãy không còn được sắp thứ tự?",
    /* W2: teaser KHÔNG nhắc lại tiền đề nữa — `SearchActionZone` đã nêu nó
       thường trực ngay trên vùng hành động, nên nói lại ở đây là cùng một ý
       hiện hai lần trên một màn hình (đúng loại trùng lặp W1 đã gỡ). Teaser
       chỉ còn làm việc của nó: mời thử. */
    challengeTeaser: "Thử phá thứ tự đã sắp của dãy rồi xem chuyện gì xảy ra.",
    framing:
      "Tìm kiếm nhị phân chỉ đúng khi dãy đã sắp thứ tự. Hãy đổi chỗ hai phần tử để phá thứ tự đó, rồi quan sát: thuật toán có thể bỏ sót giá trị có thật trong dãy.",
    hint: "Kéo đổi chỗ hai cột để phá thứ tự sắp — rồi xem thuật toán còn tìm thấy đúng không.",
    rationale:
      "Đổi chỗ tự do phá tiền điều kiện mà không ai giải thích → gây hiểu lầm; đóng khung thành thí nghiệm tiền-điều-kiện thì hệ quả (bỏ sót giá trị) là bài học tất định.",
  },
  find_max: {
    mode: "challenge",
    challengeLabel: "Thí nghiệm: thử đánh lừa thuật toán",
    challengeTeaser:
      "Thuật toán không bao giờ nhìn lại vùng đã duyệt — thử xem điều đó có đánh lừa được nó không.",
    framing:
      "Thuật toán chỉ nhớ giá trị tốt nhất ĐÃ GẶP và không bao giờ quay lại vùng đã duyệt. Hãy đổi một phần tử chưa duyệt vào vùng đã duyệt rồi xem kết quả cuối.",
    hint: "Kéo một cột chưa duyệt thả vào vùng đã duyệt (các cột xám) — kết quả cuối có còn đúng với dãy mới không?",
    rationale:
      "Đổi chỗ thường không đổi kết quả (max bất biến theo thứ tự) → tự do là trang trí; đóng khung quanh bất biến vùng-đã-duyệt thì hệ quả (thuật toán bị lừa) là bài học tất định về vòng lặp.",
    /* W4B-2B — PILOT. Trước wave này cổng đã gác KÉO; nay gác cả VÙNG CAM KẾT,
       nên Quan sát chỉ còn mô phỏng và học sinh phải chủ động bước vào vai
       "người làm thuật toán". `find_min` cố ý KHÔNG bật cờ này. */
    experimentGated: true,
  },
  find_min: {
    mode: "challenge",
    challengeLabel: "Thí nghiệm: thử đánh lừa thuật toán",
    challengeTeaser:
      "Thuật toán không bao giờ nhìn lại vùng đã duyệt — thử xem điều đó có đánh lừa được nó không.",
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

/* ── KÉO VÀ CAM KẾT KHÔNG TRANH NHAU (W3B §1.2, §15) ─────────────────────────
 *
 * Ở ba bài sắp xếp, kéo cột có mode "free" — nó ĐÃ mang nghĩa "thí nghiệm: nếu
 * đổi chỗ thì sao" từ trước wave này. Nay bước quyết định có thêm vùng cam kết
 * nghĩa là "làm đúng việc thuật toán làm". Để cả hai cùng sống thì học sinh có
 * HAI đường để "đổi chỗ hai cột này" ở CÙNG một bước, cho hai kết cục khác hẳn:
 * một cái được engine chấm, một cái đẻ ra nhánh what-if.
 *
 * Luật: cam kết trước, thí nghiệm sau — đúng thứ tự của việc học (chốt điều
 * mình nghĩ → thấy phán quyết → mới hỏi "nếu khác đi thì sao"). Mode "free"
 * KHÔNG bị gỡ; nó chỉ hoãn trong lúc còn một cam kết đang chờ.
 *
 * Hàm THUẦN, không đọc store: luật này phải kiểm được mà không cần trình duyệt
 * (`useAppStore` trong SSR chỉ trả trạng thái ĐẦU — `ARCHITECTURE_MAP §8` #13,
 * nên một luật chôn trong JSX là một luật không test được ngoài Chrome).
 */
export interface DragGateInput {
  /** Mode của bài cho phép kéo ở thời điểm này chưa (gồm cả nút thí nghiệm đã mở). */
  policyAllows: boolean;
  busy: boolean;
  /** Đang ở bước cuối — không còn gì để chạy tiếp trên nhánh. */
  last: boolean;
  /** Học sinh đã chốt cam kết ở bước này chưa. */
  answered: boolean;
}

export function whatIfDragAllowed(state: AlgorithmSimState, input: DragGateInput): boolean {
  // R3.3a giữ nguyên: chỉ khi đang dừng, chưa ở nhánh, chưa hết bài.
  if (!input.policyAllows || input.busy || input.last || state.branch) return false;
  // §15: bước sắp xếp còn cam kết đang chờ ⇒ hoãn kéo.
  if (sortInteractionOf(state) !== null && !input.answered) return false;
  return true;
}
