import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import {
  LANDING_CUBE_SAMPLE,
  LANDING_PRISM_STORY_SPEC,
  LANDING_PYRAMID_SAMPLE,
  type LandingPointSpec,
  type LandingSampleSpec,
  type Vec3Tuple,
} from "../landing-geometry-data";

export type V14PortalId = "construction" | "exploration" | "relationships";

export interface V14HeroPortalSpec {
  readonly id: V14PortalId;
  readonly index: string;
  readonly shortLabel: string;
  readonly title: string;
  readonly bg: string;
  readonly floorColor: string;
  readonly darkTheme: boolean;
  readonly accentColor: string;
  readonly position: [number, number, number];
  readonly rotation: [number, number, number];
  readonly sampleId: string;
}

export const V14_HERO_PORTAL_SPECS: readonly V14HeroPortalSpec[] = [
  {
    id: "construction",
    index: "01",
    shortLabel: "01 · Dựng hình",
    title: "Dựng hình",
    bg: "#f1ece3",
    floorColor: "#e4dccf",
    darkTheme: false,
    accentColor: "#0075de",
    position: [-1.12, 0, -0.04],
    rotation: [0, 0.46, 0],
    sampleId: LANDING_PRISM_STORY_SPEC.id,
  },
  {
    id: "exploration",
    index: "02",
    shortLabel: "02 · Quan sát 3D",
    title: "Quan sát 3D",
    bg: "#1b2847",
    floorColor: "#131c33",
    darkTheme: true,
    accentColor: "#62aef0",
    position: [0, 0, 0.08],
    rotation: [0, 0, 0],
    sampleId: LANDING_CUBE_SAMPLE.id,
  },
  {
    id: "relationships",
    index: "03",
    shortLabel: "03 · Thiết diện",
    title: "Thiết diện",
    bg: "#e6eef8",
    floorColor: "#d6e3f2",
    darkTheme: false,
    accentColor: "#dd5b00",
    position: [1.12, 0, -0.04],
    rotation: [0, -0.46, 0],
    sampleId: LANDING_PYRAMID_SAMPLE.id,
  },
] as const;

const WORLD_CENTER: Vec3Tuple = [0, -0.14, -2.15];

function scaleSampleVec(
  v: Vec3Tuple,
  scale: number,
  center: Vec3Tuple = [0, 0, 0],
): [number, number, number] {
  return [
    center[0] + v[0] * scale,
    center[1] + v[1] * scale,
    center[2] + v[2] * scale,
  ];
}

function createFanPolygonGeometry(pts: readonly [number, number, number][]): THREE.BufferGeometry {
  const geom = new THREE.BufferGeometry();
  if (pts.length < 3) return geom;
  const positions: number[] = [];
  const p0 = pts[0];
  for (let i = 1; i < pts.length - 1; i++) {
    const p1 = pts[i];
    const p2 = pts[i + 1];
    positions.push(p0[0], p0[1], p0[2], p1[0], p1[1], p1[2], p2[0], p2[1], p2[2]);
  }
  geom.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geom.computeVertexNormals();
  return geom;
}

function createCardOverlayTextures(
  title: string,
  indexLabel: string,
  darkTheme: boolean,
  accentHex: string,
): { titleTex: THREE.CanvasTexture | null; indexTex: THREE.CanvasTexture | null } {
  if (typeof document === "undefined") {
    return { titleTex: null, indexTex: null };
  }

  const titleCanvas = document.createElement("canvas");
  titleCanvas.width = 512;
  titleCanvas.height = 148;
  const tctx = titleCanvas.getContext("2d");
  if (!tctx) return { titleTex: null, indexTex: null };

  tctx.clearRect(0, 0, titleCanvas.width, titleCanvas.height);
  tctx.fillStyle = accentHex;
  if (typeof tctx.roundRect === "function") {
    tctx.beginPath();
    tctx.roundRect(24, 24, 34, 6, 3);
    tctx.fill();
  } else {
    tctx.fillRect(24, 24, 34, 6);
  }
  tctx.fillStyle = darkTheme ? "#f8fafc" : "#141413";
  tctx.font = '700 56px "Inter", "Segoe UI", system-ui, sans-serif';
  tctx.textBaseline = "top";
  tctx.fillText(title, 24, 46);

  const titleTex = new THREE.CanvasTexture(titleCanvas);
  titleTex.colorSpace = THREE.SRGBColorSpace;
  titleTex.needsUpdate = true;

  const idxCanvas = document.createElement("canvas");
  idxCanvas.width = 160;
  idxCanvas.height = 72;
  const ictx = idxCanvas.getContext("2d");
  let indexTex: THREE.CanvasTexture | null = null;
  if (ictx) {
    ictx.clearRect(0, 0, idxCanvas.width, idxCanvas.height);
    ictx.fillStyle = darkTheme ? "#cbd5e1" : "#4b4945";
    ictx.font = '600 40px "Inter", "Segoe UI", system-ui, sans-serif';
    ictx.textAlign = "right";
    ictx.textBaseline = "middle";
    ictx.fillText(`/${indexLabel}`, 144, 38);
    indexTex = new THREE.CanvasTexture(idxCanvas);
    indexTex.colorSpace = THREE.SRGBColorSpace;
    indexTex.needsUpdate = true;
  }

  return { titleTex, indexTex };
}

export function PortalCardTitleOverlay({
  title,
  indexLabel,
  darkTheme,
  accentHex,
}: {
  readonly title: string;
  readonly indexLabel: string;
  readonly darkTheme: boolean;
  readonly accentHex: string;
}) {
  const { titleTex, indexTex } = useMemo(
    () => createCardOverlayTextures(title, indexLabel, darkTheme, accentHex),
    [title, indexLabel, darkTheme, accentHex],
  );

  useEffect(() => {
    return () => {
      titleTex?.dispose();
      indexTex?.dispose();
    };
  }, [titleTex, indexTex]);

  return (
    <group>
      {titleTex && (
        <mesh position={[-0.03, 0.59, 0.015]}>
          <planeGeometry args={[0.84, 0.24]} />
          <meshBasicMaterial map={titleTex} transparent depthWrite={false} toneMapped={false} />
        </mesh>
      )}
      {indexTex && (
        <mesh position={[0.29, -0.66, 0.015]}>
          <planeGeometry args={[0.28, 0.12]} />
          <meshBasicMaterial map={indexTex} transparent depthWrite={false} toneMapped={false} />
        </mesh>
      )}
    </group>
  );
}

function createPointLabelTexture(
  text: string,
  color: string,
  bgColor: string,
): THREE.CanvasTexture | null {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 96;
  canvas.height = 64;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = bgColor;
  if (typeof ctx.roundRect === "function") {
    ctx.beginPath();
    ctx.roundRect(10, 10, 76, 44, 14);
    ctx.fill();
  } else {
    ctx.fillRect(10, 10, 76, 44);
  }
  ctx.fillStyle = color;
  ctx.font = '700 32px "Inter", "Segoe UI", system-ui, sans-serif';
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, 48, 33);

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.needsUpdate = true;
  return tex;
}

interface SolidGeometryBundle {
  readonly pointPos: Record<string, [number, number, number]>;
  readonly edgePairs: [number, number, number][];
  readonly faceGeoms: THREE.BufferGeometry[];
  readonly sectionGeom: THREE.BufferGeometry | null;
  readonly sectionLoopPts: [number, number, number][];
  readonly planeGeom: THREE.BufferGeometry | null;
  readonly planeLoopPts: [number, number, number][];
}

function buildScaledBundle(spec: LandingSampleSpec, scale: number): SolidGeometryBundle {
  const pointPos: Record<string, [number, number, number]> = {};
  for (const pt of spec.points) {
    pointPos[pt.id] = scaleSampleVec(pt.pos, scale);
  }

  const edgePairs: [number, number, number][] = [];
  for (const edge of spec.solidEdges) {
    const a = pointPos[edge.from];
    const b = pointPos[edge.to];
    if (a && b) edgePairs.push(a, b);
  }

  const faceGeoms = spec.solidFaces
    .map((faceIds) =>
      createFanPolygonGeometry(faceIds.map((id) => pointPos[id]).filter(Boolean)),
    )
    .filter((g) => g.getAttribute("position")?.count > 0);

  const sectionVerts = spec.sectionLoop.map((id) => pointPos[id]).filter(Boolean);
  const sectionGeom = sectionVerts.length >= 3 ? createFanPolygonGeometry(sectionVerts) : null;
  const sectionLoopPts =
    sectionVerts.length >= 3 ? [...sectionVerts, sectionVerts[0]] : [];

  const planePts = spec.planeQuad.map((v) => scaleSampleVec(v, scale));
  const planeGeom = planePts.length >= 3 ? createFanPolygonGeometry(planePts) : null;
  const planeLoopPts = planePts.length >= 3 ? [...planePts, planePts[0]] : [];

  return {
    pointPos,
    edgePairs,
    faceGeoms,
    sectionGeom,
    sectionLoopPts,
    planeGeom,
    planeLoopPts,
  };
}

function disposeBundle(bundle: SolidGeometryBundle): void {
  for (const g of bundle.faceGeoms) g.dispose();
  bundle.sectionGeom?.dispose();
  bundle.planeGeom?.dispose();
}

function PointBillboard({
  pt,
  position,
  visible,
  highlighted,
  showLabel,
  darkTheme,
}: {
  readonly pt: LandingPointSpec;
  readonly position: [number, number, number];
  readonly visible: boolean;
  readonly highlighted: boolean;
  readonly showLabel: boolean;
  readonly darkTheme: boolean;
}) {
  const isSeed = pt.role === "seed";
  const isIntersection = pt.role === "intersection";
  const sphereColor = isSeed
    ? darkTheme
      ? "#62aef0"
      : "#0075de"
    : isIntersection
      ? darkTheme
        ? "#ff7a1a"
        : "#dd5b00"
      : darkTheme
        ? "#e2e8f0"
        : "#31302e";
  const labelTextColor = isSeed
    ? darkTheme
      ? "#bae6fd"
      : "#005bab"
    : isIntersection
      ? darkTheme
        ? "#fed7aa"
        : "#793400"
      : darkTheme
        ? "#f8fafc"
        : "#1e1d1b";
  const pillBg = darkTheme ? "rgba(18, 27, 51, 0.85)" : "rgba(255, 255, 255, 0.88)";

  const tex = useMemo(
    () => (showLabel && visible ? createPointLabelTexture(pt.label, labelTextColor, pillBg) : null),
    [showLabel, visible, pt.label, labelTextColor, pillBg],
  );

  useEffect(() => {
    return () => {
      tex?.dispose();
    };
  }, [tex]);

  if (!visible) return null;

  const radius = isSeed || isIntersection ? (highlighted ? 0.044 : 0.036) : 0.025;

  return (
    <group position={position} renderOrder={4}>
      <mesh>
        <sphereGeometry args={[radius, 16, 16]} />
        <meshStandardMaterial color={sphereColor} roughness={0.32} metalness={0.05} />
      </mesh>
      {tex && (
        <sprite position={[0.075, 0.085, 0.04]} scale={[0.19, 0.125, 1]}>
          <spriteMaterial map={tex} transparent depthTest={false} toneMapped={false} />
        </sprite>
      )}
    </group>
  );
}

/**
 * Renders polyhedron faces + automatic front visible edges (solid) vs back hidden edges (dashed).
 */
function ArchitecturalSolid({
  faceGeoms,
  edgePairs,
  faceColor,
  faceOpacity,
  visibleEdgeColor,
  hiddenEdgeColor,
  isInside,
  showFaces = true,
  renderHiddenDashed = true,
}: {
  readonly faceGeoms: readonly THREE.BufferGeometry[];
  readonly edgePairs: readonly [number, number, number][];
  readonly faceColor: string;
  readonly faceOpacity: number;
  readonly visibleEdgeColor: string;
  readonly hiddenEdgeColor: string;
  readonly isInside: boolean;
  readonly showFaces?: boolean;
  readonly renderHiddenDashed?: boolean;
}) {
  return (
    <>
      {showFaces &&
        faceGeoms.map((g, i) => (
          <mesh key={i} geometry={g} renderOrder={0}>
            <meshPhysicalMaterial
              color={faceColor}
              transparent
              opacity={faceOpacity}
              roughness={0.35}
              depthWrite
              polygonOffset
              polygonOffsetFactor={2}
              polygonOffsetUnits={2}
              side={THREE.DoubleSide}
            />
          </mesh>
        ))}

      {renderHiddenDashed && edgePairs.length >= 2 && (
        <Line
          points={edgePairs}
          segments
          color={hiddenEdgeColor}
          lineWidth={isInside ? 1.45 : 1.2}
          dashed
          dashSize={0.075}
          gapSize={0.055}
          transparent
          opacity={0.48}
          depthTest={false}
          renderOrder={1}
        />
      )}

      {edgePairs.length >= 2 && (
        <Line
          points={edgePairs}
          segments
          color={visibleEdgeColor}
          lineWidth={isInside ? 2.4 : 1.95}
          depthTest
          renderOrder={2}
        />
      )}
    </>
  );
}

/**
 * Spatial Portal Floor + Subtle Ambient Studio Rig giving every Portal genuine room depth.
 */
function PortalRoomStage({ floorColor }: { readonly floorColor: string }) {
  return (
    <>
      <ambientLight intensity={0.85} />
      <directionalLight position={[3.5, 5, 4]} intensity={1.0} />
      <directionalLight position={[-3, 1.5, -2]} intensity={0.35} />
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.78, 0]}>
        <circleGeometry args={[1.65, 36]} />
        <meshBasicMaterial color={floorColor} toneMapped={false} />
      </mesh>
    </>
  );
}

/**
 * Portal 01 (Left) — Sequential construction of regular triangular prism ABC.A'B'C'.
 */
export function ConstructionPortalWorld({
  stepIndex,
  isInside,
  reducedMotion,
}: {
  readonly stepIndex: number;
  readonly isInside: boolean;
  readonly reducedMotion: boolean;
}) {
  const rotRef = useRef<THREE.Group>(null);
  const spec = LANDING_PRISM_STORY_SPEC;
  const milestone = spec.milestones[Math.min(Math.max(stepIndex, 0), spec.milestones.length - 1)];
  const bundle = useMemo(() => buildScaledBundle(spec, 0.205), [spec]);

  useEffect(() => () => disposeBundle(bundle), [bundle]);

  const baseEdges = useMemo(() => {
    const out: [number, number, number][] = [];
    const baseKeys = new Set(["A-B", "B-C", "C-A"]);
    for (const e of spec.solidEdges) {
      if (baseKeys.has(`${e.from}-${e.to}`)) {
        out.push(bundle.pointPos[e.from], bundle.pointPos[e.to]);
      }
    }
    return out;
  }, [bundle, spec.solidEdges]);

  const visiblePointSet = useMemo(() => {
    if (stepIndex === 0) return new Set(["A", "B", "C", "M", "N"]);
    return new Set(milestone.visiblePoints);
  }, [stepIndex, milestone.visiblePoints]);

  const activePointSet = useMemo(
    () => new Set(milestone.activePoints),
    [milestone.activePoints],
  );

  useFrame((_state, dt) => {
    if (!rotRef.current || reducedMotion) return;
    if (!isInside) {
      rotRef.current.rotation.y += dt * 0.14;
    }
  });

  return (
    <group position={WORLD_CENTER}>
      <PortalRoomStage floorColor={V14_HERO_PORTAL_SPECS[0].floorColor} />
      <group ref={rotRef} rotation={[0.25, -0.62, 0]}>
        {stepIndex === 0 && (
          <Line
            points={bundle.edgePairs}
            segments
            color="#a39e98"
            lineWidth={1.1}
            dashed
            dashSize={0.07}
            gapSize={0.05}
          />
        )}

        <ArchitecturalSolid
          faceGeoms={bundle.faceGeoms}
          edgePairs={stepIndex === 0 ? baseEdges : bundle.edgePairs}
          faceColor="#ffffff"
          faceOpacity={0.26}
          visibleEdgeColor="#232220"
          hiddenEdgeColor="#7d7872"
          isInside={isInside}
          showFaces={stepIndex >= 1}
          renderHiddenDashed={stepIndex >= 1}
        />

        {stepIndex === 1 && bundle.pointPos.M && bundle.pointPos.N && (
          <Line
            points={[bundle.pointPos.M, bundle.pointPos.N]}
            color="#0075de"
            lineWidth={2.8}
            renderOrder={3}
          />
        )}

        {stepIndex >= 2 && bundle.planeGeom && (
          <>
            <mesh geometry={bundle.planeGeom} renderOrder={2}>
              <meshBasicMaterial
                color="#0075de"
                transparent
                opacity={stepIndex === 2 ? 0.14 : 0.18}
                depthWrite={false}
                side={THREE.DoubleSide}
              />
            </mesh>
            <Line
              points={bundle.planeLoopPts}
              color="#62aef0"
              lineWidth={1.2}
              transparent
              opacity={0.78}
              renderOrder={2}
            />
          </>
        )}

        {stepIndex >= 3 && bundle.sectionGeom && (
          <mesh geometry={bundle.sectionGeom} renderOrder={3}>
            <meshBasicMaterial
              color="#dd5b00"
              transparent
              opacity={0.34}
              depthWrite={false}
              side={THREE.DoubleSide}
            />
          </mesh>
        )}

        {stepIndex >= 2 && bundle.sectionLoopPts.length >= 4 && (
          <Line
            points={bundle.sectionLoopPts}
            color="#dd5b00"
            lineWidth={isInside ? 3.4 : 2.8}
            renderOrder={3}
          />
        )}

        {spec.points.map((pt) => (
          <PointBillboard
            key={pt.id}
            pt={pt}
            position={bundle.pointPos[pt.id]}
            visible={visiblePointSet.has(pt.id)}
            highlighted={activePointSet.has(pt.id)}
            showLabel={isInside}
            darkTheme={false}
          />
        ))}
      </group>
    </group>
  );
}

/**
 * Portal 02 (Center Focal World) — Volumetric Cube ABCD.A'B'C'D' & Hexagon Section MNEPFQ.
 */
export function ExplorationPortalWorld({
  isInside,
  reducedMotion,
}: {
  readonly isInside: boolean;
  readonly reducedMotion: boolean;
}) {
  const rotRef = useRef<THREE.Group>(null);
  const spec = LANDING_CUBE_SAMPLE;
  const bundle = useMemo(() => buildScaledBundle(spec, 0.255), [spec]);

  useEffect(() => () => disposeBundle(bundle), [bundle]);

  useFrame((_state, dt) => {
    if (!rotRef.current || reducedMotion) return;
    if (!isInside) {
      rotRef.current.rotation.y += dt * 0.18;
    }
  });

  return (
    <group position={WORLD_CENTER}>
      <PortalRoomStage floorColor={V14_HERO_PORTAL_SPECS[1].floorColor} />
      <group ref={rotRef} rotation={[0.3, 0.62, 0]}>
        <ArchitecturalSolid
          faceGeoms={bundle.faceGeoms}
          edgePairs={bundle.edgePairs}
          faceColor="#62aef0"
          faceOpacity={0.14}
          visibleEdgeColor="#f8fafc"
          hiddenEdgeColor="#7c93b8"
          isInside={isInside}
        />

        {bundle.planeGeom && (
          <>
            <mesh geometry={bundle.planeGeom} renderOrder={2}>
              <meshBasicMaterial
                color="#62aef0"
                transparent
                opacity={0.14}
                depthWrite={false}
                side={THREE.DoubleSide}
              />
            </mesh>
            <Line
              points={bundle.planeLoopPts}
              color="#62aef0"
              lineWidth={1.15}
              transparent
              opacity={0.7}
              renderOrder={2}
            />
          </>
        )}

        {bundle.sectionGeom && (
          <mesh geometry={bundle.sectionGeom} renderOrder={3}>
            <meshBasicMaterial
              color="#ff7a1a"
              transparent
              opacity={0.34}
              depthWrite={false}
              side={THREE.DoubleSide}
            />
          </mesh>
        )}

        {bundle.sectionLoopPts.length >= 4 && (
          <Line
            points={bundle.sectionLoopPts}
            color="#ff7a1a"
            lineWidth={isInside ? 3.5 : 2.9}
            renderOrder={3}
          />
        )}

        {spec.points.map((pt) => (
          <PointBillboard
            key={pt.id}
            pt={pt}
            position={bundle.pointPos[pt.id]}
            visible
            highlighted={pt.role === "seed" || pt.role === "intersection"}
            showLabel={isInside}
            darkTheme
          />
        ))}
      </group>
    </group>
  );
}

/**
 * Portal 03 (Right) — Pyramid S.ABCD sliced by oblique plane (MNP) forming pentagon MENPF.
 */
export function RelationshipsPortalWorld({
  isInside,
  reducedMotion,
  showPlane,
}: {
  readonly isInside: boolean;
  readonly reducedMotion: boolean;
  readonly showPlane: boolean;
}) {
  const rotRef = useRef<THREE.Group>(null);
  const spec = LANDING_PYRAMID_SAMPLE;
  const bundle = useMemo(() => buildScaledBundle(spec, 0.195), [spec]);

  useEffect(() => () => disposeBundle(bundle), [bundle]);

  const guidePairs = useMemo(() => {
    const a = bundle.pointPos.A;
    const b = bundle.pointPos.B;
    const c = bundle.pointPos.C;
    const d = bundle.pointPos.D;
    const s = bundle.pointPos.S;
    if (!a || !b || !c || !d || !s) return null;
    return {
      diagonals: [a, c, b, d] as [number, number, number][],
      altitude: [s, a] as [number, number, number][],
    };
  }, [bundle.pointPos]);

  useFrame((_state, dt) => {
    if (!rotRef.current || reducedMotion) return;
    if (!isInside) {
      rotRef.current.rotation.y += dt * 0.14;
    }
  });

  return (
    <group position={WORLD_CENTER}>
      <PortalRoomStage floorColor={V14_HERO_PORTAL_SPECS[2].floorColor} />
      <group ref={rotRef} rotation={[0.26, -0.5, 0]}>
        <ArchitecturalSolid
          faceGeoms={bundle.faceGeoms}
          edgePairs={bundle.edgePairs}
          faceColor="#ffffff"
          faceOpacity={0.28}
          visibleEdgeColor="#232220"
          hiddenEdgeColor="#7d8794"
          isInside={isInside}
        />

        {guidePairs && (
          <>
            <Line
              points={guidePairs.diagonals}
              segments
              color="#615d59"
              lineWidth={1.15}
              dashed
              dashSize={0.07}
              gapSize={0.05}
              renderOrder={1}
            />
            <Line
              points={guidePairs.altitude}
              color="#005bab"
              lineWidth={isInside ? 2.5 : 2.1}
              renderOrder={2}
            />
          </>
        )}

        {showPlane && bundle.planeGeom && (
          <>
            <mesh geometry={bundle.planeGeom} renderOrder={2}>
              <meshBasicMaterial
                color="#0075de"
                transparent
                opacity={0.18}
                depthWrite={false}
                side={THREE.DoubleSide}
              />
            </mesh>
            <Line
              points={bundle.planeLoopPts}
              color="#0075de"
              lineWidth={1.45}
              transparent
              opacity={0.82}
              renderOrder={2}
            />
          </>
        )}

        {bundle.sectionGeom && (
          <mesh geometry={bundle.sectionGeom} renderOrder={3}>
            <meshBasicMaterial
              color="#dd5b00"
              transparent
              opacity={0.34}
              depthWrite={false}
              side={THREE.DoubleSide}
            />
          </mesh>
        )}

        {bundle.sectionLoopPts.length >= 4 && (
          <Line
            points={bundle.sectionLoopPts}
            color="#dd5b00"
            lineWidth={isInside ? 3.5 : 2.8}
            renderOrder={3}
          />
        )}

        {spec.points.map((pt) => (
          <PointBillboard
            key={pt.id}
            pt={pt}
            position={bundle.pointPos[pt.id]}
            visible
            highlighted={pt.role === "seed" || pt.role === "intersection"}
            showLabel={isInside}
            darkTheme={false}
          />
        ))}
      </group>
    </group>
  );
}
