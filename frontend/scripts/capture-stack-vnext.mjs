/**
 * capture-stack-vnext.mjs — BẰNG CHỨNG TRÌNH DUYỆT cho vNext §8 (case Stack).
 *
 * VÌ SAO CẦN: unit test dựng DOM bằng `renderToString` — SSR chỉ đi qua trạng
 * thái ĐẦU. Nó không chứng minh được rằng khi học sinh BẤM sang bước 3 thì hình
 * ngăn xếp thật sự đổi trong trình duyệt thật. Sự cố đã chụp màn hình chính là
 * loại lỗi mà SSR không thấy (ARCHITECTURE_MAP §8 #11, #13).
 *
 * HAI ĐIỀU KIỆN TRƯỚC KHI TIN BẢN SOÁT NÀY (anti-pattern #14):
 *   1. DẤU VÂN TAY TRANG — khẳng định đúng mô phỏng đã nạp, sai thì thoát != 0.
 *   2. TIÊM LỖI GIẢ — `--faultcheck` ép ngăn xếp đứng yên; bản soát PHẢI đỏ.
 *      Guard chưa từng đỏ là guard chưa được chứng minh.
 *
 * Chạy: `npm run dev` ở cửa sổ khác, rồi
 *   node scripts/capture-stack-vnext.mjs --out-dir ../docs/evaluation/semantic-vnext
 */
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const args = process.argv.slice(2);
const argOf = (k, d) => {
  const i = args.indexOf(k);
  return i >= 0 && args[i + 1] ? args[i + 1] : d;
};
const OUT = argOf("--out-dir", "../docs/evaluation/semantic-vnext");
const PORT = argOf("--port", "3000");
const FAULT = args.includes("--faultcheck");

const CHUOI = ["{", "[", "(", ")", "]", "}"];

/** Envelope ĐÚNG shape đã qua validator — không đoán. */
const ENVELOPE = {
  status: "ok",
  simulation_id: "generic.rule_scene",
  domain: "generic",
  visual_mode: "2d",
  title: "Kiểm tra đóng mở ngoặc hợp lệ bằng Stack",
  description: null,
  notes: null,
  config: {
    dsl_version: "1.0",
    title: "Kiểm tra đóng mở ngoặc hợp lệ bằng Stack",
    objects: [
      { id: "input_str", type: "array_strip", label: "Chuỗi đầu vào", items: CHUOI },
      { id: "stack_view", type: "stack_view", label: "Ngăn xếp", items: [], capacity: 6 },
      { id: "curr_char", type: "value_box", label: "Ký tự hiện tại" },
      { id: "result_box", type: "value_box", label: "Kết quả" },
    ],
    rules: [],
    interactions: [],
    processes: [
      {
        type: "step_sequence",
        steps: [
          { action: "highlight", targets: ["input_str"], narration: "Khởi tạo: ngăn xếp rỗng, con trỏ ở đầu chuỗi." },
          { action: "set_value", targets: ["curr_char"], value: "{", narration: "Đọc ký tự '{'." },
          { action: FAULT ? "highlight" : "push", targets: ["stack_view"], value: "{", narration: "Đẩy '{' vào ngăn xếp." },
          { action: "set_value", targets: ["curr_char"], value: "[", narration: "Đọc ký tự '['." },
          { action: FAULT ? "highlight" : "push", targets: ["stack_view"], value: "[", narration: "Đẩy '[' vào ngăn xếp." },
          { action: FAULT ? "highlight" : "pop", targets: ["stack_view"], narration: "Gặp ']' khớp cặp — lấy '[' ra." },
          { action: "set_value", targets: ["result_box"], value: "Hợp lệ", narration: "Duyệt hết chuỗi, ngăn xếp rỗng." },
        ],
      },
    ],
  },
};

/** Khung cần chụp + kỳ vọng NGỮ NGHĨA (không phải kỳ vọng pixel). */
const MONG = [
  { cursor: 0, ten: "A_init", stack: [], curr: "—", ket_qua: "—" },
  { cursor: 1, ten: "B_doc_ngoac_nhon", stack: [], curr: "{", ket_qua: "—" },
  { cursor: 2, ten: "C_sau_push_nhon", stack: ["{"], curr: "{", ket_qua: "—" },
  { cursor: 4, ten: "D_sau_push_vuong", stack: ["{", "["], curr: "[", ket_qua: "—" },
  { cursor: 5, ten: "E_sau_pop", stack: ["{"], curr: "[", ket_qua: "—" },
  { cursor: 6, ten: "F_ket_qua", stack: ["{"], curr: "[", ket_qua: "Hợp lệ" },
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const b = await chromium.launch();
const page = await b.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(`http://localhost:${PORT}/`, { waitUntil: "networkidle" });
await sleep(1200);

/* Vite băm URL module theo phiên — lấy URL THẬT của bản trang đã nạp, nếu không
   `import()` trần tạo instance thứ hai với store rỗng. */
const u = await page.evaluate(() => {
  const pick = (s) => {
    const h = performance.getEntriesByType("resource").map((e) => e.name).filter((n) => n.includes(s));
    return h.length ? h[h.length - 1] : new URL(s, location.origin).href;
  };
  return {
    store: pick("/src/state/store.ts"),
    registry: pick("/src/simulations/registry.ts"),
    sims: pick("/src/simulations/index.ts"),
  };
});

const nap = await page.evaluate(async ({ u, env }) => {
  const s = await import(u.store);
  const rg = await import(u.sims);
  const reg = await import(u.registry);
  if (reg.listSimulations().length === 0) rg.registerAllSimulations();
  s.useAppStore.getState().reset();
  s.useAppStore.getState().loadEnvelope(env);
  const a = s.useAppStore.getState().active;
  return a ? { ok: true, title: a.envelope?.title ?? null, steps: a.state?.timeline?.length ?? 0 } : { ok: false };
}, { u, env: ENVELOPE });

/* ── ĐIỀU KIỆN 1: dấu vân tay trang ── */
if (!nap.ok || nap.title !== ENVELOPE.title || nap.steps !== 7) {
  console.error(`VÂN TAY SAI — nạp=${JSON.stringify(nap)}; cần title="${ENVELOPE.title}", steps=7`);
  await b.close();
  process.exit(3);
}
console.log(`vân tay OK · "${nap.title}" · ${nap.steps} bước`);

mkdirSync(OUT, { recursive: true });
const ket = [];

for (const m of MONG) {
  await page.evaluate(async ({ storeUrl, cursor }) => {
    const s = await import(storeUrl);
    const st = s.useAppStore.getState();
    st.setState
      ? st.setState({ active: { ...st.active, state: { ...st.active.state, cursor } } })
      : s.useAppStore.setState({ active: { ...st.active, state: { ...st.active.state, cursor } } });
  }, { storeUrl: u.store, cursor: m.cursor });
  await sleep(350);

  /* ── PHÉP CHIẾU NGỮ NGHĨA TỪ DOM ── đọc chữ trong SVG, không đọc toạ độ. */
  const proj = await page.evaluate(() => {
    const svg = document.querySelector(".sim-stage svg");
    if (!svg) return null;
    const nodes = [...svg.querySelectorAll("text")].map((t) => t.textContent.trim());
    const groups = [...svg.querySelectorAll("g")];
    const nhan = (label) => {
      for (const g of groups) {
        const ts = [...g.querySelectorAll("text")].map((t) => t.textContent.trim());
        if (ts[0] === label && ts.length > 1) return ts[1];
      }
      return null;
    };
    /* Ngăn xếp: nhóm chứa nhãn "Ngăn xếp", lấy các ô chữ bên trong TRỪ nhãn
       nhóm và TRỪ chú thích đỉnh. `← TOP` là CHÚ GIẢI trình bày, không phải
       phần tử — lượt chạy đầu đã nuốt nó vào danh sách và báo FAIL nhầm. */
    const CHU_GIAI = new Set(["Ngăn xếp", "← TOP", "TOP", ""]);
    let stack = [];
    for (const g of groups) {
      const ts = [...g.querySelectorAll("text")].map((t) => t.textContent.trim());
      if (ts.includes("Ngăn xếp")) {
        stack = ts.filter((x) => !CHU_GIAI.has(x) && !x.includes("TOP"));
      }
    }
    return { allText: nodes, stack, curr: nhan("Ký tự hiện tại"), ket_qua: nhan("Kết quả") };
  });

  await page.screenshot({ path: join(OUT, `stack-${m.ten}.png`) });

  const chuoiDu = CHUOI.every((c) => (proj?.allText ?? []).includes(c));
  const okStack = JSON.stringify(proj?.stack ?? null) === JSON.stringify(m.stack);
  const okCurr = (proj?.curr ?? null) === m.curr;
  const okKq = (proj?.ket_qua ?? null) === m.ket_qua;
  const pass = chuoiDu && okStack && okCurr && okKq;

  ket.push({ ...m, quan_sat: proj, chuoi_du: chuoiDu, ok_stack: okStack, ok_curr: okCurr, ok_ket_qua: okKq, pass });
  console.log(`  ${m.ten.padEnd(20)} chuỗi=${chuoiDu ? "✓" : "✗"} stack=${okStack ? "✓" : "✗"}${JSON.stringify(proj?.stack)} curr=${okCurr ? "✓" : "✗"}${JSON.stringify(proj?.curr)} kq=${okKq ? "✓" : "✗"} → ${pass ? "PASS" : "FAIL"}`);
}

await b.close();

const soPass = ket.filter((k) => k.pass).length;
writeFileSync(join(OUT, "stack-visual-acceptance.json"),
  JSON.stringify({ chay_luc: new Date().toISOString(), faultcheck: FAULT, so_pass: soPass, tong: ket.length, khung: ket }, null, 2) + "\n",
  "utf-8");

console.log(`\n${soPass}/${ket.length} khung PASS${FAULT ? "  (chế độ TIÊM LỖI — cần KHÔNG đủ 6/6)" : ""}`);

/* ── ĐIỀU KIỆN 2: tiêm lỗi giả phải làm bản soát ĐỎ ── */
if (FAULT) {
  if (soPass === ket.length) {
    console.error("TIÊM LỖI mà vẫn 6/6 — bản soát KHÔNG đỏ được, tức nó không chứng minh gì.");
    process.exit(4);
  }
  console.log("tiêm lỗi làm bản soát đỏ đúng như cần — guard đã được chứng minh.");
  process.exit(0);
}
process.exit(soPass === ket.length ? 0 : 1);
