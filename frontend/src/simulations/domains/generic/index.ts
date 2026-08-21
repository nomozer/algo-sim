import { registerSimulation } from "../../registry";
import type { SimAction, SimulationModule } from "../../types";
import {
  applyMove,
  buildTimeline,
  currentFrame,
  dragTargets,
  initialBase,
  layoutPositions,
  valuesOf,
  type GenericState,
  type SimulationSpec,
} from "./model";
import { editPolicyOf } from "./edit-policy";
import { validateGenericConfig } from "./validate";
import { GenericInspector, GenericWorkspace } from "./ui";

/**
 * generic.rule_scene — engine tổng quát chạy SimulationSpec (DSL v1) do AI
 * compose. Timeline optional (có process → progressive; không → exploratory).
 * Validator ở ./validate (M7.14 — tách để patch.ts dùng chung, tránh vòng import).
 */

export function makeGenericModule(): SimulationModule<SimulationSpec, GenericState> {
  return {
    id: "generic.rule_scene",
    domain: "generic",
    title: "Mô phỏng tổng quát (AI tự dựng)",
    interactionMode: "hybrid",
    supportedVisualModes: ["2d"],

    validateConfig: validateGenericConfig,

    // pos state-owned (M7.13A): khởi tạo từ layout của spec, chỉ đổi qua "move"
    init: (spec) => {
      const base = initialBase(spec);
      // M13 fail-fast: spec không evaluate được (GenericExecutionError) thì
      // FAIL Ở ĐÂY — trước khi cảnh lên sân khấu, không phải lặng lẽ ra 0 rồi
      // "chạy" hết 10/10 bước như sự cố gốc "Dijkstra" giả.
      valuesOf(spec, base);
      return {
        spec,
        base,
        pos: layoutPositions(spec),
        timeline: buildTimeline(spec),
        cursor: 0,
      };
    },

    apply: (state, action: SimAction) => {
      if (action.type === "toggle") {
        if (action.target in state.base) {
          const cur = state.base[action.target];
          return { ...state, base: { ...state.base, [action.target]: cur >= 1 ? 0 : 1 } };
        }
      }
      if (action.type === "set_param") {
        if (action.name in state.base) {
          const val = typeof action.value === "number" ? action.value : Number(action.value);
          /* `base` là Record<string, number> và rule evaluation đọc nó như SỐ.
             Bản trước lưu thẳng `action.value` khi ép kiểu thất bại, tức nhét
             chuỗi/bool vào một bảng số — đúng loại coercion im lặng mà M13 cấm
             (bất biến "không có seed/fallback"). Không ép được thì KHÔNG đổi gì:
             thao tác ngoài miền hợp lệ là no-op, không phải là dữ liệu mới. */
          if (!Number.isFinite(val)) return state;
          return { ...state, base: { ...state.base, [action.name]: val } };
        }
      }
      if (action.type === "move") {
        return applyMove(state, action.target, action.x, action.y);
      }
      if (action.type === "step") {
        const delta = typeof action.delta === "number" ? action.delta : 1;
        const next = Math.max(0, Math.min(state.cursor + delta, state.timeline.length - 1));
        return { ...state, cursor: next };
      }
      return state;
    },

    // Luôn khai timeline; SimulationControls chỉ hiện nút bước khi stepCount > 1
    timeline: {
      stepCount: (s) => s.timeline.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: Math.max(0, Math.min(step, s.timeline.length - 1)) }),
    },

    // M7.14D: capability chỉnh sửa — affordance suy TỪ SPEC, không mặc định
    // giống nhau cho mọi cảnh generic. Domain chuyên biệt không khai → không có edit.
    edit: { policyOf: (spec) => editPolicyOf(spec) },

    // (SHELL-N) Chỉ cảnh CÓ diễn biến mới có "bước" để thuyết minh. Cảnh một
    // khung là khám phá thuần: câu duy nhất ở đó là HƯỚNG DẪN THAO TÁC, và nó
    // ở lại renderer vì phụ thuộc chế độ Chỉnh sửa (trình bày, không phải state).
    narrate: (state) =>
      state.timeline.length > 1 ? { text: currentFrame(state).narration } : null,

    getExplainContext: (state, spec) => {
      const values = valuesOf(spec, state.base);
      const frame = currentFrame(state);
      const draggable = dragTargets(spec);
      return {
        simulation_id: "generic.rule_scene",
        title: spec.title,
        values,
        objects: spec.objects.map((o) => ({ id: o.id, type: o.type, value: values[o.id] })),
        // M7.13A: vị trí THẬT của các điểm kéo được — tutor giải thích đúng cảnh hiện tại
        ...(draggable.size > 0
          ? {
              draggable_positions: Object.fromEntries(
                [...draggable].filter((id) => state.pos[id]).map((id) => [id, state.pos[id]]),
              ),
            }
          : {}),
        ...(state.timeline.length > 1
          ? {
              current_step: state.cursor + 1,
              total_steps: state.timeline.length,
              narration: frame.narration,
              entity_positions: frame.entityPos,
              visible_objects: frame.visibleIds,
            }
          : {}),
      };
    },

    Workspace: GenericWorkspace,
    Inspector: GenericInspector,
  };
}

export function registerGenericDomain(): void {
  registerSimulation(makeGenericModule());
}
