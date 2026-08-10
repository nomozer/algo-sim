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

/**
 * W4B-2Z §26 — PHIÊN ĐANG MỞ: ảnh chụp ĐỦ phần runtime RIÊNG của một mô phỏng.
 *
 * Khác hẳn Lịch sử. Lịch sử ghi "em ĐÃ từng mở bài này" (bền, localStorage,
 * mở lại = dựng lại từ envelope). Phiên ghi "bài này ĐANG mở và đang ở đúng
 * chỗ em bỏ dở" — cursor, what-if đã làm, cách xem, chế độ thử thách. Mở lại
 * từ Lịch sử luôn về bước đã ghi; chuyển phiên KHÔNG dựng lại gì cả, nó trả về
 * ĐÚNG object state cũ.
 *
 * Vì sao không nhét vào History: chuyển phiên mà phải chạy lại `init` thì mọi
 * thao tác what-if của học sinh biến mất — đó chính là lỗi cần chặn.
 */
export interface OpenSession {
  id: string;
  title: string;
  active: ActiveSimulation;
  historyId: string | null;
  sampleId: string | null;
  visualMode: VisualMode;
  challengeOpen: boolean;
  prediction: PredictionResult | null;
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

  /**
   * W4B-2Z §26 — các mô phỏng ĐANG MỞ. `active` bên dưới là BẢN LÀM VIỆC của
   * phiên đang chọn; chuyển phiên = chụp bản làm việc vào phiên cũ rồi khôi
   * phục bản của phiên mới. Không gọi AI, không validate lại, không `init` lại.
   */
  sessions: OpenSession[];
  activeSessionId: string | null;

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
   * nay đi qua Thư viện trên header. Workspace còn 2 cột: sân khấu + Giải thích.
   * W4B-2B §8: mặc định ĐÓNG ở mọi bề rộng — xem lý do ở chỗ khởi tạo bên dưới.
   */
  rightOpen: boolean;
  /**
   * M9-UX5 — AI KHÔNG còn ngang hàng với Quan sát.
   * Trước đây panel phải là hai tab [Quan sát][Hỏi AI]: một nửa cột phải, lúc
   * nào cũng vậy, dành cho AI — trong khi luật gốc R0 nói LLM KHÔNG phải xương
   * sống của hệ. Nay cột phải LUÔN là Giải thích; AI là một mục THU GỌN ở đáy.
   * (Thay `inspectorTab: "inspect" | "ai"`.)
   */
  aiOpen: boolean;
  /**
   * W4B-2U2 §13 — CHẾ ĐỘ THỬ THÁCH có mở không. TRÌNH BÀY THUẦN, sống cạnh
   * `rightOpen`/`aiOpen`, KHÔNG bao giờ vào engine state hay spec.
   *
   * Vì sao cần: `predict` là NĂNG LỰC của module, nhưng trước wave này hễ module
   * khai `predict` là `PredictionBar` hiện THƯỜNG TRỰC trong Quan sát — nên mọi
   * bài đều đọc thành hỏi-đáp. Đo được: 11 target khai `predict`.
   * Nó CHƯA TỪNG chặn playback (`nextStep` không đọc `prediction`); lỗi là SỰ
   * HIỆN DIỆN, không phải cái chốt. Cờ này tách *có năng lực* khỏi *đang bày ra*.
   */
  challengeOpen: boolean;
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
  setChallengeOpen: (v: boolean) => void;
  openLibrary: () => void;

  /** W4B-2Z §26 — mở khung soạn đề MỚI mà KHÔNG đóng phiên nào đang mở. */
  newSession: () => void;
  /** Chuyển sang một phiên đang mở — 0 gọi AI, 0 dựng lại state. */
  switchSession: (id: string) => void;
  /** Đóng một phiên. Đóng phiên đang xem thì chuyển sang phiên còn lại. */
  closeSession: (id: string) => void;
  /** M8: đổi renderer — CHỈ đổi trường trình bày, không đụng active/prediction. */
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

  /**
   * W4B-2Z §26 — chụp BẢN LÀM VIỆC hiện tại vào danh sách phiên.
   *
   * Trả về danh sách phiên đã cập nhật. Không có phiên đang chọn (đang ở Home,
   * hoặc chưa mở gì) thì trả nguyên danh sách — chụp một khoảng trống sẽ đẻ ra
   * phiên ma trong thanh bên.
   */
  function snapshot(): OpenSession[] {
    const st = get();
    if (!st.active || !st.activeSessionId) return st.sessions;
    return st.sessions.map((sn) =>
      sn.id !== st.activeSessionId
        ? sn
        : {
            ...sn,
            title: st.active!.envelope.title,
            active: st.active!,
            historyId: st.activeHistoryId,
            sampleId: st.activeSampleId,
            visualMode: st.visualMode,
            challengeOpen: st.challengeOpen,
            prediction: st.prediction,
          },
    );
  }

  /** Đưa một phiên lên làm BẢN LÀM VIỆC. Thuần khôi phục — không dựng lại gì. */
  function activate(sn: OpenSession): void {
    set({
      sessions: get().sessions,
      activeSessionId: sn.id,
      active: sn.active,
      activeHistoryId: sn.historyId,
      activeSampleId: sn.sampleId,
      visualMode: sn.visualMode,
      challengeOpen: sn.challengeOpen,
      prediction: sn.prediction,
      // `playing` là trạng thái THOÁNG QUA của lần xem: quay lại một phiên mà
      // nó tự chạy tiếp là bất ngờ, còn cursor thì đã nằm trong state rồi.
      playing: false,
      view: "workspace",
      unsupported: null,
      analysisError: null,
    });
  }

  let sessionSeq = 0;

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
    aiOpen: false,
    challengeOpen: false,
    visualMode: "2d",

    setProblemText: (text) => set({ problemText: text }),
    setAnalyzing: (v) => set({ analyzing: v }),
    setAnalysisError: (msg) => set({ analysisError: msg }),

    sessions: [],
    activeSessionId: null,

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
      /* W4B-2Z §26 — nạp mô phỏng luôn CHIẾM một phiên: đang chọn phiên nào thì
         thay nội dung phiên đó (phân tích lại đề trong cùng phiên), chưa chọn
         phiên nào thì MỞ THÊM phiên mới. Nhờ vậy "+ Mô phỏng mới" rồi nạp bài
         không đè lên bài đang mở. Chụp trước để phiên cũ không mất chỗ đang dở. */
      const kept = snapshot();
      const current = get().activeSessionId;
      const sid = current ?? `s${++sessionSeq}`;
      const entry: OpenSession = {
        id: sid,
        title: env.title,
        active: nextActive,
        historyId: item.id,
        sampleId: sampleId ?? null,
        visualMode: "2d",
        challengeOpen: false,
        prediction: null,
      };
      set({
        sessions: current
          ? kept.map((sn) => (sn.id === sid ? entry : sn))
          : [...kept, entry],
        activeSessionId: sid,
        active: nextActive,
        unsupported: null,
        analysisError: null,
        activeSampleId: sampleId ?? null,
        playing: false,
        prediction: null,
        /* W4B-2Z: mô phỏng MỚI luôn mở ở chế độ Quan sát. Trước đây `challengeOpen`
           không được đặt lại nên nó rò từ bài trước sang bài sau — với một phiên
           thì khó thấy, với nhiều phiên thì thành sai lệch đo được. */
        challengeOpen: false,
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
        sessions: snapshot(),
        activeSessionId: null,
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

    /* ── W4B-2Z §26–28 — PHIÊN ĐANG MỞ ──────────────────────────
       Cả ba thao tác dưới đây là TRÌNH BÀY + KHÔI PHỤC THUẦN: không đường nào
       chạm `fetch`, `analyze`, `classify`, `simulate`, cũng không gọi lại
       `validateConfig`/`init`. Chuyển phiên trả về ĐÚNG object state cũ, nên
       what-if của học sinh còn nguyên. Đây là bất biến ZERO-AI của §28. */

    newSession: () =>
      set({
        sessions: snapshot(),
        activeSessionId: null,
        active: null,
        activeHistoryId: null,
        activeSampleId: null,
        unsupported: null,
        analysisError: null,
        playing: false,
        prediction: null,
        view: "home",
      }),

    switchSession: (id) => {
      const kept = snapshot();
      const target = kept.find((sn) => sn.id === id);
      if (!target || id === get().activeSessionId) return;
      set({ sessions: kept });
      activate(target);
    },

    closeSession: (id) => {
      const kept = snapshot().filter((sn) => sn.id !== id);
      if (id !== get().activeSessionId) {
        // Đóng phiên KHÁC không được đụng tới bài đang xem.
        set({ sessions: kept });
        return;
      }
      const next = kept[kept.length - 1];
      if (!next) {
        set({
          sessions: [], activeSessionId: null, active: null, activeHistoryId: null,
          activeSampleId: null, playing: false, prediction: null, view: "home",
        });
        return;
      }
      set({ sessions: kept });
      activate(next);
    },

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
      // Đặt lại = về Quan sát: Thử thách là chế độ học sinh chủ động vào.
      set({
        active: { ...active, state: mod.init(active.config) },
        playing: false, prediction: null, challengeOpen: false,
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
        prediction: null,
      });
    },

    setPlaying: (v) => set({ playing: v }),
    setSpeedMs: (ms) => set({ speedMs: ms }),
    toggleRight: () => set({ rightOpen: !get().rightOpen }),
    setAiOpen: (v) => set({ aiOpen: v }),
    setChallengeOpen: (v) => set({ challengeOpen: v }),

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
    /* `reset` là "về trạng thái sạch" (dùng ở test và thoát hẳn) — nó ĐÓNG mọi
       phiên. Khác `goHome`/`newSession`, hai thao tác GIỮ phiên. */
    reset: () =>
      set({
        sessions: [],
        activeSessionId: null,
        active: null,
        unsupported: null,
        analysisError: null,
        activeSampleId: null,
        playing: false,
        prediction: null,
        challengeOpen: false,
        visualMode: "2d",
        view: "home",
        activeHistoryId: null,
        history: historyStore.list(),
      }),
  };
});
