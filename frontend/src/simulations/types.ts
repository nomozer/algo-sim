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
  | "tree"
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
  | { type: "move"; target: string; x: number; y: number }
  /* W4B-2I — THÍ NGHIỆM CẤU TRÚC (mạng). Đổi MÔ HÌNH rồi để engine tính lại,
   * khác hẳn `toggle`/`set_param` vốn chỉ đổi giá trị trong một mô hình đứng yên.
   * Tham chiếu là VAI NGỮ NGHĨA (id nút), không phải nhãn theo ngữ cảnh đề bài,
   * nên cùng bộ công cụ chạy được cho mạng trường học lẫn mạng văn phòng (§48). */
  | { type: "net_connect"; a: string; b: string }
  | { type: "net_disconnect"; a: string; b: string }
  /** Về đúng topology đã validate lúc nạp — không phải "undo" từng bước. */
  | { type: "net_reset" };

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
  /**
   * Optional (INTERACTION-FAMILY W1) — bước này đã được trình bày NGAY TRÊN SÂN
   * KHẤU, nên shell KHÔNG dựng UI dự đoán dùng chung nữa.
   *
   * Dùng khi cùng một cam kết được diễn đạt bằng HÀNH ĐỘNG lên chính đối tượng
   * (vd đặt phần tử vào ô tích luỹ) thay vì bằng một câu hỏi Có/Không: đó vẫn là
   * một dự đoán, chỉ khác hình thức, nên nó vẫn đi qua `check` — engine tất định
   * vẫn là bên duy nhất phán đúng/sai (bất biến #11).
   *
   * KHÔNG khai = shell dựng UI dùng chung như cũ. Không được để hai hình thức
   * cùng hỏi một câu trên một màn hình.
   */
  presentedInStage?(state: S): boolean;

  /**
   * W4B-3A — NHÃN CỦA LỐI VÀO THỬ THÁCH, do module cấp.
   *
   * Shell sở hữu *chỗ đặt* lối vào (dải hành động phụ cạnh transport) và *cờ
   * mở/đóng*; module sở hữu *câu mời*. Trước wave này shell viết cứng một câu
   * ("Thử thách: tự dự đoán bước này") cho mọi target, nên họ thuật toán phải
   * tự dựng lấy một nút thứ hai mới nói được đúng cơ chế của mình ("tự chọn nửa
   * để tìm tiếp") — và cái nút thứ hai ấy chính là dải `experimentTrigger`.
   *
   * DẪN XUẤT TỪ CONFIG/STATE, không từ tiêu đề đề bài (anti-pattern #2).
   * `null` = ở trạng thái này không có gì để mời. Không khai = shell dùng câu
   * mặc định (tương thích ngược).
   */
  entry?(state: S, config: unknown): PresentationEntry | null;
}

/**
 * Câu mời của một lối vào phụ. Chỉ TRÌNH BÀY — không mang ngữ nghĩa, không
 * quyết định gì; shell chỉ đọc để đặt chữ lên nút.
 */
export interface PresentationEntry {
  /** Nhãn nút, tiếng Việt, tự mô tả năng lực nằm sau nó. */
  label: string;
  /** Nhãn khi đang mở (đóng lại). Không khai → shell tự dựng "Đóng …". */
  closeLabel?: string;
  /** Câu mời-thử ngắn — vào `title`/`aria-label`, không tốn một dòng bố cục. */
  hint?: string;
  /**
   * `false` = có năng lực nhưng BƯỚC NÀY không dùng được ⇒ nút MỜ ĐI, **không**
   * biến mất.
   *
   * Vì sao không đơn giản trả `null` cho những bước đó: đo trên chính danh mục
   * offline, số bước mời được là 4/13 (binary_search) đến 21/40 (bubble_sort) —
   * tức nút sẽ NHẤP NHÁY vào/ra khỏi dải điều khiển mỗi lần học sinh bấm Tiến.
   * Một control nhảy chỗ khó dùng hơn hẳn một control mờ, và dải này đã có sẵn
   * đúng thành ngữ ấy: các nút transport dùng `disabled` chứ không tự gỡ mình.
   *
   * `null` (không phải `available: false`) vẫn dành cho ca khác hẳn: module
   * KHÔNG có chế độ này ở bài này (vd `sum_if` không có Khám phá vì kéo ở đó là
   * trang trí). Không năng lực ⇒ không nút; có năng lực ⇒ nút luôn ở đó.
   */
  available?: boolean;
}

/**
 * W4B-3A — KHÁM PHÁ (thao tác trực tiếp lên mô hình), TÁCH KHỎI THỬ THÁCH.
 *
 * VÌ SAO LÀ MỘT NĂNG LỰC RIÊNG, không gộp vào `predict`. Hai thứ này khác nhau
 * ở chỗ AI PHÁN XÉT:
 *
 * - `predict` = học sinh CAM KẾT một quyết định của thuật toán, và
 *   `predict.check` (engine tất định) phán đúng/sai;
 * - `explore` = học sinh ĐỔI mô hình (kéo đổi chỗ, ngắt một liên kết mạng), rồi
 *   `module.apply` tính lại hệ quả. KHÔNG có đúng/sai nào được phán — hệ quả
 *   tất định LÀ câu trả lời.
 *
 * Trước wave này cả hai nằm sau CÙNG một nút "Thí nghiệm" do domain tự dựng, nên
 * sản phẩm không có chỗ nào nói được rằng chúng là hai việc khác nhau — và một
 * nút mở hai thứ khác loại thì học sinh học sai luôn cả hai.
 *
 * Năng lực này KHÔNG sở hữu ngữ nghĩa: nó chỉ khai *có chế độ khám phá không* và
 * *mời bằng câu gì*. Bộ điều khiển cụ thể (kéo cột, bấm liên kết) vẫn do renderer
 * miền dựng, và mọi biến đổi vẫn đi qua `module.apply`.
 */
export interface ExploreCapability<S = unknown> {
  /**
   * `null` = ở trạng thái này không có gì để khám phá (vd bước cuối, hoặc bài mà
   * thao tác trực tiếp là trang trí). Shell không dựng lối vào rỗng.
   */
  entry(state: S, config: unknown): PresentationEntry | null;
}

/* ── NarrationCapability (SHELL-N) ────────────────────────────────────────
 *
 * KHE CỦA SHELL, CHỮ CỦA MODULE.
 *
 * Trước bản này, "thuyết minh bước hiện tại" là quy ước tự nguyện: mỗi module tự
 * dựng lấy, bằng BA cách khác nhau (`.narration-bar`, `.notes` của logic, và một
 * bản riêng trong table-module). Hệ quả đo được ở lượt audit UI baseline: hai
 * trong năm module đại diện có `narration_bar_count = 0` dù vẫn hiện một câu
 * thuyết minh — cùng vai trò, khác hiện thực, khác vị trí, và KHÔNG có gì bắt
 * module thứ 23 phải có thuyết minh.
 *
 * Nay shell cấp đúng MỘT khe ngay dưới sân khấu; module chỉ trả CHUỖI cho bước
 * hiện tại. Renderer 2D và 3D của cùng một module vì thế kể cùng một câu mà
 * không cần chép hai lần (trước đây `network/ui.tsx` và `network/ui3d.tsx` có
 * hai dòng narration song song — đúng thứ dễ trôi khỏi nhau).
 *
 * KHÔNG đụng engine/state/trace: `narrate` là hàm THUẦN, chỉ ĐỌC state.
 */
export interface Narration {
  /** Câu thuyết minh cho bước hiện tại. */
  text: string;
  /**
   * true = câu này nói về THAO TÁC CỦA HỌC SINH (vd what-if đổi chỗ), không phải
   * bước canonical của engine. Shell đánh dấu khác đi để học sinh không nhầm
   * "việc em vừa làm" với "thuật toán đang làm".
   */
  fromLearner?: boolean;
}

/**
 * M10 — vai trò của renderer 3D. Phân biệt TRUNG THỰC:
 * - "architectural_poc": 3D chứng minh dùng chung renderer, nhưng chiều sâu (Z)
 *   chỉ là BỐ CỤC (vd tách nút trên/ngoài tuyến) — không mang nghĩa khái niệm.
 * - "pedagogical": Z mã hoá một biến khái niệm thật (vd tầng giao thức).
 * Không khai = module không có 3D hoặc chưa phân loại.
 */
/**
 * Tiêu chí PHÙ HỢP SƯ PHẠM của một biểu diễn (W4B-2S §1).
 *
 * VÌ SAO CÓ KIỂU NÀY. W4B-2R phán 3D bằng đúng một câu hỏi — *"Z có mã hoá một
 * biến khái niệm không?"* — và câu đó QUÁ HẸP: nó loại 3D ngay cả khi chiều sâu
 * giúp nhận ra vật thể, thấy quan hệ, hay thao tác dễ hơn. Nay biện minh phải
 * nêu ĐÍCH DANH nó thắng ở tiêu chí nào, nên "sản phẩm đã có renderer 3D" và
 * "Z không phải biến" đều không còn là câu trả lời hợp lệ.
 */
export type PedagogicalFit =
  | "object_recognition"
  | "role_discrimination"
  | "relation_clarity"
  | "transition_clarity"
  | "direct_manipulation_fit"
  | "mechanism_fidelity"
  | "dimensional_value";

/**
 * W4B-2V — VỊ THẾ CỦA BIỂU DIỄN THAY THẾ.
 *
 * Phân biệt phải giữ: **CHẾ ĐỘ RENDER ĐƯỢC HỖ TRỢ** ≠ **BIỂU DIỄN CHÍNH CỦA
 * HỌC SINH**. Một target có thể có hai renderer mà chỉ bày MỘT cái ở luồng học
 * bình thường. Bày `[2D] [3D]` chỉ vì hai renderer cùng tồn tại là đem một chi
 * tiết cài đặt lên làm quyết định của học sinh — trong khi học sinh chưa hiểu
 * cơ chế thì không có cơ sở nào để chọn.
 */
export type AlternateRepresentationStatus =
  | "NO_ALTERNATE_NEEDED"
  | "ALTERNATE_FOR_EXPLANATION"
  | "ALTERNATE_FOR_COMPARISON"
  | "ALTERNATE_FOR_ACCESSIBILITY"
  | "DUAL_VIEW_CORE_TO_MECHANISM";

/** Khai vị thế biểu diễn. Chỉ target có >1 renderer mới cần khai. */
export interface RepresentationIntent {
  /** Biểu diễn học sinh thấy ở luồng bình thường — HỆ quyết, không phải học sinh. */
  primary: VisualMode;
  alternate: AlternateRepresentationStatus;
  /** Vì sao biểu diễn thay thế đáng tồn tại; bắt buộc khi alternate ≠ NO_ALTERNATE_NEEDED. */
  alternateReason?: string;
}

export interface ThreeDMeaning {
  role: "architectural_poc" | "pedagogical";
  /** Trục sâu (Z) mã hoá điều gì — tiếng Việt, dùng cho caption + test trung thực. */
  meaningOfZ: string;
  /**
   * Các tiêu chí mà 3D THẮNG rõ so với 2D ở bài này. Rỗng/thiếu ⇒ không đủ tư
   * cách bày cho học sinh (guard toàn danh mục chặn). Chỉ target thật sự có 3D
   * mới phải khai — không bắt 22 module điền một trường vô nghĩa.
   */
  pedagogicalFit?: PedagogicalFit[];
  /** Vì sao 2D KHÔNG diễn đạt được điều đó — buộc so sánh, không chỉ khen 3D. */
  whyNot2d?: string;
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
   * Optional (W4B-3A) — chế độ KHÁM PHÁ: học sinh đổi mô hình, `apply` tính lại.
   * Không khai = không có lối vào khám phá (mặc định an toàn, cùng khuôn
   * `timeline?` / `predict?`). Khai KHÔNG tạo ra thao tác nào — thao tác vẫn do
   * renderer miền dựng; đây chỉ là lối vào và câu mời.
   */
  explore?: ExploreCapability<S>;

  /**
   * (SHELL-N) Thuyết minh bước hiện tại — shell render, module chỉ cấp chữ.
   * `null` = bước này không có gì để nói (vd bước cuối đã có băng kết quả nói
   * đúng câu đó rồi — hiện hai lần làm học sinh tưởng là hai thông tin khác).
   * Module KHÔNG khai = shell không dựng khe (mặc định an toàn, cùng khuôn
   * `timeline?` / `predict?`).
   */
  narrate?(state: S, config: C): Narration | null;

  /**
   * Yêu cầu #4: snapshot JSON sạch (serializable, nhỏ) mô tả trạng thái thật
   * để gửi /api/explain. KHÔNG BAO GIỜ gửi Zustand/React/Three.js object.
   */
  getExplainContext(state: S, config: C): Record<string, unknown>;

  /**
   * Sân khấu chính của mô phỏng — bắt buộc. Chỉ domain UI này được biết
   * ruột state của mình; core UI (SimulationWorkspace) render qua đây,
   * không được giả định mọi simulation là thuật toán/có trace/mảng.
   * Đây đồng thời là RENDERER 2D mặc định (xem `renderers` bên dưới).
   */
  Workspace: ComponentType<WorkspaceProps<C, S>>;

  /**
   * Optional (M8) — renderer theo visual mode, CÙNG hợp đồng WorkspaceProps:
   * đọc CÙNG config/state, phát CÙNG SimAction. "2d" không khai thì mặc định
   * là `Workspace` (tương thích ngược — không module nào phải sửa).
   *
   * RÀNG BUỘC:
   * - 3D là MỘT RENDERER, không phải domain mới: không có simulation_id "_3d",
   *   không fork engine — 2D/3D dùng chung config/state/timeline/action.
   * - Một mode chỉ KHẢ DỤNG khi vừa nằm trong `supportedVisualModes` vừa có
   *   renderer thật (xem `availableVisualModes` — chống toggle giả).
   * - Bố cục/camera/mesh của renderer là dữ liệu TRÌNH BÀY, renderer tự giữ —
   *   cấm đưa vào engine state (bất biến renderer-neutral, M7.FREEZE).
   */
  renderers?: Partial<Record<VisualMode, ComponentType<WorkspaceProps<C, S>>>>;

  /**
   * M10 — tuyên bố TRUNG THỰC về nghĩa của chiều sâu 3D (chỉ khai khi có 3D).
   * Khoá bằng test: PoC không được giả vờ có nghĩa khái niệm.
   */
  threeD?: ThreeDMeaning;

  /**
   * W4B-2V: vị thế biểu diễn. Vắng ⇒ suy an toàn: mode duy nhất là chính,
   * không có biểu diễn thay thế ⇒ KHÔNG bày công tắc.
   */
  representation?: RepresentationIntent;

  /** Panel Giải thích bên phải — nội dung theo domain (biến/mã giả, truth table, bit...). */
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
