import { SAMPLES } from "./samples";
import { OFFLINE_SAMPLES, type SampleVisibility } from "./sim-samples";
import { fromLegacyAnalysis, toSimulationId } from "../simulations/legacy";
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
  visibility: SampleVisibility;
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
    ...SAMPLES.map(
      (s): CatalogEntry => ({
        id: s.id,
        title: s.analysis.problem.summary,
        simId: toSimulationId(s.algorithmId),
        domain: "algorithm" as Domain,
        envelope: fromLegacyAnalysis(s.analysis),
        visibility: "public",
      }),
    ),
    ...OFFLINE_SAMPLES.map(
      (s): CatalogEntry => ({
        id: s.id,
        title: s.envelope.title,
        simId: s.envelope.simulation_id,
        domain: s.envelope.domain,
        envelope: s.envelope,
        visibility: s.visibility ?? "public",
        preview: s.preview,
      }),
    ),
  ];
}

/** Danh mục HỌC SINH THẤY — chỉ mẫu public (Tin học THPT). */
/**
 * W5P — TIÊU ĐIỂM KHOÁ LUẬN: 13 target thuộc BA ĐIỂM NGHẼN nhận thức.
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
export function publicCatalog(): CatalogEntry[] {
  return offlineCatalog().filter(
    (e) => e.visibility === "public" && FOCUS_SIM_IDS.includes(e.simId),
  );
}

/** Gợi ý khám phá trên Home — bộ NHỎ chọn lọc, không đổ cả danh mục dài. */
const STARTER_SIM_IDS = [
  "algorithm.find_max",
  "algorithm.binary_search",
  "algorithm.bubble_sort",
  "algorithm.linear_search",
  "tree.traversal",
  "network.graph_traversal",
];

export function starterEntries(): CatalogEntry[] {
  const pub = publicCatalog();
  const out: CatalogEntry[] = [];
  for (const simId of STARTER_SIM_IDS) {
    const entry = pub.find((e) => e.simId === simId);
    if (entry) out.push(entry);
  }
  return out;
}
