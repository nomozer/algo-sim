import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import {
  buildTreeTraversal,
  makeTreeTraversalModule,
  TreeWorkspace,
  validateTreeTraversalConfig,
  type TreeNode,
  type TreeTraversalConfig,
  type TreeVariant,
} from "./tree-module";

/**
 * M17 W2A — tree_traversal: ORACLE ĐỆ QUY ĐỘC LẬP (viết riêng trong test,
 * KHÔNG gọi buildTreeTraversal) đối chiếu cả 4 biến thể; validator fail-closed;
 * trace phân biệt thật bốn variant (stack vs queue, thứ tự khác nhau).
 */

function cfg(nodes: TreeNode[], rootId: string, variant: TreeVariant): TreeTraversalConfig {
  const v = validateTreeTraversalConfig({
    specVersion: "tree-1.0", variant, rootId, nodes,
  });
  if (!v.ok) throw new Error(`config mẫu bị từ chối: ${v.error}`);
  return v.config;
}

/** Cây chuẩn:  A(B(D,E), C(F,G)) */
const N = (id: string, left: string | null = null, right: string | null = null): TreeNode => ({
  id, label: id, left, right,
});
const BALANCED: TreeNode[] = [
  N("A", "B", "C"), N("B", "D", "E"), N("C", "F", "G"),
  N("D"), N("E"), N("F"), N("G"),
];

/* ── oracle đệ quy độc lập ── */
function oracle(nodes: TreeNode[], rootId: string, variant: TreeVariant): string[] {
  const map = new Map(nodes.map((n) => [n.id, n]));
  const out: string[] = [];
  const dfs = (id: string | null) => {
    if (id === null) return;
    const n = map.get(id)!;
    if (variant === "preorder") out.push(id);
    dfs(n.left);
    if (variant === "inorder") out.push(id);
    dfs(n.right);
    if (variant === "postorder") out.push(id);
  };
  if (variant === "level_order") {
    const q = [rootId];
    while (q.length) {
      const id = q.shift()!;
      out.push(id);
      const n = map.get(id)!;
      if (n.left) q.push(n.left);
      if (n.right) q.push(n.right);
    }
  } else {
    dfs(rootId);
  }
  return out;
}

describe("engine cây — oracle đệ quy độc lập, cây chuẩn A(B(D,E),C(F,G))", () => {
  const EXPECTED: Record<TreeVariant, string[]> = {
    preorder: ["A", "B", "D", "E", "C", "F", "G"],
    inorder: ["D", "B", "E", "A", "F", "C", "G"],
    postorder: ["D", "E", "B", "F", "G", "C", "A"],
    level_order: ["A", "B", "C", "D", "E", "F", "G"],
  };
  for (const variant of Object.keys(EXPECTED) as TreeVariant[]) {
    it(`${variant}: khớp bảng tính tay + oracle`, () => {
      const got = buildTreeTraversal(cfg(BALANCED, "A", variant));
      expect(got.visitedOrder).toEqual(EXPECTED[variant]);
      expect(got.visitedOrder).toEqual(oracle(BALANCED, "A", variant));
    });
  }

  it("bốn biến thể cho THỨ TỰ KHÁC NHAU (phân biệt thật)", () => {
    const orders = (["preorder", "inorder", "postorder", "level_order"] as TreeVariant[]).map(
      (v) => buildTreeTraversal(cfg(BALANCED, "A", v)).visitedOrder.join(""),
    );
    expect(new Set(orders).size).toBe(4);
  });

  it("DFS dùng ngăn xếp + event push/pop; level_order dùng hàng đợi + enqueue/dequeue", () => {
    const pre = buildTreeTraversal(cfg(BALANCED, "A", "preorder"));
    expect(pre.frontierKind).toBe("stack");
    const preKinds = new Set(pre.steps.map((s) => s.kind));
    expect(preKinds.has("push") && preKinds.has("pop") && preKinds.has("visit")).toBe(true);
    expect(preKinds.has("enqueue")).toBe(false);

    const lvl = buildTreeTraversal(cfg(BALANCED, "A", "level_order"));
    expect(lvl.frontierKind).toBe("queue");
    const lvlKinds = new Set(lvl.steps.map((s) => s.kind));
    expect(lvlKinds.has("enqueue") && lvlKinds.has("dequeue")).toBe(true);
    expect(lvlKinds.has("push")).toBe(false);
  });
});

describe("engine cây — dạng biên đối chiếu oracle", () => {
  const CASES: { name: string; nodes: TreeNode[]; root: string }[] = [
    { name: "single node", nodes: [N("X")], root: "X" },
    { name: "left-skewed", nodes: [N("A", "B"), N("B", "C"), N("C", "D"), N("D")], root: "A" },
    { name: "right-skewed", nodes: [N("A", null, "B"), N("B", null, "C"), N("C")], root: "A" },
    { name: "incomplete (thiếu con phải)", nodes: [N("A", "B", "C"), N("B", "D"), N("C"), N("D")], root: "A" },
    { name: "uneven depth", nodes: [N("A", "B", "C"), N("B", "D"), N("C"), N("D", "E"), N("E")], root: "A" },
    { name: "label số", nodes: [{ id: "n1", label: "10", left: "n2", right: null }, { id: "n2", label: "5", left: null, right: null }], root: "n1" },
  ];
  for (const c of CASES) {
    for (const variant of ["preorder", "inorder", "postorder", "level_order"] as TreeVariant[]) {
      it(`${c.name} · ${variant}`, () => {
        const got = buildTreeTraversal(cfg(c.nodes, c.root, variant));
        expect(got.visitedOrder).toEqual(oracle(c.nodes, c.root, variant));
        // mọi node được thăm đúng một lần
        expect(new Set(got.visitedOrder).size).toBe(c.nodes.length);
        expect(got.steps[got.steps.length - 1].kind).toBe("completed");
      });
    }
  }

  it("duplicate DISPLAY label nhưng stable id khác → vẫn duyệt đúng theo id", () => {
    const nodes: TreeNode[] = [
      { id: "r", label: "5", left: "l", right: "rr" },
      { id: "l", label: "5", left: null, right: null },
      { id: "rr", label: "5", left: null, right: null },
    ];
    const got = buildTreeTraversal(cfg(nodes, "r", "preorder"));
    expect(got.visitedOrder).toEqual(["r", "l", "rr"]);
  });
});

describe("validator fail-closed (structural + semantic)", () => {
  const base = { specVersion: "tree-1.0", variant: "preorder", rootId: "A" };
  it("spec_version / variant sai bị từ chối", () => {
    expect(validateTreeTraversalConfig({ ...base, specVersion: "x", nodes: [N("A")] }).ok).toBe(false);
    expect(validateTreeTraversalConfig({ ...base, variant: "bfs", nodes: [N("A")] }).ok).toBe(false);
  });
  it("child ref không tồn tại / self-loop bị từ chối", () => {
    expect(validateTreeTraversalConfig({ ...base, nodes: [N("A", "Z")] }).ok).toBe(false);
    expect(validateTreeTraversalConfig({ ...base, nodes: [N("A", "A")] }).ok).toBe(false);
  });
  it("multi-parent (không phải cây) bị từ chối", () => {
    const r = validateTreeTraversalConfig({
      ...base, nodes: [N("A", "B", "C"), N("B", "D"), N("C", "D"), N("D")],
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("NHIỀU cha");
  });
  it("cycle (node trỏ ngược lên tổ tiên) bị từ chối qua multi-parent/root-parent", () => {
    // B trỏ về A: A là root nhưng lại thành con của B → root có cha
    const r = validateTreeTraversalConfig({
      ...base, nodes: [N("A", "B"), N("B", "A")],
    });
    expect(r.ok).toBe(false);
  });
  it("disconnected component bị từ chối", () => {
    const r = validateTreeTraversalConfig({
      ...base, nodes: [N("A", "B"), N("B"), N("orphan")],
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("rời rạc");
  });
  it("root không tồn tại / node count / depth quá bound", () => {
    expect(validateTreeTraversalConfig({ ...base, rootId: "Z", nodes: [N("A")] }).ok).toBe(false);
    const chain: TreeNode[] = [];
    for (let i = 0; i < 7; i++) chain.push(N(`n${i}`, i < 6 ? `n${i + 1}` : null));
    expect(validateTreeTraversalConfig({ ...base, rootId: "n0", nodes: chain }).ok).toBe(false); // depth 7 > 5
  });
});

describe("module + renderer đọc sự thật engine", () => {
  it("init dựng timeline; renderer hiện thứ tự duyệt của engine ở bước cuối", () => {
    const mod = makeTreeTraversalModule();
    const v = mod.validateConfig({ specVersion: "tree-1.0", variant: "inorder", rootId: "A", nodes: BALANCED });
    expect(v.ok).toBe(true);
    if (!v.ok) return;
    const state = mod.init(v.config);
    expect(state.visitedOrder).toEqual(["D", "B", "E", "A", "F", "C", "G"]);
    const last = { ...state, cursor: state.steps.length - 1 };
    const html = renderToString(
      <TreeWorkspace config={v.config} state={last} busy={false} dispatch={() => {}} />,
    ).replace(/<!--.*?-->/g, "");
    expect(html).toContain("D → B → E → A → F → C → G");
    // KHÔNG chứa nhãn generic
    expect(html).not.toContain("Điểm");
    expect(html).not.toContain("Vật di chuyển");
  });

  it("timeline clamp đúng biên", () => {
    const mod = makeTreeTraversalModule();
    const v = mod.validateConfig({ specVersion: "tree-1.0", variant: "preorder", rootId: "A", nodes: BALANCED });
    if (!v.ok) throw new Error(v.error);
    const s0 = mod.init(v.config);
    expect(mod.timeline!.goToStep(s0, 999).cursor).toBe(s0.steps.length - 1);
    expect(mod.timeline!.goToStep(s0, -3).cursor).toBe(0);
  });
});
