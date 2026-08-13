/**
 * accept-classroom-m18.mjs — NGHIỆM THU TẦNG LỚP HỌC TRONG CHROME THẬT.
 *
 * Bốn bề rộng, ba vai (khách · học sinh · giáo viên). Mỗi khẳng định nói về một
 * điều NHÌN THẤY ĐƯỢC hoặc một điều máy chủ TỪ CHỐI, không nói về mã nguồn.
 *
 * ⚠️ HAI CÁI BẪY ĐÃ CẮN Ở WAVE TRƯỚC, ghi lại để không lặp:
 *   1. dấu vân tay trang — không thấy đúng bề mặt thì THOÁT != 0, chứ không
 *      lặng lẽ báo "sạch" cho một trang trống;
 *   2. cổng :8000 có thể đang bị container Docker cũ chiếm. Script kiểm danh
 *      tính backend trước khi tin bất cứ kết quả nào.
 *
 * Cần: `npm run dev` (:3000) + uvicorn (:8000) + fixture đã seed.
 */
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const OUT = resolve(argOf("--out",
  new URL("../../docs/evaluation/m18/classroom-acceptance.json", import.meta.url)
    .pathname.replace(/^[/]/, "")));
mkdirSync(dirname(OUT), { recursive: true });

const PASSWORD = argOf("--pass", "dev-acceptance-12345");
const TEACHER = "gv.demo@algosim.test";
const STUDENT = "hs.an@algosim.test";
const VIEWPORTS = [[1920, 1080], [1536, 864], [1366, 768], [768, 900]];

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* Danh tính backend: endpoint tài khoản phải có mặt. Không có ⇒ đang nói
   chuyện với một backend cũ (container Docker), mọi kết quả sau đó vô nghĩa. */
const probe = await fetch("http://localhost:8000/api/auth/me").catch(() => null);
if (!probe || !probe.ok) {
  console.error("✗ Backend :8000 không trả lời /api/auth/me — container cũ đang chiếm cổng?");
  process.exit(2);
}

const failures = [];
const rows = [];
const fail = (m) => { failures.push(m); console.error(`  ✗ ${m}`); };

for (const [w, h] of VIEWPORTS) {
  const cdp = 9700 + Math.floor(Math.random() * 200);
  const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu",
    `--remote-debugging-port=${cdp}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "m18-"))}`,
    `--window-size=${w},${h}`, "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
  let url;
  for (let i = 0; i < 40 && !url; i++) {
    try { const l = await (await fetch(`http://127.0.0.1:${cdp}/json/list`)).json();
      url = l.find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch { /* chưa lên */ }
    if (!url) await sleep(250);
  }
  const ws = new WebSocket(url); await new Promise((r) => (ws.onopen = r));
  let id = 0; const pend = new Map();
  ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } };
  const send = (m, p = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async (x) => (await send("Runtime.evaluate",
    { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
  const evj = async (x) => JSON.parse(await ev(x));
  const login = async (email) => {
    await ev(`fetch('/api/auth/login',{method:'POST',credentials:'include',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({email:${JSON.stringify(email)},password:${JSON.stringify(PASSWORD)}})})
      .then(r=>r.json())`);
    await send("Page.reload"); await sleep(2600);
  };
  const logout = async () => {
    await ev(`fetch('/api/auth/logout',{method:'POST',credentials:'include'})`);
    await send("Page.reload"); await sleep(2600);
  };
  /* Đo bố cục: thanh điều hướng, tràn ngang, và bề rộng vùng nội dung. */
  const layout = () => evj(`(()=>{
    const q=(s)=>document.querySelector(s);
    const box=(el)=>{if(!el)return null;const r=el.getBoundingClientRect();
      return {x:Math.round(r.x),w:Math.round(r.width),visible:r.width>0&&r.height>0};};
    return JSON.stringify({
      nav: box(q('.app-nav')),
      navList: !!q('.app-nav-list'),
      drawerBtn: box(q('.nav-drawer-btn')),
      main: box(q('.app-main')),
      overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      loginBtn: !!([...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Đăng nhập')),
      hero: !!q('.home-title'),
    });
  })()`);

  await send("Page.enable"); await send("Runtime.enable");
  await send("Page.navigate", { url: "http://localhost:3000" });
  await sleep(3000);
  console.log(`\n━━ ${w}×${h}`);

  // ── 1. KHÁCH ────────────────────────────────────────────────────────────
  await logout();
  let L = await layout();
  if (!L.hero) fail(`${w}·khách: không thấy trang chủ (dấu vân tay sai)`);
  if (L.nav) fail(`${w}·khách: có thanh điều hướng ứng dụng khi CHƯA đăng nhập`);
  if (!L.loginBtn) fail(`${w}·khách: không có lối vào Đăng nhập`);
  if (L.overflowX) fail(`${w}·khách: trang tràn ngang`);

  const guestBlocked = await evj(`(async()=>{
    const r = await fetch('/api/classes',{credentials:'include'});
    const r2 = await fetch('/api/assignments',{credentials:'include'});
    return JSON.stringify({classes:r.status, assignments:r2.status});
  })()`);
  if (guestBlocked.classes !== 401) fail(`${w}·khách đọc được /api/classes (${guestBlocked.classes})`);
  if (guestBlocked.assignments !== 401) fail(`${w}·khách đọc được /api/assignments`);
  console.log(`  khách      nav=${L.nav ? "CÓ(sai)" : "không"}  tràn=${L.overflowX ? "CÓ" : "không"}  lớp/bài=401`);

  // ── 2. HỌC SINH ─────────────────────────────────────────────────────────
  await login(STUDENT);
  L = await layout();
  const wide = w > 900;
  if (!L.navList) fail(`${w}·học sinh: không dựng thanh điều hướng ứng dụng`);
  if (wide && !L.nav?.visible) fail(`${w}·học sinh: thanh điều hướng không hiện ở desktop`);
  if (!wide && L.nav && L.nav.x >= 0) fail(`${w}·học sinh: màn hẹp mà thanh vẫn chiếm chỗ (x=${L.nav.x})`);
  if (!wide && !L.drawerBtn?.visible) fail(`${w}·học sinh: màn hẹp không có nút mở ngăn kéo`);
  if (L.overflowX) fail(`${w}·học sinh: trang tràn ngang`);

  const stu = await evj(`(async()=>{
    const me = await (await fetch('/api/auth/me',{credentials:'include'})).json();
    const a  = await (await fetch('/api/assignments',{credentials:'include'})).json();
    const mk = await fetch('/api/classes',{method:'POST',credentials:'include',
      headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'Lớp giả'})});
    const ob = await fetch('/api/classes/1/observe',{credentials:'include'});
    return JSON.stringify({role:me.user?.role, assignments:a.assignments?.length ?? -1,
      createClass:mk.status, observe:ob.status});
  })()`);
  if (stu.role !== "student") fail(`${w}·học sinh: vai trò sai (${stu.role})`);
  if (stu.assignments < 1) fail(`${w}·học sinh: không nhận được bài thực hành nào`);
  if (stu.createClass !== 403) fail(`${w}·học sinh TẠO ĐƯỢC lớp (${stu.createClass})`);
  if (stu.observe !== 403) fail(`${w}·học sinh QUAN SÁT ĐƯỢC lớp (${stu.observe})`);
  console.log(`  học sinh   bài=${stu.assignments}  tạo lớp=${stu.createClass}  quan sát=${stu.observe}`);

  // ── 3. GIÁO VIÊN ────────────────────────────────────────────────────────
  await login(TEACHER);
  const tea = await evj(`(async()=>{
    const me = await (await fetch('/api/auth/me',{credentials:'include'})).json();
    const c  = await (await fetch('/api/classes',{credentials:'include'})).json();
    const cid = c.classes?.[0]?.id;
    const ob = await (await fetch('/api/classes/'+cid+'/observe',{credentials:'include'})).json();
    const bad = await fetch('/api/assignments',{method:'POST',credentials:'include',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({classroomId:cid,title:'Hỏng',
        envelope:{status:'ok',simulation_id:'logic.and_gate',config:{inputA:9,inputB:0}}})});
    return JSON.stringify({role:me.user?.role, classes:c.classes?.length ?? -1,
      hasCode: typeof c.classes?.[0]?.joinCode === 'string',
      rows: ob.rows?.length ?? -1,
      practicing: (ob.rows ?? []).filter(r=>r.status==='practicing').length,
      badAssign: bad.status,
      leaks: JSON.stringify(ob).toLowerCase()});
  })()`);
  if (tea.role !== "teacher") fail(`${w}·giáo viên: vai trò sai (${tea.role})`);
  if (tea.classes < 1) fail(`${w}·giáo viên: không thấy lớp của mình`);
  if (!tea.hasCode) fail(`${w}·giáo viên: không nhận được mã lớp`);
  if (tea.rows < 1) fail(`${w}·giáo viên: bảng quan sát rỗng`);
  if (tea.badAssign !== 400) fail(`${w}·envelope KHÔNG HỢP LỆ vẫn giao được (${tea.badAssign})`);
  for (const banned of ["verdict", "correct", "screenshot", "outerhtml"]) {
    if (tea.leaks.includes(banned)) fail(`${w}·bảng quan sát chứa "${banned}"`);
  }
  console.log(`  giáo viên  lớp=${tea.classes}  dòng quan sát=${tea.rows}  envelope hỏng=${tea.badAssign}`);

  rows.push({ viewport: `${w}x${h}`, guest: L, student: stu, teacher: tea });
  chrome.kill();
}

writeFileSync(OUT, JSON.stringify({ when: new Date().toISOString(), rows, failures }, null, 2));
console.log(`\n${failures.length === 0 ? "✔ TẤT CẢ SẠCH" : `✗ ${failures.length} lỗi`} → ${OUT}`);
process.exit(failures.length === 0 ? 0 : 1);
