// W17 — frontend fault injections (label presentation, refusal card, browser harness), 0 model calls.
//
// Runs ONLY on a detached scratch worktree given as the first argument (refuses the main
// repository). Unit injections: one exact one-line substitution (must match exactly once, else the
// run records STALE), the predicted test command, then the original bytes are written back and
// verified. Browser injections: the fault plus a run filter (one family, one viewport — applied to
// the scratch copy only, never part of the committed suite), the suite on that worktree, then the
// predicted reason code is read from its evidence; a filtered baseline runs first. Writes
// `logs/FAULT_INJECTION_W17_FRONTEND<suffix>.log` next to this script; refuses to overwrite. Usage (from
// the repository root):
//   node docs/evaluation/geometry/runs/w17-operation-annotations/diagnostics/run_fault_injections_w17_frontend.mjs D:/tmp/w17-fe D:/tmp/w17-fixtures [suffix]
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const HERE = import.meta.dirname;
const OUT = join(HERE, "logs", `FAULT_INJECTION_W17_FRONTEND${process.argv[4] ?? ""}.log`);
const WT = resolve(process.argv[2] ?? "");
const FIXTURES = process.argv[3] ? resolve(process.argv[3]) : null;
if (!process.argv[2] || resolve(HERE, "..", "..", "..", "..", "..", "..") === WT) {
  throw new Error("pass a detached scratch worktree, never the main repository");
}
if (existsSync(OUT)) throw new Error(`refusing to overwrite ${OUT}`);
const FE = join(WT, "frontend");
const ANN = "src/simulations/domains/geometry/scene3d-annotations.ts";
const EXP = "src/simulations/domains/geometry/Scene3DExplorer.tsx";
const SW = "src/components/SimulationWorkspace.tsx";
const LIB = "scripts/compiler-scene-replay-lib.mjs";
const SUITE = "scripts/compiler-scene-suite.mjs";
const V_ANN = ["npx", "vitest", "run", "src/simulations/domains/geometry/scene3d-annotations.test.ts"];
const V_EXP = ["npx", "vitest", "run", "src/simulations/domains/geometry/Scene3DExplorer.test.tsx"];
const V_REF = ["npx", "vitest", "run", "src/components/refusal-contract.test.tsx"];
const NODE = ["node", "--test", "scripts/compiler-scene-replay-lib.node-test.mjs"];

// [id, file, old, new, what it simulates, command, predicted catch] — one line each: the worktree
// checks out CRLF, so a substitution never spans a line break.
const INJECTIONS = [
  ["FE1", ANN, 'const khaDung = ketQua ? ketLuan.has(o.id) : daTinh.has(o.id) || (o.origin === "free" && coMat.has(o.id));',
    'const khaDung = daTinh.has(o.id) || (o.origin === "free" && coMat.has(o.id));',
    "a result label available from its MEASUREMENT step (early answer)", V_ANN, "không lộ trước: tiến rồi lùi …"],
  ["FE2", ANN, "if (!(ketQua ? toggles.results : toggles.measurements)) continue;",
    "if (!(toggles.results && toggles.measurements)) continue;",
    "one chip hides both categories (toggle side effect)", V_ANN, "tắt Số đo ⇒ mất dữ kiện …; tắt Kết quả ⇒ mất đáp số"],
  ["FE3", ANN, "if (!khaDung || !a.subject_ids.every((s) => coMat.has(s))) continue;", "if (!khaDung) continue;",
    "a label whose subject is not on the figure yet", V_ANN,
    "dữ kiện có từ đầu nhưng chủ thể chưa dựng ⇒ chưa có nhãn (added after run 1: NOT CAUGHT)"],
  ["FE4", ANN, "const r = ung.find((c) => cachNeo(c, n.ax, n.ay) <= NEO_TOI_DA && !daChiem.some((b) => giao(c, b)));",
    "const r = ung.find((c) => cachNeo(c, n.ax, n.ay) <= NEO_TOI_DA);",
    "labels may cover point labels and each other", V_ANN, "chỗ trên đã có nhãn điểm ⇒ xuống dưới; ưu tiên cao đặt trước"],
  ["FE5", ANN, "{ x: phai, y: tren }, { x: trai, y: tren }, { x: phai, y: duoi }, { x: trai, y: duoi },", "",
    "no corner positions (the T7 state: a crowded base label hidden)", V_ANN, "bốn phía đã kín ⇒ thử bốn góc"],
  ["FE11", ANN, "const KHE = [6, 12, 18];", "const KHE = [6];",
    "no outer rings (the T7 confirm-round state: a label half a pixel short of free is hidden)", V_ANN,
    "tám chỗ sát neo đều chạm ⇒ lùi ra vòng xa hơn"],
  ["FE6", ANN, "priority: (ketQua ? 2 : 1) + (lienQuan ? 10 : 0),", "priority: ketQua ? 2 : 1,",
    "the label of the selected subject loses its priority", V_ANN, "chọn chủ thể thì nhãn liên quan được ưu tiên"],
  ["FE7", ANN, "Object.freeze({ measurements: true, results: true });", "Object.freeze({ measurements: false, results: true });",
    "Số đo OFF by default (U-W17-1 says both ON)", V_ANN, "mặc định BẬT cả Số đo và Kết quả"],
  ["FE8", EXP, "{coSoDo.measurements && (", "{(true || coSoDo.measurements) && (",
    "a Số đo chip on a scene with no measurement label (fabricated affordance, §3.2)", V_EXP,
    "cảnh không có nhãn số đo nào ⇒ không có công tắc"],
  ["FE9", SW, '? unsupported.refusal_cause === "SOURCE" || unsupported.refusal_cause === "CONSTRUCTION"', "? false",
    "the hint repeats the backend message again (the T7 state)", V_REF, "SOURCE/CONSTRUCTION — không có câu gợi ý nhắc lại"],
  ["FE10", SW, 'unsupported.refusal_cause === "CONSTRUCTION" && khoaLoai === "input_not_grounded"', 'khoaLoai === "__never__"',
    "a CONSTRUCTION refusal labelled as untraceable data", V_REF, "CONSTRUCTION ở cổng nguồn — loại vấn đề …"],
  ["FH1", LIB, "const cameraDoi = (a, b) => cameraMotion(a, b) > CAMERA_SETTLE_TOLERANCE;",
    "const cameraDoi = (a, b) => JSON.stringify(a) !== JSON.stringify(b);",
    "cameras compared by bytes (ULP damping reads as a camera change)", NODE, "W17 toggle isolation and causal restore …"],
  ["FH2", LIB, "&& (hop ?? []).every((r) => x < r.x - margin || x > r.x + r.w + margin",
    "&& [].every((r) => x < r.x - margin || x > r.x + r.w + margin",
    "section-fill samples under DOM labels", NODE, "W17 section fill sampler: no sample under a DOM label box"],
];

// [id, file, old, new, what it simulates, family, viewport, predicted reason code]
const BROWSER = [
  ["FB1", EXP, "onClick={() => setSoDo((s) => ({ ...s, measurements: !s.measurements }))}",
    "onClick={() => { setSoDo((s) => ({ ...s, measurements: !s.measurements })); setTt((s) => ({ ...s, current_step: 0 })); }}",
    "the Số đo chip also rewinds the construction to step 0", "triangular_pyramid", "desktop", "TOGGLE_CHANGED_STEP"],
  ["FB2", LIB, 'export const LOP_PHU_KHUNG = ".geo3d-noi,.geo3d-soi,.geo3d-label,.geo3d-so-do";',
    'export const LOP_PHU_KHUNG = ".geo3d-noi,.geo3d-soi,.geo3d-label";',
    "quantity labels no longer masked from the figure's pixel measures (the T7 state)", "triangular_pyramid", "desktop",
    "CAUSAL_CANVAS_ROLE_HUE"],
];
// The run filter (scratch copy only): one family, one viewport for the positive run.
const LOC = [
  ["    for (const scenario of suite.scenarios) {",
    "    for (const scenario of suite.scenarios.filter((x) => x.id === process.env.W17_FI_HO)) {"],
  ["        record.positive[viewport.id] = await runPositive({",
    "        if (viewport.id !== process.env.W17_FI_KHUNG) continue; record.positive[viewport.id] = await runPositive({"],
];

const chay = ([cmd, ...args], env = {}) => {
  const r = spawnSync(cmd, args, { cwd: FE, encoding: "utf-8", shell: process.platform === "win32",
    env: { ...process.env, ...env }, timeout: 1_800_000 });
  const out = `${r.stdout}\n${r.stderr}`;
  const tom = out.split("\n").filter((x) => /Tests +\d|ℹ (pass|fail) /.test(x)).map((x) => x.trim()).join(" · ");
  const hong = out.split("\n").filter((x) => /^\s*(×|✖|FAIL)\s/.test(x)).map((x) => x.trim()).slice(0, 8);
  return { code: r.status, tom, hong };
};

/** Apply `[file, old, new]` substitutions; returns a restore function, or a STALE message. */
function thay(ds) {
  const goc = new Map();
  for (const [tep, cu, moi] of ds) {
    const duong = join(FE, tep);
    if (!goc.has(duong)) goc.set(duong, readFileSync(duong));
    const src = readFileSync(duong, "utf-8");
    const n = src.split(cu).length - 1;
    if (n !== 1) {
      for (const [d, b] of goc) writeFileSync(d, b);
      return `STALE: substitution found ${n}x in ${tep}`;
    }
    writeFileSync(duong, src.replace(cu, moi), "utf-8");
  }
  return () => [...goc].every(([d, b]) => (writeFileSync(d, b), readFileSync(d).equals(b)));
}

function chayTrinhDuyet(id, ho, khung, ma) {
  const ra = resolve(`D:/tmp/w17-fi-${id.toLowerCase()}${(process.argv[4] ?? "").toLowerCase()}`);
  const r = chay(["node", "scripts/compiler-scene-replay.mjs", "--suite", "scripts/generic-tier-a-scenarios.json",
    "--fixture-root", FIXTURES, "--ra", ra], { W17_FI_HO: ho, W17_FI_KHUNG: khung });
  const tep = join(ra, "BROWSER_EVIDENCE.json");
  if (!existsSync(tep)) return { code: r.code, thay: null, ra };
  const ev = JSON.parse(readFileSync(tep, "utf-8"));
  return { code: r.code, thay: JSON.stringify(ev.scenarios?.[ho]?.positive?.[khung] ?? {}).includes(ma), ra };
}

const head = execFileSync("git", ["-C", WT, "rev-parse", "--short=8", "HEAD"], { encoding: "utf-8" }).trim();
const ra = [`W17 — frontend fault injections on the detached worktree at ${head} (0 model calls)`,
  "method: one exact one-line substitution per run in the scratch worktree, test, then the original bytes "
  + "restored and verified; browser injections add a one-family/one-viewport run filter to the scratch copy", ""];
for (const cmd of [V_ANN, V_EXP, V_REF, NODE]) {
  const b = chay(cmd);
  ra.push(`baseline ${cmd.slice(-1)[0]}: exit ${b.code} · ${b.tom}`);
}
ra.push("");
for (const [id, tep, cu, moi, moTa, lenh, duDoan] of INJECTIONS) {
  const lai = thay([[tep, cu, moi]]);
  if (typeof lai === "string") { ra.push(`${id} ${lai}`, ""); continue; }
  let kq;
  try { kq = chay(lenh); } finally { kq = { ...kq, restored: lai() }; }
  ra.push(`${id} [${tep}] ${moTa}`, `  predicted: ${duDoan}`,
    `  observed : exit ${kq.code} · ${kq.tom} -> ${kq.code !== 0 ? "CAUGHT" : "NOT CAUGHT"}`,
    ...kq.hong.map((h) => `    ${h}`), `  restored byte-identical: ${kq.restored}`, "");
}
if (FIXTURES) {
  const [, , , , , ho0, khung0] = BROWSER[0];
  const loc = thay(LOC.map(([cu, moi]) => [SUITE, cu, moi]));
  if (typeof loc === "string") ra.push(`browser filter ${loc}`, "");
  else {
    try {
      const b = chayTrinhDuyet("baseline", ho0, khung0, "");
      const ev = JSON.parse(readFileSync(join(b.ra, "BROWSER_EVIDENCE.json"), "utf-8"));
      const p = ev.scenarios?.[ho0]?.positive?.[khung0] ?? {};
      ra.push(`browser baseline ${ho0}/${khung0}: positive pass ${p.pass} · predicted codes present: `
        + BROWSER.map(([id, , , , , , , ma]) => `${id}:${JSON.stringify(p).includes(ma)}`).join(" "), "");
      for (const [id, tep, cu, moi, moTa, ho, khung, ma] of BROWSER) {
        const lai = thay([[tep, cu, moi]]);
        if (typeof lai === "string") { ra.push(`${id} ${lai}`, ""); continue; }
        let kq;
        try { kq = chayTrinhDuyet(id, ho, khung, ma); } finally { kq = { ...kq, restored: lai() }; }
        ra.push(`${id} [${tep}] ${moTa} (${ho}/${khung})`, `  predicted: ${ma}`,
          `  observed : suite exit ${kq.code} · ${ma} in the positive evidence: ${kq.thay} -> ${kq.thay ? "CAUGHT" : "NOT CAUGHT"}`,
          `  evidence: ${kq.ra}`, `  restored byte-identical: ${kq.restored}`, "");
      }
    } finally {
      ra.push(`browser filter removed byte-identical: ${loc()}`, "");
    }
  }
}
for (const cmd of [V_ANN, V_EXP, V_REF, NODE]) {
  const b = chay(cmd);
  ra.push(`after all injections ${cmd.slice(-1)[0]}: exit ${b.code} · ${b.tom}`);
}
writeFileSync(OUT, ra.join("\n") + "\n", "utf-8");
console.log(ra.join("\n"));
