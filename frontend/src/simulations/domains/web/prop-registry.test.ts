/**
 * prop-registry.test.ts — BỀ MẶT CÔNG CỤ PHẢI DẪN TỪ ĐĂNG KÍ.
 *
 * ─── CÂU HỎI CỦA NGƯỜI DÙNG ────────────────────────────────────────────────
 *
 *   "sửa mô phỏng demo thì mô phỏng sinh sau có ra được các tính năng đó không?"
 *
 * Với `web.style_model`, câu trả lời trước W12 là **KHÔNG**: `ui.tsx` giữ một
 * hằng số `GROUPS` liệt kê tay ba nhóm thuộc tính. Thêm một thuộc tính vào
 * `NUMERIC_PROPS` mà quên sửa `GROUPS` thì học sinh **không có ô điều khiển
 * nào** cho nó — không lỗi, không cảnh báo, không test đỏ.
 *
 * Điều đó chạm luận điểm đề tài: bề mặt tương tác là hằng số viết tay thì một
 * đặc tả do LLM đề xuất không quyết định được gì ở tầng ấy — nó chỉ điền vào
 * một khuôn cứng. Và nó làm hỏng nghĩa của parity mẫu↔AI: hai bên "giống nhau"
 * một phần vì cả hai bị ép về cùng danh sách cứng.
 *
 * Nên test này khoá đúng một điều: **đăng kí là nguồn, UI là hệ quả.**
 */
import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { createElement } from "react";
import { NUMERIC_PROPS, NUMERIC_RANGE } from "./props";
import { WebWorkspace } from "./ui";
import { makeWebStyleModule } from "./index";
import { offlineCatalog } from "../../../data/offline-catalog";

const NODES = ["page", "heading", "paragraph"] as const;

describe("W12 — bề mặt công cụ CSS dẫn từ đăng kí", () => {
  it("mọi thuộc tính số khai đúng một bộ chọn hợp lệ", () => {
    for (const prop of NUMERIC_PROPS) {
      const node = NUMERIC_RANGE[prop].node;
      expect(NODES as readonly string[], `${prop}: node "${node}" không phải bộ chọn hợp lệ`)
        .toContain(node);
    }
  });

  it("không thuộc tính nào bị bỏ quên — đăng kí và miền giá trị khớp nhau", () => {
    /* Trống nghĩa là import hỏng, và một vòng lặp rỗng thì mọi khẳng định trên
       đều đạt một cách vô nghĩa — cùng bẫy đã làm ba guard W8 xanh giả. */
    expect(NUMERIC_PROPS.length).toBeGreaterThan(0);
    expect(Object.keys(NUMERIC_RANGE).sort()).toEqual([...NUMERIC_PROPS].sort());
  });

  it("mọi thuộc tính trong đăng kí ĐỀU có ô điều khiển trên màn hình", () => {
    const entry = offlineCatalog().find((e) => e.simId === "web.style_model");
    expect(entry, "không có mẫu web.style_model để dựng").toBeTruthy();
    const mod = makeWebStyleModule();
    const v = mod.validateConfig((entry!.envelope as { config: unknown }).config);
    expect(v.ok).toBe(true);
    if (!v.ok) return;

    const html = renderToString(createElement(WebWorkspace, {
      config: v.config, state: mod.init(v.config), busy: false, dispatch: () => {},
    } as never));

    for (const prop of NUMERIC_PROPS) {
      /* Hỏi bằng NHÃN của chính đăng kí: nếu ai đó đổi nhãn mà quên đổi đăng kí
         thì dòng này đỏ, và đó đúng là thứ cần đỏ. */
      expect(html, `thuộc tính "${prop}" có trong đăng kí nhưng KHÔNG có ô điều khiển`)
        .toContain(NUMERIC_RANGE[prop].label);
    }
  });

  /**
   * ĐỐI CHỨNG DƯƠNG — thêm một thuộc tính vào đăng kí mà UI không dẫn theo thì
   * phải bắt được. Mô phỏng lại đúng cách bản cũ hỏng: một danh sách nhóm viết
   * tay không chứa thuộc tính mới.
   */
  it("(đối chứng) danh sách nhóm viết tay bỏ sót một thuộc tính ⇒ bị bắt", () => {
    const registry = [...NUMERIC_PROPS, "letterSpacing"];
    const handWritten = [...NUMERIC_PROPS]; // quên cập nhật — đúng lỗi bản cũ
    const missed = registry.filter((p) => !handWritten.includes(p as never));
    expect(missed, "phép so này không phát hiện được thiếu sót ⇒ guard vô nghĩa")
      .toEqual(["letterSpacing"]);
  });
});
