/**
 * browser-runner.mjs — MỘT SERVER, NHIỀU KỊCH BẢN.
 *
 * ─── VẤN ĐỀ NÓ GIẢI ───────────────────────────────────────────────────────
 *
 * Mỗi script nghiệm thu trong kho tự dựng Chrome, tự chờ trang, tự nạp module.
 * Với W12 — 23 target × 4 bề rộng + chín màn trải nghiệm + thao tác trực tiếp —
 * cách ấy là hàng chục lượt khởi động lặp lại, và mỗi lượt là một cơ hội để một
 * lần chạy đo phải một server khác.
 *
 * Runner này giữ MỘT vòng đời: mở Chrome một lần, chờ trang một lần, chạy nhiều
 * kịch bản, dọn state giữa các kịch bản, đóng một lần.
 *
 * ─── CÁCH LY GIỮA CÁC KỊCH BẢN ────────────────────────────────────────────
 *
 * Không khởi động lại server để cách ly — dọn STATE. `resetBetweenScenarios`
 * gọi `store.reset()` và xoá lưu trữ, nên kịch bản sau bắt đầu từ fixture đã
 * khai. Khởi động lại chỉ dành cho thứ thật sự dính vào tiến trình.
 *
 * ⚠️ Có một bộ đếm vòng đời (`serverStarts`) được xuất ra artifact, và test đòi
 * nó bằng 1 cho một lượt chạy nhiều kịch bản. Không có nó thì một bản sửa vô ý
 * quay lại kiểu một-server-mỗi-kịch-bản mà chẳng ai biết.
 *
 * ⚠️ Backtick KHÔNG được xuất hiện trong biểu thức tiêm vào trang.
 */
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
].find(existsSync);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** Vòng đời trình duyệt — mở MỘT lần cho cả lượt chạy. */
export class BrowserSession {
  constructor({ viewport = 1920, height = 1080, url = "http://localhost:3000" } = {}) {
    this.viewport = viewport;
    this.height = height;
    this.url = url;
    this.serverStarts = 0;
    this.timings = { startup: 0, scenarios: [], cleanup: 0 };
    this._id = 0;
    this._pending = new Map();
  }

  async open() {
    if (!CHROME) throw new Error("Không tìm thấy Chrome.");
    const t0 = Date.now();
    const port = 9200 + Math.floor(Math.random() * 300);
    this.chrome = spawn(CHROME, ["--headless=new", "--disable-gpu",
      `--remote-debugging-port=${port}`,
      `--user-data-dir=${mkdtempSync(join(tmpdir(), "w12-"))}`,
      `--window-size=${this.viewport},${this.height}`,
      "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
    this.serverStarts += 1;

    let wsUrl;
    for (let i = 0; i < 40 && !wsUrl; i++) {
      try {
        const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
        wsUrl = list.find((t) => t.type === "page")?.webSocketDebuggerUrl;
      } catch { /* chưa lên */ }
      if (!wsUrl) await sleep(250);
    }
    this.ws = new WebSocket(wsUrl);
    await new Promise((r) => (this.ws.onopen = r));
    this.ws.onmessage = (e) => {
      const m = JSON.parse(e.data);
      if (m.id && this._pending.has(m.id)) { this._pending.get(m.id)(m); this._pending.delete(m.id); }
    };
    await this._send("Page.enable");
    await this._send("Runtime.enable");
    await this._send("Page.navigate", { url: this.url });
    await sleep(3200);

    /* DẤU VÂN TAY TRANG — sai route thì hỏng to, không im lặng báo sạch. */
    if (!(await this.eval(`document.querySelectorAll('.app-main,.nav-bar').length`))) {
      throw new Error("Không nhận ra trang — sai route hoặc server chưa sẵn sàng?");
    }
    this.mods = JSON.parse(await this.eval(`(()=>{const pick=(s)=>{
      const h=performance.getEntriesByType('resource').map(e=>e.name).filter(n=>n.includes(s));
      return h.length?h[h.length-1]:new URL(s,location.origin).href;};
      return JSON.stringify({store:pick('/src/state/store.ts'),catalog:pick('/src/data/offline-catalog.ts'),
      registry:pick('/src/simulations/registry.ts'),sims:pick('/src/simulations/index.ts')});})()`));
    await this.eval(`(async()=>{${Object.values(this.mods)
      .map((x) => `await import(${JSON.stringify(x)});`).join("")}return 1})()`);
    this.timings.startup = Date.now() - t0;
    return this;
  }

  _send(method, params = {}) {
    return new Promise((res) => {
      const id = ++this._id;
      this._pending.set(id, res);
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async eval(expression) {
    const r = await this._send("Runtime.evaluate",
      { expression, awaitPromise: true, returnByValue: true });
    const ex = r.result?.exceptionDetails;
    if (ex) return "LỖI: " + String(ex.exception?.description ?? ex.text ?? "?")
      .split(String.fromCharCode(10))[0];
    return r.result?.result?.value;
  }

  /** Đặt lại về fixture đã khai — KHÔNG khởi động lại tiến trình. */
  async resetBetweenScenarios() {
    return this.eval(`(async()=>{
      const s=await import(${JSON.stringify(this.mods.store)});
      s.useAppStore.getState().reset();
      try { localStorage.clear(); sessionStorage.clear(); } catch (e) { void e; }
      return 'ok';})()`);
  }

  /** Nạp một target từ danh mục mẫu offline. Thử lại một lần (flake CDP đã ghi). */
  async loadTarget(simId) {
    const run = () => this.eval(`(async()=>{
      const s=await import(${JSON.stringify(this.mods.store)});
      const c=await import(${JSON.stringify(this.mods.catalog)});
      const rg=await import(${JSON.stringify(this.mods.sims)});
      const reg=await import(${JSON.stringify(this.mods.registry)});
      if(reg.listSimulations().length===0) rg.registerAllSimulations();
      const e=c.offlineCatalog().find(x=>x.simId===${JSON.stringify(simId)});
      if(!e) return 'không có mẫu';
      try { s.useAppStore.getState().loadEnvelope(e.envelope); } catch (err) { return 'lỗi: '+String(err); }
      return s.useAppStore.getState().active ? 'ok' : 'không ra active';})()`);
    let r = await run();
    if (r !== "ok") { await sleep(1200); r = await run(); }
    return r;
  }

  /** Trạng thái tất định hiện tại — nguồn sự thật cho mọi khẳng định. */
  async snapshot() {
    const raw = await this.eval(`(async()=>{
      const s=await import(${JSON.stringify(this.mods.store)});
      const a=s.useAppStore.getState().active;
      return JSON.stringify({ moduleId: a && a.moduleId, config: a && a.config, state: a && a.state });})()`);
    return typeof raw === "string" && raw.startsWith("{") ? JSON.parse(raw) : null;
  }

  /** Phát một `SimAction` qua ĐÚNG đường học sinh đi (store.dispatch). */
  async dispatch(action) {
    return this.eval(`(async()=>{
      const s=await import(${JSON.stringify(this.mods.store)});
      s.useAppStore.getState().dispatch(${JSON.stringify(action)});
      return 'ok';})()`);
  }

  /** Bấm nút theo CHỮ hiện trên nó — đường chuột thật, không gọi hàm tắt. */
  async clickText(text) {
    return this.eval(`(()=>{
      const b=[...document.querySelectorAll('button,[role=button]')]
        .find(x=>(x.textContent||'').includes(${JSON.stringify(text)}));
      if(!b) return 'không thấy: ' + ${JSON.stringify(text)};
      b.click(); return 'ok';})()`);
  }

  /** Chạy một kịch bản và ghi thời gian. */
  async scenario(name, fn) {
    const t0 = Date.now();
    let result;
    try { result = await fn(this); }
    catch (err) { result = { pass: false, note: `ném lỗi: ${String(err)}` }; }
    const ms = Date.now() - t0;
    this.timings.scenarios.push({ name, ms });
    return { name, ms, ...result };
  }

  async close() {
    const t0 = Date.now();
    try { this.ws?.close(); } catch { /* đã đóng */ }
    try { this.chrome?.kill(); } catch { /* đã chết */ }
    this.timings.cleanup = Date.now() - t0;
  }
}

export { sleep };
