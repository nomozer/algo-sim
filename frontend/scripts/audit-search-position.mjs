/**
 * audit-search-position.mjs — W4B-2D §4/§9–§12: HỆ ĐẾM VỊ TRÍ CỦA HỌ TÌM KIẾM.
 *
 * Câu hỏi DUY NHẤT script này trả lời: ở MỘT bước có thể cam kết, học sinh có
 * nhìn thấy CÙNG một vị trí ngữ nghĩa được đánh số theo HAI hệ khác nhau trên
 * CÙNG một màn hình không?
 *
 * Vì sao phải đo trong trình duyệt chứ không đọc code: §12 của đề bài cấm quyết
 * từ tên biến. `vars.i = 2` và "Phần tử vị trí 3" chỉ là mâu thuẫn khi chúng
 * THẬT SỰ hiện cùng lúc — mà điều đó phụ thuộc panel Giải thích đang mở hay
 * đóng, tức phụ thuộc trạng thái trình bày mà SSR không đi qua
 * (`ARCHITECTURE_MAP §8` #13).
 *
 * Script này chỉ ĐỌC. Nó không bấm cam kết, không mở Thí nghiệm, không sửa gì.
 * Nó là ảnh chụp TRƯỚC khi di trú — baseline để so sau.
 *
 * DẤU VÂN TAY (bắt buộc, anti-pattern #14): mỗi lượt đo khẳng định
 * `active.moduleId` đúng target mong đợi và sân khấu đã dựng; sai thì thoát != 0
 * kèm chẩn đoán, không im lặng trả "SẠCH".
 *
 * Chạy:  npm run dev  (cửa sổ khác, cổng 3000 — vite.config.ts strictPort)
 *        node scripts/audit-search-position.mjs [--port 3000] [--out <dir>]
 */

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const PORT = argOf("--port", "3000");
const APP = `http://localhost:${PORT}`;
const OUT = resolve(argOf("--out", "../docs/evaluation/m17/w4b2d-search-family/position-numbering"));
const CDP_PORT = 9000 + Math.floor(Math.random() * 900);
mkdirSync(OUT, { recursive: true });

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const profile = mkdtempSync(join(tmpdir(), "algosim-w4b2d-"));
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", `--remote-debugging-port=${CDP_PORT}`,
  `--user-data-dir=${profile}`, "--window-size=1920,1080", "--hide-scrollbars", "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const shutdown = () => { try { chrome.kill(); } catch { /* đã chết */ } };
process.on("SIGINT", () => { shutdown(); process.exit(130); });

async function connect() {
  for (let i = 0; i < 40; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
      const page = list.find((t) => t.type === "page");
      if (page) return page.webSocketDebuggerUrl;
    } catch { /* chưa lên */ }
    await sleep(250);
  }
  throw new Error("Chrome không mở được cổng debug.");
}

const ws = new WebSocket(await connect());
await new Promise((r) => (ws.onopen = r));
let id = 0;
const pending = new Map();
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
};
const send = (method, params = {}) => new Promise((res) => {
  const i = ++id; pending.set(i, res);
  ws.send(JSON.stringify({ id: i, method, params }));
});
const evaluate = async (expr) => {
  const r = await send("Runtime.evaluate", {
    expression: expr, awaitPromise: true, returnByValue: true,
  });
  if (r.result?.exceptionDetails) {
    throw new Error(JSON.stringify(r.result.exceptionDetails.exception ?? r.result.exceptionDetails));
  }
  return r.result?.result?.value;
};
const shot = async (name) => {
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(OUT, `${name}.png`), Buffer.from(r.result.data, "base64"));
};

/* Loader dùng lại khuôn của `capture-w4b2b-experiment.mjs::loadTarget` — khuôn
   đó đã chứng minh chạy được trong Chrome thật (artifact browser-flow/). */
const loadTarget = (simId) => evaluate(`(async () => {
  const c = await import('/src/data/offline-catalog.ts');
  const s = await import('/src/state/store.ts');
  const r = await import('/src/simulations/index.ts');
  const reg = await import('/src/simulations/registry.ts');
  if (reg.listSimulations().length === 0) r.registerAllSimulations();
  const list = c.offlineCatalog();
  const i = list.findIndex((x) => x.simId === ${JSON.stringify(simId)});
  if (i < 0) return { ok: false, why: 'khong co mau offline', have: list.map((x) => x.simId) };
  s.useAppStore.getState().loadEnvelope(list[i].envelope);
  return { ok: true };
})()`);

/** DẤU VÂN TAY — đúng target, sân khấu đã dựng. Sai thì ném, không đo tiếp. */
const fingerprint = async (simId) => {
  for (let i = 0; i < 40; i += 1) {
    const st = await evaluate(`(async () => {
      const s = await import('/src/state/store.ts');
      const g = s.useAppStore.getState();
      return {
        moduleId: g.active ? g.active.moduleId : null,
        view: g.view,
        stage: !!document.querySelector('.sim-stage'),
      };
    })()`);
    if (st?.stage && st.moduleId === simId) return st;
    await sleep(250);
  }
  const diag = await evaluate(`(async () => {
    const s = await import('/src/state/store.ts');
    const g = s.useAppStore.getState();
    return { view: g.view, active: g.active ? g.active.moduleId : null,
             body: document.body.innerText.slice(0, 200) };
  })()`);
  throw new Error(`${simId}: DẤU VÂN TAY SAI — ${JSON.stringify(diag)}`);
};

const nextStepViaUi = () => evaluate(`(() => {
  const b = [...document.querySelectorAll('button')]
    .find((x) => (x.getAttribute('title') || '') === 'Tiến một bước' && !x.disabled);
  if (!b) return false;
  b.click();
  return true;
})()`);

/** Tiến tới bước ĐẦU TIÊN có vùng hành động tìm kiếm (điểm cam kết thật). */
const gotoActionable = async () => {
  for (let i = 0; i < 40; i += 1) {
    const ok = await evaluate(
      `!!document.querySelector('[aria-label="Thao tác với bước tìm kiếm"]')`,
    );
    if (ok) return i;
    if (!(await nextStepViaUi())) break;
    await sleep(260);
  }
  return -1;
};

/** Mở panel Giải thích (opt-in từ `39ad0df`) — VarsView sống trong đó. */
const openExplain = () => evaluate(`(() => {
  const b = [...document.querySelectorAll('button')]
    .find((x) => x.textContent.replace(/\\s+/g,' ').trim() === 'Giải thích');
  if (!b) return false;
  b.click();
  return true;
})()`);

/* ── THU HOẠCH: mọi tham chiếu vị trí học sinh NHÌN THẤY ────────────────────
 *
 * Đọc theo BỀ MẶT, không theo biến — vì câu hỏi là "cùng màn hình có hai hệ
 * đếm không", chứ không phải "biến nào 0-based". Mỗi bề mặt trả về text thô để
 * người đọc artifact tự kiểm lại được, cộng con số engine để đối chiếu. */
const harvest = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const g = s.useAppStore.getState();
  const st = g.active.state;
  const tr = st.branch ? st.branch.trace : st.trace;
  const step = tr.steps[st.cursor];
  const t = (el) => el ? el.textContent.replace(/\\s+/g, ' ').trim() : null;

  // Nhãn chỉ số dưới mỗi cột của ArrayView: các <text> cuối cùng trong mỗi <g>.
  const svg = document.querySelector('[aria-label="Mô phỏng dãy số"]');
  const columnIndexLabels = svg
    ? [...svg.querySelectorAll('g')].map((gr) => {
        const ts = [...gr.querySelectorAll('text')];
        return ts.length ? ts[ts.length - 1].textContent.trim() : null;
      }).filter((x) => x !== null)
    : [];

  /* Chip BIẾN đọc thành CẶP nhãn→giá trị. Bản đầu gom cả cụm thành một chuỗi
     ("cần tìm8,5trái0phải9giữa4"), không so được với vùng hành động — mà một
     phép đo không so được thì không kết luận được gì. */
  const varChips = {};
  for (const title of document.querySelectorAll('.pseudo-title')) {
    if (title.textContent.trim() !== 'BIẾN') continue;
    for (const chip of title.parentElement.querySelectorAll('div > div')) {
      const parts = [...chip.querySelectorAll('span')];
      if (parts.length === 2) varChips[parts[0].textContent.trim()] = parts[1].textContent.trim();
    }
  }

  return {
    engineVars: step.snapshot.vars,
    cursor: st.cursor,
    surfaces: {
      arrayColumnIndexes: columnIndexLabels,
      searchActionZone: t(document.querySelector('[aria-label="Thao tác với bước tìm kiếm"]')),
      /* Chip của vùng hành động đọc THEO CẤU TRÚC (nhãn tách khỏi <strong> giá
         trị). Cào cả cụm thành một chuỗi thì "Phần tử vị trí 1" + giá trị "105"
         dính thành "1105" và regex ăn nhầm — lượt đo đầu đã báo oan đúng kiểu
         đó. Bề mặt nào đo được có cấu trúc thì đừng đo bằng chuỗi. */
      searchChips: [...document.querySelectorAll('.search-state .scan-chip')].map((el) => {
        const strong = el.querySelector('strong');
        const value = strong ? strong.textContent.trim() : null;
        const label = el.textContent.replace(strong ? strong.textContent : '', '')
          .replace(/\\s+/g, ' ').trim();
        return { label, value };
      }),
      decisionStrip: t(document.querySelector('.decision-strip')),
      narration: t(document.querySelector('.narration-bar')),
      varChips,
      pseudocodeActive: t(document.querySelector('.pseudo-line.is-active')),
    },
  };
})()`);

const TARGETS = [
  { simId: "algorithm.linear_search", short: "linear_search" },
  { simId: "algorithm.binary_search", short: "binary_search" },
];

const report = { app: APP, capturedAt: null, targets: [] };

try {
  await send("Page.enable");
  await send("Runtime.enable");

  for (const tg of TARGETS) {
    console.log(`\n── ${tg.short} ─────────────────────────────`);
    await send("Page.navigate", { url: APP });
    await sleep(900);

    const loaded = await loadTarget(tg.simId);
    if (!loaded?.ok) throw new Error(`${tg.short}: không nạp được — ${JSON.stringify(loaded)}`);
    const fp = await fingerprint(tg.simId);
    console.log(`  dấu vân tay OK: ${fp.moduleId}`);

    const steps = await gotoActionable();
    if (steps < 0) throw new Error(`${tg.short}: không tới được bước có vùng hành động`);
    console.log(`  tới bước cam kết sau ${steps} lần Tiến`);

    await shot(`${tg.short}-1-observe-explain-closed`);
    const closed = await harvest();

    if (!(await openExplain())) throw new Error(`${tg.short}: không thấy nút Giải thích`);
    await sleep(500);
    await shot(`${tg.short}-2-observe-explain-open`);
    const open = await harvest();

    /* PHÉP KẾT LUẬN — cùng MỘT vị trí ngữ nghĩa, hai hệ đếm, cùng màn hình.
     *
     * So HAI BỀ MẶT ĐÃ ĐO với nhau, KHÔNG suy từ giả định. Bản đầu của script
     * này kết luận "VarsView 0-based" chỉ vì vùng hành động in `i+1` — tức nó
     * khẳng định về một bề mặt mà nó không hề đọc. Sau khi vá hệ đếm, phép đo
     * kiểu đó vẫn báo mâu thuẫn dù màn hình đã nhất quán: đúng loại guard nói
     * dối mà anti-pattern #14 cảnh báo. Nay mốc so là CHIP THẬT.
     */
    const v = open.engineVars;
    const chip = open.surfaces.varChips;
    const contradictions = [];
    const zone = open.surfaces.searchActionZone || "";
    const cols = open.surfaces.arrayColumnIndexes;
    const num = (s) => (s === undefined ? NaN : Number(String(s).replace(",", ".")));

    // Nhãn cột phải bắt đầu từ 1 — nó là vị trí nói với học sinh, không phải chỉ số mảng.
    if (cols.length > 0 && cols[0] !== "1") {
      contradictions.push({
        semanticLocation: "chỉ số cột trên sân khấu",
        detail: `nhãn cột bắt đầu từ "${cols[0]}" (${cols.join(",")}) trong khi vùng hành động đếm từ 1`,
      });
    }
    const zoneChip = (prefix) =>
      (open.surfaces.searchChips || []).find((c) => c.label.startsWith(prefix)) || null;

    // Phần tử đang xét: chip `i` và "Phần tử vị trí N" phải là CÙNG một số.
    if (typeof v.i === "number") {
      const c = zoneChip("Phần tử vị trí");
      const stated = c ? Number(c.label.replace(/\D+/g, "")) : NaN;
      if (!Number.isNaN(stated) && num(chip["i"]) !== stated) {
        contradictions.push({
          semanticLocation: "phần tử đang xét",
          detail: `chip i = ${chip["i"]} nhưng vùng hành động nói "vị trí ${stated}"`,
        });
      }
    }
    // Vùng xét nhị phân: chip trái/phải và "vùng xét L–R" phải khớp.
    if (typeof v.trai === "number" && typeof v.phai === "number") {
      const c = zoneChip("vùng xét");
      const m = c && c.value ? c.value.match(/(\d+)–(\d+)/) : null;
      if (m && (num(chip["trái"]) !== Number(m[1]) || num(chip["phải"]) !== Number(m[2]))) {
        contradictions.push({
          semanticLocation: "vùng xét của tìm kiếm nhị phân",
          detail: `chip trái=${chip["trái"]} phải=${chip["phải"]} nhưng vùng hành động nói "${m[1]}–${m[2]}"`,
        });
      }
    }

    console.log(`  mâu thuẫn cùng-màn-hình: ${contradictions.length}`);
    for (const c of contradictions) console.log(`    · ${c.semanticLocation}`);

    report.targets.push({
      target: tg.simId,
      stepsToActionable: steps,
      explainClosed: closed,
      explainOpen: open,
      contradictions,
    });
  }

  report.capturedAt = new Date().toISOString();
  report.verdict = report.targets.every((t) => t.contradictions.length === 0)
    ? "NO_CONTRADICTION"
    : "SAME_SCREEN_CONTRADICTION";
  writeFileSync(join(OUT, "position-numbering.json"), JSON.stringify(report, null, 2), "utf-8");
  console.log(`\nKẾT LUẬN: ${report.verdict}`);
  console.log(`Artifact: ${OUT}`);
  shutdown();
  process.exit(0);
} catch (err) {
  console.error(`\nTHẤT BẠI: ${err.message}`);
  shutdown();
  process.exit(2);
}
