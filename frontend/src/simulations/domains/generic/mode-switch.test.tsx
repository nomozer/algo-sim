import { describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import { toolHint } from "./EditBar";
import { makeGenericModule } from "./index";
import type { GenericState, SimulationSpec } from "./model";
import { GenericWorkspace } from "./ui";

/**
 * §8.9 + §8.10 (M7.14D): chuyển Quan sát ↔ Chỉnh sửa phải là thay đổi UI CỤC BỘ.
 * Không API/LLM call, không reset engine, không reset cursor. Và trạng thái
 * công cụ "Nối" phải rõ ràng ở từng bước.
 */

const mod = makeGenericModule();

function spec(raw: object): SimulationSpec {
  const r = mod.validateConfig(raw);
  if (!r.ok) throw new Error(r.error);
  return r.config;
}

const TRIANGLE = spec({
  dsl_version: "1.0",
  title: "Tam giác ABC",
  objects: [
    { id: "A", type: "node", x: 20, y: 70 },
    { id: "B", type: "node", x: 80, y: 70 },
    { id: "C", type: "node", x: 50, y: 20 },
    { id: "AB", type: "edge", from: "A", to: "B" },
  ],
  rules: [],
  interactions: [{ type: "drag", target: "C" }],
  processes: [
    { type: "reveal_sequence", steps: [{ objects: ["A", "B"] }, { objects: ["AB"] }, { objects: ["C"] }] },
  ],
});

describe("mode switch — không đụng engine/mạng", () => {
  it("render workspace KHÔNG gọi fetch (0 API/LLM call)", () => {
    const state = mod.init(TRIANGLE) as GenericState;
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    renderToString(
      <GenericWorkspace config={TRIANGLE} state={state} busy={false} dispatch={() => {}} />,
    );
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("dispatch KHÔNG bị gọi khi chỉ render (mode là state cục bộ của UI)", () => {
    const state = mod.init(TRIANGLE) as GenericState;
    const dispatch = vi.fn();
    renderToString(<GenericWorkspace config={TRIANGLE} state={state} busy={false} dispatch={dispatch} />);
    expect(dispatch).not.toHaveBeenCalled();
  });

  it("state engine (cursor/pos/base/timeline) KHÔNG đổi khi render lại nhiều lần", () => {
    let state = mod.init(TRIANGLE) as GenericState;
    state = mod.timeline!.goToStep(state, 2) as GenericState;
    state = mod.apply(state, { type: "move", target: "C", x: 44, y: 33 }) as GenericState;
    const snapshot = JSON.stringify({ c: state.cursor, pos: state.pos, base: state.base, t: state.timeline.length });

    for (let i = 0; i < 3; i++) {
      renderToString(<GenericWorkspace config={TRIANGLE} state={state} busy={false} dispatch={() => {}} />);
    }
    expect(JSON.stringify({ c: state.cursor, pos: state.pos, base: state.base, t: state.timeline.length })).toBe(
      snapshot,
    );
    expect(state.cursor).toBe(2); // cursor KHÔNG bị reset
    expect(state.pos.C).toEqual({ x: 44, y: 33 }); // vị trí đã kéo còn nguyên
  });

  it("EditBar: trạng thái công cụ Nối rõ ràng từng bước", () => {
    expect(toolHint(null, null, "Đoạn văn")).toContain("Chọn một công cụ");
    expect(toolHint("connect", null, "Đoạn văn")).toContain("THỨ NHẤT");
    const armed = toolHint("connect", "A", "Đoạn văn");
    expect(armed).toContain("A");
    expect(armed).toContain("THỨ HAI");
    expect(toolHint("connect", "A", "Đoạn văn")).toContain("Esc"); // có đường hủy
    expect(toolHint("add_node", null, "Đoạn văn")).toContain("chỗ trống");
  });
});
