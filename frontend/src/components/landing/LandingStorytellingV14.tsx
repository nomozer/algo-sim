import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { AnnotatedPhrase } from "./AnnotatedHeading";
import {
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
    title: "Ghim ba điểm gốc M, N, P trên đáy và cạnh bên",
    summary:
      "Từ giả thiết lăng trụ tam giác đều ABC.A′B′C′, Axo đặt chuẩn xác ba trung điểm M ∈ AB, N ∈ AC và P ∈ CC′ trên các cạnh xuất phát.",
    relationNote: "Giả thiết: M ∈ AB · N ∈ AC · P ∈ CC′",
    camera: {
      yaw: -0.36,
      pitch: 0.30,
      zoom: 1.12,
      extrude: 0.22,
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
    title: "Hoàn chỉnh khối lăng trụ và phân lớp nét thấy — khuất",
    summary:
      "Ba cạnh bên AA′, BB′, CC′ vươn thẳng góc lên đáy A′B′C′ song song với ABC, đồng thời phân tách nét liền phía trước và nét đứt phía sau theo góc nhìn.",
    relationNote: "Dựng khối: AA′, BB′, CC′ ⊥ (ABC) · Nét thấy & nét khuất",
    camera: {
      yaw: -0.22,
      pitch: 0.32,
      zoom: 1.18,
      extrude: 1,
      planeSweep: 0,
      parallelCue: 0,
      traceProgress: 0,
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
      "Đường trung bình MN song song với cạnh đáy BC trong (ABC). Vì BC nằm trong mặt bên (BCC′B′), giao tuyến qua P buộc phải song song BC và cắt BB′ đúng tại trung điểm Q.",
    relationNote: "Quan hệ: MN ∥ BC ⇒ PQ ∥ BC · Q ∈ BB′",
    camera: {
      yaw: -0.06,
      pitch: 0.35,
      zoom: 1.22,
      extrude: 1,
      planeSweep: 1,
      parallelCue: 1,
      traceProgress: 0.85,
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
      "Bốn đoạn giao tuyến MN, NP, PQ và QM khép kín trên mặt phẳng cắt (MNP), tạo thành thiết diện hình thang cân cân đối giữa các mặt bên.",
    relationNote: "Quan hệ khép kín: MN ∥ PQ · MQ và NP đối xứng qua mặt trung trực",
    camera: {
      yaw: 0.08,
      pitch: 0.37,
      zoom: 1.25,
      extrude: 1,
      planeSweep: 1,
      parallelCue: 0.52,
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

export function computeChapterEnvelope(
  progress: number,
  index: number,
  reducedMotion = false,
): StoryChapterEnvelope {
  if (reducedMotion) {
    return { opacity: 1, offsetY: 0, isVisible: true };
  }
  const p = clamp01(progress);

  if (index === 0) {
    if (p <= 0.19) return { opacity: 1, offsetY: 0, isVisible: true };
    if (p < 0.248) {
      const u = smoothstep(0.19, 0.248, p);
      return { opacity: 1 - u, offsetY: -10 * u, isVisible: 1 - u > 0.02 };
    }
    return { opacity: 0, offsetY: -10, isVisible: false };
  }

  if (index === 1) {
    if (p <= 0.252) return { opacity: 0, offsetY: 10, isVisible: false };
    if (p < 0.31) {
      const u = smoothstep(0.252, 0.31, p);
      return { opacity: u, offsetY: 10 * (1 - u), isVisible: u > 0.02 };
    }
    if (p <= 0.44) return { opacity: 1, offsetY: 0, isVisible: true };
    if (p < 0.498) {
      const u = smoothstep(0.44, 0.498, p);
      return { opacity: 1 - u, offsetY: -10 * u, isVisible: 1 - u > 0.02 };
    }
    return { opacity: 0, offsetY: -10, isVisible: false };
  }

  if (index === 2) {
    if (p <= 0.502) return { opacity: 0, offsetY: 10, isVisible: false };
    if (p < 0.56) {
      const u = smoothstep(0.502, 0.56, p);
      return { opacity: u, offsetY: 10 * (1 - u), isVisible: u > 0.02 };
    }
    if (p <= 0.69) return { opacity: 1, offsetY: 0, isVisible: true };
    if (p < 0.748) {
      const u = smoothstep(0.69, 0.748, p);
      return { opacity: 1 - u, offsetY: -10 * u, isVisible: 1 - u > 0.02 };
    }
    return { opacity: 0, offsetY: -10, isVisible: false };
  }

  if (index === 3) {
    if (p <= 0.752) return { opacity: 0, offsetY: 10, isVisible: false };
    if (p < 0.81) {
      const u = smoothstep(0.752, 0.81, p);
      return { opacity: u, offsetY: 10 * (1 - u), isVisible: u > 0.02 };
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

  // Smooth piecewise keyframes across normalized scroll progress [0, 1]
  // Stops at canonical stage centers: 0.00 -> 0.34 -> 0.64 -> 0.94
  const k = [0, 0.34, 0.64, 0.94] as const;
  let s0 = STORY_STAGES_V14[0].camera;
  let s1 = STORY_STAGES_V14[0].camera;
  let u = 0;

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

  // Ensure normal points outward relative to solid center
  const inX = vc[0] - v0[0];
  const inY = vc[1] - v0[1];
  const inZ = vc[2] - v0[2];
  if (nx * inX + ny * inY + nz * inZ > 0) {
    nx = -nx;
    ny = -ny;
    nz = -nz;
  }

  // Camera sits at (0, 0, camDist) in view space
  const viewX = -v0[0];
  const viewY = -v0[1];
  const viewZ = 11.5 - v0[2];
  return nx * viewX + ny * viewY + nz * viewZ > 0.02;
}

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

    const scale = 66 * pose.zoom;
    const cx = 300;
    const cy = 236;
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
      if (pose.extrude < 0.35) {
        return from !== "C" && to !== "C";
      }
      let frontTouch = 0;
      for (let i = 0; i < faceDefs.length; i++) {
        if (!faceFrontMap[i]) continue;
        const f = faceDefs[i];
        const hasFrom = f.includes(from);
        const hasTo = f.includes(to);
        if (hasFrom && hasTo) frontTouch++;
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

    const edges = LANDING_PRISM_STORY_SPEC.solidEdges.map((edge) => {
      const a = proj[edge.from];
      const b = proj[edge.to];
      const isVertical =
        (edge.from === "A" && edge.to === "A_prime") ||
        (edge.from === "B" && edge.to === "B_prime") ||
        (edge.from === "C" && edge.to === "C_prime");
      const isTop = edge.from.includes("prime") && edge.to.includes("prime");
      const isNonParticipating =
        isTop || (edge.from === "A" && edge.to === "A_prime");
      let opacity = 0.88;
      if (isVertical || isTop) {
        opacity = Math.max(0.24, pose.extrude * 0.9);
      }
      if (isNonParticipating && pose.parallelCue > 0.02) {
        opacity *= 1 - 0.42 * pose.parallelCue;
      }
      const front = edgeVisibleInSolid(edge.from, edge.to);
      const dashed = !front || (pose.extrude < 0.65 && (isVertical || isTop));
      return {
        key: `${edge.from}-${edge.to}`,
        a,
        b,
        dashed,
        opacity,
      };
    });

    // Right-angle bracket at A showing AA' perp AB
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

    const liftY = (1 - pose.planeSweep) * 0.78;
    const planePolyPts = LANDING_PRISM_STORY_SPEC.planeQuad.map((q) =>
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

    // Progressive traced edges around M -> N -> P -> Q
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
      if (id === "Q") return pose.planeSweep > 0.38;
      if (id === "A_prime" || id === "B_prime" || id === "C_prime") {
        return pose.extrude > 0.6;
      }
      return true;
    });

    const labels = visibleIds.map((id) => {
      const pt = proj[id];
      const dx = pt.x - centroidX;
      const dy = pt.y - centroidY;
      const len = Math.max(1, Math.hypot(dx, dy));
      const pad = 18;
      return {
        id,
        label: pMap[id].label,
        role: pMap[id].role,
        px: pt.x,
        py: pt.y,
        lx: Math.min(572, Math.max(28, pt.x + (dx / len) * pad)),
        ly: Math.min(404, Math.max(24, pt.y + (dy / len) * pad + 4)),
      };
    });

    const frontLateralPolys = faceDefs
      .slice(2)
      .filter((_, idx) => faceFrontMap[idx + 2])
      .map((f) => fmt(f.map((id) => proj[id])));

    return {
      proj,
      edges,
      frontLateralPolys,
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
          viewBox="0 0 600 430"
          role="img"
          aria-label={`Lăng trụ tam giác đều ABC.A′B′C′: ${activeStage.chapterHeading}`}
        >
          <ellipse
            className="axo-v14-svg-contact-halo"
            cx="300"
            cy="352"
            rx="186"
            ry="24"
          />

          <polygon
            className="axo-v14-svg-prism-base"
            points={scene.basePts}
          />

          {pose.extrude > 0.45 &&
            scene.frontLateralPolys.map((pts, idx) => (
              <polygon
                key={`lat-${idx}`}
                className="axo-v14-svg-prism-face"
                points={pts}
                fillOpacity={(0.36 * pose.extrude).toFixed(3)}
              />
            ))}

          {pose.extrude > 0.35 && (
            <polygon
              className="axo-v14-svg-prism-top"
              points={scene.topPts}
              fillOpacity={(0.14 * pose.extrude).toFixed(3)}
            />
          )}

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

          {pose.extrude > 0.62 && (
            <path
              className="axo-v14-svg-edge-altitude"
              d={scene.rightAnglePath}
              fill="none"
              opacity={((pose.extrude - 0.62) / 0.38).toFixed(3)}
            />
          )}

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
              fillOpacity={(0.26 * pose.planeSweep).toFixed(3)}
              strokeOpacity={(0.76 * pose.planeSweep).toFixed(3)}
            />
          )}

          {pose.sectionFill > 0.02 && (
            <polygon
              className="axo-v14-svg-section-poly"
              points={scene.sectionPts}
              fillOpacity={(0.48 * pose.sectionFill).toFixed(3)}
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
              <g key={item.id}>
                <circle
                  className={dotClass}
                  cx={item.px}
                  cy={item.py}
                  r={isInter ? 4.6 : isSeed ? 4.0 : 3.0}
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
  const [reducedMotion, setReducedMotion] = useState<boolean>(false);
  const [scrollProgress, setScrollProgress] = useState<number>(
    () => readStoryProgressOverride() ?? 0,
  );

  useEffect(() => {
    if (typeof window === "undefined") return;

    const mq = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    setReducedMotion(Boolean(mq?.matches));

    const override = readStoryProgressOverride();
    if (override !== null) {
      setScrollProgress(override);
    }

    let rafId = 0;

    const syncFromScroll = () => {
      rafId = 0;
      if (readStoryProgressOverride() !== null) return;
      const runwayEl = runwayRef.current;
      const stickyEl = stickyRef.current;
      if (!runwayEl || !stickyEl) return;
      const runwayRect = runwayEl.getBoundingClientRect();
      const stickyRect = stickyEl.getBoundingClientRect();
      const next = computeStoryScrollProgress(
        runwayRect.top,
        runwayRect.height,
        stickyRect.height,
      );
      setScrollProgress((prev) => (Math.abs(prev - next) < 0.002 ? prev : next));
    };

    const requestSync = () => {
      if (document.hidden || rafId !== 0) return;
      rafId = window.requestAnimationFrame(syncFromScroll);
    };

    const onMotionChange = (ev: MediaQueryListEvent) => {
      setReducedMotion(ev.matches);
      requestSync();
    };

    const onVisibility = () => {
      if (!document.hidden) requestSync();
      else if (rafId !== 0) {
        window.cancelAnimationFrame(rafId);
        rafId = 0;
      }
    };

    if (override === null) {
      syncFromScroll();
    }
    window.addEventListener("scroll", requestSync, { passive: true });
    window.addEventListener("resize", requestSync, { passive: true });
    document.addEventListener("visibilitychange", onVisibility);
    mq?.addEventListener?.("change", onMotionChange);

    const ro =
      typeof ResizeObserver !== "undefined" && runwayRef.current
        ? new ResizeObserver(requestSync)
        : null;
    if (runwayRef.current) ro?.observe(runwayRef.current);
    if (stickyRef.current) ro?.observe(stickyRef.current);

    return () => {
      if (rafId !== 0) window.cancelAnimationFrame(rafId);
      window.removeEventListener("scroll", requestSync);
      window.removeEventListener("resize", requestSync);
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
        <div ref={runwayRef} className="axo-v14-story-runway">
          <div ref={stickyRef} className="axo-v14-story-sticky">
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
                ABC.A′B′C′: từ ba trung điểm gốc đến thiết diện hoàn chỉnh.
              </p>
            </div>

            <div className="axo-v14-story-track">
              <PrismEditorialStage pose={pose} reducedMotion={reducedMotion} />

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
    </section>
  );
}
