/**
 * PROPOSED role-aware section check (run `f2-role-aware-oracle`) — NOT wired into the locked official suite.
 *
 * Owner policy F2: a section keeps its semantic terracotta fill; when it is the selected target its BOUNDARY turns
 * cobalt. The locked hue gate (`assessCausalCanvasHues`) counts every orange pixel of a selected-state frame as a
 * violation, so it fails exactly this policy. This module checks the policy itself, per object:
 *   ① boundary — samples along every projected edge of the selected section (polygon edges, or a polyline of the
 *      projected circle/ellipse). Front edges are scored ONE BY ONE: enough visible samples must have cobalt within a
 *      small window. Edges seen through the translucent shell (`hidden`) are dashed and may be crossed by other
 *      outlines, so they are scored IN AGGREGATE with a lower threshold.
 *   ② fill — samples the shrunk interior (away from the boundary band): must read terracotta, must not read cobalt.
 *   ③ blue ownership — most cobalt pixels of the canvas must lie in the boundary band of THIS section.
 * Pure functions over an RGBA buffer; the browser probe supplies pixels, projection and overlay boxes. Hue bands and
 * the classifier are the locked suite's (`DAI_SAC_VAI_TRO`, `phanLoaiSac`) — no colour is redefined here.
 */
import { DAI_SAC_VAI_TRO, phanLoaiSac } from "./compiler-scene-replay-lib.mjs";

/** Thresholds fixed from the unfaulted baseline before any fault was run (see run report); not tuned on faults. */
export const NGUONG_VAI_THIET_DIEN = Object.freeze({
  samplesPerEdge: 12, windowCss: 2.5, minVisibleSamples: 3,
  frontCoverage: 0.75, hiddenCoverage: 0.4, minScoredLengthShare: 0.5,
  fillMinCam: 0.5, fillMaxXanh: 0.05, minFillSamples: 12, boundaryBandCss: 6, minBlueShareInBand: 0.7,
});

const inBox = (x, y, boxes, pad = 0) => boxes.some((r) => x >= r.x - pad && x <= r.x + r.w + pad && y >= r.y - pad && y <= r.y + r.h + pad);

function distToSegment(x, y, a, b) {
  const dx = b.x - a.x, dy = b.y - a.y, L = dx * dx + dy * dy || 1;
  const t = Math.max(0, Math.min(1, ((x - a.x) * dx + (y - a.y) * dy) / L));
  return Math.hypot(x - a.x - t * dx, y - a.y - t * dy);
}

function insidePolygon(x, y, poly) {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const a = poly[i], b = poly[j];
    if ((a.y > y) !== (b.y > y) && x < ((b.x - a.x) * (y - a.y)) / (b.y - a.y) + a.x) c = !c;
  }
  return c;
}

/**
 * @param {{w:number,h:number,rgba:Uint8Array|Buffer}} img  canvas pixels (device px)
 * @param {object} o
 * @param {number} o.scale                device px per CSS px
 * @param {{w:number,h:number}} o.box     canvas size in CSS px
 * @param {{x,y,w,h}[]} o.overlays        DOM overlays in canvas CSS coordinates (excluded)
 * @param {{a:{x,y},b:{x,y},hidden:boolean}[]} o.edges  projected boundary (CSS px)
 */
export function assessSectionRole(img, { scale, box, overlays = [], edges }, N = NGUONG_VAI_THIET_DIEN) {
  const cls = (px, py) => {
    if (px < 0 || py < 0 || px >= img.w || py >= img.h) return null;
    const q = (py * img.w + px) * 4;
    return phanLoaiSac(img.rgba[q], img.rgba[q + 1], img.rgba[q + 2], DAI_SAC_VAI_TRO);
  };
  const usable = (x, y) => x >= 3 && y >= 3 && x <= box.w - 3 && y <= box.h - 3 && !inBox(x, y, overlays, 3);
  const r = Math.ceil(N.windowCss * scale);
  const totalLen = edges.reduce((s, e) => s + Math.hypot(e.b.x - e.a.x, e.b.y - e.a.y), 0) || 1;

  const edgeRows = edges.map((e, i) => {
    let visible = 0, blue = 0;
    for (let k = 0; k < N.samplesPerEdge; k += 1) {
      const t = 0.1 + (0.8 * k) / (N.samplesPerEdge - 1);
      const x = e.a.x + (e.b.x - e.a.x) * t, y = e.a.y + (e.b.y - e.a.y) * t;
      if (!usable(x, y)) continue;
      visible += 1;
      let hit = false;
      for (let dy = -r; dy <= r && !hit; dy += 1) {
        for (let dx = -r; dx <= r && !hit; dx += 1) hit = cls(Math.round(x * scale) + dx, Math.round(y * scale) + dy) === "xanh";
      }
      if (hit) blue += 1;
    }
    const scored = visible >= N.minVisibleSamples;
    const coverage = visible ? blue / visible : null;
    return { edge: i, hidden: Boolean(e.hidden), visible, blue, coverage, scored,
      length: Math.hypot(e.b.x - e.a.x, e.b.y - e.a.y), pass: scored && !e.hidden ? coverage >= N.frontCoverage : null };
  });
  const scoredShare = edgeRows.filter((e) => e.scored).reduce((s, e) => s + e.length, 0) / totalLen;

  // ② fill: interior grid, shrunk toward the centroid, outside the boundary band.
  const poly = edges.map((e) => e.a);
  const cx = poly.reduce((s, p) => s + p.x, 0) / poly.length, cy = poly.reduce((s, p) => s + p.y, 0) / poly.length;
  const shrunk = poly.map((p) => ({ x: cx + (p.x - cx) * 0.7, y: cy + (p.y - cy) * 0.7 }));
  const xs = shrunk.map((p) => p.x), ys = shrunk.map((p) => p.y);
  let fillN = 0, fillCam = 0, fillXanh = 0;
  const step = Math.max(2, (Math.max(...xs) - Math.min(...xs)) / 24);
  for (let y = Math.min(...ys); y <= Math.max(...ys); y += step) {
    for (let x = Math.min(...xs); x <= Math.max(...xs); x += step) {
      if (!insidePolygon(x, y, shrunk) || !usable(x, y)) continue;
      if (edges.some((e) => distToSegment(x, y, e.a, e.b) < N.boundaryBandCss)) continue;
      fillN += 1;
      const c = cls(Math.round(x * scale), Math.round(y * scale));
      if (c === "cam") fillCam += 1; else if (c === "xanh") fillXanh += 1;
    }
  }

  // ③ blue ownership over the whole canvas (overlays excluded).
  let blueAll = 0, blueBand = 0;
  for (let py = 0; py < img.h; py += 1) {
    for (let px = 0; px < img.w; px += 1) {
      const x = (px + 0.5) / scale, y = (py + 0.5) / scale;
      if (inBox(x, y, overlays) || cls(px, py) !== "xanh") continue;
      blueAll += 1;
      if (edges.some((e) => distToSegment(x, y, e.a, e.b) <= N.boundaryBandCss)) blueBand += 1;
    }
  }

  const reasons = [];
  const front = edgeRows.filter((e) => e.scored && !e.hidden), hiddenRows = edgeRows.filter((e) => e.scored && e.hidden);
  const hiddenSeen = hiddenRows.reduce((s, e) => s + e.visible, 0);
  const hiddenCoverage = hiddenSeen ? hiddenRows.reduce((s, e) => s + e.blue, 0) / hiddenSeen : null;
  if (scoredShare < N.minScoredLengthShare) reasons.push("BOUNDARY_NOT_OBSERVABLE");
  if (front.some((e) => !e.pass) || (hiddenCoverage !== null && hiddenCoverage < N.hiddenCoverage)) reasons.push("BOUNDARY_NOT_COBALT");
  if (fillN < N.minFillSamples) reasons.push("FILL_NOT_OBSERVABLE");
  else {
    if (fillCam / fillN < N.fillMinCam) reasons.push("FILL_NOT_TERRACOTTA");
    if (fillXanh / fillN > N.fillMaxXanh) reasons.push("FILL_TURNED_COBALT");
  }
  if (!blueAll || blueBand / blueAll < N.minBlueShareInBand) reasons.push("COBALT_NOT_ON_SELECTED_BOUNDARY");
  return {
    edges: edgeRows, scored_length_share: scoredShare, hidden_coverage: hiddenCoverage,
    fill: { samples: fillN, cam: fillCam, xanh: fillXanh },
    blue: { all: blueAll, in_band: blueBand, share: blueAll ? blueBand / blueAll : 0 },
    reasons, pass: reasons.length === 0,
  };
}

/** Projects a point with the recorded camera matrices (column-major, as `__geo3d_camera_snapshot`). */
export function project(p, cam, box) {
  const m = (M, v) => [0, 1, 2, 3].map((r) => M[r] * v[0] + M[4 + r] * v[1] + M[8 + r] * v[2] + M[12 + r] * v[3]);
  const c = m(cam.projection_matrix_column_major, m(cam.view_matrix_column_major, [p[0], p[1], p[2], 1]));
  return { x: ((c[0] / c[3] + 1) * box.w) / 2, y: ((1 - c[1] / c[3]) * box.h) / 2 };
}

const num = (s) => { const [a, b] = String(s).split("/"); return Number(a) / (b ? Number(b) : 1); };
const sub = (a, b) => a.map((x, i) => x - b[i]);
const dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const SEG = 32;
const unit = (a) => { const n = Math.hypot(...a) || 1; return a.map((x) => x / n); };

/**
 * World boundary of a section object of the backend scene, as 3-D segments with a `hidden` flag (seen through the
 * translucent shell from `eye`). Polygon section: its `polygon`; a section edge is hidden when the solid face it lies
 * in faces away. Circle/ellipse: a SEG-segment polyline; a point is hidden when it is on the far side of the curved
 * solid from the eye (SEG segments). Returns null for shapes it cannot place (the probe then reports "not observable").
 */
export function sectionBoundaryWorld(scene, id, eye) {
  const objs = scene.objects ?? [];
  const o = objs.find((x) => x.id === id);
  if (!o) return null;
  const toV = (v) => v.map(num);
  if (o.type === "section" || o.type === "polygon3") {
    const pts = (o.polygon ?? o.vertices ?? []).map(toV);
    if (pts.length < 3) return null;
    const parent = objs.find((x) => x.id === o.parent && x.type === "solid");
    const verts = parent ? parent.vertex_ids.map((vid) => toV(objs.find((x) => x.id === vid)?.xyz ?? [0, 0, 0])) : [];
    const centroid = verts.length ? verts.reduce((s, v) => s.map((x, i) => x + v[i] / verts.length), [0, 0, 0]) : null;
    return pts.map((a, i) => {
      const b = pts[(i + 1) % pts.length];
      const mid = a.map((x, k) => (x + b[k]) / 2);
      let hidden = false;
      if (parent && centroid) {
        const face = (parent.faces ?? []).map((f) => f.map((k) => verts[k])).find((F) => {
          const n = cross(sub(F[1], F[0]), sub(F[2], F[0]));
          return Math.abs(dot(n, sub(a, F[0]))) < 1e-6 * Math.hypot(...n) && Math.abs(dot(n, sub(b, F[0]))) < 1e-6 * Math.hypot(...n);
        });
        if (face) {
          let n = cross(sub(face[1], face[0]), sub(face[2], face[0]));
          if (dot(n, sub(face[0], centroid)) < 0) n = n.map((x) => -x);
          hidden = dot(n, sub(eye, mid)) < 0;
        }
      }
      return { a, b, hidden };
    });
  }
  if (o.type === "circle3" || o.type === "ellipse3") {
    const c = toV(o.center), n = unit(toV(o.normal));
    let u, v, ru, rv;
    if (o.type === "circle3") {
      const t = Math.abs(n[0]) < 0.9 ? [1, 0, 0] : [0, 1, 0];
      u = unit(cross(n, t)); v = cross(n, u); ru = rv = Math.sqrt(num(o.radius_sq));
    } else {
      if (!o.major_dir || !o.minor_dir) return null;
      u = unit(toV(o.major_dir)); v = unit(toV(o.minor_dir));
      ru = Math.sqrt(num(o.semi_major_sq)); rv = Math.sqrt(num(o.semi_minor_sq));
      if (!Number.isFinite(ru) || !Number.isFinite(rv)) return null;
    }
    const solid = objs.find((x) => (o.depends ?? []).includes(x.id) && x.type === "curved_solid");
    const axisC = solid ? toV(solid.anchor) : c;
    const P = (k) => { const a = (2 * Math.PI * k) / SEG; return c.map((x, i) => x + ru * Math.cos(a) * u[i] + rv * Math.sin(a) * v[i]); };
    return Array.from({ length: SEG }, (_, k) => {
      const a = P(k), b = P(k + 1), mid = a.map((x, i) => (x + b[i]) / 2);
      let outward = sub(mid, axisC);
      if (solid && solid.curved_kind !== "ball" && solid.apex_or_top) {          // radial from the axis, not the anchor
        const ax = unit(sub(toV(solid.apex_or_top), axisC));
        outward = sub(outward, ax.map((x) => x * dot(outward, ax)));
      }
      return { a, b, hidden: dot(outward, sub(eye, mid)) < 0 };
    });
  }
  return null;
}
