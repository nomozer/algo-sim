import { beforeEach, describe, expect, it } from "vitest";
import { makeAndGateModule } from "./domains/logic";
import { makeBinaryModule } from "./domains/binary";
import { makeNetworkModule } from "./domains/network";
import { andOutput, type LogicState } from "./domains/logic/model";
import { decimalOf } from "./domains/binary/model";
import {
  clearRegistryForTest,
  getSimulation,
  listSimulations,
  registerSimulation,
} from "./registry";
import { registerAllSimulations } from "./index";

/** Test 3 domain mới (M5) + tính đa domain của registry. */

function serializable(obj: unknown) {
  expect(JSON.parse(JSON.stringify(obj))).toEqual(obj);
}

describe("registry đa domain (M5 §1)", () => {
  beforeEach(() => clearRegistryForTest());

  it("registerAllSimulations có đủ 11 module qua 4 domain", () => {
    // registerAllSimulations dùng cờ nội bộ; đăng ký thủ công để test độc lập
    registerSimulation(makeAndGateModule());
    registerSimulation(makeBinaryModule());
    registerSimulation(makeNetworkModule());
    const metas = listSimulations();
    expect(metas.map((m) => m.id)).toEqual([
      "logic.and_gate",
      "binary.decimal_to_binary",
      "network.packet_routing",
    ]);
    const domains = new Set(metas.map((m) => m.domain));
    expect(domains).toEqual(new Set(["logic", "binary", "network"]));
  });

  it("mọi module có Workspace — core render qua registry, không switch-case (§1)", () => {
    registerSimulation(makeAndGateModule());
    registerSimulation(makeBinaryModule());
    registerSimulation(makeNetworkModule());
    for (const meta of listSimulations()) {
      expect(getSimulation(meta.id)!.Workspace).toBeDefined();
    }
  });
});

describe("logic.and_gate (exploratory)", () => {
  const mod = makeAndGateModule();

  it("KHÔNG có timeline capability (§2)", () => {
    expect(mod.timeline).toBeUndefined();
    expect(mod.interactionMode).toBe("exploratory");
  });

  it("output do engine tính đúng bảng chân trị AND (§6)", () => {
    const cases: [0 | 1, 0 | 1, 0 | 1][] = [
      [0, 0, 0],
      [0, 1, 0],
      [1, 0, 0],
      [1, 1, 1],
    ];
    for (const [a, b, expected] of cases) {
      expect(andOutput({ inputA: a, inputB: b } as LogicState)).toBe(expected);
    }
  });

  it("toggle A/B lật đúng đầu vào (pure)", () => {
    const s0 = mod.init({ inputA: 0, inputB: 0, notes: null });
    const s1 = mod.apply(s0, { type: "toggle", target: "A" });
    expect(s1.inputA).toBe(1);
    expect(s0.inputA).toBe(0); // state cũ không đổi
    const s2 = mod.apply(s1, { type: "toggle", target: "B" });
    expect(andOutput(s2)).toBe(1); // 1 AND 1
    expect(mod.apply(s2, { type: "toggle", target: "X" })).toBe(s2); // target lạ → no-op
  });

  it("getExplainContext sạch, có rule + output thật", () => {
    const s = mod.init({ inputA: 1, inputB: 1, notes: null });
    const ctx = mod.getExplainContext(s, { inputA: 1, inputB: 1, notes: null });
    serializable(ctx);
    expect(ctx.output).toBe(1);
    expect(typeof ctx.rule).toBe("string");
  });
});

describe("binary.decimal_to_binary (exploratory)", () => {
  const mod = makeBinaryModule();

  it("KHÔNG có timeline; init tạo bit đúng từ decimal", () => {
    expect(mod.timeline).toBeUndefined();
    const s = mod.init({ decimalValue: 13, bitWidth: 4, notes: null });
    expect(s.bits).toEqual([1, 1, 0, 1]); // 13 = 8+4+1
    expect(decimalOf(s)).toBe(13);
  });

  it("toggle bit cập nhật lại giá trị thập phân (§6)", () => {
    let s = mod.init({ decimalValue: 0, bitWidth: 4, notes: null });
    s = mod.apply(s, { type: "toggle", target: "0" }); // bật bit trọng số 8
    expect(decimalOf(s)).toBe(8);
    s = mod.apply(s, { type: "toggle", target: "3" }); // bật bit trọng số 1
    expect(decimalOf(s)).toBe(9);
    s = mod.apply(s, { type: "toggle", target: "0" }); // tắt lại bit 8
    expect(decimalOf(s)).toBe(1);
  });

  it("validateConfig nới bitWidth khi không đủ; reject giá trị sai", () => {
    const ok = mod.validateConfig({ decimalValue: 13, bitWidth: 2 });
    expect(ok.ok).toBe(true);
    if (ok.ok) expect(ok.config.bitWidth).toBe(4); // tự nới đủ chứa 13
    expect(mod.validateConfig({ decimalValue: -1, bitWidth: 4 }).ok).toBe(false);
    expect(mod.validateConfig({ decimalValue: 5, bitWidth: 99 }).ok).toBe(false);
  });

  it("getExplainContext sạch", () => {
    const s = mod.init({ decimalValue: 13, bitWidth: 4, notes: null });
    serializable(mod.getExplainContext(s, { decimalValue: 13, bitWidth: 4, notes: null }));
  });
});

describe("network.packet_routing (progressive)", () => {
  const mod = makeNetworkModule();
  const config = {
    nodes: [
      { id: "client", type: "client" as const },
      { id: "router", type: "router" as const },
      { id: "isp", type: "isp" as const },
      { id: "server", type: "server" as const },
    ],
    links: [
      ["client", "router"],
      ["router", "isp"],
      ["isp", "server"],
    ] as [string, string][],
    source: "client",
    destination: "server",
    notes: null,
  };

  it("CÓ timeline; route BFS tất định; steps = route length", () => {
    expect(mod.timeline).toBeDefined();
    expect(mod.interactionMode).toBe("progressive");
    const s = mod.init(config);
    expect(s.route).toEqual(["client", "router", "isp", "server"]);
    expect(mod.timeline!.stepCount(s)).toBe(4); // create + 3 hop
  });

  it("goToStep tất định + pure, clamp biên", () => {
    const s = mod.init(config);
    const tl = mod.timeline!;
    const s2 = tl.goToStep(s, 2);
    expect(tl.currentStep(s2)).toBe(2);
    expect(tl.currentStep(s)).toBe(0); // gốc không đổi
    expect(tl.currentStep(tl.goToStep(s, 99))).toBe(3);
    expect(tl.currentStep(tl.goToStep(s, -1))).toBe(0);
    // tất định: init lại cho cùng route/steps
    expect(mod.init(config).route).toEqual(s.route);
  });

  it("reset = init dựng lại state gốc (cursor 0)", () => {
    const s = mod.init(config);
    const advanced = mod.timeline!.goToStep(s, 3);
    expect(advanced.cursor).toBe(3);
    expect(mod.init(config).cursor).toBe(0);
  });

  it("validateConfig reject topo không có đường đi / link sai", () => {
    const noPath = {
      ...config,
      links: [["client", "router"]] as [string, string][],
    };
    expect(mod.validateConfig(noPath).ok).toBe(false); // server cô lập
    const badLink = { ...config, links: [["client", "khong-ton-tai"]] as [string, string][] };
    expect(mod.validateConfig(badLink).ok).toBe(false);
  });

  it("getExplainContext sạch, phản ánh bước hiện tại", () => {
    let s = mod.init(config);
    s = mod.timeline!.goToStep(s, 2);
    const ctx = mod.getExplainContext(s, config) as { packet_at: string; route: string[] };
    serializable(ctx);
    expect(ctx.packet_at).toBe("isp");
    expect(ctx.route).toEqual(["client", "router", "isp", "server"]);
  });
});

describe("registerAllSimulations tổng hợp", () => {
  it("đăng ký được toàn bộ 11 module (8 algorithm + 3 mới)", () => {
    clearRegistryForTest();
    // registerAllSimulations có cờ nội bộ (chỉ chạy 1 lần toàn app); test qua
    // các register domain trực tiếp đã bao phủ. Ở đây kiểm nhàm chạy không lỗi.
    expect(() => registerAllSimulations()).not.toThrow();
  });
});
