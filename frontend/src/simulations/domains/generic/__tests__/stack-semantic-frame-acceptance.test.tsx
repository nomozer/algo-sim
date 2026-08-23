/**
 * stack-semantic-frame-acceptance.test.tsx — TRẠNG THÁI NGỮ NGHĨA PHẢI ĐI TỚI
 * ĐƯỢC HÌNH, KHÔNG CHỈ TỚI LỜI KỂ.
 *
 * ─── SỰ CỐ QUAN SÁT TRỰC TIẾP (vNext, ảnh màn hình) ────────────────────────
 *
 * Bài "Kiểm tra đóng mở ngoặc hợp lệ bằng Stack", chuỗi `{[()]}`:
 *
 *   - narration khai chuỗi `{[()]}` — ô "Chuỗi đầu vào" TRỐNG
 *   - narration nói con trỏ tới `{`  — "Ký tự hiện tại" là `—`
 *   - narration nói push `[`         — hình Stack vẫn RỖNG
 *   - bước 2 → 3 → 6: lời kể chạy, hình đứng yên
 *
 * ─── HAI TẦNG CÙNG LÀM MẤT DỮ LIỆU ─────────────────────────────────────────
 *
 *   1. `buildTimeline` (model.ts) — nhánh `step_sequence` đẩy ra Frame chỉ mang
 *      `visibleIds`/`entityPos`/`narration`/`stepAction`. KHÔNG có kênh giá trị
 *      theo bước. `valuesOf(spec, state.base)` thì hằng số suốt timeline.
 *      Validator LẠI nhận và giữ `value`/`to_index`/`indices` của từng bước —
 *      hợp đồng hứa, engine vứt.
 *
 *   2. `ui.tsx` — `stack_view` và `array_strip` đọc `o.items` THẲNG từ spec
 *      tĩnh, không bao giờ từ `values`. Nên dù tầng 1 có sửa, collection vẫn
 *      đứng yên. (Đây cũng là ô rỗng nhãn `[0]` trong ảnh: `items: []` ⇒
 *      `max(1, 0)` = một ô trống.)
 *
 * ─── LUẬT ──────────────────────────────────────────────────────────────────
 *
 * Engine sở hữu diễn tiến: `buildTimeline` gấp step action lên một bản đồ giá
 * trị chạy dần, chụp lại vào từng Frame. Renderer CHỈ ĐỌC `frame.values` —
 * KHÔNG tự thực thi push/pop (bất biến R0; nếu renderer tự suy thì đó là engine
 * thứ hai ở tầng trình bày).
 */
import { createElement } from "react";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { makeGenericModule } from "../index";
import { GenericWorkspace } from "../ui";
import { PENDING_DISPLAY, buildTimeline, valuesOf } from "../model";
import type { SimulationSpec } from "../model";

const CHUOI = ["{", "[", "(", ")", "]", "}"];

/**
 * Spec viết ĐÚNG như DSL cho phép: mỗi bước khai hành động + dữ liệu, không
 * chỉ khai lời kể. Đây là thứ validator đã nhận từ trước.
 */
const SPEC: SimulationSpec = {
  dsl_version: "1.0",
  title: "Kiểm tra đóng mở ngoặc hợp lệ bằng Stack",
  objects: [
    { id: "input_str", type: "array_strip", label: "Chuỗi đầu vào", items: CHUOI },
    { id: "stack_view", type: "stack_view", label: "Ngăn xếp", items: [], capacity: 6 },
    { id: "curr_char", type: "value_box", label: "Ký tự hiện tại" },
    { id: "result_box", type: "value_box", label: "Kết quả" },
  ],
  rules: [],
  interactions: [],
  processes: [
    {
      type: "step_sequence",
      steps: [
        { action: "highlight", targets: ["input_str"], narration: "Khởi tạo: ngăn xếp rỗng." },
        { action: "set_value", targets: ["curr_char"], value: "{", narration: "Đọc ký tự '{'." },
        { action: "push", targets: ["stack_view"], value: "{", narration: "Đẩy '{' vào ngăn xếp." },
        { action: "set_value", targets: ["curr_char"], value: "[", narration: "Đọc ký tự '['." },
        { action: "push", targets: ["stack_view"], value: "[", narration: "Đẩy '[' vào ngăn xếp." },
        { action: "pop", targets: ["stack_view"], narration: "Gặp ']' khớp — lấy '[' ra." },
        { action: "set_value", targets: ["result_box"], value: "Hợp lệ", narration: "Duyệt hết, ngăn xếp rỗng." },
      ],
    },
  ],
};

/** Giá trị NGỮ NGHĨA ở khung k — đọc từ engine, không đọc từ pixel. */
function valuesAt(k: number): Record<string, any> {
  const frames = buildTimeline(SPEC);
  const mod = makeGenericModule();
  const s0 = mod.init(SPEC);
  return valuesOf(SPEC, frames[k].values ?? s0.base);
}

describe("§3 — bảng acceptance từng khung", () => {
  it("INIT: chuỗi hiện đủ, ngăn xếp rỗng, ký tự/kết quả CHƯA kết luận", () => {
    const v = valuesAt(0);
    expect(v["input_str"] ?? SPEC.objects[0].items).toEqual(CHUOI);
    expect(v["stack_view"] ?? []).toEqual([]);
    expect(v["curr_char"]).toBeUndefined();
    expect(v["result_box"]).toBeUndefined();
  });

  it("đọc '{': ký tự hiện tại là '{', ngăn xếp CHƯA đổi", () => {
    const v = valuesAt(1);
    expect(v["curr_char"]).toBe("{");
    expect(v["stack_view"]).toEqual([]);
    expect(v["result_box"]).toBeUndefined();
  });

  it("sau push '{': ngăn xếp có đúng một phần tử", () => {
    expect(valuesAt(2)["stack_view"]).toEqual(["{"]);
  });

  it("sau push '[': hai phần tử, '[' ở đỉnh (LIFO)", () => {
    const st = valuesAt(4)["stack_view"];
    expect(st).toEqual(["{", "["]);
    expect(st[st.length - 1]).toBe("[");
  });

  it("sau pop: mất ĐÚNG phần tử đỉnh", () => {
    expect(valuesAt(5)["stack_view"]).toEqual(["{"]);
  });

  it("FINAL: kết quả có kết luận, chuỗi đầu vào GIỮ NGUYÊN", () => {
    const v = valuesAt(6);
    expect(v["result_box"]).toBe("Hợp lệ");
    expect(v["input_str"] ?? SPEC.objects[0].items).toEqual(CHUOI);
  });
});

describe("§5 — hợp đồng thị giác của ngăn xếp: hình phải ĐỔI giữa các khung", () => {
  it("chuỗi ngăn xếp qua các khung là [] → [{] → [{,[] → [{]", () => {
    const day = [0, 2, 4, 5].map((k) => valuesAt(k)["stack_view"]);
    expect(day).toEqual([[], ["{"], ["{", "["], ["{"]]);
  });

  it("KHÔNG được đứng yên — đây chính là triệu chứng đã chụp được", () => {
    const day = [0, 2, 4, 5].map((k) => JSON.stringify(valuesAt(k)["stack_view"]));
    expect(new Set(day).size).toBeGreaterThan(1);
  });
});

describe("§8 — DOM thật phải mang đúng state của khung đang xem", () => {
  function htmlAt(cursor: number): string {
    const mod = makeGenericModule();
    const s0 = mod.init(SPEC);
    return renderToString(
      createElement(GenericWorkspace, {
        config: SPEC,
        state: { ...s0, cursor },
        busy: false,
        dispatch: () => {},
      })
    );
  }

  it("khung khởi tạo: thấy đủ 6 ký tự chuỗi đầu vào", () => {
    const html = htmlAt(0);
    for (const c of CHUOI) expect(html).toContain(c);
  });

  it("khung sau push '[': DOM có ký tự ngăn xếp, không còn rỗng", () => {
    /* Đọc từ DOM: khung 4 phải khác khung 0 về nội dung hiển thị. */
    expect(htmlAt(4)).not.toBe(htmlAt(0));
  });

  it("khung cuối: DOM hiện kết luận, không hiện dấu chưa-có ở ô Kết quả", () => {
    expect(htmlAt(6)).toContain("Hợp lệ");
  });

  it("khung khởi tạo: ô chưa có binding vẫn là dấu chưa-có (giữ bản vá trước)", () => {
    expect(htmlAt(0)).toContain(PENDING_DISPLAY);
  });
});

describe("§9 — hồi quy: số 0 THẬT không bị bản vá này nuốt", () => {
  it("value_box mang số 0 thật vẫn render 0", () => {
    const spec: SimulationSpec = {
      ...SPEC,
      objects: [{ id: "dem", type: "value_box", label: "Đếm", value: 0 }],
      processes: [],
    };
    const mod = makeGenericModule();
    const html = renderToString(
      createElement(GenericWorkspace, {
        config: spec,
        state: mod.init(spec),
        busy: false,
        dispatch: () => {},
      })
    );
    const texts = [...html.matchAll(/<text[^>]*>([^<]*)<\/text>/g)].map((m) => m[1]);
    expect(texts).toContain("0");
    expect(texts).not.toContain(PENDING_DISPLAY);
  });
});
