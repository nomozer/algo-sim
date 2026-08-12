import { registerSimulation } from "../../registry";
import type { ConfigResult, SimAction, SimulationModule } from "../../types";
import { applyStyleChange, cssTextOf, htmlTextOf, isModified, moveBlock, selectNode } from "./apply";
import { CONTENT_MAX_LENGTH, DEFAULT_STYLE, PARAGRAPH_MAX_LENGTH } from "./props";
import { SELECTOR_OF, type WebBlock, type WebConfig, type WebState, type WebStyle } from "./model";
import { WebInspector, WebWorkspace } from "./ui";

/**
 * `web.style_model` — MÔ HÌNH THUỘC TÍNH TRÌNH BÀY CÓ RÀNG BUỘC.
 *
 * EXPLORATION_FIRST: KHÔNG khai `timeline`, nên shell không dựng thanh phát —
 * đúng luật capability-driven sẵn có. Trước wave này đề HTML/CSS bị đẩy vào
 * `generic.rule_scene` và dựng thành "Bước 1/3 → hiện khung", tức bịa một trục
 * thời gian mà cơ chế không có.
 */


function validateWebConfig(raw: unknown): ConfigResult<WebConfig> {
  if (typeof raw !== "object" || raw === null) {
    return { ok: false, error: "Config không phải đối tượng JSON." };
  }
  const r = raw as Record<string, unknown>;
  const heading = typeof r.heading === "string" ? r.heading.trim() : "";
  if (!heading) return { ok: false, error: 'Thiếu "heading" (tiêu đề trang).' };
  if (heading.length > CONTENT_MAX_LENGTH) {
    return { ok: false, error: `"heading" tối đa ${CONTENT_MAX_LENGTH} ký tự.` };
  }
  if (r.paragraph !== undefined && typeof r.paragraph !== "string") {
    return { ok: false, error: '"paragraph" phải là chuỗi.' };
  }
  const paragraph = typeof r.paragraph === "string" ? r.paragraph.trim() : "";
  if (paragraph.length > PARAGRAPH_MAX_LENGTH) {
    return { ok: false, error: `"paragraph" tối đa ${PARAGRAPH_MAX_LENGTH} ký tự.` };
  }

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
  return {
    ok: true,
    config: { heading, paragraph, style, notes: typeof r.notes === "string" ? r.notes : null },
  };
}

export function makeWebStyleModule(): SimulationModule<WebConfig, WebState> {
  return {
    id: "web.style_model",
    domain: "web",
    title: "Trang web và kiểu hiển thị (HTML/CSS)",
    interactionMode: "exploratory",
    supportedVisualModes: ["2d"],

    validateConfig: validateWebConfig,

    init: (config) => {
      /* Đoạn văn rỗng KHÔNG được chiếm một ô: một ô trống thì đảo lên đảo xuống
         chẳng thấy gì đổi, và mã HTML sẽ in ra một thẻ `<p>` không có trong
         trang. Thân trang chỉ gồm những khối THỰC SỰ có mặt. */
      const order: WebBlock[] = config.paragraph
        ? ["heading", "paragraph"] : ["heading"];
      return {
        heading: config.heading,
        paragraph: config.paragraph,
        style: { ...config.style },
        order,
        selected: "page" as const,
        baseline: { ...config.style },
        baselineOrder: [...order],
      };
    },

    /** Dùng lại `set_param`/`move` sẵn có — KHÔNG đẻ action riêng cho web. */
    apply: (state, action: SimAction) => {
      if (action.type === "set_param") {
        /* Chọn nút đi qua CÙNG cổng với đổi thuộc tính: một tên lạ thì cả hai
           nhánh đều trả về state cũ, không có đường nào lọt vào miền. */
        if (action.name === "selected") {
          const node = typeof action.value === "string" ? selectNode(action.value) : null;
          return node && node !== state.selected ? { ...state, selected: node } : state;
        }
        const next = applyStyleChange(state.style, action.name, action.value);
        return next ? { ...state, style: next } : state;
      }
      if (action.type === "move") {
        const order = moveBlock(state.order, action.target, action.y);
        /* Khối vừa dời thành khối đang chọn: học sinh vừa tác động lên nó thì
           nó phải còn là thứ đang cầm, nếu không mũi tên thứ hai sẽ dời nhầm. */
        return order ? { ...state, order, selected: action.target as WebBlock } : state;
      }
      if (action.type === "toggle" && action.target === "reset") {
        return { ...state, style: { ...state.baseline }, order: [...state.baselineOrder] };
      }
      return state;
    },

    // KHÔNG khai `timeline`: cơ chế này không có tiến trình theo bước.

    narrate: (state) => ({
      text: isModified(state)
        ? `Em đang sửa ${SELECTOR_OF[state.selected]}. Bấm Về ban đầu để so sánh với trang gốc.`
        : "Bấm thẳng vào một phần của trang để chọn nó, rồi đổi thuộc tính hoặc dời nó lên xuống.",
    }),

    getExplainContext: (state) => ({
      simulation_id: "web.style_model",
      heading: state.heading,
      paragraph: state.paragraph,
      style: state.style,
      order: state.order,
      selected: state.selected,
      selector: SELECTOR_OF[state.selected],
      html: htmlTextOf(state),
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
