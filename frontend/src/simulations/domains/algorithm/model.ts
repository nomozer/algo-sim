import type { AnalysisOk, Trace } from "../../../core/types";

/**
 * Model của domain algorithm — tách riêng để index.ts (logic) và ui.tsx
 * (render) cùng import mà không tạo vòng import.
 */

/** Config = kết quả phân tích đã validate (giữ nguyên hợp đồng cũ). */
export type AlgorithmConfig = AnalysisOk;

export interface AlgorithmSimState {
  /**
   * Tham chiếu CHỈ ĐỌC tới config đã validate — state mang theo để fork
   * what-if chạy lại engine; không bao giờ bị biến đổi (tách config/state).
   */
  readonly config: AlgorithmConfig;
  /** Dòng chính — timeline tất định tính sẵn toàn bộ khi init. */
  trace: Trace;
  /** Nhánh thử nghiệm what-if (R3.3) — null khi đang ở dòng chính. */
  branch: { trace: Trace; fromStep: number; i: number; j: number } | null;
  cursor: number;
}

export function activeTrace(state: AlgorithmSimState): Trace {
  return state.branch ? state.branch.trace : state.trace;
}

export function clampStep(state: AlgorithmSimState, step: number): number {
  return Math.max(0, Math.min(step, activeTrace(state).steps.length - 1));
}
