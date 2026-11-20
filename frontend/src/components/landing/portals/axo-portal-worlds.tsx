import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { Line, Text } from "@react-three/drei";
import {
  LANDING_CUBE_SAMPLE,
  LANDING_PRISM_STORY_SPEC,
  LANDING_PYRAMID_SAMPLE,
  type LandingPointSpec,
  type LandingSampleSpec,
  type Vec3Tuple,
} from "../landing-geometry-data";
import { useBundledInterFonts } from "./PortalEngine";

export type AxoPortalId = "construction" | "exploration" | "relationships";

export interface AxoPortalCardSpec {
  readonly id: AxoPortalId;
  readonly index: string;
  readonly shortLabel: string;
  readonly title: string;
  readonly subtitle: string;
  readonly description: string;
  readonly bg: string;
  readonly position: [number, number, number];
  readonly rotation: [number, number, number];
  readonly sampleId: string;
}

export const AXO_PORTAL_CARDS: readonly AxoPortalCardSpec[] = [
  {
    id: "construction",
    index: "01",
    shortLabel: "01 · Dựng hình",
    title: "Dựng hình",
    subtitle: "ABC.A′B′C′ · 4 bước",
    description:
      "Theo dõi từng bước xuất hiện cạnh khối lăng trụ, ba điểm gốc M, N, P và thiết diện hình thang cân MNPQ.",
    bg: "#f6f5f4",
    position: [-1.14, 0, 0],
    rotation: [0, 0.46, 0],
    sampleId: LANDING_PRISM_STORY_SPEC.id,
  },
  {
    id: "exploration",
    index: "02",
    shortLabel: "02 · Quan sát 3D",
    title: "Quan sát 3D",
    subtitle: "Lập phương · MNEPFQ",
    description:
      "Xoay khối lập phương ABCD.A′B′C′D′ từ mọi góc nhìn để quan sát cấu trúc đỉnh, cạnh và lục giác đều MNEPFQ.",
    bg: "#f2f6fb",
    position: [0, 0, 0.04],
    rotation: [0, 0, 0],
    sampleId: LANDING_CUBE_SAMPLE.id,
  },
  {
    id: "relationships",
    index: "03",
    shortLabel: "03 · Thiết diện",
    title: "Thiết diện",
    subtitle: "S.ABCD ∩ (MNP)",
    description:
      "Quan sát mặt phẳng cắt (MNP), đường cao SO, hai giao điểm E, F và đa giác thiết diện khép kín MENPF.",
    bg: "#f9f5f0",
    position: [1.14, 0, 0],
    rotation: [0, -0.46, 0],
    sampleId: LANDING_PYRAMID_SAMPLE.id,
  },
] as const;

const WORLD_CENTER: Vec3Tuple = [0, -0.17, -2.12];

function scaleSampleVec(
  v: Vec3Tuple,
  scale: number,
  center: Vec3Tuple = WORLD_CENTER,
): [number, number, number] {
  return [
    center[0] + v[0] * scale,
    center[1] + v[1] * scale,
    center[2] + v[2] * scale,
  ];
}

function asciiLabel(label: string): string {
  return label.replace(/′/g, "'");
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

function createPortalTitleTexture(indexLabel: string, title: string, accentHex: string): THREE.CanvasTexture | null {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 176;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Subtle accent bar on left
  ctx.fillStyle = accentHex;
  if (typeof ctx.roundRect === "function") {
    ctx.beginPath();
    ctx.roundRect(26, 28, 10, 44, 5);
    ctx.fill();
  } else {
    ctx.fillRect(26, 28, 10, 44);
  }

  ctx.fillStyle = "#4b4945";
  ctx.font = '600 26px "Inter", "Segoe UI", system-ui, sans-serif';
  ctx.textBaseline = "middle";
  ctx.fillText(`/${indexLabel}`, 48, 50);

  ctx.fillStyle = "#141413";
  ctx.font = '700 54px "Inter", "Segoe UI", system-ui, sans-serif';
  ctx.textBaseline = "top";
  ctx.fillText(title, 26, 92);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;
  return texture;
}

export function PortalCardTitlePlane({
  indexLabel,
  title,
  accentHex,
}: {
  readonly indexLabel: string;
  readonly title: string;
  readonly accentHex: string;
}) {
  const texture = useMemo(
    () => createPortalTitleTexture(indexLabel, title, accentHex),
    [indexLabel, title, accentHex],
  );

  useEffect(() => {
    return () => {
      texture?.dispose();
    };
  }, [texture]);

  if (!texture) return null;

  return (
    <mesh position={[-0.02, 0.57, 0.014]}>
      <planeGeometry args={[0.84, 0.29]} />
      <meshBasicMaterial map={texture} transparent depthWrite={false} toneMapped={false} />
    </mesh>
  );
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
    pointPos[pt.id] = scaleSampleVec(pt.pos, scale, [0, 0, 0]);
  }

  const edgePairs: [number, number, number][] = [];
  for (const edge of spec.solidEdges) {
    const a = pointPos[edge.from];
    const b = pointPos[edge.to];
    if (a && b) edgePairs.push(a, b);
  }

  const faceGeoms = spec.solidFaces
    .map((faceIds) =>
      createFanPolygonGeometry(
        faceIds.map((id) => pointPos[id]).filter(Boolean),
      ),
    )
    .filter((g) => g.getAttribute("position")?.count > 0);

  const sectionVerts = spec.sectionLoop.map((id) => pointPos[id]).filter(Boolean);
  const sectionGeom = sectionVerts.length >= 3 ? createFanPolygonGeometry(sectionVerts) : null;
  const sectionLoopPts =
    sectionVerts.length >= 3 ? [...sectionVerts, sectionVerts[0]] : [];

  const planePts = spec.planeQuad.map((v) => scaleSampleVec(v, scale, [0, 0, 0]));
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

function PointMarker({
  pt,
  position,
  visible,
  highlighted,
  showLabel,
  fontUrl,
}: {
  readonly pt: LandingPointSpec;
  readonly position: [number, number, number];
  readonly visible: boolean;
  readonly highlighted: boolean;
  readonly showLabel: boolean;
  readonly fontUrl: string;
}) {
  if (!visible) return null;

  const isSeed = pt.role === "seed";
  const isIntersection = pt.role === "intersection";
  const color = isSeed ? "#0075de" : isIntersection ? "#dd5b00" : "#31302e";
  const radius = isSeed || isIntersection ? (highlighted ? 0.04 : 0.033) : 0.022;

  return (
    <group position={position}>
      <mesh>
        <sphereGeometry args={[radius, 16, 16]} />
        <meshStandardMaterial
          color={color}
          roughness={0.35}
          metalness={0.05}
          emissive={isIntersection && highlighted ? "#dd5b00" : "#000000"}
          emissiveIntensity={isIntersection && highlighted ? 0.25 : 0}
        />
      </mesh>
      {showLabel && (
        <Text
          font={fontUrl}
          fontSize={isSeed || isIntersection ? 0.095 : 0.078}
          position={[0.055, 0.055, 0.02]}
          color={isIntersection ? "#793400" : isSeed ? "#005bab" : "#31302e"}
          anchorX="left"
          anchorY="bottom"
          material-toneMapped={false}
        >
          {asciiLabel(pt.label)}
        </Text>
      )}
    </group>
  );
}

/**
 * Portal 01 — Sequential geometric construction of triangular prism ABC.A'B'C'.
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
  const { medium } = useBundledInterFonts();
  const rotRef = useRef<THREE.Group>(null);
  const spec = LANDING_PRISM_STORY_SPEC;
  const milestone = spec.milestones[Math.min(Math.max(stepIndex, 0), spec.milestones.length - 1)];

  const bundle = useMemo(() => buildScaledBundle(spec, 0.195), [spec]);

  useEffect(() => () => disposeBundle(bundle), [bundle]);

  const baseEdges = useMemo(() => {
    const basePairs: [number, number, number][] = [];
    const baseKeys = new Set(["A-B", "B-C", "C-A"]);
    for (const e of spec.solidEdges) {
      if (baseKeys.has(`${e.from}-${e.to}`)) {
        basePairs.push(bundle.pointPos[e.from], bundle.pointPos[e.to]);
      }
    }
    return basePairs;
  }, [bundle, spec.solidEdges]);

  const activeEdgePairs = useMemo(() => {
    if (stepIndex === 0) return baseEdges;
    return bundle.edgePairs;
  }, [stepIndex, baseEdges, bundle.edgePairs]);

  const visiblePointSet = useMemo(() => {
    if (stepIndex === 0) {
      return new Set(["A", "B", "C", "M", "N"]);
    }
    return new Set(milestone.visiblePoints);
  }, [stepIndex, milestone.visiblePoints]);

  const activePointSet = useMemo(
    () => new Set(milestone.activePoints),
    [milestone.activePoints],
  );

  const bcGuide = useMemo(
    () => [bundle.pointPos.M, bundle.pointPos.N, bundle.pointPos.P, bundle.pointPos.Q].filter(Boolean),
    [bundle.pointPos],
  );

  useFrame((_state, dt) => {
    if (!rotRef.current || reducedMotion) return;
    if (!isInside) {
      rotRef.current.rotation.y += dt * 0.16;
    }
  });

  return (
    <group position={WORLD_CENTER}>
      <ambientLight intensity={0.85} />
      <directionalLight position={[3, 5, 4]} intensity={0.95} />
      <directionalLight position={[-3, -2, 2]} intensity={0.3} />

      <group ref={rotRef} rotation={[0.24, -0.58, 0]}>
        {stepIndex >= 1 &&
          bundle.faceGeoms.map((g, i) => (
            <mesh key={i} geometry={g}>
              <meshPhysicalMaterial
                color="#ffffff"
                transparent
                opacity={0.28}
                roughness={0.35}
                depthWrite={false}
                side={THREE.DoubleSide}
              />
            </mesh>
          ))}

        {stepIndex === 0 && bundle.edgePairs.length >= 2 && (
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

        {activeEdgePairs.length >= 2 && (
          <Line
            points={activeEdgePairs}
            segments
            color="#31302e"
            lineWidth={isInside ? 2.2 : 1.7}
          />
        )}

        {stepIndex === 1 && bcGuide.length >= 3 && (
          <Line
            points={[bcGuide[0], bcGuide[1]]}
            color="#0075de"
            lineWidth={2.5}
          />
        )}

        {stepIndex >= 2 && bundle.planeGeom && (
          <>
            <mesh geometry={bundle.planeGeom}>
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
              lineWidth={1.1}
              transparent
              opacity={0.75}
            />
          </>
        )}

        {stepIndex >= 2 && bundle.sectionLoopPts.length >= 4 && (
          <Line
            points={bundle.sectionLoopPts}
            color="#dd5b00"
            lineWidth={isInside ? 3.2 : 2.5}
          />
        )}

        {stepIndex >= 3 && bundle.sectionGeom && (
          <mesh geometry={bundle.sectionGeom}>
            <meshBasicMaterial
              color="#dd5b00"
              transparent
              opacity={0.28}
              depthWrite={false}
              side={THREE.DoubleSide}
            />
          </mesh>
        )}

        {spec.points.map((pt) => (
          <PointMarker
            key={pt.id}
            pt={pt}
            position={bundle.pointPos[pt.id]}
            visible={visiblePointSet.has(pt.id)}
            highlighted={activePointSet.has(pt.id)}
            showLabel={isInside || pt.role === "seed" || pt.role === "intersection"}
            fontUrl={medium}
          />
        ))}
      </group>
    </group>
  );
}

/**
 * Portal 02 — Interactive 3D Cube ABCD.A'B'C'D' with regular hexagon section MNEPFQ.
 */
export function ExplorationPortalWorld({
  isInside,
  reducedMotion,
}: {
  readonly isInside: boolean;
  readonly reducedMotion: boolean;
}) {
  const { medium } = useBundledInterFonts();
  const rotRef = useRef<THREE.Group>(null);
  const spec = LANDING_CUBE_SAMPLE;
  const bundle = useMemo(() => buildScaledBundle(spec, 0.21), [spec]);

  useEffect(() => () => disposeBundle(bundle), [bundle]);

  useFrame((_state, dt) => {
    if (!rotRef.current || reducedMotion) return;
    if (!isInside) {
      rotRef.current.rotation.y += dt * 0.2;
    }
  });

  return (
    <group position={WORLD_CENTER}>
      <ambientLight intensity={0.85} />
      <directionalLight position={[4, 5, 3]} intensity={1.0} />
      <directionalLight position={[-3, 1, -3]} intensity={0.35} />

      <group ref={rotRef} rotation={[0.32, 0.62, 0]}>
        {bundle.faceGeoms.map((g, i) => (
          <mesh key={i} geometry={g}>
            <meshPhysicalMaterial
              color="#dcebfa"
              transparent
              opacity={0.24}
              roughness={0.28}
              depthWrite={false}
              side={THREE.DoubleSide}
            />
          </mesh>
        ))}

        <Line
          points={bundle.edgePairs}
          segments
          color="#31302e"
          lineWidth={isInside ? 2.2 : 1.75}
        />

        {bundle.planeGeom && (
          <>
            <mesh geometry={bundle.planeGeom}>
              <meshBasicMaterial
                color="#0075de"
                transparent
                opacity={0.1}
                depthWrite={false}
                side={THREE.DoubleSide}
              />
            </mesh>
            <Line
              points={bundle.planeLoopPts}
              color="#62aef0"
              lineWidth={1}
              transparent
              opacity={0.65}
            />
          </>
        )}

        {bundle.sectionGeom && (
          <mesh geometry={bundle.sectionGeom}>
            <meshBasicMaterial
              color="#dd5b00"
              transparent
              opacity={0.26}
              depthWrite={false}
              side={THREE.DoubleSide}
            />
          </mesh>
        )}

        {bundle.sectionLoopPts.length >= 4 && (
          <Line
            points={bundle.sectionLoopPts}
            color="#dd5b00"
            lineWidth={isInside ? 3.2 : 2.5}
          />
        )}

        {spec.points.map((pt) => (
          <PointMarker
            key={pt.id}
            pt={pt}
            position={bundle.pointPos[pt.id]}
            visible
            highlighted={pt.role === "seed" || pt.role === "intersection"}
            showLabel={isInside || pt.role === "seed" || pt.role === "intersection"}
            fontUrl={medium}
          />
        ))}
      </group>
    </group>
  );
}

/**
 * Portal 03 — Geometric Relationships: Pyramid S.ABCD sliced by plane (MNP) -> MENPF.
 */
export function RelationshipsPortalWorld({
  isInside,
  reducedMotion,
  showPlane,
  showSection,
  showAltitude,
}: {
  readonly isInside: boolean;
  readonly reducedMotion: boolean;
  readonly showPlane: boolean;
  readonly showSection: boolean;
  readonly showAltitude: boolean;
}) {
  const { medium } = useBundledInterFonts();
  const rotRef = useRef<THREE.Group>(null);
  const spec = LANDING_PYRAMID_SAMPLE;
  const bundle = useMemo(() => buildScaledBundle(spec, 0.165), [spec]);

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
      rotRef.current.rotation.y += dt * 0.16;
    }
  });

  return (
    <group position={WORLD_CENTER}>
      <ambientLight intensity={0.85} />
      <directionalLight position={[3, 5, 4]} intensity={1.0} />
      <directionalLight position={[-4, 1, 2]} intensity={0.35} />

      <group ref={rotRef} rotation={[0.28, -0.52, 0]}>
        {bundle.faceGeoms.map((g, i) => (
          <mesh key={i} geometry={g}>
            <meshPhysicalMaterial
              color="#ffffff"
              transparent
              opacity={0.28}
              roughness={0.32}
              depthWrite={false}
              side={THREE.DoubleSide}
            />
          </mesh>
        ))}

        <Line
          points={bundle.edgePairs}
          segments
          color="#31302e"
          lineWidth={isInside ? 2.2 : 1.7}
        />

        {showAltitude && guidePairs && (
          <>
            <Line
              points={guidePairs.diagonals}
              segments
              color="#615d59"
              lineWidth={1.25}
              dashed
              dashSize={0.07}
              gapSize={0.05}
            />
            <Line
              points={guidePairs.altitude}
              color="#005bab"
              lineWidth={isInside ? 2.6 : 2.1}
            />
          </>
        )}

        {showPlane && bundle.planeGeom && (
          <>
            <mesh geometry={bundle.planeGeom}>
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
              lineWidth={1.5}
              transparent
              opacity={0.8}
            />
          </>
        )}

        {showSection && bundle.sectionGeom && (
          <mesh geometry={bundle.sectionGeom}>
            <meshBasicMaterial
              color="#dd5b00"
              transparent
              opacity={0.3}
              depthWrite={false}
              side={THREE.DoubleSide}
            />
          </mesh>
        )}

        {showSection && bundle.sectionLoopPts.length >= 4 && (
          <Line
            points={bundle.sectionLoopPts}
            color="#dd5b00"
            lineWidth={isInside ? 3.4 : 2.6}
          />
        )}

        {spec.points.map((pt) => (
          <PointMarker
            key={pt.id}
            pt={pt}
            position={bundle.pointPos[pt.id]}
            visible={pt.id !== "O" || showAltitude}
            highlighted={pt.role === "seed" || pt.role === "intersection"}
            showLabel={isInside || pt.role === "seed" || pt.role === "intersection"}
            fontUrl={medium}
          />
        ))}
      </group>
    </group>
  );
}
