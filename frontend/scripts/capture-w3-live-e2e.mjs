/**
 * capture-w3-live-e2e.mjs — M17 W3-LIVE-C1 §12/§13: HANDOFF ĐẠI DIỆN
 * live prompt → validated candidate → engine tất định FE → Chrome.
 *
 * Điểm khác `capture-w3-encoding.mjs`: fixture KHÔNG viết tay. Candidate được
 * ĐỌC THẲNG từ artifact live (`character_encoding_live_rerun.json`) và nạp qua
 * CHÍNH `store.loadEnvelope` — đúng đường production. Hai hash phải khớp:
 *   hash(validated candidate trong artifact) == hash(spec engine đang chạy)
 * Lệch một bit là hỏng bằng chứng ⇒ thoát mã 3.
 *
 * KHÔNG gọi LLM. KHÔNG gõ lại config. KHÔNG sinh ảnh. KHÔNG sửa production.
 *
 * Chạy:  npm run dev  (cửa sổ khác)
 *        node scripts/capture-w3-live-e2e.mjs [--port 3000]
 */

import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const APP = `http://localhost:${argOf("--port", "3000")}`;
const CDP_PORT = 9347;
const C1_DIR = resolve(argOf("--c1", "../docs/evaluation/m17/w3-live-c1"));
const OUT_DIR = join(C1_DIR, "visual");
const TARGET = "binary.character_encoding";
const VIEWPORT = { width: 1440, height: 1000 };

/* Hash CHUẨN HOÁ: khoá sắp xếp để thứ tự field không làm lệch bằng chứng. */
const canon = (o) => JSON.stringify(o, Object.keys(o).sort());
const sha256 = (s) => createHash("sha256").update(s, "utf8").digest("hex");

/* ── Nguồn candidate: ARTIFACT LIVE, không phải fixture ── */
const artifact = JSON.parse(
  readFileSync(join(C1_DIR, "character_encoding_live_rerun.json"), "utf8"));

const accepted = artifact.records.filter(
  (r) => r.final_status === "ok" && r.final_route === TARGET && r.validated_candidate);

const CASES = [
  { e2e_id: "E2E-ENC-1", from_case: "LIVE-ENC-1", expect_text: "A" },
  { e2e_id: "E2E-ENC-2", from_case: "LIVE-ENC-3", expect_text: "\u1EBF" },
].map((c) => {
  const rec = accepted.find((r) => r.case_id === c.from_case);
  return { ...c, rec };
});

const runnable = CASES.filter((c) => c.rec);
const skipped = CASES.filter((c) => !c.rec);
for (const s of skipped) {
  console.log(`${s.e2e_id}: NOT_MEASURED — live KHÔNG có candidate được chấp nhận `
            + `cho ${s.from_case} (KHÔNG dựng config bằng tay).`);
}
if (runnable.length === 0) { console.error("Không có case nào chạy được."); process.exit(2); }

/* ══════════════ CDP (tái dùng khuôn capture-w3-encoding.mjs) ══════════════ */
const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const profile = mkdtempSync(join(tmpdir(), "algosim-w3e2e-"));
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", `--remote-debugging-port=${CDP_PORT}`,
  `--user-data-dir=${profile}`, "--window-size=1440,1000", "--hide-scrollbars", "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

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
    expression: expr, returnByValue: true, awaitPromise: true,
  });
  if (r.result?.exceptionDetails) {
    throw new Error(JSON.stringify(r.result.exceptionDetails).slice(0, 600));
  }
  return r.result?.result?.value;
};

await send("Page.enable");
await send("Runtime.enable");
mkdirSync(OUT_DIR, { recursive: true });

async function freshPage() {
  await send("Emulation.setDeviceMetricsOverride", {
    width: VIEWPORT.width, height: VIEWPORT.height, deviceScaleFactor: 1, mobile: false,
  });
  await send("Page.navigate", { url: APP });
  await sleep(1200);
}

async function shot(name) {
  const { data } = (await send("Page.captureScreenshot", { format: "png" })).result || {};
  if (!data) throw new Error(`captureScreenshot thất bại: ${name}`);
  const p = join(OUT_DIR, `${name}.png`);
  writeFileSync(p, Buffer.from(data, "base64"));
  return p.replace(/\\/g, "/");
}

const loadEnvelope = (envelope) => evaluate(`(async () => {
  const m = await import('/src/state/store.ts');
  m.useAppStore.getState().loadEnvelope(${JSON.stringify(envelope)});
  return true;
})()`);

const goToStep = (n) => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  s.useAppStore.getState().goToStep(${n});
  return s.useAppStore.getState().active.state.cursor ?? null;
})()`);

/* Sự thật NGỮ NGHĨA đọc từ engine state (ảnh chỉ là bằng chứng trình bày). */
const engineFacts = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const st = s.useAppStore.getState().active;
  const t = st.state;
  const m = t.meta[Math.max(0, Math.min(t.cursor, t.meta.length - 1))];
  return JSON.stringify({
    target_id: st.moduleId,
    loaded_spec: t.spec,
    cursor: t.cursor,
    step_total: t.trace.steps.length,
    phase: m.phase,
    division: m.division ?? null,
    committed_rows: m.committed,
    rows: t.rows.map((r) => ({ char: r.char, cp: r.codePoint, dec: r.decimal, bin: r.binary })),
    narration: t.trace.steps[t.cursor].narration,
  });
})()`);

/* DOM thật — chứng minh cái người học NHÌN THẤY, không chỉ state. */
const domText = () => evaluate(
  `document.querySelector('.app-single, #root')?.innerText ?? document.body.innerText`);

/* Mốc: hỏi chính engine phase nào ở bước nào — không số học trên cursor. */
const resolveMark = (mark) => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const t = s.useAppStore.getState().active.state;
  const spec = ${JSON.stringify(mark)};
  if (spec.last) return t.trace.steps.length - 1;
  let n = 0;
  for (let i = 0; i < t.meta.length; i++) {
    if (t.meta[i].phase === spec.phase) {
      if (n === (spec.nth ?? 0)) return i;
      n++;
    }
  }
  return -1;
})()`);

const results = [];
let shots = 0;

for (const c of runnable) {
  const candidate = c.rec.validated_candidate;
  const artifactHash = sha256(canon(candidate));
  const envelope = {
    status: "ok", simulation_id: TARGET, domain: "binary", visual_mode: "2d",
    title: "Mã hoá ký tự", description: null, notes: null, config: candidate,
  };

  await freshPage();
  await loadEnvelope(envelope);

  const phases = [];
  const marks = [
    ["initial", { phase: "select_character" }],
    ["mechanism_mid", { phase: "divide_step", nth: 0 }],
    ["final", { last: true }],
  ];
  for (const [label, mark] of marks) {
    const step = await resolveMark(mark);
    if (step < 0) { phases.push({ label, error: "phase không tồn tại" }); continue; }
    await goToStep(step);
    await sleep(350);
    const facts = JSON.parse(await engineFacts());
    const dom = await domText();
    const png = await shot(`${c.e2e_id}-${label}`);
    shots++;
    phases.push({
      label, step, png: png.split("/").slice(-1)[0],
      engine: facts,
      dom_has_final_binary: facts.rows.some((r) => r.bin && dom.includes(r.bin)),
      dom_excerpt: dom.replace(/\s+/g, " ").slice(0, 400),
    });
  }

  const loadedSpec = phases.find((p) => p.engine)?.engine.loaded_spec;
  const loadedHash = loadedSpec ? sha256(canon(loadedSpec)) : null;
  const mid = phases.find((p) => p.label === "mechanism_mid");
  const fin = phases.find((p) => p.label === "final");
  const init = phases.find((p) => p.label === "initial");

  const checks = {
    hash_match: loadedHash === artifactHash,
    target_runtime_dung: phases.every((p) => !p.engine || p.engine.target_id === TARGET),
    khong_phai_generic: phases.every((p) => !p.engine || p.engine.target_id !== "generic.rule_scene"),
    initial_chua_co_binary: init ? init.dom_has_final_binary === false : false,
    mid_co_phep_chia_that: !!(mid?.engine.division
      && Number.isFinite(mid.engine.division.value)
      && Number.isFinite(mid.engine.division.quotient)
      && Number.isFinite(mid.engine.division.remainder)),
    final_binary_do_engine_sinh: !!fin?.engine.rows.every((r) => typeof r.bin === "string" && r.bin.length),
    text_giu_nguyen: loadedSpec?.text === c.expect_text,
  };
  const verdict = Object.values(checks).every(Boolean) ? "PASS" : "FAIL";
  console.log(`${c.e2e_id} (${c.from_case} run${c.rec.run_id}): ${verdict} · `
            + `hash ${artifactHash.slice(0, 12)}… · ${JSON.stringify(checks)}`);

  results.push({
    e2e_id: c.e2e_id, from_case: c.from_case, from_run: c.rec.run_id,
    prompt: c.rec.prompt,
    live_validated_candidate: candidate,
    live_candidate_sha256: artifactHash,
    browser_loaded_spec: loadedSpec,
    browser_loaded_sha256: loadedHash,
    checks, verdict, phases,
  });
}

const payload = {
  wave: "M17 W3-LIVE-C1 §12/§13",
  target: TARGET,
  generated_at: new Date().toISOString(),
  source_artifact: "docs/evaluation/m17/w3-live-c1/character_encoding_live_rerun.json",
  live_git_sha: artifact.git_sha,
  model: artifact.model,
  llm_calls_in_this_step: 0,
  viewport: VIEWPORT,
  screenshots: shots,
  cases_run: results.map((r) => r.e2e_id),
  cases_not_measured: skipped.map((s) => ({
    e2e_id: s.e2e_id, from_case: s.from_case,
    reason: "live không có candidate được chấp nhận; CẤM dựng config bằng tay",
  })),
  classification: results.length && results.every((r) => r.verdict === "PASS")
    ? "REPRESENTATIVE_E2E_VERIFIED" : "REPRESENTATIVE_E2E_FAILED",
  results,
};
writeFileSync(join(C1_DIR, "representative_e2e_handoff.json"),
              JSON.stringify(payload, null, 2) + "\n", "utf8");
writeFileSync(join(OUT_DIR, "captures.json"),
              JSON.stringify({ generated_at: payload.generated_at, screenshots: shots,
                               cases: results.map((r) => ({ e2e_id: r.e2e_id,
                                 phases: r.phases.map((p) => p.png).filter(Boolean) })) },
                            null, 2) + "\n", "utf8");

console.log(`\n${payload.classification} · ${shots} ảnh · 0 LLM call`);
ws.close();
chrome.kill();
process.exit(payload.classification === "REPRESENTATIVE_E2E_VERIFIED" ? 0 : 3);
