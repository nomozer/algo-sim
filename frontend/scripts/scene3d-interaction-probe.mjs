/**
 * scene3d-interaction-probe.mjs — ĐO ĐỘ MƯỢT KHI XOAY, trên bản dựng sản phẩm.
 *
 * ─── VÌ SAO ĐO Ở TẦNG WEBGL ──────────────────────────────────────────────
 *
 * Camera, `OrbitControls`, mesh và vật liệu đều là **renderer-owned** — nằm
 * trong closure của `Scene3DWorkspace`, không có đường nào từ ngoài chạm tới.
 * Sửa mã sản phẩm để gắn móc đo là đổi chính thứ đang đo, nên bộ đo này bám
 * vào ba biên mà trang KHÔNG che được:
 *
 *   ① `requestAnimationFrame` → nhịp khung hình thật.
 *   ② `HTMLCanvasElement.getContext` → giữ lại ngữ cảnh WebGL, rồi bọc
 *      `drawElements`/`drawArrays` (draw call, tam giác), `createBuffer`/
 *      `bufferData` (cấp phát hình học), `createProgram` (vật liệu).
 *   ③ `uniformMatrix4fv` → ma trận model-view của khung. Trong lúc kéo, ma
 *      trận model đứng yên, nên **biến thiên của model-view CHÍNH LÀ biến
 *      thiên của camera** — từ đó ra góc quay giữa hai khung.
 *
 * Móc cài bằng `Page.addScriptToEvaluateOnNewDocument`, tức chạy TRƯỚC mọi
 * script của trang. Không một dòng mã sản phẩm nào bị đụng.
 *
 * ⚠️ Những gì bộ đo này KHÔNG lấy được, nó khai NOT_MEASURED chứ không đoán:
 * số lần gọi camera-fit và số lần guard kích hoạt là hàm trong closure. Chúng
 * chỉ được SUY từ bước nhảy của ma trận, và phải đọc đúng như một suy luận.
 */
import { createServer } from "node:http";
import { existsSync, readFileSync, writeFileSync, mkdirSync, readdirSync, statSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join, resolve, extname } from "node:path";
import { BrowserSession, sleep } from "./browser-runner.mjs";

const CO = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, ds) => {
  if (x.startsWith("--")) a.push([x.slice(2), ds[i + 1]?.startsWith("--") ? true : ds[i + 1] ?? true]);
  return a;
}, []));
const GOC = resolve(CO.goc ?? join(import.meta.dirname, "..", ".."));
const FE = join(GOC, "frontend");
const DIST = join(FE, "dist");
const NHAN = CO.nhan ?? "candidate";
const LAP = Number(CO.lap ?? 5);
const RA = resolve(CO.ra ?? join(GOC, "docs", "evaluation", "geometry",
  "scene3d-interaction-smoothness"));
const TAGS = (CO.ca ?? "p1,p6,p7").split(",");

const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png",
  ".woff2": "font/woff2", ".ico": "image/x-icon" };

function phucVu(thuMuc) {
  return new Promise((res) => {
    const sv = createServer((rq, rp) => {
      let p = decodeURIComponent(rq.url.split("?")[0]);
      if (p === "/") p = "/index.html";
      let f = join(thuMuc, p);
      if (!existsSync(f) || statSync(f).isDirectory()) {
        if (extname(p) !== "") { rp.writeHead(404); rp.end("khong co"); return; }
        f = join(thuMuc, "index.html");
      }
      rp.writeHead(200, { "Content-Type": MIME[extname(f)] ?? "application/octet-stream" });
      rp.end(readFileSync(f));
    });
    /* ⚠️ Cổng 0 (hệ tự chọn) thỉnh thoảng ném EACCES trên Windows sau nhiều
     * phiên Chrome — dải cổng tạm bị chiếm hoặc rơi vào vùng loại trừ của hệ.
     * Thử tuần tự một dải tường minh thay vì để cả lượt đo chết. */
    let i = 0;
    const congs = [0, 8231, 8232, 8233, 8234, 8235, 8236, 8237];
    const thu = () => {
      sv.removeAllListeners("error");
      sv.once("error", () => { i += 1; if (i < congs.length) thu(); });
      sv.listen(congs[i], "127.0.0.1", () => res({ sv, cong: sv.address().port }));
    };
    thu();
  });
}

/* ─────────── móc đo, tiêm TRƯỚC mọi script của trang ───────────
   ⚠️ Không dùng backtick trong chuỗi này. */
const MOC = `
(function () {
  var D = { frames: [], draws: 0, tris: 0, buffers: 0, programs: 0, canvases: 0,
            ctxs: 0, mats: [], moc: 'chua-bat-dau', motion: [] };
  window.__DO__ = D;
  D.reset = function (nhan) { D.moc = nhan; D.frames.length = 0; D.motion.length = 0;
    D.draws = 0; D.tris = 0; D.buffers = 0; D.programs = 0; D.t0 = performance.now(); };

  var raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = function (fn) {
    return raf(function (t) {
      var truoc = D._t; D._t = t;
      if (truoc !== undefined) D.frames.push(+(t - truoc).toFixed(3));
      D._drawFrame = 0;
      return fn(t);
    });
  };

  var gc = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (kind) {
    var ctx = gc.apply(this, arguments);
    if (ctx && (kind === 'webgl' || kind === 'webgl2' || kind === 'experimental-webgl')
        && !ctx.__daBoc) {
      ctx.__daBoc = true; D.ctxs += 1;
      var de = ctx.drawElements, da = ctx.drawArrays;
      ctx.drawElements = function (mode, count) { D.draws += 1; D.tris += count / 3;
        D._drawFrame = (D._drawFrame || 0) + 1; return de.apply(this, arguments); };
      ctx.drawArrays = function (mode, first, count) { D.draws += 1; D.tris += count / 3;
        D._drawFrame = (D._drawFrame || 0) + 1; return da.apply(this, arguments); };
      var cb = ctx.createBuffer, cp = ctx.createProgram;
      ctx.createBuffer = function () { D.buffers += 1; return cb.apply(this, arguments); };
      ctx.createProgram = function () { D.programs += 1; return cp.apply(this, arguments); };
      var um = ctx.uniformMatrix4fv;
      ctx.uniformMatrix4fv = function (loc, transpose, value) {
        // Ma trận ĐẦU TIÊN của mỗi khung: dùng làm đại diện model-view.
        if (D._drawFrame === 0 && !D._matFrame) {
          D._matFrame = 1;
          D.mats.push(Array.prototype.slice.call(value, 0, 16));
          if (D.mats.length > 400) D.mats.shift();
        }
        return um.apply(this, arguments);
      };
    }
    return ctx;
  };

  var ce = Document.prototype.createElement;
  Document.prototype.createElement = function (t) {
    if (String(t).toLowerCase() === 'canvas') D.canvases += 1;
    return ce.apply(this, arguments);
  };

  // Độ trễ từ pointermove tới khung vẽ kế tiếp.
  window.addEventListener('pointermove', function (e) {
    D._lastMove = performance.now();
  }, true);
  var raf2 = window.requestAnimationFrame;
  D.latency = [];
  window.requestAnimationFrame = function (fn) {
    return raf2(function (t) {
      if (D._lastMove !== undefined) {
        D.latency.push(+(performance.now() - D._lastMove).toFixed(2));
        D._lastMove = undefined;
      }
      D._matFrame = 0;
      return fn(t);
    });
  };
})();
`;

/** Góc quay giữa hai ma trận 4x4 (phần 3x3), độ. */
function gocGiua(a, b) {
  // R = Ra^T · Rb, góc = acos((tr(R) − 1)/2)
  const g = (m, r, c) => m[c * 4 + r];
  let tr = 0;
  for (let i = 0; i < 3; i++) {
    for (let k = 0; k < 3; k++) tr += (i === k ? 1 : 0) * 0;
  }
  // tr(Ra^T·Rb) = Σ_ij Ra[i][j]·Rb[i][j]
  let s = 0;
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) s += g(a, i, j) * g(b, i, j);
  // chuẩn hoá theo tỉ lệ (ma trận có thể mang scale)
  const na = Math.hypot(g(a, 0, 0), g(a, 1, 0), g(a, 2, 0));
  const nb = Math.hypot(g(b, 0, 0), g(b, 1, 0), g(b, 2, 0));
  const c = Math.max(-1, Math.min(1, (s / (na * nb) - 1) / 2));
  return +(Math.acos(c) * 180 / Math.PI).toFixed(4);
}

/**
 * TRỤC quay giữa hai ma trận, trong hệ của vật (≈ hệ thế giới khi ma trận model
 * không mang phép quay — đúng với hầu hết vật trong cảnh này).
 *
 * ⚠️ Đây là phép đo QUYẾT ĐỊNH của wave. Tổng GÓC quay không phân biệt được
 * "xoay quanh trục đứng của hình" với "lăn quanh một trục nằm ngang" — hai
 * chuyển động cho cảm giác khác hẳn nhau mà số độ có thể như nhau.
 */
function trucGiua(a, b) {
  const g = (m, r, c) => m[c * 4 + r];
  // R = Ra^T · Rb
  const R = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
      let s2 = 0;
      for (let k = 0; k < 3; k++) s2 += g(a, k, i) * g(b, k, j);
      R[i][j] = s2;
    }
  }
  const v = [R[2][1] - R[1][2], R[0][2] - R[2][0], R[1][0] - R[0][1]];
  const n = Math.hypot(v[0], v[1], v[2]);
  if (n < 1e-9) return null;
  const u = v.map((x) => x / n);
  // Khử dấu để trung bình không triệt tiêu: ép thành phần lớn nhất dương.
  const k = u.map(Math.abs).indexOf(Math.max(...u.map(Math.abs)));
  return u[k] < 0 ? u.map((x) => -x) : u;
}

const thongKe = (xs) => {
  if (xs.length === 0) return null;
  const s = [...xs].sort((a, b) => a - b);
  const q = (p) => s[Math.min(s.length - 1, Math.floor(s.length * p))];
  return {
    n: s.length, trungVi: +q(0.5).toFixed(2), p95: +q(0.95).toFixed(2),
    p99: +q(0.99).toFixed(2), max: +s[s.length - 1].toFixed(2),
    tren16_7: xs.filter((x) => x > 16.7).length,
    tren33_3: xs.filter((x) => x > 33.3).length,
  };
};

const FIXTURES = () => {
  const d = join(GOC, "docs", "evaluation", "geometry", "product-ui-result-rendering", "fixtures");
  return readdirSync(d).filter((f) => /^p[1-7]_/.test(f)).sort()
    .map((f) => ({ tag: f.slice(0, 2), ...JSON.parse(readFileSync(join(d, f), "utf-8")) }));
};

const DOC = `JSON.stringify({
  buoc: (document.querySelector('.geo3d-buoc-so') || {}).textContent || '',
  xuong: !!document.querySelector('.geo3d-xuong'),
  canvas: document.querySelectorAll('.geo3d-canvas canvas').length
})`;

async function motCa(sess, fx, { rong, cao }) {
  const env = JSON.stringify(fx.envelope);
  await sess.eval(`(()=>{window.__ALGO_SIM_STORE__.getState().loadEnvelope(${env});return 1})()`);
  for (let i = 0; i < 60; i++) {
    const d = JSON.parse(await sess.eval(DOC));
    if (d.xuong && d.canvas > 0 && d.buoc) break;
    await sleep(200);
  }
  // Tua tới bước cuối bằng nút thật.
  const soBuoc = fx.expected_trace_event_count ?? 1;
  for (let i = 0; i < soBuoc + 4; i++) {
    const b = await sess.eval(`(()=>{const e=document.querySelector('.geo3d-buoc-so');
      return e?e.textContent:'';})()`);
    const m = /(\d+)\s*\/\s*(\d+)/.exec(b);
    if (m && m[1] === m[2]) break;
    await sess.eval(`(()=>{const b=document.querySelector('[aria-label="Bước sau"]');
      if(b&&!b.disabled) b.click(); return 1})()`);
    await sleep(80);
  }
  await sleep(400);

  const hop = JSON.parse(await sess.eval(`(()=>{const c=document.querySelector('.geo3d-canvas canvas');
    const r=c.getBoundingClientRect();
    return JSON.stringify({x:r.x,y:r.y,w:r.width,h:r.height});})()`));

  /* ── CỬA SỔ ĐỨNG YÊN: chứng minh phép đo góc không tự bịa chuyển động ──
   *
   * Ma trận đại diện lấy là ma trận model-view ĐẦU TIÊN của mỗi khung. Nếu
   * thứ tự vẽ đổi giữa các khung thì "góc quay" đo được sẽ là góc giữa hai vật
   * KHÁC NHAU — một con số lớn mà không có chuyển động nào. Cửa sổ này để bắt
   * đúng chuyện đó: không ai chạm chuột, nên tổng góc phải ≈ 0. */
  await sess.eval(`(()=>{window.__DO__.reset('dung-yen');return 1})()`);
  await sleep(1000);
  const dYen = JSON.parse(await sess.eval(`JSON.stringify({
    frames: window.__DO__.frames.slice(), mats: window.__DO__.mats.slice(-200)})`));
  const gocYen = [];
  for (let i = 1; i < dYen.mats.length; i++) gocYen.push(gocGiua(dYen.mats[i - 1], dYen.mats[i]));

  // ── kéo 300 px trong 1 giây, thả, theo dõi thêm 1 giây ──
  await sess.eval(`(()=>{window.__DO__.reset('keo');return 1})()`);
  const y = Math.round(hop.y + hop.h / 2);
  const x0 = Math.round(hop.x + hop.w / 2 - 150);
  const g = (type, x, buttons) => sess._send("Input.dispatchMouseEvent",
    { type, x, y, button: "left", buttons, clickCount: 1 });
  await g("mousePressed", x0, 1);
  const tMoc = Date.now();
  const BUOC = 60;
  for (let i = 1; i <= BUOC; i++) {
    await g("mouseMoved", x0 + (300 * i) / BUOC, 1);
    const cho = tMoc + (1000 * i) / BUOC - Date.now();
    if (cho > 0) await sleep(cho);
  }
  const dKeo = JSON.parse(await sess.eval(`JSON.stringify({
    frames: window.__DO__.frames.slice(), latency: window.__DO__.latency.slice(),
    draws: window.__DO__.draws, tris: Math.round(window.__DO__.tris),
    buffers: window.__DO__.buffers, programs: window.__DO__.programs,
    canvases: window.__DO__.canvases, ctxs: window.__DO__.ctxs,
    mats: window.__DO__.mats.slice(-200)
  })`));
  await g("mouseReleased", x0 + 300, 0);

  // damping
  await sess.eval(`(()=>{window.__DO__.reset('damping');return 1})()`);
  await sleep(1000);
  const dDamp = JSON.parse(await sess.eval(`JSON.stringify({
    frames: window.__DO__.frames.slice(), mats: window.__DO__.mats.slice(-200),
    draws: window.__DO__.draws
  })`));

  const gocKeo = [], trucKeo = [];
  for (let i = 1; i < dKeo.mats.length; i++) {
    gocKeo.push(gocGiua(dKeo.mats[i - 1], dKeo.mats[i]));
    const t = trucGiua(dKeo.mats[i - 1], dKeo.mats[i]);
    if (t && gocKeo[gocKeo.length - 1] > 0.05) trucKeo.push(t);
  }
  const trucTB = trucKeo.length
    ? [0, 1, 2].map((k) => +(trucKeo.reduce((a, t) => a + t[k], 0) / trucKeo.length).toFixed(3))
    : null;
  const gocDamp = [];
  for (let i = 1; i < dDamp.mats.length; i++) gocDamp.push(gocGiua(dDamp.mats[i - 1], dDamp.mats[i]));

  return {
    tag: fx.tag, viewport: `${rong}x${cao}`, canvas: { w: Math.round(hop.w), h: Math.round(hop.h) },
    dungYen: {
      soKhung: dYen.frames.length,
      tongGocQuay: +gocYen.reduce((a, b) => a + b, 0).toFixed(3),
      gocMoiKhung: thongKe(gocYen),
    },
    keo: {
      frameTime: thongKe(dKeo.frames), soKhung: dKeo.frames.length,
      latency: thongKe(dKeo.latency),
      drawCalls: dKeo.draws, triangles: dKeo.tris,
      capPhatBuffer: dKeo.buffers, capPhatProgram: dKeo.programs,
      canvasTao: dKeo.canvases, glContext: dKeo.ctxs,
      gocMoiKhung: thongKe(gocKeo),
      tongGocQuay: +gocKeo.reduce((a, b) => a + b, 0).toFixed(2),
      trucQuayTrungBinh: trucTB,
      soMauTruc: trucKeo.length,
      // Bước nhảy lớn ⇒ NGHI có camera-fit hoặc dựng lại cảnh giữa lúc kéo.
      buocNhay: gocKeo.filter((x) => x > 12).length,
    },
    damping: {
      frameTime: thongKe(dDamp.frames), soKhung: dDamp.frames.length,
      tongGocQuay: +gocDamp.reduce((a, b) => a + b, 0).toFixed(2),
      conChuyenDong: gocDamp.filter((x) => x > 0.01).length,
      gocMoiKhung: thongKe(gocDamp),
    },
  };
}

export async function chay() {
  const commit = execFileSync("git", ["rev-parse", "HEAD"], { cwd: GOC }).toString().trim();
  execFileSync("npm", ["run", "build"], { cwd: FE, stdio: "pipe", shell: true, timeout: 600000 });
  const { sv, cong } = await phucVu(DIST);
  const kq = { nhan: NHAN, commit, chay_luc: new Date().toISOString(), lap: LAP, luot: [] };
  try {
    for (const [rong, cao] of [[1440, 900], [390, 844]]) {
      const sess = new BrowserSession({ viewport: rong, height: cao, webgl: true,
        url: `http://127.0.0.1:${cong}`, napModuleDev: false });
      await sess._sendTruocTrang?.();
      // Tiêm móc TRƯỚC mọi script của trang.
      sess.__moc = MOC;
      const openGoc = sess.open.bind(sess);
      sess.open = async function () {
        const r = await openGoc();
        return r;
      };
      await sess.open();
      await sess._send("Page.addScriptToEvaluateOnNewDocument", { source: MOC });
      await sess._send("Page.reload", {});
      await sleep(2500);
      for (const fx of FIXTURES().filter((f) => TAGS.includes(f.tag))) {
        for (let i = 1; i <= LAP; i++) {
          const r = await motCa(sess, fx, { rong, cao });
          kq.luot.push({ ...r, lanThu: i });
          process.stdout.write(".");
        }
      }
      await sess.close();
      console.log("");
    }
  } finally { sv.close(); }
  mkdirSync(RA, { recursive: true });
  const ten = NHAN === "baseline" ? "BASELINE_INTERACTION.json" : "CANDIDATE_INTERACTION.json";
  writeFileSync(join(RA, ten), JSON.stringify(kq, null, 2), "utf-8");
  console.log(`→ ${join(RA, ten)}  (${kq.luot.length} lượt)`);
  return kq;
}

if (import.meta.filename === process.argv[1]) await chay();
