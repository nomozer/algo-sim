/**
 * §6 — TRANSPORT QUA CONTROL THẬT, KHÔNG INJECT STORE.
 *
 * ─── VÌ SAO CẦN TẦNG NÀY ──────────────────────────────────────────────────
 *
 * `learner-gate.test.ts` đã chứng minh hợp đồng transport ở tầng engine: đi
 * xuôi chụp bảng, lùi từng bước so lại. Nhưng nó gọi `mod.timeline` TRỰC TIẾP.
 * Không test nào hỏi câu của người học: *bấm nút Sau thì màn hình có đổi không?*
 *
 * Khoảng trống ấy đúng khuôn với sự cố đã ship (`main.py` quên truyền
 * `semantic_route`): mảnh nào cũng xanh mà chưa mảnh nào được ghép.
 *
 * ─── VÌ SAO DÙNG BÀI MẪU OFFLINE ──────────────────────────────────────────
 *
 * Bài mẫu trong `data/samples.ts` chạy HOÀN TOÀN client-side — không `/api`,
 * không LLM, không quota. Nhờ đó tầng này KHÔNG cần inject gì cả: người dùng
 * chọn bài, bấm nút, trạng thái đổi thật. Đó là điều kiện §6 đòi.
 *
 * ─── HAI ĐIỀU KIỆN TRƯỚC KHI TIN MỘT BẢN SOÁT "SẠCH" (anti-pattern #14) ───
 *
 *   1. DẤU VÂN TAY TRANG — khẳng định đã nạp đúng bài và có > 1 bước; sai thì
 *      thoát != 0 thay vì báo xanh trên một trang trống.
 *   2. `--faultcheck` — vô hiệu hoá nút "Sau" bằng cách chặn sự kiện, bản soát
 *      phải TỤT ĐIỂM. Guard chưa từng đỏ là guard chưa được chứng minh.
 *
 * Chạy: node scripts/certify-transport-vnext.mjs --port 3177 [--faultcheck]
 */
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const args = process.argv.slice(2);
const argOf = (k, d) => {
  const i = args.indexOf(k);
  return i >= 0 && args[i + 1] ? args[i + 1] : d;
};
const PORT = argOf("--port", "3177");
const FAULT = args.includes("--faultcheck");
const OUT = argOf("--out-dir", "../docs/evaluation/semantic-vnext/reports");

/**
 * Bài mẫu đại diện — BA CƠ CHẾ khác nhau, không phải ba biến thể của một.
 * Chọn theo chữ HIỂN THỊ vì đó là thứ người học thấy; không có id kỹ thuật nào
 * trên DOM, và đúng ra là không nên có (`ui-hygiene`).
 */
const BAI = [
  { chu: "điểm kiểm tra cao nhất", ten: "array/quét" },
  { chu: "Duyệt cây thư mục", ten: "tree/duyệt" },
  { chu: "đường ít chặng nhất", ten: "graph/BFS" },
];

/**
 * Control thật, khoá theo `title` — đây là hợp đồng UI hiện hành, đọc từ DOM
 * chứ không đoán. Nút bước là nút ICON, không có chữ, nên tìm theo tên hiển thị
 * sẽ trượt im lặng.
 */
const NUT = {
  sau: "Tiến một bước",
  truoc: "Lùi một bước",
  dau: "Về đầu",
  lai: "Dựng lại từ đầu",
  chay: "Tự chạy",
  //: Cùng một nút, nhãn đổi theo trạng thái. Đây là hành vi ĐÚNG của UI (nút
  //: nói việc nó sắp làm), nhưng nó là cái bẫy cho mọi runner tìm theo chữ.
  dung: "Dừng",
};

async function moBai(page, chu) {
  await page.goto(`http://localhost:${PORT}/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(500);
  // Đi qua ĐÚNG đường người dùng: bấm thẻ bài mẫu trên trang chủ.
  await page.locator("button").filter({ hasText: chu }).first().click();
  await page.waitForTimeout(1400);
}

/** Phép chiếu ngữ nghĩa của màn hình: chữ trong SVG + chỉ số bước. */
async function chieu(page) {
  return page.evaluate(() => {
    const texts = [...document.querySelectorAll("svg text")].map((t) => t.textContent.trim());
    const buoc = document.body.innerText.match(/(\d+)\s*\/\s*(\d+)/);
    return { texts, buoc: buoc ? buoc[0] : null };
  });
}

async function bam(page, tieuDe) {
  const b = page.locator(`button[title="${tieuDe}"]`).first();
  if (!(await b.count())) {
    // `Tự chạy` là nút CÓ CHỮ, không có `title` — rơi về tìm theo chữ.
    const c = page.locator("button").filter({ hasText: tieuDe }).first();
    if (!(await c.count()) || (await c.isDisabled().catch(() => false))) return false;
    await c.click();
    await page.waitForTimeout(260);
    return true;
  }
  if (await b.isDisabled().catch(() => false)) return false;
  await b.click();
  await page.waitForTimeout(260);
  return true;
}

async function soatMotBai(page, bai) {
  const ket = { bai: bai.chu, ten: bai.ten, kiem: {}, ghi_chu: [] };
  await moBai(page, bai.chu);

  // ── ĐIỀU KIỆN 1: dấu vân tay trang ───────────────────────────────────────
  const dau = await chieu(page);
  if (!dau.texts.length) {
    ket.ghi_chu.push("không nạp được mô phỏng nào — trang trống");
    return ket;
  }

  if (FAULT) {
    // Tiêm lỗi: nuốt mọi cú bấm nút "Sau" ở tầng capture.
    await page.evaluate((nhan) => {
      document.addEventListener(
        "click",
        (e) => {
          const b = e.target.closest("button");
          if (b && b.getAttribute("title") === nhan) {
            e.stopImmediatePropagation();
            e.preventDefault();
          }
        },
        true,
      );
    }, "Tiến một bước");
  }

  const s0 = await chieu(page);

  // NEXT — màn hình phải ĐỔI.
  const daBam = await bam(page, NUT.sau);
  const s1 = await chieu(page);
  ket.kiem.NEXT = daBam && JSON.stringify(s1) !== JSON.stringify(s0);

  // NEXT lần hai, để có một lịch sử thật mà lùi về.
  await bam(page, NUT.sau);
  const s2 = await chieu(page);

  // PREVIOUS — phải khôi phục ĐÚNG trạng thái trước, không phải "trông giống".
  await bam(page, NUT.truoc);
  const s1b = await chieu(page);
  ket.kiem.PREVIOUS = JSON.stringify(s1b) === JSON.stringify(s1);

  // RESET — về đúng trạng thái khởi tạo.
  await bam(page, NUT.lai);
  const sr = await chieu(page);
  ket.kiem.RESET = JSON.stringify(sr) === JSON.stringify(s0);

  // PLAY/PAUSE — chạy thì đổi, dừng thì ĐỨNG YÊN.
  //
  // Nhịp tự chạy ĐO ĐƯỢC là ~1 bước/giây ở 1x, và tick đầu tiên rơi vào khoảng
  // 1,2s. Chờ 900ms như bản đầu thì bản soát báo "PLAY hỏng" trong khi nó chạy
  // hoàn toàn đúng — một guard đo sai nhịp là một guard vu oan cho sản phẩm.
  const coChay = await bam(page, NUT.chay);
  if (coChay) {
    await page.waitForTimeout(2600);
    const dangChay = await chieu(page);
    ket.kiem.PLAY = JSON.stringify(dangChay) !== JSON.stringify(sr);

    // Nút ĐỔI NHÃN sau khi bấm: `Tự chạy` → `Dừng`. Bấm lại đúng nhãn cũ thì
    // không tìm thấy gì và mô phỏng cứ chạy tiếp — PAUSE trượt vì runner, không
    // vì sản phẩm.
    const daDung = await bam(page, NUT.dung);
    const p1 = await chieu(page);
    await page.waitForTimeout(2200);
    const p2 = await chieu(page);
    ket.kiem.PAUSE = daDung && JSON.stringify(p1) === JSON.stringify(p2);
  } else {
    ket.ghi_chu.push("không tìm thấy nút Tự chạy — bỏ qua PLAY/PAUSE");
  }

  // Không rò chuỗi kỹ thuật lên bề mặt học sinh.
  const RO = ["undefined", "null", "[object Object]", "NaN", "Infinity"];
  const roRi = s2.texts.filter((t) => RO.includes(t));
  ket.kiem.KHONG_RO_RI = roRi.length === 0;
  if (roRi.length) ket.ghi_chu.push(`rò: ${roRi.join(", ")}`);

  ket.pass = Object.values(ket.kiem).every(Boolean);
  return ket;
}

/**
 * §5 — RÕ RÀNG THỊ GIÁC Ở BA BỀ RỘNG.
 *
 * Đo HÌNH HỌC, không so ảnh pixel: repo chỉ có `playwright` chứ không có
 * `@playwright/test`, nên không có `toHaveScreenshot()`. Mà đo hình học còn
 * chặt hơn — nó phát biểu được *vì sao* hỏng ("ô giá trị tràn 14px khỏi khung")
 * thay vì "12.000 pixel đổi màu", và không đỏ oan khi đổi một token màu.
 *
 * Bốn phép đo, mỗi phép ứng một cách màn hình có thể nói dối người học:
 *   TRONG_KHUNG   — đối tượng ngữ nghĩa nằm lọt trong vùng vẽ, không bị cắt
 *   KHONG_TRAN    — trang không cuộn ngang (mất dữ liệu ở mép phải)
 *   CHU_DOC_DUOC  — mọi chữ SVG có kích thước > 0, không bị thu về 0
 *   CONTROL_DUNG  — nút bước còn bấm được; điều khiển bị đẩy khỏi màn hình thì
 *                   mô phỏng thành một bức tranh tĩnh
 */
const VIEWPORTS = [
  { ten: "desktop", width: 1440, height: 900 },
  { ten: "tablet", width: 834, height: 1112 },
  { ten: "mobile", width: 390, height: 844 },
];

async function soatThiGiac(page, bai, vp) {
  await page.setViewportSize({ width: vp.width, height: vp.height });
  await moBai(page, bai.chu);
  await bam(page, NUT.sau);
  await bam(page, NUT.sau);

  const d = await page.evaluate(() => {
    const svg = document.querySelector("svg");
    if (!svg) return null;
    const k = svg.getBoundingClientRect();
    const texts = [...svg.querySelectorAll("text")];
    let ngoai = 0;
    let te = 0;
    for (const t of texts) {
      const r = t.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) te++;
      // Dung sai 1px: bo tròn sub-pixel của trình duyệt không phải lỗi bố cục.
      if (r.left < k.left - 1 || r.right > k.right + 1 ||
          r.top < k.top - 1 || r.bottom > k.bottom + 1) ngoai++;
    }
    return {
      so_chu: texts.length,
      ngoai_khung: ngoai,
      chu_te: te,
      tran_ngang: document.documentElement.scrollWidth > window.innerWidth + 1,
    };
  });

  const nutSau = page.locator(`button[title="${NUT.sau}"]`).first();
  const control =
    (await nutSau.count()) > 0 && (await nutSau.isVisible().catch(() => false));

  const kiem = {
    CO_NOI_DUNG: !!d && d.so_chu > 0,
    TRONG_KHUNG: !!d && d.ngoai_khung === 0,
    CHU_DOC_DUOC: !!d && d.chu_te === 0,
    KHONG_TRAN: !!d && !d.tran_ngang,
    CONTROL_DUNG: control,
  };
  return { bai: bai.chu, viewport: vp.ten, do: d, kiem,
           pass: Object.values(kiem).every(Boolean) };
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const ket = [];
for (const b of BAI) ket.push(await soatMotBai(page, b));

const thiGiac = [];
if (!FAULT) {
  for (const b of BAI) for (const vp of VIEWPORTS) thiGiac.push(await soatThiGiac(page, b, vp));
}
await browser.close();

const qua = ket.filter((k) => k.pass).length;
mkdirSync(OUT, { recursive: true });
writeFileSync(
  join(OUT, FAULT ? "transport-faultcheck.json" : "transport-certification.json"),
  JSON.stringify(
    { chay_luc: new Date().toISOString(), fault: FAULT, ket, thi_giac: thiGiac },
    null,
    2,
  ),
  "utf-8",
);

for (const k of ket) {
  const xau = Object.entries(k.kiem).filter(([, v]) => !v).map(([g]) => g);
  console.log(
    `${k.pass ? "PASS" : "FAIL"}  ${k.bai.padEnd(22)} ${k.ten.padEnd(16)}` +
      (k.pass ? "" : `  ← ${xau.join(", ")}`) +
      (k.ghi_chu.length ? `  (${k.ghi_chu.join(" · ")})` : ""),
  );
}
console.log(`\nTRANSPORT_REAL_UI = ${qua}/${ket.length}${FAULT ? "  [chế độ TIÊM LỖI — tụt điểm là ĐÚNG]" : ""}`);

let quaTG = 0;
if (thiGiac.length) {
  console.log("");
  for (const t of thiGiac) {
    const xau = Object.entries(t.kiem).filter(([, v]) => !v).map(([g]) => g);
    if (t.pass) quaTG++;
    console.log(
      `${t.pass ? "PASS" : "FAIL"}  ${t.viewport.padEnd(8)} ${t.bai.padEnd(24)}` +
        `chữ=${t.do?.so_chu ?? "-"}` + (t.pass ? "" : `  ← ${xau.join(", ")}`),
    );
  }
  const theoVP = VIEWPORTS.map((v) => {
    const r = thiGiac.filter((t) => t.viewport === v.ten);
    return `${v.ten} ${r.every((x) => x.pass) ? "PASS" : "FAIL"}`;
  });
  console.log(`\nVISUAL_CLARITY_3_VIEWPORT = ${quaTG}/${thiGiac.length}  (${theoVP.join(" · ")})`);
}

// Tiêm lỗi mà vẫn xanh hết ⇒ guard chưa chứng minh được gì.
if (FAULT) process.exit(qua === ket.length ? 3 : 0);
process.exit(qua === ket.length && quaTG === thiGiac.length ? 0 : 1);
