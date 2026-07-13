import { create } from "zustand";
import type { AnalysisUnsupported } from "../core/types";
import { getSimulation } from "../simulations/registry";
import type { SimAction, SimulationEnvelope, TimelineCapability } from "../simulations/types";

/**
 * Store lõi — MÙ DOMAIN (ràng buộc M2 #7): chỉ giữ moduleId + envelope +
 * config + state dạng opaque. Mọi biến đổi state đi qua module.apply /
 * module.timeline lấy từ registry. Store không import Trace, không biết
 * mảng/nhánh/mã giả là gì.
 */

export interface ActiveSimulation {
  moduleId: string;
  envelope: SimulationEnvelope;
  /** Config đã qua module.validateConfig — bất biến. */
  config: unknown;
  /** Engine state — module sở hữu, store chỉ cầm hộ. */
  state: unknown;
}

interface AppState {
  problemText: string;
  analyzing: boolean;
  analysisError: string | null;
  unsupported: AnalysisUnsupported | null;
  activeSampleId: string | null;

  active: ActiveSimulation | null;
  /** Chỉ có nghĩa khi module có timeline capability. */
  playing: boolean;
  speedMs: number;

  /** Trạng thái panel (tổng quát, không dính domain — M2 #3, #8). */
  leftOpen: boolean;
  rightOpen: boolean;
  /** AI Help KHÔNG mở mặc định (M2 #7). */
  inspectorTab: "inspect" | "ai";

  setProblemText: (text: string) => void;
  setAnalyzing: (v: boolean) => void;
  setAnalysisError: (msg: string | null) => void;
  loadEnvelope: (env: SimulationEnvelope, sampleId?: string) => void;
  loadUnsupported: (u: AnalysisUnsupported) => void;

  /** Tương tác người học → module.apply (what-if, toggle, tham số...). */
  dispatch: (action: SimAction) => void;
  /** Điều khiển timeline — NO-OP nếu module không có capability (M2 #4). */
  goToStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  toStart: () => void;
  toEnd: () => void;
  /** Dựng lại state từ config — dùng cho cả progressive lẫn exploratory. */
  resetSim: () => void;

  /**
   * M7.14: thay config + state sau một EDIT đã validate (patch flow). Store
   * vẫn MÙ DOMAIN — cặp config/state mới do module tự dựng (vd applyEditedSpec)
   * rồi đưa vào đây nguyên khối; config tiếp tục bất biến sau khi thay.
   */
  replaceSimulation: (config: unknown, state: unknown) => void;

  setPlaying: (v: boolean) => void;
  setSpeedMs: (ms: number) => void;
  toggleLeft: () => void;
  toggleRight: () => void;
  setInspectorTab: (tab: "inspect" | "ai") => void;
  reset: () => void;
}

/** Màn hình hẹp → panel đóng sẵn để workspace không bị bóp (M2 responsive). */
const WIDE_SCREEN = typeof window === "undefined" || window.innerWidth >= 1100;

export const useAppStore = create<AppState>((set, get) => {
  /** Chạy một phép biến đổi qua timeline capability; không có thì bỏ qua. */
  function withTimeline(
    fn: (tl: TimelineCapability<unknown>, state: unknown) => unknown,
  ): void {
    const { active } = get();
    if (!active) return;
    const mod = getSimulation(active.moduleId);
    if (!mod?.timeline) return;
    const next = fn(mod.timeline, active.state);
    if (next !== active.state) set({ active: { ...active, state: next } });
  }

  return {
    problemText: "",
    analyzing: false,
    analysisError: null,
    unsupported: null,
    activeSampleId: null,
    active: null,
    playing: false,
    speedMs: 1200,
    leftOpen: WIDE_SCREEN,
    rightOpen: WIDE_SCREEN,
    inspectorTab: "inspect",

    setProblemText: (text) => set({ problemText: text }),
    setAnalyzing: (v) => set({ analyzing: v }),
    setAnalysisError: (msg) => set({ analysisError: msg }),

    loadEnvelope: (env, sampleId) => {
      const mod = getSimulation(env.simulation_id);
      if (!mod) {
        set({
          analysisError: `Hệ thống chưa có mô phỏng "${env.simulation_id}".`,
          activeSampleId: null,
        });
        return;
      }
      const result = mod.validateConfig(env.config);
      if (!result.ok) {
        set({
          analysisError: `Cấu hình mô phỏng không hợp lệ: ${result.error}`,
          activeSampleId: null,
        });
        return;
      }
      set({
        active: {
          moduleId: mod.id,
          envelope: env,
          config: result.config,
          state: mod.init(result.config),
        },
        unsupported: null,
        analysisError: null,
        activeSampleId: sampleId ?? null,
        playing: false,
      });
    },

    loadUnsupported: (u) =>
      set({
        active: null,
        unsupported: u,
        analysisError: null,
        activeSampleId: null,
        playing: false,
      }),

    dispatch: (action) => {
      const { active } = get();
      if (!active) return;
      const mod = getSimulation(active.moduleId);
      if (!mod) return;
      const next = mod.apply(active.state, action);
      if (next !== active.state) set({ active: { ...active, state: next } });
    },

    goToStep: (step) => withTimeline((tl, s) => tl.goToStep(s, step)),

    nextStep: () =>
      withTimeline((tl, s) => {
        const cur = tl.currentStep(s);
        if (cur >= tl.stepCount(s) - 1) {
          set({ playing: false });
          return s;
        }
        return tl.goToStep(s, cur + 1);
      }),

    prevStep: () => {
      set({ playing: false });
      withTimeline((tl, s) => tl.goToStep(s, tl.currentStep(s) - 1));
    },

    toStart: () => {
      set({ playing: false });
      withTimeline((tl, s) => tl.goToStep(s, 0));
    },

    toEnd: () => {
      set({ playing: false });
      withTimeline((tl, s) => tl.goToStep(s, tl.stepCount(s) - 1));
    },

    resetSim: () => {
      const { active } = get();
      if (!active) return;
      const mod = getSimulation(active.moduleId);
      if (!mod) return;
      set({ active: { ...active, state: mod.init(active.config) }, playing: false });
    },

    replaceSimulation: (config, state) => {
      const { active } = get();
      if (!active) return;
      set({
        active: {
          ...active,
          config,
          state,
          envelope: { ...active.envelope, config },
        },
        playing: false,
      });
    },

    setPlaying: (v) => set({ playing: v }),
    setSpeedMs: (ms) => set({ speedMs: ms }),
    toggleLeft: () => set({ leftOpen: !get().leftOpen }),
    toggleRight: () => set({ rightOpen: !get().rightOpen }),
    setInspectorTab: (tab) => set({ inspectorTab: tab }),

    reset: () =>
      set({
        active: null,
        unsupported: null,
        analysisError: null,
        activeSampleId: null,
        playing: false,
      }),
  };
});
