import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { renderToString } from "react-dom/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PUBLIC_GEOMETRY_SAMPLES } from "../data/geometry-samples";
import { registerAllSimulations } from "../simulations";
import { getSimulation } from "../simulations/registry";
import type { SimulationEnvelope } from "../simulations/types";
import { TopNav } from "../components/TopNav";
import { LibraryView } from "../components/LibraryView";
import { WorkspaceTabBar } from "../components/WorkspaceTabBar";
import { useAuthStore } from "./auth";
import { __resetHistoryForTest, historyStore } from "./history";
import {
  clearLearnerRecoverySnapshot,
  loadLearnerRecoverySnapshot,
  saveLearnerRecoverySnapshot,
} from "./learner-recovery-snapshot";
import {
  resolveEffectiveWorkspaceTabs,
  useAppStore,
} from "./store";
import {
  buildProjectedWorkspaceTabs,
  DRAFT_RESOURCE_KEY,
  DRAFT_TAB_ID,
  findMatchingOpenSimulationTab,
  getSimulationResourceKey,
  LIBRARY_RESOURCE_KEY,
  LIBRARY_TAB_ID,
  LIBRARY_TAB_TITLE,
} from "./workspace-tab-identity";

registerAllSimulations();

const requireFromHere = createRequire(import.meta.url);
const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

const sAbcdSample =
  PUBLIC_GEOMETRY_SAMPLES.find(
    (s) => s.id === "chop-thiet-dien-ba-diem" || /S\.ABCD/i.test(s.problemText),
  ) ?? PUBLIC_GEOMETRY_SAMPLES[0]!;

const oxyzSample =
  PUBLIC_GEOMETRY_SAMPLES.find(
    (s) => s.id !== sAbcdSample.id && /oxyz/i.test(`${s.id} ${s.envelope.title} ${s.problemText}`),
  ) ?? PUBLIC_GEOMETRY_SAMPLES.find((s) => s.id !== sAbcdSample.id)!;

function cloneEnvelope(env: SimulationEnvelope): SimulationEnvelope {
  return JSON.parse(JSON.stringify(env)) as SimulationEnvelope;
}

function syncStoreForSSR() {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
  Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
}

function resetStoresClean() {
  clearLearnerRecoverySnapshot();
  __resetHistoryForTest();
  if (typeof sessionStorage !== "undefined") {
    try {
      sessionStorage.clear();
    } catch {
      /* bỏ qua nếu môi trường chỉ đọc */
    }
  }
  useAuthStore.setState({ user: null, resolved: true });
  useAppStore.getState().reset();
  useAppStore.getState().setGuestEnteredApp(true);
  syncStoreForSSR();
}

describe("Workspace Single-Instance Navigation & Snapshot Preservation", () => {
  beforeEach(() => {
    resetStoresClean();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    resetStoresClean();
  });

  it("canonical tab identity distinguishes catalog samples, custom learner submissions, library, and draft without duplicates", () => {
    expect(LIBRARY_TAB_ID).toBe("tab-library");
    expect(LIBRARY_RESOURCE_KEY).toBe("library");
    expect(LIBRARY_TAB_TITLE).toBe("Thư viện mô phỏng");
    expect(DRAFT_TAB_ID).toBe("tab-draft-new");
    expect(DRAFT_RESOURCE_KEY).toBe("draft:new");

    const sampleKeyById = getSimulationResourceKey({
      tabId: `tab-sample-${sAbcdSample.id}`,
      sampleId: sAbcdSample.id,
      title: sAbcdSample.envelope.title,
      envelope: sAbcdSample.envelope,
    });
    const sampleKeyByStatement = getSimulationResourceKey({
      title: sAbcdSample.envelope.title,
      problemStatement: `  ${sAbcdSample.problemText}  `,
      envelope: sAbcdSample.envelope,
    });
    expect(sampleKeyById).toBe(`problem:${sAbcdSample.id}`);
    expect(sampleKeyByStatement).toBe(`problem:${sAbcdSample.id}`);

    const customSubmissionKey = getSimulationResourceKey({
      tabId: "tab-hist-s999",
      historyId: "s999",
      title: sAbcdSample.envelope.title,
      originalInput: "Cho hình chóp S.ABCD có cạnh đáy bằng 99, đề tự nhập của người học.",
      envelope: sAbcdSample.envelope,
    });
    expect(customSubmissionKey).toBe("s999");
    expect(customSubmissionKey).not.toBe(sampleKeyById);

    const openTabs = [
      {
        id: `tab-sample-${sAbcdSample.id}`,
        kind: "simulation" as const,
        title: sAbcdSample.envelope.title,
        sampleId: sAbcdSample.id,
        historyId: "h-sabcd",
        active: {
          envelope: sAbcdSample.envelope,
          problemStatement: sAbcdSample.problemText,
        },
      },
      {
        id: "tab-dup-sabcd",
        kind: "simulation" as const,
        title: "Bản trùng S.ABCD",
        sampleId: sAbcdSample.id,
        historyId: "h-sabcd-dup",
        active: {
          envelope: sAbcdSample.envelope,
          problemStatement: sAbcdSample.problemText,
        },
      },
      {
        id: DRAFT_TAB_ID,
        kind: "draft" as const,
        title: "Bài toán mới",
        sampleId: null,
        historyId: null,
        active: null,
        draftText: "Đề nháp chưa chạy",
      },
    ];

    const foundBySample = findMatchingOpenSimulationTab(openTabs, {
      sampleId: sAbcdSample.id,
      envelope: sAbcdSample.envelope,
    });
    expect(foundBySample?.id).toBe(`tab-sample-${sAbcdSample.id}`);

    const missForCustomSubmission = findMatchingOpenSimulationTab(openTabs, {
      historyId: "s999",
      originalInput: "Đề tự nhập hoàn toàn khác biệt.",
      envelope: sAbcdSample.envelope,
    });
    expect(missForCustomSubmission).toBeUndefined();

    const projected = buildProjectedWorkspaceTabs(openTabs, true);
    expect(projected.map((t) => t.id)).toEqual([
      LIBRARY_TAB_ID,
      `tab-sample-${sAbcdSample.id}`,
      DRAFT_TAB_ID,
    ]);
    const resourceKeys = projected.map((t) => t.resourceKey);
    expect(new Set(resourceKeys).size).toBe(resourceKeys.length);
  });

  it("Scenarios A-D: Library is single-instance, preserves store.workspaceTabs simulation|draft invariant, and closes cleanly", () => {
    const store = useAppStore.getState();
    expect(store.libraryTabOpen).toBe(false);

    store.openLibrary();
    store.setView("library");
    store.syncLocationRoute("/library");

    let next = useAppStore.getState();
    expect(next.view).toBe("library");
    expect(next.libraryTabOpen).toBe(true);
    expect(next.workspaceTabs).toHaveLength(0);

    const projectedOnlyLib = buildProjectedWorkspaceTabs(next.workspaceTabs, next.libraryTabOpen);
    expect(projectedOnlyLib).toHaveLength(1);
    expect(projectedOnlyLib[0]).toMatchObject({
      id: LIBRARY_TAB_ID,
      kind: "library",
      resourceKey: LIBRARY_RESOURCE_KEY,
      title: LIBRARY_TAB_TITLE,
    });

    // Save UI state and load a sample + second background library navigation
    next.setLibraryUiState({ search: "Oxyz", category: "Oxyz", scrollTop: 320 });
    next.loadEnvelope(cloneEnvelope(sAbcdSample.envelope), sAbcdSample.id);
    next.openLibrary();

    next = useAppStore.getState();
    expect(next.view).toBe("library");
    expect(next.libraryTabOpen).toBe(true);
    expect(next.libraryUiState).toEqual({ search: "Oxyz", category: "Oxyz", scrollTop: 320 });
    expect(next.workspaceTabs.every((t) => t.kind === "simulation" || t.kind === "draft")).toBe(
      true,
    );

    const projectedBoth = buildProjectedWorkspaceTabs(next.workspaceTabs, next.libraryTabOpen);
    expect(projectedBoth.filter((t) => t.id === LIBRARY_TAB_ID)).toHaveLength(1);

    // Closing background simulation tab while viewing library stays on library
    next.loadEnvelope(cloneEnvelope(oxyzSample.envelope), oxyzSample.id);
    next.openLibrary();
    const oxyzTab = useAppStore
      .getState()
      .workspaceTabs.find((t) => t.sampleId === oxyzSample.id)!;
    useAppStore.getState().closeWorkspaceTab(oxyzTab.id);
    expect(useAppStore.getState().view).toBe("library");
    expect(useAppStore.getState().libraryTabOpen).toBe(true);

    // Closing library tab resets libraryTabOpen + libraryUiState and falls back to open simulation tab
    useAppStore.getState().closeWorkspaceTab(LIBRARY_TAB_ID);
    next = useAppStore.getState();
    expect(next.libraryTabOpen).toBe(false);
    expect(next.libraryUiState).toEqual({ search: "", category: "all", scrollTop: 0 });
    expect(next.view).toBe("workspace");
    expect(next.activeSampleId).toBe(sAbcdSample.id);

    // Closing last tab when library is closed falls back to home
    const lastTabId = next.activeTabId!;
    next.closeWorkspaceTab(lastTabId);
    expect(useAppStore.getState().view).toBe("home");

    // Reopen library with zero simulation tabs, then close library -> goes home
    useAppStore.getState().openLibrary();
    expect(useAppStore.getState().libraryTabOpen).toBe(true);
    useAppStore.getState().closeWorkspaceTab(LIBRARY_TAB_ID);
    expect(useAppStore.getState().libraryTabOpen).toBe(false);
    expect(useAppStore.getState().view).toBe("home");
  });

  it("Scenarios 1-7: re-activating open problems via sidebar, history, loadEnvelope, or route activates existing tab without re-init or deleting background draft", () => {
    const geomMod = getSimulation(sAbcdSample.envelope.simulation_id)!;
    expect(geomMod).toBeDefined();
    const initSpy = vi.spyOn(geomMod, "init");
    const validateSpy = vi.spyOn(geomMod, "validateEnvelope");

    const store = useAppStore.getState();
    store.openLibrary();
    store.loadEnvelope(cloneEnvelope(sAbcdSample.envelope), sAbcdSample.id);
    expect(initSpy).toHaveBeenCalledTimes(1);

    const sAbcdTab = useAppStore
      .getState()
      .workspaceTabs.find((t) => t.sampleId === sAbcdSample.id)!;
    const sAbcdHistoryId = sAbcdTab.historyId!;
    const initialStateRef = sAbcdTab.active!.state as Record<string, unknown>;
    // Simulate interactive user state on the open S.ABCD tab
    initialStateRef.__preservedCursorMarker = "step-5-camera-custom";

    // Open draft tab, type draft text, then switch to library so draft stays in background
    useAppStore.getState().openDraftWorkspaceTab();
    useAppStore.getState().setProblemText("Đang soạn đề tự nhập...");
    useAppStore.getState().openLibrary();

    // Load second problem (Oxyz) from library: preserves background tab-draft-new AND S.ABCD
    useAppStore.getState().loadEnvelope(cloneEnvelope(oxyzSample.envelope), oxyzSample.id);
    expect(initSpy).toHaveBeenCalledTimes(2);
    const oxyzHistoryId = useAppStore
      .getState()
      .workspaceTabs.find((t) => t.sampleId === oxyzSample.id)!.historyId!;

    // Close Oxyz later to test reopenFromHistory for an unopened tab, wait — first verify re-activation of open S.ABCD across ALL entry points
    initSpy.mockClear();
    validateSpy.mockClear();

    // 1. selectSidebarProblem(sAbcdHistoryId) -> in-place activate, 0 init calls
    useAppStore.getState().selectSidebarProblem(sAbcdHistoryId);
    let after = useAppStore.getState();
    expect(after.activeTabId).toBe(sAbcdTab.id);
    expect(after.view).toBe("workspace");
    expect(initSpy).not.toHaveBeenCalled();

    // Switch back to Oxyz so we actually switch tabs on subsequent activations
    useAppStore.getState().selectSidebarProblem(oxyzHistoryId);
    expect(useAppStore.getState().activeSampleId).toBe(oxyzSample.id);
    expect(initSpy).not.toHaveBeenCalled();

    // 2. reopenFromHistory(sAbcdHistoryId) -> validates cleanly and activates in-place with 0 init calls
    useAppStore.getState().reopenFromHistory(sAbcdHistoryId);
    after = useAppStore.getState();
    expect(validateSpy).toHaveBeenCalledTimes(1);
    expect(initSpy).not.toHaveBeenCalled();
    expect(after.activeTabId).toBe(sAbcdTab.id);

    // 3. loadEnvelope canonical sample match -> activates in-place with 0 init calls
    useAppStore.getState().selectSidebarProblem(oxyzHistoryId);
    useAppStore.getState().loadEnvelope(cloneEnvelope(sAbcdSample.envelope), sAbcdSample.id);
    after = useAppStore.getState();
    expect(initSpy).not.toHaveBeenCalled();
    expect(after.activeTabId).toBe(sAbcdTab.id);

    // Verify zero duplicates, draft preserved, Oxyz preserved, and S.ABCD state object untouched
    expect(after.workspaceTabs.map((t) => t.id)).toHaveLength(3);
    const preservedSabcd = after.workspaceTabs.find((t) => t.id === sAbcdTab.id)!;
    expect(preservedSabcd.active?.state).toBe(initialStateRef);
    expect((preservedSabcd.active?.state as Record<string, unknown>).__preservedCursorMarker).toBe(
      "step-5-camera-custom",
    );
    const preservedDraft = after.workspaceTabs.find((t) => t.id === DRAFT_TAB_ID)!;
    expect(preservedDraft.draftText).toBe("Đang soạn đề tự nhập...");

    // 4. Closing Oxyz then reopening from history opens it cleanly while preserving S.ABCD + draft
    const oxyzTab = after.workspaceTabs.find((t) => t.sampleId === oxyzSample.id)!;
    useAppStore.getState().closeWorkspaceTab(oxyzTab.id);
    expect(historyStore.list().some((h) => h.id === oxyzHistoryId)).toBe(true);
    useAppStore.getState().reopenFromHistory(oxyzHistoryId);
    after = useAppStore.getState();
    expect(initSpy).toHaveBeenCalledTimes(1);
    expect(after.activeSampleId).toBe(oxyzSample.id);
    expect(after.workspaceTabs).toHaveLength(3);
    expect(after.workspaceTabs.find((t) => t.id === DRAFT_TAB_ID)?.draftText).toBe(
      "Đang soạn đề tự nhập...",
    );
  });

  it("LearnerRecoverySnapshot persists optional relationActiveForId and relationsExpanded with backward compatibility", () => {
    const storeMap = new Map<string, string>();
    const memStorage: Pick<Storage, "getItem" | "setItem" | "removeItem"> = {
      getItem: (k) => storeMap.get(k) ?? null,
      setItem: (k, v) => {
        storeMap.set(k, v);
      },
      removeItem: (k) => {
        storeMap.delete(k);
      },
    };

    const baseDisplay = {
      showShell: true,
      showVertexLabels: true,
      showPlane: true,
      showSection: true,
      showAxes: false,
      showDimensionLabels: true,
      showRightAngles: true,
      showDashedHidden: true,
      auxiliaryShown: false,
      gridShown: false,
      xray: false,
      shellOpacityPct: 24,
      planeOpacityPct: 28,
    };

    saveLearnerRecoverySnapshot(
      {
        problemKey: `sample:${sAbcdSample.id}`,
        stepIndex: 4,
        selectedId: "SA",
        dockCollapsed: false,
        mobileViewMode: "dock_open",
        display: baseDisplay,
        camera: null,
        relationActiveForId: "SA",
        relationsExpanded: true,
      },
      { storage: memStorage },
    );

    const loadedWithRel = loadLearnerRecoverySnapshot(`sample:${sAbcdSample.id}`, {
      storage: memStorage,
    });
    expect(loadedWithRel?.relationActiveForId).toBe("SA");
    expect(loadedWithRel?.relationsExpanded).toBe(true);

    saveLearnerRecoverySnapshot(
      {
        problemKey: `sample:${oxyzSample.id}`,
        stepIndex: 2,
        selectedId: null,
        dockCollapsed: true,
        mobileViewMode: "stage_expanded",
        display: baseDisplay,
        camera: null,
      },
      { storage: memStorage },
    );

    const loadedWithoutRel = loadLearnerRecoverySnapshot(`sample:${oxyzSample.id}`, {
      storage: memStorage,
    });
    expect(loadedWithoutRel?.stepIndex).toBe(2);
    expect(loadedWithoutRel?.relationActiveForId).toBeUndefined();
    expect(loadedWithoutRel?.relationsExpanded).toBeUndefined();
  });

  it("SSR components: TopNav, LibraryView, WorkspaceTabBar render canonical data-* attributes without banned Unicode icons", () => {
    const store = useAppStore.getState();
    store.openLibrary();
    store.setLibraryUiState({ search: "hình chóp", category: "Tất cả", scrollTop: 0 });
    store.loadEnvelope(cloneEnvelope(sAbcdSample.envelope), sAbcdSample.id);
    store.openDraftWorkspaceTab();
    store.openLibrary();

    const { tabs: effectiveTabs } = resolveEffectiveWorkspaceTabs(useAppStore.getState());
    expect(effectiveTabs).toHaveLength(2);
    syncStoreForSSR();

    const libHtml = renderToString(<LibraryView />);
    expect(libHtml).toContain('class="axo-header ws-axo-header"');
    expect(libHtml).toContain('data-ws-tab-bar="true"');
    expect(libHtml).toContain(`data-tab-id="${LIBRARY_TAB_ID}"`);
    expect(libHtml).toContain('data-tab-kind="library"');
    expect(libHtml).toContain(`data-resource-key="${LIBRARY_RESOURCE_KEY}"`);
    expect(libHtml).toContain(`data-resource-key="problem:${sAbcdSample.id}"`);
    expect(libHtml).toContain(`data-resource-key="${DRAFT_RESOURCE_KEY}"`);
    expect(libHtml).toContain('id="view-library"');
    expect(libHtml).toContain('value="hình chóp"');

    const tabBarHtml = renderToString(<WorkspaceTabBar fallbackTitle="Mô phỏng dự phòng" />);
    expect(tabBarHtml).toContain(`data-close-tab="${LIBRARY_TAB_ID}"`);
    expect(tabBarHtml).toContain('id="btn-ws-back"');
    expect(tabBarHtml).toContain('id="btn-ws-forward"');
    expect(tabBarHtml).toContain('id="btn-header-change-prob"');

    const topNavHtml = renderToString(<TopNav />);
    expect(topNavHtml).toContain("Thư viện");

    // Closing library removes tab bar from LibraryView SSR while keeping #view-library intact
    useAppStore.getState().closeWorkspaceTab(LIBRARY_TAB_ID);
    syncStoreForSSR();
    const closedLibHtml = renderToString(<LibraryView />);
    expect(closedLibHtml).not.toContain('data-ws-tab-bar');
    expect(closedLibHtml).toContain('id="view-library"');
  });

  it(
    "Live Chromium DOM + StrictMode: Library search/category/scroll preservation, pushState/popstate Back/Forward, and sessionStorage reload hydration without duplicate tabs",
    async () => {
      const esbuild = requireFromHere("esbuild") as typeof import("esbuild");
      const { chromium } = requireFromHere("playwright") as typeof import("playwright");

      const globalCss = readFileSync(path.join(frontendDir, "src/styles/global.css"), "utf8");
      const tokensCss = readFileSync(path.join(frontendDir, "src/styles/tokens.css"), "utf8");

      const harnessCode = `
        import React, { StrictMode } from "react";
        import { createRoot } from "react-dom/client";
        import App from "./App";
        import { registerAllSimulations } from "./simulations";
        import { useAuthStore } from "./state/auth";
        import { useAppStore, WORKSPACE_SESSION_STORAGE_KEY } from "./state/store";
        import { PUBLIC_GEOMETRY_SAMPLES } from "./data/geometry-samples";

        registerAllSimulations();
        useAuthStore.setState({ user: null, resolved: true });
        useAppStore.getState().reset();
        useAppStore.getState().setGuestEnteredApp(true);

        let currentRoot = null;
        const container = document.getElementById("root");

        function mountStrict(keySuffix) {
          if (currentRoot) {
            currentRoot.unmount();
          }
          currentRoot = createRoot(container);
          currentRoot.render(
            React.createElement(StrictMode, null, React.createElement(App, { key: keySuffix }))
          );
        }

        window.__axoTestHarness = {
          mountStrict,
          remountSimulatingReload: () => {
            // Reset store in-memory and clear hydration guard via reset() without clearing sessionStorage:
            // save snapshot, reset store, restore sessionStorage, remount under StrictMode
            const saved = sessionStorage.getItem(WORKSPACE_SESSION_STORAGE_KEY);
            useAppStore.getState().reset();
            useAppStore.getState().setGuestEnteredApp(true);
            if (saved) sessionStorage.setItem(WORKSPACE_SESSION_STORAGE_KEY, saved);
            mountStrict("reload-" + Date.now());
          },
          getStoreSnapshot: () => {
            const s = useAppStore.getState();
            return {
              view: s.view,
              libraryTabOpen: s.libraryTabOpen,
              libraryUiState: s.libraryUiState,
              activeTabId: s.activeTabId,
              activeSampleId: s.activeSampleId,
              workspaceTabIds: s.workspaceTabs.map((t) => ({ id: t.id, kind: t.kind, sampleId: t.sampleId })),
            };
          },
          samples: {
            sAbcdId: ${JSON.stringify(sAbcdSample.id)},
            sAbcdTitle: ${JSON.stringify(sAbcdSample.envelope.title)},
            oxyzId: ${JSON.stringify(oxyzSample.id)},
            oxyzTitle: ${JSON.stringify(oxyzSample.envelope.title)},
          },
          openLibrary: () => useAppStore.getState().openLibrary(),
          loadSample: (id) => {
            const found = PUBLIC_GEOMETRY_SAMPLES.find((x) => x.id === id);
            if (found) useAppStore.getState().loadEnvelope(JSON.parse(JSON.stringify(found.envelope)), found.id);
          },
          activateTab: (id) => useAppStore.getState().activateWorkspaceTab(id),
          closeTab: (id) => useAppStore.getState().closeWorkspaceTab(id),
        };

        mountStrict("initial");
      `;

      const built = await esbuild.build({
        stdin: {
          contents: harnessCode,
          resolveDir: path.join(frontendDir, "src"),
          loader: "tsx",
        },
        bundle: true,
        write: false,
        format: "esm",
        jsx: "automatic",
        target: "es2022",
        loader: { ".json": "json", ".css": "text", ".svg": "dataurl", ".png": "dataurl" },
        define: {
          "process.env.NODE_ENV": '"development"',
          "import.meta.env.DEV": "true",
          "import.meta.env.PROD": "false",
          "import.meta.env.MODE": '"test"',
          "import.meta.env.VITE_API_BASE": '""',
        },
      });

      const bundleJs = built.outputFiles[0]!.text;
      const htmlDoc = `<!DOCTYPE html>
<html lang="vi">
  <head>
    <meta charset="utf-8" />
    <style>${tokensCss}\n${globalCss}\nhtml, body { margin: 0; }</style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/bundle.js"></script>
  </body>
</html>`;

      const browser = await chromium.launch({ headless: true });
      const pageErrors: string[] = [];
      const consoleErrors: string[] = [];
      let stage = "launch";

      try {
        const context = await browser.newContext({ viewport: { width: 1200, height: 640 } });
        const page = await context.newPage();

        // Intercept static HTML navigation and /bundle.js cleanly so history.pushState works on real origin
        await page.route("http://axo.test/**", async (route) => {
          const url = route.request().url();
          if (url === "http://axo.test/bundle.js") {
            await route.fulfill({
              status: 200,
              contentType: "application/javascript; charset=utf-8",
              body: bundleJs,
            });
          } else if (
            url === "http://axo.test/" ||
            url.startsWith("http://axo.test/app") ||
            url.startsWith("http://axo.test/library") ||
            url.startsWith("http://axo.test/workspace") ||
            url.startsWith("http://axo.test/simulation")
          ) {
            await route.fulfill({
              status: 200,
              contentType: "text/html; charset=utf-8",
              body: htmlDoc,
            });
          } else if (url.includes("/api/auth/")) {
            await route.fulfill({ status: 200, contentType: "application/json", body: '{"user":null}' });
          } else {
            await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
          }
        });

        page.on("pageerror", (err) => pageErrors.push(String(err)));
        page.on("console", (msg) => {
          if (msg.type() === "error") consoleErrors.push(msg.text());
        });

        stage = "goto-app";
        await page.goto("http://axo.test/app", { waitUntil: "domcontentloaded" });
        try {
          await page.waitForSelector("#nav-item-library", { timeout: 5000 });

          // 1. Click Library in Sidebar -> opens single tab-library & #view-library
          stage = "click-sidebar-library-1";
          await page.click("#nav-item-library", { timeout: 4000 });
          await page.waitForSelector("#view-library", { timeout: 5000 });
          await page.waitForSelector('[data-tab-id="tab-library"]', { timeout: 5000 });

          // Clicking sidebar Library again creates 0 duplicate tabs
          stage = "click-sidebar-library-2";
          await page.click("#nav-item-library", { timeout: 4000 });
          const libTabCount = await page.locator('[data-tab-id="tab-library"]').count();
          expect(libTabCount).toBe(1);

          // 2A. Scroll Library with full catalog (11 cards), switch to Oxyz, return -> real DOM/window scrollTop preserved!
          stage = "scroll-and-preserve-library";
          const scrollInfo = await page.evaluate(() => {
            const candidates = [
              document.getElementById("view-library"),
              document.querySelector(".app-single"),
            ].filter((el): el is HTMLElement => Boolean(el));
            const scroller = candidates.find((el) => el.scrollHeight > el.clientHeight) ?? null;
            if (scroller) {
              scroller.scrollTop = 160;
              scroller.dispatchEvent(new Event("scroll"));
              return { found: true, mode: "element", scrollTop: scroller.scrollTop };
            }
            const docEl = document.scrollingElement || document.documentElement;
            if (docEl.scrollHeight > window.innerHeight) {
              window.scrollTo(0, 160);
              window.dispatchEvent(new Event("scroll"));
              return { found: true, mode: "window", scrollTop: window.scrollY };
            }
            return { found: false, mode: "none", scrollTop: 0 };
          });
          expect(scrollInfo.found).toBe(true);
          expect(scrollInfo.scrollTop).toBeGreaterThan(0);

          await page.click(`.lib-card[data-lib-prob="${oxyzSample.id}"]`, { timeout: 4000 });
          await page.waitForFunction(
            (oid) => {
              const snap = (
                window as unknown as {
                  __axoTestHarness: {
                    getStoreSnapshot: () => { view: string; activeSampleId: string | null };
                  };
                }
              ).__axoTestHarness.getStoreSnapshot();
              return snap.view === "workspace" && snap.activeSampleId === oid;
            },
            oxyzSample.id,
            { timeout: 5000 },
          );

          await page.click("#nav-item-library", { timeout: 4000 });
          await page.waitForSelector("#view-library", { timeout: 5000 });
          await page.waitForFunction(
            () => {
              const candidates = [
                document.getElementById("view-library"),
                document.querySelector(".app-single"),
              ].filter((el): el is HTMLElement => Boolean(el));
              return window.scrollY >= 120 || candidates.some((el) => el.scrollTop >= 120);
            },
            undefined,
            { timeout: 3000 },
          );

          // 2B. Apply category filter & search, open S.ABCD card, return -> search + category preserved!
          stage = "filter-search-and-open-sabcd";
          const sabcdCategory = (
            (
              await page
                .locator(`.lib-card[data-lib-prob="${sAbcdSample.id}"] .lib-card-cat`)
                .textContent({ timeout: 4000 })
            ) ?? ""
          ).trim();
          await page.click("#btn-library-category-dropdown", { timeout: 4000 });
          await page.click(`#library-category-menu [data-lib-cat="${sabcdCategory}"]`, {
            timeout: 4000,
          });
          await page.fill("#library-search-input", "S.ABCD", { timeout: 4000 });
          await page.waitForTimeout(80);

          await page.click(`.lib-card[data-lib-prob="${sAbcdSample.id}"]`, { timeout: 4000 });
          await page.waitForFunction(
            (sid) => {
              const snap = (
                window as unknown as {
                  __axoTestHarness: {
                    getStoreSnapshot: () => { view: string; activeSampleId: string | null };
                  };
                }
              ).__axoTestHarness.getStoreSnapshot();
              return snap.view === "workspace" && snap.activeSampleId === sid;
            },
            sAbcdSample.id,
            { timeout: 5000 },
          );

          // Return to Library via Sidebar -> search + category preserved
          stage = "return-to-library";
          await page.click("#nav-item-library", { timeout: 4000 });
          await page.waitForSelector("#library-search-input", { timeout: 5000 });
          const restoredLibState = await page.evaluate(() => {
            const searchEl = document.getElementById("library-search-input") as HTMLInputElement | null;
            const catLabel = document.getElementById("library-category-btn-label")?.textContent ?? "";
            const snap = (
              window as unknown as {
                __axoTestHarness: {
                  getStoreSnapshot: () => {
                    libraryUiState: { search: string; category: string; scrollTop: number };
                  };
                };
              }
            ).__axoTestHarness.getStoreSnapshot();
            return {
              inputValue: searchEl?.value ?? "",
              catLabel: catLabel.trim(),
              libraryUiState: snap.libraryUiState,
            };
          });
          expect(restoredLibState.inputValue).toBe("S.ABCD");
          expect(restoredLibState.libraryUiState.search).toBe("S.ABCD");
          expect(restoredLibState.libraryUiState.category).toBe(sabcdCategory);
          expect(restoredLibState.catLabel).toContain(sabcdCategory);

          // Clear filter and switch to Oxyz (already open single-instance tab!)
          stage = "open-oxyz";
          await page.fill("#library-search-input", "", { timeout: 4000 });
          await page.click('#view-library [aria-label^="Bỏ lọc"]', { timeout: 4000 });
          await page.waitForTimeout(60);
          await page.evaluate((id) => {
            (
              window as unknown as { __axoTestHarness: { loadSample: (x: string) => void } }
            ).__axoTestHarness.loadSample(id);
          }, oxyzSample.id);

          await page.waitForFunction(
            (oid) =>
              (
                window as unknown as {
                  __axoTestHarness: {
                    getStoreSnapshot: () => { activeSampleId: string | null };
                  };
                }
              ).__axoTestHarness.getStoreSnapshot().activeSampleId === oid,
            oxyzSample.id,
            { timeout: 5000 },
          );

          // Test Browser Back/Forward (popstate with axoView/axoTabId)
          stage = "popstate-back";
          await page.goBack();
          await page.waitForFunction(
            () =>
              (
                window as unknown as {
                  __axoTestHarness: { getStoreSnapshot: () => { view: string } };
                }
              ).__axoTestHarness.getStoreSnapshot().view === "library",
            undefined,
            { timeout: 5000 },
          );
          stage = "popstate-forward";
          await page.goForward();
          await page.waitForFunction(
            (oid) => {
              const s = (
                window as unknown as {
                  __axoTestHarness: {
                    getStoreSnapshot: () => { view: string; activeSampleId: string | null };
                  };
                }
              ).__axoTestHarness.getStoreSnapshot();
              return s.view === "workspace" && s.activeSampleId === oid;
            },
            oxyzSample.id,
            { timeout: 5000 },
          );

          // No duplicate tabs across navigation
          stage = "pre-reload-check";
          const preReloadSnap = await page.evaluate(() =>
            (
              window as unknown as {
                __axoTestHarness: {
                  getStoreSnapshot: () => {
                    libraryTabOpen: boolean;
                    workspaceTabIds: { id: string; sampleId: string | null }[];
                    activeSampleId: string | null;
                  };
                };
              }
            ).__axoTestHarness.getStoreSnapshot(),
          );
          expect(preReloadSnap.libraryTabOpen).toBe(true);
          expect(preReloadSnap.workspaceTabIds).toHaveLength(2);

          // Simulate reload under React StrictMode double-mount -> tabs restored without duplicates
          stage = "strictmode-reload";
          await page.evaluate(() => {
            (
              window as unknown as { __axoTestHarness: { remountSimulatingReload: () => void } }
            ).__axoTestHarness.remountSimulatingReload();
          });
          await page.waitForFunction(
            (oid) => {
              const s = (
                window as unknown as {
                  __axoTestHarness: {
                    getStoreSnapshot: () => {
                      view: string;
                      activeSampleId: string | null;
                      workspaceTabIds: unknown[];
                    };
                  };
                }
              ).__axoTestHarness.getStoreSnapshot();
              return (
                s.view === "workspace" &&
                s.activeSampleId === oid &&
                s.workspaceTabIds.length === 2
              );
            },
            oxyzSample.id,
            { timeout: 5000 },
          );

          // Close tab-library from LibraryView WorkspaceTabBar button
          stage = "close-tab-library";
          await page.click("#nav-item-library", { timeout: 4000 });
          await page.waitForSelector('[data-close-tab="tab-library"]', { timeout: 5000 });
          await page.click('[data-close-tab="tab-library"]', { timeout: 4000 });
          await page.waitForFunction(
            () => {
              const s = (
                window as unknown as {
                  __axoTestHarness: {
                    getStoreSnapshot: () => { libraryTabOpen: boolean; view: string };
                  };
                }
              ).__axoTestHarness.getStoreSnapshot();
              return !s.libraryTabOpen && s.view === "workspace";
            },
            undefined,
            { timeout: 5000 },
          );

          expect(pageErrors).toEqual([]);
          expect(consoleErrors).toEqual([]);
        } catch (err) {
          const domSnippet = await page.evaluate(() => document.body.innerHTML.slice(0, 700));
          throw new Error(
            `stage=${stage} failed (${String(err)}). pageErrors=${JSON.stringify(pageErrors)} consoleErrors=${JSON.stringify(consoleErrors)} dom=${domSnippet}`,
          );
        }
      } finally {
        await browser.close();
      }
    },
    45000,
  );
});
