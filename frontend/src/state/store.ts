import { create } from "zustand";
import type { AnalysisUnsupported } from "../core/types";
import { getSimulation } from "../simulations/registry";
import { historyStore, type HistoryItem } from "./history";
import type {
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


/**
 * M18 — MẶT TRÌNH BÀY. Bốn mặt cũ giữ nguyên; năm mặt mới là tầng lớp học.
 *
 * Vì sao MỞ RỘNG trường `view` chứ không thêm router: repo chưa từng có router,
 * và điều hướng đã có đúng một chủ sở hữu là trường này. Thêm `react-router`
 * để có năm màn nữa là dựng hệ điều hướng THỨ HAI cạnh hệ đang chạy — đúng
 * loại "hai nơi làm một việc" mà M9-UX7 đã gỡ một lần.
 */
export type AppView =
  | "home" | "workspace" | "library" | "history"
  | "classes" | "assignments" | "observe" | "account";

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
  view: AppView;
  /**
   * M9-UX1: BẢN CHIẾU lịch sử bền (localStorage qua historyStore) để render.
   * Nguồn chân lý là storage; store chỉ mirror sau mỗi thao tác. reset()/goHome
   * KHÔNG xoá lịch sử — runtime state và learning history là hai đời sống riêng.
   */
  history: HistoryItem[];
  /** id item lịch sử của mô phỏng đang mở — để ghi tiến độ (cursor/mode). */
  activeHistoryId: string | null;

  /**
   * W4B-2Z §26 — các mô phỏng ĐANG MỞ. `active` bên dưới là BẢN LÀM VIỆC của
   * phiên đang chọn; chuyển phiên = chụp bản làm việc vào phiên cũ rồi khôi
   * phục bản của phiên mới. Không gọi AI, không validate lại, không `init` lại.
   */

  active: ActiveSimulation | null;
  /** Chỉ có nghĩa khi module có timeline capability. */
  playing: boolean;
  speedMs: number;

  /**
   * Trạng thái panel (tổng quát, không dính domain — M2 #3, #8).
   * M9-UX7: panel TRÁI đã GỠ HẲN — sau khi có trang Thư viện, danh mục tồn tại ở
   * ba nơi (Home / Thư viện / panel trái). Panel trái là bản sao thứ ba; đổi bài
   * nay đi qua Thư viện trên header. Workspace còn 2 cột: sân khấu + Giải thích.
   * W4B-2B §8: mặc định ĐÓNG ở mọi bề rộng — xem lý do ở chỗ khởi tạo bên dưới.
   */
  rightOpen: boolean;
  /**
   * M18 — thanh điều hướng ứng dụng đang thu gọn chưa (desktop).
   * TRÌNH BÀY thuần, không đụng engine — cùng nhóm với `rightOpen`.
   */
  sidebarCollapsed: boolean;
  /** Màn hẹp: ngăn kéo đang mở chưa. Tách khỏi `sidebarCollapsed` vì hai bề
   *  rộng có hai hành vi khác nhau, gộp một cờ sẽ làm desktop và mobile giẫm nhau. */
  sidebarDrawerOpen: boolean;
  /**
   * M18 — BÀI THỰC HÀNH mà phiên hiện tại thuộc về. `null` = tự luyện.
   *
   * Đây là thứ DUY NHẤT phân biệt "đang làm bài cô giao" với "đang tự khám
   * phá", và nó phải nằm ở store phiên vì mọi bằng chứng tiến độ đều dẫn xuất
   * từ state mô phỏng — báo về đâu là thuộc tính của PHIÊN, không phải của
   * trang đang xem.
   */
  activeAssignment: { id: number; title: string; instruction: string } | null;
  /**
   * M9-UX5 — AI KHÔNG còn ngang hàng với Quan sát.
   * Trước đây panel phải là hai tab [Quan sát][Hỏi AI]: một nửa cột phải, lúc
   * nào cũng vậy, dành cho AI — trong khi luật gốc R0 nói LLM KHÔNG phải xương
   * sống của hệ. Nay cột phải LUÔN là Giải thích; AI là một mục THU GỌN ở đáy.
   * (Thay `inspectorTab: "inspect" | "ai"`.)
   */
  aiOpen: boolean;
  /**
   * W4B-3A — CHẾ ĐỘ KHÁM PHÁ có mở không. TRÌNH BÀY THUẦN, sống cạnh
   * `rightOpen`/`aiOpen`, KHÔNG bao giờ vào engine state hay spec; và cũng MÙ
   * DOMAIN: store không biết "khám phá" ở bài này nghĩa là kéo cột hay bấm liên
   * kết mạng.
   *
   * W13 — trước đây có cờ chị em `challengeOpen` cho chế độ Thử thách (cam kết
   * đi qua `predict.check` để engine phán đúng/sai). Năng lực đó đã bị gỡ hẳn:
   * sản phẩm là hệ mô phỏng tương tác, không phải hệ hỏi-đáp. Nay chỉ còn MỘT
   * chế độ thao tác, và nó không phán gì cả — hệ quả tất định là câu trả lời.
   *
   * Trước wave này cờ này sống ở `useState` cục bộ trong HAI renderer miền
   * (`domains/algorithm/ui.tsx`, `domains/network/ui.tsx`) với tên `labOpen`,
   * nên: (1) mỗi miền tự dựng lấy một nút mở, thành một DẢI nội dung dưới mô
   * hình; (2) chuyển phiên là mất chế độ đang mở mà không ai đo được; (3) không
   * test nào chạm được vào nó ngoài trình duyệt (SSR luôn thấy `false` —
   * `ARCHITECTURE_MAP §8` #13).
   */
  exploreOpen: boolean;
  /**
   * M8: visual mode là TRÌNH BÀY THUẦN TÚY — chọn component vẽ, không hơn.
   * KHÔNG nằm trong engine state/SimulationSpec, KHÔNG do LLM chọn, KHÔNG ảnh
   * hưởng tính toán tất định. Đổi mode giữ nguyên active/state/cursor.
   * Mặc định "2d"; nạp mô
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
  setExploreOpen: (v: boolean) => void;
  openLibrary: () => void;
  setView: (view: AppView) => void;
  setActiveAssignment: (a: { id: number; title: string; instruction: string } | null) => void;
  toggleSidebar: () => void;
  openSidebarDrawer: () => void;
  closeSidebarDrawer: () => void;

  /** M8: đổi renderer — CHỈ đổi trường trình bày, không đụng active. */
  setVisualMode: (mode: VisualMode) => void;
  reset: () => void;
}


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
    if (next !== active.state) {
      set({ active: { ...active, state: next } });
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
    // W4B-2B §8 — panel PHẢI (Giải thích) ĐÓNG mặc định ở MỌI bề rộng.
    //
    // Trước đây nó mở sẵn trên màn ≥1100px với lý do "biến/mã giả là biểu diễn
    // liên kết cốt lõi". Lý do đó vẫn đúng, nhưng nó biện minh cho việc panel
    // LUÔN SẴN CÓ, không phải cho việc panel LUÔN MỞ: mở sẵn thì sân khấu — thứ
    // duy nhất mang cơ chế của bài — bị cắt ~316px ngay ở cái nhìn đầu tiên, và
    // học sinh đọc lời giải thích trước khi kịp tự nhìn ra điều gì.
    //
    // An toàn được vì thông tin KHÔNG nằm riêng ở đây: mọi bước đều mang giá trị
    // trong `Step.narration` do engine dựng (vd `core/program.ts` ghép tên+giá
    // trị biến vào chính bước xét điều kiện), và narration nằm ở cột giữa nên
    // không phụ thuộc trạng thái panel. Panel là đường ĐÀO SÂU, mở bằng nút
    // "Giải thích" trên header — không phải nguồn duy nhất của sự thật.
    //
    // Hằng `WIDE_SCREEN` đã gỡ: không còn mặc định nào phụ thuộc `window` nữa,
    // nên SSR và trình duyệt khởi tạo giống hệt nhau.
    rightOpen: false,
    sidebarCollapsed: false,
    sidebarDrawerOpen: false,
    activeAssignment: null,
    aiOpen: false,
    exploreOpen: false,
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
      const nextActive = {
        moduleId: mod.id,
        envelope: env,
        config: result.config,
        state: initialState,
      };
      /* M18-UI — MỘT MÔ PHỎNG TẠI MỘT THỜI ĐIỂM.
         Nhiều phiên (W4B-2Z §26) đã GỠ: mở thêm bài thứ hai không phải việc học
         sinh làm trong một tiết, và dải tab nó sinh ra cạnh tranh chỗ với sân
         khấu. Bài đang xem bị THAY, không bị mất — `historyStore.record` ngay
         trên đã ghi nó vào Lịch sử, mở lại vẫn 0 gọi AI. */
      set({
        active: nextActive,
        unsupported: null,
        analysisError: null,
        activeSampleId: sampleId ?? null,
        playing: false,
        /* W4B-2Z: mô phỏng MỚI luôn mở ở chế độ Quan sát — cờ chế độ không được
           rò từ bài trước sang bài sau (với một phiên thì khó thấy, với nhiều
           phiên thì thành sai lệch đo được).
           W4B-3A — cùng lý do, cùng một dòng, nay chỉ còn một chế độ. */
        exploreOpen: false,
        // Chính sách M8: mô phỏng MỚI luôn mở ở 2D (mặc định); 3D là lựa chọn
        // của người dùng SAU đó, và chỉ khi module khai hỗ trợ.
        visualMode: "2d",
        view: "workspace",
        history: historyStore.list(),
        activeHistoryId: item.id,
      });
    },

    /* W4B-2Z §26 — về Home KHÔNG đóng phiên nào: chụp bản làm việc lại trước
       khi rời đi, nếu không quay lại phiên sẽ mất chỗ đang dở. */
    goHome: () =>
      set({
        view: "home",
        active: null,
        /* M18 — rời sân khấu là rời bài: nếu giữ lại, một mô phỏng tự luyện mở
           sau đó sẽ báo tiến độ vào bài cô giao. */
        activeAssignment: null,
        activeHistoryId: null,
        unsupported: null,
        analysisError: null,
        activeSampleId: null,
        playing: false,
        history: historyStore.list(),
      }),

    openHistory: () => set({ view: "history", history: historyStore.list() }),

    openLibrary: () => set({ view: "library" }),

    /* M18 — điều hướng mức ứng dụng. Đổi mặt trình bày KHÔNG đụng `active`:
       rời sang "Lớp của em" rồi quay lại phải thấy đúng mô phỏng đang dở. */
    setView: (view) => set(
      view === "history" ? { view, history: historyStore.list() } : { view }),
    setActiveAssignment: (a) => set({ activeAssignment: a }),
    toggleSidebar: () => set({ sidebarCollapsed: !get().sidebarCollapsed }),
    openSidebarDrawer: () => set({ sidebarDrawerOpen: true }),
    closeSidebarDrawer: () => set({ sidebarDrawerOpen: false }),

    reopenFromHistory: (id) => {
      const item = historyStore.list().find((x) => x.id === id);
      if (!item) return;
      // Envelope đã validate + engine tất định → 0 gọi AI, không đi pipeline.
      get().loadEnvelope(item.envelope, undefined, item.originalInput ?? undefined);
      if (get().active) {
        if (item.lastCursor !== null) get().goToStep(item.lastCursor);
        if (item.visualMode) get().setVisualMode(item.visualMode);
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
      // Đặt lại = về Quan sát: Khám phá là chế độ học sinh chủ động vào, nên
      // dựng lại mô hình thì nó đóng theo.
      set({
        active: { ...active, state: mod.init(active.config) },
        playing: false, exploreOpen: false,
      });
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
    toggleRight: () => set({ rightOpen: !get().rightOpen }),
    setAiOpen: (v) => set({ aiOpen: v }),
    setExploreOpen: (v) => set({ exploreOpen: v }),

    // M8: CHỈ đổi trường trình bày. Không đụng active (engine state/cursor giữ
    // nguyên khối), không rebuild, không gọi mạng.
    setVisualMode: (mode) => {
      set({ visualMode: mode });
      // M9-UX1: visual mode là tiến độ trình bày an toàn → ghi vào lịch sử.
      const id = get().activeHistoryId;
      if (id) historyStore.touch(id, { visualMode: mode });
    },

    // Dọn RUNTIME — lịch sử bền KHÔNG bị đụng (hai đời sống tách biệt, M9-UX1).
    /* `reset` là "về trạng thái sạch" (dùng ở test và thoát hẳn). Khác
       `goHome`: goHome giữ lịch sử hiển thị, reset dọn cả bàn làm việc. */
    reset: () =>
      set({
        active: null,
        unsupported: null,
        analysisError: null,
        activeSampleId: null,
        playing: false,
        exploreOpen: false,
        visualMode: "2d",
        view: "home",
        activeHistoryId: null,
        history: historyStore.list(),
      }),
  };
});
