import { Suspense, useRef, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { Gltf, Preload } from "@react-three/drei";
import { Logo } from "@pmndrs/branding";
import {
  GOLDEN_PORTAL_HEIGHT,
  PortalCameraRig,
  PortalFrame,
} from "../../components/landing/portals/PortalEngine";

const picklesModel = new URL(
  "./assets/pickles_3d_version_of_hyuna_lees_illustration-transformed.glb",
  import.meta.url,
).href;
const teaModel = new URL("./assets/fiesta_tea-transformed.glb", import.meta.url).href;
const stillModel = new URL(
  "./assets/still_life_based_on_heathers_artwork-transformed.glb",
  import.meta.url,
).href;

export { GOLDEN_PORTAL_HEIGHT };

export interface ReferencePortalSpec {
  id: string;
  name: string;
  author: string;
  bg?: string;
  position: [number, number, number];
  rotation: [number, number, number];
  width: number;
  height: number;
  radius: number;
  modelSrc: string;
  modelScale?: number;
  modelPosition: [number, number, number];
}

export const REFERENCE_PORTAL_SPECS: readonly ReferencePortalSpec[] = [
  {
    id: "01",
    name: "pick\nles",
    author: "Omar Faruq Tawsif",
    bg: "#e4cdac",
    position: [-1.15, 0, 0],
    rotation: [0, 0.5, 0],
    width: 1,
    height: GOLDEN_PORTAL_HEIGHT,
    radius: 0.1,
    modelSrc: picklesModel,
    modelScale: 8,
    modelPosition: [0, -0.7, -2],
  },
  {
    id: "02",
    name: "tea",
    author: "Omar Faruq Tawsif",
    position: [0, 0, 0],
    rotation: [0, 0, 0],
    width: 1,
    height: GOLDEN_PORTAL_HEIGHT,
    radius: 0.1,
    modelSrc: teaModel,
    modelPosition: [0, -2, -3],
  },
  {
    id: "03",
    name: "still",
    author: "Omar Faruq Tawsif",
    bg: "#d1d1ca",
    position: [1.15, 0, 0],
    rotation: [0, -0.5, 0],
    width: 1,
    height: GOLDEN_PORTAL_HEIGHT,
    radius: 0.1,
    modelSrc: stillModel,
    modelScale: 2,
    modelPosition: [0, -0.8, -4],
  },
] as const;

export function EnterPortalsRefApp({
  eventSource,
  activeId: controlledActiveId,
  onActiveIdChange,
}: {
  eventSource?: HTMLElement;
  activeId?: string | null;
  onActiveIdChange?: (id: string | null) => void;
}) {
  const [uncontrolledActiveId, setUncontrolledActiveId] = useState<string | null>(null);
  const activeId = controlledActiveId !== undefined ? controlledActiveId : uncontrolledActiveId;
  const setActiveId = onActiveIdChange ?? setUncontrolledActiveId;

  return (
    <Canvas
      camera={{ fov: 75, position: [0, 0, 20] }}
      eventSource={
        eventSource ??
        (typeof document !== "undefined"
          ? document.getElementById("root") ?? undefined
          : undefined)
      }
      eventPrefix="client"
    >
      <color attach="background" args={["#f0f0f0"]} />
      {REFERENCE_PORTAL_SPECS.map((spec) => (
        <PortalFrame
          key={spec.id}
          id={spec.id}
          title={spec.name}
          indexLabel={`/${spec.id}`}
          subtitle={spec.author}
          bg={spec.bg}
          width={spec.width}
          height={spec.height}
          radius={spec.radius}
          position={spec.position}
          rotation={spec.rotation}
          activationMode="double-click"
          isActive={activeId === spec.id}
          onSelect={(id) => setActiveId(id)}
        >
          <Suspense fallback={null}>
            <Gltf
              src={spec.modelSrc}
              scale={spec.modelScale}
              position={spec.modelPosition}
              useDraco="/draco/"
            />
          </Suspense>
        </PortalFrame>
      ))}
      <PortalCameraRig
        activeId={activeId}
        galleryPosition={[0, 0, 2]}
        galleryFocus={[0, 0, 0]}
        enterOffset={[0, 0.5, 0.25]}
        enterFocus={[0, 0, -2]}
        allowGalleryOrbit
        allowWheelZoom
      />
      <Preload all />
    </Canvas>
  );
}

/**
 * Invariant Gate 1 Enter Portals Reference wrapper hosted inside the single SPA root
 * at `/about?preview=portal-reference` without altering reference scene geometry,
 * camera framing, interaction, or leaking global styles.
 */
export function ReferencePortalPreview() {
  const [activeId, setActiveId] = useState<string | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);

  return (
    <div
      ref={stageRef}
      id="axo-portal-reference-stage"
      className="axo-ref-portal-stage"
      data-active-portal={activeId ?? ""}
    >
      <EnterPortalsRefApp
        eventSource={stageRef.current ?? undefined}
        activeId={activeId}
        onActiveIdChange={setActiveId}
      />
      <div className="axo-ref-portal-overlay">
        <a href="https://pmnd.rs/" className="axo-ref-portal-pmndrs">
          pmnd.rs
          <br />
          dev collective
        </a>
        <div className="axo-ref-portal-date">15/06/2023</div>
        <Logo className="axo-ref-portal-logo" />
        <a
          id="btn-ref-portal-back"
          className="axo-ref-portal-back"
          href="#back"
          onClick={(e) => {
            e.preventDefault();
            setActiveId(null);
          }}
        >
          {activeId ? "< back" : "double click to enter portal"}
        </a>
      </div>
    </div>
  );
}
