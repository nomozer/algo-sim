import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { publicCatalog } from "../../data/offline-catalog";
import { registerAllSimulations } from "../../simulations";
import { useAuthStore } from "../../state/auth";
import { __resetHistoryForTest } from "../../state/history";
import { useAppStore } from "../../state/store";
import { LeftSidebar } from "../LeftSidebar";

registerAllSimulations();

const globalCss = readFileSync(
  resolve(__dirname, "../../styles/global.css"),
  "utf8",
);

function syncAuthAndStore(authResolved: boolean) {
  useAuthStore.setState({ user: null, resolved: authResolved });
  Object.assign(useAuthStore.getInitialState(), { user: null, resolved: authResolved });
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
}

describe("LeftSidebar Problem List States (Loading / Empty / Populated / Filtered)", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
    useAppStore.setState({
      view: "home",
      active: null,
      activeSampleId: null,
      activeHistoryId: null,
      workspaceTabs: [],
      activeTabId: null,
      history: [],
      problemProcessingRecords: {},
      leftRailProblemFilter: "all",
      leftRailProblemGroupCollapsed: false,
      analyzing: false,
    });
  });

  afterEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
    useAppStore.setState({
      workspaceTabs: [],
      activeTabId: null,
      history: [],
      problemProcessingRecords: {},
      leftRailProblemFilter: "all",
      analyzing: false,
    });
    syncAuthAndStore(true);
  });

  it("1. renders calm loading state #sb-problem-loading when auth is unresolved and list is empty", () => {
    syncAuthAndStore(false);
    const html = renderToString(<LeftSidebar />);
    expect(html).toContain('id="sb-problem-loading"');
    expect(html).toContain('data-empty-kind="loading"');
    expect(html).toContain("Đang tải danh sách…");
    expect(html).not.toContain('id="sb-problem-empty"');
    expect(html).not.toContain("sb-empty-cta");
  });

  it("2. renders clean genuine empty state without duplicate '+ Mở bài toán mới' CTA or .sb-empty-cta CSS", () => {
    syncAuthAndStore(true);
    const html = renderToString(<LeftSidebar />);
    expect(html).toContain('id="sb-problem-empty"');
    expect(html).toContain('data-empty-kind="empty"');
    expect(html).toContain("Chưa có bài toán nào.");
    expect(html).not.toContain("sb-empty-cta");
    expect(html).not.toContain("+ Mở bài toán mới");
    expect(globalCss).not.toContain(".sb-empty-cta");
  });

  it("3. renders populated problem list without empty or loading placeholders", () => {
    const sample = publicCatalog()[0]!;
    useAppStore
      .getState()
      .loadEnvelope(sample.envelope, sample.id, sample.envelope.description ?? undefined);
    syncAuthAndStore(true);
    const html = renderToString(<LeftSidebar />);
    expect(html).toContain("sb-problem-item");
    expect(html).not.toContain('id="sb-problem-empty"');
    expect(html).not.toContain('id="sb-problem-loading"');
  });

  it.each([
    ["needs_attention", "Không có bài toán nào Cần chú ý."],
    ["in_progress", "Không có bài toán nào Đang tiến hành."],
    ["ready", "Chưa có bài toán nào ở trạng thái Sẵn sàng."],
  ] as const)(
    "4-6. renders filtered empty copy for %s filter without duplicate CTA",
    (filter, expectedCopy) => {
      if (filter === "ready") {
        useAppStore.setState({
          problemProcessingRecords: {
            "attempt-in-progress-test": {
              canonicalId: "attempt-in-progress-test",
              title: "Hình chóp đang xử lý",
              problemStatement: "Cho hình chóp S.ABCD",
              status: "in_progress",
              createdAt: 1,
              updatedAt: 1,
            },
          },
          leftRailProblemFilter: "ready",
        });
      } else {
        const sample = publicCatalog()[0]!;
        useAppStore
          .getState()
          .loadEnvelope(sample.envelope, sample.id, sample.envelope.description ?? undefined);
        useAppStore.setState({ leftRailProblemFilter: filter });
      }
      syncAuthAndStore(true);
      const html = renderToString(<LeftSidebar />);
      expect(html).toContain('id="sb-problem-empty"');
      expect(html).toContain('data-empty-kind="filtered"');
      expect(html).toContain(expectedCopy);
      expect(html).not.toContain("sb-empty-cta");
      expect(html).not.toContain("+ Mở bài toán mới");
    },
  );

  it("7. keeps the primary top '#nav-item-new-problem' creation button intact", () => {
    syncAuthAndStore(true);
    const html = renderToString(<LeftSidebar />);
    expect(html).toContain('id="nav-item-new-problem"');
    expect(html).toContain("Bài toán mới");
  });
});
