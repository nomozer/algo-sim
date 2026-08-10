import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { makeNetworkModule } from "./index";
import { NetworkWorkspace } from "./ui";
import { GLYPH_BOX, endpointRoleOf, nodeGlyph } from "./node-glyph";
import type { NetworkState, NodeType } from "./model";

/**
 * W4B-2S — VAI TRÒ MIỀN PHẢI NẰM Ở HÌNH, KHÔNG PHẢI Ở CHỮ.
 *
 * §18: đừng kiểm tên class. Kiểm đúng thứ hỏng — nếu **xoá hết chữ** khỏi sân
 * khấu mà học sinh không còn phân biệt được máy khách với máy chủ, thì vai trò
 * đang được chở bằng chữ.
 */

const ALL_TYPES: NodeType[] = ["client", "router", "server", "switch", "isp"];

const CONFIG = {
  problem: {},
  nodes: [
    { id: "pc", type: "client" }, { id: "r1", type: "router" },
    { id: "net", type: "isp" }, { id: "srv", type: "server" },
    { id: "sw", type: "switch" },
  ],
  links: [["pc", "r1"], ["r1", "net"], ["net", "srv"], ["r1", "sw"]],
  source: "pc",
  destination: "srv",
  notes: null,
};

function build() {
  const mod = makeNetworkModule();
  const r = mod.validateConfig(CONFIG);
  if (!r.ok) throw new Error(r.error);
  return { mod, config: r.config, state: mod.init(r.config) as NetworkState };
}

const stageHtml = (state?: NetworkState) => {
  const b = build();
  return renderToString(
    <NetworkWorkspace config={b.config} state={state ?? b.state} busy={false} dispatch={() => {}} />,
  );
};

/** Bỏ mọi nội dung chữ — còn lại đúng phần HÌNH mà học sinh nhìn thấy. */
const stripText = (html: string) =>
  html.replace(/<text[\s\S]*?<\/text>/g, "").replace(/<title>[\s\S]*?<\/title>/g, "");

/* ══ 1. HÌNH PHÂN BIỆT ĐƯỢC VAI TRÒ ═══════════════════════════════════════ */

describe("W4B-2S · DOMAIN_ROLE_CARRIED_BY_FORM", () => {
  it("mỗi loại thiết bị có hình RIÊNG — không hai vai trò nào trùng nét vẽ", () => {
    const shapes = ALL_TYPES.map((t) => {
      const g = nodeGlyph(t);
      return [g.outline, ...g.details].join("|");
    });
    expect(new Set(shapes).size, `hai vai trò dùng chung một hình: ${shapes}`)
      .toBe(ALL_TYPES.length);
  });

  it("XOÁ HẾT CHỮ: sân khấu vẫn còn ĐỦ hình riêng cho từng vai trò có mặt", () => {
    /* Đây là phép thử của chính lỗi. Trước W4B-2S, bỏ `<text>` đi thì còn lại
       năm `<circle>` giống hệt — không cách nào biết đâu là máy chủ. */
    const silent = stripText(stageHtml());
    for (const t of ALL_TYPES) {
      expect(silent, `xoá chữ xong mất dấu vai trò "${t}"`).toContain(nodeGlyph(t).outline);
    }
  });

  it("KHÔNG còn vẽ mọi thiết bị bằng cùng một hình tròn", () => {
    const silent = stripText(stageHtml());
    /* Vòng tròn CÒN được dùng (gói tin, vòng ngắm đích) nhưng không được là thứ
       DUY NHẤT dựng nên thiết bị — nên đếm: số `<path>` phải ≥ số nút. */
    const paths = (silent.match(/<path/g) ?? []).length;
    expect(paths, "thiết bị vẫn đang là hình tròn trơn").toBeGreaterThanOrEqual(5);
  });
});

/* ══ 2. NGUỒN / ĐÍCH KHÔNG DỰA VÀO CHỮ ════════════════════════════════════ */

describe("W4B-2S · ENDPOINT_ROLE_NOT_TEXT_ONLY", () => {
  it("nguồn và đích là hai VAI TRÒ tách khỏi loại thiết bị", () => {
    expect(endpointRoleOf("pc", "pc", "srv")).toBe("source");
    expect(endpointRoleOf("srv", "pc", "srv")).toBe("destination");
    expect(endpointRoleOf("r1", "pc", "srv")).toBeNull();
    // Cùng một loại thiết bị vẫn phân biệt được nguồn/đích — điều mà glyph không làm nổi.
    expect(endpointRoleOf("a", "a", "b")).toBe("source");
    expect(endpointRoleOf("b", "a", "b")).toBe("destination");
  });

  it("đích có dấu hiệu HÌNH riêng, còn sau khi xoá chữ", () => {
    const silent = stripText(stageHtml());
    // Vòng ngắm kép quanh đích: hai circle đồng tâm, một nét đứt.
    expect(silent).toMatch(/stroke-dasharray="3 4"/);
  });

  it("gói tin phân biệt được với thiết bị (§14) — thiết bị là path, gói tin là chấm", () => {
    const silent = stripText(stageHtml());
    expect(silent).toContain("accent-pink"); // gói tin
    // …và nó không dùng chung hình với bất kỳ thiết bị nào.
    for (const t of ALL_TYPES) {
      expect(nodeGlyph(t).outline).not.toContain("accent-pink");
    }
  });
});

/* ══ 3. HÌNH DẪN XUẤT TỪ ENGINE, KHÔNG TỪ CHỮ ═════════════════════════════ */

describe("W4B-2S · GEOMETRY_NOT_CHOSEN_BY_CONTEXT_STRINGS", () => {
  const code = (s: string) =>
    s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");

  it("bảng hình khoá theo NodeType của engine — không đọc nhãn/tiêu đề/đề bài", () => {
    const src = code(readFileSync(new URL("./node-glyph.ts", import.meta.url), "utf-8"));
    for (const forbidden of ["title", "summary", "problem", "notes", "description", "label."]) {
      expect(src, `node-glyph rẽ nhánh theo ngữ cảnh (${forbidden})`).not.toContain(forbidden);
    }
    expect(src).not.toMatch(/includes\(\s*["']/);
  });

  it("renderer không suy vai trò từ thứ tự nút hay từ chuỗi", () => {
    const src = code(readFileSync(new URL("./ui.tsx", import.meta.url), "utf-8"));
    expect(src).not.toMatch(/nodes\[\s*0\s*\]|nodes\[\s*nodes\.length/);
    expect(src).not.toMatch(/\.id\s*===\s*["'](client|router|server|isp|switch)["']/);
    // Hình phải tra qua chủ sở hữu, không viết thẳng path trong renderer.
    expect(src).toContain("nodeGlyph(n.type)");
  });

  it("MỌI NodeType đều có hình — không loại nào rơi về mặc định câm", () => {
    for (const t of ALL_TYPES) {
      const g = nodeGlyph(t);
      expect(g.outline.length, `${t}: thiếu hình`).toBeGreaterThan(10);
      expect(g.role.length, `${t}: thiếu tên vai trò`).toBeGreaterThan(0);
    }
    expect(GLYPH_BOX).toBe(48);
  });
});

/* ══ 4. SỰ THẬT VẪN THUỘC ENGINE ══════════════════════════════════════════ */

describe("W4B-2S · renderer vẫn KHÔNG sở hữu kết quả", () => {
  it("đổi hình không đụng tuyến/diễn biến do engine tính", () => {
    const { state } = build();
    expect(state.route[0]).toBe("pc");
    expect(state.route[state.route.length - 1]).toBe("srv");
    // Nút ngoài tuyến (switch) vẫn được vẽ nhưng không vào route.
    expect(state.route).not.toContain("sw");
  });

  it("ngắt liên kết ⇒ engine đổi tuyến; renderer chỉ đọc lại", () => {
    const { mod, state } = build();
    const cut = mod.apply(state, { type: "net_disconnect", a: "r1", b: "net" }) as NetworkState;
    expect(cut.route).toEqual([]); // chuỗi thẳng ⇒ mất đường
    const html = renderToString(
      <NetworkWorkspace config={build().config} state={cut} busy={false} dispatch={() => {}} />,
    );
    // Thiết bị vẫn vẽ đủ hình dù không còn tuyến — hình là vai trò, không phải trạng thái tuyến.
    for (const t of ALL_TYPES) expect(stripText(html)).toContain(nodeGlyph(t).outline);
  });
});
