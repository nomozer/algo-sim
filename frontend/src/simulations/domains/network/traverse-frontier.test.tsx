import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { TraverseWorkspace, makeTraverseModule } from "./traverse-module";
import type { TraverseConfig, TraverseState } from "./traverse-module";

/**
 * FRONTIER-VIS — `network.graph_traversal`.
 *
 * Khoá đúng thứ audit chỉ ra: ở bước 3/7 thuyết minh nói "Lấy B ra khỏi hàng đợi"
 * nhưng UI không vẽ hàng đợi nào, nên học sinh không nhìn thấy frontier — và
 * BFS/DFS trông y hệt nhau. Các test dưới đây khoá: hàng đợi có thật, đúng thứ tự
 * FIFO, đầu hàng đúng, vào/ra đúng, và **dựng lại đúng từ cursor** khi lùi/tua/
 * đặt lại (không có animation state làm nguồn sự thật).
 */

const N = (...ids: string[]) => ids.map((id) => ({ id, label: id }));
const CFG: TraverseConfig = {
  nodes: N("A", "B", "C", "D", "E"),
  edges: [["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"], ["D", "E"]],
  directed: false, start: "A", goal: null, variant: "bfs", notes: null,
};

const mod = makeTraverseModule();
const cfg = (() => {
  const v = mod.validateConfig(CFG);
  if (!v.ok) throw new Error(v.error);
  return v.config;
})();
const base = mod.init(cfg) as TraverseState;
const steps = base.steps;
const at = (c: number) => mod.timeline!.goToStep(base, c) as TraverseState;
const html = (c: number) =>
  renderToString(
    <TraverseWorkspace config={cfg} state={at(c)} busy={false} dispatch={() => {}} />,
  ).replace(/<!--.*?-->/g, "");

/** Các phần tử hàng đợi theo THỨ TỰ XUẤT HIỆN trong DOM. */
function domQueue(h: string): string[] {
  const list = h.match(/<ol class="frontier-items">([\s\S]*?)<\/ol>/)?.[1] ?? "";
  return [...list.matchAll(/class="frontier-value">([^<]+)</g)].map((m) => m[1]);
}
function domHead(h: string): string | null {
  const i = h.indexOf("is-out-next");
  if (i < 0) return null;
  return h.slice(i, i + 250).match(/class="frontier-value">([^<]+)</)?.[1] ?? null;
}

describe("(FRONTIER-VIS) BFS — hàng đợi nhìn thấy được", () => {
  it("1. frontier ban đầu đúng: chỉ có nút xuất phát", () => {
    expect(steps[0].frontierAfter).toEqual(["A"]);
    expect(domQueue(html(0))).toEqual(["A"]);
  });

  it("2. hàng đợi hiển thị ĐÚNG THỨ TỰ FIFO của engine ở mọi bước", () => {
    for (let c = 0; c < steps.length; c += 1) {
      expect(domQueue(html(c)), `bước ${c}`).toEqual(steps[c].frontierAfter);
    }
  });

  it("3. phần tử đầu hàng đợi = phần tử ĐẦU MẢNG engine (nơi shift lấy ra)", () => {
    for (let c = 0; c < steps.length; c += 1) {
      const f = steps[c].frontierAfter;
      if (f.length === 0) continue;
      expect(domHead(html(c)), `bước ${c}`).toBe(f[0]);
    }
  });

  it("4. bước tiến: phần tử rời hàng đợi và phần tử mới vào đều đúng", () => {
    // bước 1 là lần visit đầu: A rời đi, hàng xóm của A vào
    const before = steps[0].frontierAfter;
    const after = steps[1].frontierAfter;
    expect(before).toEqual(["A"]);
    expect(after).not.toContain("A");
    const h = html(1);
    expect(h).toContain("vừa lấy ra");
    expect(h).toContain("mới");
    // mọi phần tử mới phải là hàng xóm THẬT của A theo config
    const neighborsOfA = CFG.edges.filter(([a, b]) => a === "A" || b === "A")
      .map(([a, b]) => (a === "A" ? b : a));
    for (const id of after) expect(neighborsOfA).toContain(id);
  });

  it("5. LÙI phục hồi đúng hàng đợi của bước trước", () => {
    const forward = html(3);
    const back = html(mod.timeline!.currentStep(at(2)));
    expect(domQueue(back)).toEqual(steps[2].frontierAfter);
    expect(domQueue(forward)).toEqual(steps[3].frontierAfter);
    // và quay lại bước 3 lần nữa cho ra ĐÚNG như lần đầu (không phụ thuộc lịch sử)
    expect(domQueue(html(3))).toEqual(domQueue(forward));
  });

  it("6. TUA tới bước bất kỳ dựng đúng frontier tại cursor đó", () => {
    for (const c of [steps.length - 1, 1, steps.length - 2, 0, 2]) {
      expect(domQueue(html(c)), `tua tới ${c}`).toEqual(steps[c].frontierAfter);
    }
  });

  it("7. ĐẶT LẠI: init lại từ config cho đúng frontier ban đầu", () => {
    const fresh = mod.init(cfg) as TraverseState;
    expect(fresh.cursor).toBe(0);
    expect(fresh.steps[0].frontierAfter).toEqual(steps[0].frontierAfter);
  });

  it("8. renderer KHÔNG tự tính BFS — bịa frontier thì UI vẽ theo bản bịa", () => {
    const forged: TraverseState = {
      ...base,
      steps: steps.map((s, i) =>
        i === 0 ? { ...s, frontierAfter: ["Z", "Y", "X"] } : s),
      cursor: 0,
    };
    const h = renderToString(
      <TraverseWorkspace config={cfg} state={forged} busy={false} dispatch={() => {}} />,
    ).replace(/<!--.*?-->/g, "");
    // nếu renderer tự chạy BFS, nó sẽ vẽ ["A"]; nó vẽ đúng bản bịa ⇒ chỉ đọc state
    expect(domQueue(h)).toEqual(["Z", "Y", "X"]);
    expect(domHead(h)).toBe("Z");
  });

  it("9. KHÔNG parse thuyết minh: đổi narration không đổi hàng đợi", () => {
    const forged: TraverseState = {
      ...base,
      steps: steps.map((s, i) =>
        i === 1 ? { ...s, narration: "Hàng đợi: X, Y, Z · Đã thăm: Q" } : s),
      cursor: 1,
    };
    const h = renderToString(
      <TraverseWorkspace config={cfg} state={forged} busy={false} dispatch={() => {}} />,
    ).replace(/<!--.*?-->/g, "");
    expect(domQueue(h)).toEqual(steps[1].frontierAfter);
    expect(domQueue(h)).not.toContain("X");
  });

  it("10. CONTRACT_GAP_EDGE: state không có cạnh nguồn→đích nên KHÔNG tô cạnh duyệt", () => {
    // hợp đồng bước chỉ có current/frontierAfter/visitedSoFar — không có edge
    for (const s of steps) {
      expect(Object.keys(s)).not.toContain("edge");
      expect(Object.keys(s)).not.toContain("from");
    }
    // ở bước giữa (chưa phải bước cuối) không có cạnh nào được tô xanh
    const mid = html(Math.floor(steps.length / 2));
    expect(mid).not.toContain('stroke="var(--accent-green)"');
  });

  it("dòng chữ frontier cũ đã bỏ — không lặp lại cùng thông tin hai nơi", () => {
    const h = html(2);
    expect(h).not.toContain("Hàng đợi: ");
    expect(h).toContain("frontier-queue");
  });
});
