/**
 * PLAYBACK CỦA NGƯỜI HỌC — trình duyệt thật, 0 lượt gọi model (w10).
 *
 * Khác `compiler-scene-suite.mjs`: bộ ấy CHỦ ĐỘNG chọn vật, orbit và tua bước
 * để chụp bằng chứng. Ở đây chỉ làm đúng việc một học sinh làm: mở bài, bấm
 * Phát MỘT lần, rồi nhìn. Mọi trạng thái (bước, chọn, tô sáng, ô soi, số đo,
 * vật được dựng) được ghi theo thời gian bằng một bộ ghi trong trang; phán
 * quyết là `assessPlayback` (hàm thuần, có node test).
 *
 * Sau đoạn quan sát, và TÁCH khỏi nó: orbit (timeline phải đứng yên), rồi
 * chọn một số đo và bấm Xem lại (bước, chọn, tô sáng phải về đầu).
 *
 * Cờ: `--fixture-root <thư mục có fixtures/>` `--ra <thư mục ra>`
 *     `--families a,b` `--viewports desktop,mobile` `--bo-qua-build`
 *     `--lap-orbit N` (lặp orbit N lần mỗi lượt, ghi chuyển trạng thái)
 *     `--theo-ho` (phim ghi vào `<ra>/<họ-kebab>/playback/<viewport>/`)
 */
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { sleep } from "./browser-runner.mjs";
import { kiemDistMoi, phucVu } from "./scene3d-orbit-gate.mjs";
import {
  LOP_DONG_THEO_TANG, assessPlayback, cameraMotion, danhGiaAnhXoayThuc,
  expectedCausalTiers, expectedGeometryTimeline, orbitPlanThuc, planOrbit, pollUntil,
  settleCamera, sha256File,
} from "./compiler-scene-replay-lib.mjs";
import {
  capture, jsonEval, openFixture, overlayRects, trustedClick, trustedOrbit, trustedZoomOut,
  vertexMarkerCheck,
} from "./compiler-scene-suite.mjs";
// Node ≥ 22.18 bóc kiểu TS; hai module này không import gì nên nạp thẳng được.
import { cauTrucGocNhin } from "../src/simulations/domains/geometry/scene3d-model.ts";
import { danhGiaGocNhin, datNguong, doLuoiGocNhin } from "../src/simulations/domains/geometry/scene3d-camera.ts";
const FRONTEND = fileURLToPath(new URL("..", import.meta.url));
/** Nhịp phát của CHÍNH sản phẩm — đọc từ nguồn, không chép số. */
const PLAYBACK_INTERVAL_MS = Number(/export const PLAYBACK_INTERVAL_MS = (\d+);/.exec(readFileSync(
  join(FRONTEND, "src/simulations/domains/geometry/scene3d-model.ts"), "utf-8"))[1]);
const FAMILIES = ["triangular_pyramid", "triangular_prism", "rectangular_pyramid",
  "cuboid", "cube", "cross_section", "regular_square_pyramid"];
const VIEWPORTS = { desktop: { width: 1440, height: 900 }, mobile: { width: 390, height: 844 } };
const PLAY = '[aria-label="Phát lại quá trình dựng"]';
const REPLAY = '[aria-label="Xem lại quá trình dựng"]';

const RECORDER = `(()=>{window.__w10_log=[];const t0=performance.now();
const snap=()=>{const m=/Bước\\s+(\\d+)\\/(\\d+)/.exec(document.querySelector('.geo3d-buoc-so')?.textContent||'');
const pause=document.querySelector('[aria-label="Tạm dừng"]');
return{t:Math.round(performance.now()-t0),step:m?Number(m[1])-1:null,total:m?Number(m[2]):null,
playing:!!pause,selected:window.__geo3d_selected_id||null,
highlighted:(window.__geo3d_highlighted_ids||[]).slice(),panel_open:!!document.querySelector('.geo3d-soi'),
rows:[...document.querySelectorAll('.geo3d-dai-luong [data-quantity-id]')].map(e=>({id:e.dataset.quantityId,
sec:(e.closest('section')?.getAttribute('aria-label')||'')})),
solution_card:!!document.querySelector('.geo3d-loi-giai'),dl_open:!!document.querySelector('.geo3d-dai-luong'),
rendered:(window.__geo3d_rendered_object_ids||[]).slice().sort(),
narration:(document.querySelector('.geo3d-narration')?.textContent||'').trim()}};
window.__w10_snap=snap;let prev='';
window.__w10_timer=setInterval(()=>{const s=snap();const k=JSON.stringify({...s,t:0});
if(k!==prev){window.__w10_log.push(s);prev=k}},30);return true})()`;

const CO = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, ds) => {
  if (x.startsWith("--")) a.push([x.slice(2), ds[i + 1]?.startsWith("--") ? true : ds[i + 1] ?? true]);
  return a;
}, []));
// `--dist <thư mục>`: đo một bản build khác `frontend/dist` (W05: dist đang bị một dev server giữ khi thử cục bộ).
const DIST = CO.dist ? resolve(String(CO.dist)) : join(FRONTEND, "dist");

/* W05 · D/E: «Đại lượng» là mục của menu «Khám phá» và là nơi DUY NHẤT liệt kê đại lượng theo bước (thẻ lời giải đã
   gỡ). Mở/đóng như người học — bấm nút menu rồi bấm mục; mục vắng (chưa có đại lượng ở bước này) ⇒ đóng menu, trả false. */
const MENU_KP = "document.querySelector('[data-mo-nhom=\"kham-pha\"]')";
const MUC_DL = "[...document.querySelectorAll('.geo3d-menu-hop [role^=menuitem]')].find((b)=>(b.textContent||'').includes('Đại lượng'))";
async function doiNganDaiLuong(session) {
  await trustedClick(session, MENU_KP);
  await sleep(200);
  const co = await session.eval(`!!(${MUC_DL})`);
  await trustedClick(session, co ? MUC_DL : MENU_KP);
  await sleep(250);
  return co;
}

async function observe(session) {
  return jsonEval(session, "window.__w10_snap()");
}

/** Số đo góc nhìn của camera THẬT (hàng z của ma trận nhìn = hướng tâm→camera),
 *  bằng CHÍNH bộ đo của sản phẩm — không một định nghĩa thứ hai. */
function chatLuongGocNhin(scene, snap, overlays = []) {
  const { diem, canh, mat } = cauTrucGocNhin(scene.objects);
  const m = snap.view_matrix_column_major;
  const huong = [m[2], m[6], m[10]];
  const q = danhGiaGocNhin(diem, canh, mat, huong);
  const { tran } = doLuoiGocNhin(diem, canh, mat);
  // `non_degenerate`: cổng ảnh xoay w11 trên camera THẬT (đỉnh khối, lớp phủ).
  return { direction: huong, ...q, pass: canh.length === 0 || datNguong(q, tran),
    non_degenerate: danhGiaAnhXoayThuc(scene, snap, overlays) };
}


const EDGE_SETS = "({hidden:window.__geo3d_hidden_edge_ids||[],mixed:window.__geo3d_mixed_edge_ids||[],"
  + "camera:window.__geo3d_camera_snapshot||null})";

/** Orbit lặp lại N lần, mỗi lần từ khung mặc định: sẵn sàng theo ĐIỀU KIỆN
 *  (camera đứng yên → cử chỉ → tập khuất sản phẩm đổi), không theo giờ đoán. */
async function orbitLap(session, scene, n) {
  const ket = [];
  let macDinh = null;   // camera sau "Xem lại toàn hình" ở lượt đầu = khung trung tính
  for (let i = 0; i < n; i++) {
    const t0 = Date.now();
    const chuyen = [];
    const moc = (state, extra = {}) => chuyen.push({ t_ms: Date.now() - t0, state, ...extra });
    if (!await trustedClick(session,
      "[...document.querySelectorAll('button')].find(e=>e.textContent.includes('Xem lại toàn hình'))")) {
      moc("TIMEOUT", { reason: "RESET_BUTTON_NOT_CLICKABLE" });
      ket.push({ lap: i, pass: false, transitions: chuyen });
      continue;
    }
    let truoc;
    try {
      // Dung sai của lib (damping trôi ULP mãi — "đứng yên" không thể là trùng byte).
      await settleCamera(() => jsonEval(session, "({snapshot:window.__geo3d_camera_snapshot||null,"
        + "frame_count:(window.__geo3d_occlusion_performance||{}).frame_count||0})"), { timeoutMs: 8_000 });
      truoc = await jsonEval(session, EDGE_SETS);
      moc("CAMERA_SETTLED");
      macDinh ??= truoc.camera;
      const lech = cameraMotion(macDinh, truoc.camera);
      moc("RESET_VS_DEFAULT", { motion: lech });
      if (!(lech <= 1e-6)) {
        ket.push({ lap: i, pass: false, transitions: chuyen, reason: "RESET_NOT_AT_DEFAULT_VIEW" });
        continue;
      }
    } catch (error) {
      moc("TIMEOUT", { reason: `CAMERA_NOT_SETTLED:${String(error).slice(0, 300)}` });
      ket.push({ lap: i, pass: false, transitions: chuyen });
      continue;
    }
    const m = truoc.camera.view_matrix_column_major;
    const plan = planOrbit(scene, [m[2], m[6], m[10]]);
    moc("PLANNED", { offset_deg: plan?.offset_deg ?? null });
    if (!plan) { ket.push({ lap: i, pass: false, transitions: chuyen, reason: "NO_QUALIFYING_ORBIT" }); continue; }
    const cao = await session.eval("document.querySelector('.geo3d-canvas canvas').clientHeight");
    await trustedOrbit(session, { dx: Math.round((-plan.offset_deg / 360) * cao), dy: 0 });
    moc("GESTURE_SENT");
    try {
      await pollUntil(async () => jsonEval(session, EDGE_SETS),
        (o) => JSON.stringify([o.hidden, o.mixed]) !== JSON.stringify([truoc.hidden, truoc.mixed]),
        { timeoutMs: 4_000, intervalMs: 100 });
      moc("VISIBILITY_CHANGED");
      ket.push({ lap: i, pass: true, transitions: chuyen });
    } catch (error) {
      moc("TIMEOUT", { reason: `VISIBILITY_UNCHANGED:${String(error).slice(0, 300)}` });
      ket.push({ lap: i, pass: false, transitions: chuyen });
    }
  }
  return ket;
}

async function runOne({ port, family, viewportId, fixture, outDir, lapOrbit = 0 }) {
  const viewport = { id: viewportId, ...VIEWPORTS[viewportId] };
  const { session } = await openFixture({ port, viewport, fixture });
  const scene = fixture.envelope.scene3d;
  // W12: thanh bước đi qua BƯỚC DỰNG (oracle độc lập đọc snapshot formation).
  const total = expectedGeometryTimeline(scene).length;
  const film = [];
  try {
    await pollUntil(() => session.eval("!!document.querySelector('.geo3d-canvas canvas')"), Boolean);
    await pollUntil(() => session.eval("!!document.querySelector('[aria-label=\"Phát lại quá trình dựng\"]')"), Boolean);
    // W05: mở «Đại lượng» TRƯỚC khi phát (nếu bước 0 đã có đại lượng) — bảng nổi, không đụng bước hay camera; nhờ
    // nó mỗi mẫu của đoạn phát đọc được tập đại lượng của bước đang hiện.
    await doiNganDaiLuong(session);
    await session.eval(RECORDER);
    const start = await observe(session);
    film.push({ step: start.step, ...await capture(session, join(outDir, `step-${String(start.step).padStart(2, "0")}.png`)) });

    // ── ĐOẠN QUAN SÁT: một lần bấm Phát, không gì khác ────────────────────
    if (!await trustedClick(session, `document.querySelector('${PLAY}')`)) throw new Error("PLAY_NOT_CLICKABLE");
    const deadline = Date.now() + (total + 3) * PLAYBACK_INTERVAL_MS;
    let seen = start.step;
    let reachedFinal = null;
    while (Date.now() < deadline) {
      const now = await observe(session);
      if (now.step !== seen) {
        seen = now.step;
        await sleep(250);
        film.push({ step: seen, ...await capture(session, join(outDir, `step-${String(seen).padStart(2, "0")}.png`)) });
      }
      if (now.step === total - 1 && !now.playing && reachedFinal === null) reachedFinal = Date.now();
      if (reachedFinal !== null && Date.now() - reachedFinal > 2.5 * PLAYBACK_INTERVAL_MS) break;
      await sleep(100);
    }
    // Bước cuối phải quan sát được: bảng chưa mở (bước 0 chưa có đại lượng — thiết diện) thì mở ở đây, SAU đoạn phát.
    if (!await session.eval("!!document.querySelector('.geo3d-dai-luong')")) await doiNganDaiLuong(session);
    await session.eval("window.__w10_log.push(window.__w10_snap())");
    const samples = await jsonEval(session, "window.__w10_log");
    // Đóng lại sau khi đã chụp mẫu: các phép đo xoay/causal phía sau đo trên khung không có bảng nổi (như W4).
    if (await session.eval("!!document.querySelector('.geo3d-dai-luong')")) await doiNganDaiLuong(session);
    const states = {};
    const chup = async (ten) => {
      const snap = await jsonEval(session, "window.__geo3d_camera_snapshot||null");
      states[ten] = { ...await capture(session, join(outDir, `${ten}.png`)), ...await observe(session),
        dimmed_labels: await session.eval("document.querySelectorAll('.geo3d-label.la-diu').length"),
        // W05 · E: vai trò đọc ở mục bảng «Đại lượng» (thẻ lời giải đã gỡ).
        dimmed_readout: await session.eval("document.querySelectorAll('.geo3d-dai-luong .geo3d-tree-item.la-diu').length"),
        // nhãn điểm: dịu ⇔ nằm ngoài tập tô sáng; số đo: lớp của từng dòng (w11:
        // đích / dữ kiện số / trung gian số / ngoài chuỗi)
        label_tiers: await jsonEval(session, "[...document.querySelectorAll('.geo3d-label')]"
          + ".map(e=>({id:e.dataset.id,dimmed:e.classList.contains('la-diu')}))"),
        // W12: dòng của BẢNG LỜI GIẢI theo id, cùng lớp vai trò của nó.
        readout_tiers: await jsonEval(session, "[...document.querySelectorAll('.geo3d-dai-luong [data-quantity-id]')]"
          + ".map(e=>({id:e.dataset.quantityId,classes:[...e.classList].filter(c=>c.startsWith('la-'))}))"),
        causal_tiers: await jsonEval(session, "window.__geo3d_causal_tiers||null"),
        vertex_marker_px: await vertexMarkerCheck(session),
        view: snap ? chatLuongGocNhin(scene, snap, await overlayRects(session)) : null };
    };
    await chup("neutral_final");

    // ── SAU quan sát: orbit không được đụng timeline ─────────────────────
    // w11: ứng viên HOẠCH ĐỊNH (cổng không suy biến + đổi tập khuất dự đoán);
    // ảnh chỉ nhận khi camera THẬT đạt cổng — trượt ⇒ về khung mặc định, thử
    // ứng viên sau. OrbitControls: Δφ = 2π·dx / chiều cao, kéo phải ⇒ phương vị GIẢM.
    const orbitBefore = await observe(session);
    // Cùng bộ hoạch định với suite: chấm trước trên camera mô phỏng (xoay quanh
    // Z qua tâm quỹ đạo + lùi nấc), chỉ gửi cử chỉ cho ứng viên đạt cổng.
    const cam0 = await jsonEval(session, "window.__geo3d_camera_snapshot||null");
    const tam0 = await jsonEval(session, "window.__geo3d_camera_target||null");
    const ungVien = cam0 && tam0 ? orbitPlanThuc(scene, cam0, tam0, await overlayRects(session)) : [];
    const thuXoay = [];
    for (const [i, c] of ungVien.entries()) {
      if (i > 0) {
        await trustedClick(session,
          "[...document.querySelectorAll('button')].find(e=>e.textContent.includes('Xem lại toàn hình'))");
        await sleep(900);
      }
      await trustedOrbit(session, { dx: c.dx, dy: 0 });
      await sleep(1500);
      await trustedZoomOut(session, c.zoom_out_notches);
      await sleep(1200);
      const snap = await jsonEval(session, "window.__geo3d_camera_snapshot||null");
      const gate = snap ? danhGiaAnhXoayThuc(scene, snap, await overlayRects(session)) : null;
      thuXoay.push({ offset_deg: c.offset_deg, zoom_out_notches: c.zoom_out_notches, pass: Boolean(gate?.pass),
        failures: gate?.failures ?? ["NO_CAMERA"] });
      if (gate?.pass) break;
    }
    states.orbit_plan = { candidates: ungVien.map((c) => [c.offset_deg, c.zoom_out_notches]), attempts: thuXoay };
    const orbitAfter = await observe(session);
    await chup("rotated_neutral");

    // ── Causal: CHỈ sau cú bấm của người dùng; đóng ô soi ⇒ trung tính ───
    // W12: đích causal là đáp số. regular-square-pyramid-w01 (ROADMAP §0.1-1/2): card Kết quả ẩn khi lời giải
    // thu gọn — người học chọn đáp số qua ngăn «Đại lượng» (chip mở ngăn, chọn thì ngăn tự đóng).
    // W05 · D: «Đại lượng» là mục của menu «Khám phá» — mở menu rồi bấm mục (một cú bấm mỗi bước, như người học).
    const KET_QUA = "[...document.querySelectorAll('.geo3d-dai-luong section[aria-label=\"Kết quả\"] [data-quantity-id]')].at(-1)";
    const doiNgan = () => doiNganDaiLuong(session);
    if (!await session.eval("!!document.querySelector('.geo3d-dai-luong')")) await doiNgan();
    const rows = await session.eval(`(${KET_QUA}) ? 1 : 0`);
    if (rows === 0 && await session.eval("!!document.querySelector('.geo3d-dai-luong')")) await doiNgan();
    const causal = { restored: null };
    if (rows > 0) {
      await trustedClick(session, KET_QUA);
      await sleep(400);
      await chup("causal_selected");
      await trustedClick(session, "document.querySelector('[aria-label=\"Bỏ chọn\"]')");
      await sleep(400);
      await chup("neutral_restored");
      const r = states.neutral_restored;
      causal.restored = r.selected === null && !r.panel_open && r.highlighted.length === 0
        && r.dimmed_labels === 0 && r.dimmed_readout === 0 && r.step === orbitAfter.step;
    }
    // Lặp orbit ở trạng thái trung tính ("Xem lại toàn hình" cũng bỏ chọn).
    const orbitRepeat = lapOrbit > 0 ? await orbitLap(session, scene, lapOrbit) : null;
    if (rows > 0) {
      if (!await session.eval("!!document.querySelector('.geo3d-dai-luong')")) await doiNgan();
      await trustedClick(session, KET_QUA);
      await sleep(400);
    }
    const beforeReplay = await observe(session);
    const hasReplay = await session.eval(`!!document.querySelector('${REPLAY}')`);
    let replay = { control_present: hasReplay, selected_before: beforeReplay.selected, ...beforeReplay };
    if (hasReplay) {
      await trustedClick(session, `document.querySelector('${REPLAY}')`);
      await sleep(200);
      const after = await observe(session);
      replay = { control_present: true, selected_before: beforeReplay.selected, step: after.step,
        selected: after.selected, highlighted: after.highlighted, playing: after.playing };
      const pause = '[aria-label="Tạm dừng"]';
      if (await session.eval(`!!document.querySelector('${pause}')`)) {
        await trustedClick(session, `document.querySelector('${pause}')`);
      }
    }
    const verdict = assessPlayback({
      samples, scene, total, intervalMs: PLAYBACK_INTERVAL_MS,
      replay: hasReplay ? replay : { step: beforeReplay.step, selected: beforeReplay.selected,
        highlighted: beforeReplay.highlighted },
      orbit: { before: orbitBefore, after: orbitAfter },
    });
    const uncaught = session.consoleEvents.filter((event) => event.loai === "exception");
    verdict.checks.no_uncaught_exception = { pass: uncaught.length === 0, details: uncaught };
    const c = states.causal_selected;
    // w11 → W12: tầng kỳ vọng tính ĐỘC LẬP từ cảnh; từng dòng của bảng lời giải
    // (theo id) mang đúng lớp tầng — ngoài chuỗi ⇒ `la-diu`.
    const tangKyVong = c?.selected ? expectedCausalTiers(scene, c.selected) : null;
    const lopDung = (row) => {
      const t = tangKyVong?.[row.id];
      const lop = t ? LOP_DONG_THEO_TANG[t] : "la-diu";
      return row.classes.length === 1 && row.classes[0] === lop;
    };
    verdict.checks.causal_layers_dim_outside = { pass: !c || (c.selected !== null && c.panel_open
      && c.label_tiers.every((l) => l.dimmed === !c.highlighted.includes(l.id))
      && JSON.stringify(c.causal_tiers, Object.keys(c.causal_tiers ?? {}).sort())
        === JSON.stringify(tangKyVong, Object.keys(tangKyVong ?? {}).sort())
      && c.readout_tiers.every(lopDung)),
    details: c ? { selected: c.selected, label_tiers: c.label_tiers, readout_tiers: c.readout_tiers,
      causal_tiers: c.causal_tiers, expected_tiers: tangKyVong } : null };
    verdict.checks.close_panel_restores_neutral = { pass: causal.restored !== false, details: causal };
    // Khung mặc định: đủ ngưỡng góc nhìn. Ảnh đã xoay: cổng KHÔNG SUY BIẾN (w11).
    verdict.checks.neutral_final_view_quality = { pass: states.neutral_final?.view?.pass === true,
      details: states.neutral_final?.view };
    verdict.checks.rotated_neutral_non_degenerate = {
      pass: states.rotated_neutral?.view?.non_degenerate?.pass === true,
      details: { view: states.rotated_neutral?.view, plan: states.orbit_plan } };
    verdict.checks.vertex_marker_px = { pass: states.neutral_final?.vertex_marker_px?.pass === true,
      details: states.neutral_final?.vertex_marker_px };
    if (orbitRepeat) {
      verdict.checks.orbit_repeatable = { pass: orbitRepeat.every((a) => a.pass), details: orbitRepeat };
    }
    verdict.pass = Object.values(verdict.checks).every((x) => x.pass);
    return { family, viewport: viewportId, total, samples, film, states, replay,
      orbit: { before: orbitBefore, after: orbitAfter }, ...verdict };
  } finally {
    await session.close();
  }
}

export async function runPlaybackCheck({ fixtureRoot, outDir, families = FAMILIES,
  viewports = Object.keys(VIEWPORTS), skipBuild = false, lapOrbit = 0, byFamily = false }) {
  if (!skipBuild) {
    execFileSync("npm", ["run", "build"], { cwd: FRONTEND, stdio: "inherit", shell: true, timeout: 600_000 });
    kiemDistMoi();
  }
  const out = resolve(outDir);
  mkdirSync(out, { recursive: true });
  const { sv, cong } = await phucVu(DIST);
  const report = {
    schema_version: "learner-playback-evidence/1",
    measured_at: new Date().toISOString(),
    measurement_commit_sha: execFileSync("git", ["rev-parse", "HEAD"], { cwd: FRONTEND, encoding: "utf-8" }).trim(),
    playback_interval_ms: PLAYBACK_INTERVAL_MS,
    orbit_repeat_per_run: lapOrbit,
    application_llm_calls: 0,
    runs: [],
  };
  try {
    for (const family of families) {
      const fixture = JSON.parse(readFileSync(join(fixtureRoot, "fixtures", `${family}_positive.json`), "utf-8"));
      for (const viewportId of viewports) {
        // `--theo-ho` (w11): phim playback nằm trong thư mục của họ, cạnh sheet.
        const outDir = byFamily ? join(out, family.replaceAll("_", "-"), "playback", viewportId)
          : join(out, "filmstrip", family, viewportId);
        const result = await runOne({ port: cong, family, viewportId, fixture, lapOrbit, outDir });
        for (const item of result.film) item.path = item.path.replaceAll("\\", "/");
        report.runs.push(result);
        const failed = Object.entries(result.checks).filter(([, c]) => !c.pass).map(([k]) => k);
        console.log(`${family}/${viewportId}: ${result.pass ? "PASS" : `FAIL ${failed.join(",")}`}`);
      }
    }
  } finally {
    sv.close();
  }
  report.pass = report.runs.every((run) => run.pass);
  writeFileSync(join(out, "PLAYBACK_EVIDENCE.json"), JSON.stringify(report, null, 2), "utf-8");
  console.log(`Wrote ${join(out, "PLAYBACK_EVIDENCE.json")}: ${report.pass ? "PASS" : "FAIL"} ${sha256File(join(out, "PLAYBACK_EVIDENCE.json")).slice(0, 12)}`);
  return report;
}

if (import.meta.filename === process.argv[1]) {
  const report = await runPlaybackCheck({
    fixtureRoot: resolve(String(CO["fixture-root"])),
    outDir: resolve(String(CO.ra)),
    families: CO.families ? String(CO.families).split(",") : undefined,
    viewports: CO.viewports ? String(CO.viewports).split(",") : undefined,
    skipBuild: Boolean(CO["bo-qua-build"]),
    lapOrbit: CO["lap-orbit"] ? Number(CO["lap-orbit"]) : 0,
    byFamily: Boolean(CO["theo-ho"]),
  });
  process.exit(report.pass ? 0 : 1);
}
