/**
 * regular-square-pyramid-w04 — đầu dò trình duyệt THẬT cho SHARED_SIMULATION_UI_CLOSURE, 0 lượt gọi model.
 *
 * Thao tác qua CDP (chuột, phím, đổi cỡ khung) trên `dist/` phục vụ fixture đóng băng qua đúng biên mạng của sản phẩm
 * (`openFixture`). Phán quyết ở hàm THUẦN của `compiler-scene-replay-lib.mjs` (mỗi hàm có ca tiêm lỗi ở node-test):
 *   Y3 bảng nổi   `assessPanelsDesktop` (1440×900) · `assessPanelsMobile` (390×844)
 *   Y4 bố cục     `assessLayout` — desktop, màn thấp 1366×650, mobile; khung trung tính · xoay · đổi cỡ
 *   Y5 chọn vật   `assessDirectSelect` (bấm thẳng lên hình, kéo để xoay) · `assessTreePanel` (cây theo bước)
 * Ảnh cho gói duyệt: nhiều bảng cùng mở, bảng kéo, đổi cỡ, chọn trên hình + cây, bố cục từng khổ, mobile.
 *
 * Cờ: `--fixture-root <thư mục có fixtures/>` `--ra <thư mục kết quả>` `--anh <thư mục ảnh>` `--bo-qua-build`
 *     `--dist <thư mục build>` (mặc định `frontend/dist`)
 *     `--ho <họ1,họ2>` (mặc định bảy họ)
 */
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { phucVu } from "./scene3d-orbit-gate.mjs";
import { capture, openFixture, trustedClick } from "./compiler-scene-suite.mjs";
import {
  assessDirectSelect, assessLayout, assessPanelsDesktop, assessPanelsMobile, assessTreePanel, chieuManHinh,
  expectedAnnotationIds, expectedGeometryTimeline, expectedVisibleIds, pollUntil, sortedUnique,
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
const DIST = CO.dist ? resolve(String(CO.dist)) : join(FE, "dist");
const HO = typeof CO.ho === "string" ? CO.ho.split(",") : ["triangular_pyramid", "rectangular_pyramid",
  "triangular_prism", "cuboid", "cube", "cross_section", "regular_square_pyramid"];
const DESKTOP = { width: 1440, height: 900 };
const THAP = { width: 1366, height: 650 };
const MOBILE = { width: 390, height: 844 };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

if (!CO["bo-qua-build"]) execFileSync("npm", ["run", "build"], { cwd: FE, stdio: "inherit", shell: true });
mkdirSync(RA, { recursive: true });

const j = async (s, e) => JSON.parse(await s.eval(`JSON.stringify(${e})`));
const q = (sel) => `document.querySelector(${JSON.stringify(sel)})`;
/** Hộp theo khung nhìn. */
const hop = (s, sel) => j(s, `(()=>{const e=${q(sel)};if(!e)return null;`
  + "const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})()");
/** Hộp theo TRANG (cộng cuộn) — so được giữa các lần cuộn trên mobile. */
const hopTrang = (s, sel) => j(s, `(()=>{const e=${q(sel)};if(!e)return null;`
  + "const r=e.getBoundingClientRect();return {x:r.x+scrollX,y:r.y+scrollY,w:r.width,h:r.height}})()");
const cam = (s) => j(s, "window.__geo3d_camera_snapshot||null");
const buoc = (s) => j(s, "(document.querySelector('.geo3d-controls .geo3d-buoc-so')?.textContent||'').trim()");
const chonId = (s) => j(s, "window.__geo3d_selected_id||null");
const nghi = () => sleep(700);
const coBang = (s, id) => j(s, `!!${q(`.geo3d-bang-noi[data-panel="${id}"]`)}`);
const choBang = (s, id, mo) => pollUntil(() => coBang(s, id), (x) => x === mo, { timeoutMs: 5000 });
const NUT_MO = { "thanh-phan": "[data-mo-bang=\"thanh-phan\"]", "dai-luong": "[data-mo-bang=\"dai-luong\"]",
  de: "[data-mo-bang=\"de\"]", "cac-buoc": ".geo3d-cac-buoc-mo" };
async function moBang(s, id, mo = true) {
  if (await coBang(s, id) === mo) return;
  if (mo) await trustedClick(s, q(NUT_MO[id]));
  else await trustedClick(s, q(`.geo3d-bang-noi[data-panel="${id}"] .geo3d-bang-noi-dong`));
  await choBang(s, id, mo);
  await nghi();
}
const dongHet = async (s) => {
  for (const id of ["de", "thanh-phan", "dai-luong", "cac-buoc", "soi"]) if (await coBang(s, id)) await moBang(s, id, false);
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
async function bam(s, x, y) {
  for (const type of ["mouseMoved", "mousePressed", "mouseReleased"]) {
    await s._send("Input.dispatchMouseEvent", { type, x, y, button: "left", buttons: type === "mousePressed" ? 1 : 0,
      clickCount: 1 });
  }
  await nghi();
}
async function phim(s, key, code) {
  for (const type of ["keyDown", "keyUp"]) {
    // Enter phải mang `text` thì nút mới nhận "bấm" như phím thật
    await s._send("Input.dispatchKeyEvent", { type, key, code: key, windowsVirtualKeyCode: code,
      ...(type === "keyDown" && key === "Enter" ? { text: "\r" } : {}) });
  }
  await sleep(200);
}
/** Chờ camera đứng yên (giảm chấn quỹ đạo còn trôi sau một lần kéo) trước khi lấy mốc. */
async function camDung(s) {
  let a = await cam(s);
  for (let i = 0; i < 20; i += 1) {
    await sleep(250);
    const b = await cam(s);
    if (JSON.stringify(a) === JSON.stringify(b)) return b;
    a = b;
  }
  return a;
}
const tieuDe = async (s, id) => {
  const r = await hop(s, `[data-panel="${id}"] .geo3d-bang-noi-tieu`);
  return [r.x + Math.min(r.w / 2, 40), r.y + r.h / 2];
};
/** Nút đóng nhìn thấy và là phần tử trên cùng tại tâm của nó — "bảng không bị lạc". */
const dongBamDuoc = (s, id) => j(s, `(()=>{const b=${q(`[data-panel="${id}"] .geo3d-bang-noi-dong`)};`
  + "if(!b)return false;const r=b.getBoundingClientRect();const x=r.x+r.width/2,y=r.y+r.height/2;"
  + "return x>=0&&y>=0&&x<=innerWidth&&y<=innerHeight&&b.contains(document.elementFromPoint(x,y))})()");
const denBuocCuoi = async (s, scene) => {
  const t = expectedGeometryTimeline(scene);
  await moBang(s, "cac-buoc", true);
  await trustedClick(s, q(`[data-geometry-step="${t.length - 1}"]`));
  await nghi();
  await moBang(s, "cac-buoc", false);
  return t[t.length - 1].anchor;
};
const denBuoc = async (s, g) => {
  await moBang(s, "cac-buoc", true);
  await trustedClick(s, q(`[data-geometry-step="${g}"]`));
  await nghi();
  await moBang(s, "cac-buoc", false);
};

/** Một khung cho `assessLayout`: đỉnh (chiếu bằng ma trận camera THẬT) + hộp nhãn điểm, theo toạ độ canvas. */
async function khung(s, name) {
  await nghi();
  const c = await cam(s);
  const cham = await j(s, "(window.__geo3d_vertex_markers||[]).filter(m=>m.id)");
  return { name, w: c.viewport_width, h: c.viewport_height,
    vertices: cham.map((m) => ({ id: m.id, ...chieuManHinh(c, m.center) })).filter((v) => !v.behind),
    labels: await j(s, "(window.__geo3d_point_label_boxes||[]).slice()") };
}
async function boCuc(s, viewport, frames) {
  await j(s, "(scrollTo(0,0),true)");
  await nghi();
  const canvas = await hop(s, ".geo3d-canvas");
  // khung nhìn THẬT của trang (innerWidth/innerHeight), không phải cỡ đã xin — hai số có thể lệch
  return { viewport: await j(s, "({w:innerWidth,h:innerHeight})"), requested_viewport: { w: viewport.width, h: viewport.height },
    canvas, canvas_element: await hop(s, ".geo3d-canvas canvas"), controls: await hop(s, ".geo3d-controls"),
    canvas_at_floor: canvas.h <= 320.5,
    scroll_width: await j(s, "document.documentElement.scrollWidth"),
    client_width: await j(s, "document.documentElement.clientWidth"),
    step_counter: await j(s, "document.querySelector('.geo3d-controls .geo3d-buoc-so')?.textContent?.trim()||null"),
    narration_line_present: await j(s, "!!document.querySelector('.geo3d-buoc-loi')"),
    narration_live: await j(s, "document.querySelector('.geo3d-narration')?.getAttribute('aria-live')==='polite'"),
    frames };
}
const xoayKhung = async (s) => {
  const c = await hop(s, ".geo3d-canvas");
  await keo(s, c.x + c.w * 0.3, c.y + c.h * 0.5, 160, 40);
};

async function quanSatBang(s, ids) {
  const o = {};
  for (const id of ids) {
    o[id] = { position: await j(s, `getComputedStyle(${q(`.geo3d-bang-noi[data-panel="${id}"]`)}).position`),
      rect: await hopTrang(s, `.geo3d-bang-noi[data-panel="${id}"]`), close_reachable: await dongBamDuoc(s, id),
      header_buttons: await j(s, `[...document.querySelectorAll('[data-panel="${id}"] .geo3d-bang-noi-dau button')]`
        + ".filter(b=>getComputedStyle(b).display!=='none').map(b=>{const r=b.getBoundingClientRect();return {w:r.width,h:r.height}})") };
  }
  return o;
}

async function chonDaiLuong(s) {
  await moBang(s, "dai-luong", true);
  const id = await j(s, "document.querySelector('.geo3d-dai-luong [data-quantity-id]')?.dataset.quantityId||null");
  if (id) await trustedClick(s, q(`.geo3d-dai-luong [data-quantity-id="${id}"]`));
  await nghi();
  return id;
}

async function runDesktop(ho, fixture) {
  const scene = fixture.envelope.scene3d;
  const anh = join(ANH, ho.replaceAll("_", "-"), "desktop");
  const { sv, cong } = await phucVu(DIST);
  const { session: s } = await openFixture({ port: cong, viewport: DESKTOP, fixture });
  const kq = { family: ho, viewport: "desktop", images: {} };
  try {
    await pollUntil(() => j(s, "!!document.querySelector('.geo3d-canvas canvas')"), Boolean, { timeoutMs: 20000 });
    await nghi();
    // ── Y5 cây: đo TRƯỚC mọi lựa chọn (nhóm của vật chọn tự mở) ──
    const t = expectedGeometryTimeline(scene);
    const g1 = Math.min(1, t.length - 1);
    await denBuoc(s, g1);
    await moBang(s, "thanh-phan", true);
    const cay = { groups_total: await j(s, "document.querySelectorAll('.geo3d-tree details.geo3d-tree-cat').length"),
      groups_open_default: await j(s, "document.querySelectorAll('.geo3d-tree details.geo3d-tree-cat[open]').length") };
    const liet = await j(s, "[...document.querySelectorAll('.geo3d-tree [data-tree-id]')].map(e=>e.dataset.treeId)");
    const coMat = new Set(expectedVisibleIds(scene, t[g1].anchor));
    const trongCay = (o) => !(o.alias_of && o.render === "non_visual");
    const idCanh = new Set(scene.objects.map((o) => o.id));
    cay.future_listed = liet.filter((id) => idCanh.has(id) && !coMat.has(id));
    cay.present_missing = scene.objects.filter((o) => trongCay(o) && coMat.has(o.id) && !liet.includes(o.id))
      .map((o) => o.id);
    await trustedClick(s, "document.querySelector('.geo3d-tree details.geo3d-tree-cat > summary')");
    await nghi();
    const moList = () => j(s, "[...document.querySelectorAll('.geo3d-tree details.geo3d-tree-cat')].map(d=>d.open)");
    cay.reopen = { open_before: await moList() };
    await moBang(s, "thanh-phan", false);
    await moBang(s, "thanh-phan", true);
    cay.reopen.open_after = await moList();
    // bàn phím: Tab tới một mục trong nhóm đã mở, Enter chọn
    const muc = await j(s, "document.querySelector('.geo3d-tree details[open] [data-tree-id]')?.dataset.treeId||null");
    if (muc) {
      await j(s, `(document.querySelector('.geo3d-tree [data-tree-id="${muc}"]').focus(),true)`);
      await phim(s, "Enter", 13);
      await nghi();
    }
    cay.keyboard = { target: muc, selected: await chonId(s) };
    kq.images.tree_step = await capture(s, join(anh, "tree_by_step.png"));
    await dongHet(s);

    // ── Y3 bảng nổi (TRƯỚC mọi cử chỉ xoay — giảm chấn còn trôi sẽ bị tính nhầm là bảng dời camera) ──
    const neo = await denBuocCuoi(s, scene);
    const o = { canvas: { before: await hop(s, ".geo3d-canvas"), states: [] }, camera: { before: await camDung(s), states: [] },
      step: { before: await buoc(s), states: [] } };
    const ghi = async () => {
      o.canvas.states.push(await hop(s, ".geo3d-canvas"));
      o.camera.states.push(await cam(s));
      o.step.states.push(await buoc(s));
    };
    const coDe = await j(s, `!!${q(NUT_MO.de)}`);
    for (const id of ["cac-buoc", "thanh-phan", ...(coDe ? ["de"] : [])]) { await moBang(s, id, true); await ghi(); }
    const qid = await chonDaiLuong(s);
    await ghi();
    o.quantity = { id: qid, selected: await chonId(s), drawer_open: await coBang(s, "dai-luong"),
      inspector_open: await coBang(s, "soi"),
      label_shown: await j(s, `!!document.querySelector('.geo3d-so-do[data-ann-id="${qid}"]')`) };
    const bang = ["soi", "thanh-phan", "dai-luong", "cac-buoc", ...(coDe ? ["de"] : [])];
    o.panels = await quanSatBang(s, bang);
    for (const id of bang) o.panels[id].rect = await hop(s, `.geo3d-bang-noi[data-panel="${id}"]`);
    kq.images.panels_all_open = await capture(s, join(anh, "panels_all_open.png"));
    const annDung = async () => {
      const dom = await j(s, "[...document.querySelectorAll('.geo3d-so-do')].map(e=>e.dataset.annId).sort()");
      return JSON.stringify(dom) === JSON.stringify(expectedAnnotationIds(scene, neo, { selectedId: await chonId(s) }));
    };
    o.annotations = { pass: await annDung() };
    let [x, y] = await tieuDe(s, "thanh-phan");
    o.drag = { before: await hop(s, "[data-panel=\"thanh-phan\"]"), camera_before: await camDung(s) };
    await keo(s, x, y, -380, 90);
    o.drag.after = await hop(s, "[data-panel=\"thanh-phan\"]");
    o.drag.camera_after = await cam(s);
    await ghi();
    kq.images.panel_dragged = await capture(s, join(anh, "panels_dragged.png"));
    await s.setViewport({ width: 1100, height: 700 });
    await nghi();
    o.resized = { canvas: await hop(s, ".geo3d-canvas"), panels: {}, close_reachable: {}, header_reachable: {} };
    for (const id of bang) {
      o.resized.panels[id] = await hop(s, `.geo3d-bang-noi[data-panel="${id}"]`);
      o.resized.close_reachable[id] = await dongBamDuoc(s, id);
      // một điểm trên dải tiêu đề mà phần tử trên cùng thuộc chính bảng này ⇒ bấm vào là bảng lên trên
      o.resized.header_reachable[id] = await j(s, `(()=>{const h=${q(`[data-panel="${id}"] .geo3d-bang-noi-dau`)};`
        + "const b=h.closest('.geo3d-bang-noi');const r=h.getBoundingClientRect();"
        + "return [0.1,0.3,0.5,0.7,0.9].some(f=>b.contains(document.elementFromPoint(r.x+r.width*f,r.y+r.height/2)))})()");
    }
    kq.images.panels_resized = await capture(s, join(anh, "panels_resized_1100x700.png"));
    await s.setViewport(null);
    await nghi();
    o.annotations.pass = o.annotations.pass && await annDung();
    [x, y] = await tieuDe(s, "cac-buoc");
    await keo(s, x, y, -260, 140);
    o.reset = { dragged: await hop(s, "[data-panel=\"cac-buoc\"]") };
    await trustedClick(s, q("[data-panel=\"cac-buoc\"] .geo3d-bang-noi-ve"));
    await nghi();
    o.reset.after = await hop(s, "[data-panel=\"cac-buoc\"]");
    o.reset.disabled_after = await j(s, `${q("[data-panel=\"cac-buoc\"] .geo3d-bang-noi-ve")}.disabled`);
    await j(s, `(${q("[data-panel=\"cac-buoc\"] .geo3d-bang-noi-dau")}.focus(),true)`);
    await phim(s, "Escape", 27);
    o.escape_closed = !(await coBang(s, "cac-buoc"));
    [x, y] = await tieuDe(s, "dai-luong");
    await keo(s, x, y, -200, 60);
    o.reopen = { closed_at: await hop(s, "[data-panel=\"dai-luong\"]") };
    await moBang(s, "dai-luong", false);
    await moBang(s, "dai-luong", true);
    o.reopen.reopened = await hop(s, "[data-panel=\"dai-luong\"]");
    kq.panels_observation = o;
    kq.panels = assessPanelsDesktop(o);
    await dongHet(s);
    // ── Y4 bố cục (bước cuối): trung tính · xoay · đổi cỡ ──
    const f0 = await khung(s, "neutral");
    kq.images.layout_neutral = await capture(s, join(anh, "layout_neutral.png"));
    await xoayKhung(s);
    const f1 = await khung(s, "rotated");
    kq.layout_observation = await boCuc(s, DESKTOP, [f0, f1]);
    await s.setViewport({ width: 1100, height: 760 });
    await nghi();
    kq.layout_resized_observation = await boCuc(s, { width: 1100, height: 760 }, [await khung(s, "resized")]);
    kq.images.layout_resized = await capture(s, join(anh, "layout_resized_1100x760.png"));
    await s.setViewport(null);
    await nghi();
    kq.layout = assessLayout(kq.layout_observation);
    kq.layout_resized = assessLayout(kq.layout_resized_observation);

    // ── Y5 chọn thẳng trên hình ──
    const c = await cam(s);
    const khungR = await hop(s, ".geo3d-canvas");
    const cham = (await j(s, "(window.__geo3d_vertex_markers||[]).filter(m=>m.id)"))
      .map((m) => ({ id: m.id, ...chieuManHinh(c, m.center) }))
      .filter((v) => !v.behind && v.x > 40 && v.y > 40 && v.x < c.viewport_width - 40 && v.y < c.viewport_height - 40);
    const dich = cham[0];
    const ds = { target_id: dich?.id ?? null, click: {}, drag: {} };
    if (dich) {
      await bam(s, khungR.x + dich.x, khungR.y + dich.y);
      ds.click.selected = await chonId(s);
      ds.click.inspector_open = await coBang(s, "soi");
      await moBang(s, "thanh-phan", true);
      ds.click.tree_current = await j(s, "document.querySelector('.geo3d-tree [aria-current=\"true\"]')?.dataset.treeId||null");
      cay.selected_group_open = await j(s, `(()=>{let e=document.querySelector('.geo3d-tree [data-tree-id="${dich.id}"]');`
        + "if(!e)return false;for(let d=e.closest('details');d;d=d.parentElement?.closest('details'))if(!d.open)return false;return true})()");
      kq.images.direct_select = await capture(s, join(anh, "direct_select_tree.png"));
      await moBang(s, "thanh-phan", false);
      ds.drag.selected_before = await chonId(s);
      ds.drag.camera_before = await camDung(s);
      await keo(s, khungR.x + 24, khungR.y + khungR.h - 60, 140, -20);
      ds.drag.selected_after = await chonId(s);
      ds.drag.camera_after = await cam(s);
    }
    kq.direct_select_observation = ds;
    kq.direct_select = assessDirectSelect(ds);
    kq.tree_observation = cay;
    kq.tree = assessTreePanel(cay);
    await dongHet(s);

    kq.exceptions = s.consoleEvents.filter((e) => e.loai === "exception");
  } finally {
    await s.close();
    sv.close();
  }
  return kq;
}

async function runThap(ho, fixture) {
  const anh = join(ANH, ho.replaceAll("_", "-"), "low");
  const { sv, cong } = await phucVu(DIST);
  const { session: s } = await openFixture({ port: cong, viewport: THAP, fixture });
  const kq = { family: ho, viewport: "low_1366x650", images: {} };
  try {
    await pollUntil(() => j(s, "!!document.querySelector('.geo3d-canvas canvas')"), Boolean, { timeoutMs: 20000 });
    await denBuocCuoi(s, fixture.envelope.scene3d);
    const f0 = await khung(s, "neutral");
    kq.images.layout = await capture(s, join(anh, "layout_low.png"));
    kq.layout_observation = await boCuc(s, THAP, [f0]);
    kq.layout = assessLayout(kq.layout_observation);
    kq.exceptions = s.consoleEvents.filter((e) => e.loai === "exception");
  } finally {
    await s.close();
    sv.close();
  }
  return kq;
}

async function runMobile(ho, fixture) {
  const scene = fixture.envelope.scene3d;
  const anh = join(ANH, ho.replaceAll("_", "-"), "mobile");
  const { sv, cong } = await phucVu(DIST);
  const { session: s } = await openFixture({ port: cong, viewport: MOBILE, fixture });
  const kq = { family: ho, viewport: "mobile", images: {} };
  try {
    await pollUntil(() => j(s, "!!document.querySelector('.geo3d-canvas canvas')"), Boolean, { timeoutMs: 20000 });
    await denBuocCuoi(s, scene);
    const f0 = await khung(s, "neutral");
    kq.images.layout = await capture(s, join(anh, "layout_mobile.png"));
    kq.layout_observation = await boCuc(s, MOBILE, [f0]);
    kq.layout = assessLayout(kq.layout_observation);
    const o = { canvas: { before: await hopTrang(s, ".geo3d-canvas"), states: [] }, step: { before: await buoc(s), states: [] } };
    const ghi = async () => { o.canvas.states.push(await hopTrang(s, ".geo3d-canvas")); o.step.states.push(await buoc(s)); };
    for (const id of ["cac-buoc", "thanh-phan"]) { await moBang(s, id, true); await ghi(); }
    const qid = await chonDaiLuong(s);
    await ghi();
    o.quantity = { id: qid, selected: await chonId(s), inspector_open: await coBang(s, "soi") };
    o.controls = await hopTrang(s, ".geo3d-controls");
    o.panels = await quanSatBang(s, ["soi", "thanh-phan", "dai-luong", "cac-buoc"]);
    await j(s, `(${q(".geo3d-bang-noi[data-panel=\"soi\"]")}.scrollIntoView({block:'start'}),true)`);
    await nghi();
    kq.images.sheets = await capture(s, join(anh, "sheets_open.png"));
    o.collapse = { expanded_body: await j(s, `!!${q("[data-panel=\"cac-buoc\"] .geo3d-bang-noi-than")}`) };
    await trustedClick(s, q("[data-panel=\"cac-buoc\"] .geo3d-bang-noi-gon"));
    await nghi();
    o.collapse.collapsed_body = await j(s, `!!${q("[data-panel=\"cac-buoc\"] .geo3d-bang-noi-than")}`);
    await j(s, "(scrollTo(0,0),true)");
    await nghi();
    // Cử chỉ xoay bắt đầu trên ĐIỂM ẢNH CANVAS (không phải nhãn số đo/nhãn điểm đè lên — bấm nhãn là chọn, không xoay)
    const diem = await j(s, "(()=>{const k=document.querySelector('.geo3d-canvas canvas');const r=k.getBoundingClientRect();"
      + "for(const fy of [0.5,0.35,0.65,0.25,0.75])for(const fx of [0.5,0.3,0.7,0.2,0.8]){const x=r.x+r.width*fx,y=r.y+r.height*fy;"
      + "if(document.elementFromPoint(x,y)===k)return {x,y}}return null})()");
    o.orbit = { camera_before: await camDung(s), start: diem };
    if (diem) await keo(s, diem.x, diem.y, 90, 30);
    o.orbit.camera_after = await cam(s);
    kq.images.after_orbit = await capture(s, join(anh, "figure_after_orbit.png"));
    kq.panels_observation = o;
    kq.panels = assessPanelsMobile(o);
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
  for (const chay of [runDesktop, runThap, runMobile]) {
    let r;
    try {
      r = await chay(ho, fixture);
    } catch (e) {
      r = { family: ho, viewport: chay.name, run_error: String(e?.stack ?? e) };
    }
    const cong = [r.panels, r.layout, r.layout_resized, r.direct_select, r.tree].filter(Boolean);
    const pass = !r.run_error && cong.every((g) => g.pass) && (r.exceptions ?? []).length === 0;
    ket.push({ ...r, pass });
    console.log(`${ho}/${r.viewport}: ${pass ? "PASS" : "FAIL"} ${JSON.stringify(sortedUnique(cong.flatMap((g) => g.reason_codes)))}`
      + `${r.run_error ? ` RUN_ERROR ${r.run_error.split("\n")[0]}` : ""}`);
  }
}
const out = { schema_version: "w04-panels-probe/1", application_llm_calls: 0,
  commit: execFileSync("git", ["rev-parse", "HEAD"], { cwd: GOC, encoding: "utf8" }).trim(),
  pass: ket.every((r) => r.pass), runs: ket };
writeFileSync(join(RA, "W04_PANELS_PROBE.json"), `${JSON.stringify(out, null, 2)}\n`);
console.log(`W04 probe: ${ket.filter((r) => r.pass).length}/${ket.length} PASS`);
process.exit(out.pass ? 0 : 1);
