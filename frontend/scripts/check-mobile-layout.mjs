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
 * phone-landscape-layout thêm (đặt trước lượt đo «trước»): ba nút phát + thanh trượt + «Các bước dựng» nằm trọn trong
 * khung nhìn lúc mở bài; tua bước không cuộn trang; nhãn điểm/số đo trong canvas ở bước cuối; «Xem lại toàn hình» trả
 * đúng góc nhìn ban đầu; «Các bước dựng»/«Đại lượng»/«Đề bài» mở từ đầu trang vẫn giữ hình (≥ 50 %), điều khiển, đầu
 * bảng, không cuộn ngang, đóng thì hình về; xoay máy dọc ↔ ngang giữ bước, lựa chọn, camera và điều khiển.
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
  landscape_small: { width: 667, height: 375, mobile: true },
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

/* ── phone-landscape-layout: kiểm thêm, đặt TRƯỚC lượt đo «trước» ─────────────────────────────────────────────── */

/** Bộ điều khiển dựng hình: ba nút phát, thanh trượt, nút «Các bước dựng» — mỗi cái nằm TRỌN trong khung nhìn? */
const dieuKhienThay = (s) => j(s, "(()=>{const t=document.querySelector('.geo3d-controls');if(!t)return null;"
  + "const ds=[...t.querySelectorAll('button'),t.querySelector('input[type=range]')].filter(Boolean);"
  + "const o=ds.map(e=>{const r=e.getBoundingClientRect();return {name:e.getAttribute('aria-label')||e.textContent.trim()||e.type,"
  + "top:r.top,bottom:r.bottom,left:r.left,right:r.right,inside:r.top>=-0.5&&r.bottom<=innerHeight+0.5&&r.left>=-0.5&&r.right<=innerWidth+0.5}});"
  + "return {all_inside:o.every(x=>x.inside),items:o}})()");
/** Phần hình (hộp nhãn điểm) nằm trong khung nhìn, theo chiều dọc. */
const phanHinhThay = (f, v) => (!f ? 0 : Math.max(0, Math.min(v.h, f.y + f.h) - Math.max(0, f.y)) / Math.max(1, f.h));
/** Nhãn điểm + nhãn số đo đang hiện nằm trong canvas (toạ độ của chính canvas). */
const nhanTrongCanvas = (s) => j(s, "(()=>{const c=document.querySelector('.geo3d-canvas');const w=c.clientWidth,h=c.clientHeight;"
  + "const p=(window.__geo3d_point_label_boxes||[]).map(b=>b.box||b),a=(window.__geo3d_annotation_boxes||[]).map(b=>b.box||b);"
  + "const ra=(b)=>b&&(b.x<-1||b.y<-1||b.x+b.w>w+1||b.y+b.h>h+1);"
  + "return {points:p.length,annotations:a.length,points_out:p.filter(ra).length,annotations_out:a.filter(ra).length}})()");
const capCam = (c) => c?.position ?? null;
const cungCam = (a, b) => !!a && !!b && a.every((x, i) => Math.abs(x - b[i]) < 1e-6);
const trangThaiChon = async (s) => ({
  step: await j(s, "(document.querySelector('.geo3d-controls .geo3d-buoc-so')?.textContent||'').trim()"),
  selected: await j(s, "window.__geo3d_selected_id||null"),
  camera: capCam(await camDung(s)),
});
const nutBang = { "cac-buoc": ".geo3d-cac-buoc-mo", de: '[data-mo-bang="de"]' };

/** Mở một bảng từ đầu trang (để bảng tự cuộn như người học thấy), đo: hình còn bao nhiêu, điều khiển còn trọn
 *  không, đầu bảng (nút đóng) thấy không, cuộn ngang; rồi đóng và đo lại hình. */
async function doBang(s, panel) {
  await j(s, "(scrollTo(0,0),true)");
  await nghi();
  if (panel === "dai-luong") { if (!await moDaiLuong(s)) return null; } else {
    if (!await j(s, `!!${q(nutBang[panel])}`)) return null;
    await trustedClick(s, q(nutBang[panel]));
    await pollUntil(() => j(s, `!!document.querySelector('.geo3d-bang-noi[data-panel="${panel}"]')`), Boolean, { timeoutMs: 5000 });
    await nghi();
  }
  const v = await vp(s);
  const f = await hinh(s);
  const o = { viewport: v, figure_visible: phanHinhThay(f, v), controls: await dieuKhienThay(s),
    header_visible: await j(s, `(()=>{const d=document.querySelector('.geo3d-bang-noi[data-panel="${panel}"] .geo3d-bang-noi-dong');`
      + "if(!d)return false;const r=d.getBoundingClientRect();return r.top>=-0.5&&r.bottom<=innerHeight+0.5})()"),
    panel: await thanBangThay(s, panel),
    horizontal_scroll: await j(s, "document.documentElement.scrollWidth>document.documentElement.clientWidth+1") };
  await dongBang(s, panel);
  const v2 = await vp(s);
  o.after_close_figure_visible = phanHinhThay(await hinh(s), v2);
  o.after_close_controls_inside = (await dieuKhienThay(s))?.all_inside ?? false;
  return o;
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
      // Bảng nổi hay trong dòng chảy — ĐỌC từ CSS thật (một `.geo3d-bang-noi` tạm trong trình phát), không đoán điểm gãy.
      panels_float: await j(s, "(()=>{const t=document.createElement('section');t.className='geo3d-bang-noi';"
        + "document.querySelector('.geo3d-player').appendChild(t);const p=getComputedStyle(t).position;t.remove();return p==='absolute'})()"),
    };
    o.controls_access = await dieuKhienThay(s);
    // Thêm SAU lượt «trước» (phone-landscape-layout): «Tách khối» / «Xem lại toàn hình» — đường thoát khi lạc góc nhìn.
    o.view_buttons = await j(s, "[...document.querySelectorAll('.geo3d-noi-nut')].map(b=>{const r=b.getBoundingClientRect();"
      + "const c=document.querySelector('.geo3d-canvas').getBoundingClientRect();"
      + "return {name:b.textContent.trim(),inside:r.top>=-0.5&&r.bottom<=innerHeight+0.5&&r.left>=-0.5&&r.right<=innerWidth+0.5,"
      + "over_canvas:r.left<c.right&&c.left<r.right&&r.top<c.bottom&&c.top<r.bottom}})");
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
    const cuonTrang = [];
    const nutSau = '.geo3d-controls [aria-label="Bước sau"]';
    for (let i = 0; i < 60; i += 1) {
      thay.push(await buocDangXemThay(s));
      const het = await j(s, `document.querySelector('${nutSau}')?.disabled!==false`);
      if (het) break;
      // Trang chỉ được coi là "bị cuộn bởi bước" khi nút đã thấy rõ trước cú bấm (bộ đo không tự cuộn).
      const nut = await j(s, `(()=>{const r=document.querySelector('${nutSau}').getBoundingClientRect();`
        + "return r.top>=0&&r.bottom<=innerHeight})()");
      const y0 = (await vp(s)).sy;
      await trustedClick(s, q(nutSau));
      await sleep(250);
      if (nut) cuonTrang.push(Math.abs((await vp(s)).sy - y0));
    }
    o.step_visibility = { checked: thay.length, hidden_in_panel: thay.filter((x) => x && !x.in_panel).map((x) => x.step),
      missing: thay.filter((x) => !x).length, page_scroll_max_px: Math.max(0, ...cuonTrang), page_scroll_samples: cuonTrang.length,
      panel_scrollable: await j(s, "(()=>{const t=document.querySelector('.geo3d-bang-noi[data-panel=\"cac-buoc\"] .geo3d-bang-noi-than');"
        + "return t?t.scrollHeight>t.clientHeight+1:false})()") };
    o.images.steps_last = await capture(s, join(anh, "steps_last.png"));
    o.labels_last_step = await nhanTrongCanvas(s);

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

    // «Xem lại toàn hình» khôi phục góc nhìn ban đầu (đường thoát khi nhãn rời khung sau cú xoay).
    await trustedClick(s, "[...document.querySelectorAll('.geo3d-noi-nut')].find(b=>(b.textContent||'').includes('Xem lại toàn hình'))");
    await nghi();
    const camVe = capCam(await camDung(s));
    const crv = await hop(s, ".geo3d-canvas");
    const frv = await hinh(s);
    o.images.after_overview = await capture(s, join(anh, "after_overview.png"));
    o.overview = { restored_camera: cungCam(capCam(o.camera0), camVe), inside: !!crv && !!frv && frv.x >= crv.x - 1
      && frv.y >= crv.y - 1 && frv.x + frv.w <= crv.x + crv.w + 1 && frv.y + frv.h <= crv.y + crv.h + 1 };

    // Ba bảng thông tin từ đầu trang: «Các bước dựng», «Đại lượng», «Đề bài».
    o.panels = {};
    for (const p of ["cac-buoc", "dai-luong", "de"]) o.panels[p] = await doBang(s, p);

    // Xoay điện thoại (dọc ↔ ngang) giữa chừng: bước, lựa chọn, camera giữ nguyên; điều khiển vẫn trong khung.
    if (kho.mobile) {
      await j(s, "(scrollTo(0,0),true)");
      if (await moDaiLuong(s)) {
        const qid = await j(s, "document.querySelector('.geo3d-dai-luong [data-quantity-id]')?.dataset.quantityId||null");
        if (qid) { await trustedClick(s, q(`.geo3d-dai-luong [data-quantity-id="${qid}"]`)); await nghi(); }
        await dongBang(s, "dai-luong");
      }
      const truoc = await trangThaiChon(s);
      const xoayKho = async (w, h) => {
        await s._send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 2, mobile: true });
        await nghi();
        await nghi();
      };
      await xoayKho(kho.height, kho.width);
      await j(s, "(scrollTo(0,0),true)");
      await nghi();
      const giua = await trangThaiChon(s);
      const giuaDk = await dieuKhienThay(s);
      const giuaNgang = await j(s, "document.documentElement.scrollWidth>document.documentElement.clientWidth+1");
      o.images.rotated = await capture(s, join(anh, "rotated.png"));
      await xoayKho(kho.width, kho.height);
      const sau = await trangThaiChon(s);
      o.rotation = { before: truoc, rotated: giua, after: sau, rotated_controls_inside: giuaDk?.all_inside ?? false,
        rotated_horizontal_scroll: giuaNgang,
        state_kept: truoc.step === giua.step && giua.step === sau.step && truoc.selected === giua.selected
          && giua.selected === sau.selected && cungCam(truoc.camera, giua.camera) && cungCam(giua.camera, sau.camera) };
    }
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
  // phone-landscape-layout (đặt trước lượt đo «trước»): điều khiển, cuộn trang, nhãn, khôi phục góc nhìn, ba bảng, xoay máy.
  if (!o.controls_access?.all_inside) codes.push("CONTROLS_OFFSCREEN");
  if ((o.view_buttons ?? []).some((b) => !b.inside)) codes.push("VIEW_BUTTONS_OFFSCREEN");
  if ((o.step_visibility?.page_scroll_max_px ?? 0) > 1) codes.push("PAGE_SCROLLED_BY_STEP");
  if ((o.labels_last_step?.points_out ?? 0) + (o.labels_last_step?.annotations_out ?? 0) > 0) {
    codes.push("LABEL_OUTSIDE_CANVAS_LAST_STEP");
  }
  if (!(o.overview?.restored_camera && o.overview?.inside)) codes.push("OVERVIEW_DOES_NOT_RESTORE");
  for (const [p, b] of Object.entries(o.panels ?? {})) {
    if (!b) continue;
    if (b.figure_visible < 0.5) codes.push(`PANEL_LOSES_FIGURE:${p}`);
    if (!b.controls?.all_inside) codes.push(`PANEL_LOSES_CONTROLS:${p}`);
    if (!b.header_visible) codes.push(`PANEL_HEADER_HIDDEN:${p}`);
    if (b.horizontal_scroll) codes.push(`HORIZONTAL_SCROLL_WITH_PANEL:${p}`);
    if (b.after_close_figure_visible < 0.5) codes.push(`FIGURE_NOT_BACK_AFTER_CLOSE:${p}`);
  }
  if (o.rotation) {
    if (!o.rotation.state_kept) codes.push("ROTATION_STATE_LOST");
    if (!o.rotation.rotated_controls_inside) codes.push("ROTATED_CONTROLS_OFFSCREEN");
    if (o.rotation.rotated_horizontal_scroll) codes.push("ROTATED_HORIZONTAL_SCROLL");
  }
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
