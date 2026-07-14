/**
 * Tầng trừu tượng mô phỏng — simulation_id là chuẩn định danh mới.
 *
 * RANH GIỚI CỨNG (yêu cầu #1):
 * - LLM chỉ sinh `SimulationEnvelope` (simulation_id + config) và config phải
 *   qua `validateConfig` trước khi chạm engine.
 * - Timeline, state transition, kết quả, hoạt cảnh do CHÍNH module sinh ra
 *   trong `init`/`apply` — tất định 100%, LLM không bao giờ là source of truth.
 *
 * BA TẦNG DỮ LIỆU (yêu cầu #3):
 *   config (bất biến, từ LLM/bài mẫu đã validate)
 *   → state (engine sở hữu; mọi biến đổi qua pure function của module)
 *   → render model (renderer 2D/3D chỉ ĐỌC state — không business logic,
 *     nhờ đó đổi 2D⇄3D giữ nguyên bước hiện tại).
 */

import type { ComponentType } from "react";

export type Domain =
  | "algorithm"
  | "binary"
  | "logic"
  | "network"
  | "database"
  | "web"
  | "geometry"
  | "generic";

export type VisualMode = "2d" | "3d" | "hybrid";

/** Hai loại mô phỏng (RULES/mục 19): progressive có timeline, exploratory không. */
export type InteractionMode = "progressive" | "exploratory" | "hybrid";

export type ConfigResult<C> = { ok: true; config: C } | { ok: false; error: string };

/**
 * Tương tác của người học — module nào không hỗ trợ action nào thì trả về
 * state cũ (no-op), không ném lỗi.
 */
export type SimAction =
  | { type: "whatif_swap"; i: number; j: number }
  | { type: "exit_branch" }
  | { type: "toggle"; target: string }
  | { type: "set_param"; name: string; value: number | string | boolean }
  /** M7.13A: kéo một object tới tọa độ domain 0–100 — engine kiểm quyền
   *  (spec khai drag + visible) và clamp constraints; renderer chỉ phát action. */
  | { type: "move"; target: string; x: number; y: number };

/**
 * Capability tùy chọn (yêu cầu #2): chỉ mô phỏng progressive/hybrid khai báo.
 * Exploratory (vd logic.and_gate) KHÔNG có trường này — không phải giả vờ
 * có "1 bước". UI chỉ hiện Next/Prev/Play khi capability tồn tại.
 */
export interface TimelineCapability<S> {
  stepCount(state: S): number;
  currentStep(state: S): number;
  /** Trả về state MỚI (pure); index tự clamp về [0, stepCount-1]. */
  goToStep(state: S, step: number): S;
}

/**
 * Props chung cho Workspace/Inspector của mọi module (yêu cầu #3):
 * renderer chỉ ĐỌC config + state và phát SimAction qua dispatch —
 * không chứa business logic, không tự biến đổi state.
 */
export interface WorkspaceProps<C = unknown, S = unknown> {
  config: C;
  state: S;
  /** true khi trình phát đang tự chạy — workspace nên khóa tương tác nặng. */
  busy: boolean;
  dispatch: (action: SimAction) => void;
}

/**
 * Capability chỉnh sửa (M7.14D) — module KHÔNG khai thì UI **không** có công cụ
 * sửa cấu trúc (mặc định an toàn: 4 domain chuyên biệt tự động không có toolbar).
 * Cùng khuôn với `timeline?`: UI hỏi capability, không tự giả định.
 * Nội dung policy do domain tự định nghĩa (generic: xem `generic/edit-policy.ts`).
 */
export interface EditPolicyLike {
  /** Thao tác UI được phép (rỗng = không có công cụ sửa cấu trúc). */
  uiActions: string[];
  /** Patch op được phép ở tầng validate. */
  allowedOps: string[];
}

export interface EditCapability<C = unknown, S = unknown> {
  /** Suy policy TỪ CONFIG/STATE hiện tại — không phải hằng số của module. */
  policyOf(config: C, state: S): EditPolicyLike;
}

/* ── PredictionCapability (M8-PRE-LIP) ────────────────────────────────────
 *
 * BẰNG CHỨNG TƯƠNG TÁC HỌC TẬP, KHÔNG PHẢI practice_activity đầy đủ.
 * Vòng lặp: Quan sát → Dự đoán/Chọn → Nộp → ENGINE TẤT ĐỊNH chấm → phản hồi là
 * DỮ LIỆU KẾT QUẢ (không phải chat) → mô phỏng canonical KHÔNG đổi.
 *
 * Cùng khuôn `timeline?` / `edit?`: module KHÔNG khai → UI KHÔNG có affordance
 * dự đoán (mặc định an toàn, không module nào phải sửa).
 *
 * RÀNG BUỘC CỨNG:
 * - `challenge` và `check` là HÀM THUẦN, chấm bằng ENGINE/TRACE có sẵn.
 * - TUYỆT ĐỐI KHÔNG gọi LLM (CORRECTNESS.md §1.6: LLM không bao giờ là judge).
 * - Không chứng minh được đúng/sai → "unsupported_to_verify", KHÔNG phán bừa.
 * - `check` KHÔNG được đổi state canonical (học sinh sai vẫn không phá dòng chính).
 */

export interface PredictionOption {
  id: string;
  label: string;
}

export interface PredictionChallenge {
  /** Câu hỏi TẤT ĐỊNH sinh từ state hiện tại. */
  question: string;
  /** 2 lựa chọn (có/không) hay N lựa chọn (chọn nút) — contract không bó vào một kiểu. */
  options: PredictionOption[];
}

export type PredictionVerdict = "correct" | "incorrect" | "unsupported_to_verify";

export interface PredictionResult {
  verdict: PredictionVerdict;
  /** Đáp án học sinh chọn. */
  answerId: string;
  /** Đáp án chuẩn — CHỈ đặt khi engine CHỨNG MINH được. */
  expectedId?: string;
  /** Giải thích TẤT ĐỊNH (do engine dựng, không phải hội thoại). */
  message: string;
}

export interface PredictionCapability<S = unknown> {
  /** null = ở trạng thái này không có gì để dự đoán (hết bước / không phải điểm quyết định). */
  challenge(state: S): PredictionChallenge | null;
  /** Chấm TẤT ĐỊNH, PURE — không đổi state canonical. */
  check(state: S, answerId: string): PredictionResult;
}

export interface SimulationModule<C = unknown, S = unknown> {
  /** Định danh chuẩn: "<domain>.<tên>", vd "algorithm.find_max". */
  id: string;
  domain: Domain;
  /** Tên hiển thị trong catalog, tiếng Việt. */
  title: string;
  interactionMode: InteractionMode;
  supportedVisualModes: VisualMode[];

  /** Chốt chặn config từ LLM — sai là từ chối, không "cố chạy". */
  validateConfig(raw: unknown): ConfigResult<C>;

  /** Engine tất định: progressive tính sẵn TOÀN BỘ timeline ngay tại đây. */
  init(config: C): S;

  /** Tương tác người học (what-if, toggle, đổi tham số) — pure function. */
  apply(state: S, action: SimAction): S;

  /** Optional (yêu cầu #2) — điều khiển bước cho progressive/hybrid. */
  timeline?: TimelineCapability<S>;

  /** Optional (M7.14D) — chỉnh sửa cấu trúc. Không khai = không có edit. */
  edit?: EditCapability<C, S>;

  /**
   * Optional (M8-PRE-LIP) — nhịp DỰ ĐOÁN của người học. Không khai = UI không
   * hiện ô dự đoán. Ground truth lấy từ chính engine tất định (trace/BFS).
   */
  predict?: PredictionCapability<S>;

  /**
   * Yêu cầu #4: snapshot JSON sạch (serializable, nhỏ) mô tả trạng thái thật
   * để gửi /api/explain. KHÔNG BAO GIỜ gửi Zustand/React/Three.js object.
   */
  getExplainContext(state: S, config: C): Record<string, unknown>;

  /**
   * Sân khấu chính của mô phỏng — bắt buộc. Chỉ domain UI này được biết
   * ruột state của mình; core UI (SimulationWorkspace) render qua đây,
   * không được giả định mọi simulation là thuật toán/có trace/mảng.
   */
  Workspace: ComponentType<WorkspaceProps<C, S>>;

  /** Panel quan sát bên phải — nội dung theo domain (biến/mã giả, truth table, bit...). */
  Inspector?: ComponentType<WorkspaceProps<C, S>>;
}

/** Vỏ chung mọi domain — đầu ra hợp lệ duy nhất của pipeline LLM. */
export interface SimulationEnvelope {
  status: "ok";
  simulation_id: string;
  domain: Domain;
  visual_mode: VisualMode;
  title: string;
  description: string | null;
  /** Ruột theo schema riêng của domain — validate 2 tầng (backend + module). */
  config: unknown;
  notes: string | null;
  /** Kết quả stage analyze của pipeline (nếu đến từ /api/analyze) — chỉ để hiển thị. */
  analysis?: unknown;
}
