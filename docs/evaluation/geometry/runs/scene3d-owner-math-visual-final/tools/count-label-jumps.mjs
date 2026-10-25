// Label-jump count with the SAME heuristic as scene3d-final-acceptance/tools/summarize-motion.mjs (offset change
// > 20 CSS px while the projected source anchor moves < 5 CSS px within <= 100 ms). Review flags, not a math oracle.
// node .../tools/count-label-jumps.mjs <motion/receipt.json>   (run from the worktree root)
import { readFileSync } from "node:fs";
import { project } from "../../../../../../frontend/scripts/section-role-oracle.mjs";
const read = (p) => JSON.parse(readFileSync(p, "utf8"));
const motion = read(process.argv[2]);
const scenes = new Map();
for (const id of ["cross_section", "triangular_prism", "cuboid"]) scenes.set(id, read(`docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/visual/final-inputs/fixtures/${id}_positive.json`).envelope.scene3d);
for (const s of read("frontend/src/data/geometry-samples.json").samples) scenes.set(s.id, s.envelope.scene3d);
for (const s of read("docs/evaluation/geometry/runs/geometric-visual-correctness-framing/demos/audit_scenes.json")) scenes.set(s.id, s.scene);
const num = (s) => { const [a, b = "1"] = String(s).split("/"); return Number(a) / Number(b); };
let total = 0;
const rows = motion.rows.map((row) => {
  const points = new Map(scenes.get(row.id).objects.filter((o) => o.type === "point3").map((o) => [o.id, o]));
  let previous = new Map(), jumps = 0, compared = 0;
  for (const frame of row.motion.snapshots) {
    const current = new Map(), camera = frame.camera;
    for (const label of frame.labels) {
      const o = points.get(label.id);
      if (!o?.xyz) continue;
      const a = project(o.xyz.map(num), camera, { w: camera.viewport_width, h: camera.viewport_height });
      const v = { ...label, ax: a.x, ay: a.y, t: frame.t };
      current.set(label.id, v);
      const p = previous.get(label.id);
      if (!p || frame.t - p.t > 100) continue;
      compared += 1;
      const anchorMove = Math.hypot(a.x - p.ax, a.y - p.ay);
      const offsetJump = Math.hypot(label.x - a.x - (p.x - p.ax), label.y - a.y - (p.y - p.ay));
      if (anchorMove < 5 && offsetJump > 20) jumps += 1;
    }
    previous = current;
  }
  total += jumps;
  return { id: row.id, width: row.width, compared, jumps };
});
console.log(JSON.stringify({ total_jump_flags: total, rows }, null, 1));
