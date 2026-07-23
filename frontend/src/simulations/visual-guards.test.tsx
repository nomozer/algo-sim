import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";

import { makeTraverseModule, TraverseWorkspace } from "./domains/network/traverse-module";

/**
 * M17-RC1 §E/§E1 — GUARD cho các lỗi thị giác đã tìm được trên trình duyệt thật.
 *
 * Đây là lưới an toàn RẺ chạy trong CI; nó KHÔNG thay thế audit trình duyệt
 * (SSR không có computed style, không có hình học). Mục đích duy nhất: nếu ai
 * đó hoàn tác bản sửa, test đỏ ngay thay vì đợi lần audit thị giác sau.
 *
 * Bối cảnh: VIS-001 (nhãn dài đè nút — network) và VIS-002/VIS-004 (nhãn dài
 * chồng nhau + badge kỹ thuật "GENERIC" — generic).
 */

/** Props đầy đủ theo `WorkspaceProps` — render như production, không cắt xén. */
function traverseProps(labels: (string | null)[]) {
  const { config, state } = traverseState(labels);
  return { config, state, busy: false, dispatch: () => {} };
}

/** Dựng state qua CHÍNH module production (validate + init), không tự bịa. */
function traverseState(labels: (string | null)[]) {
  const mod = makeTraverseModule();
  const ids = ["A", "B", "C"];
  const v = mod.validateConfig({
    nodes: ids.map((id, i) => ({ id, label: labels[i] ?? null })),
    edges: [["A", "B"], ["A", "C"]],
    directed: false, goal: null, start: "A", variant: "bfs",
  });
  if (!v.ok) throw new Error(v.error);
  return { config: v.config, state: mod.init(v.config) };
}

describe("VIS-001 — nhãn đồ thị dài không được vẽ TRONG nút", () => {
  it("nhãn NGẮN nằm trong nút (không sinh nhãn phụ bên dưới)", () => {
    const html = renderToString(<TraverseWorkspace {...traverseProps([null, null, null])} />);
    // chỉ có 3 <text> = 3 nhãn trong nút, không có hàng nhãn thứ hai
    expect(html.match(/<text/g)?.length).toBe(3);
  });

  it("nhãn DÀI hiển thị đầy đủ và tách khỏi nút", () => {
    const long = ["Trạm Hải Đăng", "Trạm Sương Mai", "Trạm Mây Trắng Đỉnh Trời"];
    const html = renderToString(<TraverseWorkspace {...traverseProps(long)} />);
    for (const label of long) {
      expect(html).toContain(label); // KHÔNG cắt chữ, không thay bằng "…"
    }
    // 3 id trong nút + 3 nhãn dưới nút = 6 <text>: bằng chứng nhãn ĐÃ ra ngoài nút
    expect(html.match(/<text/g)?.length).toBe(6);
  });

  it("canvas cao thêm khi có nhãn dài (đủ chỗ cho hàng nhãn dưới)", () => {
    const short = renderToString(<TraverseWorkspace {...traverseProps([null, null, null])} />);
    const long = renderToString(
      <TraverseWorkspace {...traverseProps(["Trạm Hải Đăng", "Trạm Sương Mai", "Trạm Thông Xanh"])} />,
    );
    const vb = (html: string) => html.match(/viewBox="0 0 (\d+) (\d+)"/);
    expect(Number(vb(long)![2])).toBeGreaterThan(Number(vb(short)![2]));
  });
});

describe("VIS-002 — badge miền phải là tiếng Việt cho học sinh", () => {
  it("không lộ thuật ngữ kỹ thuật GENERIC ở bất kỳ đâu trong nguồn workspace", async () => {
    const src = await import("../components/SimulationWorkspace?raw" as string)
      .then((m) => (m as { default: string }).default)
      .catch(() => null);
    expect(src).not.toBeNull();  // ?raw PHẢI hoạt động, không bỏ qua êm
    // badge phải đi qua ánh xạ, KHÔNG dùng thẳng domain.toUpperCase()
    expect(src).not.toMatch(/eyebrow">\{mod\.domain\.toUpperCase\(\)\}/);
    expect(src).toContain("domainBadge");
  });
});
