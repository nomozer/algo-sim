import {
  Component,
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ErrorInfo,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from "react";
import { Canvas } from "@react-three/fiber";
import { Preload } from "@react-three/drei";
import { LANDING_PRISM_STORY_SPEC } from "../landing-geometry-data";
import { HeroPortalFallbackSvg } from "./HeroPortalFallbackSvg";
import {
  GOLDEN_PORTAL_HEIGHT,
  PortalCameraRig,
  PortalFrame,
  PortalParallaxCluster,
  type PortalTransitionPhase,
} from "./PortalEngine";
import {
  ConstructionPortalWorld,
  ExplorationPortalWorld,
  PortalCardTitleOverlay,
  RelationshipsPortalWorld,
  V14_HERO_PORTAL_SPECS,
  type V14PortalId,
} from "./HeroPortalWorldsV14";

export { V14_HERO_PORTAL_SPECS, type V14PortalId };

export const AXO_V14_CAMERA_FOV = 46;

/**
 * Computes responsive gallery camera Z distance so all 3 Enter-Portals cards fill
 * the right Hero column prominently on desktop without horizontal clipping on mobile.
 */
export function computeV14PortalCameraZ(aspect: number): number {
  const safeAspect = Number.isFinite(aspect) && aspect > 0.35 ? aspect : 1;
  const tanHalfFov = Math.tan((AXO_V14_CAMERA_FOV * Math.PI) / 360);
  const halfClusterW = 1.59;
  const halfClusterH = GOLDEN_PORTAL_HEIGHT * 0.5;
  const frontEdgeOffset = 0.22;
  const distV = (halfClusterH * 1.16) / tanHalfFov;
  const distH = (halfClusterW * 1.09) / (tanHalfFov * Math.min(safeAspect, 1.75));
  return Number((frontEdgeOffset + Math.max(distV, distH)).toFixed(3));
}

function detectWebGLSupport(): boolean {
  if (typeof document === "undefined") return false;
  try {
    const canvas = document.createElement("canvas");
    return Boolean(
      canvas.getContext("webgl2", { failIfMajorPerformanceCaveat: false }) ||
        canvas.getContext("webgl", { failIfMajorPerformanceCaveat: false }) ||
        canvas.getContext("experimental-webgl"),
    );
  } catch {
    return false;
  }
}

class PortalErrorBoundary extends Component<
  { readonly children: ReactNode; readonly fallback: ReactNode },
  { readonly hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true };
  }

  componentDidCatch(_error: Error, _info: ErrorInfo): void {
    // Graceful downgrade to SVG fallback without crashing Landing V1.4
  }

  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}

export function HeroPortalStageV14() {
  const stageRef = useRef<HTMLDivElement | null>(null);
  const canvasWrapRef = useRef<HTMLDivElement | null>(null);
  const pointerRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  const [activePortal, setActivePortal] = useState<V14PortalId | null>(null);
  const [phase, setPhase] = useState<PortalTransitionPhase>("gallery");
  const [hoveredPortal, setHoveredPortal] = useState<V14PortalId | null>(null);
  const [resetNonce, setResetNonce] = useState<number>(0);
  const [stageDims, setStageDims] = useState<{ width: number; height: number }>({
    width: 634,
    height: 550,
  });
  const [reducedMotion, setReducedMotion] = useState<boolean>(() => {
    if (typeof window === "undefined" || !window.matchMedia) return false;
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  });
  const [webglSupported] = useState<boolean>(() => detectWebGLSupport());
  const [inViewport, setInViewport] = useState<boolean>(true);
  const [tabVisible, setTabVisible] = useState<boolean>(true);

  // Portal 01 step state & Portal 03 plane visibility state
  const [prismStep, setPrismStep] = useState<number>(3);
  const [prismPinned, setPrismPinned] = useState<boolean>(false);
  const [showCutPlane, setShowCutPlane] = useState<boolean>(true);

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onChange = () => setReducedMotion(mq.matches);
    mq.addEventListener?.("change", onChange);
    return () => mq.removeEventListener?.("change", onChange);
  }, []);

  useEffect(() => {
    const el = canvasWrapRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const syncDims = () => {
      const rect = el.getBoundingClientRect();
      if (rect.width > 40 && rect.height > 40) {
        setStageDims({ width: Math.round(rect.width), height: Math.round(rect.height) });
      }
    };
    syncDims();
    const ro = new ResizeObserver(syncDims);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (typeof document === "undefined") return;
    const syncVis = () => setTabVisible(document.visibilityState !== "hidden");
    syncVis();
    document.addEventListener("visibilitychange", syncVis);
    return () => document.removeEventListener("visibilitychange", syncVis);
  }, []);

  useEffect(() => {
    const el = stageRef.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries[0]) setInViewport(entries[0].isIntersecting);
      },
      { threshold: 0.05 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    if (activePortal === null || typeof window === "undefined") return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        setPhase(reducedMotion ? "gallery" : "exiting");
        setActivePortal(null);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [activePortal, reducedMotion]);

  // Gentle Portal 01 progression in gallery when visible & unpinned
  useEffect(() => {
    if (reducedMotion || !inViewport || !tabVisible || prismPinned) return;
    if (activePortal !== null && activePortal !== "construction") return;
    const timer = window.setInterval(() => {
      setPrismStep((prev) => (prev + 1) % LANDING_PRISM_STORY_SPEC.milestones.length);
    }, 2600);
    return () => window.clearInterval(timer);
  }, [activePortal, prismPinned, reducedMotion, inViewport, tabVisible]);

  const enterPortal = useCallback(
    (id: V14PortalId) => {
      if (id === activePortal) return;
      setPhase(reducedMotion ? "inside" : "entering");
      setActivePortal(id);
      setHoveredPortal(null);
      pointerRef.current = { x: 0, y: 0 };
      if (id === "construction") {
        setPrismPinned(true);
        setPrismStep(3);
      }
    },
    [activePortal, reducedMotion],
  );

  const exitPortal = useCallback(() => {
    if (activePortal === null) return;
    setPhase(reducedMotion ? "gallery" : "exiting");
    setActivePortal(null);
    setPrismPinned(false);
  }, [activePortal, reducedMotion]);

  const handleSettled = useCallback(
    (id: string, isActive: boolean) => {
      if (isActive && id === activePortal) {
        setPhase("inside");
      } else if (!isActive && activePortal === null) {
        setPhase("gallery");
      }
    },
    [activePortal],
  );

  const handlePointerMove = useCallback(
    (e: ReactPointerEvent<HTMLDivElement>) => {
      if (activePortal !== null || e.pointerType === "touch") return;
      const rect = canvasWrapRef.current?.getBoundingClientRect();
      if (!rect || rect.width <= 0 || rect.height <= 0) return;
      pointerRef.current = {
        x: ((e.clientX - rect.left) / rect.width - 0.5) * 2,
        y: ((e.clientY - rect.top) / rect.height - 0.5) * 2,
      };
    },
    [activePortal],
  );

  const handlePointerLeave = useCallback(() => {
    pointerRef.current = { x: 0, y: 0 };
    setHoveredPortal(null);
  }, []);

  const aspect = stageDims.width / Math.max(1, stageDims.height);
  const galleryZ = useMemo(() => computeV14PortalCameraZ(aspect), [aspect]);
  const portalResolution = stageDims.width < 520 ? 256 : 512;
  const activeSpec = V14_HERO_PORTAL_SPECS.find((p) => p.id === activePortal) ?? null;
  const isLoopActive = inViewport && tabVisible;

  const fallbackNode = <HeroPortalFallbackSvg selectedId={activePortal} />;

  return (
    <div
      ref={stageRef}
      className={`axo-v14-portal-root${activePortal ? " is-inside" : " is-gallery"}`}
      data-portal-state={phase}
      data-active-portal={activePortal ?? ""}
      data-hovered-portal={hoveredPortal ?? ""}
    >
      <div
        ref={canvasWrapRef}
        className={`axo-v14-portal-canvas-wrap${activePortal ? " is-inside" : ""}`}
        onPointerMove={handlePointerMove}
        onPointerLeave={handlePointerLeave}
      >
        {activePortal !== null && (
          <div className="axo-v14-portal-hud-top">
            <button
              id="btn-v14-portal-back"
              type="button"
              className="axo-v14-portal-hud-btn"
              onClick={exitPortal}
            >
              <span aria-hidden="true">←</span>
              <span>Quay lại</span>
            </button>
            <button
              id="btn-v14-portal-reset"
              type="button"
              className="axo-v14-portal-hud-btn"
              onClick={() => setResetNonce((n) => n + 1)}
            >
              Đặt lại góc nhìn
            </button>
          </div>
        )}

        {webglSupported ? (
          <PortalErrorBoundary fallback={fallbackNode}>
            <Canvas
              frameloop={isLoopActive ? "always" : "demand"}
              dpr={[1, 1.75]}
              camera={{ fov: AXO_V14_CAMERA_FOV, position: [0, 0, galleryZ] }}
              gl={{ alpha: true, antialias: true, powerPreference: "high-performance" }}
              onCreated={({ gl }) => {
                gl.domElement.dataset.v14PortalCanvas = "ready";
              }}
            >
              <PortalParallaxCluster
                activeId={activePortal}
                pointerRef={pointerRef}
                reducedMotion={reducedMotion}
              >
                {V14_HERO_PORTAL_SPECS.map((spec) => {
                  const isCardActive = activePortal === spec.id;
                  return (
                    <PortalFrame
                      key={spec.id}
                      id={spec.id}
                      bg={spec.bg}
                      position={spec.position}
                      rotation={spec.rotation}
                      width={1}
                      height={GOLDEN_PORTAL_HEIGHT}
                      radius={0.1}
                      resolution={portalResolution}
                      isActive={isCardActive}
                      reducedMotion={reducedMotion}
                      frameOutlineColor={spec.darkTheme ? "#2c3c63" : "#dfdcd6"}
                      frameOutlineHoverColor={spec.accentColor}
                      overlayFadeGroup
                      onSelect={(id) => enterPortal(id as V14PortalId)}
                      onSettled={handleSettled}
                      onHoverChange={(id, isHov) =>
                        setHoveredPortal(isHov ? (id as V14PortalId) : null)
                      }
                      headerSlot={
                        <PortalCardTitleOverlay
                          title={spec.title}
                          indexLabel={spec.index}
                          darkTheme={spec.darkTheme}
                          accentHex={spec.accentColor}
                        />
                      }
                    >
                      <Suspense fallback={null}>
                        {spec.id === "construction" && (
                          <ConstructionPortalWorld
                            stepIndex={prismStep}
                            isInside={isCardActive}
                            reducedMotion={reducedMotion}
                          />
                        )}
                        {spec.id === "exploration" && (
                          <ExplorationPortalWorld
                            isInside={isCardActive}
                            reducedMotion={reducedMotion}
                          />
                        )}
                        {spec.id === "relationships" && (
                          <RelationshipsPortalWorld
                            isInside={isCardActive}
                            reducedMotion={reducedMotion}
                            showPlane={showCutPlane}
                          />
                        )}
                      </Suspense>
                    </PortalFrame>
                  );
                })}
              </PortalParallaxCluster>

              <PortalCameraRig
                activeId={activePortal}
                resetNonce={resetNonce}
                galleryPosition={[0, 0, galleryZ]}
                galleryFocus={[0, 0, 0]}
                enterOffset={[0, 0.22, 0.68]}
                enterFocus={[0, -0.14, -2.15]}
                reducedMotion={reducedMotion}
              />
              <Preload all />
            </Canvas>
          </PortalErrorBoundary>
        ) : (
          fallbackNode
        )}

        {activePortal !== null && activeSpec && (
          <div className="axo-v14-portal-hud-bottom" role="region" aria-label={activeSpec.title}>
            {activePortal === "construction" && (
              <div className="axo-v14-portal-ctrl-row" role="group" aria-label="Bước dựng hình">
                {LANDING_PRISM_STORY_SPEC.milestones.map((m, idx) => (
                  <button
                    key={m.id}
                    type="button"
                    className={`axo-v14-portal-chip${prismStep === idx ? " is-active" : ""}`}
                    aria-pressed={prismStep === idx}
                    onClick={() => {
                      setPrismPinned(true);
                      setPrismStep(idx);
                    }}
                  >
                    B{idx + 1}
                  </button>
                ))}
              </div>
            )}
            {activePortal === "exploration" && (
              <span className="axo-v14-portal-quiet-note">
                Kéo để xoay khối lập phương &amp; lục giác MNEPFQ
              </span>
            )}
            {activePortal === "relationships" && (
              <button
                id="btn-v14-portal-toggle-plane"
                type="button"
                className={`axo-v14-portal-chip${showCutPlane ? " is-active" : ""}`}
                aria-pressed={showCutPlane}
                onClick={() => setShowCutPlane((v) => !v)}
              >
                Mặt phẳng (MNP)
              </button>
            )}
          </div>
        )}
      </div>

      {/* Visually clean keyboard triggers + mobile tap bar */}
      <div
        id="v14-portal-nav-controls"
        className="axo-v14-portal-nav-bar"
        role="group"
        aria-label="Chọn cổng 3D trong Hero"
      >
        {V14_HERO_PORTAL_SPECS.map((spec) => {
          const isSelected = activePortal === spec.id;
          return (
            <button
              key={spec.id}
              id={`btn-v14-portal-${spec.id}`}
              type="button"
              className={`axo-v14-portal-nav-pill${isSelected ? " is-active" : ""}`}
              aria-pressed={isSelected}
              onClick={() => (isSelected ? exitPortal() : enterPortal(spec.id))}
            >
              {spec.shortLabel}
            </button>
          );
        })}
      </div>
    </div>
  );
}
