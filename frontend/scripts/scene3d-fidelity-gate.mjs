/**
 * scene3d-fidelity-gate.mjs — CỔNG TRUNG THỰC THỊ GIÁC trên bản dựng sản phẩm.
 *
 * ─── NÓ TRẢ LỜI CÂU GÌ ────────────────────────────────────────────────────
 *
 * `scene3d-orbit-gate.mjs` hỏi *"quay được hết hình không"*. Cổng này hỏi
 * *"hình vẽ ra có đúng ngôn ngữ thị giác đã duyệt không"* — và nó chỉ tin
 * **điểm ảnh của canvas sản phẩm**, không tin một hằng số nào trong mã. Lý do
 * cụ thể: bảng token khai *"cạnh thấy 2,8 px"* trong khi WebGL bỏ qua
 * `linewidth`, nên suốt một thời gian mã nói 2,8 mà màn hình vẽ 1,0.
 *
 * ─── BỐN PHÉP ĐO, VÀ VÌ SAO TỪNG PHÉP ────────────────────────────────────
 *
 *  ① **Mực và tràn khung.** Cảnh rỗng vẫn "không có lỗi" — cổng cũ từng PASS
 *    7/7 trên bảy ảnh chỉ có năm chấm đen. Nên phải đo có bao nhiêu mực, và
 *    mực có chạm mép canvas không.
 *  ② **Vai màu.** Đếm điểm ảnh gần `#D95A43` (thiết diện phải có) và gần
 *    `#0075DE` (chưa chọn gì thì KHÔNG được có điểm nào).
 *  ③ **Bề dày nét**, bằng tích phân mực trên nền cục bộ, loại vùng chữ.
 *  ④ **Nhãn**, đọc thẳng từ DOM: cỡ chữ, độ đậm, nằm trong khung, không đè.
 *
 * ⚠️ Backtick KHÔNG được xuất hiện trong chuỗi tiêm vào trang.
 */
import { readFileSync, writeFileSync, mkdirSync, readdirSync, statSync, existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join, resolve } from "node:path";
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { phucVu } from "./scene3d-orbit-gate.mjs";
import { docPNG, doBeDayVuongGoc } from "./png-pixels.mjs";

const CO = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, ds) => {
  if (x.startsWith("--")) a.push([x.slice(2), ds[i + 1]?.startsWith("--") ? true : ds[i + 1] ?? true]);
  return a;
}, []));
const GOC = resolve(CO.goc ?? join(import.meta.dirname, "..", ".."));
const FE = join(GOC, "frontend");
const DIST = join(FE, "dist");
const RA = resolve(CO.ra ?? join(GOC, "docs", "evaluation", "geometry", "scene3d-fidelity"));
const ANH = resolve(CO.anh ?? "D:/tmp/algosim-fidelity/gate");
const TAGS = (CO.ca ?? "p1,p2,p3,p4,p5,p6,p7").split(",");
const TIEM = CO.tiem ? String(CO.tiem) : null;

/** Ngưỡng khai TRƯỚC khi đo. Không nới sau khi thấy số. */
export const NGUONG = {
  /** Tỉ lệ điểm ảnh có mực tối thiểu — dưới mức này coi như cảnh rỗng. */
  MUC_TOI_THIEU: 0.004,
  /**
   * Độ sáng dưới mức này mới tính là MỰC.
   *
   * ⚠️ Không đặt gần nền được. Nền của khung là một gradient nhạt chạy từ
   * `L ≈ 227` ở giữa tới `L ≈ 248` ở góc, và mảng tô khối (opacity 0,07) rơi
   * vào `L ≈ 230` — tức **nền và mảng tô nằm cùng một dải**. Lượt chạy đầu để
   * ngưỡng 232 và đọc ra `chiếm = 0,999` ở mọi ca: cổng đang đo nền, không đo
   * hình. 200 nằm dưới hẳn dải nền và trên hẳn mọi nét (đen 31, xám khuất 120,
   * cam thiết diện 110), nên nó đo đúng thứ định nghĩa hình: NÉT.
   */
  MUC_SANG_TOI_DA: 200,
  /** Bề rộng/chiều cao hình so với canvas. */
  CHIEM_MIN: 0.18,
  CHIEM_MAX: 0.92,
  /** Cạnh thấy: token D2 = 2,4 px. Dải quanh nó, đo bằng . */
  CANH_THAY_MIN: 1.6,
  CANH_THAY_MAX: 3.4,
  /** Điểm ảnh xanh chọn khi CHƯA chọn gì — phải bằng 0. */
  XANH_TOI_DA: 0,
  /** Số nhãn ra ngoài khung / đè nhau tối đa. */
  NHAN_LOI_TOI_DA: 0,
  /** Mực ĐẬM tối thiểu để coi là khối cong có đường bao. Chấm điểm chỉ vài
   *  chục điểm ảnh, nên ngưỡng này bỏ xa chúng. */
  BAO_TOI_THIEU: 400,
  /** Tỉ lệ điểm ảnh nét khuất phải ĐỔI CHỖ sau một cú xoay. */
  DOI_CHO_KHUAT_MIN: 0.35,
};

export const TRANG_THAI = {
  DAT: "DAT",
  CANH_RONG: "CANH_RONG",
  TRAN_KHUNG: "TRAN_KHUNG",
  CHIEM_SAI: "CHIEM_SAI",
  THIEU_THIET_DIEN: "THIEU_THIET_DIEN",
  XANH_TU_DONG: "XANH_TU_DONG",
  NET_QUA_MANH: "NET_QUA_MANH",
  THIEU_DUONG_BAO: "THIEU_DUONG_BAO",
  NHAN_HONG: "NHAN_HONG",
  KHUAT_KHONG_DOI: "KHUAT_KHONG_DOI",
  KHONG_DUNG_DUOC: "KHONG_DUNG_DUOC",
};

/**
 * Khung một kết quả rỗng. Mọi lối THOÁT SỚM phải trả về đủ trường, nếu không
 * dòng in kết quả sẽ ném `undefined` và một phép tiêm ĐÃ BỊ BẮT lại hiện ra
 * như một script hỏng — mất luôn tên trạng thái.
 */
const CA_RONG = {
  canvas: null, tiLeMuc: 0, chiemNgang: 0, chiemDoc: 0, tran: false,
  diemCam: 0, diemXanh: 0, diemXam: 0, diemDam: 0,
  beDayTrungVi: 0, beDayP25: 0, beDayP75: 0, soMauBeDay: 0,
  nhan: { ngoai: 0, de: 0, soNhan: 0, ky: [] },
  kieuNhan: null, sauXoay: null, doiKhuat: 0, anh: null,
};

/** Ca nào PHẢI có thiết diện, ca nào PHẢI có đường bao khối cong. */
const CO_THIET_DIEN = new Set(["p1", "p3", "p6", "p7"]);
const CO_KHOI_CONG = new Set(["p3", "p4", "p5", "p6", "p7"]);

/**
 * Đọc bảng token D2 từ NGUỒN, không chép số vào đây.
 *
 * Cổng và renderer phải nói về cùng một bảng. Bản trước ghi cứng `#d95a43`,
 * `#7d7975`, `#1f1f1f`; khi vòng D2 đổi bảng màu thì cổng đếm hụt điểm ảnh xám
 * và báo `THIEU_DUONG_BAO` cho bốn ca hoàn toàn lành — một kết luận sai trông
 * y như một lỗi thật.
 *
 * Ném khi thiếu khoá: đổi tên một vai mà cổng im lặng đọc ra `undefined` còn
 * tệ hơn cổng đỏ.
 */
export function docTokenD2() {
  const f = join(import.meta.dirname, "..", "src", "simulations", "domains", "geometry",
    "scene3d-tokens.ts");
  const src = readFileSync(f, "utf-8");
  const hex = (ten) => {
    const m = new RegExp(String.raw`${ten}:\s*0x([0-9a-fA-F]{6})`).exec(src);
    if (!m) throw new Error(`TOKEN_THIEU — không thấy màu \`${ten}\` trong ${f}`);
    return `#${m[1].toLowerCase()}`;
  };
  const so = (ten) => {
    const m = new RegExp(String.raw`${ten}:\s*([0-9.]+)`).exec(src);
    if (!m) throw new Error(`TOKEN_THIEU — không thấy số \`${ten}\` trong ${f}`);
    return Number(m[1]);
  };
  return {
    mau: {
      mesh: hex("mesh"), khuat: hex("khuat"), section: hex("section"),
      sectionKhuat: hex("sectionKhuat"), line: hex("line"),
      surface: hex("surface"), highlight: hex("highlight"),
    },
    beDay: {
      canhThay: so("canhThay"), canhKhuat: so("canhKhuat"),
      thietDienThay: so("thietDienThay"),
    },
  };
}

export const TOKEN = docTokenD2();

const gan = (rgba, i, hex, dung) => {
  const m = [1, 3, 5].map((k) => parseInt(hex.slice(k, k + 2), 16));
  return Math.hypot(rgba[i] - m[0], rgba[i + 1] - m[1], rgba[i + 2] - m[2]) <= dung;
};

/**
 * Thống kê mực, tràn khung, độ chiếm, và đếm điểm ảnh theo vai màu.
 *
 * ⚠️ `loaiTru` là BẮT BUỘC, không phải tuỳ chọn cho đẹp. Hai nút "Tách khối" /
 * "Xem lại toàn hình" nằm ĐÈ LÊN canvas, nên nếu không loại thì mực của chúng
 * tính vào hình: lượt chạy đầu đọc ra `chiếm = 0,999` và mọi ca đều
 * `TRAN_KHUNG` — một kết luận sai trông y như một lỗi thật.
 */
export function doAnh(anh, { boTrai = 0, loaiTru = [] } = {}) {
  const { w, h, rgba } = anh;
  const cam0 = (x, y) => loaiTru.some((r) =>
    x >= r.x - 2 && x <= r.x + r.w + 2 && y >= r.y - 2 && y <= r.y + r.h + 2);
  let muc = 0, x0 = 1e9, x1 = -1, y0 = 1e9, y1 = -1, cam = 0, xanh = 0, xam = 0, dam = 0;
  let hx0 = 1e9, hx1 = -1, hy0 = 1e9, hy1 = -1;   // hộp bao HÌNH HỮU HẠN
  /* Mặt nạ NÉT KHUẤT, giữ theo vị trí. Xem `doiChoKhuat`. */
  const naKhuat = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) {
    for (let x = boTrai; x < w; x++) {
      if (cam0(x, y)) continue;
      const i = (y * w + x) * 4;
      const L = 0.2126 * rgba[i] + 0.7152 * rgba[i + 1] + 0.0722 * rgba[i + 2];
      if (gan(rgba, i, TOKEN.mau.section, 60)) cam += 1;
      if (gan(rgba, i, TOKEN.mau.highlight, 60)) xanh += 1;
      if (gan(rgba, i, TOKEN.mau.khuat, 26)) { xam += 1; naKhuat[y * w + x] = 1; }
      if (gan(rgba, i, TOKEN.mau.mesh, 26)) dam += 1;
      if (L < NGUONG.MUC_SANG_TOI_DA) {
        muc += 1;
        if (x < x0) x0 = x; if (x > x1) x1 = x;
        if (y < y0) y0 = y; if (y > y1) y1 = y;
        /* ─── HỘP BAO CỦA HÌNH HỮU HẠN, tách khỏi vật VÔ HẠN ────────────
         *
         * Mặt phẳng và đường thẳng là VÔ HẠN theo đúng dữ liệu; miếng vẽ ra
         * là đại diện do tầng trình bày chọn cỡ, và nó **cố ý** bị loại khỏi
         * phép khớp khung (`userData.voHan`) — nếu không, miếng to ra sẽ đẩy
         * camera lùi, hình thật bé lại, và vòng lặp ấy không có điểm dừng.
         * Nên mực của chúng chạm mép là hệ quả ĐÃ CHỌN, không phải hình bị
         * cắt. Đo được: mười ảnh chạm mép đều thuộc đúng bốn ca có vật vô hạn,
         * còn ba ca không có thì 0/18 ảnh chạm mép.
         *
         * Phân biệt bằng MÀU: hình hữu hạn là cạnh khối và thiết diện. */
        if (gan(rgba, i, TOKEN.mau.mesh, 40) || gan(rgba, i, TOKEN.mau.khuat, 26)
          || gan(rgba, i, TOKEN.mau.section, 60)
          || gan(rgba, i, TOKEN.mau.sectionKhuat, 40)) {
          if (x < hx0) hx0 = x; if (x > hx1) hx1 = x;
          if (y < hy0) hy0 = y; if (y > hy1) hy1 = y;
        }
      }
    }
  }
  const soO = (w - boTrai) * h;
  /* `tran` nay chỉ xét HÌNH HỮU HẠN. Vật vô hạn chạm mép được đếm riêng ở
   * `chamMepVoHan` để báo cáo, không để đánh trượt. */
  const tran = hx1 >= w - 1 || hy0 <= 0 || hy1 >= h - 1 || (hx1 >= 0 && hx0 <= boTrai);
  const chamMepVoHan = (x1 >= w - 1 || y0 <= 0 || y1 >= h - 1 || x0 <= boTrai) && !tran;
  return {
    tiLeMuc: muc / soO,
    chiemNgang: x1 < 0 ? 0 : (x1 - x0) / (w - boTrai),
    chiemDoc: y1 < 0 ? 0 : (y1 - y0) / h,
    tran, chamMepVoHan, cam, xanh, xam, dam, naKhuat,
    hop: x1 < 0 ? null : { x0, x1, y0, y1 },
  };
}

/**
 * Nét khuất có ĐỔI CHỖ giữa hai khung hình không — tỉ lệ điểm ảnh xám chỉ xuất
 * hiện ở MỘT trong hai ảnh.
 *
 * ⚠️ Bản đầu so **số lượng** điểm xám trước và sau khi xoay. Đó là một proxy
 * yếu: hai ảnh hoàn toàn khác nhau vẫn có thể có cùng số điểm, và p6 ở khung
 * 390×844 đã rơi đúng vào đó — `Δ = 0,016` trong khi nét khuất rõ ràng đã dịch
 * hẳn sang chỗ khác. Đếm hiệu đối xứng thì đo đúng thứ cần đo: VỊ TRÍ.
 */
export function doiChoKhuat(a, b) {
  if (!a || !b || a.length !== b.length) return 0;
  let khac = 0, tong = 0;
  for (let i = 0; i < a.length; i++) {
    if (a[i] || b[i]) tong += 1;
    if (a[i] !== b[i]) khac += 1;
  }
  return tong === 0 ? 0 : khac / tong;
}

/* ─── đọc nhãn thẳng từ DOM ─── */
const DOC_NHAN = "(function(){"
  + "var c=document.querySelector('.geo3d-canvas canvas');"
  + "if(!c) return '[]';"
  + "var rc=c.getBoundingClientRect();"
  + "var ra=[];"
  + "var ns=document.querySelectorAll('.geo3d-label');"
  + "for(var i=0;i<ns.length;i++){var e=ns[i];"
  + " var st=getComputedStyle(e);"
  + " if(st.opacity==='0') continue;"
  + " var r=e.getBoundingClientRect();"
  + " ra.push({ky:e.textContent,x:r.x-rc.x,y:r.y-rc.y,w:r.width,h:r.height,"
  + "  co:st.fontSize,dam:st.fontWeight,mau:st.color,"
  + "  vien:st.webkitTextStrokeWidth||st.getPropertyValue('-webkit-text-stroke-width'),"
  + "  nen:st.backgroundColor});}"
  // LỚP PHỦ không phải canvas và không phải nhãn — nút bấm, chú giải.
  + "var ph=[];"
  + "var q=document.querySelectorAll('.geo3d-noi-nut, .geo3d-readout, button');"
  + "for(var j=0;j<q.length;j++){var b=q[j].getBoundingClientRect();"
  + " if(b.width<=0||b.height<=0) continue;"
  + " if(b.right<rc.left||b.left>rc.right||b.bottom<rc.top||b.top>rc.bottom) continue;"
  + " ph.push({x:b.x-rc.x,y:b.y-rc.y,w:b.width,h:b.height});}"
  + "return JSON.stringify({rong:rc.width,cao:rc.height,nhan:ra,phu:ph});})()";

/** Nhãn ra ngoài khung / đè nhau. */
export function soatNhan(d) {
  if (!d || !d.nhan) return { ngoai: 0, de: 0, soNhan: 0, ky: [] };
  let ngoai = 0, de = 0;
  for (const n of d.nhan) {
    if (n.x < 0 || n.y < 0 || n.x + n.w > d.rong + 0.5 || n.y + n.h > d.cao + 0.5) ngoai += 1;
  }
  for (let i = 0; i < d.nhan.length; i++) {
    for (let j = i + 1; j < d.nhan.length; j++) {
      const a = d.nhan[i], b = d.nhan[j];
      const gx = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
      const gy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
      if (gx > 1 && gy > 1) de += 1;
    }
  }
  return { ngoai, de, soNhan: d.nhan.length, ky: d.nhan.map((n) => n.ky) };
}

async function tuaCuoi(sess, fx) {
  for (let i = 0; i < (fx.expected_trace_event_count ?? 1) + 4; i++) {
    const b = await sess.eval(
      "(function(){var e=document.querySelector('.geo3d-buoc-so');return e?e.textContent:'';})()");
    const m = /(\d+)\s*\/\s*(\d+)/.exec(b);
    if (m && m[1] === m[2]) break;
    await sess.eval("(function(){var b=document.querySelector('[aria-label=\"Bước sau\"]');"
      + "if(b&&!b.disabled)b.click();return 1})()");
    await sleep(90);
  }
  await sleep(600);
}

async function hopCanvas(sess) {
  const t = await sess.eval(
    "(function(){var c=document.querySelector('.geo3d-canvas canvas');"
    + "if(!c) return 'KHONG';var r=c.getBoundingClientRect();"
    + "return JSON.stringify({x:r.x,y:r.y,width:r.width,height:r.height});})()");
  return typeof t === "string" && t.indexOf("{") === 0 ? JSON.parse(t) : null;
}

async function chup(sess, hop, duong) {
  const { result } = await sess._send("Page.captureScreenshot",
    { format: "png", clip: { ...hop, scale: 1 } });
  writeFileSync(duong, Buffer.from(result.data, "base64"));
  return docPNG(readFileSync(duong));
}

/** Kéo ngang một quãng, dùng để kiểm nét khuất có đổi theo camera không. */
async function xoay(sess, hop, dx) {
  const cx = Math.round(hop.x + hop.width / 2);
  const cy = Math.round(hop.y + hop.height / 2);
  const g = (type, x, buttons) => sess._send("Input.dispatchMouseEvent",
    { type, x: Math.round(x), y: cy, button: "left", buttons, clickCount: 1 });
  await g("mousePressed", cx - dx / 2, 1);
  for (let i = 1; i <= 40; i++) { await g("mouseMoved", cx - dx / 2 + (dx * i) / 40, 1); await sleep(10); }
  await g("mouseReleased", cx + dx / 2, 0);
  await sleep(500);
}

export async function motCa(sess, fx, tag, khungNhin) {
  /* Phép tiêm ⑦: nạp một cảnh KHÔNG CÓ VẬT NÀO. Cổng phải đỏ. Bài học đã trả
   * giá: một lượt chấm trước đây ghi PASS 7/7 trên bảy ảnh chỉ có năm chấm
   * đen, vì không có phép đo nào hỏi "trong ảnh có gì không". */
  const env = JSON.stringify(TIEM === "canh-rong"
    ? { ...fx.envelope, scene3d: { ...fx.envelope.scene3d, objects: [], events: [] } }
    : fx.envelope);
  await sess.eval(`(function(){window.__ALGO_SIM_STORE__.getState().loadEnvelope(${env});return 1})()`);
  await sleep(1400);
  const hopSom = await hopCanvas(sess);
  if (!hopSom) return { ...CA_RONG, tag, khungNhin, trangThai: TRANG_THAI.KHONG_DUNG_DUOC };
  if (TIEM !== "canh-rong") await tuaCuoi(sess, fx);
  const hop = await hopCanvas(sess);

  mkdirSync(ANH, { recursive: true });
  const nen = join(ANH, `${tag}-${khungNhin}`);
  const anh = await chup(sess, hop, `${nen}.png`);
  const nhanDom = JSON.parse(await sess.eval(DOC_NHAN));
  const nhan = soatNhan(nhanDom);

  /* Vùng chữ bị LOẠI khỏi phép đo bề dày: nét chữ dày 3–15 px sẽ kéo trung vị
   * lên và biến một cảnh toàn nét 1 px thành "đạt". */
  const loaiTru = (nhanDom.nhan ?? []).map((n) => ({
    x: Math.round(n.x) - 2, y: Math.round(n.y) - 2,
    w: Math.round(n.w) + 4, h: Math.round(n.h) + 4,
  }));
  /* Lớp phủ (nút bấm) đọc từ DOM, không đoán bằng một ô cố định: chúng đổi
   * chỗ theo khung nhìn, và một ô cố định sẽ hoặc bỏ sót hoặc che mất hình. */
  const phu = (nhanDom.phu ?? []).map((n) => ({
    x: Math.round(n.x), y: Math.round(n.y),
    w: Math.round(n.w), h: Math.round(n.h),
  }));
  const loaiHet = [...loaiTru, ...phu];

  const th = doAnh(anh, { loaiTru: phu });
  /* Phép đo đã hiệu chuẩn —  quét theo hàng ngang nên thổi
   * phồng mọi nét nghiêng (2,8 px @20° đọc ra 7,46 px). Màu vai đọc từ
   * NGUỒN token, không ghi cứng. */
  const beDay = doBeDayVuongGoc(anh, { loaiTru: loaiHet, mauVai: TOKEN.mau.mesh });

  // ── xoay rồi chụp lại: nét khuất PHẢI đổi ──
  await xoay(sess, hop, 260);
  const anhXoay = await chup(sess, hop, `${nen}-xoay.png`);
  const thXoay = doAnh(anhXoay, { loaiTru: phu });
  const doiKhuat = doiChoKhuat(th.naKhuat, thXoay.naKhuat);

  return {
    tag, khungNhin,
    canvas: { w: Math.round(hop.width), h: Math.round(hop.height) },
    tiLeMuc: Number(th.tiLeMuc.toFixed(5)),
    chiemNgang: Number(th.chiemNgang.toFixed(3)),
    chiemDoc: Number(th.chiemDoc.toFixed(3)),
    tran: th.tran,
    diemCam: th.cam, diemXanh: th.xanh, diemXam: th.xam, diemDam: th.dam,
    beDayTrungVi: beDay.trungVi, beDayP25: beDay.p25, beDayP75: beDay.p75,
    soMauBeDay: beDay.soMau,
    nhan,
    kieuNhan: nhanDom.nhan?.[0]
      ? { co: nhanDom.nhan[0].co, dam: nhanDom.nhan[0].dam,
        mau: nhanDom.nhan[0].mau, vien: nhanDom.nhan[0].vien,
        nen: nhanDom.nhan[0].nen }
      : null,
    sauXoay: { tiLeMuc: Number(thXoay.tiLeMuc.toFixed(5)), diemXam: thXoay.xam },
    doiKhuat: Number(doiKhuat.toFixed(4)),
    anh: `${nen}.png`,
  };
}

export function phanLoai(r) {
  if (r.trangThai) return r.trangThai;
  if (r.tiLeMuc < NGUONG.MUC_TOI_THIEU) return TRANG_THAI.CANH_RONG;
  if (r.tran) return TRANG_THAI.TRAN_KHUNG;
  const chiem = Math.max(r.chiemNgang, r.chiemDoc);
  if (chiem < NGUONG.CHIEM_MIN || chiem > NGUONG.CHIEM_MAX) return TRANG_THAI.CHIEM_SAI;
  if (CO_THIET_DIEN.has(r.tag) && r.diemCam < 50) return TRANG_THAI.THIEU_THIET_DIEN;
  if (r.diemXanh > NGUONG.XANH_TOI_DA) return TRANG_THAI.XANH_TU_DONG;
  if (r.beDayTrungVi < NGUONG.CANH_THAY_MIN
    || r.beDayTrungVi > NGUONG.CANH_THAY_MAX) return TRANG_THAI.NET_QUA_MANH;
  /* ─── ĐƯỜNG BAO KHỐI CONG: đếm mực ĐẬM, không đếm mực xám ──────────────
   *
   * Bản trước lấy số điểm ảnh XÁM (vai cạnh khuất) làm đại diện cho "có
   * đường bao". Đại diện ấy đo sai thứ: đường bao của một khối cong phần lớn
   * là phần THẤY — với mặt cầu thì gần như toàn bộ. Đo được sau vòng D2: ca
   * p3 có 1829 điểm ảnh màu cạnh thấy (đường bao rõ ràng còn đó) nhưng chỉ
   * 68 điểm xám, nên phép kiểm cũ kết luận THIẾU ĐƯỜNG BAO cho một hình hoàn
   * toàn lành. Nó cũng sẽ cho qua một bản dựng MẤT HẲN đường bao nếu mực xám
   * đến từ chỗ khác — hỏng theo cả hai chiều.
   *
   * Khối cong không có lưới cạnh, nên mực đậm của những ca ấy chỉ có thể đến
   * từ đường bao và vài chấm điểm. */
  if (CO_KHOI_CONG.has(r.tag) && r.diemDam < NGUONG.BAO_TOI_THIEU) {
    return TRANG_THAI.THIEU_DUONG_BAO;
  }
  if (r.nhan.ngoai > NGUONG.NHAN_LOI_TOI_DA
    || r.nhan.de > NGUONG.NHAN_LOI_TOI_DA) return TRANG_THAI.NHAN_HONG;
  if (r.doiKhuat < NGUONG.DOI_CHO_KHUAT_MIN) return TRANG_THAI.KHUAT_KHONG_DOI;
  return TRANG_THAI.DAT;
}

/**
 * `dist/` phải MỚI HƠN `src/`, nếu không cổng đang đo một bản dựng cũ.
 *
 * ⚠️ Đây là bản sửa của một kết luận SAI đã xảy ra thật trong wave này: một
 * phép tiêm lỗi không biên dịch được, `npm run build` đỏ, `--bo-qua-build` bỏ
 * qua, và cổng đo `dist/` của **phép tiêm TRƯỚC ĐÓ** — trả về đúng trạng thái
 * lỗi nhưng của sai nguyên nhân. Cổng `build-freshness` cũ đã đi theo nhánh
 * prototype bị từ chối; đây là chỗ nó quay lại.
 */
function kiemDistMoi() {
  const moiNhat = (thu) => {
    let t = 0;
    const di = (d) => {
      for (const e of readdirSync(d, { withFileTypes: true })) {
        if (e.name === "node_modules" || e.name.startsWith(".")) continue;
        const f = join(d, e.name);
        if (e.isDirectory()) di(f);
        else t = Math.max(t, statSync(f).mtimeMs);
      }
    };
    if (existsSync(thu)) di(thu);
    return t;
  };
  const tDist = moiNhat(DIST);
  const tSrc = moiNhat(join(FE, "src"));
  if (tDist === 0) throw new Error("DIST_THIEU — chưa có bản dựng nào để đo.");
  if (tSrc > tDist) {
    throw new Error("DIST_CU — `dist/` cũ hơn `src/` "
      + `(${Math.round((tSrc - tDist) / 1000)} s). Chạy \`npm run build\` trước, `
      + "và ĐỪNG tin số đo nào cho tới lúc ấy.");
  }
}

export async function chay() {
  const commit = execFileSync("git", ["rev-parse", "HEAD"], { cwd: GOC }).toString().trim();
  if (!CO["bo-qua-build"]) {
    execFileSync("npm", ["run", "build"], { cwd: FE, stdio: "pipe", shell: true, timeout: 600000 });
  }
  kiemDistMoi();
  const { sv, cong } = await phucVu(DIST, TIEM === "thieu-chunk");
  const kq = { commit, chay_luc: new Date().toISOString(), tiem: TIEM, nguong: NGUONG, ca: [] };
  const thu = join(GOC, "docs", "evaluation", "geometry",
    "product-ui-result-rendering", "fixtures");
  try {
    for (const [rong, cao, ten] of [[1440, 900, "1440x900"], [390, 844, "390x844"]]) {
      const tagsKhung = ten === "1440x900" ? TAGS : TAGS.filter((t) => ["p1", "p6", "p7"].includes(t));
      if (tagsKhung.length === 0) continue;
      const sess = new BrowserSession({ viewport: rong, height: cao, webgl: true,
        url: `http://127.0.0.1:${cong}`, napModuleDev: false });
      /* Trang không dựng nổi là một KẾT QUẢ có tên, không phải một ngoại lệ.
       * Phép tiêm ⑧ (mất chunk JS) đi đúng đường này; để nó ném thì lượt chạy
       * chết giữa chừng và không ai biết cổng có bắt được hay không. */
      try {
        await sess.open();
      } catch (e) {
        for (const tag of tagsKhung) {
          kq.ca.push({ ...CA_RONG, tag, khungNhin: ten,
            trangThai: TRANG_THAI.KHONG_DUNG_DUOC, chiTiet: String(e.message).slice(0, 200) });
          console.log(`  ${tag} ${ten}: ${TRANG_THAI.KHONG_DUNG_DUOC}`);
        }
        continue;
      }
      for (const tag of tagsKhung) {
        const f = readdirSync(thu).find((x) => x.startsWith(`${tag}_`));
        const fx = JSON.parse(readFileSync(join(thu, f), "utf-8"));
        const r = await motCa(sess, fx, tag, ten);
        r.trangThai = phanLoai(r);
        kq.ca.push(r);
        console.log(`  ${tag} ${ten}: ${r.trangThai}  mực=${r.tiLeMuc} `
          + `chiếm=${r.chiemNgang}/${r.chiemDoc} bềdày=${r.beDayTrungVi} `
          + `cam=${r.diemCam} xanh=${r.diemXanh} xám=${r.diemXam} `
          + `nhãn=${r.nhan.soNhan}(ngoài ${r.nhan.ngoai}, đè ${r.nhan.de}) `
          + `ΔKhuất=${r.doiKhuat}`);
      }
      await sess.close();
    }
  } finally { sv.close(); }
  kq.dat = kq.ca.every((c) => c.trangThai === TRANG_THAI.DAT);
  mkdirSync(RA, { recursive: true });
  const ten = TIEM ? `FIDELITY_TIEM_${TIEM}.json` : "FIDELITY.json";
  writeFileSync(join(RA, ten), JSON.stringify(kq, null, 2), "utf-8");
  console.log(`→ ${join(RA, ten)}  ${kq.dat ? "ĐẠT" : "KHÔNG ĐẠT"}`);
  return kq;
}

if (import.meta.filename === process.argv[1]) {
  const kq = await chay();
  process.exit(kq.dat ? 0 : 1);
}
