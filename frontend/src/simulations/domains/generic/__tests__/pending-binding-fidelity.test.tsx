/**
 * pending-binding-fidelity.test.tsx — RÀNG BUỘC CHƯA GIẢI ĐƯỢC PHẢI HIỆN LÀ
 * "CHƯA CÓ", KHÔNG PHẢI SỐ 0.
 *
 * ─── SỰ CỐ ĐÃ CHỤP ĐƯỢC MÀN HÌNH (vNext §3) ────────────────────────────────
 *
 * Bài "Kiểm tra đóng mở ngoặc hợp lệ bằng Stack" sinh ra một spec mà hai ô giá
 * trị (`Ký tự hiện tại`, `Kết quả`) KHÔNG có `value`. Học sinh nhìn thấy:
 *
 *     Ký tự hiện tại:  [ 0 ]
 *     Kết quả:         [ 0 ]
 *
 * `0` ở đây không phải dữ liệu — nó là thứ RENDERER TỰ BỊA vì
 * `ui.tsx::renderObject` viết `o.value ?? 0`. Đó là renderer phát minh trạng
 * thái ngữ nghĩa, tức thủng ranh giới R0: engine tất định sở hữu state, renderer
 * chỉ được ĐỌC. Và nó là loại lỗi tệ nhất — một con số TRÔNG NHƯ dữ liệu thật,
 * không phân biệt được với kết quả 0 hợp lệ.
 *
 * ─── VÌ SAO TEST CŨ KHÔNG BẮT ĐƯỢC ─────────────────────────────────────────
 *
 * `stack-bracket-render-certificate.test.tsx` có hẳn một case tên "không có
 * dummy zero", nhưng nó TỰ CẤP cho mình một spec đã điền đủ (`value: "("`,
 * `value: "HỢP LỆ"`). Nó chứng minh renderer hiện đúng KHI ĐƯỢC CHO DỮ LIỆU
 * ĐÚNG — đúng cái điều kiện mà màn hình hỏng không thoả. File này đi vào đúng
 * khoảng trống đó: spec THIẾU binding.
 *
 * ─── HAI VẾ, PHẢI GIỮ CẢ HAI ───────────────────────────────────────────────
 *
 *   1. thiếu binding  ⇒ KHÔNG được ra `0`, phải ra dấu "chưa có";
 *   2. giá trị THẬT là số 0 ⇒ VẪN phải ra `0`.
 *
 * Bỏ vế 2 thì bản vá biến thành "cấm số 0", và lần sau một bài đếm ra 0 sẽ hiện
 * "—" — lỗi ngược lại, cũng sai y như cũ.
 */
import { createElement } from "react";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { makeGenericModule } from "../index";
import { GenericWorkspace } from "../ui";
import { PENDING_DISPLAY } from "../model";
import type { SimulationSpec } from "../model";

const mod = makeGenericModule();

/** Dựng đúng bề mặt production, không phải một renderer rút gọn của test. */
function render(spec: SimulationSpec): string {
  const s0 = mod.init(spec);
  return renderToString(
    createElement(GenericWorkspace, {
      config: spec,
      state: s0,
      busy: false,
      dispatch: () => {},
    })
  );
}

/** Số hiện trong ô giá trị nằm trong một `<text>` riêng — bắt đúng nó, không
 *  bắt chuỗi "0" lọt vào toạ độ/thuộc tính SVG. */
function textNodes(html: string): string[] {
  return [...html.matchAll(/<text[^>]*>([^<]*)<\/text>/g)].map((m) => m[1]);
}

describe("Ràng buộc chưa giải được — KHÔNG được hiện thành 0", () => {
  /* Tái dựng đúng màn hình đã chụp: hai ô giá trị KHÔNG có `value`. */
  const SPEC_THIEU_BINDING: SimulationSpec = {
    dsl_version: "1.0",
    title: "Kiểm tra đóng mở ngoặc hợp lệ bằng Stack",
    objects: [
      { id: "input_str", type: "array_strip", label: "Chuỗi", items: [] },
      { id: "stack_view", type: "stack_view", label: "Ngăn xếp", items: [], capacity: 6 },
      { id: "curr_char", type: "value_box", label: "Ký tự hiện tại" },
      { id: "result_box", type: "value_box", label: "Kết quả" },
    ],
    rules: [],
    interactions: [],
    processes: [],
  };

  it("ô giá trị thiếu binding KHÔNG render số 0", () => {
    const nodes = textNodes(render(SPEC_THIEU_BINDING));
    expect(nodes).not.toContain("0");
  });

  it("ô giá trị thiếu binding render dấu CHƯA CÓ", () => {
    const nodes = textNodes(render(SPEC_THIEU_BINDING));
    const soODaHien = nodes.filter((t) => t === PENDING_DISPLAY).length;
    // Hai ô: `Ký tự hiện tại` và `Kết quả`.
    expect(soODaHien).toBe(2);
  });

  it("giá trị THẬT là số 0 vẫn phải render 0 — không bị bản vá nuốt mất", () => {
    const nodes = textNodes(
      render({
        ...SPEC_THIEU_BINDING,
        objects: [
          { id: "dem", type: "value_box", label: "Số phần tử đếm được", value: 0 },
        ],
      })
    );
    expect(nodes).toContain("0");
    expect(nodes).not.toContain(PENDING_DISPLAY);
  });

  it("giá trị THẬT là chuỗi rỗng cũng là dữ liệu, không phải thiếu binding", () => {
    /* `""` khác `undefined`: thuật toán đã kết luận "không có ký tự nào", chứ
       không phải "chưa biết". Ép cả hai về một dấu là mất phân biệt đó. */
    const nodes = textNodes(
      render({
        ...SPEC_THIEU_BINDING,
        objects: [{ id: "s", type: "value_box", label: "Phần còn lại", value: "" }],
      })
    );
    expect(nodes).not.toContain(PENDING_DISPLAY);
  });
});
