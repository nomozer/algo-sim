/**
 * certify-refusal-surface.mjs — BỀ MẶT TỪ CHỐI, đo trong Chrome thật.
 *
 * ─── ĐIỀU ĐANG ĐƯỢC BẢO VỆ ────────────────────────────────────────────────
 *
 * Hệ **fail-closed**: từ chối là mặc định. Nhưng một lượt từ chối chỉ đúng nếu
 * bề mặt cũng đúng, và bề mặt thì có bốn cách hỏng độc lập nhau:
 *   1. sai nhãn — nói “ngoài danh mục” cho một bài hình học dựng hụt,
 *   2. vẫn dựng cảnh — hiện khung 3D rỗng bên dưới lời từ chối,
 *   3. lộ mã kỹ thuật — `grounding_failure`, `simulation_id` lọt lên UI,
 *   4. cụt đường — từ chối xong không còn lối nào đi tiếp.
 *
 * Phần cuối nạp envelope **hỏng** (`{}`, thiếu `simulation_id`, `scene3d` sai
 * kiểu, không có `scene3d`) để khẳng định không ca nào ném lỗi hay làm trắng
 * màn — kho **không có** error boundary nào, nên một lần ném là mất cả trang.
 *
 * **0 mạng ra ngoài, 0 LLM**: mọi envelope do CDP trả tại biên `/api/analyze`.
 *
 * ═══ VIẾT LẠI 2026-09-09 · `FINAL_SYSTEM_REPRODUCIBILITY_AND_RELEASE_FREEZE` ══
 *
 * Bản trước chập chờn **9/10 lượt đỏ** (`17–19/21`), và mọi lần đỏ đều mang
 * nhãn *"nhãn rỗng"* — đọc như một lỗi NỘI DUNG. Đo lại thì không phải:
 *
 *   • trang **chưa từng dựng**: `#root` rỗng suốt 60 s, `readyState=complete`;
 *   • nhật ký mạng: `Script net::ERR_CONNECTION_REFUSED` +
 *     `net::ERR_NETWORK_ACCESS_DENIED` — JS chưa bao giờ tới nơi;
 *   • **tải lại KHÔNG cứu được** (0/2), nên đây không phải trục trặc chớp nhoáng;
 *   • đo 15 lượt mỗi bên: **Vite dev kẹt 2/15**, **bản dựng sản phẩm 0/15**.
 *
 * Ba thay đổi, mỗi cái đóng một lỗ khác nhau:
 *
 * ① **Chạy trên BẢN DỰNG SẢN PHẨM** (`vite preview`), không trên dev server.
 *    Dev server phát mỗi module một request HTTP — hàng trăm request cho mỗi
 *    phiên Chrome mới, và đó là chỗ transport gãy. Bản dựng chỉ vài tệp tĩnh.
 *    Đây cũng là thứ buổi demo thật sự chạy, nên đo nó đúng hơn về mọi mặt.
 *
 * ② **Đi qua UI THẬT + biên `/api/analyze`**, không `import('/src/state/…')`.
 *    Bản trước bơm thẳng vào store bằng đường dẫn NGUỒN — chỉ tồn tại ở dev,
 *    và bỏ qua đúng đoạn response adapter. Nay: gõ đề vào ô nhập thật, bấm nút
 *    thật, CDP trả envelope. Vừa chạy được trên bản dựng, vừa đo nhiều hơn.
 *
 * ③ **Chờ theo TRẠNG THÁI, và phân biệt HẠ TẦNG với NỘI DUNG.** Bản trước ngủ
 *    `3000 ms` sau `Page.navigate` rồi hỏi. Nay chờ tới khi trang thật sự dựng;
 *    quá hạn thì **ném `PAGE_NOT_LOADED`** chứ KHÔNG ghi 21 khẳng định rác. Một
 *    cổng báo "nhãn sai" cho một trang chưa tải là cổng nói dối về LOẠI lỗi —
 *    tệ hơn cả chập chờn, vì nó đẩy người đọc đi sửa nhầm chỗ.
 *
 * ⚠️ Không assertion nào bị bỏ: vẫn đúng **21** phép kiểm như trước.
 *
 * Cần: `npm run build` rồi `npx vite preview --port 4173` (hoặc `--base` khác).
 * Chạy: `node scripts/certify-refusal-surface.mjs [--base http://localhost:4173]`
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const REPO = fileURLToPath(new URL("../..", import.meta.url));
const OUT = join(REPO, "docs/evaluation/integration");
mkdirSync(OUT, { recursive: true });
const VP = { w: 1600, h: 900 };
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const arg = (n, d) => {
  const i = process.argv.indexOf(`--${n}`);
  return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : d;
};
const BASE = arg("base", "http://localhost:4173");
/** Trang phải dựng trong ngần này, nếu không là lỗi HẠ TẦNG (không phải nội dung). */
const TRAN_DUNG_TRANG_MS = 20000;

class PageNotLoaded extends Error {}

const port = 9800 + Math.floor(Math.random() * 90);
const dir = mkdtempSync(join(tmpdir(), "refus-"));
const proc = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${port}`,
  `--user-data-dir=${dir}`, `--window-size=${VP.w},${VP.h}`, "--hide-scrollbars",
  "--force-device-scale-factor=2", "--use-gl=angle", "--use-angle=swiftshader",
  "--enable-unsafe-swiftshader", "about:blank"], { stdio: "ignore" });
let wsUrl;
for (let i = 0; i < 80 && !wsUrl; i++) {
  try {
    wsUrl = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json())
      .find((t) => t.type === "page")?.webSocketDebuggerUrl;
  } catch { /* chưa lên */ }
  if (!wsUrl) await sleep(300);
}
const ws = new WebSocket(wsUrl); await new Promise((r) => (ws.onopen = r));
let id = 0; const pend = new Map(); const errs = []; const loiScript = [];
let dangPhucVu = null;              // envelope mà `/api/analyze` sẽ trả về

ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.method === "Runtime.consoleAPICalled" && m.params?.type === "error")
    errs.push((m.params.args ?? []).map((a) => a.value).join(" "));
  if (m.method === "Runtime.exceptionThrown")
    errs.push(m.params?.exceptionDetails?.text ?? "exception");
  if (m.method === "Network.loadingFailed" && m.params?.type === "Script")
    loiScript.push(String(m.params?.errorText));
  if (m.method === "Fetch.requestPaused") {
    const body = Buffer.from(JSON.stringify(dangPhucVu ?? {}), "utf8")
      .toString("base64");
    send("Fetch.fulfillRequest", {
      requestId: m.params.requestId, responseCode: 200,
      responseHeaders: [{ name: "Content-Type", value: "application/json" }],
      body,
    });
  }
  if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); }
};
const send = (M, p = {}) => new Promise((res) => {
  const i = ++id; pend.set(i, res);
  ws.send(JSON.stringify({ id: i, method: M, params: p }));
});
const ev = async (x) => (await send("Runtime.evaluate",
  { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
const evj = async (x) => { const v = await ev(x); return v ? JSON.parse(v) : null; };

await send("Page.enable"); await send("Runtime.enable"); await send("Network.enable");
await send("Emulation.setDeviceMetricsOverride",
  { width: VP.w, height: VP.h, deviceScaleFactor: 2, mobile: false });
await send("Fetch.enable",
  { patterns: [{ urlPattern: "*/api/analyze*", requestStage: "Request" }] });

const R = [];
const kt = (t, k, th, ok) => {
  R.push({ t, k, th, ok });
  console.log(`${ok ? "✓" : "✗"} ${t} | ${th}`);
};

/** Nạp trang và CHỜ TỚI KHI NÓ DỰNG. Quá hạn ⇒ lỗi HẠ TẦNG, ném ra ngoài. */
async function moTrangSach() {
  await send("Page.navigate", { url: BASE });
  const t0 = Date.now();
  while (Date.now() - t0 < TRAN_DUNG_TRANG_MS) {
    if (await ev(`!!document.querySelector('textarea')`)) return Date.now() - t0;
    await sleep(100);
  }
  throw new PageNotLoaded(
    `PAGE_NOT_LOADED — trang không dựng trong ${TRAN_DUNG_TRANG_MS} ms tại `
    + `${BASE}. Script lỗi: ${[...new Set(loiScript)].join(",") || "(không có)"}. `
    + "Đây là lỗi HẠ TẦNG, KHÔNG phải một khẳng định về nội dung.");
}

/** Gõ đề vào ô nhập THẬT rồi bấm nút THẬT. Không import module nguồn nào. */
async function guiDe(de) {
  const go = await ev(`(()=>{
    const ta=document.querySelector('textarea');
    if(!ta) return 'không thấy ô nhập';
    const set=Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype,'value').set;
    set.call(ta, ${JSON.stringify(de)});
    ta.dispatchEvent(new Event('input',{bubbles:true}));
    return 'ok';})()`);
  if (go !== "ok") return go;
  await sleep(120);
  const bam = await ev(`(()=>{
    const b=document.querySelector('button[aria-label="Phân tích đề bằng AI"]');
    if(!b) return 'không thấy nút gửi';
    if(b.disabled) return 'nút gửi đang bị khoá';
    b.click(); return 'ok';})()`);
  if (bam !== "ok") return bam;
  // CHỜ THEO TRẠNG THÁI: thẻ từ chối hiện ra, hoặc một khung mô phỏng hiện ra.
  for (let i = 0; i < 100; i++) {
    const xong = await ev(`(()=>{
      if(document.querySelector('.refusal-facts,.card .eyebrow')) return 'the';
      if(document.querySelector('.geo3d-canvas,.sim-stage')) return 'canh';
      return '';})()`);
    if (xong) return xong;
    await sleep(100);
  }
  return "quá hạn chờ phản hồi";
}

// Năm loại từ chối mà sản phẩm PHÁT RA THẬT. `learner_reason` lấy nguyên văn
// từ `backend/app/learner_messages.py`; không câu nào do bộ kiểm viết.
const LOAI = [
  ["OUT_OF_DOMAIN", { failure_category: "out_of_scope", error_code: "gate_out_of_scope",
    stage_reached: "domain", reason: "ngoài phạm vi",
    learner_reason: "Hệ thống này mô phỏng HÌNH HỌC KHÔNG GIAN (Toán 11–12). Đề bạn gửi không thuộc phạm vi ấy." }],
  ["UNSUPPORTED_CAPABILITY", { failure_category: "not_simulation_suitable",
    error_code: "gate_not_simulation_suitable", stage_reached: "scope",
    reason: "không có cơ chế",
    learner_reason: "Nội dung này đọc hiểu là đủ." }],
  ["GROUNDING_FAILURE", { failure_category: "geometry_generation_failed",
    error_code: "input_not_grounded", stage_reached: "grounding",
    reason: "A: source_fact_id 'A(0; 0; 0)' không có trong RequestContract",
    learner_reason: "AlgoSim đã nhận ra đây là bài hình học không gian và đã thử dựng chương trình mô phỏng, nhưng chương trình sinh ra chưa qua được khâu kiểm chứng." }],
  ["INVALID_PROGRAM", { failure_category: "geometry_generation_failed",
    error_code: "semantic_program_invalid", stage_reached: "ir_static",
    reason: "statements.3.construct_point.expr: toán hạng chưa dựng",
    learner_reason: "AlgoSim đã nhận ra đây là bài hình học không gian và đã thử dựng chương trình mô phỏng, nhưng chương trình sinh ra chưa qua được khâu kiểm chứng." }],
  ["CHECK_FAILURE", { failure_category: "geometry_generation_failed",
    error_code: "postcondition_violated", stage_reached: "postconditions",
    reason: "hậu điều kiện distance sai",
    learner_reason: "AlgoSim đã nhận ra đây là bài hình học không gian và đã thử dựng chương trình mô phỏng, nhưng chương trình sinh ra chưa qua được khâu kiểm chứng." }],
];

const DE_HINH_HOC = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3, "
  + "SA vuông góc với mặt phẳng đáy và SA = 4. Tính thể tích khối chóp S.ABCD.";

try {
  for (const [ten, u] of LOAI) {
    dangPhucVu = { status: "unsupported", ...u };
    await moTrangSach();
    const den = await guiDe(DE_HINH_HOC);
    if (den !== "the") {
      throw new PageNotLoaded(
        `PAGE_NOT_LOADED — kịch bản ${ten} không tới được thẻ từ chối (${den}). `
        + "Lỗi HẠ TẦNG hoặc đường vào, KHÔNG phải một khẳng định về nội dung.");
    }
    /* ⚠️ LOCATOR PHẢI NEO VÀO ĐÚNG THẺ TỪ CHỐI, không phải `.eyebrow` đầu tiên
       của tài liệu. Trang chủ còn những thẻ `.eyebrow` khác (khối "Gợi ý khám
       phá"), nên `document.querySelector('.eyebrow')` đọc nhầm thẻ hàng xóm.
       Phép tiêm *"bỏ nhãn thẻ từ chối"* đã **KHÔNG bị bắt** vì đúng lý do ấy:
       nhãn của thẻ từ chối rỗng, bộ kiểm đọc nhãn của thẻ khác rồi báo xanh.
       Neo bằng chính khối `.refusal-facts` — thứ chỉ `UnsupportedNotice` dựng. */
    const d = await evj(`JSON.stringify((()=>{
      const the = document.querySelector('.refusal-facts')?.closest('.card');
      const q = (s) => (the?.querySelector(s)?.textContent||'').trim();
      return {
      the_co_ton_tai: !!the,
      eyebrow:q('.eyebrow'),
      than:q('p').slice(0,60),
      goiY:q('.notes').slice(0,60),
      soCanvas: document.querySelectorAll('canvas').length,
      coXuong3D: !!document.querySelector('.geo3d-xuong'),
      loKyThuat: ['input_not_grounded','geometry_generation_failed','out_of_scope',
        'not_simulation_suitable','semantic_program_invalid','postcondition_violated',
        'source_fact_id','statements.','Traceback','at Object.'].filter(
          k=>document.body.innerText.includes(k)),
      coDuongVe: !!document.querySelector('textarea, input[type=text]')
        || [...document.querySelectorAll('a,button')].some(
             e=>/thư viện|mô phỏng mới|trang chủ/i.test(e.textContent)),
    };})())`);
    kt(`${ten} · nhãn`, "có nhãn", `"${d.eyebrow}"`,
       d.the_co_ton_tai === true && d.eyebrow.length > 0);
    kt(`${ten} · KHÔNG dựng cảnh`, "0 canvas",
       `canvas=${d.soCanvas} xuong3D=${d.coXuong3D}`,
       d.soCanvas === 0 && d.coXuong3D === false);
    kt(`${ten} · KHÔNG lộ mã kỹ thuật`, "[]", JSON.stringify(d.loKyThuat),
       d.loKyThuat.length === 0);
    kt(`${ten} · có đường quay lại`, "true", String(d.coDuongVe), d.coDuongVe === true);
    console.log(`     nhãn="${d.eyebrow}" gợi ý="${d.goiY}"`);
  }

  // ══ Biên lỗi: envelope hỏng đi qua ĐÚNG response adapter ═════════════════
  //
  // Bản trước gọi `store.loadEnvelope` thẳng, tức bỏ qua adapter. Nay envelope
  // hỏng được trả tại `/api/analyze` — nếu adapter ném thì cả trang trắng, và
  // đó chính là điều cần chặn (kho không có error boundary nào).
  const XAU = [
    ["envelope rỗng", {}],
    ["thiếu simulation_id", { status: "ok", scene3d: { objects: [], steps: [] } }],
    ["scene3d hỏng", { status: "ok", simulation_id: "generic.semantic_program",
                       config: {}, scene3d: { objects: "KHONG PHAI MANG" } }],
    ["scene3d thiếu hẳn", { status: "ok", simulation_id: "generic.semantic_program",
                            config: {} }],
  ];
  const ketXau = [];
  let trangTrong = false; let coRoot = true;
  for (const [ten, env] of XAU) {
    dangPhucVu = env;
    await moTrangSach();
    await guiDe(DE_HINH_HOC);
    await sleep(300);
    const s = await evj(`JSON.stringify({
      trong:(document.body.innerText||'').trim().length < 40,
      root:!!document.querySelector('#root')?.firstElementChild})`);
    ketXau.push([ten, s.trong ? "TRẮNG MÀN" : "còn nội dung"]);
    trangTrong = trangTrong || s.trong;
    coRoot = coRoot && s.root;
  }
  console.log("  [envelope xấu] " + JSON.stringify(ketXau));
  kt("Biên lỗi · không trắng màn", "còn nội dung",
     `trangTrong=${trangTrong} coRoot=${coRoot}`,
     trangTrong === false && coRoot === true);

  writeFileSync(join(OUT, "refusal-surface.json"), JSON.stringify({
    base: BASE, R, loiConsole: errs, loiScript: [...new Set(loiScript)],
  }, null, 2));
  console.log(`\nĐẠT ${R.filter((x) => x.ok).length}/${R.length} · LOI_CONSOLE ${errs.length}`);
  ws.close(); proc.kill();
  process.exit(R.every((x) => x.ok) && errs.length === 0 ? 0 : 1);
} catch (e) {
  // Lỗi hạ tầng KHÔNG được ghi thành artifact nghiệm thu: một tệp `17/21` do
  // trang chưa tải sẽ được đọc như một hồi quy nội dung ở lần sau.
  console.error(`\n${e instanceof PageNotLoaded ? "" : "LỖI KHÔNG NGỜ: "}${e.message}`);
  ws.close(); proc.kill();
  process.exit(2);
}
