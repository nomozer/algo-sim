import type { AlgorithmId, AnalysisOk } from "../core/types";
import type { SimulationEnvelope } from "./types";

/**
 * Tương thích ngược: hệ cũ định danh bằng algorithm_id trần ("find_max"),
 * chuẩn mới là simulation_id có domain ("algorithm.find_max").
 * Backend /api/analyze cũ và 8 bài mẫu offline đi qua mapper này.
 */

export function toSimulationId(algorithmId: AlgorithmId): string {
  return `algorithm.${algorithmId}`;
}

/** Nâng kết quả phân tích kiểu cũ (AnalysisOk) lên envelope chuẩn mới. */
export function fromLegacyAnalysis(analysis: AnalysisOk): SimulationEnvelope {
  return {
    status: "ok",
    simulation_id: toSimulationId(analysis.algorithm_id),
    domain: "algorithm",
    visual_mode: "2d",
    title: analysis.problem.summary,
    description: `${analysis.problem.input} → ${analysis.problem.output}`,
    config: analysis,
    notes: analysis.notes,
  };
}
