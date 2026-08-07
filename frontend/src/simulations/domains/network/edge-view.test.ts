import { describe, expect, it } from "vitest";

import { buildTraversal, validateTraverseConfig } from "./traverse-module";
import { edgeKey, routeEdgeViews, traversalEdgeViews, usedStatuses } from "./edge-view";
import { makeNetworkModule } from "./index";
import type { NetworkState } from "./model";

/**
 * W4B-1B — TRẠNG THÁI CẠNH dẫn xuất THUẦN từ state tất định.
 *
 * Điều quan trọng nhất ở file này là `describe("DFS quay lui")`: nó chứng minh
 * vì sao renderer KHÔNG được suy cạnh đang đi từ thứ tự thăm.
 */

function cfgOf(raw: unknown) {
  const v = validateTraverseConfig(raw);
  if (!v.ok) throw new Error(v.error);
  return v.config;
}

/* A–B, B–C, A–D. DFS từ A thăm theo thứ tự A, B, C, D — và D được nạp từ A,
   KHÔNG phải từ C. C và D không hề kề nhau. */
const BACKTRACK = cfgOf({
  nodes: [{ id: "A" }, { id: "B" }, { id: "C" }, { id: "D" }],
  edges: [["A", "B"], ["B", "C"], ["A", "D"]],
  directed: false,
  start: "A",
  goal: null,
  variant: "dfs",
});

describe("DFS quay lui — cạnh đang đi phải là cạnh CÓ THẬT", () => {
  const { steps, visitedOrder } = buildTraversal(BACKTRACK);
  const visits = steps.filter((s) => s.kind === "visit");
  const realEdges = new Set(BACKTRACK.edges.map(([a, b]) => edgeKey(a, b, false)));

  it("fixture đúng là ca quay lui: thứ tự thăm A, B, C, D", () => {
    expect(visitedOrder).toEqual(["A", "B", "C", "D"]);
  });

  it("mọi cạnh parent→current đều tồn tại trong config.edges", () => {
    for (const s of visits) {
      if (s.kind !== "visit" || s.parent === null) continue;
      expect(realEdges.has(edgeKey(s.parent, s.current, false))).toBe(true);
    }
  });

  it("SUY TỪ THỨ TỰ THĂM thì SAI: 'nút thăm trước → nút hiện tại' cho cạnh không tồn tại", () => {
    // Đây chính là cách một renderer ngây thơ sẽ làm nếu engine không giữ
    // `parent`. Ở ca này nó sinh ra cạnh C–D — không có trong đồ thị.
    const naive: string[] = [];
    for (let i = 1; i < visitedOrder.length; i++) {
      naive.push(edgeKey(visitedOrder[i - 1], visitedOrder[i], false));
    }
    const bogus = naive.filter((k) => !realEdges.has(k));
    expect(bogus.length).toBeGreaterThan(0);
    expect(bogus).toContain(edgeKey("C", "D", false));

    // còn cách dùng provenance của engine thì không sinh cạnh ma nào
    const fromParent = visits
      .filter((s) => s.kind === "visit" && s.parent !== null)
      .map((s) => edgeKey((s as { parent: string }).parent, (s as { current: string }).current, false));
    expect(fromParent.every((k) => realEdges.has(k))).toBe(true);
  });
});

describe("traversalEdgeViews — dẫn xuất theo bước", () => {
  const { steps } = buildTraversal(BACKTRACK);
  const viewsAt = (cursor: number) =>
    traversalEdgeViews(BACKTRACK.edges, BACKTRACK.directed, steps, cursor);

  it("bước đầu (intro): chưa cạnh nào được đi qua", () => {
    const v = viewsAt(0);
    expect(v.every((e) => e.status === "idle" || e.status === "considering")).toBe(true);
    expect(v.filter((e) => e.status === "active")).toHaveLength(0);
  });

  it("mỗi bước visit có TỐI ĐA một cạnh active", () => {
    for (let i = 0; i < steps.length; i++) {
      expect(viewsAt(i).filter((e) => e.status === "active").length).toBeLessThanOrEqual(1);
    }
  });

  it("cạnh đã đi qua chỉ TĂNG theo tiến trình, không bao giờ mất đi", () => {
    let prev = 0;
    for (let i = 0; i < steps.length; i++) {
      const done = viewsAt(i).filter((e) => e.status === "traversed" || e.status === "active").length;
      expect(done).toBeGreaterThanOrEqual(prev);
      prev = done;
    }
  });

  it("quay về bước 0 khôi phục đúng trạng thái đầu (Back/Reset)", () => {
    const first = viewsAt(0).map((e) => e.status);
    viewsAt(steps.length - 1);
    expect(viewsAt(0).map((e) => e.status)).toEqual(first);
  });

  it("KHÔNG đọc bước tương lai: view tại cursor k chỉ phụ thuộc steps[0..k]", () => {
    const full = viewsAt(2);
    const truncated = traversalEdgeViews(BACKTRACK.edges, BACKTRACK.directed, steps.slice(0, 3), 2);
    expect(truncated).toEqual(full);
  });

  it("mọi cạnh của config đều có đúng một view, không bịa thêm cạnh", () => {
    const v = viewsAt(1);
    expect(v).toHaveLength(BACKTRACK.edges.length);
    const known = new Set(BACKTRACK.edges.map(([a, b]) => edgeKey(a, b, false)));
    for (const e of v) expect(known.has(e.id)).toBe(true);
  });

  it("nhãn trợ năng là tiếng Việt, không lộ định danh kĩ thuật", () => {
    for (const e of viewsAt(1)) {
      expect(e.accessibleLabel).toMatch(/^Đường /);
      expect(e.accessibleLabel).not.toMatch(/network\.|algorithm\.|_/);
    }
  });
});

/* ── packet_routing ─────────────────────────────────────────────────────── */

const mod = makeNetworkModule();
const NET = {
  nodes: [
    { id: "client", type: "client" as const },
    { id: "router", type: "router" as const },
    { id: "isp", type: "isp" as const },
    { id: "server", type: "server" as const },
    { id: "sw", type: "switch" as const }, // ngoài tuyến
  ],
  links: [["client", "router"], ["router", "isp"], ["isp", "server"], ["router", "sw"]] as [
    string,
    string,
  ][],
  source: "client",
  destination: "server",
  notes: null,
};

function netState(): NetworkState {
  const r = mod.validateConfig(NET);
  if (!r.ok) throw new Error(r.error);
  return mod.init(r.config);
}

describe("routeEdgeViews — dẫn xuất từ route + cursor, KHÔNG thêm state", () => {
  const s = netState();
  const viewsAt = (cursor: number) => routeEdgeViews(s.links, s.route, cursor);

  it("bước đầu: chưa chặng nào hoàn thành, cả tuyến còn lại", () => {
    const v = viewsAt(0);
    expect(v.filter((e) => e.status === "traversed")).toHaveLength(0);
    expect(v.filter((e) => e.status === "active")).toHaveLength(0);
    expect(v.filter((e) => e.status === "remaining").length).toBe(s.route.length - 1);
  });

  it("mỗi bước sau có ĐÚNG một chặng đang đi", () => {
    for (let k = 1; k < s.route.length; k++) {
      expect(viewsAt(k).filter((e) => e.status === "active")).toHaveLength(1);
    }
  });

  it("bước cuối: toàn tuyến đã đi, không còn chặng chờ", () => {
    const v = viewsAt(s.route.length - 1);
    expect(v.filter((e) => e.status === "remaining")).toHaveLength(0);
    expect(v.filter((e) => e.status === "traversed" || e.status === "active").length).toBe(
      s.route.length - 1,
    );
  });

  it("cạnh NGOÀI tuyến luôn idle ở mọi bước", () => {
    const off = edgeKey("router", "sw", false);
    for (let k = 0; k < s.route.length; k++) {
      expect(viewsAt(k).find((e) => e.id === off)!.status).toBe("idle");
    }
  });

  it("KHÔNG có trạng thái 'đang cân nhắc' — tuyến do BFS tính trước", () => {
    for (let k = 0; k < s.route.length; k++) {
      expect(usedStatuses(viewsAt(k))).not.toContain("considering");
    }
  });

  it("PARITY 2D↔3D: cả hai renderer đọc CÙNG một dẫn xuất ở mọi bước", () => {
    // Không có engine 3D: cùng hàm thuần, cùng đầu vào ⇒ cùng kết quả. Đây là
    // điều kiện để một renderer mệnh lệnh (THREE.js) kiểm được bằng test.
    for (let k = 0; k < s.route.length; k++) {
      expect(routeEdgeViews(s.links, s.route, k)).toEqual(viewsAt(k));
    }
  });
});

describe("PARITY 2D↔3D — bảng màu 3D phủ ĐÚNG tập trạng thái renderer sinh ra", () => {
  it("mọi status xuất hiện ở bất kỳ bước nào đều có màu 3D xác định", async () => {
    const { ROUTE_EDGE_COLOR_3D } = await import("./ui3d");
    const s = netState();
    const seen = new Set<string>();
    for (let k = 0; k < s.route.length; k++) {
      for (const e of routeEdgeViews(s.links, s.route, k)) seen.add(e.status);
    }
    expect(seen.size).toBeGreaterThan(1);
    for (const status of seen) {
      expect(ROUTE_EDGE_COLOR_3D[status as keyof typeof ROUTE_EDGE_COLOR_3D]).toBeTypeOf("number");
    }
  });

  it("3D không tự bịa trạng thái nào ngoài từ vựng EdgeStatus", async () => {
    const { ROUTE_EDGE_COLOR_3D } = await import("./ui3d");
    expect(Object.keys(ROUTE_EDGE_COLOR_3D).sort()).toEqual(
      ["active", "considering", "idle", "remaining", "traversed"],
    );
  });
});
