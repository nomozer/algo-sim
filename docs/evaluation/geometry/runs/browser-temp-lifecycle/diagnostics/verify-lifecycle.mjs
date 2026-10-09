// browser-temp-lifecycle — real-Chrome verification of BrowserSession cleanup. 0 model calls.
// usage: node verify-lifecycle.mjs <repo> <dist> <out.json>     (child mode: node verify-lifecycle.mjs --child <repo> <url>)
import { createServer } from "node:http";
import { readdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { execFileSync, spawn } from "node:child_process";

const argv = process.argv.slice(2);
const CHILD = argv[0] === "--child";
const REPO = CHILD ? argv[1] : argv[0];
const imp = (p) => import(pathToFileURL(join(REPO, "frontend/scripts", p)).href);
const { BrowserSession, sleep } = await imp("browser-runner.mjs");

if (CHILD) {   // scenario G: open a session, report, then wait to be killed hard
  const s = new BrowserSession({ url: argv[2], napModuleDev: false, viewport: 640, height: 480 });
  await s.open();
  console.log(JSON.stringify({ dir: s.thuMuc, chrome_pid: s.chrome.pid }));
  await sleep(600_000);
  process.exit(0);
}

const [, DIST, OUT] = argv;
const { phucVu } = await imp("scene3d-orbit-gate.mjs");
const { openFixture } = await imp("compiler-scene-suite.mjs");
const ROOT = process.env.ALGOSIM_BROWSER_TMP ?? "D:/tmp/algosim-browser";
const norm = (p) => p.replaceAll("\\", "/").toLowerCase();

function procs() {
  const out = execFileSync("powershell", ["-NoProfile", "-Command",
    "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }"],
  { encoding: "utf8" });
  const rows = out.split(/\r?\n/).filter(Boolean).map((l) => { const [pid, ...c] = l.split("\t"); return { pid: Number(pid), cmd: c.join("\t") }; });
  const ours = rows.filter((r) => norm(r.cmd).includes(norm(ROOT)));
  return { ours: ours.length, others: rows.length - ours.length };
}
const listDir = (d, pre) => { try { return readdirSync(d).filter((n) => n.startsWith(pre)); } catch { return []; } };
const snap = () => ({ root_sessions: listDir(ROOT, "w12-").length, temp_w12: listDir(tmpdir(), "w12-").length,
  temp_scoped: listDir(tmpdir(), "scoped_dir").length, ...procs() });

const { sv, cong } = await phucVu(DIST);
const URL0 = `http://127.0.0.1:${cong}`;
const mk = () => new BrowserSession({ url: URL0, napModuleDev: false, viewport: 640, height: 480 });
const results = [];
async function scenario(name, fn) {
  const before = snap();
  let note = null, ok = true;
  try { note = await fn(); } catch (e) { ok = false; note = `SCENARIO_THREW: ${String(e?.message ?? e)}`; }
  await sleep(1500);
  const after = snap();
  const clean = after.root_sessions === before.root_sessions && after.ours === before.ours
    && after.temp_w12 === before.temp_w12 && after.others === before.others;
  const r = { name, pass: ok && clean && (note?.pass ?? true), before, after, note };
  results.push(r);
  console.log(`${r.pass ? "✓" : "✗"} ${name} ${JSON.stringify({ before, after })} ${JSON.stringify(note)}`);
}

const start = snap();
await scenario("A_sequential_5", async () => {
  for (let i = 0; i < 5; i++) { const s = mk(); await s.open(); await s.close(); }
  return { sessions: 5 };
});
await scenario("B_parallel_3_close_one_keeps_others", async () => {
  const ss = [mk(), mk(), mk()];
  await Promise.all(ss.map((s) => s.open()));
  const dirs = ss.map((s) => s.thuMuc);
  const peak = snap();
  await ss[0].close();
  const mid = { ...snap(), others_dirs_present: dirs.slice(1).every((d) => listDir(ROOT, "w12-").some((n) => norm(d).endsWith(n.toLowerCase()))) };
  const othersAlive = await Promise.all(ss.slice(1).map((s) => s.eval("1+1")));
  await Promise.all(ss.slice(1).map((s) => s.close()));
  return { peak, after_closing_one: mid, others_still_answer: othersAlive, pass: mid.others_dirs_present && othersAlive.every((x) => x === 2) && peak.ours > 0 };
});
await scenario("C_chrome_dies_during_startup", async () => {
  const s = mk();
  const p = s.open();
  for (let i = 0; i < 200 && !s.chrome?.pid; i++) await sleep(10);
  process.kill(s.chrome.pid);            // only this session's browser process
  let threw = null;
  try { await p; } catch (e) { threw = String(e.message).slice(0, 80); }
  return { threw, dir_left: s.thuMuc, pass: !!threw && !s.thuMuc };
});
await scenario("D_error_inside_session_closed_in_finally", async () => {
  const s = mk();
  let threw = null;
  try { await s.open(); throw new Error("SIMULATED_TEST_FAILURE"); } catch (e) { threw = e.message; } finally { await s.close(); }
  return { threw, pass: threw === "SIMULATED_TEST_FAILURE" && !s.thuMuc };
});
await scenario("E_chrome_crashes_mid_session_then_close", async () => {
  const s = mk();
  await s.open();
  process.kill(s.chrome.pid);
  await sleep(1000);
  await s.close();
  return { pass: !s.thuMuc && !s.donLoi };
});
await scenario("F_openFixture_fails_after_open", async () => {
  // A page that passes the runner's fingerprint (.app-main) but never shows the problem textarea ⇒ POLL_TIMEOUT.
  const srv = createServer((q, r) => { r.writeHead(200, { "Content-Type": "text/html" }); r.end("<div class='app-main'></div>"); });
  await new Promise((r) => srv.listen(0, "127.0.0.1", r));
  let threw = null;
  try { await openFixture({ port: srv.address().port, viewport: { width: 800, height: 600 }, fixture: { envelope: {}, problem_text: "x" } }); }
  catch (e) { threw = String(e.message).slice(0, 60); }
  srv.close();
  return { threw, pass: !!threw };
});
await scenario("G_runner_hard_killed_next_run_sweeps", async () => {
  const child = spawn(process.execPath, [process.argv[1], "--child", REPO, URL0], { stdio: ["ignore", "pipe", "inherit"] });
  const info = await new Promise((res) => child.stdout.once("data", (b) => res(JSON.parse(String(b)))));
  child.kill("SIGKILL");                  // no finally, no exit handler: the orphan case
  await sleep(1500);
  const leftover = snap();
  const orphanPresent = listDir(ROOT, "w12-").some((n) => norm(info.dir).endsWith(n.toLowerCase()));
  // A NEW process's first open() sweeps the root.
  const sweep = spawn(process.execPath, ["-e", `import(${JSON.stringify(pathToFileURL(join(REPO, "frontend/scripts/browser-runner.mjs")).href)})`
    + `.then(async (m) => { const s = new m.BrowserSession({ url: ${JSON.stringify(URL0)}, napModuleDev: false, viewport: 640, height: 480 }); await s.open(); await s.close(); })`],
  { stdio: ["ignore", "inherit", "inherit"] });
  await new Promise((r) => sweep.once("exit", r));
  const gone = !listDir(ROOT, "w12-").some((n) => norm(info.dir).endsWith(n.toLowerCase()));
  return { leftover_after_kill: leftover, orphan_dir_present_after_kill: orphanPresent, removed_by_next_run_sweep: gone, pass: orphanPresent && gone };
});
sv.close();
const end = snap();
writeFileSync(OUT, JSON.stringify({ schema: "browser-lifecycle-verification/1", root: ROOT, application_llm_calls: 0,
  start, end, pass: results.every((r) => r.pass), scenarios: results }, null, 2));
console.log(`${results.filter((r) => r.pass).length}/${results.length} scenarios pass · start ${JSON.stringify(start)} · end ${JSON.stringify(end)}`);
