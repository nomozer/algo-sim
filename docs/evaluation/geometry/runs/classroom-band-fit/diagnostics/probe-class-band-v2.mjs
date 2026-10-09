// Classroom band probe v2 (run classroom-band-fit). 0 model calls, API stubbed via CDP Fetch.
// Extends final-acceptance/diagnostics/probe-class-band.mjs with stricter checks registered BEFORE the fix:
// title visible, class status visible, step buttons work by trusted click, panel round trip keeps step/selection/camera
// and class status, canvas >= 320 px and not covered at its centre.
// usage: node probe-class-band-v2.mjs <repo> <dist> <out.json> [--fixture f.json] [--only role:vp,..] [--shots dir [--shot-cases role:vp,..]]
//        [--css file] [--collapse-dock]   (last two: prototype CSS injection / existing collapse click — not used for evidence)
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const argv = process.argv.slice(2);
const [REPO, DIST, OUT] = argv;
const opt = (n) => (argv.includes(n) ? argv[argv.indexOf(n) + 1] : null);
const CSS = opt("--css") ? readFileSync(opt("--css"), "utf8") : null;
const COLLAPSE_DOCK = argv.includes("--collapse-dock");
const SHOTS = opt("--shots");
// Screenshot only these role:viewport cases (representative after-images chosen before the run); absent = every case.
const SHOT_CASES = opt("--shot-cases")?.split(",") ?? null;
const imp = (p) => import(pathToFileURL(join(REPO, "frontend/scripts", p)).href);
const { BrowserSession, sleep } = await imp("browser-runner.mjs");
const { phucVu } = await imp("scene3d-orbit-gate.mjs");
const { trustedClick } = await imp("compiler-scene-suite.mjs");
const { pollUntil } = await imp("compiler-scene-replay-lib.mjs");

const fixture = JSON.parse(readFileSync(opt("--fixture") ?? join(REPO,
  "docs/evaluation/geometry/runs/phone-landscape-layout/inputs/fixtures/regular_square_pyramid_positive.json"), "utf8"));
const VIEWPORTS = {
  landscape_640: { width: 640, height: 360 },
  landscape_small: { width: 667, height: 375 },
  landscape: { width: 844, height: 390 },
  landscape_browser: { width: 844, height: 340 },
  portrait_small: { width: 360, height: 640 },
  portrait: { width: 390, height: 844 },
  low: { width: 1366, height: 650, desktop: true },
  desktop: { width: 1440, height: 900, desktop: true },
};
const SESSION = { sessionId: 1, roundId: "r1", cmdId: 1, syncCmdId: 0, mode: "follow", assignmentId: 7,
  simulationId: null, currentStep: 0, selectedId: null, isolatedIds: [], explodedGroups: [], updatedAt: null };
const ASSIGNMENT = { id: 7, classroomId: 3, title: "Chóp tứ giác đều — tính thể tích và góc giữa cạnh bên với đáy",
  instruction: "Làm theo từng bước", simulationId: fixture.envelope.simulation_id, closed: false,
  createdAt: "2026-10-09T00:00:00Z", myPractice: null };
const ROLES = {
  teacher_idle: { role: "teacher", session: null },
  teacher_live: { role: "teacher", session: SESSION },
  student_live: { role: "student", session: SESSION },
};
const TITLE_MIN_PX = 64;

function stub(role, session) {
  return async ({ url, request }) => {
    const p = new URL(url).pathname;
    const user = { id: 1, email: "x@algosim.test", displayName: "Nguyễn Văn A", role, mustChangePassword: false };
    if (p === "/api/health") return { body: { ok: true, hasKey: true, cachedProblems: 0 } };
    if (p === "/api/auth/me") return { body: { user, entitlement: { canRunSimulation: true,
      canPersistHistory: true, canJoinClass: true } } };
    if (p === "/api/classes") return { body: { classes: [{ id: 3, name: "11A2 — Toán chuyên", code: "ABC123" }] } };
    if (p === "/api/assignments") return { body: { assignments: [ASSIGNMENT] } };
    if (p === "/api/assignments/7") return { body: { ...ASSIGNMENT, envelope: fixture.envelope } };
    if (p === "/api/classes/3/session") return { body: { session } };
    if (p === "/api/classes/3/monitor") return { body: { rows: [
      { studentId: 2, helpRequested: true }, { studentId: 3, helpRequested: false }], serverNow: null, session } };
    if (request.method !== "GET") return { body: { ok: true, session } };
    return { status: 404, body: { error: "stub" } };
  };
}

const j = async (s, e) => JSON.parse(await s.eval(`JSON.stringify(${e})`));
// Class status in view: student indicator, teacher dock (open or collapsed), or the chip's read-only summary.
const STATUS_SEL = ".live-chi-bao,.live-dock,.live-dock-thu,.live-tom-tat";
const MEASURE = `(()=>{
  const W=innerWidth,H=innerHeight,de=document.documentElement;
  const box=(e)=>{const r=e.getBoundingClientRect();return {x:Math.round(r.left),y:Math.round(r.top),r:Math.round(r.right),b:Math.round(r.bottom),w:Math.round(r.width)}};
  const inside=(r)=>r.width>0&&r.left>=-0.5&&r.right<=W+0.5&&r.top>=-0.5&&r.bottom<=H+0.5;
  const row=document.querySelector('.geo3d-thanh');
  const kids=[...row.children].map(e=>({cls:e.className.split(' ')[0]||e.tagName,text:(e.textContent||'').trim().slice(0,40),...box(e),
    clipped:e.scrollWidth>e.clientWidth+1}));
  // Only rendered buttons are touch targets here; buttons inside a closed class dropdown are checked by the chip step.
  const btns=[...row.querySelectorAll('button')].filter(b=>b.getClientRects().length>0).map(b=>{const r=b.getBoundingClientRect();
    const hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);
    return {text:(b.textContent||'').trim().slice(0,30),inside:inside(r),tappable:!!hit&&(hit===b||b.contains(hit)),w:Math.round(r.width),h:Math.round(r.height)}});
  const t=document.querySelector('.geo3d-ten-bai').getBoundingClientRect();
  // Visible part = box ∩ viewport ∩ every clipping ancestor (the chip cuts its status with an ellipsis).
  const vis=(e)=>{const r=e.getBoundingClientRect();let L=Math.max(0,r.left),R=Math.min(W,r.right),T=Math.max(0,r.top),B=Math.min(H,r.bottom);
    for(let p=e.parentElement;p;p=p.parentElement){const cs=getComputedStyle(p);if(cs.overflowX!=='visible'||cs.overflowY!=='visible'){const q=p.getBoundingClientRect();
      L=Math.max(L,q.left);R=Math.min(R,q.right);T=Math.max(T,q.top);B=Math.min(B,q.bottom);}}
    return {w:Math.max(0,R-L),h:Math.max(0,B-T),full:R-L>=r.width-0.5&&B-T>=r.height-0.5}};
  const sts=[...document.querySelectorAll(${JSON.stringify(STATUS_SEL)})].filter(e=>e.getClientRects().length>0).map(e=>{const v=vis(e);
    const d=e.querySelector('.live-cham');const dv=d?vis(d):null;
    return {cls:e.className.split(' ')[0],visible_w:Math.round(v.w),full:v.full,dot_visible:!!dv&&dv.full,
      ok:(v.full&&v.w>0)||(!!dv&&dv.full)}});
  const st=sts.find(x=>x.ok)||null;
  const ctl=document.querySelector('.geo3d-controls');const c=ctl?ctl.getBoundingClientRect():null;
  const ctlItems=ctl?[...ctl.querySelectorAll('button'),ctl.querySelector('input[type=range]')].filter(Boolean):[];
  const cvEl=document.querySelector('.geo3d-canvas');const cv=cvEl.getBoundingClientRect();
  const hc=document.elementFromPoint(cv.left+cv.width/2,Math.min(cv.top+cv.height/2,H-1));
  return {viewport:{w:W,h:H},scroll_width:de.scrollWidth,client_width:de.clientWidth,
    top_row:box(row),children:kids,buttons:btns,
    title:{w:Math.round(t.width),inside:inside(t)},
    class_status:st?{...st,inside:true}:null,class_status_candidates:sts,
    canvas:{y:Math.round(cv.top),h:Math.round(cv.height),centre_free:!!hc&&cvEl.contains(hc)},
    controls_bottom:c?Math.round(c.bottom):null,
    controls_inside:ctlItems.length>0&&ctlItems.every(e=>inside(e.getBoundingClientRect()))};
})()`;
const stepText = (s) => j(s, "(document.querySelector('.geo3d-controls .geo3d-buoc-so')?.textContent||'').trim()");
const state = async (s) => ({ step: await stepText(s), selected: await j(s, "window.__geo3d_selected_id||null"),
  camera: await j(s, "(window.__geo3d_camera_snapshot||{}).position||null"),
  status: await j(s, `!!document.querySelector(${JSON.stringify(STATUS_SEL)})`) });
async function camStill(s) {
  let a = await j(s, "JSON.stringify((window.__geo3d_camera_snapshot||{}).position||null)");
  for (let i = 0; i < 20; i += 1) { await sleep(200); const b = await j(s, "JSON.stringify((window.__geo3d_camera_snapshot||{}).position||null)"); if (a === b) return; a = b; }
}

const { sv, cong } = await phucVu(DIST);
const rows = [];
try {
  for (const [roleKey, { role, session }] of Object.entries(ROLES)) {
    for (const [vpKey, vp] of Object.entries(VIEWPORTS)) {
     if (opt("--only") && !opt("--only").split(",").includes(`${roleKey}:${vpKey}`)) continue;
     // One retry, logged, ONLY when the page rendered without its stylesheet (environment flake already recorded in
     // phone-landscape-layout attempt 1); every other failure is final.
     const envRetries = [];
     for (let attempt = 1; attempt <= 2; attempt += 1) {
      const s = new BrowserSession({ viewport: vp.width, height: vp.height, webgl: true,
        url: `http://127.0.0.1:${cong}`, napModuleDev: false });
      const fail = [];
      let m = null; const extra = {}; let envFlake = false;
      try {
        // Chrome that does not start (WS_OPEN_TIMEOUT) is the same class of environment flake: one logged retry.
        try { await s.open(); } catch (e) { envFlake = true; throw e; }
        if (!vp.desktop) await s._send("Emulation.setDeviceMetricsOverride", { width: vp.width, height: vp.height,
          deviceScaleFactor: 2, mobile: true });
        await s.interceptJson("*/api/*", stub(role, session));
        await s._send("Page.reload", {});
        const nav = role === "teacher" ? "Bài đã giao" : "Bài thực hành";
        await pollUntil(() => s.eval(`[...document.querySelectorAll('button,a')].some(b=>b.textContent.includes(${JSON.stringify(nav)}))`), Boolean, { timeoutMs: 20000 });
        await s.eval(`[...document.querySelectorAll('button,a')].find(b=>b.textContent.includes(${JSON.stringify(nav)})).click()`);
        const open = role === "teacher" ? "Mở để dạy" : "Bắt đầu";
        await pollUntil(() => s.eval(`[...document.querySelectorAll('button')].some(b=>b.textContent.trim()===${JSON.stringify(open)})`), Boolean, { timeoutMs: 20000 });
        await s.eval(`[...document.querySelectorAll('button')].find(b=>b.textContent.trim()===${JSON.stringify(open)}).click()`);
        await pollUntil(() => s.eval("!!document.querySelector('.geo3d-canvas canvas')"), Boolean, { timeoutMs: 20000 });
        await pollUntil(() => s.eval(session ? "!!document.querySelector('.live-chi-bao,.live-cap,.live-nut-ket')"
          : "!!document.querySelector('.live-dock,.live-dock-thu')"), Boolean, { timeoutMs: 15000 });
        if (!await j(s, "getComputedStyle(document.querySelector('.geo3d-thanh')).display==='flex'")) {
          envFlake = true; throw new Error("ENV_STYLESHEET_NOT_APPLIED");
        }
        if (CSS) await s.eval(`(()=>{const st=document.createElement('style');st.textContent=${JSON.stringify(CSS)};document.head.appendChild(st);return true})()`);
        if (COLLAPSE_DOCK && await j(s, "!!document.querySelector('.live-dock-gap')")) await trustedClick(s, "document.querySelector('.live-dock-gap')");
        await j(s, "(scrollTo(0,0),true)");
        await sleep(800);
        await camStill(s);
        m = await j(s, MEASURE);
        if (m.scroll_width > m.client_width + 1) fail.push("HORIZONTAL_SCROLL");
        if (m.title.w < TITLE_MIN_PX || !m.title.inside) fail.push("TITLE_HIDDEN");
        if (!m.class_status || !m.class_status.inside) fail.push("CLASS_STATUS_NOT_IN_VIEW");
        if (m.buttons.some((b) => !b.inside)) fail.push("TOP_ROW_BUTTON_OUTSIDE_VIEWPORT");
        if (m.buttons.some((b) => !b.tappable)) fail.push("TOP_ROW_BUTTON_COVERED");
        if (!m.controls_inside) fail.push("PLAYER_CONTROLS_OUTSIDE_VIEWPORT");
        if (m.canvas.h < 320) fail.push("CANVAS_BELOW_FLOOR");
        if (!m.canvas.centre_free) fail.push("CANVAS_CENTRE_COVERED");
        if (SHOTS && (!SHOT_CASES || SHOT_CASES.includes(`${roleKey}:${vpKey}`))) { mkdirSync(SHOTS, { recursive: true }); await s.screenshot(join(SHOTS, `${roleKey}__${vpKey}.png`)); }
        // Step buttons work by trusted click (forward then back — scenes open at step 1).
        const st0 = await stepText(s);
        const okF = await trustedClick(s, "document.querySelector('.geo3d-controls [aria-label=\"Bước sau\"]')"); await sleep(400);
        const st1 = await stepText(s);
        const okB = await trustedClick(s, "document.querySelector('.geo3d-controls [aria-label=\"Bước trước\"]')"); await sleep(400);
        const st2 = await stepText(s);
        extra.steps = [st0, st1, st2];
        if (!okF || !okB || st1 === st0 || st2 !== st0) fail.push("STEP_BUTTONS_NOT_WORKING");
        // Panel round trip from the top of the page keeps step, selection, camera and the class status.
        await j(s, "(scrollTo(0,0),true)"); await sleep(300); await camStill(s);
        const a = await state(s);
        const okO = await trustedClick(s, "document.querySelector('.geo3d-cac-buoc-mo')");
        await pollUntil(() => j(s, "!!document.querySelector('.geo3d-bang-noi[data-panel=\"cac-buoc\"]')"), Boolean, { timeoutMs: 5000 }).catch(() => null);
        const okC = await trustedClick(s, "document.querySelector('.geo3d-bang-noi[data-panel=\"cac-buoc\"] .geo3d-bang-noi-dong')");
        await sleep(500); await camStill(s);
        const b = await state(s);
        extra.panel_round_trip = { open: okO, close: okC, before: a, after: b };
        // Same camera tolerance as check-mobile-layout.mjs (`cungCam`, 1e-6): orbit damping leaves ~1e-12 noise.
        const sameCam = !!a.camera && !!b.camera && a.camera.every((x, i) => Math.abs(x - b.camera[i]) < 1e-6);
        if (!okO || !okC || a.step !== b.step || a.selected !== b.selected || !sameCam || !b.status)
          fail.push("PANEL_ROUND_TRIP_CHANGED_STATE");
        // Chip mode: every band control must be reachable — open the chip by trusted click, every button in the
        // dropdown rendered, in view, tappable, the assignment label shown; Escape closes it.
        const chipShown = await j(s, "(()=>{const b=document.querySelector('.geo3d-lop-nut');return !!b&&b.getClientRects().length>0})()");
        extra.chip = { shown: chipShown };
        if (chipShown) {
          await j(s, "(scrollTo(0,0),true)"); await sleep(300);
          const okChip = await trustedClick(s, "document.querySelector('.geo3d-lop-nut')"); await sleep(400);
          const inner = await j(s, "(()=>{const W=innerWidth,H=innerHeight;const t=document.querySelector('.geo3d-lop-than');"
            + "const bs=[...t.querySelectorAll('button')].map(b=>{const r=b.getBoundingClientRect();"
            + "const h=r.width>0?document.elementFromPoint(r.left+r.width/2,r.top+r.height/2):null;"
            + "return {text:b.textContent.trim().slice(0,30),rendered:b.getClientRects().length>0,"
            + "inside:r.width>0&&r.left>=-0.5&&r.right<=W+0.5&&r.top>=-0.5&&r.bottom<=H+0.5,tappable:!!h&&(h===b||b.contains(h))}});"
            + "const l=t.querySelector('.nav-assignment');"
            + "return {expanded:document.querySelector('.geo3d-lop-nut').getAttribute('aria-expanded'),buttons:bs,"
            + "label_shown:!!l&&l.getClientRects().length>0}})()");
          await s.pressKey("Escape"); await sleep(300);
          const closed = await j(s, "document.querySelector('.geo3d-lop-nut').getAttribute('aria-expanded')==='false'");
          extra.chip = { shown: true, open: okChip, ...inner, closed_by_escape: closed };
          if (!okChip || inner.expanded !== "true" || inner.buttons.length === 0 || !inner.label_shown
            || inner.buttons.some((x) => !x.rendered || !x.inside || !x.tappable) || !closed)
            fail.push("CLASS_BAND_NOT_REACHABLE_THROUGH_CHIP");
        }
      } catch (e) { fail.push(`ERROR:${String(e?.message || e).slice(0, 80)}`); }
      finally { try { await s.close(); } catch { /* never opened */ } }
      if (envFlake && attempt === 1) { envRetries.push(fail.find((f) => f.startsWith("ERROR:")) ?? "ENV"); continue; }
      const row = { role: roleKey, viewport: vpKey, pass: fail.length === 0, failures: fail, ...(m || {}), viewport_key: vpKey, ...extra, env_retries: envRetries };
      row.viewport = vpKey;
      rows.push(row);
      console.log(`${row.pass ? "✓" : "✗"} ${roleKey.padEnd(12)} ${vpKey.padEnd(17)} ${fail.join(",")} top=${m ? m.top_row.b - m.top_row.y : "?"} title=${m?.title.w} ctl=${m?.controls_bottom}/${vp.height} status=${m?.class_status?.visible_w ?? "-"}px${envRetries.length ? " [env retry]" : ""}${extra.chip?.shown ? " chip" : ""}`);
      break;
     }
    }
  }
} finally { sv.close(); }
writeFileSync(OUT, JSON.stringify({ schema: "class-band-probe/2", application_llm_calls: 0, css_injected: !!CSS,
  collapse_dock_click: COLLAPSE_DOCK, title_min_px: TITLE_MIN_PX, fixture: fixture.case_id, rows }, null, 2));
console.log(`${rows.filter((r) => r.pass).length}/${rows.length} pass`);
