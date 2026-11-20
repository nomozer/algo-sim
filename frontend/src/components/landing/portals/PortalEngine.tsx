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
  Text,
  useCursor,
} from "@react-three/drei";
import { easing, geometry } from "maath";
import { suspend } from "suspend-react";
import type {} from "./r3f-jsx";

extend({ RoundedPlaneGeometry: geometry.RoundedPlaneGeometry });

export const GOLDEN_PORTAL_HEIGHT = 1.61803398875;

export type PortalTransitionPhase = "gallery" | "entering" | "inside" | "exiting";

const regularFontImport = () => import("@pmndrs/assets/fonts/inter_regular.woff");
const mediumFontImport = () => import("@pmndrs/assets/fonts/inter_medium.woff");

export function useBundledInterFonts(): { regular: string; medium: string } {
  const regular = (suspend(regularFontImport, ["axo-inter-regular"]) as { default: string })
    .default;
  const medium = (suspend(mediumFontImport, ["axo-inter-medium"]) as { default: string })
    .default;
  return { regular, medium };
}

export interface PortalFrameProps extends Omit<GroupProps, "id" | "onSelect"> {
  readonly id: string;
  readonly isActive: boolean;
  readonly onSelect: (id: string) => void;
  readonly onSettled?: (id: string, active: boolean) => void;
  readonly activationMode?: "double-click" | "single-click";
  readonly width?: number;
  readonly height?: number;
  readonly radius?: number;
  readonly resolution?: number;
  readonly dampTime?: number;
  readonly bg?: string;
  readonly reducedMotion?: boolean;
  readonly title?: string;
  readonly titleFontSize?: number;
  readonly indexLabel?: string;
  readonly subtitle?: string;
  readonly labelColor?: string;
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
  activationMode = "double-click",
  width = 1,
  height = GOLDEN_PORTAL_HEIGHT,
  radius = 0.1,
  resolution = 512,
  dampTime = 0.2,
  bg,
  reducedMotion = false,
  title,
  titleFontSize = 0.3,
  indexLabel,
  subtitle,
  labelColor = "#ffffff",
  frameOutlineColor,
  frameOutlineHoverColor,
  overlayFadeGroup = false,
  headerSlot,
  children,
  ...groupProps
}: PortalFrameProps) {
  const portal = useRef<ComponentRef<typeof MeshPortalMaterial>>(null!);
  const overlayRef = useRef<THREE.Group>(null);
  const settledTargetRef = useRef<boolean | null>(isActive ? null : false);
  const [hovered, setHovered] = useState(false);
  const { regular, medium } = useBundledInterFonts();

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

    if (overlayRef.current && overlayFadeGroup) {
      const fadeOpacity = THREE.MathUtils.clamp(1 - mat.blend * 2.4, 0, 1);
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

  const rimShape = useMemo(() => {
    if (!frameOutlineColor) return null;
    const w = width + 0.024;
    const h = height + 0.024;
    const r = Math.min(radius + 0.012, w * 0.45, h * 0.45);
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

    const inner = new THREE.Path();
    const iw = width;
    const ih = height;
    const ir = radius;
    const ix = -iw / 2;
    const iy = -ih / 2;
    inner.moveTo(ix + ir, iy);
    inner.lineTo(ix + iw - ir, iy);
    inner.quadraticCurveTo(ix + iw, iy, ix + iw, iy + ir);
    inner.lineTo(ix + iw, iy + ih - ir);
    inner.quadraticCurveTo(ix + iw, iy + ih, ix + iw - ir, iy + ih);
    inner.lineTo(ix + ir, iy + ih);
    inner.quadraticCurveTo(ix, iy + ih, ix, iy + ih - ir);
    inner.lineTo(ix, iy + ir);
    inner.quadraticCurveTo(ix, iy, ix + ir, iy);
    shape.holes.push(inner);

    const geom = new THREE.ShapeGeometry(shape, 18);
    return geom;
  }, [frameOutlineColor, width, height, radius]);

  useEffect(() => {
    return () => {
      rimShape?.dispose();
    };
  }, [rimShape]);

  const resolvedRimColor =
    hovered && !isActive && frameOutlineHoverColor
      ? frameOutlineHoverColor
      : frameOutlineColor;

  return (
    <group {...groupProps}>
      <group ref={overlayRef}>
        {title !== undefined && (
          <Text
            font={medium}
            fontSize={titleFontSize}
            anchorY="top"
            anchorX="left"
            lineHeight={0.8}
            position={[-0.375, 0.715, 0.01]}
            color={labelColor}
            material-toneMapped={false}
          >
            {title}
          </Text>
        )}
        {indexLabel !== undefined && (
          <Text
            font={regular}
            fontSize={0.1}
            anchorX="right"
            position={[0.4, -0.659, 0.01]}
            color={labelColor}
            material-toneMapped={false}
          >
            {indexLabel}
          </Text>
        )}
        {subtitle !== undefined && (
          <Text
            font={regular}
            fontSize={0.04}
            anchorX="right"
            position={[0.0, -0.677, 0.01]}
            color={labelColor}
            material-toneMapped={false}
          >
            {subtitle}
          </Text>
        )}
        {headerSlot}
      </group>

      {rimShape && resolvedRimColor && !isActive && (
        <mesh geometry={rimShape} position={[0, 0, -0.002]}>
          <meshBasicMaterial color={resolvedRimColor} toneMapped={false} />
        </mesh>
      )}

      <mesh
        name={id}
        onDoubleClick={
          activationMode === "double-click"
            ? (e) => {
                e.stopPropagation();
                onSelect(id);
              }
            : undefined
        }
        onClick={
          activationMode === "single-click"
            ? (e) => {
                e.stopPropagation();
                if (e.delta <= 6 && !isActive) {
                  onSelect(id);
                }
              }
            : undefined
        }
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(true);
        }}
        onPointerOut={() => setHovered(false)}
      >
        <roundedPlaneGeometry args={[width, height, radius]} />
        <MeshPortalMaterial
          ref={portal}
          events={isActive}
          side={THREE.DoubleSide}
          blur={0}
          resolution={resolution}
        >
          <color attach="background" args={[bg ?? "#ffffff"]} />
          {children}
        </MeshPortalMaterial>
      </mesh>
    </group>
  );
}

export interface PortalCameraRigProps {
  readonly activeId: string | null;
  readonly galleryPosition?: [number, number, number];
  readonly galleryFocus?: [number, number, number];
  readonly enterOffset?: [number, number, number];
  readonly enterFocus?: [number, number, number];
  readonly interiorPreset?: {
    readonly key: string;
    readonly offset: [number, number, number];
    readonly focus: [number, number, number];
  } | null;
  readonly reducedMotion?: boolean;
  readonly allowGalleryOrbit?: boolean;
  readonly allowWheelZoom?: boolean;
  readonly minPolarAngle?: number;
  readonly maxPolarAngle?: number;
  readonly minDistance?: number;
  readonly maxDistance?: number;
}

type CameraControlsInstance = ComponentRef<typeof CameraControls>;

export function PortalCameraRig({
  activeId,
  galleryPosition = [0, 0, 2],
  galleryFocus = [0, 0, 0],
  enterOffset = [0, 0.5, 0.25],
  enterFocus = [0, 0, -2],
  interiorPreset = null,
  reducedMotion = false,
  allowGalleryOrbit = true,
  allowWheelZoom = true,
  minPolarAngle = 0,
  maxPolarAngle = Math.PI / 2,
  minDistance,
  maxDistance,
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
  const presetKey = interiorPreset?.key ?? "";
  const presetOx = interiorPreset?.offset[0];
  const presetOy = interiorPreset?.offset[1];
  const presetOz = interiorPreset?.offset[2];
  const presetFx = interiorPreset?.focus[0];
  const presetFy = interiorPreset?.focus[1];
  const presetFz = interiorPreset?.focus[2];

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
    const interactive = activeId !== null || allowGalleryOrbit;
    const none = 0 as never;
    camControls.mouseButtons.left = interactive ? (defaults.left as never) : none;
    camControls.mouseButtons.middle = interactive ? (defaults.middle as never) : none;
    camControls.mouseButtons.right = interactive ? (defaults.right as never) : none;
    camControls.mouseButtons.wheel = interactive && allowWheelZoom ? (defaults.wheel as never) : none;
    camControls.touches.one = interactive ? (defaults.touchOne as never) : none;
    camControls.touches.two = interactive && allowWheelZoom ? (defaults.touchTwo as never) : none;
    camControls.touches.three = interactive ? (defaults.touchThree as never) : none;
  }, [controls, activeId, allowGalleryOrbit, allowWheelZoom]);

  useEffect(() => {
    const camControls = (controls ?? controlsRef.current) as CameraControlsInstance | null;
    if (!camControls) return;

    const active = activeId ? scene.getObjectByName(activeId) : undefined;
    if (active && active.parent) {
      const targetOx = presetOx ?? enterOx;
      const targetOy = presetOy ?? enterOy;
      const targetOz = presetOz ?? enterOz;
      const targetFx = presetFx ?? enterFx;
      const targetFy = presetFy ?? enterFy;
      const targetFz = presetFz ?? enterFz;
      active.parent.localToWorld(positionVec.set(targetOx, targetOy, targetOz));
      active.parent.localToWorld(focusVec.set(targetFx, targetFy, targetFz));
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
    presetKey,
    presetOx,
    presetOy,
    presetOz,
    presetFx,
    presetFy,
    presetFz,
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
