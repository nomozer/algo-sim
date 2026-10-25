// Compare renderer rim hidden flags with the oracle's for one recorded camera. node ../.superpowers/rim-flags.mjs <receipt> <case> <width> <camera>
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import { sectionBoundaryWorld } from "../../../../../../frontend/scripts/section-role-oracle.mjs";
const { chromium } = createRequire(process.cwd() + "/package.json")("playwright");
const [receipt, cid, width, camName] = process.argv.slice(2);
const row = JSON.parse(readFileSync(receipt, "utf8")).rows.find(r => r.case === cid && r.width === Number(width) && r.cameraName === camName && r.fault === "none");
const cases = JSON.parse(readFileSync("../docs/evaluation/geometry/runs/f2-role-aware-oracle/inputs/cases.json", "utf8"));
const c = cases.find(x => x.id === cid);
const scene = JSON.parse(readFileSync(c.envelope_file, "utf8")).scene3d;
const oracle = sectionBoundaryWorld(scene, c.section, row.camera).map(s => s.hidden ? "h" : "f").join("");
const b = await chromium.launch({ channel: "chrome", headless: true });
const p = await b.newPage();
await p.goto("http://127.0.0.1:3161/");
const renderer = await p.evaluate(async ({ scene, section, pos }) => {
  const V = await import("/src/simulations/domains/geometry/scene3d-view.tsx");
  const E = await import("/src/simulations/domains/geometry/scene3d-edge-visibility.ts");
  const THREE = await import("/node_modules/.vite-cache-probe-none/three.js").catch(() => null);
  const root = (V.buildObject3D(scene.objects.find(o => o.id === section), "dich"));
  const vols = [];
  for (const o of scene.objects.filter(o => o.type === "curved_solid")) {
    const g = V.buildObject3D(o, false); g.updateMatrixWorld(true);
    g.traverse(n => { if (n.userData.curvedSolidVolume) vols.push(n.userData.curvedSolidVolume); });
  }
  root.updateMatrixWorld(true);
  let out = "";
  root.traverse(n => {
    const rim = n.userData.curvedRimLoop; if (!rim) return;
    const cam = rim.midpoints[0].clone().set(...pos);
    out = rim.midpoints.map(mp => E.classifyWorldSegmentVisibility(mp.clone().applyMatrix4(n.matrixWorld), mp.clone().applyMatrix4(n.matrixWorld), cam, [], { curved_occluders: vols }).spans[0].visibility === "HIDDEN" ? "h" : "f").join("");
  });
  return { out, vols: vols.map(v => ({ ...v, anchor: v.anchor.toArray(), top: v.top?.toArray() })) };
}, { scene, section: c.section, pos: row.camera.position });
await b.close();
console.log("oracle  ", oracle);
console.log("renderer", renderer.out);
console.log(JSON.stringify(renderer.vols));
