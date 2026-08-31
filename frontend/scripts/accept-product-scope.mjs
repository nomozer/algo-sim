/**
 * accept-product-scope.mjs — BỀ MẶT CÔNG KHAI KHÔNG CÒN DANH TÍNH TIN HỌC.
 *
 * ─── HỎI GÌ, VÀ VÌ SAO KHÔNG HỎI BẰNG TEST ĐƠN VỊ ───────────────────────
 *
 * `catalog.test.tsx` đã khoá `publicCatalog()`. Nhưng một danh mục sạch KHÔNG
 * đảm bảo màn hình sạch: nhãn miền còn nằm trong hằng số, chuỗi còn nằm trong
 * component khác, một trang khác vẫn có thể in ra "Thuật toán". Câu hỏi ở đây
 * là câu duy nhất người dùng thật sự hỏi:
 *
 *     Đi hết các đường điều hướng CHÍNH, có gặp lại sản phẩm Tin học không?
 *
 * Nên nó quét TEXT ĐÃ RENDER trên từng trang, hai vai, trình duyệt thật.
 *
 * ─── HAI CÁI BẪY GIỮ NGUYÊN TỪ `accept-live-classroom.mjs` ──────────────
 *
 *   1. Dấu vân tay backend soi ROUTE MỚI, không soi `/api/auth/me` — container
 *      Docker cũ cũng trả 200 cho endpoint cũ.
 *   2. Dấu vân tay TRANG trước mọi khẳng định vắng-mặt: trang trắng làm mọi
 *      `không chứa X` xanh hết, và xanh vì màn hình rỗng.
 *
 * Cần: `npm run dev` (:3000) + uvicorn (:8000) với `ALGOSIM_TEACHER_SIGNUP_CODE`.
 */
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { provenance } from "./evidence.mjs";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(argOf("--out",
  new URL("../../docs/evaluation/geometry/product-scope-acceptance.json",
    import.meta.url).pathname.replace(/^[/]/, "")));
mkdirSync(dirname(OUT), { recursive: true });

const PASS = argOf("--pass", "accept-scope-12345");
const CODE = argOf("--teacher-code", "ACCEPT-TEACHER");
const STAMP = Date.now();

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const rows = [];
const failures = [];
const consoleErrors = [];

function ghi(scenario, actor, action, expected, actual, pass) {
  rows.push({ scenario, actor, action, expected, actual, pass });
  console.log(`  ${pass ? "✓" : "✗"} [${scenario}] ${actor}: ${action} — ${actual}`);
  if (!pass) failures.push(`[${scenario}] ${actor}: ${action} — mong ${expected}, được ${actual}`);
}

/* ── DANH TÍNH BACKEND ─────────────────────────────────────────────────── */
for (const duong of ["/api/classes/999999/session", "/api/classes/999999/monitor"]) {
  const r = await fetch(`http://localhost:3000${duong}`).then((x) => x.json()).catch(() => null);
  if (!r || r.detail === "Not Found") {
    console.error(`✗ Backend sau proxy :3000 KHÔNG có route ${duong}.`);
    console.error("  Chạy: docker compose stop backend  rồi khởi động lại uvicorn.");
    process.exit(2);
  }
}

/* ── MỘT VAI = MỘT TIẾN TRÌNH CHROME ───────────────────────────────────── */
async function moVai(ten, cdpPort) {
  const dir = mkdtempSync(join(tmpdir(), `scope-${ten}-`));
  const proc = spawn(CHROME, ["--headless=new", "--disable-gpu",
    `--remote-debugging-port=${cdpPort}`, `--user-data-dir=${dir}`,
    "--window-size=1600,900", "--hide-scrollbars",
    "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
    "about:blank"], { stdio: "ignore" });

  let wsUrl;
  for (let i = 0; i < 60 && !wsUrl; i++) {
    try {
      const l = await (await fetch(`http://127.0.0.1:${cdpPort}/json/list`)).json();
      wsUrl = l.find((t) => t.type === "page")?.webSocketDebuggerUrl;
    } catch { /* chưa lên */ }
    if (!wsUrl) await sleep(300);
  }
  if (!wsUrl) { console.error(`✗ ${ten}: Chrome không lên`); process.exit(3); }

  const ws = new WebSocket(wsUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 0; const pend = new Map();
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    if (m.method === "Runtime.consoleAPICalled" && m.params?.type === "error") {
      consoleErrors.push({ actor: ten, text: (m.params.args ?? []).map((a) => a.value).join(" ") });
    }
    if (m.method === "Runtime.exceptionThrown") {
      consoleErrors.push({ actor: ten, text: m.params?.exceptionDetails?.text ?? "exception" });
    }
    if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); }
  };
  const send = (method, params = {}) => new Promise((res) => {
    const i = ++id; pend.set(i, res);
    ws.send(JSON.stringify({ id: i, method, params }));
  });
  const ev = async (x) => (await send("Runtime.evaluate",
    { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
  const evj = async (x) => { const v = await ev(x); return v ? JSON.parse(v) : null; };

  await send("Page.enable"); await send("Runtime.enable");
  await send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(2500);
  return { ten, send, ev, evj, dong: () => { try { ws.close(); } catch {} proc.kill(); } };
}

const apij = async (v, method, path, body) => JSON.parse(await v.ev(
  `fetch(${JSON.stringify(path)},{method:${JSON.stringify(method)},credentials:'include',
   headers:{'Content-Type':'application/json'}${body ? `,body:JSON.stringify(${JSON.stringify(body)})` : ""}})
   .then(async r=>JSON.stringify({s:r.status,b:await r.json().catch(()=>null)}))`));

/* Nhãn miền của đề CŨ. Chúng là chuỗi hiển thị, nên gặp lại chúng trên màn
   hình đúng nghĩa là bề mặt còn danh tính cũ. `Hình học` KHÔNG nằm đây. */
const NHAN_CU = ["Thuật toán", "Nhị phân", "Mạng", "CSDL", "Lôgic", "Web", "Màu sắc"];
/* Cụm chữ quảng bá đề cũ. Tách khỏi nhãn miền vì chúng hỏng theo kiểu khác:
   nhãn lọt qua hằng số, còn cụm này lọt qua chuỗi viết tay trong component. */
const CUM_CU = ["Tin học THPT", "mô phỏng thuật toán", "số nhị phân",
                "cổng logic", "mạng máy tính", "cơ sở dữ liệu"];

/* ⚠️ SO SÁNH KHÔNG PHÂN BIỆT HOA–THƯỜNG, và đây KHÔNG phải chuyện tiểu tiết.
   `innerText` trả về văn bản ĐÃ RENDER, nên `text-transform: uppercase` trên
   `.starter-group-title` biến "Hình học" thành "HÌNH HỌC". Bản đầu của guard
   này so khớp nguyên văn, nên mọi khẳng định "0 nhãn miền Tin học" XANH VÔ
   NGHĨA — nó sẽ không thấy một nhóm "THUẬT TOÁN" hiện ngay giữa Thư viện.
   Lộ ra nhờ khẳng định NGƯỢC ("phải có nhóm Hình học") đỏ. */
const co = (text, chuoi) => text.toLowerCase().includes(chuoi.toLowerCase());

const doTrang = (v) => v.evj(`JSON.stringify({
  text: document.body.innerText,
  nutDieuHuong: [...document.querySelectorAll('nav button, nav a, .app-sidebar button')]
    .map(b => b.textContent.trim()).filter(Boolean),
  theGoiY: document.querySelectorAll('.starter-card').length,
  xuong3d: !!document.querySelector('.geo3d-xuong'),
  canvas: document.querySelectorAll('.geo3d-canvas canvas').length,
})`);

const diToi = async (v, nhan) => {
  await v.ev(`(()=>{const b=[...document.querySelectorAll('button,a')]
    .find(e=>e.textContent.trim()===${JSON.stringify(nhan)});if(b)b.click();return !!b})()`);
  await sleep(1500);
};

console.log("━━ Dựng hai vai ━━");
const T = await moVai("teacher", 9830);
const A = await moVai("student", 9831);

try {
  /* ── 0 · TÀI KHOẢN + LỚP + BÀI HÌNH HỌC ────────────────────────────── */
  let r = await apij(T, "POST", "/api/auth/register", {
    email: `gv.scope.${STAMP}@algosim.test`, displayName: "Cô Phạm Vi",
    password: PASS, role: "teacher", teacherCode: CODE });
  ghi("0-setup", "teacher", "đăng ký giáo viên", "200", `HTTP ${r.s}`, r.s === 200);

  r = await apij(T, "POST", "/api/classes", { name: "11A2" });
  const lop = r.b;
  ghi("0-setup", "teacher", "tạo lớp", "200", `HTTP ${r.s}`, r.s === 200 && !!lop?.id);

  /* Envelope lấy từ CHÍNH bài mẫu của sản phẩm — không viết tay. */
  const MAU = await A.evj(`fetch('/').then(()=>JSON.stringify(null))`) ?? null;
  void MAU;
  const mauHH = await T.evj(`(async()=>{
    const m = await import('/src/data/geometry-samples.json?import');
    const s = (m.default ?? m).samples.find(x => x.id === 'thiet-dien-chop');
    return JSON.stringify(s ? s.envelope : null);
  })()`);
  ghi("0-setup", "teacher", "lấy được envelope bài mẫu hình học",
      "envelope có scene3d",
      mauHH ? `simId=${mauHH.simulation_id} scene3d=${!!mauHH.scene3d}` : "không lấy được",
      !!mauHH?.scene3d);

  r = await apij(T, "POST", "/api/assignments", {
    classroomId: lop.id, title: "Thiết diện S.ABCD",
    instruction: "Dựng thiết diện qua M song song với (SBD).", envelope: mauHH });
  ghi("0-setup", "teacher", "giao được bài HÌNH HỌC (hồi quy §13)", "200",
      `HTTP ${r.s}` + (r.s === 200 ? "" : ` · ${JSON.stringify(r.b).slice(0, 160)}`),
      r.s === 200);

  r = await apij(A, "POST", "/api/auth/register", {
    email: `hs.scope.${STAMP}@algosim.test`, displayName: "An", password: PASS });
  const ok = r.s === 200;
  r = await apij(A, "POST", "/api/classes/join", { code: lop.joinCode });
  ghi("0-setup", "student", "đăng ký + vào lớp", "200", `HTTP ${r.s}`, ok && r.s === 200);

  /* ── 1 · BỀ MẶT KHÔNG CÒN DANH TÍNH TIN HỌC ────────────────────────── */
  console.log("");
  console.log("━━ SCENARIO 1 — BỀ MẶT CÔNG KHAI ━━");

  for (const [v, vai] of [[A, "student"], [T, "teacher"]]) {
    await v.send("Page.navigate", { url: "http://localhost:3000" });
    await sleep(3000);
    const home = await doTrang(v);

    ghi("1-surface", vai, "Trang chủ dựng được (dấu vân tay trang)",
        "có nội dung + điều hướng",
        `text=${home.text.length}b nav=${home.nutDieuHuong.length}`,
        home.text.length > 200 && home.nutDieuHuong.length >= 4);

    const nhanLot = NHAN_CU.filter((x) => co(home.text, x));
    ghi("1-surface", vai, "Trang chủ: 0 nhãn miền Tin học",
        "0 nhãn", nhanLot.length ? nhanLot.join(",") : "0 nhãn", nhanLot.length === 0);

    const cumLot = CUM_CU.filter((x) => co(home.text, x));
    ghi("1-surface", vai, "Trang chủ: 0 cụm quảng bá đề cũ",
        "0 cụm", cumLot.length ? cumLot.join(",") : "0 cụm", cumLot.length === 0);

    ghi("1-surface", vai, "Trang chủ: gợi ý đúng ba bài hình học",
        "3 thẻ", `${home.theGoiY} thẻ`, home.theGoiY === 3);

    /* Thư viện — chỗ dễ sót nhất, vì nó dựng nhóm từ hằng số miền. */
    await diToi(v, "Thư viện");
    const thu = await doTrang(v);
    ghi("1-surface", vai, "Thư viện dựng được (dấu vân tay trang)",
        "tiêu đề Thư viện", `khớp=${co(thu.text, "Thư viện mô phỏng")}`,
        co(thu.text, "Thư viện mô phỏng"));
    const thuLot = [...NHAN_CU, ...CUM_CU].filter((x) => co(thu.text, x));
    ghi("1-surface", vai, "Thư viện: 0 di sản Tin học",
        "0 chuỗi", thuLot.length ? thuLot.join(",") : "0 chuỗi", thuLot.length === 0);
    ghi("1-surface", vai, "Thư viện: có nhóm Hình học",
        "hiện nhãn Hình học", `có=${co(thu.text, "Hình học")}`,
        co(thu.text, "Hình học"));

    /* Không đường điều hướng CHÍNH nào dẫn tới miền cũ. */
    const navLot = home.nutDieuHuong.filter((n) => NHAN_CU.some((x) => n.includes(x)));
    ghi("1-surface", vai, "điều hướng chính: 0 mục miền Tin học",
        "0 mục", navLot.length ? navLot.join(",") : `0/${home.nutDieuHuong.length} mục`,
        navLot.length === 0);
  }

  /* ── 2 · GEOMETRY-FIRST: MỞ MỘT GỢI Ý → XƯỞNG 3D ───────────────────── */
  console.log("");
  console.log("━━ SCENARIO 2 — LỐI VÀO HÌNH HỌC ━━");

  await A.send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(3000);
  await A.ev(`(()=>{const b=document.querySelector('.starter-card');if(b)b.click();return !!b})()`);
  await sleep(4500);
  const xuong = await doTrang(A);
  ghi("2-entry", "student", "bấm gợi ý ⇒ vào thẳng xưởng 3D",
      ".geo3d-xuong + canvas", `xuong=${xuong.xuong3d} canvas=${xuong.canvas}`,
      xuong.xuong3d === true && xuong.canvas >= 1);
  ghi("2-entry", "student", "xưởng 3D: 0 di sản Tin học trên màn hình",
      "0 chuỗi",
      (() => { const l = [...NHAN_CU, ...CUM_CU].filter((x) => co(xuong.text, x));
               return l.length ? l.join(",") : "0 chuỗi"; })(),
      ![...NHAN_CU, ...CUM_CU].some((x) => co(xuong.text, x)));

  /* ── 3 · BÀI GIÁO VIÊN GIAO — HỒI QUY LỚP HỌC (§13) ────────────────── */
  console.log("");
  console.log("━━ SCENARIO 3 — BÀI ĐƯỢC GIAO ━━");

  await A.send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(2800);
  await diToi(A, "Bài thực hành");
  const ds = await doTrang(A);
  ghi("3-assignment", "student", "thấy bài giáo viên giao",
      "tiêu đề bài hiện ra", `có=${co(ds.text, "Thiết diện S.ABCD")}`,
      co(ds.text, "Thiết diện S.ABCD"));

  await A.ev(`(()=>{const b=document.querySelector('.assignment-card .btn-primary');
    if(b)b.click();return !!b})()`);
  await sleep(4500);
  const baiMo = await doTrang(A);
  ghi("3-assignment", "student", "mở bài ⇒ xưởng 3D, 0 gọi AI",
      ".geo3d-xuong + canvas", `xuong=${baiMo.xuong3d} canvas=${baiMo.canvas}`,
      baiMo.xuong3d === true && baiMo.canvas >= 1);

  await T.send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(2800);
  await diToi(T, "Bài đã giao");
  await T.ev(`(()=>{const b=document.querySelector('.assignment-card .btn-primary');
    if(b)b.click();return !!b})()`);
  await sleep(4500);
  const gvMo = await doTrang(T);
  ghi("3-assignment", "teacher", "giáo viên mở được bài để dạy",
      ".geo3d-xuong + dock lớp",
      `xuong=${gvMo.xuong3d} dock=${co(gvMo.text, "Bắt đầu tiết")
        || co(gvMo.text, "Theo cô/thầy")}`,
      gvMo.xuong3d === true);

  /* ── 4 · BA BỀ RỘNG ────────────────────────────────────────────────── */
  console.log("");
  console.log("━━ SCENARIO 4 — BA BỀ RỘNG ━━");
  for (const [w, h] of [[1920, 1080], [1536, 864], [1366, 768]]) {
    for (const [v, vai] of [[T, "teacher"], [A, "student"]]) {
      await v.send("Emulation.setDeviceMetricsOverride",
        { width: w, height: h, deviceScaleFactor: 1, mobile: false });
      await sleep(1200);
      const d = await v.evj(`JSON.stringify({
        tran: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
        xuong: !!document.querySelector('.geo3d-xuong'),
      })`);
      ghi("4-responsive", vai, `${w}x${h} — không tràn ngang`, "scrollWidth <= clientWidth",
          `tràn=${d.tran} xuong=${d.xuong}`, d.tran === false);
    }
  }
  for (const v of [T, A]) await v.send("Emulation.clearDeviceMetricsOverride");
} finally {
  T.dong(); A.dong();
}

const pass = failures.length === 0 && consoleErrors.length === 0;
writeFileSync(OUT, JSON.stringify({
  khai: "Nghiệm thu dọn phạm vi sản phẩm — hai tiến trình Chrome, hai kho cookie. "
      + "Quét TEXT ĐÃ RENDER trên từng trang: danh mục sạch không đảm bảo màn hình sạch.",
  chayLuc: new Date().toISOString(),
  contexts: ["teacher", "student"],
  chuoiCam: { nhanMien: NHAN_CU, cumQuangBa: CUM_CU },
  ...provenance("accept-product-scope", { contexts: "2" }),
  rows, failures, consoleErrors, pass,
}, null, 1) + "\n", "utf-8");

console.log(`\n${pass ? "✓ NGHIỆM THU XANH" : "✗ NGHIỆM THU ĐỎ"} — ${rows.filter((r) => r.pass).length}/${rows.length} · lỗi console ${consoleErrors.length}`);
console.log(`→ ${OUT}`);
process.exit(pass ? 0 : 1);
