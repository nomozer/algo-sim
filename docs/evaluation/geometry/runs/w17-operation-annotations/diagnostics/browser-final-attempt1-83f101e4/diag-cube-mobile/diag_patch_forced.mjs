// Run 3 of this diagnostic ("forced"): exercises the new causal-restore frame-difference path once in a
// real browser. Apply to a SCRATCH copy that already holds the fixed harness (compiler-scene-suite.mjs
// and compiler-scene-replay-lib.mjs from the working tree after the fix), never to the repository:
// one family / one viewport, and the frame-difference branch taken even when the two frames are
// byte-identical. The scratch worktree checks out CRLF: every pattern stays on one line.
//   node diag_patch_forced.mjs D:/tmp/w17-diag-cube/frontend/scripts/compiler-scene-suite.mjs
//   (cd D:/tmp/w17-diag-cube/frontend && W17_FI_HO=cube W17_FI_KHUNG=mobile node scripts/compiler-scene-replay.mjs ...)
import { readFileSync, writeFileSync } from "node:fs";
const P = process.argv[2];
if (!/w17-diag/.test(P)) throw new Error("scratch worktree only");
let s = readFileSync(P, "utf8");
const rep = (a, b) => { const k = s.split(a).length - 1; if (k !== 1) throw new Error(`${k}x: ${a.slice(0, 60)}`); s = s.replace(a, b); };
rep("    for (const scenario of suite.scenarios) {",
  "    for (const scenario of suite.scenarios.filter((x) => x.id === process.env.W17_FI_HO)) {");
rep("        record.positive[viewport.id] = await runPositive({",
  "        if (viewport.id !== process.env.W17_FI_KHUNG) continue; record.positive[viewport.id] = await runPositive({");
rep("    const savedFrames = restoredFrame.sha256 === causalBeforeFrame.sha256 ? []", "    const savedFrames = false ? []");
writeFileSync(P, s);
console.log("scratch patched (forced delta path)");
