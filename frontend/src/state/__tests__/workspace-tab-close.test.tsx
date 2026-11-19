import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import esbuild from "esbuild";
import { chromium } from "playwright";
import { renderToString } from "react-dom/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  clearSavedDraftAttachments,
  runComposerSubmit,
} from "../../components/ProblemInput";
import { useToastStore } from "../../components/TopNav";
import { WorkspaceTabBar } from "../../components/WorkspaceTabBar";
import { publicCatalog } from "../../data/offline-catalog";
import type { SimulationEnvelope } from "../../simulations/types";
import { useAuthStore } from "../auth";
import { __resetHistoryForTest, historyStore } from "../history";
import { registerAllSimulations } from "../../simulations";
import { useAppStore } from "../store";
import { DRAFT_TAB_ID, LIBRARY_TAB_ID } from "../workspace-tab-identity";

registerAllSimulations();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendDir = path.resolve(__dirname, "../../..");
const tokensCss = readFileSync(path.join(frontendDir, "src/styles/tokens.css"), "utf8");
const globalCss = readFileSync(path.join(frontendDir, "src/styles/global.css"), "utf8");

function cloneEnvelope<T>(env: T): T {
  return JSON.parse(JSON.stringify(env)) as T;
}

const sampleA = publicCatalog()[0]!;
const sampleB = publicCatalog()[1] ?? publicCatalog()[0]!;

describe("AXO V9.4.20.1 — Seamless Workspace Tab Closing & Draft Lifecycle", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    __resetHistoryForTest();
    clearSavedDraftAttachments();
    useToastStore.setState({ toasts: [] });
    useAuthStore.setState({ user: null, resolved: true });
    useAppStore.getState().reset();
    useAppStore.getState().setProblemText("");
  });

  afterEach(() => {
    vi.restoreAllMocks();
    clearSavedDraftAttachments();
    useToastStore.setState({ toasts: [] });
    useAppStore.getState().reset();
    useAppStore.getState().setProblemText("");
  });

  it("removes window.confirm from WorkspaceTabBar without adding replacement modal/toast/undo/banner", () => {
    const tabBarSrc = readFileSync(
      path.join(frontendDir, "src/components/WorkspaceTabBar.tsx"),
      "utf8",
    );
    expect(tabBarSrc).not.toContain("window.confirm");
    expect(tabBarSrc).not.toContain("Em đang nhập dở đề bài");
    expect(tabBarSrc).not.toContain("Đã đóng tab");
    expect(tabBarSrc).not.toContain("Hoàn tác");

    useAppStore.getState().loadEnvelope(cloneEnvelope(sampleA.envelope), sampleA.id);
    const tabAId = useAppStore.getState().activeTabId!;
    useAppStore.getState().openDraftWorkspaceTab();
    useAppStore.getState().setProblemText("Cho hình chóp S.ABCD có đáy là hình vuông.");
    useAppStore.getState().activateWorkspaceTab(tabAId);
    Object.assign(useAppStore.getInitialState(), useAppStore.getState());

    const html = renderToString(<WorkspaceTabBar />);
    expect(html).toContain(`data-close-tab="${DRAFT_TAB_ID}"`);
    expect(html).not.toContain("Đã đóng tab");
  });

  it("handles empty draft vs unsent text draft preservation across tab close, explicit new problem clean start, active/inactive close, last tab fallback, state isolation, and rapid open/close", () => {
    const confirmSpy = vi.fn(() => false);
    vi.stubGlobal("confirm", confirmSpy);

    const store = useAppStore.getState();

    // 1. Open simulation A, advance to step 3 & attach custom camera/xray state marker
    store.loadEnvelope(cloneEnvelope(sampleA.envelope), sampleA.id);
    const tabAId = useAppStore.getState().activeTabId!;
    const tabAStateRef = useAppStore.getState().active!.state as Record<string, unknown>;
    tabAStateRef.__tabLifecycleMarker = "camera-step-3-preserved";

    // 2. Empty draft tab closes immediately without confirmation or creating empty draft storage
    useAppStore.getState().openDraftWorkspaceTab();
    expect(useAppStore.getState().activeTabId).toBe(DRAFT_TAB_ID);
    useAppStore.getState().closeWorkspaceTab(DRAFT_TAB_ID);
    expect(confirmSpy).not.toHaveBeenCalled();
    expect(historyStore.readDraftText()).toBe("");
    expect(useAppStore.getState().activeTabId).toBe(tabAId);
    expect(useAppStore.getState().workspaceTabs.map((t) => t.id)).toEqual([tabAId]);

    // 3. Draft tab with unsent text closes without confirmation and preserves draft text
    const draftPrompt = "Cho hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác vuông.";
    useAppStore.getState().openDraftWorkspaceTab();
    useAppStore.getState().setProblemText(draftPrompt);
    expect(historyStore.readDraftText()).toBe(draftPrompt);

    // Switch back to tab A, then close background draft tab
    useAppStore.getState().activateWorkspaceTab(tabAId);
    useAppStore.getState().closeWorkspaceTab(DRAFT_TAB_ID);
    expect(confirmSpy).not.toHaveBeenCalled();
    expect(useAppStore.getState().activeTabId).toBe(tabAId);
    expect(historyStore.readDraftText()).toBe(draftPrompt);
    expect(useToastStore.getState().toasts).toHaveLength(0);

    // Preserved state on open tab A stays intact
    const curTabA = useAppStore.getState().workspaceTabs.find((t) => t.id === tabAId)!;
    expect(curTabA.active?.state).toBe(tabAStateRef);
    expect((curTabA.active?.state as Record<string, unknown>).__tabLifecycleMarker).toBe(
      "camera-step-3-preserved",
    );

    // 4. Reopening draft tab via + (openDraftWorkspaceTab) restores preserved draft text
    useAppStore.getState().openDraftWorkspaceTab();
    expect(useAppStore.getState().activeTabId).toBe(DRAFT_TAB_ID);
    expect(useAppStore.getState().problemText).toBe(draftPrompt);

    // 5. Explicit new problem clears draft cleanly so brand-new problem is not prefilled
    useAppStore.getState().closeWorkspaceTab(DRAFT_TAB_ID);
    useAppStore.getState().setProblemText("");
    historyStore.clearDraftText();
    clearSavedDraftAttachments();
    useAppStore.getState().goHome();
    expect(useAppStore.getState().problemText).toBe("");
    expect(historyStore.readDraftText()).toBe("");

    // 6. Active vs inactive close, last tab fallback (Home vs Library), and zero duplicate tabs on reopen
    useAppStore.getState().loadEnvelope(cloneEnvelope(sampleA.envelope), sampleA.id);
    useAppStore.getState().loadEnvelope(cloneEnvelope(sampleB.envelope), sampleB.id);
    const tabBId = `tab-sample-${sampleB.id}`;
    expect(useAppStore.getState().workspaceTabs).toHaveLength(2);
    expect(useAppStore.getState().activeTabId).toBe(tabBId);

    // Close active tab B -> deterministically activates neighbor A without resetting A
    useAppStore.getState().closeWorkspaceTab(tabBId);
    expect(useAppStore.getState().activeTabId).toBe(tabAId);
    expect(useAppStore.getState().view).toBe("workspace");

    // Reopen closed B -> single tab B added (no duplicates)
    useAppStore.getState().loadEnvelope(cloneEnvelope(sampleB.envelope), sampleB.id);
    expect(useAppStore.getState().workspaceTabs.filter((t) => t.id === tabBId)).toHaveLength(1);

    // Close inactive tab A while B is active -> B remains active
    useAppStore.getState().closeWorkspaceTab(tabAId);
    expect(useAppStore.getState().activeTabId).toBe(tabBId);
    expect(useAppStore.getState().workspaceTabs.map((t) => t.id)).toEqual([tabBId]);

    // Close Library while open vs close last simulation tab when Library closed -> Home
    useAppStore.getState().openLibrary();
    useAppStore.getState().closeWorkspaceTab(tabBId);
    expect(useAppStore.getState().view).toBe("library");
    useAppStore.getState().closeWorkspaceTab(LIBRARY_TAB_ID);
    expect(useAppStore.getState().view).toBe("home");

    // 7. Rapid open/close loop stays clean
    for (let i = 0; i < 10; i += 1) {
      useAppStore.getState().openDraftWorkspaceTab();
      useAppStore.getState().setProblemText(i % 2 === 0 ? "" : `Nháp nhanh ${i}`);
      useAppStore.getState().closeWorkspaceTab(DRAFT_TAB_ID);
    }
    expect(useAppStore.getState().workspaceTabs).toHaveLength(0);
    expect(useAppStore.getState().view).toBe("home");
    expect(confirmSpy).not.toHaveBeenCalled();
  });

  it("prevents stale in-flight composer completion from recreating a closed draft tab or disturbing other tabs", async () => {
    const store = useAppStore.getState();
    store.loadEnvelope(cloneEnvelope(sampleA.envelope), sampleA.id);
    const tabAId = useAppStore.getState().activeTabId!;

    useAppStore.getState().openDraftWorkspaceTab();
    useAppStore.getState().setProblemText("Cho hình chóp S.ABC có SA vuông góc (ABC).");

    const lockRef = { current: false };
    const abortRef = { current: null as AbortController | null };
    const reqRef = { current: null as string | null };

    let resolveLate!: (val: SimulationEnvelope) => void;
    // Simulate a backend call that resolves late (even ignoring AbortSignal) after draft tab was closed
    const analyzeFn = vi.fn().mockImplementationOnce(
      () =>
        new Promise<SimulationEnvelope>((resolve) => {
          resolveLate = resolve;
        }),
    );

    const submitPromise = runComposerSubmit({
      canSubmit: true,
      lockRef,
      abortRef,
      requestIdRef: reqRef,
      problemText: useAppStore.getState().problemText,
      health: { ok: true, hasKey: true, cachedProblems: 0 },
      analyzeFn,
    });

    // Close the processing draft tab immediately before response arrives -> returns cleanly to tab A
    useAppStore.getState().closeWorkspaceTab(DRAFT_TAB_ID);
    expect(useAppStore.getState().activeTabId).toBe(tabAId);
    expect(useAppStore.getState().workspaceTabs.some((t) => t.id === DRAFT_TAB_ID)).toBe(false);

    resolveLate(cloneEnvelope(sampleB.envelope));
    await submitPromise;

    const after = useAppStore.getState();
    expect(after.activeTabId).toBe(tabAId);
    expect(after.workspaceTabs.map((t) => t.id)).toEqual([tabAId]);
    expect(Object.keys(after.problemProcessingRecords)).toHaveLength(0);
    expect(after.analyzing).toBe(false);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it(
    "live Chromium click flow: closes empty, text-draft, and attachment-draft tabs with 0 confirms, restores File + blob URL on draft reopen, and clears on explicit New Problem",
    async () => {
      const harnessCode = `
        import React, { StrictMode } from "react";
        import { createRoot } from "react-dom/client";
        import App from "./App";
        import { registerAllSimulations } from "./simulations";
        import { useAuthStore } from "./state/auth";
        import { useAppStore } from "./state/store";

        window.__axoConfirmCount = 0;
        window.confirm = () => {
          window.__axoConfirmCount += 1;
          return false;
        };

        registerAllSimulations();
        useAuthStore.setState({ user: null, resolved: true });
        useAppStore.getState().setGuestEnteredApp(true);
        window.__axoStore = useAppStore;

        createRoot(document.getElementById("root")).render(
          React.createElement(StrictMode, null, React.createElement(App)),
        );
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
      const htmlDoc = `<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8" /><style>${tokensCss}\n${globalCss}\nhtml, body { margin: 0; }</style></head><body><div id="root"></div><script type="module" src="/bundle.js"></script></body></html>`;

      const browser = await chromium.launch({
        headless: true,
        args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
      });
      try {
        const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
        let nativeDialogCount = 0;
        const pageErrors: string[] = [];
        page.on("dialog", async (d) => {
          nativeDialogCount += 1;
          await d.dismiss();
        });
        page.on("pageerror", (e) => pageErrors.push(e.message));

        await page.route("http://axo.test/**", async (route) => {
          const url = route.request().url();
          if (url === "http://axo.test/bundle.js") {
            await route.fulfill({ status: 200, contentType: "application/javascript; charset=utf-8", body: bundleJs });
          } else if (url.includes("/api/auth/")) {
            await route.fulfill({ status: 200, contentType: "application/json", body: '{"user":null}' });
          } else if (url.includes("/api/health")) {
            await route.fulfill({ status: 200, contentType: "application/json", body: '{"ok":true,"hasKey":false}' });
          } else if (url.includes("/api/analyze")) {
            await route.abort();
          } else {
            await route.fulfill({ status: 200, contentType: "text/html; charset=utf-8", body: htmlDoc });
          }
        });

        await page.goto("http://axo.test/app", { waitUntil: "domcontentloaded" });
        await page.waitForSelector("#nav-item-library", { timeout: 10000 });
        await page.locator("#nav-item-library").click();
        await page.waitForSelector(".lib-card", { timeout: 10000 });
        await page.locator(".lib-card").first().click();
        await page.waitForSelector('[data-close-tab^="tab-sample-"]', { timeout: 10000 });

        // 1. Open draft tab via +, type text, attach a real PNG file
        await page.locator("#btn-header-change-prob").click();
        await page.waitForSelector("#composer-input, #home-problem-input", { timeout: 5000 });
        const draftInput = page.locator("#composer-input, #home-problem-input").first();
        await draftInput.fill("Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2a.");

        // 1x1 valid transparent PNG buffer
        const pngBase64 =
          "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";
        await page.locator("#home-file-input").setInputFiles({
          name: "de-hinh-chop.png",
          mimeType: "image/png",
          buffer: Buffer.from(pngBase64, "base64"),
        });
        await page.waitForSelector('.file-preview-card[data-kind="image"]', { timeout: 5000 });
        const blobUrlBefore = await page
          .locator('.file-preview-card[data-kind="image"] img.composer-file-thumb')
          .getAttribute("src");
        expect(blobUrlBefore).toMatch(/^blob:/);

        // 2. Switch to simulation tab in LeftSidebar -> close [Bài toán mới ×] directly
        await page.locator("#left-sidebar .sb-problem-item").first().click();
        await page.waitForSelector('[data-close-tab="tab-draft-new"]', { timeout: 5000 });
        await page.locator('[data-close-tab="tab-draft-new"]').click();
        await page.waitForTimeout(100);

        expect(await page.locator('[data-tab-id="tab-draft-new"]').count()).toBe(0);
        expect(await page.evaluate(() => (window as unknown as { __axoConfirmCount: number }).__axoConfirmCount)).toBe(0);
        expect(nativeDialogCount).toBe(0);
        expect(await page.locator("text=Đã đóng tab").count()).toBe(0);

        // 3. Reopen + -> restores both unsent text AND attached image with valid blob preview URL!
        await page.locator("#btn-header-change-prob").click();
        await page.waitForSelector("#composer-input, #home-problem-input", { timeout: 5000 });
        expect(await page.locator("#composer-input, #home-problem-input").first().inputValue()).toBe(
          "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2a.",
        );
        await page.waitForSelector('.file-preview-card[data-kind="image"] img.composer-file-thumb', {
          timeout: 5000,
        });
        const imgRestoredOk = await page.evaluate(() => {
          const img = document.querySelector(
            '.file-preview-card[data-kind="image"] img.composer-file-thumb',
          ) as HTMLImageElement | null;
          return Boolean(img && img.src.startsWith("blob:") && img.alt.includes("de-hinh-chop.png"));
        });
        expect(imgRestoredOk).toBe(true);

        // 4. Explicit click on #nav-item-new-problem ("Bài toán mới") clears draft + attachments cleanly
        await page.locator("#nav-item-new-problem").click();
        await page.waitForSelector("#composer-input, #home-problem-input", { timeout: 5000 });
        expect(await page.locator("#composer-input, #home-problem-input").first().inputValue()).toBe("");
        expect(await page.locator(".file-preview-card").count()).toBe(0);
        expect(pageErrors).toEqual([]);
      } finally {
        await browser.close();
      }
    },
    35_000,
  );
});
