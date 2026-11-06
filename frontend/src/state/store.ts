import { create } from "zustand";
import {
  canonicalPathForView,
  resolveLocationRoute,
  type AxoErrorKind,
} from "../components/AxoErrorExperience";
import type { AnalysisUnsupported } from "../core/types";
import { publicCatalog } from "../data/offline-catalog";
import { GEOMETRY_SAMPLES } from "../data/geometry-samples";
import type { AxoClientError, ClientFailureContract } from "../llm/client";
import { getSimulation } from "../simulations/registry";
import { useAuthStore } from "./auth";
import {
  clearServerHistory,
  deleteServerHistoryItem,
  fetchServerHistory,
  historyIdOf,
  historyStore,
  normalizeStatement,
  touchServerHistory,
  upsertServerHistory,
  type HistoryItem,
} from "./history";
import type {
  SimAction,
  ConfigResult,
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
  /**
   * Đề gốc đi kèm CHÍNH lần mở này (đề học sinh gửi khi phân tích, hoặc đề đã lưu khi mở lại từ Lịch sử).
   * Gắn vào `active` chứ không đọc từ bản ghi lịch sử: một bản ghi (khoá `simulation_id + config`) có thể
   * dùng chung với bài mẫu, nên mở bài mẫu từ Thư viện không được hiện đề của một lần gửi khác.
   */
  problemStatement?: string | null;
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
  | "home" | "workspace" | "library" | "history" | "not_found"
  | "classes" | "assignments" | "observe" | "account" | "monitor"
  | "login" | "register" | "forgot" | "reset" | "admin";

export interface RouteFailureState {
  readonly kind: AxoErrorKind;
  readonly requestedPath?: string | null;
}

const SAFE_ESCAPE_VIEWS = new Set<AppView>([
  "home",
  "library",
  "history",
  "classes",
  "assignments",
  "observe",
  "account",
  "monitor",
]);

function pushSafeRoute(stack: readonly AppView[], next: AppView): AppView[] {
  if (!SAFE_ESCAPE_VIEWS.has(next)) return [...stack];
  if (stack[stack.length - 1] === next) return [...stack];
  const updated = [...stack, next];
  return updated.length > 24 ? updated.slice(updated.length - 24) : updated;
}

interface AppState {
  problemText: string;
  analyzing: boolean;
  analysisError: string | null;
  clientFailure: ClientFailureContract | null;
  routeFailure: RouteFailureState | null;
  validRouteStack: AppView[];
  hasInAppNavigation: boolean;
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
  /* ⛔ `sidebarCollapsed` / `sidebarDrawerOpen` ĐÃ GỠ cùng cột điều hướng trái.
     Điều hướng nay là hàng ngang luôn hiện (`components/TopNav.tsx`) — nó không
     có trạng thái mở/thu/ngăn kéo nào để store phải nhớ. */
  /**
   * M18 — BÀI THỰC HÀNH mà phiên hiện tại thuộc về. `null` = tự luyện.
   *
   * Đây là thứ DUY NHẤT phân biệt "đang làm bài cô giao" với "đang tự khám
   * phá", và nó phải nằm ở store phiên vì mọi bằng chứng tiến độ đều dẫn xuất
   * từ state mô phỏng — báo về đâu là thuộc tính của PHIÊN, không phải của
   * trang đang xem.
   */
  activeAssignment: {
    id: number; title: string; instruction: string;
    /** Lớp của bài. Thiếu nó thì không biết hỏi phiên dạy của lớp nào. */
    classroomId?: number;
  } | null;
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
  setClientFailure: (failure: ClientFailureContract | null) => void;
  reportNetworkFailure: (err: AxoClientError | ClientFailureContract) => void;
  syncLocationRoute: (pathname: string, hash?: string, search?: string) => void;
  escapeFromError: () => AppView;
  /** `originalInput`: đề gốc (text đã chuẩn hoá) — lưu vào lịch sử nếu có. */
  /** `recordId`: ID lần học (lần gửi mới từ `newAttemptId`, hoặc bản ghi đang mở lại) — xem `historyStore.record`. */
  loadEnvelope: (env: SimulationEnvelope, sampleId?: string, originalInput?: string, recordId?: string) => void;
  loadUnsupported: (u: AnalysisUnsupported) => void;
  clearUnsupported: () => void;

  /** M9-UX1 — điều hướng trình bày + lịch sử bền. */
  goHome: () => void;
  /** W05 — trang đứng TRƯỚC khi vào xưởng (ghi lúc `loadEnvelope` từ ngoài xưởng); đích của nút quay lại. */
  returnView: AppView;
  /** W05 — rời xưởng như `goHome` (dọn bài, bài giao) nhưng về đúng `returnView`. */
  roiXuong: () => void;
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
  /**
   * TÓM TẮT tiêu điểm ngữ nghĩa của xưởng 3D — id vật đang chọn + việc vừa
   * làm. KHÔNG phải bản sao `InteractionState`: đó là `StudentObservation`,
   * thứ giáo viên đọc. `InteractionState` đầy đủ vẫn chỉ sống trong xưởng.
   */
  semanticFocus: { selectedId: string | null; action: string } | null;
  setSemanticFocus: (f: { selectedId: string | null; action: string } | null) => void;
  setView: (view: AppView) => void;
  setActiveAssignment: (a: { id: number; title: string; instruction: string } | null) => void;

  /** Axo V2.7 Phase D: Modal Cài đặt tài khoản (#user-account-settings-modal) & email khôi phục mật khẩu */
  accountModalOpen: boolean;
  accountModalTab: "profile" | "security";
  openAccountModal: (tab?: "profile" | "security") => void;
  closeAccountModal: () => void;
  authResetEmail: string;
  setAuthResetEmail: (email: string) => void;

  /** M8: đổi renderer — CHỈ đổi trường trình bày, không đụng active. */
  setVisualMode: (mode: VisualMode) => void;
  reset: () => void;
}


export const useAppStore = create<AppState>((set, get) => {
  let hasHydratedLocation = false;
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
        const lastCursor = mod.timeline.currentStep(next);
        historyStore.touch(activeHistoryId, { lastCursor });
        if (useAuthStore.getState().user !== null) {
          void touchServerHistory(activeHistoryId, { lastCursor });
        }
      }
    }
  }



  return {
    problemText: "",
    analyzing: false,
    analysisError: null,
    clientFailure: null,
    routeFailure: null,
    validRouteStack: ["home"],
    hasInAppNavigation: false,
    unsupported: null,
    activeSampleId: null,
    view: "home",
    returnView: "home",
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
    activeAssignment: null,
    semanticFocus: null,
    aiOpen: false,
    exploreOpen: false,
    visualMode: "2d",

    setProblemText: (text) => set({ problemText: text }),
    // Hybrid /4 (main 6fc6b309): một lần phân tích MỚI thất bại không được để lại mô phỏng/bài giao/lựa chọn của bài
    // trước cạnh thông báo lỗi của bài khác. Giữ `clientFailure` và ngăn điều hướng của trải nghiệm lỗi Axo.
    setAnalyzing: (v) => set(v ? { analyzing: true, unsupported: null } : { analyzing: false }),
    setAnalysisError: (msg) =>
      set((s) =>
        msg === null
          ? { analysisError: null, clientFailure: null }
          : /lượt mô phỏng thử/.test(msg)
            ? { analysisError: msg, unsupported: null, clientFailure: s.clientFailure }
            : {
                analysisError: msg,
                clientFailure: s.clientFailure,
                unsupported: null,
                active: null,
                activeAssignment: null,
                semanticFocus: null,
                activeHistoryId: null,
                activeSampleId: null,
                playing: false,
                view: "home",
                hasInAppNavigation: true,
                validRouteStack: pushSafeRoute(s.validRouteStack, "home"),
              },
      ),
    setClientFailure: (failure) => set({ clientFailure: failure }),
    reportNetworkFailure: (err) => {
      const contract: ClientFailureContract = {
        kind: err.kind,
        code: err.code,
        status: err.status,
        message: err.message,
      };
      set({
        clientFailure: contract,
        routeFailure: { kind: "network_failure" },
        analyzing: false,
        playing: false,
      });
    },
    syncLocationRoute: (pathname, hash = "", search = "") => {
      const wasHydrated = hasHydratedLocation;
      hasHydratedLocation = true;
      const hadNav = get().hasInAppNavigation || wasHydrated;
      const decision = resolveLocationRoute(pathname, hash, search);
      if (decision.kind === "not_found") {
        set({
          view: "not_found",
          routeFailure: { kind: "not_found", requestedPath: decision.requestedPath },
          playing: false,
          hasInAppNavigation: hadNav,
        });
        return;
      }
      if (decision.kind === "sample") {
        const entry = publicCatalog().find((s) => s.id === decision.sampleId);
        if (entry) {
          set({ routeFailure: null });
          get().loadEnvelope(entry.envelope, entry.id);
          if (get().active === null && get().unsupported === null) {
            set({
              view: "workspace",
              routeFailure: { kind: "unsupported_simulation", requestedPath: pathname },
              hasInAppNavigation: hadNav,
            });
            return;
          }
          if (!hadNav) set({ hasInAppNavigation: false });
        }
        return;
      }
      if (decision.kind === "history_item") {
        set({ routeFailure: null });
        get().reopenFromHistory(decision.historyId);
        if (get().active === null) {
          set({
            view: "workspace",
            routeFailure: { kind: "unsupported_simulation", requestedPath: pathname },
            hasInAppNavigation: hadNav,
          });
          return;
        }
        if (!hadNav) set({ hasInAppNavigation: false });
        return;
      }
      if (decision.kind === "workspace_root") {
        if (get().active !== null || get().unsupported !== null) {
          set({ view: "workspace", routeFailure: null, hasInAppNavigation: hadNav });
        } else {
          set((s) => ({
            view: "home",
            routeFailure: null,
            hasInAppNavigation: hadNav,
            validRouteStack: pushSafeRoute(s.validRouteStack, "home"),
          }));
          if (typeof window !== "undefined" && typeof window.history?.replaceState === "function") {
            try {
              window.history.replaceState({ axoView: "home", sampleId: null }, "", "/");
            } catch {
              /* bỏ qua nếu môi trường kiểm thử chặn replaceState */
            }
          }
        }
        return;
      }
      const nextView = decision.view;
      set((s) => ({
        view: nextView,
        routeFailure: null,
        hasInAppNavigation: hadNav,
        history: nextView === "history" || nextView === "home" ? historyStore.list() : s.history,
        validRouteStack: pushSafeRoute(s.validRouteStack, nextView),
      }));
    },
    escapeFromError: () => {
      const {
        view,
        returnView,
        validRouteStack,
        hasInAppNavigation,
        routeFailure,
        clientFailure,
        analysisError,
      } = get();
      let target: AppView = "home";
      let nextStack: AppView[] = ["home"];
      if (hasInAppNavigation) {
        const safeCandidates = validRouteStack.filter((v) => SAFE_ESCAPE_VIEWS.has(v));
        const hasOverlayOnSafeView =
          SAFE_ESCAPE_VIEWS.has(view)
          && (routeFailure !== null || clientFailure !== null || analysisError !== null);
        if (hasOverlayOnSafeView) {
          target = view;
          nextStack = safeCandidates.length > 0 ? safeCandidates : pushSafeRoute(["home"], target);
        } else if (view === "workspace" || view === "not_found") {
          target =
            safeCandidates[safeCandidates.length - 1] ??
            (SAFE_ESCAPE_VIEWS.has(returnView) ? returnView : "home");
          nextStack = safeCandidates.length > 0 ? safeCandidates : pushSafeRoute(["home"], target);
        } else if (safeCandidates.length > 1) {
          nextStack = safeCandidates.slice(0, -1);
          target = nextStack[nextStack.length - 1] ?? "home";
        } else {
          target = safeCandidates[0] ?? "home";
          nextStack = pushSafeRoute(["home"], target);
        }
      }
      set({
        view: target,
        active: null,
        activeAssignment: null,
        activeHistoryId: null,
        unsupported: null,
        analysisError: null,
        clientFailure: null,
        routeFailure: null,
        activeSampleId: null,
        playing: false,
        validRouteStack: nextStack,
        history: historyStore.list(),
      });
      if (typeof window !== "undefined" && typeof window.history?.replaceState === "function") {
        try {
          window.history.replaceState(
            { axoView: target },
            "",
            canonicalPathForView(target, null),
          );
        } catch {
          /* môi trường sandbox không cho phép replaceState thì giữ state bộ nhớ */
        }
      }
      return target;
    },


    loadEnvelope: (envIn, sampleId, originalInput, recordId) => {
      // «Đề bài» = đề người học đã gửi, đóng dấu vào envelope để mọi lối mở lại (Lịch sử, Thư viện, bài giao) mang theo
      // (main 928fb880). Mở bài mẫu TƯỜNG MINH không bao giờ đóng dấu; envelope đã mang đề đóng dấu (vd bài giao) là
      // một lần gửi với đề ấy, không phải bài mẫu.
      const deGui = sampleId ? undefined : (originalInput?.trim() || envIn.problem_statement?.trim() || undefined);
      const env = deGui ? { ...envIn, problem_statement: deGui } : envIn;
      const mod = getSimulation(env.simulation_id);
      if (!mod) {
        set({
          active: null, activeAssignment: null, semanticFocus: null, activeHistoryId: null, unsupported: null, playing: false, view: "home",
          analysisError: `Hệ thống chưa có mô phỏng "${env.simulation_id}".`,
          activeSampleId: null,
        });
        return;
      }
      let result: ConfigResult<unknown>;
      try {
        result = mod.validateEnvelope ? mod.validateEnvelope(env) : mod.validateConfig(env.config);
      } catch {
        result = { ok: false, error: "Dữ liệu không vượt qua kiểm tra an toàn. Hãy phân tích lại đề." };
      }
      if (!result.ok) {
        set({
          active: null, activeAssignment: null, semanticFocus: null, activeHistoryId: null, unsupported: null, playing: false, view: "home",
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
          active: null, activeAssignment: null, semanticFocus: null, activeHistoryId: null, unsupported: null, playing: false, view: "home",
          analysisError:
            "Mô phỏng này không còn mở được: cấu hình không vượt qua kiểm tra an toàn hiện hành. " +
            "Hãy phân tích lại đề để tạo mô phỏng mới.",
          activeSampleId: null,
        });
        return;
      }
      // M9-UX1: mô phỏng validate + khởi tạo thành công → ghi lịch sử bền.
      // Ngữ cảnh trình bày:
      //  - mở bài mẫu TƯỜNG MINH (`sampleId`) là mở bài mẫu: đề lấy từ danh mục, mọi đề kèm theo bị bỏ qua;
      //  - lần mở không kèm đề giữ trạng thái thiếu đề; chương trình trùng không chứng minh nguồn đề;
      //  - một lần gửi (có đề) trùng chương trình với bài mẫu vẫn là lần gửi: khoá bản ghi, URL, snapshot UI và đề
      //    là của chính nó (`historyStore.record` khoá theo `submissionIdOf`).
      const statementInput = normalizeStatement(deGui);
      const resolvedSampleId = sampleId ?? null;
      const sampleStatement = sampleId ? GEOMETRY_SAMPLES.find((s) => s.id === sampleId)?.problemText : null;
      const savedEnvelope = sampleStatement ? { ...env, problem_statement: sampleStatement } : env;
      // Mở bài mẫu tường minh không bao giờ ghi vào bản ghi lần học được truyền kèm.
      const item = historyStore.record(savedEnvelope, statementInput, sampleId ? undefined : recordId);
      if (useAuthStore.getState().user !== null) {
        const hasScene3d = Boolean((env as { scene3d?: unknown }).scene3d);
        const stepCount = hasScene3d ? 0 : (mod.timeline ? mod.timeline.stepCount(initialState) : 0);
        void upsertServerHistory(item, { sampleId: resolvedSampleId, stepCount });
      }
      const nextActive: ActiveSimulation = {
        moduleId: mod.id,
        envelope: env,
        config: result.config,
        state: initialState,
        problemStatement: deGui ?? null,
      };
      /* M18-UI — MỘT MÔ PHỎNG TẠI MỘT THỜI ĐIỂM.
         Nhiều phiên (W4B-2Z §26) đã GỠ: mở thêm bài thứ hai không phải việc học
         sinh làm trong một tiết, và dải tab nó sinh ra cạnh tranh chỗ với sân
         khấu. Bài đang xem bị THAY, không bị mất — `historyStore.record` ngay
         trên đã ghi nó vào Lịch sử, mở lại vẫn 0 gọi AI. */
      const prevView = get().view;
      const nextReturnView =
        prevView === "workspace" || prevView === "not_found" ? get().returnView : prevView;
      set((s) => ({
        active: nextActive,
        unsupported: null,
        analysisError: null,
        clientFailure: null,
        routeFailure: null,
        activeSampleId: resolvedSampleId,
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
        // Đổi bài ngay trong xưởng không phải "trang trước" — giữ đích quay lại cũ.
        returnView: SAFE_ESCAPE_VIEWS.has(nextReturnView) ? nextReturnView : "home",
        hasInAppNavigation: true,
        validRouteStack: pushSafeRoute(s.validRouteStack, nextReturnView),
        history: historyStore.list(),
        activeHistoryId: item.id,
      }));
    },

    roiXuong: () => {
      const ve = SAFE_ESCAPE_VIEWS.has(get().returnView) ? get().returnView : "home";
      get().goHome();
      get().setView(ve);
    },

    /* W4B-2Z §26 — về Home KHÔNG đóng phiên nào: chụp bản làm việc lại trước
       khi rời đi, nếu không quay lại phiên sẽ mất chỗ đang dở. */
    goHome: () =>
      set((s) => ({
        view: "home",
        active: null,
        /* M18 — rời sân khấu là rời bài: nếu giữ lại, một mô phỏng tự luyện mở
           sau đó sẽ báo tiến độ vào bài cô giao. */
        activeAssignment: null,
        activeHistoryId: null,
        unsupported: null,
        analysisError: null,
        clientFailure: null,
        routeFailure: null,
        activeSampleId: null,
        playing: false,
        hasInAppNavigation: true,
        validRouteStack: pushSafeRoute(s.validRouteStack, "home"),
        history: historyStore.list(),
      })),

    openHistory: () =>
      set((s) => ({
        view: "history",
        routeFailure: null,
        hasInAppNavigation: true,
        validRouteStack: pushSafeRoute(s.validRouteStack, "history"),
        history: historyStore.list(),
      })),

    openLibrary: () =>
      set((s) => ({
        view: "library",
        routeFailure: null,
        hasInAppNavigation: true,
        validRouteStack: pushSafeRoute(s.validRouteStack, "library"),
      })),

    /* M18 — điều hướng mức ứng dụng. Đổi mặt trình bày KHÔNG đụng `active`:
       rời sang "Lớp của em" rồi quay lại phải thấy đúng mô phỏng đang dở. */
    setView: (view) =>
      set((s) => ({
        view,
        routeFailure: view === "not_found" ? s.routeFailure : null,
        hasInAppNavigation: view === "not_found" ? s.hasInAppNavigation : true,
        validRouteStack: pushSafeRoute(s.validRouteStack, view),
        ...(view === "history" || view === "home" ? { history: historyStore.list() } : {}),
      })),
    setActiveAssignment: (a) => set({ activeAssignment: a }),
    setSemanticFocus: (f) => set({ semanticFocus: f }),

    reopenFromHistory: (id) => {
      const item = historyStore.list().find((x) => x.id === id);
      if (!item) return;
      const savedCursor = item.lastCursor;
      // History opens its own saved statement; matching catalog geometry cannot recover missing original wording.
      // Bản ghi là bài mẫu chỉ khi CHÍNH nó mang bằng chứng: không có đề người học, khoá biên dịch của bài mẫu và dấu
      // `problem_statement` mà lần mở bài mẫu tường minh đã ghi (`loadEnvelope`). Bản ghi cũ không dấu vẫn là "thiếu đề".
      const sampleId = item.originalInput
        ? undefined
        : GEOMETRY_SAMPLES.find((s) => historyIdOf(s.envelope) === item.id
          && s.problemText === item.envelope.problem_statement)?.id;
      // Envelope đã validate + engine tất định → 0 gọi AI, không đi pipeline.
      // Mở lại = cùng lần học: truyền chính ID bản ghi để không bị khoá lại theo nội dung (giữ ID qua reload/Back/Forward).
      // Bài mẫu được khoá bằng `historyIdOf`, chính là `item.id` theo điều kiện trên.
      get().loadEnvelope(item.envelope, sampleId, item.originalInput ?? undefined, item.id);
      if (get().active) {
        if (savedCursor !== null) {
          get().goToStep(savedCursor);
          // Cảnh 3D có số bước dựng nhiều hơn `view_steps` 2D: giữ nguyên `savedCursor` trong `historyStore`
          // để `AxoWorkspaceV62` khôi phục đúng bước dựng 3D mà không bị timeline 2D kẹp cụt.
          if (Boolean((item.envelope as { scene3d?: unknown }).scene3d)) {
            historyStore.touch(item.id, { lastCursor: savedCursor });
            set({ history: historyStore.list() });
          }
        }
        if (item.visualMode) get().setVisualMode(item.visualMode);
      }
    },

    removeHistoryItem: (id) => {
      historyStore.remove(id);
      set({ history: historyStore.list() });
      if (useAuthStore.getState().user !== null) {
        void deleteServerHistoryItem(id);
      }
    },

    clearHistory: () => {
      historyStore.clear();
      set({ history: [] });
      if (useAuthStore.getState().user !== null) {
        void clearServerHistory();
      }
    },

    loadUnsupported: (u) =>
      set((s) => ({
        view: "home",
        active: null,
        activeAssignment: null,
        semanticFocus: null,
        activeHistoryId: null,
        unsupported: u,
        analysisError: null,
        activeSampleId: null,
        playing: false,
        hasInAppNavigation: true,
        validRouteStack: pushSafeRoute(s.validRouteStack, "home"),
      })),

    clearUnsupported: () => set({ unsupported: null }),

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

    accountModalOpen: false,
    accountModalTab: "profile",
    openAccountModal: (tab = "profile") =>
      set({ accountModalOpen: true, accountModalTab: tab }),
    closeAccountModal: () => set({ accountModalOpen: false }),
    authResetEmail: "",
    setAuthResetEmail: (email) => set({ authResetEmail: email }),

    // M8: CHỈ đổi trường trình bày. Không đụng active (engine state/cursor giữ
    // nguyên khối), không rebuild, không gọi mạng.
    setVisualMode: (mode) => {
      set({ visualMode: mode });
      // M9-UX1: visual mode là tiến độ trình bày an toàn → ghi vào lịch sử.
      const id = get().activeHistoryId;
      if (id) {
        historyStore.touch(id, { visualMode: mode });
        if (useAuthStore.getState().user !== null) {
          void touchServerHistory(id, { visualMode: mode });
        }
      }
    },

    // Dọn RUNTIME — lịch sử bền KHÔNG bị đụng (hai đời sống tách biệt, M9-UX1).
    /* `reset` là "về trạng thái sạch" (dùng ở test và thoát hẳn). Khác
       `goHome`: goHome giữ lịch sử hiển thị, reset dọn cả bàn làm việc. */
    reset: () => {
      hasHydratedLocation = false;
      set({
        active: null,
        unsupported: null,
        analysisError: null,
        clientFailure: null,
        routeFailure: null,
        validRouteStack: ["home"],
        hasInAppNavigation: false,
        returnView: "home",
        activeSampleId: null,
        playing: false,
        exploreOpen: false,
        visualMode: "2d",
        view: "home",
        activeHistoryId: null,
        history: historyStore.list(),
      });
    },
  };
});

/* Đồng bộ lịch sử theo tài khoản khi trạng thái đăng nhập thay đổi. */
useAuthStore.subscribe((state, prevState) => {
  const prevId = prevState.user?.id ?? null;
  const nextId = state.user?.id ?? null;
  if (prevId === nextId) return;
  if (nextId === null) {
    historyStore.clear();
    useAppStore.setState({ history: [], activeHistoryId: null });
    return;
  }
  void fetchServerHistory().then((items) => {
    if (items === null) return;
    if (useAuthStore.getState().user?.id !== nextId) return;
    historyStore.replaceAll?.(items);
    useAppStore.setState({ history: historyStore.list() });
  });
});
