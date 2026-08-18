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
  | "color"
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
  | { type: "net_reset" }
  | { type: "step"; delta?: number };

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

/* ── W13 — KHÔNG CÒN `PredictionCapability` ───────────────────────────────
 *
 * Từ M8-PRE-LIP tới W12, module khai được một nhịp *hỏi → nộp → engine chấm
 * đúng/sai*. W4B-2U2 đã DỜI nó ra sau cổng Thử thách; W13 **gỡ hẳn**.
 *
 * Lý do là ranh giới sản phẩm, không phải kĩ thuật: đây là hệ **mô phỏng tương
 * tác**, nơi học sinh tác động lên mô hình rồi ĐỌC hệ quả tất định — không phải
 * hệ hỏi-đáp có chấm điểm. Một câu hỏi hai lựa chọn dạy học sinh đoán đáp án;
 * `explore` → `apply` bắt học sinh đổi chính mô hình rồi nhìn cơ chế trả lời.
 *
 * Thay bằng: `explore?` (lối vào + câu mời) + `apply` của từng miền. Không bề
 * mặt học sinh nào còn phát ngôn đúng/sai — khoá bởi `no-verdict.test.ts`.
 *
 * ⚠️ ĐỪNG khôi phục "cho gọn". `InteractionFeedback` của miền generic là thứ
 * KHÁC: engine phản hồi một thao tác có phạm vi hợp lệ (bất biến #11/#12), nó
 * ở lại.
 */

/**
 * Câu mời của một lối vào phụ. Chỉ TRÌNH BÀY — không mang ngữ nghĩa, không
 * quyết định gì; shell chỉ đọc để đặt chữ lên nút.
 */
export interface PresentationEntry {
  /**
   * TÊN KHẢ TRUY CẬP đầy đủ — tự mô tả năng lực nằm sau cổng ("Thí nghiệm: tự
   * chọn nửa để tìm tiếp"). Luôn tới được chuột và công nghệ hỗ trợ.
   */
  label: string;
  /**
   * W4B-3B — NHÃN NGẮN HIỂN THỊ trong dải điều khiển ("Khám phá" / "Thử thách").
   *
   * Vì sao tách khỏi `label`: đo được ở 1366×768, hai nhãn đầy đủ cộng với
   * transport + tốc độ + gợi ý phím làm dải điều khiển XUỐNG DÒNG thành băng
   * thứ hai — và điều đó xảy ra **kể cả khi chỉ có một phiên**, tức nó không
   * phải hệ quả của cột phiên cũ mà là quá tải của chính dải này.
   *
   * Chữ mô tả KHÔNG bị vứt đi: `label` (+ `hint`) vào `title`/`aria-label`, và
   * khung giải thích đầy đủ hiện ra KHI MỞ chế độ. Bất biến PhET/CLT "cổng phải
   * tự mô tả" vẫn giữ — nó nói về việc người dùng ĐỌC ĐƯỢC mục đích, không bắt
   * mọi chữ phải chiếm chỗ trong dải điều khiển.
   *
   * Không khai ⇒ hiện `label` như cũ.
   */
  shortLabel?: string;
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
  /**
   * W4B-3H — VÌ SAO bước này chưa dùng được. Một nút mờ mà không nói lý do thì
   * người học đọc ra là "hỏng", không đọc ra là "chưa tới lúc" — và họ không có
   * cách nào biết phải làm gì để nó sáng lên.
   *
   * Không khai ⇒ shell dùng câu chung. Câu này đi vào `title`/`aria-label` khi
   * nút đang mờ, nên nó tới được cả chuột lẫn công nghệ hỗ trợ mà không tốn
   * một dòng bố cục nào.
   */
  unavailableHint?: string;
}

/**
 * W4B-3A — KHÁM PHÁ: thao tác trực tiếp lên mô hình.
 *
 * W13 — nay là năng lực tương tác học tập DUY NHẤT. Năng lực chị em của nó
 * (`predict`: học sinh cam kết một quyết định rồi engine phán đúng/sai) đã bị
 * gỡ hẳn, vì đây là hệ mô phỏng tương tác chứ không phải hệ hỏi-đáp.
 *
 * Nguyên tắc còn lại: học sinh ĐỔI mô hình (kéo đổi chỗ, ngắt một liên kết
 * mạng, đổi điều kiện lọc), rồi `module.apply` tính lại hệ quả. KHÔNG có đúng/
 * sai nào được phán — **hệ quả tất định LÀ câu trả lời**.
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
   * Optional (W4B-3A) — chế độ KHÁM PHÁ: học sinh đổi mô hình, `apply` tính lại.
   * Không khai = không có lối vào khám phá (mặc định an toàn, cùng khuôn
   * `timeline?` / `edit?`). Khai KHÔNG tạo ra thao tác nào — thao tác vẫn do
   * renderer miền dựng; đây chỉ là lối vào và câu mời.
   *
   * W13 — đây nay là ĐƯỜNG DUY NHẤT để học sinh tác động lên mô hình. Không có
   * đường thứ hai nào đi qua chấm điểm.
   */
  explore?: ExploreCapability<S>;

  /**
   * (SHELL-N) Thuyết minh bước hiện tại — shell render, module chỉ cấp chữ.
   * `null` = bước này không có gì để nói (vd bước cuối đã có băng kết quả nói
   * đúng câu đó rồi — hiện hai lần làm học sinh tưởng là hai thông tin khác).
   * Module KHÔNG khai = shell không dựng khe (mặc định an toàn, cùng khuôn
   * `timeline?` / `explore?`).
   */
  narrate?(state: S, config: C): Narration | null;

  /**
   * W4B-4D — CẤU HÌNH MÀ MÔ HÌNH ĐANG CHẠY, để shell biết nó đã RỜI KHỎI ĐỀ.
   *
   * Từ khi các bài cho đổi tham số có ràng buộc, tiêu đề của đề và mô hình trên
   * màn hình có thể nói hai điều khác nhau: đề viết "đếm học sinh từ 8,0 trở
   * lên" trong khi học sinh vừa kéo ngưỡng về 6, và con số cuối cùng đọc như đáp
   * số của bài gốc. Đó không phải chuyện thẩm mỹ — màn hình đang khẳng định một
   * điều sai.
   *
   * Shell so cái này với `active.config` (bản đã validate, BẤT BIẾN) và nói ra
   * khi hai bên lệch. Module KHÔNG khai ⇒ không so, không nhãn: bài không đổi
   * được tham số thì không bao giờ lệch được.
   *
   * Trả về cái gì cũng được miễn SO SÁNH ĐƯỢC bằng giá trị (shell dùng JSON) và
   * cùng dạng với `active.config` — thường chỉ là `state.config`.
   */
  currentConfig?(state: S): unknown;

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
