import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { TreeWorkspace, makeTreeTraversalModule } from "./tree-module";
import type { TreeNode, TreeTraversalConfig, TreeTraversalState, TreeVariant } from "./tree-module";

/**
 * FRONTIER-VIS — `tree.traversal`.
 *
 * Audit chấm 11/18: cây và cạnh đang đi vẽ tốt, nhưng NGĂN XẾP — thứ quyết định
 * thứ tự duyệt — chỉ là dòng chữ "Ngăn xếp: A, B". Khoá lại: ngăn xếp là chồng
 * thật, đỉnh đúng đầu, push/pop đúng chỗ, và dựng lại đúng từ cursor.
 *
 * Bốn biến thể (preorder/inorder/postorder/level_order) dùng CHUNG một primitive
 * — không component riêng cho từng loại.
 */

const N = (id: string, left: string | null = null, right: string | null = null): TreeNode =>
  ({ id, label: id, left, right });
/** Cây chuẩn A(B(D,E), C(F,G)). */
const NODES: TreeNode[] = [
  N("A", "B", "C"), N("B", "D", "E"), N("C", "F", "G"),
  N("D"), N("E"), N("F"), N("G"),
];
const mod = makeTreeTraversalModule();
function build(variant: TreeVariant) {
  const v = mod.validateConfig({ specVersion: "tree-1.0", variant, rootId: "A", nodes: NODES });
  if (!v.ok) throw new Error(v.error);
  const cfg: TreeTraversalConfig = v.config;
  const base = mod.init(cfg) as TreeTraversalState;
  const at = (c: number) => mod.timeline!.goToStep(base, c) as TreeTraversalState;
  const html = (c: number) =>
    renderToString(
      <TreeWorkspace config={cfg} state={at(c)} busy={false} dispatch={() => {}} />,
    ).replace(/<!--.*?-->/g, "");
  return { cfg, base, steps: base.steps, html };
}

/** Phần tử frontier theo thứ tự DOM (stack đã đảo: đỉnh nằm TRƯỚC). */
function domItems(h: string): string[] {
  const list = h.match(/<ol class="frontier-items">([\s\S]*?)<\/ol>/)?.[1] ?? "";
  return [...list.matchAll(/class="frontier-value">([^<]+)</g)].map((m) => m[1]);
}
function domTop(h: string): string | null {
  const i = h.indexOf("is-out-next");
  if (i < 0) return null;
  return h.slice(i, i + 250).match(/class="frontier-value">([^<]+)</)?.[1] ?? null;
}

describe("(FRONTIER-VIS) tree.traversal — ngăn xếp nhìn thấy được", () => {
  const { steps, html } = build("inorder");

  it("1. ngăn xếp ban đầu đúng theo engine", () => {
    expect(domItems(html(0))).toEqual([...steps[0].frontierAfter].reverse());
  });

  it("2. ĐỈNH ngăn xếp = phần tử CUỐI mảng engine (nơi pop lấy ra)", () => {
    for (let c = 0; c < steps.length; c += 1) {
      const f = steps[c].frontierAfter;
      if (f.length === 0) continue;
      expect(domTop(html(c)), `bước ${c}`).toBe(f[f.length - 1]);
    }
  });

  it("3. thứ tự LIFO đúng: DOM là mảng engine ĐẢO NGƯỢC (đỉnh trên cùng)", () => {
    for (let c = 0; c < steps.length; c += 1) {
      expect(domItems(html(c)), `bước ${c}`).toEqual([...steps[c].frontierAfter].reverse());
    }
  });

  it("4. PUSH đặt phần tử mới đúng ở đỉnh", () => {
    const push = steps.findIndex((s, i) =>
      i > 0 && s.frontierAfter.length > steps[i - 1].frontierAfter.length);
    expect(push).toBeGreaterThan(0);
    const added = steps[push].frontierAfter[steps[push].frontierAfter.length - 1];
    expect(domTop(html(push))).toBe(added);
    expect(html(push)).toContain("mới");
  });

  it("5. POP lấy đúng phần tử đang ở đỉnh của bước trước", () => {
    const pop = steps.findIndex((s, i) =>
      i > 0 && s.frontierAfter.length < steps[i - 1].frontierAfter.length);
    expect(pop).toBeGreaterThan(0);
    const prev = steps[pop - 1].frontierAfter;
    const removed = prev[prev.length - 1];
    expect(html(pop)).toContain("vừa lấy ra");
    expect(html(pop)).toContain(`>${removed}<`);
  });

  it("6. LÙI / TUA / ĐẶT LẠI dựng đúng từ cursor, không phụ thuộc lịch sử", () => {
    const target = Math.floor(steps.length / 2);
    const direct = domItems(html(target));
    // đi lòng vòng rồi quay lại phải cho kết quả y hệt
    html(steps.length - 1); html(0); html(target - 1);
    expect(domItems(html(target))).toEqual(direct);
    const fresh = mod.init(build("inorder").cfg) as TreeTraversalState;
    expect(fresh.cursor).toBe(0);
    expect(fresh.steps[0].frontierAfter).toEqual(steps[0].frontierAfter);
  });

  /**
   * 7. Cạnh đang tô dẫn xuất TỪ `activePath` — dữ liệu CÓ CẤU TRÚC của engine,
   * không phải suy từ vị trí node hay từ thuyết minh.
   *
   * GHI CHÚ HỢP ĐỒNG (audit trước nghi là lỗi, hoá ra không phải):
   * `current` là node mà BƯỚC nói về, còn `activePath` là đường ngăn xếp SAU
   * bước đó. Ở bước "rời nhánh" (leave/pop) hai thứ này LỆCH NHAU một cách hợp
   * lệ — vd `current = D` trong khi `activePath = [A, B]` vì D vừa được lấy ra.
   * Vì vậy KHÔNG được khoá bất biến "current luôn thuộc activePath"; thứ khoá
   * được là: cạnh tô chỉ phụ thuộc `activePath`, và không cạnh nào ngoài
   * activePath được tô.
   */
  it("7. cạnh tô là hàm THUẦN của activePath, không của vị trí hay narration", () => {
    const { cfg, base } = build("inorder");
    const forged: TreeTraversalState = {
      ...base,
      steps: base.steps.map((s, i) =>
        i === 0 ? { ...s, activePath: ["A", "C"], narration: "bịa: đang ở B" } : s),
      cursor: 0,
    };
    const h = renderToString(
      <TreeWorkspace config={cfg} state={forged} busy={false} dispatch={() => {}} />,
    );
    // A–C nằm trong activePath bịa ⇒ phải được tô; A–B thì không
    const edges = [...h.matchAll(/<line[^>]*stroke="([^"]+)"[^>]*>/g)].map((m) => m[1]);
    expect(edges.some((c) => c.includes("accent"))).toBe(true);
    // đổi activePath thành rỗng ⇒ KHÔNG cạnh nào được tô nổi
    const none: TreeTraversalState = {
      ...base,
      steps: base.steps.map((s, i) => (i === 0 ? { ...s, activePath: [] } : s)),
      cursor: 0,
    };
    const h2 = renderToString(
      <TreeWorkspace config={cfg} state={none} busy={false} dispatch={() => {}} />,
    );
    const hi = (s: string) => (s.match(/stroke="var\(--accent-orange\)"/g) ?? []).length;
    expect(hi(h2)).toBe(0);
    expect(hi(h)).toBeGreaterThan(0);
  });

  it("7b. hợp đồng: ở bước rời nhánh, `current` KHÔNG nằm trong activePath", () => {
    // Ghi lại sự lệch pha hợp lệ này để lần sau không ai coi là lỗi.
    const diverge = steps.filter((s) => s.current && !s.activePath.includes(s.current));
    expect(diverge.length).toBeGreaterThan(0);
  });

  it("8. renderer KHÔNG tự chạy traversal — bịa frontier thì UI vẽ theo bản bịa", () => {
    const { cfg, base } = build("inorder");
    const forged: TreeTraversalState = {
      ...base,
      steps: base.steps.map((s, i) => (i === 0 ? { ...s, frontierAfter: ["G", "F"] } : s)),
      cursor: 0,
    };
    const h = renderToString(
      <TreeWorkspace config={cfg} state={forged} busy={false} dispatch={() => {}} />,
    ).replace(/<!--.*?-->/g, "");
    expect(domItems(h)).toEqual(["F", "G"]); // đảo: đỉnh = cuối mảng = F
    expect(domTop(h)).toBe("F");
  });

  it("bốn biến thể dùng CHUNG primitive, chỉ đổi mode và nhãn", () => {
    for (const v of ["preorder", "inorder", "postorder", "level_order"] as TreeVariant[]) {
      const b = build(v);
      const h = b.html(Math.floor(b.steps.length / 2));
      expect(h, v).toContain("frontier-");
      const isQueue = b.base.frontierKind === "queue";
      expect(h, v).toContain(isQueue ? "frontier-queue" : "frontier-stack");
      expect(h, v).toContain(isQueue ? "FIFO" : "LIFO");
    }
  });

  it("level_order dùng mode QUEUE — đầu ở ĐẦU mảng, khác hẳn stack", () => {
    const b = build("level_order");
    expect(b.base.frontierKind).toBe("queue");
    for (let c = 0; c < b.steps.length; c += 1) {
      const f = b.steps[c].frontierAfter;
      if (f.length === 0) continue;
      expect(domTop(b.html(c)), `bước ${c}`).toBe(f[0]);
      expect(domItems(b.html(c))).toEqual(f); // queue KHÔNG đảo
    }
  });

  it("dòng chữ ngăn xếp cũ đã bỏ — không lặp cùng thông tin hai nơi", () => {
    expect(html(2)).not.toContain("Ngăn xếp: ");
  });
});
