/**
 * mobile-canvas-fit (D5) — đầu dò trình duyệt THẬT cho bố cục mô phỏng trên điện thoại, 0 lượt gọi model.
 *
 * `ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL`: trên khổ hẹp canvas cao theo khung nhìn trong khi camera vừa
 * hình theo BỀ NGANG ⇒ dải trắng trên/dưới hình, và bảng mở ra nằm dưới nếp gấp. Đầu dò đo, mỗi họ × khổ:
 *   · độ lấp của hình (hộp bao các nhãn điểm) theo chiều cao/ngang canvas, dải trắng trên/dưới;
 *   · mở «Các bước dựng» / «Đại lượng»: sau khi bảng tự cuộn vào tầm nhìn, hình còn trọn trong khung nhìn không và
 *     thấy được bao nhiêu px thân bảng (đối chiếu bảng ↔ hình không mất ngữ cảnh);
 *   · mở/đóng bảng, chọn đại lượng, đổi bước: chiều cao canvas và camera KHÔNG đổi (bất biến W4);
 *   · bảng bước dài: bước đang xem luôn nằm trong vùng nhìn của thân bảng khi tua «Bước sau» tới cuối;
 *   · không cuộn ngang; sau một cú xoay, nhãn điểm còn trong canvas.
 * Phán quyết ở hàm THUẦN `assessMobileLayout` (cuối file). Ảnh theo `capture-policy.mjs` (tập duyệt chọn trước).
 *
 * Cờ: `--fixture-root <thư mục có fixtures/>` `--ra <thư mục kết quả>` `--anh <thư mục ảnh>` `--dist <build>`
 *     `--bo-qua-build` `--ho <họ1,họ2>` `--kho <portrait,landscape,…>` `--nhan <tên tệp JSON>`
 *     `--anh-che-do` `--review-set` (như mọi bộ đo).
 */
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { phucVu } from "./scene3d-orbit-gate.mjs";
import { capture, openFixture, trustedClick, trustedOrbit } from "./compiler-scene-suite.mjs";
import { datChinhSach, tomTatAnh } from "./capture-policy.mjs";
import { pollUntil, sortedUnique } from "./compiler-scene-replay-lib.mjs";

const CO = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, ds) => {
  if (x.startsWith("--")) a.push([x.slice(2), ds[i + 1]?.startsWith("--") ? true : ds[i + 1] ?? true]);
  return a;
}, []));
datChinhSach({ mode: CO["anh-che-do"], reviewSet: CO["review-set"] });
const FE = resolve(import.meta.dirname, "..");
const GOC = resolve(FE, "..");
const ROOT = resolve(String(CO["fixture-root"]));
const RA = resolve(String(CO.ra));
const ANH = resolve(String(CO.anh));
const DIST = CO.dist ? resolve(String(CO.dist)) : join(FE, "dist");
const HO = typeof CO.ho === "string" ? CO.ho.split(",") : ["triangular_pyramid", "rectangular_pyramid",
  "triangular_prism", "cuboid", "cube", "cross_section", "regular_square_pyramid", "regular_triangular_pyramid"];
/** Khổ đo: điện thoại dọc (hai cỡ), điện thoại ngang, màn thấp, desktop. `mobile` = giả lập cảm ứng DPR 2. */
const KHO = {
  portrait: { width: 390, height: 844, mobile: true },
  portrait_small: { width: 360, height: 640, mobile: true },
  landscape: { width: 844, height: 390, mobile: true },
  low: { width: 1366, height: 650, mobile: false },
  desktop: { width: 1440, height: 900, mobile: false },
};
const KHO_CHON = typeof CO.kho === "string" ? CO.kho.split(",") : Object.keys(KHO);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const j = async (s, e) => JSON.parse(await s.eval(`JSON.stringify(${e})`));
const q = (sel) => `document.querySelector(${JSON.stringify(sel)})`;
const hop = (s, sel) => j(s, `(()=>{const e=${q(sel)};if(!e)return null;`
  + "const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})()");
/** Hộp bao các NHÃN ĐIỂM đang hiện (toạ độ khung nhìn) — đại diện cho hình trên màn hình. */
const hinh = (s) => j(s, "(()=>{const ls=[...document.querySelectorAll('.geo3d-labels .geo3d-label')]"
  + ".map(e=>e.getBoundingClientRect()).filter(r=>r.width>0&&getComputedStyle(document.querySelector('.geo3d-labels')).display!=='none');"
  + "if(!ls.length)return null;const x=Math.min(...ls.map(r=>r.left)),y=Math.min(...ls.map(r=>r.top)),"
  + "X=Math.max(...ls.map(r=>r.right)),Y=Math.max(...ls.map(r=>r.bottom));return {x,y,w:X-x,h:Y-y,n:ls.length}})()");
const camera = (s) => j(s, "window.__geo3d_camera_snapshot||null");
async function camDung(s) {
  let a = await camera(s);
  for (let i = 0; i < 20; i += 1) {
    await sleep(250);
    const b = await camera(s);
    if (JSON.stringify(a) === JSON.stringify(b)) return b;
    a = b;
  }
  return a;
}
const nghi = () => sleep(500);
const vp = (s) => j(s, "({w:innerWidth,h:innerHeight,sy:scrollY})");
/** Phần thân bảng nằm trong khung nhìn (px dọc). */
const thanBangThay = (s, panel) => j(s, `(()=>{const b=document.querySelector('.geo3d-bang-noi[data-panel="${panel}"]');`
  + "if(!b)return null;const r=b.getBoundingClientRect();const t=Math.max(0,r.top),d=Math.min(innerHeight,r.bottom);"
  + "return {top:r.top,bottom:r.bottom,h:r.height,visible:Math.max(0,d-t)}})()");
const trongKhung = (r, v) => !!r && r.y >= -0.5 && r.y + r.h <= v.h + 0.5;

/** Bước đang xem có nằm trong vùng nhìn của thân bảng «Các bước dựng» (và của khung nhìn) không. */
const buocDangXemThay = (s) => j(s, "(()=>{const b=document.querySelector('.geo3d-bang-noi[data-panel=\"cac-buoc\"]');"
  + "const n=b&&b.querySelector('[aria-current=\"step\"]');if(!n)return null;const t=b.querySelector('.geo3d-bang-noi-than');"
  + "const r=n.getBoundingClientRect(),c=t.getBoundingClientRect();"
  + "return {in_panel:r.top>=c.top-0.5&&r.bottom<=c.bottom+0.5,in_viewport:r.top>=-0.5&&r.bottom<=innerHeight+0.5,"
  + "step:Number(n.dataset.geometryStep)}})()");

async function moBuoc(s) {
  if (!await j(s, "!!document.querySelector('.geo3d-bang-noi[data-panel=\"cac-buoc\"]')")) {
    await trustedClick(s, q(".geo3d-cac-buoc-mo"));
  }
  await pollUntil(() => j(s, "!!document.querySelector('[data-geometry-step]')"), Boolean, { timeoutMs: 5000 });
  await nghi();
}
async function dongBang(s, panel) {
  const sel = `.geo3d-bang-noi[data-panel="${panel}"] .geo3d-bang-noi-dong`;
  if (await j(s, `!!${q(sel)}`)) { await trustedClick(s, q(sel)); await nghi(); }
}
async function moDaiLuong(s) {
  await trustedClick(s, q('[data-mo-nhom="kham-pha"]'));
  await pollUntil(() => j(s, "[...document.querySelectorAll('.geo3d-menu-hop [role^=menuitem]')]"
    + ".some(b=>(b.textContent||'').includes('Đại lượng'))"), Boolean, { timeoutMs: 5000 }).catch(() => null);
  const co = await j(s, "!![...document.querySelectorAll('.geo3d-menu-hop [role^=menuitem]')]"
    + ".find(b=>(b.textContent||'').includes('Đại lượng'))");
  if (!co) { await trustedClick(s, q(".geo3d-ten-bai")); return false; }
  await trustedClick(s, "[...document.querySelectorAll('.geo3d-menu-hop [role^=menuitem]')]"
    + ".find(b=>(b.textContent||'').includes('Đại lượng'))");
  await pollUntil(() => j(s, "!!document.querySelector('.geo3d-dai-luong')"), Boolean, { timeoutMs: 5000 });
  await nghi();
  return true;
}

async function chay(ho, fixture, kind) {
  const kho = KHO[kind];
  const anh = join(ANH, ho.replaceAll("_", "-"), kind);
  const { sv, cong } = await phucVu(DIST);
  const { session: s } = await openFixture({ port: cong, viewport: kho, fixture });
  const o = { family: ho, kind, images: {} };
  try {
    // `openFixture` chỉ giả lập cảm ứng dưới 600 px — điện thoại ngang cũng là điện thoại.
    if (kho.mobile && kho.width >= 600) {
      await s._send("Emulation.setDeviceMetricsOverride", {
        width: kho.width, height: kho.height, deviceScaleFactor: 2, mobile: true });
    }
    await pollUntil(() => j(s, "!!document.querySelector('.geo3d-canvas canvas')"), Boolean, { timeoutMs: 20000 });
    await nghi();
    await j(s, "(scrollTo(0,0),true)");
    await camDung(s);
    o.viewport = await vp(s);
    o.layout = {
      scroll_width: await j(s, "document.documentElement.scrollWidth"),
      client_width: await j(s, "document.documentElement.clientWidth"),
      page_height: await j(s, "document.documentElement.scrollHeight"),
      top_row: await hop(s, ".geo3d-thanh"),
      tool_row: await hop(s, ".geo3d-thanh-nut"),
      float_row: await hop(s, ".geo3d-noi"),
      canvas: await hop(s, ".geo3d-canvas"),
      controls: await hop(s, ".geo3d-controls"),
      // Bảng nổi (desktop) hay trong dòng chảy (khổ hẹp) — cùng điểm gãy với CSS `.geo3d-bang-noi`.
      panels_float: await j(s, "!matchMedia('(max-width: 48rem)').matches"),
    };
    o.figure = await hinh(s);
    const c = o.layout.canvas;
    const f = o.figure;
    if (c && f) {
      o.fill = { h: f.h / c.h, w: f.w / c.w, blank_top: f.y - c.y, blank_bottom: c.y + c.h - (f.y + f.h),
        blank_left: f.x - c.x, blank_right: c.x + c.w - (f.x + f.w) };
    }
    o.camera0 = await camera(s);
    o.images.layout = await capture(s, join(anh, "layout.png"));

    // «Các bước dựng»: mở, để bảng tự cuộn vào tầm nhìn, đo hình + bảng cùng lúc.
    await moBuoc(s);
    await sleep(300);
    const v1 = await vp(s);
    o.steps_open = { viewport: v1, figure: await hinh(s), canvas: await hop(s, ".geo3d-canvas"),
      panel: await thanBangThay(s, "cac-buoc") };
    o.steps_open.figure_in_viewport = trongKhung(o.steps_open.figure, v1);
    o.images.steps_open = await capture(s, join(anh, "steps_open.png"));

    // Bảng bước dài: tua «Bước sau» tới cuối, bước đang xem phải thấy được trong thân bảng.
    await trustedClick(s, `[...document.querySelectorAll('[data-geometry-step]')][0]`);
    await nghi();
    const thay = [];
    for (let i = 0; i < 60; i += 1) {
      thay.push(await buocDangXemThay(s));
      const het = await j(s, "document.querySelector('.geo3d-controls [aria-label=\"Bước sau\"]')?.disabled!==false");
      if (het) break;
      await trustedClick(s, q('.geo3d-controls [aria-label="Bước sau"]'));
      await sleep(250);
    }
    o.step_visibility = { checked: thay.length, hidden_in_panel: thay.filter((x) => x && !x.in_panel).map((x) => x.step),
      missing: thay.filter((x) => !x).length,
      panel_scrollable: await j(s, "(()=>{const t=document.querySelector('.geo3d-bang-noi[data-panel=\"cac-buoc\"] .geo3d-bang-noi-than');"
        + "return t?t.scrollHeight>t.clientHeight+1:false})()") };
    o.images.steps_last = await capture(s, join(anh, "steps_last.png"));

    // Bất biến: chiều cao canvas + camera không đổi qua mở/đóng bảng, chọn đại lượng, đổi bước.
    const h0 = (await hop(s, ".geo3d-canvas"))?.h;
    const cam0 = await camDung(s);
    await dongBang(s, "cac-buoc");
    const coDaiLuong = await moDaiLuong(s);
    let dl = null;
    if (coDaiLuong) {
      const v2 = await vp(s);
      dl = { viewport: v2, figure: await hinh(s), panel: await thanBangThay(s, "dai-luong") };
      dl.figure_in_viewport = trongKhung(dl.figure, v2);
      o.images.quantity_open = await capture(s, join(anh, "quantity_open.png"));
      const qid = await j(s, "document.querySelector('.geo3d-dai-luong [data-quantity-id]')?.dataset.quantityId||null");
      if (qid) { await trustedClick(s, q(`.geo3d-dai-luong [data-quantity-id="${qid}"]`)); await nghi(); }
      dl.selected = qid;
      dl.detail_open = await j(s, "!!document.querySelector('.geo3d-bang-noi[data-panel=\"soi\"]')");
      await dongBang(s, "soi");
      await dongBang(s, "dai-luong");
    }
    o.quantity_open = dl;
    await trustedClick(s, q('.geo3d-controls [aria-label="Bước trước"]'));
    await nghi();
    const h1 = (await hop(s, ".geo3d-canvas"))?.h;
    const cam1 = await camDung(s);
    o.invariance = { canvas_h_before: h0, canvas_h_after: h1, canvas_same: Math.abs((h0 ?? 0) - (h1 ?? -9)) < 0.5,
      // Sai số dấu phẩy động (~1e-12, phép xoay hiển thị + giảm chấn) không phải camera đổi.
      camera_same: !!cam0?.position && !!cam1?.position
        && cam0.position.every((x, i) => Math.abs(x - cam1.position[i]) < 1e-6) };

    // Một cú xoay: nhãn điểm còn trong canvas (hình không văng khỏi khung).
    await j(s, "(scrollTo(0,0),true)");
    await nghi();
    await trustedOrbit(s, { dx: 120, dy: 40 });
    await camDung(s);
    const cr = await hop(s, ".geo3d-canvas");
    const fr = await hinh(s);
    o.after_orbit = { canvas: cr, figure: fr, inside: !!cr && !!fr && fr.x >= cr.x - 1 && fr.y >= cr.y - 1
      && fr.x + fr.w <= cr.x + cr.w + 1 && fr.y + fr.h <= cr.y + cr.h + 1 };
    o.images.after_orbit = await capture(s, join(anh, "after_orbit.png"));
    o.exceptions = s.consoleEvents.filter((e) => e.loai === "exception");
    o.result = assessMobileLayout(o);
  } finally {
    await s.close();
    sv.close();
  }
  return o;
}

/** Ngưỡng D5 (đặt TRƯỚC lượt đo «trước»): khổ hẹp, hình phải lấp ≥ 55 % chiều cao canvas trừ khi canvas đã ở sàn
 *  320 px hay hình ràng theo chiều cao (lấp ≥ 0,6 chiều ngang ⇒ không còn chỗ để gọn hơn mà không thu nhỏ hình). */
const NGUONG_D5 = { lapDocMin: 0.55, sanCanvas: 320, thanBangThayMin: 120 };

function assessMobileLayout(o) {
  const codes = [];
  if (o.layout.scroll_width > o.layout.client_width + 1) codes.push("HORIZONTAL_SCROLL");
  if (!o.invariance?.canvas_same) codes.push("CANVAS_RESIZED_BY_PANEL_OR_STEP");
  if (!o.invariance?.camera_same) codes.push("CAMERA_MOVED_BY_PANEL_OR_STEP");
  if ((o.step_visibility?.hidden_in_panel ?? []).length > 0) codes.push("CURRENT_STEP_HIDDEN_IN_PANEL");
  if (!o.after_orbit?.inside) codes.push("FIGURE_LEFT_CANVAS_AFTER_ORBIT");
  const hep = !o.layout.panels_float;
  const info = [];
  if (hep && o.fill && o.layout.canvas) {
    const tranDoc = o.fill.h < NGUONG_D5.lapDocMin && o.layout.canvas.h > NGUONG_D5.sanCanvas + 1 && o.fill.w >= 0.6;
    if (tranDoc) codes.push("D5_VERTICAL_BLANK_BAND");
    const doiChieu = o.steps_open?.figure_in_viewport && (o.steps_open?.panel?.visible ?? 0) >= NGUONG_D5.thanBangThayMin;
    if (!doiChieu) info.push(o.fill.h >= NGUONG_D5.lapDocMin ? "PANEL_BELOW_FOLD_FIGURE_FILLS_CANVAS" : "PANEL_BELOW_FOLD");
  }
  return { pass: codes.length === 0 && (o.exceptions ?? []).length === 0, reason_codes: codes, info_codes: info,
    narrow_layout: hep };
}

if (!CO["bo-qua-build"]) execFileSync("npm", ["run", "build"], { cwd: FE, stdio: "inherit", shell: true });
mkdirSync(RA, { recursive: true });
const ket = [];
for (const ho of HO) {
  const fixture = JSON.parse(readFileSync(join(ROOT, "fixtures", `${ho}_positive.json`), "utf8"));
  for (const kind of KHO_CHON) {
    let r;
    try {
      r = await chay(ho, fixture, kind);
    } catch (e) {
      r = { family: ho, kind, run_error: String(e?.stack ?? e) };
    }
    const pass = !r.run_error && r.result?.pass === true;
    ket.push({ ...r, pass });
    const fl = r.fill ? ` fill_h=${r.fill.h.toFixed(2)} canvas_h=${Math.round(r.layout.canvas.h)}` : "";
    console.log(`${ho}/${kind}: ${pass ? "PASS" : "FAIL"} ${JSON.stringify(r.result?.reason_codes ?? [])}`
      + ` ${JSON.stringify(r.result?.info_codes ?? [])}${fl}${r.run_error ? ` RUN_ERROR ${r.run_error.split("\n")[0]}` : ""}`);
  }
}
const out = { schema_version: "mobile-layout-probe/1", application_llm_calls: 0,
  commit: execFileSync("git", ["rev-parse", "HEAD"], { cwd: GOC, encoding: "utf8" }).trim(),
  dist: DIST, thresholds: NGUONG_D5, viewports: Object.fromEntries(KHO_CHON.map((k) => [k, KHO[k]])),
  reason_codes: sortedUnique(ket.flatMap((r) => r.result?.reason_codes ?? [])),
  pass: ket.every((r) => r.pass), runs: ket, capture_policy: tomTatAnh() };
writeFileSync(join(RA, String(CO.nhan ?? "MOBILE_LAYOUT_PROBE.json")), `${JSON.stringify(out, null, 2)}\n`);
console.log(`mobile layout probe: ${ket.filter((r) => r.pass).length}/${ket.length} PASS`);
process.exit(out.pass ? 0 : 1);
