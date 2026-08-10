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

/* ── W4B-2R: CHÍNH SÁCH BIỂU DIỄN — MỘT CHỦ SỞ HỮU KHAI BÁO ─────────────────
 *
 * Luật: **2D và 3D là LỰA CHỌN BIỂU DIỄN, không phải tầng đúng đắn.** Một target
 * chỉ được có cả hai khi mỗi bên chở một nghĩa khác nhau bảo vệ được. Trạng thái
 * bị cấm là `2D_AND_3D_BY_DEFAULT`: có 3D chỉ vì sản phẩm đã có renderer 3D.
 *
 * VÌ SAO DẪN XUẤT chứ không thêm một trường `representationPolicy` vào cả 22
 * module: chính sách đã nằm sẵn trong hai thứ module VỐN khai —
 * `supportedVisualModes` (được cấp mode nào) và `threeD.role` (chiều sâu có
 * nghĩa gì). Thêm trường thứ ba là dựng nguồn sự thật thứ hai để rồi phải giữ
 * đồng bộ bằng tay — đúng anti-pattern #1. Ở đây chỉ ĐẶT TÊN cho tổ hợp đã có.
 *
 * Hàm phân loại là MÔ TẢ (nói target đang ở đâu). Việc phán "được phép ở đó
 * không" thuộc `representationPolicyProblems` — tách ra để guard toàn danh mục
 * gọi được, và để một target sai chính sách vẫn phân loại được thay vì ném lỗi.
 */
export type RepresentationPolicy = "2d_only" | "3d_only" | "2d_and_3d_justified";

export function representationPolicyOf<C, S>(
  module: SimulationModule<C, S>,
): RepresentationPolicy {
  const modes = availableVisualModes(module);
  const has3d = modes.includes("3d");
  if (!has3d) return "2d_only";
  return modes.includes("2d") ? "2d_and_3d_justified" : "3d_only";
}

/**
 * Lý do target này VI PHẠM chính sách biểu diễn. Rỗng = hợp lệ.
 *
 * Điều kiện của `2d_and_3d_justified` là **lời khai `threeD.role`**, không phải
 * sự tồn tại của renderer: `architectural_poc` tự nhận chiều sâu chỉ là bố cục,
 * nên nó KHÔNG đủ tư cách bày toggle cho học sinh. Đây chính là phép kiểm đã
 * loại `network.packet_routing` khỏi 3D ở wave này — module tự khai
 * `meaningOfZ: "bố cục, không mang nghĩa khái niệm"`.
 */
export function representationPolicyProblems<C, S>(
  module: SimulationModule<C, S>,
): string[] {
  const out: string[] = [];
  const policy = representationPolicyOf(module);
  const declared = new Set(module.supportedVisualModes);

  if (policy === "2d_and_3d_justified") {
    if (module.threeD?.role !== "pedagogical") {
      out.push(
        `${module.id}: bày cả 2D lẫn 3D nhưng threeD.role = ` +
          `${module.threeD?.role ?? "(không khai)"} — chỉ "pedagogical" mới biện minh được`,
      );
    }
    if (!module.threeD?.meaningOfZ) {
      out.push(`${module.id}: có 3D mà không nói trục Z nghĩa là gì`);
    }
    /* W4B-2S — BIỆN MINH PHẢI NÊU ĐÍCH DANH TIÊU CHÍ.
     * Luật cũ dừng ở `role === "pedagogical"`, mà `role` chỉ là một nhãn tự nhận:
     * một target chép nhãn đó vào là qua cửa. Nay phải nói 3D THẮNG ở tiêu chí
     * nào VÀ vì sao 2D không diễn đạt được — buộc so sánh hai biểu diễn thay vì
     * khen một cái. */
    if (!module.threeD?.pedagogicalFit?.length) {
      out.push(
        `${module.id}: có 3D mà không khai pedagogicalFit — ` +
          `"đã có renderer 3D" không phải lý do sư phạm`,
      );
    }
    if (!module.threeD?.whyNot2d) {
      out.push(`${module.id}: có 3D mà không nói vì sao 2D không đủ`);
    }
  } else if (module.threeD) {
    out.push(`${module.id}: khai threeD nhưng chính sách là ${policy}`);
  }

  // Khai một mode mà không có renderer thật = affordance rỗng đã hứa rồi nuốt lời.
  for (const m of declared) {
    if (rendererFor(module, m) === undefined) {
      out.push(`${module.id}: khai mode "${m}" nhưng không có renderer`);
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
