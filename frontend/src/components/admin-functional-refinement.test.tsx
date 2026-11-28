import { readFileSync } from "node:fs";
import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import {
  AdminWorkspaceView,
  foldAdminSearchText,
  getConfirmModalSpec,
  type AdminUserItem,
} from "./AdminWorkspaceView";
import { useAuthStore } from "../state/auth";
import { useAppStore } from "../state/store";

function makeSampleUsers(): AdminUserItem[] {
  return [
    {
      id: 1,
      name: "Quản trị Hệ thống",
      email: "admin@example.test",
      username: "admin",
      emailVerified: true,
      role: "admin",
      status: "active",
      school: "Hệ thống Axo",
      joinedAt: "28/11/2026",
      joinedTs: 1764288000000,
      dailyLimit: 500,
      tokenCap: 500000,
      usedToday: 0,
      tokensToday: "Chưa đo token",
    },
    {
      id: 2,
      name: "Phạm Gia Hân",
      email: "user.han99@example.test",
      username: null,
      emailVerified: false,
      role: "student",
      status: "pending_activation",
      school: "THPT Bùi Thị Xuân",
      joinedAt: "27/11/2026",
      joinedTs: 1764201600000,
      dailyLimit: 15,
      tokenCap: 45000,
      usedToday: 3,
      tokensToday: "Chưa đo token",
    },
    {
      id: 3,
      name: "Nguyễn Văn Khôi",
      email: "khoi@example.test",
      username: null,
      emailVerified: true,
      role: "student",
      status: "active",
      school: "THPT Chu Văn An",
      joinedAt: "26/11/2026",
      joinedTs: 1764115200000,
      dailyLimit: 15,
      tokenCap: 45000,
      usedToday: 2,
      tokensToday: "Chưa đo token",
    },
  ];
}

describe("AdminWorkspaceView — Functional Refinement & Honesty Gates", () => {
  beforeEach(() => {
    useAppStore.getState().reset();
    useAuthStore.setState({
      user: {
        id: 1,
        email: "admin@example.test",
        displayName: "Quản trị Hệ thống",
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

  it("folds Vietnamese diacritics and letter đ/Đ cleanly for search matching", () => {
    expect(foldAdminSearchText("Phạm Gia Hân · Đặng")).toBe("pham gia han · dang");
    expect(foldAdminSearchText("Nguyễn Văn Khôi")).toContain("van khoi");
  });

  it("renders action-specific #admin-confirm-modal copy across all 6 action types", () => {
    const target = makeSampleUsers()[1];
    const specs = (
      ["grant_teacher", "revert_student", "lock", "unlock", "delete_account", "reset_password"] as const
    ).map((t) => getConfirmModalSpec(t, target));

    expect(new Set(specs.map((s) => s.title)).size).toBe(6);
    expect(specs[4].title).toContain("Xóa");
    expect(specs[4].desc).toContain("vĩnh viễn");
    expect(specs[4].confirmLabel).toBe("Xóa vĩnh viễn");
  });

  it("enforces borderless 2-control Header, 4-card Overview, honest analysesToday/system health, merged Accounts usage, and emailVerified tags", () => {
    const html = renderToString(
      <AdminWorkspaceView
        initialTab="overview"
        initialUsersFixture={makeSampleUsers()}
        initialOverviewFixture={{
          analysesToday: 1,
          totalAnalyses: 2,
          succeededRequests: 1,
          analyses7d: 2,
          dbConnected: true,
          databaseDialect: "postgresql",
        }}
      />,
    );
    // Header has ONLY Bell + Avatar (no manual refresh button)
    expect(html).not.toContain('id="btn-admin-refresh"');
    expect(html).toContain('id="btn-admin-notif-bell"');
    expect(html).toContain('id="btn-admin-account-menu"');
    // Overview has strictly 4 KPI cards and zero decorative badges or hardcoded req/phút
    expect((html.match(/class="admin-kpi-card"/g) ?? []).length).toBe(4);
    expect(html).not.toContain("req/phút");
    expect(html).not.toContain("Đang quản lý");
    expect(html).not.toContain("Đang bảo vệ");
    expect(html).not.toContain("Đã ghi nhận");
    // Tổng usedToday của users là 5, nhưng analysesToday từ server là 1 -> không bị ép lên 5
    expect(html).toContain(">1 lượt<");
    expect(html).not.toContain(">5 lượt<");
    // aiServiceConfigured === null -> Chưa xác định thay vì Hoạt động giả
    expect(html).toContain("Chưa xác định");
    expect(html).toContain("CSDL: PostgreSQL");

    const accountsHtml = renderToString(
      <AdminWorkspaceView initialTab="accounts" initialUsersFixture={makeSampleUsers()} />,
    );
    expect(accountsHtml).toContain("Đã xác minh email");
    expect(accountsHtml).toContain("Chưa xác minh email");
    // Merged usage column (Sử dụng hôm nay) without repetitive "Chưa đo token" in table rows
    expect(accountsHtml).toContain("Sử dụng hôm nay");
    expect(accountsHtml).not.toContain("Hạn mức AI / ngày");
    expect(accountsHtml).not.toContain("Chưa đo token");
  });

  it("contains zero fake offline mutation fallbacks and preserves required controls in AdminWorkspaceView.tsx", () => {
    const src = readFileSync(
      new URL("./AdminWorkspaceView.tsx", import.meta.url),
      "utf8",
    );
    expect(src).not.toContain("fallback to local update in offline preview");
    expect(src).not.toContain("fallback in offline preview");
    expect(src).not.toContain("ignore in offline preview");
    expect(src).not.toContain("admin@axo.edu.vn");
    expect(src).toContain('id="admin-load-error-banner"');
    expect(src).toContain('id="btn-admin-retry-overview"');
    expect(src).toContain('id="btn-admin-empty-reset"');
    expect(src).toContain('id="detail-user-email-verified"');
    expect(src).toContain('dotsTargetUser.role !== "admin"');
    expect(src).toContain("defaultRoleLimit =\n                detailUser.role === \"admin\"\n                  ? 500");
  });
});
