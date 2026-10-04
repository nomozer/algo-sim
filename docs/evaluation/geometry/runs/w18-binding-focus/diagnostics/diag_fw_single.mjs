// Chẩn đoán MỘT phép tiêm trình duyệt W18 (FW2 mặc định) trên worktree nháp, GIỮ toàn bộ stdout/stderr.
// Cùng phép thay của run_fault_injections_w18_frontend.mjs; khôi phục byte-identical ở finally.
import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const FE = "D:/tmp/w18-fe/frontend";
const [, , id = "FW2", ra = "D:/tmp/w18-diag-fw2"] = process.argv;
const EXP = "src/simulations/domains/geometry/Scene3DExplorer.tsx";
const SUITE = "scripts/compiler-scene-suite.mjs";
const PHEP = {
  FW2: [[EXP, "              onClick={() => setXem((s) => ({ showAll: !s.showAll }))}",
    "              onClick={() => { setXem((s) => ({ showAll: !s.showAll })); setTt((s) => ({ ...s, current_step: 0 })); }}"]],
  NONE: [],
};
const LOC = [
  [SUITE, "    for (const scenario of suite.scenarios) {",
    "    for (const scenario of suite.scenarios.filter((x) => x.id === process.env.W18_FI_HO)) {"],
  [SUITE, "        record.positive[viewport.id] = await runPositive({",
    "        if (viewport.id !== process.env.W18_FI_KHUNG) continue; record.positive[viewport.id] = await runPositive({"],
];
const goc = new Map();
try {
  for (const [tep, cu, moi] of [...PHEP[id], ...LOC]) {
    const d = join(FE, tep);
    if (!goc.has(d)) goc.set(d, readFileSync(d));
    const s = readFileSync(d, "utf-8");
    if (s.split(cu).length !== 2) throw new Error(`STALE ${tep}`);
    writeFileSync(d, s.replace(cu, moi), "utf-8");
  }
  const r = spawnSync("node", ["scripts/compiler-scene-replay.mjs", "--suite", "scripts/generic-tier-a-scenarios.json",
    "--fixture-root", "D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/w18-binding-focus/inputs", "--ra", ra],
  { cwd: FE, encoding: "utf-8", shell: true, timeout: 1_800_000,
    env: { ...process.env, W18_FI_HO: "triangular_pyramid", W18_FI_KHUNG: "desktop" } });
  writeFileSync(`${ra}.log`, `${r.stdout}\n--- stderr ---\n${r.stderr}\nexit=${r.status}\n`, "utf-8");
  console.log(`exit=${r.status}; log ${ra}.log`);
} finally {
  for (const [d, b] of goc) writeFileSync(d, b);
  console.log("restored", [...goc].every(([d, b]) => readFileSync(d).equals(b)));
}
