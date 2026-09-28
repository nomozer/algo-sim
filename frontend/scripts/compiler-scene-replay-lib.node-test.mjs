import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

import {
  assessCssReadiness,
  assessFormationSnapshots,
  assessImmutableWindow,
  cameraMotion,
  settleCamera,
  compareClosures,
  detectRawTokenLeakage,
  evaluateEvidenceGates,
  eventDeclaredClosure,
  expectedVisibleIds,
  pollUntil,
  solidTopology,
  validateFormulaReferences,
  validateSuiteManifest,
} from "./compiler-scene-replay-lib.mjs";

test("causal closure reports every pair independently", () => {
  const result = compareClosures(["A", "B"], ["A", "C"], ["A", "B", "D"]);
  assert.equal(result.pass, false);
  assert.deepEqual(result.pairs.oracle_vs_event.missing, ["B"]);
  assert.deepEqual(result.pairs.oracle_vs_event.unexpected, ["C"]);
  assert.deepEqual(result.pairs.oracle_vs_browser.unexpected, ["D"]);
  assert.deepEqual(result.pairs.event_vs_browser.missing, ["C"]);
  assert.deepEqual(result.pairs.event_vs_browser.unexpected, ["B", "D"]);
});

test("event closure uses events only and rejects conflicting transport declarations", () => {
  const events = [
    { object: "solid", depends: ["A", "B"] },
    { object: "volume", depends: ["solid"] },
  ];
  assert.deepEqual(eventDeclaredClosure(events, "volume"), ["A", "B", "solid", "volume"]);
  assert.throws(() => eventDeclaredClosure([
    { object: "T", depends: ["solid", "plane"] },
    { object: "T", depends: ["other", "plane"] },
  ], "T"), /EVENT_DEPENDENCY_CONFLICT:T/);
});

test("topology counts unique undirected edges", () => {
  const result = solidTopology({ objects: [{
    type: "solid", vertex_ids: ["A", "B", "C", "S"],
    faces: [[0, 1, 2], [0, 3, 1], [1, 3, 2], [2, 3, 0]],
  }] });
  assert.deepEqual(result, { vertices: 4, edges: 6, faces: 4, euler: 2 });
});

test("CSS readiness is driven by computed sentinel styles, not stylesheet rules", () => {
  const baseline = {
    div: { display: "inline", fontFamily: "Times", color: "rgb(0, 0, 0)" },
    ul: { position: "static", fontFamily: "Times" },
    span: { color: "rgb(0, 0, 0)" },
  };
  const actual = {
    scene: { display: "flex", width: 900 },
    box: { position: "relative", width: 900, height: 500 },
    canvas: { width: 898, height: 498 },
    controls: { display: "flex", fontFamily: "Inter" },
    controlButton: { color: "rgb(0, 0, 0)" },
    controlText: { color: "rgb(97, 93, 89)" },
    readout: { position: "relative", fontFamily: "Inter" },
    readoutText: { color: "rgb(97, 93, 89)" },
  };
  assert.equal(assessCssReadiness(actual, baseline, 900, 900).pass, true);
  assert.equal(assessCssReadiness(actual, baseline, 901.5, 900).checks.no_document_overflow, false);
});

test("manifest requires frozen independent oracle source", () => {
  assert.throws(() => validateSuiteManifest({
    schema_version: "generic-tier-a-suite/1",
    viewports: [{ width: 1 }, { width: 2 }],
    scenarios: [{ id: "x", positive_fixture: "p", negative_fixture: "n",
      causal_target_id: "v", oracle_expected_closure: ["v"],
      topology: { vertices: 1, edges: 0, faces: 1, euler: 2 } }],
  }), /INVALID_SUITE_MANIFEST/);
});

test("frozen source hashes use canonical Git blobs, independent of checkout newlines", () => {
  const repoRoot = resolve(import.meta.dirname, "..", "..");
  const manifest = JSON.parse(readFileSync(
    resolve(import.meta.dirname, "generic-tier-a-scenarios.json"), "utf-8",
  ));
  assert.equal(validateSuiteManifest(manifest, repoRoot), true);
});

test("semantic polling returns on state change without a fixed readiness sleep", async () => {
  let tick = 0;
  let clock = 0;
  const result = await pollUntil(
    async () => ++tick,
    (value) => value === 3,
    { now: () => clock, pause: async (ms) => { clock += ms; } },
  );
  assert.equal(result, 3);
});

const typedScene = {
  objects: [
    { id: "A", type: "point3", render: "point_marker" },
    { id: "day_ABC", type: "polygon3", render: "polygon" },
    { id: "the_tich_khoi", type: "quantity", render: "readout", formula: {
      text: "V = S(ABC) × SA",
      references: [
        { entity_id: "day_ABC", display_label: "S(ABC)" },
        { entity_id: "A", display_label: "SA" },
      ],
    } },
  ],
  events: [{ step_index: 0 }, { step_index: 1 }, { step_index: 2 }],
  free_objects: ["A", "the_tich_khoi"],
  formation: { steps: [
    { visible_ids: ["A"] },
    { visible_ids: ["A", "day_ABC"] },
    { visible_ids: ["A", "day_ABC", "the_tich_khoi"] },
  ] },
};

test("formation uses exact snapshots and proves forward plus backward playback", () => {
  assert.deepEqual(expectedVisibleIds(typedScene, 0), ["A"]);
  const result = assessFormationSnapshots(typedScene, {
    forward: [0, 1, 2].map((index) => ({
      index, direction: "forward", visible_ids: expectedVisibleIds(typedScene, index),
    })),
    backward: [2, 1, 0].map((index) => ({
      index, direction: "backward", visible_ids: expectedVisibleIds(typedScene, index),
    })),
  });
  assert.equal(result.pass, true);
  assert.deepEqual(result.future_object_leakage, []);
});

test("raw token leakage and formula references are payload-driven", () => {
  assert.equal(detectRawTokenLeakage(typedScene, "Tính thể tích khối.").pass, true);
  assert.deepEqual(
    detectRawTokenLeakage(typedScene, "Gán the_tich_khoi = 5.").leaked_tokens,
    ["the_tich_khoi"],
  );
  assert.equal(validateFormulaReferences(typedScene).pass, true);
  const broken = structuredClone(typedScene);
  broken.objects[2].formula.references[1].entity_id = "missing_height";
  assert.equal(validateFormulaReferences(broken).pass, false);
});

function passingFacts() {
  return {
    edge: {
      visible_edge_ids: ["AB"], hidden_edge_ids: ["SC"], mixed_edge_ids: [],
      duplicate_visual_owner_ids: [],
    },
    orbit_required: true,
    orbit_visibility_changed: true,
    causal: {
      selected_changed: true, closure_changed: true, render_owners_changed: true,
      canvas_changed: true, bounded_pixel_delta: true, dash_signature_preserved: true,
    },
    capture_order: ["default", "causal"],
    formation_required: true,
    formation: { pass: true, future_object_leakage: [] },
    raw_token_leakage: { leaked_tokens: [] },
    formula: { unresolved: [] },
    causal_oracle_source: "independent_manifest",
    screenshot: { blank: false, premature: false },
    uncaught_exceptions: [],
    failed_api_calls: [],
  };
}

test("all required fault injections fail with their exact reason code", () => {
  const faults = [
    ["all-solid", (f) => { f.edge.hidden_edge_ids = []; }, "HIDDEN_EDGE_IDS_EMPTY"],
    ["all-dashed", (f) => { f.edge.visible_edge_ids = []; }, "VISIBLE_EDGE_IDS_EMPTY"],
    ["duplicate-overlay", (f) => { f.edge.duplicate_visual_owner_ids = ["AB"]; },
      "DUPLICATE_VISUAL_OWNER"],
    ["frozen-hidden-set", (f) => { f.orbit_visibility_changed = false; },
      "ORBIT_VISIBILITY_FROZEN"],
    ["hook-without-canvas", (f) => { f.causal.canvas_changed = false; },
      "CAUSAL_CANVAS_UNCHANGED"],
    ["default-after-causal", (f) => { f.capture_order = ["causal", "default"]; },
      "DEFAULT_CAPTURE_AFTER_CAUSAL"],
    ["highlight-dash-overwrite", (f) => { f.causal.dash_signature_preserved = false; },
      "HIGHLIGHT_DASH_OVERWRITE"],
    ["future-object", (f) => { f.formation.future_object_leakage = ["V"]; },
      "FUTURE_OBJECT_LEAK"],
    ["raw-id", (f) => { f.raw_token_leakage.leaked_tokens = ["the_tich_khoi"]; },
      "RAW_TOKEN_LEAK"],
    ["unresolved-formula", (f) => { f.formula.unresolved = ["height"]; },
      "UNRESOLVED_FORMULA_SYMBOL"],
    ["event-oracle", (f) => { f.causal_oracle_source = "events"; },
      "CAUSAL_ORACLE_NOT_INDEPENDENT"],
    ["blank-screenshot", (f) => { f.screenshot.blank = true; },
      "BLANK_OR_PREMATURE_SCREENSHOT"],
  ];
  assert.equal(evaluateEvidenceGates(passingFacts()).pass, true);
  for (const [name, mutate, reason] of faults) {
    const facts = passingFacts();
    mutate(facts);
    const result = evaluateEvidenceGates(facts);
    assert.equal(result.pass, false, name);
    assert.ok(result.reason_codes.includes(reason), `${name}:${result.reason_codes.join(",")}`);
  }
});

const camera = (dx = 0, overrides = {}) => ({
  position: [11 + dx, 5, 9],
  view_matrix_column_major: [0.4, -0.3, 0.8, 0, 0.9, 0.1, -0.4, 0, 0, 0.9, 0.4, 0, -0.1 - dx, -0.2, -15, 1],
  projection_matrix_column_major: [0.75, 0, 0, 0, 0, 2.1, 0, 0, 0, 0, -1, -1, 0, 0, -0.2, 0],
  viewport_width: 390, viewport_height: 844, device_pixel_ratio: 2, ...overrides,
});

function sampler(frames) {
  let i = 0;
  let clock = 0;
  return {
    read: async () => frames[Math.min(i++, frames.length - 1)],
    opts: { now: () => clock, pause: async (ms) => { clock += ms; }, intervalMs: 50, timeoutMs: 2_000 },
  };
}

test("ULP drift counts as settled; a real move does not", () => {
  assert.ok(cameraMotion(camera(), camera(3e-15)) < 1e-9);
  assert.ok(cameraMotion(camera(), camera(1e-4)) > 1e-9);
  assert.equal(cameraMotion(camera(), camera(0, { device_pixel_ratio: 1 })), Infinity);
});

test("settle gate waits for consecutive stable frames, then returns the settled camera", async () => {
  const frames = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((k) => ({
    snapshot: camera(k < 4 ? k * 0.01 : 0.03 + k * 1e-15), frame_count: k * 3,
  }));
  const { read, opts } = sampler(frames);
  const settled = await settleCamera(read, { ...opts, stableSamples: 3, minFrames: 6 });
  assert.ok(settled.frame_count >= 6);
  assert.ok(cameraMotion(settled.snapshot, camera(0.03)) < 1e-9);
});

test("camera that never settles fails with SETTLING_TIMEOUT and a diagnostic", async () => {
  const frames = Array.from({ length: 100 }, (_, k) => ({ snapshot: camera(k * 0.01), frame_count: k }));
  const { read, opts } = sampler(frames);
  await assert.rejects(settleCamera(read, { ...opts, stableSamples: 3, minFrames: 6 }), (e) => {
    assert.match(e.message, /^SETTLING_TIMEOUT:/);
    assert.ok(e.diagnostic.max_motion > 1e-9 && e.diagnostic.samples > 0);
    return true;
  });
});

test("immutable window: only a settled, unchanged, zero-recompute window of 120 frames passes", () => {
  const settled = { snapshot: camera(), frame_count: 40 };
  const perf = { frame_count: 121, recompute_count: 0 };
  assert.equal(assessImmutableWindow({ settled, end: camera(2e-15), perf }).pass, true);
  assert.equal(assessImmutableWindow({ settled: null, end: camera(), perf }).code, "MEASURED_BEFORE_SETTLE");
  assert.equal(assessImmutableWindow({ settled, end: camera(),
    perf: { frame_count: 90, recompute_count: 0 } }).code, "IMMUTABLE_WINDOW_TOO_SHORT");
  assert.equal(assessImmutableWindow({ settled, end: camera(1e-3), perf }).code, "CAMERA_CHANGED_AFTER_SETTLE");
  assert.equal(assessImmutableWindow({ settled, end: camera(),
    perf: { frame_count: 121, recompute_count: 2 } }).code, "IMMUTABLE_FRAME_RECOMPUTE");
});
