import type { ComponentType } from "react";
import type { SimulationModule, VisualMode, WorkspaceProps } from "./types";

/**
 * Chọn renderer theo visual mode (M8) — DẪN XUẤT TỪ HỢP ĐỒNG MODULE, không
 * switch-case theo simulation_id (anti-pattern #2: cấm hard-code theo tên bài).
 *
 * Quy tắc:
 * - `renderers[mode]` nếu module khai; riêng "2d" mặc định là `Workspace`
 *   (mọi module hiện có tự động giữ nguyên hành vi — tương thích ngược).
 * - Một mode chỉ KHẢ DỤNG khi module vừa TUYÊN BỐ (`supportedVisualModes`)
 *   vừa CÓ renderer thật — thiếu một trong hai là không có toggle (không
 *   quảng bá affordance rỗng, cùng triết lý EditPolicy M7.14D.1).
 *
 * visualMode là TRẠNG THÁI TRÌNH BÀY (presentation), sống ở store cạnh
 * leftOpen/rightOpen — không bao giờ nằm trong engine state hay SimulationSpec,
 * không do LLM chọn. Đổi mode chỉ đổi component vẽ, không đụng state/timeline.
 */

export function rendererFor<C, S>(
  module: SimulationModule<C, S>,
  mode: VisualMode,
): ComponentType<WorkspaceProps<C, S>> | undefined {
  const declared = module.renderers?.[mode];
  if (declared) return declared;
  return mode === "2d" ? module.Workspace : undefined;
}

/** Các mode thật sự dùng được của module — nguồn duy nhất cho UI toggle. */
export function availableVisualModes<C, S>(module: SimulationModule<C, S>): VisualMode[] {
  const seen = new Set<VisualMode>();
  const out: VisualMode[] = [];
  for (const mode of module.supportedVisualModes) {
    if (!seen.has(mode) && rendererFor(module, mode) !== undefined) {
      seen.add(mode);
      out.push(mode);
    }
  }
  return out;
}

/**
 * Mode hiệu lực khi render: giữ lựa chọn của người dùng nếu module đáp ứng
 * được, ngược lại rơi an toàn về "2d" (Workspace là bắt buộc nên luôn có).
 */
export function effectiveVisualMode<C, S>(
  module: SimulationModule<C, S>,
  requested: VisualMode,
): VisualMode {
  return availableVisualModes(module).includes(requested) ? requested : "2d";
}
