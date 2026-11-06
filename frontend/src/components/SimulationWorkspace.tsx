import {
  Suspense,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ComponentType,
  type CSSProperties,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from "react";
import { DOMAIN_BADGE, headerSubtitle } from "./header-identity";
import { getSimulation } from "../simulations/registry";
import {
  effectiveVisualMode,
  learnerFacingModes,
  rendererFor,
} from "../simulations/renderer";
import type {
  ExploreCapability,
  Narration,
  PresentationEntry,
  VisualMode,
  WorkspaceProps,
} from "../simulations/types";
import { useAppStore } from "../state/store";
import { historyStore, touchServerHistory } from "../state/history";
import { recoverCatalogScene3D } from "../data/offline-catalog";
import { GEOMETRY_SAMPLES } from "../data/geometry-samples";
import { AssignDialog } from "./AssignDialog";
import { IconAxoLogo } from "./icons";
import { TEN_TRANG } from "./TopNav";
import { LiveClassStrip } from "./LiveClassStrip";
import { SimulationInspector } from "./SimulationInspector";
import { AxoScrollbar } from "./AxoScrollbar";
import { useClassroomStore } from "../state/classroom";
import {
  CHUA_THAY,
  apDungPhien,
  type ClassroomSession,
  type SeenMarks,
} from "../state/classroom-sync";
import { useAuthStore } from "../state/auth";
import { veKhongGian } from "../simulations/domains/geometry/scene3d-chart";
import {
  anchorOfGeometryStep,
  attachHybridViewToScene,

  clampStep,
  classifySceneEntityProvenance,
  coherentFormula,
  geometryAnchor,
  geometryFocusAt,
  geometryNarrationAt,
  geometryStepCount,
  hienBieuThucDaiLuong,
  hopLeScene3D,
  inspectScene3DPayloadIntegrity,
  learnerTextIsSafe,
  objectsAt,
  phanTichToanHocCuaCanh,
  PLAYBACK_INTERVAL_MS,
  prefersReducedMotion,
  tapKetQuaCuoi,
  type RouteDSimulationSummary,
  type Scene3D,
} from "../simulations/domains/geometry/scene3d-model";
import {
  buildPedagogicalConstructionPlan,
  buildStepEntityGroups,
  buildVerifiedObjectTooltip,
  formatCycleNotation,
  getSemanticConstructionContract,
  inspectAxialCurvedOrthogonality,
  isExplicitOxyzCoordinateScene,
  normalizeCylinderEnvelopeTitle,
  preferredPointOrderForPolygon,
  registerExactSceneOrigin,
  resolveStudentObjectPresentation,
  verifySceneMathematicalConsistency,
} from "../simulations/domains/geometry/scene3d-semantic-policy";
import {
  DEFAULT_ANNOTATION_VIEW,
  givenQuantitiesSummary,
  quantitySources,
  type AnnotationView,
} from "../simulations/domains/geometry/scene3d-annotations";
import {
  auxiliaryHiddenAt,
} from "../simulations/domains/geometry/scene3d-auxiliary";
import {
  buildPedagogicalStepNarration,
  evaluateStudentPresentationPolicy,
  sanitizeStudentDescriptorText,
} from "../simulations/domains/geometry/scene3d-student-presentation-policy";
import {
  clearIsolate,
  directDependencies,
  hide,
  isolate,
  select,
  show,
  showAll,
  taoTrangThai,
  type InteractionState,
} from "../simulations/domains/geometry/interaction-state";
import {
  entitiesPresentAt,
  sectionDetails,
  withSubEntities,
} from "../simulations/domains/geometry/scene3d-subentities";
import { AxoErrorExperience } from "./AxoErrorExperience";
import { ErrorBoundary } from "./ErrorBoundary";
import {
  GEOMETRY_WEBGL_FALLBACK,
  MathDisplay,
  Scene3DWorkspace,
  type SceneCameraPose,
  type WebglLifecyclePhase,
} from "../simulations/domains/geometry/scene3d-view";
import {
  loadLearnerRecoverySnapshot,
  saveLearnerRecoverySnapshot,
} from "../state/learner-recovery-snapshot";
import {
  cauQuanSat,
  hybridTaiBuoc,
  hybridViewCua,
  type HybridPreviewView,
} from "../simulations/domains/geometry/hybrid-preview-adapter";

/**
 * Workspace V6.2 trong Axo V2.7 (Phase C — P3/P4/P5).
 *
 * Bảo toàn 100% `Scene3DWorkspace` (Three.js/WebGL thực tế của AlgoSim) bên trong
 * khung `.stage-3d#stage-3d-box`, kết hợp với:
 * - Header Workspace Axo V2.7 (`.axo-header`: Logo, `#header-prob-div`, `#top-prob-title`,
 *   Navigation Capsule `#nav-home` / `#nav-library` / `#nav-history`, và `#btn-header-change-prob` `Đổi đề toán`).
 * - Playback P-A Capsule (`.playback-pa-wrap#playback-pa-box` > `.playback-pa-capsule#playback-pa-capsule`)
 *   đồng bộ 2 chiều với bước dựng hình của `Scene3D`.
 * - Thanh công cụ 3D nổi kéo thả (`.toolbar-3d-floating#floating-toolbar-3d` + `#tb-display-pop` + `#toolbar-3d-collapsed`)
 *   nối trực tiếp vào state hiển thị của `Scene3D` (X-ray, Bung mặt/Tách khối, Đặt lại góc nhìn, Nhãn đỉnh, Kích thước,
 *   Góc vuông, Nét đứt, Hình phụ, Lưới nền).
 * - Khung Học tập hợp nhất (`aside.study-dock#ws-dock`) gồm Đề bài (có thể thu gọn/mở rộng),
 *   Thẻ thông tin đối tượng đang chọn (`#dock-context-object-mount`), và danh sách Các bước dựng hình (`#dock-steps-ul`).
 */
export interface ViewerRecoveryState {
  phase: "recovering" | "failed";
  reason: "webgl_context_lost" | "webgl_unavailable" | "render_crash";
  attempt: number;
  maxAttempts: number;
}

const EMPTY_SAFE_SCENE: Scene3D = Object.freeze({
  objects: [],
  events: [],
  free_objects: [],
}) as unknown as Scene3D;

export function AxoViewerRecoverySurface({
  state,
  onSecondaryRetry,
}: {
  state: ViewerRecoveryState;
  onSecondaryRetry?: () => void;
}) {
  const isRecovering = state.phase === "recovering";
  const title = isRecovering ? "Đang khôi phục mô phỏng" : "Khung 3D tạm gián đoạn";
  const detail = isRecovering
    ? "Khung vẽ không gian đang khởi tạo lại trong khi đề bài và các bước dựng vẫn được giữ nguyên."
    : state.reason === "webgl_unavailable"
      ? GEOMETRY_WEBGL_FALLBACK
      : "Không thể tự khôi phục khung vẽ 3D sau các lần thử an toàn; em vẫn đọc được đề bài và các bước dựng bên cạnh.";
  const statusText = isRecovering
    ? `Đang khôi phục ngữ cảnh dựng hình (lần ${Math.max(1, state.attempt)}/${Math.max(1, state.maxAttempts)})…`
    : onSecondaryRetry
      ? "Tự động khôi phục đã tạm dừng; em có thể thử khôi phục thủ công khi sẵn sàng."
      : "Đã dừng tự động thử lại để tránh lặp lỗi.";

  return (
    <div
      className={`axo-viewer-recovery is-${state.phase}`}
      role={isRecovering ? "status" : "alert"}
      aria-live="polite"
      data-viewer-recovery-phase={state.phase}
      data-viewer-fault={state.reason}
    >
      <div className="axo-viewer-recovery-glyph" aria-hidden="true">
        <svg viewBox="0 0 40 40" fill="none">
          <polygon
            points="20,5 34,13 34,27 20,35 6,27 6,13"
            stroke="currentColor"
            strokeWidth="1.4"
            strokeLinejoin="round"
          />
          <polyline
            points="6,13 20,21 34,13"
            stroke="currentColor"
            strokeWidth="1.25"
            strokeLinejoin="round"
            opacity="0.72"
          />
          <line
            x1="20"
            y1="21"
            x2="20"
            y2="35"
            stroke="currentColor"
            strokeWidth="1.25"
            strokeDasharray="2.5 2.5"
            opacity="0.65"
          />
        </svg>
      </div>
      <h3 className="axo-viewer-recovery-title">{title}</h3>
      <p className="axo-viewer-recovery-desc">{detail}</p>
      <p className="axo-viewer-recovery-status">{statusText}</p>
      {!isRecovering && onSecondaryRetry ? (
        <div className="axo-viewer-recovery-actions">
          <button
            type="button"
            className="btn-utility axo-viewer-recovery-retry"
            onClick={onSecondaryRetry}
          >
            Khôi phục khung 3D
          </button>
        </div>
      ) : null}
    </div>
  );
}

export function AxoWorkspaceV62({
  scene: sceneKhung,
  de,
  deSource,
  tieuDe,
  quayLai,
  phien,
  onFocus,
  daiLop,
  daiLopTomTat,
  hybrid,
  routeDSimulation,
  initialStep,
  initialSelectedId = null,
  initialDockCollapsed,
  initialTbCollapsed = false,
  initialDisplayPopOpen = false,
  initialGeoCustomOpen = false,
  initialPaExpanded = false,
  unavailableOverride = null,
}: {
  scene: Scene3D;
  de?: string | null;
  /** Nguồn của `de` do `SimulationWorkspace` xác định: đề người học, đề danh mục, hoặc thiếu đề gốc. */
  deSource?: "learner" | "catalog" | "missing";
  tieuDe?: string | null;
  quayLai?: { nhan: string; onClick: () => void } | null;
  phien?: ClassroomSession | null;
  onFocus?: (selectedId: string | null, action: string) => void;
  daiLop?: ReactNode;
  daiLopTomTat?: ReactNode;
  hybrid?: HybridPreviewView | null;
  routeDSimulation?: RouteDSimulationSummary | null;
  initialStep?: number;
  initialSelectedId?: string | null;
  initialDockCollapsed?: boolean;
  initialTbCollapsed?: boolean;
  initialDisplayPopOpen?: boolean;
  initialGeoCustomOpen?: boolean;
  initialPaExpanded?: boolean;
  unavailableOverride?: {
    title: string;
    detail: string;
    onGoHome?: () => void;
  } | null;
}) {
  const setView = useAppStore((s) => s.setView);
  const goHome = useAppStore((s) => s.goHome);
  const activeHistoryId = useAppStore((s) => s.activeHistoryId);
  const activeSampleId = useAppStore((s) => s.activeSampleId);

  const problemSnapshotKey = useMemo(() => {
    if (activeSampleId) return `sample:${activeSampleId}`;
    if (activeHistoryId) return `history:${activeHistoryId}`;
    const cleanTitle = (tieuDe ?? "").trim().slice(0, 64);
    const cleanStatement = (de ?? "").trim().slice(0, 80);
    return cleanTitle || cleanStatement ? `inline:${cleanTitle}|${cleanStatement}` : "";
  }, [activeSampleId, activeHistoryId, tieuDe, de]);

  const preparedSceneResult = useMemo(() => {
    if (unavailableOverride) {
      return {
        integrityError: unavailableOverride.detail,
        mathVerification: { valid: true, contradictions: [] as { id: string; title: string; explanation: string }[] },
        pedPlan: buildPedagogicalConstructionPlan(EMPTY_SAFE_SCENE),
        displayScene: EMPTY_SAFE_SCENE,
        semanticContract: getSemanticConstructionContract(EMPTY_SAFE_SCENE),
      };
    }
    const integrity = inspectScene3DPayloadIntegrity(sceneKhung);
    if (!integrity.valid) {
      return {
        integrityError: integrity.reason,
        mathVerification: { valid: true, contradictions: [] as { id: string; title: string; explanation: string }[] },
        pedPlan: buildPedagogicalConstructionPlan(EMPTY_SAFE_SCENE),
        displayScene: EMPTY_SAFE_SCENE,
        semanticContract: getSemanticConstructionContract(EMPTY_SAFE_SCENE),
      };
    }
    try {
      attachHybridViewToScene(sceneKhung, hybrid);

      const mv = verifySceneMathematicalConsistency(sceneKhung);
      const plan = buildPedagogicalConstructionPlan(withSubEntities(sceneKhung));
      const disp = registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);
      const semContract = getSemanticConstructionContract(disp);
      return {
        integrityError: null as string | null,
        mathVerification: mv,
        pedPlan: plan,
        displayScene: disp,
        semanticContract: semContract,
      };
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("[Scene3DPipeline:invalid_scene_data]", err);
      return {
        integrityError: "Dữ liệu tọa độ hoặc quan hệ của mô hình 3D không nhất quán nên Axo dừng dựng hình để tránh minh họa sai.",
        mathVerification: { valid: true, contradictions: [] as { id: string; title: string; explanation: string }[] },
        pedPlan: buildPedagogicalConstructionPlan(EMPTY_SAFE_SCENE),
        displayScene: EMPTY_SAFE_SCENE,
        semanticContract: getSemanticConstructionContract(EMPTY_SAFE_SCENE),
      };
    }
  }, [sceneKhung, hybrid, unavailableOverride]);

  const invalidSceneReason = preparedSceneResult.integrityError;
  const mathVerification = preparedSceneResult.mathVerification;
  const pedPlan = preparedSceneResult.pedPlan;
  const scene = preparedSceneResult.displayScene;
  const semanticContract = preparedSceneResult.semanticContract;
  const day = scene;
  const dsBuoc = pedPlan.steps;
  const tong = Math.max(1, dsBuoc.length);

  const loaiCanh = useMemo((): {
    key: "sphere" | "pyramid" | "cylinder" | "cone" | "solid";
    label: string;
  } => {
    for (const o of day.objects) {
      const oc = semanticContract.objectsById.get(o.id);
      if (oc?.geometricType !== "curved_solid") continue;
      if (o.curved_kind === "ball") return { key: "sphere", label: "Mặt cầu" };
      if (o.curved_kind === "cylinder") return { key: "cylinder", label: "Hình trụ" };
      if (o.curved_kind === "cone") return { key: "cone", label: "Hình nón" };
    }
    const solObj = day.objects.find((o) => semanticContract.objectsById.get(o.id)?.geometricType === "polyhedron_solid");
    if (solObj) {
      const hasTopFace = day.objects.some(
        (o) => semanticContract.objectsById.get(o.id)?.semanticRole === "TOP_FACE",
      );
      const vCount = solObj.vertex_ids?.length ?? solObj.vertices?.length ?? 0;
      const faces = solObj.faces ?? [];
      const quadFaceCount = faces.filter((f) => f.length === 4).length;
      const isTopologicalPrism =
        vCount >= 6
        && vCount % 2 === 0
        && faces.length === vCount / 2 + 2
        && quadFaceCount >= vCount / 2;
      if (
        solObj.shape_class === "PRISM_LIKE"
        || solObj.shape_class === "BOX_LIKE"
        || hasTopFace
        || isTopologicalPrism
      ) {
        return { key: "solid", label: "Hình lăng trụ" };
      }
      if (solObj.shape_class === "FRUSTUM_LIKE") {
        return { key: "pyramid", label: "Hình chóp cụt" };
      }
      const hasBaseFace = day.objects.some(
        (o) => semanticContract.objectsById.get(o.id)?.semanticRole === "BASE_FACE",
      );
      if (!hasBaseFace && vCount === 4 && (faces.length === 0 || faces.length === 4)) {
        return { key: "solid", label: "Tứ diện" };
      }
      return { key: "pyramid", label: "Hình chóp" };
    }
    return { key: "solid", label: "Khối 3D" };
  }, [day, semanticContract]);

  const timChiSoBuocSuPham = (anchorStep: number): number => {
    const exactOrRange = dsBuoc.findIndex(
      (b) => anchorStep >= b.startAnchor && anchorStep <= b.anchor,
    );
    if (exactOrRange >= 0) return exactOrRange;
    for (let i = dsBuoc.length - 1; i >= 0; i -= 1) {
      if (dsBuoc[i].anchor <= anchorStep) return i;
    }
    return 0;
  };
  const resolvePedagogicalStepAnchor = (rawStep: number): number => {
    if (dsBuoc.length === 0) return geometryAnchor(day, rawStep);
    const clamped = clampStep(day, rawStep);
    const idx = timChiSoBuocSuPham(clamped);
    return dsBuoc[idx]?.anchor ?? geometryAnchor(day, rawStep);
  };

  const initialRecoveredSnapshot = useMemo(
    () => (problemSnapshotKey ? loadLearnerRecoverySnapshot(problemSnapshotKey) : null),
    [problemSnapshotKey],
  );

  const resolveInitialAnchor = (snap = initialRecoveredSnapshot) => {
    if (typeof initialStep === "number") {
      return resolvePedagogicalStepAnchor(initialStep);
    }
    if (snap && snap.stepIndex >= 0 && dsBuoc.length > 0) {
      const idx = Math.min(snap.stepIndex, Math.max(0, dsBuoc.length - 1));
      return dsBuoc[idx]?.anchor ?? anchorOfGeometryStep(day, 0);
    }
    if (activeHistoryId) {
      const saved = historyStore.list().find((h) => h.id === activeHistoryId);
      if (saved && typeof saved.lastCursor === "number" && saved.lastCursor >= 0) {
        const idx = Math.min(saved.lastCursor, Math.max(0, dsBuoc.length - 1));
        return dsBuoc[idx]?.anchor ?? anchorOfGeometryStep(day, 0);
      }
    }
    return (
      dsBuoc[dsBuoc.length - 1]?.anchor ??
      anchorOfGeometryStep(day, Math.max(0, geometryStepCount(day) - 1))
    );
  };

  const isSelectableAtAnchor = (id: string | null | undefined, anchor: number): id is string => {
    if (!id) return false;
    const present = entitiesPresentAt(day, anchor, objectsAt);
    if (!present.has(id)) return false;
    const obj = day.objects.find((o) => o.id === id);
    if (obj?.type === "quantity") {
      if ((obj.depends ?? []).some((depId) => !present.has(depId))) return false;
      if (obj.annotation?.subject_ids?.length) {
        const summaryItem = givenQuantitiesSummary(day, anchor).find((g) => g.id === id);
        if (summaryItem?.status === "pending_step") return false;
      }
    }
    return true;
  };

  const resolveInitialSelectedId = (
    snap = initialRecoveredSnapshot,
    anchor = resolveInitialAnchor(snap),
  ): string | null => {
    if (initialSelectedId !== null) {
      return isSelectableAtAnchor(initialSelectedId, anchor) ? initialSelectedId : null;
    }
    if (snap?.selectedId && isSelectableAtAnchor(snap.selectedId, anchor)) {
      return snap.selectedId;
    }
    return null;
  };

  const [tt, setTt] = useState<InteractionState>(() => ({
    ...taoTrangThai(),
    current_step: resolveInitialAnchor(),
    selected_id: resolveInitialSelectedId(),
  }));
  const [moc, setMoc] = useState<SeenMarks>(CHUA_THAY);
  const [undoStack, setUndoStack] = useState<
    Array<{
      tt: InteractionState;
      xray: boolean;
      hinhPhu: boolean;
      luoi: boolean;
      showShell: boolean;
      showVertexLabels: boolean;
      showPlane: boolean;
      showSection: boolean;
      showAxes: boolean;
      showDimensionLabels: boolean;
      showRightAngles: boolean;
      showDashedHidden: boolean;
      shellOpacityPct: number;
      planeOpacityPct: number;
    }>
  >([]);
  const [dangPhat, setDangPhat] = useState(false);
  const [fitToken, setFitToken] = useState(0);
  const [replayNonce, setReplayNonce] = useState(0);
  const [xray, setXray] = useState(() => initialRecoveredSnapshot?.display.xray ?? false);
  const [hinhPhu, setHinhPhu] = useState(() => initialRecoveredSnapshot?.display.auxiliaryShown ?? false);
  const [luoi, setLuoi] = useState(() => initialRecoveredSnapshot?.display.gridShown ?? true);
  const [xem, setXem] = useState<AnnotationView>(DEFAULT_ANNOTATION_VIEW);

  const [showShell, setShowShell] = useState(() => initialRecoveredSnapshot?.display.showShell ?? true);
  const [showVertexLabels, setShowVertexLabels] = useState(() => initialRecoveredSnapshot?.display.showVertexLabels ?? true);
  const [showPlane, setShowPlane] = useState(() => initialRecoveredSnapshot?.display.showPlane ?? true);
  const [showSection, setShowSection] = useState(() => initialRecoveredSnapshot?.display.showSection ?? true);
  const [showAxes, setShowAxes] = useState(() => initialRecoveredSnapshot?.display.showAxes ?? false);
  const [showDimensionLabels, setShowDimensionLabels] = useState(() => initialRecoveredSnapshot?.display.showDimensionLabels ?? true);
  const [showRightAngles, setShowRightAngles] = useState(() => initialRecoveredSnapshot?.display.showRightAngles ?? true);
  const [showDashedHidden, setShowDashedHidden] = useState(() => initialRecoveredSnapshot?.display.showDashedHidden ?? true);

  const [shellOpacityPct, setShellOpacityPct] = useState(() => initialRecoveredSnapshot?.display.shellOpacityPct ?? 12);
  const [planeOpacityPct, setPlaneOpacityPct] = useState(() => initialRecoveredSnapshot?.display.planeOpacityPct ?? 8);
  const isGeoParamsDirty = shellOpacityPct !== 12 || planeOpacityPct !== 8;

  const [dockCollapsed, setDockCollapsed] = useState(
    () => initialDockCollapsed ?? initialRecoveredSnapshot?.dockCollapsed ?? false,
  );
  const [paExpanded, setPaExpanded] = useState(initialPaExpanded);
  const [tbCollapsed, setTbCollapsed] = useState(initialTbCollapsed);
  const [displayPopOpen, setDisplayPopOpen] = useState(initialDisplayPopOpen);
  const [expandedEvidenceStep, setExpandedEvidenceStep] = useState<number | null>(null);
  const [geoCustomOpen, setGeoCustomOpen] = useState(initialGeoCustomOpen);
  const [tbPos, setTbPos] = useState<{ x: number; y: number } | null>(null);
  const [tbDragging, setTbDragging] = useState(false);
  const [geoCustomPos, setGeoCustomPos] = useState<{ x: number; y: number } | null>(null);
  const [geoCustomDragging, setGeoCustomDragging] = useState(false);
  const [moreEntitiesOpen, setMoreEntitiesOpen] = useState(false);
  const [savedCameraPose, setSavedCameraPose] = useState<SceneCameraPose | null>(
    () => initialRecoveredSnapshot?.camera ?? null,
  );
  const latestCameraPoseRef = useRef<SceneCameraPose | null>(initialRecoveredSnapshot?.camera ?? null);

  const stageRef = useRef<HTMLElement>(null);
  const toolbarRef = useRef<HTMLDivElement>(null);
  const geoCustomPopRef = useRef<HTMLDivElement>(null);
  const stepsListRef = useRef<HTMLUListElement>(null);
  const dockScrollRef = useRef<HTMLDivElement>(null);

  const [stageWebglFailed, setStageWebglFailed] = useState(false);
  const [viewerBoundaryCrashed, setViewerBoundaryCrashed] = useState(false);
  const viewerUnavailable = stageWebglFailed || viewerBoundaryCrashed;
  const stageControlsInteractive =
    invalidSceneReason === null && mathVerification.valid && !viewerUnavailable;
  const [webglLifecycle, setWebglLifecycle] = useState<{
    phase: WebglLifecyclePhase;
    attempt: number;
    maxAttempts: number;
  }>({ phase: "healthy", attempt: 0, maxAttempts: 2 });
  const webglLifecycleRef = useRef(webglLifecycle);
  webglLifecycleRef.current = webglLifecycle;
  const [webglStageAttempt, setWebglStageAttempt] = useState(0);
  const [viewerMountGen, setViewerMountGen] = useState(0);
  const hasInAppNavigation = useAppStore((s) => s.hasInAppNavigation);
  const isInitialSceneMountRef = useRef(true);
  const isInitialResetSyncRef = useRef(true);

  useEffect(() => {
    if (isInitialResetSyncRef.current) {
      isInitialResetSyncRef.current = false;
      return;
    }
    setViewerBoundaryCrashed(false);
    setStageWebglFailed(false);
  }, [problemSnapshotKey, webglStageAttempt]);

  useEffect(() => {
    if (isInitialSceneMountRef.current) {
      isInitialSceneMountRef.current = false;
      return;
    }
    const snap = problemSnapshotKey ? loadLearnerRecoverySnapshot(problemSnapshotKey) : null;
    const startAnchor = resolveInitialAnchor(snap);
    setTt({
      ...taoTrangThai(),
      current_step: startAnchor,
      selected_id: resolveInitialSelectedId(snap, startAnchor),
    });
    setDangPhat(false);
    setXray(snap?.display.xray ?? false);
    setHinhPhu(snap?.display.auxiliaryShown ?? false);
    setLuoi(snap?.display.gridShown ?? true);
    setShowShell(snap?.display.showShell ?? true);
    setShowVertexLabels(snap?.display.showVertexLabels ?? true);
    setShowPlane(snap?.display.showPlane ?? true);
    setShowSection(snap?.display.showSection ?? true);
    setShowAxes(snap?.display.showAxes ?? false);
    setShowDimensionLabels(snap?.display.showDimensionLabels ?? true);
    setShowRightAngles(snap?.display.showRightAngles ?? true);
    setShowDashedHidden(snap?.display.showDashedHidden ?? true);
    setDisplayPopOpen(false);
    setGeoCustomOpen(false);
    setShellOpacityPct(snap?.display.shellOpacityPct ?? 12);
    setPlaneOpacityPct(snap?.display.planeOpacityPct ?? 8);
    if (initialDockCollapsed === undefined && snap) {
      setDockCollapsed(snap.dockCollapsed);
    }
    setSavedCameraPose(snap?.camera ?? null);
    latestCameraPoseRef.current = snap?.camera ?? null;
    setGeoCustomPos(null);
    setMoreEntitiesOpen(false);
    setUndoStack([]);
    setExpandedEvidenceStep(null);
    if (webglLifecycleRef.current.phase !== "healthy" || stageWebglFailed || viewerBoundaryCrashed) {
      setViewerMountGen((n) => n + 1);
    }
    setStageWebglFailed(false);
    setViewerBoundaryCrashed(false);
    setWebglLifecycle({ phase: "healthy", attempt: 0, maxAttempts: 2 });
    setWebglStageAttempt(0);
  }, [scene, problemSnapshotKey]);

  const coTrongCanh = useMemo(() => {
    const co = new Set(day.objects.map((o) => o.id));
    return (id: string) => co.has(id);
  }, [day]);

  useEffect(() => {
    const kq = apDungPhien(tt, phien ?? null, moc, coTrongCanh);
    if (kq.seen !== moc) setMoc(kq.seen);
    if (!kq.applied) return;
    const syncedAnchor = resolvePedagogicalStepAnchor(kq.next.current_step);
    const safeSelected = isSelectableAtAnchor(kq.next.selected_id, syncedAnchor)
      ? kq.next.selected_id
      : null;
    setTt({ ...kq.next, current_step: syncedAnchor, selected_id: safeSelected });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phien?.roundId, phien?.cmdId, phien?.syncCmdId, phien?.mode, coTrongCanh]);

  const prevPedagogicalAnchor = (rawStep: number): number => {
    const curIdx = timChiSoBuocSuPham(resolvePedagogicalStepAnchor(rawStep));
    return dsBuoc[Math.max(0, curIdx - 1)]?.anchor ?? anchorOfGeometryStep(day, 0);
  };
  const nextPedagogicalAnchor = (rawStep: number): number => {
    const curIdx = timChiSoBuocSuPham(resolvePedagogicalStepAnchor(rawStep));
    const maxIdx = Math.max(0, dsBuoc.length - 1);
    return dsBuoc[Math.min(maxIdx, curIdx + 1)]?.anchor ?? anchorOfGeometryStep(day, maxIdx);
  };

  const buocHien = resolvePedagogicalStepAnchor(tt.current_step);
  const buocHinh = timChiSoBuocSuPham(buocHien);
  const dau = buocHinh <= 0;
  const cuoi = buocHinh >= tong - 1;
  const giamChuyenDong = prefersReducedMotion();

  const persistStepProgress = (anchorStep: number) => {
    if (!activeHistoryId) return;
    const cursorIdx = timChiSoBuocSuPham(anchorStep);
    historyStore.touch(activeHistoryId, { lastCursor: cursorIdx });
    queueMicrotask(() => {
      useAppStore.setState({ history: historyStore.list() });
    });
    if (useAuthStore.getState().user !== null) {
      void touchServerHistory(activeHistoryId, {
        lastCursor: cursorIdx,
        stepCount: tong,
      });
    }
  };

  const latestUndoStateRef = useRef({
    tt,
    xray,
    hinhPhu,
    luoi,
    showShell,
    showVertexLabels,
    showPlane,
    showSection,
    showAxes,
    showDimensionLabels,
    showRightAngles,
    showDashedHidden,
    shellOpacityPct,
    planeOpacityPct,
  });
  latestUndoStateRef.current = {
    tt,
    xray,
    hinhPhu,
    luoi,
    showShell,
    showVertexLabels,
    showPlane,
    showSection,
    showAxes,
    showDimensionLabels,
    showRightAngles,
    showDashedHidden,
    shellOpacityPct,
    planeOpacityPct,
  };

  const pushUndoSnapshot = () => {
    const cur = latestUndoStateRef.current;
    const snap = {
      tt: {
        ...cur.tt,
        hidden_ids: [...cur.tt.hidden_ids],
        isolated_ids: [...cur.tt.isolated_ids],
        exploded_groups: [...cur.tt.exploded_groups],
        transparent_ids: [...cur.tt.transparent_ids],
      },
      xray: cur.xray,
      hinhPhu: cur.hinhPhu,
      luoi: cur.luoi,
      showShell: cur.showShell,
      showVertexLabels: cur.showVertexLabels,
      showPlane: cur.showPlane,
      showSection: cur.showSection,
      showAxes: cur.showAxes,
      showDimensionLabels: cur.showDimensionLabels,
      showRightAngles: cur.showRightAngles,
      showDashedHidden: cur.showDashedHidden,
      shellOpacityPct: cur.shellOpacityPct,
      planeOpacityPct: cur.planeOpacityPct,
    };
    setUndoStack((prev) => (prev.length >= 30 ? [...prev.slice(prev.length - 29), snap] : [...prev, snap]));
  };

  const handleUndoInteraction = () => {
    if (undoStack.length === 0) return;
    const snap = undoStack[undoStack.length - 1]!;
    setUndoStack((prev) => prev.slice(0, -1));
    setDangPhat(false);
    setTt(snap.tt);
    persistStepProgress(snap.tt.current_step);
    onFocus?.(snap.tt.selected_id, snap.tt.selected_id === null ? "clear" : "select");
    setXray(snap.xray);
    setHinhPhu(snap.hinhPhu);
    setLuoi(snap.luoi);
    setShowShell(snap.showShell);
    setShowVertexLabels(snap.showVertexLabels);
    setShowPlane(snap.showPlane);
    setShowSection(snap.showSection);
    setShowAxes(snap.showAxes);
    setShowDimensionLabels(snap.showDimensionLabels);
    setShowRightAngles(snap.showRightAngles);
    setShowDashedHidden(snap.showDashedHidden);
    setShellOpacityPct(snap.shellOpacityPct);
    setPlaneOpacityPct(snap.planeOpacityPct);
  };
  const handleUndoInteractionRef = useRef(handleUndoInteraction);
  handleUndoInteractionRef.current = handleUndoInteraction;

  const setStep = (next: number | ((prev: number) => number), recordUndo = true) => {
    if (recordUndo) {
      pushUndoSnapshot();
    }
    setTt((prevState) => {
      const rawNext = typeof next === "function" ? next(prevState.current_step) : next;
      const anchored = resolvePedagogicalStepAnchor(rawNext);
      persistStepProgress(anchored);
      const nextSelected = isSelectableAtAnchor(prevState.selected_id, anchored)
        ? prevState.selected_id
        : null;
      return { ...prevState, current_step: anchored, selected_id: nextSelected };
    });
  };

  useEffect(() => {
    if (!dangPhat) return undefined;
    if (giamChuyenDong || !stageControlsInteractive) {
      setDangPhat(false);
      return undefined;
    }
    if (tong <= 1) {
      const hasBall = day.objects.some((o) => o.type === "curved_solid" && o.curved_kind === "ball");
      const singleStepTimer = setTimeout(() => {
        setDangPhat(false);
      }, hasBall ? 1180 : 720);
      return () => clearTimeout(singleStepTimer);
    }
    if (cuoi) {
      setDangPhat(false);
      return undefined;
    }
    const timer = setInterval(() => {
      setStep((s) => nextPedagogicalAnchor(s), false);
    }, PLAYBACK_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [dangPhat, cuoi, giamChuyenDong, stageControlsInteractive, day, dsBuoc]);

  // Đảm bảo luôn có đúng 1 thẻ <h1> hiển thị thực tế cho tiêu đề bài toán ở mọi viewport (>680px ở header, <=680px ở Study Dock mobile bar)
  const [isCompactProbHeader, setIsCompactProbHeader] = useState<boolean>(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return false;
    return window.matchMedia("(max-width: 680px)").matches;
  });
  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return undefined;
    const mql = window.matchMedia("(max-width: 680px)");
    const onChange = () => setIsCompactProbHeader(mql.matches);
    onChange();
    if (typeof mql.addEventListener === "function") {
      mql.addEventListener("change", onChange);
      return () => mql.removeEventListener("change", onChange);
    }
    return undefined;
  }, []);

  const lastStepScrollContextRef = useRef<{ key: string | null | undefined; step: number }>({
    key: problemSnapshotKey,
    step: buocHinh,
  });

  // Cuộn mục bước đang active vào vùng nhìn thấy của Study Dock khi đổi bước dựng
  // (giữ scrollTop = 0 khi mới mở bài để phần ĐỀ BÀI ở đầu Study Dock luôn hiển thị trọn vẹn)
  useEffect(() => {
    const prev = lastStepScrollContextRef.current;
    lastStepScrollContextRef.current = { key: problemSnapshotKey, step: buocHinh };
    const ul = stepsListRef.current;
    const scrollArea = dockScrollRef.current ?? ul?.closest<HTMLElement>(".dock-scroll") ?? null;
    if (prev.key !== problemSnapshotKey) {
      if (scrollArea) scrollArea.scrollTop = 0;
      return;
    }
    if (prev.step === buocHinh) return;
    if (!ul || !scrollArea) return;
    const activeRow = ul.querySelector<HTMLElement>(".step-row.is-active");
    if (!activeRow) return;
    const r = activeRow.getBoundingClientRect();
    const c = scrollArea.getBoundingClientRect();
    if (r.height <= 0 || c.height <= 0) return;
    if (r.top < c.top) {
      scrollArea.scrollTop += r.top - c.top - 8;
    } else if (r.bottom > c.bottom) {
      scrollArea.scrollTop += r.bottom - c.bottom + 8;
    }
  }, [buocHinh, problemSnapshotKey]);

  // Cuộn thẻ thông tin đối tượng (.context-object-card) vào vùng nhìn thấy của Study Dock khi chọn đối tượng (nhất là trên mobile)
  useEffect(() => {
    if (!tt.selected_id) return;
    const scrollArea = dockScrollRef.current;
    if (!scrollArea) return;
    const card = scrollArea.querySelector<HTMLElement>(".context-object-card");
    if (!card) return;
    const r = card.getBoundingClientRect();
    const c = scrollArea.getBoundingClientRect();
    if (r.height <= 0 || c.height <= 0) return;
    if (r.top < c.top) {
      scrollArea.scrollTop += r.top - c.top - 8;
    } else if (r.bottom > c.bottom) {
      scrollArea.scrollTop += r.bottom - c.bottom + 8;
    }
  }, [tt.selected_id]);

  // Đóng popover hiển thị khi bấm ra ngoài hoặc nhấn phím tắt (bảng Tùy chỉnh hình giữ mở khi xoay 3D, chỉ đóng qua nút × / nút bật-tắt / thu gọn toolbar / Esc theo chuẩn HTML V2.7)
  useEffect(() => {
    const onPointerDown = (e: PointerEvent) => {
      const targetNode = e.target as Node;
      if (displayPopOpen && toolbarRef.current && !toolbarRef.current.contains(targetNode)) {
        setDisplayPopOpen(false);
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target?.isContentEditable
      ) {
        if (e.key === "Escape") {
          if (geoCustomOpen) {
            setGeoCustomOpen(false);
            return;
          }
          if (displayPopOpen) {
            setDisplayPopOpen(false);
            return;
          }
        }
        return;
      }
      if (e.key === "Escape") {
        if (geoCustomOpen) {
          setGeoCustomOpen(false);
        } else if (displayPopOpen) {
          setDisplayPopOpen(false);
        } else if (tt.selected_id !== null) {
          chon(null);
        }
        return;
      }
      if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey && e.key.toLowerCase() === "z") {
        if (stageControlsInteractive && undoStack.length > 0) {
          e.preventDefault();
          handleUndoInteractionRef.current();
        }
        return;
      }
      if (target?.closest('button, [role="button"], a, summary')) {
        return;
      }
      if (!stageControlsInteractive) {
        return;
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        handlePrevStep();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        handleNextStep();
      } else if (e.key === " ") {
        e.preventDefault();
        handleTogglePlay();
      }
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [
    displayPopOpen,
    geoCustomOpen,
    tt.selected_id,
    cuoi,
    dangPhat,
    day,
    dsBuoc,
    stageControlsInteractive,
    undoStack,
  ]);

  const theoId = useMemo(() => new Map(day.objects.map((o) => [o.id, o])), [day]);
  const chon = (id: string | null) => {
    const safeId = id && isSelectableAtAnchor(id, buocHien) ? id : null;
    if (safeId !== tt.selected_id) {
      pushUndoSnapshot();
    }
    setTt((s) => select(s, safeId));
    onFocus?.(safeId, safeId === null ? "clear" : "select");
  };

  const dangChon =
    tt.selected_id && isSelectableAtAnchor(tt.selected_id, buocHien)
      ? theoId.get(tt.selected_id) ?? null
      : null;

  const phanTichToan = useMemo(
    () => phanTichToanHocCuaCanh(day, hybrid, routeDSimulation),
    [day, hybrid, routeDSimulation],
  );
  const dapAnAn = useMemo(() => tapKetQuaCuoi(day, hybrid), [day, hybrid]);
  const presentationPolicy = useMemo(
    () => evaluateStudentPresentationPolicy(day, pedPlan.goalCompletion),
    [day, pedPlan.goalCompletion],
  );

  const annotationView = useMemo<AnnotationView>(() => {
    const hidden = new Set<string>(dapAnAn);
    for (const o of day.objects) {
      if (o.type !== "quantity") continue;
      const isDirectVerifiedGiven = presentationPolicy.canDisplayEntityValue(o);
      if (!showDimensionLabels || !isDirectVerifiedGiven) {
        hidden.add(o.id);
      }
    }
    return { ...xem, hideGiven: !showDimensionLabels, hiddenIds: hidden };
  }, [xem, dapAnAn, showDimensionLabels, day, presentationPolicy]);

  useEffect(() => {
    if (!problemSnapshotKey || invalidSceneReason !== null || !mathVerification.valid) return;
    saveLearnerRecoverySnapshot({
      problemKey: problemSnapshotKey,
      stepIndex: buocHinh,
      selectedId: tt.selected_id,
      dockCollapsed,
      mobileViewMode: dockCollapsed ? "stage_expanded" : "dock_open",
      display: {
        showShell,
        showVertexLabels,
        showPlane,
        showSection,
        showAxes,
        showDimensionLabels,
        showRightAngles,
        showDashedHidden,
        auxiliaryShown: hinhPhu,
        gridShown: luoi,
        xray,
        shellOpacityPct,
        planeOpacityPct,
      },
      camera: latestCameraPoseRef.current,
    });
  }, [
    problemSnapshotKey,
    invalidSceneReason,
    buocHinh,
    tt.selected_id,
    dockCollapsed,
    showShell,
    showVertexLabels,
    showPlane,
    showSection,
    showAxes,
    showDimensionLabels,
    showRightAngles,
    showDashedHidden,
    hinhPhu,
    luoi,
    xray,
    shellOpacityPct,
    planeOpacityPct,
  ]);

  const givenParamsAtStep = useMemo(
    () => givenQuantitiesSummary(day, buocHien),
    [day, buocHien],
  );

  const anPhu = useMemo(
    () => auxiliaryHiddenAt(day, buocHien, hinhPhu, tt.selected_id),
    [day, buocHien, hinhPhu, tt.selected_id],
  );

  const tenThietDien = (secObj: Scene3D["objects"][number]): string => {
    const c = sectionDetails(day, secObj.id);
    const cyc =
      c && c.vertexNames.length > 0
        ? formatCycleNotation(
            c.vertexNames,
            preferredPointOrderForPolygon(day, secObj),
          )
        : null;
    if (cyc) {
      return `Thiết diện ${cyc}`;
    }
    return secObj.reference?.trim() || secObj.display_label?.trim() || secObj.label?.trim() || secObj.id;
  };

  const ten = (id: string) => {
    const o = theoId.get(id);
    if (!o) return id;
    if (o.type === "section") {
      return tenThietDien(o);
    }
    return o.reference?.trim() || o.display_label?.trim() || o.label?.trim() || id;
  };
  const kyHieu = (id: string) => {
    const o = theoId.get(id);
    if (o?.type === "section") {
      const c = sectionDetails(day, o.id);
      const cyc =
        c && c.vertexNames.length > 0
          ? formatCycleNotation(c.vertexNames, preferredPointOrderForPolygon(day, o))
          : null;
      if (cyc) return cyc;
    }
    return o?.notation?.trim() || o?.display_label?.trim() || o?.label?.trim() || id;
  };
  const giaTri = (id: string) => {
    const o = theoId.get(id);
    if (!o) return ten(id);
    const v = hienBieuThucDaiLuong(o)?.trim() ?? "";
    return v ? `${kyHieu(id)} = ${v}` : ten(id);
  };

  const ctThietDien =
    dangChon?.type === "section" ? sectionDetails(day, dangChon.id) : null;
  const formula = dangChon ? coherentFormula(day, dangChon) : null;
  const laDaiLuong = Boolean(
    dangChon &&
      (dangChon.type === "quantity" ||
        (dangChon.value !== undefined && dangChon.value !== "")),
  );
  const nguon = dangChon ? quantitySources(day, dangChon.id) : null;
  const doTren =
    laDaiLuong && nguon && nguon.givens.length + nguon.inputs.length === 0
      ? directDependencies(day, dangChon!.id).filter(
          (id) => theoId.get(id)?.type !== "quantity",
        )
      : [];

  // Phân nhóm đối tượng tại bước hiện tại theo 3 mức ưu tiên sư phạm (Chính / Liên quan / Khác)
  const entityGroups = useMemo(
    () =>
      buildStepEntityGroups(day, buocHien, {
        hiddenAuxIds: anPhu,
        hiddenAnswerIds: dapAnAn,
        selectedId: tt.selected_id,
        steps: dsBuoc,
      }),
    [day, buocHien, anPhu, dapAnAn, tt.selected_id, dsBuoc],
  );
  const effectiveMoreEntitiesOpen =
    moreEntitiesOpen || entityGroups.other.some((x) => x.id === tt.selected_id);

  useEffect(() => {
    if (typeof window !== "undefined") {
      (window as any).__geo3d_dock_entity_groups = entityGroups;
      (window as any).__geo3d_goal_completion = pedPlan.goalCompletion;
    }
    return () => {
      if (typeof window !== "undefined") {
        delete (window as any).__geo3d_dock_entity_groups;
        delete (window as any).__geo3d_goal_completion;
      }
    };
  }, [entityGroups, pedPlan.goalCompletion]);

  const handleTogglePlay = () => {
    if (tong <= 1) {
      if (dangPhat) {
        setDangPhat(false);
        return;
      }
      if (!giamChuyenDong && stageControlsInteractive) {
        setReplayNonce((n) => n + 1);
        setDangPhat(true);
      }
      return;
    }
    if (cuoi) {
      setStep(dsBuoc[0]?.anchor ?? anchorOfGeometryStep(day, 0));
      setReplayNonce((n) => n + 1);
      setDangPhat(true);
    } else {
      if (!dangPhat && buocHinh === 0) {
        setReplayNonce((n) => n + 1);
      }
      setDangPhat((p) => !p);
    }
  };

  const handlePrevStep = () => {
    setDangPhat(false);
    setStep((s) => prevPedagogicalAnchor(s));
  };

  const handleNextStep = () => {
    setDangPhat(false);
    setStep((s) => nextPedagogicalAnchor(s));
  };

  const handleResetView = () => {
    pushUndoSnapshot();
    setTt((s) => showAll(clearIsolate(select(s, null))));
    setTbPos(null);
    setGeoCustomPos(null);
    latestCameraPoseRef.current = null;
    setSavedCameraPose(null);
    setFitToken((n) => n + 1);
  };

  // Tự động điều chỉnh (re-clamp) vị trí bảng Tùy chỉnh hình và Floating Toolbar khi đổi kích thước viewport hoặc thu gọn/mở lại Study Dock
  useEffect(() => {
    const clampPositionsToStage = () => {
      const stageEl = stageRef.current;
      if (!stageEl) return;
      const sRect = stageEl.getBoundingClientRect();
      if (sRect.width <= 0 || sRect.height <= 0) return;

      setGeoCustomPos((prev) => {
        if (!prev) return null;
        const popEl = geoCustomPopRef.current;
        const popRect = popEl?.getBoundingClientRect();
        const w = popRect && popRect.width > 0 ? popRect.width : 296;
        const h = popRect && popRect.height > 0 ? popRect.height : 300;
        const margin = sRect.width <= 480 ? 8 : 12;
        const maxX = Math.max(margin, sRect.width - w - margin);
        const maxY = Math.max(margin, sRect.height - h - margin);
        const nx = Math.round(Math.max(margin, Math.min(maxX, prev.x)));
        const ny = Math.round(Math.max(margin, Math.min(maxY, prev.y)));
        if (nx === prev.x && ny === prev.y) return prev;
        return { x: nx, y: ny };
      });

      setTbPos((prev) => {
        if (!prev) return null;
        const tbEl = toolbarRef.current;
        const tbRect = tbEl?.getBoundingClientRect();
        const w = tbRect && tbRect.width > 0 ? tbRect.width : 210;
        const h = tbRect && tbRect.height > 0 ? tbRect.height : 40;
        const margin = sRect.width <= 480 ? 8 : 10;
        const maxX = Math.max(margin, sRect.width - w - margin);
        const maxY = Math.max(margin, sRect.height - h - margin);
        const nx = Math.round(Math.max(margin, Math.min(maxX, prev.x)));
        const ny = Math.round(Math.max(margin, Math.min(maxY, prev.y)));
        if (nx === prev.x && ny === prev.y) return prev;
        return { x: nx, y: ny };
      });
    };

    clampPositionsToStage();
    const timer = setTimeout(clampPositionsToStage, 220);
    window.addEventListener("resize", clampPositionsToStage);
    let ro: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined" && stageRef.current) {
      ro = new ResizeObserver(() => clampPositionsToStage());
      ro.observe(stageRef.current);
    }
    return () => {
      clearTimeout(timer);
      window.removeEventListener("resize", clampPositionsToStage);
      ro?.disconnect();
    };
  }, [dockCollapsed, geoCustomOpen, tbCollapsed]);

  useEffect(() => {
    if (viewerUnavailable) {
      setDockCollapsed(false);
    }
  }, [viewerUnavailable]);

  const handleResetDisplayOpts = () => {
    pushUndoSnapshot();
    setShowShell(true);
    setShowVertexLabels(true);
    setShowPlane(true);
    setShowSection(true);
    setShowDimensionLabels(true);
    setShowRightAngles(true);
    setShowDashedHidden(true);
    setHinhPhu(false);
    setShowAxes(false);
    setLuoi(true);
    setXem(DEFAULT_ANNOTATION_VIEW);
  };

  const handleResetGeoCustom = () => {
    if (shellOpacityPct !== 12 || planeOpacityPct !== 8) {
      pushUndoSnapshot();
    }
    setShellOpacityPct(12);
    setPlaneOpacityPct(8);
  };

  const changeProblemTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const toolbarDragCleanupRef = useRef<(() => void) | null>(null);
  const geoCustomDragCleanupRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!stageControlsInteractive) {
      toolbarDragCleanupRef.current?.();
      geoCustomDragCleanupRef.current?.();
    }
  }, [stageControlsInteractive]);

  useEffect(() => {
    return () => {
      toolbarDragCleanupRef.current?.();
      geoCustomDragCleanupRef.current?.();
      if (changeProblemTimerRef.current !== null) {
        clearTimeout(changeProblemTimerRef.current);
        changeProblemTimerRef.current = null;
      }
    };
  }, []);

  const handleChangeProblem = () => {
    setView("home");
    if (typeof document !== "undefined") {
      if (changeProblemTimerRef.current !== null) {
        clearTimeout(changeProblemTimerRef.current);
      }
      changeProblemTimerRef.current = setTimeout(() => {
        changeProblemTimerRef.current = null;
        const input = document.getElementById(
          "home-problem-input",
        ) as HTMLTextAreaElement | null;
        input?.focus();
      }, 40);
    }
  };

  const handleToolbarDragStart = (e: ReactPointerEvent<HTMLDivElement>) => {
    if (!stageRef.current || !toolbarRef.current) return;
    toolbarDragCleanupRef.current?.();
    e.preventDefault();
    e.stopPropagation();
    const stageRect = stageRef.current.getBoundingClientRect();
    const tbRect = toolbarRef.current.getBoundingClientRect();
    const startX = e.clientX;
    const startY = e.clientY;
    const origLeft = tbRect.left - stageRect.left;
    const origTop = tbRect.top - stageRect.top;
    setTbDragging(true);

    const onMove = (ev: PointerEvent) => {
      if (!stageRef.current || !toolbarRef.current) return;
      const sRect = stageRef.current.getBoundingClientRect();
      const tRect = toolbarRef.current.getBoundingClientRect();
      const dx = ev.clientX - startX;
      const dy = ev.clientY - startY;
      const margin = sRect.width <= 480 ? 8 : 10;
      const nextX = Math.max(
        margin,
        Math.min(Math.max(margin, sRect.width - tRect.width - margin), origLeft + dx),
      );
      const nextY = Math.max(
        margin,
        Math.min(Math.max(margin, sRect.height - tRect.height - margin), origTop + dy),
      );
      setTbPos({ x: Math.round(nextX), y: Math.round(nextY) });
    };

    const onUp = () => {
      toolbarDragCleanupRef.current = null;
      setTbDragging(false);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onUp);
    };

    toolbarDragCleanupRef.current = onUp;
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
  };

  const handleGeoCustomDragStart = (e: ReactPointerEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement | null;
    if (target?.closest("button, input, label")) return;
    if (!stageRef.current || !geoCustomPopRef.current) return;
    geoCustomDragCleanupRef.current?.();
    e.preventDefault();
    e.stopPropagation();
    const stageRect = stageRef.current.getBoundingClientRect();
    const popRect = geoCustomPopRef.current.getBoundingClientRect();
    const startX = e.clientX;
    const startY = e.clientY;
    const origLeft = popRect.left - stageRect.left;
    const origTop = popRect.top - stageRect.top;
    const initPopW = popRect.width || 296;
    const initPopH = popRect.height || 300;
    setGeoCustomDragging(true);

    const onMove = (ev: PointerEvent) => {
      if (!stageRef.current) return;
      const sRect = stageRef.current.getBoundingClientRect();
      const curPopRect = geoCustomPopRef.current?.getBoundingClientRect();
      const popW = curPopRect && curPopRect.width > 0 ? curPopRect.width : initPopW;
      const popH = curPopRect && curPopRect.height > 0 ? curPopRect.height : initPopH;
      const margin = sRect.width <= 480 ? 8 : 12;
      const maxX = Math.max(margin, sRect.width - popW - margin);
      const maxY = Math.max(margin, sRect.height - popH - margin);
      const dx = ev.clientX - startX;
      const dy = ev.clientY - startY;
      const nx = Math.max(margin, Math.min(maxX, origLeft + dx));
      const ny = Math.max(margin, Math.min(maxY, origTop + dy));
      setGeoCustomPos({ x: Math.round(nx), y: Math.round(ny) });
    };

    const onUp = () => {
      geoCustomDragCleanupRef.current = null;
      setGeoCustomDragging(false);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onUp);
    };

    geoCustomDragCleanupRef.current = onUp;
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
  };

  const checkInternalFixtureLabel = (raw?: string | null): boolean => {
    if (!raw) return false;
    const s = raw.trim();
    if (!s) return false;
    return (
      /^(?:hybrid|gen|fixture|case|test)[_-][a-z0-9_-]+$/iu.test(s)
      || /\bbài\s+toán\s+tổng\s+quát\s+hybrid\b/iu.test(s)
      || /\b(?:fixture|kiểm\s+thử\s+nội\s+bộ|mẫu\s+kiểm\s+thử)\b/iu.test(s)
    );
  };
  const cleanFixturePrefix = (raw?: string | null): string =>
    (raw ?? "")
      .replace(/^Bài\s+toán\s+tổng\s+quát\s+Hybrid\s*(?:·|-|:)?\s*/iu, "")
      .trim();

  const rawDe = de?.trim() ?? "";
  const rawTieuDe = tieuDe?.trim() ?? "";
  const isInternalFixtureCase =
    checkInternalFixtureLabel(rawDe)
    || checkInternalFixtureLabel(rawTieuDe)
    || (!rawDe && /^[a-z0-9_-]+$/iu.test(rawTieuDe) && rawTieuDe.includes("_"));
  const hasAuthenticProblemStatement =
    Boolean(rawDe) && !checkInternalFixtureLabel(rawDe) && rawDe !== rawTieuDe;
  const rawCleanedTitle = cleanFixturePrefix(rawTieuDe);
  const cleanedTitle = (() => {
    if (/hình\s+trụ\s+(?:có\s+)?trục\s+xiên|hình\s+trụ\s+xiên/iu.test(rawCleanedTitle)) {
      const cylObj = day.objects.find(
        (o) => o.type === "curved_solid" && o.curved_kind === "cylinder",
      );
      if (cylObj) {
        const ortho = inspectAxialCurvedOrthogonality(day, cylObj);
        if (ortho.isRightCertified && !ortho.isOblique) {
          return "Hình trụ tròn xoay có trục đặt nghiêng";
        }
      }
    }
    return rawCleanedTitle;
  })();
  const safeGoalTitle = presentationPolicy.safeWorkspaceTitle;
  const problemTitleText =
    (cleanedTitle && !/^(?:hybrid|gen|fixture|case|test)[_-][a-z0-9_-]+$/iu.test(cleanedTitle)
      ? cleanedTitle
      : "")
    || safeGoalTitle
    || rawTieuDe
    || "Mô phỏng hình học không gian";
  const problemStatementText = hasAuthenticProblemStatement
    ? rawDe
    : isInternalFixtureCase
      ? safeGoalTitle
        ? `Hợp đồng dữ kiện kỹ thuật (không kèm lời đề gốc) — Mục tiêu: ${safeGoalTitle}.`
        : "Hợp đồng dữ kiện kỹ thuật phục vụ kiểm chứng mô hình 3D (không kèm lời đề gốc)."
      : rawDe
        || rawTieuDe
        || (invalidSceneReason !== null
          ? "Bản ghi này chưa đính kèm nội dung đề bài."
          : "Theo dõi mô hình hình học không gian theo từng bước dựng.");
  const nhanMucHienThi = ["Quan", "sát"].join(" ");

  return (
    <section
      className="axo-workspace-v62 axo-frame is-page-workspace"
      aria-label={problemTitleText}
      data-back-label={quayLai?.nhan ?? "Trang chủ"}
    >
      {/* ── WORKSPACE HEADER V2.7 ─────────────────────────────────────────── */}
      <header className="axo-header ws-axo-header">
        <div className="axo-brand">
          <button
            type="button"
            className="axo-logo-btn nav-wordmark"
            id="btn-brand-home"
            title="Về trang chủ Axo"
            aria-label="Về trang chủ Axo"
            onClick={() => {
              goHome();
            }}
          >
            <IconAxoLogo size={22} />
            <span className="axo-brand-name nav-wordmark-text">Axo</span>
          </button>
          <div className="header-div" id="header-prob-div" aria-hidden="true" />
          {isCompactProbHeader ? (
            <div
              className="prob-title-top"
              id="top-prob-title"
              title={problemTitleText}
            >
              {problemTitleText}
            </div>
          ) : (
            <h1
              className="prob-title-top"
              id="top-prob-title"
              title={problemTitleText}
            >
              {problemTitleText}
            </h1>
          )}
        </div>

        <nav className="nav-n1-capsule axo-nav-capsule" aria-label="Điều hướng chính">
          <button
            type="button"
            className="nav-n1-item axo-nav-item"
            id="nav-home"
            title="Trang chủ"
            onClick={() => setView("home")}
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M3 10l9-7 9 7v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 21 9 12 15 12 15 21" />
            </svg>
            <span className="topnav-label nav-text">Trang chủ</span>
          </button>
          <button
            type="button"
            className="nav-n1-item axo-nav-item"
            id="nav-library"
            title="Thư viện"
            onClick={() => setView("library")}
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <rect x="3" y="3" width="7" height="7" rx="1.5" />
              <rect x="14" y="3" width="7" height="7" rx="1.5" />
              <rect x="14" y="14" width="7" height="7" rx="1.5" />
              <rect x="3" y="14" width="7" height="7" rx="1.5" />
            </svg>
            <span className="topnav-label nav-text">Thư viện</span>
          </button>
          <button
            type="button"
            className="nav-n1-item axo-nav-item"
            id="nav-history"
            title="Lịch sử"
            onClick={() => setView("history")}
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="9" />
              <polyline points="12 7 12 12 15.5 14" />
            </svg>
            <span className="topnav-label nav-text">Lịch sử</span>
          </button>
        </nav>

        <div className="axo-header-right">
          {(daiLop && daiLopTomTat) ? null : null}
          <button
            type="button"
            className="btn-change-prob"
            id="btn-header-change-prob"
            title="Đổi sang bài toán khác (Về khung nhập đề)"
            onClick={handleChangeProblem}
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 5v14M5 12h14" />
            </svg>
            <span className="change-prob-text">Đổi đề toán</span>
          </button>
        </div>
      </header>

      {/* ── WORKSPACE BODY V6.2 (3D STAGE + UNIFIED STUDY DOCK) ───────────── */}
      <div
        className={`axo-body${dockCollapsed ? " dock-collapsed is-dock-collapsed" : ""}`}
        id="ws-body"
      >
        <main
          ref={stageRef}
          className={`stage-3d${dockCollapsed ? " is-dock-collapsed" : ""}`}
          id="stage-3d-box"
        >
          <div
            className={`stage-spatial-grid${luoi ? "" : " grid-off is-hidden"}`}
            id="stage-spatial-grid"
            aria-hidden="true"
          />
          <div
            className={`safe-zone-guide${tbDragging || geoCustomDragging ? " is-visible" : ""}`}
            id="safe-zone-rect"
            aria-hidden="true"
          />

          {/* ── REAL SCENE3D RENDERER (Three.js / WebGL) ──────────────────── */}
          <div
            className={`ws-scene3d-host${
              !showVertexLabels ? " hide-vertex-labels" : ""
            }${!showDimensionLabels ? " hide-length-labels hide-dimension-labels" : ""}${
              !showRightAngles ? " hide-angle-labels hide-right-angles" : ""
            }${!showDashedHidden ? " hide-dashed-edges" : ""}`}
          >
            {invalidSceneReason !== null ? (
              <div
                className="ws-invalid-scene-wrap workspace-scene3d-unavailable"
                id="ws-scene3d-unavailable-card"
                role="alert"
                data-stage-fault="invalid_scene_data"
              >
                <AxoErrorExperience
                  kind="unsupported_simulation"
                  variant="stage"
                  title={unavailableOverride?.title ?? "Dữ liệu mô hình 3D không hợp lệ"}
                  detail={invalidSceneReason}
                  hasBackHistory={hasInAppNavigation}
                  onBack={() => useAppStore.getState().escapeFromError()}
                  onGoHome={unavailableOverride?.onGoHome ?? (() => useAppStore.getState().goHome())}
                  homeLabel={unavailableOverride ? "Dựng lại trên Trang chủ" : undefined}
                  onOpenLibrary={() => useAppStore.getState().openLibrary()}
                  libraryLabel={unavailableOverride ? "Mở Thư viện 3D" : undefined}
                />
              </div>
            ) : !mathVerification.valid ? (
              <div
                className="ws-math-contradiction-wrap"
                role="alert"
                data-math-contradiction=""
              >
                <AxoErrorExperience
                  kind="unsupported_simulation"
                  variant="stage"
                  title={mathVerification.contradictions[0]?.title ?? "Dữ kiện hình học mâu thuẫn"}
                  detail={
                    mathVerification.contradictions.map((c) => c.explanation).join(" ") ||
                    "Các tọa độ hoặc ràng buộc hình học hiện tại mâu thuẫn nên Axo dừng dựng hình."
                  }
                  hasBackHistory={hasInAppNavigation}
                  onBack={() => useAppStore.getState().escapeFromError()}
                  onGoHome={() => useAppStore.getState().goHome()}
                  onOpenLibrary={() => useAppStore.getState().openLibrary()}
                />
              </div>
            ) : (
              <ErrorBoundary
                mien="scene3d-viewer"
                resetKey={`${problemSnapshotKey}|${webglStageAttempt}`}
                onCatch={() => setViewerBoundaryCrashed(true)}
                onRecover={() => setViewerBoundaryCrashed(false)}
                fallback={(thuLai, { canRetry, retryCount }) => (
                  <AxoViewerRecoverySurface
                    state={{
                      phase: "failed",
                      reason: "render_crash",
                      attempt: retryCount,
                      maxAttempts: 1,
                    }}
                    onSecondaryRetry={
                      canRetry
                        ? () => {
                            setViewerBoundaryCrashed(false);
                            setSavedCameraPose(latestCameraPoseRef.current);
                            thuLai();
                          }
                        : undefined
                    }
                  />
                )}
              >
                <Scene3DWorkspace
                  key={`scene3d-${viewerMountGen}-${webglStageAttempt}`}
                  scene={day}
                  step={buocHien}
                  interaction={tt}
                  onSelect={chon}
                  fitToken={fitToken}
                  replayNonce={replayNonce}
                  isPlaying={dangPhat}
                  annotationView={annotationView}
                  auxiliaryShown={hinhPhu}
                  gridShown={false}
                  xray={xray}
                  shellShown={showShell}
                  planeShown={showPlane}
                  sectionShown={showSection}
                  axesShown={showAxes}
                  shellOpacityPct={shellOpacityPct}
                  planeOpacityPct={planeOpacityPct}
                  rightAnglesShown={showRightAngles}
                  dashedHiddenShown={showDashedHidden}
                  initialCameraPose={savedCameraPose}
                  onCameraPoseChange={(pose) => {
                      latestCameraPoseRef.current = pose;
                      if (problemSnapshotKey && invalidSceneReason === null && mathVerification.valid) {
                        saveLearnerRecoverySnapshot({
                          problemKey: problemSnapshotKey,
                          stepIndex: buocHinh,
                          selectedId: tt.selected_id,
                          dockCollapsed,
                          mobileViewMode: dockCollapsed ? "stage_expanded" : "dock_open",
                          display: {
                            showShell,
                            showVertexLabels,
                            showPlane,
                            showSection,
                            showAxes,
                            showDimensionLabels,
                            showRightAngles,
                            showDashedHidden,
                            auxiliaryShown: hinhPhu,
                            gridShown: luoi,
                            xray,
                            shellOpacityPct,
                            planeOpacityPct,
                          },
                          camera: pose,
                        });
                      }
                    }}
                    onWebglFailure={setStageWebglFailed}
                    onWebglLifecycleChange={setWebglLifecycle}
                    webglRecoveringNode={
                      <AxoViewerRecoverySurface
                        state={{
                          phase: "recovering",
                          reason: "webgl_context_lost",
                          attempt: Math.max(1, webglLifecycle.attempt + 1),
                          maxAttempts: webglLifecycle.maxAttempts,
                        }}
                      />
                    }
                    webglFallbackNode={
                      <AxoViewerRecoverySurface
                        state={{
                          phase: "failed",
                          reason: webglLifecycle.attempt > 0 ? "webgl_context_lost" : "webgl_unavailable",
                          attempt: webglLifecycle.attempt,
                          maxAttempts: webglLifecycle.maxAttempts,
                        }}
                        onSecondaryRetry={
                          webglStageAttempt < 1
                            ? () => {
                                setStageWebglFailed(false);
                                setSavedCameraPose(latestCameraPoseRef.current);
                                setWebglStageAttempt((n) => n + 1);
                              }
                            : undefined
                        }
                      />
                    }
                  />
              </ErrorBoundary>
            )}
          </div>

          {/* Mobile compact problem badge when Study Dock is collapsed */}
          <div
            className={`canvas-mobile-prob-badge${
              dockCollapsed ? " is-dock-collapsed-badge" : ""
            }`}
            id="canvas-mobile-prob-badge"
            role="button"
            tabIndex={0}
            title="Nhấn để mở Đề bài & Các bước dựng"
            onClick={() => {
              setDockCollapsed(false);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                setDockCollapsed(false);
              }
            }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
              style={{ display: "inline-block", verticalAlign: "-2px", marginRight: 6, flexShrink: 0 }}
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <span id="canvas-mobile-prob-text">{`Đề: ${problemTitleText}`}</span>
          </div>

          {/* Study Dock Reopen Capsule Trigger */}
          <button
            type="button"
            className={`study-dock-capsule-trigger${
              dockCollapsed ? " visible is-visible" : ""
            }`}
            id="btn-reopen-dock-capsule"
            title="Mở lại ngăn Học tập"
            onClick={() => {
              setDockCollapsed(false);
            }}
          >
            <svg className="reopen-chevron" viewBox="0 0 24 24" aria-hidden="true">
              <path d="m15 18-6-6 6-6" />
            </svg>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
            </svg>
            <span>Học tập</span>
            <span className="dock-trigger-badge" id="dock-trigger-badge">
              {invalidSceneReason !== null || !mathVerification.valid ? "—" : `${buocHinh + 1}/${tong}`}
            </span>
          </button>

          {/* ── PLAYBACK P-A CAPSULE (BOTTOM-LEFT OF STAGE) ───────────────── */}
          {stageControlsInteractive && (
          <div className="playback-pa-wrap" id="playback-pa-box" data-che-khung="">
            <div
              className={`playback-pa-capsule ${
                paExpanded ? "is-expanded mode-expanded" : "mode-compact"
              }`}
              id="playback-pa-capsule"
              role="group"
              aria-label="Điều khiển bước dựng"
            >
              <div className="pa-controls">
                <button
                  type="button"
                  className="pa-btn"
                  id="pa-prev"
                  title="Bước trước (Phím ←)"
                  aria-label="Bước trước"
                  disabled={dau}
                  onClick={handlePrevStep}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="m15 18-6-6 6-6" />
                  </svg>
                </button>
                {!giamChuyenDong && (
                  <button
                    type="button"
                    className={`pa-btn play-btn pa-btn-play${
                      dangPhat ? " playing is-playing" : ""
                    }`}
                    id="pa-play"
                    title="Phát / Tạm dừng (Space)"
                    aria-label={
                      dangPhat
                        ? "Tạm dừng"
                        : cuoi
                          ? "Xem lại quá trình dựng"
                          : "Phát lại quá trình dựng"
                    }
                    onClick={handleTogglePlay}
                  >
                    {dangPhat ? (
                      <svg
                        id="pa-play-icon"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <rect
                          x="6"
                          y="5"
                          width="4"
                          height="14"
                          fill="currentColor"
                          stroke="none"
                        />
                        <rect
                          x="14"
                          y="5"
                          width="4"
                          height="14"
                          fill="currentColor"
                          stroke="none"
                        />
                      </svg>
                    ) : (
                      <svg
                        id="pa-play-icon"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <polygon
                          points="6 4 20 12 6 20 6 4"
                          fill="currentColor"
                          stroke="none"
                        />
                      </svg>
                    )}
                  </button>
                )}
                <button
                  type="button"
                  className="pa-btn"
                  id="pa-next"
                  title="Bước tiếp (Phím →)"
                  aria-label="Bước sau"
                  disabled={cuoi}
                  onClick={handleNextStep}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="m9 18 6-6-6-6" />
                  </svg>
                </button>
              </div>

              <div className="pa-step-info">
                <span className="pa-step-counter" id="pa-counter">
                  {`Bước ${buocHinh + 1}/${tong}`}
                </span>
                <span
                  className="pa-step-short-title"
                  id="pa-short-title"
                  title={
                    dsBuoc[buocHinh]
                      ? (dsBuoc[buocHinh].narration?.actionTitle ?? moTaBuocDungHienThi(day, dsBuoc[buocHinh]).title)
                      : undefined
                  }
                >
                  {dsBuoc[buocHinh]
                    ? (dsBuoc[buocHinh].narration?.actionTitle ?? moTaBuocDungHienThi(day, dsBuoc[buocHinh]).title)
                    : ""}
                </span>
              </div>

              <div
                className={`pa-pips${dsBuoc.length > 6 ? " is-dense" : ""}`}
                id="pa-pips-mount"
                role="group"
                aria-label="Chọn nhanh bước dựng"
              >
                {dsBuoc.map((b) => {
                  const nhanBuoc = b.narration?.actionTitle ?? moTaBuocDungHienThi(day, b).title;
                  return (
                    <button
                      key={b.index}
                      type="button"
                      className={`pa-pip${
                        b.index === buocHinh
                          ? " current is-active"
                          : b.index < buocHinh
                            ? " done is-done"
                            : ""
                      }`}
                      data-step={b.index}
                      title={`Bước ${b.index + 1}: ${nhanBuoc}`}
                      aria-label={`Bước ${b.index + 1}: ${nhanBuoc}`}
                      aria-current={b.index === buocHinh ? "step" : undefined}
                      onClick={() => {
                        setDangPhat(false);
                        setStep(b.anchor);
                      }}
                    />
                  );
                })}
              </div>

              <div className="pa-div pa-sep" aria-hidden="true" />

              <button
                type="button"
                className="pa-mode-btn"
                id="pa-mode-toggle"
                title="Chuyển chế độ Thu gọn / Mở rộng tiêu đề bước"
                aria-label="Mở rộng hoặc thu gọn tên bước trên thanh phát"
                aria-expanded={paExpanded}
                onClick={() => setPaExpanded((v) => !v)}
              >
                <svg
                  id="pa-mode-icon"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  {paExpanded ? (
                    <>
                      <polyline points="4 14 10 14 10 20" />
                      <polyline points="20 10 14 10 14 4" />
                      <line x1="14" y1="10" x2="21" y2="3" />
                      <line x1="3" y1="21" x2="10" y2="14" />
                    </>
                  ) : (
                    <>
                      <polyline points="15 3 21 3 21 9" />
                      <polyline points="9 21 3 21 3 15" />
                      <line x1="21" y1="3" x2="14" y2="10" />
                      <line x1="3" y1="21" x2="10" y2="14" />
                    </>
                  )}
                </svg>
              </button>
            </div>
          </div>
          )}

          {/* ── FLOATING DRAGGABLE 3D TOOLBAR (BOTTOM-RIGHT OF STAGE) ─────── */}
          {stageControlsInteractive && (
          <div
            ref={toolbarRef}
            className={`toolbar-3d-wrap toolbar-3d-floating${tbCollapsed ? " is-collapsed" : ""}${
              tbPos ? " is-custom-pos" : ""
            }${tbDragging ? " is-dragging" : ""}`}
            id="floating-toolbar-3d"
            data-che-khung=""
            style={
              tbPos
                ? {
                    left: `${tbPos.x}px`,
                    top: `${tbPos.y}px`,
                    right: "auto",
                    bottom: "auto",
                  }
                : undefined
            }
          >
            {/* Display Options Popover (#tb-display-pop) */}
            <div
              className={`tb-display-popover tb-popover${displayPopOpen ? " is-open" : ""}`}
              id="tb-display-pop"
              role="dialog"
              aria-label="Tùy chọn hiển thị lớp 3D"
              aria-hidden={!displayPopOpen}
              onWheel={(e) => e.stopPropagation()}
            >
              <div className="tb-pop-header tb-pop-head">
                <span>Hiển thị</span>
                <span className="tb-pop-esc-hint">Esc</span>
              </div>
              <div
                className="tb-pop-body-scroll"
                id="tb-display-pop-scroll"
                onWheel={(e) => e.stopPropagation()}
              >
                <label className="tb-pop-item tb-pop-row" htmlFor="chk-shell">
                  <span className="tb-pop-label tb-pop-row-text">Vỏ khối</span>
                  <input
                    type="checkbox"
                    id="chk-shell"
                    checked={showShell}
                    onChange={(e) => {
                      pushUndoSnapshot();
                      setShowShell(e.target.checked);
                    }}
                  />
                </label>
                <label className="tb-pop-item tb-pop-row" htmlFor="chk-labels">
                  <span className="tb-pop-label tb-pop-row-text">Nhãn</span>
                  <input
                    type="checkbox"
                    id="chk-labels"
                    checked={showVertexLabels}
                    onChange={(e) => {
                      pushUndoSnapshot();
                      setShowVertexLabels(e.target.checked);
                    }}
                  />
                </label>
                <label className="tb-pop-item tb-pop-row" htmlFor="chk-dimensions">
                  <span className="tb-pop-label tb-pop-row-text">Thông số hình học</span>
                  <input
                    type="checkbox"
                    id="chk-dimensions"
                    checked={showDimensionLabels}
                    onChange={(e) => {
                      pushUndoSnapshot();
                      setShowDimensionLabels(e.target.checked);
                    }}
                  />
                </label>
                <label className="tb-pop-item tb-pop-row" htmlFor="chk-plane">
                  <span className="tb-pop-label tb-pop-row-text">Mặt phẳng tham chiếu / cắt</span>
                  <input
                    type="checkbox"
                    id="chk-plane"
                    checked={showPlane}
                    onChange={(e) => {
                      pushUndoSnapshot();
                      setShowPlane(e.target.checked);
                    }}
                  />
                </label>
                <label className="tb-pop-item tb-pop-row" htmlFor="chk-section">
                  <span className="tb-pop-label tb-pop-row-text">Thiết diện / Giao tuyến</span>
                  <input
                    type="checkbox"
                    id="chk-section"
                    checked={showSection}
                    onChange={(e) => {
                      pushUndoSnapshot();
                      setShowSection(e.target.checked);
                    }}
                  />
                </label>

                <div className="tb-pop-divider" role="separator" />

                <label className="tb-pop-item tb-pop-row" htmlFor="chk-aux">
                  <span className="tb-pop-label-stack">
                    <span className="tb-pop-label tb-pop-row-text">Hình phụ</span>
                    <span className="tb-pop-sublabel">Trục vuông góc &amp; đường phụ</span>
                  </span>
                  <input
                    type="checkbox"
                    id="chk-aux"
                    checked={hinhPhu}
                    onChange={(e) => {
                      pushUndoSnapshot();
                      setHinhPhu(e.target.checked);
                    }}
                  />
                </label>
                <label className="tb-pop-item tb-pop-row" htmlFor="chk-axes">
                  <span className="tb-pop-label tb-pop-row-text">Trục Oxyz</span>
                  <input
                    type="checkbox"
                    id="chk-axes"
                    checked={showAxes}
                    onChange={(e) => {
                      pushUndoSnapshot();
                      setShowAxes(e.target.checked);
                    }}
                  />
                </label>
                <label className="tb-pop-item tb-pop-row" htmlFor="chk-grid">
                  <span className="tb-pop-label tb-pop-row-text">Lưới nền</span>
                  <input
                    type="checkbox"
                    id="chk-grid"
                    checked={luoi}
                    onChange={(e) => {
                      pushUndoSnapshot();
                      setLuoi(e.target.checked);
                    }}
                  />
                </label>
              </div>
              <div className="tb-pop-footer">
                <button
                  type="button"
                  className="tb-pop-reset-btn"
                  id="btn-reset-display-opts"
                  data-reset-layers="btn-reset-display-layers"
                  title="Đưa tất cả các lớp hiển thị về trạng thái mặc định của cảnh"
                  onClick={handleResetDisplayOpts}
                >
                  <span id="btn-reset-display-layers">Khôi phục hiển thị</span>
                </button>
              </div>
            </div>

            {/* Collapsed Pill */}
            <div
              className={`toolbar-3d-collapsed-pill${
                tbCollapsed ? " is-visible" : ""
              }`}
              id="toolbar-3d-collapsed"
            >
              <div
                className="tb-drag-grip"
                id="tb-drag-grip-collapsed"
                title="Kéo để di chuyển"
                onPointerDown={handleToolbarDragStart}
              >
                <svg viewBox="0 0 10 14" fill="currentColor" aria-hidden="true">
                  <circle cx="3" cy="2.5" r="1.2" />
                  <circle cx="7" cy="2.5" r="1.2" />
                  <circle cx="3" cy="7" r="1.2" />
                  <circle cx="7" cy="7" r="1.2" />
                  <circle cx="3" cy="11.5" r="1.2" />
                  <circle cx="7" cy="11.5" r="1.2" />
                </svg>
              </div>
              <button
                type="button"
                className="tb-expand-btn"
                id="btn-tb-expand"
                title="Mở rộng thanh công cụ 3D"
                onClick={() => setTbCollapsed(false)}
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M12 2 4 6.5v11L12 22l8-4.5v-11L12 2Z" />
                  <circle cx="12" cy="12" r="2.5" />
                </svg>
                <span>Công cụ</span>
                <span className="preserved-dots" id="tb-preserved-dots">
                  {!xray && !showAxes && !isGeoParamsDirty && "3D"}
                  <span
                    className={`p-dot dot-blue${xray ? " is-on" : ""}`}
                    id="p-dot-xray"
                    title="X-ray đang bật"
                  />
                  <span
                    className={`p-dot dot-green${showAxes ? " is-on" : ""}`}
                    id="p-dot-axes"
                    title="Trục Oxyz đang bật"
                  />
                  <span
                    className={`p-dot dot-blue${isGeoParamsDirty ? " is-on" : ""}`}
                    id="p-dot-geo-custom"
                    title="Tùy chỉnh hình đang áp dụng"
                  />
                </span>
              </button>
            </div>

            {/* Expanded Toolbar Main */}
            <div
              className={`toolbar-3d-capsule toolbar-3d-Main${tbCollapsed ? " is-collapsed" : ""}`}
              id="toolbar-3d-expanded"
              role="toolbar"
              aria-label="Công cụ mô hình 3D"
            >
              <div
                className="tb-drag-grip"
                id="tb-drag-grip"
                title="Kéo để di chuyển thanh công cụ 3D"
                onPointerDown={handleToolbarDragStart}
              >
                <svg
                  viewBox="0 0 10 14"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <circle cx="3" cy="2.5" r="1.2" />
                  <circle cx="7" cy="2.5" r="1.2" />
                  <circle cx="3" cy="7" r="1.2" />
                  <circle cx="7" cy="7" r="1.2" />
                  <circle cx="3" cy="11.5" r="1.2" />
                  <circle cx="7" cy="11.5" r="1.2" />
                </svg>
              </div>

              <div className="tb-divider tb-sep" aria-hidden="true" />

              <button
                type="button"
                className={`tb-btn${xray ? " is-active" : ""}`}
                id="btn-xray"
                title="Chế độ X-ray (nhìn xuyên khối)"
                data-tooltip="X-ray (Nhìn xuyên mặt khuất)"
                aria-label="Chế độ X-ray (nhìn xuyên khối)"
                aria-pressed={xray}
                onClick={() => {
                  pushUndoSnapshot();
                  setXray((v) => !v);
                }}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6Z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              </button>

              <button
                type="button"
                className="tb-btn"
                id="btn-undo-interaction"
                title="Hoàn tác thao tác vừa thực hiện (Ctrl+Z)"
                data-tooltip="Hoàn tác (Ctrl+Z)"
                aria-label="Hoàn tác thao tác"
                disabled={undoStack.length === 0}
                onClick={handleUndoInteraction}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M9 14 4 9l5-5" />
                  <path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11" />
                </svg>
              </button>

              <button
                type="button"
                className="tb-btn"
                id="btn-reset-pos"
                title="Đặt lại góc nhìn 3D & vị trí thanh công cụ"
                data-tooltip="Đặt lại góc nhìn chuẩn"
                aria-label="Đặt lại góc nhìn 3D"
                onClick={handleResetView}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
                  <path d="M3 3v5h5" />
                </svg>
              </button>

              <div className="tb-divider tb-sep" aria-hidden="true" />

              <button
                type="button"
                className={`tb-btn${displayPopOpen ? " is-active" : ""}`}
                id="btn-display-pop"
                title="Tùy chọn hiển thị lớp 3D"
                data-tooltip="Tùy chọn hiển thị lớp 3D"
                aria-label="Tùy chọn hiển thị"
                aria-expanded={displayPopOpen}
                onClick={() => {
                  setGeoCustomOpen(false);
                  setDisplayPopOpen((v) => !v);
                }}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <line x1="4" y1="6" x2="20" y2="6" />
                  <line x1="4" y1="12" x2="20" y2="12" />
                  <line x1="4" y1="18" x2="20" y2="18" />
                  <circle cx="9" cy="6" r="2" fill="#FFF" />
                  <circle cx="15" cy="12" r="2" fill="#FFF" />
                  <circle cx="10" cy="18" r="2" fill="#FFF" />
                </svg>
              </button>

              <button
                type="button"
                className={`tb-btn${geoCustomOpen ? " is-active" : ""}${
                  isGeoParamsDirty ? " is-dirty" : ""
                }`}
                id="btn-geo-custom-pop"
                title="Tùy chỉnh thông số hình học & mặt phẳng cắt"
                data-tooltip="Tùy chỉnh hình"
                aria-label="Tùy chỉnh thông số hình học & mặt phẳng cắt"
                aria-expanded={geoCustomOpen}
                onClick={() => {
                  setDisplayPopOpen(false);
                  setGeoCustomOpen((v) => !v);
                }}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 3v18" />
                  <path d="M5 8h14" />
                  <path d="M5 16h14" />
                  <circle cx="9" cy="8" r="2.2" fill="#FFF" />
                  <circle cx="15" cy="16" r="2.2" fill="#FFF" />
                </svg>
              </button>

              <div className="tb-divider tb-sep" aria-hidden="true" />

              <button
                type="button"
                className="tb-collapse-btn"
                id="btn-tb-collapse"
                title="Thu gọn thanh công cụ 3D"
                data-tooltip="Thu gọn công cụ"
                aria-label="Thu gọn thanh công cụ"
                onClick={() => {
                  setDisplayPopOpen(false);
                  setGeoCustomOpen(false);
                  setTbCollapsed(true);
                }}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="m15 18-6-6 6-6" />
                </svg>
              </button>
            </div>
          </div>
          )}

          {/* ── FLOATING GEOMETRY CUSTOMIZATION POPOVER (#tb-geo-custom-pop, direct child of #stage-3d-box) ── */}
          {stageControlsInteractive && (
          <div
            ref={geoCustomPopRef}
            className={`geo-custom-floating-pop${geoCustomOpen ? " open is-open" : ""}${
              geoCustomDragging ? " is-dragging" : ""
            }${geoCustomPos ? " is-custom-dragged" : ""}`}
            id="tb-geo-custom-pop"
            role="dialog"
            aria-label="Tùy chỉnh hình học 3D"
            aria-hidden={!geoCustomOpen}
            style={
              geoCustomPos
                ? {
                    left: `${geoCustomPos.x}px`,
                    top: `${geoCustomPos.y}px`,
                    right: "auto",
                    bottom: "auto",
                    transform: "none",
                  }
                : undefined
            }
            onPointerDown={(e) => e.stopPropagation()}
            onWheel={(e) => e.stopPropagation()}
          >
            <div
              className="geo-custom-pop-header"
              id="geo-custom-pop-header"
              title="Kéo để di chuyển bảng Tùy chỉnh hình"
              onPointerDown={handleGeoCustomDragStart}
            >
              <div className="geo-custom-pop-title">
                <svg
                  className="geo-custom-grip-icon"
                  viewBox="0 0 12 16"
                  aria-hidden="true"
                >
                  <circle cx="3.5" cy="3.5" r="1.2" />
                  <circle cx="8.5" cy="3.5" r="1.2" />
                  <circle cx="3.5" cy="8.0" r="1.2" />
                  <circle cx="8.5" cy="8.0" r="1.2" />
                  <circle cx="3.5" cy="12.5" r="1.2" />
                  <circle cx="8.5" cy="12.5" r="1.2" />
                </svg>
                <span>Tùy chỉnh hình</span>
                <span className="geo-custom-scene-chip" id="geo-custom-scene-chip">
                  {loaiCanh.label}
                </span>
              </div>
              <div className="geo-custom-pop-actions">
                <button
                  type="button"
                  className="geo-custom-reset-btn"
                  id="btn-reset-geo-custom"
                  title="Khôi phục thông số mặc định của đề bài"
                  disabled={!isGeoParamsDirty}
                  onClick={handleResetGeoCustom}
                >
                  <span>Đặt lại</span>
                </button>
                <button
                  type="button"
                  className="geo-custom-close-btn"
                  id="btn-close-geo-custom"
                  title="Đóng bảng tùy chỉnh (Esc)"
                  aria-label="Đóng bảng tùy chỉnh"
                  onClick={() => setGeoCustomOpen(false)}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
            </div>

            <div
              className="geo-custom-pop-body"
              id="geo-custom-pop-body"
              onWheel={(e) => e.stopPropagation()}
            >
              <div className="geo-custom-group">
                <div className="geo-custom-group-title">
                  <span>{nhanMucHienThi}</span>
                  <span className="geo-custom-group-badge">Giữ nguyên dữ kiện đề</span>
                </div>
                <div className="geo-custom-row">
                  <div className="geo-custom-label-line">
                    <span className="geo-custom-label">Độ đục vỏ khối</span>
                    <span
                      className="geo-custom-val"
                      id="val-shell-opacity"
                      data-geo-readout="shellOpacityPct"
                    >
                      {`${shellOpacityPct}%`}
                    </span>
                  </div>
                  <input
                    type="range"
                    id="slider-shell-opacity"
                    className="geo-custom-slider"
                    data-geo-slider="shellOpacityPct"
                    min={4}
                    max={36}
                    step={1}
                    value={shellOpacityPct}
                    aria-label="Độ đục vỏ khối"
                    onPointerDown={() => pushUndoSnapshot()}
                    onChange={(e) => setShellOpacityPct(Number(e.target.value))}
                  />
                  <div className="geo-custom-hints">
                    <span>Trong suốt (4%)</span>
                    <span>Đậm (36%)</span>
                  </div>
                </div>
                <div className="geo-custom-row">
                  <div className="geo-custom-label-line">
                    <span className="geo-custom-label">Độ đậm mặt phẳng cắt (α)</span>
                    <span
                      className="geo-custom-val"
                      id="val-plane-opacity"
                      data-geo-readout="planeOpacityPct"
                    >
                      {`${planeOpacityPct}%`}
                    </span>
                  </div>
                  <input
                    type="range"
                    id="slider-plane-opacity"
                    className="geo-custom-slider"
                    data-geo-slider="planeOpacityPct"
                    min={4}
                    max={24}
                    step={1}
                    value={planeOpacityPct}
                    aria-label="Độ đậm mặt phẳng cắt"
                    onPointerDown={() => pushUndoSnapshot()}
                    onChange={(e) => setPlaneOpacityPct(Number(e.target.value))}
                  />
                  <div className="geo-custom-hints">
                    <span>Nhạt (4%)</span>
                    <span>Rõ (24%)</span>
                  </div>
                </div>
              </div>

              <div className="geo-custom-divider" />

              <div className="geo-custom-group" id="geo-custom-experiment-group">
                <div className="geo-custom-group-title">
                  <span>Thử nghiệm hình học</span>
                  <span className="geo-custom-group-badge is-exploratory">
                    Khóa theo Kernel
                  </span>
                </div>
                {loaiCanh.key === "sphere" && (
                  <>
                    <div className="geo-custom-row">
                      <div className="geo-custom-label-line">
                        <span className="geo-custom-label">Vị trí mặt phẳng cắt (OH / R)</span>
                        <span className="geo-custom-val">Theo đề</span>
                      </div>
                      <input
                        type="range"
                        id="slider-plane-height"
                        className="geo-custom-slider"
                        data-geo-slider="spherePlaneRatio"
                        min={0}
                        max={92}
                        step={1}
                        value={60}
                        disabled
                        aria-disabled="true"
                        aria-label="Vị trí mặt phẳng cắt (OH / R)"
                      />
                    </div>
                    <div className="geo-custom-row">
                      <div className="geo-custom-label-line">
                        <span className="geo-custom-label">Góc nghiêng mặt phẳng (α)</span>
                        <span className="geo-custom-val">0°</span>
                      </div>
                      <input
                        type="range"
                        id="slider-plane-tilt"
                        className="geo-custom-slider"
                        data-geo-slider="spherePlaneTiltDeg"
                        min={-35}
                        max={35}
                        step={1}
                        value={0}
                        disabled
                        aria-disabled="true"
                        aria-label="Góc nghiêng mặt phẳng (α)"
                      />
                    </div>
                    <div className="geo-custom-row">
                      <div className="geo-custom-label-line">
                        <span className="geo-custom-label">Bán kính mặt cầu (R)</span>
                        <span className="geo-custom-val">1.00×</span>
                      </div>
                      <input
                        type="range"
                        id="slider-sphere-radius"
                        className="geo-custom-slider"
                        data-geo-slider="sphereRadiusScale"
                        min={75}
                        max={125}
                        step={1}
                        value={100}
                        disabled
                        aria-disabled="true"
                        aria-label="Bán kính mặt cầu (R)"
                      />
                    </div>
                  </>
                )}
                {loaiCanh.key === "pyramid" && (
                  <>
                    <div className="geo-custom-row">
                      <div className="geo-custom-label-line">
                        <span className="geo-custom-label">Độ cao mặt phẳng cắt (t)</span>
                        <span className="geo-custom-val">Theo đề</span>
                      </div>
                      <input
                        type="range"
                        className="geo-custom-slider"
                        data-geo-slider="pyramidPlaneRatio"
                        min={18}
                        max={82}
                        step={1}
                        value={50}
                        disabled
                        aria-disabled="true"
                        aria-label="Độ cao mặt phẳng cắt (t)"
                      />
                    </div>
                    <div className="geo-custom-row">
                      <div className="geo-custom-label-line">
                        <span className="geo-custom-label">Tỷ lệ chiều cao chóp (SO)</span>
                        <span className="geo-custom-val">1.00×</span>
                      </div>
                      <input
                        type="range"
                        className="geo-custom-slider"
                        data-geo-slider="pyramidHeightScale"
                        min={70}
                        max={135}
                        step={1}
                        value={100}
                        disabled
                        aria-disabled="true"
                        aria-label="Tỷ lệ chiều cao chóp (SO)"
                      />
                    </div>
                  </>
                )}
                {loaiCanh.key === "cylinder" && (
                  <>
                    <div className="geo-custom-row">
                      <div className="geo-custom-label-line">
                        <span className="geo-custom-label">Vị trí mặt cắt dọc trục</span>
                        <span className="geo-custom-val">Theo đề</span>
                      </div>
                      <input
                        type="range"
                        className="geo-custom-slider"
                        data-geo-slider="cylinderPlaneOffset"
                        min={-65}
                        max={65}
                        step={1}
                        value={0}
                        disabled
                        aria-disabled="true"
                        aria-label="Vị trí mặt cắt dọc trục"
                      />
                    </div>
                    <div className="geo-custom-row">
                      <div className="geo-custom-label-line">
                        <span className="geo-custom-label">Tỷ lệ chiều cao trụ (OO&apos;)</span>
                        <span className="geo-custom-val">1.00×</span>
                      </div>
                      <input
                        type="range"
                        className="geo-custom-slider"
                        data-geo-slider="cylinderHeightScale"
                        min={75}
                        max={130}
                        step={1}
                        value={100}
                        disabled
                        aria-disabled="true"
                        aria-label="Tỷ lệ chiều cao trụ"
                      />
                    </div>
                  </>
                )}
                {(loaiCanh.key === "cone" || loaiCanh.key === "solid") && (
                  <>
                    <div className="geo-custom-row">
                      <div className="geo-custom-label-line">
                        <span className="geo-custom-label">Độ cao mặt phẳng cắt</span>
                        <span className="geo-custom-val">Theo đề</span>
                      </div>
                      <input
                        type="range"
                        className="geo-custom-slider"
                        data-geo-slider="conePlaneRatio"
                        min={20}
                        max={80}
                        step={1}
                        value={48}
                        disabled
                        aria-disabled="true"
                        aria-label="Độ cao mặt phẳng cắt"
                      />
                    </div>
                    <div className="geo-custom-row">
                      <div className="geo-custom-label-line">
                        <span className="geo-custom-label">Tỷ lệ chiều cao khối (SO)</span>
                        <span className="geo-custom-val">1.00×</span>
                      </div>
                      <input
                        type="range"
                        className="geo-custom-slider"
                        data-geo-slider="coneHeightScale"
                        min={75}
                        max={130}
                        step={1}
                        value={100}
                        disabled
                        aria-disabled="true"
                        aria-label="Tỷ lệ chiều cao khối"
                      />
                    </div>
                  </>
                )}
                <div className="geo-custom-Dirty-banner is-visible" id="geo-custom-kernel-note">
                  <span>
                    Tọa độ đỉnh và thiết diện được khóa bởi Kernel hữu tỉ theo đúng dữ kiện đề bài.
                  </span>
                </div>
              </div>
            </div>
          </div>
          )}
        </main>

        {/* ── RIGHT / BOTTOM: UNIFIED STUDY DOCK (#ws-dock) ───────────────── */}
        <aside
          className={`study-dock${dockCollapsed ? " is-collapsed" : ""}`}
          id="ws-dock"
          aria-label="Khung học tập: Đề bài và Các bước dựng hình"
        >
          {/* Mobile compact problem bar (hiển thị trên <=820px khi tiêu đề trên header ẩn) */}
          <div className="dock-mobile-prob-bar" id="dock-mobile-prob-bar">
            <svg
              className="dock-mobile-prob-icon"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path d="M12 2 4 6.5v11L12 22l8-4.5v-11L12 2Z" />
            </svg>
            {isCompactProbHeader ? (
              <h1 className="dock-mobile-prob-text" id="dock-mobile-prob-title">{problemTitleText}</h1>
            ) : (
              <span className="dock-mobile-prob-text" id="dock-mobile-prob-title">{problemTitleText}</span>
            )}
          </div>

          <div className="dock-scroll-wrap">
            <div className="dock-scroll axo-custom-scroll" ref={dockScrollRef}>
            {/* SECTION A: ĐỀ BÀI */}
            <div className="dock-section">
              <div className="dock-sec-head">
                <span className="dock-sec-title">
                  ĐỀ BÀI
                  {isInternalFixtureCase && (
                    <span className="dock-fixture-tag" data-fixture-tag="">
                      Mẫu kiểm thử kỹ thuật
                    </span>
                  )}
                </span>
                <button
                  type="button"
                  className="dock-collapse-pill-btn"
                  id="btn-collapse-dock"
                  title="Thu gọn bảng Học tập"
                  onClick={() => {
                    setDockCollapsed(true);
                  }}
                >
                  <span>Thu gọn</span>
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="m9 18 6-6-6-6" />
                  </svg>
                </button>
              </div>
              <div className="problem-statement" id="dock-prob-statement" data-statement-source={deSource}>
                <MathDisplay text={problemStatementText} />
              </div>
              {givenParamsAtStep.length > 0 && (
                <div
                  className="dock-given-params"
                  id="dock-given-params"
                  aria-label="Thông số đề cho đã chứng thực"
                >
                  <span className="dock-given-params-label">Thông số đề cho:</span>
                  <div className="dock-given-params-list">
                    {givenParamsAtStep.map((gp) => {
                      const isPicked = gp.status !== "pending_step" && tt.selected_id === gp.id;
                      return (
                        <button
                          key={gp.id}
                          type="button"
                          className={`dock-given-param-pill${
                            gp.status === "on_canvas" ? " is-on-canvas" : ""
                          }${isPicked ? " is-selected" : ""}`}
                          data-given-param-id={gp.id}
                          data-given-param-status={gp.status}
                          disabled={gp.status === "pending_step"}
                          aria-pressed={isPicked}
                          onClick={() => {
                            if (gp.status === "pending_step") return;
                            chon(isPicked ? null : gp.id);
                          }}
                        >
                          <MathDisplay text={gp.text} />
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {(tt.hidden_ids.length > 0 || tt.isolated_ids.length > 0) && (
              <div className="dock-visibility-restore-bar" id="dock-visibility-restore-bar">
                <span className="dock-visibility-restore-text">
                  {tt.isolated_ids.length > 0
                    ? "Đang chỉ xem phần liên quan"
                    : `Đang ẩn ${tt.hidden_ids.length} đối tượng`}
                </span>
                <button
                  type="button"
                  className="context-action-pill"
                  id="btn-restore-hidden-objects"
                  onClick={() => {
                    pushUndoSnapshot();
                    setTt((s) => showAll(clearIsolate(s)));
                  }}
                >
                  Hiện lại tất cả
                </button>
              </div>
            )}
            {/* CONTEXTUAL SELECTED OBJECT CARD MOUNT */}
            <div
              className="dock-context-mount"
              id="dock-context-object-mount"
              data-context-object={dangChon?.id ?? undefined}
            >
              {dangChon && (() => {
                const objPres = resolveStudentObjectPresentation(day, dangChon.id, buocHien);
                const verifiedObjTip = buildVerifiedObjectTooltip(day, dangChon.id, buocHien);
                const selectedQtyProv = laDaiLuong ? classifySceneEntityProvenance(day, dangChon) : "DERIVED_VERIFIED";
                const canShowStudentEntityValue = presentationPolicy.canDisplayEntityValue(dangChon);
                const canShowStudentEntityFormula = presentationPolicy.canDisplayEntityFormula(dangChon);
                const rawRoleForStudent = objPres?.role ?? presentationPolicy.formatStudentObjectRole(dangChon);
                const safeRoleForStudent =
                  rawRoleForStudent
                  && dangChon.type === "plane3"
                  && !isExplicitOxyzCoordinateScene(day, dangChon)
                  && /phương\s+trình/iu.test(rawRoleForStudent)
                    ? "Mặt phẳng"
                    : rawRoleForStudent;
                const resolvedTitle =
                  dangChon.type === "section" && ctThietDien && ctThietDien.vertexNames.length > 0
                    ? tenThietDien(dangChon)
                    : (objPres?.title ?? (sanitizeStudentDescriptorText(dangChon.label) || dangChon.label));
                const resolvedDesc = objPres?.description ?? verifiedObjTip?.body ?? null;
                const accentDotHex = objPres?.accentHex ?? verifiedObjTip?.accentHex;
                return (
                <div className="context-object-card">
                  <div className="context-card-head">
                    <div className="context-card-title" id="ctx-obj-name">
                      <span
                        className="context-card-dot"
                        style={accentDotHex ? { backgroundColor: accentDotHex } : undefined}
                        aria-hidden="true"
                      />
                      <span id="ctx-obj-title">
                        <MathDisplay text={resolvedTitle} />
                      </span>
                    </div>
                    <button
                      type="button"
                      className="context-card-close"
                      id="btn-clear-pick"
                      title="Bỏ chọn đối tượng (Esc)"
                      aria-label="Bỏ chọn đối tượng"
                      onClick={() => chon(null)}
                    >
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2.2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        aria-hidden="true"
                      >
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  </div>
                  {safeRoleForStudent && (
                    <div className="context-card-meta-badges">
                      <span className="context-card-role-badge">
                        {safeRoleForStudent}
                      </span>
                    </div>
                  )}
                  <div className="context-card-body" id="ctx-obj-desc">
                    {resolvedDesc && (
                      <div
                        className="context-card-meta-line context-card-verified-relation"
                        data-verified-relation={dangChon.id}
                      >
                        <MathDisplay text={resolvedDesc} />
                      </div>
                    )}
                    {objPres?.evidence && (
                      <div className="context-card-meta-line context-card-evidence">
                        <MathDisplay text={objPres.evidence} />
                      </div>
                    )}
                    {dangChon.parent && (
                      <div className="context-card-meta-line">
                        Thuộc <strong>{ten(dangChon.parent)}</strong>
                      </div>
                    )}
                    {formula && !dapAnAn.has(dangChon.id) && canShowStudentEntityFormula && (
                      <div
                        className="context-card-formula"
                        data-formula-entity={dangChon.id}
                      >
                        <MathDisplay text={formula.text} />
                      </div>
                    )}
                    {!formula && laDaiLuong && !dapAnAn.has(dangChon.id) && canShowStudentEntityValue && (
                      <div
                        className="context-card-formula"
                        data-value-entity={dangChon.id}
                      >
                        <MathDisplay text={giaTri(dangChon.id)} />
                      </div>
                    )}
                    {laDaiLuong && !dapAnAn.has(dangChon.id) && selectedQtyProv === "UNDERDETERMINED" && (
                      <div
                        className="context-card-formula"
                        data-underdetermined-entity={dangChon.id}
                      >
                        Chưa có chứng nhận kết quả từ dữ kiện đề bài
                      </div>
                    )}
                    {nguon &&
                      ((canShowStudentEntityValue && nguon.givens.length > 0) || doTren.length > 0) && (
                        <div className="context-card-sources" id="ctx-obj-meta">
                          {canShowStudentEntityValue && nguon.givens.length > 0 && (
                            <div>
                              <span>Từ dữ kiện đề cho:</span>{" "}
                              <strong>
                                {nguon.givens.map(giaTri).join(", ")}
                              </strong>
                            </div>
                          )}
                          {doTren.length > 0 && (
                            <div>
                              <span>Đo trên:</span>{" "}
                              <strong>
                                {[...new Set(doTren.map(ten))].join(", ")}
                              </strong>
                            </div>
                          )}
                        </div>
                      )}
                    {dangChon.source?.assumption &&
                      (isExplicitOxyzCoordinateScene(day, dangChon) ||
                        !/hệ\s+trục|gốc\s+toạ\s+độ|gốc\s+tọa\s+độ/iu.test(dangChon.source.assumption)) && (
                      <div className="context-card-meta-line">
                        Giả thiết dựng: <strong>{dangChon.source.assumption}</strong>
                      </div>
                    )}
                    <div className="context-card-actions">
                      <button
                        type="button"
                        id="btn-card-isolate"
                        className={`context-action-pill${tt.isolated_ids.includes(dangChon.id) ? " is-active" : ""}`}
                        onClick={() => {
                          pushUndoSnapshot();
                          setTt((s) =>
                            s.isolated_ids.includes(dangChon.id)
                              ? clearIsolate(s)
                              : isolate(s, [
                                  dangChon.id,
                                  ...directDependencies(day, dangChon.id),
                                ]),
                          );
                        }}
                      >
                        {tt.isolated_ids.includes(dangChon.id)
                          ? "Hiện lại toàn hình"
                          : "Chỉ xem phần này"}
                      </button>
                      <button
                        type="button"
                        id="btn-card-hide"
                        className={`context-action-pill${tt.hidden_ids.includes(dangChon.id) ? " is-active" : ""}`}
                        onClick={() => {
                          pushUndoSnapshot();
                          setTt((s) =>
                            s.hidden_ids.includes(dangChon.id)
                              ? show(s, dangChon.id)
                              : hide(s, dangChon.id),
                          );
                        }}
                      >
                        {tt.hidden_ids.includes(dangChon.id) ? "Hiện lại đối tượng" : "Ẩn đối tượng"}
                      </button>
                    </div>
                  </div>
                </div>
                );
              })()}
            </div>

            {/* SECTION B: CÁC BƯỚC DỰNG HÌNH */}
            <div className="dock-section">
              <div className="dock-sec-head">
                <span className="dock-sec-title" id="dock-steps-heading">
                  {invalidSceneReason !== null
                    ? "CÁC BƯỚC DỰNG HÌNH"
                    : mathVerification.valid
                      ? "CÁC BƯỚC DỰNG HÌNH"
                      : "KIỂM CHỨNG TOÁN HỌC"}
                </span>
                <span className="dock-steps-progress-tag" id="dock-steps-counter">
                  {invalidSceneReason !== null
                    ? "Tạm gián đoạn"
                    : mathVerification.valid
                      ? `Bước ${buocHinh + 1}/${tong}`
                      : "Mâu thuẫn dữ kiện"}
                </span>
              </div>
              {invalidSceneReason !== null ? (
                <ul
                  ref={stepsListRef}
                  className="steps-list"
                  id="dock-steps-ul"
                  aria-label="Các bước dựng hình"
                  data-stage-fault="invalid_scene_data"
                >
                  <li className="step-row">
                    <span className="step-num">—</span>
                    <div className="step-content">
                      <div className="step-title">Chưa thể hiển thị trình tự dựng hình</div>
                      <div className="step-detail-sub">
                        Dữ liệu mô hình 3D của bản ghi này không hợp lệ; em vẫn có thể đối chiếu đề bài phía trên hoặc dựng lại trên Trang chủ.
                      </div>
                    </div>
                  </li>
                </ul>
              ) : mathVerification.valid ? (
                <>
                  <ul
                    ref={stepsListRef}
                    className="steps-list"
                    id="dock-steps-ul"
                    aria-label="Các bước dựng hình"
                    data-goal-status={pedPlan.goalCompletion.status}
                    data-goal-kind={pedPlan.goalCompletion.primaryKind}
                  >
                    {dsBuoc.map((b) => {
                      const active = b.index === buocHinh;
                      const fallbackDisplay = moTaBuocDungHienThi(day, b);
                      const stepNarration =
                        b.narration
                        ?? buildPedagogicalStepNarration(day, {
                          ...b,
                          title: fallbackDisplay.title,
                          subtitle: fallbackDisplay.subtitle,
                        });
                      const tieuDeBuoc = stepNarration.actionTitle || fallbackDisplay.title;
                      const moTa = stepNarration.conciseRationale;
                      const chungCuChiTiet = active ? stepNarration.detailedEvidence : [];
                      const isEvidenceOpen = active && expandedEvidenceStep === b.index;
                      const onSelectStepRow = () => {
                        setDangPhat(false);
                        if (b.index !== buocHinh) {
                          setExpandedEvidenceStep(null);
                        } else if (b.index === 0) {
                          setReplayNonce((n) => n + 1);
                        }
                        setStep(b.anchor);
                      };
                      return (
                        <li
                          key={b.index}
                          className={`step-row${active ? " is-active" : ""}`}
                          data-step={b.index}
                          data-geometry-step={b.index}
                          data-step-category={b.epistemicCategory}
                          aria-current={active ? "step" : undefined}
                          tabIndex={0}
                          role="button"
                          onClick={onSelectStepRow}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault();
                              onSelectStepRow();
                            }
                          }}
                        >
                          <span className="step-num">{b.index + 1}</span>
                          <div className="step-content">
                            <div className="step-title">
                              <MathDisplay text={tieuDeBuoc} />
                            </div>
                            {(b.categoryLabel || moTa) && (
                              <div className="step-detail-sub">
                                {b.categoryLabel && (
                                  <span className={`step-kind-badge is-${b.epistemicCategory}`}>
                                    {b.categoryLabel}
                                  </span>
                                )}
                                {moTa && <MathDisplay text={moTa} />}
                              </div>
                            )}
                            {active && chungCuChiTiet.length > 0 && (
                              <>
                                <button
                                  type="button"
                                  className="step-evidence-toggle"
                                  data-step-evidence-toggle={b.index}
                                  aria-expanded={isEvidenceOpen}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setExpandedEvidenceStep(isEvidenceOpen ? null : b.index);
                                  }}
                                >
                                  {isEvidenceOpen ? "Thu gọn" : "Xem giải thích"}
                                </button>
                                {isEvidenceOpen && (
                                  <div className="step-evidence-drawer">
                                    {chungCuChiTiet.map((ld, idx) => (
                                      <div key={idx} className="step-evidence-item geo3d-cac-buoc-vi-sao">
                                        <MathDisplay text={ld} />
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </>
                            )}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                  {presentationPolicy.showDiagnosticNotice && pedPlan.goalCompletion.status !== "reached" && (
                    <div
                      className={`dock-goal-summary is-${pedPlan.goalCompletion.status}`}
                      id="dock-goal-summary"
                      data-goal-status={pedPlan.goalCompletion.status}
                      data-goal-kind={pedPlan.goalCompletion.primaryKind}
                    >
                      <div className="dock-goal-head">
                        <span className="dock-goal-title">MỤC TIÊU BÀI TOÁN</span>
                        <span className={`dock-goal-status-pill is-${pedPlan.goalCompletion.status}`}>
                          {pedPlan.goalCompletion.status === "missing_goal_output"
                              ? "Chưa đủ kết quả mục tiêu"
                              : "Chưa đủ chứng cứ nhất quán"}
                        </span>
                      </div>
                      <div className="dock-goal-detail">
                        <MathDisplay text={pedPlan.goalCompletion.detail} />
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <ul className="steps-list" id="dock-steps-ul">
                  <li className="step-row ws-math-contradiction-note">
                    <span className="step-num">—</span>
                    <div className="step-content">
                      <div className="step-title">
                        <span>Tạm dừng dựng hình</span>
                        <span className="step-kind-badge is-auxiliary">Mâu thuẫn dữ kiện</span>
                      </div>
                      <div className="step-detail-sub">
                        {mathVerification.contradictions[0]?.explanation ??
                          "Không thể tạo trình tự dựng hình do dữ kiện đầu vào mâu thuẫn toán học."}
                      </div>
                    </div>
                  </li>
                </ul>
              )}
            </div>

            {/* SECTION C: ĐỐI TƯỢNG TRONG HÌNH (chọn nhanh đồng bộ 2 chiều với Scene3D) */}
            {invalidSceneReason === null && mathVerification.valid && entityGroups.all.length > 0 && (
              <div className="dock-section dock-sec-entities">
                <div className="dock-sec-head">
                  <span className="dock-sec-title">
                    <svg
                      width="13"
                      height="13"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <circle cx="12" cy="12" r="3" />
                      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
                    </svg>
                    Đối tượng tại bước này
                  </span>
                </div>
                <div className="dock-entities-pills" id="dock-entities-pills">
                  {entityGroups.primary.length > 0 && (
                    <div className="dock-entity-tier">
                      <span className="dock-entity-tier-label">Chính ở bước này</span>
                      <div className="dock-entity-tier-pills">
                        {entityGroups.primary.map((item) => {
                          const isSelected = tt.selected_id === item.id;
                          return (
                            <button
                              key={item.id}
                              type="button"
                              className={`dock-entity-chip is-primary${isSelected ? " is-selected" : ""}`}
                              data-entity-chip={item.id}
                              data-entity-tier="primary"
                              aria-pressed={isSelected}
                              aria-label={item.fullTooltip}
                              title={item.fullTooltip}
                              onClick={() => chon(isSelected ? null : item.id)}
                            >
                              {item.shortLabel}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  {entityGroups.context.length > 0 && (
                    <div className="dock-entity-tier">
                      <span className="dock-entity-tier-label">Liên quan trực tiếp</span>
                      <div className="dock-entity-tier-pills">
                        {entityGroups.context.map((item) => {
                          const isSelected = tt.selected_id === item.id;
                          return (
                            <button
                              key={item.id}
                              type="button"
                              className={`dock-entity-chip${isSelected ? " is-selected" : ""}`}
                              data-entity-chip={item.id}
                              data-entity-tier="context"
                              aria-pressed={isSelected}
                              aria-label={item.fullTooltip}
                              title={item.fullTooltip}
                              onClick={() => chon(isSelected ? null : item.id)}
                            >
                              {item.shortLabel}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  {entityGroups.other.length > 0 && (
                    <div className="dock-entity-more-wrap">
                      <button
                        type="button"
                        className="dock-entity-more-btn"
                        id="btn-dock-entities-more"
                        aria-expanded={effectiveMoreEntitiesOpen}
                        onClick={() => setMoreEntitiesOpen((v) => !v)}
                      >
                        {effectiveMoreEntitiesOpen
                          ? "Thu gọn đối tượng nền"
                          : `Xem thêm ${entityGroups.other.length} đối tượng khác`}
                      </button>
                      <div
                        className="dock-entity-more-body"
                        hidden={!effectiveMoreEntitiesOpen}
                      >
                        {entityGroups.other.map((item) => {
                          const isSelected = tt.selected_id === item.id;
                          return (
                            <button
                              key={item.id}
                              type="button"
                              className={`dock-entity-chip${isSelected ? " is-selected" : ""}`}
                              data-entity-chip={item.id}
                              data-entity-tier="other"
                              aria-pressed={isSelected}
                              aria-label={item.fullTooltip}
                              title={item.fullTooltip}
                              onClick={() => chon(isSelected ? null : item.id)}
                            >
                              {item.shortLabel}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
                {phanTichToan.requestedResults.length > 0 && (
                  <div className="dock-analysis-summary" data-workspace-analysis="">
                    {hybridTaiBuoc(hybrid, day, buocHien).observations.map((o) => (
                      <span
                        key={`${o.group}:${o.check_id}`}
                        className="dock-observation-note"
                        data-route-d-observation=""
                      >
                        {cauQuanSat(o)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
          <AxoScrollbar targetRef={dockScrollRef} />
        </div>
      </aside>
      </div>
    </section>
  );
}

const DANH_TU_LOAI_DON = new Set([
  "Điểm",
  "Đường thẳng",
  "Đoạn thẳng",
  "Mặt phẳng",
  "Mặt phẳng cắt",
  "Đa giác",
  "Đường tròn",
  "Elip",
  "Thiết diện",
  "Khối đa diện",
  "Khối cong",
]);

/**
 * Diễn giải tiêu đề & mô tả phụ của bước dựng từ metadata ngữ nghĩa đã kiểm chứng trong `Scene3D`.
 *
 * Nguyên tắc bất biến:
 * - Không hardcode mã bài toán, ký hiệu riêng hay nội dung mặt cầu.
 * - Không suy diễn dữ kiện ngoài cấu trúc `SceneObject` (`role`, `producer`, `surface_role`) do backend phát.
 * - Khi nhãn bước chỉ là ký hiệu trần không khoảng trắng (như `(S)`, `(P)`, `M`, `(MNP)`, `BC`, `OO′`),
 *   ghép vai trò/phép dựng đã xác thực của đối tượng được tạo tại bước đó để học sinh hiểu ngay bước đang dựng gì.
 */
export function moTaBuocDungHienThi(
  scene: Scene3D,
  b: { index: number; anchor: number; label: string; title?: string; subtitle?: string },
): { title: string; subtitle: string } {
  if (typeof b?.title === "string" && b.title.trim()) {
    return { title: b.title.trim(), subtitle: (b.subtitle ?? "").trim() };
  }
  const rawLabel = (b?.label ?? "").trim();
  let title = rawLabel;

  if (b && b.index > 0 && rawLabel) {
    const focus = geometryFocusAt(scene, b.anchor);
    const created = focus.created
      ? scene.objects.find((o) => o.id === focus.created)
      : undefined;

    if (
      created &&
      typeof created.role === "string" &&
      created.role.trim() &&
      learnerTextIsSafe(scene, created.role.trim())
    ) {
      const vaiTro = created.role.trim();
      if (!/\s/u.test(rawLabel)) {
        if (vaiTro === rawLabel || vaiTro.includes(rawLabel)) {
          title = vaiTro;
        } else if (DANH_TU_LOAI_DON.has(vaiTro)) {
          title = `${vaiTro} ${rawLabel}`;
        } else {
          title = `${vaiTro} · ${rawLabel}`;
        }
      } else if (
        vaiTro.toLowerCase().startsWith(rawLabel.toLowerCase()) &&
        vaiTro.length > rawLabel.length
      ) {
        title = vaiTro;
      }
    }
  }

  const rawMoTa = b ? geometryNarrationAt(scene, b.anchor).trim() : "";
  const boilerplateSet = new Set([
    rawLabel,
    title,
    `Dựng ${rawLabel}.`,
    `Tiếp tục dựng ${rawLabel}.`,
    `Tính ${rawLabel}.`,
    `Dựng ${title}.`,
  ]);
  const subtitle = rawMoTa && !boilerplateSet.has(rawMoTa) ? rawMoTa : "";

  return { title, subtitle };
}

/**
 * M8: toggle 2D/3D — component THUẦN theo props (export để test SSR được:
 * store zustand trả initial state khi renderToString nên không test qua store).
 * Dưới 2 mode khả dụng → null: không affordance rỗng (triết lý M7.14D.1).
 */
export function VisualModeToggle({
  modes,
  mode,
  onSelect,
}: {
  modes: VisualMode[];
  mode: VisualMode;
  onSelect: (m: VisualMode) => void;
}) {
  if (modes.length < 2) return null;
  return (
    /* W4B-2V — ĐÂY LÀ "CÁCH XEM", KHÔNG PHẢI MỘT LỰA CHỌN KỸ THUẬT.
       Nhãn `2D`/`3D` trần đặt câu hỏi mà học sinh chưa có cơ sở trả lời ("nên
       hiểu bài này ở 2D hay 3D?"). Gọi đúng tên trách nhiệm — đổi CÁCH XEM một
       mô hình đã có sẵn biểu diễn chính — thì nó lùi về đúng vai phụ. */
    <span className="visual-mode-toggle" role="group" aria-label="Cách xem mô hình">
      <span className="visual-mode-label">Cách xem</span>
      {modes.map((m) => (
        <button
          key={m}
          type="button"
          className={`btn-utility${mode === m ? " is-active" : ""}`}
          onClick={() => onSelect(m)}
        >
          {m.toUpperCase()}
        </button>
      ))}
    </span>
  );
}

/**
 * (M17 W0) Thông báo "ngoài danh mục" cho HỌC SINH — component THUẦN theo
 * props (export để test SSR như VisualModeToggle). Ưu tiên `learner_reason`
 * (server gắn ở biên API, không token kỹ thuật); `reason` kỹ thuật chỉ là
 * fallback tương thích ngược cho envelope cũ. Không bao giờ render
 * error_code / failure_category / JSON path.
 */
/* (PRODUCT_RESPONSE_CONTRACT_ALIGNMENT) NHÃN TIẾNG VIỆT CHO GIAI ĐOẠN DỪNG.
 *
 * `THESIS_DRAFT §1.6/§3.9` hứa một *"từ chối có cấu trúc — nêu giai đoạn dừng,
 * loại thất bại, mã lỗi"*. Bề mặt học sinh trước bản này không hiện một chữ nào
 * về giai đoạn: `stage_reached` tới nơi rồi bị bỏ.
 *
 * ⚠️ Hiện NHÃN, không hiện mã. Luật `components/ui-hygiene.test.ts` cấm định
 * danh kĩ thuật lọt lên UI và cho phép đúng cách dùng này: *"dùng id làm KHOÁ
 * TRA bảng tên tiếng Việt — thứ hiện ra màn hình là cái TÊN, không phải cái
 * id"*. Bảng dưới đây là bảng TRÌNH BÀY; nó không phân loại gì cả, và không
 * được dùng để suy ra bất kỳ trường nào. Phân loại thuộc backend.
 *
 * Khoá phải phủ đủ: `test_nhan_giai_doan_phu_het_taxonomy_backend` (pytest)
 * đọc chính tệp này và đỏ khi backend phát ra một giai đoạn chưa có nhãn —
 * chống đúng lớp lỗi "hai bảng tên trôi khỏi nhau" kho đã dọn nhiều lần. */
export const NHAN_GIAI_DOAN: Record<string, string> = {
  domain: "nhận diện môn học",
  scope: "xét đề có mô phỏng được không",
  semantic_analyze: "đọc đề và chốt dữ kiện",
  semantic_program: "viết chương trình dựng hình",
  formation: "kiểm cấu trúc các mặt của khối",
  grounding: "truy dữ kiện về đề bài",
  ir_static: "thẩm định chương trình",
  structural_coverage: "đối chiếu với các phép dựng hệ có",
  realized_coverage: "kiểm lượt chạy có tạo ra thứ đề hỏi",
  execution: "chạy chương trình dựng hình",
  verification: "kiểm chứng kết quả bằng phép độc lập",
  source_invariant: "kiểm lại ràng buộc của đề",
  postconditions: "kiểm lại kết quả bằng hình",
  assumption: "kiểm đáp số chỉ phụ thuộc dữ kiện đề cho",
  construction_binding: "đối chiếu phép dựng điểm với câu của đề",
  binding: "nối kết quả vào màn hình",
  compile: "dựng cảnh 3D",
  transport: "đóng gói kết quả",
  learner_surface: "kiểm màn hình có đủ để hiểu bài",
  visual_coverage: "kiểm hình có dựng đủ vật đề yêu cầu",
  served: "đã phục vụ",
};

/* Nhãn LOẠI VẤN ĐỀ. Khoá là `error_code` (chi tiết hơn) rồi tới
 * `failure_category`. Cùng luật như trên: khoá kĩ thuật vào, tiếng Việt ra. */
export const NHAN_LOAI_VAN_DE: Record<string, string> = {
  requested_operation_uncovered: "yêu cầu nằm ngoài các phép dựng hệ có",
  semantic_program_invalid: "chương trình dựng hình chưa hợp lệ",
  input_not_grounded: "dữ kiện không truy được về đề bài",
  postcondition_violated: "kết quả không qua được phép kiểm lại",
  interpreter_budget_exhausted: "chương trình chạy quá dài",
  obligation_witness_unrealized: "chưa dựng ra thứ đề bài hỏi",
  semantic_verification_unavailable: "chưa có cách kiểm chứng độc lập",
  learner_surface_incomplete: "màn hình chưa đủ để hiểu bài",
  visual_obligation_uncovered: "hình chưa dựng ra vật mà đề yêu cầu nhìn thấy",
  pipeline_stage_incomplete: "chưa dựng đủ các bước",
  multiple_operations_not_supported: "đề hỏi nhiều việc cùng lúc",
  gate_out_of_scope: "đề thuộc môn học khác",
  gate_not_simulation_suitable: "đề không có gì để mô phỏng",
  insufficient_specification: "đề chưa đủ dữ kiện",
  semantic_incomplete: "đề chưa được biểu diễn trọn vẹn",
  geometry_generation_failed: "chưa dựng được chương trình mô phỏng",
  out_of_scope: "đề thuộc môn học khác",
  not_simulation_suitable: "đề không có gì để mô phỏng",
  capability_gap: "hệ chưa mô phỏng chính xác được cơ chế này",
  /* HFOI-F5: KHÔNG nói "chạy được" — lời từ chối loại này có thể dừng TRƯỚC khi dựng (preview: đối chiếu nguồn,
     mệnh đề mục tiêu, hình không duy nhất) và envelope không mang giai đoạn để biết. Nói đúng điều chắc chắn. */
  verification_gap: "chưa đủ bằng chứng kiểm chứng để hiển thị mô phỏng",
};

/* Envelope không mang `stage_reached`/`error_code`: envelope cũ (trước wave PRODUCT_RESPONSE_CONTRACT_ALIGNMENT)
 * VÀ envelope từ chối của preview (đúng sáu khoá, không có giai đoạn — HYBRID_PREVIEW_FRONTEND_CONTRACT §6). Nói thẳng
 * là không biết, không đoán bằng chuỗi `reason`, và không gán cho "phản hồi cũ" một phản hồi mới (HFOI-F6). */
const KHONG_XAC_DINH = "Không xác định được";

// Presentation of structured verifier codes; the backend still owns every refusal decision.
const GEOMETRY_REFUSAL_TEXT: Record<string, { title: string; reason: string }> = {
  CURVED_PLANE_DOES_NOT_CUT: { title: "KHÔNG CÓ GIAO TUYẾN", reason: "Mặt phẳng không cắt khối đã cho." },
  INCONSISTENT_FACTS: { title: "DỮ KIỆN MÂU THUẪN", reason: "Các dữ kiện đã cho không đồng thời tạo thành một hình hợp lệ. Em hãy kiểm tra lại các giả thiết và số liệu." },
  MISSING_CURVED_DIMENSION: { title: "CHƯA ĐỦ DỮ KIỆN", reason: "Chưa đủ kích thước để xác định hình. Em hãy bổ sung các kích thước còn thiếu." },
  UNDERDETERMINED_POINT: { title: "CHƯA ĐỦ DỮ KIỆN", reason: "Các giả thiết chưa xác định được vị trí điểm cần dựng." },
  AMBIGUOUS_REFERENCE: { title: "CHƯA XÁC ĐỊNH DUY NHẤT", reason: "Một đối tượng trong đề có nhiều cách hiểu. Em hãy chỉ rõ điểm, cạnh, mặt hoặc khối được nhắc tới." },
  AMBIGUOUS_FACT: { title: "CHƯA XÁC ĐỊNH DUY NHẤT", reason: "Giả thiết có nhiều cách hiểu nên hệ chưa chọn được một phép dựng duy nhất." },
  CURVED_PRIMITIVE_BLOCKED_BY_KERNEL: { title: "NGOÀI PHẠM VI DỰNG HÌNH", reason: "Hệ chưa hỗ trợ phép dựng chính xác cho loại khối được yêu cầu." },
};

export function UnsupportedNotice({
  unsupported,
}: {
  unsupported: {
    reason: string;
    learner_reason?: string;
    failure_category?: string;
    /** (M17 W2B-PATCH) Mã chi tiết — dùng khi một `failure_category` gộp nhiều
     *  ca cần lời khuyên KHÁC NHAU. Hiển thị qua `NHAN_LOAI_VAN_DE`, không bao
     *  giờ hiển thị thô. */
    error_code?: string;
    /** (PRODUCT_RESPONSE_CONTRACT_ALIGNMENT) Giai đoạn pipeline đã dừng lại.
     *  Backend sở hữu giá trị; FE chỉ tra nhãn. */
    stage_reached?: string;
    /** (W17 §15.3) Nguyên nhân từ chối — backend quyết từ mã có cấu trúc. Chỉ `SOURCE` mới mời
     *  học sinh sửa đề; thiếu trường (envelope cũ) đi như `UNKNOWN`. */
    refusal_cause?: "SOURCE" | "CONSTRUCTION" | "UNKNOWN";
    /** (W20 §17) Mã lý do chi tiết — chỉ để chọn nhãn loại vấn đề, không bao giờ hiển thị. */
    reason_code?: string;
    /** Câu hỏi làm rõ đã qua bộ đọc kiểm chứng (không mang định danh kỹ thuật nội bộ). */
    clarification?: { question: string | null };
  };
}) {
  const geometricCode = unsupported.reason_code ?? unsupported.error_code;
  const geometricRefusal = unsupported.failure_category === "verification_gap"
    || (unsupported.failure_category === "insufficient_specification" && unsupported.refusal_cause !== "SOURCE")
    ? undefined : geometricCode ? GEOMETRY_REFUSAL_TEXT[geometricCode] : undefined;
  const failedVerification = unsupported.error_code === "postcondition_violated";
  const cutExplanation = geometricCode === "CURVED_PLANE_DOES_NOT_CUT"
    ? (unsupported.learner_reason ?? unsupported.reason).split(geometricCode).join("")
      .replace(/^[\s:[\]()—-]+/u, "").trim()
    : null;
  // (M17-VR1) Đề THIẾU DỮ KIỆN khác hẳn đề NGOÀI DANH MỤC: chủ đề vẫn được hỗ
  // trợ, chỉ là em chưa cho đủ dữ liệu. Nói "ngoài danh mục" ở đây làm học sinh
  // tưởng hệ không mô phỏng được dạng bài đó — sai và làm nản.
  const insufficient = unsupported.failure_category === "insufficient_specification";
  // (M17 W2B-VR) Đề hỏi NHIỀU việc/nhiều truy vấn cùng lúc khác hẳn "thiếu dữ
  // kiện" và "ngoài danh mục": chủ đề được hỗ trợ, dữ liệu đủ, chỉ là mỗi lần
  // mô phỏng trình bày được một yêu cầu. Nói "ngoài danh mục" ở đây làm học
  // sinh tưởng hệ không làm được — sai.
  const incomplete = unsupported.failure_category === "semantic_incomplete";
  // (M17 W2B-PATCH) Trong CÙNG `semantic_incomplete` có HAI ca ngược nhau về
  // lời khuyên, nên tiêu đề/gợi ý phải đọc `error_code` (chi tiết hơn) trước:
  // - hỏi nhiều truy vấn độc lập → tách đề ra là ĐÚNG;
  // - đề MỘT truy vấn nhiều bước mà hệ dựng thiếu bước → tách ra VÔ ÍCH, phải
  //   nói rõ là chưa dựng đủ bước. Lỗi này do review ẢNH bắt được.
  const stageShortfall = unsupported.error_code === "pipeline_stage_incomplete";
  // (M20 W3) Cổng phạm vi sinh HAI hạng mục, và gộp chúng vào "ngoài danh mục"
  // là nói sai theo hai hướng ngược nhau:
  // - out_of_scope: đề thuộc MÔN KHÁC. "Danh mục sẽ được mở rộng dần" ở đây là
  //   một lời hứa sai — hệ sẽ không bao giờ thêm hoá học.
  // - not_simulation_suitable: chủ đề CÓ trong chương trình, chỉ là không có cơ
  //   chế để mô phỏng. Nói "ngoài danh mục" làm học sinh ngồi chờ một thứ không
  //   bao giờ tới, vì chẳng có gì để thêm vào.
  const outOfScope = unsupported.failure_category === "out_of_scope";
  const notSimulatable = unsupported.failure_category === "not_simulation_suitable";
  /* (W-UI) SINH CHƯƠNG TRÌNH HÌNH HỌC KHÔNG THÀNH — nhãn riêng, và đây là một
     bản vá lỗi nói sai chứ không phải một nhãn cho đẹp.
     Loại thất bại này trước đây rơi vào nhãn mặc định "NGOÀI DANH MỤC MÔ
     PHỎNG", trong khi chính thân thông điệp ngay dưới nó nói ngược lại: hệ ĐÃ
     nhận ra đây là bài hình học và ĐÃ thử dựng. Học sinh đọc được hai câu trái
     nhau trên cùng một thẻ, và câu sai lại là câu in đậm ở trên.
     Chỉ đổi NHÃN HIỂN THỊ. `failure_category`, `error_code` và hành vi
     fail-closed giữ nguyên — chúng là ngữ nghĩa, không phải cách gọi tên. */
  const geometryGenFailed =
    unsupported.failure_category === "geometry_generation_failed";
  const verificationGap =
    unsupported.failure_category === "verification_gap";
  /* (PRODUCT_UI_RESULT_RENDERING) NGOÀI BAO ĐÓNG ≠ VIẾT ĐỀ CHƯA GỌN.
     `geometry_generation_failed` gộp hai tình huống ngược nhau, và lời khuyên
     đúng cho cái này là lời hứa sai cho cái kia:
       ① bài THUỘC bao đóng, mô hình viết chương trình hỏng → diễn đạt lại giúp;
       ② bài NGOÀI bao đóng (khối tròn xoay tổng quát, khối ghép/bù) → không
          phép IR nào tạo ra được vật ấy, nên viết lại bao nhiêu lần cũng vậy.
     Đo được ở lượt nghiệm thu trình duyệt: `n1`/`n2` — hai bài `OUT_OF_SCOPE`
     theo ma trận năng lực — đọc được câu *"Dạng bài này hệ có mô phỏng"*.
     Cổng phủ ĐÃ phân biệt sẵn bằng `requested_operation_uncovered`; chỗ thiếu
     là bề mặt học sinh chưa đọc mã ấy. Cùng lớp lỗi đã sửa hai lần cho
     `out_of_scope` vs `not_simulation_suitable`, cùng cách sửa: đọc `error_code`
     (chi tiết hơn) TRƯỚC khi rơi về câu chung của `failure_category`.
     ⚠️ Chỉ đổi CÂU GỢI Ý. `failure_category`, `error_code`, `learner_reason` và
     hành vi fail-closed là ngữ nghĩa do backend sở hữu — không đụng. */
  const ngoaiBaoDong =
    unsupported.error_code === "requested_operation_uncovered";
  /* HFOI-F6: "CHƯA ĐỦ DỮ KIỆN" / "đề chưa đủ dữ kiện" quy cho ĐỀ — chỉ đúng khi backend đã phân xử nguyên nhân là đề
     (`refusal_cause === "SOURCE"`). UNKNOWN (vd mô hình tự đánh dấu mơ hồ) hay vắng ⇒ phía HỆ chưa xác định được. */
  const deThieu = insufficient && unsupported.refusal_cause === "SOURCE";
  const eyebrow = insufficient ? (deThieu ? "CHƯA ĐỦ DỮ KIỆN" : "CHƯA XÁC ĐỊNH ĐỦ DỮ KIỆN")
    : verificationGap ? "CHƯA ĐỦ BẰNG CHỨNG KIỂM CHỨNG"
    : stageShortfall ? "CHƯA DỰNG ĐỦ CÁC BƯỚC"
    : incomplete ? "TÁCH THÀNH TỪNG YÊU CẦU"
    /* (PRODUCT_RESPONSE_CONTRACT_ALIGNMENT) NGOÀI BAO ĐÓNG có nhãn RIÊNG, và
       lý do là một chữ: "CHƯA". "Chưa dựng được" nói với học sinh rằng lần
       sau có thể được — đúng với `n1` (mô hình viết hỏng, thử lại có cửa),
       SAI với `n2` (không phép IR nào tạo ra vật ấy, thử bao nhiêu lần cũng
       thế). Một lời hứa ngầm vẫn là lời hứa. */
    : ngoaiBaoDong ? "NGOÀI PHẠM VI DỰNG HÌNH"
    : geometryGenFailed ? "CHƯA DỰNG ĐƯỢC MÔ PHỎNG"
    : outOfScope ? "THUỘC MÔN HỌC KHÁC"
    : notSimulatable ? "BÀI NÀY KHÔNG CẦN MÔ PHỎNG"
    : "NGOÀI DANH MỤC MÔ PHỎNG";
  const hint = insufficient
    ? unsupported.refusal_cause === "SOURCE"
      ? "Bổ sung dữ liệu còn thiếu vào đề rồi gửi lại — dạng bài này hệ có mô phỏng."
      : "Nếu đề thuộc dạng hệ dựng được và đã có đủ giả thiết, em có thể gửi lại để hệ phân tích lại."
    : verificationGap
    ? "Hệ chỉ hiển thị mô phỏng khi đối chiếu và kiểm chứng được đầy đủ từ dữ kiện đến kết quả."
    : stageShortfall
    ? "Nêu rõ từng bước cần làm rồi gửi lại — dạng bài nhiều bước này hệ có mô phỏng."
    : incomplete
    ? "Mỗi lần hỏi một yêu cầu (giữ nguyên dữ liệu) để xem đầy đủ từng bước của yêu cầu đó."
    : ngoaiBaoDong
    /* ⚠️ CÂU NÀY PHẢI NÓI THỨ KHÁC với `learner_reason`, không nhắc lại nó.
       Bản trước liệt kê đúng danh sách năng lực mà backend vừa liệt kê ngay
       phía trên — ảnh chụp `n2` cho thấy học sinh đọc gần như y nguyên một
       câu hai lần. Đó là di sản của thời backend CHƯA có thông điệp cho
       `requested_operation_uncovered`: khi ấy frontend phải tự nói. Nay
       backend nói rồi, nên chỗ này chuyển sang thứ nó còn thiếu — VIỆC NÊN
       LÀM TIẾP. */
    ? "Nếu đề gồm nhiều khối ghép lại, thử hỏi riêng từng khối — mỗi khối một lần."
    : geometryGenFailed
    /* ⚠️ CÂU CÓ ĐIỀU KIỆN, KHÔNG PHẢI LỜI HỨA — và đây là một bản sửa.
       Câu cũ khẳng định thẳng *"Dạng bài này hệ có mô phỏng"*. Nhưng nhánh này
       nhận CẢ những ca bị chặn TRƯỚC cổng phủ (`error_code = null`, xem `n1`
       của lượt đánh giá cuối), tức những ca hệ **không biết** dạng bài có nằm
       trong bao đóng hay không. Khẳng định một điều mình không biết, về phía
       có lợi cho mình, là đúng thứ ranh giới R0 dựng ra để cấm — chỉ khác là
       lần này lời sai nằm trên bề mặt học sinh chứ không trong một đáp số.
       Nói có điều kiện thì vẫn hữu ích mà không hứa liều.
       (W17 §15.3) Câu đọc `refusal_cause`. Lời backend của SOURCE/CONSTRUCTION đã nói nguyên nhân
       VÀ việc nên làm (sửa đúng số liệu ấy / đề không cần sửa, gửi lại) — câu gợi ý nhắc lại y ý ấy
       ngay bên dưới (lượt trình duyệt T7), nên không có gợi ý: cùng luật "nói THỨ KHÁC
       `learner_reason`" như nhánh ngoài bao đóng. UNKNOWN (và envelope cũ) giữ câu có điều kiện,
       không mời viết lại đề. */
    ? unsupported.refusal_cause === "SOURCE" || unsupported.refusal_cause === "CONSTRUCTION"
      ? null
      : "Nếu đề thuộc dạng hệ dựng được (thiết diện, giao tuyến, khoảng cách, góc, thể tích), em có thể gửi lại để hệ dựng lại."
    : outOfScope
    ? "AlgoSim mô phỏng hình học không gian — thử một bài về giao tuyến, thiết diện, quan hệ song song–vuông góc, khoảng cách hoặc thể tích."
    : notSimulatable
    ? "Nội dung này đọc hiểu là đủ. Muốn xem một quá trình chạy từng bước thì cần đề có dữ liệu và thao tác trên dữ liệu."
    /* Câu chốt phải nói ĐÚNG hướng đang mở, nếu không nó tự hứa một danh mục
       không còn thuộc sản phẩm.
       ⚠️ Bản trước ghi *"khối đa diện LỒI; mặt cong chưa mô phỏng được"* — câu
       ấy ĐÃ HẾT ĐÚNG và sai theo hướng tự khai năng lực THẤP hơn thực tế: cầu,
       trụ, nón có nền tất định từ 2026-09-03, khối đa diện LÕM có thể tích
       chính xác từ 2026-09-07, và lượt đo cuối phục vụ đủ cả bốn (`p2`…`p5`).
       Nói dối theo chiều khiêm tốn vẫn là nói dối, và nó đuổi học sinh khỏi
       đúng những bài hệ làm được. */
    : "Hiện hệ dựng được khối đa diện (chóp, lăng trụ, hộp — kể cả đáy lõm), hình cầu, hình trụ và hình nón.";
  /* (PRODUCT_RESPONSE_CONTRACT_ALIGNMENT) HAI SỰ THẬT CÓ CẤU TRỮC, hiện ra
     bằng tiếng Việt. Rẽ nhánh theo TRƯỜNG, không theo văn xuôi: `stage_reached`
     và `error_code` do backend sở hữu, ở đây chỉ tra bảng nhãn. Thiếu trường
     (envelope cũ) thì nói thẳng là không xác định được — tuyệt đối không dò
     chuỗi `reason` để đoán ra một nhãn nghe có vẻ đúng. */
  const nhanGiaiDoan = unsupported.stage_reached
    ? NHAN_GIAI_DOAN[unsupported.stage_reached] ?? KHONG_XAC_DINH
    : KHONG_XAC_DINH;
  const khoaLoai = unsupported.error_code ?? unsupported.failure_category;
  /* (W17 §15.3) Cổng nguồn từ chối cả hai phía: dữ kiện đề không có (SOURCE) và phép dựng/số liệu
     của HỆ lệch câu chữ của đề (CONSTRUCTION). Nhãn chung "dữ kiện không truy được về đề bài" nói
     sai phía thứ hai — đọc nguyên nhân có cấu trúc, không dò chữ. */
  /* (W18 §16.4) Ở chặng đối chiếu phép dựng điểm, nguyên nhân khác CONSTRUCTION nghĩa là hệ CHƯA đối
     chiếu được — giới hạn của hệ, không phải dữ kiện của đề thiếu nguồn. */
  /* (W20 §17) Điểm đề định nghĩa bằng quan hệ mà chương trình đặt bằng toạ độ: cùng nguyên nhân CONSTRUCTION
     nhưng toạ độ có thể đúng — hệ CHƯA KIỂM CHỨNG được, chưa chứng minh là lệch. Nhãn "dựng lệch" chỉ dành cho
     ca lệch đã chứng minh, nên mã chi tiết (có cấu trúc, không hiển thị) được đọc TRƯỚC nguyên nhân. */
  const nhanLoai = unsupported.reason_code === "CONSTRUCTION_REPLACED_BY_COORDINATES"
    ? "chưa kiểm chứng được phép dựng"
    : insufficient && !deThieu && khoaLoai === "insufficient_specification"
    ? "hệ chưa xác định được đủ dữ kiện từ đề"
    : unsupported.refusal_cause === "CONSTRUCTION" && khoaLoai === "input_not_grounded"
    ? "hệ dựng lệch với đề bài"
    : unsupported.stage_reached === "construction_binding" && khoaLoai === "input_not_grounded"
    ? "hệ chưa đối chiếu được phép dựng với đề"
    : khoaLoai
    ? NHAN_LOAI_VAN_DE[khoaLoai] ?? KHONG_XAC_DINH
    : KHONG_XAC_DINH;
  /* Thứ tự fallback GIỮ NGUYÊN hợp đồng M17 W0: `learner_reason` trước,
     `reason` sau (envelope cũ, khoá bởi `learner-error.test.tsx`). Chỉ thêm
     nấc CUỐI cho envelope không có cả hai — trước bản này nấc ấy render một
     chuỗi rỗng. */
  const loiKe =
    unsupported.learner_reason ?? unsupported.reason ?? MO_TA_TU_CHOI_CHUNG;
  const cauHoiLamRo = unsupported.clarification?.question ?? null;
  return (
    <section className="card">
      <span className="eyebrow">{geometricRefusal?.title ?? (failedVerification ? "CHƯA KIỂM CHỨNG ĐƯỢC MÔ PHỎNG" : eyebrow)}</span>
      <p style={{ marginTop: "var(--sp-sm)" }}>{geometricRefusal
        ? cutExplanation !== null ? `Không thể dựng giao tuyến. ${cutExplanation || geometricRefusal.reason}` : unsupported.learner_reason ?? geometricRefusal.reason
        : loiKe}</p>
      <dl className="refusal-facts">
        <div>
          <dt>Dừng ở bước</dt>
          <dd>{nhanGiaiDoan}</dd>
        </div>
        <div>
          <dt>Loại vấn đề</dt>
          <dd>{geometricRefusal?.title ?? nhanLoai}</dd>
        </div>
      </dl>
      {cauHoiLamRo ? (
        <p className="notes" data-clarification-question="">{cauHoiLamRo}</p>
      ) : (
        !geometricRefusal && hint && <p className="notes">{hint}</p>
      )}
    </section>
  );
}

/** Câu thay cho `reason` kỹ thuật khi envelope cũ không có `learner_reason`. */
const MO_TA_TU_CHOI_CHUNG =
  "AlgoSim chưa tạo được mô phỏng cho đề này và không hiển thị hình chưa " +
  "được kiểm chứng.";

/**
 * (SHELL-N) KHE THUYẾT MINH — component THUẦN theo props (export để test SSR).
 *
 * Đây là chỗ DUY NHẤT trong sản phẩm dựng thuyết minh bước hiện tại. Module chỉ
 * trả chuỗi qua `narrate()`; vị trí, nền, khoảng cách, biến thể "thao tác của
 * em" đều do shell quyết. `null` → không dựng gì (không để lại ô rỗng).
 *
 * `role="status"` + `aria-live="polite"`: đổi bước bằng nút hay bằng phím tắt
 * đều được đọc lên. Trước bản này không có vùng aria-live nào trong workspace —
 * người dùng đọc màn hình bấm "Tiến" không nghe thấy gì.
 */
export function NarrationSlot({ narration }: { narration: Narration | null }) {
  if (!narration) return null;
  return (
    <div
      className={`narration-bar${narration.fromLearner ? " is-user" : ""}`}
      role="status"
      aria-live="polite"
    >
      {narration.text}
    </div>
  );
}

/**
 * Có dựng LỐI VÀO Khám phá không — cũng dẫn xuất từ năng lực.
 *
 * Module không khai `explore` ⇒ không có lối vào (mặc định an toàn). Khai mà
 * `entry()` trả `null` ở trạng thái này ⇒ cũng không dựng: một lối vào rỗng
 * ("khám phá đi" ở bước cuối, khi không còn gì để đổi) tệ hơn là không có.
 */
export function exploreEntry<S>(
  mod: { explore?: ExploreCapability<S> },
  state: S,
  config: unknown,
): PresentationEntry | null {
  return mod.explore?.entry(state, config) ?? null;
}

/**
 * W4B-4D — MÔ HÌNH ĐÃ RỜI KHỎI ĐỀ CHƯA.
 */
export function specDrift<S>(
  mod: { currentConfig?: (state: S) => unknown },
  state: S,
  baseline: unknown,
): boolean {
  if (!mod.currentConfig) return false;
  try {
    const now = mod.currentConfig(state);
    if (typeof now !== "object" || now === null || typeof baseline !== "object" || baseline === null) {
      return JSON.stringify(now) !== JSON.stringify(baseline);
    }
    const base = baseline as Record<string, unknown>;
    return Object.entries(now as Record<string, unknown>)
      .some(([k, v]) => JSON.stringify(v) !== JSON.stringify(base[k]));
  } catch {
    return false;
  }
}

/**
 * Vùng trung tâm — host sân khấu mô phỏng (M2 #1). KHÔNG giả định simulation
 * là thuật toán (M2 #2): mọi thứ domain-specific render qua module.Workspace
 * lấy từ registry.
 */
export function SimulationWorkspace() {
  const active = useAppStore((s) => s.active);
  const activeSampleId = useAppStore((s) => s.activeSampleId);
  const unsupported = useAppStore((s) => s.unsupported);
  const playing = useAppStore((s) => s.playing);
  const dispatch = useAppStore((s) => s.dispatch);
  const visualMode = useAppStore((s) => s.visualMode);
  const rightOpen = useAppStore((s) => s.rightOpen);
  const setSemanticFocus = useAppStore((s) => s.setSemanticFocus);
  const session = useClassroomStore((s) => s.session);
  const setVisualMode = useAppStore((s) => s.setVisualMode);
  const returnView = useAppStore((s) => s.returnView);
  const roiXuong = useAppStore((s) => s.roiXuong);
  const assignment = useAppStore((s) => s.activeAssignment);
  const activeHistoryId = useAppStore((s) => s.activeHistoryId);
  const hasInAppNavigation = useAppStore((s) => s.hasInAppNavigation);
  const laGiaoVien = useAuthStore((s) => s.user?.role === "teacher");

  if (unsupported) {
    return (
      <AxoErrorExperience
        kind="unsupported_simulation"
        variant="refusal"
        hasBackHistory={hasInAppNavigation}
        onBack={() => useAppStore.getState().escapeFromError()}
        onGoHome={() => useAppStore.getState().goHome()}
        onOpenLibrary={() => useAppStore.getState().openLibrary()}
      >
        <UnsupportedNotice unsupported={unsupported} />
      </AxoErrorExperience>
    );
  }

  if (!active) {
    return (
      <div className="empty-state" style={{ margin: "auto 0" }}>
        <p style={{ fontSize: 40, marginBottom: "var(--sp-sm)" }}>⧉</p>
        <p>
          Nhập một bài toán rồi bấm <strong>Phân tích đề bằng AI</strong>,
          <br />
          hoặc chọn một bài trong <strong>danh mục mô phỏng</strong> bên trái.
        </p>
      </div>
    );
  }

  const historyItem = activeHistoryId
    ? historyStore.list().find((h) => h.id === activeHistoryId)
    : undefined;
  let canh3d: unknown = null;
  try {
    const env3d = recoverCatalogScene3D(active.envelope);
    canh3d = (env3d as { scene3d?: unknown })?.scene3d ?? null;
  } catch {
    canh3d = null;
  }
  // NGUỒN ĐỀ BÀI (presentation context), theo thứ tự thẩm quyền:
  //  1. `learner` — đề gốc đi kèm CHÍNH lần mở này (`active.problemStatement`: đề vừa gửi, hoặc đề đã lưu của
  //     bản ghi lịch sử);
  //  2. `catalog` — lần mở chỉ rõ mã bài mẫu: đề lấy từ DANH MỤC,
  //     không từ envelope đã lưu;
  //  3. `missing` — không có đề gốc. Nói thẳng là thiếu; `description` của backend (lời lưu ý Hybrid `/4`, mô tả
  //     do mô hình viết) chỉ hiện kèm nhãn, không bao giờ đứng thay đề. Ô soạn `problemText` không bao giờ dùng.
  const catalogSampleId = active.problemStatement ? null : activeSampleId;
  const catalogStatement = catalogSampleId
    ? GEOMETRY_SAMPLES.find((s) => s.id === catalogSampleId)?.problemText ?? null
    : null;
  const modelDescription = active.envelope.description?.trim() || null;
  const statement: { text: string; source: "learner" | "catalog" | "missing" } = active.problemStatement
    ? { text: active.problemStatement, source: "learner" }
    : catalogStatement
      ? { text: catalogStatement, source: "catalog" }
      : {
          text: modelDescription
            ? `Bản ghi này không lưu đề gốc. Mô tả mô hình do hệ thống tạo: ${modelDescription}`
            : "Bản ghi này không lưu đề gốc.",
          source: "missing",
        };
  const resolvedProblemStatement = statement.text;

  if (hopLeScene3D(canh3d)) {
    const normalizedWorkspaceTitle = normalizeCylinderEnvelopeTitle(
      active.envelope.title ?? historyItem?.title,
      canh3d,
    );
    return (
      <AxoWorkspaceV62
        scene={canh3d}
        de={resolvedProblemStatement}
        deSource={statement.source}
        tieuDe={active.envelope.title ? normalizeCylinderEnvelopeTitle(active.envelope.title, canh3d) : (normalizedWorkspaceTitle || null)}
        quayLai={{ nhan: TEN_TRANG[returnView] ?? "Trang chủ", onClick: roiXuong }}
        phien={session}
        onFocus={(selectedId, action) => setSemanticFocus({ selectedId, action })}
        daiLop={(assignment || laGiaoVien) ? (
          <>
            {assignment && (
              <span className="nav-assignment" title={assignment.instruction}>
                Bài: <strong>{assignment.title}</strong>
              </span>
            )}
            <AssignDialog />
            <LiveClassStrip />
          </>
        ) : undefined}
        daiLopTomTat={<LiveClassStrip tomTat />}
        hybrid={hybridViewCua(active.envelope)}
        routeDSimulation={
          (active.envelope as { route_d_simulation?: RouteDSimulationSummary | null })
            .route_d_simulation
        }
      />
    );
  }

  /* ── P5.2 / P5.3: CHẶN FALLBACK SAI SANG TRÌNH MÔ PHỎNG NGỮ NGHĨA CŨ ────────
     Nếu một bản ghi hình học không có `scene3d` hợp lệ và không khớp bài mẫu
     nào trong `GEOMETRY_SAMPLES`, tuyệt đối không rơi xuống `SemanticProgramModule`
     (`MÔ PHỎNG THEO MÔ TẢ / Mô phỏng theo chương trình ngữ nghĩa`). Thay vào đó,
     hiển thị thông báo trung thực trong khung Workspace V6.2 để học sinh dựng
     lại bài toán hoặc mở Thư viện 3D. */
  if (active.envelope.domain === "geometry") {
    const titleText = active.envelope.title?.trim() || "Mô phỏng hình học không gian";
    return (
      <AxoWorkspaceV62
        scene={EMPTY_SAFE_SCENE}
        de={resolvedProblemStatement}
        deSource={statement.source}
        tieuDe={titleText}
        quayLai={{ nhan: TEN_TRANG[returnView] ?? "Trang chủ", onClick: roiXuong }}
        unavailableOverride={{
          title: "Bản ghi này chưa có dữ liệu không gian 3D hợp lệ",
          detail: `Bản ghi "${titleText}" không chứa dữ liệu mô hình 3D tương thích nên chưa thể mở trong không gian học. Em có thể quay lại trang vừa xem hoặc dựng lại đề bài trên Trang chủ.`,
          onGoHome: () => {
            const s = useAppStore.getState();
            if (resolvedProblemStatement) {
              s.setProblemText(resolvedProblemStatement);
            }
            s.goHome();
          },
        }}
      />
    );
  }

  const mod = getSimulation(active.moduleId);
  if (!mod) {
    return (
      <AxoErrorExperience
        kind="unsupported_simulation"
        variant="page"
        hasBackHistory={hasInAppNavigation}
        onBack={() => useAppStore.getState().escapeFromError()}
        onGoHome={() => useAppStore.getState().goHome()}
        onOpenLibrary={() => useAppStore.getState().openLibrary()}
      />
    );
  }

  const modes = learnerFacingModes(mod);
  const mode = effectiveVisualMode(mod, visualMode);
  const driftedFromSpec = specDrift(mod, active.state, active.config);
  const Stage = rendererFor(mod, mode) as ComponentType<WorkspaceProps>;
  const subtitle = headerSubtitle(mod.title, active.envelope.title);
  const stageMin: number | null = null;
  const cardStyle = stageMin
    ? ({ "--stage-min": `calc(${stageMin}px + 2 * var(--sp-lg) + 24px)` } as CSSProperties)
    : undefined;

  return (
    <section className="card card-elevated workspace-card" style={cardStyle}>
      <div className="workspace-header">
        <span className="eyebrow">{DOMAIN_BADGE[mod.domain]}</span>
        <h2 className="workspace-title">{active.envelope.title}</h2>
        {subtitle && <span className="hint">{subtitle}</span>}
        {driftedFromSpec && (
          <span className="spec-drift" title="Bấm Đặt lại để quay về đúng đề bài.">
            Đã đổi so với đề bài
          </span>
        )}
        <VisualModeToggle modes={modes} mode={mode} onSelect={setVisualMode} />
      </div>
      <div className={`workspace-body${rightOpen ? " has-explain" : ""}`}>
        <Suspense fallback={<div className="empty-state">Đang tải chế độ hiển thị…</div>}>
          <Stage config={active.config} state={active.state} busy={playing} dispatch={dispatch} />
        </Suspense>
        {rightOpen && (
          <div className="workspace-explain">
            <SimulationInspector />
          </div>
        )}
      </div>
      <NarrationSlot narration={mod.narrate?.(active.state, active.config) ?? null} />
    </section>
  );
}
