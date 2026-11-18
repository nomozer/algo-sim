import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import { analyzeViaServer } from "../../llm/client";
import { registerAllSimulations } from "../../simulations";
import { useAuthStore, type AuthUser } from "../../state/auth";
import {
  __resetHistoryForTest,
  HISTORY_ITEM_KEY_PREFIX,
  historyStore,
} from "../../state/history";
import {
  buildUnifiedProblemList,
  syncStoreFromStorageKey,
  useAppStore,
} from "../../state/store";
import { LeftSidebar } from "../LeftSidebar";
import {
  clearSavedDraftAttachments,
  executeScreenCaptureFlow,
  ProblemInput,
  runComposerSubmit,
  type ProblemInputProps,
} from "../ProblemInput";
import {
  captureScreenStillFrame,
  classifyScreenCaptureError,
  classifyScreenCaptureSupportError,
} from "../ScreenCaptureDialog";
import { ToastContainer, useToastStore } from "../TopNav";

registerAllSimulations();

type FixtureRow = {
  id: string;
  problem_text: string;
  response: Record<string, unknown> & { route_d?: { status?: string } };
};

const fixtureBundle = JSON.parse(
  readFileSync(
    resolve(
      __dirname,
      "../../../../docs/evaluation/geometry/runs/hybrid-master-backend-replacement/product-integration-frontend-fixtures.json",
    ),
    "utf8",
  ),
) as { fixtures: FixtureRow[] };

const servedFixture = fixtureBundle.fixtures.find(
  (f) => f.response.route_d?.status === "SERVED",
)!;

function syncStoresForSSR(user: AuthUser | null = null, resolved = true) {
  useAuthStore.setState({ user, resolved });
  Object.assign(useAuthStore.getInitialState(), { user, resolved });
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
  Object.assign(useToastStore.getInitialState(), useToastStore.getState());
}

function renderSidebarHtml(): string {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
  return renderToString(<LeftSidebar />);
}

function countRenderedProblemItems(sidebarHtml: string): number {
  return [...sidebarHtml.matchAll(/class="sb-problem-item(?:\s|")/g)].length;
}

describe("AXO V9.4.3 — Screen Capture UX, Conversation Lifecycle & Sidebar Refinement", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    clearSavedDraftAttachments();
    useToastStore.getState().clearToasts();
    useAppStore.getState().reset();
    useAppStore.getState().setGuestEnteredApp(true);
    syncStoresForSSR(null, true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    clearSavedDraftAttachments();
    useToastStore.getState().clearToasts();
    useAppStore.getState().reset();
    syncStoresForSSR(null, true);
  });

  describe("Phase 9.1 — Conversation Lifecycle (Tests 1–10)", () => {
    it("Test 1: Mở trang mới (/app) & nhấn nút điều hướng 'Bài toán mới' — không thêm item rỗng vào BÀI TOÁN", () => {
      const s = useAppStore.getState();
      const sidebarHtml = renderSidebarHtml();

      // Primary navigation button 'Bài toán mới' remains intact
      expect(sidebarHtml).toContain('id="nav-item-new-problem"');
      // BÀI TOÁN problem list has 0 items
      expect(countRenderedProblemItems(sidebarHtml)).toBe(0);
      expect(sidebarHtml).toContain("Chưa có bài toán nào.");

      // Even if a draft workspace tab ('tab-draft-new') was opened internally, filter='all' never shows it
      s.openDraftWorkspaceTab();
      const listAll = buildUnifiedProblemList({
        effectiveTabs: useAppStore.getState().workspaceTabs,
        effectiveActiveTabId: useAppStore.getState().activeTabId,
        view: useAppStore.getState().view,
        history: useAppStore.getState().history,
        filter: "all",
        processingRecords: useAppStore.getState().problemProcessingRecords,
        analyzing: useAppStore.getState().analyzing,
        activeProblemText: useAppStore.getState().problemText,
      });
      expect(listAll).toHaveLength(0);
      expect(countRenderedProblemItems(renderSidebarHtml())).toBe(0);
    });

    it("Test 2: Focus Composer — không tạo bản ghi lịch sử hay item trong BÀI TOÁN", () => {
      const composerHtml = renderToString(<ProblemInput />);
      expect(composerHtml).toContain('id="home-problem-input"');
      expect(historyStore.list()).toHaveLength(0);
      expect(useAppStore.getState().history).toHaveLength(0);
      expect(countRenderedProblemItems(renderSidebarHtml())).toBe(0);
    });

    it("Test 3: Nhập nội dung đề toán (DRAFT) — lưu nháp văn bản nhưng không thêm item vào BÀI TOÁN", () => {
      useAppStore
        .getState()
        .setProblemText("Cho hình chóp S.ABCD có đáy là hình vuông cạnh a.");
      historyStore.writeDraftText(useAppStore.getState().problemText);
      expect(useAppStore.getState().problemText).toContain("Cho hình chóp S.ABCD");
      expect(historyStore.readDraftText()).toContain("Cho hình chóp S.ABCD");
      expect(historyStore.list()).toHaveLength(0);
      expect(countRenderedProblemItems(renderSidebarHtml())).toBe(0);
    });

    it("Test 4: Đính kèm tệp trước khi gửi — tạo chip đính kèm cục bộ, không thêm item vào BÀI TOÁN", () => {
      const file = new File([new Uint8Array([1, 2, 3, 4])], "de-toan.png", {
        type: "image/png",
      });
      const attachment: NonNullable<ProblemInputProps["initialAttachments"]>[number] = {
        id: "att-draft-1",
        file,
        name: "de-toan.png",
        size: 4,
        sizeFormatted: "4 B",
        ext: "png",
        kind: "image",
        status: "ready",
      };
      const composerHtml = renderToString(<ProblemInput initialAttachments={[attachment]} />);
      expect(composerHtml).toContain("de-toan.png");
      expect(historyStore.list()).toHaveLength(0);
      expect(countRenderedProblemItems(renderSidebarHtml())).toBe(0);
    });

    it("Test 5 & 6: Submit (PROCESSING) không tạo bài toán hoàn thành giả; khi Backend trả READY mới thêm đúng 1 item hợp lệ có ID ổn định, title và icon nhóm hình học", async () => {
      let resolveFetch!: (res: Response) => void;
      vi.spyOn(globalThis, "fetch").mockImplementation(
        () =>
          new Promise<Response>((resolve) => {
            resolveFetch = resolve;
          }),
      );

      const requestIdRef = { current: null as string | null };
      const submitPromise = runComposerSubmit({
        canSubmit: true,
        lockRef: { current: false },
        requestIdRef,
        problemText: servedFixture.problem_text,
        attachment: null,
        health: null,
        analyzeFn: (p, sig, _r, id) =>
          analyzeViaServer(p, sig, { maxRetries: 0, baseDelayMs: 1 }, id),
      });

      // Wait a microtask so runComposerSubmit enters PROCESSING
      await Promise.resolve();
      expect(useAppStore.getState().analyzing).toBe(true);
      // During PROCESSING, BÀI TOÁN ('all') has 0 fake completed items
      expect(countRenderedProblemItems(renderSidebarHtml())).toBe(0);
      expect(historyStore.list()).toHaveLength(0);

      // Backend completes with valid READY response
      resolveFetch(
        new Response(JSON.stringify(servedFixture.response), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
      await submitPromise;

      expect(useAppStore.getState().analyzing).toBe(false);
      expect(historyStore.list()).toHaveLength(1);

      const sidebarAfterReady = renderSidebarHtml();
      expect(countRenderedProblemItems(sidebarAfterReady)).toBe(1);
      expect(sidebarAfterReady).not.toMatch(/class="sb-item-title"[^>]*>Bài toán mới<\/span>/u);
      expect(sidebarAfterReady).toContain('data-geometry-family=');

      const readyId = useAppStore.getState().activeHistoryId!;
      expect(readyId).toMatch(/^a[0-9a-f]{32}$/u);
    });

    it("Test 7 & 8: Processing failed (NEEDS_ATTENTION) không hiển thị như READY, giữ nguyên nội dung để retry, và Retry không tạo duplicate item", async () => {
      let attemptCalls = 0;
      vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
        attemptCalls += 1;
        if (attemptCalls === 1) {
          return new Response(
            JSON.stringify({ detail: "Dịch vụ tạm thời gián đoạn" }),
            { status: 503, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response(JSON.stringify(servedFixture.response), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      });

      useAppStore.getState().setProblemText(servedFixture.problem_text);
      const requestIdRef = { current: null as string | null };
      const lockRef = { current: false };

      // 1st send fails (503)
      await runComposerSubmit({
        canSubmit: true,
        lockRef,
        requestIdRef,
        problemText: useAppStore.getState().problemText,
        attachment: null,
        health: null,
        analyzeFn: (p, sig, _r, id) =>
          analyzeViaServer(p, sig, { maxRetries: 0, baseDelayMs: 1 }, id),
      });

      const firstAttemptId = requestIdRef.current!;
      expect(firstAttemptId).toMatch(/^a[0-9a-f]{32}$/u);
      // Failed attempt is NOT shown in BÀI TOÁN ('all') as a completed problem
      expect(countRenderedProblemItems(renderSidebarHtml())).toBe(0);
      expect(historyStore.list()).toHaveLength(0);
      // Input text is preserved for retry
      expect(useAppStore.getState().problemText).toBe(servedFixture.problem_text);
      // Internal needs_attention record has only 1 entry
      expect(Object.keys(useAppStore.getState().problemProcessingRecords)).toEqual([
        firstAttemptId,
      ]);

      // 2nd send (Retry) succeeds -> reuses attempt ID, clears failed record, saves exactly 1 READY item
      await runComposerSubmit({
        canSubmit: true,
        lockRef,
        requestIdRef,
        problemText: useAppStore.getState().problemText,
        attachment: null,
        health: null,
        analyzeFn: (p, sig, _r, id) =>
          analyzeViaServer(p, sig, { maxRetries: 0, baseDelayMs: 1 }, id),
      });

      expect(historyStore.list()).toHaveLength(1);
      expect(historyStore.list()[0].id).toBe(firstAttemptId);
      expect(Object.keys(useAppStore.getState().problemProcessingRecords)).toHaveLength(0);
      expect(countRenderedProblemItems(renderSidebarHtml())).toBe(1);
    });

    it("Test 9 & 10: Reload và đồng bộ nhiều tab (syncStoreFromStorageKey) giữ nguyên bài toán READY, không tái tạo placeholder rỗng và không nhân đôi cùng một ID", async () => {
      vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
        new Response(JSON.stringify(servedFixture.response), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );

      await runComposerSubmit({
        canSubmit: true,
        lockRef: { current: false },
        problemText: servedFixture.problem_text,
        attachment: null,
        health: null,
        analyzeFn: (p, sig, _r, id) =>
          analyzeViaServer(p, sig, { maxRetries: 0, baseDelayMs: 1 }, id),
      });

      const savedItems = historyStore.list();
      expect(savedItems).toHaveLength(1);
      const savedId = savedItems[0].id;

      // Simulate reload into fresh Zustand state reading from persisted historyStore
      useAppStore.setState({
        history: historyStore.list(),
        workspaceTabs: [],
        activeTabId: null,
        problemProcessingRecords: {},
      });
      const reloadedHtml = renderSidebarHtml();
      expect(countRenderedProblemItems(reloadedHtml)).toBe(1);
      expect(reloadedHtml).not.toMatch(/class="sb-item-title"[^>]*>Bài toán mới<\/span>/u);

      // Simulate cross-tab storage event firing multiple times for the same key
      syncStoreFromStorageKey(`${HISTORY_ITEM_KEY_PREFIX}${savedId}`);
      syncStoreFromStorageKey(`${HISTORY_ITEM_KEY_PREFIX}${savedId}`);
      const afterMultiTabSync = useAppStore.getState().history;
      expect(afterMultiTabSync.map((h) => h.id)).toEqual([savedId]);
      expect(countRenderedProblemItems(renderSidebarHtml())).toBe(1);
    });
  });

  describe("Phase 9.2 — Screen Capture UX (Voluntary Cancel, Toast Notices, Preview & Retake)", () => {
    it("Case A (Voluntary Cancel): đóng im lặng — không mở modal, không bật toast thừa, giữ nguyên nội dung Composer và không tạo bài toán", async () => {
      useAppStore.getState().setProblemText("Đề bài đang gõ dở");
      const busyRef = { current: false };

      for (const cancelErr of [
        { name: "AbortError", message: "User cancelled" },
        { name: "NotAllowedError", message: "Permission denied" },
        { name: "NotAllowedError", message: "Permission denied by user" },
      ]) {
        const outcome = await executeScreenCaptureFlow({
          busyRef,
          onCaptured: () => { throw new Error("unexpected capture"); },
          checkSupport: () => null,
          captureFrame: async () => {
            throw cancelErr;
          },
        });
        expect(outcome).toBe("cancelled");
        expect(useToastStore.getState().toasts).toHaveLength(0);
      }

      expect(useAppStore.getState().problemText).toBe("Đề bài đang gõ dở");
      expect(historyStore.list()).toHaveLength(0);
      expect(useAppStore.getState().analyzing).toBe(false);
    });

    it("Case B & C (Unsupported API & System Permission / Read Error): hiển thị thông báo Light Mode ngắn gọn qua ToastContainer, không mở modal lớn và không lộ stack trace", async () => {
      const busyRef = { current: false };

      // Case B: Browser Unsupported
      const unsupportedOutcome = await executeScreenCaptureFlow({
        busyRef,
        onCaptured: () => { throw new Error("unexpected capture"); },
        checkSupport: () =>
          classifyScreenCaptureSupportError({
            isSecureContext: true,
            hasDisplayMedia: false,
          }),
      });
      expect(unsupportedOutcome).toBe("unsupported");
      expect(useToastStore.getState().toasts).toHaveLength(1);
      expect(useToastStore.getState().toasts[0].tone).toBe("info");
      expect(useToastStore.getState().toasts[0].title).toContain(
        "chưa hỗ trợ chụp màn hình",
      );

      syncStoresForSSR();
      const toastHtml = renderToString(<ToastContainer />);
      expect(toastHtml).toContain('class="axo-composer-toast visible"');
      expect(toastHtml).toContain('role="status"');
      expect(toastHtml).not.toContain("screen-capture-backdrop");

      // Case C: OS/System Permission Block or SecurityError — neutral message, never accusing permanent user block
      const sysErrOutcome = await executeScreenCaptureFlow({
        busyRef,
        onCaptured: () => { throw new Error("unexpected capture"); },
        checkSupport: () => null,
        captureFrame: async () => {
          throw Object.assign(new Error("Permission denied by system"), {
            name: "NotAllowedError",
          });
        },
      });
      expect(sysErrOutcome).toBe("error");
      const activeToast = useToastStore.getState().toasts[0];
      expect(activeToast.tone).toBe("info");
      expect(activeToast.title).toBe("Chưa có quyền chia sẻ màn hình");
      expect(activeToast.description).not.toMatch(
        /vĩnh viễn|NotAllowedError|Permission denied by system/i,
      );
    });

    it("Case D: chụp liên tiếp đính kèm từng ảnh và giải phóng track", async () => {
      const attached: File[] = [];
      const revoked: string[] = [];
      const stop = vi.fn();
      const captureFrame = () => captureScreenStillFrame({
        isSecureContext: true,
        getDisplayMedia: async () => ({ getTracks: () => [{ stop }] } as unknown as MediaStream),
        createObjectURL: () => "blob:temporary",
        extractFrameFromStream: async () => ({ blob: new Blob(["image"], { type: "image/png" }), width: 10, height: 10 }),
      });
      for (let i = 0; i < 2; i++) {
        expect(await executeScreenCaptureFlow({ busyRef: { current: false }, onCaptured: file => attached.push(file), checkSupport: () => null, captureFrame, revokeUrl: url => { if (url) revoked.push(url); } })).toBe("attached");
      }
      expect(attached).toHaveLength(2);
      expect(stop).toHaveBeenCalledTimes(2);
      expect(revoked).toEqual(["blob:temporary", "blob:temporary"]);
      expect(useAppStore.getState().analyzing).toBe(false);
    });

  });

  describe("Phase 9.3 & 10 — Sidebar Layout, Navigation Hygiene & CSS Root-Cause Checks", () => {
    it("Giữ đúng cấu trúc điều hướng (không có Lịch sử hay Lớp học), bảo toàn icon nhóm hình học và không dùng display:none để giấu bài toán rỗng", () => {
      const sidebarHtml = renderSidebarHtml();
      expect(sidebarHtml).toContain("Bài toán mới");
      expect(sidebarHtml).toContain("Thư viện mô phỏng");
      expect(sidebarHtml).toContain('<span class="sb-group-title">Bài toán</span>');
      expect(sidebarHtml).not.toContain(">Lịch sử<");
      expect(sidebarHtml).not.toContain("Lớp học");
      expect(sidebarHtml).not.toContain("Bài thực hành");
      expect(sidebarHtml).not.toContain("Theo dõi lớp");

      const css = readFileSync(
        new URL("../../styles/global.css", import.meta.url),
        "utf8",
      );
      // Dead error-modal rules removed cleanly
      expect(css).not.toContain(".screen-capture-error-box");
      expect(css).not.toContain(".screen-capture-error-desc");
      // Hover trailing action uses absolute overlay on hover-capable pointers so .sb-item-title gets full row width without layout shift
      expect(css).toContain("@media (hover: hover) and (pointer: fine)");
      expect(css).toContain("@media (hover: none), (pointer: coarse), (max-width: 767px)");
      // Classify error still covers all categories cleanly
      expect(classifyScreenCaptureError({ name: "AbortError" }).code).toBe("cancelled");
    });
  });
});
