/**
 * regular-square-pyramid-w02 — đầu dò trình duyệt THẬT cho phần giao diện W2, 0 lượt gọi model.
 *
 * Mọi thao tác đi qua CDP (chuột `Input.dispatchMouseEvent`, phím `Input.dispatchKeyEvent`, đổi cỡ khung) trên
 * `dist/` phục vụ fixture đóng băng qua đúng biên mạng của sản phẩm (`openFixture`). Phán quyết ở hàm THUẦN của
 * `compiler-scene-replay-lib.mjs` (có ca tiêm lỗi ở node-test):
 *   B  `assessFloatingPanel` (desktop) · `assessStepsSheet` (khổ hẹp)
 *   A  nhãn theo bước, cả "Hiện tất cả": id trong DOM = `expectedAnnotationIds` (oracle độc lập); nhãn hợp lệ mà
 *      thiếu chỗ (`__geo3d_annotation_unplaced`) vẫn có trong ngăn «Đại lượng»
 *   C  đoạn vai CONSTRUCT_HEIGHT có mặt trên hình ở bước cuối
 *   D  `assessAuxiliary` · F `assessGridToggle`
 * Ảnh: bảng mở/kéo, nhãn theo bước, SO, hình phụ, lưới, khổ hẹp.
 *
 * Cờ: `--fixture-root <thư mục có fixtures/>` `--ra <thư mục kết quả>` `--anh <thư mục ảnh>` `--bo-qua-build`
 */
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { phucVu } from "./scene3d-orbit-gate.mjs";
import { capture, openFixture, trustedClick } from "./compiler-scene-suite.mjs";
import {
  assessAuxiliary, assessFloatingPanel, assessGridToggle, assessStepsSheet, expectedAnnotationIds,
  expectedGeometryTimeline, pollUntil, sortedUnique,
} from "./compiler-scene-replay-lib.mjs";

const CO = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, ds) => {
  if (x.startsWith("--")) a.push([x.slice(2), ds[i + 1]?.startsWith("--") ? true : ds[i + 1] ?? true]);
  return a;
}, []));
const FE = resolve(import.meta.dirname, "..");
const GOC = resolve(FE, "..");
const ROOT = resolve(String(CO["fixture-root"]));
const RA = resolve(String(CO.ra));
const ANH = resolve(String(CO.anh));
const HO = ["triangular_pyramid", "rectangular_pyramid", "triangular_prism", "cuboid", "cube", "cross_section",
  "regular_square_pyramid"];
const DESKTOP = { width: 1440, height: 900 };
const MOBILE = { width: 390, height: 844 };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

if (!CO["bo-qua-build"]) execFileSync("npm", ["run", "build"], { cwd: FE, stdio: "inherit", shell: true });
mkdirSync(RA, { recursive: true });

const j = async (s, e) => JSON.parse(await s.eval(`JSON.stringify(${e})`));
const hop = (s, sel) => j(s, `(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return null;`
  + "const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})()");
const cam = (s) => j(s, "window.__geo3d_camera_snapshot||null");
const buoc = (s) => j(s, "(document.querySelector('.geo3d-buoc-so')?.textContent||'').trim()");
const chon = (s) => j(s, "window.__geo3d_selected_id||null");
const veNgay = (s) => j(s, "(window.__geo3d_rendered_object_ids||[]).slice()");
const nghi = () => sleep(700);
const chip = (s, t) => trustedClick(s, `[...document.querySelectorAll('.geo3d-thanh-nut .geo3d-chip')]`
  + `.find((b)=>(b.textContent||'').trim()===${JSON.stringify(t)})`);
const coChip = (s, t) => j(s, `[...document.querySelectorAll('.geo3d-thanh-nut .geo3d-chip')]`
  + `.some((b)=>(b.textContent||'').trim()===${JSON.stringify(t)})`);
const moBang = async (s, mo) => {
  const dang = await j(s, "document.querySelector('.geo3d-cac-buoc-mo')?.getAttribute('aria-expanded')==='true'");
  if (dang !== mo) await trustedClick(s, "document.querySelector('.geo3d-cac-buoc-mo')");
  await pollUntil(() => j(s, "!!document.querySelector('.geo3d-bang-noi')"), (x) => x === mo, { timeoutMs: 5000 });
  await nghi();
};
const denBuoc = async (s, g) => {
  await moBang(s, true);
  await trustedClick(s, `document.querySelector('[data-geometry-step="${g}"]')`);
  await nghi();
};
async function keo(s, x, y, dx, dy) {
  const gui = (type, px, py, buttons) => s._send("Input.dispatchMouseEvent",
    { type, x: px, y: py, button: "left", buttons, clickCount: 1 });
  await gui("mouseMoved", x, y, 0);
  await gui("mousePressed", x, y, 1);
  for (let i = 1; i <= 8; i += 1) await gui("mouseMoved", x + (dx * i) / 8, y + (dy * i) / 8, 1);
  await gui("mouseReleased", x + dx, y + dy, 0);
  await nghi();
}
const tamTieuDe = async (s) => {
  const r = await hop(s, ".geo3d-bang-noi-tieu");
  return [r.x + Math.min(r.w / 2, 40), r.y + r.h / 2];
};
const thayNutDong = (s) => j(s, "(()=>{const b=document.querySelector('.geo3d-bang-noi [aria-label=\"Đóng\"]');"
  + "if(!b)return false;const r=b.getBoundingClientRect();const x=r.x+r.width/2,y=r.y+r.height/2;"
  + "return x>=0&&y>=0&&x<=innerWidth&&y<=innerHeight&&(document.elementFromPoint(x,y)===b||b.contains(document.elementFromPoint(x,y)))})()");

async function phim(s, key, code) {
  for (const type of ["keyDown", "keyUp"]) {
    await s._send("Input.dispatchKeyEvent", { type, key, code: key, windowsVirtualKeyCode: code });
  }
  await sleep(150);
}

async function desktopPanel(s) {
  const canvas_before = await hop(s, ".geo3d-canvas");
  const camera_before = await cam(s);
  const step_before = await buoc(s);
  const selected_before = await chon(s);
  await moBang(s, true);
  const o = { canvas_before, camera_before, step_before, selected_before };
  o.position = await j(s, "getComputedStyle(document.querySelector('.geo3d-bang-noi')).position");
  o.canvas_open = await hop(s, ".geo3d-canvas");
  o.camera_open = await cam(s);
  o.panel_open = await hop(s, ".geo3d-bang-noi");
  let [x, y] = await tamTieuDe(s);
  await keo(s, x, y, -420, 160);
  o.panel_dragged = await hop(s, ".geo3d-bang-noi");
  o.camera_after_drag = await cam(s);
  [x, y] = await tamTieuDe(s);
  await keo(s, x, y, -3000, -3000);
  o.panel_far = await hop(s, ".geo3d-bang-noi");
  o.close_visible_far = await thayNutDong(s);
  await j(s, "(document.querySelector('.geo3d-bang-noi-dau').focus(),true)");
  const truoc = await hop(s, ".geo3d-bang-noi");
  for (let i = 0; i < 3; i += 1) await phim(s, "ArrowRight", 39);
  o.key_dx = (await hop(s, ".geo3d-bang-noi")).x - truoc.x;
  await s.setViewport({ width: 1100, height: 700 });
  await nghi();
  o.canvas_resized = await hop(s, ".geo3d-canvas");
  o.panel_resized = await hop(s, ".geo3d-bang-noi");
  o.close_visible_resized = await thayNutDong(s);
  await s.setViewport(null);
  await nghi();
  await trustedClick(s, "document.querySelector('.geo3d-bang-noi [aria-label=\"Về vị trí mặc định\"]')");
  await nghi();
  o.panel_reset = await hop(s, ".geo3d-bang-noi");
  [x, y] = await tamTieuDe(s);
  await keo(s, x, y, -300, 120);
  o.panel_closed_at = await hop(s, ".geo3d-bang-noi");
  await j(s, "(document.querySelector('.geo3d-bang-noi-dau').focus(),true)");
  await phim(s, "Escape", 27);
  await pollUntil(() => j(s, "!!document.querySelector('.geo3d-bang-noi')"), (v) => v === false, { timeoutMs: 5000 });
  o.focus_after_close = await j(s, "document.activeElement?.classList.contains('geo3d-cac-buoc-mo')?'geo3d-cac-buoc-mo':(document.activeElement?.tagName||'')");
  await moBang(s, true);
  o.panel_reopened = await hop(s, ".geo3d-bang-noi");
  o.step_after = await buoc(s);
  o.selected_after = await chon(s);
  return o;
}

async function nhanTheoBuoc(s, scene, ho, anhDir) {
  const t = expectedGeometryTimeline(scene);
  const ra = [];
  await moBang(s, true);
  for (let g = 0; g < t.length; g += 1) {
    await denBuoc(s, g);
    const dom = await j(s, "[...document.querySelectorAll('.geo3d-so-do')].map((e)=>e.dataset.annId).sort()");
    const unplaced = await j(s, "(window.__geo3d_annotation_unplaced||[]).slice().sort()");
    ra.push({ step: g, anchor: t[g].anchor, dom, expected: expectedAnnotationIds(scene, t[g].anchor, { showAll: true }),
      unplaced });
    if (["triangular_pyramid", "triangular_prism"].includes(ho) && g <= 3) {
      await moBang(s, false);
      ra[ra.length - 1].image = await capture(s, join(anhDir, `labels_showall_step_${g}.png`));
      await moBang(s, true);
    }
  }
  return ra;
}

async function quantityIds(s) {
  if (!await coChip(s, "Đại lượng")) return [];
  await chip(s, "Đại lượng");
  await pollUntil(() => j(s, "!!document.querySelector('.geo3d-dai-luong')"), Boolean, { timeoutMs: 5000 });
  const ids = await j(s, "[...document.querySelectorAll('.geo3d-dai-luong [data-quantity-id]')].map(e=>e.dataset.quantityId)");
  await chip(s, "Đại lượng");
  return ids;
}

async function runDesktop(ho, fixture) {
  const scene = fixture.envelope.scene3d;
  const anhDir = join(ANH, ho.replaceAll("_", "-"), "desktop");
  const { sv, cong } = await phucVu(join(FE, "dist"));
  const { session: s } = await openFixture({ port: cong, viewport: DESKTOP, fixture });
  const kq = { family: ho, viewport: "desktop" };
  try {
    await pollUntil(() => j(s, "!!document.querySelector('.geo3d-canvas canvas')"), Boolean, { timeoutMs: 20000 });
    await nghi();
    kq.panel_observation = await desktopPanel(s);
    kq.panel = assessFloatingPanel(kq.panel_observation);
    await trustedClick(s, "document.querySelector('.geo3d-bang-noi [aria-label=\"Về vị trí mặc định\"]')");
    await nghi();
    kq.images = { panel_open_default: await capture(s, join(anhDir, "steps_panel_floating.png")) };
    const [x, y] = await tamTieuDe(s);
    await keo(s, x, y, -480, 120);
    kq.images.panel_dragged = await capture(s, join(anhDir, "steps_panel_dragged.png"));
    await trustedClick(s, "document.querySelector('.geo3d-bang-noi [aria-label=\"Về vị trí mặc định\"]')");
    // A: nhãn theo bước ở "Hiện tất cả" (chế độ rộng nhất); mặc định đã do bộ đo chính kiểm từng bước.
    if (await coChip(s, "Hiện tất cả")) await chip(s, "Hiện tất cả");
    kq.labels_by_step = await nhanTheoBuoc(s, scene, ho, anhDir);
    const t = expectedGeometryTimeline(scene);
    kq.labels_pass = kq.labels_by_step.every((r) => JSON.stringify(r.dom) === JSON.stringify(r.expected));
    // Nhãn hợp lệ thiếu chỗ: vẫn đọc được trong ngăn «Đại lượng».
    const cuoi = kq.labels_by_step[kq.labels_by_step.length - 1];
    await moBang(s, false);
    const ids = await quantityIds(s);
    kq.unplaced_reachable = cuoi.unplaced.every((id) => ids.includes(id));
    if (await coChip(s, "Hiện tất cả")) await chip(s, "Hiện tất cả");
    await nghi();
    // C: đoạn chiều cao có mặt ở bước cuối.
    const cao = scene.objects.filter((o) => o.type === "segment3" && (o.formation_roles ?? []).includes("CONSTRUCT_HEIGHT"))
      .map((o) => o.id);
    const ve = await veNgay(s);
    kq.height_segments = { expected: cao, rendered: cao.filter((id) => ve.includes(id)) };
    kq.height_pass = cao.every((id) => ve.includes(id));
    kq.images.final_neutral = await capture(s, join(anhDir, "final_neutral.png"));
    // D: hình phụ.
    const coPhu = await coChip(s, "Hình phụ");
    const aux = { scene, step: t[t.length - 1].anchor, chip: coPhu,
      hidden_default: await j(s, "(window.__geo3d_auxiliary_hidden_ids||[]).slice()"), rendered_default: ve };
    if (coPhu) {
      await chip(s, "Hình phụ");
      await nghi();
      aux.hidden_shown = await j(s, "(window.__geo3d_auxiliary_hidden_ids||[]).slice()");
      aux.rendered_shown = await veNgay(s);
      kq.images.auxiliary_shown = await capture(s, join(anhDir, "auxiliary_shown.png"));
      await chip(s, "Hình phụ");
      await nghi();
    } else {
      aux.hidden_shown = [];
      aux.rendered_shown = ve;
    }
    kq.auxiliary = assessAuxiliary(aux);
    kq.auxiliary_observation = { ...aux, scene: undefined };
    // F: lưới — chọn một đại lượng trước để kiểm lựa chọn không đổi.
    const g0 = { initial: await j(s, "window.__geo3d_grid_visible===true") };
    const q = (await quantityIds(s))[0];
    if (q) {
      await chip(s, "Đại lượng");
      await trustedClick(s, `document.querySelector('[data-quantity-id="${q}"]')`);
      await nghi();
    }
    g0.camera_before = await cam(s);
    g0.step_before = await buoc(s);
    g0.selected_before = await chon(s);
    g0.rendered_before = await veNgay(s);
    await chip(s, "Lưới");
    await nghi();
    g0.on = await j(s, "window.__geo3d_grid_visible===true");
    g0.camera_on = await cam(s);
    g0.step_on = await buoc(s);
    g0.selected_on = await chon(s);
    g0.rendered_on = await veNgay(s);
    const r0 = await j(s, "window.__geo3d_occlusion_performance?.recompute_count??null");
    await sleep(1200);
    const r1 = await j(s, "window.__geo3d_occlusion_performance?.recompute_count??null");
    g0.recompute_idle_delta = r0 === null || r1 === null ? null : r1 - r0;
    kq.images.grid_on = await capture(s, join(anhDir, "grid_on.png"));
    await chip(s, "Lưới");
    await nghi();
    g0.off = await j(s, "window.__geo3d_grid_visible===true");
    kq.grid = assessGridToggle(g0);
    kq.grid_observation = g0;
    kq.exceptions = s.consoleEvents.filter((e) => e.loai === "exception");
  } finally {
    await s.close();
    sv.close();
  }
  return kq;
}

async function runMobile(ho, fixture) {
  const anhDir = join(ANH, ho.replaceAll("_", "-"), "mobile");
  const { sv, cong } = await phucVu(join(FE, "dist"));
  const { session: s } = await openFixture({ port: cong, viewport: MOBILE, fixture });
  const kq = { family: ho, viewport: "mobile" };
  try {
    await pollUntil(() => j(s, "!!document.querySelector('.geo3d-canvas canvas')"), Boolean, { timeoutMs: 20000 });
    await nghi();
    const o = { canvas_before: await hop(s, ".geo3d-canvas"), camera_before: await cam(s) };
    await moBang(s, true);
    o.position = await j(s, "getComputedStyle(document.querySelector('.geo3d-bang-noi')).position");
    o.canvas_open = await hop(s, ".geo3d-canvas");
    o.controls = await hop(s, ".geo3d-controls");
    o.panel = await hop(s, ".geo3d-bang-noi");
    await j(s, "(document.querySelector('.geo3d-bang-noi').scrollIntoView({block:'center'}),true)");
    await nghi();
    const p = await hop(s, ".geo3d-bang-noi-tieu");
    const truoc = await hop(s, ".geo3d-bang-noi");
    o.camera_before = await cam(s);
    await keo(s, p.x + 20, p.y + p.h / 2, -120, -200);
    const sau = await hop(s, ".geo3d-bang-noi");
    o.panel_after_drag = { ...o.panel, x: o.panel.x + (sau.x - truoc.x), y: o.panel.y + (sau.y - truoc.y) };
    o.camera_after_drag = await cam(s);
    kq.images = { sheet_open: await capture(s, join(anhDir, "steps_sheet_open.png")) };
    o.expanded_body_present = await j(s, "!!document.querySelector('.geo3d-bang-noi-than')");
    await trustedClick(s, "document.querySelector('.geo3d-bang-noi-gon')");
    await nghi();
    o.collapsed_body_present = await j(s, "!!document.querySelector('.geo3d-bang-noi-than')");
    kq.images.sheet_collapsed = await capture(s, join(anhDir, "steps_sheet_collapsed.png"));
    await trustedClick(s, "document.querySelector('.geo3d-bang-noi-gon')");
    await nghi();
    const g = Math.min(2, expectedGeometryTimeline(fixture.envelope.scene3d).length - 1);
    await trustedClick(s, `document.querySelector('[data-geometry-step="${g}"]')`);
    await nghi();
    o.step_clicked = `Bước ${g + 1}/${expectedGeometryTimeline(fixture.envelope.scene3d).length}`;
    o.step_indicator = await buoc(s);
    kq.sheet = assessStepsSheet(o);
    kq.sheet_observation = o;
    kq.exceptions = s.consoleEvents.filter((e) => e.loai === "exception");
  } finally {
    await s.close();
    sv.close();
  }
  return kq;
}

const ket = [];
for (const ho of HO) {
  const fixture = JSON.parse(readFileSync(join(ROOT, "fixtures", `${ho}_positive.json`), "utf8"));
  for (const chay of [runDesktop, runMobile]) {
    const r = await chay(ho, fixture);
    const pass = chay === runDesktop
      ? r.panel.pass && r.labels_pass && r.unplaced_reachable && r.height_pass && r.auxiliary.pass && r.grid.pass
        && r.exceptions.length === 0
      : r.sheet.pass && r.exceptions.length === 0;
    ket.push({ ...r, pass });
    console.log(`${ho}/${r.viewport}: ${pass ? "PASS" : "FAIL"} ${JSON.stringify(sortedUnique([
      ...(r.panel?.reason_codes ?? []), ...(r.sheet?.reason_codes ?? []), ...(r.auxiliary?.reason_codes ?? []),
      ...(r.grid?.reason_codes ?? []), ...(r.labels_pass === false ? ["LABELS_BY_STEP"] : []),
      ...(r.unplaced_reachable === false ? ["UNPLACED_NOT_REACHABLE"] : []),
      ...(r.height_pass === false ? ["HEIGHT_SEGMENT_MISSING"] : [])]))}`);
  }
}
const out = { schema_version: "w02-closure-probe/1", application_llm_calls: 0,
  commit: execFileSync("git", ["rev-parse", "HEAD"], { cwd: GOC, encoding: "utf8" }).trim(),
  pass: ket.every((r) => r.pass), runs: ket };
writeFileSync(join(RA, "W02_CLOSURE_PROBE.json"), `${JSON.stringify(out, null, 2)}\n`);
console.log(`W02 probe: ${ket.filter((r) => r.pass).length}/${ket.length} PASS`);
process.exit(out.pass ? 0 : 1);
