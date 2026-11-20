import * as THREE from "three";
import { useEffect, useRef, useState } from "react";
import type { ComponentRef, ReactNode } from "react";
import {
  Canvas,
  extend,
  useFrame,
  useThree,
  type GroupProps,
} from "@react-three/fiber";
import {
  useCursor,
  MeshPortalMaterial,
  CameraControls,
  Gltf,
  Text,
  Preload,
} from "@react-three/drei";
import { useRoute, useLocation } from "wouter";
import { easing, geometry } from "maath";
import { suspend } from "suspend-react";
import type {} from "./r3f-jsx";

import picklesModel from "./assets/pickles_3d_version_of_hyuna_lees_illustration-transformed.glb?url";
import teaModel from "./assets/fiesta_tea-transformed.glb?url";
import stillModel from "./assets/still_life_based_on_heathers_artwork-transformed.glb?url";

extend({ RoundedPlaneGeometry: geometry.RoundedPlaneGeometry });

const regular = import("@pmndrs/assets/fonts/inter_regular.woff");
const medium = import("@pmndrs/assets/fonts/inter_medium.woff");

export const GOLDEN_PORTAL_HEIGHT = 1.61803398875;

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
    modelScale: 2,
    modelPosition: [0, -0.8, -4],
  },
] as const;

export function EnterPortalsRefApp({
  eventSource,
}: {
  eventSource?: HTMLElement;
}) {
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
      <Frame
        id="01"
        name={`pick\nles`}
        author="Omar Faruq Tawsif"
        bg="#e4cdac"
        position={[-1.15, 0, 0]}
        rotation={[0, 0.5, 0]}
      >
        <Gltf src={picklesModel} scale={8} position={[0, -0.7, -2]} useDraco="/draco/" />
      </Frame>
      <Frame id="02" name="tea" author="Omar Faruq Tawsif">
        <Gltf src={teaModel} position={[0, -2, -3]} useDraco="/draco/" />
      </Frame>
      <Frame
        id="03"
        name="still"
        author="Omar Faruq Tawsif"
        bg="#d1d1ca"
        position={[1.15, 0, 0]}
        rotation={[0, -0.5, 0]}
      >
        <Gltf src={stillModel} scale={2} position={[0, -0.8, -4]} useDraco="/draco/" />
      </Frame>
      <Rig />
      <Preload all />
    </Canvas>
  );
}

type FrameProps = Omit<GroupProps, "id"> & {
  id: string;
  name: string;
  author: string;
  bg?: string;
  width?: number;
  height?: number;
  children?: ReactNode;
};

function Frame({
  id,
  name,
  author,
  bg,
  width = 1,
  height = GOLDEN_PORTAL_HEIGHT,
  children,
  ...props
}: FrameProps) {
  const portal = useRef<ComponentRef<typeof MeshPortalMaterial>>(null!);
  const [, setLocation] = useLocation();
  const [, params] = useRoute("/item/:id");
  const [hovered, hover] = useState(false);
  useCursor(hovered);
  useFrame((_state, dt) =>
    easing.damp(portal.current, "blend", params?.id === id ? 1 : 0, 0.2, dt),
  );
  return (
    <group {...props}>
      <Text
        font={(suspend(medium) as { default: string }).default}
        fontSize={0.3}
        anchorY="top"
        anchorX="left"
        lineHeight={0.8}
        position={[-0.375, 0.715, 0.01]}
        material-toneMapped={false}
      >
        {name}
      </Text>
      <Text
        font={(suspend(regular) as { default: string }).default}
        fontSize={0.1}
        anchorX="right"
        position={[0.4, -0.659, 0.01]}
        material-toneMapped={false}
      >
        /{id}
      </Text>
      <Text
        font={(suspend(regular) as { default: string }).default}
        fontSize={0.04}
        anchorX="right"
        position={[0.0, -0.677, 0.01]}
        material-toneMapped={false}
      >
        {author}
      </Text>
      <mesh
        name={id}
        onDoubleClick={(e) => (
          e.stopPropagation(),
          setLocation("/item/" + e.object.name)
        )}
        onPointerOver={() => hover(true)}
        onPointerOut={() => hover(false)}
      >
        <roundedPlaneGeometry args={[width, height, 0.1]} />
        <MeshPortalMaterial
          ref={portal}
          events={params?.id === id}
          side={THREE.DoubleSide}
          blur={0}
          resolution={512}
        >
          <color attach="background" args={[bg ?? "#ffffff"]} />
          {children}
        </MeshPortalMaterial>
      </mesh>
    </group>
  );
}

function Rig({
  position = new THREE.Vector3(0, 0, 2),
  focus = new THREE.Vector3(0, 0, 0),
}: {
  position?: THREE.Vector3;
  focus?: THREE.Vector3;
}) {
  const { controls, scene } = useThree();
  const [, params] = useRoute("/item/:id");
  useEffect(() => {
    const active = params?.id ? scene.getObjectByName(params.id) : undefined;
    if (active && active.parent) {
      active.parent.localToWorld(position.set(0, 0.5, 0.25));
      active.parent.localToWorld(focus.set(0, 0, -2));
    }
    (controls as unknown as CameraControls | null)?.setLookAt(
      ...(position.toArray() as [number, number, number]),
      ...(focus.toArray() as [number, number, number]),
      true,
    );
  });
  return (
    <CameraControls makeDefault minPolarAngle={0} maxPolarAngle={Math.PI / 2} />
  );
}
