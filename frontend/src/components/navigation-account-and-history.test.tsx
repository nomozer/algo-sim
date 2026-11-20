import { readFileSync } from "node:fs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import { describeComposerError } from "./ProblemInput";
import { LibraryView } from "./LibraryView";
import { HistoryView } from "./HistoryView";
import { AuthGate, AuthPageView } from "./AuthGate";
import {
  HEADER_COMPACT_BREAKPOINT_PX,
  TopNavAccount,
  shouldUseCompactHeaderAccount,
  useToastStore,
} from "./TopNav";
import { registerAllSimulations } from "../simulations";
import { __resetHistoryForTest } from "../state/history";
import { useAppStore } from "../state/store";
import { useAuthStore } from "../state/auth";

registerAllSimulations();

function syncStoreForSSR() {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
  Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
  Object.assign(useToastStore.getInitialState(), useToastStore.getState());
}

describe("Navigation Views, Error Localization & Library Controls", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
    useAuthStore.setState({
      user: null,
      resolved: true,
      busy: false,
      error: null,
      authGate: null,
    });
    useToastStore.getState().clearToasts();
    syncStoreForSSR();
  });

  afterEach(() => {
    useToastStore.getState().clearToasts();
    useAppStore.getState().reset();
    syncStoreForSSR();
  });

  it("5. Sửa lỗi UX nhỏ đã xác minh: AuthGate dùng tên Axo, modal đóng có aria-hidden='true', describeComposerError phân biệt lỗi mạng và dịch vụ tạm ngưng", () => {
    useAuthStore.setState({ authGate: "register" });
    syncStoreForSSR();
    const gateHtml = renderToString(<AuthGate />);
    expect(gateHtml).toContain("Em/thầy cô dùng Axo với vai trò");
    expect(gateHtml).not.toContain("AlgoSim");

    const histHtml = renderToString(<HistoryView />);
    expect(histHtml).toContain('aria-hidden="true"');

    const netInfo = describeComposerError("Không kết nối được máy chủ phân tích.", null);
    expect(netInfo?.title).toBe("Không kết nối được máy chủ");

    const svcInfo = describeComposerError(
      "Dịch vụ phân tích đề chưa cấu hình khóa AI (503).",
      { ok: true, hasKey: false, cachedProblems: 0 },
    );
    expect(svcInfo?.title).toBe("Dịch vụ phân tích đề hiện chưa sẵn sàng");

    // Forgot password view: phân biệt rõ trạng thái chưa khả dụng (không nhắc SMTP, vô hiệu hóa form ngay từ đầu) và khả dụng (§8)
    const forgotUnavailableHtml = renderToString(
      <AuthPageView mode="forgot" initialEmailRecoveryAvailable={false} />,
    );
    expect(forgotUnavailableHtml).not.toContain('id="btn-goto-reset-from-forgot"');
    expect(forgotUnavailableHtml).toContain('id="forgot-unavailable-note"');
    expect(forgotUnavailableHtml).not.toContain("SMTP");
    expect(forgotUnavailableHtml).toMatch(
      /<input[^>]*id="forgot-email-input"[^>]*disabled=""/,
    );
    expect(forgotUnavailableHtml).toMatch(
      /<button[^>]*id="btn-forgot-submit"[^>]*disabled=""/,
    );

    const forgotAvailableHtml = renderToString(
      <AuthPageView mode="forgot" initialEmailRecoveryAvailable={true} />,
    );
    expect(forgotAvailableHtml).not.toContain('id="forgot-unavailable-note"');
    expect(forgotAvailableHtml).not.toMatch(
      /<input[^>]*id="forgot-email-input"[^>]*disabled=""/,
    );

    // LibraryView đã làm sạch thuật ngữ nội bộ Workspace V6.2 (§5, §11)
    const libHtml = renderToString(<LibraryView />);
    expect(libHtml).toContain('id="library-cards-grid"');
    expect(libHtml).toContain(
      "Khám phá các bài toán hình học không gian qua mô hình 3D tương tác và từng bước dựng hình.",
    );
    expect(libHtml).not.toContain("Workspace V6.2");
  });
});


describe("Auth Reset Token & TopNav Account Popover Parity", () => {
  beforeEach(() => {
    useAppStore.getState().reset();
    useAuthStore.setState({
      user: null,
      resolved: true,
      busy: false,
      error: null,
      authGate: null,
    });
    syncStoreForSSR();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    useAuthStore.setState({ user: null });
    syncStoreForSSR();
  });

  it("6. #view-reset yêu cầu ô nhập Mã khôi phục (#reset-token-input) và useAuthStore gửi đúng token tới /api/auth/reset-password", async () => {
    const resetHtml = renderToString(<AuthPageView mode="reset" />);
    expect(resetHtml).toContain('id="reset-token-input"');
    expect(resetHtml).toContain("Mã khôi phục");

    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      if (url === "/api/auth/forgot-password") {
        return new Response(
          JSON.stringify({
            ok: true,
            smtpConfigured: false,
            deliveryStatus: "BLOCKED_EXTERNAL_CONFIGURATION",
            message: "Môi trường máy chủ hiện chưa cấu hình dịch vụ gửi email (SMTP).",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url === "/api/auth/reset-password") {
        const parsed = JSON.parse(String(init?.body || "{}"));
        expect(parsed.token).toBe("tok-v28-secret");
        expect(parsed.newPassword).toBe("mat-khau-moi-12345");
        return new Response(JSON.stringify({ ok: true, updated: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`Unexpected URL: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const forgotRes = await useAuthStore
      .getState()
      .requestPasswordReset("hocsinh@truong.edu.vn");
    expect(forgotRes.ok).toBe(true);
    expect(forgotRes.smtpConfigured).toBe(false);
    expect((forgotRes as any).deliveryStatus).toBe("BLOCKED_EXTERNAL_CONFIGURATION");

    const resetRes = await (useAuthStore.getState().resetPassword as any)(
      "tok-v28-secret",
      "mat-khau-moi-12345",
      "hocsinh@truong.edu.vn",
    );
    expect(resetRes.ok).toBe(true);
    expect(resetRes.updated).toBe(true);
  });


  it("15. Targeted Parity Correction — Header sản phẩm hiển thị [Avatar] [Tên] [Chevron] trên desktop cho cả 3 vai trò và thu gọn sang [Avatar tròn] khi viewport hẹp hoặc thiếu chỗ", () => {
    const roles: Array<{
      id: number;
      email: string;
      displayName: string;
      role: "student" | "teacher" | "admin";
      expectAdminMenuItem: boolean;
    }> = [
      {
        id: 3,
        email: "hocsinh@axo.edu.vn",
        displayName: "Trần Minh Khoa",
        role: "student",
        expectAdminMenuItem: false,
      },
      {
        id: 2,
        email: "giaovien@axo.edu.vn",
        displayName: "Nguyễn Thị Lan",
        role: "teacher",
        expectAdminMenuItem: false,
      },
      {
        id: 1,
        email: "admin@axo.edu.vn",
        displayName: "Quản trị viên",
        role: "admin",
        expectAdminMenuItem: true,
      },
    ];

    for (const r of roles) {
      useAuthStore.setState({
        user: {
          id: r.id,
          email: r.email,
          displayName: r.displayName,
          role: r.role,
          mustChangePassword: false,
        },
        resolved: true,
      });
      syncStoreForSSR();

      const closedHtml = renderToString(<TopNavAccount initialOpen={false} />);
      expect(closedHtml, `role=${r.role} không được ép cứng is-compact-account`).not.toContain(
        "is-compact-account",
      );
      expect(closedHtml).toContain('id="header-user-avatar"');
      expect(closedHtml).toContain('id="header-user-name"');
      expect(closedHtml).toContain(r.displayName);
      expect(closedHtml).toContain("user-caret-svg");

      const openHtml = renderToString(<TopNavAccount initialOpen={true} />);
      expect(openHtml).toContain('id="account-popover"');
      expect(openHtml).toContain("Hạn mức AI hôm nay");
      expect(openHtml).toContain('id="btn-acc-open-settings"');
      expect(openHtml).not.toContain('id="btn-acc-open-history"');
      expect(openHtml).toContain('id="btn-acc-logout"');
      if (r.expectAdminMenuItem) {
        expect(openHtml).toContain('id="btn-acc-open-admin"');
        expect(openHtml).toContain("Bảng điều khiển Quản trị");
      } else {
        expect(openHtml).not.toContain('id="btn-acc-open-admin"');
      }
    }

    // Kiểm tra logic quyết định responsive compact dựa trên ngưỡng 720px và va chạm thực tế trên Header
    expect(HEADER_COMPACT_BREAKPOINT_PX).toBe(720);
    for (const wideViewport of [1440, 1366, 1024, 820, 745]) {
      expect(
        shouldUseCompactHeaderAccount({
          viewportWidth: wideViewport,
          navRight: 520,
          navWidth: 265,
          rightClusterLeft: 560,
          rightClusterWidth: 210,
          nameScrollWidth: 112,
          nameClientWidth: 112,
        }),
        `viewport=${wideViewport} đủ không gian phải giữ đầy đủ tên + chevron`,
      ).toBe(false);
    }
    for (const narrowViewport of [720, 656, 600, 390, 360]) {
      expect(
        shouldUseCompactHeaderAccount({
          viewportWidth: narrowViewport,
          navRight: 240,
          navWidth: 140,
          rightClusterLeft: 320,
          rightClusterWidth: 74,
        }),
        `viewport=${narrowViewport} hẹp phải chuyển sang avatar compact`,
      ).toBe(true);
    }
    // Va chạm giữa capsule điều hướng và cụm phải trên màn > 720px vẫn thu gọn an toàn
    expect(
      shouldUseCompactHeaderAccount({
        viewportWidth: 820,
        navRight: 545,
        navWidth: 265,
        rightClusterLeft: 552,
        rightClusterWidth: 250,
      }),
    ).toBe(true);
    // Tên dài bị xén vượt quá max-width cũng tự thu gọn an toàn
    expect(
      shouldUseCompactHeaderAccount({
        viewportWidth: 900,
        navRight: 520,
        navWidth: 265,
        rightClusterLeft: 620,
        rightClusterWidth: 260,
        nameScrollWidth: 215,
        nameClientWidth: 190,
      }),
    ).toBe(true);

    // Kiểm tra CSS đảm bảo kiểu desktop pill 32px + avatar 24px + compact circle + focus-visible
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    expect(css).toMatch(/\.user-profile-btn\s*\{[^}]*height:\s*32px;[^}]*padding:\s*3px 10px 3px 5px;/s);
    expect(css).toMatch(/\.user-avatar-dot\s*\{[^}]*width:\s*24px;[^}]*height:\s*24px;/s);
    expect(css).toMatch(/\.user-profile-btn:focus-visible\s*\{[^}]*outline:\s*2px solid var\(--primary\);/s);
    expect(css).toContain("@media (max-width: 720px)");
  });

});
