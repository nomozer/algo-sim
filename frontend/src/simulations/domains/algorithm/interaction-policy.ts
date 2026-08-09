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

/* W4B-2V/C — THÍ NGHIỆM LÀ CÔNG CỤ, KHÔNG PHẢI TẤM NỘI DUNG THỨ HAI.
 *
 * Đo được trước khi sửa (`docs/evaluation/m17/w4b2vc-experiment-tool/before/`):
 * mở cổng làm vùng làm việc CAO THÊM 122–186px, và `framing` là khối chữ lớn
 * nhất (135–310 ký tự) dựng trong một thẻ `.notes`. Đó đúng là "bài giảng thứ
 * hai nằm dưới mô phỏng".
 *
 * `framing` nay là MỘT CÂU HỎI HÀNH ĐỘNG. Nghĩa what-if KHÔNG bị xoá — nó
 * chuyển sang `hint`, chuỗi vốn đã render ngay cạnh chính công cụ kéo. Đây là
 * ràng buộc bắt buộc, không phải tuỳ chọn: W4B-2D §7 cấm trình bày kéo như
 * "bước tiếp theo của thuật toán", và câu phân biệt đó phải sống ở đâu đó.
 * Cắt chữ mà đánh mất phân biệt cam kết ↔ what-if là đổi một khối chữ lấy một
 * hồi quy ngữ nghĩa.
 */
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
      "Dời tiếp hay dừng lại?",
  },
  selection_sort: {
    mode: "free",
    hint: 'Kéo một cột thả lên cột khác để thử "nếu đổi chỗ thì sao?" — vị trí phần tử nhỏ nhất/lớn nhất của phần chưa sắp sẽ đổi theo.',
    rationale:
      "Thứ tự phần tử quyết định vị trí cực trị được CHỌN mỗi lượt và số lần đổi chỗ; engine chạy tiếp tất định trên dãy đã đổi nên hệ quả nhìn thấy ngay trong nhánh thử nghiệm.",
  },
  linear_search: {
    mode: "framed",
    hint: "Kéo = thí nghiệm, không phải bước thuật toán: dời đích, xem chi phí đổi.",
    rationale:
      "Vị trí của giá trị cần tìm quyết định CHI PHÍ tìm kiếm (số lần so sánh) — hệ quả tất định, nhìn thấy ở kết quả nhánh.",
    /* W4B-2D §3 — KÉO Ở ĐÂY LÀ WHAT-IF, KHÔNG PHẢI BƯỚC CỦA THUẬT TOÁN.
     *
     * `mode` giữ `framed`: lý do cũ không sai đi — hệ quả của việc dời đích chỉ
     * có nghĩa khi có khung câu hỏi. Đổi là chỗ ĐẶT nó.
     *
     * Căn cứ (source + Chrome, không suy từ tên bài):
     *  - `runLinearSearch` KHÔNG phát một sự kiện swap nào — chỉ `compare_value`
     *    / `mark` / `done`. Đổi chỗ không nằm trong thuật toán canonical, và mã
     *    giả trên màn hình cũng không có bước nào như thế.
     *  - Kéo đổi ĐẦU VÀO rồi chạy lại, tức nó hỏi "nếu khác đi thì sao" — đúng
     *    định nghĩa WHAT-IF, khác hẳn cam kết "thuật toán nên làm gì bước này".
     *  - Quan sát KHÔNG cần kéo mới hiểu được tìm tuần tự: khối chi phí (đã so
     *    sánh / chưa xét / xấu nhất) đã chở trọn cơ chế đáng học, và ảnh
     *    `position-numbering/before/` cho thấy màn hình đọc được đầy đủ khi chưa
     *    hề kéo.
     *  - Trước wave này Quan sát bày ĐỒNG THỜI vùng cam kết và lời mời kéo, không
     *    gì phân biệt hai thứ — đúng sự lẫn lộn mà tách Quan sát/Thí nghiệm sinh
     *    ra để gỡ.
     *
     * Cờ này đẩy CẢ HAI (cam kết + kéo) vào sau cổng: ở `ui.tsx`, `gated` làm
     * `dragAllowedByPolicy` phụ thuộc `labOpen` y như mode `challenge`. */
    experimentGated: true,
    challengeLabel: "Thí nghiệm: tự đi từng bước tìm",
    challengeTeaser:
      "Thuật toán này phải xét lần lượt từ đầu dãy, không được nhảy cóc — em thử tự đi xem.",
    /* §18 — HAI CÔNG CỤ, HAI CÂU HỎI KHÁC NHAU, nói tách bạch. Gộp chúng thành
       một lời mời sẽ dạy học sinh rằng kéo là "bước tiếp theo của thuật toán",
       đúng thứ §7 cấm. */
    framing:
      "Em quyết định bước tiếp theo.",
  },
  binary_search: {
    mode: "challenge",
    /* W4B-2D §26 — cổng nay gác CẢ vùng cam kết, nên nhãn nút phải hứa đúng thứ
       nằm sau nó. Nhãn cũ ("nếu dãy không còn được sắp thứ tự?") chỉ nói về
       KÉO; giữ nguyên thì học sinh mất các nút chọn nửa mà không có gì cho biết
       chúng đi đâu. Vế phá-tiền-đề không mất, nó chuyển vào `framing`. */
    challengeLabel: "Thí nghiệm: tự chọn nửa để tìm tiếp",
    /* W2: teaser KHÔNG nhắc lại tiền đề nữa — `SearchActionZone` đã nêu nó
       thường trực ngay trên vùng hành động, nên nói lại ở đây là cùng một ý
       hiện hai lần trên một màn hình (đúng loại trùng lặp W1 đã gỡ). Teaser
       chỉ còn làm việc của nó: mời thử. */
    challengeTeaser: "Mỗi bước loại đi một nửa — em thử tự quyết định loại nửa nào.",
    /* §18 — hai công cụ, hai câu hỏi. Cam kết đứng trước (đó là việc của thuật
       toán), phá tiền đề đứng sau (đó là thí nghiệm về điều kiện áp dụng). */
    framing:
      "Em chọn nửa để tìm tiếp.",
    hint: "Kéo = thí nghiệm: phá thứ tự đã sắp, xem còn tìm đúng không.",
    rationale:
      "Đổi chỗ tự do phá tiền điều kiện mà không ai giải thích → gây hiểu lầm; đóng khung thành thí nghiệm tiền-điều-kiện thì hệ quả (bỏ sót giá trị) là bài học tất định.",
    /* W4B-2D §26 — kéo VỐN đã sau cổng (mode `challenge`); cờ này thêm vùng cam
       kết vào cùng cổng đó, để Quan sát chỉ còn mô phỏng. Hành vi kéo không đổi
       một dòng. */
    experimentGated: true,
  },
  find_max: {
    mode: "challenge",
    challengeLabel: "Thí nghiệm: thử đánh lừa thuật toán",
    challengeTeaser:
      "Thuật toán không bao giờ nhìn lại vùng đã duyệt — thử xem điều đó có đánh lừa được nó không.",
    framing:
      "Cập nhật hay giữ nguyên?",
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
      "Cập nhật hay giữ nguyên?",
    hint: "Kéo một cột chưa duyệt thả vào vùng đã duyệt (các cột xám) — kết quả cuối có còn đúng với dãy mới không?",
    rationale:
      "Như find_max: chỉ có nghĩa khi đóng khung quanh bất biến vùng-đã-duyệt; đổi chỗ tự do hầu như không đổi kết quả.",
    /* W4B-2C — mở rộng họ quét dãy. Cùng `runFindExtreme`, cùng `challenge`,
       nên đây là bản sao kiến trúc ĐÚNG NGHĨA của find_max: cổng gác cả cam kết
       lẫn kéo. Không đổi một chữ nào của nhãn/khung — chúng vốn đã nói min. */
    experimentGated: true,
  },
  sum_if: {
    mode: "hidden",
    rationale:
      "Tổng có điều kiện bất biến theo thứ tự duyệt (trừ trường hợp biên vắt qua ranh giới đã-duyệt, quá khó thấy để tự khám phá) — swap không nhắm cơ chế tích luỹ; cơ chế được nhắm bằng DỰ ĐOÁN cộng-hay-không.",
    /* W4B-2C. `mode` GIỮ `hidden` — kéo ở bài này vẫn là trang trí, và thứ tự
       kiểm trong `ui.tsx` đặt `hidden` TRƯỚC cổng nên bật cờ này KHÔNG bật kéo.
       Cổng ở đây vì thế chở đúng MỘT việc: cam kết. */
    experimentGated: true,
    challengeLabel: "Thí nghiệm: tự cộng vào tổng",
    challengeTeaser:
      "Không phải phần tử nào cũng được cộng — em thử tự quyết định phần tử này có vào tổng không.",
    framing:
      "Phần tử này có vào tổng không?",
  },
  count_if: {
    mode: "hidden",
    rationale:
      "Như sum_if: biến đếm bất biến theo thứ tự duyệt; swap là trang trí. Cơ chế đếm được nhắm bằng dự đoán tăng-hay-giữ-nguyên.",
    /* W4B-2C — như sum_if: `hidden` giữ nguyên, cổng chỉ gác cam kết. */
    experimentGated: true,
    challengeLabel: "Thí nghiệm: tự đếm phần tử",
    challengeTeaser:
      "Không phải phần tử nào cũng được đếm — em thử tự quyết định phần tử này có vào nhóm không.",
    framing:
      "Phần tử này có vào nhóm không?",
  },
};

export function whatIfPolicyOf(algorithmId: AlgorithmId): WhatIfPolicy {
  return POLICIES[algorithmId];
}

/**
 * W4B-2D §2 — VÙNG CAM KẾT CÓ ĐƯỢC DỰNG KHÔNG. Hàm THUẦN, một dòng, nhưng nó
 * là chủ sở hữu thật của một bất biến toàn sản phẩm:
 *
 *   COMMITMENT_SURFACE_COUNT <= 1
 *   Quan sát ở bài gác cổng ⇒ 0 · Thí nghiệm mở ở bước quyết định ⇒ 1
 *
 * VÌ SAO TÁCH RA. Luật này trước đây chôn trong JSX của `AlgorithmWorkspace`,
 * nên test duy nhất kiểm được nó phải chọn một bài LÀM CHỨNG chưa gác cổng rồi
 * render SSR. Bài làm chứng đó đã phải đổi BA lần khi các họ lần lượt gác cổng
 * (`find_max` → `sum_if` → `linear_search`), và sẽ hết bài ngay khi họ tìm kiếm
 * được gác. Đổi bài làm chứng lần thứ tư là chữa triệu chứng: cái sai nằm ở chỗ
 * luật không có nơi nào gọi tên được ngoài JSX.
 *
 * Tách vào ĐÂY chứ không vào một helper của test, vì đây mới là chủ sở hữu khai
 * báo của chính sách tương tác — production gọi nó, test gọi nó, cùng một nguồn.
 * Một helper chỉ-dành-cho-test sẽ là bản sao thứ hai của luật, đúng thứ
 * `ARCHITECTURE_MAP §8` #1 cấm.
 *
 * `labOpen` là state TRÌNH BÀY cục bộ của workspace (không phải store), nên nó
 * vào đây như THAM SỐ — hàm không được biết React tồn tại.
 */
export function commitmentSurfaceVisible(policy: WhatIfPolicy, labOpen: boolean): boolean {
  return policy.experimentGated !== true || labOpen;
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
