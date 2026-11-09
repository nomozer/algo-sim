import type { ReactNode } from "react";
import * as THREE from "three";
import { GEOMETRY_SAMPLES } from "../data/geometry-samples";
import { veKhongGian } from "../simulations/domains/geometry/scene3d-chart";
import {
  chonHuongNhin,
  hopBaoCuaDiem,
  khungNhinSuPham,
  khungNhinVua,
} from "../simulations/domains/geometry/scene3d-camera";
import {
  canonicalEdgesOf,
  classifySolidEdgeVisibility,
  classifyWorldSegmentVisibility,
  diemVanhCongBiChe,
  resolveObliqueCylinderCapBasis,
  type CurvedSolidVolumeMeta,
  type WorldSolidOccluder,
} from "../simulations/domains/geometry/scene3d-edge-visibility";
import {
  anchorOfGeometryStep,
  daGiacMatPhang,
  diemChoDuong,
  diemHuuHan,
  diemNeoNhanMatPhang,
  geometryStepCount,
  moRongDaGiacMatPhang,
  objectsAt,
  registerExactSceneOrigin,
  toNumber,
  toVec3,
  type Scene3D,
  type SceneObject,
  type Vec3,
} from "../simulations/domains/geometry/scene3d-model";
import { auxiliaryHiddenAt } from "../simulations/domains/geometry/scene3d-auxiliary";
import { kyHieu, veTrenKhung } from "../simulations/domains/geometry/scene3d-presentation";
import {
  buildPedagogicalConstructionPlan,
  cauTrucSuPham,
  classifyCircleSemanticRole,
  compactPlaneAnchorPoints,
  computeBoundedStudiedPlanePolygon,
  inspectAxialCurvedOrthogonality,
  isAuxiliaryExplanatoryPolygon,
  planeSolidEdgeIntersections,
  resolvePlanePerpendicularLineWitness,
  resolveStepVisualRoles,
  ungroundedFreePointIdsAt,
} from "../simulations/domains/geometry/scene3d-semantic-policy";
import { isSubEntity, laDiemPhuDungMatPhang, withSubEntities } from "../simulations/domains/geometry/scene3d-subentities";

/**
 * Thumbnail SVG chuẩn hóa của Axo — chiếu trực tiếp từ dữ liệu `Scene3D` bước cuối
 * của `GEOMETRY_SAMPLES` (`withSubEntities` → `buildPedagogicalConstructionPlan` → `veKhongGian`
 * → `cauTrucSuPham` + `chonHuongNhin` + `classifySolidEdgeVisibility` / `classifyWorldSegmentVisibility` / `diemVanhCongBiChe`).
 * Dùng chung cho Trang chủ (`HomeView`), Thư viện (`LibraryView`) và Lịch sử (`SessionCard`).
 */

export type PreviewKind = "geometry";

export function previewKindOf(_simId: string): PreviewKind {
  return "geometry";
}

const GEO_THUMB_PALETTE = {
  ink: "#1E293B",
  dashed: "#64748B",
  shellFill: "rgba(148, 163, 184, 0.11)",
  shellFillStrong: "rgba(148, 163, 184, 0.17)",
  terracotta: "#C85A32",
  terracottaFill: "rgba(200, 90, 50, 0.25)",
  teal: "#0F766E",
  tealFill: "rgba(15, 118, 110, 0.16)",
  cobalt: "#2563EB",
  amber: "#D97706",
  amberFill: "rgba(217, 119, 6, 0.18)",
  planeFill: "rgba(109, 40, 217, 0.085)",
  planeStroke: "rgba(109, 40, 217, 0.38)",
  planeLabel: "#6D28D9",
} as const;

function GeoPt({
  x,
  y,
  label,
  dx,
  dy,
  color,
  r,
}: {
  x: number;
  y: number;
  label?: string;
  dx?: number;
  dy?: number;
  color?: string;
  r?: number;
}) {
  const c = color || GEO_THUMB_PALETTE.ink;
  const rad = r || 2.3;
  const tx = Number((x + (dx !== undefined ? dx : 0)).toFixed(1));
  const ty = Number((y + (dy !== undefined ? dy : -5)).toFixed(1));
  return (
    <>
      <circle cx={Number(x.toFixed(1))} cy={Number(y.toFixed(1))} r={rad} fill={c} />
      {label ? (
        <text
          x={tx}
          y={ty}
          fontFamily="Plus Jakarta Sans, sans-serif"
          fontSize="10.2"
          fontWeight="700"
          fill={c}
          paintOrder="stroke"
          stroke="#f8f6f1"
          strokeWidth="2.4"
          strokeLinejoin="round"
          textAnchor="middle"
          dominantBaseline="central"
        >
          {label}
        </text>
      ) : null}
    </>
  );
}

function GeoRightAngle({
  vx,
  vy,
  ux,
  uy,
  wx,
  wy,
  size,
  color,
}: {
  vx: number;
  vy: number;
  ux: number;
  uy: number;
  wx: number;
  wy: number;
  size?: number;
  color?: string;
}) {
  const s = size || 6.0;
  const c = color || GEO_THUMB_PALETTE.teal;
  const uLen = Math.hypot(ux, uy) || 1;
  const wLen = Math.hypot(wx, wy) || 1;
  const u1x = (ux / uLen) * s;
  const u1y = (uy / uLen) * s;
  const w1x = (wx / wLen) * s;
  const w1y = (wy / wLen) * s;
  const p1x = (vx + u1x).toFixed(1);
  const p1y = (vy + u1y).toFixed(1);
  const p2x = (vx + u1x + w1x).toFixed(1);
  const p2y = (vy + u1y + w1y).toFixed(1);
  const p3x = (vx + w1x).toFixed(1);
  const p3y = (vy + w1y).toFixed(1);
  return (
    <polyline
      points={`${p1x},${p1y} ${p2x},${p2y} ${p3x},${p3y}`}
      fill="none"
      stroke={c}
      strokeWidth="1.25"
      strokeLinejoin="round"
    />
  );
}

function orthonormalCircleBasis(normal: THREE.Vector3): [THREE.Vector3, THREE.Vector3] {
  const n = normal.clone().normalize();
  const ref = Math.abs(n.z) < 0.9 ? new THREE.Vector3(0, 0, 1) : new THREE.Vector3(0, 1, 0);
  const u1 = new THREE.Vector3().crossVectors(n, ref).normalize();
  const u2 = new THREE.Vector3().crossVectors(n, u1).normalize();
  return [u1, u2];
}

function isRedundantPolyhedronBasePlane(plane: SceneObject, presentObjects: readonly SceneObject[]): boolean {
  if (plane.type !== "plane3" || !plane.point || !plane.normal) return false;
  const p0 = toVec3(plane.point);
  const nRaw = toVec3(plane.normal);
  const nLen = Math.hypot(...nRaw);
  if (nLen <= 1e-9) return false;
  const nx = nRaw[0] / nLen;
  const ny = nRaw[1] / nLen;
  const nz = nRaw[2] / nLen;

  const basePolys = presentObjects.filter(
    (o) =>
      !isSubEntity(o.id)
      && o.type === "polygon3"
      && (o.surface_role === "BASE_REGION" || o.id.startsWith("day_"))
      && (o.polygon ?? o.vertices ?? []).length >= 3,
  );
  for (const bp of basePolys) {
    const verts = (bp.polygon ?? bp.vertices ?? []).map(toVec3);
    const allCoplanar = verts.every(
      (v) => Math.abs((v[0] - p0[0]) * nx + (v[1] - p0[1]) * ny + (v[2] - p0[2]) * nz) <= 1e-4,
    );
    if (allCoplanar) return true;
  }
  return false;
}

const _thumbnailNodeCache = new Map<string, ReactNode>();

function buildScene3DThumbnailNode(rawScene: Scene3D): ReactNode {
  const pedPlan = buildPedagogicalConstructionPlan(withSubEntities(rawScene));
  const scene = registerExactSceneOrigin(veKhongGian(pedPlan.scene), pedPlan.scene);
  const lastStep = pedPlan.steps[pedPlan.steps.length - 1];
  const finalAnchor =
    lastStep?.anchor ?? anchorOfGeometryStep(scene, Math.max(0, geometryStepCount(scene) - 1));
  const rawHiddenAux = auxiliaryHiddenAt(scene, finalAnchor, false, null);
  const ungroundedPts = ungroundedFreePointIdsAt(scene, finalAnchor);
  const stepVisualRoles = resolveStepVisualRoles(scene, finalAnchor, { auxiliaryShown: false });
  const byObjId = new Map(scene.objects.map((o) => [o.id, o]));
  const rawPresentObjects = objectsAt(scene, finalAnchor);
  const hiddenAux = new Set(
    [...rawHiddenAux].filter((id) => {
      const obj = byObjId.get(id);
      if (!obj) return true;
      if ((obj.display_group ?? []).includes("sphere_plane_aux")) return false;
      return true;
    }),
  );
  const presentObjects = rawPresentObjects.filter(
    (o) =>
      !isSubEntity(o.id)
      && veTrenKhung(o)
      && !ungroundedPts.has(o.id)
      && (o.type === "plane3" ? !isRedundantPolyhedronBasePlane(o, rawPresentObjects) : !hiddenAux.has(o.id))
      && (o.type === "plane3" || (stepVisualRoles.get(o.id)?.visible ?? true)),
  );
  const nonAuxPlaneObjects = presentObjects.filter(
    (o) => (o.display_group ?? []).includes("sphere_plane_aux") || !laDiemPhuDungMatPhang(scene, o, byObjId),
  );
  const finitePts = diemHuuHan(nonAuxPlaneObjects);

  const computePlaneSheet = (o: SceneObject): Vec3[] => {
    if (o.type !== "plane3" || !o.point || !o.normal) return [];
    if (isRedundantPolyhedronBasePlane(o, presentObjects)) return [];
    const circleSec = presentObjects.find(
      (cand) =>
        cand.type === "circle3"
        && cand.surface_role !== "BASE_REGION"
        && (cand.depends ?? []).includes(o.id)
        && cand.center
        && cand.radius_sq,
    );
    if (circleSec?.center && circleSec.radius_sq) {
      const c = new THREE.Vector3(...toVec3(circleSec.center));
      const rSec = Math.sqrt(Math.max(0, toNumber(circleSec.radius_sq))) * 1.28;
      const nVec = new THREE.Vector3(...toVec3(o.normal));
      const [u1, u2] = orthonormalCircleBasis(nVec);
      return [
        [-1, -1],
        [1, -1],
        [1, 1],
        [-1, 1],
      ].map(([sx, sy]): Vec3 => {
        const pt = c.clone().addScaledVector(u1, sx * rSec).addScaledVector(u2, sy * rSec);
        return [pt.x, pt.y, pt.z];
      });
    }
    const studied = computeBoundedStudiedPlanePolygon(scene, o, presentObjects);
    if (studied.length >= 3) return studied;
    const compactAnchors = compactPlaneAnchorPoints(scene, o, presentObjects);
    const diemChoMp =
      compactAnchors.length >= 3
        ? compactAnchors
        : [
            ...diemHuuHan(
              nonAuxPlaneObjects.filter(
                (x) =>
                  o.depends.includes(x.id)
                  || x.type === "solid"
                  || (x.type === "section" && x.depends.includes(o.id)),
              ),
            ),
            ...planeSolidEdgeIntersections(o, presentObjects),
          ];
    const mpPts = diemChoMp.length >= 3 ? diemChoMp : finitePts;
    const p0 = toVec3(o.point);
    const nVec = toVec3(o.normal);
    const daGiac = daGiacMatPhang(p0, nVec, mpPts);
    return moRongDaGiacMatPhang(p0, nVec, mpPts, daGiac) ?? daGiac ?? [];
  };

  const ct = cauTrucSuPham(nonAuxPlaneObjects);
  const cameraFitPts: Vec3[] = [...ct.diem];
  for (const o of nonAuxPlaneObjects) {
    if (o.type === "curved_solid" && o.anchor) {
      const a = toVec3(o.anchor);
      const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq ?? "0")));
      const h = Math.sqrt(Math.max(0, toNumber(o.height_sq ?? "0")));
      cameraFitPts.push(
        [a[0] + r, a[1], a[2]],
        [a[0] - r, a[1], a[2]],
        [a[0], a[1] + r, a[2]],
        [a[0], a[1] - r, a[2]],
      );
      if (o.curved_kind === "ball") {
        cameraFitPts.push([a[0], a[1], a[2] + r], [a[0], a[1], a[2] - r]);
      } else {
        const top = o.apex_or_top ? toVec3(o.apex_or_top) : [a[0], a[1], a[2] + h];
        cameraFitPts.push(
          [top[0], top[1], top[2]],
          [top[0] + r, top[1], top[2]],
          [top[0] - r, top[1], top[2]],
        );
      }
    }
  }
  const dir = chonHuongNhin(cameraFitPts, ct.canh, ct.mat, ct.tuyChon);
  const kn =
    khungNhinSuPham(cameraFitPts, ct.canh, ct.mat, 38, 1, dir, {
      tiLeDoc: 0.78,
      tiLeNgang: 0.78,
    }) ?? khungNhinVua(hopBaoCuaDiem(cameraFitPts.length >= 2 ? cameraFitPts : [[0, 0, 0], [1, 1, 1]]), 38, 1)!;

  // Use aspect=1 on PerspectiveCamera so projected NDC (v.x, v.y) is 1:1 isotropic when scaled into SVG pixels
  const cam = new THREE.PerspectiveCamera(38, 1, 0.1, 200);
  cam.up.set(0, 0, 1);
  cam.position.set(...kn.viTri);
  cam.lookAt(...kn.nhinVao);
  cam.updateMatrixWorld(true);
  cam.updateProjectionMatrix();

  const camForward = new THREE.Vector3(...kn.nhinVao).sub(cam.position).normalize();
  const camRight = new THREE.Vector3().crossVectors(camForward, new THREE.Vector3(0, 0, 1)).normalize();
  const camUp = new THREE.Vector3().crossVectors(camRight, camForward).normalize();

  // Collect all key 3D points to frame within viewBox="0 0 180 110"
  const framingPts: THREE.Vector3[] = [];
  for (const p of ct.diem) {
    framingPts.push(new THREE.Vector3(...p));
  }
  for (const o of nonAuxPlaneObjects) {
    if (o.type === "point3" && o.xyz) {
      framingPts.push(new THREE.Vector3(...toVec3(o.xyz)));
    } else if (o.type === "curved_solid" && o.anchor) {
      const anchor = new THREE.Vector3(...toVec3(o.anchor));
      const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq ?? "0")));
      const h = Math.sqrt(Math.max(0, toNumber(o.height_sq ?? "0")));
      const top = o.apex_or_top
        ? new THREE.Vector3(...toVec3(o.apex_or_top))
        : o.curved_kind !== "ball" && h > 0
          ? new THREE.Vector3(anchor.x, anchor.y, anchor.z + h)
          : null;
      if (o.curved_kind === "ball") {
        framingPts.push(
          anchor.clone().addScaledVector(camRight, r),
          anchor.clone().addScaledVector(camRight, -r),
          anchor.clone().addScaledVector(camUp, r),
          anchor.clone().addScaledVector(camUp, -r),
        );
      } else if (top) {
        const axis = top.clone().sub(anchor).normalize();
        const [u1, u2] = orthonormalCircleBasis(axis);
        for (let k = 0; k < 8; k += 1) {
          const ang = (k / 8) * Math.PI * 2;
          const rimOffset = u1
            .clone()
            .multiplyScalar(r * Math.cos(ang))
            .addScaledVector(u2, r * Math.sin(ang));
          framingPts.push(anchor.clone().add(rimOffset));
          if (o.curved_kind === "cylinder") {
            framingPts.push(top.clone().add(rimOffset));
          }
        }
        framingPts.push(top);
      }
    } else if (o.type === "plane3") {
      const sheet = computePlaneSheet(o);
      for (const sp of sheet) {
        framingPts.push(new THREE.Vector3(...sp));
      }
    }
  }

  let minNdcX = Infinity;
  let maxNdcX = -Infinity;
  let minNdcY = Infinity;
  let maxNdcY = -Infinity;
  for (const fp of framingPts) {
    const v = fp.clone().project(cam);
    if (!Number.isFinite(v.x) || !Number.isFinite(v.y)) continue;
    minNdcX = Math.min(minNdcX, v.x);
    maxNdcX = Math.max(maxNdcX, v.x);
    minNdcY = Math.min(minNdcY, v.y);
    maxNdcY = Math.max(maxNdcY, v.y);
  }
  if (!Number.isFinite(minNdcX)) {
    minNdcX = -0.5;
    maxNdcX = 0.5;
    minNdcY = -0.5;
    maxNdcY = 0.5;
  }

  const spanX = Math.max(1e-4, maxNdcX - minNdcX);
  const spanY = Math.max(1e-4, maxNdcY - minNdcY);
  const scale = Math.min(132 / spanX, 74 / spanY);
  const midX = (minNdcX + maxNdcX) * 0.5;
  const midY = (minNdcY + maxNdcY) * 0.5;

  const proj = (p: Vec3 | THREE.Vector3): [number, number] => {
    const v = (p instanceof THREE.Vector3 ? p.clone() : new THREE.Vector3(p[0], p[1], p[2])).project(cam);
    return [
      Number((90 + (v.x - midX) * scale).toFixed(1)),
      Number((57 - (v.y - midY) * scale).toFixed(1)),
    ];
  };

  // Build 3D occluders & curved solid volumes for exact visibility classification
  const presentSolids = presentObjects.filter((o) => o.type === "solid" && o.vertices && o.faces);
  const solidOccluders: WorldSolidOccluder[] = presentSolids.map((s) => ({ solid: s }));
  const curvedVolumes: CurvedSolidVolumeMeta[] = [];

  for (const o of presentObjects) {
    if (o.type !== "curved_solid" || !o.anchor || !o.curved_kind) continue;
    const anchor = new THREE.Vector3(...toVec3(o.anchor));
    const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq ?? "0")));
    const h = Math.sqrt(Math.max(0, toNumber(o.height_sq ?? "0")));
    if (!(r > 1e-6)) continue;
    const top = o.apex_or_top
      ? new THREE.Vector3(...toVec3(o.apex_or_top))
      : o.curved_kind !== "ball" && h > 0
        ? new THREE.Vector3(anchor.x, anchor.y, anchor.z + h)
        : null;
    const hActual = top ? anchor.distanceTo(top) : h;
    const baseCapCircle =
      o.curved_kind === "cylinder" && top
        ? presentObjects.find((cand) => {
            if (cand.type !== "circle3" || cand.surface_role !== "BASE_REGION" || !cand.center || !cand.normal)
              return false;
            const cc = toVec3(cand.center);
            return (
              Math.hypot(cc[0] - anchor.x, cc[1] - anchor.y, cc[2] - anchor.z) <= 1e-4
              || Math.hypot(cc[0] - top.x, cc[1] - top.y, cc[2] - top.z) <= 1e-4
            );
          })
        : undefined;
    const obliqueCap =
      o.curved_kind === "cylinder" && top && baseCapCircle?.normal
        ? resolveObliqueCylinderCapBasis(anchor, top, new THREE.Vector3(...toVec3(baseCapCircle.normal)))
        : null;
    curvedVolumes.push({
      id: o.id,
      kind: o.curved_kind as "cylinder" | "cone" | "ball",
      anchor,
      top,
      radius: r,
      height: hActual,
      ...(obliqueCap ? { capBasis: [obliqueCap.u1.clone(), obliqueCap.u2.clone()] } : {}),
    });
  }

  const elements: ReactNode[] = [];
  let keySeq = 0;
  const nextKey = (prefix: string) => `${prefix}-${(keySeq += 1)}`;

  // Helper to sample a 3D circle and split into visible/hidden SVG polylines using exact 3D occlusion
  const render3DCircleArcs = (
    center: THREE.Vector3,
    u1: THREE.Vector3,
    u2: THREE.Vector3,
    radius: number,
    options: {
      fill?: string;
      visibleStroke: string;
      hiddenStroke: string;
      visibleWidth?: number;
      hiddenWidth?: number;
      dashArray?: string;
    },
  ) => {
    const segs = 72;
    const pts3: THREE.Vector3[] = [];
    const pts2: [number, number][] = [];
    for (let i = 0; i <= segs; i += 1) {
      const t = (i / segs) * Math.PI * 2;
      const p3 = center
        .clone()
        .addScaledVector(u1, radius * Math.cos(t))
        .addScaledVector(u2, radius * Math.sin(t));
      pts3.push(p3);
      pts2.push(proj(p3));
    }
    if (options.fill) {
      elements.push(
        <polygon
          key={nextKey("circle-fill")}
          points={pts2.slice(0, segs).map(([x, y]) => `${x},${y}`).join(" ")}
          fill={options.fill}
        />,
      );
    }
    const segStates: boolean[] = [];
    for (let i = 0; i < segs; i += 1) {
      const tm = ((i + 0.5) / segs) * Math.PI * 2;
      const radialDir = u1
        .clone()
        .multiplyScalar(Math.cos(tm))
        .addScaledVector(u2, Math.sin(tm));
      const mid3 = center.clone().addScaledVector(radialDir, radius * 1.0002);
      const isHidden = diemVanhCongBiChe(mid3, cam.position, curvedVolumes);
      segStates.push(isHidden);
    }
    let start = 0;
    for (let i = 1; i <= segs; i += 1) {
      if (i < segs && segStates[i] === segStates[start]) continue;
      const hidden = segStates[start];
      const spanPts = pts2.slice(start, i + 1).map(([x, y]) => `${x},${y}`).join(" ");
      elements.push(
        <polyline
          key={nextKey(hidden ? "arc-hid" : "arc-vis")}
          points={spanPts}
          fill="none"
          stroke={hidden ? options.hiddenStroke : options.visibleStroke}
          strokeWidth={hidden ? (options.hiddenWidth ?? 1.15) : (options.visibleWidth ?? 1.55)}
          strokeDasharray={hidden ? (options.dashArray ?? "3.5,2.5") : undefined}
          strokeLinejoin="round"
        />,
      );
      start = i;
    }
  };

  // 1. Active Cutting / Target Planes (`plane3`)
  const planeSheetsToLabel: { pts2: [number, number][]; defaultPos: [number, number]; text: string }[] = [];
  for (const o of presentObjects) {
    if (o.type !== "plane3" || !o.point || !o.normal) continue;
    const sheet = computePlaneSheet(o);
    if (sheet.length >= 3) {
      const pts2 = sheet.map((p) => proj(p));
      elements.push(
        <polygon
          key={nextKey(`plane-${o.id}`)}
          points={pts2.map(([x, y]) => `${x},${y}`).join(" ")}
          fill={GEO_THUMB_PALETTE.planeFill}
          stroke={GEO_THUMB_PALETTE.planeStroke}
          strokeWidth="0.95"
          strokeLinejoin="round"
        />,
      );
      const tag = kyHieu(o);
      if (tag && tag.startsWith("(")) {
        const neo3 = diemNeoNhanMatPhang(toVec3(o.point), toVec3(o.normal), sheet);
        const defaultPos: [number, number] = neo3 ? proj(neo3) : pts2[0];
        planeSheetsToLabel.push({ pts2, defaultPos, text: tag });
      }
    }
  }

  // 2. Polyhedral Solids (`solid`) — shell fill + hidden/visible canonical edges
  const canonicalEdgeSpans3D: { a: THREE.Vector3; b: THREE.Vector3 }[] = [];
  for (const o of presentSolids) {
    const verts = o.vertices!.map(toVec3);
    for (const f of o.faces ?? []) {
      if (f.length < 3) continue;
      const fPts = f.map((idx) => proj(verts[idx])).map(([x, y]) => `${x},${y}`).join(" ");
      elements.push(
        <polygon key={nextKey(`solid-face-${o.id}`)} points={fPts} fill={GEO_THUMB_PALETTE.shellFill} />,
      );
    }
    const basePoly = presentObjects.find(
      (cand) => cand.type === "polygon3" && (cand.surface_role === "BASE_REGION" || cand.id.startsWith("day_")),
    );
    if (basePoly && (basePoly.polygon ?? basePoly.vertices)) {
      const bPts = (basePoly.polygon ?? basePoly.vertices ?? [])
        .map((v) => proj(toVec3(v)))
        .map(([x, y]) => `${x},${y}`)
        .join(" ");
      elements.push(
        <polygon key={nextKey(`base-tint-${basePoly.id}`)} points={bPts} fill="rgba(148, 163, 184, 0.08)" />,
      );
    }
    const edges = canonicalEdgesOf(o);
    for (const e of edges) {
      canonicalEdgeSpans3D.push({ a: e.a.clone(), b: e.b.clone() });
    }
    const audit = classifySolidEdgeVisibility(o, cam.position, { occluders: presentSolids });
    const edgeById = new Map(edges.map((e) => [e.id, e]));
    for (const pass of ["HIDDEN", "VISIBLE"] as const) {
      for (const span of audit.edge_spans) {
        if (span.visibility !== pass) continue;
        const edge = edgeById.get(span.edge_id);
        if (!edge) continue;
        const p0 = proj(edge.a.clone().lerp(edge.b, span.t0));
        const p1 = proj(edge.a.clone().lerp(edge.b, span.t1));
        elements.push(
          <line
            key={nextKey(`edge-${span.edge_id}-${pass}`)}
            x1={p0[0]}
            y1={p0[1]}
            x2={p1[0]}
            y2={p1[1]}
            stroke={pass === "HIDDEN" ? GEO_THUMB_PALETTE.dashed : GEO_THUMB_PALETTE.ink}
            strokeWidth={pass === "HIDDEN" ? "1.15" : "1.55"}
            strokeDasharray={pass === "HIDDEN" ? "3.5,2.5" : undefined}
            strokeLinecap="round"
          />,
        );
      }
    }
  }

  // 3. Curved Solids (`curved_solid`: sphere, cylinder, cone)
  for (const vol of curvedVolumes) {
    if (vol.kind === "ball") {
      const [cx, cy] = proj(vol.anchor);
      const [rxPt, ryPt] = proj(vol.anchor.clone().addScaledVector(camRight, vol.radius));
      const rPx = Number(Math.max(12, Math.hypot(rxPt - cx, ryPt - cy)).toFixed(1));
      elements.push(
        <circle
          key={nextKey(`ball-shell-${vol.id}`)}
          cx={cx}
          cy={cy}
          r={rPx}
          fill={GEO_THUMB_PALETTE.shellFillStrong}
          stroke={GEO_THUMB_PALETTE.ink}
          strokeWidth="1.6"
        />,
      );
      const [u1, u2] = orthonormalCircleBasis(new THREE.Vector3(0, 0, 1));
      render3DCircleArcs(vol.anchor, u1, u2, vol.radius, {
        visibleStroke: GEO_THUMB_PALETTE.dashed,
        hiddenStroke: GEO_THUMB_PALETTE.dashed,
        visibleWidth: 1.15,
        hiddenWidth: 1.0,
        dashArray: "3.5,2.8",
      });
    } else if (vol.top && vol.height > 1e-6) {
      const axis = vol.top.clone().sub(vol.anchor).normalize();
      const [u1, u2] = vol.capBasis ?? orthonormalCircleBasis(axis);
      const relative = cam.position.clone().sub(vol.anchor);
      const axial = relative.dot(axis);
      const radial = relative.clone().addScaledVector(axis, -axial);
      const distance = radial.length();
      const cosine =
        distance > 1e-6 ? (vol.radius * (vol.kind === "cone" ? 1 - axial / vol.height : 1)) / distance : 0;

      if (Math.abs(cosine) < 1) {
        const radialUnit = radial.clone().divideScalar(distance);
        const across = new THREE.Vector3().crossVectors(axis, radialUnit).normalize();
        const sinVal = Math.sqrt(Math.max(0, 1 - cosine * cosine));
        const uSil0 = radialUnit.clone().multiplyScalar(cosine).addScaledVector(across, sinVal);
        const uSil1 = radialUnit.clone().multiplyScalar(cosine).addScaledVector(across, -sinVal);
        const b0 = vol.anchor.clone().addScaledVector(uSil0, vol.radius);
        const b1 = vol.anchor.clone().addScaledVector(uSil1, vol.radius);
        const t0 = vol.kind === "cone" ? vol.top.clone() : vol.top.clone().addScaledVector(uSil0, vol.radius);
        const t1 = vol.kind === "cone" ? vol.top.clone() : vol.top.clone().addScaledVector(uSil1, vol.radius);

        const pb0 = proj(b0);
        const pb1 = proj(b1);
        const pt0 = proj(t0);
        const pt1 = proj(t1);
        elements.push(
          <polygon
            key={nextKey(`curved-shell-${vol.id}`)}
            points={
              vol.kind === "cone"
                ? `${pb0[0]},${pb0[1]} ${pt0[0]},${pt0[1]} ${pb1[0]},${pb1[1]}`
                : `${pb0[0]},${pb0[1]} ${pt0[0]},${pt0[1]} ${pt1[0]},${pt1[1]} ${pb1[0]},${pb1[1]}`
            }
            fill={GEO_THUMB_PALETTE.shellFill}
          />,
        );
        render3DCircleArcs(vol.anchor, u1, u2, vol.radius, {
          fill: "rgba(148, 163, 184, 0.09)",
          visibleStroke: GEO_THUMB_PALETTE.ink,
          hiddenStroke: GEO_THUMB_PALETTE.dashed,
          visibleWidth: 1.55,
          hiddenWidth: 1.15,
        });
        if (vol.kind === "cylinder") {
          render3DCircleArcs(vol.top, u1, u2, vol.radius, {
            fill: GEO_THUMB_PALETTE.shellFillStrong,
            visibleStroke: GEO_THUMB_PALETTE.ink,
            hiddenStroke: GEO_THUMB_PALETTE.dashed,
            visibleWidth: 1.55,
            hiddenWidth: 1.15,
          });
        }
        elements.push(
          <line
            key={nextKey(`sil0-${vol.id}`)}
            x1={pb0[0]}
            y1={pb0[1]}
            x2={pt0[0]}
            y2={pt0[1]}
            stroke={GEO_THUMB_PALETTE.ink}
            strokeWidth="1.55"
            strokeLinecap="round"
          />,
          <line
            key={nextKey(`sil1-${vol.id}`)}
            x1={pb1[0]}
            y1={pb1[1]}
            x2={pt1[0]}
            y2={pt1[1]}
            stroke={GEO_THUMB_PALETTE.ink}
            strokeWidth="1.55"
            strokeLinecap="round"
          />,
        );
      }
    }
  }

  // 4. Cross-Sections & Active Polygons (`section`, `polygon3`, `circle3`, `ellipse3`)
  for (const o of presentObjects) {
    if (o.type === "section" || o.type === "polygon3") {
      if (o.type === "polygon3" && (o.surface_role === "BASE_REGION" || o.id.startsWith("day_"))) continue;
      if ((o.display_group ?? []).includes("face") && o.parent) continue;
      const rawVerts = (o.polygon ?? o.vertices ?? []).map(toVec3);
      if (rawVerts.length < 3) continue;
      const isAux = isAuxiliaryExplanatoryPolygon(scene, o);
      const strokeColor = isAux ? GEO_THUMB_PALETTE.teal : GEO_THUMB_PALETTE.terracotta;
      const fillColor = isAux ? GEO_THUMB_PALETTE.tealFill : GEO_THUMB_PALETTE.terracottaFill;
      const pts2 = rawVerts.map((v) => proj(v));
      elements.push(
        <polygon
          key={nextKey(`sec-fill-${o.id}`)}
          points={pts2.map(([x, y]) => `${x},${y}`).join(" ")}
          fill={fillColor}
        />,
      );
      for (let i = 0; i < rawVerts.length; i += 1) {
        const a3 = new THREE.Vector3(...rawVerts[i]);
        const b3 = new THREE.Vector3(...rawVerts[(i + 1) % rawVerts.length]);
        canonicalEdgeSpans3D.push({ a: a3.clone(), b: b3.clone() });
        const vis = classifyWorldSegmentVisibility(a3, b3, cam.position, solidOccluders, {
          curved_occluders: curvedVolumes,
        });
        for (const span of vis.spans) {
          const p0 = proj(a3.clone().lerp(b3, span.t0));
          const p1 = proj(a3.clone().lerp(b3, span.t1));
          const hidden = span.visibility === "HIDDEN";
          elements.push(
            <line
              key={nextKey(`sec-edge-${o.id}-${i}`)}
              x1={p0[0]}
              y1={p0[1]}
              x2={p1[0]}
              y2={p1[1]}
              stroke={strokeColor}
              strokeWidth={hidden ? "1.35" : "1.85"}
              strokeDasharray={hidden ? "3.5,2.5" : undefined}
              strokeLinecap="round"
            />,
          );
        }
      }
    } else if (o.type === "circle3" && o.center && o.normal && o.radius_sq) {
      const role = classifyCircleSemanticRole(scene, o);
      if (role === "REFERENCE_EQUATOR" || role === "REFERENCE_GREAT_CIRCLE" || role === "BOUNDARY_AND_INTERSECTION")
        continue;
      const center = new THREE.Vector3(...toVec3(o.center));
      const normal = new THREE.Vector3(...toVec3(o.normal));
      const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq)));
      if (!(r > 1e-6) || normal.lengthSq() <= 1e-12) continue;
      const [u1, u2] = orthonormalCircleBasis(normal);
      render3DCircleArcs(center, u1, u2, r, {
        fill: GEO_THUMB_PALETTE.terracottaFill,
        visibleStroke: GEO_THUMB_PALETTE.terracotta,
        hiddenStroke: GEO_THUMB_PALETTE.terracotta,
        visibleWidth: 1.85,
        hiddenWidth: 1.35,
      });
    }
  }

  // 5. Segments & Lines (`segment3`, `line3`)
  const isCoveredByCanonicalEdge = (a: THREE.Vector3, b: THREE.Vector3): boolean =>
    canonicalEdgeSpans3D.some((e) => {
      const ab = e.b.clone().sub(e.a);
      const lenSq = ab.lengthSq();
      if (lenSq <= 1e-10) return false;
      const ta = a.clone().sub(e.a).dot(ab) / lenSq;
      const tb = b.clone().sub(e.a).dot(ab) / lenSq;
      if (ta < -1e-3 || ta > 1 + 1e-3 || tb < -1e-3 || tb > 1 + 1e-3) return false;
      const da = e.a.clone().addScaledVector(ab, ta).distanceTo(a);
      const db = e.a.clone().addScaledVector(ab, tb).distanceTo(b);
      return da <= 1e-3 && db <= 1e-3;
    });

  for (const o of presentObjects) {
    if (o.type === "segment3") {
      const rawA = o.point_a ?? o.endpoints?.[0];
      const rawB = o.point_b ?? o.endpoints?.[1];
      if (!rawA || !rawB) continue;
      const a3 = new THREE.Vector3(...toVec3(rawA));
      const b3 = new THREE.Vector3(...toVec3(rawB));
      const isWitnessOrHeight =
        Boolean(o.perpendicular_witness || o.annotation?.witness)
        || (o.formation_roles ?? []).includes("CONSTRUCT_HEIGHT");
      if (!isWitnessOrHeight && isCoveredByCanonicalEdge(a3, b3)) continue;
      const vis = classifyWorldSegmentVisibility(a3, b3, cam.position, solidOccluders, {
        curved_occluders: curvedVolumes,
      });
      const strokeColor = isWitnessOrHeight ? GEO_THUMB_PALETTE.teal : GEO_THUMB_PALETTE.terracotta;
      for (const span of vis.spans) {
        const p0 = proj(a3.clone().lerp(b3, span.t0));
        const p1 = proj(a3.clone().lerp(b3, span.t1));
        const hidden = span.visibility === "HIDDEN";
        elements.push(
          <line
            key={nextKey(`seg-${o.id}`)}
            x1={p0[0]}
            y1={p0[1]}
            x2={p1[0]}
            y2={p1[1]}
            stroke={strokeColor}
            strokeWidth={hidden ? "1.55" : "1.95"}
            strokeDasharray={hidden ? "3.5,2.5" : undefined}
            strokeLinecap="round"
          />,
        );
      }
    } else if (o.type === "line3" && o.point && o.direction) {
      const p0 = toVec3(o.point);
      const d = toVec3(o.direction);
      const dLen = Math.hypot(...d);
      if (dLen <= 1e-9) continue;
      const dirUnit: Vec3 = [d[0] / dLen, d[1] / dLen, d[2] / dLen];
      const linePts = diemChoDuong(presentObjects, o.id);
      let tMin = -0.6;
      let tMax = 2.6;
      if (linePts.length >= 2) {
        const ts = linePts.map(
          (q) => (q[0] - p0[0]) * dirUnit[0] + (q[1] - p0[1]) * dirUnit[1] + (q[2] - p0[2]) * dirUnit[2],
        );
        const lo = Math.min(...ts);
        const hi = Math.max(...ts);
        if (hi - lo > 1e-3) {
          const pad = Math.max(0.28, (hi - lo) * 0.14);
          tMin = lo - pad;
          tMax = hi + pad;
        }
      }
      const a3 = new THREE.Vector3(
        p0[0] + dirUnit[0] * tMin,
        p0[1] + dirUnit[1] * tMin,
        p0[2] + dirUnit[2] * tMin,
      );
      const b3 = new THREE.Vector3(
        p0[0] + dirUnit[0] * tMax,
        p0[1] + dirUnit[1] * tMax,
        p0[2] + dirUnit[2] * tMax,
      );
      if (o.id === "sd" && isCoveredByCanonicalEdge(new THREE.Vector3(...p0), new THREE.Vector3(...p0).add(new THREE.Vector3(...dirUnit)))) {
        continue;
      }
      const vis = classifyWorldSegmentVisibility(a3, b3, cam.position, solidOccluders, {
        curved_occluders: curvedVolumes,
      });
      const strokeColor = o.id === "truc" ? GEO_THUMB_PALETTE.teal : GEO_THUMB_PALETTE.cobalt;
      for (const span of vis.spans) {
        const s0 = proj(a3.clone().lerp(b3, span.t0));
        const s1 = proj(a3.clone().lerp(b3, span.t1));
        const hidden = span.visibility === "HIDDEN";
        elements.push(
          <line
            key={nextKey(`line-${o.id}`)}
            x1={s0[0]}
            y1={s0[1]}
            x2={s1[0]}
            y2={s1[1]}
            stroke={strokeColor}
            strokeWidth={hidden ? "1.45" : "1.8"}
            strokeDasharray={hidden ? "3.5,2.5" : undefined}
            strokeLinecap="round"
          />,
        );
      }
    }
  }

  // 6. Certified Right-Angle Witnesses (`perpendicular_witness` / `resolvePlanePerpendicularLineWitness` / `inspectAxialCurvedOrthogonality`)
  const drawnRightAngleFeet = new Set<string>();
  const pushRightAngle3D = (foot: Vec3, uVec: Vec3, vVec: Vec3) => {
    const fKey = foot.map((c) => c.toFixed(2)).join(",");
    if (drawnRightAngleFeet.has(fKey)) return;
    drawnRightAngleFeet.add(fKey);
    const uLen = Math.hypot(...uVec);
    const vLen = Math.hypot(...vVec);
    if (uLen <= 1e-6 || vLen <= 1e-6) return;
    const [fx, fy] = proj(foot);
    const [ux, uy] = proj([foot[0] + uVec[0] / uLen, foot[1] + uVec[1] / uLen, foot[2] + uVec[2] / uLen]);
    const [wx, wy] = proj([foot[0] + vVec[0] / vLen, foot[1] + vVec[1] / vLen, foot[2] + vVec[2] / vLen]);
    elements.push(
      <GeoRightAngle
        key={nextKey("ra")}
        vx={fx}
        vy={fy}
        ux={ux - fx}
        uy={uy - fy}
        wx={wx - fx}
        wy={wy - fy}
        size={5.8}
        color={GEO_THUMB_PALETTE.teal}
      />,
    );
  };

  for (const o of presentObjects) {
    const w = o.perpendicular_witness ?? o.annotation?.witness;
    if (w?.foot && w.marker) {
      pushRightAngle3D(toVec3(w.foot), toVec3(w.marker.u), toVec3(w.marker.v));
    }
    if (o.type === "plane3") {
      const mpW = resolvePlanePerpendicularLineWitness(scene, o, presentObjects);
      if (mpW) {
        pushRightAngle3D(mpW.foot, mpW.uUnit, mpW.vUnit);
      }
    }
    if (o.type === "curved_solid" && o.anchor && o.apex_or_top) {
      const ortho = inspectAxialCurvedOrthogonality(scene, o);
      if (ortho.isRightCertified) {
        const foot = toVec3(o.anchor);
        const top = toVec3(o.apex_or_top);
        const vVec: Vec3 = [top[0] - foot[0], top[1] - foot[1], top[2] - foot[2]];
        const rimPtObj = presentObjects.find(
          (p) => p.type === "point3" && p.xyz && (o.depends ?? []).includes(p.id) && p.id !== "O" && p.id !== "S" && p.id !== "O_prime",
        );
        if (rimPtObj?.xyz) {
          const rPt = toVec3(rimPtObj.xyz);
          const uVec: Vec3 = [rPt[0] - foot[0], rPt[1] - foot[1], rPt[2] - foot[2]];
          pushRightAngle3D(foot, uVec, vVec);
        }
      }
    }
  }

  // 7. Named Points (`point3`) & Plane Notation Badges
  const givenPointCoords = nonAuxPlaneObjects
    .filter((o) => o.type === "point3" && o.xyz && !isSubEntity(o.id) && o.origin !== "derived")
    .map((o) => toVec3(o.xyz!));

  const namedPointObjs = nonAuxPlaneObjects.filter((o) => {
    if (o.type !== "point3" || !o.xyz || isSubEntity(o.id)) return false;
    const sym = kyHieu(o) ?? "";
    if (!sym || sym.length > 4) return false;
    if (o.origin === "derived") {
      const p = toVec3(o.xyz);
      const coincidesWithGiven = givenPointCoords.some(
        (g) => Math.hypot(p[0] - g[0], p[1] - g[1], p[2] - g[2]) <= 1e-4,
      );
      if (coincidesWithGiven) return false;
    }
    return true;
  });

  const projectedPoints = namedPointObjs.map((o) => {
    const p3 = toVec3(o.xyz!);
    const [x, y] = proj(p3);
    const sym = kyHieu(o) ?? o.id;
    const isDerived = o.origin === "derived";
    return { id: o.id, label: sym, x, y, isDerived };
  });

  const cxMean =
    projectedPoints.length > 0
      ? projectedPoints.reduce((s, p) => s + p.x, 0) / projectedPoints.length
      : 90;
  const cyMean =
    projectedPoints.length > 0
      ? projectedPoints.reduce((s, p) => s + p.y, 0) / projectedPoints.length
      : 55;

  const occupiedPositions: [number, number][] = [];
  for (const pt of projectedPoints) {
    let vx = pt.x - cxMean;
    let vy = pt.y - cyMean;
    const vLen = Math.hypot(vx, vy);
    if (vLen < 1e-3) {
      vx = -1;
      vy = -1;
    } else {
      vx /= vLen;
      vy /= vLen;
    }
    const dist = 8.5;
    const dx = Math.max(8, Math.min(172, pt.x + vx * dist)) - pt.x;
    const dy = Math.max(9, Math.min(102, pt.y + vy * dist)) - pt.y;
    occupiedPositions.push([pt.x, pt.y], [pt.x + dx, pt.y + dy]);
    elements.push(
      <GeoPt
        key={nextKey(`pt-${pt.id}`)}
        x={pt.x}
        y={pt.y}
        label={pt.label}
        dx={dx}
        dy={dy}
        color={pt.isDerived ? GEO_THUMB_PALETTE.terracotta : GEO_THUMB_PALETTE.ink}
        r={pt.isDerived ? 2.4 : 2.3}
      />,
    );
  }

  for (const pl of planeSheetsToLabel) {
    const pCx = pl.pts2.reduce((s, p) => s + p[0], 0) / pl.pts2.length;
    const pCy = pl.pts2.reduce((s, p) => s + p[1], 0) / pl.pts2.length;
    const rawCandidates: [number, number][] = [pl.defaultPos];
    for (let i = 0; i < pl.pts2.length; i += 1) {
      const a = pl.pts2[i];
      const b = pl.pts2[(i + 1) % pl.pts2.length];
      const mid: [number, number] = [(a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5];
      for (const base of [a, mid]) {
        const ox = base[0] - pCx;
        const oy = base[1] - pCy;
        const oLen = Math.hypot(ox, oy) || 1;
        rawCandidates.push([base[0] + (ox / oLen) * 6, base[1] + (oy / oLen) * 4]);
      }
    }
    let bestPos: [number, number] = [
      Math.max(18, Math.min(162, pl.defaultPos[0])),
      Math.max(13, Math.min(100, pl.defaultPos[1])),
    ];
    let bestClearance = -Infinity;
    for (const [cx, cy] of rawCandidates) {
      const clampedX = Math.max(18, Math.min(162, cx));
      const clampedY = Math.max(13, Math.min(100, cy));
      const minClearance = occupiedPositions.reduce(
        (minD, [ox, oy]) => Math.min(minD, Math.hypot(clampedX - ox, clampedY - oy)),
        Infinity,
      );
      if (minClearance > bestClearance) {
        bestClearance = minClearance;
        bestPos = [Number(clampedX.toFixed(1)), Number(clampedY.toFixed(1))];
      }
    }
    occupiedPositions.push(bestPos);
    elements.push(
      <text
        key={nextKey(`pl-lbl-${pl.text}`)}
        x={bestPos[0]}
        y={bestPos[1]}
        fontFamily="Plus Jakarta Sans, sans-serif"
        fontStyle="italic"
        fontSize="9.8"
        fontWeight="700"
        fill={GEO_THUMB_PALETTE.planeLabel}
        paintOrder="stroke"
        stroke="#f8f6f1"
        strokeWidth="2.2"
        strokeLinejoin="round"
        textAnchor="middle"
      >
        {pl.text}
      </text>,
    );
  }

  return <>{elements}</>;
}

function getCachedSampleThumbnailNode(sampleId: string): ReactNode | null {
  if (_thumbnailNodeCache.has(sampleId)) {
    return _thumbnailNodeCache.get(sampleId)!;
  }
  const sample = GEOMETRY_SAMPLES.find((s) => s.id === sampleId);
  const rawScene = (sample?.envelope as { scene3d?: Scene3D } | undefined)?.scene3d;
  if (!rawScene) return null;
  const node = buildScene3DThumbnailNode(rawScene);
  _thumbnailNodeCache.set(sampleId, node);
  return node;
}

function renderCategoryFallback(category?: string): ReactNode {
  const fallbackId =
    category === "Mặt cầu"
      ? "cau-cat-mat-phang"
      : category === "Hình trụ"
        ? "tru-thiet-dien-tron"
        : category === "Hình nón"
          ? "non-thiet-dien-truc"
          : "thiet-dien-chop";
  const node = getCachedSampleThumbnailNode(fallbackId);
  return (
    <svg viewBox="0 0 180 110" data-thumb-fallback="true" aria-hidden="true">
      {node}
    </svg>
  );
}

export function SamplePreview({
  sampleId,
  category,
  scene3d,
}: {
  kind?: PreviewKind;
  sampleId?: string | null;
  category?: string;
  scene3d?: Scene3D | null;
}) {
  if (scene3d) {
    return (
      <svg
        viewBox="0 0 180 110"
        data-thumb-id={sampleId ?? "custom-scene3d"}
        data-thumb-fallback="false"
        aria-hidden="true"
      >
        {buildScene3DThumbnailNode(scene3d)}
      </svg>
    );
  }
  if (sampleId) {
    const node = getCachedSampleThumbnailNode(sampleId);
    if (node) {
      return (
        <svg
          viewBox="0 0 180 110"
          data-thumb-id={sampleId}
          data-thumb-fallback="false"
          aria-hidden="true"
        >
          {node}
        </svg>
      );
    }
  }
  return renderCategoryFallback(category);
}
