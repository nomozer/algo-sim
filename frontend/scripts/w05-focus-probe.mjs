/**
 * regular-square-pyramid-w05 — đầu dò trình duyệt THẬT cho CHẾ ĐỘ TẬP TRUNG, 0 lượt gọi model.
 *
 * Thao tác qua CDP (chuột, phím, đổi cỡ, toàn màn hình) trên `dist/` phục vụ fixture đóng băng qua đúng biên mạng
 * của sản phẩm (`openFixture`, vào xưởng từ trang chủ). Phán quyết ở hàm THUẦN `assessFocusMode` của
 * `compiler-scene-replay-lib.mjs` (ca tiêm lỗi ở node-test). Mỗi họ × desktop 1440×900 · màn thấp 1366×650 · mobile
 * 390×844: không thanh trên toàn cục, không cuộn ngang, hàng trên (quay lại · tên bài · công cụ nhóm) không đè canvas,
 * thanh điều khiển trong khung nhìn (desktop/màn thấp), ba menu mở/đóng bằng chuột và bàn phím, chú giải màu trong
 * «Hiển thị», «Lưới nền» bật/tắt, «Tách khối» theo cảnh, bước + lựa chọn + góc nhìn giữ qua menu · đổi cỡ · toàn màn
 * hình, nút quay lại rời xưởng. Ảnh bố cục cho gói duyệt.
 *
 * Cờ: `--fixture-root <thư mục có fixtures/>` `--ra <thư mục kết quả>` `--anh <thư mục ảnh>` `--bo-qua-build`
 *     `--dist <thư mục build>` (mặc định `frontend/dist`) `--ho <họ1,họ2>` (mặc định bảy họ)
 */
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { phucVu } from "./scene3d-orbit-gate.mjs";
import { capture, openFixture, trustedClick } from "./compiler-scene-suite.mjs";
import { assessFocusMode, expectedGeometryTimeline, pollUntil, sortedUnique } from "./compiler-scene-replay-lib.mjs";

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
const KHO = { desktop: { width: 1440, height: 900 }, low: { width: 1366, height: 650 },
  mobile: { width: 390, height: 844 } };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

if (!CO["bo-qua-build"]) execFileSync("npm", ["run", "build"], { cwd: FE, stdio: "inherit", shell: true });
mkdirSync(RA, { recursive: true });

const j = async (s, e) => JSON.parse(await s.eval(`JSON.stringify(${e})`));
const q = (sel) => `document.querySelector(${JSON.stringify(sel)})`;
const hop = (s, sel) => j(s, `(()=>{const e=${q(sel)};if(!e)return null;`
  + "const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})()");
const nghi = () => sleep(600);
const trangThai = async (s) => ({
  step: await j(s, "(document.querySelector('.geo3d-controls .geo3d-buoc-so')?.textContent||'').trim()"),
  selected: await j(s, "window.__geo3d_selected_id||null"),
  camera: await j(s, "window.__geo3d_camera_snapshot||null"),
});
/** Chờ camera đứng yên (giảm chấn quỹ đạo) trước khi lấy mốc. */
async function camDung(s) {
  let a = await j(s, "window.__geo3d_camera_snapshot||null");
  for (let i = 0; i < 20; i += 1) {
    await sleep(250);
    const b = await j(s, "window.__geo3d_camera_snapshot||null");
    if (JSON.stringify(a) === JSON.stringify(b)) return b;
    a = b;
  }
  return a;
}
const trangThaiDung = async (s) => { await camDung(s); return trangThai(s); };
async function phim(s, key, code) {
  for (const type of ["keyDown", "keyUp"]) {
    await s._send("Input.dispatchKeyEvent", { type, key, code: key, windowsVirtualKeyCode: code });
  }
  await sleep(200);
}
const nutMenu = (khoa) => `[data-mo-nhom="${khoa}"]`;
const moMenu = (s, khoa) => j(s, `${q(nutMenu(khoa))}?.getAttribute('aria-expanded')==='true'`);
const mucMenu = (ten) => `[...document.querySelectorAll('.geo3d-menu-hop [role^=menuitem]')]`
  + `.find((b)=>(b.textContent||'').includes(${JSON.stringify(ten)}))`;
async function batMenu(s, khoa, mo) {
  if (await moMenu(s, khoa) !== mo) await trustedClick(s, q(nutMenu(khoa)));
  await pollUntil(() => moMenu(s, khoa), (x) => x === mo, { timeoutMs: 5000 });
  await sleep(150);
}
async function chonMuc(s, khoa, ten) {
  await batMenu(s, khoa, true);
  await trustedClick(s, mucMenu(ten));
  await sleep(300);
  if (await moMenu(s, khoa)) await batMenu(s, khoa, false);
}

/** Một menu: chuột mở → tiêu điểm vào mục đầu → ↓ dời tiêu điểm → Escape đóng + trả tiêu điểm → mở lại → bấm
 *  ra ngoài (tên bài) đóng. Hộp menu phải nằm trọn trong khung nhìn. */
async function doMenu(s, khoa) {
  await trustedClick(s, q(nutMenu(khoa)));
  const opened = await pollUntil(() => moMenu(s, khoa), Boolean, { timeoutMs: 5000 }).then(() => true, () => false);
  await sleep(150);
  const items = await j(s, "[...document.querySelectorAll('.geo3d-menu-hop [role^=menuitem]')].map(b=>(b.textContent||'').trim())");
  const box = await hop(s, ".geo3d-menu-hop");
  const vp = await j(s, "({w:innerWidth,h:innerHeight})");
  const inside_viewport = Boolean(box) && box.x >= -0.5 && box.y >= -0.5 && box.x + box.w <= vp.w + 0.5
    && box.y + box.h <= vp.h + 0.5;
  const dangTieuDiem = () => j(s, "(document.activeElement?.getAttribute('role')||'')+'|'+(document.activeElement?.textContent||'').trim()");
  const f0 = await dangTieuDiem();
  await phim(s, "ArrowDown", 40);
  const f1 = await dangTieuDiem();
  await phim(s, "Escape", 27);
  const escape_closed = !await moMenu(s, khoa);
  const focus_returned = await j(s, `document.activeElement===${q(nutMenu(khoa))}`);
  await batMenu(s, khoa, true);
  await trustedClick(s, q(".geo3d-ten-bai"));
  await sleep(200);
  const outside_closed = !await moMenu(s, khoa);
  if (!outside_closed) await batMenu(s, khoa, false);
  return { opened, items, box, inside_viewport, focus_in_menu: f0.startsWith("menuitem"), focus_first: f0,
    focus_after_arrow: f1, arrow_moves: f1.startsWith("menuitem") && f1 !== f0, escape_closed, focus_returned,
    outside_closed };
}

async function chay(ho, fixture, kind) {
  const scene = fixture.envelope.scene3d;
  const vpXin = KHO[kind];
  const anh = join(ANH, ho.replaceAll("_", "-"), kind);
  const { sv, cong } = await phucVu(DIST);
  const { session: s } = await openFixture({ port: cong, viewport: vpXin, fixture });
  const o = { family: ho, kind, images: {} };
  try {
    await pollUntil(() => j(s, "!!document.querySelector('.geo3d-canvas canvas')"), Boolean, { timeoutMs: 20000 });
    await nghi();
    await j(s, "(scrollTo(0,0),true)");
    await camDung(s);
    o.viewport = await j(s, "({w:innerWidth,h:innerHeight})");
    o.layout = {
      nav_bar: await j(s, "!!document.querySelector('.nav-bar')"),
      focus_root: await j(s, "!!document.querySelector('.app-root.la-tap-trung')"),
      scroll_width: await j(s, "document.documentElement.scrollWidth"),
      client_width: await j(s, "document.documentElement.clientWidth"),
      page_height: await j(s, "document.documentElement.scrollHeight"),
      back_text: await j(s, "(document.querySelector('.geo3d-quay-lai')?.textContent||'').trim()"),
      title_text: await j(s, "(document.querySelector('.geo3d-ten-bai')?.textContent||'').trim()"),
      tools: await j(s, "[...document.querySelectorAll('.geo3d-thanh-nut > button, .geo3d-thanh-nut .geo3d-menu-nut')].map(b=>(b.textContent||'').trim())"),
      top_row: await hop(s, ".geo3d-thanh"),
      canvas: await hop(s, ".geo3d-canvas"),
      controls: await hop(s, ".geo3d-controls"),
      solution_card: await j(s, "!!document.querySelector('.geo3d-loi-giai')"),
    };
    o.has_faces = scene.objects.some((x) => x.type === "solid" && (x.faces ?? []).length > 0);
    o.tach_khoi = await j(s, "[...document.querySelectorAll('.geo3d-noi-nut')].some(b=>/Tách khối|Ráp lại/.test(b.textContent||''))");
    o.images.layout = await capture(s, join(anh, "focus_layout.png"));

    // Trạng thái để giữ: một bước giữa + một đại lượng đang chọn (qua «Khám phá» → «Đại lượng»).
    const t = expectedGeometryTimeline(scene);
    const g = Math.max(0, t.length - 1);
    await trustedClick(s, q(".geo3d-cac-buoc-mo"));
    await pollUntil(() => j(s, "!!document.querySelector('[data-geometry-step]')"), Boolean, { timeoutMs: 5000 });
    await trustedClick(s, q(`[data-geometry-step="${g}"]`));
    await nghi();
    await trustedClick(s, q(".geo3d-bang-noi[data-panel=\"cac-buoc\"] .geo3d-bang-noi-dong"));
    await nghi();
    await chonMuc(s, "kham-pha", "Đại lượng");
    await pollUntil(() => j(s, "!!document.querySelector('.geo3d-dai-luong')"), Boolean, { timeoutMs: 5000 }).catch(() => null);
    const qid = await j(s, "document.querySelector('.geo3d-dai-luong [data-quantity-id]')?.dataset.quantityId||null");
    if (qid) await trustedClick(s, q(`.geo3d-dai-luong [data-quantity-id="${qid}"]`));
    await nghi();
    if (await j(s, "!!document.querySelector('.geo3d-bang-noi[data-panel=\"dai-luong\"]')")) {
      await trustedClick(s, q(".geo3d-bang-noi[data-panel=\"dai-luong\"] .geo3d-bang-noi-dong"));
      await nghi();
    }
    await j(s, "(scrollTo(0,0),true)");
    o.state = { before: await trangThaiDung(s) };

    // Ba menu: chuột + bàn phím; chú giải trong «Hiển thị»; «Lưới nền» bật/tắt.
    o.menus = {};
    for (const khoa of ["kham-pha", "hien-thi", "them"]) o.menus[khoa] = await doMenu(s, khoa);
    await batMenu(s, "hien-thi", true);
    o.legend_count = await j(s, "document.querySelectorAll('.geo3d-menu-hop .geo3d-chu-giai-muc').length");
    o.images.menu_hien_thi = await capture(s, join(anh, "menu_hien_thi.png"));
    await batMenu(s, "hien-thi", false);
    await chonMuc(s, "hien-thi", "Lưới nền");
    const luoiBat = await j(s, "window.__geo3d_grid_visible===true");
    await chonMuc(s, "hien-thi", "Lưới nền");
    o.grid = { on: luoiBat, off: await j(s, "window.__geo3d_grid_visible===true") };
    await j(s, "(scrollTo(0,0),true)");
    o.state.after_menus = await trangThaiDung(s);

    // Đổi cỡ khung (desktop → màn thấp → về; màn thấp/mobile → rộng hơn → về).
    const vpKhac = kind === "desktop" ? KHO.low : kind === "low" ? KHO.desktop : { width: 430, height: 932 };
    await s.setViewport(vpKhac);
    await nghi();
    o.resized = { viewport: await j(s, "({w:innerWidth,h:innerHeight})"),
      scroll_width: await j(s, "document.documentElement.scrollWidth"),
      client_width: await j(s, "document.documentElement.clientWidth") };
    o.images.resized = await capture(s, join(anh, "focus_resized.png"));
    await s.setViewport(vpXin);
    await nghi();
    o.state.after_resize = await trangThaiDung(s);

    // Toàn màn hình: chỉ khi trình duyệt hỗ trợ (mục vắng thì thôi). Vào, đo, ra.
    o.fullscreen = { supported: await j(s, "document.fullscreenEnabled===true") };
    if (o.fullscreen.supported && o.menus.them.items.some((x) => x.includes("Toàn màn hình"))) {
      await chonMuc(s, "them", "Toàn màn hình");
      o.fullscreen.entered = await pollUntil(() => j(s, "!!document.fullscreenElement"), Boolean, { timeoutMs: 5000 })
        .then(() => true, () => false);
      await nghi();
      o.fullscreen.state_inside = await trangThaiDung(s);
      await chonMuc(s, "them", "Thoát toàn màn hình");
      o.fullscreen.exited = await pollUntil(() => j(s, "!document.fullscreenElement"), Boolean, { timeoutMs: 5000 })
        .then(() => true, () => false);
      await nghi();
      o.state.after_fullscreen = await trangThaiDung(s);
    }

    // Quay lại: rời xưởng, thanh trên toàn cục trở lại.
    await trustedClick(s, q(".geo3d-quay-lai"));
    const roi = await pollUntil(() => j(s, "!document.querySelector('.geo3d-canvas')"), Boolean, { timeoutMs: 5000 })
      .then(() => true, () => false);
    o.back = { left_workspace: roi, nav_bar_after: await j(s, "!!document.querySelector('.nav-bar')"),
      textarea_after: await j(s, "!!document.querySelector('textarea')") };
    o.images.after_back = await capture(s, join(anh, "after_back.png"));
    o.exceptions = s.consoleEvents.filter((e) => e.loai === "exception");
    o.result = assessFocusMode(o);
  } finally {
    await s.close();
    sv.close();
  }
  return o;
}

const ket = [];
for (const ho of HO) {
  const fixture = JSON.parse(readFileSync(join(ROOT, "fixtures", `${ho}_positive.json`), "utf8"));
  for (const kind of ["desktop", "low", "mobile"]) {
    let r;
    try {
      r = await chay(ho, fixture, kind);
    } catch (e) {
      r = { family: ho, kind, run_error: String(e?.stack ?? e) };
    }
    const pass = !r.run_error && r.result?.pass === true && (r.exceptions ?? []).length === 0;
    ket.push({ ...r, pass });
    console.log(`${ho}/${kind}: ${pass ? "PASS" : "FAIL"} ${JSON.stringify(r.result?.reason_codes ?? [])}`
      + `${r.run_error ? ` RUN_ERROR ${r.run_error.split("\n")[0]}` : ""}`);
  }
}
const out = { schema_version: "w05-focus-probe/1", application_llm_calls: 0,
  commit: execFileSync("git", ["rev-parse", "HEAD"], { cwd: GOC, encoding: "utf8" }).trim(),
  reason_codes: sortedUnique(ket.flatMap((r) => r.result?.reason_codes ?? [])),
  pass: ket.every((r) => r.pass), runs: ket };
writeFileSync(join(RA, "W05_FOCUS_PROBE.json"), `${JSON.stringify(out, null, 2)}\n`);
console.log(`W05 focus probe: ${ket.filter((r) => r.pass).length}/${ket.length} PASS`);
process.exit(out.pass ? 0 : 1);
