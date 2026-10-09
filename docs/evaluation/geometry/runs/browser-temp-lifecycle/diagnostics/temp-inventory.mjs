// browser-temp-lifecycle — DRY-RUN inventory of %TEMP%\w12-* and %TEMP%\scoped_dir*. Deletes nothing.
// Names only (relative to %TEMP%), no user path in the output.
// usage: node temp-inventory.mjs <out.json>
import { existsSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";

const [OUT] = process.argv.slice(2);
const T = tmpdir();
const norm = (p) => p.replaceAll("\\", "/").toLowerCase();
const cmdlines = execFileSync("powershell", ["-NoProfile", "-Command",
  "Get-CimInstance Win32_Process | ForEach-Object { \"$($_.ProcessId)`t$($_.Name)`t$($_.CommandLine)\" }"],
{ encoding: "utf8", maxBuffer: 64 * 1024 * 1024 }).split(/\r?\n/).filter(Boolean)
  .map((l) => { const [pid, name, ...c] = l.split("\t"); return { pid: Number(pid), name, cmd: norm(c.join("\t")) }; });
const alive = new Map(cmdlines.map((p) => [p.pid, p.name]));

function size(d) {
  let s = 0, files = 0;
  const walk = (p) => { let es = []; try { es = readdirSync(p, { withFileTypes: true }); } catch { return; }
    for (const e of es) { const q = join(p, e.name); if (e.isDirectory()) walk(q); else { try { s += statSync(q).size; files += 1; } catch { /* gone */ } } } };
  walk(d);
  return { bytes: s, files };
}

const rows = [];
for (const name of readdirSync(T)) {
  const full = join(T, name);
  let st; try { st = statSync(full); } catch { continue; }
  if (!st.isDirectory()) continue;
  if (name.startsWith("w12-")) {
    const referencedBy = cmdlines.filter((p) => p.cmd.includes(norm(full))).map((p) => p.pid);
    const profile = existsSync(join(full, "Local State")) || existsSync(join(full, "Default"));
    const cls = referencedBy.length ? "ACTIVE" : profile ? "VERIFIED_ORPHAN" : "UNKNOWN";
    rows.push({ kind: "w12", name, created: st.birthtime.toISOString(), class: cls, chrome_profile_layout: profile,
      referenced_by_pids: referencedBy, ...size(full) });
  } else if (name.startsWith("scoped_dir")) {
    const pid = Number((/^scoped_dir(\d+)_/.exec(name) ?? [])[1]);
    const owner = alive.get(pid) ?? null;
    let entries = []; try { entries = readdirSync(full); } catch { /* */ }
    rows.push({ kind: "scoped_dir", name, created: st.birthtime.toISOString(), creator_pid: pid || null,
      creator_alive_as: owner, class: owner ? "ACTIVE" : "UNKNOWN",
      content_signature: entries.some((e) => e === "CRX_INSTALL") ? "CRX_INSTALL" : entries.every((e) => e.endsWith(".tmp")) ? "UUID_TMP" : "OTHER",
      ...size(full) });
  }
}
const sum = (f) => rows.filter(f).reduce((a, r) => ({ count: a.count + 1, mb: a.mb + r.bytes / 1048576 }), { count: 0, mb: 0 });
const summary = {};
for (const k of ["w12", "scoped_dir"]) for (const c of ["ACTIVE", "VERIFIED_ORPHAN", "UNKNOWN"]) {
  const s = sum((r) => r.kind === k && r.class === c);
  if (s.count) summary[`${k}:${c}`] = { count: s.count, mb: Math.round(s.mb) };
}
const created = rows.map((r) => r.created).sort();
writeFileSync(OUT, JSON.stringify({
  schema: "temp-inventory/1", mode: "DRY_RUN — nothing deleted", taken_at: new Date().toISOString(),
  location: "%TEMP% (names only)",
  rules: {
    "w12:VERIFIED_ORPHAN": "prefix w12- is created only by frontend/scripts/browser-runner.mjs in this repo (code search: the other Chrome scripts use offl-, curved-, integ-, live-, scope-, algosim-audit-) AND the directory has a Chrome profile layout (Local State or Default) AND no running process command line references it",
    "w12:UNKNOWN": "w12- without a Chrome profile layout",
    "scoped_dir:UNKNOWN": "Chrome/Chromium writes scoped_dir<pid>_* for its own temporary files (component install CRX_INSTALL, uuid .tmp); any Chromium on the machine (incl. personal browsers) does this and the creating process has exited — owner not provable",
    "ACTIVE": "referenced by a running process (w12) or creating pid alive (scoped_dir)",
  },
  created_range: [created[0] ?? null, created.at(-1) ?? null], summary, entries: rows,
}, null, 2));
console.log(JSON.stringify(summary));
