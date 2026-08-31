/**
 * accept-live-classroom.mjs — NGHIỆM THU LỚP TRỰC TIẾP, BA TRÌNH DUYỆT THẬT.
 *
 * ─── VÌ SAO BA TIẾN TRÌNH CHROME, KHÔNG PHẢI BA TAB ─────────────────────
 *
 * Ba vai phải có ba kho cookie ĐỘC LẬP. Cùng một `--user-data-dir` thì phiên
 * đăng nhập sau đè lên phiên trước, và mọi khẳng định "học sinh A không sửa
 * được state của B" trở thành vô nghĩa — cả hai vốn là một người.
 *
 * Đổi vai bằng cách sửa state client (thứ một script lười sẽ làm) còn tệ hơn:
 * nó kiểm chính cái giả định đang cần chứng minh.
 *
 * ─── HAI CÁI BẪY ĐÃ CẮN Ở WAVE TRƯỚC ────────────────────────────────────
 *
 *   1. Dấu vân tay trang: không thấy đúng bề mặt thì THOÁT != 0, không lặng lẽ
 *      báo "sạch" cho một trang trống.
 *   2. Cổng :8000 có thể bị một container Docker cũ chiếm. Kiểm danh tính
 *      backend — phải có endpoint phiên dạy — trước khi tin bất cứ kết quả nào.
 *
 * Cần: `npm run dev` (:3000) + uvicorn (:8000) với `ALGOSIM_TEACHER_SIGNUP_CODE`.
 */
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { provenance } from "./evidence.mjs";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(argOf("--out",
  new URL("../../docs/evaluation/geometry/live-classroom-acceptance.json",
    import.meta.url).pathname.replace(/^[/]/, "")));
mkdirSync(dirname(OUT), { recursive: true });

const PASS = argOf("--pass", "accept-live-12345");
const CODE = argOf("--teacher-code", "ACCEPT-TEACHER");
const STAMP = Date.now();
const GV = `gv.live.${STAMP}@algosim.test`;
const HS_A = `hsa.live.${STAMP}@algosim.test`;
const HS_B = `hsb.live.${STAMP}@algosim.test`;

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
/* Dấu vân tay phải soi ĐƯỜNG DẪN MỚI, không phải một endpoint mà backend cũ
   cũng có. Bản đầu chỉ kiểm `/api/auth/me` trả 200 — và một container Docker
   cũ trên cùng cổng cũng trả 200, nên script chạy tiếp rồi đỏ ở tận Scenario 1
   với một thông điệp không liên quan (403 lúc đăng ký).

   Và soi qua ĐÚNG ORIGIN mà trình duyệt dùng (:3000, có proxy): `localhost`
   phân giải `::1` trước `127.0.0.1` trên Windows, nên curl vào 127.0.0.1 có
   thể nói chuyện với một tiến trình khác hẳn cái mà trang web nói chuyện. */
/* Backend sau proxy phải BIẾT các route phiên dạy. `/openapi.json` KHÔNG đi
   qua proxy (vite chỉ chuyển tiếp `/api`), nên hỏi thẳng route: FastAPI trả
   `{"detail":"Not Found"}` khi route không tồn tại, còn handler của ta trả
   thông điệp tiếng Việt của chính nó. Hai câu trả lời cùng mã 404 — chỉ phần
   thân phân biệt được, nên đừng kiểm bằng status. */
for (const [duong, method] of [["/api/classes/999999/session", "GET"],
                               ["/api/classes/999999/monitor", "GET"]]) {
  const r = await fetch(`http://localhost:3000${duong}`, { method })
    .then((x) => x.json()).catch(() => null);
  if (!r || r.detail === "Not Found") {
    console.error(`✗ Backend sau proxy :3000 KHÔNG có route ${duong}.`);
    console.error("  Nhiều khả năng một container Docker cũ đang giữ cổng 8000.");
    console.error("  Chạy: docker compose stop backend  rồi khởi động lại uvicorn.");
    process.exit(2);
  }
}

/* ── MỘT VAI = MỘT TIẾN TRÌNH CHROME ───────────────────────────────────── */
async function moVai(ten, cdpPort) {
  const dir = mkdtempSync(join(tmpdir(), `live-${ten}-`));
  const proc = spawn(CHROME, ["--headless=new", "--disable-gpu",
    `--remote-debugging-port=${cdpPort}`, `--user-data-dir=${dir}`,
    "--window-size=1600,900", "--hide-scrollbars",
    /* Không có ba cờ này thì headless không có WebGL, `scene3d-view` rơi về
       thông điệp dự phòng, và Scenario 5 sẽ khẳng định một màn hình xin lỗi
       thay vì khẳng định hình 3D. */
    "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
    "about:blank"],
    { stdio: "ignore" });

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
  return { ten, proc, send, ev, evj, dong: () => { try { ws.close(); } catch {} proc.kill(); } };
}

const api = (v, method, path, body) => v.ev(
  `fetch(${JSON.stringify(path)},{method:${JSON.stringify(method)},credentials:'include',
   headers:{'Content-Type':'application/json'}${body ? `,body:JSON.stringify(${JSON.stringify(body)})` : ""}})
   .then(async r=>JSON.stringify({s:r.status,b:await r.json().catch(()=>null)}))`);

const apij = async (v, method, path, body) => JSON.parse(await api(v, method, path, body));

console.log("━━ Dựng ba vai (ba tiến trình Chrome, ba kho cookie) ━━");
const T = await moVai("teacher", 9810);
const A = await moVai("studentA", 9811);
const B = await moVai("studentB", 9812);

try {
  /* ── CHUẨN BỊ: tài khoản, lớp, bài ─────────────────────────────────── */
  let r = await apij(T, "POST", "/api/auth/register",
    { email: GV, displayName: "Cô Nghiệm Thu", password: PASS,
      role: "teacher", teacherCode: CODE });
  ghi("0-setup", "teacher", "đăng ký giáo viên", "200", `HTTP ${r.s}`, r.s === 200);

  r = await apij(T, "POST", "/api/classes", { name: "11A1" });
  const lop = r.b;
  ghi("0-setup", "teacher", "tạo lớp", "200 + mã lớp",
      `HTTP ${r.s} · mã ${lop?.joinCode}`, r.s === 200 && !!lop?.joinCode);

  /* Envelope lấy từ CHÍNH bài mẫu hình học của sản phẩm, không viết tay: viết
     tay một envelope 2D thì Scenario 5 chạy trên một bề mặt không phải bề mặt
     đang nghiệm thu, và "xưởng 3D không hỏng" thành một câu vô nghĩa. */
  const MAU = JSON.parse(readFileSync(
    new URL("../src/data/geometry-samples.json", import.meta.url), "utf-8"));
  const BAI_MAU = MAU.samples.find((x) => x.id === "thiet-dien-chop");
  if (!BAI_MAU) { console.error("✗ Không thấy bài mẫu thiet-dien-chop"); process.exit(4); }
  const ENVELOPE = BAI_MAU.envelope;
  r = await apij(T, "POST", "/api/assignments",
    { classroomId: lop.id, title: "Thiết diện S.ABCD",
      instruction: "Dựng thiết diện", envelope: ENVELOPE });
  const bai = r.b;
  ghi("0-setup", "teacher", "giao bài", "200 + id bài",
      `HTTP ${r.s} · id ${bai?.id}` +
      (r.s === 200 && bai?.id ? "" : ` · ${JSON.stringify(r.b).slice(0, 240)}`),
      r.s === 200 && typeof bai?.id === "number");

  for (const [v, email, ten] of [[A, HS_A, "An"], [B, HS_B, "Bình"]]) {
    let x = await apij(v, "POST", "/api/auth/register",
      { email, displayName: ten, password: PASS });
    const ok1 = x.s === 200;
    x = await apij(v, "POST", "/api/classes/join", { code: lop.joinCode });
    ghi("0-setup", v.ten, "đăng ký + vào lớp", "200",
        `HTTP ${x.s}`, ok1 && x.s === 200);
  }

  /* ── SCENARIO 1 — BÁM THEO ─────────────────────────────────────────── */
  console.log("\n━━ SCENARIO 1 — BÁM THEO ━━");
  r = await apij(T, "POST", `/api/classes/${lop.id}/session`,
    { assignmentId: bai.id, mode: "follow" });
  const phien = r.b?.session;
  ghi("1-follow", "teacher", "bắt đầu tiết", "mode=follow, cmdId=0",
      `HTTP ${r.s} · mode=${phien?.mode} cmdId=${phien?.cmdId}` +
      (r.s === 200 ? "" : ` · ${JSON.stringify(r.b).slice(0, 200)}`),
      r.s === 200 && phien?.mode === "follow");

  const lenh = async (payload) => apij(T, "POST",
    `/api/classes/${lop.id}/session/command`, { ...payload, roundId: phien.roundId });

  let c = await lenh({ kind: "STATE_UPDATE", currentStep: 3 });
  ghi("1-follow", "teacher", "chuyển bước 2→3", "cmdId tăng",
      `cmdId=${c.b?.session?.cmdId} step=${c.b?.session?.currentStep}`,
      c.s === 200 && c.b.session.currentStep === 3 && c.b.session.cmdId === 1);

  await sleep(400);
  for (const v of [A, B]) {
    const s = (await apij(v, "GET", `/api/classes/${lop.id}/session`)).b?.session;
    ghi("1-follow", v.ten, "đọc được bước của giáo viên", "currentStep=3",
        `currentStep=${s?.currentStep}`, s?.currentStep === 3);
  }

  c = await lenh({ kind: "STATE_UPDATE", selectedId: "chop::face:1",
                   isolatedIds: ["chop::face:1"] });
  ghi("1-follow", "teacher", "chọn + cô lập mặt SAB", "selectedId lan tới HS",
      `selectedId=${c.b?.session?.selectedId}`,
      c.b?.session?.selectedId === "chop::face:1");

  await sleep(400);
  {
    const s = (await apij(A, "GET", `/api/classes/${lop.id}/session`)).b?.session;
    ghi("1-follow", "studentA", "nhận vật giáo viên chọn",
        "chop::face:1 + isolate", `selected=${s?.selectedId} isolate=${JSON.stringify(s?.isolatedIds)}`,
        s?.selectedId === "chop::face:1" && s?.isolatedIds?.[0] === "chop::face:1");
  }

  /* ── SCENARIO 2 — TỰ DO ────────────────────────────────────────────── */
  console.log("\n━━ SCENARIO 2 — TỰ DO ━━");
  c = await lenh({ kind: "SET_MODE", mode: "free" });
  ghi("2-free", "teacher", "thả lớp ra tự do", "mode=free",
      `mode=${c.b?.session?.mode}`, c.b?.session?.mode === "free");

  await apij(A, "POST", `/api/assignments/${bai.id}/progress`,
    { cursor: 2, stepCount: 8, selectedId: "chop::face:1",
      lastAction: "ISOLATE_ENTITY" });
  await apij(B, "POST", `/api/assignments/${bai.id}/progress`,
    { cursor: 5, stepCount: 8, selectedId: "M", lastAction: "SELECT_ENTITY" });
  await sleep(300);

  {
    const m = (await apij(T, "GET", `/api/classes/${lop.id}/monitor`)).b;
    const byName = Object.fromEntries((m?.rows ?? []).map((x) => [x.studentName, x]));
    const okA = byName["An"]?.selectedId === "chop::face:1" && byName["An"]?.currentStep === 2;
    const okB = byName["Bình"]?.selectedId === "M" && byName["Bình"]?.currentStep === 5;
    ghi("2-free", "teacher", "hai học sinh giữ tiêu điểm RIÊNG",
        "An=face:1@2, Bình=M@5",
        `An=${byName["An"]?.selectedId}@${byName["An"]?.currentStep}, ` +
        `Bình=${byName["Bình"]?.selectedId}@${byName["Bình"]?.currentStep}`, okA && okB);
  }

  /* ── SCENARIO 3 — GỌI CẢ LỚP VỀ ────────────────────────────────────── */
  console.log("\n━━ SCENARIO 3 — GỌI CẢ LỚP VỀ ━━");
  c = await lenh({ kind: "SYNC_CLASS", currentStep: 6, selectedId: "td" });
  const daSync = c.b?.session;
  ghi("3-sync", "teacher", "gọi cả lớp về", "syncCmdId=cmdId VÀ mode vẫn free",
      `sync=${daSync?.syncCmdId} cmd=${daSync?.cmdId} mode=${daSync?.mode}`,
      daSync?.syncCmdId === daSync?.cmdId && daSync?.mode === "free");

  await sleep(400);
  for (const v of [A, B]) {
    const s = (await apij(v, "GET", `/api/classes/${lop.id}/session`)).b?.session;
    ghi("3-sync", v.ten, "thấy mốc đồng bộ mới", "syncCmdId>0 và step=6",
        `sync=${s?.syncCmdId} step=${s?.currentStep}`,
        s?.syncCmdId > 0 && s?.currentStep === 6);
  }

  /* ── SCENARIO 4 — TRỢ GIÚP ─────────────────────────────────────────── */
  console.log("\n━━ SCENARIO 4 — TRỢ GIÚP ━━");
  r = await apij(A, "POST", `/api/assignments/${bai.id}/help`, { requested: true });
  ghi("4-help", "studentA", "giơ tay", "helpRequested=true + mốc máy chủ",
      `${r.b?.helpRequested} @ ${r.b?.helpRequestedAt}`,
      r.s === 200 && r.b?.helpRequested === true && !!r.b?.helpRequestedAt);

  let sid = null;
  {
    const m = (await apij(T, "GET", `/api/classes/${lop.id}/monitor`)).b;
    const an = (m?.rows ?? []).find((x) => x.studentName === "An");
    sid = an?.studentId;
    ghi("4-help", "teacher", "thấy An cần hỗ trợ, đúng bước + tiêu điểm",
        "help=true, step=2, selected=chop::face:1",
        `help=${an?.helpRequested} step=${an?.currentStep} sel=${an?.selectedId} chờ=${an?.helpWaitingSeconds}s`,
        an?.helpRequested === true && an?.currentStep === 2 &&
        an?.selectedId === "chop::face:1" &&
        typeof an?.helpWaitingSeconds === "number");
    const b1 = (m?.rows ?? []).find((x) => x.studentName === "Bình");
    ghi("4-help", "teacher", "Bình KHÔNG bị đánh dấu lây", "help=false",
        `help=${b1?.helpRequested}`, b1?.helpRequested === false);
  }

  r = await apij(T, "POST", `/api/classes/${lop.id}/help/${sid}/clear`);
  ghi("4-help", "teacher", "đánh dấu đã hỗ trợ", "cleared=1",
      `cleared=${r.b?.cleared}`, r.s === 200 && r.b?.cleared === 1);
  {
    const m = (await apij(T, "GET", `/api/classes/${lop.id}/monitor`)).b;
    const an = (m?.rows ?? []).find((x) => x.studentName === "An");
    ghi("4-help", "teacher", "cờ trợ giúp đã tắt", "help=false",
        `help=${an?.helpRequested}`, an?.helpRequested === false);
  }

  /* ── SCENARIO 5 — GIAO DIỆN THẬT: ĐÚNG VAI, XƯỞNG 3D KHÔNG HỎNG ───── */
  /* Bốn scenario trên đi thẳng vào API. Chúng chứng minh THẨM QUYỀN và CÁCH LY
     — không chứng minh cái gì DỰNG LÊN MÀN HÌNH. Một giao diện quên nối vào
     store vẫn để toàn bộ phần trên xanh. Đây là chỗ hỏi câu còn lại. */
  console.log("");
  console.log("━━ SCENARIO 5 — GIAO DIỆN & XƯỞNG 3D ━━");

  const vaoBai = async (v) => {
    await v.send("Page.navigate", { url: "http://localhost:3000" });
    await sleep(2600);
    await v.ev(`(()=>{const b=[...document.querySelectorAll('button,a')]
      .find(e=>['Bài thực hành','Bài đã giao'].includes(e.textContent.trim()));
      if(b)b.click();return !!b})()`);
    await sleep(1400);
    await v.ev(`(()=>{const b=document.querySelector('.assignment-card .btn-primary');
      if(b)b.click();return !!b})()`);
    await sleep(4200);
  };

  const dom = (v) => v.evj(`JSON.stringify({
    text: document.body.innerText,
    dock: !!document.querySelector('.live-dock,.live-dock-thu'),
    radio: !!document.querySelector('.live-dock [role="radiogroup"]'),
    xuong: !!document.querySelector('.geo3d-xuong'),
    canvasEl: document.querySelectorAll('.geo3d-canvas canvas').length,
    duPhong: !!document.querySelector('.geo3d-fallback'),
    nutXem: document.querySelectorAll('.geo3d-noi-nut').length,
    muc: document.querySelectorAll('.geo3d-tree-nhan').length,
  })`);

  /* Viết bằng `new RegExp` chứ không phải literal: một dấu thoát trong khối này
     bị môi trường build nuốt mất, và regex hỏng thì xanh vì lý do sai. */
  const CHI_BAO = new RegExp("Đang theo cô/thầy|Em tự khám phá|kết nối lại");

  for (const v of [T, A, B]) await vaoBai(v);
  const dT = await dom(T);
  const dA = await dom(A);

  /* DẤU VÂN TAY TRANG trước mọi khẳng định khác: đứng sai chỗ (hay trang trắng)
     thì mọi `không chứa X` bên dưới xanh hết, và xanh vì màn hình rỗng. */
  ghi("5-ui", "teacher", "đứng đúng xưởng 3D (dấu vân tay trang)",
      ".geo3d-xuong có mặt + trang có nội dung",
      `xuong=${dT.xuong} text=${dT.text.length}b`,
      dT.xuong === true && dT.text.length > 200);
  ghi("5-ui", "studentA", "đứng đúng xưởng 3D (dấu vân tay trang)",
      ".geo3d-xuong có mặt + trang có nội dung",
      `xuong=${dA.xuong} text=${dA.text.length}b`,
      dA.xuong === true && dA.text.length > 200);

  ghi("5-ui", "teacher", "dock lớp dựng trong xưởng", "có .live-dock",
      `dock=${dT.dock} radiogroup=${dT.radio}`, dT.dock === true);
  ghi("5-ui", "teacher", "KHÔNG thấy nút giơ tay của học sinh", "vắng mặt",
      `có=${dT.text.includes("Em cần hỗ trợ")}`, !dT.text.includes("Em cần hỗ trợ"));

  ghi("5-ui", "studentA", "thấy chỉ báo lớp + nút giơ tay",
      "chỉ báo chế độ + «Em cần hỗ trợ»",
      `chiBao=${CHI_BAO.test(dA.text)} gioTay=${dA.text.includes("Em cần hỗ trợ")}`,
      CHI_BAO.test(dA.text) && dA.text.includes("Em cần hỗ trợ"));
  ghi("5-ui", "studentA", "KHÔNG thấy điều khiển lớp của giáo viên",
      "vắng dock + «Gọi cả lớp về đây»",
      `dock=${dA.dock} goiVe=${dA.text.includes("Gọi cả lớp về đây")}`,
      dA.dock === false && !dA.text.includes("Gọi cả lớp về đây"));

  /* Định danh kỹ thuật lọt lên bề mặt học sinh là bug ĐÃ SHIP HAI LẦN (§8 #10). */
  const ro = ["follow", "free", "cmdId", "cmd_id", "roundId", "selected_id",
              "generic.semantic_program", "STATE_UPDATE", "SYNC_CLASS"]
    .filter((x) => dA.text.includes(x));
  ghi("5-ui", "studentA", "không rò định danh kỹ thuật lên màn hình",
      "0 chuỗi", ro.length ? ro.join(",") : "0 chuỗi", ro.length === 0);

  /* HỒI QUY 3D — hình phải THẬT SỰ dựng, không phải thông điệp dự phòng. */
  ghi("5-ui", "studentA", "WebGL dựng được hình, không rơi về dự phòng",
      "canvas >= 1, fallback vắng",
      `canvas=${dA.canvasEl} duPhong=${dA.duPhong}`,
      dA.canvasEl >= 1 && dA.duPhong === false);
  /* Đúng HAI nút nổi: «Tách khối» và «Xem lại toàn hình». Xoay và thu-phóng
     là CỬ CHỈ CHUỘT trên canvas, không phải nút — bản đầu của guard này đòi ba
     nút và đỏ vì kỳ vọng của người viết, không vì sản phẩm. */
  ghi("5-ui", "studentA", "hai nút nổi (tách khối · xem lại toàn hình) còn đủ",
      "đúng 2 nút", `${dA.nutXem} nút`, dA.nutXem === 2);

  /* Bấm một vật trong cây hình: đường tương tác 3D của HỌC SINH, đường này
     không đi qua tầng lớp học — chết ở đây thì mọi khẳng định trên vẫn xanh. */
  /* Cây hình nằm trong NGĂN KÉO, mặc định ĐÓNG — đó là canvas-first đúng ý
     đồ, không phải lỗi. Phải mở ngăn rồi mới hỏi, nếu không guard đo một ngăn
     đóng và kết luận cây hỏng. */
  await A.ev(`(()=>{const b=[...document.querySelectorAll('.geo3d-chip')]
    .find(e=>e.textContent.includes('Thành phần'));if(b)b.click();return !!b})()`);
  await sleep(900);
  const daMo = await dom(A);
  ghi("5-ui", "studentA", "mở được ngăn «Thành phần» (cây hình)",
      "cây có mục", `${daMo.muc} mục`, daMo.muc > 0);

  const bam = await A.evj(`(()=>{
    const n=[...document.querySelectorAll('.geo3d-tree-nhan')];
    if(!n.length) return JSON.stringify({co:0});
    const t=n[0].closest('button')||n[0].closest('li')||n[0];
    t.click();
    return JSON.stringify({co:n.length, ten:n[0].textContent.trim()});
  })()`);
  await sleep(1000);
  const sauBam = await dom(A);
  ghi("5-ui", "studentA", "bấm được một vật trong cây hình",
      "cây có mục, bấm xong xưởng còn nguyên",
      `mục=${bam.co} vật=${bam.ten ?? "-"} xưởng-còn=${sauBam.xuong}`,
      bam.co > 0 && sauBam.xuong === true);

  /* ── SCENARIO 6 — UỶ QUYỀN ─────────────────────────────────────────── */
  console.log("\n━━ SCENARIO 6 — UỶ QUYỀN ━━");
  r = await apij(A, "POST", `/api/classes/${lop.id}/session/command`,
    { kind: "SET_MODE", mode: "follow", roundId: phien.roundId });
  ghi("6-auth", "studentA", "thử đổi chế độ lớp", "403", `HTTP ${r.s}`, r.s === 403);

  r = await apij(A, "GET", `/api/classes/${lop.id}/monitor`);
  ghi("6-auth", "studentA", "thử đọc bảng theo dõi", "403", `HTTP ${r.s}`, r.s === 403);

  r = await apij(B, "POST", `/api/classes/${lop.id}/help/${sid}/clear`);
  ghi("6-auth", "studentB", "thử xoá cờ trợ giúp của An", "403",
      `HTTP ${r.s}`, r.s === 403);

  r = await apij(A, "POST", `/api/classes/${lop.id}/session`,
    { assignmentId: bai.id, mode: "free" });
  ghi("6-auth", "studentA", "thử bắt đầu tiết", "403", `HTTP ${r.s}`, r.s === 403);

  /* ── KẾT THÚC TIẾT ─────────────────────────────────────────────────── */
  r = await apij(T, "DELETE", `/api/classes/${lop.id}/session`);
  ghi("7-end", "teacher", "kết thúc tiết", "session=null",
      `session=${JSON.stringify(r.b?.session)}`, r.s === 200 && r.b?.session === null);
  {
    const s = (await apij(A, "GET", `/api/classes/${lop.id}/session`)).b;
    ghi("7-end", "studentA", "không còn phiên để bám", "session=null",
        `session=${JSON.stringify(s?.session)}`, s?.session === null);
  }
  /* ── SCENARIO 8 — BA BỀ RỘNG MÁY PHÒNG TIN ────────────────────────── */
  /* Không phải "responsive" chung chung: ba con số này là ba cỡ màn hình có
     thật trong phòng máy. Câu hỏi là DÙNG ĐƯỢC KHÔNG, nên guard soi hai thứ
     hỏng được: trang tràn ngang, và điều khiển của vai bị cắt khỏi khung. */
  console.log("");
  console.log("━━ SCENARIO 8 — BA BỀ RỘNG ━━");

  const BE_RONG = [[1920, 1080], [1536, 864], [1366, 768]];

  const doBeRong = async (v, w, h) => {
    await v.send("Emulation.setDeviceMetricsOverride",
      { width: w, height: h, deviceScaleFactor: 1, mobile: false });
    await sleep(1300);
    return v.evj(`JSON.stringify((()=>{
      const de=document.documentElement;
      const trong=(el)=>{ if(!el) return null;
        const r=el.getBoundingClientRect();
        return {w:Math.round(r.width), h:Math.round(r.height),
                lot: r.left >= -1 && r.right <= window.innerWidth + 1
                     && r.width > 0 && r.height > 0}; };
      return {
        tranNgang: de.scrollWidth > de.clientWidth + 1,
        rong: window.innerWidth,
        canvas: trong(document.querySelector('.geo3d-canvas canvas')),
        dock: trong(document.querySelector('.live-dock')),
        gioTay: trong([...document.querySelectorAll('button')]
          .find(b=>b.textContent.includes('Em cần hỗ trợ'))),
      };
    })())`);
  };

  for (const [w, h] of BE_RONG) {
    for (const [v, vai] of [[T, "teacher"], [A, "studentA"]]) {
      const d = await doBeRong(v, w, h);
      ghi("8-responsive", vai, `${w}x${h} — không tràn ngang`,
          "scrollWidth <= clientWidth",
          `tràn=${d.tranNgang} rộng=${d.rong}`, d.tranNgang === false);
      ghi("8-responsive", vai, `${w}x${h} — hình 3D còn thấy được`,
          "canvas lọt trong khung, kích thước > 0",
          d.canvas ? `${d.canvas.w}x${d.canvas.h} lọt=${d.canvas.lot}` : "vắng",
          d.canvas !== null && d.canvas.lot === true);

      /* Điều khiển của VAI phải còn với tới được — mỗi vai một thứ khác nhau,
         nên không hỏi chung một câu cho cả hai. */
      const dk = vai === "teacher" ? d.dock : d.gioTay;
      const ten = vai === "teacher" ? "dock lớp" : "nút giơ tay";
      ghi("8-responsive", vai, `${w}x${h} — ${ten} không bị cắt khỏi khung`,
          "nằm trọn trong khung nhìn",
          dk ? `${dk.w}x${dk.h} lọt=${dk.lot}` : "vắng",
          dk !== null && dk.lot === true);
    }
  }
  for (const v of [T, A]) await v.send("Emulation.clearDeviceMetricsOverride");

} finally {
  T.dong(); A.dong(); B.dong();
}

const pass = failures.length === 0 && consoleErrors.length === 0;
writeFileSync(OUT, JSON.stringify({
  khai: "Nghiệm thu lớp trực tiếp — BA tiến trình Chrome, ba kho cookie độc lập. "
      + "Không đổi vai bằng cách sửa state client.",
  chayLuc: new Date().toISOString(),
  contexts: ["teacher", "studentA", "studentB"],
  /* Bằng chứng buộc vào MÃ NGUỒN, không vào HEAD: sửa một dòng mã sản phẩm là
     artifact này thành `STALE_SOURCE`, và ledger cấm ghi DONE khi bằng chứng đã
     cũ. Thiếu khối này thì con số ở đây không gắn với bản nào cả. */
  ...provenance("accept-live-classroom", { contexts: "3" }),
  rows, failures, consoleErrors, pass,
}, null, 1) + "\n", "utf-8");

console.log(`\n${pass ? "✓ NGHIỆM THU XANH" : "✗ NGHIỆM THU ĐỎ"} — ${rows.filter(r => r.pass).length}/${rows.length} · lỗi console ${consoleErrors.length}`);
console.log(`→ ${OUT}`);
process.exit(pass ? 0 : 1);
