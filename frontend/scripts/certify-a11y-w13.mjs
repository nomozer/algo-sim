/**
 * certify-a11y-w13.mjs — GIẢM CHUYỂN ĐỘNG & TƯƠNG PHẢN, ĐO TRÊN TRÌNH DUYỆT THẬT.
 *
 * ─── VÌ SAO VITEST KHÔNG ĐỦ (LẦN NÀY KHÁC LẦN W12) ────────────────────────
 *
 * `styles/tokens.test.ts` đã khoá được hai thứ ở tầng MÃ NGUỒN: khối
 * `@media (prefers-reduced-motion: reduce)` có tồn tại, và token màu chữ nào
 * trượt WCAG AA. Nhưng cả hai đều dừng ở "luật CÓ ĐƯỢC VIẾT RA", không chạm
 * tới "trình duyệt CÓ LÀM THEO". Ba khoảng trống chỉ hiện ra khi CSS chạy thật:
 *
 *   · một khai báo `!important` viết ở file khác, hoặc một luật đặt SAU trong
 *     thứ tự tầng, vẫn thắng khối reduce — mã nguồn nhìn vẫn đúng;
 *   · `transition` do JS gán inline không nằm trong `.css` nào để mà quét;
 *   · và quan trọng nhất: guard tĩnh phải GIẢ ĐỊNH mỗi đoạn chữ nằm trên
 *     `--canvas` hay `--canvas-soft`. Nền thật là kết quả của cây DOM — thẻ
 *     lồng trong thẻ, nền trong suốt xuyên xuống tổ tiên. Chỉ
 *     `getComputedStyle` mới biết cặp (chữ, nền) THẬT SỰ chồng lên nhau.
 *
 * Nên script này KHÔNG lặp lại phép đo của vitest. Nó đo thứ vitest không với
 * tới: giá trị TÍNH TOÁN sau khi mọi tầng CSS đã phân giải.
 *
 * ─── PHÉP ĐO TƯƠNG PHẢN LÀ THEO CẶP THẬT, KHÔNG THEO BẢNG MÀU ─────────────
 *
 * Đi từng phần tử có chữ nhìn thấy được → `color` tính toán → leo cây tổ tiên
 * tìm nền ĐỤC ĐẦU TIÊN → tính tỉ lệ. Ngưỡng chọn theo cỡ chữ, đúng WCAG 1.4.3:
 * chữ lớn (≥24px, hoặc ≥18.66px và đậm) chỉ cần 3:1, còn lại 4.5:1. Chấm mọi
 * thứ bằng 4.5 là tự sinh phát hiện giả trên tiêu đề.
 *
 * ─── HAI ĐIỀU KIỆN TRƯỚC KHI TIN KẾT QUẢ "SẠCH" (ARCHITECTURE_MAP §8 #14) ──
 *
 * (a) dấu vân tay trang — `BrowserSession.open()` đã ném lỗi nếu sai route;
 * (b) tiêm lỗi giả — mục FAULT ở cuối tự bơm một khối CSS phá cả hai trục rồi
 *     đòi thấy màu đỏ. Guard chưa từng đỏ là guard chưa được chứng minh.
 *
 * ⚠️ Backtick KHÔNG được xuất hiện trong biểu thức tiêm vào trang.
 *
 * Dùng: `npm run dev` ở cửa sổ khác, rồi
 *   node scripts/certify-a11y-w13.mjs [--out <đường/dẫn.json>]
 */
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { provenance } from "./evidence.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(
  argOf(
    "--out",
    new URL("../../docs/evaluation/m20/w13-a11y.json", import.meta.url).pathname.replace(/^[/]/, ""),
  ),
);
mkdirSync(dirname(OUT), { recursive: true });

/* ── Biểu thức tiêm vào trang (KHÔNG backtick) ────────────────────────────── */

/**
 * Bảng đo TƯƠNG PHẢN của mọi phần tử có chữ nhìn thấy được.
 *
 * "Có chữ" = có ít nhất một text node con TRỰC TIẾP không rỗng. Lấy cả phần tử
 * cha thì một `<div>` bọc sẽ bị tính lây màu của con và ra kết quả vô nghĩa.
 */
const DO_TUONG_PHAN = `(()=>{
  var lum = function (c) {
    var p = c.map(function (v) {
      v = v / 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2];
  };
  var rgb = function (s) {
    var m = s.match(/rgba?\\(([^)]+)\\)/);
    if (!m) return null;
    var p = m[1].split(',').map(function (x) { return parseFloat(x); });
    return { c: [p[0], p[1], p[2]], a: p.length > 3 ? p[3] : 1 };
  };
  var nenThat = function (el) {
    var n = el;
    while (n && n !== document.documentElement) {
      var v = rgb(getComputedStyle(n).backgroundColor);
      if (v && v.a > 0.95) return v.c;
      n = n.parentElement;
    }
    return [255, 255, 255];
  };
  /* Nền của CHỮ SVG không nằm ở tổ tiên mà ở hình ANH EM vẽ trước nó (nhãn
     trắng đặt trên một circle/rect đã tô). Leo cây DOM ở đó cho ra nền trang
     và đẻ ra phát hiện giả "trắng trên trắng 1:1". Hỏi đúng câu hỏi hình học:
     tại tâm chữ, phần tử nào nằm NGAY DƯỚI nó. */
  var nenSvg = function (el) {
    /* CHỈ hình THẬT SỰ TÔ mới được coi là nền. Bản đầu nhận mọi phần tử trong
       chồng điểm và đọc ngay 8 "nền đen" giả: elementsFromPoint trả về CẢ TỔ
       TIÊN, mà nhóm g và svg có fill mặc định rgb(0,0,0) dù chúng không tô gì.
       Bỏ tổ tiên, và chỉ chấp nhận rect/circle/ellipse/polygon/path. */
    var HINH = { rect: 1, circle: 1, ellipse: 1, polygon: 1, path: 1 };
    var r = el.getBoundingClientRect();
    var duoi = document.elementsFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    for (var i = 0; i < duoi.length; i++) {
      var e = duoi[i];
      if (e === el || e.contains(el) || el.contains(e)) continue;
      if (e.namespaceURI !== 'http://www.w3.org/2000/svg') continue;
      if (!HINH[e.tagName.toLowerCase()]) continue;
      var cs2 = getComputedStyle(e);
      if (cs2.fill === 'none') continue;
      var f = rgb(cs2.fill);
      if (f && f.a > 0.95) return f.c;
    }
    return nenThat(el);
  };
  var ten = function (el) {
    return el.tagName.toLowerCase() +
      (el.className && typeof el.className === 'string' && el.className.trim()
        ? '.' + el.className.trim().split(/\\s+/).slice(0, 2).join('.') : '');
  };
  var ra = [];
  var all = document.querySelectorAll('body *');
  for (var i = 0; i < all.length; i++) {
    var el = all[i];
    var chu = '';
    for (var j = 0; j < el.childNodes.length; j++) {
      if (el.childNodes[j].nodeType === 3) chu += el.childNodes[j].nodeValue;
    }
    chu = chu.replace(/\\s+/g, ' ').trim();
    if (!chu) continue;
    var cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    if (parseFloat(cs.opacity) < 0.1) continue;
    var r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    /* CHỮ SVG lấy màu từ thuộc tính fill, KHÔNG phải color. Bản đầu chỉ đọc
       color nên nhãn chỉ số của ArrayView (11px) và chữ 8px trong SamplePreview
       vô hình với phép đo — đúng họ anti-pattern #13: guard không chạm tới một
       loại bề mặt thì nó im lặng báo sạch. */
    var laSvg = el.namespaceURI === 'http://www.w3.org/2000/svg';
    var fg = rgb(laSvg ? cs.fill : cs.color);
    if (!fg || fg.a < 0.1) continue;
    var bg = laSvg ? nenSvg(el) : nenThat(el);
    var L1 = lum(fg.c), L2 = lum(bg);
    var ti = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
    var px = parseFloat(cs.fontSize);
    var dam = parseInt(cs.fontWeight, 10) >= 700;
    var can = (px >= 24 || (px >= 18.66 && dam)) ? 3 : 4.5;
    ra.push({
      sel: ten(el), chu: chu.slice(0, 40), px: px, dam: dam, svg: laSvg,
      mau: laSvg ? cs.fill : cs.color, nen: 'rgb(' + bg.join(', ') + ')',
      ti: Math.round(ti * 100) / 100, can: can, dat: ti >= can
    });
  }
  return JSON.stringify(ra);
})()`;

/** Đo thời lượng hoạt cảnh/chuyển tiếp TÍNH TOÁN của các lớp hoạt cảnh đã biết. */
const DO_CHUYEN_DONG = `(()=>{
  var lop = ['composer-spin', 'gen-pop', 'gen-edge-draw'];
  var ra = { probe: {}, that: [] };
  for (var i = 0; i < lop.length; i++) {
    var d = document.createElement('div');
    d.className = lop[i];
    d.setAttribute('data-a11y-probe', '1');
    document.body.appendChild(d);
    var cs = getComputedStyle(d);
    ra.probe[lop[i]] = { dur: cs.animationDuration, lap: cs.animationIterationCount };
    d.remove();
  }
  var all = document.querySelectorAll('body *');
  for (var k = 0; k < all.length && ra.that.length < 12; k++) {
    var c2 = getComputedStyle(all[k]);
    if (c2.transitionDuration && c2.transitionDuration !== '0s') {
      ra.that.push({
        sel: all[k].tagName.toLowerCase() +
          (typeof all[k].className === 'string' && all[k].className.trim()
            ? '.' + all[k].className.trim().split(/\\s+/)[0] : ''),
        dur: c2.transitionDuration
      });
    }
  }
  return JSON.stringify(ra);
})()`;

/** Giây từ chuỗi CSS kiểu "0.35s, 0s" — lấy giá trị LỚN NHẤT (xấu nhất). */
function giayLonNhat(s) {
  const v = String(s ?? "")
    .split(",")
    .map((x) => {
      const t = x.trim();
      if (t.endsWith("ms")) return parseFloat(t) / 1000;
      return parseFloat(t) || 0;
    });
  return v.length ? Math.max(...v) : 0;
}

/* ── Chạy ─────────────────────────────────────────────────────────────────── */

const s = new BrowserSession({ viewport: 1440, height: 900 });
await s.open();

/** Bật/tắt giả lập "giảm chuyển động" ở tầng CDP — đúng thứ hệ điều hành gửi. */
async function datMedia(giaTri) {
  await s._send("Emulation.setEmulatedMedia", {
    features: [{ name: "prefers-reduced-motion", value: giaTri }],
  });
  await sleep(250);
}

const ket = { motion: {}, contrast: {}, fault: {} };

/* ── TRỤC 1 — GIẢM CHUYỂN ĐỘNG ───────────────────────────────────────────── */

await datMedia("no-preference");
const truoc = JSON.parse(await s.eval(DO_CHUYEN_DONG));
await datMedia("reduce");
const sau = JSON.parse(await s.eval(DO_CHUYEN_DONG));

/**
 * `.composer-spin` là NGOẠI LỆ CÓ CHỦ ĐÍCH: nó là chỉ báo duy nhất cho "AI đang
 * phân tích" (không kèm chữ, `aria-label` không đổi khi chạy), nên nó phải
 * CHẬM LẠI chứ không được TẮT. Hai lớp còn lại phải bị triệt tiêu.
 */
ket.motion.probe = {};
for (const lop of ["gen-pop", "gen-edge-draw"]) {
  const a = giayLonNhat(truoc.probe[lop]?.dur);
  const b = giayLonNhat(sau.probe[lop]?.dur);
  ket.motion.probe[lop] = { truoc: a, sau: b, dat: a > 0.05 && b <= 0.001 };
}
const spinTruoc = giayLonNhat(truoc.probe["composer-spin"]?.dur);
const spinSau = giayLonNhat(sau.probe["composer-spin"]?.dur);
ket.motion.probe["composer-spin"] = {
  truoc: spinTruoc,
  sau: spinSau,
  lap: sau.probe["composer-spin"]?.lap,
  dat: spinSau >= 1.5 && sau.probe["composer-spin"]?.lap === "infinite",
};

const conChay = sau.that.filter((t) => giayLonNhat(t.dur) > 0.001);
ket.motion.transitionThat = { doDuoc: sau.that.length, conChay };
ket.motion.TRANSITION_BI_TRIET_TIEU = sau.that.length > 0 && conChay.length === 0;
ket.motion.verdict =
  Object.values(ket.motion.probe).every((x) => x.dat) && ket.motion.TRANSITION_BI_TRIET_TIEU
    ? "CERTIFIED"
    : "RED";

/* ── TRỤC 2 — TƯƠNG PHẢN TRÊN CẶP THẬT ───────────────────────────────────── */

await datMedia("no-preference");

/**
 * QUÉT TOÀN DANH MỤC, KHÔNG CHỌN TAY BA BỀ MẶT.
 *
 * Bản đầu đo home + library + `algorithm.bubble_sort` rồi báo CERTIFIED — trong
 * khi `.frontier-tag` (mạng/cây) và `.loop-cond-verdict` (chương trình) tô chữ
 * bằng `--accent-orange`/`--accent-green` và KHÔNG bề mặt nào trong ba cái đó
 * render chúng. Đó chính là anti-pattern #13: guard đặt ở chỗ phụ thuộc route
 * nào tình cờ được đi qua. Danh mục tự khai target của nó, nên hỏi nó.
 */
const simIds = JSON.parse(
  await s.eval(`(async()=>{var c=await import(${JSON.stringify(s.mods.catalog)});
    return JSON.stringify(c.offlineCatalog().map(function(x){return x.simId;}));})()`),
);

const BE_MAT = [
  { ten: "home", vao: async () => { await s.resetBetweenScenarios(); await sleep(500); } },
  { ten: "library", vao: async () => { await s.clickText("Thư viện"); await sleep(900); } },
  ...simIds.map((id) => ({
    ten: id,
    vao: async () => {
      await s.resetBetweenScenarios();
      await sleep(250);
      const r = await s.loadTarget(id);
      if (r !== "ok") throw new Error("không nạp được " + id + ": " + r);
      await sleep(700);
    },
  })),
];

ket.contrast.beMat = {};
ket.contrast.boQua = [];
const truotGop = new Map();
for (const bm of BE_MAT) {
  try {
    await bm.vao();
  } catch (err) {
    /* Không nuốt: một target không nạp được là VÙNG CHƯA ĐO, không phải vùng sạch. */
    ket.contrast.boQua.push({ beMat: bm.ten, vi: String(err).slice(0, 120) });
    continue;
  }
  const rows = JSON.parse(await s.eval(DO_TUONG_PHAN));
  const truot = rows.filter((r) => !r.dat);
  ket.contrast.beMat[bm.ten] = { doDuoc: rows.length, truot: truot.length };
  for (const r of truot) {
    const key = r.mau + " trên " + r.nen + " @" + r.sel;
    if (!truotGop.has(key)) truotGop.set(key, { ...r, beMat: [bm.ten], soLan: 1 });
    else {
      const g = truotGop.get(key);
      g.soLan += 1;
      if (!g.beMat.includes(bm.ten)) g.beMat.push(bm.ten);
    }
  }
}
ket.contrast.truot = [...truotGop.values()].sort((a, b) => a.ti - b.ti);
ket.contrast.soBeMat = Object.keys(ket.contrast.beMat).length;
ket.contrast.tongPhanTu = Object.values(ket.contrast.beMat).reduce((a, b) => a + b.doDuoc, 0);
/* Bỏ qua một bề mặt là chưa đo được nó — không được coi là đã sạch. */
ket.contrast.verdict =
  ket.contrast.truot.length === 0 && ket.contrast.boQua.length === 0 ? "CERTIFIED" : "RED";

/* ── FAULT — GUARD CHƯA TỪNG ĐỎ LÀ GUARD CHƯA ĐƯỢC CHỨNG MINH ────────────── */

/**
 * Bơm một khối CSS đặt SAU mọi stylesheet của trang — đúng hình dạng của lỗi
 * thật mà guard tĩnh KHÔNG bắt được: mã nguồn `global.css` vẫn đúng nguyên vẹn,
 * chỉ có tầng phân giải cuối cùng bị một luật khác thắng.
 */
const TIEM = `(()=>{
  var st = document.createElement('style');
  st.id = 'a11y-fault';
  st.textContent = '@media (prefers-reduced-motion: reduce){*,*::before,*::after{' +
    'animation-duration:5s !important;transition-duration:5s !important;}}' +
    '.home-title,h1,h2{color:#cfcfcf !important;}';
  document.head.appendChild(st);
  return 'da tiem';
})()`;
const GO_TIEM = `(()=>{var e=document.getElementById('a11y-fault');if(e)e.remove();return 'da go';})()`;

/* Về trang chủ để so với ĐÚNG nền của nó, không so với target vừa nạp cuối. */
await s.resetBetweenScenarios();
await sleep(500);
await s.eval(TIEM);
await datMedia("reduce");
const faultMotion = JSON.parse(await s.eval(DO_CHUYEN_DONG));
await datMedia("no-preference");
const faultRows = JSON.parse(await s.eval(DO_TUONG_PHAN));
await s.eval(GO_TIEM);

ket.fault.motion = {
  genPopSau: giayLonNhat(faultMotion.probe["gen-pop"]?.dur),
  batDuoc: giayLonNhat(faultMotion.probe["gen-pop"]?.dur) > 0.001,
};
ket.fault.contrast = {
  truot: faultRows.filter((r) => !r.dat).length,
  nen: ket.contrast.beMat.home?.truot ?? 0,
  batDuoc: faultRows.filter((r) => !r.dat).length > (ket.contrast.beMat.home?.truot ?? 0),
};
ket.fault.verdict =
  ket.fault.motion.batDuoc && ket.fault.contrast.batDuoc ? "GUARD_CHUNG_MINH_DUOC" : "GUARD_MU";

/* ── Kết & artifact ──────────────────────────────────────────────────────── */

ket.provenance = provenance("certify-a11y-w13", { viewport: 1440 });
ket.verdict =
  ket.fault.verdict === "GUARD_CHUNG_MINH_DUOC" &&
  ket.motion.verdict === "CERTIFIED" &&
  ket.contrast.verdict === "CERTIFIED"
    ? "CERTIFIED"
    : "RED";

writeFileSync(OUT, JSON.stringify(ket, null, 2), "utf-8");
await s.close();

console.log("── GIẢM CHUYỂN ĐỘNG ───────────────────────────────");
for (const [k, v] of Object.entries(ket.motion.probe)) {
  console.log(`  ${(v.dat ? "✔" : "✘")} ${k.padEnd(16)} ${v.truoc}s → ${v.sau}s` +
    (v.lap ? `  (lặp: ${v.lap})` : ""));
}
console.log(`  ${(ket.motion.TRANSITION_BI_TRIET_TIEU ? "✔" : "✘")} transition thật: ` +
  `${ket.motion.transitionThat.doDuoc} phần tử đo được, ${ket.motion.transitionThat.conChay.length} còn chạy`);
console.log("\n── TƯƠNG PHẢN (cặp chữ/nền THẬT, quét toàn danh mục) ─");
console.log(`  ${ket.contrast.soBeMat} bề mặt · ${ket.contrast.tongPhanTu} phần tử có chữ ` +
  `· ${ket.contrast.truot.length} cặp trượt · ${ket.contrast.boQua.length} bề mặt bỏ qua`);
for (const b of ket.contrast.boQua) console.log(`    ⚠ chưa đo được: ${b.beMat} — ${b.vi}`);
for (const r of ket.contrast.truot.slice(0, 16)) {
  console.log(`    ✘ ${String(r.ti).padStart(5)}:1 (cần ${r.can}) ${r.svg ? "[SVG] " : ""}${r.sel}` +
    ` — ${r.mau} trên ${r.nen}`);
  console.log(`        "${r.chu}"  ${r.px}px${r.dam ? " đậm" : ""}  ` +
    `[${r.beMat.slice(0, 3).join(",")}${r.beMat.length > 3 ? ",+" + (r.beMat.length - 3) : ""}]`);
}
console.log("\n── FAULT ──────────────────────────────────────────");
console.log(`  chuyển động: gen-pop dưới reduce = ${ket.fault.motion.genPopSau}s ` +
  `→ ${ket.fault.motion.batDuoc ? "BẮT ĐƯỢC" : "MÙ"}`);
console.log(`  tương phản: ${ket.fault.contrast.truot} trượt (nền: ${ket.fault.contrast.nen}) ` +
  `→ ${ket.fault.contrast.batDuoc ? "BẮT ĐƯỢC" : "MÙ"}`);
console.log(`\nKẾT: ${ket.verdict}   → ${OUT}`);

process.exit(ket.verdict === "CERTIFIED" ? 0 : 2);
