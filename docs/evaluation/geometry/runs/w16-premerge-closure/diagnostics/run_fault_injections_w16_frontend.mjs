// W16 — frontend fault injections (renderer layering + harness assessor), 0 model calls.
//
// Runs ONLY on a detached scratch worktree given as the first argument (refuses the main
// repository): one exact source substitution per run (must match exactly once, else the run
// aborts as STALE), the predicted test command, then the original bytes are written back and
// verified. Writes `logs/FAULT_INJECTION_W16_FRONTEND.log` next to this script; refuses to
// overwrite. Usage (from the repository root):
//   node docs/evaluation/geometry/runs/w16-premerge-closure/diagnostics/run_fault_injections_w16_frontend.mjs D:/tmp/w16-fe
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const HERE = import.meta.dirname;
const OUT = join(HERE, "logs", "FAULT_INJECTION_W16_FRONTEND.log");
const WT = resolve(process.argv[2] ?? "");
if (!process.argv[2] || resolve(HERE, "..", "..", "..", "..", "..", "..") === WT) {
  throw new Error("pass a detached scratch worktree, never the main repository");
}
if (existsSync(OUT)) throw new Error(`refusing to overwrite ${OUT}`);
const FE = join(WT, "frontend");
const VIEW = "src/simulations/domains/geometry/scene3d-view.tsx";
const LIB = "scripts/compiler-scene-replay-lib.mjs";
const VITEST = ["npx", "vitest", "run", "src/simulations/domains/geometry/scene3d-section.test.ts"];
const NODE = ["node", "--test", "scripts/compiler-scene-replay-lib.node-test.mjs"];

const INJECTIONS = [
  ["FL1", VIEW, "if (thietDien) mesh.renderOrder = THU_TU_TO_THIET_DIEN;",
    "if (thietDien) mesh.renderOrder = THU_TU_VE_THIET_DIEN;",
    "section fill back to renderOrder 10 (drawn over the edges, the W15 state)", VITEST,
    "W16 scene-wide ordering test + the W15 fill test"],
  // Một dòng, không `\n`: worktree checkout ra CRLF (lượt 1 báo STALE vì `\n`).
  ["FH1", LIB, "    && doanKhoi.every((e) => _cachDoan(x, y, e.d[0], e.d[1]) >= margin)", "",
    "W15 sampler again: samples may sit on solid edges", NODE, "W16 section fill sampler test"],
  ["FH2", LIB, "pass: rho < 1 && tuongPhan >= T.T_ON_MIN };", "pass: tuongPhan >= T.T_ON_MIN };",
    "under-edges check ignores rho (fill over the edge passes)", NODE,
    "W16 SECTION_FILL_UNDER_EDGES: the fill drawn over the edge fails"],
  ["FH3", LIB, 'if (!(canh ?? []).length) return { pass: false, reason: "NOT_APPLICABLE_NO_CROSSING_EDGE", edges: [] };',
    'if (!(canh ?? []).length) return { pass: true, reason: "NOT_APPLICABLE_NO_CROSSING_EDGE", edges: [] };',
    "no crossing edge counted as a pass", NODE, "W16 … no crossing edge is not a pass"],
];

const chay = ([cmd, ...args]) => {
  const r = spawnSync(cmd, args, { cwd: FE, encoding: "utf-8", shell: process.platform === "win32" });
  const out = `${r.stdout}\n${r.stderr}`;
  const tom = out.split("\n").filter((x) => /Tests +\d|ℹ (pass|fail) /.test(x)).map((x) => x.trim()).join(" · ");
  const hong = out.split("\n").filter((x) => /^\s*(×|✖|FAIL)\s/.test(x)).map((x) => x.trim()).slice(0, 8);
  return { code: r.status, tom, hong };
};

const head = execFileSync("git", ["-C", WT, "rev-parse", "--short=8", "HEAD"], { encoding: "utf-8" }).trim();
const ra = [`W16 — frontend fault injections on the detached worktree at ${head} (0 model calls)`,
  "method: one exact source substitution per run in the scratch worktree, test, then the original bytes restored and verified", ""];
for (const [cmd] of [[VITEST], [NODE]]) {
  const b = chay(cmd);
  ra.push(`baseline ${cmd.slice(-1)[0]}: exit ${b.code} · ${b.tom}`);
}
ra.push("");
for (const [id, tep, cu, moi, moTa, lenh, duDoan] of INJECTIONS) {
  const duong = join(FE, tep);
  const goc = readFileSync(duong);
  const src = goc.toString("utf-8");
  if (src.split(cu).length - 1 !== 1) {
    ra.push(`${id} STALE: substitution found ${src.split(cu).length - 1}x in ${tep}`, "");
    continue;
  }
  writeFileSync(duong, src.replace(cu, moi), "utf-8");
  let kq;
  try {
    kq = chay(lenh);
  } finally {
    writeFileSync(duong, goc);
  }
  const lai = readFileSync(duong).equals(goc);
  ra.push(`${id} [${tep}] ${moTa}`, `  predicted: ${duDoan}`,
    `  observed : exit ${kq.code} · ${kq.tom} -> ${kq.code !== 0 ? "CAUGHT" : "NOT CAUGHT"}`,
    ...kq.hong.map((h) => `    ${h}`), `  restored byte-identical: ${lai}`, "");
}
for (const [cmd] of [[VITEST], [NODE]]) {
  const b = chay(cmd);
  ra.push(`after all injections ${cmd.slice(-1)[0]}: exit ${b.code} · ${b.tom}`);
}
writeFileSync(OUT, ra.join("\n") + "\n", "utf-8");
console.log(ra.join("\n"));
