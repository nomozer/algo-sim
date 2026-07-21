import { beforeAll, describe, expect, it } from "vitest";
import descriptorsJson from "./capability-descriptors.json";
import { getSimulation, registerAllSimulations } from "./index";
import { offlineCatalog } from "../data/offline-catalog";
import { andOutput } from "./domains/logic/model";
import { decimalOf } from "./domains/binary/model";
import type { Trace } from "../core/types";

/**
 * M17-Lite W0 — CROSS-LOCK authenticity contract ↔ engine FE THẬT (test-only).
 *
 * capability-descriptors.json (sinh từ backend) nay nhúng khối `authenticity`
 * per-target: required_state_fields / required_trace_events /
 * required_result_fields. Test này chạy ENGINE THẬT của từng module trên
 * config thật (offline catalog + fixture nội tuyến) và soi:
 *  - mọi required_state_field là field THẬT của state engine trả về;
 *  - mọi required_trace_event xuất hiện THẬT trong timeline/trace engine dựng;
 *  - kết quả authoritative tồn tại và do engine tính (không phải LLM).
 * Contract khai field không có thật → đỏ. Đây là "răng" của audit Wave 0:
 * renderer đẹp nhưng thiếu authoritative state/trace không thể tự nhận REAL.
 */

interface Authenticity {
  required_state_fields: string[];
  required_trace_events: string[];
  required_result_fields: string[];
  renderer_semantic_requirements: string[];
  generic_allowed: boolean;
  near_miss_mechanisms: string[];
}
const targets = (descriptorsJson as unknown as {
  runtime_targets: Record<string, { authenticity: Authenticity | null }>;
}).runtime_targets;

beforeAll(() => registerAllSimulations());

function auth(id: string): Authenticity {
  const a = targets[id]?.authenticity;
  expect(a, `${id} thiếu khối authenticity trong descriptor JSON`).toBeTruthy();
  return a as Authenticity;
}

/** init qua validateConfig THẬT của module — config sai là fail ngay. */
function initState(id: string, config: unknown): Record<string, unknown> {
  const mod = getSimulation(id);
  expect(mod, `thiếu module ${id}`).toBeDefined();
  const v = mod!.validateConfig(config);
  expect(v.ok, `${id}: config mẫu bị validator từ chối: ${v.ok ? "" : v.error}`).toBe(true);
  if (!v.ok) throw new Error("unreachable");
  return mod!.init(v.config) as Record<string, unknown>;
}

function sampleConfig(id: string): unknown {
  const entry = offlineCatalog().find((e) => e.simId === id);
  expect(entry, `không có mẫu offline cho ${id}`).toBeDefined();
  return entry!.envelope.config;
}

function traceEventTypes(trace: Trace): Set<string> {
  const out = new Set<string>();
  for (const step of trace.steps) for (const ev of step.events) out.add(ev.type);
  return out;
}

function expectStateFields(id: string, state: Record<string, unknown>) {
  for (const f of auth(id).required_state_fields) {
    expect(f in state, `${id}: state thiếu field khai trong contract: ${f}`).toBe(true);
  }
}

// ── 9 target domain algorithm (8 chuyên biệt + scan) — trace engine ──
const ALGO_IDS = [
  "algorithm.find_max",
  "algorithm.find_min",
  "algorithm.sum_if",
  "algorithm.count_if",
  "algorithm.linear_search",
  "algorithm.binary_search",
  "algorithm.bubble_sort",
  "algorithm.insertion_sort",
] as const;

/** ScanSpec nội tuyến (không có mẫu offline cho scan — discovery A). */
const SCAN_SPEC = {
  scan_version: "1.0",
  array: [3, 6, 2, 8, 5],
  seed: { from: "constant", value: 4, varName: "nguong" },
  compare: { kind: "to_constant", op: ">", value: 4 },
  update: { kind: "none" },
  marking: "match_highlight",
  stop: "first_match",
};

describe("M17 W0 — authenticity cross-lock: domain algorithm", () => {
  for (const id of ALGO_IDS) {
    it(`${id}: state + trace event + done.result đúng contract`, () => {
      const state = initState(id, sampleConfig(id));
      expectStateFields(id, state);
      const types = traceEventTypes(state.trace as Trace);
      for (const evt of auth(id).required_trace_events) {
        expect(types.has(evt), `${id}: trace thiếu event ${evt}`).toBe(true);
      }
      // done.result — kết quả authoritative do engine phát ở event done
      const steps = (state.trace as Trace).steps;
      const done = steps[steps.length - 1].events.find((e) => e.type === "done");
      expect(done, `${id}: trace không có event done`).toBeDefined();
      expect((done as { result: string }).result.length).toBeGreaterThan(0);
    });
  }

  it("algorithm.scan: state + trace event + done.result đúng contract", () => {
    const state = initState("algorithm.scan", SCAN_SPEC);
    expectStateFields("algorithm.scan", state);
    const types = traceEventTypes(state.trace as Trace);
    for (const evt of auth("algorithm.scan").required_trace_events) {
      expect(types.has(evt), `scan: trace thiếu event ${evt}`).toBe(true);
    }
    const steps = (state.trace as Trace).steps;
    expect(steps[steps.length - 1].events.some((e) => e.type === "done")).toBe(true);
  });
});

describe("M17 W0 — authenticity cross-lock: logic / binary (exploratory)", () => {
  it("logic.and_gate: state fields + andOutput dẫn xuất tất định", () => {
    const state = initState("logic.and_gate", sampleConfig("logic.and_gate"));
    expectStateFields("logic.and_gate", state);
    expect(auth("logic.and_gate").required_trace_events).toEqual([]);
    // required_result_fields = ["andOutput"] — hàm dẫn xuất THẬT của model
    const out = andOutput(state as { inputA: 0 | 1; inputB: 0 | 1 });
    expect(out === 0 || out === 1).toBe(true);
  });

  it("binary.decimal_to_binary: state fields + decimalOf khớp config", () => {
    const config = sampleConfig("binary.decimal_to_binary") as { decimalValue: number };
    const state = initState("binary.decimal_to_binary", config);
    expectStateFields("binary.decimal_to_binary", state);
    expect(auth("binary.decimal_to_binary").required_trace_events).toEqual([]);
    // engine dựng bits sao cho decimalOf(bits) == decimalValue — authoritative
    expect(decimalOf(state as { bits: (0 | 1)[]; bitWidth: number })).toBe(config.decimalValue);
  });
});

describe("M17 W0 — authenticity cross-lock: network", () => {
  it("network.packet_routing: route BFS + packetAt từng bước", () => {
    const config = sampleConfig("network.packet_routing") as {
      source: string;
      destination: string;
    };
    const state = initState("network.packet_routing", config) as unknown as {
      route: string[];
      steps: { packetAt: string }[];
    };
    expectStateFields("network.packet_routing", state as unknown as Record<string, unknown>);
    // required_result_fields = ["route"] — engine BFS tính, không từ LLM
    expect(state.route.length).toBeGreaterThan(0);
    expect(state.route[0]).toBe(config.source);
    expect(state.route[state.route.length - 1]).toBe(config.destination);
    // required_trace_events = ["packetAt"] — mọi bước mang vị trí gói tin
    expect(state.steps.length).toBeGreaterThan(0);
    for (const s of state.steps) expect(typeof s.packetAt).toBe("string");
  });

  it("network.protocol_encapsulation: đủ 4 delta kind + PDU cuối", () => {
    const state = initState(
      "network.protocol_encapsulation",
      sampleConfig("network.protocol_encapsulation"),
    ) as unknown as { steps: { delta: { kind: string }; pdu: unknown[] }[] };
    expectStateFields(
      "network.protocol_encapsulation",
      state as unknown as Record<string, unknown>,
    );
    const kinds = new Set(state.steps.map((s) => s.delta.kind));
    for (const k of auth("network.protocol_encapsulation").required_trace_events) {
      expect(kinds.has(k), `encap: thiếu delta kind ${k}`).toBe(true);
    }
    // PDU sau bước cuối tồn tại (steps.final_pdu)
    expect(state.steps[state.steps.length - 1].pdu.length).toBeGreaterThan(0);
  });
});

describe("M17 W0 — authenticity cross-lock: generic.rule_scene", () => {
  it("state fields trên mẫu offline; timeline reveal dựng bởi engine", () => {
    const state = initState("generic.rule_scene", sampleConfig("generic.rule_scene"));
    expectStateFields("generic.rule_scene", state);
  });

  it("required_trace_events reveal/move — engine dựng frame cho CẢ HAI process", () => {
    // reveal_sequence: visibleIds tăng dần theo frame
    const reveal = initState("generic.rule_scene", {
      dsl_version: "1.0",
      title: "Hiện dần hai điểm",
      objects: [
        { id: "a", type: "node", label: "A" },
        { id: "b", type: "node", label: "B" },
      ],
      rules: [],
      interactions: [],
      processes: [{ type: "reveal_sequence", steps: [{ objects: ["a"] }, { objects: ["b"] }] }],
    }) as unknown as { timeline: { visibleIds: string[] }[] };
    expect(reveal.timeline.length).toBeGreaterThan(1);
    const first = reveal.timeline[0].visibleIds.length;
    const last = reveal.timeline[reveal.timeline.length - 1].visibleIds.length;
    expect(last).toBeGreaterThan(first);

    // move_along_path: entityPos đổi theo frame (id nút, không pixel)
    const move = initState("generic.rule_scene", {
      dsl_version: "1.0",
      title: "Thực thể đi theo đường",
      objects: [
        { id: "n1", type: "node", label: "Trạm 1" },
        { id: "n2", type: "node", label: "Trạm 2" },
        { id: "rb", type: "moving_entity", label: "Robot" },
      ],
      rules: [],
      interactions: [],
      processes: [{ type: "move_along_path", entity: "rb", path: ["n1", "n2"] }],
    }) as unknown as { timeline: { entityPos: Record<string, string> }[] };
    expect(move.timeline.length).toBeGreaterThan(1);
    expect(move.timeline[0].entityPos["rb"]).toBe("n1");
    expect(move.timeline[move.timeline.length - 1].entityPos["rb"]).toBe("n2");
  });
});

describe("M17 W0 — generic_allowed chỉ generic.rule_scene", () => {
  it("mọi target khác generic_allowed=false", () => {
    for (const [id, t] of Object.entries(targets)) {
      if (!t.authenticity) continue;
      expect(t.authenticity.generic_allowed, id).toBe(id === "generic.rule_scene");
    }
  });
});
