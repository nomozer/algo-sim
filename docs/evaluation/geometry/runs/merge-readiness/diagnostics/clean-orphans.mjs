// Remove ONLY the manifest's VERIFIED_ORPHAN %TEMP%\w12-* entries that still pass every check at this moment.
// usage: node clean-orphans.mjs <TEMP_INVENTORY.json> <out.json> [--apply]     (default: dry run, deletes nothing)
import { existsSync, lstatSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { execFileSync } from "node:child_process";

const [MANIFEST, OUT] = process.argv.slice(2);
const APPLY = process.argv.includes("--apply");
const T = resolve(tmpdir());
const man = JSON.parse(readFileSync(MANIFEST, "utf8"));
const norm = (p) => p.replaceAll("\\", "/").toLowerCase();
const procs = execFileSync("powershell", ["-NoProfile", "-Command",
  "Get-CimInstance Win32_Process | ForEach-Object { $_.CommandLine }"], { encoding: "utf8", maxBuffer: 64 << 20 })
  .split(/\r?\n/).filter(Boolean).map(norm);
const chromeRunning = execFileSync("powershell", ["-NoProfile", "-Command",
  "@(Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\").Count"], { encoding: "utf8" }).trim();

function size(d) {
  let s = 0;
  const walk = (p) => { let es = []; try { es = readdirSync(p, { withFileTypes: true }); } catch { return; }
    for (const e of es) { const q = join(p, e.name); if (e.isDirectory() && !e.isSymbolicLink()) walk(q); else { try { s += statSync(q).size; } catch { /* */ } } } };
  walk(d);
  return s;
}

const rows = [];
for (const e of man.entries.filter((x) => x.kind === "w12" && x.class === "VERIFIED_ORPHAN")) {
  const r = { name: e.name, action: "SKIP", reason: null, bytes: 0 };
  const p = join(T, e.name);
  if (!/^w12-[A-Za-z0-9]{6}$/.test(e.name) || basename(p) !== e.name || resolve(dirname(p)) !== T) r.reason = "NOT_DIRECT_CHILD_OF_TEMP";
  else if (!existsSync(p)) r.reason = "ALREADY_GONE";
  else {
    const l = lstatSync(p);
    if (l.isSymbolicLink() || !l.isDirectory()) r.reason = "LINK_OR_NOT_DIRECTORY";
    else if (l.birthtime.toISOString() !== e.created) r.reason = "CREATION_TIME_DIFFERS_FROM_MANIFEST";
    else if (new Date(e.created) > new Date(man.taken_at)) r.reason = "CREATED_AFTER_INVENTORY";
    else if (!existsSync(join(p, "Local State")) && !existsSync(join(p, "Default"))) r.reason = "NO_CHROME_PROFILE_LAYOUT";
    else if (procs.some((c) => c.includes(norm(p)) || c.includes(e.name.toLowerCase()))) r.reason = "REFERENCED_BY_A_PROCESS";
    else {
      r.bytes = size(p);
      r.action = APPLY ? "DELETE" : "WOULD_DELETE";
      if (APPLY) {
        try { rmSync(p, { recursive: true, force: false, maxRetries: 5, retryDelay: 200 }); r.result = existsSync(p) ? "FAILED" : "DELETED"; }
        catch (err) { r.result = "FAILED"; r.error = String(err.code ?? err.message); }
      }
    }
  }
  rows.push(r);
}
const by = (f) => rows.filter(f);
const gb = (xs) => Math.round(xs.reduce((a, r) => a + r.bytes, 0) / 1e7) / 100;
const summary = {
  mode: APPLY ? "APPLY" : "DRY_RUN", at: new Date().toISOString(), manifest_taken_at: man.taken_at,
  chrome_processes_running: Number(chromeRunning), manifest_entries: rows.length,
  eligible: by((r) => r.action !== "SKIP").length, eligible_gb: gb(by((r) => r.action !== "SKIP")),
  deleted: by((r) => r.result === "DELETED").length, failed: by((r) => r.result === "FAILED").length,
  skipped: by((r) => r.action === "SKIP").length,
  skip_reasons: Object.fromEntries([...new Set(by((r) => r.action === "SKIP").map((r) => r.reason))].map((k) => [k, by((r) => r.reason === k).length])),
};
writeFileSync(OUT, JSON.stringify({ schema: "temp-orphan-cleanup/1", summary, entries: rows }, null, 2));
console.log(JSON.stringify(summary));
