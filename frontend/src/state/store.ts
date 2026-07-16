import { create } from "zustand";
import type { AnalysisUnsupported } from "../core/types";
import { getSimulation } from "../simulations/registry";
import { historyStore, type HistoryItem } from "./history";
import type {
  PredictionResult,
  SimAction,
  SimulationEnvelope,
  TimelineCapability,
  VisualMode,
} from "../simulations/types";

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

  /**
   * M9-UX1 (mở rộng M9-UX5): BỐN MẶT TRÌNH BÀY trên cùng store — "home" (mặc
   * định: composer + vài gợi ý nổi bật), "workspace" (khi có mô phỏng),
   * "library" (danh mục ĐẦY ĐỦ, gom nhóm), "history" (toàn bộ lịch sử).
   * Là presentation state như visualMode: không đụng engine.
   *
   * Vì sao tách "library" khỏi Home (M9-UX5): Home từng bung cả 12 mẫu tại chỗ
   * và liệt kê mọi bài đang học dở — học sinh học dở nhiều thì gợi ý bị đẩy
   * xuống, Home phình theo lịch sử. Danh mục đầy đủ có NHÀ RIÊNG thì Home
   * KHÔNG BAO GIỜ phình: luôn là composer + 6 gợi ý + 1 thẻ tiếp tục.
   */
  view: "home" | "workspace" | "library" | "history";
  /**
   * M9-UX1: BẢN CHIẾU lịch sử bền (localStorage qua historyStore) để render.
   * Nguồn chân lý là storage; store chỉ mirror sau mỗi thao tác. reset()/goHome
   * KHÔNG xoá lịch sử — runtime state và learning history là hai đời sống riêng.
   */
  history: HistoryItem[];
  /** id item lịch sử của mô phỏng đang mở — để ghi tiến độ (cursor/mode). */
  activeHistoryId: string | null;

  active: ActiveSimulation | null;
  /** Chỉ có nghĩa khi module có timeline capability. */
  playing: boolean;
  speedMs: number;

  /**
   * M8-PRE-LIP: kết quả chấm dự đoán của người học — DỮ LIỆU KẾT QUẢ, giữ TÁCH
   * KHỎI engine state để mô phỏng canonical KHÔNG BAO GIỜ bị thao tác học sinh
   * làm sai lệch. Tự xoá mỗi khi state/bước đổi (dự đoán gắn với một thời điểm).
   */
  prediction: PredictionResult | null;

  /**
   * Trạng thái panel (tổng quát, không dính domain — M2 #3, #8).
   * M9-UX7: panel TRÁI đã GỠ HẲN — sau khi có trang Thư viện, danh mục tồn tại ở
   * ba nơi (Home / Thư viện / panel trái). Panel trái là bản sao thứ ba; đổi bài
   * nay đi qua Thư viện trên header. Workspace còn 2 cột: sân khấu + Quan sát.
   */
  rightOpen: boolean;
  /**
   * M9-UX5 — AI KHÔNG còn ngang hàng với Quan sát.
   * Trước đây panel phải là hai tab [Quan sát][Hỏi AI]: một nửa cột phải, lúc
   * nào cũng vậy, dành cho AI — trong khi luật gốc R0 nói LLM KHÔNG phải xương
   * sống của hệ. Nay cột phải LUÔN là Quan sát; AI là một mục THU GỌN ở đáy.
   * (Thay `inspectorTab: "inspect" | "ai"`.)
   */
  aiOpen: boolean;
  /**
   * M8: visual mode là TRÌNH BÀY THUẦN TÚY — chọn component vẽ, không hơn.
   * KHÔNG nằm trong engine state/SimulationSpec, KHÔNG do LLM chọn, KHÔNG ảnh
   * hưởng tính toán tất định. Đổi mode giữ nguyên active/state/cursor/prediction
   * (dự đoán gắn với BƯỚC, không gắn với renderer). Mặc định "2d"; nạp mô
   * phỏng mới thì quay về "2d" (chính sách M8: 2D là mặc định).
   */
  visualMode: VisualMode;

  setProblemText: (text: string) => void;
  setAnalyzing: (v: boolean) => void;
  setAnalysisError: (msg: string | null) => void;
  /** `originalInput`: đề gốc (text đã chuẩn hoá) — lưu vào lịch sử nếu có. */
  loadEnvelope: (env: SimulationEnvelope, sampleId?: string, originalInput?: string) => void;
  loadUnsupported: (u: AnalysisUnsupported) => void;

  /** M9-UX1 — điều hướng trình bày + lịch sử bền. */
  goHome: () => void;
  openHistory: () => void;
  /** Mở lại từ lịch sử: envelope đã validate + engine tất định — 0 gọi AI. */
  reopenFromHistory: (id: string) => void;
  removeHistoryItem: (id: string) => void;
  clearHistory: () => void;

  /** Tương tác người học → module.apply (what-if, toggle, tham số...). */
  dispatch: (action: SimAction) => void;
  /**
   * M8-PRE-LIP: nộp dự đoán → module.predict.check (ENGINE chấm, KHÔNG LLM).
   * NO-OP nếu module không khai capability. KHÔNG đụng engine state.
   */
  submitPrediction: (answerId: string) => void;
  clearPrediction: () => void;
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
  toggleRight: () => void;
  setAiOpen: (v: boolean) => void;
  openLibrary: () => void;
  /** M8: đổi renderer — CHỈ đổi trường trình bày, không đụng active/prediction. */
  setVisualMode: (mode: VisualMode) => void;
  reset: () => void;
}

/** Màn hình hẹp → panel đóng sẵn để workspace không bị bóp (M2 responsive). */
const WIDE_SCREEN = typeof window === "undefined" || window.innerWidth >= 1100;

export const useAppStore = create<AppState>((set, get) => {
  /** Chạy một phép biến đổi qua timeline capability; không có thì bỏ qua. */
  function withTimeline(
    fn: (tl: TimelineCapability<unknown>, state: unknown) => unknown,
  ): void {
    const { active, activeHistoryId } = get();
    if (!active) return;
    const mod = getSimulation(active.moduleId);
    if (!mod?.timeline) return;
    const next = fn(mod.timeline, active.state);
    // Đổi bước → dự đoán cũ hết hiệu lực (nó gắn với MỘT thời điểm cụ thể).
    if (next !== active.state) {
      set({ active: { ...active, state: next }, prediction: null });
      // M9-UX1: ghi tiến độ TRÌNH BÀY vào lịch sử bền (cursor là tất định nên
      // goToStep khôi phục đúng). Chỉ storage — không set() để khỏi re-render.
      if (activeHistoryId) {
        historyStore.touch(activeHistoryId, { lastCursor: mod.timeline.currentStep(next) });
      }
    }
  }

  return {
    problemText: "",
    analyzing: false,
    analysisError: null,
    unsupported: null,
    activeSampleId: null,
    view: "home",
    history: historyStore.list(),
    activeHistoryId: null,
    active: null,
    playing: false,
    speedMs: 1200,
    prediction: null,
    // Panel PHẢI (Quan sát) giữ mở trên màn rộng: biến/mã giả là biểu diễn
    // liên kết cốt lõi của M9-S1, không phải trang trí.
    rightOpen: WIDE_SCREEN,
    aiOpen: false,
    visualMode: "2d",

    setProblemText: (text) => set({ problemText: text }),
    setAnalyzing: (v) => set({ analyzing: v }),
    setAnalysisError: (msg) => set({ analysisError: msg }),

    loadEnvelope: (env, sampleId, originalInput) => {
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
      // M13: lưới sau cùng — config qua được validateConfig (hai tầng, Task
      // 3/5) nhưng runtime vẫn có thể phát hiện không evaluate được (defense
      // in depth). Store MÙ DOMAIN: bắt Error BẤT KỲ từ mod.init, không
      // import kiểu lỗi domain generic. Ghi lịch sử PHẢI nằm SAU init thành
      // công — cảnh hỏng không được lên sân khấu, cũng không bị ghi lại.
      let initialState: unknown;
      try {
        initialState = mod.init(result.config);
      } catch {
        set({
          analysisError:
            "Mô phỏng này không còn mở được: cấu hình không vượt qua kiểm tra an toàn hiện hành. " +
            "Hãy phân tích lại đề để tạo mô phỏng mới.",
          activeSampleId: null,
        });
        return;
      }
      // M9-UX1: mô phỏng validate + khởi tạo thành công → ghi lịch sử bền
      // (dedup theo simulation_id + config; mở lại chỉ touch, không nhân bản).
      const item = historyStore.record(env, originalInput ?? null);
      set({
        active: {
          moduleId: mod.id,
          envelope: env,
          config: result.config,
          state: initialState,
        },
        unsupported: null,
        analysisError: null,
        activeSampleId: sampleId ?? null,
        playing: false,
        prediction: null,
        // Chính sách M8: mô phỏng MỚI luôn mở ở 2D (mặc định); 3D là lựa chọn
        // của người dùng SAU đó, và chỉ khi module khai hỗ trợ.
        visualMode: "2d",
        view: "workspace",
        history: historyStore.list(),
        activeHistoryId: item.id,
      });
    },

    goHome: () =>
      set({
        view: "home",
        active: null,
        activeHistoryId: null,
        unsupported: null,
        analysisError: null,
        activeSampleId: null,
        playing: false,
        prediction: null,
        history: historyStore.list(),
      }),

    openHistory: () => set({ view: "history", history: historyStore.list() }),

    openLibrary: () => set({ view: "library" }),

    reopenFromHistory: (id) => {
      const item = historyStore.list().find((x) => x.id === id);
      if (!item) return;
      // Envelope đã validate + engine tất định → 0 gọi AI, không đi pipeline.
      get().loadEnvelope(item.envelope, undefined, item.originalInput ?? undefined);
      if (get().active) {
        if (item.lastCursor !== null) get().goToStep(item.lastCursor);
        if (item.visualMode) get().setVisualMode(item.visualMode);
        // goToStep xoá prediction (đúng ngữ nghĩa); tiến độ đã khôi phục xong.
        set({ prediction: null });
      }
    },

    removeHistoryItem: (id) => {
      historyStore.remove(id);
      set({ history: historyStore.list() });
    },

    clearHistory: () => {
      historyStore.clear();
      set({ history: [] });
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
      if (next !== active.state) set({ active: { ...active, state: next }, prediction: null });
    },

    submitPrediction: (answerId) => {
      const { active } = get();
      if (!active) return;
      const mod = getSimulation(active.moduleId);
      // Module không khai capability → KHÔNG có dự đoán (mặc định an toàn).
      if (!mod?.predict) return;
      // ENGINE chấm. `check` là hàm thuần → engine state KHÔNG hề bị đụng:
      // kết quả sống ở `prediction`, tách khỏi `active.state` (canonical).
      set({ prediction: mod.predict.check(active.state, answerId) });
    },

    clearPrediction: () => set({ prediction: null }),

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
      set({ active: { ...active, state: mod.init(active.config) }, playing: false, prediction: null });
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
        prediction: null,
      });
    },

    setPlaying: (v) => set({ playing: v }),
    setSpeedMs: (ms) => set({ speedMs: ms }),
    toggleRight: () => set({ rightOpen: !get().rightOpen }),
    setAiOpen: (v) => set({ aiOpen: v }),

    // M8: CHỈ đổi trường trình bày. Không đụng active (engine state/cursor giữ
    // nguyên khối), không xoá prediction (nó gắn với BƯỚC hiện tại — bước không
    // đổi thì dự đoán còn nguyên hiệu lực), không rebuild, không gọi mạng.
    setVisualMode: (mode) => {
      set({ visualMode: mode });
      // M9-UX1: visual mode là tiến độ trình bày an toàn → ghi vào lịch sử.
      const id = get().activeHistoryId;
      if (id) historyStore.touch(id, { visualMode: mode });
    },

    // Dọn RUNTIME — lịch sử bền KHÔNG bị đụng (hai đời sống tách biệt, M9-UX1).
    reset: () =>
      set({
        active: null,
        unsupported: null,
        analysisError: null,
        activeSampleId: null,
        playing: false,
        prediction: null,
        visualMode: "2d",
        view: "home",
        activeHistoryId: null,
        history: historyStore.list(),
      }),
  };
});
