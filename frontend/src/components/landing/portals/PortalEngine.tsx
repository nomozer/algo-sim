import * as THREE from "three";
import { useEffect, useMemo, useRef, useState } from "react";
import type { ComponentRef, ReactNode } from "react";
import {
  extend,
  useFrame,
  useThree,
  type GroupProps,
} from "@react-three/fiber";
import {
  CameraControls,
  MeshPortalMaterial,
  useCursor,
} from "@react-three/drei";
import { easing, geometry } from "maath";
import type {} from "./r3f-jsx";

extend({ RoundedPlaneGeometry: geometry.RoundedPlaneGeometry });

export const GOLDEN_PORTAL_HEIGHT = 1.61803398875;

export type PortalTransitionPhase = "gallery" | "entering" | "inside" | "exiting";

export interface PortalFrameProps extends Omit<GroupProps, "id" | "onSelect"> {
  readonly id: string;
  readonly isActive: boolean;
  readonly onSelect: (id: string) => void;
  readonly onSettled?: (id: string, active: boolean) => void;
  readonly onHoverChange?: (id: string, hovered: boolean) => void;
  readonly width?: number;
  readonly height?: number;
  readonly radius?: number;
  readonly resolution?: number;
  readonly dampTime?: number;
  readonly bg?: string;
  readonly reducedMotion?: boolean;
  readonly frameOutlineColor?: string;
  readonly frameOutlineHoverColor?: string;
  readonly overlayFadeGroup?: boolean;
  readonly headerSlot?: ReactNode;
  readonly children?: ReactNode;
}

export function PortalFrame({
  id,
  isActive,
  onSelect,
  onSettled,
  onHoverChange,
  width = 1,
  height = GOLDEN_PORTAL_HEIGHT,
  radius = 0.1,
  resolution = 512,
  dampTime = 0.2,
  bg = "#ffffff",
  reducedMotion = false,
  frameOutlineColor,
  frameOutlineHoverColor,
  overlayFadeGroup = true,
  headerSlot,
  children,
  ...groupProps
}: PortalFrameProps) {
  const outerGroupRef = useRef<THREE.Group>(null);
  const portal = useRef<ComponentRef<typeof MeshPortalMaterial>>(null!);
  const overlayRef = useRef<THREE.Group>(null);
  const settledTargetRef = useRef<boolean | null>(isActive ? null : false);
  const [hovered, setHovered] = useState(false);

  useCursor(hovered && !isActive);

  useEffect(() => {
    settledTargetRef.current = null;
    if (isActive) {
      setHovered(false);
    }
  }, [isActive]);

  useFrame((_state, dt) => {
    const mat = portal.current;
    if (!mat) return;
    const target = isActive ? 1 : 0;

    if (reducedMotion) {
      mat.blend = target;
    } else {
      easing.damp(mat, "blend", target, dampTime, dt);
    }

    if (outerGroupRef.current) {
      const hoverZ = !isActive && hovered && !reducedMotion ? 0.065 : 0;
      if (reducedMotion) {
        outerGroupRef.current.position.z = hoverZ;
      } else {
        easing.damp(outerGroupRef.current.position, "z", hoverZ, 0.14, dt);
      }
    }

    if (overlayRef.current && overlayFadeGroup) {
      const fadeOpacity = THREE.MathUtils.clamp(1 - mat.blend * 2.5, 0, 1);
      overlayRef.current.visible = fadeOpacity > 0.02;
      overlayRef.current.traverse((obj) => {
        const mesh = obj as THREE.Mesh;
        if (mesh.material && "opacity" in mesh.material) {
          const material = mesh.material as THREE.Material & {
            opacity: number;
            transparent: boolean;
          };
          material.transparent = true;
          material.opacity = fadeOpacity;
        }
      });
    }

    if (Math.abs(mat.blend - target) < 0.015) {
      if (settledTargetRef.current !== isActive) {
        settledTargetRef.current = isActive;
        onSettled?.(id, isActive);
      }
    }
  });

  const rimGeom = useMemo(() => {
    if (!frameOutlineColor) return null;
    const w = width + 0.022;
    const h = height + 0.022;
    const r = Math.min(radius + 0.011, w * 0.45, h * 0.45);
    const shape = new THREE.Shape();
    const x = -w / 2;
    const y = -h / 2;
    shape.moveTo(x + r, y);
    shape.lineTo(x + w - r, y);
    shape.quadraticCurveTo(x + w, y, x + w, y + r);
    shape.lineTo(x + w, y + h - r);
    shape.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    shape.lineTo(x + r, y + h);
    shape.quadraticCurveTo(x, y + h, x, y + h - r);
    shape.lineTo(x, y + r);
    shape.quadraticCurveTo(x, y, x + r, y);

    const hole = new THREE.Path();
    const ix = -width / 2;
    const iy = -height / 2;
    hole.moveTo(ix + radius, iy);
    hole.lineTo(ix + width - radius, iy);
    hole.quadraticCurveTo(ix + width, iy, ix + width, iy + radius);
    hole.lineTo(ix + width, iy + height - radius);
    hole.quadraticCurveTo(ix + width, iy + height, ix + width - radius, iy + height);
    hole.lineTo(ix + radius, iy + height);
    hole.quadraticCurveTo(ix, iy + height, ix, iy + height - radius);
    hole.lineTo(ix, iy + radius);
    hole.quadraticCurveTo(ix, iy, ix + radius, iy);
    shape.holes.push(hole);

    return new THREE.ShapeGeometry(shape, 18);
  }, [frameOutlineColor, width, height, radius]);

  useEffect(() => {
    return () => {
      rimGeom?.dispose();
    };
  }, [rimGeom]);

  const resolvedRimColor =
    hovered && !isActive && frameOutlineHoverColor
      ? frameOutlineHoverColor
      : frameOutlineColor;

  return (
    <group {...groupProps}>
      <group ref={outerGroupRef}>
        <group ref={overlayRef}>{headerSlot}</group>

        {rimGeom && resolvedRimColor && !isActive && (
          <mesh geometry={rimGeom} position={[0, 0, -0.002]}>
            <meshBasicMaterial color={resolvedRimColor} toneMapped={false} />
          </mesh>
        )}

        <mesh
          name={id}
          onClick={(e) => {
            e.stopPropagation();
            if (e.delta <= 6 && !isActive) {
              onSelect(id);
            }
          }}
          onPointerOver={(e) => {
            e.stopPropagation();
            setHovered(true);
            onHoverChange?.(id, true);
          }}
          onPointerOut={() => {
            setHovered(false);
            onHoverChange?.(id, false);
          }}
        >
          <roundedPlaneGeometry args={[width, height, radius]} />
          <MeshPortalMaterial
            ref={portal}
            events={isActive}
            side={THREE.DoubleSide}
            blur={0}
            resolution={resolution}
          >
            <color attach="background" args={[bg]} />
            {children}
          </MeshPortalMaterial>
        </mesh>
      </group>
    </group>
  );
}

export interface PortalParallaxGroupProps {
  readonly activeId: string | null;
  readonly pointerRef: React.MutableRefObject<{ x: number; y: number }>;
  readonly reducedMotion: boolean;
  readonly children: ReactNode;
}

export function PortalParallaxCluster({
  activeId,
  pointerRef,
  reducedMotion,
  children,
}: PortalParallaxGroupProps) {
  const clusterRef = useRef<THREE.Group>(null);

  useFrame((_state, dt) => {
    const g = clusterRef.current;
    if (!g) return;
    const targetRotY =
      activeId === null && !reducedMotion ? pointerRef.current.x * 0.085 : 0;
    const targetRotX =
      activeId === null && !reducedMotion ? -pointerRef.current.y * 0.05 : 0;
    if (reducedMotion) {
      g.rotation.y = targetRotY;
      g.rotation.x = targetRotX;
    } else {
      easing.damp(g.rotation, "y", targetRotY, 0.18, dt);
      easing.damp(g.rotation, "x", targetRotX, 0.18, dt);
    }
  });

  return <group ref={clusterRef}>{children}</group>;
}

export interface PortalCameraRigProps {
  readonly activeId: string | null;
  readonly resetNonce?: number;
  readonly galleryPosition?: [number, number, number];
  readonly galleryFocus?: [number, number, number];
  readonly enterOffset?: [number, number, number];
  readonly enterFocus?: [number, number, number];
  readonly reducedMotion?: boolean;
  readonly minPolarAngle?: number;
  readonly maxPolarAngle?: number;
  readonly minDistance?: number;
  readonly maxDistance?: number;
}

type CameraControlsInstance = ComponentRef<typeof CameraControls>;

export function PortalCameraRig({
  activeId,
  resetNonce = 0,
  galleryPosition = [0, 0, 3.8],
  galleryFocus = [0, 0, 0],
  enterOffset = [0, 0.22, 0.68],
  enterFocus = [0, -0.12, -2.15],
  reducedMotion = false,
  minPolarAngle = 0.15,
  maxPolarAngle = Math.PI * 0.64,
  minDistance = 1.2,
  maxDistance = 6.5,
}: PortalCameraRigProps) {
  const { controls, scene } = useThree();
  const controlsRef = useRef<CameraControlsInstance | null>(null);
  const defaultActionsRef = useRef<{
    left: number;
    middle: number;
    right: number;
    wheel: number;
    touchOne: number;
    touchTwo: number;
    touchThree: number;
  } | null>(null);

  const positionVec = useMemo(() => new THREE.Vector3(), []);
  const focusVec = useMemo(() => new THREE.Vector3(), []);
  const galleryX = galleryPosition[0];
  const galleryY = galleryPosition[1];
  const galleryZ = galleryPosition[2];
  const focusX = galleryFocus[0];
  const focusY = galleryFocus[1];
  const focusZ = galleryFocus[2];
  const enterOx = enterOffset[0];
  const enterOy = enterOffset[1];
  const enterOz = enterOffset[2];
  const enterFx = enterFocus[0];
  const enterFy = enterFocus[1];
  const enterFz = enterFocus[2];

  useEffect(() => {
    const camControls = (controls ?? controlsRef.current) as CameraControlsInstance | null;
    if (!camControls) return;

    if (!defaultActionsRef.current) {
      defaultActionsRef.current = {
        left: camControls.mouseButtons.left,
        middle: camControls.mouseButtons.middle,
        right: camControls.mouseButtons.right,
        wheel: camControls.mouseButtons.wheel,
        touchOne: camControls.touches.one,
        touchTwo: camControls.touches.two,
        touchThree: camControls.touches.three,
      };
    }

    const defaults = defaultActionsRef.current;
    const isInside = activeId !== null;
    const none = 0 as never;
    // Unlock orbit only inside an active portal; keep wheel unbound so vertical page scrolling never traps users
    camControls.mouseButtons.left = isInside ? (defaults.left as never) : none;
    camControls.mouseButtons.middle = isInside ? (defaults.middle as never) : none;
    camControls.mouseButtons.right = isInside ? (defaults.right as never) : none;
    camControls.mouseButtons.wheel = none;
    camControls.touches.one = isInside ? (defaults.touchOne as never) : none;
    camControls.touches.two = none;
    camControls.touches.three = none;
  }, [controls, activeId]);

  useEffect(() => {
    const camControls = (controls ?? controlsRef.current) as CameraControlsInstance | null;
    if (!camControls) return;

    const active = activeId ? scene.getObjectByName(activeId) : undefined;
    if (active && active.parent) {
      active.parent.localToWorld(positionVec.set(enterOx, enterOy, enterOz));
      active.parent.localToWorld(focusVec.set(enterFx, enterFy, enterFz));
    } else {
      positionVec.set(galleryX, galleryY, galleryZ);
      focusVec.set(focusX, focusY, focusZ);
    }

    void camControls.setLookAt(
      positionVec.x,
      positionVec.y,
      positionVec.z,
      focusVec.x,
      focusVec.y,
      focusVec.z,
      !reducedMotion,
    );
  }, [
    controls,
    scene,
    activeId,
    resetNonce,
    galleryX,
    galleryY,
    galleryZ,
    focusX,
    focusY,
    focusZ,
    enterOx,
    enterOy,
    enterOz,
    enterFx,
    enterFy,
    enterFz,
    reducedMotion,
    positionVec,
    focusVec,
  ]);

  return (
    <CameraControls
      ref={controlsRef}
      makeDefault
      minPolarAngle={minPolarAngle}
      maxPolarAngle={maxPolarAngle}
      minDistance={minDistance}
      maxDistance={maxDistance}
    />
  );
}
