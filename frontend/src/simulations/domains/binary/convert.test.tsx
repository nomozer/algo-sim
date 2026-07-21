import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import {
  BaseConvWorkspace,
  buildConvSteps,
  canonicalDigits,
  CONV_BASES,
  digitsValid,
  makeBaseConvModule,
  parseInBase,
  strategyOf,
  toBase,
  validateBaseConvConfig,
  type BaseConvConfig,
  type ConvBase,
} from "./convert-module";

/**
 * M17 W1 — binary.base_conversion: oracle ĐỘC LẬP (parseInt/Number.toString
 * của JS runtime — không phải code engine) đối chiếu mọi cặp cơ số; validator
 * fail-closed; trace bất biến; renderer đọc đúng sự thật engine.
 */

function cfg(source: ConvBase, target: ConvBase, input: string): BaseConvConfig {
  const v = validateBaseConvConfig({ sourceBase: source, targetBase: target, inputValue: input });
  if (!v.ok) throw new Error(`config mẫu bị từ chối: ${v.error}`);
  return v.config;
}

describe("engine đổi cơ số — oracle parseInt/toString trên MỌI cặp cơ số", () => {
  const VALUES = [0, 1, 7, 89, 156, 255, 2026, 65535];
  const pairs = CONV_BASES.flatMap((s) => CONV_BASES.filter((t) => t !== s).map((t) => [s, t] as const));

  it(`đủ ${pairs.length} cặp (4 cơ số × 3 đích) × ${VALUES.length} giá trị`, () => {
    expect(pairs.length).toBe(12);
    for (const [source, target] of pairs) {
      for (const value of VALUES) {
        const input = value.toString(source).toUpperCase();
        const { decimalValue, result, steps } = buildConvSteps(cfg(source, target, input));
        // oracle độc lập: JS runtime
        expect(decimalValue, `${input} b${source}`).toBe(parseInt(input, source));
        expect(result, `${input} b${source}→b${target}`).toBe(
          value.toString(target).toUpperCase(),
        );
        // bước cuối là result và khớp
        const last = steps[steps.length - 1];
        expect(last.kind).toBe("result");
        if (last.kind === "result") expect(last.output).toBe(result);
      }
    }
  });

  it("10→X chỉ có divide; X→10 chỉ có weight; X→Y có CẢ HAI + 2 stage marker", () => {
    const kinds = (c: BaseConvConfig) => new Set(buildConvSteps(c).steps.map((s) => s.kind));
    const d2h = kinds(cfg(10, 16, "2026"));
    expect(d2h.has("divide")).toBe(true);
    expect(d2h.has("weight")).toBe(false);
    const h2d = kinds(cfg(16, 10, "9C"));
    expect(h2d.has("weight")).toBe(true);
    expect(h2d.has("divide")).toBe(false);
    const o2h = buildConvSteps(cfg(8, 16, "755"));
    const k = new Set(o2h.steps.map((s) => s.kind));
    expect(k.has("weight") && k.has("divide")).toBe(true);
    expect(o2h.steps.filter((s) => s.kind === "stage")).toHaveLength(2);
  });

  it("tổng dồn weight từng bước khớp tính tay tiền tố", () => {
    const { steps } = buildConvSteps(cfg(16, 10, "9C"));
    const ws = steps.filter((s) => s.kind === "weight");
    expect(ws).toHaveLength(2);
    if (ws[0].kind === "weight") expect(ws[0].runningSum).toBe(9 * 16);
    if (ws[1].kind === "weight") expect(ws[1].runningSum).toBe(9 * 16 + 12);
  });
});

describe("validator fail-closed + canonical normalization", () => {
  it("cơ số ngoài {2,8,10,16} bị từ chối", () => {
    expect(validateBaseConvConfig({ sourceBase: 5, targetBase: 10, inputValue: "44" }).ok).toBe(false);
    expect(validateBaseConvConfig({ sourceBase: 10, targetBase: 3, inputValue: "44" }).ok).toBe(false);
  });
  it("source == target bị từ chối", () => {
    expect(validateBaseConvConfig({ sourceBase: 10, targetBase: 10, inputValue: "44" }).ok).toBe(false);
  });
  it("chữ số sai cơ số bị từ chối (8 không có '9', 2 không có '2')", () => {
    expect(validateBaseConvConfig({ sourceBase: 8, targetBase: 10, inputValue: "79" }).ok).toBe(false);
    expect(validateBaseConvConfig({ sourceBase: 2, targetBase: 10, inputValue: "102" }).ok).toBe(false);
    expect(digitsValid("9C", 16)).toBe(true);
    expect(digitsValid("9G", 16)).toBe(false);
  });
  it("vượt giới hạn 65535 bị từ chối", () => {
    expect(validateBaseConvConfig({ sourceBase: 10, targetBase: 16, inputValue: "65536" }).ok).toBe(false);
  });
  it("canonical: hex thường → HOA, bỏ 0 thừa đầu; '0' giữ nguyên", () => {
    const v = validateBaseConvConfig({ sourceBase: 16, targetBase: 10, inputValue: "009c" });
    expect(v.ok).toBe(true);
    if (v.ok) expect(v.config.inputValue).toBe("9C");
    expect(canonicalDigits("000")).toBe("0");
  });
  it("strategy dẫn xuất tất định; khai sai bị từ chối", () => {
    expect(strategyOf(10, 2)).toBe("quotient_remainder");
    expect(strategyOf(2, 10)).toBe("positional_weights");
    expect(strategyOf(8, 16)).toBe("two_stage");
    expect(
      validateBaseConvConfig({
        sourceBase: 10, targetBase: 16, inputValue: "44", strategy: "two_stage",
      }).ok,
    ).toBe(false);
  });
  it("helper parse/toBase khớp oracle runtime", () => {
    expect(parseInBase("9C", 16)).toBe(0x9c);
    expect(toBase(2026, 16)).toBe("7EA");
  });
});

describe("module + renderer đọc đúng sự thật engine", () => {
  it("init dựng timeline; cursor cuối hiện kết quả engine trong HTML", () => {
    const mod = makeBaseConvModule();
    const v = mod.validateConfig({ sourceBase: 10, targetBase: 16, inputValue: "2026" });
    expect(v.ok).toBe(true);
    if (!v.ok) return;
    const state = mod.init(v.config);
    expect(state.result).toBe("7EA");
    const last = { ...state, cursor: state.steps.length - 1 };
    const html = renderToString(
      <BaseConvWorkspace config={v.config} state={last} busy={false} dispatch={() => {}} />,
    ).replace(/<!--.*?-->/g, "");
    expect(html).toContain("7EA");
    expect(html).toContain("2026");
    // hàng chia đầu tiên của engine: 2026 : 16 = 126 dư 10 (A)
    expect(html).toContain("126");
  });

  it("timeline capability: stepCount/goToStep clamp đúng", () => {
    const mod = makeBaseConvModule();
    const v = mod.validateConfig({ sourceBase: 2, targetBase: 8, inputValue: "101101" });
    if (!v.ok) throw new Error(v.error);
    const s0 = mod.init(v.config);
    expect(mod.timeline!.stepCount(s0)).toBe(s0.steps.length);
    expect(mod.timeline!.goToStep(s0, 999).cursor).toBe(s0.steps.length - 1);
    expect(mod.timeline!.goToStep(s0, -5).cursor).toBe(0);
  });
});
