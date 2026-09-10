/**
 * png-pixels.mjs — giải mã PNG và ĐO BỀ DÀY NÉT TỪ ĐIỂM ẢNH.
 *
 * ─── VÌ SAO TỒN TẠI ───────────────────────────────────────────────────────
 *
 * Token thị giác khai cạnh thấy 2,8 px. Nhưng renderer vẽ cạnh khối bằng
 * `THREE.Line`, và **WebGL bỏ qua `linewidth`** — nên giá trị trong mã không
 * nói gì về thứ hiện trên màn hình. Đọc `linewidth` rồi tuyên bố "2,8 px" là
 * đúng loại tự lừa mà kho này đã trả giá: đo BỘ ĐO chứ không đo HỆ.
 *
 * Nên bề dày phải đo trên **ảnh chụp thật của canvas**. Tệp này làm đúng một
 * việc đó, và cố ý KHÔNG biết gì về three.js hay về renderer.
 *
 * ─── VÌ SAO KHÔNG ĐẾM ĐIỂM ẢNH THÔ ───────────────────────────────────────
 *
 * Nét có khử răng cưa, nên một cạnh 1 px thật có thể trải ra 2–3 điểm ảnh mờ.
 * Đếm "điểm ảnh có màu" sẽ báo 2–3 px cho một nét 1 px. Ở đây dùng **tích phân
 * độ phủ**: cộng phần mực trên mỗi lát cắt, rồi nhân với `|sin α|` của cạnh để
 * quy về bề dày VUÔNG GÓC. Một nét 1 px thật cho ~1,0 dù trải trên ba điểm ảnh.
 */
import { inflateSync } from "node:zlib";

// ───────────────────────────── PNG ─────────────────────────────
/** Giải mã PNG 8-bit không xen kẽ → { w, h, rgba: Uint8Array }. */
export function docPNG(buf) {
  if (buf.readUInt32BE(0) !== 0x89504e47) throw new Error("không phải PNG");
  let p = 8, w = 0, h = 0, bitDepth = 0, colorType = 0, interlace = 0;
  const idat = [];
  while (p < buf.length) {
    const len = buf.readUInt32BE(p);
    const typ = buf.toString("ascii", p + 4, p + 8);
    const data = buf.subarray(p + 8, p + 8 + len);
    if (typ === "IHDR") {
      w = data.readUInt32BE(0); h = data.readUInt32BE(4);
      bitDepth = data[8]; colorType = data[9]; interlace = data[12];
    } else if (typ === "IDAT") idat.push(data);
    else if (typ === "IEND") break;
    p += 12 + len;
  }
  if (bitDepth !== 8) throw new Error(`bitDepth ${bitDepth} chưa hỗ trợ`);
  if (interlace !== 0) throw new Error("PNG xen kẽ chưa hỗ trợ");
  const kenh = { 0: 1, 2: 3, 4: 2, 6: 4 }[colorType];
  if (!kenh) throw new Error(`colorType ${colorType} chưa hỗ trợ`);

  const raw = inflateSync(Buffer.concat(idat));
  const bpp = kenh;
  const stride = w * bpp;
  const out = new Uint8Array(w * h * 4);
  const truoc = new Uint8Array(stride);
  const hien = new Uint8Array(stride);
  let q = 0;
  for (let y = 0; y < h; y++) {
    const loc = raw[q++];
    raw.copy(hien, 0, q, q + stride); q += stride;
    for (let i = 0; i < stride; i++) {
      const a = i >= bpp ? hien[i - bpp] : 0;
      const b = truoc[i];
      const c = i >= bpp ? truoc[i - bpp] : 0;
      let v = hien[i];
      if (loc === 1) v += a;
      else if (loc === 2) v += b;
      else if (loc === 3) v += (a + b) >> 1;
      else if (loc === 4) {
        const pa = Math.abs(b - c), pb = Math.abs(a - c), pc = Math.abs(a + b - 2 * c);
        v += (pa <= pb && pa <= pc) ? a : (pb <= pc ? b : c);
      }
      hien[i] = v & 0xff;
    }
    for (let x = 0; x < w; x++) {
      const s = x * bpp, d = (y * w + x) * 4;
      if (kenh === 1) { out[d] = out[d + 1] = out[d + 2] = hien[s]; out[d + 3] = 255; }
      else if (kenh === 2) { out[d] = out[d + 1] = out[d + 2] = hien[s]; out[d + 3] = hien[s + 1]; }
      else if (kenh === 3) { out[d] = hien[s]; out[d + 1] = hien[s + 1]; out[d + 2] = hien[s + 2]; out[d + 3] = 255; }
      else { out[d] = hien[s]; out[d + 1] = hien[s + 1]; out[d + 2] = hien[s + 2]; out[d + 3] = hien[s + 3]; }
    }
    truoc.set(hien);
  }
  return { w, h, rgba: out };
}

const hex = (s) => [1, 3, 5].map((i) => parseInt(s.slice(i, i + 2), 16));
const luma = ([r, g, b]) => 0.2126 * r + 0.7152 * g + 0.0722 * b;

/** Ảnh có phải một mảng phẳng không (dùng cho WEBGL_FRAME_NONBLANK). */
export function anhPhang(anh, nguong = 12) {
  const { w, h, rgba } = anh;
  let min = 255, max = 0, n = 0, tong = 0;
  for (let y = 0; y < h; y += 3) {
    for (let x = 0; x < w; x += 3) {
      const l = luma([rgba[(y * w + x) * 4], rgba[(y * w + x) * 4 + 1], rgba[(y * w + x) * 4 + 2]]);
      min = Math.min(min, l); max = Math.max(max, l); tong += l; n++;
    }
  }
  return { phang: max - min < nguong, min: +min.toFixed(1), max: +max.toFixed(1), trungBinh: +(tong / n).toFixed(1) };
}

/**
 * Đo bề dày VUÔNG GÓC của những nét mang màu `mauHex` trên nền `nenHex`.
 *
 * Cách làm, từng bước, để người đọc kiểm được:
 *  ① mỗi HÀNG điểm ảnh: tìm các đoạn liên tiếp có "độ phủ" > 0 với màu đích;
 *  ② nối các đoạn ở hàng liền nhau thành một CẠNH (tâm trôi < `troiToiDa`);
 *  ③ mỗi cạnh: `bề dày = trung vị(mực mỗi lát) × |sin α|`, với `α` là góc giữa
 *     cạnh và phương ngang, suy từ độ trôi của tâm.
 *
 * Loại bỏ (theo đúng chỉ thị §9): cạnh quá ngắn, cạnh gần như NGANG (|sin α|
 * nhỏ ⇒ chia cho số bé, sai số nổ), và các lát có mực lệch quá xa trung vị —
 * đó là chỗ có giao điểm, đầu mút hoặc nhãn đè lên.
 */
export function doBeDayNet(anh, {
  mauHex, nenHex = "#FAF9F7", dungSai = 62, daiToiThieu = 22,
  troiToiDa = 2.2, sinToiThieu = 0.55, vung = null, loiToiThieu = 0.35, loaiTru = [],
} = {}) {
  const { w, h, rgba } = anh;
  const dich = hex(mauHex), nen = hex(nenHex);
  const lDich = luma(dich), lNen = luma(nen);
  const x0 = vung?.x0 ?? 0, x1 = vung?.x1 ?? w, y0 = vung?.y0 ?? 0, y1 = vung?.y1 ?? h;

  /* Vùng phải BỎ QUA: nhãn điểm và nút DOM nằm ĐÈ lên canvas, và chữ của
   * nhãn gần như cùng màu với cạnh thấy (#171717 vs #1F1F1F) — đo trên ảnh
   * còn nhãn thì bộ đo trả về độ dày THÂN CHỮ. Đo thật lượt đầu: 15,3 px.
   * Không ẩn chúng bằng CSS: một lượt thử làm vậy khiến canvas WebGL trắng
   * trơn (đổi style → dựng lại → chưa kịp vẽ), tức bộ đo tự phá thứ nó đo. */
  const trongVungCam = (x, y) => loaiTru.some((r) =>
    x >= r.x - 3 && x <= r.x + r.w + 3 && y >= r.y - 3 && y <= r.y + r.h + 3);

  /** Độ phủ mực của một điểm ảnh với màu đích: 0 = nền, 1 = đúng màu đích. */
  const phu = (x, y) => {
    if (trongVungCam(x, y)) return 0;
    const i = (y * w + x) * 4;
    const px = [rgba[i], rgba[i + 1], rgba[i + 2]];
    // Điểm ảnh phải nằm trên đoạn nền→đích, không lệch sang màu khác.
    const t = (lNen - luma(px)) / (lNen - lDich);
    if (!(t > 0.06)) return 0;
    const kv = [0, 1, 2].map((k) => nen[k] + (dich[k] - nen[k]) * Math.min(1, t));
    const d = Math.hypot(px[0] - kv[0], px[1] - kv[1], px[2] - kv[2]);
    return d > dungSai ? 0 : Math.min(1, t);
  };

  // ① đoạn theo hàng
  const hang = [];
  for (let y = y0; y < y1; y++) {
    const ds = [];
    let bat = -1, muc = 0, tamTong = 0, loi = 0;
    for (let x = x0; x < x1; x++) {
      const c = phu(x, y);
      if (c > 0) {
        if (bat < 0) { bat = x; muc = 0; tamTong = 0; loi = 0; }
        muc += c; tamTong += c * x; loi = Math.max(loi, c);
      } else if (bat >= 0) {
        ds.push({ bat, ket: x - 1, muc, loi, tam: tamTong / muc });
        bat = -1;
      }
    }
    if (bat >= 0) ds.push({ bat, ket: x1 - 1, muc, loi, tam: tamTong / muc });
    /* ⚠️ LỌC THEO LÕI, và ngưỡng 0,35 là con số đã tính chứ không phải ước.
     * Một nét 1 px khử răng cưa, xấu nhất, rơi đúng giữa hai điểm ảnh và cho
     * hai điểm 0,50 — nên ngưỡng phải DƯỚI 0,5, nếu không bộ đo mù đúng cái ca
     * nó sinh ra để phát hiện (thử với ngưỡng 0,55: nét 1 px cho 0 mẫu).
     * Mảng tô đậm nhất trong cảnh là nền thiết diện 0,14 ⇒ 0,35 vẫn loại sạch.
     *
     * ⚠️ Vì sao cần lọc: mặt khối tô 0,07 và nền thiết diện tô 0,14 nằm ĐÚNG
     * trên đoạn nền→màu nét, nên không lọc thì bộ đo nhặt cả mảng tô và trả ra
     * những con số vô nghĩa — đo thật trên cùng một ảnh: trung vị 0,09 px và
     * max 45 px. Một NÉT luôn có ít nhất một điểm ảnh lõi gần đặc; một mảng tô
     * mờ thì không bao giờ. */
    hang.push({ y, ds: ds.filter((d) => d.loi >= loiToiThieu) });
  }

  // ② nối thành cạnh
  const canh = [];
  let dangMo = [];
  for (const { y, ds } of hang) {
    const moi = [];
    for (const d of ds) {
      const noi = dangMo.find((c) => Math.abs(c.tamCuoi - d.tam) <= troiToiDa && c.yCuoi === y - 1);
      if (noi) { noi.lat.push(d); noi.tamCuoi = d.tam; noi.yCuoi = y; moi.push(noi); }
      else moi.push({ lat: [d], tamDau: d.tam, tamCuoi: d.tam, yDau: y, yCuoi: y });
    }
    for (const c of dangMo) if (!moi.includes(c)) canh.push(c);
    dangMo = moi;
  }
  canh.push(...dangMo);

  // ③ bề dày
  const mau = [];
  for (const c of canh) {
    const n = c.lat.length;
    if (n < daiToiThieu) continue;
    const dy = c.yCuoi - c.yDau, dx = c.tamCuoi - c.tamDau;
    const sin = Math.abs(dy) / Math.hypot(dx, dy);
    if (!(sin >= sinToiThieu)) continue;                 // gần ngang ⇒ bỏ
    const mucs = c.lat.map((l) => l.muc).sort((a, b) => a - b);
    const tv = mucs[Math.floor(mucs.length / 2)];
    const giu = c.lat.filter((l) => Math.abs(l.muc - tv) <= 0.4 * tv);   // bỏ giao điểm/nhãn
    if (giu.length < daiToiThieu) continue;
    for (const l of giu) mau.push(l.muc * sin);
  }

  mau.sort((a, b) => a - b);
  if (mau.length === 0) return { soMau: 0, trungVi: null, min: null, max: null };
  return {
    soMau: mau.length,
    trungVi: +mau[Math.floor(mau.length / 2)].toFixed(2),
    min: +mau[0].toFixed(2),
    max: +mau[mau.length - 1].toFixed(2),
    p25: +mau[Math.floor(mau.length * 0.25)].toFixed(2),
    p75: +mau[Math.floor(mau.length * 0.75)].toFixed(2),
  };
}

/** Ảnh tổng hợp để tự kiểm bộ đo: các nét dọc bề dày biết trước. */
export function anhThu(beDay, { w = 200, h = 120, mauHex = "#1F1F1F", nenHex = "#FAF9F7" } = {}) {
  const nen = hex(nenHex), dich = hex(mauHex);
  const rgba = new Uint8Array(w * h * 4);
  for (let i = 0; i < w * h; i++) {
    rgba[i * 4] = nen[0]; rgba[i * 4 + 1] = nen[1]; rgba[i * 4 + 2] = nen[2]; rgba[i * 4 + 3] = 255;
  }
  const tam = w / 2;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      // Độ phủ của một dải dọc rộng `beDay` quanh `tam`, có khử răng cưa.
      const c = Math.max(0, Math.min(1,
        Math.min(x + 1, tam + beDay / 2) - Math.max(x, tam - beDay / 2)));
      if (c <= 0) continue;
      const i = (y * w + x) * 4;
      for (let k = 0; k < 3; k++) rgba[i + k] = Math.round(nen[k] + (dich[k] - nen[k]) * c);
    }
  }
  return { w, h, rgba };
}

/**
 * Bề dày nét đo bằng NỀN CỤC BỘ — bản dùng cho ảnh sản phẩm thật.
 *
 * ⚠️ Vì sao cần bản thứ hai. `doBeDayNet` phân loại theo màu TUYỆT ĐỐI, và
 * trên ảnh sản phẩm nó vỡ: mặt khối tô mờ, miếng mặt phẳng, vật `noiBat` tô
 * xanh và nền chuyển màu làm "nền" không còn là một hằng số. Đo thật bằng bản
 * ấy trả về những con số vô nghĩa trên cùng một ảnh — 0,09 px, 12 px, 112 px.
 *
 * Bản này không hỏi màu. Nó tìm CỰC TIỂU ĐỘ SÁNG so với nền NGAY CẠNH nó, rồi
 * lấy bề rộng ở nửa độ sâu (FWHM). Một nét, dù nằm trên nền nào, vẫn là một
 * chỗ lõm cục bộ; một mảng tô thì không có chỗ lõm.
 */
export function doBeDayCucBo(anh, {
  sauToiThieu = 22, cuaSo = 7, daiToiThieu = 10, buoc = 1,
  loaiTru = [], vung = null, mauLoc = null, dungSaiMau = 70,
} = {}) {
  const { w, h, rgba } = anh;
  const x0 = vung?.x0 ?? 0, x1 = vung?.x1 ?? w, y0 = vung?.y0 ?? 0, y1 = vung?.y1 ?? h;
  const L = (x, y) => { const i = (y * w + x) * 4;
    return 0.2126 * rgba[i] + 0.7152 * rgba[i + 1] + 0.0722 * rgba[i + 2]; };
  const cam = (x, y) => loaiTru.some((r) =>
    x >= r.x - 3 && x <= r.x + r.w + 3 && y >= r.y - 3 && y <= r.y + r.h + 3);
  const hopMau = (x, y) => {
    if (!mauLoc) return true;
    const i = (y * w + x) * 4;
    const m = [1, 3, 5].map((k) => parseInt(mauLoc.slice(k, k + 2), 16));
    return Math.hypot(rgba[i] - m[0], rgba[i + 1] - m[1], rgba[i + 2] - m[2]) <= dungSaiMau;
  };

  const mau = [];
  for (let y = y0 + cuaSo; y < y1 - cuaSo; y += buoc) {
    for (let x = x0 + cuaSo; x < x1 - cuaSo; x++) {
      if (cam(x, y)) continue;
      const l = L(x, y);
      if (!(l <= L(x - 1, y) && l < L(x + 1, y))) continue;      // cực tiểu cục bộ
      // Nền cục bộ = mức sáng nhất trong cửa sổ hai bên.
      let nenT = 0, nenP = 0;
      for (let d = 1; d <= cuaSo; d++) {
        nenT = Math.max(nenT, L(x - d, y)); nenP = Math.max(nenP, L(x + d, y));
      }
      const nen = Math.min(nenT, nenP);
      const sau = nen - l;
      if (sau < sauToiThieu) continue;
      if (!hopMau(x, y)) continue;
      /* TÍCH PHÂN MỰC trên nền cục bộ, không phải FWHM.
       *
       * FWHM tính bằng số điểm ảnh NGUYÊN nên nó bão hoà: thử với nét tổng
       * hợp 1 / 1,6 / 2,8 px đều trả về đúng "2". Một phép đo không phân biệt
       * được 1 px với 2,8 px thì vô dụng cho đúng câu hỏi của wave này.
       *
       * Mực = Σ (nền − sáng) / (nền − đáy). Nét phủ trọn một điểm ảnh đóng góp
       * 1,0; nét mảnh hơn một điểm ảnh đóng góp phần lẻ. */
      let t = x, p = x;
      while (t > x0 && L(t - 1, y) < nen - 2 && x - t < cuaSo) t--;
      while (p < x1 - 1 && L(p + 1, y) < nen - 2 && p - x < cuaSo) p++;
      let muc = 0;
      for (let k = t; k <= p; k++) muc += Math.max(0, (nen - L(k, y)) / sau);
      mau.push(muc);
    }
  }
  mau.sort((a, b) => a - b);
  if (mau.length < daiToiThieu) return { soMau: mau.length, trungVi: null, min: null, max: null };
  return {
    soMau: mau.length,
    trungVi: +mau[Math.floor(mau.length / 2)].toFixed(2),
    p25: +mau[Math.floor(mau.length * 0.25)].toFixed(2),
    p75: +mau[Math.floor(mau.length * 0.75)].toFixed(2),
    min: mau[0], max: mau[mau.length - 1],
  };
}
