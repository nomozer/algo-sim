import { registerSimulation } from "../../registry";
import type { ConfigResult, SimAction, SimulationModule } from "../../types";
import { applyStyleChange, cssTextOf, isModified } from "./apply";
import type { WebConfig, WebState, WebStyle } from "./model";
import { WebInspector, WebWorkspace } from "./ui";

/**
 * `web.style_model` — MÔ HÌNH THUỘC TÍNH TRÌNH BÀY CÓ RÀNG BUỘC.
 *
 * EXPLORATION_FIRST: KHÔNG khai `timeline`, nên shell không dựng thanh phát —
 * đúng luật capability-driven sẵn có. Trước wave này đề HTML/CSS bị đẩy vào
 * `generic.rule_scene` và dựng thành "Bước 1/3 → hiện khung", tức bịa một trục
 * thời gian mà cơ chế không có.
 */

const DEFAULT_STYLE: WebStyle = {
  backgroundColor: "#bfdbfe",
  color: "#1f2937",
  fontSize: 20,
  padding: 16,
  borderRadius: 8,
};

function validateWebConfig(raw: unknown): ConfigResult<WebConfig> {
  if (typeof raw !== "object" || raw === null) {
    return { ok: false, error: "Config không phải đối tượng JSON." };
  }
  const r = raw as Record<string, unknown>;
  const content = typeof r.content === "string" ? r.content.trim() : "";
  if (!content) return { ok: false, error: 'Thiếu "content" (nội dung khối).' };
  if (content.length > 120) return { ok: false, error: '"content" tối đa 120 ký tự.' };

  const rawStyle = r.style;
  if (rawStyle !== undefined && (typeof rawStyle !== "object" || rawStyle === null)) {
    return { ok: false, error: '"style" phải là đối tượng.' };
  }
  /* Style của spec đi qua ĐÚNG cổng mà học sinh đi (`applyStyleChange`), nên LLM
     không thể tuồn giá trị ngoài miền vào bằng đường config — một cổng, hai lối. */
  let style: WebStyle = { ...DEFAULT_STYLE };
  for (const [k, v] of Object.entries((rawStyle ?? {}) as Record<string, unknown>)) {
    const next = applyStyleChange(style, k, v as number | string | boolean);
    if (!next) return { ok: false, error: `Thuộc tính "${k}" không hỗ trợ hoặc giá trị ngoài miền.` };
    style = next;
  }
  return { ok: true, config: { content, style, notes: typeof r.notes === "string" ? r.notes : null } };
}

export function makeWebStyleModule(): SimulationModule<WebConfig, WebState> {
  return {
    id: "web.style_model",
    domain: "web",
    title: "Thay đổi kiểu hiển thị (CSS)",
    interactionMode: "exploratory",
    supportedVisualModes: ["2d"],

    validateConfig: validateWebConfig,

    init: (config) => ({
      content: config.content,
      style: { ...config.style },
      baseline: { ...config.style },
    }),

    /** Dùng lại `set_param` sẵn có — KHÔNG đẻ action riêng cho web. */
    apply: (state, action: SimAction) => {
      if (action.type === "set_param") {
        const next = applyStyleChange(state.style, action.name, action.value);
        return next ? { ...state, style: next } : state;
      }
      if (action.type === "toggle" && action.target === "reset") {
        return { ...state, style: { ...state.baseline } };
      }
      return state;
    },

    // KHÔNG khai `timeline`: cơ chế này không có tiến trình theo bước.

    narrate: (state) => ({
      text: isModified(state)
        ? "Em đang xem kết quả sau khi đổi. Bấm Về ban đầu để so sánh."
        : "Đổi thuộc tính bên trái và quan sát khối bên phải đổi ngay.",
    }),

    getExplainContext: (state) => ({
      simulation_id: "web.style_model",
      content: state.content,
      style: state.style,
      css: cssTextOf(state.style),
      modified: isModified(state),
    }),

    Workspace: WebWorkspace,
    Inspector: WebInspector,
  };
}

export function registerWebDomain(): void {
  registerSimulation(makeWebStyleModule());
}
