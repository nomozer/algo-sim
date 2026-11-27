import { Suspense } from "react";
import { renderToString } from "react-dom/server";
import { beforeEach, describe, expect, it } from "vitest";
import App from "../../App";
import { registerAllSimulations } from "../../simulations";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { __resetHistoryForTest } from "../../state/history";
import { useAppStore } from "../../state/store";
import { renderReadyHtml } from "../../test-source";
import {
  isChunkLoadError,
  lazyWithRetry,
  shouldPrefetchOnIntent,
} from "../../utils/lazy-with-retry";

registerAllSimulations();

function syncStoresForSSR() {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
  Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
}

const ADMIN_USER: AuthUser = {
  id: 901,
  email: "admin-lazy@axo.edu.vn",
  displayName: "Quản trị Axo",
  role: "admin",
  mustChangePassword: false,
  status: "active",
};

describe("Route-level Lazy Loading, Retry & Sample Loading Concurrency", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
    useAuthStore.setState({ user: null, resolved: true, authGate: null, error: null });
    syncStoresForSSR();
  });

  it("renders Suspense loading fallback immediately on unresolved lazy routes without blank shell", () => {
    useAppStore.getState().syncLocationRoute("/library", "", "");
    syncStoresForSSR();
    const libPendingHtml = renderToString(<App />);
    expect(libPendingHtml).toContain("axo-route-loading");
    expect(libPendingHtml).toContain("Đang tải thư viện mô phỏng");
    expect(libPendingHtml).toContain("axo-left-sidebar-slot");
  });

  it("resolves /, /about, /login, /library, /admin, and /simulation/<slug> cleanly via renderReadyHtml", async () => {
    useAppStore.getState().syncLocationRoute("/", "", "");
    syncStoresForSSR();
    const landingHtml = await renderReadyHtml(<App />);
    expect(landingHtml).toContain('id="view-landing"');
    expect(landingHtml).not.toContain('id="left-sidebar"');

    useAppStore.getState().syncLocationRoute("/about", "", "");
    syncStoresForSSR();
    const aboutHtml = await renderReadyHtml(<App />);
    expect(aboutHtml).toContain('id="view-landing"');

    useAppStore.getState().syncLocationRoute("/login", "", "");
    syncStoresForSSR();
    const loginHtml = await renderReadyHtml(<App />);
    expect(loginHtml).toContain("Đăng nhập");

    useAppStore.getState().syncLocationRoute("/library", "", "");
    syncStoresForSSR();
    const libraryHtml = await renderReadyHtml(<App />);
    expect(libraryHtml).toContain('id="view-library"');

    useAuthStore.setState({ user: ADMIN_USER, resolved: true });
    useAppStore.getState().setView("admin");
    syncStoresForSSR();
    const adminHtml = await renderReadyHtml(<App />);
    expect(adminHtml).toContain("Quản trị");

    useAuthStore.setState({ user: null, resolved: true });
    useAppStore.getState().syncLocationRoute("/simulation/thiet-dien-chop", "", "");
    await useAppStore.getState().waitForPendingSampleLoad();
    syncStoresForSSR();
    const simHtml = await renderReadyHtml(<App />);
    expect(simHtml).toContain('id="ws-dock"');
    expect(simHtml).not.toContain('data-error-kind="not_found"');
  });

  it("lazyWithRetry retries once on transient network failure and clears cached failure for manual retry", async () => {
    let calls = 0;
    const RecoveringLazy = lazyWithRetry(async () => {
      calls += 1;
      if (calls === 1) {
        throw new Error("Failed to fetch dynamically imported module: chunk-a.js");
      }
      return {
        default: function RecoveredView() {
          return <div data-recovered-chunk="ok">Recovered</div>;
        },
      };
    });

    await RecoveringLazy.preload();
    expect(calls).toBe(2);

    let html = await renderReadyHtml(
      <Suspense fallback={<div>loading</div>}>
        <RecoveringLazy />
      </Suspense>,
    );
    expect(html).toContain('data-recovered-chunk="ok"');

    // Twice failing load rejects and resets preloaded promise so subsequent retry calls loader again.
    let permanentCalls = 0;
    const ResettableLazy = lazyWithRetry(async () => {
      permanentCalls += 1;
      if (permanentCalls <= 2) {
        throw new Error("ChunkLoadError: Loading chunk 42 failed.");
      }
      return {
        default: function AfterManualRetry() {
          return <div data-manual-retry="ok">OK</div>;
        },
      };
    });

    await expect(ResettableLazy.preload()).rejects.toThrow(/ChunkLoadError/);
    expect(permanentCalls).toBe(2);

    await expect(ResettableLazy.preload()).resolves.toBeDefined();
    expect(permanentCalls).toBe(3);

    html = await renderReadyHtml(
      <Suspense fallback={<div>loading</div>}>
        <ResettableLazy />
      </Suspense>,
    );
    expect(html).toContain('data-manual-retry="ok"');
  });

  it("detects chunk load errors accurately across browser engines", () => {
    expect(isChunkLoadError(new Error("Failed to fetch dynamically imported module: /x.js"))).toBe(true);
    expect(isChunkLoadError(new Error("Importing a module script failed."))).toBe(true);
    expect(isChunkLoadError(new Error("Unable to preload CSS for /assets/foo.css"))).toBe(true);
    expect(isChunkLoadError(new Error("Syntax error in JSON"))).toBe(false);
    expect(isChunkLoadError("non-error")).toBe(false);
  });

  it("shouldPrefetchOnIntent respects Save-Data and slow cellular connections", () => {
    const nav = navigator as Navigator & { connection?: unknown };
    const prevDescriptor = Object.getOwnPropertyDescriptor(nav, "connection");
    try {
      Object.defineProperty(nav, "connection", {
        configurable: true,
        value: { saveData: true, effectiveType: "4g" },
      });
      expect(shouldPrefetchOnIntent()).toBe(false);

      Object.defineProperty(nav, "connection", {
        configurable: true,
        value: { saveData: false, effectiveType: "2g" },
      });
      expect(shouldPrefetchOnIntent()).toBe(false);

      Object.defineProperty(nav, "connection", {
        configurable: true,
        value: { saveData: false, effectiveType: "4g" },
      });
      expect(shouldPrefetchOnIntent()).toBe(true);
    } finally {
      if (prevDescriptor) {
        Object.defineProperty(nav, "connection", prevDescriptor);
      } else {
        delete (nav as { connection?: unknown }).connection;
      }
    }
  });

  it("openSampleById guards against out-of-order async resolution when user switches route", async () => {
    const firstPromise = useAppStore.getState().openSampleById("cau-cat-mat-phang");
    useAppStore.getState().openLibrary();
    await firstPromise;
    await useAppStore.getState().waitForPendingSampleLoad();

    expect(useAppStore.getState().view).toBe("library");
    expect(useAppStore.getState().loadingSampleId).toBeNull();
  });
});
