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
    init: (spec) => ({
      spec,
      base: initialBase(spec),
      pos: layoutPositions(spec),
      timeline: buildTimeline(spec),
      cursor: 0,
    }),

    apply: (state, action: SimAction) => {
      if (action.type === "toggle") {
        if (action.target in state.base) {
          const cur = state.base[action.target];
          return { ...state, base: { ...state.base, [action.target]: cur >= 1 ? 0 : 1 } };
        }
      }
      if (action.type === "move") {
        return applyMove(state, action.target, action.x, action.y);
      }
      return state;
    },

    // Luôn khai timeline; SimulationControls chỉ hiện nút bước khi stepCount > 1
    timeline: {
      stepCount: (s) => s.timeline.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: Math.max(0, Math.min(step, s.timeline.length - 1)) }),
    },

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
