import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { makeNetworkModule } from "./index";
import { NetworkWorkspace } from "./ui";
import { bfsRoute, isModified, isReachable, type NetworkState } from "./model";

/**
 * W4B-2I — THÍ NGHIỆM CẤU TRÚC CÓ RÀNG BUỘC (network.packet_routing).
 *
 * Điều phải chứng minh: học sinh sửa MÔ HÌNH → ENGINE tính lại → hệ quả hiện ra.
 * Renderer không tính định tuyến ở bất kỳ khâu nào, và bản gốc luôn dựng lại được.
 *
 * Topology dùng xuyên suốt — có ĐÚNG hai đường A→S, nên ngắt một liên kết cho
 * đường vòng, ngắt hai liên kết cho trạng thái không tới được:
 *
 *      R1 ─── R2
 *     /         \
 *    A           S
 *     \         /
 *      R3 ─── R4
 */
const CONFIG = {
  problem: {},
  nodes: [
    { id: "A", type: "client" }, { id: "R1", type: "router" }, { id: "R2", type: "router" },
    { id: "R3", type: "router" }, { id: "R4", type: "router" }, { id: "S", type: "server" },
  ],
  links: [["A", "R1"], ["R1", "R2"], ["R2", "S"], ["A", "R3"], ["R3", "R4"], ["R4", "S"]],
  source: "A",
  destination: "S",
  notes: null,
};

function build() {
  const mod = makeNetworkModule();
  const r = mod.validateConfig(CONFIG);
  if (!r.ok) throw new Error(r.error);
  return { mod, config: r.config, state: mod.init(r.config) };
}

const code = (src: string) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");

/* ══ 1. BASELINE ══════════════════════════════════════════════════════════ */

describe("W4B-2I · baseline mạng", () => {
  it("tuyến gốc là đường ngắn nhất BFS, engine tính — không phải renderer", () => {
    const { state } = build();
    expect(state.route).toEqual(["A", "R1", "R2", "S"]);
    expect(isReachable(state)).toBe(true);
    expect(isModified(state)).toBe(false);
  });

  it("config KHÔNG tới được vẫn bị VALIDATOR chặn — canonical là đúng-hoặc-từ-chối", () => {
    /* Ranh giới hai trục (CORRECTNESS.md): mô phỏng do HỆ dựng phải đúng hoặc từ
       chối, nên LLM không được phép giao một topology đứt. Học sinh thì được
       phép làm đứt — đó là thí nghiệm. Nới validator ra sẽ xoá đúng phân biệt đó. */
    const mod = makeNetworkModule();
    const r = mod.validateConfig({ ...CONFIG, links: [["A", "R1"], ["R2", "S"]] });
    expect(r.ok).toBe(false);
  });
});

/* ══ 2. SỬA MÔ HÌNH → ENGINE TÍNH LẠI ═════════════════════════════════════ */

describe("W4B-2I · WHAT_IF_RECOMPUTE_ENGINE_OWNED", () => {
  it("ngắt một chặng ⇒ engine tìm ĐƯỜNG KHÁC, không phải renderer vẽ lại", () => {
    const { mod, state } = build();
    const next = mod.apply(state, { type: "net_disconnect", a: "R1", b: "R2" }) as NetworkState;
    expect(next.route).toEqual(["A", "R3", "R4", "S"]);
    expect(isReachable(next)).toBe(true);
    // Tuyến mới phải khớp ĐÚNG BFS trên topology mới — cùng một nguồn sự thật.
    expect(next.route).toEqual(
      bfsRoute(next.nodes.map((n) => n.id), next.links, next.source, next.destination),
    );
    // Diễn biến dựng lại theo tuyến mới, con trỏ về đầu.
    expect(next.steps.map((s) => s.packetAt)).toEqual(["A", "R3", "R4", "S"]);
    expect(next.cursor).toBe(0);
  });

  it("ngắt cả hai đường ⇒ TRẠNG THÁI KHÔNG TỚI ĐƯỢC, tất định, không ném lỗi", () => {
    const { mod, state } = build();
    let s = mod.apply(state, { type: "net_disconnect", a: "R1", b: "R2" }) as NetworkState;
    s = mod.apply(s, { type: "net_disconnect", a: "R3", b: "R4" }) as NetworkState;
    expect(s.route).toEqual([]);
    expect(isReachable(s)).toBe(false);
    /* Vẫn có ĐÚNG MỘT bước, và `packetAt` vẫn là nodeId thật: renderer 2D/3D
       không phải học thêm một hình thái state nào. Đây là chỗ bản cũ NỔ
       (`byId[route[0]]` → undefined.type). */
    expect(s.steps).toHaveLength(1);
    expect(s.steps[0].packetAt).toBe("A");
    expect(s.steps[0].narration).toContain("không đi được");
  });

  it("nối lại ⇒ tuyến quay về; đường đi luôn khớp BFS ở MỌI cấu hình", () => {
    const { mod, state } = build();
    const cut = mod.apply(state, { type: "net_disconnect", a: "R1", b: "R2" }) as NetworkState;
    const back = mod.apply(cut, { type: "net_connect", a: "R1", b: "R2" }) as NetworkState;
    expect(back.route).toEqual(["A", "R1", "R2", "S"]);
    expect(isModified(back)).toBe(false);
  });

  it("BASELINE_RESET_RESTORES_ORIGINAL_SPEC — về ban đầu là phép toán, không phải undo", () => {
    const { mod, state } = build();
    let s = mod.apply(state, { type: "net_disconnect", a: "R1", b: "R2" }) as NetworkState;
    s = mod.apply(s, { type: "net_disconnect", a: "R3", b: "R4" }) as NetworkState;
    s = mod.apply(s, { type: "net_connect", a: "A", b: "S" }) as NetworkState;
    const reset = mod.apply(s, { type: "net_reset" }) as NetworkState;
    expect(reset.links).toEqual(state.links);
    expect(reset.route).toEqual(state.route);
    expect(isModified(reset)).toBe(false);
  });

  it("thí nghiệm KHÔNG BAO GIỜ ghi đè `baseline` (bản gốc còn nguyên qua mọi nhánh)", () => {
    const { mod, state } = build();
    const origin = JSON.stringify(state.baseline);
    let s: NetworkState = state;
    for (const a of [
      { type: "net_disconnect", a: "R1", b: "R2" },
      { type: "net_disconnect", a: "R3", b: "R4" },
      { type: "net_connect", a: "R1", b: "R4" },
    ] as const) {
      s = mod.apply(s, a) as NetworkState;
      expect(JSON.stringify(s.baseline), "baseline bị thí nghiệm ghi đè").toBe(origin);
    }
    // …và state gốc không bị mutate tại chỗ.
    expect(JSON.stringify(state.baseline)).toBe(origin);
  });
});

/* ══ 3. FAIL-CLOSED ═══════════════════════════════════════════════════════ */

describe("W4B-2I · WHAT_IF_CHANGE_IS_STRUCTURED_AND_VALIDATED", () => {
  it("sửa không hợp lệ ⇒ state KHÔNG ĐỔI (cùng tham chiếu), không ném, không sửa liều", () => {
    const { mod, state } = build();
    for (const bad of [
      { type: "net_disconnect", a: "A", b: "KHONG_CO" },   // nút không tồn tại
      { type: "net_disconnect", a: "A", b: "A" },          // hai đầu trùng nhau
      { type: "net_disconnect", a: "A", b: "S" },          // liên kết không tồn tại
      { type: "net_connect", a: "A", b: "R1" },            // đã nối rồi
      { type: "net_connect", a: "R1", b: "KHONG_CO" },     // nút không tồn tại
      { type: "net_connect", a: "R2", b: "R2" },           // tự nối chính nó
    ] as const) {
      expect(mod.apply(state, bad), JSON.stringify(bad)).toBe(state);
    }
  });

  it("action của domain khác rơi vào đây thì bị bỏ qua, không đổi state", () => {
    const { mod, state } = build();
    expect(mod.apply(state, { type: "whatif_swap", i: 0, j: 1 })).toBe(state);
    expect(mod.apply(state, { type: "toggle", target: "A" })).toBe(state);
  });
});

/* ══ 4. RENDERER KHÔNG SỞ HỮU ĐỊNH TUYẾN ══════════════════════════════════ */

describe("W4B-2I · renderer chỉ ĐỌC — không tính định tuyến", () => {
  it("ui.tsx không gọi BFS, không tự dựng tuyến hay diễn biến", () => {
    const src = code(readFileSync(new URL("./ui.tsx", import.meta.url), "utf-8"));
    for (const forbidden of ["bfsRoute", "buildSteps", "recompute", "hopDistance"]) {
      expect(src, `renderer tự tính định tuyến (${forbidden})`).not.toContain(forbidden);
    }
  });

  it("Quan sát: KHÔNG có liên kết nào bấm được (cổng đóng)", () => {
    const { config, state } = build();
    const html = renderToString(
      <NetworkWorkspace config={config} state={state} busy={false} dispatch={() => {}} />,
    );
    expect(html).not.toContain('role="button"');
    expect(html).toContain("Thí nghiệm");
  });

  it("không tới được ⇒ nói thẳng, và KHÔNG vẽ gói tin đứng im ở nguồn", () => {
    const { mod, config, state } = build();
    let s = mod.apply(state, { type: "net_disconnect", a: "R1", b: "R2" }) as NetworkState;
    s = mod.apply(s, { type: "net_disconnect", a: "R3", b: "R4" }) as NetworkState;
    const html = renderToString(
      <NetworkWorkspace config={config} state={s} busy={false} dispatch={() => {}} />,
    );
    expect(html).toContain("Không còn đường nào");
    expect(html).not.toContain("accent-pink"); // chấm gói tin
  });

  it("2D và 3D đọc CÙNG một state sau thí nghiệm — không có sự thật riêng cho 3D", () => {
    const { mod, state } = build();
    const next = mod.apply(state, { type: "net_disconnect", a: "R1", b: "R2" }) as NetworkState;
    expect(next.route).toEqual(["A", "R3", "R4", "S"]);

    /* Bằng chứng đúng chỗ: ĐƯỜNG TÍNH (`model.ts` — bfs/recompute/apply) không
       được biết chế độ hiển thị tồn tại. `index.ts` CÓ nhắc `"3d"` một cách hợp
       lệ — đó là khai renderer (`renderers: { "3d": … }`), không phải rẽ nhánh
       sự thật; khẳng định trên file đó sẽ cấm nhầm chính cơ chế M8 dựng ra. */
    const model = code(readFileSync(new URL("./model.ts", import.meta.url), "utf-8"));
    expect(model).not.toMatch(/visualMode|["']3d["']|renderer/i);

    // …và chỉ có MỘT module/engine: 3D là renderer, không phải simulation_id riêng.
    expect(mod.id).toBe("network.packet_routing");
    expect(Object.keys(mod.renderers ?? {})).toEqual(["3d"]);
  });
});
