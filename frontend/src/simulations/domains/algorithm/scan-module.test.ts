import { describe, expect, it } from "vitest";
import { makeScanModule } from "./scan-module";
import { getSimulation, registerAllSimulations } from "../../index";

/**
 * M12 — module `algorithm.scan`: adapter quanh scan-interpreter. Kiểm hợp đồng
 * SimulationModule (registry/validate/init/timeline/explain) — engine đã được
 * chứng minh riêng ở core/scan.test.ts (parity + validator + tất định).
 */

const SPEC = {
  scan_version: "1.0",
  array: [32, 31, 36, 30, 37],
  labels: ["Th 2", "Th 3", "Th 4", "Th 5", "Th 6"],
  seed: { from: "constant", value: 35, varName: "nguong" },
  compare: { kind: "to_constant", op: ">", value: 35 },
  update: { kind: "none" },
  marking: "match_highlight",
  stop: "first_match",
};

describe("module algorithm.scan (M12)", () => {
  it("đăng ký trong registry cùng domain algorithm", () => {
    registerAllSimulations();
    const mod = getSimulation("algorithm.scan");
    expect(mod).toBeDefined();
    expect(mod!.domain).toBe("algorithm");
    expect(mod!.interactionMode).toBe("progressive");
    // M15 Task 12 (W2) — scan là catch-all trong-family, KHÔNG predict (capability
    // learner-feedback ngoài phạm vi formalize family này).
    expect(mod!.predict).toBeUndefined();
  });

  it("validateConfig: nhận spec hợp lệ, từ chối spec sai", () => {
    const mod = makeScanModule();
    expect(mod.validateConfig(SPEC).ok).toBe(true);
    expect(mod.validateConfig({ ...SPEC, stop: "forever" }).ok).toBe(false);
    expect(mod.validateConfig({ ...SPEC, timeline: [] }).ok).toBe(false); // khóa lạ
  });

  it("init: timeline do interpreter sinh — tìm thấy 36 tại vị trí 3 rồi dừng", () => {
    const mod = makeScanModule();
    const r = mod.validateConfig(SPEC);
    if (!r.ok) throw new Error(r.error);
    const s = mod.init(r.config);
    expect(mod.timeline!.stepCount(s)).toBeGreaterThan(1);
    const lastStep = s.trace.steps[s.trace.steps.length - 1];
    const done = lastStep.events.find((e) => e.type === "done");
    expect(done && done.type === "done" ? done.result : "").toContain("vị trí thứ 3");
    // đúng ngữ nghĩa first_match: 30, 37 chưa bị xét
    expect(lastStep.snapshot.marks[2]).toBe("found");
    expect(lastStep.snapshot.marks[3]).toBeUndefined();
  });

  it("goToStep clamp + apply là no-op (v1 không action)", () => {
    const mod = makeScanModule();
    const r = mod.validateConfig(SPEC);
    if (!r.ok) throw new Error(r.error);
    const s = mod.init(r.config);
    const tl = mod.timeline!;
    expect(tl.currentStep(tl.goToStep(s, 99))).toBe(s.trace.steps.length - 1);
    expect(tl.currentStep(tl.goToStep(s, -5))).toBe(0);
    expect(mod.apply(s, { type: "toggle", target: "x" })).toBe(s);
  });

  it("getExplainContext serializable + mang pseudocode dẫn xuất", () => {
    const mod = makeScanModule();
    const r = mod.validateConfig(SPEC);
    if (!r.ok) throw new Error(r.error);
    const ctx = mod.getExplainContext(mod.init(r.config), r.config) as Record<string, unknown>;
    expect(JSON.parse(JSON.stringify(ctx))).toEqual(ctx);
    expect(Array.isArray(ctx.pseudocode)).toBe(true);
    expect((ctx.pseudocode as string[]).length).toBe(5);
  });
});
