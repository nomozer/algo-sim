// Diagnostic patch for a SCRATCH copy of compiler-scene-suite.mjs only (never the repository):
// one family / one viewport, plus a 40-frame series (100 ms apart) at the causal neutral and
// restored points, saving each distinct canvas frame and the label boxes / camera per frame.
// The scratch worktree checks out CRLF: every pattern stays on one line.
import { readFileSync, writeFileSync } from "node:fs";
const P = process.argv[2];
if (!/w17-diag/.test(P)) throw new Error("scratch worktree only");
let s = readFileSync(P, "utf8");
const rep = (a, b) => { const k = s.split(a).length - 1; if (k !== 1) throw new Error(`${k}x: ${a.slice(0, 60)}`); s = s.replace(a, b); };
rep("    for (const scenario of suite.scenarios) {",
  "    for (const scenario of suite.scenarios.filter((x) => x.id === process.env.W17_FI_HO)) {");
rep("        record.positive[viewport.id] = await runPositive({",
  "        if (viewport.id !== process.env.W17_FI_KHUNG) continue; record.positive[viewport.id] = await runPositive({");
const CHUOI = [
  "async function chuoiKhung(session, outDir, ten) {",
  "  const ds = []; const da = new Set();",
  "  for (let i = 0; i < 40; i += 1) {",
  "    const f = await canvasFrame(session);",
  "    const t = await jsonEval(session, \"({ann:window.__geo3d_annotation_boxes||null,pts:window.__geo3d_point_label_boxes||null,\"",
  "      + \"cam:window.__geo3d_camera_snapshot||null,scroll:window.scrollY,now:performance.now(),\"",
  "      + \"op:Array.from(document.querySelectorAll('.geo3d-so-do,.geo3d-label')).map((e)=>[e.dataset.annId||e.dataset.id,getComputedStyle(e).opacity,e.style.transform])})\");",
  "    ds.push({ i, sha: f.sha256.slice(0, 12), ...t });",
  "    if (!da.has(f.sha256)) { da.add(f.sha256); writeFileSync(join(outDir, `diag_${ten}_${String(i).padStart(2, \"0\")}_${f.sha256.slice(0, 8)}.png`), Buffer.from(f.encoded, \"base64\")); }",
  "    await new Promise((d) => setTimeout(d, 100));",
  "  }",
  "  writeFileSync(join(outDir, `diag_${ten}.json`), JSON.stringify(ds, null, 1));",
  "}",
  "",
  "async function khungOnDinh(session) {",
].join("\r\n");
rep("async function khungOnDinh(session) {", CHUOI);
rep("    const causalBeforeFrame = await khungOnDinh(session);",
  "    const causalBeforeFrame = await khungOnDinh(session); await chuoiKhung(session, outDir, \"neutral\");");
rep("    const restoredFrame = await khungOnDinh(session);",
  "    const restoredFrame = await khungOnDinh(session); await chuoiKhung(session, outDir, \"restored\");");
writeFileSync(P, s);
console.log("patched", P);
