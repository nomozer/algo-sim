import { SAMPLES } from "./samples";
import { OFFLINE_SAMPLES } from "./sim-samples";
import { fromLegacyAnalysis, toSimulationId } from "../simulations/legacy";
import type { Domain, SimulationEnvelope } from "../simulations/types";

/**
 * Danh mục bài mẫu OFFLINE hợp nhất (M9-UX1) — một nguồn cho cả HomeView
 * (gợi ý khám phá) lẫn InputPanel (drawer trong workspace). Mỗi entry mang
 * sẵn envelope đã chuẩn — click = loadEnvelope, không cần AI.
 */

export interface CatalogEntry {
  id: string;
  title: string;
  simId: string;
  domain: Domain;
  envelope: SimulationEnvelope;
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

export function offlineCatalog(): CatalogEntry[] {
  return [
    ...SAMPLES.map((s) => ({
      id: s.id,
      title: s.analysis.problem.summary,
      simId: toSimulationId(s.algorithmId),
      domain: "algorithm" as Domain,
      envelope: fromLegacyAnalysis(s.analysis),
    })),
    ...OFFLINE_SAMPLES.map((s) => ({
      id: s.id,
      title: s.envelope.title,
      simId: s.envelope.simulation_id,
      domain: s.envelope.domain,
      envelope: s.envelope,
    })),
  ];
}

/** Gợi ý khám phá trên Home — bộ NHỎ chọn lọc, không đổ cả danh mục dài. */
const STARTER_SIM_IDS = [
  "algorithm.find_max",
  "algorithm.binary_search",
  "algorithm.bubble_sort",
  "binary.decimal_to_binary",
  "network.packet_routing",
];

export function starterEntries(): CatalogEntry[] {
  const all = offlineCatalog();
  const out: CatalogEntry[] = [];
  for (const simId of STARTER_SIM_IDS) {
    const entry = all.find((e) => e.simId === simId);
    if (entry) out.push(entry);
  }
  return out;
}
