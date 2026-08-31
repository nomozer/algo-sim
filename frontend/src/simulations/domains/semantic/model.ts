/**
 * Engine phía frontend cho route sinh ngữ nghĩa `generic.semantic_program`.
 *
 * KHÁC HẲN các module miền khác: ở đây engine tất định đã chạy XONG ở backend
 * (`SemanticProgramInterpreter`), và envelope mang sẵn TOÀN BỘ chuỗi khung. Việc
 * của module này chỉ là *đọc* — nó KHÔNG tính lại bước, KHÔNG đánh giá lại biểu
 * thức, KHÔNG suy diễn trạng thái ngữ nghĩa.
 *
 * Đó chính là bất biến #31: khung thứ k suy hoàn toàn từ trạng thái bước k.
 * Renderer được nội suy PIXEL giữa hai khung (trượt con trỏ, đổi màu dần) —
 * nhưng mọi GIÁ TRỊ hiển thị phải đọc từ một khung có thật.
 *
 * Lỗi mà thiết kế này chặn: bản cũ chỉ nhận khung ĐẦU rồi phát narration chạy,
 * nên lời kể tới bước 15 trong khi ngăn xếp trên hình vẫn rỗng.
 */

export interface SemanticObject {
  id: string;
  type: string;
  label?: string;
  items?: unknown[];
  /**
   * Giá trị hộp — **SCALAR đã định dạng** cho người đọc (`"√3"`, `"3/5"`,
   * `"(1, 2, 3)"`), hoặc một số/chuỗi thường với bài Tin học.
   *
   * ⚠️ KHÔNG phải đối tượng runtime. Backend từng đặt thẳng `Vec3`/`Fraction`
   * vào đây; envelope khi ấy không `json.dumps` được và cả lượt phân tích chết
   * ở bước ghi cache — sau khi mọi cổng đã báo thành công. Nay biên vận chuyển
   * (`semantic_program/transport.py`) đảm bảo nó luôn là scalar, nên
   * `String(value)` an toàn và không bao giờ ra `[object Object]`.
   */
  value?: unknown;
  /**
   * CẤU TRÚC chính xác đi kèm, khi giá trị là số chính xác hay vật hình học:
   * `{kind:"rational"|"radical"|"vec3", …}`. `value` là DẪN XUẤT của nó.
   *
   * Vắng mặt khi giá trị vốn đã là JSON thường — bọc một `int` vào một dict
   * chỉ để "cho đồng bộ" là dựng hình dạng thứ hai cho cùng một thứ.
   */
  exact?: { kind: string; [k: string]: unknown };
  target?: string;
  target_index?: number;
  capacity?: number;
  /* ── `graph_view` (2026-08-21) ──────────────────────────────────────────
     Cả bốn trường đều do BACKEND đọc từ `memory_snapshot` rồi gửi xuống.
     Renderer KHÔNG được suy ra `visited` bằng cách tự chạy lại BFS/DFS —
     làm thế là dựng engine thứ hai ở tầng trình bày (R0 cấm). Không khai
     `visited_ref`/`current_ref` thì hai trường dưới vắng mặt, và đồ thị vẽ
     không tô trạng thái. */
  nodes?: string[];
  edges?: string[][];
  visited?: string[];
  current?: string | null;
  /* ── `map_view` (2026-08-23) ────────────────────────────────────────────
     Cặp khoá→giá trị, ĐÃ SẮP THEO KHOÁ ở backend. Renderer không sắp lại và
     không tự suy: thứ tự chèn phụ thuộc lượt chạy nên hai lần chụp cùng một
     bài sẽ cho hình khác nhau. Cùng luật với `nodes`/`edges`. */
  entries?: [string, unknown][];
}

export interface SemanticFrame {
  step_index: number;
  narration: string;
  objects: SemanticObject[];
  highlighted_object_ids?: string[];
}

export interface SemanticViewStep {
  view_index: number;
  frame_lo: number;
  frame_hi: number;
  narration: string;
}

export interface SemanticConfig {
  spec_version: string;
  title: string;
  frames: SemanticFrame[];
  view_steps: SemanticViewStep[];
  grouping_level: "step" | "iteration";
  presentation_overflow: boolean;
  execution_truncated: boolean;
}

export interface SemanticStep {
  viewIndex: number;
  narration: string;
  objects: SemanticObject[];
  highlighted: string[];
}

export interface SemanticState {
  cursor: number;
  timeline: SemanticStep[];
  groupingLevel: "step" | "iteration";
  /** Chạm trần trình bày — shell phải KHAI, không im lặng (§4.3). */
  presentationOverflow: boolean;
  /** Chạm trần thực thi — cấm cắt câm (luật cứng #12). */
  executionTruncated: boolean;
}

export type ConfigResult<C> = { ok: true; config: C } | { ok: false; error: string };

function laDay(x: unknown): x is unknown[] {
  return Array.isArray(x);
}

/**
 * Chốt chặn config — sai là TỪ CHỐI, không "cố chạy".
 *
 * Kiểm luôn bất biến #32 ở phía nhận: các đoạn bước xem phải phân hoạch đầy đủ
 * dãy khung, không chồng lấn, không trỏ ra ngoài. Backend đã bảo đảm, nhưng một
 * envelope tới đây có thể đến từ lịch sử đã lưu hoặc bài mẫu — kiểm hai đầu thì
 * hợp đồng mới thật sự là hợp đồng.
 */
export function validateSemanticConfig(raw: unknown): ConfigResult<SemanticConfig> {
  if (!raw || typeof raw !== "object") return { ok: false, error: "Cấu hình rỗng." };
  const c = raw as Partial<SemanticConfig>;

  if (!laDay(c.frames) || c.frames.length === 0) {
    return { ok: false, error: "Mô phỏng không có khung hình nào." };
  }
  if (!laDay(c.view_steps) || c.view_steps.length === 0) {
    return { ok: false, error: "Mô phỏng không có bước xem nào." };
  }

  const n = c.frames.length;
  const steps = [...(c.view_steps as SemanticViewStep[])].sort(
    (a, b) => a.frame_lo - b.frame_lo,
  );

  if (steps[0].frame_lo !== 0 || steps[steps.length - 1].frame_hi !== n - 1) {
    return { ok: false, error: "Các bước xem không phủ hết chuỗi khung hình." };
  }
  for (let i = 0; i < steps.length; i += 1) {
    const s = steps[i];
    if (s.frame_lo < 0 || s.frame_hi >= n || s.frame_lo > s.frame_hi) {
      return { ok: false, error: "Bước xem trỏ ra ngoài chuỗi khung hình." };
    }
    if (i > 0 && s.frame_lo !== steps[i - 1].frame_hi + 1) {
      return { ok: false, error: "Các bước xem chồng lấn hoặc bỏ sót khung hình." };
    }
  }

  return { ok: true, config: c as SemanticConfig };
}

/**
 * Dựng timeline từ config.
 *
 * Mỗi bước xem đọc khung **CUỐI** đoạn nó phủ — đó là trạng thái người học nhìn
 * thấy sau khi đoạn ấy chạy xong. Không nội suy, không trộn khung.
 */
export function buildSemanticState(raw: unknown): SemanticState {
  const c = raw as SemanticConfig;
  const timeline: SemanticStep[] = (c.view_steps ?? []).map((vs) => {
    const frame = c.frames[vs.frame_hi] ?? c.frames[c.frames.length - 1];
    return {
      viewIndex: vs.view_index,
      narration: vs.narration,
      objects: frame?.objects ?? [],
      highlighted: frame?.highlighted_object_ids ?? [],
    };
  });

  return {
    cursor: 0,
    timeline,
    groupingLevel: c.grouping_level ?? "step",
    presentationOverflow: Boolean(c.presentation_overflow),
    executionTruncated: Boolean(c.execution_truncated),
  };
}

export function stepCount(state: SemanticState): number {
  return state.timeline.length;
}

export function goToStep(state: SemanticState, step: number): SemanticState {
  const max = Math.max(0, state.timeline.length - 1);
  const cursor = Math.min(Math.max(0, step), max);
  return cursor === state.cursor ? state : { ...state, cursor };
}
