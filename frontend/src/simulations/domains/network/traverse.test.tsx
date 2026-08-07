import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import {
  buildTraversal,
  makeTraverseModule,
  TraverseInspector,
  validateTraverseConfig,
  type TraverseConfig,
} from "./traverse-module";

/**
 * M17 W1 — network.graph_traversal: oracle BFS/DFS ĐỘC LẬP viết riêng trong
 * test đối chiếu thứ tự thăm; đường đi BFS phải NGẮN NHẤT (đối chiếu hop
 * distance oracle); unreachable là KẾT QUẢ hợp lệ; validator fail-closed.
 */

function cfg(partial: Partial<TraverseConfig> & Pick<TraverseConfig, "nodes" | "edges" | "start" | "variant">): TraverseConfig {
  const v = validateTraverseConfig({ directed: false, goal: null, ...partial });
  if (!v.ok) throw new Error(v.error);
  return v.config;
}

const N = (ids: string[]) => ids.map((id) => ({ id, label: null }));

// Đồ thị mẫu:  A—B, A—C, B—D, C—D, D—E  (vô hướng)
const NODES = N(["A", "B", "C", "D", "E"]);
const EDGES: [string, string][] = [["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"], ["D", "E"]];

/** Oracle BFS độc lập — hàng đợi, hàng xóm theo thứ tự khai báo. */
function oracleBfs(config: TraverseConfig): string[] {
  const adj = new Map<string, string[]>(config.nodes.map((n) => [n.id, []]));
  for (const [a, b] of config.edges) {
    adj.get(a)!.push(b);
    if (!config.directed) adj.get(b)!.push(a);
  }
  const out: string[] = [];
  const seen = new Set([config.start]);
  const q = [config.start];
  while (q.length) {
    const cur = q.shift()!;
    out.push(cur);
    if (cur === config.goal) break;
    for (const nb of adj.get(cur)!) {
      if (!seen.has(nb)) {
        seen.add(nb);
        q.push(nb);
      }
    }
  }
  return out;
}

/** Oracle DFS độc lập — ĐỆ QUY theo thứ tự khai báo (chuẩn giáo khoa). */
function oracleDfs(config: TraverseConfig): string[] {
  const adj = new Map<string, string[]>(config.nodes.map((n) => [n.id, []]));
  for (const [a, b] of config.edges) {
    adj.get(a)!.push(b);
    if (!config.directed) adj.get(b)!.push(a);
  }
  const out: string[] = [];
  const seen = new Set<string>();
  let stop = false;
  function go(id: string) {
    if (stop || seen.has(id)) return;
    seen.add(id);
    out.push(id);
    if (id === config.goal) {
      stop = true;
      return;
    }
    for (const nb of adj.get(id)!) go(nb);
  }
  go(config.start);
  return out;
}

describe("engine duyệt — oracle độc lập", () => {
  it("BFS: thứ tự thăm khớp oracle hàng đợi (A B C D E)", () => {
    const c = cfg({ nodes: NODES, edges: EDGES, start: "A", variant: "bfs" });
    const got = buildTraversal(c);
    expect(got.visitedOrder).toEqual(oracleBfs(c));
    expect(got.visitedOrder).toEqual(["A", "B", "C", "D", "E"]);
  });

  it("DFS: thứ tự thăm khớp oracle đệ quy (A B D C E — đi sâu trước)", () => {
    const c = cfg({ nodes: NODES, edges: EDGES, start: "A", variant: "dfs" });
    const got = buildTraversal(c);
    expect(got.visitedOrder).toEqual(oracleDfs(c));
    expect(got.visitedOrder[1]).toBe("B"); // đi sâu nhánh khai báo trước
  });

  it("BFS + goal: dừng ở đích, đường đi NGẮN NHẤT và các cạnh liên tiếp có thật", () => {
    const c = cfg({ nodes: NODES, edges: EDGES, start: "A", goal: "E", variant: "bfs" });
    const got = buildTraversal(c);
    expect(got.reachable).toBe(true);
    expect(got.path![0]).toBe("A");
    expect(got.path![got.path!.length - 1]).toBe("E");
    // ngắn nhất: A→B→D→E hoặc A→C→D→E đều 3 cạnh — BFS tất định chọn B trước
    expect(got.path).toEqual(["A", "B", "D", "E"]);
    const undirected = new Set(EDGES.flatMap(([a, b]) => [`${a}|${b}`, `${b}|${a}`]));
    for (let i = 0; i < got.path!.length - 1; i++) {
      expect(undirected.has(`${got.path![i]}|${got.path![i + 1]}`)).toBe(true);
    }
  });

  it("unreachable là KẾT QUẢ hợp lệ: reachable=false, path=null, không throw", () => {
    const c = cfg({
      nodes: N(["A", "B", "X", "Y"]),
      edges: [["A", "B"], ["X", "Y"]],
      start: "A",
      goal: "Y",
      variant: "bfs",
    });
    const got = buildTraversal(c);
    expect(got.reachable).toBe(false);
    expect(got.path).toBeNull();
    expect(got.visitedOrder).toEqual(["A", "B"]); // chỉ phần liên thông
    const last = got.steps[got.steps.length - 1];
    expect(last.kind).toBe("result");
    expect(last.narration).toContain("KHÔNG đến được");
  });

  it("đồ thị CÓ HƯỚNG: cạnh một chiều không đi ngược", () => {
    const c = cfg({
      nodes: N(["A", "B", "C"]),
      edges: [["A", "B"], ["C", "B"]],
      directed: true,
      start: "A",
      goal: "C",
      variant: "bfs",
    });
    const got = buildTraversal(c);
    expect(got.reachable).toBe(false); // B→C không tồn tại (chỉ C→B)
  });

  it("mỗi bước visit mang frontier + visitedSoFar nhất quán (tiền tố của thứ tự cuối)", () => {
    const c = cfg({ nodes: NODES, edges: EDGES, start: "A", variant: "dfs" });
    const got = buildTraversal(c);
    const visits = got.steps.filter((s) => s.kind === "visit");
    expect(visits).toHaveLength(got.visitedOrder.length);
    visits.forEach((s, i) => {
      expect(s.visitedSoFar).toEqual(got.visitedOrder.slice(0, i + 1));
    });
  });
});

describe("validator fail-closed", () => {
  const base = { nodes: N(["A", "B"]), edges: [["A", "B"]], start: "A", variant: "bfs" };
  it("cạnh tham chiếu nút không tồn tại / self-loop bị từ chối", () => {
    expect(validateTraverseConfig({ ...base, edges: [["A", "Z"]] }).ok).toBe(false);
    expect(validateTraverseConfig({ ...base, edges: [["A", "A"]] }).ok).toBe(false);
  });
  it("start/goal phải là nút thật; goal ≠ start", () => {
    expect(validateTraverseConfig({ ...base, start: "Z" }).ok).toBe(false);
    expect(validateTraverseConfig({ ...base, goal: "Z" }).ok).toBe(false);
    expect(validateTraverseConfig({ ...base, goal: "A" }).ok).toBe(false);
  });
  it("variant ngoài enum / id trùng / quá bound bị từ chối", () => {
    expect(validateTraverseConfig({ ...base, variant: "dijkstra" }).ok).toBe(false);
    expect(validateTraverseConfig({ ...base, nodes: N(["A", "A"]) }).ok).toBe(false);
    expect(validateTraverseConfig({ ...base, nodes: N(Array.from({ length: 11 }, (_, i) => `n${i}`)) }).ok).toBe(false);
  });
});

describe("module + inspector đọc sự thật engine", () => {
  it("timeline đủ intro + visit + result; inspector hiện thứ tự thăm", () => {
    const mod = makeTraverseModule();
    const v = mod.validateConfig({
      nodes: N(["A", "B", "C"]),
      edges: [["A", "B"], ["B", "C"]],
      directed: false,
      start: "A",
      goal: null,
      variant: "bfs",
    });
    expect(v.ok).toBe(true);
    if (!v.ok) return;
    const state = mod.init(v.config);
    expect(state.steps[0].kind).toBe("intro");
    expect(state.steps[state.steps.length - 1].kind).toBe("result");
    expect(state.frontierKind).toBe("queue");
    // W4B-1B — HIỆN DẦN. Trước đây test này khẳng định inspector in ĐỦ
    // "A → B → C" ngay ở bước 0, tức là nó KHOÁ LẠI chính lỗi lộ đáp án
    // (DESIGN_BRIEF §3.3). Nay hợp đồng ngược lại: giữa chừng chỉ nêu phần đã
    // thăm, thứ tự đầy đủ chỉ công bố ở bước cuối.
    const htmlAt = (cursor: number) =>
      renderToString(
        <TraverseInspector
          config={v.config}
          state={{ ...state, cursor }}
          busy={false}
          dispatch={() => {}}
        />,
      ).replace(/<!--.*?-->/g, "");

    const first = htmlAt(0);
    expect(first).not.toContain("A → B → C"); // KHÔNG lộ đáp án
    expect(first).toContain("Đã thăm");

    const final = htmlAt(state.steps.length - 1);
    expect(final).toContain("A → B → C"); // công bố ở bước cuối
    // "(engine)" là thuật ngữ lập trình viên — không được lên màn hình học sinh
    expect(final).not.toContain("(engine)");
  });
});
