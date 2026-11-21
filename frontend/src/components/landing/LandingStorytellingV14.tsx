import {
  useCallback,
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
  readonly epistemicRole: string;
  readonly chapterHeading: string;
  readonly title: string;
  readonly summary: string;
  readonly relationNote: string;
  readonly establishedState: string;
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
    mobileShortTag: "Từ đề bài",
    epistemicRole: "Giả thiết",
    chapterHeading: "Chặng 1: Từ đề bài",
    title: "Khởi tạo lăng trụ đứng và ba điểm gốc",
    summary:
      "Trên lăng trụ tam giác đều ABC.A′B′C′, hệ cố định ba trung điểm xuất phát M trên AB, N trên AC và P trên cạnh bên CC′.",
    relationNote: "Giả thiết: Lăng trụ đứng đáy đều ABC.A′B′C′ · Trung điểm M, N, P",
    establishedState: "ΔABC đều · AA′ ⊥ (ABC) · M ∈ AB, N ∈ AC, P ∈ CC′",
    camera: {
      yaw: -0.26,
      pitch: 0.27,
      zoom: 1,
      extrude: 1,
      prismBuild: 1,
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
    mobileShortTag: "Mặt cắt",
    epistemicRole: "Đối tượng đã dựng",
    chapterHeading: "Chặng 2: Dựng không gian",
    title: "Mở mặt phẳng cắt (MNP) qua lòng khối",
    summary:
      "Mặt phẳng qua ba điểm gốc cắt ngay mặt đáy theo đoạn MN và cắt mặt bên (ACC′A′) theo đoạn NP.",
    relationNote: "Đối tượng đã dựng: (MNP) cắt (ABC) theo MN và cắt (ACC′A′) theo NP",
    establishedState: "(MNP) ∩ (ABC) = MN · (MNP) ∩ (ACC′A′) = NP",
    camera: {
      yaw: -0.18,
      pitch: 0.28,
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
    mobileShortTag: "Song song",
    epistemicRole: "Quan hệ quan sát được",
    chapterHeading: "Chặng 3: Xác lập quan hệ",
    title: "Dẫn quan hệ song song để tìm giao điểm Q",
    summary:
      "Vì MN song song với BC trên mặt đáy, giao tuyến đi qua P trên mặt bên (BCC′B′) giữ phương song song với BC và cắt cạnh BB′ tại Q.",
    relationNote: "Quan hệ quan sát được: MN ∥ BC ⇒ PQ ∥ BC · Xác định Q ∈ BB′",
    establishedState: "MN ∥ BC ⇒ (MNP) ∩ (BCC′B′) = PQ ∥ BC · Q ∈ BB′",
    camera: {
      yaw: -0.09,
      pitch: 0.29,
      zoom: 1,
      extrude: 1,
      prismBuild: 1,
      planeSweep: 1,
      parallelCue: 1,
      traceProgress: 0.75,
      sectionFill: 0,
    },
  },
  {
    index: 3,
    shortNum: "4",
    desktopTag: "Kết quả",
    mobileShortTag: "Thiết diện",
    epistemicRole: "Kết quả xác lập",
    chapterHeading: "Chặng 4: Hoàn thiện thiết diện",
    title: "Khép kín thiết diện hình thang cân MNPQ",
    summary:
      "Đoạn QM nối kín bốn đỉnh đồng phẳng trên (MNP), tạo thành hình thang cân với hai đáy song song MN, PQ và hai cạnh bên bằng nhau.",
    relationNote: "Kết quả xác lập: Thiết diện phẳng hình thang cân MNPQ trên (MNP)",
    establishedState: "MNPQ đồng phẳng · MN ∥ PQ · NP = QM",
    camera: {
      yaw: -0.04,
      pitch: 0.29,
      zoom: 1,
      extrude: 1,
      prismBuild: 1,
      planeSweep: 1,
      parallelCue: 0.55,
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

/**
 * Maps rendered vertical centers of the 4 chapter cards relative to a viewport
 * reading focal line into [0, 1], guaranteeing threshold crossings at 0.25 / 0.50 / 0.75
 * at the exact midpoints between neighboring chapters.
 */
export function computeChapterScrollProgress(
  chapterCenters: readonly number[],
  focalY: number,
  lastChapterBottom?: number,
): number {
  if (chapterCenters.length < 4) return 0;
  const [c0, c1, c2, c3] = chapterCenters;

  if (focalY <= c0) {
    return lerp(0, 0.125, clamp01(1 - (c0 - focalY) / 180));
  }
  if (focalY <= c1) {
    return 0.125 + 0.25 * clamp01((focalY - c0) / Math.max(1, c1 - c0));
  }
  if (focalY <= c2) {
    return 0.375 + 0.25 * clamp01((focalY - c1) / Math.max(1, c2 - c1));
  }
  if (focalY <= c3) {
    return 0.625 + 0.25 * clamp01((focalY - c2) / Math.max(1, c3 - c2));
  }
  const tail = Math.max(110, ((lastChapterBottom ?? c3 + 120) - c3) * 0.8);
  return lerp(0.875, 1, clamp01((focalY - c3) / tail));
}

export function stageIndexFromProgress(progress: number): number {
  const p = clamp01(progress);
  if (p < 0.25) return 0;
  if (p < 0.5) return 1;
  if (p < 0.75) return 2;
  return 3;
}

/**
 * Guarantees strictly 1 active chapter across all p in [0, 1].
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
  const w = 0.028;

  if (index === 0) {
    if (p >= 0.25) return { opacity: 0, offsetY: -14, isVisible: false };
    if (p > 0.25 - w) {
      const u = smoothstep(0.25 - w, 0.25, p);
      return { opacity: 1 - 0.26 * u, offsetY: -14 * u, isVisible: true };
    }
    return { opacity: 1, offsetY: 0, isVisible: true };
  }

  if (index === 1) {
    if (p < 0.25) return { opacity: 0, offsetY: 14, isVisible: false };
    if (p >= 0.5) return { opacity: 0, offsetY: -14, isVisible: false };
    if (p < 0.25 + w) {
      const u = smoothstep(0.25, 0.25 + w, p);
      return { opacity: 0.74 + 0.26 * u, offsetY: 14 * (1 - u), isVisible: true };
    }
    if (p > 0.5 - w) {
      const u = smoothstep(0.5 - w, 0.5, p);
      return { opacity: 1 - 0.26 * u, offsetY: -14 * u, isVisible: true };
    }
    return { opacity: 1, offsetY: 0, isVisible: true };
  }

  if (index === 2) {
    if (p < 0.5) return { opacity: 0, offsetY: 14, isVisible: false };
    if (p >= 0.75) return { opacity: 0, offsetY: -14, isVisible: false };
    if (p < 0.5 + w) {
      const u = smoothstep(0.5, 0.5 + w, p);
      return { opacity: 0.74 + 0.26 * u, offsetY: 14 * (1 - u), isVisible: true };
    }
    if (p > 0.75 - w) {
      const u = smoothstep(0.75 - w, 0.75, p);
      return { opacity: 1 - 0.26 * u, offsetY: -14 * u, isVisible: true };
    }
    return { opacity: 1, offsetY: 0, isVisible: true };
  }

  if (index === 3) {
    if (p < 0.75) return { opacity: 0, offsetY: 14, isVisible: false };
    if (p < 0.75 + w) {
      const u = smoothstep(0.75, 0.75 + w, p);
      return { opacity: 0.74 + 0.26 * u, offsetY: 14 * (1 - u), isVisible: true };
    }
    return { opacity: 1, offsetY: 0, isVisible: true };
  }

  return { opacity: 0, offsetY: 0, isVisible: false };
}

/**
 * Stage-locked interpolation: strictly prevents geometric features (plane, Q,
 * parallel guides, final section fill) from leaking into earlier chapters.
 */
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

  const s0 = STORY_STAGES_V14[0].camera;
  const s1 = STORY_STAGES_V14[1].camera;
  const s2 = STORY_STAGES_V14[2].camera;
  const s3 = STORY_STAGES_V14[3].camera;

  if (p < 0.25) {
    return {
      progress: p,
      activeStageIndex,
      ...s0,
    };
  }

  if (p < 0.5) {
    const u1 = smoothstep(0.25, 0.37, p);
    return {
      progress: p,
      activeStageIndex,
      yaw: lerp(s0.yaw, s1.yaw, u1),
      pitch: lerp(s0.pitch, s1.pitch, u1),
      zoom: 1,
      extrude: 1,
      prismBuild: 1,
      planeSweep: u1,
      parallelCue: 0,
      traceProgress: 0.5 * smoothstep(0.28, 0.42, p),
      sectionFill: 0,
    };
  }

  if (p < 0.75) {
    const u2 = smoothstep(0.5, 0.62, p);
    return {
      progress: p,
      activeStageIndex,
      yaw: lerp(s1.yaw, s2.yaw, u2),
      pitch: lerp(s1.pitch, s2.pitch, u2),
      zoom: 1,
      extrude: 1,
      prismBuild: 1,
      planeSweep: 1,
      parallelCue: u2,
      traceProgress: lerp(0.5, 0.75, smoothstep(0.54, 0.66, p)),
      sectionFill: 0,
    };
  }

  const u3 = smoothstep(0.75, 0.87, p);
  return {
    progress: p,
    activeStageIndex,
    yaw: lerp(s2.yaw, s3.yaw, u3),
    pitch: lerp(s2.pitch, s3.pitch, u3),
    zoom: 1,
    extrude: 1,
    prismBuild: 1,
    planeSweep: 1,
    parallelCue: lerp(1, s3.parallelCue, u3),
    traceProgress: lerp(0.75, 1, smoothstep(0.75, 0.84, p)),
    sectionFill: smoothstep(0.78, 0.88, p),
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

const STORY_SVG_W = 700;
const STORY_SVG_H = 480;
const PRISM_HEIGHT_SCALE = 1.16;

const STORY_POINT_KEYS = [
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
] as const;

function scaleStoryHeight(pt: Vec3Tuple, baseY: number, factor = PRISM_HEIGHT_SCALE): Vec3Tuple {
  return [pt[0], baseY + (pt[1] - baseY) * factor, pt[2]];
}

function buildDoubleTickD(a: ProjectedPoint2D, b: ProjectedPoint2D): string {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const len = Math.hypot(dx, dy) || 1;
  const ux = dx / len;
  const uy = dy / len;
  const nx = (-dy / len) * 4.2;
  const ny = (dx / len) * 4.2;
  const mx = (a.x + b.x) * 0.5;
  const my = (a.y + b.y) * 0.5;
  const off = 2.4;
  return [
    `M ${(mx - ux * off - nx).toFixed(1)} ${(my - uy * off - ny).toFixed(1)} L ${(mx - ux * off + nx).toFixed(1)} ${(my - uy * off + ny).toFixed(1)}`,
    `M ${(mx + ux * off - nx).toFixed(1)} ${(my + uy * off - ny).toFixed(1)} L ${(mx + ux * off + nx).toFixed(1)} ${(my + uy * off + ny).toFixed(1)}`,
  ].join(" ");
}

// Module-level precomputed invariant 3D & 2D geometry (zero recomputation on scroll)
const STORY_FACE_DEFS: readonly (readonly string[])[] = [
  ["A", "C", "B"],
  ["A_prime", "B_prime", "C_prime"],
  ["A", "B", "B_prime", "A_prime"],
  ["B", "C", "C_prime", "B_prime"],
  ["C", "A", "A_prime", "C_prime"],
];

const STORY_STATIC_GEOM = (() => {
  const pMap = LANDING_PRISM_STORY_SPEC.pointMap;
  const baseY = pMap["A"].pos[1];
  const coords: Record<string, Vec3Tuple> = {};
  for (const key of STORY_POINT_KEYS) {
    const p = pMap[key].pos;
    coords[key] =
      key === "A" || key === "B" || key === "C" || key === "M" || key === "N"
        ? p
        : scaleStoryHeight(p, baseY);
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

  // Bounded plane quad for (MNP)
  const m = coords["M"];
  const n = coords["N"];
  const p = coords["P"];
  const q = coords["Q"];
  const ux = n[0] - m[0];
  const uy = n[1] - m[1];
  const uz = n[2] - m[2];
  const vx = p[0] - m[0];
  const vy = p[1] - m[1];
  const vz = p[2] - m[2];
  const normal: Vec3Tuple = [
    uy * vz - uz * vy,
    uz * vx - ux * vz,
    ux * vy - uy * vx,
  ];
  const planeQuad = computeBoundedPlaneQuad([m, n, p, q], normal, 0.24);

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

  // Exact isometric 2D true-shape trapezoid MNPQ from canonical domainXyz
  const domM = pMap["M"].domainXyz;
  const domN = pMap["N"].domainXyz;
  const domP = pMap["P"].domainXyz;
  const domQ = pMap["Q"].domainXyz;
  const uxRaw: Vec3Tuple = [domN[0] - domM[0], domN[1] - domM[1], domN[2] - domM[2]];
  const uLen = Math.hypot(...uxRaw) || 1;
  const uAxis: Vec3Tuple = [uxRaw[0] / uLen, uxRaw[1] / uLen, uxRaw[2] / uLen];
  const midTop: Vec3Tuple = [(domM[0] + domN[0]) * 0.5, (domM[1] + domN[1]) * 0.5, (domM[2] + domN[2]) * 0.5];
  const midBot: Vec3Tuple = [(domQ[0] + domP[0]) * 0.5, (domQ[1] + domP[1]) * 0.5, (domQ[2] + domP[2]) * 0.5];
  const vxRaw: Vec3Tuple = [midBot[0] - midTop[0], midBot[1] - midTop[1], midBot[2] - midTop[2]];
  const vLen = Math.hypot(...vxRaw) || 1;
  const vAxis: Vec3Tuple = [vxRaw[0] / vLen, vxRaw[1] / vLen, vxRaw[2] / vLen];
  const trapCentroid: Vec3Tuple = [
    (domM[0] + domN[0] + domP[0] + domQ[0]) * 0.25,
    (domM[1] + domN[1] + domP[1] + domQ[1]) * 0.25,
    (domM[2] + domN[2] + domP[2] + domQ[2]) * 0.25,
  ];
  const insetCenterX = 577;
  const insetCenterY = 144;
  const insetScale = 34;
  const mapTrapPt = (id: string, dom: Vec3Tuple) => {
    const rel: Vec3Tuple = [
      dom[0] - trapCentroid[0],
      dom[1] - trapCentroid[1],
      dom[2] - trapCentroid[2],
    ];
    const u = rel[0] * uAxis[0] + rel[1] * uAxis[1] + rel[2] * uAxis[2];
    const v = rel[0] * vAxis[0] + rel[1] * vAxis[1] + rel[2] * vAxis[2];
    return {
      id,
      label: pMap[id].label,
      role: pMap[id].role,
      x: insetCenterX + u * insetScale,
      y: insetCenterY + v * insetScale,
    };
  };
  const trapPts = [
    mapTrapPt("M", domM),
    mapTrapPt("N", domN),
    mapTrapPt("P", domP),
    mapTrapPt("Q", domQ),
  ];
  const trapPolyPoints = trapPts.map((pt) => `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`).join(" ");
  const insetTicksD = [
    buildDoubleTickD({ x: trapPts[1].x, y: trapPts[1].y, z: 0 }, { x: trapPts[2].x, y: trapPts[2].y, z: 0 }),
    buildDoubleTickD({ x: trapPts[0].x, y: trapPts[0].y, z: 0 }, { x: trapPts[3].x, y: trapPts[3].y, z: 0 }),
  ].join(" ");

  return {
    pMap,
    coords,
    solidCenter,
    planeQuad,
    rightAnglePts: { b1, b2, bc },
    trapPts,
    trapPolyPoints,
    insetTicksD,
    insetCardRect: { x: 466, y: 20, width: 222, height: 202 },
  };
})();

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
    const { pMap, coords, solidCenter, planeQuad, rightAnglePts, insetCardRect } =
      STORY_STATIC_GEOM;

    const insetReveal = reducedMotion
      ? pose.activeStageIndex === 3
        ? 1
        : 0
      : smoothstep(0.76, 0.9, pose.progress);
    const scale = 78 * pose.zoom;
    const cx = lerp(332, 224, insetReveal);
    const cy = 254;
    const proj: Record<string, ProjectedPoint2D> = {};
    for (const k of STORY_POINT_KEYS) {
      proj[k] = projectPrismPoint3D(coords[k], pose.yaw, pose.pitch, cx, cy, scale);
    }

    const seedHaloStrength = reducedMotion
      ? pose.activeStageIndex === 0
        ? 1
        : 0
      : pose.activeStageIndex >= 1
        ? Math.max(0, 1 - smoothstep(0.25, 0.34, pose.progress))
        : 1;

    const faceFrontMap = STORY_FACE_DEFS.map((f) =>
      isFaceFrontFacing(
        f.map((id) => coords[id]),
        solidCenter,
        pose.yaw,
        pose.pitch,
      ),
    );

    const edgeVisibleInSolid = (from: string, to: string): boolean => {
      for (let i = 0; i < STORY_FACE_DEFS.length; i++) {
        if (!faceFrontMap[i]) continue;
        const f = STORY_FACE_DEFS[i];
        if (f.includes(from) && f.includes(to)) return true;
      }
      return false;
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

    const edges = LANDING_PRISM_STORY_SPEC.solidEdges.map((edge) => {
      const a = proj[edge.from];
      const b = proj[edge.to];
      const isTop = edge.from.includes("prime") && edge.to.includes("prime");
      const isNonParticipating =
        isTop || (edge.from === "A" && edge.to === "A_prime");
      let opacity = 0.92;
      if (isNonParticipating && pose.parallelCue > 0.02) {
        opacity *= 1 - 0.16 * pose.parallelCue;
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

    const raB1 = projectPrismPoint3D(rightAnglePts.b1, pose.yaw, pose.pitch, cx, cy, scale);
    const raB2 = projectPrismPoint3D(rightAnglePts.b2, pose.yaw, pose.pitch, cx, cy, scale);
    const raC = projectPrismPoint3D(rightAnglePts.bc, pose.yaw, pose.pitch, cx, cy, scale);

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

    const liftY = (1 - pose.planeSweep) * 0.56;
    const planePolyPts = planeQuad.map((qPt) =>
      projectPrismPoint3D(
        [qPt[0], qPt[1] + liftY, qPt[2]],
        pose.yaw,
        pose.pitch,
        cx,
        cy,
        scale,
      ),
    );

    const fmt = (pts: readonly ProjectedPoint2D[]) =>
      pts.map((pt) => `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`).join(" ");

    const loopIds = ["M", "N", "P", "Q"] as const;
    const traceHostFaceIdx = [0, 4, 3, 2] as const;
    const tracedEdges = loopIds.map((id, idx) => {
      const nextId = loopIds[(idx + 1) % loopIds.length];
      const u = clamp01(pose.traceProgress * loopIds.length - idx);
      const p0 = proj[id];
      const p1 = proj[nextId];
      const hostIdx = traceHostFaceIdx[idx] ?? 0;
      const isFront = hostIdx === 0 ? true : Boolean(faceFrontMap[hostIdx]);
      return {
        key: `${id}-${nextId}`,
        x1: p0.x,
        y1: p0.y,
        x2: lerp(p0.x, p1.x, u),
        y2: lerp(p0.y, p1.y, u),
        u,
        isFront,
      };
    });

    const showQ =
      pose.activeStageIndex >= 2 &&
      (pose.parallelCue > 0.25 || pose.traceProgress > 0.56 || reducedMotion);
    const visibleIds = STORY_POINT_KEYS.filter((id) => (id === "Q" ? showQ : true));

    const labelCandidates = visibleIds.map((id) => {
      const pt = proj[id];
      const dx = pt.x - centroidX;
      const dy = pt.y - centroidY;
      const len = Math.max(1, Math.hypot(dx, dy));
      const pad = id === "C" ? 15 : 18;
      let lx = pt.x + (dx / len) * pad;
      let ly = pt.y + (dy / len) * pad + 4;
      // Nudge any top-right vertex label (e.g. B') clear of Stage 4 inset frame
      if (insetReveal > 0.08 && lx > insetCardRect.x - 24 && ly < insetCardRect.y + insetCardRect.height + 16) {
        lx = Math.min(lx, insetCardRect.x - 24);
      }
      return { id, x: lx, y: ly };
    });
    separateLabelPositions(
      labelCandidates,
      STORY_SVG_W,
      STORY_SVG_H,
      28,
      30,
      22,
      24,
    );

    const makeBaseEqTick = (aId: string, bId: string, tFrac: number) => {
      const pa = proj[aId];
      const pb = proj[bId];
      const mx = lerp(pa.x, pb.x, tFrac);
      const my = lerp(pa.y, pb.y, tFrac);
      const dx = pb.x - pa.x;
      const dy = pb.y - pa.y;
      const len = Math.hypot(dx, dy) || 1;
      const nx = (-dy / len) * 4.2;
      const ny = (dx / len) * 4.2;
      return `M ${(mx - nx).toFixed(1)} ${(my - ny).toFixed(1)} L ${(mx + nx).toFixed(1)} ${(my + ny).toFixed(1)}`;
    };
    const equilateralBaseTicksD = [
      makeBaseEqTick("A", "B", 0.3),
      makeBaseEqTick("B", "C", 0.5),
      makeBaseEqTick("A", "C", 0.3),
    ].join(" ");

    const congruenceLegsD = [
      buildDoubleTickD(proj["N"], proj["P"]),
      buildDoubleTickD(proj["M"], proj["Q"]),
    ].join(" ");

    const labels = visibleIds.map((id, i) => ({
      id,
      label: pMap[id].label,
      role: pMap[id].role,
      px: proj[id].x,
      py: proj[id].y,
      lx: labelCandidates[i].x,
      ly: labelCandidates[i].y,
    }));

    const frontLateralPolys = STORY_FACE_DEFS.slice(2)
      .map((f, idx) => ({
        pts: fmt(f.map((id) => proj[id])),
        front: faceFrontMap[idx + 2],
        toneClass:
          idx === 0
            ? "axo-v14-svg-prism-face-lit"
            : "axo-v14-svg-prism-face-shade",
      }))
      .filter((item) => item.front);

    const haloCy = Math.min(448, (proj["A"].y + proj["B"].y + proj["C"].y) / 3 + 26);

    return {
      proj,
      cx,
      insetReveal,
      seedHaloStrength,
      edges,
      frontLateralPolys,
      midpointTicks,
      equilateralBaseTicksD,
      congruenceLegsD,
      haloCy,
      rightAnglePath: `M ${raB1.x.toFixed(1)} ${raB1.y.toFixed(1)} L ${raC.x.toFixed(1)} ${raC.y.toFixed(1)} L ${raB2.x.toFixed(1)} ${raB2.y.toFixed(1)}`,
      basePts: fmt([proj["A"], proj["B"], proj["C"]]),
      topPts: fmt([proj["A_prime"], proj["B_prime"], proj["C_prime"]]),
      planePts: fmt(planePolyPts),
      sectionPts: fmt([proj["M"], proj["N"], proj["P"], proj["Q"]]),
      tracedEdges,
      labels,
    };
  }, [pose, reducedMotion]);

  const { trapPts, trapPolyPoints, insetTicksD, insetCardRect } = STORY_STATIC_GEOM;

  return (
    <div
      id="landing-storytelling-scene"
      className="axo-v14-story-stage"
      data-story-stage={pose.activeStageIndex}
      data-story-progress={pose.progress.toFixed(3)}
      data-reduced-motion={reducedMotion ? "true" : "false"}
    >
      <svg
        className="axo-v14-story-svg"
        viewBox={`0 0 ${STORY_SVG_W} ${STORY_SVG_H}`}
        role="img"
        aria-label={`Lăng trụ tam giác đều ABC.A′B′C′: ${activeStage.chapterHeading}`}
      >
        <ellipse
          className="axo-v14-svg-contact-halo"
          cx={scene.cx.toFixed(1)}
          cy={scene.haloCy.toFixed(1)}
          rx="192"
          ry="24"
        />

        <polygon className="axo-v14-svg-prism-base" points={scene.basePts} />

        {scene.frontLateralPolys.map((face, idx) => (
          <polygon
            key={`lat-${idx}`}
            className={`axo-v14-svg-prism-face ${face.toneClass}`}
            points={face.pts}
            fillOpacity={face.toneClass.includes("lit") ? "0.82" : "0.44"}
          />
        ))}

        <polygon
          className="axo-v14-svg-prism-top"
          points={scene.topPts}
          fillOpacity="0.200"
          strokeOpacity="0.720"
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
          opacity="0.88"
        />

        <path
          className="axo-v14-svg-eq-tick"
          d={scene.equilateralBaseTicksD}
          fill="none"
          opacity={Math.max(0.28, 0.85 * (1 - 0.5 * pose.sectionFill)).toFixed(3)}
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
              className="axo-v14-svg-parallel-band"
              x1={scene.proj["B"].x}
              y1={scene.proj["B"].y}
              x2={scene.proj["C"].x}
              y2={scene.proj["C"].y}
            />
            <line
              className="axo-v14-svg-parallel-band"
              x1={scene.proj["M"].x}
              y1={scene.proj["M"].y}
              x2={scene.proj["N"].x}
              y2={scene.proj["N"].y}
            />
            <line
              className="axo-v14-svg-parallel-band"
              x1={scene.proj["P"].x}
              y1={scene.proj["P"].y}
              x2={scene.proj["Q"].x}
              y2={scene.proj["Q"].y}
            />
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
            <line
              className="axo-v14-svg-parallel-guide"
              x1={scene.proj["P"].x}
              y1={scene.proj["P"].y}
              x2={scene.proj["Q"].x}
              y2={scene.proj["Q"].y}
            />
          </g>
        )}

        {pose.planeSweep > 0.02 && (
          <polygon
            className="axo-v14-svg-cutting-plane"
            points={scene.planePts}
            fillOpacity={(0.13 * pose.planeSweep).toFixed(3)}
            strokeOpacity={(0.54 * pose.planeSweep).toFixed(3)}
          />
        )}

        {pose.sectionFill > 0.02 && (
          <polygon
            className="axo-v14-svg-section-poly"
            points={scene.sectionPts}
            fillOpacity={(0.4 * pose.sectionFill).toFixed(3)}
            stroke="none"
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
              strokeDasharray={seg.isFront ? undefined : "6 4"}
              strokeOpacity={(
                (seg.isFront ? 0.96 : 0.72) *
                Math.min(1, 0.45 + 0.55 * seg.u)
              ).toFixed(3)}
            />
          ) : null,
        )}

        {pose.sectionFill > 0.35 && (
          <path
            className="axo-v14-svg-leg-tick"
            d={scene.congruenceLegsD}
            fill="none"
            opacity={Math.min(0.92, (pose.sectionFill - 0.35) * 1.54).toFixed(3)}
          />
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
            <g key={item.id}>
              {isSeed && scene.seedHaloStrength > 0.04 && (
                <circle
                  className="axo-v14-svg-seed-halo"
                  cx={item.px}
                  cy={item.py}
                  r={(7.5 + 3.2 * scene.seedHaloStrength).toFixed(1)}
                  opacity={(0.82 * scene.seedHaloStrength).toFixed(3)}
                />
              )}
              <circle
                className={dotClass}
                cx={item.px}
                cy={item.py}
                r={isInter ? 4.8 : isSeed ? 4.4 : 3.2}
              />
              <text className={textClass} x={item.lx} y={item.ly}>
                {item.label}
              </text>
            </g>
          );
        })}

        {scene.insetReveal > 0.02 && (
          <g
            className="axo-v14-svg-trueshape-inset"
            opacity={scene.insetReveal.toFixed(3)}
            transform={`translate(0 ${(10 * (1 - scene.insetReveal)).toFixed(1)})`}
          >
            <rect
              className="axo-v14-svg-inset-card"
              x={insetCardRect.x}
              y={insetCardRect.y}
              width={insetCardRect.width}
              height={insetCardRect.height}
              rx="12"
            />
            <text
              className="axo-v14-svg-inset-caption"
              x={insetCardRect.x + insetCardRect.width * 0.5}
              y="46"
            >
              Hình thật thiết diện
            </text>
            <text
              className="axo-v14-svg-inset-subcaption"
              x={insetCardRect.x + insetCardRect.width * 0.5}
              y="64"
            >
              Hình thang cân MNPQ
            </text>
            <polygon
              className="axo-v14-svg-section-poly"
              points={trapPolyPoints}
              fillOpacity="0.38"
              strokeOpacity="0.94"
            />
            <line
              className="axo-v14-svg-parallel-guide"
              x1={trapPts[0].x}
              y1={trapPts[0].y}
              x2={trapPts[1].x}
              y2={trapPts[1].y}
            />
            <line
              className="axo-v14-svg-parallel-guide"
              x1={trapPts[3].x}
              y1={trapPts[3].y}
              x2={trapPts[2].x}
              y2={trapPts[2].y}
            />
            <path className="axo-v14-svg-leg-tick" d={insetTicksD} fill="none" />
            {trapPts.map((tp, idx) => (
              <g key={`trap-${tp.id}`}>
                <circle
                  className={
                    tp.role === "intersection"
                      ? "axo-v14-svg-section-dot"
                      : "axo-v14-svg-seed-dot"
                  }
                  cx={tp.x.toFixed(1)}
                  cy={tp.y.toFixed(1)}
                  r="3.8"
                />
                <text
                  className={
                    tp.role === "intersection"
                      ? "axo-v14-svg-label-inter"
                      : "axo-v14-svg-label-seed"
                  }
                  x={(tp.x + (idx === 0 || idx === 3 ? -15 : 15)).toFixed(1)}
                  y={(tp.y + (idx < 2 ? -10 : 16)).toFixed(1)}
                >
                  {tp.label}
                </text>
              </g>
            ))}
          </g>
        )}
      </svg>

      <div className="axo-v14-story-stage-bar">
        <span className="axo-v14-story-stage-status">
          {`0${activeStage.shortNum} / 04 · ${activeStage.epistemicRole}`}
        </span>
        <div className="axo-v14-story-legend" aria-hidden="true">
          <span className="axo-v14-story-legend-item">
            <span className="axo-v14-story-swatch is-seed" />
            Điểm gốc
          </span>
          <span className="axo-v14-story-legend-item">
            <span className="axo-v14-story-swatch is-plane" />
            Mặt phẳng (MNP)
          </span>
          <span className="axo-v14-story-legend-item">
            <span className="axo-v14-story-swatch is-section" />
            Thiết diện MNPQ
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

const STAGE_SNAP_PROGRESS = [0.08, 0.375, 0.625, 0.92] as const;

export function LandingStorytellingV14() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const runwayRef = useRef<HTMLDivElement | null>(null);
  const stagePinRef = useRef<HTMLDivElement | null>(null);
  const chapterRefs = useRef<(HTMLLIElement | null)[]>([]);
  const targetProgressRef = useRef<number>(readStoryProgressOverride() ?? 0);
  const currentProgressRef = useRef<number>(targetProgressRef.current);
  const reducedMotionRef = useRef<boolean>(false);

  const [reducedMotion, setReducedMotion] = useState<boolean>(false);
  const [scrollProgress, setScrollProgress] = useState<number>(
    () => targetProgressRef.current,
  );

  const computeFocalY = useCallback((): number => {
    const pinEl = stagePinRef.current;
    if (!pinEl) return 380;
    const pinHeight = pinEl.getBoundingClientRect().height || 500;
    if (window.innerWidth <= 920) {
      const topOffset = 68;
      const pinBottom = topOffset + pinHeight;
      const freeBelowPin = Math.max(0, window.innerHeight - pinBottom);
      const bandOffset = Math.round(Math.max(140, Math.min(168, freeBelowPin * 0.5)));
      return Math.min(window.innerHeight - 40, pinBottom + bandOffset);
    }
    const dockBottom = Math.min(window.innerHeight - 96, 88 + pinHeight);
    return Math.max(240, dockBottom - 110);
  }, []);

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
      if (reducedMotionRef.current || Math.abs(diff) < 0.002) {
        if (Math.abs(cur - target) > 0.0005) {
          currentProgressRef.current = target;
          setScrollProgress(target);
        }
        return;
      }
      const next = cur + diff * 0.36;
      currentProgressRef.current = next;
      setScrollProgress(next);
      rafId = window.requestAnimationFrame(tick);
    };

    const syncTarget = (immediate = false) => {
      if (readStoryProgressOverride() !== null) return;
      const secEl = sectionRef.current;
      if (!secEl) return;
      const secRect = secEl.getBoundingClientRect();

      let nextTarget: number | null = null;
      if (secRect.top > window.innerHeight + 160) {
        nextTarget = 0;
      } else if (secRect.bottom < -160) {
        nextTarget = 1;
      } else {
        const chEls = chapterRefs.current;
        if (chEls.length < 4 || chEls.some((el) => !el)) return;
        const rects = chEls.map((el) => el!.getBoundingClientRect());
        const centers = rects.map((r) => r.top + r.height * 0.5);
        nextTarget = computeChapterScrollProgress(
          centers,
          computeFocalY(),
          rects[3].bottom,
        );
      }

      targetProgressRef.current = nextTarget;
      if (
        immediate ||
        reducedMotionRef.current ||
        Math.abs(nextTarget - currentProgressRef.current) > 0.22
      ) {
        if (Math.abs(currentProgressRef.current - nextTarget) > 0.001) {
          currentProgressRef.current = nextTarget;
          setScrollProgress(nextTarget);
        }
        return;
      }
      if (!document.hidden && rafId === 0 && Math.abs(nextTarget - currentProgressRef.current) >= 0.002) {
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
    if (stagePinRef.current) ro?.observe(stagePinRef.current);

    return () => {
      if (rafId !== 0) window.cancelAnimationFrame(rafId);
      window.removeEventListener("scroll", handleScrollOrResize);
      window.removeEventListener("resize", handleScrollOrResize);
      document.removeEventListener("visibilitychange", onVisibility);
      mq?.removeEventListener?.("change", onMotionChange);
      ro?.disconnect();
    };
  }, [computeFocalY]);

  const jumpToChapter = useCallback(
    (idx: number) => {
      if (typeof window === "undefined") return;
      const chEl = chapterRefs.current[idx];
      if (!chEl) return;
      const rect = chEl.getBoundingClientRect();
      const chCenterDoc = window.scrollY + rect.top + rect.height * 0.5;
      const focal = computeFocalY();
      const targetY =
        window.innerWidth <= 920
          ? Math.max(
              0,
              Math.round(
                window.scrollY +
                  rect.top -
                  (68 + (stagePinRef.current?.getBoundingClientRect().height || 300) + 14),
              ),
            )
          : Math.max(0, Math.round(chCenterDoc - focal));
      const snap = STAGE_SNAP_PROGRESS[idx] ?? 0;

      if (readStoryProgressOverride() === null) {
        targetProgressRef.current = snap;
        currentProgressRef.current = snap;
        setScrollProgress(snap);
      }
      window.scrollTo({
        top: targetY,
        behavior: reducedMotionRef.current ? "auto" : "smooth",
      });
    },
    [computeFocalY],
  );

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
            Cuộn để theo dõi mạch dựng liên tục trên lăng trụ tam giác đều ABC.A′B′C′.
          </p>
        </div>

        <div ref={runwayRef} className="axo-v14-story-runway">
          <div className="axo-v14-story-track">
            <div ref={stagePinRef} className="axo-v14-story-stage-pin">
              <PrismEditorialStage pose={pose} reducedMotion={reducedMotion} />
            </div>

            <div className="axo-v14-story-narrative">
              <div className="axo-v14-story-narrative-head">
                <p className="axo-v14-story-context-line">
                  Mô hình: Lăng trụ tam giác đều ABC.A′B′C′
                </p>
                <nav
                  className="axo-v14-story-rail"
                  aria-label="Tiến trình bốn chặng dựng hình"
                >
                  {STORY_STAGES_V14.map((s, idx) => {
                    const segFill = reducedMotion
                      ? idx <= pose.activeStageIndex
                        ? 1
                        : 0
                      : clamp01(pose.progress * STORY_STAGES_V14.length - idx);
                    const stateCls =
                      idx === pose.activeStageIndex
                        ? " is-current"
                        : idx < pose.activeStageIndex
                          ? " is-done"
                          : "";
                    return (
                      <button
                        key={s.shortNum}
                        type="button"
                        className={`axo-v14-story-rail-item${stateCls}`}
                        aria-current={idx === pose.activeStageIndex ? "step" : undefined}
                        aria-label={`${s.chapterHeading}: ${s.title}`}
                        onClick={() => jumpToChapter(idx)}
                      >
                        <span className="axo-v14-story-rail-bar" aria-hidden="true">
                          <span
                            className="axo-v14-story-rail-fill"
                            style={{ transform: `scaleX(${segFill.toFixed(3)})` }}
                          />
                        </span>
                        <span className="axo-v14-story-rail-label">
                          {`0${s.shortNum} · ${s.mobileShortTag}`}
                        </span>
                      </button>
                    );
                  })}
                </nav>
              </div>

              <ol
                className="axo-v14-story-chapters"
                aria-label="Các chặng dựng hình theo cuộn trang"
              >
                {STORY_STAGES_V14.map((stage, idx) => {
                  const isActive = idx === pose.activeStageIndex;
                  const state = isActive
                    ? "active"
                    : idx < pose.activeStageIndex
                      ? "done"
                      : "upcoming";
                  return (
                    <li
                      key={stage.shortNum}
                      ref={(el) => {
                        chapterRefs.current[idx] = el;
                      }}
                      data-story-chapter={idx}
                      data-active={isActive ? "true" : "false"}
                      data-state={state}
                      className={`axo-v14-story-chapter${isActive ? " is-active" : ""}`}
                    >
                      <div className="axo-v14-story-chapter-meta">
                        <span className="axo-v14-story-chapter-index">
                          {stage.chapterHeading}
                        </span>
                        <span className="axo-v14-story-chapter-sep" aria-hidden="true">
                          ·
                        </span>
                        <span className="axo-v14-story-epistemic-role">
                          {stage.epistemicRole}
                        </span>
                      </div>
                      <h3 className="axo-v14-story-chapter-title">
                        <button
                          type="button"
                          className="axo-v14-story-chapter-trigger"
                          aria-current={isActive ? "step" : undefined}
                          onClick={() => jumpToChapter(idx)}
                        >
                          {stage.title}
                        </button>
                      </h3>
                      <p className="axo-v14-story-chapter-summary">
                        {stage.summary}
                      </p>
                      <div className="axo-v14-story-epistemic-box">
                        {stage.establishedState}
                      </div>
                    </li>
                  );
                })}
              </ol>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
