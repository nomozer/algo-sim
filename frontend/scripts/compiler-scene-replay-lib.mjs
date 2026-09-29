import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { relative, resolve } from "node:path";

// Bộ đo góc nhìn của CHÍNH sản phẩm (Node ≥ 22.18 bóc kiểu TS; hai module này
// không import gì) — không một định nghĩa thứ hai trong bộ đo.
import { cauTrucGocNhin } from "../src/simulations/domains/geometry/scene3d-model.ts";
import {
  NGUONG_GOC_NHIN, danhGiaGocNhin, datNguong, doLuoiGocNhin,
} from "../src/simulations/domains/geometry/scene3d-camera.ts";

const cameraModules = { cauTrucGocNhin, danhGiaGocNhin, datNguong, doLuoiGocNhin, NGUONG_GOC_NHIN };

export const sortedUnique = (values) => [...new Set(values ?? [])].sort();

export function setDiff(expected, actual) {
  const left = sortedUnique(expected);
  const right = sortedUnique(actual);
  return {
    missing: left.filter((id) => !right.includes(id)),
    unexpected: right.filter((id) => !left.includes(id)),
  };
}

function comparePair(leftName, left, rightName, right) {
  const diff = setDiff(left, right);
  return {
    left: leftName,
    right: rightName,
    missing: diff.missing,
    unexpected: diff.unexpected,
    pass: diff.missing.length === 0 && diff.unexpected.length === 0,
  };
}

export function compareClosures(oracle, declared, observed) {
  const sets = {
    oracle_expected_closure: sortedUnique(oracle),
    event_declared_closure: sortedUnique(declared),
    browser_observed_closure: sortedUnique(observed),
  };
  const pairs = {
    oracle_vs_event: comparePair(
      "oracle_expected_closure", sets.oracle_expected_closure,
      "event_declared_closure", sets.event_declared_closure,
    ),
    oracle_vs_browser: comparePair(
      "oracle_expected_closure", sets.oracle_expected_closure,
      "browser_observed_closure", sets.browser_observed_closure,
    ),
    event_vs_browser: comparePair(
      "event_declared_closure", sets.event_declared_closure,
      "browser_observed_closure", sets.browser_observed_closure,
    ),
  };
  return { ...sets, pairs, pass: Object.values(pairs).every((p) => p.pass) };
}

export function eventDeclaredClosure(events, targetId) {
  const dependencies = new Map();
  for (const event of events ?? []) {
    const objectIds = Array.isArray(event.objects)
      ? event.objects
      : event.object ? [event.object] : [];
    for (const objectId of objectIds) {
      const next = sortedUnique(event.depends);
      if (dependencies.has(objectId)) {
        const before = dependencies.get(objectId);
        if (JSON.stringify(before) !== JSON.stringify(next)) {
          throw new Error(`EVENT_DEPENDENCY_CONFLICT:${objectId}`);
        }
      } else {
        dependencies.set(objectId, next);
      }
    }
  }
  const seen = new Set();
  const queue = [targetId];
  while (queue.length > 0) {
    const id = queue.shift();
    if (!id || seen.has(id)) continue;
    seen.add(id);
    queue.push(...(dependencies.get(id) ?? []));
  }
  return sortedUnique(seen);
}

export function solidTopology(scene) {
  const solid = (scene?.objects ?? []).find((object) => object.type === "solid");
  if (!solid) return { vertices: 0, edges: 0, faces: 0, euler: null };
  const edges = new Set();
  for (const face of solid.faces ?? []) {
    for (let index = 0; index < face.length; index += 1) {
      const a = face[index];
      const b = face[(index + 1) % face.length];
      edges.add(a < b ? `${a}:${b}` : `${b}:${a}`);
    }
  }
  const vertices = (solid.vertex_ids ?? solid.vertices ?? []).length;
  const faces = (solid.faces ?? []).length;
  return { vertices, edges: edges.size, faces, euler: vertices - edges.size + faces };
}

/* ─── ORBIT CHỌN TRƯỚC (w10) ────────────────────────────────────────────────
 * Cú kéo pixel cố định (w09) có thể dừng ở một góc ép dẹt hình, hoặc không đổi
 * cạnh khuất nào — và cổng chờ một điều không bao giờ tới (ORBIT_EVIDENCE_
 * TIMEOUT). Ở đây góc xoay quanh Z được CHỌN TRƯỚC: đạt ngưỡng góc nhìn của
 * chính sản phẩm (`scene3d-camera.ts`) VÀ đổi tập cạnh khuất dự đoán. Dự đoán
 * dùng mặt trước/sau của khối lồi — chỉ để chọn cử chỉ; phán quyết vẫn là tập
 * cạnh sản phẩm báo ra. */
const num = (s) => { const [a, b] = String(s).split("/"); return b ? Number(a) / Number(b) : Number(a); };

function predictedHidden(scene, d) {
  const hidden = [];
  for (const solid of (scene.objects ?? []).filter((o) => o.type === "solid" && o.faces)) {
    const p = solid.vertices.map((v) => v.map(num));
    const c = p.reduce((s, q) => s.map((x, i) => x + q[i] / p.length), [0, 0, 0]);
    const back = solid.faces.map((f) => {
      const [a, b, e] = [p[f[0]], p[f[1]], p[f[2]]];
      const u = b.map((x, i) => x - a[i]);
      const v = e.map((x, i) => x - a[i]);
      let n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
      if (n.reduce((s, x, i) => s + x * (a[i] - c[i]), 0) < 0) n = n.map((x) => -x);
      return n.reduce((s, x, i) => s + x * d[i], 0) < 0;
    });
    const adj = new Map();
    solid.faces.forEach((f, k) => f.forEach((ia, i) => {
      const ib = f[(i + 1) % f.length];
      const key = [solid.vertex_ids[Math.min(ia, ib)], solid.vertex_ids[Math.max(ia, ib)]].join("-");
      adj.set(key, [...(adj.get(key) ?? []), k]);
    }));
    for (const [key, faces] of adj) if (faces.every((k) => back[k])) hidden.push(key);
  }
  return hidden.sort();
}

export const ORBIT_OFFSETS_DEG = [60, -60, 45, -45, 75, -75, 90, -90, 120, -120, 30, -30];

/** Ảnh ĐÃ XOAY chỉ cần CHIỀU SÂU: hình vẫn choán, có độ sâu, không mặt nào bị
 *  ép thành một đường. Ngưỡng NHÃN (khoảng đỉnh, đỉnh–cạnh) là của khung mặc
 *  định; cảnh đông điểm hầu như không phương vị nào đạt nó (đo w10: thiết diện
 *  chỉ 30°/60°), nên đòi nó ở đây là không bao giờ xoay được. */
export function hasDepth(q, tran, nguong = cameraModules.NGUONG_GOC_NHIN) {
  return q.dienTichBao >= nguong.tiLeDienTichBao * tran.dienTichBao
    && q.doSau >= nguong.tiLeDoSau * tran.doSau
    && q.matNghiengMin >= nguong.matNghiengMin;
}

export function planOrbit(scene, direction, { offsets = ORBIT_OFFSETS_DEG, camera = cameraModules } = {}) {
  const { diem, canh, mat } = camera.cauTrucGocNhin(scene.objects ?? []);
  const { tran } = camera.doLuoiGocNhin(diem, canh, mat);
  const before = predictedHidden(scene, direction);
  for (const offset of offsets) {
    const a = (offset * Math.PI) / 180;
    const d = [direction[0] * Math.cos(a) - direction[1] * Math.sin(a),
      direction[0] * Math.sin(a) + direction[1] * Math.cos(a), direction[2]];
    const after = predictedHidden(scene, d);
    const quality = camera.danhGiaGocNhin(diem, canh, mat, d);
    const pass = canh.length === 0 || hasDepth(quality, tran, camera.NGUONG_GOC_NHIN);
    if (pass && JSON.stringify(after) !== JSON.stringify(before)) {
      return { offset_deg: offset, direction_after: d, quality, depth_pass: pass,
        predicted_hidden_before: before, predicted_hidden_after: after };
    }
  }
  return null;
}

export function assessCssReadiness(actual, baseline, scrollWidth, viewportWidth) {
  const checks = {
    scene_layout: Boolean(actual.scene)
      && actual.scene.display === "flex" && actual.scene.width > 100,
    canvas_layout: Boolean(actual.box)
      && ["relative", "absolute"].includes(actual.box.position),
    canvas_size: Boolean(actual.canvas)
      && actual.canvas.width > 100 && actual.canvas.height > 100
      && actual.canvas.width <= actual.box.width + 2
      && actual.canvas.height <= actual.box.height + 2,
    controls_styled: Boolean(actual.controls && actual.controlButton && actual.controlText)
      && actual.controls.display !== baseline.div.display
      && actual.controls.fontFamily !== baseline.div.fontFamily
      && actual.controlText.color !== baseline.span.color,
    readout_styled: Boolean(actual.readout && actual.readoutText)
      && actual.readout.position !== baseline.ul.position
      && actual.readout.fontFamily !== baseline.ul.fontFamily
      && actual.readoutText.color !== baseline.span.color,
    no_document_overflow: scrollWidth <= viewportWidth + 1,
  };
  return { checks, pass: Object.values(checks).every(Boolean) };
}

export function expectedVisibleIds(scene, step) {
  const formationStep = scene?.formation?.steps?.[step];
  if (formationStep && Array.isArray(formationStep.visible_ids)) {
    return sortedUnique(formationStep.visible_ids);
  }
  const visible = new Set(scene?.free_objects ?? []);
  for (const event of scene?.events ?? []) {
    if ((event.step_index ?? 0) > step) continue;
    if (Array.isArray(event.objects)) event.objects.forEach((id) => visible.add(id));
    else if (event.object) visible.add(event.object);
  }
  return sortedUnique([...visible].filter((id) =>
    (scene?.objects ?? []).some((object) => object.id === id)));
}

const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export function detectRawTokenLeakage(scene, visibleText) {
  const candidates = new Set();
  for (const object of scene?.objects ?? []) {
    for (const value of [object.id, object.type, object.render]) {
      if (typeof value === "string" && value.includes("_")) candidates.add(value);
    }
  }
  const leakedTokens = [...candidates].filter((token) =>
    new RegExp(`(^|[^\\p{L}\\p{N}_])${escapeRegex(token)}($|[^\\p{L}\\p{N}_])`, "u")
      .test(String(visibleText ?? "")));
  const snakeTokens = String(visibleText ?? "").match(/\b[\p{L}\p{N}]+_[\p{L}\p{N}_]+\b/gu) ?? [];
  const leaked = sortedUnique([...leakedTokens, ...snakeTokens]);
  return { leaked_tokens: leaked, pass: leaked.length === 0 };
}

export function validateFormulaReferences(scene) {
  const ids = new Set((scene?.objects ?? []).map((object) => object.id));
  const unresolved = [];
  for (const object of scene?.objects ?? []) {
    const formula = object.formula;
    if (!formula) continue;
    for (const reference of formula.references ?? []) {
      if (!ids.has(reference.entity_id)
          || !String(reference.display_label ?? "").trim()) {
        unresolved.push({ object_id: object.id, reference });
      }
    }
  }
  return { unresolved, pass: unresolved.length === 0 };
}

export function assessFormationSnapshots(scene, observations) {
  const expectedSteps = scene?.formation?.steps ?? [];
  const forward = observations?.forward ?? [];
  const backward = observations?.backward ?? [];
  const mismatch = [];
  // Bí danh đáp số (w10) là MỘT kết luận với nguồn, không có dòng riêng trong
  // cây ⇒ không phải vật quan sát được; nguồn của nó vẫn được kiểm như mọi vật.
  const aliases = new Set((scene?.objects ?? []).filter((o) => o.alias_of).map((o) => o.id));
  for (const observation of [...forward, ...backward]) {
    const expected = expectedVisibleIds(scene, observation.index).filter((id) => !aliases.has(id));
    const diff = setDiff(expected, observation.visible_ids);
    if (diff.missing.length || diff.unexpected.length) {
      mismatch.push({ index: observation.index, direction: observation.direction, ...diff });
    }
  }
  const forwardOrder = forward.map((item) => item.index);
  const backwardOrder = backward.map((item) => item.index);
  const expectedForward = expectedSteps.map((_, index) => index);
  const expectedBackward = [...expectedForward].reverse();
  return {
    mismatch,
    forward_complete: JSON.stringify(forwardOrder) === JSON.stringify(expectedForward),
    backward_complete: JSON.stringify(backwardOrder) === JSON.stringify(expectedBackward),
    future_object_leakage: mismatch.flatMap((item) => item.unexpected),
    pass: mismatch.length === 0
      && JSON.stringify(forwardOrder) === JSON.stringify(expectedForward)
      && JSON.stringify(backwardOrder) === JSON.stringify(expectedBackward),
  };
}

export function evaluateEvidenceGates(facts) {
  const reasons = [];
  if ((facts.edge?.visible_edge_ids ?? []).length === 0) reasons.push("VISIBLE_EDGE_IDS_EMPTY");
  if ((facts.edge?.hidden_edge_ids ?? []).length === 0) reasons.push("HIDDEN_EDGE_IDS_EMPTY");
  if ((facts.edge?.mixed_edge_ids ?? []).length > 0) reasons.push("MIXED_EDGE_POLICY");
  if ((facts.edge?.duplicate_visual_owner_ids ?? []).length > 0) {
    reasons.push("DUPLICATE_VISUAL_OWNER");
  }
  if (facts.orbit_required && facts.orbit_visibility_changed !== true) {
    reasons.push("ORBIT_VISIBILITY_FROZEN");
  }
  if (facts.causal?.selected_changed !== true) reasons.push("CAUSAL_SELECTION_UNCHANGED");
  if (facts.causal?.closure_changed !== true) reasons.push("CAUSAL_CLOSURE_UNCHANGED");
  if (facts.causal?.render_owners_changed !== true) reasons.push("CAUSAL_RENDER_OWNERS_UNCHANGED");
  if (facts.causal?.canvas_changed !== true) reasons.push("CAUSAL_CANVAS_UNCHANGED");
  if (facts.causal?.bounded_pixel_delta !== true) reasons.push("CAUSAL_PIXEL_DELTA_UNBOUNDED");
  if (facts.causal?.dash_signature_preserved !== true) reasons.push("HIGHLIGHT_DASH_OVERWRITE");
  const order = facts.capture_order ?? [];
  const neutral = order.indexOf("neutral_final") >= 0
    ? order.indexOf("neutral_final") : order.indexOf("default");
  const causal = order.indexOf("causal_selected") >= 0
    ? order.indexOf("causal_selected") : order.indexOf("causal");
  if (neutral < 0 || causal < 0 || neutral > causal) {
    reasons.push("DEFAULT_CAPTURE_AFTER_CAUSAL");
  }
  if ((facts.formation?.future_object_leakage ?? []).length > 0) {
    reasons.push("FUTURE_OBJECT_LEAK");
  }
  if (facts.formation_required && facts.formation?.pass !== true) {
    reasons.push("FORMATION_FORWARD_BACKWARD_INCOMPLETE");
  }
  if ((facts.raw_token_leakage?.leaked_tokens ?? []).length > 0) reasons.push("RAW_TOKEN_LEAK");
  if ((facts.formula?.unresolved ?? []).length > 0) reasons.push("UNRESOLVED_FORMULA_SYMBOL");
  if (facts.causal_oracle_source !== "independent_manifest") {
    reasons.push("CAUSAL_ORACLE_NOT_INDEPENDENT");
  }
  if (facts.screenshot?.blank === true || facts.screenshot?.premature === true) {
    reasons.push("BLANK_OR_PREMATURE_SCREENSHOT");
  }
  if ((facts.uncaught_exceptions ?? []).length > 0) reasons.push("UNCAUGHT_EXCEPTION");
  if ((facts.failed_api_calls ?? []).length > 0) reasons.push("FAILED_API_CALL");
  return { reason_codes: sortedUnique(reasons), pass: reasons.length === 0 };
}

export function sha256File(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

export function sha256GitBlob(repoRoot, path) {
  const absolute = resolve(repoRoot, path);
  const repositoryPath = relative(repoRoot, absolute).replaceAll("\\", "/");
  if (repositoryPath === ".." || repositoryPath.startsWith("../")) {
    throw new Error(`SOURCE_OUTSIDE_REPOSITORY:${path}`);
  }
  const content = execFileSync("git", ["show", `HEAD:${repositoryPath}`], {
    cwd: repoRoot,
  });
  return createHash("sha256").update(content).digest("hex");
}

export function validateSuiteManifest(manifest, repoRoot) {
  const errors = [];
  if (manifest?.schema_version !== "generic-tier-a-suite/1") {
    errors.push("schema_version");
  }
  if (!Array.isArray(manifest?.viewports) || manifest.viewports.length !== 2) {
    errors.push("viewports");
  }
  if (!Array.isArray(manifest?.scenarios) || manifest.scenarios.length !== 6) {
    errors.push("scenarios");
  }
  const names = new Set();
  for (const scenario of manifest?.scenarios ?? []) {
    if (!scenario.id || names.has(scenario.id)) errors.push(`scenario_id:${scenario.id}`);
    names.add(scenario.id);
    if (!scenario.positive_fixture || !scenario.negative_fixture) {
      errors.push(`fixtures:${scenario.id}`);
    }
    if (!scenario.causal_target_id
        || !scenario.oracle_expected_closure?.includes(scenario.causal_target_id)) {
      errors.push(`oracle_target:${scenario.id}`);
    }
    if (!scenario.oracle_source?.path || !scenario.oracle_source?.sha256
        || scenario.oracle_source?.hash_basis !== "git_blob_at_measurement_commit") {
      errors.push(`oracle_source:${scenario.id}`);
    } else if (repoRoot) {
      if (sha256GitBlob(repoRoot, scenario.oracle_source.path)
          !== scenario.oracle_source.sha256) {
        errors.push(`oracle_source_hash:${scenario.id}`);
      }
    }
    for (const key of ["vertices", "edges", "faces", "euler"]) {
      if (typeof scenario.topology?.[key] !== "number") errors.push(`topology:${scenario.id}:${key}`);
    }
  }
  const requiredScenarios = [
    "triangular_pyramid", "triangular_prism", "rectangular_pyramid",
    "cuboid", "cube", "cross_section",
  ];
  if (JSON.stringify([...names].sort()) !== JSON.stringify(requiredScenarios.sort())) {
    errors.push("cross_family_scenarios");
  }
  if (errors.length > 0) throw new Error(`INVALID_SUITE_MANIFEST:${errors.join(",")}`);
  return true;
}

export async function pollUntil(read, predicate, {
  timeoutMs = 25_000,
  intervalMs = 100,
  now = () => Date.now(),
  pause = (ms) => new Promise((resolvePause) => setTimeout(resolvePause, ms)),
} = {}) {
  const deadline = now() + timeoutMs;
  let last;
  do {
    last = await read();
    if (predicate(last)) return last;
    await pause(intervalMs);
  } while (now() <= deadline);
  throw new Error(`POLL_TIMEOUT:${JSON.stringify(last)}`);
}

/* ─── CAMERA SETTLING (w09) ─────────────────────────────────────────────────
 * OrbitControls damping keeps rewriting the pose in its last ULPs after
 * auto-fit (mobile: every frame, forever), so "settled" cannot mean
 * byte-identical. Relative matrix motion ≤ 1e-9 moves a projected point by
 * ≤ ~1e-6 px at ≤ 2000 physical px — far below the 0.5 px oracle tolerance —
 * while any pose change a learner could see is orders of magnitude larger. */
export const CAMERA_SETTLE_TOLERANCE = 1e-9;

export function cameraMotion(a, b) {
  if (!a || !b || a.viewport_width !== b.viewport_width || a.viewport_height !== b.viewport_height
      || a.device_pixel_ratio !== b.device_pixel_ratio) return Infinity;
  let worst = 0;
  for (const key of ["view_matrix_column_major", "projection_matrix_column_major"]) {
    a[key].forEach((value, index) => {
      worst = Math.max(worst, Math.abs(value - b[key][index]) / Math.max(1, Math.abs(value)));
    });
  }
  return worst;
}

/** Poll `read()` → `{snapshot, frame_count}` until the camera has stayed within
 *  tolerance for `stableSamples` consecutive samples spanning ≥ `minFrames`
 *  animation frames. Never settling is a failure with a diagnostic. */
export async function settleCamera(read, {
  stableSamples = 5, minFrames = 30, tolerance = CAMERA_SETTLE_TOLERANCE,
  timeoutMs = 10_000, intervalMs = 50,
  now = () => Date.now(),
  pause = (ms) => new Promise((resolvePause) => setTimeout(resolvePause, ms)),
} = {}) {
  const deadline = now() + timeoutMs;
  let previous = null;
  let streakStart = null;
  let streak = 0;
  let samples = 0;
  let maxMotion = 0;
  let lastMotion = null;
  do {
    const current = await read();
    samples += 1;
    if (previous) {
      lastMotion = cameraMotion(previous.snapshot, current.snapshot);
      maxMotion = Math.max(maxMotion, lastMotion);
      if (lastMotion <= tolerance) {
        streak += 1;
        streakStart ??= previous;
      } else {
        streak = 0;
        streakStart = null;
      }
      if (streak >= stableSamples && current.frame_count - streakStart.frame_count >= minFrames) {
        return { ...current, settle_samples: samples, settle_max_motion: maxMotion };
      }
    }
    previous = current;
    await pause(intervalMs);
  } while (now() <= deadline);
  const error = new Error(`SETTLING_TIMEOUT:${JSON.stringify({ samples, last_motion: lastMotion })}`);
  error.diagnostic = { samples, streak, last_motion: lastMotion, max_motion: maxMotion, tolerance };
  throw error;
}

/** The 120-frame window only means "immutable" after settling: zero
 *  recomputation, and the camera at the end still equals the settled one. */
export function assessImmutableWindow({ settled, end, perf, frames = 120 }) {
  const details = { frames: perf?.frame_count ?? 0, recompute_count: perf?.recompute_count ?? null,
    motion_since_settle: settled ? cameraMotion(settled.snapshot, end) : null };
  const fail = (code) => ({ pass: false, code, ...details });
  if (!settled) return fail("MEASURED_BEFORE_SETTLE");
  if (details.frames < frames) return fail("IMMUTABLE_WINDOW_TOO_SHORT");
  if (details.motion_since_settle > CAMERA_SETTLE_TOLERANCE) return fail("CAMERA_CHANGED_AFTER_SETTLE");
  if (details.recompute_count !== 0) return fail("IMMUTABLE_FRAME_RECOMPUTE");
  return { pass: true, code: "IMMUTABLE_WINDOW_PASS", ...details };
}

/* ─── LEARNER PLAYBACK (w10) ────────────────────────────────────────────────
 * Judges a timeline recorded while a learner only pressed Play once: no
 * causal selection, no detail panel, one step at a time to the final step,
 * then stop. `events[k].semantic_kind` comes from the scene the page loaded. */
export function assessPlayback({
  samples, events, objects = [], total, intervalMs, replay = null, orbit = null,
}) {
  const checks = {};
  const add = (name, pass, details = undefined) => {
    checks[name] = { pass: Boolean(pass), ...(details === undefined ? {} : { details }) };
  };
  const last = total - 1;
  const byStep = new Map();
  for (const sample of samples) if (!byStep.has(sample.step)) byStep.set(sample.step, sample);
  const settledAt = (step) => [...samples].reverse().find((sample) => sample.step === step);
  const steps = samples.map((sample) => sample.step);
  add("starts_at_step_zero", steps[0] === 0, { first: steps[0] });
  add("no_causal_selection", samples.every((sample) => sample.selected === null),
    samples.filter((sample) => sample.selected !== null).slice(0, 3));
  add("detail_panel_stays_closed", samples.every((sample) => !sample.panel_open));
  const jumps = steps.slice(1).map((step, index) => step - steps[index]).filter((delta) => delta !== 0);
  add("advances_one_step_at_a_time", jumps.every((delta) => delta === 1), { jumps });
  const firstFinal = samples.findIndex((sample) => sample.step === last);
  add("reaches_final_step", firstFinal >= 0, { last, max: Math.max(...steps) });
  const afterFinal = firstFinal >= 0 ? samples.slice(firstFinal) : [];
  const stopped = afterFinal.find((sample) => !sample.playing);
  add("stops_at_final_step", firstFinal >= 0 && afterFinal.every((sample) => sample.step === last)
    && !!stopped && stopped.t - samples[firstFinal].t <= intervalMs + 500
    && samples.at(-1).t - samples[firstFinal].t >= 2 * intervalMs,
  { stopped_after_ms: stopped ? stopped.t - samples[firstFinal].t : null,
    observed_after_final_ms: firstFinal >= 0 ? samples.at(-1).t - samples[firstFinal].t : null });
  const construction = [];
  const measurement = [];
  for (let k = 1; k <= last; k += 1) {
    const kind = events.find((event) => event.step_index === k)?.semantic_kind;
    const now = settledAt(k);
    const before = settledAt(k - 1);
    if (!now || !before) continue;
    if (kind === "GEOMETRY_CONSTRUCTION") {
      construction.push({ step: k,
        changed: JSON.stringify(now.rendered) !== JSON.stringify(before.rendered) });
    }
    if (kind === "MEASUREMENT") {
      measurement.push({ step: k, added: now.readout.filter((row) => !before.readout.includes(row)) });
    }
  }
  add("construction_steps_change_geometry", construction.every((c) => c.changed), construction);
  add("measurement_steps_show_a_value", measurement.every((m) => m.added.length > 0), measurement);
  // Đáp số + mọi BÍ DANH của nó (`alias_of`) là MỘT kết luận ⇒ đúng MỘT dòng.
  // Không so giá trị: AB = AD = 4 ở hình lập phương là hai đại lượng thật.
  const finalRows = firstFinal >= 0 ? settledAt(last).readout : [];
  const ten = (o) => (o?.notation || o?.label || "").replace(/\s+/g, "");
  const answers = events.filter((event) => event.semantic_kind === "FINAL_RESULT" && event.object)
    .map((event) => event.object).filter((id, i, all) => all.indexOf(id) === i)
    .map((id) => {
      const names = new Set((objects ?? []).filter((o) => o.id === id || o.alias_of === id).map(ten));
      return { id, rows: finalRows.filter((row) => names.has(row.split("=")[0].replace(/\s+/g, ""))) };
    });
  add("final_result_shown_once", answers.length > 0 && answers.every((a) => a.rows.length === 1),
    { rows: finalRows, answers });
  if (replay) {
    add("replay_resets_step_selection_highlight",
      replay.step === 0 && replay.selected === null && replay.highlighted.length === 0, replay);
  }
  if (orbit) {
    add("orbit_preserves_timeline", orbit.before.step === orbit.after.step
      && JSON.stringify(orbit.before.readout) === JSON.stringify(orbit.after.readout), orbit);
  }
  return { pass: Object.values(checks).every((check) => check.pass), checks };
}
