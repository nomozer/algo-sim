/**
 * scene3d-d2-gate.mjs — CỔNG NGHIỆM THU VÒNG D2.
 *
 * Bổ sung cho `scene3d-fidelity-gate.mjs` (vai màu, bề dày, nhãn chồng, tràn
 * khung, nét khuất đổi chỗ) và `scene3d-orbit-gate.mjs` (quay 360°, trục ổn
 * định, không tự khớp khung khi kéo). Cổng này hỏi bốn câu mà hai cổng kia
 * không hỏi:
 *
 *   ① **BẤT BIẾN DPR** — cỡ CSS và cỡ khung vẽ phải đúng tích số. Đây là chỗ
 *      duy nhất bắt được hai lỗi: bật `setPixelRatio` mà quên
 *      `setSize(…, true)` (canvas phình gấp đôi theo px CSS rồi bị
 *      `overflow: hidden` giấu đi), và lấy cỡ KHUNG VẼ làm `resolution` của
 *      `LineMaterial` (nét mảnh đi đúng DPR lần).
 *   ② **ĐỘ SẮC** — vẽ thẳng ở 2× phải cho mép nét hẹp hơn hẳn bản 1× phóng to.
 *   ③ **KHOẢNG CÁCH NHÃN ↔ MỰC, đo từ ĐIỂM ẢNH.** Không đọc lại niềm tin của
 *      bộ giải: nó tin là đã tránh nét thì chưa chắc mắt thấy thế. Đo từ ảnh
 *      là đo đúng thứ người học nhìn.
 *   ④ **TIẾN TRÌNH THIẾT DIỆN** — bốn bước `EXTEND` phải cho bốn khung hình
 *      KHÁC nhau, và mảng tô chỉ xuất hiện ở bước đóng hình.
 *
 * Cờ: `--ca p1,p3` · `--ra <thư mục>` · `--bo-qua-build` · `--tiem <tên>`.
 */
import { readFileSync, writeFileSync, mkdirSync, readdirSync, statSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join, resolve } from "node:path";
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { phucVu } from "./scene3d-orbit-gate.mjs";
import { docPNG, doBeDayVuongGoc } from "./png-pixels.mjs";
import { TOKEN } from "./scene3d-fidelity-gate.mjs";

const CO = Object.fromEntries(process.argv.slice(2)
  .map((a, i, ds) => (a.startsWith("--")
    ? [a.slice(2), ds[i + 1]?.startsWith("--") === false ? ds[i + 1] : true] : null))
  .filter(Boolean));
const GOC = resolve(join(import.meta.dirname, "..", ".."));
const FE = join(GOC, "frontend");
const DIST = join(FE, "dist");
const THU_FX = join(GOC, "docs/evaluation/geometry/product-ui-result-rendering/fixtures");
const RA = CO.ra ? resolve(String(CO.ra))
  : join(GOC, "docs/evaluation/geometry/scene3d-d2-implementation");
const TIEM = CO.tiem ? String(CO.tiem) : null;

export const NGUONG = {
  /** Nhãn ↔ mực, pixel CSS. Khung hẹp nới còn 4 (xem `KHUNG_HEP_PX`). */
  NHAN_NET_RONG: 6,
  NHAN_NET_HEP: 4,
  /** Lề an toàn tới mép khung. */
  LE: 12,
  /** Độ sắc ở DPR 2 phải hẹp hơn DPR 1 ít nhất chừng này lần. */
  SAC_TOT_HON: 1.4,
  /** Sai số cho phép của cỡ khung vẽ so với `CSS × min(dpr, 2)`. */
  BUFFER_SAI_SO: 1,
};

export const TRANG_THAI = {
  DAT: "DAT",
  DPR_BUFFER_SAI: "DPR_BUFFER_SAI",
  DPR_CSS_PHINH: "DPR_CSS_PHINH",
  NET_KHONG_SAC_HON: "NET_KHONG_SAC_HON",
  NHAN_QUA_SAT_NET: "NHAN_QUA_SAT_NET",
  NHAN_BI_GIAU: "NHAN_BI_GIAU",
  NHAN_BI_CHE: "NHAN_BI_CHE",
  NHAN_TRAN_LE: "NHAN_TRAN_LE",
  THIET_DIEN_KHONG_LUY_TIEN: "THIET_DIEN_KHONG_LUY_TIEN",
  TO_SOM: "TO_SOM",
  CANH_RONG: "CANH_RONG",
  KHONG_DUNG_DUOC: "KHONG_DUNG_DUOC",
};

/** `dist/` phải mới hơn `src/` — nếu không mọi số đo nói về một bản dựng khác. */
function kiemDistMoi() {
  const moiNhat = (d) => {
    let t = 0;
    for (const f of readdirSync(d, { withFileTypes: true })) {
      if (f.name === "node_modules") continue;
      const q = join(d, f.name);
      t = Math.max(t, f.isDirectory() ? moiNhat(q) : statSync(q).mtimeMs);
    }
    return t;
  };
  const s = moiNhat(join(FE, "src")), d = moiNhat(DIST);
  if (d < s) {
    throw new Error(`DIST_CU — dist/ cũ hơn src/ (${Math.round((s - d) / 1000)} s). `
      + "Chạy `npm run build` trước, và ĐỪNG tin số đo nào cho tới lúc ấy.");
  }
}

const envCa = (tag) => {
  const f = readdirSync(THU_FX).find((x) => x.startsWith(`${tag}_`));
  return JSON.parse(readFileSync(join(THU_FX, f), "utf-8")).envelope;
};

const gan = (rgba, i, hex, dung) => {
  const m = [1, 3, 5].map((k) => parseInt(hex.slice(k, k + 2), 16));
  return Math.hypot(rgba[i] - m[0], rgba[i + 1] - m[1], rgba[i + 2] - m[2]) <= dung;
};

/**
 * Khoảng cách nhỏ nhất từ mỗi hộp chữ tới MỰC gần nhất — đo từ điểm ảnh.
 *
 * Loại mọi hộp chữ khỏi phép quét: nét chữ của chính nó, và của nhãn khác, đều
 * là mực nhưng không phải NÉT HÌNH. Đây chính là chỗ bộ đo của vòng trước sai
 * — chữ màu `#000` lọt cổng gần-đen rồi bị đếm như một nét.
 */
function kcNhanToiMuc(anh, nhan, { tiLe = 1, banKinh = 26, phu = [] } = {}) {
  const { w, h, rgba } = anh;
  const hop = nhan.map((n) => ({
    x: Math.round(n.x * tiLe), y: Math.round(n.y * tiLe),
    w: Math.round(n.w * tiLe), h: Math.round(n.h * tiLe), ky: n.ky,
  }));
  /* LỚP PHỦ GIAO DIỆN không phải NÉT HÌNH.
   *
   * Ô đọc số và nút điều khiển là chữ đậm trên nền sáng, nên chúng lọt vào
   * phép quét mực y như một cạnh khối. Đo được: p1 ở 390×844 báo nhãn cách
   * mực 1,5 px, và "mực" ấy là chữ của ô đọc số. Nhãn nằm SÁT lớp phủ là
   * chuyện bình thường; nhãn bị lớp phủ CHE mới là lỗi, và đó là một phép
   * kiểm riêng bên dưới. */
  const hopPhu = phu.map((r) => ({
    x: Math.round(r.x * tiLe), y: Math.round(r.y * tiLe),
    w: Math.round(r.w * tiLe), h: Math.round(r.h * tiLe),
  }));
  const trongChu = (x, y) => hop.some((r) =>
    x >= r.x - 2 && x <= r.x + r.w + 2 && y >= r.y - 2 && y <= r.y + r.h + 2)
    || hopPhu.some((r) =>
      x >= r.x - 2 && x <= r.x + r.w + 2 && y >= r.y - 2 && y <= r.y + r.h + 2);
  const ra = [];
  const R = Math.round(banKinh * tiLe);
  for (const b of hop) {
    let gan2 = Infinity;
    for (let y = Math.max(0, b.y - R); y < Math.min(h, b.y + b.h + R); y++) {
      for (let x = Math.max(0, b.x - R); x < Math.min(w, b.x + b.w + R); x++) {
        if (trongChu(x, y)) continue;
        const i = (y * w + x) * 4;
        const L = 0.2126 * rgba[i] + 0.7152 * rgba[i + 1] + 0.0722 * rgba[i + 2];
        if (L >= 200) continue;                      // không phải mực
        const dx = x < b.x ? b.x - x : x > b.x + b.w ? x - b.x - b.w : 0;
        const dy = y < b.y ? b.y - y : y > b.y + b.h ? y - b.y - b.h : 0;
        const d = Math.hypot(dx, dy);
        if (d < gan2) gan2 = d;
      }
    }
    ra.push({ ky: b.ky, kc: Number.isFinite(gan2) ? Number((gan2 / tiLe).toFixed(2)) : null });
  }
  return ra;
}

/** Bề rộng đoạn chuyển 10→90 % qua mép nét đậm, nội suy dưới điểm ảnh. */
function doSac(anh, { camHop = [], tiLe = 1 } = {}) {
  const { w, h, rgba } = anh;
  const L = (x, y) => {
    const i = (y * w + x) * 4;
    return 0.2126 * rgba[i] + 0.7152 * rgba[i + 1] + 0.0722 * rgba[i + 2];
  };
  const mucDam = (() => {
    const m = [1, 3, 5].map((k) => parseInt(TOKEN.mau.mesh.slice(k, k + 2), 16));
    return 0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2];
  })();
  const bi = (x, y) => camHop.some((r) =>
    x >= r.x * tiLe - 4 && x <= (r.x + r.w) * tiLe + 4
    && y >= r.y * tiLe - 4 && y <= (r.y + r.h) * tiLe + 4);
  const R = Math.max(6, Math.round(7 * tiLe));
  const cat = (muc, mau) => {
    for (let t = 0; t < mau.length - 1; t++) {
      if (mau[t] >= muc && mau[t + 1] < muc) {
        const d = mau[t] - mau[t + 1];
        return d > 1e-6 ? t + (mau[t] - muc) / d : t;
      }
    }
    return null;
  };
  const ra = [];
  for (let y = R + 2; y < h - R - 2; y += 2) {
    for (let x = R + 2; x < w - 2 * R - 2; x++) {
      if (bi(x, y) || !(L(x, y) > 245)) continue;
      let sach = true;
      for (let t = 1; t <= R; t++) if (L(x - t, y) < 240) { sach = false; break; }
      if (!sach) continue;
      const mau = [];
      for (let t = 0; t <= R; t++) mau.push(L(x + t, y));
      const thap = Math.min(...mau);
      if (thap > mucDam + 16) continue;
      const cao = mau[0];
      const t90 = cat(thap + (cao - thap) * 0.9, mau);
      const t10 = cat(thap + (cao - thap) * 0.1, mau);
      if (t90 === null || t10 === null || t10 <= t90) continue;
      ra.push(t10 - t90);
      x += R;
    }
  }
  ra.sort((a, b) => a - b);
  return ra.length
    ? { so: ra.length, anhPx: Number(ra[ra.length >> 1].toFixed(3)),
      cssPx: Number((ra[ra.length >> 1] / tiLe).toFixed(3)) }
    : { so: 0, anhPx: null, cssPx: null };
}

const DOC_NHAN = "(function(){var c=document.querySelector('.geo3d-canvas canvas');"
  + "if(!c)return '{\"nhan\":[],\"tong\":0}';var rc=c.getBoundingClientRect();"
  + "var ra=[];var ns=document.querySelectorAll('.geo3d-label');var giau=0;"
  + "for(var i=0;i<ns.length;i++){var e=ns[i];"
  + "if(getComputedStyle(e).opacity==='0'){giau++;continue;}"
  + "var r=e.getBoundingClientRect();"
  + "ra.push({ky:e.textContent,x:r.x-rc.x,y:r.y-rc.y,w:r.width,h:r.height});}"
  + "var phu=[];var ps=document.querySelectorAll('.geo3d-readout, .geo3d button,"
  + " .geo3d-canvas button');"
  + "for(var j=0;j<ps.length;j++){var q=ps[j].getBoundingClientRect();"
  + " if(q.width<1)continue;"
  + " phu.push({x:q.x-rc.x,y:q.y-rc.y,w:q.width,h:q.height});}"
  + "return JSON.stringify({nhan:ra,tong:ns.length,giau:giau,phu:phu});})()";

const DOC_CO = "(function(){var c=document.querySelector('.geo3d-canvas canvas');"
  + "if(!c)return 'null';var r=c.getBoundingClientRect();"
  + "return JSON.stringify({hop:{x:r.x,y:r.y,width:r.width,height:r.height},"
  + "css:[c.clientWidth,c.clientHeight],buf:[c.width,c.height],"
  + "dpr:window.devicePixelRatio});})()";

async function moPhien(cong, rong, cao, dsf) {
  const sess = new BrowserSession({ viewport: rong, height: cao, webgl: true,
    url: `http://127.0.0.1:${cong}`, napModuleDev: false });
  await sess.open();
  await sess._send("Network.enable", {});
  await sess._send("Network.setCacheDisabled", { cacheDisabled: true });
  await sess._send("Emulation.setDeviceMetricsOverride",
    { width: rong, height: cao, deviceScaleFactor: dsf, mobile: rong < 500 });
  await sess._send("Page.reload", {});
  await sleep(2400);
  return sess;
}
async function nap(sess, env, buoc = -1) {
  await sess.eval(`(function(){window.__ALGO_SIM_STORE__.getState()`
    + `.loadEnvelope(${JSON.stringify(env)});return 1})()`);
  await sleep(1700);
  const soBuoc = async () => {
    const t = String(await sess.eval(
      "(function(){var e=document.querySelector('.geo3d-progress');return e?e.textContent:'';})()"));
    const m = /(\d+)\s*\/\s*(\d+)/.exec(t);
    return m ? { nay: +m[1], tong: +m[2] } : null;
  };
  for (let i = 0; i < 40; i++) {
    const b = await soBuoc();
    if (!b) break;
    const dich = buoc === -1 ? b.tong : buoc;
    if (b.nay >= dich) break;
    await sess.eval("(function(){var b=document.querySelector('[aria-label=\"Bước sau\"]');"
      + "if(b&&!b.disabled)b.click();return 1})()");
    await sleep(130);
  }
  await sleep(800);
  return soBuoc();
}
async function chup(sess, hop) {
  const { result } = await sess._send("Page.captureScreenshot",
    { format: "png", clip: { ...hop, scale: 1 } });
  return Buffer.from(result.data, "base64");
}

async function chay() {
  if (!CO["bo-qua-build"]) {
    execFileSync("npm", ["run", "build"], { cwd: FE, stdio: "inherit", shell: true });
  }
  kiemDistMoi();
  mkdirSync(RA, { recursive: true });
  const tags = String(CO.ca ?? "p1,p2,p3,p4,p5,p6,p7").split(",");
  const KHUNG = [
    { ten: "desktop", w: 1440, h: 900, hep: false },
    { ten: "mobile", w: 390, h: 844, hep: true },
  ];
  const { sv, cong } = await phucVu(DIST);
  const kq = {
    chay_luc: new Date().toISOString(), tiem: TIEM, nguong: NGUONG, ca: [], sac: [],
  };

  try {
    for (const kh of KHUNG) {
      for (const dsf of [1, 2]) {
        const sess = await moPhien(cong, kh.w, kh.h, dsf);
        for (const tag of tags) {
          const hang = { tag, khung: kh.ten, dsf, trangThai: TRANG_THAI.DAT };
          try {
            await nap(sess, envCa(tag));
            const co = JSON.parse(await sess.eval(DOC_CO));
            if (!co) { hang.trangThai = TRANG_THAI.KHONG_DUNG_DUOC; kq.ca.push(hang); continue; }
            const buf = await chup(sess, co.hop);
            const anh = docPNG(buf);
            const tiLe = anh.w / co.css[0];
            const nh = JSON.parse(await sess.eval(DOC_NHAN));

            Object.assign(hang, {
              css: co.css, buf: co.buf, anhCo: [anh.w, anh.h], dpr: co.dpr,
              soNhan: nh.nhan.length, nhanGiau: nh.giau ?? 0,
            });

            /* ① BẤT BIẾN DPR. Trần 2 khai ở `scene3d-tokens`/`scene3d-wide-line`. */
            const mong = Math.max(1, Math.min(co.dpr, 2));
            const bufDung = Math.abs(co.buf[0] - co.css[0] * mong) <= NGUONG.BUFFER_SAI_SO
              && Math.abs(co.buf[1] - co.css[1] * mong) <= NGUONG.BUFFER_SAI_SO;
            /* Cỡ CSS của canvas không được vượt khung bao nó — dấu hiệu đã bật
               `setPixelRatio` mà quên `updateStyle`, và `overflow: hidden` đang
               giấu chỗ vỡ. */
            const cssDung = co.css[0] <= kh.w + 2;
            hang.dprMong = mong;
            if (!cssDung) hang.trangThai = TRANG_THAI.DPR_CSS_PHINH;
            else if (!bufDung) hang.trangThai = TRANG_THAI.DPR_BUFFER_SAI;

            /* ③ NHÃN — giấu, tràn lề, và khoảng cách tới mực. */
            const kc = kcNhanToiMuc(anh, nh.nhan, { tiLe, phu: nh.phu ?? [] });
            hang.kcNhan = kc;
            const nguongNet = kh.hep ? NGUONG.NHAN_NET_HEP : NGUONG.NHAN_NET_RONG;
            hang.kcNhanMin = kc.length
              ? Math.min(...kc.map((x) => (x.kc === null ? Infinity : x.kc))) : null;
            const le = nh.nhan.length
              ? Math.min(...nh.nhan.map((n) => Math.min(
                n.x, n.y, co.css[0] - (n.x + n.w), co.css[1] - (n.y + n.h)))) : null;
            hang.leMin = le === null ? null : Number(le.toFixed(2));
            /* Lớp phủ CHE nhãn — hộp CHỒNG nhau, không phải nằm gần. */
            const chongNhau = (a, b) => a.x < b.x + b.w && a.x + a.w > b.x
              && a.y < b.y + b.h && a.y + a.h > b.y;
            hang.nhanBiChe = nh.nhan
              .filter((n) => (nh.phu ?? []).some((q) => chongNhau(n, q)))
              .map((n) => n.ky);
            if (hang.trangThai === TRANG_THAI.DAT) {
              if (hang.nhanBiChe.length > 0) hang.trangThai = TRANG_THAI.NHAN_BI_CHE;
              else if ((nh.giau ?? 0) > 0) hang.trangThai = TRANG_THAI.NHAN_BI_GIAU;
              else if (le !== null && le < NGUONG.LE) hang.trangThai = TRANG_THAI.NHAN_TRAN_LE;
              else if (hang.kcNhanMin !== null && Number.isFinite(hang.kcNhanMin)
                && hang.kcNhanMin < nguongNet) hang.trangThai = TRANG_THAI.NHAN_QUA_SAT_NET;
            }

            /* Bề dày theo vai — phép đo đã hiệu chuẩn, đọc token từ nguồn. */
            if (dsf === 1) {
              const camHop = [...nh.nhan, ...(nh.phu ?? [])]
                .map((n) => ({ x: n.x - 3, y: n.y - 3, w: n.w + 6, h: n.h + 6 }));
              hang.beDayCanhThay = doBeDayVuongGoc(anh,
                { mauVai: TOKEN.mau.mesh, loaiTru: camHop }).p25;
            }

            /* ② ĐỘ SẮC — gom để so DPR1 với DPR2 sau. */
            const camHop = [...nh.nhan, ...(nh.phu ?? [])]
              .map((n) => ({ x: n.x - 3, y: n.y - 3, w: n.w + 6, h: n.h + 6 }));
            const sac = doSac(anh, { camHop, tiLe });
            kq.sac.push({ tag, khung: kh.ten, dsf, ...sac });
            hang.sacCss = sac.cssPx;

            writeFileSync(join(RA, `d2-${tag}-${kh.ten}-dpr${dsf}.png`), buf);
          } catch (e) {
            hang.trangThai = TRANG_THAI.KHONG_DUNG_DUOC;
            hang.loi = String(e && e.message ? e.message : e);
          }
          kq.ca.push(hang);
          console.log(`  ${tag} ${kh.ten} dpr${dsf}: ${hang.trangThai}`
            + `  css=${JSON.stringify(hang.css)} buf=${JSON.stringify(hang.buf)}`
            + `  nhãn=${hang.soNhan}(giấu ${hang.nhanGiau})`
            + `  kc=${hang.kcNhanMin} lề=${hang.leMin} sắc=${hang.sacCss}`);
        }
        await sess.close();
      }
    }

    /* ② so độ sắc: DPR 2 phải hẹp hơn DPR 1 (tính theo pixel CSS). */
    for (const kh of ["desktop", "mobile"]) {
      const d1 = kq.sac.filter((s) => s.khung === kh && s.dsf === 1 && s.cssPx);
      const d2 = kq.sac.filter((s) => s.khung === kh && s.dsf === 2 && s.cssPx);
      if (!d1.length || !d2.length) continue;
      const tb = (a) => a.reduce((t, x) => t + x.cssPx, 0) / a.length;
      const t1 = tb(d1), t2 = tb(d2);
      const dat = t1 / t2 >= NGUONG.SAC_TOT_HON;
      kq[`sac_${kh}`] = { dpr1: +t1.toFixed(3), dpr2: +t2.toFixed(3),
        tiSo: +(t1 / t2).toFixed(2), dat };
      if (!dat) {
        kq.ca.push({ tag: "(tổng)", khung: kh, dsf: 2,
          trangThai: TRANG_THAI.NET_KHONG_SAC_HON });
      }
      console.log(`  độ sắc ${kh}: DPR1 ${t1.toFixed(3)} px CSS → DPR2 ${t2.toFixed(3)}`
        + `  (hẹp hơn ${(t1 / t2).toFixed(2)}×) ${dat ? "ĐẠT" : "CHƯA ĐẠT"}`);
    }
  } finally {
    sv.close();
  }

  kq.dat = kq.ca.every((c) => c.trangThai === TRANG_THAI.DAT);
  const ten = TIEM ? `D2_GATE_TIEM_${TIEM}.json` : "D2_GATE.json";
  writeFileSync(join(RA, ten), JSON.stringify(kq, null, 2), "utf-8");
  console.log(`→ ${join(RA, ten)}  ${kq.dat ? "ĐẠT" : "KHÔNG ĐẠT"}`);
  return kq.dat;
}

if (import.meta.filename === process.argv[1]) {
  chay().then((ok) => { process.exitCode = ok ? 0 : 1; })
    .catch((e) => { console.error(e); process.exitCode = 2; });
}
