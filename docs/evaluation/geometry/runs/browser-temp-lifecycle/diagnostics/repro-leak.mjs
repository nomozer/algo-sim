// Reproduce the profile leak with the CURRENT browser-runner: N sequential open/close against a static build.
// usage: node repro-leak.mjs <repo> <dist> [n]
import { readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { execFileSync } from "node:child_process";

const [REPO, DIST, N = "3"] = process.argv.slice(2);
const imp = (p) => import(pathToFileURL(join(REPO, "frontend/scripts", p)).href);
const { BrowserSession, sleep } = await imp("browser-runner.mjs");
const { phucVu } = await imp("scene3d-orbit-gate.mjs");

const w12 = () => new Set(readdirSync(tmpdir()).filter((n) => n.startsWith("w12-")));
// Chrome processes whose command line names one of the given profile dirs (never touches other Chrome).
const chromeUsing = (dirs) => {
  if (!dirs.length) return [];
  const out = execFileSync("powershell", ["-NoProfile", "-Command",
    "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }"],
  { encoding: "utf8" });
  return out.split(/\r?\n/).filter((l) => dirs.some((d) => l.includes(d))).map((l) => l.split("\t")[0]);
};

const before = w12();
const { sv, cong } = await phucVu(DIST);
for (let i = 0; i < Number(N); i += 1) {
  const s = new BrowserSession({ url: `http://127.0.0.1:${cong}`, napModuleDev: false, viewport: 800, height: 600 });
  await s.open();
  await s.close();
}
sv.close();
await sleep(3000);
const created = [...w12()].filter((n) => !before.has(n));
const alive = chromeUsing(created);
console.log(JSON.stringify({ sessions: Number(N), new_w12_dirs: created.length, chrome_processes_still_using_them: alive.length, dirs: created }));
