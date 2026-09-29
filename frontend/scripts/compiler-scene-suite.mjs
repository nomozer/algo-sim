import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import {
  mkdirSync, readFileSync, statSync, writeFileSync,
} from "node:fs";
import { dirname, join, relative, resolve } from "node:path";

import { BrowserSession } from "./browser-runner.mjs";
import { kiemDistMoi, phucVu } from "./scene3d-orbit-gate.mjs";
import {
  assessCssReadiness,
  assessFormationSnapshots,
  assessImmutableWindow,
  compareClosures,
  detectRawTokenLeakage,
  evaluateEvidenceGates,
  eventDeclaredClosure,
  expectedVisibleIds,
  planOrbit,
  pollUntil,
  settleCamera,
  sha256File,
  sha256GitBlob,
  solidTopology,
  validateFormulaReferences,
  validateSuiteManifest,
} from "./compiler-scene-replay-lib.mjs";

const REPO_ROOT = resolve(import.meta.dirname, "..", "..");
const FRONTEND = join(REPO_ROOT, "frontend");
const DIST = join(FRONTEND, "dist");
const SUBMIT = '[aria-label="Phân tích đề bằng AI"]';

export const jsonEval = async (session, expression) => {
  const value = await session.eval(`JSON.stringify(${expression})`);
  if (typeof value !== "string") throw new Error(`EXPECTED_JSON:${String(value)}`);
  return JSON.parse(value);
};

const sha256 = (value) => createHash("sha256").update(value).digest("hex");

function assertion(pass, details = undefined) {
  return { pass: Boolean(pass), ...(details === undefined ? {} : { details }) };
}

const VISIBILITY_STATE = "visible_edge_ids:window.__geo3d_visible_edge_ids||[],"
  + "hidden_edge_ids:window.__geo3d_hidden_edge_ids||[],"
  + "mixed_edge_ids:window.__geo3d_mixed_edge_ids||[],"
  + "edge_spans:window.__geo3d_edge_spans||[],";
const EDGE_STATE = VISIBILITY_STATE
  + "duplicate_visual_owner_ids:window.__geo3d_duplicate_visual_owner_ids||[],"
  + "highlighted_render_owner_ids:window.__geo3d_highlighted_render_owner_ids||[],"
  + "selected_id:window.__geo3d_selected_id||null,"
  + "dash_signature:window.__geo3d_edge_dash_signature||{},";

/** Settle the camera; a camera that never settles is recorded as a failed
 *  `camera_settled_<state>` assertion (with diagnostic) instead of aborting. */
async function settleOrRecord(session, result, state) {
  try {
    const settled = await settleCamera(() => jsonEval(session,
      "({snapshot:window.__geo3d_camera_snapshot||null,"
      + "frame_count:(window.__geo3d_occlusion_performance||{}).frame_count||0})"));
    result.camera_settle = { ...result.camera_settle,
      [state]: { samples: settled.settle_samples, max_motion: settled.settle_max_motion } };
    return settled;
  } catch (error) {
    if (!String(error.message).startsWith("SETTLING_TIMEOUT")) throw error;
    result.assertions[`camera_settled_${state}`] = assertion(false, error.diagnostic);
    return null;
  }
}

async function setTextarea(session, text) {
  return session.eval(`(()=>{const t=document.querySelector('textarea');if(!t)return false;`
    + `const set=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;`
    + `set.call(t,${JSON.stringify(text)});t.dispatchEvent(new Event('input',{bubbles:true}));return true})()`);
}

async function rectFor(session, expression) {
  return jsonEval(session, `(()=>{const e=${expression};if(!e)return null;const r=e.getBoundingClientRect();`
    + `return{x:r.left,y:r.top,w:r.width,h:r.height}})()`);
}

export async function trustedClick(session, expression) {
  // Như người dùng: cuộn tới phần tử trước khi bấm. Không cuộn thì phần tử
  // nằm dưới khung nhìn (ô soi mobile, w10) nhận một cú bấm ở toạ độ ngoài màn hình.
  await session.eval(`(()=>{const e=${expression};if(e)e.scrollIntoView({block:"nearest"});return true})()`);
  const rect = await rectFor(session, expression);
  if (!rect || rect.w <= 0 || rect.h <= 0) return false;
  await session.mouse(rect.x + rect.w / 2, rect.y + rect.h / 2);
  return true;
}

async function clickAria(session, label) {
  return trustedClick(session,
    `document.querySelector('[aria-label=${JSON.stringify(label)}]')`);
}

async function clickText(session, text) {
  return trustedClick(session,
    `[...document.querySelectorAll('button')].find(e=>(e.textContent||'').includes(${JSON.stringify(text)}))`);
}

export async function currentStep(session) {
  const text = await session.eval(`document.querySelector('.geo3d-buoc-so')?.textContent||''`);
  const match = /Bước\s+(\d+)\/(\d+)/.exec(String(text));
  return match ? { index: Number(match[1]) - 1, count: Number(match[2]), text } : null;
}

async function moveStep(session, direction) {
  const before = await currentStep(session);
  const label = direction > 0 ? "Bước sau" : "Bước trước";
  const state = await jsonEval(session, `(()=>{const b=document.querySelector('[aria-label=${JSON.stringify(label)}]');`
    + `return b?{exists:true,disabled:b.disabled}:{exists:false,disabled:true}})()`);
  if (!state.exists || state.disabled) return false;
  if (!await clickAria(session, label)) return false;
  await pollUntil(() => currentStep(session),
    (next) => next && before && next.index === before.index + direction,
    { timeoutMs: 5_000 });
  return true;
}

async function goToEnd(session) {
  while (await moveStep(session, 1)) { /* semantic state transition */ }
  return currentStep(session);
}

async function goToStart(session) {
  while (await moveStep(session, -1)) { /* semantic state transition */ }
  return currentStep(session);
}

async function projectedLabels(session) {
  return jsonEval(session, `(()=>Object.fromEntries([...document.querySelectorAll('.geo3d-label[data-id]')].map(e=>{`
    + `const r=e.getBoundingClientRect();return[e.dataset.id,{x:Math.round(r.left+r.width/2),`
    + `y:Math.round(r.top+r.height/2),text:(e.textContent||'').trim()}]})))()`);
}

function projectionComparison(before, after) {
  const common = Object.keys(before).filter((id) => after[id]);
  const deltas = Object.fromEntries(common.map((id) => [id, Math.hypot(
    after[id].x - before[id].x, after[id].y - before[id].y,
  )]));
  const moved = common.filter((id) => deltas[id] >= 3);
  const distinctBefore = new Set(common.map((id) => `${before[id].x}:${before[id].y}`)).size;
  const distinctAfter = new Set(common.map((id) => `${after[id].x}:${after[id].y}`)).size;
  return {
    common_ids: common,
    deltas,
    moved_ids: moved,
    distinct_before: distinctBefore,
    distinct_after: distinctAfter,
    pass: common.length >= 3 && moved.length >= 2
      && distinctBefore === common.length && distinctAfter === common.length,
  };
}

export async function trustedOrbit(session, {
  dx = 190, dy = 48, startX = 0.52, startY = 0.48,
} = {}) {
  const rect = await rectFor(session, `document.querySelector('.geo3d-canvas canvas')`);
  if (!rect) throw new Error("NO_CANVAS_FOR_ORBIT");
  const x = rect.x + rect.w * startX;
  const y = rect.y + rect.h * startY;
  await session._send("Input.dispatchMouseEvent", {
    type: "mouseMoved", x, y, button: "left", buttons: 0,
  });
  await session._send("Input.dispatchMouseEvent", {
    type: "mousePressed", x, y, button: "left", buttons: 1, clickCount: 1,
  });
  for (let step = 1; step <= 16; step += 1) {
    await session._send("Input.dispatchMouseEvent", {
      type: "mouseMoved",
      x: x + (dx * step) / 16,
      y: y + (dy * step) / 16,
      button: "left", buttons: 1,
    });
  }
  await session._send("Input.dispatchMouseEvent", {
    type: "mouseReleased", x: x + dx, y: y + dy,
    button: "left", buttons: 0, clickCount: 1,
  });
}

export async function capture(session, path) {
  const absolute = resolve(path);
  mkdirSync(dirname(absolute), { recursive: true });
  const result = await session.screenshot(absolute);
  if (result !== "ok" || statSync(absolute).size < 4_096) {
    throw new Error(`INVALID_SCREENSHOT:${absolute}`);
  }
  return {
    path: relative(REPO_ROOT, absolute).replaceAll("\\", "/"),
    bytes: statSync(absolute).size,
    sha256: sha256File(absolute),
  };
}

async function canvasHash(session) {
  const rect = await rectFor(session, `document.querySelector('.geo3d-canvas canvas')`);
  if (!rect) throw new Error("NO_CANVAS_CLIP");
  const response = await session._send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
    clip: { x: rect.x, y: rect.y, width: rect.w, height: rect.h, scale: 1 },
  });
  const data = Buffer.from(response.result.data, "base64");
  return { sha256: sha256(data), bytes: data.length };
}

async function canvasFrame(session) {
  const rect = await rectFor(session, `document.querySelector('.geo3d-canvas canvas')`);
  if (!rect) throw new Error("NO_CANVAS_CLIP");
  const response = await session._send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
    clip: { x: rect.x, y: rect.y, width: rect.w, height: rect.h, scale: 1 },
  });
  const encoded = response.result.data;
  const data = Buffer.from(encoded, "base64");
  return { sha256: sha256(data), bytes: data.length, encoded };
}

async function pixelDelta(session, before, after) {
  return session.eval(`(async()=>{const load=src=>new Promise((ok,bad)=>{`
    + `const i=new Image();i.onload=()=>ok(i);i.onerror=bad;i.src=src});`
    + `const a=await load(${JSON.stringify(`data:image/png;base64,${before.encoded}`)});`
    + `const b=await load(${JSON.stringify(`data:image/png;base64,${after.encoded}`)});`
    + `if(a.width!==b.width||a.height!==b.height)return{pass:false,reason:'SIZE_MISMATCH'};`
    + `const c=document.createElement('canvas');c.width=a.width;c.height=a.height;const x=c.getContext('2d');`
    + `x.drawImage(a,0,0);const pa=x.getImageData(0,0,c.width,c.height).data;`
    + `x.clearRect(0,0,c.width,c.height);x.drawImage(b,0,0);const pb=x.getImageData(0,0,c.width,c.height).data;`
    + `let changed=0,minX=c.width,minY=c.height,maxX=-1,maxY=-1;for(let i=0;i<pa.length;i+=4){`
    + `const d=Math.abs(pa[i]-pb[i])+Math.abs(pa[i+1]-pb[i+1])+Math.abs(pa[i+2]-pb[i+2]);`
    + `if(d<24)continue;changed++;const p=i/4,xx=p%c.width,yy=Math.floor(p/c.width);`
    + `minX=Math.min(minX,xx);minY=Math.min(minY,yy);maxX=Math.max(maxX,xx);maxY=Math.max(maxY,yy)}`
    + `const total=c.width*c.height,ratio=changed/total;return{changed_pixels:changed,total_pixels:total,`
    + `changed_ratio:ratio,bounds:changed?{x:minX,y:minY,width:maxX-minX+1,height:maxY-minY+1}:null,`
    + `pass:changed>0&&ratio<0.75}})()`);
}

async function cssReadiness(session, viewport) {
  const measured = await jsonEval(session, `(()=>{const pick=s=>document.querySelector(s);const style=e=>{const s=getComputedStyle(e);`
    + `const r=e.getBoundingClientRect();return{display:s.display,position:s.position,fontFamily:s.fontFamily,`
    + `fontSize:s.fontSize,color:s.color,width:r.width,height:r.height,left:r.left,right:r.right}};`
    + `const baselineTag=(tag)=>{const e=document.createElement(tag);e.style.cssText='all:initial;position:static;';`
    + `e.textContent='sentinel';document.body.appendChild(e);const x=style(e);e.remove();return x};`
    + `const scene=pick('.geo3d'),box=pick('.geo3d-canvas'),canvas=pick('.geo3d-canvas canvas'),`
    + `controls=pick('.geo3d-controls'),controlButton=pick('.geo3d-controls button'),`
    + `controlText=pick('.geo3d-scrub-label'),`
    + `readout=pick('.geo3d-readout'),readoutText=pick('.geo3d-readout-ten');`
    + `const actual={scene:scene&&style(scene),box:box&&style(box),canvas:canvas&&style(canvas),`
    + `controls:controls&&style(controls),controlButton:controlButton&&style(controlButton),`
    + `controlText:controlText&&style(controlText),`
    + `readout:readout&&style(readout),readoutText:readoutText&&style(readoutText)};`
    + `const baseline={div:baselineTag('div'),button:baselineTag('button'),`
    + `ul:baselineTag('ul'),span:baselineTag('span')};`
    + `let sheets={count:document.styleSheets.length,readableRules:0,unreadable:0};`
    + `for(const sheet of document.styleSheets){try{sheets.readableRules+=(sheet.cssRules||[]).length}catch(e){sheets.unreadable++}}`
    + `return{actual,baseline,stylesheets_auxiliary:sheets,scrollWidth:document.documentElement.scrollWidth,`
    + `viewportWidth:window.innerWidth}})()`);
  const assessed = assessCssReadiness(
    measured.actual, measured.baseline, measured.scrollWidth, Number(viewport.width),
  );
  return { ...measured, ...assessed };
}

export async function openFixture({ port, viewport, fixture }) {
  const envelope = fixture.envelope;
  const session = new BrowserSession({
    viewport: viewport.width,
    height: viewport.height,
    webgl: true,
    url: `http://127.0.0.1:${port}`,
    napModuleDev: false,
  });
  await session.open();
  if (viewport.width < 600) {
    await session._send("Emulation.setDeviceMetricsOverride", {
      width: viewport.width, height: viewport.height, deviceScaleFactor: 2, mobile: true,
    });
  }
  let analyzeCalls = 0;
  const apiEvents = [];
  await session.interceptJson("*/api/*", async ({ url }) => {
    const pathname = new URL(url).pathname;
    if (pathname === "/api/analyze") {
      analyzeCalls += 1;
      apiEvents.push({ pathname, status: 200 });
      return { status: 200, body: envelope };
    }
    if (pathname === "/api/health") {
      apiEvents.push({ pathname, status: 200 });
      return { status: 200, body: { ok: true, hasKey: true, cachedProblems: 0 } };
    }
    if (pathname === "/api/auth/me") {
      apiEvents.push({ pathname, status: 200 });
      return { status: 200, body: { user: null } };
    }
    apiEvents.push({ pathname, status: 404 });
    return { status: 404, body: { error: "outside frozen replay" } };
  });
  session.consoleEvents = [];
  await session._send("Page.reload", {});
  await pollUntil(() => session.eval(`!!document.querySelector('textarea')`), Boolean);
  if (!await setTextarea(session, fixture.problem_text)) throw new Error("TEXTAREA_NOT_READY");
  await pollUntil(() => session.eval(`(()=>{const b=document.querySelector(${JSON.stringify(SUBMIT)});`
    + `return !!b&&!b.disabled})()`), Boolean);
  if (!await trustedClick(session, `document.querySelector(${JSON.stringify(SUBMIT)})`)) {
    throw new Error("SUBMIT_NOT_CLICKED");
  }
  return { session, analyzeCalls: () => analyzeCalls, apiEvents: () => [...apiEvents] };
}

async function observeTree(session, scene, expectedIds) {
  await clickText(session, "Thành phần");
  await pollUntil(() => session.eval(`!!document.querySelector('.geo3d-tree')`), Boolean,
    { timeoutMs: 5_000 });
  const rows = await jsonEval(session, `(()=>[...document.querySelectorAll('.geo3d-tree-item')].map(e=>({`
    + `text:(e.querySelector('.geo3d-tree-nhan')?.textContent||'').trim(),disabled:e.disabled})))()`);
  const expected = new Set(expectedIds);
  const checks = [];
  for (const object of scene.objects ?? []) {
    const matches = rows.filter((row) => row.text === object.label);
    const observedPresent = matches.some((row) => !row.disabled);
    checks.push({
      id: object.id,
      label: object.label,
      expected_present: expected.has(object.id),
      matches: matches.length,
      observed_present: matches.length > 0 ? observedPresent : null,
      pass: matches.length > 0 && observedPresent === expected.has(object.id),
    });
  }
  await clickAria(session, "Đóng");
  await pollUntil(() => session.eval(`!document.querySelector('.geo3d-tree')`), Boolean,
    { timeoutMs: 5_000 });
  return { objects: checks, pass: checks.every((item) => item.pass) };
}

async function formationEvidence(session, scene, outDir, captureMode = "full") {
  await goToStart(session);
  const steps = [];
  const observations = { forward: [], backward: [] };
  const stepTotal = scene.formation?.steps?.length ?? scene.events.length;
  for (let index = 0; index < stepTotal; index += 1) {
    const step = await currentStep(session);
    const expectedIds = expectedVisibleIds(scene, index);
    const tree = await observeTree(session, scene, expectedIds);
    const labels = await projectedLabels(session);
    const expectedPointIds = expectedIds.filter((id) =>
      scene.objects.some((object) => object.id === id && object.type === "point3"));
    const actualPointIds = Object.keys(labels).sort();
    const expectedReadoutObjects = scene.objects.filter((object) =>
      expectedIds.includes(object.id) && object.render === "readout");
    const readoutTexts = await jsonEval(session, `(()=>[...document.querySelectorAll('.geo3d-readout li')].map(e=>`
      + `(e.querySelector('.geo3d-readout-ten')?.textContent||'').trim()))()`);
    const expectedReadoutIds = expectedReadoutObjects.map((object) => object.id).sort();
    const actualReadoutIds = expectedReadoutObjects.filter((object) =>
      readoutTexts.includes(object.notation || object.label)).map((object) => object.id).sort();
    const representative = Math.floor((stepTotal - 1) / 2);
    const shouldCapture = captureMode === "full" || index === representative;
    const image = shouldCapture
      ? await capture(session, join(outDir,
          index === representative ? "formation_current_step.png" : `formation_step_${index}.png`))
      : null;
    const canvas = await canvasHash(session);
    const learnerText = await session.eval(
      `document.querySelector('.geo3d-buoc-loi')?.textContent||''`,
    );
    const observedVisibleIds = tree.objects
      .filter((item) => item.observed_present === true).map((item) => item.id).sort();
    observations.forward.push({
      index, direction: "forward", visible_ids: observedVisibleIds,
    });
    steps.push({
      index,
      indicator: step,
      expected_visible_ids: expectedIds,
      tree,
      expected_point_ids: expectedPointIds.sort(),
      observed_point_ids: actualPointIds,
      point_visibility_pass: JSON.stringify(expectedPointIds.sort()) === JSON.stringify(actualPointIds),
      expected_readout_ids: expectedReadoutIds,
      observed_readout_ids: actualReadoutIds,
      readout_visibility_pass: JSON.stringify(expectedReadoutIds) === JSON.stringify(actualReadoutIds),
      screenshot: image,
      canvas,
      learner_text: learnerText,
    });
    if (index < stepTotal - 1 && !await moveStep(session, 1)) {
      throw new Error(`FORMATION_STOPPED_AT:${index}`);
    }
  }
  for (let index = stepTotal - 1; index >= 0; index -= 1) {
    const expectedIds = expectedVisibleIds(scene, index);
    const tree = await observeTree(session, scene, expectedIds);
    observations.backward.push({
      index,
      direction: "backward",
      visible_ids: tree.objects
        .filter((item) => item.observed_present === true).map((item) => item.id).sort(),
    });
    if (index > 0 && !await moveStep(session, -1)) {
      throw new Error(`FORMATION_BACKWARD_STOPPED_AT:${index}`);
    }
  }
  const trace = assessFormationSnapshots(scene, observations);
  const canvasHashes = new Set(steps.map((step) => step.canvas.sha256));
  const pass = steps.every((step) => step.indicator?.index === step.index
    && step.indicator?.count === stepTotal
    && step.tree.pass && step.point_visibility_pass && step.readout_visibility_pass)
    && canvasHashes.size >= 2 && trace.pass;
  return { steps, observations, trace, distinct_canvas_frames: canvasHashes.size, pass };
}

async function runPositive({ port, viewport, fixture, scenario, outDir }) {
  const scene = fixture.envelope.scene3d;
  const { session, analyzeCalls, apiEvents } = await openFixture({ port, viewport, fixture });
  const result = { viewport, assertions: {}, screenshots: {}, capture_order: [] };
  try {
    await pollUntil(() => session.eval(`!!document.querySelector('.geo3d-canvas canvas')`), Boolean);
    await goToEnd(session);
    await pollUntil(() => session.eval(`document.querySelector('.geo3d-readout')?.textContent||''`),
      (text) => String(text).includes(scenario.expected_answer));

    const topology = solidTopology(scene);
    result.topology = topology;
    result.assertions.topology = assertion(
      Object.entries(scenario.topology).every(([key, value]) => topology[key] === value),
      { expected: scenario.topology, actual: topology },
    );
    if (scenario.section_vertices) {
      const section = scene.objects.find((object) => object.type === "section");
      result.assertions.section_vertices = assertion(
        section?.polygon?.length === scenario.section_vertices,
        { expected: scenario.section_vertices, actual: section?.polygon?.length ?? null },
      );
    }

    const labels = await projectedLabels(session);
    result.labels = labels;
    result.assertions.labels = assertion(
      scenario.expected_labels.every((label) =>
        Object.values(labels).some((point) => point.text === label)),
      { expected: scenario.expected_labels, actual: Object.values(labels).map((point) => point.text) },
    );
    const css = await cssReadiness(session, viewport);
    result.css_readiness = css;
    result.assertions.css_readiness = assertion(css.pass, css.checks);
    result.canvas_box = await rectFor(session, `document.querySelector('.geo3d-canvas canvas')`);

    await pollUntil(
      () => jsonEval(session, `({${EDGE_STATE}})`),
      (edge) => edge.visible_edge_ids.length > 0 && edge.hidden_edge_ids.length > 0,
      { timeoutMs: 8_000 },
    );
    // Auto-fit + damping keep moving the camera after the edge sets first
    // appear; snapshot and sets are read together only once it has settled.
    const neutralSettled = await settleOrRecord(session, result, "neutral_final");
    const { camera: neutralCamera, ...edgeDefault } = await jsonEval(session,
      `({${EDGE_STATE}camera:window.__geo3d_camera_snapshot||null})`);
    result.edge_semantics_neutral_final = edgeDefault;
    result.camera_snapshots = {
      neutral_final: { snapshot: neutralCamera, sha256: sha256(JSON.stringify(neutralCamera)) },
    };
    result.scene3d_envelope_sha256 = sha256(JSON.stringify(scene));
    result.assertions.neutral_has_no_emphasis = assertion(
      edgeDefault.selected_id === null && edgeDefault.highlighted_render_owner_ids.length === 0,
      edgeDefault,
    );
    const visibleText = await session.eval(`document.body.innerText||''`);
    result.raw_token_leakage = detectRawTokenLeakage(scene, visibleText);
    result.formula_entity_coherence = validateFormulaReferences(scene);

    // Default phải được chụp trước causal/orbit/formation.
    result.screenshots.neutral_final = await capture(session, join(outDir, "neutral_final.png"));
    result.capture_order.push("neutral_final");
    // The window opens only after settling (the capture above may itself
    // have scheduled frames), so settle again right before resetting.
    const windowSettled = neutralSettled
      && await settleOrRecord(session, result, "immutable_window");
    // The published counters only refresh on the next rendered frame: zero them
    // in the same task as the reset, or the poll reads the pre-reset window
    // (seen in w09: frame_count 138 >= 120 before any window frame ran).
    await session.eval(`(()=>{window.__geo3d_reset_occlusion_performance?.();`
      + `window.__geo3d_occlusion_performance={frame_count:0,recompute_count:0}})()`);
    const { perf: immutable, camera: windowEnd } = await pollUntil(
      () => jsonEval(session, `({perf:window.__geo3d_occlusion_performance||{frame_count:0},`
        + `camera:window.__geo3d_camera_snapshot||null})`),
      (value) => value.perf.frame_count >= 120,
      { timeoutMs: 8_000, intervalMs: 20 },
    );
    const timings = [...(immutable.recomputation_times_ms ?? [])].sort((a, b) => a - b);
    const percentile = (p) => timings.length
      ? timings[Math.min(timings.length - 1, Math.floor((timings.length - 1) * p))] : 0;
    result.occlusion_performance = {
      ...immutable,
      median_recomputation_ms: percentile(0.5),
      p95_recomputation_ms: percentile(0.95),
      max_recomputation_ms: timings.at(-1) ?? 0,
      immutable_frame_recomputations: immutable.recompute_count,
    };
    const windowVerdict = assessImmutableWindow({
      settled: windowSettled || null, end: windowEnd, perf: immutable,
    });
    result.occlusion_performance.immutable_window = windowVerdict;
    result.assertions.immutable_120_frames = assertion(windowVerdict.pass, result.occlusion_performance);
    const causalBeforeFrame = await canvasFrame(session);
    const causalBeforeState = await jsonEval(session, `({selected_id:window.__geo3d_selected_id||null,`
      + `highlighted_ids:window.__geo3d_highlighted_ids||[],`
      + `highlighted_render_owner_ids:window.__geo3d_highlighted_render_owner_ids||[]})`);

    const target = scene.objects.find((object) => object.id === scenario.causal_target_id);
    const targetText = target?.notation || target?.label;
    if (!targetText) throw new Error(`MISSING_CAUSAL_TARGET:${scenario.causal_target_id}`);
    const clicked = await trustedClick(session,
      `[...document.querySelectorAll('.geo3d-readout li')].find(e=>(e.querySelector('.geo3d-readout-ten')?.textContent||'').trim()===${JSON.stringify(targetText)})`);
    if (!clicked) throw new Error(`CAUSAL_TARGET_NOT_CLICKABLE:${targetText}`);
    await pollUntil(() => session.eval(`window.__geo3d_selected_id||null`),
      (id) => id === scenario.causal_target_id, { timeoutMs: 5_000 });
    const causalState = await pollUntil(
      () => jsonEval(session, `({selected_id:window.__geo3d_selected_id||null,`
        + `highlighted_ids:window.__geo3d_highlighted_ids||[],`
        + `highlighted_render_owner_ids:window.__geo3d_highlighted_render_owner_ids||[],`
        + `dash_signature:window.__geo3d_edge_dash_signature||{}})`),
      (state) => state.selected_id === scenario.causal_target_id
        && state.highlighted_render_owner_ids.length > 0,
      { timeoutMs: 8_000 },
    );
    const declared = eventDeclaredClosure(scene.events, scenario.causal_target_id);
    const causal = compareClosures(
      scenario.oracle_expected_closure, declared, causalState.highlighted_ids,
    );
    causal.selected_id = causalState.selected_id;
    const causalAfterFrame = await canvasFrame(session);
    const delta = causalBeforeFrame.sha256 === causalAfterFrame.sha256
      ? { changed_pixels: 0, changed_ratio: 0, bounds: null, pass: false }
      : await pixelDelta(session, causalBeforeFrame, causalAfterFrame);
    causal.visual = {
      selected_changed: causalBeforeState.selected_id !== causalState.selected_id,
      closure_changed: JSON.stringify(causalBeforeState.highlighted_ids)
        !== JSON.stringify(causalState.highlighted_ids),
      render_owners_changed: JSON.stringify(causalBeforeState.highlighted_render_owner_ids)
        !== JSON.stringify(causalState.highlighted_render_owner_ids),
      canvas_changed: causalBeforeFrame.sha256 !== causalAfterFrame.sha256,
      pixel_delta: delta,
      dash_signature_preserved:
        JSON.stringify(edgeDefault.dash_signature) === JSON.stringify(causalState.dash_signature),
    };
    causal.pass = causal.pass && causalState.selected_id === scenario.causal_target_id
      && causal.visual.selected_changed && causal.visual.closure_changed
      && causal.visual.render_owners_changed && causal.visual.canvas_changed && delta.pass
      && causal.visual.dash_signature_preserved;
    result.causal_closure = causal;
    result.assertions.causal_closure = assertion(causal.pass, causal);
    result.screenshots.causal_selected = await capture(session, join(outDir, "causal_selected.png"));
    result.capture_order.push("causal_selected");

    await clickText(session, "Xem lại toàn hình");
    await pollUntil(() => session.eval(`window.__geo3d_selected_id||null`),
      (id) => id === null, { timeoutMs: 5_000 });
    const resetEmphasis = await jsonEval(session,
      `({selected_id:window.__geo3d_selected_id||null,highlighted_ids:window.__geo3d_highlighted_ids||[],`
      + `highlighted_render_owner_ids:window.__geo3d_highlighted_render_owner_ids||[]})`);
    result.assertions.emphasis_reset_before_rotation = assertion(
      resetEmphasis.selected_id === null && resetEmphasis.highlighted_render_owner_ids.length === 0,
      resetEmphasis,
    );
    await goToEnd(session);
    if (viewport.orbit) {
      const before = await projectedLabels(session);
      const hiddenBefore = await jsonEval(session,
        `({visible_edge_ids:window.__geo3d_visible_edge_ids||[],`
        + `hidden_edge_ids:window.__geo3d_hidden_edge_ids||[],`
        + `mixed_edge_ids:window.__geo3d_mixed_edge_ids||[],edge_spans:window.__geo3d_edge_spans||[]})`);
      // w10: cử chỉ HOẠCH ĐỊNH trước (`planOrbit`: đạt ngưỡng góc nhìn + đổi
      // tập khuất dự đoán) đi đầu; ba cú kéo cố định cũ chỉ còn là dự phòng.
      // OrbitControls: Δφ = 2π·dx / chiều cao khung, kéo phải làm phương vị GIẢM.
      const cam0 = await jsonEval(session, "window.__geo3d_camera_snapshot||null");
      const m0 = cam0?.view_matrix_column_major;
      const plan = m0 ? planOrbit(scene, [m0[2], m0[6], m0[10]]) : null;
      const cao = await session.eval("document.querySelector('.geo3d-canvas canvas').clientHeight");
      const gestures = [
        ...(plan ? [{ dx: Math.round((-plan.offset_deg / 360) * cao), dy: 0, startX: 0.52, startY: 0.48,
          planned: true }] : []),
        { dx: 190, dy: 48, startX: 0.52, startY: 0.48 },
        { dx: -170, dy: 84, startX: 0.67, startY: 0.42 },
        { dx: 120, dy: -110, startX: 0.43, startY: 0.63 },
      ];
      let observedOrbit = null;
      const attempts = [];
      const t0 = Date.now();
      for (const gesture of gestures) {
        const started_ms = Date.now() - t0;
        await trustedOrbit(session, gesture);
        try {
          observedOrbit = await pollUntil(async () => ({
            points: await projectedLabels(session),
            sets: await jsonEval(session,
              `({visible_edge_ids:window.__geo3d_visible_edge_ids||[],`
              + `hidden_edge_ids:window.__geo3d_hidden_edge_ids||[],`
              + `mixed_edge_ids:window.__geo3d_mixed_edge_ids||[],`
              + `edge_spans:window.__geo3d_edge_spans||[]})`),
          }), (observed) => projectionComparison(before, observed.points).moved_ids.length >= 2
            && JSON.stringify(observed.sets) !== JSON.stringify(hiddenBefore),
          { timeoutMs: 4_000 });
          attempts.push({ gesture, started_ms, ended_ms: Date.now() - t0, pass: true,
            state: "GESTURE_SENT→MOTION_AND_VISIBILITY_CHANGE" });
          break;
        } catch (error) {
          attempts.push({ gesture, started_ms, ended_ms: Date.now() - t0, pass: false,
            state: "GESTURE_SENT→TIMEOUT", reason: String(error) });
        }
      }
      if (!observedOrbit) throw new Error(`ORBIT_EVIDENCE_TIMEOUT:${JSON.stringify({ plan, attempts })}`);
      const after = observedOrbit.points;
      // Damping is still carrying the orbit here: settle, then read the sets
      // and the camera in ONE evaluation so the oracle sees the same camera.
      await settleOrRecord(session, result, "rotated_neutral");
      const { camera: rotatedCamera, ...hiddenAfter } = await jsonEval(session,
        `({${VISIBILITY_STATE}camera:window.__geo3d_camera_snapshot||null})`);
      result.camera_snapshots.rotated_neutral = {
        snapshot: rotatedCamera,
        sha256: sha256(JSON.stringify(rotatedCamera)),
      };
      const orbit = projectionComparison(before, after);
      orbit.plan = plan;
      orbit.attempts = attempts;
      orbit.visibility_before = hiddenBefore;
      orbit.visibility_after = hiddenAfter;
      // Chữ ký nét đứt + owner của trạng thái xoay (cho crop có metadata) —
      // đọc RIÊNG: gộp vào `hiddenAfter` thì phép so tập khuất bên dưới luôn đúng.
      result.edge_semantics_rotated_neutral = { ...hiddenAfter, ...await jsonEval(session,
        "({dash_signature:window.__geo3d_edge_dash_signature||{},"
        + "duplicate_visual_owner_ids:window.__geo3d_duplicate_visual_owner_ids||[]})") };
      orbit.visibility_recomputed = JSON.stringify(hiddenBefore) !== JSON.stringify(hiddenAfter);
      orbit.pass = orbit.pass && orbit.visibility_recomputed;
      result.orbit = orbit;
      result.assertions.orbit = assertion(orbit.pass, orbit);
      result.screenshots.rotated_neutral = await capture(session, join(outDir, "rotated_neutral.png"));
      await clickText(session, "Xem lại toàn hình");
    }

    if (viewport.formation) {
      await clickText(session, "Xem lại toàn hình");
      result.formation = await formationEvidence(
        session, scene, join(outDir, "formation"),
        viewport.formation === "representative" ? "representative" : "full",
      );
      result.assertions.formation = assertion(result.formation.pass, {
        steps: result.formation.steps.length,
        distinct_canvas_frames: result.formation.distinct_canvas_frames,
      });
    }

    const apiCalls = analyzeCalls();
    result.assertions.single_analyze_call = assertion(apiCalls === 1, apiCalls);
    const uncaught = session.consoleEvents.filter((event) => event.loai === "exception");
    const seriousConsole = session.consoleEvents.filter((event) =>
      event.loai !== "exception" &&
      !/favicon|DevTools|Download the React/i.test(event.text));
    const failedApiCalls = apiEvents().filter((event) => event.status >= 400);
    result.uncaught_exceptions = uncaught;
    result.failed_api_calls = failedApiCalls;
    result.console_events = seriousConsole;
    result.assertions.no_uncaught_exception = assertion(uncaught.length === 0, uncaught);
    result.assertions.no_failed_api_call = assertion(failedApiCalls.length === 0, failedApiCalls);
    result.assertions.no_serious_console_error = assertion(seriousConsole.length === 0, seriousConsole);
    result.evidence_gates = evaluateEvidenceGates({
      edge: edgeDefault,
      orbit_required: Boolean(viewport.orbit),
      orbit_visibility_changed: viewport.orbit ? result.orbit?.visibility_recomputed : true,
      causal: {
        selected_changed: causal.visual.selected_changed,
        closure_changed: causal.visual.closure_changed,
        render_owners_changed: causal.visual.render_owners_changed,
        canvas_changed: causal.visual.canvas_changed,
        bounded_pixel_delta: causal.visual.pixel_delta.pass,
        dash_signature_preserved: causal.visual.dash_signature_preserved,
      },
      capture_order: result.capture_order,
      formation_required: Boolean(viewport.formation),
      formation: viewport.formation
        ? result.formation.trace
        : { pass: true, future_object_leakage: [] },
      raw_token_leakage: result.raw_token_leakage,
      formula: result.formula_entity_coherence,
      causal_oracle_source: "independent_manifest",
      screenshot: { blank: false, premature: !css.pass },
      uncaught_exceptions: uncaught,
      failed_api_calls: failedApiCalls,
    });
    result.assertions.evidence_gates = assertion(
      result.evidence_gates.pass, result.evidence_gates.reason_codes,
    );
    result.pass = Object.values(result.assertions).every((item) => item.pass);
    return result;
  } finally {
    await session.close();
  }
}

async function runNegative({ port, viewport, fixture, scenario, outDir }) {
  const { session, analyzeCalls, apiEvents } = await openFixture({ port, viewport, fixture });
  try {
    await pollUntil(() => session.eval(`!!document.querySelector('.refusal-facts')`), Boolean);
    const observed = await jsonEval(session, `(()=>{const s=window.__ALGO_SIM_STORE__?.getState?.();`
      + `return{unsupported:s?.unsupported||null,canvas:!!document.querySelector('.geo3d-canvas canvas'),`
      + `active:!!s?.active,body:document.body.innerText,scrollWidth:document.documentElement.scrollWidth,`
      + `viewportWidth:window.innerWidth}})()`);
    const expected = scenario.negative_expected;
    const structuredPass = observed.unsupported?.error_code === expected.product_error_code
      && observed.unsupported?.stage_reached === expected.stage_reached;
    const learnerPass = Boolean(fixture.envelope.learner_reason)
      && observed.body.includes(fixture.envelope.learner_reason)
      && !observed.body.includes(fixture.envelope.reason);
    const kernelPass = scenario.id !== "cross_section"
      || (fixture.contract_gate?.kernel_error_code === expected.kernel_error_code
        && fixture.envelope.reason.includes(expected.kernel_error_code));
    const screenshot = await capture(session, join(outDir, "refusal.png"));
    const rawTokenLeakage = detectRawTokenLeakage(fixture.envelope.scene3d, observed.body);
    const uncaught = session.consoleEvents.filter((event) => event.loai === "exception");
    const seriousConsole = session.consoleEvents.filter((event) =>
      event.loai !== "exception" &&
      !/favicon|DevTools|Download the React/i.test(event.text));
    const failedApiCalls = apiEvents().filter((event) => event.status >= 400);
    const assertions = {
      structured_refusal: assertion(structuredPass, {
        expected: { error_code: expected.product_error_code, stage_reached: expected.stage_reached },
        actual: observed.unsupported,
      }),
      learner_message: assertion(learnerPass),
      canvas_absent: assertion(!observed.canvas),
      answer_absent: assertion(!observed.active),
      no_document_overflow: assertion(observed.scrollWidth <= observed.viewportWidth + 1, {
        scroll_width: observed.scrollWidth,
        viewport_width: observed.viewportWidth,
      }),
      no_raw_token_leakage: assertion(rawTokenLeakage.pass, rawTokenLeakage),
      contract_gate: assertion(kernelPass, fixture.contract_gate ?? null),
      single_analyze_call: assertion(analyzeCalls() === 1, analyzeCalls()),
      no_uncaught_exception: assertion(uncaught.length === 0, uncaught),
      no_failed_api_call: assertion(failedApiCalls.length === 0, failedApiCalls),
      no_serious_console_error: assertion(seriousConsole.length === 0, seriousConsole),
    };
    return {
      viewport, assertions, observed: { ...observed, body: undefined }, screenshot,
      raw_token_leakage: rawTokenLeakage,
      uncaught_exceptions: uncaught,
      failed_api_calls: failedApiCalls,
      console_events: seriousConsole,
      pass: Object.values(assertions).every((item) => item.pass),
    };
  } finally {
    await session.close();
  }
}

function verifyContractGate(suite) {
  const gate = suite.section_contract_gate;
  if (gate?.semantics !== "requested_non_empty_section_must_fail_closed"
      || gate?.kernel_error_code !== "PLANE_DOES_NOT_CUT") {
    throw new Error("SECTION_CONTRACT_DRIFT");
  }
  for (const source of gate.sources ?? []) {
    if (source.hash_basis !== "git_blob_at_measurement_commit"
        || sha256GitBlob(REPO_ROOT, source.path) !== source.sha256) {
      throw new Error(`SECTION_CONTRACT_DRIFT:${source.path}`);
    }
  }
  return gate;
}

export async function runSuite({
  suitePath, fixtureRoot, outDir, screenshotDir = undefined, skipBuild = false,
}) {
  const suiteAbsolute = resolve(suitePath);
  const suite = JSON.parse(readFileSync(suiteAbsolute, "utf-8"));
  validateSuiteManifest(suite, REPO_ROOT);
  const contractGate = verifyContractGate(suite);
  const candidate = JSON.parse(readFileSync(join(REPO_ROOT, "docs", "evaluation",
    "semantic-benchmark", "EVALUATION_CANDIDATE.json"), "utf-8"));
  if ((candidate.product_commit_sha ?? candidate.commit) !== suite.product_commit_sha
      || candidate.measured_system?.tree_hash !== suite.product_tree_sha) {
    throw new Error("PRODUCT_PROVENANCE_MISMATCH");
  }
  const measurementCommitSha = execFileSync("git", ["rev-parse", "HEAD"], {
    cwd: REPO_ROOT, encoding: "utf-8",
  }).trim();
  if (!skipBuild) {
    execFileSync("npm", ["run", "build"], {
      cwd: FRONTEND, stdio: "inherit", shell: true, timeout: 600_000,
    });
    kiemDistMoi();
  }
  const output = resolve(outDir);
  const screenshots = resolve(screenshotDir ?? join(output, "screenshots"));
  mkdirSync(output, { recursive: true });
  mkdirSync(screenshots, { recursive: true });
  const root = resolve(fixtureRoot);
  const { sv, cong } = await phucVu(DIST);
  const report = {
    schema_version: "generic-tier-a-browser-evidence/1",
    task_id: suite.task_id,
    measured_at: new Date().toISOString(),
    measurement_commit_sha: measurementCommitSha,
    product_commit_sha: suite.product_commit_sha,
    product_tree_sha: suite.product_tree_sha,
    suite_manifest: relative(REPO_ROOT, suiteAbsolute).replaceAll("\\", "/"),
    suite_manifest_sha256: sha256File(suiteAbsolute),
    fixture_manifest_sha256: sha256File(join(root, "FIXTURE_MANIFEST.json")),
    section_contract_gate: contractGate,
    application_llm_calls: 0,
    scenarios: {},
  };
  try {
    for (const scenario of suite.scenarios) {
      const positive = JSON.parse(readFileSync(join(root, scenario.positive_fixture), "utf-8"));
      const negative = JSON.parse(readFileSync(join(root, scenario.negative_fixture), "utf-8"));
      const scenarioOut = join(screenshots, scenario.id);
      const record = { positive: {}, negative: {} };
      for (const viewport of suite.viewports) {
        record.positive[viewport.id] = await runPositive({
          port: cong,
          viewport,
          fixture: positive,
          scenario,
          outDir: join(scenarioOut, viewport.id),
        });
      }
      for (const viewport of suite.viewports) {
        record.negative[viewport.id] = await runNegative({
          port: cong,
          viewport,
          fixture: negative,
          scenario,
          outDir: join(scenarioOut, "negative", viewport.id),
        });
      }
      record.pass = Object.values(record.positive).every((item) => item.pass)
        && Object.values(record.negative).every((item) => item.pass);
      report.scenarios[scenario.id] = record;
      console.log(`${scenario.id}: ${record.pass ? "PASS" : "FAIL"}`);
    }
  } finally {
    sv.close();
  }
  report.pass = Object.values(report.scenarios).every((scenario) => scenario.pass);
  const reportPath = join(output, "BROWSER_EVIDENCE.json");
  writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf-8");
  console.log(`Wrote ${reportPath}: ${report.pass ? "PASS" : "FAIL"}`);
  return report;
}
