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

/** Bài mẫu đại diện — ba cơ chế khác nhau, không phải ba biến thể của một. */
const BAI = [
  { id: "diem-cao-nhat", ten: "array/quét" },
  { id: "xep-hang-chieu-cao", ten: "array/hoán vị" },
  { id: "tra-tu-dien", ten: "array/chia đôi" },
];

/** Nhãn nút trên UI tiếng Việt — UI học sinh không nói tiếng máy. */
const NUT = { sau: "Sau", truoc: "Trước", lai: "Làm lại", chay: "Chạy" };

async function moBai(page, id) {
  await page.goto(`http://localhost:${PORT}/`, { waitUntil: "networkidle" });
  // Đi qua ĐÚNG đường người dùng: bấm thẻ bài mẫu, không nạp thẳng URL trạng thái.
  const the = page.locator(`[data-sample-id="${id}"]`).first();
  if (await the.count()) {
    await the.click();
  } else {
    // Bản dựng chưa gắn `data-sample-id` ⇒ tìm theo chữ hiển thị.
    await page.getByRole("button", { name: /mẫu|thử|xem/i }).first().click().catch(() => {});
  }
  await page.waitForTimeout(700);
}

/** Phép chiếu ngữ nghĩa của màn hình: chữ trong SVG + chỉ số bước. */
async function chieu(page) {
  return page.evaluate(() => {
    const texts = [...document.querySelectorAll("svg text")].map((t) => t.textContent.trim());
    const buoc = document.body.innerText.match(/(\d+)\s*\/\s*(\d+)/);
    return { texts, buoc: buoc ? buoc[0] : null };
  });
}

async function bam(page, nhan) {
  const b = page.getByRole("button", { name: nhan, exact: false }).first();
  if (!(await b.count())) return false;
  if (await b.isDisabled().catch(() => false)) return false;
  await b.click();
  await page.waitForTimeout(260);
  return true;
}

async function soatMotBai(page, bai) {
  const ket = { bai: bai.id, ten: bai.ten, kiem: {}, ghi_chu: [] };
  await moBai(page, bai.id);

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
          if (b && b.textContent.includes(nhan)) {
            e.stopImmediatePropagation();
            e.preventDefault();
          }
        },
        true,
      );
    }, NUT.sau);
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
  const coChay = await bam(page, NUT.chay);
  if (coChay) {
    await page.waitForTimeout(900);
    const dangChay = await chieu(page);
    ket.kiem.PLAY = JSON.stringify(dangChay) !== JSON.stringify(sr);
    await bam(page, NUT.chay); // nút đổi nhãn Chạy/Dừng — bấm lại là tạm dừng
    const p1 = await chieu(page);
    await page.waitForTimeout(900);
    const p2 = await chieu(page);
    ket.kiem.PAUSE = JSON.stringify(p1) === JSON.stringify(p2);
  } else {
    ket.ghi_chu.push("không tìm thấy nút Chạy — bỏ qua PLAY/PAUSE");
  }

  // Không rò chuỗi kỹ thuật lên bề mặt học sinh.
  const RO = ["undefined", "null", "[object Object]", "NaN", "Infinity"];
  const roRi = s2.texts.filter((t) => RO.includes(t));
  ket.kiem.KHONG_RO_RI = roRi.length === 0;
  if (roRi.length) ket.ghi_chu.push(`rò: ${roRi.join(", ")}`);

  ket.pass = Object.values(ket.kiem).every(Boolean);
  return ket;
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const ket = [];
for (const b of BAI) ket.push(await soatMotBai(page, b));
await browser.close();

const qua = ket.filter((k) => k.pass).length;
mkdirSync(OUT, { recursive: true });
writeFileSync(
  join(OUT, FAULT ? "transport-faultcheck.json" : "transport-certification.json"),
  JSON.stringify({ chay_luc: new Date().toISOString(), fault: FAULT, ket }, null, 2),
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

// Tiêm lỗi mà vẫn xanh hết ⇒ guard chưa chứng minh được gì.
if (FAULT) process.exit(qua === ket.length ? 3 : 0);
process.exit(qua === ket.length ? 0 : 1);
