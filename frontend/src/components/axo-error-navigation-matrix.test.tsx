import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { renderToString } from "react-dom/server";
import App, { reconcileCrashedResetKey } from "../App";
import { publicCatalog } from "../data/offline-catalog";
import { AxoErrorExperience } from "./AxoErrorExperience";
import { ErrorBoundary } from "./ErrorBoundary";
import { registerAllSimulations } from "../simulations";
import { historyStore } from "../state/history";
import { useAppStore } from "../state/store";

describe("AXO Master §9: Error State Design Quality, Strict Classification & 10-Case Navigation Gate", () => {
  beforeEach(() => {
    registerAllSimulations();
    useAppStore.getState().reset();
  });

  it("1. 404 (`not_found`) uses borderless architectural layout without pill-badge stuffing and with custom authored <path> geometric SVG", () => {
    const htmlDeepLink = renderToString(
      <AxoErrorExperience
        kind="not_found"
        variant="page"
        requestedPath="/khong-ton-tai"
        hasBackHistory={false}
        onBack={() => {}}
        onGoHome={() => {}}
        onOpenLibrary={() => {}}
      />,
    );
    expect(htmlDeepLink).toContain('data-error-kind="not_found"');
    expect(htmlDeepLink).toContain('data-illustration="axo-404-polyhedron"');
    // Must use authored <path> vector art (no shape-assembled primitive soup, no pill badge eyebrow)
    expect(htmlDeepLink).toContain("<path");
    expect(htmlDeepLink).not.toContain("<circle");
    expect(htmlDeepLink).not.toContain("<polygon");
    expect(htmlDeepLink).not.toContain("<rect");
    expect(htmlDeepLink).not.toContain("axo-error-badge");
    // Fresh deep-link without visited history: single primary CTA "Về trang chủ", never 3 simultaneous CTAs
    expect(htmlDeepLink).toContain("Về trang chủ");
    expect(htmlDeepLink).not.toContain("Quay lại");
    const buttonMatches = htmlDeepLink.match(/<button\b/g) ?? [];
    expect(buttonMatches.length).toBeLessThanOrEqual(2);
  });

  it("2. Contextual primary CTA switches to `Quay lại` when valid in-app history exists (`hasBackHistory={true}`)", () => {
    const htmlWithHistory = renderToString(
      <AxoErrorExperience
        kind="not_found"
        variant="page"
        requestedPath="/simulation/id-khong-ton-tai"
        hasBackHistory={true}
        onBack={() => {}}
        onGoHome={() => {}}
        onOpenLibrary={() => {}}
      />,
    );
    expect(htmlWithHistory).toContain('data-error-action="back"');
    expect(htmlWithHistory).toContain("Quay lại");
    const buttonMatches = htmlWithHistory.match(/<button\b/g) ?? [];
    expect(buttonMatches.length).toBeLessThanOrEqual(2);
  });

  it("3. Runtime / WebGL / Unsupported states NEVER display `404` and only expose retry when a real recovery action is provided", () => {
    const htmlWebglNoRetry = renderToString(
      <AxoErrorExperience
        kind="render_failure"
        variant="stage"
        title="Khung dựng hình 3D tạm thời không thể hiển thị"
        detail="Không khởi tạo được chế độ 3D trên thiết bị này."
        hasBackHistory={true}
        onBack={() => {}}
        onGoHome={() => {}}
      />,
    );
    expect(htmlWebglNoRetry).toContain('data-error-kind="render_failure"');
    expect(htmlWebglNoRetry).not.toMatch(/\b404\b/u);
    expect(htmlWebglNoRetry).not.toContain('data-error-action="secondary-retry"');

    const htmlWebglWithRetry = renderToString(
      <AxoErrorExperience
        kind="render_failure"
        variant="stage"
        hasBackHistory={true}
        onBack={() => {}}
        onGoHome={() => {}}
        onSecondaryRetry={() => {}}
        secondaryRetryLabel="Khôi phục khung 3D"
      />,
    );
    expect(htmlWebglWithRetry).toContain('data-error-action="secondary-retry"');
    expect(htmlWebglWithRetry).toContain("Khôi phục khung 3D");
    expect(htmlWebglWithRetry).not.toMatch(/\b404\b/u);
  });

  it("4. ErrorBoundary caps retry attempts per resetKey to prevent infinite crash loops", () => {
    const fallbackSpy = vi.fn<
      (thuLai: () => void, meta: { readonly canRetry: boolean; readonly retryCount: number }) => ReactNode
    >(() => null);
    const boundary = new ErrorBoundary({
      mien: "main",
      resetKey: "sim-1",
      fallback: fallbackSpy,
      children: null,
    });
    boundary.state = { hong: true, soLanThuLai: 0 };
    boundary.setState = ((updater: unknown) => {
      const next = typeof updater === "function" ? updater(boundary.state) : updater;
      boundary.state = { ...boundary.state, ...(next as object) };
    }) as typeof boundary.setState;

    // Attempt 1: retry is available (`canRetry === true`)
    boundary.render();
    const firstThuLai = fallbackSpy.mock.calls[0]?.[0];
    const firstMeta = fallbackSpy.mock.calls[0]?.[1];
    expect(firstMeta?.canRetry).toBe(true);
    expect(firstMeta?.retryCount).toBe(0);

    // Trigger reset, then simulate immediate re-throw on same resetKey
    firstThuLai?.();
    boundary.state = {
      ...boundary.state,
      ...ErrorBoundary.getDerivedStateFromError(),
    };
    boundary.render();
    const secondMeta = fallbackSpy.mock.calls[1]?.[1];
    expect(secondMeta?.canRetry).toBe(false);
    expect(secondMeta?.retryCount).toBe(1);
  });

  it("5. §9.4 Ten post-error navigation state transitions recover cleanly without dead-ends or history loops", () => {
    // Case 1 & 10: Direct deep-link to non-existent URL without history -> not_found, hasInAppNavigation = false, escape -> Home `/`
    useAppStore.getState().syncLocationRoute("/duong-dan-sai");
    expect(useAppStore.getState().view).toBe("not_found");
    expect(useAppStore.getState().routeFailure?.requestedPath).toBe("/duong-dan-sai");
    expect(useAppStore.getState().hasInAppNavigation).toBe(false);
    expect(useAppStore.getState().escapeFromError()).toBe("home");
    expect(useAppStore.getState().view).toBe("home");
    expect(useAppStore.getState().routeFailure).toBeNull();

    // Case 2: Valid route (`/library`) -> internal navigation to non-existent `/simulation/missing` -> Back returns to `/library`!
    useAppStore.getState().openLibrary();
    expect(useAppStore.getState().hasInAppNavigation).toBe(true);
    useAppStore.getState().syncLocationRoute("/simulation/khong-co-bai-nay");
    expect(useAppStore.getState().view).toBe("not_found");
    expect(useAppStore.getState().escapeFromError()).toBe("library");
    expect(useAppStore.getState().view).toBe("library");

    // Case 3 & 4 & 5: Valid route (`/home` -> `/simulation/thiet-dien-chop`) -> runtime / WebGL error -> escape returns to last valid route cleanly
    useAppStore.getState().goHome();
    useAppStore.getState().syncLocationRoute("/simulation/thiet-dien-chop");
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().hasInAppNavigation).toBe(true);
    expect(useAppStore.getState().escapeFromError()).toBe("home");

    // Case 6: Reload on error URL -> clean `not_found` state, then escape -> `/`
    useAppStore.getState().reset();
    useAppStore.getState().syncLocationRoute("/simulation/khong-ton-tai");
    expect(useAppStore.getState().view).toBe("not_found");
    expect(useAppStore.getState().hasInAppNavigation).toBe(false);
    expect(useAppStore.getState().escapeFromError()).toBe("home");

    // Case 7 & 8: Browser popstate Back/Forward between valid route and error route -> store state stays consistent, then open valid sample
    useAppStore.getState().syncLocationRoute("/khong-ton-tai-2");
    expect(useAppStore.getState().view).toBe("not_found");
    useAppStore.getState().syncLocationRoute("/simulation/thiet-dien-chop");
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().active).not.toBeNull();

    // Case 9: Return from error -> hit a second error -> escape again without getting stuck in error loop
    useAppStore.getState().openHistory();
    useAppStore.getState().syncLocationRoute("/loi-lan-1");
    expect(useAppStore.getState().view).toBe("not_found");
    expect(useAppStore.getState().escapeFromError()).toBe("history");
    useAppStore.getState().syncLocationRoute("/loi-lan-2");
    expect(useAppStore.getState().view).toBe("not_found");
    expect(useAppStore.getState().escapeFromError()).toBe("history");
  });

  it("6. URL navigation to a corrupted history item (`scene3d` invalid) surfaces `unsupported_simulation` (never 404, never silent Home drop) and escapes cleanly", () => {
    const validBaseEnv = {
      status: "ok" as const,
      simulation_id: "generic.semantic_program",
      domain: "geometry" as const,
      visual_mode: "2d" as const,
      title: "Bản ghi 3D hỏng trong lịch sử",
      description: "Bản ghi hỏng.",
      config: {
        spec_version: "1.0",
        title: "Bản ghi 3D hỏng trong lịch sử",
        frames: [{ step_index: 0, narration: "Khởi tạo.", objects: [], highlighted_object_ids: [] }],
        view_steps: [{ view_index: 0, frame_lo: 0, frame_hi: 0, narration: "Khởi tạo." }],
      },
      notes: null,
    };
    const recorded = historyStore.record(validBaseEnv, "Bản ghi hỏng.");
    // Simulate corrupted scene3d persisted in storage
    historyStore.replaceAll?.([
      {
        ...recorded,
        envelope: { ...validBaseEnv, scene3d: { malformed: true } } as unknown as typeof validBaseEnv,
      },
    ]);
    // Khoá do `record` cấp (bản ghi có đề ⇒ khoá lần gửi `s…`), không tự dựng lại công thức khoá.
    const brokenId = recorded.id;

    useAppStore.getState().openHistory();
    useAppStore.getState().syncLocationRoute(`/simulation/${brokenId}`);
    expect(useAppStore.getState().routeFailure?.kind).toBe("unsupported_simulation");

    Object.assign(useAppStore.getInitialState(), useAppStore.getState());
    const html = renderToString(<App />);
    expect(html).toContain('data-error-kind="unsupported_simulation"');
    expect(html).not.toContain('data-error-kind="not_found"');
    expect(useAppStore.getState().escapeFromError()).toBe("history");
    historyStore.clear();
  });

  it("7. Adversarial Review [M-01] & [m-01]: escaping ErrorBoundary via TopNav clears `crashedResetKey` (preserving `canvasFirst` on return), and escaping Home `network_failure` stays on Home with `problemText` preserved", () => {
    // [m-01] Visit Library -> back to Home -> type problemText -> encounter network_failure -> escapeFromError stays on Home!
    useAppStore.getState().openLibrary();
    useAppStore.getState().goHome();
    useAppStore.getState().setProblemText("Cho hình chóp S.ABC có SA ⊥ (ABC).");
    useAppStore.getState().reportNetworkFailure({
      kind: "network",
      code: "NETWORK_UNREACHABLE",
      message: "Mất kết nối máy chủ.",
    });
    expect(useAppStore.getState().routeFailure?.kind).toBe("network_failure");
    expect(useAppStore.getState().escapeFromError()).toBe("home");
    expect(useAppStore.getState().view).toBe("home");
    expect(useAppStore.getState().problemText).toBe("Cho hình chóp S.ABC có SA ⊥ (ABC).");

    // [M-01] Simulate a workspace render crash -> escape via TopNav (`openLibrary`) -> reopen the SAME sample -> `crashedResetKey` must clear as soon as `mainResetKey` changes!
    const sample = publicCatalog()[0]!;
    const simKey = `workspace|${sample.id}|${sample.envelope.simulation_id}|${sample.envelope.title}`;
    expect(reconcileCrashedResetKey(simKey, simKey)).toBe(simKey);
    const afterTopNavEscape = reconcileCrashedResetKey(simKey, "library|||");
    expect(afterTopNavEscape).toBeNull();
    expect(reconcileCrashedResetKey(afterTopNavEscape, simKey)).toBeNull();

    useAppStore.getState().loadEnvelope(sample.envelope, sample.id);
    Object.assign(useAppStore.getInitialState(), useAppStore.getState());
    const cleanWorkspaceHtml = renderToString(<App />);
    expect(cleanWorkspaceHtml).toContain("la-canh-3d");
    expect(cleanWorkspaceHtml).not.toContain('class="nav-bar"');
  });
});
