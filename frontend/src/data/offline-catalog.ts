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
  database: "var(--accent-teal)",
  web: "var(--accent-orange)",
  geometry: "var(--secondary)",
  generic: "var(--accent-orange-deep)",
};

export const DOMAIN_LABEL: Record<Domain, string> = {
  algorithm: "Thuật toán",
  logic: "Lôgic",
  binary: "Nhị phân",
  network: "Mạng",
  database: "CSDL",
  web: "Web",
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
export function publicCatalog(): CatalogEntry[] {
  return offlineCatalog().filter((e) => e.visibility === "public");
}

/** Gợi ý khám phá trên Home — bộ NHỎ chọn lọc, không đổ cả danh mục dài. */
const STARTER_SIM_IDS = [
  "algorithm.find_max",
  "algorithm.binary_search",
  "algorithm.bubble_sort",
  "binary.decimal_to_binary",
  "network.packet_routing",
  "logic.and_gate",
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
