import type { ReactNode } from "react";
import type { AnalysisUnsupported } from "../core/types";
import { canonicalSlugForSampleId, resolveSampleByRouteToken } from "../data/offline-catalog";
import type { ClientFailureContract } from "../llm/client";
import { historyStore } from "../state/history";
import type { AppView } from "../state/store";

export type AxoErrorKind =
  | "not_found"
  | "render_failure"
  | "unsupported_simulation"
  | "network_failure";

export type LocationRouteDecision =
  | { readonly kind: "view"; readonly view: Exclude<AppView, "not_found"> }
  | { readonly kind: "workspace_root" }
  | { readonly kind: "sample"; readonly sampleId: string }
  | { readonly kind: "history_item"; readonly historyId: string }
  | { readonly kind: "not_found"; readonly requestedPath: string };

const STATIC_PATH_TO_VIEW: Readonly<Record<string, Exclude<AppView, "not_found">>> = {
  "/": "home",
  "/index.html": "home",
  "/library": "library",
  "/history": "history",
  "/login": "login",
  "/register": "register",
  "/forgot": "forgot",
  "/reset": "reset",
  "/admin": "admin",
  "/classes": "classes",
  "/assignments": "assignments",
  "/observe": "observe",
  "/monitor": "monitor",
  "/account": "account",
};

export function canonicalPathForView(
  view: AppView,
  activeSampleId?: string | null,
): string {
  switch (view) {
    case "home":
      return "/";
    case "library":
      return "/library";
    case "history":
      return "/history";
    case "workspace":
      return activeSampleId ? `/simulation/${encodeURIComponent(canonicalSlugForSampleId(activeSampleId))}` : "/workspace";
    case "login":
      return "/login";
    case "register":
      return "/register";
    case "forgot":
      return "/forgot";
    case "reset":
      return "/reset";
    case "admin":
      return "/admin";
    case "classes":
      return "/classes";
    case "assignments":
      return "/assignments";
    case "observe":
      return "/observe";
    case "monitor":
      return "/monitor";
    case "account":
      return "/account";
    case "not_found":
      return "/404";
  }
}

/**
 * Phân giải đường dẫn trình duyệt thành mặt trình bày có kiểm chứng.
 * Đường dẫn lạ hoặc tài nguyên mô phỏng không có trong danh mục/lịch sử ⇒ `not_found`.
 */
export function resolveLocationRoute(
  pathname: string,
  hash = "",
  search = "",
): LocationRouteDecision {
  if (hash === "#admin" || pathname === "/admin") {
    return { kind: "view", view: "admin" };
  }
  const hasResetToken = search ? new URLSearchParams(search).has("reset_token") : false;
  if (hash === "#reset" || hasResetToken || pathname === "/reset") {
    return { kind: "view", view: "reset" };
  }

  const normalized =
    pathname.length > 1 && pathname.endsWith("/")
      ? pathname.replace(/\/+$/, "")
      : pathname || "/";

  const staticMatch = STATIC_PATH_TO_VIEW[normalized];
  if (staticMatch) {
    return { kind: "view", view: staticMatch };
  }

  if (normalized === "/workspace") {
    return { kind: "workspace_root" };
  }

  if (normalized.startsWith("/simulation/")) {
    const rawSlug = normalized.slice("/simulation/".length);
    if (!rawSlug || rawSlug.includes("/")) {
      return { kind: "not_found", requestedPath: normalized };
    }
    let decodedSlug = rawSlug;
    try {
      decodedSlug = decodeURIComponent(rawSlug);
    } catch {
      return { kind: "not_found", requestedPath: normalized };
    }
    const sample = resolveSampleByRouteToken(decodedSlug);
    if (sample) {
      return { kind: "sample", sampleId: sample.id };
    }
    const hist = historyStore.list().find((item) => item.id === decodedSlug);
    if (hist) {
      return { kind: "history_item", historyId: hist.id };
    }
    return { kind: "not_found", requestedPath: normalized };
  }

  return { kind: "not_found", requestedPath: normalized };
}

export interface AxoErrorClassificationInput {
  readonly routeNotFound?: boolean;
  readonly renderException?: boolean;
  readonly webglFailed?: boolean;
  readonly clientFailure?: ClientFailureContract | null;
  readonly unsupported?: AnalysisUnsupported | null;
  readonly invalidSceneContract?: boolean;
  readonly mathContradiction?: boolean;
}

/**
 * Phân loại lỗi dựa hoàn toàn trên trạng thái thực tế và hợp đồng lỗi có kiểu.
 * Tuyệt đối không đoán loại lỗi từ chuỗi văn bản `message` hay `reason`.
 */
export function classifyAxoErrorState(
  input: AxoErrorClassificationInput,
): AxoErrorKind | null {
  if (input.routeNotFound) return "not_found";
  if (input.renderException || input.webglFailed) return "render_failure";
  if (input.clientFailure) {
    if (input.clientFailure.code === "NOT_FOUND") return "not_found";
    if (
      input.clientFailure.kind === "network" ||
      input.clientFailure.code === "NETWORK_UNREACHABLE" ||
      input.clientFailure.code === "SERVICE_UNAVAILABLE" ||
      input.clientFailure.code === "HTTP_ERROR"
    ) {
      return "network_failure";
    }
  }
  if (input.unsupported || input.invalidSceneContract || input.mathContradiction) {
    return "unsupported_simulation";
  }
  return null;
}

interface ErrorCopyPreset {
  readonly kicker?: string;
  readonly title: string;
  readonly description: string;
}

const ERROR_COPY_BY_KIND: Readonly<Record<AxoErrorKind, ErrorCopyPreset>> = {
  not_found: {
    kicker: "404",
    title: "Trang hoặc mô hình này không tồn tại trên Axo",
    description:
      "Đường dẫn em vừa mở không khớp với không gian học hay bài mô phỏng nào hiện có.",
  },
  render_failure: {
    title: "Khung dựng hình 3D tạm thời không thể hiển thị",
    description:
      "Quá trình vẽ mô hình không gian gặp sự cố hiển thị trên thiết bị hoặc trình duyệt hiện tại. Thanh điều hướng và dữ liệu phiên học của em vẫn được giữ nguyên.",
  },
  unsupported_simulation: {
    title: "Chưa thể dựng mô hình 3D đã kiểm chứng cho nội dung này",
    description:
      "Dữ kiện hình học hiện tại không thỏa điều kiện dựng tất định hoặc chưa thuộc phạm vi hỗ trợ, nên Axo từ chối hiển thị hình xấp xỉ để tránh gây hiểu lầm.",
  },
  network_failure: {
    title: "Không kết nối được máy chủ hoặc không tải được dữ liệu",
    description:
      "Yêu cầu tải dữ liệu mô phỏng chưa hoàn tất do kết nối mạng hoặc dịch vụ máy chủ tạm thời không phản hồi.",
  },
};

function Illustration404Polyhedron() {
  return (
    <svg
      className="axo-error-svg"
      data-illustration="axo-404-polyhedron"
      viewBox="0 0 280 164"
      fill="none"
      role="img"
      aria-label="Minh họa khối đa diện 3D Axo khuyết đỉnh cho trạng thái 404 không tìm thấy đường dẫn"
    >
      {/* Nét khuất chuẩn SGK của mặt đáy và trục chiếu */}
      <path
        d="M66 120 L138 94 L210 120 M138 94 L138 42"
        stroke="#a39e98"
        strokeWidth="1.5"
        strokeDasharray="5 4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Khung đa diện nhìn thấy trên nền giấy ấm Axo */}
      <path
        d="M66 120 L132 144 L210 120 M66 120 L110 62 L138 42 L132 144"
        stroke="#31302e"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Mặt đỉnh tách rời biểu trưng cho đường dẫn không tồn tại (tắt chuyển động khi prefers-reduced-motion) */}
      <g className="axo-error-svg-float">
        <path
          d="M150 40 C174 32 194 34 212 44 M208 32 L232 24 L240 46 L216 54 Z"
          fill="#0075de"
          fillOpacity="0.08"
          stroke="#0075de"
          strokeWidth="1.7"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>
    </svg>
  );
}

function IllustrationRenderInterrupted() {
  return (
    <svg
      className="axo-error-svg"
      data-illustration="axo-render-interrupted"
      viewBox="0 0 280 160"
      fill="none"
      role="img"
      aria-label="Minh họa khung dựng hình 3D tạm dừng hiển thị"
    >
      <path
        d="M56 28 H224 V136 H56 Z M96 116 L140 98 L184 116"
        stroke="#a39e98"
        strokeWidth="1.4"
        strokeDasharray="5 4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M96 116 L140 50 L184 116 M96 116 L140 130 L184 116"
        stroke="#31302e"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <g className="axo-error-svg-float">
        <path
          d="M78 86 H202"
          stroke="#0075de"
          strokeWidth="1.8"
          strokeDasharray="8 5"
          strokeLinecap="round"
        />
      </g>
    </svg>
  );
}

function IllustrationConstraintUnclosed() {
  return (
    <svg
      className="axo-error-svg"
      data-illustration="axo-constraint-unclosed"
      viewBox="0 0 280 160"
      fill="none"
      role="img"
      aria-label="Minh họa ràng buộc hình học chưa khép kín hoặc chưa hỗ trợ"
    >
      <path
        d="M54 124 L140 98 L226 124 L140 148 Z"
        stroke="#a39e98"
        strokeWidth="1.4"
        strokeDasharray="5 4"
        strokeLinejoin="round"
      />
      <path
        d="M88 122 L132 56 M192 122 L156 66"
        stroke="#31302e"
        strokeWidth="1.85"
        strokeLinecap="round"
      />
      <g className="axo-error-svg-float">
        <path
          d="M132 56 L156 66"
          stroke="#d97706"
          strokeWidth="1.85"
          strokeDasharray="4 4"
          strokeLinecap="round"
        />
      </g>
    </svg>
  );
}

function IllustrationNetworkLink() {
  return (
    <svg
      className="axo-error-svg"
      data-illustration="axo-network-link"
      viewBox="0 0 280 160"
      fill="none"
      role="img"
      aria-label="Minh họa gián đoạn kết nối dữ liệu mạng"
    >
      <path
        d="M56 124 L140 100 L224 124 L140 146 Z"
        stroke="#a39e98"
        strokeWidth="1.35"
        strokeDasharray="5 4"
        strokeLinejoin="round"
      />
      <path
        d="M66 84 L92 70 L118 84 L92 98 Z M162 84 L188 70 L214 84 L188 98 Z"
        stroke="#31302e"
        strokeWidth="1.75"
        strokeLinejoin="round"
      />
      <g className="axo-error-svg-float">
        <path
          d="M118 84 H134 M146 84 H162"
          stroke="#0075de"
          strokeWidth="1.9"
          strokeLinecap="round"
        />
      </g>
    </svg>
  );
}

function renderIllustrationByKind(kind: AxoErrorKind) {
  switch (kind) {
    case "not_found":
      return <Illustration404Polyhedron />;
    case "render_failure":
      return <IllustrationRenderInterrupted />;
    case "unsupported_simulation":
      return <IllustrationConstraintUnclosed />;
    case "network_failure":
      return <IllustrationNetworkLink />;
  }
}

export interface AxoErrorExperienceProps {
  readonly kind: AxoErrorKind;
  readonly variant?: "page" | "stage" | "refusal";
  readonly title?: string;
  readonly detail?: string;
  readonly requestedPath?: string | null;
  readonly dataMathContradiction?: boolean;
  /** Có lịch sử điều hướng hợp lệ trong phiên để hiển thị "Quay lại" làm hành động chính hay không (§9.2). */
  readonly hasBackHistory?: boolean;
  readonly children?: ReactNode;
  readonly backLabel?: string;
  readonly homeLabel?: string;
  readonly libraryLabel?: string;
  readonly onBack?: () => void;
  readonly onGoHome?: () => void;
  readonly onOpenLibrary?: () => void;
  /** Hành động khôi phục phụ có giới hạn số lần thử — không bao giờ đặt làm nút chính mặc định (§9.3). */
  readonly onSecondaryRetry?: () => void;
  readonly secondaryRetryLabel?: string;
}

export function AxoErrorExperience({
  kind,
  variant = "page",
  title,
  detail,
  requestedPath,
  dataMathContradiction = false,
  hasBackHistory = true,
  children,
  backLabel = "Quay lại",
  homeLabel = "Về trang chủ",
  libraryLabel = "Mở Thư viện",
  onBack,
  onGoHome,
  onOpenLibrary,
  onSecondaryRetry,
  secondaryRetryLabel = "Thử dựng lại khung nhìn",
}: AxoErrorExperienceProps) {
  const preset = ERROR_COPY_BY_KIND[kind];
  const resolvedTitle = title ?? preset.title;
  const resolvedDetail = detail ?? preset.description;
  const showBackPrimary = hasBackHistory && Boolean(onBack);
  const primaryHomeHandler = onGoHome ?? onBack;

  return (
    <section
      className={`axo-error-experience is-${variant} is-kind-${kind}`}
      role="alert"
      data-error-kind={kind}
      data-math-contradiction={dataMathContradiction ? "" : undefined}
    >
      <div className="axo-error-surface">
        {variant !== "refusal" && (
          <div className="axo-error-visual">{renderIllustrationByKind(kind)}</div>
        )}

        <div className="axo-error-body">
          {kind === "not_found" && preset.kicker && (
            <p className="axo-error-kicker" aria-hidden="true">
              {preset.kicker}
            </p>
          )}
          {variant !== "refusal" && (
            <>
              <h1 className="axo-error-title">{resolvedTitle}</h1>
              <p className="axo-error-desc">{resolvedDetail}</p>
            </>
          )}

          {kind === "not_found" && requestedPath && (
            <p className="axo-error-path-note">
              Đường dẫn đã mở: <code className="axo-error-path-code">{requestedPath}</code>
            </p>
          )}

          {children && <div className="axo-error-slot">{children}</div>}

          <div className="axo-error-actions" aria-label="Điều hướng khôi phục">
            {showBackPrimary ? (
              <button
                type="button"
                className="btn-primary axo-error-btn-primary"
                data-error-action="back"
                onClick={onBack}
              >
                <svg
                  className="axo-error-btn-icon"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M19 12H5" />
                  <path d="m12 19-7-7 7-7" />
                </svg>
                <span>{backLabel}</span>
              </button>
            ) : (
              primaryHomeHandler && (
                <button
                  type="button"
                  className="btn-primary axo-error-btn-primary"
                  data-error-action="home"
                  onClick={primaryHomeHandler}
                >
                  <span>{homeLabel}</span>
                </button>
              )
            )}

            {onSecondaryRetry ? (
              <button
                type="button"
                className="axo-error-btn-secondary"
                data-error-action="secondary-retry"
                onClick={onSecondaryRetry}
              >
                <span>{secondaryRetryLabel}</span>
              </button>
            ) : onOpenLibrary ? (
              <button
                type="button"
                className="axo-error-btn-secondary"
                data-error-action="library"
                onClick={onOpenLibrary}
              >
                <span>{libraryLabel}</span>
              </button>
            ) : (
              showBackPrimary &&
              onGoHome && (
                <button
                  type="button"
                  className="axo-error-btn-secondary"
                  data-error-action="home"
                  onClick={onGoHome}
                >
                  <span>{homeLabel}</span>
                </button>
              )
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
