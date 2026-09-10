/**
 * scene3d-browser-acceptance.mjs — CỔNG TRÌNH DUYỆT chạy trên BẢN DỰNG SẢN PHẨM.
 *
 * ─── VÌ SAO TỒN TẠI ───────────────────────────────────────────────────────
 *
 * Wave trước đóng với `BROWSER_EVIDENCE = NOT_ESTABLISHED`: `spot-check-demo`
 * cho 4/12, nhưng chạy lại trên mã CHƯA sửa cũng chỉ 6/12 trong khi nền tài
 * liệu là 12/12. Một cổng không lập lại được nền của chính nó thì không chứng
 * minh được gì — cho cả hai phía.
 *
 * Nguyên nhân định vị được ở wave này: `spot-check-demo` (và `browser-runner`)
 * nạp cảnh bằng `import('/src/state/store.ts')` — đường **chỉ tồn tại trên
 * Vite dev**. Đo trên dev là đo một transport đã biết là chập chờn (2/15 phiên
 * kẹt), rồi quy kết quả cho sản phẩm.
 *
 * Cổng này đo trên `dist/` phục vụ tĩnh, và vào bằng `window.__ALGO_SIM_STORE__`
 * — thứ `main.tsx` phơi ra ở CẢ hai chế độ. Không sửa một dòng mã sản phẩm nào.
 *
 * ─── LUẬT ────────────────────────────────────────────────────────────────
 *
 * ① Mỗi thất bại phải có TÊN. `xuong=false canvas=0` không phải kết luận —
 *   nó là triệu chứng của ít nhất năm bệnh khác nhau, và cổng phải nói bệnh nào.
 * ② Chờ CÓ ĐIỀU KIỆN, không `sleep` cố định.
 * ③ Lỗi hạ tầng ghi RIÊNG, không bao giờ cộng vào phán quyết về sản phẩm.
 * ④ Bề dày nét đo từ ĐIỂM ẢNH của ảnh chụp, không đọc `linewidth` trong mã.
 *
 * Dùng:
 *   node scripts/scene3d-browser-acceptance.mjs --nhan candidate --lap 3
 *   node scripts/scene3d-browser-acceptance.mjs --tiem      # phép tiêm
 */
import { spawn, execFileSync } from "node:child_process";
import { createServer } from "node:http";
import {
  existsSync, readFileSync, writeFileSync, mkdirSync, readdirSync, statSync,
} from "node:fs";
import { join, resolve, extname } from "node:path";
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { docPNG, doBeDayCucBo, anhPhang } from "./png-pixels.mjs";

const CO = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, ds) => {
  if (x.startsWith("--")) a.push([x.slice(2), ds[i + 1]?.startsWith("--") ? true : ds[i + 1] ?? true]);
  return a;
}, []));
const GOC = resolve(CO.goc ?? join(import.meta.dirname, "..", ".."));
const FE = join(GOC, "frontend");
const DIST = join(FE, "dist");
const NHAN = CO.nhan ?? "candidate";
const LAP = Number(CO.lap ?? 3);
const RA = resolve(CO.ra ?? join(GOC, "docs", "evaluation", "geometry",
  "scene3d-visual-language-browser-acceptance"));

/** Mọi trạng thái cổng có thể kết luận. Thứ tự = thứ tự phân loại. */
export const TRANG_THAI = [
  "BUILD_FAILED", "STALE_BUILD", "SERVER_UNREACHABLE", "ENTRY_CHUNK_UNREACHABLE",
  "PAGE_LOAD_FAILED", "ROOT_EMPTY", "WRONG_FIXTURE", "CANVAS_MISSING",
  "WEBGL_UNAVAILABLE", "SCENE_NOT_READY", "ASSERTION_FAILED", "PASS",
];

/** Tỉ lệ điểm ảnh KHÁC nền — cảnh có hình thì phải có mực. */
export function tiLeMuc(anh, nen = [250, 249, 247], nguong = 18) {
  const { w, h, rgba } = anh;
  let co = 0, tong = 0;
  for (let y = 0; y < h; y += 2) {
    for (let x = 0; x < w; x += 2) {
      const i = (y * w + x) * 4;
      const d = Math.abs(rgba[i] - nen[0]) + Math.abs(rgba[i + 1] - nen[1]) + Math.abs(rgba[i + 2] - nen[2]);
      if (d > nguong) co++;
      tong++;
    }
  }
  return co / tong;
}

/** Dưới ngưỡng này thì cảnh coi như chưa dựng. Đo được: cảnh bước 0 của p1
 *  chỉ ~0,15 % mực; cảnh đủ hình 3–12 %. */
export const NGUONG_MUC = 0.012;

const sha = () => execFileSync("git", ["rev-parse", "HEAD"], { cwd: GOC }).toString().trim();

/** mtime mới nhất trong một cây (bỏ thư mục rác). */
function moiNhat(goc, bo = new Set(["node_modules", ".git", "dist"])) {
  let m = 0;
  const di = (d) => {
    let ds; try { ds = readdirSync(d, { withFileTypes: true }); } catch { return; }
    for (const e of ds) {
      if (bo.has(e.name)) continue;
      const p = join(d, e.name);
      if (e.isDirectory()) di(p);
      else { const t = statSync(p).mtimeMs; if (t > m) m = t; }
    }
  };
  di(goc);
  return m;
}

// ─────────────────────── ① dựng + đóng dấu + tươi ───────────────────────
export function dungVaDongDau({ boQuaDung = false } = {}) {
  const commit = sha();
  if (!boQuaDung) {
    try {
      execFileSync("npm", ["run", "build"], { cwd: FE, stdio: "pipe", shell: true, timeout: 600000 });
    } catch (e) {
      return { ok: false, trangThai: "BUILD_FAILED", chiTiet: String(e.stdout ?? e).slice(-1200) };
    }
    writeFileSync(join(DIST, ".build-stamp.json"),
      JSON.stringify({ commit, luc: new Date().toISOString() }, null, 2), "utf-8");
  }
  const dau = join(DIST, ".build-stamp.json");
  if (!existsSync(dau)) return { ok: false, trangThai: "STALE_BUILD", chiTiet: "không có dấu bản dựng" };
  const d = JSON.parse(readFileSync(dau, "utf-8"));
  if (d.commit !== commit) {
    return { ok: false, trangThai: "STALE_BUILD", chiTiet: `dấu ${d.commit.slice(0, 8)} ≠ HEAD ${commit.slice(0, 8)}` };
  }
  const src = moiNhat(join(FE, "src")), dist = moiNhat(DIST);
  if (src > dist) {
    return { ok: false, trangThai: "STALE_BUILD", chiTiet: `src mới hơn dist ${Math.round((src - dist) / 1000)}s` };
  }
  return { ok: true, commit, srcMtime: src, distMtime: dist };
}

// ─────────────────────────── ② phục vụ tĩnh ───────────────────────────
const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png",
  ".woff2": "font/woff2", ".ico": "image/x-icon" };

export function phucVu(thuMuc) {
  return new Promise((res) => {
    const sv = createServer((rq, rp) => {
      let p = decodeURIComponent(rq.url.split("?")[0]);
      if (p === "/") p = "/index.html";
      let f = join(thuMuc, p);
      /* ⚠️ Fallback SPA chỉ áp cho đường ĐIỀU HƯỚNG (không có phần mở rộng).
       *
       * Bản đầu fallback cho MỌI đường, nên một chunk `.js` bị mất vẫn trả về
       * `index.html` kèm HTTP 200 — và phép tiêm "entry chunk mất" LỌT: cổng
       * báo PASS trên một bản dựng không tải nổi mã. Đúng loại lỗi mà chính
       * cổng này sinh ra để bắt, nằm ngay trong cổng. */
      const coDuoi = extname(p) !== "";
      if (!existsSync(f) || statSync(f).isDirectory()) {
        if (coDuoi) { rp.writeHead(404); rp.end("khong co"); return; }
        f = join(thuMuc, "index.html");
      }
      try {
        rp.writeHead(200, { "Content-Type": MIME[extname(f)] ?? "application/octet-stream" });
        rp.end(readFileSync(f));
      } catch { rp.writeHead(500); rp.end("loi"); }
    });
    sv.listen(0, "127.0.0.1", () => res({ sv, cong: sv.address().port }));
  });
}

/** Probe tài liệu + MỌI entry chunk TRƯỚC khi mở Chrome. */
export async function doDuong(base, thuMuc) {
  let html;
  try {
    const r = await fetch(base);
    if (!r.ok) return { ok: false, trangThai: "SERVER_UNREACHABLE", chiTiet: `HTTP ${r.status}` };
    html = await r.text();
  } catch (e) { return { ok: false, trangThai: "SERVER_UNREACHABLE", chiTiet: String(e) }; }

  const duong = [...html.matchAll(/(?:src|href)="([^"]+)"/g)].map((m) => m[1])
    .filter((u) => u.startsWith("/") && /\.(js|css)$/.test(u));
  const trang = [];
  for (const u of duong) {
    try {
      const r = await fetch(base + u);
      trang.push({ url: u, status: r.status, bytes: (await r.arrayBuffer()).byteLength });
      if (!r.ok) return { ok: false, trangThai: "ENTRY_CHUNK_UNREACHABLE", chiTiet: `${u} → ${r.status}`, trang };
    } catch (e) {
      return { ok: false, trangThai: "ENTRY_CHUNK_UNREACHABLE", chiTiet: `${u} → ${e}`, trang };
    }
  }
  if (trang.length === 0) {
    return { ok: false, trangThai: "ENTRY_CHUNK_UNREACHABLE", chiTiet: "index.html không trỏ chunk nào", trang };
  }
  return { ok: true, trang };
}

// ─────────────────────────── ③ hợp đồng sẵn sàng ───────────────────────────
// ⚠️ KHÔNG được có backtick trong khối này — nó đóng luôn template literal.
// Bước hiện tại đọc từ ĐÚNG bề mặt học sinh (chuỗi "Bước k/n"), không từ
// state nội bộ: store không giữ số bước, nó nằm trong state của module.
const DOC_TRANG_THAI = `JSON.stringify((()=>{
  const S = window.__ALGO_SIM_STORE__ ? window.__ALGO_SIM_STORE__.getState() : null;
  const cv = document.querySelector('.geo3d-canvas canvas');
  const root = document.querySelector('#root');
  return {
    documentLoaded: document.readyState === 'complete',
    rootNonEmpty: (root ? root.childElementCount : 0) > 0,
    rootText: (root ? (root.innerText || '') : '').slice(0, 240),
    storeHook: !!window.__ALGO_SIM_STORE__,
    view: S ? S.view : null,
    analysisError: S ? (S.analysisError || null) : null,
    activeTitle: S && S.active ? (S.active.envelope ? S.active.envelope.title : null) : null,
    moduleId: S && S.active ? S.active.moduleId : null,
    buoc: (document.querySelector('.geo3d-buoc-so') || {}).textContent || '',
    xuong: !!document.querySelector('.geo3d-xuong'),
    canvasCount: document.querySelectorAll('.geo3d-canvas canvas').length,
    canvasW: cv ? cv.clientWidth : 0,
    canvasH: cv ? cv.clientHeight : 0,
    fallback: !!document.querySelector('.geo3d-fallback'),
    readout: (document.querySelector('.geo3d-readout') || {}).innerText || '',
    nhan: Array.from(document.querySelectorAll('.geo3d-label'))
      .filter(function(e){ return e.style.opacity !== '0'; })
      .map(function(e){ return e.textContent; }),
  };
})())`;

/** Chờ CÓ ĐIỀU KIỆN. Trả trạng thái cuối cùng + đã đạt hay chưa. */
async function choDenKhi(sess, dieuKien, { hanMs = 25000, nhipMs = 250 } = {}) {
  const het = Date.now() + hanMs;
  let tt = null;
  while (Date.now() < het) {
    tt = JSON.parse(await sess.eval(DOC_TRANG_THAI));
    if (dieuKien(tt)) return { dat: true, tt };
    await sleep(nhipMs);
  }
  return { dat: false, tt };
}

/** "Bước 13/13" → đúng bước cuối. Chuỗi rỗng hoặc khác ⇒ chưa sẵn sàng. */
export function dungBuocCuoi(chuoi, soBuoc) {
  const m = /(\d+)\s*\/\s*(\d+)/.exec(String(chuoi ?? ""));
  if (!m) return false;
  return Number(m[1]) === Number(m[2]) && Number(m[2]) === soBuoc;
}

/** Phân loại thất bại thành MỘT tên bệnh. */
export function phanLoai(tt) {
  if (!tt) return "PAGE_LOAD_FAILED";
  if (!tt.documentLoaded) return "PAGE_LOAD_FAILED";
  if (!tt.rootNonEmpty) return "ROOT_EMPTY";
  if (tt.analysisError) return "WRONG_FIXTURE";
  if (tt.fallback) return "WEBGL_UNAVAILABLE";
  if (!tt.xuong || tt.canvasCount === 0) return "CANVAS_MISSING";
  if (!(tt.canvasW > 0 && tt.canvasH > 0)) return "CANVAS_MISSING";
  return "SCENE_NOT_READY";
}

// ─────────────────────────── ④ chụp ───────────────────────────
async function chup(sess, duongDan, clip = null) {
  const { result } = await sess._send("Page.captureScreenshot",
    clip ? { format: "png", clip: { ...clip, scale: 1 } } : { format: "png" });
  const b = Buffer.from(result.data, "base64");
  writeFileSync(duongDan, b);
  return b;
}

/**
 * Tua tới bước CUỐI bằng đúng nút của người học.
 *
 * ⚠️ `store.toEnd()` KHÔNG dùng được: tuyến hình học đi thẳng vào
 * `Scene3DExplorer`, không qua registry, nên bước nằm trong state tương tác
 * của chính explorer chứ không nằm ở timeline của store — `withTimeline` thấy
 * `mod.timeline` rỗng và lặng lẽ NO-OP. Lượt chạy trước đứng ở "Bước 1/13" mà
 * cổng vẫn tưởng đã tua.
 */
async function tuaToiCuoi(sess, soBuoc) {
  for (let i = 0; i < soBuoc + 4; i++) {
    const buoc = await sess.eval(`(()=>{const e=document.querySelector('.geo3d-buoc-so');
      return e ? e.textContent : '';})()`);
    if (dungBuocCuoi(buoc, soBuoc)) return true;
    const bam = await sess.eval(`(()=>{const b=document.querySelector('[aria-label="Bước sau"]');
      if(!b) return 'khong-thay-nut'; if(b.disabled) return 'nut-tat'; b.click(); return 'ok';})()`);
    if (bam !== "ok") return false;
    await sleep(90);
  }
  return false;
}

async function keoChuot(sess, x0, y0, x1, y1) {
  const g = (type, x, y) => sess._send("Input.dispatchMouseEvent",
    { type, x, y, button: "left", buttons: 1, clickCount: 1 });
  await g("mousePressed", x0, y0);
  for (let i = 1; i <= 8; i++) {
    await g("mouseMoved", x0 + ((x1 - x0) * i) / 8, y0 + ((y1 - y0) * i) / 8);
    await sleep(30);
  }
  await g("mouseReleased", x1, y1);
  await sleep(500);
}

// ─────────────────────────── ⑤ một lượt ───────────────────────────
const FIXTURES = () => {
  const d = join(GOC, "docs", "evaluation", "geometry", "product-ui-result-rendering", "fixtures");
  return readdirSync(d).filter((f) => /^p[1-7]_/.test(f)).sort()
    .map((f) => ({ tag: f.slice(0, 2), file: f, ...JSON.parse(readFileSync(join(d, f), "utf-8")) }));
};

export async function motLuot({ nhan, lanThu, rong = 1440, cao = 900, xoay = false, luuAnh = true }) {
  const kq = { nhan, lanThu, rong, cao, xoay, batDau: new Date().toISOString(), ca: [] };
  const dung = dungVaDongDau({ boQuaDung: lanThu > 1 });
  if (!dung.ok) return { ...kq, trangThai: dung.trangThai, chiTiet: dung.chiTiet };
  kq.commit = dung.commit;

  const { sv, cong } = await phucVu(DIST);
  const base = `http://127.0.0.1:${cong}`;
  kq.base = base;
  try {
    const probe = await doDuong(base, DIST);
    kq.entryChunks = probe.trang;
    if (!probe.ok) return { ...kq, trangThai: probe.trangThai, chiTiet: probe.chiTiet };

    const sess = new BrowserSession({ viewport: rong, height: cao, url: base, webgl: true, napModuleDev: false });
    try {
      await sess.open();
    } catch (e) {
      return { ...kq, trangThai: "PAGE_LOAD_FAILED", chiTiet: String(e).slice(0, 400) };
    }
    kq.pageLoadRetries = sess.pageLoadRetries;
    kq.webglRenderer = await sess.eval(`(()=>{const c=document.createElement('canvas');
      const g=c.getContext('webgl2')||c.getContext('webgl');
      if(!g) return 'KHONG_CO';
      const d=g.getExtension('WEBGL_debug_renderer_info');
      return d ? g.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'khong ro';})()`);

    if (luuAnh) mkdirSync(join(RA, "screenshots"), { recursive: true });

    for (const fx of FIXTURES()) {
      const t0 = Date.now();
      const env = JSON.stringify(fx.envelope);
      /* ⚠️ `toEnd()` là BẮT BUỘC, không phải tiện tay.
       *
       * `loadEnvelope` đặt cảnh ở **bước 0** — lúc ấy mới chỉ có các điểm tự
       * do, chưa có khối, chưa có cạnh, chưa có thiết diện. Lượt chạy đầu của
       * cổng này báo **PASS 7/7** trên đúng những ảnh như thế: bảy tấm chỉ có
       * năm chấm đen và năm cái nhãn. Một cổng xanh trên cảnh rỗng còn tệ hơn
       * không có cổng.
       *
       * Nên hợp đồng sẵn sàng phải gồm `EXPECTED_STEP_VISIBLE`: tua tới bước
       * CUỐI rồi mới chấm, và đòi `step` đúng bằng số sự kiện − 1. */
      const soBuoc = fx.expected_trace_event_count ?? 1;
      await sess.eval(`(()=>{window.__ALGO_SIM_STORE__.getState().loadEnvelope(${env});return 1})()`);
      // Chờ xưởng dựng xong rồi mới tua.
      await choDenKhi(sess, (s) => s.xuong && s.canvasCount > 0 && s.buoc.length > 0,
        { hanMs: 20000 });
      await tuaToiCuoi(sess, soBuoc);
      const { dat, tt } = await choDenKhi(sess, (s) =>
        s.rootNonEmpty && s.xuong && s.canvasCount > 0
        && s.canvasW > 0 && s.canvasH > 0 && s.activeTitle === fx.envelope.title
        && dungBuocCuoi(s.buoc, soBuoc));

      const ca = {
        tag: fx.tag, fixture: fx.file, title: fx.envelope.title,
        msCho: Date.now() - t0, readiness: tt, consoleErrors: sess.consoleEvents.length,
      };
      if (!dat) {
        ca.trangThai = phanLoai(tt);
        if (luuAnh) {
          const p = join(RA, "screenshots", `${nhan}-${fx.tag}-CHAN-DOAN.png`);
          await chup(sess, p); ca.anhChanDoan = p;
        }
        kq.ca.push(ca); continue;
      }

      // Khung WebGL có phải một mảng phẳng không.
      const hop = JSON.parse(await sess.eval(`(()=>{const c=document.querySelector('.geo3d-canvas canvas');
        const r=c.getBoundingClientRect();
        return JSON.stringify({x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height)});})()`));
      const buf = await chup(sess, join(RA, "screenshots", `${nhan}-${fx.tag}${xoay ? "-xoay" : ""}-${rong}x${cao}.png`), hop);
      const anh = docPNG(buf);
      const phang = anhPhang(anh);
      ca.canvasBox = hop;
      ca.frame = phang;
      ca.anh = join(RA, "screenshots", `${nhan}-${fx.tag}${xoay ? "-xoay" : ""}-${rong}x${cao}.png`);
      /* Ngoài "không phẳng", còn phải có ĐỦ MỰC. Một cảnh chỉ gồm mấy chấm
       * đen trên nền trắng cũng "không phẳng" — chính nó đã lừa lượt đầu. */
      ca.mucPhu = tiLeMuc(anh);
      ca.trangThai = (phang.phang || ca.mucPhu < NGUONG_MUC) ? "SCENE_NOT_READY" : "PASS";
      if (phang.phang) ca.chiTiet = "khung WebGL phẳng — không có gì được vẽ";
      else if (ca.mucPhu < NGUONG_MUC) {
        ca.chiTiet = `chỉ ${(ca.mucPhu * 100).toFixed(2)} % điểm ảnh có mực `
          + `(ngưỡng ${(NGUONG_MUC * 100).toFixed(1)} %) — nhiều khả năng cảnh chưa dựng tới bước cuối`;
      }

      // Ô chữ và nút DOM nằm đè lên canvas — lấy toạ độ để BỎ QUA khi đo.
      const camJson = await sess.eval(`(()=>{const c=document.querySelector('.geo3d-canvas canvas');
        const b=c.getBoundingClientRect();
        const rs=[];
        document.querySelectorAll('.geo3d-label')
          .forEach(function(e){ const r=e.getBoundingClientRect();
            if(r.width>0&&r.height>0) rs.push({x:Math.round(r.x-b.x),y:Math.round(r.y-b.y),
              w:Math.round(r.width),h:Math.round(r.height)}); });
        return JSON.stringify(rs);})()`);
      const loaiTru = JSON.parse(camJson);
      ca.loaiTru = loaiTru;
      const doNet = (mauLoc, sauToiThieu) =>
        doBeDayCucBo(anh, { cuaSo: 9, sauToiThieu, mauLoc, dungSaiMau: 95, loaiTru });
      ca.beDay = {
        canhThay: doNet("#1F1F1F", 26),
        canhKhuat: doNet("#7D7975", 16),
        thietDien: doNet("#D95A43", 16),
        moiNet: doBeDayCucBo(anh, { cuaSo: 9, sauToiThieu: 26, loaiTru }),
      };

      if (xoay && !phang.phang) {
        const cx = hop.x + hop.width / 2, cy = hop.y + hop.height / 2;
        await keoChuot(sess, cx - 120, cy, cx + 120, cy - 60);
        const b2 = await chup(sess, join(RA, "screenshots", `${nhan}-${fx.tag}-sau-xoay.png`), hop);
        ca.anhSauXoay = join(RA, "screenshots", `${nhan}-${fx.tag}-sau-xoay.png`);
        ca.doiSauXoay = !Buffer.from(buf).equals(Buffer.from(b2));
        ca.frameSauXoay = anhPhang(docPNG(b2));
      }
      kq.ca.push(ca);
    }
    kq.consoleEvents = sess.consoleEvents;
    await sess.close();
  } finally { sv.close(); }

  const dat = kq.ca.filter((c) => c.trangThai === "PASS").length;
  return { ...kq, trangThai: dat === kq.ca.length && kq.ca.length > 0 ? "PASS" : "ASSERTION_FAILED", dat, tong: kq.ca.length };
}

// ─────────────────────────── phép tiêm ───────────────────────────
/**
 * Tám phép tiêm §10. Một cổng chưa từng đỏ là một cổng chưa được chứng minh —
 * và cổng này vừa được viết lại từ đầu, nên nó nợ phần chứng minh ấy nhiều hơn
 * bất kỳ cổng nào khác trong kho.
 */
async function phepTiem() {
  const { mkdtempSync, cpSync, rmSync, unlinkSync } = await import("node:fs");
  const { tmpdir } = await import("node:os");
  const kq = [];
  const ghi = (ten, mong, thuc, bat) => {
    kq.push({ ten, mong, thuc, bat });
    console.log(`${bat ? "ĐỎ ✓" : "LỌT ✗"}  ${ten.padEnd(38)} mong ${mong} · thực ${thuc}`);
  };

  // ① dist cũ
  {
    const dau = join(DIST, ".build-stamp.json");
    const luu = readFileSync(dau, "utf-8");
    writeFileSync(dau, JSON.stringify({ commit: "0".repeat(40), luc: "x" }), "utf-8");
    const r = dungVaDongDau({ boQuaDung: true });
    writeFileSync(dau, luu, "utf-8");
    ghi("① dist thuộc commit khác", "STALE_BUILD", r.trangThai ?? "PASS", r.trangThai === "STALE_BUILD");
  }
  // ② entry chunk không tải được
  {
    const tmp = mkdtempSync(join(tmpdir(), "tiem-"));
    cpSync(DIST, tmp, { recursive: true });
    for (const f of readdirSync(join(tmp, "assets"))) {
      if (f.endsWith(".js")) unlinkSync(join(tmp, "assets", f));
    }
    const { sv, cong } = await phucVu(tmp);
    const r = await doDuong(`http://127.0.0.1:${cong}`, tmp);
    sv.close(); rmSync(tmp, { recursive: true, force: true });
    ghi("② entry chunk mất", "ENTRY_CHUNK_UNREACHABLE", r.trangThai ?? "PASS",
      r.trangThai === "ENTRY_CHUNK_UNREACHABLE");
  }
  // ③ #root rỗng
  {
    const tmp = mkdtempSync(join(tmpdir(), "tiem-"));
    writeFileSync(join(tmp, "index.html"),
      "<!doctype html><meta charset=utf-8><div id=root></div>", "utf-8");
    const { sv, cong } = await phucVu(tmp);
    const sess = new BrowserSession({ viewport: 800, height: 600, webgl: true,
      url: `http://127.0.0.1:${cong}`, napModuleDev: false });
    let tt = null;
    try { await sess.open(); } catch { /* mong đợi: trang không dựng */ }
    try { tt = JSON.parse(await sess.eval(DOC_TRANG_THAI)); } catch { /* không đọc được */ }
    try { await sess.close(); } catch { /* đã đóng */ }
    sv.close(); rmSync(tmp, { recursive: true, force: true });
    const t = phanLoai(tt);
    ghi("③ #root rỗng", "ROOT_EMPTY", t, t === "ROOT_EMPTY" || t === "PAGE_LOAD_FAILED");
  }
  // ④–⑦ cần một phiên thật trên bản dựng
  {
    const { sv, cong } = await phucVu(DIST);
    const sess = new BrowserSession({ viewport: 1440, height: 900, webgl: true,
      url: `http://127.0.0.1:${cong}`, napModuleDev: false });
    await sess.open();
    const fx = FIXTURES()[0];
    const env = JSON.stringify(fx.envelope);
    const nap = async () => {
      await sess.eval(`(()=>{window.__ALGO_SIM_STORE__.getState().loadEnvelope(${env});return 1})()`);
      await choDenKhi(sess, (x) => x.xuong && x.canvasCount > 0, { hanMs: 20000 });
    };

    // ④ canvas vắng
    await nap();
    await sess.eval(`(()=>{const c=document.querySelector('.geo3d-canvas canvas');
      if(c) c.remove(); return 1})()`);
    const t4 = phanLoai(JSON.parse(await sess.eval(DOC_TRANG_THAI)));
    ghi("④ canvas bị gỡ khỏi DOM", "CANVAS_MISSING", t4, t4 === "CANVAS_MISSING");

    // ⑤ cảnh chưa tua tới bước cuối
    await sess.eval(`(()=>{location.reload();return 1})()`);
    await sleep(2500);
    await nap();
    const hop = JSON.parse(await sess.eval(`(()=>{const c=document.querySelector('.geo3d-canvas canvas');
      const r=c.getBoundingClientRect();
      return JSON.stringify({x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height)});})()`));
    const anh5 = docPNG(await chup(sess, join(RA, "screenshots", "tiem-05-chua-tua.png"), hop));
    const muc5 = tiLeMuc(anh5);
    ghi("⑤ cảnh dừng ở bước đầu", `mực < ${NGUONG_MUC}`, muc5.toFixed(4), muc5 < NGUONG_MUC);

    // ⑥ khung WebGL trắng
    const trang = { w: 40, h: 40, rgba: new Uint8Array(40 * 40 * 4).fill(250) };
    ghi("⑥ khung WebGL phẳng", "phang=true", String(anhPhang(trang).phang), anhPhang(trang).phang === true);

    // ⑦ sai fixture
    await sess.eval(`(()=>{window.__ALGO_SIM_STORE__.getState()
      .loadEnvelope({simulation_id:'khong.ton.tai',title:'x',config:{}});return 1})()`);
    await sleep(400);
    const t7 = phanLoai(JSON.parse(await sess.eval(DOC_TRANG_THAI)));
    ghi("⑦ envelope sai mô phỏng", "WRONG_FIXTURE", t7, t7 === "WRONG_FIXTURE");

    await sess.close(); sv.close();
  }
  // ⑧ oracle bề dày bị đổi
  {
    const { anhThu } = await import("./png-pixels.mjs");
    const dung = doBeDayCucBo(anhThu(2.8), { cuaSo: 9 }).trungVi;
    const doi = doBeDayCucBo(anhThu(1.0), { cuaSo: 9 }).trungVi;
    ghi("⑧ oracle phân biệt 2,8 px với 1 px", "khác nhau",
      `${dung} vs ${doi}`, Math.abs(dung - 2.8) < 0.15 && Math.abs(doi - dung) > 0.6);
  }

  mkdirSync(RA, { recursive: true });
  writeFileSync(join(RA, "FAULT_INJECTIONS.json"),
    JSON.stringify({ chay_luc: new Date().toISOString(), bat: kq.filter((x) => x.bat).length,
      tong: kq.length, phep: kq }, null, 2), "utf-8");
  console.log(`
${kq.filter((x) => x.bat).length}/${kq.length} phép tiêm bị bắt`);
}

// ─────────────────────────── chạy ───────────────────────────
if (import.meta.filename === process.argv[1] && CO.tiem) {
  mkdirSync(RA, { recursive: true });
  await phepTiem();
} else if (import.meta.filename === process.argv[1]) {
  mkdirSync(RA, { recursive: true });
  const luots = [];
  for (let i = 1; i <= LAP; i++) {
    const r = await motLuot({
      nhan: NHAN, lanThu: i, luuAnh: i === 1,
      rong: Number(CO.rong ?? 1440), cao: Number(CO.cao ?? 900), xoay: !!CO.xoay,
    });
    luots.push(r);
    console.log(`${NHAN} lượt ${i}: ${r.trangThai} — ${r.dat ?? 0}/${r.tong ?? 0} ca`
      + (r.chiTiet ? ` · ${r.chiTiet}` : ""));
    for (const c of r.ca ?? []) {
      if (c.trangThai !== "PASS") console.log(`   ✗ ${c.tag} ${c.trangThai} ${c.chiTiet ?? ""} `
        + `· view=${c.readiness?.view} err=${JSON.stringify(c.readiness?.analysisError)} `
        + `xuong=${c.readiness?.xuong} canvas=${c.readiness?.canvasCount}`);
    }
  }
  const ten = CO.ten ?? (NHAN === "baseline" ? "BASELINE_RUNS.json" : "CANDIDATE_RUNS.json");
  writeFileSync(join(RA, ten), JSON.stringify({
    nhan: NHAN, lap: LAP, chay_luc: new Date().toISOString(), luots,
  }, null, 2), "utf-8");
  console.log(`→ ${join(RA, ten)}`);
}
