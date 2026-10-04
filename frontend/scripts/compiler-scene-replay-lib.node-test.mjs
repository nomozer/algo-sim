import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import test from "node:test";

import {
  assessCausalCanvasHues,
  assessCssReadiness,
  assessFormationSnapshots,
  DAI_SAC_VAI_TRO,
  phanLoaiSac,
  assessImmutableWindow,
  assessPlayback,
  cameraMotion,
  cameraSauCuChi,
  chieuManHinh,
  settleCamera,
  compareClosures,
  danhGiaAnhXoayThuc,
  detectRawTokenLeakage,
  doCoDauDinh,
  evaluateEvidenceGates,
  eventDeclaredClosure,
  expectedCausalTiers,
  expectedVisibleIds,
  aliasTreeRowCheck,
  isHiddenAlias,
  assessGeometrySteps,
  assessFormation,
  assessStructuredReferences,
  renderedSets,
  expectedGeometryTimeline,
  expectedSolutionRows,
  orbitCandidates,
  orbitPlanThuc,
  planOrbit,
  pollUntil,
  solidTopology,
  validateFormulaReferences,
  validateSuiteManifest,
} from "./compiler-scene-replay-lib.mjs";
// W15: export CHƯA có thì phải đỏ ĐÚNG ca của nó, không làm hỏng việc nạp cả tệp.
import * as LIB from "./compiler-scene-replay-lib.mjs";

/** Camera tổng hợp (Z lên, fov 50°) theo đúng khuôn `__geo3d_camera_snapshot`. */
function cameraSnapshot(eye, target, W, H) {
  const tru = (a, b) => a.map((x, i) => x - b[i]);
  const chuan = (a) => { const d = Math.hypot(...a); return a.map((x) => x / d); };
  const cheo = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const tich = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const z = chuan(tru(eye, target));
  const x = chuan(cheo([0, 0, 1], z));
  const y = cheo(z, x);
  const f = 1 / Math.tan((25 * Math.PI) / 180);
  const [n, xa] = [0.1, 200];
  return {
    view_matrix_column_major: [x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0,
      -tich(x, eye), -tich(y, eye), -tich(z, eye), 1],
    projection_matrix_column_major: [f / (W / H), 0, 0, 0, 0, f, 0, 0, 0, 0, (xa + n) / (n - xa), -1,
      0, 0, (2 * xa * n) / (n - xa), 0],
    viewport_width: W, viewport_height: H,
  };
}

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
    solution: { display: "grid", fontFamily: "Inter" },
    solutionTitle: { color: "rgb(97, 93, 89)" },
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

/* w10 — bí danh đáp số không phải một dòng riêng trong cây (cùng nhãn với
   nguồn), nên nó không phải vật QUAN SÁT được; cây không liệt kê nó ở bước
   nào cả mà formation vẫn phải đạt. Một vật thường vắng mặt thì vẫn trượt. */
test("formation ignores answer aliases, which the tree never lists separately", () => {
  const scene = { ...typedScene, objects: [...typedScene.objects,
    { id: "v", alias_of: "the_tich_khoi", render: "non_visual" }] };
  // Bí danh VẪN HIỆN (AD := AB) là vật quan sát được như mọi vật khác.
  assert.equal(isHiddenAlias({ id: "AD", alias_of: "AB", render: "readout" }), false);
  scene.formation = { steps: [{ visible_ids: ["A"] }, { visible_ids: ["A", "day_ABC"] },
    { visible_ids: ["A", "day_ABC", "the_tich_khoi", "v"] }] };
  const seen = (index) => expectedVisibleIds(scene, index).filter((id) => id !== "v");
  const obs = (drop = []) => ({
    forward: [0, 1, 2].map((index) => ({ index, direction: "forward",
      visible_ids: seen(index).filter((id) => !drop.includes(id)) })),
    backward: [2, 1, 0].map((index) => ({ index, direction: "backward", visible_ids: seen(index) })),
  });
  assert.equal(assessFormationSnapshots(scene, obs()).pass, true);
  assert.equal(assessFormationSnapshots(scene, obs(["day_ABC"])).pass, false);
});

/* Bí danh không đóng góp dòng nào vào cây: số dòng mang nhãn của nó bằng số
   vật KHÔNG-bí-danh cùng nhãn — 1 khi mượn nhãn nguồn, 0 khi có nhãn riêng
   (`v`). Lần đo w10 thứ 3 đỏ oan vì tiêu chí cũ đòi đúng 1 cho mọi bí danh. */
test("alias tree rows: none of its own, whether or not it shares the source label", () => {
  const scene = { objects: [{ id: "V", label: "Thể tích" },
    { id: "v", label: "v", alias_of: "V", render: "non_visual" },
    { id: "w", label: "Thể tích", alias_of: "V", render: "non_visual" }] };
  const rows = (...texts) => texts.map((text) => ({ text, disabled: false }));
  assert.equal(aliasTreeRowCheck(scene, scene.objects[1], rows("Thể tích")).pass, true);
  assert.equal(aliasTreeRowCheck(scene, scene.objects[2], rows("Thể tích")).pass, true);
  assert.equal(aliasTreeRowCheck(scene, scene.objects[1], rows("Thể tích", "v")).pass, false);
  assert.equal(aliasTreeRowCheck(scene, scene.objects[2], rows("Thể tích", "Thể tích")).pass, false);
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
    orbit_non_degenerate: true,
    causal: {
      selected_changed: true, closure_changed: true, tiers_match: true, readout_classes_match: true,
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
    ["flat-rotated-view", (f) => { f.orbit_non_degenerate = false; },
      "ORBIT_DEGENERATE_PROJECTION"],
    ["tiers-collapsed", (f) => { f.causal.tiers_match = false; }, "CAUSAL_TIERS_MISMATCH"],
    ["readout-tier-class", (f) => { f.causal.readout_classes_match = false; },
      "CAUSAL_READOUT_TIER_CLASS"],
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
    ["canvas-role-hue", (f) => { f.canvas_role_hues = { pass: false }; },
      "CAUSAL_CANVAS_ROLE_HUE"],
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

/* W12 — cảnh tổng hợp BA bước dựng: đáy (1), khối (2); bước đo diện tích và
   kết luận thể tích nhập vào bước dựng khối (khung neo = sự kiện 4). */
const PLAY_SCENE = {
  objects: [
    { id: "A", label: "A", type: "point3", render: "point_marker", origin: "free" },
    { id: "SA", label: "SA", type: "quantity", render: "readout", origin: "free" },
    { id: "day", label: "Đáy ABC", type: "polygon3", render: "polygon", origin: "derived" },
    { id: "khoi", label: "Khối chóp", type: "solid", render: "mesh", origin: "derived" },
    { id: "dt", label: "Diện tích ABC", type: "quantity", render: "readout", origin: "derived" },
    { id: "the_tich", label: "Thể tích", notation: "V", type: "quantity", render: "readout",
      origin: "derived" },
    /** Bí danh đáp số (`v = V`): cùng một kết luận, phải là MỘT dòng. */
    { id: "v", label: "v", alias_of: "the_tich", type: "quantity", render: "non_visual",
      origin: "derived" },
  ],
  events: [
    { step_index: 0, semantic_kind: "EXPLANATION", object: null },
    { step_index: 1, semantic_kind: "GEOMETRY_CONSTRUCTION", object: "day" },
    { step_index: 2, semantic_kind: "GEOMETRY_CONSTRUCTION", object: "khoi" },
    { step_index: 3, semantic_kind: "MEASUREMENT", object: "dt" },
    { step_index: 4, semantic_kind: "FINAL_RESULT", object: "the_tich" },
  ],
  formation: { steps: [["A", "SA"], ["A", "SA", "day"], ["A", "SA", "day", "khoi"],
    ["A", "SA", "day", "khoi", "dt"], ["A", "SA", "day", "khoi", "dt", "the_tich", "v"]]
    .map((visible_ids, k) => ({ step_index: k, visible_ids,
      semantic_kind: ["EXPLANATION", "GEOMETRY_CONSTRUCTION", "GEOMETRY_CONSTRUCTION",
        "MEASUREMENT", "FINAL_RESULT"][k] })) },
};
const ROWS = [
  [{ id: "SA", sec: "Dữ kiện" }],
  [{ id: "SA", sec: "Dữ kiện" }],
  [{ id: "the_tich", sec: "Kết quả" }, { id: "SA", sec: "Dữ kiện" }, { id: "dt", sec: "Các bước tính" }],
];
const frame = (t, step, extra = {}) => ({
  t, step, playing: true, selected: null, panel_open: false, highlighted: [],
  rendered: [["A"], ["A", "day"], ["A", "day", "khoi"]][step] ?? ["A"],
  rows: ROWS[step] ?? [], ...extra,
});
const genuine = () => [frame(0, 0), frame(1400, 1), frame(2800, 2),
  frame(2900, 2, { playing: false }), frame(5900, 2, { playing: false })];
const judge = (samples, extra = {}) =>
  assessPlayback({ samples, scene: PLAY_SCENE, total: 3, intervalMs: 1400, ...extra });

/* w10 — orbit chọn trước bằng số đo, không bằng cú kéo pixel cố định: góc
   xoay phải vừa giữ hình đọc được (ngưỡng góc nhìn) vừa ĐỔI tập cạnh khuất. */
const CUBE = { objects: [{ id: "K", type: "solid", render: "mesh",
  vertices: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]]
    .map((p) => p.map(String)),
  vertex_ids: ["A", "B", "C", "D", "E", "F", "G", "H"],
  faces: [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]] }] };

test("orbit plan: rotated view keeps quality AND changes the hidden-edge set", () => {
  const d = [8, 3, 6].map((x) => x / Math.hypot(8, 3, 6));
  const plan = planOrbit(CUBE, d);
  assert.ok(plan, "a qualifying orbit exists for a cube");
  assert.ok(plan.gate.pass, JSON.stringify(plan.gate));
  assert.notDeepEqual(plan.predicted_hidden_after, plan.predicted_hidden_before);
  assert.deepEqual(plan.predicted_hidden_before.sort(), ["A-B", "A-D", "A-E"].sort());
  for (const c of orbitCandidates(CUBE, d)) assert.ok(c.gate.pass && Math.abs(c.offset_deg) >= 30);
});

/* w11 — review W10-H4: ảnh xoay w10 được nhận chỉ vì còn "chiều sâu". Chính
   các camera ấy (bằng chứng w10, bất biến) phải trượt cổng không suy biến —
   chóp tam giác (A trên SC, C ra khỏi khung), chóp chữ nhật (S–A–B). */
test("rotated gate rejects the w10 rotated cameras the reviewer flagged", () => {
  const run = resolve(import.meta.dirname, "..", "..", "docs", "evaluation", "geometry", "runs",
    "w10-pedagogical-playback");
  const ev = JSON.parse(readFileSync(join(run, "results", "BROWSER_EVIDENCE.json"), "utf-8"));
  for (const family of ["triangular_pyramid", "rectangular_pyramid"]) {
    const fx = JSON.parse(readFileSync(join(run, "inputs", "fixtures", `${family}_positive.json`),
      "utf-8")).envelope.scene3d;
    for (const r of Object.values(ev.scenarios[family].positive)) {
      const g = danhGiaAnhXoayThuc(fx, r.camera_snapshots.rotated_neutral.snapshot);
      assert.equal(g.pass, false, family);
      assert.ok(g.failures.includes("FACE_NEAR_EDGE_ON") && g.failures.includes("VERTEX_ON_FOREIGN_EDGE"),
        `${family}: ${g.failures}`);
      assert.ok(g.metrics.ba_dinh_gan_thang_hang.includes("S"));
    }
  }
});

test("planned gesture camera: rotating about Z through the target keeps distance and elevation", () => {
  const tam = [0.5, 0.5, 0.5];
  const snap = cameraSnapshot([6, -5, 4], tam, 800, 600);
  cameraSauCuChi(snap, tam, 0, 0).view_matrix_column_major
    .forEach((x, i) => assert.ok(Math.abs(x - snap.view_matrix_column_major[i]) < 1e-9));
  const r = cameraSauCuChi(snap, tam, 60, 3);
  const d0 = Math.hypot(5.5, -5.5, 3.5);
  const d1 = Math.hypot(...r.position.map((x, i) => x - tam[i]));
  assert.ok(Math.abs(d1 - d0 / 0.95 ** 3) < 1e-9, "each notch dollies out by 1/0.95");
  assert.ok(Math.abs((r.position[2] - 0.5) / d1 - 3.5 / d0) < 1e-9, "elevation unchanged");
  const az = (p) => Math.atan2(p[1] - 0.5, p[0] - 0.5) * 180 / Math.PI;
  assert.ok(Math.abs(((az(r.position) - az([6, -5, 4]) + 540) % 360) - 180 - 60) < 1e-9);
});

test("planned orbit: every candidate passes the perspective gate on its simulated camera", () => {
  const snap = cameraSnapshot([6, -5, 4], [0.5, 0.5, 0.5], 800, 600);
  const plan = orbitPlanThuc(CUBE, snap, [0.5, 0.5, 0.5]);
  assert.ok(plan.length > 0);
  for (const c of plan) {
    assert.ok(c.predicted_gate.pass && [3, 6].includes(c.zoom_out_notches));
    assert.notDeepEqual(c.predicted_hidden_after, c.predicted_hidden_before);
  }
});

test("rotated gate: a key vertex under an overlay is not readable evidence", () => {
  const snap = cameraSnapshot([4, -6, 3], [0.5, 0.5, 0.5], 800, 600);
  const s = chieuManHinh(snap, [0, 0, 0]);
  const g = danhGiaAnhXoayThuc(CUBE, snap, [{ x: s.x - 5, y: s.y - 5, w: 10, h: 10 }]);
  assert.ok(g.failures.includes("KEY_VERTEX_NOT_READABLE"));
  assert.equal(g.unreadable_vertices[0].vertex, "A");
});

test("causal tiers: numerical givens, numerical intermediates, structural context", () => {
  const q = (id, origin, edges) => ({ id, type: "quantity", origin, depends: edges.map(([s]) => s),
    dependency_edges: edges.map(([source_id, relation]) => ({ source_id, relation })) });
  const scene = { objects: [
    { id: "A", origin: "free", depends: [] }, { id: "K", origin: "derived", depends: ["A"] },
    q("AB", "free", []), q("S", "derived", [["AB", "numerical"], ["K", "structural"]]),
    q("V", "derived", [["S", "numerical"], ["K", "structural"]]), q("X", "free", []) ] };
  assert.deepEqual(expectedCausalTiers(scene, "V"),
    { V: "dich", S: "trung_gian", AB: "du_kien_so", K: "boi_canh", A: "boi_canh" });
});

test("role hues: the role oranges, amber and blue classify; neutrals and type colours do not", () => {
  const loai = (h) => phanLoaiSac(...[0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)), DAI_SAC_VAI_TRO);
  for (const h of ["c2410c", "fb923c", "f59e0b"]) assert.equal(loai(h), "cam", h);
  assert.equal(loai("2563eb"), "xanh");
  // xám ngữ cảnh, nền ngữ cảnh, mực cạnh, điểm đề cho, tím mặt phẳng, xanh két
  // đường, đỏ điểm dựng, nền hổ phách mờ gần trắng
  for (const h of ["6b7280", "d1d5db", "1e293b", "374151", "7c3aed", "0f766e", "dc2626", "f5f1e9"]) {
    assert.equal(loai(h), null, h);
  }
});

test("canvas role hues: an orange or blue pixel needs a DRAWN object carrying that role", () => {
  const scene = { objects: [
    { id: "T", render: "polygon" }, { id: "S_T", render: "readout" }, { id: "P", render: "point_marker" }] };
  const tiers = { S_T: "dich", T: "boi_canh" };
  const census = (cam, xanh) => ({ total: 600_000, cam, xanh });
  // e115eede: viền thiết diện NGỮ CẢNH hổ phách, không vật vẽ nào mang tầng cam.
  assert.equal(assessCausalCanvasHues(scene, tiers, census(2400, 0)).cam.pass, false);
  assert.equal(assessCausalCanvasHues(scene, tiers, census(30, 12)).pass, true);
  // đích là một con số (readout) ⇒ xanh trên khung cũng không có chủ
  assert.equal(assessCausalCanvasHues(scene, tiers, census(0, 5000)).xanh.pass, false);
  // có vật VẼ ĐƯỢC mang tầng ⇒ không phán
  assert.equal(assessCausalCanvasHues(scene, { ...tiers, P: "dich" }, census(0, 5000)).pass, true);
  // thiếu phép đếm ⇒ trượt, không mặc định đỗ
  assert.equal(assessCausalCanvasHues(scene, tiers, undefined).pass, false);
});

test("vertex marker diameter is measured through the camera, in CSS px", () => {
  const snap = cameraSnapshot([0, -10, 0], [0, 0, 0], 800, 600);
  const donVi = (2 * 10 * Math.tan((50 * Math.PI) / 360)) / 600;
  const [m] = doCoDauDinh(snap, [{ id: "A", state: "thuong", center: [0, 0, 0], radius_world: 3 * donVi }]);
  assert.ok(Math.abs(m.diameter_px - 6) < 0.05, String(m.diameter_px));
});

/* W12 — thanh bước đi qua BƯỚC DỰNG. Oracle đọc snapshot formation của sáu
   cảnh w11 (bất biến): mỗi bước sau bước 0 mở ở sự kiện dựng, bước đo/kết luận
   không bao giờ mở bước. */
const W11_FIXTURES = resolve(import.meta.dirname, "..", "..", "docs", "evaluation", "geometry",
  "runs", "w11-pedagogical-polish", "inputs", "fixtures");
const w11Scene = (family) => JSON.parse(readFileSync(join(W11_FIXTURES, `${family}_positive.json`),
  "utf-8")).envelope.scene3d;

test("geometry timeline: steps open only at construction events that change the figure", () => {
  const counts = { triangular_pyramid: 3, triangular_prism: 3, rectangular_pyramid: 5,
    cuboid: 5, cube: 5, cross_section: 10 };
  for (const [family, count] of Object.entries(counts)) {
    const sc = w11Scene(family);
    const t = expectedGeometryTimeline(sc);
    assert.equal(t.length, count, family);
    assert.equal(t.at(-1).end, sc.events.length - 1, family);
    for (const g of t.slice(1)) assert.equal(g.kinds[0], "GEOMETRY_CONSTRUCTION", family);
  }
  const pyramid = expectedSolutionRows(w11Scene("triangular_pyramid"), 5);
  assert.deepEqual(pyramid, { givens: ["AB_length", "AC_length", "SA_length"],
    steps: ["dien_tich_day_ABC"], results: ["the_tich_khoi_chop"] });
});

test("geometry steps: a genuine observation passes; each injected fault fails its own check", () => {
  const sc = w11Scene("triangular_pyramid");
  const t = expectedGeometryTimeline(sc);
  const draw = (k) => sc.formation.steps[k].visible_ids.filter((id) =>
    sc.objects.find((o) => o.id === id)?.render !== "readout").sort();
  const genuineObs = () => ({ step_count: t.length, steps: t.map((g) => ({
    index: g.index, rendered: draw(g.anchor),
    focus_label: g.index === 0 ? "— (dữ kiện đề cho)"
      : sc.objects.find((o) => o.id === sc.events[g.start].object).label,
    solution: expectedSolutionRows(sc, g.anchor) })) });
  assert.equal(assessGeometrySteps(sc, genuineObs()).pass, true);
  const fault = (check, mutate) => {
    const obs = genuineObs();
    mutate(obs);
    assert.equal(assessGeometrySteps(sc, obs).checks[check], false, check);
  };
  fault("step_count_matches", (o) => { o.step_count = sc.events.length; });
  fault("no_static_frames", (o) => { o.steps[2].rendered = o.steps[1].rendered; });
  fault("no_measurement_geometry_steps", (o) => { o.steps[2].focus_label = "Diện tích ABC"; });
  fault("no_final_result_geometry_steps", (o) => { o.steps[2].focus_label = "Thể tích S.ABC"; });
  fault("solution_in_sync", (o) => { o.steps[1].solution.results = ["the_tich_khoi_chop"]; });
});

/* Cảnh đông điểm (chóp có đỉnh trên A + thiết diện): hầu như không phương vị
   nào đạt ngưỡng NHÃN, nhưng ảnh xoay chỉ cần CHIỀU SÂU — không mặt nào bị ép
   dẹt, hình vẫn choán và có độ sâu. Đòi ngưỡng nhãn ở đây là không bao giờ xoay. */
test("orbit plan: a crowded section scene still gets a rotation that keeps depth", () => {
  const fx = JSON.parse(readFileSync(resolve(import.meta.dirname, "..", "..", "docs", "evaluation",
    "geometry", "runs", "20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair",
    "inputs", "fixtures", "cross_section_positive.json"), "utf-8")).envelope.scene3d;
  const plan = planOrbit(fx, [0.81, 0.47, 0.34]);
  assert.ok(plan, "no rotation found");
  assert.ok(plan.gate.pass);
  assert.notDeepEqual(plan.predicted_hidden_after, plan.predicted_hidden_before);
});

test("orbit plan: no qualifying rotation ⇒ null, never a guess", () => {
  assert.equal(planOrbit(CUBE, [0, 0, 1], { offsets: [] }), null);
});

test("learner playback: one press plays every GEOMETRY step once and stops at the last one", () => {
  const verdict = judge(genuine(), {
    replay: { step: 0, selected: null, highlighted: [] },
    orbit: { before: { step: 2, rows: ROWS[2] }, after: { step: 2, rows: ROWS[2] } },
  });
  assert.equal(verdict.pass, true, JSON.stringify(verdict.checks));
});

test("learner playback: every known state-machine fault is caught by its own check", () => {
  const fault = (name, samples, extra) => {
    const verdict = judge(samples, extra);
    assert.equal(verdict.checks[name].pass, false, name);
  };
  const g = genuine();
  const last = (mutate) => g.map((f) => (f.step === 2 ? { ...f, ...mutate(f) } : f));
  fault("no_causal_selection", g.map((f, i) => (i === 2 ? { ...f, selected: "khoi" } : f)));
  fault("detail_panel_stays_closed", g.map((f, i) => (i === 3 ? { ...f, panel_open: true } : f)));
  fault("reaches_final_step", [frame(0, 0), frame(1400, 1), frame(2800, 1), frame(7000, 1)]);
  fault("advances_one_step_at_a_time", [frame(0, 0), frame(1400, 2), ...g.slice(3)]);
  fault("stops_at_final_step", g.map((f) => ({ ...f, playing: true })));
  fault("stops_at_final_step", [...g, frame(8000, 0, { playing: true })]);
  // Thanh bước còn đếm sự kiện (5) thay vì bước dựng (3).
  fault("step_count_is_geometry_steps", g, { total: 5 });
  // Một "bước" chỉ tính số: chỉ số tăng mà hình đứng yên (slideshow).
  fault("every_geometry_step_changes_the_figure", g.map((f) => ({ ...f, rendered: ["A"] })));
  fault("solution_in_sync_with_geometry_step", g.map((f) => ({ ...f, rows: [] })));
  fault("solution_in_sync_with_geometry_step",
    g.map((f) => (f.step === 1 ? { ...f, rows: ROWS[2] } : f)));
  fault("final_result_shown_once", last((f) => ({ rows: [...f.rows, { id: "v", sec: "Kết quả" }] })));
  fault("final_result_shown_once", last((f) => ({
    rows: f.rows.map((r) => (r.id === "the_tich" ? { ...r, sec: "Các bước tính" } : r)) })));
  fault("replay_resets_step_selection_highlight", g, { replay: { step: 2, selected: null, highlighted: [] } });
  fault("orbit_preserves_timeline", g,
    { orbit: { before: { step: 2, rows: ROWS[2] }, after: { step: 1, rows: ROWS[1] } } });
});

/* ─── W14: ĐỘ PHỦ VAI TRÒ DỰNG HÌNH (ba nguồn) ─────────────────────────────
   Cảnh tổng hợp: kỳ vọng độc lập, khai báo sản phẩm và quan sát được dựng tay ở
   đây — phép kiểm phải đúng khi ba nguồn khớp và trượt khi BẤT KỲ nguồn nào lệch. */
const vat = (id, type, dinh, extra = {}) => ({ id, type, render: type === "polygon3" ? "polygon"
  : type === "segment3" ? "segment" : type === "solid" ? "mesh" : type === "plane3" ? "surface"
    : "polygon", ...(type === "segment3" ? { endpoint_ids: dinh } : { vertex_ids: dinh }), ...extra });
const ROLE = { B: "CONSTRUCT_BASE", H: "CONSTRUCT_HEIGHT", T: "CONSTRUCT_TRANSLATED_FACE",
  L: "CONSTRUCT_LATERAL_BOUNDARY", C: "CLOSE_SOLID", X: "CONSTRUCT_CUTTING_OBJECT",
  I: "CONSTRUCT_INTERSECTION", Z: "CLOSE_SECTION" };
const ky = (cls, role, kind, vertices) => ({ class: cls, role: ROLE[role], kind, vertices });

function chopTamGiac() {
  return {
    scene: { objects: [
      vat("day", "polygon3", ["A", "B", "C"]), vat("cao", "segment3", ["S", "A"]),
      vat("sb", "segment3", ["S", "B"]), vat("sc", "segment3", ["S", "C"]),
      vat("khoi", "solid", ["S", "A", "B", "C"], { shape_class: "PYRAMID_LIKE",
        formation_requirements: [ROLE.B, ROLE.H, ROLE.L, ROLE.C] })] },
    expected: [ky("PYRAMID_LIKE", "B", "polygon3", ["A", "B", "C"]),
      ky("PYRAMID_LIKE", "H", "segment3", ["A", "S"]), ky("PYRAMID_LIKE", "L", "segment3", ["B", "S"]),
      ky("PYRAMID_LIKE", "L", "segment3", ["C", "S"]), ky("PYRAMID_LIKE", "C", "solid", ["A", "B", "C", "S"])],
    rendered: [[], ["day"], ["day", "cao"], ["day", "cao", "sb", "sc"], ["day", "cao", "sb", "sc", "khoi"]],
  };
}

function langTru() {
  return {
    scene: { objects: [
      vat("day", "polygon3", ["A", "B", "C"]), vat("tren", "polygon3", ["D", "E", "F"]),
      vat("ad", "segment3", ["A", "D"]), vat("be", "segment3", ["B", "E"]), vat("cf", "segment3", ["C", "F"]),
      vat("khoi", "solid", ["A", "B", "C", "D", "E", "F"], { shape_class: "PRISM_LIKE",
        formation_requirements: [ROLE.B, ROLE.T, ROLE.L, ROLE.C] })] },
    expected: [ky("PRISM_LIKE", "B", "polygon3", ["A", "B", "C"]),
      ky("PRISM_LIKE", "T", "polygon3", ["D", "E", "F"]), ky("PRISM_LIKE", "L", "segment3", ["A", "D"]),
      ky("PRISM_LIKE", "L", "segment3", ["B", "E"]), ky("PRISM_LIKE", "L", "segment3", ["C", "F"]),
      ky("PRISM_LIKE", "C", "solid", ["A", "B", "C", "D", "E", "F"])],
    rendered: [[], ["day"], ["day", "tren"], ["day", "tren", "ad", "be", "cf"],
      ["day", "tren", "ad", "be", "cf", "khoi"]],
  };
}

function thietDien() {
  return {
    scene: { objects: [vat("alpha", "plane3", []),
      { id: "T", type: "section", render: "polygon", shape_class: "SECTION",
        formation_requirements: [ROLE.X, ROLE.I, ROLE.Z] }] },
    expected: [ky("SECTION", "X", "plane3", []), ky("SECTION", "I", "section", []),
      ky("SECTION", "Z", "section", [])],
    rendered: [[], ["alpha"], ["alpha", "T#2"], ["alpha", "T#4c"], ["alpha", "T#4cf"]],
  };
}

const quanSat = (rendered, scene) => rendered.map((ids, index) =>
  ({ index, renderedSets: renderedSets(scene, ids) }));
const phan = (ca, lop, sua = (c) => c) => {
  const c = sua(structuredClone(ca));
  return assessFormation(c.expected, c.scene, quanSat(c.rendered, c.scene), [lop]);
};

test("formation roles: a genuine three-way agreement passes for every class", () => {
  assert.equal(phan(chopTamGiac(), "PYRAMID_LIKE").pass, true);
  assert.equal(phan(langTru(), "PRISM_LIKE").pass, true);
  assert.equal(phan(thietDien(), "SECTION").pass, true);
  // V7: đường cao trùng cạnh bên được phép hiện CÙNG bước với các cạnh bên khác.
  assert.equal(phan(chopTamGiac(), "PYRAMID_LIKE", (c) => {
    c.rendered[2] = ["day", "cao", "sb", "sc"];
    return c;
  }).pass, true);
});

test("formation roles: each injected fault fails with its reason", () => {
  const fault = (ca, lop, reason, sua) => {
    const v = phan(ca, lop, sua);
    assert.equal(v.pass, false, reason);
    assert.ok(v.reason_codes.includes(reason), `${reason}: ${v.reason_codes.join(",")}`);
  };
  const boKhoi = (c, ids) => {
    c.rendered = c.rendered.map((r) => r.filter((id) => !ids.includes(id)));
    return c;
  };
  fault(chopTamGiac(), "PYRAMID_LIKE", "EXPECTED_OBJECT_NOT_OBSERVED_IN_ORDER", (c) => boKhoi(c, ["sb", "sc"]));
  fault(chopTamGiac(), "PYRAMID_LIKE", "EXPECTED_OBJECT_NOT_OBSERVED_IN_ORDER", (c) => {
    c.rendered = c.rendered.map((r, i) => (i >= 1 ? [...new Set([...r, "khoi"])] : r));
    return c;
  });
  // Sản phẩm bỏ CẢ yêu cầu đường cao LẪN bước đường cao: kỳ vọng độc lập vẫn bắt.
  fault(chopTamGiac(), "PYRAMID_LIKE", "DECLARED_DISAGREES_WITH_EXPECTED", (c) => {
    c.scene.objects.at(-1).formation_requirements = [ROLE.B, ROLE.L, ROLE.C];
    return boKhoi(c, ["cao"]);
  });
  fault(chopTamGiac(), "PYRAMID_LIKE", "EXPECTED_OBJECT_NOT_OBSERVED_IN_ORDER", (c) => {
    c.scene.objects.at(-1).formation_requirements = [ROLE.B, ROLE.L, ROLE.C];
    return boKhoi(c, ["cao"]);
  });
  fault(chopTamGiac(), "PYRAMID_LIKE", "DECLARED_REQUIREMENTS_EMPTY", (c) => {
    c.scene.objects.at(-1).formation_requirements = [];
    return c;
  });
  fault(chopTamGiac(), "PYRAMID_LIKE", "DECLARED_REQUIREMENTS_EMPTY", (c) => {
    delete c.scene.objects.at(-1).shape_class;
    return c;
  });
  fault(chopTamGiac(), "PYRAMID_LIKE", "EXPECTED_REQUIREMENTS_EMPTY", (c) => {
    c.expected = [];
    return c;
  });
  fault(langTru(), "PRISM_LIKE", "DECLARED_DISAGREES_WITH_EXPECTED", (c) => {
    c.scene.objects.at(-1).formation_requirements = [ROLE.B, ROLE.L, ROLE.T, ROLE.C];
    return c;
  });
  // Đáy trên hiện CÙNG bước với cạnh bên: thứ tự nghiêm của lăng trụ bị phá.
  fault(langTru(), "PRISM_LIKE", "EXPECTED_OBJECT_NOT_OBSERVED_IN_ORDER", (c) => {
    boKhoi(c, ["tren"]);
    c.rendered = c.rendered.map((r) => (r.includes("ad") ? [...r, "tren"] : r));
    return c;
  });
  // Thiết diện khép viền mà chưa tô: chưa phải CLOSE_SECTION.
  fault(thietDien(), "SECTION", "EXPECTED_OBJECT_NOT_OBSERVED_IN_ORDER", (c) => {
    c.rendered[4] = ["alpha", "T#4c"];
    return c;
  });
  const g = evaluateEvidenceGates({ ...passingFacts(),
    formation_coverage: phan(chopTamGiac(), "PYRAMID_LIKE", (c) => boKhoi(c, ["sb", "sc"])) });
  assert.ok(g.reason_codes.includes("FORMATION_ROLE_COVERAGE"), g.reason_codes.join(","));
});

/* ─── W14: MỌI THAM CHIẾU CÓ CẤU TRÚC ĐỀU ĐƯỢC VẼ / HIỆN ───────────────────
   Quan sát "thật" mô phỏng đúng renderer: vật vẽ được của khung neo, thiết diện
   mang `#<số đỉnh>[c][f]`; bảng lời giải = lớp lời giải kỳ vọng. */
function quanSatRenderer(sc) {
  const byId = new Map(sc.objects.map((o) => [o.id, o]));
  return expectedGeometryTimeline(sc).map((g) => {
    const st = sc.formation.steps[g.anchor];
    const prog = new Map((st.geometry_progress ?? []).map((p) => [p.object_id, p]));
    const rendered = st.visible_ids.flatMap((id) => {
      const o = byId.get(id);
      if (!o || o.render === "readout" || o.render === "non_visual") return [];
      if (o.type !== "section" || !o.polygon) return [id];
      const p = prog.get(id);
      const closed = p ? p.closed : o.closed;
      const len = closed ? o.polygon.length : p.visible_edge_ids.length + 1;
      return [`${id}#${len}${closed ? "c" : ""}${(p ? p.fill_visible : o.fill_visible) ? "f" : ""}`];
    }).sort();
    return { index: g.index, rendered, solution: expectedSolutionRows(sc, g.anchor) };
  });
}

test("structured references: a renderer-faithful observation passes on every family fixture", () => {
  for (const family of ["triangular_pyramid", "triangular_prism", "rectangular_pyramid", "cuboid",
    "cube", "cross_section"]) {
    const sc = w11Scene(family);
    const v = assessStructuredReferences(sc, { steps: quanSatRenderer(sc) });
    assert.equal(v.pass, true, `${family}: ${JSON.stringify(v.fail.slice(0, 3))}`);
  }
});

test("structured references: each of (a)-(d) fails on its own injected fault", () => {
  const sai = (family, check, sua) => {
    const sc = w11Scene(family);
    const steps = quanSatRenderer(sc);
    sua(steps, sc);
    const v = assessStructuredReferences(sc, { steps });
    assert.equal(v.pass, false, check);
    assert.ok(v.fail.some((f) => f.check === check), `${check}: ${JSON.stringify(v.fail)}`);
    return v;
  };
  const t = (sc) => expectedGeometryTimeline(sc);
  // (a) vật trọng tâm của bước dựng đáy không được vẽ.
  sai("triangular_pyramid", "a", (steps, sc) => {
    const id = sc.formation.steps[t(sc)[1].start].focus_ids[0];
    steps[1].rendered = steps[1].rendered.filter((x) => x !== id);
  });
  // (b) đại lượng đang hiện ở khung neo vắng khỏi bảng lời giải.
  sai("triangular_pyramid", "b", (steps) => {
    const last = steps.at(-1);
    last.solution = { ...last.solution, givens: last.solution.givens.slice(1) };
  });
  // (c) thứ công thức thể tích nhắc tới không còn hiện ở đâu trong khung cuối.
  sai("triangular_pyramid", "c", (steps, sc) => {
    const last = steps.at(-1);
    const ids = new Set([...last.solution.steps, ...last.solution.results]);
    const ref = sc.objects.filter((o) => ids.has(o.id))
      .flatMap((o) => o.formula?.references ?? [])[0].entity_id;
    last.rendered = last.rendered.filter((x) => x !== ref);
    last.solution = Object.fromEntries(Object.entries(last.solution)
      .map(([k, v]) => [k, v.filter((x) => x !== ref)]));
  });
  // (d) renderer vẽ thiếu một cạnh thiết diện so với tiến độ.
  sai("cross_section", "d", (steps) => {
    const s = steps.find((x) => x.rendered.some((r) => /#\d+$/.test(r)));
    s.rendered = s.rendered.map((r) => r.replace(/#(\d+)$/, (_m, n) => `#${Number(n) - 1}`));
  });
  const v = sai("triangular_pyramid", "b", (steps) => {
    steps.at(-1).solution = { givens: [], steps: [], results: [] };
  });
  const g = evaluateEvidenceGates({ ...passingFacts(), structured_references: v });
  assert.ok(g.reason_codes.includes("STRUCTURED_REFERENCE_NOT_RENDERED"), g.reason_codes.join(","));
});

test("manifest refuses a scenario whose role coverage would silently enforce nothing", () => {
  const repoRoot = resolve(import.meta.dirname, "..", "..");
  const goc = JSON.parse(readFileSync(resolve(import.meta.dirname, "generic-tier-a-scenarios.json"), "utf-8"));
  for (const sua of [(s) => { delete s.formation_coverage; }, (s) => { s.formation_coverage.enforce = []; },
    (s) => { s.formation_coverage.enforce = ["SPHERE_LIKE"]; }, (s) => { s.expected_formation = []; }]) {
    const m = structuredClone(goc);
    sua(m.scenarios[0]);
    assert.throws(() => validateSuiteManifest(m, repoRoot), /formation_coverage:triangular_pyramid/);
  }
});

// ── W15 · SECTION_FILL_DISTINGUISHABLE — bộ chấm THUẦN trên cặp mẫu (bật/tắt tô) ──
//
// Cặp mẫu tổng hợp theo đúng mô hình phối màu (sRGB, "over") của cảnh: nền trắng, mặt sau
// khối xám 0.22, miếng mặt cắt tím 0.2, mặt trước khối xám 0.22; ba mức sáng 1 · 0.75 · 0.55.
// Renderer CŨ: tô hổ phách 0.16 nằm DƯỚI mặt cắt và mặt trước (đồng phẳng, không renderOrder).
// Renderer MỚI: tô vẽ SAU CÙNG. Ngưỡng do ASSUMPTION_CERTIFICATE_AMENDMENT đăng ký (Task 3).
const MAU_TO = [0xf5, 0x9e, 0x0b], MAU_MP = [0x7c, 0x3a, 0xed], MAU_KHOI = [0x64, 0x74, 0x8b];
const tren = (duoi, mau, a) => duoi.map((d, i) => d * (1 - a) + mau[i] * a);
const sang = (mau, k) => mau.map((x) => x * k);
const nenCanh = (k) => tren(tren(tren([255, 255, 255], sang(MAU_KHOI, k), 0.22), MAU_MP, 0.2), sang(MAU_KHOI, k), 0.22);
const cap = (on, off) => ({ on: on.map(Math.round), off: off.map(Math.round) });
const MUC_SANG = [1, 0.75, 0.55];
const toMoi = (a = 0.45) => MUC_SANG.map((k) => cap(tren(nenCanh(k), sang(MAU_TO, k), a), nenCanh(k)));
const toCu = () => MUC_SANG.map((k) => cap(
  tren(tren(tren(tren([255, 255, 255], sang(MAU_KHOI, k), 0.22), sang(MAU_TO, k), 0.16), MAU_MP, 0.2),
    sang(MAU_KHOI, k), 0.22), nenCanh(k)));
const khongTo = () => MUC_SANG.map((k) => cap(nenCanh(k), nenCanh(k)));
const cham = (trangThai, mau) => {
  assert.equal(typeof LIB.assessSectionFill, "function", "assessSectionFill chưa có (W15 Task 8)");
  return LIB.assessSectionFill(trangThai, mau);
};

test("W15 section fill: deltaE76 is CIE76 on sRGB D65", () => {
  assert.equal(typeof LIB.deltaE76, "function", "deltaE76 chưa có (W15 Task 8)");
  assert.equal(LIB.deltaE76([10, 20, 30], [10, 20, 30]), 0);
  assert.ok(Math.abs(LIB.deltaE76([255, 255, 255], [0, 0, 0]) - 100) < 1e-6);
});

test("W15 section fill: a genuine fill passes on the closed step", () => {
  const kq = cham("closed", toMoi());
  assert.equal(kq.pass, true, JSON.stringify(kq));
});

test("W15 section fill: a missing fill fails on the closed step", () => {
  assert.equal(cham("closed", khongTo()).pass, false);
});

test("W15 section fill: a fill present before closing fails", () => {
  assert.equal(cham("pre_close", toMoi()).pass, false);
  assert.equal(cham("pre_close", khongTo()).pass, true);
});

test("W15 section fill: a fill not removed after stepping back fails", () => {
  assert.equal(cham("rewound", toMoi()).pass, false);
  assert.equal(cham("rewound", khongTo()).pass, true);
});

test("W15 section fill: the old 0.16 coplanar composite fails the registered threshold", () => {
  const kq = cham("closed", toCu());
  assert.equal(kq.pass, false, JSON.stringify(kq));
});

test("W15 section fill: no samples never passes", () => {
  for (const s of ["closed", "pre_close", "rewound"]) assert.equal(cham(s, []).pass, false, s);
});

test("W15 section fill: interior samples keep the registered margin from every projected edge", () => {
  assert.equal(typeof LIB.diemMauThietDien, "function", "diemMauThietDien chưa có (W15 Task 8)");
  const snap = cameraSnapshot([6, -8, 6], [0, 0, 0], 800, 600);
  const vuong = [["-2", "-2", "0"], ["2", "-2", "0"], ["2", "2", "0"], ["-2", "2", "0"]];
  const mau = LIB.diemMauThietDien(vuong, snap);
  assert.ok(mau.length > 20, `chỉ ${mau.length} mẫu`);
  const p = vuong.map((v) => LIB.chieuManHinh(snap, v.map(Number)));
  const cachCanh = ([x, y]) => Math.min(...p.map((a, i) => {
    const b = p[(i + 1) % p.length], dx = b.x - a.x, dy = b.y - a.y;
    const t = Math.max(0, Math.min(1, ((x - a.x) * dx + (y - a.y) * dy) / (dx * dx + dy * dy)));
    return Math.hypot(x - (a.x + t * dx), y - (a.y + t * dy));
  }));
  assert.ok(mau.every((q) => cachCanh(q) >= LIB.NGUONG_TO_THIET_DIEN.margin_px));
});

test("W15 section fill: a polygon behind the camera gives no samples (the gate fails safe)", () => {
  assert.equal(typeof LIB.diemMauThietDien, "function", "diemMauThietDien chưa có (W15 Task 8)");
  const snap = cameraSnapshot([1, 0, 10], [0, 0, 0], 800, 600);
  assert.deepEqual(LIB.diemMauThietDien([["0", "0", "20"], ["1", "0", "20"], ["0", "1", "20"]], snap), []);
});

test("W15 manifest requires three distinct negative kinds per scenario", () => {
  const m = JSON.parse(readFileSync(resolve(import.meta.dirname, "generic-tier-a-scenarios.json"), "utf-8"));
  const sai = structuredClone(m);
  sai.scenarios[0].negative_fixtures = (sai.scenarios[0].negative_fixtures ?? []).slice(0, 1);
  assert.throws(() => validateSuiteManifest(sai), /INVALID_SUITE_MANIFEST:.*negatives:triangular_pyramid/);
});

test("W17 manifest: extra refusal kinds come from a closed set and always declare their cause", () => {
  const m = JSON.parse(readFileSync(resolve(import.meta.dirname, "generic-tier-a-scenarios.json"), "utf-8"));
  const them = (n) => { const x = structuredClone(m); x.scenarios[0].negative_fixtures.push(n); return x; };
  const am = { fixture: "fixtures/x.json", expected: { product_error_code: "e", stage_reached: "s" } };
  assert.throws(() => validateSuiteManifest(them({ kind: "system_cause", ...am })), /negatives:triangular_pyramid/);
  assert.throws(() => validateSuiteManifest(them({ kind: "made_up", ...am,
    expected: { ...am.expected, refusal_cause: "UNKNOWN" } })), /negatives:triangular_pyramid/);
  const sai = structuredClone(m);
  sai.scenarios[0].served_fixtures = [{ kind: "x", fixture: "fixtures/x.json", expected: {} }];
  assert.throws(() => validateSuiteManifest(sai), /served:triangular_pyramid/);
});

test("W15 section fill: thresholds in code equal the pre-registered ones", () => {
  const doc = readFileSync(resolve(import.meta.dirname, "..", "..", "docs", "architecture",
    "ASSUMPTION_CERTIFICATE_AMENDMENT.md"), "utf-8");
  const m = doc.match(/SECTION_FILL_THRESHOLDS = (\{[^}]*\})/);
  assert.ok(m, "ngưỡng chưa được đăng ký trong ASSUMPTION_CERTIFICATE_AMENDMENT.md");
  assert.deepEqual(LIB.NGUONG_TO_THIET_DIEN, JSON.parse(m[1]));
});

// ── W16 · §14.4 — tô thiết diện nằm DƯỚI cạnh khối; bộ lấy mẫu W15 khớp đăng ký §11 ──

const VUONG_TD = [["-2", "-2", "0"], ["2", "-2", "0"], ["2", "2", "0"], ["-2", "2", "0"]];
const SNAP_TD = cameraSnapshot([6, -8, 6], [0, 0, 0], 800, 600);
const cachDoan = ([x, y], a, b) => {
  const dx = b.x - a.x, dy = b.y - a.y;
  const t = Math.max(0, Math.min(1, ((x - a.x) * dx + (y - a.y) * dy) / (dx * dx + dy * dy || 1)));
  return Math.hypot(x - (a.x + t * dx), y - (a.y + t * dy));
};

test("W16 section fill sampler: margin around EVERY projected solid edge and vertex marker (§11)", () => {
  const canh = [{ id: "khoi::edge:P-Q", a: [-3, 0, 0], b: [3, 0, 0] }];
  const cham = [{ id: "M", center: [1, 1, 0], radius_world: 0.15 }];
  const mau = LIB.diemMauThietDien(VUONG_TD, SNAP_TD, { canh, cham });
  assert.ok(mau.length > 10, `chỉ ${mau.length} mẫu`);
  const [a, b] = [canh[0].a, canh[0].b].map((p) => LIB.chieuManHinh(SNAP_TD, p));
  assert.ok(mau.every((q) => cachDoan(q, a, b) >= LIB.NGUONG_TO_THIET_DIEN.margin_px), "mẫu nằm trên cạnh khối");
  const [d] = LIB.doCoDauDinh(SNAP_TD, cham);
  const c = LIB.chieuManHinh(SNAP_TD, cham[0].center);
  assert.ok(mau.every(([x, y]) => Math.hypot(x - c.x, y - c.y) >= d.diameter_px / 2 + LIB.NGUONG_TO_THIET_DIEN.margin_px),
    "mẫu nằm trên dấu điểm");
  assert.ok(LIB.diemMauThietDien(VUONG_TD, SNAP_TD).length > mau.length, "không vật cản thì nhiều mẫu hơn");
});

test("W17 section fill sampler: no sample under a DOM label box over the canvas (§11 measures the fill)", () => {
  // Lượt trình duyệt T7: nhãn "Diện tích thiết diện = 9" (nền 90 % giấy) nằm trên đúng vùng mẫu —
  // mẫu dưới nó đọc nền nhãn, ΔE bật/tắt tô ≈ 10 % (min 2.8 < T_ON_MIN) dù phần tô vẫn rõ.
  const tat = LIB.diemMauThietDien(VUONG_TD, SNAP_TD);
  const [cx, cy] = [tat.reduce((s, q) => s + q[0], 0) / tat.length, tat.reduce((s, q) => s + q[1], 0) / tat.length];
  const hop = [{ x: cx - 40, y: cy - 9, w: 80, h: 18 }];
  const mau = LIB.diemMauThietDien(VUONG_TD, SNAP_TD, { hop });
  const m = LIB.NGUONG_TO_THIET_DIEN.margin_px;
  assert.ok(mau.length > 10 && mau.length < tat.length, `${mau.length} / ${tat.length}`);
  assert.ok(mau.every(([x, y]) => x < hop[0].x - m || x > hop[0].x + hop[0].w + m
    || y < hop[0].y - m || y > hop[0].y + hop[0].h + m), "mẫu nằm dưới nhãn");
});

test("W16 under-edges sampling: core band within 1 CSS px of a crossing edge, references 4 px aside", () => {
  assert.equal(typeof LIB.diemCanhQuaThietDien, "function", "diemCanhQuaThietDien chưa có (W16)");
  const canh = [{ id: "qua", a: [-3, 0, 0], b: [3, 0, 0] }, { id: "ngoai", a: [5, 5, 0], b: [6, 6, 0] }];
  const ra = LIB.diemCanhQuaThietDien(VUONG_TD, SNAP_TD, canh, []);
  assert.deepEqual(ra.map((x) => x.id), ["qua"]);
  const [a, b] = [canh[0].a, canh[0].b].map((p) => LIB.chieuManHinh(SNAP_TD, p));
  assert.ok(ra[0].core.length >= 3 && ra[0].ref.length >= 3, JSON.stringify(ra[0]).slice(0, 200));
  assert.ok(ra[0].core.every((q) => cachDoan(q, a, b) <= 1 + 1e-9));
  assert.ok(ra[0].ref.every((q) => Math.abs(cachDoan(q, a, b) - 4) < 1e-6));
  // nửa px: dải lõi phủ cả điểm ảnh thiết bị ở DPR 2 (ảnh mobile)
  const lech = new Set(ra[0].core.map((q) => Math.round(cachDoan(q, a, b) * 2)));
  assert.ok(lech.has(1) && lech.has(2), [...lech].join(","));
});

// Mô hình phối màu "over" (sRGB) của §14.4: nền B, tô hổ phách 0.45, nét #1e293b độ phủ c, độ đục α.
const NEN_TD = [205, 206, 212], TO_TD = [0xf5, 0x9e, 0x0b], NET_TD = [0x1e, 0x29, 0x3b];
const tron = (duoi, mau, a) => duoi.map((d, i) => Math.round(d * (1 - a) + mau[i] * a));
const NEN_BAT = tron(NEN_TD, TO_TD, 0.45);
const thamChieu = () => Array.from({ length: 6 }, () => ({ on: NEN_BAT, off: NEN_TD }));
const canhTrenTo = (c, alpha) => ({ id: "e", ref: thamChieu(), core: [
  { on: tron(NEN_BAT, NET_TD, c * alpha), off: tron(NEN_TD, NET_TD, c * alpha) },
  { on: NEN_BAT, off: NEN_TD }] });
const toTrenCanh = (c, alpha) => ({ id: "e", ref: thamChieu(), core: [
  { on: tron(tron(NEN_TD, NET_TD, c * alpha), TO_TD, 0.45), off: tron(NEN_TD, NET_TD, c * alpha) },
  { on: NEN_BAT, off: NEN_TD }] });

test("W16 SECTION_FILL_UNDER_EDGES: an edge drawn above the fill passes, even half-covered and dashed", () => {
  assert.equal(typeof LIB.assessSectionFillUnderEdges, "function", "assessSectionFillUnderEdges chưa có (W16)");
  for (const [c, alpha] of [[1, 1], [0.5, 1], [0.5, 0.9], [1, 0.9]]) {
    const kq = LIB.assessSectionFillUnderEdges([canhTrenTo(c, alpha)]);
    assert.equal(kq.pass, true, `${c}/${alpha} ${JSON.stringify(kq)}`);
  }
});

test("W16 SECTION_FILL_UNDER_EDGES: the fill drawn over the edge fails", () => {
  assert.equal(typeof LIB.assessSectionFillUnderEdges, "function", "assessSectionFillUnderEdges chưa có (W16)");
  for (const [c, alpha] of [[1, 1], [0.5, 1], [1, 0.9]]) {
    const kq = LIB.assessSectionFillUnderEdges([toTrenCanh(c, alpha)]);
    assert.equal(kq.pass, false, `${c}/${alpha} ${JSON.stringify(kq)}`);
    assert.ok(kq.edges[0].rho >= 1, JSON.stringify(kq.edges[0]));
  }
});

test("W16 section-fill page code compiles (no identifier clash with the shared PNG prelude)", async () => {
  // Lượt trình duyệt 55cde06e: mã trong trang khai `const doc` trùng tên hàm giải ảnh của
  // `giaiMaHaiKhung` ⇒ SyntaxError trong trang ⇒ 0 mẫu ở mọi trạng thái. Test node của thư viện
  // không chạy mã ấy; ở đây BIÊN DỊCH đúng chuỗi mà bộ chạy gửi vào trang.
  const { Script } = await import("node:vm");
  const SUITE = await import("./compiler-scene-suite.mjs");
  assert.equal(typeof SUITE.maDocCapDiem, "function", "maDocCapDiem chưa có (W16)");
  const ma = SUITE.maDocCapDiem({ encoded: "AAAA" }, { encoded: "AAAA" },
    { viewport_width: 800, viewport_height: 600 }, [[1, 2]], [{ id: "e", core: [[1, 2]], ref: [[3, 4]] }]);
  assert.doesNotThrow(() => new Script(ma), "mã trong trang không biên dịch được");
});

test("W16 SECTION_FILL_UNDER_EDGES: an edge that is not drawn fails; no crossing edge is not a pass", () => {
  assert.equal(typeof LIB.assessSectionFillUnderEdges, "function", "assessSectionFillUnderEdges chưa có (W16)");
  const khongVe = { id: "e", ref: thamChieu(), core: [{ on: NEN_BAT, off: NEN_TD }] };
  assert.equal(LIB.assessSectionFillUnderEdges([khongVe]).pass, false);
  const rong = LIB.assessSectionFillUnderEdges([]);
  assert.deepEqual([rong.pass, rong.reason], [false, "NOT_APPLICABLE_NO_CROSSING_EDGE"]);
});

/* W17 · §15.5 — the on-figure quantity label checks. One camera that maps world (x, y) straight to
 * pixels (orthographic, 100 px per unit, canvas 400×300, origin at the canvas centre). */
const CAM_W17 = (() => {
  const p = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  const v = [0.5, 0, 0, 0, 0, 2 / 3, 0, 0, 0, 0, 1, 0, 0, 0, -1, 1];
  return { projection_matrix_column_major: p, view_matrix_column_major: v, viewport_width: 400, viewport_height: 300 };
})();
const CANH_W17 = {
  free_objects: ["A", "B", "AB"],
  objects: [
    { id: "A", type: "point3", xyz: ["0", "0", "0"] }, { id: "B", type: "point3", xyz: ["1", "0", "0"] },
    { id: "AB", type: "quantity", origin: "free", value: "3",
      annotation: { kind: "length", category: "measurement", subject_ids: ["A", "B"], anchor: "segment" } },
    { id: "V", type: "quantity", origin: "derived", value: "9",
      annotation: { kind: "length", category: "result", subject_ids: ["A", "B"], anchor: "segment" } },
  ],
  events: [{ step_index: 0, action: "INIT", object: null }, { step_index: 1, action: "MEASURE", object: "V",
    semantic_kind: "MEASUREMENT" }, { step_index: 2, action: "MEASURE", object: "V", semantic_kind: "FINAL_RESULT" }],
};

test("W17 annotation oracle: a result label only from its concluding event", () => {
  const tatCa = { showAll: true };
  assert.deepEqual(LIB.expectedAnnotationIds(CANH_W17, 0, tatCa), ["AB"]);
  assert.deepEqual(LIB.expectedAnnotationIds(CANH_W17, 1, tatCa), ["AB"]);
  assert.deepEqual(LIB.expectedAnnotationIds(CANH_W17, 2, tatCa), ["AB", "V"]);
});

/* W18 §16.5–16.7: default compact (given data), selection focus, same_as, witness anchor. */
const CANH_W18 = {
  free_objects: ["A", "B", "C", "AB"],
  objects: [
    { id: "A", type: "point3", xyz: ["0", "0", "0"] }, { id: "B", type: "point3", xyz: ["1", "0", "0"] },
    { id: "C", type: "point3", xyz: ["0", "1", "0"] },
    { id: "AB", type: "quantity", origin: "free", value: "3",
      annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" } },
    { id: "h", type: "quantity", origin: "derived", value: "3", depends: ["A", "B"],
      annotation: { kind: "length", category: "measurement", role: "intermediate", subject_ids: ["A", "B"],
        anchor: "segment", same_as: "AB" } },
    { id: "d", type: "quantity", origin: "derived", value: "1", depends: ["C", "AB"],
      dependency_edges: [{ source_id: "AB", relation: "numerical" }],
      annotation: { kind: "distance", category: "measurement", role: "intermediate", subject_ids: ["C", "A"],
        anchor: "witness", witness: { from: "C", foot: ["0", "0", "0"], on: "A",
          marker: { u: ["1", "0", "0"], v: ["0", "1", "0"] } } } },
    { id: "V", type: "quantity", origin: "derived", value: "9", depends: ["d"],
      dependency_edges: [{ source_id: "d", relation: "numerical" }],
      annotation: { kind: "length", category: "result", role: "result", subject_ids: ["A", "B"], anchor: "segment" } },
  ],
  events: [{ step_index: 0, action: "INIT", object: null },
    { step_index: 1, action: "MEASURE", object: "h", semantic_kind: "MEASUREMENT" },
    { step_index: 2, action: "MEASURE", object: "d", semantic_kind: "MEASUREMENT" },
    { step_index: 3, action: "MEASURE", object: "V", semantic_kind: "MEASUREMENT" },
    { step_index: 4, action: "MEASURE", object: "V", semantic_kind: "FINAL_RESULT" }],
};

test("W18 annotation oracle: compact default, selection focus, same_as, show-all", () => {
  assert.deepEqual(LIB.expectedAnnotationIds(CANH_W18, 4), ["AB"]);
  assert.deepEqual(LIB.expectedAnnotationIds(CANH_W18, 4, { showAll: true }), ["AB", "V", "d"]);
  assert.deepEqual(LIB.expectedAnnotationIds(CANH_W18, 4, { selectedId: "V" }), ["AB", "V", "d"]);
  assert.deepEqual(LIB.expectedAnnotationIds(CANH_W18, 3, { selectedId: "V" }), ["AB", "d"]);   // not before its conclusion
  assert.deepEqual(LIB.expectedAnnotationIds(CANH_W18, 4, { selectedId: "C" }), ["AB", "d"]);   // object ⇒ quantities about it
  assert.deepEqual(LIB.expectedAnnotationIds(CANH_W18, 4, { selectedId: "h" }), ["AB"]);        // same_as ⇒ its owner
  assert.deepEqual(LIB.annotationWorldAnchor(CANH_W18, CANH_W18.objects.find((o) => o.id === "d").annotation),
    [0, 0.5, 0]);
});

test("W18 one detail region and witness drawn exactly for shown distance labels", () => {
  assert.equal(LIB.assessDetailRegion({ formula_text: "V = 3·3", regions: ["inspector"] }).pass, true);
  assert.deepEqual(LIB.assessDetailRegion({ formula_text: "V = 3·3", regions: ["inspector", "solution:V"] })
    .reason_codes, ["DETAIL_REGIONS_2"]);
  assert.deepEqual(LIB.assessDetailRegion({ formula_text: "V = 3·3", regions: [] }).reason_codes, ["DETAIL_REGIONS_0"]);
  assert.equal(LIB.assessWitness({ scene: CANH_W18, shownIds: ["AB", "d"], witnessIds: ["d"] }).pass, true);
  assert.deepEqual(LIB.assessWitness({ scene: CANH_W18, shownIds: ["AB", "d"], witnessIds: [] }).reason_codes,
    ["WITNESS_MISSING:d"]);
  assert.deepEqual(LIB.assessWitness({ scene: CANH_W18, shownIds: ["AB"], witnessIds: ["d"] }).reason_codes,
    ["WITNESS_NOT_SHOWN_LABEL:d"]);
});

test("W17 annotation boxes: inside, near the independently projected anchor, no overlaps", () => {
  // AB's anchor (0.5, 0, 0) projects to (250, 150): view x = 0.5·0.5 = 0.25 ⇒ (1.25 / 2)·400.
  const tot = { id: "AB", box: { x: 205, y: 126, w: 40, h: 18 } };
  const ok = LIB.assessAnnotationBoxes({ scene: CANH_W17, step: 0, boxes: [tot], points: [], camera: CAM_W17,
    mustShow: ["AB"] });
  assert.equal(ok.pass, true, ok.reason_codes.join());
  const cases = [
    [{ id: "AB", box: { x: 205, y: 60, w: 40, h: 18 } }, [], "ANNOTATION_FAR_FROM_SUBJECT"],
    [{ id: "AB", box: { x: 380, y: 126, w: 40, h: 18 } }, [], "ANNOTATION_OUTSIDE_CANVAS"],
    [tot, [{ id: "A", x: 210, y: 130, w: 20, h: 16 }], "ANNOTATION_OVER_POINT_LABEL"],
    [{ id: "V", box: { x: 205, y: 126, w: 40, h: 18 } }, [], "ANNOTATION_NOT_AVAILABLE"],
  ];
  for (const [b, points, code] of cases) {
    const kq = LIB.assessAnnotationBoxes({ scene: CANH_W17, step: 0, boxes: [b], points, camera: CAM_W17 });
    assert.ok(kq.reason_codes.some((c) => c.startsWith(code)), `${code}: ${kq.reason_codes.join()}`);
  }
  const chong = LIB.assessAnnotationBoxes({ scene: CANH_W17, step: 2, camera: CAM_W17, points: [],
    boxes: [tot, { id: "V", box: { x: 215, y: 130, w: 40, h: 18 } }] });
  assert.ok(chong.reason_codes.some((c) => c.startsWith("ANNOTATION_OVERLAP")), chong.reason_codes.join());
  const thieu = LIB.assessAnnotationBoxes({ scene: CANH_W17, step: 0, boxes: [], points: [], camera: CAM_W17,
    mustShow: ["AB"] });
  assert.deepEqual(thieu.reason_codes, ["ANNOTATION_MISSING:AB"]);
});

/* Same pose, the last ULPs rewritten (OrbitControls damping, see CAMERA_SETTLE_TOLERANCE) vs a pose a
 * learner could see (view translated by 0.01). */
const camLech = (d) => ({ ...CAM_W17, view_matrix_column_major: CAM_W17.view_matrix_column_major
  .map((x, i) => (i === 12 ? x + d : x)) });
const CAM_ULP = camLech(1e-14);
const CAM_KHAC = camLech(0.01);

test("W18 show-all isolation and W17 causal restore record each state separately", () => {
  const on = { annotation_ids: ["AB", "V"], dash_signature: { e: ["VISIBLE_SOLID"] },
    rendered_object_ids: ["A"], camera: CAM_W17, selected_id: null, step: 4 };
  const off = { ...on, annotation_ids: ["AB"] };
  const k = { expectedOn: ["AB", "V"], expectedOff: ["AB"] };
  assert.equal(LIB.assessShowAllIsolation({ on, off, back: on, ...k }).pass, true);
  // Lượt trình duyệt T7: camera chỉ lệch ở ULP cuối (1e-14) giữa bật/tắt — không phải "đổi camera".
  assert.equal(LIB.assessShowAllIsolation({ on, off: { ...off, camera: CAM_ULP }, back: on, ...k }).pass, true);
  assert.deepEqual(LIB.assessShowAllIsolation({ on, off: { ...off, camera: CAM_KHAC }, back: on, ...k }).reason_codes,
    ["SHOW_ALL_OFF_CHANGED_CAMERA"]);
  assert.deepEqual(LIB.assessShowAllIsolation({ on, off: { ...off, dash_signature: {} }, back: on, ...k }).reason_codes,
    ["SHOW_ALL_OFF_CHANGED_DASH_SIGNATURE"]);
  assert.deepEqual(LIB.assessShowAllIsolation({ on, off: on, back: on, ...k }).reason_codes,
    ["SHOW_ALL_OFF_LABELS_NOT_ORACLE"]);
  const n = { camera: CAM_W17, selected_id: null, scroll_y: 120, canvas_sha256: "x" };
  const s = { ...n, selected_id: "V", scroll_y: 300 };
  assert.equal(LIB.assessCausalRestore({ neutral: n, selected: s, restored: n }).pass, true);
  assert.equal(LIB.assessCausalRestore({ neutral: n, selected: { ...s, camera: CAM_ULP },
    restored: { ...n, camera: CAM_ULP } }).pass, true);
  assert.deepEqual(LIB.assessCausalRestore({ neutral: n, selected: s, restored: { ...n, scroll_y: 300 } })
    .reason_codes, ["SCROLL_NOT_RESTORED"]);
  assert.deepEqual(LIB.assessCausalRestore({ neutral: n, selected: s, restored: { ...n, camera: CAM_KHAC } })
    .reason_codes, ["RESTORE_MOVED_CAMERA"]);
  assert.deepEqual(LIB.assessCausalRestore({ neutral: n, selected: { ...s, camera: CAM_KHAC }, restored: n })
    .reason_codes, ["SELECTION_MOVED_CAMERA"]);
});

test("W17 causal restore: capture noise (≤ 1 per channel) is not a change; anything larger is", () => {
  const n = { camera: CAM_W17, selected_id: null, scroll_y: 120, canvas_sha256: "x" };
  const s = { ...n, selected_id: "V", scroll_y: 300 };
  const r = { ...n, canvas_sha256: "y" };
  // Lượt đo cuối 83f101e4: cùng camera, hộp nhãn, độ mờ và vị trí cuộn, khung lúc nghỉ vẫn có lúc
  // lệch trên toàn khung, mỗi kênh ≤ 1 (chuỗi chẩn đoán cube/mobile).
  assert.equal(LIB.NHIEU_KHUNG_TOI_DA, 1);
  assert.equal(LIB.assessCausalRestore({ neutral: n, selected: s, restored: r,
    canvasDelta: { same_size: true, max_channel_delta: 1, changed_pixels: 47791 } }).pass, true);
  assert.deepEqual(LIB.assessCausalRestore({ neutral: n, selected: s, restored: r,
    canvasDelta: { same_size: true, max_channel_delta: 2, changed_pixels: 1 } }).reason_codes, ["CANVAS_NOT_RESTORED"]);
  assert.deepEqual(LIB.assessCausalRestore({ neutral: n, selected: s, restored: r,
    canvasDelta: { same_size: false, max_channel_delta: 0, changed_pixels: 0 } }).reason_codes, ["CANVAS_NOT_RESTORED"]);
  // Không đo được độ lệch ⇒ không suy ra "bằng nhau".
  assert.deepEqual(LIB.assessCausalRestore({ neutral: n, selected: s, restored: r }).reason_codes,
    ["CANVAS_NOT_RESTORED"]);
  assert.deepEqual(LIB.assessCausalRestore({ neutral: n, selected: s, restored: r,
    canvasDelta: { same_size: true, max_channel_delta: 1, changed_pixels: 3 } }).canvas,
  { equal_bytes: false, same_size: true, max_channel_delta: 1, changed_pixels: 3 });
});

test("role tokens are machine data: on screen they are a raw-token leak", () => {
  const sc = { objects: [{ id: "khoi", type: "solid", render: "mesh", shape_class: "PYRAMID_LIKE",
    formation_roles: ["CLOSE_SOLID"], formation_requirements: ["CONSTRUCT_BASE"] }],
  formation: { steps: [{ formation_roles: ["DECLARE_ENTITIES"] }] } };
  assert.equal(detectRawTokenLeakage(sc, "Dựng đáy ABC.").pass, true);
  for (const token of ["PYRAMID_LIKE", "CLOSE_SOLID", "CONSTRUCT_BASE", "DECLARE_ENTITIES"]) {
    assert.deepEqual(detectRawTokenLeakage(sc, `Bước: ${token}`).leaked_tokens, [token], token);
  }
});
