import { readFileSync } from "node:fs";
import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import {
  AdminAccountsPaginationBar,
  AdminWorkspaceView,
  buildAdminPaginationItems,
  computeAdminPagination,
  type AdminUserItem,
} from "./AuthGate";
import { useAuthStore } from "../state/auth";
import { useAppStore } from "../state/store";

function makeUsers(count: number): AdminUserItem[] {
  return Array.from({ length: count }, (_, idx) => {
    const id = idx + 1;
    return {
      id,
      name: `Học sinh ${id}`,
      email: `hs${id}@axo.edu.vn`,
      role: "student",
      status: "active",
      school: "THPT Chu Văn An",
      joinedAt: "30/10/2026",
      joinedTs: 1761800000000 + id,
      dailyLimit: 15,
      tokenCap: 45000,
      usedToday: 0,
      tokensToday: "Chưa đo token",
    };
  });
}

describe("Admin Accounts Pagination — V2.7 Parity & 10 Mandatory Edge Cases", () => {
  beforeEach(() => {
    useAppStore.getState().reset();
    useAuthStore.setState({
      user: {
        id: 1,
        email: "admin@axo.edu.vn",
        displayName: "Quản trị viên Axo",
        role: "admin",
        mustChangePassword: false,
      },
      resolved: true,
      busy: false,
      error: null,
      authGate: null,
    });
    Object.assign(useAppStore.getInitialState(), useAppStore.getState());
    Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
  });

  it("hides #admin-page-nav-group completely when totalPages <= 1 (0, 1, 3, and 10 accounts at 10/page) with no placeholder", () => {
    for (const count of [0, 1, 3, 10]) {
      const html = renderToString(
        <AdminWorkspaceView initialTab="accounts" initialUsersFixture={makeUsers(count)} />,
      ).replace(/<!--\s*-->/g, "");
      expect(html).toContain('id="admin-accounts-pagination"');
      expect(html).toContain('id="admin-pagination-summary"');
      expect(html).toContain('id="admin-page-size-select"');
      expect(html).toContain("Số dòng mỗi trang:");
      expect(html).toContain("10 / trang");
      expect(html).not.toContain('id="admin-page-nav-group"');
      expect(html).not.toContain('id="btn-page-prev"');
      expect(html).not.toContain('id="btn-page-next"');

      if (count === 0) {
        expect(html).toContain("Hiển thị 0 tài khoản");
      } else {
        expect(html).toContain(`1–${count}`);
        expect(html).toContain(`trong tổng số`);
        expect(html).not.toContain("Trang 1/1");
      }
    }
  });

  it("shows navigation cluster when totalPages >= 2 (11 accounts at 10/page) with active state and disabled Prev", () => {
    const html = renderToString(
      <AdminWorkspaceView initialTab="accounts" initialUsersFixture={makeUsers(11)} />,
    ).replace(/<!--\s*-->/g, "");
    expect(html).toContain('id="admin-page-nav-group"');
    expect(html).toContain('id="btn-page-prev"');
    expect(html).toContain('id="btn-page-next"');
    expect(html).toContain('data-page-num="1"');
    expect(html).toContain('data-page-num="2"');
    expect(html).not.toContain('data-page-num="3"');
    expect(html).toContain("Trang");
    expect(html).toContain("1/2");
  });

  it("computes exact pagination math and auto-clamps out-of-range currentPage across all boundary transitions", () => {
    // Case 1: 0 items
    expect(computeAdminPagination(0, 10, 1)).toEqual({
      totalItems: 0,
      pageSize: 10,
      totalPages: 1,
      safePage: 1,
      startIndex: 0,
      endIndex: 0,
      hasMultiplePages: false,
    });

    // Case 2: 1 item
    expect(computeAdminPagination(1, 10, 1)).toEqual({
      totalItems: 1,
      pageSize: 10,
      totalPages: 1,
      safePage: 1,
      startIndex: 0,
      endIndex: 1,
      hasMultiplePages: false,
    });

    // Case 3: exact 10 items
    expect(computeAdminPagination(10, 10, 1)).toEqual({
      totalItems: 10,
      pageSize: 10,
      totalPages: 1,
      safePage: 1,
      startIndex: 0,
      endIndex: 10,
      hasMultiplePages: false,
    });

    // Case 4: 11 items on page 2
    expect(computeAdminPagination(11, 10, 2)).toEqual({
      totalItems: 11,
      pageSize: 10,
      totalPages: 2,
      safePage: 2,
      startIndex: 10,
      endIndex: 11,
      hasMultiplePages: true,
    });

    // Case 6/7/8: deleting last item on page 2 (11 -> 10 items) or search reducing pages clamps safePage 2 -> 1
    expect(computeAdminPagination(10, 10, 2)).toEqual({
      totalItems: 10,
      pageSize: 10,
      totalPages: 1,
      safePage: 1,
      startIndex: 0,
      endIndex: 10,
      hasMultiplePages: false,
    });

    // Changing pageSize 10 -> 20 with 15 items collapses to 1 page
    expect(computeAdminPagination(15, 20, 2)).toEqual({
      totalItems: 15,
      pageSize: 20,
      totalPages: 1,
      safePage: 1,
      startIndex: 0,
      endIndex: 15,
      hasMultiplePages: false,
    });
  });

  it("builds full page numbers for small page counts (<= 7) and non-button ellipsis truncation for many pages (e.g. 9/18)", () => {
    expect(buildAdminPaginationItems(1, 1)).toEqual([]);
    expect(buildAdminPaginationItems(5, 3)).toEqual([
      { type: "page", page: 1 },
      { type: "page", page: 2 },
      { type: "page", page: 3 },
      { type: "page", page: 4 },
      { type: "page", page: 5 },
    ]);
    expect(buildAdminPaginationItems(7, 4).map((x) => (x.type === "page" ? x.page : "…"))).toEqual([
      1, 2, 3, 4, 5, 6, 7,
    ]);

    // Exact Owner spec at 9/18: 1 | … | 8 | 9 | 10 | … | 18
    expect(buildAdminPaginationItems(18, 9).map((x) => (x.type === "page" ? x.page : "…"))).toEqual([
      1,
      "…",
      8,
      9,
      10,
      "…",
      18,
    ]);

    // Never emit ellipsis for a single missing page (e.g. page 4/18 -> 1 | 2 | 3 | 4 | 5 | … | 18)
    expect(buildAdminPaginationItems(18, 4).map((x) => (x.type === "page" ? x.page : "…"))).toEqual([
      1,
      2,
      3,
      4,
      5,
      "…",
      18,
    ]);

    // Render 9/18 via AdminAccountsPaginationBar and verify `…` is a non-interactive span, never a button
    const barHtml = renderToString(
      <AdminAccountsPaginationBar
        totalItems={180}
        pageSize={10}
        currentPage={9}
        pageSizeOpen={false}
        onTogglePageSize={() => {}}
        onSelectPageSize={() => {}}
        onPageChange={() => {}}
      />,
    ).replace(/<!--\s*-->/g, "");
    expect(barHtml).toContain("81–90");
    expect(barHtml).toContain("9/18");
    expect(barHtml).toContain('class="admin-page-ellipsis"');
    expect(barHtml).toContain('aria-hidden="true"');
    expect(barHtml).not.toMatch(/<button[^>]*>…<\/button>/);
    expect(barHtml).toContain('data-page-num="9"');
    expect(barHtml).toContain('aria-current="page"');
  });

  it("preserves V2.7 active hover protection (:not(.is-current)) in global.css", () => {
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf-8");
    expect(css).not.toMatch(/\.btn-page-nav:hover:not\(:disabled\)\s*\{/);
    expect(css).toContain(".btn-page-nav:hover:not(:disabled):not(.is-current)");
  });
});
