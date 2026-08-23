/**
 * e2e-stack-production.mjs — ĐƯỜNG NGƯỜI DÙNG THẬT, KHÔNG TIÊM STORE.
 *
 * ─── VÌ SAO CÓ FILE THỨ HAI ────────────────────────────────────────────────
 *
 * `capture-stack-vnext.mjs` tiêm envelope thẳng vào `useAppStore.loadEnvelope`.
 * Nó chứng minh renderer + engine ĐÚNG khi được cho một envelope đúng — tức
 * bằng chứng COMPONENT, không phải E2E. Màn hình sản phẩm vẫn hỏng sau bản soát
 * ấy vì lỗi nằm ở đường SINH: `main.py` gọi `run_pipeline` mà quên
 * `semantic_route`, nên route sinh ngữ nghĩa chưa từng chạy cho người dùng.
 *
 * File này đi đúng đường đó: gõ đề vào ô nhập thật, bấm nút gửi thật, chờ HTTP
 * thật, bấm nút "Tiến một bước" thật. Không `loadEnvelope`, không fixture,
 * không sample offline.
 *
 * ─── TIÊU TỐN QUOTA THẬT ───────────────────────────────────────────────────
 *
 * Mỗi lượt chạy = 1 request `/api/analyze` = nhiều lượt LLM phía backend. Ngân
 * sách vNext §12: ≤3 lần sinh, ≤30 lượt logic, ≤40 HTTP. Script đếm và IN ra
 * số request nó tự tạo; phần backend đọc từ `/api/health`.
 *
 * Chạy: dev server ở cổng `--port`, backend docker có SEMANTIC_ROUTE_MODE=serve.
 */
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const args = process.argv.slice(2);
const argOf = (k, d) => { const i = args.indexOf(k); return i >= 0 && args[i + 1] ? args[i + 1] : d; };
const OUT = argOf("--out-dir", "../docs/evaluation/semantic-vnext/e2e");
const PORT = argOf("--port", "3100");
const FAULT = argOf("--fault", "");

// `--de` để soát được đề KHÁC mà không phải sửa mã: đề ghép ngoặc dừng ở
// `predicate_verdict` (taxonomy cố ý không có), nên nó KHÔNG bao giờ chứng minh
// được đường phát. Muốn bằng chứng trình duyệt cho một envelope do route SINH
// phát ra thì phải chạy một đề nằm trong taxonomy — vd `derived_sequence`.
const DE_BAI = argOf(
  "--de",
  "Kiểm tra tính hợp lệ của chuỗi đóng mở ngoặc bằng ngăn xếp Stack với chuỗi {[()]}.",
);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
mkdirSync(OUT, { recursive: true });

const b = await chromium.launch();
const page = await b.newPage({ viewport: { width: 1440, height: 900 } });

/* Chộp ĐÚNG response sản phẩm — nguồn sự thật cho "route nào đã phục vụ". */
let apiRes = null;
let soRequest = 0;
/* Chộp cả REQUEST, không chỉ response: một lượt soát từng kết luận "server sai"
   trong khi thứ UI gửi đi mới là cái khác — không nhìn được body thì không phân
   biệt nổi hai khả năng ấy. */
let apiReq = null;
page.on("request", (r) => {
  if (r.url().includes("/api/analyze")) {
    try { apiReq = JSON.parse(r.postData() || "null"); } catch { apiReq = r.postData(); }
  }
});
page.on("response", async (r) => {
  if (!r.url().includes("/api/analyze")) return;
  soRequest += 1;
  try { apiRes = { status: r.status(), body: await r.json() }; } catch { apiRes = { status: r.status(), body: null }; }
});

await page.goto(`http://localhost:${PORT}/`, { waitUntil: "networkidle" });
await sleep(800);

/* ── ĐƯỜNG NGƯỜI DÙNG: gõ đề, bấm gửi ── */
await page.fill(".composer-text", DE_BAI);
await page.click(".composer-send");
console.log("đã gửi đề qua UI thật — chờ API…");

/* Chờ có response hoặc hết giờ. Không poll store. */
for (let i = 0; i < 120 && apiRes === null; i++) await sleep(1000);

if (apiRes === null) {
  console.error("KHÔNG nhận được response /api/analyze trong 120s");
  await page.screenshot({ path: join(OUT, "e2e-timeout.png") });
  await b.close();
  process.exit(2);
}

writeFileSync(join(OUT, "api-response.json"), JSON.stringify(apiRes, null, 2) + "\n", "utf-8");
const env = apiRes.body ?? {};
console.log(`HTTP ${apiRes.status} · status=${env.status} · simulation_id=${env.simulation_id} · source=${env.source}`);
console.log("  UI gui di:", JSON.stringify(apiReq?.input?.content ?? apiReq).slice(0, 160));

/* ── VÂN TAY ROUTE: phải là route sinh ngữ nghĩa, không phải rule_scene ── */
const routeOk = env.simulation_id === "generic.semantic_program" || env.source === "semantic_program";

/* ── Đi từng bước bằng NÚT THẬT ── */
const KHUNG = ["A_init", "B_buoc2", "C_buoc3", "D_buoc4", "E_buoc5", "F_cuoi"];
const ket = [];

async function chieuNguNghia() {
  return page.evaluate(() => {
    const svg = document.querySelector(".sim-stage svg");
    const text = (sel) => document.querySelector(sel)?.textContent?.trim() ?? null;
    if (!svg) return { co_svg: false, narration: text(".narration, .step-narration") };
    const groups = [...svg.querySelectorAll("g")];
    const CHU_GIAI = new Set(["Ngăn xếp", "Stack", "← TOP", "TOP", ""]);
    const nhan = (label) => {
      for (const g of groups) {
        const ts = [...g.querySelectorAll("text")].map((t) => t.textContent.trim());
        if (ts[0] === label && ts.length > 1) return ts[1];
      }
      return null;
    };
    let stack = null;
    for (const g of groups) {
      const ts = [...g.querySelectorAll("text")].map((t) => t.textContent.trim());
      if (ts.some((x) => x === "Ngăn xếp" || x === "Stack")) {
        stack = ts.filter((x) => !CHU_GIAI.has(x) && !x.includes("TOP"));
      }
    }
    const allText = [...svg.querySelectorAll("text")].map((t) => t.textContent.trim());
    return {
      co_svg: true,
      allText,
      stack,
      curr: nhan("Ký tự hiện tại") ?? nhan("Ký tự"),
      ket_qua: nhan("Kết quả"),
      narration: document.body.innerText.split("\n").filter((l) => l.length > 12).pop() ?? null,
    };
  });
}

for (let i = 0; i < KHUNG.length; i++) {
  if (i > 0) {
    const nut = page.locator('button[title="Tiến một bước"]');
    if ((await nut.count()) === 0) { console.log("  không có nút bước — dừng ở khung", i); break; }
    if (await nut.isDisabled()) { console.log("  hết bước ở khung", i); break; }
    await nut.click();
    await sleep(450);
  }
  const proj = await chieuNguNghia();
  await page.screenshot({ path: join(OUT, `e2e-${KHUNG[i]}.png`) });
  ket.push({ khung: KHUNG[i], ...proj });
  console.log(`  ${KHUNG[i].padEnd(10)} svg=${proj.co_svg} stack=${JSON.stringify(proj.stack)} curr=${JSON.stringify(proj.curr)} kq=${JSON.stringify(proj.ket_qua)}`);
}

await b.close();

/* ── PHÁN QUYẾT NGỮ NGHĨA ── */
const coChuoi = ket.some((k) => ["{", "[", "(", ")", "]", "}"].every((c) => (k.allText ?? []).includes(c)));
const stackDoi = new Set(ket.map((k) => JSON.stringify(k.stack))).size > 1;
const coKetLuan = ket.some((k) => /hợp lệ|không hợp lệ/i.test(String(k.ket_qua ?? "")));

const bao = {
  chay_luc: new Date().toISOString(),
  de_bai: DE_BAI,
  fault: FAULT || null,
  so_request_analyze: soRequest,
  http_status: apiRes.status,
  envelope_status: env.status,
  simulation_id: env.simulation_id ?? null,
  source: env.source ?? null,
  route_la_semantic: routeOk,
  chuoi_dau_vao_hien: coChuoi,
  stack_doi_giua_cac_khung: stackDoi,
  co_ket_luan_cuoi: coKetLuan,
  khung: ket,
};
writeFileSync(join(OUT, "e2e-stack-production.json"), JSON.stringify(bao, null, 2) + "\n", "utf-8");

console.log(`\nroute_la_semantic      ${routeOk ? "PASS" : "FAIL"}`);
console.log(`chuoi_dau_vao_hien     ${coChuoi ? "PASS" : "FAIL"}`);
console.log(`stack_doi_giua_khung   ${stackDoi ? "PASS" : "FAIL"}`);
console.log(`co_ket_luan_cuoi       ${coKetLuan ? "PASS" : "FAIL"}`);
console.log(`request /api/analyze   ${soRequest}`);

process.exit(routeOk && coChuoi && stackDoi && coKetLuan ? 0 : 1);
