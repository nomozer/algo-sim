import { registerSimulation } from "../../registry";
import { isChannelValue, type Channel } from "../../color-channels";
import type { ConfigResult, SimAction, SimulationModule } from "../../types";
import {
  CHANNEL_FIELD,
  cornerNameOf,
  cssColorOfState,
  dominantChannel,
  hexColorOfState,
  isGray,
  type ColorConfig,
  type ColorState,
} from "./model";
import { ColorInspector, ColorWorkspace } from "./ui";

/**
 * color.rgb_model — mô phỏng KHÁM PHÁ (exploratory): không timeline.
 *
 * KHÔNG có `predict`: bài này không có "bước tiếp theo" nào để cam kết. Trộn
 * màu là quan hệ TỨC THÌ ba-vào-một; dựng một ô hỏi đúng/sai ở đây sẽ là quiz
 * gắn thêm vào một công cụ, đúng thứ Phase B vừa gỡ ra khỏi họ thuật toán.
 * Transport khai `RESET_ONLY` cùng lý do (`transport-policy.ts`).
 */

const FIELD_OF_NAME: Record<string, Channel> = {
  red: "r",
  green: "g",
  blue: "b",
};

function validateColorConfig(raw: unknown): ConfigResult<ColorConfig> {
  if (typeof raw !== "object" || raw === null) {
    return { ok: false, error: "Config không phải đối tượng JSON." };
  }
  const r = raw as Record<string, unknown>;
  for (const name of ["red", "green", "blue"] as const) {
    if (!isChannelValue(r[name])) {
      return { ok: false, error: `"${name}" phải là số nguyên từ 0 đến 255.` };
    }
  }
  return {
    ok: true,
    config: {
      red: r.red as number,
      green: r.green as number,
      blue: r.blue as number,
      notes: typeof r.notes === "string" ? r.notes : null,
    },
  };
}

export function makeColorModule(): SimulationModule<ColorConfig, ColorState> {
  return {
    id: "color.rgb_model",
    domain: "color",
    title: "Mô hình màu RGB",
    interactionMode: "exploratory",
    supportedVisualModes: ["2d"],

    validateConfig: validateColorConfig,

    init: (config) => ({ red: config.red, green: config.green, blue: config.blue }),

    apply: (state, action: SimAction) => {
      if (action.type !== "set_param") return state;
      const ch = FIELD_OF_NAME[action.name];
      // Tên trường lạ ⇒ no-op cùng tham chiếu. KHÔNG kẹp bừa một giá trị sai:
      // `set_param` sai tên là lỗi của nơi gọi, và im lặng nhận nó sẽ biến mọi
      // action của miền khác thành một lần đổi màu.
      if (!ch || !isChannelValue(action.value)) return state;
      const field = CHANNEL_FIELD[ch];
      if (state[field] === action.value) return state;
      return { ...state, [field]: action.value };
    },

    // KHÔNG có timeline (M5 §2) — Controls chỉ hiện Đặt lại.

    /* W4B-4D — mô hình đã rời khỏi đề chưa. Khai đúng ba khoá học sinh đổi
       được; `notes` của đề không nằm trong đó nên nhãn "Đã đổi so với đề bài"
       không kêu oan ngay khi vừa mở. */
    currentConfig: (state) => ({ red: state.red, green: state.green, blue: state.blue }),

    /* Lối vào Khám phá: bài này KHÔNG gác công cụ sau cửa nào (ba thanh trượt
       dùng được ngay — Policy B), nên `explore.entry` ở đây chỉ là lời mời có
       tên, không phải cái chốt. Trả `null` khi không còn gì để đổi thì sai:
       màu luôn đổi được. */
    explore: {
      entry: () => ({
        label: "Khám phá: kéo từng kênh để xem màu đổi theo",
        shortLabel: "Khám phá",
        closeLabel: "Đóng khám phá",
        hint: "Giữ hai kênh cố định, kéo kênh thứ ba — đó là cách đọc ra việc mỗi kênh đóng góp gì.",
        available: true,
      }),
    },

    // (SHELL-N) Không có bước, nên "thuyết minh" là GIÁ TRỊ HIỆN TẠI + quan hệ
    // đọc được từ nó. Mọi câu dưới đây dẫn xuất tất định từ ba số.
    narrate: (state) => {
      const css = cssColorOfState(state);
      const hex = hexColorOfState(state);
      const corner = cornerNameOf(state);
      const head = `Ba kênh đang ở ${state.red} · ${state.green} · ${state.blue} — tức ${css}, viết gọn là ${hex}.`;
      if (corner) return { text: `${head} Đây đúng là màu ${corner}.` };
      if (isGray(state)) {
        return { text: `${head} Ba kênh bằng nhau nên màu không còn sắc — chỉ là một mức xám.` };
      }
      const top = dominantChannel(state);
      if (top) {
        const NAME: Record<Channel, string> = { r: "đỏ", g: "lục", b: "lam" };
        return { text: `${head} Kênh ${NAME[top]} đang mạnh nhất nên màu nghiêng về phía đó.` };
      }
      return { text: `${head} Hai kênh đang cùng ở mức cao nhất nên màu là kết quả trộn của chúng.` };
    },

    getExplainContext: (state) => ({
      simulation_id: "color.rgb_model",
      red: state.red,
      green: state.green,
      blue: state.blue,
      cssColor: cssColorOfState(state),
      hexColor: hexColorOfState(state),
    }),

    Workspace: ColorWorkspace,
    Inspector: ColorInspector,
  };
}

export function registerColorDomain(): void {
  registerSimulation(makeColorModule());
}
