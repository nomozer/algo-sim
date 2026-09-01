import { GEOMETRY_SAMPLES } from "./geometry-samples";
import type { Domain, SimulationEnvelope } from "../simulations/types";

/**
 * Danh mục bài mẫu OFFLINE hợp nhất (M9-UX1) — một nguồn cho cả HomeView
 * (gợi ý khám phá) lẫn InputPanel (drawer trong workspace). Mỗi entry mang
 * sẵn envelope đã chuẩn — click = loadEnvelope, không cần AI.
 *
 * M9-UX2 — LUẬT PHẠM VI: kiến trúc được phép tổng quát, nhưng danh mục CÔNG
 * KHAI khoanh trong Tin học THPT. `visibility` là metadata TƯỜNG MINH khai tại
 * định nghĩa mẫu (CẤM lọc theo chuỗi tiêu đề). Gỡ một mẫu khỏi danh mục công
 * khai KHÔNG gỡ năng lực đã nuôi nó — fixture nội bộ vẫn sống cho test/dev,
 * và lịch sử học mở lại bằng envelope nên không phụ thuộc danh mục.
 */

export interface CatalogEntry {
  id: string;
  title: string;
  simId: string;
  domain: Domain;
  envelope: SimulationEnvelope;
  visibility: "public" | "internal_fixture";
  /** Gợi ý preview tường minh (vd generic không tự nói lên từ simId). */
  preview?: string;
}

export const DOMAIN_COLOR: Record<Domain, string> = {
  algorithm: "var(--accent-green)",
  logic: "var(--accent-purple-deep)",
  binary: "var(--primary)",
  network: "var(--accent-pink)",
  tree: "var(--accent-green)",
  database: "var(--accent-teal)",
  web: "var(--accent-orange)",
  color: "var(--accent-sky)",
  geometry: "var(--secondary)",
  generic: "var(--accent-orange-deep)",
};

export const DOMAIN_LABEL: Record<Domain, string> = {
  algorithm: "Thuật toán",
  logic: "Lôgic",
  binary: "Nhị phân",
  network: "Mạng",
  tree: "Cây",
  database: "CSDL",
  web: "Web",
  color: "Màu sắc",
  geometry: "Hình học",
  generic: "Tổng quát",
};

/** TOÀN BỘ mẫu (kể cả fixture nội bộ) — cho test/dev/regression. */
export function offlineCatalog(): CatalogEntry[] {
  return [
    // HÌNH HỌC — envelope SINH RA từ kernel, không viết tay (xem
    // `geometry-samples.ts`). `domain` đọc từ envelope chứ không gán cứng
    // "geometry" ở đây: gán cứng là dựng nguồn sự thật thứ hai, và nó sẽ lệch
    // đúng lúc backend đổi nhãn miền.
    //
    // ⚠️ Hai nguồn cũ (`SAMPLES` — bài mẫu Tin học soạn sẵn; `OFFLINE_SAMPLES`
    // — mẫu viết tay cho dev) đã gỡ cùng chín domain Tin học. Đây nay là nguồn
    // DUY NHẤT của danh mục offline, và nó là nguồn SINH RA chứ không viết tay
    // — tức bài mẫu không thể mang một toạ độ do người gõ vào.
    ...GEOMETRY_SAMPLES.map(
      (s): CatalogEntry => ({
        id: s.id,
        title: s.envelope.title,
        simId: s.envelope.simulation_id,
        domain: s.envelope.domain,
        envelope: s.envelope,
        visibility: "public",
        preview: s.group,
      }),
    ),
  ];
}

/**
 * PHẠM VI SẢN PHẨM — miền nào được BÀY RA cho người dùng.
 *
 * Đề tài đổi 2026-08-24 (`STATUS_LEDGER §0-2026-08-24`): sản phẩm là hệ mô phỏng
 * **hình học không gian 3D**. Trước bản này `publicCatalog()` lọc theo
 * `FOCUS_SIM_IDS` — 13 target Tin học — nên Thư viện và Trang chủ bày ra một
 * danh mục thuật toán/mạng/cây, còn ba bài hình học thì KHÔNG lối nào tới được
 * (chúng mang `simulation_id` là `generic.semantic_program`, không nằm trong
 * danh sách ấy). Tức bề mặt công khai vẫn đang quảng bá đề tài cũ.
 *
 * ⚠️ Đây là hằng số của **BỀ MẶT**, không phải của **NĂNG LỰC**. Mười miền Tin
 * học vẫn đăng ký đầy đủ, vẫn chạy, vẫn mở lại được từ Lịch sử và từ bài giáo
 * viên đã giao, vẫn nguyên trong test/benchmark. Chúng chỉ thôi được BÀY. Xoá
 * chúng là chuyện khác hẳn và phải quyết riêng — de-expose trước, delete sau.
 */
export const PRODUCT_DOMAINS: readonly Domain[] = ["geometry"];

/**
 * W5P — TIÊU ĐIỂM KHOÁ LUẬN (ĐỀ CŨ): 13 target thuộc BA ĐIỂM NGHẼN nhận thức.
 *
 * ⚠️ KHÔNG còn lái bề mặt công khai — `publicCatalog()` nay hỏi `PRODUCT_DOMAINS`.
 * Giữ lại vì nó vẫn là mirror của `FOCUS_SIMULATION_IDS` bên backend và vẫn có
 * nghĩa cho lát đánh giá của đề cũ; đọc nó như **lịch sử khoa học**, không như
 * trạng thái sản phẩm.
 *
 * Mirror của `FOCUS_SIMULATION_IDS` bên `backend/app/simulation/catalog.py`
 * (cùng khuôn hai tầng như mọi hợp đồng khác trong repo).
 *
 * Nó khai TIÊU ĐIỂM, không khai NĂNG LỰC: 11 target ngoài danh sách vẫn đăng ký
 * đầy đủ, vẫn AI tới được, vẫn chạy trong test/regression — chỉ thôi được QUẢNG
 * BÁ ở Thư viện. Nguồn phán quyết: `docs/STATUS_LEDGER.md §0`.
 */
export const FOCUS_SIM_IDS: readonly string[] = [
  "algorithm.find_max",
  "algorithm.find_min",
  "algorithm.sum_if",
  "algorithm.count_if",
  "algorithm.linear_search",
  "algorithm.scan",
  "algorithm.bounded_control_flow",
  "algorithm.binary_search",
  "algorithm.bubble_sort",
  "algorithm.insertion_sort",
  "algorithm.selection_sort",
  "tree.traversal",
  "network.graph_traversal",
];

/**
 * Bài Thư viện bày cho học sinh = mẫu công khai VÀ thuộc tiêu điểm.
 *
 * Hai điều kiện là hai câu hỏi khác nhau, cố ý giữ tách: `visibility` nói "mẫu
 * này có phải fixture nội bộ không", `FOCUS_SIM_IDS` nói "target này có thuộc
 * tiêu điểm khoá luận không". Gộp lại thì đổi phạm vi đề tài sẽ phải đi sửa
 * metadata của từng mẫu.
 */
/**
 * Danh mục NGƯỜI DÙNG THẤY: mẫu công khai VÀ thuộc phạm vi sản phẩm.
 *
 * Hai điều kiện là hai câu hỏi khác nhau, cố ý giữ tách: `visibility` nói "mẫu
 * này có phải fixture nội bộ không", `PRODUCT_DOMAINS` nói "miền này có thuộc
 * sản phẩm hiện tại không". Gộp lại thì mỗi lần đổi phạm vi sẽ phải đi sửa
 * metadata của từng mẫu.
 */
export function publicCatalog(): CatalogEntry[] {
  return discoverableCatalog().filter((e) => PRODUCT_DOMAINS.includes(e.domain));
}

/**
 * Mẫu KHÔNG PHẢI fixture nội bộ — bất kể miền.
 *
 * ─── VÌ SAO TÁCH KHỎI `publicCatalog()` ──────────────────────────────────
 *
 * Hai câu hỏi khác nhau đã có lúc trùng đáp án nên bị dùng lẫn:
 *
 *   "mẫu này có phải fixture nội bộ không"   → `discoverableCatalog()`
 *   "miền này có thuộc sản phẩm hiện tại không" → `publicCatalog()`
 *
 * Lúc sản phẩm còn là Tin học thì hai tập trùng nhau, nên các cross-lock
 * (`capability-descriptors`, `generation-parity`, `target-certification`,
 * `experience-manifest`) đều hỏi `publicCatalog()` — trong khi thứ chúng thật
 * sự canh là **target có bịa ra một mẫu không có thật hay không**, chuyện của
 * runtime chứ không phải chuyện của bề mặt quảng bá.
 *
 * Thu hẹp bề mặt xuống hình học làm hai tập tách ra, và các guard ấy đỏ vì
 * **hỏi nhầm câu**, không vì hệ hỏng. Nên tách tên chứ không nới ngưỡng: nới
 * ngưỡng là bỏ luôn thứ guard đang canh.
 */
export function discoverableCatalog(): CatalogEntry[] {
  return offlineCatalog().filter((e) => e.visibility === "public");
}

/**
 * Gợi ý trên Trang chủ — bộ NHỎ chọn lọc, không đổ cả danh mục dài.
 *
 * Chọn theo **id mẫu**, không theo `simId` như bản cũ: mọi bài hình học dùng
 * chung `generic.semantic_program`, nên lọc theo `simId` sẽ hoặc lấy hết hoặc
 * không lấy gì — không phân biệt được bài nào với bài nào.
 */
const STARTER_SAMPLE_IDS = [
  "thiet-dien-chop",
  "vuong-goc-chop",
  "the-tich-chop",
];

export function starterEntries(): CatalogEntry[] {
  const pub = publicCatalog();
  const out: CatalogEntry[] = [];
  for (const id of STARTER_SAMPLE_IDS) {
    const entry = pub.find((e) => e.id === id);
    if (entry) out.push(entry);
  }
  return out;
}
