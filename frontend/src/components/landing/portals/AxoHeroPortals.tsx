import { Component, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { Canvas } from "@react-three/fiber";
import { Preload } from "@react-three/drei";
import {
  LANDING_PRISM_STORY_SPEC,
  openSampleInWorkspace,
} from "../landing-geometry-data";
import {
  GOLDEN_PORTAL_HEIGHT,
  PortalCameraRig,
  PortalFrame,
  type PortalTransitionPhase,
} from "./PortalEngine";
import {
  AXO_PORTAL_CARDS,
  ConstructionPortalWorld,
  ExplorationPortalWorld,
  PortalCardTitlePlane,
  RelationshipsPortalWorld,
  type AxoPortalId,
} from "./axo-portal-worlds";

export { AXO_PORTAL_CARDS, type AxoPortalId };

export const AXO_HERO_CAMERA_FOV = 42;

/**
 * Computes responsive gallery camera Z distance from container aspect ratio so all
 * 3 tilted portals remain completely unclipped across desktop, tablet, and 320px mobile.
 */
export function computeAxoPortalCameraZ(aspect: number): number {
  const safeAspect = Number.isFinite(aspect) && aspect > 0.35 ? aspect : 1;
  const tanHalfFov = Math.tan((AXO_HERO_CAMERA_FOV * Math.PI) / 360);
  const halfClusterWidth = 1.62;
  const halfClusterHeight = GOLDEN_PORTAL_HEIGHT * 0.54;
  const frontEdgeOffset = 0.24;
  const distV = halfClusterHeight / tanHalfFov;
  const distH = (halfClusterWidth * 1.14) / (tanHalfFov * Math.min(safeAspect, 1.85));
  return Number((frontEdgeOffset + Math.max(distV, distH)).toFixed(3));
}

type ExploreViewPreset = "default" | "top" | "section";

const EXPLORE_VIEW_PRESETS: Readonly<
  Record<
    ExploreViewPreset,
    { label: string; offset: [number, number, number]; focus: [number, number, number] }
  >
> = {
  default: { label: "Góc chuẩn", offset: [0, 0.24, 0.85], focus: [0, -0.17, -2.12] },
  top: { label: "Từ đỉnh", offset: [0.16, 1.56, -0.35], focus: [0, -0.17, -2.12] },
  section: { label: "Trực diện", offset: [-1.08, 0.36, -0.35], focus: [0, -0.17, -2.12] },
};

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

class PortalWebGLErrorBoundary extends Component<
  { readonly children: ReactNode; readonly fallback: ReactNode },
  { readonly hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true };
  }

  componentDidCatch(_error: Error, _info: ErrorInfo): void {
    // Graceful downgrade to SVG architectural fallback without breaking Landing Hero
  }

  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}

export function AxoHeroPortalFallback({
  activePortal,
}: {
  readonly activePortal: AxoPortalId | null;
}) {
  return (
    <div id="axo-portal-fallback" className="axo-portal-fallback">
      <svg
        viewBox="0 0 540 360"
        className="axo-portal-fallback-svg"
        role="img"
        aria-label="Ba cổng trải nghiệm hình học không gian Axo"
      >
        <rect
          x="26"
          y="46"
          width="144"
          height="232"
          rx="16"
          className={`axo-portal-fallback-card${activePortal === "construction" ? " is-selected" : ""}`}
        />
        <rect
          x="198"
          y="34"
          width="144"
          height="252"
          rx="16"
          className={`axo-portal-fallback-card${activePortal === "exploration" ? " is-selected" : ""}`}
        />
        <rect
          x="370"
          y="46"
          width="144"
          height="232"
          rx="16"
          className={`axo-portal-fallback-card${activePortal === "relationships" ? " is-selected" : ""}`}
        />
        {/* Portal 01 prism sketch */}
        <polygon points="98,128 62,216 134,216" className="axo-portal-fallback-stroke" />
        <polygon points="74,174 122,174 114,202 82,202" className="axo-portal-fallback-section" />
        {/* Portal 02 cube sketch */}
        <rect x="234" y="138" width="72" height="72" className="axo-portal-fallback-stroke" />
        <polygon points="234,162 270,138 306,162 292,210 248,210" className="axo-portal-fallback-section" />
        {/* Portal 03 pyramid sketch */}
        <polygon points="442,118 398,218 486,218" className="axo-portal-fallback-stroke" />
        <polygon points="414,178 442,158 470,178 462,204 422,204" className="axo-portal-fallback-section" />
      </svg>
      <div className="axo-portal-fallback-caption">
        {activePortal
          ? AXO_PORTAL_CARDS.find((c) => c.id === activePortal)?.description
          : "Chế độ rút gọn WebGL: chọn một cổng bên dưới để xem thông tin và mở bài mẫu trong Xưởng 3D."}
      </div>
      {activePortal && (
        <button
          type="button"
          className="axo-sp-btn-primary"
          onClick={() => {
            const card = AXO_PORTAL_CARDS.find((c) => c.id === activePortal);
            if (card) openSampleInWorkspace(card.sampleId);
          }}
        >
          Mở trong Xưởng 3D
        </button>
      )}
    </div>
  );
}

export function AxoHeroPortals() {
  const stageRef = useRef<HTMLDivElement | null>(null);
  const canvasWrapRef = useRef<HTMLDivElement | null>(null);

  const [activePortal, setActivePortal] = useState<AxoPortalId | null>(null);
  const [phase, setPhase] = useState<PortalTransitionPhase>("gallery");
  const [stageDims, setStageDims] = useState<{ width: number; height: number }>({
    width: 560,
    height: 440,
  });
  const [reducedMotion, setReducedMotion] = useState<boolean>(() => {
    if (typeof window === "undefined" || !window.matchMedia) return false;
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  });
  const [webglSupported] = useState<boolean>(() => detectWebGLSupport());
  const [inViewport, setInViewport] = useState<boolean>(true);
  const [tabVisible, setTabVisible] = useState<boolean>(true);
  const [mountedCanvas, setMountedCanvas] = useState<boolean>(true);

  // Portal 01 interior/gallery state
  const [prismStep, setPrismStep] = useState<number>(3);
  const [prismAutoPlay, setPrismAutoPlay] = useState<boolean>(true);

  // Portal 02 interior state
  const [explorePreset, setExplorePreset] = useState<ExploreViewPreset>("default");

  // Portal 03 interior state
  const [showPlane, setShowPlane] = useState<boolean>(true);
  const [showSection, setShowSection] = useState<boolean>(true);
  const [showAltitude, setShowAltitude] = useState<boolean>(true);

  useEffect(() => {
    setMountedCanvas(true);
    return () => setMountedCanvas(false);
  }, []);

  // Reduced motion subscription
  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onChange = () => setReducedMotion(mq.matches);
    mq.addEventListener?.("change", onChange);
    return () => mq.removeEventListener?.("change", onChange);
  }, []);

  // Responsive ResizeObserver on the 3D canvas container
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

  // Offscreen / hidden tab RAF throttling
  useEffect(() => {
    if (typeof document === "undefined") return;
    const onVis = () => setTabVisible(document.visibilityState !== "hidden");
    onVis();
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
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

  // Escape key exits active portal back to 3-portal gallery
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

  // Portal 01 calm step progression
  useEffect(() => {
    if (reducedMotion || !inViewport || !tabVisible) return;
    if (activePortal !== null && activePortal !== "construction") return;
    if (activePortal === "construction" && !prismAutoPlay) return;

    const timer = window.setInterval(() => {
      setPrismStep((prev) => (prev + 1) % LANDING_PRISM_STORY_SPEC.milestones.length);
    }, 2400);
    return () => window.clearInterval(timer);
  }, [activePortal, prismAutoPlay, reducedMotion, inViewport, tabVisible]);

  const enterPortal = useCallback(
    (id: AxoPortalId) => {
      if (id === activePortal) return;
      setPhase(reducedMotion ? "inside" : "entering");
      setActivePortal(id);
      if (id === "exploration") setExplorePreset("default");
    },
    [activePortal, reducedMotion],
  );

  const exitPortal = useCallback(() => {
    if (activePortal === null) return;
    setPhase(reducedMotion ? "gallery" : "exiting");
    setActivePortal(null);
  }, [activePortal, reducedMotion]);

  const handlePortalSettled = useCallback((id: string, isActive: boolean) => {
    if (isActive && id === activePortal) {
      setPhase("inside");
    } else if (!isActive && activePortal === null) {
      setPhase("gallery");
    }
  }, [activePortal]);

  const aspect = stageDims.width / Math.max(1, stageDims.height);
  const galleryZ = useMemo(() => computeAxoPortalCameraZ(aspect), [aspect]);
  const portalResolution = stageDims.width < 520 ? 256 : 512;
  const activeCard = AXO_PORTAL_CARDS.find((c) => c.id === activePortal) ?? null;
  const interiorPreset =
    activePortal === "exploration"
      ? {
          key: `explore-${explorePreset}`,
          offset: EXPLORE_VIEW_PRESETS[explorePreset].offset,
          focus: EXPLORE_VIEW_PRESETS[explorePreset].focus,
        }
      : null;

  const isLoopActive = inViewport && tabVisible;

  const fallbackEl = <AxoHeroPortalFallback activePortal={activePortal} />;

  return (
    <div
      ref={stageRef}
      id="axo-hero-portals-stage"
      className={`axo-portal-stage${activePortal ? " is-inside" : " is-gallery"}`}
      data-portal-state={phase}
      data-active-portal={activePortal ?? ""}
    >
      <div
        ref={canvasWrapRef}
        className={`axo-portal-canvas-wrap${activePortal ? " is-inside" : ""}`}
      >
        <div className="axo-portal-hud-top">
          {activePortal !== null ? (
            <button
              id="btn-axo-portal-back"
              type="button"
              className="axo-portal-back-btn"
              onClick={exitPortal}
            >
              <span aria-hidden="true">←</span>
              <span>Thu về 3 cổng</span>
            </button>
          ) : (
            <span className="axo-portal-gallery-hint">
              Chọn một cổng 3D để bước vào khám phá
            </span>
          )}
          {activeCard && (
            <span className="axo-portal-active-badge" aria-live="polite">
              {activeCard.shortLabel}
            </span>
          )}
        </div>

        {mountedCanvas && webglSupported ? (
          <PortalWebGLErrorBoundary fallback={fallbackEl}>
            <Canvas
              frameloop={isLoopActive ? "always" : "demand"}
              dpr={[1, 1.75]}
              camera={{ fov: AXO_HERO_CAMERA_FOV, position: [0, 0, galleryZ] }}
              gl={{ alpha: true, antialias: true, powerPreference: "high-performance" }}
              onCreated={({ gl }) => {
                const canvas = gl.domElement;
                canvas.dataset.axoPortalCanvas = "ready";
              }}
            >
              {AXO_PORTAL_CARDS.map((card) => {
                const isCardActive = activePortal === card.id;
                const accentHex =
                  card.id === "relationships" ? "#dd5b00" : "#0075de";
                return (
                  <PortalFrame
                    key={card.id}
                    id={card.id}
                    bg={card.bg}
                    position={card.position}
                    rotation={card.rotation}
                    width={1}
                    height={GOLDEN_PORTAL_HEIGHT}
                    radius={0.1}
                    resolution={portalResolution}
                    activationMode="single-click"
                    isActive={isCardActive}
                    reducedMotion={reducedMotion}
                    frameOutlineColor="#e6e6e6"
                    frameOutlineHoverColor="#0075de"
                    overlayFadeGroup
                    onSelect={(id) => enterPortal(id as AxoPortalId)}
                    onSettled={handlePortalSettled}
                    headerSlot={
                      <PortalCardTitlePlane
                        indexLabel={card.index}
                        title={card.title}
                        accentHex={accentHex}
                      />
                    }
                  >
                    <Suspense fallback={null}>
                      {card.id === "construction" && (
                        <ConstructionPortalWorld
                          stepIndex={prismStep}
                          isInside={isCardActive}
                          reducedMotion={reducedMotion}
                        />
                      )}
                      {card.id === "exploration" && (
                        <ExplorationPortalWorld
                          isInside={isCardActive}
                          reducedMotion={reducedMotion}
                        />
                      )}
                      {card.id === "relationships" && (
                        <RelationshipsPortalWorld
                          isInside={isCardActive}
                          reducedMotion={reducedMotion}
                          showPlane={showPlane}
                          showSection={showSection}
                          showAltitude={showAltitude}
                        />
                      )}
                    </Suspense>
                  </PortalFrame>
                );
              })}

              <PortalCameraRig
                activeId={activePortal}
                galleryPosition={[0, 0, galleryZ]}
                galleryFocus={[0, 0, 0]}
                enterOffset={[0, 0.24, 0.85]}
                enterFocus={[0, -0.17, -2.12]}
                interiorPreset={interiorPreset}
                reducedMotion={reducedMotion}
                allowGalleryOrbit={false}
                allowWheelZoom={false}
                minPolarAngle={0.15}
                maxPolarAngle={Math.PI * 0.62}
                minDistance={1.1}
                maxDistance={6.8}
              />
              <Preload all />
            </Canvas>
          </PortalWebGLErrorBoundary>
        ) : (
          fallbackEl
        )}

        {activePortal !== null && activeCard && (
          <div className="axo-portal-interior-bar" role="region" aria-label={activeCard.title}>
            {activePortal === "construction" && (
              <div className="axo-portal-interior-controls">
                <div className="axo-portal-step-group" role="group" aria-label="Các bước dựng hình">
                  {LANDING_PRISM_STORY_SPEC.milestones.map((m, idx) => (
                    <button
                      key={m.id}
                      type="button"
                      className={`axo-portal-chip-btn${prismStep === idx ? " is-active" : ""}`}
                      aria-pressed={prismStep === idx}
                      onClick={() => {
                        setPrismAutoPlay(false);
                        setPrismStep(idx);
                      }}
                    >
                      B{idx + 1}
                    </button>
                  ))}
                </div>
                <button
                  type="button"
                  className="axo-portal-chip-btn"
                  onClick={() => setPrismAutoPlay((v) => !v)}
                >
                  {prismAutoPlay && !reducedMotion ? "Tạm dừng" : "Tự chạy"}
                </button>
              </div>
            )}

            {activePortal === "exploration" && (
              <div className="axo-portal-interior-controls">
                <div className="axo-portal-step-group" role="group" aria-label="Góc quan sát 3D">
                  {(Object.keys(EXPLORE_VIEW_PRESETS) as ExploreViewPreset[]).map((key) => (
                    <button
                      key={key}
                      type="button"
                      className={`axo-portal-chip-btn${explorePreset === key ? " is-active" : ""}`}
                      aria-pressed={explorePreset === key}
                      onClick={() => setExplorePreset(key)}
                    >
                      {EXPLORE_VIEW_PRESETS[key].label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {activePortal === "relationships" && (
              <div className="axo-portal-interior-controls">
                <div className="axo-portal-step-group" role="group" aria-label="Lớp hình học">
                  <button
                    type="button"
                    className={`axo-portal-chip-btn${showPlane ? " is-active" : ""}`}
                    aria-pressed={showPlane}
                    onClick={() => setShowPlane((v) => !v)}
                  >
                    Mặt phẳng (MNP)
                  </button>
                  <button
                    type="button"
                    className={`axo-portal-chip-btn${showSection ? " is-active" : ""}`}
                    aria-pressed={showSection}
                    onClick={() => setShowSection((v) => !v)}
                  >
                    Thiết diện MENPF
                  </button>
                  <button
                    type="button"
                    className={`axo-portal-chip-btn${showAltitude ? " is-active" : ""}`}
                    aria-pressed={showAltitude}
                    onClick={() => setShowAltitude((v) => !v)}
                  >
                    Đường phụ &amp; SA
                  </button>
                </div>
              </div>
            )}

            <button
              id="btn-axo-portal-open-workspace"
              type="button"
              className="axo-portal-workspace-link"
              onClick={() => openSampleInWorkspace(activeCard.sampleId)}
            >
              Mở mẫu trong Xưởng 3D ↗
            </button>
          </div>
        )}
      </div>

      <div
        id="axo-portal-pill-bar"
        className="axo-portal-pill-bar"
        role="group"
        aria-label="Chọn cổng khám phá không gian 3D"
      >
        {AXO_PORTAL_CARDS.map((card) => {
          const isSelected = activePortal === card.id;
          return (
            <button
              key={card.id}
              id={`btn-axo-portal-${card.id}`}
              type="button"
              className={`axo-portal-pill-btn${isSelected ? " is-active" : ""}`}
              aria-pressed={isSelected}
              onClick={() => (isSelected ? exitPortal() : enterPortal(card.id))}
            >
              {card.shortLabel}
            </button>
          );
        })}
      </div>
    </div>
  );
}
