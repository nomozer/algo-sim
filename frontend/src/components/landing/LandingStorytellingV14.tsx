import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { AnnotatedPhrase } from "./AnnotatedHeading";
import { separateLabelPositions } from "./LandingHeroScene3D";
import {
  computeBoundedPlaneQuad,
  LANDING_PRISM_STORY_SPEC,
  type Vec3Tuple,
} from "./landing-geometry-data";

export interface StoryStageV14Spec {
  readonly index: number;
  readonly shortNum: string;
  readonly desktopTag: string;
  readonly mobileShortTag: string;
  readonly chapterHeading: string;
  readonly title: string;
  readonly summary: string;
  readonly relationNote: string;
  readonly camera: {
    readonly yaw: number;
    readonly pitch: number;
    readonly zoom: number;
    readonly extrude: number;
    readonly prismBuild: number;
    readonly planeSweep: number;
    readonly parallelCue: number;
    readonly traceProgress: number;
    readonly sectionFill: number;
  };
}

export const STORY_STAGES_V14: readonly StoryStageV14Spec[] = [
  {
    index: 0,
    shortNum: "1",
    desktopTag: "Từ đề bài",
    mobileShortTag: "Đề bài",
    chapterHeading: "Chặng 1: Từ đề bài",
    title: "Ghim giả thiết cạnh a = 4 và ba điểm M, N, P",
    summary:
      "Từ đề bài lăng trụ tam giác đều ABC.A′B′C′ tất cả các cạnh bằng 4, Axo dựng nền khối không gian và đặt ba trung điểm gốc M ∈ AB, N ∈ AC, P ∈ CC′.",
    relationNote: "Giả thiết gốc: ABC.A′B′C′ đều cạnh a = 4 · Trung điểm M, N, P",
    camera: {
      yaw: -0.28,
      pitch: 0.31,
      zoom: 1,
      extrude: 1,
      prismBuild: 0.18,
      planeSweep: 0,
      parallelCue: 0,
      traceProgress: 0,
      sectionFill: 0,
    },
  },
  {
    index: 1,
    shortNum: "2",
    desktopTag: "Dựng không gian",
    mobileShortTag: "Dựng hình",
    chapterHeading: "Chặng 2: Dựng không gian",
    title: "Dựng mặt phẳng cắt (MNP) qua lòng khối lăng trụ",
    summary:
      "Khối lăng trụ đứng hoàn chỉnh hiện lên cùng mặt phẳng cắt (MNP), nối hai giao tuyến xuất phát MN trên đáy và NP trên mặt bên (ACC′A′).",
    relationNote: "Cấu trúc không gian: (MNP) cắt (ABC) theo MN và cắt (ACC′A′) theo NP",
    camera: {
      yaw: -0.19,
      pitch: 0.32,
      zoom: 1,
      extrude: 1,
      prismBuild: 1,
      planeSweep: 1,
      parallelCue: 0,
      traceProgress: 0.5,
      sectionFill: 0,
    },
  },
  {
    index: 2,
    shortNum: "3",
    desktopTag: "Xác lập quan hệ",
    mobileShortTag: "Quan hệ",
    chapterHeading: "Chặng 3: Xác lập quan hệ",
    title: "Truyền quan hệ song song MN ∥ BC để tìm Q ∈ BB′",
    summary:
      "Đường trung bình MN song song với cạnh đáy BC trong (ABC). Vì BC nằm trong mặt bên (BCC′B′), giao tuyến qua P phải song song BC và cắt cạnh BB′ đúng tại Q.",
    relationNote: "Quan hệ song song: MN ∥ BC ⇒ PQ ∥ BC · Khóa điểm Q ∈ BB′",
    camera: {
      yaw: -0.09,
      pitch: 0.34,
      zoom: 1,
      extrude: 1,
      prismBuild: 1,
      planeSweep: 1,
      parallelCue: 1,
      traceProgress: 0.78,
      sectionFill: 0.08,
    },
  },
  {
    index: 3,
    shortNum: "4",
    desktopTag: "Kết quả",
    mobileShortTag: "Kết quả",
    chapterHeading: "Chặng 4: Hoàn thiện thiết diện",
    title: "Khép kín thiết diện hình thang cân MNPQ",
    summary:
      "Đoạn QM khép kín bốn cạnh trên mặt phẳng cắt (MNP), tạo thành thiết diện hình thang cân đối xứng sẵn sàng để kiểm chứng trực tiếp.",
    relationNote: "Thiết diện khép kín: Hình thang cân MNPQ thuộc mặt phẳng (MNP)",
    camera: {
      yaw: 0.02,
      pitch: 0.35,
      zoom: 1,
      extrude: 1,
      prismBuild: 1,
      planeSweep: 1,
      parallelCue: 0.45,
      traceProgress: 1,
      sectionFill: 1,
    },
  },
];

export interface StoryInterpolatedPose {
  readonly progress: number;
  readonly activeStageIndex: number;
  readonly yaw: number;
  readonly pitch: number;
  readonly zoom: number;
  readonly extrude: number;
  readonly prismBuild: number;
  readonly planeSweep: number;
  readonly parallelCue: number;
  readonly traceProgress: number;
  readonly sectionFill: number;
}

interface ProjectedPoint2D {
  readonly x: number;
  readonly y: number;
  readonly z: number;
}

function clamp01(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(1, value));
}

function smoothstep(edge0: number, edge1: number, x: number): number {
  const t = clamp01((x - edge0) / Math.max(1e-6, edge1 - edge0));
  return t * t * (3 - 2 * t);
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

export interface StoryChapterEnvelope {
  readonly opacity: number;
  readonly offsetY: number;
  readonly isVisible: boolean;
}

export function computeStoryScrollProgress(
  runwayTop: number,
  runwayHeight: number,
  stickyHeight: number,
): number {
  const travel = Math.max(1, runwayHeight - stickyHeight);
  return clamp01(-runwayTop / travel);
}

export function stageIndexFromProgress(progress: number): number {
  const p = clamp01(progress);
  if (p < 0.25) return 0;
  if (p < 0.5) return 1;
  if (p < 0.75) return 2;
  return 3;
}

/**
 * Guarantees strictly 1 active visible chapter across all p in [0, 1]:
 * zero blank deadband and zero simultaneous overlapping text.
 */
export function computeChapterEnvelope(
  progress: number,
  index: number,
  reducedMotion = false,
): StoryChapterEnvelope {
  if (reducedMotion) {
    return { opacity: 1, offsetY: 0, isVisible: true };
  }
  const p = clamp01(progress);
  const w = 0.038;

  if (index === 0) {
    if (p >= 0.25) return { opacity: 0, offsetY: -14, isVisible: false };
    if (p > 0.25 - w) {
      const u = smoothstep(0.25 - w, 0.25, p);
      return { opacity: 1 - 0.62 * u, offsetY: -14 * u, isVisible: true };
    }
    return { opacity: 1, offsetY: 0, isVisible: true };
  }

  if (index === 1) {
    if (p < 0.25) return { opacity: 0, offsetY: 14, isVisible: false };
    if (p >= 0.5) return { opacity: 0, offsetY: -14, isVisible: false };
    if (p < 0.25 + w) {
      const u = smoothstep(0.25, 0.25 + w, p);
      return { opacity: 0.38 + 0.62 * u, offsetY: 14 * (1 - u), isVisible: true };
    }
    if (p > 0.5 - w) {
      const u = smoothstep(0.5 - w, 0.5, p);
      return { opacity: 1 - 0.62 * u, offsetY: -14 * u, isVisible: true };
    }
    return { opacity: 1, offsetY: 0, isVisible: true };
  }

  if (index === 2) {
    if (p < 0.5) return { opacity: 0, offsetY: 14, isVisible: false };
    if (p >= 0.75) return { opacity: 0, offsetY: -14, isVisible: false };
    if (p < 0.5 + w) {
      const u = smoothstep(0.5, 0.5 + w, p);
      return { opacity: 0.38 + 0.62 * u, offsetY: 14 * (1 - u), isVisible: true };
    }
    if (p > 0.75 - w) {
      const u = smoothstep(0.75 - w, 0.75, p);
      return { opacity: 1 - 0.62 * u, offsetY: -14 * u, isVisible: true };
    }
    return { opacity: 1, offsetY: 0, isVisible: true };
  }

  if (index === 3) {
    if (p < 0.75) return { opacity: 0, offsetY: 14, isVisible: false };
    if (p < 0.75 + w) {
      const u = smoothstep(0.75, 0.75 + w, p);
      return { opacity: 0.38 + 0.62 * u, offsetY: 14 * (1 - u), isVisible: true };
    }
    return { opacity: 1, offsetY: 0, isVisible: true };
  }

  return { opacity: 0, offsetY: 0, isVisible: false };
}

export function interpolateStoryPose(
  progress: number,
  reducedMotion = false,
): StoryInterpolatedPose {
  const p = clamp01(progress);
  const activeStageIndex = stageIndexFromProgress(p);

  if (reducedMotion) {
    const cam = STORY_STAGES_V14[activeStageIndex].camera;
    return {
      progress: p,
      activeStageIndex,
      ...cam,
    };
  }

  // Piecewise smooth keyframes aligned cleanly with chapter beats
  const k = [0.1, 0.38, 0.65, 0.9] as const;
  let s0 = STORY_STAGES_V14[0].camera;
  let s1 = STORY_STAGES_V14[0].camera;
  let u = 0;

  if (p <= k[0]) {
    return { progress: p, activeStageIndex, ...s0 };
  }
  if (p <= k[1]) {
    s0 = STORY_STAGES_V14[0].camera;
    s1 = STORY_STAGES_V14[1].camera;
    u = smoothstep(k[0], k[1], p);
  } else if (p <= k[2]) {
    s0 = STORY_STAGES_V14[1].camera;
    s1 = STORY_STAGES_V14[2].camera;
    u = smoothstep(k[1], k[2], p);
  } else {
    s0 = STORY_STAGES_V14[2].camera;
    s1 = STORY_STAGES_V14[3].camera;
    u = smoothstep(k[2], k[3], p);
  }

  return {
    progress: p,
    activeStageIndex,
    yaw: lerp(s0.yaw, s1.yaw, u),
    pitch: lerp(s0.pitch, s1.pitch, u),
    zoom: lerp(s0.zoom, s1.zoom, u),
    extrude: lerp(s0.extrude, s1.extrude, u),
    prismBuild: lerp(s0.prismBuild, s1.prismBuild, u),
    planeSweep: lerp(s0.planeSweep, s1.planeSweep, u),
    parallelCue: lerp(s0.parallelCue, s1.parallelCue, u),
    traceProgress: lerp(s0.traceProgress, s1.traceProgress, u),
    sectionFill: lerp(s0.sectionFill, s1.sectionFill, u),
  };
}

function rotatePointViewSpace(
  pt: Vec3Tuple,
  yaw: number,
  pitch: number,
): Vec3Tuple {
  const cosY = Math.cos(yaw);
  const sinY = Math.sin(yaw);
  const x1 = pt[0] * cosY - pt[2] * sinY;
  const z1 = pt[0] * sinY + pt[2] * cosY;

  const cosP = Math.cos(pitch);
  const sinP = Math.sin(pitch);
  const y2 = pt[1] * cosP - z1 * sinP;
  const z2 = pt[1] * sinP + z1 * cosP;
  return [x1, y2, z2];
}

export function projectPrismPoint3D(
  pt: Vec3Tuple,
  yaw: number,
  pitch: number,
  cx: number,
  cy: number,
  scale: number,
): ProjectedPoint2D {
  const [x1, y2, z2] = rotatePointViewSpace(pt, yaw, pitch);
  const camDist = 11.5;
  const persp = camDist / Math.max(3, camDist - z2);
  return {
    x: cx + x1 * scale * persp,
    y: cy - y2 * scale * persp,
    z: z2,
  };
}

function isFaceFrontFacing(
  facePts: readonly Vec3Tuple[],
  solidCenter: Vec3Tuple,
  yaw: number,
  pitch: number,
): boolean {
  if (facePts.length < 3) return false;
  const v0 = rotatePointViewSpace(facePts[0], yaw, pitch);
  const v1 = rotatePointViewSpace(facePts[1], yaw, pitch);
  const v2 = rotatePointViewSpace(facePts[2], yaw, pitch);
  const vc = rotatePointViewSpace(solidCenter, yaw, pitch);

  const ax = v1[0] - v0[0];
  const ay = v1[1] - v0[1];
  const az = v1[2] - v0[2];
  const bx = v2[0] - v0[0];
  const by = v2[1] - v0[1];
  const bz = v2[2] - v0[2];

  let nx = ay * bz - az * by;
  let ny = az * bx - ax * bz;
  let nz = ax * by - ay * bx;

  const inX = vc[0] - v0[0];
  const inY = vc[1] - v0[1];
  const inZ = vc[2] - v0[2];
  if (nx * inX + ny * inY + nz * inZ > 0) {
    nx = -nx;
    ny = -ny;
    nz = -nz;
  }

  const viewX = -v0[0];
  const viewY = -v0[1];
  const viewZ = 11.5 - v0[2];
  return nx * viewX + ny * viewY + nz * viewZ > 0.02;
}

const STORY_SVG_W = 640;
const STORY_SVG_H = 470;
const STORY_PLANE_QUAD = computeBoundedPlaneQuad(
  LANDING_PRISM_STORY_SPEC.sectionLoop.map(
    (id) => LANDING_PRISM_STORY_SPEC.pointMap[id].pos,
  ),
  [Math.sqrt(3), -Math.sqrt(3), -1],
  0.34,
);

function PrismEditorialStage({
  pose,
  reducedMotion,
}: {
  readonly pose: StoryInterpolatedPose;
  readonly reducedMotion: boolean;
}) {
  const activeStage =
    STORY_STAGES_V14[pose.activeStageIndex] ?? STORY_STAGES_V14[0];

  const scene = useMemo(() => {
    const pMap = LANDING_PRISM_STORY_SPEC.pointMap;
    const baseY = pMap["A"].pos[1];
    const extrudeVec = (id: string): Vec3Tuple => {
      const p = pMap[id].pos;
      if (id === "A" || id === "B" || id === "C" || id === "M" || id === "N") {
        return p;
      }
      return [p[0], baseY + (p[1] - baseY) * pose.extrude, p[2]];
    };

    const coords: Record<string, Vec3Tuple> = {};
    for (const key of [
      "A",
      "B",
      "C",
      "A_prime",
      "B_prime",
      "C_prime",
      "M",
      "N",
      "P",
      "Q",
    ]) {
      coords[key] = extrudeVec(key);
    }

    const scale = 64 * pose.zoom;
    const cx = STORY_SVG_W * 0.5;
    const cy = 226;
    const proj: Record<string, ProjectedPoint2D> = {};
    for (const [k, v] of Object.entries(coords)) {
      proj[k] = projectPrismPoint3D(v, pose.yaw, pose.pitch, cx, cy, scale);
    }

    const solidCenter: Vec3Tuple = [
      (coords["A"][0] +
        coords["B"][0] +
        coords["C"][0] +
        coords["A_prime"][0] +
        coords["B_prime"][0] +
        coords["C_prime"][0]) /
        6,
      (coords["A"][1] +
        coords["B"][1] +
        coords["C"][1] +
        coords["A_prime"][1] +
        coords["B_prime"][1] +
        coords["C_prime"][1]) /
        6,
      (coords["A"][2] +
        coords["B"][2] +
        coords["C"][2] +
        coords["A_prime"][2] +
        coords["B_prime"][2] +
        coords["C_prime"][2]) /
        6,
    ];

    const faceDefs: readonly (readonly string[])[] = [
      ["A", "C", "B"],
      ["A_prime", "B_prime", "C_prime"],
      ["A", "B", "B_prime", "A_prime"],
      ["B", "C", "C_prime", "B_prime"],
      ["C", "A", "A_prime", "C_prime"],
    ];

    const faceFrontMap = faceDefs.map((f) =>
      isFaceFrontFacing(
        f.map((id) => coords[id]),
        solidCenter,
        pose.yaw,
        pose.pitch,
      ),
    );

    const edgeVisibleInSolid = (from: string, to: string): boolean => {
      let frontTouch = 0;
      for (let i = 0; i < faceDefs.length; i++) {
        if (!faceFrontMap[i]) continue;
        const f = faceDefs[i];
        if (f.includes(from) && f.includes(to)) frontTouch++;
      }
      return frontTouch >= 1;
    };

    const centroidX =
      (proj["A"].x +
        proj["B"].x +
        proj["C"].x +
        proj["A_prime"].x +
        proj["B_prime"].x +
        proj["C_prime"].x) /
      6;
    const centroidY =
      (proj["A"].y +
        proj["B"].y +
        proj["C"].y +
        proj["A_prime"].y +
        proj["B_prime"].y +
        proj["C_prime"].y) /
      6;

    const prismWeight = 0.18 + 0.82 * pose.prismBuild;
    const edges = LANDING_PRISM_STORY_SPEC.solidEdges.map((edge) => {
      const a = proj[edge.from];
      const b = proj[edge.to];
      const isTop = edge.from.includes("prime") && edge.to.includes("prime");
      const isUpperStructure =
        edge.from.includes("prime") || edge.to.includes("prime");
      const isNonParticipating =
        isTop || (edge.from === "A" && edge.to === "A_prime");
      let opacity = 0.88;
      if (isUpperStructure) {
        opacity *= prismWeight;
      }
      if (isNonParticipating && pose.parallelCue > 0.02) {
        opacity *= 1 - 0.36 * pose.parallelCue;
      }
      const front = edgeVisibleInSolid(edge.from, edge.to);
      return {
        key: `${edge.from}-${edge.to}`,
        a,
        b,
        dashed: !front,
        opacity,
      };
    });

    // Perpendicular right-angle witness at A (AA' perp AB)
    const pA = coords["A"];
    const pB = coords["B"];
    const pAp = coords["A_prime"];
    const uAB: Vec3Tuple = [pB[0] - pA[0], pB[1] - pA[1], pB[2] - pA[2]];
    const uAAp: Vec3Tuple = [pAp[0] - pA[0], pAp[1] - pA[1], pAp[2] - pA[2]];
    const lenAB = Math.hypot(...uAB) || 1;
    const lenAAp = Math.hypot(...uAAp) || 1;
    const raSize = 0.36;
    const b1: Vec3Tuple = [
      pA[0] + (uAB[0] / lenAB) * raSize,
      pA[1] + (uAB[1] / lenAB) * raSize,
      pA[2] + (uAB[2] / lenAB) * raSize,
    ];
    const b2: Vec3Tuple = [
      pA[0] + (uAAp[0] / lenAAp) * raSize,
      pA[1] + (uAAp[1] / lenAAp) * raSize,
      pA[2] + (uAAp[2] / lenAAp) * raSize,
    ];
    const bc: Vec3Tuple = [
      b1[0] + (uAAp[0] / lenAAp) * raSize,
      b1[1] + (uAAp[1] / lenAAp) * raSize,
      b1[2] + (uAAp[2] / lenAAp) * raSize,
    ];
    const raB1 = projectPrismPoint3D(b1, pose.yaw, pose.pitch, cx, cy, scale);
    const raB2 = projectPrismPoint3D(b2, pose.yaw, pose.pitch, cx, cy, scale);
    const raC = projectPrismPoint3D(bc, pose.yaw, pose.pitch, cx, cy, scale);

    // Midpoint witness ticks for given midpoints M in AB, N in AC, P in CC', Q in BB'
    const makeTickSegment = (ptId: string, aId: string, bId: string) => {
      const pm = proj[ptId];
      const pa = proj[aId];
      const pb = proj[bId];
      const dx = pb.x - pa.x;
      const dy = pb.y - pa.y;
      const len = Math.hypot(dx, dy) || 1;
      const nx = -dy / len;
      const ny = dx / len;
      const r = 4.6;
      return {
        key: `tick-${ptId}`,
        x1: pm.x - nx * r,
        y1: pm.y - ny * r,
        x2: pm.x + nx * r,
        y2: pm.y + ny * r,
      };
    };
    const midpointTicks = [
      makeTickSegment("M", "A", "B"),
      makeTickSegment("N", "A", "C"),
      makeTickSegment("P", "C", "C_prime"),
    ];

    const liftY = (1 - pose.planeSweep) * 0.62;
    const planePolyPts = STORY_PLANE_QUAD.map((q) =>
      projectPrismPoint3D(
        [q[0], q[1] + liftY, q[2]],
        pose.yaw,
        pose.pitch,
        cx,
        cy,
        scale,
      ),
    );

    const fmt = (pts: readonly ProjectedPoint2D[]) =>
      pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");

    const loopIds = ["M", "N", "P", "Q"] as const;
    const tracedEdges = loopIds.map((id, idx) => {
      const nextId = loopIds[(idx + 1) % loopIds.length];
      const u = clamp01(pose.traceProgress * loopIds.length - idx);
      const p0 = proj[id];
      const p1 = proj[nextId];
      return {
        key: `${id}-${nextId}`,
        x1: p0.x,
        y1: p0.y,
        x2: lerp(p0.x, p1.x, u),
        y2: lerp(p0.y, p1.y, u),
        u,
      };
    });

    const visibleIds = [
      "A",
      "B",
      "C",
      "A_prime",
      "B_prime",
      "C_prime",
      "M",
      "N",
      "P",
      "Q",
    ].filter((id) => {
      if (id === "Q") {
        return pose.activeStageIndex >= 2 && (pose.parallelCue > 0.25 || pose.traceProgress > 0.56);
      }
      return true;
    });

    const labelCandidates = visibleIds.map((id) => {
      const pt = proj[id];
      const dx = pt.x - centroidX;
      const dy = pt.y - centroidY;
      const len = Math.max(1, Math.hypot(dx, dy));
      const pad = id === "C" ? 16 : 19;
      return {
        id,
        x: pt.x + (dx / len) * pad,
        y: pt.y + (dy / len) * pad + 4,
      };
    });
    separateLabelPositions(
      labelCandidates,
      STORY_SVG_W,
      STORY_SVG_H,
      28,
      28,
      28,
      30,
    );

    const labels = visibleIds.map((id, i) => ({
      id,
      label: pMap[id].label,
      role: pMap[id].role,
      px: proj[id].x,
      py: proj[id].y,
      lx: labelCandidates[i].x,
      ly: labelCandidates[i].y,
      opacity: id.includes("prime") ? prismWeight : 1,
    }));

    const frontLateralPolys = faceDefs
      .slice(2)
      .map((f, idx) => ({
        pts: fmt(f.map((id) => proj[id])),
        front: faceFrontMap[idx + 2],
        toneClass:
          idx === 0
            ? "axo-v14-svg-prism-face-lit"
            : "axo-v14-svg-prism-face-shade",
      }))
      .filter((item) => item.front);

    const haloCy = Math.min(432, (proj["A"].y + proj["B"].y + proj["C"].y) / 3 + 26);

    return {
      proj,
      prismWeight,
      edges,
      frontLateralPolys,
      midpointTicks,
      haloCy,
      rightAnglePath: `M ${raB1.x.toFixed(1)} ${raB1.y.toFixed(1)} L ${raC.x.toFixed(1)} ${raC.y.toFixed(1)} L ${raB2.x.toFixed(1)} ${raB2.y.toFixed(1)}`,
      basePts: fmt([proj["A"], proj["B"], proj["C"]]),
      topPts: fmt([proj["A_prime"], proj["B_prime"], proj["C_prime"]]),
      planePts: fmt(planePolyPts),
      sectionPts: fmt([proj["M"], proj["N"], proj["P"], proj["Q"]]),
      tracedEdges,
      labels,
    };
  }, [pose]);

  return (
    <div className="axo-v14-story-stage-pin">
      <div
        id="landing-storytelling-scene"
        className="axo-v14-story-stage"
        data-story-stage={pose.activeStageIndex}
        data-story-progress={pose.progress.toFixed(3)}
        data-reduced-motion={reducedMotion ? "true" : "false"}
      >
        <div className="axo-v14-story-stage-meta">
          <span className="axo-v14-story-stage-counter">
            Chặng {pose.activeStageIndex + 1} / {STORY_STAGES_V14.length} ·{" "}
            {activeStage.desktopTag}
          </span>
          <div className="axo-v14-story-progress-track" aria-hidden="true">
            <div
              className="axo-v14-story-progress-fill"
              style={{
                transform: `scaleX(${Math.max(0.06, pose.progress).toFixed(4)})`,
              }}
            />
          </div>
        </div>

        <svg
          className="axo-v14-story-svg"
          viewBox={`0 0 ${STORY_SVG_W} ${STORY_SVG_H}`}
          role="img"
          aria-label={`Lăng trụ tam giác đều ABC.A′B′C′: ${activeStage.chapterHeading}`}
        >
          <ellipse
            className="axo-v14-svg-contact-halo"
            cx={STORY_SVG_W * 0.5}
            cy={scene.haloCy.toFixed(1)}
            rx="168"
            ry="22"
          />

          <polygon className="axo-v14-svg-prism-base" points={scene.basePts} />

          {scene.frontLateralPolys.map((face, idx) => (
            <polygon
              key={`lat-${idx}`}
              className={`axo-v14-svg-prism-face ${face.toneClass}`}
              points={face.pts}
              fillOpacity={(0.52 * scene.prismWeight).toFixed(3)}
            />
          ))}

          <polygon
            className="axo-v14-svg-prism-top"
            points={scene.topPts}
            fillOpacity={(0.18 * scene.prismWeight).toFixed(3)}
            strokeOpacity={scene.prismWeight.toFixed(3)}
          />

          {scene.edges.map((edge) => (
            <line
              key={edge.key}
              className={
                edge.dashed
                  ? "axo-v14-svg-prism-edge-back"
                  : "axo-v14-svg-prism-edge-front"
              }
              x1={edge.a.x}
              y1={edge.a.y}
              x2={edge.b.x}
              y2={edge.b.y}
              strokeOpacity={
                edge.dashed
                  ? (edge.opacity * 0.56).toFixed(3)
                  : edge.opacity.toFixed(3)
              }
            />
          ))}

          <path
            className="axo-v14-svg-edge-altitude"
            d={scene.rightAnglePath}
            fill="none"
            opacity={(0.88 * scene.prismWeight).toFixed(3)}
          />

          {scene.midpointTicks.map((tick) => (
            <line
              key={tick.key}
              className="axo-v14-svg-midpoint-tick"
              x1={tick.x1.toFixed(1)}
              y1={tick.y1.toFixed(1)}
              x2={tick.x2.toFixed(1)}
              y2={tick.y2.toFixed(1)}
            />
          ))}

          {pose.parallelCue > 0.04 && (
            <g opacity={pose.parallelCue.toFixed(3)}>
              <line
                className="axo-v14-svg-parallel-guide"
                x1={scene.proj["B"].x}
                y1={scene.proj["B"].y}
                x2={scene.proj["C"].x}
                y2={scene.proj["C"].y}
              />
              <line
                className="axo-v14-svg-parallel-guide"
                x1={scene.proj["M"].x}
                y1={scene.proj["M"].y}
                x2={scene.proj["N"].x}
                y2={scene.proj["N"].y}
              />
              {pose.planeSweep > 0.45 && (
                <line
                  className="axo-v14-svg-parallel-guide"
                  x1={scene.proj["P"].x}
                  y1={scene.proj["P"].y}
                  x2={scene.proj["Q"].x}
                  y2={scene.proj["Q"].y}
                />
              )}
            </g>
          )}

          {pose.planeSweep > 0.02 && (
            <polygon
              className="axo-v14-svg-cutting-plane"
              points={scene.planePts}
              fillOpacity={(0.22 * pose.planeSweep).toFixed(3)}
              strokeOpacity={(0.76 * pose.planeSweep).toFixed(3)}
            />
          )}

          {pose.sectionFill > 0.02 && (
            <polygon
              className="axo-v14-svg-section-poly"
              points={scene.sectionPts}
              fillOpacity={(0.28 * pose.sectionFill).toFixed(3)}
              strokeOpacity={Math.min(0.92, pose.sectionFill).toFixed(3)}
            />
          )}

          {scene.tracedEdges.map((seg) =>
            seg.u > 0.01 ? (
              <line
                key={seg.key}
                className="axo-v14-svg-section-trace"
                x1={seg.x1}
                y1={seg.y1}
                x2={seg.x2}
                y2={seg.y2}
                strokeOpacity={Math.min(0.96, 0.45 + 0.51 * seg.u).toFixed(3)}
              />
            ) : null,
          )}

          {scene.labels.map((item) => {
            const isSeed = item.role === "seed";
            const isInter = item.role === "intersection";
            const dotClass = isInter
              ? "axo-v14-svg-section-dot"
              : isSeed
                ? "axo-v14-svg-seed-dot"
                : "axo-v14-svg-vertex-dot";
            const textClass = isInter
              ? "axo-v14-svg-label-inter"
              : isSeed
                ? "axo-v14-svg-label-seed"
                : "axo-v14-svg-vertex-text";
            return (
              <g key={item.id} opacity={item.opacity.toFixed(3)}>
                <circle
                  className={dotClass}
                  cx={item.px}
                  cy={item.py}
                  r={isInter ? 4.6 : isSeed ? 4.1 : 3.0}
                />
                <text className={textClass} x={item.lx} y={item.ly}>
                  {item.label}
                </text>
              </g>
            );
          })}
        </svg>

        <div className="axo-v14-story-stage-readout" aria-live="polite">
          <span className="axo-v14-story-relation-text">
            {activeStage.relationNote}
          </span>
        </div>
      </div>
    </div>
  );
}

function readStoryProgressOverride(): number | null {
  if (typeof window === "undefined") return null;
  const val = new URLSearchParams(window.location.search).get("story_progress");
  if (val === null) return null;
  const parsed = Number(val);
  return Number.isFinite(parsed) ? clamp01(parsed) : null;
}

export function LandingStorytellingV14() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const runwayRef = useRef<HTMLDivElement | null>(null);
  const stickyRef = useRef<HTMLDivElement | null>(null);
  const targetProgressRef = useRef<number>(readStoryProgressOverride() ?? 0);
  const currentProgressRef = useRef<number>(targetProgressRef.current);
  const reducedMotionRef = useRef<boolean>(false);

  const [reducedMotion, setReducedMotion] = useState<boolean>(false);
  const [scrollProgress, setScrollProgress] = useState<number>(
    () => targetProgressRef.current,
  );

  useEffect(() => {
    if (typeof window === "undefined") return;

    const mq = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    const initialReduced = Boolean(mq?.matches);
    reducedMotionRef.current = initialReduced;
    setReducedMotion(initialReduced);

    const override = readStoryProgressOverride();
    if (override !== null) {
      targetProgressRef.current = override;
      currentProgressRef.current = override;
      setScrollProgress(override);
    }

    let rafId = 0;

    const tick = () => {
      rafId = 0;
      if (readStoryProgressOverride() !== null || document.hidden) return;
      const target = targetProgressRef.current;
      const cur = currentProgressRef.current;
      const diff = target - cur;
      if (reducedMotionRef.current || Math.abs(diff) < 0.0012) {
        if (cur !== target) {
          currentProgressRef.current = target;
          setScrollProgress(target);
        }
        return;
      }
      const next = cur + diff * 0.34;
      currentProgressRef.current = next;
      setScrollProgress(next);
      rafId = window.requestAnimationFrame(tick);
    };

    const syncTarget = (immediate = false) => {
      if (readStoryProgressOverride() !== null) return;
      const runwayEl = runwayRef.current;
      const stickyEl = stickyRef.current;
      if (!runwayEl || !stickyEl) return;
      const runwayRect = runwayEl.getBoundingClientRect();
      const stickyRect = stickyEl.getBoundingClientRect();
      const nextTarget = computeStoryScrollProgress(
        runwayRect.top,
        runwayRect.height,
        stickyRect.height,
      );
      targetProgressRef.current = nextTarget;
      if (
        immediate ||
        reducedMotionRef.current ||
        Math.abs(nextTarget - currentProgressRef.current) > 0.2
      ) {
        currentProgressRef.current = nextTarget;
        setScrollProgress(nextTarget);
        return;
      }
      if (!document.hidden && rafId === 0 && Math.abs(nextTarget - currentProgressRef.current) >= 0.0012) {
        rafId = window.requestAnimationFrame(tick);
      }
    };

    const handleScrollOrResize = () => syncTarget(false);

    const onMotionChange = (ev: MediaQueryListEvent) => {
      reducedMotionRef.current = ev.matches;
      setReducedMotion(ev.matches);
      syncTarget(true);
    };

    const onVisibility = () => {
      if (!document.hidden) syncTarget(false);
      else if (rafId !== 0) {
        window.cancelAnimationFrame(rafId);
        rafId = 0;
      }
    };

    if (override === null) {
      syncTarget(true);
    }
    window.addEventListener("scroll", handleScrollOrResize, { passive: true });
    window.addEventListener("resize", handleScrollOrResize, { passive: true });
    document.addEventListener("visibilitychange", onVisibility);
    mq?.addEventListener?.("change", onMotionChange);

    const ro =
      typeof ResizeObserver !== "undefined" && runwayRef.current
        ? new ResizeObserver(handleScrollOrResize)
        : null;
    if (runwayRef.current) ro?.observe(runwayRef.current);
    if (stickyRef.current) ro?.observe(stickyRef.current);

    return () => {
      if (rafId !== 0) window.cancelAnimationFrame(rafId);
      window.removeEventListener("scroll", handleScrollOrResize);
      window.removeEventListener("resize", handleScrollOrResize);
      document.removeEventListener("visibilitychange", onVisibility);
      mq?.removeEventListener?.("change", onMotionChange);
      ro?.disconnect();
    };
  }, []);

  const pose = useMemo(
    () => interpolateStoryPose(scrollProgress, reducedMotion),
    [scrollProgress, reducedMotion],
  );

  return (
    <section
      id="cach-hoat-dong"
      ref={sectionRef}
      className="axo-v14-story"
      aria-labelledby="landing-story-heading"
    >
      <div className="axo-v14-story-shell">
        <div className="axo-v14-story-header">
          <h2 id="landing-story-heading" className="axo-v14-story-title">
            Theo dõi bài toán qua{" "}
            <AnnotatedPhrase variant="underline">
              từng lớp không gian
            </AnnotatedPhrase>
            .
          </h2>
          <p className="axo-v14-story-lead">
            Cuộn xuống để quan sát mạch dựng liên tục trên lăng trụ tam giác đều
            ABC.A′B′C′ cạnh a = 4: từ ba trung điểm gốc M, N, P đến thiết diện
            hoàn chỉnh.
          </p>
        </div>

        <div ref={runwayRef} className="axo-v14-story-runway">
          <div ref={stickyRef} className="axo-v14-story-sticky">
            <div className="axo-v14-story-track">
              <PrismEditorialStage pose={pose} reducedMotion={reducedMotion} />

              <div className="axo-v14-story-narrative">
                <ol
                  className="axo-v14-story-chapters"
                  aria-label="Các chặng dựng hình theo cuộn trang"
                >
                  {STORY_STAGES_V14.map((stage, idx) => {
                    const env = computeChapterEnvelope(
                      pose.progress,
                      idx,
                      reducedMotion,
                    );
                    const isActive = reducedMotion
                      ? true
                      : idx === pose.activeStageIndex;
                    return (
                      <li
                        key={stage.shortNum}
                        data-story-chapter={idx}
                        data-active={isActive ? "true" : "false"}
                        data-chapter-visible={env.isVisible ? "true" : "false"}
                        className={
                          isActive
                            ? "axo-v14-story-chapter is-active"
                            : "axo-v14-story-chapter"
                        }
                        style={
                          reducedMotion
                            ? undefined
                            : {
                                opacity: env.opacity.toFixed(3),
                                transform: `translate3d(0, ${env.offsetY.toFixed(1)}px, 0)`,
                                visibility: env.isVisible ? "visible" : "hidden",
                                pointerEvents: env.isVisible ? "auto" : "none",
                              }
                        }
                      >
                        <div className="axo-v14-story-chapter-index">
                          {stage.chapterHeading}
                        </div>
                        <h3 className="axo-v14-story-chapter-title">{stage.title}</h3>
                        <p className="axo-v14-story-chapter-summary">
                          {stage.summary}
                        </p>
                      </li>
                    );
                  })}
                </ol>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
