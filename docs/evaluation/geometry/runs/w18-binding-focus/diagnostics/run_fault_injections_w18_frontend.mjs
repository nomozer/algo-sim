// W18 — frontend fault injections (focused labels, one explanation place, witness, browser harness), 0
// model calls. Same mechanism as the W17 driver (immutable, w17-operation-annotations/diagnostics):
//
// Runs ONLY on a detached scratch worktree given as the first argument (refuses the main repository).
// Unit injections: one exact one-line substitution (must match exactly once, else STALE), the predicted
// test command, then the original bytes are written back and verified. Browser injections: the fault
// plus a run filter (one family, one viewport — scratch copy only, never part of the committed suite),
// the suite on that worktree, then the predicted reason code is read from its evidence; a filtered
// baseline runs first. Writes `logs/FAULT_INJECTION_W18_FRONTEND<suffix>.log` next to this script;
// refuses to overwrite. Usage (from the repository root):
//   node docs/evaluation/geometry/runs/w18-binding-focus/diagnostics/run_fault_injections_w18_frontend.mjs D:/tmp/w18-fe D:/tmp/w18-fixtures [suffix]
//
// The brief's minimum list maps to: result too early = FE1; all labels on by default = FE2; label on the
// wrong subject = FE3; two duplicate detail panels = FE4 (unit) and FW4 (browser); highlight turning
// dashed lines solid = FW1. The backend ones are in `run_fault_injections_w18.py`.
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const HERE = import.meta.dirname;
const OUT = join(HERE, "logs", `FAULT_INJECTION_W18_FRONTEND${process.argv[4] ?? ""}.log`);
const WT = resolve(process.argv[2] ?? "");
const FIXTURES = process.argv[3] ? resolve(process.argv[3]) : null;
if (!process.argv[2] || resolve(HERE, "..", "..", "..", "..", "..", "..") === WT) {
  throw new Error("pass a detached scratch worktree, never the main repository");
}
if (existsSync(OUT)) throw new Error(`refusing to overwrite ${OUT}`);
const FE = join(WT, "frontend");
const G = "src/simulations/domains/geometry/";
const ANN = `${G}scene3d-annotations.ts`;
const EXP = `${G}Scene3DExplorer.tsx`;
const SOL = `${G}scene3d-solution.tsx`;
const VIEW = `${G}scene3d-view.tsx`;
const SUITE = "scripts/compiler-scene-suite.mjs";
const V_ANN = ["npx", "vitest", "run", `${G}scene3d-annotations.test.ts`];
const V_EXP = ["npx", "vitest", "run", `${G}Scene3DExplorer.test.tsx`];
const NODE = ["node", "--test", "scripts/compiler-scene-replay-lib.node-test.mjs"];

// [id, file, old, new, what it simulates, command, predicted catch] — one line each (CRLF checkout).
const INJECTIONS = [
  ["FE1", ANN, '    const khaDung = vai === "result" ? ketLuan.has(o.id) : daTinh.has(o.id) || (o.origin === "free" && coMat.has(o.id));',
    '    const khaDung = daTinh.has(o.id) || (o.origin === "free" && coMat.has(o.id));',
    "a result label available from its MEASUREMENT step (result too early)", V_ANN,
    "Hiện tất cả: … đáp số vẫn chỉ từ bước kết luận; chọn một đại lượng … chọn trước bước kết luận"],
  ["FE2", ANN, "export const DEFAULT_ANNOTATION_VIEW: AnnotationView = Object.freeze({ showAll: false });",
    "export const DEFAULT_ANNOTATION_VIEW: AnnotationView = Object.freeze({ showAll: true });",
    "every label on by default", V_ANN, "mặc định chỉ dữ kiện đề cho …"],
  ["FE3", ANN, "    return p.length === 2 && p[0] && p[1] ? trungBinh([p[0], p[1]]) : null;",
    "    return p[0] ?? null;",
    "a segment label anchored at one endpoint (label on the wrong subject)", V_ANN,
    "điểm neo: trung điểm đoạn, trọng tâm miền, trọng tâm khối …"],
  ["FE4", EXP, "            {formula && !moLoiGiai && (", "            {formula && (",
    "the inspector keeps its formula while the open solution shows it (two detail copies)", V_EXP,
    "mở lời giải ⇒ công thức ở lời giải (ô soi khi ấy bỏ khối công thức)"],
  ["FE5", ANN, "    if (!(view.showAll || vai === \"given\" || lienQuan)) continue;",
    "    if (!(view.showAll || vai === \"given\")) continue;",
    "selecting a quantity does not bring its label and numeric chain", V_ANN,
    "chọn một đại lượng: nó và chuỗi số của nó …; chọn một vật …"],
  ["FE6", SOL, "  const rieng = (xs: SolutionItem[]) => xs.filter((x) => goc(x.id) === x.id);",
    "  const rieng = (xs: SolutionItem[]) => xs;",
    "a same_as measurement gets a second solution row", V_EXP, "same_as: đại lượng đo lại đúng dữ kiện không có dòng thứ hai"],
  ["FE7", SOL, "  const [moTrong, setMoTrong] = useState(false);", "  const [moTrong, setMoTrong] = useState(true);",
    "the full solution open by default", V_EXP, "lời giải đầy đủ THU GỌN mặc định …"],
  ["FE8", VIEW, '          <div ref={soDoRef} className="geo3d-so-do-lop" aria-label="Số đo trên hình">',
    '          <div ref={soDoRef} className="geo3d-so-do-lop" aria-hidden="true">',
    "the label layer hidden from assistive technology (labels not operable)", V_EXP,
    "nhãn số đo bấm được: lớp nhãn không còn aria-hidden …"],
];

// [id, file, old, new, what it simulates, family, viewport, predicted reason code]
// Run 2 (amendment §16.8 dated correction, registered before re-measuring): FW1 now predicts the per-step dash
// check (run 1 predicted the causal `dash_signature_preserved`, which no edge highlight reaches); FW4 runs on a
// family whose result carries a referenced formula (cross_section has none, so run 1 could not see it).
const BROWSER = [
  ["FW1", VIEW, '    const isHidden = span.visibility === "HIDDEN";',
    '    const isHidden = span.visibility === "HIDDEN" && owner.userData.highlighted !== true;',
    "a highlighted hidden edge drawn solid", "triangular_pyramid", "desktop", "DASH_DIFFERS_FROM_OCCLUSION"],
  ["FW2", EXP, "              onClick={() => setXem((s) => ({ showAll: !s.showAll }))}",
    "              onClick={() => { setXem((s) => ({ showAll: !s.showAll })); setTt((s) => ({ ...s, current_step: 0 })); }}",
    "the 'Hiện tất cả' chip also rewinds the construction to step 0", "triangular_pyramid", "desktop",
    "SHOW_ALL_OFF_CHANGED_STEP"],
  ["FW3", VIEW, "    const ds = witnessesShown(scene, nhanSoDo);",
    "    const ds = witnessesShown(scene, annotationsAt(scene, buoc, { showAll: true }, null));",
    "every witness drawn whether or not its distance label shows", "cross_section", "desktop",
    "WITNESS_NOT_SHOWN_LABEL"],
  ["FW4", EXP, "            {formula && !moLoiGiai && (", "            {formula && (",
    "two regions carry the selected quantity's formula", "triangular_pyramid", "desktop", "DETAIL_REGIONS_2"],
];
// The run filter (scratch copy only): one family, one viewport for the positive run.
const LOC = [
  ["    for (const scenario of suite.scenarios) {",
    "    for (const scenario of suite.scenarios.filter((x) => x.id === process.env.W18_FI_HO)) {"],
  ["        record.positive[viewport.id] = await runPositive({",
    "        if (viewport.id !== process.env.W18_FI_KHUNG) continue; record.positive[viewport.id] = await runPositive({"],
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
  const ra = resolve(`D:/tmp/w18-fi-${id.toLowerCase()}${(process.argv[4] ?? "").toLowerCase()}`);
  const r = chay(["node", "scripts/compiler-scene-replay.mjs", "--suite", "scripts/generic-tier-a-scenarios.json",
    "--fixture-root", FIXTURES, "--ra", ra], { W18_FI_HO: ho, W18_FI_KHUNG: khung });
  const tep = join(ra, "BROWSER_EVIDENCE.json");
  if (!existsSync(tep)) return { code: r.code, thay: null, ra };
  const ev = JSON.parse(readFileSync(tep, "utf-8"));
  return { code: r.code, thay: JSON.stringify(ev.scenarios?.[ho]?.positive?.[khung] ?? {}).includes(ma), ra };
}

const head = execFileSync("git", ["-C", WT, "rev-parse", "--short=8", "HEAD"], { encoding: "utf-8" }).trim();
const ra = [`W18 — frontend fault injections on the detached worktree at ${head} (0 model calls)`,
  "method: one exact one-line substitution per run in the scratch worktree, test, then the original bytes "
  + "restored and verified; browser injections add a one-family/one-viewport run filter to the scratch copy", ""];
for (const cmd of [V_ANN, V_EXP, NODE]) {
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
  const loc = thay(LOC.map(([cu, moi]) => [SUITE, cu, moi]));
  if (typeof loc === "string") ra.push(`browser filter ${loc}`, "");
  else {
    try {
      for (const [ho0, khung0] of [...new Set(BROWSER.map(([, , , , , ho, khung]) => `${ho}|${khung}`))]
        .map((x) => x.split("|"))) {
        const b = chayTrinhDuyet(`baseline-${ho0}`, ho0, khung0, "");
        const ev = JSON.parse(readFileSync(join(b.ra, "BROWSER_EVIDENCE.json"), "utf-8"));
        const p = ev.scenarios?.[ho0]?.positive?.[khung0] ?? {};
        ra.push(`browser baseline ${ho0}/${khung0}: positive pass ${p.pass} · predicted codes present: `
          + BROWSER.filter(([, , , , , ho]) => ho === ho0)
            .map(([id, , , , , , , ma]) => `${id}:${JSON.stringify(p).includes(ma)}`).join(" "), "");
      }
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
for (const cmd of [V_ANN, V_EXP, NODE]) {
  const b = chay(cmd);
  ra.push(`after all injections ${cmd.slice(-1)[0]}: exit ${b.code} · ${b.tom}`);
}
writeFileSync(OUT, ra.join("\n") + "\n", "utf-8");
console.log(ra.join("\n"));
