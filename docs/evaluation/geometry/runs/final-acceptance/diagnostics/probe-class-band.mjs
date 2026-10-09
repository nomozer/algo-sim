// Throwaway probe: classroom band (daiLop) in the 3D top row at phone sizes. 0 model calls, API stubbed.
// usage: node probe-class-band.mjs <repo> <dist> <out.json> [shotDir]
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const [REPO, DIST, OUT, SHOTS] = process.argv.slice(2);
const imp = (p) => import(pathToFileURL(join(REPO, "frontend/scripts", p)).href);
const { BrowserSession, sleep } = await imp("browser-runner.mjs");
const { phucVu } = await imp("scene3d-orbit-gate.mjs");
const { pollUntil } = await imp("compiler-scene-replay-lib.mjs");

const fixture = JSON.parse(readFileSync(join(REPO,
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
// Realistic long-ish Vietnamese labels: teacher-written title, class name.
const ASSIGNMENT = { id: 7, classroomId: 3, title: "Chóp tứ giác đều — tính thể tích và góc giữa cạnh bên với đáy",
  instruction: "Làm theo từng bước", simulationId: fixture.envelope.simulation_id, closed: false,
  createdAt: "2026-10-09T00:00:00Z", myPractice: null };
const ROLES = {
  teacher_idle: { role: "teacher", session: null },
  teacher_live: { role: "teacher", session: SESSION },
  student_live: { role: "student", session: SESSION },
};

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

const MEASURE = `(()=>{
  const W=innerWidth,H=innerHeight,de=document.documentElement;
  const box=(e)=>{const r=e.getBoundingClientRect();return {x:Math.round(r.left),y:Math.round(r.top),r:Math.round(r.right),b:Math.round(r.bottom),w:Math.round(r.width)}};
  const row=document.querySelector('.geo3d-thanh');
  const kids=[...row.children].map(e=>({cls:e.className.split(' ')[0]||e.tagName,text:(e.textContent||'').trim().slice(0,40),...box(e),
    clipped:e.scrollWidth>e.clientWidth+1}));
  const btns=[...row.querySelectorAll('button')].map(b=>{const r=b.getBoundingClientRect();
    const cx=r.left+r.width/2,cy=r.top+r.height/2;const hit=document.elementFromPoint(cx,cy);
    return {text:(b.textContent||'').trim().slice(0,30),inside:r.left>=-0.5&&r.right<=W+0.5&&r.top>=-0.5&&r.bottom<=H+0.5,
      tappable:!!hit&&(hit===b||b.contains(hit)),w:Math.round(r.width),h:Math.round(r.height)}});
  const ctl=document.querySelector('.geo3d-controls');const c=ctl?ctl.getBoundingClientRect():null;
  const cv=document.querySelector('.geo3d-canvas').getBoundingClientRect();
  return {viewport:{w:W,h:H},scroll_width:de.scrollWidth,client_width:de.clientWidth,
    top_row:box(row),top_row_overflows:row.scrollWidth>row.clientWidth+1,children:kids,buttons:btns,
    canvas:{y:Math.round(cv.top),h:Math.round(cv.height)},
    controls_bottom:c?Math.round(c.bottom):null,controls_inside:!!c&&c.bottom<=H+0.5&&c.right<=W+0.5};
})()`;

const { sv, cong } = await phucVu(DIST);
const rows = [];
try {
  for (const [roleKey, { role, session }] of Object.entries(ROLES)) {
    for (const [vpKey, vp] of Object.entries(VIEWPORTS)) {
      const s = new BrowserSession({ viewport: vp.width, height: vp.height, webgl: true,
        url: `http://127.0.0.1:${cong}`, napModuleDev: false });
      await s.open();
      try {
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
        // Let the session/monitor polls land, then let layout settle.
        await pollUntil(() => s.eval(session ? "!!document.querySelector('.live-chi-bao,.live-cap,.live-nut-ket')"
          : "!!document.querySelector('.live-dock,.live-dock-thu')"), Boolean, { timeoutMs: 15000 });
        await sleep(800);
        const m = JSON.parse(await s.eval(`JSON.stringify(${MEASURE})`));
        const fail = [];
        if (m.scroll_width > m.client_width + 1) fail.push("HORIZONTAL_SCROLL");
        if (m.buttons.some((b) => !b.inside)) fail.push("TOP_ROW_BUTTON_OUTSIDE_VIEWPORT");
        if (m.buttons.some((b) => !b.tappable)) fail.push("TOP_ROW_BUTTON_COVERED");
        if (!m.controls_inside) fail.push("PLAYER_CONTROLS_OUTSIDE_VIEWPORT");
        const row = { role: roleKey, ...m, viewport: vpKey, size: m.viewport, pass: fail.length === 0, failures: fail };
        rows.push(row);
        console.log(`${row.pass ? "✓" : "✗"} ${roleKey} ${vpKey} ${fail.join(",")} top_row_h=${m.top_row.b - m.top_row.y} scrollW=${m.scroll_width}/${m.client_width} controls_bottom=${m.controls_bottom}/${vp.height}`);
        if (SHOTS && !row.pass) { mkdirSync(SHOTS, { recursive: true }); await s.screenshot(join(SHOTS, `${roleKey}__${vpKey}.png`)); }
      } finally { await s.close(); }
    }
  }
} finally { sv.close(); }
writeFileSync(OUT, JSON.stringify({ schema: "class-band-probe/1", fixture: fixture.case_id,
  product_commit_sha: fixture.product_commit_sha, rows }, null, 2));
console.log(`${rows.filter((r) => r.pass).length}/${rows.length} pass`);
